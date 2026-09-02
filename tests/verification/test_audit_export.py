"""Contrato del informe de auditoría generado."""
from csv import DictReader
from dataclasses import fields
from types import SimpleNamespace
import json

from mordheim_combat_lab.verification.audit_export import AuditRow
from mordheim_combat_lab.verification.audit_export import build_audit_rows
from mordheim_combat_lab.verification.audit_export import filter_audit_rows
from mordheim_combat_lab.verification.audit_export import write_csv
from mordheim_combat_lab.verification.inventory import inventory
import pytest


@pytest.mark.parametrize("question,ruling,verified,dependencies,expected", [
    ("¿Cómo se combina?", "", False, (), "needs_ruling"),
    ("¿Cómo se combina?", "", False, ("missing",), "needs_ruling"),
    ("¿Cómo se combina?", "Se suma, según la fuente.", False, (), "ready"),
    ("¿Cómo se combina?", "Se suma, según la fuente.", True, (), "verified"),
    ("¿Cómo se combina?", "Se suma, según la fuente.", False, ("missing",), "blocked_by_dependency"),
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
        pending=[] if verified else [(target, "Trabajo pendiente, no una pregunta.")],
    )
    monkeypatch.setattr(audit_export, "verify_semantics", lambda *args: report)
    monkeypatch.setattr(audit_export, "read_yaml", lambda path: {
        "weapons": [{"id": "weapon.example"}],
    } if path.name == "close-combat.yaml" else {})
    monkeypatch.setattr(specifications, "load_fixtures", lambda *args: [{
        "sources": [{"target": target}], "question": question, "ruling": ruling,
        "interpretation": "Descripción de la especificación, no una decisión.",
    }])
    row, = build_audit_rows(tmp_path)
    assert row.review_status == expected
    assert row.question == question
    assert row.ruling == ruling
    assert row.interpretation != row.ruling
    assert (row.semantic_status == "verified") is verified


@pytest.mark.parametrize("metadata,valid", [
    ({"question": "¿Qué valor?", "pending": "Falta respuesta"}, True),
    ({"question": "¿Qué valor?", "ruling": "El valor es 4."}, True),
    ({"question": "¿Qué valor?"}, False),
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


def test_cli_forwards_review_filter(monkeypatch, tmp_path):
    from mordheim_combat_lab.cli.commands import main
    from mordheim_combat_lab.verification import audit_export
    captured = {}
    def generate(**kwargs):
        captured.update(kwargs)
        return tmp_path / "rules-audit.csv"
    monkeypatch.setattr(audit_export, "generate_audit", generate)
    assert main(["audit", "--review-status", "needs_ruling", "--scope", "YES"]) == 0
    assert captured["review_status"] == "needs_ruling"
    assert captured["scope"] == "YES"


@pytest.fixture(scope="module")
def audit_rows():
    return build_audit_rows()


def test_audit_covers_every_scope_class_and_matches_semantic_inventory(audit_rows):
    included = [row for row in audit_rows if row.scope == "YES"]
    assert {row.id for row in included} == {item.id for item in inventory()}
    semantic_statuses = {row.semantic_status for row in included}
    assert semantic_statuses <= {"verified", "pending"}
    assert "verified" in semantic_statuses
    assert all(row.semantic_status == "out_of_scope" for row in audit_rows if row.scope != "YES")
    assert all(row.scope_reason for row in audit_rows if row.scope != "YES")
    assert all(row.review_status == "not_applicable" for row in audit_rows if row.scope != "YES")
    assert len({row.id for row in audit_rows}) == len(audit_rows)


def test_audit_filters_are_composable(audit_rows):
    verified = filter_audit_rows(audit_rows, scope="YES", status="verified")
    assert verified
    assert all(row.scope == "YES" and row.semantic_status == "verified" for row in verified)
    reviewed = filter_audit_rows(audit_rows, scope="YES", status="verified", review_status="verified")
    assert reviewed
    assert all(row.review_status == "verified" for row in reviewed)


def test_resolved_real_question_is_preserved_in_verified_row(audit_rows):
    row = next(row for row in audit_rows if row.id == "mechanic/skill.swordmaster")
    assert row.review_status == "verified"
    assert row.question and row.ruling


def test_audit_writer_creates_excel_friendly_csv(tmp_path):
    row = AuditRow(
        "rule/example", "editorial_effect", "Regla <ejemplo>", "rules.yaml", "Sección", "",
        "YES", "", "YES", '{"id": "example"}', "linked", "verified", "", "scenario-1",
        "", "Respuesta, con fundamento", "verified", "¿Primera línea?\n¿Segunda?", "Interpretación general",
    )
    csv_path = tmp_path / "audit.csv"
    write_csv((row,), csv_path)
    with csv_path.open(encoding="utf-8-sig", newline="") as stream:
        parsed = list(DictReader(stream))
    assert list(parsed[0]) == [field.name for field in fields(AuditRow)]
    assert parsed[0]["name"] == "Regla <ejemplo>"
    assert parsed[0]["question"] == "¿Primera línea? ¿Segunda?"
    assert parsed[0]["ruling"] == row.ruling
    assert parsed[0]["review_status"] == "verified"
    assert len(csv_path.read_text(encoding="utf-8-sig").splitlines()) == 2
