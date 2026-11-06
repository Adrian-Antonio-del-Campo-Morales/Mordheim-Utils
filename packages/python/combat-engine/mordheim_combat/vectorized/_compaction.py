"""Drop decided duels from a batch so later rounds only carry live rows.

A batch keeps one row per duel for its whole life, but most duels end long
before the round horizon: outside a stalemate only a fifth of the row-rounds
of a 100k sample belong to a live duel, and every array operation still pays
for the rest.  ``RowCompactor`` re-indexes the batch to its live rows at a
round boundary and remembers where each of them came from, so the counts and
the per-row observations are still reported at the original width.

The re-indexing is generic: it walks the carried containers by dataclass
reflection instead of naming their fields, so a per-row column added to
``CombatState`` or to a resource ledger is carried without a change here.
Anything it cannot recognise as per-row data raises rather than being left
behind at the old width.

Compaction never changes a result.  Every draw inside the round loop is
sized by the rows it applies to, and a decided row takes part in none of
them, so the live duels see the same random stream whether or not the decided
rows are still present.  ``tests/engines/vectorized/runtime/test_compaction.py``
pins that: the same samples run with compaction disabled, at the production
threshold and at every round must agree exactly.
"""
from __future__ import annotations

import dataclasses

import numpy as np

#: Compact once the live rows fall below this fraction of the current width.
#: Gathering costs one copy of every column, so compacting at a mild loss
#: would spend more than the narrower rounds save.
COMPACTION_FRACTION = 0.5

#: Never compact a batch narrower than this.  The gather is a fixed cost per
#: column; below a few thousand rows the rounds it saves are already cheap.
COMPACTION_MIN_WIDTH = 4096

#: ``CombatState`` columns laid out as (characteristic, row) rather than
#: (row, ...), so they are re-indexed along their second axis.
ROW_AXIS_1 = frozenset({"random_modifiers"})


class RowCompactor:
    """Maps the rows of a compacted batch back to the rows of the sample.

    ``index`` is ``None`` while the batch still has all of its rows; after the
    first compaction ``index[i]`` is the original row of compact row ``i``.
    Outcome buffers hold the last known value of the rows already dropped.
    """

    __slots__ = ("enabled", "full_count", "width", "index", "events", "_buffers")

    def __init__(self, count: int, *, enabled: bool = True) -> None:
        self.enabled = enabled
        self.full_count = count
        self.width = count
        self.index: np.ndarray | None = None
        self.events = 0
        self._buffers: dict[str, np.ndarray] = {}

    def should_compact(self, live: np.ndarray) -> bool:
        """Whether dropping the decided rows is worth a gather right now."""
        if not self.enabled or self.width < COMPACTION_MIN_WIDTH:
            return False
        return int(np.count_nonzero(live)) < COMPACTION_FRACTION * self.width

    def record(self, name: str, values: np.ndarray) -> None:
        """Store the current rows' values of one outcome at sample width."""
        buffer = self._buffers.get(name)
        if buffer is None:
            buffer = self._buffers[name] = np.empty(
                (self.full_count,) + values.shape[1:], dtype=values.dtype)
        if self.index is None:
            buffer[...] = values
        else:
            buffer[self.index] = values

    def full(self, name: str, values: np.ndarray) -> np.ndarray:
        """One outcome at sample width: the current rows over the dropped ones."""
        if self.index is None:
            return values
        self.record(name, values)
        return self._buffers[name]

    def compact(self, keep: np.ndarray, containers: list) -> list:
        """Re-index every per-row column of ``containers`` to ``keep``.

        ``keep`` is a boolean mask over the current rows.  Dataclasses and
        lists are updated in place; arrays and tuples are rebuilt and returned
        in the order given, because the caller holds those by value.  An array
        reached through several containers is re-indexed once and stays shared.
        """
        rows = np.flatnonzero(keep)
        memo: dict[int, np.ndarray] = {}
        result = [self._value(value, rows, memo, None) for value in containers]
        self.index = rows if self.index is None else self.index[rows]
        self.width = int(rows.size)
        self.events += 1
        return result

    def _value(self, value, rows, memo, field):
        if value is None:
            return None
        if isinstance(value, np.ndarray):
            cached = memo.get(id(value))
            if cached is not None:
                return cached
            if field in ROW_AXIS_1:
                if value.ndim != 2 or value.shape[1] != self.width:
                    raise ValueError(
                        f"{field}: expected (n, {self.width}), got {value.shape}")
                out = value[:, rows]
            elif value.ndim >= 1 and value.shape[0] == self.width:
                out = value[rows]
            else:
                raise ValueError(
                    f"{field}: not a per-row column of width {self.width}: "
                    f"{value.shape}")
            memo[id(value)] = out
            return out
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            for item in dataclasses.fields(value):
                current = getattr(value, item.name)
                if _is_row_data(current):
                    setattr(value, item.name,
                            self._value(current, rows, memo, item.name))
            return value
        if isinstance(value, list):
            value[:] = [self._value(item, rows, memo, field)
                        if _is_row_data(item) else item for item in value]
            return value
        if isinstance(value, tuple):
            return tuple(self._value(item, rows, memo, field)
                         if _is_row_data(item) else item for item in value)
        raise TypeError(f"{field}: cannot re-index {type(value).__name__}")


def _is_row_data(value) -> bool:
    """Whether a container field can hold per-row columns."""
    if isinstance(value, np.ndarray):
        return True
    if isinstance(value, (list, tuple)):
        return any(_is_row_data(item) for item in value)
    return dataclasses.is_dataclass(value) and not isinstance(value, type)
