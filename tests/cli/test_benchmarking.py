from dataclasses import replace
import json

import pytest

from mordheim_combat_lab.cli.benchmarking import benchmark_payload
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import compare_with_baseline
from mordheim_combat_lab.cli.benchmarking import deep_benchmark_plan
from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
from mordheim_combat_lab.cli.benchmarking import load_benchmark_payload
from mordheim_combat_lab.cli.benchmarking import parse_sizes
from mordheim_combat_lab.cli.benchmarking import print_results_table
from mordheim_combat_lab.cli.benchmarking import print_sweep_table
from mordheim_combat_lab.cli.benchmarking import run_benchmark
from mordheim_combat_lab.cli.benchmarking import sweep_payload
from mordheim_combat_lab.cli.benchmarking import write_benchmark_payload
from mordheim_combat_lab.cli.benchmarking import write_report
from mordheim_combat_lab.cli.commands import build_parser
from mordheim_combat_lab.cli.commands import main


def test_benchmark_suite_has_the_five_required_scenarios():
    assert {item.id for item in benchmark_scenarios()} == {
        "basic", "multiattack", "defences", "stateful", "long",
    }


def test_deep_suite_extends_the_five_core_scenarios():
    ids = {item.id for item in deep_test_scenarios()}
    assert {item.id for item in benchmark_scenarios()} <= ids
    assert len(ids) >= 10  # the core five plus archetype matrix pairs


def test_deep_suite_scenarios_compile_into_legal_duels():
    from mordheim_construction.compiler import compile_fighter
    for scenario in deep_test_scenarios():
        compile_fighter(scenario.first)
        compile_fighter(scenario.second)


def test_deep_suite_includes_the_timing_and_parry_amplifiers():
    by_id = {item.id: item for item in deep_test_scenarios()}
    assert {
        "triple-weapon-vs-parry", "a2-vs-w1-stun", "frenzy-vs-w2",
        "durable-vs-elite", "heavy-grind",
    } <= set(by_id)
    # The grind pairs are the long 75-round budget, like the core ``long``.
    assert by_id["heavy-grind"].maximum_rounds == 75
    assert by_id["long"].maximum_rounds == 75
    # The amplifiers must keep the timing-prone signature alive: the heavy
    # grind is expected to leave a measurable share of duels unresolved.
    from mordheim_combat.modular.duel import simulate_duel_reference
    from mordheim_construction.compiler import compile_fighter
    scenario = by_id["heavy-grind"]
    result = simulate_duel_reference(
        compile_fighter(scenario.first), compile_fighter(scenario.second),
        2_000, seed=2026, maximum_rounds=scenario.maximum_rounds,
    )
    assert result.unresolved / 2_000 >= 0.05


def test_deep_benchmark_plan_keeps_modular_at_the_reference_size_only():
    scenarios = benchmark_scenarios()
    plan = deep_benchmark_plan(
        scenarios, vector_sizes=(1_000, 10_000), batch_sizes=(1_000, 10_000),
        modular_simulations=100, backends=("all",), installed=("numpy",),
    )
    assert plan.vector_backends == ("numpy",)
    assert plan.excluded[0]["backend"] == "native"
    modular_runs = [run for run in plan.runs if run[1] == "modular"]
    vector_runs = [run for run in plan.runs if run[1] != "modular"]
    assert len(modular_runs) == len(scenarios)
    assert all(run[2] == 100 for run in modular_runs)
    # The full numpy grid: every scenario x every size x every batch.
    assert len(vector_runs) == len(scenarios) * 2 * 2
    assert all(run[1] == "numpy" for run in vector_runs)
    assert {run[2] for run in vector_runs} == {1_000, 10_000}
    assert {run[3] for run in vector_runs} == {1_000, 10_000}
    assert all(run[2] >= 1_000 for run in vector_runs)


def test_deep_benchmark_plan_respects_backend_restriction():
    plan = deep_benchmark_plan(
        benchmark_scenarios()[:1], vector_sizes=(1_000,), batch_sizes=(1_000,),
        modular_simulations=100, backends=("numpy",), installed=("numpy", "native"),
    )
    assert plan.vector_backends == ("numpy",)


def test_deep_parser_defaults_and_guards():
    args = build_parser().parse_args(["benchmark", "--deep"])
    assert args.deep is True
    assert args.deep_simulation_sizes == "10k,100k,500k,1M,5M"
    assert args.deep_batch_sizes == "25k,100k,200k,500k"
    assert args.deep_modular_simulations == 10_000

    from mordheim_combat_lab.cli.commands import main
    assert main(["benchmark", "--deep", "--backend", "modular"]) == 2


def test_benchmark_reports_raw_samples_and_median():
    result = run_benchmark(
        benchmark_scenarios()[0], simulations=20, batch_size=20, seed=3,
        backend="numpy", warmups=0, repeats=2,
    )
    assert result.scenario == "basic"
    assert len(result.samples_seconds) == 2
    assert result.median_seconds > 0
    assert result.simulations_per_second > 0


def test_benchmark_can_measure_the_modular_engine():
    result = run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=2, seed=3,
        backend="modular", warmups=0, repeats=1,
    )
    assert result.backend == "modular"
    assert result.simulations_per_second > 0


def test_benchmark_notifies_progress_after_every_warmup_and_repeat():
    updates = []
    run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=2, seed=3,
        backend="numpy", warmups=1, repeats=2, on_progress=lambda: updates.append(True),
    )
    assert len(updates) == 3


def test_benchmark_defaults_to_all_engines():
    args = build_parser().parse_args(["benchmark"])
    assert args.backend == "all"


def test_benchmark_table_states_the_shared_simulation_count(capsys):
    scenario = benchmark_scenarios()[0]
    result = run_benchmark(
        scenario, simulations=2, batch_size=2, seed=3,
        backend="numpy", warmups=0, repeats=1,
    )
    print_results_table(
        [result], [], simulations=2, batch_size=2, seed=3, repeats=1,
    )
    output = capsys.readouterr().out
    assert "2 simulations per scenario and engine" in output
    assert "Scenario" in output
    assert "Engine" in output
    assert "Vectorized" in output
    assert "sim/s" in output
    assert "Median" in output


def test_benchmark_table_lists_unavailable_engines(capsys):
    print_results_table(
        [], [{"backend": "native", "reason": "backend is not compiled in this environment"}],
        simulations=2, batch_size=2, seed=3, repeats=1,
    )
    output = capsys.readouterr().out
    assert "native not available: backend is not compiled in this environment" in output


def test_parse_sizes_supports_suffixes_lists_and_defaults():
    assert parse_sizes("1k, 10k;100k", default=5) == (1_000, 10_000, 100_000)
    assert parse_sizes("2m", default=5) == (2_000_000,)
    assert parse_sizes("100000,100000", default=5) == (100_000,)
    assert parse_sizes(None, default=5) == (5,)
    assert parse_sizes("", default=5) == (5,)
    with pytest.raises(ValueError, match="invalid size token"):
        parse_sizes("ten", default=5)
    with pytest.raises(ValueError, match="must be positive"):
        parse_sizes("-5", default=5)


def test_sweep_payload_keeps_per_configuration_results():
    result = run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=1, seed=3,
        backend="numpy", warmups=0, repeats=1,
    )
    payload = sweep_payload(
        [result], [], simulation_sizes=(2,), batch_sizes=(1,), seed=3,
        warmups=0, repeats=1,
    )
    assert payload["schema"] == "mordheim-combat-benchmark-sweep/v1"
    assert payload["results"][0]["simulations"] == 2
    assert payload["results"][0]["batch_size"] == 1
    assert payload["results"][0]["median_seconds"] > 0


def test_sweep_report_writes_csv_and_markdown(tmp_path):
    result = run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=2, seed=3,
        backend="numpy", warmups=0, repeats=1,
    )
    payload = sweep_payload(
        [result], [], simulation_sizes=(2,), batch_sizes=(2,), seed=3,
        warmups=0, repeats=1,
    )
    csv_path = tmp_path / "sweep.csv"
    md_path = tmp_path / "sweep.md"
    write_report(csv_path, payload)
    write_report(md_path, payload)
    assert csv_path.read_text(encoding="utf-8").splitlines()[0].startswith("scenario;engine")
    assert "| scenario | engine |" in md_path.read_text(encoding="utf-8")
    assert "Vectorized" in md_path.read_text(encoding="utf-8")


def test_benchmark_report_round_trips_as_a_versioned_baseline(tmp_path):
    result = run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=2, seed=3,
        backend="numpy", warmups=0, repeats=1,
    )
    payload = benchmark_payload(
        [result], [], simulations=2, batch_size=2, seed=3, warmups=0, repeats=1,
    )
    path = tmp_path / "baseline.json"
    write_benchmark_payload(path, payload)
    loaded = load_benchmark_payload(path)
    assert loaded["schema"] == "mordheim-combat-benchmark/v1"
    assert loaded["results"][0]["scenario"] == "basic"
    assert loaded["environment"]["python"]


def test_performance_gate_requires_one_improvement_and_no_regressions():
    current = run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=2, seed=3,
        backend="numpy", warmups=0, repeats=1,
    )
    baseline = benchmark_payload(
        [replace(current, simulations_per_second=100.0)], [],
        simulations=2, batch_size=2, seed=3, warmups=0, repeats=1,
    )
    improved = compare_with_baseline(
        [replace(current, simulations_per_second=111.0)], baseline,
    )
    stable = compare_with_baseline(
        [replace(current, simulations_per_second=109.0)], baseline,
    )
    regressed = compare_with_baseline(
        [replace(current, simulations_per_second=94.9)], baseline,
    )
    assert improved.passed and improved.comparisons[0].status == "IMPROVED"
    assert not stable.passed and stable.comparisons[0].status == "STABLE"
    assert not regressed.passed and regressed.comparisons[0].status == "REGRESSED"

    second = replace(current, scenario="long", simulations_per_second=100.0)
    mixed_baseline = benchmark_payload(
        [replace(current, simulations_per_second=100.0), second], [],
        simulations=2, batch_size=2, seed=3, warmups=0, repeats=1,
    )
    mixed = compare_with_baseline([
        replace(current, simulations_per_second=120.0),
        replace(second, simulations_per_second=94.0),
    ], mixed_baseline)
    assert mixed.improved and mixed.regressed and not mixed.passed


def test_baseline_loader_rejects_unknown_schema(tmp_path):
    path = tmp_path / "old.json"
    path.write_text('{"schema":"old","results":[]}', encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported benchmark schema"):
        load_benchmark_payload(path)


def test_benchmark_parser_exposes_performance_gate_options():
    args = build_parser().parse_args([
        "benchmark", "--baseline", "before.json", "--require-improvement",
        "--min-improvement", "12", "--max-regression", "4",
    ])
    assert args.baseline == "before.json"
    assert args.require_improvement
    assert (args.min_improvement, args.max_regression) == (12.0, 4.0)


def test_benchmark_parser_exposes_sweep_sizes():
    args = build_parser().parse_args([
        "benchmark", "--simulation-sizes", "1k,10k", "--batch-sizes", "100,1k",
    ])
    assert args.simulation_sizes == "1k,10k"
    assert args.batch_sizes == "100,1k"


def test_sweep_mode_runs_and_prints_per_configuration_rows(capsys):
    assert main(["benchmark", "--simulation-sizes", "2", "--batch-sizes", "2",
                 "--scenario", "basic", "--backend", "numpy",
                 "--warmups", "0", "--repeats", "1", "--seed", "3"]) == 0
    output = capsys.readouterr().out
    assert "Benchmark sweep:" in output
    assert "2 simulations" in output
    assert "Vectorized" in output
    assert "sim/s" in output


def test_required_improvement_needs_a_baseline_without_running_benchmarks(capsys):
    assert main(["benchmark", "--require-improvement"]) == 2
    assert "requires --baseline" in capsys.readouterr().err


def test_gate_options_are_rejected_in_sweep_mode(capsys):
    assert main(["benchmark", "--simulation-sizes", "2",
                 "--baseline", "before.json"]) == 2
    assert "single-configuration" in capsys.readouterr().err


def test_sweep_table_mentions_all_configured_sizes(capsys):
    result = run_benchmark(
        benchmark_scenarios()[0], simulations=2, batch_size=2, seed=3,
        backend="numpy", warmups=0, repeats=1,
    )
    print_sweep_table(
        [result], [], simulation_sizes=(2, 4), batch_sizes=(2,), seed=3, repeats=1,
    )
    output = capsys.readouterr().out
    assert "2 simulations, 4 simulations" in output
    assert "batch sizes 2" in output


def test_deep_benchmark_saves_the_report_by_default(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert main(["benchmark", "--deep", "--simulation-sizes", "1k", "--batch-sizes", "1k",
                 "--scenario", "basic", "--backend", "numpy",
                 "--deep-modular-simulations", "100", "--warmups", "0", "--repeats", "1"]) == 0
    path = tmp_path / "outputs" / "benchmarks" / "deep.json"
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["mode"] == "deep"
    assert payload["schema"] == "mordheim-combat-benchmark-sweep/v1"
    assert payload["results"]


def test_parity_deep_parser_uses_the_certification_sample_policy():
    args = build_parser().parse_args(["parity", "--deep"])
    assert args.deep_simulations is None  # split policy resolved at run time
    assert args.max_modular_duels == 3_000_000


def test_parallel_oracle_worker_policies_default_to_auto(monkeypatch):
    monkeypatch.delenv("MORDHEIM_PARALLEL_ORACLE_WORKERS", raising=False)
    parser = build_parser()
    # None means "auto": pool only samples estimated over the ~20 s gate.
    assert parser.parse_args(["parity"]).workers is None
    assert parser.parse_args(["test-report"]).workers is None
    assert parser.parse_args(["parity", "--workers", "4"]).workers == 4
    # 1 is kept verbatim and collapses to sequential at resolve time.
    assert parser.parse_args(["test-report", "--workers", "1"]).workers == 1
    assert parser.parse_args(["test-report", "--workers", "auto"]).workers is None


def test_parallel_oracle_workers_honour_the_environment_default(monkeypatch):
    monkeypatch.setenv("MORDHEIM_PARALLEL_ORACLE_WORKERS", "8")
    assert build_parser().parse_args(["parity"]).workers == 8
    assert build_parser().parse_args(["test-report"]).workers == 8
    # An explicit flag wins over the environment.
    assert build_parser().parse_args(["parity", "--workers", "2"]).workers == 2


def test_parity_level_presets_map_onto_the_historical_sample_flags():
    from argparse import Namespace
    from mordheim_combat_lab.cli.commands import apply_parity_level

    args = Namespace(level="statistical", statistical=False, deep=False)
    apply_parity_level(args)
    assert args.statistical and not args.deep
    args = Namespace(level="deep", statistical=False, deep=False)
    apply_parity_level(args)
    assert args.deep and not args.statistical
    # Without --level the historical flags keep their exact semantics.
    args = Namespace(level="deterministic", statistical=True, deep=False)
    apply_parity_level(args)
    assert args.statistical and not args.deep
    # A preset plus an explicit alias still runs both sample groups.
    args = Namespace(level="statistical", statistical=False, deep=True)
    apply_parity_level(args)
    assert args.statistical and args.deep


def test_parity_parser_accepts_level_and_keeps_the_hidden_aliases():
    parsed = build_parser().parse_args(["parity", "--level", "deep"])
    assert parsed.level == "deep"
    # The historical aliases are hidden from the help but still parse.
    parsed = build_parser().parse_args(["parity", "--deep", "--statistical"])
    assert parsed.deep and parsed.statistical


def test_advanced_options_are_hidden_from_help_and_shown_by_help_all():
    import argparse
    from mordheim_combat_lab.cli.commands import _ADVANCED_OPTIONS

    def option(parser, command, flag):
        subparsers = next(action for action in parser._actions
                          if action.__class__.__name__ == "_SubParsersAction")
        sub = subparsers.choices[command]
        return next(action for action in sub._actions if flag in action.option_strings)

    concise = build_parser()
    verbose = build_parser(advanced_help=True)
    for command, flags in _ADVANCED_OPTIONS.items():
        for flag in tuple(flags)[:3]:  # spot-check the hidden set
            assert option(concise, command, flag).help is argparse.SUPPRESS
            assert option(verbose, command, flag).help is not argparse.SUPPRESS
    # Everyday options stay documented on the concise parser.
    assert option(concise, "parity", "--level").help is not argparse.SUPPRESS
    assert option(concise, "parity", "--truncations").help is not argparse.SUPPRESS


def test_help_all_prints_the_advanced_options(capsys):
    assert main(["parity", "--help-all"]) == 0
    output = capsys.readouterr().out
    assert "--statistical-simulations" in output
    assert "--deep-simulations" in output


def test_deep_parity_saves_the_report_by_default(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert main(["parity", "--deep", "--deep-simulations", "30",
                 "--deep-cross-simulations", "50", "--seed", "3"]) == 0
    path = tmp_path / "outputs" / "parity" / "deep.json"
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "mordheim-combat-parity/v2"
    assert payload["deep"] is not None
    assert payload["elapsed_seconds"] > 0
    assert all("reference_seconds" in row for row in payload["deep"]["samples"])
