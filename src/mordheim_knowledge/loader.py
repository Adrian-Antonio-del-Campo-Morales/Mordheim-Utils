"""knowledge.loader: responsibility extracted without altering the rules."""
from __future__ import annotations
from mordheim_knowledge.paths import project_root

from dataclasses import dataclass
from functools import lru_cache
import os as os
from pathlib import Path
import sys as sys
import yaml as yaml


RUNTIME_SCOPES = frozenset({"YES", "NO", "LATER"})


RUNTIME_IMPLEMENTED = frozenset({"YES", "NO"})


RUNTIME_GRANTS = frozenset({"profile", "band", "selectable", "none"})


RUNTIME_BINDING_KINDS = frozenset({"mechanic", "trait", "profile", "compiler"})


SELECTABLE_RULE_KINDS = frozenset({
    "warband_skill", "mutation", "blessing", "virtue", "mark",
    "modification", "profile_ability", "warband_variant",
})


PROFILE_BINDING_IDS = frozenset({
    "profile.skill-access", "profile.equipment-restrictions",
    "profile.natural-attacks", "profile.fist", "profile.random-characteristics",
    "profile.characteristics",
})


@dataclass(frozen=True, slots=True)
class BandPackage:
    collection: str; ruleset: str; band: dict; profiles: tuple[dict, ...]; equipment_lists: tuple[dict, ...]
    special_rules: tuple[dict, ...]; path: Path


def knowledge_root() -> Path:
    override = os.environ.get("MORDHEIM_COMBAT_LAB_KNOWLEDGE_PATH")
    if override: return Path(override)
    if getattr(sys, "frozen", False): return Path(sys._MEIPASS) / "sources" / "knowledge"
    return project_root() / "sources" / "knowledge"


def read_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict): raise ValueError(f"expected a mapping in {path}")
    return value


def validate_rule_runtime(rule: dict, *, context: str = "special rule") -> None:
    """Validate canonical runtime metadata without inferring missing bindings."""
    runtime = rule.get("runtime")
    if runtime is None:
        return
    if not isinstance(runtime, dict):
        raise ValueError(f"{context} {rule.get('id')}: runtime must be a mapping")
    scope = runtime.get("scope")
    implemented = runtime.get("implemented")
    grant = runtime.get("grant")
    effects = runtime.get("effects")
    if scope not in RUNTIME_SCOPES:
        raise ValueError(f"{context} {rule.get('id')}: invalid runtime scope {scope!r}")
    if implemented not in RUNTIME_IMPLEMENTED:
        raise ValueError(f"{context} {rule.get('id')}: invalid implementation status {implemented!r}")
    if grant not in RUNTIME_GRANTS:
        raise ValueError(f"{context} {rule.get('id')}: invalid runtime grant {grant!r}")
    if grant == "selectable" and rule.get("kind") not in SELECTABLE_RULE_KINDS:
        raise ValueError(f"{context} {rule.get('id')}: selectable rule has invalid kind {rule.get('kind')!r}")
    if not isinstance(effects, list) or not effects:
        raise ValueError(f"{context} {rule.get('id')}: runtime effects must be a non-empty list")
    effect_ids = []
    effect_scopes = []
    for effect in effects:
        if not isinstance(effect, dict):
            raise ValueError(f"{context} {rule.get('id')}: runtime effect must be a mapping")
        effect_id = str(effect.get("id") or "")
        effect_scope = effect.get("scope")
        if not effect_id:
            raise ValueError(f"{context} {rule.get('id')}: runtime effect has no id")
        if effect_scope not in RUNTIME_SCOPES:
            raise ValueError(f"{context} {rule.get('id')}/{effect_id}: invalid scope {effect_scope!r}")
        binding = effect.get("binding")
        if binding is not None:
            if not isinstance(binding, dict):
                raise ValueError(f"{context} {rule.get('id')}/{effect_id}: binding must be a mapping or null")
            if binding.get("kind") not in RUNTIME_BINDING_KINDS or not str(binding.get("id") or ""):
                raise ValueError(f"{context} {rule.get('id')}/{effect_id}: invalid runtime binding")
            if binding.get("kind") == "profile" and binding.get("id") not in PROFILE_BINDING_IDS:
                raise ValueError(f"{context} {rule.get('id')}/{effect_id}: unknown profile binding {binding.get('id')!r}")
            if "parameters" in binding and not isinstance(binding["parameters"], dict):
                raise ValueError(f"{context} {rule.get('id')}/{effect_id}: binding parameters must be a mapping")
        if binding is None and not str(effect.get("reason") or ""):
            raise ValueError(f"{context} {rule.get('id')}/{effect_id}: unbound effect needs a reason")
        if implemented == "YES" and effect_scope == "YES" and binding is None:
            raise ValueError(f"{context} {rule.get('id')}/{effect_id}: implemented YES effect has no binding")
        effect_ids.append(effect_id)
        effect_scopes.append(effect_scope)
    if len(effect_ids) != len(set(effect_ids)):
        raise ValueError(f"{context} {rule.get('id')}: duplicate runtime effect ids")
    expected_scope = "YES" if "YES" in effect_scopes else "LATER" if "LATER" in effect_scopes else "NO"
    if scope != expected_scope:
        raise ValueError(f"{context} {rule.get('id')}: runtime scope {scope} does not match effects ({expected_scope})")


def runtime_bindings(rule: dict, kind: str | None = None, *, include_pending: bool = False) -> tuple[dict, ...]:
    """Return executable bindings, or design-time bindings when explicitly requested.

    Pending rules may already point at a canonical future contract.  They must
    remain invisible to compiler/engine consumers until ``implemented`` is YES.
    """
    runtime = rule.get("runtime") or {}
    if not include_pending and runtime.get("implemented") != "YES":
        return ()
    result = []
    for effect in runtime.get("effects") or ():
        binding = effect.get("binding")
        if isinstance(binding, dict) and (kind is None or binding.get("kind") == kind):
            result.append(binding)
    return tuple(result)


@lru_cache(maxsize=None)
def load_collections(root: Path | None = None):
    document = read_yaml((root or knowledge_root()) / "registry/collections.yaml")
    rows = tuple(document.get("collections") or ())
    ids = [str(row.get("id") or "") for row in rows]
    if any(not collection_id for collection_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("collection registry has missing or duplicate IDs")
    return rows


@lru_cache(maxsize=None)
def load_bands(collection: str, root: Path | None = None):
    base = root or knowledge_root(); result = []
    collections = {str(row["id"]): row for row in load_collections(base)}
    if collection not in collections:
        raise ValueError(f"unknown band collection: {collection}")
    allowed_rulesets = set(collections[collection].get("rulesets") or ())
    for path in sorted((base / "bands" / collection).glob("*/band.yaml")):
        directory = path.parent
        band = read_yaml(path)
        ruleset = str(band.get("ruleset") or "")
        if not ruleset:
            raise ValueError(f"band package has no ruleset: {path}")
        if ruleset not in allowed_rulesets:
            raise ValueError(f"collection {collection} does not allow ruleset {ruleset}: {path}")
        special_rules = tuple(read_yaml(directory/"special-rules.yaml").get("rules") or ())
        for rule in special_rules:
            validate_rule_runtime(rule, context=f"{collection}/{band.get('id')}")
        result.append(BandPackage(collection, ruleset, band, tuple(read_yaml(directory/"profiles.yaml").get("profiles") or ()), tuple(read_yaml(directory/"equipment-access.yaml").get("equipment_lists") or ()), special_rules, directory))
    return tuple(result)


@lru_cache(maxsize=None)
def load_mechanics(ruleset: str, root: Path | None = None):
    document = read_yaml((root or knowledge_root()) / "catalog/mechanics/close-combat.yaml")
    if document.get("ruleset") != ruleset: raise ValueError(f"catalogue does not describe {ruleset}")
    return document


@lru_cache(maxsize=None)
def load_execution_contract(ruleset: str, root: Path | None = None):
    document = read_yaml((root or knowledge_root()) / "catalog/mechanics/execution.yaml")
    if document.get("ruleset") != ruleset: raise ValueError(f"execution contract does not describe {ruleset}")
    return document




@lru_cache(maxsize=None)
def load_items(ruleset: str, root: Path | None = None):
    base = (root or knowledge_root()) / "catalog/items"
    rows = []
    for path in sorted(base.glob("*.yaml")):
        document = read_yaml(path)
        if document.get("ruleset") != ruleset:
            raise ValueError(f"item catalogue does not describe {ruleset}: {path}")
        rows.extend(document.get("items") or ())
    ids = [str(row.get("id") or "") for row in rows]
    if any(not item_id for item_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("item catalogue has missing or duplicate IDs")
    return tuple(rows)


@lru_cache(maxsize=None)
def load_simulation_mappings(ruleset: str, root: Path | None = None):
    base = root or knowledge_root()
    document = read_yaml(base / "catalog/mechanics/simulation-mappings.yaml")
    if document.get("ruleset") != ruleset: raise ValueError(f"simulation mappings do not describe {ruleset}")
    mechanics = load_mechanics(ruleset, base)
    mechanic_options = {
        str(row["id"]): row.get("engine_option")
        for family in ("weapons","armours","defences","materials","preparations","poisons","skills")
        for row in mechanics.get(family) or ()
    }
    declared = document.get("item_mappings") or ()
    declared_ids = [str(row.get("item_id") or "") for row in declared]
    if any(not item_id for item_id in declared_ids) or len(declared_ids) != len(set(declared_ids)):
        raise ValueError("simulation mappings have missing or duplicate item IDs")
    mappings = {str(row["item_id"]): dict(row) for row in declared}
    for item in load_items(ruleset, base):
        item_id = str(item["id"])
        if item_id in mappings:
            continue
        status = item.get("combat_status") or "out_of_scope"
        mechanic_id = item.get("mechanic_id")
        if status == "implemented":
            engine_option = mechanic_options.get(str(mechanic_id))
            if not mechanic_id or not engine_option:
                raise ValueError(f"implemented item has no executable mechanic: {item_id}")
            mappings[item_id] = {
                "item_id": item_id, "status": "implemented",
                "mechanic_id": mechanic_id, "engine_option": engine_option,
            }
        elif status == "out_of_scope":
            mappings[item_id] = {"item_id": item_id, "status": "out_of_scope"}
        else:
            raise ValueError(f"unknown combat status for item {item_id}: {status}")
    return {**document, "item_mappings": tuple(mappings.values())}


@lru_cache(maxsize=None)
def load_skills(ruleset: str, root: Path | None = None):
    base=(root or knowledge_root()) / "catalog/skills"; rows=[]
    for path in sorted(base.glob("*.yaml")):
        document=read_yaml(path)
        if document.get("ruleset") != ruleset: raise ValueError(f"skill catalogue does not describe {ruleset}: {path}")
        rows.extend(document.get("skills") or ())
    ids = [str(row.get("id") or "") for row in rows]
    if any(not skill_id for skill_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("skill catalogue has missing or duplicate IDs")
    for skill in rows:
        validate_rule_runtime(skill, context="skill")
    return tuple(rows)


@lru_cache(maxsize=None)
def load_runtime_scope(ruleset: str, root: Path | None = None):
    document=read_yaml((root or knowledge_root())/"registry/runtime-scope.yaml")
    if document.get("ruleset") != ruleset:raise ValueError(f"runtime scope does not describe {ruleset}")
    return document
