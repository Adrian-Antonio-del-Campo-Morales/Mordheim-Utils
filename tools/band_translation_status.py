"""Report the Spanish-translation status of every band in the knowledge base.

Usage::

    python tools/band_translation_status.py            # summary table
    python tools/band_translation_status.py --json     # machine-readable
    python tools/band_translation_status.py --band X   # detail for one band

A *field* is one translatable string: a band name, a profile name, a special
rule name or a special-rule effect. The status counts fields whose
``name_i18n.es`` / ``effect_i18n.es`` is filled versus ``null``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

BANDS_ROOT = Path(__file__).resolve().parent.parent / "sources" / "knowledge" / "bands"


def band_fields(band_dir: Path) -> dict:
    """Count translatable fields and translated ones for one band."""
    total = filled = 0
    detail = {"band_name": [0, 0], "profiles": [0, 0], "rules": [0, 0], "effects": [0, 0]}

    band_file = band_dir / "band.yaml"
    if band_file.exists():
        doc = yaml.safe_load(band_file.read_text(encoding="utf-8")) or {}
        if doc.get("name"):
            total += 1
            i18n = doc.get("name_i18n") or {}
            if i18n.get("es"):
                filled += 1
                detail["band_name"][1] += 1
            detail["band_name"][0] += 1

    profiles_file = band_dir / "profiles.yaml"
    if profiles_file.exists():
        doc = yaml.safe_load(profiles_file.read_text(encoding="utf-8")) or {}
        for profile in doc.get("profiles") or []:
            if not profile.get("name"):
                continue
            total += 1
            detail["profiles"][0] += 1
            if (profile.get("name_i18n") or {}).get("es"):
                filled += 1
                detail["profiles"][1] += 1

    rules_file = band_dir / "special-rules.yaml"
    if rules_file.exists():
        doc = yaml.safe_load(rules_file.read_text(encoding="utf-8")) or {}
        for rule in doc.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            if rule.get("name"):
                total += 1
                detail["rules"][0] += 1
                if (rule.get("name_i18n") or {}).get("es"):
                    filled += 1
                    detail["rules"][1] += 1
            if rule.get("effect"):
                total += 1
                detail["effects"][0] += 1
                if (rule.get("effect_i18n") or {}).get("es"):
                    filled += 1
                    detail["effects"][1] += 1

    return {"total": total, "filled": filled, "detail": detail}


def all_bands() -> list[tuple[str, dict]]:
    rows = []
    for collection in sorted(BANDS_ROOT.iterdir()):
        if not collection.is_dir():
            continue
        for band_dir in sorted(collection.iterdir()):
            if band_dir.is_dir():
                rows.append((f"{collection.name}/{band_dir.name}", band_fields(band_dir)))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="output JSON")
    parser.add_argument("--band", help="show detail for one band (collection/name)")
    args = parser.parse_args()

    if args.band:
        collection, _, name = args.band.partition("/")
        band_dir = BANDS_ROOT / collection / name
        if not band_dir.is_dir():
            print(f"band not found: {args.band}", file=sys.stderr)
            return 1
        info = band_fields(band_dir)
        print(json.dumps(info, indent=2))
        return 0

    rows = all_bands()
    total = sum(info["total"] for _, info in rows)
    filled = sum(info["filled"] for _, info in rows)

    if args.json:
        print(json.dumps({
            "bands": {name: info for name, info in rows},
            "total": total,
            "filled": filled,
            "percent": round(100 * filled / total, 1) if total else 100.0,
        }, indent=2))
        return 0

    print(f"{'BAND':52s} {'FIELDS':>7s} {'DONE':>6s} {'%':>6s}")
    for name, info in rows:
        pct = f"{100 * info['filled'] / info['total']:.0f}%" if info["total"] else "-"
        print(f"{name:52s} {info['total']:7d} {info['filled']:6d} {pct:>6s}")
    print("-" * 74)
    pct = f"{100 * filled / total:.1f}%" if total else "-"
    print(f"{'TOTAL':52s} {total:7d} {filled:6d} {pct:>6s}")
    return 0


if __name__ == "__main__":
    main()
