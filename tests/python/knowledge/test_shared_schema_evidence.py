"""F051: a shared definition is judged by the evidence of every schema that uses it.

``defs.schema.json`` declares the vocabulary several document schemas reach. A
member of such a definition is unused only when **no** document of the contract
observes it: schema A exercising ``a`` and schema B exercising ``b`` backs both
members, and the audit must report neither. When a member nobody observes is
left, the finding names exactly those members — the same set in
``Finding.members`` and in ``Finding.detail`` — instead of the union of what each
schema missed plus the wording of whichever schema reported first.

The probes below replace the maintained reader (``_documents``) and the merged
schema in memory and drive the real ``audit_strictness``: no test writes to the
contract, to the knowledge base or to the shared checkout. The last group runs
the audit once against ``sources/knowledge`` and states the invariants the
repair has to keep in the committed corpus, including the F044 mappings.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from mordheim_knowledge import editorial_schema_audit as audit
from mordheim_knowledge import editorial_schemas


ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
DEFINITIONS = editorial_schemas.DEFINITIONS_FILE

#: A real name of ``defs.schema.json``: the probes must resolve through the
#: maintained ``_shared_definition`` check, not through a patched one.
SHARED = "display_text"
ANCHOR = f"#/$defs/{SHARED}"
LOCAL = "#/$defs/local_note"
SCHEMA_A = "alpha.yaml.schema.json"
SCHEMA_B = "beta.yaml.schema.json"

TWO_STRING_PROPERTIES = {"pair_a": {"type": "string"}, "pair_b": {"type": "string"}}
THREE_STRING_PROPERTIES = {**TWO_STRING_PROPERTIES, "pair_c": {"type": "string"}}


# --------------------------------------------------------------------------- #
# In-memory probes: two document schemas reaching one shared definition
# --------------------------------------------------------------------------- #


def shared_schema(properties: dict[str, dict], *, local: bool = False) -> dict:
    """One document schema whose body reaches a synthetic shared definition."""
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"note": {"$ref": f"#/$defs/{SHARED}"}},
        "$defs": {
            SHARED: {
                "type": "object",
                "additionalProperties": False,
                "properties": properties,
            }
        },
    }
    if local:
        # A definition of the document schema itself: its evidence belongs to
        # this schema and is never pooled with anybody else's.
        schema["properties"]["extra"] = {"$ref": LOCAL}
        schema["$defs"]["local_note"] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {"kept": {"type": "string"}},
        }
    return schema


def use_schema(monkeypatch, schema: dict, names: set[str]) -> None:
    """Make the merged-schema reader return one synthetic schema for ``names``."""
    real = editorial_schemas.schema_for
    monkeypatch.setattr(
        editorial_schemas,
        "schema_for",
        lambda name: schema if name in names else real(name),
    )


def probe(monkeypatch, documents: dict, schema: dict) -> list[audit.Finding]:
    """Audit synthetic documents against a synthetic schema, entirely in memory."""
    use_schema(monkeypatch, schema, set(documents))
    monkeypatch.setattr(audit, "_documents", lambda base: documents)
    monkeypatch.setattr(audit, "dead_definitions", lambda: [])
    return audit.audit_strictness()


def findings_at(findings: list[audit.Finding], kind: str) -> list[audit.Finding]:
    """Every finding of one kind, at any path."""
    return [finding for finding in findings if finding.kind == kind]


def single(findings: list[audit.Finding], kind: str) -> audit.Finding:
    """The only finding of one kind; the probes above report no other one."""
    found = findings_at(findings, kind)
    assert len(found) == 1, [(item.schema, item.path, item.members) for item in found]
    return found[0]


def snapshot(findings: list[audit.Finding]) -> list[tuple]:
    """Identity plus evidence of every finding, order included."""
    return [
        (
            finding.schema,
            finding.kind,
            finding.path,
            finding.detail,
            finding.members,
            finding.documents,
        )
        for finding in findings
    ]


def document(label: str, note: dict) -> tuple[str, dict]:
    """One document of a schema that reaches the shared definition."""
    return (label, {"note": note})


def justified(monkeypatch, value) -> tuple[str, str, str]:
    """A synthetic justification for the synthetic shared definition."""
    entry = (DEFINITIONS, "unused_property", ANCHOR)
    monkeypatch.setitem(audit.JUSTIFIED_FINDINGS, entry, value)
    return entry


# --------------------------------------------------------------------------- #
# The defect: complementary use must silence the shared declaration
# --------------------------------------------------------------------------- #


def test_complementary_documents_pool_into_one_shared_declaration(monkeypatch):
    """Schema A exercises `pair_a` and schema B `pair_b`: neither is unused.

    This is the reported defect: pooled as the union of the members each schema
    missed, the audit reported both, although a document of the knowledge base
    exercises each one.
    """
    documents = {
        SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})],
        SCHEMA_B: [document("mordheim/beta/band.yaml", {"pair_b": "used"})],
    }
    findings = probe(monkeypatch, documents, shared_schema(TWO_STRING_PROPERTIES))
    assert findings == [], [str(finding) for finding in findings]

    # Non-vacuity: each schema on its own does miss the member the other one
    # exercises, so a per-schema reading has something to report.
    for schema_path, observed, missing in (
        (SCHEMA_A, {"pair_a": "used"}, "pair_b"),
        (SCHEMA_B, {"pair_b": "used"}, "pair_a"),
    ):
        subject = audit._SchemaAudit(schema_path)  # noqa: SLF001 - the auditor is under test
        subject.observe({"note": observed}, f"synthetic/{schema_path}")
        unexercised = subject.unexercised()
        assert [item[0] for item in unexercised] == ["unused_property"]
        assert unexercised[0][1] == ANCHOR
        assert unexercised[0][3] == (missing,)


def test_a_member_used_by_any_schema_is_not_reported_by_another(monkeypatch):
    """One schema exercising every member and another exercising none: no finding."""
    documents = {
        SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "x", "pair_b": "y"})],
        SCHEMA_B: [document("mordheim/beta/band.yaml", {})],
    }
    findings = probe(monkeypatch, documents, shared_schema(TWO_STRING_PROPERTIES))
    assert findings == [], [str(finding) for finding in findings]


def test_a_member_no_document_observes_is_reported_once_with_its_own_detail(monkeypatch):
    """The global evidence decides; detail and members describe the same member."""
    documents = {
        SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})],
        SCHEMA_B: [document("mordheim/beta/band.yaml", {"pair_b": "used"})],
    }
    findings = probe(monkeypatch, documents, shared_schema(THREE_STRING_PROPERTIES))
    declared = single(findings, "unused_property")
    assert declared.schema == DEFINITIONS
    assert declared.path == ANCHOR
    assert declared.members == ("pair_c",)
    assert declared.detail == "declared property never present: pair_c"
    # The documented evidence pools the schemas that report the declaration.
    assert declared.documents == ("mordheim/alpha/band.yaml", "mordheim/beta/band.yaml")


def test_a_shared_definition_only_one_schema_reaches_reads_like_before(monkeypatch):
    """Pooling with one contributor keeps the finding and its documents."""
    documents = {SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})]}
    findings = probe(monkeypatch, documents, shared_schema(TWO_STRING_PROPERTIES))
    declared = single(findings, "unused_property")
    assert declared.schema == DEFINITIONS
    assert declared.path == ANCHOR
    assert declared.members == ("pair_b",)
    assert declared.documents == ("mordheim/alpha/band.yaml",)


def test_a_local_definition_keeps_its_own_schema(monkeypatch):
    """Only the definitions of ``defs.schema.json`` are pooled."""
    schema = shared_schema(TWO_STRING_PROPERTIES, local=True)
    use_schema(monkeypatch, schema, {SCHEMA_A})
    subject = audit._SchemaAudit(SCHEMA_A)  # noqa: SLF001 - the auditor is under test
    subject.observe(
        {"note": {"pair_a": "x", "pair_b": "y"}, "extra": {}},
        "mordheim/alpha/band.yaml",
    )
    assert audit._shared_definition(LOCAL) is False  # noqa: SLF001
    unexercised = subject.unexercised()
    assert [(item[0], item[1]) for item in unexercised] == [("unused_property", LOCAL)]
    assert unexercised[0][3] == ("kept",)
    assert unexercised[0][2] == "declared property never present: kept"


# --------------------------------------------------------------------------- #
# The order of schemas and documents must not change the result
# --------------------------------------------------------------------------- #


def test_the_pooled_result_is_stable_in_any_order(monkeypatch):
    """Reversing the schemas and the documents of each schema changes nothing."""
    properties = {**TWO_STRING_PROPERTIES, "pair_c": {"type": "string"}}
    items = [
        (
            SCHEMA_A,
            [
                document("mordheim/alpha/band.yaml", {"pair_a": "used"}),
                document("trollheim/alpha/band.yaml", {"pair_a": "used"}),
            ],
        ),
        (
            SCHEMA_B,
            [
                document("mordheim/beta/band.yaml", {"pair_b": "used"}),
                document("trollheim/beta/band.yaml", {"pair_b": "used"}),
            ],
        ),
    ]
    forwards = probe(monkeypatch, dict(items), shared_schema(properties))
    backwards = probe(
        monkeypatch,
        {name: list(reversed(documents)) for name, documents in reversed(items)},
        shared_schema(properties),
    )
    assert snapshot(forwards) == snapshot(backwards)
    assert single(forwards, "unused_property").members == ("pair_c",)
    assert single(forwards, "unused_property").documents == (
        "mordheim/alpha/band.yaml",
        "mordheim/beta/band.yaml",
        "trollheim/alpha/band.yaml",
        "trollheim/beta/band.yaml",
    )


# --------------------------------------------------------------------------- #
# Every kind the audit pools: properties, types, enum values and branches
# --------------------------------------------------------------------------- #


def test_detail_and_members_agree_for_every_pooled_kind(monkeypatch):
    """Complementary documents back the shared types, values and branches."""
    properties = {
        "pair_a": {"type": "string"},
        "pair_b": {"type": "string"},
        "pair_c": {"type": "string"},
        "mode": {"enum": ["x", "y", "z"]},
        "text": {"type": ["string", "integer", "boolean"]},
        "pick": {"oneOf": [{"type": "string"}, {"type": "integer"}, {"const": "never"}]},
    }
    documents = {
        SCHEMA_A: [
            document(
                "mordheim/alpha/band.yaml",
                {"pair_a": "used", "mode": "x", "text": "word", "pick": "chosen"},
            )
        ],
        SCHEMA_B: [
            document(
                "mordheim/beta/band.yaml",
                {"pair_b": "used", "mode": "y", "text": 7, "pick": 42},
            )
        ],
    }
    findings = probe(monkeypatch, documents, shared_schema(properties))
    reported = {
        (finding.kind, finding.path): finding
        for finding in findings
        if finding.schema == DEFINITIONS
    }
    assert set(reported) == {
        ("unused_property", ANCHOR),
        ("unused_enum_value", f"{ANCHOR}.mode"),
        ("unused_type", f"{ANCHOR}.text"),
        ("dead_branch", f"{ANCHOR}.pick"),
    }, sorted(reported)
    assert reported[("unused_property", ANCHOR)].members == ("pair_c",)
    assert (
        reported[("unused_property", ANCHOR)].detail
        == "declared property never present: pair_c"
    )
    assert reported[("unused_enum_value", f"{ANCHOR}.mode")].members == ("str:z",)
    assert (
        reported[("unused_enum_value", f"{ANCHOR}.mode")].detail
        == "declared value never present: str:z"
    )
    assert reported[("unused_type", f"{ANCHOR}.text")].members == ("boolean",)
    assert (
        reported[("unused_type", f"{ANCHOR}.text")].detail
        == "declared type never observed: boolean"
    )
    assert reported[("dead_branch", f"{ANCHOR}.pick")].members == ("2",)
    assert reported[("dead_branch", f"{ANCHOR}.pick")].detail == "branch never selected: 2"
    for finding in findings:
        if finding.kind in audit.SOFT_FINDINGS:
            assert finding.members == tuple(sorted(finding.members)), finding
            assert finding.detail == audit._DETAIL_LEADS[finding.kind] + ", ".join(  # noqa: SLF001
                finding.members
            ), finding


# --------------------------------------------------------------------------- #
# The allowlist: member scope, staleness and the legacy text entries
# --------------------------------------------------------------------------- #


def test_a_member_mapping_covers_only_the_members_it_names(monkeypatch):
    """A mapping that omits a member leaves the finding unjustified."""
    justified(monkeypatch, {"pair_c": "kept for the synthetic contract"})
    documents = {SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})]}
    findings = probe(monkeypatch, documents, shared_schema(THREE_STRING_PROPERTIES))
    declared = single(findings, "unused_property")
    assert declared.members == ("pair_b", "pair_c")
    assert declared in audit.unjustified_findings(findings)

    justified(monkeypatch, {"pair_b": "kept", "pair_c": "kept"})
    findings = probe(monkeypatch, documents, shared_schema(THREE_STRING_PROPERTIES))
    declared = single(findings, "unused_property")
    assert declared.members == ("pair_b", "pair_c")
    assert declared not in audit.unjustified_findings(findings)


def test_a_member_added_later_is_not_covered_by_an_old_mapping(monkeypatch):
    """A new property of the same shared definition is a finding of its own."""
    justified(monkeypatch, {"pair_b": "kept", "pair_c": "kept"})
    documents = {SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})]}
    properties = {**THREE_STRING_PROPERTIES, "pair_d": {"type": "string"}}
    findings = probe(monkeypatch, documents, shared_schema(properties))
    declared = single(findings, "unused_property")
    assert declared.members == ("pair_b", "pair_c", "pair_d")
    assert declared.detail == "declared property never present: pair_b, pair_c, pair_d"
    assert declared in audit.unjustified_findings(findings)


def test_a_member_any_schema_exercises_makes_the_global_mapping_stale(monkeypatch):
    """`pair_b` is exercised by schema B, so it cannot stay justified as unused."""
    entry = justified(monkeypatch, {"pair_b": "kept", "pair_c": "kept"})
    documents = {
        SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})],
        SCHEMA_B: [document("mordheim/beta/band.yaml", {"pair_b": "used"})],
    }
    findings = probe(monkeypatch, documents, shared_schema(THREE_STRING_PROPERTIES))
    declared = single(findings, "unused_property")
    assert declared.members == ("pair_c",)
    assert declared not in audit.unjustified_findings(findings)
    assert entry in audit.stale_justifications(findings)

    justified(monkeypatch, {"pair_c": "kept"})
    assert entry not in audit.stale_justifications(findings)
    assert declared not in audit.unjustified_findings(findings)


def test_a_text_justification_still_covers_every_member_of_its_path(monkeypatch):
    """The legacy single-string entry keeps its behaviour, pooled or not."""
    entry = justified(monkeypatch, "the synthetic contract keeps this declaration alive")
    documents = {SCHEMA_A: [document("mordheim/alpha/band.yaml", {"pair_a": "used"})]}
    findings = probe(monkeypatch, documents, shared_schema(THREE_STRING_PROPERTIES))
    declared = single(findings, "unused_property")
    assert declared.members == ("pair_b", "pair_c")
    assert declared not in audit.unjustified_findings(findings)
    assert entry not in audit.stale_justifications(findings)
    assert entry in audit.JUSTIFIED_FINDINGS


def test_pooling_never_hides_the_looseness_findings(monkeypatch):
    """Hard findings and local findings stay with the schema that carries them."""
    schema = {
        "type": "object",
        "properties": {"note": {"$ref": f"#/$defs/{SHARED}"}, "kept": {"type": "string"}},
        "$defs": {
            SHARED: {
                "type": "object",
                "additionalProperties": False,
                "properties": TWO_STRING_PROPERTIES,
            }
        },
    }
    documents = {
        SCHEMA_A: [
            ("mordheim/alpha/band.yaml", {"note": {"pair_a": "x", "pair_b": "y"}, "legacy": 1})
        ],
        SCHEMA_B: [
            ("mordheim/beta/band.yaml", {"note": {"pair_a": "x", "pair_b": "y"}, "legacy": 2})
        ],
    }
    findings = probe(monkeypatch, documents, schema)
    hard = audit.hard_findings(findings)
    assert {finding.kind for finding in hard} == {"open_object", "undeclared_key"}
    assert {finding.schema for finding in hard} == {SCHEMA_A, SCHEMA_B}
    local = findings_at(findings, "unused_property")
    assert {finding.schema for finding in local} == {SCHEMA_A, SCHEMA_B}
    assert {finding.path for finding in local} == {"$"}
    assert {finding.members for finding in local} == {("kept",)}
    assert [finding for finding in findings if finding.schema == DEFINITIONS] == []


# --------------------------------------------------------------------------- #
# The committed corpus: what the repair has to keep there
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=None)
def real_findings() -> tuple[audit.Finding, ...]:
    """The maintained strictness audit of the committed knowledge base, once."""
    return tuple(audit.audit_strictness(KNOWLEDGE))


def test_the_committed_audit_still_tells_one_story_per_finding():
    """No hard, unjustified or stale finding, and detail matching members."""
    findings = list(real_findings())
    assert audit.hard_findings(findings) == []
    assert audit.unjustified_findings(findings) == []
    assert audit.stale_justifications(findings) == []
    soft = [finding for finding in findings if finding.kind in audit.SOFT_FINDINGS]
    assert soft, "the audit reports nothing; the strictness gate would be vacuous"
    for finding in soft:
        assert finding.members, finding
        assert finding.members == tuple(sorted(finding.members)), finding
        assert finding.detail == audit._DETAIL_LEADS[finding.kind] + ", ".join(finding.members), (  # noqa: SLF001
            finding
        )


def test_the_shared_definition_findings_are_pooled_and_unchanged():
    """The remaining shared findings keep their identity and their members."""
    shared = {
        (finding.kind, finding.path): finding.members
        for finding in real_findings()
        if finding.schema == DEFINITIONS and finding.kind in audit.SOFT_FINDINGS
    }
    assert shared == {
        ("unused_enum_value", "#/$defs/catalog_status"): ("str:draft",),
        ("unused_enum_value", "#/$defs/characteristic_name"): (
            "str:BS",
            "str:I",
            "str:Ld",
            "str:M",
            "str:W",
        ),
    }, shared


def test_the_grant_vocabulary_has_no_unused_member_left():
    """F051 in the real corpus: every `rule_runtime.grant` value is exercised.

    `band`, `profile` and `selectable` are used by the band special rules and
    `none` by the skills catalogue, so the shared enum is reached everywhere and
    the pooled finding — the union of the members each schema missed — was the
    false positive this repair removes. The allowlist entry that used to justify
    it is gone for the same reason: it matched no finding.
    """
    enum = editorial_schemas.schema_for("special-rules.yaml.schema.json")["$defs"]["rule_runtime"][
        "properties"
    ]["grant"]["enum"]
    observed = set()
    for path in sorted((KNOWLEDGE / "bands").glob("*/*/special-rules.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for rule in payload.get("rules") or []:
            grant = (rule.get("runtime") or {}).get("grant")
            if grant is not None:
                observed.add(grant)
    for path in sorted((KNOWLEDGE / "catalog" / "skills").glob("*.yaml")):
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for skill in payload.get("skills") or []:
            grant = (skill.get("runtime") or {}).get("grant")
            if grant is not None:
                observed.add(grant)
    assert observed == set(enum), (sorted(observed), enum)
    assert [
        finding
        for finding in real_findings()
        if finding.path == "#/$defs/rule_runtime.grant"
    ] == []


def test_the_equipment_access_mappings_of_f044_are_preserved():
    """The repair does not touch the two accepted local declarations."""
    equipment = {
        (finding.kind, finding.path): finding.members
        for finding in real_findings()
        if finding.schema == "equipment-access.yaml.schema.json"
    }
    assert equipment == {
        ("unused_property", "#/$defs/equipment_list"): ("notes", "notes_i18n"),
        ("unused_enum_value", "#/$defs/equipment_list.applies_to.profile_types[]"): (
            "str:animal",
            "str:henchman",
            "str:summoned",
        ),
    }, equipment
