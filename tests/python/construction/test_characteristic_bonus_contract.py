"""T13.2a -- characteristic bonus contract of the combat compiler.

These cases pin how ``stat_bonuses`` are built and applied.  A binding may only
target the canonical characteristics, and a bonus must be an integer:
booleans, decimals and strings are refused instead of silently coerced.  A
nonzero bonus to an unknown optional characteristic (``movement`` or
``leadership``) is refused rather than inventing a base value, while a zero
bonus keeps it unknown.

The compiler paths run through isolated fabricated bindings and isolated
``Characteristics`` values; no knowledge-base file is edited.  The real
Middenheim and Mark of Onogal bonuses are re-checked at the end.
"""
from __future__ import annotations

import pytest

from mordheim_construction import compiler as compiler_module
from mordheim_construction.compiler import (
    _apply_characteristic_bonuses,
    _characteristic_bonus_block,
    compile_fighter,
)
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


#: Real selectable, executable rules used as hosts for fabricated bindings.
HOST_RULE = "warpstone-troll--vomit-attack"
MIDDENHEIM = "band--middenheim-physical-prowess"
NORSE_BERSERK_CHARGE = "band--norse-special-skills-berserk-charge"
#: Real "compiler"-bound rules whose SPECIAL_RULE_EFFECTS entry carries stats.
BLOATED_FOULNESS = "band--blessings-of-nurgle-bloated-foulness"
MARK_OF_NURGLE = "band--blessings-of-nurgle-mark-of-nurgle"

CANONICAL_KEYS = (
    "weapon_skill", "strength", "toughness", "wounds",
    "initiative", "attacks", "movement", "leadership",
)


def _fabricate_bindings(monkeypatch, rule_id, bindings):
    """Replace one rule's executable bindings and delegate for every other rule."""
    real = compiler_module.runtime_bindings

    def fake(rule, kind=None, **kwargs):
        if str(rule.get("id")) == rule_id:
            return tuple(
                binding for binding in bindings
                if kind is None or binding.get("kind") == kind
            )
        return real(rule, kind, **kwargs)

    monkeypatch.setattr(compiler_module, "runtime_bindings", fake)


def _characteristic_binding(bonuses, profile_ids=None):
    parameters = {"bonuses": bonuses}
    if profile_ids is not None:
        parameters["profile_ids"] = list(profile_ids)
    return {"kind": "profile", "id": "profile.characteristics", "parameters": parameters}


def _free_build(**optional):
    """A free-selection build whose characteristics come from the caller."""
    return FighterBuild(
        "mordheim",
        characteristics=Characteristics(5, 3, 3, 1, 4, 1, **optional),
        special_rule_ids=(HOST_RULE,),
    )


@pytest.mark.parametrize("key", CANONICAL_KEYS)
def test_every_canonical_characteristic_accepts_signed_integer_bonuses(key):
    assert _characteristic_bonus_block({key: 1}, source="case") == {key: 1}
    assert _characteristic_bonus_block({key: -2}, source="case") == {key: -2}
    assert _characteristic_bonus_block({key: 0}, source="case") == {key: 0}


@pytest.mark.parametrize("key", ["ballistic_skill", "M", "Strength", "", 3])
def test_unknown_characteristic_keys_are_rejected(key):
    with pytest.raises(ValueError, match="unknown characteristic bonus"):
        _characteristic_bonus_block({key: 1}, source="case")


@pytest.mark.parametrize("value", [True, False, 1.5, -0.5, "1", "1.0", None, [1]])
def test_non_integer_bonuses_are_rejected_without_conversion(value):
    with pytest.raises(ValueError, match="non-integer strength bonus"):
        _characteristic_bonus_block({"strength": value}, source="case")


def test_zero_bonus_keeps_an_unknown_optional_characteristic():
    unknown = Characteristics(5, 3, 3, 1, 4, 1)
    assert _apply_characteristic_bonuses(unknown, {"movement": 0, "leadership": 0}) == unknown


def test_nonzero_bonus_to_an_unknown_optional_characteristic_is_refused():
    unknown = Characteristics(5, 3, 3, 1, 4, 1)
    with pytest.raises(ValueError, match="no known base movement"):
        _apply_characteristic_bonuses(unknown, {"movement": 1})
    with pytest.raises(ValueError, match="no known base leadership"):
        _apply_characteristic_bonuses(unknown, {"leadership": -1})


def test_known_optional_characteristics_accumulate_signed_bonuses():
    known = Characteristics(5, 3, 3, 1, 4, 1, movement=4, leadership=8)
    applied = _apply_characteristic_bonuses(known, {"movement": 2, "leadership": -1})
    assert (applied.movement, applied.leadership) == (6, 7)


def test_compiled_profile_applies_and_accumulates_valid_bonuses(monkeypatch):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"strength": 1, "toughness": -1, "wounds": 0, "initiative": 2}),
        _characteristic_binding({"strength": 1, "movement": 1, "leadership": -1}),
    ])
    compiled = compile_fighter(_free_build(movement=5, leadership=8))
    assert compiled.characteristics == Characteristics(
        5, 5, 2, 1, 6, 1, movement=6, leadership=7,
    )


def test_compiler_rejects_an_unknown_characteristic_key(monkeypatch):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"ballistic_skill": 1}),
    ])
    with pytest.raises(ValueError, match="unknown characteristic bonus 'ballistic_skill'"):
        compile_fighter(_free_build())


@pytest.mark.parametrize("value", [True, 1.5, "1"])
def test_compiler_rejects_non_integer_bonuses(monkeypatch, value):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"strength": value}),
    ])
    with pytest.raises(ValueError, match="non-integer strength bonus"):
        compile_fighter(_free_build())


def test_compiler_requires_a_known_base_for_a_nonzero_optional_bonus(monkeypatch):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"movement": 1}),
    ])
    with pytest.raises(ValueError, match="no known base movement"):
        compile_fighter(_free_build())
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"leadership": 1}),
    ])
    with pytest.raises(ValueError, match="no known base leadership"):
        compile_fighter(_free_build())


def test_zero_bonus_to_an_unknown_optional_characteristic_stays_unknown(monkeypatch):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"movement": 0, "leadership": 0}),
    ])
    compiled = compile_fighter(_free_build())
    assert compiled.characteristics.movement is None
    assert compiled.characteristics.leadership is None


def test_canceling_valid_contributions_keep_unknown_optional_bases(monkeypatch):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"movement": 1, "leadership": -1}),
        _characteristic_binding({"movement": -1, "leadership": 1}),
    ])
    compiled = compile_fighter(_free_build())
    assert compiled.characteristics.movement is None
    assert compiled.characteristics.leadership is None


def test_recipient_filter_does_not_impose_an_optional_requirement(monkeypatch):
    _fabricate_bindings(monkeypatch, HOST_RULE, [
        _characteristic_binding({"movement": 1}, profile_ids=("mercenary-captain",)),
    ])
    compiled = compile_fighter(_free_build())
    assert compiled.characteristics.movement is None


def test_recipient_filter_still_applies_to_the_matching_profile(monkeypatch):
    plain = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
    ))
    _fabricate_bindings(monkeypatch, MIDDENHEIM, [
        _characteristic_binding({"movement": 1, "strength": 1}, profile_ids=("mercenary-captain",)),
    ])
    compiled = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
        special_rule_ids=(MIDDENHEIM,),
    ))
    assert compiled.characteristics.movement == plain.characteristics.movement + 1
    assert compiled.characteristics.strength == plain.characteristics.strength + 1


def _tainted_one(rule_id):
    return FighterBuild(
        "mordheim", band_id="carnival-of-chaos", profile_id="tainted-ones",
        special_rule_ids=(rule_id,),
    )


def test_special_rule_effect_stats_apply_valid_bonuses():
    # Two real Blessings of Nurgle: one grants Toughness and Wounds, the other
    # only Wounds.  Their difference isolates the compiled stats contract.
    bloated = compile_fighter(_tainted_one(BLOATED_FOULNESS))
    marked = compile_fighter(_tainted_one(MARK_OF_NURGLE))
    assert bloated.characteristics.toughness == marked.characteristics.toughness + 1
    assert bloated.characteristics.wounds == marked.characteristics.wounds


@pytest.mark.parametrize("stats,message", [
    ({"ballistic_skill": 1}, "unknown characteristic bonus"),
    ({"strength": 1.5}, "non-integer strength bonus"),
    ({"strength": True}, "non-integer strength bonus"),
])
def test_special_rule_effect_stats_are_validated(monkeypatch, stats, message):
    monkeypatch.setitem(
        compiler_module.SPECIAL_RULE_EFFECTS, BLOATED_FOULNESS, {"stats": stats},
    )
    with pytest.raises(ValueError, match=message):
        compile_fighter(_tainted_one(BLOATED_FOULNESS))


def test_special_rule_effect_stats_require_a_known_base(monkeypatch):
    monkeypatch.setitem(
        compiler_module.SPECIAL_RULE_EFFECTS, NORSE_BERSERK_CHARGE, {"stats": {"movement": 1}},
    )
    with pytest.raises(ValueError, match="no known base movement"):
        compile_fighter(FighterBuild(
            "mordheim",
            characteristics=Characteristics(5, 3, 3, 1, 4, 1),
            special_rule_ids=(NORSE_BERSERK_CHARGE,),
        ))


def test_real_middenheim_and_mark_of_onogal_bonuses_are_preserved():
    ordinary = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
    ))
    middenheimer = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
        special_rule_ids=(MIDDENHEIM,),
    ))
    assert middenheimer.characteristics.strength == ordinary.characteristics.strength + 1

    unmarked = compile_fighter(FighterBuild(
        "mordheim", band_id="marauders-of-chaos", profile_id="marauder-chieftain",
    ))
    marked = compile_fighter(FighterBuild(
        "mordheim", band_id="marauders-of-chaos", profile_id="marauder-chieftain",
        special_rule_ids=("band--mark-of-onogal",),
    ))
    assert marked.characteristics.toughness == unmarked.characteristics.toughness + 1
