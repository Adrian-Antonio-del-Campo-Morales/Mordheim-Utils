"""The desktop executes the generated rules, including pending decisions."""
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
import json
from pathlib import Path
import subprocess

import pytest

from mordheim_construction.eligibility import call

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "tests/fixtures/eligibility/decisions.json").read_text())
RECIPIENT_CASES = json.loads((ROOT / "tests/fixtures/eligibility/entry-recipients.json").read_text())


def codes(result):
    return [issue["code"] for issue in (result if isinstance(result, list) else [result]) if issue]


@pytest.mark.phase2_construction
@pytest.mark.parametrize("case", RECIPIENT_CASES, ids=lambda case: case["name"])
def test_printed_entry_recipients_match_the_direct_typescript_module(case):
    """The transport projects the same offers as `profileFactsProjection`.

    `tests/typescript/domain/shared-eligibility.test.ts` runs the same fixture
    against the maintained module directly.
    """
    facts = call("profileFacts", case["package"], case["profile"], None, {"mappings": {}})
    assert [offer["item_id"] for offer in facts["equipment_access"]] == case["offers"]


@pytest.mark.phase2_construction
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_shared_decisions(case):
    assert codes(call(case["operation"], *case["args"])) == case["codes"]


def _bundle_check(target=None) -> subprocess.CompletedProcess:
    """Run the maintained generator in check mode; it never writes the bundle."""
    command = ["node", str(ROOT / "tools/web/build-eligibility.mjs"), "--check"]
    if target is not None:
        command.append(str(target))
    return subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


@pytest.mark.phase1_kb_contracts
def test_bundle_matches_a_fresh_generation():
    """Compare the checked-in bundle with the real build, not only its banner.

    The banner digest only proves which sources were hashed; a hand-edited body
    can keep it valid. Check mode rebuilds in memory and compares the whole
    artifact, so any divergence fails here.
    """
    result = _bundle_check()
    assert result.returncode == 0, (result.stdout + result.stderr).strip()


@pytest.mark.phase1_kb_contracts
def test_body_only_divergence_fails_without_rewriting_the_checked_file(tmp_path):
    bundle = files("mordheim_construction").joinpath("_eligibility.js").read_text(encoding="utf-8")
    assert "// Source SHA256:" in bundle
    tampered = bundle.replace(
        "\nvar MordheimEligibility",
        "\n// body-only edit; the banner digest is preserved\nvar MordheimEligibility",
        1,
    )
    assert tampered != bundle
    candidate = tmp_path / "_eligibility.js"
    candidate.write_text(tampered, encoding="utf-8", newline="\n")
    result = _bundle_check(candidate)
    assert result.returncode != 0
    assert "stale" in (result.stdout + result.stderr).lower()
    assert candidate.read_text(encoding="utf-8") == tampered


@pytest.mark.phase1_kb_contracts
def test_parallel_desktop_calls_keep_their_own_facts():
    def decide(case):
        return codes(call(case["operation"], *case["args"]))
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(decide, CASES * 3)) == [case["codes"] for case in CASES * 3]


@pytest.mark.phase1_kb_contracts
def test_validation_failure_does_not_poison_the_embedded_runtime():
    package = {"band": {"id": "test"}, "profiles": [], "equipment_lists": [], "special_rules": []}
    catalogue = {"packages": {}, "foreign_packages": {}, "mechanics": {}, "mappings": {}, "skills": {}}
    with pytest.raises(ValueError, match="missing"):
        call("profileEquipment", package, {"id": "hero", "equipment_lists": ["missing"]}, catalogue)
    assert call("skillCategoryAllowed", ["combat"], "combat") is True
