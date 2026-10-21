"""Review the 98 ``shared-operator`` keys against the existing exact checks.

No engine is imported.  The script groups the keys by the operator their clause
actually exercises, marks the narrow subset that an existing exact check
demonstrates, and leaves the rest as pending differential obligations.
"""
from __future__ import annotations

import collections
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "sources/knowledge/verification/clause-contracts.csv"
RECON = Path(__file__).resolve().parent / "universe-reconciliation.csv"
OUT = Path(__file__).resolve().parent / "shared-operator-review.tsv"


def category(row: dict[str, str]) -> str:
    effect = row["effect_id"] or ""
    key = f"{row['id']}::{row['clause_id']}"
    if "natural-armour" in effect:
        return "natural-armour"
    if effect in {"skill.lightning-reflexes", "weapon.trident",
                  "mechanic.strike-first-vs-skinks-always",
                  "mechanic.strike-first-vs-skinks-first-round",
                  "skill.always-strikes-first", "dance.woven-mist",
                  "weapon.pike", "weapon.spear", "weapon.quarter-staff",
                  "material.ithilmar", "skill.strongman",
                  "mechanic.sabretusk-charge"}:
        return "priority"
    if effect in {"skill.extra-attack", "skill.red-fury",
                  "skill.art-of-silent-death", "mechanic.maddened-with-pain",
                  "trait.first-round-charge-attack-bonus",
                  "trait.charge-attack-bonus", "mechanic.frantic",
                  "mechanic.death-blow", "mechanic.black-hunger",
                  "skill.web-of-steel", "skill.inspiring-sermon",
                  "skill.unarmed-fighting", "weapon.chain-sticks",
                  "weapon.knuckledusters", "weapon.natural-attacks",
                  "weapon.squig-prodder", "proposed.core.combat-two-weapons",
                  "weapon.veskit-claws"} or effect.startswith("profile-rule."):
        return "attack-count"
    if effect in {"defence.buckler"}:
        return "buckler"
    if effect == "weapon.starsword":
        return "special-save"
    if effect == "proposed.core.combat-critical-hits":
        return "critical"
    if effect in {"profile.equipment-restrictions", "profile.natural-attacks"}:
        return "equipment-restrictions"
    if effect == "skill.savage-fury":
        return "other"
    if "stand-up" in key:
        return "stand-up"
    if effect == "mechanic.armour-save-floor":
        return "armour-floor"
    return "other"


def exact_evidence(row: dict[str, str], cat: str) -> str:
    effect = row["effect_id"] or ""
    if cat == "priority" and effect in {"skill.strongman", "material.ithilmar"}:
        return "priority: strongman double-handed / ithilmar off-hand variant"
    if cat == "attack-count" and effect == "proposed.core.combat-two-weapons":
        return "attack-pools: off-hand dagger variant"
    return ""


def main() -> None:
    rows = list(csv.DictReader(REGISTRY.open(encoding="utf-8")))
    rec = {
        (r["id"], r["clause_id"]): r
        for r in csv.DictReader(RECON.open(encoding="utf-8"))
    }
    shared = [
        r for r in rows
        if rec.get((r["id"], r["clause_id"]), {}).get("consumer_class") == "shared-operator"
    ]
    counts = collections.Counter()
    evidence = collections.Counter()
    lines = ["category\texact_evidence\tkey\teffect"]
    for row in shared:
        cat = category(row)
        proof = exact_evidence(row, cat)
        counts[cat] += 1
        if proof:
            evidence[cat] += 1
        lines.append(
            f"{cat}\t{proof or 'pending'}\t{row['id']}::{row['clause_id']}\t"
            f"{row['effect_id'] or '-'}"
        )
    print(f"shared-operator rows={len(shared)}")
    for cat, count in counts.most_common():
        print(f"{count:4} {cat:24} exact={evidence[cat]}")
    print(f"exact evidence total={sum(evidence.values())}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
