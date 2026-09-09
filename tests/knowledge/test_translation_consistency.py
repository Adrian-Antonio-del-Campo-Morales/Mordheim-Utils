"""Translation consistency guard: one English text must map to one Spanish text.

Duplicate rule prose is common across the knowledge base (the same
"Immune to psychology." or "Causes fear." clause is copied into every band and
hireling that uses it, and rule names repeat the same way). When independent
translation passes touch different copies, the same English text can end up
with two different Spanish renderings — the player sees one term in a band
sheet and a different one in a hireling entry for the identical rule. The
glossary (``catalog/translation-glossary.md``) exists precisely to prevent that.

This test walks every YAML document under the KB and, for each localized field
family (``effect``/``effect_i18n``, ``note``/``note_i18n``, ``name``/``name_i18n``),
collects the ``.es`` values keyed by their normalized canonical English text.
It fails when any English text resolves to more than one Spanish translation.

Names get one extra guard: the same English name must not appear both
translated and untranslated, because the KB display readers
(``mordheim_knowledge.i18n.display_name``) fall back to the canonical English
name and that mixture would render one rule in two languages depending on
which copy the UI happens to read.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

KB_ROOT = Path(__file__).resolve().parents[2] / "sources" / "knowledge"

#: (canonical field, i18n block) families checked for one-EN-one-ES consistency.
FIELD_FAMILIES = (
    ("effect", "effect_i18n"),
    ("note", "note_i18n"),
    ("name", "name_i18n"),
)


def _normalize(text: str) -> str:
    """Collapse whitespace so folded YAML scalars compare equal."""
    return " ".join(str(text).split())


class _FamilyTracker:
    """Collects ES renderings per normalized EN text for one field family."""

    def __init__(self, field: str, i18n_field: str) -> None:
        self.field = field
        self.i18n_field = i18n_field
        self.en_to_es: dict[str, set[str]] = defaultdict(set)
        self.en_translated: dict[str, str] = {}
        self.en_untranslated: dict[str, str] = {}
        self.findings: list[str] = []

    def observe(self, node: dict, origin: str) -> None:
        en = node.get(self.field)
        if not isinstance(en, str) or not en:
            return
        key = _normalize(en)
        label = node.get("id") or node.get("name") or "?"
        i18n = node.get(self.i18n_field) if isinstance(node.get(self.i18n_field), dict) else None
        es = i18n.get("es") if i18n else None
        if isinstance(es, str) and es:
            es_value = _normalize(es)
            seen = self.en_to_es[key]
            if es_value not in seen:
                # First sighting defines the translation; later variants are conflicts.
                if seen:
                    self.findings.append(
                        f"{origin} ({label}): English {self.field} {key[:90]!r} already "
                        f"translated as {sorted(seen)[0][:90]!r} — this copy uses {es_value[:90]!r}"
                    )
                seen.add(es_value)
            self.en_translated.setdefault(key, f"{origin} ({label})")
            self.en_untranslated.pop(key, None)
        else:
            # A copy without a Spanish translation is only a (latent) conflict
            # when another copy of the same EN text is already translated: the
            # untranslated entry will render English while its twins render
            # Spanish for the identical rule.
            if key in self.en_translated:
                self.findings.append(
                    f"{origin} ({label}): English {self.field} {key[:90]!r} has no "
                    f"{self.i18n_field}.es while {self.en_translated[key]} translates it"
                )
            else:
                self.en_untranslated.setdefault(key, f"{origin} ({label})")


def test_same_english_text_always_gets_the_same_spanish_translation() -> None:
    trackers = [_FamilyTracker(field, i18n_field) for field, i18n_field in FIELD_FAMILIES]

    def walk(node, origin: str) -> None:
        if isinstance(node, dict):
            for tracker in trackers:
                tracker.observe(node, origin)
            for value in node.values():
                walk(value, origin)
        elif isinstance(node, list):
            for item in node:
                walk(item, origin)

    for kb_file in sorted(KB_ROOT.rglob("*.yaml")):
        doc = yaml.safe_load(kb_file.read_text(encoding="utf-8"))
        if doc is None:
            continue
        walk(doc, str(kb_file.relative_to(KB_ROOT)))

    findings = [finding for tracker in trackers for finding in tracker.findings]
    assert not findings, (
        f"{len(findings)} inconsistent translation(s) "
        "(same English text, different or missing Spanish):\n" + "\n".join(findings)
    )
