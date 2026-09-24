"""external.test_calibration_overrides: measured profiles over the defaults."""
from __future__ import annotations

import pytest

from mordheim_combat_lab.application.settings import (
    CALIBRATION_SCHEMA,
    DuelExecutionSettings,
    apply_calibration,
    battery_pool_plan,
    default_batch_size,
    measured_pool_speedups,
    pool_batch_size,
    pool_spawn_seconds,
    pool_speedup,
    pool_workers,
)

PROFILE = {
    "schema": CALIBRATION_SCHEMA,
    "batch_sizes": {"native": 7_500, "numpy": 50_000},
    "pooled_batch_sizes": {"native": 2_500, "numpy": 12_500},
    "pool_workers": {"native": 10, "numpy": 6},
    "spawn_seconds": {"native": 0.05, "numpy": 0.03},
    "evidence": {"native": {"ignored": True}},
}

#: Synthetic worker sweep with a known solution: 100k sequential samples and
#: 200k pooled samples at batch 5k make 4 and 8 segments, and the walls give
#: a per-pair speedup of 3.3333x at 4 workers and 6.25x at 8 (the raw ratio is
#: the sequential per-duel cost over the pooled one).
MEASURED_CURVE_PROFILE = {
    "schema": CALIBRATION_SCHEMA,
    "batch_sizes": {"native": 5_000},
    "pooled_batch_sizes": {"native": 5_000},
    "pool_workers": {"native": 8},
    "spawn_seconds": {"native": 0.20},
    "method": {"samples": {"native": {"sequential": 100_000, "pooled": 200_000}}},
    "evidence": {"native": {
        "sequential_batch": {"seconds": {"5000": [0.100, 0.200, 0.400]}},
        "pooled_workers": {"seconds": {
            "4": [0.060, 0.120, 0.240],
            "8": [0.032, 0.064, 0.128],
        }},
    }},
}

#: A machine whose 12-worker pool only measures 1.5x (spawn dominates, slow
#: cores): the shared 4.8x estimate would engage, the measured curve refuses.
PESSIMISTIC_PROFILE = {
    "schema": CALIBRATION_SCHEMA,
    "batch_sizes": {"native": 5_000},
    "pooled_batch_sizes": {"native": 5_000},
    "pool_workers": {"native": 12},
    "spawn_seconds": {"native": 0.20},
    "method": {"samples": {"native": {"sequential": 60_000, "pooled": 60_000}}},
    "evidence": {"native": {
        "sequential_batch": {"seconds": {"5000": [0.090]}},
        "pooled_workers": {"seconds": {"12": [0.060]}},
    }},
}


@pytest.fixture(autouse=True)
def _reference_defaults():
    """No test may leak measured constants into the rest of the session."""
    apply_calibration(None)
    yield
    apply_calibration(None)


def test_profile_replaces_every_measured_axis():
    applied = apply_calibration(PROFILE)

    assert default_batch_size("native") == 7_500
    assert default_batch_size("numpy") == 50_000
    assert pool_workers("native") == 10
    assert pool_workers("numpy") == 6
    assert pool_workers("auto") == 10  # auto follows the native measurement
    assert pool_spawn_seconds("native") == 0.05
    assert pool_spawn_seconds("auto") == 0.05
    assert pool_batch_size("numpy", DuelExecutionSettings(1_000_000, 7, 100_000, 20)) == 12_500
    # Native resolves its sequential default to the calibrated 7.5k, and the
    # pooled batch then switches to the measured 2.5k.
    assert pool_batch_size("native", DuelExecutionSettings(1_000_000, 7, 7_500, 20)) == 2_500
    assert set(applied) == {"batch_sizes", "pooled_batch_sizes", "pool_workers", "spawn_seconds"}


def test_untouched_axes_keep_the_reference_values():
    apply_calibration({"schema": CALIBRATION_SCHEMA, "pool_workers": {"numpy": 6}})

    assert default_batch_size("native") == 5_000
    assert default_batch_size("numpy") == 100_000
    assert pool_workers("native") == 14
    assert pool_workers("numpy") == 6
    assert pool_spawn_seconds("numpy") == 0.20


def test_explicit_batches_are_never_rewritten_by_calibration():
    apply_calibration(PROFILE)
    explicit = DuelExecutionSettings(1_000_000, 7, 40_000, 20)
    assert pool_batch_size("numpy", explicit) == 40_000


def test_hostile_or_foreign_payloads_are_ignored():
    assert apply_calibration({"schema": "mordheim-combat-lab-calibration/v99",
                              "pool_workers": {"native": 3}}) == {}
    assert apply_calibration({"pool_workers": {"native": 3}}) == {}
    assert apply_calibration({"schema": CALIBRATION_SCHEMA,
                              "pool_workers": {"native": 999, "numpy": 0, "auto": 2.5},
                              "spawn_seconds": {"native": -1.0},
                              "batch_sizes": {"native": 10},
                              "unknown_section": {"native": 1}}) == {}

    assert pool_workers("native") == 14
    assert pool_workers("numpy") == 8
    assert pool_spawn_seconds("native") == 0.24
    assert default_batch_size("native") == 5_000


def test_empty_payload_restores_the_reference_defaults():
    apply_calibration(PROFILE)
    assert apply_calibration({}) == {}
    assert default_batch_size("native") == 5_000
    assert pool_workers("native") == 14
    assert pool_spawn_seconds("numpy") == 0.20


def test_measured_curve_replaces_the_shared_model_per_backend():
    applied = apply_calibration(MEASURED_CURVE_PROFILE)

    assert applied["pool_speedups"] == {"native": {4: 3.3333, 8: 6.25}}
    # Anchors are the measured worker counts.
    assert pool_speedup(4, "native") == pytest.approx(3.3333, abs=1e-3)
    assert pool_speedup(8, "native") == pytest.approx(6.25, abs=1e-3)
    # Linear between anchors: 6 segments sits halfway, above the shared 3.6x.
    assert pool_speedup(6, "native") == pytest.approx((3.3333 + 6.25) / 2, abs=1e-3)
    # Above the measured range the largest measurement is held.
    assert pool_speedup(12, "native") == pytest.approx(6.25, abs=1e-3)
    # Below it the lowest anchor's efficiency is held (3.3333x over 4 segments).
    assert pool_speedup(3, "native") == pytest.approx(2.5, abs=1e-3)
    assert pool_speedup(2, "native") == pytest.approx(1.6667, abs=1e-3)


def test_shared_curve_remains_the_fallback_for_unmeasured_backends():
    apply_calibration(MEASURED_CURVE_PROFILE)
    shared = 12 * 0.40

    assert pool_speedup(12, "numpy") == pytest.approx(shared)  # no numpy evidence
    assert pool_speedup(12) == pytest.approx(shared)  # no backend asked for
    assert pool_speedup(12, "modular") == pytest.approx(shared)  # unknown backend
    assert pool_speedup(12, "auto") == pytest.approx(6.25, abs=1e-3)  # auto follows native

    apply_calibration(None)
    assert pool_speedup(12, "native") == pytest.approx(shared)


def test_measured_curve_changes_the_pool_decision():
    settings = DuelExecutionSettings(100_000, 7, 5_000, 20)
    # Shared model (14 workers, 5.6x): two fighters save 0.284 s against the
    # 0.30 s spawn gate — sequential.
    assert battery_pool_plan(0.175, settings, "native", 2) is None

    apply_calibration(MEASURED_CURVE_PROFILE)
    # This machine measured 6.25x at 8 workers: the same run clears the gate.
    assert battery_pool_plan(0.175, settings, "native", 2) == 8


def test_a_slow_machine_keeps_the_pool_sequential():
    settings = DuelExecutionSettings(60_000, 7, 5_000, 20)
    # Shared model (12 segments, 4.8x): five fighters save 0.328 s > 0.30 s.
    assert battery_pool_plan(0.0855, settings, "native", 5) == 14

    apply_calibration(PESSIMISTIC_PROFILE)
    # The profile measured only 1.5x: 0.133 s does not pay the 0.25 s gate.
    assert battery_pool_plan(0.0855, settings, "native", 5) is None


def test_measured_curve_ignores_degenerate_evidence():
    assert measured_pool_speedups({"schema": CALIBRATION_SCHEMA}) == {}
    assert measured_pool_speedups({"schema": "other", "evidence": {}, "method": {}}) == {}
    mismatched = {
        "schema": CALIBRATION_SCHEMA,
        "method": {"samples": {"native": {"sequential": 10_000, "pooled": 10_000}}},
        "evidence": {"native": {
            "sequential_batch": {"seconds": {"5000": [0.100, 0.200]}},
            "pooled_workers": {"seconds": {"2": [0.050]}},  # one pair, not two
        }},
    }
    assert measured_pool_speedups(mismatched) == {}


def test_measured_curve_clamps_points_to_physics():
    superlinear = {
        "schema": CALIBRATION_SCHEMA,
        "method": {"samples": {"native": {"sequential": 10_000, "pooled": 10_000}}},
        "evidence": {"native": {
            "sequential_batch": {"seconds": {"5000": [0.100]}},
            # 10x from a 2-segment pool is a measurement artifact, not physics.
            "pooled_workers": {"seconds": {"2": [0.010]}},
        }},
    }
    assert measured_pool_speedups(superlinear) == {"native": {2: 2.0}}

    losing = {
        "schema": CALIBRATION_SCHEMA,
        "method": {"samples": {"native": {"sequential": 20_000, "pooled": 20_000}}},
        "evidence": {"native": {
            "sequential_batch": {"seconds": {"5000": [0.100]}},
            # Pooling is 4x *slower* here: recorded as "no gain", never a bonus.
            "pooled_workers": {"seconds": {"4": [0.400]}},
        }},
    }
    assert measured_pool_speedups(losing) == {"native": {4: 1.0}}
