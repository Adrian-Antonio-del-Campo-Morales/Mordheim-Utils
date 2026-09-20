from dataclasses import replace
import json

import pytest

from mordheim_combat_lab.cli.benchmarking import benchmark_payload
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
from mordheim_combat_lab.cli.benchmarking import compare_with_baseline
from mordheim_combat_lab.cli.benchmarking import deep_benchmark_plan
from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
from mordheim_combat_lab.cli.benchmarking import load_benchmark_payload
from mordheim_combat_lab.cli.benchmarking import parse_sizes
from mordheim_combat_lab.cli.benchmarking import print_results_table
from mordheim_combat_lab.cli.benchmarking import print_sweep_table
from mordheim_combat_lab.cli.benchmarking import run_benchmark
from mordheim_combat_lab.cli.benchmarking import run_benchmark_units
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


def test_deep_pair_sets_are_stable_and_fast_is_a_full_subset():
    full = deep_test_scenarios("full")
    fast = deep_test_scenarios("fast")
    mini = deep_test_scenarios("mini")
    full_ids = tuple(item.id for item in full)
    fast_ids = tuple(item.id for item in fast)
    mini_ids = tuple(item.id for item in mini)

    assert len(full) == 42
    assert len(fast) == 30
    assert len(mini) == 10
    assert set(fast_ids) <= set(full_ids)
    # mini keeps the cheap baseline/mirror pairs that fast drops on purpose:
    # they measure fixed per-batch overhead, so it is only a full subset.
    assert set(mini_ids) <= set(full_ids)
    assert len(set(full_ids)) == len(full_ids)
    assert fast_ids == (
        "defences", "stateful", "sigmarite-vs-undead", "regen-vs-fire",
        "natural-armour-vs-magic", "pistol-vs-parry", "concussion-vs-dwarf",
        "paired-poison-vs-undead", "ward-vs-magic", "unarmed-vs-steel",
        "injury-profile-vs-death-knife", "entangle-vs-fencer",
        "triple-weapon-vs-parry", "a2-vs-w1-stun", "frenzy-vs-w2",
        "elite-vs-durable", "heavy-grind", "ithilmar-duel",
        "skills-vs-hitter", "helmet-vs-injury-profile-2",
        "cathayan-longsword-vs-sword", "blessed-vs-regen",
        "injury-profile-3-vs-4", "skill-stack-vs-hitter",
        "resilient-vs-high-strength", "charge-skills-vs-tank",
        "first-round-opener", "random-characteristics-vs-stable",
        "trained-bear-vs-scarecrow", "silent-walker-vs-cold-one",
    )
    with pytest.raises(ValueError, match="choose 'mini', 'fast' or 'full'"):
        deep_test_scenarios("unknown")


def test_deep_suite_scenarios_compile_into_legal_duels():
    from mordheim_construction.compiler import compile_fighter
    for scenario in deep_test_scenarios():
        compile_fighter(scenario.first)
        compile_fighter(scenario.second)


def test_deep_suite_includes_the_timing_and_parry_amplifiers():
    by_id = {item.id: item for item in deep_test_scenarios()}
    assert {
        "triple-weapon-vs-parry", "a2-vs-w1-stun", "frenzy-vs-w2",
        "durable-vs-elite", "heavy-grind", "ithilmar-duel",
        "skills-vs-hitter", "helmet-vs-injury-profile-2",
        "cathayan-longsword-vs-sword", "blessed-vs-regen",
    } <= set(by_id)
    # The grind pairs are the long 75-round budget, like the core ``long``.
    assert by_id["heavy-grind"].maximum_rounds == 75
    assert by_id["long"].maximum_rounds == 75
    # Keep this test independent of engine/KB behavior: the statistical
    # calibration is documented separately and may change while an engine
    # implementation is under investigation.
    assert by_id["skills-vs-hitter"].first.skill_ids == (
        "skill.strongman", "skill.thick-skull", "skill.step-aside",
    )
    assert by_id["helmet-vs-injury-profile-2"].first.defence_ids == (
        "defence.helmet",
    )
    assert by_id["cathayan-longsword-vs-sword"].first.main_weapon_id == (
        "weapon.cathayan-longsword"
    )
    assert by_id["blessed-vs-regen"].first_attack_tags == ("attack.blessed",)


def test_coverage_completion_pairs_expose_their_intended_compiled_axes():
    from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters

    compiled = {
        scenario.id: compile_benchmark_fighters(scenario)
        for scenario in deep_test_scenarios("fast")[-8:]
    }
    first, second = compiled["injury-profile-3-vs-4"]
    assert (first.injury_profile, second.injury_profile) == (3, 4)

    first, _ = compiled["skill-stack-vs-hitter"]
    assert {
        "skill.expert-fighter", "skill.infinite-hatred", "skill.red-fury",
        "skill.sure-strike",
    } <= set(first.global_effects.tags)
    assert first.global_effects.wound_modifier == 1
    assert first.global_effects.reroll_hits
    assert first.global_effects.reroll_wounds
    assert first.global_effects.attacks_bonus == 1

    first, _ = compiled["resilient-vs-high-strength"]
    assert first.global_effects.incoming_strength_modifier == -1

    first, _ = compiled["charge-skills-vs-tank"]
    assert first.global_effects.charge_ws_bonus == 1
    assert first.global_effects.charge_strength_bonus == 1

    first, second = compiled["first-round-opener"]
    assert first.global_effects.first_round_charge_attacks_bonus == 1
    assert second.main_weapon.first_round_strength_bonus == 2

    first, _ = compiled["random-characteristics-vs-stable"]
    assert first.random_characteristics == (
        ("WS", 1, 6, 0), ("S", 1, 6, 0),
        ("T", 1, 6, 0), ("A", 1, 3, 0),
    )

    first, second = compiled["trained-bear-vs-scarecrow"]
    assert first.global_effects.bear_hug
    assert "attack.fire" in first.main_weapon.tags
    assert second.global_effects.caught_fire_threshold == 3

    first, second = compiled["silent-walker-vs-cold-one"]
    assert first.global_effects.ward_save_mundane_only
    assert first.global_effects.ward_save == 5
    assert second.natural_armour_unmodified
    assert second.natural_armour_save == 6
    assert "attack.magical" in second.main_weapon.tags


def test_deep_benchmark_plan_keeps_modular_at_the_reference_size_only():
    scenarios = benchmark_scenarios()
    plan = deep_benchmark_plan(
        scenarios, vector_sizes=(1_000, 10_000), batch_sizes=(1_000, 10_000),
        modular_simulations=100, backends=("modular", "numpy", "native"), installed=("numpy",),
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
    assert plan.modular_backend is None
    assert all(run[1] == "numpy" for run in plan.runs)


def test_deep_parser_defaults_and_guards():
    args = build_parser().parse_args(["benchmark", "--deep"])
    assert args.deep is True
    assert args.pair_set is None  # deep sweeps resolve None to "full"
    fast = build_parser().parse_args([
        "benchmark", "--deep", "--pair-set", "fast",
        "--scenario", "skills-vs-hitter",
    ])
    assert fast.pair_set == "fast"
    assert fast.scenario == "skills-vs-hitter"
    # The deep grids are the defaults of the generic size options: no
    # separate --deep-* aliases exist any more.
    from mordheim_combat_lab.cli.commands import DEEP_BATCH_SIZES, DEEP_SIMULATION_SIZES
    assert args.simulation_sizes is None and args.batch_sizes is None
    assert DEEP_SIMULATION_SIZES == "10k,100k,500k,1M,5M"
    assert DEEP_BATCH_SIZES == "25k,100k,200k,500k"
    assert args.deep_modular_simulations == 10_000
    override = build_parser().parse_args([
        "benchmark", "--deep", "--simulation-sizes", "5k,50k",
        "--batch-sizes", "5k,25k",
    ])
    assert override.simulation_sizes == "5k,50k"
    assert override.batch_sizes == "5k,25k"

    from mordheim_combat_lab.cli.commands import main
    assert main([
        "benchmark", "--deep", "--backend", "modular", "--scenario", "basic",
        "--deep-modular-simulations", "1", "--warmups", "0", "--repeats", "1",
    ]) == 0


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


def test_benchmark_defaults_to_all_engines_and_accepts_a_selected_set():
    args = build_parser().parse_args(["benchmark"])
    assert args.backend == ("modular", "numpy", "native")
    selected = build_parser().parse_args(["benchmark", "--backend", "modular", "numpy"])
    assert selected.backend == ["modular", "numpy"]


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

    tagged = sweep_payload(
        [result], [], simulation_sizes=(2,), batch_sizes=(1,), seed=3,
        warmups=0, repeats=1, pair_set="fast",
    )
    assert tagged["pair_set"] == "fast"


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
    reports = list((tmp_path / "outputs" / "benchmarks").glob("deep-*.json"))
    assert len(reports) == 1
    path = reports[0]
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["mode"] == "deep"
    assert payload["schema"] == "mordheim-combat-benchmark-sweep/v1"
    assert payload["results"]


def test_deep_benchmark_pair_set_is_recorded_in_payload(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    output = tmp_path / "fast.json"
    assert main([
        "benchmark", "--deep", "--pair-set", "fast",
        "--simulation-sizes", "1k", "--batch-sizes", "1k",
        "--scenario", "defences", "--backend", "numpy",
        "--deep-modular-simulations", "20", "--warmups", "0", "--repeats", "1",
        "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["mode"] == "deep"
    assert payload["pair_set"] == "fast"
    assert {row["scenario"] for row in payload["results"]} == {"defences"}


def test_pair_set_is_rejected_outside_deep_benchmark(capsys):
    assert main(["benchmark", "--pair-set", "fast", "--backend", "numpy"]) == 2
    assert "--pair-set applies to --deep and --tts" in capsys.readouterr().err


def test_parity_deep_parser_uses_the_certification_sample_policy():
    args = build_parser().parse_args(["parity", "--level", "deep"])
    assert args.deep_simulations is None  # split policy resolved at run time
    assert args.max_modular_duels == 5_000_000
    fast = build_parser().parse_args([
        "parity", "--level", "deep", "--pair-set", "fast",
    ])
    assert fast.level == "deep" and fast.pair_set == "fast"
    truncations = build_parser().parse_args([
        "parity", "--truncations", "--pair-set", "fast",
    ])
    assert truncations.truncations and truncations.pair_set == "fast"


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


def test_parity_level_is_the_only_preset_selector(tmp_path):
    """--level is the single way to pick a sample group.

    The former --statistical/--deep aliases are gone: their mixing semantics
    (``--level deep --statistical``) was the source of the confusing help.
    """
    output = tmp_path / "statistical.json"
    assert main([
        "parity", "--level", "statistical", "--statistical-simulations", "30",
        "--seed", "3", "--workers", "1", "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["statistical"]
    assert payload["deep"] is None
    with pytest.raises(SystemExit):
        build_parser().parse_args(["parity", "--statistical"])
    with pytest.raises(SystemExit):
        build_parser().parse_args(["parity", "--deep"])


def test_deep_parity_saves_the_report_by_default(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert main(["parity", "--level", "deep", "--deep-simulations", "30",
                 "--deep-cross-simulations", "50", "--seed", "3"]) == 0
    reports = list((tmp_path / "outputs" / "parity").glob("deep-*.json"))
    assert len(reports) == 1
    payload = json.loads(reports[0].read_text(encoding="utf-8"))
    assert payload["schema"] == "mordheim-combat-parity/v2"
    assert payload["deep"] is not None
    assert payload["elapsed_seconds"] > 0
    assert all("reference_seconds" in row for row in payload["deep"]["samples"])


# ---------------------------------------------------------------------------
# --processes: parallel scenario execution and real speedup reporting
# ---------------------------------------------------------------------------


def _unit(scenario_id="basic", backend="numpy", simulations=2, batch_size=2,
          batch="unit"):
    from mordheim_combat_lab.cli.benchmarking import BenchmarkUnit
    scenario = next(
        item for item in benchmark_scenarios() if item.id == scenario_id
    )
    return BenchmarkUnit(
        scenario=scenario, backend=backend, simulations=simulations,
        batch_size=batch_size, seed=3, warmups=0, repeats=1, batch=batch,
    )


def test_benchmark_units_run_sequentially_and_through_the_pool_with_equal_totals():
    units = (
        _unit(batch="basic/numpy"),
        _unit(scenario_id="defences", backend="modular", batch="defences/modular"),
    )
    sequential, sequential_timings, sequential_failures = run_benchmark_units(
        units, processes=1)
    pooled, pooled_timings, pooled_failures = run_benchmark_units(units, processes=2)
    assert not sequential_failures and not pooled_failures
    # The engines are deterministic: pool and sequential runs measure the same
    # units (throughput itself is timing data and legitimately differs).
    assert [(item.scenario, item.backend, item.simulations, item.batch_size,
             item.repeats) for item in pooled] == [
        (item.scenario, item.backend, item.simulations, item.batch_size,
         item.repeats) for item in sequential
    ]
    assert [name for name, _seconds in pooled_timings] == [
        "basic/numpy", "defences/modular",
    ]
    assert all(seconds > 0 for _name, seconds in pooled_timings)


def test_run_benchmark_units_rejects_invalid_process_counts():
    with pytest.raises(ValueError, match="processes must be >= 1"):
        run_benchmark_units((_unit(),), processes=0)


def test_sequential_benchmark_units_report_failures_without_stopping():
    import mordheim_combat_lab.cli.benchmarking as benchmarking_module

    def explode(*_args, **_kwargs):
        raise RuntimeError("boom")

    original = benchmarking_module.simulate_duel
    benchmarking_module.simulate_duel = explode
    try:
        results, timings, failures = run_benchmark_units(
            (_unit(batch="will-fail"),
             _unit(scenario_id="defences", backend="modular", batch="fine")),
            processes=1,
        )
    finally:
        benchmarking_module.simulate_duel = original
    assert [item.scenario for item in results] == ["defences"]
    assert timings[0] == ("will-fail", 0.0)
    assert timings[1][0] == "fine" and timings[1][1] > 0
    assert [(unit.batch, reason) for unit, reason in failures] == [
        ("will-fail", "boom"),
    ]


def test_benchmark_parser_processes_defaults_to_sequential():
    assert build_parser().parse_args(["benchmark"]).processes == 1
    assert build_parser().parse_args(["benchmark", "--processes", "4"]).processes == 4


def test_benchmark_with_processes_reports_sequential_vs_pool_speedup(tmp_path):
    output = tmp_path / "sweep.json"
    assert main([
        "benchmark", "--backend", "numpy", "--simulation-sizes", "2",
        "--batch-sizes", "2", "--seed", "3", "--warmups", "0", "--repeats", "1",
        "--processes", "2", "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    speedup = payload["parallel_speedup"]
    assert speedup["mode"] == "worker-estimate-vs-wall"
    assert speedup["processes"] == 2
    assert speedup["wall_seconds"] > 0
    assert speedup["speedup"] > 0
    rows = speedup["rows"]
    assert len(rows) == 5  # five standard scenarios x numpy x one size/batch
    for row in rows:
        assert row["worker_seconds"] > 0
        assert row["estimated_sequential_seconds"] > 0
        assert 0 < row["speedup"] <= len(rows)


def test_deep_benchmark_with_processes_reports_worker_sample_speedup(tmp_path):
    output = tmp_path / "deep-parallel.json"
    assert main([
        "benchmark", "--deep", "--simulation-sizes", "1k", "--batch-sizes", "1k",
        "--scenario", "basic", "--backend", "numpy",
        "--deep-modular-simulations", "10", "--warmups", "1", "--repeats", "2",
        "--processes", "2", "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    speedup = payload["parallel_speedup"]
    assert speedup["mode"] == "worker-estimate-vs-wall"
    assert speedup["processes"] == 2
    assert speedup["wall_seconds"] > 0
    assert speedup["speedup"] > 0
    rows = speedup["rows"]
    assert {row["unit"] for row in rows} == {"basic/numpy/1000/1000"}
    assert all(row["worker_seconds"] > 0 for row in rows)
    assert all(row["speedup"] > 0 for row in rows)
    assert payload["elapsed_seconds"] > 0
    assert payload["engine_seconds"] > 0


def test_benchmark_payload_records_total_wall_time(tmp_path):
    output = tmp_path / "single.json"
    assert main([
        "benchmark", "-n", "2000", "--batch-size", "2000", "--backend", "numpy",
        "--seed", "3", "--warmups", "0", "--repeats", "1",
        "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["elapsed_seconds"] > 0
    assert payload["engine_seconds"] > 0
    # Sequentially the timed engine samples can never exceed the wall time;
    # the remainder is the setup and overhead the wall report exposes.
    assert payload["engine_seconds"] <= payload["elapsed_seconds"] + 0.05


def test_benchmark_console_prints_the_elapsed_summary(capsys):
    assert main([
        "benchmark", "-n", "2", "--batch-size", "2", "--backend", "numpy",
        "--seed", "3", "--warmups", "0", "--repeats", "1",
    ]) == 0
    output = capsys.readouterr().out
    assert "Total wall time:" in output
    assert "setup and overhead" in output


# --tts: time-to-solution — strategies ranked by the wall time of solving
# the whole workload, with the deterministic totals as a correctness gate
# ---------------------------------------------------------------------------


def _tts_scenarios():
    from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios as _bs
    return _bs()


def test_tts_strategy_parser_defaults_and_canonicalizes():
    from mordheim_combat_lab.cli.benchmarking import parse_tts_strategies

    assert parse_tts_strategies(None) == (
        "sequential", "processes=4", "parallel=4")
    assert parse_tts_strategies("") == (
        "sequential", "processes=4", "parallel=4")
    assert parse_tts_strategies("sequential") == ("sequential",)
    assert parse_tts_strategies("processes=1") == ("sequential",)
    assert parse_tts_strategies("parallel=1,processes=2") == (
        "sequential", "processes=2")
    with pytest.raises(ValueError, match="invalid TTS strategy"):
        parse_tts_strategies("threads=4")
    with pytest.raises(ValueError, match="invalid TTS strategy"):
        parse_tts_strategies("processes=0")
    with pytest.raises(ValueError, match="invalid TTS strategy"):
        parse_tts_strategies("parallel")


def test_tts_strategies_agree_on_totals_and_parallel_beats_sequential():
    from mordheim_combat_lab.cli.benchmarking import run_tts_strategy

    scenarios = _tts_scenarios()
    results = [
        run_tts_strategy(
            strategy, scenarios, simulations=100, batch_size=25, seed=11,
        )
        for strategy in ("sequential", "processes=2", "parallel=2")
    ]
    totals = {result.totals for result in results}
    assert len(totals) == 1  # same per-batch streams under every strategy
    first, second, unresolved = totals.pop()
    assert first + second + unresolved == 500  # 5 scenarios x 100 duels
    walls = {result.strategy: result.wall_seconds for result in results}
    # Every strategy pays the same spawn-free sequential work plus startup;
    # the parallel forms must not be pathologically slower (2 tiny spawns).
    assert walls["processes=2"] < 10 * walls["sequential"]
    assert walls["parallel=2"] < 10 * walls["sequential"]


def test_tts_determinism_gate_and_ranking():
    from dataclasses import replace
    from mordheim_combat_lab.cli.benchmarking import (
        TtsStrategyResult, tts_determinism_gate, tts_ranking,
    )

    fast = TtsStrategyResult(
        "parallel=4", "batch-pool", 4, wall_seconds=3.0, engine_seconds=3.0,
        totals=(60, 30, 10), per_scenario_seconds=(("a", 1.5), ("b", 1.5)),
    )
    slow = TtsStrategyResult(
        "sequential", "sequential", 1, wall_seconds=8.0, engine_seconds=8.0,
        totals=(60, 30, 10), per_scenario_seconds=(("a", 4.0), ("b", 4.0)),
    )
    assert tts_determinism_gate((fast, slow)) == {
        "passed": True, "distinct_totals": [[60, 30, 10]]}
    rows = tts_ranking((slow, fast))
    assert [row["strategy"] for row in rows] == ["parallel=4", "sequential"]
    assert rows[0]["speedup_vs_sequential"] == pytest.approx(8.0 / 3.0)
    disagreeing = replace(fast, totals=(60, 30, 11))
    assert tts_determinism_gate((fast, disagreeing))["passed"] is False
    assert tts_determinism_gate((fast,)) is None


def test_tts_study_runs_cells_winners_and_parity(tmp_path, capsys):
    output = tmp_path / "tts-study.json"
    assert main([
        "benchmark", "--tts", "--simulation-sizes", "100,200",
        "--batch-sizes", "50", "--seed", "11", "--backend", "numpy",
        "--strategies", "sequential,parallel=2", "--repeats", "2",
        "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "mordheim-combat-benchmark-tts/v1"
    assert payload["configuration"]["simulation_sizes"] == [100, 200]
    assert payload["configuration"]["batch_sizes"] == [50]
    assert payload["configuration"]["repeats"] == 2
    assert len(payload["cells"]) == 2  # 2 sims x 1 batch
    for cell in payload["cells"]:
        assert len(cell["results"]) == 2
        assert cell["winners"][0]["strategy"] in {"sequential", "parallel=2"}
        assert cell["winners"][-1]["overall"] is True
        for item in cell["results"]:
            assert len(item["repeat_walls_seconds"]) == 2
    assert payload["parity"]["passed"] is True
    assert main([
        "benchmark", "--tts", "--simulation-sizes", "100", "--batch-sizes",
        "50", "--seed", "11", "--backend", "numpy",
        "--strategies", "sequential,parallel=2",
    ]) == 0
    stdout = capsys.readouterr().out
    assert "Time-to-solution study" in stdout
    assert "Parity gate: PASS" in stdout


def test_tts_study_runs_native_and_gates_numpy_parity(tmp_path):
    output = tmp_path / "tts-native.json"
    assert main([
        "benchmark", "--tts", "-n", "200", "--batch-size", "100", "--seed", "11",
        "--backend", "numpy", "native", "--strategies", "sequential,parallel=2",
        "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    cell = payload["cells"][0]
    backends = {item["backend"] for item in cell["results"]}
    assert backends == {"numpy", "native"}
    # native never runs parallel=N (a NumPy-driver pool)
    assert all(
        item["strategy"] != "parallel=2"
        for item in cell["results"] if item["backend"] == "native")
    # Parity gate: per-backend across strategies (identical per-batch streams
    # within one engine). Cross-engine totals legitimately differ — each
    # engine derives its streams from the seed in its own way.
    assert payload["parity"]["passed"] is True
    numpy_totals = {
        tuple(item["totals"]) for item in cell["results"]
        if item["backend"] == "numpy"}
    assert len(numpy_totals) == 1
    # Rate sanity: both engines land within sampling noise (same distributions).
    rates = {row["backend"]: row for row in cell["rates"]}
    assert abs(rates["numpy"]["first"] - rates["native"]["first"]) < 0.05


def test_tts_rejects_invalid_and_conflicting_options(capsys):
    assert main([
        "benchmark", "--tts", "--backend", "numpy", "--strategies", "threads=4",
    ]) == 2
    assert "invalid TTS strategy" in capsys.readouterr().err
    assert main([
        "benchmark", "--tts", "--backend", "numpy", "--strategies", "sequential",
    ]) == 2
    assert "at least two" in capsys.readouterr().err
    assert main([
        "benchmark", "--tts", "--backend", "numpy", "--deep",
    ]) == 2
    assert "--deep sweeps belong to the classic throughput mode" \
        in capsys.readouterr().err
    assert main([
        "benchmark", "--tts", "--backend", "numpy", "--processes", "4",
    ]) == 2
    assert "--processes belongs to the standard throughput modes" \
        in capsys.readouterr().err
    assert main([
        "benchmark", "--tts", "--backend", "native",
    ]) == 2
    assert "include numpy in --backend" in capsys.readouterr().err
    assert main([
        "benchmark", "--tts", "--backend", "numpy", "modular",
    ]) == 2
    assert "drop modular" in capsys.readouterr().err


def test_tts_parser_defaults():
    assert build_parser().parse_args(["benchmark"]).tts is False
    assert build_parser().parse_args(["benchmark", "--tts"]).tts is True
    assert build_parser().parse_args(
        ["benchmark", "--tts", "--strategies", "sequential,processes=3"]
    ).strategies == "sequential,processes=3"


def test_tts_accepts_pair_sets_and_records_them(tmp_path, capsys):
    """--tts + --pair-set runs the real deep pair set as the workload."""
    output = tmp_path / "tts-mini.json"
    assert main([
        "benchmark", "--tts", "--pair-set", "mini", "-n", "100",
        "--batch-size", "25", "--seed", "11", "--backend", "numpy",
        "--strategies", "sequential,parallel=2",
        "--output", str(output), "--json",
    ]) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["pair_set"] == "mini"
    # The mini pair set replaces the standard five-scenario workload.
    assert payload["configuration"]["scenarios"] == 10
    assert len(payload["cells"][0]["results"][0]["per_scenario_seconds"]) == 10
    assert payload["parity"]["passed"] is True
    assert main([
        "benchmark", "--tts", "--pair-set", "mini", "-n", "100",
        "--batch-size", "25", "--seed", "11", "--backend", "numpy",
        "--strategies", "sequential,parallel=2",
    ]) == 0
    stdout = capsys.readouterr().out
    assert "(mini pair set)" in stdout


def test_tts_rejects_pair_set_without_value_still_applies(capsys):
    # --pair-set remains rejected outside --deep/--tts workloads.
    assert main([
        "benchmark", "--pair-set", "fast", "--backend", "numpy",
    ]) == 2
    assert "--pair-set applies to --deep and --tts" in capsys.readouterr().err
