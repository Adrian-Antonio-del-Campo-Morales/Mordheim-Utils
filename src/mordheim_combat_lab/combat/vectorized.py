"""combat.vectorized: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from functools import lru_cache
from mordheim_combat_lab.combat.phases import InjuryContext
from mordheim_combat_lab.combat.phases import bear_hug_wins
from mordheim_combat_lab.combat.phases import ignores_unarmed_penalties
from mordheim_combat_lab.combat.phases import to_hit_target
from mordheim_combat_lab.combat.phases import wound_target
from mordheim_combat_lab.domain.dice import AlwaysAccept
from mordheim_combat_lab.domain.dice import DecisionPolicy
from mordheim_combat_lab.domain.effects import merge_effects
from mordheim_combat_lab.domain.models import CompiledFighter
from mordheim_combat_lab.domain.models import DuelRequest
from mordheim_combat_lab.domain.models import DuelResult
from mordheim_combat_lab.domain.models import EffectSet
from mordheim_combat_lab.domain.models import SimulationCancelled
import numpy as np


STANDING, KNOCKED_DOWN, STUNNED, PARALYZED, OUT = range(5)


@dataclass(slots=True)
class CombatState:
    wounds: np.ndarray
    condition: np.ndarray
    initiative_penalty: np.ndarray
    initiative_floor: np.ndarray
    frenzy: np.ndarray
    lucky_charm: np.ndarray
    crimson_initiative: np.ndarray
    attack_penalty: np.ndarray
    entangled: np.ndarray
    parry_used: np.ndarray
    parry_remaining: np.ndarray
    critical_used: np.ndarray
    force_of_will_used: np.ndarray
    force_of_will_active: np.ndarray
    force_of_will_penalty: np.ndarray
    disability: np.ndarray
    mark_of_old_ones_used: np.ndarray
    luck_used: np.ndarray
    on_fire: np.ndarray
    weapon_skill: np.ndarray
    strength: np.ndarray
    toughness: np.ndarray
    initiative: np.ndarray
    attacks: np.ndarray


@dataclass(slots=True)
class PreparedAttack:
    weapon: EffectSet
    effect: EffectSet
    active: np.ndarray
    strength: np.ndarray
    armour_strength: np.ndarray
    hit_target: np.ndarray
    rolls: np.ndarray
    hit_rows: np.ndarray
    rerolled: np.ndarray


@dataclass(slots=True)
class VectorAttackObservation:
    """Single-row phase observation used by exact semantic replay."""
    hit: bool = False
    hit_roll: int | None = None
    hit_target: int | None = None
    parried: bool = False
    wounded: bool = False
    saved: bool = False
    damage: int = 0
    critical: bool = False


@dataclass(frozen=True, slots=True)
class VectorBatchObservation:
    """Per-row terminal state exposed only to verification and diagnostics."""

    winner: np.ndarray
    rounds: np.ndarray
    first_wounds: np.ndarray
    second_wounds: np.ndarray
    first_condition: np.ndarray
    second_condition: np.ndarray
    first_resources: tuple[tuple[str, np.ndarray], ...]
    second_resources: tuple[tuple[str, np.ndarray], ...]


@dataclass(frozen=True, slots=True)
class OptionalPhasePlan:
    """Immutable switches for stateful phases that a duel can never enter."""

    first_force_of_will: bool
    second_force_of_will: bool
    first_spines: bool
    second_spines: bool
    first_netter: bool
    second_netter: bool
    first_black_hunger: bool
    second_black_hunger: bool
    first_entangle: bool
    second_entangle: bool
    first_can_burn: bool
    second_can_burn: bool


def has(effect: EffectSet, mechanic_id: str) -> bool:
    return mechanic_id in effect.tags


def _has_weapon_tag(fighter: CompiledFighter, mechanic_id: str) -> bool:
    return any(has(weapon, mechanic_id) for weapon in (
        fighter.main_weapon,
        *((fighter.off_hand,) if fighter.off_hand is not None else ()),
        *fighter.extra_attacks,
    ))


def _can_ignite(attacker: CompiledFighter, defender: CompiledFighter) -> bool:
    """Whether any ordinary attack in this matchup can set the defender on fire."""
    weapons = (
        attacker.main_weapon,
        *((attacker.off_hand,) if attacker.off_hand is not None else ()),
        *attacker.extra_attacks,
    )
    return any(
        _compiled_attack_effect(attacker, defender, weapon)[1].ignition_threshold <= 6
        for weapon in weapons
    )


def _optional_phase_plan(first: CompiledFighter, second: CompiledFighter) -> OptionalPhasePlan:
    """Compile optional round phases once instead of probing them for every round."""
    return OptionalPhasePlan(
        first_force_of_will=has(first.global_effects, "mechanic.force-of-will"),
        second_force_of_will=has(second.global_effects, "mechanic.force-of-will"),
        first_spines=has(first.global_effects, "spines"),
        second_spines=has(second.global_effects, "spines"),
        first_netter=has(first.global_effects, "mechanic.netter"),
        second_netter=has(second.global_effects, "mechanic.netter"),
        first_black_hunger=has(first.global_effects, "mechanic.black-hunger"),
        second_black_hunger=has(second.global_effects, "mechanic.black-hunger"),
        first_entangle=_has_weapon_tag(first, "weapon.chained-squig"),
        second_entangle=_has_weapon_tag(second, "weapon.chained-squig"),
        first_can_burn=_can_ignite(second, first),
        second_can_burn=_can_ignite(first, second),
    )


def _parry_capacity(fighter: CompiledFighter) -> int:
    """Return the number of parries available in a close-combat phase."""
    effects = fighter.global_effects
    available = sum((
        fighter.main_weapon.parry,
        bool(fighter.off_hand and fighter.off_hand.parry),
        effects.parry,
        has(effects, "skill.miniath"),
        has(effects, "skill.axe-master") and any(
            has(weapon, tag)
            for weapon in (fighter.main_weapon, fighter.off_hand or EffectSet())
            for tag in ("weapon.axe", "weapon.dwarf-axe")
        ),
        has(effects, "skill.shield-mastery") and has(effects, "defence.shield"),
    ))
    return min(2 if has(effects, "skill.unbeatable-warrior") else 1, int(available))


def _claim_criticals(candidate: np.ndarray, rows: np.ndarray, state: CombatState) -> np.ndarray:
    """Allow at most one critical per attacker and close-combat phase."""
    accepted = np.zeros(candidate.size, dtype=bool)
    positions = np.flatnonzero(candidate)
    if positions.size == 0:
        return accepted
    eligible = positions[~state.critical_used[rows[positions]]]
    if eligible.size == 0:
        return accepted
    claimed_rows, first = np.unique(rows[eligible], return_index=True)
    accepted[eligible[first]] = True
    state.critical_used[claimed_rows] = True
    return accepted


def _critical_wound_threshold(effect: EffectSet, weapon: EffectSet, poison_blocked: bool) -> int:
    """Return the natural To Wound roll that produces a critical hit."""
    if (has(effect, "poison.wolfsbane") and not poison_blocked) or has(effect, "mechanic.body-slam"):
        return 5
    if has(effect, "skill.art-of-silent-death"):
        return 5
    if has(effect, "skill.unarmed-critical-strikes") and has(weapon, "weapon.fist"):
        return 5
    return 6


def to_hit(attacker_ws: int, defender_ws: int) -> int:
    return to_hit_target(attacker_ws, defender_ws)


def hit_targets(attacker_ws: np.ndarray, defender_ws: np.ndarray) -> np.ndarray:
    return np.where(
        defender_ws == 0, 2,
        np.where(attacker_ws > defender_ws, 3,
                 np.where(defender_ws > 2 * attacker_ws, 5, 4)),
    ).astype(np.int8)


def wound_targets(strength: np.ndarray, toughness: int | np.ndarray,
                  maximum: int = 7) -> np.ndarray:
    difference = strength - np.broadcast_to(toughness, strength.shape)
    targets = np.select(
        (difference >= 2, difference == 1, difference == 0,
         difference == -1, difference >= -3),
        (2, 3, 4, 5, 6),
        default=7,
    )
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
    result += charging.astype(np.int16) * effect.charge_attacks_bonus
    if first_round:
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
    if not has(fighter.global_effects, "skill.always-strikes-first"):
        value[stood] = -1
    return value


def _parry_hits(defender: CompiledFighter, effect: EffectSet, hit_rows: np.ndarray,
                hit_values: np.ndarray, hit_strength: np.ndarray,
                defender_state: CombatState,
                rng: np.random.Generator,
                selected_rows: np.ndarray | None = None) -> tuple[np.ndarray,np.ndarray]:
    if effect.cannot_be_parried:
        return hit_rows,np.empty(0,dtype=np.int64)
    parry = (defender.main_weapon.parry or bool(defender.off_hand and defender.off_hand.parry)
             or defender.global_effects.parry or has(defender.global_effects,"skill.miniath"))
    parry |= has(defender.global_effects,"skill.axe-master") and (
        has(defender.main_weapon,"weapon.axe")
        or bool(defender.off_hand and has(defender.off_hand,"weapon.axe"))
    )
    parry |= has(defender.global_effects,"skill.shield-mastery") and bool(defender.off_hand and has(defender.off_hand,"defence.shield"))
    if not parry or hit_rows.size == 0:
        return hit_rows,np.empty(0,dtype=np.int64)
    eligible = ((defender_state.condition[hit_rows] == STANDING)
                & (defender_state.parry_remaining[hit_rows] > 0)
                & (hit_strength < 2 * defender_state.strength[hit_rows]))
    if selected_rows is not None:
        # ``resolve_attacks`` has already selected the highest one or two hits
        # for each duel row across the complete attack pool. Repeating that
        # grouping here would introduce a Python loop per simulated duel.
        eligible &= np.isin(hit_rows, selected_rows)
    else:
        eligible_rows = np.unique(hit_rows[eligible])
        # Keep the standalone operator correct for callers that pass several
        # hits for the same row without the pool-level preselection.
        if eligible_rows.size != np.count_nonzero(eligible):
            highest = np.zeros(hit_rows.size, dtype=bool)
            for row in eligible_rows:
                positions = np.flatnonzero((hit_rows == row) & eligible)
                limit = int(defender_state.parry_remaining[row])
                highest[positions[np.argsort(hit_values[positions])[-limit:]]] = True
            eligible &= highest
    if not eligible.any():
        return hit_rows,np.empty(0,dtype=np.int64)
    parry_roll = rng.integers(1, 7, hit_rows.size)
    match_allowed = any(has(defender.global_effects,x) for x in ("skill.sword-master","skill.swordmaster","skill.defensive-stance","skill.unbeatable-warrior"))
    starblade = has(defender.main_weapon, "weapon.starblade") or bool(
        defender.off_hand and has(defender.off_hand, "weapon.starblade")
    )
    parry_success = parry_roll >= 4 if starblade else (
        (parry_roll >= hit_values) if match_allowed else (parry_roll > hit_values)
    )
    can_parry_six = has(defender.global_effects, "rule.blood-dragon-sword-master")
    blockable_roll = (hit_values != 6) | can_parry_six
    blocked = eligible & blockable_roll & parry_success
    dwarf_axes = has(defender.main_weapon,"weapon.dwarf-axe") and bool(defender.off_hand and has(defender.off_hand,"weapon.dwarf-axe"))
    miniath_reroll = (has(defender.global_effects,"skill.miniath")
                      and (defender.main_weapon.parry or bool(defender.off_hand and defender.off_hand.parry)))
    sword_and_buckler = (
        (has(defender.main_weapon,"weapon.sword") or bool(defender.off_hand and has(defender.off_hand,"weapon.sword")))
        and (has(defender.global_effects,"defence.buckler")
             or bool(defender.off_hand and has(defender.off_hand,"defence.buckler")))
    )
    sword_master_reroll = has(defender.global_effects,"skill.sword-master") and (
        not has(defender.global_effects,"rule.dwarf-axe-parry-reroll") or dwarf_axes
    )
    reroll = (miniath_reroll or sword_and_buckler or sword_master_reroll
              or has(defender.main_weapon,"weapon.double-bladed-sword"))
    if reroll and (~blocked).any():
        second = rng.integers(1, 7, hit_rows.size)
        second_success = second >= 4 if starblade else (
            (second >= hit_values) if match_allowed else (second > hit_values)
        )
        blocked |= eligible & blockable_roll & second_success
    defender_state.parry_used[hit_rows[eligible]] = True
    defender_state.parry_remaining[hit_rows[eligible]] -= 1
    return hit_rows[~blocked],hit_rows[blocked]


@lru_cache(maxsize=1024)
def _compiled_attack_effect(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
) -> tuple[EffectSet, EffectSet, bool]:
    """Compile immutable weapon/global interactions outside the hot row loop."""
    poison_immune = defender.global_effects.poison_immunity or has(
        defender.global_effects, "poison_immune"
    )
    if poison_immune:
        if weapon == attacker.main_weapon and attacker.main_weapon_without_poison is not None:
            weapon = attacker.main_weapon_without_poison
        elif weapon == attacker.off_hand and attacker.off_hand_without_poison is not None:
            weapon = attacker.off_hand_without_poison
    effect = weapon if has(weapon,"mechanic.body-slam") else merge_effects(
        weapon, attacker.global_effects,
    )
    if has(effect, "mechanic.death-blow") and attacker.characteristics.attacks < 2:
        effect = replace(
            effect,
            hit_modifier=effect.hit_modifier - 1,
            wound_modifier=effect.wound_modifier - 1,
            injury_modifier=effect.injury_modifier - 1,
        )
    unarmed_adjustment = ignores_unarmed_penalties(effect) and has(weapon,"weapon.fist")
    if unarmed_adjustment:
        effect = merge_effects(effect, EffectSet(target_armour_bonus=-1))
    return weapon, effect, unarmed_adjustment


def _prepare_weapon_attack(attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
                           active: np.ndarray, charging: np.ndarray,
                           attacker_state: CombatState, defender_state: CombatState,
                           rng: np.random.Generator,
    first_round: bool) -> PreparedAttack | None:
    if active.size == 0:
        return None
    weapon, effect, unarmed_adjustment = _compiled_attack_effect(attacker, defender, weapon)
    stunned = active[defender_state.condition[active] == STUNNED]
    defender_state.condition[stunned] = OUT
    active = active[defender_state.condition[active] != OUT]
    if active.size == 0:
        return None
    charge_rows = charging[active]
    strength = (np.full(active.size,effect.fixed_strength,dtype=np.int16) if effect.fixed_strength
                else attacker_state.strength[active]+effect.strength_bonus)
    if unarmed_adjustment:
        strength += 1
    if has(effect,"mechanic.energy-focus") and any(
        has(weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks")
    ):
        strength += effect.energy_focus_attacks
    if has(weapon, "rule.scorpion-tail") and (
        defender.global_effects.poison_immunity or has(defender.global_effects, "poison_immune")
    ):
        strength[:] = 2
    retain_named_weapon_bonus = (
        has(effect,"mechanic.retain-flail-morning-star-strength-bonus")
        and any(has(weapon,tag) for tag in ("weapon.flail","weapon.morning-star"))
    )
    if first_round or has(effect,"skill.tireless") or has(effect,"skill.mighty-biceps") or retain_named_weapon_bonus:
        strength += weapon.first_round_strength_bonus
    if first_round:
        mounted_only = any(has(weapon, tag) for tag in ("weapon.lance", "weapon.boar-spear"))
        if not mounted_only or attacker.mounted:
            strength += charge_rows.astype(np.int16) * effect.charge_strength_bonus
    armour_strength = strength + effect.armour_strength_modifier
    if defender.global_effects.incoming_strength_modifier:
        strength = np.maximum(1, strength + defender.global_effects.incoming_strength_modifier)
    attacker_ws = attacker_state.weapon_skill[active] + weapon.weapon_skill_bonus
    knife_fighting=has(effect,"skill.knife-fighting") and (
        has(weapon,"weapon.dagger") or has(weapon,"weapon.yambiya")
    )
    attacker_ws += int(knife_fighting)
    if first_round:
        attacker_ws_values = attacker_ws + charge_rows.astype(np.int8) * effect.charge_ws_bonus
    else:
        attacker_ws_values = attacker_ws
    hit_target = hit_targets(attacker_ws_values, defender_state.weapon_skill[active])
    modifier = np.full(active.size, effect.hit_modifier, dtype=np.int8)
    modifier += defender.global_effects.incoming_hit_modifier
    if has(defender.global_effects, "rule.putrid-stench") and has(
        attacker.global_effects, "undead_or_possessed"
    ):
        modifier += 1
    if has(effect, "skill.berserker"):
        modifier += charge_rows.astype(np.int8)
    if first_round and has(attacker.global_effects, "skill.ferocious-charge"):
        modifier[charge_rows] -= 1
    if first_round and has(defender.global_effects, "skill.bellowing-battle-roar"):
        modifier -= 1
    if has(defender.global_effects,"cloud_of_flies"):
        modifier -= 1
    hit_target = np.clip(hit_target - modifier, 2, 6)
    if has(effect,"skill.sweep") and weapon.two_handed:
        failed_tests = ~_characteristic_test(defender, defender_state.initiative[active], rng)
        rolls=np.where(failed_tests,6,1).astype(np.int8);successful=failed_tests
    else:
        rolls = np.full(active.size, 6, dtype=np.int8) if effect.automatic_hit else rng.integers(1, 7, active.size, dtype=np.int8)
        successful = rolls >= hit_target
    helpless = np.isin(defender_state.condition[active], (KNOCKED_DOWN, PARALYZED))
    successful |= helpless
    rolls[helpless] = 1
    reroll = np.full(active.size, effect.reroll_hits, dtype=bool)
    reroll |= charge_rows & effect.charge_reroll_hits
    reroll |= charge_rows & has(effect, "rule.berserk-charge") & any(
        has(weapon, tag) for tag in (
            "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
        )
    )
    reroll |= first_round and has(effect, "skill.hatred")
    amazon_enemy=any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in defender.global_effects.tags
    )
    reroll |= first_round and has(attacker.global_effects,"mechanic.amazon-isolationists") and amazon_enemy
    reroll |= charge_rows & has(effect, "skill.infallible")
    reroll |= charge_rows & first_round & has(effect,"skill.axe-expert") & (has(weapon,"weapon.axe") or has(weapon,"weapon.dwarf-axe"))
    reroll |= charge_rows & first_round & has(effect,"skill.expert-swordsman") & any(has(weapon,x) for x in ("weapon.sword","weapon.scimitar","weapon.weeping-blades"))
    reroll |= first_round & has(effect,"skill.crack-shot") & any(has(weapon,x) for x in ("weapon.pistol","weapon.duelling-pistol"))
    reroll |= charge_rows & has(attacker.global_effects,"dagger_master") & (has(weapon,"weapon.dagger") or has(weapon,"weapon.yambiya"))
    reroll |= has(effect,"skill.weapons-of-the-north") and any(
        has(weapon, tag) for tag in (
            "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
        )
    )
    reroll |= first_round and has(effect,"skill.duellist")
    luck = has(effect,"skill.luck") & ~attacker_state.luck_used[active] & ~reroll
    reroll |= luck
    if has(effect, "skill.virtue-of-valour"):
        reroll |= defender_state.strength[active]>attacker_state.strength[active]
    rerolled = np.zeros(active.size, dtype=bool)
    failed = np.flatnonzero(reroll & ~successful)
    if failed.size:
        rerolled[failed] = True
        rerolls = rng.integers(1, 7, failed.size)
        successful[failed] = rerolls >= hit_target[failed]
        rolls[failed] = rerolls
        luck_failed = failed[luck[failed]]
        attacker_state.luck_used[active[luck_failed]] = True
    if has(attacker.global_effects,"mechanic.mark-of-the-old-ones"):
        available=(~successful)&(~attacker_state.mark_of_old_ones_used[active])
        chosen=np.flatnonzero(available)
        if chosen.size:
            # Each duel row represents one independent warrior, so each may
            # convert its first failed roll once per battle.
            successful[chosen]=True
            rolls[chosen]=hit_target[chosen]
            attacker_state.mark_of_old_ones_used[active[chosen]]=True
    hit_rows = active[successful]
    if has(defender.global_effects,"mechanic.spider-infested"):
        missed=active[~successful]
        np.add.at(attacker_state.initiative_penalty,missed,1)
        attacker_state.initiative_floor[missed]=0
    return PreparedAttack(
        weapon, effect, active, strength, armour_strength, hit_target,
        rolls, hit_rows, rerolled,
    )


def _apply_hit_defences(
    attacker: CompiledFighter, defender: CompiledFighter, prepared: PreparedAttack,
    attacker_state: CombatState, defender_state: CombatState,
    rng: np.random.Generator, charging: np.ndarray,
    parry_rows: np.ndarray | None = None,
) -> np.ndarray:
    """Resolve the hit-to-parry boundary once and return surviving hits."""
    weapon,effect,active,strength,rolls = (
        prepared.weapon,prepared.effect,prepared.active,prepared.strength,prepared.rolls
    )
    hit_rows=prepared.hit_rows[defender_state.condition[prepared.hit_rows]!=OUT]
    hit_positions=np.searchsorted(active,hit_rows)
    hit_values=rolls[hit_positions]
    hit_rows,parried_rows=_parry_hits(
        defender,effect,hit_rows,hit_values,strength[hit_positions],defender_state,rng,parry_rows
    )
    if parried_rows.size and has(defender.global_effects,"mechanic.spider-infested"):
        np.add.at(attacker_state.initiative_penalty,parried_rows,1)
        attacker_state.initiative_floor[parried_rows]=0
    if (
        parried_rows.size
        and (has(defender.main_weapon,"weapon.cutlass")
             or bool(defender.off_hand and has(defender.off_hand,"weapon.cutlass")))
        and not has(weapon,"effect.cutlass-counter")
    ):
        counter=EffectSet(tags=("effect.cutlass-counter",))
        _resolve_weapon(
            defender,attacker,counter,parried_rows,np.zeros(charging.size,dtype=bool),
            defender_state,attacker_state,rng,False,
        )
    if hit_rows.size and defender_state.lucky_charm[hit_rows].any():
        eligible=defender_state.lucky_charm[hit_rows]
        charm_rolls=rng.integers(1,7,hit_rows.size)
        defender_state.lucky_charm[hit_rows[eligible]]=False
        hit_rows=hit_rows[~(eligible&(charm_rolls>=4))]
    return hit_rows


def _resolve_weapon(attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
                    active: np.ndarray, charging: np.ndarray, attacker_state: CombatState,
                    defender_state: CombatState, rng: np.random.Generator, first_round: bool,
                    prepared: PreparedAttack | None = None,
                    parry_rows: np.ndarray | None = None,
                    defender_phase_condition: np.ndarray | None = None,
                    decisions: DecisionPolicy | None = None,
                    defences_resolved: bool = False,
                    observation: VectorAttackObservation | None = None) -> None:
    prepared = prepared or _prepare_weapon_attack(attacker,defender,weapon,active,charging,attacker_state,defender_state,rng,first_round)
    if prepared is None:
        return
    weapon,effect,active,strength,armour_strength,hit_target,rolls,hit_rows = (
        prepared.weapon,prepared.effect,prepared.active,prepared.strength,prepared.armour_strength,
        prepared.hit_target,prepared.rolls,prepared.hit_rows)
    if observation is not None and active.size:
        observation.hit_target = int(hit_target[0])
        observation.hit_roll = int(rolls[0])
        observation.hit = bool(hit_rows.size)
    knife_fighting=has(effect,"skill.knife-fighting") and (has(weapon,"weapon.dagger") or has(weapon,"weapon.yambiya"))
    if not defences_resolved:
        parries_before = defender_state.parry_remaining.copy()
        charms_before = defender_state.lucky_charm.copy()
        hit_rows=_apply_hit_defences(
            attacker,defender,prepared,attacker_state,defender_state,rng,charging,parry_rows
        )
        if observation is not None and prepared.hit_rows.size and hit_rows.size == 0:
            row = int(prepared.hit_rows[0])
            observation.parried = defender_state.parry_remaining[row] < parries_before[row]
            observation.saved = bool(charms_before[row] and not defender_state.lucky_charm[row]
                                     and not observation.parried)
    if hit_rows.size == 0:
        return
    hit_positions = np.searchsorted(active, hit_rows)
    hit_values = rolls[hit_positions]
    if has(weapon,"weapon.kusara-kama"):
        penalized=hit_rows[hit_values>=5];np.add.at(defender_state.attack_penalty,penalized,1)
    if has(weapon,"weapon.chained-squig"):
        defender_state.entangled[hit_rows]=True
    if has(effect,"mechanic.anvil-head"):
        repeats=rng.integers(1,4,hit_rows.size)
        hit_rows=np.repeat(hit_rows,repeats)
        hit_positions=np.repeat(hit_positions,repeats)
        hit_values=np.repeat(hit_values,repeats)
    ignition_target=(
        min(effect.ignition_threshold,defender.global_effects.caught_fire_threshold)
        if effect.ignition_threshold <= 6 else 7
    )
    if ignition_target<=6 and hit_rows.size:
        ignited=rng.integers(1,7,hit_rows.size)>=ignition_target
        defender_state.on_fire[hit_rows[ignited]]=True
    poison_blocked = defender.global_effects.poison_immunity or has(defender.global_effects, "poison_immune")
    automatic_wound = (
        np.ones(hit_rows.size,dtype=bool)
        if has(effect,"effect.automatic-wound")
        else (hit_values == 6)
        if ((has(effect,"poison.black-lotus") and not poison_blocked) or has(effect,"wight_blades"))
        else np.zeros(hit_rows.size,dtype=bool)
    )
    strength_hits = strength[hit_positions]
    armour_strength_hits = armour_strength[hit_positions]
    toughness = defender_state.toughness[hit_rows]
    raw_targets = wound_targets(strength_hits, toughness, effect.maximum_wound_target)
    targets = np.minimum(raw_targets,4) if has(effect,"skill.monster-slayer") else raw_targets
    # A positive modifier improves the wound roll (for example, Manbane and
    # Expert Fighter), while a natural 1 remains a failed wound roll.
    sigmarite_bonus = int(
        has(weapon, "weapon.sigmarite-hammer")
        and has(defender.global_effects, "undead_or_possessed")
    )
    targets = np.maximum(2, targets - effect.wound_modifier - sigmarite_bonus)
    wound_rolls = rng.integers(1, 7, hit_rows.size)
    critical_rolls = wound_rolls.copy()
    wounded = automatic_wound | (wound_rolls >= targets)
    if has(weapon,"weapon.rapier") and (~wounded).any():
        failed=np.flatnonzero(~wounded);extra_hits=rng.integers(1,7,failed.size)>=np.minimum(6,hit_target[hit_positions[failed]]+1)
        extra_wounds=rng.integers(1,7,failed.size)>=targets[failed]
        wounded[failed]=extra_hits&extra_wounds
    if has(effect, "poison.manbane") and not poison_blocked:
        wounded &= wound_rolls != 1
    if effect.reroll_wounds and (~wounded).any():
        failed = np.flatnonzero(~wounded)
        rerolls = rng.integers(1, 7, failed.size)
        wounded[failed] = rerolls >= targets[failed]
        wound_rolls[failed] = rerolls
    if has(attacker.global_effects,"mechanic.mark-of-the-old-ones"):
        available=(~wounded)&(~attacker_state.mark_of_old_ones_used[hit_rows])
        chosen=np.flatnonzero(available)
        if chosen.size:
            wounded[chosen]=True
            wound_rolls[chosen]=targets[chosen]
            attacker_state.mark_of_old_ones_used[hit_rows[chosen]]=True
    wound_rows = hit_rows[wounded]
    if observation is not None:
        observation.wounded = bool(wound_rows.size)
    if wound_rows.size == 0:
        return
    wound_positions = np.searchsorted(hit_rows, wound_rows)
    wound_strength = armour_strength_hits[wounded].copy()
    if has(effect,"skill.monster-slayer-effective-strength-armour"):
        boosted = raw_targets[wounded] > 4
        wound_strength[boosted] = np.maximum(wound_strength[boosted], toughness[wounded][boosted])
    critical_threshold = _critical_wound_threshold(effect, weapon, poison_blocked)
    if has(attacker.global_effects,"spiritual_weapons"):critical_threshold=5
    critical_candidates = (
        (~automatic_wound[wounded])
        & (critical_rolls[wounded] >= critical_threshold)
        & (targets[wounded] < 6)
    )
    if has(effect, "effect.no-critical"):
        critical_candidates[:] = False
    critical = _claim_criticals(
        critical_candidates,
        wound_rows,
        attacker_state,
    )
    if has(defender.global_effects,"skill.hardy-constitution") and critical.any():
        critical &= rng.integers(1,7,critical.size)<5
    magical_attack = has(effect,"attack.magical")
    hug_wounds = np.zeros(wound_rows.size,dtype=bool)
    save_target = armour_targets(
        defender, wound_strength, effect, magical_attack, hug_wounds,
    )
    saved = np.zeros(wound_rows.size, dtype=bool)
    eligible = save_target <= 6
    saved[eligible] = rng.integers(1, 7, int(eligible.sum())) >= np.maximum(2, save_target[eligible])
    if observation is not None and saved.any():
        observation.saved = True
        observation.critical = bool(critical[saved].any())
    wound_rows = wound_rows[~saved]
    critical = critical[~saved]
    if wound_rows.size == 0:
        return
    ward, regeneration = special_save_targets(defender, effect)
    if ward <= 6:
        protected = rng.integers(1, 7, wound_rows.size) >= ward
        if observation is not None and protected.any():
            observation.saved = True
        wound_rows = wound_rows[~protected]
        critical = critical[~protected]
    if regeneration<=6 and wound_rows.size:
        regenerated=rng.integers(1,7,wound_rows.size)>=regeneration
        if observation is not None and regenerated.any():
            observation.saved = True
        wound_rows=wound_rows[~regenerated];critical=critical[~regenerated]
    if wound_rows.size == 0:
        return
    if defender.injury_profile==2:
        if observation is not None:
            observation.damage = 1
            observation.critical = bool(critical.any())
        defender_state.condition[wound_rows]=OUT
        return
    condition_for_helpless = (
        defender_phase_condition[wound_rows]
        if defender_phase_condition is not None
        else defender_state.condition[wound_rows]
    )
    helpless_wounds = np.isin(condition_for_helpless, (KNOCKED_DOWN, PARALYZED))
    defender_state.condition[wound_rows[helpless_wounds]] = OUT
    damage = max(1, effect.damage)
    if has(defender.global_effects,"flammable") and has(effect,"attack.fire"):
        damage *= 2
    if observation is not None:
        observation.damage = damage
        observation.critical = bool(critical.any())
    affected_rows = np.unique(wound_rows)
    wounds_before = defender_state.wounds[affected_rows].copy()
    damage_rows = np.repeat(wound_rows, damage)
    damage_critical = np.repeat(critical, damage)
    damage_helpless = np.repeat(helpless_wounds, damage)
    np.subtract.at(defender_state.wounds, damage_rows, 1)
    if has(defender.global_effects, "acid_blood"):
        reactive = EffectSet(
            tags=("rule.acid-blood", "effect.no-critical"),
            fixed_strength=3,
            automatic_hit=True,
            cannot_be_parried=True,
        )
        counts = np.bincount(damage_rows, minlength=defender_state.wounds.size)
        for index in range(int(counts.max(initial=0))):
            reactive_rows = np.flatnonzero(counts > index)
            _resolve_weapon(
                defender, attacker, reactive, reactive_rows,
                np.zeros(attacker_state.wounds.size, dtype=bool),
                defender_state, attacker_state, rng, False,
            )
    if has(effect, "poison.nightshade") and not poison_blocked:
        np.add.at(defender_state.initiative_penalty, wound_rows, 1)
    if has(effect, "poison.spider-spittle") and not poison_blocked:
        failed_tests = ~_characteristic_test(defender, defender_state.toughness[wound_rows], rng)
        paralyzed = wound_rows[failed_tests & (defender_state.condition[wound_rows] == STANDING)]
        defender_state.condition[paralyzed] = PARALYZED
    # Damage rows are ordered by duel row. The ordinal within each row tells
    # us which damage instance reaches zero wounds and therefore creates an
    # injury roll, without grouping each simulated duel in Python.
    row_starts = np.flatnonzero(np.r_[True, damage_rows[1:] != damage_rows[:-1]])
    row_lengths = np.diff(np.r_[row_starts, damage_rows.size])
    damage_ordinals = np.arange(damage_rows.size) - np.repeat(row_starts, row_lengths) + 1
    wounds_per_damage = np.repeat(wounds_before, row_lengths)
    injury_mask = (~damage_helpless) & (
        (wounds_per_damage <= 0) | (damage_ordinals >= wounds_per_damage)
    )
    injury_rows = damage_rows[injury_mask]
    if injury_rows.size == 0:
        return
    if defender.injury_profile == 4:
        defender_state.condition[np.unique(injury_rows)] = OUT
        return
    injury_criticals = damage_critical[injury_mask]
    injury_rolls = rng.integers(1, 7, injury_rows.size) + effect.injury_modifier + int(knife_fighting)
    critical_bonus=2+int(has(effect,"skill.web-of-steel"))+effect.critical_injury_bonus
    injury_rolls += injury_criticals.astype(np.int16) * critical_bonus
    threshold = defender.global_effects.out_of_action_threshold
    if has(defender.global_effects,"injury_reroll_out") and not has(effect,"attack.fire"):
        out_threshold = 6 if has(defender.global_effects,"skill.hard-to-kill") or has(defender.global_effects,"skill.tough-as-steel") else threshold
        reroll = injury_rolls >= out_threshold
        injury_rolls[reroll] = rng.integers(1, 7, int(reroll.sum()))
    injury_context=InjuryContext(
        out_threshold=threshold,
        injury_profile=defender.injury_profile,
        hard_to_kill=has(defender.global_effects,"skill.hard-to-kill") or has(defender.global_effects,"skill.tough-as-steel"),
        concussion=effect.concussion,
        concussion_immune=has(defender.global_effects,"concussion_immune"),
        fragile=has(defender.global_effects,"fragile_halflings"),
        poisonous=has(effect, "poisonous_injury") and not poison_blocked,
        survivor=has(defender.global_effects,"survivor"),
        head_crusher=has(effect,"skill.head-crusher"),
        ignore_pain=has(defender.global_effects,"skill.ignore-pain"),
        jump_up=has(defender.global_effects,"skill.jump-up"),
        mandrake=has(defender.global_effects,"preparation.mandrake-root"),
    )
    lowest = int(injury_rolls.min(initial=0))
    highest_roll = int(injury_rolls.max(initial=0))
    injury_table = injury_conditions(
        np.arange(lowest, highest_roll + 1, dtype=np.int16), injury_context,
    )
    injury = injury_table[injury_rolls - lowest]
    if defender.global_effects.thick_skull:
        stunned = injury == STUNNED
        threshold_roll = 2 if defender.helmet_save <= 4 else 3
        recovery = rng.integers(1, 7, injury_rows.size) >= threshold_roll
        injury[stunned & recovery] = KNOCKED_DOWN
    if defender.helmet_save <= 6 and not defender.global_effects.thick_skull:
        stunned = injury == STUNNED
        recovery = rng.integers(1, 7, injury_rows.size) >= defender.helmet_save
        injury[stunned & recovery] = KNOCKED_DOWN
    injured = np.unique(injury_rows)
    highest_by_row = np.full(defender_state.condition.size, STANDING, dtype=np.int8)
    np.maximum.at(highest_by_row, injury_rows, injury)
    highest = highest_by_row[injured]
    defender_state.condition[injured] = np.maximum(defender_state.condition[injured], highest)
    defender_state.frenzy[injured] &= highest == STANDING
    contagious_rows=injured[(highest==OUT)]
    if (contagious_rows.size and has(defender.global_effects,"contagious")
            and not has(attacker.global_effects,"undead_or_possessed")):
        passed = _characteristic_test(attacker, attacker_state.toughness[contagious_rows], rng,
                                      six_always_fails=True)
        infected=contagious_rows[~passed]
        attacker_state.wounds[infected]-=1
        defeated=infected[attacker_state.wounds[infected]<=0]
        if defeated.size:
            attacker_state.condition[defeated]=OUT


def resolve_attacks(attacker: CompiledFighter, defender: CompiledFighter, rows: np.ndarray,
                    attacks: np.ndarray, charging: np.ndarray, attacker_state: CombatState,
                    defender_state: CombatState, rng: np.random.Generator, first_round: bool,
                    decisions: DecisionPolicy | None = None,
                    observations: list[VectorAttackObservation] | None = None,
                    decision_prefix: str = "") -> None:
    if rows.size == 0:
        return
    defender_phase_condition = defender_state.condition.copy()
    bull_rows=rows[first_round & charging[rows] & has(attacker.global_effects,"mechanic.bull-charge")]
    if bull_rows.size and decisions is not None and not decisions.choose(
        f"{decision_prefix + '.' if decision_prefix else ''}bull-charge", attacker
    ):
        bull_rows=np.empty(0,dtype=np.int64)
    if bull_rows.size:
        bull=EffectSet(tags=("mechanic.bull-charge",),hit_modifier=1)
        prepared=_prepare_weapon_attack(attacker,defender,bull,bull_rows,charging,attacker_state,defender_state,rng,first_round)
        if prepared is not None:
            observation = VectorAttackObservation(
                hit=bool(prepared.hit_rows.size), hit_roll=int(prepared.rolls[0]),
                hit_target=int(prepared.hit_target[0]),
            ) if observations is not None else None
            parries_before=defender_state.parry_remaining.copy()
            hit_rows=prepared.hit_rows[defender_state.condition[prepared.hit_rows]!=OUT]
            hit_values=prepared.rolls[np.searchsorted(prepared.active,hit_rows)]
            hit_strength=prepared.strength[np.searchsorted(prepared.active,hit_rows)]
            hit_rows,_=_parry_hits(defender,prepared.effect,hit_rows,hit_values,hit_strength,defender_state,rng)
            if observation is not None and prepared.hit_rows.size and hit_rows.size == 0:
                row=int(prepared.hit_rows[0])
                observation.parried=defender_state.parry_remaining[row] < parries_before[row]
            if hit_rows.size:
                charm=defender_state.lucky_charm[hit_rows]
                if charm.any():
                    rolls=rng.integers(1,7,hit_rows.size)
                    defender_state.lucky_charm[hit_rows[charm]]=False
                    hit_rows=hit_rows[~(charm&(rolls>=4))]
                standing=hit_rows[defender_state.condition[hit_rows]==STANDING]
                defender_state.condition[standing]=KNOCKED_DOWN
            if observations is not None and observation is not None:
                observations.append(observation)
        rows=rows[~np.isin(rows,bull_rows)]
        if rows.size==0:return
    maximum = int(attacks[rows].max(initial=0))
    prepared_attacks: list[PreparedAttack] = []
    body_rows=rows[first_round & charging[rows] & has(attacker.global_effects,"mechanic.body-slam")]
    if body_rows.size and decisions is not None and not decisions.choose(
        f"{decision_prefix + '.' if decision_prefix else ''}body-slam", attacker
    ):
        body_rows=np.empty(0,dtype=np.int64)
    if body_rows.size:
        body=EffectSet(tags=("mechanic.body-slam",),strength_bonus=1,hit_modifier=1)
        prepared=_prepare_weapon_attack(attacker,defender,body,body_rows,charging,attacker_state,defender_state,rng,first_round)
        if prepared is not None:prepared_attacks.append(prepared)
        rows=rows[~np.isin(rows,body_rows)]
    for index in range(maximum):
        active = rows[(attacks[rows] > index) & (defender_state.condition[rows] != OUT)]
        if active.size == 0:
            continue
        offhand = attacker.off_hand_attacks and attacker.off_hand is not None
        main_pistol = has(attacker.main_weapon,"weapon.pistol") or has(attacker.main_weapon,"weapon.duelling-pistol")
        off_pistol = bool(attacker.off_hand and (
            has(attacker.off_hand,"weapon.pistol") or has(attacker.off_hand,"weapon.duelling-pistol")
        ))
        if main_pistol:
            use_off = np.full(active.size, bool(offhand and (not first_round or index > 0)))
        else:
            use_off = offhand & (index == attacks[active] - 1)
            if off_pistol and not first_round:
                use_off = np.zeros(active.size, dtype=bool)
        main_weapon=(
            attacker.main_weapon_without_poison
            if (defender.global_effects.poison_immunity
                or has(defender.global_effects, "poison_immune"))
            and attacker.main_weapon_without_poison is not None
            else attacker.main_weapon
        )
        if index==0 and has(attacker.global_effects,"mechanic.unpredictable-attack"):
            main_weapon=merge_effects(main_weapon,EffectSet(cannot_be_parried=True,tags=("mechanic.unpredictable-attack",)))
        main = _prepare_weapon_attack(attacker,defender,main_weapon,active[~use_off],charging,attacker_state,defender_state,rng,first_round)
        if main is not None:
            prepared_attacks.append(main)
        if offhand:
            off = _prepare_weapon_attack(attacker,defender,attacker.off_hand,active[use_off],charging,attacker_state,defender_state,rng,first_round)
            if off is not None:
                prepared_attacks.append(off)
    for weapon in attacker.extra_attacks:
        if has(weapon, "rule.horned-one") and not charging[rows].any():
            continue
        extra = _prepare_weapon_attack(attacker, defender, weapon, rows, charging, attacker_state, defender_state, rng, first_round)
        if extra is not None: prepared_attacks.append(extra)
    best_roll = np.full(charging.size,-1,dtype=np.int8)
    second_roll = np.full(charging.size,-1,dtype=np.int8)
    selected = [np.zeros(0,dtype=np.int64) for _ in prepared_attacks]
    owner = np.full(charging.size,-1,dtype=np.int32)
    second_owner = np.full(charging.size,-1,dtype=np.int32)
    two_parries = _parry_capacity(defender) == 2
    for attack_index,prepared in enumerate(prepared_attacks):
        positions=np.searchsorted(prepared.active,prepared.hit_rows)
        values=prepared.rolls[positions]
        better=values>best_roll[prepared.hit_rows]
        if two_parries:
            replaced_rows=prepared.hit_rows[better]
            second_roll[replaced_rows]=best_roll[replaced_rows]
            second_owner[replaced_rows]=owner[replaced_rows]
            between=(~better) & (values>second_roll[prepared.hit_rows])
            second_rows=prepared.hit_rows[between]
            second_roll[second_rows]=values[between]
            second_owner[second_rows]=attack_index
        chosen=prepared.hit_rows[better]
        best_roll[chosen]=values[better]
        owner[chosen]=attack_index
    for attack_index in range(len(prepared_attacks)):
        selected[attack_index]=np.flatnonzero((owner==attack_index) | (second_owner==attack_index))
    defences_resolved=False
    replaced_attack_indices: set[int] = set()
    if attacker.global_effects.bear_hug and prepared_attacks:
        # Bear Hug depends on two surviving hits across separate attacks.  Move
        # the hit/parry boundary ahead of wound resolution, aggregate those
        # hits, then replace exactly one pair with the opposed Strength test.
        defended=[]
        for prepared,parry_rows in zip(prepared_attacks,selected):
            surviving=_apply_hit_defences(
                attacker,defender,prepared,attacker_state,defender_state,rng,charging,parry_rows
            )
            defended.append(replace(prepared,hit_rows=surviving))
        prepared_attacks=defended
        occurrences: dict[int,list[tuple[int,int]]]={}
        for attack_index,prepared in enumerate(prepared_attacks):
            for position,row in enumerate(prepared.hit_rows):
                occurrences.setdefault(int(row),[]).append((attack_index,position))
        policy=decisions or AlwaysAccept()
        hug_rows=[]
        remove=[np.zeros(prepared.hit_rows.size,dtype=bool) for prepared in prepared_attacks]
        for row,positions in occurrences.items():
            key=f"{decision_prefix + '.' if decision_prefix else ''}bear-hug"
            if len(positions)<2 or not policy.choose(key,{"row":row}):
                continue
            for attack_index,position in positions[:2]:
                remove[attack_index][position]=True
                replaced_attack_indices.add(attack_index)
            hug_rows.append(row)
        prepared_attacks=[
            replace(prepared,hit_rows=prepared.hit_rows[~removed])
            for prepared,removed in zip(prepared_attacks,remove)
        ]
        if hug_rows:
            hug_rows_array=np.asarray(hug_rows,dtype=np.int64)
            attacker_rolls=rng.integers(1,7,hug_rows_array.size)
            defender_rolls=rng.integers(1,7,hug_rows_array.size)
            won=np.fromiter((
                bear_hug_wins(
                    int(attacker_roll),int(attacker_state.strength[row]),
                    int(defender_roll),int(defender_state.strength[row]),
                )
                for row,attacker_roll,defender_roll in zip(
                    hug_rows_array,attacker_rolls,defender_rolls
                )
            ),dtype=bool,count=hug_rows_array.size)
            won_rows=hug_rows_array[won]
            if won_rows.size:
                hug=EffectSet(
                    tags=("effect.automatic-wound","effect.no-critical"),
                    automatic_hit=True,cannot_be_parried=True,ignore_armour=True,
                )
                prepared_hug=_prepare_weapon_attack(
                    attacker,defender,hug,won_rows,charging,
                    attacker_state,defender_state,rng,first_round,
                )
                if prepared_hug is not None:
                    hug_observation = VectorAttackObservation() if observations is not None else None
                    _resolve_weapon(
                        attacker,defender,hug,won_rows,charging,
                        attacker_state,defender_state,rng,first_round,
                        prepared=prepared_hug,
                        defender_phase_condition=defender_phase_condition,
                        defences_resolved=True,
                        observation=hug_observation,
                    )
                    if observations is not None and hug_observation is not None:
                        observations.append(hug_observation)
        defences_resolved=True
    for attack_index,(prepared,parry_rows) in enumerate(zip(prepared_attacks,selected)):
        observation = VectorAttackObservation() if observations is not None else None
        _resolve_weapon(attacker,defender,prepared.weapon,prepared.active,charging,
                        attacker_state,defender_state,rng,first_round,
                        prepared=prepared,parry_rows=parry_rows,
                        defender_phase_condition=defender_phase_condition,
                        decisions=decisions,
                        defences_resolved=defences_resolved,
                        observation=observation)
        if (observations is not None and observation is not None
                and attack_index not in replaced_attack_indices):
            observations.append(observation)


def _new_state(fighter: CompiledFighter, count: int, rng: np.random.Generator) -> CombatState:
    wounds = fighter.characteristics.wounds + int(has(fighter.global_effects, "skill.monstrous"))
    crimson = rng.integers(1,4,count,dtype=np.int8) if has(fighter.global_effects,"preparation.crimson-shade") else np.zeros(count,dtype=np.int8)
    characteristic_values={
        "WS":np.full(count,fighter.characteristics.weapon_skill,dtype=np.int16),
        "S":np.full(count,fighter.characteristics.strength,dtype=np.int16),
        "T":np.full(count,fighter.characteristics.toughness+fighter.global_effects.toughness_bonus,dtype=np.int16),
        "I":np.full(count,fighter.characteristics.initiative,dtype=np.int16),
        "A":np.full(count,fighter.characteristics.attacks,dtype=np.int16),
    }
    for key,dice,sides,bonus in fighter.random_characteristics:
        rolls=np.zeros(count,dtype=np.int16)
        for _ in range(dice):rolls+=rng.integers(1,sides+1,count,dtype=np.int16)
        characteristic_values[key]=rolls+bonus
    state=CombatState(np.full(count, wounds, dtype=np.int16), np.zeros(count, dtype=np.int8),
                       np.zeros(count, dtype=np.int8), np.ones(count, dtype=np.int8),
                       np.full(count, fighter.global_effects.frenzy),
                       np.full(count, has(fighter.global_effects, "defence.lucky-charm")),crimson,
                       np.zeros(count,dtype=np.int8),np.zeros(count,dtype=bool),
                       np.zeros(count,dtype=bool),np.full(count,_parry_capacity(fighter),dtype=np.int8),np.zeros(count,dtype=bool),
                       np.zeros(count,dtype=bool),np.zeros(count,dtype=bool),np.zeros(count,dtype=np.int8),
                       np.zeros(count,dtype=np.int8),np.zeros(count,dtype=bool),np.zeros(count,dtype=bool),np.zeros(count,dtype=bool),
                       characteristic_values["WS"],characteristic_values["S"],
                       characteristic_values["T"],characteristic_values["I"],
                       characteristic_values["A"])
    if has(fighter.global_effects,"mechanic.disability"):
        state.disability[:]=rng.integers(1,7,count,dtype=np.int8)
        state.initiative[state.disability==1]=np.maximum(1,state.initiative[state.disability==1]-1)
        state.weapon_skill[state.disability==2]=np.maximum(1,state.weapon_skill[state.disability==2]-1)
        state.toughness[state.disability==4]=np.maximum(1,state.toughness[state.disability==4]-1)
        state.strength[state.disability==5]=np.maximum(1,state.strength[state.disability==5]-1)
    return state


def _resolve_spines(first: CompiledFighter, second: CompiledFighter,
                    rows: np.ndarray, charge1: np.ndarray, charge2: np.ndarray,
                    state1: CombatState, state2: CombatState,
                    rng: np.random.Generator) -> None:
    """Resolve simultaneous, non-critical Spines hits at phase start."""
    spines=EffectSet(
        tags=("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True)
    prepared1=(
        _prepare_weapon_attack(first,second,spines,rows,charge1,state1,state2,rng,False)
        if has(first.global_effects,"spines") else None)
    prepared2=(
        _prepare_weapon_attack(second,first,spines,rows,charge2,state2,state1,rng,False)
        if has(second.global_effects,"spines") else None)
    if prepared1 is not None:
        _resolve_weapon(first,second,spines,rows,charge1,state1,state2,rng,False,prepared=prepared1)
    if prepared2 is not None:
        _resolve_weapon(second,first,spines,rows,charge2,state2,state1,rng,False,prepared=prepared2)


def _rescue_force_of_will(fighter: CompiledFighter, state: CombatState,
                          rows: np.ndarray, rng: np.random.Generator) -> None:
    if not has(fighter.global_effects,"mechanic.force-of-will") or rows.size==0:return
    eligible=rows[(state.condition[rows]==OUT)&~state.force_of_will_used[rows]]
    if eligible.size==0:return
    state.force_of_will_used[eligible]=True
    success=_characteristic_test(fighter,state.toughness[eligible],rng)
    rescued=eligible[success]
    state.condition[rescued]=STANDING
    state.wounds[rescued]=1
    state.force_of_will_active[rescued]=True


def _sustain_force_of_will(fighter: CompiledFighter, state: CombatState,
                           rng: np.random.Generator,
                           rows: np.ndarray | None = None) -> None:
    if not has(fighter.global_effects,"mechanic.force-of-will"):return
    eligible = state.force_of_will_active & (state.condition != OUT)
    if rows is not None:
        selected = np.zeros(state.wounds.size, dtype=bool)
        selected[rows] = True
        eligible &= selected
    active=np.flatnonzero(eligible)
    if active.size==0:return
    state.force_of_will_penalty[active]+=1
    target=np.maximum(0,state.toughness[active]-state.force_of_will_penalty[active])
    failed=rng.integers(1,7,active.size)>target
    removed=active[failed]
    state.condition[removed]=OUT
    state.force_of_will_active[removed]=False


def _black_hunger_backlash(fighter: CompiledFighter, state: CombatState,
                           rows: np.ndarray, rng: np.random.Generator) -> None:
    if not has(fighter.global_effects,"mechanic.black-hunger") or rows.size==0:return
    active=rows[state.condition[rows]!=OUT]
    if active.size==0:return
    hits=rng.integers(1,4,active.size)
    backlash=EffectSet(tags=("mechanic.black-hunger-backlash","effect.no-critical"),fixed_strength=3,
                       automatic_hit=True,cannot_be_parried=True,ignore_armour=True)
    for index in range(3):
        hit_rows=active[hits>index]
        _resolve_weapon(fighter,fighter,backlash,hit_rows,np.zeros(state.wounds.size,dtype=bool),state,state,rng,False)
        _rescue_force_of_will(fighter,state,hit_rows,rng)


def _resolve_fire(victim: CompiledFighter, opponent: CompiledFighter,
                   victim_state: CombatState, opponent_state: CombatState,
                   rng: np.random.Generator,
                   rows: np.ndarray | None = None) -> None:
    """Resolve the Recovery-phase test and S4 hit for warriors on fire."""
    burning=np.flatnonzero(victim_state.on_fire&(victim_state.condition!=OUT))
    if rows is not None:
        burning = np.intersect1d(burning, rows, assume_unique=True)
    if burning.size==0:return
    extinguished=rng.integers(1,7,burning.size)>=4
    victim_state.on_fire[burning[extinguished]]=False
    still_burning=burning[~extinguished]
    if still_burning.size==0:return
    fire=EffectSet(tags=("attack.fire","effect.no-critical"),fixed_strength=4,
                   automatic_hit=True,cannot_be_parried=True)
    source=replace(opponent,main_weapon=fire,off_hand=None,global_effects=EffectSet(),extra_attacks=())
    _resolve_weapon(source,victim,fire,still_burning,np.zeros(victim_state.wounds.size,dtype=bool),
                    opponent_state,victim_state,rng,False)


def _resolve_netter_charge(netter: CompiledFighter, target: CompiledFighter,
                           rows: np.ndarray, netter_state: CombatState,
                           target_state: CombatState,
                           rng: np.random.Generator) -> np.ndarray:
    """Resolve Netter's first-round charge reaction and return caught rows."""
    if rows.size == 0 or not has(netter.global_effects,"mechanic.netter"):
        return np.empty(0,dtype=np.int64)
    hits=rng.integers(1,7,rows.size)>=max(2,7-netter.ballistic_skill)
    escape=_characteristic_test(target,target_state.strength[rows],rng)
    caught=rows[hits&~escape]
    target_state.condition[caught]=KNOCKED_DOWN
    return caught


def _resource_observation(state: CombatState) -> tuple[tuple[str, np.ndarray], ...]:
    return (
        ("lucky-charm", ~state.lucky_charm.copy()),
        ("force-of-will", state.force_of_will_used.copy()),
        ("mark-of-the-old-ones", state.mark_of_old_ones_used.copy()),
        ("luck", state.luck_used.copy()),
    )


def _simulate_batch_core(first: CompiledFighter, second: CompiledFighter, count: int,
                         rng: np.random.Generator, maximum_rounds: int,
                         decisions: DecisionPolicy | None = None,
                         *, observe: bool = False
                         ) -> tuple[int, int, int] | VectorBatchObservation:
    state1, state2 = _new_state(first,count,rng), _new_state(second,count,rng)
    first_charges = rng.random(count) < .5
    rounds = np.zeros(count, dtype=np.int16) if observe else None
    optional = _optional_phase_plan(first, second)
    entangle_effect = (
        EffectSet(tags=("effect.chained-squig-entangle",),fixed_strength=3,automatic_hit=True)
        if optional.first_entangle or optional.second_entangle else None
    )
    for round_index in range(maximum_rounds):
        unresolved = (state1.condition != OUT) & (state2.condition != OUT)
        if not unresolved.any():
            break
        if round_index:
            active_rows = np.flatnonzero(unresolved)
            if optional.first_force_of_will:
                _sustain_force_of_will(first,state1,rng,active_rows)
            if optional.second_force_of_will:
                _sustain_force_of_will(second,state2,rng,active_rows)
            if optional.first_can_burn:
                _resolve_fire(first,second,state1,state2,rng,active_rows)
            if optional.second_can_burn:
                _resolve_fire(second,first,state2,state1,rng,active_rows)
            if optional.first_force_of_will:
                _rescue_force_of_will(first, state1, active_rows, rng)
            if optional.second_force_of_will:
                _rescue_force_of_will(second, state2, active_rows, rng)
        unresolved = (state1.condition != OUT) & (state2.condition != OUT)
        if not unresolved.any():
            break
        active_rows = np.flatnonzero(unresolved)
        if rounds is not None:
            rounds[unresolved] += 1
        state1.parry_used[:] = False; state2.parry_used[:] = False
        state1.parry_remaining[:] = _parry_capacity(first)
        state2.parry_remaining[:] = _parry_capacity(second)
        state1.critical_used[:] = False; state2.critical_used[:] = False
        if has(first.global_effects,"mechanic.spawn-special-attacks"):
            state1.attacks[:]=rng.integers(1,7,count,dtype=np.int16)+1
        if has(second.global_effects,"mechanic.spawn-special-attacks"):
            state2.attacks[:]=rng.integers(1,7,count,dtype=np.int16)+1
        stunned1, stunned2 = state1.condition == STUNNED, state2.condition == STUNNED
        stood1, stood2 = state1.condition == KNOCKED_DOWN, state2.condition == KNOCKED_DOWN
        state1.condition[stunned1] = KNOCKED_DOWN; state2.condition[stunned2] = KNOCKED_DOWN
        state1.condition[stood1 & ~stunned1] = STANDING; state2.condition[stood2 & ~stunned2] = STANDING
        paralyzed1, paralyzed2 = state1.condition == PARALYZED, state2.condition == PARALYZED
        paralyzed_rows1=np.flatnonzero(paralyzed1)
        paralyzed_rows2=np.flatnonzero(paralyzed2)
        if paralyzed_rows1.size:
            recover1=_characteristic_test(first,state1.toughness[paralyzed_rows1],rng)
            state1.condition[paralyzed_rows1[recover1]] = STANDING
        if paralyzed_rows2.size:
            recover2=_characteristic_test(second,state2.toughness[paralyzed_rows2],rng)
            state2.condition[paralyzed_rows2[recover2]] = STANDING
        first_round = round_index == 0
        charge1 = first_charges if first_round else np.zeros(count,dtype=bool)
        charge2 = ~first_charges if first_round else np.zeros(count,dtype=bool)
        if first_round:
            if optional.first_netter:
                rows=np.flatnonzero(unresolved&charge1)
                _resolve_netter_charge(first,second,rows,state1,state2,rng)
            if optional.second_netter:
                rows=np.flatnonzero(unresolved&charge2)
                _resolve_netter_charge(second,first,rows,state2,state1,rng)
        if optional.first_spines or optional.second_spines:
            _resolve_spines(first,second,active_rows,charge1,charge2,state1,state2,rng)
        if optional.first_force_of_will:
            _rescue_force_of_will(first,state1,active_rows,rng)
        if optional.second_force_of_will:
            _rescue_force_of_will(second,state2,active_rows,rng)
        if optional.second_entangle:
            entangled1=np.flatnonzero(state1.entangled&(state2.condition==STANDING)&unresolved)
            _resolve_weapon(second,first,entangle_effect,entangled1,charge2,state2,state1,rng,False)
        if optional.first_entangle:
            entangled2=np.flatnonzero(state2.entangled&(state1.condition==STANDING)&unresolved)
            _resolve_weapon(first,second,entangle_effect,entangled2,charge1,state1,state2,rng,False)
        charged1, charged2 = charge2, charge1
        attacks1=attack_count(first,charge1,first_round,state1.frenzy,charged1,state1.attack_penalty,state1.wounds<first.characteristics.wounds,state1.attacks)
        attacks2=attack_count(second,charge2,first_round,state2.frenzy,charged2,state2.attack_penalty,state2.wounds<second.characteristics.wounds,state2.attacks)
        attacks1=np.where(attacks1>0,np.maximum(1,attacks1+second.global_effects.incoming_attacks_modifier),0)
        attacks2=np.where(attacks2>0,np.maximum(1,attacks2+first.global_effects.incoming_attacks_modifier),0)
        attacks1[state1.on_fire]=0;attacks2[state2.on_fire]=0
        if has(first.global_effects,"animal_friendship") and has(second.global_effects,"species.animal"):
            attacks2[:]=0
        if has(second.global_effects,"animal_friendship") and has(first.global_effects,"species.animal"):
            attacks1[:]=0
        state1.attack_penalty[:]=0;state2.attack_penalty[:]=0
        if first_round and has(first.main_weapon,"weapon.serpent-whip"):attacks1+=charge1|charged1
        if first_round and has(second.main_weapon,"weapon.serpent-whip"):attacks2+=charge2|charged2
        if first_round and has(first.main_weapon,"weapon.boar-spear"):attacks2[charge2]=np.maximum(1,attacks2[charge2]-1)
        if first_round and has(second.main_weapon,"weapon.boar-spear"):attacks1[charge1]=np.maximum(1,attacks1[charge1]-1)
        if first_round and has(first.global_effects,"skill.sigmar-s-sign") and has(second.global_effects,"undead_or_possessed"):
            attacks2=np.where(attacks2>0,np.maximum(1,attacks2-1),0)
        if first_round and has(second.global_effects,"skill.sigmar-s-sign") and has(first.global_effects,"undead_or_possessed"):
            attacks1=np.where(attacks1>0,np.maximum(1,attacks1-1),0)
        p1,p2=priority(first,second,first_round,charge1,charged1,stood1),priority(second,first,first_round,charge2,charged2,stood2)
        i1,i2=effective_initiative(first,state1),effective_initiative(second,state2)
        first_acts=(p1>p2)|((p1==p2)&(i1>i2));ties=(p1==p2)&(i1==i2)
        first_acts[ties]=rng.random(int(ties.sum()))<.5
        rows=np.flatnonzero(unresolved&(state1.condition==STANDING)&first_acts)
        resolve_attacks(first,second,rows,attacks1,charge1,state1,state2,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows,rng)
        reply=rows[state2.condition[rows]==STANDING]
        resolve_attacks(second,first,reply,attacks2,charge2,state2,state1,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,reply,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,reply,rng)
        rows=np.flatnonzero(unresolved&(state2.condition==STANDING)&~first_acts)
        resolve_attacks(second,first,rows,attacks2,charge2,state2,state1,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows,rng)
        reply=rows[state1.condition[rows]==STANDING]
        resolve_attacks(first,second,reply,attacks1,charge1,state1,state2,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,reply,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,reply,rng)
        if optional.first_black_hunger:
            _black_hunger_backlash(first,state1,active_rows,rng)
        if optional.second_black_hunger:
            _black_hunger_backlash(second,state2,active_rows,rng)
    a=int(np.count_nonzero((state2.condition==OUT)&(state1.condition!=OUT)))
    b=int(np.count_nonzero((state1.condition==OUT)&(state2.condition!=OUT)))
    if observe:
        winner = np.zeros(count, dtype=np.int8)
        winner[(state2.condition == OUT) & (state1.condition != OUT)] = 1
        winner[(state1.condition == OUT) & (state2.condition != OUT)] = -1
        return VectorBatchObservation(
            winner=winner,
            rounds=rounds if rounds is not None else np.zeros(count, dtype=np.int16),
            first_wounds=state1.wounds.copy(),
            second_wounds=state2.wounds.copy(),
            first_condition=state1.condition.copy(),
            second_condition=state2.condition.copy(),
            first_resources=_resource_observation(state1),
            second_resources=_resource_observation(state2),
        )
    return a,b,count-a-b


def simulate_batch(first: CompiledFighter, second: CompiledFighter, count: int,
                   rng: np.random.Generator, maximum_rounds: int,
                   decisions: DecisionPolicy | None = None) -> tuple[int, int, int]:
    result = _simulate_batch_core(first, second, count, rng, maximum_rounds, decisions)
    assert isinstance(result, tuple)
    return result


def simulate_batch_observed(first: CompiledFighter, second: CompiledFighter, count: int,
                            rng: np.random.Generator, maximum_rounds: int,
                            decisions: DecisionPolicy | None = None) -> VectorBatchObservation:
    result = _simulate_batch_core(
        first, second, count, rng, maximum_rounds, decisions, observe=True,
    )
    assert isinstance(result, VectorBatchObservation)
    return result


def available_backends() -> tuple[str, ...]:
    """Return executable production backends in selection order."""
    try:
        from mordheim_combat_lab import _combat_native
    except ImportError:
        return ("numpy",)
    return ("native", "numpy") if hasattr(_combat_native, "simulate_duel") else ("numpy",)


def _simulate_duel_numpy(request: DuelRequest) -> DuelResult:
    rng=np.random.default_rng(request.seed);a=b=u=0;remaining=request.simulations
    while remaining:
        if request.cancel_event is not None and request.cancel_event.is_set():
            raise SimulationCancelled("simulation cancelled")
        count=min(remaining,request.batch_size)
        x,y,z=simulate_batch(
            request.first,request.second,count,rng,request.maximum_rounds,
            request.decision_policy,
        )
        a+=x;b+=y;u+=z;remaining-=count
    return DuelResult(a,b,u,request.simulations)


def simulate_duel(request: DuelRequest, *, backend: str = "auto") -> DuelResult:
    """Run a duel through the selected backend without changing `DuelRequest`."""
    if backend not in {"auto", "numpy", "native"}:
        raise ValueError(f"unknown combat backend: {backend}")
    selected = available_backends()[0] if backend == "auto" else backend
    if selected == "numpy":
        return _simulate_duel_numpy(request)
    try:
        from mordheim_combat_lab import _combat_native
    except ImportError as error:
        raise RuntimeError("native combat backend is not available") from error
    if not hasattr(_combat_native, "simulate_duel"):
        raise RuntimeError("native combat backend is not available")
    from mordheim_combat_lab.combat.kernel import compile_duel_plan

    plan = compile_duel_plan(request.first, request.second)
    if not plan.optimization_eligible:
        return _simulate_duel_numpy(request)
    supports = getattr(_combat_native, "supports_plan", lambda _plan: False)
    if not supports(plan):
        if backend == "native":
            raise RuntimeError("native combat backend does not support this duel plan")
        return _simulate_duel_numpy(request)
    return _combat_native.simulate_duel(request, plan)
