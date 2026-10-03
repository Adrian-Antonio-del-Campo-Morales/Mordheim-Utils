import json

import pytest

from mordheim_combat_lab.verification import coverage_gate
from mordheim_combat_lab.verification.coverage_gate import CoverageFile
from mordheim_combat_lab.verification.coverage_gate import CoverageReport


def _file(module: str, area: str, covered: tuple[int, ...], statements: tuple[int, ...]):
    return CoverageFile(
        module=module, area=area, statements=len(statements),
        covered=covered, missing=tuple(sorted(set(statements) - set(covered))),
        path=f"packages/python/combat-engine/mordheim_combat/{area}/{module.rsplit('.', 1)[-1]}.py",
    )


def _report(*files):
    return CoverageReport(files=tuple(files), suites=("fake",), seconds=0.0)


def _budget(areas):
    return {"schema": coverage_gate.BUDGET_SCHEMA, "suites": ("fake",),
            "areas": areas}


def test_area_mapping():
    assert coverage_gate._area_for("packages/python/combat-engine/mordheim_combat/vectorized/_driver.py") == "vectorized"
    assert coverage_gate._area_for("packages/python/combat-engine/mordheim_combat/modular/duel.py") == "modular"
    assert coverage_gate._area_for("packages/python/combat-engine/mordheim_combat/phases.py") == "phases"
    assert coverage_gate._area_for("packages/python/combat-engine/mordheim_combat/vector_dice.py") == "phases"
    assert coverage_gate._area_for("packages/python/combat-engine/mordheim_combat/native/_combat_native.pyx") is None


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
    report = coverage_gate.measure_coverage(("tests/python/combat/vectorized/test_backends.py",))
    assert report.files
    assert report.suites == ("tests/python/combat/vectorized/test_backends.py",)
    assert any(item.area == "vectorized" and item.statements > 0
               for item in report.files)
    assert report.seconds >= 0


@pytest.mark.parametrize('exit_code', [1, 2, 3, 4, 5])
def test_failed_interrupted_or_empty_test_run_cannot_return_measurement(monkeypatch, exit_code):
    # Failure, interruption/collection error, internal error, usage error and
    # empty collection all invalidate a coverage measurement.
    monkeypatch.setattr(pytest, 'main', lambda args: pytest.ExitCode(exit_code))
    with pytest.raises(RuntimeError, match=f'pytest exit code {exit_code}'):
        coverage_gate.measure_coverage(('unused-detector',))


@pytest.mark.parametrize('entrypoint', ['gate', 'gate-update', 'budget-script'])
def test_real_failing_detector_cannot_pass_gate_or_overwrite_budget(tmp_path, entrypoint):
    from pathlib import Path
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[3]
    detector = tmp_path / 'test_failing_detector.py'
    detector.write_text('def test_detector():\n    assert False, "deliberate detector failure"\n', encoding='utf-8')
    budget = tmp_path / 'budget.json'
    original = json.dumps(_budget({})).encode('utf-8')
    budget.write_bytes(original)
    if entrypoint == 'budget-script':
        command = [sys.executable, '-X', 'utf8', 'tools/verification/update-coverage-budget.py',
                   '--suites', str(detector), '--output', str(budget)]
    else:
        command = [sys.executable, '-X', 'utf8', 'tools/mordheim-utils.py', 'coverage-gate',
                   '--suites', str(detector), '--budget', str(budget)]
        if entrypoint == 'gate-update':
            command.append('--update-budget')
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True,
                               encoding='utf-8', timeout=60)
    output = completed.stdout + completed.stderr
    assert 'deliberate detector failure' in output, output
    assert completed.returncode != 0, output
    assert 'pytest exit code 1' in output, output
    assert budget.read_bytes() == original


def test_failed_area_floor_cannot_overwrite_budget(tmp_path):
    from pathlib import Path
    import subprocess
    import sys
    root = Path(__file__).resolve().parents[3]
    detector = tmp_path / 'test_partial_engine_detector.py'
    detector.write_text('def test_detector():\n'
        '    from mordheim_combat.modular.state import FighterState\n'
        '    assert callable(FighterState)\n', encoding='utf-8')
    budget = tmp_path / 'budget.json'
    original = json.dumps(_budget({})).encode('utf-8')
    budget.write_bytes(original)
    completed = subprocess.run([sys.executable, '-X', 'utf8', 'tools/mordheim-utils.py',
        'coverage-gate', '--suites', str(detector), '--budget', str(budget),
        '--update-budget', '--area-floor', 'modular:100'], cwd=root,
        capture_output=True, text=True, encoding='utf-8', timeout=60)
    output = completed.stdout + completed.stderr
    assert '1 passed' in output and 'below the 100.00% floor' in output, output
    assert completed.returncode != 0, output
    assert budget.read_bytes() == original
    assert ' updated' not in output
