"""C02a: printed Mordheim equipment prohibitions meet one verdict everywhere.

Every case names a profile whose source prints an equipment clause, one item
the clause refuses and one item the same clause (or its printed exception)
leaves legal. The three construction surfaces read the same KB binding: the
picker offer, a directly selected slot and a carried kit.
"""
from pathlib import Path

import pytest

from mordheim_construction.compiler import _applicable_rules, compile_fighter
from mordheim_construction.eligibility import (
    call, configuration_context, construction_call, desktop_call, validate,
)
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands, runtime_bindings

pytestmark = pytest.mark.phase2_construction

ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"
PACKAGES = {str(package.band["id"]): package for package in load_bands("mordheim", ROOT)}
FORBIDDEN_CODES = {"equipment_forbidden", "equipment_combination_forbidden"}

CASES = [
    # Black Orc Nuttaz: 'never use any form of armour or ranged weapons'.
    {"band": "black-orcs", "profile": "orc-nuttaz",
     "refused": ["armour.light-armour", "crossbow"], "allowed": ["weapon.sword"]},
    # Halflings: the named big weapons, with the Village Ogre keeping its own list.
    {"band": "halflings-mic", "profile": "halfling-elder",
     "refused": ["long_bow"], "allowed": ["weapon.dagger"]},
    {"band": "halflings-mic", "profile": "village-ogre",
     "refused": [], "allowed": ["long_bow"]},
    # High Elves Sword Wardens: 'may never use missile weapons of any sort'.
    {"band": "high-elves-lus", "profile": "sword-wardens",
     "refused": ["crossbow"], "allowed": ["weapon.sword"]},
    # Khorne Raiders: Hooks only for Flayerkin, armour for Madbrains and Quartermasters.
    {"band": "khorne-raiders-sar", "profile": "flayerkin",
     "refused": ["weapon.sword"], "allowed": ["armour.light-armour"]},
    {"band": "khorne-raiders-sar", "profile": "madbrains",
     "refused": ["armour.light-armour"], "allowed": ["weapon.sword"]},
    {"band": "khorne-raiders-sar", "profile": "quartermasters",
     "refused": [], "allowed": ["armour.light-armour"]},
    # Daemon-Fimm: weapons refused, armour from the Heroes list kept.
    {"band": "lords-of-the-marsh-mim", "profile": "daemon-fimm",
     "refused": ["weapon.sword"], "allowed": ["armour.light-armour"]},
    # Vim-To Mage: 'a walking staff (club) and a dagger' and nothing else.
    {"band": "nipponese-expedition-web", "profile": "vim-to-mage",
     "refused": ["weapon.sword", "armour.light-armour"],
     "allowed": ["weapon.club", "weapon.dagger"]},
    # Savage Orcs: Nuttaz missile ban, Gobbo Boyz bow ban, Wierdo armour ban.
    {"band": "savage-orcs-kaz", "profile": "nuttaz",
     "refused": ["crossbow"], "allowed": ["weapon.club"]},
    {"band": "savage-orcs-kaz", "profile": "gobbo-boyz",
     "refused": ["bow"], "allowed": ["weapon.club"]},
    {"band": "savage-orcs-kaz", "profile": "weirdo",
     "refused": ["armour.light-armour"], "allowed": ["weapon.club"]},
    # Silent Brotherhood: blackpowder refused.
    {"band": "silent-brotherhood-sc", "profile": "brotherhood-agents",
     "refused": ["blunderbuss"], "allowed": ["weapon.sword"]},
    # Snotlings: Small Hands with the Shoota Team carve-out.
    {"band": "snotlings-web", "profile": "runts",
     "refused": ["blunderbuss", "armour.light-armour"], "allowed": ["weapon.dagger"]},
    {"band": "snotlings-web", "profile": "scouts",
     "refused": ["handgun"], "allowed": ["weapon.dagger"]},
    {"band": "snotlings-web", "profile": "shoota-teams",
     "refused": [], "allowed": ["blunderbuss"]},
    {"band": "snotlings-web", "profile": "bullied-goblin",
     "refused": ["elf_bow"], "allowed": ["weapon.dagger"]},
    # Strigoi Skeletons: no missile weapons.
    {"band": "strigoi-kaz", "profile": "skeletons",
     "refused": ["crossbow"], "allowed": ["weapon.sword"]},
    # Slayers: no armour, no constant-save cloak, no thrown-else missiles;
    # the printed Lucky Charm exception is not forbidden.
    {"band": "dwarf-slayer-cult-web", "profile": "giant-slayer",
     "refused": ["armour.light-armour", "bearcloak", "crossbow"],
     "allowed": [], "not_forbidden": ["lucky_charm"]},
    {"band": "dwarf-slayer-cult-web", "profile": "axe-hurlers",
     "refused": ["crossbow"], "allowed": ["weapon.dagger"]},
    # Ogre: heavy armour and the two named materials refused, light armour legal.
    {"band": "ogre-hunting-party-web", "profile": "ogre-hunter",
     "refused": ["armour.heavy-armour", "armour.ithilmar-armour", "armour.gromril-armour"],
     "allowed": ["armour.light-armour"]},
    # Dark Elves: the band-wide blackpowder disdain.
    {"band": "druchii-mic", "profile": "corsairs",
     "refused": ["blunderbuss"], "allowed": ["weapon.sword"]},
    {"band": "druchii-mic", "profile": "sorceress",
     "refused": ["weapon.pistol"], "allowed": ["weapon.sword"]},
]
IDS = [f"{case['band']}/{case['profile']}" for case in CASES]


def _rows(case):
    package = PACKAGES[case["band"]]
    row = next(profile for profile in package.profiles if profile["id"] == case["profile"])
    return package, row


def _slots(item):
    if item.startswith("armour."):
        return {"armour_id": item}
    if item == "bearcloak" or item == "lucky_charm":
        return {"defence_ids": [item]}
    return {"main_weapon_id": item}


def _bindings(package, row):
    return tuple(
        binding
        for rule in _applicable_rules(package, row)
        if (rule.get("runtime") or {}).get("grant") != "selectable"
        for binding in runtime_bindings(rule, "profile"))


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_the_picker_never_offers_an_item_the_printed_clause_refuses(case):
    package, row = _rows(case)
    build = FighterBuild("mordheim", band_id=case["band"], profile_id=case["profile"])
    offers = set(desktop_call("equipment", build, root=ROOT, package=package, profile=row))
    assert [item for item in case["refused"] if item in offers] == []


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_a_direct_selection_meets_the_same_refusal(case):
    package, row = _rows(case)
    bindings = _bindings(package, row)

    def decide(item):
        slots = _slots(item)
        build = FighterBuild("mordheim", band_id=case["band"], profile_id=case["profile"], **slots)
        try:
            validate("boundEquipment", build, root=ROOT, package=package, profile=row,
                     main_weapon_id=slots.get("main_weapon_id"), profile_bindings=bindings)
        except ValueError:
            return False
        return True

    for item in case["refused"]:
        assert not decide(item), f"{item} survives a direct selection"
    for item in case["allowed"] + case.get("not_forbidden", []):
        assert decide(item), f"{item} is refused by the printed clause"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_a_carried_kit_reads_the_prohibition_and_keeps_the_exception(case):
    package, row = _rows(case)

    def codes(item):
        slots = _slots(item)
        build = FighterBuild("mordheim", band_id=case["band"], profile_id=case["profile"], **slots)
        facts = configuration_context(build, package, row, possession=(item,), slots=slots)
        return {issue["code"] for issue in construction_call("validateConstruction", build, facts)
                if not call("issueIsInformational", issue["code"])}

    for item in case["refused"]:
        assert codes(item), f"{item} is not refused in a carried kit"
    for item in case.get("not_forbidden", []):
        assert not codes(item) & FORBIDDEN_CODES, f"{item} is refused by the printed clause"


def test_vim_to_mage_owns_only_the_walking_staff_and_dagger():
    package = PACKAGES["nipponese-expedition-web"]
    row = next(profile for profile in package.profiles if profile["id"] == "vim-to-mage")

    def blocking(item, slot):
        build = FighterBuild("mordheim", band_id="nipponese-expedition-web",
                             profile_id="vim-to-mage", owned_item_ids=(item,), **slot)
        facts = configuration_context(build, package, row, possession=(item,), slots=slot)
        return [issue["code"] for issue in construction_call("validateConstruction", build, facts)
                if not call("issueIsInformational", issue["code"])]

    assert blocking("weapon.club", {"main_weapon_id": "weapon.club"}) == []
    assert blocking("weapon.dagger", {"main_weapon_id": "weapon.dagger"}) == []
    for item, slot in (("weapon.sword", {"main_weapon_id": "weapon.sword"}),
                       ("armour.light-armour", {"armour_id": "armour.light-armour"}),
                       ("preparation.black-lotus", {})):
        assert blocking(item, slot), item


def test_black_orcs_never_ride_while_the_normal_orcs_keep_their_mount():
    package = PACKAGES["black-orcs"]

    def mounted(profile_id):
        row = next(profile for profile in package.profiles if profile["id"] == profile_id)
        build = FighterBuild("mordheim", band_id="black-orcs", profile_id=profile_id, mounted=True)
        try:
            validate("boundEquipment", build, root=ROOT, package=package, profile=row,
                     profile_bindings=_bindings(package, row))
        except ValueError:
            return False
        return True

    assert [profile for profile in ("black-orc-boss", "black-orcs", "orc-nuttaz") if mounted(profile)] == []
    assert all(mounted(profile) for profile in ("younguns", "orc-boyz", "orc-shootaz"))


def test_slayers_use_lucky_charms_and_keep_the_armour_and_cloak_ban():
    package = PACKAGES["dwarf-slayer-cult-web"]

    def offers(profile_id):
        row = next(profile for profile in package.profiles if profile["id"] == profile_id)
        build = FighterBuild("mordheim", band_id="dwarf-slayer-cult-web", profile_id=profile_id)
        return set(desktop_call("equipment", build, root=ROOT, package=package, profile=row))

    for profile in ("giant-slayer", "doomseeker", "troll-slayers", "stubbles", "axe-hurlers"):
        assert "defence.lucky-charm" in offers(profile), profile
        assert "armour.light-armour" not in offers(profile), profile
    # The Rememberer is expressly not a Slayer: armour stays and the exception does not reach him.
    assert "defence.lucky-charm" not in offers("rememberer")
    assert "armour.light-armour" in offers("rememberer")
    # The named exception is a selectable kit piece, not merely unforbidden text.
    fighter = compile_fighter(FighterBuild("mordheim", band_id="dwarf-slayer-cult-web",
                                           profile_id="giant-slayer",
                                           defence_ids=("defence.lucky-charm",)))
    assert fighter is not None
