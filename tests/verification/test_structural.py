"""Auditoría estructural de fases y bindings."""
from __future__ import annotations

from dataclasses import fields
from itertools import combinations
from mordheim_construction.contracts import effect_index
from mordheim_core.effects import merge_best_effects
from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet
from mordheim_combat_lab.verification.specifications import load_phase_verification
from mordheim_combat_lab.verification.structural import audit_phase_verification


def test_structural_audit_covers_the_current_implemented_catalogue_snapshot():
    report = audit_phase_verification()
    assert report.errors == ()
    assert report.structural_complete
    # Catalogue snapshot only, never an assertion of semantic completeness.
    assert report.execution_mechanics == 193
    assert report.projected_mechanics == 190
    assert report.projected_trait_bindings == 36
    assert report.evidenced_profile_bindings == 6
    assert report.projected_automatic_compiler_bindings == 34
    assert report.evidenced_selectable_compiler_bindings == 8
    assert report.evidenced_special_compiler_bindings == 18
    assert report.observable_canonical_bindings == 171
    assert report.evidenced_complex_sequences == 13
    assert report.modular_tag_consumers == 74
    assert report.modular_operator_fields == 54
    assert report.modular_execution_mechanics == 193
    assert report.implemented_rule_records == 394
    assert report.canonical_bindings == 171


def test_every_effect_field_has_an_owned_phase_operator():
    specification = load_phase_verification("mordheim")
    assert set(specification["operator_fields"]) == {field.name for field in fields(EffectSet)}
    assert specification["composition_policies"] == {
        "stack": "additive",
        "best": "best-independent-value",
        "once": "first-per-canonical-id",
    }


def test_complex_rules_declare_their_minimal_phase_sequences():
    complex_rules = load_phase_verification("mordheim")["complex_rules"]
    assert complex_rules["trained-bear--bear-hug"]["phases"] == ["hit", "wound", "armour"]
    assert complex_rules["mechanic.force-of-will"]["phases"] == ["injury", "aftermath", "duel_start"]
    assert complex_rules["critical-per-phase"]["phases"] == ["wound", "injury"]
    assert all(rule.get("scenario") for rule in complex_rules.values())


def test_bindings_are_classified_compositionally_instead_of_repeating_editorial_rules():
    specification = load_phase_verification("mordheim")
    assert specification["binding_categories"] == {
        "mechanic": "phase_operator",
        "trait": "compiled_modifier",
        "profile": "construction",
        "compiler": "construction",
    }
    assert audit_phase_verification().interaction_groups > 0


def test_semantic_evidence_declares_an_observable_for_each_binding_kind():
    evidence = load_phase_verification("mordheim")["semantic_evidence"]
    assert evidence["mechanism_projection"]["observable"] == "compiled-effect-set"
    assert evidence["binding_strategies"] == {
        "mechanic": "compiled-effect-and-phase",
        "trait": "compiled-value-and-phase",
        "profile": "construction-result",
        "compiler": "acceptance-and-rejection",
    }


def test_all_declarative_effect_pairs_compose_independently_of_catalogue_order():
    effects = [definition.effect for definition in effect_index("mordheim").values()]
    for left, right in combinations(effects, 2):
        for merge in (merge_effects, merge_best_effects):
            forward, reverse = merge(left, right), merge(right, left)
            assert set(forward.tags) == set(reverse.tags)
            for field in fields(EffectSet):
                if field.name != "tags":
                    assert getattr(forward, field.name) == getattr(reverse, field.name)
