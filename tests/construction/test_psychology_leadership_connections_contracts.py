"""Construction contracts split from the modular Psychology/Leadership connections.

These are the canonical-compiler contracts of
``tests/engines/modular/test_psychology_leadership_connections.py``: each one
proves that the printed band rule reaches the compiled profile of its recipient
and that an unselected or non-recipient build stays without it.  They keep the
canonical ``FighterBuild``/``compile_fighter`` path, so they belong with the
construction rules rather than with the engine execution suites.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest


def canonical(band, profile, *, collection="mordheim", rules=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", special_rule_ids=tuple(rules), **options))


def test_causes_fear_reaches_the_compiler():
    troll = canonical("chaos-streets-greenskins", "troll", collection="trollheim")
    assert "mechanic.causes-fear" in troll.global_effects.tags
    zombie = canonical("trollheim-undead", "zombies", collection="trollheim")
    assert "mechanic.causes-fear" in zombie.global_effects.tags
    # Negative control: a sibling build of the same band without the rule.
    orc = canonical("chaos-streets-greenskins", "orc-boyz", collection="trollheim")
    assert "mechanic.causes-fear" not in orc.global_effects.tags


def test_psychology_immunity_and_fear_immunity_are_distinct_recipients():
    golem = canonical("khemri-tomb-guardians", "stone-golem", collection="trollheim")
    assert "mechanic.psychology-immunity" in golem.global_effects.tags
    zombie = canonical("chaos-streets-undead-bloodlines", "zombie", collection="trollheim")
    assert "mechanic.psychology-immunity" in zombie.global_effects.tags
    blackheart = canonical("hochland-bandits", "blackhearts")
    assert "mechanic.fear-immunity" in blackheart.global_effects.tags
    # The immunity is the fear-only one, not the whole Psychology immunity.
    assert "mechanic.psychology-immunity" not in blackheart.global_effects.tags
    # Negative control: a living sibling of the same band.
    scorpion = canonical("khemri-tomb-guardians", "tomb-scorpions", collection="trollheim")
    assert "mechanic.psychology-immunity" not in scorpion.global_effects.tags


def test_selectable_fear_immunity_needs_its_selection():
    skill = "band--pit-fighter-skill-grizzled-veteran"
    selected = canonical("pit-fighters", "pit-king", rules=(skill,))
    assert "mechanic.psychology-immunity" in selected.global_effects.tags
    unselected = canonical("pit-fighters", "pit-king")
    assert "mechanic.psychology-immunity" not in unselected.global_effects.tags


def test_stupidity_and_frenzy_land_on_their_profiles():
    troll = canonical("chaos-streets-greenskins", "troll", collection="trollheim")
    assert "mechanic.stupidity" in troll.global_effects.tags
    goblin = canonical("forest-goblins-lus", "red-toof-clan-goblins")
    assert goblin.global_effects.frenzy
    assert not canonical("forest-goblins-lus", "forest-goblins").global_effects.frenzy


def test_handler_leadership_and_cold_blooded_reach_their_bands():
    monkey = canonical("lustrian-reavers", "barbary-monkey")
    assert "mechanic.handler-leadership" in monkey.global_effects.tags
    saurus = canonical("lustria-lizardmen", "saurus-braves", collection="trollheim")
    assert "mechanic.cold-blooded-psychology" in saurus.global_effects.tags
    # Negative control: another band's animal handler has no Cold Blooded.
    assert "mechanic.cold-blooded-psychology" not in monkey.global_effects.tags


def test_hatred_and_isolationists_reach_their_bands():
    slayer = canonical("pit-fighters", "dwarf-troll-slayer")
    assert "mechanic.hatred-orcs-goblins" in slayer.global_effects.tags
    amazon = canonical("lustria-amazons", "amazon-warriors", collection="trollheim")
    assert "mechanic.amazon-isolationists" in amazon.global_effects.tags


def test_undead_composite_and_its_living_negative_control():
    skeletons = canonical("khemri-lahmian-brotherhood", "skeleton-warriors",
                          collection="trollheim")
    assert "nature.undead" in skeletons.global_effects.tags
    assert "mechanic.causes-fear" in skeletons.global_effects.tags
    assert "mechanic.psychology-immunity" in skeletons.global_effects.tags
    # The living members of the same band are not Undead, which is exactly why
    # the band-wide aggregate stays out of scope.
    jackals = canonical("khemri-lahmian-brotherhood", "jackals", collection="trollheim")
    assert "nature.undead" not in jackals.global_effects.tags
    assert "mechanic.causes-fear" not in jackals.global_effects.tags


def test_leader_range_skills_widen_only_their_selected_bearer():
    power = "band--von-carstein-power-dark-majesty"
    assert "mechanic.leader-twelve" in canonical(
        "chaos-streets-undead-bloodlines", "von-carstein-vampire",
        collection="trollheim", rules=(power,)).global_effects.tags
    assert "mechanic.leader-twelve" not in canonical(
        "chaos-streets-undead-bloodlines", "von-carstein-vampire",
        collection="trollheim").global_effects.tags
