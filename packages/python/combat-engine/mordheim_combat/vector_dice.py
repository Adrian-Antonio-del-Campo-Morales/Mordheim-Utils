"""Order-independent verification dice and the fast production adapter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True, slots=True)
class VectorRollRequest:
    """One semantic roll requested for explicit simulation row identifiers."""

    key: str
    rows: np.ndarray
    sides: int = 6

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("a vector roll request needs a semantic key")
        if self.sides < 2:
            raise ValueError("a die must have at least two sides")
        if self.rows.ndim != 1:
            raise ValueError("vector roll rows must be one-dimensional")


class VectorDiceSource(Protocol):
    def roll(self, request: VectorRollRequest) -> np.ndarray: ...

    def random(self, key: str, rows: np.ndarray) -> np.ndarray: ...


class FastVectorDice:
    """Bulk NumPy generator used by the production executor."""

    def __init__(self, seed: int = 0) -> None:
        self._rng = np.random.default_rng(seed)

    def roll(self, request: VectorRollRequest) -> np.ndarray:
        return self._rng.integers(1, request.sides + 1, request.rows.size)

    def random(self, key: str, rows: np.ndarray) -> np.ndarray:
        del key
        return self._rng.random(rows.size)


class KeyedVectorDice:
    """Stable verification dice keyed by seed, semantic event and row id."""

    def __init__(self, seed: int = 0) -> None:
        self.seed = int(seed)

    def _rng(self, key: str, row: int, sides: int = 0) -> np.random.Generator:
        # Match ``KeyedDice(seed + row)`` exactly so a scalar replay and one
        # vector row observe the same semantic die without sharing execution.
        entropy = [self.seed + int(row), int(sides), *key.encode("utf-8")]
        return np.random.default_rng(np.random.SeedSequence(entropy))

    def roll(self, request: VectorRollRequest) -> np.ndarray:
        return np.fromiter(
            (
                self._rng(request.key, int(row), request.sides).integers(
                    1, request.sides + 1
                )
                for row in request.rows
            ),
            dtype=np.int64,
            count=request.rows.size,
        )

    def random(self, key: str, rows: np.ndarray) -> np.ndarray:
        return np.fromiter(
            (self._rng(key, int(row)).random() for row in rows),
            dtype=np.float64,
            count=rows.size,
        )
