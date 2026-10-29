"""Battery catalogue integrity: profiles, references and case invariants.

No duel is executed and no engine is imported: these checks protect the
catalogue's own coherence — cumulative profiles, admitted clause keys and
origins, positive-control pairs, and the magnitude/input-limit contracts the
runner relies on.
"""
from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from tests.engines.fixtures.battery_catalogue import (
    OUTCOMES,
    PROFILE_LEVELS,
    STATISTICAL_MAGNITUDES,
    VARIANTS,
    BatteryCase,
    battery_cases,
    case_magnitudes,
    input_limit,
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


def test_profiles_are_cumulative_and_represent_their_required_variants():
    quick = battery_cases("quick")
    complete = battery_cases("complete")
    deep = battery_cases("deep")
    assert {case.id for case in quick} <= {case.id for case in complete}
    assert {case.id for case in complete} <= {case.id for case in deep}
    for level, cases in (("quick", quick), ("complete", complete)):
        # A secondary label never grants coverage: only the case's own variant counts.
        covered = {case.variant for case in cases}
        assert set(required_variants(level)) <= covered, level
    for case in deep:
        assert case.level in PROFILE_LEVELS
        assert case.variant in VARIANTS
        assert "winner" in case.observables


def test_catalogue_references_are_valid():
    validate_cases()
    validate_keys(battery_cases("deep"), _admitted_keys())
    validate_origins(battery_cases("deep"))


def test_validation_rejects_incoherent_cases():
    parry = _case("q04-parry-attempt")
    validate_cases((replace(parry, observables=("winner",)),), require_coverage=False)
    with pytest.raises(ValueError):
        validate_cases(
            (replace(parry, observables=("winner", "invented")),),
            require_coverage=False,
        )
    with pytest.raises(ValueError):
        validate_cases(
            (replace(parry, observables=("rounds",)),), require_coverage=False,
        )
    first_relic = _case("v14-relic-first")
    with pytest.raises(ValueError):
        validate_cases((replace(first_relic, also_covers=("B14.3",)),),
                       require_coverage=False)
    reroll = _case("c04-parry-reroll")
    with pytest.raises(ValueError):
        validate_cases((replace(reroll, witness="invented-witness"),),
                       require_coverage=False)


def test_absence_cases_have_a_positive_control_of_the_same_variant():
    for case in battery_cases("deep"):
        if case.expect != "absent":
            assert case.positive_control is None
            continue
        control = _case(case.positive_control)
        assert control.variant == case.variant
        assert control.expect == "present"
        assert control.id != case.id


def test_statistical_magnitudes_always_include_the_winner():
    """The comparison is terminal outcomes, never a witness name."""
    assert STATISTICAL_MAGNITUDES[0] == "winner"
    assert set(STATISTICAL_MAGNITUDES) <= set(OUTCOMES)
    parry = _case("q04-parry-attempt")
    assert case_magnitudes(parry) == ("winner", "rounds", "wounds", "condition")
    # A witness declared as an observable is ignored, not turned into a gate.
    only_witness = replace(
        parry, observables=("parry-attempts", "wounds", "winner"),
    )
    assert case_magnitudes(only_witness) == ("winner", "wounds")
    assert case_magnitudes(
        replace(parry, observables=("winner", "winner", "rounds")),
    ) == ("winner", "rounds")


def test_input_limit_keeps_only_real_limits():
    """A witness or consumer tag no longer blocks a statistical sample."""
    parry = _case("q04-parry-attempt")
    assert parry.blocked_by is None
    assert parry.decision_scope == "uniform"
    assert input_limit(parry) is None
    assert input_limit(replace(parry, blocked_by="witness:G06")) is None
    assert input_limit(replace(parry, blocked_by="consume:G05")) is None
    assert input_limit(replace(parry, blocked_by="state:G00/G02")) == "state:G00/G02"
    assert input_limit(replace(parry, blocked_by="decision:G02")) == "decision:G02"
    assert input_limit(replace(parry, decision_scope="per-row")) == "decision:per-row"
