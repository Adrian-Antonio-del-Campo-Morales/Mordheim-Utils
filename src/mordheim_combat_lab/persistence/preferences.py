"""persistence.preferences: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

import json as json
import os as os
from pathlib import Path
from typing import Mapping


def settings_path() -> Path:
    """Per-user location compatible with the previous application."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "Mordheim Combat Lab" / "settings.json"


def load_preferences() -> dict:
    try:
        value = json.loads(settings_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save_preferences(values: Mapping[str, object]) -> None:
    """Persist UI-owned values without coupling them to a workbook schema."""
    path = settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(dict(values), indent=2), encoding="utf-8")
    except OSError:
        # Preferences must never prevent the simulator from starting.
        pass
