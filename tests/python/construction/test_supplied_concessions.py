"""The canonical band behind each supplied or printed concession.

The Commands were already executed on synthetic fighters by
``test_local_modifier_variants``; here the canonical Mazzalupo package must reach
them.  The Snotling teams and the Wheelo are one printed profile each, so their
single-model projection is the compiled participant itself.  The Machine-Ogre
fights with its own jaws and claws, while the 2D6 Customisation Chart is rolled
in the post-battle sequence and stays outside the duel.  The Prophet and the
Cleric keep their printed armour permission beside the excluded sermon/prayer
producers.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {(collection, str(package.band["id"])): package
            for collection in ("mordheim", "trollheim")
            for package in load_bands(collection, KNOWLEDGE)}
COMMANDS = ("follow-me-mine-pugnacious-ones", "art-thou-ready-to-die-fighting")


def profile_row(collection, band, profile_id):
    return next(row for row in PACKAGES[(collection, band)].profiles
                if str(row["id"]) == profile_id)


def unit(collection, band, profile_id, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                                        collection=collection, **options))


def offers(collection, band, profile_id):
    build = FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                         collection=collection)
    facts = desktop_call("profileFacts", build,
                         package=PACKAGES[(collection, band)],
                         profile=profile_row(collection, band, profile_id))
    return {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}


@pytest.mark.parametrize("command", COMMANDS)
def test_the_canonical_mazzalupo_band_reaches_both_supplied_commands(command):
    # The promoted package id is `mazzalupo-web`; the printed warband is its
    # canonical family, which is the recipient the compiler must accept.
    knight = unit("mordheim", "mazzalupo-web", "wandering-knight",
                  main_weapon_id="weapon.mace",
                  trait_overrides={"active_command": command})
    assert f"condition.command.{command}" in knight.global_effects.tags

    with pytest.raises(ValueError, match="Mazzalupo recipient"):
        unit("mordheim", "outlaws-of-stirwood-forest", "cleric",
             main_weapon_id="weapon.dagger",
             trait_overrides={"active_command": command})


def test_snotling_teams_are_one_printed_participant_without_extra_attacks():
    for profile_id, wounds, attacks in (("shoota-teams", 2, 2), ("snotling-mobs", 3, 3)):
        row = profile_row("mordheim", "snotlings-web", profile_id)
        fighter = unit("mordheim", "snotlings-web", profile_id,
                       main_weapon_id="weapon.fist")
        assert (fighter.characteristics.wounds, fighter.characteristics.attacks) == (wounds, attacks)
        assert fighter.extra_attacks == ()
        assert row["fixed_equipment"] == []
        # The printed rule is the projection itself: no extra per-Snotling model.
        rule = next(rule for rule in PACKAGES[("mordheim", "snotlings-web")].special_rules
                    if rule["id"] == f"{profile_id}--teamwork")
        assert rule["runtime"]["effects"][0]["id"] == "profile.single-model-projection"


def test_wheelo_crew_kit_is_the_printed_dagger_and_pebble_on_one_vehicle():
    row = profile_row("mordheim", "snotlings-web", "wheelo")
    assert row["fixed_equipment"] == ["dagger", "small_pebble"]
    # The individual participant is the vehicle, not a second crew model.
    wheelo = unit("mordheim", "snotlings-web", "wheelo", main_weapon_id="weapon.dagger")
    assert wheelo.fighter_id == "snotlings-web:wheelo"
    assert "weapon.dagger" in wheelo.main_weapon.tags
    assert "mechanic.wheelo-impact" in wheelo.global_effects.tags
    assert wheelo.extra_attacks == ()


def test_machine_ogre_fights_with_its_own_natural_attack_and_no_kit():
    profile = profile_row("mordheim", "metal-mongers-mim", "machine-ogre")
    assert profile["equipment_lists"] == [] and profile["fixed_equipment"] == []
    ogre = unit("mordheim", "metal-mongers-mim", "machine-ogre",
                main_weapon_id="weapon.fist")
    assert "weapon.natural-attacks" in ogre.main_weapon.tags
    assert (ogre.characteristics.strength, ogre.characteristics.attacks) == (5, 3)
    # Tinker-Rat customisation is the post-battle 2D6 chart: excluded, not a
    # duel binding, so the profile clause is not closed on its attack alone.
    chart = next(rule for rule in PACKAGES[("mordheim", "metal-mongers-mim")].special_rules
                 if rule["id"] == "band--customisation-chart")
    assert chart["runtime"]["scope"] == "NO"
    assert chart["runtime"]["effects"][0]["binding"] is None


@pytest.mark.parametrize("band,profile_id,armour", [
    ("chaos-streets-mordheim-inhabitants", "prophet", "toughened_leathers"),
    ("outlaws-of-stirwood-forest", "cleric", "light_armour"),
])
def test_the_printed_armour_permission_is_reachable_beside_the_excluded_producers(
        band, profile_id, armour):
    collection = "trollheim" if band.startswith("chaos-streets") else "mordheim"
    assert armour in offers(collection, band, profile_id)
    fighter = unit(collection, band, profile_id, main_weapon_id="weapon.dagger",
                   armour_id=f"armour.{armour.replace('_', '-')}")
    assert fighter.armour_save == 6
    # Neither producer is invented: the sermon stays deferred and the Cleric's
    # Prayer rule carries only its printed sorcery prohibition.
    rules = {rule["id"]: rule for rule in PACKAGES[(collection, band)].special_rules}
    if band.startswith("chaos-streets"):
        assert rules["band--revival-sermons"]["runtime"]["implemented"] == "NO"
    else:
        assert rules["cleric--disciple-of-sigmar"]["runtime"]["effects"][0]["binding"]["id"] == \
            "compiler.disciple-of-sigmar"
