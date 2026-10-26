"""Battery preparation, completeness and report bookkeeping.

These tests protect the battery layer built on the shared runner: result
stages (prepared, executed, compared, approved), clause/backend bookkeeping,
failure classification and report completeness.  Generic runner and
comparator checks live in ``test_runner.py``; the catalogue's own integrity is
covered by ``test_parity_battery_cases.py``.
"""
from types import SimpleNamespace

import pytest

from mordheim_combat_lab.verification.parity import _battery_runner as battery
from mordheim_combat_lab.verification.parity import _runner
from mordheim_combat_lab.verification.parity._report import battery_report_payload



def case(identifier="case", *, variant_id="B06.1", **options):
    values = dict(
        id=identifier, level="complete", variant=variant_id, origin="new:test",
        first=None, second=None, rows=8, seed=1, maximum_rounds=4,
        context=None, decisions={}, decision_scope="uniform",
        observables=("winner", "rounds"), blocked_by=None,
    )
    values.update(options)
    return SimpleNamespace(**values)


def result(identifier="a", status="PASS", *, backend="numpy", compared=None,
           approved=None, detail="", variant="B06.1", executed=None,
           keys=(), comparisons=(), blocked_by=None):
    if executed is None:
        executed = status in {"PASS", "DIVERGENCE"}
    return battery.BatteryCaseResult(
        case=identifier, level="complete", variant=variant,
        obligation=variant.split(".")[0],
        backend=backend, status=status, keys=tuple(keys), observables=("winner",),
        rows=8, executed=executed,
        compared=executed if compared is None else compared,
        approved=(status == "PASS") if approved is None else approved,
        magnitudes=tuple(item.magnitude for item in comparisons),
        comparisons=tuple(comparisons), detail=detail, blocked_by=blocked_by,
    )


def report(results, *, complete=False, accepted=False):
    return battery.BatteryReport(
        complete=complete, accepted=accepted, scope="profile", profile="quick",
        results=tuple(results),
        passed=tuple(item.case for item in results if item.status == "PASS"),
        divergences=tuple(item.case for item in results if item.status == "DIVERGENCE"),
        incompatible=tuple(item.case for item in results if item.status == "INCOMPATIBLE"),
        not_run=tuple(item.case for item in results if item.status == "NOT_RUN"),
        missing_variants=(),
    )


def comparison(magnitude, *, passed=True, modular=(0.5, 0.4, 0.1),
               candidate=(0.5, 0.4, 0.1), detail=""):
    return _runner.MagnitudeComparison(
        magnitude=magnitude, modular_rates=tuple(modular),
        candidate_rates=tuple(candidate), tolerances=(0.05, 0.05, 0.05),
        passed=passed, detail=detail,
    )


def battery_payload(report_, *, backend="numpy", backends=None):
    return battery_report_payload(
        report_, profile=report_.profile, backend=backend,
        catalog_sha256="catalog-sha", inventory_sha256="inventory-sha",
        elapsed_seconds=1.5, backends=backends,
    )


def test_battery_payload_records_stages_limits_and_pending_sensitivity():
    report_ = report((
        result("a", "PASS", compared=True, approved=True,
               comparisons=(comparison("winner"), comparison("rounds"))),
        result("b", "DIVERGENCE", compared=True,
               comparisons=(comparison("winner", passed=False,
                                       modular=(0.9, 0.1, 0.0),
                                       candidate=(0.1, 0.9, 0.0)),),
               detail="DIVERGENCE: winner[first]: modular=0.9, candidate=0.1, tol=0.05"),
        result("c", "INCOMPATIBLE", blocked_by="state:G00/G02",
               detail="INCOMPATIBLE:state:G00/G02"),
        result("d", "NOT_RUN",
               detail="NOT_RUN:native-stale: extension is not installed"),
        result("e", "NOT_RUN", detail="NOT_RUN:compile:KeyError: missing weapon"),
    ))
    payload = battery_payload(report_)
    coverage = payload["coverage"]
    assert payload["execution"] == "run"
    # A real input limit is not preparation evidence; a compile error still is.
    assert coverage["prepared"] == 4
    assert coverage["executed"] == 2
    assert coverage["compared"] == 2
    assert coverage["approved"] == 1
    assert coverage["divergent"] == 1
    assert coverage["errors"] == 2
    assert coverage["dependency"] == 2
    assert set(payload["magnitudes"]) == {"winner", "rounds"}
    assert payload["limits"] == {"c": "state:G00/G02"}
    assert payload["sensitivity"]["demonstrated"] == []
    assert payload["sensitivity"]["pending"] == ["a", "b", "c", "d", "e"]
    assert payload["complete"] is False and payload["accepted"] is False


def test_battery_payload_keeps_backends_separate():
    report_ = report((
        result("a", "PASS", compared=True, approved=True,
               comparisons=(comparison("winner"),)),
        result("a", "NOT_RUN", backend="native",
               detail="NOT_RUN:native-stale: extension is stale"),
    ))
    payload = battery_payload(report_, backends=("numpy", "native"))
    rows = {row["backend"]: row for row in payload["backends"]}
    assert rows["numpy"]["available"] is True
    assert rows["numpy"]["compared"] == 1 and rows["numpy"]["approved"] == 1
    assert rows["native"]["available"] is False and rows["native"]["not_run"] == 1
    assert rows["native"]["executed"] == 0


def test_an_exception_before_observation_is_neither_execution_nor_comparison():
    report_ = report((
        result("a", "DIVERGENCE", executed=False, compared=False,
               detail="DIVERGENCE:exception:ValueError: boom"),
        result("b", "DIVERGENCE", compared=True,
               comparisons=(comparison("winner", passed=False,
                                       modular=(0.1, 0.8, 0.1),
                                       candidate=(0.3, 0.6, 0.1)),),
               detail="DIVERGENCE: winner[second]: modular=0.1, candidate=0.3, tol=0.05"),
    ))
    payload = battery_payload(report_)
    coverage = payload["coverage"]
    assert coverage["executed"] == 1
    assert coverage["compared"] == 1
    assert coverage["approved"] == 0
    assert coverage["errors"] == 2
    assert payload["cases"][0]["executed"] is False
    assert payload["cases"][0]["compared"] is False


def test_malformed_outcome_codes_are_an_own_error_not_a_dependency():
    from mordheim_combat_lab.verification.parity._report import battery_failure_kind

    detail = "NOT_RUN:outcome-codes: oracle winner code(s) [3] outside [0, 1, 2]"
    assert battery_failure_kind("NOT_RUN", detail) == "error"
    assert battery_failure_kind("NOT_RUN", "NOT_RUN:native-stale: absent") == "dependency"


def test_battery_report_is_incomplete_with_missing_variants(monkeypatch):
    item = case("a", variant_id="B06.1")
    monkeypatch.setattr(battery, "required_variants", lambda profile: ("B06.1", "B06.2"))
    incomplete = battery.battery_report((result("a"),), (item,), profile="complete")
    assert incomplete.missing_variants == ("B06.2",)
    assert incomplete.complete is False and incomplete.accepted is False

    monkeypatch.setattr(battery, "required_variants", lambda profile: ("B06.1",))
    complete = battery.battery_report((result("a"),), (item,), profile="complete")
    assert complete.complete is True and complete.accepted is True

    diagnostic = battery.battery_report((result("a"),), (item,), profile=None)
    assert diagnostic.scope == "provided" and diagnostic.accepted is False


def test_battery_report_marks_a_dependency_incomplete():
    report_ = battery.battery_report(
        (result("a", "INCOMPATIBLE",
                detail="INCOMPATIBLE:state:G00/G02"),),
        (case("a"),), profile="quick",
    )
    assert report_.complete is False and report_.accepted is False
    assert report_.incompatible == ("a",)


def test_battery_report_merges_backends_with_the_worst_verdict():
    merged = battery.battery_report(
        (
            result("a"), result("b"),
            result("a", "PASS", backend="native"),
            result("b", "DIVERGENCE", backend="native",
                   detail="DIVERGENCE: winner[first]"),
        ),
        (case("a"), case("b")), profile="quick",
    )
    assert len(merged.results) == 4
    assert merged.passed == ("a",)
    assert merged.divergences == ("b",)
    assert merged.complete is False and merged.accepted is False
