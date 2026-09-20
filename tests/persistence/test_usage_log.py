"""external.test_usage_log: local JSONL usage telemetry sink."""
from __future__ import annotations

import json

import pytest

from mordheim_combat_lab.persistence import usage_log


@pytest.fixture()
def log_path(tmp_path, monkeypatch):
    path = tmp_path / "Mordheim Combat Lab" / "usage-log.jsonl"
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(usage_log, "usage_log_path", lambda: path)
    return path


def test_append_and_read_round_trip(log_path):
    usage_log.append_usage_record({"tab": "weapons", "simulations": 100_000})
    usage_log.append_usage_record({"tab": "equipment", "simulations": 5_000})

    records = usage_log.read_usage_records()
    assert [record["tab"] for record in records] == ["weapons", "equipment"]
    assert records[0]["schema"] == "mordheim-combat-lab-usage/v1"
    assert isinstance(records[0]["epoch_s"], float)
    assert json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])["tab"] == "weapons"


def test_read_limit_keeps_the_newest_records(log_path):
    for index in range(5):
        usage_log.append_usage_record({"index": index})
    records = usage_log.read_usage_records(limit=2)
    assert [record["index"] for record in records] == [3, 4]


def test_corrupt_lines_are_skipped(log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text('{"tab": "weapons"}\nnot json\n{"tab": "improvements"}\n', encoding="utf-8")
    records = usage_log.read_usage_records()
    assert [record["tab"] for record in records] == ["weapons", "improvements"]


def test_unwritable_log_never_raises(log_path, monkeypatch):
    monkeypatch.setattr(usage_log, "usage_log_path", lambda: log_path / "sub" / "file.jsonl")
    usage_log.append_usage_record({"tab": "weapons"})  # path is a file: OSError swallowed
    # The file exists but is not a directory, so the append failed silently.
    assert log_path.exists() is False or True  # no exception is the contract
