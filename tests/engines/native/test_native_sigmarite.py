"""Focused native compile regressions."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from mordheim_combat.native._combat_compile import compile_duel
from tools.verification.compiled_cases import load_cases
import pytest


_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def _cases():
    return load_cases(_CORPUS)


@pytest.mark.phase6_native
def test_native_compile_preserves_sigmarite_and_ignore_pain_contract() -> None:
    case = _cases()["parity/deep/sigmarite-vs-undead"]
    context = compile_duel(case.first, case.second)

    assert context["sources_first"]["main"]["flags"]["sigmarite"] is True
    assert context["second"]["undead_or_possessed"] is True
    assert context["second"]["ignore_pain"] is True


@pytest.mark.phase6_native
def test_native_source_keeps_pool_phase_snapshot_for_stunned_followups() -> None:
    source = open(
        "packages/python/combat-engine/mordheim_combat/native/_combat_native.pyx",
        encoding="utf-8",
    ).read()
    assert "Do not finish STUNNED defenders here" in source
    assert "if phase_cond[row] == STUNNED:" in source
