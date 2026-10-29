"""Frozen-corpus access for tooling tests moved out of ``tests/engines/parity``.

The parity catalogue, reporting and benchmark checks keep the historical
unified ``scenario/...`` keys.  They read the engine corpus
directly; nothing here imports the construction compiler, the knowledge base or
an engine, and no fighter is rebuilt.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest

from tools.verification.compiled_cases import CompiledCase
from tools.verification.compiled_cases import load_cases


CORPUS = Path(__file__).resolve().parents[1] / "engines" / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def precompiled_cases() -> dict[str, CompiledCase]:
    """Load the frozen corpus once per session."""
    return load_cases(CORPUS)


@pytest.fixture(scope="session")
def cases() -> dict[str, CompiledCase]:
    """The precompiled cases, keyed by ``case_key``."""
    return precompiled_cases()
