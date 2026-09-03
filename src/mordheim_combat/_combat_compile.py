"""Compile-time context for the native combat backend.

Every tag decision that the vectorized engine (``mordheim_combat.vectorized``)
makes inside its hot loops depends only on the two fighters and the weapon
being used, so the native engine folds it into scalar flags ONCE per duel.
This module mirrors each of those decisions by reusing the exact Python
helpers of the certified engine (``_compiled_attack_effect``,
``_critical_wound_threshold``, ``special_save_targets``, ``_parry_capacity``,
``_optional_phase_plan``).  The result is a plain nested dict consumed by the
Cython core in ``_combat_native``.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache

from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
from mordheim_combat.vectorized import _compiled_attack_effect
from mordheim_combat.vectorized import _critical_wound_threshold
from mordheim_combat.vectorized import _optional_phase_plan
from mordheim_combat.vectorized import _parry_capacity
from mordheim_combat.vectorized import has
from mordheim_combat.vectorized import special_save_targets
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet

#: Capacity gates the compiled core can handle (checked by ``supports_plan``).
MAX_EXTRA_ATTACKS = 8
MAX_RANDOM_CHARACTERISTICS = 8


class NotSupported(RuntimeError):
    """Raised when a duel plan exceeds the compiled core's capacity."""


def _values(effect: EffectSet) -> tuple[int, ...]:
    return tuple(int(getattr(effect, name)) for name in EFFECT_VALUE_FIELDS)


def _ignore_unarmed(effect: EffectSet) -> bool:
    from mordheim_combat.phases import ignores_unarmed_penalties
    return ignores_unarmed_penalties(effect)


def _fire_source(opponent: CompiledFighter) -> CompiledFighter:
    """Synthetic attacker used by the Recovery-phase fire resolution."""
    fire = EffectSet(
        tags=("attack.fire", "effect.no-critical"), fixed_strength=4,
        automatic_hit=True, cannot_be_parried=True,
    )
    return replace(
        opponent, main_weapon=fire, off_hand=None,
        global_effects=EffectSet(), extra_attacks=(),
    )


def _constructed(tags=(), **values) -> EffectSet:
    return EffectSet(tags=tuple(tags), **values)


# ---------------------------------------------------------------------------
# Per-attack-source compile.  ``attacker``/``defender`` are CompiledFighters;
# ``weapon`` is an EffectSet that will be handed to ``_resolve_weapon``.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=4096)
def compile_source(attacker: CompiledFighter, defender: CompiledFighter,
                   weapon: EffectSet) -> dict:
    """Fold every tag decision for one (attacker, defender, weapon) triple."""
    weapon_c, effect, unarmed_adjustment = _compiled_attack_effect(
        attacker, defender, weapon,
    )
    g = attacker.global_effects
    dg = defender.global_effects
    poison_blocked = dg.poison_immunity or has(dg, "poison_immune")
    axe_group = ("weapon.axe", "weapon.dwarf-axe", "weapon.double-handed-weapon")
    sword_group = ("weapon.sword", "weapon.scimitar", "weapon.weeping-blades")

    knife_fighting = bool(
        has(effect, "skill.knife-fighting")
        and (has(weapon_c, "weapon.dagger") or has(weapon_c, "weapon.yambiya"))
    )
    sigmarite_bonus = bool(
        has(weapon_c, "weapon.sigmarite-hammer") and has(dg, "undead_or_possessed")
    )
    mounted_only = any(
        has(weapon_c, tag) for tag in ("weapon.lance", "weapon.boar-spear")
    )
    retain_flail = bool(
        has(effect, "mechanic.retain-flail-morning-star-strength-bonus")
        and any(has(weapon_c, tag) for tag in ("weapon.flail", "weapon.morning-star"))
    )
    berserk_charge = bool(
        has(effect, "rule.berserk-charge")
        and any(has(weapon_c, tag) for tag in axe_group)
    )
    weapons_north = bool(
        has(effect, "skill.weapons-of-the-north")
        and any(has(weapon_c, tag) for tag in axe_group)
    )
    axe_expert = bool(
        has(effect, "skill.axe-expert")
        and (has(weapon_c, "weapon.axe") or has(weapon_c, "weapon.dwarf-axe"))
    )
    expert_swordsman = bool(
        has(effect, "skill.expert-swordsman")
        and any(has(weapon_c, tag) for tag in sword_group)
    )
    crack_shot = bool(
        has(effect, "skill.crack-shot")
        and (has(weapon_c, "weapon.pistol") or has(weapon_c, "weapon.duelling-pistol"))
    )
    dagger_master = bool(
        has(g, "dagger_master")
        and (has(weapon_c, "weapon.dagger") or has(weapon_c, "weapon.yambiya"))
    )
    energy_focus = bool(
        has(effect, "mechanic.energy-focus")
        and any(has(weapon_c, tag) for tag in ("weapon.fist", "weapon.natural-attacks"))
    )
    energy_focus_strength = bool(
        energy_focus and effect.energy_focus_attacks
    )
    amazon_enemy = any(
        tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
        for tag in dg.tags
    )
    amazon = bool(
        has(g, "mechanic.amazon-isolationists") and amazon_enemy
    )
    spiritual = has(g, "spiritual_weapons")

    flags = {
        "unarmed": bool(unarmed_adjustment),
        "knife_fighting": knife_fighting,
        "sigmarite": sigmarite_bonus,
        "mounted_only": mounted_only,
        "first_round_bonus_always": bool(
            has(effect, "skill.tireless") or has(effect, "skill.mighty-biceps")
            or retain_flail
        ),
        "scorpion_tail_poison": bool(
            has(weapon_c, "rule.scorpion-tail") and poison_blocked
        ),
        "energy_focus_strength": energy_focus_strength,
        "berserker": has(effect, "skill.berserker"),
        "ferocious": has(g, "skill.ferocious-charge"),
        "sweep": bool(has(effect, "skill.sweep") and weapon_c.two_handed),
        "putrid": bool(
            has(dg, "rule.putrid-stench") and has(g, "undead_or_possessed")
        ),
        "bellowing": has(dg, "skill.bellowing-battle-roar"),
        "cloud_flies": has(dg, "cloud_of_flies"),
        # Hit-modifier arithmetic is linear: fold the defender-side extras.
        # ``bellowing`` only applies on the first round and is applied by the
        # core when ``first_round`` is set.
        "hit_mod_base": 0,
        "reroll_base": bool(effect.reroll_hits),
        "reroll_charge": bool(
            effect.charge_reroll_hits or berserk_charge or dagger_master
            or has(effect, "skill.infallible")
        ),
        "reroll_charge_fr": bool(axe_expert or expert_swordsman),
        "reroll_fr_all": bool(
            has(effect, "skill.hatred") or crack_shot
            or has(effect, "skill.duellist") or amazon
        ),
        "reroll_all": weapons_north,
        "luck": has(effect, "skill.luck"),
        "virtue": has(effect, "skill.virtue-of-valour"),
        "auto_wound_six": bool(
            (has(effect, "poison.black-lotus") and not poison_blocked)
            or has(effect, "wight_blades")
        ),
        "automatic_wound_tag": has(effect, "effect.automatic-wound"),
        "monster_slayer": has(effect, "skill.monster-slayer"),
        "monster_slayer_eff": has(
            effect, "skill.monster-slayer-effective-strength-armour"
        ),
        "rapier": has(weapon_c, "weapon.rapier"),
        "manbane": bool(has(effect, "poison.manbane") and not poison_blocked),
        "hardy": has(dg, "skill.hardy-constitution"),
        "magical": has(effect, "attack.magical"),
        "no_critical": has(effect, "effect.no-critical"),
        "kusara": has(weapon_c, "weapon.kusara-kama"),
        "chained": has(weapon_c, "weapon.chained-squig"),
        "anvil": has(effect, "mechanic.anvil-head"),
        "counter_cutlass": bool(
            not has(weapon_c, "effect.cutlass-counter")
            and (has(defender.main_weapon, "weapon.cutlass")
                 or bool(defender.off_hand and has(defender.off_hand, "weapon.cutlass")))
        ),
        "flammable_double": bool(
            has(dg, "flammable") and has(effect, "attack.fire")
        ),
        "nightshade": bool(
            has(effect, "poison.nightshade") and not poison_blocked
        ),
        "spider_spittle": bool(
            has(effect, "poison.spider-spittle") and not poison_blocked
        ),
        "web_of_steel": has(effect, "skill.web-of-steel"),
        "poisonous_injury": bool(
            has(effect, "poisonous_injury") and not poison_blocked
        ),
        "head_crusher": has(effect, "skill.head-crusher"),
        "fire": has(effect, "attack.fire"),
        "horned_one": has(weapon_c, "rule.horned-one"),
    }
    flags["hit_mod_base"] = int(
        effect.hit_modifier + dg.incoming_hit_modifier
        + int(flags["putrid"]) - int(flags["cloud_flies"])
    )

    ward, regeneration = special_save_targets(defender, effect)
    threshold = _critical_wound_threshold(effect, weapon_c, poison_blocked)
    if spiritual:
        threshold = 5
    return {
        "weapon": _values(weapon_c),
        "effect": _values(effect),
        "flags": flags,
        "critical_threshold": int(threshold),
        "ignition": int(
            min(effect.ignition_threshold, dg.caught_fire_threshold)
            if effect.ignition_threshold <= 6 else 7
        ),
        "ward": int(ward),
        "regeneration": int(regeneration),
        "damage": int(max(1, effect.damage)),
    }


# ---------------------------------------------------------------------------
# Fighter-level compile (both roles: attacker of ``foe`` and defender).
# ---------------------------------------------------------------------------


def _parry_flags(me: CompiledFighter) -> dict:
    g = me.global_effects
    main, off = me.main_weapon, me.off_hand
    parry = bool(
        main.parry or (off is not None and off.parry) or g.parry
        or has(g, "skill.miniath")
    )
    parry = parry or bool(
        has(g, "skill.axe-master")
        and (has(main, "weapon.axe") or bool(off and has(off, "weapon.axe")))
    )
    parry = parry or bool(
        has(g, "skill.shield-mastery") and bool(off and has(off, "defence.shield"))
    )
    sword = has(main, "weapon.sword") or bool(off and has(off, "weapon.sword"))
    dwarf_axes = bool(
        has(main, "weapon.dwarf-axe") and bool(off and has(off, "weapon.dwarf-axe"))
    )
    miniath_reroll = bool(
        has(g, "skill.miniath") and (main.parry or bool(off and off.parry))
    )
    sword_and_buckler = bool(
        sword and (has(g, "defence.buckler") or bool(off and has(off, "defence.buckler")))
    )
    sword_master_reroll = bool(
        has(g, "skill.sword-master")
        and (not has(g, "rule.dwarf-axe-parry-reroll") or dwarf_axes)
    )
    return {
        "parry": parry,
        "match_allowed": any(
            has(g, tag) for tag in (
                "skill.sword-master", "skill.swordmaster",
                "skill.defensive-stance", "skill.unbeatable-warrior",
            )
        ),
        "starblade": bool(
            has(main, "weapon.starblade") or bool(off and has(off, "weapon.starblade"))
        ),
        "can_parry_six": has(g, "rule.blood-dragon-sword-master"),
        "dwarf_axes": dwarf_axes,
        "parry_reroll": bool(
            miniath_reroll or sword_and_buckler or sword_master_reroll
            or has(main, "weapon.double-bladed-sword")
        ),
    }


def _compile_fighter(me: CompiledFighter, foe: CompiledFighter) -> dict:
    g = me.global_effects
    main, off = me.main_weapon, me.off_hand
    if len(me.extra_attacks) > MAX_EXTRA_ATTACKS:
        raise NotSupported("too many extra attacks for the native backend")
    if len(me.random_characteristics) > MAX_RANDOM_CHARACTERISTICS:
        raise NotSupported("too many random characteristics for the native backend")
    parry = _parry_flags(me)
    stats = me.characteristics
    result = {
        "ws": stats.weapon_skill,
        "s": stats.strength,
        "t": stats.toughness,
        "w": stats.wounds,
        "ini": stats.initiative,
        "a": stats.attacks,
        "armour_save": int(me.armour_save),
        "natural_armour_save": int(me.natural_armour_save),
        "natural_armour_worst_save": int(me.natural_armour_worst_save),
        "helmet_save": int(me.helmet_save),
        "injury_profile": int(me.injury_profile),
        "ballistic_skill": int(me.ballistic_skill),
        "off_hand_attacks": bool(me.off_hand_attacks),
        "mounted": bool(me.mounted),
        "parry_capacity": int(_parry_capacity(me)),
        # defender-side save / injury flags
        "natural_armour_unmodified": bool(me.natural_armour_unmodified),
        "natural_armour_negated_by_magic": bool(g.natural_armour_negated_by_magic),
        "armour_cannot_be_ignored": bool(g.armour_cannot_be_ignored),
        "armour_save_floor": int(g.armour_save_floor),
        "out_of_action_threshold": int(g.out_of_action_threshold),
        "caught_fire_threshold": int(g.caught_fire_threshold),
        "poison_immune": bool(g.poison_immunity or has(g, "poison_immune")),
        "incoming_strength_modifier": int(g.incoming_strength_modifier),
        "incoming_attacks_modifier": int(g.incoming_attacks_modifier),
        "thick_skull": bool(g.thick_skull),
        "injury_reroll_out": has(g, "injury_reroll_out"),
        "hard_to_kill": bool(
            has(g, "skill.hard-to-kill") or has(g, "skill.tough-as-steel")
        ),
        "concussion_immune": has(g, "concussion_immune"),
        "fragile": has(g, "fragile_halflings"),
        "survivor": has(g, "survivor"),
        "ignore_pain": has(g, "skill.ignore-pain"),
        "jump_up": has(g, "skill.jump-up"),
        "mandrake": has(g, "preparation.mandrake-root"),
        "acid_blood": has(g, "acid_blood"),
        "contagious": has(g, "contagious"),
        "flammable": has(g, "flammable"),
        "spider_infested": has(g, "mechanic.spider-infested"),
        # attacker-side ability flags (each vs ``foe`` where relevant)
        "bull_charge": has(g, "mechanic.bull-charge"),
        "body_slam": has(g, "mechanic.body-slam"),
        "unpredictable": has(g, "mechanic.unpredictable-attack"),
        "bear_hug": bool(g.bear_hug),
        "spawn": has(g, "mechanic.spawn-special-attacks"),
        "netter": has(g, "mechanic.netter"),
        "spines": has(g, "spines"),
        "black_hunger": has(g, "mechanic.black-hunger"),
        "force_of_will": has(g, "mechanic.force-of-will"),
        "entangle": bool(
            has(main, "weapon.chained-squig")
            or bool(off and has(off, "weapon.chained-squig"))
        ),
        "can_burn": None,  # filled by compile_duel with the foe's ignition view
        "serpent_whip": has(main, "weapon.serpent-whip"),
        "boar_spear": has(main, "weapon.boar-spear"),
        "sigmar_effective": bool(
            has(g, "skill.sigmar-s-sign") and has(foe.global_effects, "undead_or_possessed")
        ),
        "animal_friendship_effective": bool(
            has(g, "animal_friendship") and has(foe.global_effects, "species.animal")
        ),
        "undead_or_possessed": has(g, "undead_or_possessed"),
        "ferocious_charge": has(g, "skill.ferocious-charge"),
        "mark": has(g, "mechanic.mark-of-the-old-ones"),
        "blessed": has(g, "skill.blessed-sight"),
        "amazon": bool(has(g, "mechanic.amazon-isolationists") and any(
            tag.startswith("band.lizardmen") or "lustria-lizardmen" in tag or "norse" in tag
            for tag in foe.global_effects.tags
        )),
        "spiritual_weapons": has(g, "spiritual_weapons"),
        "strike_skinks_always": bool(
            has(g, "mechanic.strike-first-vs-skinks-always")
            and has(foe.global_effects, "species.skink")
        ),
        "strike_skinks_first": bool(
            has(g, "mechanic.strike-first-vs-skinks-first-round")
            and has(foe.global_effects, "species.skink")
        ),
        "lightning_reflexes": has(g, "skill.lightning-reflexes"),
        "always_strikes_first": has(g, "skill.always-strikes-first"),
        "strongman": bool(g.strongman and main.two_handed and main.priority < 0),
        "long_boat_hook": has(main, "weapon.long-boat-hook"),
        "trident": has(main, "weapon.trident"),
        # attack-count scalars
        "attacks_bonus_total": int(
            g.attacks_bonus + main.attacks_bonus + (off.attacks_bonus if off else 0)
        ),
        "extra_weapon_attack": int(me.off_hand_attacks or main.paired),
        "fist_penalized": bool(
            has(main, "weapon.fist") and not _ignore_unarmed(g)
        ),
        "unarmed_bonus": bool(
            has(g, "skill.unarmed-fighting") and has(main, "weapon.fist")
        ),
        "art_bonus": bool(
            has(g, "skill.art-of-silent-death")
            and (has(main, "weapon.fist") or has(main, "weapon.fighting-claws"))
        ),
        "inspiring": has(g, "skill.inspiring-sermon"),
        "first_round_attacks_bonus": int(main.first_round_attacks_bonus),
        "frenzy_effect": bool(g.frenzy),
        "vomit": has(main, "weapon.vomit-attack"),
        "sweep_main": bool(has(g, "skill.sweep") and main.two_handed),
        "main_pistol": bool(
            has(main, "weapon.pistol") or has(main, "weapon.duelling-pistol")
        ),
        "off_pistol": bool(
            off is not None
            and (has(off, "weapon.pistol") or has(off, "weapon.duelling-pistol"))
        ),
        "charge_attacks_bonus": int(g.charge_attacks_bonus),
        "first_round_charge_attacks_bonus": int(g.first_round_charge_attacks_bonus),
        "body_bull_anvil": bool(
            has(g, "mechanic.body-slam") or has(g, "mechanic.bull-charge")
            or has(g, "mechanic.anvil-head")
        ),
        "death_blow": bool(has(g, "mechanic.death-blow") and stats.attacks >= 2),
        "energy_focus_active": bool(
            has(g, "mechanic.energy-focus")
            and any(has(main, tag) for tag in ("weapon.fist", "weapon.natural-attacks"))
        ),
        "energy_focus_attacks": int(g.energy_focus_attacks),
        "maddened": has(g, "maddened_with_pain"),
        # priority scalars
        "weapon_priority": int(main.priority),
        "priority_global": int(g.priority),
        "initiative_bonus_total": int(
            g.initiative_bonus + main.initiative_bonus
            + (off.initiative_bonus if off else 0)
        ),
        # initialize scalars
        "base_wounds": int(stats.wounds + int(has(g, "skill.monstrous"))),
        "toughness_bonus": int(g.toughness_bonus),
        "frenzy_init": bool(g.frenzy),
        "lucky_charm_init": has(g, "defence.lucky-charm"),
        "crimson_shade": has(g, "preparation.crimson-shade"),
        "disability": has(g, "mechanic.disability"),
        # parry flags (defender role)
        **{f"parry_{key}": value for key, value in parry.items()},
        "random_characteristics": list(me.random_characteristics),
    }
    return result


# ---------------------------------------------------------------------------
# Duel-level compile
# ---------------------------------------------------------------------------


def compile_duel(first: CompiledFighter, second: CompiledFighter) -> dict:
    """Build the full immutable context consumed by the native batch core."""
    optional = _optional_phase_plan(first, second)
    fire_effect = _constructed(
        ("attack.fire", "effect.no-critical"), fixed_strength=4,
        automatic_hit=True, cannot_be_parried=True,
    )
    entangle_effect = _constructed(
        ("effect.chained-squig-entangle",), fixed_strength=3, automatic_hit=True,
    )
    hug_effect = _constructed(
        ("effect.automatic-wound", "effect.no-critical"),
        automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
    )
    acid_effect = _constructed(
        ("rule.acid-blood", "effect.no-critical"), fixed_strength=3,
        automatic_hit=True, cannot_be_parried=True,
    )
    counter_effect = _constructed(("effect.cutlass-counter",))
    spines_effect = _constructed(
        ("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True,
    )
    backlash_effect = _constructed(
        ("mechanic.black-hunger-backlash", "effect.no-critical"), fixed_strength=3,
        automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
    )
    bull_effect = _constructed(("mechanic.bull-charge",), hit_modifier=1)
    body_effect = _constructed(
        ("mechanic.body-slam",), strength_bonus=1, hit_modifier=1,
    )

    def sources(me, foe):
        main_base = (
            me.main_weapon_without_poison
            if (foe.global_effects.poison_immunity or has(foe.global_effects, "poison_immune"))
            and me.main_weapon_without_poison is not None
            else me.main_weapon
        )
        result = {"main": compile_source(me, foe, main_base)}
        unpredictable = has(me.global_effects, "mechanic.unpredictable-attack")
        result["unpredictable"] = (
            compile_source(
                me, foe,
                merge_effects(
                    main_base,
                    _constructed(
                        ("mechanic.unpredictable-attack",), cannot_be_parried=True,
                    ),
                ),
            )
            if unpredictable else None
        )
        result["off"] = (
            compile_source(me, foe, me.off_hand) if me.off_hand is not None else None
        )
        result["extras"] = [compile_source(me, foe, extra) for extra in me.extra_attacks]
        return result

    def reactions(me, foe):
        return {
            "bull": compile_source(me, foe, bull_effect),
            "body": compile_source(me, foe, body_effect),
            "spines": compile_source(me, foe, spines_effect),
            "backlash": compile_source(me, me, backlash_effect),
            "fire": compile_source(_fire_source(me), foe, fire_effect),
            "entangle": compile_source(me, foe, entangle_effect),
            "hug": compile_source(me, foe, hug_effect),
            "acid": compile_source(me, foe, acid_effect),
            "counter": compile_source(me, foe, counter_effect),
        }

    first_ctx = _compile_fighter(first, second)
    second_ctx = _compile_fighter(second, first)
    first_ctx["can_burn"] = bool(optional.first_can_burn)
    second_ctx["can_burn"] = bool(optional.second_can_burn)
    return {
        "first": first_ctx,
        "second": second_ctx,
        "sources_first": sources(first, second),
        "sources_second": sources(second, first),
        "reactions_first": reactions(first, second),
        "reactions_second": reactions(second, first),
    }
