from __future__ import annotations

import csv
import os
from pathlib import Path
import subprocess
import sys

from mordheim_combat_lab.verification.test_reporting import SEMANTIC_COLUMNS
from mordheim_combat_lab.verification.test_reporting import TECHNICAL_COLUMNS
from mordheim_combat_lab.verification.test_reporting import _overall
from mordheim_combat_lab.verification.test_reporting import generate_test_report
from mordheim_combat_lab.verification.test_reporting import semantic_report_rows
from mordheim_combat_lab.verification.test_reporting import write_csv


def test_semantic_csv_inventory_is_human_readable_and_complete():
    rows = semantic_report_rows()
    assert len(rows) == 3347
    assert len({row["test_id"] for row in rows}) == len(rows)
    assert not [row for row in rows if row["passes"] == "FAIL"]
    assert {row["passes"] for row in rows} == {"PASS", "PENDING"}
    assert any(row["numpy_status"] == "PASS" for row in rows)
    assert not any(row["numpy_status"] == "PENDING_ADAPTER" for row in rows)
    assert any(row["numpy_status"] == "PENDING_SEMANTIC" for row in rows)
    from mordheim_combat.vectorized import available_backends

    native_present = "native" in available_backends()
    if native_present:
        # Per-operator rows are not applicable to a duel-level engine; its
        # certification appears on the duel-level (statistical) rows.
        assert any(row["native_status"] == "NOT_APPLICABLE" for row in rows)
        assert not any(row["native_status"] == "NOT_AVAILABLE" for row in rows)
        assert not any(row["native_status"] == "PENDING_ADAPTER" for row in rows)
    else:
        assert any(row["native_status"] == "NOT_AVAILABLE" for row in rows)


def test_csv_uses_excel_friendly_bom_semicolons_and_unicode(tmp_path):
    path = tmp_path / "report.csv"
    write_csv(path, SEMANTIC_COLUMNS, ({
        "test_id": "regla/ñ", "details": "+Parada\ncon héroe",
        "expected": '{"resultado":"éxito"}', "passes": "PASS",
    },))
    raw = path.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf")
    assert b";" in raw
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = tuple(csv.DictReader(stream, delimiter=";"))
    assert rows[0]["details"] == "'+Parada con héroe"
    assert len(raw.splitlines()) == 2


def test_semantic_columns_put_engine_results_and_statuses_side_by_side():
    assert SEMANTIC_COLUMNS == (
        "test_id", "category", "operation", "rules", "expected",
        "modular_result", "numpy_result", "native_result",
        "modular_status", "numpy_status", "native_status", "passes", "details",
    )


def test_overall_status_distinguishes_fail_pending_and_scope():
    assert _overall("PASS", "PASS_SHARED") == "PASS"
    assert _overall("PASS", "NOT_AVAILABLE") == "PENDING"
    assert _overall("PASS", "DIVERGENCE") == "FAIL"
    assert _overall("OUT_OF_SCOPE", "OUT_OF_SCOPE") == "OUT_OF_SCOPE"


def test_both_reports_survive_a_semantic_generation_failure(tmp_path, monkeypatch):
    import mordheim_combat_lab.verification.test_reporting as reporting

    monkeypatch.setattr(reporting, "semantic_report_rows", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    def technical(path):
        write_csv(path, TECHNICAL_COLUMNS, ({"test_id": "sample", "status": "PASS", "passes": "PASS"},))
        return 0
    monkeypatch.setattr(reporting, "run_technical_tests", technical)
    semantic, technical_path, rows, exit_code = generate_test_report(tmp_path)
    assert semantic.is_file() and technical_path.is_file()
    assert rows[0]["passes"] == "FAIL"
    assert exit_code == 0


def test_internal_pytest_plugin_records_parametrized_skipped_and_xfail(tmp_path):
    suite = tmp_path / "test_sample.py"
    suite.write_text(
        "import pytest\n"
        "@pytest.mark.parametrize('value', [1, 2])\n"
        "def test_parameter(value): assert value > 0\n"
        "@pytest.mark.skip(reason='sample')\n"
        "def test_skip(): pass\n"
        "@pytest.mark.xfail(reason='sample')\n"
        "def test_xfail(): assert False\n",
        encoding="utf-8",
    )
    report = tmp_path / "technical.csv"
    environment = dict(os.environ)
    environment["MORDHEIM_TEST_REPORT_CSV"] = str(report)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p",
         "mordheim_combat_lab.verification.pytest_reporter", "-p", "no:cacheprovider",
         "--rootdir", str(tmp_path), str(suite)],
        env=environment, cwd=tmp_path, check=False, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    with report.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = tuple(csv.DictReader(stream, delimiter=";"))
    assert len(rows) == 4
    assert {row["status"] for row in rows} == {"PASS", "SKIP", "XFAIL"}
    assert sum(row["status"] == "PASS" for row in rows) == 2
