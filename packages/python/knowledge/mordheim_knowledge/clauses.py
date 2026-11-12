"""knowledge: The clause inventory of the knowledge base and its coverage denominator.

An *identity* is one thing the duel runtime must honour and a test may
demonstrate:

* ``core/<rule-id>`` — a core combat rule of ``catalog/rules/core-combat.yaml``;
* ``mechanic/<mechanic-id>`` — a close-combat mechanic (``catalog/mechanics/
  close-combat.yaml``) that the runtime scope does not exclude;
* ``item/<item-id>`` — an item whose ``combat_status`` is ``implemented``;
* ``rule/<collection>/<owner>/<rule-id>/<effect-id>`` — a classified effect of a
  band rule, catalogue skill, or hireling rule (``catalog/hirelings/<owner>/``,
  top-level and inline profile rules alike) whose scope is ``YES``.

A record may break its printed text into *clauses* (``clauses: [{id, scope}]``)
when it has several observable parts, or when part of the printed text is
deliberately outside the duel (``scope: 'NO'``).  A record without clauses is
one obligation: its identity is the clause.  Clauses carry no text and no
evidence: the printed prose is the rule, and the tests declare what they cover
(conformance-scenario ``audit_id``/``covers``, the ``covers`` pytest marker).

This module reads the knowledge base only and imports nothing from the combat
or construction packages.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Iterable, Iterator

from mordheim_knowledge.loader import knowledge_root, read_yaml, validate_clauses

#: Identity kinds, in the order the inventory lists them.
IDENTITY_KINDS = ("core", "mechanic", "item", "rule")

#: Clause scope that counts towards coverage.
ADMITTED_SCOPE = "YES"

#: Families of ``catalog/mechanics/close-combat.yaml`` that hold mechanic records.
MECHANIC_FAMILIES = ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills")


@dataclass(frozen=True, slots=True)
class Clause:
    identity: str
    clause_id: str
    scope: str

    @property
    def key(self) -> tuple[str, str]:
        return (self.identity, self.clause_id)

    @property
    def admitted(self) -> bool:
        return self.scope == ADMITTED_SCOPE


@dataclass(frozen=True, slots=True)
class Identity:
    """One record the inventory tracks, with the clauses it declares (possibly none)."""
    identity: str
    source_file: str
    #: ``True`` when the duel runtime must honour the record (the coverage denominator).
    admitted: bool
    clauses: tuple[Clause, ...]
    #: Scope of the owning runtime effect for ``rule/`` identities, else ``None``.
    effect_scope: str | None = None

    @property
    def kind(self) -> str:
        return self.identity.split("/", 1)[0]

    @property
    def admitted_clause_ids(self) -> frozenset[str]:
        return frozenset(c.clause_id for c in self.clauses if c.admitted)


def rule_identity(collection: str, owner: str, rule_id: str, effect_id: str) -> str:
    return f"rule/{collection}/{owner}/{rule_id}/{effect_id}"


def _clauses(record: dict, identity: str) -> tuple[Clause, ...]:
    return tuple(Clause(identity, str(c["id"]), str(c["scope"])) for c in validate_clauses(record, context=identity))


def iter_identities(root: Path | None = None) -> Iterator[Identity]:
    """Every identity of the knowledge base, admitted or not, in document order."""
    base = root or knowledge_root()

    def relative(path: Path) -> str:
        return path.relative_to(base).as_posix()

    core = base / "catalog/rules/core-combat.yaml"
    for rule in read_yaml(core).get("rules") or ():
        identity = f"core/{rule['id']}"
        yield Identity(identity, relative(core), True, _clauses(rule, identity))
    excluded = {str(row.get("id")) for row in read_yaml(base / "registry/runtime-scope.yaml").get("mechanic_exclusions") or ()}
    mechanics = base / "catalog/mechanics/close-combat.yaml"
    catalogue = read_yaml(mechanics)
    for family in MECHANIC_FAMILIES:
        for record in catalogue.get(family) or ():
            identity = f"mechanic/{record['id']}"
            yield Identity(identity, relative(mechanics), str(record["id"]) not in excluded, _clauses(record, identity))
    for path in sorted((base / "catalog/items").glob("*.yaml")):
        for item in read_yaml(path).get("items") or ():
            identity = f"item/{item['id']}"
            yield Identity(identity, relative(path), item.get("combat_status") == "implemented", _clauses(item, identity))

    def rule_effects(rule: dict, collection: str, owner: str, source: str) -> Iterator[Identity]:
        for effect in (rule.get("runtime") or {}).get("effects") or ():
            identity = rule_identity(collection, owner, str(rule["id"]), str(effect["id"]))
            clauses = _clauses(effect, identity)
            scope = str(effect.get("scope"))
            admitted = scope == ADMITTED_SCOPE or any(c.admitted for c in clauses)
            yield Identity(identity, source, admitted, clauses, scope)

    for path in sorted((base / "bands").glob("*/*/special-rules.yaml")):
        for rule in read_yaml(path).get("rules") or ():
            yield from rule_effects(rule, path.parent.parent.name, path.parent.name, relative(path))
    for path in sorted((base / "catalog/skills").glob("*.yaml")):
        for skill in read_yaml(path).get("skills") or ():
            yield from rule_effects(skill, "catalog", path.stem, relative(path))
    for path in sorted((base / "catalog/hirelings").glob("*/*.yaml")):
        document = read_yaml(path)
        for rule in document.get("rules") or ():
            yield from rule_effects(rule, "catalog", path.parent.name, relative(path))
        for profile in document.get("profiles") or ():
            for rule in profile.get("rules") or ():
                if isinstance(rule, dict):
                    yield from rule_effects(rule, "catalog", path.parent.name, relative(path))


@lru_cache(maxsize=None)
def load_identities(root: Path | None = None) -> tuple[Identity, ...]:
    """The validated inventory; a duplicate identity is a knowledge-base defect."""
    identities = tuple(iter_identities(root))
    names = [i.identity for i in identities]
    if len(names) != len(set(names)):
        duplicates = sorted({n for n in names if names.count(n) > 1})
        raise ValueError(f"duplicate identities: {duplicates[:5]}")
    return identities


def load_clauses(root: Path | None = None) -> tuple[Clause, ...]:
    """Every declared clause of the knowledge base."""
    return tuple(c for i in load_identities(root) for c in i.clauses)


def declared_clauses(identities: Iterable[Identity]) -> dict[str, set[str]]:
    """Every identity with the clause ids it declares (empty for a record without clauses)."""
    return {i.identity: {c.clause_id for c in i.clauses} for i in identities}


def admitted_clauses(identities: Iterable[Identity],
                     kinds: Iterable[str] = IDENTITY_KINDS) -> dict[str, set[str]]:
    """The admitted identities of the given kinds with their ``YES`` clause ids.

    An empty set means the identity is one undivided obligation: any scenario
    or marker naming it covers it.
    """
    wanted = set(kinds)
    return {i.identity: set(i.admitted_clause_ids) for i in identities if i.admitted and i.kind in wanted}


def inventory_digest(identities: Iterable[Identity]) -> str:
    """Stable digest of the admitted inventory: identity and sorted YES clause ids."""
    payload = sorted((i.identity, sorted(i.admitted_clause_ids)) for i in identities if i.admitted)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()
