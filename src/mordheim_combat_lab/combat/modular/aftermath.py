"""combat.modular.aftermath: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations
from mordheim_combat_lab.combat import phases

from dataclasses import replace
from mordheim_combat_lab.combat.phases import _characteristic_test
from mordheim_combat_lab.combat.modular.attacks import resolve_reference_attack
from mordheim_combat_lab.combat.modular.state import AttackOutcome
from mordheim_combat_lab.combat.modular.state import FighterState
from mordheim_combat_lab.combat.modular.state import _parry_capacity
from mordheim_combat_lab.combat.phases import Condition
from mordheim_combat_lab.combat.phases import has_tag
from mordheim_combat_lab.domain.dice import DiceSource
from mordheim_combat_lab.domain.dice import RollRequest
from mordheim_combat_lab.domain.models import CompiledFighter
from mordheim_combat_lab.domain.models import EffectSet




def _react_to_wound(
    attacker: CompiledFighter, defender: CompiledFighter,
    outcome: AttackOutcome, dice: DiceSource, key: str,
) -> AttackOutcome:
    attacker_state, defender_state = outcome.attacker, outcome.defender
    if outcome.damage and phases.has_tag(defender.global_effects, "acid_blood"):
        acid = EffectSet(
            tags=("rule.acid-blood", "effect.no-critical"), fixed_strength=3,
            automatic_hit=True, cannot_be_parried=True,
        )
        reaction_source = replace(
            defender_state, condition=Condition.STANDING,
            wounds=max(1, defender_state.wounds),
        )
        for index in range(outcome.damage):
            reaction = resolve_reference_attack(
                defender, attacker, reaction_source, attacker_state, acid, dice,
                key=f"{key}.acid-blood.{index}",
            )
            attacker_state = reaction.defender
    if (
        defender_state.condition == Condition.OUT
        and phases.has_tag(defender.global_effects, "contagious")
        and not phases.has_tag(attacker.global_effects, "undead_or_possessed")
        and not phases._characteristic_test(
            attacker_state.toughness, dice, f"{key}.contagious", six_fails=True,
            reroll=phases.has_tag(attacker.global_effects, "skill.blessed-sight"),
        )
    ):
        attacker_state = replace(
            attacker_state,
            wounds=attacker_state.wounds - 1,
            condition=(Condition.OUT if attacker_state.wounds <= 1 else attacker_state.condition),
        )
    return replace(outcome, attacker=attacker_state, defender=defender_state)


def _start_round_state(fighter: CompiledFighter, state: FighterState) -> tuple[FighterState, bool]:
    stood = state.condition == Condition.KNOCKED_DOWN
    condition = (
        Condition.KNOCKED_DOWN if state.condition == Condition.STUNNED
        else Condition.STANDING if stood
        else state.condition
    )
    return replace(
        state, condition=condition, parries_remaining=_parry_capacity(fighter),
        critical_available=True, attack_penalty=0,
    ), stood


def _force_of_will(
    fighter: CompiledFighter, state: FighterState, dice: DiceSource, key: str,
    *, sustain: bool = False,
) -> FighterState:
    if not phases.has_tag(fighter.global_effects, "mechanic.force-of-will"):
        return state
    if sustain and state.force_of_will_active and state.condition != Condition.OUT:
        penalty = state.force_of_will_penalty + 1
        if not phases._characteristic_test(
            max(0, state.toughness - penalty), dice, f"{key}.sustain",
            reroll=phases.has_tag(fighter.global_effects, "skill.blessed-sight"),
        ):
            return replace(state, condition=Condition.OUT, force_of_will_active=False, force_of_will_penalty=penalty)
        return replace(state, force_of_will_penalty=penalty)
    if state.force_of_will_active:
        return state
    if state.condition == Condition.OUT and "force-of-will" not in state.resources_spent:
        state = state.spend("force-of-will")
        if phases._characteristic_test(
            state.toughness, dice, f"{key}.rescue",
            reroll=phases.has_tag(fighter.global_effects, "skill.blessed-sight"),
        ):
            return replace(state, condition=Condition.STANDING, wounds=1, force_of_will_active=True)
    return state


def _fire_recovery(
    victim: CompiledFighter, opponent: CompiledFighter,
    victim_state: FighterState, opponent_state: FighterState,
    dice: DiceSource, key: str,
) -> tuple[FighterState, FighterState, tuple[AttackOutcome, ...]]:
    if not victim_state.on_fire or not victim_state.active:
        return victim_state, opponent_state, ()
    if dice.roll(RollRequest(f"{key}.extinguish")) >= 4:
        return replace(victim_state, on_fire=False), opponent_state, ()
    fire = EffectSet(
        tags=("attack.fire", "effect.no-critical"), fixed_strength=4,
        automatic_hit=True, cannot_be_parried=True,
    )
    result = resolve_reference_attack(
        opponent, victim, opponent_state, victim_state, fire, dice,
        key=f"{key}.hit",
    )
    return result.defender, result.attacker, (result,)


def _netter(
    netter: CompiledFighter, target: CompiledFighter,
    netter_state: FighterState, target_state: FighterState,
    dice: DiceSource, key: str,
) -> FighterState:
    if not phases.has_tag(netter.global_effects, "mechanic.netter"):
        return target_state
    hit_target = max(2, 7 - netter.ballistic_skill)
    if dice.roll(RollRequest(f"{key}.hit")) < hit_target:
        return target_state
    if phases._characteristic_test(
        target_state.strength, dice, f"{key}.escape",
        reroll=phases.has_tag(target.global_effects, "skill.blessed-sight"),
    ):
        return target_state
    return replace(target_state, condition=Condition.KNOCKED_DOWN)


def _spines(
    owner: CompiledFighter, target: CompiledFighter,
    owner_state: FighterState, target_state: FighterState,
    dice: DiceSource, key: str,
) -> tuple[FighterState, FighterState, tuple[AttackOutcome, ...]]:
    if not phases.has_tag(owner.global_effects, "spines"):
        return owner_state, target_state, ()
    effect = EffectSet(
        tags=("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True,
    )
    result = resolve_reference_attack(
        owner, target, owner_state, target_state, effect, dice, key=key,
    )
    return result.attacker, result.defender, (result,)


def _black_hunger(
    fighter: CompiledFighter, state: FighterState, dice: DiceSource, key: str,
) -> tuple[FighterState, tuple[AttackOutcome, ...]]:
    if not phases.has_tag(fighter.global_effects, "mechanic.black-hunger") or not state.active:
        return state, ()
    count = dice.roll(RollRequest(f"{key}.hits", 3))
    effect = EffectSet(
        tags=("mechanic.black-hunger-backlash", "effect.no-critical"),
        fixed_strength=3, automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
    )
    outcomes = []
    for index in range(count):
        result = resolve_reference_attack(
            fighter, fighter, state, state, effect, dice, key=f"{key}.hit.{index}",
        )
        state = result.defender
        outcomes.append(replace(result, attacker=state, defender=state))
        if not state.active:
            break
    return state, tuple(outcomes)
