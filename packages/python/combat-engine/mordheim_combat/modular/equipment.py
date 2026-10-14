"""Equipment that remains usable after ammunition or weapon loss."""
from dataclasses import replace

from mordheim_combat.phases import has_tag
from mordheim_core.models import CompiledFighter, EffectSet
from .state import FighterState


def is_pistol(weapon: EffectSet | None) -> bool:
    return weapon is not None and any(has_tag(weapon, tag) for tag in ('weapon.pistol', 'weapon.duelling-pistol'))


def whipcrack_weapon(fighter: CompiledFighter) -> EffectSet | None:
    for weapon in (fighter.main_weapon, fighter.off_hand):
        if weapon is not None and any(has_tag(weapon, tag) for tag in (
                'weapon.steel-whip', 'weapon.beastlash', 'weapon.pirate-scourge',
                'weapon.serpent-whip', 'weapon.barbed-whip')):
            return weapon
    return None


def equipment_for_state(fighter: CompiledFighter, state: FighterState, *, first_round: bool) -> CompiledFighter:
    if state.transformed or state.equipment_cast_off:
        dagger_tags = ('weapon.dagger', 'weapon.yambiya', 'weapon.poisoned-daggers', 'weapon.disease-dagger')
        retained = next(((weapon, clean, slot) for weapon, clean, slot in (
            (fighter.main_weapon, fighter.main_weapon_without_poison, fighter.main_hand_slot),
            (fighter.off_hand, fighter.off_hand_without_poison, fighter.off_hand_slot))
            if weapon is not None and slot not in state.broken_hands
                and any(has_tag(weapon, tag) for tag in dagger_tags)),
            (fighter.unarmed_weapon, fighter.unarmed_weapon, 'unarmed'))
        main, clean, slot = retained
        retained_extra = None
        retained_extra_clean = None
        if slot == 'unarmed':
            item = next((item for item in fighter.mutation_equipment
                if item.kind == 'weapon' and item.slot is not None
                and (item.slot.startswith('extra.') or item.slot == 'tail')
                and item.slot not in state.broken_hands
                and any(has_tag(item.effect, tag) for tag in dagger_tags)), None)
            if item is not None:
                tags = (f'mutation.hand.{item.slot}', 'mutation.carried-weapon',
                        *(('rule.prehensile-tail',) if item.slot == 'tail' else ()))
                retained_extra = replace(item.effect, tags=(*item.effect.tags, *tags))
                if item.effect_without_poison is not None:
                    retained_extra_clean = replace(item.effect_without_poison,
                        tags=(*item.effect_without_poison.tags, *tags))
        if main is None:
            raise ValueError('A transformed Bitten needs a compiled unarmed fallback')
        effect = fighter.global_effects_without_equipment
        if state.transformed:
            effect = replace(effect, tags=(*effect.tags, 'rule.unarmed-without-penalties'))
        fighter = replace(fighter, main_weapon=main, off_hand=None, off_hand_attacks=False,
            main_weapon_without_poison=clean, off_hand_without_poison=None,
            main_hand_slot=slot, armour_save=max(1, 7-effect.armour_save_bonus), helmet_save=7,
            shield_and_skill_effects=fighter.skill_effects_only, global_effects=effect,
            extra_attacks=(*tuple(attack for attack in fighter.extra_attacks
                if not has_tag(attack, 'mutation.carried-weapon')),
                *((retained_extra,) if retained_extra is not None else ())),
            extra_attacks_without_poison=(*tuple(pair for pair in fighter.extra_attacks_without_poison
                if not has_tag(pair[0], 'mutation.carried-weapon')),
                *((((retained_extra,retained_extra_clean),) if retained_extra_clean is not None else ()))))
    if state.hillman_wolf:
        natural = EffectSet(tags=('weapon.natural-attacks', 'rule.unarmed-without-penalties'))
        # The source discards all equipment until after battle; no in-duel
        # reversion or equipment recovery is printed.
        return replace(fighter, main_weapon=natural, off_hand=None, off_hand_attacks=False,
            main_weapon_without_poison=natural, off_hand_without_poison=None,
            armour_save=7, helmet_save=7, natural_armour_save=7,
            shield_and_skill_effects=EffectSet(),
            global_effects=replace(fighter.global_effects, parry=False,
                armour_save_bonus=0, ward_save=7, regeneration_save=7),
            extra_attacks=(EffectSet(tags=('rule.hillman-bite',), strength_bonus=-1),),
            main_hand_slot='natural')
    main = None if fighter.main_hand_slot in state.broken_hands or (not first_round and is_pistol(fighter.main_weapon)) else fighter.main_weapon
    off = None if fighter.off_hand_slot in state.broken_hands or (not first_round and is_pistol(fighter.off_hand)) else fighter.off_hand
    main_clean, off_clean = fighter.main_weapon_without_poison, fighter.off_hand_without_poison
    main_slot = fighter.main_hand_slot
    if main is None and off is not None and fighter.off_hand_attacks:
        main, off = off, None
        main_clean, off_clean = off_clean, None
        main_slot = fighter.off_hand_slot
    if main is None:
        if fighter.unarmed_weapon is None:
            raise ValueError('A fighter losing its last weapon needs a compiled unarmed fallback')
        main, main_clean = fighter.unarmed_weapon, fighter.unarmed_weapon
        main_slot = 'unarmed'
    return replace(fighter, main_weapon=main, off_hand=off,
        off_hand_attacks=fighter.off_hand_attacks and off is not None,
        main_weapon_without_poison=main_clean, off_hand_without_poison=off_clean,
        main_hand_slot=main_slot,
        extra_attacks=tuple(attack for attack in fighter.extra_attacks if first_round or not is_pistol(attack)))
