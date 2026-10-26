"""Eshin Assassin Clothes: the printed Assassin's Luck re-roll of a save.

chaos-in-the-streets printed 159 prints the item's own paragraph:

    "Salvacion: Los Ropajes de Asesino Eshin actuan exactamente igual que una
    Armadura Ligera, proporcionando una tirada de salvacion de 6+. No pueden
    combinarse con ninguna otra armadura excepto el casco. La suerte del
    Asesino: los ropajes de asesino eshin permiten repetir las tiradas de
    salvacion fallidas."

The sentence names save rolls without a cost and without a frequency, so the
bearer of the robes rolls one second armour die after every failed save and the
accepted result is the second one.  The save it names is the one the entry
grants, so the re-roll is wired at the armour stage; the ward and regeneration
saves of other rules are not extended by this paragraph.  A die that was already
re-rolled (the Luck skill of an interactive replay) is never re-rolled twice,
and the printed free re-roll is taken before the once-per-battle Luck skill is
spent.
"""
from __future__ import annotations

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
import pytest



ROBES = "armour.eshin-assassin-robes"
LIGHT_ARMOUR = "armour.light-armour"


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, "init")
    dice.finish()
    return result


def roll(key, value, sides=6):
    return {"key": key, "value": value, "sides": sides}


def attack(attacker, defender, rolls, decisions=None):
    dice = StrictDice(rolls)
    choices = StrictDecisions(decisions) if decisions is not None else None
    result = resolve_reference_attack(
        attacker, defender, state(attacker), state(defender),
        attacker.main_weapon, dice, key="a", decisions=choices)
    dice.finish()
    if choices is not None:
        choices.finish()
    return result


#: S3 against T3 needs a 4 to wound and the 6+ save fails on a five, so the
#: printed five and the re-rolled six are the two armour faces this entry asks.
FAILED_ROBES_SAVE = [roll("a.hit", 6), roll("a.wound", 4), roll("a.armour", 5)]
RE_ROLLED_SIX = [*FAILED_ROBES_SAVE, roll("a.armour.reroll", 6)]


def test_the_printed_re_roll_saves_a_failed_robes_save(precompiled):
    compiled = precompiled()
    attacker, robes = compiled.first, compiled.second
    result = attack(attacker, robes, RE_ROLLED_SIX)
    assert result.saved is True
    assert result.damage == 0
    assert result.defender.wounds == 3


def test_a_holding_robes_save_asks_for_no_re_roll(precompiled):
    # StrictDice.finish() proves the tape ended at the single armour die.
    compiled = precompiled()
    attacker, robes = compiled.first, compiled.second
    result = attack(attacker, robes, [roll("a.hit", 6), roll("a.wound", 4), roll("a.armour", 6)])
    assert result.saved is True
    assert result.damage == 0


def test_a_plain_armour_bearer_keeps_the_plain_failed_save(precompiled):
    compiled = precompiled()
    attacker, armoured = compiled.first, compiled.second
    result = attack(attacker, armoured, FAILED_ROBES_SAVE)
    assert result.saved is False
    assert result.damage == 1
    assert result.defender.wounds == 2


def test_the_second_result_stands_when_the_re_roll_also_fails(precompiled):
    compiled = precompiled()
    attacker, robes = compiled.first, compiled.second
    result = attack(attacker, robes, [*FAILED_ROBES_SAVE, roll("a.armour.reroll", 4)])
    assert result.saved is False
    assert result.damage == 1
    assert result.defender.wounds == 2


def test_the_printed_re_roll_costs_nothing_and_precedes_the_luck_skill(precompiled):
    # The free printed re-roll is taken, so the once-per-battle Luck skill stays
    # unspent; a bearer without the robes has to pay for the same second die.
    robe_case = precompiled(0)
    free = attack(robe_case.first, robe_case.second, RE_ROLLED_SIX)
    assert free.saved is True
    assert "luck" not in free.defender.resources_spent
    paid_case = precompiled(1)
    paid = attack(paid_case.first, paid_case.second, RE_ROLLED_SIX)
    assert paid.saved is True
    assert "luck" in paid.defender.resources_spent


def test_an_interactive_luck_re_roll_is_never_re_rolled_a_second_time(precompiled):
    # The player spends Luck on the armour die; the robes must then ask for no
    # further die, and only the scripted decision is requested.
    compiled = precompiled()
    result = attack(compiled.first, compiled.second, RE_ROLLED_SIX,
                    decisions=[{"key": "a.armour.luck", "value": True}])
    assert result.saved is True
    assert "luck" in result.defender.resources_spent
