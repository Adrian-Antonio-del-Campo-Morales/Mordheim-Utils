"""No conditional rule lives exclusively in the vectorized engine."""
from __future__ import annotations

from pathlib import Path
import re as re


ROOT = Path(__file__).resolve().parents[2]


def test_no_legacy_conditional_tag_is_absent_from_the_modular_engine():
    legacy = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "src/mordheim_combat/vectorized").glob("*.py"))
    )
    modular_paths = [ROOT / "src/mordheim_combat/phases.py"]
    modular_paths.extend((ROOT / "src/mordheim_combat/modular").glob("*.py"))
    modular_paths.append(ROOT / "src/mordheim_combat_lab/verification/consumers.py")
    modular = "\n".join(path.read_text(encoding="utf-8") for path in modular_paths)
    conditional_tags = set(re.findall(r'has\w*\([^\n]*?["\']([^"\']+)["\']', legacy))
    assert {tag for tag in conditional_tags if tag not in modular} == set()
