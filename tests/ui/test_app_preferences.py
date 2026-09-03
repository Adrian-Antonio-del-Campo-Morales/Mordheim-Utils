"""external.test_app_preferences: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_combat_lab.ui.app import _preference_int


def test_preference_int_uses_default_for_invalid_or_out_of_range_values():
    assert _preference_int({"count": "20"}, "count", 10, 1) == 20
    assert _preference_int({"count": "bad"}, "count", 10, 1) == 10
    assert _preference_int({"count": 0}, "count", 10, 1) == 10
