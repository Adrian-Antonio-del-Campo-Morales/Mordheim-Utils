"""Construction contracts extracted from the modular local-modifier suite.

Every check below compiles a build or asserts a construction refusal; none
executes a round.  Statements, parametrizations and expectations are copied
verbatim from ``tests/engines/modular/test_local_modifier_variants.py``; the
execution assertions and their inputs stay in the modular suite.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild



def canonical(band, profile, weapon='weapon.sword', **options):
    return compile_fighter(FighterBuild('mordheim', band_id=band, profile_id=profile,
        main_weapon_id=weapon, **options))


def enemy(strength=3, *, weapon='weapon.mace', armour='armour.no-armour', **options):
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, strength, 3, 2, 3, 1, leadership=7),
        main_weapon_id=weapon, armour_id=armour, **options))


def test_woodsmen_staff_keeps_parry_and_two_hand_compatibility_construction_contract():
    woodsman = canonical('woodsmen-de-artois-mou', 'chief', 'weapon.quarter-staff')
    assert woodsman.main_weapon.two_handed and woodsman.main_weapon.parry
    for off_hand in ('weapon.sword', 'defence.shield', 'defence.buckler'):
        with pytest.raises(ValueError, match='both hands'):
            canonical('woodsmen-de-artois-mou', 'chief', 'weapon.quarter-staff', off_hand_id=off_hand)


def test_priest_bite_follows_both_double_handed_weapons_and_uses_only_own_strength_construction_contract():
    assert not canonical('shallows-beasts-mim', 'renegades').extra_attacks


@pytest.mark.parametrize('selection', ['weapon.dagger', 'weapon.fist'])
def test_sabretusk_charge_replaces_profile_attacks_only_during_actual_charge_construction_contract(selection):
    cub = canonical('ogre-hunting-party-web', 'sabretusks', selection)
    assert 'weapon.natural-attacks' in cub.main_weapon.tags


def test_bitter_valour_rerolls_wounds_using_natural_strength_construction_contract():
    knight = canonical('knights-of-the-bitter-moors-mim', 'questing-knight',
        special_rule_ids=('band--virtue-of-valour',))
    assert 'skill.virtue-of-valour' not in knight.global_effects.tags


def test_wolf_rat_bite_uses_strength_four_without_an_armour_penalty_construction_contract():
    rat = canonical('skaven-of-clan-moulder-web', 'wolf-rats', 'weapon.dagger')
    assert 'weapon.natural-attacks' in rat.main_weapon.tags
    assert 'poison.black-lotus' not in rat.main_weapon.tags


@pytest.mark.parametrize('band', ['lizardmen', 'lizardmen-lus'])
def test_cold_blooded_psychology_uses_lowest_two_in_the_real_fear_charge_construction_contract(band):
    skink = canonical(band, 'skink-great-crests', 'weapon.axe')
    assert skink.characteristics.leadership == 7
    assert skink.global_effects.tags.count('mechanic.cold-blooded-psychology') == 1


@pytest.mark.parametrize('profile', ['draich', 'young-nobles', 'shearls'])
def test_craven_can_fail_a_fear_charge_even_when_the_fimir_causes_fear_construction_contract(profile):
    # The Draich causes Fear innately; the other two receive an explicit current
    # acquired-Fear condition, proving the same exception without a fake KB grant.
    fighter = canonical('lords-of-the-marsh-mim', profile, 'weapon.axe',
        **({} if profile == 'draich' else {'trait_overrides': {'causes_fear': True}}))
    assert fighter.global_effects.tags.count('mechanic.craven') == 1
    assert 'mechanic.causes-fear' in fighter.global_effects.tags


def test_stupidity_completion_brood_bonus_affects_only_stupidity_tests_construction_contract():
    fighter = canonical('brood-of-ghurash-the-sc', 'firstborns', 'weapon.fist',
                        trait_overrides={'stupidity_leadership_bonus': 2})
    assert fighter.characteristics.leadership == 4
    with pytest.raises(ValueError, match='non-negative integer'):
        canonical('brood-of-ghurash-the-sc', 'firstborns', 'weapon.fist',
                  trait_overrides={'stupidity_leadership_bonus': True})


def test_stupidity_completion_acquired_prior_failure_lasts_until_next_own_turn_construction_contract():
    with pytest.raises(ValueError, match='active Stupidity'):
        enemy(trait_overrides={'stupidity_initial_failed': True})


def test_unlimited_hatred_means_any_enemy_not_infinite_duration_construction_contract():
    rule = 'band--chaos-dwarfs-special-skills-unlimited-hatred'
    warrior = canonical('sons-of-hashut', 'chaos-dwarf-champions', 'weapon.mace',
                        special_rule_ids=(rule,))
    control = canonical('sons-of-hashut', 'chaos-dwarf-champions', 'weapon.mace')
    assert 'skill.hatred' in warrior.global_effects.tags
    assert 'skill.hatred' not in control.global_effects.tags
    with pytest.raises(ValueError):
        canonical('sons-of-hashut', 'hobgoblins', 'weapon.mace', special_rule_ids=(rule,))


@pytest.mark.parametrize('band', ['norse-explorers-btb', 'norse-explorers-lustria'])
def test_barbarian_courage_rerolls_fear_without_rerolling_stupidity_construction_contract(band):
    rule = 'band--norse-special-skills-barbarian-courage'
    assert 'mechanic.fear-reroll' not in canonical(band, 'jarl', 'weapon.fist').global_effects.tags
    with pytest.raises(ValueError):
        canonical(band, 'marauders', 'weapon.fist', special_rule_ids=(rule,))


@pytest.mark.parametrize('band,profile', [('carnival-of-chaos', 'plague-bearers'), ('carnival-of-chaos', 'nurglings'), ('carnival-of-chaos', 'plague-cart'), ('khorne-raiders-sar', 'madbrains')])
def test_explicit_automatic_leadership_passes_without_dice_or_borrowed_leader_construction_contract(band, profile):
    fighter = canonical(band, profile, 'weapon.fist', trait_overrides={'stupidity': True})
    control = canonical(band, 'carnival-master' if band == 'carnival-of-chaos' else 'dread-captain', 'weapon.fist')
    assert 'mechanic.automatic-leadership' in fighter.global_effects.tags
    assert 'mechanic.automatic-leadership' not in control.global_effects.tags


def test_spawn_explicit_automatic_leadership_preserves_its_separate_preparation_construction_contract():
    spawn = canonical('marauders-of-chaos', 'spawn-of-chaos', 'weapon.fist')
    assert 'mechanic.automatic-leadership' in spawn.global_effects.tags
    assert 'mechanic.automatic-leadership' not in canonical('marauders-of-chaos', 'marauder-chieftain', 'weapon.fist').global_effects.tags


def test_revenant_is_selected_requires_thirster_and_recovers_at_own_turn_start_despite_fire_construction_contract():
    thirst = 'strigoi-vampire--great-thirster'
    curse = 'strigoi-vampire--curse-of-the-revenant'
    base = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist')
    vampire = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist', special_rule_ids=(thirst, curse))
    assert 'mechanic.curse-of-the-revenant' not in base.global_effects.tags
    with pytest.raises(ValueError, match='requires Great Thirster'):
        canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist', special_rule_ids=(curse,))
    assert vampire.global_effects.regeneration_save == 7


def test_rousing_sermon_is_priest_only_once_and_expires_after_own_turn_construction_contract():
    skill = 'band--special-skill-rousing-sermon'
    with pytest.raises(ValueError, match='not available'):
        canonical('protectorate-of-sigmar-lotd3', 'templar', 'weapon.fist', special_rule_ids=(skill,))


def test_frantic_ignores_weapon_penalties_low_initiative_and_standing_up_construction_contract():
    fanatic = canonical('crooked-moon-kep', 'fanatics', 'weapon.fist')
    assert 'mechanic.frantic' in fanatic.global_effects.tags
    assert 'mechanic.frantic' not in canonical('crooked-moon-kep', 'big-boss', 'weapon.fist').global_effects.tags


def test_questing_vow_is_acquired_knight_only_and_qualifies_non_fear_leadership_construction_contract():
    skill = 'band--questing-vow'
    base = canonical('bretonnian-chapel-guard', 'questing-knight', 'weapon.fist')
    assert 'mechanic.questing-vow' not in base.global_effects.tags
    with pytest.raises(ValueError, match='not available'):
        canonical('bretonnian-chapel-guard', 'damsel', 'weapon.fist', special_rule_ids=(skill,))


def test_gibbet_iron_cage_is_inseparable_normal_five_plus_armour_construction_contract():
    gibbet = canonical('ghost-pirates-sar', 'gibbets', 'weapon.mace')
    assert gibbet.armour_save == 5 and gibbet.natural_armour_save == 7
    assert canonical('ghost-pirates-sar', 'the-cursed', 'weapon.mace').armour_save == 7
    with pytest.raises(ValueError, match='forbidden|not available'):
        canonical('ghost-pirates-sar', 'gibbets', 'weapon.mace', armour_id='armour.light-armour')


def test_frustratingly_tiny_is_acquired_snotling_defence_not_an_innate_goblin_skill_construction_contract():
    skill = 'bullied-goblin--frustratingly-tiny'
    base = canonical('snotlings-web', 'bigsnotz', 'weapon.sword')
    tiny = canonical('snotlings-web', 'bigsnotz', 'weapon.sword', special_rule_ids=(skill,))
    assert base.global_effects.incoming_hit_modifier == 0
    assert tiny.global_effects.incoming_hit_modifier == -1
    with pytest.raises(ValueError, match='not available'):
        canonical('snotlings-web', 'bullied-goblin', 'weapon.sword', special_rule_ids=(skill,))


def test_hellblade_has_exact_nature_filter_and_deadly_wound_boundary_construction_contract():
    blade = canonical('khorne-raiders-sar', 'dread-captain', 'weapon.hellblade')
    assert blade.main_weapon.two_handed and 'attack.magical' in blade.main_weapon.tags
    with pytest.raises(ValueError, match='mortal special metals'):
        canonical('khorne-raiders-sar', 'dread-captain', 'weapon.hellblade', main_material_id='material.gromril')


def test_shornaal_uses_highest_two_then_stops_testing_after_success_construction_contract():
    with pytest.raises(ValueError, match='not available'):
        canonical('marauders-of-chaos', 'seer', special_rule_ids=('band--mark-of-shornaal',))


def test_supplied_righteous_charge_is_mounted_and_expires_after_first_round_construction_contract():
    with pytest.raises(ValueError, match='mounted recipient'):
        canonical('knights-of-the-bitter-moors-mim', 'questing-knight',
                  trait_overrides={'righteous_charge_active': True})


def test_pimp_nomination_refuses_wrong_recipient_and_nonfemale_target_construction_contract():
    with pytest.raises(ValueError, match='requires Flesh-Peddler'):
        enemy(trait_overrides={'flesh_peddler_mark': True})


def test_native_morr_ceremonial_scythe_is_a_distinct_complete_weapon_construction_contract():
    priest = canonical('hirelings.hired-sword.2b',
        'hireling.hired-sword.priest-of-morr-miracle-workers', 'weapon.ceremonial-scythe')
    generic = enemy(weapon='weapon.scythe')
    assert priest.main_weapon.strength_bonus == 1
    assert priest.main_weapon.two_handed and priest.main_weapon.armour_penetration == 0
    assert 'mechanic.morrs-servant' in priest.global_effects.tags
    assert generic.main_weapon.strength_bonus == 0 and generic.main_weapon.armour_penetration == 1
    for options in ({'off_hand_id': 'weapon.dagger'}, {'off_hand_id': 'defence.shield'},
                    {'off_hand_id': 'defence.buckler'}, {'armour_id': 'armour.light-armour'}):
        with pytest.raises(ValueError):
            canonical('hirelings.hired-sword.2b',
                'hireling.hired-sword.priest-of-morr-miracle-workers', 'weapon.ceremonial-scythe', **options)
    with pytest.raises(ValueError):
        canonical('hirelings.hired-sword.2b',
            'hireling.hired-sword.priest-of-morr-miracle-workers', 'weapon.scythe')


def test_native_verena_sword_only_keeps_owned_ceremonial_dagger_inactive_construction_contract():
    profile = 'hireling.hired-sword.priest-of-verena'
    priest = canonical('hirelings.hired-sword.2b', profile, 'weapon.sword',
        owned_item_ids=('dagger', 'sword'))
    assert priest.main_weapon.parry
    for weapon, off in [('weapon.dagger', None), ('weapon.sword', 'weapon.dagger'),
                        ('weapon.axe', None)]:
        with pytest.raises(ValueError):
            canonical('hirelings.hired-sword.2b', profile, weapon, off_hand_id=off)


@pytest.mark.parametrize('drinking,ws,strength', [(2, 4, 3), (3, 5, 4), (4, 5, 4), (5, 5, 5), (6, 5, 4)])
def test_native_snorri_drinking_results_persist_in_both_player_turns_construction_contract(drinking, ws, strength):
    fighter = canonical('hirelings.dramatis-personae.2b', 'hireling.dramatis.snorri-nosebiter',
        'weapon.dwarf-axe', off_hand_id='weapon.mace', trait_overrides={'snorri_drunk_result': drinking})
    assert (fighter.characteristics.weapon_skill, fighter.characteristics.strength) == (ws, strength)
    assert fighter.global_effects.ward_save == 5
    assert 'mechanic.psychology-immunity' in fighter.global_effects.tags


@pytest.mark.parametrize('count', [1, 2])
def test_native_eagle_friend_has_separate_first_strike_strength_three_attacks_construction_contract(count):
    pid = 'hireling.hired-sword.war-priestess-of-myrmidia'
    fighter = canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger',
        characteristics=Characteristics(3, 5, 3, 1, 4, 1, leadership=8),
        special_rule_ids=(pid + '.skill.eagle-friend',),
        trait_overrides={'eagle_friends': count, 'frenzy': True})
    assert len(fighter.extra_attacks) == count  # Frenzy doubles her A, never her birds.
    with pytest.raises(ValueError, match='requires Eagle Friend'):
        canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger', trait_overrides={'eagle_friends': count})


def test_snerik_keeps_his_source_only_cloak_without_a_fake_duel_effect_construction_contract():
    pid = 'hireling.dramatis.snerik-night-goblin-scout'
    cloak = pid + '.item.camouflage-cloak'
    build = FighterBuild('mordheim', band_id='hirelings.dramatis-personae.2b', profile_id=pid,
        main_weapon_id='weapon.sword', off_hand_id='weapon.dagger',
        owned_item_ids=('dagger', 'sword', 'short_bow', cloak))
    fighter = compile_fighter(build)
    with pytest.raises(ValueError, match='complete legal printed kit'):
        compile_fighter(replace(build, owned_item_ids=('dagger', 'sword', 'short_bow')))
    assert not any('camouflage' in tag for tag in fighter.global_effects.tags)


def test_guiding_dream_refuses_a_nominated_nonhero_and_foreign_mark_construction_contract():
    with pytest.raises(ValueError, match='requires Guiding Dream'):
        enemy(trait_overrides={'guiding_dream_target': True})


def test_strigoi_iron_sinews_is_optional_and_changes_real_wounding_once_construction_contract():
    band = 'survivors-of-strigos-sylv'
    base = canonical(band, 'strigoi-vampire', 'weapon.fist')
    fighter = canonical(band, 'strigoi-vampire', 'weapon.fist',
        special_rule_ids=('strigoi-vampire--iron-sinews',))
    assert base.characteristics.strength == 4
    assert fighter.characteristics.strength == 5
    with pytest.raises(ValueError, match='not available'):
        canonical(band, 'seer', special_rule_ids=('strigoi-vampire--iron-sinews',))


def test_kindred_hatred_requires_bloodline_only_for_vampire_opponents_construction_contract():
    with pytest.raises(ValueError, match='conflicts with the canonical profile'):
        canonical('blood-dragons-mou', 'vampire', trait_overrides={'vampire_bloodline': 'strigoi'})


@pytest.mark.parametrize('source', ['fearsome', 'mutation', 'blessing', 'current-condition', 'canonical-condition'])
def test_acquired_fear_reaches_the_same_real_charge_test_construction_contract(source):
    if source == 'fearsome':
        owner = canonical('mercenaries', 'mercenary-captain', 'weapon.mace', skill_ids=('skill.fearsome',))
        catalogue = CombatCatalogue()
        captain = next(p for p in catalogue.profiles('mordheim', 'mercenaries') if p.profile_id == 'mercenary-captain')
        assert 'skill.fearsome' in catalogue.in_scope_skill_ids(catalogue.skills(captain))
    elif source == 'mutation':
        owner = canonical('cult-of-the-possessed', 'mutants', 'weapon.mace', special_rule_ids=('band--mutations-hideous',))
    elif source == 'blessing':
        owner = canonical('carnival-of-chaos', 'tainted-ones', 'weapon.mace', special_rule_ids=('band--blessings-of-nurgle-hideous',))
    elif source == 'canonical-condition':
        # The canonical id, resolved by construction and not a trait name.
        owner = enemy(condition_ids=('campaign.condition.causes-fear',))
        assert 'mechanic.causes-fear' not in enemy().global_effects.tags
    else:
        owner = enemy(trait_overrides={'causes_fear': True})  # Supplied acquired/current condition.
        assert 'mechanic.causes-fear' not in enemy().global_effects.tags
    assert owner.global_effects.tags.count('mechanic.causes-fear') == 1


@pytest.mark.parametrize('band,profile,rule', [
    ('beastmen-raiders', 'beastmen-chieftain', 'band--beastmen-special-skills-fearless'),
    ('vampire-hunters-of-sylvania-lotd5', 'vampire-hunter', 'band--special-skill-iron-will'),
])
def test_fear_immunity_skips_the_test_without_general_leadership_immunity_construction_contract(band, profile, rule):
    assert 'mechanic.fear-immunity' not in canonical(band, profile, 'weapon.fist').global_effects.tags
    if band.startswith('vampire-hunters'):
        with pytest.raises(ValueError):
            canonical(band, 'priest-of-morr', 'weapon.fist', special_rule_ids=(rule,))


@pytest.mark.parametrize('material,ward', [('material.normal', 4), ('material.gromril', 7), ('material.ithilmar', 7)])
def test_ghost_pirate_ethereal_save_is_source_specific_construction_contract(material, ward):
    assert 'mechanic.ghost-pirate-ethereal' not in canonical('ghost-pirates-sar', 'sea-singer', 'weapon.dagger').global_effects.tags
    if ward == 4:
        with pytest.raises(ValueError, match='Ethereal cannot'):
            canonical('ghost-pirates-sar', 'ghost-captain', 'weapon.dagger', skill_ids=('skill.step-aside',))


@pytest.mark.parametrize('fitting', ['axe', 'club', 'spear', 'morning-star'])
def test_wheelo_fitting_modifies_impact_without_changing_crew_construction_contract(fitting):
    if fitting == 'axe':
        with pytest.raises(ValueError, match='requires a Wheelo'):
            enemy(trait_overrides={'wheelo_fitting': fitting})


def test_ulric_pelt_contributes_once_and_the_printed_kit_refuses_other_armour_construction_contract():
    profile = 'hireling.hired-sword.wolf-priest-of-ulric-miracle-workers'
    wolf = canonical('hirelings.hired-sword.2b', profile, 'weapon.dagger', defence_ids=('defence.wolf-pelt-cloak',))
    assert wolf.armour_save == 6
    for options in ({'armour_id': 'armour.light-armour'}, {'main_weapon_id': 'weapon.pistol'},
                    {'off_hand_id': 'defence.shield'}):
        selected = options.pop('main_weapon_id', 'weapon.dagger')
        with pytest.raises(ValueError): canonical('hirelings.hired-sword.2b', profile, selected, **options)


def test_snorri_requires_a_participating_result_without_changing_other_profiles_construction_contract():
    profile = 'hireling.dramatis.snorri-nosebiter'
    for value in (None, 1, 0, 7, True, 2.0, '2'):
        traits = {} if value is None else {'snorri_drunk_result': value}
        with pytest.raises((ValueError, TypeError)):
            canonical('hirelings.dramatis-personae.2b', profile, 'weapon.dwarf-axe', trait_overrides=traits)
    with pytest.raises(ValueError, match='canonical drinking rule'):
        enemy(trait_overrides={'snorri_drunk_result': 3})
    with pytest.raises(ValueError):
        canonical('hirelings.dramatis-personae.2b', profile, 'weapon.dwarf-axe',
            armour_id='armour.light-armour', trait_overrides={'snorri_drunk_result': 3})


def test_sigmar_enlightened_is_offered_separately_and_not_granted_to_other_priests():
    from mordheim_construction.selection import available_special_rules
    profile = 'hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers'
    mark = profile + '.skill.enlightened'
    build = FighterBuild('mordheim', band_id='hirelings.hired-sword.2b', profile_id=profile, main_weapon_id='weapon.dagger')
    base = compile_fighter(build)
    assert 'mechanic.sigmar-enlightened' not in base.global_effects.tags
    assert mark in set(available_special_rules(build, None))
    catalogue = CombatCatalogue()
    choice = next(p for p in catalogue.profiles('mordheim', 'hirelings.hired-sword.2b') if p.profile_id == profile)
    option = next(s for s in catalogue.skills(choice) if s.rule_id == mark)
    assert option.runtime_available and option.unavailable_reason is None
    assert catalogue.skill_ui_ids(choice, (), (mark,)) == (option.id,)
    cultist = canonical('cult-of-the-possessed', 'brethren', 'weapon.mace')
    assert 'warband-group.chaotic' in cultist.global_effects.tags
    with pytest.raises(ValueError):
        canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.druid-priest-of-taal', 'weapon.dagger', special_rule_ids=(mark,))
