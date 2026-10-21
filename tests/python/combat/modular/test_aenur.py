"""Ienh-Khain's Strength and critical clause in the resolved duel.

The canonical hireling kit resolves the unique sword without naming a weapon.
Its +1 Strength lives on the sword's attack contract and composes exactly once
with Aenur's printed Mighty Blow.  The printed critical threshold 5 keeps the
ordinary critical system around it: a wound roll of 4 is no critical, 5 and 6
are, and the per-turn availability and needing-six rule are untouched.
"""
from __future__ import annotations

from mordheim_combat.modular.contexts import (
    _attack_strength, _combined_effect, prepare_wound_context,
)
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import resolve_wound
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild
import pytest

BAND = "hirelings.dramatis-personae.core"
PROFILE = "hireling.dramatis.aenur"


def aenur():
    """Compile the printed kit: the unique equipment decides the weapon."""
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=PROFILE))


def opponent():
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))


def state(fighter):
    return initialize_fighter(fighter, StrictDice([]), "probe")


def wound_context(unit, foe):
    return prepare_wound_context(
        unit, foe, state(unit), state(foe), unit.main_weapon,
        _combined_effect(unit, unit.main_weapon), key="wound")


@pytest.mark.compilation
def test_the_kit_resolves_ienh_khain_and_applies_its_strength_once():
    unit = aenur()
    assert "weapon.ienh-khain" in unit.main_weapon.tags
    assert unit.main_weapon.strength_bonus == 1
    # The profile's own +1 is Mighty Blow; the sword's point stays on the weapon.
    assert unit.global_effects.strength_bonus == 1
    combined = _combined_effect(unit, unit.main_weapon)
    assert combined.strength_bonus == 2
    strength, _ = _attack_strength(
        unit, opponent(), state(unit), unit.main_weapon, combined, False, False)
    # S4 + Mighty Blow + Ienh-Khain = 6; a duplicated sword point would make 7.
    assert unit.characteristics.strength == 4
    assert strength == 6


@pytest.mark.rule_behavior
def test_the_sword_critical_starts_at_five_and_keeps_the_ordinary_limits():
    unit, foe = aenur(), opponent()
    context = wound_context(unit, foe)
    assert (context.critical_threshold, context.critical_available) == (5, True)
    assert context.critical_when_needing_six is False
    results = {roll: resolve_wound(context, StrictDice([{"key": "wound", "value": roll}]))
               for roll in (4, 5, 6)}
    # The printed 5-6 replaces only the threshold, not the wound itself.
    assert results[4].success is True and results[4].critical is False
    assert results[5].success is True and results[5].critical is True
    assert results[6].success is True and results[6].critical is True
