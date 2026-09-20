"""persistence: Local usage telemetry for simulation runs.

Appends one JSON Lines record per completed simulation run under the
per-user data directory. Purely local: no network, no identifiers, and
every failure is swallowed — telemetry must never disturb a simulation.
"""
from __future__ import annotations

import json as json
import os as os
import time as time
from pathlib import Path
from typing import Any, Mapping

_SCHEMA = "mordheim-combat-lab-usage/v1"


def usage_log_path() -> Path:
    """Per-user JSONL location, next to the settings file."""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "Mordheim Combat Lab" / "usage-log.jsonl"


def _compact(value: Any) -> Any:
    """Reduce values to JSON-safe, privacy-friendly primitives."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): _compact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_compact(item) for item in value]
    return str(value)


def append_usage_record(fields: Mapping[str, Any]) -> None:
    """Append one telemetry record; never raises.

    Schema ``mordheim-combat-lab-usage/v1``: ``schema``, ISO-8601 ``ts``,
    monotonic-safe ``epoch_s`` plus the caller's fields (tab, simulation
    sizes, per-fighter resolutions with the real engine and wall time).
    """
    record = {
        "schema": _SCHEMA,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "epoch_s": round(time.time(), 3),
        **{key: _compact(value) for key, value in fields.items()},
    }
    try:
        path = usage_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # telemetry must never disturb a simulation


def read_usage_records(limit: int | None = None) -> list[dict]:
    """Return recent records (oldest first); ``limit`` keeps the newest."""
    try:
        lines = usage_log_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict):
            records.append(value)
    if limit is not None and len(records) > limit:
        return records[-limit:]
    return records
