"""Vectorized engine: per-weapon attack preparation, hit/parry
boundaries and wound resolution."""
from __future__ import annotations

import numpy as np
from dataclasses import replace
from functools import lru_cache
from mordheim_combat.phases import InjuryContext, bear_hug_wins, ignores_unarmed_penalties
from mordheim_core.dice import AlwaysAccept, DecisionPolicy
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter, EffectSet
from mordheim_combat.vectorized._types import CombatState, KNOCKED_DOWN, OUT, OptionalPhasePlan, PARALYZED, PreparedAttack, STANDING, STUNNED, VectorAttackObservation, _claim_criticals, _critical_wound_threshold, _has_weapon_tag, _parry_capacity, _run_starts, has
from mordheim_combat.vectorized._operators import _characteristic_test, armour_targets, hit_targets, injury_conditions, special_save_targets, wound_targets

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

def _parry_hits(defender: CompiledFighter, effect: EffectSet, hit_rows: np.ndarray,
                hit_values: np.ndarray, hit_strength: np.ndarray,
                defender_state: CombatState,
                rng: np.random.Generator,
                selected_rows: np.ndarray | None = None) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    """Return (surviving rows, parried rows, survivor mask over the input rows).

    The survivor mask lets callers filter sibling arrays (e.g. positions within
    the active pool) without a second searchsorted over the whole pool.
    """
    if effect.cannot_be_parried:
        return hit_rows,np.empty(0,dtype=np.int64),np.ones(hit_rows.size,dtype=bool)
    parry = (defender.main_weapon.parry or bool(defender.off_hand and defender.off_hand.parry)
             or defender.global_effects.parry or has(defender.global_effects,"skill.miniath"))
    parry |= has(defender.global_effects,"skill.axe-master") and (
        has(defender.main_weapon,"weapon.axe")
        or bool(defender.off_hand and has(defender.off_hand,"weapon.axe"))
    )
    parry |= has(defender.global_effects,"skill.shield-mastery") and bool(defender.off_hand and has(defender.off_hand,"defence.shield"))
    if not parry or hit_rows.size == 0:
        return hit_rows,np.empty(0,dtype=np.int64),np.ones(hit_rows.size,dtype=bool)
    can_parry_six = has(defender.global_effects, "rule.blood-dragon-sword-master")
    # A natural six in the eligible pool prevents substituting a lower hit.
    if not can_parry_six and _parry_capacity(defender) < 2:
        defender_state.parry_remaining[np.unique(hit_rows[hit_values == 6])] = 0
    eligible = ((defender_state.condition[hit_rows] == STANDING)
                & (defender_state.parry_remaining[hit_rows] > 0)
                & (hit_strength < 2 * defender_state.strength[hit_rows])
                & ((hit_values != 6) | can_parry_six))
    if selected_rows is not None:
        # ``resolve_attacks`` has already selected the highest one or two hits
        # for each duel row across the complete attack pool. Repeating that
        # grouping here would introduce a Python loop per simulated duel.
        eligible &= np.isin(hit_rows, selected_rows)
    else:
        eligible_values = hit_rows[eligible]
        eligible_rows = eligible_values[_run_starts(eligible_values)]
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
        return hit_rows,np.empty(0,dtype=np.int64),np.ones(hit_rows.size,dtype=bool)
    parry_roll = rng.integers(1, 7, hit_rows.size)
    match_allowed = any(has(defender.global_effects,x) for x in ("skill.sword-master","skill.swordmaster","skill.defensive-stance","skill.unbeatable-warrior"))
    starblade = has(defender.main_weapon, "weapon.starblade") or bool(
        defender.off_hand and has(defender.off_hand, "weapon.starblade")
    )
    parry_success = parry_roll >= 4 if starblade else (
        (parry_roll >= hit_values) if match_allowed else (parry_roll > hit_values)
    )
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
              or dwarf_axes or has(defender.main_weapon, "weapon.fighting-claws")
              or has(defender.main_weapon,"weapon.double-bladed-sword"))
    if reroll and (~blocked).any():
        second = rng.integers(1, 7, hit_rows.size)
        second_success = second >= 4 if starblade else (
            (second >= hit_values) if match_allowed else (second > hit_values)
        )
        blocked |= eligible & blockable_roll & second_success
    defender_state.parry_used[hit_rows[eligible]] = True
    np.add.at(defender_state.parry_remaining, hit_rows[eligible], -1)
    return hit_rows[~blocked],hit_rows[blocked],~blocked

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
    first_round: bool, *, melee_attack: bool = True) -> PreparedAttack | None:
    if active.size == 0:
        return None
    weapon, effect, unarmed_adjustment = _compiled_attack_effect(attacker, defender, weapon)
    if melee_attack:
        stunned = active[defender_state.condition[active] == STUNNED]
        defender_state.condition[stunned] = OUT
    active = active[defender_state.condition[active] != OUT]
    if active.size == 0:
        return None
    charge_rows = charging[active]
    strength = (np.full(active.size,effect.fixed_strength,dtype=np.int16) if effect.fixed_strength
                else attacker_state.strength[active]
                + effect.strength_bonus if effect.strength_bonus
                else attacker_state.strength[active])
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
    if first_round and effect.charge_strength_bonus and charge_rows.any():
        mounted_only = any(has(weapon, tag) for tag in ("weapon.lance", "weapon.boar-spear"))
        if not mounted_only or attacker.mounted:
            strength += charge_rows.astype(np.int16) * effect.charge_strength_bonus
    armour_strength = (strength + effect.armour_strength_modifier
                       if effect.armour_strength_modifier else strength)
    if defender.global_effects.incoming_strength_modifier:
        strength = np.maximum(1, strength + defender.global_effects.incoming_strength_modifier)
    attacker_ws = attacker_state.weapon_skill[active]
    if weapon.weapon_skill_bonus:
        attacker_ws = attacker_ws + weapon.weapon_skill_bonus
    knife_fighting=has(effect,"skill.knife-fighting") and (
        has(weapon,"weapon.dagger") or has(weapon,"weapon.yambiya")
    )
    attacker_ws += int(knife_fighting)
    if first_round and effect.charge_ws_bonus and charge_rows.any():
        attacker_ws_values = attacker_ws + charge_rows.astype(np.int8) * effect.charge_ws_bonus
    else:
        attacker_ws_values = attacker_ws
    if has(weapon, "effect.serpent-staff-power"):
        attacker_ws_values = np.full(active.size, 4, dtype=np.int16)
    hit_target = hit_targets(attacker_ws_values, defender_state.weapon_skill[active])
    modifier = effect.hit_modifier + defender.global_effects.incoming_hit_modifier
    modifier -= int(has(defender.main_weapon, "weapon.ball-and-chain"))
    if has(defender.global_effects, "rule.putrid-stench") and has(
        attacker.global_effects, "undead_or_possessed"
    ):
        modifier += 1
    if first_round and has(defender.global_effects, "skill.bellowing-battle-roar"):
        modifier -= 1
    if has(defender.global_effects,"cloud_of_flies"):
        modifier -= 1
    hit_target = np.clip(hit_target - modifier, 2, 6)
    if has(effect, "skill.berserker"):
        hit_target[charge_rows] = np.clip(hit_target[charge_rows] - 1, 2, 6)
    if first_round and has(attacker.global_effects, "skill.ferocious-charge"):
        hit_target[charge_rows] = np.clip(hit_target[charge_rows] + 1, 2, 6)
    if has(effect,"skill.sweep") and weapon.two_handed:
        failed_tests = ~_characteristic_test(defender, defender_state.initiative[active], rng)
        rolls=np.where(failed_tests,6,1).astype(np.int8);successful=failed_tests
    else:
        automatic = (defender_state.weapon_skill[active] == 0) | effect.automatic_hit
        automatic |= np.isin(defender_state.condition[active], (KNOCKED_DOWN, PARALYZED))
        rolls = np.zeros(active.size, dtype=np.int8)
        if (~automatic).any():
            rolls[~automatic] = rng.integers(1, 7, int((~automatic).sum()), dtype=np.int8)
        successful = automatic | (rolls >= hit_target)
        hit_target[defender_state.weapon_skill[active] == 0] = 0
    helpless_cond = defender_state.condition[active]
    helpless = (helpless_cond == KNOCKED_DOWN) | (helpless_cond == PARALYZED)
    successful |= helpless
    rolls[helpless] = 0
    reroll = np.full(active.size, effect.reroll_hits, dtype=bool)
    if effect.charge_reroll_hits:
        reroll |= charge_rows
    if has(effect, "rule.berserk-charge") and any(
        has(weapon, tag) for tag in (
            "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
        )
    ):
        reroll |= charge_rows
    if first_round and has(effect, "skill.hatred"):
        reroll |= True
    amazon_enemy=any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in defender.global_effects.tags
    )
    if first_round and has(attacker.global_effects,"mechanic.amazon-isolationists") and amazon_enemy:
        reroll |= True
    if has(effect, "skill.infallible"):
        reroll |= charge_rows
    if first_round and has(effect,"skill.axe-expert") and (has(weapon,"weapon.axe") or has(weapon,"weapon.dwarf-axe")):
        reroll |= charge_rows
    if first_round and has(effect,"skill.expert-swordsman") and any(has(weapon,x) for x in ("weapon.sword","weapon.scimitar","weapon.weeping-blades")):
        reroll |= charge_rows
    if first_round and has(effect,"skill.crack-shot") and any(has(weapon,x) for x in ("weapon.pistol","weapon.duelling-pistol")):
        reroll |= True
    if has(attacker.global_effects,"dagger_master") and (has(weapon,"weapon.dagger") or has(weapon,"weapon.yambiya")):
        reroll |= charge_rows
    if has(effect,"skill.weapons-of-the-north") and any(
        has(weapon, tag) for tag in (
            "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
        )
    ):
        reroll |= True
    if first_round and has(effect,"skill.duellist"):
        reroll |= True
    if has(effect,"skill.luck"):
        luck = ~attacker_state.luck_used[active] & ~reroll
        reroll |= luck
    else:
        luck = None
    if has(effect, "skill.virtue-of-valour"):
        reroll |= defender_state.strength[active]>attacker_state.strength[active]
    rerolled = np.zeros(active.size, dtype=bool)
    failed = np.flatnonzero(reroll & ~successful)
    if failed.size:
        rerolled[failed] = True
        rerolls = rng.integers(1, 7, failed.size)
        successful[failed] = rerolls >= hit_target[failed]
        rolls[failed] = rerolls
        if luck is not None:
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
    hit_positions: np.ndarray | None = None,
) -> np.ndarray:
    """Resolve the hit-to-parry boundary once and return surviving hits."""
    weapon,effect,active,strength,rolls = (
        prepared.weapon,prepared.effect,prepared.active,prepared.strength,prepared.rolls
    )
    hit_rows=prepared.hit_rows[defender_state.condition[prepared.hit_rows]!=OUT]
    if hit_positions is None:
        hit_positions=np.searchsorted(active,hit_rows)
    else:
        hit_positions=hit_positions[defender_state.condition[prepared.hit_rows]!=OUT]
    hit_values=rolls[hit_positions]
    hit_rows,parried_rows,survived=_parry_hits(
        defender,effect,hit_rows,hit_values,strength[hit_positions],defender_state,rng,parry_rows
    )
    hit_positions=hit_positions[survived]
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
        kept=~(eligible&(charm_rolls>=4))
        hit_rows=hit_rows[kept]
        hit_positions=hit_positions[kept]
    return hit_rows, hit_positions

def _resolve_weapon(attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
                    active: np.ndarray, charging: np.ndarray, attacker_state: CombatState,
                    defender_state: CombatState, rng: np.random.Generator, first_round: bool,
                    **options) -> None:
    """Resolve complete weapon attacks, including repeated Rapier Barrage."""
    original = weapon
    penalty = 0
    any_hit = False
    while active.size:
        continuation = []
        _resolve_weapon_once(attacker, defender, weapon, active, charging,
            attacker_state, defender_state, rng, first_round,
            barrage_rows=continuation, **options)
        from ._driver import _rescue_force_of_will
        _rescue_force_of_will(defender, defender_state, active, rng)
        _rescue_force_of_will(attacker, attacker_state, active, rng)
        observation = options.get('observation')
        if observation is not None:
            any_hit |= observation.hit
            observation.hit = any_hit
        if not continuation:
            return
        active = np.concatenate(continuation)
        active = active[(attacker_state.condition[active] != OUT) & (defender_state.condition[active] != OUT)]
        penalty += 1
        weapon = replace(original, hit_modifier=original.hit_modifier - penalty)
        options = {**options, 'prepared': None, 'parry_rows': None,
                   'defences_resolved': False, 'hit_positions': None}


def _resolve_weapon_once(attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
                    active: np.ndarray, charging: np.ndarray, attacker_state: CombatState,
                    defender_state: CombatState, rng: np.random.Generator, first_round: bool,
                    prepared: PreparedAttack | None = None,
                    parry_rows: np.ndarray | None = None,
                    defender_phase_condition: np.ndarray | None = None,
                    decisions: DecisionPolicy | None = None,
                    defences_resolved: bool = False,
                    hit_positions: np.ndarray | None = None,
                    observation: VectorAttackObservation | None = None,
                    barrage_rows: list[np.ndarray] | None = None,
                    key: str = "test", melee_attack: bool = True) -> None:
    prepared = prepared or _prepare_weapon_attack(attacker,defender,weapon,active,charging,attacker_state,defender_state,rng,first_round,
        melee_attack=melee_attack)
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
        hit_rows, hit_positions = _apply_hit_defences(
            attacker,defender,prepared,attacker_state,defender_state,rng,charging,parry_rows,
            hit_positions,
        )
        if observation is not None and prepared.hit_rows.size and hit_rows.size == 0:
            row = int(prepared.hit_rows[0])
            observation.parried = defender_state.parry_remaining[row] < parries_before[row]
            observation.saved = bool(charms_before[row] and not defender_state.lucky_charm[row]
                                     and not observation.parried)
    if hit_rows.size == 0:
        return
    if defences_resolved:
        hit_positions = np.searchsorted(active, hit_rows)
    hit_values = rolls[hit_positions]
    if has(weapon,"weapon.kusara-kama"):
        penalized=hit_rows[hit_values>=5]
        np.add.at(defender_state.attack_penalty,penalized,1)
        for row in penalized:
            main = (not defender.off_hand_attacks or defender.off_hand is None or decisions is None
                    or decisions.choose(f'{key}.kusara-main-hand', defender))
            target = defender_state.hampered_main if main else defender_state.hampered_off
            target[row] += 1
    if has(weapon,"weapon.chained-squig"):
        defender_state.entangled[hit_rows]=True
    # Anvil Head replaces charge attacks only: the D3 wound expansion is
    # inert outside a charge (Khemri, Necromantic Modification / Anvil Head).
    # Dice are drawn only for charging rows so the RNG stream stays aligned
    # with the native backend.
    if first_round and has(effect,"mechanic.anvil-head"):
        charging_hits = charging[hit_rows]
        if charging_hits.any():
            repeats=np.ones(hit_rows.size,dtype=np.int64)
            repeats[charging_hits]=rng.integers(1,4,int(charging_hits.sum()))
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
    # Disease Dagger adds one ordinary automatic wound on a natural-six hit.
    # Immunity blocks only this additional wound; the ordinary dagger wound
    # continues through the normal pipeline.
    if has(weapon, "weapon.disease-dagger") and not poison_blocked and not has(
        defender.global_effects, "undead_or_possessed"
    ):
        candidates = hit_rows[hit_values == 6]
        if candidates.size:
            infection_passed = _characteristic_test(
                defender, defender_state.toughness[candidates], rng,
            )
            infected = candidates[~infection_passed]
            if infected.size:
                infection = EffectSet(
                    tags=("effect.automatic-wound", "effect.no-critical"),
                    fixed_strength=3, automatic_hit=True,
                    cannot_be_parried=True,
                )
                _resolve_weapon(
                    attacker, defender, infection, infected,
                    np.zeros(charging.size, dtype=bool), attacker_state,
                    defender_state, rng, False, melee_attack=False,
                )
                alive = defender_state.condition[hit_rows] != OUT
                hit_rows = hit_rows[alive]
                hit_positions = hit_positions[alive]
                hit_values = hit_values[alive]
    if has(effect, "poison.spider-spittle") and not poison_blocked:
        candidates = hit_rows[defender_state.condition[hit_rows] == STANDING]
        failed_tests = ~_characteristic_test(defender, defender_state.toughness[candidates], rng)
        defender_state.condition[candidates[failed_tests]] = PARALYZED
    automatic_wound = np.full(hit_rows.size, has(effect, "effect.automatic-wound"), dtype=bool)
    guaranteed_wound = (hit_values == 6) & (
        (has(effect, "poison.black-lotus") and not poison_blocked) or has(effect, "wight_blades")
    )
    if has(effect, "poison.black-lotus") and not poison_blocked and decisions is not None:
        for position in np.flatnonzero(guaranteed_wound):
            if not decisions.choose(f"{key}.lotus-critical", int(hit_rows[position])):
                automatic_wound[position] = True
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
    # Automatic wounds (e.g. a won bear hug) roll no die: the modular oracle
    # returns roll=0 for them, so drawing one here would shift every later
    # roll (special saves, injury) and diverge from the oracle.
    wound_rolls = np.zeros(hit_rows.size, dtype=np.int8)
    if not automatic_wound.all():
        wound_rolls[~automatic_wound] = rng.integers(1, 7, int((~automatic_wound).sum()))
    critical_rolls = wound_rolls.copy()
    wounded = automatic_wound | guaranteed_wound | (wound_rolls >= targets)
    if has(effect, "poison.manbane") and not poison_blocked:
        wounded &= wound_rolls != 1
    if effect.reroll_wounds and (~wounded).any():
        failed = np.flatnonzero(~wounded)
        rerolls = rng.integers(1, 7, failed.size)
        wounded[failed] = rerolls >= targets[failed]
        wound_rolls[failed] = rerolls
        if poison_blocked or not has(effect, "poison.devil-s-toxin"):
            critical_rolls[failed] = rerolls
    if has(attacker.global_effects,"mechanic.mark-of-the-old-ones"):
        available=(~wounded)&(~attacker_state.mark_of_old_ones_used[hit_rows])
        chosen=np.flatnonzero(available)
        if chosen.size:
            wounded[chosen]=True
            wound_rolls[chosen]=targets[chosen]
            attacker_state.mark_of_old_ones_used[hit_rows[chosen]]=True
    if has(weapon, "weapon.rapier") and (~wounded).any() and barrage_rows is not None:
        barrage_rows.append(hit_rows[~wounded])
    wound_rows = hit_rows[wounded]
    if observation is not None:
        observation.wounded = bool(wound_rows.size)
    if wound_rows.size == 0:
        return
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
        positions = np.flatnonzero(critical)
        cancelled = positions[rng.integers(1, 7, positions.size) >= 5]
        critical[cancelled] = False
        attacker_state.critical_used[wound_rows[cancelled]] = False
    critical_results = np.zeros(wound_rows.size, dtype=np.int16)
    if critical.any():
        critical_results[critical] = (rng.integers(1, 7, int(critical.sum()))
            + effect.critical_injury_bonus + int(has(effect, "skill.web-of-steel")))
    magical_attack = has(effect,"attack.magical")
    save_target = armour_targets(
        defender, wound_strength, effect, magical_attack, critical_results >= 3,
    )
    saved = np.zeros(wound_rows.size, dtype=bool)
    eligible = save_target <= 6
    if eligible.any():
        saved[eligible] = rng.integers(1, 7, int(eligible.sum())) >= np.maximum(2, save_target[eligible])
    if has(defender.global_effects, "skill.luck"):
        rerolled = eligible & ~saved & ~defender_state.luck_used[wound_rows]
        if rerolled.any():
            rerolls = rng.integers(1, 7, int(rerolled.sum()))
            saved[rerolled] = rerolls >= np.maximum(2, save_target[rerolled])
            defender_state.luck_used[wound_rows[rerolled]] = True
    if has(defender.global_effects, "mechanic.mark-of-the-old-ones"):
        converted = eligible & ~saved & ~defender_state.mark_of_old_ones_used[wound_rows]
        if converted.any():
            saved[converted] = True
            defender_state.mark_of_old_ones_used[wound_rows[converted]] = True
    if observation is not None and saved.any():
        observation.saved = True
        observation.critical = bool(critical[saved].any())
    wound_rows = wound_rows[~saved]
    critical = critical[~saved]
    critical_results = critical_results[~saved]
    if wound_rows.size == 0:
        return
    ward, regeneration = special_save_targets(defender, effect)
    if ward <= 6:
        protected = rng.integers(1, 7, wound_rows.size) >= ward
        if observation is not None and protected.any():
            observation.saved = True
        wound_rows = wound_rows[~protected]
        critical = critical[~protected]
        critical_results = critical_results[~protected]
    if regeneration<=6 and wound_rows.size:
        regenerated=rng.integers(1,7,wound_rows.size)>=regeneration
        if observation is not None and regenerated.any():
            observation.saved = True
        wound_rows=wound_rows[~regenerated];critical=critical[~regenerated]
        critical_results = critical_results[~regenerated]
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
    helpless_wounds = (condition_for_helpless == KNOCKED_DOWN) & melee_attack
    defender_state.condition[wound_rows[helpless_wounds]] = OUT
    damage = (rng.integers(1, effect.damage_die_sides + 1, wound_rows.size)
              if effect.damage_die_sides else np.full(wound_rows.size, max(1, effect.damage)))
    damage = np.maximum(damage, np.where(critical, 2, 1))
    if has(defender.global_effects,"flammable") and has(effect,"attack.fire"):
        damage *= 2
    if observation is not None:
        observation.damage = int(damage[0])
        observation.critical = bool(critical.any())
    affected_rows = wound_rows[_run_starts(wound_rows)]
    wounds_before = defender_state.wounds[affected_rows].copy()
    damage_rows = np.repeat(wound_rows, damage)
    damage_critical_bonus = np.repeat(np.where(critical_results >= 5, 2, 0), damage)
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
                melee_attack=False,
            )
    if has(effect, "poison.nightshade") and not poison_blocked:
        np.add.at(defender_state.initiative_penalty, damage_rows, 1)
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
        defender_state.condition[injury_rows[_run_starts(injury_rows)]] = OUT
        return
    injury_rolls = rng.integers(1, 7, injury_rows.size) + effect.injury_modifier + int(knife_fighting)
    injury_rolls += damage_critical_bonus[injury_mask]
    threshold = defender.global_effects.out_of_action_threshold
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
    if has(defender.global_effects, "injury_reroll_out") and not has(effect, "attack.fire"):
        reroll = injury == OUT
        if decisions is not None:
            ordinals = {}
            for position, row in enumerate(injury_rows):
                index = ordinals.get(int(row), 0)
                ordinals[int(row)] = index + 1
                reroll[position] = decisions.choose(f"{key}.injury.{index}.reroll-choice", int(injury[position]))
        if reroll.any():
            totals = (rng.integers(1, 7, int(reroll.sum())) + effect.injury_modifier
                      + int(knife_fighting) + damage_critical_bonus[injury_mask][reroll])
            injury[reroll] = injury_conditions(totals, injury_context)
    injured = injury_rows[_run_starts(injury_rows)]
    highest_by_row = np.full(defender_state.condition.size, STANDING, dtype=np.int8)
    np.maximum.at(highest_by_row, injury_rows, injury)
    highest = highest_by_row[injured]
    stunned = highest == STUNNED
    if stunned.any() and (defender.global_effects.thick_skull or defender.helmet_save <= 6):
        threshold_roll = ((2 if defender.helmet_save <= 4 else 3)
                          if defender.global_effects.thick_skull else defender.helmet_save)
        converted = np.flatnonzero(stunned)[rng.integers(1, 7, int(stunned.sum())) >= threshold_roll]
        highest[converted] = KNOCKED_DOWN
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
            hit_positions=np.searchsorted(prepared.active,hit_rows)
            hit_values=prepared.rolls[hit_positions]
            hit_strength=prepared.strength[hit_positions]
            hit_rows,_,_=_parry_hits(defender,prepared.effect,hit_rows,hit_values,hit_strength,defender_state,rng)
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
    offhand = attacker.off_hand_attacks and attacker.off_hand is not None
    main_pistol = any(has(attacker.main_weapon, tag) for tag in ('weapon.pistol', 'weapon.duelling-pistol'))
    off_pistol = bool(attacker.off_hand and any(has(attacker.off_hand, tag) for tag in ('weapon.pistol', 'weapon.duelling-pistol')))
    off_counts = np.where(attacks > 1, 1, 0) if offhand else np.zeros_like(attacks)
    if main_pistol and offhand:
        off_counts = np.maximum(0, attacks - 1) if first_round else attacks.copy()
    if off_pistol and not first_round:
        off_counts[:] = 0
    main_counts = attacks - off_counts
    if (offhand and attacker.main_weapon != attacker.off_hand and not main_pistol and not off_pistol
            and (attacks[rows] > 2).any() and decisions is not None
            and not decisions.choose(f"{decision_prefix + '.' if decision_prefix else ''}main-weapon-majority", attacker)):
        main_counts, off_counts = off_counts, main_counts
    original_main, original_off = main_counts.copy(), off_counts.copy()
    main_penalty = np.where(attacker_state.hampered_main + attacker_state.hampered_off > 0,
                            attacker_state.hampered_main, attacker_state.attack_penalty)
    main_counts = np.maximum(0, main_counts - main_penalty)
    off_counts = np.maximum(0, off_counts - attacker_state.hampered_off)
    minimum = (main_counts + off_counts == 0) & (attacks > 0)
    main_counts[minimum & (original_main > 0)] = 1
    off_counts[minimum & (original_main == 0) & (original_off > 0)] = 1
    for index in range(maximum):
        active = rows[(main_counts[rows] + off_counts[rows] > index) & (defender_state.condition[rows] != OUT)]
        if active.size == 0:
            continue
        use_off = index >= main_counts[active]
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
    two_parries = _parry_capacity(defender) == 2
    second_roll = np.full(charging.size,-1,dtype=np.int8) if two_parries else None
    second_owner = np.full(charging.size,-1,dtype=np.int32) if two_parries else None
    selected = [np.zeros(0,dtype=np.int64) for _ in prepared_attacks]
    owner = np.full(charging.size,-1,dtype=np.int32)
    positions_by_attack: list[np.ndarray] = []
    can_parry_six = has(defender.global_effects, "rule.blood-dragon-sword-master")
    for attack_index,prepared in enumerate(prepared_attacks):
        positions=np.searchsorted(prepared.active,prepared.hit_rows)
        positions_by_attack.append(positions)
        values=prepared.rolls[positions]
        if not can_parry_six and not two_parries:
            defender_state.parry_remaining[prepared.hit_rows[values == 6]] = 0
        competing=np.where(
            ((values != 6) | can_parry_six)
            & (not prepared.effect.cannot_be_parried)
            & (prepared.strength[positions] < 2 * defender_state.strength[prepared.hit_rows]),
            values, -1,
        )
        better=competing>best_roll[prepared.hit_rows]
        if two_parries:
            replaced_rows=prepared.hit_rows[better]
            second_roll[replaced_rows]=best_roll[replaced_rows]
            second_owner[replaced_rows]=owner[replaced_rows]
            between=(~better) & (competing>second_roll[prepared.hit_rows])
            second_rows=prepared.hit_rows[between]
            second_roll[second_rows]=competing[between]
            second_owner[second_rows]=attack_index
        chosen=prepared.hit_rows[better]
        best_roll[chosen]=competing[better]
        owner[chosen]=attack_index
    for attack_index in range(len(prepared_attacks)):
        selected[attack_index] = (
            np.flatnonzero((owner==attack_index) | (second_owner==attack_index))
            if two_parries else np.flatnonzero(owner==attack_index)
        )
    defences_resolved=False
    replaced_attack_indices: set[int] = set()
    if attacker.global_effects.bear_hug and prepared_attacks:
        # Bear Hug depends on two surviving hits across separate attacks.  Move
        # the hit/parry boundary ahead of wound resolution, aggregate those
        # hits, then replace exactly one pair with the opposed Strength test.
        defended=[]
        for prepared,parry_rows in zip(prepared_attacks,selected):
            surviving,_=_apply_hit_defences(
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
        # Earlier attacks by this same warrior cannot create an automatic
        # finisher. Wound resolution keeps the phase-start condition snapshot.
        observation = VectorAttackObservation() if observations is not None else None
        _resolve_weapon(attacker,defender,prepared.weapon,prepared.active,charging,
                        attacker_state,defender_state,rng,first_round,
                        prepared=prepared,parry_rows=parry_rows,
                        defender_phase_condition=defender_phase_condition,
                        decisions=decisions,
                        defences_resolved=defences_resolved,
                        hit_positions=positions_by_attack[attack_index]
                        if attack_index < len(positions_by_attack) else None,
                        observation=observation)
        if (observations is not None and observation is not None
                and attack_index not in replaced_attack_indices):
            observations.append(observation)
