"""Print effect_id counts per decisive operator stage."""
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
    per_stage: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for row in runtime:
        per_stage[stage(row["consumer"])][row["effect_id"] or "(empty)"] += 1
    for name in sorted(per_stage):
        print(f"\n== {name} ({sum(per_stage[name].values())} keys) ==")
        for effect, count in per_stage[name].most_common():
            print(f"{count:5} {effect}")


if __name__ == "__main__":
    main()
