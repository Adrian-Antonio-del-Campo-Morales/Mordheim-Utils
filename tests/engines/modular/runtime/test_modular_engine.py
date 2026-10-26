"""Integration of the modular engine."""
from __future__ import annotations

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.duel import simulate_duel_reference
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import DuelState
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import build_attacks
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import KeyedDice
from mordheim_core.dice import ScriptedDice
from mordheim_core.models import SimulationCancelled
import pytest as pytest
from threading import Event


def test_scalar_attack_pool_has_no_dependency_on_the_vectorized_engine(monkeypatch, precompiled):
    import mordheim_combat.vectorized as engine

    monkeypatch.setattr(engine, "attack_count", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))
    assert build_attacks(AttackPoolContext(precompiled().first)).attacks == 2


def test_reference_round_generates_priority_attacks_and_aftermath_itself(precompiled):
    compiled = precompiled()
    first, second = compiled.first, compiled.second
    state = DuelState(
        initialize_fighter(first, KeyedDice(1), "first"),
        initialize_fighter(second, KeyedDice(2), "second"),
        first_charged=True,
    )
    result = resolve_round(first, second, state, KeyedDice(7), AlwaysAccept())
    assert result.state.round_index == 1
    assert result.state.trace[0].value == "priority"
    assert result.state.trace[-1].value == "aftermath"
    assert result.attacks


def test_reference_duels_are_reproducible_without_calling_numpy_executor(monkeypatch, precompiled):
    import mordheim_combat.vectorized as engine

    monkeypatch.setattr(engine, "simulate_duel", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))
    compiled = precompiled()
    first, second = compiled.first, compiled.second
    a = simulate_duel_reference(first, second, 20, seed=17, maximum_rounds=10)
    b = simulate_duel_reference(first, second, 20, seed=17, maximum_rounds=10)
    assert a == b
    assert a.first_wins + a.second_wins + a.unresolved == 20


def test_reference_duel_honours_cancellation_and_maximum_rounds(precompiled):
    duelist = precompiled().first
    cancelled = Event()
    cancelled.set()
    with pytest.raises(SimulationCancelled):
        simulate_duel_reference(duelist, duelist, 2, cancel_event=cancelled)
    result = simulate_duel_reference(duelist, duelist, 5, seed=4, maximum_rounds=1)
    assert result.simulations == 5
