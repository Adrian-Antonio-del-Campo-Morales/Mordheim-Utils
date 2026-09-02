"""combat.modular.duel: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_combat_lab.combat.modular import rounds
from mordheim_combat_lab.combat.modular.state import initialize_duel
from mordheim_combat_lab.domain.dice import DecisionPolicy
from mordheim_combat_lab.domain.dice import SeededDice
from mordheim_combat_lab.domain.models import CompiledFighter
from mordheim_combat_lab.domain.models import DuelResult
from mordheim_combat_lab.domain.models import SimulationCancelled


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


def simulate_duel(request) -> DuelResult:
    """Adaptar el mismo `DuelRequest` que consume el motor vectorizado."""
    return simulate_duel_reference(
        request.first, request.second, request.simulations,
        seed=request.seed, maximum_rounds=request.maximum_rounds,
        decisions=request.decision_policy, cancel_event=request.cancel_event,
    )
