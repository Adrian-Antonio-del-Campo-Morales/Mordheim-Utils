"""Printed list dependencies: real recipients and existing item consumers."""
from pathlib import Path

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import call, package_facts
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands


ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"
PACKAGES = {p.band["id"]: p for p in load_bands("mordheim", ROOT)}


def facts(band, profile):
    package = PACKAGES[band]
    row = next(p for p in package.profiles if p["id"] == profile)
    return call("profileFacts", package_facts(package), row, None,
                {"packages": {}, "foreign_packages": {}, "mechanics": {},
                 "mappings": {}, "skills": {}, "items": {}})


def issue(band, profile, item, kind, mechanic=None):
    return call("equipmentIssue", {"profile": facts(band, profile), "item_id": item,
        "item": {"kind": kind, "mechanic_id": mechanic or item, "tags": []}})


def test_poison_daggers_keep_both_fanatic_recipients_and_black_lotus():
    for band in ("crooked-moon-kep", "night-goblins-kaz"):
        assert not issue(band, "fanatics", "poison_daggers", "close-combat-weapon",
                         "weapon.poisoned-daggers")
        assert issue(band, "night-goblins", "poison_daggers", "close-combat-weapon",
                     "weapon.poisoned-daggers")
        fighter = compile_fighter(FighterBuild("mordheim", band_id=band,
            profile_id="fanatics", main_weapon_id="weapon.poisoned-daggers"))
        assert fighter.main_weapon.paired
        assert "poison.black-lotus" in fighter.main_weapon.tags


def test_house_guard_pike_and_mare_vow_reach_their_existing_consumers():
    pike = compile_fighter(FighterBuild("mordheim", band_id="house-guard-sc",
        profile_id="pikemen", main_weapon_id="weapon.pike"))
    assert pike.main_weapon.two_handed and pike.main_weapon.priority == 1
    assert issue("house-guard-sc", "warhounds", "pike", "close-combat-weapon", "weapon.pike")
    assert not issue("order-of-the-mare-web", "gallant", "lance", "close-combat-weapon", "weapon.lance")
    assert issue("order-of-the-mare-web", "paragon", "lance", "close-combat-weapon", "weapon.lance")


def test_bearcloak_and_ogre_list_restrict_the_line_without_removing_other_lists():
    assert not issue("mazzalupo-web", "sheepherder", "bearcloak", "combat-equipment")
    assert issue("mazzalupo-web", "churl", "bearcloak", "combat-equipment")
    for item, kind, mechanic in (("helmet", "combat-equipment", "defence.helmet"),
                                 ("light_armour", "armour", "armour.light-armour")):
        assert not issue("pit-fighters", "ogre-pit-fighter", item, kind, mechanic)
        assert issue("pit-fighters", "dwarf-troll-slayer", item, kind, mechanic)
        assert not issue("pit-fighters", "pit-king", item, kind, mechanic)
    ogre = compile_fighter(FighterBuild("mordheim", band_id="pit-fighters",
        profile_id="ogre-pit-fighter", main_weapon_id="weapon.mace",
        armour_id="armour.light-armour", defence_ids=("defence.helmet",)))
    assert ogre.armour_save == 6
    assert "defence.helmet" in ogre.global_effects.tags
