"""Vectorized engine: owned rolls and the personal once-per-battle choices.

Batch port of ``modular.contexts.OwnedRollDice.roll``.  The scalar wrapper is
constructed at every roll site the roller *owns* (its hits, saves, injuries,
recovery, initialisation …) and offers, in this order, Ranald's Luck (adjust
one roll by one, once per battle), Oracle / Augur (re-roll one roll, once per
battle), the Luck skill (re-roll one roll, once per battle) and the Scryer's
close-combat re-roll (no resource).  Each choice is taken once for the row set,
as every other batch decision in this engine is.

The ledger is ``CombatState`` itself (``ranalds_luck_used``,
``one_roll_reroll_used``, ``luck_used``), so every roll site of a fighter
spends the same per-row resource.  Every roll site the oracle owns goes
through :func:`owned_roll` (or :class:`OwnedRowDice` for scalar helpers), and
the batch driver runs with the oracle's ``AlwaysAccept`` default policy, so
the three resource tags are admitted (plan decisions D9 / D12).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from mordheim_core.dice import DecisionPolicy
from mordheim_core.models import CompiledFighter

from mordheim_combat.vectorized._types import CombatState, has

#: Tags that make a roll site's result depend on the personal ledger.
OWNED_ROLL_TAGS = (
    "mechanic.ranalds-luck", "mechanic.oracle", "mechanic.augur-one-roll-reroll",
    "skill.luck", "mechanic.scryer",
)


@dataclass(frozen=True, slots=True)
class OwnedRoll:
    """One owned roll per row and the rows whose die was re-rolled."""

    values: np.ndarray
    rerolled: np.ndarray


def has_personal_choices(fighter: CompiledFighter) -> bool:
    """Whether ``owned_roll`` can ever alter this fighter's die."""
    return any(has(fighter.global_effects, tag) for tag in OWNED_ROLL_TAGS)


def owned_roll(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator, key: str, *,
    decisions: DecisionPolicy | None, sides: int = 6,
    modifiable: bool = True, close_combat: bool = False,
    die: np.ndarray | None = None,
) -> OwnedRoll:
    """Draw (or take) one owned die per row and apply the personal choices.

    ``decisions`` ``None`` mirrors the scalar wrapper built without a policy:
    the die is returned untouched.  Inside a round the scalar pipeline always
    has a policy (``decisions or AlwaysAccept()``), so round callers pass one.
    ``modifiable=False`` is the scalar ``unmodifiable`` entry: Ranald's Luck
    and the Scryer do not touch the die, the once-per-battle re-rolls still
    may.  ``die`` lets a caller that already drew the die (the Leadership
    dice) reuse it.
    """
    rows = np.asarray(rows, dtype=np.intp)
    values = (rng.integers(1, sides + 1, rows.size).astype(np.int16)
              if die is None else np.asarray(die, dtype=np.int16).copy())
    rerolled = np.zeros(rows.size, dtype=bool)
    if decisions is None or rows.size == 0:
        return OwnedRoll(values, rerolled)
    effects = fighter.global_effects
    reroll_key = ".reroll" not in key
    if modifiable and has(effects, "mechanic.ranalds-luck"):
        available = ~state.ranalds_luck_used[rows]
        if available.any():
            if decisions.choose(f"{key}.ranalds-luck.plus", fighter):
                values = np.where(available, values + 1, values).astype(np.int16)
                state.ranalds_luck_used[rows[available]] = True
            elif decisions.choose(f"{key}.ranalds-luck.minus", fighter):
                values = np.where(available, values - 1, values).astype(np.int16)
                state.ranalds_luck_used[rows[available]] = True
    if reroll_key and any(has(effects, tag) for tag in
                          ("mechanic.oracle", "mechanic.augur-one-roll-reroll")):
        available = ~state.one_roll_reroll_used[rows]
        if available.any() and decisions.choose(f"{key}.one-roll-reroll", fighter):
            fresh = rng.integers(1, sides + 1, rows.size).astype(np.int16)
            values = np.where(available, fresh, values)
            state.one_roll_reroll_used[rows[available]] = True
            rerolled |= available
    if reroll_key and has(effects, "skill.luck"):
        available = ~state.luck_used[rows] & ~rerolled
        if available.any() and decisions.choose(f"{key}.luck", fighter):
            fresh = rng.integers(1, sides + 1, rows.size).astype(np.int16)
            values = np.where(available, fresh, values)
            state.luck_used[rows[available]] = True
            rerolled |= available
    if reroll_key and close_combat and modifiable and has(effects, "mechanic.scryer"):
        available = ~rerolled
        if available.any() and decisions.choose(f"{key}.scryer", fighter):
            fresh = rng.integers(1, sides + 1, rows.size).astype(np.int16)
            values = np.where(available, fresh, values)
            rerolled |= available
    return OwnedRoll(values, rerolled)


class OwnedRowDice:
    """One row's owned dice through the modular ``DiceSource`` protocol.

    Scalar helpers the engine reuses (``mutations.apply_brand``) roll through
    a ``DiceSource``; this adapter makes those rolls the owner's owned rolls,
    exactly as the oracle hands ``apply_brand`` the Inquisitor's
    ``OwnedRollDice``.
    """

    def __init__(self, fighter: CompiledFighter, state: CombatState, row: int,
                 rng: np.random.Generator, decisions: DecisionPolicy | None,
                 *, close_combat: bool = False) -> None:
        self.fighter, self.state, self.row = fighter, state, int(row)
        self.rng, self.decisions, self.close_combat = rng, decisions, close_combat

    def roll(self, request) -> int:
        return int(owned_roll(
            self.fighter, self.state, np.array([self.row]), self.rng, request.key,
            decisions=self.decisions, sides=request.sides,
            close_combat=self.close_combat).values[0])
