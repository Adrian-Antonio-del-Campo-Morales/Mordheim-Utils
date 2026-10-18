"""P01/P02 focal discriminators: the printed Druchii-only kit variants.

The Druchii local source prints its own Sea Dragon Cloak (a +1 close-combat
save improvement, a 6+ save alone, combining with light armour and a shield
with no penalty) and its own Draich (user Strength +2, two-handed, Swift — it
does not strike last).  The shared catalogue entries stay untouched, so every
case compares the Druchii route against the preserved constant-save cloak from
the corsairs and the shared strike-last Draich.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild, Characteristics


def build(**options):
    return FighterBuild("mordheim", Characteristics(3, 4, 3, 2, 3, 1, leadership=7), **options)


def druchii(**options):
    defaults = dict(main_weapon_id="weapon.sword")
    return compile_fighter(build(band_id="druchii-mic", profile_id="noble", **{**defaults, **options}))


# --- P01: the printed Druchii Sea Dragon Cloak ------------------------------
def test_druchii_sea_dragon_cloak_alone_is_a_6_plus_save():
    cloak = druchii(armour_id="armour.no-armour",
                    defence_ids=("defence.sea-dragon-cloak-druchii",))
    assert cloak.armour_save == 6
    assert "defence.sea-dragon-cloak-druchii" in cloak.global_effects.tags


def test_druchii_sea_dragon_cloak_combines_with_light_armour_and_shield():
    light = druchii(armour_id="armour.light-armour",
                    defence_ids=("defence.sea-dragon-cloak-druchii",))
    assert light.armour_save == 5
    both = druchii(armour_id="armour.light-armour", off_hand_id="defence.shield",
                   defence_ids=("defence.sea-dragon-cloak-druchii",))
    assert both.armour_save == 4


def test_the_shared_constant_save_cloak_variant_keeps_its_printed_shape():
    corsair = compile_fighter(build(
        band_id="dark-elf-corsairs-mou", profile_id="corsairs",
        main_weapon_id="weapon.sword", armour_id="armour.no-armour",
        defence_ids=("defence.sea-dragon-cloak",)))
    assert corsair.armour_save == 5


def test_a_warrior_carries_one_sea_dragon_cloak_not_a_stack_of_variants():
    with pytest.raises(ValueError, match="one Sea Dragon cloak"):
        druchii(armour_id="armour.no-armour", defence_ids=(
        "defence.sea-dragon-cloak-druchii", "defence.sea-dragon-cloak-druchii"))


# --- P02: the printed Druchii Draich ----------------------------------------
def test_druchii_draich_is_user_s_plus_2_two_handed_and_swift():
    draich = druchii(main_weapon_id="weapon.draich-druchii")
    assert draich.main_weapon.strength_bonus == 2
    assert draich.main_weapon.two_handed
    # Swift: no weapon-imposed Strike Last, and no borrowed parry, Concussion
    # or Critical Hit bonus from the shared catalogue entry.
    assert draich.main_weapon.priority == 0
    assert not draich.main_weapon.parry
    assert draich.main_weapon.critical_injury_bonus == 0


def test_the_shared_draich_keeps_its_printed_strike_last_bundle():
    shared = compile_fighter(build(
        band_id="lustria-dark-elves", profile_id="darkblades",
        main_weapon_id="weapon.draich", collection="trollheim"))
    assert shared.main_weapon.strength_bonus == 2
    assert shared.main_weapon.priority == -1
    assert shared.main_weapon.parry
