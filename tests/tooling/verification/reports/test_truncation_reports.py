"""Truncation report payload and progress contract (tooling)."""
from mordheim_combat_lab.verification.parity import compare_truncation_parity
from mordheim_combat_lab.verification.parity import parity_report_markdown
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import ParityReport
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_construction.compiler import compile_fighter
import pytest


def _pair(scenario_id: str = "basic"):
    scenario = next(
        item for item in benchmark_scenarios() if item.id == scenario_id
    )
    return (
        compile_fighter(scenario.first), compile_fighter(scenario.second),
        scenario.maximum_rounds,
    )


@pytest.mark.evidence
def test_truncation_rows_flow_into_payload_and_markdown():
    first, second, maximum_rounds = _pair()
    rows = compare_truncation_parity(
        "basic", first, second, 200, seed=3,
        maximum_rounds=maximum_rounds, horizons=(2, 4),
    )
    report = ParityReport(complete=True, obligations=(), verified=(),
                          pending=(), divergences=(), exact_checks=())
    payload = parity_report_payload(
        report, truncations=rows, truncation_pair_set="fast",
    )
    truncations = payload["truncations"]
    assert truncations["pair_set"] == "fast"
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


@pytest.mark.evidence
def test_truncation_progress_fires_once_per_horizon():
    first, second, maximum_rounds = _pair()
    calls = []
    rows = compare_truncation_parity(
        "basic", first, second, 60, seed=3,
        maximum_rounds=maximum_rounds, horizons=(2, 4, 6),
        on_progress=lambda: calls.append(1),
    )
    assert len(calls) == len(rows) == 3
