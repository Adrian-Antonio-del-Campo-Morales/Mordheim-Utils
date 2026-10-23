from __future__ import annotations

import pytest

from mordheim_combat.vectorized import available_backends
from mordheim_combat.vectorized import simulate_duel
from mordheim_core.models import DuelRequest


def request(case):
    return DuelRequest(case.first, case.second, 20, seed=7)


@pytest.mark.phase5_vectorized
def test_auto_and_numpy_use_the_same_available_backend(vector_case):
    case = vector_case("test_backends/test_auto_and_numpy_use_the_same_available_backend-0-0")
    assert "numpy" in available_backends()
    if available_backends()[0] == "numpy":
        assert simulate_duel(request(case), backend="auto") == simulate_duel(
            request(case), backend="numpy",
        )


@pytest.mark.phase5_vectorized
def test_backend_selection_rejects_unknown_or_unavailable_backends(vector_case):
    case = vector_case("test_backends/test_backend_selection_rejects_unknown_or_unavailable_backends-0-0")
    with pytest.raises(ValueError, match="unknown combat backend"):
        simulate_duel(request(case), backend="gpu")
    if "native" not in available_backends():
        with pytest.raises(RuntimeError, match="not available|layout is stale"):
            simulate_duel(request(case), backend="native")
