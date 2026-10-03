"""Strict, single-duel replay through each engine's real round driver.

Scripts are authored separately for the scalar and optimized draw orders.
They do not pretend that historical backend seeds or physical streams match.
No random draw, decision, engine fallback, or unused fixture is tolerated.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter, DuelContext
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions


class ReplayRng:
    """NumPy-compatible bounded draws backed by existing strict dice.

    Integer requests use ``draw.<index>.integer``; binary charge/priority
    requests use ``draw.<index>.binary`` (1 selects first, 2 selects second).
    Values and sides are checked even when a native caller requests one row.
    """
    def __init__(self, rolls: list[dict]):
        self.dice = StrictDice(rolls)

    def _draw(self, kind: str, sides: int) -> int:
        return self.dice.roll(RollRequest(f"draw.{len(self.dice.requests)}.{kind}", sides))

    def integers(self, low, high=None, size=None, dtype=None):
        if high is None or low != 1 or high <= low:
            raise ValueError("replay requires an explicit die interval starting at one")
        shape = () if size is None else size
        count = int(np.prod(shape)) if isinstance(shape, tuple) else int(shape or 1)
        if size == 0:
            count = 0
        values = [self._draw("integer", high - 1) for _ in range(count)]
        return np.asarray(values, dtype=dtype).reshape(shape) if size is not None else values[0]

    def random(self, size=None):
        shape = () if size is None else size
        count = int(np.prod(shape)) if isinstance(shape, tuple) else int(shape or 1)
        if size == 0:
            count = 0
        values = [0.0 if self._draw("binary", 2) == 1 else 0.75 for _ in range(count)]
        return np.asarray(values).reshape(shape) if size is not None else values[0]

    def finish(self):
        self.dice.finish()


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
    elif backend in {"numpy", "native"}:
        from mordheim_combat.kernel import compile_duel_plan
        plan = compile_duel_plan(first, second, context=context)
        if backend == "native":
            from mordheim_combat import _combat_native as engine
            if getattr(engine, "CONTEXT_VERSION", None) != 1 or not hasattr(engine, "simulate_batch_observed"):
                raise RuntimeError("native replay extension is stale; rebuild it")
            if not plan.optimization_eligible or not engine.supports_plan(plan):
                raise RuntimeError("native replay does not support this duel plan")
        else:
            from mordheim_combat import vectorized as engine
        rng = ReplayRng(rolls)
        result = engine.simulate_batch_observed(
            first, second, 1, rng, maximum_rounds, decisions, context=context)
        dice = rng.dice
        resources = []
        for fighter, entries in zip((first, second), (result.first_resources, result.second_resources)):
            # The vector legacy lucky-charm flag is false even when unowned.
            resources.append(frozenset(name for name, values in entries if bool(values[0])
                and (name != "lucky-charm" or "defence.lucky-charm" in fighter.global_effects.tags)))
        winner = {1: 0, -1: 1, 0: 2}[int(result.winner[0])]
        observation = (winner, int(result.rounds[0]),
                       (int(result.first_wounds[0]), int(result.second_wounds[0])),
                       (int(result.first_condition[0]), int(result.second_condition[0])),
                       tuple(resources))
    else:
        raise ValueError(f"unknown replay backend: {backend}")
    dice.finish()
    decisions.finish()
    return ReplayObservation(backend, *observation, tuple(dice.requests), tuple(decisions.requests))
