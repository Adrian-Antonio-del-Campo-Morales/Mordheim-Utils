from __future__ import annotations

import numpy as np

from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


def fighter():
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))


def test_observed_batch_preserves_per_row_terminal_state():
    result = simulate_batch_observed(
        fighter(), fighter(), 64, np.random.default_rng(9), maximum_rounds=10,
    )

    assert result.winner.shape == result.rounds.shape == (64,)
    assert result.first_wounds.shape == result.second_wounds.shape == (64,)
    assert result.first_condition.shape == result.second_condition.shape == (64,)
    assert set(np.unique(result.winner)) <= {-1, 0, 1}
    assert np.all((result.rounds >= 1) & (result.rounds <= 10))
    assert {name for name, _values in result.first_resources} == {
        "lucky-charm", "force-of-will", "mark-of-the-old-ones", "luck",
    }
