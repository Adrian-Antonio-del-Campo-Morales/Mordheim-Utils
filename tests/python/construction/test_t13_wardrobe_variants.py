"""T13 wardrobe variants: the origin tunics' limit and the Eshin exception.

The three recovered entries are read from their own printed paragraphs:

* chaos-in-the-streets printed 159, Eshin Assassin Clothes: "los Ropajes de
  Asesino Eshin actuan exactamente igual que una Armadura Ligera,
  proporcionando una tirada de salvacion de 6+. No pueden combinarse con
  ninguna otra armadura excepto el casco."
* khemri printed 61 and chaos-in-the-streets printed 68, the two Tunicas de
  Mago: a 6+ armour save that "no se combinara con ninguna otra pieza de
  armadura" / "no puede combinar sus efectos con ninguna otra armadura".  No
  helmet is excepted in either paragraph, and both manuals list the Casco under
  Armaduras, so the helmet is refused as well.

The two tunics therefore carry origin-specific mechanics (`armour.mage-robes`,
`armour.wizard-robe`) while the generic `armour.wizard-s-robe` keeps the helmet
exception of its own source and no origin re-judges its bearers.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import call
from mordheim_core.models import FighterBuild

ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"

# band, profile, the origin mechanic its own item binds to
KHEMRI_TUNIC = ("khemri-mages", "archmage", "armour.mage-robes")
ARCANE_TUNIC = ("chaos-streets-arcane-society", "arcane-mage", "armour.wizard-robe")
ASSASSIN_ROBES = ("chaos-streets-deathbringers", "silent-hunter", "armour.eshin-assassin-robes")


def build(armour_id, **options):
    return {
        "band_id": "test-band", "profile_id": "hero", "variant_ids": [],
        "main_weapon_id": "weapon.mace", "armour_id": armour_id,
        "off_hand_id": "", "extra_hand_id": "", "defence_ids": [],
        "main_material_id": "material.normal", "off_material_id": "material.normal",
        "skill_ids": [], "special_rule_ids": [], "open_flame": False, **options,
    }


def loadout(armour_id, **options):
    """The shared hands-stage decision, with no catalogue and no dice."""
    return call("loadoutRestriction", {
        "build": build(armour_id, **options),
        "main_weapon": {"main_hand": True, "hands": 1, "paired": False},
        "off_weapon": None, "contracts": [], "selected_mechanics": [], "stage": "hands",
    })


def compile_with(band_id, profile_id, armour_id, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id, collection="trollheim",
        armour_id=armour_id, **options), ROOT)


def refusal(band_id, profile_id, armour_id, **options):
    with pytest.raises(ValueError) as error:
        compile_with(band_id, profile_id, armour_id, **options)
    return str(error.value)


# ---------------------------------------------------------------------------
# The shared rule itself: the two tunics refuse every other armour piece
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("armour_id", ["armour.mage-robes", "armour.wizard-robe"])
@pytest.mark.parametrize("other", ["defence.helmet", "defence.cooking-pot-helmet"])
def test_the_origin_tunics_refuse_another_defence_including_a_helmet(armour_id, other):
    assert loadout(armour_id, defence_ids=[other]) == (
        f"{armour_id} cannot be combined with any other armour")


@pytest.mark.parametrize("armour_id", ["armour.mage-robes", "armour.wizard-robe"])
@pytest.mark.parametrize("other", ["defence.shield", "defence.buckler", "defence.kite-shield"])
def test_the_origin_tunics_refuse_a_hand_held_armour_piece(armour_id, other):
    assert loadout(armour_id, off_hand_id=other) == (
        f"{armour_id} cannot be combined with any other armour")


@pytest.mark.parametrize("armour_id", ["armour.mage-robes", "armour.wizard-robe"])
def test_the_origin_tunics_alone_carry_their_six_plus_save(armour_id):
    assert loadout(armour_id) is None


# ---------------------------------------------------------------------------
# The other users keep their own printed limit
# ---------------------------------------------------------------------------
def test_the_generic_wizard_s_robe_still_admits_a_helmet():
    # Its own source prints "cannot combine with other armour except a helmet",
    # so the two origin variants must not re-judge it.
    assert loadout("armour.wizard-s-robe", defence_ids=["defence.helmet"]) is None
    assert loadout("armour.wizard-s-robe", off_hand_id="defence.shield") == (
        "armour.wizard-s-robe cannot be combined with other armour except a helmet")


def test_the_eshin_robes_still_admit_the_printed_helmet_exception():
    assert loadout("armour.eshin-assassin-robes", defence_ids=["defence.helmet"]) is None
    assert loadout("armour.eshin-assassin-robes", off_hand_id="defence.shield") == (
        "armour.eshin-assassin-robes cannot be combined with other armour except a helmet")


# ---------------------------------------------------------------------------
# The real bands: item -> origin mechanic -> the same decision
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("band_id,profile_id,armour_id", [KHEMRI_TUNIC, ARCANE_TUNIC])
def test_each_origin_item_binds_its_own_tunic_and_keeps_the_six_plus_save(
        band_id, profile_id, armour_id):
    fighter = compile_with(band_id, profile_id, armour_id)
    assert fighter.armour_save == 6
    assert armour_id in fighter.global_effects.tags


@pytest.mark.parametrize("other", [{"defence_ids": ("defence.helmet",)},
                                   {"off_hand_id": "defence.shield"},
                                   {"off_hand_id": "defence.buckler"}])
def test_the_arcane_society_tunic_refuses_the_armour_its_own_list_offers(other):
    # chaos-in-the-streets printed 167 offers the Casco, the Escudo and the
    # Rodela beside the Tunica de Mago; the printed save clause refuses them.
    assert refusal("chaos-streets-arcane-society", "arcane-mage",
                   "armour.wizard-robe", **other) == (
        "armour.wizard-robe cannot be combined with any other armour")


def test_the_deathbringer_assassin_keeps_the_helmet_its_paragraph_excepts():
    fighter = compile_with(*ASSASSIN_ROBES, defence_ids=("defence.helmet",))
    assert fighter.armour_save == 6
    assert refusal(*ASSASSIN_ROBES, off_hand_id="defence.shield") == (
        "armour.eshin-assassin-robes cannot be combined with other armour except a helmet")
