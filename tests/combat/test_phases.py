"""Contratos puros de fases."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from mordheim_combat_lab.combat.phases import ArmourContext
from mordheim_combat_lab.combat.phases import AttackPoolContext
from mordheim_combat_lab.combat.phases import BearHugContext
from mordheim_combat_lab.combat.phases import Condition
from mordheim_combat_lab.combat.phases import HitContext
from mordheim_combat_lab.combat.phases import InjuryContext
from mordheim_combat_lab.combat.phases import ParryContext
from mordheim_combat_lab.combat.phases import Phase
from mordheim_combat_lab.combat.phases import PriorityContext
from mordheim_combat_lab.combat.phases import RoundContext
from mordheim_combat_lab.combat.phases import SpecialSaveContext
from mordheim_combat_lab.combat.phases import StrikeContext
from mordheim_combat_lab.combat.phases import WoundContext
from mordheim_combat_lab.combat.phases import armour_target
from mordheim_combat_lab.combat.phases import build_attacks
from mordheim_combat_lab.combat.phases import resolve_armour
from mordheim_combat_lab.combat.phases import resolve_attack
from mordheim_combat_lab.combat.phases import resolve_bear_hug
from mordheim_combat_lab.combat.phases import resolve_hit
from mordheim_combat_lab.combat.phases import resolve_injury
from mordheim_combat_lab.combat.phases import resolve_parry
from mordheim_combat_lab.combat.phases import resolve_priority
from mordheim_combat_lab.combat.phases import resolve_strike_sequence
from mordheim_combat_lab.combat.phases import resolve_special_save
from mordheim_combat_lab.combat.phases import resolve_wound
from mordheim_combat_lab.combat.phases import to_hit_target
from mordheim_combat_lab.combat.phases import wound_target
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.dice import AlwaysAccept
from mordheim_combat_lab.domain.dice import AlwaysReject
from mordheim_combat_lab.domain.dice import KeyedDice
from mordheim_combat_lab.domain.dice import RollRequest
from mordheim_combat_lab.domain.dice import ScriptedDice
from mordheim_combat_lab.domain.dice import exact_distribution
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import EffectSet
from mordheim_combat_lab.domain.models import FighterBuild
import numpy as np
import pytest as pytest


class VectorTape:
    def __init__(self,*values):
        self.values=list(values)

    def integers(self,low,high=None,size=None,dtype=None):
        value=self.values.pop(0)
        result=np.asarray(value if np.ndim(value) else np.full(size or 1,value),dtype=dtype)
        return result if size is not None else result.item()


def fighter(**changes):
    build = dict(
        ruleset="mordheim",
        characteristics=Characteristics(3, 3, 3, 1, 3, 1),
    )
    build.update(changes)
    return compile_fighter(FighterBuild(**build))


@pytest.mark.parametrize(
    ("attacker_ws", "defender_ws", "expected"),
    ((3, 0, 2), (4, 3, 3), (3, 3, 4), (2, 5, 5), (3, 6, 4)),
)
def test_to_hit_table_is_a_pure_exhaustive_threshold(attacker_ws, defender_ws, expected):
    assert to_hit_target(attacker_ws, defender_ws) == expected
    outcomes = exact_distribution(
        (6,),
        lambda rolls: resolve_hit(
            HitContext(attacker_ws, defender_ws), ScriptedDice(rolls)
        ).success,
    )
    assert outcomes[True] == Fraction(7 - expected, 6)


def test_hit_modifier_and_reroll_are_local_composable_operators():
    improved = resolve_hit(HitContext(3, 3, modifier=1), ScriptedDice((3,)))
    rerolled = resolve_hit(HitContext(3, 3, reroll=True), ScriptedDice((3, 4)))
    assert (improved.target, improved.success) == (3, True)
    assert (rerolled.target, rerolled.success, rerolled.rerolled) == (4, True, True)
    distribution = exact_distribution(
        (6, 6),
        lambda rolls: resolve_hit(HitContext(3, 3, reroll=True), ScriptedDice(rolls)).success,
    )
    assert distribution == {False: Fraction(1, 4), True: Fraction(3, 4)}


@pytest.mark.parametrize(
    ("strength", "toughness", "expected"),
    ((5, 3, 2), (4, 3, 3), (3, 3, 4), (3, 4, 5), (3, 5, 6), (3, 7, 7)),
)
def test_to_wound_table_is_independently_exhaustive(strength, toughness, expected):
    assert wound_target(strength, toughness) == expected
    outcomes = exact_distribution(
        (6,),
        lambda rolls: resolve_wound(
            WoundContext(strength, toughness), ScriptedDice(rolls)
        ).success,
    )
    expected_success = Fraction(max(0, 7 - expected), 6)
    assert outcomes.get(True, Fraction(0)) == expected_success


def test_automatic_wound_never_synthesizes_a_critical():
    result = resolve_wound(WoundContext(3, 3, automatic=True), ScriptedDice(()))
    assert result.success and not result.critical and result.roll == 0


def test_failed_wound_can_still_succeed_without_inventing_a_critical():
    failed = resolve_wound(
        WoundContext(3, 6, failure_still_wounds=True), ScriptedDice((1,))
    )
    critical = resolve_wound(
        WoundContext(3, 3, failure_still_wounds=True), ScriptedDice((6,))
    )
    assert failed.success and failed.roll == 1 and not failed.critical
    assert critical.success and critical.critical


def test_armour_phase_owns_strength_penetration_natural_armour_and_floors():
    ordinary = ArmourContext(armour_save=5, strength=4, armour_penetration=1)
    natural = replace(ordinary, natural_armour_save=5, natural_armour_unmodified=True)
    ignored = replace(ordinary, ignore_armour=True)
    untiring = replace(ignored, armour_save_floor=6, armour_cannot_be_ignored=True)
    assert armour_target(ordinary) == 7
    assert armour_target(natural) == 5
    assert armour_target(ignored) == 7
    assert armour_target(untiring) == 6
    assert resolve_armour(natural, ScriptedDice((5,))).saved


def test_special_saves_resolve_ward_before_regeneration_exactly():
    context = SpecialSaveContext(ward_save=5, regeneration_save=4)
    distribution = exact_distribution(
        (6, 6),
        lambda rolls: resolve_special_save(context, ScriptedDice(rolls)).saved,
    )
    assert distribution == {False: Fraction(1, 3), True: Fraction(2, 3)}
    assert resolve_special_save(context, ScriptedDice((5, 1))).source == "ward"
    assert resolve_special_save(context, ScriptedDice((1, 4))).source == "regeneration"


@pytest.mark.parametrize(
    ("roll", "context", "condition"),
    (
        (1, InjuryContext(), Condition.KNOCKED_DOWN),
        (3, InjuryContext(), Condition.STUNNED),
        (5, InjuryContext(), Condition.OUT),
        (5, InjuryContext(hard_to_kill=True), Condition.STUNNED),
        (3, InjuryContext(true_grit=True), Condition.KNOCKED_DOWN),
        (4, InjuryContext(true_grit=True), Condition.STUNNED),
        (4, InjuryContext(injury_profile=3), Condition.OUT),
        (6, InjuryContext(survivor=True), Condition.STUNNED),
        (3, InjuryContext(ignore_pain=True), Condition.KNOCKED_DOWN),
    ),
)
def test_injury_profiles_are_local_roll_mappings(roll, context, condition):
    assert resolve_injury(context, ScriptedDice((roll,))).condition == condition


def test_parry_phase_owns_eligibility_comparison_and_reroll():
    ineligible = resolve_parry(
        ParryContext(4, attacker_strength=6, defender_strength=3), ScriptedDice(())
    )
    rerolled = resolve_parry(
        ParryContext(4, 3, 3, reroll=True), ScriptedDice((4, 5))
    )
    starblade = resolve_parry(
        ParryContext(5, 3, 3, fixed_target=4), ScriptedDice((4,))
    )
    assert not ineligible.attempted
    assert rerolled.blocked and rerolled.rerolled
    assert starblade.blocked


@pytest.mark.parametrize("allowed", [False, True])
@pytest.mark.parametrize("roll", range(1, 7))
def test_parry_six_requires_explicit_exception(allowed, roll):
    result = resolve_parry(
        ParryContext(6, 3, 3, match_allowed=True, can_parry_six=allowed),
        ScriptedDice((roll,) if allowed else ()),
    )
    assert result.attempted is allowed
    assert result.blocked is (allowed and roll == 6)


@pytest.mark.parametrize("overrides", [
    {"available": False}, {"cannot_be_parried": True}, {"attacker_strength": 6},
])
def test_parry_six_exception_preserves_other_prohibitions(overrides):
    values = dict(hit_roll=6, attacker_strength=3, defender_strength=3,
                  match_allowed=True, can_parry_six=True, reroll=True)
    result = resolve_parry(ParryContext(**(values | overrides)), ScriptedDice(()))
    assert not result.attempted


def test_priority_and_attack_generation_are_directly_testable_phases():
    flags = fighter(main_weapon_id="weapon.double-handed-weapon")
    strong = fighter(
        main_weapon_id="weapon.double-handed-weapon",
        skill_ids=("skill.strongman",),
    )
    assert resolve_priority(PriorityContext(flags, fighter())).priority == -1
    assert resolve_priority(PriorityContext(strong, fighter())).priority == 0
    assert build_attacks(AttackPoolContext(fighter(), charging=False)).attacks == 1
    assert build_attacks(AttackPoolContext(fighter(off_hand_id="weapon.dagger"))).attacks == 2


@pytest.mark.parametrize("charging", [False, True])
def test_standing_up_preserves_only_explicit_always_strikes_first(charging):
    ordinary = fighter(main_weapon_id="weapon.mace")
    always_first = fighter(main_weapon_id="weapon.mace", skill_ids=("skill.always-strikes-first",))
    for actor, expected in ((ordinary, -1), (always_first, 1)):
        result = resolve_priority(PriorityContext(
            actor, ordinary, first_round=True, charging=charging, stood_up=True,
        ))
        assert result.priority == expected


def test_bear_hug_is_the_minimal_cross_phase_sequence_with_an_explicit_choice():
    context = BearHugContext(2, 4, 4)
    declined = resolve_bear_hug(context, ScriptedDice(()), AlwaysReject())
    assert declined.available and not declined.chosen
    distribution = exact_distribution(
        (6, 6),
        lambda rolls: resolve_bear_hug(context, ScriptedDice(rolls), AlwaysAccept()).wounded,
    )
    assert distribution == {False: Fraction(5, 12), True: Fraction(7, 12)}
    won = resolve_bear_hug(context, ScriptedDice((3, 3)), AlwaysAccept())
    assert won.wounded and not won.armour_allowed


def test_production_attack_orchestrator_aggregates_bear_hug_across_two_attacks():
    from mordheim_combat_lab.combat.vectorized import OUT
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import resolve_attacks

    attacker=replace(
        fighter(characteristics=Characteristics(3,4,3,1,3,2)),
        global_effects=EffectSet(bear_hug=True),
    )
    defender=fighter()
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    resolve_attacks(
        attacker,defender,np.array([0]),np.array([2]),np.array([False]),
        attacker_state,defender_state,VectorTape(6,6,3,4,1,5,5),False,AlwaysAccept(),
    )
    # Strength 4 + 3 ties Strength 3 + 4, so the Bear wins. The two normal
    # hits are replaced by one automatic wound and no armour roll is consumed.
    assert defender_state.condition.tolist()==[OUT]

    defender_state=_new_state(defender,1,np.random.default_rng(3))
    resolve_attacks(
        attacker,defender,np.array([0]),np.array([2]),np.array([False]),
        _new_state(attacker,1,np.random.default_rng(4)),defender_state,
        VectorTape(6,6,1,1),False,AlwaysReject(),
    )
    assert defender_state.wounds.tolist()==[1]


def test_attack_and_round_orchestrators_prove_phase_order_and_short_circuiting():
    strike = StrikeContext(
        hit=HitContext(3, 3),
        wound=WoundContext(3, 3),
        armour=ArmourContext(7),
    )
    result = resolve_attack(strike, ScriptedDice((6, 6, 5)))
    assert result.trace == (
        Phase.HIT,
        Phase.WOUND,
        Phase.ARMOUR,
        Phase.SPECIAL_SAVE,
        Phase.INJURY,
    )
    missed = resolve_attack(strike, ScriptedDice((1,)))
    assert missed.trace == (Phase.HIT,)
    round_result = resolve_strike_sequence(RoundContext(0, (strike,)), ScriptedDice((6, 6, 5)))
    assert round_result.state.trace == (
        Phase.DUEL_START,
        Phase.PRIORITY,
        Phase.ATTACKS,
        Phase.HIT,
        Phase.WOUND,
        Phase.ARMOUR,
        Phase.SPECIAL_SAVE,
        Phase.INJURY,
        Phase.AFTERMATH,
    )
    assert (round_result.state.attacks, round_result.state.hits, round_result.state.wounds) == (1, 1, 1)


def test_keyed_dice_replays_semantic_rolls_independently_of_request_order():
    first = KeyedDice(41)
    a = first.roll(RollRequest("round.0.hit"))
    b = first.roll(RollRequest("round.0.wound"))
    second = KeyedDice(41)
    assert second.roll(RollRequest("round.0.wound")) == b
    assert second.roll(RollRequest("round.0.hit")) == a
