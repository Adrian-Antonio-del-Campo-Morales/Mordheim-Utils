"""Scripted single-duel execution for the native replay-driver contracts.

The native extension consumes NumPy-style binary/integer draws, so a recorded
tape is replayed through the real compiled batch core.  This helper observes
driver behaviour only; it does not compare engines.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mordheim_combat.native import simulate_batch_observed
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelContext
from tests.engines.shared.dice import StrictDice
from tests.engines.shared.dice import StrictDecisions


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


def replay_duel(first: CompiledFighter, second: CompiledFighter, *,
                rolls: list[dict], choices: list[dict] | None = None,
                maximum_rounds: int = 1,
                context: DuelContext | None = None) -> ReplayObservation:
    """Observe one native batch; an unavailable or unsupported duel never falls back."""
    if maximum_rounds < 1:
        raise ValueError("maximum rounds must be positive")
    decisions = StrictDecisions(choices or [])
    rng = ReplayRng(rolls)
    result = simulate_batch_observed(
        first, second, 1, rng, maximum_rounds, decisions, context=context,
    )
    dice = rng.dice
    resources = []
    for fighter, entries in zip(
        (first, second), (result.first_resources, result.second_resources),
    ):
        # The legacy lucky-charm flag is false even when unowned.
        resources.append(frozenset(
            name for name, values in entries if bool(values[0])
            and (name != "lucky-charm"
                 or "defence.lucky-charm" in fighter.global_effects.tags)
        ))
    winner = {1: 0, -1: 1, 0: 2}[int(result.winner[0])]
    observation = (
        winner, int(result.rounds[0]),
        (int(result.first_wounds[0]), int(result.second_wounds[0])),
        (int(result.first_condition[0]), int(result.second_condition[0])),
        tuple(resources),
    )
    dice.finish()
    decisions.finish()
    return ReplayObservation(*observation, tuple(dice.requests), tuple(decisions.requests))
