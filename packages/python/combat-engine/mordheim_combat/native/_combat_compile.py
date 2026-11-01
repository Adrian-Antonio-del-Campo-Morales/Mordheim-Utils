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
from mordheim_combat.phases import black_lotus_wounds
from mordheim_combat.vectorized import has
from mordheim_combat.vectorized import special_save_targets
from mordheim_combat.modular.contexts import _darting_steel_parry
from mordheim_combat.modular.contexts import _estalian_parry
from mordheim_combat.modular.contexts import _hit_reroll
from mordheim_combat.modular.contexts import prepare_special_save_context
from mordheim_combat.modular.state import maximum_wounds
from mordheim_combat.vectorized._state import charge_allowed
from mordheim_core.context import PreparedDuelContext
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet

#: The learned Shadow Dances, in ``modular/rounds.py::SHADOW_DANCES`` order.
SHADOW_DANCES = ("whirling-death", "storm-of-blades", "the-shadows-coil", "woven-mist")
#: The two Djinn powers, in the order the oracle offers them.
DJINN_POWERS = ("curse", "luck")

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


# Per-attack-source compile.  ``attacker``/``defender`` are CompiledFighters;
# ``weapon`` is an EffectSet that will be handed to ``_resolve_weapon``.


def _cutthroat(attacker: CompiledFighter, effect: EffectSet, weapon: EffectSet) -> bool:
    """Printed Cutthroat: paired daggers pierce one extra point of armour."""
    dagger_tags = ("weapon.dagger", "weapon.yambiya", "weapon.poisoned-daggers",
                   "weapon.disease-dagger")
    hands = (attacker.main_weapon, attacker.off_hand)
    paired = (
        attacker.main_weapon.paired
        and any(tag in attacker.main_weapon.tags for tag in dagger_tags)
        or attacker.off_hand is not None
        and all(any(tag in hand.tags for tag in dagger_tags) for hand in hands)
    )
    return bool(has(effect, "skill.cutthroat") and paired
                and any(tag in weapon.tags for tag in dagger_tags))


def _flesh_peddler(attacker: CompiledFighter, defender: CompiledFighter) -> bool:
    g = attacker.global_effects
    if not (has(g, "mechanic.flesh-peddler") and has(g, "condition.flesh-peddler-mark")):
        return False
    if not has(defender.global_effects, "sex.female"):
        raise ValueError(
            "Flesh-Peddler's nominated opponent requires an explicit female fact")
    return True


def _symbol_of_unity(attacker: CompiledFighter, defender: CompiledFighter) -> bool:
    """Sigmar's Symbol of Unity blunts the blows of the faithful."""
    g, dg = attacker.global_effects, defender.global_effects
    if not has(dg, "mechanic.sigmar-symbol-of-unity"):
        return False
    named = any(has(g, tag) for tag in ("band.witch-hunters",
                                        "band.trollheim-witch-hunters",
                                        "band.sisters-of-sigmar"))
    mercenary = has(g, "warband-group.human-mercenary")
    if (mercenary and any(has(g, tag) for tag in ("band.mercenaries",
                                                  "band.trollheim-mercenaries"))
            and not any(tag.startswith("mercenary-origin.") for tag in g.tags)):
        raise ValueError(
            "Symbol of Unity requires the generic mercenary warband's explicit origin")
    excluded = any(has(g, tag) for tag in ("mercenary-origin.marienburg",
                                           "mercenary-origin.middenheim"))
    return bool(named or (mercenary and not excluded))


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
    sword_group = ("weapon.sword", "weapon.weeping-blades")

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
        "automatic_wound_tag": bool(
            has(effect, "effect.automatic-wound")
            or (has(weapon_c, "effect.wraith-touch") and not any(
                has(dg, tag) for tag in ("nature.undead", "nature.possessed")))),
        #: The Liche mends itself on the wound its touch steals.
        "wraith_heal": bool(
            has(weapon_c, "effect.wraith-touch")
            and attacker.fighter_id == "restless-dead:liche"),
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
        "disease_dagger": has(weapon_c, "weapon.disease-dagger"),
        "luck_wound": has(effect, "skill.luck"),
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
        # --- ``modular/contexts.py`` modifiers folded per source ----------
        #: Printed Invincible Swordsman: a fixed To Hit target of two.
        "fixed_hit_target": 2 if has(effect, "mechanic.invincible-swordsman") else 0,
        #: The nominated Guiding Dream target hits better on a 2 or 3.
        "guiding_dream_target": has(attacker.global_effects, "condition.guiding-dream-target"),
        #: Shallya's Tranquil Aura lowers the Weapon Skill of every living
        #: model fighting in it, attacker and defender alike.
        "shallya_aura": bool(
            (has(g, "mechanic.shallya-tranquil-aura") or has(dg, "mechanic.shallya-tranquil-aura"))),
        "shallya_self": not any(has(g, tag) for tag in ("nature.daemon", "nature.undead")),
        "shallya_foe": not any(has(dg, tag) for tag in ("nature.daemon", "nature.undead")),
        #: Strength the oracle adds outside the generic EffectSet fields.
        "strength_fr_bonus": int(
            has(weapon_c, "weapon.spear") and has(effect, "mechanic.seaguard-spear-master")),
        "strength_charge_fr_bonus": int(
            has(g, "rule.slay-large-creature") and has(dg, "size.large")),
        #: The Wolf Rat's printed S4 bite contributes no armour modifier.
        "wolf_rat_bite": has(effect, "mechanic.wolf-rat-bite"),
        #: Cutthroat's paired-dagger armour penetration.
        "armour_penetration_extra": int(_cutthroat(attacker, effect, weapon_c)),
        #: Daemonic Flesh keeps no natural armour against a blessed attack.
        "daemonic_flesh_negated": bool(
            has(dg, "mechanic.daemonic-flesh") and has(effect, "attack.blessed")),
        #: Achilles Heel scores its critical even on a wound needing a six.
        "critical_when_needing_six": has(effect, "mechanic.achilles-heel"),
        #: The Hellblade crits on a five once its wound target is four or less.
        "hellblade": has(weapon_c, "weapon.hellblade"),
        #: Wound Valour re-rolls against a stronger printed opponent.
        "reroll_wounds_extra": bool(
            has(effect, "skill.wound-valour")
            and defender.characteristics.strength > attacker.characteristics.strength),
        #: The two printed parry variants.
        "parry_roll_under": _estalian_parry(defender),
        "parry_max_roll": _darting_steel_parry(defender),
        # --- ``modular/attacks.py`` and ``modular/pools.py`` clauses ------
        #: The Honourable strike nothing at a helpless foe.
        "honorable": has(g, "mechanic.honorable"),
        #: The Magic Acorn turns one missed opening blow of a Hero into a hit.
        "magic_acorn": bool(
            has(g, "mechanic.magic-acorn") and has(g, "fighter-kind.hero")),
        #: Marks of Ranald ducks any hit on an unmodifiable six.
        "marks_of_ranald": has(dg, "mechanic.marks-of-ranald"),
        #: Corruption forces one landed blow to be rolled again.
        "corruption": bool(
            has(dg, "mechanic.corruption") and not has(g, "mechanic.psychology-immunity")),
        #: Titanic Strength knocks a standing foe down on a failed wound.
        "titanic_strength": has(g, "mechanic.titanic-strength"),
        #: The Marine Hunter doubles its damage against aquatic prey.
        "marine_hunter": bool(
            has(g, "mechanic.marine-hunter") and has(dg, "species.aquatic")),
        #: Achilles Heel ignores armour on a stampeding charge wound of 5+.
        "achilles_stampede": bool(
            has(effect, "mechanic.achilles-heel")
            and has(effect, "condition.stampede-active")),
        #: The Cursed Hillman's one transformation attempt per lost Wound.
        "lycanthrope": bool(
            has(dg, "mechanic.hillman-lycanthrope")),
        #: The Torturer saps a living victim's Strength with every wound.
        "torturer": bool(
            has(g, "mechanic.torturer") and not has(dg, "nature.undead")),
        #: The Great Thirster is roused by the kill itself.
        "great_thirster": has(g, "mechanic.great-thirster"),
        # Killing Blow: a natural To Hit six wounds automatically (no die, so
        # no critical) and cannot be parried (``modular/attacks.py``).
        "killing_blow": has(effect, "mechanic.killing-blow"),
        # Spectral Touch: a natural six adds one extra wound of this attack,
        # not a fresh hit, poison or critical trigger.
        "spectral_touch": has(effect, "trait.spectral-touch"),
        # Black Lotus keeps an explicitly permitted critical attempt: the
        # oracle asks ``{key}.lotus-critical`` before turning the wound
        # automatic.  ``wight_blades`` is the other guaranteed-wound half.
        "lotus": bool(black_lotus_wounds(effect, dg) and not poison_blocked),
        "wight_blades": has(effect, "wight_blades"),
        "magical_attack": has(effect, "attack.magical"),
        # Printed weapon profiles the injury table reads.
        "shock": has(effect, "weapon.shock-rod"),
        "skull_busta": has(effect, "weapon.skull-busta"),
        "needle_and_thread": has(g, "mechanic.needle-and-thread"),
        # Injury-table shape supplied by the attack.
        "artefact_chart": has(effect, "weapon.count-of-ventimiglias-misericordia"),
        "blessing_of_morr": bool(
            has(effect, "mechanic.blessing-of-morr") and has(dg, "nature.undead")),
        "knife_fighting_injury": bool(
            has(effect, "skill.knife-fighting")
            and (has(effect, "weapon.dagger") or has(effect, "weapon.yambiya"))),
    }
    flags["hit_mod_base"] = int(
        effect.hit_modifier + dg.incoming_hit_modifier
        + int(flags["putrid"]) - int(flags["cloud_flies"])
        # ``modular/contexts.py::prepare_hit_context``, constant clauses.
        + int(_flesh_peddler(attacker, defender))
        - int(has(dg, "mechanic.unholy-stink"))
        + int(has(weapon_c, "weapon.hellblade") and not any(
            has(dg, tag) for tag in ("nature.undead", "nature.daemon")))
        + int(has(g, "mechanic.andanti-knowledge") and has(dg, "species.vampire"))
        - int(has(dg, "mechanic.foul-odour") and not any(
            has(g, tag) for tag in ("nature.undead", "nature.possessed", "nature.daemon")))
        - int(has(g, "condition.snorri-stench") or has(dg, "condition.snorri-stench"))
        - int(_symbol_of_unity(attacker, defender))
    )
    #: Only in the first round and only on a charge.
    flags["hit_mod_charge_fr"] = int(
        bool(has(g, "skill.backstabber") and has(g, "condition.unseen-charge"))
        + bool(has(g, "condition.summoned-this-turn"))
    )
    #: Foul Odour feeds a fire attack rather than blunting it.
    flags["strength_fire_bonus"] = int(
        has(dg, "mechanic.foul-odour") and has(effect, "attack.fire"))

    saves = prepare_special_save_context(defender, effect, key="special",
                                         defender_state=None, melee_attack=True)
    ward = 7 if saves.ward_blocked else saves.ward_save
    regeneration = 7 if saves.regeneration_blocked else saves.regeneration_save
    threshold = _critical_wound_threshold(effect, weapon_c, poison_blocked)
    if spiritual or (
        has(effect, "skill.unarmed-critical-strikes")
        and has(weapon_c, "weapon.natural-attacks")
    ):
        # ``_critical_wound_threshold`` reads only ``weapon.fist`` for the
        # unarmed clause and knows nothing of Spiritual Weapons; the oracle
        # (``modular/contexts.py::prepare_wound_context``) reads both.
        threshold = 5
    # The supplied dynamic value: a weapon whose own ``critical_threshold``
    # is lower than the rule's wins (``min`` in the oracle).  This is the
    # ``effect-values`` behaviour the native gate used to refuse.
    threshold = min(threshold, effect.critical_threshold)
    # Hatred and every other To Hit re-roll of ``modular/contexts.py``'s
    # ``_hit_reroll``, folded by the three facts that vary inside the duel.
    # Calling the oracle's own predicate keeps the long hatred list in one
    # place instead of copying it into a second engine.
    #: index = 8*first_round + 4*charging + 2*charged + frenzy.  ``charged``
    #: carries ``condition.being-charged``, which the oracle reads for the
    #: Pikewall re-roll; it is a per-row fact, so it is folded here too.
    charged_effect = merge_effects(effect, _constructed(("condition.being-charged",)))
    reroll_table = [
        1 if _hit_reroll(attacker, defender, weapon_c,
                         charged_effect if charged else effect,
                         bool(first_round), bool(charging), frenzy=bool(frenzy)) else 0
        for first_round in (0, 1) for charging in (0, 1)
        for charged in (0, 1) for frenzy in (0, 1)
    ]
    return {
        "weapon": _values(weapon_c),
        "effect": _values(effect),
        "flags": flags,
        "reroll_table": reroll_table,
        "critical_threshold": int(threshold),
        "ignition": int(
            min(effect.ignition_threshold, dg.caught_fire_threshold)
            if effect.ignition_threshold <= 6 else 7
        ),
        "ward": int(ward),
        "regeneration": int(regeneration),
        "damage": int(max(1, effect.damage)),
    }


# Fighter-level compile (both roles: attacker of ``foe`` and defender).


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
            miniath_reroll or sword_and_buckler or sword_master_reroll or dwarf_axes
            or (has(g, "skill.chosen-of-the-white-tower") and any(
                has(candidate, tag)
                for candidate in (main, off or EffectSet(), g)
                for tag in ("weapon.sword", "defence.buckler")))
            or has(main, "weapon.fighting-claws")
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
        "movement": stats.movement,
        "leadership": stats.leadership,
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
        "luck": has(g, "skill.luck"),
        "infection_immune": bool(g.poison_immunity or has(g, "poison_immune") or has(g, "undead_or_possessed")),
        "incoming_strength_modifier": int(g.incoming_strength_modifier),
        "incoming_attacks_modifier": int(g.incoming_attacks_modifier),
        "thin_flesh": has(g, "rule.thin-flesh"),
        "lycanthrope_self": has(g, "mechanic.hillman-lycanthrope"),
        "thick_skull": bool(g.thick_skull),
        "injury_reroll_out": has(g, "injury_reroll_out"),
        # Supplied dynamic effect values the oracle reads off the defender:
        # the ethereal save face and the fire-negated natural armour.
        "ethereal_hit_save": int(g.ethereal_hit_save),
        "ethereal": has(g, "mechanic.ethereal-hit-save"),
        "natural_armour_negated_by_fire": bool(g.natural_armour_negated_by_fire),
        # Injury-table shape and the post-table reactions of the victim.
        "bat_injury_chart": has(g, "mechanic.bat-injury-chart"),
        "fen_hard_to_kill": has(g, "mechanic.fen-hard-to-kill"),
        "hard_to_rattle": has(g, "mechanic.hard-to-rattle"),
        "inured_to_pain": has(g, "mechanic.inured-to-pain"),
        "undead_construct": has(g, "mechanic.undead-construct"),
        "veskit_no_pain": has(g, "mechanic.veskit-no-pain"),
        "marianna_jump_up": bool(
            has(g, "mechanic.marianna-no-pain-jump-up")
            and has(g, "skill.jump-up") and has(g, "skill.ignore-pain")),
        "hard_to_kill": bool(
            has(g, "skill.hard-to-kill") or has(g, "skill.tough-as-steel")
        ),
        "true_grit": has(g, "skill.tough-as-steel"),
        "concussion_immune": has(g, "concussion_immune"),
        "fragile": has(g, "fragile_halflings"),
        "survivor": has(g, "survivor"),
        "ignore_pain": bool(has(g, "skill.ignore-pain") and not has(g, "rule.squishy")),
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
        "serpent_whip": any(
            has(weapon, tag)
            for weapon in (main, off)
            if weapon is not None
            for tag in ("weapon.steel-whip", "weapon.beastlash", "weapon.pirate-scourge", "weapon.serpent-whip")
        ),
        "boar_spear": has(main, "weapon.boar-spear"),
        "sigmar_effective": bool(
            has(g, "skill.sigmar-s-sign") and has(foe.global_effects, "undead_or_possessed")
        ),
        "animal_friendship_effective": bool(
            (has(g, "animal_friendship") or has(g, "mechanic.animal-friendship"))
            and has(foe.global_effects, "species.normal-animal")
        ),
        #: Frantic's explicit top priority outranks every ordinary tier.
        "frantic": has(g, "mechanic.frantic"),
        #: The Sabretusk's charge replaces A1 with A2, not a generic +1.
        "sabretusk_charge": has(g, "mechanic.sabretusk-charge"),
        # --- per-turn producers of ``modular/rounds.py`` ------------------
        "lunatics": has(g, "mechanic.lunatics"),
        "centigor_drunken": has(g, "mechanic.centigor-drunken"),
        "animosity": bool(
            has(g, "mechanic.goblin-squabble") or has(g, "mechanic.fungus-rowdy")),
        "animosity_wide": has(g, "mechanic.fungus-rowdy"),
        "feral_instinct": has(g, "mechanic.feral-instinct"),
        "bitten_transform": has(g, "mechanic.bitten-transform"),
        "devoted_to_vampire": has(g, "mechanic.devoted-to-the-vampire"),
        "devoted_vampire_killed": has(g, "condition.devoted-vampire-killed"),
        "devoted_vampire_down": has(g, "condition.devoted-vampire-down"),
        "petru_debilitating": has(g, "condition.petru-debilitating"),
        "petru_strength": has(g, "condition.petru-strength"),
        "petru_resilience": has(g, "condition.petru-resilience"),
        "follow_me": has(g, "condition.command.follow-me-mine-pugnacious-ones"),
        "death_fighting": has(g, "condition.command.art-thou-ready-to-die-fighting"),
        "righteous_charge": has(g, "condition.righteous-charge"),
        "sea_shanty": has(g, "mechanic.sea-shanty"),
        "sea_shanty_psychology": has(g, "mechanic.sea-shanty-psychology"),
        "shanty_excluded": bool(
            any(has(foe.global_effects, tag) for tag in
                ("nature.undead", "nature.possessed", "nature.daemon",
                 "nature.construct", "nature.non-living"))),
        "shanty_psych_excluded": has(foe.global_effects, "mechanic.psychology-immunity"),
        "crude_belch_ogre": has(g, "mechanic.crude-belch-ogre"),
        "crude_belch_halfling": has(g, "skill.crude-belch-halfling"),
        #: Ravening Onslaught: a natural six adds another blow.
        "ravening_onslaught": has(g, "mechanic.ravening-onslaught"),
        "mantle_of_crows": has(g, "mechanic.mantle-of-crows"),
        "electrical_touch": has(g, "mechanic.electrical-touch"),
        "giggle_juice_spray": has(g, "mechanic.giggle-juice-spray"),
        "slayer_deathblow": has(g, "mechanic.deathblow"),
        "wheelo_morning_star": has(g, "wheelo.fitting.morning-star"),
        "wheelo_axe": has(g, "wheelo.fitting.axe"),
        "wheelo_club": has(g, "wheelo.fitting.club"),
        "wheelo_spear": has(g, "wheelo.fitting.spear"),
        "noblesse_stomp": bool(
            has(g, "mechanic.noblesse-stomp")
            and not has(me.main_weapon, "effect.serpent-staff-power")),
        "gaoler_grapple": bool(
            has(g, "mechanic.gaoler-grapple")
            and not has(g, "condition.mim-no-hand-attacks")
            and not any(has(foe.global_effects, tag) for tag in
                        ("nature.undead", "nature.daemon", "nature.dead",
                         "mechanic.pain-immunity", "size.large"))),
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
        "strongman": bool(g.strongman and (main.two_handed or has(main, "weapon.broadsword")) and main.priority < 0),
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
        "spear": has(main, "weapon.spear"),
        "opponent_always_first": has(foe.global_effects, "skill.always-strikes-first"),
        "initiative_bonus_total": int(
            g.initiative_bonus + main.initiative_bonus
            + (off.initiative_bonus if off else 0)
        ),
        # initialize scalars (port of ``modular.state.initialize_fighter``)
        "base_wounds": int(stats.wounds + int(has(g, "skill.monstrous"))),
        "starting_wounds": int(maximum_wounds(me)),
        "toughness_bonus": int(g.toughness_bonus),
        "frenzy_init": bool(g.frenzy),
        "lucky_charm_init": has(g, "defence.lucky-charm"),
        "crimson_shade": has(g, "preparation.crimson-shade"),
        "disability": has(g, "mechanic.disability"),
        **_init_fields(me, foe),
        **_psychology_fields(me, foe),
        # parry flags (defender role)
        **{f"parry_{key}": value for key, value in parry.items()},
        "random_characteristics": list(me.random_characteristics),
    }
    return result


# State initialisation facts (the oracle's ``initialize_fighter`` reads them
# from tags; the compiled core applies them in the same order).

#: ``(tag, stat index, bonus, backley)`` in the oracle's declaration order.
#: Stat indices follow ``vectorized._state.STATS`` (WS, S, T, I, A).
_CONDITION_DELTAS = (
    ("condition.petru-debilitating", 2, -1, False),
    ("condition.petru-strength", 1, 1, False),
    ("condition.petru-resilience", 2, 1, False),
    ("condition.alchemist-resilience", 2, 1, False),
    ("condition.alchemist-strength", 1, 1, False),
    ("condition.alchemist-aberrantius-vigortia", 1, 1, False),
    ("condition.alchemist-aberrantius-vigortia", 2, 1, False),
    ("condition.alchemist-backleys-brew", 1, -1, True),
    ("condition.alchemist-backleys-brew", 3, -1, True),
)


def _init_fields(me: CompiledFighter, foe: CompiledFighter) -> dict:
    g = me.global_effects
    supplied_disability = next(
        (result for result in range(1, 7) if has(g, f"condition.disability-{result}")), 0,
    )
    if has(g, "mechanic.disability") and not supplied_disability:
        # Same contract as the oracle: the permanent table result is supplied
        # at construction, never rolled inside the duel.
        raise ValueError(
            "Disability requires a permanent supplied result, not a duel-time table roll"
        )
    return {
        "initiative_missing": me.characteristics.initiative is None,
        "inconsistency": has(g, "mechanic.inconsistency"),
        "condition_deltas": [
            (stat, bonus, backley) for tag, stat, bonus, backley in _CONDITION_DELTAS
            if has(g, tag)
        ],
        "poetry_inspired": has(g, "condition.poetry-inspired"),
        "supplied_disability": int(supplied_disability),
        "guiding_dream": has(g, "mechanic.guiding-dream"),
        "guiding_dream_nominated": has(g, "condition.guiding-dream-target"),
        "netted_init": has(g, "condition.netted"),
        "persistent_frenzy": has(g, "mechanic.persistent-frenzy"),
        "frenzy_permitted": bool(
            not has(g, "mechanic.psychology-immunity") or has(g, "condition.snorri-frenzy")
        ),
        "stupidity_failed_init": bool(
            has(g, "condition.stupidity-failed")
            and not has(g, "condition.stupidity-exempt")
            and not g.frenzy
            and not has(g, "mechanic.psychology-immunity")
        ),
        "massively_built_init": has(g, "condition.massively-built-lost-turn"),
        "danse_macabre_init": has(g, "condition.danse-macabre-controlled"),
        "hillman_wolf_init": "compiler.hillman-wolf-form" in me.construction_tags,
        "can_charge": bool(charge_allowed(me, foe)),
        # Own-turn recovery options and per-turn declarations.
        "revenant": has(g, "mechanic.curse-of-the-revenant"),
        "herb_lore": has(g, "mechanic.herb-lore"),
        "herb_lore_outside": has(g, "mechanic.herb-lore-outside-combat"),
        "rousing_sermon": has(g, "mechanic.rousing-sermon"),
        "alchemist_backley": has(g, "condition.alchemist-backleys-brew"),
        "alchemist_addicted": has(g, "condition.alchemist-addicted"),
        "alchemist_vigortia": has(g, "condition.alchemist-aberrantius-vigortia"),
        "confound_and_confuse": has(g, "mechanic.confound-and-confuse"),
        "djinns_curse": has(g, "mechanic.djinns-curse"),
        "solkan_inquisitor": has(g, "mechanic.solkan-inquisitor"),
        "djinn_ethereal": has(g, "mechanic.djinn-ethereal"),
        #: The learned Shadow Dances, as a bit per ``SHADOW_DANCES`` index.
        "dances": sum(1 << i for i, dance in enumerate(SHADOW_DANCES)
                      if has(g, f"dance.{dance}")),
        "main_gauche_modes": bool(
            has(g, "mechanic.main-gauche-modes") and me.off_hand is not None
            and has(me.off_hand, "weapon.main-gauche")),
        # The Rememberer's printed re-roll: the Slayer Hero his band
        # remembers may repeat one missed blow against a large (or, in the
        # wider printed variant, a tough) enemy.
        "rememberer": bool(
            has(g, "condition.rememberer-support") and has(g, "identity.slayer")
            and has(g, "fighter-kind.hero")
            and (has(g, "mechanic.rememberer-large-only")
                 or has(g, "mechanic.rememberer-large-or-tough"))),
        "rememberer_large_or_tough": has(g, "mechanic.rememberer-large-or-tough"),
        "rememberer_target_large": has(foe.global_effects, "size.large"),
    }


# Psychology and Leadership facts (ports of ``modular/psychology.py``,
# ``modular/leadership.py`` and the charm block of ``modular/rounds.py``).
# Every decision that reads only the two compiled fighters is folded here;
# the per-row facts (conditions, resources, the supplied participants) stay
# in the compiled core.

_ANIMAL_TAGS = ("species.animal", "species.normal-animal", "species.beast")
_ENLIGHTENED_FOES = ("species.orc", "species.goblin", "warband-group.chaotic",
                     "nature.daemon", "nature.possessed", "identity.chaos-follower")
_ACCUSTOMED_FOES = ("species.vampire", "undead-kind.skeleton", "undead-kind.spirit")
#: The Skaven bands whose Rat Ogres print the nearby-Hero Stupidity exemption.
PRINTED_SKAVEN_BANDS = ("band.skaven-of-clan-mors-kaz",
                        "band.skaven-of-clan-moulder-web",
                        "band.skaven-of-clan-pristekk-sc")
#: Charge gates a Fear-causing singer imposes on its charging target
#: (``modular/psychology.py::resolve_fear``), by code.
CHARGE_GATES = ("", "ashamed-and-afraid", "slaanesh-charge",
                "hypnotic-musk-charge", "charismatic-charge")
#: The three Vampire control powers, in the oracle's ``CONTROL_POWERS`` order.
CONTROL_POWERS = ("hypnotic-gaze", "lahmia-seduction", "lahmian-seduction")


def _sex(effect: EffectSet) -> str | None:
    return next((sex for sex in ("male", "female") if has(effect, f"sex.{sex}")), None)


def fears_opponent_fire(me: CompiledFighter, foe: CompiledFighter) -> bool:
    from mordheim_combat.modular.psychology import fears_opponent_fire
    return bool(fears_opponent_fire(me, foe))


def causes_fear(me: CompiledFighter, foe: CompiledFighter) -> bool:
    """Whether ``me`` causes Fear in ``foe`` (the oracle's own predicate)."""
    from mordheim_combat.modular.psychology import causes_fear
    return bool(causes_fear(me, foe))


def _charge_gate(target: CompiledFighter, singer: CompiledFighter) -> int:
    t, s = target.global_effects, singer.global_effects
    if has(t, "mechanic.ashamed-and-afraid") and has(s, "identity.sigmarite-opponent"):
        return 1
    if has(s, "mechanic.slaanesh-charge-test"):
        return 2
    if (has(s, "mechanic.hypnotic-musk") and not target.mounted
            and not has(t, "condition.goading-charge")
            and any(has(t, tag) for tag in _ANIMAL_TAGS)):
        return 3
    if has(s, "mechanic.opposite-sex-charge-test"):
        sexes = (_sex(t), _sex(s))
        if None in sexes:
            raise ValueError("Charismatic requires both duelists' explicit male/female facts")
        if sexes[0] != sexes[1]:
            return 4
    return 0


def _fauna_mode(target: CompiledFighter, owner: CompiledFighter) -> int:
    """0 no Tranquil Fauna; 1 the animal is barred; 2 its handler tests."""
    t = target.global_effects
    if not (has(owner.global_effects, "mechanic.taal-tranquil-fauna") and has(t, "species.animal")):
        return 0
    conditional = any(has(t, tag) for tag in ("fauna-animal.handled", "fauna-animal.large-predator"))
    ordinary = has(t, "fauna-animal.ordinary") or has(t, "species.normal-animal")
    if not conditional and not ordinary:
        raise ValueError(
            "Tranquil Fauna requires the animal's explicit ordinary/handled/large-predator qualification"
        )
    if conditional:
        if target.animal_handler_leadership is None:
            raise ValueError("Tranquil Fauna requires the qualified Animal Handler's Leadership")
        return 2
    return 1


def _psychology_fields(me: CompiledFighter, foe: CompiledFighter) -> dict:
    g, fg = me.global_effects, foe.global_effects
    from mordheim_combat.modular.leadership import undead_foes_fear_immunity
    male = has(g, "sex.male")
    not_undead_daemon = not (has(g, "nature.undead") or has(g, "nature.daemon"))
    lahmia_male_gate = has(fg, "mechanic.lahmia-seduction") and not_undead_daemon and not (
        has(g, "mechanic.psychology-immunity") or has(g, "mechanic.stupidity"))
    if lahmia_male_gate and _sex(g) is None:
        raise ValueError("Lahmia Seduction requires the opponent's explicit male/female fact")
    beauty_target = bool(
        has(fg, "mechanic.beauty-of-the-sea") and male and not has(g, "species.animal")
    )
    return {
        # immunities and automatic results
        "psychology_immunity": has(g, "mechanic.psychology-immunity"),
        "fear_immunity": has(g, "mechanic.fear-immunity"),
        "fear_immunity_undead_chargers": bool(
            has(g, "mechanic.fear-immunity-undead-chargers") and has(fg, "nature.undead")),
        "undead_foes_no_fear": bool(undead_foes_fear_immunity(me, foe)),
        "automatic_leadership": has(g, "mechanic.automatic-leadership"),
        "holy_relic": has(g, "defence.holy-relic"),
        "sigmar_enlightened": bool(
            has(g, "mechanic.sigmar-enlightened") and any(has(fg, tag) for tag in _ENLIGHTENED_FOES)),
        # the tested value and its modifiers
        "squig_recipient": me.fighter_id == "night-goblins-web:cave-squigs",
        "handler_leadership": has(g, "mechanic.handler-leadership"),
        "stupidity_leadership": me.stupidity_leadership,
        "stupidity_leadership_bonus": int(me.stupidity_leadership_bonus),
        "own_leadership": has(g, "mechanic.own-leadership"),
        "broken_spirit": has(g, "mechanic.broken-spirit"),
        "devoted": has(g, "mechanic.devoted"),
        "slave": has(g, "identity.slave"),
        "halfling": has(g, "species.halfling"),
        "poetry_victorious_leader": has(g, "condition.poetry-victorious-leader"),
        "mob_leadership": has(g, "mechanic.mob-leadership"),
        "mob_allies": int(me.mob_allies),
        # ``apply_opponent_leadership``: the opponent's facts projected onto me
        "enchanting_beauty": bool(has(fg, "mechanic.enchanting-beauty") and not_undead_daemon),
        "questing_vow_reroll": bool(has(g, "mechanic.questing-vow") and causes_fear(foe, me)),
        "opponent_ghostly_howl": has(fg, "mechanic.ghostly-howl"),
        # dice conventions and re-rolls
        "cold_blooded_leadership": has(g, "mechanic.cold-blooded-leadership"),
        "cold_blooded_psychology": has(g, "mechanic.cold-blooded-psychology"),
        "first_failed_leadership_reroll": has(g, "mechanic.first-failed-leadership-reroll"),
        "mandatory_leadership_reroll": has(g, "mechanic.mandatory-leadership-reroll"),
        "leadership_reroll": has(g, "mechanic.leadership-reroll"),
        "raise_our_insignia": has(g, "condition.command.raise-our-insignia"),
        "fear_reroll": has(g, "mechanic.fear-reroll"),
        "ranalds_luck": has(g, "mechanic.ranalds-luck"),
        "one_roll_reroll": bool(has(g, "mechanic.oracle") or has(g, "mechanic.augur-one-roll-reroll")),
        "scryer": has(g, "mechanic.scryer"),
        # Stupidity
        "stupidity": has(g, "mechanic.stupidity"),
        "stupidity_exempt": has(g, "condition.stupidity-exempt"),
        "impetuous_charge": has(g, "condition.impetuous-charge"),
        "disability_hero_nearby": has(g, "condition.disability-hero-nearby"),
        "skaven_group": has(g, "warband-group.skaven"),
        "printed_skaven_bits": sum(
            1 << i for i, band in enumerate(PRINTED_SKAVEN_BANDS) if has(g, band)),
        "bear_handler_recipient": has(g, "mechanic.bear-handler-recipient"),
        "bear_handler_nearby": has(g, "condition.bear-handler-nearby"),
        # Fear
        "causes_fear": causes_fear(me, foe),
        "fears_foe_fire": fears_opponent_fire(me, foe),
        "morrs_special": bool(has(fg, "mechanic.morrs-servant") and has(g, "nature.undead")),
        "ere_we_go": has(g, "mechanic.ere-we-go"),
        "accustomed_to_fear": bool(
            has(g, "mechanic.accustomed-to-fear") and any(has(fg, tag) for tag in _ACCUSTOMED_FOES)),
        "craven": has(g, "mechanic.craven"),
        "wheelo_impact": has(g, "mechanic.wheelo-impact"),
        "charge_gate": _charge_gate(me, foe),
        "beauty_target": beauty_target,
        # charms (me as the target of the foe's power)
        "dance_target": bool(
            has(fg, "mechanic.mesmerising-dance") and not any(
                has(g, tag) for tag in ("nature.undead", "species.lizardman", "mechanic.charm-immunity"))),
        "pendant_target": bool(has(fg, "defence.eye-pendant") and has(g, "nature.undead")),
        "shornaal_target": bool(has(fg, "mechanic.mark-of-shornaal") and not has(g, "mechanic.charm-immunity")),
        "hypnotist_target": bool(has(fg, "mechanic.hypnotist") and not any(
            has(g, tag) for tag in ("nature.undead", "nature.daemon",
                                    "mechanic.psychology-immunity", "mechanic.charm-immunity"))),
        "foe_hypnotist": has(fg, "mechanic.hypnotist"),
        "fauna_mode": _fauna_mode(me, foe),
        "animal_handler_leadership": me.animal_handler_leadership,
        "deceive_target": bool(has(fg, "mechanic.lahmia-deceive") and not any(
            has(g, tag) for tag in ("nature.undead", "nature.daemon", "mechanic.psychology-immunity"))),
        "hypnotize_target": bool(has(fg, "mechanic.lahmian-hypnotize") and not has(g, "mechanic.psychology-immunity")),
        "foe_controls": [
            has(fg, "mechanic.hypnotic-gaze"),
            has(fg, "mechanic.lahmia-seduction"),
            has(fg, "mechanic.lahmian-seduction"),
        ],
        "control_excluded": [
            has(g, "mechanic.psychology-immunity"),
            not not_undead_daemon or has(g, "mechanic.psychology-immunity") or has(g, "mechanic.stupidity"),
            has(g, "mechanic.psychology-immunity"),
        ],
        "male": male,
    }


# Reaction effects shared by every compiled side.
_FIRE_EFFECT = _constructed(
    ("attack.fire", "effect.no-critical"), fixed_strength=4,
    automatic_hit=True, cannot_be_parried=True,
)
_REACTIONS = {
    "entangle": _constructed(
        ("effect.chained-squig-entangle",), fixed_strength=3, automatic_hit=True,
    ),
    "hug": _constructed(
        ("effect.automatic-wound", "effect.no-critical"),
        automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
    ),
    "acid": _constructed(
        ("rule.acid-blood", "effect.no-critical"), fixed_strength=3,
        automatic_hit=True, cannot_be_parried=True,
    ),
    "counter": _constructed(("effect.cutlass-counter",)),
    "spines": _constructed(
        ("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True,
    ),
    "backlash": _constructed(
        ("mechanic.black-hunger-backlash", "effect.no-critical"), fixed_strength=3,
        automatic_hit=True, cannot_be_parried=True, ignore_armour=True,
    ),
    "bull": _constructed(("mechanic.bull-charge",), hit_modifier=1),
    #: The Crow Master's Mantle: one automatic Strength 2 hit that opens the
    #: combat phase.  Fixed-strength crows are not the bearer's own blows,
    #: so they inherit no personal weapon contribution.
    "crows": _constructed(("mechanic.mantle-of-crows",), fixed_strength=2,
                          automatic_hit=True, cannot_be_parried=True),
    #: The Noblesse stomp: one extra blow against a foe already on the ground.
    "stomp": _constructed(("rule.noblesse-stomp",)),
    #: The Giggle Juice spray replaces one allocated blow of the pool.
    "giggle": _constructed(("mechanic.giggle-juice-spray-attack",),
                           automatic_hit=True, fixed_strength=2, injury_modifier=1),
    "body": _constructed(("mechanic.body-slam",), strength_bonus=1, hit_modifier=1),
    "infection": _constructed(
        ("effect.automatic-wound", "effect.no-critical"),
        fixed_strength=3, automatic_hit=True, cannot_be_parried=True,
    ),
}


def compile_sources(me: CompiledFighter, foe: CompiledFighter) -> dict:
    """Fold the attack sources of ``me`` against ``foe``."""
    main_base = (
        me.main_weapon_without_poison
        if (foe.global_effects.poison_immunity or has(foe.global_effects, "poison_immune"))
        and me.main_weapon_without_poison is not None
        else me.main_weapon
    )
    result = {"main": compile_source(me, foe, main_base)}
    result["unarmed"] = compile_source(
        me, foe, me.unarmed_weapon or EffectSet(tags=("weapon.fist",)),
    )
    result["unpredictable"] = (
        compile_source(
            me, foe,
            merge_effects(
                main_base,
                _constructed(("mechanic.unpredictable-attack",), cannot_be_parried=True),
            ),
        )
        if has(me.global_effects, "mechanic.unpredictable-attack") else None
    )
    result["off"] = compile_source(me, foe, me.off_hand) if me.off_hand is not None else None
    # The Priest's bite is its own final event, after both warriors' weapon
    # attacks, so the ordinary pool never allocates it.
    result["extras"] = [compile_source(me, foe, extra) for extra in me.extra_attacks
                        if not has(extra, "rule.strikes-last-bite")]
    result["last_bite"] = [compile_source(me, foe, extra) for extra in me.extra_attacks
                           if has(extra, "rule.strikes-last-bite")]
    return result


def g_of(fighter: CompiledFighter) -> EffectSet:
    return fighter.global_effects


def compile_reactions(me: CompiledFighter, foe: CompiledFighter) -> dict:
    """Fold the reaction attacks ``me`` can deliver against ``foe``."""
    # The backlash strikes its own bearer, so it is folded against ``me``.
    result = {
        name: compile_source(me, me if name == "backlash" else foe, effect)
        for name, effect in _REACTIONS.items()
    }
    result["fire"] = compile_source(_fire_source(me), foe, _FIRE_EFFECT)
    #: The electrical touch is a jolt whose Strength reads the victim's own
    #: armour, so it is compiled against that victim.
    result["impact"] = compile_source(
        replace(me, global_effects=EffectSet()), foe, _constructed(
            (), fixed_strength=5 if has(g_of(me), "wheelo.fitting.morning-star") else 4,
            automatic_hit=True, cannot_be_parried=True,
            armour_penetration=int(has(g_of(me), "wheelo.fitting.axe")),
            concussion=has(g_of(me), "wheelo.fitting.club")))
    result["jolt"] = compile_source(me, foe, _constructed(
        ("mechanic.electrical-touch-attack",), automatic_hit=True,
        fixed_strength=5 if has(foe.global_effects, "condition.metal-armour") else 3,
        ignore_armour=True))
    result["crows"] = compile_source(
        replace(me, global_effects=EffectSet(), main_weapon=EffectSet(),
                off_hand=None, extra_attacks=()),
        foe, _REACTIONS["crows"])
    return result


#: Whole-pool attack replacements the oracle offers before the attack count
#: (``modular/rounds.py::select_attack_replacement``), in its printed order.
#: ``anvil-head`` is omitted: its offer is gated on a per-row charge, which
#: the compiled core cannot express as one projection per duel.
def attack_replacements(me: CompiledFighter) -> list[tuple[str, CompiledFighter]]:
    """The projections ``select_attack_replacement`` can return, in order.

    Each entry is the decision suffix the oracle asks under its round key and
    the fighter that replaces the whole pool when the player accepts.  The
    caller interns them in a :class:`ProjectionTable`, so a row that takes an
    offer is simulated by exactly the scalars that fighter compiles to.
    """
    offers: list[tuple[str, CompiledFighter]] = []
    if has(me.global_effects, "mechanic.wraith-touch"):
        offers.append(("wraith-touch", replace(
            me, main_weapon=EffectSet(
                tags=("weapon.fist", "effect.wraith-touch", "effect.no-critical"),
                strength_bonus=-1, target_armour_bonus=1),
            main_weapon_without_poison=None, off_hand=None,
            off_hand_without_poison=None, off_hand_attacks=False, extra_attacks=())))
    if me.vomit_attack is not None:
        offers.append(("vomit-attack", replace(
            me, main_weapon=me.vomit_attack, main_weapon_without_poison=None,
            off_hand=None, off_hand_without_poison=None, off_hand_attacks=False,
            extra_attacks=())))
    if has(me.main_weapon, "weapon.serpent-staff"):
        offers.append(("serpent-staff", replace(
            me, main_weapon=EffectSet(
                tags=("effect.serpent-staff-power",), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())))
    # Anvil Head is offered only in the first round and only to a charging
    # row, so its projection carries that gate rather than the whole pool.
    if has(me.global_effects, "mechanic.anvil-head"):
        offers.append(("anvil-head", replace(me, global_effects=replace(
            me.global_effects, tags=tuple(
                tag for tag in me.global_effects.tags if tag != "mechanic.anvil-head")))))
    # Death Blow is a removal, not a replacement: declining it drops the tag
    # for this round only, so the declined shape is its own projection.
    if has(me.global_effects, "mechanic.death-blow") and me.characteristics.attacks >= 2:
        offers.append(("death-blow", replace(me, global_effects=replace(
            me.global_effects, tags=tuple(
                tag for tag in me.global_effects.tags if tag != "mechanic.death-blow")))))
    return offers


def main_gauche_modes(me: CompiledFighter) -> list[CompiledFighter]:
    """The blade kept back to parry, then the blade used as a dagger.

    One mode is declared per combat turn (``modular/rounds.py``).  Either way
    the blade stays in the hand it is carried in, so the attack mode is
    declared on the off hand and is never promoted to the main one.
    """
    off = me.off_hand
    if not (has(me.global_effects, "mechanic.main-gauche-modes")
            and off is not None and has(off, "weapon.main-gauche")):
        return []
    clean = me.off_hand_without_poison or off
    dagger = replace(off, parry=False, tags=(*off.tags, "weapon.dagger"),
                     target_armour_bonus=1)
    dagger_clean = replace(clean, parry=False, tags=(*clean.tags, "weapon.dagger"),
                           target_armour_bonus=1)
    return [
        replace(me, off_hand=off, off_hand_without_poison=clean, off_hand_attacks=False),
        replace(me, off_hand=dagger, off_hand_without_poison=dagger_clean,
                off_hand_attacks=True),
    ]


def shifty_weapons(me: CompiledFighter) -> list[CompiledFighter]:
    """The two weapons ``select_shifty_weapon`` can nominate, main hand first.

    The bonus strike keeps the hand slot its weapon is carried in and drops
    every other contribution, exactly as the oracle projects it.  A bearer
    with no usable off hand nominates only its main weapon.
    """
    from mordheim_combat.modular.equipment import is_pistol
    if not has(me.global_effects, "skill.shifty"):
        return []
    def only(weapon, clean, slot):
        return replace(me, main_weapon=weapon, main_weapon_without_poison=clean,
                       main_hand_slot=slot, off_hand=None,
                       off_hand_without_poison=None, off_hand_attacks=False,
                       extra_attacks=())
    main = only(me.main_weapon, me.main_weapon_without_poison, me.main_hand_slot)
    off = me.off_hand if me.off_hand_attacks else None
    if off is None or off == me.main_weapon:
        return [main]
    if is_pistol(off):
        # The printed ruling keeps a pistol-only bonus as its own strike.
        return [main]
    return [main, only(off, me.off_hand_without_poison, me.off_hand_slot)]


def mutation_row_state(row_state=None):
    """One row's mutation facts as the state ``modular.mutations`` reads.

    ``vectorized._mutations.MutationState`` is already that dataclass view of
    a ``FighterState``, so the port keeps one definition instead of a second
    copy; the rules themselves stay in ``modular.mutations``.
    """
    from mordheim_combat.vectorized._mutations import MutationState
    return MutationState() if row_state is None else row_state


def project_mutated(base: CompiledFighter, row_state, *, first_round: bool) -> CompiledFighter:
    """The effective fighter of a row that carries brands.

    ``fighter_for_mutations`` applies the chart results to the printed
    profile and ``equipment_for_state`` then projects the kit that survives,
    which is exactly what ``modular/rounds.py::_mutated_phase_fighter`` does
    before the pool is counted.
    """
    from mordheim_combat.modular.equipment import equipment_for_state
    from mordheim_combat.modular.mutations import fighter_for_mutations
    from mordheim_combat.modular.state import FighterState
    projected = fighter_for_mutations(base, row_state)
    carrier = FighterState(
        wounds=max(1, int(row_state.wounds)),
        transformed=bool(row_state.transformed),
        equipment_cast_off=bool(row_state.equipment_cast_off),
        hillman_wolf=bool(row_state.hillman_wolf),
    )
    return equipment_for_state(projected, carrier, first_round=first_round)


def compile_side(me: CompiledFighter, foe: CompiledFighter) -> dict:
    """One fighter's complete compiled view against ``foe``.

    This is the unit the native projection tables store: the printed fighter
    is entry zero of its side, and every per-row projection (a broken hand, a
    transformation, an acquired brand) is folded through the same function and
    appended, so a projected row is simulated by exactly the scalars the
    printed fighter would get had it been compiled in that shape.
    """
    fighter = _compile_fighter(me, foe)
    fighter["can_burn"] = bool(_optional_phase_plan(me, foe).first_can_burn)
    return {
        "fighter": fighter,
        "sources": compile_sources(me, foe),
        "reactions": compile_reactions(me, foe),
    }


class ProjectionTable:
    """Per-side registry of projected fighters, interned by identity.

    Entry zero of each side is the printed fighter the duel compiled.  The
    core asks :meth:`intern` for the index of a projected fighter; a new
    projection is folded once through :func:`compile_side` and appended, and
    the core mirrors the append into its own C tables.  Rows then carry only
    the index, exactly as ``CombatState.effective_fighter`` carries a cached
    projection per row in the NumPy engine.
    """

    def __init__(self, first: CompiledFighter, second: CompiledFighter) -> None:
        self.fighters = {"first": first, "second": second}
        self.entries = {"first": [first], "second": [second]}
        self._index = {"first": {first: 0}, "second": {second: 0}}
        #: One ``compile_side`` view per entry; the core mirrors every entry
        #: it does not hold yet into its C tables before a batch and after a
        #: row projection is interned.
        self.compiled = {
            "first": [compile_side(first, second)],
            "second": [compile_side(second, first)],
        }
        #: The whole-pool replacements of ``select_attack_replacement``, in
        #: the oracle's printed order: the decision suffix the core asks and
        #: the fighter it projects to.
        self.replacement_fighters = {
            "first": [fighter for _, fighter in attack_replacements(first)],
            "second": [fighter for _, fighter in attack_replacements(second)],
        }
        self.replacements = {
            "first": [name for name, _ in attack_replacements(first)],
            "second": [name for name, _ in attack_replacements(second)],
        }
        #: The two declared Main Gauche modes (parry, dagger), interned so a
        #: row simply moves to the mode its player declared this turn.
        self.gauche_fighters = {
            "first": main_gauche_modes(first),
            "second": main_gauche_modes(second),
        }
        #: The nominated Shifty strike: one bonus attack with the weapon its
        #: bearer chooses, projected so it keeps that weapon's own profile.
        self.shifty_fighters = {
            "first": shifty_weapons(first),
            "second": shifty_weapons(second),
        }
        #: Per-row mutation state, the object-valued half of the oracle's
        #: ``FighterState`` that no C column can hold.  A row appears here
        #: only once it actually carries a brand.
        self.mutation_rows = {"first": {}, "second": {}}

    # -- per-row mutation transitions, driven by the compiled round --------

    def brand_row(self, side: str, row: int, option, dice, decisions, key: str) -> int:
        """Apply one chart result to one row and intern its new projection."""
        from mordheim_combat.modular.mutations import apply_brand
        current = self.mutation_rows[side].get(row) or mutation_row_state()
        self.mutation_rows[side][row] = apply_brand(
            self.fighters[side], current, option, dice, decisions, key)
        return 0

    def mutation_option(self, side: str, result: int):
        """The owner's printed D66 chart entry, or ``None`` when absent."""
        return next((option for option in self.fighters[side].mutation_options
                     if option.roll == result), None)

    def project_row(self, side: str, row: int, decisions, key: str,
                    first_round: bool) -> int:
        """Select this phase's tail and intern the row's effective fighter."""
        from mordheim_combat.modular.mutations import select_mutation_tail
        current = self.mutation_rows[side].get(row)
        if current is None or not current.mutations:
            return 0
        base = self.fighters[side]
        current = select_mutation_tail(base, current, decisions, key)
        self.mutation_rows[side][row] = current
        return int(self.intern(side, project_mutated(
            base, current, first_round=first_round)))

    def row_brand_count(self, side: str, row: int) -> int:
        current = self.mutation_rows[side].get(row)
        return 0 if current is None else len(current.mutations)

    def foe(self, side: str) -> CompiledFighter:
        return self.fighters["second" if side == "first" else "first"]

    def intern(self, side: str, fighter: CompiledFighter) -> int:
        index = self._index[side].get(fighter)
        if index is None:
            index = len(self.entries[side])
            self.entries[side].append(fighter)
            self._index[side][fighter] = index
            self.compiled[side].append(compile_side(fighter, self.foe(side)))
        return index

    def fighter(self, side: str, index: int) -> CompiledFighter:
        return self.entries[side][index]


# Contextual facts (``PreparedDuelContext``) folded for the compiled core.

CONDITION_CODES = {
    "standing": 0, "knocked-down": 1, "stunned": 2, "paralyzed": 3, "out": 4, "fleeing": 5,
}

#: Provider and identity facts the oracle's Leadership and Psychology
#: operators read from a nearby participant, as ``ParticipantC`` flags.
PARTICIPANT_FLAGS = (
    "mechanic.leader-six", "mechanic.leader-twelve", "mechanic.leader-four",
    "mechanic.dim-witted-leader", "mechanic.leader-fallback", "mechanic.relay-orders",
    "mechanic.songster", "mechanic.slave-driver", "condition.scourge-armed",
    "mechanic.bear-handler", "mechanic.handler-leadership", "condition.mouth-sewn",
    "fighter-kind.hero", "species.skaven", "mechanic.undivided-leader",
    "mechanic.wizened-halfling", "species.halfling", "nature.undead",
    "species.vampire", "identity.necromancer",
)


def compile_context(prepared: PreparedDuelContext | None) -> dict | None:
    """Fold the supplied local facts into index-addressed scalars.

    Participants keep the order of ``prepared.participants`` (the two
    duelists first), sides and bands become small integers, distances a full
    matrix with ``-1`` for an unknown pair, and the charge, active-player and
    contact facts become flags.  Nothing is inferred: a missing distance stays
    missing, exactly as ``PreparedDuelContext.distance`` raises for it.
    """
    if prepared is None:
        return None
    facts = prepared.facts
    participants = prepared.participants
    index = {p.participant_id: i for i, p in enumerate(participants)}
    sides = {}
    for p in participants:
        sides.setdefault(p.side_id, len(sides))
    bands = sorted({
        tag for p in participants for tag in p.fighter.global_effects.tags
        if tag.startswith("band.")
    })
    if len(bands) > 64:
        raise ValueError("the native context supports at most 64 distinct band identities")
    band_bit = {band: 1 << i for i, band in enumerate(bands)}
    count = len(participants)
    distances = [[-1.0] * count for _ in range(count)]
    for a, b, inches in facts.distances:
        distances[index[a]][index[b]] = distances[index[b]][index[a]] = float(inches)
    duelists = {facts.first_id, facts.second_id}
    contacts = None
    if facts.contacts is not None:
        contacts = [(index[a], index[b]) for a, b in facts.contacts]
    rows = []
    for p in participants:
        g = p.fighter.global_effects
        stats = p.fighter.characteristics
        flags = {tag: has(g, tag) for tag in PARTICIPANT_FLAGS}
        flags["weapon.pirate-scourge"] = any(
            has(weapon, "weapon.pirate-scourge")
            for weapon in (p.fighter.main_weapon, p.fighter.off_hand) if weapon is not None
        )
        flags["weapon.squig-prodder"] = any(
            has(weapon, "weapon.squig-prodder")
            for weapon in (p.fighter.main_weapon, p.fighter.off_hand) if weapon is not None
        )
        rows.append({
            "printed_skaven_bits": sum(
                1 << i for i, band in enumerate(PRINTED_SKAVEN_BANDS) if has(g, band)),
            "id": p.participant_id,
            "side": sides[p.side_id],
            "condition": CONDITION_CODES[p.condition],
            "leadership": stats.leadership,
            "movement": stats.movement,
            "bands": sum(band_bit[tag] for tag in g.tags if tag in band_bit),
            "squig_herder": p.fighter.fighter_id == "night-goblins-web:squig-herder",
            "flags": flags,
        })
    return {
        "participants": rows,
        "distances": distances,
        "bands": bands,
        "charging": (
            None if facts.charging is None
            else (facts.first_id in facts.charging, facts.second_id in facts.charging)
        ),
        "active_first": (
            None if facts.active_participant is None
            else facts.active_participant == facts.first_id
        ),
        "contacts": contacts,
        "duelists_in_contact": bool(
            contacts is not None and any({a, b} == duelists for a, b in facts.contacts)
        ),
    }


# Duel-level compile


def compile_duel(first: CompiledFighter, second: CompiledFighter) -> dict:
    """Build the full immutable context consumed by the native batch core.

    The historical flat keys are kept for the core and its tests; the two
    sides are folded through :func:`compile_side`, the same function the
    projection tables use for every later per-row projection.
    """
    from mordheim_combat.kernel import require_optimized_support
    require_optimized_support(first, second)
    first_side = compile_side(first, second)
    second_side = compile_side(second, first)
    return {
        "first": first_side["fighter"],
        "second": second_side["fighter"],
        "sources_first": first_side["sources"],
        "sources_second": second_side["sources"],
        "reactions_first": first_side["reactions"],
        "reactions_second": second_side["reactions"],
    }
