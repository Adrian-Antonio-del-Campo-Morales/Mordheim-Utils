"""external.test_usage_observation: compare_builds usage telemetry payloads."""
from __future__ import annotations

from threading import Event

import pytest

from mordheim_combat_lab.application.analyses import ComparisonCandidate, compare_builds
from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_core.models import Characteristics, FighterBuild, SimulationCancelled


def build(weapon="weapon.dagger"):
    return FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1), main_weapon_id=weapon)


def test_compare_builds_reports_resolution_and_timings():
    captured = []
    candidates = (ComparisonCandidate("mace", "Mace", build("weapon.mace")),)
    compare_builds(build(), build(), candidates, DuelExecutionSettings(2_000, 11, 1_000, 5),
                   Event(), observe=captured.append)
    (payload,) = captured
    assert payload["baseline"]["id"] == "baseline"
    assert payload["candidates"][0]["id"] == "mace"
    for row in (payload["baseline"], *payload["candidates"]):
        assert row["simulations"] == 2_000
        assert row["batch_size"] == 1_000  # explicit batch is honoured verbatim
        assert row["engine"] in ("native", "numpy")
        assert row["workers"] == 0
        assert row["wall_seconds"] > 0
    # Small samples: the measured baseline rules the pool out, and the log
    # keeps the calibration inputs for later recalibration.
    assert payload["pool"]["workers"] == 0
    assert payload["pool"]["segments"] == 0
    assert payload["pool"]["baseline_seconds"] > 0


def test_compare_builds_reports_the_legacy_default_resolution():
    captured = []
    candidates = (ComparisonCandidate("mace", "Mace", build("weapon.mace")),)
    compare_builds(build(), build(), candidates, DuelExecutionSettings(10_000, 3, 100_000, 5),
                   Event(), observe=captured.append)
    (payload,) = captured
    for row in (payload["baseline"], *payload["candidates"]):
        # The legacy global default resolves to the engine actually running.
        assert row["batch_size"] in (5_000, 100_000)
        assert row["engine"] in ("native", "numpy")


def test_compare_builds_skips_records_on_cancellation():
    captured = []
    cancelled = Event()
    cancelled.set()
    with pytest.raises(SimulationCancelled):
        compare_builds(build(), build(), (), DuelExecutionSettings(1_000, 0, 1_000, 2),
                       cancelled, observe=captured.append)
    assert captured == []
