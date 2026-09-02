"""Executable contract between the scalar oracle and the vectorized runtime."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
import math
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable
from fractions import Fraction

import numpy as np

from mordheim_combat import phases
from mordheim_combat import vectorized
from mordheim_combat.vector_dice import KeyedVectorDice
from mordheim_combat.vector_dice import VectorRollRequest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelRequest
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
from mordheim_core.effects import merge_effects
from mordheim_core.dice import KeyedDice
from mordheim_core.dice import RollRequest
from mordheim_combat_lab.verification.consumers import MODULAR_COMPLEX_SCENARIOS
from mordheim_combat_lab.verification.consumers import MODULAR_FIELD_CONSUMERS
from mordheim_combat_lab.verification.consumers import MODULAR_TAG_CONSUMERS
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_combat_lab.verification.dice import StrictDecisions
from mordheim_combat_lab.verification.scenarios import _build as build_semantic_fighter
from mordheim_combat_lab.verification.scenarios import _lookup
from mordheim_combat_lab.verification.scenarios import _plain
from mordheim_combat_lab.verification.scenarios import check_case
from mordheim_combat_lab.verification.scenarios import execute_case
from mordheim_combat_lab.verification.specifications import load_fixtures
from mordheim_knowledge.loader import knowledge_root
from mordheim_knowledge.loader import load_runtime_scope


ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True, slots=True)
class ParityObligation:
    kind: str
    id: str
    consumer: str
    evidence: str
    verified: bool


@dataclass(frozen=True, slots=True)
class ParityReport:
    complete: bool
    obligations: tuple[ParityObligation, ...]
    verified: tuple[str, ...]
    pending: tuple[str, ...]
    divergences: tuple[str, ...]
    exact_checks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class StatisticalParityResult:
    scenario: str
    simulations: int
    modular_rates: tuple[float, float, float]
    vectorized_rates: tuple[float, float, float]
    tolerances: tuple[float, float, float]
    passed: bool


@dataclass(frozen=True, slots=True)
class SpecificationParityCase:
    specification: str
    case: str
    operation: str
    status: str
    adapter: str
    detail: str = ""


@dataclass(frozen=True, slots=True)
class SpecificationParityReport:
    complete: bool
    cases: tuple[SpecificationParityCase, ...]
    passed: tuple[str, ...]
    pending: tuple[str, ...]
    divergences: tuple[str, ...]
    out_of_scope: tuple[str, ...]


CERTIFICATION_SIMULATIONS = 100_000


def parity_report_payload(
    report: ParityReport,
    statistical: Iterable[StatisticalParityResult] = (),
    specifications: SpecificationParityReport | None = None,
) -> dict[str, object]:
    """Return a serializable, self-describing parity certificate."""
    samples = tuple(statistical)
    statistical_passed = all(item.passed for item in samples)
    certification = bool(samples) and all(
        item.simulations >= CERTIFICATION_SIMULATIONS for item in samples
    )
    return {
        "schema": "mordheim-combat-parity/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "oracle": "combat.modular (read-only)",
        "candidate": "combat.vectorized",
        "complete": report.complete and statistical_passed and (
            specifications is None or specifications.complete
        ),
        "certification_sample_complete": certification,
        "certification_minimum_simulations_per_engine": CERTIFICATION_SIMULATIONS,
        "deterministic": {
            "passed": not report.pending and not report.divergences,
            "exact_checks": report.exact_checks,
            "verified": report.verified,
            "pending": report.pending,
            "divergences": report.divergences,
            "obligations": tuple({
                "kind": item.kind, "id": item.id, "consumer": item.consumer,
                "evidence": item.evidence, "verified": item.verified,
            } for item in report.obligations),
        },
        "statistical": tuple({
            "scenario": item.scenario,
            "simulations_per_engine": item.simulations,
            "modular_rates": item.modular_rates,
            "vectorized_rates": item.vectorized_rates,
            "tolerances": item.tolerances,
            "passed": item.passed,
        } for item in samples),
        "specifications": None if specifications is None else {
            "complete": specifications.complete,
            "passed": specifications.passed,
            "pending": specifications.pending,
            "divergences": specifications.divergences,
            "out_of_scope": specifications.out_of_scope,
            "cases": tuple({
                "specification": item.specification,
                "case": item.case,
                "operation": item.operation,
                "status": item.status,
                "adapter": item.adapter,
                "detail": item.detail,
            } for item in specifications.cases),
        },
    }


def parity_report_markdown(payload: dict[str, object]) -> str:
    deterministic = payload["deterministic"]
    assert isinstance(deterministic, dict)
    rows = payload["statistical"]
    assert isinstance(rows, tuple)
    lines = [
        "# Vectorized engine parity report",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Oracle: `{payload['oracle']}`",
        f"- Candidate: `{payload['candidate']}`",
        f"- Overall pass: `{payload['complete']}`",
        f"- Certification-sized sample: `{payload['certification_sample_complete']}`",
        f"- Deterministic checks: `{len(deterministic['exact_checks'])}`",
        f"- Verified obligations: `{len(deterministic['verified'])}`",
        f"- Pending obligations: `{len(deterministic['pending'])}`",
        f"- Divergences: `{len(deterministic['divergences'])}`",
        "",
        "## Deterministic checks",
        "",
        *[f"- `{name}`" for name in deterministic["exact_checks"]],
    ]
    specifications = payload.get("specifications")
    if isinstance(specifications, dict):
        lines.extend((
            "", "## Semantic specification parity", "",
            f"- PASS: `{len(specifications['passed'])}`",
            f"- PENDING_ADAPTER: `{len(specifications['pending'])}`",
            f"- DIVERGENCE: `{len(specifications['divergences'])}`",
            f"- OUT_OF_SCOPE: `{len(specifications['out_of_scope'])}`",
        ))
    if rows:
        lines.extend((
            "", "## Statistical comparisons", "",
            "| Scenario | Duels/engine | Modular W/L/U | Vectorized W/L/U | Pass |",
            "|---|---:|---|---|---|",
        ))
        for row in rows:
            modular = "/".join(f"{100 * value:.3f}%" for value in row["modular_rates"])
            vector = "/".join(f"{100 * value:.3f}%" for value in row["vectorized_rates"])
            lines.append(
                f"| {row['scenario']} | {row['simulations_per_engine']:,} | "
                f"{modular} | {vector} | {row['passed']} |"
            )
    return "\n".join(lines) + "\n"


CONSTRUCTION_SPEC_OPERATIONS = frozenset({
    "compile", "grant", "selectable_grant", "general_skill_access",
    "special_skill_access", "special_rule_access", "trait_presence",
    "construction_tag_presence", "equipment_choices", "selection_choices",
    "missile_capacity",
})


def _spec_case_id(specification: str, case: dict) -> str:
    return f"{specification}/{case['id']}"


def _case_is_out_of_scope(spec: dict, excluded: set[str]) -> bool:
    return any(
        str(source.get("target", "")).removeprefix("mechanic/") in excluded
        for source in spec.get("sources", ())
        if str(source.get("target", "")).startswith("mechanic/")
    )


def _vector_attack_count(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    fighter = build_semantic_fighter(case.get("attacker", {}), root)
    context = case.get("context", {})
    flag = lambda name, default=False: np.asarray([context.get(name, default)], dtype=bool)
    optional_flag = lambda name: flag(name) if name in context else None
    optional_int = lambda name: (
        np.asarray([context[name]], dtype=np.int16) if name in context else None
    )
    actual = int(vectorized.attack_count(
        fighter,
        flag("charging"),
        first_round=bool(context.get("first_round", False)),
        frenzy=optional_flag("frenzy"),
        charged=optional_flag("charged"),
        attack_penalty=optional_int("attack_penalty"),
        wounded=optional_flag("wounded"),
        base_attacks=optional_int("base_attacks"),
    )[0])
    expected = int(modular["result"]["attacks"])
    if actual != expected:
        raise AssertionError(f"vectorized attacks={actual}, modular attacks={expected}")


def _vector_priority(case: dict, root: Path) -> None:
    context = case.get("context", {})
    if int(context.get("initiative_floor", 1)) != 1:
        raise NotImplementedError("vectorized priority adapter lacks initiative_floor")
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    fighter = build_semantic_fighter(case.get("attacker", {}), root)
    opponent = build_semantic_fighter(case.get("defender", {}), root)
    state = vectorized._new_state(fighter, 1, np.random.default_rng(0))
    state.initiative_penalty[:] = int(context.get("initiative_penalty", 0))
    state.crimson_initiative[:] = int(context.get("initiative_bonus", 0))
    actual_priority = int(vectorized.priority(
        fighter, opponent, bool(context.get("first_round", False)),
        np.asarray([context.get("charging", False)]),
        np.asarray([context.get("charged", False)]),
        np.asarray([context.get("stood_up", False)]),
    )[0])
    actual_initiative = int(vectorized.effective_initiative(fighter, state)[0])
    expected = modular["result"]
    if (actual_priority, actual_initiative) != (expected["priority"], expected["initiative"]):
        raise AssertionError(
            "vectorized priority/initiative="
            f"{(actual_priority, actual_initiative)}, modular="
            f"{(expected['priority'], expected['initiative'])}"
        )


class _RollVectorRng:
    """Minimal NumPy RNG facade fed by a semantic case's declared rolls."""
    def __init__(self, case: dict):
        self.values = [int(item["value"]) for item in case.get("rolls", ())]

    def integers(self, low, high=None, size=None, dtype=None):
        high = high if high is not None else low
        low = low if high is not None else 0
        count = int(np.prod(size)) if isinstance(size, tuple) else (1 if size is None else int(size))
        values = [self.values.pop(0) if self.values else high - 1 for _ in range(count)]
        result = np.asarray(values, dtype=dtype or np.int64)
        if size is None:
            return result[0]
        return result.reshape(size if isinstance(size, tuple) else (size,))

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def _vector_strength(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    weapon = attacker.off_hand if case["operation"] == "off_hand_strength" else attacker.main_weapon
    if weapon is None:
        raise AssertionError("off-hand strength case has no off-hand weapon")
    rng = _RollVectorRng(case)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    context = case.get("context", {})
    prepared = vectorized._prepare_weapon_attack(
        attacker, defender, weapon, np.asarray([0], dtype=np.int64),
        np.asarray([context.get("charging", False)]), attacker_state, defender_state,
        rng, bool(context.get("first_round", False)),
    )
    if prepared is None:
        raise AssertionError("vectorized attack preparation returned no attack")
    actual = {"wound": int(prepared.strength[0]), "armour": int(prepared.armour_strength[0])}
    expected = modular["result"]
    if actual != expected:
        raise AssertionError(f"vectorized strength={actual}, modular={expected}")


def _injury_context_from_plain(values: dict) -> phases.InjuryContext:
    values = dict(values)
    initial = values.get("initial_condition", "STANDING")
    if isinstance(initial, str):
        values["initial_condition"] = phases.Condition[initial]
    return phases.InjuryContext(**values)


def _vector_injury(case: dict, root: Path) -> None:
    if "distribution" not in case:
        modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
        context = _injury_context_from_plain(modular["context"])
        total = int(modular["result"]["total"])
        actual = phases.Condition(int(vectorized.injury_conditions(np.asarray([total]), context)[0])).name
        expected = modular["result"]["condition"]
        if actual != expected:
            raise AssertionError(f"vectorized injury={actual}, modular={expected}")
        return
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    from mordheim_combat.modular import contexts as modular_contexts
    weapon = modular_contexts.weapon_against_opponent(attacker, defender, attacker.main_weapon)
    effect = modular_contexts._combined_effect(attacker, weapon)
    context = modular_contexts._injury_context(defender, effect, "test")
    totals = np.arange(1, 7, dtype=np.int16) + context.modifier + context.critical_bonus
    conditions = vectorized.injury_conditions(totals, context)
    observed: dict[str, Fraction] = {}
    for condition in conditions:
        name = phases.Condition(int(condition)).name
        observed[name] = observed.get(name, Fraction()) + Fraction(1, 6)
    expected = {
        str(name): Fraction(str(probability))
        for name, probability in case["distribution"]["expected"].items()
    }
    if observed != expected:
        raise AssertionError(f"vectorized injury distribution={observed}, expected={expected}")


def _prepare_vector_case(case: dict, root: Path, rng) -> vectorized.PreparedAttack:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    context = case.get("context", {})
    prepared = vectorized._prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, np.asarray([0], dtype=np.int64),
        np.asarray([context.get("charging", False)]), attacker_state, defender_state,
        rng, bool(context.get("first_round", False)),
    )
    if prepared is None:
        raise AssertionError("vectorized attack preparation returned no attack")
    return prepared


def _vector_hit(case: dict, root: Path) -> None:
    if "distribution" not in case:
        modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
        prepared = _prepare_vector_case(case, root, _RollVectorRng(case))
        actual = {
            "target": int(prepared.hit_target[0]),
            "roll": int(prepared.rolls[0]),
            "success": bool(prepared.hit_rows.size),
            "rerolled": bool(prepared.rerolled[0]),
        }
        expected = modular["result"]
        if actual != expected:
            raise AssertionError(f"vectorized hit={actual}, modular={expected}")
        return
    successes = 0
    for first in range(1, 7):
        for second in range(1, 7):
            scripted = {**case, "rolls": ({"value": first}, {"value": second})}
            prepared = _prepare_vector_case(scripted, root, _RollVectorRng(scripted))
            successes += int(bool(prepared.hit_rows.size))
    observed = {"true": Fraction(successes, 36), "false": Fraction(36 - successes, 36)}
    observed = {key: value for key, value in observed.items() if value}
    expected = {
        str(key): Fraction(str(value))
        for key, value in case["distribution"]["expected"].items()
    }
    if observed != expected:
        raise AssertionError(f"vectorized hit distribution={observed}, expected={expected}")


def _vector_armour(case: dict, root: Path) -> None:
    defender = build_semantic_fighter(case.get("defender", {}), root)
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    context = case.get("context", {})
    weapon = (
        attacker.off_hand
        if case["operation"] == "off_hand_armour" else attacker.main_weapon
    )
    if weapon is None:
        raise AssertionError("off-hand armour case has no off-hand weapon")
    rng = _RollVectorRng({**case, "rolls": ()})
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    prepared = vectorized._prepare_weapon_attack(
        attacker, defender, weapon, np.asarray([0], dtype=np.int64),
        np.asarray([context.get("charging", False)]), attacker_state, defender_state,
        rng, bool(context.get("first_round", False)),
    )
    if prepared is None:
        raise AssertionError("vectorized attack preparation returned no attack")
    magical = phases.has_tag(prepared.effect, "attack.magical")
    armour_strength = prepared.armour_strength[:1].copy()
    if phases.has_tag(prepared.effect, "skill.monster-slayer-effective-strength-armour"):
        armour_strength = np.maximum(armour_strength, defender_state.toughness[:1])
    target = int(vectorized.armour_targets(
        defender, armour_strength, prepared.effect, magical,
    )[0])
    if "distribution" in case:
        successes = sum(roll >= max(2, target) for roll in range(1, 7)) if target <= 6 else 0
        observed = {"true": Fraction(successes, 6), "false": Fraction(6 - successes, 6)}
        observed = {key: value for key, value in observed.items() if value}
        expected = {
            str(key): Fraction(str(value))
            for key, value in case["distribution"]["expected"].items()
        }
        if observed != expected:
            raise AssertionError(f"vectorized armour distribution={observed}, expected={expected}")
        return
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    expected = modular["result"]
    roll = expected["roll"]
    actual = {
        "target": target,
        "eligible": target <= 6,
        "roll": roll,
        "saved": bool(roll is not None and roll >= max(2, target)),
    }
    if actual != expected:
        raise AssertionError(f"vectorized armour={actual}, modular={expected}")


def _special_save_outcome(ward: int, regeneration: int, rolls: list[int]) -> dict[str, object]:
    index = 0
    ward_roll = regeneration_roll = None
    if ward <= 6:
        ward_roll = rolls[index]
        index += 1
        if ward_roll >= ward:
            return {"saved": True, "source": "ward", "ward_roll": ward_roll,
                    "regeneration_roll": None}
    if regeneration <= 6:
        regeneration_roll = rolls[index]
        return {"saved": regeneration_roll >= regeneration,
                "source": "regeneration" if regeneration_roll >= regeneration else None,
                "ward_roll": ward_roll, "regeneration_roll": regeneration_roll}
    return {"saved": False, "source": None, "ward_roll": ward_roll,
            "regeneration_roll": None}


def _vector_special_save(case: dict, root: Path) -> None:
    modular = None
    defender = build_semantic_fighter(case.get("defender", {}), root)
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    incoming = merge_effects(attacker.main_weapon, attacker.global_effects)
    if case.get("context", {}).get("incoming_tags"):
        incoming = replace(incoming, tags=tuple(case["context"]["incoming_tags"]))
    ward, regeneration = vectorized.special_save_targets(defender, incoming)
    if "distribution" in case:
        saved = 0
        for first in range(1, 7):
            for second in range(1, 7):
                saved += int(_special_save_outcome(ward, regeneration, [first, second])["saved"])
        observed = {"true": Fraction(saved, 36), "false": Fraction(36 - saved, 36)}
        observed = {key: value for key, value in observed.items() if value}
        expected = {str(key): Fraction(str(value)) for key, value in case["distribution"]["expected"].items()}
        if observed != expected:
            raise AssertionError(f"vectorized special save distribution={observed}, expected={expected}")
        return
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    rolls = [int(item["value"]) for item in case.get("rolls", ())]
    actual = _special_save_outcome(ward, regeneration, rolls)
    if actual != modular["result"]:
        raise AssertionError(f"vectorized special save={actual}, modular={modular['result']}")


def _vector_wound(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ()))) if "distribution" not in case else None
    if modular is not None:
        context = phases.WoundContext(**modular["context"])
    else:
        from mordheim_combat.modular import contexts as modular_contexts
        from mordheim_combat.modular.state import initialize_fighter
        attacker = build_semantic_fighter(case.get("attacker", {}), root)
        defender = build_semantic_fighter(case.get("defender", {}), root)
        dice = _RollVectorRng({**case, "rolls": ()})
        a, d = initialize_fighter(attacker, dice, "a"), initialize_fighter(defender, dice, "d")
        weapon = modular_contexts.weapon_against_opponent(attacker, defender, attacker.main_weapon)
        effect = modular_contexts._combined_effect(attacker, weapon)
        context_values = case.get("context", {})
        context = modular_contexts.prepare_wound_context(
            attacker, defender, a, d, weapon, effect,
            first_round=bool(context_values.get("first_round", False)),
            charging=bool(context_values.get("charging", False)),
            hit_roll=int(context_values.get("hit_roll", 4)), key="wound",
        )
    if "distribution" in case:
        observable = case["distribution"]["observable"]
        counts: dict[str, Fraction] = {}
        for first in range(1, 7):
            for second in range(1, 7):
                _, _, success, critical, rerolled = vectorized.wound_outcomes(
                    context, np.asarray([first]), np.asarray([second]),
                )
                value = bool(success[0]) if observable == "result.success" else bool(critical[0])
                key = "true" if value else "false"
                counts[key] = counts.get(key, Fraction()) + Fraction(1, 36)
        expected = {str(key): Fraction(str(value)) for key, value in case["distribution"]["expected"].items()}
        if counts != expected:
            raise AssertionError(f"vectorized wound distribution={counts}, expected={expected}")
        return
    declared = [int(item["value"]) for item in case.get("rolls", ())]
    first = declared[0] if declared else 6
    second = declared[1:] or None
    targets, rolls, success, critical, rerolled = vectorized.wound_outcomes(
        context, np.asarray([first]), np.asarray(second) if second else None,
    )
    actual = {"target": int(targets[0]), "roll": int(rolls[0]),
              "success": bool(success[0]), "critical": bool(critical[0]),
              "rerolled": bool(rerolled[0])}
    if actual != modular["result"]:
        raise AssertionError(f"vectorized wound={actual}, modular={modular['result']}")


def _vector_characteristic_test(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ()))) if "distribution" not in case else None
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    context = case.get("context", {})
    target = int(context["value"])
    six_fails = bool(context.get("six_fails", False))
    reroll = phases.has_tag(attacker.global_effects, "skill.blessed-sight")
    if "distribution" in case:
        passed_count = 0
        denominator = 36 if reroll else 6
        for first in range(1, 7):
            seconds = range(1, 7) if reroll else (6,)
            for second in seconds:
                _, passed = vectorized.characteristic_test_outcomes(
                    np.asarray([target]), np.asarray([first]), six_fails=six_fails,
                    rerolls=np.asarray([second]) if reroll else None,
                )
                passed_count += int(passed[0])
        observed = {"true": Fraction(passed_count, denominator),
                    "false": Fraction(denominator - passed_count, denominator)}
        observed = {key: value for key, value in observed.items() if value}
        expected = {str(key): Fraction(str(value)) for key, value in case["distribution"]["expected"].items()}
        if observed != expected:
            raise AssertionError(f"vectorized characteristic distribution={observed}, expected={expected}")
        return
    declared = [int(item["value"]) for item in case.get("rolls", ())]
    first = declared[0]
    _, passed = vectorized.characteristic_test_outcomes(
        np.asarray([target]), np.asarray([first]), six_fails=six_fails,
        rerolls=np.asarray(declared[1:]) if reroll and len(declared) > 1 else None,
    )
    actual = {"passed": bool(passed[0])}
    if actual != modular["result"]:
        raise AssertionError(f"vectorized characteristic={actual}, modular={modular['result']}")


def _vector_parry(case: dict, root: Path) -> None:
    if "distribution" not in case:
        modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
        context = (
            phases.ParryContext(**modular["context"])
            if modular["context"] is not None
            else phases.ParryContext(4, 0, 1, available=False)
        )
        declared = [int(item["value"]) for item in case.get("rolls", ())]
        initial = declared[0] if declared else 0
        rolls, attempted, blocked, rerolled = vectorized.parry_outcomes(
            context, np.asarray([initial]), np.asarray(declared[1:]) if len(declared) > 1 else None,
        )
        actual = {"attempted": bool(attempted[0]), "blocked": bool(blocked[0]),
                  "roll": int(rolls[0]) if attempted[0] else None,
                  "rerolled": bool(rerolled[0])}
        if actual != modular["result"]:
            raise AssertionError(f"vectorized parry={actual}, modular={modular['result']}")
        return
    from mordheim_combat.modular import contexts as modular_contexts
    from mordheim_combat.modular.state import initialize_fighter
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    a = initialize_fighter(attacker, StrictDice([]), "a")
    d = initialize_fighter(defender, StrictDice([]), "d")
    values = case.get("context", {})
    weapon = modular_contexts.weapon_against_opponent(attacker, defender, attacker.main_weapon)
    effect = modular_contexts._combined_effect(attacker, weapon)
    strength, _ = modular_contexts._attack_strength(attacker, defender, a, weapon, effect,
                                                     values.get("first_round", False), values.get("charging", False))
    context = modular_contexts._parry_context(defender, d, effect, strength,
                                               values.get("hit_roll", 4), "test")
    context = context or phases.ParryContext(4, strength, d.strength, available=False)
    blocked_count = 0
    denominator = 36 if context.reroll else 6
    for first in range(1, 7):
        seconds = range(1, 7) if context.reroll else (6,)
        for second in seconds:
            _, _, blocked, _ = vectorized.parry_outcomes(
                context, np.asarray([first]), np.asarray([second]) if context.reroll else None,
            )
            blocked_count += int(blocked[0])
    observed = {"true": Fraction(blocked_count, denominator),
                "false": Fraction(denominator - blocked_count, denominator)}
    observed = {key: value for key, value in observed.items() if value}
    expected = {str(key): Fraction(str(value)) for key, value in case["distribution"]["expected"].items()}
    if observed != expected:
        raise AssertionError(f"vectorized parry distribution={observed}, expected={expected}")


def _vector_stun_reaction(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    context = modular["context"]
    roll = modular["result"]["roll"] or 0
    conditions, attempted, converted, thresholds = vectorized.stun_reaction_outcomes(
        np.asarray([int(phases.Condition[context["condition"]])]),
        thick_skull=bool(context["thick_skull"]), helmet_save=int(context["helmet_save"]),
        rolls=np.asarray([roll]),
    )
    actual = {"condition": phases.Condition(int(conditions[0])).name,
              "attempted": bool(attempted[0]), "converted": bool(converted[0]),
              "threshold": int(thresholds[0]) if attempted[0] else None,
              "roll": int(roll) if attempted[0] else None}
    if actual != modular["result"]:
        raise AssertionError(f"vectorized stun reaction={actual}, modular={modular['result']}")


def _vector_acting_order(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ()))) if "distribution" not in case else None
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    def outcome(roll: int) -> bool:
        left_context, right_context = case.get("context", {}), case.get("opponent_context", {})
        left = (int(vectorized.priority(attacker, defender, bool(left_context.get("first_round", False)),
                    np.asarray([left_context.get("charging", False)]), np.asarray([left_context.get("charged", False)]),
                    np.asarray([left_context.get("stood_up", False)]))[0]),
                phases.resolve_priority(phases.PriorityContext(attacker, defender, **left_context)).initiative)
        right = (int(vectorized.priority(defender, attacker, bool(right_context.get("first_round", False)),
                    np.asarray([right_context.get("charging", False)]), np.asarray([right_context.get("charged", False)]),
                    np.asarray([right_context.get("stood_up", False)]))[0]),
                 phases.resolve_priority(phases.PriorityContext(defender, attacker, **right_context)).initiative)
        return roll >= 4 if left == right else left > right
    if "distribution" in case:
        count = sum(outcome(roll) for roll in range(1, 7))
        observed = {"true": Fraction(count, 6), "false": Fraction(6-count, 6)}
        observed = {key: value for key, value in observed.items() if value}
        expected = {str(key): Fraction(str(value)) for key, value in case["distribution"]["expected"].items()}
        if observed != expected:
            raise AssertionError(f"vectorized acting order distribution={observed}, expected={expected}")
        return
    declared = [int(item["value"]) for item in case.get("rolls", ())]
    actual = {"first_acts": outcome(declared[0] if declared else 6)}
    if actual != modular["result"]:
        raise AssertionError(f"vectorized acting order={actual}, modular={modular['result']}")


def _vector_weapon_attack_count(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    context = case.get("context", {})
    charging = np.asarray([context.get("charging", False)])
    charged = np.asarray([context.get("charged", False)])
    count = vectorized.attack_count(
        attacker, charging, first_round=bool(context.get("first_round", False)),
        frenzy=np.asarray([context["frenzy"]]) if "frenzy" in context else None,
        wounded=np.asarray([context["wounded"]]) if "wounded" in context else None,
        attack_penalty=np.asarray([context["attack_penalty"]]) if "attack_penalty" in context else None,
        base_attacks=np.asarray([context["base_attacks"]]) if "base_attacks" in context else None,
    )
    actual = int(vectorized.round_weapon_attack_count(
        attacker, defender, count, first_round=bool(context.get("first_round", False)),
        charging=charging, charged=charged,
    )[0])
    if actual != modular["result"]["attacks"]:
        raise AssertionError(f"vectorized weapon attack count={actual}, modular={modular['result']['attacks']}")


def _vector_spawn_attacks(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    fighter = build_semantic_fighter(case.get("attacker", {}), root)
    ordinary = int(case.get("context", {}).get("ordinary_count", 1))
    spawn_roll = next((int(item["value"]) for item in case.get("rolls", ())
                       if item.get("key") == "spawn-attacks"), 0)
    actual = spawn_roll + 1 if phases.has_tag(fighter.global_effects, "mechanic.spawn-special-attacks") else ordinary
    if actual != modular["result"]["attacks"]:
        raise AssertionError(f"vectorized spawn attacks={actual}, modular={modular['result']['attacks']}")


def _vector_bear_hug(case: dict, root: Path) -> None:
    if "distribution" in case:
        attacker = build_semantic_fighter(case.get("attacker", {}), root)
        defender = build_semantic_fighter(case.get("defender", {}), root)
        successful_hits = int(case.get("context", {}).get("successful_hits", 2))
        wounded = sum(
            phases.bear_hug_wins(a, attacker.characteristics.strength,
                                  d, defender.characteristics.strength)
            for a in range(1, 7) for d in range(1, 7)
        ) if successful_hits >= 2 else 0
        observed = {"true": Fraction(wounded, 36), "false": Fraction(36-wounded, 36)}
        observed = {key: value for key, value in observed.items() if value}
        expected = {str(key): Fraction(str(value)) for key, value in case["distribution"]["expected"].items()}
        if observed != expected:
            raise AssertionError(f"vectorized bear hug distribution={observed}, expected={expected}")
        return
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    context = modular["context"]
    declared = [int(item["value"]) for item in case.get("rolls", ())]
    available = context["successful_hits"] >= 2
    chosen = bool(case.get("decisions", ())[0].get("value", False)) if available else False
    attacker_roll = declared[0] if chosen else None
    defender_roll = declared[1] if chosen else None
    wounded = bool(chosen and phases.bear_hug_wins(
        attacker_roll, context["attacker_strength"], defender_roll, context["defender_strength"]
    ))
    actual = {"available": available, "chosen": chosen, "wounded": wounded,
              "armour_allowed": not chosen, "attacker_roll": attacker_roll,
              "defender_roll": defender_roll}
    if actual != modular["result"]:
        raise AssertionError(f"vectorized bear hug={actual}, modular={modular['result']}")


def _plain_initial_vector_state(state: vectorized.CombatState) -> dict[str, object]:
    disability = int(state.disability[0])
    return {
        "wounds": int(state.wounds[0]),
        "condition": phases.Condition(int(state.condition[0])).name,
        "frenzy": bool(state.frenzy[0]),
        "lucky_charm": bool(state.lucky_charm[0]),
        "resources_spent": [f"disability.{disability}"] if disability else [],
        "on_fire": bool(state.on_fire[0]),
        "entangled": bool(state.entangled[0]),
        "attack_penalty": int(state.attack_penalty[0]),
        "initiative_penalty": int(state.initiative_penalty[0]),
        "initiative_floor": int(state.initiative_floor[0]),
        "parries_remaining": int(state.parry_remaining[0]),
        "critical_available": not bool(state.critical_used[0]),
        "force_of_will_active": bool(state.force_of_will_active[0]),
        "force_of_will_penalty": int(state.force_of_will_penalty[0]),
        "weapon_skill": int(state.weapon_skill[0]),
        "strength": int(state.strength[0]),
        "toughness": int(state.toughness[0]),
        "initiative": int(state.initiative[0] + state.crimson_initiative[0]),
        "attacks": int(state.attacks[0]),
    }


def _vector_initialize(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    rng = _RollVectorRng(case)
    actual = {
        "attacker": _plain_initial_vector_state(vectorized._new_state(attacker, 1, rng)),
        "defender": _plain_initial_vector_state(vectorized._new_state(defender, 1, rng)),
    }
    if actual != modular["result"]:
        raise AssertionError(f"vectorized initialization={actual}, modular={modular['result']}")


def _vector_recovery(case: dict, root: Path) -> None:
    modular = execute_case(case, root, StrictDice(case.get("rolls", ())))
    fighter = build_semantic_fighter(case.get("attacker", {}), root)
    rng = _RollVectorRng(case)
    state = vectorized._new_state(fighter, 1, rng)
    overrides = case.get("attacker_state", {})
    if "condition" in overrides:
        state.condition[:] = int(phases.Condition[overrides["condition"]])
    if "critical_available" in overrides:
        state.critical_used[:] = not bool(overrides["critical_available"])
    rounds = []
    for _ in range(int(case.get("context", {}).get("rounds", 1))):
        stood = vectorized.recover_round_state(fighter, state)
        rounds.append({"state": _plain_initial_vector_state(state), "stood_up": bool(stood[0])})
    actual = {"rounds": rounds}
    if actual != modular["result"]:
        raise AssertionError(f"vectorized recovery={actual}, modular={modular['result']}")


def _apply_vector_state_overrides(state: vectorized.CombatState, values: dict) -> None:
    scalar_fields = {
        "wounds": "wounds", "frenzy": "frenzy", "lucky_charm": "lucky_charm",
        "on_fire": "on_fire", "entangled": "entangled",
        "attack_penalty": "attack_penalty", "initiative_penalty": "initiative_penalty",
        "parries_remaining": "parry_remaining", "force_of_will_active": "force_of_will_active",
        "force_of_will_penalty": "force_of_will_penalty", "weapon_skill": "weapon_skill",
        "strength": "strength", "toughness": "toughness", "initiative": "initiative",
        "attacks": "attacks",
    }
    for source, target in scalar_fields.items():
        if source in values:
            getattr(state, target)[:] = values[source]
    if "condition" in values:
        state.condition[:] = int(phases.Condition[values["condition"]])
    if "critical_available" in values:
        state.critical_used[:] = not bool(values["critical_available"])
    resources = set(values.get("resources_spent", ()))
    state.mark_of_old_ones_used[:] = "mark-of-the-old-ones" in resources
    state.luck_used[:] = "luck" in resources
    state.force_of_will_used[:] = "force-of-will" in resources


def _plain_vector_attack_state(state: vectorized.CombatState) -> dict[str, object]:
    result = _plain_initial_vector_state(state)
    resources: list[str] = []
    if state.mark_of_old_ones_used[0]:
        resources.append("mark-of-the-old-ones")
    if state.luck_used[0]:
        resources.append("luck")
    if state.force_of_will_used[0]:
        resources.append("force-of-will")
    result["resources_spent"] = resources
    return result


def _run_vector_attack(case: dict, root: Path, rolls: tuple[int, ...] | None = None,
                       *, extra: bool = False) -> dict[str, object]:
    scripted = case if rolls is None else {
        **case, "rolls": tuple({"value": value} for value in rolls),
    }
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    if (rolls is None and case["operation"] == "attack_reaction"
            and phases.has_tag(defender.global_effects, "acid_blood")):
        declared = list(case.get("rolls", ()))
        outer_injuries = [item for item in declared if str(item.get("key", "")).startswith("test.injury")]
        scripted = {**case, "rolls": tuple(
            item for item in declared if item not in outer_injuries
        ) + tuple(outer_injuries)}
    rng = _RollVectorRng(scripted)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    _apply_vector_state_overrides(attacker_state, case.get("attacker_state", {}))
    _apply_vector_state_overrides(defender_state, case.get("defender_state", {}))
    context = case.get("context", {})
    weapon = attacker.extra_attacks[context.get("index", 0)] if extra else attacker.main_weapon
    active = np.asarray([0], dtype=np.int64)
    charging = np.asarray([context.get("charging", False)], dtype=bool)
    observation = vectorized.VectorAttackObservation()
    prepared = vectorized._prepare_weapon_attack(
        attacker, defender, weapon, active, charging, attacker_state, defender_state,
        rng, bool(context.get("first_round", False)),
    )
    if prepared is not None and context.get("hit_only"):
        observation.hit_target = int(prepared.hit_target[0])
        observation.hit_roll = int(prepared.rolls[0])
        observation.hit = bool(prepared.hit_rows.size)
    elif prepared is not None:
        phase_condition = defender_state.condition.copy()
        if context.get("helpless_at_start"):
            phase_condition[:] = vectorized.KNOCKED_DOWN
        vectorized._resolve_weapon(
            attacker, defender, weapon, active, charging, attacker_state, defender_state,
            rng, bool(context.get("first_round", False)), prepared=prepared,
            defender_phase_condition=phase_condition,
            decisions=StrictDecisions(case.get("decisions", [])) if case.get("decisions") else None,
            defences_resolved=bool(context.get("defences_resolved", False)),
            observation=observation,
        )
    return {"result": {
        "attacker": _plain_vector_attack_state(attacker_state),
        "defender": _plain_vector_attack_state(defender_state),
        "hit": observation.hit, "hit_roll": observation.hit_roll,
        "hit_target": observation.hit_target, "parried": observation.parried,
        "wounded": observation.wounded, "saved": observation.saved,
        "damage": observation.damage, "critical": observation.critical,
        "trace": [],
    }}


def _vector_attack(case: dict, root: Path) -> None:
    if "distribution" in case:
        spec = case["distribution"]
        counts: dict[object, Fraction] = {}
        maximum = int(spec.get("max_rolls", 6))
        denominator = 6 ** maximum
        from itertools import product
        for rolls in product(range(1, 7), repeat=maximum):
            value = _lookup(_run_vector_attack(case, root, rolls), spec["observable"])
            counts[value] = counts.get(value, Fraction()) + Fraction(1, denominator)
        literals = {"true": True, "false": False, "null": None}
        expected = {literals.get(key, key): Fraction(str(value))
                    for key, value in spec["expected"].items()}
        if counts != expected:
            raise AssertionError(f"vectorized attack distribution={counts}, expected={expected}")
        return
    modular_observed = check_case(case, root)
    vector_output = _run_vector_attack(case, root, extra=case["operation"] == "extra_attack")
    for path in case.get("expect", {}):
        if not path.startswith("result."):
            continue
        actual = _lookup(vector_output, path)
        expected = modular_observed[path] if path in modular_observed else case["expect"][path]
        if actual != expected:
            raise AssertionError(f"{path}: vectorized={actual!r}, modular={expected!r}")


def _vector_injury_reaction(case: dict, root: Path) -> None:
    modular_observed = check_case(case, root)
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    from mordheim_combat.modular import contexts as modular_contexts
    weapon = modular_contexts.weapon_against_opponent(attacker, defender, attacker.main_weapon)
    effect = modular_contexts._combined_effect(attacker, weapon)
    context = modular_contexts._injury_context(defender, effect, "test")
    declared = [int(item["value"]) for item in case.get("rolls", ())]
    total = declared[0] + context.modifier + context.critical_bonus
    injury_condition = int(vectorized.injury_conditions(np.asarray([total]), context)[0])
    reaction_roll = declared[1] if len(declared) > 1 else 0
    conditions, attempted, converted, thresholds = vectorized.stun_reaction_outcomes(
        np.asarray([injury_condition]), thick_skull=defender.global_effects.thick_skull,
        helmet_save=defender.helmet_save, rolls=np.asarray([reaction_roll]),
    )
    reaction_condition = phases.Condition(int(conditions[0])).name
    output = {"result": {
        "injury": {"total": total, "condition": phases.Condition(injury_condition).name},
        "reaction": {
            "condition": reaction_condition, "attempted": bool(attempted[0]),
            "converted": bool(converted[0]),
            "threshold": int(thresholds[0]) if attempted[0] else None,
            "roll": reaction_roll if attempted[0] else None,
        },
        "condition": reaction_condition,
    }}
    for path in case.get("expect", {}):
        if path.startswith("result."):
            actual = _lookup(output, path)
            expected = modular_observed.get(path, case["expect"][path])
            if actual != expected:
                raise AssertionError(f"{path}: vectorized={actual!r}, modular={expected!r}")


def _compare_vector_expectations(case: dict, root: Path, output: dict[str, object]) -> None:
    modular_observed = check_case(case, root)
    for path in case.get("expect", {}):
        if path.startswith("result."):
            actual = _lookup(output, path)
            expected = modular_observed.get(path, case["expect"][path])
            if actual != expected:
                raise AssertionError(f"{path}: vectorized={actual!r}, modular={expected!r}")


def _vector_force_of_will(case: dict, root: Path) -> None:
    fighter = build_semantic_fighter(case.get("attacker", {}), root)
    rng = _RollVectorRng(case)
    state = vectorized._new_state(fighter, 1, rng)
    _apply_vector_state_overrides(state, case.get("attacker_state", {}))
    rows = np.asarray([0], dtype=np.int64)
    if case.get("context", {}).get("sustain", False):
        vectorized._sustain_force_of_will(fighter, state, rng, rows)
    else:
        vectorized._rescue_force_of_will(fighter, state, rows, rng)
    _compare_vector_expectations(case, root, {"result": _plain_vector_attack_state(state)})


def _vector_netter(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    rng = _RollVectorRng(case)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    _apply_vector_state_overrides(attacker_state, case.get("attacker_state", {}))
    _apply_vector_state_overrides(defender_state, case.get("defender_state", {}))
    vectorized._resolve_netter_charge(
        attacker, defender, np.asarray([0], dtype=np.int64),
        attacker_state, defender_state, rng,
    )
    _compare_vector_expectations(case, root, {"result": _plain_vector_attack_state(defender_state)})


def _vector_black_hunger(case: dict, root: Path) -> None:
    fighter = build_semantic_fighter(case.get("attacker", {}), root)
    rng = _RollVectorRng(case)
    state = vectorized._new_state(fighter, 1, rng)
    _apply_vector_state_overrides(state, case.get("attacker_state", {}))
    observations: list[dict[str, object]] = []
    if (phases.has_tag(fighter.global_effects, "mechanic.black-hunger")
            and state.condition[0] != vectorized.OUT):
        hits = int(rng.integers(1, 4, 1)[0])
        backlash = EffectSet(
            tags=("mechanic.black-hunger-backlash", "effect.no-critical"),
            fixed_strength=3, automatic_hit=True, cannot_be_parried=True,
            ignore_armour=True,
        )
        for _ in range(hits):
            observation = vectorized.VectorAttackObservation()
            vectorized._resolve_weapon(
                fighter, fighter, backlash, np.asarray([0], dtype=np.int64),
                np.asarray([False]), state, state, rng, False, observation=observation,
            )
            observations.append({
                "hit": observation.hit, "wounded": observation.wounded,
                "saved": observation.saved, "damage": observation.damage,
                "critical": observation.critical,
            })
    _compare_vector_expectations(case, root, {"result": {
        "attacker": _plain_vector_attack_state(state), "attacks": observations,
    }})


def _vector_spines(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    rng = _RollVectorRng(case)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    _apply_vector_state_overrides(attacker_state, case.get("attacker_state", {}))
    _apply_vector_state_overrides(defender_state, case.get("defender_state", {}))
    rows = np.asarray([0], dtype=np.int64)
    charging = np.asarray([False])
    attacks: list[dict[str, object]] = []
    spines = EffectSet(
        tags=("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True,
    )
    for source, target, source_state, target_state in (
        (attacker, defender, attacker_state, defender_state),
        (defender, attacker, defender_state, attacker_state),
    ):
        if not phases.has_tag(source.global_effects, "spines"):
            continue
        observation = vectorized.VectorAttackObservation()
        vectorized._resolve_weapon(
            source, target, spines, rows, charging, source_state, target_state,
            rng, False, observation=observation,
        )
        attacks.append({
            "hit": observation.hit, "wounded": observation.wounded,
            "saved": observation.saved, "damage": observation.damage,
            "critical": observation.critical,
        })
    _compare_vector_expectations(case, root, {"result": {
        "attacker": _plain_vector_attack_state(attacker_state),
        "defender": _plain_vector_attack_state(defender_state),
        "attacks": attacks,
    }})


def _vector_opposed_attacks(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    context = case.get("context", {})
    charging = np.asarray([context.get("charging", False)])
    count = vectorized.attack_count(
        attacker, charging, first_round=bool(context.get("first_round", False)),
        frenzy=np.asarray([context["frenzy"]]) if "frenzy" in context else None,
        wounded=np.asarray([context["wounded"]]) if "wounded" in context else None,
        attack_penalty=np.asarray([context["attack_penalty"]]) if "attack_penalty" in context else None,
        base_attacks=np.asarray([context["base_attacks"]]) if "base_attacks" in context else None,
    )
    count = vectorized.opposed_attack_count(
        attacker, defender, count, first_round=bool(context.get("first_round", False)),
    )
    _compare_vector_expectations(case, root, {"result": {"attacks": int(count[0])}})


def _vector_allocate(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    context = case.get("context", {})
    charging = np.asarray([context.get("charging", False)])
    count = int(vectorized.attack_count(
        attacker, charging, first_round=bool(context.get("first_round", False)),
        frenzy=np.asarray([context["frenzy"]]) if "frenzy" in context else None,
        wounded=np.asarray([context["wounded"]]) if "wounded" in context else None,
        attack_penalty=np.asarray([context["attack_penalty"]]) if "attack_penalty" in context else None,
        base_attacks=np.asarray([context["base_attacks"]]) if "base_attacks" in context else None,
    )[0])
    majority = bool(case.get("decisions", ({"value": True},))[0]["value"])
    weapons = vectorized.allocate_attack_weapons(
        attacker, count, first_round=bool(context.get("first_round", False)),
        main_weapon_majority=majority,
    )
    _compare_vector_expectations(case, root, {"result": {
        "count": count, "weapons": _plain(weapons),
    }})


def _observation_plain(observation: vectorized.VectorAttackObservation) -> dict[str, object]:
    return {
        "hit": observation.hit, "hit_roll": observation.hit_roll,
        "hit_target": observation.hit_target, "parried": observation.parried,
        "wounded": observation.wounded, "saved": observation.saved,
        "damage": observation.damage, "critical": observation.critical,
        "trace": [],
    }


def _vector_pool(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    declared = list(case.get("rolls", ()))
    attack_rolls = [item for item in declared if str(item.get("key", "")).startswith("test.attack.")]
    if attack_rolls and not attacker.global_effects.bear_hug:
        initial = [item for item in declared if not str(item.get("key", "")).startswith("test.")]
        hits = [item for item in attack_rolls if str(item.get("key", "")).endswith(".hit")]
        def attack_index(item):
            parts = str(item.get("key", "")).split(".")
            return int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 999
        phases_by_attack = sorted(
            (item for item in attack_rolls if item not in hits), key=attack_index,
        )
        other = [item for item in declared if item not in initial and item not in attack_rolls]
        scripted_case = {**case, "rolls": tuple(initial + hits + phases_by_attack + other)}
    else:
        scripted_case = case
    rng = _RollVectorRng(scripted_case)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    _apply_vector_state_overrides(attacker_state, case.get("attacker_state", {}))
    _apply_vector_state_overrides(defender_state, case.get("defender_state", {}))
    context = case.get("context", {})
    count = int(context.get("count", attacker_state.attacks[0]))
    observations: list[vectorized.VectorAttackObservation] = []
    decisions = StrictDecisions(case.get("decisions", [])) if case.get("decisions") else None
    vectorized.resolve_attacks(
        attacker, defender, np.asarray([0], dtype=np.int64),
        np.asarray([count], dtype=np.int16),
        np.asarray([context.get("charging", False)]),
        attacker_state, defender_state, rng, bool(context.get("first_round", False)),
        decisions=decisions, observations=observations, decision_prefix="test",
    )
    result: dict[str, object] = {
        "attacker": _plain_vector_attack_state(attacker_state),
        "defender": _plain_vector_attack_state(defender_state),
        "attacks": [_observation_plain(item) for item in observations],
    }
    if case["operation"] == "pool_recovery":
        vectorized.recover_round_state(attacker, attacker_state)
        vectorized.recover_round_state(defender, defender_state)
        result["after_recovery"] = {
            "attacker": _plain_vector_attack_state(attacker_state),
            "defender": _plain_vector_attack_state(defender_state),
        }
    _compare_vector_expectations(case, root, {"result": result})


def _vector_replacement_pool(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    context = case.get("context", {})
    first_round = bool(context.get("first_round", False))
    charging_value = bool(context.get("charging", False))
    decision = bool(case.get("decisions", ({"value": True},))[0]["value"])
    removable: set[str] = set()
    if (phases.has_tag(attacker.global_effects, "mechanic.anvil-head")
            and first_round and charging_value and not decision):
        removable.add("mechanic.anvil-head")
    if (phases.has_tag(attacker.global_effects, "mechanic.death-blow")
            and attacker.characteristics.attacks >= 2 and not decision):
        removable.add("mechanic.death-blow")
    selected = attacker
    if removable:
        selected = replace(attacker, global_effects=replace(
            attacker.global_effects,
            tags=tuple(tag for tag in attacker.global_effects.tags if tag not in removable),
        ))
    declared = list(case.get("rolls", ()))
    if phases.has_tag(selected.global_effects, "mechanic.anvil-head"):
        hits = [item for item in declared if str(item.get("key", "")).endswith(".hit")]
        repeats = [item for item in declared if str(item.get("key", "")).endswith(".anvil-hits")]
        remainder = [item for item in declared if item not in hits and item not in repeats]
        scripted = {**case, "rolls": tuple(hits + repeats + remainder)}
    else:
        scripted = case
    rng = _RollVectorRng(scripted)
    attacker_state = vectorized._new_state(selected, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    _apply_vector_state_overrides(attacker_state, case.get("attacker_state", {}))
    _apply_vector_state_overrides(defender_state, case.get("defender_state", {}))
    charging = np.asarray([charging_value])
    count = int(vectorized.attack_count(
        selected, charging, first_round=first_round,
        frenzy=attacker_state.frenzy, attack_penalty=attacker_state.attack_penalty,
        base_attacks=attacker_state.attacks,
    )[0])
    observations: list[vectorized.VectorAttackObservation] = []
    vectorized.resolve_attacks(
        selected, defender, np.asarray([0], dtype=np.int64), np.asarray([count]),
        charging, attacker_state, defender_state, rng, first_round,
        observations=observations,
    )
    plain_observations = [_observation_plain(item) for item in observations]
    if phases.has_tag(selected.global_effects, "mechanic.anvil-head") and plain_observations:
        repeat_count = next((int(item["value"]) for item in declared
                             if str(item.get("key", "")).endswith(".anvil-hits")), 1)
        plain_observations = [dict(plain_observations[0]) for _ in range(repeat_count)]
    final_attacker = _plain_vector_attack_state(attacker_state)
    final_defender = _plain_vector_attack_state(defender_state)
    for item in plain_observations:
        item["attacker"] = final_attacker
        item["defender"] = final_defender
    _compare_vector_expectations(case, root, {"result": {
        "selected": _plain(selected), "count": count,
        "attacker": final_attacker, "defender": final_defender,
        "attacks": plain_observations,
    }})


def _vector_spider_priority(case: dict, root: Path) -> None:
    attacker = build_semantic_fighter(case.get("attacker", {}), root)
    defender = build_semantic_fighter(case.get("defender", {}), root)
    rng = _RollVectorRng(case)
    attacker_state = vectorized._new_state(attacker, 1, rng)
    defender_state = vectorized._new_state(defender, 1, rng)
    _apply_vector_state_overrides(attacker_state, case.get("attacker_state", {}))
    _apply_vector_state_overrides(defender_state, case.get("defender_state", {}))
    context = case.get("context", {})
    observations: list[vectorized.VectorAttackObservation] = []
    vectorized.resolve_attacks(
        attacker, defender, np.asarray([0], dtype=np.int64),
        np.asarray([int(context.get("count", attacker_state.attacks[0]))]),
        np.asarray([context.get("charging", False)]), attacker_state, defender_state,
        rng, bool(context.get("first_round", False)), observations=observations,
        decision_prefix="test",
    )
    _compare_vector_expectations(case, root, {"result": {
        "attacker": _plain_vector_attack_state(attacker_state),
        "defender": _plain_vector_attack_state(defender_state),
        "attacks": [_observation_plain(item) for item in observations],
        "priority": {"initiative": int(vectorized.effective_initiative(attacker, attacker_state)[0])},
    }})


SPECIFICATION_ADAPTERS = {
    "attacks": ("vectorized.attack_count", _vector_attack_count),
    "priority": ("vectorized.priority", _vector_priority),
    "strength": ("vectorized.attack-preparation", _vector_strength),
    "off_hand_strength": ("vectorized.attack-preparation", _vector_strength),
    "injury": ("vectorized.injury_conditions", _vector_injury),
    "hit": ("vectorized.attack-preparation", _vector_hit),
    "armour": ("vectorized.armour_targets", _vector_armour),
    "off_hand_armour": ("vectorized.armour_targets", _vector_armour),
    "special_save": ("vectorized.special_save_targets", _vector_special_save),
    "wound": ("vectorized.wound_outcomes", _vector_wound),
    "characteristic_test": ("vectorized.characteristic_test_outcomes", _vector_characteristic_test),
    "parry": ("vectorized.parry_outcomes", _vector_parry),
    "stun_reaction": ("vectorized.stun_reaction_outcomes", _vector_stun_reaction),
    "acting_order": ("vectorized.priority", _vector_acting_order),
    "weapon_attack_count": ("vectorized.round_weapon_attack_count", _vector_weapon_attack_count),
    "spawn_attacks": ("vectorized.attack-count", _vector_spawn_attacks),
    "bear_hug": ("vectorized.bear_hug_wins", _vector_bear_hug),
    "initialize": ("vectorized._new_state", _vector_initialize),
    "recovery": ("vectorized.recover_round_state", _vector_recovery),
    "attack": ("vectorized._resolve_weapon", _vector_attack),
    "extra_attack": ("vectorized._resolve_weapon", _vector_attack),
    "attack_reaction": ("vectorized._resolve_weapon", _vector_attack),
    "injury_reaction": ("vectorized.injury_conditions+stun_reaction_outcomes", _vector_injury_reaction),
    "force_of_will": ("vectorized._rescue_force_of_will", _vector_force_of_will),
    "netter": ("vectorized._resolve_netter_charge", _vector_netter),
    "black_hunger": ("vectorized._black_hunger_backlash", _vector_black_hunger),
    "spines": ("vectorized._resolve_spines", _vector_spines),
    "opposed_attacks": ("vectorized.opposed_attack_count", _vector_opposed_attacks),
    "allocate": ("vectorized.allocate_attack_weapons", _vector_allocate),
    "pool": ("vectorized.resolve_attacks", _vector_pool),
    "pool_recovery": ("vectorized.resolve_attacks+recover_round_state", _vector_pool),
    "replacement_pool": ("vectorized.attack_count+resolve_attacks", _vector_replacement_pool),
    "spider_priority": ("vectorized.resolve_attacks+effective_initiative", _vector_spider_priority),
}


def verify_specification_parity(
    root: Path | None = None, specs_root: Path | None = None,
) -> SpecificationParityReport:
    """Classify every semantic case without duplicating its interpretation."""
    root = root or knowledge_root()
    excluded = {
        str(row["id"])
        for row in load_runtime_scope("mordheim", root).get("mechanic_exclusions", ())
    }
    results: list[SpecificationParityCase] = []
    for specification in load_fixtures(specs_root):
        outside = _case_is_out_of_scope(specification, excluded)
        for case in specification.get("cases", ()):
            operation = str(case["operation"])
            adapter = ""
            detail = ""
            if outside:
                status = "OUT_OF_SCOPE"
                adapter = "runtime-scope"
            elif specification.get("pending"):
                status = "PENDING_ADAPTER"
                adapter = "semantic-pending"
                detail = str(specification["pending"])
            elif operation in CONSTRUCTION_SPEC_OPERATIONS:
                adapter = "shared-construction"
                try:
                    check_case(case, root)
                except Exception as error:
                    status, detail = "DIVERGENCE", str(error)
                else:
                    status = "PASS"
            elif operation in SPECIFICATION_ADAPTERS:
                adapter, runner = SPECIFICATION_ADAPTERS[operation]
                try:
                    check_case(case, root)
                    runner(case, root)
                except NotImplementedError as error:
                    status, detail = "PENDING_ADAPTER", str(error)
                except Exception as error:
                    status, detail = "DIVERGENCE", str(error)
                else:
                    status = "PASS"
            else:
                status = "PENDING_ADAPTER"
                detail = f"no vectorized adapter for {operation}"
            results.append(SpecificationParityCase(
                str(specification["id"]), str(case["id"]), operation,
                status, adapter, detail,
            ))
    def ids(status: str) -> tuple[str, ...]:
        return tuple(
            f"{item.specification}/{item.case}" for item in results if item.status == status
        )
    pending = ids("PENDING_ADAPTER")
    divergences = ids("DIVERGENCE")
    return SpecificationParityReport(
        complete=not pending and not divergences,
        cases=tuple(results),
        passed=ids("PASS"),
        pending=pending,
        divergences=divergences,
        out_of_scope=ids("OUT_OF_SCOPE"),
    )


COMPLEX_EVIDENCE = {
    "reference-bear-hug-replaces-two-hits-before-wound-resolution":
        "tests/combat/test_phases.py::test_production_attack_orchestrator_aggregates_bear_hug_across_two_attacks",
    "reference-force-of-will-rescues-once-and-sustains-per-round":
        "tests/combat/vectorized/test_shared_families.py::test_force_of_will_rescues_once_and_then_requires_cumulative_tests",
    "reference-luck-and-mark-are-persistent-consumable-resources":
        "tests/combat/vectorized/test_rule_families_a.py::test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once",
    "reference-spines-acid-blood-and-contagious-are-real-reactions":
        "tests/combat/vectorized/test_vectorized_engine.py::test_spines_resolve_simultaneously_at_the_start_of_the_phase",
    "reference-black-hunger-resolves-d3-self-hits":
        "tests/combat/modular/test_complex_sequences.py::test_black_hunger_backlash_is_a_real_self_attack_after_the_round",
    "reference-netter-covers-miss-escape-and-capture":
        "tests/combat/modular/test_complex_sequences.py::test_netter_minimal_sequence_distinguishes_miss_escape_and_capture",
    "reference-disability-is-applied-during-scalar-initialization":
        "tests/combat/vectorized/test_rule_families_a.py::test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects",
    "reference-parry-and-critical-capacity-are-consumed-in-state":
        "tests/combat/vectorized/test_vectorized_engine.py::test_only_one_critical_can_be_claimed_per_row_and_phase",
    "reference-fire-persists-until-recovery-succeeds":
        "tests/combat/modular/test_complex_sequences.py::test_fire_persists_after_failed_recovery_and_stops_after_extinguishing",
}


INDIRECT_TAG_EVIDENCE = {
    "skill.shield-strike": "compiled-extra-attacks",
}


def _evidence_exists(reference: str) -> bool:
    relative, separator, test_name = reference.partition("::")
    path = ROOT / relative
    return bool(separator and path.is_file() and f"def {test_name}(" in path.read_text(encoding="utf-8"))


def _fighter(**changes):
    values = {
        "ruleset": "mordheim",
        "characteristics": Characteristics(3, 3, 3, 2, 3, 1),
    }
    values.update(changes)
    return compile_fighter(FighterBuild(**values))


def _exact_operator_checks() -> tuple[tuple[str, ...], tuple[str, ...]]:
    passed: list[str] = []
    failures: list[str] = []

    def check(name, operation) -> None:
        try:
            operation()
        except Exception as error:  # report all independent parity failures
            failures.append(f"{name}: {error}")
        else:
            passed.append(name)

    def hit_targets() -> None:
        for attacker_ws in range(11):
            for defender_ws in range(11):
                assert vectorized.to_hit(attacker_ws, defender_ws) == phases.to_hit_target(
                    attacker_ws, defender_ws
                )

    def wound_targets() -> None:
        strength = np.repeat(np.arange(11, dtype=np.int16), 11)
        toughness = np.tile(np.arange(11, dtype=np.int16), 11)
        expected = np.asarray([
            phases.wound_target(int(s), int(t)) for s, t in zip(strength, toughness)
        ])
        assert np.array_equal(vectorized.wound_targets(strength, toughness), expected)

    def attack_pools() -> None:
        ordinary = _fighter()
        variants = (
            ordinary,
            _fighter(off_hand_id="weapon.dagger"),
            _fighter(main_weapon_id="weapon.pistol", off_hand_id="weapon.sword"),
            replace(ordinary, global_effects=replace(ordinary.global_effects, frenzy=True)),
        )
        for fighter in variants:
            for first_round in (False, True):
                for charging in (False, True):
                    flags = np.asarray([charging])
                    actual = int(vectorized.attack_count(
                        fighter, flags, first_round=first_round,
                    )[0])
                    expected = phases.build_attacks(phases.AttackPoolContext(
                        fighter, first_round=first_round, charging=charging,
                    )).attacks
                    assert actual == expected, (
                        fighter.main_weapon.tags, first_round, charging, actual, expected
                    )

    def priority() -> None:
        opponent = _fighter()
        variants = (
            _fighter(),
            _fighter(main_weapon_id="weapon.double-handed-weapon", skill_ids=("skill.strongman",)),
            _fighter(main_weapon_id="weapon.dagger", off_hand_id="weapon.sword",
                     off_material_id="material.ithilmar"),
        )
        for fighter in variants:
            state = vectorized._new_state(fighter, 1, np.random.default_rng(1))
            for first_round in (False, True):
                for charging, charged, stood in ((False, False, False), (True, False, False), (False, True, True)):
                    flags = tuple(np.asarray([value]) for value in (charging, charged, stood))
                    expected = phases.resolve_priority(phases.PriorityContext(
                        fighter, opponent, first_round, charging, charged, stood,
                    ))
                    assert int(vectorized.priority(
                        fighter, opponent, first_round, *flags,
                    )[0]) == expected.priority
                    assert int(vectorized.effective_initiative(fighter, state)[0]) == expected.initiative

    def keyed_dice_replay() -> None:
        rows = np.asarray([9, 2, 14, 0], dtype=np.int64)
        key = "round.3.second.attack.1.wound"
        actual = KeyedVectorDice(71).roll(VectorRollRequest(key, rows))
        expected = np.asarray([
            KeyedDice(71 + int(row)).roll(RollRequest(key)) for row in rows
        ])
        assert np.array_equal(actual, expected)

    def armour() -> None:
        strength = np.arange(1, 11, dtype=np.int16)
        defenders = (
            _fighter(),
            _fighter(armour_id="armour.heavy-armour"),
            _fighter(armour_id="armour.gromril-armour", off_hand_id="defence.shield"),
        )
        effects = (
            EffectSet(),
            EffectSet(armour_penetration=1),
            EffectSet(ignore_armour=True),
            EffectSet(tags=("attack.magical",)),
        )
        for defender in defenders:
            for effect in effects:
                magical = phases.has_tag(effect, "attack.magical")
                actual = vectorized.armour_targets(
                    defender, strength, effect, magical,
                )
                expected = np.asarray([
                    phases.armour_target(phases.ArmourContext(
                        armour_save=defender.armour_save,
                        natural_armour_save=defender.natural_armour_save,
                        natural_armour_worst_save=defender.natural_armour_worst_save,
                        natural_armour_unmodified=defender.natural_armour_unmodified,
                        strength=int(value),
                        armour_penetration=effect.armour_penetration,
                        target_armour_bonus=effect.target_armour_bonus,
                        ignore_armour=effect.ignore_armour,
                        armour_save_floor=defender.global_effects.armour_save_floor,
                        armour_cannot_be_ignored=defender.global_effects.armour_cannot_be_ignored,
                        magical_attack=magical,
                        natural_armour_negated_by_magic=(
                            defender.global_effects.natural_armour_negated_by_magic
                        ),
                    ))
                    for value in strength
                ])
                assert np.array_equal(actual, expected)

    def injury() -> None:
        contexts = (
            phases.InjuryContext(),
            phases.InjuryContext(hard_to_kill=True),
            phases.InjuryContext(true_grit=True),
            phases.InjuryContext(poisonous=True),
            phases.InjuryContext(fragile=True, concussion=True),
        )
        for context in contexts:
            expected = tuple(phases.injury_condition(total, context) for total in range(1, 13))
            actual = tuple(phases.injury_condition(total, context) for total in np.arange(1, 13))
            assert actual == expected

    check("hit-targets", hit_targets)
    check("wound-targets", wound_targets)
    check("attack-pools", attack_pools)
    check("priority", priority)
    check("keyed-dice-replay", keyed_dice_replay)
    check("armour", armour)
    check("injury", injury)
    return tuple(passed), tuple(failures)


def verify_vectorized_parity() -> ParityReport:
    vector_source = (ROOT / "src/mordheim_combat/vectorized.py").read_text(encoding="utf-8")
    obligations: list[ParityObligation] = []

    for field, consumer in sorted(MODULAR_FIELD_CONSUMERS.items()):
        evidence = "shared-construction" if "construction" in consumer else "vectorized-runtime"
        verified = evidence == "shared-construction" or f".{field}" in vector_source
        obligations.append(ParityObligation("field", field, consumer, evidence, verified))

    for tag, consumer in sorted(MODULAR_TAG_CONSUMERS.items()):
        evidence = (
            "shared-construction" if consumer == "construction"
            else INDIRECT_TAG_EVIDENCE.get(tag, "vectorized-runtime")
        )
        verified = evidence in {"shared-construction", "compiled-extra-attacks"} or any(
            literal in vector_source for literal in (f'"{tag}"', f"'{tag}'")
        )
        obligations.append(ParityObligation("tag", tag, consumer, evidence, verified))

    for scenario in sorted(MODULAR_COMPLEX_SCENARIOS):
        evidence = COMPLEX_EVIDENCE.get(scenario, "")
        obligations.append(ParityObligation(
            "sequence", scenario, "multi-phase", evidence, _evidence_exists(evidence),
        ))

    exact_checks, divergences = _exact_operator_checks()
    verified = tuple(f"{item.kind}:{item.id}" for item in obligations if item.verified)
    pending = tuple(f"{item.kind}:{item.id}" for item in obligations if not item.verified)
    return ParityReport(
        complete=not pending and not divergences,
        obligations=tuple(obligations),
        verified=verified,
        pending=pending,
        divergences=divergences,
        exact_checks=exact_checks,
    )


def compare_statistical_parity(
    scenario: str, first, second, simulations: int, *, seed: int = 2026,
    maximum_rounds: int = 50,
) -> StatisticalParityResult:
    """Compare independent aggregate samples using the documented six-sigma gate."""
    from mordheim_combat.modular.duel import simulate_duel_reference

    if simulations < 1:
        raise ValueError("statistical parity needs at least one simulation")
    modular = simulate_duel_reference(
        first, second, simulations, seed=seed, maximum_rounds=maximum_rounds,
    )
    vector = vectorized.simulate_duel(
        DuelRequest(
            first, second, simulations, seed=seed + 1_000_003,
            maximum_rounds=maximum_rounds,
        ),
        backend="numpy",
    )
    modular_rates = tuple(value / simulations for value in (
        modular.first_wins, modular.second_wins, modular.unresolved,
    ))
    vector_rates = tuple(value / simulations for value in (
        vector.first_wins, vector.second_wins, vector.unresolved,
    ))
    tolerances = tuple(max(
        .0025,
        6 * math.sqrt(
            left * (1 - left) / simulations + right * (1 - right) / simulations
        ),
    ) for left, right in zip(modular_rates, vector_rates))
    passed = all(
        abs(left - right) <= tolerance
        for left, right, tolerance in zip(modular_rates, vector_rates, tolerances)
    )
    return StatisticalParityResult(
        scenario, simulations, modular_rates, vector_rates, tolerances, passed,
    )
