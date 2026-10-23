"""Precompiled-case access for the modular engine suite (T07).

The modular tests no longer build fighters through the knowledge base and the
construction compiler.  They read the frozen corpus produced by T06, whose
cases keep the provenance captured for each pytest invocation.  Nothing here
imports the compiler, the knowledge base or the engine: a missing or
incompatible corpus raises ``CompiledCaseError`` instead of recompiling a
fighter.

``precompiled()`` resolves the case captured for the running test from its
provenance (``unit/modular/<file>/<test>-<parameter-set>-<case>``), so a test
cannot silently read another invocation's fighters.  ``cases`` exposes the whole
corpus for tests that need to say which case they mean.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pytest

from tools.verification.compiled_builds import BuildSnapshots
from tools.verification.compiled_builds import load_builds
from tools.verification.compiled_cases import CompiledCase
from tools.verification.compiled_cases import load_cases


CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def precompiled_cases() -> dict[str, CompiledCase]:
    """Load the frozen corpus once per session."""
    return load_cases(CORPUS)


def _parameter_set(request) -> int:
    """The invocation's position in its function's collection order.

    The corpus records it as ``-<parameter-set>-``: ``0`` for a plain test and
    the collection index for each parametrized case, which is also pytest's
    invocation order.
    """
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
    return f"unit/modular/{stem}/{name}-{_parameter_set(request)}-{case_index}"


@pytest.fixture(scope="session")
def compiled_builds() -> BuildSnapshots:
    """The frozen ``compile_fighter`` results, loaded once for the session."""
    return load_builds(
        Path(__file__).resolve().parents[1] / "fixtures" / "compiled-builds.json")


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
