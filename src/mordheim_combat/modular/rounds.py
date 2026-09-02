"""combat.modular.rounds: responsabilidad extraída sin alterar las reglas."""
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
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import CombatRoundResult
from mordheim_combat.modular.state import DuelState
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
    outcomes: list[AttackOutcome] = []
    first_round = state.round_index == 0
    if not first_round:
        first_state = _force_of_will(first, first_state, dice, f"round.{state.round_index}.first.force", sustain=True)
        second_state = _force_of_will(second, second_state, dice, f"round.{state.round_index}.second.force", sustain=True)
        first_state, second_state, fire = _fire_recovery(
            first, second, first_state, second_state, dice, f"round.{state.round_index}.first.fire"
        )
        outcomes.extend(fire)
        second_state, first_state, fire = _fire_recovery(
            second, first, second_state, first_state, dice, f"round.{state.round_index}.second.fire"
        )
        outcomes.extend(fire)
    if first_state.condition == Condition.PARALYZED and _characteristic_test(
        first_state.toughness, dice, f"round.{state.round_index}.first.paralysis",
        reroll=phases.has_tag(first.global_effects, "skill.blessed-sight"),
    ):
        first_state = replace(first_state, condition=Condition.STANDING)
    if second_state.condition == Condition.PARALYZED and _characteristic_test(
        second_state.toughness, dice, f"round.{state.round_index}.second.paralysis",
        reroll=phases.has_tag(second.global_effects, "skill.blessed-sight"),
    ):
        second_state = replace(second_state, condition=Condition.STANDING)
    first_state, first_stood = _start_round_state(first, first_state)
    second_state, second_stood = _start_round_state(second, second_state)
    first_charging = first_round and state.first_charged
    second_charging = first_round and not state.first_charged
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

    first_priority = phases.resolve_priority(PriorityContext(
        first, second, first_round, first_charging, second_charging, first_stood,
        first_state.initiative_penalty,
        initiative_floor=first_state.initiative_floor,
    ))
    second_priority = phases.resolve_priority(PriorityContext(
        second, first, first_round, second_charging, first_charging, second_stood,
        second_state.initiative_penalty,
        initiative_floor=second_state.initiative_floor,
    ))
    first_acts = phases.first_acts_before(
        first_priority, second_priority, dice, key=f"round.{state.round_index}.priority-tie",
    )

    first_attack_fighter = select_attack_replacement(
        first, first_round=first_round, charging=first_charging,
        decisions=decisions, key=f"round.{state.round_index}.first",
    )
    second_attack_fighter = select_attack_replacement(
        second, first_round=first_round, charging=second_charging,
        decisions=decisions, key=f"round.{state.round_index}.second",
    )

    first_count = phases.build_attacks(AttackPoolContext(
        first_attack_fighter, first_round, first_charging, second_charging,
        first_state.frenzy, first_state.wounds < first.characteristics.wounds,
        first_state.attack_penalty, first_state.attacks,
    )).attacks
    second_count = phases.build_attacks(AttackPoolContext(
        second_attack_fighter, first_round, second_charging, first_charging,
        second_state.frenzy, second_state.wounds < second.characteristics.wounds,
        second_state.attack_penalty, second_state.attacks,
    )).attacks
    first_count = resolve_spawn_attack_count(
        first_attack_fighter, first_count, dice, f"round.{state.round_index}.first.spawn-attacks"
    )
    second_count = resolve_spawn_attack_count(
        second_attack_fighter, second_count, dice, f"round.{state.round_index}.second.spawn-attacks"
    )
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
    order = ((first_attack_fighter, second, True), (second_attack_fighter, first, False)) if first_acts else (
        (second_attack_fighter, first, False), (first_attack_fighter, second, True)
    )
    for attacker, defender, is_first in order:
        if is_first:
            first_state, second_state, resolved = _resolve_attack_pool(
                attacker, defender, first_state, second_state, first_count, dice,
                key=f"round.{state.round_index}.first", first_round=first_round,
                charging=first_charging, decisions=decisions,
            )
        else:
            second_state, first_state, resolved = _resolve_attack_pool(
                attacker, defender, second_state, first_state, second_count, dice,
                key=f"round.{state.round_index}.second", first_round=first_round,
                charging=second_charging, decisions=decisions,
            )
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
        DuelState(first_state, second_state, state.round_index + 1, state.first_charged, trace),
        tuple(outcomes),
    )


def select_attack_replacement(
    fighter: CompiledFighter, *, first_round: bool, charging: bool,
    decisions: DecisionPolicy, key: str,
) -> CompiledFighter:
    """Apply optional whole-pool replacements before attack count and resolution."""
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
    if phases.has_tag(attacker.main_weapon, "weapon.serpent-whip") and (charging or charged):
        count += 1
    if phases.has_tag(defender.main_weapon, "weapon.boar-spear") and charging:
        count = max(1, count - 1)
    return count
