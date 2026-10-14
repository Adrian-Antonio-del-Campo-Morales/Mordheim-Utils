"""T13 Eshin Assassin Clothes: the printed Assassin's Luck re-roll of a save.

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
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild

ROBES = "armour.eshin-assassin-robes"
LIGHT_ARMOUR = "armour.light-armour"
ATTACKER = Characteristics(3, 3, 3, 3, 3, 1, leadership=7)


def fighter(armour_id=None, **options):
    armour = {"armour_id": armour_id} if armour_id else {}
    return compile_fighter(FighterBuild("mordheim", ATTACKER, **armour, **options))


def mace():
    return fighter(main_weapon_id="weapon.mace")


def robes(*, luck=False):
    return fighter(ROBES, skill_ids=("skill.luck",) if luck else ())


def plain_armour(*, luck=False):
    return fighter(LIGHT_ARMOUR, skill_ids=("skill.luck",) if luck else ())


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


def test_the_printed_re_roll_saves_a_failed_robes_save():
    result = attack(mace(), robes(), RE_ROLLED_SIX)
    assert result.saved is True
    assert result.damage == 0
    assert result.defender.wounds == 3


def test_a_holding_robes_save_asks_for_no_re_roll():
    # StrictDice.finish() proves the tape ended at the single armour die.
    result = attack(mace(), robes(), [roll("a.hit", 6), roll("a.wound", 4), roll("a.armour", 6)])
    assert result.saved is True
    assert result.damage == 0


def test_a_plain_armour_bearer_keeps_the_plain_failed_save():
    result = attack(mace(), plain_armour(), FAILED_ROBES_SAVE)
    assert result.saved is False
    assert result.damage == 1
    assert result.defender.wounds == 2


def test_the_second_result_stands_when_the_re_roll_also_fails():
    result = attack(mace(), robes(), [*FAILED_ROBES_SAVE, roll("a.armour.reroll", 4)])
    assert result.saved is False
    assert result.damage == 1
    assert result.defender.wounds == 2


def test_the_printed_re_roll_costs_nothing_and_precedes_the_luck_skill():
    # The free printed re-roll is taken, so the once-per-battle Luck skill stays
    # unspent; a bearer without the robes has to pay for the same second die.
    free = attack(mace(), robes(luck=True), RE_ROLLED_SIX)
    assert free.saved is True
    assert "luck" not in free.defender.resources_spent
    paid = attack(mace(), plain_armour(luck=True), RE_ROLLED_SIX)
    assert paid.saved is True
    assert "luck" in paid.defender.resources_spent


def test_an_interactive_luck_re_roll_is_never_re_rolled_a_second_time():
    # The player spends Luck on the armour die; the robes must then ask for no
    # further die, and only the scripted decision is requested.
    result = attack(mace(), robes(luck=True), RE_ROLLED_SIX,
                    decisions=[{"key": "a.armour.luck", "value": True}])
    assert result.saved is True
    assert "luck" in result.defender.resources_spent
