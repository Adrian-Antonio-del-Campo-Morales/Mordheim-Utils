import json

from mordheim_combat_lab.verification import coverage_gate
from mordheim_combat_lab.verification.coverage_gate import CoverageFile
from mordheim_combat_lab.verification.coverage_gate import CoverageReport


def _file(module: str, area: str, covered: tuple[int, ...], statements: tuple[int, ...]):
    return CoverageFile(
        module=module, area=area, statements=len(statements),
        covered=covered, missing=tuple(sorted(set(statements) - set(covered))),
        path=f"src/mordheim_combat/{area}/{module.rsplit('.', 1)[-1]}.py",
    )


def _report(*files):
    return CoverageReport(files=tuple(files), suites=("fake",), seconds=0.0)


def _budget(areas):
    return {"schema": coverage_gate.BUDGET_SCHEMA, "suites": ("fake",),
            "areas": areas}


def test_area_mapping():
    assert coverage_gate._area_for("src/mordheim_combat/vectorized/_driver.py") == "vectorized"
    assert coverage_gate._area_for("src/mordheim_combat/modular/duel.py") == "modular"
    assert coverage_gate._area_for("src/mordheim_combat/phases.py") == "phases"
    assert coverage_gate._area_for("src/mordheim_combat/vector_dice.py") == "phases"
    assert coverage_gate._area_for("src/mordheim_combat/native/_combat_native.pyx") is None


def test_gate_passes_when_every_budgeted_line_is_still_covered():
    entry = _file("mordheim_combat.vectorized._driver", "vectorized",
                  covered=(10, 11, 12), statements=(10, 11, 12, 13, 14))
    budget = _budget({"vectorized": {"mordheim_combat.vectorized._driver": [10, 11, 12]}})
    result = coverage_gate.evaluate(_report(entry), budget)
    assert result.passed
    assert result.errors == ()


def test_gate_fails_when_a_budgeted_line_stops_being_exercised():
    entry = _file("mordheim_combat.vectorized._driver", "vectorized",
                  covered=(10, 12), statements=(10, 11, 12))
    budget = _budget({"vectorized": {"mordheim_combat.vectorized._driver": [10, 11, 12]}})
    result = coverage_gate.evaluate(_report(entry), budget)
    assert not result.passed
    assert any("line(s) lost" in error and "11" in error for error in result.errors)


def test_gate_fails_when_a_budgeted_module_disappears_entirely():
    entry = _file("mordheim_combat.modular.duel", "modular",
                  covered=(1, 2), statements=(1, 2))
    budget = _budget({"vectorized": {
        "mordheim_combat.vectorized._driver": [10, 11, 12]}})
    result = coverage_gate.evaluate(_report(entry), budget)
    assert not result.passed
    assert any(module in error for error in result.errors
               for module in ("_driver",))


def test_area_floor_is_enforced():
    entry = _file("mordheim_combat.modular.duel", "modular",
                  covered=(1,), statements=(1, 2, 3, 4))
    result = coverage_gate.evaluate(_report(entry), None,
                                    minimum_percent={"modular": 90.0})
    assert not result.passed
    assert any("modular" in error and "floor" in error for error in result.errors)
    result = coverage_gate.evaluate(_report(entry), None,
                                    minimum_percent={"modular": 10.0})
    assert result.passed


def test_budget_round_trip(tmp_path):
    entry = _file("mordheim_combat.modular.duel", "modular",
                  covered=(3, 7), statements=(1, 3, 7))
    path = tmp_path / "budget.json"
    coverage_gate.write_budget(path, _report(entry))
    payload = coverage_gate.write_budget(path, _report(entry))
    assert payload["schema"] == coverage_gate.BUDGET_SCHEMA
    loaded = coverage_gate.load_budget(path)
    assert loaded["areas"]["modular"]["mordheim_combat.modular.duel"] == [3, 7]
    loaded_report = CoverageReport(
        files=(_file("mordheim_combat.modular.duel", "modular",
                     covered=(3, 7), statements=(1, 3, 7)),),
        suites=("fake",), seconds=0.0,
    )
    assert coverage_gate.evaluate(loaded_report, loaded).passed


def test_load_budget_rejects_unknown_schema(tmp_path):
    import pytest
    path = tmp_path / "budget.json"
    path.write_text(json.dumps({"schema": "nope"}), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported coverage budget schema"):
        coverage_gate.load_budget(path)


def test_load_budget_mentions_update_flag_when_missing(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError, match="--update-budget"):
        coverage_gate.load_budget(tmp_path / "absent.json")


def test_measurement_smoke_requires_coverage_installed():
    pytest = __import__("pytest")
    pytest.importorskip("coverage")
    report = coverage_gate.measure_coverage(("tests/combat/vectorized/test_backends.py",))
    assert report.files
    assert report.suites == ("tests/combat/vectorized/test_backends.py",)
    assert any(item.area == "vectorized" and item.statements > 0
               for item in report.files)
    assert report.seconds >= 0
