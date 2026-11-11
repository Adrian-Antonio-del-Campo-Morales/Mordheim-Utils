"""Development and application commands; heavy imports stay local."""
from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path
import json
import os
import sys
import time

from mordheim_combat_lab.cli.options import add_scenarios, size, sizes
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


def _scenario_label(args, default: str | None = None) -> str | None:
    """The ``--scenarios`` values as given, for report labels and filenames."""
    values = getattr(args, "scenarios", None)
    return " ".join(values) if values else default



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

    errors, compiled = _structural_errors(knowledge_root())
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


def _tts_benchmark_command(args, scenarios, label) -> int:
    """Time-to-solution study: run every (simulations x batch size) cell of
    the workload through every applicable (strategy x backend) combination
    and rank the combinations by the wall time of solving the cell
    completely. Within one backend every strategy executes the same duel
    streams, so their totals cross-check as a parity gate."""
    from mordheim_combat_lab.cli.benchmarking import (
        BenchmarkProgress, parse_tts_strategies,
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
        print("Benchmark configuration error: --strategies compares execution "
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
    simulation_sizes = tuple(args.simulations)
    batch_sizes = tuple(args.batch_size)
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
        scenario_count=scenario_count, scenarios=label,
        elapsed_seconds=perf_counter() - command_started,
        parity=parity_report,
    )
    if args.output:
        write_report(Path(args.output), payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print_tts_study_summary(cells, scenarios=label)
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
    from mordheim_combat_lab.cli.benchmarking import benchmark_cases
    from mordheim_combat_lab.cli.benchmarking import benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import gate_against_baseline
    from mordheim_combat_lab.cli.benchmarking import load_benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import print_elapsed_summary
    from mordheim_combat_lab.cli.benchmarking import print_gate
    from mordheim_combat_lab.cli.benchmarking import print_results_table
    from mordheim_combat_lab.cli.benchmarking import print_sweep_table
    from mordheim_combat_lab.cli.benchmarking import run_benchmark
    from mordheim_combat_lab.cli.benchmarking import sweep_payload
    from mordheim_combat_lab.cli.benchmarking import write_report
    from mordheim_combat.vectorized import available_backends

    def refuse(message: str) -> int:
        print(f"Benchmark configuration error: {message}", file=sys.stderr)
        return 2

    sweep = len(args.simulations) > 1 or len(args.batch_size) > 1
    gated = args.baseline or args.require_improvement is not None
    if args.require_improvement is not None and not args.baseline:
        return refuse("--require-improvement needs --baseline")
    if gated and (sweep or args.strategies):
        return refuse("a --baseline gate compares one configuration: give one "
                      "--simulations and --batch-size value and no --strategies")
    if args.strategies and args.processes > 1:
        return refuse("--strategies sets its own workers; drop --workers")
    if args.profile and (sweep or args.strategies or args.processes > 1 or gated):
        return refuse("--profile measures one sequential configuration (no lists, "
                      "--strategies, --workers or gate): instrumentation slows the engine")

    try:
        scenarios, rejected = benchmark_cases(args.scenarios)
    except ValueError as error:
        return refuse(str(error))
    for key, reason in rejected:
        print(f"NOT RUN: {key}: {reason}", file=sys.stderr)
    if not scenarios:
        return refuse("none of the selected scenarios can run")
    if args.strategies:
        return _tts_benchmark_command(args, scenarios, _scenario_label(args))
    from time import perf_counter

    installed = available_backends()
    command_started = perf_counter()
    backends = tuple(args.backend)
    runnable_backends = tuple(
        backend for backend in backends
        if backend != "native" or backend in installed
    )
    simulation_sizes = tuple(args.simulations)
    batch_sizes = tuple(args.batch_size)
    units = (
        len(scenarios) * len(runnable_backends)
        * len(simulation_sizes) * len(batch_sizes) * (args.warmups + args.repeats)
    )
    progress = None if args.json else BenchmarkProgress(units)
    unavailable = [{"scenario": key, "reason": reason} for key, reason in rejected]
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
                            fighters=(scenario.first, scenario.second),
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
                Path(args.output).parent if args.output else Path("outputs/benchmarks"),
                f"profile-{backend}", ".pstats")
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

    simulations, batch_size = args.simulations[0], args.batch_size[0]
    improvement = 10.0 if args.require_improvement is None else args.require_improvement
    payload = benchmark_payload(
        results, unavailable, simulations=simulations,
        batch_size=batch_size, seed=args.seed, warmups=args.warmups,
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
                improvement_threshold=improvement / 100,
                regression_threshold=args.max_regression / 100,
            )
            payload["comparison"] = asdict(gate)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            print(f"Benchmark baseline error: {error}", file=sys.stderr)
            return 2
    if args.output:
        write_report(Path(args.output), payload)
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print_results_table(
            results, unavailable, simulations=simulations,
            batch_size=batch_size, seed=args.seed, repeats=args.repeats,
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
            print_gate(gate, improvement=improvement,
                       regression=args.max_regression)
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
    return int(args.require_improvement is not None and (gate is None or not gate.passed))


def _deterministic_parity(args) -> int:
    """The exact obligation checks of the vectorized engine (no sampling)."""
    from mordheim_combat_lab.verification.parity import (
        parity_report_markdown, parity_report_payload, verify_vectorized_parity,
    )

    started = time.perf_counter()
    report = verify_vectorized_parity()
    payload = parity_report_payload(report, elapsed_seconds=time.perf_counter() - started)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            parity_report_markdown(payload) if output.suffix.casefold() in {".md", ".markdown"}
            else json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(f"vectorized_parity_complete={report.complete}")
        print(f"{len(report.verified)}/{len(report.obligations)} obligations verified; "
              f"{len(report.pending)} pending; {len(report.divergences)} divergences")
        print(f"exact_checks={','.join(report.exact_checks)}")
        for divergence in report.divergences:
            print(f"DIVERGENCE: {divergence}")
        for pending in report.pending:
            print(f"PENDING: {pending}")
        if args.output:
            print(f"REPORT: {Path(args.output).resolve()}")
    return int(bool(args.require_complete and not report.complete))


def _parity_cases(entries, simulations: int, seed: int):
    """``ParityCase`` objects for the selected entries, plus the
    ``(key, rounds, status, reason)`` of every entry that cannot be prepared.

    A declared limitation -- a blocked or not-applicable E2E delivery, inputs
    no runner can express -- is ``INCOMPATIBLE`` (listed, not a failure); a
    missing frozen case or a preparation crash is ``NOT_RUN`` (a failure).
    """
    from mordheim_combat_lab.cli.scenarios import load_checkout_module
    from mordheim_combat_lab.verification.parity import ParityCase
    from mordheim_combat_lab.verification.parity import _battery_cases as battery
    from mordheim_core.dice import ScriptedDecisions

    catalog = load_checkout_module("tools.verification.parity_catalog")
    frozen, rejected = catalog.load([entry for entry in entries if entry.kind != "battery"])
    frozen = {item.key: item for item in frozen}
    rejected = dict(rejected)
    definitions = root = None
    prepared, failures = [], []
    for entry in entries:
        if entry.kind == "battery":
            # Battery cases may script decisions: the per-duel (observed)
            # surface passes them on, so this is the one tool that runs them.
            if definitions is None:
                from mordheim_construction.compiler import compile_fighter
                from mordheim_knowledge.loader import knowledge_root

                definitions = {str(case.id): case for case in battery.battery_cases()}
                root = knowledge_root()
            case = definitions[entry.name]
            limit = battery.input_limit(case)
            if limit is not None:
                failures.append((entry.key, case.maximum_rounds, "INCOMPATIBLE", limit))
                continue
            try:
                prepared.append(ParityCase(
                    label=entry.key,
                    first=compile_fighter(case.first, root),
                    second=compile_fighter(case.second, root),
                    maximum_rounds=case.maximum_rounds, simulations=simulations,
                    seed=seed, context=battery.resolve_context(case.context, root),
                    decisions=ScriptedDecisions(dict(case.decisions)),
                ))
            except Exception as error:  # an invalid case is not a divergence
                failures.append((entry.key, case.maximum_rounds, "NOT_RUN",
                                 f"Preparation failed: {type(error).__name__}: {error}"))
            continue
        if entry.key in rejected:
            reason = rejected[entry.key]
            status = "NOT_RUN" if reason.startswith("the frozen corpus has no case") else "INCOMPATIBLE"
            failures.append((entry.key, 50, status, reason))
            continue
        case = frozen[entry.key].case
        prepared.append(ParityCase(
            label=entry.key, first=case.first, second=case.second,
            maximum_rounds=case.limits.maximum_rounds, simulations=simulations,
            seed=seed, context=case.context,
        ))
    return prepared, failures


def _parity_markdown(payload: dict) -> str:
    lines = [
        "# Parity comparison", "",
        f"- Scenarios: `{' '.join(payload['scenarios'])}`",
        f"- Backends: `{', '.join(payload['backends'])}`",
        f"- Complete: `{payload['complete']}`; parity approved: `{payload['parity_approved']}`",
        "- Summary: " + ", ".join(f"{key} {value}" for key, value in payload["summary"].items()),
        "", "| Status | Case | Backend | Duels | Rounds | Detail |", "|---|---|---|---:|---:|---|",
    ]
    for row in payload["results"]:
        detail = str(row["detail"]).replace("|", "&#124;").replace("\n", "<br>")
        lines.append(f"| {row['status']} | {row['case']} | {row['backend']} | "
                     f"{row['simulations']:,} | {row['maximum_rounds']} | {detail} |")
    return "\n".join(lines) + "\n"


def _compare_parity(args, entries, backends: tuple[str, ...]) -> int:
    """Compare scenario and battery entries with the modular oracle."""
    from dataclasses import replace as _replace

    from mordheim_combat_lab.verification.parity import ParityRow, run_parity
    from mordheim_combat_lab.verification.parity._report import UNDERPOWERED, power_verdict
    from mordheim_combat_lab.verification.parity._runner import NATIVE_OBSERVED_NOTE
    from mordheim_combat_lab.verification.parity._statistical import MAX_DETECTABLE_DIFFERENCE

    from mordheim_combat_lab.provenance import run_provenance
    from mordheim_knowledge.paths import project_root

    started = time.perf_counter()
    provenance = run_provenance(project_root(), ("modular", *backends))
    prepared, failures = _parity_cases(entries, args.simulations, args.seed)
    if args.rounds:
        # Each value replaces the case's own limit, exactly as the samplers'
        # --rounds does; a list runs the case once per limit.
        prepared = [
            _replace(case, label=case.label if len(args.rounds) == 1
                     else f"{case.label}@rounds={limit}", maximum_rounds=limit)
            for case in prepared for limit in args.rounds
        ]
        failures = [(key, limit, status, detail) for key, _rounds, status, detail in failures
                    for limit in args.rounds]
    completed, total = 0, len(prepared)

    def progress():
        nonlocal completed
        completed += 1
        if not args.json:
            print(f"Sampled {completed}/{total}", flush=True)

    run = run_parity(
        prepared, backends=backends, candidate="observed", workers=args.workers,
        seed=args.seed, on_progress=progress,
    )

    def powered(row):
        # A passing row too small to detect the maximum detectable difference
        # is UNDERPOWERED: not approved, not complete, not a failure.
        status, approved, detail = power_verdict(row)
        return row if status == row.status else _replace(
            row, status=status, approved=approved, detail=detail)

    positions = {entry.key: index for index, entry in enumerate(entries)}
    rows = [powered(row) for row in run.rows] + [
        ParityRow(case=key, backend=backend, maximum_rounds=rounds,
                  simulations=args.simulations, status=status, detail=detail)
        for key, rounds, status, detail in failures for backend in backends
    ]
    rows.sort(key=lambda row: (positions.get(row.case.split("@rounds=")[0], len(positions)),
                               row.maximum_rounds))
    reference_only = backends == ("modular",)
    success = "COMPLETED" if reference_only else "PASS"
    measured = [row for row in rows if row.status != "INCOMPATIBLE"]
    summary = {
        "completed": sum(row.status == "COMPLETED" for row in rows),
        "passed": sum(row.status == "PASS" for row in rows),
        "failed": sum(row.status not in {"COMPLETED", "PASS", "INCOMPATIBLE", UNDERPOWERED}
                      for row in rows),
        "blocked": sum(row.status == "INCOMPATIBLE" for row in rows),
        "underpowered": sum(row.status == UNDERPOWERED for row in rows),
    }
    payload = {
        "scenarios": list(args.scenarios), "backends": list(backends),
        "reference_only": reference_only,
        # A declared limitation is not a failure, but it leaves the run
        # incomplete: --require-complete fails unless every case passed.
        "complete": bool(rows) and all(row.status == success for row in rows),
        "parity_approved": not reference_only and bool(rows) and all(row.approved for row in rows),
        "summary": summary, "modular_duels": run.modular_duels,
        "max_detectable_difference": MAX_DETECTABLE_DIFFERENCE,
        "backend_notes": {"native": NATIVE_OBSERVED_NOTE} if "native" in backends else {},
        "elapsed_seconds": time.perf_counter() - started,
        "provenance": provenance,
        "results": [
            {**asdict(row), "minimum_detectable_difference": row.minimum_detectable_difference}
            for row in rows
        ],
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            _parity_markdown(payload) if output.suffix.casefold() in {".md", ".markdown"}
            else json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8")
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        for row in rows:
            print(f"{row.status}: {row.case} [{row.backend}] n={row.simulations} "
                  f"rounds={row.maximum_rounds} {row.detail}".rstrip())
        print("Summary: " + ", ".join(f"{key}={value}" for key, value in summary.items()))
        if summary["underpowered"]:
            print(f"{summary['underpowered']} row(s) UNDERPOWERED: passed the gate with too "
                  f"few duels to detect a {MAX_DETECTABLE_DIFFERENCE} rate difference; "
                  "not approved, not complete.")
        if "native" in backends:
            print(f"Native rows: {NATIVE_OBSERVED_NOTE}.")
        if reference_only:
            print("Modular execution only: these results do not approve "
                  "statistical parity or rule correctness.")
        if args.output:
            print(f"REPORT: {Path(args.output).resolve()}")
    return int(not measured or summary["failed"] > 0 or (
        args.require_complete and not payload["complete"]))


def parity_command(args) -> int:
    """Dispatch ``parity``; a failed oracle worker pool is a failed run (exit 2)."""
    from mordheim_combat_lab.verification.parity._runner import ParityPoolError

    try:
        return _parity_command(args)
    except ParityPoolError as error:
        print(f"Parity run error: {error}", file=sys.stderr)
        return 2


def _parity_command(args) -> int:
    from mordheim_combat_lab.cli.scenarios import load_checkout_module

    def refuse(message: str) -> int:
        print(f"Parity configuration error: {message}", file=sys.stderr)
        return 2

    if not args.scenarios:
        return _deterministic_parity(args)
    backends = tuple(dict.fromkeys(args.backend))
    if "modular" in backends and len(backends) > 1:
        return refuse("--backend modular runs the reference alone; "
                      "name the candidates (numpy, native) without it")
    try:
        entries = load_checkout_module("tools.verification.parity_catalog").select(
            args.scenarios)
    except ValueError as error:
        return refuse(str(error))
    try:
        return _compare_parity(args, entries, backends)
    except ValueError as error:  # e.g. the E2E decision policies do not correspond
        return refuse(str(error))


def test_report_command(args) -> int:
    """Run the repository's tests and write the technical CSV."""
    from collections import Counter
    import csv
    from mordheim_combat_lab.verification.reporting import generate_test_report
    from mordheim_combat_lab.report_naming import timestamped_report_path

    started = time.perf_counter()
    output = (Path(args.output).resolve() if args.output else
              timestamped_report_path("outputs", "test-report", "")).resolve()
    technical_path, technical_exit = generate_test_report(output)
    with technical_path.open("r", encoding="utf-8-sig", newline="") as stream:
        counts = Counter(str(row.get("status", "")) for row in csv.DictReader(stream, delimiter=";"))
    print("technical: " + ", ".join(
        f"{status}={counts.get(status, 0)}"
        for status in ("PASS", "FAIL", "ERROR", "SKIP", "XFAIL", "XPASS", "NOT_RUN")
    ))
    print(f"TECHNICAL REPORT: {technical_path}")
    print(f"Elapsed: {time.perf_counter() - started:.2f}s")
    return int(bool(technical_exit))


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
    # Parsing never pre-loads mordheim_combat into sys.modules (which would
    # break the coverage-gate measurement): ``--scenarios`` values are
    # resolved by each command, after parsing.
    parser = ArgumentParser(prog=prog, formatter_class=_HelpFormatter)
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("ui", help="open the graphical interface",
                        formatter_class=_HelpFormatter).set_defaults(handler=ui_command)

    verification = commands.add_parser(
        "verify", help="validate KB structure and default construction",
        description="Validate the knowledge base and its structural connections "
                    "(editorial schemas, execution contract, default profile "
                    "compilation); structural errors fail.  Game rules are "
                    "checked by the modular mechanics and E2E suites.  Set "
                    "MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH to check another "
                    "knowledge base.",
        formatter_class=_HelpFormatter)
    verification.add_argument("--json", action="store_true",
                              help="print the verification payload as JSON")
    verification.set_defaults(handler=verify_command)

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
        help="pytest paths to measure (default: the deterministic engine suites)")
    coverage_content.add_argument(
        "--area-floor", action="append", metavar="AREA:PCT",
        help="minimum coverage percent per area, e.g. --area-floor modular:95 "
             "(repeatable)")
    coverage_output = coverage.add_argument_group("budget and output")
    coverage_output.add_argument(
        "--budget", default="tests/tooling/coverage/fixtures/budget.json", metavar="PATH",
        help="budget file to check against (default: the committed one)")
    coverage_output.add_argument(
        "--update-budget", action="store_true",
        help="write the measured covered lines as the new budget instead of "
             "checking the existing one")
    coverage_output.add_argument("--json", action="store_true",
                                help="print the machine-readable report as JSON")
    coverage.set_defaults(handler=coverage_gate_command)

    benchmark = commands.add_parser(
        "benchmark", help="measure the combat engines",
        description="Measure the combat engines (modular, NumPy, native).  One "
                    "--simulations and --batch-size value is a single "
                    "configuration that a --baseline can gate; comma lists sweep "
                    "every combination; --strategies compares execution "
                    "strategies (time to solution).",
        epilog="Measurement procedure and the baseline-gate workflow live in "
               "docs/guides/develop-and-release.md; measured optima are "
               "machine-local (performance calibrate).",
        formatter_class=_HelpFormatter)
    run_options = benchmark.add_argument_group("what runs")
    add_scenarios(run_options, default="small")
    run_options.add_argument(
        "--backend", choices=("modular", "numpy", "native"), nargs="+",
        default=("modular", "numpy", "native"), metavar="ENGINE",
        help="engines to measure (default: modular numpy native)")
    run_options.add_argument(
        "--simulations", type=sizes, default=(100,), metavar="N[,N...]",
        help="duels per scenario and engine; k/m suffixes; a list sweeps "
             "(default 100: a smoke size, pass real sizes for measurements)")
    run_options.add_argument(
        "--batch-size", type=sizes, default=(100_000,), metavar="N[,N...]",
        help="NumPy/native batch; a list sweeps (default: 100000)")
    run_options.add_argument("--seed", type=int, default=2026, help="random seed")
    run_options.add_argument(
        "--warmups", type=_warmups, default=1, metavar="N",
        help="untimed runs before timing (0-100, default: 1)")
    run_options.add_argument(
        "--repeats", type=_positive, default=5, metavar="N",
        help="timed runs; the median is reported (default: 5)")
    run_options.add_argument(
        "--workers", dest="processes", type=_positive, default=1, metavar="N",
        help="worker processes, one scenario per worker; reports the pool's "
             "wall time and concurrency, not a speedup (default: 1)")
    study = benchmark.add_argument_group("studies")
    study.add_argument(
        "--strategies", metavar="LIST",
        help="compare execution strategies by total wall time (time to "
             "solution): sequential, processes=N (one scenario per worker), "
             "parallel=N (each scenario split over N workers; modular and "
             "numpy) and parallel=N:C (modular split into C chunks); within an "
             "engine every strategy must reproduce the same totals",
    )
    study.add_argument(
        "--profile", action="store_true",
        help="run the timed repeats under cProfile, print each engine's top "
             "functions and save .pstats files beside --output (default "
             "outputs/benchmarks); profiled timings cannot feed a gate",
    )
    report_options = benchmark.add_argument_group("baseline gate and report")
    report_options.add_argument(
        "--baseline", metavar="PATH",
        help="compare with a saved single-configuration report (a former --output .json)")
    report_options.add_argument(
        "--require-improvement", nargs="?", const=10.0, type=_percentage,
        default=None, metavar="PCT",
        help="fail unless some scenario improves by PCT %% (default 10) and "
             "none regresses by more than --max-regression")
    report_options.add_argument(
        "--max-regression", type=_percentage, default=5.0, metavar="PCT",
        help="largest regression the gate allows, percent (default: 5)")
    report_options.add_argument(
        "--output", metavar="PATH",
        help="save the report: .json (also the file a later --baseline reads), "
             ".csv or .md")
    report_options.add_argument("--json", action="store_true",
                                help="print the report as JSON")
    benchmark.set_defaults(handler=benchmark_command)

    parity = commands.add_parser(
        "parity", help="compare the NumPy and native engines with the modular oracle",
        description="Compare the optimized engines with the modular oracle on "
                    "--scenarios with the six-sigma gate.  Without --scenarios "
                    "only the exact obligation checks run (no sampling).",
        formatter_class=_HelpFormatter)
    selection = parity.add_argument_group("what runs")
    add_scenarios(selection, default="none: only the exact obligation checks")
    selection.add_argument(
        "--backend", choices=("modular", "numpy", "native"), nargs="+",
        default=("numpy",), metavar="ENGINE",
        help="candidates compared with the oracle: numpy, native or both; "
             "modular alone only executes the oracle (default: numpy)")
    selection.add_argument(
        "--simulations", type=size, default=10_000, metavar="N",
        help="duels per scenario and engine; k/m suffixes; below 7200 a passing "
             "case is UNDERPOWERED, never approved (default: 10000)")
    selection.add_argument(
        "--rounds", type=sizes, default=None, metavar="N[,N...]",
        help="round limit replacing each scenario's own; a list compares every "
             "horizon, which shows defects in *when* duels resolve")
    selection.add_argument("--seed", type=int, default=2026, help="random seed")
    selection.add_argument(
        "--workers", type=_oracle_workers, metavar="N|auto",
        default=os.environ.get("MORDHEIM_PARALLEL_ORACLE_WORKERS", "auto"),
        help="worker processes for the modular oracle; auto pools only samples "
             "estimated over ~20 s, 1 disables the pool")
    parity_output = parity.add_argument_group("report")
    parity_output.add_argument(
        "--require-complete", action="store_true",
        help="fail unless every selected case passed (or, without --scenarios, "
             "every obligation is verified)")
    parity_output.add_argument("--output", metavar="PATH",
                               help="save the report as .json or .md")
    parity_output.add_argument("--json", action="store_true",
                               help="print the report as JSON")
    parity.set_defaults(handler=parity_command)

    test_report = commands.add_parser(
        "test-report", help="run the tests and write the technical test CSV",
        description="Run the repository's pytest suite and write an Excel-friendly "
                    "technical-tests.csv into the output directory.  Engine "
                    "comparisons belong to parity.",
        formatter_class=_HelpFormatter)
    test_report.add_argument(
        "--output", metavar="DIR",
        help="directory for the CSV (default: a timestamped outputs/test-report directory)")
    test_report.set_defaults(handler=test_report_command)

    calibration = commands.add_parser(
        "calibrate", help="measure this machine's engine optima and install the profile",
        description="Sweep every duel type in the deep matrix across batches, pooled "
                    "batches and worker counts on both engines, plus process-pool "
                    "spawn cost, and install a per-machine calibration profile the "
                    "Combat Lab loads at startup (batches, workers, spawn cost and "
                    "the pool speedup curve re-derived from the sweep evidence). "
                    "Default ~8-10 minutes; --scenarios small runs a ~2 minute survey.",
        epilog="Re-run after a hardware change, an engine update or new combat rules. "
               "The profile lives next to the preferences; --reset removes it.",
        formatter_class=_HelpFormatter)
    calibration_scope = calibration.add_argument_group("coverage")
    add_scenarios(calibration_scope,
                  default="big; the NumPy sweeps narrow big to normal, "
                          "because a NumPy duel costs 3-5x a native one")
    calibration_scope.add_argument("--seed", type=int, default=7,
                                   help="random seed for every sweep")
    calibration_measure = calibration.add_argument_group("measurement")
    calibration_measure.add_argument(
        "--simulations", type=size, default=500_000, metavar="N",
        help="duels per scenario in the native sequential sweep; the worker sweep "
             "runs twice as many and NumPy sweeps are sized from their batch "
             "candidates (default: 500000)")
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
    return args.handler(args)
