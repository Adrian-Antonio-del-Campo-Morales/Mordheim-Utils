"""Catalogue coverage of the implemented canonical rule families (tooling)."""
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"


@pytest.mark.evidence
def test_first_25_pending_families_moved_to_the_executable_catalogue():
    implemented = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    assert implemented["counts"]["families"] == 66
    assert implemented["counts"]["rules"] == 101


@pytest.mark.evidence
def test_no_scope_yes_rules_remain_without_an_implementation_family():
    implemented = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    assert implemented["counts"] == {"families": 66, "rules": 101, "kinds": {"compiler": 41, "mechanic": 20, "trait": 5}}
