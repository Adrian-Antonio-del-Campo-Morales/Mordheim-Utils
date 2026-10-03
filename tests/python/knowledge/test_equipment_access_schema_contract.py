"""F044: the equipment-access list contract against its documents and consumers.

The strictness audit reports two declarations of ``equipment-access.yaml.schema.json``
that no committed document exercises: the list-level ``notes``/``notes_i18n``
pair and three values of the ``applies_to.profile_types`` vocabulary
(``animal``, ``henchman``, ``summoned``). Both are kept — and justified member
by member in ``editorial_schema_audit.JUSTIFIED_FINDINGS`` — because the
maintained reference projection reads them; deleting a consumed declaration to
turn the gate green is not a repair.

These tests state that disposition and, above all, its limits. The two members
justified for a definition stay narrow: a property or an enum value added later
to the same declaration is still an unjustified finding, and a mapped member the
documents start exercising turns the entry stale instead of hiding.

No test here writes to the knowledge base or to the contract. The negative
probes clone the merged schema in memory, and the staleness probe audits one
synthetic package under ``tmp_path`` (F049: mutations stay isolated from the
shared inputs).
"""
from __future__ import annotations

import copy
from functools import lru_cache
from pathlib import Path

import yaml

from mordheim_knowledge import editorial_schema_audit as audit
from mordheim_knowledge import editorial_schemas


ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
SCHEMA = "equipment-access.yaml.schema.json"
PROFILES_SCHEMA = "profiles.yaml.schema.json"
LIST_DEFINITION = "#/$defs/equipment_list"
RECIPIENT_VOCABULARY = "#/$defs/equipment_list.applies_to.profile_types[]"
JUSTIFIED_PROPERTIES = (SCHEMA, "unused_property", LIST_DEFINITION)
JUSTIFIED_RECIPIENTS = (SCHEMA, "unused_enum_value", RECIPIENT_VOCABULARY)


@lru_cache(maxsize=None)
def real_findings() -> tuple[audit.Finding, ...]:
    """The maintained strictness audit of the committed knowledge base, once."""
    return tuple(audit.audit_strictness(KNOWLEDGE))


def finding(findings, path: str, kind: str) -> audit.Finding | None:
    """The finding of one document schema at one path, if it is reported."""
    return next(
        (
            item
            for item in findings
            if item.schema == SCHEMA and item.kind == kind and item.path == path
        ),
        None,
    )


def equipment_access(**extra) -> dict:
    """A minimal equipment-access document; ``extra`` extends the only list."""
    return {
        "schema_version": 2,
        "band_id": "contract-fixture",
        "equipment_lists": [
            {
                "id": "fixture-list",
                "name": "Fixture list",
                "items": [{"item_id": "dagger", "cost": 2}],
                "source": {"manual": "user-ruling", "printed_page": 0, "section": "Fixture"},
                **extra,
            }
        ],
    }


def problems(payload: dict) -> list[str]:
    """Schema problems of one parsed document, through the maintained validator."""
    return editorial_schemas.problems_of(SCHEMA, payload)


def clone_schema(monkeypatch) -> dict:
    """The merged document schema, cloned; edits never reach the contract file."""
    real = editorial_schemas.schema_for
    clone = copy.deepcopy(real(SCHEMA))
    monkeypatch.setattr(
        editorial_schemas,
        "schema_for",
        lambda name: clone if name == SCHEMA else real(name),
    )
    return clone


# --------------------------------------------------------------------------- #
# Disposition: the two reported findings, justified member by member
# --------------------------------------------------------------------------- #


def test_the_reported_findings_are_justified_member_by_member():
    """The allowlist names exactly the members the audit reports, nothing wider."""
    findings = real_findings()
    properties = finding(findings, LIST_DEFINITION, "unused_property")
    assert properties is not None, "the list-level notes finding disappeared"
    assert properties.members == ("notes", "notes_i18n")
    recipients = finding(findings, RECIPIENT_VOCABULARY, "unused_enum_value")
    assert recipients is not None, "the recipient-vocabulary finding disappeared"
    assert recipients.members == ("str:animal", "str:henchman", "str:summoned")
    assert set(audit.JUSTIFIED_FINDINGS[JUSTIFIED_PROPERTIES]) == set(properties.members)
    assert set(audit.JUSTIFIED_FINDINGS[JUSTIFIED_RECIPIENTS]) == set(recipients.members)
    assert [item for item in audit.unjustified_findings(findings) if item.schema == SCHEMA] == []
    assert [entry for entry in audit.stale_justifications(findings) if entry[0] == SCHEMA] == []


def test_the_rest_of_the_allowlist_still_covers_the_real_audit():
    """Unrelated declarations keep their own justifications; none is widened."""
    findings = real_findings()
    assert audit.unjustified_findings(findings) == []
    assert audit.stale_justifications(findings) == []


def test_the_recipient_vocabulary_is_the_profile_kind_vocabulary():
    """A recipient is a profile kind: both schemas declare the same four values."""
    recipients = editorial_schemas.schema_for(SCHEMA)["$defs"]["equipment_list"]["properties"][
        "applies_to"
    ]["properties"]["profile_types"]["items"]["enum"]
    kinds = editorial_schemas.schema_for(PROFILES_SCHEMA)["$defs"]["profile"]["properties"]["type"][
        "enum"
    ]
    assert recipients == kinds == ["hero", "henchman", "animal", "summoned"]


def test_the_canonical_profiles_exercise_every_recipient_kind():
    """The three values the audit cannot see in equipment-access are live data."""
    used = {
        profile.get("type")
        for profiles in (KNOWLEDGE / "bands").glob("*/*/profiles.yaml")
        for profile in yaml.safe_load(profiles.read_text(encoding="utf-8"))["profiles"]
    }
    assert {"animal", "henchman", "summoned"} <= used, sorted(used)


# --------------------------------------------------------------------------- #
# The declarations themselves: shapes and closed vocabularies
# --------------------------------------------------------------------------- #


def test_a_list_note_and_its_translation_validate():
    payload = equipment_access(notes="Fixture note.", notes_i18n={"es": "Nota sintética."})
    assert problems(payload) == []


def test_malformed_list_note_blocks_are_rejected():
    for extra in (
        {"notes": ""},
        {"notes": 7},
        {"notes_i18n": {"en": "an English mirror is never stored"}},
        {"notes_i18n": {"es": ""}},
        {"notes_i18n": "Nota sintética."},
    ):
        reported = problems(equipment_access(**extra))
        assert reported, extra
        assert any("notes" in problem for problem in reported), (extra, reported)


def test_every_declared_recipient_kind_validates():
    for kind in ("hero", "henchman", "animal", "summoned"):
        assert problems(equipment_access(applies_to={"profile_types": [kind]})) == [], kind


def test_undeclared_or_malformed_recipient_blocks_are_rejected():
    for extra in (
        {"applies_to": {"profile_types": ["dragon"]}},
        {"applies_to": {"profile_types": []}},
        {"applies_to": {"profile_types": ["hero", "hero"]}},
        {"applies_to": {}},
        {"applies_to": {"profile_types": ["hero"], "bands": ["fixture-band"]}},
    ):
        reported = problems(equipment_access(**extra))
        assert reported, extra
        assert any("applies_to" in problem for problem in reported), (extra, reported)


# --------------------------------------------------------------------------- #
# Precision: the member scope covers nothing else, in the same path or outside
# --------------------------------------------------------------------------- #


def test_a_new_property_in_the_justified_definition_or_outside_it_is_a_finding(monkeypatch):
    clone = clone_schema(monkeypatch)
    clone["$defs"]["equipment_list"]["properties"]["illustration"] = {"$ref": "#/$defs/display_text"}
    clone["$defs"]["equipment_entry"]["properties"]["illustration"] = {"$ref": "#/$defs/display_text"}
    findings = audit.audit_strictness(KNOWLEDGE)
    declared = finding(findings, LIST_DEFINITION, "unused_property")
    assert declared is not None
    assert declared.members == ("illustration", "notes", "notes_i18n")
    assert set(audit.JUSTIFIED_FINDINGS[JUSTIFIED_PROPERTIES]) < set(declared.members)
    assert declared in audit.unjustified_findings(findings)
    unrelated = finding(findings, "#/$defs/equipment_entry", "unused_property")
    assert unrelated is not None
    assert unrelated.members == ("illustration",)
    assert unrelated in audit.unjustified_findings(findings)


def test_a_new_recipient_value_is_a_finding(monkeypatch):
    clone = clone_schema(monkeypatch)
    clone["$defs"]["equipment_list"]["properties"]["applies_to"]["properties"]["profile_types"][
        "items"
    ]["enum"].append("swarm")
    findings = audit.audit_strictness(KNOWLEDGE)
    declared = finding(findings, RECIPIENT_VOCABULARY, "unused_enum_value")
    assert declared is not None
    assert declared.members == ("str:animal", "str:henchman", "str:summoned", "str:swarm")
    assert declared in audit.unjustified_findings(findings)


# --------------------------------------------------------------------------- #
# Staleness: an exercised member must be removed from the justification
# --------------------------------------------------------------------------- #


def documented_list(**extra) -> dict:
    """The same fixture with every *other* equipment-list member exercised."""
    return equipment_access(
        name_i18n={"es": "Lista sintética"},
        applies_to={"profile_types": ["hero"]},
        loadouts=[{"id": "fixture-loadout", "name": "Fixture loadout", "cost": 3, "items": ["dagger"]}],
        **extra,
    )


def test_a_note_in_the_documents_turns_the_justification_stale(tmp_path):
    """One isolated synthetic package: `notes` is exercised, so its member goes stale."""
    package = tmp_path / "bands" / "mordheim" / "fixture-band"
    package.mkdir(parents=True)
    (package / "band.yaml").write_text(
        yaml.safe_dump({"schema_version": 2, "id": "fixture-band", "name": "Fixture band"}),
        encoding="utf-8",
    )
    for name in ("profiles.yaml", "special-rules.yaml"):
        (package / name).write_text(yaml.safe_dump({}), encoding="utf-8")

    (package / "equipment-access.yaml").write_text(
        yaml.safe_dump(documented_list(notes="A note the documents now exercise.")),
        encoding="utf-8",
    )
    findings = audit.audit_strictness(tmp_path)
    declared = finding(findings, LIST_DEFINITION, "unused_property")
    assert declared is not None
    assert declared.members == ("notes_i18n",)
    assert declared not in audit.unjustified_findings(findings)
    assert JUSTIFIED_PROPERTIES in audit.stale_justifications(findings)

    (package / "equipment-access.yaml").write_text(
        yaml.safe_dump(documented_list()), encoding="utf-8"
    )
    findings = audit.audit_strictness(tmp_path)
    declared = finding(findings, LIST_DEFINITION, "unused_property")
    assert declared is not None
    assert declared.members == ("notes", "notes_i18n")
    assert JUSTIFIED_PROPERTIES not in audit.stale_justifications(findings)
