"""Restricted-weapon construction contracts.

Moved from ``tests/engines/vectorized/test_runtime_regressions.py`` by T08:
the subject is warband construction (illegal equipment combinations), not the
vectorized engine.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild
import pytest as pytest


def build(*, attacks=1, strength=3, toughness=3, wounds=1, **changes):
    options = dict(
        ruleset="mordheim",
        characteristics=Characteristics(3, strength, toughness, wounds, 3, attacks),
    )
    options.update(changes)
    return compile_fighter(FighterBuild(**options))


@pytest.mark.parametrize(
    "weapon",
    (
        "weapon.morning-star",
        "weapon.spear",
        "weapon.broadsword",
        "weapon.squig-prodder",
        "weapon.boar-spear",
    ),
)
def test_restricted_weapons_reject_an_illegal_second_weapon(weapon):
    with pytest.raises(ValueError, match="cannot be combined"):
        build(main_weapon_id=weapon, off_hand_id="weapon.dagger")


def test_restricted_weapons_and_toughened_leathers_keep_legal_combinations():
    assert build(main_weapon_id="weapon.spear", off_hand_id="defence.buckler").off_hand is not None
    assert build(main_weapon_id="weapon.broadsword", off_hand_id="defence.shield").off_hand is not None
    assert build(main_weapon_id="weapon.squig-prodder", off_hand_id="weapon.spiked-gauntlet").off_hand is not None
    assert build(armour_id="armour.toughened-leathers", off_hand_id="defence.buckler").off_hand is not None
    with pytest.raises(ValueError, match="toughened leathers"):
        build(armour_id="armour.toughened-leathers", off_hand_id="defence.shield")
