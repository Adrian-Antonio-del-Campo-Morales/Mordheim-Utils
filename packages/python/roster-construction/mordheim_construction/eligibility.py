"""Transport to the shared TypeScript rules; this adapter contains no rule decisions."""
from __future__ import annotations

import atexit
from functools import lru_cache
from importlib.resources import files
import os
from pathlib import Path
from threading import RLock

from mordheim_construction.combat_packages import combat_packages
from mordheim_knowledge.loader import (
    knowledge_root, load_bands, load_collections, load_items, load_mechanics, load_simulation_mappings,
    load_skills, runtime_bindings,
)

_lock = RLock()
_runtime = None
_runtime_pid = None
_installed = set()


def _close_runtime():
    global _runtime
    if _runtime is not None and _runtime_pid == os.getpid():
        _runtime.close()
        _runtime = None


def _engine():
    global _runtime, _runtime_pid
    if _runtime is None or _runtime_pid != os.getpid():
        from py_mini_racer import MiniRacer
        engine = MiniRacer()
        try:
            engine.eval(files("mordheim_construction").joinpath("_eligibility.js").read_text(encoding="utf-8"))
        except Exception:
            engine.close()
            raise
        _runtime = engine
        _runtime_pid = os.getpid()
        _installed.clear()
        atexit.register(_close_runtime)
    return _runtime


def call(operation, *args):
    """Execute the shared browser/desktop function, with JSON-only transport."""
    with _lock:
        return _invoke(f"MordheimEligibility.{operation}", *args)


def _invoke(function, *args):
    from py_mini_racer import JSEvalException
    try:
        return _engine().call(function, *args, timeout_sec=10)
    except JSEvalException as error:
        # Preserve the compiler's public validation exception at the transport boundary.
        raise ValueError(str(error)) from error


def package_facts(package):
    profile_keys = ("id", "type", "skill_access", "equipment_lists", "fixed_equipment",
                    "equipment_restrictions", "rule_ids", "hireling_equipment")
    return {
        "band": {key: package.band[key] for key in ("id", "canonical_family") if key in package.band},
        "profiles": [{key: row[key] for key in profile_keys if key in row} for row in package.profiles],
        "equipment_lists": [{key: row[key] for key in ("id", "items", "loadouts") if key in row}
                            for row in package.equipment_lists],
        "special_rules": [
            {**{key: rule[key] for key in ("id", "kind", "eligibility", "applies_to") if key in rule},
             "runtime": rule.get("runtime") or {},
             "bindings": [
                binding for kind in ("mechanic", "profile", "compiler")
                for binding in runtime_bindings(rule, kind)
            ]}
            for rule in package.special_rules
        ],
    }


@lru_cache(maxsize=None)
def _catalogue(collection, ruleset, root):
    mechanics = {str(row["id"]): row for family in (
        "weapons", "armours", "defences", "materials", "preparations", "poisons", "skills",
    ) for row in load_mechanics(ruleset, root).get(family, ())}
    by_option = {str(row.get("engine_option")): mid for mid, row in mechanics.items() if row.get("engine_option")}
    mappings = {}
    for row in load_simulation_mappings(ruleset, root).get("item_mappings") or ():
        mechanic_id = row.get("mechanic_id") or by_option.get(str(row.get("engine_option")))
        if row.get("status") == "implemented" and mechanic_id in mechanics:
            mappings[str(row["item_id"])] = mechanic_id
    packages = {str(pack.band["id"]): package_facts(pack) for pack in combat_packages(collection, root)}
    foreign = packages if collection == "mordheim" else {
        str(pack.band["id"]): package_facts(pack) for pack in combat_packages("mordheim", root)
    }
    return {
        "packages": packages, "foreign_packages": foreign,
        "mechanics": mechanics, "mappings": mappings,
        "skills": {str(row["id"]): {key: row[key] for key in ("id", "category", "kind", "source_refs") if key in row}
                   for row in load_skills(ruleset, root)},
        "items": {str(row["id"]): {"kind": str(row.get("kind") or ""), "mechanic_id": row.get("mechanic_id"),
                                   "tags": [str(tag) for tag in row.get("tags") or ()]}
                  for row in load_items(ruleset, root)},
        "free_rules": {str(rule["id"]): rule for collection_row in load_collections(root)
                       if ruleset in collection_row.get("rulesets", ())
                       for pack in combat_packages(str(collection_row["id"]), root)
                       for rule in package_facts(pack)["special_rules"]},
    }


def build_facts(build, main_weapon_id=None):
    keys = ("band_id", "profile_id", "main_weapon_id", "armour_id", "off_hand_id",
            "extra_hand_id", "main_material_id", "off_material_id", "main_poison_id",
            "off_poison_id", "defence_ids", "skill_ids", "preparation_ids",
            "special_rule_ids", "mounted", "owned_item_ids")
    result = {key: getattr(build, key) for key in keys}
    # The House chosen for a House Guard warband is a selection fact, like a
    # declared variant; the shared `configuredProfile` turns it into the
    # conjunctive gate printed equipment lines carry. Other selected facts travel
    # in `variant_ids` already (a chosen Modus Operandi, a background, a tribe).
    variants = list(build.variant_ids)
    house = build.trait_overrides.get("house_guard_house")
    if house is not None:
        variants.append(f"house.{house}")
    result["variant_ids"] = tuple(variants)
    result["open_flame"] = build.trait_overrides.get("lit_item", False)
    if main_weapon_id is not None:
        result["main_weapon_id"] = main_weapon_id
    return result


def context(build, package=None, profile=None, main_weapon_id=None,
            profile_bindings=(), compiler_contracts=(), compiler_bindings=()):
    return {
        "build": build_facts(build, main_weapon_id),
        "package": package_facts(package) if package else {
            "band": {"id": build.band_id or "custom"}, "profiles": [],
            "equipment_lists": [], "special_rules": [],
        },
        "profile": profile or {"id": build.profile_id or "custom"},
        "profile_bindings": list(profile_bindings),
        "compiler_bindings": list(compiler_bindings),
        "contracts": list(compiler_contracts),
    }


def desktop_call(operation, build, root=None, **kwargs):
    resolved = Path(root) if root is not None else knowledge_root()
    key = f"{resolved.resolve()}|{build.collection}|{build.ruleset}"
    with _lock:
        engine = _engine()
        if key not in _installed:
            engine.call("MordheimEligibility.installCatalogue", key,
                        _catalogue(build.collection, build.ruleset, resolved), timeout_sec=10)
            _installed.add(key)
        return _invoke("MordheimEligibility.desktopCall", operation, key,
                       context(build, **kwargs))


def construction_call(operation, build, context_facts, proposals=(), root=None, *, draft=False):
    """Run a batch construction query against the shared module.

    The installed catalogue supplies the canonical item facts for the
    candidates the context does not carry; a transport failure raises so the
    caller reports an explicit operation error instead of falling back to a
    permissive local rule.
    """
    resolved = Path(root) if root is not None else knowledge_root()
    key = f"{resolved.resolve()}|{build.collection}|{build.ruleset}"
    with _lock:
        engine = _engine()
        if key not in _installed:
            engine.call("MordheimEligibility.installCatalogue", key,
                        _catalogue(build.collection, build.ruleset, resolved), timeout_sec=10)
            _installed.add(key)
        return _invoke("MordheimEligibility.constructionCall", operation, key,
                       context_facts, list(proposals), {"draft": draft})


def configuration_context(build, package, profile, *, possession, slots, root=None):
    """Project a supplied complete kit separately from the active duel slots."""
    band = desktop_call("bandFacts", build, root, package=package, profile=profile)
    return {"profile": desktop_call("profileFacts", build, root, package=package, profile=profile),
            "items": {}, "skills": {}, "possession": list(possession), "slots": slots,
            "limits": band["equipment_limits"], "band_forbids": band["equipment_forbids"],
            "operation": {"product": "combat-lab", "mounted": build.mounted}}


def validate(operation, build, root=None, **kwargs):
    # boundEquipment needs the canonical item facts installed for the caller's root;
    # the other specialist stages stay catalogue-free.
    if operation in {"categoryProhibitions", "requiredInitial", "mutationLimit"}:
        message = call("buildRestriction", {**context(build, **kwargs), "catalogue": {
            "packages": {}, "foreign_packages": {}, "mechanics": {}, "mappings": {}, "skills": {},
        }}, operation)
    else:
        message = desktop_call(operation, build, root, **kwargs)
    if message is not None:
        raise ValueError(message)


def selected_rules(build, package, profile, root, compiler_contracts):
    result = desktop_call("selectedRules", build, root, package=package, profile=profile,
                          compiler_contracts=compiler_contracts)
    if result["message"] is not None:
        raise ValueError(result["message"])
    return result["rules"]


def validate_special_rule(build, package, profile, rule, starting_skills, stage):
    bindings = runtime_bindings(rule)
    message = call("specialRuleRestriction", {
        "build": build_facts(build), "profile": profile,
        "rule": {**rule, "bindings": list(bindings)},
        "native_virtue": package is not None and any(row.get("id") == rule.get("id") for row in package.special_rules),
        "starting_skills": list(starting_skills), "stage": stage,
    })
    if message is not None:
        raise ValueError(message)


def validate_loadout(build, main_weapon_id, mechanics, contracts, selected_mechanics, stage):
    message = call("loadoutRestriction", {
        "build": build_facts(build, main_weapon_id),
        "main_weapon": mechanics[main_weapon_id],
        "off_weapon": mechanics.get(build.off_hand_id),
        "contracts": list(contracts), "selected_mechanics": list(selected_mechanics),
        "stage": stage,
    })
    if message is not None:
        raise ValueError(message)


def validate_additional_equipment(build):
    message = call("additionalEquipmentRestriction", build_facts(build))
    if message is not None:
        raise ValueError(message)
