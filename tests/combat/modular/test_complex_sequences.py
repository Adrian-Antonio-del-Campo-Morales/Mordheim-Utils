"""Secuencias mínimas de reglas complejas."""
from __future__ import annotations

from mordheim_combat.vectorized import KNOCKED_DOWN
from mordheim_combat.vectorized import OUT
from mordheim_combat.vectorized import STANDING
from mordheim_combat.vectorized import _black_hunger_backlash
from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _resolve_fire
from mordheim_combat.vectorized import _resolve_netter_charge
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild
import numpy as np


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


def ordinary(*, strength=3, wounds=1):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, strength, 3, wounds, 3, 1),
    ))


def test_netter_minimal_sequence_distinguishes_miss_escape_and_capture():
    netter = compile_fighter(FighterBuild(
        "mordheim", band_id="night-goblins-mic", profile_id="big-boss",
        special_rule_ids=("band--night-goblin-special-skills-netter",),
    ))
    target = ordinary(strength=3)

    for dice, expected in (((1, 6), STANDING), ((6, 1), STANDING), ((6, 6), KNOCKED_DOWN)):
        netter_state = _new_state(netter, 1, ScriptedRng())
        target_state = _new_state(target, 1, ScriptedRng())
        caught = _resolve_netter_charge(
            netter, target, np.array([0]), netter_state, target_state,
            ScriptedRng(*dice),
        )
        assert target_state.condition[0] == expected
        assert caught.tolist() == ([0] if expected == KNOCKED_DOWN else [])


def test_fire_persists_after_failed_recovery_and_stops_after_extinguishing():
    victim, opponent = ordinary(wounds=2), ordinary()
    victim_state = _new_state(victim, 1, ScriptedRng())
    opponent_state = _new_state(opponent, 1, ScriptedRng())
    victim_state.on_fire[0] = True

    _resolve_fire(victim, opponent, victim_state, opponent_state, ScriptedRng(1, 1))
    assert victim_state.on_fire[0]
    _resolve_fire(victim, opponent, victim_state, opponent_state, ScriptedRng(4))
    assert not victim_state.on_fire[0]


def test_black_hunger_backlash_is_a_real_self_attack_after_the_round():
    hungry = compile_fighter(FighterBuild(
        "mordheim", band_id="skaven-clan-eshin", profile_id="assassin-adept",
        special_rule_ids=("band--skaven-special-skills-black-hunger",),
    ))
    state = _new_state(hungry, 1, ScriptedRng())
    assert state.condition[0] == STANDING
    _black_hunger_backlash(hungry, state, np.array([0]), ScriptedRng(1, 6, 6, 6))
    assert state.condition[0] == OUT
