"""Contract of the generated audit report."""
from csv import DictReader, DictWriter
from dataclasses import fields, replace
from types import SimpleNamespace
import json

from mordheim_combat_lab.verification.audit_export import AuditRow
from mordheim_combat_lab.verification.audit_export import build_audit_rows
from mordheim_combat_lab.verification.audit_export import combat_audit_rows
from mordheim_combat_lab.verification.audit_export import filter_audit_rows
from mordheim_combat_lab.verification.audit_export import write_csv
from mordheim_combat_lab.verification.inventory import inventory
import pytest


@pytest.mark.parametrize("question,ruling,verified,dependencies,expected", [
    ("How does it combine?", "", False, (), "needs_ruling"),
    ("How does it combine?", "", False, ("missing",), "needs_ruling"),
    ("How does it combine?", "It adds up, per the source.", False, (), "ready"),
    ("How does it combine?", "It adds up, per the source.", True, (), "verified"),
    ("How does it combine?", "It adds up, per the source.", False, ("missing",), "blocked_by_dependency"),
    ("", "", False, (), "ready"),
])
def test_review_keeps_history_separate_from_verification(
    tmp_path, monkeypatch, question, ruling, verified, dependencies, expected,
):
    from mordheim_combat_lab.verification import audit_export, specifications
    target = "mechanic/weapon.example"
    report = SimpleNamespace(
        obligations=[SimpleNamespace(id=target, binding="bound", dependencies=dependencies)],
        verified=[target] if verified else [], fixtures=[], verified_interactions=[],
        pending=[] if verified else [(target, "Pending work, not a question.")],
    )
    monkeypatch.setattr(audit_export, "verify_semantics", lambda *args: report)
    monkeypatch.setattr(audit_export, "read_yaml", lambda path: {
        "weapons": [{"id": "weapon.example"}],
    } if path.name == "close-combat.yaml" else {})
    monkeypatch.setattr(specifications, "load_fixtures", lambda *args: [{
        "sources": [{"target": target}], "question": question, "ruling": ruling,
        "interpretation": "Description of the specification, not a decision.",
    }])
    row, = build_audit_rows(tmp_path)
    assert row.review_status == expected
    assert row.question == question
    assert row.ruling == ruling
    assert row.interpretation != row.ruling
    assert (row.semantic_status == "verified") is verified


@pytest.mark.parametrize("metadata,valid", [
    ({"question": "What value?", "pending": "Missing answer"}, True),
    ({"question": "What value?", "ruling": "The value is 4."}, True),
    ({"question": "What value?"}, False),
    ({"question": " "}, False),
    ({"ruling": 4}, False),
])
def test_review_metadata_validation(tmp_path, metadata, valid):
    from mordheim_combat_lab.verification.specifications import load_fixtures
    directory = tmp_path / "semantic"
    directory.mkdir()
    (directory / "example.yaml").write_text(json.dumps({
        "schema_version": 1, "specifications": [{"id": "example", **metadata}],
    }), encoding="utf-8")
    if valid:
        assert load_fixtures(tmp_path)[0]["question"] == metadata["question"]
    else:
        with pytest.raises(ValueError):
            load_fixtures(tmp_path)


@pytest.mark.parametrize("scope,review_status", [
    ("YES", "needs_ruling"), ("UNCLASSIFIED", "needs_classification"),
])
def test_cli_forwards_review_filter(monkeypatch, tmp_path, capsys, scope, review_status):
    from mordheim_combat_lab.cli.commands import main
    from mordheim_combat_lab.verification import audit_export
    captured = {}
    def generate(**kwargs):
        captured.update(kwargs)
        return tmp_path / "combat-audit.csv", tmp_path / "rules-audit.csv"
    monkeypatch.setattr(audit_export, "generate_audit", generate)
    assert main(["audit", "--review-status", review_status, "--scope", scope]) == 0
    assert captured["review_status"] == review_status
    assert captured["scope"] == scope
    assert capsys.readouterr().out.splitlines() == [
        str((tmp_path / name).resolve()) for name in ("combat-audit.csv", "rules-audit.csv")
    ]


@pytest.mark.parametrize("runtime,scope,semantic,review", [
    ({}, "UNCLASSIFIED", "unclassified", "needs_classification"),
    ({"effects": [{"id": "effect", "binding": None}]},
     "UNCLASSIFIED", "unclassified", "needs_classification"),
    ({"scope": "NO", "reason": "Campaign only."}, "NO", "out_of_scope", "not_applicable"),
    ({"scope": "LATER", "reason": "Deferred."}, "LATER", "deferred", "deferred"),
    ({"scope": "YES"}, "YES", "pending", "ready"),
])
def test_missing_classification_is_not_an_exclusion(tmp_path, monkeypatch, runtime, scope, semantic, review):
    from mordheim_combat_lab.verification import audit_export, specifications
    path = tmp_path / "catalog/skills/warband.yaml"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"skills": [{"id": "skill.example", "runtime": runtime}]}))
    read_yaml = audit_export.read_yaml
    monkeypatch.setattr(audit_export, "read_yaml", lambda candidate: read_yaml(candidate) if candidate == path else {})
    monkeypatch.setattr(audit_export, "verify_semantics", lambda *args: SimpleNamespace(
        obligations=[], verified=[], fixtures=[], verified_interactions=[], pending=[],
    ))
    monkeypatch.setattr(specifications, "load_fixtures", lambda *args: [])
    row, = build_audit_rows(tmp_path)
    assert (row.scope, row.semantic_status, row.review_status) == (scope, semantic, review)
    if scope == "UNCLASSIFIED":
        assert row.structural_status == "unclassified"
        assert row.implemented == "UNKNOWN"
        assert "Exclusion" not in row.scope_reason
    else:
        assert row.implemented == "NO"


@pytest.fixture(scope="module")
def audit_rows():
    return build_audit_rows()


def test_audit_covers_every_scope_class_and_matches_semantic_inventory(audit_rows):
    included = [row for row in audit_rows if row.scope == "YES" and row.scope_basis == "kb"
                and row.kind not in {"item_effect", "source_effect"}]
    assert {row.id for row in included} == {item.id for item in inventory()}
    semantic_statuses = {row.semantic_status for row in included}
    assert semantic_statuses <= {"verified", "pending"}
    assert all(row.semantic_status == "out_of_scope" for row in audit_rows if row.scope == "NO")
    assert all(row.scope_reason for row in audit_rows if row.scope != "YES")
    assert all(row.review_status == "not_applicable" for row in audit_rows if row.scope == "NO")
    unclassified = filter_audit_rows(audit_rows, scope="UNCLASSIFIED", status="unclassified",
                                     review_status="needs_classification")
    assert unclassified
    tough = next(row for row in audit_rows if row.id == "rule/catalog/warband/skill.tough-as-steel/unclassified")
    assert tough.scope == "YES" and tough.scope_basis == "reviewed_source"
    assert tough.implemented == "UNKNOWN" and tough.semantic_status == "pending"
    assert len({row.id for row in audit_rows}) == len(audit_rows)


def test_audit_filters_are_composable(audit_rows):
    for status in {row.semantic_status for row in audit_rows if row.scope == "YES"}:
        selected = filter_audit_rows(audit_rows, scope="YES", status=status)
        assert selected
        assert all(row.scope == "YES" and row.semantic_status == status for row in selected)
        for review in {row.review_status for row in selected}:
            reviewed = filter_audit_rows(audit_rows, scope="YES", status=status, review_status=review)
            assert reviewed
            assert all(row.review_status == review for row in reviewed)


def test_resolved_real_question_is_preserved_regardless_of_current_verification(audit_rows):
    row = next(row for row in audit_rows if row.id == "mechanic/skill.swordmaster")
    assert row.question and row.ruling
    assert (row.review_status == "verified") == (row.semantic_status == "verified")


def test_pending_reason_exposes_stale_scope_evidence():
    from mordheim_combat_lab.verification.audit_export import _scenario_evidence
    report = SimpleNamespace(pending=[("mechanic/example", "Incomplete evidence")],
                             fixtures=[SimpleNamespace(id="spec-example", targets=("mechanic/example",),
                                                       errors=("scope changed or scope review missing",))],
                             verified_interactions=[])
    _, _, pending = _scenario_evidence(report)
    assert "spec-example: scope changed or scope review missing" in pending["mechanic/example"]


def test_audit_writer_creates_excel_friendly_csv(tmp_path):
    row = AuditRow(
        "rule/example", "editorial_effect", "Rule <example>", "rules.yaml", "Section", "",
        "YES", "", "YES", '{"id": "example"}', "linked", "verified", "", "scenario-1",
        "", "Answer, with grounds", "verified", "First line?\nSecond?", "General interpretation",
    )
    csv_path = tmp_path / "audit.csv"
    write_csv((row,), csv_path)
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        parsed = list(DictReader(stream))
    assert list(parsed[0]) == [field.name for field in fields(AuditRow)]
    assert parsed[0]["name"] == "Rule <example>"
    assert parsed[0]["question"] == "First line? Second?"
    assert parsed[0]["ruling"] == row.ruling
    assert parsed[0]["review_status"] == "verified"
    assert len(csv_path.read_text(encoding="utf-8-sig").splitlines()) == 2


@pytest.mark.parametrize("custom_output", [False, True])
def test_separate_reports_preserve_every_filtered_row(tmp_path, monkeypatch, audit_rows, custom_output):
    from mordheim_combat_lab.verification import audit_export
    monkeypatch.setattr(audit_export, "build_audit_rows", lambda *args: audit_rows)
    monkeypatch.setattr(audit_export, "project_root", lambda: tmp_path)
    output = tmp_path / "custom" if custom_output else None
    for scope in (None, "UNCLASSIFIED"):
        combat_path, rules_path = audit_export.generate_audit(output=output, scope=scope)
        with combat_path.open(encoding="utf-8-sig", newline="") as stream:
            combat = list(DictReader(stream))
        with rules_path.open(encoding="utf-8-sig", newline="") as stream:
            rules = list(DictReader(stream))
        assert {row["id"] for row in combat} == {row.id for row in filter_audit_rows(audit_rows, scope=scope)}
        assert all(row["kind"] in {"editorial_effect", "item_effect", "source_effect"} for row in rules)
        expected = filter_audit_rows(audit_rows, scope=scope)
        included_effects = {row.id for row in expected if row.kind in {"editorial_effect", "item_effect", "source_effect"}}
        assert {row["id"] for row in combat} & {row["id"] for row in rules} == included_effects
        assert len(combat) + len(rules) - len(included_effects) == len(expected)
        assert {row["id"] for row in combat + rules} == {row.id for row in expected}
        assert rules_path.name == combat_path.name.replace("combat-audit", "rules-audit", 1)
        if custom_output:
            assert combat_path.name == "combat-audit.csv"
        else:
            assert combat_path.name.startswith("combat-audit-")


def test_combat_report_keeps_pending_editorial_and_historical_t13_work(tmp_path):
    included = AuditRow(
        "rule/example/included", "editorial_effect", "Included effect", "rules.yaml", "", "",
        "YES", "", "NO", "unbound", "unbound", "pending", "Not implemented", "", "", "",
    )
    deferred = replace(included, id="rule/example/deferred", scope="LATER",
                       semantic_status="out_of_scope", review_status="not_applicable")
    excluded = replace(deferred, id="rule/example/excluded", scope="NO")
    unrelated = replace(excluded, id="rule/example/campaign")
    plan = tmp_path / "origins.csv"
    with plan.open("w", encoding="utf-8", newline="") as stream:
        writer = DictWriter(stream, fieldnames=["origin_key", "disposition", "existing_audit_status",
                                               "canonical_id", "canonical_file", "source_question", "lots", "question_id",
                                               "family", "clause_summary"])
        writer.writeheader()
        for origin, target, disposition in (("deferred", deferred.id, "included"),
                                             ("excluded", excluded.id, "mixed"),
                                             ("missing", "rule/removed", "source-blocked"),
                                             ("campaign", unrelated.id, "campaign")):
            writer.writerow(dict(origin_key=origin, disposition=disposition,
                                 existing_audit_status=json.dumps([{"id": target}]),
                                 canonical_id="source-rule", canonical_file="rules.yaml",
                                 source_question="Which recipient?", lots='["T13.5"]', question_id="Q1",
                                 family="band-rule", clause_summary="Individual combat effect"))
    rows = {row.id: row for row in combat_audit_rows((included, deferred, excluded, unrelated), plan)}
    assert set(rows) == {included.id, deferred.id, excluded.id, unrelated.id, "planning/missing"}
    assert rows[included.id].combat_work_status == "implementation_required"
    for original in (deferred, excluded):
        row = rows[original.id]
        assert (row.scope, row.implemented, row.semantic_status) == (
            original.scope, original.implemented, original.semantic_status,
        )
        assert row.combat_work_status == ("excluded" if row.scope == "NO" else "deferred_scope_review")
        assert row.t13_origin and row.t13_lots
    missing = rows["planning/missing"]
    assert missing.combat_work_status == "needs_target_reconciliation"
    assert missing.implemented == "UNKNOWN" and missing.t13_question_id == "Q1"


def test_item_effects_keep_mapping_scope_and_text_without_inventing_verification(tmp_path, monkeypatch):
    from mordheim_combat_lab.verification import audit_export, specifications
    documents = {
        "registry/runtime-scope.yaml": {},
        "catalog/mechanics/close-combat.yaml": {"weapons": [{"id": "weapon.base", "engine_option": "Base"}]},
        "catalog/mechanics/simulation-mappings.yaml": {"item_mappings": [{"item_id": "alias", "status": "implemented", "engine_option": "Base"}]},
        "catalog/items/items.yaml": {"items": [
            {"id": "alias", "effect": "Parry one hit"},
            {"id": "excluded", "combat_status": "out_of_scope", "combat_reason": "Missile attacks only"},
            {"id": "unclassified", "effect": "Unreviewed printed effect"},
        ]},
        "catalog/hirelings/rules.yaml": {"rules": [{"id": "hireling.rule", "effect": "Extra attack"}]},
        "catalog/campaign/mutations.yaml": {"mutations": [{"id": "mutation.test", "effect": "Natural armour", "source": "Rulebook"}]},
    }
    for relative, document in documents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
    monkeypatch.setattr(audit_export, "verify_semantics", lambda *args: SimpleNamespace(
        obligations=[], verified=[], fixtures=[], verified_interactions=[], pending=[],
    ))
    monkeypatch.setattr(specifications, "load_fixtures", lambda *args: [])
    rows = {row.id: row for row in build_audit_rows(tmp_path)}
    alias = rows["item/alias"]
    assert alias.scope == "YES" and alias.implemented == "YES"
    assert json.loads(alias.binding)["id"] == "weapon.base"
    assert alias.effect_text == "Parry one hit" and alias.semantic_status == "pending"
    assert rows["item/excluded"].scope_reason == "Missile attacks only"
    assert rows["item/unclassified"].implemented == "UNKNOWN"
    hireling = rows["source/catalog/hirelings/rules.yaml/hireling.rule/unclassified"]
    mutation = rows["source/catalog/campaign/mutations.yaml/mutation.test/unclassified"]
    assert hireling.effect_text == "Extra attack" and mutation.effect_text == "Natural armour"
    assert hireling.scope == mutation.scope == "UNCLASSIFIED"
    assert mutation.section == "Rulebook"
    assert set(rows) == {row.id for row in combat_audit_rows(tuple(rows.values()))}


def test_recursive_inventory_keeps_anonymous_nested_and_prose_candidates(tmp_path, monkeypatch):
    from mordheim_combat_lab.verification import audit_export, specifications
    documents = {
        "registry/runtime-scope.yaml": {},
        "catalog/mechanics/close-combat.yaml": {},
        "catalog/rules/special-rules.yaml": {"rules": [{"id": "shared", "effect": "Shared armour"}]},
        "catalog/items/nested/items.yaml": {"items": [{"id": "blade", "effect": "Parry",
            "notes": "Two-handed", "rules": [{"effect": "Nested extra attack"}]},
            {"effect": "Anonymous item"}]},
        "catalog/skills/nested/skills.yaml": {"skills": [{"id": "skill.ref", "rule_ref": "shared"},
            {"effect": "Anonymous skill"}, {"id": "skill.broken", "rule_ref": "missing"}]},
        "bands/test/band/special-rules.yaml": {"rules": [{"id": "parent", "effect": "Parent effect",
            "rules": [{"id": "child", "effect": "Nested child", "effect_i18n": {"es": "Nested child"}}]}]},
        "bands/test/band/profiles.yaml": {"profiles": [{"id": "warrior",
            "equipment_restrictions": ["No armour"], "rules": ["Cannot parry"],
            "traits": {"cause_fear": True}, "rule_ids": ["parent", "missing.rule"],
            "unresolved_references": [{"kind": "skill", "source_name": "Printed ability"}]}]},
        "other/unknown.yaml": {"entries": [{"id": "runtime.only", "runtime": {"scope": "YES",
            "implemented": "NO", "effects": [{"id": "bonus", "scope": "YES", "binding": None}]}}]},
        "other/localized.yml": {"entries": [{"effect_i18n": {"es": "Sólo texto localizado"}}]},
    }
    for relative, content in documents.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(content), encoding="utf-8")
    monkeypatch.setattr(audit_export, "inventory", lambda *args: ())
    monkeypatch.setattr(audit_export, "verify_semantics", lambda *args: pytest.fail("semantic execution"))
    monkeypatch.setattr(specifications, "load_fixtures", lambda *args: [])
    rows = build_audit_rows(tmp_path, inventory_only=True)
    texts = [row.effect_text for row in rows]
    for text in ("Parry", "Two-handed", "Nested extra attack", "Anonymous skill", "Anonymous item", "Parent effect",
                 "Nested child", "No armour", "Cannot parry"):
        assert texts.count(text) == 1
    assert texts.count("Shared armour") == 2  # shared definition and its referring skill
    assert any("missing" in row.effect_text for row in rows if row.canonical_id == "skill.broken")
    assert any(row.canonical_id == "runtime.only" and row.implemented == "NO" for row in rows)
    assert any("@/items/0/rules/0" in row.id for row in rows)
    assert any('"cause_fear": true' in text for text in texts)
    assert any("Printed ability" in text for text in texts)
    assert any("Sólo texto localizado" in text for text in texts)
    assert "Unresolved rule_ids reference: missing.rule" in texts
    assert "Unresolved rule_ids reference: parent" not in texts
    assert len(rows) == len({row.id for row in rows})
    assert {row.id for row in combat_audit_rows(rows)} == {row.id for row in rows}


def test_inventory_mode_never_executes_semantic_verification(monkeypatch):
    from mordheim_combat_lab.verification import audit_export
    monkeypatch.setattr(audit_export, "verify_semantics", lambda *args: pytest.fail("semantic execution"))
    rows = build_audit_rows(inventory_only=True)
    assert rows and all(row.audit_mode == "inventory" for row in rows)
    assert not any(row.semantic_status == "verified" for row in rows)
    from mordheim_knowledge.loader import knowledge_root, read_yaml
    path = knowledge_root() / "bands/mordheim/crooked-moon-goblins-mim/special-rules.yaml"
    if not path.exists():
        path = next(path for path in knowledge_root().glob("bands/*/*/special-rules.yaml")
                    if any(rule.get("rule_ref") == "shared-rule.regeneration" and not rule.get("effect")
                           for rule in read_yaml(path).get("rules", [])))
    rule = next(rule for rule in read_yaml(path)["rules"]
                if rule.get("rule_ref") == "shared-rule.regeneration" and not rule.get("effect"))
    shared = next(rule for rule in read_yaml(knowledge_root() / "catalog/rules/special-rules.yaml")["rules"]
                  if rule["id"] == "shared-rule.regeneration")
    assert all(row.effect_text == shared["effect"] for row in rows
               if row.source_file == path.relative_to(knowledge_root()).as_posix() and row.canonical_id == rule["id"])
    assert all(row.semantic_status == "deferred" for row in rows if row.scope == "LATER")
    reviewed = [row for row in rows if row.scope_basis == "reviewed_source"]
    assert len(reviewed) == 3394
    assert all(row.implemented == "UNKNOWN" for row in reviewed)
    assert any(row.scope == "YES" and row.scope_category == "construction" for row in reviewed)
    assert any(row.scope == "UNCLASSIFIED" and row.scope_category == "source_review" for row in reviewed)
    assert all(row.combat_work_status == "needs_target_reconciliation"
               for row in combat_audit_rows(tuple(reviewed)) if row.scope == "YES")


@pytest.mark.parametrize("scope", ["YES", "NO", "UNCLASSIFIED"])
def test_scope_review_is_bound_to_source_and_never_marks_implementation(tmp_path, scope):
    from hashlib import sha256
    from mordheim_combat_lab.verification.audit_export import _apply_scope_review
    row = AuditRow("source/example", "source_effect", "Example", "example.yaml", "", "",
        "UNCLASSIFIED", "Missing classification", "UNKNOWN", "unbound", "unclassified", "unclassified",
        "Missing classification", "", "", "", audit_mode="inventory")
    row = replace(row, effect_text="Persistent melee ward", review_status="needs_classification")
    decision = dict(id=row.id, source_file=row.source_file,
        effect_sha256=sha256(row.effect_text.encode()).hexdigest(), scope=scope,
        category="combat", reason="Reviewed individual ward clause.")
    path = tmp_path / "review.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = DictWriter(stream, fieldnames=list(decision)); writer.writeheader(); writer.writerow(decision)
    reviewed, = _apply_scope_review((row,), path)
    assert reviewed.scope == scope and reviewed.scope_basis == "reviewed_source"
    assert reviewed.implemented == "UNKNOWN" and reviewed.binding == "unbound"
    assert reviewed.semantic_status != "verified"
    changed, = _apply_scope_review((replace(row, effect_text="Now a different rule"),), path)
    assert changed.scope == "UNCLASSIFIED" and changed.scope_basis == "stale_review"
    assert "Source changed" in changed.scope_reason
    explicit = replace(row, scope="NO", scope_reason="Canonical exclusion")
    assert _apply_scope_review((explicit,), path) == (explicit,)


def test_canonical_reconciliation_keeps_implemented_work_and_resolved_decisions(tmp_path, monkeypatch):
    from mordheim_combat_lab.verification import audit_export
    monkeypatch.setattr(audit_export, "project_root", lambda: tmp_path)
    decisions = tmp_path / "docs/decisions/design-rulings.md"
    decisions.parent.mkdir(parents=True)
    decisions.write_text("## Armour ruling — Q128\nUser ruling: treat it as armour.\n", encoding="utf-8")
    row = AuditRow("rule/new-binding", "editorial_effect", "Cloak", "rules.yaml", "", "",
                   "YES", "", "YES", "bound", "linked", "pending", "Stale spec", "", "", "",
                   canonical_id="cloak", review_status="needs_ruling")
    plan = tmp_path / "plan.csv"
    origin = dict(origin_key="origin", disposition="included", existing_audit_status='[{"id":"rule/old-binding"}]',
                  canonical_id="cloak", canonical_file="sources/knowledge/rules.yaml", source_question="Armour?",
                  lots='["T13.2"]', question_id="T13-Q128", family="band-rule", clause_summary="Armour",
                  mechanisms='["saves"]')
    with plan.open("w", encoding="utf-8", newline="") as stream:
        writer = DictWriter(stream, fieldnames=list(origin)); writer.writeheader(); writer.writerow(origin)
    result = combat_audit_rows((row,), plan)
    assert len(result) == 1 and result[0].id == row.id
    assert result[0].combat_work_status == "implemented_pending_verification"
    assert result[0].question_status == "resolved" and "treat it as armour" in result[0].ruling
    assert result[0].review_status == "ready"
    assert result[0].development_family == '["saves"]'
    origin["question_id"] = "T13-Q999"
    with plan.open("w", encoding="utf-8", newline="") as stream:
        writer = DictWriter(stream, fieldnames=list(origin)); writer.writeheader(); writer.writerow(origin)
    pending = combat_audit_rows((replace(row, implemented="NO", review_status="ready"),), plan)
    assert pending[0].combat_work_status == "needs_question_review"
