"""Benchmark execution on the real engines, at smoke sizes.

Complements ``test_benchmark_gate`` (which stubs everything): a tiny number
of duels per check keeps this suite in the fast loop while proving the
measurement path actually runs each engine, records warm-up time and feeds
the profiler. The scenario catalogue must also resolve without the checkout
root on ``sys.path`` — the installed CLI runs from any directory.
"""
from __future__ import annotations

import subprocess
import sys

from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import run_benchmark


def test_run_benchmark_measures_the_modular_and_numpy_engines():
    scenario = benchmark_scenarios()[0]
    for backend in ("modular", "numpy"):
        result = run_benchmark(
            scenario, simulations=10, batch_size=10, seed=7, backend=backend,
            warmups=1, repeats=2,
        )
        assert result.backend == backend
        assert result.simulations == 10 and result.repeats == 2
        assert len(result.samples_seconds) == 2
        assert result.median_seconds > 0
        assert result.simulations_per_second > 0
        assert result.warmup_seconds > 0


def test_run_benchmark_without_warmups_records_no_warmup_time():
    scenario = benchmark_scenarios()[0]
    result = run_benchmark(
        scenario, simulations=5, batch_size=5, seed=7, backend="numpy",
        warmups=0, repeats=1,
    )
    assert result.warmup_seconds == 0.0


def test_profiler_collects_engine_frames_from_the_timed_repeats():
    import cProfile
    import pstats

    scenario = benchmark_scenarios()[0]
    profiler = cProfile.Profile()
    run_benchmark(
        scenario, simulations=5, batch_size=5, seed=7, backend="modular",
        warmups=1, repeats=1, profiler=profiler,
    )
    files = {entry[0] for entry in pstats.Stats(profiler).stats}
    assert any("modular" in str(name) for name in files)


def test_scenario_catalogue_loads_without_the_checkout_root_on_sys_path(tmp_path):
    import os

    probe = (
        "import mordheim_combat_lab.cli.scenarios as s; "
        "print(len(s.SCENARIOS), s.scenario_key('basic'))"
    )
    # The launcher exports the checkout root on PYTHONPATH; scrub it so the
    # probe exercises the file-path fallback, not the ordinary import.
    environment = {key: value for key, value in os.environ.items()
                   if key != "PYTHONPATH"}
    completed = subprocess.run(
        [sys.executable, "-c", probe], cwd=tmp_path, env=environment,
        capture_output=True, text=True, timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    count, key = completed.stdout.split()
    assert int(count) >= 43 and key == "scenario/basic"


def test_scenarios_select_every_catalogue_with_the_same_values():
    from mordheim_combat_lab.cli.benchmarking import benchmark_cases
    from mordheim_combat_lab.cli.scenarios import scenarios_for_level

    for level in ("small", "normal", "big"):
        cases, rejected = benchmark_cases([level])
        assert [case.id for case in cases] == [item.id for item in scenarios_for_level(level)]
        assert rejected == ()
    # Without --scenarios: small.  ``long`` is a scenario name, not a level.
    assert len(benchmark_cases(None)[0]) == 8
    assert [case.id for case in benchmark_cases(["long"])[0]] == ["long"]
    # Several values run their union; E2E deliveries and battery cases run
    # with their own duel context, keyed by their full name.
    key = "e2e/core/combat-critical-hits/a-critical-table-modifier-shifts-the-applied-band"
    cases, _ = benchmark_cases(["basic", key, "battery/q04-parry-attempt"])
    assert [case.id for case in cases] == ["basic", key, "battery/q04-parry-attempt"]
    assert cases[1].context is not None and cases[2].context is not None
    # A case the production engines cannot express is reported, not run.
    cases, rejected = benchmark_cases(["battery/q08-death-blow-optional"])
    assert cases == () and "scripted decisions" in rejected[0][1]


def test_unknown_values_and_options_are_errors(capsys):
    import pytest
    from mordheim_combat_lab.cli.benchmarking import benchmark_cases
    from mordheim_combat_lab.cli.commands import build_parser

    with pytest.raises(ValueError, match="unknown scenario"):
        benchmark_cases(["all"])
    for argv in (["benchmark", "--pair-set", "small"], ["benchmark", "--deep"],
                 ["parity", "--certificate", "deep"], ["calibrate", "--pool-simulations", "1"]):
        with pytest.raises(SystemExit):
            build_parser().parse_args(argv)
        assert "unrecognized arguments" in capsys.readouterr().err


def test_shared_option_levels_match_the_catalogue():
    from mordheim_combat_lab.cli.options import LEVELS
    from mordheim_combat_lab.cli.scenarios import LEVELS as catalogue_levels

    assert LEVELS == catalogue_levels
