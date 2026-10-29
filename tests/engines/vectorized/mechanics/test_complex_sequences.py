"""Minimal sequences of complex rules."""
from __future__ import annotations

from mordheim_combat.vectorized import KNOCKED_DOWN
from mordheim_combat.vectorized import OUT
from mordheim_combat.vectorized import STANDING
from mordheim_combat.vectorized import _black_hunger_backlash
from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _resolve_fire
from mordheim_combat.vectorized import _resolve_netter_charge
import numpy as np
import pytest




class ScriptedRng:
    def __init__(self, *values):
        self.values = list(values)

    def integers(self, low, high=None, size=None, dtype=None):
        value = self.values.pop(0)
        result = np.asarray(
            value if np.ndim(value) else np.full(size or 1, value),
            dtype=dtype,
        )
        return result if size is not None else result.item()


def test_netter_minimal_sequence_distinguishes_miss_escape_and_capture(vector_case):
    case = vector_case(
        "unit/modular/test_complex_sequences/test_netter_minimal_sequence_distinguishes_miss_escape_and_capture-0-0"
    )
    # The KB retires the net-throwing technique (`grant: none`): the caller supplies
    # the caught victim's condition and no construction selects the producer.  The
    # vectorized helper keeps its regression tape, so its tag is a fixture fact.
    netter = case.first
    target = case.second

    for dice, expected in (((1, 6), STANDING), ((6, 1), STANDING), ((6, 6), KNOCKED_DOWN)):
        netter_state = _new_state(netter, 1, ScriptedRng())
        target_state = _new_state(target, 1, ScriptedRng())
        caught = _resolve_netter_charge(
            netter, target, np.array([0]), netter_state, target_state,
            ScriptedRng(*dice),
        )
        assert target_state.condition[0] == expected
        assert caught.tolist() == ([0] if expected == KNOCKED_DOWN else [])


def test_fire_persists_after_failed_recovery_and_stops_after_extinguishing(vector_case):
    case = vector_case(
        "unit/modular/test_complex_sequences/test_fire_persists_after_failed_recovery_and_stops_after_extinguishing-0-0"
    )
    victim, opponent = case.first, case.second
    victim_state = _new_state(victim, 1, ScriptedRng())
    opponent_state = _new_state(opponent, 1, ScriptedRng())
    victim_state.on_fire[0] = True

    _resolve_fire(victim, opponent, victim_state, opponent_state, ScriptedRng(1, 1))
    assert victim_state.on_fire[0]
    _resolve_fire(victim, opponent, victim_state, opponent_state, ScriptedRng(4))
    assert not victim_state.on_fire[0]


def test_black_hunger_backlash_is_a_real_self_attack_after_the_round(vector_case):
    case = vector_case(
        "unit/modular/test_complex_sequences/test_black_hunger_backlash_is_a_real_self_attack_after_the_round-0-0"
    )
    hungry = case.first
    state = _new_state(hungry, 1, ScriptedRng())
    assert state.condition[0] == STANDING
    _black_hunger_backlash(hungry, state, np.array([0]), ScriptedRng(1, 6, 6, 6))
    assert state.condition[0] == OUT
