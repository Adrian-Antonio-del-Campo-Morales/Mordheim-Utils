"""Canonical Black Guard equipment, single Mark choice and Augur's shared resource."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.psychology import resolve_fear
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

PRIEST = 'hireling.hired-sword.priest-of-morr-miracle-workers'
HAUNTED = PRIEST + '.skill.haunted-mien'
AUGUR = PRIEST + '.skill.augur'


def build(*marks, **options):
    return FighterBuild('mordheim', band_id='hirelings.hired-sword.2b', profile_id=PRIEST,
        special_rule_ids=marks, main_weapon_id=options.pop('main_weapon_id', 'weapon.dagger'), **options)


def tape(*rolls):
    return StrictDice([{'key': key, 'value': value} for key, value in rolls])


@pytest.mark.eligibility
def test_black_guard_offering_projection_and_compilation_share_the_selected_mark():
    selected = build(HAUNTED, main_weapon_id='weapon.sword', armour_id='armour.heavy-armour',
                     owned_item_ids=('sword', 'heavy_armour'))
    pack = next(pack for pack in combat_packages('mordheim') if pack.band['id'] == selected.band_id)
    profile = next(profile for profile in pack.profiles if profile['id'] == PRIEST)
    offered = desktop_call('catalogueEquipment', selected, package=pack, profile=profile)
    assert {'weapon.sword', 'armour.heavy-armour'} <= set(offered)
    facts = desktop_call('profileFacts', selected, package=pack, profile=profile)
    assert 'armour' not in facts['equipment_forbids']
    assert {'combat', 'strength'} <= set(facts['skill_access'])
    assert {'sword', 'heavy_armour'} <= {offer['item_id'] for offer in facts['equipment_access']}
    fighter = compile_fighter(selected)
    assert fighter.armour_save == 5 and 'weapon.sword' in fighter.main_weapon.tags


@pytest.mark.parametrize('marks', [(), (AUGUR,)])
@pytest.mark.eligibility
def test_priest_and_augur_keep_their_original_kit_strictures(marks):
    with pytest.raises(ValueError, match='printed kit|not available|forbidden'):
        compile_fighter(build(*marks, main_weapon_id='weapon.sword', armour_id='armour.heavy-armour'))


@pytest.mark.eligibility
def test_black_guard_does_not_grant_foreign_unique_equipment_or_missing_physical_copies():
    with pytest.raises(ValueError, match='ordinary human access|not available'):
        compile_fighter(build(HAUNTED, main_weapon_id='weapon.starsword', owned_item_ids=('starsword',)))
    with pytest.raises(ValueError, match='physical copies'):
        compile_fighter(build(HAUNTED, main_weapon_id='weapon.sword', off_hand_id='weapon.sword',
                              owned_item_ids=('sword',)))


# Primary: only one Mark is admitted. The Augur's compiled Strength and
# psychology immunity are the secondary guarantee of the admitted choice.
@pytest.mark.eligibility
def test_two_marks_are_refused_and_augur_reduces_strength_once():
    with pytest.raises(ValueError, match='only one Mark'):
        compile_fighter(build(AUGUR, HAUNTED))
    plain = compile_fighter(build())
    augur = compile_fighter(build(AUGUR))
    assert augur.characteristics.strength == plain.characteristics.strength - 1
    assert 'mechanic.psychology-immunity' in augur.global_effects.tags


@pytest.mark.rule_behavior
def test_black_guard_combat_and_strength_skills_reach_the_real_round():
    owner = compile_fighter(build(HAUNTED, main_weapon_id='weapon.sword', armour_id='armour.heavy-armour',
        skill_ids=('skill.expert-swordsman', 'skill.mighty-blow')))
    foe = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 4, 2, 2, 1, leadership=7),
        main_weapon_id='weapon.mace'))
    initial = initialize_duel(owner, foe, tape(), context=DuelContext(
        charging=('first',), active_participant='first'))
    dice = tape(('round.0.first.attack.0.hit', 1), ('round.0.first.attack.0.hit.reroll', 4),
                ('round.0.first.attack.0.wound', 4), ('round.0.second.attack.0.hit', 1))
    result = resolve_round(owner, foe, initial, dice, StrictDecisions([]))
    dice.finish()
    assert result.attacks[0].wounded and result.state.second.wounds == 1


@pytest.mark.rule_behavior
def test_augur_one_roll_resource_is_shared_across_attacks_and_not_reset():
    owner = compile_fighter(build(AUGUR))
    foe = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 2, 1), main_weapon_id='weapon.mace'))
    first, second = initialize_fighter(owner, tape(), 'a'), initialize_fighter(foe, tape(), 'b')
    dice = tape(('a.hit', 1), ('a.hit.reroll', 4), ('a.wound', 4))
    decisions = StrictDecisions([{'key': 'a.hit.one-roll-reroll', 'value': True}])
    result = resolve_reference_attack(owner, foe, first, second, owner.main_weapon, dice,
        key='a', decisions=decisions)
    dice.finish(); decisions.finish()
    assert 'one-roll-reroll' in result.attacker.resources_spent
    assert result.hit and not result.wounded  # S2 cannot wound T3 on 4.
    dice = tape(('b.hit', 1))
    second_attack = resolve_reference_attack(owner, foe, result.attacker, result.defender,
        owner.main_weapon, dice, key='b', decisions=StrictDecisions([]))
    dice.finish()
    assert not second_attack.hit


@pytest.mark.rule_behavior
def test_augur_psychology_immunity_skips_a_real_living_fear_causer_without_spending_reroll():
    augur, plain = compile_fighter(build(AUGUR)), compile_fighter(build())
    foe = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 2, 1),
        trait_overrides={'causes_fear': True, 'creature_kind': 'living'}))
    def start(owner):
        return initialize_duel(owner, foe, tape(), context=DuelContext(
            charging=('first',), active_participant='first'))
    immune = resolve_fear(augur, foe, start(augur), tape(), StrictDecisions([]))
    assert immune.engaged and not immune.failed_charges
    assert 'one-roll-reroll' not in immune.first.resources_spent
    dice = tape(('round.0.first.fear.charge.0', 6), ('round.0.first.fear.charge.1', 6))
    frightened = resolve_fear(plain, foe, start(plain), dice, StrictDecisions([]))
    dice.finish()
    assert not frightened.engaged and 'first' in frightened.failed_charges
