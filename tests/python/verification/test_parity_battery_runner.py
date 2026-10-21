"""Infrastructure proofs for the parity battery runner (synthetic only).

These tests exercise the comparator, typed witnesses, pair resolution and
coverage.  They never compile a fighter, sample an engine or run a candidate.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from mordheim_combat_lab.verification.parity import _battery_runner as runner


def witness(name="frenzy", kind="flag", present="flag-true", absent="flag-false"):
    return SimpleNamespace(name=name, kind=kind, present=present, absent=absent)


def variant(identifier="B06.1", *, witness_value=None, owner="G06"):
    return SimpleNamespace(
        id=identifier, title=identifier, witness=witness_value, case_kind="duel",
        required=True, level="complete", owner=owner, evidence="", secondary=(),
    )


def case(identifier="case", *, variant_id="B06.1", **options):
    values = dict(
        id=identifier, level="complete", variant=variant_id, origin="new:test",
        first=None, second=None, rows=8, seed=1, maximum_rounds=4,
        context=None, decisions={}, decision_scope="uniform",
        observables=("winner", "frenzy"), expect="present", positive_control=None,
        witness_value=None, also_covers=(), comparison="witness", focused=None,
        requires=(), blocked_by=None, note="",
    )
    values.update(options)
    return SimpleNamespace(**values)


def test_tolerance_is_the_existing_six_sigma_gate():
    assert runner._tolerance(0.0, 0.0, 64) == pytest.approx(0.0025)
    expected = 6 * np.sqrt(0.25 / 64 + 0.25 / 64)
    assert runner._tolerance(0.5, 0.5, 64) == pytest.approx(expected)


def test_compare_passes_and_reports_the_worst_category():
    left = np.array([0, 1] * 32)
    right = np.array([0, 1] * 32)
    assert runner._compare([("winner", left, right)], 64) is None
    shifted = np.array([0] * 64)
    detail = runner._compare([("winner", left, shifted)], 64)
    assert detail is not None and "winner[1]" in detail


@pytest.mark.parametrize(
    "kind,present,values,expected,activated,rate",
    [
        ("counter", "count>0", np.array([0, 2, 0, 1]), None, True, 0.5),
        ("counter", "count==0", np.array([0, 0, 0, 0]), None, True, 1.0),
        ("flag", "flag-true", np.array([False, True, False]), None, True, 1 / 3),
        ("flag", "flag-false", np.array([False, False]), None, True, 1.0),
        ("category", "class-equals", np.array([0, 1, 1]), 1, True, 2 / 3),
        ("category", "class-differs", np.array([1, 1]), 0, True, 1.0),
        ("direct-result", "value-equals", np.array([7, 8]), 7, True, 0.5),
        ("direct-result", "value-differs", np.array([7, 8]), 7, True, 0.5),
        ("hash", "hash-changes", np.array(["a", "b"]), "a", True, 0.5),
        ("hash", "hash-same", np.array(["a", "a"]), "a", True, 1.0),
    ],
)
def test_typed_witness_predicates(kind, present, values, expected, activated, rate):
    seen, fraction = runner._predicate(kind, present, values, expected)
    assert seen is activated
    assert fraction == pytest.approx(rate)


def test_acting_order_is_a_category_not_a_positive_count():
    seen, rate = runner._predicate("category", "class-equals", np.array([0, 0]), 0)
    assert seen and rate == 1.0
    seen, rate = runner._predicate("category", "class-equals", np.array([1, 1]), 0)
    assert not seen and rate == 0.0


def test_focused_condition_label_maps_to_the_shared_code():
    assert runner._focused_value(case(focused="condition:out")) == ("condition", 4)
    assert runner._focused_value(case(focused="winner:2")) == ("winner", 2)


def test_blocked_case_is_reported_without_compiling(monkeypatch):
    monkeypatch.setitem(runner.VARIANTS, "B14.1", variant("B14.1", witness_value=witness("leadership-test-value", "direct-result", "value-equals", "value-differs")))
    monkeypatch.setattr(runner, "VARIANT_KEYS", {"B14.1": ("k::v",)})
    item = case(variant_id="B14.1", blocked_by="consume:G05")
    result = runner._run_case(item, backend="numpy", rows=8, root=None,
                              focused_seen={}, witness_seen={})
    assert result.status == "INCOMPATIBLE"
    assert "consumer:B14.1" in result.detail and "G05" in result.detail
    assert result.variant == "B14.1" and result.keys == ("k::v",)


def test_non_activating_positive_control_is_not_activated():
    control = case("positive")
    negative = case("negative", expect="absent", positive_control="positive")
    results = (
        runner.BatteryCaseResult(
            case="positive", level="complete", variant="B06.1", obligation="B06",
            backend="numpy", status="PASS", keys=(), observables=("frenzy",), rows=8,
        ),
        runner.BatteryCaseResult(
            case="negative", level="complete", variant="B06.1", obligation="B06",
            backend="numpy", status="PASS", keys=(), observables=("frenzy",), rows=8,
        ),
    )
    resolved = runner._resolve_controls((control, negative), results, {}, {"positive": False})
    assert resolved[1].status == "NOT_ACTIVATED"
    assert "positive-control:positive" in resolved[1].detail


def test_focused_positive_without_negative_is_not_evidence():
    positive = case("focused-positive", comparison="focused", focused="winner:2")
    result = runner.BatteryCaseResult(
        case="focused-positive", level="complete", variant="B06.1", obligation="B06",
        backend="numpy", status="PASS", keys=(), observables=("winner",), rows=8,
        comparison="focused", coupling="focused",
    )
    resolved = runner._resolve_controls((positive,), (result,), {"focused-positive": True}, {})
    assert resolved[0].status == "NOT_ACTIVATED"
    assert "no-negative-control" in resolved[0].detail


def test_missing_variants_and_provided_scope(monkeypatch):
    item = case("a", variant_id="B06.1")
    monkeypatch.setattr(runner, "required_variants", lambda profile: ("B06.1", "B06.2"))
    monkeypatch.setattr(
        runner, "_run_case",
        lambda *args, **kwargs: runner.BatteryCaseResult(
            case="a", level="complete", variant="B06.1", obligation="B06",
            backend="numpy", status="PASS", keys=(), observables=("winner",), rows=8,
        ),
    )
    report = runner.run_battery((item,), profile="complete", root=".")
    assert report.scope == "profile"
    assert report.missing_variants == ("B06.2",)
    assert report.complete is False and report.accepted is False

    subset = runner.run_battery((item,), root=".")
    assert subset.scope == "provided"
    assert subset.accepted is False and subset.missing_variants == ()


def test_also_covers_counts_for_coverage(monkeypatch):
    item = case("a", variant_id="B06.1", also_covers=("B06.2",))
    monkeypatch.setattr(runner, "required_variants", lambda profile: ("B06.1", "B06.2"))
    monkeypatch.setattr(
        runner, "_run_case",
        lambda *args, **kwargs: runner.BatteryCaseResult(
            case="a", level="complete", variant="B06.1", obligation="B06",
            backend="numpy", status="PASS", keys=(), observables=("winner",), rows=8,
        ),
    )
    report = runner.run_battery((item,), profile="complete", root=".")
    assert report.missing_variants == ()
    assert report.complete is True and report.accepted is True
