"""combat.modular.duel: responsibility extracted without altering the rules."""
from __future__ import annotations

import numpy as np

from mordheim_combat.modular import rounds
from mordheim_combat.modular.state import initialize_duel
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import SeededDice
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelResult
from mordheim_core.models import ObservedDuelResult
from mordheim_core.models import SimulationCancelled


def simulate_duel_reference(
    first: CompiledFighter, second: CompiledFighter, simulations: int,
    *, seed: int = 0, maximum_rounds: int = 50,
    decisions: DecisionPolicy | None = None,
    cancel_event: object | None = None,
) -> DuelResult:
    """Scalar simulator under test; each simulation has a replayable dice stream."""
    if min(simulations, maximum_rounds) < 1:
        raise ValueError("simulation limits must be positive")
    wins_first = wins_second = unresolved = 0
    for simulation in range(simulations):
        if cancel_event is not None and getattr(cancel_event, "is_set")():
            raise SimulationCancelled("scalar simulation cancelled")
        dice = SeededDice(seed + simulation)
        state = initialize_duel(first, second, dice)
        for _ in range(maximum_rounds):
            if cancel_event is not None and getattr(cancel_event, "is_set")():
                raise SimulationCancelled("scalar simulation cancelled")
            if not state.first.active or not state.second.active:
                break
            state = rounds.resolve_round(first, second, state, dice, decisions).state
        if state.first.active and not state.second.active:
            wins_first += 1
        elif state.second.active and not state.first.active:
            wins_second += 1
        else:
            unresolved += 1
    return DuelResult(wins_first, wins_second, unresolved, simulations)


def simulate_duel_observed(
    first: CompiledFighter, second: CompiledFighter, simulations: int,
    *, seed: int = 0, maximum_rounds: int = 50,
    decisions: DecisionPolicy | None = None,
    cancel_event: object | None = None,
) -> ObservedDuelResult:
    """Run one oracle sample and keep the per-duel terminal records.

    Adds no new behaviour: the same deterministic duel stream and counting
    rules as ``simulate_duel_reference``, recorded row by row so
    verification can compare whole distributions (resolution rounds,
    remaining wounds, conditions) instead of only the three aggregate
    counts.  ``as_result()`` reproduces the aggregate sample exactly, so the
    observed leg can replace a counting leg without changing the certified
    numbers.  ``resolution_rounds`` mirrors the vectorized driver's per-row
    ledger: the rounds executed before the duel ended (1..maximum_rounds),
    with ``maximum_rounds`` for duels that ran out of budget (unresolved).
    """
    if min(simulations, maximum_rounds) < 1:
        raise ValueError("simulation limits must be positive")
    winner = np.zeros(simulations, dtype=np.int8)
    resolution_rounds = np.zeros(simulations, dtype=np.int16)
    first_wounds = np.zeros(simulations, dtype=np.int16)
    second_wounds = np.zeros(simulations, dtype=np.int16)
    first_condition = np.zeros(simulations, dtype=np.int8)
    second_condition = np.zeros(simulations, dtype=np.int8)
    for simulation in range(simulations):
        if cancel_event is not None and getattr(cancel_event, "is_set")():
            raise SimulationCancelled("scalar simulation cancelled")
        dice = SeededDice(seed + simulation)
        state = initialize_duel(first, second, dice)
        rounds_executed = 0
        for _ in range(maximum_rounds):
            if cancel_event is not None and getattr(cancel_event, "is_set")():
                raise SimulationCancelled("scalar simulation cancelled")
            if not state.first.active or not state.second.active:
                break
            state = rounds.resolve_round(first, second, state, dice, decisions).state
            rounds_executed += 1
        if state.first.active and not state.second.active:
            outcome = 0
        elif state.second.active and not state.first.active:
            outcome = 1
        else:
            outcome = 2
        winner[simulation] = outcome
        resolution_rounds[simulation] = rounds_executed
        first_wounds[simulation] = state.first.wounds
        second_wounds[simulation] = state.second.wounds
        first_condition[simulation] = int(state.first.condition)
        second_condition[simulation] = int(state.second.condition)
    return ObservedDuelResult(
        winner, resolution_rounds, first_wounds, second_wounds,
        first_condition, second_condition, simulations, maximum_rounds,
    )


def simulate_duel(request) -> DuelResult:
    """Accept the same `DuelRequest` consumed by the vectorized engine."""
    return simulate_duel_reference(
        request.first, request.second, request.simulations,
        seed=request.seed, maximum_rounds=request.maximum_rounds,
        decisions=request.decision_policy, cancel_event=request.cancel_event,
    )
