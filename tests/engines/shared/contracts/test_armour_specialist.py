"""Strength-only protection of worn Heavy Armour, with explicit exclusions."""
from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat import phases
from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.vectorized._operators import armour_context, armour_target_values
from mordheim_combat.vectorized._state import initialize_fighter as vector_state
from mordheim_core.dice import ScriptedDice
from mordheim_core.models import EffectSet


def fighters(cases, variant="ordinary"):
    base = cases["scenario/basic"].first
    attacker = replace(base, global_effects=EffectSet())
    tags = ["skill.armour-specialist", "armour.heavy-armour"]
    shield = "defence.kite-shield" if variant == "kite" else "defence.shield"
    if variant == "no-skill": tags.remove("skill.armour-specialist")
    if variant == "no-heavy": tags.remove("armour.heavy-armour")
    if variant == "gromril": tags = ["skill.armour-specialist", "armour.gromril-armour"]
    if variant == "buckler": shield = "defence.buckler"
    defender = replace(base, global_effects=EffectSet(tags=tuple(tags)),
        armour_save=6 if variant == "degraded" else 4,
        natural_armour_save=3 if variant == "natural" else 7,
        natural_armour_unmodified=variant == "natural", mounted=variant == "mounted",
        shield_and_skill_effects=EffectSet(tags=() if variant == "no-shield" else (shield,),
                                          armour_save_bonus=1))
    return attacker, defender


@pytest.mark.parametrize("backend", ["modular", "numpy"])
@pytest.mark.parametrize("variant,strength,options,expected", [
    ("ordinary", 3, {}, 4), ("ordinary", 4, {}, 5), ("ordinary", 8, {}, 5),
    ("ordinary", 8, {"armour_penetration": 1}, 6),
    ("ordinary", 8, {"target_armour_bonus": 1}, 4),
    ("ordinary", 8, {"tags": ("condition.djinns-curse-active",)}, 6),
    ("ordinary", 8, {"ignore_armour": True}, 7),
    ("ordinary", 3, {"ignore_armour_except_shield_and_skills": True}, 6),
    ("mounted", 8, {}, 7), ("no-skill", 8, {}, 7), ("no-heavy", 8, {}, 7),
    ("no-shield", 8, {}, 7), ("buckler", 8, {}, 7), ("kite", 8, {}, 5),
    ("natural", 8, {}, 3), ("degraded", 3, {}, 6), ("gromril", 8, {}, 7),
])
def test_armour_specialist_limits_only_eligible_strength_penalties(
    cases, backend, variant, strength, options, expected,
):
    attacker, defender = fighters(cases, variant)
    weapon = EffectSet(fixed_strength=strength, **options)
    if backend == "modular":
        context = prepare_armour_context(attacker, defender,
            initialize_fighter(attacker, ScriptedDice(()), "first"),
            initialize_fighter(defender, ScriptedDice(()), "second"), weapon, weapon)
        assert phases.armour_target(context) == expected
    else:
        rng = np.random.default_rng(1)
        context = armour_context(attacker, defender,
            vector_state(attacker, 2, rng), vector_state(defender, 2, rng),
            weapon, weapon, np.arange(2))
        assert armour_target_values(context).tolist() == [expected, expected]
    assert defender.global_effects.armour_save_floor == 7


@pytest.mark.parametrize("backend", ["modular", "numpy"])
def test_armour_specialist_saves_a_real_high_strength_hit(cases, backend):
    attacker, defender = fighters(cases)
    weapon = EffectSet(tags=("effect.no-critical",), automatic_hit=True, fixed_strength=8)
    if backend == "modular":
        from mordheim_combat.modular.attacks import resolve_reference_attack
        result = resolve_reference_attack(attacker, defender,
            initialize_fighter(attacker, ScriptedDice(()), "first"),
            initialize_fighter(defender, ScriptedDice(()), "second"),
            weapon, ScriptedDice((2, 5)), key="specialist")
        assert result.saved and result.defender.wounds == defender.characteristics.wounds
    else:
        from mordheim_combat.vectorized._attacks import _resolve_weapon

        class Tape:
            values = [2, 5]
            def integers(self, low, high=None, size=None):
                assert size == 1
                return np.array([self.values.pop(0)])

        rng = np.random.default_rng(1)
        first, second = vector_state(attacker, 1, rng), vector_state(defender, 1, rng)
        tape = Tape()
        _resolve_weapon(attacker, defender, weapon, np.array([0]), np.zeros(1, dtype=bool),
                        first, second, tape, False)
        assert not tape.values
        assert second.wounds.tolist() == [defender.characteristics.wounds]


def test_vector_armour_target_helper_keeps_the_strength_cap_per_row(cases):
    from mordheim_combat.vectorized._operators import armour_targets

    _, defender = fighters(cases)
    assert armour_targets(defender, np.array([3, 4, 8]), EffectSet(), False).tolist() == [4, 5, 5]
