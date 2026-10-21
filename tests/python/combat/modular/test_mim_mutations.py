"""MiM 159–164: current-body consequences, physical gear and no campaign proxy."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.contexts import OwnedRollDice, _attack_strength, _combined_effect, weapon_against_opponent
from mordheim_combat.modular.pools import electrical_touch_weapon
from mordheim_combat.modular.mutations import apply_brand, fighter_for_mutations, select_mutation_tail
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import has_tag, Condition
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, EffectSet, FighterBuild, CarriedEquipment

pytestmark = pytest.mark.phase3_rules


@pytest.fixture(scope='module')
def chart():
    priest = compile_fighter(FighterBuild('mordheim', band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.priest-of-verena', variant_ids=('deity.solkan',),
        special_rule_ids=('hireling.hired-sword.priest-of-verena.skill.inquisitor',)))
    assert {option.roll for option in priest.mutation_options} == {10*t+u for t in range(1,7) for u in range(1,7)}
    return {option.roll: option for option in priest.mutation_options}


@pytest.fixture(scope='module')
def human():
    return compile_fighter(FighterBuild('mordheim', Characteristics(3,3,3,3,4,2,movement=5,leadership=7),
        main_weapon_id='weapon.sword', off_hand_id='weapon.mace', armour_id='armour.light-armour',
        defence_ids=('defence.helmet',)))


class Choices:
    def __init__(self, *yes): self.yes, self.requests = set(yes), []
    def choose(self, key, context=None):
        self.requests.append(key)
        return key in self.yes


def initial(fighter):
    dice = StrictDice([])
    result = initialize_fighter(fighter, dice, 'init')
    dice.finish()
    return result


def brand(fighter, current, option, rolls=(), decisions=None):
    dice = StrictDice([{'key': 'brand.'+key, 'value': value} for key, value in rolls])
    result = apply_brand(fighter, current, option, dice, decisions, 'brand')
    dice.finish()
    return result


def test_stat_mutations_preserve_temporary_losses_and_crystal_locks_only_subsequent_mutation(chart, human):
    current = replace(initial(human), strength=2)
    current = brand(human, current, chart[64])
    assert current.strength == 4
    assert fighter_for_mutations(human,current).characteristics.leadership == 3
    current = brand(human, current, chart[63])
    assert (current.toughness,current.wounds) == (6,1)
    current = brand(human,current,chart[24])
    current = brand(human,current,chart[12])
    view = fighter_for_mutations(human,current)
    assert (view.characteristics.toughness,view.characteristics.wounds) == (6,1)
    # Actual current-turn effects are retained rather than resetting to T6.
    assert replace(current,toughness=5).toughness == 5
    assert view.characteristics.movement == 4


def test_halving_rounds_up_and_never_simulates_retirement(chart,human):
    current = brand(human,initial(human),chart[12])
    assert current.toughness == 2
    current = brand(human,current,chart[66], [('atrophy',5)])
    assert fighter_for_mutations(human,current).characteristics.movement == 3
    current = brand(human,current,chart[66], [('atrophy',6)])
    assert fighter_for_mutations(human,current).characteristics.movement == 0
    assert current.condition == Condition.STANDING


def test_head_atrophy_gains_stupidity_not_a_fictitious_injury(chart,human):
    current = brand(human, initial(human), chart[66], [('atrophy',1)])
    view = fighter_for_mutations(human,current)
    assert has_tag(view.global_effects,'mechanic.stupidity')
    assert current.wounds == 3 and current.condition == Condition.STANDING


def test_claw_stows_only_selected_weapon_and_retains_shield_permission(chart,human):
    shield = EffectSet(tags=('defence.shield',),armour_save_bonus=1)
    unit = replace(human,off_hand=shield,off_hand_attacks=False,mutation_equipment=(
        human.mutation_equipment[0], CarriedEquipment('shield',shield,'defence','off')))
    current = brand(unit,initial(unit),chart[25],decisions=Choices('brand.hand.off'))
    view = fighter_for_mutations(unit,current)
    assert has_tag(view.off_hand,'defence.shield')
    assert has_tag(view.main_weapon,'weapon.sword')
    assert len(view.extra_attacks) == 1 and view.extra_attacks[0].strength_bonus == 1
    assert has_tag(view.extra_attacks[0],'mutation.hand.off')


def test_tentacle_does_not_invent_an_equipment_prohibition(chart,human):
    current = brand(human,initial(human),chart[33])
    view = fighter_for_mutations(human,current)
    assert view.main_weapon == human.main_weapon and view.off_hand == human.off_hand
    assert view.global_effects.incoming_attacks_modifier == -1


@pytest.mark.parametrize('face,tag',[(1,'weapon.sword'),(2,'weapon.mace'),(3,'weapon.mace'),
    (4,'weapon.axe'),(5,'weapon.axe'),(6,'weapon.flail')])
def test_bone_weapon_uses_its_actual_subroll_and_replaces_only_the_selected_hand(chart,human,face,tag):
    current = brand(human,initial(human),chart[65],[('limb',face)],Choices('brand.hand.main'))
    view = fighter_for_mutations(human,current)
    assert has_tag(view.main_weapon,tag) and not view.main_weapon.two_handed
    assert has_tag(view.off_hand,'weapon.mace')
    assert len(current.mutation_equipment) == len(human.mutation_equipment)
    assert current.mutation_equipment[0].slot is None
    assert view.helmet_save == 4


def test_second_bone_weapon_prevents_other_hand_equipment_but_keeps_helmet(chart,human):
    current = brand(human,initial(human),chart[65],[('limb',1)])
    current = brand(human,current,chart[65],[('limb',5)])
    view = fighter_for_mutations(human,current)
    assert has_tag(view.main_weapon,'weapon.sword') and has_tag(view.off_hand,'weapon.axe')
    assert view.helmet_save == 4
    assert all(item.slot not in ('main','off') for item in current.mutation_equipment)


def test_atrophy_promotes_the_surviving_real_hand_and_removes_that_claw_only(chart,human):
    current = brand(human,initial(human),chart[25],decisions=Choices('brand.hand.main'))
    current = brand(human,current,chart[66],[('atrophy',2)],Choices('brand.hand.main'))
    view = fighter_for_mutations(human,current)
    assert has_tag(view.main_weapon,'weapon.mace') and view.main_hand_slot == 'off'
    assert view.extra_attacks == ()
    current = brand(human,current,chart[66],[('atrophy',4)])
    assert has_tag(fighter_for_mutations(human,current).global_effects,'condition.mim-no-hand-attacks')
    assert current.condition == Condition.STANDING


def test_extra_arm_does_not_create_weapon_and_can_equip_one_real_stowed_copy(chart,human):
    axe = EffectSet(tags=('weapon.axe',),armour_penetration=1)
    unit = replace(human,mutation_equipment=(*human.mutation_equipment,CarriedEquipment('axe',axe,'weapon')))
    empty = brand(unit,initial(unit),chart[41])
    assert fighter_for_mutations(unit,empty).extra_attacks == ()
    equipped = brand(unit,initial(unit),chart[41],decisions=Choices(f'brand.equip.{len(human.mutation_equipment)}'))
    view = fighter_for_mutations(unit,equipped)
    assert len(view.extra_attacks) == 1 and has_tag(view.extra_attacks[0],'weapon.axe')
    assert sum(item.item_id == 'axe' for item in equipped.mutation_equipment) == 1


def test_extra_arm_moves_one_existing_poisoned_copy_with_its_own_clean_snapshot(chart,human):
    unit = compile_fighter(FighterBuild('mordheim',human.characteristics,
        main_weapon_id='weapon.sword',off_hand_id='weapon.sword',
        main_poison_id='poison.black-lotus',off_poison_id='poison.black-venom'))
    current = brand(unit,initial(unit),chart[41],decisions=Choices('brand.equip.1'))
    view = fighter_for_mutations(unit,current)
    assert len(view.extra_attacks) == 1
    extra = view.extra_attacks[0]
    assert has_tag(extra,'poison.black-venom') and not has_tag(extra,'poison.black-lotus')
    immune = replace(human,global_effects=EffectSet(poison_immunity=True))
    clean = weapon_against_opponent(view,immune,extra)
    assert not has_tag(clean,'poison.black-venom') and clean.strength_bonus == 0
    assert sum(item.slot is not None and item.kind == 'weapon' for item in current.mutation_equipment) == 2


def test_equipped_tail_shield_excludes_the_other_tail_only_when_chosen(chart,human):
    shield = EffectSet(tags=('defence.shield',),armour_save_bonus=1)
    unit = replace(human,mutation_equipment=(*human.mutation_equipment,
        CarriedEquipment('shield',shield,'defence')))
    current = brand(unit,initial(unit),chart[36])
    current = brand(unit,current,chart[44],decisions=Choices(f'brand.equip.{len(human.mutation_equipment)}'))
    other_tail = select_mutation_tail(unit,current,None,'phase')
    assert len(fighter_for_mutations(unit,other_tail).extra_attacks) == 1
    assert fighter_for_mutations(unit,other_tail).armour_save == 6
    shield_tail = select_mutation_tail(unit,current,Choices('phase.tail.1'),'phase')
    view = fighter_for_mutations(unit,shield_tail)
    assert view.extra_attacks == () and view.armour_save == 5


def test_extra_arm_does_not_turn_an_unsupported_bow_into_a_melee_attack(chart,human):
    unit = replace(human,mutation_equipment=(*human.mutation_equipment,CarriedEquipment('bow',EffectSet(),'weapon')))
    choices = Choices(f'brand.equip.{len(human.mutation_equipment)}')
    current = brand(unit,initial(unit),chart[41],decisions=choices)
    assert fighter_for_mutations(unit,current).extra_attacks == ()
    assert f'brand.equip.{len(human.mutation_equipment)}' not in choices.requests


def test_possessed_extra_arm_is_unarmed_and_cannot_equip_a_weapon(chart,human):
    unit = replace(human,global_effects=replace(human.global_effects,tags=(*human.global_effects.tags,'nature.possessed')))
    current = brand(unit,initial(unit),chart[41])
    assert len(fighter_for_mutations(unit,current).extra_attacks) == 1
    assert has_tag(fighter_for_mutations(unit,current).extra_attacks[0],'weapon.natural-attacks')


def test_poison_bite_upgrades_existing_bite_without_creating_a_second_one(chart,human):
    current = brand(human,initial(human),chart[52])
    current = brand(human,current,chart[55])
    current = brand(human,current,chart[42])
    view = fighter_for_mutations(human,current)
    assert len(view.extra_attacks) == 1
    bite = view.extra_attacks[0]
    assert has_tag(bite,'rule.strikes-last-bite') and has_tag(bite,'rule.poisonous-bite')
    immune = replace(human,global_effects=EffectSet(poison_immunity=True))
    assert _attack_strength(view,human,current,bite,_combined_effect(view,bite),True,True)[0] == 5
    assert _attack_strength(view,immune,current,bite,_combined_effect(view,bite),True,True)[0] == 2


def test_spiked_tail_is_an_alternative_not_a_second_simultaneous_tail(chart,human):
    current = brand(human,initial(human),chart[36])
    current = brand(human,current,chart[54])
    current = select_mutation_tail(human,current,Choices('phase.tail.1'),'phase')
    tails = fighter_for_mutations(human,current).extra_attacks
    assert len(tails) == 1 and has_tag(tails[0],'rule.spiked-tail')
    current = select_mutation_tail(human,current,None,'next')
    tails = fighter_for_mutations(human,current).extra_attacks
    assert len(tails) == 1 and has_tag(tails[0],'rule.scorpion-tail')


def test_scaled_skin_composes_physical_light_armour_and_shield(chart,human):
    unit = compile_fighter(FighterBuild('mordheim',human.characteristics,main_weapon_id='weapon.sword',
        off_hand_id='defence.shield',armour_id='armour.light-armour'))
    current = brand(unit,initial(unit),chart[43])
    view = fighter_for_mutations(unit,current)
    assert (view.armour_save,view.natural_armour_save,view.natural_armour_worst_save) == (3,5,6)


def test_burning_body_discards_ordinary_gear_and_retains_actual_protected_items(chart,human):
    sword = replace(human.mutation_equipment[0],effect=EffectSet(tags=('weapon.sword','material.gromril')))
    armour = next(item for item in human.mutation_equipment if item.kind == 'armour')
    unit = replace(human,main_weapon=sword.effect,mutation_equipment=(sword,armour,
        CarriedEquipment('charm',EffectSet(tags=('lucky-charm',)),'other','defence.3')))
    current = brand(unit,initial(unit),chart[61])
    view = fighter_for_mutations(unit,current)
    assert has_tag(view.main_weapon,'material.gromril')
    assert view.armour_save == 7 and has_tag(view.global_effects,'lucky-charm')
    assert has_tag(view.global_effects_without_equipment,'mechanic.burning-body')
    assert has_tag(view.global_effects,'rule.unarmed-without-penalties')


def test_burning_body_cannot_re_equip_forbidden_gear_with_a_later_extra_arm(chart,human):
    current = brand(human,initial(human),chart[61])
    decisions = Choices('brand.equip.0')
    current = brand(human,current,chart[41],decisions=decisions)
    assert fighter_for_mutations(human,current).extra_attacks == ()
    assert 'brand.equip.0' not in decisions.requests


def test_hulking_brute_leadership_can_reach_zero_without_a_source_floor_of_one(chart,human):
    unit = replace(human,characteristics=replace(human.characteristics,leadership=3))
    current = brand(unit,initial(unit),chart[64])
    assert fighter_for_mutations(unit,current).characteristics.leadership == 0


def test_subroll_resources_stay_with_explicit_priest_owner_not_mutation_recipient(chart,human):
    owner = replace(human,global_effects=EffectSet(tags=('mechanic.ranalds-luck',)))
    owner_state, victim_state = initial(owner), initial(human)
    dice = StrictDice([{'key':'brand.atrophy','value':4}])
    decisions = Choices('brand.atrophy.ranalds-luck.plus')
    owned = OwnedRollDice(dice,owner,owner_state,decisions)
    result = apply_brand(human,victim_state,chart[66],owned,decisions,'brand')
    dice.finish()
    assert result.atrophied_legs == 1 and result.atrophied_arms == 0
    assert 'ranalds-luck' in owned.state.resources_spent
    assert 'ranalds-luck' not in result.resources_spent


@pytest.mark.parametrize('roll',[14,15,16,31,45,51,56])
def test_external_chart_facets_do_not_create_attacks_saves_or_campaign_results(chart,human,roll):
    current = brand(human,initial(human),chart[roll])
    view = fighter_for_mutations(human,current)
    assert view.extra_attacks == human.extra_attacks
    assert view.global_effects == human.global_effects
    assert current.condition == Condition.STANDING


def plated():
    return compile_fighter(FighterBuild('mordheim', Characteristics(3,3,3,3,4,2,movement=5,leadership=7),
        main_weapon_id='weapon.sword',armour_id='armour.plate-armour',defence_ids=('defence.helmet',)))


@pytest.mark.parametrize('roll',[25,41,65])
def test_a_worn_metal_armour_keeps_its_identity_through_equipment_rewriting_mutations(chart,roll):
    """The printed electrical-strength clause reads the armour actually worn.

    Great Claw, the Extra Arm and Beweaponed Extremities all move physical
    objects between the fighter's hands.  The plate mail is still worn
    afterwards, so the metal-armour identity the compiler derived from it must
    survive the inventory rebuild instead of being withdrawn with the
    re-projection - and the printed Strength 5 against metal armour keeps
    answering for it.
    """
    plate = plated()
    assert 'condition.metal-armour' in plate.global_effects.tags
    current = brand(plate,initial(plate),chart[roll],[('limb',1)] if roll == 65 else ())
    view = fighter_for_mutations(plate,current)
    assert 'condition.metal-armour' in view.global_effects.tags
    assert electrical_touch_weapon(view).fixed_strength == 5
    assert view.armour_save == plate.armour_save


def test_the_metal_armour_identity_leaves_with_the_armour_burning_body_destroys(chart):
    plate = plated()
    current = brand(plate,initial(plate),chart[61])
    assert all(item.slot is None for item in current.mutation_equipment)
    view = fighter_for_mutations(plate,current)
    assert 'condition.metal-armour' not in view.global_effects.tags
    assert electrical_touch_weapon(view).fixed_strength == 3
    assert view.armour_save == 7


def test_the_supplied_metal_armour_fact_follows_the_worn_metal_defences(chart,human):
    # ``metal_armour`` is a supplied fact about the fighter's worn kit, so the
    # identity lasts while any of that kit is worn and leaves with the last of
    # it - never the other way round.
    assert 'condition.metal-armour' not in human.global_effects.tags
    fact = compile_fighter(FighterBuild('mordheim', human.characteristics,
        main_weapon_id='weapon.sword',off_hand_id='defence.shield',
        armour_id='armour.light-armour',trait_overrides={'metal_armour':True}))
    assert 'condition.metal-armour' in fact.global_effects.tags
    kept = fighter_for_mutations(fact,brand(fact,initial(fact),chart[25]))
    assert 'condition.metal-armour' in kept.global_effects.tags
    gone = fighter_for_mutations(fact,brand(fact,initial(fact),chart[61]))
    assert 'condition.metal-armour' not in gone.global_effects.tags
    # Negative control: the ordinary light-armoured fighter never gains it.
    plain = fighter_for_mutations(human,brand(human,initial(human),chart[25]))
    assert 'condition.metal-armour' not in plain.global_effects.tags
