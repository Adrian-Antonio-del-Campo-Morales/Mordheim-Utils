"""Compile the equipment configuration used in a vector combat phase."""
from dataclasses import replace

from mordheim_core.models import CompiledFighter, EffectSet
from ._types import has


def phase_equipment(fighter: CompiledFighter, *, first_round: bool,
                    broken_hands: int = 0) -> CompiledFighter:
    def pistol(weapon):
        return weapon is not None and any(has(weapon, tag) for tag in (
            'weapon.pistol', 'weapon.duelling-pistol'))

    main = None if broken_hands & 1 or (not first_round and pistol(fighter.main_weapon)) else fighter.main_weapon
    off = None if broken_hands & 2 or (not first_round and pistol(fighter.off_hand)) else fighter.off_hand
    main_clean, off_clean = fighter.main_weapon_without_poison, fighter.off_hand_without_poison
    slot = fighter.main_hand_slot
    if main is None and off is not None and fighter.off_hand_attacks:
        main, off = off, None
        main_clean, off_clean = off_clean, None
        slot = fighter.off_hand_slot
    if main is None:
        if fighter.unarmed_weapon is None:
            raise ValueError('Equipment loss requires a compiled unarmed fallback')
        main = main_clean = fighter.unarmed_weapon
        slot = 'unarmed'
    return replace(fighter, main_weapon=main, off_hand=off,
        main_weapon_without_poison=main_clean, off_hand_without_poison=off_clean,
        off_hand_attacks=fighter.off_hand_attacks and off is not None, main_hand_slot=slot)


def staff_power(fighter: CompiledFighter, decisions, key: str) -> CompiledFighter:
    if has(fighter.main_weapon, 'weapon.serpent-staff') and (
        decisions is None or decisions.choose(f'{key}.serpent-staff', fighter)
    ):
        return replace(fighter, main_weapon=EffectSet(
            tags=('effect.serpent-staff-power',), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())
    return fighter
