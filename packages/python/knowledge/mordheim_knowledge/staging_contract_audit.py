"""Editorial contract audit of the staged warband packages.

The two staging trees — ``sources/2A`` and ``sources/2B`` — hold warbands that are
modelled *before* they are promoted into the knowledge base, and they sit outside
the coverage guardian of ``tests/python/knowledge/test_editorial_schemas.py``. That is
exactly the window in which the shape of a package drifts, so this module
answers the question the contract can answer about them:

* :func:`schema_deviations` validates the four documents of every package with
  the same JSON Schemas the active knowledge base is validated with — unknown
  fields, wrong types, missing required keys, violated patterns and the
  cross-field invariants the contract encodes (identity vs the directory, a
  source reference complete, an unpriced equipment entry carrying its note, an
  effect without a binding carrying its reason).
* :func:`novel_open_values` reports the values a staging tree uses in the fields
  the contract deliberately types loosely (``status``, ``sources[].manual``,
  ``categories``, ``grade``, ``profiles[].source_path``) and that never appear in
  the active knowledge base.

* :func:`catalogue_deviations` does the same for the staged *catalogues* — the
  items, the Hired Sword and Dramatis profiles, the magic, market and campaign
  documents of ``sources/<tree>/catalog/`` — validated
  against the schema of the KB document that will claim them at promotion. That
  destination is the one ``sources/2B/promotion-schema-plan.md`` declares, and the
  deviations here are its extension classes; the promotion plan is a document, so
  this pass is what keeps it from going stale.
* :func:`naming_drift` reports the files ``tools/knowledge/maintenance/normalize_names.py --check`` would
  rewrite, because the title-case policy of ``name`` / ``name_i18n.es`` is a gate
  for the knowledge base (``tests/python/knowledge/test_name_normalization.py``) but not
  for the staging trees — one of the two canonical-formatting rules the staging
  is not already held to.
* :func:`collection_shape_drift` reports the flow collections of the keys the
  knowledge base writes in block form (``source_path``, ``equipment_lists``,
  ``rule_ids``, ``skill_access``, ``source``, ``characteristics``, ``name_i18n``,
  ``combat_traits``) — the other one. A promotion copy that writes one of them as
  ``[a, b]`` carries the KB's facts in a shape the KB does not have, so the merge
  shows a diff that is nothing but shape; ``staging_promotion.shape_pass`` is the
  repair and ``tests/python/knowledge/test_staging_collection_shape.py`` is its gate.

The passes answer different questions, and a green schema run is not a promotion
certificate: the first says the shape is the promoted shape, the second says how
far the values still are from the dialect the knowledge base speaks.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field as dataclass_field
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator

import yaml

from mordheim_knowledge.editorial_schemas import BAND_SCHEMAS, validator_for
from mordheim_knowledge.staging_promotion import flow_collections

#: Trees the audit reads, relative to the checkout root.
TREE_DIRECTORIES = {
    "KB": Path("sources") / "knowledge",
    "2A": Path("sources") / "2A",
    "2B": Path("sources") / "2B",
}

#: Trees audited by default: the staged ones.
STAGED_TREES = ("2A", "2B")

#: Tree the open-field vocabulary is compared against.
REFERENCE_TREE = "KB"

#: ``bands/<collection>/<band-id>/`` packages.
PACKAGE_GLOB = "bands/*/*"

#: ``band.yaml`` is keyed by ``id``, the other three documents by ``band_id``.
IDENTITY_KEY = {"band.yaml": "id"}

_INDEX = re.compile(r"/(\d+)(?=/|$)")
_BRANCH = re.compile(r"is not valid under any of the given schemas")


class StagingAuditError(ValueError):
    """The checkout layout does not hold the staging trees."""


def tree_root(name: str) -> Path:
    """``sources/<name>`` located from the package location."""
    try:
        relative = TREE_DIRECTORIES[name]
    except KeyError as exc:
        raise StagingAuditError(f"Unknown tree {name!r}; expected one of {sorted(TREE_DIRECTORIES)}") from exc
    for parent in Path(__file__).resolve().parents:
        candidate = parent / relative
        if candidate.is_dir():
            return candidate
    raise StagingAuditError(f"Cannot find the staged tree {relative.as_posix()}")


def checkout_root() -> Path:
    """The repository root, located from ``sources/<tree>``."""
    return tree_root(REFERENCE_TREE).parents[1]


def read_document(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def packages(root: Path) -> list[Path]:
    """Every ``bands/<collection>/<band-id>/`` directory declaring a ``band.yaml``."""
    return sorted(path for path in root.glob(PACKAGE_GLOB) if (path / "band.yaml").is_file())


def normalize_path(parts: Iterable[Any]) -> str:
    """``roster/members/3/profile_id`` → ``roster/members[]/profile_id``.

    The signature of a deviation must survive the number of members a band has.
    """
    return _INDEX.sub("/[]", "/".join(str(part) for part in parts)) or "(root)"


def source_references(node: Any) -> Iterator[dict]:
    """Every ``source_ref`` of a document: a mapping carrying ``manual`` and ``section``."""
    if isinstance(node, dict):
        if "manual" in node and "section" in node:
            yield node
        for value in node.values():
            yield from source_references(value)
    elif isinstance(node, list):
        for value in node:
            yield from source_references(value)


@dataclass
class SchemaDeviation:
    """One ``(document, path, kind, message)`` signature and the packages showing it."""

    document: str
    path: str
    kind: str
    message: str
    packages: set[str] = dataclass_field(default_factory=set)
    keys: Counter[str] = dataclass_field(default_factory=Counter)
    count: int = 0

    @property
    def signature(self) -> tuple[str, str, str, str]:
        return (self.document, self.path, self.kind, self.message)

    def add(self, package: str, keys: Iterable[str], count: int = 1) -> None:
        self.packages.add(package)
        self.keys.update(keys)
        self.count += count

    def __str__(self) -> str:
        keys = f" keys={sorted(self.keys)}" if self.keys else ""
        return f"{len(self.packages)}x {self.document}:{self.path} [{self.kind}] {self.message}{keys}"


class _OwnDeviation:
    """A deviation raised here rather than by jsonschema, shaped like an error."""

    def __init__(self, message: str, path: list[Any], validator: str) -> None:
        self.message = message
        self.absolute_path = path
        self.validator = validator


def _short_message(error: Any) -> tuple[str, str]:
    """``(kind, message)``, collapsing the branches jsonschema prints in full."""
    if _BRANCH.search(error.message):
        return error.validator, f"is not valid under any of the given schemas ({error.validator})"
    return error.validator, error.message


def _extra_keys(error: Any) -> list[str]:
    if error.validator != "additionalProperties":
        return []
    return sorted(re.findall(r"'([^']+)'", error.message))


def deviation_class(deviation: SchemaDeviation) -> str:
    """``family path kind detail`` — one line per promotion decision.

    The detail is the unexpected-key vocabulary, or the value an ``enum`` or a
    ``required`` names, because each of those is a decision the promotion has to
    take. The remaining validators (``pattern``, ``const``, ``type``,
    ``minItems``) collapse into one class each however many documents show them,
    so another record with the same defect does not look like a new decision.
    """
    detail = "+".join(sorted(deviation.keys))
    if not detail and deviation.kind in ("enum", "required"):
        match = re.search(r"'([^']+)'", deviation.message)
        detail = match.group(1) if match else ""
    return " ".join(part for part in (deviation.document, deviation.path, deviation.kind, detail) if part)


def package_errors(directory: Path) -> list[tuple[Any, str]]:
    """``(error, document)`` of one staged package, missing documents included."""
    found: list[tuple[Any, str]] = []
    for document, schema_path in BAND_SCHEMAS.items():
        path = directory / document
        if not path.is_file():
            found.append((_OwnDeviation(f"{document} is missing", ["/"], "missing-document"), document))
            continue
        payload = read_document(path)
        if not isinstance(payload, dict):
            found.append((_OwnDeviation("the document must be a mapping", ["/"], "type"), document))
            continue
        key = IDENTITY_KEY.get(document, "band_id")
        declared = payload.get(key)
        if str(declared or "") != directory.name:
            found.append(
                (
                    _OwnDeviation(
                        f"{key} {declared!r} does not match the directory {directory.name!r}",
                        ["/", key],
                        "identity",
                    ),
                    document,
                )
            )
        for error in validator_for(schema_path).iter_errors(payload):
            found.append((error, document))
    return found


def schema_deviations(root: Path) -> list[SchemaDeviation]:
    """Every schema deviation of a tree, grouped by signature and most widespread first."""
    found: dict[tuple[str, str, str, str], SchemaDeviation] = {}
    for directory in packages(root):
        package = f"{directory.parent.name}/{directory.name}"
        for error, document in package_errors(directory):
            kind, message = _short_message(error)
            deviation = SchemaDeviation(document, normalize_path(error.absolute_path), kind, message)
            found.setdefault(deviation.signature, deviation).add(package, _extra_keys(error))
    return sorted(found.values(), key=lambda deviation: (-len(deviation.packages), deviation.document, deviation.path))


# --------------------------------------------------------------------------- #
# Open-field vocabulary
# --------------------------------------------------------------------------- #


def _status(payload: dict) -> Iterator[Any]:
    yield payload.get("status")


def _categories(payload: dict) -> Iterator[Any]:
    yield from payload.get("categories") or []


def _grade(payload: dict) -> Iterator[Any]:
    yield payload.get("grade")


def _manuals(payload: dict) -> Iterator[Any]:
    yield from (entry.get("manual") for entry in source_references(payload))


def _source_path_root(payload: dict) -> Iterator[Any]:
    for profile in payload.get("profiles") or []:
        path = profile.get("source_path") or []
        yield path[0] if path else None


@dataclass(frozen=True)
class OpenField:
    """A field the contract types loosely, with the document that carries it."""

    label: str
    document: str
    extract: Callable[[dict], Iterator[Any]]


#: Fields the contract leaves open, listed once per document that carries them.
#: Several documents carry the same ``source_ref``, so a label may repeat; the
#: counters below aggregate by label, which is the granularity the report wants.
OPEN_FIELDS: tuple[OpenField, ...] = (
    OpenField("status", "band.yaml", _status),
    OpenField("categories[]", "band.yaml", _categories),
    OpenField("grade", "band.yaml", _grade),
    OpenField("sources[].manual", "band.yaml", _manuals),
    OpenField("profiles[].source_path[0]", "profiles.yaml", _source_path_root),
    OpenField("sources[].manual", "profiles.yaml", _manuals),
    OpenField("sources[].manual", "equipment-access.yaml", _manuals),
    OpenField("sources[].manual", "special-rules.yaml", _manuals),
)


def open_field_values(root: Path) -> dict[str, Counter[str]]:
    """``{field: Counter(value)}`` of the fields the contract leaves open."""
    counters: dict[str, Counter[str]] = {field.label: Counter() for field in OPEN_FIELDS}
    for directory in packages(root):
        for field in OPEN_FIELDS:
            path = directory / field.document
            if not path.is_file():
                continue
            payload = read_document(path)
            if not isinstance(payload, dict):
                continue
            counters[field.label].update(label for label in map(_label, field.extract(payload)))
    return counters


def _label(value: Any) -> str:
    """Readable, hashable rendering of a value (`null` rather than `None`)."""
    return "null" if value is None else str(value)


def novel_open_values(root: Path, reference: Path | None = None) -> dict[str, dict[str, int]]:
    """Open-field values of a tree that never appear in the reference tree."""
    known = open_field_values(reference or tree_root(REFERENCE_TREE))
    return {
        label: {value: count for value, count in sorted(values.items()) if value not in known[label]}
        for label, values in open_field_values(root).items()
        if any(value not in known[label] for value in values)
    }


#: Open-field values the staged trees introduce on purpose, each with the decision
#: that sanctions it. A value earns its place here one of two ways: the KB already
#: carries it somewhere else (``2a`` is the grade of the hired-swords and dramatis
#: catalogues of the active KB) or the value is a new *name*, not a new field — a
#: source id the registry now carries, a grade a new source pack needs so the
#: grades stay auditable apart.
ACCEPTED_OPEN_VALUES: dict[str, dict[str, str]] = {
    "categories[]": {
        "2a": "Grade of the mordheimer.net grade-2a warbands; the KB already grades its "
        "hired-swords and dramatis catalogues `2a`.",
        "2b": "Grade of the 2B sources, kept apart from `2a` the way the grade contract "
        "requires ('kept apart so a source change stays auditable').",
    },
    "grade": {
        "2a": "Same grade as `categories[]`; the band and its hirelings carry one grade.",
        "2b": "Same grade as `categories[]`; the band and its hirelings carry one grade.",
    },
}


def registered_source_ids() -> set[str]:
    """The ids ``registry/sources.yaml`` registers: the vocabulary of `manual`."""
    path = checkout_root() / "sources" / "knowledge" / "registry" / "sources.yaml"
    payload = read_document(path)
    return {str(entry.get("id")) for entry in payload.get("sources") or []}


def open_value_findings(root: Path, reference: Path | None = None) -> dict[str, dict[str, int]]:
    """Novel open-field values that no decision sanctions yet.

    ``manual`` is judged against the registry rather than against KB usage: a
    source id is canonical because it is registered, wherever it is printed. The
    other open fields are judged against the KB vocabulary plus
    ``ACCEPTED_OPEN_VALUES``.
    """
    registered = registered_source_ids()
    findings: dict[str, dict[str, int]] = {}
    for label, values in novel_open_values(root, reference).items():
        sanctioned = ACCEPTED_OPEN_VALUES.get(label, {})
        for value, count in values.items():
            if value in sanctioned:
                continue
            if label.endswith("sources[].manual") and value in registered:
                continue
            findings.setdefault(label, {})[value] = count
    return findings


# --------------------------------------------------------------------------- #
# Staged catalogues against their promotion destination
# ---------------------------------------------------------------------------

#: ``(glob relative to a staging tree, destination schema of the KB document that
#: will claim the file at promotion)``. The destination is the one
#: ``sources/2B/promotion-schema-plan.md`` declares, so this mapping and that plan
#: have to move together.
CATALOGUE_TARGETS: tuple[tuple[str, str], ...] = (
    ("catalog/items/*.yaml", "catalog-items.yaml.schema.json"),
    ("catalog/hirelings/*.yaml", "hireling-profile-hired-sword.yaml.schema.json"),
    ("catalog/hirelings/dramatis-personae/*.yaml", "hireling-profile-dramatis-personae.yaml.schema.json"),
    ("catalog/hired-swords-and-dramatis-*.yaml", "campaign-hired-swords-and-dramatis.yaml.schema.json"),
    ("catalog/magic-2a.yaml", "campaign-magic.yaml.schema.json"),
    ("catalog/magic-2b.yaml", "campaign-magic.yaml.schema.json"),
    ("catalog/trading-post-*.yaml", "campaign-trading-post.yaml.schema.json"),
)

#: Staged files promotion deliberately leaves behind. The plan declares them
#: bookkeeping — every entry they hold already lives in the catalogue that
#: resolved it — so no destination claims them and the coverage gate must not
#: read them as a gap. Each entry carries the decision that keeps it out.
NOT_PROMOTED: tuple[tuple[str, str], ...] = (
    (
        "catalog/items/missing-item-stubs.yaml",
        "The stub list of a completed sweep: the items it tracked were resolved into the catalogues "
        "that own them, and the file is not merged (promotion plan, section 4).",
    ),
)


@dataclass(frozen=True)
class CatalogueFamily:
    """One staged catalogue family and the KB schema its documents become.

    ``label`` names the family the way the report and the promotion plan do: the
    directory of a family that shares one shape, the file of a document whose
    shape is its own.
    """

    label: str
    schema_path: str
    files: tuple[Path, ...]


def catalogue_families(root: Path) -> list[CatalogueFamily]:
    """Every staged catalogue family that is present in a tree.

    A file ``NOT_PROMOTED`` declares is not part of any family: no destination
    claims it, so no schema judges it.
    """
    declared = {path for path, _ in not_promoted_paths(root)}
    families: list[CatalogueFamily] = []
    for pattern, schema_path in CATALOGUE_TARGETS:
        relative = Path(pattern)
        if any(character in pattern for character in "*?"):
            files = tuple(
                sorted(
                    path
                    for path in root.glob(pattern)
                    if path.is_file() and path not in declared
                )
            )
            label = relative.parent.as_posix()
        else:
            path = root / pattern
            files = (path,) if path.is_file() and path not in declared else ()
            label = relative.as_posix()
        if files:
            families.append(CatalogueFamily(label, schema_path, files))
    return families


def not_promoted_paths(root: Path) -> list[Path]:
    """``(path, decision)`` of every staged file promotion leaves behind."""
    found = []
    for relative, decision in NOT_PROMOTED:
        path = root / relative
        if path.is_file():
            found.append((path, decision))
    return found


def catalogue_coverage(root: Path) -> tuple[list[Path], list[CatalogueFamily]]:
    """``(unclaimed files, families)`` of a staging catalogue tree.

    Unclaimed means a YAML the promotion plan does not route anywhere: it would
    reach the knowledge base with no schema that claims it. A file
    ``NOT_PROMOTED`` names is a declared decision, not a gap, so it is not
    reported as unclaimed.
    """
    families = catalogue_families(root)
    claimed = {path for family in families for path in family.files}
    declared = {path for path, _ in not_promoted_paths(root)}
    present = [path for path in sorted((root / "catalog").rglob("*.yaml")) if path.is_file()]
    return [path for path in present if path not in claimed and path not in declared], families


def catalogue_deviations(root: Path) -> list[SchemaDeviation]:
    """Every schema deviation of the staged catalogues, grouped by signature.

    ``document`` is the family (``catalog/items``) so identical extensions group
    across files, and ``packages`` carries the file names that show it.
    """
    found: dict[tuple[str, str, str, str], SchemaDeviation] = {}
    for family in catalogue_families(root):
        for path in family.files:
            payload = read_document(path)
            if not isinstance(payload, dict):
                continue
            for error in validator_for(family.schema_path).iter_errors(payload):
                kind, message = _short_message(error)
                deviation = SchemaDeviation(family.label, normalize_path(error.absolute_path), kind, message)
                found.setdefault(deviation.signature, deviation).add(path.name, _extra_keys(error))
    return sorted(found.values(), key=lambda deviation: (-len(deviation.packages), deviation.document, deviation.path))


# --------------------------------------------------------------------------- #
# The canonical-formatting gate the staging is not held to
# --------------------------------------------------------------------------- #

_NORMALIZER = Path("tools") / "knowledge" / "maintenance" / "normalize_names.py"
_WOULD_CHANGE = re.compile(r"^would change (.+?) \((\d+) name fields?\)", re.MULTILINE)


def naming_drift(root: Path) -> dict[str, int]:
    """``{file relative to the staging tree: name fields}`` of the naming policy.

    ``tools/knowledge/maintenance/normalize_names.py`` is the canonical pass of the knowledge base and
    its ``--check`` is a gate for ``sources/knowledge``; running it over a staging
    tree is what says whether a promotion copy would need rewriting first.
    """
    tool = checkout_root() / _NORMALIZER
    if not tool.is_file():
        raise StagingAuditError(f"Cannot find the name normalizer: {_NORMALIZER.as_posix()}")
    result = subprocess.run(
        [sys.executable, str(tool), "--check", str(root)],
        cwd=checkout_root(),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    output = (result.stdout or "") + (result.stderr or "")
    drift: dict[str, int] = {}
    for match in _WOULD_CHANGE.finditer(output):
        path = Path(match.group(1))
        try:
            key = path.relative_to(root).as_posix()
        except ValueError:
            key = path.as_posix()
        drift[key] = int(match.group(2))
    return dict(sorted(drift.items()))


# --------------------------------------------------------------------------- #
# The collection shape the KB keeps
# --------------------------------------------------------------------------- #


def collection_shape_drift(root: Path) -> dict[str, int]:
    """``{key: non-empty flow collections}`` of the block-collection keys.

    The KB writes ``source_path``, ``equipment_lists``, ``rule_ids``,
    ``skill_access``, ``source``, ``characteristics``, ``name_i18n`` and
    ``combat_traits`` as block collections (1 892 sequences and 7 353 mappings)
    and never as a non-empty flow collection. An empty ``[]`` or ``{}`` is not a
    finding: that is the KB's own shape for "nothing".
    """
    drift: Counter[str] = Counter()
    for path in sorted(root.rglob("*.yaml")):
        if not path.is_file():
            continue
        try:
            found = flow_collections(path.read_text(encoding="utf-8"))
        except ValueError:
            # A flow collection that never closes is malformed YAML, not a shape
            # deviation; the parse of the document reports it on its own pass.
            drift["(unterminated flow collection)"] += 1
            continue
        for collection in found:
            drift[collection.key] += 1
    return dict(sorted(drift.items()))
