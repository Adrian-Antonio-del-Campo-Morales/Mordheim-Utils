"""verification: Structural verification of bindings and default construction."""
from __future__ import annotations

from mordheim_construction.contracts import COMPILER_CONTRACTS, SPECIAL_RULE_EFFECTS, PROFILE_RULE_EFFECTS
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root, read_yaml, PROFILE_BINDING_IDS
from mordheim_knowledge.loader import runtime_bindings
from pathlib import Path


def _binding_contract_error(binding: dict, execution_ids: set[str]) -> str | None:
    """Use the maintained contracts, never a second registry of binding states."""
    kind, identifier = binding.get("kind"), str(binding.get("id"))
    if kind == "mechanic":
        known = identifier in execution_ids
    elif kind == "trait":
        known = identifier.removeprefix("trait.").replace("-", "_") in TRAIT_TYPES
    elif kind == "profile":
        known = identifier in PROFILE_BINDING_IDS
    elif kind == "compiler":
        known = (
            identifier in COMPILER_CONTRACTS
            # A profile rule selected by the build keeps the ``special-rule.``
            # binding namespace (the Bear, Cold Steel); its executable contract
            # lives in PROFILE_RULE_EFFECTS. Both maintained compiler tables
            # remain authoritative for that binding namespace.
            or identifier.startswith("special-rule.") and (
                identifier.removeprefix("special-rule.") in SPECIAL_RULE_EFFECTS
                or identifier.removeprefix("special-rule.") in PROFILE_RULE_EFFECTS
            )
            # Both maintained compiler tables are authoritative for either
            # namespace: a profile ability may be carried by a selectable
            # special-rule contract (the Necrotect's Hatred) and vice versa.
            or identifier.startswith("profile-rule.") and (
                identifier.removeprefix("profile-rule.") in PROFILE_RULE_EFFECTS
                or identifier.removeprefix("profile-rule.") in SPECIAL_RULE_EFFECTS
            )
        )
    else:
        known = False
    return None if known else f"unknown {kind} binding {identifier}"


def _catalogue_binding_errors(root: Path | None, execution_ids: set[str]) -> list[str]:
    """Check catalogued skills/hireling rules without changing band evidence counts."""
    errors = []
    root = root or knowledge_root()

    def walk(node, path):
        if isinstance(node, dict):
            if "runtime" in node and "id" in node:
                try:
                    for binding in runtime_bindings(node):
                        error = _binding_contract_error(binding, execution_ids)
                        if error:
                            errors.append(f"{path.relative_to(root)}/{node['id']}: {error}")
                except ValueError as exc:
                    errors.append(f"{path.relative_to(root)}: {exc}")
            for child in node.values():
                walk(child, path)
        elif isinstance(node, list):
            for child in node:
                walk(child, path)

    for directory in (root / "catalog/skills", root / "catalog/hirelings"):
        for path in sorted(directory.rglob("*.yaml")):
            walk(read_yaml(path), path)
    return errors


def required_profile_build(collection: str, band_id: str, profile_id: str) -> FighterBuild:
    """Supply each profile's printed mandatory initial choice.

    These are construction facts the source requires before the member exists,
    not production defaults: these fixtures choose Tentacle for a mutant,
    Bloated Foulness for a Tainted One, one Veteran Tracker skill for a Trapper,
    one mutation for a Rat Ogre and one disability result for a Cripple. The
    profiles whose printed line requires a choice receive one.
    """
    special_rule_ids = (
        ("band--mutations-tentacle",)
        if band_id in {"cult-of-the-possessed", "trollheim-cult-of-the-possessed"}
        and profile_id in {"mutants", "the-possessed"}
        else ("band--blessings-of-nurgle-bloated-foulness",)
        if band_id == "carnival-of-chaos" and profile_id == "tainted-ones"
        else ("band--ogre-hunting-skills-netter",)
        if band_id == "ogre-hunting-party-web" and profile_id == "trappers"
        else ("band--mutations-tentacle",)
        if band_id == "skaven-of-clan-moulder-web" and profile_id == "rat-ogres"
        else ()
    )
    condition_ids = (
        ("condition.disability-2",)
        if band_id == "chaos-streets-mordheim-inhabitants" and profile_id == "cripples"
        else ()
    )
    return FighterBuild(
        "mordheim",
        band_id=band_id,
        profile_id=profile_id,
        collection=collection,
        special_rule_ids=special_rule_ids,
        condition_ids=condition_ids,
    )
