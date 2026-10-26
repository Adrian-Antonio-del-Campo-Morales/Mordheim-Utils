"""Round-truncation statistical parity: real engine distributions per horizon.

The benchmark pair and round budget come from the frozen corpus; horizons,
samples, seeds and the six-sigma gate are unchanged.  Each row is a real
comparison of the modular oracle and the vectorized backend, produced by the
shared runner with ``horizons=``.
"""
from mordheim_combat_lab.verification.parity import TRUNCATION_HORIZONS
from mordheim_combat_lab.verification.parity import ParityCase
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import run_parity
from mordheim_combat_lab.verification.parity import statistical_result
from tests.engines.fixtures.precompiled_catalog import benchmark_case_key
import pytest


def _case(cases, scenario_id: str = "basic"):
    case = cases[benchmark_case_key(scenario_id)]
    return ParityCase(
        label=scenario_id, first=case.first, second=case.second,
        maximum_rounds=case.limits.maximum_rounds, seed=3,
    )


def test_truncation_rows_name_their_horizon_and_pass_smoke(cases):
    run = run_parity(
        (_case(cases),), backends=("numpy",), candidate="counts",
        simulations=400, horizons=TRUNCATION_HORIZONS,
    )
    rows = tuple(statistical_result(row) for row in run.rows)
    assert len(rows) == len(TRUNCATION_HORIZONS)
    for row, horizon in zip(rows, TRUNCATION_HORIZONS):
        assert row.scenario == f"basic@rounds={horizon}"
        assert row.backend == "numpy"
        assert row.simulations == 400
        assert row.passed  # six-sigma gate at small N is permissive


def test_horizons_respect_the_round_budget(cases):
    run = run_parity(
        (_case(cases, "long"),), backends=("numpy",), candidate="counts",
        simulations=60, horizons=(2, 50, 75, 90),
    )
    assert [row.case for row in run.rows] == [
        "long@rounds=2", "long@rounds=50", "long@rounds=75",
    ]


def test_truncation_rows_are_independent_samples_of_the_same_gate(cases):
    # Each horizon row must behave like the aggregate statistical comparison
    # at that truncation budget (the underlying gate is the same function).
    case = _case(cases)
    horizon = TRUNCATION_HORIZONS[0]
    run = run_parity(
        (case,), backends=("numpy",), candidate="counts", simulations=300,
        horizons=(horizon,),
    )
    row = statistical_result(run.rows[0])
    direct = compare_statistical_parity(
        f"basic@rounds={horizon}", case.first, case.second, 300, seed=3,
        maximum_rounds=horizon,
    )
    assert row.scenario == direct.scenario
    assert row.modular_rates == direct.modular_rates
    assert row.vectorized_rates == direct.vectorized_rates
    assert row.passed == direct.passed
