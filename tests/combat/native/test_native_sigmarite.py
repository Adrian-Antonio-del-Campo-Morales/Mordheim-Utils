"""Focused native compile regressions."""
from __future__ import annotations

from mordheim_combat.native._combat_compile import compile_duel
from mordheim_combat_lab.cli.benchmarking import DEEP_SCENARIOS
from mordheim_construction.compiler import compile_fighter


def test_native_compile_preserves_sigmarite_and_ignore_pain_contract() -> None:
    scenario = next(item for item in DEEP_SCENARIOS if item.id == "sigmarite-vs-undead")
    from mordheim_knowledge.loader import knowledge_root

    first = compile_fighter(scenario.first, knowledge_root())
    second = compile_fighter(scenario.second, knowledge_root())
    context = compile_duel(first, second)

    assert context["sources_first"]["main"]["flags"]["sigmarite"] is True
    assert context["second"]["undead_or_possessed"] is True
    assert context["second"]["ignore_pain"] is True


def test_native_source_keeps_pool_phase_snapshot_for_stunned_followups() -> None:
    source = open(
        "packages/python/combat-engine/mordheim_combat/native/_combat_native.pyx",
        encoding="utf-8",
    ).read()
    assert "Do not finish STUNNED defenders here" in source
    assert "if phase_cond[row] == STUNNED:" in source
