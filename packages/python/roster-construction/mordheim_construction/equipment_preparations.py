"""Supplied Weaponsmith maintenance result on the actual worn pieces, without a roll."""
from dataclasses import replace

from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet


def apply_maintenance(fighter, bindings, profile):
    results = {binding["parameters"]["maintenance_result"] for binding in bindings
               if binding.get("id") == "profile.equipment-maintenance"}
    if not results:
        return fighter
    if len(results) != 1 or next(iter(results)) not in range(1, 7):
        raise ValueError("Supply exactly one printed Weaponsmith maintenance result (1-6)")
    if not ("fighter-kind.hero" in fighter.global_effects.tags
            or profile and profile.get("id") == "hireling.hired-sword.weaponsmith"):
        raise ValueError("Weaponsmith maintenance requires a Hero or the Weaponsmith")
    result = next(iter(results))
    # The first result stands even without matching equipment. Result 6 only
    # changes excluded shooting ranges; neither outcome rerolls or grants a save.
    targets = {2: {"armour.light-armour", "armour.heavy-armour"},
               3: {"defence.helmet"}, 4: {"defence.buckler"},
               5: {"defence.shield"}}.get(result, set())
    inventory = []
    for item in fighter.mutation_equipment:
        if item.slot is None or not targets.intersection(item.effect.tags):
            inventory.append(item)
            continue
        modifier = (EffectSet(parry=True, tags=("defence.buckler",)) if result == 5
                    else EffectSet(armour_save_bonus=1))
        changed = merge_effects(item.effect, modifier)
        inventory.append(replace(item, effect=changed))
        # Include the modification in the item's own contribution. It therefore
        # leaves with that physical piece, including a broken shield/buckler.
        fighter = replace(fighter,
            armour_save=fighter.armour_save - modifier.armour_save_bonus,
            global_effects=merge_effects(fighter.global_effects, modifier))
        if item.slot == "off":
            fighter = replace(fighter, off_hand=changed)
        if {"defence.shield", "defence.buckler", "defence.kite-shield"}.intersection(item.effect.tags):
            fighter = replace(fighter, shield_and_skill_effects=merge_effects(
                fighter.shield_and_skill_effects, modifier))
    return replace(fighter, mutation_equipment=tuple(inventory))
