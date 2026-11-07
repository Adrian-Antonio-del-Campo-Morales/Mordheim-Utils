"""The statistical battery: short duels that isolate one mechanic each.

122 duel configurations of one to three rounds, built from the knowledge base
rather than frozen, where a single rule decides the outcome.  A long duel
averages a defect away; these do not.  They are selected like any other
scenario (``--scenarios battery`` or ``battery/<id>``) and compared by the one
parity comparison -- nothing here grades a case by itself.

This module is data: it never imports an engine, compiles a fighter or runs a
duel.  ``resolve_context`` is the single lazy bridge for the context providers
the caller compiles.  Two cases declare an input the engines cannot express
(``blocked_by``); ``input_limit`` names it so a run reports them instead of
quietly running a different duel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from mordheim_core.models import Characteristics, DuelContext, FighterBuild

__all__ = [
    "BatteryCase",
    "ContextSpec",
    "ProviderSpec",
    "battery_cases",
    "input_limit",
    "resolve_context",
]


@dataclass(frozen=True, slots=True)
class ProviderSpec:
    """A nearby compile input; ``resolve_context`` compiles it."""

    participant_id: str
    side_id: str
    fighter: FighterBuild
    condition: str = "standing"


@dataclass(frozen=True, slots=True)
class ContextSpec:
    """Local facts whose providers still need compiling by the caller."""

    nearby: tuple[ProviderSpec, ...] = ()
    distances: tuple[tuple[str, str, float], ...] = ()
    charging: tuple[str, ...] | None = None
    active_participant: str | None = None
    contacts: tuple[tuple[str, str], ...] | None = None
    terrain: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class BatteryCase:
    """One short duel: the inputs, the horizon and any declared limit."""

    id: str
    first: FighterBuild
    second: FighterBuild
    maximum_rounds: int = 50
    seed: int = 2026
    context: DuelContext | ContextSpec | None = None
    decisions: Mapping[str, bool] = field(default_factory=dict)
    #: An input the current build cannot produce (``state:``/``decision:``).
    blocked_by: str | None = None


def _case(
    id: str, first: FighterBuild, second: FighterBuild, *,
    context: DuelContext | ContextSpec | None = None,
    decisions: Mapping[str, bool] | None = None,
    blocked_by: str | None = None,
    maximum_rounds: int = 50,
) -> BatteryCase:
    return BatteryCase(
        id=id, first=first, second=second, maximum_rounds=maximum_rounds,
        context=context, decisions=dict(decisions or {}), blocked_by=blocked_by,
    )


def _characteristics(
    weapon_skill: int = 3, strength: int = 3, toughness: int = 3,
    wounds: int = 2, initiative: int = 3, attacks: int = 1, leadership: int = 7,
) -> Characteristics:
    return Characteristics(
        weapon_skill=weapon_skill, strength=strength, toughness=toughness,
        wounds=wounds, initiative=initiative, attacks=attacks,
        leadership=leadership,
    )


def _fighter(
    *,
    weapon: str | None = None,
    off_hand: str | None = None,
    armour: str | None = None,
    defence: tuple[str, ...] = (),
    collection: str | None = None,
    band: str | None = None,
    profile: str | None = None,
    skills: tuple[str, ...] = (),
    preparations: tuple[str, ...] = (),
    specials: tuple[str, ...] = (),
    conditions: tuple[str, ...] = (),
    main_material: str | None = None,
    off_material: str | None = None,
    poison: str | None = None,
    traits: Mapping[str, object] | None = None,
    **chars: int,
) -> FighterBuild:
    options: dict[str, object] = {}
    if weapon is not None:
        options["main_weapon_id"] = weapon
    if off_hand is not None:
        options["off_hand_id"] = off_hand
    if armour is not None:
        options["armour_id"] = armour
    if defence:
        options["defence_ids"] = tuple(defence)
    if collection is not None:
        options["collection"] = collection
    if band is not None:
        options["band_id"] = band
    if profile is not None:
        options["profile_id"] = profile
    if skills:
        options["skill_ids"] = tuple(skills)
    if preparations:
        options["preparation_ids"] = tuple(preparations)
    if specials:
        options["special_rule_ids"] = tuple(specials)
    if conditions:
        options["condition_ids"] = tuple(conditions)
    if main_material is not None:
        options["main_material_id"] = main_material
    if off_material is not None:
        options["off_material_id"] = off_material
    if poison is not None:
        options["main_poison_id"] = poison
    if traits:
        options["trait_overrides"] = dict(traits)
    if profile is None:
        options.setdefault("main_weapon_id", "weapon.mace")
        options["characteristics"] = _characteristics(**chars)
    return FighterBuild("mordheim", **options)


def _battle() -> DuelContext:
    return DuelContext(charging=(), active_participant="first")


def _charging(side: str = "first") -> DuelContext:
    return DuelContext(charging=(side,), active_participant=side)


def _leader_context(
    distance: float, *, provider: FighterBuild | None = None,
) -> ContextSpec:
    # The provider's canonical profile carries its own grant: ``serpent-priestess``
    # declares ``serpent-priestess--leader`` (grant: profile), which compiles
    # ``mechanic.leader-six``.  A mechanic id is never supplied as a skill of a
    # canonical profile: its ``skill_access`` rejects it before sampling.
    leader = provider or _fighter(
        collection="mordheim", band="amazons-lustria", profile="serpent-priestess",
    )
    return ContextSpec(
        nearby=(ProviderSpec("leader", "first", leader),),
        distances=(("first", "leader", distance),),
        charging=("first",), active_participant="first",
    )


def resolve_context(context, root) -> DuelContext | None:
    """Compile a ``ContextSpec`` for P02; a real DuelContext passes through."""
    if context is None or isinstance(context, DuelContext):
        return context
    from mordheim_construction.compiler import compile_fighter
    from mordheim_core.models import LocalParticipant

    nearby = tuple(
        LocalParticipant(
            participant_id=provider.participant_id,
            side_id=provider.side_id,
            fighter=compile_fighter(provider.fighter, root),
            condition=provider.condition,
        )
        for provider in context.nearby
    )
    return DuelContext(
        nearby=nearby,
        distances=context.distances,
        charging=context.charging,
        active_participant=context.active_participant,
        contacts=context.contacts,
        terrain=context.terrain,
    )


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

_CASES: tuple[BatteryCase, ...] = (
    # -- quick regression representatives ------------------------------------
    _case(
        "q04-injury-chart",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "q04-parry-attempt",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "q04-parry-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "q04-natural-armour-six",
        _fighter(weapon="weapon.sword", strength=4),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastmen-chieftain",
                 specials=("band--beastmen-special-skills-shaggy-hide",)),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "q05-flammable-fire",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(collection="mordheim", band="restless-dead", profile="scarecrows"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c03-flammable-absent",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "q06-intrinsic-save",
        _fighter(weapon="weapon.sword"),
        _fighter(collection="mordheim", band="ghost-pirates-sar", profile="gibbets"),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "q08-death-blow-optional",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.death-blow",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
        decisions={"round.0.first.death-blow": False,
                   "round.1.first.death-blow": False},
    ),
    _case(
        "q09-fear-charged",
        _fighter(weapon="weapon.mace", leadership=7),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "q10-leader-six",
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(6),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "q11-black-hunger",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.black-hunger",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c15-hunger-absent",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "q00-honorable",
        _fighter(weapon="weapon.sword", wounds=3),
        _fighter(weapon="weapon.mace", strength=4, attacks=2,
                 skills=("mechanic.honorable",)),
        context=_battle(),
        maximum_rounds=2,
    ),
    # -- complete: repaired and reused cases ---------------------------------
    _case(
        "c04-parry-reroll",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler"),
        context=_charging(),
        maximum_rounds=3,
    ),
    _case(
        "c06-two-swords-one-attempt",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", off_hand="weapon.sword"),
        context=_charging(),
        maximum_rounds=3,
    ),
    _case(
        "c06-two-parries",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", off_hand="weapon.sword",
                 skills=("skill.unbeatable-warrior",)),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c06-two-swords-capacity",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", off_hand="weapon.sword"),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c06-reroll-capacity",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler", wounds=3),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c04-stand-up-last",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(),
        maximum_rounds=4,
    ),
    _case(
        "c04-highest-injury",
        _fighter(weapon="weapon.mace", strength=4, attacks=2),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c04-hard-head",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", traits={"concussion_immune": True}),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c04-hard-to-kill",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", skills=("skill.hard-to-kill",)),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c04-thick-skull",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", skills=("skill.thick-skull",)),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c04-hide-combines",
        _fighter(weapon="weapon.sword", strength=3),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastmen-chieftain",
                 specials=("band--beastmen-special-skills-shaggy-hide",),
                 off_hand="defence.shield"),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "c00-amazon-isolationists",
        _fighter(weapon="weapon.sword", wounds=3,
                 skills=("mechanic.amazon-isolationists",)),
        _fighter(collection="mordheim", band="lizardmen", profile="saurus-braves"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c00-questing-vow",
        _fighter(weapon="weapon.sword", skills=("mechanic.questing-vow",)),
        _fighter(weapon="weapon.mace", wounds=3, traits={"causes_fear": True}),
        context=_charging(),
        maximum_rounds=2,
        decisions={"round.0.first.fear.charge.reroll": True},
    ),
    _case(
        "c00-questing-vow-absent",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3, traits={"causes_fear": True}),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c05-poltergeist-immediate-out",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword",
                 traits={"injury_profile": 2}, wounds=2),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "c05-ethereal-improved",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.ethereal-hit-save-improved",), wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c05-ethereal-save",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", skills=("mechanic.ethereal-hit-save",)),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c05-ethereal-bypass",
        _fighter(weapon="weapon.mace", traits={"magical_attacks": True}),
        _fighter(weapon="weapon.mace", skills=("mechanic.ethereal-hit-save",)),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c05-bear-hug",
        _fighter(collection="mordheim", band="channel-rats-mim", profile="domnu",
                 weapon="weapon.fist"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
        decisions={"round.0.first.bear-hug": True,
                   "round.1.first.bear-hug": True},
    ),
    _case(
        "c03-petru-potion",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
        blocked_by="state:preparation.strength-draught",
    ),
    _case(
        "c08-death-blow-decline",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.death-blow",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=3,
        decisions={"round.0.first.death-blow": False,
                   "round.1.first.death-blow": False,
                   "round.2.first.death-blow": False},
    ),
    _case(
        "c09-troll-fear",
        _fighter(weapon="weapon.mace", leadership=7),
        _fighter(collection="mordheim", band="black-orcs", profile="troll"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "c09-beastlash-fear",
        _fighter(weapon="weapon.beastlash"),
        _fighter(collection="mordheim", band="house-guard-sc", profile="warhounds",
                 traits={"house_guard_house": "fierezza"}),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "c10-leader-absence",
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(8),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "c10-leader-swapped",
        _fighter(weapon="weapon.sword", wounds=3),
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors", traits={"stupidity": True}),
        context=ContextSpec(
            nearby=(ProviderSpec("leader", "second",
                                 _fighter(collection="mordheim", band="amazons-lustria",
                                          profile="serpent-priestess")),),
            distances=(("second", "leader", 6),),
            charging=("second",), active_participant="second",
        ),
        maximum_rounds=2,
        decisions={"round.0.second.stupidity.leader.leader": True},
    ),
    _case(
        "c11-curse-of-revenant",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.great-thirster", "mechanic.curse-of-the-revenant")),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=4,
    ),
    _case(
        "c11-great-thirster",
        _fighter(weapon="weapon.mace", strength=4, skills=("mechanic.great-thirster",)),
        _fighter(weapon="weapon.sword", wounds=1),
        context=_charging(),
        maximum_rounds=3,
    ),
    _case(
        "c11-acid-blood",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3, traits={"acid_blood": True}),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c11-acid-blood-absent",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "c11-spines",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3, traits={"spines": True}),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "c11-spines-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "d09-fear-charge-parry",
        _fighter(weapon="weapon.sword", leadership=7),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=2,
    ),
    _case(
        "d10-leader-retest",
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_leader_context(6),
        maximum_rounds=2,
        decisions={"round.0.first.fear.charge.leader.leader": True},
    ),
    _case(
        "d04-long-horizon",
        _fighter(weapon="weapon.sword", off_hand="defence.buckler", wounds=3),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging(),
        maximum_rounds=12,
    ),
    _case(
        "d08-force-of-will",
        _fighter(weapon="weapon.mace", strength=4,
                 skills=("mechanic.force-of-will",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=6,
    ),
    _case(
        "d05-spines-injury",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", wounds=3, traits={"spines": True}),
        context=_charging(),
        maximum_rounds=6,
    ),
    # -- one material case for every remaining duel variant ------------------
    _case(
        "v01-profile",
        _fighter(collection="mordheim", band="adventurers-kaz", profile="imperial-noble"),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=1,
    ),
    _case(
        "v01-restriction",
        _fighter(weapon="weapon.sword", skills=("mechanic.shallya-strictures",)),
        _fighter(weapon="weapon.mace"),
        context=_battle(),
        maximum_rounds=2,
        blocked_by="state:mechanic.shallya-strictures",
    ),
    _case(
        "v01-random",
        _fighter(collection="mordheim", band="marauders-of-chaos",
                 profile="condemned", weapon="weapon.fist"),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v01-force-of-will",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=1,
                 skills=("mechanic.force-of-will",)),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "v01-force-of-will-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=5,
                 skills=("mechanic.force-of-will",)),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "v02-hatred",
        _fighter(weapon="weapon.mace", skills=("mechanic.hatred-orcs-goblins",)),
        _fighter(weapon="weapon.mace", traits={"species": "orc"}),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "v02-hatred-absent",
        _fighter(weapon="weapon.mace", skills=("mechanic.hatred-orcs-goblins",)),
        _fighter(weapon="weapon.mace"),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "v02-hit-reroll",
        _fighter(weapon="weapon.sword", skills=("skill.expert-swordsman",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v02-hit-reroll-absent",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v02-general-hit",
        _fighter(weapon="weapon.duelling-pistol"),
        _fighter(weapon="weapon.sword"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v02-general-absent",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.sword"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v03-poison",
        _fighter(weapon="weapon.sword", poison="poison.black-lotus"),
        _fighter(weapon="weapon.mace", wounds=4),
        context=_charging(),
        maximum_rounds=2,
        decisions={"round.0.first.attack.0.lotus-critical": False,
                   "round.1.first.attack.0.lotus-critical": False,
                   # ``_attacks._resolve_weapon`` reaches the main pool without
                   # propagating its round key, so the candidate asks under the
                   # default key.  Declaring it keeps the intended refusal; the
                   # missing key propagation is an engine defect (TODO).
                   "test.lotus-critical": False},
    ),
    _case(
        "v03-poison-immune",
        _fighter(weapon="weapon.sword", poison="poison.black-lotus"),
        _fighter(weapon="weapon.mace", wounds=4, traits={"poison_immune": True}),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v03-strength",
        _fighter(weapon="weapon.flail", strength=2, skills=("skill.mighty-biceps",)),
        _fighter(weapon="weapon.mace"),
        context=_charging("second"),
        maximum_rounds=2,
    ),
    _case(
        "v03-strength-absent",
        _fighter(weapon="weapon.flail", strength=2),
        _fighter(weapon="weapon.mace"),
        context=_charging("second"),
        maximum_rounds=2,
    ),
    _case(
        "v03-wound-reroll",
        _fighter(weapon="weapon.sword", skills=("skill.sure-strike",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v03-wound-reroll-absent",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v04-buckler-armour",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 off_hand="defence.buckler"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v05-regeneration",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", skills=("skill.regeneration",)),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v05-regeneration-blocked",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(weapon="weapon.mace", skills=("skill.regeneration",)),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v06-parry-denial",
        _fighter(weapon="weapon.war-maul"),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v07-weapon-injury",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v08-base-pool",
        _fighter(weapon="weapon.pistol", off_hand="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v08-extra-attack",
        _fighter(weapon="weapon.sword", traits={"frenzy": True}),
        _fighter(weapon="weapon.mace"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v08-unarmed",
        _fighter(weapon="weapon.fist", skills=("skill.unarmed-fighting",)),
        _fighter(weapon="weapon.mace"),
        context=_battle(),
        maximum_rounds=1,
    ),
    _case(
        "v08-ordinary-fist",
        _fighter(weapon="weapon.fist"),
        _fighter(weapon="weapon.mace"),
        context=_battle(),
        maximum_rounds=1,
    ),
    _case(
        "v09-transform",
        _fighter(collection="mordheim", band="masters-of-horror-sylv",
                 profile="the-bitten", weapon="weapon.sword",
                 off_hand="defence.shield"),
        _fighter(weapon="weapon.mace"),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v09-netted",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.dagger", conditions=("condition.netted",)),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v09-netted-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.dagger"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v10-priority",
        _fighter(weapon="weapon.pike", initiative=2),
        _fighter(weapon="weapon.sword", initiative=5),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "v10-round-state",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=6,
    ),
    _case(
        "v11-immunity",
        _fighter(weapon="weapon.mace", skills=("mechanic.fear-immunity",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-immunity-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-psych-immunity",
        _fighter(weapon="weapon.mace", skills=("mechanic.psychology-immunity",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-psych-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-conditional-immunity",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.fear-immunity-undead-chargers",)),
        _fighter(collection="mordheim", band="blood-dragons-mou",
                 profile="skeleton-warriors"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-conditional-absent",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.fear-immunity-undead-chargers",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-cold-blood",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.cold-blooded-psychology",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v11-cold-blood-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"),
        maximum_rounds=1,
    ),
    _case(
        "v12-stupidity",
        _fighter(weapon="weapon.mace", skills=("mechanic.stupidity",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v12-stupidity-exempt",
        _fighter(weapon="weapon.mace", skills=("mechanic.stupidity",),
                 conditions=("condition.stupidity-exempt",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v14-leader-twelve",
        _fighter(collection="mordheim", band="gunnery-school-of-nuln",
                 profile="senior-student", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            12, provider=_fighter(collection="mordheim",
                                  band="gunnery-school-of-nuln",
                                  profile="senior-gunnery-officer"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "v14-leader-thirteen",
        _fighter(collection="mordheim", band="gunnery-school-of-nuln",
                 profile="senior-student", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            13, provider=_fighter(collection="mordheim",
                                  band="gunnery-school-of-nuln",
                                  profile="senior-gunnery-officer"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "v14-auto",
        _fighter(weapon="weapon.mace", skills=("mechanic.automatic-leadership",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-auto-absent",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-own",
        _fighter(collection="mordheim", band="battle-monks-of-cathay",
                 profile="raging-peasants", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim",
                                 band="battle-monks-of-cathay",
                                 profile="emissary"),
        ),
        maximum_rounds=2,
    ),
    _case(
        "v14-own-absent",
        _fighter(collection="mordheim", band="battle-monks-of-cathay",
                 profile="soldiers", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim",
                                 band="battle-monks-of-cathay",
                                 profile="emissary"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "v14-handler",
        _fighter(collection="mordheim", band="night-goblins-web",
                 profile="cave-squigs", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim", band="night-goblins-web",
                                 profile="squig-herder"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.handler.leader": True},
    ),
    _case(
        "v14-handler-absent",
        _fighter(collection="mordheim", band="night-goblins-web",
                 profile="cave-squigs", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            8, provider=_fighter(collection="mordheim", band="night-goblins-web",
                                 profile="squig-herder"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.handler.leader": True},
    ),
    _case(
        "v14-mob",
        _fighter(weapon="weapon.mace", skills=("mechanic.mob-leadership",),
                 traits={"mob_allies": 1, "stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-mob-absent",
        _fighter(weapon="weapon.mace", skills=("mechanic.mob-leadership",),
                 traits={"mob_allies": 0, "stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-brood",
        _fighter(weapon="weapon.mace", skills=("mechanic.brood-mentality",),
                 traits={"stupidity": True, "stupidity_leadership_bonus": 1}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v14-brood-absent",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v14-cold-blood",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.cold-blooded-leadership",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-cold-blood-absent",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-reroll",
        _fighter(weapon="weapon.mace", skills=("mechanic.leadership-reroll",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.reroll": True},
    ),
    _case(
        "v14-reroll-absent",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=2,
    ),
    _case(
        "v14-relay",
        _fighter(collection="mordheim", band="house-guard-sc", profile="guards",
                 traits={"stupidity": True, "house_guard_house": "fierezza"}),
        _fighter(weapon="weapon.sword"),
        context=ContextSpec(
            nearby=(
                ProviderSpec("relay", "first",
                             _fighter(collection="mordheim", band="house-guard-sc",
                                      profile="adjutant",
                                      traits={"house_guard_house": "fierezza"}),
                             ),
                ProviderSpec("leader", "first",
                             _fighter(collection="mordheim", band="house-guard-sc",
                                      profile="commander",
                                      traits={"house_guard_house": "fierezza"}),
                             ),
            ),
            distances=(("first", "relay", 6), ("relay", "leader", 6),
                       ("first", "leader", 12)),
            charging=("first",), active_participant="first",
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.relay": True},
    ),
    _case(
        "v14-relay-absent",
        _fighter(collection="mordheim", band="house-guard-sc", profile="guards",
                 traits={"stupidity": True, "house_guard_house": "fierezza"}),
        _fighter(weapon="weapon.sword"),
        context=ContextSpec(
            nearby=(
                ProviderSpec("leader", "first",
                             _fighter(collection="mordheim", band="house-guard-sc",
                                      profile="commander",
                                      traits={"house_guard_house": "fierezza"}),
                             ),
            ),
            distances=(("first", "leader", 12),),
            charging=("first",), active_participant="first",
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "v14-relic-first",
        _fighter(weapon="weapon.mace", defence=("defence.holy-relic",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=1,
    ),
    _case(
        "v14-relic-second",
        _fighter(weapon="weapon.mace", defence=("defence.holy-relic",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=3,
    ),
    _case(
        "v14-slave",
        _fighter(collection="mordheim", band="skaven-of-clan-skryre-rel",
                 profile="skaven-slaves", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            3, provider=_fighter(collection="mordheim",
                                 band="skaven-of-clan-skryre-rel",
                                 profile="overseer"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "v14-slave-absent",
        _fighter(collection="mordheim", band="skaven-of-clan-skryre-rel",
                 profile="skaven-slaves", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            7, provider=_fighter(collection="mordheim",
                                 band="skaven-of-clan-skryre-rel",
                                 profile="overseer"),
        ),
        maximum_rounds=2,
        decisions={"round.0.first.stupidity.leader.leader": True},
    ),
    _case(
        "v14-modifiers",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", skills=("mechanic.enchanting-beauty",)),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v14-modifiers-absent",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_charging(),
        maximum_rounds=2,
    ),
    _case(
        "v15-monstrous",
        _fighter(weapon="weapon.mace", skills=("skill.monstrous",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(),
        maximum_rounds=1,
    ),
    _case(
        "v15-contagious",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=1, traits={"contagious": True}),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "v15-contagious-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=1),
        context=_charging(),
        maximum_rounds=1,
    ),
    _case(
        "v15-torturer",
        _fighter(weapon="weapon.mace", skills=("mechanic.torturer",)),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    _case(
        "v15-torturer-absent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging("first"),
        maximum_rounds=1,
    ),
    # -- deep: justified interactions between already materialized rules -----
    _case(
        "d08-frenzy-parry",
        _fighter(weapon="weapon.mace", traits={"frenzy": True}),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler"),
        context=_charging(),
        maximum_rounds=3,
    ),
    _case(
        "d04-armour-parry",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 off_hand="defence.buckler"),
        context=_charging(),
        maximum_rounds=3,
    ),
    _case(
        "d10-order-attacks",
        _fighter(weapon="weapon.pike", initiative=2),
        _fighter(weapon="weapon.mace", attacks=2, initiative=5),
        context=_charging(),
        maximum_rounds=2,
    ),
)


def battery_cases(cases: tuple[BatteryCase, ...] = _CASES) -> tuple[BatteryCase, ...]:
    """Every battery case, in catalogue order."""
    return cases


def input_limit(case: BatteryCase) -> str | None:
    """The real input limitation that prevents running ``case``, if any.

    A ``state:``/``decision:`` tag means the scenario needs an input the
    current build cannot produce -- an initial state, a campaign-only
    preparation or a construction-time refusal.  Such a case is reported with
    its cause, never silently replaced by a different duel.
    """
    blocked = case.blocked_by
    if blocked is not None and blocked.startswith(("state:", "decision:")):
        return blocked
    return None
