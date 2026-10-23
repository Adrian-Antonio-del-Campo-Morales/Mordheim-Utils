"""Nemesis Crown Rune Use: item-local supplied effects, without pre-battle rolls."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def build(**options):
    return FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
                        main_weapon_id='weapon.axe', **options)


def inscribed(rune, slots, **options):
    return compile_fighter(build(condition_ids=(f'condition.rune-{rune}',),
        trait_overrides={f'rune_{rune}_slots': slots}, **options))


def tape(*rolls):
    return StrictDice([{'key': key, 'value': value} for key, value in rolls])


@pytest.mark.phase3_rules
@pytest.mark.parametrize('rune,hit,wound', [('striking', 3, 4), ('cleaving', 4, 3)])
def test_weapon_rune_changes_its_printed_hit_or_wound_boundary(rune, hit, wound):
    owner = inscribed(rune, ['main'], off_hand_id='weapon.mace')
    foe = compile_fighter(build())
    own = initialize_fighter(owner, tape(), 'a')
    enemy = initialize_fighter(foe, tape(), 'b')
    dice = tape(('r.hit', hit), ('r.wound', wound))
    result = resolve_reference_attack(owner, foe, own, enemy, owner.main_weapon, dice,
                                     key='r', decisions=StrictDecisions([]))
    dice.finish()
    assert result.wounded and result.damage == 1
    assert owner.off_hand.weapon_skill_bonus == owner.off_hand.strength_bonus == 0
    # An ordinary off-hand blow does not inherit the rune from the axe.
    dice = tape(('o.hit', 3)) if rune == 'striking' else tape(('o.hit', 4), ('o.wound', 3))
    other = resolve_reference_attack(owner, foe, own, enemy, owner.off_hand, dice,
                                    key='o', decisions=StrictDecisions([]))
    dice.finish()
    assert not other.wounded


@pytest.mark.phase3_rules
@pytest.mark.parametrize('rune,armour_roll,special_roll', [('stone', 4, None), ('iron', 1, 6)])
def test_armour_rune_changes_the_actual_save(rune, armour_roll, special_roll):
    owner = inscribed(rune, ['armour'], armour_id='armour.heavy-armour')
    foe = compile_fighter(replace(build(), main_weapon_id='weapon.mace'))
    rolls = [('r.hit', 4), ('r.wound', 4), ('r.armour', armour_roll)]
    if special_roll is not None:
        rolls.append(('r.special.ward', special_roll))
    dice = tape(*rolls)
    result = resolve_reference_attack(foe, owner,
        initialize_fighter(foe, tape(), 'a'), initialize_fighter(owner, tape(), 'b'),
        foe.main_weapon, dice, key='r', decisions=StrictDecisions([]))
    dice.finish()
    assert result.saved and result.defender.wounds == 2


@pytest.mark.phase4_modular
def test_fury_and_speed_reach_the_round_without_inscription_or_expiry_rolls():
    owner = compile_fighter(build(condition_ids=('condition.rune-fury', 'condition.rune-speed'),
        off_hand_id='weapon.mace',
        trait_overrides={'rune_fury_slots': ['main'], 'rune_speed_slots': ['off']}))
    foe = compile_fighter(build())
    # Separate weapons obey the one-rune-per-item bound. Their printed A/I
    # consequences survive the opponent's following player turn.
    state = initialize_duel(owner, foe, tape(), context=DuelContext(
        charging=(), active_participant='first'))
    for index in range(2):
        dice = tape(*[(f'round.{index}.first.attack.{attack}.hit', 1) for attack in range(3)],
                    (f'round.{index}.second.attack.0.hit', 1))
        result = resolve_round(owner, foe, state, dice)
        dice.finish()
        assert len(result.attacks) == 4
        state = result.state


@pytest.mark.phase2_construction
@pytest.mark.parametrize('conditions,facts,options,message', [
    (('condition.rune-fury', 'condition.rune-cleaving'),
     {'rune_fury_slots': ['main'], 'rune_cleaving_slots': ['main']}, {}, 'Only one Rune'),
    (('condition.rune-iron',), {'rune_iron_slots': ['main']}, {}, 'not eligible'),
    (('condition.rune-cleaving',), {'rune_cleaving_slots': ['off']}, {}, 'actual active'),
    (('condition.rune-fury',), {'rune_fury_slots': ['main', 'main']}, {}, 'distinct active'),
])
def test_source_rune_limits_reject_invalid_item_assignments(conditions, facts, options, message):
    with pytest.raises(ValueError, match=message):
        compile_fighter(build(condition_ids=conditions, trait_overrides=facts, **options))


@pytest.mark.phase2_construction
def test_two_durable_stone_runes_remain_on_two_distinct_physical_items():
    owner = inscribed('stone', ['armour', 'off'], armour_id='armour.light-armour',
                       off_hand_id='defence.shield')
    assert owner.armour_save == 3  # light6, shield5, two distinct +1 runes
    active = {item.slot: item for item in owner.mutation_equipment}
    assert active['armour'].effect.armour_save_bonus == 2
    assert active['off'].effect.armour_save_bonus == 2
