"""Printed recipient effects, physical equipment loss and existing potion lifecycle."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import _parry_context
from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.conditions import resolve_supplied_conditions
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def hero(*conditions, **options):
    return compile_fighter(FighterBuild('mordheim', Characteristics(4, 3, 3, 2, 4, 1, leadership=8),
        band_id='mercenaries', profile_id='mercenary-captain', main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'),
        condition_ids=conditions, **options))


def tape(*rolls):
    return StrictDice([{'key': key, 'value': value} for key, value in rolls])


@pytest.mark.rule_behavior
@pytest.mark.parametrize('result,options,save', [
    (2, {'armour_id': 'armour.heavy-armour'}, 4),
    (2, {'armour_id': 'armour.light-armour'}, 5),
    (3, {'defence_ids': ('defence.helmet',)}, 6),
    (4, {'off_hand_id': 'defence.buckler'}, 6),
])
def test_maintenance_save_reaches_an_actual_attack(result, options, save):
    owner = hero(f'condition.maintenance-{result}', **options)
    enemy = hero()
    assert owner.armour_save == save
    if result == 3:
        assert owner.helmet_save == 4  # +1 armour, not a second injury-reaction modifier.
    dice = tape(('r.hit', 4), ('r.wound', 4), ('r.armour', save))
    defender_state = replace(initialize_fighter(owner, tape(), 'd'), parries_remaining=0)
    outcome = resolve_reference_attack(enemy, owner, initialize_fighter(enemy, tape(), 'a'),
        defender_state, enemy.main_weapon, dice, key='r', decisions=StrictDecisions([]))
    dice.finish()
    assert outcome.saved and outcome.defender.wounds == 2


@pytest.mark.rule_behavior
@pytest.mark.parametrize('main,rolls', [
    ('weapon.mace', [('r.hit', 4), ('r.parry', 5)]),
    ('weapon.sword', [('r.hit', 4), ('r.parry', 3), ('r.parry.reroll', 5)]),
])
def test_improved_shield_parries_like_buckler_including_sword_composition(main, rolls):
    owner = hero('condition.maintenance-5', main_weapon_id=main, off_hand_id='defence.shield')
    enemy = hero()
    dice = tape(*rolls)
    result = resolve_reference_attack(enemy, owner, initialize_fighter(enemy, tape(), 'a'),
        initialize_fighter(owner, tape(), 'd'), enemy.main_weapon, dice, key='r', decisions=StrictDecisions([]))
    dice.finish()
    assert result.parried
    assert owner.armour_save == 6


@pytest.mark.rule_behavior
@pytest.mark.parametrize('condition,off,bonus', [
    ('condition.maintenance-4', 'defence.buckler', 1),
    ('condition.maintenance-5', 'defence.shield', 1),
])
def test_broken_improved_piece_loses_save_identity_and_parry(condition, off, bonus):
    owner = hero(condition, off_hand_id=off)
    current = replace(initialize_fighter(owner, tape(), 'd'), broken_hands=frozenset({'off'}))
    effective = equipment_for_state(owner, current, first_round=True)
    assert effective.armour_save == owner.armour_save + bonus == 7
    assert 'defence.buckler' not in effective.global_effects.tags
    assert _parry_context(effective, current, hero().main_weapon, 3, 4, 'r') is None
    # Projection is safe to compose with itself; no second subtraction.
    assert equipment_for_state(effective, current, first_round=True) == effective


@pytest.mark.interaction
def test_rune_and_maintenance_stay_on_one_physical_shield_and_leave_together():
    owner = hero('condition.maintenance-5', 'condition.rune-stone',
                 off_hand_id='defence.shield', trait_overrides={'rune_stone_slots': ['off']})
    assert owner.armour_save == 5
    current = replace(initialize_fighter(owner, tape(), 'd'), broken_hands=frozenset({'off'}))
    effective = equipment_for_state(owner, current, first_round=True)
    assert effective.armour_save == 7
    assert effective.shield_and_skill_effects.armour_save_bonus == 0
    assert not effective.global_effects.parry
    discarded = equipment_for_state(owner, replace(current, equipment_cast_off=True), first_round=True)
    assert discarded.armour_save == 7 and discarded.helmet_save == 7


@pytest.mark.rule_behavior
@pytest.mark.parametrize('result', [1, 2, 3, 4, 5, 6])
def test_first_result_stands_without_relevant_equipment(result):
    owner = hero(f'condition.maintenance-{result}')
    assert owner.armour_save == 7 and not owner.global_effects.parry
    initialize_fighter(owner, tape(), 'd')  # no invented table roll or reroll


@pytest.mark.eligibility
def test_recipient_and_one_table_result_are_enforced():
    with pytest.raises(ValueError, match='only one supplied result'):
        hero('condition.maintenance-2', 'condition.maintenance-3')
    for condition in ('condition.maintenance-2', 'condition.witch-strength'):
        with pytest.raises(ValueError, match='Hero'):
            compile_fighter(FighterBuild('mordheim', band_id='mercenaries', profile_id='warriors',
                main_weapon_id='weapon.mace', condition_ids=(condition,)))


@pytest.mark.rule_behavior
@pytest.mark.parametrize('suffix,stat,value,expiry', [
    ('debilitating', 'toughness', 2, 6), ('strength', 'strength', 4, 1),
    ('resilience', 'toughness', 4, 1),
])
def test_witch_draught_uses_the_existing_operator_and_own_recovery(suffix, stat, value, expiry):
    owner = hero(f'condition.witch-{suffix}')
    enemy = hero()
    state = initialize_duel(owner, enemy, tape(), context=DuelContext(charging=('first',), active_participant='first'))
    assert getattr(state.first, stat) == value
    def play(current, rolls):
        dice = tape(*rolls)
        result = resolve_round(owner, enemy, current, dice, StrictDecisions([]))
        dice.finish()
        return result.state
    stays = 5 if expiry == 6 else 2
    state = play(state, [(f'round.0.first.petru-{suffix}', stays),
                        ('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])
    assert getattr(state.first, stat) == value
    # Enemy recovery consumes no expiry die for this recipient.
    state = play(state, [('round.1.priority-tie', 4),
                        ('round.1.first.attack.0.hit', 1), ('round.1.second.attack.0.hit', 1)])
    state = play(state, [(f'round.2.first.petru-{suffix}', expiry), ('round.2.priority-tie', 4),
                        ('round.2.first.attack.0.hit', 1), ('round.2.second.attack.0.hit', 1)])
    assert getattr(state.first, stat) == 3
    assert f'condition.petru-{suffix}' in state.first.resources_spent



@pytest.mark.compilation
def test_witch_fortitude_and_alias_deduplication():
    owner = hero('condition.witch-fortitude', 'condition.petru-fortitude')
    assert initialize_fighter(owner, tape(), 'a').wounds == 3
    supplied = resolve_supplied_conditions(('condition.witch-fortitude', 'condition.petru-fortitude'))
    assert supplied.mechanic_ids == ('condition.petru-fortitude',)
    with pytest.raises(ValueError, match='only one supplied result'):
        hero('condition.witch-strength', 'condition.petru-resilience')


@pytest.mark.eligibility
@pytest.mark.parametrize("condition", ['condition.maintenance-2', 'condition.witch-strength'])
def test_supplied_custom_hero_uses_the_shared_recipient_identity(condition):
    fighter = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1),
        armour_id='armour.heavy-armour', condition_ids=(condition,),
        trait_overrides={'fighter_kind': 'hero'}))
    if condition == 'condition.maintenance-2':
        assert fighter.armour_save == 4
    else:
        assert initialize_fighter(fighter, tape(), 'a').strength == 4
