"""H02 focal discriminators: printed kits and the variants they offer.

Each case reads the canonical route the package exposes: the offered item or
choice, the complete printed kit, `compile_fighter`, and the modular effect the
piece carries.  The shared eligibility engine is never bypassed.
"""
from __future__ import annotations

import pytest

from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.dice import ScriptedDice
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_combat.modular import psychology
from mordheim_combat.modular.contexts import prepare_wound_context
from mordheim_combat.modular.state import initialize_fighter
from mordheim_knowledge.campaign import load_campaign_catalog
from mordheim_knowledge.loader import load_items


def fighter(**options):
    return FighterBuild("mordheim", Characteristics(3, 4, 3, 2, 3, 1, leadership=7), **options)


def package(band_id):
    return next(row for row in combat_packages("mordheim") if row.band["id"] == band_id)


def offers(band_id, profile_id, **options):
    pack = package(band_id)
    build = fighter(band_id=band_id, profile_id=profile_id, **options)
    profile = next(row for row in pack.profiles if row["id"] == profile_id)
    return set(desktop_call("equipment", build, package=pack, profile=profile))


def hireling_kit(band_id, profile_id, **options):
    pack = package(band_id)
    build = fighter(band_id=band_id, profile_id=profile_id, **options)
    profile = next(row for row in pack.profiles if row["id"] == profile_id)
    return tuple(desktop_call("hirelingKit", build, package=pack, profile=profile))


# --- Dark Elf Corsairs: the shared printed kits ------------------------------

def test_the_sorceress_offers_and_carries_her_dark_elven_blade_and_dagger():
    assert offers("dark-elf-corsairs-mou", "sorceress") >= {
        "weapon.sword", "weapon.dagger", "material.dark-elf-blade"}
    sorceress = compile_fighter(fighter(band_id="dark-elf-corsairs-mou", profile_id="sorceress"))
    assert sorceress.main_weapon.tags[:2] == ("weapon.sword", "material.dark-elf-blade")
    assert sorceress.main_weapon.critical_injury_bonus == 1
    # The dagger beside the blade is its own copy, not a second dark elven blade.
    assert sorceress.off_hand.tags == ("weapon.dagger", "material.normal")


def test_the_beastmaster_offers_light_armour_blade_and_beastlash():
    assert offers("dark-elf-corsairs-mou", "beastmaster") >= {
        "armour.light-armour", "weapon.sword", "weapon.beastlash", "material.dark-elf-blade"}
    beastmaster = compile_fighter(fighter(
        band_id="dark-elf-corsairs-mou", profile_id="beastmaster",
        armour_id="armour.light-armour"))
    assert beastmaster.main_weapon.tags[:2] == ("weapon.sword", "material.dark-elf-blade")
    assert beastmaster.off_hand.tags == ("weapon.beastlash", "material.normal")
    assert beastmaster.armour_save == 6


# --- printed equipment choices ----------------------------------------------

def test_each_black_orc_option_compiles_as_a_whole_kit_and_the_alternatives_do_not_mix():
    axes = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.black-orc-overseer"))
    assert axes.main_weapon.tags == ("weapon.axe", "material.normal")
    double = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.black-orc-overseer",
        main_weapon_id="weapon.double-handed-weapon"))
    assert double.main_weapon.two_handed
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_fighter(fighter(
            band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.black-orc-overseer",
            off_hand_id="weapon.double-handed-weapon"))


def test_each_gaoler_option_compiles_and_two_flails_are_not_the_printed_pair():
    flail = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.gaoler"))
    assert flail.main_weapon.tags[0] == "weapon.flail"
    hammers = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.gaoler",
        main_weapon_id="weapon.mace", off_hand_id="weapon.club"))
    assert {hammers.main_weapon.tags[0], hammers.off_hand.tags[0]} == {"weapon.mace", "weapon.club"}
    assert hireling_kit("hirelings.hired-sword.1b", "hireling.hired-sword.gaoler",
                        owned_item_ids=("hammer", "club")) == ("hammer", "club")
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_fighter(fighter(
            band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.gaoler",
            off_hand_id="weapon.flail"))


def test_each_centaur_option_compiles_and_sword_does_not_mix_with_spear():
    sword = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1c", profile_id="hireling.hired-sword.chaos-centaur"))
    assert sword.main_weapon.tags[0] == "weapon.sword"
    spear = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1c", profile_id="hireling.hired-sword.chaos-centaur",
        main_weapon_id="weapon.spear"))
    assert spear.main_weapon.tags[0] == "weapon.spear"
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_fighter(fighter(
            band_id="hirelings.hired-sword.1c", profile_id="hireling.hired-sword.chaos-centaur",
            main_weapon_id="weapon.sword", off_hand_id="weapon.spear"))


def test_the_witch_hunter_kit_offers_either_pistol_and_carries_the_garlic():
    default = hireling_kit("hirelings.hired-sword.1b", "hireling.hired-sword.witch-hunter")
    assert "duelling_pistol" in default and "garlic" in default
    crossbow = ("sword", "dagger", "blessed_water", "garlic", "crossbow_pistol")
    chosen = compile_fighter(fighter(
        band_id="hirelings.hired-sword.1b", profile_id="hireling.hired-sword.witch-hunter",
        owned_item_ids=crossbow))
    assert chosen.main_weapon.tags[0] == "weapon.sword"
    carried = {entry.item_id for entry in chosen.mutation_equipment}
    assert "crossbow_pistol" in carried and "duelling_pistol" not in carried


# --- Johann: optional drug and the automatic coating ------------------------

def test_johanns_crimson_shade_is_optional_and_does_not_duplicate_the_lotus():
    plain = compile_fighter(fighter(
        band_id="hirelings.dramatis-personae.core", profile_id="hireling.dramatis.johann-the-knife"))
    assert plain.main_weapon.tags.count("poison.black-lotus") == 1
    assert "preparation.crimson-shade" not in plain.global_effects.tags
    assert "crimson_shade" not in hireling_kit(
        "hirelings.dramatis-personae.core", "hireling.dramatis.johann-the-knife")
    dosed = compile_fighter(fighter(
        band_id="hirelings.dramatis-personae.core", profile_id="hireling.dramatis.johann-the-knife",
        preparation_ids=("preparation.crimson-shade",)))
    assert "preparation.crimson-shade" in dosed.global_effects.tags
    assert dosed.main_weapon.tags.count("poison.black-lotus") == 1
    assert "crimson_shade" in hireling_kit(
        "hirelings.dramatis-personae.core", "hireling.dramatis.johann-the-knife",
        preparation_ids=("preparation.crimson-shade",))


# --- Countess Marianna: garlic coating against Vampires only ----------------

def test_the_garlic_coating_wounds_a_vampire_on_a_natural_six_and_no_one_else():
    countess = compile_fighter(fighter(
        band_id="hirelings.dramatis-personae.1a",
        profile_id="hireling.dramatis.countess-marianna-chevaux-vampire-assassin"))
    assert {"poison.black-lotus", "poison.vampires-only"} <= set(countess.main_weapon.tags)
    vampire = compile_fighter(fighter(trait_overrides={"vampire": True}))

    def lotus_wounds(defender):
        return prepare_wound_context(
            countess, defender,
            initialize_fighter(countess, ScriptedDice({}), "a"),
            initialize_fighter(defender, ScriptedDice({}), "d"),
            countess.main_weapon, countess.main_weapon, hit_roll=6).failure_still_wounds

    assert lotus_wounds(vampire)
    assert not lotus_wounds(compile_fighter(fighter()))


# --- Nicodemus: the two printed staff modes ---------------------------------

def nicodemus(**options):
    return compile_fighter(fighter(
        band_id="hirelings.dramatis-personae.1a",
        profile_id="hireling.dramatis.nicodemus-the-cursed-pilgrim", **options))


def test_the_staff_two_handed_mode_is_a_concussive_club_with_a_buckler_parry():
    staff = nicodemus()
    assert staff.main_weapon.tags[0] == "weapon.wizards-staff"
    assert staff.main_weapon.two_handed and staff.main_weapon.parry
    assert staff.main_weapon.concussion
    with pytest.raises(ValueError, match="complete legal printed kit|both hands"):
        nicodemus(off_hand_id="weapon.dagger")


def test_the_left_hand_mode_is_an_ordinary_one_handed_club_without_parry():
    club = nicodemus(main_weapon_id="weapon.club")
    assert club.main_weapon.tags[:2] == ("weapon.club", "weapon.mace")
    assert not club.main_weapon.two_handed and not club.main_weapon.parry


# --- particular objects -----------------------------------------------------

def test_the_ceremonial_scythe_is_the_priests_fixed_weapon_with_its_printed_grip():
    scythe = compile_fighter(fighter(
        band_id="hirelings.hired-sword.2b",
        profile_id="hireling.hired-sword.priest-of-morr-miracle-workers",
        main_weapon_id="weapon.ceremonial-scythe"))
    assert scythe.main_weapon.strength_bonus == 1
    assert scythe.main_weapon.two_handed
    with pytest.raises(ValueError, match="complete legal printed kit|both hands"):
        compile_fighter(fighter(
            band_id="hirelings.hired-sword.2b",
            profile_id="hireling.hired-sword.priest-of-morr-miracle-workers",
            main_weapon_id="weapon.ceremonial-scythe", off_hand_id="weapon.dagger"))


def test_the_beastlash_causes_fear_in_animals_and_not_in_other_opponents():
    hunter = compile_fighter(fighter(
        band_id="hirelings.hired-sword.2b", profile_id="hireling.hired-sword.bog-hunter"))
    animal = compile_fighter(fighter(trait_overrides={"normal_animal": True}))
    beastman = compile_fighter(fighter(trait_overrides={"species": "beastman"}))
    assert hunter.main_weapon.tags[0] == "weapon.beastlash"
    assert psychology.causes_fear(hunter, animal)
    assert not psychology.causes_fear(hunter, beastman)
    assert not psychology.causes_fear(
        compile_fighter(fighter(main_weapon_id="weapon.sword")), animal)


def test_the_candle_tree_relic_is_the_sisters_own_arcane_candelabrum():
    sister = compile_fighter(fighter(
        band_id="hirelings.hired-sword.2b", profile_id="hireling.hired-sword.sister-of-sigmar",
        special_rule_ids=("band--special-skills-sign-of-sigmar",
                          "band--special-skills-righteous-fury")))
    assert "defence.holy-relic" in sister.global_effects.tags
    assert "arcane_candelabrum" in {entry.item_id for entry in sister.mutation_equipment}


def test_the_bearman_starting_cloak_is_the_no_effect_mim_item_only_for_him():
    items = {row["id"]: row for row in load_items("mordheim")}
    assert items["wolf_cloak"].get("mechanic_id") is None
    assert items["wolf_cloak"].get("combat_status") == "out_of_scope"
    bear = compile_fighter(fighter(
        band_id="hirelings.hired-sword.2b", profile_id="hireling.hired-sword.norse-bearman-bodyguard",
        main_weapon_id="weapon.axe", off_hand_id="defence.shield",
        armour_id="armour.light-armour"))
    assert "wolf_cloak" in {entry.item_id for entry in bear.mutation_equipment}
    # Light armour and shield alone: the starting cloak carries no save.
    assert bear.armour_save == 5
    document = load_campaign_catalog("mordheim").catalogue("trading-post")
    cloak = next(row for row in document["items"]
                 if row.get("item_id") == "wolf_cloak")
    assert cloak["restrictions"][0]["structure"]["profile_ids"] == [
        "hireling.hired-sword.norse-bearman-bodyguard"]


# --- personas and general fixed equipment -----------------------------------

def test_luthors_selectable_persona_is_the_separate_normalized_looter_profile():
    rows = {row["id"]: row for row in package("hirelings.dramatis-personae.1c").profiles}
    wolfenbaum, looter = rows["hireling.dramatis.luthor-wolfenbaum"], rows["hireling.dramatis.luthor-the-looter"]
    assert wolfenbaum["normalization_status"] == "out_of_scope"
    assert not wolfenbaum.get("unresolved_references")
    assert looter["normalization_status"] == "normalized"
    assert "pistol" in {entry["item_id"] for entry in looter["hireling_equipment"]["fixed_items"]}
    assert compile_fighter(fighter(
        band_id="hirelings.dramatis-personae.1c",
        profile_id="hireling.dramatis.luthor-the-looter",
        main_weapon_id="weapon.sword", armour_id="armour.heavy-armour")).main_weapon.tags[0] == "weapon.sword"


def test_the_pair_keeps_its_identity_and_the_individual_warriors_are_their_own_profiles():
    rows = {row["id"]: row for row in package("hirelings.dramatis-personae.1a").profiles}
    pair = rows["hireling.dramatis.ulli-and-marquand"]
    assert pair["normalization_status"] == "out_of_scope"
    assert not pair.get("unresolved_references")
    assert rows["hireling.dramatis.ulli"]["normalization_status"] == "normalized"
    assert rows["hireling.dramatis.marquand"]["normalization_status"] == "normalized"


def test_the_horseman_is_not_dismounted_into_an_invented_profile():
    horseman = next(row for row in package("hirelings.dramatis-personae.2a").profiles
                    if row["id"] == "hireling.dramatis.the-headless-horseman")
    assert horseman["normalization_status"] == "out_of_scope"
    assert "characteristics" not in horseman
    assert "rider-and-mount" in horseman["out_of_scope_reason"]


def test_fixed_equipment_reaches_every_hireling_and_refuses_extra_ownership():
    warrior = compile_fighter(fighter(
        band_id="hirelings.hired-sword.2b", profile_id="hireling.hired-sword.priest-of-morr-miracle-workers",
        main_weapon_id="weapon.ceremonial-scythe"))
    assert "compiler.hireling-fixed-equipment" in warrior.construction_tags
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_fighter(fighter(
            band_id="hirelings.hired-sword.2b",
            profile_id="hireling.hired-sword.priest-of-morr-miracle-workers",
            main_weapon_id="weapon.ceremonial-scythe",
            owned_item_ids=("ceremonial_scythe", "dagger", "light_armour")))
