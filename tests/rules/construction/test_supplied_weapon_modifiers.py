"""Supplied weapon-exemplar modifiers: the blessing, the honing and the coating."""
import pytest
from dataclasses import replace

from mordheim_combat.phases import PriorityContext, resolve_priority
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def build(band, profile, main, **options):
    return FighterBuild('mordheim', Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
                        band_id=band, profile_id=profile, main_weapon_id=main, **options)


def tape(*rolls):
    return StrictDice([{'key': key, 'value': value} for key, value in rolls])


def strike(attacker, defender, weapon, *rolls):
    dice = tape(*rolls)
    result = resolve_reference_attack(attacker, defender, initialize_fighter(attacker, tape(), 'a'),
        initialize_fighter(defender, tape(), 'b'), weapon, dice, key='r',
        decisions=StrictDecisions([]))
    dice.finish()
    return result


@pytest.mark.phase3_rules
@pytest.mark.parametrize('band,profile,weapon', [
    ('sisters-of-sigmar', 'sister-superior', 'weapon.mace'),
    ('witch-hunters', 'witch-hunter-captain', 'weapon.sword'),
])
def test_supplied_blessing_wounds_undead_and_possessed_on_two_plus(band, profile, weapon):
    bearer = compile_fighter(build(band, profile, weapon,
        condition_ids=('condition.blessed-weapon',),
        trait_overrides={'blessed_weapon_slots': ['main']}))
    undead = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace',
        trait_overrides={'creature_kind': 'undead'}))
    possessed = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace',
        trait_overrides={'creature_kind': 'possessed'}))
    living = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace'))
    # Strength 3 against Toughness 4 needs 5+; the blessing alone lowers it to 2+.
    assert strike(bearer, undead, bearer.main_weapon, ('r.hit', 4), ('r.wound', 2)).wounded
    assert strike(bearer, possessed, bearer.main_weapon, ('r.hit', 4), ('r.wound', 2)).wounded
    assert not strike(bearer, living, bearer.main_weapon, ('r.hit', 4), ('r.wound', 2)).wounded
    # The printed consequence is neither an automatic hit nor an automatic wound:
    # a 3 still misses Weapon Skill 3, and a 1 still fails to wound.
    assert not strike(bearer, undead, bearer.main_weapon, ('r.hit', 3)).hit
    assert not strike(bearer, undead, bearer.main_weapon, ('r.hit', 4), ('r.wound', 1)).wounded


@pytest.mark.phase3_rules
def test_supplied_blessing_leaves_the_other_hand_and_the_saves_alone():
    bearer = compile_fighter(build('sisters-of-sigmar', 'sister-superior', 'weapon.mace',
        off_hand_id='weapon.dagger', condition_ids=('condition.blessed-weapon',),
        trait_overrides={'blessed_weapon_slots': ['main']}))
    armoured = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace',
        armour_id='armour.heavy-armour', trait_overrides={'creature_kind': 'undead'}))
    assert 'blessing.undead-possessed-on-two' in bearer.main_weapon.tags
    assert 'blessing.undead-possessed-on-two' not in bearer.off_hand.tags
    # The blesser still rolls to hit, and the wounded Undead still rolls its 5+ save.
    assert not strike(bearer, armoured, bearer.off_hand, ('r.hit', 3)).hit
    saved = strike(bearer, armoured, bearer.main_weapon, ('r.hit', 4), ('r.wound', 2), ('r.armour', 5))
    assert saved.saved and saved.defender.wounds == initialize_fighter(armoured, tape(), 'b').wounds


@pytest.mark.phase2_construction
def test_supplied_blessing_needs_a_sisters_or_witch_hunters_bearer():
    with pytest.raises(ValueError, match='bearers'):
        compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.sword',
            condition_ids=('condition.blessed-weapon',),
            trait_overrides={'blessed_weapon_slots': ['main']}))
    with pytest.raises(ValueError, match='at most 1'):
        compile_fighter(build('sisters-of-sigmar', 'sister-superior', 'weapon.mace',
            off_hand_id='weapon.dagger', condition_ids=('condition.blessed-weapon',),
            trait_overrides={'blessed_weapon_slots': ['main', 'off']}))


@pytest.mark.phase3_rules
@pytest.mark.parametrize('band,profile,weapon', [
    ('witch-hunters', 'witch-hunter-captain', 'weapon.sword'),
    ('battle-monks-of-cathay', 'soldiers', 'weapon.dragon-sword'),
])
def test_supplied_honing_gives_the_named_blades_cutting_edge(band, profile, weapon):
    plain = compile_fighter(build(band, profile, weapon))
    honed = compile_fighter(build(band, profile, weapon,
        condition_ids=('condition.swordsmith-honing',), trait_overrides={'honing_slots': ['main']}))
    # The honing is a supplied fact, not a between-battles service: without it the
    # printed Cutting Edge rule is absent and no roll is asked for.
    assert plain.main_weapon.armour_penetration == 0
    assert 'rule.cutting-edge' not in plain.main_weapon.tags
    assert honed.main_weapon.armour_penetration == 1
    assert 'rule.cutting-edge' in honed.main_weapon.tags


@pytest.mark.phase3_rules
def test_supplied_honing_worsens_the_save_on_the_honed_blade_alone():
    honed = compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.sword',
        off_hand_id='weapon.sword', condition_ids=('condition.swordsmith-honing',),
        trait_overrides={'honing_slots': ['main']}))
    unhoned = compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.sword',
        off_hand_id='weapon.sword'))
    armoured = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace',
        armour_id='armour.heavy-armour'))
    # Heavy armour saves on 5+; on Strength 3 the honed blade's extra -1 denies a 5.
    assert strike(unhoned, armoured, unhoned.main_weapon, ('r.hit', 4), ('r.wound', 4),
                  ('r.armour', 5)).saved
    assert not strike(honed, armoured, honed.main_weapon, ('r.hit', 4), ('r.wound', 4),
                      ('r.armour', 5)).saved
    # The other hand carries a blade of the same list but was not named.
    assert 'rule.cutting-edge' not in honed.off_hand.tags
    assert strike(honed, armoured, honed.off_hand, ('r.hit', 4), ('r.wound', 4),
                  ('r.armour', 5)).saved


@pytest.mark.phase2_construction
def test_supplied_honing_reaches_swords_only_and_at_most_three():
    bearer = compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.sword',
        off_hand_id='weapon.sword', condition_ids=('condition.swordsmith-honing',),
        trait_overrides={'honing_slots': ['main', 'off']}))
    assert 'rule.cutting-edge' in bearer.main_weapon.tags
    assert 'rule.cutting-edge' in bearer.off_hand.tags
    with pytest.raises(ValueError, match='not eligible'):
        compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.mace',
            condition_ids=('condition.swordsmith-honing',),
            trait_overrides={'honing_slots': ['main']}))
    with pytest.raises(ValueError, match='distinct'):
        compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.sword',
            condition_ids=('condition.swordsmith-honing',),
            trait_overrides={'honing_slots': ['main', 'main']}))


@pytest.mark.phase4_modular
def test_distinct_supplied_modifiers_compose_without_relaxing_the_rune_limit():
    facts = {'blessed_weapon_slots': ['main'], 'honing_slots': ['main'],
             'rune_cleaving_slots': ['main'], 'rune_striking_slots': ['main']}
    conditions = ('condition.blessed-weapon', 'condition.swordsmith-honing',
                  'condition.rune-cleaving')
    bearer = compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.sword',
        condition_ids=conditions, trait_overrides=facts))
    assert 'blessing.undead-possessed-on-two' in bearer.main_weapon.tags
    assert 'rule.cutting-edge' in bearer.main_weapon.tags
    assert bearer.main_weapon.armour_penetration == 1
    assert bearer.main_weapon.strength_bonus == 1
    with pytest.raises(ValueError, match='Only one Rune'):
        compile_fighter(build('witch-hunters', 'witch-hunter-captain', 'weapon.sword',
            condition_ids=(*conditions, 'condition.rune-striking'), trait_overrides=facts))


@pytest.mark.phase3_rules
def test_master_craftsman_strength_changes_only_the_chosen_weapon_and_leaves_with_it():
    owner = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.sword',
        off_hand_id='weapon.dagger', condition_ids=('condition.master-craftsman-strength',),
        trait_overrides={'craftsman_strength_slots': ['main']}))
    foe = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace'))
    assert strike(owner, foe, owner.main_weapon, ('r.hit', 4), ('r.wound', 3)).wounded
    assert not strike(owner, foe, owner.off_hand, ('r.hit', 4), ('r.wound', 3)).wounded
    active = equipment_for_state(owner, replace(initialize_fighter(owner, tape(), 'a'),
                                               broken_hands=('main',)), first_round=False)
    assert active.main_weapon.strength_bonus == owner.off_hand.strength_bonus
    assert 'weapon.dagger' in active.main_weapon.tags
    with pytest.raises(ValueError, match='at most 1'):
        compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.sword',
            off_hand_id='weapon.dagger', condition_ids=('condition.master-craftsman-strength',),
            trait_overrides={'craftsman_strength_slots': ['main', 'off']}))


@pytest.mark.phase3_rules
def test_master_craftsman_initiative_controls_round_order_and_expires_on_weapon_loss():
    owner = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.sword',
        off_hand_id='weapon.dagger', condition_ids=('condition.master-craftsman-initiative',),
        trait_overrides={'craftsman_initiative_slots': ['main']}))
    foe = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace'))
    state = initialize_duel(owner, foe, tape(), context=DuelContext(charging=(), active_participant='first'))
    dice = tape(('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
                ('round.0.second.attack.0.hit', 1))
    result = resolve_round(owner, foe, state, dice)
    dice.finish()  # Strict tape has no Initiative tie roll: the upgrade wins it.
    assert result.state.round_index == 1
    assert resolve_priority(PriorityContext(owner, foe)).initiative == 4
    active = equipment_for_state(owner, replace(state.first, broken_hands=('main',)), first_round=False)
    assert resolve_priority(PriorityContext(active, foe)).initiative == 3
    assert owner.off_hand.initiative_bonus == 0


@pytest.mark.phase3_rules
def test_master_craftsman_initiative_on_extra_hand_counts_once_and_leaves_with_that_hand():
    owner = compile_fighter(build('cult-of-the-possessed', 'mutants', 'weapon.sword',
        extra_hand_id='weapon.dagger', special_rule_ids=('band--mutations-extra-arm',),
        condition_ids=('condition.master-craftsman-initiative',),
        trait_overrides={'craftsman_initiative_slots': ['extra']}))
    foe = compile_fighter(build('mercenaries', 'mercenary-captain', 'weapon.mace'))
    assert resolve_priority(PriorityContext(owner, foe)).initiative == 4
    state = replace(initialize_fighter(owner, tape(), 'a'), broken_hands=('extra',))
    active = equipment_for_state(owner, state, first_round=False)
    assert resolve_priority(PriorityContext(active, foe)).initiative == 3


@pytest.mark.phase3_rules
def test_supplied_coating_stays_on_the_chosen_weapon_and_on_its_poison_free_copy():
    coated = compile_fighter(build('hirelings.dramatis-personae.2a', 'hireling.dramatis.the-foole',
        'weapon.sword', off_hand_id='weapon.dagger',
        condition_ids=('condition.giggle-juice-coating',), trait_overrides={'coating_slots': ['main']}))
    assert coated.main_weapon.strength_bonus == 1 and coated.main_weapon.injury_modifier == 1
    assert 'poison.giggle-juice' in coated.main_weapon.tags
    # The Foole's other carried pieces keep the printed kit untouched.
    assert coated.off_hand.strength_bonus == 0 and coated.off_hand.injury_modifier == 0
    assert 'poison.giggle-juice' not in coated.off_hand.tags
    # A poison-immune defender meets the piece without the coating.
    clean = coated.main_weapon_without_poison
    assert clean.strength_bonus == 0 and clean.injury_modifier == 0
    assert 'poison.giggle-juice' not in clean.tags
    # One supplied coating covers one weapon only.
    with pytest.raises(ValueError, match='at most 1'):
        compile_fighter(build('hirelings.dramatis-personae.2a', 'hireling.dramatis.the-foole',
            'weapon.sword', off_hand_id='weapon.dagger',
            condition_ids=('condition.giggle-juice-coating',),
            trait_overrides={'coating_slots': ['main', 'off']}))
