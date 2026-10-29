"""Vectorized engine: stateless NumPy projections of the canonical
scalar phase operators."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from mordheim_combat import phases
from mordheim_combat.phases import InjuryContext, ignores_unarmed_penalties, to_hit_target, wound_target
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter, EffectSet
from mordheim_combat.vectorized._state import STAT_ATTRIBUTES, require_characteristics
from mordheim_combat.vectorized._types import (
    CombatState, KNOCKED_DOWN, OUT, PARALYZED, STANDING, STUNNED, _parry_capacity, has,
)

#: Ordering placeholder for a profile that prints no Initiative (the
#: Necrarch Banshee).  It sorts after every printed value, and two absent rows
#: compare equal so the caller's printed tie roll decides, exactly as
#: ``phases.priority_order`` treats ``None``.
ABSENT_INITIATIVE = -1_000_000

def to_hit(attacker_ws: int, defender_ws: int) -> int:
    return to_hit_target(attacker_ws, defender_ws)

def hit_targets(attacker_ws: np.ndarray, defender_ws: np.ndarray, *,
                guiding_dream: np.ndarray | None = None,
                modifier: np.ndarray | int | None = None,
                fixed_target: np.ndarray | int | None = None,
                needs_sixes: np.ndarray | None = None) -> np.ndarray:
    # The three cases are mutually exclusive, so the table collapses to one
    # arithmetic expression: 4 minus (attacker stronger) plus (defender much
    # stronger), with zero marking an automatic hit against defender WS 0.
    target = 4 + (defender_ws > 2 * attacker_ws) - (attacker_ws > defender_ws)
    target = target.astype(np.int16)
    if guiding_dream is not None:
        # +1 To Hit is one point less on the target roll.
        target = target - np.asarray(guiding_dream, dtype=np.int16)
    if modifier is not None:
        # A positive modifier improves the roll, so it lowers the target.
        target = target - np.asarray(modifier, dtype=np.int16)
    zero = defender_ws == 0
    # ``resolve_hit`` returns an automatic hit against WS 0 before any fixed
    # target, but a fear effect that needs sixes still demands a natural six.
    sixes = (np.zeros(np.shape(target), dtype=bool) if needs_sixes is None
             else np.broadcast_to(np.asarray(needs_sixes, dtype=bool), np.shape(target)))
    if fixed_target is not None:
        target = np.where(
            np.asarray(fixed_target) > 0, np.asarray(fixed_target, dtype=np.int16), target,
        )
    target = np.where(sixes, 6, target)
    target = np.where(zero & ~sixes, 0, target)
    return target.astype(np.int8)

def characteristic(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator, name: str,
) -> np.ndarray:
    """Read WS/S/T/I/A of ``rows``, drawing a variable value first.

    An Inconsistency profile has each still-variable characteristic rolled at
    the operation that needs it, once per round.  Passing the rows here is
    what keeps the dice on the affected simulations only.  A fixed profile
    costs one attribute read and no die.
    """
    if name not in STAT_ATTRIBUTES:
        raise ValueError(f"unknown combat characteristic: {name}")
    require_characteristics(fighter, state, rows, rng, {name})
    return getattr(state, STAT_ATTRIBUTES[name])[rows]

def guiding_dream_hit_modifier(
    attacker: CompiledFighter, defender: CompiledFighter, state: CombatState,
    rows: np.ndarray,
) -> np.ndarray:
    """The +1 To Hit a Guiding Dream result of 2-3 grants, per row.

    The nominated model is the attacker (``condition.guiding-dream-target``)
    and the dream only affects attacks against the opposing Hero, so a
    supplied non-Hero opponent is refused exactly as the modular context does.
    """
    if not has(attacker.global_effects, "condition.guiding-dream-target"):
        return np.zeros(rows.size, dtype=np.int16)
    if not has(defender.global_effects, "fighter-kind.hero"):
        raise ValueError("Guiding Dream requires the nominated opposing model to be a Hero")
    return np.isin(state.guiding_dream_result[rows], (2, 3)).astype(np.int16)

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
    if context.shock:
        result[(totals >= 1) & (totals <= 4)] = STUNNED
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
                                 six_fails: bool = True,
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
    state.hampered_main[:] = 0
    state.hampered_off[:] = 0
    return stood

def armour_targets(defender: CompiledFighter, strength: np.ndarray,
                   effect: EffectSet, magical_attack: bool,
                   ignore: np.ndarray | bool = False) -> np.ndarray:
    """Vector form of the canonical `armour_target` contract."""
    strength_penetration = np.maximum(0, strength - 3)
    modifier = (
        strength_penetration
        + effect.armour_penetration
        - effect.target_armour_bonus
    )
    armour = defender.armour_save + modifier
    natural = np.full(strength.size, defender.natural_armour_save, dtype=np.int16)
    if not defender.natural_armour_unmodified:
        # Mirror the canonical contract: the strength and target-bonus part is
        # capped at the armour's worst save, and penetration applies after that
        # cap.  Unmodified natural armour ignores both strength and penetration.
        natural = np.minimum(
            natural + strength_penetration - effect.target_armour_bonus,
            defender.natural_armour_worst_save,
        ) + effect.armour_penetration
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
        protected = ~(ignored & magical_attack)
        target[protected] = np.minimum(target[protected], defender.global_effects.armour_save_floor)
    return target

def effective_initiative(fighter: CompiledFighter, state: CombatState) -> np.ndarray:
    """Initiative used for the tie-break, with printed absence preserved.

    A profile that prints no Initiative never gains one from a bonus: it
    sorts after every printed value (``ABSENT_INITIATIVE``).  Two absent rows
    remain equal, which lets the caller's printed tie roll decide, and a
    printed value always beats the absence.
    """
    off_hand_bonus = fighter.off_hand.initiative_bonus if fighter.off_hand is not None else 0
    numeric = np.maximum(
        state.initiative_floor,
        state.initiative
        + fighter.global_effects.initiative_bonus
        + fighter.main_weapon.initiative_bonus
        + off_hand_bonus
        + state.crimson_initiative
        - state.initiative_penalty,
    ).astype(np.int32)
    return np.where(state.initiative_missing, ABSENT_INITIATIVE, numeric).astype(np.int32)

def _characteristic_test(fighter: CompiledFighter, target: np.ndarray,
                         rng: np.random.Generator, *, six_always_fails: bool = True) -> np.ndarray:
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
                 base_attacks: np.ndarray | None = None,
                 player_turn: bool = True) -> np.ndarray:
    effect = fighter.global_effects
    extra_weapon_attack = int(fighter.off_hand_attacks or fighter.main_weapon.paired)
    base = (
        fighter.characteristics.attacks + effect.attacks_bonus
        + fighter.main_weapon.attacks_bonus
        + (fighter.off_hand.attacks_bonus if fighter.off_hand is not None else 0)
    )
    result = (base_attacks.astype(np.int16,copy=True)+base-fighter.characteristics.attacks
              if base_attacks is not None else np.full(charging.size,base,dtype=np.int16))
    if has(effect, "mechanic.sabretusk-charge") and charging.any():
        # ``phases.build_attacks``: the printed clause replaces the Attacks
        # characteristic with 2 on the charge; it is not a generic +1, so the
        # substitution happens before every bonus is added on top.
        result[charging] = 2 + base - fighter.characteristics.attacks
    if wounded is not None and has(effect,"maddened_with_pain"):
        result += wounded.astype(np.int16)
    if effect.charge_attacks_bonus and charging.any():
        result += charging.astype(np.int16) * effect.charge_attacks_bonus
    if first_round and effect.first_round_charge_attacks_bonus and charging.any():
        result += charging.astype(np.int16) * effect.first_round_charge_attacks_bonus
    if has(fighter.main_weapon, "weapon.fist") and phases.unarmed_attack_cap_applies(effect):
        result[:] = 1
        extra_weapon_attack = 0
    # ``phases.build_attacks``: a natural-attack body is unarmed in the same
    # sense as the neutral fist, and the two skills count the same empty hands
    # once — hence the ``elif`` chain mirroring the oracle.
    if has(effect, "skill.unarmed-fighting") and (
        has(fighter.main_weapon, "weapon.fist")
        or has(fighter.main_weapon, "weapon.natural-attacks")
    ):
        result += 1
    elif has(effect,"skill.art-of-silent-death") and (has(fighter.main_weapon,"weapon.fist") or has(fighter.main_weapon,"weapon.fighting-claws")):
        result += 1
    if has(effect,"skill.inspiring-sermon"):
        result += np.asarray(player_turn, dtype=np.int16)
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
    if has(fighter.main_weapon, "weapon.fist") and phases.unarmed_attack_cap_applies(effect):
        # ``phases.build_attacks`` caps at 1; it never raises a zeroed pool.
        result = np.minimum(result, np.int16(1))
    if (has(fighter.main_weapon, "weapon.vomit-attack")
            or has(fighter.main_weapon, "effect.wraith-touch")):
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
            if off_pistol:
                result[:] = 2
            elif not fighter.off_hand_attacks:
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
    if has(fighter.main_weapon, "effect.serpent-staff-power"):
        result[:] = 1
    if attack_penalty is not None:result=np.maximum(0,result-attack_penalty)
    return result

def round_weapon_attack_count(attacker: CompiledFighter, defender: CompiledFighter,
                              count: np.ndarray, *, first_round: bool,
                              charging: np.ndarray, charged: np.ndarray) -> np.ndarray:
    """Port of ``modular.rounds.apply_round_weapon_attack_modifiers``."""
    result = np.asarray(count, dtype=np.int16).copy()
    if not first_round:
        return result
    live = result > 0
    whipcrack = any(
        weapon is not None and any(has(weapon, tag) for tag in phases.WHIPCRACK_WEAPON_TAGS)
        for weapon in (attacker.main_weapon, attacker.off_hand)
    )
    if whipcrack:
        result[live] += (np.asarray(charging | charged, dtype=bool)[live]).astype(np.int16)
    if has(defender.main_weapon, "weapon.boar-spear"):
        affected = np.asarray(charging, dtype=bool) & live
        result[affected] = np.maximum(1, result[affected] - 1)
    return result

def opposed_attack_count(attacker: CompiledFighter, defender: CompiledFighter,
                         count: np.ndarray, *, first_round: bool,
                         defer_grapple: bool = False) -> np.ndarray:
    """Port of ``modular.rounds.apply_opponent_attack_modifiers``."""
    result = np.asarray(count, dtype=np.int16).copy()
    if (any(has(defender.global_effects, tag) for tag in (
            "animal_friendship", "mechanic.animal-friendship"))
            and has(attacker.global_effects, "species.normal-animal")):
        result[:] = 0
        return result
    live = result > 0
    if (first_round and has(defender.global_effects, "skill.sigmar-s-sign")
            and has(attacker.global_effects, "undead_or_possessed")
            and not has(attacker.global_effects, "nature.daemon")):
        result[live] = np.maximum(1, result[live] - 1)
    modifier = defender.global_effects.incoming_attacks_modifier
    if defer_grapple and modifier < 0 and has(defender.global_effects, "rule.tentacle-grapple"):
        # Keep Tentacle's one optional loss for the allocated pool.
        modifier += 1
    if modifier:
        live = result > 0
        result[live] = np.maximum(1, result[live] + modifier)
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
    if fighter.global_effects.strongman and weapon_priority < 0 and (
        fighter.main_weapon.two_handed or has(fighter.main_weapon, "weapon.broadsword")
    ):
        weapon_priority = 0
    if has(fighter.main_weapon, "weapon.long-boat-hook") and not first_round:
        weapon_priority = 0
    # The spear's and the pike's printed Strike First only applies in the first
    # turn of hand-to-hand combat (mordheimer.net, close-combat weapons /
    # Strike First), mirroring the long-boat-hook's first-round scope.
    if (has(fighter.main_weapon, "weapon.spear")
            or has(fighter.main_weapon, "weapon.pike")) and not first_round:
        weapon_priority = 0
    value = np.full(charging.size, weapon_priority + fighter.global_effects.priority, dtype=np.int8)
    if has(fighter.global_effects,"mechanic.strike-first-vs-skinks-always") and has(opponent.global_effects,"species.skink"):
        value[:] = 20
    if has(fighter.main_weapon, "weapon.trident"):
        value[charged] = np.maximum(value[charged], 1)
    if first_round:
        if weapon_priority >= 0:
            value = np.maximum(value, charging.astype(np.int8))
        if has(fighter.global_effects,"mechanic.strike-first-vs-skinks-first-round") and has(opponent.global_effects,"species.skink"):
            value[:] = 20
        if has(fighter.global_effects, "skill.lightning-reflexes"):
            value[charged] = np.maximum(value[charged], 1)
    if not has(fighter.global_effects, "skill.always-strikes-first"):
        value[stood] = -1
    # ``phases.resolve_priority``: a profile that prints no Initiative fights
    # outside the Initiative order — it strikes last and the first-round charge
    # floor never raises it.  ``effective_initiative``'s ``ABSENT_INITIATIVE``
    # only orders rows *within* a tier; the oracle also demotes the tier itself.
    if fighter.characteristics.initiative is None:
        value[:] = -1
    if has(fighter.global_effects, "dance.woven-mist-active"):
        value = np.maximum(value, np.int8(1))
    if has(fighter.global_effects, "mechanic.frantic"):
        # ``phases.priority_order``: Frantic's explicit top priority is applied
        # last, so it ignores weapon penalties, ordinary Initiative and the
        # stand-up demotion alike.  30 is well inside int8, and the driver
        # widens to int32 before scaling the tier, so no overflow remains.
        value[:] = 30
    return value


# ---------------------------------------------------------------------------
# Context projections (G03)
#
# The modular ``prepare_*_context`` helpers are the single rule source: these
# functions reproduce their arithmetic over one row per simulation.  They are
# stateless, so a caller passes the rows whose operation needs the projection;
# rows outside it are untouched and no die is drawn here.  Row-dependent facts
# (condition, Guiding Dream result, frenzy, spent resources) stay arrays; the
# fighter-level qualifiers are resolved once and broadcast.
# ---------------------------------------------------------------------------


def combined_effect(attacker: CompiledFighter, weapon: EffectSet) -> EffectSet:
    """Port of ``modular.contexts._combined_effect``.

    The three whole-body attacks carry their own profile and are not merged
    with the fighter's global effects; every other attack is.
    """
    if any(has(weapon, tag) for tag in (
        "mechanic.body-slam", "mechanic.giggle-juice-spray-attack",
        "mechanic.electrical-touch-attack",
    )):
        return weapon
    return merge_effects(weapon, attacker.global_effects)


def weapon_against_opponent(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
) -> EffectSet:
    """Port of ``modular.contexts.weapon_against_opponent``.

    A poison-immune opponent sees the poison-free contribution, so a coating
    never reaches the wound table against it.
    """
    if not (defender.global_effects.poison_immunity
            or has(defender.global_effects, "poison_immune")):
        return weapon
    if weapon == attacker.main_weapon and attacker.main_weapon_without_poison is not None:
        return attacker.main_weapon_without_poison
    if weapon == attacker.off_hand and attacker.off_hand_without_poison is not None:
        return attacker.off_hand_without_poison
    for poisoned, clean in attacker.extra_attacks_without_poison:
        if weapon == poisoned:
            return clean
    return weapon


def supplied_ward(effects: EffectSet, *, suppress_step_aside: bool = False) -> int:
    """Port of ``modular.contexts._supplied_ward``."""
    ward = effects.ward_save
    if has(effects, "mechanic.excellent-reflexes"):
        ward = min(ward, 4 if has(effects, "condition.tomb-robber-dodge-known") else 5)
    if effects.step_aside and not suppress_step_aside:
        ward = min(ward, 4 if has(effects, "skill.vampire-reflexes") else 5)
    if (effects.step_aside and not suppress_step_aside
            and has(effects, "skill.elven-agility")):
        ward = min(ward, 4)
    return ward


def attack_strength(
    attacker: CompiledFighter, defender: CompiledFighter, state: CombatState,
    weapon: EffectSet, effect: EffectSet, rows: np.ndarray, *,
    first_round: bool, charging, melee_attack: bool = True,
) -> tuple[np.ndarray, np.ndarray]:
    """Port of ``modular.contexts._attack_strength`` per row."""
    rows = np.asarray(rows)
    size = rows.size
    charge = np.broadcast_to(np.asarray(charging, dtype=bool), (size,))
    strength = (
        np.full(size, effect.fixed_strength, dtype=np.int16)
        if effect.fixed_strength
        else state.strength[rows].astype(np.int16) + effect.strength_bonus
    )
    if ignores_unarmed_penalties(effect) and has(weapon, "weapon.fist"):
        strength = strength + 1
    if has(effect, "mechanic.energy-focus") and any(
        has(weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks")
    ):
        strength = strength + effect.energy_focus_attacks
    retains = (
        has(effect, "mechanic.retain-flail-morning-star-strength-bonus")
        and any(has(weapon, tag) for tag in ("weapon.flail", "weapon.morning-star"))
    )
    if (first_round or has(effect, "skill.tireless")
            or has(effect, "skill.mighty-biceps") or retains):
        strength = strength + weapon.first_round_strength_bonus
    if (first_round and has(weapon, "weapon.spear")
            and has(effect, "mechanic.seaguard-spear-master")):
        strength = strength + 1
    if first_round and effect.charge_strength_bonus:
        mounted_only = any(has(weapon, tag) for tag in ("weapon.lance", "weapon.boar-spear"))
        if not mounted_only or attacker.mounted:
            strength = strength + charge.astype(np.int16) * effect.charge_strength_bonus
    if (melee_attack and first_round
            and has(attacker.global_effects, "rule.slay-large-creature")
            and has(defender.global_effects, "size.large")):
        strength = strength + charge.astype(np.int16)
    if has(defender.global_effects, "mechanic.foul-odour") and has(effect, "attack.fire"):
        strength = strength + 1
    if has(weapon, "rule.eagle-friend"):
        strength = np.full(size, 3, dtype=np.int16)
    if any(has(weapon, tag) for tag in ("rule.scorpion-tail", "rule.poisonous-bite")):
        immune = (defender.global_effects.poison_immunity
                  or has(defender.global_effects, "poison_immune"))
        strength = np.full(size, 2 if immune else 5, dtype=np.int16)
    armour_strength = strength + effect.armour_strength_modifier
    if has(effect, "mechanic.wolf-rat-bite"):
        # Printed S4 wounds normally but contributes no armour modifier.
        strength = np.full(size, 4, dtype=np.int16)
        armour_strength = np.full(size, 3, dtype=np.int16)
    strength = np.maximum(1, strength + defender.global_effects.incoming_strength_modifier)
    return strength, armour_strength


def hit_reroll(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
    effect: EffectSet, rows: np.ndarray, *, first_round: bool, charging,
    frenzy=False,
) -> np.ndarray:
    """Port of ``modular.contexts._hit_reroll`` per row."""
    rows = np.asarray(rows)
    size = rows.size
    charge = np.broadcast_to(np.asarray(charging, dtype=bool), (size,))
    frenzy = np.broadcast_to(np.asarray(frenzy, dtype=bool), (size,))
    enemy_tags = set(defender.global_effects.tags)
    attacker_tags = set(attacker.global_effects.tags)

    pride = False
    if first_round and has(effect, "mechanic.dueling-pride"):
        if not any(tag.startswith("house-guard.") for tag in effect.tags):
            raise ValueError("Dueling Pride requires an explicit House Guard house")
        if has(effect, "house-guard.fierezza") and has(effect, "fighter-kind.hero"):
            if not any(tag.startswith("fighter-kind.") for tag in defender.global_effects.tags):
                raise ValueError("Dueling Pride requires the opponent's explicit fighter role")
            pride = has(defender.global_effects, "fighter-kind.hero")
    amazon_enemy = any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in enemy_tags
    )
    kindred = False
    if (first_round and has(effect, "mechanic.kindred-hatred")
            and "species.vampire" in enemy_tags):
        bloodlines = [tag for tag in enemy_tags if tag.startswith("vampire-bloodline.")]
        if len(bloodlines) != 1:
            raise ValueError("Kindred Hatred requires the opposing Vampire's explicit bloodline")
        kindred = bloodlines[0] != "vampire-bloodline.strigoi"
    imposed_hatred = (
        first_round
        and has(defender.global_effects, "mechanic.fighting-undead")
        and "species.vampire" in attacker_tags
    )
    psychology_allowed = ~frenzy & (not has(attacker.global_effects, "mechanic.psychology-immunity"))
    hatred = first_round and psychology_allowed & (
        has(effect, "skill.hatred")
        or has(effect, "mechanic.burn-the-witch") and "identity.spellcaster" in enemy_tags
        or has(effect, "mechanic.hang-the-bandit") and "warband-group.bandit" in enemy_tags
        or has(effect, "mechanic.profound-hatred") and not bool(
            {"band.sisters-of-sigmar", "band.trollheim-sisters-of-sigmar"}.intersection(enemy_tags))
        or has(defender.global_effects, "mechanic.greenskin-traitor")
        and bool({"species.orc", "species.goblin", "species.black-orc"}.intersection(attacker_tags))
        or has(effect, "skill.righteous-fury") and (
            bool({"species.skaven", "nature.undead", "nature.possessed",
                  "species.beastman", "species.dark-elf"}.intersection(enemy_tags))
            or "warband-group.chaotic" in enemy_tags
            or "identity.chaos-follower" in enemy_tags
            or "warband-group.evil" in enemy_tags and not bool(
                {"warband-group.human", "warband-group.human-mercenary"}.intersection(enemy_tags))
        )
        or has(effect, "mechanic.noble-disdain") and "condition.ranged-armed" in enemy_tags
        or has(effect, "mechanic.hatred-human-warband") and bool(
            {"warband-group.human", "warband-group.human-mercenary",
             "warband-group.chaos-human"}.intersection(enemy_tags))
        or has(effect, "mechanic.ulric-intense-rivals") and "identity.ulric-rival" in enemy_tags
        or has(effect, "mechanic.hatred-chaotic-warband") and "warband-group.chaotic" in enemy_tags
        or has(effect, "mechanic.gaoler-hatred") and bool({
            "warband-group.skaven", "warband-group.beastmen", "warband-group.undead",
            "band.cult-of-the-possessed", "band.trollheim-cult-of-the-possessed",
            "band.carnival-of-chaos"}.intersection(enemy_tags))
        or has(effect, "mechanic.fanatical-hatred") and bool({
            "warband-group.orcs-and-goblins", "band.black-orcs", "band.forest-goblins",
            "band.forest-goblins-lus", "band.horned-hunters", "band.sisters-of-sigmar",
            "mercenary-origin.middenheim", "warband-group.skaven", "warband-group.undead",
            "warband-group.beastmen", "band.cult-of-the-possessed",
            "band.trollheim-cult-of-the-possessed",
            "band.carnival-of-chaos"}.intersection(enemy_tags))
        or has(effect, "mechanic.man-hater") and {"species.human", "sex.male"}.issubset(enemy_tags)
        or "identity.greenskin" in enemy_tags and any(has(effect, tag) for tag in (
            "mechanic.hatred-orcs-goblins", "mechanic.hatred-skaven-orcs-goblins"))
        or any(has(effect, tag) and any(f"species.{species}" in enemy_tags for species in targets)
            for tag, targets in (("mechanic.hatred-orcs-goblins", ("orc", "goblin")),
                                 ("mechanic.hatred-skaven", ("skaven",)),
                                 ("mechanic.hatred-dwarfs", ("dwarf",)),
                                 ("mechanic.hatred-skaven-orcs-goblins", ("skaven", "orc", "goblin")),
                                 ("mechanic.hatred-dwarfs-skaven", ("dwarf", "skaven"))))
        or has(effect, "mechanic.despise-despoilers") and "identity.necromancer" in enemy_tags
        or has(effect, "mechanic.hatred-undead") and "nature.undead" in enemy_tags
        or has(effect, "mechanic.hatred-beastmen") and "species.beastman" in enemy_tags
        or has(effect, "mechanic.hatred-dark-elves") and "species.dark-elf" in enemy_tags
        or has(effect, "mechanic.hatred-high-elves") and "species.high-elf" in enemy_tags
        or has(effect, "mechanic.vengeful-hatred") and _vengeful_enmity_target(effect, enemy_tags)
        or has(effect, "mechanic.hatred-slavers") and "identity.slaver" in enemy_tags
        or has(effect, "mechanic.amazon-isolationists") and amazon_enemy
    )
    kindred_rows = first_round and ~frenzy & kindred
    imposed_rows = first_round & imposed_hatred
    charge_rows = first_round & charge
    mask = (
        np.full(size, bool(effect.reroll_hits), dtype=bool)
        | np.full(size, bool(first_round and has(effect, "mechanic.first-round-hit-reroll")), dtype=bool)
        | np.full(size, bool(pride), dtype=bool)
        | np.full(size, bool(first_round and has(effect, "mechanic.pikewall")
                             and has(effect, "condition.being-charged")
                             and weapon.priority > 0), dtype=bool)
        | (charge_rows & bool(effect.charge_reroll_hits))
        | (charge & has(effect, "rule.berserk-charge") & any(
            has(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
            )))
        | np.asarray(hatred, dtype=bool)
        | np.full(size, bool(first_round and has(effect, "mechanic.devoted-killer-hatred")
                             and has(effect, "condition.devoted-killer-hatred")), dtype=bool)
        | kindred_rows
        | imposed_rows
        # Infallible rerolls on any charge, not only the first round's
        # (modular ``_hit_reroll``: ``charging and skill.infallible``).
        | (charge & has(effect, "skill.infallible"))
        | (charge_rows & has(effect, "skill.axe-expert") & any(
            has(weapon, tag) for tag in ("weapon.axe", "weapon.dwarf-axe")))
        | (charge_rows & has(effect, "skill.expert-swordsman") & any(
            has(weapon, tag) for tag in ("weapon.sword", "weapon.weeping-blades")))
        # Crack Shot is first-round-only but does not require the charge
        # (modular: ``first_round and skill.crack-shot`` with a pistol).
        | np.full(size, bool(first_round and has(effect, "skill.crack-shot") and any(
            has(weapon, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol"))), dtype=bool)
        | (charge & has(attacker.global_effects, "dagger_master") & any(
            has(weapon, tag) for tag in ("weapon.dagger", "weapon.yambiya")))
        | np.full(size, bool(has(effect, "skill.weapons-of-the-north") and any(
            has(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon"))), dtype=bool)
        | np.full(size, bool(first_round and has(effect, "skill.duellist")), dtype=bool)
        | np.full(size, bool(has(effect, "skill.virtue-of-valour")
                            and defender.characteristics.strength > attacker.characteristics.strength),
                 dtype=bool)
    )
    return mask


def _vengeful_enmity_target(effect: EffectSet, enemy_tags: set[str]) -> bool:
    """Port of ``modular.contexts.vengeful_enmity_target``."""
    marker = next((tag for tag in effect.tags if tag.startswith("enmity-target.")), None)
    if marker is None:
        return False
    kind, _, target = marker.partition(".")[2].partition(".")
    if not target:
        return False
    if kind == "individual":
        return f"instance.{target}" in enemy_tags
    if kind == "leader":
        return f"instance.{target}" in enemy_tags
    if kind == "warband":
        return f"warband-instance.{target}" in enemy_tags
    if kind == "warband-type":
        return f"warband-group.{target}" in enemy_tags
    return False


@dataclass(frozen=True, slots=True)
class VectorHitContext:
    weapon_skill: np.ndarray
    defender_weapon_skill: np.ndarray
    modifier: np.ndarray
    reroll: np.ndarray
    automatic: np.ndarray
    needs_sixes: np.ndarray
    fixed_target: int | None


def hit_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: CombatState, defender_state: CombatState,
    weapon: EffectSet, effect: EffectSet, rows: np.ndarray, *,
    first_round: bool = False, charging=False, melee_attack: bool = True,
    allow_luck: bool = True, helpless_at_start: bool = False,
    needs_sixes: np.ndarray | bool | None = None,
) -> VectorHitContext:
    """Port of ``modular.contexts.prepare_hit_context`` per row.

    ``hit_targets(..., modifier=ctx.modifier, fixed_target=ctx.fixed_target,
    needs_sixes=ctx.needs_sixes)`` finishes the projection; the successful
    roll itself stays with the attack consumer.

    ``needs_sixes`` accepts the full-batch mask from PsychologyResources;
    only ``rows`` are read. Omission retains the optional state-column input.
    """
    rows = np.asarray(rows)
    size = rows.size
    charge = np.broadcast_to(np.asarray(charging, dtype=bool), (size,))
    ws = attacker_state.weapon_skill[rows].astype(np.int16) + weapon.weapon_skill_bonus
    if first_round:
        ws = ws + charge.astype(np.int16) * effect.charge_ws_bonus
    modifier = np.full(
        size, effect.hit_modifier + defender.global_effects.incoming_hit_modifier,
        dtype=np.int16,
    )

    def adjust(condition, points: int = 1) -> None:
        nonlocal modifier
        modifier = modifier + np.where(
            np.broadcast_to(np.asarray(condition, dtype=bool), (size,)), points, 0,
        )

    if melee_attack and has(defender.global_effects, "condition.hypnotized"):
        adjust(True)
    if melee_attack:
        adjust(has(effect, "condition.ye-give-way-victorious"))
        adjust(has(effect, "condition.ye-give-way-refused"), -1)
    if melee_attack and has(defender.global_effects, "condition.djinns-curse-active"):
        adjust(True, -1)
    if melee_attack:
        adjust(bool(first_round and has(attacker.global_effects, "skill.backstabber")
                    and has(attacker.global_effects, "condition.unseen-charge")) & charge)
        adjust(bool(first_round and has(
            attacker.global_effects, "condition.summoned-this-turn")) & charge)
        adjust(np.broadcast_to(np.asarray(
            getattr(attacker_state, "banter_trick_active", False), dtype=bool,
        ), attacker_state.wounds.shape)[rows])
        adjust(np.broadcast_to(np.asarray(
            getattr(defender_state, "banter_trick_active", False), dtype=bool,
        ), defender_state.wounds.shape)[rows], -1)
    if melee_attack and has(attacker.global_effects, "condition.guiding-dream-target"):
        if not has(defender.global_effects, "fighter-kind.hero"):
            raise ValueError("Guiding Dream requires the nominated opposing model to be a Hero")
        adjust(np.isin(attacker_state.guiding_dream_result[rows], (2, 3)))
    if melee_attack and any(has(fighter.global_effects, "condition.snorri-stench")
                            for fighter in (attacker, defender)):
        adjust(True, -1)
    if (has(attacker.global_effects, "mechanic.flesh-peddler")
            and has(attacker.global_effects, "condition.flesh-peddler-mark")):
        if not has(defender.global_effects, "sex.female"):
            raise ValueError("Flesh-Peddler's nominated opponent requires an explicit female fact")
        adjust(True)
    if melee_attack and has(defender.global_effects, "mechanic.unholy-stink"):
        adjust(True, -1)
    if melee_attack and any(has(effect, tag) for tag in (
            "condition.command.follow-me-active", "condition.righteous-charge-active")):
        adjust(True)
    if (has(weapon, "weapon.hellblade")
            and not any(has(defender.global_effects, tag) for tag in ("nature.undead", "nature.daemon"))):
        adjust(True)
    adjust(melee_attack and has(attacker.global_effects, "mechanic.andanti-knowledge")
           and has(defender.global_effects, "species.vampire"))
    adjust(has(defender.main_weapon, "weapon.ball-and-chain"), -1)
    if (has(defender.global_effects, "rule.putrid-stench")
            and has(attacker.global_effects, "undead_or_possessed")):
        adjust(True)
    if has(effect, "skill.knife-fighting") and any(
        has(weapon, tag) for tag in ("weapon.dagger", "weapon.yambiya")
    ):
        ws = ws + 1
    if has(weapon, "effect.serpent-staff-power"):
        ws = np.full(size, 4, dtype=np.int16)
    adjust(charge & has(effect, "skill.berserker"))
    adjust(bool(first_round and has(effect, "skill.ferocious-charge")) & charge, -1)
    adjust(first_round and has(defender.global_effects, "skill.bellowing-battle-roar"), -1)
    adjust(has(defender.global_effects, "cloud_of_flies"), -1)
    if (melee_attack and has(defender.global_effects, phases.COLD_STEEL_TAG)
            and phases.cold_steel_metal_attack(weapon)
            and not phases.cold_steel_exempt(effect)):
        adjust(True, -1)
    adjust(melee_attack and has(defender.global_effects, "mechanic.foul-odour")
           and not any(has(attacker.global_effects, tag) for tag in
                       ("nature.undead", "nature.possessed", "nature.daemon")), -1)
    if melee_attack and has(defender.global_effects, "mechanic.sigmar-symbol-of-unity"):
        named = any(has(attacker.global_effects, tag) for tag in
                    ("band.witch-hunters", "band.trollheim-witch-hunters", "band.sisters-of-sigmar"))
        mercenary = has(attacker.global_effects, "warband-group.human-mercenary")
        if (mercenary and any(has(attacker.global_effects, tag) for tag in
                              ("band.mercenaries", "band.trollheim-mercenaries"))
                and not any(tag.startswith("mercenary-origin.")
                            for tag in attacker.global_effects.tags)):
            raise ValueError(
                "Symbol of Unity requires the generic mercenary warband's explicit origin"
            )
        excluded = any(has(attacker.global_effects, tag) for tag in
                       ("mercenary-origin.marienburg", "mercenary-origin.middenheim"))
        adjust(named or (mercenary and not excluded), -1)

    defender_ws = defender_state.weapon_skill[rows].astype(np.int16)
    if melee_attack and any(
        has(fighter.global_effects, "mechanic.shallya-tranquil-aura")
        for fighter in (attacker, defender)
    ):
        active = np.asarray(attacker_state.condition[rows] != OUT, dtype=bool)
        if not any(has(attacker.global_effects, tag) for tag in ("nature.daemon", "nature.undead")):
            ws = np.where(active, np.maximum(0, ws - 1), ws)
        if not any(has(defender.global_effects, tag) for tag in ("nature.daemon", "nature.undead")):
            defender_ws = np.where(active, np.maximum(0, defender_ws - 1), defender_ws)

    reroll = hit_reroll(
        attacker, defender, weapon, effect, rows,
        first_round=first_round, charging=charge, frenzy=attacker_state.frenzy[rows],
    )
    luck = (
        allow_luck and has(effect, "skill.luck")
        and ~attacker_state.luck_used[rows] & ~reroll
    )
    automatic = (
        bool(effect.automatic_hit or helpless_at_start)
        | np.broadcast_to(np.asarray(
            getattr(defender_state, "charm_auto_hit", False), dtype=bool,
        ), defender_state.wounds.shape)[rows]
        | (defender_state.condition[rows] == PARALYZED)
    )
    fear_mask = (getattr(attacker_state, "fear_hit_sixes", False)
                 if needs_sixes is None else needs_sixes)
    needs_sixes = np.broadcast_to(
        np.asarray(fear_mask, dtype=bool), attacker_state.wounds.shape,
    )[rows] & melee_attack
    fixed = 2 if melee_attack and has(effect, "mechanic.invincible-swordsman") else None
    return VectorHitContext(ws, defender_ws, modifier, reroll | luck, automatic, needs_sixes, fixed)


@dataclass(frozen=True, slots=True)
class VectorWoundContext:
    strength: np.ndarray
    toughness: np.ndarray
    modifier: np.ndarray
    maximum_target: int
    automatic: np.ndarray
    reroll: np.ndarray
    critical_threshold: np.ndarray
    critical_available: np.ndarray
    critical_on_reroll: np.ndarray
    critical_when_needing_six: np.ndarray
    failure_still_wounds: np.ndarray
    unharmed: np.ndarray


def wound_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: CombatState, defender_state: CombatState,
    weapon: EffectSet, effect: EffectSet, rows: np.ndarray, *,
    hit_roll=4, first_round: bool = False, charging=False,
    melee_attack: bool = True, allow_luck: bool = True,
) -> VectorWoundContext:
    """Port of ``modular.contexts.prepare_wound_context`` per row."""
    rows = np.asarray(rows)
    size = rows.size
    strength, _ = attack_strength(
        attacker, defender, attacker_state, weapon, effect, rows,
        first_round=first_round, charging=charging, melee_attack=melee_attack,
    )
    toughness = np.maximum(
        1,
        defender_state.toughness[rows].astype(np.int16)
        - int(melee_attack and has(defender.global_effects, "rule.thin-flesh")),
    )
    poison_blocked = (defender.global_effects.poison_immunity
                      or has(defender.global_effects, "poison_immune"))
    automatic = np.full(
        size,
        bool(has(effect, "effect.automatic-wound")
             or has(weapon, "effect.wraith-touch") and not any(
                 has(defender.global_effects, tag)
                 for tag in ("nature.undead", "nature.possessed"))),
        dtype=bool,
    )
    six = np.broadcast_to(np.asarray(hit_roll) == 6, (size,))
    luck = (
        allow_luck and has(effect, "skill.luck")
        and ~attacker_state.luck_used[rows] & (not bool(effect.reroll_wounds))
    )
    lotus = phases.black_lotus_wounds(effect, defender.global_effects)
    failure_still_wounds = six & bool(
        has(effect, "wight_blades") or lotus and not poison_blocked
    )
    maximum = effect.maximum_wound_target
    if has(effect, "skill.monster-slayer"):
        maximum = min(maximum, 4)
    if (has(weapon, "blessing.undead-possessed-on-two")
            and has(defender.global_effects, "undead_or_possessed")):
        maximum = min(maximum, 2)
    modifier = np.full(
        size,
        effect.wound_modifier + int(
            has(weapon, "weapon.sigmarite-hammer")
            and has(defender.global_effects, "undead_or_possessed")
        ),
        dtype=np.int16,
    )
    critical = 5 if (
        has(effect, "poison.wolfsbane") and not poison_blocked
        or has(effect, "mechanic.body-slam")
        or has(effect, "skill.art-of-silent-death")
        or has(attacker.global_effects, "spiritual_weapons")
        or has(effect, "skill.unarmed-critical-strikes") and any(
            has(weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks"))
    ) else 6
    critical = min(critical, effect.critical_threshold)
    critical_rows = np.full(size, critical, dtype=np.int8)
    if has(weapon, "weapon.hellblade"):
        targets = wound_targets(strength, toughness, maximum)
        critical_rows = np.where(
            np.maximum(2, targets.astype(np.int16) - modifier) <= 4,
            min(critical, 5), critical_rows,
        )
    reroll = (
        bool(effect.reroll_wounds) | luck
        | (has(effect, "skill.wound-valour")
           and defender.characteristics.strength > attacker.characteristics.strength)
    ) & ~(six & bool(lotus and not poison_blocked))
    return VectorWoundContext(
        strength, toughness, modifier, maximum,
        automatic=automatic,
        reroll=np.asarray(reroll, dtype=bool),
        critical_threshold=critical_rows,
        critical_available=~attacker_state.critical_used[rows]
        & (not has(effect, "effect.no-critical")),
        critical_on_reroll=np.full(
            size, bool(poison_blocked or not has(effect, "poison.devil-s-toxin")), dtype=bool,
        ),
        critical_when_needing_six=np.full(
            size, bool(has(effect, "mechanic.achilles-heel")), dtype=bool,
        ),
        failure_still_wounds=np.asarray(failure_still_wounds, dtype=bool),
        unharmed=np.full(
            size,
            phases.cold_steel_unharmed(defender.global_effects, weapon, effect),
            dtype=bool,
        ),
    )


@dataclass(frozen=True, slots=True)
class VectorArmourContext:
    armour_save: int
    natural_armour_save: int
    natural_armour_worst_save: int
    natural_armour_unmodified: bool
    armour_strength: np.ndarray
    armour_penetration: int
    target_armour_bonus: int
    ignore_armour: np.ndarray
    armour_save_floor: int
    armour_cannot_be_ignored: bool
    magical_attack: bool
    natural_armour_negated_by_magic: bool
    flaming_attack: bool
    natural_armour_negated_by_fire: bool
    incoming_save_modifier: int


def armour_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: CombatState, defender_state: CombatState,
    weapon: EffectSet, effect: EffectSet, rows: np.ndarray, *,
    first_round: bool = False, charging=False, melee_attack: bool = True,
) -> VectorArmourContext:
    """Port of ``modular.contexts.prepare_armour_context`` per row."""
    rows = np.asarray(rows)
    strength, armour_strength = attack_strength(
        attacker, defender, attacker_state, weapon, effect, rows,
        first_round=first_round, charging=charging, melee_attack=melee_attack,
    )
    dagger_tags = ("weapon.dagger", "weapon.yambiya",
                   "weapon.poisoned-daggers", "weapon.disease-dagger")
    dagger_pair = (
        attacker.main_weapon.paired
        and any(tag in attacker.main_weapon.tags for tag in dagger_tags)
        or attacker.off_hand is not None and all(
            any(tag in hand.tags for tag in dagger_tags)
            for hand in (attacker.main_weapon, attacker.off_hand)
        )
    )
    cutthroat = int(
        has(effect, "skill.cutthroat") and dagger_pair
        and any(tag in weapon.tags for tag in dagger_tags)
    )
    if has(effect, "skill.monster-slayer-effective-strength-armour"):
        toughness = defender_state.toughness[rows]
        armour_strength = np.where(
            strength < toughness, np.maximum(armour_strength, toughness), armour_strength,
        )
    armour_save = defender.armour_save
    if not melee_attack and has(defender.global_effects, "defence.sabertooth-hide"):
        armour_save += 1
    natural_save = defender.natural_armour_save
    natural_worst = defender.natural_armour_worst_save
    if (defender.global_effects.natural_armour_negated_by_fire
            and has(effect, "attack.fire")):
        natural_save = natural_worst = 7
        armour_save += max(0, 7 - defender.natural_armour_save)
    if (has(defender.global_effects, "mechanic.daemonic-flesh")
            and has(effect, "attack.blessed")):
        natural_save = natural_worst = 7
    if effect.ignore_armour_except_shield_and_skills:
        armour_save = max(1, 7 - defender.shield_and_skill_effects.armour_save_bonus)
        natural_save = natural_worst = 7
    if (has(defender.global_effects, "mechanic.norse-bulwark")
            and has(defender.main_weapon, "weapon.axe")
            and has(defender.shield_and_skill_effects, "defence.shield")):
        armour_save = max(2, armour_save - 1)
    ignore = np.full(
        rows.size, bool(effect.ignore_armour), dtype=bool,
    ) | (bool(effect.ignore_armour_against_knocked_down)
         & (defender_state.condition[rows] == KNOCKED_DOWN))
    return VectorArmourContext(
        armour_save, natural_save, natural_worst,
        defender.natural_armour_unmodified, armour_strength,
        effect.armour_penetration + cutthroat,
        effect.target_armour_bonus - (
            weapon.target_armour_bonus
            if has(weapon, "weapon.fist") and ignores_unarmed_penalties(effect) else 0
        ),
        ignore,
        defender.global_effects.armour_save_floor,
        defender.global_effects.armour_cannot_be_ignored,
        has(effect, "attack.magical"),
        defender.global_effects.natural_armour_negated_by_magic,
        has(effect, "attack.fire"),
        defender.global_effects.natural_armour_negated_by_fire,
        int(has(effect, "condition.djinns-curse-active")),
    )


def armour_target_values(context: VectorArmourContext) -> np.ndarray:
    """Port of ``modular.phases.armour_target`` over the projected context."""
    modifier = (
        np.maximum(0, context.armour_strength - 3)
        + context.armour_penetration
        - context.target_armour_bonus
    )
    armour = context.armour_save + modifier + context.incoming_save_modifier
    natural = np.full(
        context.armour_strength.size, context.natural_armour_save, dtype=np.int16,
    )
    if not context.natural_armour_unmodified:
        natural = np.minimum(
            natural + np.maximum(0, context.armour_strength - 3)
            - context.target_armour_bonus,
            context.natural_armour_worst_save,
        ) + context.armour_penetration + context.incoming_save_modifier
    if ((context.natural_armour_negated_by_magic and context.magical_attack)
            or (context.natural_armour_negated_by_fire and context.flaming_attack)):
        natural = np.full(context.armour_strength.size, 7, dtype=np.int16)
    target = np.minimum(armour, natural)
    if context.ignore_armour.any():
        replacement = (
            context.armour_save_floor + context.incoming_save_modifier
            if context.armour_cannot_be_ignored and not context.magical_attack else 7
        )
        target = np.where(context.ignore_armour, replacement, target)
    if context.armour_save_floor <= 6:
        protected = ~context.ignore_armour
        target = np.where(
            protected,
            np.minimum(target, context.armour_save_floor + context.incoming_save_modifier),
            target,
        )
    return target.astype(np.int16)


@dataclass(frozen=True, slots=True)
class VectorSpecialSaveContext:
    ward_save: np.ndarray
    regeneration_save: np.ndarray
    ward_blocked: np.ndarray
    regeneration_blocked: np.ndarray
    ward_unmodifiable: np.ndarray


def special_save_context(
    defender: CompiledFighter, incoming: EffectSet, state: CombatState,
    rows: np.ndarray, *, melee_attack: bool = True,
    dodge_trick_active: np.ndarray | bool | None = None,
) -> VectorSpecialSaveContext:
    """Port of the modular save context; optional dodge mask is full-batch."""
    rows = np.asarray(rows)
    size = rows.size
    djinn_curse = int(has(incoming, "condition.djinns-curse-active"))
    if incoming.ignore_armour_except_shield_and_skills:
        allowed = defender.shield_and_skill_effects
        ward = supplied_ward(allowed, suppress_step_aside=(
            has(defender.global_effects, "mechanic.ethereal-hit-save")
            and not has(incoming, "attack.magical")))
        return VectorSpecialSaveContext(
            np.full(size, ward + djinn_curse, dtype=np.int16),
            np.full(size, allowed.regeneration_save + djinn_curse, dtype=np.int16),
            np.full(size, bool(allowed.ward_save_mundane_only
                               and has(incoming, "attack.magical")), dtype=bool),
            np.full(size, bool(
                allowed.regeneration_blocked_by_fire and has(incoming, "attack.fire")
                or allowed.regeneration_blocked_by_blessed and has(incoming, "attack.blessed")
            ), dtype=bool),
            np.zeros(size, dtype=bool),
        )
    ward = np.full(size, supplied_ward(defender.global_effects, suppress_step_aside=(
        has(defender.global_effects, "mechanic.ethereal-hit-save")
        and not has(incoming, "attack.magical"))), dtype=np.int16)
    ward_blocked = np.full(size, bool(defender.global_effects.ward_save_mundane_only
                                     and has(incoming, "attack.magical")), dtype=bool)
    dodge = (getattr(state, "dodge_trick_active", None)
             if dodge_trick_active is None else dodge_trick_active)
    if melee_attack and dodge is not None:
        dodge_rows = np.broadcast_to(np.asarray(dodge, dtype=bool), state.wounds.shape)[rows]
        ward = np.where(dodge_rows, np.where(ward_blocked, 4, np.minimum(ward, 4)), ward)
        ward_blocked = ward_blocked & ~dodge_rows
    if (has(defender.global_effects, "mechanic.ghost-pirate-ethereal")
            and not any(has(incoming, tag) for tag in
                        ("attack.magical", "material.gromril", "material.ithilmar",
                         "ammo.silver-bullets"))):
        ward = np.where(ward_blocked, 4, np.minimum(ward, 4))
        ward_blocked[:] = False
    if has(defender.global_effects, "dance.shadows-coil-active"):
        ward = np.where(ward_blocked, 4, np.minimum(ward, 4))
        ward_blocked[:] = False
    if has(incoming, "attack.magical"):
        for tag, threshold in (("mechanic.gypsy-ward", 5), ("mechanic.magical-void", 4)):
            if has(defender.global_effects, tag):
                ward = np.where(ward_blocked, threshold, np.minimum(ward, threshold))
                ward_blocked[:] = False
    if has(defender.global_effects, "condition.djinns-luck-active"):
        threshold = np.where(ward_blocked | (ward > 6), 6, 4)
        ward = np.where(ward_blocked, threshold, np.minimum(ward, threshold))
        ward_blocked[:] = False
    blocked = (
        defender.global_effects.regeneration_blocked_by_fire and has(incoming, "attack.fire")
        or defender.global_effects.regeneration_blocked_by_blessed
        and has(incoming, "attack.blessed")
    )
    intrinsic_djinn = (
        bool(has(defender.global_effects, "mechanic.djinn-ethereal")
             and not has(defender.global_effects, "condition.djinns-luck-active")
             and not has(incoming, "attack.magical"))
        & ~ward_blocked & (ward >= 5)
    )
    return VectorSpecialSaveContext(
        (ward + np.where(intrinsic_djinn, 0, djinn_curse)).astype(np.int16),
        np.full(size, defender.global_effects.regeneration_save + djinn_curse, dtype=np.int16),
        ward_blocked,
        np.full(size, bool(blocked), dtype=bool),
        intrinsic_djinn,
    )


def parry_capacity(fighter: CompiledFighter) -> int:
    """Port of ``modular.state._parry_capacity`` (both skill grants included)."""
    effects = fighter.global_effects
    weapons = (fighter.main_weapon, fighter.off_hand or EffectSet())
    available = sum((
        fighter.main_weapon.parry,
        bool(fighter.off_hand and fighter.off_hand.parry),
        int(has(fighter.main_weapon, "weapon.double-bladed-sword")),
        effects.parry,
        int(has(effects, "skill.miniath")),
        int(has(effects, "skill.chosen-of-the-white-tower")),
        int(has(effects, "skill.instinctive-warrior") and any(
            has(weapon, "weapon.double-handed-weapon") for weapon in weapons)),
        int(has(effects, "skill.axe-master") and any(
            has(weapon, tag) for weapon in weapons
            for tag in ("weapon.axe", "weapon.dwarf-axe"))),
        int(has(effects, "skill.shield-mastery")
            and has(effects, "defence.shield")),
    ))
    two_parries = (
        has(effects, "skill.unbeatable-warrior")
        or has(fighter.main_weapon, "weapon.double-bladed-sword")
    )
    return min(2 if two_parries else 1, int(available))


@dataclass(frozen=True, slots=True)
class VectorParryContext:
    eligible: np.ndarray
    cannot_be_parried: bool
    match_allowed: bool
    fixed_target: int | None
    reroll: np.ndarray
    can_parry_six: bool
    roll_under: np.ndarray | None
    maximum_roll: np.ndarray | None
    strength: np.ndarray
    hit_roll: np.ndarray
    weapon_skill: np.ndarray


def parry_context(
    defender: CompiledFighter, defender_state: CombatState, effect: EffectSet,
    strength, hit_roll, rows: np.ndarray,
) -> VectorParryContext:
    """Port of ``modular.contexts._parry_context`` and its two weapon variants."""
    rows = np.asarray(rows)
    size = rows.size
    hit_roll = np.broadcast_to(np.asarray(hit_roll), (size,))
    parrying = (
        defender.main_weapon, defender.off_hand or EffectSet(),
        *(weapon for weapon in defender.extra_attacks
          if has(weapon, "mutation.carried-weapon")),
    )
    native = any(weapon.parry for weapon in parrying)
    effects = defender.global_effects
    match_allowed = (
        any(has(effects, tag) for tag in (
            "skill.sword-master", "skill.swordmaster", "skill.unbeatable-warrior"))
        or has(effects, "skill.defensive-stance") and native
    )
    starblade = any(has(weapon, "weapon.starblade") for weapon in parrying)
    reroll = native and has(effects, "skill.miniath")
    reroll = reroll or (
        has(effects, "skill.chosen-of-the-white-tower")
        and any(has(candidate, tag)
                for candidate in (*parrying, effects)
                for tag in ("weapon.sword", "defence.buckler"))
    )
    sword_and_buckler = (
        any(has(weapon, "weapon.sword") for weapon in parrying)
        and any(has(weapon, "defence.buckler") for weapon in (*parrying, effects))
    )
    dwarf_axes = (
        all(has(weapon, "weapon.dwarf-axe") for weapon in
            (defender.main_weapon, defender.off_hand) if weapon is not None)
        and defender.off_hand is not None
    )
    axe_and_sword = sorted(
        "axe" if has(weapon, "weapon.dwarf-axe")
        else "sword" if has(weapon, "weapon.sword")
        else "other"
        for weapon in (defender.main_weapon, defender.off_hand) if weapon is not None
    ) == ["axe", "sword"]
    sword_master_reroll = has(effects, "skill.sword-master") and (
        not has(effects, "rule.dwarf-axe-parry-reroll") or dwarf_axes
    )
    reroll = (reroll or sword_and_buckler or sword_master_reroll or dwarf_axes
              or axe_and_sword or has(defender.main_weapon, "weapon.fighting-claws"))
    reroll = reroll or has(defender.main_weapon, "weapon.double-bladed-sword")
    estalian = _estalian_parry(defender)
    darting = _darting_steel_parry(defender)
    capacity = parry_capacity(defender)
    eligible = (
        (defender_state.parry_remaining[rows] > 0)
        & (capacity > 0)
        & (defender_state.condition[rows] == STANDING)
    )
    return VectorParryContext(
        eligible, bool(effect.cannot_be_parried), match_allowed,
        fixed_target=4 if starblade else None,
        reroll=np.full(size, bool(reroll), dtype=bool),
        can_parry_six=(has(effects, "rule.blood-dragon-sword-master") or estalian),
        roll_under=defender_state.weapon_skill[rows] if estalian else None,
        maximum_roll=hit_roll if darting else None,
        strength=np.broadcast_to(np.asarray(strength), (size,)),
        hit_roll=hit_roll,
        weapon_skill=defender_state.weapon_skill[rows],
    )


def _estalian_parry(defender: CompiledFighter) -> bool:
    if _darting_steel_parry(defender):
        return True
    hands = (defender.main_weapon, defender.off_hand or EffectSet())
    return (has(defender.global_effects, "mechanic.estalian-technique")
            and any(has(weapon, "weapon.rapier") for weapon in hands)
            and any(has(weapon, "weapon.main-gauche") for weapon in hands))


def _darting_steel_parry(defender: CompiledFighter) -> bool:
    hands = (defender.main_weapon, defender.off_hand or EffectSet())
    return (has(defender.global_effects, "mechanic.darting-steel")
            and any(has(weapon, "weapon.sword") for weapon in hands)
            and any(has(weapon, "defence.buckler")
                    for weapon in (*hands, defender.global_effects)))


@dataclass(frozen=True, slots=True)
class VectorInjuryContext:
    modifier: np.ndarray
    out_threshold: np.ndarray
    stun_threshold: np.ndarray
    injury_profile: np.ndarray
    hard_to_kill: np.ndarray
    true_grit: np.ndarray
    concussion: np.ndarray
    concussion_immune: np.ndarray
    shock: np.ndarray
    fragile: np.ndarray
    poisonous: np.ndarray
    survivor: np.ndarray
    initial_condition: np.ndarray
    head_crusher: np.ndarray
    ignore_pain: np.ndarray
    jump_up: np.ndarray
    mandrake: np.ndarray


def injury_context(
    defender: CompiledFighter, effect: EffectSet, state: CombatState,
    rows: np.ndarray, *, injury_bonus: int = 0,
) -> VectorInjuryContext:
    """Port of ``modular.contexts._injury_context`` per row."""
    rows = np.asarray(rows)
    size = rows.size
    effects = defender.global_effects
    artefact = has(effect, "weapon.count-of-ventimiglias-misericordia")
    modifier = (
        effect.injury_modifier + int(injury_bonus)
        + int(has(effect, "mechanic.blessing-of-morr")
              and has(effects, "nature.undead"))
        + int(has(effect, "skill.knife-fighting")
              and any(has(effect, tag) for tag in ("weapon.dagger", "weapon.yambiya")))
        - int(has(effects, "mechanic.inured-to-pain"))
    )
    out_threshold = (
        4 if artefact or has(effects, "mechanic.bat-injury-chart")
        else effects.out_of_action_threshold
    )
    hard_to_kill = (
        has(effects, "skill.hard-to-kill")
        or has(effects, "mechanic.fen-hard-to-kill") and not has(effect, "attack.fire")
    )
    true_grit = has(effects, "skill.tough-as-steel") or bool(effects.true_grit)
    return VectorInjuryContext(
        np.full(size, modifier, dtype=np.int16),
        np.full(size, out_threshold, dtype=np.int8),
        np.full(size, 1 if artefact else 3, dtype=np.int8),
        np.full(size, defender.injury_profile, dtype=np.int8),
        np.full(size, bool(hard_to_kill), dtype=bool),
        np.full(size, bool(true_grit), dtype=bool),
        np.full(size, bool(effect.concussion), dtype=bool),
        np.full(size, bool(has(effects, "concussion_immune")), dtype=bool),
        np.full(size, bool(has(effect, "weapon.shock-rod")), dtype=bool),
        np.full(size, bool(has(effects, "fragile_halflings")), dtype=bool),
        np.full(size, bool(has(effect, "poisonous_injury") and not (
            effects.poison_immunity or has(effects, "poison_immune"))), dtype=bool),
        np.full(size, bool(has(effects, "survivor")), dtype=bool),
        state.condition[rows].astype(np.int8),
        np.full(size, bool(has(effect, "skill.head-crusher")), dtype=bool),
        np.full(size, bool(has(effects, "skill.ignore-pain")
                           and not has(effects, "rule.squishy")), dtype=bool),
        np.full(size, bool(has(effects, "skill.jump-up")), dtype=bool),
        np.full(size, bool(has(effects, "preparation.mandrake-root")), dtype=bool),
    )


def injury_results(totals: np.ndarray, context: VectorInjuryContext) -> np.ndarray:
    """Port of ``modular.phases.injury_condition`` over the projected context.

    ``totals`` is a 1-D series of rolls for one row, or one row of totals per
    simulated duel; a per-row flag is broadcast along the trailing axis.
    """
    totals = np.asarray(totals, dtype=np.int16)
    size = context.out_threshold.size

    def field(name: str) -> np.ndarray:
        value = getattr(context, name)
        if totals.ndim > 1 and np.ndim(value) == 1:
            value = value.reshape((size,) + (1,) * (totals.ndim - 1))
        return value

    result = np.where(
        totals >= field("out_threshold"), OUT,
        np.where(totals >= field("stun_threshold"), STUNNED, KNOCKED_DOWN),
    ).astype(np.int8)
    result = np.where(
        field("hard_to_kill"),
        np.where(totals >= 6, OUT, np.where(totals >= 3, STUNNED, KNOCKED_DOWN)),
        result,
    )
    result = np.where(
        field("true_grit"),
        np.where(totals >= 6, OUT, np.where(totals >= 4, STUNNED, KNOCKED_DOWN)),
        result,
    )
    result = np.where(
        field("concussion") & ~field("concussion_immune")
        & (totals >= 2) & (totals <= 4), STUNNED, result,
    )
    result = np.where(field("shock") & (totals >= 1) & (totals <= 4), STUNNED, result)
    result = np.where(
        field("injury_profile") == 1,
        np.where(totals >= 4, OUT, np.where(totals >= 2, STUNNED, KNOCKED_DOWN)),
        result,
    )
    result = np.where(
        field("injury_profile") == 3,
        np.where(totals >= 4, OUT, KNOCKED_DOWN),
        result,
    )
    result = np.where(field("fragile") & (totals == 2), STUNNED, result)
    result = np.where(
        field("poisonous"),
        np.where(totals >= 5, OUT, np.where(totals >= 2, STUNNED, KNOCKED_DOWN)),
        result,
    )
    result = np.where(
        field("survivor") & (field("initial_condition") == STANDING) & (result == OUT),
        STUNNED, result,
    )
    result = np.where(field("head_crusher") & (result == KNOCKED_DOWN), STUNNED, result)
    no_pain = field("ignore_pain") & (result == STUNNED)
    result = np.where(no_pain, KNOCKED_DOWN, result)
    result = np.where(
        field("jump_up") & (result == KNOCKED_DOWN) & ~no_pain, STANDING, result,
    )
    result = np.where(field("mandrake") & (result == STUNNED), KNOCKED_DOWN, result)
    return result.astype(np.int8)
