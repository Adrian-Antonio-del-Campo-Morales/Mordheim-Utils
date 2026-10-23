"""Battery catalog: variants, membership, magnitudes and case invariants.

No duel is executed here: these checks are structural preparation evidence.
Witness and expectation fields remain declaration data, never a gate.
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
    STATISTICAL_MAGNITUDES,
    VARIANT_KEYS,
    VARIANTS,
    WITNESSES,
    BatteryCase,
    ContextSpec,
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
        # A secondary label never grants coverage: only the case's own variant counts.
        covered = {case.variant for case in cases}
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

    for forbidden in ("keys", "activation", "support", "support_distance", "family"):
        assert forbidden not in BatteryCase.__dataclass_fields__

    parry = _case("q04-parry-attempt")
    assert parry.first.main_weapon_id == "weapon.mace"
    assert parry.second.main_weapon_id == "weapon.sword"
    absent_parry = _case("q04-parry-absent")
    assert absent_parry.participant == "second"
    assert absent_parry.positive_control == "q04-parry-attempt"

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
    assert leader.witness_value == 8
    assert _case("c10-leader-absence").witness_value == 8
    # The leadership arrives through the canonical profile grant: no mechanic
    # id may be supplied as a skill of the provider build.
    assert leader.context.nearby[0].fighter.band_id == "amazons-lustria"
    assert leader.context.nearby[0].fighter.profile_id == "serpent-priestess"
    assert leader.context.nearby[0].fighter.skill_ids == ()
    assert _case("v14-cold-blood").witness_value == 3
    assert _case("v14-modifiers").first.trait_overrides == {"stupidity": True}
    assert "mechanic.enchanting-beauty" in _case("v14-modifiers").second.skill_ids

    revenant = _case("c11-curse-of-revenant")
    assert set(revenant.first.skill_ids) == {
        "mechanic.great-thirster", "mechanic.curse-of-the-revenant",
    }
    guard = _case("c09-beastlash-fear")
    assert guard.second.trait_overrides.get("house_guard_house") == "fierezza"

    poison = _case("v03-poison")
    assert poison.first.main_poison_id == "poison.black-lotus"
    assert poison.decisions["test.lotus-critical"] is False
    immune = _case("v03-poison-immune")
    assert immune.positive_control == "v03-poison"
    assert "trait.poison-immune" in immune.second.special_rule_ids

    regeneration = _case("v05-regeneration")
    assert "skill.regeneration" in regeneration.second.skill_ids
    blocked = _case("v05-regeneration-blocked")
    assert blocked.first.main_weapon_id == "weapon.brazier-iron"
    assert blocked.second.skill_ids == ("skill.regeneration",)
    assert blocked.participant == "second"
    assert blocked.positive_control == "v05-regeneration"

    netted = _case("v09-netted-absent")
    assert netted.second.condition_ids == ()
    assert netted.positive_control == "v09-netted"

    exempt = _case("v12-stupidity-exempt")
    assert "condition.stupidity-exempt" in exempt.first.condition_ids

    parry = _case("c04-parry-reroll")
    assert "defence.buckler" in parry.second.defence_ids

    highest = _case("c04-highest-injury")
    assert highest.origin.endswith("highest-injury-result-applies")

    reroll = _case("c04-parry-reroll")
    assert not hasattr(reroll.second, "off_weapon_id")
    assert hasattr(reroll.second, "off_hand_id")

    resource = _case("v01-force-of-will")
    assert resource.participant == "second"
    assert "mechanic.force-of-will" in resource.second.skill_ids
    assert all(case.participant in {"first", "second", "both"}
               for case in battery_cases("deep"))

    first_relic = _case("v14-relic-first")
    second_relic = _case("v14-relic-second")
    assert first_relic.maximum_rounds == 1
    # _battle() alternates the player turn: the first tests in rounds 0 and 2.
    assert second_relic.maximum_rounds == 3
    assert second_relic.blocked_by is None
    assert second_relic.expect == "absent"

    with pytest.raises(ValueError):
        validate_cases((replace(first_relic, also_covers=("B14.3",)),),
                       require_coverage=False)


@pytest.mark.phase5_vectorized
def test_preparations_use_rule_ids_and_defence_slots_the_compiler_accepts():
    """Static guards for the two defects found in the remaining scenarios."""
    hand_held = {"defence.shield", "defence.buckler", "defence.kite-shield"}
    for case in battery_cases("deep"):
        for build in (case.first, case.second):
            # compiler.py: hand-held defences belong in off_hand_id.
            assert not hand_held.intersection(build.defence_ids), case.id
            if build.band_id:
                # A band/profile build resolves special_rule_ids only against
                # that band's rule ids; trait./mechanic./rule. ids are effects.
                assert not any(
                    identifier.startswith(("trait.", "mechanic.", "rule."))
                    for identifier in build.special_rule_ids
                ), case.id
    honorable = _case("q00-honorable")
    # The bearer is the second participant so its Round 1 pool meets the target
    # still Knocked Down/Stunned: the first participant recovers on its own turn.
    assert honorable.second.main_weapon_id == "weapon.mace"
    assert honorable.participant == "second"
    assert honorable.blocked_by is None
    random = _case("v01-random")
    assert (random.first.band_id, random.first.profile_id) == (
        "marauders-of-chaos", "condemned"
    )
    restriction = _case("v01-restriction")
    assert restriction.context.charging == ()
    hard_head = _case("c04-hard-head")
    assert hard_head.second.trait_overrides == {"concussion_immune": True}
    assert hard_head.blocked_by is None


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
    assert {case.variant for case in absences} == {
        "B01.2", "B02.2", "B02.3", "B02.4", "B03.2", "B03.3", "B03.4",
        "B03.5", "B05.1", "B05.2", "B06.1", "B06.2", "B08.4", "B09.3",
        "B11.2", "B11.3", "B11.4", "B11.5", "B11.6",
        "B12.1", "B14.1", "B14.2", "B14.3", "B14.4", "B14.5", "B14.6",
        "B14.7", "B14.8", "B14.9", "B14.10", "B14.11", "B14.12",
        "B14.13", "B15.1", "B15.4", "B15.5", "B15.6",
    }
    assert len(absences) == 40


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
def test_input_limit_keeps_only_real_limits():
    """A witness or consumer tag no longer blocks a statistical sample."""
    parry = _case("q04-parry-attempt")
    # The retired witness vocabulary no longer appears as a declared block on a
    # statistical case; when present it still never limits execution.
    assert parry.blocked_by is None
    assert input_limit(replace(parry, blocked_by="witness:G06")) is None
    assert input_limit(replace(parry, blocked_by="consume:G05")) is None
    assert parry.decision_scope == "uniform"
    assert input_limit(parry) is None
    assert input_limit(replace(parry, blocked_by="state:G00/G02")) == "state:G00/G02"
    assert input_limit(replace(parry, blocked_by="decision:G02")) == "decision:G02"
    assert input_limit(replace(parry, decision_scope="per-row")) == "decision:per-row"
    # The repaired preparations expose no real limit; the genuinely missing
    # input keeps its cause.
    assert input_limit(_case("q00-honorable")) is None
    assert input_limit(_case("v01-random")) is None
    assert input_limit(_case("c04-hard-head")) is None
    assert input_limit(_case("v14-relic-second")) is None
    potion = _case("c03-petru-potion")
    assert input_limit(potion) == "state:preparation.strength-draught"
    assert potion.blocked_by == "state:preparation.strength-draught"
    # The handler branch is reachable through the canonical Squig rule
    # (leadership.py:170-203), so neither case declares a blocked input.
    handler = _case("v14-handler")
    assert input_limit(handler) is None
    assert handler.blocked_by is None
    assert _case("v14-handler-absent").blocked_by is None
    assert handler.first.profile_id == "cave-squigs"
    assert handler.first.trait_overrides.get("stupidity") is True
    restriction = _case("v01-restriction")
    assert input_limit(restriction) == "state:mechanic.shallya-strictures"
    assert restriction.context.charging == ()


@pytest.mark.phase5_vectorized
def test_validation_accepts_a_case_without_its_variant_witness():
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


@pytest.mark.phase5_vectorized
def test_transferred_e2e_pairs_are_normal_statistical_scenarios():
    """The reused pairs describe different rules, both compared on outcomes."""
    pairs = {
        "v02-hatred": ("v02-hatred-absent",),
        "v03-strength": ("v03-strength-absent",),
        "c05-ethereal-save": ("c05-ethereal-bypass",),
        "c04-parry-reroll": ("c06-two-swords-one-attempt",),
        "v08-unarmed": ("v08-ordinary-fist",),
        "c11-spines": ("c11-spines-absent",),
        "c11-acid-blood": ("c11-acid-blood-absent",),
        "v15-contagious": ("v15-contagious-absent",),
        "v15-torturer": ("v15-torturer-absent",),
        # One positive carries two capacity controls: one where the printed
        # allowance is missing, one where a reroll must not become a new
        # attempt.  Both judge ``parry-attempts`` at two, never ``reroll-used``.
        "c06-two-parries": ("c06-two-swords-capacity", "c06-reroll-capacity"),
    }
    for positive_id, control_ids in pairs.items():
        positive = _case(positive_id)
        for control_id in control_ids:
            control = _case(control_id)
            assert control.variant == positive.variant
            assert control.id != positive.id
            assert positive.origin.startswith(("e2e:", "new:"))
            assert control.origin.startswith(("e2e:", "new:"))
            assert case_magnitudes(positive)[0] == "winner"
            assert case_magnitudes(control)[0] == "winner"
            # Both members are executable scenarios when no real input is missing.
            assert input_limit(positive) is None
            assert input_limit(control) is None

    capacity = _case("c06-two-parries")
    assert capacity.origin.endswith("two-parrying-weapons-give-two-parry-attempts")
    assert _case("c06-two-swords-capacity").origin.endswith(
        "without-the-skill-only-the-first-attack-is-parried"
    )
    reroll_capacity = _case("c06-reroll-capacity")
    assert "defence.buckler" in reroll_capacity.second.defence_ids
    assert reroll_capacity.origin.endswith("a-failed-parry-reroll-consumes-the-phase-attempt")

    reroll = _case("c04-parry-reroll")
    assert "reroll-used" in reroll.observables
    with pytest.raises(ValueError):
        validate_cases((replace(reroll, witness="invented-witness"),),
                       require_coverage=False)


@pytest.mark.phase5_vectorized
def test_blocked_cases_keep_their_variant_and_dependency():
    blocked = [case for case in battery_cases("deep") if case.blocked_by]
    # Only real input limits remain declared: the witness/consume vocabulary is
    # retired from the statistical path and no longer marks a case as blocked.
    assert [case.id for case in blocked] == [
        "c03-petru-potion", "v01-restriction",
    ]
    assert all(case.blocked_by.startswith(("state:", "decision:"))
               for case in blocked)
    assert all(case.variant in VARIANTS for case in blocked)
    assert all(input_limit(case) == case.blocked_by for case in blocked)
