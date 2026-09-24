"""Editorial JSON Schemas of the knowledge base documents.

Every maintained YAML document of the knowledge base — the four files of a
warband package, the catalogue families, the hireling and campaign catalogues
and the registry tables — is defined by the versioned contract in
``contracts/knowledge-editorial-v1/``. The schemas are read from disk rather
than duplicated in code, so the contract stays the single source of truth,
exactly as the campaign file does with ``contracts/campaign-file-v5/``.

The document schemas share definitions through a relative ``$ref`` into
``defs.schema.json``. Validation merges those definitions into the document
schema before handing it to ``Draft202012Validator``, so no external schema
registry (and no extra dependency) is needed at run time.

The schemas describe the document envelope: which fields exist, their types and
the editorial conventions the knowledge base follows (ids, i18n blocks, source
references, runtime classification). They complement — and never replace — the
semantic validation of :mod:`mordheim_knowledge.loader`, which stays the
authority on references, ids, the runtime contract and legal construction.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from mordheim_knowledge.loader import knowledge_root

#: Directory of the editorial contract inside ``contracts/``.
CONTRACT_DIRECTORY = "knowledge-editorial-v1"

#: Shared definitions every document schema references.
DEFINITIONS_FILE = "defs.schema.json"

#: Schema of every document of a ``bands/<collection>/<band-id>/`` package.
BAND_SCHEMAS = {
    "band.yaml": "band.yaml.schema.json",
    "profiles.yaml": "profiles.yaml.schema.json",
    "equipment-access.yaml": "equipment-access.yaml.schema.json",
    "special-rules.yaml": "special-rules.yaml.schema.json",
}

#: Documents of a band package, in reading order.
BAND_DOCUMENTS = tuple(BAND_SCHEMAS)

#: Collections whose ``bands/<collection>/`` trees carry band packages.
COLLECTIONS = ("mordheim", "trollheim")

#: ``(glob relative to the knowledge root, schema)`` of the hireling catalogue.
#: One shape per profile family: a Hired Sword and a Dramatis Persona are
#: declared apart because a Dramatis entry may be published while it cannot be
#: modelled yet, which a Hired Sword may not.
HIRELING_DOCUMENTS: tuple[tuple[str, str], ...] = tuple(
    (f"catalog/hirelings/{family}/{name}.yaml", schema)
    for family, schema in (
        ("hired-swords", "hireling-profile-hired-sword.yaml.schema.json"),
        ("dramatis-personae", "hireling-profile-dramatis-personae.yaml.schema.json"),
    )
    for name in ("core", "grade-1a", "grade-1b", "grade-1c", "grade-2a")
) + (
    ("catalog/hirelings/hired-swords/rules.yaml", "hireling-rules.yaml.schema.json"),
    ("catalog/hirelings/dramatis-personae/rules.yaml", "hireling-rules.yaml.schema.json"),
    ("catalog/hirelings/traits.yaml", "hirelings-traits.yaml.schema.json"),
)

#: Documents that live in a covered tree but belong to another workflow, with
#: the reason they are outside this contract. Kept explicit so the coverage test
#: stays strict for everything else; an entry is deleted when its document joins
#: the contract, and the test fails when an entry goes stale.
UNCOVERED_DOCUMENTS: dict[str, str] = {
    "registry/bindings.yaml": (
        "staging binding registry of the 2A/2B ingestion workflow, gated by "
        "tests/python/knowledge/test_binding_registry.py; it joins this contract when the "
        "staged warbands are promoted into the knowledge base"
    ),
}

#: ``(document, schema)`` of the campaign catalogue: each document has its own
#: shape, so each one is listed by path.
CAMPAIGN_DOCUMENTS: tuple[tuple[str, str], ...] = tuple(
    (f"catalog/campaign/{name}.yaml", f"campaign-{name}.yaml.schema.json")
    for name in (
        "experience-and-advances",
        "exploration-and-income",
        "hired-swords-and-dramatis",
        "magic",
        "mutations",
        "post-battle-sequence",
        "recruitment-and-veterans",
        "scenario-rewards",
        "scenarios",
        "serious-injuries",
        "trading-and-rarity",
        "trading-post",
        "warband-rating",
    )
)

#: ``(glob relative to the knowledge root, schema)`` of every remaining document.
#: A glob covers a whole family that shares one shape; the others are listed by
#: path because their shape is their own.
CATALOGUE_DOCUMENTS: tuple[tuple[str, str], ...] = (
    *HIRELING_DOCUMENTS,
    *CAMPAIGN_DOCUMENTS,
    ("catalog/items/*.yaml", "catalog-items.yaml.schema.json"),
    ("catalog/skills/*.yaml", "catalog-skills.yaml.schema.json"),
    ("catalog/rules/conditions.yaml", "catalog-rules-conditions.yaml.schema.json"),
    ("catalog/rules/core-combat.yaml", "catalog-rules-prose.yaml.schema.json"),
    ("catalog/rules/special-rules.yaml", "catalog-rules-prose.yaml.schema.json"),
    ("catalog/rules/racial-maximums.yaml", "catalog-rules-racial-maximums.yaml.schema.json"),
    ("catalog/rules/resolution.yaml", "catalog-rules-resolution.yaml.schema.json"),
    (
        "catalog/rules/implemented-canonical-families.yaml",
        "catalog-rules-implemented-canonical-families.yaml.schema.json",
    ),
    ("catalog/mechanics/close-combat.yaml", "catalog-mechanics-close-combat.yaml.schema.json"),
    ("catalog/mechanics/execution.yaml", "catalog-mechanics-execution.yaml.schema.json"),
    (
        "catalog/mechanics/simulation-mappings.yaml",
        "catalog-mechanics-simulation-mappings.yaml.schema.json",
    ),
    ("registry/aliases.yaml", "registry-aliases.yaml.schema.json"),
    ("registry/collections.yaml", "registry-collections.yaml.schema.json"),
    ("registry/rulesets.yaml", "registry-rulesets.yaml.schema.json"),
    ("registry/sources.yaml", "registry-sources.yaml.schema.json"),
    ("registry/runtime-schema.yaml", "registry-runtime-schema.yaml.schema.json"),
    ("registry/runtime-scope.yaml", "registry-runtime-scope.yaml.schema.json"),
    ("registry/warband-groups.yaml", "registry-warband-groups.yaml.schema.json"),
)

#: Trees this contract covers; the coverage test walks exactly these with
#: ``rglob``, so a document nested one level deeper (the hireling catalogue) is
#: claimed like any other.
CATALOGUE_TREES = (
    "catalog/items",
    "catalog/skills",
    "catalog/rules",
    "catalog/mechanics",
    "catalog/hirelings",
    "catalog/campaign",
    "registry",
)

_DEFINITIONS_PREFIX = f"{DEFINITIONS_FILE}#/$defs/"


class EditorialSchemaError(ValueError):
    """The editorial contract itself cannot be read or is not a valid schema."""


def contract_directory() -> Path:
    """``contracts/knowledge-editorial-v1`` located from the checkout layout."""
    relative = Path("contracts") / CONTRACT_DIRECTORY
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative
        if candidate.is_dir():
            return candidate
    raise EditorialSchemaError(f"Cannot find the editorial contract: contracts/{CONTRACT_DIRECTORY}")


def schema_files() -> tuple[str, ...]:
    """Every schema file of the contract, definitions included."""
    documents = set(BAND_SCHEMAS.values()) | {schema for _, schema in CATALOGUE_DOCUMENTS}
    return tuple(sorted(documents | {DEFINITIONS_FILE}))


def _read(path: Path) -> dict:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EditorialSchemaError(f"Cannot read the editorial contract schema {path.name}: {exc}") from exc
    if not isinstance(document, dict):
        raise EditorialSchemaError(f"Editorial contract schema {path.name} must be a JSON object")
    return document


def _rewrite_references(node: Any) -> Any:
    """Turn ``defs.schema.json#/$defs/x`` references into local ``#/$defs/x``."""
    if isinstance(node, dict):
        return {
            key: (
                f"#/$defs/{value[len(_DEFINITIONS_PREFIX):]}"
                if key == "$ref" and isinstance(value, str) and value.startswith(_DEFINITIONS_PREFIX)
                else _rewrite_references(value)
            )
            for key, value in node.items()
        }
    if isinstance(node, list):
        return [_rewrite_references(item) for item in node]
    return node


@lru_cache(maxsize=None)
def schema_for(schema_path: str) -> dict:
    """The self-contained JSON Schema of one document, keyed by its file name.

    Shared definitions are inlined into ``$defs`` so the schema validates
    without a schema registry; the files on disk stay modular.
    """
    if schema_path not in schema_files():
        raise EditorialSchemaError(
            f"Unknown document schema {schema_path!r}; expected one of {sorted(schema_files())}"
        )
    directory = contract_directory()
    if schema_path == DEFINITIONS_FILE:
        return _read(directory / DEFINITIONS_FILE)
    definitions = _read(directory / DEFINITIONS_FILE).get("$defs")
    if not isinstance(definitions, dict) or not definitions:
        raise EditorialSchemaError(f"{DEFINITIONS_FILE} declares no $defs")
    schema = _rewrite_references(_read(directory / schema_path))
    local = schema.setdefault("$defs", {})
    if not isinstance(local, dict):
        raise EditorialSchemaError(f"{schema_path} declares a non-object $defs")
    clash = sorted(set(local) & set(definitions))
    if clash:
        raise EditorialSchemaError(f"{schema_path} redefines shared definitions: {clash}")
    local.update(_rewrite_references(definitions))
    return schema


@lru_cache(maxsize=None)
def validator_for(schema_path: str) -> Draft202012Validator:
    """Validator of one document, with the contract checked once."""
    schema = schema_for(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise EditorialSchemaError(f"{schema_path} is not a valid Draft 2020-12 schema: {exc}") from exc
    return Draft202012Validator(schema)


def problems_of(schema_path: str, payload: Any) -> list[str]:
    """Schema errors of one already-parsed document, as readable strings."""
    return [
        f"{'/'.join(str(part) for part in error.absolute_path) or '(root)'}: {error.message}"
        for error in sorted(
            validator_for(schema_path).iter_errors(payload),
            key=lambda error: [str(part) for part in error.absolute_path],
        )
    ]


def validate_document(schema_path: str, payload: Any) -> list[str]:
    """Validate a parsed document, reporting an unknown schema as a problem."""
    try:
        return problems_of(schema_path, payload)
    except EditorialSchemaError as exc:
        return [str(exc)]


def _read_document(path: Path) -> tuple[dict | None, list[str]]:
    """Parsed YAML document plus the problems found while reading it."""
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return None, [f"cannot read the document: {exc}"]
    if not isinstance(payload, dict):
        return None, ["the document must be a mapping"]
    return payload, []


def validate_band_package(directory: Path) -> list[str]:
    """Validate the four documents of one ``bands/<collection>/<band>`` package.

    Besides the schemas, every document must still name its own directory:
    ``id`` in ``band.yaml`` and ``band_id`` in the other three.
    """
    band_id = directory.name
    problems: list[str] = []
    for document, schema_path in BAND_SCHEMAS.items():
        path = directory / document
        if not path.is_file():
            problems.append(f"{document}: missing")
            continue
        payload, read_problems = _read_document(path)
        if payload is None:
            problems.extend(f"{document}: {problem}" for problem in read_problems)
            continue
        key = "id" if document == "band.yaml" else "band_id"
        declared = payload.get(key)
        if str(declared or "") != band_id:
            problems.append(
                f"{document}: {key} {declared!r} does not match the directory {band_id!r}"
            )
        problems.extend(f"{document}: {problem}" for problem in problems_of(schema_path, payload))
    return problems


def validate_band_packages(root: Path | None = None) -> list[str]:
    """Validate every band package of the knowledge base, both collections."""
    base = root or knowledge_root()
    problems: list[str] = []
    for collection in COLLECTIONS:
        for band_yaml in sorted((base / "bands" / collection).glob("*/band.yaml")):
            problems.extend(
                f"{collection}/{band_yaml.parent.name}/{problem}"
                for problem in validate_band_package(band_yaml.parent)
            )
    return problems


def document_schemas(root: Path | None = None) -> list[tuple[str, str]]:
    """``(document, schema)`` of every catalogue and registry document on disk.

    The order is the document path, so callers see a stable list. A document is
    claimed by the first pattern that matches it.
    """
    base = root or knowledge_root()
    claimed: dict[str, str] = {}
    for pattern, schema_path in CATALOGUE_DOCUMENTS:
        for path in sorted(base.glob(pattern)):
            claimed.setdefault(path.relative_to(base).as_posix(), schema_path)
    return sorted(claimed.items())


def validate_catalogue_documents(root: Path | None = None) -> list[str]:
    """Validate the catalogue and registry documents against their schemas.

    Returns one ``<document>: <problem>`` string per mismatch.
    """
    base = root or knowledge_root()
    problems: list[str] = []
    for name, schema_path in document_schemas(base):
        payload, read_problems = _read_document(base / name)
        if payload is None:
            problems.extend(f"{name}: {problem}" for problem in read_problems)
            continue
        problems.extend(f"{name}: {problem}" for problem in problems_of(schema_path, payload))
    return problems


def validate_knowledge_base(root: Path | None = None) -> list[str]:
    """Validate every maintained document of the knowledge base."""
    return [*validate_band_packages(root), *validate_catalogue_documents(root)]
