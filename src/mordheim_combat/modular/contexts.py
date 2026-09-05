"""combat.modular.contexts: responsibility extracted without altering the rules."""
from __future__ import annotations
from mordheim_combat import phases

from mordheim_combat.modular.state import FighterState
from mordheim_combat.phases import ArmourContext
from mordheim_combat.phases import HitContext
from mordheim_combat.phases import InjuryContext
from mordheim_combat.phases import ParryContext
from mordheim_combat.phases import SpecialSaveContext
from mordheim_combat.phases import WoundContext
from mordheim_combat.phases import has_tag
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


def _combined_effect(fighter: CompiledFighter, weapon: EffectSet) -> EffectSet:
    return weapon if phases.has_tag(weapon, "mechanic.body-slam") else merge_effects(weapon, fighter.global_effects)


def weapon_against_opponent(attacker: CompiledFighter, defender: CompiledFighter,
                            weapon: EffectSet) -> EffectSet:
    """Select the poison-free contribution before adding transient attack effects."""
    if not (defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")):
        return weapon
    if weapon == attacker.main_weapon and attacker.main_weapon_without_poison is not None:
        return attacker.main_weapon_without_poison
    if weapon == attacker.off_hand and attacker.off_hand_without_poison is not None:
        return attacker.off_hand_without_poison
    return weapon


def _attack_strength(
    attacker: CompiledFighter, defender: CompiledFighter,
    state: FighterState, weapon: EffectSet, effect: EffectSet,
    first_round: bool, charging: bool,
) -> tuple[int, int]:
    strength = effect.fixed_strength or state.strength + effect.strength_bonus
    if phases.ignores_unarmed_penalties(effect) and phases.has_tag(weapon, "weapon.fist"):
        strength += 1
    if phases.has_tag(effect, "mechanic.energy-focus") and any(
        phases.has_tag(weapon, tag) for tag in ("weapon.fist", "weapon.natural-attacks")
    ):
        strength += effect.energy_focus_attacks
    if phases.has_tag(weapon, "rule.scorpion-tail") and defender.global_effects.poison_immunity:
        strength = 2
    retains = phases.has_tag(effect, "mechanic.retain-flail-morning-star-strength-bonus") and any(
        phases.has_tag(weapon, tag) for tag in ("weapon.flail", "weapon.morning-star")
    )
    if first_round or phases.has_tag(effect, "skill.tireless") or phases.has_tag(effect, "skill.mighty-biceps") or retains:
        strength += weapon.first_round_strength_bonus
    if first_round and charging:
        mounted_only = any(phases.has_tag(weapon, tag) for tag in ("weapon.lance", "weapon.boar-spear"))
        if not mounted_only or attacker.mounted:
            strength += effect.charge_strength_bonus
    armour_strength = strength + effect.armour_strength_modifier
    strength = max(1, strength + defender.global_effects.incoming_strength_modifier)
    return strength, armour_strength


def _hit_reroll(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
    effect: EffectSet, first_round: bool, charging: bool,
) -> bool:
    enemy_tags = defender.global_effects.tags
    amazon_enemy = any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in enemy_tags
    )
    return bool(
        effect.reroll_hits
        or charging and effect.charge_reroll_hits
        or charging and phases.has_tag(effect, "rule.berserk-charge") and (
            any(phases.has_tag(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
            ))
        )
        or first_round and phases.has_tag(effect, "skill.hatred")
        or first_round and phases.has_tag(effect, "mechanic.amazon-isolationists") and amazon_enemy
        or charging and phases.has_tag(effect, "skill.infallible")
        or charging and first_round and phases.has_tag(effect, "skill.axe-expert") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.axe", "weapon.dwarf-axe")
        )
        or charging and first_round and phases.has_tag(effect, "skill.expert-swordsman") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.sword", "weapon.scimitar", "weapon.weeping-blades")
        )
        or first_round and phases.has_tag(effect, "skill.crack-shot") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.pistol", "weapon.duelling-pistol")
        )
        or charging and phases.has_tag(attacker.global_effects, "dagger_master") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.dagger", "weapon.yambiya")
        )
        or phases.has_tag(effect, "skill.weapons-of-the-north") and (
            any(phases.has_tag(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
            ))
        )
        or first_round and phases.has_tag(effect, "skill.duellist")
        or phases.has_tag(effect, "skill.virtue-of-valour")
        and defender.characteristics.strength > attacker.characteristics.strength
    )


def _parry_context(
    defender: CompiledFighter, defender_state: FighterState,
    effect: EffectSet, strength: int, hit_roll: int, key: str,
) -> ParryContext | None:
    if defender_state.parries_remaining <= 0 or defender_state.condition != phases.Condition.STANDING:
        return None
    native_parry = defender.main_weapon.parry or bool(defender.off_hand and defender.off_hand.parry)
    match_allowed = any(phases.has_tag(defender.global_effects, tag) for tag in (
        "skill.sword-master", "skill.swordmaster", "skill.unbeatable-warrior",
    )) or (
        phases.has_tag(defender.global_effects, "skill.defensive-stance") and native_parry
    )
    starblade = any(
        phases.has_tag(weapon, "weapon.starblade")
        for weapon in (defender.main_weapon, defender.off_hand or EffectSet())
    )
    # Miniath grants a parry to any weapon, but only native parrying weapons
    # gain the reroll (Lustria, High Elf Special Skills / Miniath).
    # Hochland Swordmaster changes equality only; it grants no reroll.
    reroll = native_parry and phases.has_tag(defender.global_effects, "skill.miniath")
    sword_and_buckler = (
        any(phases.has_tag(weapon, "weapon.sword") for weapon in (defender.main_weapon, defender.off_hand or EffectSet()))
        and any(phases.has_tag(weapon, "defence.buckler") for weapon in (
            defender.main_weapon, defender.off_hand or EffectSet(), defender.global_effects,
        ))
    )
    dwarf_axes = all(
        phases.has_tag(weapon, "weapon.dwarf-axe")
        for weapon in (defender.main_weapon, defender.off_hand)
        if weapon is not None
    ) and defender.off_hand is not None
    sword_master_reroll = phases.has_tag(defender.global_effects, "skill.sword-master") and (
        not phases.has_tag(defender.global_effects, "rule.dwarf-axe-parry-reroll") or dwarf_axes
    )
    reroll = (reroll or sword_and_buckler or sword_master_reroll or dwarf_axes
              or phases.has_tag(defender.main_weapon, "weapon.fighting-claws"))
    reroll = reroll or phases.has_tag(defender.main_weapon, "weapon.double-bladed-sword")
    return ParryContext(
        hit_roll, strength, defender_state.strength,
        cannot_be_parried=effect.cannot_be_parried,
        match_allowed=match_allowed,
        fixed_target=4 if starblade else None,
        reroll=reroll,
        key=f"{key}.parry",
        can_parry_six=phases.has_tag(defender.global_effects, "rule.blood-dragon-sword-master"),
    )


def _injury_context(defender: CompiledFighter, effect: EffectSet, key: str,
                    defender_state: FighterState | None = None) -> InjuryContext:
    global_effects = defender.global_effects
    return InjuryContext(
        modifier=effect.injury_modifier + int(
            phases.has_tag(effect, "skill.knife-fighting")
            and any(phases.has_tag(effect, tag) for tag in ("weapon.dagger", "weapon.yambiya"))
        ),
        critical_bonus=0,
        out_threshold=global_effects.out_of_action_threshold,
        injury_profile=defender.injury_profile,
        hard_to_kill=phases.has_tag(global_effects, "skill.hard-to-kill"),
        true_grit=phases.has_tag(global_effects, "skill.tough-as-steel"),
        concussion=effect.concussion,
        concussion_immune=phases.has_tag(global_effects, "concussion_immune"),
        fragile=phases.has_tag(global_effects, "fragile_halflings"),
        # Poisonous changes injuries inflicted by the attack, not injuries
        # received by the creature carrying the trait.
        poisonous=(phases.has_tag(effect, "poisonous_injury")
                   and not (global_effects.poison_immunity or phases.has_tag(global_effects, "poison_immune"))),
        survivor=phases.has_tag(global_effects, "survivor"),
        initial_condition=(defender_state.condition if defender_state is not None else phases.Condition.STANDING),
        head_crusher=phases.has_tag(effect, "skill.head-crusher"),
        ignore_pain=phases.has_tag(global_effects, "skill.ignore-pain"),
        jump_up=phases.has_tag(global_effects, "skill.jump-up"),
        mandrake=phases.has_tag(global_effects, "preparation.mandrake-root"),
        key=f"{key}.injury",
    )


def prepare_hit_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, first_round: bool = False,
    charging: bool = False, helpless_at_start: bool = False, key: str = "hit",
) -> HitContext:
    """The runtime and semantic tests share this contextual projection."""
    ws = attacker_state.weapon_skill + weapon.weapon_skill_bonus
    if first_round and charging:
        ws += effect.charge_ws_bonus
    modifier = effect.hit_modifier + defender.global_effects.incoming_hit_modifier
    modifier -= int(phases.has_tag(defender.main_weapon, "weapon.ball-and-chain"))
    if phases.has_tag(defender.global_effects, "rule.putrid-stench") and phases.has_tag(attacker.global_effects, "undead_or_possessed"):
        modifier += 1
    ws += int(phases.has_tag(effect, "skill.knife-fighting") and any(
        phases.has_tag(weapon, tag) for tag in ("weapon.dagger", "weapon.yambiya")
    ))
    if phases.has_tag(weapon, "effect.serpent-staff-power"):
        ws = 4
    modifier += int(charging and phases.has_tag(effect, "skill.berserker"))
    modifier -= int(first_round and charging and phases.has_tag(effect, "skill.ferocious-charge"))
    modifier -= int(first_round and phases.has_tag(defender.global_effects, "skill.bellowing-battle-roar"))
    modifier -= int(phases.has_tag(defender.global_effects, "cloud_of_flies"))
    reroll = _hit_reroll(attacker, defender, weapon, effect, first_round, charging)
    luck = phases.has_tag(effect, "skill.luck") and "luck" not in attacker_state.resources_spent
    return HitContext(
        ws, defender_state.weapon_skill, modifier,
        automatic=effect.automatic_hit or helpless_at_start or defender_state.condition == phases.Condition.PARALYZED,
        reroll=reroll or luck, key=key,
    )


def prepare_special_save_context(
    defender: CompiledFighter, incoming: EffectSet, *, key: str = "special",
) -> SpecialSaveContext:
    ward = defender.global_effects.ward_save
    if defender.global_effects.step_aside:
        ward = min(ward, 4 if phases.has_tag(defender.global_effects, "skill.vampire-reflexes") else 5)
    if defender.global_effects.step_aside and phases.has_tag(defender.global_effects, "skill.elven-agility"):
        ward = min(ward, 4)
    blocked = (
        defender.global_effects.regeneration_blocked_by_fire and phases.has_tag(incoming, "attack.fire")
        or defender.global_effects.regeneration_blocked_by_blessed and phases.has_tag(incoming, "attack.blessed")
    )
    return SpecialSaveContext(
        ward, defender.global_effects.regeneration_save,
        ward_blocked=defender.global_effects.ward_save_mundane_only and phases.has_tag(incoming, "attack.magical"),
        regeneration_blocked=blocked, key=key,
    )


def prepare_wound_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, hit_roll: int = 4,
    first_round: bool = False, charging: bool = False, key: str = "wound",
) -> WoundContext:
    strength, _ = _attack_strength(attacker, defender, attacker_state, weapon, effect, first_round, charging)
    poison_blocked = defender.global_effects.poison_immunity or phases.has_tag(defender.global_effects, "poison_immune")
    automatic = phases.has_tag(effect, "effect.automatic-wound")
    failure_still_wounds = hit_roll == 6 and (
        phases.has_tag(effect, "wight_blades")
        or phases.has_tag(effect, "poison.black-lotus") and not poison_blocked)
    maximum = min(effect.maximum_wound_target, 4) if phases.has_tag(effect, "skill.monster-slayer") else effect.maximum_wound_target
    modifier = effect.wound_modifier + int(
        phases.has_tag(weapon, "weapon.sigmarite-hammer") and phases.has_tag(defender.global_effects, "undead_or_possessed")
    )
    critical_threshold = 5 if (
        phases.has_tag(effect, "poison.wolfsbane") and not poison_blocked
        or phases.has_tag(effect, "mechanic.body-slam")
        or phases.has_tag(effect, "skill.art-of-silent-death")
        or phases.has_tag(attacker.global_effects, "spiritual_weapons")
        or phases.has_tag(effect, "skill.unarmed-critical-strikes") and phases.has_tag(weapon, "weapon.fist")
    ) else 6
    return WoundContext(
        strength, defender_state.toughness, modifier, maximum_target=maximum,
        # Lotus already wounds: its optional critical attempt is not a failed
        # wound eligible for Dark Steel/Sure Strike rerolls.
        automatic=automatic, reroll=effect.reroll_wounds and not (
            hit_roll == 6 and phases.has_tag(effect, "poison.black-lotus") and not poison_blocked
        ),
        critical_threshold=critical_threshold,
        critical_available=attacker_state.critical_available and not phases.has_tag(effect, "effect.no-critical"),
        critical_on_reroll=poison_blocked or not phases.has_tag(effect, "poison.devil-s-toxin"),
        failure_still_wounds=failure_still_wounds,
        key=key,
    )


def prepare_armour_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, first_round: bool = False,
    charging: bool = False, key: str = "armour",
) -> ArmourContext:
    strength, armour_strength = _attack_strength(attacker, defender, attacker_state, weapon, effect, first_round, charging)
    if phases.has_tag(effect, "skill.monster-slayer-effective-strength-armour") and strength < defender_state.toughness:
        armour_strength = max(armour_strength, defender_state.toughness)
    return ArmourContext(
        defender.armour_save, defender.natural_armour_save,
        defender.natural_armour_worst_save, defender.natural_armour_unmodified,
        armour_strength, effect.armour_penetration,
        effect.target_armour_bonus - (
            weapon.target_armour_bonus
            if phases.has_tag(weapon, "weapon.fist") and phases.ignores_unarmed_penalties(effect) else 0
        ),
        effect.ignore_armour, defender.global_effects.armour_save_floor,
        defender.global_effects.armour_cannot_be_ignored,
        phases.has_tag(effect, "attack.magical"), defender.global_effects.natural_armour_negated_by_magic,
        key=key,
    )
