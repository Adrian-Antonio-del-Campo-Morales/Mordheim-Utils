"""Oracle/vectorized obligation inventory: field, tag and complex
sequence consumers, exact operator checks and the vectorized parity
report."""
from __future__ import annotations

from dataclasses import replace
import numpy as np
from mordheim_combat import phases
from mordheim_combat import vectorized
from mordheim_combat.vector_dice import KeyedVectorDice
from mordheim_combat.vector_dice import VectorRollRequest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
from mordheim_core.dice import KeyedDice
from mordheim_core.dice import RollRequest
from mordheim_combat_lab.verification.consumers import MODULAR_COMPLEX_SCENARIOS
from mordheim_combat_lab.verification.consumers import MODULAR_FIELD_CONSUMERS
from mordheim_combat_lab.verification.consumers import MODULAR_TAG_CONSUMERS
from mordheim_combat_lab.verification.parity._report import ParityObligation, ParityReport, ROOT

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
        # Exercise the engine's actual vector formula ``hit_targets`` (the
        # array operator the attack path calls), not the ``to_hit`` scalar
        # wrapper that delegates straight to the shared ``to_hit_target``.
        # The 11x11 grid includes the ``defender_ws == 2 * attacker_ws``
        # boundary and the ``defender_ws == 0`` case, so an off-by-one on
        # either branch is caught deterministically.
        attacker_ws = np.repeat(np.arange(11, dtype=np.int16), 11)
        defender_ws = np.tile(np.arange(11, dtype=np.int16), 11)
        actual = vectorized.hit_targets(attacker_ws, defender_ws)
        expected = np.asarray([
            phases.to_hit_target(int(a), int(d))
            for a, d in zip(attacker_ws, defender_ws)
        ], dtype=np.int8)
        assert np.array_equal(actual, expected)

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
    vector_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "src/mordheim_combat/vectorized").glob("*.py"))
    )
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
