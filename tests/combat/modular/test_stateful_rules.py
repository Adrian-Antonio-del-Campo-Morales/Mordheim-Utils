"""Secuencias con estado del motor modular."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.combat.modular.aftermath import _black_hunger
from mordheim_combat_lab.combat.modular.aftermath import _fire_recovery
from mordheim_combat_lab.combat.modular.aftermath import _force_of_will
from mordheim_combat_lab.combat.modular.aftermath import _netter
from mordheim_combat_lab.combat.modular.aftermath import _react_to_wound
from mordheim_combat_lab.combat.modular.aftermath import _spines
from mordheim_combat_lab.combat.modular.pools import _resolve_attack_pool
from mordheim_combat_lab.combat.modular.attacks import resolve_reference_attack
from mordheim_combat_lab.combat.modular.rounds import resolve_round
from mordheim_combat_lab.combat.modular.state import DuelState
from mordheim_combat_lab.combat.modular.state import initialize_fighter
from mordheim_combat_lab.combat.phases import Condition
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.dice import AlwaysAccept
from mordheim_combat_lab.domain.dice import RollRequest
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import EffectSet
from mordheim_combat_lab.domain.models import FighterBuild


class ConstantDice:
    def __init__(self, value):
        self.value = value

    def roll(self, request: RollRequest):
        return min(self.value, request.sides)


class TapeDice:
    def __init__(self, *values):
        self.values = iter(values)

    def roll(self, request: RollRequest):
        value = next(self.values)
        assert 1 <= value <= request.sides
        return value


def fighter(*, ws=3, strength=3, toughness=3, wounds=1, initiative=3, attacks=1):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(ws, strength, toughness, wounds, initiative, attacks),
    ))


def states(attacker, defender):
    return (
        initialize_fighter(attacker, ConstantDice(1), "attacker"),
        initialize_fighter(defender, ConstantDice(1), "defender"),
    )


def test_reference_luck_and_mark_are_persistent_consumable_resources():
    ordinary = fighter()
    lucky = replace(ordinary, global_effects=EffectSet(tags=("skill.luck",)))
    marked = replace(ordinary, global_effects=EffectSet(tags=("mechanic.mark-of-the-old-ones",)))
    target = fighter()
    a, d = states(lucky, target)
    luck = resolve_reference_attack(lucky, target, a, d, lucky.main_weapon, ConstantDice(1), key="luck")
    assert "luck" in luck.attacker.resources_spent
    a, d = states(marked, target)
    mark = resolve_reference_attack(marked, target, a, d, marked.main_weapon, ConstantDice(1), key="mark")
    assert mark.hit and "mark-of-the-old-ones" in mark.attacker.resources_spent


def test_reference_parry_and_critical_capacity_are_consumed_in_state():
    attacker = fighter(ws=6, strength=4)
    defender = fighter(wounds=3)
    defender = replace(defender, global_effects=EffectSet(parry=True))
    a, d = states(attacker, defender)
    parried = resolve_reference_attack(
        attacker, defender, a, d, attacker.main_weapon,
        TapeDice(4, 5), key="parry",
    )
    assert parried.parried and parried.defender.parries_remaining == 0

    plain = fighter(wounds=3)
    a, d = states(attacker, plain)
    critical = resolve_reference_attack(
        attacker, plain, a, d, attacker.main_weapon,
        TapeDice(6, 6, 6), key="critical",
    )
    assert not critical.attacker.critical_available


def test_attack_pool_parries_the_highest_hit_roll_not_the_first_hit():
    attacker = fighter(ws=6, attacks=2)
    defender = replace(
        fighter(wounds=3), global_effects=EffectSet(parry=True)
    )
    a, d = states(attacker, defender)
    _, final_defender, outcomes = _resolve_attack_pool(
        attacker, defender, a, d, 2, TapeDice(3, 5, 4, 1, 1),
        key="highest-parry", first_round=False, charging=False,
        decisions=AlwaysAccept(),
    )
    assert [outcome.hit_roll for outcome in outcomes] == [3, 5]
    assert not any(outcome.parried for outcome in outcomes)
    assert final_defender.parries_remaining == 0


def test_lucky_charm_save_releases_parry_for_next_highest_hit():
    attacker = fighter(ws=6, attacks=2)
    defender = replace(
        fighter(wounds=3),
        global_effects=EffectSet(parry=True, tags=("defence.lucky-charm",)),
    )
    a, d = states(attacker, defender)
    _, final_defender, outcomes = _resolve_attack_pool(
        attacker, defender, a, d, 2, TapeDice(5, 4, 6, 5),
        key="charm-then-parry", first_round=False, charging=False,
        decisions=AlwaysAccept(),
    )
    assert outcomes[0].saved
    assert outcomes[1].parried
    assert final_defender.parries_remaining == 0


def test_reference_force_of_will_rescues_once_and_sustains_per_round():
    base = fighter(toughness=3)
    force = replace(base, global_effects=EffectSet(tags=("mechanic.force-of-will",)))
    state = replace(initialize_fighter(force, ConstantDice(1), "force"), condition=Condition.OUT)
    rescued = _force_of_will(force, state, ConstantDice(1), "force.rescue")
    assert rescued.condition == Condition.STANDING and rescued.force_of_will_active
    failed = _force_of_will(force, rescued, ConstantDice(6), "force.sustain", sustain=True)
    assert failed.condition == Condition.OUT
    assert _force_of_will(force, failed, ConstantDice(1), "force.again").condition == Condition.OUT


def test_reference_netter_covers_miss_escape_and_capture():
    base = fighter(strength=3)
    netter = replace(base, global_effects=EffectSet(tags=("mechanic.netter",)), ballistic_skill=3)
    n, target = states(netter, base)
    assert _netter(netter, base, n, target, TapeDice(1), "net.miss").condition == Condition.STANDING
    assert _netter(netter, base, n, target, TapeDice(6, 1), "net.escape").condition == Condition.STANDING
    assert _netter(netter, base, n, target, TapeDice(6, 6), "net.catch").condition == Condition.KNOCKED_DOWN


def test_reference_fire_persists_until_recovery_succeeds():
    victim, opponent = fighter(wounds=2), fighter()
    v, o = states(victim, opponent)
    v = replace(v, on_fire=True)
    burning, o, _ = _fire_recovery(victim, opponent, v, o, ConstantDice(1), "fire.fail")
    assert burning.on_fire
    extinguished, _, _ = _fire_recovery(victim, opponent, burning, o, ConstantDice(6), "fire.pass")
    assert not extinguished.on_fire


def test_reference_spines_acid_blood_and_contagious_are_real_reactions():
    ordinary = fighter(wounds=2)
    spined = replace(ordinary, global_effects=EffectSet(tags=("spines",)))
    s, t = states(spined, ordinary)
    _, _, spines = _spines(spined, ordinary, s, t, ConstantDice(6), "spines")
    assert spines and spines[0].hit

    acid = replace(fighter(), global_effects=EffectSet(tags=("acid_blood",)))
    attacker = fighter(ws=6, strength=6, wounds=2)
    a, d = states(attacker, acid)
    outcome = resolve_reference_attack(
        attacker, acid, a, d, attacker.main_weapon,
        ConstantDice(6), key="acid-trigger",
    )
    reacted = _react_to_wound(attacker, acid, outcome, ConstantDice(6), "acid-trigger")
    assert outcome.damage == 1 and reacted.attacker.wounds == 1

    contagious = replace(fighter(), global_effects=EffectSet(tags=("contagious",)))
    a, d = states(attacker, contagious)
    outcome = resolve_reference_attack(
        attacker, contagious, a, d, attacker.main_weapon,
        ConstantDice(6), key="contagious-trigger",
    )
    reacted = _react_to_wound(attacker, contagious, outcome, ConstantDice(6), "contagious-trigger")
    assert outcome.defender.condition == Condition.OUT and reacted.attacker.wounds == 1


def test_reference_spines_are_simultaneous_even_when_both_hits_are_lethal():
    base = fighter()
    spined = replace(base, global_effects=EffectSet(tags=("spines",)))
    state = DuelState(*states(spined, spined), first_charged=True)
    result = resolve_round(spined, spined, state, ConstantDice(6))
    assert result.state.first.condition == Condition.OUT
    assert result.state.second.condition == Condition.OUT


def test_reference_black_hunger_resolves_d3_self_hits():
    base = fighter(wounds=2)
    hungry = replace(base, global_effects=EffectSet(tags=("mechanic.black-hunger",)))
    state = initialize_fighter(hungry, ConstantDice(1), "hungry")
    state, outcomes = _black_hunger(hungry, state, ConstantDice(6), "hunger")
    assert len(outcomes) <= 3
    assert outcomes


def test_reference_bear_hug_replaces_two_hits_before_wound_resolution():
    bear = compile_fighter(FighterBuild(
        "mordheim", band_id="kislevites", profile_id="trained-bear",
    ))
    target = fighter()
    b, t = states(bear, target)
    b, t, outcomes = _resolve_attack_pool(
        bear, target, b, t, 2,
        TapeDice(6, 6, 3, 3, 5),
        key="bear", first_round=False, charging=False,
        decisions=AlwaysAccept(),
    )
    assert len(outcomes) == 1
    assert outcomes[0].wounded
    assert t.condition == Condition.OUT


def test_reference_disability_is_applied_during_scalar_initialization():
    base = fighter(toughness=4)
    disabled = replace(base, global_effects=EffectSet(tags=("mechanic.disability",)))
    state = initialize_fighter(disabled, TapeDice(4), "disabled")
    assert state.toughness == 3
    assert "disability.4" in state.resources_spent
