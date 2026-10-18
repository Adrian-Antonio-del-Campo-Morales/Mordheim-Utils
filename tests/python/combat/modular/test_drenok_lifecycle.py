"""TC15 printed p27: source-specific Berserker, Icefang and worn hide."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import _combined_effect, prepare_armour_context
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.phases import Condition
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

PID = 'hireling.dramatis.drenok-johansen-wielder-of-the-great-axe'


def tape(*rolls):
    return StrictDice([{'key': key, 'value': value} for key, value in rolls])


def drenok(**options):
    return compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b',
        profile_id=PID, defence_ids=('defence.sabertooth-hide',), **options))


def enemy(*, strength=3, wounds=3):
    return compile_fighter(FighterBuild('mordheim', Characteristics(6, strength, 3, wounds, 3, 1, leadership=7),
        main_weapon_id='weapon.mace'))


def state(fighter):
    return initialize_fighter(fighter, tape(), 'init')


def test_printed_unique_kit_uses_its_own_defaults_and_no_slayer_berserker():
    owner = drenok()
    assert 'weapon.icefang-axe' in owner.main_weapon.tags
    assert owner.main_weapon.two_handed and owner.main_weapon.parry
    assert owner.characteristics.strength == 4 and owner.main_weapon.strength_bonus == 2
    assert owner.main_weapon.injury_modifier == 1 and owner.armour_save == 6
    assert 'mechanic.drenok-berserker' in owner.global_effects.tags
    assert 'skill.berserker' not in owner.global_effects.tags
    dice = tape(('a.hit', 3))
    result = resolve_reference_attack(owner, enemy(), state(owner), state(enemy()), owner.main_weapon,
        dice, key='a', first_round=True, charging=True, decisions=StrictDecisions([]))
    dice.finish()
    assert not result.hit  # equal WS still needs 4; no Slayer charging +1.


def test_icefang_parry_and_injury_bonus_reach_actual_attacks():
    owner, foe = drenok(), enemy(wounds=1)
    dice = tape(('a.hit', 4), ('a.wound', 4), ('a.injury.0', 4))
    result = resolve_reference_attack(owner, foe, state(owner), state(foe), owner.main_weapon,
        dice, key='a', decisions=StrictDecisions([]))
    dice.finish()
    assert result.defender.condition == Condition.OUT  # injury 4 +1 -> 5
    dice = tape(('b.hit', 4), ('b.parry', 5))
    result = resolve_reference_attack(foe, owner, state(foe), state(owner), foe.main_weapon,
        dice, key='b', decisions=StrictDecisions([]))
    dice.finish()
    assert result.parried


def test_hide_six_saves_before_step_aside_and_does_not_supply_the_missile_face():
    owner, foe = drenok(), enemy()
    dice = tape(('a.hit', 4), ('a.parry', 1), ('a.wound', 5), ('a.armour', 6))
    result = resolve_reference_attack(foe, owner, state(foe), state(owner), foe.main_weapon,
        dice, key='a', decisions=StrictDecisions([]))
    dice.finish()
    assert result.saved
    context = prepare_armour_context(foe, owner, state(foe), state(owner), foe.main_weapon,
        _combined_effect(foe, foe.main_weapon), melee_attack=False)
    assert context.armour_save == 7  # no invented use of the excluded 5+ face


@pytest.mark.parametrize('roll,fighting', [(3, False), (4, True)])
def test_last_wound_uses_its_four_plus_instead_of_injury_without_restoring_health(roll, fighting):
    owner, foe = drenok(), enemy(strength=8)
    current = replace(state(owner), wounds=1)
    dice = tape(('a.hit', 4), ('a.wound', 4), ('a.special.ward', 4), ('a.drenok-berserker', roll))
    result = resolve_reference_attack(foe, owner, state(foe), current, foe.main_weapon,
        dice, key='a', decisions=StrictDecisions([]))
    dice.finish()
    assert result.defender.wounds == 0
    assert result.defender.active == fighting and result.defender.drenok_fighting == fighting
    assert result.defender.condition == (Condition.STANDING if fighting else Condition.OUT)
    assert result.wounded and not result.saved


def test_additional_wound_in_the_same_turn_does_not_repeat_or_roll_an_injury():
    owner, foe = drenok(), enemy(strength=8)
    current = replace(state(owner), wounds=0, drenok_fighting=True)
    dice = tape(('b.hit', 4), ('b.wound', 4), ('b.special.ward', 4))
    result = resolve_reference_attack(foe, owner, state(foe), current, foe.main_weapon,
        dice, key='b', decisions=StrictDecisions([]))
    dice.finish()
    assert result.defender.active and result.defender.wounds == 0


def test_zero_wound_drenok_fights_then_renews_in_both_player_turns_and_failure_ends_duel():
    owner, foe = drenok(), enemy()
    initial = initialize_duel(owner, foe, tape(), context=DuelContext(
        charging=(), active_participant='first'))
    initial = replace(initial, first=replace(initial.first, wounds=0, drenok_fighting=True), round_index=1)
    assert not initial.first_player_turn
    dice = tape(('round.1.first.drenok-berserker', 4),
        ('round.1.first.attack.0.hit', 4), ('round.1.first.attack.1.hit', 1),
        ('round.1.first.attack.0.wound', 4), ('round.1.second.attack.0.hit', 1))
    result = resolve_round(owner, foe, initial, dice, StrictDecisions([]))
    dice.finish()
    assert result.state.first.active and result.state.first.wounds == 0
    assert result.state.second.wounds == 2 and result.attacks[0].wounded
    dice = tape(('round.2.first.drenok-berserker', 3))
    ended = resolve_round(owner, foe, result.state, dice, StrictDecisions([]))
    dice.finish()
    assert not ended.state.first.active and ended.state.second.active
    assert not ended.attacks
