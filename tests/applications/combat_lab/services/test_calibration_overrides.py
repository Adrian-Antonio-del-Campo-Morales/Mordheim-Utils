"""external.test_calibration_overrides: measured profiles over the defaults."""
from __future__ import annotations

import pytest

from mordheim_combat_lab.application.settings import (
    CALIBRATION_SCHEMA,
    DuelExecutionSettings,
    apply_calibration,
    default_batch_size,
    measured_pool_speedups,
    pool_speedup,
    pool_spawn_seconds,
    pool_workers,
)

PROFILE = {
    "schema": CALIBRATION_SCHEMA,
    "batch_sizes": {"native": 7_500, "numpy": 50_000},
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


def test_profile_replaces_every_measured_axis():
    applied = apply_calibration(PROFILE)

    assert default_batch_size("native") == 7_500
    assert default_batch_size("numpy") == 50_000
    assert pool_workers("native") == 10
    assert pool_workers("numpy") == 6
    assert pool_workers("auto") == 10  # auto follows the native measurement
    assert pool_spawn_seconds("native") == 0.05
    assert pool_spawn_seconds("auto") == 0.05
    assert set(applied) == {"batch_sizes", "pool_workers", "spawn_seconds"}


def test_untouched_axes_keep_the_reference_values():
    apply_calibration({"schema": CALIBRATION_SCHEMA, "pool_workers": {"numpy": 6}})

    assert default_batch_size("native") == 5_000
    assert default_batch_size("numpy") == 100_000
    assert pool_workers("native") == 14
    assert pool_workers("numpy") == 6
    assert pool_spawn_seconds("numpy") == 0.20


def test_legacy_pooled_batch_section_is_ignored():
    applied = apply_calibration({**PROFILE, "pooled_batch_sizes": {"numpy": 12_500}})
    assert "pooled_batch_sizes" not in applied


def sweep_profile(*, sequential_batch, sweep_batch=None, legacy_pooled=None):
    """Numpy evidence: 4 pairs of 1s sequential at 400k, 0.5s pooled at 800k."""
    profile = {
        "schema": CALIBRATION_SCHEMA,
        "batch_sizes": {"numpy": sequential_batch},
        "method": {"samples": {"numpy": {"sequential": 400_000, "pooled": 800_000}}},
        "evidence": {"numpy": {
            "sequential_batch": {"seconds": {str(sequential_batch): [1.0, 1.0]}},
            "pooled_workers": {"seconds": {"4": [0.5, 0.5], "8": [0.4, 0.4]}},
        }},
    }
    if sweep_batch is not None:
        profile["method"]["worker_sweep_batch"] = {"numpy": sweep_batch}
    if legacy_pooled is not None:
        profile["pooled_batch_sizes"] = {"numpy": legacy_pooled}
    return profile


def test_speedup_curve_uses_the_batch_the_workers_were_swept_at():
    # 800k at 100k = 8 batches: 4 workers -> 4 segments, 8 -> 8 segments.
    curve = measured_pool_speedups(sweep_profile(sequential_batch=100_000, sweep_batch=100_000))
    assert curve == {"numpy": {4: 4.0, 8: 5.0}}
    apply_calibration(sweep_profile(sequential_batch=100_000, sweep_batch=100_000))
    assert pool_speedup(8, "numpy") == 5.0


def test_curve_measured_at_another_batch_is_not_installed():
    # Old profiles swept workers at the pooled batch (25k by default); that
    # configuration no longer runs, so the shared conservative curve applies.
    assert measured_pool_speedups(sweep_profile(sequential_batch=100_000)) == {}
    assert measured_pool_speedups(
        sweep_profile(sequential_batch=100_000, legacy_pooled=25_000)) == {}
    # An old profile whose pooled batch equalled the sequential one still counts.
    assert measured_pool_speedups(
        sweep_profile(sequential_batch=100_000, legacy_pooled=100_000)) == {
            "numpy": {4: 4.0, 8: 5.0}}


# The foreign/hostile payloads are rejected on shape and schema version.
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


# Provenance is checked, never enforced: a profile from another machine or
# engine build is applied with a recorded PROVENANCE WARNING.
STAMP = {
    "cpu_count": 12, "platform": "Linux-x", "python": "3.14.4", "numpy": "2.5.4",
    "engine_digests": {"numpy": "a" * 64, "native": "b" * 64},
    "native_build_sha256": "c" * 64,
    "revision": {"commit": "abc", "dirty": False},
}


@pytest.fixture
def stamped(monkeypatch):
    from mordheim_combat_lab.application import settings

    monkeypatch.setattr(settings, "measurement_provenance",
                        lambda engines, emit=True: dict(STAMP))


def test_profile_from_this_machine_and_engine_applies_silently(stamped, capsys):
    from mordheim_combat_lab.application.settings import calibration_provenance_warnings

    apply_calibration({**PROFILE, "provenance": STAMP})
    assert calibration_provenance_warnings() == ()
    assert "PROVENANCE WARNING" not in capsys.readouterr().err


def test_profile_from_elsewhere_warns_and_is_still_applied(stamped, capsys):
    from mordheim_combat_lab.application.settings import calibration_provenance_warnings

    foreign = {**STAMP, "cpu_count": 32, "native_build_sha256": "d" * 64}
    applied = apply_calibration({**PROFILE, "provenance": foreign})
    assert applied and pool_workers("native") == 10
    (warning,) = calibration_provenance_warnings()
    assert "CPU count differs" in warning and "native build differs" in warning
    assert "random streams" in warning
    assert "PROVENANCE WARNING" in capsys.readouterr().err
    apply_calibration(None)
    assert calibration_provenance_warnings() == ()


def test_profile_without_provenance_warns_that_it_is_unknown(stamped):
    from mordheim_combat_lab.application.settings import calibration_provenance_warnings

    apply_calibration(PROFILE)
    assert default_batch_size("native") == 7_500
    (warning,) = calibration_provenance_warnings()
    assert "records no provenance" in warning
