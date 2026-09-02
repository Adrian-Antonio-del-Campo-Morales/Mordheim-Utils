"""Interacciones del motor modular."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from mordheim_combat_lab.combat.phases import ArmourContext
from mordheim_combat_lab.combat.phases import HitContext
from mordheim_combat_lab.combat.phases import InjuryContext
from mordheim_combat_lab.combat.phases import SpecialSaveContext
from mordheim_combat_lab.combat.phases import WoundContext
from mordheim_combat_lab.combat.phases import resolve_armour
from mordheim_combat_lab.combat.phases import resolve_hit
from mordheim_combat_lab.combat.phases import resolve_injury
from mordheim_combat_lab.combat.phases import resolve_special_save
from mordheim_combat_lab.combat.phases import resolve_wound
from mordheim_combat_lab.domain.dice import ScriptedDice
from mordheim_combat_lab.domain.dice import exact_distribution


def test_hit_bonus_and_reroll_compose_without_changing_natural_d6_domain():
    context = HitContext(3, 3, modifier=1, reroll=True)
    distribution = exact_distribution(
        (6, 6),
        lambda rolls: resolve_hit(context, ScriptedDice(rolls)).success,
    )
    assert distribution == {False: Fraction(1, 9), True: Fraction(8, 9)}


def test_wound_modifier_and_maximum_target_have_fixed_operator_order():
    context = WoundContext(1, 6, modifier=1, maximum_target=5)
    result = resolve_wound(context, ScriptedDice((4,)))
    assert result.target == 4 and result.success


def test_ignore_armour_and_non_ignorable_floor_have_explicit_precedence():
    ordinary = resolve_armour(
        ArmourContext(armour_save=4, ignore_armour=True), ScriptedDice(())
    )
    protected = resolve_armour(
        ArmourContext(
            armour_save=4, ignore_armour=True,
            armour_save_floor=6, armour_cannot_be_ignored=True,
        ),
        ScriptedDice((6,)),
    )
    magical = resolve_armour(
        ArmourContext(
            armour_save=4, ignore_armour=True,
            armour_save_floor=6, armour_cannot_be_ignored=True,
            magical_attack=True,
        ),
        ScriptedDice((6,)),
    )
    assert not ordinary.eligible
    assert protected.saved and protected.target == 6
    assert magical.saved and magical.target == 6


def test_ward_then_regeneration_and_blockers_are_non_commutative_by_ruling():
    context = SpecialSaveContext(ward_save=5, regeneration_save=4)
    assert resolve_special_save(context, ScriptedDice((5,))).source == "ward"
    blocked = replace(context, ward_blocked=True)
    assert resolve_special_save(blocked, ScriptedDice((4,))).source == "regeneration"
    none = replace(blocked, regeneration_blocked=True)
    assert not resolve_special_save(none, ScriptedDice(())).saved


def test_injury_replacements_are_applied_after_the_base_table():
    assert resolve_injury(
        InjuryContext(concussion=True), ScriptedDice((2,))
    ).condition.name == "STUNNED"
    assert resolve_injury(
        InjuryContext(concussion=True, concussion_immune=True), ScriptedDice((2,))
    ).condition.name == "KNOCKED_DOWN"
    assert resolve_injury(
        InjuryContext(head_crusher=True, ignore_pain=True), ScriptedDice((1,))
    ).condition.name == "KNOCKED_DOWN"
