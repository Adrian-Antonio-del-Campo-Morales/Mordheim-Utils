"""Construction contracts split from ``tests/engines/modular/test_local_modifier_variants.py``.

Every check below asserts the compiled output of the canonical
builder or a construction refusal; none executes a round, so they belong to the
construction suite.  Names, parametrizations, assertions and bodies are the
originals; the phase marker is the construction category.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def canonical(band, profile, weapon='weapon.sword', **options):
    return compile_fighter(FighterBuild('mordheim', band_id=band, profile_id=profile,
        main_weapon_id=weapon, **options))


def _penthesilea_canonical():
    return compile_fighter(FighterBuild('mordheim',
        band_id='hirelings.dramatis-personae.1b',
        profile_id='hireling.dramatis.penthesilea-mark-of-the-serpent'))

@pytest.mark.phase2_construction
def test_penthesilea_canonical_profile_treatment_does_not_duplicate_the_mark():
    pent = _penthesilea_canonical()
    # The printed +1 Movement/Initiative of the mark is already inside the
    # normalized profile (M 5*, I 5*); compilation keeps exactly those numbers.
    assert (pent.characteristics.movement, pent.characteristics.initiative) == (5, 5)
    assert 'weapon.starsword' in pent.main_weapon.tags
    assert 'mechanic.mesmerising-dance' in pent.global_effects.tags
    assert {'mechanic.charm-immunity', 'mechanic.fear-immunity'} <= set(pent.global_effects.tags)
    assert pent.global_effects.charge_attacks_bonus == 1

@pytest.mark.phase2_construction
def test_arkhar_is_a_selected_leader_mark_not_a_bandwide_grant():
    leader = canonical('marauders-of-chaos', 'marauder-chieftain',
                       special_rule_ids=('band--mark-of-arkhar',))
    control = canonical('marauders-of-chaos', 'champions')
    assert leader.global_effects.frenzy and not control.global_effects.frenzy
    with pytest.raises(ValueError):
        canonical('marauders-of-chaos', 'champions', special_rule_ids=('band--mark-of-arkhar',))

@pytest.mark.phase2_construction
@pytest.mark.parametrize('profile,immune', [('giant-slayer', True), ('stubbles', False), ('rememberer', False)])
def test_slayer_compound_rule_preserves_novice_and_rememberer_exceptions(profile, immune):
    slayer = canonical('dwarf-slayer-cult-web', profile, 'weapon.axe')
    assert ('mechanic.psychology-immunity' in slayer.global_effects.tags) is immune
    if profile != 'rememberer':
        with pytest.raises(ValueError, match='armour is forbidden'):
            canonical('dwarf-slayer-cult-web', profile, 'weapon.axe', armour_id='armour.light-armour')
    else:
        assert canonical('dwarf-slayer-cult-web', profile, 'weapon.axe', armour_id='armour.light-armour').armour_save < 7

@pytest.mark.phase2_construction
def test_ogre_hunter_huuuuge_preserves_light_armour_but_refuses_heavy():
    # The Ogre Equipment List offers the Cleaver (which counts as an Axe);
    # ``weapon.cleaver`` is the axe-profile weapon the list actually resolves.
    assert canonical('ogre-hunting-party-web', 'ogre-hunter', 'weapon.cleaver', armour_id='armour.light-armour').armour_save == 6
    with pytest.raises(ValueError, match='heavy armour'):
        canonical('ogre-hunting-party-web', 'ogre-hunter', 'weapon.cleaver', armour_id='armour.heavy-armour')

@pytest.mark.phase2_construction
def test_foul_odour_refuses_any_supplied_open_flame_through_shared_legality():
    rule = 'band--ostlander-special-skills-foul-odour'
    assert canonical('ostlanders', 'elder', special_rule_ids=(rule,))
    with pytest.raises(ValueError, match='Foul Odour forbids carrying open flames'):
        canonical('ostlanders', 'elder', special_rule_ids=(rule,), trait_overrides={'lit_item': True})

@pytest.mark.phase2_construction
def test_wheelo_mighty_blow_replaces_strength_with_crew_wound_bonus():
    fighter = canonical('snotlings-web', 'wheelo', 'weapon.dagger', skill_ids=('skill.mighty-blow',))
    assert fighter.global_effects.strength_bonus == 0
    assert fighter.global_effects.wound_modifier == 1

@pytest.mark.phase2_construction
@pytest.mark.parametrize('profile,weapon,off', [
    ('trickster-priest-of-ranald', 'weapon.sword', 'weapon.dagger'),
    ('druid-priest-of-taal', 'weapon.dagger', None),
])
def test_native_priest_strictures_compile_kit_and_refuse_foreign_equipment(profile, weapon, off):
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.' + profile, weapon, off_hand_id=off)
    assert weapon in fighter.main_weapon.tags
    for override in ({'armour_id': 'armour.heavy-armour'}, {'main_weapon_id': 'weapon.pistol'},
                     {'main_weapon_id': 'weapon.axe'}):
        options = {'off_hand_id': off, **override}
        selected = options.pop('main_weapon_id', weapon)
        with pytest.raises(ValueError):
            canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.' + profile, selected, **options)

@pytest.mark.phase2_construction
def test_ulric_rival_identity_does_not_expand_to_an_entire_witch_hunter_warband():
    hunter = canonical('witch-hunters', 'witch-hunters')
    priest = canonical('witch-hunters', 'warrior-priest', 'weapon.mace')
    zealot = canonical('witch-hunters', 'zealots', 'weapon.mace')
    assert 'identity.ulric-rival' in hunter.global_effects.tags
    assert 'identity.ulric-rival' in priest.global_effects.tags
    assert 'identity.ulric-rival' not in zealot.global_effects.tags

@pytest.mark.phase2_construction
def test_native_sister_requires_two_distinct_skills_without_matriarch_access():
    from mordheim_construction.selection import available_special_rules
    build = FighterBuild('mordheim', band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.sister-of-sigmar', main_weapon_id='weapon.sigmarite-hammer')
    choices = available_special_rules(build, None)
    assert set(choices) == {'band--special-skills-' + suffix for suffix in (
        'sign-of-sigmar', 'protection-of-sigmar', 'righteous-fury', 'absolute-faith')}
    sign, fury, faith = ('band--special-skills-' + suffix for suffix in ('sign-of-sigmar', 'righteous-fury', 'absolute-faith'))
    for selected in ((), (sign,), (sign, sign), (sign, fury, faith)):
        with pytest.raises(ValueError, match='exactly two distinct'):
            compile_fighter(replace(build, special_rule_ids=selected))
    with pytest.raises(ValueError, match='not available'):
        compile_fighter(replace(build, special_rule_ids=(sign, 'band--special-skills-utter-determination')))
