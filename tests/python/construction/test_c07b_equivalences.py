"""C07b — printed weapon, armour and material equivalences in construction.

Each expectation is a printed line of the canonical KB read through the shared
module: the Snotlings' pointy stick is the dagger whose armour modifier belongs
to it, the Arcane Society's Travel Staff carries only the Balanced clause, the
Khemri bronze breastplate is Light Armour, the Sylvania shovel uses the halberd
profile, the Ironbreaker's kit is Gromril Armour, the Knight Errant upgrades the
light armour he prints, the Dwarf Axe and the Gromril allowance reach their Dwarf
lists, the Dark Steel weapon keeps the base weapon's own rules, and the Pristekk
special equipment reaches the packmasters who print it.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import (load_bands, load_items, load_mechanics,
                                      load_simulation_mappings)

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {(collection, str(package.band["id"])): package
            for collection in ("mordheim", "trollheim")
            for package in load_bands(collection, KNOWLEDGE)}
ITEMS = {str(item["id"]): item for item in load_items("mordheim", KNOWLEDGE)}
MAPPINGS = {str(row["item_id"]): row
            for row in load_simulation_mappings("mordheim", KNOWLEDGE)["item_mappings"]}


def profile_row(collection: str, band: str, profile_id: str) -> dict:
    return next(row for row in PACKAGES[(collection, band)].profiles if str(row["id"]) == profile_id)


def build(collection: str, band: str, profile_id: str, **options) -> FighterBuild:
    return FighterBuild("mordheim", band_id=band, profile_id=profile_id, collection=collection, **options)


def unit(collection: str, band: str, profile_id: str, **options):
    return compile_fighter(build(collection, band, profile_id, **options))


def offers(collection: str, band: str, profile_id: str) -> set:
    facts = desktop_call("profileFacts", build(collection, band, profile_id),
                         package=PACKAGES[(collection, band)], profile=profile_row(collection, band, profile_id))
    return {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}


def lines(collection: str, band: str, item_id: str) -> list:
    return [entry for equipment_list in PACKAGES[(collection, band)].equipment_lists
            for entry in equipment_list.get("items") or () if str(entry["item_id"]) == item_id]


ENGINE_OPTIONS = {str(row.get("engine_option")): str(row["id"])
                  for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons")
                  for row in load_mechanics("mordheim", KNOWLEDGE).get(family) or ()}


def mechanic(item_id: str):
    """The executable mechanic of an implemented item, declared or derived."""
    assert ITEMS[item_id]["combat_status"] == "implemented", item_id
    row = MAPPINGS[item_id]
    return row.get("mechanic_id") or ENGINE_OPTIONS.get(row.get("engine_option"))


@pytest.mark.parametrize("band", ["crooked-moon-kep", "night-goblins-kaz"])
def test_the_snotling_mob_fights_with_the_printed_pointy_stick_as_a_dagger(band):
    """The printed Dagger equivalence reaches the mob's own attack."""
    assert mechanic("pointy_stick") == "weapon.dagger"
    assert "pointy_stick" in {str(item) for item in profile_row("mordheim", band, "snotling-mob")["fixed_equipment"]}
    mob = unit("mordheim", band, "snotling-mob")
    assert "weapon.dagger" in mob.main_weapon.tags
    assert mob.main_weapon.target_armour_bonus == 1
    # It may only ever use that piece: nothing else is offered, and a direct
    # build with another weapon is refused rather than silently equipped.
    with pytest.raises(ValueError, match="equipment"):
        unit("mordheim", band, "snotling-mob", main_weapon_id="weapon.sword")
    assert offers("mordheim", band, "snotling-mob") == {"pointy_stick", "weapon.dagger"}


def test_the_travel_staff_reaches_its_spellcasters_with_only_the_balanced_clause():
    """Balanced is the +1 Initiative; the quarter staff's other properties stay its own."""
    assert mechanic("travel_staff") == "weapon.travel-staff"
    for profile_id in ("grand-wizard", "arcane-mage"):
        assert "travel_staff" in offers("trollheim", "chaos-streets-arcane-society", profile_id)
        staff = unit("trollheim", "chaos-streets-arcane-society", profile_id,
                     main_weapon_id="weapon.travel-staff")
        assert (staff.main_weapon.strength_bonus, staff.main_weapon.initiative_bonus) == (0, 1)
        assert not staff.main_weapon.parry and not staff.main_weapon.two_handed
    # The printed recipient line keeps the staff from the bodyguard.
    assert "travel_staff" not in offers("trollheim", "chaos-streets-arcane-society", "arcane-bodyguard")
    with pytest.raises(ValueError, match="not available"):
        unit("trollheim", "chaos-streets-arcane-society", "arcane-bodyguard",
             main_weapon_id="weapon.travel-staff")
    # The related Quarter Staff keeps the parry and the two-handed loadout this
    # fragment does not print, so no wholesale alias was inherited.
    quarter = next(row for row in load_items("mordheim", KNOWLEDGE) if str(row["id"]) == "quarter_staff")
    assert ITEMS["travel_staff"]["mechanic_id"] != quarter.get("mechanic_id")


def test_the_bronze_breastplate_is_the_printed_light_armour():
    """Counts as Light Armour: one 6+ save, not a second contribution."""
    assert mechanic("bronze_breastplate") == "armour.light-armour"
    assert "bronze_breastplate" in offers("trollheim", "khemri-tomb-guardians", "tomb-guardians")
    wearer = unit("trollheim", "khemri-tomb-guardians", "tomb-guardians", main_weapon_id="weapon.mace",
                  armour_id="armour.light-armour")
    assert wearer.armour_save == 6
    assert unit("trollheim", "khemri-tomb-guardians", "tomb-guardians",
                main_weapon_id="weapon.mace").armour_save == 7


def test_the_sylvania_shovel_uses_the_halberd_profile():
    """Both printed lines of the band carry the same equivalence."""
    assert mechanic("shovel") == "weapon.halberd"
    assert [line["notes"] for line in lines("mordheim", "grave-robbers-sylv", "shovel")] \
        == ["Counts as a Halberd", "Counts as a Halberd"]
    for profile_id in ("graver", "thugs"):
        assert "shovel" in offers("mordheim", "grave-robbers-sylv", profile_id)
        wielder = unit("mordheim", "grave-robbers-sylv", profile_id, main_weapon_id="weapon.halberd")
        assert "weapon.halberd" in wielder.main_weapon.tags
        assert (wielder.main_weapon.strength_bonus, wielder.main_weapon.two_handed) == (1, True)


def test_the_ironbreaker_and_the_gromril_allowance_reach_their_dwarf_lists():
    """The fixed kit is offered and the material composes its own -1."""
    assert mechanic("gromril_armour") == "armour.gromril-armour"
    assert "gromril_armour" in {str(item) for item in
                                profile_row("mordheim", "clan-angrund-kep", "ironbreaker")["fixed_equipment"]}
    assert "gromril_armour" in offers("mordheim", "clan-angrund-kep", "ironbreaker")
    armoured = unit("mordheim", "clan-angrund-kep", "ironbreaker", main_weapon_id="weapon.axe",
                    armour_id="armour.gromril-armour")
    assert armoured.armour_save == 4
    assert mechanic("dwarf_axe") == "weapon.dwarf-axe"
    for band, profile_id in (("clan-angrund-kep", "dwarf-clansmen"),
                             ("dwarf-guildsmen-kaz", "master-craftsman"),
                             ("dwarf-slayers-kaz", "slayers")):
        assert "dwarf_axe" in offers("mordheim", band, profile_id), (band, profile_id)
        wielder = unit("mordheim", band, profile_id, main_weapon_id="weapon.dwarf-axe")
        assert "weapon.dwarf-axe" in wielder.main_weapon.tags
        assert wielder.main_weapon.armour_penetration == 1
    gromril = unit("mordheim", "clan-angrund-kep", "dwarf-clansmen", main_weapon_id="weapon.axe",
                   main_material_id="material.gromril")
    assert "material.gromril" in gromril.main_weapon.tags
    assert gromril.main_weapon.armour_penetration == 2
    # The allowance is a Dwarf list line rather than a general purchase route.
    assert "material.gromril" in offers("mordheim", "clan-angrund-kep", "dwarf-clansmen")
    with pytest.raises(ValueError, match="not available"):
        unit("mordheim", "skaven-of-clan-pristekk-sc", "packmasters", main_weapon_id="weapon.axe",
             main_material_id="material.gromril")


def test_the_knight_errants_printed_armour_upgrade_composes_once():
    """Light armour becomes heavy armour; the two saves never stack."""
    row = profile_row("mordheim", "bretonnian-knights-errant-mou", "knights-errant")
    assert {"light_armour", "shield"} <= {str(item) for item in row["fixed_equipment"]}
    assert lines("mordheim", "bretonnian-knights-errant-mou", "heavy_armour")[0]["notes"] \
        == "Upgrade from Light Armour to Heavy Armour, +30 gc."
    printed = unit("mordheim", "bretonnian-knights-errant-mou", "knights-errant",
                   main_weapon_id="weapon.sword", armour_id="armour.light-armour")
    upgrade = unit("mordheim", "bretonnian-knights-errant-mou", "knights-errant",
                   main_weapon_id="weapon.sword", armour_id="armour.heavy-armour")
    assert (printed.armour_save, upgrade.armour_save) == (6, 5)


def test_the_dark_steel_weapon_keeps_the_base_weapons_own_rules():
    """The material is an operator on the base weapon, not a replacement profile."""
    assert mechanic("dark_steel_weapon") == "material.dark-steel"
    blade = unit("trollheim", "lustria-dark-elves", "corsairs", main_weapon_id="weapon.sword",
                 main_material_id="material.dark-steel")
    assert "material.dark-steel" in blade.main_weapon.tags
    assert blade.main_weapon.parry and blade.main_weapon.strength_bonus == 0


def test_the_pristekk_special_equipment_reaches_its_listed_bearers():
    """The three printed weapons are registered and their clauses reach the listed profile."""
    for item_id, mechanic_id in (("thinglash", "weapon.thinglash"),
                                 ("thing_catcher", "weapon.thing-catcher"),
                                 ("shock_rod", "weapon.shock-rod")):
        assert mechanic(item_id) == mechanic_id, item_id
    special = next(equipment_list
                   for equipment_list in PACKAGES[("mordheim", "skaven-of-clan-pristekk-sc")].equipment_lists
                   if str(equipment_list["id"]) == "special-clan-pristekk-equipment")
    printed = {str(entry["item_id"]): str(entry.get("notes")) for entry in special["items"]}
    assert "+1 enemy armour save; whipcrack; cannot be parried" in printed["thinglash"]
    assert "two-handed; capture animals and large models" in printed["thing_catcher"]
    assert "first strike" in printed["shock_rod"] and "two-handed" in printed["shock_rod"]
    for item_id in ("thinglash", "thing_catcher", "shock_rod"):
        assert item_id in offers("mordheim", "skaven-of-clan-pristekk-sc", "packmasters")
    lash = unit("mordheim", "skaven-of-clan-pristekk-sc", "packmasters", main_weapon_id="weapon.thinglash")
    assert (lash.main_weapon.strength_bonus, lash.main_weapon.target_armour_bonus) == (1, 1)
    assert lash.main_weapon.cannot_be_parried
    catcher = unit("mordheim", "skaven-of-clan-pristekk-sc", "packmasters", main_weapon_id="weapon.thing-catcher")
    assert catcher.main_weapon.two_handed
    rod = unit("mordheim", "skaven-of-clan-pristekk-sc", "packmasters", main_weapon_id="weapon.shock-rod")
    assert rod.main_weapon.two_handed and rod.main_weapon.priority == 1
