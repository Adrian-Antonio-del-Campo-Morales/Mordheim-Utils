"""combat: Prepared per-attack contexts shared by orchestration and verification."""
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
    if first_round and phases.has_tag(weapon, "weapon.spear") and phases.has_tag(effect, "mechanic.seaguard-spear-master"):
        strength += 1
    if first_round and charging:
        mounted_only = any(phases.has_tag(weapon, tag) for tag in ("weapon.lance", "weapon.boar-spear"))
        if not mounted_only or attacker.mounted:
            strength += effect.charge_strength_bonus
    if (has_tag(defender.global_effects, "mechanic.foul-odour")
            and has_tag(effect, "attack.fire")):
        strength += 1
    if phases.has_tag(weapon, "rule.eagle-friend"):
        strength = 3  # Directed bird weapon: never the Priestess's personal Strength bonuses.
    armour_strength = strength + effect.armour_strength_modifier
    if phases.has_tag(effect, "mechanic.wolf-rat-bite"):
        # Its printed S4 wounds normally but contributes no armour modifier.
        strength = 4
        armour_strength = 3
    strength = max(1, strength + defender.global_effects.incoming_strength_modifier)
    return strength, armour_strength


def _hit_reroll(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
    effect: EffectSet, first_round: bool, charging: bool, *, frenzy: bool = False,
) -> bool:
    pride = False
    if first_round and has_tag(effect, "mechanic.dueling-pride"):
        if not any(tag.startswith("house-guard.") for tag in effect.tags):
            raise ValueError("Dueling Pride requires an explicit House Guard house")
        if has_tag(effect, "house-guard.fierezza") and has_tag(effect, "fighter-kind.hero"):
            if not any(tag.startswith("fighter-kind.") for tag in defender.global_effects.tags):
                raise ValueError("Dueling Pride requires the opponent's explicit fighter role")
            pride = has_tag(defender.global_effects, "fighter-kind.hero")
    enemy_tags = defender.global_effects.tags
    amazon_enemy = any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in enemy_tags
    )
    kindred = False
    if first_round and not frenzy and has_tag(effect, "mechanic.kindred-hatred") and "species.vampire" in enemy_tags:
        bloodlines = [tag for tag in enemy_tags if tag.startswith("vampire-bloodline.")]
        if len(bloodlines) != 1:
            raise ValueError("Kindred Hatred requires the opposing Vampire's explicit bloodline")
        kindred = bloodlines[0] != "vampire-bloodline.strigoi"
    psychology_allowed = not phases.has_tag(attacker.global_effects, "mechanic.psychology-immunity")
    hatred = first_round and psychology_allowed and (
        phases.has_tag(effect, "skill.hatred")
        or has_tag(effect, "skill.righteous-fury") and (
            bool({"species.skaven", "nature.undead", "nature.possessed",
                  "species.beastman", "species.dark-elf"}.intersection(enemy_tags))
            or "warband-group.chaotic" in enemy_tags
            or "identity.chaos-follower" in enemy_tags
            or "warband-group.evil" in enemy_tags and not bool(
                {"warband-group.human", "warband-group.human-mercenary"}.intersection(enemy_tags))
        )
        or has_tag(effect, "mechanic.noble-disdain") and "condition.ranged-armed" in enemy_tags
        or has_tag(effect, "mechanic.hatred-human-warband") and bool(
            {"warband-group.human", "warband-group.human-mercenary", "warband-group.chaos-human"}.intersection(enemy_tags))
        or has_tag(effect, "mechanic.ulric-intense-rivals") and "identity.ulric-rival" in enemy_tags
        or has_tag(effect, "mechanic.hatred-chaotic-warband") and "warband-group.chaotic" in enemy_tags
        or any(has_tag(effect, tag) and any(f"species.{species}" in enemy_tags for species in targets)
            for tag, targets in (("mechanic.hatred-orcs-goblins", ("orc", "goblin")),
                                 ("mechanic.hatred-skaven", ("skaven",)),
                                 ("mechanic.hatred-dwarfs", ("dwarf",)),
                                 ("mechanic.hatred-skaven-orcs-goblins", ("skaven", "orc", "goblin")),
                                 ("mechanic.hatred-dwarfs-skaven", ("dwarf", "skaven"))))
        or phases.has_tag(effect, "mechanic.hatred-undead") and "nature.undead" in enemy_tags
        or phases.has_tag(effect, "mechanic.hatred-dark-elves") and "species.dark-elf" in enemy_tags
        or phases.has_tag(effect, "mechanic.hatred-high-elves") and "species.high-elf" in enemy_tags
        or phases.has_tag(effect, "mechanic.amazon-isolationists") and amazon_enemy
    )
    return bool(
        effect.reroll_hits
        or pride
        or first_round and has_tag(effect, "mechanic.pikewall")
        and has_tag(effect, "condition.being-charged") and weapon.priority > 0
        or charging and effect.charge_reroll_hits
        or charging and phases.has_tag(effect, "rule.berserk-charge") and (
            any(phases.has_tag(weapon, tag) for tag in (
                "weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon",
            ))
        )
        or hatred
        or kindred
        or charging and phases.has_tag(effect, "skill.infallible")
        or charging and first_round and phases.has_tag(effect, "skill.axe-expert") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.axe", "weapon.dwarf-axe")
        )
        or charging and first_round and phases.has_tag(effect, "skill.expert-swordsman") and any(
            phases.has_tag(weapon, tag) for tag in ("weapon.sword", "weapon.weeping-blades")
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
            phases.has_tag(effect, "mechanic.blessing-of-morr")
            and phases.has_tag(global_effects, "nature.undead")
        ) + int(
            phases.has_tag(effect, "skill.knife-fighting")
            and any(phases.has_tag(effect, tag) for tag in ("weapon.dagger", "weapon.yambiya"))
        ),
        critical_bonus=0,
        out_threshold=(4 if phases.has_tag(global_effects, "mechanic.bat-injury-chart")
                       else global_effects.out_of_action_threshold),
        injury_profile=defender.injury_profile,
        hard_to_kill=(phases.has_tag(global_effects, "skill.hard-to-kill")
                      or phases.has_tag(global_effects, "mechanic.fen-hard-to-kill")
                      and not phases.has_tag(effect, "attack.fire")),
        true_grit=phases.has_tag(global_effects, "skill.tough-as-steel"),
        concussion=effect.concussion,
        shock=phases.has_tag(effect, "weapon.shock-rod"),
        concussion_immune=phases.has_tag(global_effects, "concussion_immune"),
        fragile=phases.has_tag(global_effects, "fragile_halflings"),
        # Poisonous changes injuries inflicted by the attack, not injuries
        # received by the creature carrying the trait.
        poisonous=(phases.has_tag(effect, "poisonous_injury")
                   and not (global_effects.poison_immunity or phases.has_tag(global_effects, "poison_immune"))),
        survivor=phases.has_tag(global_effects, "survivor"),
        initial_condition=(defender_state.condition if defender_state is not None else phases.Condition.STANDING),
        head_crusher=phases.has_tag(effect, "skill.head-crusher"),
        ignore_pain=(phases.has_tag(global_effects, "skill.ignore-pain")
                     and not phases.has_tag(global_effects, "rule.squishy")),
        jump_up=phases.has_tag(global_effects, "skill.jump-up"),
        mandrake=phases.has_tag(global_effects, "preparation.mandrake-root"),
        key=f"{key}.injury",
    )


def prepare_hit_context(
    attacker: CompiledFighter, defender: CompiledFighter,
    attacker_state: FighterState, defender_state: FighterState,
    weapon: EffectSet, effect: EffectSet, *, first_round: bool = False,
    charging: bool = False, helpless_at_start: bool = False, key: str = "hit",
    melee_attack: bool = True,
) -> HitContext:
    """The runtime and semantic tests share this contextual projection."""
    ws = attacker_state.weapon_skill + weapon.weapon_skill_bonus
    if first_round and charging:
        ws += effect.charge_ws_bonus
    modifier = effect.hit_modifier + defender.global_effects.incoming_hit_modifier
    if melee_attack and has_tag(attacker.global_effects, "condition.guiding-dream-target"):
        if not has_tag(defender.global_effects, "fighter-kind.hero"):
            raise ValueError("Guiding Dream requires the nominated opposing model to be a Hero")
        if attacker_state.guiding_dream_result in (2, 3):
            modifier += 1
    if melee_attack and any(has_tag(fighter.global_effects, "condition.snorri-stench")
                            for fighter in (attacker, defender)):
        # All models fighting in contact are in the source's 2-inch aura,
        # including the bearer; unrelated models are outside this 1v1 duel.
        modifier -= 1
    if (has_tag(attacker.global_effects, "mechanic.flesh-peddler")
            and has_tag(attacker.global_effects, "condition.flesh-peddler-mark")):
        if not has_tag(defender.global_effects, "sex.female"):
            raise ValueError("Flesh-Peddler's nominated opponent requires an explicit female fact")
        modifier += 1
    if melee_attack and has_tag(defender.global_effects, "mechanic.unholy-stink"):
        modifier -= 1
    if melee_attack and any(has_tag(effect, tag) for tag in (
            "condition.command.follow-me-active", "condition.righteous-charge-active")):
        modifier += 1
    if (phases.has_tag(weapon, "weapon.hellblade")
            and not any(phases.has_tag(defender.global_effects, tag) for tag in ("nature.undead", "nature.daemon"))):
        modifier += 1
    modifier += int(melee_attack and has_tag(attacker.global_effects, "mechanic.andanti-knowledge")
        and has_tag(defender.global_effects, "species.vampire"))
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
    modifier -= int(melee_attack and has_tag(defender.global_effects, "mechanic.foul-odour")
        and not any(has_tag(attacker.global_effects, tag) for tag in
            ("nature.undead", "nature.possessed", "nature.daemon")))
    if melee_attack and has_tag(defender.global_effects, "mechanic.sigmar-symbol-of-unity"):
        named = any(has_tag(attacker.global_effects, tag) for tag in
                    ("band.witch-hunters", "band.trollheim-witch-hunters", "band.sisters-of-sigmar"))
        mercenary = has_tag(attacker.global_effects, "warband-group.human-mercenary")
        if mercenary and any(has_tag(attacker.global_effects, tag) for tag in
                            ("band.mercenaries", "band.trollheim-mercenaries")) and not any(
                tag.startswith("mercenary-origin.") for tag in attacker.global_effects.tags):
            raise ValueError("Symbol of Unity requires the generic mercenary warband's explicit origin")
        excluded = any(has_tag(attacker.global_effects, tag) for tag in
                       ("mercenary-origin.marienburg", "mercenary-origin.middenheim"))
        modifier -= int(named or (mercenary and not excluded))
    reroll = _hit_reroll(attacker, defender, weapon, effect, first_round, charging, frenzy=attacker_state.frenzy)
    luck = phases.has_tag(effect, "skill.luck") and "luck" not in attacker_state.resources_spent
    defender_ws = defender_state.weapon_skill
    if melee_attack and any(current.active and has_tag(fighter.global_effects, "mechanic.shallya-tranquil-aura")
            for fighter, current in ((attacker, attacker_state), (defender, defender_state))):
        for own, is_attacker in ((attacker, True), (defender, False)):
            if not any(has_tag(own.global_effects, tag) for tag in ("nature.daemon", "nature.undead")):
                if is_attacker:
                    ws = max(0, ws - 1)
                else:
                    defender_ws = max(0, defender_ws - 1)
    return HitContext(
        ws, defender_ws, modifier,
        automatic=effect.automatic_hit or helpless_at_start or defender_state.charm_auto_hit
            or defender_state.condition == phases.Condition.PARALYZED,
        reroll=reroll or luck, key=key, needs_sixes=attacker_state.fear_hit_sixes and melee_attack,
    )


def _supplied_ward(effects: EffectSet) -> int:
    """The special save one effect set supplies on its own."""
    ward = effects.ward_save
    if effects.step_aside:
        ward = min(ward, 4 if phases.has_tag(effects, "skill.vampire-reflexes") else 5)
    if effects.step_aside and phases.has_tag(effects, "skill.elven-agility"):
        ward = min(ward, 4)
    return ward


def prepare_special_save_context(
    defender: CompiledFighter, incoming: EffectSet, *, key: str = "special",
) -> SpecialSaveContext:
    if incoming.ignore_armour_except_shield_and_skills:
        # Printed Ladle clause: "The only saving throws allowed are from shields
        # or skills".  Read the special save from the shield and skill
        # selections alone, so an equipment defence (Enchanted Skins), a
        # mechanic-granted ward or a supplied trait cannot save while a skill's
        # own save (Step Aside, Elven Agility) still resolves.  A save source
        # that only reminds us for mundane attacks keeps that limit.
        allowed = defender.shield_and_skill_effects
        return SpecialSaveContext(
            _supplied_ward(allowed), allowed.regeneration_save,
            ward_blocked=(
                allowed.ward_save_mundane_only and phases.has_tag(incoming, "attack.magical")
            ),
            regeneration_blocked=(
                allowed.regeneration_blocked_by_fire and phases.has_tag(incoming, "attack.fire")
                or allowed.regeneration_blocked_by_blessed and phases.has_tag(incoming, "attack.blessed")
            ),
            key=key,
        )
    ward = _supplied_ward(defender.global_effects)
    ward_blocked = defender.global_effects.ward_save_mundane_only and phases.has_tag(incoming, "attack.magical")
    # This source treats its listed metals as magical only for this save.
    # Do not change the incoming attack's magic status or other wards.
    if (phases.has_tag(defender.global_effects, "mechanic.ghost-pirate-ethereal")
            and not any(phases.has_tag(incoming, tag) for tag in
                        ("attack.magical", "material.gromril", "material.ithilmar", "ammo.silver-bullets"))):
        ward = 4 if ward_blocked else min(ward, 4)
        ward_blocked = False
    if phases.has_tag(defender.global_effects, "dance.shadows-coil-active"):
        ward = 4 if ward_blocked else min(ward, 4)
        ward_blocked = False
    if phases.has_tag(incoming, "attack.magical"):
        for tag, threshold in (("mechanic.gypsy-ward", 5), ("mechanic.magical-void", 4)):
            if phases.has_tag(defender.global_effects, tag):
                ward = threshold if ward_blocked else min(ward, threshold)
                ward_blocked = False
    blocked = (
        defender.global_effects.regeneration_blocked_by_fire and phases.has_tag(incoming, "attack.fire")
        or defender.global_effects.regeneration_blocked_by_blessed and phases.has_tag(incoming, "attack.blessed")
    )
    return SpecialSaveContext(
        ward, defender.global_effects.regeneration_save,
        ward_blocked=ward_blocked,
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
    automatic = (phases.has_tag(effect, "effect.automatic-wound")
        or has_tag(weapon, "effect.wraith-touch") and not any(
            has_tag(defender.global_effects, tag) for tag in ("nature.undead", "nature.possessed")))
    luck = (
        phases.has_tag(effect, "skill.luck")
        and "luck" not in attacker_state.resources_spent
        and not effect.reroll_wounds
    )
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
    if (phases.has_tag(weapon, "weapon.hellblade")
            and max(2, phases.wound_target(strength, defender_state.toughness, maximum) - modifier) <= 4):
        critical_threshold = min(critical_threshold, 5)
    return WoundContext(
        strength, defender_state.toughness, modifier, maximum_target=maximum,
        # Lotus already wounds: its optional critical attempt is not a failed
        # wound eligible for Dark Steel/Sure Strike rerolls.
        automatic=automatic, reroll=(effect.reroll_wounds or luck or (
            phases.has_tag(effect, "skill.wound-valour")
            and defender.characteristics.strength > attacker.characteristics.strength
        )) and not (
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
    dagger_tags = ("weapon.dagger", "weapon.yambiya", "weapon.poisoned-daggers", "weapon.disease-dagger")
    daggers = (attacker.main_weapon, attacker.off_hand)
    dagger_pair = (
        attacker.main_weapon.paired and any(tag in attacker.main_weapon.tags for tag in dagger_tags)
        or attacker.off_hand is not None and all(
            any(tag in hand.tags for tag in dagger_tags) for hand in daggers
        )
    )
    cutthroat = int(phases.has_tag(effect, "skill.cutthroat") and dagger_pair
                   and any(tag in weapon.tags for tag in dagger_tags))
    if phases.has_tag(effect, "skill.monster-slayer-effective-strength-armour") and strength < defender_state.toughness:
        armour_strength = max(armour_strength, defender_state.toughness)
    armour_save = defender.armour_save
    natural_armour_save = defender.natural_armour_save
    natural_armour_worst_save = defender.natural_armour_worst_save
    if effect.ignore_armour_except_shield_and_skills:
        # Printed Ladle clause: only shields and skills may save, so the armour
        # the defender wears, its natural armour and every other provenance are
        # denied while the shield and skill selections keep their own save.
        armour_save = max(1, 7 - defender.shield_and_skill_effects.armour_save_bonus)
        natural_armour_save = 7
        natural_armour_worst_save = 7
    if (phases.has_tag(defender.global_effects, "mechanic.norse-bulwark")
            and phases.has_tag(defender.main_weapon, "weapon.axe")
            and defender.off_hand is not None and phases.has_tag(defender.off_hand, "defence.shield")):
        armour_save = max(2, armour_save - 1)
    ignore_armour = effect.ignore_armour or (
        effect.ignore_armour_against_knocked_down
        and defender_state.condition == phases.Condition.KNOCKED_DOWN
    )
    return ArmourContext(
        armour_save, natural_armour_save,
        natural_armour_worst_save, defender.natural_armour_unmodified,
        armour_strength, effect.armour_penetration + cutthroat,
        effect.target_armour_bonus - (
            weapon.target_armour_bonus
            if phases.has_tag(weapon, "weapon.fist") and phases.ignores_unarmed_penalties(effect) else 0
        ),
        ignore_armour, defender.global_effects.armour_save_floor,
        defender.global_effects.armour_cannot_be_ignored,
        phases.has_tag(effect, "attack.magical"), defender.global_effects.natural_armour_negated_by_magic,
        key=key,
    )
