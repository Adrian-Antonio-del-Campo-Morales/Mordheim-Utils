"""The printed kit and rules reach the resolved duel.

Veskit, High Executioner of Clan Eshin (``dramatis personae`` core) compiles his
own printed kit: integrated fighting claws at fixed Strength 5 with an extra
armour penalty, Metallic Body's 3+ armour and Unfeeling's immunity to
psychology.  The retained cases in ``test_defence_parries_and_ward.py``
already cover the A4 profile (no doubled pistol attack), the adopted parry and
the No Pain injury results; the discriminators below add what those do not
read: the face the 3+ save actually resolves on, the total modifier of the
claws, and the skipped psychology test.
"""
from __future__ import annotations

from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.state import DuelState, initialize_fighter
from mordheim_combat.phases import armour_target, resolve_armour
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
import pytest


def state(fighter):
    return initialize_fighter(fighter, StrictDice([]), "probe")


def armour_stage(attacker_fighter, defender):
    return prepare_armour_context(
        attacker_fighter, defender, state(attacker_fighter), state(defender),
        attacker_fighter.main_weapon, attacker_fighter.main_weapon, key="armour")


@pytest.mark.phase2_construction
def test_the_claws_keep_four_attacks_and_reach_a_total_minus_three_modifier(precompiled):
    compiled = precompiled()
    claws, armoured = compiled.first, compiled.second
    # The printed A4 already includes the integrated pistols' extra attack.
    assert (claws.characteristics.attacks, claws.main_weapon.attacks_bonus) == (4, 0)
    assert (claws.main_weapon.fixed_strength, claws.main_weapon.armour_penetration) == (5, 1)
    # Strength 5 contributes -2 and the claws' own extra point makes the printed
    # total -3, so heavy armour's 5+ face cannot be rolled at all.
    stage = armour_stage(claws, armoured)
    assert (stage.strength, stage.armour_penetration) == (5, 1)
    assert armour_target(stage) == 8
    assert resolve_armour(stage, StrictDice([])).eligible is False


@pytest.mark.phase3_rules
def test_metallic_body_is_the_armour_save_on_three_or_better(precompiled):
    # The mechanical body is armour, not a ward or a regeneration save.
    compiled = precompiled()
    stage = armour_stage(compiled.first, compiled.second)
    assert armour_target(stage) == 3
    assert resolve_armour(stage, StrictDice([{"key": "armour", "value": 3}])).saved is True
    assert resolve_armour(stage, StrictDice([{"key": "armour", "value": 2}])).saved is False


@pytest.mark.phase3_rules
def test_unfeeling_skips_the_psychology_test_instead_of_rolling_leadership(precompiled):
    compiled = precompiled()
    fighter, foe = compiled.first, compiled.second
    duel = DuelState(state(fighter), state(foe), first_charged=False)
    # Empty dice are the discriminator: a non-immune warrior would request a
    # Leadership roll here, and StrictDice would refuse it.
    passed = resolve_local_leadership(
        fighter, duel, StrictDice([]), StrictDecisions([]), "ld",
        first=True, psychology=True)
    assert passed is True
