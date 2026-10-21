"""Structural probe for the P00 behaviour inventory (no engine execution).

Reads the canonical registry and the P00 reconciliation snapshot, and prints
grouping candidates for the behaviour/variant inventory.  It never writes the
registry and never imports a combat engine.
"""
from __future__ import annotations

import collections
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "sources/knowledge/verification/clause-contracts.csv"
RECON = Path(__file__).resolve().parent / "universe-reconciliation.csv"


def load():
    rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8")))
    rec = {
        (r["id"], r["clause_id"]): r
        for r in csv.DictReader(RECON.open(encoding="utf-8"))
    }
    return rows, rec


def consumer_tail(value: str) -> str:
    parts = [p.strip() for p in value.split(";") if p.strip()]
    return parts[0] if parts else ""


def main() -> None:
    rows, rec = load()
    runtime = [
        r for r in rows
        if rec.get((r["id"], r["clause_id"]), {}).get("consumer_class") in {"runtime", "mixed"}
    ]
    print(f"runtime+mixed rows: {len(runtime)}")

    print("\n== effect_id (runtime+mixed) ==")
    for value, count in collections.Counter(r["effect_id"] for r in runtime).most_common():
        print(f"{count:5} {value or '(empty)'}")

    print("\n== relation ==")
    for value, count in collections.Counter(r["relation"] for r in runtime).most_common():
        print(f"{count:5} {value or '(empty)'}")

    print("\n== consumer tail ==")
    tails = collections.Counter(consumer_tail(r["consumer"]) for r in runtime)
    for value, count in tails.most_common(40):
        print(f"{count:5} {value or '(empty)'}")

    print("\n== clause_id token frequency ==")
    tokens = collections.Counter()
    for r in runtime:
        for token in re.split(r"[./:#_-]+", r["clause_id"]):
            if token and not token.isdigit():
                tokens[token] += 1
    for value, count in tokens.most_common(50):
        print(f"{count:5} {value}")

    print("\n== shared-operator detail ==")
    so = [
        r for r in rows
        if rec.get((r["id"], r["clause_id"]), {}).get("consumer_class") == "shared-operator"
    ]
    for r in so:
        print(
            f"{r['id']} | {r['clause_id']} | effect={r['effect_id'] or '-'} | "
            f"consumer={r['consumer']} | verification={r['verification'][:90]}"
        )


if __name__ == "__main__":
    main()
