"""Strict scripted dice and decisions for the precompiled modular tests."""
from __future__ import annotations

from mordheim_core.dice import RollRequest


class EvidenceMismatch(AssertionError):
    """An executed observation differs from its scripted expectation."""


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
