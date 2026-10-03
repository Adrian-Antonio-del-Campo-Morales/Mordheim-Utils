"""combat: Per-round state machine of the modular engine."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import replace
from mordheim_combat.modular.aftermath import _black_hunger
from mordheim_combat.modular.aftermath import _characteristic_test
from mordheim_combat.modular.aftermath import _fire_recovery
from mordheim_combat.modular.aftermath import _force_of_will
from mordheim_combat.modular.aftermath import _netter
from mordheim_combat.modular.aftermath import _spines
from mordheim_combat.modular.aftermath import _start_round_state
from mordheim_combat.modular.state import _refresh_random_characteristics
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import CombatRoundResult
from mordheim_combat.modular.state import DuelState
from mordheim_combat.modular.equipment import equipment_for_state, is_pistol, whipcrack_weapon
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import Phase
from mordheim_combat.phases import PriorityContext
from mordheim_combat.phases import build_attacks
from mordheim_combat.phases import first_acts_before
from mordheim_combat.phases import has_tag
from mordheim_combat.phases import resolve_priority
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import DecisionPolicy
from mordheim_core.dice import DiceSource
from mordheim_core.dice import RollRequest
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


def resolve_round(
    first: CompiledFighter, second: CompiledFighter, state: DuelState,
    dice: DiceSource, decisions: DecisionPolicy | None = None,
) -> CombatRoundResult:
    """Resolve one complete scalar round through the fixed phase pipeline."""
    decisions = decisions or AlwaysAccept()
    first_state, second_state = state.first, state.second
    original_first, original_second = first, second
    outcomes: list[AttackOutcome] = []
    first_round = state.round_index == 0
    if not first_round:
        first_state = _refresh_random_characteristics(
            first, first_state, dice, f"round.{state.round_index}.first"
        )
        second_state = _refresh_random_characteristics(
            second, second_state, dice, f"round.{state.round_index}.second"
        )
    first = equipment_for_state(first, first_state, first_round=first_round)
    second = equipment_for_state(second, second_state, first_round=first_round)
    if not first_round:
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force", sustain=True)
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force", sustain=True)
        if state.first_player_turn:
            first_state, second_state, fire = _fire_recovery(
                first, second, first_state, second_state, dice, f"round.{state.round_index}.first.fire")
        else:
            second_state, first_state, fire = _fire_recovery(
                second, first, second_state, first_state, dice, f"round.{state.round_index}.second.fire")
        outcomes.extend(fire)
    if state.first_player_turn and first_state.condition == Condition.PARALYZED and _characteristic_test(
        first_state.toughness, dice, f"round.{state.round_index}.first.paralysis",
        reroll=phases.has_tag(first.global_effects, "skill.blessed-sight"),
    ):
        first_state = replace(first_state, condition=Condition.STANDING)
    if not state.first_player_turn and second_state.condition == Condition.PARALYZED and _characteristic_test(
        second_state.toughness, dice, f"round.{state.round_index}.second.paralysis",
        reroll=phases.has_tag(second.global_effects, "skill.blessed-sight"),
    ):
        second_state = replace(second_state, condition=Condition.STANDING)
    first_state, first_stood = _start_round_state(first, first_state, recover=state.first_player_turn)
    second_state, second_stood = _start_round_state(second, second_state, recover=not state.first_player_turn)
    first_charged, second_charged = state.initial_charge_flags
    first_charging = first_round and first_charged
    second_charging = first_round and second_charged
    if first_charging:
        second_state = _netter(first, second, first_state, second_state, dice, "round.0.first.netter")
    if second_charging:
        first_state = _netter(second, first, second_state, first_state, dice, "round.0.second.netter")
    # Resolve both Spines attacks from one snapshot.  A simultaneous mutation
    # still retaliates when the opposing Spines hit takes it out of action.
    before_first, before_second = first_state, second_state
    _, second_state, first_spines = _spines(
        first, second, before_first, before_second, dice,
        f"round.{state.round_index}.first.spines",
    )
    _, first_state, second_spines = _spines(
        second, first, before_second, before_first, dice,
        f"round.{state.round_index}.second.spines",
    )
    outcomes.extend((*first_spines, *second_spines))
    entangle = EffectSet(
        tags=("effect.chained-squig-entangle",), fixed_strength=3,
        automatic_hit=True,
    )
    if first_state.entangled and second_state.condition == Condition.STANDING:
        result = resolve_reference_attack(
            second, first, second_state, first_state, entangle, dice,
            key=f"round.{state.round_index}.first.entangled",
        )
        second_state, first_state = result.attacker, result.defender
        outcomes.append(result)
    if second_state.entangled and first_state.condition == Condition.STANDING:
        result = resolve_reference_attack(
            first, second, first_state, second_state, entangle, dice,
            key=f"round.{state.round_index}.second.entangled",
        )
        first_state, second_state = result.attacker, result.defender
        outcomes.append(result)
    first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force.after-spines")
    second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force.after-spines")

    first_attack_fighter = select_attack_replacement(
        first, first_round=first_round, charging=first_charging,
        decisions=decisions, key=f"round.{state.round_index}.first",
    )
    second_attack_fighter = select_attack_replacement(
        second, first_round=first_round, charging=second_charging,
        decisions=decisions, key=f"round.{state.round_index}.second",
    )
    if has_tag(first_attack_fighter.main_weapon, "effect.serpent-staff-power"):
        first_state = replace(first_state, parries_remaining=0)
    if has_tag(second_attack_fighter.main_weapon, "effect.serpent-staff-power"):
        second_state = replace(second_state, parries_remaining=0)
    first_priority = phases.resolve_priority(PriorityContext(
        first_attack_fighter, second, first_round, first_charging, second_charging, first_stood,
        first_state.initiative_penalty,
        initiative_bonus=first_state.initiative - first.characteristics.initiative,
        initiative_floor=first_state.initiative_floor,
    ))
    second_priority = phases.resolve_priority(PriorityContext(
        second_attack_fighter, first, first_round, second_charging, first_charging, second_stood,
        second_state.initiative_penalty,
        initiative_bonus=second_state.initiative - second.characteristics.initiative,
        initiative_floor=second_state.initiative_floor,
    ))
    first_acts = phases.first_acts_before(
        first_priority, second_priority, dice, key=f"round.{state.round_index}.priority-tie",
    )

    first_count = phases.build_attacks(AttackPoolContext(
        first_attack_fighter, first_round, first_charging, second_charging,
        first_state.frenzy, first_state.wounds < first.characteristics.wounds,
        0, first_state.attacks, state.first_player_turn,
    )).attacks
    second_count = phases.build_attacks(AttackPoolContext(
        second_attack_fighter, first_round, second_charging, first_charging,
        second_state.frenzy, second_state.wounds < second.characteristics.wounds,
        0, second_state.attacks, not state.first_player_turn,
    )).attacks
    first_count = resolve_spawn_attack_count(
        first_attack_fighter, first_count, dice, f"round.{state.round_index}.first.spawn-attacks"
    )
    second_count = resolve_spawn_attack_count(
        second_attack_fighter, second_count, dice, f"round.{state.round_index}.second.spawn-attacks"
    )
    first_shifty = (first_round and second_charging and has_tag(first.global_effects, "skill.shifty")
        and not has_tag(first_attack_fighter.main_weapon, "effect.serpent-staff-power"))
    second_shifty = (first_round and first_charging and has_tag(second.global_effects, "skill.shifty")
        and not has_tag(second_attack_fighter.main_weapon, "effect.serpent-staff-power"))
    # Add after Frenzy, before whole-warrior attack reductions. Split off only
    # this one attack below; ordinary attacks retain their original priority.
    if first_shifty and not (has_tag(first_attack_fighter.main_weapon, "weapon.fist")
            and not phases.ignores_unarmed_penalties(first.global_effects)):
        first_count += 1
    if second_shifty and not (has_tag(second_attack_fighter.main_weapon, "weapon.fist")
            and not phases.ignores_unarmed_penalties(second.global_effects)):
        second_count += 1
    first_count = apply_round_weapon_attack_modifiers(
        first, second, first_count, first_round=first_round,
        charging=first_charging, charged=second_charging,
    )
    second_count = apply_round_weapon_attack_modifiers(
        second, first, second_count, first_round=first_round,
        charging=second_charging, charged=first_charging,
    )
    first_count = apply_opponent_attack_modifiers(first, second, first_count, first_round=first_round)
    second_count = apply_opponent_attack_modifiers(second, first, second_count, first_round=first_round)
    if first_state.on_fire or first_state.condition != Condition.STANDING:
        first_count = 0
    if second_state.on_fire or second_state.condition != Condition.STANDING:
        second_count = 0
    first_shifty = first_shifty and first_count > 0
    second_shifty = second_shifty and second_count > 0
    events = [
        (first_attack_fighter, second, True, first_count - int(first_shifty), first_priority, 'first'),
        (second_attack_fighter, first, False, second_count - int(second_shifty), second_priority, 'second'),
    ]
    if not first_acts:
        events.reverse()
    # A charged whip's bonus has its own Strike First timing. Its ordinary
    # attacks retain their own priority and cannot borrow that bonus's tier.
    for owner, charged in ((True, second_charging), (False, first_charging)):
        for index, event in enumerate(events):
            attacker, defender, is_first, count, priority, label = event
            whip = whipcrack_weapon(attacker)
            if is_first != owner or not charged or not count or whip is None:
                continue
            events[index] = (*event[:3], count - 1, priority, label)
            bonus_fighter = replace(attacker, main_weapon=whip, off_hand=None,
                off_hand_attacks=False, extra_attacks=(), main_hand_slot=(
                    attacker.main_hand_slot if whip == attacker.main_weapon else attacker.off_hand_slot))
            bonus_priority = phases.PriorityResult(1, priority.initiative)
            bonus = (bonus_fighter, defender, is_first, 1, bonus_priority, f'{label}.whipcrack')
            position = len(events)
            for candidate_index, candidate in enumerate(events):
                if phases.first_acts_before(bonus_priority, candidate[4], dice,
                        key=f'round.{state.round_index}.{label}.whip-priority-tie'):
                    position = candidate_index
                    break
            events.insert(position, bonus)
            break
    # Ties belong to the two warriors at a given tier/Initiative, not to every
    # event. Reuse the ordinary tie when their bonus attacks share that tier.
    ties = {first_priority: first_acts} if first_priority == second_priority else {}
    for attacker, defender, is_first, active, stood, fighter_state in (
        (first, second, True, first_shifty, first_stood, first_state),
        (second, first, False, second_shifty, second_stood, second_state),
    ):
        if not active:
            continue
        label = 'first' if is_first else 'second'
        bonus_fighter = select_shifty_weapon(attacker, decisions, key=f"round.{state.round_index}.{label}.shifty")
        bonus_priority = resolve_priority(PriorityContext(
            bonus_fighter, defender, first_round, first_charging if is_first else second_charging,
            second_charging if is_first else first_charging, stood, fighter_state.initiative_penalty,
            initiative_bonus=fighter_state.initiative - attacker.characteristics.initiative,
            initiative_floor=fighter_state.initiative_floor,
        ))
        if bonus_priority.priority >= 0:
            bonus_priority = replace(bonus_priority, priority=max(1, bonus_priority.priority))
        bonus = (bonus_fighter, defender, is_first, 1, bonus_priority, f'{label}.shifty')
        position = len(events)
        for index, candidate in enumerate(events):
            candidate_priority = candidate[4]
            if bonus_priority == candidate_priority:
                if candidate[2] == is_first:
                    before = True
                else:
                    if bonus_priority not in ties:
                        # Whipcrack may already have resolved this exact tie.
                        peer = next((i for i, event in enumerate(events)
                            if event[2] == is_first and event[4] == bonus_priority), None)
                        winner = (peer < index if peer is not None else
                            first_acts_before(bonus_priority, candidate_priority, dice,
                                key=f"round.{state.round_index}.{label}.shifty-priority-tie"))
                        ties[bonus_priority] = winner if is_first else not winner
                    before = ties[bonus_priority] == is_first
            else:
                before = (bonus_priority.priority, bonus_priority.initiative) > (
                    candidate_priority.priority, candidate_priority.initiative)
            if before:
                position = index
                break
        events.insert(position, bonus)
    already_attacked = {True: False, False: False}
    for event_index, (attacker, defender, is_first, count, _, label) in enumerate(events):
        current = first_state if is_first else second_state
        initial = before_first if is_first else before_second
        if (label in ('first', 'second') and (first_shifty if is_first else second_shifty)
                and current.broken_hands != initial.broken_hands):
            # Trap Blade can break the bonus's weapon before the ordinary hit
            # rolls exist. Those later attacks must use the surviving equipment.
            source = original_first if is_first else original_second
            usable = equipment_for_state(replace(source, global_effects=attacker.global_effects),
                current, first_round=first_round)
            count = max(0, count - int(attacker.off_hand_attacks and not usable.off_hand_attacks))
            if has_tag(usable.main_weapon, 'weapon.fist') and not phases.ignores_unarmed_penalties(usable.global_effects):
                count = min(count, 1)
            attacker = usable
        # Kusara's minimum belongs to the warrior's whole phase, including
        # separately timed Whipcrack attacks. Consume each suppression once.
        other_attacks = already_attacked[is_first] or any(
            event[2] == is_first and event[3] > 0 for event in events[event_index + 1:])
        minimum_attacks = 0 if other_attacks else 1
        if is_first:
            first_state, second_state, resolved = _resolve_attack_pool(
                attacker, defender, first_state, second_state,
                count, dice,
                key=f"round.{state.round_index}.{label}", first_round=first_round,
                charging=first_charging, decisions=decisions,
                defender_condition_at_start=before_second.condition,
                minimum_attacks=minimum_attacks,
                single_bonus=label.endswith('.shifty'),
            )
        else:
            second_state, first_state, resolved = _resolve_attack_pool(
                attacker, defender, second_state, first_state,
                count, dice,
                key=f"round.{state.round_index}.{label}", first_round=first_round,
                charging=second_charging, decisions=decisions,
                defender_condition_at_start=before_first.condition,
                minimum_attacks=minimum_attacks,
                single_bonus=label.endswith('.shifty'),
            )
        already_attacked[is_first] = already_attacked[is_first] or bool(resolved)
        outcomes.extend(resolved)
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force.after-attack")
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force.after-attack")

    first_state, backlash = _black_hunger(first, first_state, dice, f"round.{state.round_index}.first.black-hunger")
    outcomes.extend(backlash)
    first_state = _force_of_will(
        first, first_state, dice, f"round.{state.round_index}.first.force.after-black-hunger"
    )
    second_state, backlash = _black_hunger(second, second_state, dice, f"round.{state.round_index}.second.black-hunger")
    outcomes.extend(backlash)
    second_state = _force_of_will(
        second, second_state, dice, f"round.{state.round_index}.second.force.after-black-hunger"
    )
    trace = tuple(dict.fromkeys((
        *(state.trace if state.round_index == 0 else ()), Phase.PRIORITY, Phase.ATTACKS,
        *(phase for outcome in outcomes for phase in outcome.trace), Phase.AFTERMATH,
    )))
    return CombatRoundResult(
        replace(state, first=first_state, second=second_state,
                round_index=state.round_index + 1, trace=trace),
        tuple(outcomes),
    )


def select_shifty_weapon(
    fighter: CompiledFighter, decisions: DecisionPolicy, *, key: str,
) -> CompiledFighter:
    """Project one nominated melee attack, preserving its original hand slot.

    Shifty grants no extra pistol shot. A pistol-only loadout needs a reviewed
    allocation contract; do not invent a fist attack while weapons remain.
    """
    weapon, clean, slot = fighter.main_weapon, fighter.main_weapon_without_poison, fighter.main_hand_slot
    off = fighter.off_hand if fighter.off_hand_attacks else None
    if off is not None and not is_pistol(off) and (
        is_pistol(weapon) or (off != weapon and not decisions.choose(f'{key}.main-weapon', fighter))
    ):
        weapon, clean, slot = off, fighter.off_hand_without_poison, fighter.off_hand_slot
    elif is_pistol(weapon):
        raise ValueError('Shifty requires a nominated melee weapon; pistol-only bonus allocation is unresolved')
    return replace(fighter, main_weapon=weapon, main_weapon_without_poison=clean,
        main_hand_slot=slot, off_hand=None, off_hand_without_poison=None,
        off_hand_attacks=False, extra_attacks=())


def select_attack_replacement(
    fighter: CompiledFighter, *, first_round: bool, charging: bool,
    decisions: DecisionPolicy, key: str,
) -> CompiledFighter:
    """Apply optional whole-pool replacements before attack count and resolution."""
    if fighter.vomit_attack is not None and decisions.choose(f"{key}.vomit-attack", fighter):
        return replace(fighter, main_weapon=fighter.vomit_attack,
            main_weapon_without_poison=None, off_hand=None, off_hand_without_poison=None,
            off_hand_attacks=False, extra_attacks=())
    if (has_tag(fighter.main_weapon, "weapon.serpent-staff")
            and decisions.choose(f"{key}.serpent-staff", fighter)):
        return replace(fighter, main_weapon=EffectSet(
            tags=("effect.serpent-staff-power",), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())
    removable = []
    if (has_tag(fighter.global_effects, "mechanic.anvil-head")
            and first_round and charging
            and not decisions.choose(f"{key}.anvil-head", fighter)):
        removable.append("mechanic.anvil-head")
    if (has_tag(fighter.global_effects, "mechanic.death-blow")
            and fighter.characteristics.attacks >= 2
            and not decisions.choose(f"{key}.death-blow", fighter)):
        removable.append("mechanic.death-blow")
    if not removable:
        return fighter
    effects = replace(
        fighter.global_effects,
        tags=tuple(tag for tag in fighter.global_effects.tags if tag not in removable),
    )
    return replace(fighter, global_effects=effects)


def resolve_spawn_attack_count(
    fighter: CompiledFighter, ordinary_count: int, dice: DiceSource, key: str,
) -> int:
    if has_tag(fighter.main_weapon, "weapon.vomit-attack"):
        return ordinary_count
    if phases.has_tag(fighter.global_effects, "mechanic.spawn-special-attacks"):
        return dice.roll(RollRequest(key)) + 1
    return ordinary_count


def apply_opponent_attack_modifiers(
    attacker: CompiledFighter, defender: CompiledFighter, count: int, *, first_round: bool,
) -> int:
    if not count:
        return 0
    if (
        phases.has_tag(defender.global_effects, "animal_friendship")
        and phases.has_tag(attacker.global_effects, "species.animal")
    ):
        return 0
    if (
        first_round
        and phases.has_tag(defender.global_effects, "skill.sigmar-s-sign")
        and phases.has_tag(attacker.global_effects, "undead_or_possessed")
    ):
        count = max(1, count - 1)
    return max(1, count + defender.global_effects.incoming_attacks_modifier)


def apply_round_weapon_attack_modifiers(
    attacker: CompiledFighter, defender: CompiledFighter, count: int, *,
    first_round: bool, charging: bool, charged: bool,
) -> int:
    """Apply weapon rules that change the pool because either fighter charged."""
    if not count or not first_round:
        return count
    if whipcrack_weapon(attacker) is not None and (charging or charged):
        count += 1
    if phases.has_tag(defender.main_weapon, "weapon.boar-spear") and charging:
        count = max(1, count - 1)
    return count
