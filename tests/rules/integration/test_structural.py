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
import pytest


_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"


@pytest.mark.evidence
def test_catalogue_audit_rejects_unknown_active_contracts_but_allows_plans(tmp_path):
    import json
    from mordheim_combat_lab.verification.structural import _catalogue_binding_errors

    path = tmp_path / "catalog/skills/test.yaml"
    path.parent.mkdir(parents=True)
    rule = {"id": "skill.test", "runtime": {
        "scope": "YES", "implemented": "YES", "grant": "none",
        "effects": [{"id": "test", "scope": "YES",
                     "binding": {"kind": "mechanic", "id": "skill.known"}}],
    }}

    def errors():
        path.write_text(json.dumps({"skills": [rule]}), encoding="utf-8")
        return _catalogue_binding_errors(tmp_path, {"skill.known"})

    assert errors() == []
    rule["runtime"]["effects"][0]["binding"]["id"] = "skill.missing"
    assert "unknown mechanic binding skill.missing" in errors()[0]
    rule["runtime"]["implemented"] = "NO"
    assert errors() == []
    rule["runtime"]["scope"] = "LATER"
    rule["runtime"]["effects"][0]["scope"] = "LATER"
    rule["runtime"]["implemented"] = "YES"
    assert "active binding requires scope YES" in errors()[0]
    rule["runtime"]["scope"] = "YES"
    rule["runtime"]["effects"][0]["scope"] = "YES"
    rule["runtime"]["effects"][0]["binding"] = {
        "kind": "compiler", "id": "special-rule.banshee--cold-steel",
    }
    assert errors() == []
    rule["runtime"]["effects"][0]["binding"]["id"] = "special-rule.unknown-profile-rule"
    assert "unknown compiler binding" in errors()[0]


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


@pytest.mark.evidence
def test_structural_audit_covers_the_current_implemented_catalogue_snapshot():
    """No allow-list: the audit is green or the test fails.

    The two profiles the duel runtime cannot carry (the Gyrocopter and the
    River Boat) are declared exclusions of `runtime-scope.yaml` with their
    reason; the Banshee now reaches the pipeline with a blank Initiative.
    Spectral Touch and Shifty compile canonically; their optimized support
    guards do not weaken this structural audit.
    """
    report = audit_phase_verification()
    assert report.errors == ()
    assert report.structural_complete
    # Catalogue snapshot only, never an assertion of semantic completeness.
    # Current modular deliveries reconciled on 2026-10-19.  The inventories
    # were counted independently from the knowledge base and the execution
    # contract; every delta from the previous snapshot is a promoted record,
    # never a relaxed check:
    #   execution contract rows                 310 -> 504
    #   projected rows (504 - 3 excluded rows)  307 -> 501
    #   trait bindings                           38 -> 39
    #   automatic compiler bindings               37 -> 46 (all observed)
    #   selectable compiler bindings               8 -> 9  (Twistkin)
    #   special compiler bindings                 18 -> 22
    #   canonical bindings                       264 -> 346
    #   tag-only consumers                       167 -> 321
    #   modular execution rows                   310 -> 504
    #   implemented rule records (995 Mordheim + 417 Trollheim) 1016 -> 1412
    # Counts describe structural projection only, not semantic certification.
    # E2E_0021 adds Fey Quickness: one execution row and projection.
    # Band-rule binding counts stay unchanged; this is a catalogued skill.
    assert report.execution_mechanics == 505
    assert report.projected_mechanics == 502  # three declared exclusions
    assert report.projected_trait_bindings == 39
    assert report.evidenced_profile_bindings == 7  # active use whitelist, separate from ownership
    assert report.projected_automatic_compiler_bindings == 46
    assert report.evidenced_selectable_compiler_bindings == 9
    # +2 on 2026-10-21: the Necrotect's Hated profile ability and the Lahmia
    # Lost Innocence special rule now carry their maintained compiled-observable
    # evidence instead of being reported as unknown/missing bindings.
    assert report.evidenced_special_compiler_bindings == 24
    # +1 on 2026-10-21: the Necrotect binding is now recognised through the
    # `profile-rule.*` namespace that the structural contract already validated.
    assert report.observable_canonical_bindings == 347
    assert report.evidenced_complex_sequences == 13
    assert report.modular_tag_consumers == 321
    # Field-consumer registry stays in lockstep with the EffectSet contract;
    # derived here from the same static registry the audit reads.
    from mordheim_combat_lab.verification.structural import MODULAR_FIELD_CONSUMERS
    assert report.modular_operator_fields == len(MODULAR_FIELD_CONSUMERS)
    assert len(MODULAR_FIELD_CONSUMERS) == len(set(MODULAR_FIELD_CONSUMERS))
    assert report.modular_execution_mechanics == 505
    # 420 base records + 2 forbid-skill-categories profile rules + the
    # implemented records of the promoted bands, including Spectral Touch and Shifty.
    # Derived from the knowledge base instead of pinning a number: it moves with
    # legitimately promoted rules and fails on any silent drift.
    assert report.implemented_rule_records == _implemented_rule_records()
    # The count itself is derived from the band packages; the assertion above
    # already fails on any silent drift, so no pinned historical total is kept.
    assert report.canonical_bindings == 347


@pytest.mark.phase4_modular
def test_every_effect_field_has_an_owned_phase_operator():
    specification = load_phase_verification("mordheim")
    assert set(specification["operator_fields"]) == {field.name for field in fields(EffectSet)}
    assert specification["composition_policies"] == {
        "stack": "additive",
        "best": "best-independent-value",
        "once": "first-per-canonical-id",
    }


@pytest.mark.phase4_modular
def test_complex_rules_declare_their_minimal_phase_sequences():
    complex_rules = load_phase_verification("mordheim")["complex_rules"]
    assert complex_rules["trained-bear--bear-hug"]["phases"] == ["hit", "wound", "armour"]
    assert complex_rules["mechanic.force-of-will"]["phases"] == ["injury", "aftermath", "duel_start"]
    assert complex_rules["critical-per-phase"]["phases"] == ["wound", "injury"]
    assert all(rule.get("scenario") for rule in complex_rules.values())


@pytest.mark.phase4_modular
def test_bindings_are_classified_compositionally_instead_of_repeating_editorial_rules():
    specification = load_phase_verification("mordheim")
    assert specification["binding_categories"] == {
        "mechanic": "phase_operator",
        "trait": "compiled_modifier",
        "profile": "construction",
        "compiler": "construction",
    }
    assert audit_phase_verification().interaction_groups > 0


@pytest.mark.phase4_modular
def test_semantic_evidence_declares_an_observable_for_each_binding_kind():
    evidence = load_phase_verification("mordheim")["semantic_evidence"]
    assert evidence["mechanism_projection"]["observable"] == "compiled-effect-set"
    assert evidence["binding_strategies"] == {
        "mechanic": "compiled-effect-and-phase",
        "trait": "compiled-value-and-phase",
        "profile": "construction-result",
        "compiler": "acceptance-and-rejection",
    }


@pytest.mark.phase3_rules
def test_all_declarative_effect_pairs_compose_independently_of_catalogue_order():
    effects = [definition.effect for definition in effect_index("mordheim").values()]
    for left, right in combinations(effects, 2):
        for merge in (merge_effects, merge_best_effects):
            forward, reverse = merge(left, right), merge(right, left)
            assert set(forward.tags) == set(reverse.tags)
            for field in fields(EffectSet):
                if field.name != "tags":
                    assert getattr(forward, field.name) == getattr(reverse, field.name)
