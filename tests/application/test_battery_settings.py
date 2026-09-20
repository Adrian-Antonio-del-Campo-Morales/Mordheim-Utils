"""external.test_battery_settings: battery splitting, seeding and pooling."""
from __future__ import annotations

import time
from dataclasses import replace
from threading import Event
from unittest.mock import patch

import pytest

from mordheim_combat_lab.application.settings import (
    DuelExecutionSettings,
    battery_pool_plan,
    default_batch_size,
    pool_batch_size,
    pool_speedup,
    resolve_battery_settings,
    simulate_battery,
    split_battery,
)
from mordheim_combat_lab.application.analyses import ComparisonCandidate, compare_builds
from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelResult, FighterBuild

# Sequential wall seconds per battery measured on the reference machine
# (native batch 5k; numpy batch 100k — crossover table in
# docs/guides/develop-and-release.md). The pool policy is tested against
# these real costs, not against invented ones.
MEASURED_BASELINE_SECONDS = {
    10_000: 0.0150,
    25_000: 0.0358,
    60_000: 0.0855,
    100_000: 0.1430,
    250_000: 0.3381,
    500_000: 0.7111,
    1_000_000: 1.3955,
}
NUMPY_BASELINE_SECONDS = {200_000: 0.8387, 800_000: 3.0397, 1_000_000: 3.3819}


def build(weapon="weapon.dagger"):
    return FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1), main_weapon_id=weapon)


def _result(simulations):
    """A consistent fake DuelResult (:class:`DuelResult` validates the sum)."""
    first = simulations // 2
    return DuelResult(first, simulations - first, 0, simulations)


def test_split_battery_segments_cover_the_whole_batch_plan():
    # 2M duels at batch 5k -> 400 batches -> 4 workers take 100 batches each.
    assert split_battery(2_000_000, 5_000, 4) == ((0, 100), (100, 200), (200, 300), (300, 400))
    # A trailing partial batch is its own batch (same plan as the driver).
    assert split_battery(10_000, 3_000, 4) == ((0, 1), (1, 2), (2, 3), (3, 4))
    # More workers than batches degenerates to one worker per batch.
    assert split_battery(10_000, 3_000, 99) == ((0, 1), (1, 2), (2, 3), (3, 4))
    # Every segment chain is contiguous and non-empty.
    for simulations, batch_size, workers in ((1_000_000, 5_000, 12), (7_500, 2_500, 8), (10, 4, 3)):
        segments = split_battery(simulations, batch_size, workers)
        batches = len((lambda f, r: (f,) * f + (((r,) if r else ())))( *divmod(simulations, batch_size)))
        covered = sum(stop - first for first, stop in segments)
        assert covered == batches
        assert segments[0][0] == 0
        for (_first, stop), (next_first, _next_stop) in zip(segments, segments[1:]):
            assert stop == next_first


def test_split_battery_rejects_non_positive_workers():
    with pytest.raises(ValueError):
        split_battery(10_000, 5_000, 0)


def test_large_battery_policy_selects_the_measured_optima():
    small = DuelExecutionSettings(500_000, 0, 5_000, 10)
    assert small.large_battery_processes("native") is None
    assert small.large_battery_processes("numpy") is None

    big = DuelExecutionSettings(2_000_000, 0, 5_000, 10)
    assert big.large_battery_processes("native") == 14
    assert big.large_battery_processes("auto") == 14
    assert big.large_battery_processes("numpy") == 8


def test_resolve_battery_settings_maps_the_legacy_default_per_backend():
    legacy = DuelExecutionSettings(10_000, 0, 100_000, 10)
    assert resolve_battery_settings(legacy, "native").batch_size == 5_000
    assert resolve_battery_settings(legacy, "auto").batch_size == 5_000
    assert resolve_battery_settings(legacy, "numpy").batch_size == 100_000

    explicit = DuelExecutionSettings(10_000, 0, 7_500, 10)
    assert resolve_battery_settings(explicit, "native").batch_size == 7_500


def test_default_batch_size_unknown_backend_raises():
    with pytest.raises(ValueError):
        default_batch_size("modular")


def test_battery_pool_reproduces_the_sequential_result_bit_for_bit():
    settings = DuelExecutionSettings(20_000, 1234, 2_000, 10)
    first, second = compile_fighter(build()), compile_fighter(build())

    sequential = simulate_battery(first, second, settings, workers=0)
    pooled = simulate_battery(first, second, settings, workers=2)

    assert (pooled.first_wins, pooled.second_wins, pooled.unresolved) == (
        sequential.first_wins, sequential.second_wins, sequential.unresolved)
    assert pooled.simulations == settings.simulations


def test_simulate_battery_forced_numpy_matches_the_numpy_driver():
    """The calibration sweeps force the numpy path on eligible plans."""
    settings = DuelExecutionSettings(20_000, 1234, 5_000, 10)
    first, second = compile_fighter(build()), compile_fighter(build())

    sequential = simulate_duel(settings.request(first, second), backend="numpy")
    pooled = simulate_battery(first, second, settings, workers=2, backend="numpy")

    assert (pooled.first_wins, pooled.second_wins, pooled.unresolved) == (
        sequential.first_wins, sequential.second_wins, sequential.unresolved)


def test_comparison_service_battery_pool_preserves_results():
    candidates = (ComparisonCandidate("mace", "Mace", build("weapon.mace")),)
    settings = DuelExecutionSettings(2_000, 11, 1_000, 5)
    sequential = compare_builds(build(), build(), candidates, settings, Event(), workers=0)
    pooled = compare_builds(build(), build(), candidates, settings, Event(), workers=2)

    assert pooled.results[0].win_rate == sequential.results[0].win_rate
    assert pooled.results[0].enemy_win_rate == sequential.results[0].enemy_win_rate
    assert pooled.results[0].unresolved_rate == sequential.results[0].unresolved_rate


def test_pool_speedup_stays_under_the_measured_curve():
    # Measured: 1.70x at 2 segments, 3.38x at 5, 5.78x at 12 (native), 3.96x
    # at 8 (numpy). The model must never promise more than was measured.
    assert pool_speedup(2) < 1.70
    assert pool_speedup(5) < 3.38
    assert pool_speedup(8) < 3.96
    assert pool_speedup(12) < 5.78
    assert pool_speedup(1) == 1.0
    assert pool_speedup(12) > pool_speedup(5) > pool_speedup(2) > pool_speedup(1)


def test_battery_pool_plan_activation_points():
    def plan(sims, fighters, baseline=None, backend="native", batch=5_000):
        seconds = MEASURED_BASELINE_SECONDS[sims] if baseline is None else baseline
        return battery_pool_plan(seconds, DuelExecutionSettings(sims, 7, batch, 20), backend, fighters)

    # Two segments still pay off in a wide run, but not in a narrow one.
    assert plan(10_000, 200) == 14
    assert plan(10_000, 8) is None
    # Marginal widths stay sequential: the estimate demands a 1.25x margin.
    assert plan(25_000, 3) is None
    assert plan(100_000, 2) is None
    # Wide runs engage the pool well below the old 1M sample threshold.
    assert plan(25_000, 96) == 14
    assert plan(60_000, 9) == 14
    assert plan(100_000, 8) == 14
    # Large samples pay for the pool even with a single candidate.
    assert plan(250_000, 3) == 14
    assert plan(500_000, 1) == 14
    assert plan(1_000_000, 1) == 14
    # The numpy fallback tops out at 8 workers (memory-bandwidth bound),
    # and counts segments with the pooled batch (25k), not the sequential
    # 100k: at 100k samples the default batch was a single batch, so the
    # numpy fallback could never pool at all.
    assert plan(1_000_000, 1, NUMPY_BASELINE_SECONDS[1_000_000], "numpy", 100_000) == 8
    assert plan(100_000, 1, 0.25, "numpy", 100_000) is None  # one narrow fighter
    assert plan(100_000, 4, 0.25, "numpy", 100_000) == 8  # 25k splits it in four


def test_pool_batch_size_rewrites_only_the_numpy_legacy_default():
    legacy_numpy = DuelExecutionSettings(1_000_000, 7, 100_000, 20)
    assert pool_batch_size("numpy", legacy_numpy) == 25_000

    # Explicit batches stand (the legacy global default is the sentinel).
    explicit = DuelExecutionSettings(1_000_000, 7, 40_000, 20)
    assert pool_batch_size("numpy", explicit) == 40_000

    # Native keeps its measured pool optimum (within 4% of the best point).
    native = DuelExecutionSettings(1_000_000, 7, 5_000, 20)
    assert pool_batch_size("native", native) == 5_000
    assert pool_batch_size("auto", legacy_numpy) == 100_000


def test_compare_builds_automatic_policy_engages_the_pool_from_the_baseline_cost():
    pools = []
    seen = []

    class FakePool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers
            pools.append(self)

        def shutdown(self, wait=True):
            pass

    def slow_baseline(request):
        time.sleep(0.03)  # stands in for a battery that really costs this much
        return _result(request.simulations)

    def fake_battery(fighter, enemy, settings, cancel_event, workers=None, pool=None):
        seen.append(pool)
        return _result(settings.simulations)

    candidates = tuple(
        ComparisonCandidate(f"c{index}", f"C{index}", build("weapon.mace")) for index in range(100)
    )
    settings = DuelExecutionSettings(1_000_000, 11, 5_000, 5)
    with patch("mordheim_combat_lab.application.analyses.simulate_duel", slow_baseline), \
            patch("mordheim_combat_lab.application.analyses.simulate_battery", fake_battery), \
            patch("concurrent.futures.ProcessPoolExecutor", FakePool):
        compare_builds(build(), build(), candidates, settings, Event())

    assert len(pools) == 1  # one executor for the whole run
    assert pools[0].max_workers == 14
    assert seen == [pools[0]] * len(candidates)  # every candidate shares it


def test_compare_builds_switches_numpy_candidates_to_the_pooled_batch():
    batches = []

    class FakePool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def shutdown(self, wait=True):
            pass

    def slow_baseline(request):
        time.sleep(0.02)  # stands in for the numpy sequential probe
        return _result(request.simulations)

    def fake_battery(fighter, enemy, settings, cancel_event, workers=None, pool=None):
        batches.append((settings.batch_size, pool is not None))
        return _result(settings.simulations)

    def numpy_resolution(settings, fighter, enemy):
        return replace(settings, batch_size=100_000), "numpy"

    candidates = tuple(
        ComparisonCandidate(f"c{index}", f"C{index}", build("weapon.mace")) for index in range(50)
    )
    settings = DuelExecutionSettings(1_000_000, 11, 100_000, 5)
    with patch("mordheim_combat_lab.application.analyses.simulate_duel", slow_baseline), \
            patch("mordheim_combat_lab.application.analyses.simulate_battery", fake_battery), \
            patch("mordheim_combat_lab.application.analyses.resolve_fighter_settings",
                  numpy_resolution), \
            patch("concurrent.futures.ProcessPoolExecutor", FakePool):
        compare_builds(build(), build(), candidates, settings, Event())

    # Candidates run at the measured pooled batch; the sequential baseline
    # kept the numpy sequential optimum it measured with.
    assert batches and all(batch == 25_000 and pooled for batch, pooled in batches)


def test_compare_builds_stays_sequential_when_the_measured_cost_is_tiny():
    pools = []

    class FakePool:
        def __init__(self, max_workers=None):
            pools.append(self)

    def instant_baseline(request):
        return _result(request.simulations)

    def fake_battery(fighter, enemy, settings, cancel_event, workers=None, pool=None):
        return _result(settings.simulations)

    candidates = tuple(
        ComparisonCandidate(f"c{index}", f"C{index}", build("weapon.mace")) for index in range(100)
    )
    # Same 1M samples and width as the engaging run: only the measured cost
    # differs, and the decision is driven by the measurement.
    settings = DuelExecutionSettings(1_000_000, 11, 5_000, 5)
    with patch("mordheim_combat_lab.application.analyses.simulate_duel", instant_baseline), \
            patch("mordheim_combat_lab.application.analyses.simulate_battery", fake_battery), \
            patch("concurrent.futures.ProcessPoolExecutor", FakePool):
        compare_builds(build(), build(), candidates, settings, Event())

    assert pools == []


def test_compare_builds_reuses_one_pool_for_the_whole_run():
    pools = []
    calls = []

    class FakePool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers
            self.shutdown_called = False
            pools.append(self)

        def shutdown(self, wait=True):
            self.shutdown_called = True

    def fake_duel(request):
        calls.append(("baseline", None))
        return _result(request.simulations)

    def fake_battery(fighter, enemy, settings, cancel_event, workers=None, pool=None):
        calls.append(("candidate", pool))
        return simulate_battery(fighter, enemy, settings, cancel_event, workers=0)

    candidates = (
        ComparisonCandidate("mace", "Mace", build("weapon.mace")),
        ComparisonCandidate("sword", "Sword", build("weapon.sword")),
    )
    settings = DuelExecutionSettings(2_000, 11, 1_000, 5)
    with patch("mordheim_combat_lab.application.analyses.simulate_duel", fake_duel), \
            patch("mordheim_combat_lab.application.analyses.simulate_battery", fake_battery), \
            patch("concurrent.futures.ProcessPoolExecutor", FakePool):
        compare_builds(build(), build(), candidates, settings, Event(), workers=2)

    assert len(pools) == 1  # one executor for every candidate
    assert calls[0] == ("baseline", None)  # the baseline calibrates in-process
    assert calls[1:] == [("candidate", pools[0]), ("candidate", pools[0])]
    assert pools[0].max_workers == 2
    assert pools[0].shutdown_called
