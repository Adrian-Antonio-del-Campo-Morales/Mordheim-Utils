"""C03d — recipients and legal combinations published by items and rules.

Every expectation is a printed line of the canonical KB, decided by the shared
module through the embedded runtime:

* the Skull Busta line declares the Orc recipients the printed text names, so
  the Goblin bearer is refused by the declared recipient and the combination
  rules still allow a shield while refusing another weapon or another hand;
* the Witch Elves' Black Lotus line declares its printed recipient while the
  general market route stays open to the other Druchii profiles;
* Huge Jaws reaches Saurus Heroes by configured species and role, so a supplied
  promotion of a Saurus Henchman qualifies and the Skink Heroes never do;
* the trident's "Priest of Manann only" line reaches that one hireling out of
  the whole hired-sword catalogue.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import build_facts, call, desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands


# Every case decides a declared recipient against its lawful control, so the
# primary category is admission, not the projection that carries it.
pytestmark = pytest.mark.eligibility

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {
    (collection, str(package.band["id"])): package
    for collection in ("mordheim", "trollheim")
    for package in load_bands(collection, KNOWLEDGE)
}
HIRELINGS = {str(package.band["id"]): package for package in combat_packages("mordheim")
             if str(package.band["id"]).startswith("hirelings.")}


def profile_row(collection: str, band: str, profile_id: str) -> dict:
    for profile in PACKAGES[(collection, band)].profiles:
        if str(profile["id"]) == profile_id:
            return profile
    raise AssertionError(f"{band} publishes no profile {profile_id}")


def line_of(collection: str, band: str, list_id: str, item_id: str) -> dict:
    for equipment_list in PACKAGES[(collection, band)].equipment_lists:
        if str(equipment_list["id"]) != list_id:
            continue
        for entry in equipment_list.get("items") or ():
            if str(entry["item_id"]) == item_id:
                return entry
    raise AssertionError(f"{band}/{list_id} publishes no line {item_id}")


def offered(collection: str, band: str, profile_id: str, variants=()) -> set:
    profile = profile_row(collection, band, profile_id)
    if variants:
        profile = call("configuredProfile", profile, list(variants))
    facts = desktop_call("profileFacts", FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                        collection=collection), package=PACKAGES[(collection, band)], profile=profile)
    return {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}


def fighter(collection: str, band: str, profile_id: str, **options) -> FighterBuild:
    return FighterBuild("mordheim", band_id=band, profile_id=profile_id, collection=collection, **options)


def test_skull_busta_recipients_and_combinations_are_read_from_the_declared_line():
    entry = line_of("mordheim", "savage-orcs-kaz", "savage-orc-equipment-list", "skull_busta")
    assert entry["applies_to"] == {"profile_ids": ["boss", "weirdo", "spottaz", "brutes", "nuttaz", "boyz"]}
    for profile_id in ("boss", "boyz", "nuttaz"):
        assert "skull_busta" in offered("mordheim", "savage-orcs-kaz", profile_id)
    assert "skull_busta" not in offered("mordheim", "savage-orcs-kaz", "gobbo-boyz")
    # The declared recipients are the fact the projection reads, not the notes.
    goblin = profile_row("mordheim", "savage-orcs-kaz", "gobbo-boyz")
    assert call("entryReachesProfile", entry, goblin) is False
    assert call("entryReachesProfile", entry,
                profile_row("mordheim", "savage-orcs-kaz", "boss")) is True
    with pytest.raises(ValueError, match="equipment is not available"):
        compile_fighter(fighter("mordheim", "savage-orcs-kaz", "gobbo-boyz",
                                main_weapon_id="weapon.skull-busta"))
    # Shields stay legal, another weapon and another hand do not: the shared
    # loadout predicate decides both hands, and no canonical bearer can gain an
    # extra hand for this item (its extra-hand providers are Skaven/Chaos rules).
    assert compile_fighter(fighter("mordheim", "savage-orcs-kaz", "boyz",
                                  main_weapon_id="weapon.skull-busta", off_hand_id="defence.shield"))
    with pytest.raises(ValueError, match="only be combined with shields"):
        compile_fighter(fighter("mordheim", "savage-orcs-kaz", "boyz",
                                main_weapon_id="weapon.skull-busta", off_hand_id="weapon.dagger"))
    with pytest.raises(ValueError, match="must be the main weapon"):
        compile_fighter(fighter("mordheim", "savage-orcs-kaz", "boyz",
                                main_weapon_id="weapon.dagger", off_hand_id="weapon.skull-busta"))
    predicate = {"main_weapon": {"main_hand": True}, "off_weapon": None, "contracts": [],
                 "selected_mechanics": []}
    for extra, message in (("weapon.dagger", "only be combined with shields"), ("defence.shield", None)):
        result = call("loadoutRestriction", {
            "build": build_facts(fighter("mordheim", "savage-orcs-kaz", "boyz",
                                         main_weapon_id="weapon.skull-busta", extra_hand_id=extra)),
            **predicate})
        assert (message in result) if message else result is None


def test_maibd_poison_recipient_keeps_the_route_open_for_the_market():
    entry = line_of("mordheim", "druchii-mic", "witch-elves-equipment-list", "black_lotus")
    assert entry["applies_to"] == {"profile_ids": ["witch-elves"]}
    assert "black_lotus" in offered("mordheim", "druchii-mic", "witch-elves")
    for profile_id in ("noble", "corsairs", "beastmaster"):
        assert "black_lotus" not in offered("mordheim", "druchii-mic", profile_id)
    # The dose bought on the open market is not turned into a universal ban.
    assert compile_fighter(fighter("mordheim", "druchii-mic", "witch-elves",
                                   main_weapon_id="weapon.dagger", main_poison_id="poison.black-lotus"))
    assert compile_fighter(fighter("mordheim", "druchii-mic", "noble",
                                   main_weapon_id="weapon.sword", main_poison_id="poison.black-lotus"))
    assert compile_fighter(fighter("mordheim", "druchii-mic", "noble",
                                   main_weapon_id="weapon.sword", main_poison_id="poison.black-venom"))


def test_huge_jaws_reaches_saurus_heroes_including_a_supplied_promotion():
    def selectable(profile_id: str, variants=()) -> list:
        profile = profile_row("trollheim", "lustria-lizardmen", profile_id)
        if variants:
            profile = call("configuredProfile", profile, list(variants))
        from mordheim_construction.eligibility import package_facts
        return call("selectableRuleOptions", package_facts(PACKAGES[("trollheim", "lustria-lizardmen")]), profile)

    mark = "band--sacred-mark-huge-jaws"
    assert mark in selectable("saurus-totem-warrior")
    assert mark in selectable("saurus-braves", ("promotion.hero",))
    assert mark not in selectable("saurus-braves")
    assert mark not in selectable("skink-priest")
    assert mark not in selectable("skink-braves", ("promotion.hero",))
    assert selectable("skink-priest").count("band--sacred-mark-venom-glands") == 1
    promoted = compile_fighter(fighter("trollheim", "lustria-lizardmen", "saurus-braves",
                                       variant_ids=("promotion.hero",), special_rule_ids=(mark,)))
    assert "huge_jaws" in promoted.global_effects.tags
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(fighter("trollheim", "lustria-lizardmen", "saurus-braves", special_rule_ids=(mark,)))
    for profile_id in ("skink-priest", "skink-braves"):
        with pytest.raises(ValueError, match="not available"):
            compile_fighter(fighter("trollheim", "lustria-lizardmen", profile_id,
                                    variant_ids=("promotion.hero",), special_rule_ids=(mark,)))


def test_the_priest_of_manann_line_reaches_that_one_hireling():
    reached = {}
    for band, package in HIRELINGS.items():
        for profile in package.profiles:
            facts = desktop_call("profileFacts", FighterBuild(
                "mordheim", band_id=band, profile_id=str(profile["id"]), collection="mordheim"),
                package=package, profile=profile)
            ids = {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}
            if ids & {"trident", "weapon.trident"}:
                reached[str(profile["id"])] = sorted(ids & {"trident", "weapon.trident"})
    assert sum(len(package.profiles) for package in HIRELINGS.values()) > 100
    # The line itself reaches the Priest of Manann alone; the Imperial Assassin's
    # trident is its own printed Weapons Master grant, not this line.
    assert reached == {"hireling.hired-sword.mariner-priest-of-manann": ["trident"],
                       "hireling.hired-sword.imperial-assassin": ["weapon.trident"]}
