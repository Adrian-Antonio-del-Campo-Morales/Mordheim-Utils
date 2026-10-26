"""Scripted single-duel execution for existing modular rule tests.

No optimized-engine replay or cross-engine parity is provided by this helper.
"""
from __future__ import annotations

from dataclasses import dataclass
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter, DuelContext
from tests.engines.shared.dice import StrictDice, StrictDecisions


@dataclass(frozen=True, slots=True)
class ReplayObservation:
    backend: str
    winner: int
    rounds: int
    wounds: tuple[int, int]
    conditions: tuple[int, int]
    resources: tuple[frozenset[str], frozenset[str]]
    rolls: tuple[RollRequest, ...]
    decisions: tuple[str, ...]

    @property
    def terminal(self):
        return self.winner, self.rounds, self.wounds, self.conditions, self.resources



def replay_duel(first: CompiledFighter, second: CompiledFighter, *, backend: str,
                rolls: list[dict], choices: list[dict] | None = None,
                maximum_rounds: int = 1, context: DuelContext | None = None) -> ReplayObservation:
    """Observe actual engine execution; explicit native never falls back."""
    if maximum_rounds < 1:
        raise ValueError("maximum rounds must be positive")
    decisions = StrictDecisions(choices or [])
    if backend == "modular":
        from mordheim_combat.modular.state import initialize_duel
        from mordheim_combat.modular.rounds import resolve_round
        dice = StrictDice(rolls)
        state = initialize_duel(first, second, dice, context=context)
        for _ in range(maximum_rounds):
            if not state.first.active or not state.second.active:
                break
            state = resolve_round(first, second, state, dice, decisions).state
        winner = 0 if state.first.active and not state.second.active else (
            1 if state.second.active and not state.first.active else 2)
        observation = (winner, state.round_index,
                       (state.first.wounds, state.second.wounds),
                       (int(state.first.condition), int(state.second.condition)),
                       tuple(frozenset(name for name in local.resources_spent if not name.startswith("disability.")) | ({"lucky-charm"} if not local.lucky_charm
                            and "defence.lucky-charm" in fighter.global_effects.tags else set())
                            for fighter, local in ((first, state.first), (second, state.second))))
    else:
        raise ValueError("slice replay supports only the modular engine")
    dice.finish()
    decisions.finish()
    return ReplayObservation(backend, *observation, tuple(dice.requests), tuple(decisions.requests))

