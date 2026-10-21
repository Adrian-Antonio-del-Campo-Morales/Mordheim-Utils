"""Report decisive operator stages and residual ambiguous consumers."""
from __future__ import annotations

import collections
import csv
from pathlib import Path

from stage_probe import stage

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "sources/knowledge/verification/clause-contracts.csv"
RECON = Path(__file__).resolve().parent / "universe-reconciliation.csv"


def main() -> None:
    rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8")))
    rec = {
        (r["id"], r["clause_id"]): r
        for r in csv.DictReader(RECON.open(encoding="utf-8"))
    }
    runtime = [
        r for r in rows
        if rec.get((r["id"], r["clause_id"]), {}).get("consumer_class") in {"runtime", "mixed"}
    ]
    counts = collections.Counter(stage(r["consumer"]) for r in runtime)
    print("stage counts")
    for name, count in counts.most_common():
        print(f"{count:5} {name}")
    print("\nunmapped")
    residual = collections.Counter(
        r["consumer"] for r in runtime if stage(r["consumer"]) == "B99-unmapped"
    )
    for value, count in residual.most_common():
        print(f"{count:5} {value}")
    print("\nfamily x stage")
    table = collections.Counter(
        (rec[(r["id"], r["clause_id"])]["behaviour_family"], stage(r["consumer"]))
        for r in runtime
    )
    for (family, name), count in sorted(table.items()):
        print(f"{count:5} {name:24} {family}")


if __name__ == "__main__":
    main()
