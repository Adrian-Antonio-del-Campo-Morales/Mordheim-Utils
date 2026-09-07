"""Translation coverage guard: catch partially translated rules.

A finished Spanish ``effect_i18n.es`` mirrors the whole English ``effect``.
When a translation was truncated during ingestion it ends mid-rule, which
shows up as *both* a short character ratio and a low sentence-unit ratio
(the pre-fix `band--kidnapped`, `band--stragglers-and-prisoners` and
`band--animosity` translations all sat near 0.3-0.5 on both axes while
complete translations hover near 1.0).

Legitimate concise translations collapse sentences but not text (the shortest
complete translation in the corpus sits at ~73% of the English length), so the
primary signal is character coverage: any Spanish text shorter than 70% of its
English effect is suspect. For multi-sentence rules the sentence axis must
agree (≤85% sentence-unit coverage) to tolerate punctuation noise; shorter
rules are judged on the character axis alone. The three truncations fixed so
far (`band--kidnapped`, `band--stragglers-and-prisoners`, `band--animosity`)
all sat between 0.28 and 0.47 on the character axis before repair.

Only 170 of the 1,537 `effect_i18n.es` pairs today are multi-sentence rules,
so the widened check matters: single-sentence effects can be truncated too.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

KB_ROOT = Path(__file__).resolve().parents[2] / "sources" / "knowledge"

_UNITS = re.compile(r"[.!?]")


def _sentence_units(text: str) -> int:
    return len(_UNITS.findall(text))


def _label(node: dict) -> str:
    for key in ("id", "item_id", "rule_id"):
        if node.get(key):
            return str(node[key])
    if node.get("name"):
        return str(node["name"])
    return "<unnamed>"


def _walk(node, path: list, findings: list) -> None:
    if isinstance(node, dict):
        effect = node.get("effect")
        es = (node.get("effect_i18n") or {}).get("es") if isinstance(node.get("effect_i18n"), dict) else None
        if (
            isinstance(effect, str)
            and isinstance(es, str)
            and es
            and es != effect
            and len(effect) > 60
        ):
            en_units = _sentence_units(effect)
            unit_ratio = _sentence_units(es) / en_units if en_units else 1.0
            char_ratio = len(es) / len(effect)
            # Truncation shows up as less than 70% of the English text; for
            # multi-sentence rules the sentence axis must agree (the shortest
            # complete translation in the corpus sits at ~73% length).
            if char_ratio < 0.70 and (en_units < 4 or unit_ratio <= 0.85):
                findings.append(
                    f"{path[-1] if path else '?'} {_label(node)}: sentence coverage "
                    f"{_sentence_units(es)}/{en_units} ({unit_ratio:.2f}), text "
                    f"{len(es)}/{len(effect)} chars ({char_ratio:.2f}) — translation "
                    "may stop before the end of the rule"
                )
        for key, value in node.items():
            _walk(value, path + [key], findings)
    elif isinstance(node, list):
        for item in node:
            _walk(item, path, findings)


def test_no_spanish_rule_translation_is_truncated() -> None:
    findings: list[str] = []
    for kb_file in sorted(KB_ROOT.rglob("*.yaml")):
        doc = yaml.safe_load(kb_file.read_text(encoding="utf-8"))
        if doc is None:
            continue
        _walk(doc, [kb_file.name], findings)
    assert not findings, "\n".join(findings)
