"""TC15 p23/p26 plus authorized Weapon Master ruling: complete canonical admission."""
from dataclasses import replace
import pytest
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.eligibility import desktop_call
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_combat.modular.contexts import _combined_effect, _hit_reroll
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_core.models import DuelContext

PID = 'hireling.dramatis.penthesilea-mark-of-the-serpent'


def build(**options):
    return FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b', profile_id=PID, **options)


def package_and_profile():
    package = next(p for p in combat_packages('mordheim') if p.band['id'] == 'hirelings.dramatis-personae.1b')
    return package, next(p for p in package.profiles if p['id'] == PID)


def test_full_profile_admits_printed_weapons_without_invented_combat_bonuses():
    owner = compile_fighter(build(main_weapon_id='weapon.starsword', off_hand_id='weapon.starblade',
        defence_ids=('defence.enchanted-skins',)))
    assert (owner.characteristics.movement, owner.characteristics.initiative) == (5,5)
    assert (owner.characteristics.strength, owner.characteristics.attacks) == (4,2)
    assert owner.global_effects.charge_attacks_bonus == 1  # Savage Fury alone.
    assert 'weapon.starsword' in owner.main_weapon.tags
    assert 'weapon.starblade' in owner.off_hand.tags


def test_source_concealment_is_explicitly_terrain_only_and_mark_already_in_profile():
    _, profile = package_and_profile()
    rules = {r['id'].split('.rule.')[-1]: r for r in profile['rules']}
    assert rules['concealment']['runtime']['scope'] == 'NO'
    assert 'jungle' in rules['concealment']['effect'].lower()
    assert (profile['characteristics']['M'],profile['characteristics']['I']) == (5,5)
    assert rules['man-hater']['runtime']['effects'][0]['binding']['id'] == 'mechanic.man-hater'


# Primary: the two printed pieces are consumed exactly once. The real round
# below is the secondary guarantee that the compiled pair reaches combat.
def test_printed_two_weapon_configuration_consumes_one_of_each_and_no_duplicate_copy():
    package, profile = package_and_profile()
    selected = build(main_weapon_id='weapon.starsword',off_hand_id='weapon.starblade')
    kit = desktop_call('hirelingKit',selected,package=package,profile=profile)
    assert kit.count('starsword') == kit.count('starblade') == 1
    with pytest.raises(ValueError):
        desktop_call('hirelingKit',replace(selected,off_hand_id='weapon.starsword'),package=package,profile=profile)
    component = compile_fighter(selected)
    foe = compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,2,1,leadership=7)))
    tape = StrictDice([{'key':key,'value':1} for key in
        ('round.0.second.mesmerising-dance.0','round.0.second.mesmerising-dance.1',
         'round.0.first.attack.0.hit','round.0.first.attack.1.hit','round.0.first.attack.2.hit',
         'round.0.first.attack.3.hit','round.0.second.attack.0.hit')])
    state = initialize_duel(component,foe,StrictDice([]),context=DuelContext(charging=('first',),active_participant='first'))
    decisions = StrictDecisions([{'key':'round.0.first.main-weapon-majority','value':True}])
    result = resolve_round(component,foe,state,tape,decisions)
    decisions.finish()
    tape.finish()
    assert len(result.attacks) == 5


@pytest.mark.parametrize('tags,expected', [
    (('species.human','sex.male'),True),
    (('species.human','sex.female','warband-group.human'),False),
    (('species.elf','sex.male','warband-group.human'),False),
    (('species.human','warband-group.human'),False)])
def test_man_hater_uses_individual_human_male_identity(tags,expected):
    owner = compile_fighter(build())
    foe = compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,2,1)))
    foe = replace(foe,global_effects=replace(foe.global_effects,tags=tags))
    effect = _combined_effect(owner,owner.main_weapon)
    assert _hit_reroll(owner,foe,owner.main_weapon,effect,True,False) is expected
    assert not _hit_reroll(owner,foe,owner.main_weapon,effect,False,False)
    assert not _hit_reroll(owner,foe,owner.main_weapon,effect,True,False,frenzy=True)


def test_weapons_training_allows_owned_melee_equipment_but_not_free_copies():
    owner = compile_fighter(build(main_weapon_id='weapon.mace', owned_item_ids=('mace',)))
    assert 'weapon.mace' in owner.main_weapon.tags
    with pytest.raises(ValueError,match='physical copies'):
        compile_fighter(build(main_weapon_id='weapon.mace'))
    with pytest.raises(ValueError,match='physical copies'):
        compile_fighter(build(main_weapon_id='weapon.mace',off_hand_id='weapon.mace',owned_item_ids=('mace',)))
    doubled = compile_fighter(build(main_weapon_id='weapon.mace',off_hand_id='weapon.mace',owned_item_ids=('mace','mace')))
    assert doubled.off_hand_attacks


@pytest.mark.parametrize('item,weapon', [('pistol','weapon.pistol'),('bow','weapon.bow')])
def test_weapons_training_does_not_grant_ranged_weapons(item,weapon):
    with pytest.raises(ValueError,match='does not grant ranged'):
        compile_fighter(build(main_weapon_id=weapon,owned_item_ids=(item,)))


def test_weapon_knowledge_of_one_character_does_not_leak_to_other_profiles():
    with pytest.raises(ValueError,match='legal printed kit'):
        compile_fighter(FighterBuild('mordheim',band_id='hirelings.dramatis-personae.1b',
            profile_id='hireling.dramatis.maximilian-the-mad',main_weapon_id='weapon.mace'))


@pytest.mark.parametrize('item,weapon', [
    ('weapon.vomit-attack','weapon.vomit-attack'),
    ('hireling.dramatis.drenok-johansen-wielder-of-the-great-axe.item.axe-of-icefang','weapon.icefang-axe')])
def test_training_does_not_turn_an_ability_or_another_character_unique_into_owned_gear(item,weapon):
    with pytest.raises(ValueError,match='does not grant ranged weapons, armour or another'):
        compile_fighter(build(main_weapon_id=weapon,owned_item_ids=(item,)))
