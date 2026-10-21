"""C02c: printed profile restrictions decide offer and compilation alike.

Every case drives the canonical package, the shared offer projection and the
compiler the application uses; a direct selection meets the same verdict as the
picker, and a printed exception keeps its own object.
"""
from __future__ import annotations

import pytest

from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild

pytestmark = pytest.mark.phase2_construction

COLLECTIONS = ("mordheim", "trollheim")
PACKS = {(collection, str(pack.band["id"])): pack
         for collection in COLLECTIONS for pack in combat_packages(collection)}


def collection_of(band):
    return next(collection for collection in COLLECTIONS
                if (collection, band) in PACKS)


def profile_of(band, profile_id):
    package = PACKS[(collection_of(band), band)]
    return next(row for row in package.profiles if row["id"] == profile_id)


def build(band, profile_id, **options):
    return FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                        collection=collection_of(band), **options)


def offered(band, profile_id, item_id, **options):
    package = PACKS[(collection_of(band), band)]
    return item_id in set(desktop_call(
        "equipment", build(band, profile_id, **options), package=package,
        profile=profile_of(band, profile_id)))


def test_a_profile_without_armour_hides_and_refuses_every_armour():
    assert not offered("kislevites", "esaul", "armour.light-armour")
    with pytest.raises(ValueError, match="armour is forbidden"):
        compile_fighter(build("kislevites", "esaul", armour_id="armour.light-armour"))


def test_khorne_armour_belongs_to_its_two_printed_bearers():
    for profile_id in ("dread-captain", "cannibal-boys", "plunderers", "madbrains"):
        assert not offered("khorne-raiders-sar", profile_id, "armour.light-armour")
        with pytest.raises(ValueError, match="armour-suit|armour"):
            compile_fighter(build("khorne-raiders-sar", profile_id,
                                  armour_id="armour.light-armour"))
    assert offered("khorne-raiders-sar", "quartermasters", "armour.light-armour")
    assert offered("khorne-raiders-sar", "flayerkin", "armour.light-armour")


def test_flayerkin_may_carry_only_its_hooks():
    assert not offered("khorne-raiders-sar", "flayerkin", "weapon.sword")
    with pytest.raises(ValueError, match="weapons"):
        compile_fighter(build("khorne-raiders-sar", "flayerkin",
                              main_weapon_id="weapon.sword"))


def test_the_strigoi_items_clause_is_not_a_weapon_only_clause():
    """The Vim-To vow admits only its printed staff and dagger."""
    assert not offered("nipponese-expedition-web", "vim-to-mage", "weapon.sword")
    with pytest.raises(ValueError, match="admits only"):
        compile_fighter(build("nipponese-expedition-web", "vim-to-mage",
                              main_weapon_id="weapon.sword"))
    assert offered("nipponese-expedition-web", "vim-to-mage", "weapon.club")
    assert compile_fighter(build("nipponese-expedition-web", "vim-to-mage",
                                 main_weapon_id="weapon.club"))


def test_the_morr_priest_keeps_dagger_and_scythe_and_no_armour():
    assert offered("vampire-hunters-of-sylvania-lotd5", "priest-of-morr", "weapon.dagger")
    assert offered("vampire-hunters-of-sylvania-lotd5", "priest-of-morr", "weapon.scythe")
    assert not offered("vampire-hunters-of-sylvania-lotd5", "priest-of-morr", "weapon.mace")
    compile_fighter(build("vampire-hunters-of-sylvania-lotd5", "priest-of-morr",
                          main_weapon_id="weapon.scythe"))
    with pytest.raises(ValueError, match="admits only"):
        compile_fighter(build("vampire-hunters-of-sylvania-lotd5", "priest-of-morr",
                              main_weapon_id="weapon.mace"))
    with pytest.raises(ValueError, match="armour is forbidden"):
        compile_fighter(build("vampire-hunters-of-sylvania-lotd5", "priest-of-morr",
                              armour_id="armour.light-armour"))


def test_black_orc_younguns_keep_legal_gear_and_recipient_exceptions():
    package = PACKS[("mordheim", "black-orcs")]

    def access(profile_id):
        facts = desktop_call(
            "profileFacts", build("black-orcs", profile_id), package=package,
            profile=profile_of("black-orcs", profile_id))
        return {row["item_id"] for row in facts["equipment_access"]}

    young = access("younguns")
    assert {"weapon.dagger", "weapon.axe", "weapon.sword", "weapon.spear"} <= young
    assert "weapon.double-handed-weapon" not in young
    assert "crossbow" not in young
    assert "weapon.double-handed-weapon" in access("orc-boyz")
    assert "weapon.double-handed-weapon" in access("orc-nuttaz")
    assert "crossbow" in access("orc-shootaz")
    assert compile_fighter(build("black-orcs", "younguns", main_weapon_id="weapon.axe"))
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build("black-orcs", "younguns",
                              main_weapon_id="weapon.double-handed-weapon"))


def test_knights_henchmen_refuse_missile_weapons_beyond_their_list():
    for profile_id in ("men-at-arms", "mounted-yeomen"):
        assert not offered("knights-of-the-bitter-moors-mim", profile_id, "weapon.pistol")
        with pytest.raises(ValueError, match="missile weapons are forbidden"):
            compile_fighter(build("knights-of-the-bitter-moors-mim", profile_id,
                                  main_weapon_id="weapon.pistol"))
        assert compile_fighter(build("knights-of-the-bitter-moors-mim", profile_id,
                                     main_weapon_id="weapon.sword"))


def test_corsairs_keep_the_sea_dragon_cloak_and_refuse_hero_only_gear():
    assert offered("lustria-dark-elves", "corsairs", "defence.sea-dragon-cloak")
    assert not offered("lustria-dark-elves", "corsairs", "poison.black-venom")
    with pytest.raises(ValueError, match="forbidden"):
        compile_fighter(build("lustria-dark-elves", "corsairs",
                              main_poison_id="poison.black-venom"))
    assert not offered("lustria-dark-elves", "corsairs", "weapon.draich")
    with pytest.raises(ValueError, match="forbidden"):
        compile_fighter(build("lustria-dark-elves", "corsairs",
                              main_weapon_id="weapon.draich"))
    assert compile_fighter(build("lustria-dark-elves", "corsairs",
                                 main_weapon_id="weapon.sword"))


def test_the_high_elf_drugs_and_poisons_clause_keeps_the_rest():
    with pytest.raises(ValueError, match="drugs are forbidden"):
        compile_fighter(build("lustria-high-elves", "loremaster",
                              preparation_ids=("preparation.mandrake-root",)))
    with pytest.raises(ValueError, match="poisons are forbidden"):
        compile_fighter(build("lustria-high-elves", "loremaster",
                              main_poison_id="poison.black-lotus"))
    for material in ("material.gromril", "material.obsidian"):
        with pytest.raises(ValueError, match="forbidden"):
            compile_fighter(build("lustria-high-elves", "loremaster",
                                  main_material_id=material))
    assert compile_fighter(build("lustria-high-elves", "loremaster",
                                 main_material_id="material.normal"))
