"""Pipeline gate: pinned spec digests must match the live KB inventory.

Wraps ``tools/refresh_spec_digests.py --check``. Data-only KB edits (i18n
fills, formatting that preserves parsed values) legitimately move the
fingerprints; this gate reports that drift loudly so the digests get
refreshed intentionally instead of silently going stale.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "refresh_spec_digests.py"


def test_spec_digest_pins_are_fresh() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        "refresh_spec_digests --check reported stale digest pins:\n"
        + (result.stdout or result.stderr)
    )
