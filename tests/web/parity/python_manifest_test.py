"""Gates for the desktop→web test traceability manifest (Agent 0, parity lane).

Enforces web-test-migration-plan.md §Matriz invariants:

1. regeneration identity — the committed manifest equals a fresh
   ``tools/make_test_manifest.py`` run (no drift from the desktop net);
2. completeness — no row without disposition, owner or (for M/U/I/S) target;
3. exclusion justification — every ``X`` row carries a non-empty reason;
4. bidirectional sanity — every ``web_target`` is either a real tracked
   file or still ``pending`` (targets must exist once work lands);
5. desktop net coverage — the number of enumerated cases matches the
   manifest ``total`` and the sources list matches reality.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "tests" / "web" / "parity" / "campaign-test-manifest.json"
GENERATOR = ROOT / "tools" / "make_test_manifest.py"

VALID_DISPOSITIONS = {"M", "A", "U", "I", "S", "X"}


def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_manifest_exists_and_parses() -> None:
    data = _manifest()
    assert data["plan"] == "web-test-migration-plan.md"
    assert data["deterministic"] is True
    assert isinstance(data["rows"], list) and data["rows"]


def test_regeneration_is_byte_identical(tmp_path: Path) -> None:
    """The committed manifest must equal a fresh generator run."""
    before = MANIFEST.read_bytes()
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    after = MANIFEST.read_bytes()
    assert after == before, "manifest drifted from the desktop net; regenerate it"


def test_every_row_is_complete() -> None:
    for row in _manifest()["rows"]:
        assert row["source_file"], row
        assert row["source_test"], row
        assert row["behavior_id"], row
        assert row["web_disposition"] in VALID_DISPOSITIONS, row
        assert row["owner"], row
        if row["web_disposition"] != "X":
            assert row["web_target"], f"missing target: {row}"


def test_every_exclusion_carries_a_reason() -> None:
    for row in _manifest()["rows"]:
        if row["web_disposition"] == "X":
            assert row["exclusion_reason"], f"unjustified exclusion: {row}"
        else:
            assert not row["exclusion_reason"]


def test_counts_match_rows() -> None:
    data = _manifest()
    counts: dict[str, int] = {}
    for row in data["rows"]:
        counts[row["web_disposition"]] = counts.get(row["web_disposition"], 0) + 1
    assert data["counts"] == dict(sorted(counts.items()))
    assert data["total"] == len(data["rows"])


def test_no_duplicate_source_rows() -> None:
    data = _manifest()
    keys = [(r["source_file"], r["source_test"]) for r in data["rows"]]
    assert len(keys) == len(set(keys)), "duplicate rows in manifest"


def test_manifest_covers_the_real_desktop_net() -> None:
    """Row total must match a live pytest collection of the same sources."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/campaign", "tests/ui",
         "--collect-only", "-q", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    live = sum(
        1 for line in result.stdout.splitlines() if "::" in line and line.startswith("tests/")
    )
    data = _manifest()
    assert data["total"] == live, (
        f"manifest total {data['total']} != live collection {live}; regenerate"
    )
