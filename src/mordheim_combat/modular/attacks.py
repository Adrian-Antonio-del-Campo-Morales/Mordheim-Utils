"""combat.modular.attacks: responsibility extracted without altering the rules."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import replace
from mordheim_combat.phases import _characteristic_test
from mordheim_combat.modular.contexts import _attack_strength
from mordheim_combat.modular.contexts import _combined_effect
from mordheim_combat.modular.contexts import _hit_reroll
from mordheim_combat.modular.contexts import _injury_context
from mordheim_combat.modular.contexts import _parry_context
from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.contexts import prepare_hit_context
from mordheim_combat.modular.contexts import prepare_special_save_context
from mordheim_combat.modular.contexts import prepare_wound_context
from mordheim_combat.modular.contexts import weapon_against_opponent
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import FighterState
from mordheim_combat.phases import BearHugContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import has_tag
from mordheim_combat.phases import resolve_armour
from mordheim_combat.phases import resolve_bear_hug
from mordheim_combat.phases import resolve_hit
from mordheim_combat.phases import resolve_injury
from mordheim_combat.phases import resolve_parry
from mordheim_combat.phases import resolve_special_save
from mordheim_combat.phases import resolve_wound
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


def resolve_reference_attack(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, dice: DiceSource, *, key: str,
    first_round: bool = False, charging: bool = False,
    helpless_at_start: bool = False,
    hit_only: bool = False,
    prepared_hit: object | None = None,
    defences_resolved: bool = False,
    defences_only: bool = False,
    parry_allowed: bool = True,
    decisions: DecisionPolicy | None = None,
) -> AttackOutcome:
    """Resolve one attack and return new immutable fighter states."""
    if not attacker_state.active or not defender_state.active:
        return AttackOutcome(attacker_state, defender_state)
    if defender_state.condition == Condition.STUNNED:
        return AttackOutcome(attacker_state, replace(defender_state, condition=Condition.OUT))
    weapon = weapon_against_opponent(attacker, defender, weapon)
    effect = _combined_effect(attacker, weapon)
    if phases.has_tag(effect, "mechanic.death-blow") and attacker.characteristics.attacks < 2:
        effect = replace(
            effect,
            hit_modifier=effect.hit_modifier - 1,
            wound_modifier=effect.wound_modifier - 1,
            injury_modifier=effect.injury_modifier - 1,
        )
    strength, armour_strength = _attack_strength(
        attacker, defender, attacker_state, weapon, effect, first_round, charging
    )
    hit_context = prepare_hit_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        first_round=first_round, charging=charging,
        helpless_at_start=helpless_at_start, key=f"{key}.hit",
    )
    reroll = _hit_reroll(attacker, defender, weapon, effect, first_round, charging)
    luck_available = phases.has_tag(effect, "skill.luck") and "luck" not in attacker_state.resources_spent and not reroll
    if prepared_hit is not None:
        hit = prepared_hit
    elif phases.has_tag(effect, "skill.sweep") and weapon.two_handed:
        passed = phases._characteristic_test(
            defender_state.initiative, dice, f"{key}.sweep",
            reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"),
        )
        from mordheim_combat.phases import HitResult
        hit = HitResult(0, 1 if passed else 6, not passed)
    else:
        hit = phases.resolve_hit(hit_context, dice)
    trace = (Phase.HIT,)
    if luck_available and hit.rerolled:
        attacker_state = attacker_state.spend("luck")
    if not hit.success and phases.has_tag(attacker.global_effects, "mechanic.mark-of-the-old-ones") and "mark-of-the-old-ones" not in attacker_state.resources_spent:
        attacker_state = attacker_state.spend("mark-of-the-old-ones")
        hit = replace(hit, success=True, roll=hit.target)
    if not hit.success:
        if phases.has_tag(defender.global_effects, "mechanic.spider-infested"):
            attacker_state = replace(
                attacker_state,
                initiative_penalty=attacker_state.initiative_penalty + 1,
                initiative_floor=0,
            )
        return AttackOutcome(
            attacker_state, defender_state, hit_roll=hit.roll,
            hit_target=hit.target, trace=trace,
        )
    if hit_only:
        return AttackOutcome(
            attacker_state, defender_state, hit=True, hit_roll=hit.roll,
            hit_target=hit.target, trace=trace,
        )
    if not defences_resolved and defender_state.lucky_charm:
        charm = dice.roll(RollRequest(f"{key}.lucky-charm"))
        defender_state = replace(defender_state, lucky_charm=False)
        if charm >= 4:
            return AttackOutcome(attacker_state, defender_state, hit=True, hit_roll=hit.roll, saved=True, trace=trace)
    parry_context = None if defences_resolved or not parry_allowed else _parry_context(
        defender, defender_state, effect, strength, hit.roll, key
    )
    if parry_context is not None:
        parry = phases.resolve_parry(parry_context, dice)
        trace += (Phase.PARRY,)
        if parry.attempted:
            defender_state = replace(defender_state, parries_remaining=defender_state.parries_remaining - 1)
        if parry.blocked:
            if phases.has_tag(defender.global_effects, "mechanic.spider-infested"):
                attacker_state = replace(
                    attacker_state,
                    initiative_penalty=attacker_state.initiative_penalty + 1,
                    initiative_floor=0,
                )
            if (
                any(phases.has_tag(candidate, "weapon.cutlass") for candidate in (
                    defender.main_weapon, defender.off_hand or EffectSet()
                ))
                and not phases.has_tag(weapon, "effect.cutlass-counter")
            ):
                counter = EffectSet(tags=("effect.cutlass-counter",))
                reaction = resolve_reference_attack(
                    defender, attacker, defender_state, attacker_state, counter, dice,
                    key=f"{key}.cutlass-counter",
                )
                defender_state, attacker_state = reaction.attacker, reaction.defender
            return AttackOutcome(attacker_state, defender_state, hit=True, hit_roll=hit.roll, parried=True, trace=trace)
    if defences_only:
        return AttackOutcome(
            attacker_state, defender_state, hit=True, hit_roll=hit.roll,
            hit_target=hit.target, trace=trace,
        )
    # Bull Charge substitutes the wound step: an undefended hit is consumed by
    # the pool handler to knock the target down without a To Wound roll.
    if phases.has_tag(effect, "mechanic.bull-charge"):
        return AttackOutcome(
            attacker_state, defender_state, hit=True, hit_roll=hit.roll,
            hit_target=hit.target, trace=trace,
        )
    if phases.has_tag(weapon, "weapon.kusara-kama") and hit.roll >= 5:
        defender_state = replace(defender_state, attack_penalty=defender_state.attack_penalty + 1)
    if phases.has_tag(weapon, "weapon.chained-squig"):
        defender_state = replace(defender_state, entangled=True)
    ignition = (
        min(effect.ignition_threshold, defender.global_effects.caught_fire_threshold)
        if effect.ignition_threshold <= 6 else 7
    )
    if ignition <= 6 and dice.roll(RollRequest(f"{key}.ignition")) >= ignition:
        defender_state = replace(defender_state, on_fire=True)
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")
    wound = phases.resolve_wound(prepare_wound_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        hit_roll=hit.roll, first_round=first_round, charging=charging, key=f"{key}.wound",
    ), dice)
    trace += (Phase.WOUND,)
    if not wound.success and phases.has_tag(attacker.global_effects, "mechanic.mark-of-the-old-ones") and "mark-of-the-old-ones" not in attacker_state.resources_spent:
        attacker_state = attacker_state.spend("mark-of-the-old-ones")
        wound = replace(wound, success=True, roll=wound.target, critical=False)
    if not wound.success:
        if phases.has_tag(weapon, "weapon.rapier"):
            extra_target = min(6, hit.target + 1)
            extra_hit = dice.roll(RollRequest(f"{key}.rapier.hit")) >= extra_target
            extra_wound = extra_hit and dice.roll(RollRequest(f"{key}.rapier.wound")) >= wound.target
            if extra_hit and extra_wound:
                wound = replace(wound, success=True)
            else:
                return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace)
        else:
            return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace)
    if phases.has_tag(effect, "poison.manbane") and not poison_blocked and wound.roll == 1:
        return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace)
    if wound.critical:
        if phases.has_tag(defender.global_effects, "skill.hardy-constitution") and dice.roll(
            RollRequest(f"{key}.hardy-constitution")
        ) >= 5:
            wound = replace(wound, critical=False)
        else:
            attacker_state = replace(attacker_state, critical_available=False)
    armour = phases.resolve_armour(prepare_armour_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        first_round=first_round, charging=charging, key=f"{key}.armour",
    ), dice)
    trace += (Phase.ARMOUR,)
    if armour.saved:
        return AttackOutcome(attacker_state, defender_state, True, wounded=True, saved=True, critical=wound.critical, trace=trace)
    special = phases.resolve_special_save(prepare_special_save_context(
        defender, effect, key=f"{key}.special",
    ), dice)
    trace += (Phase.SPECIAL_SAVE,)
    if special.saved:
        return AttackOutcome(attacker_state, defender_state, True, wounded=True, saved=True, critical=wound.critical, trace=trace)
    if defender.injury_profile == 2 or helpless_at_start:
        return AttackOutcome(attacker_state, replace(defender_state, condition=Condition.OUT), True, wounded=True, damage=1, critical=wound.critical, trace=trace)
    damage = max(1, effect.damage) * (2 if phases.has_tag(defender.global_effects, "flammable") and phases.has_tag(effect, "attack.fire") else 1)
    remaining = defender_state.wounds - damage
    if phases.has_tag(effect, "poison.nightshade") and not poison_blocked:
        defender_state = replace(defender_state, initiative_penalty=defender_state.initiative_penalty + 1)
    if (
        phases.has_tag(effect, "poison.spider-spittle") and not poison_blocked
        and defender_state.condition == Condition.STANDING
        and not phases._characteristic_test(
            defender_state.toughness, dice, f"{key}.spider-spittle",
            reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"),
        )
    ):
        defender_state = replace(defender_state, condition=Condition.PARALYZED)
    if remaining > 0:
        defender_state = replace(defender_state, wounds=remaining)
        return AttackOutcome(attacker_state, defender_state, True, wounded=True, damage=damage, critical=wound.critical, trace=trace)
    if defender.injury_profile == 4:
        return AttackOutcome(
            attacker_state, replace(defender_state, wounds=remaining, condition=Condition.OUT),
            True, wounded=True, damage=damage, critical=wound.critical, trace=trace,
        )
    injury_context = _injury_context(defender, effect, key, defender_state)
    if wound.critical:
        injury_context = replace(
            injury_context,
            modifier=injury_context.modifier + 2
            + int(phases.has_tag(effect, "skill.web-of-steel"))
            + effect.critical_injury_bonus,
        )
    injury_count = max(1, damage - max(0, defender_state.wounds - 1))
    injuries = []
    for injury_index in range(injury_count):
        local = replace(injury_context, key=f"{key}.injury.{injury_index}")
        injury = phases.resolve_injury(local, dice)
        can_reroll = (
            phases.has_tag(defender.global_effects, "injury_reroll_out")
            and not phases.has_tag(effect, "attack.fire")
        )
        reroll = can_reroll and (
            decisions.choose(f"{key}.injury.{injury_index}.reroll-choice", injury)
            if decisions is not None else injury.condition == Condition.OUT
        )
        if reroll:
            injury = phases.resolve_injury(
                replace(local, key=f"{key}.injury.{injury_index}.reroll"), dice
            )
        injuries.append(injury)
    trace += (Phase.INJURY,)
    condition = max(injury.condition for injury in injuries)
    condition = phases.resolve_stun_reaction(phases.StunReactionContext(
        condition, defender.global_effects.thick_skull, defender.helmet_save, key
    ), dice).condition
    defender_state = replace(
        defender_state, wounds=remaining, condition=max(defender_state.condition, condition),
        frenzy=defender_state.frenzy and condition == Condition.STANDING,
    )
    return AttackOutcome(attacker_state, defender_state, True, wounded=True, damage=damage, critical=wound.critical, trace=trace)


