# -*- coding: utf-8 -*-
"""Cotejo de los 7 Dramatis Personae grade-2a (KB) contra la fuente mordheimer.net.

Para cada perfil: localiza su bloque en el texto de la página fuente y compara
fee/upkeep, fila de stats y presencia de los nombres de regla. Escribe un
informe JSON junto a este script.

Uso: python check_2a_dramatis.py
"""
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "build/cache/2a-dp/dramatis-grade-2a.txt"
PKG = ROOT / "sources/knowledge/catalog/hirelings/dramatis-personae/grade-2a.yaml"
OUT = ROOT / "build/cache/2a-dp/dp_check.json"


def main() -> int:
    t = re.sub(r"\s+", " ", SRC.read_text(encoding="utf-8"))
    t = t.replace("&#x27;", "'").replace("’", "'").replace("&quot;", '"')
    d = yaml.safe_load(PKG.read_text(encoding="utf-8"))

    names = [p["name"] for p in d["profiles"]]
    # nombres cortos de fila: DP largos se imprimen como alias ('Sprandle', 'Horseman', 'Foole', 'Gwen'...)
    aliases = {
        "Aksho'akhash the Vile Dreadwing, Lord of the Carrion Throne": ["Aksho"],
        "“Busty” Gwen": ["Gwen"],
        "The Dark Jester in Mordheim": ["Dark Jester", "Jester"],
        "The Headless Horseman": ["Horseman"],
        "The Foole": ["Foole"],
        "Sigmund Spindle, the Harvester of Flesh": ["Sprandle", "Spindle"],
        "William Schäkestange, Master Bard": ["Schäkestange", "William"],
    }

    # localizar inicios de bloque: '<alias> Source:' o '<alias> <italic-marker> Source:'
    pos = {}
    for nm in names:
        for alias in aliases.get(nm, [nm]):
            m = re.search(re.escape(alias) + r"\s*[\u200b ]*Source:", t)
            if m:
                pos[nm] = m.start()
                break

    order = sorted((v, k) for k, v in pos.items() if v is not None)
    blocks = {}
    for i, (start, nm) in enumerate(order):
        end = order[i + 1][0] if i + 1 < len(order) else len(t)
        blocks[nm] = t[start:end]

    report = []
    for p in d["profiles"]:
        nm = p["name"]
        b = blocks.get(nm, "")
        row = {"name": nm, "findings": []}
        if not b:
            row["findings"].append("bloque no localizado en la fuente")
            report.append(row)
            continue

        c = p.get("characteristics")
        seq = (
            [str(c[k]) for k in ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")]
            if c
            else None
        )

        # stats: primera terna de 9 números tras el header de perfil
        sm = re.search(
            r"Profile M WS BS S T W I A Ld [A-Za-z'()\u2019 ]*?((?:\d+[\s\*()]*){9})", b
        )
        got = re.findall(r"\d+", sm.group(1)) if sm else None
        stats_ok = got is not None and seq is not None and got[:9] == seq
        if not stats_ok and seq is not None:
            row["findings"].append(f"stats impresas {got} vs KB {seq}")
        elif seq is None:
            row["multi_profile"] = True  # ej. Headless Horseman (Horseman + Steed)

        # fee
        fm = re.search(r"(\d+) gold crowns to hire[^\d]+(\d+) gold crowns upkeep", b)
        row["fee_src"] = fm.groups() if fm else None

        # rating
        rm = re.search(r"rating by \+?(\d+) points", b)
        wr = p.get("warband_rating", {})
        pkg_base = (
            wr.get("base") if wr.get("kind") == "base_plus_experience" else wr.get("value")
        )
        row["rating_src"] = int(rm.group(1)) if rm else None
        row["rating_pkg"] = pkg_base
        if rm and pkg_base is not None and int(rm.group(1)) != pkg_base:
            row["findings"].append(
                f"rating impreso +{rm.group(1)} vs KB {pkg_base}"
            )

        # reglas: nombres KB presentes en el bloque
        for r in p.get("rules", []):
            key = r["name"].split(" (")[0].split(" — ")[0]
            if len(key) > 6 and key not in b:
                row["findings"].append(f"regla '{r['name']}' no aparece")

        report.append(row)

    OUT.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    for row in report:
        print(row["name"], "->", row["findings"] or "OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
