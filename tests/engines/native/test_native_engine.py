"""Regressions of the compiled native backend (mordheim_combat.native).

The behavioural cases fail with an actionable message when the extension is
missing or built for stale layouts; only the explicit unavailability contract
in ``runtime/test_duel_context.py`` simulates that condition deliberately.

Fighters come from the shared precompiled corpus; this module never compiles
from the knowledge base.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest

from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
from mordheim_combat.native import available_backends
from mordheim_combat.native import simulate_duel
from mordheim_combat.native._combat_compile import compile_duel
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
        pytest.fail(
            "native combat extension is not available or was built for stale "
            "layouts; install it with `python -m pip install -e \".[dev]\"` "
            "(a working C compiler is required) and reinstall after an update"
        )


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


def test_native_is_the_only_available_backend() -> None:
    """The native entry point has no auto-selection: it either runs or fails."""
    _require_native()
    assert available_backends() == ("native",)
    # Historical frozen key from the removed backend-selection test.
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_is_selected_by_auto_when_available-0-0"
    )
    request = _request(case, 200)
    assert simulate_duel(request) == simulate_duel(request)


def test_native_accumulates_counts_across_batches() -> None:
    """Batch accumulation must neither lose nor duplicate duels."""
    _require_native()
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_accumulates_counts_across_batches-0-0"
    )
    request = _request(case, 2_500, batch_size=700)
    result = simulate_duel(request)
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
    result = simulate_duel(request)
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
    first = simulate_duel(_request(case, 8_000, seed=2024))
    second = simulate_duel(_request(case, 8_000, seed=2024))
    assert first == second
    other = simulate_duel(_request(case, 8_000, seed=2025))
    assert (other.first_wins, other.second_wins, other.unresolved) != (
        first.first_wins, first.second_wins, first.unresolved,
    )


def test_native_statistical_parity_against_modular_oracle() -> None:
    """The statistical gate (modular oracle) certifies the native backend."""
    _require_native()
    case = _case(
        "unit/native/test_native_engine/"
        "test_native_statistical_parity_against_modular_oracle-0-0"
    )
    from tools.verification.parity_statistical import compare_statistical_parity

    result = compare_statistical_parity(
        "native-smoke", case.first, case.first, 2_000, seed=3, backend="native",
    )
    assert result.passed
