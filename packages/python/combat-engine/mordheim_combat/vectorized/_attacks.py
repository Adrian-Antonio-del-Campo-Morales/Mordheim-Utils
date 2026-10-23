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
from mordheim_combat.vectorized._types import CombatState, KNOCKED_DOWN, OUT, OptionalPhasePlan, PARALYZED, PreparedAttack, STANDING, STUNNED, VectorAttackObservation, _claim_criticals, _critical_wound_threshold, _has_weapon_tag, _run_starts, has
from mordheim_combat.vectorized._operators import _characteristic_test, armour_targets, attack_strength, hit_context, hit_reroll, hit_targets, injury_conditions, parry_capacity, parry_context, special_save_targets, wound_context, wound_targets

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

def _parry_offer_capacity(defender: CompiledFighter) -> int:
    """Parry attempts available in this phase.

    Delegates to G03's ``_operators.parry_capacity`` (the port of the modular
    ``state._parry_capacity``), which already reads the two skill grants this
    module used to add by hand.
    """
    return parry_capacity(defender)

def _parry_hits(defender: CompiledFighter, effect: EffectSet, hit_rows: np.ndarray,
                hit_values: np.ndarray, hit_strength: np.ndarray,
                defender_state: CombatState,
                rng: np.random.Generator,
                selected_rows: np.ndarray | None = None,
                *, attacker: CompiledFighter | None = None,
                attacker_state: CombatState | None = None,
                weapon: EffectSet | None = None,
                natural_values: np.ndarray | None = None,
                ) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    """Return (surviving rows, parried rows, survivor mask over the input rows).

    The survivor mask lets callers filter sibling arrays (e.g. positions within
    the active pool) without a second searchsorted over the whole pool.
    """
    if effect.cannot_be_parried or hit_rows.size == 0:
        return hit_rows,np.empty(0,dtype=np.int64),np.ones(hit_rows.size,dtype=bool)
    # Eligibility, match rules and reroll rights come from G03's operator (the
    # port of modular _parry_context): Estalian technique, Darting Steel,
    # Starblade, sword-and-buckler and the White Tower grant all live there.
    context = parry_context(
        defender, defender_state, effect, hit_strength, hit_values, hit_rows,
    )
    can_parry_six = context.can_parry_six
    # A granted success is not a natural six: the physical face decides both the
    # unparryable six and Killing Blow's automatic wound.
    natural = hit_values if natural_values is None else natural_values
    killing_blow = (natural == 6) & has(effect, "mechanic.killing-blow")
    # A natural six in the eligible pool prevents substituting a lower hit.
    if not can_parry_six and parry_capacity(defender) < 2:
        defender_state.parry_remaining[np.unique(hit_rows[natural == 6])] = 0
    eligible = (context.eligible
                # The natural-six clear above may have emptied the row after
                # the context snapshot was taken.
                & (defender_state.parry_remaining[hit_rows] > 0)
                & (hit_strength < 2 * defender_state.strength[hit_rows])
                & ((natural != 6) | can_parry_six)
                & ~killing_blow)
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

    def succeeds(values: np.ndarray, positions: np.ndarray) -> np.ndarray:
        """One parry die against the modular contract's success rule."""
        passed = np.ones(values.size, dtype=bool)
        if context.maximum_roll is not None:
            passed &= values <= context.maximum_roll[positions]
        if context.roll_under is not None:
            passed &= values < context.roll_under[positions]
        elif context.fixed_target is not None:
            passed &= values >= context.fixed_target
        elif context.match_allowed:
            passed &= values >= hit_values[positions]
        else:
            passed &= values > hit_values[positions]
        return passed

    positions = np.arange(hit_rows.size)
    blocked = eligible & succeeds(rng.integers(1, 7, hit_rows.size), positions)
    failed_positions = np.flatnonzero(
        eligible & ~blocked & np.asarray(context.reroll, dtype=bool),
    )
    if failed_positions.size:
        blocked[failed_positions] = succeeds(
            rng.integers(1, 7, failed_positions.size), failed_positions,
        )
    # Sword-breaker: a blocked blow is trapped on 4+, breaking the attacking
    # weapon's hand.  The break is per row and survives the attack, so the next
    # round's equipment projection can substitute the backup or the fist.
    held = effect if weapon is None else weapon
    if (attacker is not None and attacker_state is not None and blocked.any()
            and not has(effect, "weapon.indestructible")
            and any(tag.startswith("weapon.") and tag not in (
                "weapon.fist", "weapon.natural-attacks") for tag in held.tags)
            and any(has(candidate, "weapon.sword-breaker") for candidate in (
                defender.main_weapon, defender.off_hand or EffectSet()))):
        blocked_rows = hit_rows[blocked]
        trapped = blocked_rows[rng.integers(1, 7, blocked_rows.size) >= 4]
        # The trapped hand is the one that held the striking weapon: the main
        # hand only when its own weapon matches (modular trap-blade branch),
        # which keeps an off-hand strike from breaking the main hand.
        main_matches = any(
            tag in attacker.main_weapon.tags
            for tag in held.tags if tag.startswith("weapon.")
        )
        for row in trapped:
            mask = int(attacker_state.broken_hands[row])
            hand = 1 if not mask & 1 and main_matches else 2
            attacker_state.broken_hands[row] = mask | hand
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
    first_round: bool, *, melee_attack: bool = True,
    needs_sixes: np.ndarray | bool | None = None) -> PreparedAttack | None:
    if active.size == 0:
        return None
    weapon, effect, _ = _compiled_attack_effect(attacker, defender, weapon)
    if melee_attack:
        stunned = active[defender_state.condition[active] == STUNNED]
        defender_state.condition[stunned] = OUT
    active = active[defender_state.condition[active] != OUT]
    # Wraith Touch cannot touch the restless dead or the possessed: the whole
    # attack is void, before any die is drawn (modular resolve_reference_attack).
    if has(weapon, "effect.wraith-touch") and any(
            has(defender.global_effects, tag)
            for tag in ("nature.undead", "nature.possessed")):
        return None
    if melee_attack and has(attacker.global_effects, "mechanic.honorable"):
        # Each attack re-checks it: an earlier attack in the same pool may have
        # knocked the opponent down, and the bearer does not strike him then.
        active = active[defender_state.condition[active] == STANDING]
    if active.size == 0:
        return None
    charge_rows = charging[active]
    # Strength and the To Hit Context come from G03's operators: they are the
    # port of modular _attack_strength / prepare_hit_context, so every modifier
    # (Guiding Dream, hatred, knife fighting, seaguard, cold steel...) has one
    # definition and the resolution no longer keeps a second, partial copy.
    strength, armour_strength = attack_strength(
        attacker, defender, attacker_state, weapon, effect, active,
        first_round=first_round, charging=charge_rows, melee_attack=melee_attack,
    )
    context = hit_context(
        attacker, defender, attacker_state, defender_state, weapon, effect, active,
        first_round=first_round, charging=charge_rows, melee_attack=melee_attack,
        needs_sixes=needs_sixes,
    )
    hit_target = hit_targets(
        context.weapon_skill, context.defender_weapon_skill,
        modifier=context.modifier, fixed_target=context.fixed_target,
        needs_sixes=context.needs_sixes,
    )
    # A WS 0 defender is hit automatically (the modular target is 0); every
    # other target stays inside the printable 2..6 band.
    hit_target = np.where(
        (context.defender_weapon_skill == 0) & ~context.needs_sixes, 0,
        np.clip(hit_target, 2, 6),
    ).astype(np.int8)
    if has(effect,"skill.sweep") and weapon.two_handed:
        failed_tests = ~_characteristic_test(defender, defender_state.initiative[active], rng)
        rolls=np.where(failed_tests,6,1).astype(np.int8);successful=failed_tests
    else:
        helpless = np.isin(defender_state.condition[active], (KNOCKED_DOWN, PARALYZED))
        automatic = context.automatic | helpless
        rolls = np.zeros(active.size, dtype=np.int8)
        if (~automatic).any():
            rolls[~automatic] = rng.integers(1, 7, int((~automatic).sum()), dtype=np.int8)
        successful = automatic | (rolls >= hit_target)
    # The physical face is kept before any granted success rewrites the roll:
    # Killing Blow, Black Lotus, Wight Blades and Onslaught read this value.
    natural = rolls.copy()
    # ``context.reroll`` already folds the Luck skill in; call the shared helper
    # once more to mark which rows actually spent Luck.
    luck = None
    if has(effect, "skill.luck"):
        luck = (~attacker_state.luck_used[active] & ~hit_reroll(
            attacker, defender, weapon, effect, active,
            first_round=first_round, charging=charge_rows,
            frenzy=attacker_state.frenzy[active],
        ))
    reroll = context.reroll
    rerolled = np.zeros(active.size, dtype=bool)
    failed = np.flatnonzero(reroll & ~successful)
    if failed.size:
        rerolled[failed] = True
        rerolls = rng.integers(1, 7, failed.size)
        successful[failed] = rerolls >= hit_target[failed]
        rolls[failed] = rerolls
        natural[failed] = rerolls
        if luck is not None:
            luck_failed = failed[luck[failed]]
            attacker_state.luck_used[active[luck_failed]] = True
    # Seaguard Spear Master: one failed hit in the opening round is rerolled,
    # spending the phase resource; each simulation row may spend its own.  A die
    # Hatred (or Luck) already rerolled is never repeated: modular keeps
    # ``hit.rerolled`` and the spear's clause reads ``not hit.rerolled``.
    if (first_round and has(weapon, "weapon.spear")
            and has(effect, "mechanic.seaguard-spear-master")):
        misses = np.flatnonzero(
            ~successful & ~rerolled & ~attacker_state.seaguard_used[active])
        if misses.size:
            first_misses = misses[_run_starts(active[misses])]
            dies = rng.integers(1, 7, first_misses.size)
            successful[first_misses] = dies >= hit_target[first_misses]
            rolls[first_misses] = dies
            natural[first_misses] = dies
            rerolled[first_misses] = True
            attacker_state.seaguard_used[active[first_misses]] = True
    # Corruption: the defender forces one successful hit against it to be
    # rerolled, once per phase and unless the attacker is immune to psychology.
    # The same clause reads ``not hit.rerolled``: a hit already rerolled by
    # Hatred or Luck is not repeated.
    if (has(defender.global_effects, "mechanic.corruption")
            and not has(attacker.global_effects, "mechanic.psychology-immunity")):
        hits = np.flatnonzero(
            successful & ~rerolled & ~defender_state.corruption_used[active])
        if hits.size:
            first_hits = hits[_run_starts(active[hits])]
            dies = rng.integers(1, 7, first_hits.size)
            successful[first_hits] = dies >= hit_target[first_hits]
            rolls[first_hits] = dies
            natural[first_hits] = dies
            rerolled[first_hits] = True
            defender_state.corruption_used[active[first_hits]] = True
    if has(attacker.global_effects,"mechanic.mark-of-the-old-ones"):
        available=(~successful)&(~attacker_state.mark_of_old_ones_used[active])
        chosen=np.flatnonzero(available)
        if chosen.size:
            # Each duel row represents one independent warrior, so each may
            # convert its first failed roll once per battle.  ``natural`` keeps
            # the physical die, so the grant is not read as a natural six.
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
        rolls, hit_rows, rerolled, natural,
    )

def _apply_hit_defences(
    attacker: CompiledFighter, defender: CompiledFighter, prepared: PreparedAttack,
    attacker_state: CombatState, defender_state: CombatState,
    rng: np.random.Generator, charging: np.ndarray,
    parry_rows: np.ndarray | None = None,
    hit_positions: np.ndarray | None = None,
    *, saved_rows: np.ndarray | None = None,
) -> np.ndarray:
    """Resolve the hit-to-parry boundary once and return surviving hits.

    ``saved_rows`` is an optional whole-batch mask the caller can pass to learn
    which rows an ethereal hit save intercepted (the replay observation needs
    the saved hit, not just its removal).
    """
    weapon,effect,active,strength,rolls = (
        prepared.weapon,prepared.effect,prepared.active,prepared.strength,prepared.rolls
    )
    hit_rows=prepared.hit_rows[defender_state.condition[prepared.hit_rows]!=OUT]
    if hit_positions is None:
        hit_positions=np.searchsorted(active,hit_rows)
    else:
        hit_positions=hit_positions[defender_state.condition[prepared.hit_rows]!=OUT]
    hit_values=rolls[hit_positions]
    natural_values=(prepared.natural[hit_positions]
                    if prepared.natural is not None else hit_values)
    # Ethereal models duck an ordinary hit on their printed save; a magical
    # attack bypasses it (modular _resolve_reference_attack_once).  The save is
    # resolved before the parry boundary, so it consumes no parry capacity.
    if (hit_rows.size and has(defender.global_effects, "mechanic.ethereal-hit-save")
            and not has(effect, "attack.magical")):
        passed = rng.integers(1, 7, hit_rows.size) >= defender.global_effects.ethereal_hit_save
        if saved_rows is not None and passed.any():
            saved_rows[hit_rows[passed]] = True
        hit_rows = hit_rows[~passed]
        hit_positions = hit_positions[~passed]
        hit_values = hit_values[~passed]
        natural_values = natural_values[~passed]
    hit_rows,parried_rows,survived=_parry_hits(
        defender,effect,hit_rows,hit_values,strength[hit_positions],defender_state,rng,parry_rows,
        attacker=attacker, attacker_state=attacker_state, weapon=weapon,
        natural_values=natural_values,
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
                    key: str = "test", melee_attack: bool = True,
                    needs_sixes: np.ndarray | bool | None = None) -> None:
    prepared = prepared or _prepare_weapon_attack(attacker,defender,weapon,active,charging,attacker_state,defender_state,rng,first_round,
        melee_attack=melee_attack, needs_sixes=needs_sixes)
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
        ethereal_saved = np.zeros(attacker_state.wounds.size, dtype=bool)
        hit_rows, hit_positions = _apply_hit_defences(
            attacker,defender,prepared,attacker_state,defender_state,rng,charging,parry_rows,
            hit_positions, saved_rows=ethereal_saved,
        )
        if observation is not None and prepared.hit_rows.size and hit_rows.size == 0:
            row = int(prepared.hit_rows[0])
            observation.parried = defender_state.parry_remaining[row] < parries_before[row]
            observation.saved = bool(ethereal_saved[row]) or bool(
                charms_before[row] and not defender_state.lucky_charm[row]
                and not observation.parried)
    if hit_rows.size == 0:
        return
    if defences_resolved:
        hit_positions = np.searchsorted(active, hit_rows)
    hit_values = rolls[hit_positions]
    natural_values = (prepared.natural[hit_positions]
                      if prepared.natural is not None else hit_values)
    # Spectral Touch: a natural six resolves one extra wound of the same attack
    # through the ordinary saves, without a fresh hit, poison or critical
    # trigger (modular resolve_reference_attack).  It is resolved before the
    # attack's own To Wound step, exactly as the modular engine orders it.
    if hit_values.size and has(effect, "trait.spectral-touch"):
        spectral_rows = hit_rows[natural_values == 6]
        if spectral_rows.size:
            # No new To Hit die is rolled: the extra wound belongs to the hit
            # already established, so it cannot be a fresh attack.
            spectral = replace(
                effect,
                tags=(*effect.tags, "effect.automatic-wound", "effect.no-critical"),
                damage=1, damage_die_sides=0,
                automatic_hit=True, cannot_be_parried=True,
            )
            prepared_spectral = _prepare_weapon_attack(
                attacker, defender, spectral, spectral_rows, charging,
                attacker_state, defender_state, rng, first_round,
                melee_attack=melee_attack,
            )
            if prepared_spectral is not None:
                _resolve_weapon(
                    attacker, defender, spectral, spectral_rows, charging,
                    attacker_state, defender_state, rng, first_round,
                    prepared=prepared_spectral, defences_resolved=True,
                    melee_attack=melee_attack,
                )
                alive = ((defender_state.condition[hit_rows] != OUT)
                         & (attacker_state.condition[hit_rows] != OUT))
                hit_rows = hit_rows[alive]
                hit_positions = hit_positions[alive]
                hit_values = hit_values[alive]
                if hit_rows.size == 0:
                    return
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
    # The wound contract comes from G03's operator (the port of modular
    # prepare_wound_context): strength, toughness, armour-piercing modifier,
    # automatic wounds, reroll rights, critical thresholds, Cold Steel and the
    # clauses that wound anyway.  This layer only draws dice and applies the
    # outcome, instead of keeping a second partial calculation.
    wound = wound_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        hit_rows, hit_roll=natural_values, first_round=first_round,
        charging=charging[hit_rows], melee_attack=melee_attack,
    )
    if wound.unharmed.any():
        # Cold Steel: the attack cannot harm the bearer at all, so it consumes
        # no wound die and produces no wound or critical (modular resolve_wound).
        keep = ~wound.unharmed
        hit_rows, hit_positions = hit_rows[keep], hit_positions[keep]
        hit_values, natural_values = hit_values[keep], natural_values[keep]
        wound = replace(
            wound,
            strength=wound.strength[keep], toughness=wound.toughness[keep],
            modifier=wound.modifier[keep], automatic=wound.automatic[keep],
            reroll=wound.reroll[keep], critical_threshold=wound.critical_threshold[keep],
            critical_available=wound.critical_available[keep],
            critical_on_reroll=wound.critical_on_reroll[keep],
            critical_when_needing_six=wound.critical_when_needing_six[keep],
            failure_still_wounds=wound.failure_still_wounds[keep],
            unharmed=wound.unharmed[keep],
        )
        if hit_rows.size == 0:
            return
    strength_hits = wound.strength
    armour_strength_hits = armour_strength[hit_positions]
    targets = np.maximum(
        2, wound_targets(strength_hits, wound.toughness, wound.maximum_target) - wound.modifier,
    )
    # Killing Blow: a natural six on the To Hit roll wounds automatically (no
    # To Wound die, so no critical is invented) and cannot be parried; the
    # parry exclusion lives in ``_parry_hits``.
    killing_blow = (natural_values == 6) & has(effect, "mechanic.killing-blow")
    automatic_wound = wound.automatic | killing_blow
    guaranteed_wound = wound.failure_still_wounds
    if has(effect, "poison.black-lotus") and not poison_blocked and decisions is not None:
        for position in np.flatnonzero(guaranteed_wound):
            if not decisions.choose(f"{key}.lotus-critical", int(hit_rows[position])):
                automatic_wound[position] = True
    # Automatic wounds (e.g. a won bear hug) roll no die: the modular oracle
    # returns roll=0 for them, so drawing one here would shift every later
    # roll (special saves, injury) and diverge from the oracle.
    wound_rolls = np.zeros(hit_rows.size, dtype=np.int8)
    if (~automatic_wound).any():
        wound_rolls[~automatic_wound] = rng.integers(1, 7, int((~automatic_wound).sum()))
    critical_rolls = wound_rolls.copy()
    rolled_success = (~automatic_wound) & (wound_rolls >= targets)
    wounded = automatic_wound | guaranteed_wound | rolled_success
    if has(effect, "poison.manbane") and not poison_blocked:
        wounded &= wound_rolls != 1
        rolled_success &= wound_rolls != 1
    luck = None
    if has(effect, "skill.luck"):
        luck = (~attacker_state.luck_used[hit_rows] & ~bool(effect.reroll_wounds))
    reroll_failed = (~automatic_wound) & (wound_rolls < targets) & wound.reroll
    if reroll_failed.any():
        failed = np.flatnonzero(reroll_failed)
        rerolls = rng.integers(1, 7, failed.size)
        wound_rolls[failed] = rerolls
        rolled_success[failed] = rerolls >= targets[failed]
        wounded[failed] = rolled_success[failed]
        if luck is not None:
            spent = failed[luck[failed]]
            if spent.size:
                attacker_state.luck_used[hit_rows[spent]] = True
        critical_rolls[failed] = np.where(
            wound.critical_on_reroll[failed], rerolls, critical_rolls[failed],
        )
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
    # The Liche's Wraith Touch restores one wound on a landed strike, capped at
    # the printed profile (modular resolve_reference_attack).
    if (wound_rows.size and has(weapon, "effect.wraith-touch")
            and attacker.fighter_id == "restless-dead:liche" and decisions is not None):
        for row in wound_rows[attacker_state.wounds[wound_rows]
                               < attacker.characteristics.wounds]:
            if decisions.choose(f"{key}.wraith-heal", attacker):
                attacker_state.wounds[row] += 1
    # Titanic Strength: a melee blow that fails to wound still knocks a still
    # standing opponent down unless it passes a Strength test (modular
    # _resolve_reference_attack_body).
    if melee_attack and has(attacker.global_effects, "mechanic.titanic-strength"):
        standing = hit_rows[~wounded][defender_state.condition[hit_rows[~wounded]] == STANDING]
        if standing.size:
            knocked = standing[~_characteristic_test(
                defender, defender_state.strength[standing], rng,
            )]
            defender_state.condition[knocked] = KNOCKED_DOWN
            defender_state.frenzy[knocked] &= has(
                defender.global_effects, "mechanic.persistent-frenzy",
            )
    if wound_rows.size == 0:
        return
    wound_strength = armour_strength_hits[wounded].copy()
    if has(effect,"skill.monster-slayer-effective-strength-armour"):
        raw_targets = wound_targets(strength_hits, wound.toughness, effect.maximum_wound_target)
        boosted = raw_targets[wounded] > 4
        wound_strength[boosted] = np.maximum(
            wound_strength[boosted], wound.toughness[wounded][boosted],
        )
    critical_candidates = (
        rolled_success[wounded]
        & wound.critical_available[wounded]
        & ((targets[wounded] < 6) | wound.critical_when_needing_six[wounded])
        & (critical_rolls[wounded] >= wound.critical_threshold[wounded])
    )
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
    # Eshin Assassin robes: the printed sixth-save sentence rerolls every failed
    # armour save once, and the second result stands.  It replaces, rather than
    # consumes, the Luck skill's once-per-battle reroll (modular
    # _resolve_wound_damage_body).
    if has(defender.global_effects, "armour.eshin-assassin-robes"):
        rerolled = eligible & ~saved
        if rerolled.any():
            rerolls = rng.integers(1, 7, int(rerolled.sum()))
            saved[rerolled] = rerolls >= np.maximum(2, save_target[rerolled])
    elif has(defender.global_effects, "skill.luck"):
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
    # Marine Hunter: every wound it inflicts on an aquatic creature is doubled.
    if (has(attacker.global_effects, "mechanic.marine-hunter")
            and has(defender.global_effects, "species.aquatic")):
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
    # Torturer: a close-combat wound weakens its victim by one Strength until
    # the end of the duel, once per wounding attack (modular _react_to_wound).
    if (melee_attack and has(attacker.global_effects, "mechanic.torturer")
            and not has(defender.global_effects, "nature.undead")):
        defender_state.torture_strength_loss[affected_rows] += 1
        defender_state.strength[affected_rows] = np.maximum(
            1, defender_state.strength[affected_rows] - 1,
        )
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
    # Hard to Rattle improves the helmet reaction to 4+ (fire is excluded); a
    # Skull Busta worsens a helmet (not Thick Skull) to 6+.
    helmet_save = defender.helmet_save
    if (has(defender.global_effects, "mechanic.hard-to-rattle")
            and not has(effect, "attack.fire")):
        helmet_save = min(helmet_save, 4)
    if (has(effect, "weapon.skull-busta") and helmet_save <= 6
            and not defender.global_effects.thick_skull):
        helmet_save = 6
    if stunned.any() and (defender.global_effects.thick_skull or helmet_save <= 6):
        threshold_roll = ((2 if helmet_save <= 4 else 3)
                          if defender.global_effects.thick_skull else helmet_save)
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
                    decision_prefix: str = "",
                    needs_sixes: np.ndarray | None = None,
                    forfeits: np.ndarray | None = None,
                    extra_forfeits: np.ndarray | None = None) -> None:
    if rows.size == 0:
        return
    # Fear's mask is a per-round state fact, exactly as the modular
    # ``FighterState.fear_hit_sixes`` is.  A caller that carries the mask
    # separately hands it over here, so every prepared attack reads the same
    # column through ``hit_context(needs_sixes=...)``.
    if needs_sixes is not None:
        attacker_state.fear_hit_sixes[:] = np.broadcast_to(
            np.asarray(needs_sixes, dtype=bool), attacker_state.wounds.shape)
    # Honorable: the bearer does not strike a Knocked Down or Stunned opponent
    # (modular _resolve_attack_pool skips the whole pool).  Filtered per row,
    # because a batch mixes the two conditions.
    if has(attacker.global_effects, "mechanic.honorable"):
        rows = rows[defender_state.condition[rows] == STANDING]
        if rows.size == 0:
            return
    # Seed the parry a skill grants at the pool boundary: the round driver seeds
    # ``parry_remaining`` from ``_types._parry_capacity``, which does not read
    # Chosen of the White Tower or Instinctive Warrior.  ``parry_used`` marks the
    # grant, so a second pool in the same round (whipcrack, entangle) cannot
    # replenish parries the first pool already spent; the driver clears it with
    # ``parry_remaining`` at the start of every round.
    offered_parries = _parry_offer_capacity(defender)
    if offered_parries:
        fresh = ((defender_state.parry_remaining[rows] <= 0)
                 & ~defender_state.parry_used[rows])
        if fresh.any():
            defender_state.parry_remaining[rows[fresh]] = offered_parries
            defender_state.parry_used[rows[fresh]] = True
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
            natural_values=(prepared.natural[hit_positions]
                            if prepared.natural is not None else hit_values)
            hit_strength=prepared.strength[hit_positions]
            if (hit_rows.size and has(defender.global_effects,"mechanic.ethereal-hit-save")
                    and not has(prepared.effect,"attack.magical")):
                passed=rng.integers(1,7,hit_rows.size)>=defender.global_effects.ethereal_hit_save
                if observation is not None and passed.any():
                    observation.saved=True
                hit_rows=hit_rows[~passed]
                hit_positions=hit_positions[~passed]
                hit_values=hit_values[~passed]
                natural_values=natural_values[~passed]
                hit_strength=hit_strength[~passed]
            hit_rows,_,_=_parry_hits(defender,prepared.effect,hit_rows,hit_values,hit_strength,defender_state,rng,
                attacker=attacker,attacker_state=attacker_state,weapon=prepared.weapon,
                natural_values=natural_values)
            if observation is not None and prepared.hit_rows.size and hit_rows.size == 0:
                row=int(prepared.hit_rows[0])
                observation.parried=defender_state.parry_remaining[row] < parries_before[row]
            if hit_rows.size:
                charm=defender_state.lucky_charm[hit_rows]
                if charm.any():
                    rolls=rng.integers(1,7,hit_rows.size)
                    defender_state.lucky_charm[hit_rows[charm]]=False
                    hit_rows=hit_rows[~(charm&(rolls>=4))]
                # Bull Charge substitutes the wound step: an undefended hit is
                # consumed by the knockdown, but the target's armour save can
                # still stop it (modular _resolve_reference_attack_body).
                positions=np.searchsorted(prepared.active,hit_rows)
                save_target=armour_targets(
                    defender,prepared.strength[positions],prepared.effect,
                    has(prepared.effect,"attack.magical"),
                )
                save_eligible=save_target<=6
                saved=np.zeros(hit_rows.size,dtype=bool)
                if save_eligible.any():
                    saved[save_eligible]=rng.integers(1,7,int(save_eligible.sum()))>=np.maximum(
                        2,save_target[save_eligible])
                if observation is not None and saved.any():
                    observation.saved=True
                hit_rows=hit_rows[~saved]
                standing=hit_rows[defender_state.condition[hit_rows]==STANDING]
                defender_state.condition[standing]=KNOCKED_DOWN
                defender_state.frenzy[standing]&=has(
                    defender.global_effects,"mechanic.persistent-frenzy")
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
    # A nominated attack loss (Tentacle Grapple) removes that exact allocation
    # position, so the remainder keeps the weapons it was assigned.
    if forfeits is None:
        forfeits = np.full(attacker_state.wounds.size, -1, dtype=np.int16)
    if extra_forfeits is None:
        extra_forfeits = np.full(attacker_state.wounds.size, -1, dtype=np.int16)
    for index in range(maximum):
        active = rows[(main_counts[rows] + off_counts[rows] > index)
                      & (defender_state.condition[rows] != OUT)
                      & (forfeits[rows] != index)]
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
    vomit_weapon = any(has(attacker.main_weapon, tag)
                       for tag in ("weapon.vomit-attack", "effect.wraith-touch"))
    for extra_index, weapon in enumerate(attacker.extra_attacks):
        # ``pool_attack_weapons`` leaves these two to their own events and
        # drops every independent contribution behind a whole-pool replacement.
        if vomit_weapon or any(has(weapon, tag) for tag in
                               ("rule.strikes-last-bite", "rule.eagle-friend")):
            continue
        if has(weapon, "rule.horned-one") and not charging[rows].any():
            continue
        # Tentacle Grapple removes the nominated allocation from this exact
        # position, so the remaining extras keep the order the pool printed.
        extra_rows = rows[extra_forfeits[rows] != extra_index]
        if extra_rows.size == 0:
            continue
        extra = _prepare_weapon_attack(attacker, defender, weapon, extra_rows, charging, attacker_state, defender_state, rng, first_round)
        if extra is not None: prepared_attacks.append(extra)
    if has(attacker.global_effects, "mechanic.ravening-onslaught"):
        # A natural six earns one more attack with the same weapon, and that
        # attack may earn another in turn (modular grows its pending pool the
        # same way).  Only rows that hit on a natural six are offered the extra.
        index = 0
        while index < len(prepared_attacks):
            prepared = prepared_attacks[index]
            positions = np.searchsorted(prepared.active, prepared.hit_rows)
            sixes = positions[(prepared.natural[positions] if prepared.natural is not None
                           else prepared.rolls[positions]) == 6]
            if sixes.size:
                repeat = _prepare_weapon_attack(
                    attacker, defender, prepared.weapon, prepared.active[sixes],
                    charging, attacker_state, defender_state, rng, first_round,
                )
                if repeat is not None:
                    prepared_attacks.append(repeat)
            index += 1
    best_roll = np.full(charging.size,-1,dtype=np.int8)
    two_parries = _parry_offer_capacity(defender) == 2
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
        natural=(prepared.natural[positions]
                 if prepared.natural is not None else values)
        if not can_parry_six and not two_parries:
            defender_state.parry_remaining[prepared.hit_rows[natural == 6]] = 0
        competing=np.where(
            ((natural != 6) | can_parry_six)
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
