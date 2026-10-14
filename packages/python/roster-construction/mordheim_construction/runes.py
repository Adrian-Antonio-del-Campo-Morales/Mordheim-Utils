"""Apply source-qualified runes to the actual carried item, without inscription rolls."""
from dataclasses import replace
import re

from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet


def apply_item_modifiers(fighter, bindings, effects, facts):
    """Nemesis Crown p61: supplied runes last this battle, one per physical item."""
    occupied = set()
    inventory = list(fighter.mutation_equipment)
    for binding in bindings:
        if binding.get("id") != "profile.item-modifiers":
            continue
        parameters = binding.get("parameters") or {}
        fact = parameters["slot_fact"]
        slots = facts.get(fact)
        if (not isinstance(slots, list) or not slots
                or any(not isinstance(slot, str) or not re.fullmatch(
                    r"main|off|extra|armour|defence\.[0-9]+", slot) for slot in slots)
                or len(set(slots)) != len(slots)):
            raise ValueError(f"{fact} requires distinct active equipment slots")
        raw = parameters["effect_parameters"]
        modifier = EffectSet(**{**raw, "tags": tuple(raw.get("tags") or ())})
        for slot in slots:
            if slot in occupied:
                raise ValueError(f"Only one Rune may be inscribed on an item: {slot}")
            matches = [(index, item) for index, item in enumerate(inventory) if item.slot == slot]
            if len(matches) != 1:
                raise ValueError(f"Rune requires an actual active carried item: {slot}")
            index, item = matches[0]
            tags = set(item.effect.tags)
            armour_rune = bool(modifier.ward_save < 7 or modifier.armour_save_bonus)
            eligible = (bool(tags & {"armour.light-armour", "armour.heavy-armour",
                                    "armour.gromril-armour", "armour.ithilmar-armour",
                                    "defence.helmet", "defence.shield", "defence.kite-shield"})
                        if armour_rune else item.kind == "weapon" and bool(
                            tags & {"weapon.sword", "weapon.mace", "weapon.axe",
                                    "weapon.double-handed-weapon"} or item.effect.two_handed))
            if not eligible or "armour.attlas-plate-mail" in tags:
                raise ValueError(f"Item is not eligible for this source Rune: {item.item_id}")
            occupied.add(slot)
            changed = merge_effects(item.effect, modifier)
            inventory[index] = replace(item, effect=changed,
                effect_without_poison=(merge_effects(item.effect_without_poison, modifier)
                                       if item.effect_without_poison is not None else None))
            if armour_rune:
                shield = bool(tags & {"defence.shield", "defence.kite-shield"})
                fighter = replace(fighter,
                    armour_save=max(1, fighter.armour_save - modifier.armour_save_bonus),
                    global_effects=merge_effects(fighter.global_effects, modifier),
                    shield_and_skill_effects=(merge_effects(fighter.shield_and_skill_effects, modifier)
                                              if shield else fighter.shield_and_skill_effects))
                if slot == "off":
                    fighter = replace(fighter, off_hand=changed)
            elif slot == "main":
                fighter = replace(fighter, main_weapon=changed,
                    main_weapon_without_poison=(merge_effects(fighter.main_weapon_without_poison, modifier)
                                               if fighter.main_weapon_without_poison is not None else None))
            elif slot == "off":
                fighter = replace(fighter, off_hand=changed,
                    off_hand_without_poison=(merge_effects(fighter.off_hand_without_poison, modifier)
                                              if fighter.off_hand_without_poison is not None else None))
            elif slot == "extra":
                extra = list(fighter.extra_attacks)
                try:
                    attack_index = extra.index(item.effect)
                except ValueError as exc:
                    raise ValueError("Rune requires the declared extra-hand weapon attack") from exc
                extra[attack_index] = changed
                # An extra-hand weapon is already one independent allocated attack.
                extra.extend(replace(changed, attacks_bonus=0) for _ in range(modifier.attacks_bonus))
                fighter = replace(fighter, extra_attacks=tuple(extra))
            else:
                raise ValueError(f"Weapon Rune requires an actual weapon hand: {slot}")
    return replace(fighter, mutation_equipment=tuple(inventory))
