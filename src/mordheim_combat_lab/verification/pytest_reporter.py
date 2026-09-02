"""Internal pytest plugin used by ``mordheim_combat_lab test-report``."""
from __future__ import annotations

import os
from pathlib import Path

from mordheim_combat_lab.verification.test_reporting import TECHNICAL_COLUMNS
from mordheim_combat_lab.verification.test_reporting import write_csv


def pytest_configure(config):
    config._mordheim_report_rows = {}
    pytest_runtest_logreport.rows = config._mordheim_report_rows


def pytest_collection_modifyitems(config, items):
    rows = config._mordheim_report_rows
    for item in items:
        parts = item.nodeid.split("::")
        rows[item.nodeid] = {
            "test_id": item.nodeid, "file": parts[0],
            "class": "::".join(parts[1:-1]), "test": parts[-1],
            "markers": " | ".join(sorted({marker.name for marker in item.iter_markers()})),
            "status": "NOT_RUN", "duration_seconds": 0.0, "error": "", "passes": "NOT_RUN",
        }


def pytest_runtest_logreport(report):
    rows = getattr(pytest_runtest_logreport, "rows", None)
    if rows is None:
        return
    row = rows.get(report.nodeid)
    if row is None:
        return
    row["duration_seconds"] = float(row["duration_seconds"]) + float(report.duration)
    was_xfail = getattr(report, "wasxfail", None)
    if report.skipped:
        row["status"] = "XFAIL" if was_xfail else "SKIP"
        row["passes"] = "PASS"
    elif report.when == "call" and report.passed:
        row["status"] = "XPASS" if was_xfail else "PASS"
        row["passes"] = "FAIL" if was_xfail else "PASS"
    elif report.failed:
        row["status"] = "FAIL" if report.when == "call" else "ERROR"
        row["passes"] = "FAIL"
        row["error"] = str(report.longrepr)


def pytest_runtestloop(session):
    pytest_runtest_logreport.rows = session.config._mordheim_report_rows


def pytest_collectreport(report):
    if not report.failed:
        return
    rows = getattr(pytest_runtest_logreport, "rows", None)
    if rows is None:
        return
    test_id = f"collection/{report.nodeid}"
    rows[test_id] = {
        "test_id": test_id, "file": report.nodeid, "class": "", "test": "collection",
        "markers": "", "status": "ERROR", "duration_seconds": 0.0,
        "error": str(report.longrepr), "passes": "FAIL",
    }


def pytest_sessionfinish(session, exitstatus):
    path = os.environ.get("MORDHEIM_TEST_REPORT_CSV")
    if path:
        rows = session.config._mordheim_report_rows
        if exitstatus and not any(row["status"] in {"FAIL", "ERROR", "XPASS"} for row in rows.values()):
            rows["pytest/session"] = {
                "test_id": "pytest/session", "file": "", "class": "", "test": "session",
                "markers": "", "status": "ERROR", "duration_seconds": 0.0,
                "error": f"pytest exited with status {exitstatus}", "passes": "FAIL",
            }
        write_csv(Path(path), TECHNICAL_COLUMNS, rows.values())
