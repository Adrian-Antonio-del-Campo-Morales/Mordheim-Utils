"""Frozen precompiled cases for the shared engine contracts (T01/T02).

These tests cover phase operators, context and kernel planning that several
backends share.  They read the frozen corpus produced by T06 and never build a
fighter through the knowledge base or the construction compiler.

``precompiled()`` resolves the case captured for the running test invocation
from its provenance (``unit/shared/<file>/<test>-<parameter-set>-<case>``).
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


def _parameter_set(request) -> int:
    """The invocation's position in its function's collection order."""
    node = request.node
    if not hasattr(node, "callspec"):
        return 0
    siblings = [
        item for item in node.session.items
        if item.originalname == node.originalname and item.path == node.path
    ]
    return siblings.index(node)


def _case_key(request, case_index: int) -> str:
    stem = Path(str(request.node.path)).stem
    name = request.node.originalname
    return f"unit/shared/{stem}/{name}-{_parameter_set(request)}-{case_index}"


@pytest.fixture(scope="session")
def cases() -> dict[str, CompiledCase]:
    """The precompiled cases, keyed by ``case_key``."""
    return precompiled_cases()


@pytest.fixture
def precompiled(request, cases):
    """The case captured for this test invocation; ``precompiled(1)`` the next."""

    def load(case_index: int = 0) -> CompiledCase:
        key = _case_key(request, case_index)
        try:
            return cases[key]
        except KeyError:
            raise AssertionError(
                f"missing precompiled case {key} for {request.node.nodeid}"
            ) from None

    return load
