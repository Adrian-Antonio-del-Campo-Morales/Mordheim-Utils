"""Round-truncation parity: both inputs loaded from the frozen corpus.

The benchmark pair and its round budget come straight from the precompiled
case; no knowledge base is read and no fighter is compiled.  Horizons,
samples, seeds and the six-sigma gate are unchanged.
"""
from mordheim_combat_lab.verification.parity import TRUNCATION_HORIZONS
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import compare_truncation_parity
from mordheim_combat_lab.verification.parity import StatisticalParityResult
import pytest


def _pair(cases, scenario_id: str = "basic"):
    case = cases[f"benchmark/{scenario_id}"]
    return case.first, case.second, case.limits.maximum_rounds


@pytest.mark.phase5_vectorized
def test_truncation_horizons_are_ascending_and_positive():
    assert TRUNCATION_HORIZONS == tuple(sorted(TRUNCATION_HORIZONS))
    assert all(horizon >= 1 for horizon in TRUNCATION_HORIZONS)


@pytest.mark.phase5_vectorized
def test_truncation_rows_name_their_horizon_and_pass_smoke(cases):
    first, second, maximum_rounds = _pair(cases)
    rows = compare_truncation_parity(
        "basic", first, second, 400, seed=3,
        maximum_rounds=maximum_rounds,
    )
    assert len(rows) == len(TRUNCATION_HORIZONS)
    for row, horizon in zip(rows, TRUNCATION_HORIZONS):
        assert isinstance(row, StatisticalParityResult)
        assert row.scenario == f"basic@rounds={horizon}"
        assert row.backend == "numpy"
        assert row.simulations == 400
        assert row.passed  # six-sigma gate at small N is permissive


@pytest.mark.phase5_vectorized
def test_horizons_respect_the_round_budget(cases):
    first, second, maximum_rounds = _pair(cases, "long")  # 75-round budget
    rows = compare_truncation_parity(
        "long", first, second, 60, seed=3,
        maximum_rounds=maximum_rounds, horizons=(2, 50, 75, 90),
    )
    assert [row.scenario for row in rows] == [
        "long@rounds=2", "long@rounds=50", "long@rounds=75",
    ]


@pytest.mark.phase5_vectorized
def test_no_fitting_horizon_is_rejected(cases):
    first, second, _ = _pair(cases)
    with pytest.raises(ValueError, match="no truncation horizon"):
        compare_truncation_parity(
            "basic", first, second, 50, maximum_rounds=5,
            horizons=(8, 10),
        )


@pytest.mark.phase5_vectorized
def test_truncation_rows_are_independent_samples_of_the_same_gate(cases):
    # Each horizon row must behave like the aggregate statistical comparison
    # at that truncation budget (the underlying gate is the same function).
    first, second, maximum_rounds = _pair(cases)
    horizon = TRUNCATION_HORIZONS[0]
    rows = compare_truncation_parity(
        "basic", first, second, 300, seed=3,
        maximum_rounds=maximum_rounds, horizons=(horizon,),
    )
    direct = compare_statistical_parity(
        f"basic@rounds={horizon}", first, second, 300, seed=3,
        maximum_rounds=horizon,
    )
    assert rows[0].scenario == direct.scenario
    assert rows[0].modular_rates == direct.modular_rates
    assert rows[0].vectorized_rates == direct.vectorized_rates
    assert rows[0].passed == direct.passed


@pytest.mark.phase5_vectorized
def test_truncation_pooled_oracle_matches_the_sequential_path(cases):
    first, second, maximum_rounds = _pair(cases)
    kwargs = dict(simulations=300, seed=3, maximum_rounds=maximum_rounds,
                  horizons=(2, 4, 6))
    sequential = compare_truncation_parity("basic", first, second, **kwargs)
    pooled = compare_truncation_parity(
        "basic", first, second, workers=2, **kwargs)
    def fields(rows):
        return [(row.scenario, row.modular_rates, row.vectorized_rates,
                 row.tolerances, row.passed) for row in rows]
    assert fields(pooled) == fields(sequential)



