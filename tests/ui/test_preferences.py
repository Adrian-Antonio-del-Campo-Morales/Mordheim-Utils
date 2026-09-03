"""external.test_preferences: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_combat_lab.persistence.preferences import load_preferences
from mordheim_combat_lab.persistence.preferences import save_preferences


def test_preferences_round_trip_arbitrary_ui_values(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr("mordheim_combat_lab.persistence.preferences.settings_path", lambda: path)

    save_preferences({"simulations": 12_000, "window_geometry": "1200x800"})

    assert load_preferences() == {"simulations": 12_000, "window_geometry": "1200x800"}
