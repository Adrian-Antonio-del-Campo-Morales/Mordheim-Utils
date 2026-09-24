"""external.test_editorial_schemas: the editorial contract of the knowledge base.

Every maintained YAML document — the four files of a warband package, the
catalogue families, the hireling catalogue, the campaign catalogue and the
registry tables — has its format defined once in
``contracts/knowledge-editorial-v1``. These tests keep the committed knowledge
base validating against the schemas, prove that no document escapes the
contract, and keep the schemas honest about the code-level contracts they
mirror (the effect-set fields, the trait registry, the runtime classification
of ``registry/runtime-schema.yaml`` and the campaign documents a post-battle
step can name).
"""
from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import shutil

from jsonschema import Draft202012Validator
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_core.models import EffectSet
from mordheim_knowledge import editorial_schema_audit as audit
from mordheim_knowledge import editorial_schemas
from mordheim_knowledge import open_field_normalization as normalization
from mordheim_knowledge import staging_contract_audit as staging
import pytest
import yaml as yaml


ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "sources" / "knowledge"
BANDS = KNOWLEDGE / "bands"
CATALOG = KNOWLEDGE / "catalog"
REGISTRY = KNOWLEDGE / "registry"
BAND_SCHEMAS = editorial_schemas.BAND_SCHEMAS
DOCUMENTS = editorial_schemas.BAND_DOCUMENTS
SCHEMA_FILES = editorial_schemas.schema_files()

#: JSON Schema type of each Python type the compiler accepts in TRAIT_TYPES.
TRAIT_JSON_TYPES = {int: "integer", bool: "boolean", (list, tuple): "array"}


def band_packages() -> list[Path]:
    return sorted(BANDS.glob("*/*/band.yaml"))


def read(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def catalogue_documents() -> list[tuple[str, str]]:
    """``(document, schema)`` of every catalogue and registry document on disk."""
    return editorial_schemas.document_schemas(KNOWLEDGE)


def test_contract_declares_one_schema_per_document():
    assert DOCUMENTS == ("band.yaml", "profiles.yaml", "equipment-access.yaml", "special-rules.yaml")
    directory = editorial_schemas.contract_directory()
    assert directory.name == "knowledge-editorial-v1"
    for filename in (*SCHEMA_FILES, "README.md"):
        assert (directory / filename).is_file(), filename


@pytest.mark.parametrize("schema_path", SCHEMA_FILES)
def test_schema_is_valid_draft_2020_12(schema_path):
    Draft202012Validator.check_schema(editorial_schemas.schema_for(schema_path))


def test_every_catalogue_and_registry_document_is_covered_exactly_once():
    """A new catalogue file must be claimed by a schema, not validated by nobody."""
    claimed = [document for document, _ in catalogue_documents()]
    on_disk = [
        path.relative_to(KNOWLEDGE).as_posix()
        for tree in editorial_schemas.CATALOGUE_TREES
        for path in (KNOWLEDGE / tree).rglob("*.yaml")
    ]
    uncovered = sorted(set(on_disk) - set(claimed))
    assert uncovered == sorted(editorial_schemas.UNCOVERED_DOCUMENTS), uncovered
    assert len(set(claimed)) == len(claimed), "a document is claimed by two schemas"
    covered = sorted(set(on_disk) - set(editorial_schemas.UNCOVERED_DOCUMENTS))
    assert covered == sorted(claimed), set(covered) ^ set(claimed)


def test_no_declared_exception_has_gone_stale():
    """An exception kept for a document that is gone hides a real coverage gap."""
    for document in editorial_schemas.UNCOVERED_DOCUMENTS:
        assert (KNOWLEDGE / document).is_file(), document


def test_both_collections_are_covered_by_the_contract():
    by_collection = {collection: 0 for collection in editorial_schemas.COLLECTIONS}
    for path in band_packages():
        by_collection[path.parents[1].name] += 1
    assert all(by_collection.values()), by_collection


@pytest.mark.parametrize("band_yaml", band_packages(), ids=lambda path: path.parent.name)
def test_band_package_matches_the_editorial_schemas(band_yaml):
    problems = editorial_schemas.validate_band_package(band_yaml.parent)
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize(
    ("document", "schema_path"),
    catalogue_documents(),
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_catalogue_document_matches_its_editorial_schema(document, schema_path):
    problems = editorial_schemas.problems_of(schema_path, read(KNOWLEDGE / document))
    assert not problems, "\n".join(problems)


def test_every_band_package_carries_the_four_documents():
    for band_yaml in band_packages():
        for document in DOCUMENTS:
            assert (band_yaml.parent / document).is_file(), f"{band_yaml.parent.name}/{document}"


def test_combat_traits_definition_matches_the_compiler_registry():
    """`profiles.yaml` combat traits are executable: the schema mirrors TRAIT_TYPES."""
    combat_traits = editorial_schemas.schema_for(BAND_SCHEMAS["profiles.yaml"])["$defs"]["profile"]["properties"]["combat_traits"]
    assert combat_traits["additionalProperties"] is False
    declared = {key: value["type"] for key, value in combat_traits["properties"].items()}
    assert declared == {key: TRAIT_JSON_TYPES[value] for key, value in TRAIT_TYPES.items()}


def test_supported_combat_traits_are_compiler_traits():
    """The runtime-scope policy can only support traits the compiler knows."""
    scope = read(REGISTRY / "runtime-scope.yaml")
    assert set(scope["supported_combat_traits"]) <= set(TRAIT_TYPES)


def test_execution_parameters_are_effect_set_fields():
    """Every parameter of the execution contract is a field of EffectSet."""
    execution = read(CATALOG / "mechanics" / "execution.yaml")
    known = {field.name for field in fields(EffectSet)}
    assert not [
        (mechanic["id"], key)
        for mechanic in execution["mechanics"]
        for key in mechanic["parameters"]
        if key not in known
    ]


def test_the_execution_parameter_vocabulary_is_closed_and_exact():
    """The schema of `parameters` declares every field of EffectSet and nothing else."""
    parameters = editorial_schemas.schema_for("catalog-mechanics-execution.yaml.schema.json")[
        "$defs"
    ]["mechanic"]["properties"]["parameters"]
    assert parameters["additionalProperties"] is False
    declared = {
        name: subschema["type"]
        for name, subschema in parameters["properties"].items()
        if name != "tags"
    }
    expected = {
        field.name: ("boolean" if field.type in (bool, "bool") else "integer")
        for field in fields(EffectSet)
        if field.name != "tags"
    }
    assert declared == expected, set(declared) ^ set(expected)


def test_runtime_enums_match_the_registry_contract():
    registry = read(REGISTRY / "runtime-schema.yaml")
    definitions = editorial_schemas.schema_for(BAND_SCHEMAS["special-rules.yaml"])["$defs"]
    runtime = definitions["rule_runtime"]["properties"]
    assert runtime["scope"]["enum"] == registry["runtime"]["scope_values"]
    assert runtime["implemented"]["enum"] == registry["runtime"]["implemented_values"]
    assert runtime["grant"]["enum"] == registry["runtime"]["grant_values"]
    assert (
        definitions["rule"]["properties"]["kind"]["enum"]
        == registry["selectable_rule"]["kind_values"]
    )
    assert (
        definitions["runtime_binding"]["properties"]["kind"]["enum"]
        == registry["selectable_rule"]["binding_kinds"]
    )


def test_a_stray_band_key_is_rejected():
    payload = read(BANDS / "mordheim" / "orc-mob" / "band.yaml")
    payload["summary"] = "legacy prose key"
    problems = editorial_schemas.problems_of(BAND_SCHEMAS["band.yaml"], payload)
    assert any("summary" in problem and "Additional properties" in problem for problem in problems)


def test_a_missing_characteristic_is_rejected():
    payload = read(BANDS / "mordheim" / "orc-mob" / "profiles.yaml")
    del payload["profiles"][0]["characteristics"]["Ld"]
    problems = editorial_schemas.problems_of(BAND_SCHEMAS["profiles.yaml"], payload)
    assert any(problem.startswith("profiles/0/characteristics") for problem in problems), problems


def test_a_rule_without_text_or_shared_reference_is_rejected():
    payload = read(BANDS / "mordheim" / "orc-mob" / "special-rules.yaml")
    rule = next(item for item in payload["rules"] if item.get("effect"))
    del rule["effect"]
    del rule["effect_i18n"]
    problems = editorial_schemas.problems_of(BAND_SCHEMAS["special-rules.yaml"], payload)
    assert any(problem.startswith(f"rules/{payload['rules'].index(rule)}") for problem in problems)


def test_an_implemented_item_without_a_mechanic_is_rejected():
    payload = read(CATALOG / "items" / "weapons-close-combat.yaml")
    item = next(row for row in payload["items"] if row["combat_status"] == "implemented")
    del item["mechanic_id"]
    problems = editorial_schemas.problems_of("catalog-items.yaml.schema.json", payload)
    assert any("mechanic_id" in problem and "required" in problem for problem in problems), problems


def test_a_stray_catalogue_key_is_rejected():
    payload = read(CATALOG / "skills" / "general.yaml")
    payload["skills"][0]["summary"] = "legacy prose key"
    problems = editorial_schemas.problems_of("catalog-skills.yaml.schema.json", payload)
    assert any("summary" in problem and "Additional properties" in problem for problem in problems)


def test_band_id_must_match_the_directory(tmp_path):
    directory = tmp_path / "not-orc-mob"
    directory.mkdir()
    shutil.copy(BANDS / "mordheim" / "orc-mob" / "band.yaml", directory / "band.yaml")
    problems = editorial_schemas.validate_band_package(directory)
    assert any("does not match the directory" in problem for problem in problems), problems


def test_an_unknown_document_is_reported_instead_of_raising():
    problems = editorial_schemas.validate_document("roster.yaml", {})
    assert len(problems) == 1 and problems[0].startswith("Unknown document schema 'roster.yaml'"), problems


def campaign_document(name: str) -> dict:
    return read(CATALOG / "campaign" / f"{name}.yaml")


def test_every_post_battle_step_resolves_a_document_of_its_directory():
    """The `resolves` of a step is a file that must exist, so a step cannot name one that is gone."""
    sequence = campaign_document("post-battle-sequence")["sequence"]
    available = {path.name for path in (CATALOG / "campaign").glob("*.yaml")}
    resolved = {step["resolves"] for step in sequence["steps"]}
    assert resolved <= available, resolved - available
    schema = editorial_schemas.schema_for("campaign-post-battle-sequence.yaml.schema.json")
    declared = schema["properties"]["sequence"]["$ref"].removeprefix("#/$defs/")
    step = schema["$defs"][declared]["properties"]["steps"]["items"]["$ref"].removeprefix("#/$defs/")
    resolved_enum = schema["$defs"][step]["properties"]["resolves"]["enum"]
    assert set(resolved_enum) == available, set(resolved_enum) ^ available


def test_the_hireling_traits_schema_matches_the_trait_registry():
    """The trait vocabulary is closed: the schema lists exactly the traits the catalogue uses."""
    schema = editorial_schemas.schema_for("hirelings-traits.yaml.schema.json")
    declared = schema["$defs"]["profile_traits"]["properties"]["traits"]["items"]["enum"]
    registry = read(CATALOG / "hirelings" / "traits.yaml")
    used = {trait for row in registry["traits"] for trait in row["traits"]}
    assert declared == sorted(used), set(declared) ^ used


def test_hireling_skill_lists_are_a_subset_of_the_band_vocabulary():
    """A hireling may only be offered skill lists the bands themselves use."""
    band_lists = {
        skill
        for profiles in BANDS.glob("*/*/profiles.yaml")
        for profile in read(profiles).get("profiles", [])
        for skill in profile.get("skill_access", [])
    }
    hireling_lists = {
        skill
        for profiles in (CATALOG / "hirelings").rglob("*.yaml")
        for profile in read(profiles).get("profiles", [])
        for skill in profile.get("skill_access", [])
    }
    assert hireling_lists <= band_lists, hireling_lists - band_lists


def test_a_stray_campaign_key_is_rejected():
    payload = campaign_document("mutations")
    payload["mutations"][0]["summary"] = "legacy prose key"
    problems = editorial_schemas.problems_of("campaign-mutations.yaml.schema.json", payload)
    assert any("summary" in problem and "Additional properties" in problem for problem in problems)


def test_a_scenario_award_without_ref_or_effect_is_rejected():
    """An Experience row declares the canonical award or the source text, never neither and never both."""
    payload = campaign_document("scenarios")
    scenario = next(row for row in payload["scenarios"] if row["progression"].get("experience"))
    award = scenario["progression"]["experience"][0]
    award.pop("ref", None)
    award.pop("effect", None)
    problems = editorial_schemas.problems_of("campaign-scenarios.yaml.schema.json", payload)
    assert any("experience/0" in problem for problem in problems), problems


def test_a_rare_item_without_a_rarity_is_rejected():
    payload = campaign_document("trading-post")
    entry = next(row for row in payload["items"] if row["availability"]["kind"] == "rare")
    del entry["availability"]["rarity"]
    problems = editorial_schemas.problems_of("campaign-trading-post.yaml.schema.json", payload)
    assert any("availability" in problem and "rarity" in problem for problem in problems), problems


def test_an_out_of_scope_dramatis_entry_must_say_why():
    payload = read(CATALOG / "hirelings" / "dramatis-personae" / "grade-1c.yaml")
    entry = next(row for row in payload["profiles"] if row["normalization_status"] == "out_of_scope")
    del entry["out_of_scope_reason"]
    problems = editorial_schemas.problems_of("hireling-profile-dramatis-personae.yaml.schema.json", payload)
    assert any("out_of_scope_reason" in problem for problem in problems), problems


def test_a_hired_sword_may_not_be_published_out_of_scope():
    """A Hired Sword that cannot be modelled has no status to hide in: only Dramatis entries may be out of scope."""
    payload = read(CATALOG / "hirelings" / "hired-swords" / "core.yaml")
    payload["profiles"][0]["normalization_status"] = "out_of_scope"
    problems = editorial_schemas.problems_of("hireling-profile-hired-sword.yaml.schema.json", payload)
    assert any("normalization_status" in problem for problem in problems), problems


def test_a_nested_eligibility_expression_validates():
    """The expression grammar nests, so the boolean form covers what the allow/forbid lists cannot."""
    expression = {
        "not": {
            "any_of": [
                {"band_id": "witch-hunters"},
                {"all_of": [{"group_id": "warband-group.good-aligned"}, {"group_id": "warband-group.elf"}]},
            ]
        }
    }
    payload = campaign_document("hired-swords-and-dramatis")
    payload["hired_swords"][0]["eligibility"] = {"expression": expression}
    problems = editorial_schemas.problems_of("campaign-hired-swords-and-dramatis.yaml.schema.json", payload)
    assert not problems, "\n".join(problems)


def test_the_eligibility_expression_operators_are_closed():
    """An expression uses one operator or leaf per node; anything else is a contract error."""
    payload = campaign_document("hired-swords-and-dramatis")
    payload["hired_swords"][0]["eligibility"] = {"expression": {"maybe": {"band_id": "witch-hunters"}}}
    problems = editorial_schemas.problems_of("campaign-hired-swords-and-dramatis.yaml.schema.json", payload)
    assert any("eligibility" in problem for problem in problems), problems


def test_a_campaign_document_is_validated_with_its_own_schema():
    """The campaign catalogue shares the envelope but not the shape: each document has its own schema."""
    schemas = dict(catalogue_documents())
    campaign = {
        document: schema
        for document, schema in schemas.items()
        if document.startswith("catalog/campaign/")
    }
    assert len(campaign) == len(editorial_schemas.CAMPAIGN_DOCUMENTS)
    assert len(set(campaign.values())) == len(campaign), "two campaign documents share a schema"
    for document, schema in campaign.items():
        problems = editorial_schemas.problems_of(schema, read(KNOWLEDGE / document))
        assert not problems, "\n".join(problems)


def test_the_contract_is_strict_about_the_committed_documents():
    """No schema admits data the KB does not have, and every unused declaration is classified.

    The audit compares every schema with the documents it claims: a node that
    leaves keys undescribed, a tautology or an unreachable definition is a hard
    finding, and a declaration no document exercises must be justified in
    ``editorial_schema_audit.JUSTIFIED_FINDINGS`` for the contract it serves.
    """
    findings = audit.audit_strictness(KNOWLEDGE)
    hard = audit.hard_findings(findings)
    assert not hard, "\n".join(str(finding) for finding in hard)
    unjustified = audit.unjustified_findings(findings)
    assert not unjustified, "\n".join(str(finding) for finding in unjustified)


def test_no_strictness_justification_has_gone_stale():
    """A justification kept for a declaration the data now exercises hides a real gap."""
    stale = audit.stale_justifications(audit.audit_strictness(KNOWLEDGE))
    assert not stale, stale


# --------------------------------------------------------------------------- #
# Staged warbands: the contract applies before promotion
# --------------------------------------------------------------------------- #

#: Open-field values the staged trees introduce on purpose, each one a new *name*
#: rather than a new dialect: the grade of the pack and the source ids the registry
#: now carries. A set, not a count: ingesting more bands must not fail these tests,
#: but a new label must, because every one of them is a promotion decision — and
#: the decision has to be written down in ``staging.ACCEPTED_OPEN_VALUES`` or in
#: ``registry/sources.yaml`` before the value is legitimate.
STAGED_OPEN_VALUES = {
    "2A": {
        "categories[]": {"2a"},
        "grade": {"2a"},
        "sources[].manual": {
            "sylvania-supplement",
            "mordheim-index-catalog",
            "mordheim-facebook-group",
        },
    },
    "2B": {
        "categories[]": {"2b"},
        "grade": {"2b"},
        "sources[].manual": {"broheim.net"},
    },
}


def staged_roots() -> list[tuple[str, Path]]:
    return [(tree, staging.tree_root(tree)) for tree in staging.STAGED_TREES]


@pytest.mark.parametrize("tree,root", staged_roots(), ids=lambda value: value if isinstance(value, str) else None)
def test_the_staged_packages_match_the_editorial_schemas(tree, root):
    """A staged package has the promoted shape from the moment it is modelled.

    The staging trees are outside the coverage guardian, so this is the gate that
    catches a field the contract does not know about before a promotion copies it
    into the knowledge base.
    """
    deviations = staging.schema_deviations(root)
    assert not deviations, f"{tree}: " + "; ".join(str(deviation) for deviation in deviations)


def test_the_staged_schema_gate_is_not_vacuous(tmp_path):
    """The gate fails on a package the contract does not accept."""
    source = BANDS / "mordheim" / "averlanders"
    package = tmp_path / "bands" / "mordheim" / "averlanders"
    package.mkdir(parents=True)
    for document in DOCUMENTS:
        body = read(source / document)
        if document == "band.yaml":
            body["legacy_key"] = "prose the contract never names"
        (package / document).write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
    deviations = staging.schema_deviations(tmp_path)
    assert deviations, "a stray field must be reported"
    assert {(deviation.document, deviation.path) for deviation in deviations} == {("band.yaml", "(root)")}
    assert deviations[0].keys == {"legacy_key": 1}, deviations[0]


def test_the_staged_open_fields_are_pinned():
    """Every open-field value the staging adds to the vocabulary is declared here."""
    for tree, root in staged_roots():
        observed = {label: set(values) for label, values in staging.novel_open_values(root).items()}
        assert observed == STAGED_OPEN_VALUES[tree], f"{tree}: {observed}"


def test_no_pinned_staged_value_has_gone_stale():
    """A pinned label the trees no longer use hides the next one that appears."""
    for tree, root in staged_roots():
        used = staging.open_field_values(root)
        for label, values in STAGED_OPEN_VALUES[tree].items():
            assert values <= set(used[label]), f"{tree}/{label}: {sorted(values - set(used[label]))}"


def test_every_open_field_names_a_document_of_the_contract():
    assert {field.document for field in staging.OPEN_FIELDS} <= set(DOCUMENTS)


@pytest.mark.parametrize("tree,root", staged_roots(), ids=lambda value: value if isinstance(value, str) else None)
def test_every_introduced_open_value_is_sanctioned(tree, root):
    """A value outside the KB vocabulary needs the decision that introduced it.

    Two decisions count: a registered source id (the vocabulary `manual` answers
    to) and ``ACCEPTED_OPEN_VALUES``, which carries the reason. Anything else is a
    dialect, and a dialect is what promotion would copy into the knowledge base.
    """
    assert staging.open_value_findings(root) == {}, tree


def test_every_manual_of_the_kb_and_the_staging_is_a_registered_source():
    """`manual` is a registered source id wherever it is written."""
    registered = staging.registered_source_ids()
    roots = [KNOWLEDGE, *[staging.tree_root(tree) for tree in staging.STAGED_TREES]]
    for root in roots:
        assert normalization.manual_values(root) <= registered, root


# --------------------------------------------------------------------------- #
# Staged catalogues: the promotion destination, not just the package shape
# --------------------------------------------------------------------------- #

#: Extension classes of the staged catalogues against the schema of the KB
#: document that will claim them at promotion — the classes
#: ``sources/2B/promotion-schema-plan.md`` analyses and decides on. A set, not a
#: count, for the same reason as ``STAGED_OPEN_VALUES``: ingesting another rare
#: item must not fail this test, but a *new* field, enum value or missing
#: required property must, because the promotion plan does not cover it yet.
#: Extension classes of the staged catalogues, by tree. The list is the plan's
#: remaining work, and it is empty: the hireling split, the campaign side, the
#: magic envelope and the lore materialisation closed every class, and a new one
#: fails this gate until `sources/2B/promotion-schema-plan.md` declares it.
STAGED_CATALOGUE_CLASSES: dict[str, set[str]] = {"2A": set(), "2B": set()}

def staged_catalogue_classes(root: Path) -> set[str]:
    return {staging.deviation_class(deviation) for deviation in staging.catalogue_deviations(root)}


@pytest.mark.parametrize("tree,root", staged_roots(), ids=lambda value: value if isinstance(value, str) else None)
def test_the_staged_catalogues_use_only_the_declared_extension_classes(tree, root):
    """The promotion plan is a document; this keeps it describing the trees.

    Each class is a decision the promotion has to take, so a new one — a field,
    an enum value, a missing required property — must be added to
    ``sources/2B/promotion-schema-plan.md`` and to the table above in the same
    commit. The number of records showing a class is deliberately not pinned.
    """
    observed = staged_catalogue_classes(root)
    new = sorted(observed - STAGED_CATALOGUE_CLASSES[tree])
    gone = sorted(STAGED_CATALOGUE_CLASSES[tree] - observed)
    assert not new, f"{tree}: undeclared promotion classes: {new}"
    assert not gone, f"{tree}: declared promotion classes no longer observed: {gone}"


@pytest.mark.parametrize("tree,root", staged_roots(), ids=lambda value: value if isinstance(value, str) else None)
def test_the_staged_catalogue_names_are_gated_by_the_knowledge_base_policy(tree, root):
    """The staging trees answer to the title-case policy of the KB, not to a pin.

    The policy is a gate for `sources/knowledge` in its own test; this one is what
    says a promotion copy of a staging tree no longer needs rewriting first.
    """
    assert staging.naming_drift(root) == {}


def test_the_name_normalizer_is_clean_on_the_knowledge_base():
    """The KB is the reference the staging drift is measured against."""
    assert staging.naming_drift(KNOWLEDGE) == {}


def test_every_staged_catalogue_document_has_a_promotion_destination():
    """A staged catalogue YAML no destination claims would be promoted by nobody."""
    for tree, root in staged_roots():
        unclaimed, families = staging.catalogue_coverage(root)
        assert not unclaimed, f"{tree}: {[path.as_posix() for path in unclaimed]}"
        assert families, f"{tree}: no catalogue family found"
        assert {family.schema_path for family in families} <= set(SCHEMA_FILES)


def test_the_catalogue_gate_is_not_vacuous(tmp_path):
    """A stray item field and an unrouted file are both reported."""
    items = tmp_path / "catalog" / "items"
    items.mkdir(parents=True)
    body = read(CATALOG / "items" / "combat-equipment.yaml")
    (items / "combat-equipment.yaml").write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
    assert staging.catalogue_deviations(tmp_path) == []
    assert staging.catalogue_coverage(tmp_path)[0] == []

    body["items"][0]["stray_key"] = "prose the contract never names"
    (items / "combat-equipment.yaml").write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
    classes = staged_catalogue_classes(tmp_path)
    assert classes == {"catalog/items items/[] additionalProperties stray_key"}, classes

    (tmp_path / "catalog" / "unrouted.yaml").write_text("items: []\n", encoding="utf-8")
    unclaimed, _ = staging.catalogue_coverage(tmp_path)
    assert [path.name for path in unclaimed] == ["unrouted.yaml"]


def test_the_naming_gate_is_not_vacuous(tmp_path):
    """A package whose name breaks the policy is reported with its field count."""
    package = tmp_path / "bands" / "mordheim" / "averlanders"
    package.mkdir(parents=True)
    for document in DOCUMENTS:
        body = read(BANDS / "mordheim" / "averlanders" / document)
        (package / document).write_text(yaml.safe_dump(body, allow_unicode=True), encoding="utf-8")
    assert staging.naming_drift(tmp_path) == {}

    profile = read(package / "profiles.yaml")
    profile["profiles"][0]["name"] = "desert dog of the empire"
    (package / "profiles.yaml").write_text(yaml.safe_dump(profile, allow_unicode=True), encoding="utf-8")
    drift = staging.naming_drift(tmp_path)
    assert list(drift) == ["bands/mordheim/averlanders/profiles.yaml"], drift
    assert drift["bands/mordheim/averlanders/profiles.yaml"] >= 1


def test_the_audit_reports_the_looseness_it_looks_for(monkeypatch):
    """The strictness gate is not vacuous: it flags an open object and an unused declaration."""
    schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["band_id", "members"],
        "properties": {
            "band_id": {"type": "string"},
            "members": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"id": {"type": "string"}, "role": {"type": "string"}},
                },
            },
        },
        "$defs": {},
    }
    monkeypatch.setattr(editorial_schemas, "schema_for", lambda name: schema)
    subject = audit._SchemaAudit("synthetic.yaml")  # noqa: SLF001 - the auditor is what is under test
    subject.observe(
        {"band_id": "orc-mob", "members": [{"id": "boss", "legacy_key": "prose"}]},
        "synthetic",
    )
    hard = {finding.kind for finding in subject.hard_findings()}
    assert hard == {"open_object", "undeclared_key"}, hard
    kinds = {kind for kind, _, _ in subject.unexercised()}
    assert kinds == {"unused_property"}, sorted(subject.unexercised())
