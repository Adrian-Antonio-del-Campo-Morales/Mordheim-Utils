"""Printed lasting injury results supplied to a duel, without campaign rolls."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def build(**options):
    return FighterBuild('mordheim', Characteristics(3, 3, 4, 2, 4, 1, leadership=7),
                        main_weapon_id='weapon.axe', **options)


@pytest.mark.rule_behavior
@pytest.mark.parametrize('condition,attribute,expected,rolls', [
    ('campaign.condition.hand-injury', 'weapon_skill', 0,
     [('round.0.second.attack.0.wound', 1), ('round.0.first.attack.0.hit', 1)]),
    ('campaign.condition.chest-wound', 'toughness', 3,
     [('round.0.second.attack.0.hit', 4), ('round.0.second.attack.0.wound', 4),
      ('round.0.first.attack.0.hit', 1)]),
])
def test_supplied_injury_changes_the_actual_hit_or_wound_boundary(condition, attribute, expected, rolls):
    original = build(condition_ids=(condition, condition))
    if attribute == 'weapon_skill':
        original = replace(original, characteristics=replace(original.characteristics, weapon_skill=1))
    injured = compile_fighter(original)
    opponent = compile_fighter(replace(build(), characteristics=Characteristics(3, 3, 3, 2, 3, 1, leadership=7)))
    initial_dice = StrictDice([])
    state = initialize_duel(injured, opponent, initial_dice,
        context=DuelContext(charging=('second',), active_participant='second'))
    initial_dice.finish()
    assert getattr(state.first, attribute) == expected
    dice = StrictDice([{'key': key, 'value': value} for key, value in rolls])
    decisions = StrictDecisions([])
    result = resolve_round(injured, opponent, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert result.attacks[0].hit
    assert result.attacks[0].wounded == (attribute == 'toughness')
    assert result.state.first.wounds == (1 if attribute == 'toughness' else 2)


@pytest.mark.rule_behavior
def test_nervous_condition_changes_round_order_without_a_fabricated_priority_tie():
    injured = compile_fighter(build(condition_ids=('campaign.condition.nervous-condition',)))
    opponent = compile_fighter(build())
    state = initialize_duel(injured, opponent, StrictDice([]),
        context=DuelContext(charging=(), active_participant='first'))
    dice = StrictDice([{'key': f'round.1.{side}.attack.0.hit', 'value': 1}
                       for side in ('second', 'first')])
    result = resolve_round(injured, opponent, replace(state, round_index=1), dice, StrictDecisions([]))
    dice.finish()
    assert result.state.first.initiative == 3


@pytest.mark.eligibility
def test_amputated_arm_limits_active_weapons_without_forbidding_holstered_ownership():
    supplied = build(condition_ids=('campaign.condition.amputated-arm',), owned_item_ids=('axe', 'sword'))
    assert 'weapon.axe' in compile_fighter(supplied).main_weapon.tags
    for restricted in (replace(supplied, off_hand_id='weapon.sword'),
                       replace(supplied, main_weapon_id='weapon.double-handed-weapon', owned_item_ids=None)):
        with pytest.raises(ValueError, match='weapon|hand|forbid'):
            compile_fighter(restricted)
