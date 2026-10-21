"""Parity battery catalog: variants, witnesses and cases (P01).

P00 revision 4 + addenda A8-A10 fix the contract.  This module is data only:
it declares variants, their typed witnesses and reusable cases.  It never
imports an engine, compiles a fighter or runs a duel; ``resolve_context`` is the
single lazy bridge for the context providers P02 has to compile.

Membership is transferred once from the P00 inventory through
``_battery_keys.py`` (1914 keys, 63 variants).  There is no runtime read of
``P00-results`` and no second manual registry.

Profiles are cumulative by case id: ``quick`` subset ``complete`` subset
``deep``.  A case declares the rule, state, context and decisions of its E2E
origin; a missing candidate capability is an explicit ``blocked_by`` dependency
(``state:``, ``consume:``, ``witness:``, ``decision:``), never a weaker duel.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

from mordheim_core.models import Characteristics, DuelContext, FighterBuild

from mordheim_combat_lab.verification.parity._battery_keys import (
    INVENTORY_SHA256,
    VARIANT_BEHAVIOUR,
    VARIANT_KEYS,
    VARIANT_ORDER,
    VARIANT_TITLES,
)

__all__ = [
    "INVENTORY_SHA256",
    "OBLIGATIONS",
    "OBSERVABLES",
    "OUTCOMES",
    "PROFILE_LEVELS",
    "ProviderSpec",
    "ContextSpec",
    "VARIANT_KEYS",
    "VARIANTS",
    "WITNESSES",
    "BatteryCase",
    "Obligation",
    "Variant",
    "Witness",
    "battery_cases",
    "required_variants",
    "resolve_context",
    "validate_cases",
    "validate_keys",
    "validate_origins",
]

PROFILE_LEVELS = ("quick", "complete", "deep")
OUTCOMES = ("winner", "rounds", "wounds", "condition")

WitnessKind = Literal["counter", "flag", "category", "direct-result", "hash"]
Predicate = Literal[
    "count>0", "count==0", "flag-true", "flag-false",
    "class-equals", "class-differs",
    "value-equals", "value-differs",
    "hash-changes", "hash-same",
]

_KIND_PREDICATES: Mapping[str, tuple[str, str]] = {
    "counter": ("count>0", "count==0"),
    "flag": ("flag-true", "flag-false"),
    "category": ("class-equals", "class-differs"),
    "direct-result": ("value-equals", "value-differs"),
    "hash": ("hash-changes", "hash-same"),
}


@dataclass(frozen=True, slots=True)
class Witness:
    name: str
    kind: WitnessKind
    present: Predicate
    absent: Predicate


def _witness(name: str, kind: WitnessKind) -> Witness:
    present, absent = _KIND_PREDICATES[kind]
    return Witness(name, kind, present, absent)  # type: ignore[arg-type]


#: Typed witness vocabulary fixed by P00 §7.6.  A variant names one of these.
_WITNESS_TABLE: tuple[tuple[str, WitnessKind], ...] = (
    ("lucky-charm", "counter"),
    ("force-of-will", "counter"),
    ("mark-of-the-old-ones", "counter"),
    ("luck", "counter"),
    ("frenzy", "flag"),
    ("devoted-frenzy", "flag"),
    ("on-fire", "flag"),
    ("entangled", "flag"),
    ("force-of-will-active", "flag"),
    ("broken-hands", "flag"),
    ("hampered", "flag"),
    ("disability", "flag"),
    ("netted", "flag"),
    ("grappled", "flag"),
    ("entranced", "flag"),
    ("fear-hit-sixes", "counter"),
    ("fear-test-skipped", "flag"),
    ("psychology-test-skipped", "flag"),
    ("psychology-dice", "direct-result"),
    ("stupidity-failed", "flag"),
    ("animosity-failed", "flag"),
    ("feral-instinct-failed", "flag"),
    ("leadership-first-failed", "counter"),
    ("leadership-auto-pass", "flag"),
    ("leadership-test-value", "direct-result"),
    ("poetry-first-leadership", "flag"),
    ("hit-modified", "counter"),
    ("wound-modified", "counter"),
    ("strength-modified", "counter"),
    ("armour-save-rolled", "counter"),
    ("special-save-rolled", "counter"),
    ("parried", "counter"),
    ("attack-count", "counter"),
    ("acting-order", "category"),
    ("reroll-used", "counter"),
    ("equipment", "hash"),
)

WITNESSES: Mapping[str, Witness] = {
    name: _witness(name, kind) for name, kind in _WITNESS_TABLE
}

OBSERVABLES = tuple(OUTCOMES) + tuple(WITNESSES)


@dataclass(frozen=True, slots=True)
class ProviderSpec:
    """A nearby compile input; ``resolve_context`` compiles it for P02."""

    participant_id: str
    side_id: str
    fighter: FighterBuild
    condition: str = "standing"


@dataclass(frozen=True, slots=True)
class ContextSpec:
    """Local facts whose providers still need compiling by the runner."""

    nearby: tuple[ProviderSpec, ...] = ()
    distances: tuple[tuple[str, str, float], ...] = ()
    charging: tuple[str, ...] | None = None
    active_participant: str | None = None
    contacts: tuple[tuple[str, str], ...] | None = None
    terrain: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class Variant:
    id: str
    title: str
    witness: Witness | None
    case_kind: Literal["duel", "structural", "unlocated"] = "duel"
    required: bool = True
    level: Literal["quick", "complete", "deep"] = "complete"
    owner: str = "G06"
    evidence: str = ""
    secondary: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Obligation:
    id: str
    family: str
    variants: tuple[Variant, ...]


@dataclass(frozen=True, slots=True)
class BatteryCase:
    id: str
    level: Literal["quick", "complete", "deep"]
    variant: str
    origin: str
    first: FighterBuild
    second: FighterBuild
    rows: int = 64
    seed: int = 2026
    maximum_rounds: int = 50
    context: DuelContext | ContextSpec | None = None
    decisions: Mapping[str, bool] = field(default_factory=dict)
    decision_scope: Literal["uniform", "per-row"] = "uniform"
    observables: tuple[str, ...] = OUTCOMES
    expect: Literal["present", "absent"] = "present"
    positive_control: str | None = None
    witness_value: int | str | None = None
    also_covers: tuple[str, ...] = ()
    comparison: Literal["witness", "focused"] = "witness"
    focused: str | None = None
    requires: tuple[str, ...] = ()
    blocked_by: str | None = None
    note: str = ""


# ---------------------------------------------------------------------------
# Variant table: (id, witness, case_kind, level, owner, secondary)
# ---------------------------------------------------------------------------

_VARIANT_TABLE: tuple[tuple[str, str | None, str, str, str, tuple[str, ...]], ...] = (
    ("B00.1", None, "structural", "complete", "G01", ()),
    ("B01.1", None, "duel", "complete", "G02/G06", ()),
    ("B01.2", "force-of-will", "duel", "complete", "G06", ()),
    ("B01.3", "netted", "duel", "complete", "G02/G06", ()),
    ("B01.5", None, "duel", "complete", "G00/G02", ()),
    ("B01.6", None, "duel", "complete", "G02", ()),
    ("B02.2", "hit-modified", "duel", "complete", "G06", ()),
    ("B02.3", "reroll-used", "duel", "complete", "G06", ()),
    ("B02.4", "hit-modified", "duel", "complete", "G06", ()),
    ("B03.2", "wound-modified", "duel", "complete", "G06", ()),
    ("B03.3", "strength-modified", "duel", "complete", "G06", ("B10.1",)),
    ("B03.4", "wound-modified", "duel", "complete", "G06", ()),
    ("B03.5", "on-fire", "duel", "quick", "G06", ()),
    ("B04.1", "armour-save-rolled", "duel", "quick", "G06", ()),
    ("B04.2", "armour-save-rolled", "duel", "quick", "G06", ()),
    ("B04.3", "armour-save-rolled", "duel", "complete", "G06", ("B06.2",)),
    ("B05.1", "special-save-rolled", "duel", "complete", "G06", ()),
    ("B05.2", "special-save-rolled", "duel", "complete", "G06", ()),
    ("B06.1", "parried", "duel", "quick", "G06", ()),
    ("B06.2", "parried", "duel", "complete", "G06", ()),
    ("B06.3", None, "duel", "complete", "G06", ()),
    ("B07.1", "condition", "duel", "quick", "P03/G06", ()),
    ("B07.2", "condition", "duel", "quick", "G06", ()),
    ("B07.3", "condition", "duel", "complete", "G06", ()),
    ("B08.1", "attack-count", "duel", "complete", "G06", ()),
    ("B08.2", "attack-count", "duel", "complete", "G06", ()),
    ("B08.4", "attack-count", "duel", "complete", "G06", ()),
    ("B08.5", "attack-count", "duel", "complete", "G06", ()),
    ("B09.1", None, "structural", "complete", "P01", ()),
    ("B09.2", "equipment", "duel", "complete", "G02/G06", ()),
    ("B09.3", "netted", "duel", "complete", "G05/G06", ()),
    ("B10.1", "acting-order", "duel", "complete", "G06", ()),
    ("B10.2", None, "duel", "complete", "G06", ()),
    ("B10.3", "attack-count", "duel", "quick", "G06", ()),
    ("B10.4", None, "duel", "complete", "G06", ()),
    ("B11.1", "fear-hit-sixes", "duel", "quick", "G05/G06", ()),
    ("B11.2", "fear-test-skipped", "duel", "complete", "G05/G06", ()),
    ("B11.3", "psychology-test-skipped", "duel", "complete", "G05/G06", ()),
    ("B11.4", "fear-test-skipped", "duel", "complete", "G05/G06", ()),
    ("B11.5", "psychology-dice", "duel", "complete", "G05/G06", ()),
    ("B11.6", "reroll-used", "duel", "complete", "G05/G06", ()),
    ("B11.7", "frenzy", "duel", "complete", "G02/G06", ("B02.2",)),
    ("B12.1", "stupidity-failed", "duel", "complete", "G05/G06", ()),
    ("B14.1", "leadership-first-failed", "duel", "quick", "G05/G06", ()),
    ("B14.2", "leadership-first-failed", "duel", "complete", "G05/G06", ()),
    ("B14.3", "leadership-auto-pass", "duel", "complete", "G05/G06", ()),
    ("B14.4", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.5", "leadership-first-failed", "duel", "complete", "G05/G06", ()),
    ("B14.6", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.7", "stupidity-failed", "duel", "complete", "G05/G06", ()),
    ("B14.8", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.9", "reroll-used", "duel", "complete", "G05/G06", ()),
    ("B14.10", "leadership-first-failed", "duel", "complete", "G05/G06", ()),
    ("B14.11", "leadership-auto-pass", "duel", "complete", "G05/G06", ()),
    ("B14.12", "leadership-first-failed", "duel", "complete", "G05/G06", ()),
    ("B14.13", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B15.1", "wounds", "duel", "quick", "G06", ()),
    ("B15.2", "wounds", "duel", "complete", "G06", ()),
    ("B15.3", "wounds", "duel", "complete", "G00/G02", ()),
    ("B15.4", "attack-count", "duel", "complete", "G03/G06", ()),
    ("B15.5", "wound-modified", "duel", "complete", "G03/G06", ()),
    ("B15.6", "strength-modified", "duel", "complete", "G02/G06", ()),
    ("B99.1", None, "unlocated", "complete", "G01", ()),
)

_EVIDENCE = {
    "B06.1": "exact operator check `parry`; E2E core/combat-parry",
    "B07.1": "exact `injury` check is defective (P03); E2E chart",
    "B04.2": "shared-operator; `armour` grid lacks natural-armour fields",
    "B09.1": "compiler-only; no duel case",
    "B99.1": "consumer does not name a decisive operator",
    "B14.1": "modular `leadership.py` reads nearby/distance; candidate does not consume yet",
}

def _variant_witness(name: str | None) -> Witness | None:
    if name is None:
        return None
    # A9: condition/wounds are direct-result outcomes, not WITNESSES entries.
    if name in {"condition", "wounds"}:
        return _witness(name, "direct-result")
    return WITNESSES[name]


_VARIANTS: dict[str, Variant] = {}
for _id, _witness_name, _kind, _level, _owner, _secondary in _VARIANT_TABLE:
    _VARIANTS[_id] = Variant(
        id=_id,
        title=VARIANT_TITLES[_id],
        witness=_variant_witness(_witness_name),
        case_kind=_kind,  # type: ignore[arg-type]
        required=True,  # A8: pending input never removes a base variant
        level=_level,  # type: ignore[arg-type]
        owner=_owner,
        evidence=_EVIDENCE.get(_id, "P00 §4.4"),
        secondary=_secondary,
    )

VARIANTS: Mapping[str, Variant] = dict(_VARIANTS)
if set(VARIANTS) != set(VARIANT_ORDER):  # pragma: no cover - import guard
    raise RuntimeError("variant table does not match the transferred inventory")

_OBLIGATIONS: dict[str, Obligation] = {}
for _variant in VARIANTS.values():
    _family = VARIANT_BEHAVIOUR[_variant.id]
    _OBLIGATIONS.setdefault(
        _family.split("-")[0], Obligation(_family.split("-")[0], _family, ()),
    )
    _existing = _OBLIGATIONS[_family.split("-")[0]]
    _OBLIGATIONS[_family.split("-")[0]] = Obligation(
        _existing.id, _existing.family, (*_existing.variants, _variant),
    )
OBLIGATIONS: Mapping[str, Obligation] = dict(_OBLIGATIONS)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

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
    distance: float, *, rule: str = "mechanic.leader-six",
    provider_skills: tuple[str, ...] | None = None,
    provider: FighterBuild | None = None,
    second_id: str = "second",
) -> ContextSpec:
    leader = provider or _fighter(
        collection="mordheim", band="amazons-lustria", profile="serpent-priestess",
        skills=(rule,) if provider_skills is None else provider_skills,
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


def _case(
    id: str, level: str, variant: str, origin: str,
    first: FighterBuild, second: FighterBuild, *,
    requires: tuple[str, ...] = (),
    context: DuelContext | ContextSpec | None = None,
    decisions: Mapping[str, bool] | None = None,
    decision_scope: str = "uniform",
    observables: tuple[str, ...] | None = None,
    expect: str = "present",
    positive_control: str | None = None,
    witness_value: int | str | None = None,
    also_covers: tuple[str, ...] = (),
    comparison: str = "witness",
    focused: str | None = None,
    blocked_by: str | None = None,
    rows: int = 64,
    maximum_rounds: int = 50,
    note: str = "",
) -> BatteryCase:
    witness = VARIANTS[variant].witness
    if observables is None:
        declared = list(OUTCOMES)
        if witness is not None and witness.name not in declared:
            declared.append(witness.name)
        observables = tuple(declared)
    return BatteryCase(
        id=id, level=level, variant=variant, origin=origin,  # type: ignore[arg-type]
        first=first, second=second, rows=rows, maximum_rounds=maximum_rounds,
        context=context, decisions=dict(decisions or {}),
        decision_scope=decision_scope,  # type: ignore[arg-type]
        observables=observables, expect=expect,  # type: ignore[arg-type]
        positive_control=positive_control, witness_value=witness_value,
        also_covers=also_covers, comparison=comparison,  # type: ignore[arg-type]
        focused=focused, requires=requires, blocked_by=blocked_by,
        note=note,
    )


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

_CASES: tuple[BatteryCase, ...] = (
    # -- quick regression representatives ------------------------------------
    _case(
        "q04-injury-chart", "quick", "B07.1",
        "e2e:core/combat-critical-hits::natural-six-critical-triggers-the-chart",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        witness_value="stunned",
        note="Resultado directo de la tabla de lesión; condición declarada.",
    ),
    _case(
        "q04-parry-attempt", "quick", "B06.1",
        "e2e:core/combat-parry::sword-parries-one-hit",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        blocked_by="witness:G06",
        note="Intento de parada con espada; testigo `parried` aún no publicado.",
    ),
    _case(
        "q04-natural-armour-six", "quick", "B04.2",
        "e2e:rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/"
        "trait.natural-armour-save::the-shaggy-hide-saves-on-six",
        _fighter(weapon="weapon.sword", strength=4),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastman-chief",
                 specials=("trait.natural-armour-save",)),
        context=_charging(), maximum_rounds=1,
        requires=("trait.natural-armour-save",),
        blocked_by="witness:G06",
        note="Piel natural 6+ materializada con la banda del origen, no armadura ligera.",
    ),
    _case(
        "q05-flammable-fire", "quick", "B03.5",
        "e2e:rule/mordheim/restless-dead/scarecrows--flammable/trait.flammable::"
        "a-fire-attack-wounds-the-printed-scarcrow-twice-over",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(collection="mordheim", band="restless-dead", profile="scarecrows",
                 specials=("trait.flammable",), wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.brazier-iron", "trait.flammable"),
        blocked_by="witness:G06",
        note="Ataque de fuego (braser) contra inflamable; el testigo es on-fire.",
    ),
    _case(
        "q06-intrinsic-save", "quick", "B04.1",
        "e2e:rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/"
        "profile.equipment-restrictions::the-intrinsic-cage-save-holds-on-five",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 defence=("defence.shield",)),
        context=_charging(), maximum_rounds=1,
        blocked_by="witness:G06",
        note="Save intrínseco y armadura llevada en la misma resolución.",
    ),
    _case(
        "q08-death-blow-optional", "quick", "B10.3",
        "e2e:mechanic/mechanic.death-blow::the-bearer-declines-and-attacks-normally",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.death-blow",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.death-blow",),
        decisions={"round.0.first.death-blow": False},
        blocked_by="witness:G06",
        note="Decisión de rechazo declarada; sin guion sería NOT_RUN:decision-script.",
    ),
    _case(
        "q09-fear-charged", "quick", "B11.1",
        "e2e:rule/mordheim/beastmen-raiders/minotaur--fear/mechanic.causes-fear::"
        "a-charged-opponent-that-fails-its-fear-test-hits-only-with-sixes",
        _fighter(weapon="weapon.mace", leadership=7),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.causes-fear",),
        blocked_by="consume:G05",
        note="Miedo en la carga; el candidato aún no ejecuta la fase (G05).",
    ),
    _case(
        "q10-leader-six", "quick", "B14.1",
        "e2e:rule/mordheim/amazons-lustria/serpent-priestess--leader/mechanic.leader-six::"
        "a-supplied-leader-at-six-inches-lends-his-leadership",
        _fighter(weapon="weapon.mace", leadership=6),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(6), maximum_rounds=2,
        requires=("mechanic.leader-six",),
        blocked_by="consume:G05",
        note="Líder en `nearby` a 6\"; el duelista conserva su prueba.",
    ),
    _case(
        "q11-black-hunger", "quick", "B15.1",
        "e2e:mechanic/mechanic.black-hunger::the-backlash-ignores-armour",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.black-hunger",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.black-hunger",),
        witness_value=-1,
        note="Reacción de la propia fase: una herida al horizonte; regla en el build.",
    ),
    _case(
        "q00-honorable", "quick", "B10.4",
        "e2e:rule/mordheim/adventurers-kaz/imperial-noble--honorable/mechanic.honorable::"
        "no-attack-is-made-against-a-knocked-down-opponent",
        _fighter(weapon="weapon.sword", skills=("mechanic.honorable",)),
        _fighter(weapon="weapon.mace", conditions=("condition.knocked-down",)),
        context=_charging(), maximum_rounds=1,
        requires=("mechanic.honorable", "condition.knocked-down"),
        blocked_by="witness:G06",
        note="Regla y estado del rival derribado; el estado inicial aún no se inyecta.",
    ),
    # -- complete: repaired and reused cases ---------------------------------
    _case(
        "c04-parry-reroll", "complete", "B06.2",
        "e2e:core/combat-parry::sword-and-buckler-reroll-a-failed-parry",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", defence=("defence.buckler",)),
        context=_charging(), maximum_rounds=3,
        requires=("defence.buckler",),
        blocked_by="witness:G06",
        note="Rodela en el defensor; repetición de parada y capacidad en varias rondas.",
    ),
    _case(
        "c04-stand-up-last", "complete", "B10.2",
        "e2e:core/combat-injury-states::recovery-belongs-to-the-fighters-own-turn",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3,
                 conditions=("condition.knocked-down",)),
        context=_battle(), maximum_rounds=4,
        requires=("condition.knocked-down",),
        blocked_by="witness:G06",
        note="Derribo declarado; el observable de orden/recuperación falta (G06).",
    ),
    _case(
        "c04-highest-injury", "quick", "B07.2",
        "e2e:core/combat-injury-states::highest-injury-result-applies",
        _fighter(weapon="weapon.mace", strength=4, attacks=2),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        witness_value="out",
        note="Dos heridas en la misma fase; se conserva el peor resultado.",
    ),
    _case(
        "c04-hard-head", "complete", "B07.1",
        "e2e:rule/mordheim/adventurers-kaz/dwarf--hard-head/trait.concussion-immune::"
        "the-mace-no-longer-converts-a-two-into-a-stun",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", specials=("trait.concussion-immune",)),
        context=_charging(), maximum_rounds=2,
        requires=("trait.concussion-immune",), witness_value="stunned",
        note="Inmunidad a conmoción en la tabla de lesión.",
    ),
    _case(
        "c04-hard-to-kill", "complete", "B07.1",
        "e2e:rule/mordheim/adventurers-kaz/dwarf--hard-to-kill/skill.hard-to-kill::"
        "a-five-only-stuns-the-adventurer-dwarf",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", skills=("skill.hard-to-kill",)),
        context=_charging(), maximum_rounds=2,
        requires=("skill.hard-to-kill",), witness_value="stunned",
        note="Borde exacto 5: aturde en lugar de sacar de combate.",
    ),
    _case(
        "c04-thick-skull", "complete", "B07.1",
        "e2e:rule/mordheim/black-dwarfs/band--chaos-dwarf-special-skills-thick-skull/"
        "skill.thick-skull::the-printed-three-converts-the-stun",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", skills=("skill.thick-skull",)),
        context=_charging(), maximum_rounds=2,
        requires=("skill.thick-skull",), witness_value="stunned",
        note="Reacción de cráneo grueso sobre el aturdimiento.",
    ),
    _case(
        "c04-hide-combines", "complete", "B04.2",
        "e2e:rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/"
        "trait.natural-armour-save::a-shield-takes-the-hide-to-five",
        _fighter(weapon="weapon.sword", strength=3),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastman-chief",
                 specials=("trait.natural-armour-save",),
                 defence=("defence.shield",)),
        context=_charging(), maximum_rounds=1,
        requires=("trait.natural-armour-save", "defence.shield"),
        blocked_by="witness:G06",
        note="Piel natural combinada con escudo; variante de parámetro.",
    ),
    _case(
        "c04-hide-stacks", "complete", "B04.2",
        "e2e:rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/"
        "trait.natural-armour-stacks::the-hide-combines-with-a-carried-shield-on-the-recorded-five",
        _fighter(weapon="weapon.sword", strength=3),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastman-chief",
                 specials=("trait.natural-armour-stacks",),
                 defence=("defence.shield",)),
        context=_charging(), maximum_rounds=1,
        requires=("trait.natural-armour-stacks", "defence.shield"),
        blocked_by="witness:G06",
        note="Acumulación por pieles; no se sustituye por armadura.",
    ),
    _case(
        "c00-amazon-isolationists", "complete", "B02.3",
        "e2e:rule/mordheim/amazons-lustria/band--special-rules/"
        "mechanic.amazon-isolationists::the-first-round-miss-against-lizardmen-is-taken-again",
        _fighter(weapon="weapon.sword", wounds=3,
                 skills=("mechanic.amazon-isolationists",)),
        _fighter(collection="mordheim", band="amazons-lustria", profile="eagle-warriors"),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.amazon-isolationists",),
        blocked_by="witness:G06",
        note="Repetición de impacto en la primera ronda contra el enemigo declarado.",
    ),
    _case(
        "c00-questing-vow", "complete", "B11.6",
        "e2e:rule/mordheim/bretonnian-chapel-guard/band--questing-vow/"
        "mechanic.questing-vow::the-failed-test-against-a-fear-causer-is-taken-again",
        _fighter(weapon="weapon.sword", skills=("mechanic.questing-vow",)),
        _fighter(weapon="weapon.mace", wounds=3, specials=("mechanic.causes-fear",)),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.questing-vow", "mechanic.causes-fear"),
        blocked_by="consume:G05",
        note="Repetición de un test de miedo fallido (modificador de la prueba).",
    ),
    _case(
        "c05-poltergeist-immediate-out", "complete", "B07.1",
        "e2e:rule/mordheim/call-of-the-night-haint-mim/poltergeists--incorporeal/"
        "trait.injury-profile::the-first-wound-takes-the-poltergeist-out-without-an-injury-roll",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword",
                 specials=("trait.injury-profile",), wounds=2),
        context=_charging(), maximum_rounds=1,
        requires=("trait.injury-profile",), witness_value="out",
        note="Perfil de lesión inmediata: la primera herida resuelve sin tirada.",
    ),
    _case(
        "c05-ethereal-improved", "complete", "B05.1",
        "e2e:rule/mordheim/call-of-the-night-haint-mim/mourngul--haunter-of-the-dark/"
        "unimplemented.call-of-the-night-haint-mim.mourngul.haunter-of-the-dark::"
        "the-improved-ethereal-save-discards-a-hit-on-three",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", defence=("defence.ethereal",), wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("defence.ethereal",),
        blocked_by="witness:G06",
        note="Save etéreo mejorado declarado como defensa del segundo.",
    ),
    _case(
        "c05-bear-hug", "complete", "B08.5",
        "e2e:rule/mordheim/channel-rats-mim/domnu--bear-hug/"
        "unimplemented.channel-rats-mim.domnu.bear-hug::"
        "two-unarmed-hits-are-replaced-by-one-unsaveable-bear-hug-wound",
        _fighter(weapon="weapon.fist", attacks=2,
                 specials=("rule.bear-hug",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("rule.bear-hug", "weapon.fist"),
        blocked_by="witness:G06",
        note="Dos impactos desarmados se sustituyen por un agarre; recuento de ataques.",
    ),
    _case(
        "c03-petru-potion", "complete", "B01.3",
        "e2e:rule/mordheim/channel-rats-mim/petru--potions/"
        "unimplemented.channel-rats-mim.petru.potions::"
        "the-strength-draught-raises-the-affected-heroes-strength-by-one",
        _fighter(weapon="weapon.mace",
                 preparations=("preparation.mandrake-root",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("preparation.mandrake-root",),
        blocked_by="state:G00/G02",
        note="Preparación inicial declarada; la inyección de estado no existe aún.",
    ),
    _case(
        "c08-death-blow-decline", "complete", "B10.3",
        "e2e:rule/trollheim/chaos-streets-deathbringers/"
        "band--deathbringer-special-skills-death-blow/mechanic.death-blow::"
        "the-bearer-declines-and-attacks-normally",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.death-blow",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=3,
        requires=("mechanic.death-blow",),
        decisions={"round.0.first.death-blow": False},
        blocked_by="witness:G06",
        note="Uso opcional rechazado; el pool conserva los ataques normales.",
    ),
    _case(
        "c09-troll-fear", "complete", "B11.1",
        "e2e:rule/mordheim/black-orcs/troll--fear/mechanic.causes-fear::"
        "a-charged-opponent-that-passes-its-fear-test-fights-normally",
        _fighter(weapon="weapon.mace", leadership=7),
        _fighter(collection="mordheim", band="black-orcs", profile="troll",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.causes-fear",),
        blocked_by="consume:G05",
        note="Cara opuesta del miedo: test superado; la fase no se ejecuta aún (G05).",
    ),
    _case(
        "c09-beastlash-fear", "complete", "B11.1",
        "e2e:mechanic/weapon.beastlash::"
        "beastlash-fear-test-is-required-of-an-animal-that-is-charged",
        _fighter(weapon="weapon.beastlash"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.beastlash",),
        blocked_by="consume:G05",
        note="Disparador beastlash + animal cargado; la variante de parada es B06.3.",
    ),
    _case(
        "c10-leader-absence", "complete", "B14.1",
        "new:control sin líder — el mismo duelista conserva su Ld",
        _fighter(weapon="weapon.mace", leadership=6),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(8), maximum_rounds=2,
        requires=("mechanic.leader-six",),
        expect="absent", positive_control="q10-leader-six",
        blocked_by="consume:G05",
        note="Mismo proveedor a 8\": fuera del radio de 6\", no debe prestar valor.",
    ),
    _case(
        "c10-leader-swapped", "complete", "B14.1",
        "new:dirigido — dirección del participante intercambiada",
        _fighter(weapon="weapon.sword", wounds=3),
        _fighter(weapon="weapon.mace", leadership=6),
        context=ContextSpec(
            nearby=(ProviderSpec("leader", "second",
                                 _fighter(collection="mordheim", band="amazons-lustria",
                                          profile="serpent-priestess",
                                          skills=("mechanic.leader-six",))),),
            distances=(("second", "leader", 6),),
            charging=("second",), active_participant="second",
        ), maximum_rounds=2,
        requires=("mechanic.leader-six",),
        blocked_by="consume:G05",
        note="La misma construcción con el líder como segundo participante.",
    ),
    _case(
        "c11-curse-of-revenant", "complete", "B15.2",
        "e2e:mechanic/mechanic.curse-of-the-revenant::"
        "a-five-restores-one-lost-wound-at-the-own-turn-start",
        _fighter(weapon="weapon.mace", skills=("mechanic.curse-of-the-revenant",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=4,
        requires=("mechanic.curse-of-the-revenant",),
        witness_value=1,
        note="Recuperación 5+ al inicio del turno propio; una herida, con tope.",
    ),
    _case(
        "c11-great-thirster", "complete", "B11.7",
        "e2e:mechanic/mechanic.great-thirster::"
        "taking-the-opponent-out-of-action-grants-frenzy",
        _fighter(weapon="weapon.mace", strength=4, skills=("mechanic.great-thirster",)),
        _fighter(weapon="weapon.sword", wounds=1),
        context=_charging(), maximum_rounds=3,
        requires=("mechanic.great-thirster",),
        blocked_by="witness:G02/G06",
        note="Frenesí tras sacar de acción al oponente; se pierde al quedar derribado.",
    ),
    _case(
        "c11-acid-blood", "complete", "B15.4",
        "e2e:rule/mordheim/cult-of-the-possessed/band--mutations-blackblood/"
        "trait.acid-blood::an-unsaved-wound-answers-with-the-printed-strength-three-hit",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3, specials=("trait.acid-blood",)),
        context=_charging(), maximum_rounds=2,
        requires=("trait.acid-blood",),
        blocked_by="witness:G03/G06",
        note="Sangre ácida: S3 automática al perder una herida, no recuperación.",
    ),
    _case(
        "c11-spines", "complete", "B15.4",
        "e2e:rule/mordheim/cult-of-the-possessed/band--mutations-spines/trait.spines::"
        "the-automatic-spines-hit-lands-on-the-contacting-opponent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3, specials=("trait.spines",)),
        context=_charging(), maximum_rounds=2,
        requires=("trait.spines",),
        blocked_by="witness:G03/G06",
        note="Espinas: S1 al inicio de la fase de close combat; disparador distinto del ácido.",
    ),
    _case(
        "d09-fear-charge-parry", "deep", "B11.1",
        "new:interacción miedo → carga → parada",
        _fighter(weapon="weapon.sword", leadership=7),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=2,
        requires=("mechanic.causes-fear",),
        blocked_by="consume:G05",
        note="El miedo altera el pool antes de la parada; composición declarada.",
    ),
    _case(
        "d10-leader-retest", "deep", "B14.1",
        "new:interacción liderazgo → retest de psicología",
        _fighter(weapon="weapon.mace", leadership=6),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_leader_context(6), maximum_rounds=2,
        requires=("mechanic.leader-six", "mechanic.causes-fear"),
        blocked_by="consume:G05",
        note="Dos familias comparten el test de liderazgo; el orden cambia el resultado.",
    ),
    _case(
        "d04-long-horizon", "deep", "B06.2",
        "new:horizonte largo de desgaste",
        _fighter(weapon="weapon.sword", defence=("defence.buckler",), wounds=3),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging(), maximum_rounds=12,
        requires=("defence.buckler",),
        blocked_by="witness:G06",
        note="Doce rondas para observar capacidad de parada y recuperación.",
    ),
    _case(
        "d08-force-of-will", "deep", "B01.2",
        "new:interacción fuerza de voluntad → levantarse → ronda siguiente",
        _fighter(weapon="weapon.mace", strength=4,
                 skills=("mechanic.force-of-will",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=6,
        requires=("mechanic.force-of-will",),
        decisions={"round.0.first.force-of-will": True},
        blocked_by="witness:G06",
        note="Recurso de un solo uso y recuperación en el horizonte.",
    ),
    _case(
        "d05-spines-regeneration", "deep", "B15.4",
        "new:interacción espinas → varias heridas en la misma fase",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", wounds=3, specials=("trait.spines",)),
        context=_charging(), maximum_rounds=6,
        requires=("trait.spines",),
        blocked_by="witness:G03/G06",
        note="Espinas y heridas múltiples; no se reutiliza el criterio de B15.2.",
    ),
    _case(
        "d06-transform-equipment", "deep", "B09.2",
        "e2e:rule/mordheim/masters-of-horror-sylv/the-bitten--transform/"
        "unimplemented.masters-of-horror-sylv.the-bitten.transform::"
        "transforming-casts-off-the-worn-armour",
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 specials=("rule.bitten-transform",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=4,
        requires=("rule.bitten-transform", "armour.light-armour"),
        witness_value="starting-loadout",
        blocked_by="witness:G02/G06",
        note="Pérdida de armadura intra-duelo; hash de equipo no exportado.",
    ),
    # -- one material case for every remaining duel variant ------------------
    _case(
        "v01-profile", "complete", "B01.1",
        "new:perfil y características iniciales",
        _fighter(collection="mordheim", band="adventurers-kaz", profile="imperial-noble"),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=1,
        blocked_by="witness:G02/G06",
        note="Campos iniciales compilados; sin testigo por fila.",
    ),
    _case(
        "v01-restriction", "complete", "B01.5",
        "new:restricción de carga suministrada",
        _fighter(weapon="weapon.sword", skills=("mechanic.shallya-strictures",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.shallya-strictures",),
        blocked_by="state:G00/G02",
        note="Restricción de elección declarada; la entrada aún no se suministra.",
    ),
    _case(
        "v01-random", "complete", "B01.6",
        "new:característica aleatoria/avance",
        _fighter(weapon="weapon.mace", specials=("profile.random-characteristics",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("profile.random-characteristics",),
        blocked_by="state:G00/G02",
        note="Valores iniciales/avance suministrados; pendiente de inyección.",
    ),
    _case(
        "v02-hatred", "complete", "B02.2",
        "new:hatred contra la identidad declarada",
        _fighter(weapon="weapon.sword", skills=("skill.hatred",)),
        _fighter(collection="mordheim", band="dwarf-rangers", profile="dwarf-clansman"),
        context=_charging(), maximum_rounds=2,
        requires=("skill.hatred",),
        blocked_by="witness:G06",
        note="Repetición de impacto solo contra la identidad odiada.",
    ),
    _case(
        "v02-hit-reroll", "complete", "B02.3",
        "new:reroll de impacto por skill",
        _fighter(weapon="weapon.sword", skills=("skill.expert-swordsman",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("skill.expert-swordsman",),
        blocked_by="witness:G06",
        note="Un impacto fallido se repite una vez.",
    ),
    _case(
        "v02-general-hit", "complete", "B02.4",
        "new:modificador general de impacto",
        _fighter(weapon="weapon.duelling-pistol"),
        _fighter(weapon="weapon.sword"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.duelling-pistol",),
        blocked_by="witness:G06",
        note="Bonificador de impacto del arma declarado.",
    ),
    _case(
        "v03-poison", "complete", "B03.2",
        "new:veneno e inmunidad",
        _fighter(weapon="weapon.sword", main_material="material.normal"),
        _fighter(weapon="weapon.mace", specials=("trait.poison-immune",)),
        context=_charging(), maximum_rounds=2,
        requires=("trait.poison-immune",),
        blocked_by="witness:G06",
        note="Inmunidad al veneno materializada; el veneno cambia la tirada de herida.",
    ),
    _case(
        "v03-strength", "complete", "B03.3",
        "new:bonificación de fuerza",
        _fighter(weapon="weapon.sword", skills=("skill.mighty-biceps",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("skill.mighty-biceps",),
        blocked_by="witness:G06",
        note="Fuerza efectiva modificada; strongman también toca prioridad (B10.1).",
    ),
    _case(
        "v03-wound-reroll", "complete", "B03.4",
        "new:reroll/daño de herida",
        _fighter(weapon="weapon.sword", skills=("skill.sure-strike",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("skill.sure-strike",),
        blocked_by="witness:G06",
        note="Repetición de herida fallida; no se infiere de heridas terminales.",
    ),
    _case(
        "v04-buckler-armour", "complete", "B04.3",
        "new:el buckler no mejora la armadura",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 defence=("defence.buckler",)),
        context=_charging(), maximum_rounds=2,
        requires=("defence.buckler", "armour.light-armour"),
        blocked_by="witness:G06",
        note="Save de armadura sin bonificación; la parada se declara en B06.2.",
    ),
    _case(
        "v05-regeneration", "complete", "B05.2",
        "new:save de regeneración y bloqueo por fuego",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", specials=("trait.regeneration",)),
        context=_charging(), maximum_rounds=2,
        requires=("trait.regeneration",),
        blocked_by="witness:G06",
        note="Save por herida; la recuperación es B15.2, no esta variante.",
    ),
    _case(
        "v06-parry-denial", "complete", "B06.3",
        "new:ataque que niega la parada",
        _fighter(weapon="weapon.war-maul"),
        _fighter(weapon="weapon.sword", defence=("defence.buckler",)),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.war-maul", "defence.buckler"),
        blocked_by="witness:G06",
        note="La negación no tiene contador negativo publicado; no se usa `parried`.",
    ),
    _case(
        "v07-weapon-injury", "complete", "B07.3",
        "new:modificador de lesión por arma",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        witness_value="stunned",
        note="Maza/concusión sobre la tirada de lesión.",
    ),
    _case(
        "v08-base-pool", "complete", "B08.1",
        "new:recuento base con mano torpe y pistola",
        _fighter(weapon="weapon.pistol", off_hand="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.pistol", "weapon.sword"),
        blocked_by="witness:G06",
        note="Reparto de ataques por mano; `attack-count` pendiente.",
    ),
    _case(
        "v08-extra-attack", "complete", "B08.2",
        "new:frenesí/ataque extra",
        _fighter(weapon="weapon.sword", specials=("trait.frenzy",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("trait.frenzy",),
        blocked_by="witness:G06",
        note="+1 ataque solo con la regla; no se acredita por la etiqueta.",
    ),
    _case(
        "v08-unarmed", "complete", "B08.4",
        "new:combate sin armas",
        _fighter(weapon="weapon.fist", skills=("skill.unarmed-fighting",)),
        _fighter(weapon="weapon.sword"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.fist", "skill.unarmed-fighting"),
        blocked_by="witness:G06",
        note="Sin penalización por desarmado; recuento y fuerza.",
    ),
    _case(
        "v09-netted", "complete", "B09.3",
        "e2e:rule/mordheim/crooked-moon-kep/band--night-goblin-special-skills/"
        "unimplemented.crooked-moon-kep.band.night-goblin-special-skills::"
        "without-the-band-netter-rule-the-charge-asks-for-no-net-die",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.dagger", conditions=("condition.netted",)),
        context=_charging(), maximum_rounds=2,
        requires=("condition.netted",),
        blocked_by="witness:G05/G06",
        note="Estado de red declarado en el defensor; init de estado pendiente.",
    ),
    _case(
        "v10-priority", "complete", "B10.1",
        "new:prioridad y orden de actuación",
        _fighter(weapon="weapon.pike", initiative=2),
        _fighter(weapon="weapon.sword", initiative=5),
        context=_charging(), maximum_rounds=1,
        requires=("weapon.pike",),
        witness_value=0,
        blocked_by="witness:G06",
        note="Categoría 0/1: el pike con carga actúa primero; no se evalúa con >0.",
    ),
    _case(
        "v10-round-state", "complete", "B10.4",
        "new:estado y modificadores por ronda",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=6,
        blocked_by="witness:G06",
        note="Cierre de ronda; sin testigo por fila, solo horizonte declarado.",
    ),
    _case(
        "v11-immunity", "complete", "B11.2",
        "new:inmunidad plena a miedo",
        _fighter(weapon="weapon.mace", skills=("mechanic.fear-immunity",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.fear-immunity", "mechanic.causes-fear"),
        blocked_by="consume:G05",
        note="La prueba de miedo no se toma; las demás pruebas siguen.",
    ),
    _case(
        "v11-psych-immunity", "complete", "B11.3",
        "new:inmunidad completa a psicología",
        _fighter(weapon="weapon.mace", skills=("mechanic.psychology-immunity",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.psychology-immunity", "mechanic.causes-fear"),
        blocked_by="consume:G05",
        note="No se toma ninguna prueba de psicología, no solo la de miedo.",
    ),
    _case(
        "v11-conditional-immunity", "complete", "B11.4",
        "new:inmunidad condicionada al cargante no-muerto",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.fear-immunity-undead-chargers",)),
        _fighter(collection="mordheim", band="undead", profile="skeleton-warriors",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.fear-immunity-undead-chargers", "mechanic.causes-fear"),
        blocked_by="consume:G05",
        note="La condición (cargante no-muerto) forma parte del contrato.",
    ),
    _case(
        "v11-conditional-absent", "complete", "B11.4",
        "new:control fuera de la condición (cargante vivo)",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.fear-immunity-undead-chargers",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.fear-immunity-undead-chargers", "mechanic.causes-fear"),
        expect="absent", positive_control="v11-conditional-immunity",
        blocked_by="consume:G05",
        note="Fuera de la condición la prueba se toma; el control positivo la omite.",
    ),
    _case(
        "v11-cold-blood", "complete", "B11.5",
        "new:sangre fría psicológica (3D6, conservar 2)",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.cold-blooded-psychology",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur",
                 specials=("mechanic.causes-fear",)),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.cold-blooded-psychology", "mechanic.causes-fear"),
        witness_value=3,
        blocked_by="consume:G05",
        note="La prueba se hace: 3 dados y se descarta el mayor; no es inmunidad.",
    ),
    _case(
        "v12-stupidity", "complete", "B12.1",
        "new:tirada de estupidez",
        _fighter(weapon="weapon.mace", skills=("mechanic.stupidity",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(), maximum_rounds=3,
        requires=("mechanic.stupidity",),
        blocked_by="consume:G05",
        note="Inicio de turno; pierde el turno solo si falla.",
    ),
    _case(
        "v14-leader-twelve", "complete", "B14.2",
        "new:Inspiring Presence a 12 pulgadas",
        _fighter(weapon="weapon.mace", leadership=6),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(12, rule="mechanic.leader-twelve"), maximum_rounds=2,
        requires=("mechanic.leader-twelve",),
        blocked_by="consume:G05",
        note="Mismo proveedor a 12\"; a 13\" debe dejar de prestar.",
    ),
    _case(
        "v14-auto", "complete", "B14.3",
        "new:éxito automático de liderazgo",
        _fighter(weapon="weapon.mace", skills=("mechanic.automatic-leadership",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.automatic-leadership",),
        blocked_by="consume:G05",
        note="No hay prueba que tirar; no exige líder ni radio.",
    ),
    _case(
        "v14-own", "complete", "B14.4",
        "new:liderazgo propio; préstamo prohibido",
        _fighter(weapon="weapon.mace", leadership=7,
                 skills=("mechanic.own-leadership",)),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(6), maximum_rounds=2,
        requires=("mechanic.own-leadership", "mechanic.leader-six"),
        witness_value=7,
        blocked_by="consume:G05",
        note="El líder cercano no cambia la prueba; valor propio declarado.",
    ),
    _case(
        "v14-handler", "complete", "B14.5",
        "new:liderazgo de cuidador a 6 pulgadas",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.handler-leadership",)),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim", band="adventurers-kaz",
                                 profile="bear-handler",
                                 skills=("mechanic.handler-leadership",)),
        ), maximum_rounds=2,
        requires=("mechanic.handler-leadership",),
        blocked_by="consume:G05",
        note="Usa el valor del handler, nunca el líder de banda.",
    ),
    _case(
        "v14-mob", "complete", "B14.6",
        "new:bonificación por aliados a 3 pulgadas",
        _fighter(weapon="weapon.mace", skills=("mechanic.mob-leadership",),
                 traits={"mob_allies": 1}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.mob-leadership",),
        witness_value=8,
        blocked_by="consume:G05",
        note="+1 Ld por aliado suministrado en `mob_allies`; no se simula la banda.",
    ),
    _case(
        "v14-brood", "complete", "B14.7",
        "new:Brood Mentality solo para estupidez",
        _fighter(weapon="weapon.mace", skills=("mechanic.brood-mentality",),
                 conditions=("condition.stupidity",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("mechanic.brood-mentality", "condition.stupidity"),
        blocked_by="consume:G05",
        note="Bonificación suministrada a la prueba de estupidez, no al liderazgo.",
    ),
    _case(
        "v14-cold-blood", "complete", "B14.8",
        "new:sangre fría de liderazgo (3D6, conservar 2)",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.cold-blooded-leadership",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.cold-blooded-leadership",),
        witness_value=8,
        blocked_by="consume:G05",
        note="La prueba se hace con 3D6 y descarte del mayor; valor declarado.",
    ),
    _case(
        "v14-reroll", "complete", "B14.9",
        "new:reroll de liderazgo",
        _fighter(weapon="weapon.mace", skills=("mechanic.leadership-reroll",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.leadership-reroll",),
        blocked_by="consume:G05",
        note="Primera prueba fallida repetida una vez.",
    ),
    _case(
        "v14-relay", "complete", "B14.10",
        "new:relay orders a 6 pulgadas",
        _fighter(weapon="weapon.mace", leadership=6),
        _fighter(weapon="weapon.sword"),
        context=ContextSpec(
            nearby=(
                ProviderSpec("relay", "first",
                             _fighter(collection="mordheim", band="amazons-lustria",
                                      profile="serpent-priestess",
                                      skills=("mechanic.relay-orders",)),
                             ),
                ProviderSpec("leader", "first",
                             _fighter(collection="mordheim", band="amazons-lustria",
                                      profile="serpent-priestess",
                                      skills=("mechanic.leader-six",)),
                             ),
            ),
            distances=(("first", "relay", 6), ("relay", "leader", 6)),
            charging=("first",), active_participant="first",
        ), maximum_rounds=2,
        requires=("mechanic.relay-orders", "mechanic.leader-six"),
        blocked_by="consume:G05",
        note="El relay transmite el valor del líder, nunca el suyo.",
    ),
    _case(
        "v14-relic-first", "complete", "B14.11",
        "new:reliquia sagrada en la primera prueba",
        _fighter(weapon="weapon.mace", defence=("defence.holy-relic",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("defence.holy-relic",),
        blocked_by="consume:G05",
        note="La primera prueba de liderazgo es automática.",
    ),
    _case(
        "v14-relic-second", "complete", "B14.11",
        "new:reliquia sagrada en la segunda prueba",
        _fighter(weapon="weapon.mace", defence=("defence.holy-relic",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("defence.holy-relic",),
        expect="absent", positive_control="v14-relic-first",
        blocked_by="consume:G05",
        note="La segunda prueba se tira; el control positivo la hace automática.",
    ),
    _case(
        "v14-slave", "complete", "B14.12",
        "new:slave driver a 3/6 pulgadas",
        _fighter(weapon="weapon.mace",
                 conditions=("identity.slave",)),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            3, provider=_fighter(collection="mordheim", band="adventurers-kaz",
                                 profile="slave-driver",
                                 skills=("mechanic.slave-driver",)),
        ), maximum_rounds=2,
        requires=("mechanic.slave-driver", "identity.slave"),
        blocked_by="consume:G05",
        note="Usa el valor del overseer; el líder de banda no se usa.",
    ),
    _case(
        "v14-modifiers", "complete", "B14.13",
        "new:modificadores de liderazgo",
        _fighter(weapon="weapon.mace", skills=("mechanic.feral-instinct",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.feral-instinct",),
        witness_value=6,
        blocked_by="consume:G05",
        note="Penalización de la prueba sin prestar valor.",
    ),
    _case(
        "v15-monstrous", "complete", "B15.3",
        "new:incremento del máximo de heridas",
        _fighter(weapon="weapon.mace", skills=("skill.monstrous",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=1,
        requires=("skill.monstrous",),
        witness_value=3,
        note="+1 Herida inicial (2+1); no es curación.",
    ),
    _case(
        "v15-contagious", "complete", "B15.5",
        "new:reacción al quedar fuera de acción",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=1, specials=("trait.contagious",)),
        context=_charging(), maximum_rounds=2,
        requires=("trait.contagious",),
        blocked_by="witness:G03/G06",
        note="Prueba de T del atacante tras sacar de acción; no-muertos exentos.",
    ),
    _case(
        "v15-torturer", "complete", "B15.6",
        "new:pérdida de Fuerza por herida no salvada",
        _fighter(weapon="weapon.sword", skills=("mechanic.torturer",)),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.torturer",),
        blocked_by="witness:G02/G06",
        note="−1 F por herida no salvada, acumulativo; no es daño.",
    ),
)


def battery_cases(
    level: str = "complete", cases: tuple[BatteryCase, ...] = _CASES,
) -> tuple[BatteryCase, ...]:
    """Return the cases of ``level`` and every cheaper profile, by id."""
    if level not in PROFILE_LEVELS:
        raise ValueError(f"unknown battery profile {level!r}; choose {PROFILE_LEVELS}")
    limit = PROFILE_LEVELS.index(level)
    return tuple(case for case in cases if PROFILE_LEVELS.index(case.level) <= limit)


def required_variants(level: str = "complete") -> tuple[str, ...]:
    """Duel variants a profile must represent; structural variants excluded."""
    if level not in PROFILE_LEVELS:
        raise ValueError(f"unknown battery profile {level!r}; choose {PROFILE_LEVELS}")
    limit = PROFILE_LEVELS.index(level)
    return tuple(
        variant.id for variant in VARIANTS.values()
        if variant.case_kind == "duel" and PROFILE_LEVELS.index(variant.level) <= limit
    )


_BLOCKED_PREFIXES = ("state:", "consume:", "witness:", "decision:")


def _build_ids(build: FighterBuild) -> set[str]:
    values: set[str] = set()
    for name in (
        "main_weapon_id", "off_hand_id", "armour_id", "main_material_id",
        "off_material_id", "profile_id", "band_id",
    ):
        value = getattr(build, name, None)
        if isinstance(value, str):
            values.add(value)
    for name in (
        "defence_ids", "skill_ids", "preparation_ids", "special_rule_ids",
        "condition_ids", "variant_ids",
    ):
        values.update(getattr(build, name, ()) or ())
    values.update(str(key) for key in (build.trait_overrides or {}))
    return values


def validate_cases(
    cases: tuple[BatteryCase, ...] = _CASES, *, require_coverage: bool = True,
) -> None:
    """Check the P00 rev4 + A8-A10 invariants that need no engine execution."""
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("battery case ids must be unique")
    seen: dict[str, BatteryCase] = {}
    for case in cases:
        if case.level not in PROFILE_LEVELS:
            raise ValueError(f"unknown profile level in {case.id}: {case.level}")
        variant = VARIANTS.get(case.variant)
        if variant is None:
            raise ValueError(f"{case.id} names unknown variant {case.variant}")
        if variant.case_kind != "duel":
            raise ValueError(f"{case.id} uses non-duel variant {case.variant}")
        if variant.witness is not None and variant.witness.name not in case.observables:
            raise ValueError(f"{case.id} omits its witness {variant.witness.name}")
        if "winner" not in case.observables:
            raise ValueError(f"{case.id} must always observe the winner")
        unknown = set(case.observables) - set(OBSERVABLES)
        if unknown:
            raise ValueError(f"{case.id} declares unknown observables {sorted(unknown)}")
        if not case.origin.startswith(("e2e:", "spec:", "new:")):
            raise ValueError(f"{case.id} has an unsupported origin {case.origin!r}")
        if not case.id:
            raise ValueError("battery case id cannot be empty")
        if case.rows < 1 or case.seed < 0 or case.maximum_rounds < 1:
            raise ValueError(f"{case.id} has invalid sample parameters")
        if case.decision_scope not in {"uniform", "per-row"}:
            raise ValueError(f"{case.id} has an unknown decision scope")
        if case.comparison not in {"witness", "focused"}:
            raise ValueError(f"{case.id} has an unknown comparison")
        if case.blocked_by is not None and not case.blocked_by.startswith(
                _BLOCKED_PREFIXES):
            raise ValueError(f"{case.id} has an unknown blocked_by tag")
        kind = variant.witness.kind if variant.witness else None
        if kind in {"category", "direct-result", "hash"} and case.witness_value is None:
            raise ValueError(f"{case.id} needs witness_value for {kind}")
        if kind in {"counter", "flag"} and case.witness_value is not None:
            raise ValueError(f"{case.id} cannot use witness_value for {kind}")
        if case.comparison == "focused":
            if not case.focused or ":" not in case.focused:
                raise ValueError(f"{case.id} needs a focused <outcome>:<value>")
        elif case.focused is not None:
            raise ValueError(f"{case.id} declares focused without comparison=focused")
        if case.expect == "present":
            if case.positive_control is not None:
                raise ValueError(f"{case.id} is positive and cannot have a control")
        elif case.expect == "absent":
            control = seen.get(case.positive_control or "")
            if control is None:
                raise ValueError(f"{case.id} needs a declared earlier control")
            if control.variant != case.variant or control.expect != "present":
                raise ValueError(f"{case.id} control must be a positive of its variant")
            if case.comparison == "focused" and control.focused != case.focused:
                raise ValueError(f"{case.id} focused pair must share the result")
        else:
            raise ValueError(f"{case.id} has an unknown expect {case.expect!r}")
        for secondary in case.also_covers:
            if secondary not in VARIANTS or secondary == case.variant:
                raise ValueError(f"{case.id} has an invalid also_covers entry")
            other = VARIANTS[secondary]
            if other.witness is not None and other.witness.name not in case.observables:
                raise ValueError(f"{case.id} does not evaluate {secondary}'s witness")
        builds = (case.first, case.second)
        context = case.context
        if isinstance(context, ContextSpec):
            builds += tuple(provider.fighter for provider in context.nearby)
        available: set[str] = set()
        for build in builds:
            available |= _build_ids(build)
        missing = sorted(set(case.requires) - available)
        if missing:
            raise ValueError(f"{case.id} requires unmaterialized ids {missing[:5]}")
        seen[case.id] = case
    for level in PROFILE_LEVELS[1:]:
        previous = {case.id for case in battery_cases(PROFILE_LEVELS[PROFILE_LEVELS.index(level) - 1], cases)}
        current = {case.id for case in battery_cases(level, cases)}
        if not previous <= current:
            raise ValueError(f"profile {level} does not contain the previous profile")
    if require_coverage:
        covered = {
            variant for case in battery_cases("complete", cases)
            for variant in (case.variant, *case.also_covers)
        }
        missing = [variant for variant in required_variants("complete")
                   if variant not in covered]
        if missing:
            raise ValueError(f"complete does not represent variants {missing}")


def validate_keys(
    cases: tuple[BatteryCase, ...] = _CASES, admitted: set[str] | None = None,
) -> None:
    """Check membership against the transferred inventory and, if given, registry."""
    missing = sorted({
        key for case in cases for key in VARIANT_KEYS[case.variant]
        if admitted is not None and key not in admitted
    })
    if missing:
        raise ValueError(f"battery cases reference non-admitted keys: {missing[:5]}")
    for variant, keys in VARIANT_KEYS.items():
        if not keys:
            raise ValueError(f"variant {variant} has no transferred keys")


def validate_origins(
    cases: tuple[BatteryCase, ...] = _CASES, audit_ids: set[str] | None = None,
) -> None:
    """Check origin shape and, when supplied, that the E2E identity exists."""
    for case in cases:
        if case.origin.startswith("new:"):
            if len(case.origin) <= 4:
                raise ValueError(f"{case.id} has an empty new: origin")
            continue
        if "::" not in case.origin:
            raise ValueError(f"{case.id} origin lacks '<audit>::<scenario>': {case.origin}")
        if audit_ids is not None and case.origin.startswith("e2e:"):
            audit = case.origin[4:].split("::", 1)[0]
            if audit not in audit_ids:
                raise ValueError(f"{case.id} references missing audit {audit}")


validate_cases()
validate_origins()
validate_keys()
