"""verification.dice: responsibility extracted without altering the rules."""
from __future__ import annotations

from fractions import Fraction
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from typing import Callable


class StrictDice:
    def __init__(self, rolls: list[dict]):
        self.rolls = rolls
        self.requests: list[RollRequest] = []

    def roll(self, request: RollRequest) -> int:
        index = len(self.requests)
        self.requests.append(request)
        if index >= len(self.rolls):
            raise EvidenceMismatch(f"unexpected roll {request.key} D{request.sides}")
        expected = self.rolls[index]
        if expected["key"] != request.key or expected.get("sides", 6) != request.sides:
            raise EvidenceMismatch(f"roll {index}: expected {expected}, got {request}")
        value = expected["value"]
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= request.sides:
            raise ValueError(f"invalid fixture die: {expected}")
        return value

    def finish(self):
        if len(self.requests) != len(self.rolls):
            raise EvidenceMismatch(f"unused rolls: {self.rolls[len(self.requests):]}")


class StrictDecisions:
    def __init__(self, choices: list[dict]):
        self.choices = choices
        self.used = 0
        self.requests: list[str] = []

    def choose(self, key: str, context: object | None = None) -> bool:
        self.requests.append(key)
        if self.used >= len(self.choices):
            raise EvidenceMismatch(f"unexpected decision {key}")
        expected = self.choices[self.used]
        self.used += 1
        if key != expected["key"]:
            raise EvidenceMismatch(f"expected decision {expected['key']}, got {key}")
        if not isinstance(expected["value"], bool):
            raise ValueError("decision values must be booleans")
        return expected["value"]

    def finish(self):
        if self.used != len(self.choices):
            raise EvidenceMismatch("unused scripted decisions")


class _NeedRoll(Exception):
    def __init__(self, request: RollRequest):
        self.request = request


class _PrefixDice:
    def __init__(self, prefix: tuple[tuple[RollRequest, int], ...]):
        self.prefix = prefix
        self.used = 0

    def roll(self, request: RollRequest) -> int:
        if self.used == len(self.prefix):
            raise _NeedRoll(request)
        expected, value = self.prefix[self.used]
        self.used += 1
        if expected != request:
            raise EvidenceMismatch("non-deterministic dice request during enumeration")
        return value


def enumerate_exact(run: Callable[[DiceSource], object], *, max_rolls: int = 6,
                    max_leaves: int = 100_000) -> dict[object, Fraction]:
    """Explore only requested dice; short-circuited branches retain their weight."""
    pending = [((), Fraction(1))]
    distribution: dict[object, Fraction] = {}
    leaves = 0
    while pending:
        prefix, weight = pending.pop()
        dice = _PrefixDice(prefix)
        try:
            outcome = run(dice)
        except _NeedRoll as need:
            if len(prefix) >= max_rolls:
                raise ValueError("enumeration roll bound exceeded; split the scenario")
            for value in range(1, need.request.sides + 1):
                pending.append(((*prefix, (need.request, value)), weight / need.request.sides))
        else:
            if dice.used != len(prefix):
                raise EvidenceMismatch("enumeration replay consumed an inconsistent prefix")
            leaves += 1
            if leaves > max_leaves:
                raise ValueError("enumeration leaf bound exceeded; split the scenario")
            distribution[outcome] = distribution.get(outcome, Fraction(0)) + weight
    if sum(distribution.values()) != 1:
        raise EvidenceMismatch("enumerated probabilities do not sum to one")
    return distribution
