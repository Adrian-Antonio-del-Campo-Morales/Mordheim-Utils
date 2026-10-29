"""Codec and loader for the precompiled engine cases (T02).

The corpus is a versioned, canonical JSON document shared by the modular,
vectorized, native, parity and benchmark suites.  This module is deliberately
independent of the knowledge base, the construction compiler and the combat
packages: it only understands the core dataclasses it has to reconstruct.

Public surface (fixed by T01)::

    load_cases(path) -> Mapping[str, CompiledCase]
    encode_case(case) / decode_case(raw)
    encode_compiled_fighter / decode_compiled_fighter
    encode_effect_set / decode_effect_set
    encode_duel_context / decode_duel_context
    encode_local_participant / decode_local_participant
    canonical_json(obj)

A missing or incompatible document raises CompiledCaseError.  Nothing in this
module ever recompiles a fighter or reads the knowledge base.
"""
from __future__ import annotations

from dataclasses import MISSING
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from dataclasses import fields
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from mordheim_core.models import CarriedEquipment
from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelContext
from mordheim_core.models import EffectSet
from mordheim_core.models import LocalParticipant
from mordheim_core.models import MutationOption


SCHEMA = "mordheim-compiled-cases"
SCHEMA_VERSION = 1
EFFECT_SCHEMA = "EffectSet/v1"

_ORIGIN_KINDS = frozenset({"unit", "e2e", "semantic", "benchmark"})
_PARTICIPANT_CONDITIONS = frozenset({
    "standing", "knocked-down", "stunned", "paralyzed", "out", "fleeing",
})
_STATE_CONDITIONS = frozenset({"STANDING", "KNOCKED_DOWN", "STUNNED", "PARALYZED", "OUT"})
_CASE_FIELDS = frozenset({
    "case_key", "origin", "fighters", "context", "auxiliary_participants",
    "initial_state", "determinism", "limits", "benchmark", "expectations",
    "fingerprints",
})
_DOCUMENT_FIELDS = frozenset({
    "schema", "schema_version", "generator", "source", "cases", "fingerprints",
})
_EXPECTATION_FIELDS = frozenset({
    "expect_initial", "expect_rounds", "expect_final", "expect_events",
    "expect_fighters", "expect_error", "expect", "distribution",
})


class CompiledCaseError(ValueError):
    """A precompiled case, or the document containing it, is invalid."""

    def __init__(self, case_key: str, field: str, reason: str):
        self.case_key = case_key
        self.field = field
        self.reason = reason
        super().__init__(f"{case_key}: {field}: {reason}")


@dataclass(frozen=True, slots=True)
class CaseOrigin:
    kind: str
    node_id: str
    path: str
    sha256: str


@dataclass(frozen=True, slots=True)
class CaseLimits:
    """Declared inputs of a frozen case.

    The maintained scenario entries carry only their round budget: sample
    widths, seeds and batch sizes are execution configuration, not scenario
    data.  Historical cases keep the three sample fields, so both shapes load
    and encode.
    """

    simulations: int | None = None
    seed: int | None = None
    batch_size: int | None = None
    maximum_rounds: int = 50


@dataclass(frozen=True, slots=True)
class CompiledCase:
    case_key: str
    origin: CaseOrigin
    first: CompiledFighter
    second: CompiledFighter
    context: DuelContext | None = None
    auxiliary_participants: tuple[LocalParticipant, ...] = ()
    initial_state: Mapping[str, Mapping[str, object]] = dataclass_field(default_factory=dict)
    dice: tuple[Mapping[str, object], ...] = ()
    decisions: tuple[Mapping[str, object], ...] = ()
    limits: CaseLimits = CaseLimits(1, 0, 100_000, 1)
    benchmark: Mapping[str, object] | None = None
    expectations: Mapping[str, object] | None = None
    fingerprints: Mapping[str, str] = dataclass_field(default_factory=dict)


def _fail(case_key: str, field: str, reason: str) -> None:
    raise CompiledCaseError(case_key, field, reason)


def canonical_json(value: object) -> str:
    """Stable UTF-8 JSON used for hashes and for the corpus file itself."""
    try:
        return json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise CompiledCaseError("<document>", "json", str(error)) from error


def _sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _mapping(value: object, case_key: str, field: str) -> Mapping:
    if not isinstance(value, dict):
        _fail(case_key, field, f"expected an object, got {type(value).__name__}")
    return value


def _sequence(value: object, case_key: str, field: str) -> list:
    if not isinstance(value, list):
        _fail(case_key, field, f"expected an array, got {type(value).__name__}")
    return value


def _text(value: object, case_key: str, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        _fail(case_key, field, "expected a non-empty string")
    return value


def _integer(value: object, case_key: str, field: str, *, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        _fail(case_key, field, f"expected an integer, got {type(value).__name__}")
    if minimum is not None and value < minimum:
        _fail(case_key, field, f"expected an integer >= {minimum}, got {value}")
    return value


def _boolean(value: object, case_key: str, field: str) -> bool:
    if not isinstance(value, bool):
        _fail(case_key, field, f"expected a boolean, got {type(value).__name__}")
    return value


def _optional(value: object, case_key: str, field: str, decoder):
    if value is None:
        return None
    return decoder(value, case_key, field)


def _hex_digest(value: object, case_key: str, field: str) -> str:
    text = _text(value, case_key, field)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        _fail(case_key, field, "expected a lowercase sha256 hex digest")
    return text


def _relative_path(value: object, case_key: str, field: str) -> str:
    text = _text(value, case_key, field)
    if "\\" in text or text.startswith("/") or ".." in text.split("/"):
        _fail(case_key, field, "expected a relative POSIX path")
    return text


def _exact_keys(raw: Mapping, expected: frozenset[str], case_key: str, field: str) -> None:
    unknown = sorted(set(raw) - expected)
    missing = sorted(expected - set(raw))
    if unknown:
        _fail(case_key, field, "unknown field(s): " + ", ".join(unknown))
    if missing:
        _fail(case_key, field, "missing field(s): " + ", ".join(missing))


def _effect_defaults() -> dict[str, object]:
    defaults = {}
    for item in fields(EffectSet):
        if item.default is not MISSING:
            defaults[item.name] = item.default
        else:
            defaults[item.name] = item.default_factory()
    return defaults


_EFFECT_DEFAULTS = _effect_defaults()


def encode_effect_set(value: EffectSet) -> dict:
    if not isinstance(value, EffectSet):
        raise CompiledCaseError("<value>", "effect", "expected EffectSet")
    sparse = {}
    for name, default in _EFFECT_DEFAULTS.items():
        current = getattr(value, name)
        if current != default:
            sparse[name] = list(current) if isinstance(current, tuple) else current
    return sparse


def decode_effect_set(raw: object, case_key: str = "<value>", field: str = "effect") -> EffectSet:
    data = _mapping(raw, case_key, field)
    values = {}
    for name, value in data.items():
        if name not in _EFFECT_DEFAULTS:
            _fail(case_key, f"{field}.{name}", "unknown EffectSet field")
        default = _EFFECT_DEFAULTS[name]
        if isinstance(default, bool):
            values[name] = _boolean(value, case_key, f"{field}.{name}")
        elif isinstance(default, int):
            values[name] = _integer(value, case_key, f"{field}.{name}")
        elif isinstance(default, tuple):
            entries = _sequence(value, case_key, f"{field}.{name}")
            values[name] = tuple(
                _text(entry, case_key, f"{field}.{name}[]") for entry in entries
            )
        else:  # pragma: no cover - guards a future EffectSet field type
            _fail(case_key, f"{field}.{name}", "unsupported EffectSet field type")
    try:
        return EffectSet(**values)
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


def encode_characteristics(value: Characteristics) -> dict:
    if not isinstance(value, Characteristics):
        raise CompiledCaseError("<value>", "characteristics", "expected Characteristics")
    return {
        "weapon_skill": value.weapon_skill,
        "strength": value.strength,
        "toughness": value.toughness,
        "wounds": value.wounds,
        "initiative": value.initiative,
        "attacks": value.attacks,
        "movement": value.movement,
        "leadership": value.leadership,
    }


def decode_characteristics(raw: object, case_key: str = "<value>", field: str = "characteristics") -> Characteristics:
    data = _mapping(raw, case_key, field)
    expected = frozenset({
        "weapon_skill", "strength", "toughness", "wounds", "initiative", "attacks",
        "movement", "leadership",
    })
    _exact_keys(data, expected, case_key, field)
    values = {
        name: _integer(data[name], case_key, f"{field}.{name}")
        for name in ("weapon_skill", "strength", "toughness", "wounds", "attacks")
    }
    for name in ("initiative", "movement", "leadership"):
        values[name] = _optional(
            data[name], case_key, f"{field}.{name}",
            lambda value, key, label: _integer(value, key, label),
        )
    try:
        return Characteristics(**values)
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


def encode_carried_equipment(value: CarriedEquipment) -> dict:
    if not isinstance(value, CarriedEquipment):
        raise CompiledCaseError("<value>", "equipment", "expected CarriedEquipment")
    return {
        "item_id": value.item_id,
        "effect": encode_effect_set(value.effect),
        "kind": value.kind,
        "slot": value.slot,
        "stat_bonuses": [list(entry) for entry in value.stat_bonuses],
        "effect_without_poison": (
            None if value.effect_without_poison is None
            else encode_effect_set(value.effect_without_poison)
        ),
    }


def decode_carried_equipment(raw: object, case_key: str = "<value>", field: str = "equipment") -> CarriedEquipment:
    data = _mapping(raw, case_key, field)
    expected = frozenset({
        "item_id", "effect", "kind", "slot", "stat_bonuses", "effect_without_poison",
    })
    _exact_keys(data, expected, case_key, field)
    bonuses = _sequence(data["stat_bonuses"], case_key, f"{field}.stat_bonuses")
    decoded_bonuses = []
    for index, entry in enumerate(bonuses):
        pair = _sequence(entry, case_key, f"{field}.stat_bonuses[{index}]")
        if len(pair) != 2:
            _fail(case_key, f"{field}.stat_bonuses[{index}]", "expected [name, value]")
        decoded_bonuses.append((
            _text(pair[0], case_key, f"{field}.stat_bonuses[{index}].name"),
            _integer(pair[1], case_key, f"{field}.stat_bonuses[{index}].value"),
        ))
    try:
        return CarriedEquipment(
            item_id=_text(data["item_id"], case_key, f"{field}.item_id"),
            effect=decode_effect_set(data["effect"], case_key, f"{field}.effect"),
            kind=_text(data["kind"], case_key, f"{field}.kind"),
            slot=_optional(data["slot"], case_key, f"{field}.slot",
                           lambda value, key, label: _text(value, key, label)),
            stat_bonuses=tuple(decoded_bonuses),
            effect_without_poison=_optional(
                data["effect_without_poison"], case_key, f"{field}.effect_without_poison",
                decode_effect_set,
            ),
        )
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


def encode_mutation_option(value: MutationOption) -> dict:
    if not isinstance(value, MutationOption):
        raise CompiledCaseError("<value>", "mutation", "expected MutationOption")
    return {
        "roll": value.roll,
        "effect": encode_effect_set(value.effect),
        "stat_ops": [list(entry) for entry in value.stat_ops],
        "extra_attacks": [encode_effect_set(entry) for entry in value.extra_attacks],
        "limb_forms": [encode_effect_set(entry) for entry in value.limb_forms],
    }


def decode_mutation_option(raw: object, case_key: str = "<value>", field: str = "mutation") -> MutationOption:
    data = _mapping(raw, case_key, field)
    _exact_keys(
        data,
        frozenset({"roll", "effect", "stat_ops", "extra_attacks", "limb_forms"}),
        case_key, field,
    )
    stat_ops = []
    for index, entry in enumerate(_sequence(data["stat_ops"], case_key, f"{field}.stat_ops")):
        triple = _sequence(entry, case_key, f"{field}.stat_ops[{index}]")
        if len(triple) != 3:
            _fail(case_key, f"{field}.stat_ops[{index}]", "expected [target, stat, value]")
        stat_ops.append((
            _text(triple[0], case_key, f"{field}.stat_ops[{index}].target"),
            _text(triple[1], case_key, f"{field}.stat_ops[{index}].stat"),
            _integer(triple[2], case_key, f"{field}.stat_ops[{index}].value"),
        ))
    try:
        return MutationOption(
            roll=_integer(data["roll"], case_key, f"{field}.roll", minimum=1),
            effect=decode_effect_set(data["effect"], case_key, f"{field}.effect"),
            stat_ops=tuple(stat_ops),
            extra_attacks=tuple(
                decode_effect_set(entry, case_key, f"{field}.extra_attacks[{index}]")
                for index, entry in enumerate(
                    _sequence(data["extra_attacks"], case_key, f"{field}.extra_attacks")
                )
            ),
            limb_forms=tuple(
                decode_effect_set(entry, case_key, f"{field}.limb_forms[{index}]")
                for index, entry in enumerate(
                    _sequence(data["limb_forms"], case_key, f"{field}.limb_forms")
                )
            ),
        )
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


# -- CompiledFighter --------------------------------------------------------

def _encode_optional_effect(value: EffectSet | None):
    return None if value is None else encode_effect_set(value)


def _decode_optional_effect(value, case_key, field):
    return _optional(value, case_key, field, decode_effect_set)


def _encode_effects(values):
    return [encode_effect_set(entry) for entry in values]


def _decode_effects(value, case_key, field):
    return tuple(
        decode_effect_set(entry, case_key, f"{field}[{index}]")
        for index, entry in enumerate(_sequence(value, case_key, field))
    )


def _encode_effect_pairs(values):
    return [[encode_effect_set(first), encode_effect_set(second)] for first, second in values]


def _decode_effect_pairs(value, case_key, field):
    decoded = []
    for index, entry in enumerate(_sequence(value, case_key, field)):
        pair = _sequence(entry, case_key, f"{field}[{index}]")
        if len(pair) != 2:
            _fail(case_key, f"{field}[{index}]", "expected an EffectSet pair")
        decoded.append((
            decode_effect_set(pair[0], case_key, f"{field}[{index}][0]"),
            decode_effect_set(pair[1], case_key, f"{field}[{index}][1]"),
        ))
    return tuple(decoded)


def _encode_random_characteristics(values):
    return [list(entry) for entry in values]


def _decode_random_characteristics(value, case_key, field):
    decoded = []
    for index, entry in enumerate(_sequence(value, case_key, field)):
        row = _sequence(entry, case_key, f"{field}[{index}]")
        if len(row) != 4:
            _fail(case_key, f"{field}[{index}]", "expected [name, count, sides, bonus]")
        decoded.append((
            _text(row[0], case_key, f"{field}[{index}].name"),
            _integer(row[1], case_key, f"{field}[{index}].count"),
            _integer(row[2], case_key, f"{field}[{index}].sides"),
            _integer(row[3], case_key, f"{field}[{index}].bonus"),
        ))
    return tuple(decoded)


def _encode_text_list(values):
    return list(values)


def _decode_text_list(value, case_key, field):
    return tuple(
        _text(entry, case_key, f"{field}[{index}]")
        for index, entry in enumerate(_sequence(value, case_key, field))
    )


def _encode_optional_int(value):
    return value


def _decode_optional_int(value, case_key, field):
    return _optional(value, case_key, field,
                     lambda entry, key, label: _integer(entry, key, label))


def _encode_optional_text(value):
    return value


def _decode_optional_text(value, case_key, field):
    return _optional(value, case_key, field,
                     lambda entry, key, label: _text(entry, key, label))


def _encode_mutations(values):
    return [encode_mutation_option(entry) for entry in values]


def _decode_mutations(value, case_key, field):
    return tuple(
        decode_mutation_option(entry, case_key, f"{field}[{index}]")
        for index, entry in enumerate(_sequence(value, case_key, field))
    )


def _encode_carried(values):
    return [encode_carried_equipment(entry) for entry in values]


def _decode_carried(value, case_key, field):
    return tuple(
        decode_carried_equipment(entry, case_key, f"{field}[{index}]")
        for index, entry in enumerate(_sequence(value, case_key, field))
    )


def _identity(value, case_key, field):
    return value


_FIGHTER_ENCODERS = {
    "fighter_id": lambda value: value,
    "characteristics": encode_characteristics,
    "main_weapon": encode_effect_set,
    "off_hand": _encode_optional_effect,
    "global_effects": encode_effect_set,
    "armour_save": lambda value: value,
    "helmet_save": lambda value: value,
    "natural_armour_save": lambda value: value,
    "off_hand_attacks": lambda value: value,
    "natural_armour_unmodified": lambda value: value,
    "injury_profile": lambda value: value,
    "random_characteristics": _encode_random_characteristics,
    "natural_armour_worst_save": lambda value: value,
    "shield_and_skill_effects": encode_effect_set,
    "extra_attacks": _encode_effects,
    "missile_weapon_limit": lambda value: value,
    "ballistic_skill": lambda value: value,
    "construction_tags": _encode_text_list,
    "main_weapon_without_poison": _encode_optional_effect,
    "off_hand_without_poison": _encode_optional_effect,
    "mounted": lambda value: value,
    "unarmed_weapon": _encode_optional_effect,
    "main_hand_slot": lambda value: value,
    "off_hand_slot": lambda value: value,
    "vomit_attack": _encode_optional_effect,
    "stupidity_leadership": _encode_optional_int,
    "stupidity_leadership_bonus": lambda value: value,
    "mob_allies": lambda value: value,
    "animal_handler_leadership": _encode_optional_int,
    "skill_effects_only": encode_effect_set,
    "global_effects_without_equipment": encode_effect_set,
    "mutation_options": _encode_mutations,
    "mutation_equipment": _encode_carried,
    "natural_armour_stacks": lambda value: value,
    "extra_attacks_without_poison": _encode_effect_pairs,
}

_FIGHTER_DECODERS = {
    "fighter_id": lambda value, key, label: _text(value, key, label),
    "characteristics": decode_characteristics,
    "main_weapon": decode_effect_set,
    "off_hand": _decode_optional_effect,
    "global_effects": decode_effect_set,
    "armour_save": lambda value, key, label: _integer(value, key, label, minimum=1),
    "helmet_save": lambda value, key, label: _integer(value, key, label, minimum=1),
    "natural_armour_save": lambda value, key, label: _integer(value, key, label, minimum=1),
    "off_hand_attacks": lambda value, key, label: _boolean(value, key, label),
    "natural_armour_unmodified": lambda value, key, label: _boolean(value, key, label),
    "injury_profile": lambda value, key, label: _integer(value, key, label, minimum=0),
    "random_characteristics": _decode_random_characteristics,
    "natural_armour_worst_save": lambda value, key, label: _integer(value, key, label, minimum=1),
    "shield_and_skill_effects": decode_effect_set,
    "extra_attacks": _decode_effects,
    "missile_weapon_limit": lambda value, key, label: _integer(value, key, label, minimum=0),
    "ballistic_skill": lambda value, key, label: _integer(value, key, label, minimum=0),
    "construction_tags": _decode_text_list,
    "main_weapon_without_poison": _decode_optional_effect,
    "off_hand_without_poison": _decode_optional_effect,
    "mounted": lambda value, key, label: _boolean(value, key, label),
    "unarmed_weapon": _decode_optional_effect,
    "main_hand_slot": lambda value, key, label: _text(value, key, label),
    "off_hand_slot": lambda value, key, label: _text(value, key, label),
    "vomit_attack": _decode_optional_effect,
    "stupidity_leadership": _decode_optional_int,
    "stupidity_leadership_bonus": lambda value, key, label: _integer(value, key, label),
    "mob_allies": lambda value, key, label: _integer(value, key, label, minimum=0),
    "animal_handler_leadership": _decode_optional_int,
    "skill_effects_only": decode_effect_set,
    "global_effects_without_equipment": decode_effect_set,
    "mutation_options": _decode_mutations,
    "mutation_equipment": _decode_carried,
    "natural_armour_stacks": lambda value, key, label: _boolean(value, key, label),
    "extra_attacks_without_poison": _decode_effect_pairs,
}

assert set(_FIGHTER_ENCODERS) == {item.name for item in fields(CompiledFighter)}
assert set(_FIGHTER_DECODERS) == set(_FIGHTER_ENCODERS)


def encode_compiled_fighter(value: CompiledFighter) -> dict:
    if not isinstance(value, CompiledFighter):
        raise CompiledCaseError("<value>", "fighter", "expected CompiledFighter")
    return {
        name: encoder(getattr(value, name))
        for name, encoder in _FIGHTER_ENCODERS.items()
    }


def decode_compiled_fighter(raw: object, case_key: str = "<value>", field: str = "fighter") -> CompiledFighter:
    data = _mapping(raw, case_key, field)
    _exact_keys(data, frozenset(_FIGHTER_DECODERS), case_key, field)
    values = {
        name: decoder(data[name], case_key, f"{field}.{name}")
        for name, decoder in _FIGHTER_DECODERS.items()
    }
    try:
        return CompiledFighter(**values)
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


# -- Duel context and participants -----------------------------------------

def encode_local_participant(value: LocalParticipant) -> dict:
    if not isinstance(value, LocalParticipant):
        raise CompiledCaseError("<value>", "participant", "expected LocalParticipant")
    return {
        "participant_id": value.participant_id,
        "side_id": value.side_id,
        "fighter": encode_compiled_fighter(value.fighter),
        "condition": value.condition,
    }


def decode_local_participant(raw: object, case_key: str = "<value>", field: str = "participant") -> LocalParticipant:
    data = _mapping(raw, case_key, field)
    _exact_keys(
        data, frozenset({"participant_id", "side_id", "fighter", "condition"}),
        case_key, field,
    )
    condition = _text(data["condition"], case_key, f"{field}.condition")
    if condition not in _PARTICIPANT_CONDITIONS:
        _fail(case_key, f"{field}.condition", f"unknown condition {condition!r}")
    try:
        return LocalParticipant(
            participant_id=_text(data["participant_id"], case_key, f"{field}.participant_id"),
            side_id=_text(data["side_id"], case_key, f"{field}.side_id"),
            fighter=decode_compiled_fighter(data["fighter"], case_key, f"{field}.fighter"),
            condition=condition,
        )
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


def encode_duel_context(value: DuelContext) -> dict:
    if not isinstance(value, DuelContext):
        raise CompiledCaseError("<value>", "context", "expected DuelContext")
    return {
        "first_id": value.first_id,
        "second_id": value.second_id,
        "nearby": [encode_local_participant(item) for item in value.nearby],
        "distances": [list(item) for item in value.distances],
        "contacts": None if value.contacts is None else [list(item) for item in value.contacts],
        "terrain": [list(item) for item in value.terrain],
        "charging": None if value.charging is None else list(value.charging),
        "active_participant": value.active_participant,
    }


def decode_duel_context(raw: object, case_key: str = "<value>", field: str = "context") -> DuelContext:
    data = _mapping(raw, case_key, field)
    _exact_keys(
        data,
        frozenset({
            "first_id", "second_id", "nearby", "distances", "contacts", "terrain",
            "charging", "active_participant",
        }),
        case_key, field,
    )
    nearby = tuple(
        decode_local_participant(entry, case_key, f"{field}.nearby[{index}]")
        for index, entry in enumerate(_sequence(data["nearby"], case_key, f"{field}.nearby"))
    )
    distances = []
    for index, entry in enumerate(_sequence(data["distances"], case_key, f"{field}.distances")):
        row = _sequence(entry, case_key, f"{field}.distances[{index}]")
        if len(row) != 3:
            _fail(case_key, f"{field}.distances[{index}]", "expected [first, second, inches]")
        first = _text(row[0], case_key, f"{field}.distances[{index}].first")
        second = _text(row[1], case_key, f"{field}.distances[{index}].second")
        inches = row[2]
        if isinstance(inches, bool) or not isinstance(inches, (int, float)) or not math.isfinite(inches):
            _fail(case_key, f"{field}.distances[{index}].inches", "expected finite inches")
        distances.append((first, second, inches))
    contacts = None
    if data["contacts"] is not None:
        contacts = []
        for index, entry in enumerate(_sequence(data["contacts"], case_key, f"{field}.contacts")):
            pair = _sequence(entry, case_key, f"{field}.contacts[{index}]")
            if len(pair) != 2:
                _fail(case_key, f"{field}.contacts[{index}]", "expected [first, second]")
            contacts.append((
                _text(pair[0], case_key, f"{field}.contacts[{index}].first"),
                _text(pair[1], case_key, f"{field}.contacts[{index}].second"),
            ))
    terrain = []
    for index, entry in enumerate(_sequence(data["terrain"], case_key, f"{field}.terrain")):
        pair = _sequence(entry, case_key, f"{field}.terrain[{index}]")
        if len(pair) != 2:
            _fail(case_key, f"{field}.terrain[{index}]", "expected [participant, label]")
        terrain.append((
            _text(pair[0], case_key, f"{field}.terrain[{index}].participant"),
            _text(pair[1], case_key, f"{field}.terrain[{index}].label"),
        ))
    charging = None
    if data["charging"] is not None:
        charging = tuple(
            _text(entry, case_key, f"{field}.charging[{index}]")
            for index, entry in enumerate(_sequence(data["charging"], case_key, f"{field}.charging"))
        )
    active = _optional(
        data["active_participant"], case_key, f"{field}.active_participant",
        lambda entry, key, label: _text(entry, key, label),
    )
    try:
        return DuelContext(
            first_id=_text(data["first_id"], case_key, f"{field}.first_id"),
            second_id=_text(data["second_id"], case_key, f"{field}.second_id"),
            nearby=nearby,
            distances=tuple(distances),
            contacts=None if contacts is None else tuple(contacts),
            terrain=tuple(terrain),
            charging=charging,
            active_participant=active,
        )
    except (TypeError, ValueError) as error:
        _fail(case_key, field, str(error))


# -- initial state ---------------------------------------------------------
#
# FighterState lives in the combat package, which this module must not import.
# The field names and JSON shapes are therefore fixed here as part of the
# shared contract; a mismatch is a deliberate schema change, not an inference.

_INITIAL_STATE_KINDS: dict[str, str] = {
    "wounds": "int",
    "condition": "condition",
    "frenzy": "bool",
    "lucky_charm": "bool",
    "resources_spent": "frozenset_str",
    "on_fire": "bool",
    "entangled": "bool",
    "attack_penalty": "int",
    "initiative_penalty": "int",
    "initiative_floor": "int",
    "parries_remaining": "int",
    "critical_available": "bool",
    "force_of_will_active": "bool",
    "force_of_will_penalty": "int",
    "weapon_skill": "int",
    "strength": "int",
    "torture_strength_loss": "int",
    "toughness": "int",
    "initiative": "optional_int",
    "attacks": "int",
    "broken_hands": "frozenset_str",
    "hampered_hands": "tuple_str",
    "fear_hit_sixes": "bool",
    "stupidity_failed": "bool",
    "massively_built_lost_turn": "bool",
    "charm_attack_blocked": "bool",
    "charm_auto_hit": "bool",
    "entranced": "bool",
    "guiding_dream_result": "int",
    "drunken_result": "int",
    "animosity_failed": "bool",
    "last_shadow_dance": "optional_str",
    "dodge_trick_active": "bool",
    "banter_trick_active": "bool",
    "trip_trick_active": "bool",
    "mouth_sewn": "bool",
    "hillman_wolf": "bool",
    "devoted_frenzy": "bool",
    "drenok_fighting": "bool",
    "transformed": "bool",
    "equipment_cast_off": "bool",
    "bitten_result": "int",
    "lunatic_result": "int",
    "lunatic_stupidity": "bool",
    "feral_instinct_failed": "bool",
    "danse_macabre_controlled": "bool",
    "random_rolled": "frozenset_str",
    "random_modifiers": "pairs_str_int",
    "random_round": "int",
    "starting_wounds": "int",
    "djinn_power": "optional_str",
    "last_djinn_power": "optional_str",
    "electrical_available_at": "int",
    "grappled": "bool",
    "grappling": "bool",
    "netted": "bool",
    "mutations": "mutations",
    "mutation_weapon_limbs": "effects",
    "atrophied_arms": "int",
    "atrophied_legs": "int",
    "mutated_hands": "tuple_str",
    "mutation_equipment": "carried_optional",
    "alchemist_backley_penalties": "pairs_str_int",
}


def _encode_initial_value(name: str, value: object):
    kind = _INITIAL_STATE_KINDS[name]
    if kind == "frozenset_str":
        return sorted(value)
    if kind == "tuple_str":
        return list(value)
    if kind == "pairs_str_int":
        return [list(entry) for entry in value]
    if kind == "mutations":
        return [encode_mutation_option(entry) for entry in value]
    if kind == "effects":
        return [encode_effect_set(entry) for entry in value]
    if kind == "carried_optional":
        return None if value is None else [encode_carried_equipment(entry) for entry in value]
    return value


def _decode_initial_value(name: str, value: object, case_key: str, field: str):
    kind = _INITIAL_STATE_KINDS[name]
    if kind == "int":
        return _integer(value, case_key, field)
    if kind == "bool":
        return _boolean(value, case_key, field)
    if kind == "optional_int":
        return _optional(value, case_key, field,
                         lambda entry, key, label: _integer(entry, key, label))
    if kind == "optional_str":
        return _optional(value, case_key, field,
                         lambda entry, key, label: _text(entry, key, label))
    if kind == "condition":
        text = _text(value, case_key, field)
        if text not in _STATE_CONDITIONS:
            _fail(case_key, field, f"unknown Condition name {text!r}")
        return text
    if kind == "frozenset_str":
        return frozenset(
            _text(entry, case_key, f"{field}[{index}]")
            for index, entry in enumerate(_sequence(value, case_key, field))
        )
    if kind == "tuple_str":
        return tuple(
            _text(entry, case_key, f"{field}[{index}]")
            for index, entry in enumerate(_sequence(value, case_key, field))
        )
    if kind == "pairs_str_int":
        decoded = []
        for index, entry in enumerate(_sequence(value, case_key, field)):
            pair = _sequence(entry, case_key, f"{field}[{index}]")
            if len(pair) != 2:
                _fail(case_key, f"{field}[{index}]", "expected [name, value]")
            decoded.append((
                _text(pair[0], case_key, f"{field}[{index}].name"),
                _integer(pair[1], case_key, f"{field}[{index}].value"),
            ))
        return tuple(decoded)
    if kind == "mutations":
        return tuple(
            decode_mutation_option(entry, case_key, f"{field}[{index}]")
            for index, entry in enumerate(_sequence(value, case_key, field))
        )
    if kind == "effects":
        return tuple(
            decode_effect_set(entry, case_key, f"{field}[{index}]")
            for index, entry in enumerate(_sequence(value, case_key, field))
        )
    if kind == "carried_optional":
        if value is None:
            return None
        return tuple(
            decode_carried_equipment(entry, case_key, f"{field}[{index}]")
            for index, entry in enumerate(_sequence(value, case_key, field))
        )
    _fail(case_key, field, f"unsupported initial-state kind {kind!r}")  # pragma: no cover


def encode_initial_state(value: Mapping[str, Mapping[str, object]]) -> dict:
    encoded = {}
    for side in ("first", "second"):
        overrides = _mapping(value.get(side, {}), "<case>", f"initial_state.{side}")
        encoded[side] = {}
        for name, override in overrides.items():
            if name not in _INITIAL_STATE_KINDS:
                raise CompiledCaseError("<case>", f"initial_state.{side}.{name}", "unknown field")
            encoded[side][name] = _encode_initial_value(name, override)
    if set(value) - {"first", "second"}:
        raise CompiledCaseError("<case>", "initial_state", "expected first/second only")
    return encoded


def decode_initial_state(raw: object, case_key: str = "<value>", field: str = "initial_state") -> dict:
    data = _mapping(raw, case_key, field)
    _exact_keys(data, frozenset({"first", "second"}), case_key, field)
    decoded = {}
    for side in ("first", "second"):
        overrides = _mapping(data[side], case_key, f"{field}.{side}")
        decoded[side] = {}
        for name, value in overrides.items():
            if name not in _INITIAL_STATE_KINDS:
                _fail(case_key, f"{field}.{side}.{name}", "unknown FighterState field")
            decoded[side][name] = _decode_initial_value(
                name, value, case_key, f"{field}.{side}.{name}"
            )
    return decoded


# -- case document ---------------------------------------------------------

def encode_origin(value: CaseOrigin) -> dict:
    if not isinstance(value, CaseOrigin):
        raise CompiledCaseError("<value>", "origin", "expected CaseOrigin")
    if value.kind not in _ORIGIN_KINDS:
        raise CompiledCaseError("<value>", "origin.kind", f"unknown kind {value.kind!r}")
    return {
        "kind": value.kind,
        "node_id": value.node_id,
        "path": value.path,
        "sha256": value.sha256,
    }


def decode_origin(raw: object, case_key: str = "<value>", field: str = "origin") -> CaseOrigin:
    data = _mapping(raw, case_key, field)
    _exact_keys(data, frozenset({"kind", "node_id", "path", "sha256"}), case_key, field)
    kind = _text(data["kind"], case_key, f"{field}.kind")
    if kind not in _ORIGIN_KINDS:
        _fail(case_key, f"{field}.kind", f"unknown kind {kind!r}")
    return CaseOrigin(
        kind=kind,
        node_id=_text(data["node_id"], case_key, f"{field}.node_id"),
        path=_relative_path(data["path"], case_key, f"{field}.path"),
        sha256=_hex_digest(data["sha256"], case_key, f"{field}.sha256"),
    )


#: Round budget is required; the sample fields are optional so a scenario
#: entry need not freeze execution metadata it no longer owns.
_LIMIT_FIELDS = frozenset({"simulations", "seed", "batch_size", "maximum_rounds"})


def _decode_limits(raw: object, case_key: str, field: str) -> CaseLimits:
    data = _mapping(raw, case_key, field)
    unknown = sorted(set(data) - _LIMIT_FIELDS)
    if unknown:
        _fail(case_key, field, "unknown field(s): " + ", ".join(unknown))
    if "maximum_rounds" not in data:
        _fail(case_key, field, "expected maximum_rounds")

    def optional(name: str, *, minimum: int | None = None) -> int | None:
        if name not in data:
            return None
        return _integer(data[name], case_key, f"{field}.{name}", minimum=minimum)

    return CaseLimits(
        simulations=optional("simulations", minimum=1),
        seed=optional("seed"),
        batch_size=optional("batch_size", minimum=1),
        maximum_rounds=_integer(
            data["maximum_rounds"], case_key, f"{field}.maximum_rounds", minimum=1
        ),
    )


def encode_limits(value: CaseLimits) -> dict:
    if not isinstance(value, CaseLimits):
        raise CompiledCaseError("<value>", "limits", "expected CaseLimits")
    encoded = {"maximum_rounds": value.maximum_rounds}
    for name in ("simulations", "seed", "batch_size"):
        item = getattr(value, name)
        if item is not None:
            encoded[name] = item
    return encoded


def _encode_dice(values) -> list[dict]:
    return [
        {
            "key": _entry["key"],
            "sides": _entry["sides"],
            "value": _entry["value"],
        }
        for _entry in values
    ]


def _encode_decisions(values) -> list[dict]:
    return [{"key": _entry["key"], "value": _entry["value"]} for _entry in values]


def _decode_dice(raw, case_key: str, field: str) -> tuple[dict, ...]:
    decoded = []
    for index, entry in enumerate(_sequence(raw, case_key, field)):
        data = _mapping(entry, case_key, f"{field}[{index}]")
        _exact_keys(data, frozenset({"key", "sides", "value"}), case_key, f"{field}[{index}]")
        sides = _integer(data["sides"], case_key, f"{field}[{index}].sides", minimum=1)
        value = _integer(data["value"], case_key, f"{field}[{index}].value", minimum=1)
        if value > sides:
            _fail(case_key, f"{field}[{index}].value", "die value exceeds its sides")
        decoded.append({
            "key": _text(data["key"], case_key, f"{field}[{index}].key"),
            "sides": sides,
            "value": value,
        })
    return tuple(decoded)


def _decode_decisions(raw, case_key: str, field: str) -> tuple[dict, ...]:
    decoded = []
    for index, entry in enumerate(_sequence(raw, case_key, field)):
        data = _mapping(entry, case_key, f"{field}[{index}]")
        _exact_keys(data, frozenset({"key", "value"}), case_key, f"{field}[{index}]")
        decoded.append({
            "key": _text(data["key"], case_key, f"{field}[{index}].key"),
            "value": _boolean(data["value"], case_key, f"{field}[{index}].value"),
        })
    return tuple(decoded)


def _decode_benchmark(raw, case_key: str, field: str) -> Mapping | None:
    if raw is None:
        return None
    data = _mapping(raw, case_key, field)
    allowed = frozenset({"warmups", "repeats", "sizes", "simulations", "batch_size"})
    unknown = sorted(set(data) - allowed)
    if unknown:
        _fail(case_key, field, "unknown field(s): " + ", ".join(unknown))
    decoded = {}
    if "warmups" in data:
        decoded["warmups"] = _integer(data["warmups"], case_key, f"{field}.warmups", minimum=0)
    if "repeats" in data:
        decoded["repeats"] = _integer(data["repeats"], case_key, f"{field}.repeats", minimum=1)
    if "simulations" in data:
        decoded["simulations"] = _integer(
            data["simulations"], case_key, f"{field}.simulations", minimum=1
        )
    if "batch_size" in data:
        decoded["batch_size"] = _integer(
            data["batch_size"], case_key, f"{field}.batch_size", minimum=1
        )
    if "sizes" in data:
        decoded["sizes"] = [
            _integer(entry, case_key, f"{field}.sizes[{index}]", minimum=1)
            for index, entry in enumerate(_sequence(data["sizes"], case_key, f"{field}.sizes"))
        ]
    return decoded


def _decode_expectations(raw, case_key: str, field: str) -> Mapping | None:
    if raw is None:
        return None
    data = _mapping(raw, case_key, field)
    unknown = sorted(set(data) - _EXPECTATION_FIELDS)
    if unknown:
        _fail(case_key, field, "unknown expectation channel(s): " + ", ".join(unknown))
    decoded = dict(data)
    for name, value in data.items():
        location = f"{field}.{name}"
        if name == "expect_error":
            _text(value, case_key, location)
        elif name == "expect_events":
            _sequence(value, case_key, location)
        else:
            checkpoints = _mapping(value, case_key, location)
            if name == "expect_rounds":
                # JSON object keys are strings; the E2E runner addresses rounds
                # by integer index, so the reviewed checkpoint map keeps ints.
                decoded[name] = {
                    int(key) if key.isdigit() else key: checkpoint
                    for key, checkpoint in checkpoints.items()
                    if _text(key, case_key, location + ".key")
                }
    return decoded


def _encode_expectations(value) -> Mapping | None:
    return None if value is None else dict(value)


def _case_body(case: CompiledCase) -> dict:
    return {
        "case_key": case.case_key,
        "origin": encode_origin(case.origin),
        "fighters": {
            "first": encode_compiled_fighter(case.first),
            "second": encode_compiled_fighter(case.second),
        },
        "context": None if case.context is None else encode_duel_context(case.context),
        "auxiliary_participants": [
            encode_local_participant(item) for item in case.auxiliary_participants
        ],
        "initial_state": encode_initial_state(case.initial_state),
        "determinism": {
            "dice": _encode_dice(case.dice),
            "decisions": _encode_decisions(case.decisions),
        },
        "limits": encode_limits(case.limits),
        "benchmark": None if case.benchmark is None else dict(case.benchmark),
        "expectations": _encode_expectations(case.expectations),
    }


def _inputs_payload(body: Mapping) -> dict:
    return {
        "fighters": body["fighters"],
        "context": body["context"],
        "auxiliary_participants": body["auxiliary_participants"],
        "initial_state": body["initial_state"],
        "determinism": body["determinism"],
        "limits": body["limits"],
        "benchmark": body["benchmark"],
    }


def _case_fingerprints(body: Mapping) -> dict[str, str]:
    inputs = _inputs_payload(body)
    case_payload = {**inputs, "expectations": body["expectations"]}
    return {
        "inputs_sha256": _sha256(inputs),
        "case_sha256": _sha256(case_payload),
    }


def encode_case(case: CompiledCase) -> dict:
    body = _case_body(case)
    return {**body, "fingerprints": _case_fingerprints(body)}


def decode_case(raw: object, document_key: str = "<document>") -> CompiledCase:
    data = _mapping(raw, document_key, "case")
    _exact_keys(data, _CASE_FIELDS, document_key, "case")
    case_key = _text(data["case_key"], document_key, "case.case_key")
    fighters = _mapping(data["fighters"], case_key, "fighters")
    _exact_keys(fighters, frozenset({"first", "second"}), case_key, "fighters")
    determinism = _mapping(data["determinism"], case_key, "determinism")
    _exact_keys(determinism, frozenset({"dice", "decisions"}), case_key, "determinism")
    fingerprints = _mapping(data["fingerprints"], case_key, "fingerprints")
    _exact_keys(
        fingerprints, frozenset({"inputs_sha256", "case_sha256"}),
        case_key, "fingerprints",
    )
    decoded = CompiledCase(
        case_key=case_key,
        origin=decode_origin(data["origin"], case_key, "origin"),
        first=decode_compiled_fighter(fighters["first"], case_key, "fighters.first"),
        second=decode_compiled_fighter(fighters["second"], case_key, "fighters.second"),
        context=(
            None if data["context"] is None
            else decode_duel_context(data["context"], case_key, "context")
        ),
        auxiliary_participants=tuple(
            decode_local_participant(entry, case_key, f"auxiliary_participants[{index}]")
            for index, entry in enumerate(
                _sequence(data["auxiliary_participants"], case_key, "auxiliary_participants")
            )
        ),
        initial_state=decode_initial_state(data["initial_state"], case_key, "initial_state"),
        dice=_decode_dice(determinism["dice"], case_key, "determinism.dice"),
        decisions=_decode_decisions(determinism["decisions"], case_key, "determinism.decisions"),
        limits=_decode_limits(data["limits"], case_key, "limits"),
        benchmark=_decode_benchmark(data["benchmark"], case_key, "benchmark"),
        expectations=_decode_expectations(data["expectations"], case_key, "expectations"),
        fingerprints={
            "inputs_sha256": _hex_digest(fingerprints["inputs_sha256"], case_key, "fingerprints.inputs_sha256"),
            "case_sha256": _hex_digest(fingerprints["case_sha256"], case_key, "fingerprints.case_sha256"),
        },
    )
    expected = _case_fingerprints(_case_body(decoded))
    if decoded.fingerprints != expected:
        _fail(case_key, "fingerprints", "stored fingerprints do not match the case")
    return decoded


def _validate_source(raw: object) -> dict:
    data = _mapping(raw, "<document>", "source")
    _exact_keys(data, frozenset({"revision", "kb_root", "files"}), "<document>", "source")
    files = []
    for index, entry in enumerate(_sequence(data["files"], "<document>", "source.files")):
        item = _mapping(entry, "<document>", f"source.files[{index}]")
        _exact_keys(item, frozenset({"path", "sha256"}), "<document>", f"source.files[{index}]")
        files.append({
            "path": _relative_path(item["path"], "<document>", f"source.files[{index}].path"),
            "sha256": _hex_digest(item["sha256"], "<document>", f"source.files[{index}].sha256"),
        })
    return {
        "revision": _text(data["revision"], "<document>", "source.revision"),
        "kb_root": _relative_path(data["kb_root"], "<document>", "source.kb_root"),
        "files": files,
    }


def _validate_generator(raw: object) -> dict:
    data = _mapping(raw, "<document>", "generator")
    _exact_keys(data, frozenset({"name", "version"}), "<document>", "generator")
    return {
        "name": _text(data["name"], "<document>", "generator.name"),
        "version": _integer(data["version"], "<document>", "generator.version", minimum=1),
    }


def _document_fingerprints(cases: list[dict]) -> dict[str, str]:
    entries = [
        {"case_key": case["case_key"], "case_sha256": case["fingerprints"]["case_sha256"]}
        for case in sorted(cases, key=lambda item: item["case_key"])
    ]
    return {
        "cases_sha256": _sha256(entries),
        "corpus_sha256": _sha256({
            "schema": SCHEMA,
            "schema_version": SCHEMA_VERSION,
            "cases": entries,
        }),
    }


def encode_document(cases, *, source: Mapping, generator: Mapping) -> dict:
    """Build the canonical document, including every fingerprint."""
    encoded_cases = sorted(
        (encode_case(case) for case in cases), key=lambda item: item["case_key"]
    )
    keys = [case["case_key"] for case in encoded_cases]
    if len(keys) != len(set(keys)):
        raise CompiledCaseError("<document>", "cases", "duplicate case_key")
    return {
        "schema": SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "generator": _validate_generator(generator),
        "source": _validate_source(source),
        "cases": encoded_cases,
        "fingerprints": _document_fingerprints(encoded_cases),
    }


def load_cases(path) -> dict[str, CompiledCase]:
    """Load and validate a corpus document.  Never compiles or consults the KB."""
    location = Path(path)
    try:
        text = location.read_text(encoding="utf-8")
    except OSError as error:
        raise CompiledCaseError("<document>", "path", f"cannot read {location}: {error}") from error
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise CompiledCaseError("<document>", "json", str(error)) from error
    data = _mapping(raw, "<document>", "document")
    _exact_keys(data, _DOCUMENT_FIELDS, "<document>", "document")
    if data["schema"] != SCHEMA:
        _fail("<document>", "schema", f"expected {SCHEMA!r}")
    if data["schema_version"] != SCHEMA_VERSION:
        _fail("<document>", "schema_version", f"expected {SCHEMA_VERSION}")
    _validate_generator(data["generator"])
    _validate_source(data["source"])
    raw_cases = _sequence(data["cases"], "<document>", "cases")
    decoded: dict[str, CompiledCase] = {}
    for index, entry in enumerate(raw_cases):
        case = decode_case(entry, "<document>")
        if case.case_key in decoded:
            _fail(case.case_key, "case_key", "duplicate case_key")
        decoded[case.case_key] = case
    encoded = [encode_case(case) for case in decoded.values()]
    expected = _document_fingerprints(encoded)
    fingerprints = _mapping(data["fingerprints"], "<document>", "fingerprints")
    _exact_keys(
        fingerprints, frozenset({"cases_sha256", "corpus_sha256"}),
        "<document>", "fingerprints",
    )
    if fingerprints != expected:
        _fail("<document>", "fingerprints", "stored document fingerprints do not match the cases")
    return decoded
