from dataclasses import replace

import pytest

from mordheim_combat_lab.cli.benchmarking import benchmark_payload
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import compare_with_baseline
from mordheim_combat_lab.cli.benchmarking import load_benchmark_payload
from mordheim_combat_lab.cli.benchmarking import run_benchmark
from mordheim_combat_lab.cli.benchmarking import write_benchmark_payload
from mordheim_combat_lab.cli.commands import build_parser
from mordheim_combat_lab.cli.commands import _print_benchmark_table
from mordheim_combat_lab.cli.commands import main


def test_benchmark_suite_has_the_five_required_scenarios():
    assert {item.id for item in benchmark_scenarios()} == {
        "basic", "multiattack", "defences", "stateful", "long",
    }


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
    args = build_parser().parse_args(["benchmark", "-n", "2", "--repeats", "1"])
    _print_benchmark_table((scenario,), ("modular", "numpy"), [result], [], args)
    output = capsys.readouterr().out
    assert "2 simulaciones por escenario y motor" in output
    assert "Escenario" in output
    assert "Modular sim/s" in output
    assert "Vectorizado Mid" in output
    assert "NO DISPONIBLE" in output


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


def test_required_improvement_needs_a_baseline_without_running_benchmarks(capsys):
    assert main(["benchmark", "--require-improvement"]) == 2
    assert "requires --baseline" in capsys.readouterr().err
