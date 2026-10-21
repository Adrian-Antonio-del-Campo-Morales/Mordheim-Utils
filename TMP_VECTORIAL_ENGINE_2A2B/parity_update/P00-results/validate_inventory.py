"""Static checks for the P00 behaviour inventory. Reads CSV only, never an engine."""
from __future__ import annotations

import collections
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = HERE.parent / "P00-deliverable.md"
INVENTORY = HERE / "behaviour-inventory.csv"
RECON = HERE / "universe-reconciliation.csv"

STATUSES = {
    "operator-base", "case-preparable", "pending-observable", "pending-input",
    "pending-rule", "check-defect", "structural", "consumer-ambiguous",
}
BEHAVIOURS = {
    "B00-routing": "B00", "B01-initial-state": "B01", "B02-hit": "B02",
    "B03-wound": "B03", "B04-armour": "B04", "B05-special-save": "B05",
    "B06-parry": "B06", "B07-injury": "B07", "B08-attack-pool": "B08",
    "B09-equipment": "B09", "B10-round-order": "B10", "B11-fear": "B11",
    "B12-stupidity": "B12", "B14-leadership": "B14", "B15-aftermath": "B15",
    "B99-unmapped": "B99",
}
errors: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


rows = list(csv.DictReader(INVENTORY.open(encoding="utf-8")))
check(len(rows) == 1914, f"esperaba 1914 filas, hay {len(rows)}")

keys = [f"{r['id']}::{r['clause_id']}" for r in rows]
duplicates = [k for k, n in collections.Counter(keys).items() if n > 1]
check(not duplicates, f"claves duplicadas: {duplicates[:5]}")

recon = {
    (r["id"], r["clause_id"]): r for r in csv.DictReader(RECON.open(encoding="utf-8"))
}
runtime = {
    f"{r['id']}::{r['clause_id']}" for r in recon.values()
    if r.get("consumer_class") in {"runtime", "mixed"}
}
recon_keys = {f"{r['id']}::{r['clause_id']}" for r in recon.values()}
check(set(keys) == runtime, "las claves del inventario no coinciden con runtime+mixed")
check(not (set(keys) - recon_keys), "hay claves fuera de la reconciliación")

variants = collections.Counter(r["variant_id"] for r in rows)
check(len(variants) == 63, f"esperaba 63 variantes, hay {len(variants)}")
check(sum(variants.values()) == 1914, f"la suma de variantes es {sum(variants.values())}")
check(
    not [r for r in rows if "other" in r["variant"].lower()],
    "queda alguna etiqueta 'other'",
)
for row in rows:
    key = f"{row['id']}::{row['clause_id']}"
    prefix = BEHAVIOURS.get(row["behaviour_id"])
    check(prefix is not None, f"{key}: comportamiento desconocido {row['behaviour_id']}")
    check(
        prefix is not None and row["variant_id"].startswith(prefix + "."),
        f"{key}: {row['variant_id']} no pertenece a {row['behaviour_id']}",
    )
    check(row["status"] in STATUSES, f"{key}: estado desconocido {row['status']}")
    check(bool(row["reference"].strip()), f"{key}: referencia vacía")
    check(bool(row["dependency"].strip()), f"{key}: dependencia vacía")
    check(bool(row["variant"].strip()), f"{key}: nombre de variante vacío")

# The delivered catalogue must reproduce the CSV counts exactly.
text = DOC.read_text(encoding="utf-8")
start, end = text.index("### 4.4 "), text.index("### 4.5 ")
catalogue = text[start:end]
doc_rows = {
    vid: int(count)
    for vid, count in re.findall(r"^\| (B\d\d\.\d+)[^|]*\| (\d+)", catalogue, re.M)
}
check(len(doc_rows) == 63, f"el catálogo documenta {len(doc_rows)} variantes")
check(
    doc_rows == dict(variants),
    "los recuentos del catálogo no coinciden con el CSV: "
    + str(sorted(set(doc_rows.items()) ^ set(variants.items()))[:5]),
)
for heading, total in re.findall(r"^#### (B\d\d)[^\n]*\((\d+) claves\)", catalogue, re.M):
    actual = sum(n for vid, n in variants.items() if vid.startswith(heading + "."))
    check(int(total) == actual, f"{heading}: cabecera {total}, CSV {actual}")

# Cross-references used by the contract must exist.
for token in ("Witness", "DuelContext.nearby", "off_hand_id", "VARIANT_KEYS"):
    check(token in text, f"el entregable no menciona {token}")
check("off_hand_id" in text, "el entregable no corrige off_weapon_id a off_hand_id")

report = [
    f"filas={len(rows)} claves_unicas={len(set(keys))} variantes={len(variants)}",
    f"runtime+mixed={len(runtime)} catalogo={len(doc_rows)}",
    "recuentos: " + ", ".join(f"{v}={n}" for v, n in sorted(variants.items())),
    "OK" if not errors else "ERRORES:",
    *errors,
]
(HERE / "inventory-validation.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
print("\n".join(report))
sys.exit(1 if errors else 0)
