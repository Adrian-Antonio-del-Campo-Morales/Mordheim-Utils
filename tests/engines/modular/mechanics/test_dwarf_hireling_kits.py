"""Dwarf hireling kits: printed equipment that had no durable consumer.

Three dwarf Hired Swords refused for a printed equipment reason rather than a
missing rule.  The Treasure Hunter's Mining Pick and Lantern Rig named no
canonical object, so the profile never compiled at all; the Slayer Pirate's
printed pistols were absent from his kit and his ``count the pistol as a club``
clause had no operator.  Each case below goes through the canonical hireling
package and reads a real compiled weapon or the shared round preparer, and each
one carries the negative control that would still pass under the wrong reading.
"""
from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from mordheim_combat.modular.contexts import _combined_effect, _hit_reroll
from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.state import FighterState
from mordheim_core.models import Characteristics, FighterBuild


# The frozen-build loader is the only compilation route in this module: the
# fixture below replaces this name with ``load_builds(...).fighter``, so every
# builder keeps its complete FighterBuild and the local ``replace`` calls stay
# untouched, while nothing compiles here.
compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


TREASURE_HUNTER = "hireling.hired-sword.dwarf-treasure-hunter"
TREASURE_HUNTER_BAND = "hirelings.hired-sword.1b"
SLAYER_PIRATE = "hireling.hired-sword.dwarf-slayer-pirate"
SLAYER_PIRATE_BAND = "hirelings.hired-sword.2a"


def hireling(profile_id, band, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile_id,
                                        collection="mordheim", **options))


def plain(*tags):
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7), main_weapon_id="weapon.mace"))
    return replace(fighter, global_effects=replace(fighter.global_effects,
        tags=(*fighter.global_effects.tags, *tags)))


def rerolls(attacker, defender, *, first_round=True):
    return _hit_reroll(attacker, defender, attacker.main_weapon,
                       _combined_effect(attacker, attacker.main_weapon), first_round, False)


# --- the Treasure Hunter's two handed unique object ---------------------------

def test_the_mining_pick_is_the_treasure_hunters_two_handed_weapon(precompiled):
    """The printed Mining Pick uses the double-handed axe/hammer rules.

    The unique object declares that equivalence, so the profile that previously
    refused for an unmapped object now compiles and the pick is the active
    weapon: two-handed and Strength as the user +2.
    """
    compiled = precompiled()
    hunter, dagger = compiled.first, compiled.second
    assert hunter.main_weapon.two_handed is True
    assert hunter.main_weapon.strength_bonus == 2
    # Negative control: the Dagger of the same kit is not two-handed and gains
    # no Strength, so the printed properties are the pick's, not the profile's.
    assert dagger.main_weapon.two_handed is False
    assert dagger.main_weapon.strength_bonus == 0


def test_the_dwarf_hatred_needs_the_enemy_identity():
    """All Dwarfs hate Orcs and Goblins; the printed target must be supplied."""
    hunter = hireling(TREASURE_HUNTER, TREASURE_HUNTER_BAND,
                      main_weapon_id="weapon.double-handed-weapon")
    assert "mechanic.hatred-orcs-goblins" in hunter.global_effects.tags
    assert rerolls(hunter, plain("species.goblin")) is True
    assert rerolls(hunter, plain("species.orc")) is True
    # Negative control: an unqualified opponent is never rerolled, and the
    # shared Hatred timing stays first-round only.
    assert rerolls(hunter, plain("species.dwarf")) is False
    assert rerolls(hunter, plain("species.goblin"), first_round=False) is False


# --- the Slayer Pirate's spent pistol ----------------------------------------

def test_a_spent_pistol_is_counted_as_a_club_for_the_slayer_pirate(precompiled):
    """The printed Festooned with Pistols clause keeps a spent pistol in hand.

    Ordinary pistol bearers lose the weapon after the opening round; this one
    keeps it as a club, so Strength as the user with Concussion and without the
    pistol's fixed Strength or armour penetration replace the shot profile.
    """
    compiled = precompiled()
    pirate, ordinary = compiled.first, compiled.second
    assert "mechanic.festooned-with-pistols" in pirate.global_effects.tags
    state = FighterState(wounds=1)
    opening = equipment_for_state(pirate, state, first_round=True)
    assert "weapon.pistol" in opening.main_weapon.tags
    assert opening.main_weapon.fixed_strength == 4
    later = equipment_for_state(pirate, state, first_round=False)
    assert "weapon.mace" in later.main_weapon.tags
    assert later.main_weapon.concussion is True
    assert later.main_weapon.fixed_strength == 0
    assert later.main_weapon.armour_penetration == 0
    # Negative control: an ordinary pistol bearer loses the spent pistol.
    dropped = equipment_for_state(ordinary, FighterState(wounds=1), first_round=False)
    assert "weapon.pistol" not in dropped.main_weapon.tags
