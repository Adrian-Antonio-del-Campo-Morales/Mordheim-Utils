"""Pipeline gate: maintained YAML must satisfy the canonical formatting.

Wraps ``tools/format_yaml.py --check`` so the lexical formatting policy
(folded prose blocks, canonical scalar quoting, 120-column cap, semantic
round-trip) is enforced on every test run, not only when someone remembers
to run the tool by hand.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "format_yaml.py"
KB_ROOT = ROOT / "sources" / "knowledge"


def test_yaml_formatting_is_canonical() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--check", str(KB_ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        "format_yaml --check reported files needing reformatting:\n"
        + (result.stdout or result.stderr)
    )
