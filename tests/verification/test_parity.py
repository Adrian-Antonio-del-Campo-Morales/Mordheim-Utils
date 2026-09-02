from mordheim_combat_lab.verification.parity import verify_vectorized_parity
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import parity_report_markdown
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import verify_specification_parity
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


def test_vectorized_parity_inventory_is_complete_and_exact_checks_pass():
    report = verify_vectorized_parity()
    assert report.pending == ()
    assert report.divergences == ()
    assert report.complete
    assert set(report.exact_checks) == {
        "hit-targets", "wound-targets", "attack-pools", "priority",
        "keyed-dice-replay",
        "armour", "injury",
    }


def test_parity_inventory_covers_fields_tags_and_complex_sequences():
    report = verify_vectorized_parity()
    kinds = {item.kind for item in report.obligations}
    assert kinds == {"field", "tag", "sequence"}
    assert all(item.evidence for item in report.obligations)


def test_semantic_specs_are_reused_as_a_case_level_parity_inventory():
    report = verify_specification_parity()
    assert len(report.cases) == 3347
    assert report.divergences == ()
    assert len(report.passed) == 3344
    assert len(report.pending) == 3
    assert report.out_of_scope == ()
    assert {item.status for item in report.cases} <= {
        "PASS", "DIVERGENCE", "PENDING_ADAPTER", "OUT_OF_SCOPE",
    }
    assert all(
        item.status == "PASS"
        for item in report.cases if item.operation in {"attacks", "priority"}
    )


def test_statistical_parity_reports_three_outcomes_and_six_sigma_tolerances():
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    result = compare_statistical_parity("smoke", fighter, fighter, 20, seed=3)
    assert len(result.modular_rates) == len(result.vectorized_rates) == 3
    assert len(result.tolerances) == 3
    assert all(tolerance >= .0025 for tolerance in result.tolerances)


def test_report_distinguishes_smoke_samples_from_certification_samples():
    report = verify_vectorized_parity()
    payload = parity_report_payload(report)
    assert payload["complete"]
    assert not payload["certification_sample_complete"]
    markdown = parity_report_markdown(payload)
    assert "Oracle: `combat.modular (read-only)`" in markdown
    assert "## Deterministic checks" in markdown


def test_report_exposes_semantic_case_statuses_without_claiming_completion():
    report = verify_vectorized_parity()
    specifications = verify_specification_parity()
    payload = parity_report_payload(report, specifications=specifications)
    assert not payload["complete"]
    assert payload["specifications"]["passed"]
    assert payload["specifications"]["pending"]
    markdown = parity_report_markdown(payload)
    assert "## Semantic specification parity" in markdown
    assert "PENDING_ADAPTER: `3`" in markdown
