"""Equipment that remains usable after ammunition or weapon loss."""
from dataclasses import replace

from mordheim_combat.phases import has_tag
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter, EffectSet
from .state import FighterState


def is_pistol(weapon: EffectSet | None) -> bool:
    return weapon is not None and any(has_tag(weapon, tag) for tag in ('weapon.pistol', 'weapon.duelling-pistol'))


def pistol_as_club(weapon: EffectSet) -> EffectSet:
    """The club one printed bearer keeps in hand once a pistol's shot is spent.

    A spent pistol is normally discarded, but the Slayer Pirate's Festooned
    with Pistols clause counts it as a club in the rounds after the opening one.
    The club profile therefore replaces the pistol: Strength as the user with
    Concussion, while the pistol's fixed Strength, armour penetration and
    opening-round properties leave with it.  The bearer's material identity is
    carried over so armour and material rules still read it.
    """
    material = tuple(tag for tag in weapon.tags if tag.startswith('material.'))
    return EffectSet(tags=(*material, 'weapon.mace'), concussion=True)


def whipcrack_weapon(fighter: CompiledFighter) -> EffectSet | None:
    for weapon in (fighter.main_weapon, fighter.off_hand):
        if weapon is not None and any(has_tag(weapon, tag) for tag in (
                'weapon.steel-whip', 'weapon.beastlash', 'weapon.pirate-scourge',
                'weapon.serpent-whip', 'weapon.barbed-whip', 'weapon.thinglash')):
            return weapon
    return None


def _without_discarded_bonuses(characteristics, items, kept_slots):
    """Retire the numeric bonuses of the equipment a transformation casts off.

    A bonus an item folded into the compiled profile - Att'la's Plate Mail's
    extra Wound - lasts exactly as long as the item is worn, so the discarded
    items' bonuses leave the profile and the current Wounds follow the reduced
    maximum.
    """
    bonuses = {}
    for item in items:
        if item.slot is None or item.slot in kept_slots:
            continue
        for stat, amount in item.stat_bonuses:
            bonuses[stat] = bonuses.get(stat, 0) + amount
    if not bonuses:
        return characteristics
    values = {}
    for stat, amount in bonuses.items():
        current = getattr(characteristics, stat)
        if current is None:
            continue
        values[stat] = max(1, current - amount) if stat == 'wounds' else max(0, current - amount)
    return replace(characteristics, **values)


def equipment_for_state(fighter: CompiledFighter, state: FighterState, *, first_round: bool) -> CompiledFighter:
    lost = tuple(item for item in fighter.mutation_equipment
                 if item.slot in state.broken_hands and item.kind in {'armour', 'defence'})
    if lost:
        # Read each physical piece's declared contribution, including runes and
        # maintenance, rather than leaving its bonus/identity in the total.
        lost_slots = {item.slot for item in lost}
        kept = tuple(item for item in fighter.mutation_equipment if item.slot not in lost_slots)
        innate = fighter.global_effects_without_equipment
        kept_tags = set(innate.tags).union(*(item.effect.tags for item in kept if item.slot is not None))
        removed_tags = set().union(*(item.effect.tags for item in lost)) - kept_tags
        bonus = sum(item.effect.armour_save_bonus for item in lost)
        worn = tuple(item.effect for item in kept if item.slot is not None
                     and item.kind in {'armour', 'defence'})
        globals_ = replace(fighter.global_effects,
            tags=tuple(tag for tag in fighter.global_effects.tags if tag not in removed_tags),
            armour_save_bonus=fighter.global_effects.armour_save_bonus-bonus,
            parry=innate.parry or any(effect.parry for effect in worn),
            ward_save=min((innate.ward_save, *(effect.ward_save for effect in worn))))
        shields = fighter.skill_effects_only
        for item in kept:
            if item.slot is not None and any(has_tag(item.effect, tag) for tag in (
                    'defence.shield', 'defence.buckler', 'defence.kite-shield')):
                shields = merge_effects(shields, item.effect)
        fighter = replace(fighter, armour_save=fighter.armour_save+bonus,
            global_effects=globals_, shield_and_skill_effects=shields,
            mutation_equipment=tuple(replace(item, slot=None) if item.slot in lost_slots else item
                                     for item in fighter.mutation_equipment))
    if state.transformed or state.equipment_cast_off:
        dagger_tags = ('weapon.dagger', 'weapon.yambiya', 'weapon.poisoned-daggers', 'weapon.disease-dagger')
        retained = next(((weapon, clean, slot) for weapon, clean, slot in (
            (fighter.main_weapon, fighter.main_weapon_without_poison, fighter.main_hand_slot),
            (fighter.off_hand, fighter.off_hand_without_poison, fighter.off_hand_slot))
            if weapon is not None and slot not in state.broken_hands
                and any(has_tag(weapon, tag) for tag in dagger_tags)),
            (fighter.unarmed_weapon, fighter.unarmed_weapon, 'unarmed'))
        main, clean, slot = retained
        # Only the item this branch keeps keeps its folded-in bonuses.
        kept_slots = set() if slot == 'unarmed' else {slot}
        retained_extra = None
        retained_extra_clean = None
        if slot == 'unarmed':
            item = next((item for item in fighter.mutation_equipment
                if item.kind == 'weapon' and item.slot is not None
                and (item.slot.startswith('extra.') or item.slot == 'tail')
                and item.slot not in state.broken_hands
                and any(has_tag(item.effect, tag) for tag in dagger_tags)), None)
            if item is not None:
                kept_slots.add(item.slot)
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
            characteristics=_without_discarded_bonuses(
                fighter.characteristics, fighter.mutation_equipment, kept_slots),
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
            characteristics=_without_discarded_bonuses(
                fighter.characteristics, fighter.mutation_equipment, frozenset()),
            armour_save=7, helmet_save=7, natural_armour_save=7,
            shield_and_skill_effects=EffectSet(),
            global_effects=replace(fighter.global_effects, parry=False,
                armour_save_bonus=0, ward_save=7, regeneration_save=7),
            extra_attacks=(EffectSet(tags=('rule.hillman-bite',), strength_bonus=-1),),
            main_hand_slot='natural')
    # A Festooned with Pistols bearer keeps his spent pistol as a club instead
    # of losing it, so every place that discards a spent pistol substitutes the
    # club profile for that bearer and leaves ordinary bearers discarded.
    festooned = has_tag(fighter.global_effects, 'mechanic.festooned-with-pistols')
    def after_the_opening_round(weapon: EffectSet | None) -> EffectSet | None:
        if weapon is None or first_round or not is_pistol(weapon):
            return weapon
        return pistol_as_club(weapon) if festooned else None
    broken = state.broken_hands
    broken_extra = tuple(item.effect for item in fighter.mutation_equipment
                         if item.slot == 'extra' and item.slot in broken)
    main = after_the_opening_round(fighter.main_weapon) if fighter.main_hand_slot not in broken else None
    off = after_the_opening_round(fighter.off_hand) if fighter.off_hand_slot not in broken else None
    main_clean = after_the_opening_round(fighter.main_weapon_without_poison)
    off_clean = after_the_opening_round(fighter.off_hand_without_poison)
    main_slot = fighter.main_hand_slot
    if main is None and off is not None and fighter.off_hand_attacks:
        main, off = off, None
        main_clean, off_clean = off_clean, None
        main_slot = fighter.off_hand_slot
    if main is None:
        # Dropped pieces remain unavailable; a separately carried backup is a
        # distinct physical item, selected in the caller's declared kit order.
        backup = next(((index, item, candidate) for index, item in enumerate(fighter.mutation_equipment)
            if item.slot is None and item.kind == 'weapon' and f'backup.{index}' not in broken
            and any(tag.startswith('weapon.') for tag in item.effect.tags)
            and (candidate := after_the_opening_round(item.effect)) is not None), None)
        if backup is not None:
            index, item, main = backup
            main_clean = item.effect_without_poison or main
            main_slot = f'backup.{index}'
    if main is None:
        if fighter.unarmed_weapon is None:
            raise ValueError('A fighter losing its last weapon needs a compiled unarmed fallback')
        main, main_clean = fighter.unarmed_weapon, fighter.unarmed_weapon
        main_slot = 'unarmed'
    return replace(fighter, main_weapon=main, off_hand=off,
        off_hand_attacks=fighter.off_hand_attacks and off is not None,
        main_weapon_without_poison=main_clean, off_hand_without_poison=off_clean,
        main_hand_slot=main_slot,
        extra_attacks=tuple(kept for kept in
            (after_the_opening_round(attack) for attack in fighter.extra_attacks
             if attack not in broken_extra) if kept is not None))
