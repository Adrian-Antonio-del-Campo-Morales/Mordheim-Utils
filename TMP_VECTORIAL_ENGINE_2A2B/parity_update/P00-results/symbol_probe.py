"""Count decisive consumer symbols per stage for variant design."""
from __future__ import annotations

import collections
import csv
import json
import re
from pathlib import Path

from stage_probe import stage

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "sources/knowledge/verification/clause-contracts.csv"
RECON = Path(__file__).resolve().parent / "universe-reconciliation.csv"


def symbols(consumer: str) -> list[str]:
    try:
        parts = json.loads(consumer)
    except json.JSONDecodeError:
        parts = [consumer]
    found = []
    for part in parts:
        match = re.search(r"([A-Za-z_][\w/]*\.py|mordheim_[\w.]+)::?([A-Za-z_]\w*)", part)
        if match:
            found.append(f"{match.group(1)}::{match.group(2)}")
        else:
            found.append(part.strip())
    return found


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
        for symbol in symbols(row["consumer"]):
            per_stage[stage(row["consumer"])][symbol] += 1
    for name in sorted(per_stage):
        print(f"\n== {name} ==")
        for symbol, count in per_stage[name].most_common(30):
            print(f"{count:5} {symbol}")


if __name__ == "__main__":
    main()
