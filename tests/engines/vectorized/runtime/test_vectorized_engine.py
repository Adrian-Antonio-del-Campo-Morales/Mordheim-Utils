"""Vectorized simulator execution, isolation and request contracts."""
from __future__ import annotations

from threading import Event

import numpy as np
import pytest

from mordheim_combat.vectorized import simulate_duel
from mordheim_core.models import DuelRequest
from mordheim_core.models import SimulationCancelled

class FixedRng:
    def __init__(self, *values): self.values=list(values)
    def integers(self, low, high=None, size=None, dtype=None):
        value=self.values.pop(0)
        result=np.asarray(value if np.ndim(value) else np.full(size or 1,value),dtype=dtype)
        return result if size is not None else result.item()

def test_seeded_duel_is_reproducible_and_counts_are_complete(vector_case):
    case=vector_case("test_vectorized_engine/test_seeded_duel_is_reproducible_and_counts_are_complete-0-0")
    request=DuelRequest(case.first,case.second,10_000,seed=91,batch_size=2_000)
    first=simulate_duel(request);second=simulate_duel(request)
    assert first==second
    assert first.first_wins+first.second_wins+first.unresolved==10_000
    assert pytest.approx(first.first_win_rate+first.second_win_rate+first.unresolved_rate)==100

def test_symmetric_duel_is_statistically_symmetric_across_chunk_sizes(vector_case):
    case=vector_case("test_vectorized_engine/test_symmetric_duel_is_statistically_symmetric_across_chunk_sizes-0-0")
    unit=case.first
    small=simulate_duel(DuelRequest(unit,unit,20_000,seed=7,batch_size=1_000))
    large=simulate_duel(DuelRequest(unit,unit,20_000,seed=7,batch_size=20_000))
    assert abs(small.first_win_rate-small.second_win_rate)<2
    assert abs(large.first_win_rate-large.second_win_rate)<2
    assert abs(small.first_win_rate-large.first_win_rate)<2

def test_cancellation_is_checked_between_batches(vector_case):
    case=vector_case("test_vectorized_engine/test_cancellation_is_checked_between_batches-0-0")
    event=Event();event.set()
    with pytest.raises(SimulationCancelled):simulate_duel(DuelRequest(case.first,case.second,100,cancel_event=event))

def test_invalid_request_and_result_are_rejected(vector_case):
    from mordheim_core.models import DuelResult
    case=vector_case("test_vectorized_engine/test_invalid_request_and_result_are_rejected-0-0")
    with pytest.raises(ValueError):DuelRequest(case.first,case.second,0)
    with pytest.raises(ValueError):DuelResult(1,1,1,2)

def test_charge_conditions_are_isolated_per_vector_row(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    from mordheim_core.models import EffectSet
    case=vector_case("test_vectorized_engine/test_charge_conditions_are_isolated_per_vector_row-0-0")
    attacker,defender=case.first,case.second
    attacker_state=_new_state(attacker,2,np.random.default_rng(1));defender_state=_new_state(defender,2,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0,1]),np.array([True,False]),attacker_state,defender_state,FixedRng([1,1],6,1),True)
    assert defender_state.entangled.tolist()==[True,False]

def test_random_profile_characteristics_are_rolled_per_simulation_row(vector_case):
    from mordheim_combat.vectorized import _new_state
    case=vector_case("test_vectorized_engine/test_random_profile_characteristics_are_rolled_per_simulation_row-0-0")
    condemned=case.first
    condemned_state=_new_state(condemned,200,np.random.default_rng(41))
    assert condemned_state.weapon_skill.min()>=1 and condemned_state.weapon_skill.max()<=6
    assert condemned_state.strength.min()>=1 and condemned_state.strength.max()<=6
    assert condemned_state.toughness.min()>=1 and condemned_state.toughness.max()<=6
    assert condemned_state.attacks.min()>=1 and condemned_state.attacks.max()<=3
    for values in (condemned_state.weapon_skill, condemned_state.strength,
                   condemned_state.toughness, condemned_state.attacks):
        assert np.unique(values).size>1
    # Spawn's D6+1 is rolled per round, not by _new_state. Its live attack
    # pool is covered by test_spawn_special_attacks_replaces_the_pool_with_one_die_plus_one.
