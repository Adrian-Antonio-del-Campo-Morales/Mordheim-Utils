"""P01 battery catalog: variants, witnesses, membership and case invariants.

No duel is executed here: these checks are structural preparation evidence.
"""
from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from mordheim_combat_lab.verification.parity._battery_cases import (
    OBLIGATIONS,
    OUTCOMES,
    PROFILE_LEVELS,
    VARIANT_KEYS,
    VARIANTS,
    WITNESSES,
    BatteryCase,
    ContextSpec,
    battery_cases,
    required_variants,
    validate_cases,
    validate_keys,
    validate_origins,
)

ROOT = Path(__file__).resolve().parents[3]


def _admitted_keys() -> set[str]:
    with (ROOT / "sources/knowledge/verification/clause-contracts.csv").open(
        encoding="utf-8", newline="",
    ) as handle:
        return {
            f"{row['id']}::{row['clause_id']}"
            for row in csv.DictReader(handle)
            if row["clause_scope"] == "YES"
        }


def _case(case_id: str) -> BatteryCase:
    return next(case for case in battery_cases("deep") if case.id == case_id)


@pytest.mark.phase5_vectorized
def test_catalog_has_the_transferred_variants_and_exact_membership():
    assert len(VARIANTS) == 63
    assert {variant.id for variant in VARIANTS.values()} == set(VARIANT_KEYS)
    assert sum(len(keys) for keys in VARIANT_KEYS.values()) == 1914
    duel = [variant for variant in VARIANTS.values() if variant.case_kind == "duel"]
    assert len(duel) == 60
    assert {variant.id for variant in duel} == set(required_variants("complete"))
    assert {variant.id: variant.case_kind for variant in VARIANTS.values()} == {
        **{variant.id: "duel" for variant in duel},
        "B00.1": "structural",
        "B09.1": "structural",
        "B99.1": "unlocated",
    }
    assert all(variant.required for variant in VARIANTS.values())  # A8
    assert set(OBLIGATIONS) == {variant.id.split(".")[0] for variant in VARIANTS.values()}


@pytest.mark.phase5_vectorized
def test_profiles_are_cumulative_and_represent_their_required_variants():
    quick = battery_cases("quick")
    complete = battery_cases("complete")
    deep = battery_cases("deep")
    assert {case.id for case in quick} <= {case.id for case in complete}
    assert {case.id for case in complete} <= {case.id for case in deep}
    assert required_variants("quick") == tuple(
        variant.id for variant in VARIANTS.values()
        if variant.case_kind == "duel" and variant.level == "quick"
    )
    for level, cases in (("quick", quick), ("complete", complete)):
        covered = {case.variant for case in cases} | {
            secondary for case in cases for secondary in case.also_covers
        }
        assert set(required_variants(level)) <= covered, level
    for case in deep:
        assert case.level in PROFILE_LEVELS
        assert case.variant in VARIANTS
        assert case.observables and set(case.observables)
        assert "winner" in case.observables
        assert case.origin.startswith(("e2e:", "spec:", "new:"))


@pytest.mark.phase5_vectorized
def test_witness_types_follow_the_typed_contract():
    for name, witness in WITNESSES.items():
        assert witness.name == name
        assert witness.kind in {"counter", "flag", "category", "direct-result", "hash"}
        assert witness.present != witness.absent
    for variant in VARIANTS.values():
        if variant.witness is None:
            continue
        if variant.witness.name in {"condition", "wounds"}:
            assert variant.witness.kind == "direct-result"
            assert variant.id.startswith(("B07.", "B15.")), variant.id
        if variant.witness.kind == "direct-result":
            assert variant.id.startswith(("B07.", "B11.", "B14.", "B15.")), variant.id
        if variant.witness.kind == "category":
            assert variant.witness.name == "acting-order"
        if variant.witness.kind == "hash":
            assert variant.witness.name == "equipment"


@pytest.mark.phase5_vectorized
def test_case_invariants_and_materialized_preparations():
    validate_cases()
    validate_keys(battery_cases("deep"), _admitted_keys())
    validate_origins(battery_cases("deep"))

    assert all(case.witness_value is not None for case in battery_cases("deep")
               if VARIANTS[case.variant].witness is not None
               and VARIANTS[case.variant].witness.kind in {
                   "category", "direct-result", "hash"})
    for forbidden in ("keys", "activation", "support", "support_distance", "family"):
        assert forbidden not in BatteryCase.__dataclass_fields__

    natural = _case("q04-natural-armour-six")
    assert natural.second.band_id == "beastmen-raiders"
    assert "trait.natural-armour-save" in natural.second.special_rule_ids
    assert natural.second.armour_id == "armour.no-armour"

    fire = _case("q05-flammable-fire")
    assert fire.first.main_weapon_id == "weapon.brazier-iron"
    assert "trait.flammable" in fire.second.special_rule_ids

    hunger = _case("q11-black-hunger")
    assert "mechanic.black-hunger" in hunger.first.skill_ids

    leader = _case("q10-leader-six")
    assert isinstance(leader.context, ContextSpec)
    assert leader.context.distances == (("first", "leader", 6),)
    assert leader.context.nearby[0].participant_id == "leader"

    parry = _case("c04-parry-reroll")
    assert "defence.buckler" in parry.second.defence_ids

    highest = _case("c04-highest-injury")
    assert highest.origin.endswith("highest-injury-result-applies")

    reroll = _case("c04-parry-reroll")
    assert not hasattr(reroll.second, "off_weapon_id")
    assert hasattr(reroll.second, "off_hand_id")


@pytest.mark.phase5_vectorized
def test_absence_cases_have_a_positive_control_of_the_same_variant():
    for case in battery_cases("deep"):
        if case.expect != "absent":
            assert case.positive_control is None
            continue
        control = _case(case.positive_control)
        assert control.variant == case.variant
        assert control.expect == "present"
        assert control.id != case.id
    absences = [case for case in battery_cases("deep") if case.expect == "absent"]
    assert {case.variant for case in absences} == {"B14.1", "B14.11", "B11.4"}


@pytest.mark.phase5_vectorized
def test_focused_pairs_follow_a10_without_a_control_on_the_positive():
    positive = _case("v10-priority")
    positive = replace(
        positive, id="a10-focus-positive", variant=positive.variant,
        comparison="focused", focused="winner:1", positive_control=None,
        expect="present",
    )
    negative = replace(
        positive, id="a10-focus-negative", expect="absent",
        positive_control=positive.id,
    )
    validate_cases((positive, negative), require_coverage=False)
    # A10: the positive carries no control; only the negative references it.
    assert positive.positive_control is None and negative.positive_control == positive.id
    with pytest.raises(ValueError):
        validate_cases((positive, replace(negative, focused="winner:2")),
                       require_coverage=False)


@pytest.mark.phase5_vectorized
def test_blocked_cases_keep_their_variant_and_dependency():
    blocked = [case for case in battery_cases("deep") if case.blocked_by]
    assert blocked
    assert all(case.blocked_by.startswith(
        ("state:", "consume:", "witness:", "decision:")) for case in blocked)
    assert all(case.variant in VARIANTS for case in blocked)
    assert all(not case.blocked_by.startswith("state:") or case.context is not None
               or case.requires for case in blocked)
