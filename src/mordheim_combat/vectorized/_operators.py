"""Vectorized engine: stateless NumPy projections of the canonical
scalar phase operators."""
from __future__ import annotations

import numpy as np
from mordheim_combat.phases import InjuryContext, ignores_unarmed_penalties, to_hit_target, wound_target
from mordheim_core.models import CompiledFighter, EffectSet
from mordheim_combat.vectorized._types import CombatState, KNOCKED_DOWN, OUT, STANDING, STUNNED, _parry_capacity, has

def to_hit(attacker_ws: int, defender_ws: int) -> int:
    return to_hit_target(attacker_ws, defender_ws)

def hit_targets(attacker_ws: np.ndarray, defender_ws: np.ndarray) -> np.ndarray:
    # The three cases are mutually exclusive, so the table collapses to one
    # arithmetic expression: 4 minus (attacker stronger) plus (defender much
    # stronger), with defender WS 0 always hitting on 2+.
    target = 4 + (defender_ws > 2 * attacker_ws) - (attacker_ws > defender_ws)
    return np.where(defender_ws == 0, 2, target).astype(np.int8)

def wound_targets(strength: np.ndarray, toughness: int | np.ndarray,
                  maximum: int = 7) -> np.ndarray:
    difference = strength - np.broadcast_to(toughness, strength.shape)
    # The wound table is a single descending ramp: 4 - diff clipped to [2, 6],
    # with the "impossible" tail (diff <= -4) as 7. Cheaper than np.select.
    targets = np.clip(4 - difference, 2, 6)
    targets = np.where(difference <= -4, 7, targets)
    return np.minimum(targets, maximum).astype(np.int8)

def injury_conditions(totals: np.ndarray, context: InjuryContext) -> np.ndarray:
    """Independent NumPy projection of the canonical injury table."""
    totals = np.asarray(totals, dtype=np.int16)
    result = np.where(
        totals >= context.out_threshold, OUT,
        np.where(totals >= 3, STUNNED, KNOCKED_DOWN),
    ).astype(np.int8)
    if context.hard_to_kill:
        result = np.where(totals >= 6, OUT, np.where(totals >= 3, STUNNED, KNOCKED_DOWN))
    if context.true_grit:
        result = np.where(totals >= 6, OUT, np.where(totals >= 4, STUNNED, KNOCKED_DOWN))
    if context.concussion and not context.concussion_immune:
        result[(totals >= 2) & (totals <= 4)] = STUNNED
    if context.injury_profile == 1:
        result = np.where(totals >= 4, OUT, np.where(totals >= 2, STUNNED, KNOCKED_DOWN))
    elif context.injury_profile == 3:
        result = np.where(totals >= 4, OUT, KNOCKED_DOWN)
    if context.fragile:
        result[totals == 2] = STUNNED
    if context.poisonous:
        result = np.where(totals >= 5, OUT, np.where(totals >= 2, STUNNED, KNOCKED_DOWN))
    if context.survivor and int(context.initial_condition) == STANDING:
        result[result == OUT] = STUNNED
    if context.head_crusher:
        result[result == KNOCKED_DOWN] = STUNNED
    knocked_down_by_no_pain = context.ignore_pain & (result == STUNNED)
    result[knocked_down_by_no_pain] = KNOCKED_DOWN
    if context.jump_up:
        result[(result == KNOCKED_DOWN) & ~knocked_down_by_no_pain] = STANDING
    if context.mandrake:
        result[result == STUNNED] = KNOCKED_DOWN
    return result.astype(np.int8)

def special_save_targets(defender: CompiledFighter, incoming: EffectSet) -> tuple[int, int]:
    ward = defender.global_effects.ward_save
    if defender.global_effects.step_aside:
        ward = min(ward, 4 if has(defender.global_effects, "skill.vampire-reflexes") else 5)
    if defender.global_effects.step_aside and has(defender.global_effects, "skill.elven-agility"):
        ward = min(ward, 4)
    if defender.global_effects.ward_save_mundane_only and has(incoming, "attack.magical"):
        ward = 7
    regeneration = defender.global_effects.regeneration_save
    if (
        defender.global_effects.regeneration_blocked_by_fire and has(incoming, "attack.fire")
        or defender.global_effects.regeneration_blocked_by_blessed and has(incoming, "attack.blessed")
    ):
        regeneration = 7
    return ward, regeneration

def wound_outcomes(context, rolls: np.ndarray,
                   rerolls: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized canonical wound-roll operator used by runtime verification."""
    rolls = np.asarray(rolls, dtype=np.int16).copy()
    target = max(2, wound_target(context.strength, context.toughness, context.maximum_target) - context.modifier)
    targets = np.full(rolls.size, target, dtype=np.int8)
    if context.automatic:
        return (targets, np.zeros(rolls.size, dtype=np.int16),
                np.ones(rolls.size, dtype=bool), np.zeros(rolls.size, dtype=bool),
                np.zeros(rolls.size, dtype=bool))
    success = rolls >= target
    rerolled = np.zeros(rolls.size, dtype=bool)
    failed = ~success
    if context.reroll and failed.any():
        if rerolls is None:
            raise ValueError("reroll values are required by the wound context")
        rolls[failed] = np.asarray(rerolls, dtype=np.int16)[:int(failed.sum())]
        success[failed] = rolls[failed] >= target
        rerolled[failed] = True
    rolled_success = success.copy()
    success |= context.failure_still_wounds
    critical = (
        rolled_success & context.critical_available & (target < 6)
        & (rolls >= context.critical_threshold)
        & (~rerolled | context.critical_on_reroll)
    )
    return targets, rolls, success, critical, rerolled

def characteristic_test_outcomes(targets: np.ndarray, rolls: np.ndarray, *,
                                 six_fails: bool = False,
                                 rerolls: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Pure vector form of a characteristic test, including an optional reroll."""
    targets = np.asarray(targets, dtype=np.int16)
    final = np.asarray(rolls, dtype=np.int16).copy()
    passed = final <= targets
    if six_fails:
        passed &= final != 6
    failed = ~passed
    if rerolls is not None and failed.any():
        final[failed] = np.asarray(rerolls, dtype=np.int16)[:int(failed.sum())]
        passed[failed] = final[failed] <= targets[failed]
        if six_fails:
            passed[failed] &= final[failed] != 6
    return final, passed

def parry_outcomes(context, rolls: np.ndarray,
                   rerolls: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Pure vector form of the local parry contract."""
    rolls = np.asarray(rolls, dtype=np.int16).copy()
    eligible = bool(
        context.available and not context.cannot_be_parried
        and (context.hit_roll != 6 or context.can_parry_six)
        and context.attacker_strength < 2 * context.defender_strength
    )
    attempted = np.full(rolls.size, eligible, dtype=bool)
    blocked = np.zeros(rolls.size, dtype=bool)
    rerolled = np.zeros(rolls.size, dtype=bool)
    if not eligible:
        return rolls, attempted, blocked, rerolled
    target = context.fixed_target
    blocked = rolls >= target if target is not None else (
        rolls >= context.hit_roll if context.match_allowed else rolls > context.hit_roll
    )
    failed = ~blocked
    if context.reroll and failed.any():
        if rerolls is None:
            raise ValueError("reroll values are required by the parry context")
        rolls[failed] = np.asarray(rerolls, dtype=np.int16)[:int(failed.sum())]
        blocked[failed] = rolls[failed] >= target if target is not None else (
            rolls[failed] >= context.hit_roll if context.match_allowed
            else rolls[failed] > context.hit_roll
        )
        rerolled[failed] = True
    return rolls, attempted, blocked, rerolled

def stun_reaction_outcomes(conditions: np.ndarray, *, thick_skull: bool,
                           helmet_save: int, rolls: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Pure vector form of the Thick Skull/helmet reaction."""
    conditions = np.asarray(conditions, dtype=np.int8).copy()
    rolls = np.asarray(rolls, dtype=np.int16)
    stunned = conditions == STUNNED
    threshold = 2 if thick_skull and helmet_save <= 4 else 3 if thick_skull else helmet_save
    eligible = stunned & (thick_skull or helmet_save <= 6)
    converted = eligible & (rolls >= threshold)
    conditions[converted] = KNOCKED_DOWN
    return conditions, eligible, converted, np.full(conditions.size, threshold, dtype=np.int16)

def recover_round_state(fighter: CompiledFighter, state: CombatState) -> np.ndarray:
    """Advance deterministic start-of-round recovery and return rows that stood up."""
    stood = state.condition == KNOCKED_DOWN
    stunned = state.condition == STUNNED
    state.condition[stunned] = KNOCKED_DOWN
    state.condition[stood] = STANDING
    state.parry_remaining[:] = _parry_capacity(fighter)
    state.critical_used[:] = False
    state.attack_penalty[:] = 0
    return stood

def armour_targets(defender: CompiledFighter, strength: np.ndarray,
                   effect: EffectSet, magical_attack: bool,
                   ignore: np.ndarray | bool = False) -> np.ndarray:
    """Vector form of the canonical `armour_target` contract."""
    modifier = (
        np.maximum(0, strength - 3)
        + effect.armour_penetration
        - effect.target_armour_bonus
    )
    armour = defender.armour_save + modifier
    natural = np.full(strength.size, defender.natural_armour_save, dtype=np.int16)
    if not defender.natural_armour_unmodified:
        natural += modifier
    natural = np.minimum(natural, defender.natural_armour_worst_save)
    if defender.global_effects.natural_armour_negated_by_magic and magical_attack:
        natural[:] = 7
    target = np.minimum(armour, natural).astype(np.int16)
    ignored = np.broadcast_to(ignore, strength.shape) | effect.ignore_armour
    if ignored.any():
        replacement = (
            defender.global_effects.armour_save_floor
            if defender.global_effects.armour_cannot_be_ignored and not magical_attack
            else 7
        )
        target[ignored] = replacement
    if defender.global_effects.armour_save_floor <= 6:
        target = np.minimum(target, defender.global_effects.armour_save_floor)
    return target

def effective_initiative(fighter: CompiledFighter, state: CombatState) -> np.ndarray:
    off_hand_bonus = fighter.off_hand.initiative_bonus if fighter.off_hand is not None else 0
    return np.maximum(
        state.initiative_floor,
        state.initiative
        + fighter.global_effects.initiative_bonus
        + fighter.main_weapon.initiative_bonus
        + off_hand_bonus
        + state.crimson_initiative
        - state.initiative_penalty,
    )

def _characteristic_test(fighter: CompiledFighter, target: np.ndarray,
                         rng: np.random.Generator, *, six_always_fails: bool = False) -> np.ndarray:
    """Resolve a D6 characteristic test, including Blessed Sight's one reroll."""
    rolls = rng.integers(1, 7, target.size)
    passed = rolls <= target
    if six_always_fails:
        passed &= rolls != 6
    failed = ~passed
    if failed.any() and has(fighter.global_effects, "skill.blessed-sight"):
        rerolls = rng.integers(1, 7, int(failed.sum()))
        rerolled = rerolls <= target[failed]
        if six_always_fails:
            rerolled &= rerolls != 6
        passed[failed] = rerolled
    return passed

def attack_count(fighter: CompiledFighter, charging: np.ndarray, first_round: bool = False,
                 frenzy: np.ndarray | None = None, charged: np.ndarray | None = None,
                 attack_penalty: np.ndarray | None = None,
                 wounded: np.ndarray | None = None,
                 base_attacks: np.ndarray | None = None) -> np.ndarray:
    effect = fighter.global_effects
    extra_weapon_attack = int(fighter.off_hand_attacks or fighter.main_weapon.paired)
    base = (
        fighter.characteristics.attacks + effect.attacks_bonus
        + fighter.main_weapon.attacks_bonus
        + (fighter.off_hand.attacks_bonus if fighter.off_hand is not None else 0)
    )
    result = (base_attacks.astype(np.int16,copy=True)+base-fighter.characteristics.attacks
              if base_attacks is not None else np.full(charging.size,base,dtype=np.int16))
    if wounded is not None and has(effect,"maddened_with_pain"):
        result += wounded.astype(np.int16)
    if effect.charge_attacks_bonus and charging.any():
        result += charging.astype(np.int16) * effect.charge_attacks_bonus
    if first_round and effect.first_round_charge_attacks_bonus and charging.any():
        result += charging.astype(np.int16) * effect.first_round_charge_attacks_bonus
    if has(fighter.main_weapon, "weapon.fist") and not ignores_unarmed_penalties(effect):
        result[:] = 1
        extra_weapon_attack = 0
    if has(effect,"skill.unarmed-fighting") and has(fighter.main_weapon,"weapon.fist"):
        result += 1
    if has(effect,"skill.art-of-silent-death") and (has(fighter.main_weapon,"weapon.fist") or has(fighter.main_weapon,"weapon.fighting-claws")):
        result += 1
    if has(effect,"skill.inspiring-sermon"):
        result += 1
    if first_round:
        result += fighter.main_weapon.first_round_attacks_bonus
    if frenzy is not None:
        result[frenzy] *= 2
    elif effect.frenzy:
        result *= 2
    if first_round:
        if has(effect, "skill.ferocious-charge"):
            result[charging] *= 2
    result += extra_weapon_attack
    if has(fighter.main_weapon, "weapon.vomit-attack"):
        result[:] = 1
    if has(effect, "skill.sweep") and fighter.main_weapon.two_handed:
        # Sweep replaces the warrior's normal attacks with a single Initiative
        # test attack; it is not one test for each attack characteristic.
        result[:] = 1
    main_pistol = has(fighter.main_weapon, "weapon.pistol") or has(fighter.main_weapon, "weapon.duelling-pistol")
    off_pistol = bool(fighter.off_hand and (
        has(fighter.off_hand, "weapon.pistol") or has(fighter.off_hand, "weapon.duelling-pistol")
    ))
    if main_pistol:
        if first_round:
            if not fighter.off_hand_attacks:
                result[:] = 1
        elif fighter.off_hand_attacks:
            result = np.maximum(0, result - 1)
        else:
            result[:] = 0
    elif off_pistol and not first_round:
        result = np.maximum(0, result - 1)
    if first_round and (has(effect,"mechanic.body-slam") or has(effect,"mechanic.bull-charge")):
        result[charging] = 1
    if first_round and has(effect,"mechanic.anvil-head"):
        result[charging] = 1
    if has(effect,"mechanic.death-blow") and fighter.characteristics.attacks >= 2:
        result[:] = 1
    if has(effect,"mechanic.energy-focus") and any(
        has(fighter.main_weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks")
    ):
        result = np.maximum(0, result - effect.energy_focus_attacks)
    if attack_penalty is not None:result=np.maximum(0,result-attack_penalty)
    return result

def round_weapon_attack_count(attacker: CompiledFighter, defender: CompiledFighter,
                              count: np.ndarray, *, first_round: bool,
                              charging: np.ndarray, charged: np.ndarray) -> np.ndarray:
    """Apply weapon rules which alter the completed attack pool."""
    result = np.asarray(count, dtype=np.int16).copy()
    if not first_round:
        return result
    if has(attacker.main_weapon, "weapon.serpent-whip"):
        result += (charging | charged).astype(np.int16)
    if has(defender.main_weapon, "weapon.boar-spear"):
        affected = charging & (result > 0)
        result[affected] = np.maximum(1, result[affected] - 1)
    return result

def opposed_attack_count(attacker: CompiledFighter, defender: CompiledFighter,
                         count: np.ndarray, *, first_round: bool) -> np.ndarray:
    """Apply opponent rules to a completed attack pool."""
    result = np.asarray(count, dtype=np.int16).copy()
    active = result > 0
    result[active] = np.maximum(
        1, result[active] + defender.global_effects.incoming_attacks_modifier,
    )
    if has(defender.global_effects, "animal_friendship") and has(
        attacker.global_effects, "species.animal"
    ):
        result[:] = 0
    if (first_round and has(defender.global_effects, "skill.sigmar-s-sign")
            and has(attacker.global_effects, "undead_or_possessed")):
        result[active] = np.maximum(1, result[active] - 1)
    return result

def allocate_attack_weapons(fighter: CompiledFighter, count: int, *, first_round: bool,
                            main_weapon_majority: bool = True) -> tuple[EffectSet, ...]:
    """Prepare the scalar weapon sequence consumed by a vector attack row."""
    if (count > 2 and fighter.off_hand_attacks and fighter.off_hand is not None
            and fighter.main_weapon != fighter.off_hand
            and not any(has(weapon, tag)
                        for weapon in (fighter.main_weapon, fighter.off_hand)
                        for tag in ("weapon.pistol", "weapon.duelling-pistol"))):
        if not main_weapon_majority:
            return (*(fighter.off_hand for _ in range(count - 1)), fighter.main_weapon)
    result: list[EffectSet] = []
    for index in range(count):
        if not fighter.off_hand_attacks or fighter.off_hand is None:
            weapon = fighter.main_weapon
        else:
            main_pistol = any(has(fighter.main_weapon, tag) for tag in (
                "weapon.pistol", "weapon.duelling-pistol",
            ))
            off_pistol = any(has(fighter.off_hand, tag) for tag in (
                "weapon.pistol", "weapon.duelling-pistol",
            ))
            if main_pistol:
                weapon = fighter.off_hand if not first_round or index > 0 else fighter.main_weapon
            elif off_pistol and not first_round:
                weapon = fighter.main_weapon
            else:
                weapon = fighter.off_hand if index == count - 1 else fighter.main_weapon
        result.append(weapon)
    return tuple(result)

def priority(fighter: CompiledFighter, opponent: CompiledFighter, first_round: bool,
             charging: np.ndarray, charged: np.ndarray, stood: np.ndarray) -> np.ndarray:
    weapon_priority = fighter.main_weapon.priority
    if fighter.global_effects.strongman and fighter.main_weapon.two_handed and weapon_priority < 0:
        weapon_priority = 0
    if has(fighter.main_weapon, "weapon.long-boat-hook") and not first_round:
        weapon_priority = 0
    # The spear's Strike First only applies in the first turn of hand-to-hand
    # combat (mordheimer.net, close-combat weapons / Strike First), mirroring
    # the long-boat-hook's first-round scope.
    if has(fighter.main_weapon, "weapon.spear") and not first_round:
        weapon_priority = 0
    value = np.full(charging.size, weapon_priority + fighter.global_effects.priority, dtype=np.int8)
    if has(fighter.global_effects,"mechanic.strike-first-vs-skinks-always") and has(opponent.global_effects,"species.skink"):
        value[:] = 20
    if has(fighter.main_weapon, "weapon.trident"):
        value[charged] = np.maximum(value[charged], 1)
    if first_round:
        value = np.maximum(value, charging.astype(np.int8))
        if has(fighter.global_effects,"mechanic.strike-first-vs-skinks-first-round") and has(opponent.global_effects,"species.skink"):
            value[:] = 20
        if has(fighter.global_effects, "skill.lightning-reflexes"):
            value[charged] = np.maximum(value[charged], 1)
        # Spear: strikes first in the first turn of close combat, even if
        # charged (mordheimer.net, close-combat weapons / Strike First), so
        # it outranks the charger's own strike-first tier.  An opponent with
        # Always Strikes First keeps its unconditional priority and the pair
        # resolves by Initiative instead.
        if has(fighter.main_weapon, "weapon.spear") and not has(
            opponent.global_effects, "skill.always-strikes-first"
        ):
            value[charged] = np.maximum(value[charged], 2)
    if not has(fighter.global_effects, "skill.always-strikes-first"):
        value[stood] = -1
    return value
