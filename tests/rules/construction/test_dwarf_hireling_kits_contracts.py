"""Construction contracts split from ``tests/engines/modular/test_dwarf_hireling_kits.py``.

These tests assert on the canonical compiler itself -- the printed profile
facts and the refusals it produces -- so they keep calling
``compile_fighter`` instead of reading frozen engine inputs.
"""
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def hireling(profile_id, band, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                                        collection="mordheim", **options))


TREASURE_HUNTER = "hireling.hired-sword.dwarf-treasure-hunter"


TREASURE_HUNTER_BAND = "hirelings.hired-sword.1b"


SLAYER_PIRATE = "hireling.hired-sword.dwarf-slayer-pirate"


SLAYER_PIRATE_BAND = "hirelings.hired-sword.2a"


@pytest.mark.phase2_construction
def test_the_lantern_rig_stays_a_carried_object_not_a_weapon():
    """The rig follows the lantern, so it may not occupy an active weapon slot."""
    rig = "hireling.hired-sword.dwarf-treasure-hunter.item.lantern-rig"
    with pytest.raises(ValueError, match="non-duel unique equipment cannot occupy an active combat position"):
        hireling(TREASURE_HUNTER, TREASURE_HUNTER_BAND, main_weapon_id=rig)
    # The same profile still compiles with the printed two-handed pick.
    hunter = hireling(TREASURE_HUNTER, TREASURE_HUNTER_BAND,
                      main_weapon_id="weapon.double-handed-weapon")
    assert rig not in hunter.main_weapon.tags


@pytest.mark.phase2_construction
def test_the_slayer_pirates_sword_and_pistol_are_one_legal_kit():
    """The printed Weapons/Armour line is the Sword, Blackpowder and Pistols."""
    sword = hireling(SLAYER_PIRATE, SLAYER_PIRATE_BAND, main_weapon_id="weapon.sword")
    assert "weapon.sword" in sword.main_weapon.tags
    owned = ("sword", "superior_blackpowder", "pistol")
    owned = hireling(SLAYER_PIRATE, SLAYER_PIRATE_BAND, main_weapon_id="weapon.pistol",
                     owned_item_ids=owned)
    assert "weapon.pistol" in owned.main_weapon.tags
    # Ownership the printed kit does not print is still refused by name.
    with pytest.raises(ValueError, match="complete legal printed kit"):
        hireling(SLAYER_PIRATE, SLAYER_PIRATE_BAND, main_weapon_id="weapon.sword",
                 owned_item_ids=("sword", "superior_blackpowder", "pistol", "axe"))
