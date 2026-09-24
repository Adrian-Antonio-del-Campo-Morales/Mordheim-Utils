"""external.test_2b_translation: Spanish translation guards for the 2B staging tree.

Every band package in ``sources/2B`` carries ``name_i18n.es`` /
``effect_i18n.es`` blocks alongside the canonical English text. These tests
pin the translation contract so partial or silently damaged translations
cannot reach promotion:

* **Names** (band, profiles, rules) must be translated as soon as the
  manifest claims ``modeled`` — transcription workers write them inline.
* **Effect translations** may still be pending at ``modeled`` (the
  translation pass runs later), but every translation that *exists* must be
  complete: never truncated mid-rule and never an English mirror.
* **i18n blocks must only contain locale keys.** A single-line flow mapping
  such as ``effect_i18n: {es: texto, con comas}`` is parsed by YAML with the
  ``es`` value ending at the first comma — the rest of the sentence becomes
  spurious sibling keys and is silently lost (this exact defect hit 30
  scalars in staging and was repaired by
  ``tools/ingestion/repair_2b_flow_i18n.py``).
* **Cross-band consistency**: two copies of the same English rule text must
  not carry different Spanish renderings (the same guard the active KB
  enforces in ``test_translation_consistency.py``).
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
STAGING = ROOT / "sources" / "2B"
MANIFEST = STAGING / "manifest.yaml"

#: Only real locales may appear inside an ``*_i18n`` block.
KNOWN_LOCALES = {"es", "en", "fr", "de", "it"}

#: Any Spanish effect shorter than 70% of its English text (beyond 60 chars)
#: is treated as truncated — the same threshold as the active KB guard.
MIN_CHAR_RATIO = 0.70


def _manifest_status() -> dict[str, str]:
    if not MANIFEST.exists():
        return {}
    document = yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}
    return {
        str(row.get("id")): str(row.get("status"))
        for row in document.get("bands") or []
        if isinstance(row, dict) and row.get("id")
    }


def _staging_band_dirs() -> list[Path]:
    bands = STAGING / "bands" / "mordheim"
    if not bands.exists():
        return []
    return [path for path in sorted(bands.iterdir()) if path.is_dir()]


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def test_modeled_bands_translate_all_names() -> None:
    """Band names, profile names and rule names carry ``name_i18n.es``."""
    status = _manifest_status()
    findings: list[str] = []
    for band_dir in _staging_band_dirs():
        if status.get(band_dir.name) not in {"modeled", "english-reviewed", "translated", "validated", "promotable"}:
            continue
        band = _load(band_dir / "band.yaml")
        if band.get("name") and not (band.get("name_i18n") or {}).get("es"):
            findings.append(f"{band_dir.name}: band name untranslated")
        profiles = _load(band_dir / "profiles.yaml")
        for profile in profiles.get("profiles") or []:
            if profile.get("name") and not (profile.get("name_i18n") or {}).get("es"):
                findings.append(f"{band_dir.name}: profile {profile.get('id')!r} name untranslated")
        rules = _load(band_dir / "special-rules.yaml")
        for rule in rules.get("rules") or []:
            if not isinstance(rule, dict) or not rule.get("name"):
                continue
            if not (rule.get("name_i18n") or {}).get("es"):
                findings.append(f"{band_dir.name}: rule {rule.get('id')!r} name untranslated")
    assert not findings, f"{len(findings)} untranslated name(s):\n" + "\n".join(findings)


def test_no_spanish_effect_translation_is_truncated_or_english() -> None:
    """Existing effect translations are complete — never cut mid-rule, never EN."""
    findings: list[str] = []
    for band_dir in _staging_band_dirs():
        rules_file = band_dir / "special-rules.yaml"
        if not rules_file.exists():
            continue
        rules = _load(rules_file)
        for rule in rules.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            effect = rule.get("effect")
            es = (rule.get("effect_i18n") or {}).get("es")
            if not isinstance(effect, str) or not effect:
                continue
            if es is None:
                continue  # translation pass has not run for this rule yet
            if not isinstance(es, str) or not es:
                findings.append(f"{band_dir.name}: rule {rule.get('id')!r} has an empty effect_i18n.es")
            elif es == effect:
                findings.append(f"{band_dir.name}: rule {rule.get('id')!r} Spanish effect equals the English text")
            elif len(effect) > 60 and len(es) < MIN_CHAR_RATIO * len(effect):
                ratio = len(es) / len(effect)
                findings.append(
                    f"{band_dir.name}: rule {rule.get('id')!r} Spanish effect is {ratio:.2f} of the "
                    "English length — translation may stop before the end of the rule"
                )
    assert not findings, f"{len(findings)} suspect translation(s):\n" + "\n".join(findings)


def test_i18n_blocks_only_contain_locale_keys() -> None:
    """``*_i18n`` mappings must never hold non-locale keys.

    This is the guard for flow-scalar comma damage: YAML silently splits
    ``{es: texto, con comas}`` into ``es: texto`` plus a ``con comas: null``
    sibling, losing the rest of the sentence without any parse error.
    """
    findings: list[str] = []

    def walk(node, where: str) -> None:
        if isinstance(node, dict):
            for field in ("name_i18n", "effect_i18n", "note_i18n"):
                block = node.get(field)
                if isinstance(block, dict):
                    unexpected = [key for key in block if key not in KNOWN_LOCALES]
                    if unexpected:
                        label = node.get("id") or node.get("name") or "?"
                        findings.append(
                            f"{where} {label} ({field}): non-locale keys {unexpected} — "
                            "the scalar was probably written as a flow mapping with commas"
                        )
            for key, value in node.items():
                walk(value, where)
        elif isinstance(node, list):
            for item in node:
                walk(item, where)

    for path in sorted(STAGING.rglob("*.yaml")):
        doc = _load(path)
        walk(doc, str(path.relative_to(STAGING)))
    assert not findings, f"{len(findings)} damaged i18n block(s):\n" + "\n".join(findings)


def test_same_english_effect_gets_the_same_spanish_translation() -> None:
    """One English effect text maps to at most one Spanish rendering."""
    en_to_es: dict[str, set[str]] = defaultdict(set)
    for band_dir in _staging_band_dirs():
        rules_file = band_dir / "special-rules.yaml"
        if not rules_file.exists():
            continue
        rules = _load(rules_file)
        for rule in rules.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            effect = rule.get("effect")
            es = (rule.get("effect_i18n") or {}).get("es")
            if isinstance(effect, str) and isinstance(es, str) and es:
                en_to_es[" ".join(effect.split())].add(" ".join(es.split()))
    findings = [
        f"{en[:70]!r}: {sorted(renderings)}"
        for en, renderings in sorted(en_to_es.items())
        if len(renderings) > 1
    ]
    assert not findings, f"{len(findings)} inconsistent translation(s):\n" + "\n".join(findings)
