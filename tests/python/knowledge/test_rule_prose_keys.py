"""Rule prose has exactly one key: ``effect``.

The KB-wide migration (`tools/knowledge/maintenance/rename_summary_keys.py`) renamed every prose
``summary`` mapping key to ``effect`` (and the count metadata block of
``implemented-canonical-families.yaml`` to ``counts``) so that rule text —
band rules, catalog skills/mechanics, conditions, spells, scenarios,
mutations and artefact blurbs — always lives under the single key the
readers, coverage guard and formatter understand. This test guards that no
``summary`` key ever returns to ``sources/knowledge``.
"""
from __future__ import annotations

from pathlib import Path

import yaml

KB_ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"


def _keys(node) -> set:
    if isinstance(node, dict):
        result = set(node)
        for value in node.values():
            result |= _keys(value)
        return result
    if isinstance(node, list):
        result = set()
        for value in node:
            result |= _keys(value)
        return result
    return set()


def test_no_summary_key_survives_in_the_knowledge_base() -> None:
    offenders: list[str] = []
    for path in sorted(KB_ROOT.rglob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if document is None:
            continue
        if "summary" in _keys(document):
            offenders.append(path.relative_to(KB_ROOT).as_posix())
    assert offenders == [], (
        "the rule-prose key is `effect`; these files still carry a `summary` "
        f"key (run tools/knowledge/maintenance/rename_summary_keys.py): {offenders}"
    )
