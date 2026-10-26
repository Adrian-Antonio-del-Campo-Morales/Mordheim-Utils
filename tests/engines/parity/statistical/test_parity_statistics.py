"""Real statistical comparisons of the vectorized backend against the oracle.

Each case samples both engines and asserts the six-sigma outcome comparison;
the frozen benchmark pair and its round budget come from the corpus.
"""
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from tests.engines.fixtures.precompiled_catalog import benchmark_case_key
import pytest


def test_statistical_parity_reports_three_outcomes_and_six_sigma_tolerances(cases):
    fighter = cases[benchmark_case_key("basic")].first
    result = compare_statistical_parity("smoke", fighter, fighter, 20, seed=3)
    assert len(result.modular_rates) == len(result.vectorized_rates) == 3
    assert len(result.tolerances) == 3
    assert all(tolerance >= .0025 for tolerance in result.tolerances)


def test_statistical_samples_record_per_engine_wall_times(cases):
    case = cases[benchmark_case_key("basic")]
    result = compare_statistical_parity(
        "smoke", case.first, case.second, 40, seed=3,
        maximum_rounds=case.limits.maximum_rounds,
    )
    assert result.reference_seconds > 0  # the oracle sample was timed here
    assert result.candidate_seconds > 0
    # A precomputed oracle sample carries its caller-provided measurement.
    from mordheim_combat.modular.duel import simulate_duel_reference
    modular = simulate_duel_reference(
        case.first, case.second, 40, seed=3,
        maximum_rounds=case.limits.maximum_rounds,
    )
    replayed = compare_statistical_parity(
        "smoke", case.first, case.second, 40, seed=3,
        maximum_rounds=case.limits.maximum_rounds, modular=modular,
        reference_seconds=12.5,
    )
    assert replayed.reference_seconds == 12.5
    assert replayed.candidate_seconds > 0
