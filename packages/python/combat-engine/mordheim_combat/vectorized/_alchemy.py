"""Vectorized engine: alchemist recovery at the start of the bearer's turn.

``CombatState`` carries the Backley penalties as a per-row tuple; the two facts
it does not carry (the once-per-battle Backley attempt and the cured addiction)
live in ``AlchemyResources``, owned by the round driver, so no shared column is
added to a schema owned by G02.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mordheim_combat.vectorized._operators import _characteristic_test
from mordheim_combat.vectorized._types import CombatState, OUT, STANDING, has

BACKLEY = "condition.alchemist-backleys-brew"
ADDICTED = "condition.alchemist-addicted"
VIGORTIA = "condition.alchemist-aberrantius-vigortia"

#: ``CombatState.random_modifiers`` row order (see ``_state.STATS``).
_MODIFIER_ROWS = {"WS": 0, "S": 1, "T": 2, "I": 3, "A": 4}


@dataclass(slots=True)
class AlchemyResources:
    """Per-row alchemy facts ``CombatState`` does not carry."""

    backley_used: np.ndarray
    addiction_cured: np.ndarray


def alchemy_resources(count: int) -> AlchemyResources:
    return AlchemyResources(
        backley_used=np.zeros(count, dtype=bool),
        addiction_cured=np.zeros(count, dtype=bool),
    )


def _adjust(state: CombatState, row: int, values: dict[str, int]) -> None:
    """Apply characteristic deltas to one row and its variable modifiers."""
    for stat, delta in values.items():
        if not delta:
            continue
        if stat == "S":
            state.strength[row] += delta
        elif stat == "T":
            state.toughness[row] += delta
        elif stat == "I":
            state.initiative[row] += delta
        state.random_modifiers[_MODIFIER_ROWS[stat], row] += delta


def resolve_alchemist(
    fighter, state: CombatState, rows: np.ndarray, rng: np.random.Generator,
    resources: AlchemyResources, decisions=None, key: str = "alchemist",
) -> None:
    """Port of ``modular.alchemy.resolve_alchemist`` for a set of rows.

    Called once at the start of this fighter's own turn, never the opponent's.
    """
    if rows.size == 0:
        return
    alive = rows[state.condition[rows] != OUT]
    if alive.size == 0:
        return

    backley = alive[
        ~resources.backley_used[alive]
        & has(fighter.global_effects, BACKLEY)
    ]
    if backley.size:
        passed = _characteristic_test(
            fighter, state.toughness[backley], rng, state=state, rows=backley,
            key=f"{key}.alchemist-backley", decisions=decisions)
        for row in backley[passed]:
            penalties = dict(state.backley_penalties[int(row)])
            _adjust(state, int(row), {stat: penalty for stat, penalty in penalties.items()})
            state.backley_penalties[int(row)] = ()
            resources.backley_used[int(row)] = True

    addicted = alive[
        ~resources.addiction_cured[alive]
        & has(fighter.global_effects, ADDICTED)
        & (state.condition[alive] == STANDING)
    ]
    if addicted.size == 0:
        return
    from mordheim_combat.vectorized._owned import owned_roll

    cured = addicted[owned_roll(fighter, state, addicted, rng, f"{key}.alchemist-brew",
                                decisions=decisions).values == 6]
    for row in cured:
        resources.addiction_cured[int(row)] = True
        if not has(fighter.global_effects, VIGORTIA):
            _adjust(state, int(row), {"S": 1, "T": 1})
