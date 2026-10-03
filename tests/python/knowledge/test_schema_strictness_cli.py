"""F052: the strictness CLI publishes ``Finding.members`` in its JSON.

The audit has carried structured member evidence since F051, but the CLI's
``reported`` projection serialized only kind, schema, path, detail and
documents, so a machine consumer could not read the members without parsing
human prose. Each reported element now carries ``members`` as a JSON array with
exactly the members of its finding — ``[]`` for a finding that has none, such
as every hard finding.

The probes below load the delivered CLI with ``importlib`` and replace the
findings provider (``editorial_schema_audit.audit_strictness``) and, when a
scenario needs one, the in-memory allowlist. The real ``main()`` runs
unmodified, so these tests exercise its actual serialization, counters and exit
code; no test writes to the contract, the knowledge base or the shared
checkout.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from mordheim_knowledge import editorial_schema_audit as audit

ROOT = Path(__file__).resolve().parents[3]
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

#: A soft finding with no allowlist entry: unjustified, so it fails a run.
UNJUSTIFIED = audit.Finding(
    schema="epsilon.yaml.schema.json",
    kind="unused_type",
    path="#/$defs/epsilon_value",
    detail="declared type never present: array",
    documents=("epsilon/five.yaml",),
    members=("array",),
)

#: An allowlist entry no finding carries: stale.
STALE = ("zeta.yaml.schema.json", "unused_property", "#/$defs/ghost")


def justify(*findings, extra=None):
    """An allowlist covering exactly these soft findings, plus optional entries.

    The CLI fails a run when an allowlist entry matches no finding, so a
    scenario that wants exit 0 must justify exactly what it supplies.
    """
    entries = {
        (finding.schema, finding.kind, finding.path): "kept by the scenario"
        for finding in findings
        if not finding.hard
    }
    if extra:
        entries.update(extra)
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


# --------------------------------------------------------------------------- #
# The new field: exact members, in order, including the empty array
# --------------------------------------------------------------------------- #


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


# --------------------------------------------------------------------------- #
# The projection keeps the contract: fields, order and valid JSON
# --------------------------------------------------------------------------- #


def test_the_projection_preserves_every_existing_field_and_the_order(monkeypatch, capsys):
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL, HARD], "--json", allowlist=justify(SHARED, LOCAL)
    )
    document = payload(out)
    assert code == 1  # one hard finding
    assert document["reported"] == [reported(SHARED), reported(LOCAL), reported(HARD)]
    for item in document["reported"]:
        assert set(item) == {"kind", "schema", "path", "detail", "documents", "members"}


def test_the_json_document_keeps_its_documented_top_level_fields(monkeypatch, capsys):
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL], "--json", allowlist=justify(SHARED, LOCAL)
    )
    document = payload(out)
    assert code == 0
    assert set(document) == {
        "findings",
        "hard",
        "justified",
        "unjustified",
        "stale_justifications",
        "reported",
    }
    assert document["findings"] == 2
    assert document["hard"] == 0
    assert document["justified"] == 2
    assert document["unjustified"] == 0
    assert document["stale_justifications"] == []
    assert document["reported"] == [reported(SHARED), reported(LOCAL)]


# --------------------------------------------------------------------------- #
# --only: the selection changes, the global counters and the exit code do not
# --------------------------------------------------------------------------- #


def test_only_all_reports_every_finding_in_their_order(monkeypatch, capsys):
    code, out = run(
        monkeypatch,
        capsys,
        [SHARED, LOCAL, UNJUSTIFIED, HARD],
        "--json",
        "--only",
        "all",
        allowlist=justify(SHARED, LOCAL),
    )
    document = payload(out)
    assert code == 1
    assert [item["kind"] for item in document["reported"]] == [
        "unused_property",
        "unused_enum_value",
        "unused_type",
        "open_object",
    ]
    assert (document["findings"], document["hard"], document["justified"], document["unjustified"]) == (
        4,
        1,
        2,
        1,
    )


def test_only_hard_reports_hard_findings_only_and_keeps_the_global_counters(monkeypatch, capsys):
    code, out = run(
        monkeypatch,
        capsys,
        [SHARED, LOCAL, HARD],
        "--json",
        "--only",
        "hard",
        allowlist=justify(SHARED, LOCAL),
    )
    document = payload(out)
    assert code == 1
    assert document["reported"] == [reported(HARD)]
    assert (document["findings"], document["hard"], document["justified"], document["unjustified"]) == (
        3,
        1,
        2,
        0,
    )


def test_only_soft_reports_justified_then_unjustified(monkeypatch, capsys):
    code, out = run(
        monkeypatch,
        capsys,
        [UNJUSTIFIED, SHARED, LOCAL],
        "--json",
        "--only",
        "soft",
        allowlist=justify(SHARED, LOCAL),
    )
    document = payload(out)
    assert code == 1  # the unjustified finding still fails the run
    assert document["reported"] == [reported(SHARED), reported(LOCAL), reported(UNJUSTIFIED)]
    assert (document["findings"], document["hard"], document["justified"], document["unjustified"]) == (
        3,
        0,
        2,
        1,
    )


def test_the_filter_can_hide_a_finding_but_not_its_effect(monkeypatch, capsys):
    code, out = run(
        monkeypatch,
        capsys,
        [SHARED, LOCAL, UNJUSTIFIED],
        "--json",
        "--only",
        "hard",
        allowlist=justify(SHARED, LOCAL),
    )
    document = payload(out)
    assert code == 1
    assert document["reported"] == []
    assert (document["findings"], document["hard"], document["justified"], document["unjustified"]) == (
        3,
        0,
        2,
        1,
    )


def test_exit_is_zero_and_the_report_keeps_its_members_when_the_state_is_clean(monkeypatch, capsys):
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL], "--json", "--only", "hard", allowlist=justify(SHARED, LOCAL)
    )
    assert code == 0
    assert payload(out)["reported"] == []
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL], "--json", "--only", "soft", allowlist=justify(SHARED, LOCAL)
    )
    assert code == 0
    assert [item["members"] for item in payload(out)["reported"]] == [
        ["pair_b", "pair_c"],
        ["str:kept"],
    ]


def test_a_stale_justification_fails_the_run_even_when_the_filter_hides_it(monkeypatch, capsys):
    allowlist = justify(SHARED, LOCAL, extra={STALE: "no finding carries this entry"})
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL], "--json", "--only", "hard", allowlist=allowlist
    )
    document = payload(out)
    assert code == 1
    assert document["reported"] == []
    assert document["stale_justifications"] == [list(STALE)]
    code, out = run(monkeypatch, capsys, [SHARED, LOCAL], "--json", allowlist=allowlist)
    assert code == 1
    assert payload(out)["reported"] == [reported(SHARED), reported(LOCAL)]


# --------------------------------------------------------------------------- #
# The text report: F052 does not touch it
# --------------------------------------------------------------------------- #


def test_the_text_report_still_prints_the_findings_and_the_summary(monkeypatch, capsys):
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL, UNJUSTIFIED], allowlist=justify(SHARED, LOCAL)
    )
    assert code == 1  # the unjustified finding
    assert out == (
        f"{SHARED}\n{LOCAL}\n{UNJUSTIFIED}\n"
        "\n"
        "3 findings: 0 hard, 2 justified, 1 unjustified, 0 stale justifications\n"
    )


def test_the_text_summary_keeps_the_global_counts_under_a_filter(monkeypatch, capsys):
    code, out = run(
        monkeypatch, capsys, [SHARED, LOCAL, HARD], "--only", "hard", allowlist=justify(SHARED, LOCAL)
    )
    assert code == 1
    assert out == (
        f"{HARD}\n"
        "\n"
        "3 findings: 1 hard, 2 justified, 0 unjustified, 0 stale justifications\n"
    )
