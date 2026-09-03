"""Regresiones del backend nativo compilado (mordheim_combat._combat_native).

El backend se omite con ``pytest.skip`` cuando la extensión no está compilada
(entornos sin compilador C): ``available_backends()`` entonces solo reporta
NumPy y el comportamiento público no cambia.
"""
from __future__ import annotations

import pytest

from mordheim_combat.vectorized import available_backends
from mordheim_combat.vectorized import simulate_duel
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild


def _request(simulations: int, *, seed: int = 7, batch_size: int = 500) -> DuelRequest:
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    return DuelRequest(fighter, fighter, simulations, seed=seed, batch_size=batch_size)


def _require_native() -> None:
    if "native" not in available_backends():
        pytest.skip("native combat backend is not compiled in this environment")


def test_native_is_selected_by_auto_when_available() -> None:
    _require_native()
    assert available_backends()[0] == "native"
    request = _request(200)
    assert simulate_duel(request, backend="auto") == simulate_duel(
        request, backend="native",
    )


def test_native_accumulates_counts_across_batches() -> None:
    """La acumulación por lotes no debe perder ni duplicar duelos."""
    _require_native()
    request = _request(2_500, batch_size=700)
    result = simulate_duel(request, backend="native")
    assert result.first_wins + result.second_wins + result.unresolved \
        == result.simulations


def test_native_symmetric_duel_is_statistically_fair() -> None:
    """Dos perfiles idénticos deben ganar ~50% cada uno (lote único y grande)."""
    _require_native()
    request = _request(20_000, batch_size=20_000, seed=2026)
    result = simulate_duel(request, backend="native")
    p = result.first_wins / result.simulations
    assert abs(p - 0.5) < 6 * (0.5 * 0.5 / result.simulations) ** 0.5 + 0.0025


def test_native_runs_are_deterministic_per_seed() -> None:
    """Reproducibilidad tipo replay: misma semilla ⇒ idéntico resultado;
    distinta semilla ⇒ corriente de dados distinta (el PCG32 por lote se
    deriva de la semilla de la petición)."""
    _require_native()
    first = simulate_duel(_request(8_000, seed=2024), backend="native")
    second = simulate_duel(_request(8_000, seed=2024), backend="native")
    assert first == second
    other = simulate_duel(_request(8_000, seed=2025), backend="native")
    assert (other.first_wins, other.second_wins, other.unresolved) != (
        first.first_wins, first.second_wins, first.unresolved,
    )


def test_native_statistical_parity_against_modular_oracle() -> None:
    """La puerta estadística (oráculo modular) certifica el backend nativo."""
    _require_native()
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    result = compare_statistical_parity(
        "native-smoke", fighter, fighter, 2_000, seed=3, backend="native",
    )
    assert result.passed
