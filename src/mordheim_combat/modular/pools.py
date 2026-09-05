"""combat.modular.attacks: responsibility extracted without altering the rules."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import replace
from mordheim_combat.phases import _characteristic_test
from mordheim_combat.modular.aftermath import _react_to_wound
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


from .attacks import resolve_reference_attack

def _weapon_for_attack(fighter: CompiledFighter, index: int, count: int, first_round: bool) -> EffectSet:
    if not fighter.off_hand_attacks or fighter.off_hand is None:
        return fighter.main_weapon
    main_pistol = any(phases.has_tag(fighter.main_weapon, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol"))
    off_pistol = any(phases.has_tag(fighter.off_hand, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol"))
    if main_pistol:
        return fighter.off_hand if not first_round or index > 0 else fighter.main_weapon
    if off_pistol and not first_round:
        return fighter.main_weapon
    return fighter.off_hand if index == count - 1 else fighter.main_weapon


def allocate_attack_weapons(
    fighter: CompiledFighter, count: int, first_round: bool,
    decisions: DecisionPolicy, *, key: str,
) -> tuple[EffectSet, ...]:
    """Choose which distinct melee weapon resolves all but one attack."""
    if (count > 2 and fighter.off_hand_attacks and fighter.off_hand is not None
            and fighter.main_weapon != fighter.off_hand
            and not any(phases.has_tag(weapon, tag)
                        for weapon in (fighter.main_weapon, fighter.off_hand)
                        for tag in ("weapon.pistol", "weapon.duelling-pistol"))):
        if not decisions.choose(f"{key}.main-weapon-majority", fighter):
            return (*(fighter.off_hand for _ in range(count - 1)), fighter.main_weapon)
    return tuple(_weapon_for_attack(fighter, index, count, first_round) for index in range(count))


def _prepared_hit(prepared: AttackOutcome):
    from mordheim_combat.phases import HitResult

    return HitResult(prepared.hit_target or 0, prepared.hit_roll or 1, prepared.hit)


def _resolve_prepared_defences(
    attacker: CompiledFighter,
    defender: CompiledFighter,
    attacker_state: FighterState,
    defender_state: FighterState,
    prepared_attacks: tuple[tuple[EffectSet, AttackOutcome], ...],
    dice: DiceSource,
    *,
    keys: tuple[str, ...],
    first_round: bool,
    charging: bool,
    helpless: bool,
) -> tuple[FighterState, FighterState, dict[int, AttackOutcome]]:
    """Resolve per-hit defences after every hit roll is known.

    Lucky Charm reacts to the first successful hit in attack order. Parries are
    then offered from the highest remaining hit roll downwards. Unparryable
    attacks do not consume capacity, and a charm save leaves that capacity
    available for the next eligible hit.
    """
    resolved: dict[int, AttackOutcome] = {}
    successful = [
        index for index, (_, prepared) in enumerate(prepared_attacks)
        if prepared.hit
    ]

    if defender_state.lucky_charm and successful:
        index = successful[0]
        weapon, prepared = prepared_attacks[index]
        outcome = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=keys[index], first_round=first_round, charging=charging,
            helpless_at_start=helpless, prepared_hit=_prepared_hit(prepared),
            defences_only=True, parry_allowed=False,
        )
        attacker_state, defender_state = outcome.attacker, outcome.defender
        if outcome.saved:
            resolved[index] = replace(
                outcome, hit_roll=prepared.hit_roll,
                hit_target=prepared.hit_target,
            )

    candidates = sorted(
        (index for index in successful if index not in resolved),
        key=lambda index: prepared_attacks[index][1].hit_roll or 0,
        reverse=True,
    )
    for index in candidates:
        if defender_state.parries_remaining <= 0 or not attacker_state.active:
            break
        weapon, prepared = prepared_attacks[index]
        outcome = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=keys[index], first_round=first_round, charging=charging,
            helpless_at_start=helpless, prepared_hit=_prepared_hit(prepared),
            defences_only=True,
        )
        attacker_state, defender_state = outcome.attacker, outcome.defender
        if outcome.parried:
            resolved[index] = replace(
                outcome, hit_roll=prepared.hit_roll,
                hit_target=prepared.hit_target,
            )

    return attacker_state, defender_state, resolved


def _resolve_attack_pool(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    count: int, dice: DiceSource, *, key: str, first_round: bool, charging: bool,
    decisions: DecisionPolicy,
) -> tuple[FighterState, FighterState, tuple[AttackOutcome, ...]]:
    outcomes: list[AttackOutcome] = []
    if count <= 0 or attacker_state.condition != Condition.STANDING:
        return attacker_state, defender_state, ()
    helpless = defender_state.condition in (Condition.KNOCKED_DOWN, Condition.PARALYZED)
    use_bull_charge = (
        first_round and charging
        and phases.has_tag(attacker.global_effects, "mechanic.bull-charge")
        and decisions.choose(f"{key}.bull-charge", attacker)
    )
    if use_bull_charge:
        bull = EffectSet(tags=("mechanic.bull-charge",), hit_modifier=1)
        result = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, bull, dice,
            key=f"{key}.bull-charge", first_round=True, charging=True,
            helpless_at_start=helpless, decisions=decisions,
        )
        if result.hit and not result.parried and result.defender.condition == Condition.STANDING:
            result = replace(result, defender=replace(result.defender, condition=Condition.KNOCKED_DOWN))
        result = _react_to_wound(attacker, defender, result, dice, f"{key}.bull-charge")
        return result.attacker, result.defender, (result,)

    use_body_slam = (
        first_round and charging
        and phases.has_tag(attacker.global_effects, "mechanic.body-slam")
        and decisions.choose(f"{key}.body-slam", attacker)
    )
    if use_body_slam:
        weapons = (EffectSet(tags=("mechanic.body-slam",), strength_bonus=1, hit_modifier=1),)
    else:
        weapons = allocate_attack_weapons(attacker, count, first_round, decisions, key=key)
    weapons += tuple(weapon for weapon in attacker.extra_attacks
                     if charging or not phases.has_tag(weapon, "rule.horned-one"))
    weapons = tuple(weapon_against_opponent(attacker, defender, weapon) for weapon in weapons)
    if weapons and phases.has_tag(attacker.global_effects, "mechanic.unpredictable-attack"):
        weapons = (merge_effects(weapons[0], EffectSet(cannot_be_parried=True)), *weapons[1:])

    prepared_attacks: list[tuple[EffectSet, AttackOutcome]] = []
    attack_keys = tuple(f"{key}.attack.{index}" for index in range(len(weapons)))
    for index, weapon in enumerate(weapons):
        prepared = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=attack_keys[index], first_round=first_round,
            charging=charging, helpless_at_start=helpless, hit_only=True,
        )
        attacker_state = prepared.attacker
        prepared_attacks.append((weapon, prepared))
    prepared_tuple = tuple(prepared_attacks)
    attacker_state, defender_state, defended = _resolve_prepared_defences(
        attacker, defender, attacker_state, defender_state, prepared_tuple, dice,
        keys=attack_keys, first_round=first_round, charging=charging,
        helpless=helpless,
    )

    # Bear Hug replaces two successful, undefended hits before wound
    # resolution. Its opposed roll is independently exhaustive; this branch
    # verifies only the state-transfer sequence in the scalar orchestrator.
    if attacker.global_effects.bear_hug and len(weapons) >= 2:
        surviving = [
            prepared.hit and index not in defended
            for index, (_, prepared) in enumerate(prepared_tuple[:2])
        ]
        hug = phases.resolve_bear_hug(BearHugContext(
            sum(surviving),
            attacker_state.strength, defender_state.strength,
            key=f"{key}.bear-hug",
        ), dice, decisions)
        if hug.chosen:
            if hug.wounded:
                automatic = EffectSet(
                    tags=("effect.automatic-wound", "effect.no-critical"),
                    automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
                )
                result = resolve_reference_attack(
                    attacker, defender, attacker_state, defender_state, automatic, dice,
                    key=f"{key}.bear-hug.result", first_round=first_round,
                    charging=charging, helpless_at_start=helpless,
                    decisions=decisions,
                )
                result = _react_to_wound(attacker, defender, result, dice, f"{key}.bear-hug.result")
                attacker_state, defender_state = result.attacker, result.defender
                outcomes.append(result)
        else:
            for index, (weapon, success) in enumerate(zip(weapons[:2], surviving)):
                if not success or not defender_state.active:
                    continue
                result = resolve_reference_attack(
                    attacker, defender, attacker_state, defender_state, weapon, dice,
                    key=attack_keys[index], first_round=first_round,
                    charging=charging, helpless_at_start=helpless,
                    prepared_hit=_prepared_hit(prepared_tuple[index][1]),
                    defences_resolved=True, decisions=decisions,
                )
                result = replace(
                    result, hit_roll=prepared_tuple[index][1].hit_roll,
                    hit_target=prepared_tuple[index][1].hit_target,
                )
                result = _react_to_wound(
                    attacker, defender, result, dice,
                    f"{key}.bear-hug.normal.{index}",
                )
                attacker_state, defender_state = result.attacker, result.defender
                outcomes.append(result)
        for index, (weapon, prepared) in enumerate(prepared_tuple[2:], start=2):
            if not defender_state.active or not prepared.hit:
                continue
            if index in defended:
                continue
            result = resolve_reference_attack(
                attacker, defender, attacker_state, defender_state, weapon, dice,
                key=attack_keys[index], first_round=first_round,
                charging=charging, helpless_at_start=helpless,
                prepared_hit=_prepared_hit(prepared), defences_resolved=True,
                decisions=decisions,
            )
            result = replace(
                result, hit_roll=prepared.hit_roll, hit_target=prepared.hit_target
            )
            result = _react_to_wound(
                attacker, defender, result, dice, f"{key}.attack.{index}"
            )
            attacker_state, defender_state = result.attacker, result.defender
            outcomes.append(result)
        return attacker_state, defender_state, tuple(outcomes)

    for index, (weapon, prepared) in enumerate(prepared_attacks):
        if not prepared.hit:
            outcomes.append(prepared)
            continue
        if index in defended:
            outcomes.append(defended[index])
            continue
        if not attacker_state.active or not defender_state.active:
            break
        result = resolve_reference_attack(
            attacker, defender, attacker_state, defender_state, weapon, dice,
            key=f"{key}.attack.{index}", first_round=first_round,
            charging=charging, helpless_at_start=helpless,
            prepared_hit=_prepared_hit(prepared), defences_resolved=True,
            decisions=decisions,
        )
        result = replace(
            result, hit_roll=prepared.hit_roll, hit_target=prepared.hit_target
        )
        result = _react_to_wound(attacker, defender, result, dice, f"{key}.attack.{index}")
        attacker_state, defender_state = result.attacker, result.defender
        outcomes.append(result)
        # Anvil Head replaces charge attacks only: the D3 wound expansion is
        # inert outside a charge (Khemri, Necromantic Modification / Anvil Head).
        if (result.hit and not result.parried and first_round and charging
                and phases.has_tag(_combined_effect(attacker, weapon), "mechanic.anvil-head")):
            repeats = dice.roll(RollRequest(f"{key}.attack.{index}.anvil-hits", 3)) - 1
            repeated = merge_effects(weapon, EffectSet(automatic_hit=True, cannot_be_parried=True))
            for repeat_index in range(repeats):
                extra = resolve_reference_attack(
                    attacker, defender, attacker_state, defender_state, repeated, dice,
                    key=f"{key}.attack.{index}.anvil.{repeat_index}",
                    first_round=first_round, charging=charging,
                    helpless_at_start=helpless, decisions=decisions,
                )
                extra = _react_to_wound(
                    attacker, defender, extra, dice,
                    f"{key}.attack.{index}.anvil.{repeat_index}",
                )
                attacker_state, defender_state = extra.attacker, extra.defender
                outcomes.append(extra)
                if not defender_state.active:
                    break
    return attacker_state, defender_state, tuple(outcomes)
