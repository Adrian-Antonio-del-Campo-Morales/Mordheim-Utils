"""Precompiled-case access for the parity and benchmark suites (T10).

Parity, replay and benchmark consumers no longer build fighters through the
knowledge base and the construction compiler.  They read the frozen corpus
produced by T06, keyed by the stable ``case_key`` that T01 fixed, and keep
their own scenarios, dice, decisions, contexts, seeds, samples and
tolerances.  Nothing here imports the compiler, the knowledge base or the
engines: a missing or incompatible corpus raises ``CompiledCaseError``
instead of recompiling a fighter.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest

from tools.verification.compiled_cases import CompiledCase
from tools.verification.compiled_cases import load_cases


CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def precompiled_cases() -> dict[str, CompiledCase]:
    """Load the frozen corpus once per session."""
    return load_cases(CORPUS)


@pytest.fixture(scope="session")
def cases() -> dict[str, CompiledCase]:
    """The precompiled cases, keyed by ``case_key``."""
    return precompiled_cases()
