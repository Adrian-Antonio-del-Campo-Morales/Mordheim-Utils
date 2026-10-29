"""T02: round-trip and rejection proofs for the precompiled-case codec."""
from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import fields
import json
from pathlib import Path

import pytest

from mordheim_core.models import CarriedEquipment
from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelContext
from mordheim_core.models import EffectSet
from mordheim_core.models import LocalParticipant
from mordheim_core.models import MutationOption
from tools.verification import compiled_cases as codec



SOURCE = {
    "revision": "8415ba80c22d4cf61fddd22473e2ebabe776b58e",
    "kb_root": "sources/knowledge",
    "files": [],
}
GENERATOR = {"name": "export-compiled-cases", "version": 1}


def _fighter(fighter_id: str, **changes) -> CompiledFighter:
    base = {
        "fighter_id": fighter_id,
        "characteristics": Characteristics(3, 3, 3, 2, 5, 1),
        "main_weapon": EffectSet(tags=("weapon.mace",)),
        "off_hand": None,
        "global_effects": EffectSet(),
        "armour_save": 7,
        "helmet_save": 7,
        "natural_armour_save": 7,
    }
    base.update(changes)
    return CompiledFighter(**base)


def _case(**changes) -> codec.CompiledCase:
    first = _fighter("first")
    second = _fighter("second", off_hand=EffectSet(tags=("defence.shield",)))
    base = {
        "case_key": "unit/test/sample",
        "origin": codec.CaseOrigin(
            "unit", "tests/example.py::test_sample", "tests/example.py", "a" * 64,
        ),
        "first": first,
        "second": second,
        "context": DuelContext(charging=(), active_participant="first"),
        "auxiliary_participants": (
            LocalParticipant("ally", "first", first, "standing"),
        ),
        "initial_state": {
            "first": {
                "condition": "KNOCKED_DOWN",
                "resources_spent": frozenset({"lucky-charm", "x"}),
                "random_modifiers": (("S", 1),),
                "hampered_hands": ("main",),
            },
            "second": {},
        },
        "dice": ({"key": "round.0.first.attack.0.hit", "sides": 6, "value": 4},),
        "decisions": ({"key": "round.0.first.attack.0.parry", "value": True},),
        "limits": codec.CaseLimits(1, 0, 100_000, 1),
        "benchmark": None,
        "expectations": {"expect_final": {"rounds_executed": 1}},
    }
    base.update(changes)
    return codec.CompiledCase(**base)


def _document() -> dict:
    return codec.encode_document([_case()], source=SOURCE, generator=GENERATOR)


def _write(path: Path, document: dict) -> Path:
    path.write_text(codec.canonical_json(document), encoding="utf-8")
    return path


def test_compiled_fighter_round_trip_keeps_every_field():
    fighter = _fighter(
        "complex",
        natural_armour_unmodified=True,
        injury_profile=2,
        random_characteristics=(("S", 1, 6, 0), ("I", 2, 3, 1)),
        shield_and_skill_effects=EffectSet(parry=True),
        extra_attacks=(EffectSet(strength_bonus=1),),
        construction_tags=("compiler.hillman-wolf-form",),
        mutation_options=(MutationOption(3, EffectSet(tags=("mutation.x",)), (("self", "S", 1),)),),
        mutation_equipment=(
            CarriedEquipment("weapon.claw", EffectSet(), "weapon", "main", (("S", 1),), None),
        ),
        extra_attacks_without_poison=((EffectSet(), EffectSet(tags=("a",))),),
    )
    encoded = codec.encode_compiled_fighter(fighter)
    assert set(encoded) == {item.name for item in fields(CompiledFighter)}
    assert codec.decode_compiled_fighter(encoded) == fighter


def test_effect_set_is_sparse_and_rejects_unknown_fields():
    effect = EffectSet(strength_bonus=2, tags=("weapon.mace",))
    encoded = codec.encode_effect_set(effect)
    assert encoded == {"strength_bonus": 2, "tags": ["weapon.mace"]}
    assert codec.decode_effect_set(encoded) == effect
    with pytest.raises(codec.CompiledCaseError, match="unknown EffectSet field"):
        codec.decode_effect_set({"not_a_field": 1})


def test_context_distinguishes_null_from_empty_sequences():
    absent = codec.encode_duel_context(DuelContext())
    empty = codec.encode_duel_context(
        DuelContext(charging=(), active_participant="first")
    )
    assert absent["charging"] is None
    assert absent["contacts"] is None
    assert empty["charging"] == []
    assert codec.decode_duel_context(absent).charging is None
    assert codec.decode_duel_context(empty).charging == ()


def test_initial_state_round_trip_normalizes_sets_tuples_and_conditions():
    case = _case()
    encoded = codec.encode_initial_state(case.initial_state)
    assert encoded["first"]["resources_spent"] == ["lucky-charm", "x"]
    assert encoded["first"]["random_modifiers"] == [["S", 1]]
    assert codec.decode_initial_state(encoded) == case.initial_state


def test_document_round_trip_and_reproducible_bytes(tmp_path):
    case = _case()
    document = codec.encode_document([case], source=SOURCE, generator=GENERATOR)
    path = _write(tmp_path / "compiled-cases.json", document)
    loaded = codec.load_cases(path)
    expected = codec.decode_case(codec.encode_case(case))
    assert list(loaded) == [case.case_key]
    assert loaded[case.case_key] == expected
    assert codec.canonical_json(document) == path.read_text(encoding="utf-8")
    assert codec.encode_document([case], source=SOURCE, generator=GENERATOR) == document


def test_canonical_json_is_sorted_and_compact():
    assert codec.canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_loader_rejects_missing_file(tmp_path):
    with pytest.raises(codec.CompiledCaseError, match="cannot read"):
        codec.load_cases(tmp_path / "absent.json")


def test_loader_rejects_unknown_schema_version(tmp_path):
    document = _document()
    document["schema_version"] = 2
    with pytest.raises(codec.CompiledCaseError, match="schema_version"):
        codec.load_cases(_write(tmp_path / "v2.json", document))


def test_loader_rejects_unknown_fighter_field(tmp_path):
    document = _document()
    document["cases"][0]["fighters"]["first"]["bogus"] = 1
    with pytest.raises(codec.CompiledCaseError, match="unknown field"):
        codec.load_cases(_write(tmp_path / "field.json", document))


def test_loader_rejects_bool_where_an_integer_is_required(tmp_path):
    document = _document()
    document["cases"][0]["fighters"]["first"]["armour_save"] = True
    with pytest.raises(codec.CompiledCaseError, match="expected an integer"):
        codec.load_cases(_write(tmp_path / "bool.json", document))


def test_loader_rejects_tampered_case_fingerprint(tmp_path):
    document = _document()
    document["cases"][0]["expectations"]["expect_final"]["rounds_executed"] = 99
    with pytest.raises(codec.CompiledCaseError, match="fingerprints"):
        codec.load_cases(_write(tmp_path / "tampered.json", document))


def test_loader_rejects_duplicate_case_keys(tmp_path):
    document = _document()
    document["cases"].append(deepcopy(document["cases"][0]))
    with pytest.raises(codec.CompiledCaseError, match="duplicate case_key"):
        codec.load_cases(_write(tmp_path / "duplicate.json", document))


def test_loader_rejects_unknown_document_field(tmp_path):
    document = _document()
    document["generated_at"] = "2026-10-23T00:00:00Z"
    with pytest.raises(codec.CompiledCaseError, match="unknown field"):
        codec.load_cases(_write(tmp_path / "timestamp.json", document))


def test_codec_does_not_import_the_compiler_knowledge_or_engines():
    tree = ast.parse(Path(codec.__file__).read_text(encoding="utf-8"))
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    forbidden = (
        "mordheim_construction",
        "mordheim_knowledge",
        "mordheim_combat",
        "mordheim_modular_e2e",
        "mordheim_combat_lab",
    )
    offenders = [
        name for name in modules
        if any(name == prefix or name.startswith(prefix + ".") for prefix in forbidden)
    ]
    assert offenders == [], offenders
    assert "json" in modules
