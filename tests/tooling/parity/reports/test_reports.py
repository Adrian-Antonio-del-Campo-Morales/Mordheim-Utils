"""Parity report payloads: recorded samples must not mislead.

These checks build prepared results — no fighter compilation, no duel samples —
and assert the payload fields a reader relies on: recorded versus absent
elapsed time, per-engine rates and times, smoke versus certification samples,
battery limits/magnitudes with sensitivity still pending, and truncation rows
that keep their scenario label, rates and pass state.
"""
from mordheim_combat_lab.verification.parity import ParityReport
from mordheim_combat_lab.verification.parity import StatisticalParityResult
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import _battery_runner as runner
from mordheim_combat_lab.verification.parity._report import battery_report_payload
import pytest


def _empty_report() -> ParityReport:
    return ParityReport(complete=True, obligations=(), verified=(), pending=(),
                        divergences=(), exact_checks=())


def _deep_result(scenario, *, modular=(0.6, 0.3, 0.1), candidate=None,
                 passed=True, reference_seconds=0.25, candidate_seconds=0.125):
    """One prepared deep row: the payload only needs the recorded sample."""
    return StatisticalParityResult(
        scenario=scenario, backend="numpy", simulations=50,
        modular_rates=modular,
        vectorized_rates=modular if candidate is None else candidate,
        tolerances=(0.05, 0.05, 0.05), passed=passed,
        reference_seconds=reference_seconds, candidate_seconds=candidate_seconds,
    )


def _row(scenario: str, *, passed: bool = True) -> StatisticalParityResult:
    return StatisticalParityResult(
        scenario=scenario, backend="numpy", simulations=200,
        modular_rates=(0.5, 0.4, 0.1), vectorized_rates=(0.5, 0.4, 0.1),
        tolerances=(0.05, 0.05, 0.05), passed=passed,
    )


@pytest.mark.evidence
def test_payload_records_total_elapsed_time_only_when_measured():
    payload = parity_report_payload(_empty_report(), elapsed_seconds=12.25)
    assert payload["elapsed_seconds"] == 12.25
    # A payload assembled from precomputed samples must not invent a total.
    assert parity_report_payload(_empty_report())["elapsed_seconds"] is None


@pytest.mark.evidence
def test_deep_payload_exposes_samples_rates_times_and_the_pass_state():
    samples = (
        _deep_result("matrix:basic"),
        _deep_result("matrix:defences", candidate=(0.4, 0.5, 0.1), passed=False),
    )
    payload = parity_report_payload(_empty_report(), deep=samples,
                                    deep_pair_set="fast")
    deep = payload["deep"]
    assert deep["pair_set"] == "fast"
    assert len(deep["samples"]) == len(samples)
    assert deep["complete"] == all(row.passed for row in samples)
    assert deep["complete"] is False
    for row in deep["samples"]:
        assert len(row["reference_rates"]) == len(row["candidate_rates"]) == 3
        assert row["reference_seconds"] > 0 and row["candidate_seconds"] > 0
    passing = parity_report_payload(_empty_report(), deep=samples[:1])
    assert passing["deep"]["complete"] is True


@pytest.mark.evidence
def test_smoke_samples_are_not_reported_as_certification_samples():
    smoke = StatisticalParityResult(
        scenario="smoke", backend="numpy", simulations=400,
        modular_rates=(0.5, 0.5, 0.0), vectorized_rates=(0.5, 0.5, 0.0),
        tolerances=(0.05, 0.05, 0.05), passed=True,
    )
    payload = parity_report_payload(_empty_report(), statistical=(smoke,))
    assert payload["complete"]
    assert payload["certification_sample_complete"] is False

    certified = StatisticalParityResult(
        scenario="full", backend="numpy", simulations=100_000,
        modular_rates=(0.5, 0.5, 0.0), vectorized_rates=(0.5, 0.5, 0.0),
        tolerances=(0.05, 0.05, 0.05), passed=True,
    )
    assert parity_report_payload(
        _empty_report(), statistical=(certified,),
    )["certification_sample_complete"] is True


@pytest.mark.evidence
def test_battery_payload_keeps_limits_magnitudes_and_pending_sensitivity():
    passing = runner.BatteryCaseResult(
        case="a", level="complete", variant="B06.2", obligation="B06",
        backend="numpy", status="PASS", keys=(), observables=("winner",),
        rows=64, executed=True, compared=True, approved=True,
        magnitudes=("winner",),
        comparisons=(
            runner.MagnitudeComparison("winner", (0.5, 0.4, 0.1),
                                       (0.5, 0.4, 0.1), (0.05, 0.05, 0.05), True),
        ),
    )
    blocked = runner.BatteryCaseResult(
        case="b", level="complete", variant="B08.4", obligation="B08",
        backend="numpy", status="INCOMPATIBLE", keys=(), observables=("winner",),
        rows=64, blocked_by="state:G00/G02",
        detail="INCOMPATIBLE:state:G00/G02 owner=G00/G02",
    )
    report = runner.BatteryReport(
        complete=False, accepted=False, scope="profile", profile="quick",
        results=(passing, blocked),
        passed=("a",), divergences=(), incompatible=("b",), not_run=(),
        missing_variants=(),
    )
    payload = battery_report_payload(
        report, profile="quick", backend="numpy",
        catalog_sha256="catalog-sha", inventory_sha256="inventory-sha",
        elapsed_seconds=1.5,
    )
    assert payload["magnitudes"]["winner"] == {"cases": 1, "passed": 1}
    assert payload["limits"] == {"b": "state:G00/G02"}
    assert payload["sensitivity"]["demonstrated"] == []
    assert payload["sensitivity"]["pending"] == ["a", "b"]
    assert payload["complete"] is False and payload["accepted"] is False


@pytest.mark.evidence
def test_truncation_rows_flow_into_the_payload_with_their_horizon():
    rows = (_row("basic@rounds=2"), _row("basic@rounds=4"))
    report = ParityReport(complete=True, obligations=(), verified=(),
                          pending=(), divergences=(), exact_checks=())
    payload = parity_report_payload(
        report, truncations=rows, truncation_pair_set="fast",
    )
    truncations = payload["truncations"]
    assert truncations["pair_set"] == "fast"
    assert truncations["complete"] is True
    assert [sample["scenario"] for sample in truncations["samples"]] == [
        "basic@rounds=2", "basic@rounds=4",
    ]
    assert all(len(sample["modular_rates"]) == 3 and len(sample["vectorized_rates"]) == 3
               for sample in truncations["samples"])

    failing = parity_report_payload(
        report, truncations=(_row("basic@rounds=2", passed=False),),
    )
    assert failing["truncations"]["complete"] is False
    assert failing["complete"] is False
