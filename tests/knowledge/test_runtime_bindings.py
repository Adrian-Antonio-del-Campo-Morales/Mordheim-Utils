"""Knowledge-base bindings must reference maintained runtime contracts."""
from pathlib import Path

import pytest

from mordheim_combat_lab.verification.structural import (
    _binding_contract_error,
    _catalogue_binding_errors,
)
from mordheim_knowledge.loader import load_bands, load_execution_contract, runtime_bindings

_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[2] / "sources" / "knowledge"


@pytest.mark.evidence
def test_catalogue_audit_rejects_unknown_active_contracts_but_allows_plans(tmp_path):
    import json
    from mordheim_combat_lab.verification.structural import _catalogue_binding_errors

    path = tmp_path / "catalog/skills/test.yaml"
    path.parent.mkdir(parents=True)
    rule = {"id": "skill.test", "runtime": {
        "scope": "YES", "implemented": "YES", "grant": "none",
        "effects": [{"id": "test", "scope": "YES",
                     "binding": {"kind": "mechanic", "id": "skill.known"}}],
    }}

    def errors():
        path.write_text(json.dumps({"skills": [rule]}), encoding="utf-8")
        return _catalogue_binding_errors(tmp_path, {"skill.known"})

    assert errors() == []
    rule["runtime"]["effects"][0]["binding"]["id"] = "skill.missing"
    assert "unknown mechanic binding skill.missing" in errors()[0]
    rule["runtime"]["implemented"] = "NO"
    assert errors() == []
    rule["runtime"]["scope"] = "LATER"
    rule["runtime"]["effects"][0]["scope"] = "LATER"
    rule["runtime"]["implemented"] = "YES"
    assert "active binding requires scope YES" in errors()[0]
    rule["runtime"]["scope"] = "YES"
    rule["runtime"]["effects"][0]["scope"] = "YES"
    rule["runtime"]["effects"][0]["binding"] = {
        "kind": "compiler", "id": "special-rule.banshee--cold-steel",
    }
    assert errors() == []
    rule["runtime"]["effects"][0]["binding"]["id"] = "special-rule.unknown-profile-rule"
    assert "unknown compiler binding" in errors()[0]


@pytest.mark.evidence
def test_in_scope_knowledge_rules_have_known_bindings():
    execution_ids = {
        str(row.get("id") or "")
        for row in load_execution_contract("mordheim", _KNOWLEDGE_ROOT).get("mechanics") or ()
    }
    errors = []
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection, _KNOWLEDGE_ROOT):
            for rule in band.special_rules:
                runtime = rule.get("runtime") or {}
                if runtime.get("scope") != "YES":
                    continue
                bindings = runtime_bindings(rule, include_pending=True)
                if not bindings:
                    errors.append(f"{band.band['id']}/{rule['id']}: scope YES rule has no binding")
                for binding in bindings:
                    error = _binding_contract_error(binding, execution_ids)
                    if error:
                        errors.append(f"{rule['id']}: {error}")
    errors.extend(_catalogue_binding_errors(_KNOWLEDGE_ROOT, execution_ids))
    assert errors == []
