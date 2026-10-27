"""Observation contracts exposed by the compiled native engine.

The batch observation is the per-row terminal state used by the replay driver
and diagnostics; it is not part of the production ``DuelResult`` counting path.
"""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VectorBatchObservation:
    """Per-row terminal state exposed only to verification and diagnostics."""

    winner: np.ndarray
    rounds: np.ndarray
    first_wounds: np.ndarray
    second_wounds: np.ndarray
    first_condition: np.ndarray
    second_condition: np.ndarray
    first_resources: tuple[tuple[str, np.ndarray], ...]
    second_resources: tuple[tuple[str, np.ndarray], ...]
