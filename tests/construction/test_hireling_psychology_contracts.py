"""Construction contract: the hireling Fear projection keeps the ogre identities.

The ten trait rows are five profiles whose whole-profile row and individual trait
row name the same Fear consequence; ``fear_carriers`` compiles every recipient so
this file can read the identities the compilation projects.  It owns the
compiler, so it builds the carriers itself instead of loading engine fixtures.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def hireling(profile_id, band, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile_id, collection="mordheim", **options))


# The ten trait rows are five profiles whose whole-profile row and individual
# trait row name the same consequence; each must reach the operator exactly once.
def fear_carriers():
    return (
        hireling("hireling.hired-sword.dark-mage", "hirelings.hired-sword.2a"),
        hireling("hireling.hired-sword.ogre-slave-master", "hirelings.hired-sword.2a",
                 main_weapon_id="weapon.axe", off_hand_id="weapon.club",
                 owned_item_ids=("axe", "club", "light_armour")),
        hireling("hireling.hired-sword.bone-goliath", "hirelings.hired-sword.1c",
                 main_weapon_id="weapon.natural-attacks"),
        hireling("hireling.hired-sword.chaos-centaur", "hirelings.hired-sword.1c",
                 main_weapon_id="weapon.spear", off_hand_id="defence.shield",
                 owned_item_ids=("throwing_axe", "shield", "spear")),
        hireling("hireling.hired-sword.ogre-bodyguard", "hirelings.hired-sword.core",
                 main_weapon_id="weapon.double-handed-weapon"),
    )


def test_the_ogre_identities_survive_the_fear_projection():
    _, slave, goliath, _, bodyguard = fear_carriers()
    assert "species.ogre" in slave.global_effects.tags
    assert "species.ogre" in goliath.global_effects.tags
    assert "species.ogre" in bodyguard.global_effects.tags
    assert "mechanic.undead-construct" in goliath.global_effects.tags
