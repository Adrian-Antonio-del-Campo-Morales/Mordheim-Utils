"""Armour Specialist caps only Strength's eligible worn-armour penalty."""
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from mordheim_core.models import DuelContext, EffectSet
from tools.verification.compiled_cases import load_cases

native = pytest.importorskip("mordheim_combat._combat_native")


@lru_cache(maxsize=1)
def _base():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
    base = load_cases(path)["scenario/basic"].first
    return replace(base, global_effects=EffectSet(),
        characteristics=replace(base.characteristics, wounds=3),
        main_weapon=EffectSet(tags=("weapon.mace",)), main_weapon_without_poison=None,
        off_hand=None, off_hand_without_poison=None, off_hand_attacks=False,
        extra_attacks=(), armour_save=7, natural_armour_save=7,
        helmet_save=7, shield_and_skill_effects=EffectSet())


class Tape:
    def __init__(self, *values):
        self.values = list(values)

    def integers(self, low, high, size=None):
        count = 1 if size is None else int(size)
        assert len(self.values) >= count, "unexpected extra die"
        drawn, self.values = self.values[:count], self.values[count:]
        return np.asarray(drawn, dtype=np.int8)

    def random(self, size=None):
        return np.zeros(size)


def _defender(*, skill=True, mounted=False, heavy=True, shield="defence.shield",
              armour=4, natural=7):
    tags = (("skill.armour-specialist",) if skill else ()) + (
        "armour.heavy-armour" if heavy else "armour.light-armour",)
    return replace(_base(), global_effects=EffectSet(tags=tags), mounted=mounted,
        armour_save=armour, natural_armour_save=natural,
        shield_and_skill_effects=EffectSet(tags=(shield,) if shield else (), armour_save_bonus=1))


def _wounds(defender, strength, rolls, **modifiers):
    weapon = EffectSet(tags=("weapon.mace", "effect.no-critical"),
        automatic_hit=True, cannot_be_parried=True, fixed_strength=strength, **modifiers)
    attacker = replace(_base(), main_weapon=weapon,
        characteristics=replace(_base().characteristics, initiative=5))
    tape = Tape(*rolls)
    result = native.simulate_batch_observed(attacker, defender, 1, tape, 1,
        context=DuelContext(charging=(), active_participant="first"))
    assert not tape.values
    return int(result.second_wounds[0])


@pytest.mark.parametrize("strength,modifiers,target", [
    (3, {}, 4), (4, {}, 5), (5, {}, 5), (8, {}, 5),
    (8, {"armour_penetration": 1}, 6),
    (8, {"target_armour_bonus": -1}, 6),
    (8, {"target_armour_bonus": 1}, 4),
])
def test_armour_specialist_caps_strength_before_other_armour_modifiers(strength, modifiers, target):
    defender = _defender()
    assert _wounds(defender, strength, (4, target - 1, 1), **modifiers) == 2
    assert _wounds(defender, strength, (4, target, 1), **modifiers) == 3


@pytest.mark.parametrize("options", [
    {"skill": False}, {"mounted": True}, {"heavy": False},
    {"shield": None}, {"shield": "defence.buckler"},
])
def test_armour_specialist_requires_the_printed_skill_equipment_and_foot_bearer(options):
    assert _wounds(_defender(**options), 6, (4, 1)) == 2


def test_armour_specialist_accepts_a_kite_shield_without_improving_a_bad_base_or_natural_save():
    assert _wounds(_defender(shield="defence.kite-shield", armour=3), 8, (4, 5, 1)) == 3
    # A worsened 6+ worn save stays 6+; the natural 4+ still takes the full
    # Strength-5 penalty and becomes 6+, so a 5 fails both saves.
    assert _wounds(_defender(armour=6, natural=4), 5, (4, 5, 1)) == 2
    assert _wounds(_defender(armour=6, natural=4), 5, (4, 6, 1)) == 3


@pytest.mark.parametrize("modifier", ["ignore_armour", "ignore_armour_except_shield_and_skills"])
def test_armour_specialist_adds_no_protection_when_worn_armour_is_ignored(modifier):
    # Keep the existing ignore-armour behavior unchanged; the skill cannot
    # introduce a new save when the unskilled profile has none.
    assert _wounds(_defender(), 8, (4, 1), **{modifier: True}) == 2
    assert _wounds(_defender(skill=False), 8, (4, 1), **{modifier: True}) == 2
