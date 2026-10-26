"""Construction contracts split from ``tests/engines/modular/test_local_modifier_variants.py``.

Each check below asserts a catalog offer, the compiled output of
the canonical builder or a construction refusal; none executes a round, so they
belong to the construction suite.  Names, parametrizations, assertions and
bodies are the originals.
"""
from __future__ import annotations

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


TROLL_STUPIDITY_RECIPIENTS = (
    ('black-orcs', 'troll', 'black-orc-boss'),
    ('night-goblins-kaz', 'troll', 'big-boss'),
    ('night-goblins-mic', 'troll', 'big-boss'),
    ('night-goblins-web', 'troll', 'boss'),
    ('orc-mob', 'troll', 'orc-boss'),
    ('underworld-alliance-mim', 'warpstone-troll', 'goblin-bully'),
)


STUPIDITY_COMPLETION_PROFILES = (
    ('skaven-clan-eshin', 'rat-ogre'), ('skaven-clan-pestilens', 'rat-ogre'),
    ('skaven-of-clan-mors-kaz', 'rat-ogre'), ('skaven-of-clan-moulder-web', 'rat-ogres'),
    ('skaven-of-clan-pristekk-sc', 'rat-ogres'), ('crooked-moon-kep', 'troll'),
    ('mazzalupo-web', 'black-sheep'), ('dark-elves', 'cold-one-beasthounds'),
    ('brood-of-ghurash-the-sc', 'firstborns'), ('forest-goblins', 'gigantic-spider'),
    ('forest-goblins-lus', 'gigantic-spider'), ('kislevites', 'trained-bear'),
)


def test_local_skill_activation_is_offered_and_refuses_a_foreign_band():
    c = CombatCatalogue()
    for band, profile, rule in (
        ('high-elves-lus', 'loremaster', 'band--skill-unerring-strike'),
        ('silent-brotherhood-sc', 'poisoner', 'band--skill-cutthroat'),
        ('knights-of-the-bitter-moors-mim', 'questing-knight', 'band--virtue-of-valour'),
    ):
        choice = next(r for r in c.profiles('mordheim', band) if r.profile_id == profile)
        assert rule in {r.rule_id for r in c.skills(choice) if r.runtime_available}
    with pytest.raises(ValueError):
        canonical('high-elves-lus', 'loremaster', special_rule_ids=('band--skill-cutthroat',))
    # The PDF table, not the original erroneous profile projection, governs access.
    for profile, categories in (
        ('loremaster', {'academic', 'speed', 'special'}),
        ('sword-wardens', {'combat', 'academic', 'strength', 'speed', 'special'}),
        ('rangers', {'shooting', 'speed', 'special'}),
    ):
        choice = next(r for r in c.profiles('mordheim', 'high-elves-lus') if r.profile_id == profile)
        assert set(c.profile(choice)['skill_access']) == categories
        assert 'band--skill-unerring-strike' in {r.rule_id for r in c.skills(choice) if r.runtime_available}


def test_band_fear_uses_the_printed_recipient_exceptions():
    for band, profile, expected in (
        ('brood-of-ghurash-the-sc', 'firstborns', True),
        ('brood-of-ghurash-the-sc', 'children', False),
        ('maneaters', 'captain', True), ('maneaters', 'youngbloods', False),
        ('tomb-guardians', 'tomb-lord', True), ('tomb-guardians', 'tomb-scorpions', False),
        ('undead', 'vampire', True), ('undead', 'necromancer', False),
        ('beastmen-raiders', 'minotaur', True), ('skaven-clan-eshin', 'rat-ogre', True),
    ):
        assert ('mechanic.causes-fear' in canonical(band, profile, 'weapon.fist').global_effects.tags) is expected, (band, profile)
    with pytest.raises(ValueError, match='available|recipient|only'):
        canonical('cult-of-the-possessed', 'brethren', special_rule_ids=('band--mutations-hideous',))


def test_troll_stupidity_recipients_are_canonical_and_do_not_leak():
    for band, profile, control in TROLL_STUPIDITY_RECIPIENTS:
        fighter = canonical(band, profile, 'weapon.fist')
        assert fighter.global_effects.tags.count('mechanic.stupidity') == 1, band
        assert 'mechanic.stupidity' not in canonical(band, control, 'weapon.fist').global_effects.tags, band


def test_stupidity_completion_canonical_routes_and_brood_recipient_filter():
    for band, profile in STUPIDITY_COMPLETION_PROFILES:
        # Moulder's printed 'It's Alive!' requires exactly one mutation per Rat Ogre.
        mutations = ('band--mutations-great-claw',) if (band, profile) == (
            'skaven-of-clan-moulder-web', 'rat-ogres') else ()
        fighter = canonical(band, profile, 'weapon.fist', special_rule_ids=mutations)
        assert fighter.global_effects.tags.count('mechanic.stupidity') == 1, (band, profile)
    worm = canonical('brood-of-ghurash-the-sc', 'baneworms', 'weapon.fist')
    assert 'mechanic.stupidity' not in worm.global_effects.tags
    with pytest.raises(ValueError, match='Brood Mentality'):
        canonical('brood-of-ghurash-the-sc', 'baneworms', 'weapon.fist',
                  trait_overrides={'stupidity_leadership_bonus': 1})


def test_elf_identity_and_hatred_do_not_spread_to_animals_or_mixed_recruits():
    for band, profile in [('dark-elves', 'cold-one-beasthounds'), ('druchii-mic', 'slavehounds'),
                          ('lothern-sea-patrol-sar', 'commodore')]:
        fighter = canonical(band, profile, 'weapon.fist')
        assert not any(tag.startswith('mechanic.hatred-') for tag in fighter.global_effects.tags)
    for band, profile in [('dark-elves', 'cold-one-beasthounds'), ('druchii-mic', 'slavehounds'),
                          ('lothern-sea-patrol-sar', 'raw-recruits')]:
        assert not any(tag in canonical(band, profile, 'weapon.fist').global_effects.tags
                       for tag in ('species.high-elf', 'species.dark-elf'))
    # The source explicitly allows both Elven and Human Raw Recruits.
    recruit = canonical('lothern-sea-patrol-sar', 'raw-recruits', 'weapon.fist', trait_overrides={'elf_kind': 'high'})
    assert 'species.high-elf' in recruit.global_effects.tags
    assert 'species.dark-elf' in canonical('druchii-mic', 'witch-elves', 'weapon.fist').global_effects.tags
    assert 'species.high-elf' in canonical('shadow-warriors', 'shadow-warrior', 'weapon.fist').global_effects.tags
    assert 'species.high-elf' not in canonical('high-elves-lus', 'seaguard', 'weapon.fist', trait_overrides={'elf_kind': 'other'}).global_effects.tags
    wood = enemy(trait_overrides={'elf_kind': 'wood'})
    assert {'species.elf', 'species.wood-elf'} <= set(wood.global_effects.tags)
    with pytest.raises(ValueError, match='elf_kind'):
        enemy(trait_overrides={'elf_kind': 'unknown-elf'})


def test_tomb_guardians_psychology_immunity_excludes_the_living_scorpion():
    for profile in ('tomb-lord', 'liche-priest', 'acolytes', 'skeleton-warriors', 'tomb-guardians'):
        assert 'mechanic.psychology-immunity' in canonical('tomb-guardians', profile, 'weapon.fist').global_effects.tags
    assert 'mechanic.psychology-immunity' not in canonical('tomb-guardians', 'tomb-scorpions', 'weapon.fist').global_effects.tags


def test_cloak_uses_the_armour_role_and_normal_shield_helmet_composition():
    cloak = 'defence.sea-dragon-cloak'
    assert enemy(defence_ids=(cloak,)).armour_save == 5
    assert enemy(defence_ids=(cloak,), off_hand_id='defence.shield').armour_save == 4
    assert enemy(defence_ids=(cloak, 'defence.helmet'), off_hand_id='defence.shield').armour_save == 4
    with pytest.raises(ValueError, match='armour choice'):
        enemy(armour='armour.light-armour', defence_ids=(cloak,))
    with pytest.raises(ValueError, match='armour|not available'):
        canonical('dwarf-slayer-cult-web', 'giant-slayer', 'weapon.axe', defence_ids=(cloak,))
