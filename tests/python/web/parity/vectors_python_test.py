"""Python runner for the shared malformed-save parity vectors.

Each vector = one JSON-pointer mutation on a schema-valid v5 fixture. Both
toolchains apply the same mutation and must agree on the outcome
(``reject`` = CampaignFileError / adapter error, ``accept`` = clean load).

The TypeScript mirror is ``tests/typescript/parity-vectors.test.ts``.
Vector files are the contract; runner mistakes must fail here, not bend
expectations.
"""

from __future__ import annotations

import copy
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
VECTORS = ROOT / "tests" / "fixtures" / "parity" / "vectors"
FIXTURES = ROOT / "contracts" / "campaign-file-v5" / "fixtures"
MANIFEST = ROOT / "outputs" / "parity" / "test-manifests" / "campaign-test-manifest.json"
MANIFEST_GENERATOR = ROOT / "tools" / "verification" / "make_test_manifest.py"

sys.path.insert(0, str(ROOT / "packages" / "python" / "campaign"))
sys.path.insert(0, str(ROOT / "packages" / "python" / "knowledge"))
sys.path.insert(0, str(ROOT / "packages" / "python" / "core"))
sys.path.insert(0, str(ROOT / "packages" / "python" / "adapters" / "desktop-ui"))

from mordheim_campaign.persistence import (  # noqa: E402
    CampaignFileError,
    load_campaign,
)

DATA = json.loads((VECTORS / "malformed_save.json").read_text(encoding="utf-8"))
VECTORS_LIST = DATA["vectors"]


def _base_document(base: str) -> dict:
    doc = json.loads((FIXTURES / base).read_text(encoding="utf-8"))
    doc.pop("view", None)
    return doc


def _pointer_parts(pointer: str) -> list[str]:
    return [p.replace("~1", "/").replace("~0", "~") for p in pointer.split("/")[1:]]


def _apply(doc: dict, vector: dict) -> dict:
    doc = copy.deepcopy(doc)
    op = vector.get("mutation", {}).get("op", "set")
    if op == "set":
        parts = _pointer_parts(vector["pointer"])
        node = doc
        for part in parts[:-1]:
            node = node[int(part)] if isinstance(node, list) else node[part]
        last = parts[-1]
        if isinstance(node, list):
            node[int(last)] = vector["value"]
        else:
            node[last] = vector["value"]
        return doc
    if op == "set_with_state":
        # rebuild states[0] as a committed roster snapshot containing the bad value
        value = vector["value"]
        roster = copy.deepcopy(doc["campaign"]["warriors"])
        for w in roster:
            for eq in w.get("equipment", []):
                eq["quantity"] = value
        doc["campaign"]["states"] = [{"number": 0, "roster": roster}]
        return doc
    if op == "set_nonfinite":
        doc["campaign"]["starting_gold"] = math.inf
        return doc
    if op in {"duplicate_followup", "orphan_advance", "duplicate_advance", "completed_advance_for_lost_warrior"}:
        # the incomplete (complete=false) post-battle is the LAST row in the
        # fixtures — mutations must land there or the validator ignores them
        pending = doc["campaign"]["post_battles"][-1]
    if op == "duplicate_followup":
        wid = vector["mutation"]["warrior_id"]
        pending["pending_follow_ups"] = [
            {"id": "same", "step": 0, "type": "prisoner", "warrior_id": wid},
            {"id": "same", "step": 0, "type": "prisoner", "warrior_id": wid},
        ]
        return doc
    if op == "orphan_advance":
        pending["pending_advances"] = [
            {"warrior_id": "absent-warrior", "threshold": 20, "table": "hero", "committed": False}
        ]
        return doc
    if op == "duplicate_advance":
        advance = {
            "warrior_id": vector["mutation"]["warrior_id"],
            "threshold": 20,
            "table": "hero",
            "committed": False,
        }
        pending["pending_advances"] = [advance, dict(advance)]
        return doc
    if op == "completed_advance_for_lost_warrior":
        pending["pending_advances"] = [
            {"warrior_id": "lost-warrior", "threshold": 20, "table": "hero", "committed": True}
        ]
        return doc
    raise AssertionError(f"unknown mutation op: {op}")


@pytest.mark.parametrize("vector", VECTORS_LIST, ids=lambda v: v["id"])
def test_parity_vector(vector, tmp_path: Path) -> None:
    doc = _apply(_base_document(vector["base"]), vector)
    path = tmp_path / "vector.mordheim"
    path.write_text(json.dumps(doc, allow_nan=True), encoding="utf-8")
    if vector["expected"] == "reject":
        with pytest.raises(CampaignFileError):
            load_campaign(path)
    else:
        restored = load_campaign(path)
        assert restored.campaign is not None


def test_vector_ids_unique_and_counted() -> None:
    ids = [v["id"] for v in VECTORS_LIST]
    assert len(ids) == len(set(ids))
    subprocess.run([sys.executable, str(MANIFEST_GENERATOR)], cwd=ROOT, check=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["counts"].get("S", 0) >= len(VECTORS_LIST), (
        "manifest S count fell below the delivered malformed_save vectors"
    )
