"""Strictness audit of the editorial contract against the real documents.

A schema can drift from the knowledge base in two directions, and this module
looks for both:

* **Too loose.** A node admits keys no document declares, or a subschema is a
  tautology (``{}``, ``True``, ``additionalProperties: true``). Those are the
  *hard* findings: the contract stops describing the data and starts accepting
  anything.
* **Never exercised.** A declared property, enum value, JSON type or
  ``oneOf``/``anyOf`` branch that no document of the knowledge base reaches.
  Those are the *soft* findings: they are either tightened or recorded in
  :data:`JUSTIFIED_FINDINGS` with the contract that keeps them alive, so a
  stale declaration cannot hide behind a silent schema.

The audit reads the same merged schemas the validators use
(:func:`mordheim_knowledge.editorial_schemas.schema_for`), so what is audited is
exactly what is enforced.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import yaml
from jsonschema import Draft202012Validator

from mordheim_knowledge import editorial_schemas
from mordheim_knowledge.editorial_schemas import EditorialSchemaError, knowledge_root

#: Finding kinds that mean the schema is looser than the data, or declares a
#: definition nothing can reach. The contract is strict when this list is empty.
HARD_FINDINGS = ("tautology", "open_object", "undeclared_key", "dead_definition")

#: Finding kinds that mean the schema declares more than the data exercises.
#: Every one of them must be justified in :data:`JUSTIFIED_FINDINGS`.
SOFT_FINDINGS = ("unused_property", "unused_type", "unused_enum_value", "dead_branch")

#: Declarations kept on purpose although no document uses them today, keyed by
#: ``(schema, kind, path)``. The value is the contract or workflow that keeps
#: the declaration alive; an entry that stops matching a finding is stale and
#: fails the guardian test.
JUSTIFIED_FINDINGS: dict[tuple[str, str, str], str] = {
    # -- vocabularies anchored to the executable layer -------------------
    # The execution contract declares every field of the effect set it builds, not
    # only the ones today's mechanics set: `mordheim_construction.contracts.effect_index`
    # accepts exactly this vocabulary and the guardian test compares it with
    # `fields(EffectSet)`.
    (
        "catalog-mechanics-execution.yaml.schema.json",
        "unused_property",
        "#/$defs/mechanic.parameters",
    ): "fields of EffectSet; the compiler accepts the whole vocabulary",
    (
        "catalog-mechanics-execution.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/mechanic.stacking",
    ): "stacking values of the effect-set compiler; no mechanic stacks by best today",
    # `profiles.yaml` combat traits are executable: the schema mirrors TRAIT_TYPES,
    # so a trait no profile carries is still a trait the compiler implements.
    (
        "profiles.yaml.schema.json",
        "unused_property",
        "#/$defs/profile.combat_traits",
    ): "mirror of the TRAIT_TYPES registry, guarded by its own test",
    (
        "profiles.yaml.schema.json",
        "unused_type",
        "#/$defs/profile.group_size.maximum",
    ): "`int | None` in knowledge_port/profile: the campaign engines branch on `is not None`",
    (
        "defs.schema.json",
        "unused_enum_value",
        "#/$defs/rule_runtime.grant",
    ): "grant values of registry/runtime-schema.yaml, compared by the guardian test",
    (
        "defs.schema.json",
        "unused_enum_value",
        "#/$defs/characteristic_name",
    ): "the nine characteristics of the profile line; a binding may name any of them",
    (
        "defs.schema.json",
        "unused_enum_value",
        "#/$defs/catalog_status",
    ): "`draft` is the editorial state catalog/campaign/README.md prescribes for unconfirmed rules",
    (
        "catalog-rules-implemented-canonical-families.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/family.implemented",
    ): "the classification vocabulary of the audit it documents; every family is YES today",
    # -- vocabularies the campaign engine dispatches on ------------------
    # `post_battle_engine` reads `recipient`, `subject` and `note`; `scenario_rewards`
    # documents `hero_and_henchman_group | leader | hero | manual`.
    (
        "campaign-experience-and-advances.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/award.recipient",
    ): "recipient vocabulary the post-battle engine dispatches on",
    (
        "campaign-exploration-and-income.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/recipient",
    ): "recipient vocabulary the post-battle engine dispatches on",
    (
        "campaign-serious-injuries.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/reward.recipient",
    ): "recipient vocabulary the post-battle engine dispatches on",
    (
        "campaign-serious-injuries.yaml.schema.json",
        "unused_property",
        "#/$defs/miss_games",
    ): "`subject` is read by post_battle_engine._followup_actor",
    (
        "campaign-serious-injuries.yaml.schema.json",
        "unused_property",
        "#/$defs/remove_warrior",
    ): "`subject` and `note` are read by post_battle_engine and post_battle_resolution",
    (
        "campaign-serious-injuries.yaml.schema.json",
        "unused_property",
        "#/$defs/reward",
    ): "`note` is printed by post_battle_engine when a reward carries one",
    (
        "campaign-serious-injuries.yaml.schema.json",
        "unused_property",
        "#/$defs/resources",
    ): "resource kinds the campaign tracks; this document only grants experience",
    # The snake_case characteristic vocabulary is the one the racial maximums and the
    # advance engine use; a document names the characteristics it needs.
    (
        "campaign-experience-and-advances.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/characteristic",
    ): "characteristic vocabulary shared with catalog/rules/racial-maximums.yaml",
    (
        "campaign-exploration-and-income.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/characteristic",
    ): "characteristic vocabulary shared with catalog/rules/racial-maximums.yaml",
    (
        "campaign-hired-swords-and-dramatis.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/characteristic",
    ): "characteristic vocabulary shared with catalog/rules/racial-maximums.yaml",
    (
        "campaign-serious-injuries.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/characteristic_enum",
    ): "characteristic vocabulary shared with catalog/rules/racial-maximums.yaml",
    (
        "campaign-experience-and-advances.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/choose_skill.source",
    ): "skill-source vocabulary the campaign advance follows; today's tables use one source",
    (
        "campaign-experience-and-advances.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/generate_spell.source",
    ): "skill-source vocabulary the campaign advance follows; today's tables use one source",
    (
        "campaign-experience-and-advances.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/promote_henchman.skill_lists.source",
    ): "skill-source vocabulary the campaign advance follows; today's tables use one source",
    (
        "campaign-exploration-and-income.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/characteristic_test.success_when",
    ): "test outcomes the exploration procedure engine resolves",
    (
        "campaign-hired-swords-and-dramatis.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/availability_procedure.success_when",
    ): "test outcomes the availability procedure resolves",
    (
        "campaign-trading-and-rarity.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/allocation_rule.from",
    ): "disposition sources the trading engine resolves; each rule names the one it uses",
    (
        "campaign-post-battle-sequence.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/step.resolves",
    ): "the sibling catalogue documents a step may hand over to; the guardian test derives the enum from the directory",
    # -- shapes the two profile families share --------------------------
    # A Hired Sword and a Dramatis Persona declare the same profile shape; a
    # declaration unused in one family is exercised by the other (`hire_eligibility`
    # reads the equipment `rules`, `counts_as.quantity` appears on Long Daggers).
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_property",
        "#/$defs/unique_equipment",
    ): "equipment shape shared with the Dramatis Persona family, which uses it",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_property",
        "#/$defs/counts_as",
    ): "quantity is used by the Dramatis Persona catalogue (Long Daggers counts as two swords)",
    (
        "hireling-profile-dramatis-personae.yaml.schema.json",
        "unused_property",
        "#/$defs/unique_equipment",
    ): "equipment shape shared with the Hired Sword family, which uses it",
    (
        "hireling-profile-dramatis-personae.yaml.schema.json",
        "dead_branch",
        "#/$defs/unique_equipment.counts_as",
    ): "counts_as accepts a plain id or the context object; the Hired Sword family uses the plain id",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_property",
        "#/$defs/unresolved_reference",
    ): "editorial annotation of a reference the ingest workflow could not resolve",
    (
        "hireling-profile-dramatis-personae.yaml.schema.json",
        "unused_property",
        "#/$defs/inline_rule",
    ): "rule shape shared with the Hired Sword family and with rules.yaml",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_property",
        "#/$defs/inline_rule",
    ): "`mechanics` is read by knowledge_port when a profile rule is executable",
    # -- optional provenance ------------------------------------------
    (
        "campaign-trading-and-rarity.yaml.schema.json",
        "unused_property",
        "#/$defs/allocation",
    ): "provenance is optional on the allocation table; the rules below it carry their own",
    (
        "campaign-trading-and-rarity.yaml.schema.json",
        "unused_property",
        "#/$defs/rarity",
    ): "provenance is optional on the rarity table; the records below it carry their own",
    # -- shape the staged trees already use -------------------------------
    # `grade: 2b`, `fixed_item.notes`, the starting `experience` of a hireling
    # profile and the printed `eligibility.note` are the four extensions the
    # promotion of `sources/2B` needs. Each one follows a pattern the KB already
    # has (the grade vocabulary, the equipment-list `notes`, the `experience` of
    # `profiles.yaml`, the `restriction.note` of the trading post), and each one is
    # exercised by a staged document today: the gate that pins what the staged
    # catalogues extend is the same decision. They show up here because the audit
    # measures the contract against the *committed* knowledge base only; the
    # staging trees are the documents that will carry them at promotion.
    (
        "hireling-profile-dramatis-personae.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/profile.grade",
    ): "grade of the 2B sources, exercised by the staged catalogues",
    (
        "hireling-profile-dramatis-personae.yaml.schema.json",
        "unused_enum_value",
        "$.grade",
    ): "grade of the 2B sources, exercised by the staged catalogues",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_enum_value",
        "#/$defs/profile.grade",
    ): "grade of the 2B sources, exercised by the staged catalogues",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_enum_value",
        "$.grade",
    ): "grade of the 2B sources, exercised by the staged catalogues",
    (
        "hireling-profile-dramatis-personae.yaml.schema.json",
        "unused_property",
        "#/$defs/fixed_item",
    ): "`notes` is what the 2B hirelings write on a referenced item today",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_property",
        "#/$defs/fixed_item",
    ): "`notes` is what the 2B hirelings write on a referenced item today",
    (
        "hireling-profile-hired-sword.yaml.schema.json",
        "unused_property",
        "#/$defs/profile",
    ): "starting `experience`, the name `profiles.yaml` gives the same field",
    (
        "campaign-hired-swords-and-dramatis.yaml.schema.json",
        "unused_property",
        "#/$defs/eligibility",
    ): "printed hiring rule, the role `restriction.note` plays in the trading post",
}

#: How many document labels a finding prints before summarising the rest.
_DOCUMENT_SAMPLE = 3


@dataclass(frozen=True)
class Finding:
    """One declaration of the contract that the documents do or do not back."""

    schema: str
    kind: str
    path: str
    detail: str
    documents: tuple[str, ...] = ()

    @property
    def hard(self) -> bool:
        return self.kind in HARD_FINDINGS

    def __str__(self) -> str:
        where = f"{self.schema}{self.path}"
        sample = ", ".join(self.documents[:_DOCUMENT_SAMPLE])
        if len(self.documents) > _DOCUMENT_SAMPLE:
            sample += f", +{len(self.documents) - _DOCUMENT_SAMPLE} more"
        tail = f" [{sample}]" if sample else ""
        return f"{self.kind}: {where} — {self.detail}{tail}"


def _key(value: Any) -> str:
    """Hashable, readable identity of a document value."""
    if isinstance(value, str):
        return f"str:{value}"
    return f"{type(value).__name__}:{value!r}"


def _json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _document_type(_: Any) -> str:
    return "object"


class _SchemaAudit:
    """Observed vocabulary of the documents claimed by one document schema."""

    def __init__(self, schema_path: str) -> None:
        self.schema_path = schema_path
        self.schema = editorial_schemas.schema_for(schema_path)
        self.defs: dict[str, Any] = self.schema.get("$defs") or {}
        # path -> evidence collected while walking the documents
        self.declared_properties: dict[str, set[str]] = defaultdict(set)
        self.seen_properties: dict[str, set[str]] = defaultdict(set)
        self.undeclared_keys: dict[str, Counter[str]] = defaultdict(Counter)
        self.open_nodes: dict[str, str] = {}
        self.tautologies: set[str] = set()
        self.declared_types: dict[str, set[str]] = defaultdict(set)
        self.seen_types: dict[str, set[str]] = defaultdict(set)
        self.declared_values: dict[str, set[str]] = defaultdict(set)
        self.seen_values: dict[str, set[str]] = defaultdict(set)
        self.branch_hits: dict[str, Counter[int]] = defaultdict(Counter)
        self.branch_counts: dict[str, int] = {}
        self.documents: dict[str, set[str]] = defaultdict(set)

    # -- walking ---------------------------------------------------------

    def observe(self, payload: dict, label: str) -> None:
        self._walk(
            self.schema, payload, "$", label, composed=False, conditional=False, closed=False
        )

    def _name(self, path: str, label: str) -> None:
        self.documents[path].add(label)

    @lru_cache(maxsize=None)
    def _branch_validator(self, branch_json: str) -> Draft202012Validator:
        branch = json.loads(branch_json)
        return Draft202012Validator({"$defs": self.defs, "allOf": [branch]})

    def _walk(
        self,
        node: Any,
        value: Any,
        path: str,
        label: str,
        *,
        composed: bool,
        conditional: bool,
        closed: bool,
    ) -> None:
        if node is True or node == {}:
            self.tautologies.add(path)
            return
        if node is False:
            return
        if not isinstance(node, dict):
            return
        if "$ref" in node:
            name = str(node["$ref"]).rsplit("/", 1)[-1]
            target = self.defs.get(name)
            if target is None:
                raise EditorialSchemaError(f"{self.schema_path}: unresolved reference to {name!r}")
            # Evidence is aggregated by definition, not by use site: the question a
            # finding answers is "does any document back this declaration?".
            self._walk(
                target,
                value,
                f"#/$defs/{name}",
                label,
                composed=composed,
                conditional=conditional,
                closed=closed or _closes(node),
            )
            siblings = {key: item for key, item in node.items() if key != "$ref"}
            if siblings:
                self._walk(
                    siblings,
                    value,
                    path,
                    label,
                    composed=composed,
                    conditional=conditional,
                    closed=closed or _closes(node),
                )
            return

        self._name(path, label)
        vocabulary = node.get("enum")
        if "const" in node:
            vocabulary = [node["const"]] if vocabulary is None else vocabulary
        if vocabulary is not None and not conditional:
            declared = {_key(item) for item in vocabulary}
            self.declared_values[path] |= declared
            observed = _key(value)
            if observed in declared:
                self.seen_values[path].add(observed)
            else:
                self.seen_values[path].add(f"<not declared: {observed}>")
        if not conditional:
            declared_types = node.get("type")
            if isinstance(declared_types, str):
                self.declared_types[path].add(declared_types)
            elif isinstance(declared_types, list):
                self.declared_types[path].update(str(item) for item in declared_types)
            self.seen_types[path].add(_json_type(value))

        if isinstance(value, dict):
            self._walk_object(
                node, value, path, label, composed=composed, conditional=conditional, closed=closed
            )
        elif isinstance(value, list):
            items = node.get("items")
            if isinstance(items, dict):
                for item in value:
                    self._walk(
                        items,
                        item,
                        f"{path}[]",
                        label,
                        composed=False,
                        conditional=conditional,
                        closed=False,
                    )
            elif isinstance(items, list):
                for index, item in enumerate(value):
                    if index < len(items):
                        self._walk(
                            items[index],
                            item,
                            f"{path}[{index}]",
                            label,
                            composed=False,
                            conditional=conditional,
                            closed=False,
                        )

        branches_closed = closed or _closes(node)
        for keyword in ("allOf",):
            for index, branch in enumerate(node.get(keyword) or []):
                self._walk(
                    branch,
                    value,
                    f"{path}|{keyword}[{index}]",
                    label,
                    composed=True,
                    conditional=False,
                    closed=branches_closed,
                )
        for keyword in ("oneOf", "anyOf"):
            branches = node.get(keyword)
            if not isinstance(branches, list):
                continue
            self.branch_counts[path] = len(branches)
            for index, branch in enumerate(branches):
                validator = self._branch_validator(json.dumps(branch, sort_keys=True))
                matched = not any(True for _ in validator.iter_errors(value))
                if matched:
                    self.branch_hits[path][index] += 1
                # A branch that matches constrains the value like any other node, so
                # its vocabulary is exercised; a branch that does not match is not
                # evidence of anything.
                self._walk(
                    branch,
                    value,
                    f"{path}|{keyword}[{index}]",
                    label,
                    composed=True,
                    conditional=not matched,
                    closed=branches_closed,
                )
        for keyword in ("if", "then", "else"):
            branch = node.get(keyword)
            if isinstance(branch, dict):
                self._walk(
                    branch,
                    value,
                    f"{path}|{keyword}",
                    label,
                    composed=True,
                    conditional=True,
                    closed=branches_closed,
                )

    def _walk_object(
        self,
        node: dict,
        value: dict,
        path: str,
        label: str,
        *,
        composed: bool,
        conditional: bool,
        closed: bool,
    ) -> None:
        properties = node.get("properties") or {}
        patterns = node.get("patternProperties") or {}
        additional = node.get("additionalProperties")
        object_node = bool(properties or patterns or "additionalProperties" in node or node.get("type") == "object")
        if not object_node:
            return
        if not conditional:
            self.declared_properties[path] |= set(properties)
            self.seen_properties[path] |= set(value)
            self.declared_types[path].add("object")
            self.seen_types[path].add("object")
            # Only then does the node leave keys undescribed: a schema, a ``false``
            # or a ``patternProperties`` in ``additionalProperties`` describes them.
            if not closed and (additional is None or additional is True):
                unfixed = sorted(
                    key
                    for key in value
                    if key not in properties
                    and not any(_matches(pattern, key) for pattern in patterns)
                )
                if unfixed:
                    self.undeclared_keys[path].update(unfixed)
        if not conditional:
            # An ``if`` condition reads the keys it constrains and must tolerate the
            # rest, so openness is only a finding when the node shapes real data.
            if additional is True:
                self.open_nodes.setdefault(path, "additionalProperties: true admits any key")
            elif additional is None and properties and not closed and not composed:
                self.open_nodes.setdefault(
                    path, "properties declared without additionalProperties: false"
                )
        for name, subschema in properties.items():
            if name in value:
                self._walk(
                    subschema,
                    value[name],
                    f"{path}.{name}",
                    label,
                    composed=False,
                    conditional=conditional,
                    closed=False,
                )
        for name, subschema in patterns.items():
            for key in value:
                if _matches(name, key):
                    self._walk(
                        subschema,
                        value[key],
                        f"{path}.{{{name}}}",
                        label,
                        composed=False,
                        conditional=conditional,
                        closed=False,
                    )
        if isinstance(additional, dict):
            for key in value:
                if key not in properties and not any(_matches(pattern, key) for pattern in patterns):
                    self._walk(
                        additional,
                        value[key],
                        f"{path}.*",
                        label,
                        composed=False,
                        conditional=conditional,
                        closed=False,
                    )

    # -- findings --------------------------------------------------------

    def hard_findings(self) -> list[Finding]:
        """Findings that mean the schema admits data no document declares."""
        found: list[Finding] = []
        for path in sorted(self.tautologies):
            found.append(
                Finding(
                    self.schema_path,
                    "tautology",
                    path,
                    "subschema accepts any value, so it constrains nothing",
                    tuple(sorted(self.documents[path])),
                )
            )
        for path, reason in sorted(self.open_nodes.items()):
            found.append(
                Finding(
                    self.schema_path,
                    "open_object",
                    path,
                    reason,
                    tuple(sorted(self.documents[path])),
                )
            )
        for path, keys in sorted(self.undeclared_keys.items()):
            found.append(
                Finding(
                    self.schema_path,
                    "undeclared_key",
                    path,
                    "keys present in the documents and described nowhere: "
                    + ", ".join(sorted(keys)),
                    tuple(sorted(self.documents[path])),
                )
            )
        return found

    def declared(self) -> set[tuple[str, str]]:
        """Every ``(kind, path)`` at which this schema declares vocabulary."""
        return (
            {("unused_property", path) for path in self.declared_properties}
            | {("unused_type", path) for path in self.declared_types}
            | {("unused_enum_value", path) for path in self.declared_values}
            | {("dead_branch", path) for path in self.branch_counts}
        )

    def unexercised(self) -> list[tuple[str, str, str]]:
        """``(kind, path, detail)`` of every declaration no document reaches."""
        found: list[tuple[str, str, str]] = []
        for path, declared in sorted(self.declared_properties.items()):
            missing = sorted(declared - self.seen_properties[path])
            if missing:
                found.append(
                    ("unused_property", path, "declared property never present: " + ", ".join(missing))
                )
        for path, declared in sorted(self.declared_types.items()):
            missing = sorted(declared - self.seen_types[path])
            if missing:
                found.append(
                    ("unused_type", path, "declared type never observed: " + ", ".join(missing))
                )
        for path, declared in sorted(self.declared_values.items()):
            missing = sorted(declared - self.seen_values[path])
            if missing:
                found.append(
                    (
                        "unused_enum_value",
                        path,
                        "declared value never present: " + ", ".join(missing),
                    )
                )
        for path, total in sorted(self.branch_counts.items()):
            missing = [str(index) for index in range(total) if not self.branch_hits[path][index]]
            if missing:
                found.append(
                    ("dead_branch", path, "branch never selected: " + ", ".join(missing))
                )
        return found


def _closes(node: dict) -> bool:
    """Whether a node closes the key set of the value it validates."""
    additional = node.get("additionalProperties")
    return additional is False or isinstance(additional, dict) or bool(node.get("patternProperties"))


def _matches(pattern: str, key: str) -> bool:
    try:
        return re.search(pattern, key) is not None
    except re.error:
        return False


def _documents(root: Path) -> dict[str, list[tuple[str, dict]]]:
    """``schema file -> [(document label, payload)]`` of every covered document."""
    by_schema: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for collection in editorial_schemas.COLLECTIONS:
        for band_yaml in sorted((root / "bands" / collection).glob("*/band.yaml")):
            for document, schema_path in editorial_schemas.BAND_SCHEMAS.items():
                path = band_yaml.parent / document
                by_schema[schema_path].append(
                    (f"{collection}/{band_yaml.parent.name}/{document}", _read(path))
                )
    for document, schema_path in editorial_schemas.document_schemas(root):
        by_schema[schema_path].append((document, _read(root / document)))
    return by_schema


def _definition_references(node: Any) -> set[str]:
    """Names of the definitions one schema node references."""
    found: set[str] = set()
    if isinstance(node, dict):
        reference = node.get("$ref")
        if isinstance(reference, str) and "#/$defs/" in reference:
            found.add(reference.rpartition("/")[2])
        for value in node.values():
            found |= _definition_references(value)
    elif isinstance(node, list):
        for value in node:
            found |= _definition_references(value)
    return found


def _reachable_definitions(
    schema: dict, shared_definitions: dict[str, Any]
) -> tuple[set[str], set[str]]:
    """``(local, shared)`` definition names a document schema can reach from its body.

    The walk crosses the two pools as the references do: a local definition may
    reference a shared one and the other way round.
    """
    local_definitions = schema.get("$defs") or {}
    body = {key: value for key, value in schema.items() if key != "$defs"}
    local_seen: set[str] = set()
    shared_seen: set[str] = set()
    pending = _definition_references(body)
    while pending:
        name = pending.pop()
        # A name lives in exactly one pool: ``schema_for`` refuses to merge a
        # document schema that redefines a shared definition.
        definitions = local_definitions if name in local_definitions else shared_definitions
        seen = local_seen if definitions is local_definitions else shared_seen
        if name in seen or name not in definitions:
            continue
        seen.add(name)
        pending |= _definition_references(definitions[name]) - seen
    return local_seen, shared_seen


def dead_definitions() -> list[Finding]:
    """Definitions of the contract no document schema can reach.

    A definition nobody references is dead weight: it can drift from the
    documents for ever without a test noticing.
    """
    directory = editorial_schemas.contract_directory()
    schemas = {name: _read(directory / name) for name in editorial_schemas.schema_files()}
    shared_definitions = schemas[editorial_schemas.DEFINITIONS_FILE].get("$defs") or {}
    reachable_shared: set[str] = set()
    findings: list[Finding] = []
    for schema_path, document in sorted(schemas.items()):
        if schema_path == editorial_schemas.DEFINITIONS_FILE:
            continue
        local_definitions = document.get("$defs") or {}
        reachable_local, shared_of_document = _reachable_definitions(document, shared_definitions)
        reachable_shared |= shared_of_document
        dead = sorted(set(local_definitions) - reachable_local)
        if dead:
            findings.append(
                Finding(
                    schema_path,
                    "dead_definition",
                    ", ".join(dead),
                    "definition declared and referenced by nobody in this schema",
                )
            )
    dead_shared = sorted(set(shared_definitions) - reachable_shared)
    if dead_shared:
        findings.append(
            Finding(
                editorial_schemas.DEFINITIONS_FILE,
                "dead_definition",
                ", ".join(dead_shared),
                "definition declared and referenced by no document schema",
            )
        )
    return findings


def _read(path: Path) -> dict:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:  # pragma: no cover - the loader reports this first
        raise EditorialSchemaError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EditorialSchemaError(f"{path} is not a mapping")
    return payload


def audit_strictness(root: Path | None = None) -> list[Finding]:
    """Every declaration of the contract that the documents back or contradict.

    A definition of ``defs.schema.json`` is one declaration shared by several
    document schemas, so it is reported once — with the pooled evidence of every
    document that uses it — and only when no document of the knowledge base
    reaches it.
    """
    base = root or knowledge_root()
    audits: list[_SchemaAudit] = []
    for schema_path, documents in sorted(_documents(base).items()):
        audit = _SchemaAudit(schema_path)
        for label, payload in documents:
            audit.observe(payload, label)
        audits.append(audit)

    findings: list[Finding] = dead_definitions()
    declared_by: dict[tuple[str, str], set[str]] = defaultdict(set)
    reported_by: dict[tuple[str, str], set[str]] = defaultdict(set)
    pooled_documents: dict[tuple[str, str], set[str]] = defaultdict(set)
    details: dict[tuple[str, str], str] = {}
    for audit in audits:
        findings.extend(audit.hard_findings())
        for kind, path in audit.declared():
            if _shared_definition(path):
                declared_by[(kind, path)].add(audit.schema_path)
        for kind, path, detail in audit.unexercised():
            if not _shared_definition(path):
                findings.append(
                    Finding(
                        audit.schema_path,
                        kind,
                        path,
                        detail,
                        tuple(sorted(audit.documents[path])),
                    )
                )
                continue
            reported_by[(kind, path)].add(audit.schema_path)
            pooled_documents[(kind, path)] |= audit.documents[path]
            details.setdefault((kind, path), detail)
    for key in sorted(reported_by):
        if reported_by[key] != declared_by[key]:
            continue
        kind, path = key
        findings.append(
            Finding(
                editorial_schemas.DEFINITIONS_FILE,
                kind,
                path,
                details[key],
                tuple(sorted(pooled_documents[key])),
            )
        )
    return findings


@lru_cache(maxsize=1)
def _shared_definition_names() -> frozenset[str]:
    """Names declared by ``defs.schema.json``, i.e. shared by several schemas."""
    definitions = editorial_schemas.schema_for(editorial_schemas.DEFINITIONS_FILE).get("$defs")
    return frozenset(definitions or {})


def _shared_definition(path: str) -> bool:
    """Whether an evidence path names a definition of ``defs.schema.json``."""
    prefix = "#/$defs/"
    if not path.startswith(prefix):
        return False
    name = path[len(prefix) :]
    for separator in (".", "|", "["):
        name = name.split(separator, 1)[0]
    return name in _shared_definition_names()


def hard_findings(findings: Iterable[Finding]) -> list[Finding]:
    return [finding for finding in findings if finding.hard]


def unjustified_findings(findings: Iterable[Finding]) -> list[Finding]:
    """Findings that are neither hard nor recorded in the allowlist."""
    known = {(schema, kind, path) for schema, kind, path in JUSTIFIED_FINDINGS}
    return [
        finding
        for finding in findings
        if not finding.hard and (finding.schema, finding.kind, finding.path) not in known
    ]


def stale_justifications(findings: Iterable[Finding]) -> list[tuple[str, str, str]]:
    """Allowlist entries that no longer match a finding."""
    observed = {(finding.schema, finding.kind, finding.path) for finding in findings}
    return sorted(entry for entry in JUSTIFIED_FINDINGS if entry not in observed)
