from __future__ import annotations

import pytest

from mordheim_combat.vectorized import available_backends
from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild


def request():
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    return DuelRequest(fighter, fighter, 20, seed=7)


def test_auto_and_numpy_use_the_same_available_backend():
    assert "numpy" in available_backends()
    if available_backends()[0] == "numpy":
        assert simulate_duel(request(), backend="auto") == simulate_duel(
            request(), backend="numpy",
        )


def test_backend_selection_rejects_unknown_or_unavailable_backends():
    with pytest.raises(ValueError, match="unknown combat backend"):
        simulate_duel(request(), backend="gpu")
    if "native" not in available_backends():
        with pytest.raises(RuntimeError, match="not available|layout is stale"):
            simulate_duel(request(), backend="native")
