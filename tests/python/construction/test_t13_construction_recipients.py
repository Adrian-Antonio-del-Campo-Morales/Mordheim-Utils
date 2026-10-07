"""T13 — printed construction/access recipients of the equipment lists.

Every expectation is a printed line of the canonical band package
(``equipment-access.yaml`` ``applies_to`` / ``special-rules.yaml``
``profile.equipment-restrictions``), read live from
``sources/knowledge/bands`` and decided by the shared module through the
embedded runtime.  The suite is deliberately representative rather than one
case per band:

* the recipients of a named line are offered to the named profile and to no
  other member of the same list (brood dagger, bosspole, Man Catcher, the
  Sacred Markings, the Feather Headdress, the Mare lance);
* a printed prohibition that covers the whole warband refuses a direct
  selection, not merely an unreachable offer (the Human Pirates variant lines);
* the accepted controls already in the KB survive (Mare heavy armour,
  Wood Elf Ithilmar).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import call, package_facts
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {
    str(package.band["id"]): package
    for collection in ("mordheim", "trollheim")
    for package in load_bands(collection, KNOWLEDGE)
}

# Real ids under test; the transport resolves item ids through the catalogue
# mappings, so the fixture carries the mappings of the lines it reads.
MAPPINGS = {
    "dagger": "weapon.dagger",
    "rapier": "weapon.rapier",
    "heavy_armour": "armour.heavy-armour",
    "lance": "weapon.lance",
}
CATALOGUE = {"packages": {}, "foreign_packages": {}, "mechanics": {}, "mappings": MAPPINGS,
             "skills": {}, "items": {}}


def row(band: str, profile_id: str) -> dict:
    """The canonical profile row of the loaded package, never a synthetic one."""
    for profile in PACKAGES[band].profiles:
        if str(profile["id"]) == profile_id:
            return profile
    raise AssertionError(f"{band} publishes no profile {profile_id}")


def projected(band: str, profile_id: str) -> dict:
    """`ProfileFacts` of one canonical profile, decided by the shared module."""
    return call("profileFacts", package_facts(PACKAGES[band]), row(band, profile_id), None, CATALOGUE)


def offers(band: str, profile_id: str) -> set[str]:
    return {str(offer["item_id"]) for offer in projected(band, profile_id)["equipment_access"]}


def forbids(band: str, profile_id: str) -> set[str]:
    return {str(token) for token in projected(band, profile_id)["equipment_forbids"]}


# Informational codes report a pending KB fact; they never refuse a selection.
INFORMATIONAL = {"construction_clause_unstructured", "equipment_unknown_item", "skill_pending_special_list"}


def refusal(band: str, profile_id: str, item_id: str, item: dict | None) -> str | None:
    facts = projected(band, profile_id)
    issue = call("equipmentIssue", {"profile": facts, "item_id": item_id, "item": item})
    code = str(issue["code"]) if issue else None
    return None if code in INFORMATIONAL else code


# (band, printed line, the named recipient, a peer of the same list)
RECIPIENT_CASES = [
    ("brood-of-ghurash-the-sc", "dagger", "children", "broodmother"),
    ("forest-goblins-lus", "boss_pole", "chieftain", "shaman"),
    ("forest-goblins-lus", "boss_pole", "bosses", "forest-goblins"),
    ("underworld-alliance-mim", "man_catcher", "goblin-bully", "goblin-stinky-gits"),
    ("underworld-alliance-mim", "man_catcher", "skaven-slum-lord", "skaven-slave-champions"),
    ("lizardmen-lus", "oversized_jaws", "saurus-totem-warriors", "skink-priest"),
    ("lizardmen-lus", "poison_glands", "skink-priest", "saurus-totem-warriors"),
    ("lizardmen-lus", "poison_glands", "skink-great-crests", "saurus-braves"),
    ("lustria-savage-goblins", "feather_headdress", "witch-doctor", "big-boss"),
    ("lustria-savage-goblins", "feather_headdress", "witch-doctor", "red-teeth"),
]


@pytest.mark.parametrize("band,item,recipient,peer", RECIPIENT_CASES,
                         ids=[f"{row[0]}:{row[1]}:{row[2]}" for row in RECIPIENT_CASES])
def test_a_printed_recipient_reaches_its_profile_and_no_peer(band, item, recipient, peer):
    assert item in offers(band, recipient)
    assert item not in offers(band, peer)


def test_the_hero_only_sacred_marking_reaches_every_hero_and_no_henchman():
    for profile_id in ("skink-priest", "skink-great-crests", "saurus-totem-warriors"):
        assert "mark_of_the_old_ones" in offers("lizardmen-lus", profile_id), profile_id
    for profile_id in ("skink-braves", "saurus-braves"):
        assert "mark_of_the_old_ones" not in offers("lizardmen-lus", profile_id), profile_id


def test_the_mare_lance_is_knight_only_and_the_paragon_keeps_its_own_prohibition():
    for profile_id in ("gallant", "redeemed-knights"):
        assert "weapon.lance" in offers("order-of-the-mare-web", profile_id), profile_id
    # The Paragon is a Knight, but its own printed vow forbids the lance: the
    # restriction is a fact of its profile, not an artefact of the offer list.
    assert "weapon.lance" not in offers("order-of-the-mare-web", "paragon")
    assert "weapon.lance" in forbids("order-of-the-mare-web", "paragon")
    assert "weapon.lance" not in forbids("order-of-the-mare-web", "gallant")
    assert refusal("order-of-the-mare-web", "paragon", "weapon.lance",
                   {"kind": "close-combat-weapon", "mechanic_id": "weapon.lance", "tags": []}) is not None


def test_a_prohibited_direct_selection_is_refused_not_only_unreachable():
    """The Human Pirates base list prints the Estalian/Wasteland variant lines."""
    assert "weapon.rapier" in offers("sartosan-pirates-sar", "captain")
    assert refusal("sartosan-pirates-sar", "captain", "weapon.rapier",
                   {"kind": "close-combat-weapon", "mechanic_id": "weapon.rapier", "tags": []}) \
        == "equipment_forbidden"
    assert refusal("sartosan-pirates-sar", "captain", "armour.heavy-armour",
                   {"kind": "armour", "mechanic_id": "armour.heavy-armour", "tags": []}) \
        == "equipment_forbidden"
    assert refusal("sartosan-pirates-sar", "captain", "handgun",
                   {"kind": "ranged-weapon", "mechanic_id": None, "tags": ["blackpowder"]}) \
        == "equipment_forbidden"
    # The crossbow is the line the Estalian variant removes, so it stays legal here.
    assert refusal("sartosan-pirates-sar", "captain", "crossbow",
                   {"kind": "ranged-weapon", "mechanic_id": None, "tags": ["crossbow"]}) is None


def test_the_named_recipient_lines_refuse_a_direct_selection_of_a_peer():
    assert refusal("underworld-alliance-mim", "goblin-stinky-gits", "man_catcher",
                   {"kind": "close-combat-weapon", "mechanic_id": "weapon.man-catcher", "tags": []}) \
        == "equipment_not_permitted"
    assert refusal("lustria-savage-goblins", "red-teeth", "feather_headdress",
                   {"kind": "trollheim-equipment", "mechanic_id": None, "tags": []}) \
        == "equipment_not_permitted"
    assert refusal("brood-of-ghurash-the-sc", "broodmother", "weapon.dagger",
                   {"kind": "close-combat-weapon", "mechanic_id": "weapon.dagger", "tags": []}) \
        == "equipment_not_permitted"
    assert refusal("brood-of-ghurash-the-sc", "children", "weapon.dagger",
                   {"kind": "close-combat-weapon", "mechanic_id": "weapon.dagger", "tags": []}) is None


def test_the_applied_controls_are_preserved():
    """CLARIFIED-MARE-HEAVY-ARMOUR and CLARIFIED-WOOD-ELF-ITHILMAR."""
    for profile_id in ("paragon", "gallant", "redeemed-knights"):
        assert "armour.heavy-armour" in offers("order-of-the-mare-web", profile_id), profile_id
    assert "armour.heavy-armour" not in offers("order-of-the-mare-web", "pilgrims")
    for profile_id in ("hunt-master", "waywatcher", "forest-mage"):
        assert "ithilmar_weapon" in offers("wood-elves-of-athel-loren-web", profile_id), profile_id
        assert "ithilmar_armour" in offers("wood-elves-of-athel-loren-web", profile_id), profile_id
    for profile_id in ("deepwood-scout", "glade-guard"):
        assert "ithilmar_weapon" not in offers("wood-elves-of-athel-loren-web", profile_id), profile_id
        assert "ithilmar_armour" not in offers("wood-elves-of-athel-loren-web", profile_id), profile_id


# --- selection facts: House and Modus Operandi -----------------------------
# A printed line conditional on the build's selection reaches the profile only
# when the build declares it. `configuredProfile` carries the selection facts,
# so the shared `profileFacts` projection keeps reading one predicate.


# (printed line, the House it names) — house-guard-sc heroes-equipment-list.
HOUSE_LINES = {
    "rapier": "house.fierezza",
    "sword_breaker": "house.fierezza",
    "crossbow_pistol": "house.halcon",
    "long_bow": "house.halcon",
    "pavise": "house.baluardo",
    "house_guard_plate_armour": "house.baluardo",
}
SNIPER_LINES = {"crossbow", "long_bow"}


def offers_with(band: str, profile_id: str, variants: tuple[str, ...]) -> set[str]:
    """Offers of a profile configured with the build's declared selection facts."""
    configured = call("configuredProfile", row(band, profile_id), list(variants))
    return {str(offer["item_id"])
            for offer in call("profileFacts", package_facts(PACKAGES[band]), configured, None, CATALOGUE)["equipment_access"]}


def test_a_house_qualified_line_reaches_only_the_selected_house():
    plain = offers_with("house-guard-sc", "commander", ())
    assert set(HOUSE_LINES).isdisjoint(plain), "a House line needs the House selection"
    # An unqualified line of the same list stays offered to every House.
    assert "mace" in plain and "heavy_armour" in plain
    for token in ("house.fierezza", "house.halcon", "house.baluardo"):
        ids = offers_with("house-guard-sc", "commander", (token,))
        assert {line for line, house in HOUSE_LINES.items() if house == token} <= ids, token
        assert {line for line, house in HOUSE_LINES.items() if house != token}.isdisjoint(ids), token


def test_a_house_qualified_line_refuses_a_direct_selection_without_the_house():
    build = dict(band_id="house-guard-sc", profile_id="commander", main_weapon_id="weapon.rapier")
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(FighterBuild("mordheim", **build))
    assert compile_fighter(FighterBuild("mordheim", **build,
        trait_overrides={"house_guard_house": "fierezza"}))


def test_the_sniper_modus_operandi_reaches_only_the_specialised_hero():
    # The selection is not a standalone profile: without the Modus Operandi the
    # ranged lines stay unoffered, with it they reach the hero who chose it.
    for profile_id in ("poisoner", "assassins"):
        assert SNIPER_LINES.isdisjoint(offers_with("silent-brotherhood-sc", profile_id, ())), profile_id
        ids = offers_with("silent-brotherhood-sc", profile_id, ("modus-operandi.sniper",))
        assert SNIPER_LINES <= ids, profile_id
        # A different Modus Operandi does not grant the Sniper lines.
        other = offers_with("silent-brotherhood-sc", profile_id, ("modus-operandi.executor",))
        assert SNIPER_LINES.isdisjoint(other), profile_id
