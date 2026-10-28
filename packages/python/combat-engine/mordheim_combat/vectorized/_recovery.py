"""Vectorized engine: recovery that owns no attack step.

Only the behaviours the round driver calls between the equipment projection and
the attack phase live here; fire, Force of Will and Black Hunger already have
their ports in ``_driver``.
"""
from __future__ import annotations

import numpy as np

from mordheim_combat.vectorized._types import CombatState, OUT, has


def revenant_recovery(
    fighter, state: CombatState, rows: np.ndarray, rng: np.random.Generator,
    decisions=None, key: str = "revenant",
) -> None:
    """Q013: one 5+ attempt at the start of the bearer's own turn.

    The attempt belongs to the active player's turn, so it is keyed by the
    round and never shared with the opponent.  A failed attempt is not
    remembered: the next own turn rolls again, exactly like the scalar
    ``resources_spent`` key that carries the round index.
    """
    if rows.size == 0 or not has(fighter.global_effects, "mechanic.curse-of-the-revenant"):
        return
    maximum = fighter.characteristics.wounds + int(
        has(fighter.global_effects, "skill.monstrous")
    )
    eligible = rows[(state.condition[rows] != OUT) & (state.wounds[rows] < maximum)]
    if eligible.size == 0:
        return
    from mordheim_combat.vectorized._owned import owned_roll

    healed = eligible[owned_roll(fighter, state, eligible, rng, key,
                                 decisions=decisions).values >= 5]
    if healed.size:
        state.wounds[healed] = np.minimum(maximum, state.wounds[healed] + 1)
