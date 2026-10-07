"""combat: Reference attack resolution for the modular engine."""
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


def _resolve_reference_attack_once(
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
    defences_only: bool = False,
    parry_allowed: bool = True,
    decisions: DecisionPolicy | None = None,
    barrage_penalty: int = 0,
    secondary_outcomes: list[AttackOutcome] | None = None,
) -> AttackOutcome:
    """Resolve one attack and return new immutable fighter states."""
    if not attacker_state.active or not defender_state.active:
        return AttackOutcome(attacker_state, defender_state)
    if (melee_attack and prepared_hit is None
            and phases.has_tag(attacker.global_effects, "mechanic.honorable")
            and defender_state.condition in (Condition.KNOCKED_DOWN, Condition.STUNNED)):
        return AttackOutcome(attacker_state, defender_state)
    if melee_attack and (stunned_at_start if stunned_at_start is not None else
                         defender_state.condition == Condition.STUNNED and prepared_hit is None):
        return AttackOutcome(attacker_state, replace(defender_state, condition=Condition.OUT))
    if (phases.has_tag(weapon, "effect.wraith-touch")
            and any(phases.has_tag(defender.global_effects, tag) for tag in ("nature.undead", "nature.possessed"))):
        return AttackOutcome(attacker_state, defender_state)
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
        helpless_at_start=helpless_at_start, key=f"{key}.hit", melee_attack=melee_attack,
    )
    hit_context = replace(hit_context, modifier=hit_context.modifier - barrage_penalty)
    reroll = _hit_reroll(attacker, defender, weapon, effect, first_round, charging, frenzy=attacker_state.frenzy)
    luck_available = phases.has_tag(effect, "skill.luck") and "luck" not in attacker_state.resources_spent
    luck_for_hit = luck_available and not reroll
    if prepared_hit is not None:
        hit = prepared_hit
    elif phases.has_tag(effect, "skill.sweep") and weapon.two_handed and not hit_context.needs_sixes:
        passed = phases._characteristic_test(
            defender_state.initiative, dice, f"{key}.sweep",
            reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"),
        )
        from mordheim_combat.phases import HitResult
        hit = HitResult(0, 1 if passed else 6, not passed)
    else:
        hit = phases.resolve_hit(hit_context, dice)
    if (prepared_hit is None and not hit.success and not hit.rerolled
            and first_round and phases.has_tag(weapon, "weapon.spear")
            and phases.has_tag(effect, "mechanic.seaguard-spear-master")
            and "seaguard-spear-master" not in attacker_state.resources_spent
            and (decisions is None or decisions.choose(f"{key}.spear-master", hit))):
        # One chosen failed hit, not one reroll per attack. Declining a miss
        # keeps the resource for a later miss in this same first-round pool.
        hit = replace(phases.resolve_hit(replace(hit_context,
            reroll=False, key=f"{key}.hit.reroll"), dice), rerolled=True)
        attacker_state = attacker_state.spend("seaguard-spear-master")
    # Keep physical die provenance before a replacement success changes its face.
    if natural_hit_six is None:
        natural_hit_six = hit.roll == 6 and not (
            phases.has_tag(effect, "skill.sweep") and weapon.two_handed and not hit_context.needs_sixes
        )
    trace = (Phase.HIT,)
    if luck_for_hit and hit.rerolled:
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
            hit_target=hit.target, trace=trace, natural_hit_six=natural_hit_six,
        )
    if (not defences_resolved and not ethereal_resolved
            and phases.has_tag(defender.global_effects, "mechanic.ethereal-hit-save")
            and not phases.has_tag(effect, "attack.magical")
            and dice.roll(RollRequest(f"{key}.ethereal")) >= 4):
        return AttackOutcome(attacker_state, defender_state, hit=True, hit_roll=hit.roll,
            hit_target=hit.target, saved=True, trace=trace)
    killing_blow = natural_hit_six and phases.has_tag(effect, "mechanic.killing-blow")
    if killing_blow:
        effect = replace(effect, cannot_be_parried=True)
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
            if (any(phases.has_tag(candidate, "weapon.sword-breaker") for candidate in
                    (defender.main_weapon, defender.off_hand or EffectSet()))
                    and any(tag.startswith('weapon.') and tag not in ('weapon.fist', 'weapon.natural-attacks')
                            for tag in weapon.tags)):
                if dice.roll(RollRequest(f"{key}.trap-blade")) >= 4:
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
    if natural_hit_six and phases.has_tag(effect, "trait.spectral-touch"):
        # One extra wound of this attack, not a fresh hit/poison/critical trigger.
        extra_key = f"{key}.spectral-touch"
        extra = _resolve_wound_damage(
            attacker, defender, attacker_state, defender_state, weapon,
            effect,
            phases.WoundResult(0, 0, True, False), phases.CriticalResult(), dice,
            key=extra_key, first_round=first_round, charging=charging,
            helpless_at_start=helpless_at_start, decisions=decisions,
            trace=(Phase.WOUND,), single_wound=True,
        )
        from mordheim_combat.modular.aftermath import _react_to_wound
        extra = _react_to_wound(attacker, defender, extra, dice, extra_key)
        if secondary_outcomes is not None:
            secondary_outcomes.append(extra)
        attacker_state, defender_state = extra.attacker, extra.defender
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
    if ignition <= 6 and dice.roll(RollRequest(f"{key}.ignition")) >= ignition:
        defender_state = replace(defender_state, on_fire=True)
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")
    if (phases.has_tag(weapon, "weapon.disease-dagger") and hit.roll == 6
            and not poison_blocked
            and not phases.has_tag(defender.global_effects, "undead_or_possessed")
            and not phases._characteristic_test(defender_state.toughness, dice, f"{key}.infection")):
        # Infection is an additional automatic wound, not a second dagger hit.
        # The source grants no armour-denial exception; retain ordinary saves.
        infection = EffectSet(tags=("effect.automatic-wound", "effect.no-critical"),
            automatic_hit=True, cannot_be_parried=True, fixed_strength=3)
        extra = resolve_reference_attack(attacker, defender, attacker_state, defender_state,
            infection, dice, key=f"{key}.infection-wound", melee_attack=False,
            defences_resolved=True, decisions=decisions)
        from mordheim_combat.modular.aftermath import _react_to_wound
        extra = _react_to_wound(attacker, defender, extra, dice, f"{key}.infection-wound")
        if secondary_outcomes is not None:
            secondary_outcomes.append(extra)
        attacker_state, defender_state = extra.attacker, extra.defender
        if not attacker_state.active or not defender_state.active:
            return AttackOutcome(attacker_state, defender_state, hit=True, reactions_resolved=True)
    if (phases.has_tag(effect, "poison.spider-spittle") and not poison_blocked
            and defender_state.condition == Condition.STANDING
            and not phases._characteristic_test(
                defender_state.toughness, dice, f"{key}.spider-spittle",
                reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"))):
        defender_state = replace(defender_state, condition=Condition.PARALYZED)
    wound_context = prepare_wound_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        hit_roll=hit.roll, first_round=first_round, charging=charging, key=f"{key}.wound",
    )
    if killing_blow and not (phases.has_tag(effect, "poison.black-lotus") and not poison_blocked):
        # No To Wound die is rolled, so no natural wound six or critical is invented.
        # Black Lotus retains its explicitly permitted critical attempt and
        # existing guaranteed-wound fallback; it is not an ordinary wound roll.
        wound_context = replace(wound_context, automatic=True, reroll=False)
    if (hit.roll == 6 and phases.has_tag(effect, "poison.black-lotus") and not poison_blocked
            and decisions is not None and not decisions.choose(f"{key}.lotus-critical", wound_context)):
        wound_context = replace(wound_context, automatic=True)
    luck_for_wound = (
        phases.has_tag(effect, "skill.luck")
        and "luck" not in attacker_state.resources_spent
        and not effect.reroll_wounds
    )
    wound = phases.resolve_wound(wound_context, dice)
    if luck_for_wound and wound.rerolled:
        attacker_state = attacker_state.spend("luck")
    trace += (Phase.WOUND,)
    if not wound.success and phases.has_tag(attacker.global_effects, "mechanic.mark-of-the-old-ones") and "mark-of-the-old-ones" not in attacker_state.resources_spent:
        attacker_state = attacker_state.spend("mark-of-the-old-ones")
        wound = replace(wound, success=True, roll=wound.target, critical=False)
    if not wound.success:
        if (melee_attack and phases.has_tag(attacker.global_effects, "mechanic.titanic-strength")
                and defender_state.condition == Condition.STANDING
                and not phases._characteristic_test(defender_state.strength, dice,
                    f"{key}.titanic-strength", reroll=phases.has_tag(defender.global_effects, "skill.blessed-sight"))):
            defender_state = replace(defender_state, condition=Condition.KNOCKED_DOWN)
        return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace,
            barrage_available=phases.has_tag(weapon, "weapon.rapier"))
    if phases.has_tag(effect, "poison.manbane") and not poison_blocked and wound.roll == 1:
        return AttackOutcome(attacker_state, defender_state, hit=True, trace=trace)
    if (phases.has_tag(weapon, "effect.wraith-touch") and attacker.fighter_id == "restless-dead:liche"
            and attacker_state.wounds < attacker.characteristics.wounds
            and decisions is not None and decisions.choose(f"{key}.wraith-heal", attacker)):
        attacker_state = replace(attacker_state, wounds=attacker_state.wounds + 1)
    if wound.critical:
        if phases.has_tag(defender.global_effects, "skill.hardy-constitution") and dice.roll(
            RollRequest(f"{key}.hardy-constitution")
        ) >= 5:
            wound = replace(wound, critical=False)
        else:
            attacker_state = replace(attacker_state, critical_available=False)
    critical = phases.CriticalResult()
    if wound.critical:
        critical = phases.resolve_critical(dice, key=f"{key}.critical",
            modifier=effect.critical_injury_bonus + int(phases.has_tag(effect, "skill.web-of-steel")))
    return _resolve_wound_damage(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        wound, critical, dice, key=key, first_round=first_round, charging=charging,
        helpless_at_start=helpless_at_start, decisions=decisions, trace=trace,
    )


def _resolve_wound_damage(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, wound: phases.WoundResult,
    critical: phases.CriticalResult, dice: DiceSource, *, key: str,
    first_round: bool, charging: bool, helpless_at_start: bool,
    decisions: DecisionPolicy | None, trace: tuple[Phase, ...],
    single_wound: bool = False,
) -> AttackOutcome:
    """Shared saves, damage and injury for an already established wound."""
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(
        defender.global_effects, "poison_immune")
    armour_context = prepare_armour_context(
        attacker, defender, attacker_state, defender_state, weapon, effect,
        first_round=first_round, charging=charging, key=f"{key}.armour",
    )
    armour = phases.resolve_armour(replace(armour_context,
        ignore_armour=armour_context.ignore_armour or critical.ignore_armour), dice)
    trace += (Phase.ARMOUR,)
    if not armour.saved and armour.roll is not None:
        defender_luck = (
            phases.has_tag(defender.global_effects, "skill.luck")
            and "luck" not in defender_state.resources_spent
        )
        if defender_luck:
            armour = phases.resolve_armour(replace(
                armour_context,
                ignore_armour=armour_context.ignore_armour or critical.ignore_armour,
                key=f"{key}.armour.reroll",
            ), dice)
            defender_state = defender_state.spend("luck")
        if (not armour.saved
                and phases.has_tag(defender.global_effects, "mechanic.mark-of-the-old-ones")
                and "mark-of-the-old-ones" not in defender_state.resources_spent):
            defender_state = defender_state.spend("mark-of-the-old-ones")
            armour = replace(armour, saved=True)
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
    if single_wound:
        damage = 1
    else:
        weapon_damage = (dice.roll(RollRequest(f"{key}.damage", effect.damage_die_sides))
                         if effect.damage_die_sides else effect.damage)
        damage = max(1, weapon_damage, critical.damage) * (2 if phases.has_tag(defender.global_effects, "flammable") and phases.has_tag(effect, "attack.fire") else 1)
    if (phases.has_tag(attacker.global_effects, "mechanic.marine-hunter")
            and phases.has_tag(defender.global_effects, "species.aquatic")):
        damage *= 2
    remaining = defender_state.wounds - damage
    if phases.has_tag(effect, "poison.nightshade") and not poison_blocked:
        defender_state = replace(
            defender_state,
            initiative_penalty=defender_state.initiative_penalty + damage,
        )
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
            modifier=injury_context.modifier + critical.injury_modifier,
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
    ), dice).condition
    defender_state = replace(
        defender_state, wounds=remaining, condition=max(defender_state.condition, condition),
        frenzy=defender_state.frenzy and condition == Condition.STANDING,
    )
    return AttackOutcome(attacker_state, defender_state, True, wounded=True, damage=damage, critical=wound.critical, trace=trace)
