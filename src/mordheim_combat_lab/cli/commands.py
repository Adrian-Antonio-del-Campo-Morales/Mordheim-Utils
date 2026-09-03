"""Development and application commands; heavy imports stay local."""
from argparse import ArgumentParser
from dataclasses import asdict
from pathlib import Path
import json
import sys


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


def validate_command(args) -> int:
    from mordheim_construction.compiler import compile_fighter
    from mordheim_construction.contracts import validate_execution_contract
    from mordheim_core.models import FighterBuild
    from mordheim_knowledge.loader import load_bands
    from mordheim_combat_lab.verification.structural import audit_phase_verification

    knowledge = Path(args.knowledge).resolve() if args.knowledge else None
    specs = Path(args.specs).resolve() if args.specs else None
    errors = list(validate_execution_contract("mordheim", knowledge))
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
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"structural_complete=True; {compiled} profiles compile with their default construction")
    print("Semantic status is separate: use `python -m mordheim_combat_lab verify --require-complete`.")
    return 0


def verify_command(args) -> int:
    from mordheim_knowledge.loader import knowledge_root
    from mordheim_combat_lab.verification.audit import verify_semantics
    from mordheim_combat_lab.verification.inventory import inventory
    from mordheim_combat_lab.verification.structural import audit_phase_verification

    knowledge = Path(args.knowledge).resolve() if args.knowledge else knowledge_root()
    specs = Path(args.specs).resolve() if args.specs else None
    if args.inventory:
        print(json.dumps([asdict(item) for item in inventory(knowledge)],
                         ensure_ascii=True, indent=2))
        return 0
    structural = audit_phase_verification("mordheim", knowledge, specs)
    semantic = verify_semantics(knowledge, specs)
    payload = {"structural_complete": structural.structural_complete,
               "structural_errors": structural.errors,
               "semantic_complete": semantic.semantic_complete, **asdict(semantic)}
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
    else:
        print(f"structural_complete={structural.structural_complete}")
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
        for error in (*structural.errors, *semantic.errors):
            print(f"FAIL: {error}")
        if semantic.pending:
            print("PENDING: use --json for the effect-by-effect backlog.")
    return int(bool(structural.errors or semantic.errors or
                    args.require_complete and not semantic.semantic_complete))


def benchmark_command(args) -> int:
    from mordheim_combat_lab.cli.benchmarking import BenchmarkProgress
    from mordheim_combat_lab.cli.benchmarking import benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_combat_lab.cli.benchmarking import compare_with_baseline
    from mordheim_combat_lab.cli.benchmarking import load_benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import parse_sizes
    from mordheim_combat_lab.cli.benchmarking import print_gate
    from mordheim_combat_lab.cli.benchmarking import print_results_table
    from mordheim_combat_lab.cli.benchmarking import print_sweep_table
    from mordheim_combat_lab.cli.benchmarking import run_benchmark
    from mordheim_combat_lab.cli.benchmarking import sweep_payload
    from mordheim_combat_lab.cli.benchmarking import write_benchmark_payload
    from mordheim_combat_lab.cli.benchmarking import write_report
    from mordheim_combat.vectorized import available_backends

    sweep = args.simulation_sizes is not None or args.batch_sizes is not None
    if sweep and (args.baseline or args.save_baseline or args.require_improvement):
        print("Benchmark configuration error: --baseline/--save-baseline and "
              "--require-improvement apply to single-configuration runs only",
              file=sys.stderr)
        return 2
    if args.require_improvement and not args.baseline:
        print("Benchmark baseline error: --require-improvement requires --baseline",
              file=sys.stderr)
        return 2

    scenarios = benchmark_scenarios()
    if args.scenario != "all":
        scenarios = tuple(item for item in scenarios if item.id == args.scenario)
    backends = ("modular", "numpy", "native") if args.backend == "all" else (args.backend,)
    installed = available_backends()
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
    results = []
    unavailable = []
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
    if progress is not None:
        progress.finish()

    if sweep:
        payload = sweep_payload(
            results, unavailable, simulation_sizes=simulation_sizes,
            batch_sizes=batch_sizes, seed=args.seed, warmups=args.warmups,
            repeats=args.repeats,
        )
        if args.output:
            write_report(Path(args.output), payload)
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2))
        else:
            print_sweep_table(
                results, unavailable, simulation_sizes=simulation_sizes,
                batch_sizes=batch_sizes, seed=args.seed, repeats=args.repeats,
            )
            if args.output:
                print(f"Report: {Path(args.output).resolve()}")
        return 0

    payload = benchmark_payload(
        results, unavailable, simulations=args.simulations,
        batch_size=args.batch_size, seed=args.seed, warmups=args.warmups,
        repeats=args.repeats,
    )
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
        if gate is not None:
            print_gate(gate, improvement=args.min_improvement,
                       regression=args.max_regression)
        if args.output:
            print(f"Report: {Path(args.output).resolve()}")
        if args.save_baseline:
            print(f"Baseline: {Path(args.save_baseline).resolve()}")
    return int(bool(args.require_improvement and (gate is None or not gate.passed)))


def parity_command(args) -> int:
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
    from mordheim_construction.compiler import compile_fighter
    from mordheim_combat_lab.verification.parity import compare_statistical_parity
    from mordheim_combat_lab.verification.parity import parity_report_markdown
    from mordheim_combat_lab.verification.parity import parity_report_payload
    from mordheim_combat_lab.verification.parity import verify_vectorized_parity
    from mordheim_combat_lab.verification.parity import verify_specification_parity

    report = verify_vectorized_parity()
    specification_report = verify_specification_parity()
    statistical = ()
    if args.statistical:
        from mordheim_combat.vectorized import available_backends
        from mordheim_combat.modular.duel import simulate_duel_reference

        installed = available_backends()
        samples: list = []
        for scenario in benchmark_scenarios():
            first, second = (
                compile_fighter(scenario.first), compile_fighter(scenario.second),
            )
            # One modular oracle sample certifies every optimized candidate;
            # `backend` records which engine produced each comparison.
            modular = simulate_duel_reference(
                first, second, args.statistical_simulations, seed=args.seed,
                maximum_rounds=scenario.maximum_rounds,
            )
            samples.append(compare_statistical_parity(
                scenario.id, first, second, args.statistical_simulations, seed=args.seed,
                maximum_rounds=scenario.maximum_rounds, modular=modular, backend="numpy",
            ))
            if "native" in installed:
                samples.append(compare_statistical_parity(
                    scenario.id, first, second, args.statistical_simulations, seed=args.seed,
                    maximum_rounds=scenario.maximum_rounds, modular=modular, backend="native",
                ))
        statistical = tuple(samples)
    complete = (
        report.complete and specification_report.complete
        and all(item.passed for item in statistical)
    )
    payload = parity_report_payload(report, statistical, specification_report)
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
                f"{'PASS' if item.passed else 'FAIL'} ({item.simulations:,} duels/engine)"
            )
        if args.output:
            print(f"REPORT: {Path(args.output).resolve()}")
    return int(bool(args.require_complete and not complete))


def test_report_command(args) -> int:
    import csv
    from collections import Counter
    from mordheim_combat_lab.verification.test_reporting import generate_test_report

    semantic_path, technical_path, semantic_rows, technical_exit = generate_test_report(
        Path(args.output).resolve(), statistical=args.statistical,
        simulations=args.statistical_simulations, seed=args.seed,
    )
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
    semantic_failed = semantic_counts.get("FAIL", 0) > 0
    incomplete = semantic_counts.get("PENDING", 0) > 0
    return int(bool(technical_exit or semantic_failed or (args.require_complete and incomplete)))


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


def ui_command(_args) -> int:
    from mordheim_combat_lab.ui.app import main
    return int(main() or 0)


def build_parser(prog: str = "mordheim-combat-lab") -> ArgumentParser:
    parser = ArgumentParser(prog=prog)
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("ui", help="open the graphical interface").set_defaults(handler=ui_command)
    validation = commands.add_parser("validate", help="validate the KB and structural connections")
    validation.add_argument("--knowledge")
    validation.add_argument("--specs")
    validation.set_defaults(handler=validate_command)
    verification = commands.add_parser(
        "verify", help="run the semantic specifications against the modular engine")
    verification.add_argument("--knowledge")
    verification.add_argument("--specs")
    verification.add_argument("--inventory", action="store_true")
    verification.add_argument("--json", action="store_true")
    verification.add_argument("--require-complete", action="store_true")
    verification.set_defaults(handler=verify_command)
    audit = commands.add_parser("audit", help="generate the auditable rule inventory")
    audit.add_argument("--knowledge")
    audit.add_argument("--specs")
    audit.add_argument("--output")
    audit.add_argument("--scope", choices=("YES", "NO", "LATER"))
    audit.add_argument("--status", choices=("verified", "pending", "out_of_scope"))
    audit.add_argument("--review-status",
                       choices=("ready", "blocked_by_dependency", "needs_ruling",
                                "verified", "not_applicable"),
                       help="filter by review status; needs_ruling surfaces unanswered 100_000s")
    audit.set_defaults(handler=audit_command)
    benchmark = commands.add_parser("benchmark", help="measure the combat engines")
    benchmark.add_argument("-n", "--simulations", type=_positive, default=100_000,
                           help="simulations per scenario and engine")
    benchmark.add_argument("--seed", type=int, default=2026)
    benchmark.add_argument("--batch-size", type=_positive, default=100_000,
                           help="batch size for the vectorized and native engines")
    benchmark.add_argument(
        "--simulation-sizes",
        help="comma/space separated simulation counts, e.g. 1k,10k,100k (sweep mode)")
    benchmark.add_argument(
        "--batch-sizes",
        help="comma/space separated batch sizes, e.g. 10k,100k (sweep mode)")
    benchmark.add_argument(
        "--backend", choices=("all", "modular", "numpy", "native"), default="all",
        help="engines to measure; by default modular, vectorized and native are measured separately",
    )
    benchmark.add_argument(
        "--scenario",
        choices=("all", "basic", "multiattack", "defences", "stateful", "long"),
        default="all",
    )
    benchmark.add_argument(
        "--warmups", type=int, choices=range(0, 101), default=1,
        help="warm-up runs per configuration (0-100)",
    )
    benchmark.add_argument("--repeats", type=_positive, default=5)
    benchmark.add_argument("--json", action="store_true")
    benchmark.add_argument("--output",
                           help="save this run as a report (.json, or .csv/.md in sweep mode)")
    benchmark.add_argument("--save-baseline",
                           help="save this single-configuration run as a JSON baseline")
    benchmark.add_argument("--baseline",
                           help="compare against a previous single-configuration JSON baseline")
    benchmark.add_argument(
        "--require-improvement", action="store_true",
        help="fail unless some scenario improves and none exceeds the allowed regression",
    )
    benchmark.add_argument("--min-improvement", type=_percentage, default=10.0)
    benchmark.add_argument("--max-regression", type=_percentage, default=5.0)
    benchmark.set_defaults(handler=benchmark_command)
    parity = commands.add_parser(
        "parity", help="certify the vectorized engine against the modular oracle")
    parity.add_argument("--json", action="store_true")
    parity.add_argument("--require-complete", action="store_true")
    parity.add_argument("--statistical", action="store_true",
                        help="add aggregate six-sigma statistical certification samples")
    parity.add_argument("--statistical-simulations", type=_positive, default=100_000)
    parity.add_argument("--seed", type=int, default=2026)
    parity.add_argument("--output", help="save the report as .json or .md")
    parity.set_defaults(handler=parity_command)
    test_report = commands.add_parser(
        "test-report", help="generate the human-readable parity and technical test CSVs")
    test_report.add_argument("--output", default="outputs/test-report")
    test_report.add_argument("--statistical", action="store_true")
    test_report.add_argument("--statistical-simulations", type=_positive, default=100_000)
    test_report.add_argument("--seed", type=int, default=2026)
    test_report.add_argument("--require-complete", action="store_true")
    test_report.set_defaults(handler=test_report_command)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        return ui_command(args)
    if getattr(args, "inventory", False) and getattr(args, "require_complete", False):
        parser.error("--inventory and --require-complete cannot be combined")
    return args.handler(args)
