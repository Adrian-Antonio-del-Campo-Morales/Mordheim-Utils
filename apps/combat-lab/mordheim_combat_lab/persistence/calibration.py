"""persistence: Machine calibration profile for the Combat Lab.

Holds the JSON document written by ``mordheim-combat-lab calibrate`` next to
the preferences and the usage log. Purely local: the app loads it at startup
and layers its measured values over the reference-machine constants
(:func:`mordheim_combat_lab.application.settings.apply_calibration`);
every failure is swallowed so a missing or corrupt profile can never prevent
the simulator from starting.
"""
from __future__ import annotations

import json as json
import os as os
from pathlib import Path
from typing import Any, Mapping


def calibration_path() -> Path:
    """Per-user profile location, next to the settings file."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "Mordheim Combat Lab" / "calibration.json"


def load_calibration() -> dict:
    """Read the installed profile; an empty mapping when absent or corrupt."""
    try:
        value = json.loads(calibration_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save_calibration(payload: Mapping[str, Any]) -> Path | None:
    """Install a profile, returning its path (``None`` when unwritable)."""
    path = calibration_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(payload), indent=2), encoding="utf-8")
    except OSError:
        return None
    return path


def clear_calibration() -> bool:
    """Remove the installed profile (``False`` when there was nothing to remove)."""
    try:
        calibration_path().unlink()
        return True
    except OSError:
        return False
