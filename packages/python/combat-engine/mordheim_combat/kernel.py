"""Primitive, immutable boundary consumed by optimized combat backends."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from typing import Collection
from typing import Literal

from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from mordheim_core.models import DuelContext
from mordheim_core.context import PreparedDuelContext, prepare_duel_context


EFFECT_VALUE_FIELDS = tuple(field.name for field in fields(EffectSet) if field.name != "tags")

OptimizedBackend = Literal["numpy", "native"]


@dataclass(frozen=True, slots=True)
class EffectKernelPlan:
    tag_mask: int
    values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class FighterKernelPlan:
    characteristics: tuple[int, int, int, int, int, int]
    global_effects: EffectKernelPlan
    main_weapon: EffectKernelPlan
    off_hand: EffectKernelPlan | None
    extra_attacks: tuple[EffectKernelPlan, ...]
    armour_save: int
    natural_armour_save: int
    natural_armour_worst_save: int
    helmet_save: int
    injury_profile: int
    ballistic_skill: int
    off_hand_attacks: bool
    mounted: bool
    movement: int | None = None
    leadership: int | None = None


@dataclass(frozen=True, slots=True)
class DuelKernelPlan:
    version: int
    tag_ids: tuple[str, ...]
    first: FighterKernelPlan
    second: FighterKernelPlan
    optimization_eligible: bool
    context: PreparedDuelContext | None = None


@dataclass(frozen=True, slots=True)
class PendingCapabilities:
    """Behaviors an optimized backend has not ported yet.

    The NumPy and native gates are independent. A port group rebuilds the
    NumPy value (``dataclasses.replace``) once its runtime path is connected;
    the native value stays frozen until Cython has its own port of the same
    behavior, so NumPy progress never grants native support accidentally.
    """

    residual_tags: frozenset[str]
    local_modifier_tags: frozenset[str]
    weapon_profile_tags: frozenset[str]
    behaviours: frozenset[str]


def _effects(fighter: CompiledFighter) -> tuple[EffectSet, ...]:
    return (
        fighter.global_effects, fighter.main_weapon,
        *((fighter.off_hand,) if fighter.off_hand is not None else ()),
        *fighter.extra_attacks,
    )


def _effect_plan(effect: EffectSet, tag_indices: dict[str, int]) -> EffectKernelPlan:
    mask = 0
    for tag in effect.tags:
        mask |= 1 << tag_indices[tag]
    return EffectKernelPlan(
        mask,
        tuple(int(getattr(effect, name)) for name in EFFECT_VALUE_FIELDS),
    )


def _fighter_plan(fighter: CompiledFighter, tag_indices: dict[str, int]) -> FighterKernelPlan:
    stats = fighter.characteristics
    return FighterKernelPlan(
        characteristics=(
            stats.weapon_skill, stats.strength, stats.toughness,
            stats.wounds, stats.initiative, stats.attacks,
        ),
        global_effects=_effect_plan(fighter.global_effects, tag_indices),
        main_weapon=_effect_plan(fighter.main_weapon, tag_indices),
        off_hand=(
            _effect_plan(fighter.off_hand, tag_indices)
            if fighter.off_hand is not None else None
        ),
        extra_attacks=tuple(_effect_plan(effect, tag_indices) for effect in fighter.extra_attacks),
        armour_save=fighter.armour_save,
        natural_armour_save=fighter.natural_armour_save,
        natural_armour_worst_save=fighter.natural_armour_worst_save,
        helmet_save=fighter.helmet_save,
        injury_profile=fighter.injury_profile,
        ballistic_skill=fighter.ballistic_skill,
        off_hand_attacks=fighter.off_hand_attacks,
        mounted=fighter.mounted,
        movement=stats.movement, leadership=stats.leadership,
    )


def _pending_snapshot() -> PendingCapabilities:
    """Return the behaviors no optimized backend has ported yet.

    Both gates start from this same snapshot. Only the NumPy entry in
    ``_PENDING`` is expected to shrink during the port; the native path keeps
    rejecting everything this snapshot names until Cython is ported.
    """
    residual_tags = {
        "mechanic.feral-instinct", "mechanic.slave-driver", "mechanic.opposite-sex-charge-test",
        "mechanic.relay-orders", "mechanic.songster", "mechanic.devoted", "mechanic.broken-spirit",
        "mechanic.invincible-swordsman", "mechanic.djinns-curse", "mechanic.greenskin-traitor",
        "mechanic.cannot-charge", "mechanic.sea-shanty", "mechanic.sea-shanty-psychology",
        "mechanic.crude-belch-ogre", "mechanic.noblesse-stomp", "mechanic.ranalds-luck",
        "mechanic.oracle", "mechanic.augur-one-roll-reroll", "mechanic.slaanesh-charge-test",
        "skill.chosen-of-the-white-tower", "skill.instinctive-warrior", "mechanic.marks-of-ranald",
        "mechanic.devoted-to-the-vampire", "mechanic.bitten-transform", "weapon.ienh-khain",
        "mechanic.estalian-technique", "mechanic.darting-steel", "mechanic.rememberer-large-only",
        "mechanic.rememberer-large-or-tough", "mechanic.achilles-heel", "mechanic.corruption",
        "condition.rememberer-support", "condition.stampede-active", "mechanic.main-gauche-modes",
        "mechanic.inconsistency", "condition.petru-debilitating", "condition.petru-strength",
        "condition.petru-resilience", "condition.petru-fortitude", "condition.danse-macabre-controlled",
        "mechanic.herb-lore-self-heal", "condition.alchemist-backleys-brew", "condition.alchemist-addicted",
        "mechanic.herb-lore", "condition.alchemist-strength", "condition.alchemist-resilience",
        "condition.alchemist-aberrantius-vigortia", "condition.fungus-brew-dizzy",
        "mechanic.fungus-rowdy", "mechanic.lunatics", "mechanic.own-leadership",
        "mechanic.mob-leadership",
        "mechanic.leader-twelve", "mechanic.drug-immunity",
        "mechanic.persistent-frenzy", "mechanic.hypnotic-musk", "condition.impetuous-charge",
        "mechanic.beak", "mechanic.prehensile-tail", "mechanic.electrical-touch",
        "mechanic.gaoler-grapple", "mechanic.inured-to-pain", "mechanic.giggle-juice-spray",
        "mechanic.daemonic-flesh", "condition.djinns-curse-active", "condition.djinns-luck-active",
        "poison.giggle-juice", "mechanic.solkan-inquisitor", "mechanic.solkan-witch-finder",
        "condition.witch-finder-charge", "condition.tomb-robber-dodge-known",
        "condition.bear-handler-nearby", "condition.command.raise-our-insignia",
        "condition.goading-charge", "condition.netted", "condition.nuttaz-charge",
        "condition.poetry-inspired", "condition.poetry-victorious-leader",
        "mechanic.bear-handler", "mechanic.bear-handler-recipient", "mechanic.dim-witted-leader",
        "mechanic.herb-lore-outside-combat", "mechanic.magic-acorn",
        "mechanic.undead-construct", "mechanic.marianna-no-pain-jump-up",
        "mechanic.festooned-with-pistols",
        "mechanic.deathblow",
        "mechanic.fear-beastmen", "mechanic.hatred-beastmen",
        "condition.summoned-this-turn",
        "weapon.count-of-ventimiglias-misericordia",
    }
    local_modifier_tags = {
        "mechanic.confound-and-confuse", "mechanic.dodge-sidestepper",
        "mechanic.babbling-banter", "mechanic.mantle-of-crows", "skill.backstabber",
        "mechanic.needle-and-thread", "mechanic.hillman-lycanthrope",
        "mechanic.ghostly-howl",
        "rule.thin-flesh", "rule.slay-large-creature",
        "mechanic.kindred-hatred", "mechanic.guiding-dream", "mechanic.myrmidia-eagle-friend", "mechanic.dueling-pride", "mechanic.pikewall", "mechanic.taal-tranquil-fauna", "mechanic.sigmar-symbol-of-unity", "mechanic.shallya-strictures", "mechanic.shallya-tranquil-aura", "defence.holy-relic", "weapon.arcane-candelabrum", "mechanic.snorri-drunk", "skill.righteous-fury", "mechanic.first-failed-leadership-reroll", "mechanic.sigmar-enlightened", "mechanic.ulric-intense-rivals", "mechanic.morrs-servant", "mechanic.marine-hunter", "mechanic.flesh-peddler", "mechanic.norse-shieldmaster", "condition.righteous-charge", "mechanic.righteous-charge", "mechanic.undivided-leader", "mechanic.wizened-halfling", "mechanic.goblin-squabble", "mechanic.fear-human", "condition.command.follow-me-mine-pugnacious-ones", "condition.command.art-thou-ready-to-die-fighting", "mechanic.beauty-of-the-sea", "mechanic.wheelo-impact", "mechanic.noble-disdain", "weapon.hellblade", "mechanic.hatred-undead", "mechanic.blessing-of-morr", "mechanic.torturer", "mechanic.mesmerising-dance", "mechanic.charm-immunity", "mechanic.mark-of-shornaal", "mechanic.hypnotist", "mechanic.wraith-touch", "mechanic.titanic-strength", "mechanic.foul-odour", "mechanic.centigor-drunken", "mechanic.ethereal-hit-save", "mechanic.ghost-pirate-ethereal", "mechanic.unholy-stink", "mechanic.andanti-knowledge", "mechanic.fears-fire", "mechanic.hatred-human-warband", "mechanic.hatred-chaotic-warband", "mechanic.hatred-skaven", "mechanic.hatred-dwarfs", "mechanic.hatred-skaven-orcs-goblins", "mechanic.hatred-dwarfs-skaven", "mechanic.hatred-orcs-goblins", "mechanic.animal-friendship", "mechanic.honorable", "dance.whirling-death", "dance.storm-of-blades", "dance.the-shadows-coil", "dance.woven-mist", "mechanic.bat-injury-chart", "mechanic.fen-hard-to-kill", "mechanic.magical-void", "mechanic.hard-to-rattle", "mechanic.questing-vow", "mechanic.rousing-sermon", "mechanic.frantic", "mechanic.great-thirster", "mechanic.curse-of-the-revenant", "rule.squishy", "mechanic.psychology-immunity", "mechanic.fear-immunity", "mechanic.fear-reroll", "mechanic.leadership-reroll", "mechanic.mandatory-leadership-reroll", "mechanic.hatred-dark-elves", "mechanic.hatred-high-elves", "mechanic.handler-leadership", "mechanic.brood-mentality", "mechanic.stupidity", "condition.stupidity-exempt", "mechanic.craven", "mechanic.cold-blooded-leadership", "mechanic.cold-blooded-psychology", "weapon.beastlash", "mechanic.causes-fear", "mechanic.leader-six", "mechanic.automatic-leadership", "mechanic.seaguard-spear-master", "rule.strikes-last-bite", "mechanic.sabretusk-charge", "skill.cutthroat", "skill.wound-valour", "mechanic.sea-troll-slime", "mechanic.wolf-rat-bite", "mechanic.gypsy-ward", "mechanic.ravening-onslaught", "skill.crude-belch-halfling",
    }
    weapon_profile_tags = {
        "weapon.pry-bar", "weapon.kanabo", "weapon.wizards-staff", "weapon.katana",
        "weapon.shock-rod", "weapon.skull-busta", "weapon.long-daggers",
        "weapon.knuckledusters",
    }
    behaviours = frozenset({
        # Dynamic EffectSet values (critical threshold, ethereal save, fire
        # negation) are still resolved only by the modular engine.
        "effect-values",
        "vomit",
        "spectral-touch",
        "shifty",
        "killing-blow",
    })
    return PendingCapabilities(
        frozenset(residual_tags), frozenset(local_modifier_tags),
        frozenset(weapon_profile_tags), behaviours,
    )


#: Behaviors whose NumPy runtime path is connected end to end.  The native
#: gate keeps rejecting all of them until Cython ports the same behavior.
NUMPY_CONNECTED_TAGS = frozenset({
    # Round integration (G06)
    "mechanic.stupidity", "condition.stupidity-exempt", "mechanic.causes-fear",
    "mechanic.fear-human", "mechanic.fear-immunity", "mechanic.fear-reroll",
    "mechanic.craven", "skill.crude-belch-halfling", "mechanic.crude-belch-ogre",
    "mechanic.centigor-drunken", "mechanic.goblin-squabble", "mechanic.fungus-rowdy",
    "dance.whirling-death", "dance.storm-of-blades", "dance.the-shadows-coil",
    "dance.woven-mist", "mechanic.hypnotist", "mechanic.taal-tranquil-fauna",
    "defence.eye-pendant", "mechanic.great-thirster", "mechanic.curse-of-the-revenant",
    "mechanic.death-blow", "mechanic.nominated-strike-first", "mechanic.noblesse-stomp",
    "mechanic.gaoler-grapple", "condition.netted", "mechanic.bitten-transform",
    "mechanic.electrical-touch", "condition.alchemist-backleys-brew",
    "condition.alchemist-addicted", "condition.alchemist-aberrantius-vigortia",
    "mechanic.leader-six",
})


#: Non-tag behaviours whose NumPy runtime path is now complete.
NUMPY_CONNECTED_BEHAVIOURS = frozenset({
    "effect-values", "vomit", "spectral-touch", "shifty", "killing-blow",
})


def _numpy_gate() -> PendingCapabilities:
    """The NumPy gate minus every behavior the driver now executes."""
    base = _pending_snapshot()
    return PendingCapabilities(
        base.residual_tags - NUMPY_CONNECTED_TAGS,
        base.local_modifier_tags - NUMPY_CONNECTED_TAGS,
        base.weapon_profile_tags - NUMPY_CONNECTED_TAGS,
        base.behaviours - NUMPY_CONNECTED_BEHAVIOURS,
    )


#: NumPy admission gate. Port groups replace this value when a behavior lands.
NUMPY_PENDING = _numpy_gate()
#: Native admission gate: frozen until the Cython port covers the behavior.
NATIVE_PENDING = _pending_snapshot()
_PENDING: dict[str, PendingCapabilities] = {
    "numpy": NUMPY_PENDING,
    "native": NATIVE_PENDING,
}


def pending_capabilities(backend: OptimizedBackend) -> PendingCapabilities:
    """Return the admission gate for one optimized backend.

    Read-only for callers: a port group replaces the entry in ``_PENDING``
    rather than mutating the returned snapshot.
    """
    try:
        return _PENDING[backend]
    except KeyError:
        raise ValueError(f"unknown optimized backend: {backend}") from None


def require_optimized_support(
    first: CompiledFighter, second: CompiledFighter, *,
    backend: OptimizedBackend | None = None,
) -> None:
    """Refuse modular-only choices before an optimized engine can omit them.

    ``backend`` names the engine that will actually run, so the NumPy path and
    the native path are admitted independently. Legacy calls without a backend
    keep the conservative native gate; they never gain support because NumPy
    advanced.
    """
    pending = _PENDING["native"] if backend is None else pending_capabilities(backend)
    if any(set(effect.tags) & pending.residual_tags
           or ("effect-values" in pending.behaviours and (
               effect.critical_threshold != 6 or effect.ethereal_hit_save != 4
               or effect.natural_armour_negated_by_fire))
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Residual modular effects require the modular engine; optimized ports are pending")
    if any(set(effect.tags) & pending.local_modifier_tags
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Local modifier variants currently require the modular engine; optimized ports are pending")
    if "vomit" in pending.behaviours and any(fighter.vomit_attack is not None for fighter in (first, second)):
        raise ValueError("optional Vomit Attack currently requires the modular engine; optimized ports are pending")
    if "spectral-touch" in pending.behaviours and any(
            "trait.spectral-touch" in effect.tags
            for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Spectral Touch currently requires the modular engine; optimized ports are pending")
    if "shifty" in pending.behaviours and any(
            "skill.shifty" in effect.tags
            for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Shifty currently requires the modular engine; optimized ports are pending")
    if "killing-blow" in pending.behaviours and any(
            "mechanic.killing-blow" in effect.tags
            for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Killing Blow currently requires the modular engine; optimized ports are pending")
    if any(set(effect.tags) & pending.weapon_profile_tags
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Printed weapon profiles currently require the modular engine; optimized ports are pending")


def compile_duel_plan(
    first: CompiledFighter, second: CompiledFighter,
    *, certified_tags: Collection[str] | None = None,
    context: DuelContext | None = None,
    backend: OptimizedBackend | None = None,
) -> DuelKernelPlan:
    require_optimized_support(first, second, backend=backend)
    tag_ids = tuple(sorted({tag for fighter in (first, second) for effect in _effects(fighter)
                            for tag in effect.tags}))
    indices = {tag: index for index, tag in enumerate(tag_ids)}
    eligible = certified_tags is None or set(tag_ids) <= set(certified_tags)
    return DuelKernelPlan(
        1, tag_ids, _fighter_plan(first, indices), _fighter_plan(second, indices), eligible,
        prepare_duel_context(first, second, context),
    )
