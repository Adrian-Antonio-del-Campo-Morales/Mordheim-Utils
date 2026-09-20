"""Development and application commands; heavy imports stay local."""
from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path
import json
import os
import sys
import time

from mordheim_combat_lab.console import HelpFormatter as _StyledHelpFormatter


def _positive(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise ValueError("value must be positive")
    return parsed


def _percentage(value: str) -> float:
    parsed = float(value)
    if not 0 <= parsed <= 100:
        raise ValueError("percentage must be between 0 and 100")
    return parsed


def _warmups(value: str) -> int:
    """Warm-up count for benchmark runs (0-100)."""
    parsed = int(value)
    if not 0 <= parsed <= 100:
        raise ValueError("warm-ups must be between 0 and 100")
    return parsed


#: Default grids for ``benchmark --deep``: the generic ``--simulation-sizes``
#: and ``--batch-sizes`` options override them, which is why there are no
#: separate ``--deep-*`` aliases.
DEEP_SIMULATION_SIZES = "10k,100k,500k,1M,5M"
DEEP_BATCH_SIZES = "25k,100k,200k,500k"


def _oracle_workers(value: str) -> int | None:
    """Worker policy for the modular-oracle samples.

    ``auto`` (the default) pools only the samples whose estimated sequential
    runtime exceeds the parallel gate; an explicit positive integer forces
    that pool size; ``1`` stays sequential.
    """
    if value.casefold() == "auto":
        return None
    parsed = int(value)
    if parsed < 1:
        raise ValueError("workers must be at least one")
    return parsed


def _parity_sample_timing(item) -> str:
    """Engine-level wall times for one statistical/deep parity sample line.

    ``reference`` is the modular oracle for statistical/matrix rows and NumPy
    for the numpy<->native cross rows; the candidate is the certified engine.
    """
    reference = "numpy" if item.scenario.startswith("cross:") else "oracle"
    return (
        f"({item.simulations:,} duels/engine; "
        f"{reference} {item.reference_seconds:.2f}s + "
        f"{item.backend} {item.candidate_seconds:.2f}s)"
    )


def _structural_errors(knowledge, specs) -> tuple[list[str], int]:
    """Structural layer of ``verify`` (the former ``validate`` command).

    Runs the editorial contract of every maintained document (band packages,
    catalogue, hireling and campaign catalogues, registry), the execution
    contract, the phase-verification audit and the default compilation of
    every band profile. Returns the error list and the compiled profile count.
    """
    from mordheim_construction.compiler import compile_fighter
    from mordheim_construction.contracts import validate_execution_contract
    from mordheim_core.models import FighterBuild
    from mordheim_knowledge.editorial_schemas import validate_knowledge_base
    from mordheim_knowledge.loader import load_bands
    from mordheim_combat_lab.verification.structural import audit_phase_verification

    errors = list(validate_knowledge_base(knowledge))
    errors.extend(validate_execution_contract("mordheim", knowledge))
    report = audit_phase_verification("mordheim", knowledge, specs)
    errors.extend(report.errors)
    compiled = 0
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection, knowledge):
            for profile in band.profiles:
                try:
                    compile_fighter(FighterBuild(
                        "mordheim", collection=collection,
                        band_id=str(band.band["id"]), profile_id=str(profile["id"]),
                    ), knowledge)
                except ValueError as error:
                    # Scope exclusions and mandatory selectable grants are valid
                    # classifications; every other compilation failure is structural.
                    message = str(error).casefold()
                    if not any(expected in message for expected in (
                        "outside the duel runtime", "at least one mutation",
                        "exactly one or two mutations", "requires one or two mutations",
                        "require at least one blessing",
                    )):
                        errors.append(f"{collection}/{band.band['id']}/{profile['id']}: {error}")
                else:
                    compiled += 1
    return errors, compiled


def verify_command(args) -> int:
    """Validate the knowledge base and run the semantic specifications.

    The structural layer always runs first (the gate the old ``validate``
    command enforced). ``--structural`` stops there; otherwise the semantic
    specifications run against the modular engine. ``--inventory`` keeps its
    fast JSON-only path.
    """
    from mordheim_knowledge.loader import knowledge_root
    from mordheim_combat_lab.verification.audit import verify_semantics
    from mordheim_combat_lab.verification.inventory import inventory

    knowledge = Path(args.knowledge).resolve() if args.knowledge else knowledge_root()
    specs = Path(args.specs).resolve() if args.specs else None
    if args.inventory:
        print(json.dumps([asdict(item) for item in inventory(knowledge)],
                         ensure_ascii=True, indent=2))
        return 0
    errors, compiled = _structural_errors(knowledge, specs)
    if args.structural:
        if args.json:
            print(json.dumps({"structural_complete": not errors,
                              "structural_errors": errors,
                              "profiles_compiled": compiled},
                             ensure_ascii=True, indent=2))
        else:
            for error in errors:
                print(f"FAIL: {error}")
            if errors:
                print("structural_complete=False")
            else:
                print(f"structural_complete=True; {compiled} profiles compile with "
                      "their default construction")
            print("semantic layer skipped (--structural)")
        return int(bool(errors))
    semantic = verify_semantics(knowledge, specs)
    payload = {"structural_complete": not errors,
               "structural_errors": errors,
               "profiles_compiled": compiled,
               "semantic_complete": semantic.semantic_complete, **asdict(semantic)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(f"structural_complete={not errors} ({compiled} profiles compile)")
        print(f"semantic_complete={semantic.semantic_complete}")
        print(f"{len(semantic.verified)}/{len(semantic.obligations)} obligations verified; "
              f"{len(semantic.pending)} pending; "
              f"{sum(len(item.passed_cases) for item in semantic.fixtures)} passed cases; "
              f"{sum(len(item.killed_mutations) for item in semantic.fixtures)} detected mutations")
        required = [item for item in semantic.interaction_assessments
                    if item.verification_requirement == "required"]
        print(f"interaction_policy={semantic.interaction_policy}; "
              f"{len(required) - len(semantic.required_pending_interactions)}/{len(required)} required interactions covered; "
              f"{len(semantic.required_pending_interactions)} required pending")
        for error in (*errors, *semantic.errors):
            print(f"FAIL: {error}")
        if semantic.pending:
            print("PENDING: use --json for the effect-by-effect backlog.")
    return int(bool(errors or semantic.errors or
                    args.require_complete and not semantic.semantic_complete))


def _deep_benchmark_command(args, scenarios, installed) -> int:
    """Deep benchmark: modular as a small reference, optimized engines swept
    over large sizes and batch sizes (see deep_benchmark_plan for the policy)."""
    pair_set = getattr(args, "pair_set", "full")
    if not args.output:
        from mordheim_combat_lab.report_naming import timestamped_report_path
        args.output = {
            "mini": timestamped_report_path("outputs/benchmarks", "deep-mini", ".json"),
            "fast": timestamped_report_path("outputs/benchmarks", "deep-fast", ".json"),
        }.get(pair_set, timestamped_report_path("outputs/benchmarks", "deep", ".json"))
    from time import perf_counter

    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import deep_benchmark_plan
    from mordheim_combat_lab.cli.benchmarking import print_deep_benchmark_header
    from mordheim_combat_lab.cli.benchmarking import print_sweep_table
    from mordheim_combat_lab.cli.benchmarking import run_benchmark
    from mordheim_combat_lab.cli.benchmarking import sweep_payload
    from mordheim_combat_lab.cli.benchmarking import print_elapsed_summary
    from mordheim_combat_lab.cli.benchmarking import write_report
    from mordheim_combat_lab.cli.benchmarking import parse_sizes

    command_started = perf_counter()
    vector_sizes = parse_sizes(
        args.simulation_sizes if args.simulation_sizes else DEEP_SIMULATION_SIZES, 10_000)
    batch_sizes = parse_sizes(
        args.batch_sizes if args.batch_sizes else DEEP_BATCH_SIZES, 4_000)
    backends = tuple(args.backend)
    plan = deep_benchmark_plan(
        scenarios, vector_sizes=vector_sizes, batch_sizes=batch_sizes,
        modular_simulations=args.deep_modular_simulations,
        backends=backends, installed=installed,
    )
    if not plan.runs:
        print("Benchmark configuration error: none of the requested backends is "
              "available for --deep",
              file=sys.stderr)
        return 2
    by_id = {scenario.id: scenario for scenario in scenarios}
    unavailable = list(plan.excluded)
    processes = max(1, int(getattr(args, "processes", 1) or 1))
    # The bar advances once per executed sample, not per planned run: each
    # optimized run performs warmups + repeats executions, the modular
    # reference only one. Counting runs would show a bogus 100% while most
    # of the sweep is still executing. (Pool mode advances once per unit.)
    progress = None if args.json else BenchmarkProgress(
        sum(1 if backend == "modular" else args.warmups + args.repeats
            for _s, backend, _n, _b in plan.runs)
    )
    timings = []
    if processes > 1:
        from mordheim_combat_lab.cli.benchmarking import BenchmarkUnit
        from mordheim_combat_lab.cli.benchmarking import run_benchmark_units
        # The pool parallelizes whole scenario measurements. Repeating every
        # unit sequentially first would double the wall time of a full deep
        # profile, so the speedup report reuses the per-sample totals the
        # workers already measured (identical work, same seed, same machine).
        units = [
            BenchmarkUnit(
                scenario=by_id[scenario_id], backend=backend,
                simulations=simulations, batch_size=batch_size, seed=args.seed,
                warmups=0 if backend == "modular" else args.warmups,
                repeats=1 if backend == "modular" else args.repeats,
                batch=f"{scenario_id}/{backend}/{simulations}/{batch_size}",
            )
            for scenario_id, backend, simulations, batch_size in plan.runs
        ]
        pool_started = perf_counter()
        results, timings, failures = run_benchmark_units(
            units, processes=processes,
            on_progress=progress.advance if progress is not None else None,
        )
        pool_wall = perf_counter() - pool_started
        unavailable.extend(
            {"scenario": unit.scenario.id, "backend": unit.backend,
             "reason": reason}
            for unit, reason in failures
        )
    else:
        results = []
        for scenario_id, backend, simulations, batch_size in plan.runs:
            try:
                results.append(run_benchmark(
                    by_id[scenario_id], simulations=simulations, batch_size=batch_size,
                    seed=args.seed, backend=backend,
                    warmups=0 if backend == "modular" else args.warmups,
                    repeats=1 if backend == "modular" else args.repeats,
                    on_progress=progress.advance if progress is not None else None,
                ))
            except RuntimeError as error:
                unavailable.append({"scenario": scenario_id, "backend": backend,
                                    "reason": str(error)})
        pool_wall = None
    if progress is not None:
        progress.finish()
    elapsed_seconds = perf_counter() - command_started
    engine_seconds = sum(sum(item.samples_seconds) for item in results)
    payload = sweep_payload(
        results, unavailable, simulation_sizes=vector_sizes,
        batch_sizes=batch_sizes, seed=args.seed, warmups=args.warmups,
        repeats=args.repeats, pair_set=pair_set,
    )
    payload["mode"] = "deep"
    payload["modular_reference_simulations"] = plan.modular_simulations
    payload["elapsed_seconds"] = elapsed_seconds
    payload["engine_seconds"] = engine_seconds
    speedup_summary = None
    if pool_wall is not None:
        from mordheim_combat_lab.cli.benchmarking import speedup_payload
        speedup = speedup_payload(
            timings, pool_wall=pool_wall, processes=processes,
        )
        if speedup is not None:
            payload["parallel_speedup"] = speedup
            if not args.json:
                speedup_summary = (
                    f"Parallel speedup: {processes} processes; wall "
                    f"{speedup['wall_seconds']:.2f}s vs {speedup['speedup'] * speedup['wall_seconds']:.2f}s "
                    f"of engine samples -> {speedup['speedup']:.2f}x"
                )
    if args.output:
        write_report(Path(args.output), payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print_deep_benchmark_header(plan, pair_set=pair_set)
        print_sweep_table(
            results, unavailable, simulation_sizes=vector_sizes,
            batch_sizes=batch_sizes, seed=args.seed, repeats=args.repeats,
        )
        if speedup_summary:
            print(speedup_summary)
        print_elapsed_summary(
            elapsed_seconds=elapsed_seconds, engine_seconds=engine_seconds,
            processes=processes,
        )
        for entry in plan.excluded:
            print(f"{entry['backend']} not available: {entry['reason']}")
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
    return 0


def _tts_benchmark_command(args, scenarios, pair_set) -> int:
    """Time-to-solution study: run every (simulations x batch size) cell of
    the workload through every (strategy x backend) combination and rank the
    combinations by the wall time of solving the cell completely. The
    identical per-batch streams cross-check strategy vs strategy and native
    vs numpy totals as a parity gate."""
    from mordheim_combat_lab.cli.benchmarking import (
        BenchmarkProgress, parse_sizes, parse_tts_strategies,
        print_tts_study_summary, run_tts_study_cell, tts_backend_parity,
        tts_backend_rates, tts_cell_payload, tts_cell_winners,
        tts_study_payload, write_report,
    )
    from time import perf_counter

    strategies = None
    try:
        strategies = parse_tts_strategies(args.strategies)
    except ValueError as error:
        print(f"Benchmark configuration error: {error}", file=sys.stderr)
        return 2
    if len(strategies) < 2:
        print("Benchmark configuration error: --tts compares execution "
              "strategies; pass at least two, e.g. "
              "--strategies 'sequential,processes=4,parallel=4'", file=sys.stderr)
        return 2
    backends = tuple(args.backend)
    if "modular" in backends:
        print("Benchmark configuration error: --tts measures the optimized "
              "engines only; drop modular", file=sys.stderr)
        return 2
    backends = tuple(
        backend for backend in ("numpy", "native") if backend in backends)
    if not backends:
        print("Benchmark configuration error: --tts needs --backend numpy "
              "(and optionally native)", file=sys.stderr)
        return 2
    simulation_sizes = parse_sizes(args.simulation_sizes, args.simulations)
    batch_sizes = parse_sizes(args.batch_sizes, args.batch_size)
    repeats = max(1, int(getattr(args, "repeats", 1) or 1))
    scenario_count = len(scenarios)
    # Only combinations that will actually run (parallel=N is numpy-only).
    combinations_per_cell = sum(
        1 for backend in backends for strategy in strategies
        if not (strategy.startswith("parallel=") and backend != "numpy"))
    total_combinations = (len(simulation_sizes) * len(batch_sizes)
                          * combinations_per_cell * scenario_count * repeats)
    progress = None if args.json else BenchmarkProgress(total_combinations)
    command_started = perf_counter()
    cells: list[dict[str, object]] = []
    parity_reports: list[dict[str, object]] = []
    rate_rows: list[dict[str, float | str]] = []
    for simulations in simulation_sizes:
        for batch_size in batch_sizes:
            cell_results = run_tts_study_cell(
                strategies, backends, scenarios, simulations=simulations,
                batch_size=batch_size, seed=args.seed, repeats=repeats,
                on_progress=progress.advance if progress is not None else None,
            )
            parity_reports.append(tts_backend_parity(cell_results))
            rate_rows.extend(tts_backend_rates(
                cell_results, simulations=simulations,
                scenario_count=scenario_count))
            cells.append({
                "simulations": simulations, "batch_size": batch_size,
                "results": cell_results,
                "winners": tts_cell_winners(
                    cell_results, scenario_count=scenario_count,
                    simulations=simulations),
                "rates": tts_backend_rates(
                    cell_results, simulations=simulations,
                    scenario_count=scenario_count),
            })
    if progress is not None:
        progress.finish()
    parity_report = (
        None if not parity_reports
        else {
            "passed": all(item["passed"] for item in parity_reports),
            "backends": parity_reports[0]["backends"],
        })
    payload = tts_study_payload(
        [tts_cell_payload(cell) for cell in cells],
        simulations=simulation_sizes, batch_sizes=batch_sizes, seed=args.seed,
        strategies=strategies, backends=backends, repeats=repeats,
        scenario_count=scenario_count, pair_set=pair_set,
        elapsed_seconds=perf_counter() - command_started,
        parity=parity_report,
    )
    if args.output:
        write_report(Path(args.output), payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print_tts_study_summary(cells, pair_set=pair_set)
        if parity_report is not None:
            verdict = "PASS" if parity_report["passed"] else "FAIL"
            print(f"Parity gate: {verdict} - per-backend totals across "
                  f"strategies (cross-engine rate parity is the parity "
                  f"command's job).")
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
    failed = parity_report is not None and not parity_report["passed"]
    return 1 if failed else 0


def benchmark_command(args) -> int:
    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_combat_lab.cli.benchmarking import compare_with_baseline
    from mordheim_combat_lab.cli.benchmarking import load_benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import parse_sizes
    from mordheim_combat_lab.cli.benchmarking import print_elapsed_summary
    from mordheim_combat_lab.cli.benchmarking import print_gate
    from mordheim_combat_lab.cli.benchmarking import print_results_table
    from mordheim_combat_lab.cli.benchmarking import print_sweep_table
    from mordheim_combat_lab.cli.benchmarking import run_benchmark
    from mordheim_combat_lab.cli.benchmarking import sweep_payload
    from mordheim_combat_lab.cli.benchmarking import write_benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import write_report
    from mordheim_combat.vectorized import available_backends

    if args.deep and (args.baseline or args.save_baseline or args.require_improvement):
        print("Benchmark configuration error: --deep cannot be combined with "
              "--baseline/--save-baseline/--require-improvement", file=sys.stderr)
        return 2
    pair_set = getattr(args, "pair_set", None)
    if (pair_set is not None and pair_set != "full"
            and not (args.deep or args.tts)):
        print(
            "Benchmark configuration error: --pair-set applies to --deep and "
            "--tts workloads",
            file=sys.stderr)
        return 2
    sweep = args.simulation_sizes is not None or args.batch_sizes is not None
    if sweep and not args.deep and (args.baseline or args.save_baseline or args.require_improvement):
        print("Benchmark configuration error: --baseline/--save-baseline and "
              "--require-improvement apply to single-configuration runs only",
              file=sys.stderr)
        return 2
    if args.require_improvement and not args.baseline:
        print("Benchmark baseline error: --require-improvement requires --baseline",
              file=sys.stderr)
        return 2
    if args.tts:
        if args.deep:
            print("Benchmark configuration error: --tts is itself a full "
                  "workload study (--pair-set already selects every combat "
                  "type); --deep sweeps belong to the classic throughput mode",
                  file=sys.stderr)
            return 2
        if args.baseline or args.save_baseline or args.require_improvement:
            print("Benchmark configuration error: --tts compares wall times and "
                  "does not support baseline gates", file=sys.stderr)
            return 2
        if max(1, int(getattr(args, "processes", 1) or 1)) > 1:
            print("Benchmark configuration error: --tts selects its own "
                  "strategies with --strategies; --processes belongs to the "
                  "standard throughput modes", file=sys.stderr)
            return 2
        if args.backend and "native" in args.backend and "numpy" not in args.backend:
            print("Benchmark configuration error: --tts runs the numpy engine "
                  "for the batch-pool strategies; include numpy in --backend",
                  file=sys.stderr)
            return 2

    scenarios = benchmark_scenarios()
    if args.deep:
        from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
        scenarios = deep_test_scenarios(pair_set or "full")
    if args.tts and pair_set is not None:
        from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
        scenarios = deep_test_scenarios(pair_set)
    if args.scenario != "all":
        scenarios = tuple(item for item in scenarios if item.id == args.scenario)
    if not scenarios:
        scope = (
            f"the {pair_set} deep pair set"
            if args.deep or (args.tts and pair_set is not None)
            else "the standard benchmark suite")
        print(
            f"Benchmark configuration error: scenario {args.scenario!r} is not "
            f"available in {scope}",
            file=sys.stderr,
        )
        return 2
    if args.tts:
        return _tts_benchmark_command(args, scenarios, pair_set)
    from time import perf_counter

    installed = available_backends()
    command_started = perf_counter()
    if args.deep:
        return _deep_benchmark_command(args, scenarios, installed)
    backends = tuple(args.backend)
    runnable_backends = tuple(
        backend for backend in backends
        if backend != "native" or backend in installed
    )
    simulation_sizes = parse_sizes(args.simulation_sizes, args.simulations)
    batch_sizes = parse_sizes(args.batch_sizes, args.batch_size)
    units = (
        len(scenarios) * len(runnable_backends)
        * len(simulation_sizes) * len(batch_sizes) * (args.warmups + args.repeats)
    )
    progress = None if args.json else BenchmarkProgress(units)
    unavailable = []
    processes = max(1, int(getattr(args, "processes", 1) or 1))
    timings = []
    if processes > 1:
        from mordheim_combat_lab.cli.benchmarking import BenchmarkUnit
        from mordheim_combat_lab.cli.benchmarking import run_benchmark_units
        work_units = []
        for simulations in simulation_sizes:
            for batch_size in batch_sizes:
                for backend in backends:
                    if backend == "native" and backend not in installed:
                        unavailable.append({
                            "backend": backend,
                            "reason": "native backend is not compiled in this environment",
                        })
                        continue
                    for scenario in scenarios:
                        work_units.append(BenchmarkUnit(
                            scenario=scenario, backend=backend,
                            simulations=simulations, batch_size=batch_size,
                            seed=args.seed, warmups=args.warmups,
                            repeats=args.repeats,
                            batch=f"{scenario.id}/{backend}/{simulations}/{batch_size}",
                        ))
        pool_started = perf_counter()
        results, timings, failures = run_benchmark_units(
            work_units, processes=processes,
            on_progress=progress.advance if progress is not None else None,
        )
        pool_wall = perf_counter() - pool_started
        unavailable.extend(
            {"scenario": unit.scenario.id, "backend": unit.backend,
             "reason": reason}
            for unit, reason in failures
        )
    else:
        results = []
        for simulations in simulation_sizes:
            for batch_size in batch_sizes:
                for backend in backends:
                    if backend == "native" and backend not in installed:
                        unavailable.append({
                            "backend": backend,
                            "reason": "native backend is not compiled in this environment",
                        })
                        continue
                    for scenario in scenarios:
                        try:
                            results.append(run_benchmark(
                                scenario, simulations=simulations, batch_size=batch_size,
                                seed=args.seed, backend=backend, warmups=args.warmups,
                                repeats=args.repeats,
                                on_progress=progress.advance if progress is not None else None,
                            ))
                        except RuntimeError as error:
                            unavailable.append({
                                "scenario": scenario.id, "backend": backend,
                                "reason": str(error),
                            })
        pool_wall = None
    if progress is not None:
        progress.finish()

    elapsed_seconds = perf_counter() - command_started
    engine_seconds = sum(sum(item.samples_seconds) for item in results)
    speedup_summary = None
    speedup_report = None
    if pool_wall is not None:
        from mordheim_combat_lab.cli.benchmarking import speedup_payload
        speedup_report = speedup_payload(
            timings, pool_wall=pool_wall, processes=processes,
        )
        if speedup_report is not None:
            speedup_summary = (
                f"Parallel speedup: {processes} processes; wall "
                f"{speedup_report['wall_seconds']:.2f}s vs "
                f"{speedup_report['speedup'] * speedup_report['wall_seconds']:.2f}s "
                f"of engine samples -> {speedup_report['speedup']:.2f}x"
            )
    if sweep:
        payload = sweep_payload(
            results, unavailable, simulation_sizes=simulation_sizes,
            batch_sizes=batch_sizes, seed=args.seed, warmups=args.warmups,
            repeats=args.repeats,
        )
        if speedup_report is not None:
            payload["parallel_speedup"] = speedup_report
        payload["elapsed_seconds"] = elapsed_seconds
        payload["engine_seconds"] = engine_seconds
        if args.output:
            write_report(Path(args.output), payload)

        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
        else:
            print_sweep_table(
                results, unavailable, simulation_sizes=simulation_sizes,
                batch_sizes=batch_sizes, seed=args.seed, repeats=args.repeats,
            )
            if speedup_summary:
                print(speedup_summary)
            print_elapsed_summary(
                elapsed_seconds=elapsed_seconds, engine_seconds=engine_seconds,
                processes=processes,
            )
            if args.output:
                print(f"Report: {Path(args.output).resolve()}")
        return 0

    payload = benchmark_payload(
        results, unavailable, simulations=args.simulations,
        batch_size=args.batch_size, seed=args.seed, warmups=args.warmups,
        repeats=args.repeats,
    )
    if speedup_report is not None:
        payload["parallel_speedup"] = speedup_report
    payload["elapsed_seconds"] = elapsed_seconds
    payload["engine_seconds"] = engine_seconds
    gate = None
    if args.baseline:
        try:
            baseline = load_benchmark_payload(Path(args.baseline))
            expected = payload["configuration"]
            if baseline.get("configuration") != expected:
                raise ValueError(
                    "baseline configuration differs from the current benchmark: "
                    f"expected {expected}, found {baseline.get('configuration')}"
                )
            gate = compare_with_baseline(
                results, baseline,
                improvement_threshold=args.min_improvement / 100,
                regression_threshold=args.max_regression / 100,
            )
            payload["comparison"] = asdict(gate)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Benchmark baseline error: {error}", file=sys.stderr)
            return 2
    if args.save_baseline:
        write_benchmark_payload(Path(args.save_baseline), payload)
    if args.output:
        write_report(Path(args.output), payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print_results_table(
            results, unavailable, simulations=args.simulations,
            batch_size=args.batch_size, seed=args.seed, repeats=args.repeats,
        )
        if speedup_summary:
            print(speedup_summary)
        print_elapsed_summary(
            elapsed_seconds=elapsed_seconds, engine_seconds=engine_seconds,
            processes=processes,
        )
        if gate is not None:
            print_gate(gate, improvement=args.min_improvement,
                       regression=args.max_regression)
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
        if args.save_baseline:
            print(f"Baseline: {Path(args.save_baseline).resolve()}")
    return int(bool(args.require_improvement and (gate is None or not gate.passed)))


def parity_command(args) -> int:
    level = getattr(args, "level", "deterministic")
    args.statistical = level == "statistical"
    args.deep = level == "deep"
    pair_set = getattr(args, "pair_set", "full")
    if pair_set != "full" and not (args.deep or args.truncations):
        print(
            "Parity configuration error: --pair-set applies to --deep or "
            "--truncations; no pair set is run by the deterministic/statistical "
            "presets.",
            file=sys.stderr,
        )
        return 2
    if args.deep and not args.output:
        from mordheim_combat_lab.report_naming import timestamped_report_path
        args.output = {
            "mini": timestamped_report_path("outputs/parity", "deep-mini", ".json"),
            "fast": timestamped_report_path("outputs/parity", "deep-fast", ".json"),
        }.get(pair_set, timestamped_report_path("outputs/parity", "deep", ".json"))
    started = time.perf_counter()
    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
    from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
    from mordheim_combat_lab.verification.parity import compare_statistical_parity
    from mordheim_combat_lab.verification.parity import compare_truncation_parity
    from mordheim_combat_lab.verification.parity import parity_report_markdown
    from mordheim_combat_lab.verification.parity import parity_report_payload
    from mordheim_combat_lab.verification.parity import verify_vectorized_parity
    from mordheim_combat_lab.verification.parity import verify_specification_parity

    deep_scenarios = (
        deep_test_scenarios(pair_set)
        if args.deep or args.truncations else ()
    )

    report = verify_vectorized_parity()
    specification_report = verify_specification_parity()
    statistical = ()
    if args.statistical:
        from mordheim_combat.modular.parallel import resolve_oracle_workers
        from mordheim_combat.modular.parallel import run_oracle_sample
        from mordheim_combat.vectorized import available_backends

        installed = available_backends()
        progress = None if args.json else BenchmarkProgress(len(benchmark_scenarios()))
        samples: list = []
        for scenario in benchmark_scenarios():
            first, second = compile_benchmark_fighters(scenario)
            # One modular oracle sample certifies every optimized candidate;
            # `backend` records which engine produced each comparison.
            oracle_started = time.perf_counter()
            modular = run_oracle_sample(
                first, second, args.statistical_simulations, seed=args.seed,
                maximum_rounds=scenario.maximum_rounds,
                workers=resolve_oracle_workers(
                    args.workers, args.statistical_simulations,
                    scenario.maximum_rounds,
                ),
            )
            oracle_seconds = time.perf_counter() - oracle_started
            samples.append(compare_statistical_parity(
                scenario.id, first, second, args.statistical_simulations, seed=args.seed,
                maximum_rounds=scenario.maximum_rounds, modular=modular, backend="numpy",
                reference_seconds=oracle_seconds,
            ))
            if "native" in installed:
                samples.append(compare_statistical_parity(
                    scenario.id, first, second, args.statistical_simulations, seed=args.seed,
                    maximum_rounds=scenario.maximum_rounds, modular=modular, backend="native",
                    reference_seconds=oracle_seconds,
                ))
            if progress is not None:
                progress.advance()
        if progress is not None:
            progress.finish()
        statistical = tuple(samples)
    deep_samples, modular_duels = (), 0
    deep_native_installed = False
    if args.deep:
        from mordheim_combat.vectorized import available_backends
        from mordheim_combat_lab.verification.parity import DeepPair
        from mordheim_combat_lab.verification.parity import certify_deep

        installed = available_backends()
        deep_native_installed = "native" in installed
        if (args.deep_simulations is not None
                and args.deep_simulations <= 10_000
                and args.deep_cross_simulations == 1_000_000
                and deep_native_installed):
            print(
                "Note: --deep-simulations sizes the matrix samples (modular "
                "oracle + backends); the numpy<->native cross layer still runs "
                f"at the default {args.deep_cross_simulations:,} duels/pair, "
                "which dominates smoke runs once the matrix is small. Pass "
                "--deep-cross-simulations to scale it down too.",
                file=sys.stderr,
            )
        pairs = tuple(
            DeepPair(
                scenario.id,
                *compile_benchmark_fighters(scenario),
                scenario.maximum_rounds,
                simulations=(
                    args.deep_simulations
                    if args.deep_simulations is not None
                    else (25_000 if scenario.maximum_rounds > 50 else 100_000)
                ),
            )
            for scenario in deep_scenarios
        )
        requested_duels = sum(pair.simulations for pair in pairs)
        if args.deep_simulations is not None:
            breakdown = (
                f"{pair_set} set: {len(pairs)} pairs x "
                f"{args.deep_simulations:,}"
            )
        else:
            regular = sum(pair.simulations == 100_000 for pair in pairs)
            long_pairs = sum(pair.simulations != 100_000 for pair in pairs)
            parts = []
            if regular:
                parts.append(f"{regular} pairs at 100k")
            if long_pairs:
                parts.append(f"{long_pairs} long pair(s) at 25k")
            breakdown = f"{pair_set} set: " + ", ".join(parts)
        if requested_duels > args.max_modular_duels:
            print(
                "Parity configuration error: --deep would need "
                f"{requested_duels:,} modular duels ({breakdown}), above the "
                f"--max-modular-duels ceiling of {args.max_modular_duels:,}. "
                "Lower --deep-simulations or raise --max-modular-duels.",
                file=sys.stderr,
            )
            return 2
        progress = None if args.json else BenchmarkProgress(
            len(pairs) * (2 if deep_native_installed else 1)
        )
        deep_samples, modular_duels = certify_deep(
            pairs,
            simulations=(
                args.deep_simulations
                if args.deep_simulations is not None else 100_000
            ),
            cross_simulations=args.deep_cross_simulations, seed=args.seed,
            native_installed="native" in installed,
            on_progress=progress.advance if progress is not None else None,
            workers=args.workers,
            escalate=True,
            max_modular_duels=args.max_modular_duels,
        )
        if progress is not None:
            progress.finish()
    truncation_samples = ()
    if args.truncations:
        from mordheim_combat_lab.verification.parity import TRUNCATION_HORIZONS
        truncation_progress = None if args.json else BenchmarkProgress(
            len(deep_scenarios) * len(TRUNCATION_HORIZONS)
        )
        rows: list = []
        for scenario in deep_scenarios:
            first, second = compile_benchmark_fighters(scenario)
            for row in compare_truncation_parity(
                scenario.id, first, second,
                args.truncation_simulations, seed=args.seed,
                maximum_rounds=scenario.maximum_rounds,
                horizons=TRUNCATION_HORIZONS,
                workers=args.workers,
                on_progress=(truncation_progress.advance
                             if truncation_progress is not None else None),
            ):
                rows.append(row)
        if truncation_progress is not None:
            truncation_progress.finish()
        truncation_samples = tuple(rows)
    complete = (
        report.complete and specification_report.complete
        and all(item.passed for item in statistical)
        and all(item.passed for item in deep_samples)
        and all(item.passed for item in truncation_samples)
    )
    elapsed = time.perf_counter() - started
    payload = parity_report_payload(
        report, statistical, specification_report, deep=deep_samples,
        truncations=truncation_samples, elapsed_seconds=elapsed,
        deep_pair_set=pair_set if args.deep else None,
        truncation_pair_set=pair_set if args.truncations else None,
    )
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        content = (
            parity_report_markdown(payload)
            if output.suffix.casefold() in {".md", ".markdown"}
            else json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
        )
        output.write_text(content, encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(f"vectorized_parity_complete={complete}")
        print(
            f"{len(report.verified)}/{len(report.obligations)} obligations verified; "
            f"{len(report.pending)} pending; {len(report.divergences)} divergences"
        )
        print(f"exact_checks={','.join(report.exact_checks)}")
        print(
            f"specifications: {len(specification_report.passed)} PASS; "
            f"{len(specification_report.pending)} PENDING_ADAPTER; "
            f"{len(specification_report.divergences)} DIVERGENCE; "
            f"{len(specification_report.out_of_scope)} OUT_OF_SCOPE"
        )
        for divergence in report.divergences:
            print(f"DIVERGENCE: {divergence}")
        for pending in report.pending:
            print(f"PENDING: {pending}")
        for divergence in specification_report.divergences:
            print(f"SPEC DIVERGENCE: {divergence}")
        for item in statistical:
            print(
                f"STATISTICAL: {item.scenario}/{item.backend} "
                f"{'PASS' if item.passed else 'FAIL'} {_parity_sample_timing(item)}"
            )
        if deep_samples:
            if deep_native_installed:
                print(
                    f"DEEP: modular oracle {modular_duels:,} duels across the "
                    f"{pair_set} archetype set ({len(deep_scenarios)} pairs); "
                    f"cross-backend samples at "
                    f"{args.deep_cross_simulations:,} duels/engine"
                )
            else:
                print(
                    f"DEEP: modular oracle {modular_duels:,} duels across the "
                    f"{pair_set} archetype set ({len(deep_scenarios)} pairs); "
                    "cross-backend certification skipped "
                    "(native backend is not compiled in this environment)"
                )
            escalated = {
                row.scenario[len("matrix:"):]: row.simulations
                for row in deep_samples if row.escalated
            }
            if escalated:
                detail = ", ".join(
                    f"{label} ({size:,})" for label, size in sorted(escalated.items())
                )
                print(
                    f"DEEP: escalated {len(escalated)} pair(s) to larger "
                    f"samples: {detail}"
                )
            for item in deep_samples:
                print(
                    f"DEEP: {item.scenario}/{item.backend} "
                    f"{'PASS' if item.passed else 'FAIL'} {_parity_sample_timing(item)}"
                )
        for item in truncation_samples:
            print(
                f"TRUNCATION: {item.scenario}/{item.backend} "
                f"{'PASS' if item.passed else 'FAIL'} "
                f"{_parity_sample_timing(item)}"
            )
        print(f"Elapsed: {elapsed:.2f}s")
        if args.output:
            print(f"REPORT: {Path(args.output).resolve()}")
    return int(bool(args.require_complete and not complete))


def test_report_command(args) -> int:
    import csv
    from collections import Counter
    started = time.perf_counter()
    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_combat_lab.verification.specifications import load_fixtures
    from mordheim_combat_lab.verification.reporting import run_technical_tests
    from mordheim_combat_lab.verification.reporting import write_semantic_report

    # One unit per semantic specification, plus one per statistical scenario.
    # The bar closes before the pytest phase, which prints its own dots.
    from mordheim_combat_lab.report_naming import timestamped_report_path
    output = (Path(args.output).resolve() if args.output else
              timestamped_report_path("outputs", "test-report", "")).resolve()
    units = len(load_fixtures()) + (
        len(benchmark_scenarios()) if args.statistical else 0
    )
    progress = BenchmarkProgress(units)
    semantic_path, semantic_rows = write_semantic_report(
        output, statistical=args.statistical,
        simulations=args.statistical_simulations, seed=args.seed,
        on_progress=progress.advance, workers=args.workers,
    )
    progress.finish()
    technical_path = output / "technical-tests.csv"
    technical_exit = run_technical_tests(technical_path)
    semantic_counts = Counter(str(row.get("passes", "")) for row in semantic_rows)
    with technical_path.open("r", encoding="utf-8-sig", newline="") as stream:
        technical_rows = tuple(csv.DictReader(stream, delimiter=";"))
    technical_counts = Counter(str(row.get("status", "")) for row in technical_rows)
    print("semantic: " + ", ".join(
        f"{status}={semantic_counts.get(status, 0)}"
        for status in ("PASS", "FAIL", "PENDING", "OUT_OF_SCOPE")
    ))
    print("technical: " + ", ".join(
        f"{status}={technical_counts.get(status, 0)}"
        for status in ("PASS", "FAIL", "ERROR", "SKIP", "XFAIL", "XPASS", "NOT_RUN")
    ))
    print(f"SEMANTIC REPORT: {semantic_path}")
    print(f"TECHNICAL REPORT: {technical_path}")
    print(f"Elapsed: {time.perf_counter() - started:.2f}s")
    semantic_failed = semantic_counts.get("FAIL", 0) > 0
    incomplete = semantic_counts.get("PENDING", 0) > 0
    return int(bool(technical_exit or semantic_failed or (args.require_complete and incomplete)))


def coverage_gate_command(args) -> int:
    from mordheim_combat_lab.verification import coverage_gate

    suites = tuple(args.suites) if args.suites else coverage_gate.DEFAULT_SUITES
    floors = {}
    for token in args.area_floor or ():
        area, separator, percent = token.partition(":")
        if not separator or area not in coverage_gate.AREA_PATHS:
            print(
                f"Coverage configuration error: {token!r} must be "
                f"<area>:<percent> for one of {tuple(coverage_gate.AREA_PATHS)}",
                file=sys.stderr,
            )
            return 2
        try:
            floors[area] = _percentage(percent)
        except ValueError:
            print(f"Coverage configuration error: bad percentage in {token!r}",
                  file=sys.stderr)
            return 2
    started = time.perf_counter()
    try:
        report = coverage_gate.measure_coverage(suites)
    except ModuleNotFoundError:
        print(
            "Coverage gate error: the `coverage` package is not installed; "
            "install the project dev extra (`pip install -e .[dev]`)",
            file=sys.stderr,
        )
        return 2
    budget_path = Path(args.budget).resolve()
    if args.update_budget:
        coverage_gate.write_budget(budget_path, report)
        result = coverage_gate.evaluate(report, None, minimum_percent=floors)
    else:
        try:
            budget = coverage_gate.load_budget(budget_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Coverage budget error: {error}", file=sys.stderr)
            return 2
        result = coverage_gate.evaluate(report, budget, minimum_percent=floors)
    payload = coverage_gate.report_payload(
        result, minimum_percent=floors, budget_path=str(budget_path),
    )
    payload["elapsed_seconds"] = time.perf_counter() - started
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        areas = payload["areas"]
        for area, stats in areas.items():
            print(
                f"coverage {area}: {stats['percent']:.2f}% "
                f"({stats['covered']}/{stats['statements']} statements)"
            )
        if args.update_budget:
            print(f"BUDGET: {budget_path} updated")
        if result.passed:
            print("coverage_gate=passed")
        else:
            for error in result.errors:
                print(f"FAIL: {error}")
            print("coverage_gate=failed")
        print(f"Elapsed: {payload['elapsed_seconds']:.2f}s")
    return int(not result.passed)


def audit_command(args) -> int:
    from mordheim_combat_lab.verification.audit_export import generate_audit

    path = generate_audit(
        knowledge=Path(args.knowledge).resolve() if args.knowledge else None,
        specs=Path(args.specs).resolve() if args.specs else None,
        output=Path(args.output).resolve() if args.output else None,
        scope=args.scope, status=args.status, review_status=args.review_status,
    )
    print(path.resolve())
    return 0


def calibrate_command(args) -> int:
    """Lazy entry point: the sweeps import the combat engines themselves."""
    from mordheim_combat_lab.cli.calibration import calibration_command
    return calibration_command(args)


def ui_command(_args) -> int:
    from mordheim_combat_lab.ui.app import main
    return int(main() or 0)


class _HelpFormatter(_StyledHelpFormatter):
    """Help layout with the shared repository palette (console.py)."""


def build_parser(prog: str = "mordheim-combat-lab") -> ArgumentParser:
    # Light import on purpose: scenario definitions carry no combat-engine
    # imports, so parsing argument choices never pre-loads mordheim_combat
    # into sys.modules (which would break the coverage-gate measurement).
    from mordheim_combat_lab.cli.scenarios import DEEP_SCENARIOS

    parser = ArgumentParser(prog=prog, formatter_class=_HelpFormatter)
    deep_scenario_ids = tuple(item.id for item in DEEP_SCENARIOS)
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("ui", help="open the graphical interface",
                        formatter_class=_HelpFormatter).set_defaults(handler=ui_command)

    verification = commands.add_parser(
        "verify", help="validate the KB and run the semantic specifications",
        description="Validate the knowledge base and its structural connections "
                    "(editorial schemas, execution contract, phase verification, "
                    "default profile compilation) and run the semantic "
                    "specifications against the modular engine.",
        formatter_class=_HelpFormatter)
    verify_paths = verification.add_argument_group("paths")
    verify_paths.add_argument("--knowledge", metavar="PATH",
                              help="override the knowledge base location")
    verify_paths.add_argument("--specs", metavar="PATH",
                              help="override the specifications directory")
    verify_layers = verification.add_argument_group("layers")
    verify_layers.add_argument("--structural", action="store_true",
                               help="stop after the structural layer (the former "
                                    "`validate` command); the semantic layer is "
                                    "skipped")
    verify_output = verification.add_argument_group("output and strictness")
    verify_output.add_argument("--inventory", action="store_true",
                               help="print the rule inventory as JSON and exit")
    verify_output.add_argument("--json", action="store_true",
                               help="print the verification payload as JSON")
    verify_output.add_argument("--require-complete", action="store_true",
                               help="fail unless every obligation is verified "
                                    "(pending items are allowed otherwise)")
    verification.set_defaults(handler=verify_command)

    audit = commands.add_parser(
        "audit", help="generate the auditable rule inventory",
        description="Generate the auditable per-rule inventory CSV "
                    "(default: outputs/audit/rules-audit.csv).",
        formatter_class=_HelpFormatter)
    audit_paths = audit.add_argument_group("paths")
    audit_paths.add_argument("--knowledge", metavar="PATH",
                             help="override the knowledge base location")
    audit_paths.add_argument("--specs", metavar="PATH",
                             help="override the specifications directory")
    audit_filters = audit.add_argument_group("filters")
    audit_filters.add_argument("--scope", choices=("YES", "NO", "LATER"),
                               help="filter by scope classification")
    audit_filters.add_argument("--status", choices=("verified", "pending", "out_of_scope"),
                               help="filter by semantic status")
    audit_filters.add_argument("--review-status",
                               choices=("ready", "blocked_by_dependency", "needs_ruling",
                                        "verified", "not_applicable"),
                               help="filter by review status; needs_ruling surfaces "
                                    "the unanswered review questions")
    audit_output = audit.add_argument_group("output")
    audit_output.add_argument("--output", metavar="PATH",
                              help="output directory for the CSV (default: outputs/audit)")
    audit.set_defaults(handler=audit_command)

    coverage = commands.add_parser(
        "coverage-gate",
        help="measure deterministic engine coverage and check the drift budget",
        description="Run the deterministic combat-engine suites under coverage and "
                    "check that every line in the committed budget is still "
                    "exercised (drift gate), with optional per-area floors.",
        formatter_class=_HelpFormatter)
    coverage_content = coverage.add_argument_group("measurement")
    coverage_content.add_argument(
        "--suites", nargs="+", metavar="PATH",
        help="pytest paths to measure (default: modular + vectorized + phases "
             "+ the parity deterministic corpus)")
    coverage_content.add_argument(
        "--area-floor", action="append", metavar="AREA:PCT",
        help="minimum coverage percent per area, e.g. --area-floor modular:95 "
             "(repeatable)")
    coverage_output = coverage.add_argument_group("budget and output")
    coverage_output.add_argument(
        "--budget", default="tests/fixtures/coverage/budget.json", metavar="PATH",
        help="coverage budget file to check against (default: "
             "tests/fixtures/coverage/budget.json)")
    coverage_output.add_argument(
        "--update-budget", action="store_true",
        help="write the measured covered lines as the new budget instead of "
             "checking the existing one")
    coverage_output.add_argument("--json", action="store_true",
                                help="print the machine-readable report as JSON")
    coverage.set_defaults(handler=coverage_gate_command)

    benchmark = commands.add_parser(
        "benchmark", help="measure the combat engines",
        description="Measure the combat engines (modular, NumPy, native) in a single "
                    "configuration, a size sweep, a --deep large-scale profile or "
                    "the --tts time-to-solution study.",
        epilog="Recommended shapes, measured optima and calibration live in "
               "docs/guides/develop-and-release.md.",
        formatter_class=_HelpFormatter)
    run_options = benchmark.add_argument_group("run configuration")
    run_options.add_argument("-n", "--simulations", type=_positive, default=100_000,
                             metavar="DUELS", help="simulations per scenario and engine")
    run_options.add_argument("--seed", type=int, default=2026,
                             help="random seed for the engines")
    run_options.add_argument("--batch-size", type=_positive, default=100_000,
                             metavar="DUELS",
                             help="batch size for the vectorized and native engines")
    run_options.add_argument(
        "--backend", choices=("modular", "numpy", "native"), nargs="+",
        default=("modular", "numpy", "native"), metavar="ENGINE",
        help="engines to measure (one or more); defaults to modular, vectorized and native",
    )
    run_options.add_argument(
        "--scenario",
        choices=("all", *deep_scenario_ids),
        default="all", help="scenario/pair id to measure; defaults to all five "
                             "standard scenarios, or all selected pairs in --deep",
    )
    run_options.add_argument(
        "--warmups", type=_warmups, default=1, metavar="N",
        help="warm-up runs per configuration (0-100)",
    )
    run_options.add_argument("--repeats", type=_positive, default=5, metavar="TIMES",
                             help="timed repetitions per configuration (median is reported)")
    deep_options = benchmark.add_argument_group("sweeps and deep profiles")
    deep_options.add_argument(
        "--simulation-sizes", metavar="SIZES",
        help="comma/space separated simulation counts, e.g. 1k,10k,100k (sweep "
             "mode); --deep defaults to " + DEEP_SIMULATION_SIZES)
    deep_options.add_argument(
        "--batch-sizes", metavar="SIZES",
        help="comma/space separated batch sizes, e.g. 10k,100k (sweep mode); "
             "--deep defaults to " + DEEP_BATCH_SIZES)
    deep_options.add_argument(
        "--deep", action="store_true",
        help="deep profile: sweep the optimized engines over large sizes and batch "
             "sizes while measuring the modular oracle only at a small reference size",
    )
    deep_options.add_argument(
        "--pair-set", choices=("mini", "fast", "full"), default=None, metavar="SET",
        help="pair set for --deep and --tts workloads: mini is the 10-pair "
             "performance-survey set; fast is the 30-pair coverage-oriented set "
             "for a roughly 10-15 minute pooled profile; full is the 42-pair "
             "matrix (deep sweeps default to full)",
    )
    deep_options.add_argument(
        "--deep-modular-simulations", type=_positive, default=10_000, metavar="DUELS",
        help="duels per scenario for the modular reference point in --deep mode",
    )
    deep_options.add_argument(
        "--processes", type=_positive, default=1, metavar="N",
        help="run the scenario measurements through a process pool of N workers "
             "and report the real multi-core speedup; 1 keeps the historical "
             "sequential execution",
    )
    tts_options = benchmark.add_argument_group("time to solution")
    tts_options.add_argument(
        "--tts", action="store_true",
        help="time-to-solution study: run every (simulation size x batch size) "
             "cell of the workload through every (strategy x backend) "
             "combination and rank them by total wall time (spawns included); "
             "--pair-set selects the combat-type workload, --simulation-sizes "
             "and --batch-sizes the grid, --repeats the per-cell median; the "
             "identical per-batch streams double as a parity gate across "
             "strategies and backends",
    )
    tts_options.add_argument(
        "--strategies", metavar="LIST",
        help="comma separated strategies for --tts: sequential, processes=N, "
             "parallel=N (default: sequential,processes=4,parallel=4; "
             "parallel=N runs on numpy only)",
    )
    report_options = benchmark.add_argument_group("comparison gates and reports")
    report_options.add_argument("--json", action="store_true",
                                help="print the machine-readable report as JSON")
    report_options.add_argument("--output", metavar="PATH",
                                help="save this run as a report (.json, or .csv/.md in sweep mode; "
                                     "--deep defaults to deep.json or deep-fast.json by pair set)")
    report_options.add_argument("--save-baseline", metavar="PATH",
                                help="save this single-configuration run as a JSON baseline")
    report_options.add_argument("--baseline", metavar="PATH",
                                help="compare against a previous single-configuration JSON baseline")
    report_options.add_argument(
        "--require-improvement", action="store_true",
        help="fail unless some scenario improves and none exceeds the allowed regression",
    )
    report_options.add_argument("--min-improvement", type=_percentage, default=10.0,
                                metavar="PCT", help="required improvement threshold, percent")
    report_options.add_argument("--max-regression", type=_percentage, default=5.0,
                                metavar="PCT", help="maximum allowed regression, percent")
    benchmark.set_defaults(handler=benchmark_command)

    parity = commands.add_parser(
        "parity", help="certify the vectorized and native engines against the modular oracle",
        description="Certify the vectorized engine (and, when compiled, the native "
                    "backend) against the modular oracle with deterministic checks, "
                    "optional six-sigma statistical samples and --deep certification.",
        epilog="--level selects the certification preset; the size of each layer "
               "is tuned with the --*-simulations options.",
        formatter_class=_HelpFormatter)
    parity_samples = parity.add_argument_group("certification samples")
    parity_samples.add_argument(
        "--level", choices=("deterministic", "statistical", "deep"),
        default="deterministic", metavar="LEVEL",
        help="preset: deterministic (default) runs the exact checks only; "
             "statistical adds the aggregate six-sigma samples on the five "
             "standard scenarios; deep runs the selected archetype pair set "
             "(fast or full) plus the numpy<->native cross at scale",
    )
    parity_samples.add_argument(
        "--pair-set", choices=("mini", "fast", "full"), default="full", metavar="SET",
        help="pair set for --deep/--truncations: mini is the 10-pair "
             "performance-survey set; fast is the 30-pair "
             "coverage-oriented set for a roughly 10-15 minute pooled run; "
             "full is the 42-pair deep matrix (default)",
    )
    parity_samples.add_argument("--statistical-simulations", type=_positive, default=100_000,
                                metavar="DUELS",
                                help="duels per engine and scenario for "
                                     "--level statistical")
    parity_samples.add_argument(
        "--deep-simulations", type=_positive, default=None, metavar="DUELS",
        help="duels per archetype pair and engine at --level deep; defaults to "
             "100 000 per pair, or 25 000 for the long 75-round pair; an "
             "explicit value applies to every pair.  Pairs that come back "
             "suspicious (3-6 sigma) or timing-prone (1%%+ unresolved) are "
             "re-certified at twice the sample while the "
             "--max-modular-duels budget allows",
    )
    parity_samples.add_argument("--deep-cross-simulations", type=_positive, default=1_000_000,
                                metavar="DUELS",
                                help="duels per pair for the numpy<->native "
                                     "cross-certification (never touches the modular engine)")
    parity_samples.add_argument("--max-modular-duels", type=_positive, default=5_000_000,
                                metavar="DUELS",
                           help="ceiling for the total modular-oracle duels a "
                                "--level deep run may ask for (the default full "
                                "split needs 4 050 000, plus any adaptive "
                                "escalation within the same ceiling)")
    parity_samples.add_argument(
        "--truncations", action="store_true",
        help="add round-truncation outcome samples: the six-sigma gate is "
             "reapplied at every horizon (2, 4, 6, 8, 10, 12, 15, 20 rounds) on "
             "every deep-matrix pair, so orchestration defects that only "
             "shift *when* duels resolve become visible",
    )
    parity_samples.add_argument(
        "--truncation-simulations", type=_positive, default=10_000,
        metavar="DUELS",
        help="duels per engine, scenario and horizon for --truncations",
    )
    parity_samples.add_argument("--seed", type=int, default=2026,
                                help="seed for the statistical and deep samples")
    parity_samples.add_argument(
        "--workers", type=_oracle_workers, metavar="N|auto",
        default=os.environ.get("MORDHEIM_PARALLEL_ORACLE_WORKERS", "auto"),
        help="processes for the modular-oracle samples of the statistical and "
             "deep layers; auto pools only samples estimated to take over ~20 s "
             "sequentially, 1 disables the pool (also from "
             "MORDHEIM_PARALLEL_ORACLE_WORKERS)",
    )
    parity_output = parity.add_argument_group("report and strictness")
    parity_output.add_argument("--json", action="store_true",
                               help="print the certificate as JSON")
    parity_output.add_argument("--require-complete", action="store_true",
                               help="fail unless the certificate is complete")
    parity_output.add_argument("--output", metavar="PATH",
                               help="save the report as .json or .md (deep defaults to "
                                    "deep.json for full, deep-fast.json for fast "
                                    "or deep-mini.json for mini)")
    parity.set_defaults(handler=parity_command)

    test_report = commands.add_parser(
        "test-report", help="generate the human-readable parity and technical test CSVs",
        description="Generate the Excel-friendly CSVs of semantic parity and technical "
                    "tests into an output directory.",
        formatter_class=_HelpFormatter)
    test_report_content = test_report.add_argument_group("content")
    test_report_content.add_argument("--statistical", action="store_true",
                                     help="add the five statistical parity rows to "
                                          "the semantic CSV")
    test_report_content.add_argument("--statistical-simulations", type=_positive, default=100_000,
                                     metavar="DUELS",
                                     help="duels per engine and scenario for --statistical")
    test_report_content.add_argument("--seed", type=int, default=2026,
                                     help="seed for the statistical comparisons")
    test_report_content.add_argument(
        "--workers", type=_oracle_workers, metavar="N|auto",
        default=os.environ.get("MORDHEIM_PARALLEL_ORACLE_WORKERS", "auto"),
        help="processes for the modular-oracle samples of --statistical; "
             "auto pools only samples estimated to take over ~20 s sequentially, "
             "1 disables the pool (also from MORDHEIM_PARALLEL_ORACLE_WORKERS)",
    )
    test_report_output = test_report.add_argument_group("output and strictness")
    test_report_output.add_argument("--output", metavar="PATH",
                                    help="directory for the two CSVs (default: outputs/test-report)")
    test_report_output.add_argument("--require-complete", action="store_true",
                                    help="fail when pending items or missing backends "
                                         "would keep the report from being complete")
    test_report.set_defaults(handler=test_report_command)

    calibration = commands.add_parser(
        "calibrate", help="measure this machine's engine optima and install the profile",
        description="Sweep every duel type in the deep matrix across batches, pooled "
                    "batches and worker counts on both engines, plus process-pool "
                    "spawn cost, and install a per-machine calibration profile the "
                    "Combat Lab loads at startup (batches, workers, spawn cost and "
                    "the pool speedup curve re-derived from the sweep evidence). "
                    "Default ~8-10 minutes; --pairs mini runs a ~2 minute survey.",
        epilog="Re-run after a hardware change, an engine update or new combat rules. "
               "The profile lives next to the preferences; --reset removes it.",
        formatter_class=_HelpFormatter)
    calibration_scope = calibration.add_argument_group("coverage")
    calibration_scope.add_argument("--pairs", choices=("full", "fast", "mini"), default="full",
                                   help="duel-type coverage of the native sweeps "
                                        "(default: full, all 42 pairs)")
    calibration_scope.add_argument("--seed", type=int, default=7,
                                   help="random seed for every sweep")
    calibration_measure = calibration.add_argument_group("measurement")
    calibration_measure.add_argument("--sample-size", type=_positive, default=500_000,
                                     metavar="DUELS",
                                     help="simulations per fighter in the native "
                                          "sequential sweep (default: 500000); the numpy "
                                          "sweep is sized separately from its batch "
                                          "candidates so each spans several batches")
    calibration_measure.add_argument("--pool-sample-size", type=_positive, default=1_000_000,
                                     metavar="DUELS",
                                     help="simulations per fighter in the pooled sweeps; "
                                          "numpy uses half (default: 1000000)")
    calibration_output = calibration.add_argument_group("output")
    calibration_output.add_argument("--output", metavar="PATH",
                                    help="also write the full report to PATH")
    calibration_output.add_argument("--no-install", action="store_true",
                                    help="measure and report without installing the profile")
    calibration_output.add_argument("--json", action="store_true",
                                    help="print the report as JSON")
    calibration_output.add_argument("--reset", action="store_true",
                                    help="remove the installed profile and exit")
    calibration.set_defaults(handler=calibrate_command)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        return ui_command(args)
    if getattr(args, "inventory", False) and getattr(args, "require_complete", False):
        parser.error("--inventory and --require-complete cannot be combined")
    return args.handler(args)
