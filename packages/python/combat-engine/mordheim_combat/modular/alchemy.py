"""Alchemist recovery under the project's once-per-own-turn timing ruling."""
from dataclasses import replace

from mordheim_combat.modular.contexts import OwnedRollDice
from mordheim_combat.modular.state import require_characteristics
from mordheim_combat.phases import Condition, _characteristic_test, has_tag
from mordheim_core.dice import RollRequest

BACKLEY = "condition.alchemist-backleys-brew"
ADDICTED = "condition.alchemist-addicted"
VIGORTIA = "condition.alchemist-aberrantius-vigortia"


def alchemist_addicted(fighter, current):
    return has_tag(fighter.global_effects, ADDICTED) and ADDICTED not in current.resources_spent


def resolve_alchemist(fighter, current, dice, decisions, key):
    """Called once at the start of this fighter's turn, never the opponent's."""
    if not current.active:
        return current
    if has_tag(fighter.global_effects, BACKLEY) and BACKLEY not in current.resources_spent:
        current = require_characteristics(fighter, current, dice, key, {"T"}, decisions)
        owned = OwnedRollDice(dice, fighter, current, decisions)
        passed = _characteristic_test(current.toughness, owned, f"{key}.alchemist-backley",
                                     reroll=has_tag(fighter.global_effects, "skill.blessed-sight"))
        current = replace(current, resources_spent=current.resources_spent | owned.state.resources_spent)
        if passed:
            # Restore only the penalty actually applied: a stat already at one
            # was not reduced, and must not gain a free point on recovery.
            penalties = dict(current.alchemist_backley_penalties)
            modifiers = dict(current.random_modifiers)
            for stat, penalty in penalties.items():
                modifiers[stat] = modifiers.get(stat, 0) + penalty
            current = replace(current.spend(BACKLEY),
                              strength=current.strength + penalties.get("S", 0),
                              initiative=current.initiative + penalties.get("I", 0),
                              random_modifiers=tuple(modifiers.items()),
                              alchemist_backley_penalties=())
    if alchemist_addicted(fighter, current) and current.condition == Condition.STANDING:
        owned = OwnedRollDice(dice, fighter, current, decisions)
        roll = owned.roll(RollRequest(f"{key}.alchemist-brew"))
        current = replace(current, resources_spent=current.resources_spent | owned.state.resources_spent)
        if roll == 6:
            current = current.spend(ADDICTED)
            if not has_tag(fighter.global_effects, VIGORTIA):
                current = require_characteristics(fighter, current, dice, key, {"S", "T"}, decisions)
                modifiers = dict(current.random_modifiers)
                for stat in ("S", "T"):
                    modifiers[stat] = modifiers.get(stat, 0) + 1
                current = replace(current, strength=current.strength + 1, toughness=current.toughness + 1,
                                  random_modifiers=tuple(modifiers.items()))
    return current
