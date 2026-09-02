"""Enumeración exacta de resoluciones locales."""
from __future__ import annotations

from fractions import Fraction
from mordheim_combat.phases import ArmourContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import InjuryContext
from mordheim_combat.phases import ParryContext
from mordheim_combat.phases import SpecialSaveContext
from mordheim_combat.phases import resolve_armour
from mordheim_combat.phases import resolve_injury
from mordheim_combat.phases import resolve_parry
from mordheim_combat.phases import resolve_special_save
from mordheim_core.dice import ScriptedDice
from mordheim_core.dice import exact_distribution
import pytest as pytest


@pytest.mark.parametrize("target", range(2, 7))
def test_every_armour_target_enumerates_all_d6_faces(target):
    distribution = exact_distribution(
        (6,),
        lambda rolls: resolve_armour(
            ArmourContext(armour_save=target), ScriptedDice(rolls)
        ).saved,
    )
    assert distribution[True] == Fraction(7 - target, 6)


def test_parry_and_parry_reroll_have_exact_distributions():
    ordinary = exact_distribution(
        (6,),
        lambda rolls: resolve_parry(
            ParryContext(4, 3, 3), ScriptedDice(rolls)
        ).blocked,
    )
    rerolled = exact_distribution(
        (6, 6),
        lambda rolls: resolve_parry(
            ParryContext(4, 3, 3, reroll=True), ScriptedDice(rolls)
        ).blocked,
    )
    assert ordinary == {False: Fraction(2, 3), True: Fraction(1, 3)}
    assert rerolled == {False: Fraction(4, 9), True: Fraction(5, 9)}


@pytest.mark.parametrize(
    ("context", "expected"),
    (
        (InjuryContext(), (
            Condition.KNOCKED_DOWN, Condition.KNOCKED_DOWN,
            Condition.STUNNED, Condition.STUNNED,
            Condition.OUT, Condition.OUT,
        )),
        (InjuryContext(hard_to_kill=True), (
            Condition.KNOCKED_DOWN, Condition.KNOCKED_DOWN, Condition.STUNNED,
            Condition.STUNNED, Condition.STUNNED, Condition.OUT,
        )),
        (InjuryContext(injury_profile=3), (
            Condition.KNOCKED_DOWN, Condition.KNOCKED_DOWN, Condition.KNOCKED_DOWN,
            Condition.OUT, Condition.OUT, Condition.OUT,
        )),
    ),
)
def test_injury_tables_map_every_d6_face(context, expected):
    assert tuple(
        resolve_injury(context, ScriptedDice((roll,))).condition
        for roll in range(1, 7)
    ) == expected


def test_ward_and_regeneration_distribution_accounts_for_short_circuiting():
    context = SpecialSaveContext(ward_save=6, regeneration_save=5)
    distribution = exact_distribution(
        (6, 6),
        lambda rolls: resolve_special_save(context, ScriptedDice(rolls)).saved,
    )
    assert distribution == {False: Fraction(5, 9), True: Fraction(4, 9)}
