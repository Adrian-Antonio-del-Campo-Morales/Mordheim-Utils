"""Pure phase contracts."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from mordheim_combat.phases import ArmourContext
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import BearHugContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import HitContext
from mordheim_combat.phases import InjuryContext
from mordheim_combat.phases import ParryContext
from mordheim_combat.phases import Phase
from mordheim_combat.phases import PriorityContext
from mordheim_combat.phases import RoundContext
from mordheim_combat.phases import SpecialSaveContext
from mordheim_combat.phases import StrikeContext
from mordheim_combat.phases import WoundContext
from mordheim_combat.phases import armour_target
from mordheim_combat.phases import build_attacks
from mordheim_combat.phases import resolve_armour
from mordheim_combat.phases import resolve_attack
from mordheim_combat.phases import resolve_bear_hug
from mordheim_combat.phases import resolve_hit
from mordheim_combat.phases import resolve_injury
from mordheim_combat.phases import resolve_parry
from mordheim_combat.phases import resolve_priority
from mordheim_combat.phases import resolve_strike_sequence
from mordheim_combat.phases import resolve_special_save
from mordheim_combat.phases import resolve_wound
from mordheim_combat.phases import to_hit_target
from mordheim_combat.phases import wound_target
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import AlwaysReject
from mordheim_core.dice import KeyedDice
from mordheim_core.dice import RollRequest
from mordheim_core.dice import ScriptedDice
from mordheim_core.dice import exact_distribution
import numpy as np
import pytest as pytest


class VectorTape:
    def __init__(self,*values):
        self.values=list(values)

    def integers(self,low,high=None,size=None,dtype=None):
        value=self.values.pop(0)
        result=np.asarray(value if np.ndim(value) else np.full(size or 1,value),dtype=dtype)
        return result if size is not None else result.item()


@pytest.fixture
def precompiled(shared_precompiled):
    """Resolve this module's historical ``unit/shared`` case."""
    return shared_precompiled


# The assertion consumes the vectorized attack orchestrator, not the modular
# oracle, so the item belongs to the backend it executes.
def test_production_attack_orchestrator_aggregates_bear_hug_across_two_attacks(precompiled):
    from mordheim_combat.vectorized import OUT
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import resolve_attacks

    compiled = precompiled()
    attacker = compiled.first
    defender = compiled.second
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    resolve_attacks(
        attacker,defender,np.array([0]),np.array([2]),np.array([False]),
        attacker_state,defender_state,VectorTape(6,6,3,4,5),False,AlwaysAccept(),
    )
    # Strength 4 + 3 ties Strength 3 + 4, so the Bear wins. The two normal
    # hits are replaced by one automatic wound and no armour roll is consumed.
    assert defender_state.condition.tolist()==[OUT]

    defender_state=_new_state(defender,1,np.random.default_rng(3))
    resolve_attacks(
        attacker,defender,np.array([0]),np.array([2]),np.array([False]),
        _new_state(attacker,1,np.random.default_rng(4)),defender_state,
        VectorTape(6,6,1,1),False,AlwaysReject(),
    )
    assert defender_state.wounds.tolist()==[1]
