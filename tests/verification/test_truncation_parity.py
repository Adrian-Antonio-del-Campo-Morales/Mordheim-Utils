from mordheim_combat_lab.verification.parity import TRUNCATION_HORIZONS
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import compare_truncation_parity
from mordheim_combat_lab.verification.parity import parity_report_markdown
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import ParityReport
from mordheim_combat_lab.verification.parity import StatisticalParityResult
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_construction.compiler import compile_fighter


def _pair(scenario_id: str = "basic"):
    scenario = next(
        item for item in benchmark_scenarios() if item.id == scenario_id
    )
    return (
        compile_fighter(scenario.first), compile_fighter(scenario.second),
        scenario.maximum_rounds,
    )


def test_truncation_horizons_are_ascending_and_positive():
    assert TRUNCATION_HORIZONS == tuple(sorted(TRUNCATION_HORIZONS))
    assert all(horizon >= 1 for horizon in TRUNCATION_HORIZONS)


def test_truncation_rows_name_their_horizon_and_pass_smoke():
    first, second, maximum_rounds = _pair()
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


def test_horizons_respect_the_round_budget():
    first, second, maximum_rounds = _pair("long")  # 75-round budget
    rows = compare_truncation_parity(
        "long", first, second, 60, seed=3,
        maximum_rounds=maximum_rounds, horizons=(2, 50, 75, 90),
    )
    assert [row.scenario for row in rows] == [
        "long@rounds=2", "long@rounds=50", "long@rounds=75",
    ]


def test_no_fitting_horizon_is_rejected():
    import pytest
    first, second, _ = _pair()
    with pytest.raises(ValueError, match="no truncation horizon"):
        compare_truncation_parity(
            "basic", first, second, 50, maximum_rounds=5,
            horizons=(8, 10),
        )


def test_truncation_rows_are_independent_samples_of_the_same_gate():
    # Each horizon row must behave like the aggregate statistical comparison
    # at that truncation budget (the underlying gate is the same function).
    first, second, maximum_rounds = _pair()
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


def test_truncation_rows_flow_into_payload_and_markdown():
    first, second, maximum_rounds = _pair()
    rows = compare_truncation_parity(
        "basic", first, second, 200, seed=3,
        maximum_rounds=maximum_rounds, horizons=(2, 4),
    )
    report = ParityReport(complete=True, obligations=(), verified=(),
                          pending=(), divergences=(), exact_checks=())
    payload = parity_report_payload(report, truncations=rows)
    truncations = payload["truncations"]
    assert isinstance(truncations, dict)
    assert truncations["complete"]
    assert len(truncations["samples"]) == 2
    assert truncations["samples"][0]["scenario"] == "basic@rounds=2"
    assert "modular_rates" in truncations["samples"][0]
    assert "vectorized_rates" in truncations["samples"][0]
    assert len(truncations["samples"][0]["modular_rates"]) == 3
    markdown = parity_report_markdown(payload)
    assert "## Round-truncation parity samples" in markdown
    assert "basic@rounds=2" in markdown
    assert "| True |" in markdown


def test_truncation_pooled_oracle_matches_the_sequential_path():
    first, second, maximum_rounds = _pair()
    kwargs = dict(simulations=300, seed=3, maximum_rounds=maximum_rounds,
                  horizons=(2, 4, 6))
    sequential = compare_truncation_parity("basic", first, second, **kwargs)
    pooled = compare_truncation_parity(
        "basic", first, second, workers=2, **kwargs)
    def fields(rows):
        return [(row.scenario, row.modular_rates, row.vectorized_rates,
                 row.tolerances, row.passed) for row in rows]
    assert fields(pooled) == fields(sequential)


def test_truncation_progress_fires_once_per_horizon():
    first, second, maximum_rounds = _pair()
    calls = []
    rows = compare_truncation_parity(
        "basic", first, second, 60, seed=3,
        maximum_rounds=maximum_rounds, horizons=(2, 4, 6),
        on_progress=lambda: calls.append(1),
    )
    assert len(calls) == len(rows) == 3

