"""combat: Reference attack resolution for the modular engine."""
from __future__ import annotations
from mordheim_combat import phases

from dataclasses import replace
from types import SimpleNamespace
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
from mordheim_combat.modular.contexts import OwnedRollDice
from mordheim_combat.modular.contexts import reject_curse_unmodifiable_save
from mordheim_combat.modular.state import AttackOutcome
from mordheim_combat.modular.state import FighterState
from mordheim_combat.modular.state import require_characteristics
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


def _trip_eligible(attacker: CompiledFighter, attacker_state: FighterState,
                   weapon: EffectSet) -> bool:
    """The Trip trick replaces a wound roll of attacks the bearer directs.

    The trip state lives on FighterState (it is set per combat turn by
    resolve_round when the Confound-and-Confuse chooser accepts the trip
    slot), never on the compiled profile, which never changes between
    rounds; read it there.
    """
    return (phases.has_tag(attacker.global_effects, "mechanic.confound-and-confuse")
        and attacker_state.trip_trick_active
        and "jester.trip" not in attacker_state.resources_spent
        and not phases.has_tag(weapon, "effect.wraith-touch"))


def _mim_regeneration(defender, current, dice, decisions, key):
    """MiM's full restoration follows damage; only a rolled failure exhausts it."""
    if (not has_tag(defender.global_effects, "mechanic.mim-regeneration")
            or "mim-regeneration-exhausted" in current.resources_spent
            or decisions is not None and not decisions.choose(f"{key}.mim-regeneration", current)):
        return current, False
    if dice.roll(RollRequest(f"{key}.mim-regeneration")) >= 4:
        maximum = defender.characteristics.wounds + int(has_tag(defender.global_effects, "skill.monstrous"))
        return replace(current, wounds=maximum), True
    return current.spend("mim-regeneration-exhausted"), False


def resolve_reference_attack(attacker, defender, attacker_state, defender_state, weapon, dice, **options):
    """Resolve an attack; Rapier Barrage requires no established wound, even saved."""
    trance_target = defender_state.entranced
    if attacker_state.entranced and options.get('prepared_hit') is None:
        return AttackOutcome(attacker_state, defender_state)
    # The first declaration benefits from the trance; subsequent attacks do not.
    if (attacker_state.entranced or defender_state.entranced) and options.get('prepared_hit') is None:
        options = {**options, 'helpless_at_start': options.get('helpless_at_start', False) or trance_target}
        attacker_state = replace(attacker_state, entranced=False)
        defender_state = replace(defender_state, entranced=False)
    base_key = options['key']
    initial_stun = defender_state.condition == Condition.STUNNED
    penalty = 0
    any_hit = False
    reacted_damage = 0
    secondary_wounded = False
    while True:
        secondary_outcomes = []
        result = _resolve_reference_attack_once(attacker, defender, attacker_state,
            defender_state, weapon, dice, barrage_penalty=penalty,
            secondary_outcomes=secondary_outcomes, **options)
        secondary_damage = sum(outcome.damage for outcome in secondary_outcomes)
        reacted_damage += secondary_damage
        secondary_wounded = secondary_wounded or any(outcome.wounded for outcome in secondary_outcomes)
        if secondary_outcomes or secondary_wounded:
            result = replace(result, damage=result.damage + reacted_damage,
                damage_already_reacted=reacted_damage,
                wounded=result.wounded or secondary_wounded)
        any_hit = any_hit or result.hit
        policy = options.get('decisions')
        if (not result.barrage_available or result.wounded or not result.attacker.active or not result.defender.active
                or policy is not None and not policy.choose(f"{options['key']}.barrage", result)):
            return replace(result, hit=any_hit, barrage_available=False,
                melee_attack=options.get("melee_attack", True),
                knocked_down_target=bool(options.get("helpless_at_start", False)))
        penalty += 1
        attacker_state, defender_state = result.attacker, result.defender
        options = {**options, 'key': f'{base_key}.barrage.{penalty}',
            'prepared_hit': None, 'natural_hit_six': None,
            'defences_resolved': False, 'stunned_at_start': initial_stun}


def _resolve_reference_attack_once(attacker, defender, attacker_state, defender_state, weapon, dice, **options):
    own = OwnedRollDice(dice, attacker, attacker_state, options.get("decisions"))
    self_hit = (attacker_state is defender_state and (
        attacker is defender or has_tag(weapon, "mechanic.black-hunger-backlash")))
    enemy = own if self_hit else OwnedRollDice(
        dice, defender, defender_state, options.get("decisions"))
    result = _resolve_reference_attack_body(attacker, defender, attacker_state, defender_state,
        weapon, dice, attacker_dice=own, defender_dice=enemy, self_attack=self_hit, **options)
    return replace(result,
        attacker=replace(result.attacker, resources_spent=result.attacker.resources_spent | own.state.resources_spent),
        defender=replace(result.defender, resources_spent=result.defender.resources_spent | enemy.state.resources_spent))


def _resolve_reference_attack_body(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, dice: DiceSource, *, key: str,
    first_round: bool = False, charging: bool = False,
    helpless_at_start: bool = False,
    stunned_at_start: bool | None = None,
    melee_attack: bool = True,
    hit_only: bool = False,
    prepared_hit: object | None = None,
    natural_hit_six: bool | None = None,
    defences_resolved: bool = False,
    ethereal_resolved: bool = False,
    marks_resolved: bool = False,
    defences_only: bool = False,
    parry_allowed: bool = True,
    decisions: DecisionPolicy | None = None,
    barrage_penalty: int = 0,
    secondary_outcomes: list[AttackOutcome] | None = None,
    attacker_dice=None, defender_dice=None,
    rememberer_pool_key: str | None = None,
    self_attack: bool = False,
    single_wound: bool = False,
) -> AttackOutcome:
    """Resolve one attack and return new immutable fighter states."""
    if not attacker_state.active or not defender_state.active:
        return AttackOutcome(attacker_state, defender_state)
    if (melee_attack and prepared_hit is None
            and phases.has_tag(attacker.global_effects, "mechanic.honorable")
            and defender_state.condition in (Condition.KNOCKED_DOWN, Condition.STUNNED)):
        return AttackOutcome(attacker_state, defender_state)
    if (melee_attack and not has_tag(weapon, "mechanic.electrical-touch-attack")
            and (stunned_at_start if stunned_at_start is not None else
                         defender_state.condition == Condition.STUNNED and prepared_hit is None)):
        return AttackOutcome(attacker_state, replace(defender_state, condition=Condition.OUT))
    if (phases.has_tag(weapon, "effect.wraith-touch")
            and any(phases.has_tag(defender.global_effects, tag) for tag in ("nature.undead", "nature.possessed"))):
        return AttackOutcome(attacker_state, defender_state)
    weapon = weapon_against_opponent(attacker, defender, weapon)
    effect = _combined_effect(attacker, weapon)
    if (has_tag(weapon, "mechanic.giggle-juice-spray-attack")
            and (defender.global_effects.poison_immunity or has_tag(defender.global_effects, "poison_immune"))):
        return AttackOutcome(attacker_state, defender_state, hit=True, trace=(Phase.HIT,))
    if phases.has_tag(effect, "mechanic.death-blow") and attacker.characteristics.attacks < 2:
        effect = replace(
            effect,
            hit_modifier=effect.hit_modifier - 1,
            wound_modifier=effect.wound_modifier - 1,
            injury_modifier=effect.injury_modifier - 1,
        )
    if prepared_hit is None:
        automatic = (effect.automatic_hit or helpless_at_start or defender_state.charm_auto_hit
                     or defender_state.condition == Condition.PARALYZED)
        automatic = automatic or (defender_state.weapon_skill == 0 and not (
            has_tag(defender.global_effects, "mechanic.inconsistency")
            and "WS" not in defender_state.random_rolled
            and any(stat == "WS" for stat, *_ in defender.random_characteristics)))
        needs_sixes = attacker_state.fear_hit_sixes and melee_attack
        sweep = has_tag(effect, "skill.sweep") and weapon.two_handed and not needs_sixes
        if sweep:
            defender_state = require_characteristics(defender, defender_state, dice,
                f"{key}.defender", {"I"}, decisions)
        elif not automatic and not needs_sixes and not has_tag(effect, "mechanic.invincible-swordsman"):
            attacker_state = require_characteristics(attacker, attacker_state, dice,
                f"{key}.attacker", {"WS"}, decisions)
            defender_state = require_characteristics(defender, defender_state, dice,
                f"{key}.defender", {"WS"}, decisions)
        attacker_dice.state, defender_dice.state = attacker_state, defender_state
    hit_context = prepare_hit_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        first_round=first_round, charging=charging,
        helpless_at_start=helpless_at_start, key=f"{key}.hit", melee_attack=melee_attack,
        allow_luck=decisions is None,
    )
    hit_context = replace(hit_context, modifier=hit_context.modifier - barrage_penalty)
    reroll = _hit_reroll(attacker, defender, weapon, effect, first_round, charging, frenzy=attacker_state.frenzy)
    luck_available = phases.has_tag(effect, "skill.luck") and "luck" not in attacker_state.resources_spent
    luck_for_hit = decisions is None and luck_available and not reroll
    if prepared_hit is not None:
        hit = prepared_hit
    elif phases.has_tag(effect, "skill.sweep") and weapon.two_handed and not hit_context.needs_sixes:
        passed = phases._characteristic_test(
            defender_state.initiative, defender_dice, f"{key}.sweep",
            reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"),
        )
        from mordheim_combat.phases import HitResult
        hit = HitResult(0, 1 if passed else 6, not passed)
    else:
        hit = phases.resolve_hit(hit_context, attacker_dice)
        if attacker_dice.rerolled:
            hit = replace(hit, rerolled=True)
    if (prepared_hit is None and melee_attack and not hit.success and not hit.rerolled
            and has_tag(attacker.global_effects, "condition.rememberer-support")
            and has_tag(attacker.global_effects, "identity.slayer")
            and has_tag(attacker.global_effects, "fighter-kind.hero")
            and (has_tag(defender.global_effects, "size.large")
                 or has_tag(attacker.global_effects, "mechanic.rememberer-large-or-tough")
                 and defender_state.toughness >= 5)
            and any(has_tag(attacker.global_effects, tag) for tag in
                    ("mechanic.rememberer-large-only", "mechanic.rememberer-large-or-tough"))):
        active_key = f"rememberer-active.{rememberer_pool_key or key}"
        active = active_key in attacker_state.resources_spent
        if (active or "rememberer" not in attacker_state.resources_spent
                and decisions is not None and decisions.choose(f"{key}.rememberer", hit)):
            attacker_state = attacker_state.spend("rememberer")
            if rememberer_pool_key is not None:
                attacker_state = attacker_state.spend(active_key)
            hit = replace(phases.resolve_hit(replace(hit_context,
                reroll=False, key=f"{key}.hit.reroll"), attacker_dice), rerolled=True)
    if (prepared_hit is None and melee_attack and hit.success and not hit.rerolled
            and has_tag(defender.global_effects, "mechanic.corruption")
            and not has_tag(attacker.global_effects, "mechanic.psychology-immunity")
            and "corruption" not in defender_state.resources_spent
            and decisions is not None and decisions.choose(f"{key}.corruption", hit)):
        defender_state = defender_state.spend("corruption")
        hit = replace(phases.resolve_hit(replace(hit_context,
            reroll=False, key=f"{key}.hit.reroll"), attacker_dice), rerolled=True)
    if (prepared_hit is None and not hit.success and not hit.rerolled
            and first_round and phases.has_tag(weapon, "weapon.spear")
            and phases.has_tag(effect, "mechanic.seaguard-spear-master")
            and "seaguard-spear-master" not in attacker_state.resources_spent
            and (decisions is None or decisions.choose(f"{key}.spear-master", hit))):
        # One chosen failed hit, not one reroll per attack. Declining a miss
        # keeps the resource for a later miss in this same first-round pool.
        hit = replace(phases.resolve_hit(replace(hit_context,
            reroll=False, key=f"{key}.hit.reroll"), attacker_dice), rerolled=True)
        attacker_state = attacker_state.spend("seaguard-spear-master")
    # Keep physical die provenance before a replacement success changes its face.
    if natural_hit_six is None:
        natural_hit_six = (attacker_dice.original_roll == 6 if attacker_dice.original_roll is not None
                          else hit.roll == 6) and not (
            phases.has_tag(effect, "skill.sweep") and weapon.two_handed and not hit_context.needs_sixes
        )
    trace = (Phase.HIT,)
    if luck_for_hit and hit.rerolled:
        attacker_state = attacker_state.spend("luck")
    if (not hit.success and melee_attack and first_round
            and has_tag(attacker.global_effects, "mechanic.magic-acorn")
            and has_tag(attacker.global_effects, "fighter-kind.hero")
            and "magic-acorn" not in attacker_state.resources_spent):
        attacker_state = attacker_state.spend("magic-acorn")
        hit = replace(hit, success=True)
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
            hit_target=hit.target, trace=trace, natural_hit_six=natural_hit_six,
        )
    attacker_state = replace(attacker_state,
        resources_spent=attacker_state.resources_spent | attacker_dice.state.resources_spent)
    defender_state = replace(defender_state,
        resources_spent=defender_state.resources_spent | defender_dice.state.resources_spent)
    if (not defences_resolved and not ethereal_resolved
            and phases.has_tag(defender.global_effects, "mechanic.ethereal-hit-save")
            and not phases.has_tag(effect, "attack.magical")):
        reject_curse_unmodifiable_save(defender, effect, "Ethereal")
        if defender_dice.unmodifiable(RollRequest(f"{key}.ethereal")) >= defender.global_effects.ethereal_hit_save:
            return AttackOutcome(attacker_state, defender_state, hit=True, hit_roll=hit.roll,
                hit_target=hit.target, saved=True, trace=trace)
    # Printed Marks of Ranald clause: the Priest ducks past any hit on an
    # unmodifiable 6+, regardless of Strength or source including magical
    # attacks, on a roll made before critical hit effects are determined.  Like
    # the ethereal save it intercepts the hit here, so the ability never also
    # resolves later as a ward save.
    if (not defences_resolved and not marks_resolved
            and phases.has_tag(defender.global_effects, "mechanic.marks-of-ranald")):
        reject_curse_unmodifiable_save(defender, effect, "Marks of Ranald")
        if defender_dice.unmodifiable(RollRequest(f"{key}.marks-of-ranald")) >= 6:
            return AttackOutcome(attacker_state, defender_state, hit=True, hit_roll=hit.roll,
                hit_target=hit.target, saved=True, trace=trace)
    killing_blow = natural_hit_six and phases.has_tag(effect, "mechanic.killing-blow")
    if killing_blow:
        effect = replace(effect, cannot_be_parried=True)
    if not defences_resolved and defender_state.lucky_charm:
        charm = defender_dice.roll(RollRequest(f"{key}.lucky-charm"))
        defender_state = replace(defender_state, lucky_charm=False)
        if charm >= 4:
            return AttackOutcome(attacker_state, defender_state, hit=True, hit_roll=hit.roll, saved=True, trace=trace)
    parry_context = None if defences_resolved or not parry_allowed else _parry_context(
        defender, defender_state, effect, 0, hit.roll, key, natural_hit_six=natural_hit_six,
    )
    if parry_context is not None:
        if not parry_context.cannot_be_parried and (not natural_hit_six or parry_context.can_parry_six):
            if not effect.fixed_strength:
                attacker_state = require_characteristics(attacker, attacker_state, dice,
                    f"{key}.attacker", {"S"}, decisions)
            defender_state = require_characteristics(defender, defender_state, dice,
                f"{key}.defender", {"S", "WS"} if parry_context.roll_under is not None else {"S"}, decisions)
            attacker_dice.state, defender_dice.state = attacker_state, defender_state
            strength, _ = _attack_strength(attacker, defender, attacker_state, weapon, effect,
                                          first_round, charging, melee_attack=melee_attack)
            parry_context = _parry_context(defender, defender_state, effect, strength, hit.roll, key,
                                          natural_hit_six=natural_hit_six)
        parry = phases.resolve_parry(parry_context, defender_dice)
        trace += (Phase.PARRY,)
        if parry.attempted:
            defender_state = replace(defender_state, parries_remaining=defender_state.parries_remaining - 1)
        if parry.blocked:
            if (any(phases.has_tag(candidate, "weapon.sword-breaker") for candidate in
                    (defender.main_weapon, defender.off_hand or EffectSet()))
                    and not has_tag(weapon, "weapon.indestructible")
                    and any(tag.startswith('weapon.') and tag not in ('weapon.fist', 'weapon.natural-attacks')
                            for tag in weapon.tags)):
                if defender_dice.roll(RollRequest(f"{key}.trap-blade")) >= 4:
                    hand = attacker.main_hand_slot if attacker.main_hand_slot not in attacker_state.broken_hands and any(
                        tag in attacker.main_weapon.tags for tag in weapon.tags if tag.startswith('weapon.')) else attacker.off_hand_slot
                    attacker_state = replace(attacker_state, broken_hands=attacker_state.broken_hands | {hand})
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
    if (melee_attack and has_tag(attacker.global_effects, "mechanic.plague-carrier")
            and "plague-carrier-infected" not in attacker_state.resources_spent):
        defender_state = require_characteristics(defender, defender_state, dice,
            f"{key}.defender", {"T"}, decisions)
        defender_dice.state = defender_state
        resisted = _characteristic_test(defender_state.toughness, defender_dice,
            f"{key}.plague-carrier", reroll=has_tag(defender.global_effects, "skill.blessed-sight"))
        if not resisted:
            defender_state = replace(defender_state,
                initiative_penalty=defender_state.initiative_penalty + 1)
            attacker_state = attacker_state.spend("plague-carrier-infected")
    if natural_hit_six and phases.has_tag(effect, "trait.spectral-touch"):
        # One extra wound of this attack, not a fresh hit/poison/critical trigger.
        extra_key = f"{key}.spectral-touch"
        extra = _resolve_wound_damage(
            attacker, defender, attacker_state, defender_state, weapon,
            effect,
            phases.WoundResult(0, 0, True, False), phases.CriticalResult(), dice,
            key=extra_key, first_round=first_round, charging=charging,
            helpless_at_start=helpless_at_start, decisions=decisions,
            trace=(Phase.WOUND,), single_wound=True, melee_attack=melee_attack,
        )
        from mordheim_combat.modular.aftermath import _react_to_wound
        extra = _react_to_wound(attacker, defender, extra, dice, extra_key, decisions=decisions)
        if secondary_outcomes is not None:
            secondary_outcomes.append(extra)
        attacker_state, defender_state = extra.attacker, extra.defender
        attacker_dice.state, defender_dice.state = attacker_state, defender_state
        if not attacker_state.active or not defender_state.active:
            return AttackOutcome(attacker_state, defender_state, hit=True,
                hit_roll=hit.roll, hit_target=hit.target, trace=trace,
                reactions_resolved=True)
    # Bull Charge substitutes the wound step: an undefended hit is consumed by
    # the pool handler to knock the target down without a To Wound roll.
    if (phases.has_tag(effect, "mechanic.bull-charge")
            and not phases.has_tag(weapon, "weapon.vomit-attack")):
        return AttackOutcome(
            attacker_state, defender_state, hit=True, hit_roll=hit.roll,
            hit_target=hit.target, trace=trace,
        )
    if phases.has_tag(weapon, "weapon.kusara-kama") and hit.roll >= 5:
        hand = defender.main_hand_slot
        if (defender.off_hand_attacks and defender.off_hand is not None and decisions is not None
                and not decisions.choose(f"{key}.kusara-main-hand", defender)):
            hand = defender.off_hand_slot
        defender_state = replace(defender_state, attack_penalty=defender_state.attack_penalty + 1,
            hampered_hands=(*defender_state.hampered_hands, hand))
    if phases.has_tag(weapon, "weapon.chained-squig"):
        defender_state = replace(defender_state, entangled=True)
    ignition = (
        min(effect.ignition_threshold, defender.global_effects.caught_fire_threshold)
        if effect.ignition_threshold <= 6 else 7
    )
    if ignition <= 6 and attacker_dice.roll(RollRequest(f"{key}.ignition")) >= ignition:
        defender_state = replace(defender_state, on_fire=True)
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")
    if (not poison_blocked and (
            has_tag(weapon, "weapon.disease-dagger") and natural_hit_six
            and not has_tag(defender.global_effects, "undead_or_possessed")
            or has_tag(effect, "poison.spider-spittle") and defender_state.condition == Condition.STANDING)):
        defender_state = require_characteristics(defender, defender_state, dice,
            f"{key}.defender", {"T"}, decisions)
        defender_dice.state = defender_state
    if (phases.has_tag(weapon, "weapon.disease-dagger") and natural_hit_six
            and not poison_blocked
            and not phases.has_tag(defender.global_effects, "undead_or_possessed")
            and not phases._characteristic_test(defender_state.toughness, defender_dice, f"{key}.infection")):
        # Infection is an additional automatic wound, not a second dagger hit.
        # The source grants no armour-denial exception; retain ordinary saves.
        infection = EffectSet(tags=("effect.automatic-wound", "effect.no-critical"),
            automatic_hit=True, cannot_be_parried=True, fixed_strength=3)
        attacker_state = replace(attacker_state,
            resources_spent=attacker_state.resources_spent | attacker_dice.state.resources_spent)
        defender_state = replace(defender_state,
            resources_spent=defender_state.resources_spent | defender_dice.state.resources_spent)
        extra = resolve_reference_attack(attacker, defender, attacker_state, defender_state,
            infection, dice, key=f"{key}.infection-wound", melee_attack=False,
            defences_resolved=True, decisions=decisions)
        from mordheim_combat.modular.aftermath import _react_to_wound
        extra = _react_to_wound(attacker, defender, extra, dice, f"{key}.infection-wound", decisions=decisions)
        if secondary_outcomes is not None:
            secondary_outcomes.append(extra)
        attacker_state, defender_state = extra.attacker, extra.defender
        attacker_dice.state, defender_dice.state = attacker_state, defender_state
        if not attacker_state.active or not defender_state.active:
            return AttackOutcome(attacker_state, defender_state, hit=True, reactions_resolved=True)
    if (phases.has_tag(effect, "poison.spider-spittle") and not poison_blocked
            and defender_state.condition == Condition.STANDING
            and not phases._characteristic_test(
                defender_state.toughness, defender_dice, f"{key}.spider-spittle",
                reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"))):
        defender_state = replace(defender_state, condition=Condition.PARALYZED)
    automatic_wound = (has_tag(effect, "effect.automatic-wound")
        or has_tag(weapon, "effect.wraith-touch")
        or natural_hit_six and has_tag(effect, "mechanic.killing-blow"))
    if not effect.fixed_strength and (not automatic_wound or not effect.ignore_armour):
        attacker_state = require_characteristics(attacker, attacker_state, dice,
            f"{key}.attacker", {"S"}, decisions)
    if not automatic_wound:
        defender_state = require_characteristics(defender, defender_state, dice,
            f"{key}.defender", {"T"}, decisions)
    attacker_dice.state, defender_dice.state = attacker_state, defender_state
    wound_context = prepare_wound_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        hit_roll=6 if natural_hit_six else 0, first_round=first_round, charging=charging, key=f"{key}.wound",
        melee_attack=melee_attack, allow_luck=decisions is None,
    )
    if killing_blow and not (phases.has_tag(effect, "poison.black-lotus") and not poison_blocked):
        # No To Wound die is rolled, so no natural wound six or critical is invented.
        # Black Lotus retains its explicitly permitted critical attempt and
        # existing guaranteed-wound fallback; it is not an ordinary wound roll.
        wound_context = replace(wound_context, automatic=True, reroll=False)
    if (natural_hit_six and phases.has_tag(effect, "poison.black-lotus") and not poison_blocked
            and decisions is not None and not decisions.choose(f"{key}.lotus-critical", wound_context)):
        wound_context = replace(wound_context, automatic=True)
    luck_for_wound = (
        decisions is None and phases.has_tag(effect, "skill.luck")
        and "luck" not in attacker_state.resources_spent
        and not effect.reroll_wounds
    )
    # Trip (The Dark Jester / Confound and Confuse) is the round's chosen
    # alternative for exactly one attack: after a single successful hit the
    # bearer may give up that attack's wound roll and instead trip the
    # opponent on the Jester's D6 of 2+.  The choice and the
    # trip roll are resolved BEFORE the wound step, so no wound die is
    # consumed and a printed wound reroll (Luck, Wound Valour) is never
    # spent on a replaced roll; a 1 leaves the opponent standing and the
    # attack simply ends.
    if (melee_attack and _trip_eligible(attacker, attacker_state, weapon) and decisions is not None
            and defender_state.condition == Condition.STANDING
            and decisions.choose(f"{key}.trip.hit", wound_context)):
        attacker_state = attacker_state.spend("jester.trip")
        if attacker_dice.roll(RollRequest(f"{key}.trip-roll")) >= 2:
            defender_state = replace(defender_state, condition=Condition.KNOCKED_DOWN,
                frenzy=defender_state.frenzy and has_tag(defender.global_effects, "mechanic.persistent-frenzy"))
        return AttackOutcome(attacker_state, defender_state, hit=True,
            hit_roll=hit.roll, hit_target=hit.target, trace=trace)
    attacker_state = replace(attacker_state,
        resources_spent=attacker_state.resources_spent | attacker_dice.state.resources_spent)
    defender_state = replace(defender_state,
        resources_spent=defender_state.resources_spent | defender_dice.state.resources_spent)
    attacker_dice.state = attacker_state
    attacker_dice.rerolled = False
    wound = phases.resolve_wound(wound_context, attacker_dice)
    if attacker_dice.rerolled:
        wound = replace(wound, rerolled=True)
    attacker_state = replace(attacker_state,
        resources_spent=attacker_state.resources_spent | attacker_dice.state.resources_spent)
    if wound.critical and attacker_dice.original_roll is not None:
        wound = replace(wound, critical=attacker_dice.original_roll >= wound_context.critical_threshold)
    if luck_for_wound and wound.rerolled:
        attacker_state = attacker_state.spend("luck")
    trace += (Phase.WOUND,)
    if not wound.success and phases.has_tag(attacker.global_effects, "mechanic.mark-of-the-old-ones") and "mark-of-the-old-ones" not in attacker_state.resources_spent:
        attacker_state = attacker_state.spend("mark-of-the-old-ones")
        wound = replace(wound, success=True, roll=wound.target, critical=False)
    if not wound.success:
        if (melee_attack and has_tag(attacker.global_effects, "mechanic.titanic-strength")
                and defender_state.condition == Condition.STANDING):
            defender_state = require_characteristics(defender, defender_state, dice,
                f"{key}.defender", {"S"}, decisions)
            defender_dice.state = defender_state
        if (melee_attack and phases.has_tag(attacker.global_effects, "mechanic.titanic-strength")
                and defender_state.condition == Condition.STANDING
                and not phases._characteristic_test(defender_state.strength, defender_dice,
                    f"{key}.titanic-strength", reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"))):
            defender_state = replace(defender_state, condition=Condition.KNOCKED_DOWN,
                frenzy=defender_state.frenzy and has_tag(defender.global_effects, "mechanic.persistent-frenzy"))
        return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace,
            barrage_available=phases.has_tag(weapon, "weapon.rapier"))
    if phases.has_tag(effect, "poison.manbane") and not poison_blocked and wound.roll == 1:
        return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace)
    if (phases.has_tag(weapon, "effect.wraith-touch") and attacker.fighter_id == "restless-dead:liche"
            and attacker_state.wounds < attacker.characteristics.wounds
            and decisions is not None and decisions.choose(f"{key}.wraith-heal", attacker)):
        attacker_state = replace(attacker_state, wounds=attacker_state.wounds + 1)
    if (melee_attack and first_round and charging
            and has_tag(effect, "mechanic.achilles-heel")
            and has_tag(effect, "condition.stampede-active") and wound.roll >= 5):
        effect = replace(effect, ignore_armour=True)
    if wound.critical:
        if phases.has_tag(defender.global_effects, "skill.hardy-constitution") and defender_dice.roll(
            RollRequest(f"{key}.hardy-constitution")
        ) >= 5:
            wound = replace(wound, critical=False)
        else:
            attacker_state = replace(attacker_state, critical_available=False)
    critical = phases.CriticalResult()
    if wound.critical:
        critical = phases.resolve_critical(attacker_dice, key=f"{key}.critical",
            modifier=effect.critical_injury_bonus + int(phases.has_tag(effect, "skill.web-of-steel")))
    attacker_state = replace(attacker_state,
        resources_spent=attacker_state.resources_spent | attacker_dice.state.resources_spent)
    defender_state = replace(defender_state,
        resources_spent=defender_state.resources_spent | defender_dice.state.resources_spent)
    return _resolve_wound_damage(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        wound, critical, dice, key=key, first_round=first_round, charging=charging,
        helpless_at_start=helpless_at_start, decisions=decisions, trace=trace,
        melee_attack=melee_attack,
        self_attack=self_attack,
        single_wound=single_wound,
    )


def _resolve_wound_damage(attacker, defender, attacker_state, defender_state, weapon, effect,
                          wound, critical, dice, **options):
    own = OwnedRollDice(dice, attacker, attacker_state, options.get("decisions"))
    self_hit = options.pop("self_attack", False) or (attacker_state is defender_state and (
        attacker is defender or has_tag(weapon, "mechanic.black-hunger-backlash")))
    enemy = own if self_hit else OwnedRollDice(
        dice, defender, defender_state, options.get("decisions"))
    result = _resolve_wound_damage_body(attacker, defender, attacker_state, defender_state,
        weapon, effect, wound, critical, dice, attacker_dice=own, defender_dice=enemy, **options)
    return replace(result,
        attacker=replace(result.attacker, resources_spent=result.attacker.resources_spent | own.state.resources_spent),
        defender=replace(result.defender, resources_spent=result.defender.resources_spent | enemy.state.resources_spent))


def _resolve_wound_damage_body(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, wound: phases.WoundResult,
    critical: phases.CriticalResult, dice: DiceSource, *, key: str,
    first_round: bool, charging: bool, helpless_at_start: bool,
    decisions: DecisionPolicy | None, trace: tuple[Phase, ...],
    single_wound: bool = False, melee_attack: bool = True,
    attacker_dice=None, defender_dice=None,
) -> AttackOutcome:
    """Shared saves, damage and injury for an already established wound."""
    if not effect.fixed_strength and not effect.ignore_armour:
        attacker_state = require_characteristics(attacker, attacker_state, dice,
            f"{key}.attacker", {"S"}, decisions)
        attacker_dice.state = attacker_state
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(
        defender.global_effects, "poison_immune")
    armour_context = prepare_armour_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        first_round=first_round, charging=charging, key=f"{key}.armour",
        melee_attack=melee_attack,
    )
    armour_context = replace(armour_context,
        ignore_armour=armour_context.ignore_armour or critical.ignore_armour)
    daemonic_save = (has_tag(defender.global_effects, "mechanic.daemonic-flesh")
            and not has_tag(effect, "attack.magical") and not has_tag(effect, "attack.blessed")
            and not armour_context.ignore_armour
            and phases.armour_target(armour_context) == defender.natural_armour_save)
    if daemonic_save:
        reject_curse_unmodifiable_save(defender, effect, "Daemonic Flesh")
    armour_dice = SimpleNamespace(roll=defender_dice.unmodifiable) if daemonic_save else defender_dice
    armour = phases.resolve_armour(armour_context, armour_dice)
    trace += (Phase.ARMOUR,)
    # chaos-in-the-streets printed 159, Assassin's Luck: "La suerte del Asesino: los ropajes
    # de asesino eshin permiten repetir las tiradas de salvacion fallidas".  The printed
    # sentence names no cost and no frequency, so the robes' bearer rolls a second armour
    # die after every failed save and the second result stands.  A die that was already
    # re-rolled (the Luck skill of an interactive replay, or any other source) is never
    # re-rolled again, and the free printed re-roll is taken before the once-per-battle
    # Luck skill is spent.
    if (not armour.saved and armour.roll is not None
            and not getattr(armour_dice, "rerolled", False)):
        assassin_luck = phases.has_tag(defender.global_effects, "armour.eshin-assassin-robes")
        defender_luck = (
            not assassin_luck and decisions is None
            and phases.has_tag(defender.global_effects, "skill.luck")
            and "luck" not in defender_state.resources_spent
        )
        if assassin_luck or defender_luck:
            armour = phases.resolve_armour(replace(
                armour_context,
                ignore_armour=armour_context.ignore_armour or critical.ignore_armour,
                key=f"{key}.armour.reroll",
            ), armour_dice)
            if defender_luck:
                defender_state = defender_state.spend("luck")
        if (not armour.saved
                and phases.has_tag(defender.global_effects, "mechanic.mark-of-the-old-ones")
                and "mark-of-the-old-ones" not in defender_state.resources_spent):
            defender_state = defender_state.spend("mark-of-the-old-ones")
            armour = replace(armour, saved=True)
    if armour.saved:
        return AttackOutcome(attacker_state, defender_state, True, wounded=True, saved=True, critical=wound.critical, trace=trace)
    special_context = prepare_special_save_context(
        defender, effect, key=f"{key}.special", defender_state=defender_state,
        melee_attack=melee_attack,
    )
    intrinsic_djinn = (has_tag(defender.global_effects, "mechanic.djinn-ethereal")
        and not has_tag(defender.global_effects, "condition.djinns-luck-active")
        and not special_context.ward_blocked
        and special_context.ward_save - int(has_tag(effect, "condition.djinns-curse-active")) == 5)
    if intrinsic_djinn:
        reject_curse_unmodifiable_save(defender, effect, "Djinn Ethereal")
    special_dice = SimpleNamespace(roll=lambda request:
        defender_dice.unmodifiable(request) if intrinsic_djinn and request.key.endswith(".ward")
        else defender_dice.roll(request))
    special = phases.resolve_special_save(special_context, special_dice)
    trace += (Phase.SPECIAL_SAVE,)
    if special.saved:
        return AttackOutcome(attacker_state, defender_state, True, wounded=True, saved=True, critical=wound.critical, trace=trace)
    if defender.injury_profile == 2 or helpless_at_start:
        defender_state, healed = _mim_regeneration(defender, defender_state, defender_dice, decisions, key)
        if healed:
            return AttackOutcome(attacker_state, defender_state, True, wounded=True,
                damage=1, critical=wound.critical, trace=trace)
        return AttackOutcome(attacker_state, replace(defender_state, condition=Condition.OUT), True, wounded=True, damage=1, critical=wound.critical, trace=trace)
    if single_wound:
        damage = 1
    else:
        weapon_damage = (attacker_dice.roll(RollRequest(f"{key}.damage", effect.damage_die_sides))
                         if effect.damage_die_sides else effect.damage)
        damage = max(1, weapon_damage, critical.damage) * (2 if phases.has_tag(defender.global_effects, "flammable") and phases.has_tag(effect, "attack.fire") else 1)
    if (not single_wound and phases.has_tag(attacker.global_effects, "mechanic.marine-hunter")
            and phases.has_tag(defender.global_effects, "species.aquatic")):
        damage *= 2
    remaining = defender_state.wounds - damage
    if phases.has_tag(effect, "poison.nightshade") and not poison_blocked:
        defender_state = replace(
            defender_state,
            initiative_penalty=defender_state.initiative_penalty + damage,
        )
    defender_state, healed = _mim_regeneration(defender, defender_state, defender_dice, decisions, key)
    if healed:
        return AttackOutcome(attacker_state, defender_state, True, wounded=True,
            damage=damage, critical=wound.critical, trace=trace)
    if phases.has_tag(defender.global_effects, 'mechanic.hillman-lycanthrope') and not defender_state.hillman_wolf:
        # One attempt for each lost Wound; a transformation replaces injury
        # resolution and uses the source's distinct W2 wolf profile.
        for lost in range(damage):
            if defender_dice.roll(RollRequest(f'{key}.lycanthrope.{lost}')) >= 4:
                defender_state = replace(defender_state, hillman_wolf=True,
                    wounds=2, condition=Condition.STANDING, weapon_skill=4,
                    strength=4, toughness=4, initiative=5, attacks=2,
                    parries_remaining=0)
                return AttackOutcome(attacker_state, defender_state, True,
                    wounded=True, damage=damage, critical=wound.critical, trace=trace)
    if remaining > 0:
        defender_state = replace(defender_state, wounds=remaining)
        return AttackOutcome(attacker_state, defender_state, True, wounded=True, damage=damage, critical=wound.critical, trace=trace)
    if defender.injury_profile == 4:
        return AttackOutcome(
            attacker_state, replace(defender_state, wounds=remaining, condition=Condition.OUT),
            True, wounded=True, damage=damage, critical=wound.critical, trace=trace,
        )
    # Backstabber's Injury half: +1 on Injury rolls during the first round of
    # the combat the unseen charge opened; the opponent recovers afterwards.
    injury_context = _injury_context(
        defender, effect, key, defender_state,
        injury_bonus=int(melee_attack and first_round and charging
            and phases.has_tag(attacker.global_effects, "skill.backstabber")
            and phases.has_tag(attacker.global_effects, "condition.unseen-charge")),
    )
    if (phases.has_tag(defender.global_effects, 'mechanic.hillman-lycanthrope')
            and not defender_state.hillman_wolf):
        injury_context = replace(injury_context, modifier=injury_context.modifier - 1)
    if wound.critical:
        injury_context = replace(
            injury_context,
            modifier=injury_context.modifier + critical.injury_modifier,
        )
    injury_count = max(1, damage - max(0, defender_state.wounds - 1))
    injuries = []
    for injury_index in range(injury_count):
        local = replace(injury_context, key=f"{key}.injury.{injury_index}")
        injury = phases.resolve_injury(local, attacker_dice)
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
                replace(local, key=f"{key}.injury.{injury_index}.reroll"), attacker_dice
            )
        if (has_tag(defender.global_effects, 'mechanic.undead-construct')
                and not has_tag(effect, 'attack.magical')
                and not effect.ignore_armour_except_shield_and_skills
                and defender_dice.roll(RollRequest(f'{key}.injury.{injury_index}.undead-construct'))
                    >= 4 + int(has_tag(effect, 'condition.djinns-curse-active'))):
            # The construct ignores this Injury result; it has still lost the
            # actual Wound and this does not create a pre-damage ward save.
            continue
        if has_tag(defender.global_effects, "mechanic.inured-to-pain") and injury.total <= 0:
            # The printed zero ignores this damage, including its lost Wound.
            damage -= 1
            remaining += 1
            if phases.has_tag(effect, "poison.nightshade") and not poison_blocked:
                defender_state = replace(defender_state,
                    initiative_penalty=defender_state.initiative_penalty - 1)
        else:
            injuries.append(injury)
    trace += (Phase.INJURY,)
    if not injuries:
        return AttackOutcome(attacker_state, replace(defender_state, wounds=remaining),
            True, wounded=damage > 0, damage=damage, critical=wound.critical, trace=trace)
    condition = max(injury.condition for injury in injuries)
    if (has_tag(defender.global_effects, 'mechanic.veskit-no-pain')
            and condition != Condition.OUT):
        condition = Condition.STANDING
    if (has_tag(defender.global_effects, 'mechanic.marianna-no-pain-jump-up')
            and has_tag(defender.global_effects, 'skill.jump-up')
            and has_tag(defender.global_effects, 'skill.ignore-pain')
            and condition == Condition.KNOCKED_DOWN):
        condition = Condition.STANDING
    helmet_save = defender.helmet_save
    if (phases.has_tag(defender.global_effects, "mechanic.hard-to-rattle")
            and not phases.has_tag(effect, "attack.fire")):
        helmet_save = min(helmet_save, 4)
    # Basha worsens a helmet reaction, not Thick Skull's replacement reaction.
    if (phases.has_tag(effect, "weapon.skull-busta") and helmet_save <= 6
            and not defender.global_effects.thick_skull):
        helmet_save = 6
    condition = phases.resolve_stun_reaction(phases.StunReactionContext(
        condition, defender.global_effects.thick_skull, helmet_save, key
    ), defender_dice).condition
    if (melee_attack and condition == Condition.STUNNED
            and phases.has_tag(attacker.global_effects, 'mechanic.needle-and-thread')):
        defender_state = replace(defender_state, mouth_sewn=True)
    defender_state = replace(
        defender_state, wounds=remaining, condition=max(defender_state.condition, condition),
        frenzy=defender_state.frenzy and (condition == Condition.STANDING
            or has_tag(defender.global_effects, "mechanic.persistent-frenzy")),
    )
    return AttackOutcome(attacker_state, defender_state, True, wounded=True, damage=damage, critical=wound.critical, trace=trace)
