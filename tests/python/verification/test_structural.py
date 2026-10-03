"""Structural audit of phases and bindings."""
from __future__ import annotations

from dataclasses import fields
from itertools import combinations
from pathlib import Path

from mordheim_construction.contracts import effect_index
from mordheim_core.effects import merge_best_effects
from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet
from mordheim_combat_lab.verification.specifications import load_phase_verification
from mordheim_combat_lab.verification.structural import audit_phase_verification
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import runtime_bindings


_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"


def _implemented_rule_records() -> int:
    """Count implemented band rules straight from the knowledge base.

    Mirrors the audit's own walk over the band packages (scope YES +
    implemented YES) so the test fails when the recorded count drifts from the
    catalogue rather than when a legitimately promoted band moves the number.
    The reason for every delta stays documented beside the pin below.
    """
    total = 0
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection, _KNOWLEDGE_ROOT):
            for rule in band.special_rules:
                runtime = rule.get("runtime") or {}
                if runtime.get("scope") == "YES" and runtime.get("implemented") == "YES":
                    total += 1
                    if not runtime_bindings(rule):
                        raise AssertionError(
                            f"{band.band['id']}/{rule['id']}: implemented rule has no binding"
                        )
    return total


def test_structural_audit_covers_the_current_implemented_catalogue_snapshot():
    """No allow-list: the audit is green or the test fails.

    The three profiles the duel runtime cannot carry (the Gyrocopter, the River
    Boat and the Banshee) are declared exclusions of `runtime-scope.yaml` with
    their reason. L03 Spectral Touch and L04 Shifty now compile canonically;
    their optimized support guards do not weaken this structural audit.
    """
    report = audit_phase_verification()
    assert report.errors == ()
    assert report.structural_complete
    # Catalogue snapshot only, never an assertion of semantic completeness.
    assert report.execution_mechanics == 194  # 193 entry + L04 Shifty
    assert report.projected_mechanics == 191  # 190 entry + L04 Shifty
    assert report.projected_trait_bindings == 38  # L03 Spectral: 37 -> 38
    assert report.evidenced_profile_bindings == 6
    assert report.projected_automatic_compiler_bindings == 35
    assert report.evidenced_selectable_compiler_bindings == 8
    assert report.evidenced_special_compiler_bindings == 18
    assert report.observable_canonical_bindings == 175  # 173 + L03 Spectral + L04 Shifty
    assert report.evidenced_complex_sequences == 13
    assert report.modular_tag_consumers == 75  # L04: Shifty's existing round consumer
    # Field-consumer registry stays in lockstep with the EffectSet contract;
    # derived here from the same static registry the audit reads.
    from mordheim_combat_lab.verification.structural import MODULAR_FIELD_CONSUMERS
    assert report.modular_operator_fields == len(MODULAR_FIELD_CONSUMERS)
    assert len(MODULAR_FIELD_CONSUMERS) == len(set(MODULAR_FIELD_CONSUMERS))
    assert report.modular_execution_mechanics == 194
    # 420 base records + 2 forbid-skill-categories profile rules + the
    # implemented records of the promoted bands, including L03/L04 activation.
    # Derived from the knowledge base instead of pinning a number: it moves with
    # legitimately promoted rules and fails on any silent drift.
    assert report.implemented_rule_records == _implemented_rule_records()
    assert report.implemented_rule_records == 493  # 491 + L03 Spectral + L04 Shifty
    assert report.canonical_bindings == 175


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
