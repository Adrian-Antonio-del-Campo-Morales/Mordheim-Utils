"""T13 — printed construction/access recipients of the equipment lists.

Every expectation is a printed line of the canonical band package
(``equipment-access.yaml`` ``applies_to`` / ``special-rules.yaml``
``profile.equipment-restrictions``), read live from
``sources/knowledge/bands`` and decided by the shared module through the
embedded runtime.  The suite is deliberately representative rather than one
case per band:

* the recipients of a named line are offered to the named profile and to no
  other member of the same list (brood dagger, bosspole, Man Catcher, the
  Sacred Markings, the Feather Headdress, the Mare lance, the Beastmaster's
  Whip, the Elven Runestones, the Snake Whip, the Pirate Parrot, the Poisoned
  Darts);
* a printed prohibition that covers the whole warband refuses a direct
  selection, not merely an unreachable offer (the Human Pirates variant lines);
* a printed refusal carried by named profiles (the Clan Pestilens Rat Familiar
  Scroll bar) refuses those bearers while the printed exception stays legal;
* the accepted controls already in the KB survive (Mare heavy armour,
  Wood Elf Ithilmar).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import (call, configuration_context, construction_call,
                                               desktop_call, market_recipients, package_facts)
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
# The printed market bearers are the live KB facts of
# `catalog/campaign/trading-post.yaml`, never a fixture: the projection reads the
# same data the campaign market publishes.
CATALOGUE = {"packages": {}, "foreign_packages": {}, "mechanics": {}, "mappings": MAPPINGS,
             "skills": {}, "items": {}, "market_recipients": market_recipients(KNOWLEDGE)}


def row(band: str, profile_id: str) -> dict:
    """The canonical profile row of the loaded package, never a synthetic one."""
    for profile in PACKAGES[band].profiles:
        if str(profile["id"]) == profile_id:
            return profile
    raise AssertionError(f"{band} publishes no profile {profile_id}")


AFTER_CREATION = ("equipment.post-creation",)


def projected(band: str, profile_id: str, phase: tuple[str, ...] = ()) -> dict:
    """`ProfileFacts` of one canonical profile, decided by the shared module."""
    configured = call("configuredProfile", row(band, profile_id), list(phase)) if phase \
        else row(band, profile_id)
    return call("profileFacts", package_facts(PACKAGES[band]), configured, None, CATALOGUE)


def offers(band: str, profile_id: str, phase: tuple[str, ...] = ()) -> set[str]:
    return {str(offer["item_id"]) for offer in projected(band, profile_id, phase)["equipment_access"]}


def offers_after_creation(band: str, profile_id: str) -> set[str]:
    """Offers of the same profile outside the band's starting list."""
    return offers(band, profile_id, AFTER_CREATION)


def forbids(band: str, profile_id: str) -> set[str]:
    return {str(token) for token in projected(band, profile_id)["equipment_forbids"]}


# Informational codes report a pending KB fact; they never refuse a selection.
INFORMATIONAL = {"construction_clause_unstructured", "equipment_unknown_item", "skill_pending_special_list"}


def refusal(band: str, profile_id: str, item_id: str, item: dict | None,
            phase: tuple[str, ...] = ()) -> str | None:
    facts = projected(band, profile_id, phase)
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
    ("khemri-lahmian-brotherhood", "snake_whip", "lahmian-vampire", "necromancer"),
    ("lustria-dark-elves", "beastmaster_whip", "beastmaster", "corsairs"),
    ("lustria-high-elves", "elven_runestones", "loremaster", "sea-guard"),
    ("lustria-pirates", "parrot", "pirate-captain", "crew"),
    ("lustria-pygmies", "poisoned_darts", "pygmies", "great-headhunter"),
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


def test_the_undead_and_mootlander_lists_reach_their_own_profiles():
    """C04a reconciliation: the Necromancer's Undead list access and the Moot
    Elder's extra pistol already flow through the shared offer and its own
    printed recipient."""
    # `offers` resolves the raw list ids through this fixture's minimal mappings.
    assert "sword" in offers("undead", "necromancer")
    # Ghouls publish no list at all: their bones are intrinsic attacks.
    assert offers("undead", "ghouls") == set()

    def offered(band: str, profile_id: str) -> set[str]:
        """Concessions need the full catalogue, so this one goes through it."""
        return set(desktop_call("equipment",
            FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                         main_weapon_id="weapon.dagger"),
            KNOWLEDGE, package=PACKAGES[band], profile=row(band, profile_id)))

    assert "weapon.pistol" in offered("mootlanders", "moot-elder")
    # The extra pistol is the Moot Elder's own printed line, not the band's.
    assert "weapon.pistol" not in offered("mootlanders", "warriors")


def test_the_estalian_variant_keeps_the_heavy_armour_its_rules_add():
    """F074-pirate-variants: the Estalian line adds heavy armour to the printed
    Pirate Equipment List, while the profile entry keeps 'may not wear armour'
    for the other body armour of that same list."""
    estalian = dict(band_id="estalian-corsairs-sar", profile_id="captain")
    assert compile_fighter(FighterBuild("mordheim", **estalian,
                                        main_weapon_id="weapon.rapier",
                                        armour_id="armour.heavy-armour"))
    for armour in ("armour.light-armour", "armour.toughened-leathers"):
        with pytest.raises(ValueError, match="forbidden"):
            compile_fighter(FighterBuild("mordheim", **estalian,
                                         main_weapon_id="weapon.sword", armour_id=armour))
    # Hand-held defences stay selectable, exactly as for the sibling pirates.
    assert compile_fighter(FighterBuild("mordheim", **estalian,
                                        main_weapon_id="weapon.sword",
                                        off_hand_id="defence.shield"))


def test_the_promoted_ghoul_reaches_the_fallen_list_and_the_henchman_does_not():
    """The printed clause grants the Fallen equipment list to the promoted Hero
    only, so the unpromoted Ghoul carries nothing while the configured Hero
    reaches the list its own lines name."""
    assert offers("fallen-the-rel", "ghouls") == set()
    promoted = offers("fallen-the-rel", "ghouls", ("promotion.hero",))
    assert {"sword", "light_armour"} <= promoted
    # The list is the band's Heroes' list, so its own bearers keep it.
    for profile_id in ("revenant", "butcher", "scavengers"):
        assert "sword" in offers("fallen-the-rel", profile_id), profile_id
    # The offered set and the verdict agree: the Henchman's direct selection is
    # refused and the same selection compiles once the promotion is supplied.
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(FighterBuild("mordheim", band_id="fallen-the-rel", profile_id="ghouls",
                                     main_weapon_id="weapon.sword"))
    assert compile_fighter(FighterBuild("mordheim", band_id="fallen-the-rel", profile_id="ghouls",
                                        main_weapon_id="weapon.sword",
                                        variant_ids=("promotion.hero",)))


def test_the_maldred_mercenaries_use_the_mercenary_list_only_before_the_first_game():
    """The printed phase of `mercenaries--equipment-restrictions`: the Mercenary
    Equipment list is open before the first game and the Squire and Men-at-Arms
    Equipment Lists the profile declares replace it afterwards."""
    def equipment(variant_ids: tuple[str, ...] = (), profile_id: str = "mercenaries") -> set[str]:
        return set(desktop_call("equipment",
            FighterBuild("mordheim", band_id="disciples-of-maldred-mou", profile_id=profile_id,
                         main_weapon_id="weapon.dagger", variant_ids=variant_ids),
            KNOWLEDGE, package=PACKAGES["disciples-of-maldred-mou"],
            profile=row("disciples-of-maldred-mou", profile_id)))

    creation, afterwards = equipment(), equipment(("equipment.post-creation",))
    assert "weapon.morning-star" in creation
    assert "weapon.morning-star" not in afterwards
    assert "weapon.spear" in afterwards
    # Direct selection reads the same phase as the offer: the creation blade
    # compiles before the first game and is refused afterwards, while the
    # profile's own Squire list still compiles in that phase.
    compile_fighter(FighterBuild("mordheim", band_id="disciples-of-maldred-mou",
                                 profile_id="mercenaries", main_weapon_id="weapon.morning-star"))
    with pytest.raises(ValueError):
        compile_fighter(FighterBuild("mordheim", band_id="disciples-of-maldred-mou",
                                     profile_id="mercenaries", main_weapon_id="weapon.morning-star",
                                     variant_ids=("equipment.post-creation",)))
    compile_fighter(FighterBuild("mordheim", band_id="disciples-of-maldred-mou",
                                 profile_id="mercenaries", main_weapon_id="weapon.spear",
                                 variant_ids=("equipment.post-creation",)))
    # The clause belongs to the Mercenaries alone: a peer of the same band
    # keeps one access in both phases.
    assert equipment(profile_id="prophet") == equipment(("equipment.post-creation",), profile_id="prophet")


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


def test_the_rat_familiar_scroll_bar_refuses_its_non_sorcerer_bearers():
    """Clan Pestilens prints the refusal on three heroes; the Sorcerer is the exception."""
    scroll = {"kind": "trollheim-equipment", "mechanic_id": None, "tags": []}
    for profile_id in ("plague-priest", "plague-monks", "monk-initiates"):
        assert "rat_familiar_scroll" in forbids("lustria-clan-pestilens", profile_id), profile_id
        assert refusal("lustria-clan-pestilens", profile_id, "rat_familiar_scroll", scroll) \
            == "equipment_forbidden", profile_id
    assert "rat_familiar_scroll" not in forbids("lustria-clan-pestilens", "pestilens-sorcerer")
    assert refusal("lustria-clan-pestilens", "pestilens-sorcerer", "rat_familiar_scroll", scroll) is None
    # The same printed fact reaches the compiler, not only the projection: the
    # named bearers cannot own the scroll and the printed exception compiles.
    for profile_id in ("plague-priest", "plague-monks", "monk-initiates"):
        with pytest.raises(ValueError, match="forbidden"):
            compile_fighter(FighterBuild("mordheim", collection="trollheim",
                                         band_id="lustria-clan-pestilens", profile_id=profile_id,
                                         owned_item_ids=("rat_familiar_scroll",)))
    assert compile_fighter(FighterBuild("mordheim", collection="trollheim",
                                        band_id="lustria-clan-pestilens", profile_id="pestilens-sorcerer",
                                        owned_item_ids=("rat_familiar_scroll",)))


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


def test_the_middenheim_wolfcloak_reaches_only_the_heroes_of_that_variant():
    """'Wolfcloak — Middenheim Heroes only': one printed line, two selectors.

    The Mercenaries publish the background as a warband variant, so the
    printed recipient is the chosen option plus the printed profile kind: a
    Reikland Hero, an undeclared build and every Henchman of the same printed
    list stay without the line.
    """
    for profile_id in ("mercenary-captain", "champions", "youngbloods"):
        plain = offers_with("mercenaries", profile_id, ())
        assert "wolfcloak" not in plain, profile_id
        assert "sword" in plain, profile_id
        assert "wolfcloak" in offers_with("mercenaries", profile_id, ("middenheim",)), profile_id
        for other in ("reikland", "marienburg", "ostermark"):
            assert "wolfcloak" not in offers_with("mercenaries", profile_id, (other,)), (profile_id, other)
    for profile_id in ("warriors", "swordsmen"):
        declared = offers_with("mercenaries", profile_id, ("middenheim",))
        assert "wolfcloak" not in declared, profile_id
        assert "sword" in declared, profile_id


# --- supplied states: the warband's current leader ---------------------------
# A printed line whose recipient is a state instead of a starting profile is
# decided by the canonical condition the caller declares (`condition_ids`), the
# same fact the Norse Battle Tongue row reads through its
# `eligible_condition_ids`. The Red Teeth clause prints the exception ('May not
# select the Feather Headdress unless this model somehow becomes the warband
# leader'), so the headdress reaches the bearer that declares the state, stays
# refused for that same bearer without it, and the mandatory starting leader the
# printed note names keeps the line with no state supplied at all.
LEADER_STATE = "condition.current-warband-leader"


def state_build(band: str, profile_id: str, **options) -> FighterBuild:
    return FighterBuild("mordheim", collection="trollheim", band_id=band,
                        profile_id=profile_id, **options)


def offers_of(build: FighterBuild) -> set[str]:
    """Offers of one build through the transport the editor reads."""
    facts = desktop_call("profileFacts", build, KNOWLEDGE, package=PACKAGES[build.band_id],
                         profile=row(build.band_id, build.profile_id))
    return {str(offer["item_id"]) for offer in facts["equipment_access"]}


def decisions(build: FighterBuild, possession: tuple[str, ...]) -> list[dict]:
    """Whole-configuration verdicts of one supplied kit, as the editor asks them."""
    facts = configuration_context(build, PACKAGES[build.band_id],
                                  row(build.band_id, build.profile_id),
                                  possession=possession, slots={"main_weapon_id": "weapon.fist"},
                                  root=KNOWLEDGE)
    return list(construction_call("validateConstruction", build, facts, root=KNOWLEDGE))


def test_the_printed_leader_exception_reaches_the_bearer_that_declares_the_state():
    band = "lustria-savage-goblins"
    assert "feather_headdress" not in offers_of(state_build(band, "red-teeth"))
    assert "feather_headdress" in offers_of(state_build(band, "red-teeth",
                                                      condition_ids=(LEADER_STATE,)))
    # The mandatory starting leader keeps the line with no state supplied, and
    # the exception is not a per-band list: any model that declares the state
    # reaches the line the printed note reserves to the leader.
    assert "feather_headdress" in offers_of(state_build(band, "witch-doctor"))
    assert "feather_headdress" not in offers_of(state_build(band, "big-boss"))
    assert "feather_headdress" in offers_of(state_build(band, "big-boss",
                                                       condition_ids=(LEADER_STATE,)))


def test_the_leader_exception_decides_a_selection_and_keeps_the_clause_halves():
    band = "lustria-savage-goblins"
    leader = state_build(band, "red-teeth", condition_ids=(LEADER_STATE,))
    assert [issue["code"] for issue in decisions(state_build(band, "red-teeth"),
                                                 ("feather_headdress",))] == ["equipment_not_permitted"]
    assert decisions(leader, ("feather_headdress",)) == []
    # The other two printed halves keep their verdict for the same bearer: the
    # Sacrifice Dagger stays refused and a missile without Thrown Weapon does too.
    assert [issue["code"] for issue in decisions(leader, ("sacrifice_dagger",))] \
        == ["equipment_not_permitted"]
    assert [issue["code"] for issue in decisions(leader, ("short_bow",))] == ["equipment_forbidden"]


def test_the_leader_exception_reaches_the_compiled_kit():
    """The same supplied state decides the canonical compilation, not only the offer."""
    band = "lustria-savage-goblins"

    def compiled(profile_id: str, **options) -> object:
        return compile_fighter(FighterBuild("mordheim", collection="trollheim", band_id=band,
                                            profile_id=profile_id,
                                            owned_item_ids=("feather_headdress",), **options))

    with pytest.raises(ValueError, match="not on any equipment list"):
        compiled("red-teeth")
    assert compiled("red-teeth", condition_ids=(LEADER_STATE,))
    assert compiled("witch-doctor")


# --- band-wide prohibitions that name a catalogue entry ----------------------
# C02b: the same resolution the profile projection publishes as
# `equipment_forbid_items`, for the band-wide list. The Sartosan Pirates forbid
# the Estalian/Wasteland lines of the printed Human Pirates table, and `handgun`
# names a canonical record: the clause is expressed by that fact instead of
# being reported while another, legal item of the same bearer is selected.


def test_a_band_token_that_names_a_catalogue_entry_is_expressed_not_reported():
    captain = state_build("sartosan-pirates-sar", "captain", main_weapon_id="weapon.sword")
    assert decisions(captain, ("sword",)) == []
    assert [issue["code"] for issue in decisions(captain, ("handgun",))] == ["equipment_forbidden"]


def test_an_unanswered_band_token_stays_reported_and_a_resolved_one_does_not():
    """The resolution decides the report, never the refusal."""
    profile = {"band_id": "sartosan-pirates-sar", "profile_id": "captain", "fixed_equipment": [],
               "equipment_access": None, "equipment_forbids": [], "skill_access": [], "skill_lists": []}
    handgun = {"kind": "ranged-weapon", "mechanic_id": None, "tags": ["blackpowder"]}
    assert call("equipmentIssue", {"profile": profile, "item_id": "sword", "item": None,
                                   "band_forbids": ["handgun"], "band_forbid_items": []})["code"] \
        == "construction_clause_unstructured"
    assert call("equipmentIssue", {"profile": profile, "item_id": "sword", "item": None,
                                   "band_forbids": ["handgun"],
                                   "band_forbid_items": ["handgun"]}) is None
    assert call("equipmentIssue", {"profile": profile, "item_id": "handgun", "item": handgun,
                                   "band_forbids": ["handgun"],
                                   "band_forbid_items": ["handgun"]})["code"] == "equipment_forbidden"
    # A lookup that explicitly answered null is unresolved too. Check the
    # producer path, which must not publish it as a known catalogue item.
    build = state_build("sartosan-pirates-sar", "captain", main_weapon_id="weapon.sword")
    facts = configuration_context(build, PACKAGES[build.band_id],
                                  row(build.band_id, build.profile_id),
                                  possession=("sword",), slots={"main_weapon_id": "weapon.sword"},
                                  root=KNOWLEDGE)
    facts["band_forbids"] = ["unknown-c02b-item"]
    facts["items"]["unknown-c02b-item"] = None
    issues = construction_call("validateConstruction", build, facts, root=KNOWLEDGE)
    assert any(issue["code"] == "construction_clause_unstructured"
               and issue.get("rule_id") == "unknown-c02b-item" for issue in issues)


def test_the_middenheim_wolfcloak_refuses_a_direct_selection():
    """The same predicate backs the offer and a selection made outside it."""
    build = dict(band_id="mercenaries", profile_id="mercenary-captain",
                 main_weapon_id="weapon.dagger", owned_item_ids=("wolfcloak",))
    for variants in ((), ("reikland",)):
        with pytest.raises(ValueError, match="not on any equipment list"):
            compile_fighter(FighterBuild("mordheim", **build, variant_ids=variants))
    assert compile_fighter(FighterBuild("mordheim", **build, variant_ids=("middenheim",)))


# --- printed market bearers: catalog/campaign/trading-post.yaml -------------
# A printed buying clause that no band list gates reaches individual
# construction through the same projection: `market_recipients` carries the
# published bearer of each market entry to the shared module, so the named
# recipient keeps the item while every other member of that band loses the offer
# and a direct selection. Each selector is read where the source prints it —
# the band scope, the printed kinds (`Heroes`/`Henchmen`), the named profiles,
# the named denial and the capability — and the clause of one band's market
# never narrows a sibling band's list. A concession (Weapon Knowledge) never
# bypasses it, and a capability whose rule executes is carried by the build that
# selects it, so the printed requirement has a positive route rather than being
# reported by an unimplemented record.


def market_forbids(band: str, profile_id: str) -> set[str]:
    """Items the profile's list offers and the printed market bearer refuses."""
    return {str(row["item_id"]) for row in projected(band, profile_id).get("market_bearer_forbids", ())}


def market_clause(band: str, profile_id: str, item_id: str) -> str | None:
    """The printed clause that refuses one item for this profile, or None."""
    rows = projected(band, profile_id).get("market_bearer_forbids", ())
    return next((str(row["bearer"]) for row in rows if str(row["item_id"]) == item_id), None)


def test_a_printed_market_denial_reaches_the_named_bearer_only():
    """'Sold as Lance (entry lance); not available to Questing Knights'."""
    lance = {"kind": "close-combat-weapon", "mechanic_id": "weapon.lance", "tags": []}
    assert "lance_not_questing_knight" in offers("bretonnian-chapel-guard", "knights-errant")
    assert refusal("bretonnian-chapel-guard", "knights-errant", "lance_not_questing_knight", lance) is None
    assert "lance_not_questing_knight" not in offers("bretonnian-chapel-guard", "questing-knight")
    assert refusal("bretonnian-chapel-guard", "questing-knight", "lance_not_questing_knight", lance) \
        == "equipment_not_permitted"
    # The source's explicit Pilgrim and Bowmen lists include shortswords.
    # "Knights only" was an extraction error, not an overriding source rule.
    shortsword = {"kind": "close-combat-weapon", "mechanic_id": "weapon.sword", "tags": []}
    for profile_id in ("damsel", "squires", "battle-pilgrims", "bowmen"):
        assert "shortsword" in offers("bretonnian-chapel-guard", profile_id), profile_id
        assert market_clause("bretonnian-chapel-guard", profile_id, "shortsword") is None, profile_id
        assert refusal("bretonnian-chapel-guard", profile_id, "shortsword", shortsword) is None, profile_id
    for profile_id in ("questing-knight", "knights-errant"):
        assert "shortsword" not in offers("bretonnian-chapel-guard", profile_id), profile_id
        assert market_clause("bretonnian-chapel-guard", profile_id, "shortsword") is None, profile_id


def test_a_printed_market_bearer_kind_refuses_the_hero_and_keeps_the_henchman():
    """'Skink Henchmen only' arrives as the published kind, not as a profile list."""
    poison = {"kind": "poison", "mechanic_id": "poison.reptile-venom", "tags": []}
    assert "reptile_venom" in offers("lustria-lizardmen", "skink-braves")
    assert "reptile_venom" not in offers("lustria-lizardmen", "skink-priest")
    assert refusal("lustria-lizardmen", "skink-braves", "reptile_venom", poison) is None
    assert refusal("lustria-lizardmen", "skink-priest", "reptile_venom", poison) \
        == "equipment_not_permitted"
    # The band that prints the poison on its own list keeps its own line: the
    # published clause still refuses the heroes there.
    assert refusal("lizardmen-lus", "skink-great-crests", "reptile_venom", poison) \
        == "equipment_not_permitted"


def test_a_printed_market_bearer_speaks_for_its_band_and_no_sibling_band():
    """'Shadow Warrior Weavers only' is scoped to the band that publishes it.

    The same profile id is printed by three bands, and only the Shadow Warriors
    market names its Weaver, so the clause narrows that band's line alone: the
    Sons of Nagarythe and the Lustria High Elves keep the runestones their own
    printed lines offer.

    The Weaver is the bearer of the phase the band's own list prints ('Heroes
    only at warband creation; outside the starting list, Elven Runestones are
    available to Shadow Weavers only'), so the clause speaks where that list
    stops: at creation the authorized Heroes keep the runestones and outside it
    only the Weaver does.
    """
    stones = {"kind": "trollheim-equipment", "mechanic_id": None, "tags": []}
    starting = ("shadow-master", "shadow-walker", "shadow-weaver")
    for profile_id in starting:
        assert "elven_runestones" in offers("shadow-warriors", profile_id), profile_id
        assert refusal("shadow-warriors", profile_id, "elven_runestones", stones) is None, profile_id
        after = offers_after_creation("shadow-warriors", profile_id)
        assert ("elven_runestones" in after) == (profile_id == "shadow-weaver"), profile_id
    assert refusal("shadow-warriors", "shadow-master", "elven_runestones", stones,
                   phase=AFTER_CREATION) == "equipment_not_permitted"
    # The same phase reaches the compiler: the starting list compiles, and
    # outside it the named bearer is the Weaver alone.
    assert compile_fighter(FighterBuild("mordheim", band_id="shadow-warriors",
                                        profile_id="shadow-master",
                                        owned_item_ids=("elven_runestones",)))
    with pytest.raises(ValueError, match="not on any equipment list"):
        compile_fighter(FighterBuild("mordheim", band_id="shadow-warriors", profile_id="shadow-master",
                                     owned_item_ids=("elven_runestones",), variant_ids=AFTER_CREATION))
    for band, profile_id in (("chaos-streets-sons-of-nagarythe", "shadow-weaver"),
                             ("lustria-high-elves", "loremaster")):
        assert "elven_runestones" in offers(band, profile_id), (band, profile_id)
        assert "elven_runestones" not in market_forbids(band, profile_id), (band, profile_id)


def test_a_supplied_promotion_answers_the_printed_gnoblar_hero_kind():
    """'Common (Gnoblar Heroes Only)' is a printed kind of the gnoblar entries.

    The market publishes the two canonical gnoblar profiles the band prints and
    the kind the clause names, so a supplied promotion — the only way a gnoblar
    becomes a Hero — changes the answer, and no profile is invented for it.
    """
    assert market_recipients(KNOWLEDGE)["pigback_mount"][0]["profile_ids"] == ["gnoblar-fighters", "flingers"]
    for profile_id in ("gnoblar-fighters", "flingers"):
        assert "pigback_mount" not in offers_with("ogre-hunting-party-web", profile_id, ()), profile_id
        assert "pigback_mount" in offers_with("ogre-hunting-party-web", profile_id, ("promotion.hero",)), profile_id
    # The mount is the gnoblar line: an Ogre Hero of the same band keeps none.
    assert "pigback_mount" not in offers_with("ogre-hunting-party-web", "ogre-hunter", ("promotion.hero",))
    build = dict(band_id="ogre-hunting-party-web", profile_id="gnoblar-fighters",
                 owned_item_ids=("pigback_mount",))
    with pytest.raises(ValueError, match="not on any equipment list"):
        compile_fighter(FighterBuild("mordheim", **build))
    assert compile_fighter(FighterBuild("mordheim", **build, variant_ids=("promotion.hero",)))


CHOSEN = "band--marauder-special-skills-chosen-of-chaos"
AXE = {"kind": "close-combat-weapon", "mechanic_id": "weapon.double-handed-weapon", "tags": []}


def with_selection(band: str, profile_id: str, rule_ids: tuple[str, ...]) -> dict:
    """`ProfileFacts` of the canonical profile carrying the build's own selections."""
    build = FighterBuild("mordheim", band_id=band, profile_id=profile_id, special_rule_ids=rule_ids)
    return desktop_call("profileFacts", build, package=PACKAGES[band], profile=row(band, profile_id))


def test_a_printed_capability_is_a_requirement_and_never_a_default():
    """'Marauders of Chaos Heroes with the Chosen of Chaos skill only'.

    The capability is the band rule the source names, not a `skill.*` id, and the
    clause demands it: a bearer that does not carry it is refused, and the item
    is refused rather than granted while that rule has no executable
    construction contract. The selected capability reaches the same decision
    through the canonical projection, so a build that carries the rule keeps the
    axe the moment the record can execute.
    """
    facts = market_recipients(KNOWLEDGE)["great_axe"]
    assert facts[0]["required_rule_ids"] == [CHOSEN]
    assert not CHOSEN.startswith("skill."), "the printed capability keeps its rule identity"
    # Presence and absence of the printed requirement, decided directly.
    for capability, expected in (([], False), ([CHOSEN], True)):
        assert call("marketBearerAdmits", {
            "band_id": "marauders-of-chaos", "profile_id": "champions", "profile_type": "hero",
            "capability_ids": capability, "alternatives": facts}) is expected, capability
    # Absence on the canonical routes: no offer, and a direct selection refused
    # by the printed clause instead of granted by default.
    assert "great_axe" not in offers("marauders-of-chaos", "champions")
    assert refusal("marauders-of-chaos", "champions", "great_axe", AXE) == "equipment_not_permitted"
    with pytest.raises(ValueError, match="printed trading-post clause"):
        compile_fighter(FighterBuild("mordheim", band_id="marauders-of-chaos",
                                     profile_id="champions", owned_item_ids=("great_axe",)))
    # Presence: the build's own selected rule reaches `bearerCapabilities`, so
    # the projected offer and the acceptance both admit that same hero.
    granted = with_selection("marauders-of-chaos", "champions", (CHOSEN,))
    assert "great_axe" in {str(offer["item_id"]) for offer in granted["equipment_access"]}
    assert call("equipmentIssue", {"profile": granted, "item_id": "great_axe", "item": AXE}) is None
    # The rule executes as the selectable capability its printed text admits, so
    # the requirement has a canonical positive route: the same build that carries
    # the rule compiles with the axe, and every refusal above is preserved.
    chosen = compile_fighter(FighterBuild("mordheim", band_id="marauders-of-chaos", profile_id="champions",
                                         owned_item_ids=("great_axe",), special_rule_ids=(CHOSEN,)))
    assert chosen is not None
    # The selection adds no combat bonus of its own: without the axe the compiled
    # fighter is the printed profile, and the other half of the printed sentence
    # is already the recipient's own access ('uses the Hero equipment list, if he
    # does not already') while the campaign maximum stays out of construction.
    plain = compile_fighter(FighterBuild("mordheim", band_id="marauders-of-chaos", profile_id="champions"))
    selected = compile_fighter(FighterBuild("mordheim", band_id="marauders-of-chaos", profile_id="champions",
                                            special_rule_ids=(CHOSEN,)))
    assert selected.characteristics == plain.characteristics
    assert (selected.armour_save, selected.natural_armour_save) \
        == (plain.armour_save, plain.natural_armour_save)
    for profile_id in ("marauder-chieftain", "seer", "champions", "condemned"):
        assert row("marauders-of-chaos", profile_id)["equipment_lists"] == ["hero-equipment-list"], profile_id


def test_the_chaos_steed_prints_the_same_requirement_and_no_band_list_offers_it():
    """'Marauders with the Chosen of Chaos skill only'.

    The steed's printed bearer is the same capability, and no band list of either
    market offers the entry, so the requirement is decided by the market clause
    itself: absent, it refuses the item, and present it admits the bearer without
    simulating a mount or a purchase.
    """
    facts = market_recipients(KNOWLEDGE)["chaos_steed"]
    assert facts[0]["required_rule_ids"] == [CHOSEN]
    for band_id, profile_id in (("marauders-of-chaos", "champions"), ("cult-of-the-possessed", "mutants")):
        for capability, expected in (([], False), ([CHOSEN], True)):
            assert call("marketBearerAdmits", {
                "band_id": band_id, "profile_id": profile_id, "profile_type": "hero",
                "capability_ids": capability, "alternatives": facts}) is expected, (band_id, capability)
    assert "chaos_steed" not in offers("marauders-of-chaos", "champions")
    with pytest.raises(ValueError, match="not on any equipment list"):
        compile_fighter(FighterBuild("mordheim", band_id="marauders-of-chaos", profile_id="champions",
                                     owned_item_ids=("chaos_steed",)))
    # The bearer requirement is resolved by the same clause: the hero that carries
    # the capability is admitted, and the construction route still has no band
    # list to offer the steed from, so no mount and no purchase is simulated.
    with pytest.raises(ValueError, match="not on any equipment list"):
        compile_fighter(FighterBuild("mordheim", band_id="marauders-of-chaos", profile_id="champions",
                                     owned_item_ids=("chaos_steed",), special_rule_ids=(CHOSEN,)))


def test_the_canonical_construction_route_refuses_the_wrong_market_bearer():
    """`compile_fighter` meets the offer's verdict and names the printed clause."""
    wrong = [
        ("ogre-hunting-party-web", "trappers", "sharp_stuff", ()),
        # Weapon Knowledge reaches the Sister of Sigmar's unique candelabrum;
        # a concession is no alias around the printed bearer.
        ("hochland-bandits", "duelist", "arcane_candelabrum", ()),
    ]
    for band_id, profile_id, item_id, variants in wrong:
        with pytest.raises(ValueError, match="printed trading-post clause"):
            compile_fighter(FighterBuild("mordheim", band_id=band_id, profile_id=profile_id,
                                         owned_item_ids=(item_id,), variant_ids=variants))
    assert compile_fighter(FighterBuild("mordheim", band_id="shadow-warriors", profile_id="shadow-weaver",
                                        owned_item_ids=("elven_runestones",),
                                        variant_ids=("equipment.post-creation",)))
    assert compile_fighter(FighterBuild("mordheim", band_id="ogre-hunting-party-web",
                                        profile_id="gnoblar-fighters", owned_item_ids=("sharp_stuff",)))


# --------------------------------------------------------------------------- #
# 'Skaven Heroes may use any of the Skaven Special Skills in the rulebook
#  except for the Art of Silent Death' (Clan Mors printed 36 / Clan Skryre
#  printed 41).  The members are the rulebook entries the active KB already
#  publishes and executes for the rulebook Skaven band; the last member of the
#  table is refused by name instead of being granted.                         #
# --------------------------------------------------------------------------- #

SKAVEN_INHERITANCE = {
    "skaven-of-clan-mors-kaz": (
        ("claw-leader", "stormvermin", "mors-sorcerer", "young-claws"),
        ("clanrats", "skavenslaves", "rat-ogre"),
    ),
    "skaven-of-clan-skryre-kaz": (
        ("master-engineer", "engineers", "warlock-engineer", "engineer-apprentices"),
        ("clanrats", "skavenslaves"),
    ),
}
# The rulebook Skaven special-skill table, minus the member the clause excludes.
RULEBOOK_SKAVEN_SKILLS = (
    "band--skaven-special-skills-black-hunger",
    "band--skaven-special-skills-tail-fighting",
    "band--skaven-special-skills-wall-runner",
    "band--skaven-special-skills-infiltration",
)
EXCLUDED_SKAVEN_SKILL = "band--skaven-special-skills-art-of-silent-death"


def offered_rules(band: str, profile_id: str) -> set[str]:
    """Selectable band rules the shared module offers to one canonical profile."""
    return {str(rule) for rule in desktop_call(
        "specialRules", FighterBuild("mordheim", band_id=band, profile_id=profile_id),
        package=PACKAGES[band], profile=row(band, profile_id))}


def inherited_rule(band: str, rule_id: str) -> dict:
    return next(rule for rule in PACKAGES[band].special_rules if str(rule["id"]) == rule_id)


def test_the_rulebook_skaven_table_is_published_for_its_heroes_and_the_excluded_skill_is_refused():
    """The clause is one access list: four published members, one named denial.

    The printed recipients are the Heroes of the band, the members are the
    rulebook entries the KB already carries for the Skaven table, and the
    excluded fifth entry is published as no member: the shared module must not
    offer it and `compile_fighter` must refuse it, never grant it silently.
    """
    for band, (heroes, henchmen) in SKAVEN_INHERITANCE.items():
        rule = inherited_rule(band, "band--rulebook-inheritance")
        # The declared recipients of the printed access are the band's Heroes.
        assert rule["applies_to"]["profile_types"] == ["hero"], band
        assert rule["applies_to"].get("band") is True, band
        # The clause publishes the admitted list itself, not the special catalogue.
        access = [effect for effect in rule["runtime"]["effects"]
                  if (effect.get("binding") or {}).get("id") == "profile.skill-access"]
        assert len(access) == 1, band
        parameters = access[0]["binding"]["parameters"]
        assert parameters["category"] == "special", band
        assert tuple(parameters["skills"]) == RULEBOOK_SKAVEN_SKILLS, band
        # The named denial is recorded, and it names the excluded member.
        denial = [effect for effect in rule["runtime"]["effects"]
                  if effect["id"].endswith(".art-of-silent-death")]
        assert len(denial) == 1 and denial[0]["binding"] is None, band
        assert "Art of Silent Death" in denial[0]["reason"], band
        # Every published member names the same recipients in its own rule.
        for member in RULEBOOK_SKAVEN_SKILLS:
            published = inherited_rule(band, member)
            assert published["applies_to"]["profile_types"] == ["hero"], (band, member)
            assert published["applies_to"].get("band") is True, (band, member)
            assert published["runtime"]["grant"] == "selectable", (band, member)
        # Heroes are offered the four members, and the excluded entry is not.
        for hero in heroes:
            offered = offered_rules(band, hero)
            assert set(RULEBOOK_SKAVEN_SKILLS) <= offered, (band, hero)
            assert EXCLUDED_SKAVEN_SKILL not in offered, (band, hero)
            with pytest.raises(ValueError, match="special rule is not available"):
                compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=hero,
                                             special_rule_ids=(EXCLUDED_SKAVEN_SKILL,)))
        # Henchmen of the same band receive no member of the table.
        for henchman in henchmen:
            assert not set(RULEBOOK_SKAVEN_SKILLS) & offered_rules(band, henchman), (band, henchman)
            with pytest.raises(ValueError, match="special rule is not available"):
                compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=henchman,
                                             special_rule_ids=(RULEBOOK_SKAVEN_SKILLS[1],)))
        # The printed recipient is the current Hero role, including a supplied
        # promotion, rather than a closed list of starting Hero archetypes.
        promoted = FighterBuild("mordheim", band_id=band, profile_id="clanrats",
            variant_ids=("promotion.hero",), special_rule_ids=(RULEBOOK_SKAVEN_SKILLS[1],),
            extra_hand_id="weapon.sword")
        assert compile_fighter(promoted) is not None, band
        with pytest.raises(ValueError, match="special rule is not available"):
            compile_fighter(FighterBuild("mordheim", band_id=band, profile_id="clanrats",
                variant_ids=("promotion.hero",), special_rule_ids=(EXCLUDED_SKAVEN_SKILL,)))


def test_the_admitted_skaven_choices_reach_the_compiled_fighter_through_their_existing_contracts():
    """Reused operators: the mechanic and the compiler contract of the table.

    Black Hunger compiles through `mechanic.black-hunger`, Tail Fighting enables
    the tail's extra hand through the compiler contract the rulebook band already
    uses, and the two members whose whole consequence is movement/deployment stay
    published while remaining outside the duel runtime. The declared Skaven
    equipment access of both bands is untouched.
    """
    for band, (heroes, _) in SKAVEN_INHERITANCE.items():
        hero = heroes[0]
        hunger = compile_fighter(FighterBuild(
            "mordheim", band_id=band, profile_id=hero,
            special_rule_ids=("band--skaven-special-skills-black-hunger",)))
        assert "mechanic.black-hunger" in hunger.skill_effects_only.tags, band
        plain = compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=hero))
        assert "mechanic.black-hunger" not in plain.skill_effects_only.tags, band
        # Tail Fighting is what admits the tail's extra hand, and nothing else is.
        tail = FighterBuild("mordheim", band_id=band, profile_id=hero, extra_hand_id="weapon.sword",
                            special_rule_ids=("band--skaven-special-skills-tail-fighting",))
        assert compile_fighter(tail) is not None
        with pytest.raises(ValueError, match="an extra hand requires"):
            compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=hero,
                                         extra_hand_id="weapon.sword"))
        # The out-of-scope members stay published and refuse a duel selection.
        for member in ("band--skaven-special-skills-wall-runner",
                       "band--skaven-special-skills-infiltration"):
            rule = inherited_rule(band, member)
            assert rule["runtime"]["implemented"] == "NO", (band, member)
            assert rule["runtime"]["grant"] == "selectable", (band, member)
            with pytest.raises(ValueError, match="outside the executable duel runtime"):
                compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=hero,
                                             special_rule_ids=(member,)))
    # The inherited weapon lists keep carrying the rulebook Skaven weapons.
    assert {"weeping_blades", "fighting_claws", "warp_pistol"} <= offers("skaven-of-clan-mors-kaz",
                                                                         "claw-leader")
    assert "jezzail" in offers("skaven-of-clan-skryre-kaz", "master-engineer")


# C02b — the Trollheim equipment clauses that name a catalogue entry beside a
# material or a weapon family.  The printed line names the entry
# (`beastmaster_whip`, `mage_staff`, `elven_runestones`, `sacrifice_dagger`), so
# the shared module decides it by the entry's own id instead of reporting the
# clause as one the KB does not express: the bearer's legal selection is decided
# by its list and records, the named entry is refused on direct selection and
# through inventory, and every half of a compound clause keeps its own verdict.
# --------------------------------------------------------------------------- #
C02B_CLAUSES = [
    # (band, bearer, [(prohibited entry, its canonical record)], legal entry, legal weapon)
    ("chaos-streets-undead-bloodlines", "lahmia-vampire",
     [("heavy_armour", {"kind": "armour", "mechanic_id": "armour.heavy-armour", "tags": []}),
      ("weapon.halberd", {"kind": "close-combat-weapon", "mechanic_id": "weapon.halberd",
                          "tags": [], "hands": 2})],
     "light_armour", "weapon.sword"),
    ("chaos-streets-undead-bloodlines", "necrarch-vampire",
     [("weapon.double-handed-weapon", {"kind": "close-combat-weapon",
                                        "mechanic_id": "weapon.double-handed-weapon", "tags": [],
                                        "hands": 2})],
     "sword", "weapon.sword"),
    ("khemri-tomb-guardians", "mortuary-acolytes",
     [("light_armour", {"kind": "armour", "mechanic_id": "armour.light-armour", "tags": []})],
     "mace", "weapon.mace"),
    ("lustria-dark-elves", "corsairs",
     [("beastmaster_whip", {"kind": "trollheim-equipment", "mechanic_id": None, "tags": []}),
      ("weapon.draich", {"kind": "close-combat-weapon", "mechanic_id": "weapon.draich", "tags": []})],
     "sword", "weapon.sword"),
    ("lustria-high-elves", "explorers",
     [("mage_staff", {"kind": "trollheim-equipment", "mechanic_id": None, "tags": []}),
      ("elven_runestones", {"kind": "out-of-scope", "mechanic_id": None, "tags": []})],
     "sword", "weapon.sword"),
    ("lustria-high-elves", "sea-guard",
     [("elven_runestones", {"kind": "out-of-scope", "mechanic_id": None, "tags": []})],
     "sword", "weapon.sword"),
    ("lustria-high-elves", "sword-guardians",
     [("elven_runestones", {"kind": "out-of-scope", "mechanic_id": None, "tags": []}),
      ("elf_bow", {"kind": "ranged-weapon", "mechanic_id": None, "tags": ["longbow"]})],
     "sword", "weapon.sword"),
    ("lustria-lizardmen", "skink-braves",
     [("weapon.sword", {"kind": "close-combat-weapon", "mechanic_id": "weapon.sword", "tags": []}),
      ("defence.helmet", {"kind": "defence", "mechanic_id": "defence.helmet", "tags": []})],
     "spear", "weapon.spear"),
    ("lustria-savage-goblins", "red-teeth",
     [("sacrifice_dagger", {"kind": "trollheim-equipment", "mechanic_id": None, "tags": []}),
      ("short_bow", {"kind": "ranged-weapon", "mechanic_id": None, "tags": ["bow"]})],
     "sword", "weapon.sword"),
]


def c02b_facts(band: str, profile_id: str) -> dict:
    """`ProfileFacts` of the bearer as the canonical list resolves it."""
    build = FighterBuild("mordheim", band_id=band, profile_id=profile_id, collection="trollheim")
    return desktop_call("profileFacts", build, KNOWLEDGE, package=PACKAGES[band],
                        profile=row(band, profile_id))


def c02b_build(band: str, profile_id: str, **kwargs) -> FighterBuild:
    return FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                        collection="trollheim", **kwargs)


def c02b_verdict(facts: dict, item_id: str, item: dict | None) -> str | None:
    issue = call("equipmentIssue", {"profile": facts, "item_id": item_id, "item": item})
    return str(issue["code"]) if issue else None


@pytest.mark.parametrize("band,profile,prohibited,legal,legal_weapon", C02B_CLAUSES,
                         ids=[f"{row[0]}:{row[1]}" for row in C02B_CLAUSES])
def test_a_trollheim_clause_naming_an_entry_is_expressed_by_that_entry(band, profile, prohibited,
                                                                      legal, legal_weapon):
    facts = c02b_facts(band, profile)
    # The clause is expressed: the legal selection is decided by the bearer's own
    # list and records, never reported as a clause the KB leaves without contract.
    assert c02b_verdict(facts, legal, None) in (None, "equipment_unknown_item"), legal
    # Every half of the compound clause is refused, by direct selection and by
    # the inventory the compiler receives.
    for item_id, item in prohibited:
        assert c02b_verdict(facts, item_id, item) in {"equipment_not_permitted",
                                                      "equipment_forbidden"}, item_id
        with pytest.raises(ValueError):
            compile_fighter(c02b_build(band, profile, owned_item_ids=(item_id,)))
    # The legal kit of the same bearer still compiles.
    assert compile_fighter(c02b_build(band, profile, main_weapon_id=legal_weapon))
