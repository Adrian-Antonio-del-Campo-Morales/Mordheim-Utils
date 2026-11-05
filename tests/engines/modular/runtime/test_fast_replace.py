"""Fast state replace and the combined-effect cache: accessory-path guards.

These two optimizations must be observationally identical to the stdlib
paths they replace, and must keep the debugging guarantees: a mistyped
field raises, classes with ``__post_init__`` are refused, the effect cache
is value-keyed so injected effect sets never hit a stale entry, and the
debug cross-check catches any divergence.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace as std_replace

import pytest

from mordheim_combat.modular import _fast_replace
from mordheim_combat.modular.contexts import (
    _combined_effect,
    clear_combined_effect_cache,
)
from mordheim_combat.modular.state import DuelState, FighterState
from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet


def test_fast_replace_matches_dataclasses_replace():
    state = FighterState(wounds=3, weapon_skill=4, strength=3,
                         resources_spent=frozenset({"luck"}))
    duel = DuelState(state, FighterState(wounds=1), round_index=2)
    assert _fast_replace.replace(state, wounds=2) == std_replace(state, wounds=2)
    assert _fast_replace.replace(state) == state
    changed = _fast_replace.replace(duel, first=std_replace(state, wounds=0),
                                    round_index=3)
    assert changed == std_replace(duel, first=std_replace(state, wounds=0),
                                  round_index=3)
    # The produced instance is a real frozen FighterState.
    produced = _fast_replace.replace(state, wounds=2)
    assert type(produced) is FighterState
    with pytest.raises(FrozenInstanceError):
        produced.wounds = 5  # type: ignore[misc]


def test_unknown_field_raises_instead_of_silently_ignoring():
    state = FighterState(wounds=3)
    with pytest.raises(TypeError, match="wuonds"):
        _fast_replace.replace(state, wuonds=2)


def test_unregistered_dataclasses_fall_through_to_the_stdlib_path():
    effect = EffectSet(strength_bonus=1)
    assert _fast_replace.replace(effect, hit_modifier=2) == std_replace(
        effect, hit_modifier=2)
    with pytest.raises(TypeError):
        _fast_replace.replace(effect, not_a_field=1)


def test_classes_with_post_init_are_refused_registration():
    @dataclass(frozen=True)
    class Guarded:
        value: int

        def __post_init__(self):
            if self.value < 0:
                raise ValueError("negative")

    with pytest.raises(TypeError, match="__post_init__"):
        _fast_replace.register(Guarded)


def test_debug_cross_check_validates_every_call(monkeypatch):
    monkeypatch.setattr(_fast_replace, "_DEBUG_CROSS_CHECK", True)
    state = FighterState(wounds=3)
    assert _fast_replace.replace(state, wounds=1) == std_replace(state, wounds=1)
    # A diverging copier is caught immediately.
    broken = lambda obj, changes: std_replace(obj, wounds=99)
    monkeypatch.setitem(_fast_replace._COPIERS, FighterState, broken)
    with pytest.raises(AssertionError, match="diverged"):
        _fast_replace.replace(state, wounds=1)


class _Fighter:
    def __init__(self, global_effects):
        self.global_effects = global_effects


def test_combined_effect_cache_is_value_keyed_and_transparent():
    clear_combined_effect_cache()
    weapon = EffectSet(tags=("weapon.sword",), parry=True)
    globals_ = EffectSet(tags=("skill.luck",), strength_bonus=1)
    merged = _combined_effect(_Fighter(globals_), weapon)
    assert merged == merge_effects(weapon, globals_)
    # An equal-but-distinct pair shares the cached result (hit by value)...
    again = _combined_effect(
        _Fighter(EffectSet(tags=("skill.luck",), strength_bonus=1)),
        EffectSet(tags=("weapon.sword",), parry=True))
    assert again is merged
    # ...while an injected, modified effect set misses and merges fresh.
    doctored = _combined_effect(
        _Fighter(globals_), EffectSet(tags=("weapon.sword",), hit_modifier=1))
    assert doctored != merged
    assert doctored == merge_effects(
        EffectSet(tags=("weapon.sword",), hit_modifier=1), globals_)
    clear_combined_effect_cache()


def test_combined_effect_keeps_the_transient_attack_exemptions():
    clear_combined_effect_cache()
    slam = EffectSet(tags=("mechanic.body-slam",), fixed_strength=4)
    assert _combined_effect(
        _Fighter(EffectSet(strength_bonus=2)), slam) is slam
