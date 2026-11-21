"""Per-row equipment projection: one shared fighter plus sparse row overrides.

The driver used to hold every row's projected ``CompiledFighter`` in a
``dict[row, CompiledFighter]`` rebuilt for the whole batch every round, then
walked it row by row in Python to group rows and clamp Wounds.  Nearly every
row shares one object, so ``RowEquipment`` stores that object once and keeps
only the rows whose projection differs.  Reads and writes keep the old
``equipment[row]`` interface, so the per-row patches are unchanged.

Grouping keeps the old semantics exactly: rows are partitioned by the
*identity* of their (attacker, defender) objects, groups come out in the order
of their first row, and each group lists its rows in input order.  The pools
draw their dice group by group, so this order is what keeps the random streams
-- and therefore every result -- identical.
"""
from __future__ import annotations

import numpy as np

# The Wound ceiling is the validated modular contract, never a second formula:
# ``vectorized/_state.py`` seeds ``CombatState.wounds`` from this very function,
# so the per-round clamp has to spend the same one.
from mordheim_combat.modular.state import maximum_wounds
from mordheim_core.models import CompiledFighter


class RowEquipment:
    """Row -> projected fighter map stored as ``uniform`` plus ``overrides``."""

    __slots__ = ("uniform", "overrides")

    def __init__(self, uniform: CompiledFighter,
                 overrides: dict[int, CompiledFighter] | None = None) -> None:
        self.uniform = uniform
        self.overrides: dict[int, CompiledFighter] = {}
        if overrides:
            for row, value in overrides.items():
                if value is not uniform:
                    self.overrides[int(row)] = value

    def __getitem__(self, row) -> CompiledFighter:
        return self.overrides.get(int(row), self.uniform)

    def __setitem__(self, row, value: CompiledFighter) -> None:
        row = int(row)
        if value is self.uniform:
            self.overrides.pop(row, None)
        else:
            self.overrides[row] = value

    def codes(self, rows: np.ndarray) -> tuple[np.ndarray, list[CompiledFighter]]:
        """Identity code of each row's object (0 = ``uniform``) and the objects."""
        objects = [self.uniform]
        if not self.overrides:
            return np.zeros(rows.size, dtype=np.int64), objects
        index = {id(self.uniform): 0}
        keys = np.fromiter(self.overrides.keys(), dtype=np.int64, count=len(self.overrides))
        values = np.empty(keys.size, dtype=np.int64)
        for position, value in enumerate(self.overrides.values()):
            code = index.get(id(value))
            if code is None:
                code = index[id(value)] = len(objects)
                objects.append(value)
            values[position] = code
        order = np.argsort(keys)
        keys, values = keys[order], values[order]
        position = np.minimum(np.searchsorted(keys, rows), keys.size - 1)
        return np.where(keys[position] == rows, values[position], 0), objects


def equipment_groups(rows: np.ndarray, attacker: RowEquipment, defender: RowEquipment):
    """Split rows by the identity of the equipment pair their simulation projects."""
    if rows.size == 0:
        return []
    if not attacker.overrides and not defender.overrides:
        return [(attacker.uniform, defender.uniform, np.array(rows, dtype=np.int64))]
    rows = np.asarray(rows, dtype=np.int64)
    attacker_codes, attackers = attacker.codes(rows)
    defender_codes, defenders = defender.codes(rows)
    keys = attacker_codes * len(defenders) + defender_codes
    _, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
    order = np.argsort(inverse, kind="stable")
    bounds = np.cumsum(np.bincount(inverse, minlength=first.size))[:-1]
    members = np.split(rows[order], bounds)
    return [
        (attackers[attacker_codes[first[group]]], defenders[defender_codes[first[group]]],
         members[group])
        for group in np.argsort(first, kind="stable")
    ]


def clamp_maximum_wounds(wounds: np.ndarray, equipment: RowEquipment,
                         rows: np.ndarray) -> None:
    """Lower each row's Wounds to the maximum its own projection allows."""
    if rows.size == 0:
        return
    rows = np.asarray(rows, dtype=np.int64)
    codes, objects = equipment.codes(rows)
    limits = np.array([maximum_wounds(value) for value in objects], dtype=np.int64)
    limit = limits[codes]
    over = wounds[rows] > limit
    if over.any():
        wounds[rows[over]] = limit[over]
