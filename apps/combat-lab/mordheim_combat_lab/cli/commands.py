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


def _structural_errors(knowledge) -> tuple[list[str], int]:
    """Structural layer of ``verify`` (the former ``validate`` command).

    Runs the editorial contract of every maintained document (band packages,
    catalogue, hireling and campaign catalogues, registry), the execution
    contract, binding contracts and the default compilation of every band
    profile. Returns the error list and the compiled profile count.
    """
    from mordheim_construction.compiler import compile_fighter
    from mordheim_construction.contracts import validate_execution_contract
    from mordheim_core.models import FighterBuild
    from mordheim_knowledge.editorial_schemas import validate_knowledge_base
    from mordheim_knowledge.loader import load_bands, load_execution_contract, runtime_bindings
    from mordheim_combat_lab.verification.structural import (
        _binding_contract_error,
        _catalogue_binding_errors,
        required_profile_build,
    )

    errors = list(validate_knowledge_base(knowledge))
    errors.extend(validate_execution_contract("mordheim", knowledge))
    execution_ids = {
        str(row.get("id") or "")
        for row in load_execution_contract("mordheim", knowledge).get("mechanics") or ()
    }
    compiled = 0
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection, knowledge):
            for rule in band.special_rules:
                runtime = rule.get("runtime") or {}
                if runtime.get("scope") != "YES" or runtime.get("implemented") != "YES":
                    continue
                bindings = runtime_bindings(rule)
                if not bindings:
                    errors.append(
                        f"{band.band['id']}/{rule['id']}: implemented rule has no binding"
                    )
                for binding in bindings:
                    error = _binding_contract_error(binding, execution_ids)
                    if error:
                        errors.append(f"{rule['id']}: {error}")
            for profile in band.profiles:
                try:
                    # Supply the profile's printed mandatory initial choice from
                    # the same helper the structural projection uses, so a
                    # Trapper/Rat Ogre/Cripple is compiled with what its source
                    # requires instead of becoming a false structural failure.
                    compile_fighter(
                        required_profile_build(
                            collection, str(band.band["id"]), str(profile["id"])
                        ), knowledge
                    )
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
    errors.extend(_catalogue_binding_errors(knowledge, execution_ids))
    return errors, compiled


def verify_command(args) -> int:
    """Validate KB structure and default construction, without semantic tests."""
    from mordheim_knowledge.loader import knowledge_root
    from mordheim_combat_lab.verification.inventory import inventory

    knowledge = Path(args.knowledge).resolve() if args.knowledge else knowledge_root()
    if args.inventory:
        print(json.dumps([asdict(item) for item in inventory(knowledge)],
                         ensure_ascii=True, indent=2))
        return 0
    errors, compiled = _structural_errors(knowledge)
    payload = {"structural_complete": not errors, "structural_errors": errors,
               "profiles_compiled": compiled}
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        for error in errors:
            print(f"FAIL: {error}")
        print(f"structural_complete={not errors}; {compiled} profiles compile with "
              "their default construction")
    return int(bool(errors))


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
    from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
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
                fighters=compile_benchmark_fighters(by_id[scenario_id]),
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
    warmup_seconds = sum(item.warmup_seconds for item in results)
    payload = sweep_payload(
        results, unavailable, simulation_sizes=vector_sizes,
        batch_sizes=batch_sizes, seed=args.seed, warmups=args.warmups,
        repeats=args.repeats, pair_set=pair_set,
    )
    payload["mode"] = "deep"
    payload["modular_reference_simulations"] = plan.modular_simulations
    payload["elapsed_seconds"] = elapsed_seconds
    payload["engine_seconds"] = engine_seconds
    payload["warmup_seconds"] = warmup_seconds
    speedup_summary = None
    if pool_wall is not None:
        from mordheim_combat_lab.cli.benchmarking import speedup_payload
        speedup = speedup_payload(
            timings, pool_wall=pool_wall, processes=processes,
        )
        if speedup is not None:
            payload["parallel_speedup"] = speedup
            if not args.json:
                from mordheim_combat_lab.cli.benchmarking import format_parallel_summary
                speedup_summary = format_parallel_summary(speedup)
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
            processes=processes, warmup_seconds=warmup_seconds,
        )
        for entry in plan.excluded:
            print(f"{entry['backend']} not available: {entry['reason']}")
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
    return 0


def _tts_benchmark_command(args, scenarios, pair_set) -> int:
    """Time-to-solution study: run every (simulations x batch size) cell of
    the workload through every applicable (strategy x backend) combination
    and rank the combinations by the wall time of solving the cell
    completely. Within one backend every strategy executes the same duel
    streams, so their totals cross-check as a parity gate."""
    from mordheim_combat_lab.cli.benchmarking import (
        BenchmarkProgress, parse_sizes, parse_tts_strategies,
        print_tts_study_summary, run_tts_study_cell, tts_backend_parity,
        tts_backend_rates, tts_cell_payload, tts_cell_winners,
        tts_strategy_applies, tts_study_payload, write_report,
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
    backends = tuple(
        backend for backend in ("modular", "numpy", "native")
        if backend in tuple(args.backend))
    applicable = {
        backend: tuple(strategy for strategy in strategies
                       if tts_strategy_applies(strategy, backend))
        for backend in backends
    }
    inapplicable = [backend for backend, rows in applicable.items() if len(rows) < 2]
    if inapplicable:
        print("Benchmark configuration error: fewer than two of the requested "
              f"strategies apply to {', '.join(inapplicable)} (parallel=N:C is "
              "modular-only, parallel=N applies to modular and numpy)",
              file=sys.stderr)
        return 2
    simulation_sizes = parse_sizes(args.simulation_sizes, args.simulations)
    batch_sizes = parse_sizes(args.batch_sizes, args.batch_size)
    repeats = max(1, int(getattr(args, "repeats", 1) or 1))
    scenario_count = len(scenarios)
    # The modular oracle has no batch axis: it runs once per simulation size
    # and its rows are reused in that size's other batch cells.
    optimized = tuple(backend for backend in backends if backend != "modular")
    combinations_per_cell = sum(len(applicable[backend]) for backend in optimized)
    modular_combinations = len(applicable.get("modular", ()))
    total_combinations = (
        len(simulation_sizes) * len(batch_sizes) * combinations_per_cell
        + len(simulation_sizes) * modular_combinations
    ) * scenario_count * repeats
    progress = None if args.json else BenchmarkProgress(total_combinations)
    command_started = perf_counter()
    cells: list[dict[str, object]] = []
    parity_reports: list[dict[str, object]] = []
    rate_rows: list[dict[str, float | str]] = []
    for simulations in simulation_sizes:
        modular_rows = None
        for batch_size in batch_sizes:
            cell_backends = backends if modular_rows is None else optimized
            cell_results = run_tts_study_cell(
                strategies, cell_backends, scenarios, simulations=simulations,
                batch_size=batch_size, seed=args.seed, repeats=repeats,
                on_progress=progress.advance if progress is not None else None,
            )
            if "modular" in backends:
                if modular_rows is None:
                    modular_rows = tuple(
                        item for item in cell_results if item.backend == "modular")
                else:
                    cell_results = modular_rows + tuple(cell_results)
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
    from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
    from mordheim_combat_lab.cli.benchmarking import gate_against_baseline
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
    if getattr(args, "profile", False):
        if args.deep or args.tts or sweep:
            print("Benchmark configuration error: --profile applies to "
                  "single-configuration runs only (no --deep/--tts/size sweeps)",
                  file=sys.stderr)
            return 2
        if max(1, int(getattr(args, "processes", 1) or 1)) > 1:
            print("Benchmark configuration error: --profile needs the "
                  "sequential path; drop --processes", file=sys.stderr)
            return 2
        if args.baseline or args.save_baseline or args.require_improvement:
            print("Benchmark configuration error: profiled timings include "
                  "instrumentation overhead and cannot feed a baseline gate",
                  file=sys.stderr)
            return 2

    scenarios = benchmark_scenarios()
    if args.deep:
        from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
        scenarios = deep_test_scenarios(pair_set or "full")
    if args.tts and pair_set is not None:
        from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
        scenarios = deep_test_scenarios(pair_set)
    requested_scenarios = tuple(dict.fromkeys(args.scenario))
    if "all" not in requested_scenarios:
        if not (args.deep or (args.tts and pair_set is not None)):
            # Explicit ids select from the whole frozen catalogue: naming a
            # scenario outside the small default suite is the point.
            from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
            scenarios = deep_test_scenarios("full")
        available = {item.id for item in scenarios}
        unknown = [name for name in requested_scenarios if name not in available]
        scenarios = tuple(
            item for item in scenarios if item.id in requested_scenarios)
        if unknown or not scenarios:
            scope = (
                f"the {pair_set} deep pair set"
                if args.deep or (args.tts and pair_set is not None)
                else "the standard benchmark suite")
            names = ", ".join(repr(name) for name in (unknown or requested_scenarios))
            print(
                f"Benchmark configuration error: scenario(s) {names} not "
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
    profilers: dict[str, object] = {}
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
                            fighters=compile_benchmark_fighters(scenario),
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
                        profiler = None
                        if getattr(args, "profile", False):
                            import cProfile
                            profiler = profilers.setdefault(
                                backend, cProfile.Profile())
                        try:
                            results.append(run_benchmark(
                                scenario, simulations=simulations, batch_size=batch_size,
                                seed=args.seed, backend=backend, warmups=args.warmups,
                                repeats=args.repeats,
                                on_progress=progress.advance if progress is not None else None,
                                profiler=profiler,
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
    warmup_seconds = sum(item.warmup_seconds for item in results)
    profile_paths: dict[str, Path] = {}
    if profilers:
        from mordheim_combat_lab.cli.benchmarking import write_profile
        from mordheim_combat_lab.report_naming import timestamped_report_path
        for backend, profiler in profilers.items():
            path = timestamped_report_path(
                Path(args.profile_output), f"profile-{backend}", ".pstats")
            write_profile(profiler, path)
            profile_paths[backend] = path
    speedup_summary = None
    speedup_report = None
    if pool_wall is not None:
        from mordheim_combat_lab.cli.benchmarking import speedup_payload
        speedup_report = speedup_payload(
            timings, pool_wall=pool_wall, processes=processes,
        )
        if speedup_report is not None:
            from mordheim_combat_lab.cli.benchmarking import format_parallel_summary
            speedup_summary = format_parallel_summary(speedup_report)
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
        payload["warmup_seconds"] = warmup_seconds
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
                processes=processes, warmup_seconds=warmup_seconds,
            )
            if args.output:
                print(f"Report: {Path(args.output).resolve()}")
        return 0

    payload = benchmark_payload(
        results, unavailable, simulations=args.simulations,
        batch_size=args.batch_size, seed=args.seed, warmups=args.warmups,
        repeats=args.repeats, processes=processes, backends=backends,
    )
    if speedup_report is not None:
        payload["parallel_speedup"] = speedup_report
    payload["elapsed_seconds"] = elapsed_seconds
    payload["engine_seconds"] = engine_seconds
    payload["warmup_seconds"] = warmup_seconds
    if profile_paths:
        payload["profiled"] = True
        payload["profile_outputs"] = {
            backend: str(path) for backend, path in profile_paths.items()}
    gate = None
    if args.baseline:
        try:
            baseline = load_benchmark_payload(Path(args.baseline))
            gate = gate_against_baseline(
                payload, baseline, results,
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
            processes=processes, warmup_seconds=warmup_seconds,
        )
        if profilers:
            from mordheim_combat_lab.cli.benchmarking import render_profile
            print("Profiled timings include cProfile overhead; use them for "
                  "hotspots, not throughput claims.")
            for backend, profiler in profilers.items():
                print(f"\nProfile ({backend}), top functions by cumulative time:")
                print(render_profile(profiler))
                print(f"Profile data: {profile_paths[backend].resolve()}")
        if gate is not None:
            print_gate(gate, improvement=args.min_improvement,
                       regression=args.max_regression)
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
        if args.save_baseline:
            print(f"Baseline: {Path(args.save_baseline).resolve()}")
    return int(bool(args.require_improvement and (gate is None or not gate.passed)))


def _battery_command(args, profile: str) -> int:
    """Run the renewed P01/P02 battery and emit the P03 certificate.

    This is the only path that consumes the battery catalog.  It never falls
    back to NumPy for ``--backend native`` and never turns a declared, blocked
    or unexecuted case into a pass: a dependency stays a dependency.

    Exit status: 1 on an own error (a crashed candidate, a requested backend
    that is absent or stale, a divergence...) even without
    ``--require-complete``; with it, also on any incomplete certificate,
    ``UNDERPOWERED`` rows included.  Provenance differences (engine imported
    from outside this checkout, uncommitted sources) are warned about and
    recorded, never failures.
    """
    import hashlib

    from mordheim_combat_lab.verification.parity import _battery_cases as catalog
    from mordheim_combat_lab.verification.parity._battery_runner import (
        battery_report, battery_results, prepare_cases,
    )
    from mordheim_combat_lab.verification.parity._runner import run_parity
    from mordheim_combat_lab.verification.parity._report import (
        battery_failure_kind, battery_report_markdown, battery_report_payload,
    )
    from mordheim_combat_lab.verification.parity._statistical import (
        MAX_DETECTABLE_DIFFERENCE,
    )
    from mordheim_combat_lab.provenance import run_provenance
    from mordheim_knowledge.paths import project_root

    backend = getattr(args, "backend", None) or "numpy"
    requested = ("numpy", "native") if backend == "all" else (backend,)
    # Per-engine source digests of the packages actually imported, the native
    # build hash and the checkout revision; differences are warnings only.
    provenance = run_provenance(
        project_root(), tuple(dict.fromkeys(("modular", *requested))))
    rows = getattr(args, "rows", None)
    cases = catalog.battery_cases(profile)
    started = time.perf_counter()
    # One compiled input and one modular sample per case, shared by every
    # requested candidate: the oracle is paid for once, not per backend.
    reuse: dict = {}
    results: list = []
    for name in requested:
        prepared, failures = prepare_cases(
            cases, backend=name, rows=rows, reuse=reuse,
        )
        run = run_parity(
            prepared, backends=(name,), reference="modular",
            candidate="observed",
            workers=getattr(args, "workers", 1),
            repeat_candidate=True, cache=reuse,
        ) if prepared else None
        results.extend(battery_results(
            cases, () if run is None else run.rows, failures,
        ))
    report = battery_report(tuple(results), cases, profile=profile)
    elapsed = time.perf_counter() - started
    payload = battery_report_payload(
        report, profile=profile, backend=backend,
        catalog_sha256=hashlib.sha256(Path(catalog.__file__).read_bytes()).hexdigest(),
        inventory_sha256=catalog.INVENTORY_SHA256,
        elapsed_seconds=elapsed,
        backends=requested,
        provenance=provenance,
        rows_override=rows,
    )
    payload["oracle_workers_requested"] = getattr(args, "workers", 1)
    payload["oracle_workers_environment"] = os.environ.get(
        "MORDHEIM_PARALLEL_ORACLE_WORKERS")
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        content = (
            battery_report_markdown(payload)
            if output.suffix.casefold() in {".md", ".markdown"}
            else json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
        )
        output.write_text(content, encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        coverage = payload["coverage"]
        print(
            f"battery_profile={profile} backend={backend} "
            f"execution={payload['execution']}"
        )
        print(
            f"battery_complete={payload['complete']} "
            f"battery_accepted={payload['accepted']}"
        )
        print("battery: " + ", ".join(
            f"{name}={coverage.get(name, 0)}"
            for name in (
                "declared", "case_ids", "prepared", "executed", "compared",
                "approved", "divergent", "incompatible", "not_run",
                "underpowered", "errors", "dependency", "sensitivity_pending",
            )
        ))
        magnitudes = payload.get("magnitudes") or {}
        if magnitudes:
            print("battery magnitudes: " + ", ".join(
                f"{name}={row['passed']}/{row['cases']}"
                for name, row in sorted(magnitudes.items())
            ))
        if coverage.get("errors"):
            print(
                f"battery: {coverage['errors']} case(s) failed before approval "
                "(own error; see the case detail)"
            )
        if coverage.get("divergent"):
            print(
                f"battery: {coverage['divergent']} case(s) compared with a "
                "divergent distribution"
            )
        if coverage.get("dependency"):
            print(
                f"battery: {coverage['dependency']} case(s) kept out by a real "
                "input limit or a backend that declines the plan; partial "
                "execution, certificate incomplete"
            )
        if coverage.get("underpowered"):
            print(
                f"battery: {coverage['underpowered']} case(s) UNDERPOWERED: "
                "passed the six-sigma gate with too few rows to detect a "
                f"{MAX_DETECTABLE_DIFFERENCE} rate difference; not approved, "
                "certificate incomplete (minimum detectable difference per row "
                "in the report)"
            )
        limits = payload.get("limits") or {}
        for case_id, cause in sorted(limits.items()):
            print(f"LIMIT: {case_id} blocked_by={cause}")
        for row in payload["backends"]:
            print(
                f"BACKEND: {row['backend']} available={row['available']} "
                f"executed={row['executed']} compared={row['compared']} "
                f"approved={row['approved']} incompatible={row['incompatible']} "
                f"not_run={row['not_run']} underpowered={row['underpowered']}"
                + (f" ({row['note']})" if row.get("note") else "")
            )
        for message in provenance["warnings"]:
            print(f"PROVENANCE WARNING: {message}")
        if report.missing_variants:
            print("MISSING VARIANTS: " + ", ".join(report.missing_variants))
        owners = coverage.get("dependencies_by_owner") or {}
        for owner, case_ids in owners.items():
            print(f"DEPENDENCY: {owner} owns {len(case_ids)} case(s)")
        if payload["execution"] == "not-run":
            print(
                "battery: preparation only; no candidate sample was executed "
                "(a declared or blocked case is not a pass)"
            )
        if args.output:
            print(f"BATTERY REPORT: {Path(args.output).resolve()}")
        print(f"Elapsed: {elapsed:.2f}s")
    # One classification for the CLI and the report: an own error fails the
    # command even without --require-complete; a dependency only leaves the run
    # partial (identified as incomplete, never a pass).
    kinds = [
        battery_failure_kind(
            str(result.status), str(getattr(result, "detail", "") or ""),
        )
        for result in report.results
    ]
    errored = "error" in kinds
    incomplete = not (report.complete and report.accepted)
    return int(bool(errored or (
        getattr(args, "require_complete", False) and incomplete
    )))


def _catalog_parity_command(args) -> int:
    """Execute the fixture catalogues through the existing unified runner."""
    from mordheim_combat_lab.verification.parity import ParityCase, ParityRow, run_parity
    from mordheim_core.dice import ScriptedDecisions
    from mordheim_knowledge.paths import project_root

    started = time.perf_counter()
    catalog = args.catalog or "all"
    backend = args.backend or "numpy"
    profile = args.profile
    if args.level is not None and catalog == "battery":
        print("Parity configuration error: --level selects precompiled scenarios only.", file=sys.stderr)
        return 2
    if profile is not None and catalog == "precompiled":
        print("Parity configuration error: --profile filters battery cases only.", file=sys.stderr)
        return 2
    if ((args.level is not None and args.level not in ("small", "normal", "long"))
            or args.pair_set is not None or args.truncations
            or args.deep_simulations is not None):
        print("Parity configuration error: --catalog uses catalogue selection, --level small|normal|long, not --pair-set/--truncations/--deep-simulations.", file=sys.stderr)
        return 2
    if args.rows is not None:
        print("Parity configuration error: use --simulations with --catalog, not --rows.", file=sys.stderr)
        return 2
    try:
        from mordheim_combat_lab.cli.scenarios import load_checkout_module
        precompiled_catalog = load_checkout_module(
            "tests.engines.fixtures.precompiled_catalog")
        battery_catalogue = load_checkout_module(
            "tests.engines.fixtures.battery_catalogue")
        load_cases = load_checkout_module(
            "tools.verification.compiled_cases").load_cases
    except ImportError as error:
        print(f"Catalogue execution requires the source checkout and its test fixtures: {error}", file=sys.stderr)
        return 2

    requested = ("numpy", "native") if backend == "all" else (backend,)
    prepared = []
    failures = []
    order = []

    def failed(label, size, horizon, error):
        for engine in requested:
            failures.append(ParityRow(
                case=label, backend=engine, maximum_rounds=horizon,
                simulations=size, status="NOT_RUN", detail=f"Preparation failed: {type(error).__name__}: {error}",
            ))

    if catalog in ("precompiled", "all"):
        corpus_path = project_root() / "tests/engines/fixtures/compiled-cases.json"
        try:
            frozen = load_cases(corpus_path)
        except Exception as error:
            print(f"Cannot load frozen corpus (no compilation fallback): {error}", file=sys.stderr)
            return 2
        keys = tuple(precompiled_catalog.scenario_key(item.name)
                     for item in precompiled_catalog.scenarios_for_level(args.level or "small"))
        for key in keys:
            order.append(key)
            size, horizon = args.simulations or 1, 50
            try:
                item = frozen[key]
                size = args.simulations or args.statistical_simulations
                horizon = item.limits.maximum_rounds
                if any(item.initial_state.values()) or item.dice or item.decisions:
                    raise ValueError("this frozen case requires initial-state overrides or an exact replay; no inputs will be silently ignored")
                prepared.append(ParityCase(
                    label=key, first=item.first, second=item.second,
                    maximum_rounds=horizon, simulations=size, seed=args.seed,
                    context=item.context,
                ))
            except Exception as error:
                failed(key, size, horizon, error)

    if catalog in ("battery", "all"):
        from mordheim_construction.compiler import compile_fighter
        from mordheim_knowledge.loader import knowledge_root
        root = knowledge_root()
        for item in battery_catalogue.battery_cases(profile or "deep"):
            label = "battery/" + item.id
            order.append(label)
            size = args.simulations or item.rows
            limit = battery_catalogue.input_limit(item)
            if limit:
                prepared.append(ParityCase(
                    label=label, first=None, second=None, simulations=size,
                    maximum_rounds=item.maximum_rounds, blocked_by=limit,
                ))
                continue
            try:
                first = compile_fighter(item.first, root)
                second = compile_fighter(item.second, root)
                context = battery_catalogue.resolve_context(item.context, root)
                prepared.append(ParityCase(
                    label=label, first=first, second=second,
                    simulations=size, maximum_rounds=item.maximum_rounds,
                    seed=item.seed, context=context,
                    decisions=ScriptedDecisions(dict(item.decisions)),
                    magnitudes=battery_catalogue.case_magnitudes(item),
                ))
            except Exception as error:
                failed(label, size, item.maximum_rounds, error)

    completed = 0

    def progress():
        nonlocal completed
        if not args.json:
            print(f"Sampled {completed + 1}/{len(prepared)}: {prepared[completed].label}", flush=True)
        completed += 1

    run = run_parity(
        prepared, backends=requested, candidate="observed", workers=args.workers,
        seed=args.seed, on_progress=progress,
    )
    positions = {label: index for index, label in enumerate(order)}
    # A passing row too small to detect the maximum detectable difference is
    # UNDERPOWERED (not approved, not complete) — not a failure of a plain run.
    from dataclasses import replace as _replace
    from mordheim_combat_lab.verification.parity._battery_runner import _power_verdict
    from mordheim_combat_lab.verification.parity._report import UNDERPOWERED
    from mordheim_combat_lab.verification.parity._runner import NATIVE_OBSERVED_NOTE
    from mordheim_combat_lab.verification.parity._statistical import (
        MAX_DETECTABLE_DIFFERENCE,
    )

    def powered(row):
        status, approved, detail = _power_verdict(row)
        return row if status == row.status else _replace(
            row, status=status, approved=approved, detail=detail)

    rows = sorted((*(powered(row) for row in run.rows), *failures),
                  key=lambda row: positions[row.case])
    reference_only = backend == "modular"
    success = "COMPLETED" if reference_only else "PASS"
    summary = {
        "completed": sum(row.status == "COMPLETED" for row in rows),
        "passed": sum(row.status == "PASS" for row in rows),
        "failed": sum(row.status not in {"COMPLETED", "PASS", "INCOMPATIBLE", UNDERPOWERED}
                      for row in rows),
        "blocked": sum(row.status == "INCOMPATIBLE" for row in rows),
        "underpowered": sum(row.status == UNDERPOWERED for row in rows),
    }
    payload = {
        "catalog": catalog, "profile": profile or ("deep" if catalog != "precompiled" else None),
        "level": (args.level or "small") if catalog != "battery" else None,
        "backend": backend, "reference_only": reference_only,
        "complete": bool(rows) and all(row.status == success for row in rows),
        "parity_approved": not reference_only and bool(rows) and all(row.approved for row in rows),
        "summary": summary, "modular_duels": run.modular_duels,
        "max_detectable_difference": MAX_DETECTABLE_DIFFERENCE,
        "backend_notes": {"native": NATIVE_OBSERVED_NOTE} if "native" in requested else {},
        "elapsed_seconds": time.perf_counter() - started,
        "results": [
            {**asdict(row),
             "minimum_detectable_difference": row.minimum_detectable_difference}
            for row in rows
        ],
    }
    content = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    if args.output:
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    if args.json:
        print(content, end="")
    else:
        for row in rows:
            print(f"{row.status}: {row.case} [{row.backend}] n={row.simulations} rounds={row.maximum_rounds} {row.detail}")
        print("Summary: " + ", ".join(f"{key}={value}" for key, value in summary.items()))
        if summary["underpowered"]:
            print(f"{summary['underpowered']} row(s) UNDERPOWERED: passed the gate with too "
                  f"few duels to detect a {MAX_DETECTABLE_DIFFERENCE} rate difference; "
                  "not approved, not complete.")
        if "native" in requested:
            print(f"Native rows: {NATIVE_OBSERVED_NOTE}.")
        if reference_only:
            print("Modular execution only: these results do not approve statistical parity or rule correctness.")
        if args.output:
            print(f"REPORT: {Path(args.output).resolve()}")
    return int(not rows or summary["failed"] > 0 or (
        args.require_complete and not payload["complete"]
    ))


def _e2e_parity_command(args) -> int:
    """Execute explicitly selected precompiled E2E deliveries.

    A separate entry point for the E2E catalogue keeps the 43 precompiled
    scenarios and the battery path untouched; sampling and the six-sigma gate
    are still the shared runner's.
    """
    from tools.verification import e2e_parity

    selections = list(getattr(args, "e2e", None) or ())
    selection_file = getattr(args, "e2e_selection_file", None)
    if selection_file:
        try:
            selections.extend(e2e_parity.read_selection_file(Path(selection_file)))
        except OSError as error:
            print(f"Parity configuration error: cannot read --e2e-selection-file: {error}",
                  file=sys.stderr)
            return 2
    if not selections and not selection_file:
        index, _ = e2e_parity.discover(
            Path(args.e2e_deliveries) if getattr(args, "e2e_deliveries", None) else None)
        selections = sorted(index)
        if not selections:
            print("Parity configuration error: no E2E deliveries found.", file=sys.stderr)
            return 2
    if getattr(args, "level", None) is not None or getattr(args, "profile", None) is not None:
        print("Parity configuration error: --catalog e2e is configured with "
              "--simulations/--seed/--workers/--magnitudes; --level and "
              "--profile select other catalogues.", file=sys.stderr)
        return 2
    if (getattr(args, "pair_set", None) is not None
            or getattr(args, "truncations", False)
            or getattr(args, "deep_simulations", None) is not None):
        print("Parity configuration error: --catalog e2e does not use "
              "--pair-set/--truncations/--deep-simulations.", file=sys.stderr)
        return 2
    simulations = getattr(args, "simulations", None)
    if simulations is None:
        print("Parity configuration error: --catalog e2e requires an explicit "
              "--simulations <DUELS> sample width.", file=sys.stderr)
        return 2
    backend = getattr(args, "backend", None) or "numpy"
    if backend == "modular":
        print("Parity configuration error: --catalog e2e compares a candidate; "
              "choose numpy, native or all.", file=sys.stderr)
        return 2
    try:
        magnitudes = e2e_parity.parse_magnitudes(getattr(args, "magnitudes", None))
    except e2e_parity.MagnitudeError as error:
        print(f"Parity configuration error: {error}", file=sys.stderr)
        return 2
    deliveries = (Path(args.e2e_deliveries)
                  if getattr(args, "e2e_deliveries", None) else None)
    output_md = getattr(args, "output_md", None)
    if args.output and output_md and Path(args.output).resolve() == Path(output_md).resolve():
        print("Parity configuration error: --output and --output-md must use different paths.",
              file=sys.stderr)
        return 2
    try:
        payload, code = e2e_parity.execute(
            selections,
            simulations=simulations,
            seed=args.seed,
            backend=backend,
            workers=getattr(args, "workers", None),
            magnitudes=magnitudes,
            deliveries=deliveries,
        )
    except e2e_parity.SelectionError as error:
        print(f"Parity configuration error: {error}", file=sys.stderr)
        return 2
    content = json.dumps(payload, ensure_ascii=True, indent=2) + "\n"
    e2e_parity.write_reports(
        payload, output=Path(args.output) if args.output else None,
        output_md=Path(output_md) if output_md else None,
    )
    if args.json:
        print(content, end="")
    else:
        for item in payload["results"]:
            print(f"{item['outcome'].upper()}: {item['case_key']} {item['detail']}".rstrip())
        summary = payload["summary"]
        print("Summary: " + ", ".join(
            f"{name}={value}" for name, value in summary.items()))
        print("Compared magnitudes: "
              + ", ".join(payload["options"]["magnitudes"]))
        print("Samples only: this connection does not certify statistical "
              "parity or engine compatibility.")
        if args.output:
            print(f"REPORT: {Path(args.output).resolve()}")
        if output_md:
            print(f"MARKDOWN: {Path(output_md).resolve()}")
    return code


def parity_command(args) -> int:
    """Dispatch ``parity``; a failed oracle worker pool is a failed run (exit 2)."""
    from mordheim_combat_lab.verification.parity._runner import ParityPoolError

    try:
        return _parity_command(args)
    except ParityPoolError as error:
        print(f"Parity run error: {error}", file=sys.stderr)
        return 2


def _parity_command(args) -> int:
    if getattr(args, "level", None) == "e2e":
        if getattr(args, "catalog", None) not in (None, "precompiled", "e2e"):
            print("Parity configuration error: --level e2e cannot select a battery catalogue.",
                  file=sys.stderr)
            return 2
        args.catalog = "e2e"
        args.level = None
    if getattr(args, "catalog", None) == "e2e":
        return _e2e_parity_command(args)
    if getattr(args, "output_md", None):
        print("Parity configuration error: --output-md currently requires --catalog e2e or --level e2e.",
              file=sys.stderr)
        return 2
    if getattr(args, "catalog", None) is not None or getattr(args, "backend", None) == "modular":
        return _catalog_parity_command(args)
    if getattr(args, "simulations", None) is not None:
        print("Parity configuration error: --simulations requires --catalog.", file=sys.stderr)
        return 2
    # P03: ``--profile`` selects the renewed battery; every historical selector
    # (``--level``, ``--pair-set``, ``--truncations``) keeps its old meaning when
    # ``--profile`` is absent.  An explicit legacy selector plus ``--profile`` is
    # two different measurements of the same command, so it is refused instead
    # of silently mixing them; the argparse defaults are not a conflict.
    profile = getattr(args, "profile", None)
    if profile is not None:
        explicit = [
            name for name, value in (
                ("--level", getattr(args, "level", None)),
                ("--pair-set", getattr(args, "pair_set", None)),
                ("--truncations", True if getattr(args, "truncations", False) else None),
            ) if value is not None
        ]
        if explicit:
            print(
                "Parity configuration error: --profile selects the renewed "
                "battery and cannot be combined with " + ", ".join(explicit)
                + "; run the historical certificate without --profile.",
                file=sys.stderr,
            )
            return 2
        return _battery_command(args, profile)
    selected_backend = getattr(args, "backend", None)
    if selected_backend is not None and (
        getattr(args, "level", None) not in ("statistical", "deep")
        or getattr(args, "truncations", False)
    ):
        print(
            "Parity configuration error: --backend requires --profile or "
            "--level statistical|deep without --truncations.",
            file=sys.stderr,
        )
        return 2
    if getattr(args, "rows", None) is not None:
        print(
            "Parity configuration error: --rows applies to the renewed battery; "
            "pass it with --profile quick|complete|deep.",
            file=sys.stderr,
        )
        return 2
    if getattr(args, "level", None) in ("small", "normal", "long"):
        print("Parity configuration error: --level small|normal|long requires --catalog.", file=sys.stderr)
        return 2
    level = getattr(args, "level", None) or "deterministic"
    args.statistical = level == "statistical"
    args.deep = level == "deep"
    pair_set = getattr(args, "pair_set", None) or "full"
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
    statistical_backends = ()
    if args.statistical:
        from mordheim_combat.vectorized import available_backends

        installed = available_backends()
        if selected_backend in {"native", "all"} and "native" not in installed:
            print(
                "Parity configuration error: native backend is not available; "
                "use --backend numpy or install the native backend.",
                file=sys.stderr,
            )
            return 2
        statistical_backends = (
            (selected_backend,) if selected_backend in {"numpy", "native"}
            else tuple(name for name in ("numpy", "native") if name in installed)
        )
    started = time.perf_counter()
    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
    from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
    from mordheim_combat_lab.verification.parity import ParityCase
    from mordheim_combat_lab.verification.parity import compare_statistical_parity
    from mordheim_combat_lab.verification.parity import run_parity
    from mordheim_combat_lab.verification.parity import statistical_result
    from mordheim_combat_lab.verification.parity import parity_report_markdown
    from mordheim_combat_lab.verification.parity import parity_report_payload
    from mordheim_combat_lab.verification.parity import verify_vectorized_parity

    deep_scenarios = (
        deep_test_scenarios(pair_set)
        if args.deep or args.truncations else ()
    )

    report = verify_vectorized_parity()
    statistical = ()
    if args.statistical:
        from mordheim_combat.modular.parallel import resolve_oracle_workers
        from mordheim_combat.modular.parallel import run_oracle_sample
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
            for backend in statistical_backends:
                samples.append(compare_statistical_parity(
                    scenario.id, first, second, args.statistical_simulations, seed=args.seed,
                    maximum_rounds=scenario.maximum_rounds, modular=modular, backend=backend,
                    reference_seconds=oracle_seconds,
                ))
            if progress is not None:
                progress.advance()
        if progress is not None:
            progress.finish()
        statistical = tuple(samples)
    deep_samples, modular_duels = (), 0
    deep_native_installed = False
    from mordheim_combat.modular.parallel import resolve_oracle_workers as _resolve_workers
    from mordheim_combat.vectorized import available_backends as _available_backends

    installed_backends = tuple(
        name for name in ("numpy", "native") if name in _available_backends())
    # What the certificate was asked to certify, and with what.  No --backend
    # means "the installed backends" (historical behaviour, recorded as such);
    # an explicit native/all whose native backend is missing leaves the
    # certificate incomplete and fails the command.
    requested_backends = (
        ("numpy", "native") if selected_backend == "all"
        else (selected_backend,) if selected_backend in ("numpy", "native")
        else None
    )
    certified_backends = (
        statistical_backends if args.statistical
        else installed_backends if requested_backends is None
        else tuple(name for name in requested_backends if name in installed_backends)
    )
    missing_backends = tuple(
        name for name in (requested_backends or ())
        if name not in installed_backends
    )
    resolved_workers: dict[str, object] = {}
    if args.statistical:
        resolved_workers.update({
            scenario.id: _resolve_workers(
                args.workers, args.statistical_simulations, scenario.maximum_rounds)
            for scenario in benchmark_scenarios()
        })
    if args.deep:
        deep_native_installed = "native" in certified_backends
        if missing_backends:
            print(
                "PARITY INCOMPLETE: requested backend(s) "
                f"{', '.join(missing_backends)} not available; the deep "
                "certificate cannot cover them and will be marked incomplete.",
                file=sys.stderr,
            )
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
        segments = tuple(
            (
                scenario,
                *compile_benchmark_fighters(scenario),
                scenario.maximum_rounds,
                (
                    args.deep_simulations
                    if args.deep_simulations is not None
                    else (25_000 if scenario.maximum_rounds > 50 else 100_000)
                ),
            )
            for scenario in deep_scenarios
        )
        requested_duels = sum(segment[4] for segment in segments)
        if args.deep_simulations is not None:
            breakdown = (
                f"{pair_set} set: {len(segments)} pairs x "
                f"{args.deep_simulations:,}"
            )
        else:
            regular = sum(segment[4] == 100_000 for segment in segments)
            long_pairs = sum(segment[4] != 100_000 for segment in segments)
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
            len(segments) * (2 if deep_native_installed else 1)
        )
        resolved_workers.update({
            f"matrix:{scenario.id}": _resolve_workers(
                args.workers, simulations, maximum_rounds)
            for scenario, _first, _second, maximum_rounds, simulations in segments
        })
        matrix = run_parity(
            tuple(
                ParityCase(
                    label=f"matrix:{scenario.id}", first=first,
                    second=second, maximum_rounds=maximum_rounds,
                    simulations=simulations, seed=args.seed,
                )
                for scenario, first, second, maximum_rounds, simulations
                in segments
            ),
            backends=certified_backends,
            candidate="counts",
            workers=args.workers,
            on_progress=progress.advance if progress is not None else None,
            escalate=True,
            max_modular_duels=args.max_modular_duels,
        ) if certified_backends else None
        cross = None
        if deep_native_installed:
            cross = run_parity(
                tuple(
                    ParityCase(
                        label=f"cross:{scenario.id}", first=first,
                        second=second, maximum_rounds=maximum_rounds,
                        simulations=args.deep_cross_simulations,
                        seed=args.seed,
                    )
                    for scenario, first, second, maximum_rounds, _simulations
                    in segments
                ),
                backends=("native",),
                reference="numpy",
                candidate="counts",
                workers=args.workers,
                on_progress=progress.advance if progress is not None else None,
            )
        if progress is not None:
            progress.finish()
        by_case: dict[str, list] = {}
        for row in (() if matrix is None else matrix.rows):
            by_case.setdefault(row.case, []).append(row)
        for row in (() if cross is None else cross.rows):
            by_case.setdefault(row.case, []).append(row)
        deep_samples = tuple(
            statistical_result(row)
            for scenario, *_rest in segments
            for label in (f"matrix:{scenario.id}", f"cross:{scenario.id}")
            for row in by_case.get(label, ())
        )
        modular_duels = 0 if matrix is None else matrix.modular_duels
    truncation_samples = ()
    if args.truncations:
        from mordheim_combat_lab.verification.parity import TRUNCATION_HORIZONS
        truncation_progress = None if args.json else BenchmarkProgress(
            len(deep_scenarios) * len(TRUNCATION_HORIZONS)
        )
        rows: list = []
        for scenario in deep_scenarios:
            first, second = compile_benchmark_fighters(scenario)
            resolved_workers.update({
                f"{scenario.id}@rounds={horizon}": _resolve_workers(
                    args.workers, args.truncation_simulations, horizon)
                for horizon in TRUNCATION_HORIZONS
                if horizon <= scenario.maximum_rounds
            })
            run = run_parity(
                (
                    ParityCase(
                        label=scenario.id, first=first, second=second,
                        maximum_rounds=scenario.maximum_rounds,
                        simulations=args.truncation_simulations,
                        seed=args.seed,
                    ),
                ),
                backends=("numpy",),
                candidate="counts",
                workers=args.workers,
                horizons=TRUNCATION_HORIZONS,
                on_progress=(truncation_progress.advance
                             if truncation_progress is not None else None),
            )
            rows.extend(statistical_result(row) for row in run.rows)
        if truncation_progress is not None:
            truncation_progress.finish()
        truncation_samples = tuple(rows)
    complete = (
        report.complete
        and all(item.passed for item in statistical)
        and all(item.passed for item in deep_samples)
        and all(item.passed for item in truncation_samples)
        and not missing_backends
    )
    elapsed = time.perf_counter() - started
    from mordheim_combat_lab.provenance import run_provenance
    from mordheim_knowledge.paths import project_root

    provenance = run_provenance(
        project_root(),
        ("modular", *(certified_backends if (args.statistical or args.deep)
                      else ("numpy",) if args.truncations else ())),
    )
    payload = parity_report_payload(
        report, statistical, deep=deep_samples,
        truncations=truncation_samples, elapsed_seconds=elapsed,
        deep_pair_set=pair_set if args.deep else None,
        truncation_pair_set=pair_set if args.truncations else None,
        backends={
            "requested": (list(requested_backends) if requested_backends is not None
                          else "installed"),
            "available": list(installed_backends),
            "certified": list(certified_backends) if (args.statistical or args.deep) else [],
            "missing": list(missing_backends),
        },
        provenance=provenance,
        oracle_workers={
            "requested": args.workers if args.workers is not None else "auto",
            "environment": os.environ.get("MORDHEIM_PARALLEL_ORACLE_WORKERS"),
            "resolved": resolved_workers,
        },
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
        for divergence in report.divergences:
            print(f"DIVERGENCE: {divergence}")
        for pending in report.pending:
            print(f"PENDING: {pending}")
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
                    "cross-backend certification skipped ("
                    + ("native backend is not compiled in this environment"
                       if "native" not in installed_backends
                       else "native backend not requested")
                    + ")"
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
    if missing_backends:
        print(
            "PARITY INCOMPLETE: requested backend(s) "
            f"{', '.join(missing_backends)} unavailable (available: "
            f"{', '.join(installed_backends)}); certificate marked incomplete.",
            file=sys.stderr,
        )
        return 1
    return int(bool(args.require_complete and not complete))


def test_report_command(args) -> int:
    """Generate technical results and optionally statistical parity results."""
    from collections import Counter
    import csv
    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_combat_lab.verification.reporting import generate_test_report
    from mordheim_combat_lab.report_naming import timestamped_report_path

    started = time.perf_counter()
    output = (Path(args.output).resolve() if args.output else
              timestamped_report_path("outputs", "test-report", "")).resolve()
    progress = BenchmarkProgress(len(benchmark_scenarios())) if args.statistical else None
    statistical_path, technical_path, rows, technical_exit = generate_test_report(
        output, statistical=args.statistical, simulations=args.statistical_simulations,
        seed=args.seed, workers=args.workers,
        on_progress=progress.advance if progress is not None else None,
    )
    if progress is not None:
        progress.finish()
    statistical_counts = Counter(str(row.get("passes", "")) for row in rows)
    with technical_path.open("r", encoding="utf-8-sig", newline="") as stream:
        technical_rows = tuple(csv.DictReader(stream, delimiter=";"))
    technical_counts = Counter(str(row.get("status", "")) for row in technical_rows)
    if statistical_path is not None:
        print("statistical: " + ", ".join(
            f"{status}={statistical_counts.get(status, 0)}"
            for status in ("PASS", "FAIL", "PENDING", "OUT_OF_SCOPE")
        ))
        print(f"STATISTICAL REPORT: {statistical_path}")
    print("technical: " + ", ".join(
        f"{status}={technical_counts.get(status, 0)}"
        for status in ("PASS", "FAIL", "ERROR", "SKIP", "XFAIL", "XPASS", "NOT_RUN")
    ))
    print(f"TECHNICAL REPORT: {technical_path}")
    print(f"Elapsed: {time.perf_counter() - started:.2f}s")
    failed = statistical_counts.get("FAIL", 0) > 0
    incomplete = statistical_counts.get("PENDING", 0) > 0
    return int(bool(technical_exit or failed or (args.require_complete and incomplete)))


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
    except RuntimeError as error:
        print(f"Coverage gate error: {error}", file=sys.stderr)
        return 1
    budget_path = Path(args.budget).resolve()
    if args.update_budget:
        result = coverage_gate.evaluate(report, None, minimum_percent=floors)
        if result.passed:
            coverage_gate.write_budget(budget_path, report)
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
        if args.update_budget and result.passed:
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

    paths = generate_audit(
        knowledge=Path(args.knowledge).resolve() if args.knowledge else None,
        specs=Path(args.specs).resolve() if args.specs else None,
        output=Path(args.output).resolve() if args.output else None,
        scope=args.scope, status=args.status, review_status=args.review_status,
        inventory_only=args.inventory_only, t13=args.t13, family=args.family, work_status=args.work_status,
    )
    for path in paths:
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
        "verify", help="validate KB structure and default construction",
        description="Validate the knowledge base and its structural connections "
                    "(editorial schemas, execution contract, default profile "
                    "compilation). Game rules are checked by the modular "
                    "mechanics and E2E suites.",
        formatter_class=_HelpFormatter)
    verify_paths = verification.add_argument_group("paths")
    verify_paths.add_argument("--knowledge", metavar="PATH",
                              help="override the knowledge base location")
    verify_layers = verification.add_argument_group("layers")
    verify_layers.add_argument("--structural", action="store_true",
                               help="compatibility option; verification is structural only")
    verify_output = verification.add_argument_group("output and strictness")
    verify_output.add_argument("--inventory", action="store_true",
                               help="print the rule inventory as JSON and exit")
    verify_output.add_argument("--json", action="store_true",
                               help="print the verification payload as JSON")
    verify_output.add_argument("--require-complete", action="store_true",
                               help="compatibility option; structural errors always fail")
    verification.set_defaults(handler=verify_command)

    audit = commands.add_parser(
        "audit", help="generate the auditable rule inventory",
        description="Generate separate combat-mechanic and editorial-rule CSVs "
                    "under outputs/audit, with timestamped names by default.",
        formatter_class=_HelpFormatter)
    audit_paths = audit.add_argument_group("paths")
    audit_paths.add_argument("--knowledge", metavar="PATH",
                             help="override the knowledge base location")
    audit_paths.add_argument("--specs", metavar="PATH",
                             help="override the structural specifications directory")
    audit.add_argument("--inventory-only", action="store_true", help="compatibility option; audit exports inventory only")
    audit.add_argument("--historical-origins", "--t13", dest="t13", action="store_true",
                       help="restrict to historical plan origins (the legacy --t13 spelling is still accepted)")
    audit.add_argument("--family", help="filter by a mechanism family")
    audit.add_argument("--work-status", choices=("needs_target_reconciliation", "needs_classification", "excluded", "deferred_scope_review", "needs_ruling", "needs_question_review", "implementation_required", "implemented_pending_verification", "verified_modular"))
    audit_filters = audit.add_argument_group("filters")
    audit_filters.add_argument("--scope", choices=("YES", "NO", "LATER", "UNCLASSIFIED"),
                               help="filter by scope classification")
    audit_filters.add_argument("--status", choices=("verified", "pending", "out_of_scope", "unclassified", "deferred", "not_run"),
                               help="filter by semantic status")
    audit_filters.add_argument("--review-status",
                               choices=("ready", "blocked_by_dependency", "needs_ruling",
                                        "verified", "not_applicable", "needs_classification", "deferred"),
                               help="filter by review status; needs_ruling surfaces "
                                    "the unanswered review questions")
    audit_output = audit.add_argument_group("output")
    audit_output.add_argument("--output", metavar="PATH",
                              help="output directory for both CSVs (default: outputs/audit)")
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
        "--budget", default="tests/tooling/coverage/fixtures/budget.json", metavar="PATH",
        help="coverage budget file to check against (default: "
             "tests/tooling/coverage/fixtures/budget.json)")
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
        epilog="Measurement procedure and the baseline-gate workflow live in "
               "docs/guides/develop-and-release.md; measured optima are "
               "machine-local (performance calibrate).",
        formatter_class=_HelpFormatter)
    run_options = benchmark.add_argument_group("run configuration")
    run_options.add_argument("-n", "--simulations", type=_positive, default=100,
                             metavar="DUELS",
                             help="simulations per scenario and engine (the small "
                                  "default is a smoke run; pass real sizes for "
                                  "measurements)")
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
        "--scenario", nargs="+",
        choices=("all", *deep_scenario_ids),
        default=("all",), metavar="ID",
        help="scenario/pair ids to measure (one or more); defaults to the small "
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
        help="pair set for --deep and --tts workloads: mini is the small "
             "performance-survey set; fast is the normal coverage-oriented set "
             "for a roughly 10-15 minute pooled profile; full is the 43-pair "
             "matrix (deep sweeps default to full)",
    )
    deep_options.add_argument(
        "--deep-modular-simulations", type=_positive, default=10_000, metavar="DUELS",
        help="duels per scenario for the modular reference point in --deep mode",
    )
    deep_options.add_argument(
        "--processes", type=_positive, default=1, metavar="N",
        help="run the scenario measurements through a process pool of N workers "
             "and report the pool's wall time and sample concurrency (not a "
             "speedup over a sequential run); N is part of the measurement "
             "design, so a baseline gate requires the same N; 1 keeps the "
             "historical sequential execution",
    )
    tts_options = benchmark.add_argument_group("time to solution")
    tts_options.add_argument(
        "--tts", action="store_true",
        help="time-to-solution study: run every (simulation size x batch size) "
             "cell of the workload through every applicable (strategy x "
             "backend) combination, including the modular oracle, and rank "
             "them by total wall time (spawns included); --pair-set selects "
             "the combat-type workload, --simulation-sizes and --batch-sizes "
             "the grid (modular ignores the batch axis and runs once per "
             "size), --repeats the per-cell median; within a backend the "
             "identical duel streams double as a parity gate across strategies",
    )
    tts_options.add_argument(
        "--strategies", metavar="LIST",
        help="comma separated strategies for --tts: sequential (one process), "
             "processes=N (one scenario per worker), parallel=N (each scenario "
             "split inside a pool of N: numpy splits its batch plan, modular "
             "its duel range) and parallel=N:C (modular only: split into C "
             "chunks over N workers) (default: sequential,processes=4,parallel=4)",
    )
    profile_options = benchmark.add_argument_group("profiling")
    profile_options.add_argument(
        "--profile", action="store_true",
        help="run the timed repeats under cProfile, print each backend's top "
             "functions and write per-backend .pstats files; single-"
             "configuration sequential runs only, and the profiled timings "
             "cannot feed a baseline gate (instrumentation slows the engine)",
    )
    profile_options.add_argument(
        "--profile-output", metavar="DIR", default="outputs/benchmarks",
        help="directory for the profile-<backend>-<timestamp>.pstats files",
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
    catalog_options = parity.add_argument_group("fixture catalogues")
    catalog_options.add_argument(
        "--catalog", choices=("precompiled", "battery", "all", "e2e"), default=None,
        help="select frozen cases, build-based battery cases, both, or explicitly selected precompiled E2E deliveries (--e2e); without --profile all cases are selected",
    )
    catalog_options.add_argument(
        "--simulations", type=_positive, default=None, metavar="DUELS",
        help="with --catalog, override samples per case; otherwise use --statistical-simulations for frozen scenarios or the battery row count",
    )
    e2e_options = parity.add_argument_group("precompiled E2E connection")
    e2e_options.add_argument(
        "--e2e", action="append", default=[], metavar="CASE_KEY",
        help="with --catalog e2e, a delivery case_key or audit_id::id "
             "(repeatable; the selection is always explicit)",
    )
    e2e_options.add_argument(
        "--e2e-selection-file", metavar="PATH",
        help="with --catalog e2e, read one case_key or audit_id::id per "
             "line ('#' comments allowed)",
    )
    e2e_options.add_argument(
        "--e2e-deliveries", metavar="DIR",
        help="with --catalog e2e, override the delivery directory",
    )
    e2e_options.add_argument(
        "--magnitudes", metavar="LIST", default=None,
        help="with --catalog e2e, comma-separated observed magnitudes: "
             "winner (mandatory), rounds; default winner. Deliveries declare winner only; "
             "this flag widens the campaign without rewriting them",
    )
    parity_samples = parity.add_argument_group("certification samples")
    parity_samples.add_argument(
        "--level", choices=("deterministic", "statistical", "deep", "small", "normal", "long", "e2e"),
        default=None, metavar="LEVEL",
        help="e2e selects all E2E deliveries; with --catalog: small (default), normal or long; otherwise historical certificate preset: "
             "deterministic runs the exact checks only; "
             "statistical adds the aggregate six-sigma samples on the small "
             "standard scenarios; deep runs the selected archetype pair set "
             "(fast or full) plus the numpy<->native cross at scale",
    )
    parity_samples.add_argument(
        "--pair-set", choices=("mini", "fast", "full"), default=None, metavar="SET",
        help="pair set for --deep/--truncations: mini is the small "
             "performance-survey set; fast is the normal "
             "coverage-oriented set for a roughly 10-15 minute pooled run; "
             "full is the 43-pair deep matrix (default)",
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
        help="processes for modular-oracle samples, including --profile "
             "quick|complete|deep; auto pools only samples estimated to take over ~20 s "
             "sequentially, 1 disables the pool (also from "
             "MORDHEIM_PARALLEL_ORACLE_WORKERS)",
    )
    parity_output = parity.add_argument_group("report and strictness")
    parity_output.add_argument("--json", action="store_true",
                               help="print the certificate as JSON")
    parity_output.add_argument("--require-complete", action="store_true",
                               help="fail unless the certificate is complete; with "
                                    "--profile a missing, incompatible or "
                                    "unexecuted scenario also fails")
    parity_output.add_argument("--output-md", metavar="PATH",
                               help="with the E2E catalogue, save a Markdown summary independently of --output")
    parity_output.add_argument("--output", metavar="PATH",
                               help="save the report as .json or .md (deep defaults to "
                                    "deep.json for full, deep-fast.json for fast "
                                    "or deep-mini.json for mini)")
    battery = parity.add_argument_group("renewed behaviour battery")
    battery.add_argument(
        "--profile", choices=("quick", "complete", "deep"), default=None,
        metavar="PROFILE",
        help="filter battery cases; with --catalog the default is the full deep profile; profiles are cumulative "
             "(quick is contained in complete, complete in deep) and default "
             "to the NumPy candidate",
    )
    battery.add_argument(
        "--backend", choices=("modular", "numpy", "native", "all"), default=None,
        metavar="ENGINE",
        help="modular runs only the reference (defaults to --catalog all); numpy, native "
             "(never falls back to NumPy) or all. Statistical defaults to "
             "installed backends; explicit native/all requires native. "
             "Deep defaults to installed backends; explicit native/all "
             "without native marks the certificate incomplete (exit 1). "
             "Profiles default to numpy and report availability per backend",
    )
    battery.add_argument(
        "--rows", type=_positive, default=None, metavar="DUELS",
        help="override the sample width of every battery case for --profile; "
             "the declared width stays the default. Combine it with "
             "--require-complete for an acceptance run: a case is approved only "
             "when its width can detect a 5-point shift (at least 7200 rows); "
             "the certificate records the override",
    )
    parity.set_defaults(handler=parity_command)

    test_report = commands.add_parser(
        "test-report", help="generate the human-readable parity and technical test CSVs",
        description="Generate technical-test CSVs and optional statistical parity "
                    "results into an output directory.",
        formatter_class=_HelpFormatter)
    test_report_content = test_report.add_argument_group("content")
    test_report_content.add_argument("--statistical", action="store_true",
                                     help="also generate the statistical parity CSV")
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
                                    help="directory for generated CSVs (default: outputs/test-report)")
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
                                        "(default: full, all 43 scenarios)")
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
                                     help="simulations per fighter in the pool-worker sweep; "
                                          "numpy uses half, and the sample is raised so the "
                                          "largest worker candidate gets one batch per worker "
                                          "(default: 1000000)")
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
