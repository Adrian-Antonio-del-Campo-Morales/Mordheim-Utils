"""Ejecutor y matriz de verificación semántica."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from mordheim_combat_lab.domain.dice import RollRequest
from mordheim_combat_lab.knowledge.loader import knowledge_root
from mordheim_combat_lab.verification.audit import verify_semantics
from mordheim_combat_lab.verification.dice import StrictDecisions
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_combat_lab.verification.dice import enumerate_exact
from mordheim_combat_lab.verification.inventory import binding_key
from mordheim_combat_lab.verification.inventory import inventory
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_combat_lab.verification.scenarios import check_case
from mordheim_combat_lab.verification.specifications import load_fixtures
from mordheim_combat_lab.verification.structural import audit_phase_verification
import pytest as pytest
import yaml as yaml


@pytest.mark.parametrize("spec_id", ["initial-choice-mordheim-mutants", "initial-choice-tainted-ones"])
def test_initial_choice_mutation_is_isolated(spec_id):
    spec = next(s for s in load_fixtures() if s["id"] == spec_id)
    case = next(c for c in spec["cases"] if c["id"] == "choices")
    check_case(case, knowledge_root())
    with pytest.raises(EvidenceMismatch):
        check_case(case, knowledge_root(), spec["mutations"][0])
    check_case(case, knowledge_root())


@pytest.mark.parametrize("operation, choices", [
    ("selection_choices", {"bad": {"armour_id": "armour.light-armour"}}),
    ("selection_choices", {"bad": {"arbitrary_code": "pass"}}),
    ("equipment_choices", {"bad": {"special_rule_ids": []}}),
])
def test_construction_choices_reject_fields_outside_their_contract(operation, choices):
    with pytest.raises(ValueError, match="unsupported construction fields"):
        check_case({"operation": operation, "context": {"choices": choices},
                    "expect": {"result.accepted": []}}, knowledge_root())


def test_selection_choices_cannot_ignore_decisions():
    with pytest.raises(ValueError, match="construction cases cannot request combat decisions"):
        check_case({"operation": "selection_choices", "context": {"choices": {}},
                    "decisions": [{"key": "unrelated", "value": True}],
                    "expect": {"result.accepted": []}}, knowledge_root())


def test_category_prohibition_mutation_is_isolated():
    spec = next(s for s in load_fixtures()
                if s["id"] == "category-prohibitions-battle-monks-of-cathay-poison")
    case = next(c for c in spec["cases"] if c["id"] == "choices-dragon-monks")
    check_case(case, knowledge_root())
    with pytest.raises(EvidenceMismatch):
        check_case(case, knowledge_root(), spec["mutations"][0])
    check_case(case, knowledge_root())


def test_semantic_inventory_includes_effects_not_only_implemented_rules(tmp_path):
    def write(name, value):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value), encoding="utf-8")
    write("registry/runtime-scope.yaml", {})
    write("catalog/mechanics/close-combat.yaml", {})
    rule = {"id": "mixed", "effect": "A written effect", "runtime": {
        "scope": "LATER", "implemented": "NO", "effects": [
            {"id": "active", "scope": "YES", "binding": None},
            {"id": "later", "scope": "LATER", "binding": None},
        ]}}
    write("bands/example/warband/special-rules.yaml", {"rules": [rule]})
    for name in ("profiles", "band", "equipment-access"):
        write(f"bands/example/warband/{name}.yaml", {})
    result = inventory(tmp_path)
    assert len(result) == 1
    assert result[0].id == "rule/example/warband/mixed/active"
    assert result[0].binding == "unbound"
    old_digest = result[0].source_digest
    rule["effect"] = "Changed written effect"
    write("bands/example/warband/special-rules.yaml", {"rules": [rule]})
    assert inventory(tmp_path)[0].source_digest != old_digest


def test_binding_identity_preserves_parameters_and_ignores_mapping_order():
    a = {"kind": "trait", "id": "trait.ward-save", "parameters": {"value": 5}}
    b = {"id": "trait.ward-save", "parameters": {"value": 5}, "kind": "trait"}
    c = {**a, "parameters": {"value": 4}}
    assert binding_key(a) == binding_key(b)
    assert binding_key(a) != binding_key(c)


def test_structural_success_is_not_semantic_success():
    assert audit_phase_verification().structural_complete
    report = verify_semantics()
    assert report.errors == ()
    # Unreviewed catalogue entries must never be silently certified by the
    # structural audit or by the presence of a tag in the runtime.
    assert set(report.verified).isdisjoint(target for target, _ in report.pending)
    assert len(report.verified) + len(report.pending) == len(report.obligations)
    assert report.semantic_complete == (not report.pending and not report.errors
        and not report.required_pending_interactions
        and not report.pending_higher_order_interactions)


def test_interaction_risk_is_separate_from_verification_requirement():
    from mordheim_combat_lab.verification.interactions import assess_interaction
    contracts = {
        "left": {"reads": [], "writes": ["state.wounds"]},
        "right": {"reads": ["state.wounds"], "writes": []},
    }
    result = assess_interaction("left", "right", contracts)
    assert result.risk_level == "critical"
    assert result.verification_requirement == "required"
    assert result.status == "pending"
    overridden = assess_interaction("left", "right", contracts, override={
        "risk_level": "medium", "verification_requirement": "recommended",
        "status": "covered_by_composition", "risk_reasons": ["generic_stack"],
        "evidence": ["operator:stack"],
    })
    assert overridden.risk_level == "medium"
    assert overridden.verification_requirement == "recommended"
    assert overridden.status == "covered_by_composition"


@pytest.mark.parametrize("values", [[], [{"key": "wrong", "value": 3}],
                                    [{"key": "hit", "sides": 3, "value": 3}]])
def test_strict_dice_rejects_unexpected_requests(values):
    with pytest.raises(EvidenceMismatch):
        StrictDice(values).roll(RollRequest("hit"))


def test_strict_dice_checks_unused_rolls_and_repeated_keys():
    tape = StrictDice([{"key": "hit", "value": 2}, {"key": "hit", "value": 6}])
    assert tape.roll(RollRequest("hit")) == 2
    with pytest.raises(EvidenceMismatch, match="unused"):
        tape.finish()
    assert tape.roll(RollRequest("hit")) == 6
    tape.finish()


def test_strict_decisions_rejects_unused_and_unexpected_choices():
    policy = StrictDecisions([{"key": "hug", "value": False}])
    with pytest.raises(EvidenceMismatch, match="unused"):
        policy.finish()
    assert policy.choose("hug") is False
    policy.finish()
    with pytest.raises(EvidenceMismatch):
        policy.choose("hug")


def test_adaptive_enumeration_weights_short_circuit_and_mixed_dice_exactly():
    def trial(dice):
        if dice.roll(RollRequest("first")) >= 5:
            return "early"
        return "late" if dice.roll(RollRequest("second", 3)) == 3 else "failed"
    assert enumerate_exact(trial) == {
        "early": Fraction(1, 3), "late": Fraction(2, 9), "failed": Fraction(4, 9),
    }


def test_enumeration_refuses_to_truncate_unbounded_sequences():
    def forever(dice):
        while True:
            dice.roll(RollRequest("again"))
    with pytest.raises(ValueError, match="roll bound"):
        enumerate_exact(forever, max_rolls=2)


@pytest.mark.parametrize("case", [
    pytest.param(case, id=f"{spec['id']}/{case['id']}")
    for spec in load_fixtures() if not spec.get("pending")
    for case in spec["cases"]
])
def test_authored_semantic_case(case):
    check_case(case, knowledge_root())


def test_bear_hug_has_a_real_source_link_and_detected_behavioural_mutations():
    report = verify_semantics()
    bear = next(fixture for fixture in report.fixtures if fixture.id == "bear-hug")
    assert bear.errors == ()
    assert "tie-no-armour" in bear.passed_cases
    assert "remove-hug-handler-activation" in bear.killed_mutations
    assert bear.targets[0] in report.verified


def _single_spec(monkeypatch, change):
    import mordheim_combat_lab.verification.audit as semantic
    fixture = deepcopy(next(s for s in load_fixtures() if s["id"] == "mighty-blow"))
    change(fixture)
    monkeypatch.setattr(semantic, "load_fixtures", lambda root: (fixture,))
    return verify_semantics()


def test_changed_source_cannot_reuse_old_evidence(monkeypatch):
    report = _single_spec(monkeypatch, lambda s: s["sources"][0].update(digest="outdated"))
    assert not report.verified
    assert any("source changed" in error for error in report.errors)


def test_surviving_mutation_prevents_certification(monkeypatch):
    report = _single_spec(monkeypatch, lambda s: s.update(mutations=[{
        "id": "no-change", "path": "attacker.global_effects.strength_bonus", "value": 1,
        "cases": ["ordinary-strength"],
    }]))
    assert not report.verified
    assert any("surviving mutation" in error for error in report.errors)


def test_compile_only_case_cannot_claim_consumer_evidence(monkeypatch):
    def change(spec):
        spec["cases"] = [spec["cases"][0]]
        spec["cases"][0]["roles"] = ["compiled", "consumer", "boundary"]
    report = _single_spec(monkeypatch, change)
    assert not report.verified
    assert any("compile-only" in error for error in report.errors)


def test_unresolved_ruling_stays_pending(monkeypatch):
    report = _single_spec(monkeypatch, lambda s: s.update(pending="needs source clarification"))
    assert not report.errors
    assert not report.verified
    assert ("mechanic/skill.mighty-blow", "needs source clarification") in report.pending


def test_interaction_proof_does_not_certify_participant_rules(monkeypatch):
    import mordheim_combat_lab.verification.audit as semantic
    interaction = next(s for s in load_fixtures() if s["id"] == "two-strength-skills-stack")
    monkeypatch.setattr(semantic, "load_fixtures", lambda root: (interaction,))
    report = verify_semantics()
    assert not report.errors
    assert not report.verified
    assert len(report.verified_interactions) == 1
    assert not report.semantic_complete


def test_scope_change_invalidates_previous_reviews(monkeypatch):
    report = _single_spec(monkeypatch, lambda spec: spec.update(scope_digest="old-scope"))
    assert not report.verified
    assert any("scope changed" in error for error in report.errors)


def test_unknown_scenario_field_cannot_be_silently_ignored():
    with pytest.raises(ValueError, match="unknown scenario fields"):
        check_case({"id": "typo", "operation": "compile", "expected": {}}, knowledge_root())


def test_misspelled_activation_condition_cannot_be_silently_ignored():
    with pytest.raises(ValueError, match="unknown context fields"):
        check_case({"id": "typo", "operation": "strength", "context": {"charing": True},
                    "expect": {"result.wound": 3}}, knowledge_root())


def test_distribution_cannot_silently_ignore_fixed_expectations():
    with pytest.raises(ValueError, match="cannot silently ignore"):
        check_case({"id": "mixed", "operation": "hit", "expect": {"result.success": True},
                    "distribution": {}}, knowledge_root())


def test_mutation_must_reference_real_passing_baseline_cases(monkeypatch):
    report = _single_spec(monkeypatch, lambda spec: spec["mutations"][0]["cases"].append("typo"))
    assert not report.verified
    assert any("passing baseline cases" in error for error in report.errors)


def test_interaction_concepts_are_normalized_and_unknown_concepts_rejected():
    from mordheim_combat_lab.verification.interactions import normalize_interaction_contract
    assert normalize_interaction_contract({"reads": ["strength.base", "fighter.strength"],
                                           "writes": ["attacks.count"]}) == {
        "reads": ["fighter.strength"], "writes": ["attack.count"],
    }
    with pytest.raises(ValueError, match="unknown interaction concepts"):
        normalize_interaction_contract({"reads": [], "writes": ["attaks.count"]})


def test_isolated_construction_mutation_does_not_leak():
    spec = next(s for s in load_fixtures() if s["id"] == "access-mordheim-dark-elves")
    case = next(c for c in spec["cases"] if c["id"] == "granted-high-born")
    with pytest.raises(EvidenceMismatch):
        check_case(case, knowledge_root(), spec["mutations"][0])
    check_case(case, knowledge_root())


def test_isolated_resource_mutations_do_not_leak():
    spec = next(s for s in load_fixtures() if any(
        m.get("runtime_fault") == "retain-critical-allowance" for m in s.get("mutations", [])))
    mutant = next(m for m in spec["mutations"] if m.get("runtime_fault") == "retain-critical-allowance")
    case = next(c for c in spec["cases"] if c["id"] in mutant["cases"])
    with pytest.raises(EvidenceMismatch):
        check_case(case, knowledge_root(), mutant)
    check_case(case, knowledge_root())


def test_rapier_failed_extra_hit_omits_extra_wound_roll():
    # Focused regression, not a certificate of all Rapier interactions.
    check_case({"id": "rapier-extra-miss", "operation": "attack",
                "attacker": {"main_weapon_id": "weapon.rapier"},
                "rolls": [{"key": "test.hit", "value": 4},
                          {"key": "test.wound", "value": 1},
                          {"key": "test.rapier.hit", "value": 1}],
                "expect": {"result.hit": True, "result.wounded": False,
                           "result.defender.wounds": 3}}, knowledge_root())


def test_integration_checks_execute_real_phase_calls(monkeypatch):
    from dataclasses import replace
    import mordheim_combat_lab.combat.modular.rounds as reference
    from mordheim_combat_lab.combat.modular.state import CombatRoundResult
    import mordheim_combat_lab.combat.phases as phases
    from mordheim_combat_lab.verification.integrations import verify_integrations
    def forged_round(first, second, state, dice, decisions=None):
        return CombatRoundResult(replace(
            state, round_index=1, second=replace(state.second, condition=phases.Condition.OUT)), ())
    monkeypatch.setattr(reference, "resolve_round", forged_round)
    passed, errors = verify_integrations(knowledge_root())
    assert "actual-phase-order-and-state-transfer" not in passed
    assert any("actual-phase-order-and-state-transfer" in error for error in errors)


def test_generic_operator_witnesses_detect_an_incorrect_composition(monkeypatch):
    import mordheim_combat_lab.domain.effects as effects
    from mordheim_combat_lab.verification.operators import verify_operators
    from mordheim_combat_lab.verification.operators import OPERATOR_CHECKS
    assert verify_operators() == (OPERATOR_CHECKS, ())
    monkeypatch.setattr(effects, "merge_effects", lambda left, right: left)
    passed, errors = verify_operators()
    assert "stack" not in passed
    assert errors


def test_compositional_evidence_cannot_depend_on_itself(monkeypatch):
    report = _single_spec(monkeypatch, lambda spec: spec.update(depends_on=["mechanic/skill.mighty-blow"]))
    assert not report.verified
    assert any("circular semantic dependencies" in error for error in report.errors)


def test_unverified_shared_consumer_keeps_editorial_grant_pending(monkeypatch):
    import mordheim_combat_lab.verification.audit as semantic
    fixture = next(s for s in load_fixtures() if s["id"] == "poison-grant-mordheim-undead-vampire")
    monkeypatch.setattr(semantic, "load_fixtures", lambda root: (fixture,))
    report = verify_semantics()
    assert not report.errors
    assert not report.verified
    assert (fixture["sources"][0]["target"], "dependency lacks semantic evidence") in report.pending


def test_claimed_equivalence_must_not_change_any_observable(monkeypatch):
    def change(spec):
        spec["mutations"][0]["equivalent_reason"] = "Incorrect claim for test of the verifier"
    report = _single_spec(monkeypatch, change)
    assert not report.verified
    assert any("claimed equivalent mutation changes" in error for error in report.errors)


def test_redundant_access_mutation_is_justified_not_counted_as_detected(monkeypatch):
    import mordheim_combat_lab.verification.audit as semantic
    fixture = next(s for s in load_fixtures() if s["id"] == "access-nagarythe-already-strength")
    monkeypatch.setattr(semantic, "load_fixtures", lambda root: (fixture,))
    report = verify_semantics()
    assert not report.errors
    assert report.fixtures[0].killed_mutations == ()
    assert report.fixtures[0].justified_mutations == ("redirect-redundant-grant",)
    assert fixture["sources"][0]["target"] in report.verified


def test_three_rule_evidence_does_not_certify_pairs_or_bindings(monkeypatch):
    import mordheim_combat_lab.verification.audit as semantic
    fixture = next(s for s in load_fixtures() if s["id"] == "concussion-no-pain-jump-up")
    monkeypatch.setattr(semantic, "load_fixtures", lambda root: (fixture,))
    report = verify_semantics()
    assert not report.errors
    assert not report.verified
    assert not report.verified_interactions
    assert len(report.verified_higher_order_interactions) == 1
    assert len(report.pending_higher_order_interactions) == 1
