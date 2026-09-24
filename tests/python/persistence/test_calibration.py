"""external.test_calibration: machine calibration profile persistence."""
from __future__ import annotations

import json

from mordheim_combat_lab.persistence import calibration


def test_path_sits_next_to_the_preferences(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert calibration.calibration_path() == (
        tmp_path / "Mordheim Combat Lab" / "calibration.json")


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    payload = {"schema": "mordheim-combat-lab-calibration/v1", "pool_workers": {"native": 12}}

    path = calibration.save_calibration(payload)

    assert path == tmp_path / "Mordheim Combat Lab" / "calibration.json"
    assert json.loads(path.read_text(encoding="utf-8"))["pool_workers"] == {"native": 12}
    assert calibration.load_calibration() == payload


def test_missing_or_corrupt_profile_loads_as_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert calibration.load_calibration() == {}

    path = calibration.calibration_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json", encoding="utf-8")
    assert calibration.load_calibration() == {}

    path.write_text("[1, 2]", encoding="utf-8")  # valid JSON, wrong shape
    assert calibration.load_calibration() == {}


def test_unwritable_profile_never_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    blocked = tmp_path / "Mordheim Combat Lab"
    blocked.write_text("a file where the directory should be", encoding="utf-8")
    assert calibration.save_calibration({"schema": "x"}) is None


def test_clear_reports_whether_something_was_removed(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert calibration.clear_calibration() is False
    calibration.save_calibration({"schema": "mordheim-combat-lab-calibration/v1"})
    assert calibration.clear_calibration() is True
    assert calibration.load_calibration() == {}
