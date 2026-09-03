"""verification.interactions: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import dataclass


INTERACTION_ALIASES = {
    "attacks.base": "fighter.attacks", "attacks.count": "attack.count",
    "strength.base": "fighter.strength", "strength.wound": "attack.strength",
    "hit.rolls": "hit.roll", "wound.rolls": "wound.roll",
    "round.first_round": "round.first", "charge": "round.charging",
    "recovery.stood-up": "state.stood_up", "priority.order": "priority.tier",
    "damage.wound": "damage.unsaved",
}


INTERACTION_CONCEPTS = frozenset({
    "armour.allowed", "armour.strength", "armour.target", "attack.assignment",
    "attack.count", "attack.fire", "attack.penetration", "attack.strength",
    "build.offhand", "build.profile", "build.variant", "construction.skill-access",
    "construction.skill-lists", "damage.unsaved", "defender.poison_immunity",
    "defender.strength", "defender.toughness", "defender.weapon_skill",
    "fighter.attacks", "fighter.initiative", "fighter.strength", "fighter.weapon_skill",
    "fighter.wounds", "hit.reroll", "hit.roll", "hit.success", "hit.target",
    "injury.condition", "injury.origin", "injury.roll", "injury.total",
    "priority.tier", "priority.weapon", "round.charged", "round.charging", "round.first",
    "skill.strongman", "state.critical_available", "state.frenzy", "state.parries", "state.lucky_charm",
    "state.stood_up", "state.wounds", "weapon.kind", "wound.roll", "wound.success", "wound.target",
})

RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
REQUIREMENT_ORDER = {"not_applicable": 0, "optional": 1, "recommended": 2, "required": 3}

CRITICAL_CONCEPTS = frozenset({
    "damage.unsaved", "state.critical_available", "state.frenzy", "state.lucky_charm",
    "state.parries", "state.stood_up", "state.wounds", "injury.condition", "injury.origin",
    "injury.roll", "injury.total", "attack.fire",
})
HIGH_CONCEPTS = frozenset({
    "armour.allowed", "armour.target", "attack.assignment", "attack.count",
    "hit.reroll", "priority.tier", "priority.weapon", "wound.success",
})


@dataclass(frozen=True)
class InteractionAssessment:
    bindings: tuple[str, str]
    risk_level: str
    verification_requirement: str
    status: str
    risk_reasons: tuple[str, ...]
    evidence: tuple[str, ...] = ()


def assess_interaction(left: str, right: str, contracts: dict[str, dict], *,
                       tested: bool = False, override: dict | None = None) -> InteractionAssessment:
    """Classify a pair; a documented override prevails over the heuristic."""
    a, b = contracts[left], contracts[right]
    concepts = ((set(a["writes"]) & (set(b["reads"]) | set(b["writes"])))
                | (set(b["writes"]) & set(a["reads"])))
    if concepts & CRITICAL_CONCEPTS:
        risk = "critical"
    elif concepts & HIGH_CONCEPTS:
        risk = "high"
    elif concepts:
        risk = "medium"
    else:
        risk = "low"
    requirement = "required" if risk in {"critical", "high"} else "recommended" if risk == "medium" else "optional"
    status = "tested" if tested else "pending"
    reasons = tuple(sorted(f"shared_concept:{concept}" for concept in concepts)) or ("no_shared_runtime_concept",)
    evidence: tuple[str, ...] = ("semantic_interaction_fixture",) if tested else ()
    if override:
        risk = override.get("risk_level", risk)
        requirement = override.get("verification_requirement", requirement)
        status = override.get("status", status)
        reasons = tuple(override.get("risk_reasons") or reasons)
        evidence = tuple(override.get("evidence") or ())
    if risk not in RISK_ORDER:
        raise ValueError(f"unknown interaction risk level: {risk}")
    if requirement not in REQUIREMENT_ORDER:
        raise ValueError(f"unknown interaction verification requirement: {requirement}")
    if status not in {"tested", "covered_by_composition", "independent", "illegal", "pending", "needs_ruling"}:
        raise ValueError(f"unknown interaction status: {status}")
    return InteractionAssessment(tuple(sorted((left, right))), risk, requirement, status, reasons, evidence)


def normalize_interaction_contract(contract: dict) -> dict:
    normalized = {}
    for side in ("reads", "writes"):
        values = contract.get(side)
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError("interaction contract requires explicit lists of concepts")
        concepts = {INTERACTION_ALIASES.get(value, value) for value in values}
        if concepts - INTERACTION_CONCEPTS:
            raise ValueError(f"unknown interaction concepts: {sorted(concepts - INTERACTION_CONCEPTS)}")
        normalized[side] = sorted(concepts)
    return normalized
