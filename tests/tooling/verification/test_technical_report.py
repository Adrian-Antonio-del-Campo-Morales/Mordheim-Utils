"""Technical test report: verdicts and report freshness.

The pytest child of ``run_technical_tests`` is always replaced by a stub; no
test suite runs from here.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from mordheim_combat_lab.verification import pytest_reporter
from mordheim_combat_lab.verification import reporting

REPO_ROOT = Path(__file__).resolve().parents[3]


def _row():
    return {"test_id": "t", "status": "NOT_RUN", "duration_seconds": 0.0,
            "error": "", "passes": "NOT_RUN"}


def _report(when="call", outcome="passed", wasxfail=None):
    report = SimpleNamespace(
        nodeid="t", when=when, duration=0.1, longrepr="trace",
        passed=outcome == "passed", skipped=outcome == "skipped",
        failed=outcome == "failed",
    )
    if wasxfail is not None:
        report.wasxfail = wasxfail
    return report


@pytest.mark.parametrize("reports, status, passes", [
    ([_report("setup"), _report(), _report("teardown")], "PASS", "PASS"),
    ([_report("setup", "skipped")], "SKIP", "SKIP"),
    ([_report("setup"), _report("call", "skipped")], "SKIP", "SKIP"),
    ([_report("setup"), _report("call", "skipped", wasxfail="known")], "XFAIL", "XFAIL"),
    ([_report("setup"), _report("call", "passed", wasxfail="known")], "XPASS", "FAIL"),
    ([_report("setup"), _report("call", "failed")], "FAIL", "FAIL"),
    ([_report("setup", "failed")], "ERROR", "FAIL"),
])
def test_skips_and_expected_failures_never_count_as_passes(monkeypatch, reports, status,
                                                           passes):
    rows = {"t": _row()}
    monkeypatch.setattr(pytest_reporter.pytest_runtest_logreport, "rows", rows, raising=False)
    for report in reports:
        pytest_reporter.pytest_runtest_logreport(report)
    assert (rows["t"]["status"], rows["t"]["passes"]) == (status, passes)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream, delimiter=";"))


def _fake_pytest(monkeypatch, *, returncode=0, writes=True, seen=None):
    def fake_run(command, *, env, check, cwd=None):
        if seen is not None:
            seen.update(command=command, env=env, cwd=cwd)
        if writes:
            reporting.write_csv(Path(env["MORDHEIM_TEST_REPORT_CSV"]),
                                reporting.TECHNICAL_COLUMNS,
                                [{"test_id": "fresh", "status": "PASS", "passes": "PASS"}])
        return SimpleNamespace(returncode=returncode)

    monkeypatch.setattr(reporting.subprocess, "run", fake_run)


def _stale(path: Path) -> None:
    reporting.write_csv(path, reporting.TECHNICAL_COLUMNS,
                        [{"test_id": "stale", "status": "PASS", "passes": "PASS"}])
    os.utime(path, (1_000_000_000, 1_000_000_000))


@pytest.mark.parametrize("returncode", [0, 3])
def test_a_stale_csv_is_not_reported_after_a_crash(tmp_path, monkeypatch, returncode):
    path = tmp_path / "technical-tests.csv"
    _stale(path)
    _fake_pytest(monkeypatch, returncode=returncode, writes=False)
    assert reporting.run_technical_tests(path) == (returncode or 1)
    rows = _read(path)
    assert [row["test_id"] for row in rows] == ["pytest/session"]
    assert "did not create its report" in rows[0]["error"]


def test_a_csv_written_by_this_run_is_reported(tmp_path, monkeypatch):
    path = tmp_path / "technical-tests.csv"
    _stale(path)
    _fake_pytest(monkeypatch, returncode=1)
    assert reporting.run_technical_tests(path) == 1
    assert [row["test_id"] for row in _read(path)] == ["fresh"]


def test_an_unremovable_stale_csv_is_still_detected(tmp_path, monkeypatch):
    path = tmp_path / "technical-tests.csv"
    _stale(path)
    original = Path.unlink

    def refuse(self, *args, **kwargs):
        if self == path:
            raise PermissionError("locked")
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", refuse)
    _fake_pytest(monkeypatch, writes=False)
    assert reporting.run_technical_tests(path) == 1
    assert _read(path)[0]["test_id"] == "pytest/session"


def test_the_child_imports_this_checkout(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setenv("PYTHONPATH", "/elsewhere")
    _fake_pytest(monkeypatch, seen=seen)
    assert reporting.run_technical_tests(tmp_path / "technical-tests.csv") == 0
    assert seen["cwd"] == str(REPO_ROOT)
    paths = seen["env"]["PYTHONPATH"].split(os.pathsep)
    assert str(REPO_ROOT / "apps" / "combat-lab") in paths
    assert str(REPO_ROOT / "packages" / "python" / "combat-engine") in paths
    assert paths[-1] == "/elsewhere"
    assert "mordheim_combat_lab.verification.pytest_reporter" in seen["command"]
