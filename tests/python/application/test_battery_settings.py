"""external.test_battery_settings: battery splitting, seeding and pooling."""
from __future__ import annotations

import pytest

from mordheim_combat_lab.application.settings import (
    DuelExecutionSettings,
    battery_pool_plan,
    default_batch_size,
    pool_batch_size,
    resolve_battery_settings,
    split_battery,
)

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
