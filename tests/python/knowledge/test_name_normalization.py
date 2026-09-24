"""Pipeline gate: every KB name must satisfy the capitalization policy.

Wraps ``tools/knowledge/maintenance/normalize_names.py --check`` so the rule documented in the
docs (``name`` and ``name_i18n.es`` title-cased, canonical scalar quoting,
no ``en`` mirrors, no empty locale blocks) is enforced on every test run,
not only when someone remembers to run the tool by hand.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / "tools" / "knowledge" / "maintenance" / "normalize_names.py"
KB_ROOT = ROOT / "sources" / "knowledge"


def test_kb_names_are_normalized() -> None:
    result = subprocess.run(
        [sys.executable, str(TOOL), "--check", str(KB_ROOT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        "normalize_names --check reported files needing normalization:\n"
        + (result.stdout or result.stderr)
    )
