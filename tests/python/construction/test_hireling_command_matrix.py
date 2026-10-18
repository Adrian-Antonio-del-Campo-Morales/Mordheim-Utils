"""Hireling and Mazzalupo Command contracts from canonical catalogues.

Explicit rule tables preserve the assigned cases independently of retired
development inventories. Construction and runtime assertions remain separate.
"""
from __future__ import annotations

from functools import lru_cache

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import available_special_rules
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_knowledge.campaign import load_campaign_catalog, load_hirelings
from mordheim_knowledge.loader import load_bands, load_collections, runtime_bindings

COLLECTION = "mordheim"
WANDERING_KNIGHT = "wandering-knight"

#: ``(canonical rule id, owner profile id, assigned Q)`` for every hireling
#: case. The owner is the catalogue profile whose ``rules`` declare the node;
#: question ids retain historical provenance only.
HIRELING_ORIGINS = (
    ("hireling.dramatis.aldred-fellblade.rule.righteous-fury-orcs-goblins", "hireling.dramatis.aldred-fellblade", "Q159"),
    ("hireling.dramatis.aldred-fellblade.rule.fellblade", "hireling.dramatis.aldred-fellblade", "Q160"),
    ("hireling.dramatis.armen-abbas.rule.skills-physician", "hireling.dramatis.armen-abbas", "Q161"),
    ("hireling.dramatis.armen-abbas.rule.angel-wings", "hireling.dramatis.armen-abbas", ""),
    ("hireling.dramatis.snorri-nosebiter.rule.slayer-rules", "hireling.dramatis.snorri-nosebiter", "Q163"),
    ("hireling.dramatis.snorri-nosebiter.rule.drunk", "hireling.dramatis.snorri-nosebiter", ""),
    ("hireling.dramatis.snorri-nosebiter.rule.lucky", "hireling.dramatis.snorri-nosebiter", ""),
    ("hireling.hired-sword.black-orc-bodyguard.rule.i-said-shut-it", "hireling.hired-sword.black-orc-bodyguard", "Q164"),
    ("hireling.hired-sword.black-orc-bodyguard.rule.whose-da-man", "hireling.hired-sword.black-orc-bodyguard", ""),
    ("hireling.hired-sword.bog-hunter.rule.unholy-stink", "hireling.hired-sword.bog-hunter", ""),
    ("hireling.hired-sword.bog-hunter.rule.fenland-strider", "hireling.hired-sword.bog-hunter", ""),
    ("hireling.hired-sword.whaler.rule.marine-hunter", "hireling.hired-sword.whaler", "Q165"),
    ("hireling.hired-sword.whaler.rule.hardened", "hireling.hired-sword.whaler", ""),
    ("hireling.hired-sword.ogre-treasure-hunter.rule.diver", "hireling.hired-sword.ogre-treasure-hunter", ""),
    ("hireling.hired-sword.ogre-treasure-hunter.rule.fear", "hireling.hired-sword.ogre-treasure-hunter", ""),
    ("hireling.hired-sword.grave-warden.rule.immune-to-disease", "hireling.hired-sword.grave-warden", ""),
    ("hireling.hired-sword.grave-warden.rule.hardened", "hireling.hired-sword.grave-warden", ""),
    ("hireling.hired-sword.grave-warden.rule.gardener", "hireling.hired-sword.grave-warden", "Q166"),
    ("hireling.hired-sword.halfling-fence.rule.sham", "hireling.hired-sword.halfling-fence", "Q167"),
    ("hireling.hired-sword.halfling-pimp.rule.flesh-peddler", "hireling.hired-sword.halfling-pimp", ""),
    ("hireling.hired-sword.halfling-pimp.rule.playboy", "hireling.hired-sword.halfling-pimp", "Q168"),
    ("hireling.hired-sword.albino-stormvermin.rule.hardened", "hireling.hired-sword.albino-stormvermin", ""),
    ("hireling.hired-sword.norse-bearman-bodyguard.rule.shieldmaster", "hireling.hired-sword.norse-bearman-bodyguard", ""),
    ("hireling.hired-sword.norse-bearman-bodyguard.rule.bulwark", "hireling.hired-sword.norse-bearman-bodyguard", "Q169"),
    ("hireling.hired-sword.norse-bearman-bodyguard.rule.drunken", "hireling.hired-sword.norse-bearman-bodyguard", "Q170"),
    ("hireling.hired-sword.sister-of-sigmar.rule.blessing-of-sigmar", "hireling.hired-sword.sister-of-sigmar", "Q171"),
    ("hireling.hired-sword.sister-of-sigmar.rule.candle-tree", "hireling.hired-sword.sister-of-sigmar", "Q125"),
    ("hireling.hired-sword.midshipman.rule.pilot", "hireling.hired-sword.midshipman", "Q172"),
    ("hireling.hired-sword.midshipman.rule.rigger", "hireling.hired-sword.midshipman", ""),
    ("hireling.hired-sword.mariner-priest-of-manann.rule.prayers", "hireling.hired-sword.mariner-priest-of-manann", ""),
    ("hireling.hired-sword.mariner-priest-of-manann.rule.seafaring", "hireling.hired-sword.mariner-priest-of-manann", "Q173"),
    ("hireling.hired-sword.mariner-priest-of-manann.rule.marks-of-manann", "hireling.hired-sword.mariner-priest-of-manann", "Q174"),
    ("hireling.hired-sword.priest-of-morr-miracle-workers.rule.prayers", "hireling.hired-sword.priest-of-morr-miracle-workers", ""),
    ("hireling.hired-sword.priest-of-morr-miracle-workers.rule.strictures", "hireling.hired-sword.priest-of-morr-miracle-workers", ""),
    ("hireling.hired-sword.priest-of-morr-miracle-workers.rule.loner", "hireling.hired-sword.priest-of-morr-miracle-workers", ""),
    ("hireling.hired-sword.priest-of-morr-miracle-workers.rule.morrs-servant", "hireling.hired-sword.priest-of-morr-miracle-workers", "Q175"),
    ("hireling.hired-sword.priest-of-morr-miracle-workers.rule.marks-of-morr", "hireling.hired-sword.priest-of-morr-miracle-workers", ""),
    ("hireling.hired-sword.war-priestess-of-myrmidia.rule.prayers", "hireling.hired-sword.war-priestess-of-myrmidia", ""),
    ("hireling.hired-sword.war-priestess-of-myrmidia.rule.war-honed", "hireling.hired-sword.war-priestess-of-myrmidia", ""),
    ("hireling.hired-sword.war-priestess-of-myrmidia.rule.marks-of-myrmidia", "hireling.hired-sword.war-priestess-of-myrmidia", "Q176"),
    ("hireling.hired-sword.trickster-priest-of-ranald.rule.prayers", "hireling.hired-sword.trickster-priest-of-ranald", ""),
    ("hireling.hired-sword.trickster-priest-of-ranald.rule.strictures", "hireling.hired-sword.trickster-priest-of-ranald", ""),
    ("hireling.hired-sword.trickster-priest-of-ranald.rule.marks-of-ranald", "hireling.hired-sword.trickster-priest-of-ranald", "Q177"),
    ("hireling.hired-sword.priestess-of-shallya.rule.prayers", "hireling.hired-sword.priestess-of-shallya", ""),
    ("hireling.hired-sword.priestess-of-shallya.rule.strictures", "hireling.hired-sword.priestess-of-shallya", "Q178"),
    ("hireling.hired-sword.priestess-of-shallya.rule.mercy", "hireling.hired-sword.priestess-of-shallya", "Q179"),
    ("hireling.hired-sword.priestess-of-shallya.rule.marks-of-shallya", "hireling.hired-sword.priestess-of-shallya", "Q180"),
    ("hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.rule.prayers", "hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers", ""),
    ("hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.rule.marks-of-sigmar", "hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers", "Q181"),
    ("hireling.hired-sword.druid-priest-of-taal.rule.prayers", "hireling.hired-sword.druid-priest-of-taal", ""),
    ("hireling.hired-sword.druid-priest-of-taal.rule.strictures", "hireling.hired-sword.druid-priest-of-taal", ""),
    ("hireling.hired-sword.druid-priest-of-taal.rule.marks-of-taal", "hireling.hired-sword.druid-priest-of-taal", "Q182"),
    ("hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.prayers", "hireling.hired-sword.wolf-priest-of-ulric-miracle-workers", ""),
    ("hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.strictures", "hireling.hired-sword.wolf-priest-of-ulric-miracle-workers", "Q183"),
    ("hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.intense-rivals", "hireling.hired-sword.wolf-priest-of-ulric-miracle-workers", ""),
    ("hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.rule.marks-of-ulric", "hireling.hired-sword.wolf-priest-of-ulric-miracle-workers", ""),
    ("hireling.hired-sword.priest-of-verena.rule.prayers", "hireling.hired-sword.priest-of-verena", ""),
    ("hireling.hired-sword.priest-of-verena.rule.strictures", "hireling.hired-sword.priest-of-verena", ""),
    ("hireling.hired-sword.priest-of-verena.rule.marks-of-solkan", "hireling.hired-sword.priest-of-verena", "Q184"),
    ("hireling.hired-sword.crimashin.rule.infiltrate", "hireling.hired-sword.crimashin", ""),
    ("hireling.hired-sword.holy-man.rule.true-believer", "hireling.hired-sword.holy-man", "Q185"),
    ("hireling.hired-sword.holy-man.rule.skills", "hireling.hired-sword.holy-man", ""),
)

#: ``(spell id, band rule id, roll, difficulty, recipient clause)`` for the
#: five Commands of the partition, from ``lore.commands`` and the band rules.
COMMANDS = (
    ("spell.commands.raise-our-insignia", "wandering-knight--command-raise-our-insignia", "1", 6, 'within 12"'),
    ("spell.commands.move-ye-miscreant", "wandering-knight--command-move-ye-miscreant", "2", 6, 'within 6"'),
    ("spell.commands.follow-me-mine-pugnacious-ones", "wandering-knight--command-follow-me-mine-pugnacious-ones", "3", 8, 'within 4"'),
    ("spell.commands.be-on-guard-my-brave-ones", "wandering-knight--command-be-on-guard-my-brave-ones", "4", 7, 'within 12"'),
    ("spell.commands.art-thou-ready-to-die-fighting", "wandering-knight--command-art-thou-ready-to-die-fighting", "6", 8, 'within 4"'),
)

#: The sixth Command affects missile target selection and is outside the melee matrix.
EXCLUDED_COMMAND = "spell.commands.pay-them-no-heed"

def _walk(node):
    if isinstance(node, dict):
        if isinstance(node.get("id"), str):
            yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _find_node(document, node_id):
    return next((node for node in _walk(document) if node["id"] == node_id), None)


@lru_cache(maxsize=None)
def _catalogue():
    return load_hirelings()


@lru_cache(maxsize=None)
def _magic():
    return load_campaign_catalog().catalogue("magic")


@lru_cache(maxsize=None)
def _band_index():
    profiles: dict[str, str] = {}
    rules: dict[str, str] = {}
    for collection in load_collections():
        for package in load_bands(str(collection["id"])):
            band_id = str(package.band.get("id") or "")
            for profile in package.profiles:
                profiles.setdefault(str(profile.get("id") or ""), band_id)
            for rule in package.special_rules:
                rules.setdefault(str(rule.get("id") or ""), band_id)
    return profiles, rules


@lru_cache(maxsize=None)
def _mazzalupo_package():
    for collection in load_collections():
        for package in load_bands(str(collection["id"])):
            if str(package.band.get("id")) == "mazzalupo-web":
                return package
    raise AssertionError("mazzalupo-web band package not found")


# Canonical command boundary


def test_sixth_command_stays_outside_the_melee_command_matrix():
    assert EXCLUDED_COMMAND not in {spell for spell, *_ in COMMANDS}
    lore = _lore_commands()
    assert EXCLUDED_COMMAND in {spell["id"] for spell in lore["spells"]}


# Hireling origins: canonical node and published catalogue resolution


@pytest.mark.parametrize(("origin", "owner", "_question"), HIRELING_ORIGINS)
def test_hireling_origin_resolves_to_its_canonical_rule_node(origin, owner, _question):
    document = next(profile for profile in _catalogue().profiles if profile.get("id") == owner)
    node = _find_node(document, origin)
    assert node is not None, origin
    assert node["name"].strip(), origin
    assert node["effect"].strip(), origin
    runtime = node["runtime"]
    assert runtime["scope"] in {"YES", "NO", "LATER"}, origin
    assert (runtime["implemented"] == "YES") == (runtime["scope"] == "YES"), origin
    if runtime["scope"] == "YES":
        assert runtime_bindings(node), origin
    else:
        assert all(effect.get("reason") for effect in runtime["effects"]), origin


@pytest.mark.parametrize(("origin", "owner", "_question"), HIRELING_ORIGINS)
def test_hireling_origin_resolves_in_the_published_hireling_catalogue(origin, owner, _question):
    profile = next((row for row in _catalogue().profiles if row.get("id") == owner), None)
    assert profile is not None, owner
    assert profile["normalization_status"] == "normalized", owner
    assert profile["kind"] in {"hired-sword", "dramatis-personae"}, owner
    rule = next(
        (row for row in profile.get("rules") or () if row.get("id") == origin),
        None,
    )
    assert rule is not None, origin
    assert rule["effect"].strip(), origin


def test_no_hireling_profile_or_rule_is_part_of_band_construction():
    band_profiles, band_rules = _band_index()
    owners = {owner for _origin, owner, _q in HIRELING_ORIGINS}
    assert owners.isdisjoint(band_profiles)
    assert {origin for origin, _owner, _q in HIRELING_ORIGINS}.isdisjoint(band_rules)
    assert len(owners) == 25


def test_free_selection_build_does_not_apply_hireling_rules():
    # Aldred Fellblade's canonical characteristics (M4 WS6 BS4 S4 T4 W2 I4 A2 Ld8).
    # A free-selection build is not a canonical hireling construction; this
    # negative control only shows the profile's rules do not leak into the
    # custom build path, which never receives a hireling profile id.
    compiled = compile_fighter(
        FighterBuild(
            "mordheim",
            characteristics=Characteristics(6, 4, 4, 2, 4, 2, movement=4, leadership=8),
        )
    )
    assert compiled.fighter_id == "custom:custom"
    assert compiled.construction_tags == ()
    origins = {origin for origin, _owner, _q in HIRELING_ORIGINS}
    assert not origins.intersection(compiled.global_effects.tags)
    assert not any(tag.startswith("hireling.") for tag in compiled.global_effects.tags)


# Mazzalupo Commands: orders inside a spell-shaped catalogue


def _lore_commands():
    lore = next(
        (row for row in _magic().get("lores") or () if row.get("id") == "lore.commands"),
        None,
    )
    assert lore is not None, "lore.commands missing from the magic catalogue"
    return lore


def _band_rule(rule_id):
    return next(
        (rule for rule in _mazzalupo_package().special_rules if rule.get("id") == rule_id),
        None,
    )


@pytest.mark.parametrize(("spell_id", "_band_rule_id", "roll", "difficulty", "clause"), COMMANDS)
def test_command_origin_resolves_in_lore_commands(spell_id, _band_rule_id, roll, difficulty, clause):
    lore = _lore_commands()
    spell = next((row for row in lore["spells"] if row.get("id") == spell_id), None)
    assert spell is not None, spell_id
    assert spell["roll"] == roll, spell_id
    assert spell["difficulty"] == difficulty, spell_id
    assert clause in spell["effect"], spell_id


def test_commands_lore_separates_orders_from_spells():
    lore = _lore_commands()
    note = " ".join(lore["note"].split())
    assert "do not count as spells" in note
    assert "not a wizard" in note
    assert "recovery phase" in note
    assert 'within 6"' in note
    assert "one Command per turn" in note
    assert len(lore["spells"]) == 6  # the five included plus the excluded sixth


@pytest.mark.parametrize(("spell_id", "band_rule_id", "_roll", "difficulty", "_clause"), COMMANDS)
def test_command_band_rule_is_declared_out_of_scope_without_binding(spell_id, band_rule_id, _roll, difficulty, _clause):
    rule = _band_rule(band_rule_id)
    assert rule is not None, band_rule_id
    runtime = rule["runtime"]
    assert runtime["scope"] == "NO", band_rule_id
    assert runtime["implemented"] == "NO", band_rule_id
    assert runtime["grant"] == "profile", band_rule_id
    effects = runtime["effects"]
    assert len(effects) == 1, band_rule_id
    assert effects[0]["binding"] is None, band_rule_id
    assert "Out of scope" in effects[0]["reason"], band_rule_id
    assert runtime_bindings(rule) == (), band_rule_id
    assert rule["applies_to"]["profile_ids"] == [WANDERING_KNIGHT], band_rule_id
    assert rule["effect"].startswith(f"Difficulty: {difficulty}."), band_rule_id


def test_commands_gate_rule_declares_the_subsystem_out_of_scope():
    rule = _band_rule("wandering-knight--commands")
    assert rule is not None
    runtime = rule["runtime"]
    assert runtime["scope"] == "NO"
    assert runtime["implemented"] == "NO"
    assert runtime["grant"] == "profile"
    assert runtime_bindings(rule) == ()
    assert rule["applies_to"]["profile_ids"] == [WANDERING_KNIGHT]
    reason = runtime["effects"][0]["reason"]
    assert "Out of scope" in reason
    assert "Commands" in reason


def test_canonical_wandering_knight_compiles_without_command_effects():
    compiled = compile_fighter(
        FighterBuild("mordheim", collection=COLLECTION, band_id="mazzalupo-web", profile_id=WANDERING_KNIGHT)
    )
    assert compiled.fighter_id == "mazzalupo-web:wandering-knight"
    command_ids = {spell for spell, *_ in COMMANDS} | {band for _spell, band, *_ in COMMANDS}
    assert not command_ids.intersection(compiled.construction_tags)
    assert not any(tag.startswith("spell.commands.") for tag in compiled.global_effects.tags)
    assert not any("command" in tag for tag in compiled.global_effects.tags)


def test_wandering_knight_is_not_offered_commands_as_selectable_rules():
    build = FighterBuild("mordheim", collection=COLLECTION, band_id="mazzalupo-web", profile_id=WANDERING_KNIGHT)
    offered = {str(rule.get("id")) for rule in available_special_rules(build, None)}
    assert not offered.intersection({spell for spell, *_ in COMMANDS})
    assert not offered.intersection({band for _spell, band, *_ in COMMANDS} | {"wandering-knight--commands"})

@pytest.mark.parametrize('profile,weapon,off,armour', [
    ('albino-stormvermin', 'weapon.halberd', None, 'armour.heavy-armour'),
    ('norse-bearman-bodyguard', 'weapon.axe', 'defence.shield', 'armour.light-armour'),
    ('crimashin', 'weapon.dagger', 'weapon.sword', 'armour.no-armour'),
    ('holy-man', 'weapon.double-handed-weapon', None, 'armour.no-armour'),
])
def test_native_hireling_compiles_its_source_qualified_printed_kit(profile, weapon, off, armour):
    result = compile_fighter(FighterBuild('mordheim', band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.' + profile, main_weapon_id=weapon,
        off_hand_id=off, armour_id=armour))
    assert result.fighter_id.endswith('hireling.hired-sword.' + profile)
    assert weapon in result.main_weapon.tags
    if profile == 'crimashin':
        assert 'material.gromril' in result.main_weapon.tags
    elif profile == 'holy-man':
        assert result.main_weapon.strength_bonus == 2
        assert result.main_weapon.priority == -1 and result.main_weapon.two_handed
    elif profile == 'norse-bearman-bodyguard':
        assert result.off_hand.parry
        assert 'mechanic.centigor-drunken' in result.global_effects.tags


def test_native_kit_keeps_whole_choices_quantities_and_materials():
    base = dict(band_id='hirelings.hired-sword.2b', profile_id='hireling.hired-sword.black-orc-bodyguard',
                main_weapon_id='weapon.axe', off_hand_id='weapon.axe', armour_id='armour.heavy-armour')
    assert compile_fighter(FighterBuild('mordheim', **base))
    # The printed alternative is two axes OR a two-handed weapon, never their union.
    for options in ({'owned_item_ids': ('heavy_armour', 'helmet', 'axe')},
                    {'owned_item_ids': ('heavy_armour', 'helmet', 'axe', 'axe', 'two_handed_weapon')},
                    {'main_material_id': 'material.ithilmar'}):
        with pytest.raises(ValueError, match='complete legal printed kit'):
            compile_fighter(FighterBuild('mordheim', **base, **options))
    # Aldred's intrinsic clauses resolve (Righteous Fury, the Fellblade and the
    # excluded Destiny), so the same build compiles with its printed weapon.
    aldred = compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.2b',
        profile_id='hireling.dramatis.aldred-fellblade', main_weapon_id='weapon.double-handed-weapon'))
    assert aldred.main_weapon.two_handed and 'skill.righteous-fury' in aldred.global_effects.tags
