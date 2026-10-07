"""construction: Resolve supplied canonical condition ids to their operators.

The knowledge base's ``catalog/rules/conditions.yaml`` is the only
interpretation table: this module reads each condition's declared ``runtime``
binding and hands the resulting trait values and mechanic ids to the compiler.
No adapter keeps a second table, and a condition whose runtime is not
implemented is refused by name instead of being guessed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mordheim_knowledge.loader import load_conditions


@dataclass(frozen=True, slots=True)
class SuppliedConditions:
    """Operators a set of supplied canonical conditions resolves to."""

    condition_ids: tuple[str, ...]
    trait_values: dict
    mechanic_ids: tuple[str, ...]


def resolve_supplied_conditions(
    condition_ids, facts=None, ruleset: str = "mordheim", root: Path | None = None,
) -> SuppliedConditions:
    """Resolve the caller's current conditions through the KB catalogue.

    ``facts`` supplies the warrior's declared facts (``trait_overrides``), used
    only for a condition whose source prints more than one variant and therefore
    declares ``variant_fact``. A duplicate id resolves once, so two routes that
    grant the same condition never apply its effect twice.
    """
    catalogue = {str(row["id"]): row for row in load_conditions(ruleset, root)}
    facts = facts or {}
    ordered: list[str] = []
    traits: dict = {}
    mechanics: list[str] = []
    for raw_id in condition_ids:
        condition_id = str(raw_id)
        if condition_id in ordered:
            continue
        row = catalogue.get(condition_id)
        if row is None:
            raise ValueError(f"unknown canonical condition: {condition_id!r}")
        runtime = row.get("runtime") or {}
        if runtime.get("implemented") != "YES":
            reason = next((str(effect.get("reason")) for effect in runtime.get("effects") or ()
                           if effect.get("reason")), "no executable duel binding")
            raise ValueError(f"condition is outside the executable duel runtime: {condition_id}: {reason}")
        variant: object = None
        variant_fact = runtime.get("variant_fact")
        if variant_fact is not None:
            variant = facts.get(str(variant_fact))
            admitted = tuple(effect.get("variant") for effect in runtime.get("effects") or ()
                             if effect.get("variant") is not None)
            if variant not in admitted:
                raise ValueError(
                    f"condition {condition_id} needs the supplied {variant_fact} fact; "
                    f"admitted values are {sorted(admitted)}")
        for effect in runtime.get("effects") or ():
            if effect.get("scope") != "YES":
                continue
            effect_variant = effect.get("variant")
            if effect_variant is not None and effect_variant != variant:
                continue
            binding = effect.get("binding")
            if not isinstance(binding, dict):
                continue
            kind, binding_id = binding.get("kind"), str(binding.get("id") or "")
            if kind == "trait":
                key = binding_id.removeprefix("trait.").replace("-", "_")
                traits[key] = (binding.get("parameters") or {}).get("value")
            elif kind == "mechanic":
                mechanics.append(binding_id)
            else:
                raise ValueError(
                    f"condition {condition_id} has an unsupported binding kind: {kind!r} ({binding_id})")
        ordered.append(condition_id)
    return SuppliedConditions(tuple(ordered), traits, tuple(mechanics))
