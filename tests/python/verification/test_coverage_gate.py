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


@pytest.mark.parametrize('entrypoint', ['gate', 'gate-update', 'budget-script'])
def test_real_failing_detector_cannot_pass_gate_or_overwrite_budget(tmp_path, entrypoint):
    from pathlib import Path
    import json
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
    import json
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
