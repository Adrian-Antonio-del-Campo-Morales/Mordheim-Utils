"""Export contract for the precompiled corpus (T03).

Reproducibility, provenance, refusal of prose and conservation of explicitly
declared expectations.  Engine output is never an input here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from tools.knowledge.export_compiled_cases import ExportError
from tools.knowledge.export_compiled_cases import export_cases
from tools.verification.compiled_cases import load_cases

pytestmark = pytest.mark.phase2_construction


def _fighter(fighter_id: str) -> CompiledFighter:
    return CompiledFighter(
        fighter_id=fighter_id,
        characteristics=Characteristics(3, 3, 3, 3, 3, 1),
        main_weapon=EffectSet(),
        off_hand=None,
        global_effects=EffectSet(),
        armour_save=7,
        helmet_save=7,
        natural_armour_save=7,
    )


def _plan(tmp_path: Path, **overrides) -> dict:
    (tmp_path / "knowledge").mkdir(exist_ok=True)
    (tmp_path / "source.txt").write_text("reviewed source\n", encoding="utf-8")
    case = {
        "case_key": "unit/shared/example",
        "origin": {
            "kind": "unit",
            "node_id": "tests/rules/construction/example.py::test_example",
            "path": "source.txt",
        },
        "fighters": {"first": _fighter("first"), "second": _fighter("second")},
        "expect_error": "reviewed refusal",
        "limits": {"maximum_rounds": 2},
    }
    case.update(overrides)
    return {"revision": "deadbeef", "cases": [case]}


def test_export_is_reproducible_and_loadable(tmp_path):
    plan = _plan(tmp_path)
    first = export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "a.json")
    second = export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "b.json")
    assert (tmp_path / "a.json").read_bytes() == (tmp_path / "b.json").read_bytes()
    assert first.corpus_sha256 == second.corpus_sha256
    loaded = load_cases(tmp_path / "a.json")
    assert list(loaded) == ["unit/shared/example"]
    assert first.case_count == 1


def test_origin_and_source_fingerprints_are_traceable(tmp_path):
    plan = _plan(tmp_path)
    plan["files"] = ["source.txt"]
    receipt = export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "cases.json")
    document = json.loads((tmp_path / "cases.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256((tmp_path / "source.txt").read_bytes()).hexdigest()
    assert document["source"] == {
        "revision": "deadbeef",
        "kb_root": "knowledge",
        "files": [{"path": "source.txt", "sha256": digest}],
    }
    assert document["cases"][0]["origin"]["sha256"] == digest
    assert receipt.case_hashes["unit/shared/example"] == document["cases"][0]["fingerprints"]["case_sha256"]


def test_expectations_are_copied_only_when_declared(tmp_path):
    plan = _plan(tmp_path)
    case = plan["cases"][0]
    export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "cases.json")
    declared = load_cases(tmp_path / "cases.json")["unit/shared/example"]
    assert declared.expectations == {"expect_error": "reviewed refusal"}
    del case["expect_error"]
    export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "empty.json")
    assert load_cases(tmp_path / "empty.json")["unit/shared/example"].expectations is None


def test_prose_and_duplicate_keys_are_refused(tmp_path):
    plan = _plan(tmp_path, description="engine output can never be a fixture")
    with pytest.raises(ExportError, match="prose"):
        export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "cases.json")
    plan = _plan(tmp_path)
    plan["cases"].append(dict(plan["cases"][0]))
    with pytest.raises(ExportError, match="duplicate case_key"):
        export_cases(plan, kb_root=tmp_path / "knowledge", destination=tmp_path / "cases.json")
    assert not (tmp_path / "cases.json").exists()
