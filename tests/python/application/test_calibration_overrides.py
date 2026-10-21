"""external.test_calibration_overrides: measured profiles over the defaults."""
from __future__ import annotations

import pytest

from mordheim_combat_lab.application.settings import (
    CALIBRATION_SCHEMA,
    DuelExecutionSettings,
    apply_calibration,
    default_batch_size,
    pool_batch_size,
    pool_spawn_seconds,
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


@pytest.fixture(autouse=True)
def _reference_defaults():
    """No test may leak measured constants into the rest of the session."""
    apply_calibration(None)
    yield
    apply_calibration(None)


@pytest.mark.workflow
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


@pytest.mark.workflow
def test_untouched_axes_keep_the_reference_values():
    apply_calibration({"schema": CALIBRATION_SCHEMA, "pool_workers": {"numpy": 6}})

    assert default_batch_size("native") == 5_000
    assert default_batch_size("numpy") == 100_000
    assert pool_workers("native") == 14
    assert pool_workers("numpy") == 6
    assert pool_spawn_seconds("numpy") == 0.20


@pytest.mark.workflow
def test_explicit_batches_are_never_rewritten_by_calibration():
    apply_calibration(PROFILE)
    explicit = DuelExecutionSettings(1_000_000, 7, 40_000, 20)
    assert pool_batch_size("numpy", explicit) == 40_000


# The foreign/hostile payloads are rejected on shape and schema version.
@pytest.mark.data_contract
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


@pytest.mark.workflow
def test_empty_payload_restores_the_reference_defaults():
    apply_calibration(PROFILE)
    assert apply_calibration({}) == {}
    assert default_batch_size("native") == 5_000
    assert pool_workers("native") == 14
    assert pool_spawn_seconds("numpy") == 0.20
