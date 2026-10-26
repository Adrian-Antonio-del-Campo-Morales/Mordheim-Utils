"""Frozen precompiled cases and build snapshots for the vectorized tests (T08).

The corpus is generated once from the reviewed sources and never recompiled
here.  A missing key is an error: nothing in this package reads the knowledge
base or calls the construction compiler to prepare a fighter.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.verification.compiled_builds import BuildSnapshots
from tools.verification.compiled_builds import load_builds
from tools.verification.compiled_cases import load_cases

CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
BUILDS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-builds.json"
PREFIX = "unit/vectorized/"


@pytest.fixture(scope="session")
def vector_case():
    """Return a resolver from ``<module>/<test>-<param>-<case>`` to a case."""
    cases = load_cases(CORPUS)

    def resolve(relative_key: str):
        key = relative_key if relative_key.startswith("unit/") else PREFIX + relative_key
        try:
            return cases[key]
        except KeyError as error:
            raise AssertionError(f"missing precompiled case {key}") from error

    return resolve


@pytest.fixture(scope="session")
def compiled_builds() -> BuildSnapshots:
    """The frozen ``compile_fighter`` results, loaded once for the session."""
    return load_builds(BUILDS)
