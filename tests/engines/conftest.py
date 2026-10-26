"""Historical shared-corpus access for shared tests moved to engine suites.

Frozen case keys kept their original ``unit/shared/<file>/...`` provenance when
tests moved out of ``tests/engines/shared``.  A directory-local conftest cannot
derive that historical key from the new path, so ``shared_precompiled``
resolves it explicitly.  It reads only the frozen corpus; nothing here imports
the construction compiler, the knowledge base or an engine.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest

from tools.verification.compiled_cases import CompiledCase
from tools.verification.compiled_cases import load_cases


CORPUS = Path(__file__).resolve().parent / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def _cases() -> dict[str, CompiledCase]:
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
def shared_cases() -> dict[str, CompiledCase]:
    """The precompiled cases, keyed by their historical shared key."""
    return _cases()


@pytest.fixture
def shared_precompiled(request, shared_cases):
    """Resolve the historical shared case for this invocation."""

    def load(case_index: int = 0) -> CompiledCase:
        key = _case_key(request, case_index)
        try:
            return shared_cases[key]
        except KeyError:
            raise AssertionError(
                f"missing precompiled case {key} for {request.node.nodeid}"
            ) from None

    return load
