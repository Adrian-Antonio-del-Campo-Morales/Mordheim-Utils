"""Assign runtime keys to the decisive modular operator (structural only).

The registry's ``consumer`` is an ordered pipeline.  The decisive symbol for a
behaviour is the last runtime symbol in that pipeline; shared construction and
initialization entries earlier in the list are prerequisites, not the rule.
"""
from __future__ import annotations

import json
import re

STAGE_RULES = (
    ("initialize_fighter", "B01-initial-state"),
    ("initialize_duel", "B01-initial-state"),
    ("require_characteristics", "B01-initial-state"),
    ("FighterState", "B01-initial-state"),
    ("armour_target", "B04-armour"),
    ("prepare_armour_context", "B04-armour"),
    ("_injury_context", "B07-injury"),
    ("injury_condition", "B07-injury"),
    ("resolve_injury", "B07-injury"),
    ("resolve_critical", "B07-injury"),
    ("causes_fear", "B11-fear"),
    ("resolve_fear", "B11-fear"),
    ("undead_foes_fear_immunity", "B11-fear"),
    ("resolve_stupidity", "B12-stupidity"),
    ("resolve_local_leadership", "B14-leadership"),
    ("resolve_leadership", "B14-leadership"),
    ("apply_opponent_leadership", "B14-leadership"),
    ("_hit_reroll", "B02-hit"),
    ("prepare_hit_context", "B02-hit"),
    ("resolve_hit", "B02-hit"),
    ("prepare_wound_context", "B03-wound"),
    ("_attack_strength", "B03-wound"),
    ("_resolve_wound_damage", "B03-wound"),
    ("resolve_wound", "B03-wound"),
    ("prepare_special_save_context", "B05-special-save"),
    ("resolve_special_save", "B05-special-save"),
    ("_supplied_ward", "B05-special-save"),
    ("_parry_context", "B06-parry"),
    ("_parry_capacity", "B06-parry"),
    ("resolve_parry", "B06-parry"),
    ("build_attacks", "B08-attack-pool"),
    ("_resolve_attack_pool", "B08-attack-pool"),
    ("_resolve_prepared_defences", "B08-attack-pool"),
    ("unarmed_attack_cap_applies", "B08-attack-pool"),
    ("ignores_unarmed_penalties", "B08-attack-pool"),
    ("equipment_for_state", "B09-equipment"),
    ("apply_round_weapon_attack_modifiers", "B09-equipment"),
    ("whipcrack_weapon", "B09-equipment"),
    ("resolve_stun_reaction", "B10-round-order"),
    ("resolve_priority", "B10-round-order"),
    ("first_acts_before", "B10-round-order"),
    ("select_attack_replacement", "B10-round-order"),
    ("apply_opponent_attack_modifiers", "B10-round-order"),
    ("resolve_round", "B10-round-order"),
    ("_resolve_reference_attack_once", "B10-round-order"),
    ("_react_to_wound", "B15-aftermath"),
    ("_revenant_recovery", "B15-aftermath"),
    ("_black_hunger", "B15-aftermath"),
    ("_start_round_state", "B15-aftermath"),
    ("_spines", "B15-aftermath"),
    ("resolve_alchemist", "B15-aftermath"),
    ("_force_of_will", "B01-initial-state"),
    ("compile_fighter", "B01-initial-state"),
)

_STAGE_BY_FILE = (
    ("modular/rounds.py", "B10-round-order"),
    ("modular/contexts.py", "B99-unmapped"),
    ("modular/attacks.py", "B03-wound"),
    ("modular/pools.py", "B08-attack-pool"),
    ("modular/equipment.py", "B09-equipment"),
    ("modular/psychology.py", "B11-fear"),
    ("modular/leadership.py", "B14-leadership"),
    ("modular/state.py", "B01-initial-state"),
    ("modular/aftermath.py", "B15-aftermath"),
    ("phases.py", "B99-unmapped"),
)


def _parts(consumer: str) -> list[str]:
    try:
        value = json.loads(consumer)
    except json.JSONDecodeError:
        value = [consumer]
    if isinstance(value, str):
        value = [value]
    return [str(item) for item in value]


def _symbol(part: str) -> str:
    # ``mordheim_combat.modular.contexts.prepare_hit_context`` -> symbol
    dotted = re.fullmatch(r"[\w.]*?([A-Za-z_]\w*)", part.strip())
    if "::" in part:
        return part.split("::")[-1].strip()
    if dotted and "." in part:
        return dotted.group(1)
    return part.strip()


#: Symbols that are prerequisites or the round/attack loop, not a rule's
#: decisive operator.  A later specific operator in the same pipeline wins.
_SKIP = frozenset({
    "compile_fighter", "_compile_fighter", "prepare_source_profile",
    "initialize_fighter", "initialize_duel", "require_characteristics",
    "FighterState", "MODULAR_TAG_CONSUMERS", "require_optimized_support",
    "OwnedRollDice", "combat_packages", "resolve_supplied_conditions",
    "profileFactsProjection", "load_hirelings", "createHirelingsWorkflow",
    "resolve_round", "resolve_reference_attack_once", "_resolve_reference_attack_body",
    "resolve_reference_attack", "_resolve_weapon_once",
    "apply_round_weapon_attack_modifiers", "select_attack_replacement",
    "apply_opponent_attack_modifiers", "apply_opponent_leadership",
    "_start_round_state",
})


def stage(consumer: str) -> str:
    parts = _parts(consumer)
    for part in reversed(parts):
        symbol = _symbol(part)
        if symbol in _SKIP:
            continue
        for needle, name in STAGE_RULES:
            if needle == symbol or needle in part:
                return name
    # Only prerequisites/loop symbols remain: the generic round/attack loop is
    # the best available disposition; otherwise the consumer is ambiguous.
    for part in reversed(parts):
        symbol = _symbol(part)
        if symbol in {"resolve_round", "resolve_reference_attack_once",
                      "_resolve_reference_attack_body", "resolve_reference_attack",
                      "apply_round_weapon_attack_modifiers"}:
            return "B10-round-order"
        if symbol in {"prepare_source_profile", "require_characteristics"}:
            return "B01-initial-state"
        if symbol in {"MODULAR_TAG_CONSUMERS", "require_optimized_support"}:
            return "B00-routing"
        for needle, name in _STAGE_BY_FILE:
            if needle in part:
                return name
    return "B99-unmapped"
