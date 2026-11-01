"""Regressions of the compiled native backend (mordheim_combat._combat_native).

The backend is skipped with ``pytest.skip`` when the extension is not compiled
(environments without a C compiler): ``available_backends()`` then only reports
NumPy and the public behaviour is unchanged.

Fighters come from the shared precompiled corpus; this module never compiles
from the knowledge base.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest

from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
from mordheim_combat.native._combat_compile import compile_duel
from mordheim_combat.vectorized import available_backends
from mordheim_combat.vectorized import simulate_duel
from mordheim_core.models import DuelRequest
from tools.verification.compiled_cases import load_cases


_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def _cases():
    return load_cases(_CORPUS)


def _case(key: str):
    return _cases()[key]


def _request(case, simulations: int, *, seed: int = 7,
             batch_size: int = 500) -> DuelRequest:
    return DuelRequest(
        case.first, case.second, simulations, seed=seed, batch_size=batch_size,
    )


def _require_native() -> None:
    if "native" not in available_backends():
        pytest.skip("native combat backend is not compiled in this environment")


def test_native_compile_keeps_unarmed_fallback_for_later_pistol_rounds() -> None:
    """A main pistol becomes unarmed after opening round when no off-hand exists."""
    case = _case("scenario/pistol-vs-parry")
    first, second = case.first, case.second
    context = compile_duel(first, second)
    compiled = context["sources_first"]

    assert compiled["main"]["flags"]["hit_mod_base"] == 1
    assert compiled["unarmed"]["weapon"] == tuple(
        int(getattr(first.unarmed_weapon, name))
        for name in EFFECT_VALUE_FIELDS
    )

def test_native_compile_preserves_entangle_reaction_contract() -> None:
    """Entangle reaction is compiled as automatic fixed-strength attack."""
    case = _case("scenario/entangle-vs-fencer")
    first, second = case.first, case.second
    context = compile_duel(first, second)
    reaction = context["reactions_first"]["entangle"]

    assert context["first"]["entangle"] is True
    assert reaction["weapon"][5] == 3
    assert reaction["effect"][37] == 1


def test_native_is_selected_by_auto_when_available() -> None:
    _require_native()
    assert available_backends()[0] == "native"
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_is_selected_by_auto_when_available-0-0"
    )
    request = _request(case, 200)
    assert simulate_duel(request, backend="auto") == simulate_duel(
        request, backend="native",
    )


def test_native_accumulates_counts_across_batches() -> None:
    """Batch accumulation must neither lose nor duplicate duels."""
    _require_native()
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_accumulates_counts_across_batches-0-0"
    )
    request = _request(case, 2_500, batch_size=700)
    result = simulate_duel(request, backend="native")
    assert result.first_wins + result.second_wins + result.unresolved \
        == result.simulations


def test_native_symmetric_duel_is_statistically_fair() -> None:
    """Two identical profiles must each win ~50% (single large batch)."""
    _require_native()
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_symmetric_duel_is_statistically_fair-0-0"
    )
    request = _request(case, 20_000, batch_size=20_000, seed=2026)
    result = simulate_duel(request, backend="native")
    p = result.first_wins / result.simulations
    assert abs(p - 0.5) < 6 * (0.5 * 0.5 / result.simulations) ** 0.5 + 0.0025


def test_native_runs_are_deterministic_per_seed() -> None:
    """Replay-style reproducibility: same seed ⇒ identical result;
    different seed ⇒ different dice stream (the per-batch PCG32 is derived
    from the request seed)."""
    _require_native()
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_runs_are_deterministic_per_seed-0-0"
    )
    first = simulate_duel(_request(case, 8_000, seed=2024), backend="native")
    second = simulate_duel(_request(case, 8_000, seed=2024), backend="native")
    assert first == second
    other = simulate_duel(_request(case, 8_000, seed=2025), backend="native")
    assert (other.first_wins, other.second_wins, other.unresolved) != (
        first.first_wins, first.second_wins, first.unresolved,
    )
