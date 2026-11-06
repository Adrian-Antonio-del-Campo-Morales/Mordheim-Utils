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


def test_each_scenario_set_selects_the_same_scenarios_in_every_mode():
    from mordheim_combat_lab.cli.commands import select_benchmark_scenarios
    from mordheim_combat_lab.cli.scenarios import scenarios_for_level

    for level in ("small", "normal", "long"):
        expected = [item.id for item in scenarios_for_level(level)]
        for deep in (False, True):
            selected = select_benchmark_scenarios(level, None, deep=deep)
            assert [item.id for item in selected] == expected
    # ``long`` is also a scenario id: on its own it is that one scenario.
    assert [item.id for item in select_benchmark_scenarios(None, ["long"])] == ["long"]


def test_scenario_rejects_set_names_and_points_to_the_set_option(capsys):
    import pytest
    from mordheim_combat_lab.cli.commands import build_parser

    for name in ("all", "small", "normal"):
        with pytest.raises(SystemExit):
            build_parser().parse_args(["benchmark", "--scenario", name])
        assert "--pair-set small|normal|long" in capsys.readouterr().err
