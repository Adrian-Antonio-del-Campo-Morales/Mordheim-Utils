"""Marauders' Inconsistency/Fate: supplied advances and penalty-free fists."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.state import initialize_fighter, require_characteristics
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def build(**options):
    return FighterBuild('mordheim', band_id='marauders-of-chaos', profile_id='condemned', **options)


@pytest.mark.parametrize('weapon', ['weapon.dagger', 'weapon.fist'])
@pytest.mark.phase3_rules
def test_variable_condemned_fights_without_unarmed_penalties_and_rolls_only_when_needed(weapon):
    fighter = compile_fighter(build(main_weapon_id=weapon))
    assert fighter.main_weapon.strength_bonus == 0
    assert fighter.main_weapon.attacks_bonus == 0
    assert {row[0] for row in fighter.random_characteristics} == {'WS', 'S', 'T', 'A'}
    dice = StrictDice([])
    state = initialize_fighter(fighter, dice, 'owner')
    dice.finish()
    dice = StrictDice([{'key': 'need.characteristic.A.0', 'sides': 3, 'value': 3}])
    state = require_characteristics(fighter, state, dice, 'need', {'A'})
    state = require_characteristics(fighter, state, dice, 'again', {'A'})
    dice.finish()
    assert state.attacks == 3 and state.random_rolled == frozenset({'A'})


@pytest.mark.phase2_construction
def test_partial_fixed_values_are_preserved_and_all_fixed_unlocks_equipment():
    supplied = Characteristics(5, 4, 3, 1, 4, 2, movement=4, leadership=7)
    partial = build(characteristics=supplied, trait_overrides={'condemned_fixed_characteristics': ['WS', 'S']})
    fighter = compile_fighter(partial)
    assert {row[0] for row in fighter.random_characteristics} == {'T', 'A'}
    dice = StrictDice([])
    state = require_characteristics(fighter, initialize_fighter(fighter, dice, 'owner'), dice, 'need', {'WS', 'S'})
    dice.finish()
    assert (state.weapon_skill, state.strength) == (5, 4)
    armed = compile_fighter(replace(partial, main_weapon_id='weapon.sword',
        trait_overrides={'condemned_fixed_characteristics': ['WS', 'S', 'T', 'A']}))
    assert not armed.random_characteristics and armed.main_weapon.parry


@pytest.mark.parametrize('options', [
    {'main_weapon_id': 'weapon.sword'},
    {'armour_id': 'armour.light-armour'},
    {'off_hand_id': 'defence.shield'},
    {'characteristics': Characteristics(5, 4, 3, 1, 4, 2), 'main_weapon_id': 'weapon.sword'},
])
@pytest.mark.phase2_construction
def test_variable_equipment_use_is_forbidden_even_with_manual_stat_values(options):
    with pytest.raises(ValueError, match='uses no equipment'):
        compile_fighter(build(**options))


@pytest.mark.phase2_construction
def test_permanent_results_require_declared_values_and_source_identity():
    with pytest.raises(ValueError, match='fixed characteristic values'):
        compile_fighter(build(trait_overrides={'condemned_fixed_characteristics': ['WS']}))
    with pytest.raises(ValueError, match='Only the Condemned'):
        compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 3, 1),
            trait_overrides={'condemned_fixed_characteristics': ['WS']}))
