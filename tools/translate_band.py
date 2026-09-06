"""Apply reviewed Spanish translations to one band's YAML files.

Usage: python tools/translate_band.py <translation-file.yaml>

The translation file is a YAML document of the shape::

    band:
      mordheim/mercenaries: Mercenarios
    profiles:
      mercenary-captain: Capitán mercenario
      ...
    rules:
      mercenary-captain--leader:
        name: Líder
        effect: >-
          Cualquier guerrero a 6" del Capitán mercenario...
      ...

Only ``name_i18n.es`` / ``effect_i18n.es`` / band ``name_i18n.es`` are
touched; ids, runtime blocks, bindings and sources stay untouched. Values
are normalized to single logical lines (artifact newlines from the source
are not reproduced).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

BANDS_ROOT = Path(__file__).resolve().parent.parent / "sources" / "knowledge" / "bands"


def normalize(text: str) -> str:
    """Fold artifact newlines into single spaces."""
    return re.sub(r"\s*\n\s*", " ", str(text)).strip()


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    plan = yaml.safe_load(Path(sys.argv[1]).read_text(encoding="utf-8"))

    bands = plan.get("band") or {}
    if not bands:
        print("no band key in plan", file=sys.stderr)
        return 1
    band_path, band_es = next(iter(bands.items()))
    band_dir = BANDS_ROOT / band_path
    if not band_dir.is_dir():
        print(f"band not found: {band_path}", file=sys.stderr)
        return 1

    changed = 0

    band_file = band_dir / "band.yaml"
    band_doc = yaml.safe_load(band_file.read_text(encoding="utf-8")) or {}
    if band_doc.get("name"):
        i18n = band_doc.setdefault("name_i18n", {})
        i18n.setdefault("en", band_doc["name"])
        if i18n.get("es") != band_es:
            i18n["es"] = band_es
            changed += 1
    band_file.write_text(
        yaml.safe_dump(band_doc, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )

    profiles = plan.get("profiles") or {}
    profiles_file = band_dir / "profiles.yaml"
    if profiles:
        doc = yaml.safe_load(profiles_file.read_text(encoding="utf-8")) or {}
        for profile in doc.get("profiles") or []:
            pid = profile.get("id")
            if pid in profiles and profile.get("name"):
                es = profiles[pid]
                i18n = profile.setdefault("name_i18n", {})
                i18n.setdefault("en", profile["name"])
                if i18n.get("es") != es:
                    i18n["es"] = es
                    changed += 1
        profiles_file.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )

    rules = plan.get("rules") or {}
    rules_file = band_dir / "special-rules.yaml"
    if rules:
        doc = yaml.safe_load(rules_file.read_text(encoding="utf-8")) or {}
        for rule in doc.get("rules") or []:
            rid = rule.get("id")
            if rid not in rules:
                continue
            entry = rules[rid] or {}
            if rule.get("name") and entry.get("name"):
                i18n = rule.setdefault("name_i18n", {})
                i18n.setdefault("en", rule["name"])
                if i18n.get("es") != entry["name"]:
                    i18n["es"] = entry["name"]
                    changed += 1
            if rule.get("effect") and entry.get("effect"):
                i18n = rule.setdefault("effect_i18n", {})
                i18n.setdefault("en", normalize(rule["effect"]))
                es = normalize(entry["effect"])
                if i18n.get("es") != es:
                    i18n["es"] = es
                    changed += 1
        rules_file.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100),
            encoding="utf-8",
        )

    print(f"{band_path}: {changed} fields updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
