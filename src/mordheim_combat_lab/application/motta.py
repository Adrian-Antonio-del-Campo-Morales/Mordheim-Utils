"""application.motta: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from math import hypot


MOTTA_CONSTANT = 507.4


MOTTA_COST_FLOOR = 0.01


def motta_score(improvement: float, cost: float | None) -> float | None:
    """Return the legacy MOTTA score, or ``None`` when a cost is unavailable."""
    if cost is None:
        return None
    return improvement / hypot(cost, MOTTA_COST_FLOOR) * MOTTA_CONSTANT
