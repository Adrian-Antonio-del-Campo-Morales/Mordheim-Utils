"""domain.dice: responsibility extracted without altering the rules."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
import numpy as np
from typing import Callable
from typing import Hashable
from typing import Mapping
from typing import Protocol
from typing import Sequence
from typing import TypeVar


@dataclass(frozen=True, slots=True)
class RollRequest:
    """Semantic identity of one die roll.

    ``key`` is intentionally meaningful rather than a stream position.  A
    future optimized engine can therefore request rolls in a different order
    and still replay the same combat through ``KeyedDice``.
    """

    key: str
    sides: int = 6

    def __post_init__(self) -> None:
        if self.sides < 2:
            raise ValueError("a die must have at least two sides")
        if not self.key:
            raise ValueError("a roll request needs a semantic key")


class DiceSource(Protocol):
    def roll(self, request: RollRequest) -> int: ...


class SeededDice:
    """Ordinary deterministic source used by scalar simulations."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = np.random.default_rng(seed)

    def roll(self, request: RollRequest) -> int:
        return int(self._rng.integers(1, request.sides + 1))


class ScriptedDice:
    """A strict roll tape for focused phase and interaction tests."""

    def __init__(self, values: Sequence[int] | Mapping[str, int]) -> None:
        self._mapping = dict(values) if isinstance(values, Mapping) else None
        self._values = iter(values) if not isinstance(values, Mapping) else None

    def roll(self, request: RollRequest) -> int:
        if self._mapping is not None:
            if request.key not in self._mapping:
                raise KeyError(f"no scripted value for {request.key}")
            value = int(self._mapping[request.key])
        else:
            try:
                value = int(next(self._values))  # type: ignore[arg-type]
            except StopIteration as exc:
                raise RuntimeError(f"dice tape exhausted at {request.key}") from exc
        if not 1 <= value <= request.sides:
            raise ValueError(f"scripted {request.key} roll {value} is not a D{request.sides} result")
        return value


class KeyedDice:
    """Order-independent deterministic dice keyed by semantic roll identity."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = int(seed)

    def roll(self, request: RollRequest) -> int:
        # Python's hash is process-randomized; SeedSequence receives stable
        # UTF-8 bytes instead so persisted traces replay across processes.
        entropy = [self.seed, request.sides, *request.key.encode("utf-8")]
        rng = np.random.default_rng(np.random.SeedSequence(entropy))
        return int(rng.integers(1, request.sides + 1))


class DecisionPolicy(Protocol):
    def choose(self, key: str, context: object | None = None) -> bool: ...


class AlwaysAccept:
    def choose(self, key: str, context: object | None = None) -> bool:
        return True


class AlwaysReject:
    def choose(self, key: str, context: object | None = None) -> bool:
        return False


class ScriptedDecisions:
    def __init__(self, choices: Mapping[str, bool]) -> None:
        self._choices = dict(choices)

    def choose(self, key: str, context: object | None = None) -> bool:
        if key not in self._choices:
            raise KeyError(f"no scripted decision for {key}")
        return bool(self._choices[key])


T = TypeVar("T", bound=Hashable)


def exact_distribution(
    roll_sides: Sequence[int], resolver: Callable[[tuple[int, ...]], T]
) -> dict[T, Fraction]:
    """Enumerate a finite local resolution and return exact probabilities."""

    if any(sides < 2 for sides in roll_sides):
        raise ValueError("all enumerated dice must have at least two sides")
    counts: Counter[T] = Counter()
    for values in product(*(range(1, sides + 1) for sides in roll_sides)):
        counts[resolver(tuple(values))] += 1
    denominator = 1
    for sides in roll_sides:
        denominator *= sides
    return {outcome: Fraction(count, denominator) for outcome, count in counts.items()}
