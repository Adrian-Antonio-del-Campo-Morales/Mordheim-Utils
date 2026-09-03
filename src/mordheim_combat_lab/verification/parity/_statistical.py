"""Aggregate statistical parity between the modular oracle and each
optimized backend using the six-sigma gate."""
from __future__ import annotations

import math
from mordheim_combat import vectorized
from mordheim_core.models import DuelRequest
from mordheim_combat_lab.verification.parity._report import StatisticalParityResult

def _parity_result(scenario: str, backend: str, simulations: int, modular, vector) -> StatisticalParityResult:
    modular_rates = tuple(value / simulations for value in (
        modular.first_wins, modular.second_wins, modular.unresolved,
    ))
    vector_rates = tuple(value / simulations for value in (
        vector.first_wins, vector.second_wins, vector.unresolved,
    ))
    tolerances = tuple(max(
        .0025,
        6 * math.sqrt(
            left * (1 - left) / simulations + right * (1 - right) / simulations
        ),
    ) for left, right in zip(modular_rates, vector_rates))
    passed = all(
        abs(left - right) <= tolerance
        for left, right, tolerance in zip(modular_rates, vector_rates, tolerances)
    )
    return StatisticalParityResult(
        scenario=scenario, backend=backend, simulations=simulations,
        modular_rates=modular_rates, vectorized_rates=vector_rates,
        tolerances=tolerances, passed=passed,
    )

def compare_statistical_parity(
    scenario: str, first, second, simulations: int, *, seed: int = 2026,
    maximum_rounds: int = 50, backend: str = "numpy", modular=None,
) -> StatisticalParityResult:
    """Compare independent aggregate samples using the documented six-sigma gate.

    The modular engine is the only correctness oracle; ``backend`` selects the
    optimized candidate to certify against it ("numpy" or "native").  Pass a
    precomputed ``modular`` result to certify several candidates against the
    same oracle sample without re-running the modular engine.
    """
    from mordheim_combat.modular.duel import simulate_duel_reference

    if simulations < 1:
        raise ValueError("statistical parity needs at least one simulation")
    if backend not in {"numpy", "native"}:
        raise ValueError(f"unknown optimized backend: {backend}")
    if modular is None:
        modular = simulate_duel_reference(
            first, second, simulations, seed=seed, maximum_rounds=maximum_rounds,
        )
    vector = vectorized.simulate_duel(
        DuelRequest(
            first, second, simulations, seed=seed + 1_000_003,
            maximum_rounds=maximum_rounds,
        ),
        backend=backend,
    )
    return _parity_result(scenario, backend, simulations, modular, vector)
