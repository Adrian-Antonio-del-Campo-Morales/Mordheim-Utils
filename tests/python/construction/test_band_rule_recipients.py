"""T13-F017 — automatic band grants must honour their recipient filters.

Shared contract cases run through the real embedded runtime; the canonical
adventurers-kaz tables are read live from the KB and checked through both the
embedded runtime and the maintained ``selection._applicable_rules`` route.
Expectations come from the canonical YAML and the accepted F035 register.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mordheim_construction.eligibility import call, package_facts
from mordheim_construction.selection import _applicable_rules
from mordheim_knowledge.loader import load_bands

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "tests/fixtures/eligibility/band-rule-recipients.json").read_text(encoding="utf-8"))["cases"]
PACK = next(pack for pack in load_bands("mordheim", ROOT / "sources" / "knowledge")
            if str(pack.band["id"]) == "adventurers-kaz")
TABLES = {
    "band--dwarf-special-skills": "dwarf",
    "band--elf-special-skills": "elf",
    "band--barbarian-special-skills": "barbarian",
    "band--noble-special-skills": "imperial-noble",
}
BAND_WIDE = ("band--no-fixed-leader", "band--hired-swords")
PROFILE_IDS = [str(profile["id"]) for profile in PACK.profiles]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_shared_contract_cases_through_embedded_runtime(case):
    rows = call("applicableRules", case["package"], case["profile"])
    assert [str(row["id"]) for row in rows] == case["expected_rule_ids"]


def assert_canonical_recipients(profile_id, rule_ids):
    applied = {rule_id for rule_id, recipient in TABLES.items() if recipient == profile_id}
    assert set(rule_ids) & set(TABLES) == applied, profile_id
    assert set(BAND_WIDE) <= set(rule_ids), profile_id
    assert ("dwarf--hard-to-kill" in rule_ids) == (profile_id == "dwarf"), profile_id
    assert len(rule_ids) == len(set(rule_ids)), profile_id


@pytest.mark.parametrize("profile_id", PROFILE_IDS)
def test_canonical_recipients_through_embedded_runtime(profile_id):
    rows = call("applicableRules", package_facts(PACK), {"id": profile_id})
    assert_canonical_recipients(profile_id, [str(row["id"]) for row in rows])


@pytest.mark.parametrize("profile_id", PROFILE_IDS)
def test_canonical_recipients_through_maintained_selection(profile_id):
    rule_ids = [str(rule["id"]) for rule in _applicable_rules(PACK, {"id": profile_id})]
    assert_canonical_recipients(profile_id, rule_ids)
    if profile_id == "dwarf":
        # Profile-branch rules precede the band additions and the profile's
        # explicit rule_ids reference is not duplicated.
        assert rule_ids.index("dwarf--hard-to-kill") < rule_ids.index("band--dwarf-special-skills")
