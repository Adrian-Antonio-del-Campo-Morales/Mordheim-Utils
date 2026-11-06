"""Dropping decided duels must not change a result, and must carry every column."""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from mordheim_combat.vectorized import _compaction
from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_combat.vectorized import simulate_duel
from mordheim_combat.vectorized._alchemy import alchemy_resources
from mordheim_combat.vectorized._compaction import RowCompactor
from mordheim_combat.vectorized._driver import _round_ledger
from mordheim_combat.vectorized._leadership import leadership_resources
from mordheim_combat.vectorized._psychology import psychology_resources
from mordheim_combat.vectorized._state import initialize_fighter
from mordheim_core.models import DuelRequest
from tests.engines.fixtures.precompiled_catalog import scenario_key

#: (fraction, minimum width) of the three settings every result must share.
SETTINGS = {
    "disabled": (0.0, 4096),
    "production": (0.5, 4096),
    "every round": (1.0, 1),
}


@pytest.fixture
def compaction(monkeypatch):
    """Apply one compaction setting and count the compactions it performs."""
    performed = []
    original = RowCompactor.compact

    def counting(self, keep, containers):
        performed.append(int(self.width))
        return original(self, keep, containers)

    monkeypatch.setattr(RowCompactor, "compact", counting)

    def apply(fraction: float, minimum_width: int):
        monkeypatch.setattr(_compaction, "COMPACTION_FRACTION", fraction)
        monkeypatch.setattr(_compaction, "COMPACTION_MIN_WIDTH", minimum_width)
        performed.clear()
        return performed

    return apply


def _observation(sample) -> tuple:
    return tuple(
        np.asarray(getattr(sample, name)).tobytes()
        for name in ("winner", "rounds", "first_wounds", "second_wounds",
                     "first_condition", "second_condition")
    )


def test_compaction_changes_no_count_and_no_observation(cases, compaction):
    """Every draw is sized by the rows it applies to, so dropping the decided
    ones leaves the live duels on exactly the same stream."""
    case = cases[scenario_key("basic")]
    results = {}
    for label, (fraction, minimum_width) in SETTINGS.items():
        performed = compaction(fraction, minimum_width)
        counted = simulate_duel(
            DuelRequest(case.first, case.second, 6000, seed=2026,
                        batch_size=6000, maximum_rounds=50),
            backend="numpy")
        observed = simulate_batch_observed(
            case.first, case.second, 6000, np.random.default_rng(5), 50)
        results[label] = (counted, _observation(observed), bool(performed))
    assert results["disabled"][2] is False  # the comparison would be vacuous
    assert results["production"][2] is True
    assert results["every round"][2] is True
    assert results["production"][:2] == results["disabled"][:2]
    assert results["every round"][:2] == results["disabled"][:2]


def test_compaction_carries_every_per_row_column(cases):
    """A per-row column added to any carried container must be re-indexed too:
    the walk is generic, and anything it cannot place raises instead."""
    case = cases[scenario_key("basic")]
    width = 8
    state = initialize_fighter(case.first, width, np.random.default_rng(0),
                               lazy_inconsistency=True)
    containers = [state, leadership_resources(width), psychology_resources(width),
                  alchemy_resources(width), _round_ledger(width)]
    keep = np.zeros(width, dtype=bool)
    keep[[1, 2, 5]] = True

    compactor = RowCompactor(width)
    compactor.compact(keep, containers)

    assert compactor.width == 3
    assert compactor.index.tolist() == [1, 2, 5]
    for container in containers:
        for field in dataclasses.fields(container):
            value = getattr(container, field.name)
            for column in (value if isinstance(value, (list, tuple)) else [value]):
                if not isinstance(column, np.ndarray):
                    continue
                axis = 1 if field.name in _compaction.ROW_AXIS_1 else 0
                assert column.shape[axis] == 3, f"{field.name} kept the old width"


def test_a_second_compaction_composes_the_row_map(cases):
    """The map addresses sample rows, not the rows of the previous pass."""
    case = cases[scenario_key("basic")]
    state = initialize_fighter(case.first, 6, np.random.default_rng(0),
                               lazy_inconsistency=True)
    compactor = RowCompactor(6)
    compactor.compact(np.array([False, True, True, True, False, True]), [state])
    assert compactor.index.tolist() == [1, 2, 3, 5]
    compactor.compact(np.array([False, True, False, True]), [state])
    assert compactor.index.tolist() == [2, 5]
    assert compactor.width == 2


def test_an_unknown_container_is_refused_instead_of_being_left_behind():
    compactor = RowCompactor(4)
    with pytest.raises(ValueError):
        compactor.compact(np.array([True, False, True, False]),
                          [np.zeros(7, dtype=bool)])
