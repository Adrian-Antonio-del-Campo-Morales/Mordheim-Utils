"""The desktop executes the generated rules, including pending decisions."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from importlib.resources import files
import json
from pathlib import Path

import pytest

from mordheim_construction.eligibility import call

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "tests/fixtures/eligibility/decisions.json").read_text())
RECIPIENT_CASES = json.loads((ROOT / "tests/fixtures/eligibility/entry-recipients.json").read_text())


def codes(result):
    return [issue["code"] for issue in (result if isinstance(result, list) else [result]) if issue]


@pytest.mark.parametrize("case", RECIPIENT_CASES, ids=lambda case: case["name"])
def test_printed_entry_recipients_match_the_direct_typescript_module(case):
    """The transport projects the same offers as `profileFactsProjection`.

    `tests/typescript/domain/shared-eligibility.test.ts` runs the same fixture
    against the maintained module directly.
    """
    facts = call("profileFacts", case["package"], case["profile"], None, {"mappings": {}})
    assert [offer["item_id"] for offer in facts["equipment_access"]] == case["offers"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_shared_decisions(case):
    assert codes(call(case["operation"], *case["args"])) == case["codes"]


def test_bundle_matches_maintained_sources():
    source = ROOT / "packages/typescript/domain/eligibility"
    digest = sha256("".join((source / name).read_text(encoding="utf-8") for name in ("index.ts", "bridge.ts")).encode()).hexdigest()
    bundle = files("mordheim_construction").joinpath("_eligibility.js").read_text(encoding="utf-8")
    assert f"// Source SHA256: {digest}" in bundle, "Run npm run build:eligibility"


def test_parallel_desktop_calls_keep_their_own_facts():
    def decide(case):
        return codes(call(case["operation"], *case["args"]))
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(decide, CASES * 3)) == [case["codes"] for case in CASES * 3]


def test_validation_failure_does_not_poison_the_embedded_runtime():
    package = {"band": {"id": "test"}, "profiles": [], "equipment_lists": [], "special_rules": []}
    catalogue = {"packages": {}, "foreign_packages": {}, "mechanics": {}, "mappings": {}, "skills": {}}
    with pytest.raises(ValueError, match="missing"):
        call("profileEquipment", package, {"id": "hero", "equipment_lists": ["missing"]}, catalogue)
    assert call("skillCategoryAllowed", ["combat"], "combat") is True
