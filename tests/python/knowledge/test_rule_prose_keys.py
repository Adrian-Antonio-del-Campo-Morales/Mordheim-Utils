"""Rule prose has exactly one key: ``effect``.

Band rules, catalog skills/mechanics, conditions, spells, scenarios,
mutations and artefact blurbs always use the single key understood by the
readers, coverage guard and formatter. This test is the permanent guard that
prevents the retired ``summary`` key from returning to the knowledge base.
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
        f"key: {offenders}"
    )
