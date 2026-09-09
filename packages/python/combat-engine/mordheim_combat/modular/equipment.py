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
                'weapon.steel-whip', 'weapon.beastlash', 'weapon.pirate-scourge', 'weapon.serpent-whip')):
            return weapon
    return None


def equipment_for_state(fighter: CompiledFighter, state: FighterState, *, first_round: bool) -> CompiledFighter:
    main = None if 'main' in state.broken_hands or (not first_round and is_pistol(fighter.main_weapon)) else fighter.main_weapon
    off = None if 'off' in state.broken_hands or (not first_round and is_pistol(fighter.off_hand)) else fighter.off_hand
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
        main_hand_slot=main_slot)
