"""F052: the strictness CLI publishes ``Finding.members`` in its JSON.

The audit has carried structured member evidence since F051, but the CLI's
``reported`` projection serialized only kind, schema, path, detail and
documents, so a machine consumer could not read the members without parsing
human prose. Each reported element now carries ``members`` as a JSON array with
exactly the members of its finding — ``[]`` for a finding that has none, such
as every hard finding.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from mordheim_knowledge import editorial_schema_audit as audit


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "audit_schema_strictness_cli", ROOT / "tools" / "knowledge" / "audit_schema_strictness.py"
)
cli = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cli)

#: A finding of a definition shared by several document schemas, with the
#: pooled members F051 computes.
SHARED = audit.Finding(
    schema="defs.schema.json",
    kind="unused_property",
    path="#/$defs/display_group",
    detail="declared property never present: pair_b, pair_c",
    documents=("alpha/one.yaml", "beta/two.yaml"),
    members=("pair_b", "pair_c"),
)

#: A finding local to one document schema, with a single member.
LOCAL = audit.Finding(
    schema="gamma.yaml.schema.json",
    kind="unused_enum_value",
    path="#/$defs/local_kind",
    detail="declared value never present: str:kept",
    documents=("gamma/three.yaml",),
    members=("str:kept",),
)

#: A hard finding: hard findings are never about individual members.
HARD = audit.Finding(
    schema="delta.yaml.schema.json",
    kind="open_object",
    path="#/$defs/open",
    detail="object accepts undeclared keys",
    documents=("delta/four.yaml",),
)


def justify(*findings):
    entries = {
        (finding.schema, finding.kind, finding.path): "kept by the scenario"
        for finding in findings
        if not finding.hard
    }
    return entries


def run(monkeypatch, capsys, findings, *arguments, allowlist=None):
    """Run the real ``main()`` over supplied findings; return (exit code, stdout)."""
    frozen = list(findings)
    monkeypatch.setattr(audit, "audit_strictness", lambda: frozen)
    if allowlist is not None:
        monkeypatch.setattr(audit, "JUSTIFIED_FINDINGS", dict(allowlist))
    code = cli.main(list(arguments))
    return code, capsys.readouterr().out


def reported(finding):
    """The CLI's documented projection of one finding."""
    return {
        "kind": finding.kind,
        "schema": finding.schema,
        "path": finding.path,
        "detail": finding.detail,
        "documents": list(finding.documents),
        "members": list(finding.members),
    }


def payload(text):
    """The single JSON document ``--json`` prints, parsed as emitted."""
    return json.loads(text)


def test_a_shared_finding_publishes_every_pooled_member_in_order(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, [SHARED], "--json", allowlist=justify(SHARED))
    document = payload(out)
    assert code == 0
    assert len(document["reported"]) == 1
    assert document["reported"][0]["members"] == ["pair_b", "pair_c"]
    assert all(isinstance(member, str) for member in document["reported"][0]["members"])


def test_a_local_finding_publishes_its_own_members(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, [LOCAL], "--json", allowlist=justify(LOCAL))
    document = payload(out)
    assert code == 0
    assert document["reported"] == [reported(LOCAL)]
    assert document["reported"][0]["schema"] == "gamma.yaml.schema.json"
    assert document["reported"][0]["members"] == ["str:kept"]


def test_a_hard_finding_without_members_publishes_an_empty_array(monkeypatch, capsys):
    code, out = run(monkeypatch, capsys, [HARD], "--json")
    document = payload(out)
    assert code == 1
    assert document["hard"] == 1
    assert document["reported"] == [reported(HARD)]
    assert document["reported"][0]["members"] == []


def test_the_projection_preserves_every_existing_field_and_the_order(monkeypatch, capsys):
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL, HARD], "--json", allowlist=justify(SHARED, LOCAL)
    )
    document = payload(out)
    assert code == 1  # one hard finding
    assert document["reported"] == [reported(SHARED), reported(LOCAL), reported(HARD)]
    for item in document["reported"]:
        assert set(item) == {"kind", "schema", "path", "detail", "documents", "members"}
