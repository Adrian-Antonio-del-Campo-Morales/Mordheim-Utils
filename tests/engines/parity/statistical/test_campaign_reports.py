"""Report generation for the parity campaign.

The report is built from runner rows, so these checks use synthetic
``ParityRow`` values: they pin the certificate's identities, rates,
tolerances, differences, timings and verdicts without sampling an engine or
running a duel.  What they do not prove is parity itself; that is the
campaign's own result, not a report contract.
"""
import json

import pytest

from tools.verification.parity_campaign import campaign_markdown
from tools.verification.parity_campaign import campaign_payload
from mordheim_combat_lab.verification.parity import MagnitudeComparison
from mordheim_combat_lab.verification.parity import ParityRow


def _config(keys, **overrides):
    config = {
        "level": "small",
        "scenario_keys": list(keys),
        "simulations": 1_000,
        "seed": 2_026,
        "maximum_rounds": None,
        "workers": "auto",
        "corpus": "tests/engines/fixtures/compiled-cases.json",
        "corpus_sha256": "0" * 64,
    }
    config.update(overrides)
    return config


def _row(
    key, *, modular=(0.50, 0.30, 0.20), candidate=(0.52, 0.29, 0.19),
    tolerances=(0.004, 0.004, 0.004), passed=True, status="PASS",
    executed=True, compared=True, approved=True, detail="", simulations=1_000,
):
    return ParityRow(
        case=key,
        backend="numpy",
        maximum_rounds=50,
        simulations=simulations,
        status=status,
        comparisons=(MagnitudeComparison(
            "winner", modular, candidate, tolerances, passed, detail,
        ),) if compared or executed else (),
        executed=executed,
        compared=compared,
        approved=approved,
        modular_seconds=12.5,
        candidate_seconds=3.5,
        detail=detail,
    )


def test_payload_records_identity_rates_tolerances_differences_and_timings():
    payload = campaign_payload(
        (_row("scenario/basic"),), config=_config(["scenario/basic"]),
        elapsed_seconds=16.0,
    )
    record, = payload["scenarios"]
    assert record["corpus_key"] == "scenario/basic"
    assert record["scenario"] == "basic"
    assert record["simulations_per_engine"] == 1_000
    assert record["maximum_rounds"] == 50
    assert record["executed"] and record["compared"] and record["approved"]
    assert record["verdict"] == "pass"
    winner, = record["magnitudes"]
    assert winner["modular_rates"] == [0.50, 0.30, 0.20]
    assert winner["candidate_rates"] == [0.52, 0.29, 0.19]
    assert winner["tolerances"] == [0.004, 0.004, 0.004]
    assert winner["differences"] == pytest.approx([0.02, 0.01, 0.01])
    assert (record["reference_seconds"], record["candidate_seconds"]) == (12.5, 3.5)
    assert payload["complete"] is True
    assert payload["config"]["seed"] == 2_026
    assert payload["elapsed_seconds"] == 16.0
    assert json.loads(json.dumps(payload)) == payload


def test_elapsed_time_and_certification_size_are_only_claimed_when_measured():
    smoke = campaign_payload(
        (_row("scenario/basic"),), config=_config(["scenario/basic"]),
    )
    # A payload assembled without a measurement must not invent a total, and a
    # narrow campaign is not reported as a certification-sized sample.
    assert smoke["elapsed_seconds"] is None
    assert smoke["certification_sample_complete"] is False

    certified = campaign_payload(
        (_row("scenario/basic", simulations=100_000),),
        config=_config(["scenario/basic"], simulations=100_000),
    )
    assert certified["certification_sample_complete"] is True


def test_uncompared_and_unexecuted_rows_are_never_approved():
    rows = (
        _row(
            "scenario/basic", modular=(0.50, 0.30, 0.20),
            candidate=(0.10, 0.30, 0.60), passed=False, status="DIVERGENCE",
            approved=False, detail="DIVERGENCE: winner[first] outside tolerance",
        ),
        _row(
            "scenario/long", status="NOT_RUN", executed=False,
            compared=False, approved=False, detail="NOT_RUN:reference: boom",
        ),
    )
    payload = campaign_payload(
        rows, config=_config([row.case for row in rows]),
    )
    assert [record["verdict"] for record in payload["scenarios"]] == [
        "divergent", "not-run",
    ]
    coverage = payload["coverage"]
    assert coverage["approved"] == 0
    assert coverage["compared"] == 1
    assert coverage["executed"] == 1
    assert coverage["divergent"] == 1
    assert coverage["not_run"] == 1
    assert payload["complete"] is False

    markdown = campaign_markdown(payload)
    assert "`scenario/long`: `NOT_RUN`" in markdown
    assert "NOT_RUN:reference: boom" in markdown
    assert "Complete: `False`" in markdown


def test_incompatible_scenarios_are_reported_as_not_run():
    payload = campaign_payload(
        (_row(
            "scenario/basic", status="INCOMPATIBLE", executed=False,
            compared=False, approved=False,
            detail="INCOMPATIBLE:admission: this duel requires the modular engine",
        ),),
        config=_config(["scenario/basic"]),
    )
    record, = payload["scenarios"]
    assert record["verdict"] == "not-run"
    assert payload["coverage"]["incompatible"] == 1
    assert payload["coverage"]["not_run"] == 0
    assert payload["complete"] is False
    assert "INCOMPATIBLE:admission" in campaign_markdown(payload)


def test_rejected_scenarios_are_reported_and_block_completeness():
    payload = campaign_payload(
        (_row("scenario/basic"),),
        config=_config(["scenario/basic", "scenario/missing"]),
        rejected=(("scenario/missing", "the frozen corpus has no case scenario/missing"),),
    )
    assert payload["coverage"]["selected"] == 2
    assert payload["coverage"]["rejected"] == 1
    assert payload["coverage"]["not_run"] == 1
    assert payload["complete"] is False
    markdown = campaign_markdown(payload)
    assert "`scenario/missing`: `NOT_RUN`" in markdown
    assert "the frozen corpus has no case" in markdown


def test_empty_run_is_incomplete():
    payload = campaign_payload((), config=_config([]))
    assert payload["complete"] is False
    assert payload["coverage"]["selected"] == 0
    assert "None: every selected scenario" not in campaign_markdown(payload)


def test_markdown_carries_the_configuration_and_per_outcome_evidence():
    payload = campaign_payload(
        (_row("scenario/basic"),),
        config=_config(["scenario/basic"], level="normal", workers=8),
        elapsed_seconds=4.0,
    )
    markdown = campaign_markdown(payload)
    assert "Level: `normal`" in markdown
    assert "Workers: `8`" in markdown
    assert "Corpus SHA256: `" in markdown
    assert "| Corpus key |" in markdown
    assert "50.000%/30.000%/20.000%" in markdown   # modular rates
    assert "52.000%/29.000%/19.000%" in markdown   # NumPy rates
    assert "0.400%/0.400%/0.400%" in markdown      # tolerances
    assert "2.000%/1.000%/1.000%" in markdown      # differences
