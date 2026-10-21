"""The Town Crier 6 inheritance of the two Karak Azgal Dwarf bands.

The printed clause grants the referenced Dwarf rules to the band's Dwarfs,
apart from Incomparable Miners.  Three combat consequences are admitted:
Hard to Kill (the Dwarf injury chart), Hard Head (maces and clubs lose their
concussion) and Hatred of Orcs and Goblins.  Each is an automatic band grant,
never a skill the player buys, and it reaches only the Dwarfs: the Slayers'
Rememberer may be supplied as a Human, who keeps the Human line and therefore
receives none of the three.
"""
from __future__ import annotations

import pytest

from mordheim_combat.phases import Condition, injury_condition
from mordheim_combat.modular.contexts import _combined_effect, _hit_reroll, _injury_context
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import available_special_rules
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root, load_bands

ROOT = knowledge_root()
COLLECTION = "mordheim"
INHERITANCE = "band--town-crier-6-inheritance"
DWARF_RULES = ("skill.hard-to-kill", "concussion_immune", "mechanic.hatred-orcs-goblins")
ALL_DWARF_BANDS = ("dwarf-guildsmen-kaz", "dwarf-slayers-kaz")


def _package(band):
    return next(row for row in load_bands(COLLECTION, ROOT) if row.band["id"] == band)


def _profile_ids(band):
    return [str(profile["id"]) for profile in _package(band).profiles]


def _compiled(band, profile, **overrides):
    return compile_fighter(FighterBuild(COLLECTION, band_id=band, profile_id=profile, **overrides), ROOT)


@pytest.mark.parametrize("band", ALL_DWARF_BANDS)
@pytest.mark.compilation
def test_every_dwarf_member_inherits_the_admitted_rules_automatically(band):
    for profile in _profile_ids(band):
        unit = _compiled(band, profile)
        for tag in DWARF_RULES:
            assert tag in unit.global_effects.tags, (band, profile, tag)
            # The inheritance is one printed clause, so it contributes once.
            assert unit.global_effects.tags.count(tag) == 1, (band, profile, tag)
        # Nothing is offered as a choice: the old `selectable` declaration let a
        # player buy Hard to Kill as a skill instead of inheriting it.
        assert INHERITANCE not in available_special_rules(
            FighterBuild(COLLECTION, band_id=band, profile_id=profile), ROOT)


@pytest.mark.parametrize("band", ALL_DWARF_BANDS)
@pytest.mark.knowledge_integrity
def test_no_other_rule_of_the_band_grants_the_same_dwarf_rules(band):
    for rule in _package(band).special_rules:
        runtime = rule.get("runtime") or {}
        if rule["id"] == INHERITANCE:
            continue
        bound = {str((effect.get("binding") or {}).get("id"))
                 for effect in runtime.get("effects") or ()}
        assert not bound & set(DWARF_RULES), (band, rule["id"], bound & set(DWARF_RULES))


@pytest.mark.eligibility
def test_the_inheritance_cannot_be_selected_as_a_skill():
    build = FighterBuild(COLLECTION, band_id="dwarf-slayers-kaz", profile_id="giant-slayer",
                         special_rule_ids=(INHERITANCE,))
    with pytest.raises(ValueError, match="not selectable"):
        compile_fighter(build, ROOT)


@pytest.mark.compilation
def test_the_supplied_human_rememberer_keeps_the_human_line_without_dwarf_rules():
    for overrides, inherited in (({}, True), ({"species": "human"}, False)):
        unit = _compiled("dwarf-slayers-kaz", "rememberer", trait_overrides=overrides)
        for tag in DWARF_RULES:
            assert (tag in unit.global_effects.tags) is inherited, (overrides, tag)


@pytest.mark.rule_behavior
def test_the_inherited_rules_reach_their_modular_consumers():
    dwarf = _compiled("dwarf-guildsmen-kaz", "artisans")
    human = _compiled("dwarf-slayers-kaz", "rememberer", trait_overrides={"species": "human"})
    # Hard Head: the incoming mace keeps its concussion against a Human but not
    # against the Dwarf, so injury face 2 stays a knock-down only for the Dwarf.
    mace = _compiled("dwarf-guildsmen-kaz", "master-craftsman", main_weapon_id="weapon.mace")
    assert mace.main_weapon.concussion is True
    dwarf_state = initialize_fighter(dwarf, StrictDice([]), "dwarf")
    human_state = initialize_fighter(human, StrictDice([]), "human")
    dwarf_injury = _injury_context(dwarf, mace.main_weapon, "dwarf", dwarf_state)
    human_injury = _injury_context(human, mace.main_weapon, "human", human_state)
    assert dwarf_injury.hard_to_kill is True and dwarf_injury.concussion_immune is True
    assert human_injury.hard_to_kill is False and human_injury.concussion_immune is False
    assert injury_condition(2, dwarf_injury) == Condition.KNOCKED_DOWN
    assert injury_condition(2, human_injury) == Condition.STUNNED
    assert injury_condition(5, dwarf_injury) == Condition.STUNNED
    # Hatred: a missed attack re-rolls against Orcs and Goblins in the first
    # round only, and the Human Rememberer never inherits it.
    greenskin = compile_fighter(FighterBuild(COLLECTION, band_id="night-goblins-web",
        profile_id="night-goblin-warriors"), ROOT)
    effect = _combined_effect(dwarf, dwarf.main_weapon)
    assert _hit_reroll(dwarf, greenskin, dwarf.main_weapon, effect, True, False) is True
    assert _hit_reroll(dwarf, greenskin, dwarf.main_weapon, effect, False, False) is False
    assert _hit_reroll(human, greenskin, human.main_weapon,
                       _combined_effect(human, human.main_weapon), True, False) is False
