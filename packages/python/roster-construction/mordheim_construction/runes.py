"""Apply supplied item modifiers to the actual carried item, without a roll."""
from dataclasses import replace
import re

from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet


def _clean_counterpart(effect, without_poison, modifier, poison):
    """The piece's own effect without the supplied modifier.

    A rune belongs to the weapon, so it also reaches the counterpart the engine
    hands a poison-immune defender; a supplied coating is itself the poison, so
    that defender meets the piece as it stood before the coating.
    """
    if without_poison is None:
        return effect if poison else None
    return without_poison if poison else merge_effects(without_poison, modifier)


def apply_item_modifiers(fighter, bindings, effects, facts):
    """Nemesis Crown p61 runes and declared supplied modifiers on one real item.

    A rune binding keeps the printed rune rule: one rune per physical item, on a
    sword, mace, axe, two-handed weapon or the armour it inscribes.  A binding
    that declares ``eligibility`` reaches only the exemplars that block admits,
    up to its own cap and bearer requirement, and ``poison_coating`` records
    that the supplied modifier is itself a poison.
    """
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
        declared = parameters.get("eligibility") or {}
        poison = bool(parameters.get("poison_coating"))
        if declared:
            limit = int(declared.get("max_items") or 1)
            if len(slots) > limit:
                raise ValueError(f"a supplied result covers at most {limit} items: {fact}")
            bearers = tuple(declared.get("bearer_tags") or ())
            if bearers and not set(bearers).intersection(fighter.global_effects.tags):
                raise ValueError(
                    f"the supplied modifier needs one of these bearers: {', '.join(bearers)}")
        for slot in slots:
            if not declared and slot in occupied:
                raise ValueError(f"Only one Rune may be inscribed on an item: {slot}")
            matches = [(index, item) for index, item in enumerate(inventory) if item.slot == slot]
            if len(matches) != 1:
                raise ValueError(f"{'Item modifier' if declared else 'Rune'}"
                                 f" requires an actual active carried item: {slot}")
            index, item = matches[0]
            tags = set(item.effect.tags)
            armour_rune = bool(modifier.ward_save < 7 or modifier.armour_save_bonus)
            if declared:
                admitted = set(declared.get("tags") or ())
                eligible = item.kind == "weapon" and (not admitted or bool(tags & admitted))
            else:
                eligible = (bool(tags & {"armour.light-armour", "armour.heavy-armour",
                                         "armour.gromril-armour", "armour.ithilmar-armour",
                                         "defence.helmet", "defence.shield", "defence.kite-shield"})
                            if armour_rune else item.kind == "weapon" and bool(
                                tags & {"weapon.sword", "weapon.mace", "weapon.axe",
                                        "weapon.double-handed-weapon"} or item.effect.two_handed))
            if not eligible or "armour.attlas-plate-mail" in tags:
                raise ValueError(f"Item is not eligible for this "
                                 f"{'supplied modifier' if declared else 'source Rune'}: {item.item_id}")
            if not declared:
                occupied.add(slot)
            changed = merge_effects(item.effect, modifier)
            inventory[index] = replace(item, effect=changed,
                effect_without_poison=_clean_counterpart(
                    item.effect, item.effect_without_poison, modifier, poison))
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
                    main_weapon_without_poison=_clean_counterpart(
                        fighter.main_weapon, fighter.main_weapon_without_poison, modifier, poison))
            elif slot == "off":
                fighter = replace(fighter, off_hand=changed,
                    off_hand_without_poison=_clean_counterpart(
                        fighter.off_hand, fighter.off_hand_without_poison, modifier, poison))
            elif slot == "extra":
                extra = list(fighter.extra_attacks)
                try:
                    attack_index = extra.index(item.effect)
                except ValueError as exc:
                    raise ValueError(f"{'Item modifier' if declared else 'Rune'}"
                                     " requires the declared extra-hand weapon attack") from exc
                extra[attack_index] = changed
                # An extra-hand weapon is already one independent allocated attack.
                extra.extend(replace(changed, attacks_bonus=0) for _ in range(modifier.attacks_bonus))
                clean_extra = list(fighter.extra_attacks_without_poison)
                if attack_index < len(clean_extra):
                    plain, clean = clean_extra[attack_index]
                    clean_extra[attack_index] = (
                        changed, _clean_counterpart(plain, clean, modifier, poison))
                fighter = replace(fighter, extra_attacks=tuple(extra),
                                  extra_attacks_without_poison=tuple(clean_extra))
            else:
                raise ValueError(f"{'A supplied weapon modifier' if declared else 'Weapon Rune'}"
                                 f" requires an actual weapon hand: {slot}")
    return replace(fighter, mutation_equipment=tuple(inventory))
