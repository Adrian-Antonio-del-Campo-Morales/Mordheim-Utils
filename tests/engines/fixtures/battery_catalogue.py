"""Parity battery catalog: variants, scenarios and cases (P01).

This module is data only: it declares variants, their historical witness
vocabulary (kept for traceability) and reusable statistical scenarios.  It
never imports an engine, compiles a fighter or runs a duel; ``resolve_context``
is the single lazy bridge for the context providers the runner compiles.

The statistical contract compares real duel samples of the modular oracle and
of the candidate and judges the terminal outcome distribution
(``STATISTICAL_MAGNITUDES``, always starting with ``winner``).  Typed witnesses,
``expect``, ``positive_control`` and ``witness_value`` are declaration data, not
gates: a case is neither blocked nor approved by an internal event.  Only the
real input limits of ``input_limit`` (``state:``/``decision:``, including
per-row decision scripts) keep a case from running.

Membership is transferred once from the P00 inventory through
``battery_keys.py`` (1914 keys, 63 variants).  There is no runtime read of
``P00-results`` and no second manual registry.

Profiles are cumulative by case id: ``quick`` subset ``complete`` subset
``deep``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Mapping

from mordheim_core.models import Characteristics, DuelContext, FighterBuild

from tests.engines.fixtures.battery_keys import (
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
    "STATISTICAL_MAGNITUDES",
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
    "case_magnitudes",
    "input_limit",
    "required_variants",
    "resolve_context",
    "validate_cases",
    "validate_keys",
    "validate_origins",
]

PROFILE_LEVELS = ("quick", "complete", "deep")
OUTCOMES = ("winner", "rounds", "wounds", "condition")

#: Terminal magnitudes a statistical case may compare.  ``winner`` is always
#: compared; the rest are optional and only used when the case declares them
#: and both engines expose them with the same meaning.
STATISTICAL_MAGNITUDES = ("winner", "rounds", "wounds", "condition")

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
    ("leadership-first-failed", "flag"),
    ("leadership-auto-pass", "flag"),
    ("leadership-test-value", "direct-result"),
    ("poetry-first-leadership", "flag"),
    ("hit-modified", "counter"),
    ("wound-modified", "counter"),
    ("strength-modified", "counter"),
    ("armour-save-rolled", "counter"),
    ("special-save-rolled", "counter"),
    ("parried", "counter"),
    ("parry-attempts", "counter"),
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
    participant: Literal["first", "second", "both"] = "both"
    also_covers: tuple[str, ...] = ()
    comparison: Literal["witness", "focused"] = "witness"
    focused: str | None = None
    requires: tuple[str, ...] = ()
    blocked_by: str | None = None
    note: str = ""
    witness: str | None = None


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
    ("B14.1", "leadership-test-value", "duel", "quick", "G05/G06", ()),
    ("B14.2", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.3", "leadership-auto-pass", "duel", "complete", "G05/G06", ()),
    ("B14.4", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.5", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.6", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.7", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.8", "psychology-dice", "duel", "complete", "G05/G06", ()),
    ("B14.9", "reroll-used", "duel", "complete", "G05/G06", ()),
    ("B14.10", "leadership-test-value", "duel", "complete", "G05/G06", ()),
    ("B14.11", "leadership-auto-pass", "duel", "complete", "G05/G06", ()),
    ("B14.12", "leadership-test-value", "duel", "complete", "G05/G06", ()),
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
    "B14.1": "modular `leadership.py` and vectorized `_leadership.py` read "
              "nearby/distance; the tested value is not published per row yet",
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
    participant: str = "both",
    also_covers: tuple[str, ...] = (),
    comparison: str = "witness",
    focused: str | None = None,
    witness: str | None = None,
    blocked_by: str | None = None,
    rows: int = 64,
    maximum_rounds: int = 50,
    note: str = "",
) -> BatteryCase:
    variant_witness = VARIANTS[variant].witness
    if observables is None:
        declared = list(OUTCOMES)
        criterion = witness or (variant_witness.name if variant_witness else None)
        if criterion is not None and criterion not in declared:
            declared.append(criterion)
        observables = tuple(declared)
    return BatteryCase(
        id=id, level=level, variant=variant, origin=origin,  # type: ignore[arg-type]
        first=first, second=second, rows=rows, maximum_rounds=maximum_rounds,
        context=context, decisions=dict(decisions or {}),
        decision_scope=decision_scope,  # type: ignore[arg-type]
        observables=observables, expect=expect,  # type: ignore[arg-type]
        positive_control=positive_control, witness_value=witness_value,
        participant=participant,  # type: ignore[arg-type]
        also_covers=also_covers, comparison=comparison,  # type: ignore[arg-type]
        focused=focused, witness=witness, requires=requires, blocked_by=blocked_by,
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
        participant="second",
        note="Resultado directo de la tabla de lesión; condición del defensor.",
    ),
    _case(
        "q04-parry-attempt", "quick", "B06.1",
        "e2e:core/combat-parry::sword-parries-one-hit",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword"),
        context=_charging(), maximum_rounds=2,
        participant="second",
        note="El defensor empuña la espada; `parried` aún no publicado.",
    ),
    _case(
        "q04-parry-absent", "complete", "B06.1",
        "new:control sin arma de parada",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        participant="second",
        expect="absent", positive_control="q04-parry-attempt",
        note="El defensor con maza no puede parar; el control con espada sí.",
    ),
    _case(
        "q04-natural-armour-six", "quick", "B04.2",
        "e2e:rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/"
        "trait.natural-armour-save::the-shaggy-hide-saves-on-six",
        _fighter(weapon="weapon.sword", strength=4),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastmen-chieftain",
                 specials=("band--beastmen-special-skills-shaggy-hide",)),
        context=_charging(), maximum_rounds=1,
        requires=("band--beastmen-special-skills-shaggy-hide",),
        note="Piel natural 6+ materializada con la regla impresa de la banda "
             "(seleccionable), no con armadura ligera.",
    ),
    _case(
        "q05-flammable-fire", "quick", "B03.5",
        "e2e:rule/mordheim/restless-dead/scarecrows--flammable/trait.flammable::"
        "a-fire-attack-wounds-the-printed-scarcrow-twice-over",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(collection="mordheim", band="restless-dead", profile="scarecrows"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.brazier-iron", "scarecrows"),
        participant="second",
        note="Ataque de fuego (braser) contra inflamable; el testigo es on-fire.",
    ),
    _case(
        "c03-flammable-absent", "complete", "B03.5",
        "new:control con el mismo fuego y sin flammable",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.brazier-iron",),
        participant="second",
        expect="absent", positive_control="q05-flammable-fire",
        note="Mismo braser contra un defensor no inflamable; no debe prender.",
    ),
    _case(
        "q06-intrinsic-save", "quick", "B04.1",
        "e2e:rule/mordheim/ghost-pirates-sar/gibbets--iron-cage/"
        "profile.equipment-restrictions::the-intrinsic-cage-save-holds-on-five",
        _fighter(weapon="weapon.sword"),
        _fighter(collection="mordheim", band="ghost-pirates-sar", profile="gibbets"),
        context=_charging(), maximum_rounds=1,
        requires=("gibbets",),
        note="Perfil con la regla impresa: la salvación intrínseca 5+ de la jaula, "
             "sin armadura comprada.",
    ),
    _case(
        "q08-death-blow-optional", "quick", "B10.3",
        "e2e:mechanic/mechanic.death-blow::the-bearer-declines-and-attacks-normally",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.death-blow",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.death-blow",),
        decisions={"round.0.first.death-blow": False,
                   "round.1.first.death-blow": False},
        note="La elección se declara en cada ronda: el motor la consulta de nuevo "
             "al inicio de cada fase de combate.",
    ),
    _case(
        "q09-fear-charged", "quick", "B11.1",
        "e2e:rule/mordheim/beastmen-raiders/minotaur--fear/mechanic.causes-fear::"
        "a-charged-opponent-that-fails-its-fear-test-hits-only-with-sixes",
        _fighter(weapon="weapon.mace", leadership=7),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("minotaur",),
        participant="first",
        note="Miedo en la carga; el minotauro recibe la regla impresa desde su "
             "perfil, sin id de efecto en `specials`.",
    ),
    _case(
        "q10-leader-six", "quick", "B14.1",
        "e2e:rule/mordheim/amazons-lustria/serpent-priestess--leader/mechanic.leader-six::"
        "a-supplied-leader-at-six-inches-lends-his-leadership",
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(6), maximum_rounds=2,
        requires=("serpent-priestess", "amazon-warriors", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=8,
        participant="first",
        note="Misma banda: la amazona a 6\" del líder presta su valor 8. El "
             "proveedor es el perfil canónico `serpent-priestess`, cuya propia "
             "regla `serpent-priestess--leader` (grant: profile) compila "
             "`mechanic.leader-six`; la regla no se declara como skill.",
    ),
    _case(
        "q11-black-hunger", "quick", "B15.1",
        "e2e:mechanic/mechanic.black-hunger::the-backlash-ignores-armour",
        _fighter(weapon="weapon.mace", attacks=2, skills=("mechanic.black-hunger",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.black-hunger",),
        witness_value=-1,
        participant="first",
        note="El retroceso lo resuelve el motor al inicio del turno del portador "
             "(`aftermath._black_hunger`: D3 impactos automáticos de Fuerza 3 que "
             "ignoran armadura, sin decisión). El caso compara resultados "
             "terminales sobre las mismas filas; no declara testigo de evento.",
    ),
    _case(
        "c15-hunger-absent", "complete", "B15.1",
        "new:control sin hambre negra",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        witness_value=-1,
        participant="first",
        expect="absent", positive_control="q11-black-hunger",
        note="El negativo necesita el mismo evento de reacción; sin G06 solo hay herida terminal.",
    ),
    _case(
        "q00-honorable", "quick", "B10.4",
        "e2e:rule/mordheim/adventurers-kaz/imperial-noble--honorable/mechanic.honorable::"
        "no-attack-is-made-against-a-knocked-down-opponent",
        _fighter(weapon="weapon.sword", wounds=3),
        _fighter(weapon="weapon.mace", strength=4, attacks=2,
                 skills=("mechanic.honorable",)),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.honorable",),
        participant="second",
        note="La maza de concusión convierte la lesión en aturdido (2-4) o derribado "
             "en la ronda 0; la ronda 1 es el turno del portador y el oponente no ha "
             "tenido aún su recuperación, así que la guarda de `pools.resolve_attacks` "
             "recibe el pool con el rival derribado/aturdido y no ataca. Sin la regla "
             "ese mismo estado se resolvía como fuera de combate automático. No inyecta "
             "estado inicial: la condición se produce dentro del duelo y el orden de "
             "turnos es el del contexto declarado.",
    ),
    # -- complete: repaired and reused cases ---------------------------------
    _case(
        "c04-parry-reroll", "complete", "B06.2",
        "e2e:core/combat-parry::sword-and-buckler-reroll-a-failed-parry",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler"),
        context=_charging(), maximum_rounds=3,
        requires=("defence.buckler",),
        witness="reroll-used",
        participant="second",
        note="adaptado:sword-and-buckler-reroll-a-failed-parry → el guion de "
             "tiradas se sustituye por el criterio de evento `reroll-used` sobre 64 "
             "filas. Criterio: al menos una repetición de parada fallida por la "
             "rodela. Las tentativas consumidas por fase se miden en "
             "`c06-two-parries`/`c06-two-swords-capacity`, no con este testigo de "
             "evento.",
    ),
    _case(
        "c06-two-swords-one-attempt", "complete", "B06.2",
        "e2e:core/combat-parry::two-swords-give-one-attempt-per-phase",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", off_hand="weapon.sword"),
        context=_charging(), maximum_rounds=3,
        requires=("weapon.sword",),
        witness="reroll-used",
        participant="second",
        expect="absent", positive_control="c04-parry-reroll",
        note="adaptado:two-swords-give-one-attempt-per-phase → mismo criterio de "
             "evento sobre 64 filas. Criterio: ninguna repetición de parada sin "
             "rodela. La capacidad de una sola tentativa por fase se mide en "
             "`c06-two-swords-capacity`, no con este testigo de evento.",
    ),
    _case(
        "c06-two-parries", "complete", "B06.2",
        "e2e:mechanic/skill.unbeatable-warrior::"
        "two-parrying-weapons-give-two-parry-attempts",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", off_hand="weapon.sword",
                 skills=("skill.unbeatable-warrior",)),
        context=_charging("first"), maximum_rounds=1,
        requires=("weapon.sword", "skill.unbeatable-warrior"),
        witness="parry-attempts",
        witness_value=2,
        participant="second",
        note="adaptado:two-parries-with-two-weapons → el guion de tiradas se "
             "sustituye por `parry-attempts` sobre 64 filas. Criterio: el defensor "
             "con capacidad impresa de dos paradas consume 2 tentativas en una "
             "misma fase (el atacante lleva dos ataques). Criterio por fase, no "
             "suma: si alguna fase consume dos, el máximo vale 2. Falta que G06 "
             "publique, por fila y por lado, el máximo de tentativas consumidas en "
             "una fase (capacidad − parry_remaining al cierre de cada fase, máximo "
             "entre fases); una repetición de la misma tirada no incrementa el "
             "contador.",
    ),
    _case(
        "c06-two-swords-capacity", "complete", "B06.2",
        "e2e:mechanic/skill.unbeatable-warrior::"
        "without-the-skill-only-the-first-attack-is-parried",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", off_hand="weapon.sword"),
        context=_charging("first"), maximum_rounds=1,
        requires=("weapon.sword",),
        witness="parry-attempts",
        witness_value=2,
        participant="second",
        expect="absent", positive_control="c06-two-parries",
        note="adaptado:without-the-skill-only-the-first-attack-is-parried "
             "(cláusula two-parries-with-two-weapons) → mismo recuento por fase "
             "sobre 64 filas. Criterio: con dos espadas y sin la regla de dos "
             "paradas, ninguna fase consume 2 tentativas y el segundo ataque no "
             "recibe parada. Es un caso propio porque cada caso tiene un único "
             "testigo efectivo: `c06-two-swords-one-attempt` "
             "mide el evento de repetición y este mide la capacidad. Misma "
             "publicación G06 que el positivo.",
    ),
    _case(
        "c06-reroll-capacity", "complete", "B06.2",
        "e2e:core/combat-parry::a-failed-parry-reroll-consumes-the-phase-attempt",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler", wounds=3),
        context=_charging("first"), maximum_rounds=1,
        requires=("weapon.sword", "defence.buckler"),
        witness="parry-attempts",
        witness_value=2,
        participant="second",
        expect="absent", positive_control="c06-two-parries",
        note="adaptado:a-failed-parry-reroll-consumes-the-phase-attempt → mismo "
             "recuento por fase sobre 64 filas. Criterio: la repetición de una "
             "parada fallida es la misma tentativa, así que ninguna fase llega a 2; "
             "si el motor contara la tirada repetida como tentativa nueva, el "
             "máximo valdría 2 y el control fallaría. Falta la misma publicación "
             "G06 que el positivo.",
    ),
    _case(
        "c04-stand-up-last", "complete", "B10.2",
        "e2e:core/combat-injury-states::recovery-belongs-to-the-fighters-own-turn",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(), maximum_rounds=4,
        note="La maza derriba dentro del duelo; el segundo se levanta al inicio de "
             "su propio turno, sin estado inicial inyectado.",
    ),
    _case(
        "c04-highest-injury", "quick", "B07.2",
        "e2e:core/combat-injury-states::highest-injury-result-applies",
        _fighter(weapon="weapon.mace", strength=4, attacks=2),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        witness_value="out",
        participant="second",
        note="Dos heridas en la misma fase; se conserva el peor resultado.",
    ),
    _case(
        "c04-hard-head", "complete", "B07.1",
        "e2e:rule/mordheim/adventurers-kaz/dwarf--hard-head/trait.concussion-immune::"
        "the-mace-no-longer-converts-a-two-into-a-stun",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", traits={"concussion_immune": True}),
        context=_charging(), maximum_rounds=2,
        requires=("concussion_immune",), witness_value="knocked-down",
        participant="second",
        note="La inmunidad impresa convierte el dos en derribado en lugar de "
             "aturdido; se suministra como rasgo tipado, sin estado inicial.",
    ),
    _case(
        "c04-hard-to-kill", "complete", "B07.1",
        "e2e:rule/mordheim/adventurers-kaz/dwarf--hard-to-kill/skill.hard-to-kill::"
        "a-five-only-stuns-the-adventurer-dwarf",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", skills=("skill.hard-to-kill",)),
        context=_charging(), maximum_rounds=2,
        requires=("skill.hard-to-kill",), witness_value="stunned",
        participant="second",
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
        participant="second",
        note="Reacción de cráneo grueso sobre el aturdimiento.",
    ),
    _case(
        "c04-hide-combines", "complete", "B04.2",
        "e2e:rule/mordheim/beastmen-raiders/band--beastmen-special-skills-shaggy-hide/"
        "trait.natural-armour-save::a-shield-takes-the-hide-to-five",
        _fighter(weapon="weapon.sword", strength=3),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="beastmen-chieftain",
                 specials=("band--beastmen-special-skills-shaggy-hide",),
                 off_hand="defence.shield"),
        context=_charging(), maximum_rounds=1,
        requires=("band--beastmen-special-skills-shaggy-hide", "defence.shield"),
        note="Piel natural combinada con escudo; variante de parámetro.",
    ),
    _case(
        "c00-amazon-isolationists", "complete", "B02.3",
        "e2e:rule/mordheim/amazons-lustria/band--special-rules/"
        "mechanic.amazon-isolationists::the-first-round-miss-against-lizardmen-is-taken-again",
        _fighter(weapon="weapon.sword", wounds=3,
                 skills=("mechanic.amazon-isolationists",)),
        _fighter(collection="mordheim", band="lizardmen", profile="saurus-braves"),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.amazon-isolationists", "saurus-braves"),
        note="Repetición de impacto en la primera ronda contra un enemigo lagarto: "
             "`contexts.py` reconoce la banda `band.lizardmen` del oponente y activa "
             "`amazon_enemy`.",
    ),
    _case(
        "c00-questing-vow", "complete", "B11.6",
        "e2e:rule/mordheim/bretonnian-chapel-guard/band--questing-vow/"
        "mechanic.questing-vow::the-failed-test-against-a-fear-causer-is-taken-again",
        _fighter(weapon="weapon.sword", skills=("mechanic.questing-vow",)),
        _fighter(weapon="weapon.mace", wounds=3, traits={"causes_fear": True}),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.questing-vow", "causes_fear"),
        decisions={"round.0.first.fear.charge.reroll": True},
        participant="first",
        note="El voto repite el test de miedo fallido contra el causante; la "
             "repetición es una decisión uniforme declarada.",
    ),
    _case(
        "c00-questing-vow-absent", "complete", "B11.6",
        "new:control sin la repetición del voto",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3, traits={"causes_fear": True}),
        context=_charging(), maximum_rounds=2,
        requires=("causes_fear",),
        participant="first",
        expect="absent", positive_control="c00-questing-vow",
        note="El mismo test de miedo fallido sin `questing-vow`: no se repite; `reroll-used` cero.",
    ),
    _case(
        "c05-poltergeist-immediate-out", "complete", "B07.1",
        "e2e:rule/mordheim/call-of-the-night-haint-mim/poltergeists--incorporeal/"
        "trait.injury-profile::the-first-wound-takes-the-poltergeist-out-without-an-injury-roll",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword",
                 traits={"injury_profile": 2}, wounds=2),
        context=_charging(), maximum_rounds=1,
        requires=("injury_profile",), witness_value="out",
        participant="second",
        note="Perfil de lesión inmediata: la primera herida resuelve sin tirada.",
    ),
    _case(
        "c05-ethereal-improved", "complete", "B05.1",
        "e2e:rule/mordheim/call-of-the-night-haint-mim/mourngul--haunter-of-the-dark/"
        "unimplemented.call-of-the-night-haint-mim.mourngul.haunter-of-the-dark::"
        "the-improved-ethereal-save-discards-a-hit-on-three",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.ethereal-hit-save-improved",), wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.ethereal-hit-save-improved",),
        note="Save etéreo mejorado (5+) materializado como regla del defensor.",
    ),
    _case(
        "c05-ethereal-save", "complete", "B05.1",
        "e2e:mechanic/mechanic.ethereal-hit-save::"
        "the-ethereal-save-holds-on-four-immediately-after-the-hit",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", skills=("mechanic.ethereal-hit-save",)),
        context=_charging("first"), maximum_rounds=1,
        requires=("mechanic.ethereal-hit-save",),
        participant="second",
        note="adaptado:the-ethereal-save-holds-on-four-immediately-after-the-hit → "
             "el dado etéreo declarado se sustituye por el criterio de evento "
             "`special-save-rolled` sobre 64 filas. Criterio: el save se tira al "
             "menos en una fila. Falta el contador de saves especiales por lado.",
    ),
    _case(
        "c05-ethereal-bypass", "complete", "B05.1",
        "e2e:mechanic/mechanic.ethereal-hit-save::"
        "a-magical-attack-bypasses-the-ethereal-save",
        _fighter(weapon="weapon.mace", traits={"magical_attacks": True}),
        _fighter(weapon="weapon.mace", skills=("mechanic.ethereal-hit-save",)),
        context=_charging("first"), maximum_rounds=1,
        requires=("mechanic.ethereal-hit-save",),
        participant="second",
        expect="absent", positive_control="c05-ethereal-save",
        note="adaptado:a-magical-attack-bypasses-the-ethereal-save → mismo criterio "
             "sobre 64 filas. Criterio: ningún save especial tirado contra un ataque "
             "mágico, que lo ignora sin tirarlo.",
    ),
    _case(
        "c05-bear-hug", "complete", "B08.5",
        "e2e:rule/mordheim/channel-rats-mim/domnu--bear-hug/"
        "unimplemented.channel-rats-mim.domnu.bear-hug::"
        "two-unarmed-hits-are-replaced-by-one-unsaveable-bear-hug-wound",
        _fighter(collection="mordheim", band="channel-rats-mim", profile="domnu",
                 weapon="weapon.fist"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=("domnu", "weapon.fist"),
        decisions={"round.0.first.bear-hug": True,
                   "round.1.first.bear-hug": True},
        note="Dos impactos desarmados del Domnu (Fuerza de voluntad impresa y "
             "`rule.bear-hug-unarmed`) se sustituyen por el agarre; la marca la "
             "compila el perfil.",
    ),
    _case(
        "c03-petru-potion", "complete", "B01.3",
        "e2e:rule/mordheim/channel-rats-mim/petru--potions/"
        "unimplemented.channel-rats-mim.petru.potions::"
        "the-strength-draught-raises-the-affected-heroes-strength-by-one",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        requires=(),
        blocked_by="state:preparation.strength-draught",
        note="El origen prueba el brebaje de Fuerza de Petru. La KB declara "
             "`petru--potions` fuera de alcance (`implemented: NO`: reparto "
             "aleatorio pre-batalla con persistencia de campaña), así que no hay "
             "preparación que compilar; la raíz de mandrágora es otra poción (+1 T) "
             "y no se declara como equivalente. El caso permanece INCOMPATIBLE con "
             "esta causa y no materializa un sustituto.",
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
        decisions={"round.0.first.death-blow": False,
                   "round.1.first.death-blow": False,
                   "round.2.first.death-blow": False},
        note="Uso opcional rechazado; el pool conserva los ataques normales.",
    ),
    _case(
        "c09-troll-fear", "complete", "B11.1",
        "e2e:rule/mordheim/black-orcs/troll--fear/mechanic.causes-fear::"
        "a-charged-opponent-that-passes-its-fear-test-fights-normally",
        _fighter(weapon="weapon.mace", leadership=7),
        _fighter(collection="mordheim", band="black-orcs", profile="troll"),
        context=_charging("second"), maximum_rounds=1,
        requires=("troll",),
        note="Cara opuesta del miedo: el troll recibe la regla impresa desde su "
             "perfil; test superado.",
    ),
    _case(
        "c09-beastlash-fear", "complete", "B11.1",
        "e2e:mechanic/weapon.beastlash::"
        "beastlash-fear-test-is-required-of-an-animal-that-is-charged",
        _fighter(weapon="weapon.beastlash"),
        _fighter(collection="mordheim", band="house-guard-sc", profile="warhounds",
                 traits={"house_guard_house": "fierezza"}),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.beastlash", "warhounds", "house_guard_house"),
        note="El látigo de bestias solo causa miedo a un animal (`species.animal`): el "
             "oponente es la jauría canónica, que además no causa miedo, así que la "
             "prueba de miedo cargada sí se toma. La variante de parada es B06.3.",
    ),
    _case(
        "c10-leader-absence", "complete", "B14.1",
        "new:control sin líder — el mismo duelista conserva su Ld",
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(8), maximum_rounds=2,
        requires=("serpent-priestess", "amazon-warriors", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=8,
        expect="absent", positive_control="q10-leader-six",
        participant="first",
        note="Mismo proveedor a 8\": fuera del radio de 6\", la prueba usa el Ld propio 7 y no el 8 prestado.",
    ),
    _case(
        "c10-leader-swapped", "complete", "B14.1",
        "new:dirigido — dirección del participante intercambiada",
        _fighter(weapon="weapon.sword", wounds=3),
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors", traits={"stupidity": True}),
        context=ContextSpec(
            nearby=(ProviderSpec("leader", "second",
                                 _fighter(collection="mordheim", band="amazons-lustria",
                                          profile="serpent-priestess")),),
            distances=(("second", "leader", 6),),
            charging=("second",), active_participant="second",
        ), maximum_rounds=2,
        requires=("serpent-priestess", "amazon-warriors", "stupidity"),
        decisions={"round.0.second.stupidity.leader.leader": True},
        witness_value=8,
        participant="second",
        note="La misma construcción con el líder como segundo participante.",
    ),
    _case(
        "c11-curse-of-revenant", "complete", "B15.2",
        "e2e:mechanic/mechanic.curse-of-the-revenant::"
        "a-five-restores-one-lost-wound-at-the-own-turn-start",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.great-thirster", "mechanic.curse-of-the-revenant")),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=4,
        requires=("mechanic.great-thirster", "mechanic.curse-of-the-revenant"),
        witness_value=1,
        participant="first",
        note="Recuperación 5+ al inicio del turno propio; una herida, con tope. La "
             "propia regla exige Gran Asediador (Great Thirster): el portador declara "
             "ambas habilidades, como el vampiro canónico que ya la tenía.",
    ),
    _case(
        "c11-great-thirster", "complete", "B11.7",
        "e2e:mechanic/mechanic.great-thirster::"
        "taking-the-opponent-out-of-action-grants-frenzy",
        _fighter(weapon="weapon.mace", strength=4, skills=("mechanic.great-thirster",)),
        _fighter(weapon="weapon.sword", wounds=1),
        context=_charging(), maximum_rounds=3,
        requires=("mechanic.great-thirster",),
        note="Frenesí tras sacar de acción al oponente; se pierde al quedar derribado.",
    ),
    _case(
        "c11-acid-blood", "complete", "B15.4",
        "e2e:rule/mordheim/cult-of-the-possessed/band--mutations-blackblood/"
        "trait.acid-blood::an-unsaved-wound-answers-with-the-printed-strength-three-hit",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3, traits={"acid_blood": True}),
        context=_charging("first"), maximum_rounds=1,
        requires=("acid_blood",),
        witness_value=2,
        participant="second",
        note="adaptado:an-unsaved-wound-answers-with-the-printed-strength-three-hit → "
             "el dado de herida del contraataque se sustituye por el recuento de "
             "ataques por fila sobre 64 filas. Criterio: el portador ejecuta 2 "
             "ataques en una fila (el propio y el automático de S3 al perder una "
             "herida). Falta el valor de `attack-count` por lado y por fase.",
    ),
    _case(
        "c11-acid-blood-absent", "complete", "B15.4",
        "e2e:rule/mordheim/cult-of-the-possessed/band--mutations-blackblood/"
        "trait.acid-blood::an-unsaved-wound-answers-with-the-printed-strength-three-hit",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging("first"), maximum_rounds=1,
        requires=(),
        witness_value=2,
        participant="second",
        expect="absent", positive_control="c11-acid-blood",
        note="control del mismo escenario sin `trait.acid-blood`: mismo recuento "
             "sobre 64 filas. Criterio: ninguna fila llega a 2 ataques; sin la "
             "reacción no hay contraataque automático.",
    ),
    _case(
        "c11-spines", "complete", "B15.4",
        "e2e:rule/mordheim/cult-of-the-possessed/band--mutations-spines/trait.spines::"
        "the-automatic-spines-hit-lands-on-the-contacting-opponent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3, traits={"spines": True}),
        context=_charging(), maximum_rounds=1,
        requires=("spines",),
        witness_value=2,
        participant="second",
        note="adaptado:the-automatic-spines-hit-lands-on-the-contacting-opponent → "
             "el dado de herida declarado se sustituye por el recuento de ataques "
             "por fila sobre 64 filas. Criterio: el portador ejecuta 2 ataques en "
             "una fila (el propio y el automático de S1 al inicio de la fase). "
             "Falta el valor de `attack-count` por lado y por fase.",
    ),
    _case(
        "c11-spines-absent", "complete", "B15.4",
        "e2e:rule/mordheim/cult-of-the-possessed/band--mutations-spines/trait.spines::"
        "the-automatic-spines-hit-lands-on-the-contacting-opponent",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=1,
        requires=(),
        witness_value=2,
        participant="second",
        expect="absent", positive_control="c11-spines",
        note="control del mismo escenario sin `trait.spines`: mismo recuento sobre "
             "64 filas. Criterio: ninguna fila llega a 2 ataques; sin la mutación "
             "no hay impacto automático al inicio de la fase.",
    ),
    _case(
        "d09-fear-charge-parry", "deep", "B11.1",
        "new:interacción miedo → carga → parada",
        _fighter(weapon="weapon.sword", leadership=7),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=2,
        requires=("minotaur",),
        note="El miedo altera el pool antes de la parada; composición declarada.",
    ),
    _case(
        "d10-leader-retest", "deep", "B14.1",
        "new:interacción liderazgo → retest de psicología",
        _fighter(collection="mordheim", band="amazons-lustria",
                 profile="amazon-warriors"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_leader_context(6), maximum_rounds=2,
        requires=("serpent-priestess", "amazon-warriors", "minotaur"),
        decisions={"round.0.first.fear.charge.leader.leader": True},
        witness_value=8,
        participant="first",
        note="Dos familias comparten el test de liderazgo; el orden cambia el "
             "resultado. La carga del primer participante pide el préstamo en el "
             "test de miedo y se declara la decisión.",
    ),
    _case(
        "d04-long-horizon", "deep", "B06.2",
        "new:horizonte largo de desgaste",
        _fighter(weapon="weapon.sword", off_hand="defence.buckler", wounds=3),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging(), maximum_rounds=12,
        requires=("defence.buckler",),
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
        note="Recurso de un solo uso y recuperación; el consumidor no pide decisión.",
    ),
    _case(
        "d05-spines-injury", "deep", "B15.4",
        "new:interacción espinas → varias heridas en la misma fase",
        _fighter(weapon="weapon.mace", attacks=2),
        _fighter(weapon="weapon.sword", wounds=3, traits={"spines": True}),
        context=_charging(), maximum_rounds=6,
        requires=("spines",),
        note="Espinas y heridas múltiples; no se reutiliza el criterio de B15.2.",
    ),
    # -- one material case for every remaining duel variant ------------------
    _case(
        "v01-profile", "complete", "B01.1",
        "new:perfil y características iniciales",
        _fighter(collection="mordheim", band="adventurers-kaz", profile="imperial-noble"),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=1,
        note="Campos iniciales compilados; sin testigo por fila.",
    ),
    _case(
        "v01-restriction", "complete", "B01.5",
        "new:restricción de carga suministrada",
        _fighter(weapon="weapon.sword", skills=("mechanic.shallya-strictures",)),
        _fighter(weapon="weapon.mace"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.shallya-strictures",),
        blocked_by="state:mechanic.shallya-strictures",
        note="Limitación real de entrada: la cláusula se ejerce cuando el portador "
             "pretende cargar a un objetivo no exento, y `build_duel_state` rechaza "
             "esa configuración con ValueError antes de muestrear. Declarar el duelo "
             "sin carga no ejerce la restricción y sería otro escenario; no se "
             "materializa un sustituto.",
    ),
    _case(
        "v01-random", "complete", "B01.6",
        "new:característica aleatoria/avance",
        _fighter(collection="mordheim", band="marauders-of-chaos",
                 profile="condemned", weapon="weapon.fist"),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("condemned",),
        note="El Perdido imprime WS/S/T en D6 y A en D3; ambos motores tiran esas "
             "cuatro características al inicio de cada turno, sin inyección.",
    ),
    _case(
        "v01-force-of-will", "complete", "B01.2",
        "e2e:mechanic/mechanic.force-of-will::the-toughness-test-stands-him-back-up",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=1,
                 skills=("mechanic.force-of-will",)),
        context=_charging(), maximum_rounds=1,
        requires=("mechanic.force-of-will",),
        participant="second",
        note="El recurso pertenece al segundo; el contador no se publica por fila.",
    ),
    _case(
        "v01-force-of-will-absent", "complete", "B01.2",
        "new:control con el recurso disponible y sin el evento que lo consume",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=5,
                 skills=("mechanic.force-of-will",)),
        context=_charging(), maximum_rounds=1,
        requires=("mechanic.force-of-will",),
        participant="second",
        expect="absent", positive_control="v01-force-of-will",
        note="Mismo portador y mismo recurso; con cinco heridas un solo ataque no "
             "lo reduce a cero, así que no hay gasto y el contador debe quedar en cero.",
    ),
    _case(
        "v02-hatred", "complete", "B02.2",
        "e2e:mechanic/mechanic.hatred-orcs-goblins::"
        "a-first-round-miss-is-rerolled-against-a-qualifying-orc",
        _fighter(weapon="weapon.mace", skills=("mechanic.hatred-orcs-goblins",)),
        _fighter(weapon="weapon.mace", traits={"species": "orc"}),
        context=_charging("first"), maximum_rounds=1,
        requires=("mechanic.hatred-orcs-goblins",),
        witness="reroll-used",
        participant="first",
        note="adaptado:a-first-round-miss-is-rerolled-against-a-qualifying-orc → "
             "el guion de tiradas del E2E se sustituye por el criterio de evento "
             "`reroll-used` sobre 64 filas. Criterio: al menos una repetición de "
             "impacto en la primera ronda contra la identidad odiada. Falta "
             "publicar el contador de repeticiones por lado; `hit-modified` no lo "
             "sustituye.",
    ),
    _case(
        "v02-hatred-absent", "complete", "B02.2",
        "e2e:mechanic/mechanic.hatred-orcs-goblins::"
        "the-same-miss-stands-without-the-qualifying-orc",
        _fighter(weapon="weapon.mace", skills=("mechanic.hatred-orcs-goblins",)),
        _fighter(weapon="weapon.mace"),
        context=_charging("first"), maximum_rounds=1,
        requires=("mechanic.hatred-orcs-goblins",),
        witness="reroll-used",
        participant="first",
        expect="absent", positive_control="v02-hatred",
        note="adaptado:the-same-miss-stands-without-the-qualifying-orc → mismo "
             "criterio de evento sobre 64 filas. Criterio: ninguna repetición de "
             "impacto sin la identidad odiada; el fallo se queda como está.",
    ),
    _case(
        "v02-hit-reroll", "complete", "B02.3",
        "new:reroll de impacto por skill",
        _fighter(weapon="weapon.sword", skills=("skill.expert-swordsman",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("skill.expert-swordsman",),
        participant="first",
        note="Un impacto fallido se repite una vez.",
    ),
    _case(
        "v02-hit-reroll-absent", "complete", "B02.3",
        "new:control sin la regla de repetición de impacto",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        participant="first",
        expect="absent", positive_control="v02-hit-reroll",
        note="Mismo ataque sin `expert-swordsman`: no se repite ningún impacto, "
             "así que `reroll-used` queda en cero aunque haya impactos.",
    ),
    _case(
        "v02-general-hit", "complete", "B02.4",
        "new:modificador general de impacto",
        _fighter(weapon="weapon.duelling-pistol"),
        _fighter(weapon="weapon.sword"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.duelling-pistol",),
        participant="first",
        note="+1 a impactar en la primera ronda; la primera ronda es el disparador.",
    ),
    _case(
        "v02-general-absent", "complete", "B02.4",
        "new:control sin el modificador de impacto del arma",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.sword"),
        context=_charging(), maximum_rounds=2,
        participant="first",
        expect="absent", positive_control="v02-general-hit",
        note="Mismo asalto con espada: ningún impacto lleva el +1 del arma, "
             "así que `hit-modified` queda en cero.",
    ),
    _case(
        "v03-poison", "complete", "B03.2",
        "new:veneno sobre la tirada de herida",
        _fighter(weapon="weapon.sword", poison="poison.black-lotus"),
        _fighter(weapon="weapon.mace", wounds=4),
        context=_charging(), maximum_rounds=2,
        requires=("poison.black-lotus",),
        decisions={"round.0.first.attack.0.lotus-critical": False,
                   "round.1.first.attack.0.lotus-critical": False,
                   # ``_attacks._resolve_weapon`` reaches the main pool without
                   # propagating its round key, so the candidate asks under the
                   # default key.  Declaring it keeps the intended refusal; the
                   # missing key propagation is an engine defect (TODO).
                   "test.lotus-critical": False},
        participant="first",
        note="El veneno modifica la tirada de herida; el crítico adicional del "
             "Loto Negro se rechaza en cada ataque declarado. El motor vectorial "
             "pregunta además bajo su clave por defecto `test.*`, que se declara "
             "para no dejar sin script al mismo rechazo.",
    ),
    _case(
        "v03-poison-immune", "complete", "B03.2",
        "new:control con inmunidad al veneno",
        _fighter(weapon="weapon.sword", poison="poison.black-lotus"),
        _fighter(weapon="weapon.mace", wounds=4, traits={"poison_immune": True}),
        context=_charging(), maximum_rounds=2,
        requires=("poison.black-lotus", "poison_immune"),
        participant="first",
        expect="absent", positive_control="v03-poison",
        note="Mismo ataque envenenado contra un defensor inmune: no hay modificación de herida.",
    ),
    _case(
        "v03-strength", "complete", "B03.3",
        "e2e:mechanic/skill.mighty-biceps::"
        "the-heavy-weapon-bonus-is-retained-in-the-second-round",
        _fighter(weapon="weapon.flail", strength=2, skills=("skill.mighty-biceps",)),
        _fighter(weapon="weapon.mace"),
        context=_charging("second"), maximum_rounds=2,
        requires=("weapon.flail", "skill.mighty-biceps"),
        witness_value=2,
        participant="first",
        note="adaptado:the-heavy-weapon-bonus-is-retained-in-the-second-round → "
             "el dado de herida declarado se sustituye por el recuento de "
             "modificaciones de Fuerza sobre 64 filas. Criterio: 2 modificaciones "
             "en una fila (bonificación del arma en la ronda 0 y retenida en la 1). "
             "Falta el contador acumulado por lado.",
    ),
    _case(
        "v03-strength-absent", "complete", "B03.3",
        "e2e:mechanic/skill.mighty-biceps::without-the-skill-the-bonus-is-not-retained",
        _fighter(weapon="weapon.flail", strength=2),
        _fighter(weapon="weapon.mace"),
        context=_charging("second"), maximum_rounds=2,
        requires=("weapon.flail",),
        witness_value=2,
        participant="first",
        expect="absent", positive_control="v03-strength",
        note="adaptado:without-the-skill-the-bonus-is-not-retained → mismo recuento "
             "sobre 64 filas. Criterio: ninguna fila llega a 2 modificaciones; "
             "solo la ronda 0 conserva la bonificación del arma.",
    ),
    _case(
        "v03-wound-reroll", "complete", "B03.4",
        "new:reroll/daño de herida",
        _fighter(weapon="weapon.sword", skills=("skill.sure-strike",)),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("skill.sure-strike",),
        participant="first",
        note="Repetición de herida fallida; no se infiere de heridas terminales.",
    ),
    _case(
        "v03-wound-reroll-absent", "complete", "B03.4",
        "new:control sin la repetición de herida",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        participant="first",
        expect="absent", positive_control="v03-wound-reroll",
        note="Misma tirada sin `sure-strike`: ninguna herida se repite, "
             "así que `wound-modified` queda en cero.",
    ),
    _case(
        "v04-buckler-armour", "complete", "B04.3",
        "new:el buckler no mejora la armadura",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 off_hand="defence.buckler"),
        context=_charging(), maximum_rounds=2,
        requires=("defence.buckler", "armour.light-armour"),
        note="Save de armadura sin bonificación; la parada se declara en B06.2.",
    ),
    _case(
        "v05-regeneration", "complete", "B05.2",
        "new:save de regeneración por herida",
        _fighter(weapon="weapon.sword"),
        _fighter(weapon="weapon.mace", skills=("skill.regeneration",)),
        context=_charging(), maximum_rounds=2,
        requires=("skill.regeneration",),
        participant="second",
        note="Save 4+ por herida no salvada; la recuperación es B15.2. El bloqueo "
             "por fuego tiene su propio control.",
    ),
    _case(
        "v05-regeneration-blocked", "complete", "B05.2",
        "new:control de regeneración bloqueada por fuego",
        _fighter(weapon="weapon.brazier-iron"),
        _fighter(weapon="weapon.mace", skills=("skill.regeneration",)),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.brazier-iron", "skill.regeneration"),
        participant="second",
        expect="absent", positive_control="v05-regeneration",
        note="Misma construcción que el positivo; el arma de fuego activa "
             "`regeneration_blocked_by_fire` y no se tira el save 4+.",
    ),
    _case(
        "v06-parry-denial", "complete", "B06.3",
        "new:ataque que niega la parada",
        _fighter(weapon="weapon.war-maul"),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.war-maul", "defence.buckler"),
        note="La negación no tiene contador negativo publicado; no se usa `parried`.",
    ),
    _case(
        "v07-weapon-injury", "complete", "B07.3",
        "new:modificador de lesión por arma",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_charging(), maximum_rounds=2,
        witness_value="stunned",
        participant="second",
        note="Maza/concusión sobre la tirada de lesión.",
    ),
    _case(
        "v08-base-pool", "complete", "B08.1",
        "new:recuento base con mano torpe y pistola",
        _fighter(weapon="weapon.pistol", off_hand="weapon.sword"),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.pistol", "weapon.sword"),
        note="Pistola en la mano principal y espada en la torpe: el reparto de "
             "ataques por mano lo resuelve el motor antes del pool. El caso compara "
             "resultados terminales; no exige un recuento de ataques.",
    ),
    _case(
        "v08-extra-attack", "complete", "B08.2",
        "new:frenesí/ataque extra",
        _fighter(weapon="weapon.sword", traits={"frenzy": True}),
        _fighter(weapon="weapon.mace"),
        context=_charging(), maximum_rounds=2,
        requires=("frenzy",),
        note="+1 ataque solo con la regla; no se acredita por la etiqueta.",
    ),
    _case(
        "v08-unarmed", "complete", "B08.4",
        "e2e:mechanic/skill.unarmed-fighting::"
        "the-unarmed-bearer-is-not-clamped-and-gains-one-attack",
        _fighter(weapon="weapon.fist", skills=("skill.unarmed-fighting",)),
        _fighter(weapon="weapon.mace"),
        context=_battle(), maximum_rounds=1,
        requires=("weapon.fist", "skill.unarmed-fighting"),
        witness_value=2,
        participant="first",
        note="adaptado:the-unarmed-bearer-is-not-clamped-and-gains-one-attack → "
             "el tope de ataques declarados se sustituye por el recuento de ataques "
             "por fila sobre 64 filas. Criterio: al menos una fila alcanza 2 ataques "
             "(el clamp no se aplica y añade el ataque impreso). Falta el valor de "
             "`attack-count` por lado.",
    ),
    _case(
        "v08-ordinary-fist", "complete", "B08.4",
        "e2e:mechanic/skill.unarmed-fighting::"
        "the-ordinary-fist-is-clamped-to-one-attack",
        _fighter(weapon="weapon.fist"),
        _fighter(weapon="weapon.mace"),
        context=_battle(), maximum_rounds=1,
        requires=("weapon.fist",),
        witness_value=2,
        participant="first",
        expect="absent", positive_control="v08-unarmed",
        note="adaptado:the-ordinary-fist-is-clamped-to-one-attack → mismo recuento "
             "sobre 64 filas. Criterio: ninguna fila alcanza 2 ataques; el puño "
             "ordinario queda clavado a 1, valor que el E2E afirma y que este par "
             "no vuelve a declarar como expectativa propia.",
    ),
    _case(
        "v09-transform", "complete", "B09.2",
        "e2e:rule/mordheim/masters-of-horror-sylv/the-bitten--transform/"
        "unimplemented.masters-of-horror-sylv.the-bitten.transform::"
        "transforming-casts-off-the-worn-armour",
        _fighter(collection="mordheim", band="masters-of-horror-sylv",
                 profile="the-bitten", weapon="weapon.sword",
                 off_hand="defence.shield"),
        _fighter(weapon="weapon.mace"),
        context=_battle(), maximum_rounds=3,
        requires=("weapon.sword", "defence.shield"),
        witness_value="starting-loadout",
        participant="first",
        note="El escudo es el objeto perdido; la forma la concede el perfil, no una regla añadida.",
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
        note="`condition.netted` es una condición suministrada, no un estado "
             "inyectado: ambos motores inicializan al portador como derribado "
             "(`modular/state.py` y `vectorized/_state.py`) y lo liberan en su "
             "propia recuperación, donde pierde la acción y golpea último.",
    ),
    _case(
        "v09-netted-absent", "complete", "B09.3",
        "new:control sin la condición de red",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.dagger"),
        context=_charging(), maximum_rounds=2,
        expect="absent", positive_control="v09-netted",
        note="El mismo combatiente sin `condition.netted`: la bandera `netted` "
             "debe quedar falsa en todas las filas.",
    ),
    _case(
        "v10-priority", "complete", "B10.1",
        "new:prioridad y orden de actuación",
        _fighter(weapon="weapon.pike", initiative=2),
        _fighter(weapon="weapon.sword", initiative=5),
        context=_charging(), maximum_rounds=1,
        requires=("weapon.pike",),
        witness_value=0,
        note="Categoría 0/1: el pike con carga actúa primero; no se evalúa con >0.",
    ),
    _case(
        "v10-round-state", "complete", "B10.4",
        "new:estado y modificadores por ronda",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=6,
        note="Cierre de ronda; sin testigo por fila, solo horizonte declarado.",
    ),
    _case(
        "v11-immunity", "complete", "B11.2",
        "new:inmunidad plena a miedo",
        _fighter(weapon="weapon.mace", skills=("mechanic.fear-immunity",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.fear-immunity", "minotaur"),
        participant="first",
        note="La prueba de miedo no se toma; las demás pruebas siguen.",
    ),
    _case(
        "v11-immunity-absent", "complete", "B11.2",
        "new:control sin inmunidad al miedo",
        _fighter(weapon="weapon.mace"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("minotaur",),
        participant="first",
        expect="absent", positive_control="v11-immunity",
        note="Sin inmunidad la prueba de miedo se toma; el control la omite.",
    ),
    _case(
        "v11-psych-immunity", "complete", "B11.3",
        "new:inmunidad completa a psicología",
        _fighter(weapon="weapon.mace", skills=("mechanic.psychology-immunity",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.psychology-immunity", "minotaur"),
        participant="first",
        note="No se toma ninguna prueba de psicología, no solo la de miedo.",
    ),
    _case(
        "v11-psych-absent", "complete", "B11.3",
        "new:control sin inmunidad completa a psicología",
        _fighter(weapon="weapon.mace"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("minotaur",),
        participant="first",
        expect="absent", positive_control="v11-psych-immunity",
        note="Sin la inmunidad la prueba de miedo se toma; el positivo la omite.",
    ),
    _case(
        "v11-conditional-immunity", "complete", "B11.4",
        "new:inmunidad condicionada al cargante no-muerto",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.fear-immunity-undead-chargers",)),
        _fighter(collection="mordheim", band="blood-dragons-mou",
                 profile="skeleton-warriors"),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.fear-immunity-undead-chargers", "skeleton-warriors"),
        participant="first",
        note="La condición (cargante no-muerto) forma parte del contrato.",
    ),
    _case(
        "v11-conditional-absent", "complete", "B11.4",
        "new:control fuera de la condición (cargante vivo)",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.fear-immunity-undead-chargers",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.fear-immunity-undead-chargers", "minotaur"),
        expect="absent", positive_control="v11-conditional-immunity",
        participant="first",
        note="Fuera de la condición la prueba se toma; el control positivo la omite.",
    ),
    _case(
        "v11-cold-blood", "complete", "B11.5",
        "new:sangre fría psicológica (3D6, conservar 2)",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.cold-blooded-psychology",)),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("mechanic.cold-blooded-psychology", "minotaur"),
        witness_value=3,
        participant="first",
        note="La prueba se hace: 3 dados y se descarta el mayor; no es inmunidad.",
    ),
    _case(
        "v11-cold-blood-absent", "complete", "B11.5",
        "new:control sin la sangre fría psicológica",
        _fighter(weapon="weapon.mace"),
        _fighter(collection="mordheim", band="beastmen-raiders", profile="minotaur"),
        context=_charging("second"), maximum_rounds=1,
        requires=("minotaur",),
        witness_value=3,
        participant="first",
        expect="absent", positive_control="v11-cold-blood",
        note="Sin la regla la misma prueba de miedo se hace con 2D6; el positivo usa 3 y descarta el mayor.",
    ),
    _case(
        "v12-stupidity", "complete", "B12.1",
        "new:tirada de estupidez",
        _fighter(weapon="weapon.mace", skills=("mechanic.stupidity",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(), maximum_rounds=3,
        requires=("mechanic.stupidity",),
        participant="first",
        note="Inicio de turno; pierde el turno solo si falla.",
    ),
    _case(
        "v12-stupidity-exempt", "complete", "B12.1",
        "new:control con la exención de estupidez suministrada",
        _fighter(weapon="weapon.mace", skills=("mechanic.stupidity",),
                 conditions=("condition.stupidity-exempt",)),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_battle(), maximum_rounds=3,
        requires=("mechanic.stupidity", "condition.stupidity-exempt"),
        participant="first",
        expect="absent", positive_control="v12-stupidity",
        note="La condición suministrada representa el Héroe Skaven eximente a 6\": "
             "no se tira estupidez y `stupidity-failed` queda falsa; el positivo sí falla.",
    ),
    _case(
        "v14-leader-twelve", "complete", "B14.2",
        "new:Inspiring Presence a 12 pulgadas",
        _fighter(collection="mordheim", band="gunnery-school-of-nuln",
                 profile="senior-student", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            12, provider=_fighter(collection="mordheim",
                                  band="gunnery-school-of-nuln",
                                  profile="senior-gunnery-officer"),
        ), maximum_rounds=2,
        requires=("senior-gunnery-officer", "senior-student", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=8,
        participant="first",
        note="El radio de 12\" es un grant canónico: `senior-gunnery-officer--leader` "
             "(grant: profile) compila `mechanic.leader-six` y `mechanic.leader-twelve` "
             "en el Senior Gunnery Officer, que presta su Ld 8. No se declara ningún "
             "mechanic como skill y no se usa la variante de banda de Reikland, que "
             "la construcción no materializa.",
    ),
    _case(
        "v14-leader-thirteen", "complete", "B14.2",
        "new:control fuera del radio de 12 pulgadas",
        _fighter(collection="mordheim", band="gunnery-school-of-nuln",
                 profile="senior-student", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            13, provider=_fighter(collection="mordheim",
                                  band="gunnery-school-of-nuln",
                                  profile="senior-gunnery-officer"),
        ), maximum_rounds=2,
        requires=("senior-gunnery-officer", "senior-student", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=8,
        participant="first",
        expect="absent", positive_control="v14-leader-twelve",
        note="El mismo proveedor a 13\": fuera del radio de 12\", la prueba usa el "
             "Ld propio 7 del Senior Student.",
    ),
    _case(
        "v14-auto", "complete", "B14.3",
        "new:éxito automático de liderazgo",
        _fighter(weapon="weapon.mace", skills=("mechanic.automatic-leadership",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.automatic-leadership", "stupidity"),
        participant="first",
        note="La prueba de estupidez se declara superada; no exige líder ni radio.",
    ),
    _case(
        "v14-auto-absent", "complete", "B14.3",
        "new:control sin éxito automático de liderazgo",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("stupidity",),
        participant="first",
        expect="absent", positive_control="v14-auto",
        note="Sin la regla la prueba de Ld se tira; el control la declara superada.",
    ),
    _case(
        "v14-own", "complete", "B14.4",
        "new:liderazgo propio; préstamo prohibido",
        _fighter(collection="mordheim", band="battle-monks-of-cathay",
                 profile="raging-peasants", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim",
                                 band="battle-monks-of-cathay",
                                 profile="emissary"),
        ), maximum_rounds=2,
        requires=("raging-peasants", "emissary", "stupidity"),
        witness_value=6,
        participant="first",
        note="El perfil Raging Peasants prohíbe el préstamo: valor propio 6 con el Emissary a 6\".",
    ),
    _case(
        "v14-own-absent", "complete", "B14.4",
        "new:control sin la prohibición de préstamo",
        _fighter(collection="mordheim", band="battle-monks-of-cathay",
                 profile="soldiers", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim",
                                 band="battle-monks-of-cathay",
                                 profile="emissary"),
        ), maximum_rounds=2,
        requires=("emissary", "soldiers", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=6,
        participant="first",
        expect="absent", positive_control="v14-own",
        note="Sin la prohibición, el Emissary a 6\" presta su 8: el valor deja de ser el propio 6.",
    ),
    _case(
        "v14-handler", "complete", "B14.5",
        "new:liderazgo de cuidador a 6 pulgadas",
        _fighter(collection="mordheim", band="night-goblins-web",
                 profile="cave-squigs", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            6, provider=_fighter(collection="mordheim", band="night-goblins-web",
                                 profile="squig-herder"),
        ), maximum_rounds=2,
        requires=("cave-squigs", "squig-herder", "stupidity"),
        decisions={"round.0.first.stupidity.handler.leader": True},
        witness_value=6,
        participant="first",
        note="La rama del handler es alcanzable por la regla canónica de Squigs, no "
             "solo por el Oso: `leadership.py` identifica al receptor por "
             "`fighter_id == 'night-goblins-web:cave-squigs'` y acepta como proveedor "
             "al `squig-herder` con `mechanic.handler-leadership` de la misma banda a "
             "6\" (12\" con pinchador). Handle Animal - Squig presta el Ld 6 del pastor "
             "a cualquier prueba de Liderazgo, y la estupidez suministrada es la que la "
             "hace observable; no se sustituye por la regla del Bear Tamer.",
    ),
    _case(
        "v14-handler-absent", "complete", "B14.5",
        "new:control con el handler fuera de 6 pulgadas",
        _fighter(collection="mordheim", band="night-goblins-web",
                 profile="cave-squigs", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", wounds=3),
        context=_leader_context(
            8, provider=_fighter(collection="mordheim", band="night-goblins-web",
                                 profile="squig-herder"),
        ), maximum_rounds=2,
        requires=("cave-squigs", "squig-herder", "stupidity"),
        decisions={"round.0.first.stupidity.handler.leader": True},
        witness_value=6,
        participant="first",
        expect="absent", positive_control="v14-handler",
        note="El pastor a 8\" queda fuera del radio de 6\" (el perfil no lleva "
             "pinchador por defecto), así que el Squig prueba con su Ld propia 5: el "
             "valor prestado 6 debe estar ausente.",
    ),
    _case(
        "v14-mob", "complete", "B14.6",
        "new:bonificación por aliados a 3 pulgadas",
        _fighter(weapon="weapon.mace", skills=("mechanic.mob-leadership",),
                 traits={"mob_allies": 1, "stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.mob-leadership", "mob_allies", "stupidity"),
        witness_value=8,
        participant="first",
        note="+1 Ld por aliado suministrado en `mob_allies`; no se simula la banda.",
    ),
    _case(
        "v14-mob-absent", "complete", "B14.6",
        "new:control con cero aliados",
        _fighter(weapon="weapon.mace", skills=("mechanic.mob-leadership",),
                 traits={"mob_allies": 0, "stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.mob-leadership", "mob_allies", "stupidity"),
        witness_value=8,
        participant="first",
        expect="absent", positive_control="v14-mob",
        note="Sin aliados el valor es el Ld propio 7; el positivo suma 1.",
    ),
    _case(
        "v14-brood", "complete", "B14.7",
        "new:Brood Mentality solo para estupidez",
        _fighter(weapon="weapon.mace", skills=("mechanic.brood-mentality",),
                 traits={"stupidity": True, "stupidity_leadership_bonus": 1}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("mechanic.brood-mentality", "stupidity",
                  "stupidity_leadership_bonus"),
        witness_value=8,
        participant="first",
        note="Estupidez declarada por trait; el +1 se aplica a su prueba de Ld.",
    ),
    _case(
        "v14-brood-absent", "complete", "B14.7",
        "new:control sin el bonus de Brood Mentality",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("stupidity",),
        witness_value=8,
        participant="first",
        expect="absent", positive_control="v14-brood",
        note="Misma prueba de estupidez sin la regla ni el +1: el valor es 7, no 8.",
    ),
    _case(
        "v14-cold-blood", "complete", "B14.8",
        "new:sangre fría de liderazgo (3D6, conservar 2)",
        _fighter(weapon="weapon.mace",
                 skills=("mechanic.cold-blooded-leadership",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.cold-blooded-leadership", "stupidity"),
        witness_value=3,
        participant="first",
        note="La prueba se hace con 3D6 y descarte del mayor; el testigo es el número de dados.",
    ),
    _case(
        "v14-cold-blood-absent", "complete", "B14.8",
        "new:control sin la sangre fría de liderazgo",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("stupidity",),
        witness_value=3,
        participant="first",
        expect="absent", positive_control="v14-cold-blood",
        note="Sin la regla la misma prueba usa 2D6; el positivo usa 3 y descarta el mayor.",
    ),
    _case(
        "v14-reroll", "complete", "B14.9",
        "new:reroll de liderazgo",
        _fighter(weapon="weapon.mace", skills=("mechanic.leadership-reroll",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("mechanic.leadership-reroll", "stupidity"),
        decisions={"round.0.first.stupidity.reroll": True},
        participant="first",
        note="Primera prueba fallida repetida una vez; la repetición se declara.",
    ),
    _case(
        "v14-reroll-absent", "complete", "B14.9",
        "new:control sin la repetición de liderazgo",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=2,
        requires=("stupidity",),
        participant="first",
        expect="absent", positive_control="v14-reroll",
        note="Sin `leadership-reroll` la primera prueba fallida no se repite; `reroll-used` cero.",
    ),
    _case(
        "v14-relay", "complete", "B14.10",
        "new:relay orders a 6 pulgadas",
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
        ), maximum_rounds=2,
        requires=("adjutant", "commander", "stupidity"),
        decisions={"round.0.first.stupidity.leader.relay": True},
        witness_value=8,
        participant="first",
        note="El Adjutant (Ld 6) transmite el Ld 8 del Commander; su propio valor no se usa.",
    ),
    _case(
        "v14-relay-absent", "complete", "B14.10",
        "new:control sin relay orders",
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
        ), maximum_rounds=2,
        requires=("commander", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=8,
        participant="first",
        expect="absent", positive_control="v14-relay",
        note="Sin relay, el Commander a 12\" queda fuera de 6\"; la prueba usa el Ld propio 7.",
    ),
    _case(
        "v14-relic-first", "complete", "B14.11",
        "new:reliquia sagrada en la primera prueba",
        _fighter(weapon="weapon.mace", defence=("defence.holy-relic",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=1,
        requires=("defence.holy-relic", "stupidity"),
        participant="first",
        note="Solo la primera prueba (ronda 0), que la reliquia declara superada.",
    ),
    _case(
        "v14-relic-second", "complete", "B14.11",
        "new:reliquia sagrada en la segunda prueba",
        _fighter(weapon="weapon.mace", defence=("defence.holy-relic",),
                 traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=3,
        requires=("defence.holy-relic", "stupidity"),
        participant="first",
        expect="absent", positive_control="v14-relic-first",
        note="El portador prueba estupidez en las rondas 0 y 2: la reliquia "
             "gasta su pase automático en la primera y la segunda se tira.",
    ),
    _case(
        "v14-slave", "complete", "B14.12",
        "new:slave driver a 3/6 pulgadas",
        _fighter(collection="mordheim", band="skaven-of-clan-skryre-rel",
                 profile="skaven-slaves", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            3, provider=_fighter(collection="mordheim",
                                 band="skaven-of-clan-skryre-rel",
                                 profile="overseer"),
        ), maximum_rounds=2,
        requires=("skaven-slaves", "overseer", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=6,
        participant="first",
        note="Esclavo de la misma banda usa el Ld 6 del overseer a 3\"; el líder no.",
    ),
    _case(
        "v14-slave-absent", "complete", "B14.12",
        "new:control con el overseer fuera de rango",
        _fighter(collection="mordheim", band="skaven-of-clan-skryre-rel",
                 profile="skaven-slaves", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_leader_context(
            7, provider=_fighter(collection="mordheim",
                                 band="skaven-of-clan-skryre-rel",
                                 profile="overseer"),
        ), maximum_rounds=2,
        requires=("skaven-slaves", "overseer", "stupidity"),
        decisions={"round.0.first.stupidity.leader.leader": True},
        witness_value=6,
        participant="first",
        expect="absent", positive_control="v14-slave",
        note="El overseer a 7\" queda fuera de 3\"; la prueba usa el Ld propio 2 del esclavo.",
    ),
    _case(
        "v14-modifiers", "complete", "B14.13",
        "new:modificador de liderazgo del oponente",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword", skills=("mechanic.enchanting-beauty",)),
        context=_charging(), maximum_rounds=2,
        requires=("mechanic.enchanting-beauty", "stupidity"),
        witness_value=6,
        participant="first",
        note="Enchanting Beauty proyecta `condition.enchanting-beauty` sobre el que prueba: 7 - 1 = 6.",
    ),
    _case(
        "v14-modifiers-absent", "complete", "B14.13",
        "new:control sin el modificador de liderazgo",
        _fighter(weapon="weapon.mace", traits={"stupidity": True}),
        _fighter(weapon="weapon.sword"),
        context=_charging(), maximum_rounds=2,
        requires=("stupidity",),
        witness_value=6,
        participant="first",
        expect="absent", positive_control="v14-modifiers",
        note="La misma prueba sin la belleza encantadora usa el Ld propio 7.",
    ),
    _case(
        "v15-monstrous", "complete", "B15.3",
        "new:incremento del máximo de heridas",
        _fighter(weapon="weapon.mace", skills=("skill.monstrous",)),
        _fighter(weapon="weapon.sword"),
        context=_battle(), maximum_rounds=1,
        requires=("skill.monstrous",),
        witness_value=3,
        participant="first",
        note="+1 Herida inicial (2+1); no es curación.",
    ),
    _case(
        "v15-contagious", "complete", "B15.5",
        "e2e:rule/trollheim/lustria-clan-pestilens/"
        "band--clan-pestilens-special-skills-contagious/trait.contagious::"
        "a-failed-toughness-test-costs-the-attacking-model-a-wound",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=1, traits={"contagious": True}),
        context=_charging(), maximum_rounds=1,
        requires=("contagious",),
        witness_value=1,
        participant="first",
        note="adaptado:a-failed-toughness-test-costs-the-attacking-model-a-wound → "
             "el dado de reacción declarado se sustituye por el recuento de heridas "
             "modificadas sobre 64 filas. Criterio: el atacante pierde 1 herida en "
             "una fila por la prueba de T fallida. Falta el contador de heridas "
             "modificadas por lado.",
    ),
    _case(
        "v15-contagious-absent", "complete", "B15.5",
        "e2e:rule/trollheim/lustria-clan-pestilens/"
        "band--clan-pestilens-special-skills-contagious/trait.contagious::"
        "without-the-rule-the-same-out-result-asks-for-no-reaction",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=1),
        context=_charging(), maximum_rounds=1,
        requires=(),
        witness_value=1,
        participant="first",
        expect="absent", positive_control="v15-contagious",
        note="adaptado:without-the-rule-the-same-out-result-asks-for-no-reaction → "
             "mismo recuento sobre 64 filas. Criterio: ninguna fila con una herida "
             "modificada en el atacante; sin la regla no hay reacción ni prueba.",
    ),
    _case(
        "v15-torturer", "complete", "B15.6",
        "e2e:mechanic/mechanic.torturer::"
        "an-unsaved-wound-costs-the-living-defender-one-strength",
        _fighter(weapon="weapon.mace", skills=("mechanic.torturer",)),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging("first"), maximum_rounds=1,
        requires=("mechanic.torturer",),
        witness_value=1,
        participant="second",
        note="adaptado:an-unsaved-wound-costs-the-living-defender-one-strength → el "
             "estado de Fuerza declarado se sustituye por el recuento de "
             "modificaciones de Fuerza sobre 64 filas. El consumidor real es "
             "`aftermath._react_to_wound`: la pérdida de Fuerza es reactiva a una "
             "herida no salvada en close combat y no pide decisión (el agarre del "
             "gaoler es otra regla). Criterio: el defensor sufre 1 pérdida de Fuerza "
             "en una fila.",
    ),
    _case(
        "v15-torturer-absent", "complete", "B15.6",
        "e2e:mechanic/mechanic.torturer::"
        "an-unsaved-wound-costs-the-living-defender-one-strength",
        _fighter(weapon="weapon.mace"),
        _fighter(weapon="weapon.mace", wounds=3),
        context=_charging("first"), maximum_rounds=1,
        requires=(),
        witness_value=1,
        participant="second",
        expect="absent", positive_control="v15-torturer",
        note="control del mismo escenario sin `mechanic.torturer`: mismo recuento "
             "sobre 64 filas. Criterio: ninguna pérdida de Fuerza en el defensor.",
    ),
    # -- deep: justified interactions between already materialized rules -----
    _case(
        "d08-frenzy-parry", "deep", "B08.2",
        "new:interacción ataques adicionales → capacidad defensiva",
        _fighter(weapon="weapon.mace", traits={"frenzy": True}),
        _fighter(weapon="weapon.sword", off_hand="defence.buckler"),
        context=_charging(), maximum_rounds=3,
        requires=("frenzy", "defence.buckler"),
        note="El frenesí amplía el pool de la carga y la rodela decide cuántos de "
             "esos ataques se paran con repetición; composición B08.2 + B06.2.",
    ),
    _case(
        "d04-armour-parry", "deep", "B04.3",
        "new:interacción armadura → parada",
        _fighter(weapon="weapon.mace", strength=4),
        _fighter(weapon="weapon.mace", armour="armour.light-armour",
                 off_hand="defence.buckler"),
        context=_charging(), maximum_rounds=3,
        requires=("armour.light-armour", "defence.buckler"),
        note="La armadura ligera y la rodela resuelven dos defensas distintas en la "
             "misma secuencia; composición B04.1 + B04.3 + B06.2.",
    ),
    _case(
        "d10-order-attacks", "deep", "B10.1",
        "new:interacción orden de actuación → ataques",
        _fighter(weapon="weapon.pike", initiative=2),
        _fighter(weapon="weapon.mace", attacks=2, initiative=5),
        context=_charging(), maximum_rounds=2,
        requires=("weapon.pike",),
        note="El pike en carga actúa primero aunque su Iniciativa sea menor; el "
             "defensor con dos ataques conserva su pool. Composición B10.1 + B08.1.",
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


def case_magnitudes(case: BatteryCase) -> tuple[str, ...]:
    """Return the terminal magnitudes a statistical case compares.

    ``winner`` is always present, first, because it is the base comparison.
    Any other declared observable is compared only when it is a terminal
    distribution both engines expose with the same meaning; a witness name is
    ignored instead of becoming a requirement.
    """
    magnitudes = ["winner"]
    for name in case.observables:
        if name in STATISTICAL_MAGNITUDES and name not in magnitudes:
            magnitudes.append(name)
    return tuple(magnitudes)


def input_limit(case: BatteryCase) -> str | None:
    """Return the real input limitation that prevents running ``case``.

    A witness or consumer tag is retired from the statistical path: it never
    blocks a real duel sample.  ``state:``/``decision:`` tags stay real limits
    because the scenario needs an input the current build cannot produce — an
    initial state, a campaign-only preparation, a construction-time refusal or
    a rule branch no canonical build reaches — and a per-row decision script
    remains unsupported.  Such a case is kept in the profile denominator with
    its cause, never silently replaced.
    """
    if case.decision_scope == "per-row":
        return "decision:per-row"
    blocked = case.blocked_by
    if blocked is None:
        return None
    if blocked.startswith(("state:", "decision:")):
        return blocked
    return None


_BLOCKED_PREFIXES = ("state:", "consume:", "witness:", "decision:")


def _build_ids(build: FighterBuild) -> set[str]:
    values: set[str] = set()
    for name in (
        "main_weapon_id", "off_hand_id", "armour_id", "main_material_id",
        "off_material_id", "main_poison_id", "off_poison_id", "profile_id", "band_id",
    ):
        value = getattr(build, name, None)
        if isinstance(value, str):
            values.add(value)
    for name in (
        "defence_ids", "skill_ids", "preparation_ids", "special_rule_ids",
        "condition_ids", "variant_ids", "owned_item_ids",
    ):
        values.update(getattr(build, name, ()) or ())
    values.update(str(key) for key in (build.trait_overrides or {}))
    return values


def validate_cases(
    cases: tuple[BatteryCase, ...] = _CASES, *, require_coverage: bool = True,
) -> None:
    """Check the structural invariants that need no engine execution.

    The statistical contract validates the scenario (variant, origin, declared
    magnitudes, sample parameters and real input limits); it imposes no witness,
    expectation or positive-control requirement.
    """
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("battery case ids must be unique")
    for case in cases:
        if case.level not in PROFILE_LEVELS:
            raise ValueError(f"unknown profile level in {case.id}: {case.level}")
        variant = VARIANTS.get(case.variant)
        if variant is None:
            raise ValueError(f"{case.id} names unknown variant {case.variant}")
        if variant.case_kind != "duel":
            raise ValueError(f"{case.id} uses non-duel variant {case.variant}")
        if case.witness is not None and case.witness not in WITNESSES:
            raise ValueError(f"{case.id} overrides with an unknown witness {case.witness}")
        if not case_magnitudes(case):
            raise ValueError(f"{case.id} declares no terminal magnitude")
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
        if case.participant not in {"first", "second", "both"}:
            raise ValueError(f"{case.id} has an unknown participant {case.participant!r}")
        if case.expect not in {"present", "absent"}:
            raise ValueError(f"{case.id} has an unknown expect {case.expect!r}")
        if case.also_covers:
            # One case belongs to one variant.  A secondary label cannot count as
            # covered just because the same scenario touches another rule: use a
            # separate case for it.
            raise ValueError(
                f"{case.id} declares also_covers; use a separate case per variant"
            )
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
    for level in PROFILE_LEVELS[1:]:
        previous = {case.id for case in battery_cases(PROFILE_LEVELS[PROFILE_LEVELS.index(level) - 1], cases)}
        current = {case.id for case in battery_cases(level, cases)}
        if not previous <= current:
            raise ValueError(f"profile {level} does not contain the previous profile")
    if require_coverage:
        covered = {
            case.variant for case in battery_cases("complete", cases)
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
