"""Shared pytest configuration: the single phase-category guard.

`docs/reference/test-sequence.md` fixes one phase category per executable test,
chosen from its assertions. The categories are registered in `pyproject.toml`,
so `pytest -m <category>` selects them. Strict marker registration alone does
not detect a missing or a doubled category, so this guard validates the
collected items: it rejects items that carry none, several, or a marker that is
not a category.
"""
from __future__ import annotations

import pytest

from tools.verification.test_sequence import CATEGORY_ORDER

PRIMARY_CATEGORIES = frozenset(CATEGORY_ORDER)

# Pytest's own marks select or skip; they are not a phase category.
RUNNER_MARKERS = frozenset({
    "parametrize",
    "skip",
    "skipif",
    "xfail",
    "usefixtures",
    "filterwarnings",
})

# Roots whose items are classified. Extend this tuple (not the checks) when a
# root is classified by its owner.
CLASSIFIED_ROOTS = (
    "tests/python/architecture",
    "tests/python/contracts",
    "tests/python/knowledge",
    "tests/python/construction",
    "tests/python/application",
    "tests/python/persistence",
    "tests/python/ui",
    "tests/python/cli",
    "tests/python/web",
    "tests/python/combat",
    "tests/python/verification",
    "tests/E2E/modular-engine",
)


def _is_classified_path(relative_path: str) -> bool:
    return any(
        relative_path == root or relative_path.startswith(root + "/")
        for root in CLASSIFIED_ROOTS
    )


def pytest_collection_modifyitems(config, items):
    problems = []
    for item in items:
        try:
            relative_path = item.path.relative_to(config.rootpath).as_posix()
        except ValueError:
            continue
        if not _is_classified_path(relative_path):
            continue
        markers = {marker.name for marker in item.iter_markers()}
        categories = sorted(markers & PRIMARY_CATEGORIES)
        unknown = sorted(markers - PRIMARY_CATEGORIES - RUNNER_MARKERS)
        if len(categories) == 1 and not unknown:
            continue
        if not categories:
            reason = "no phase category"
        elif len(categories) > 1:
            reason = "multiple phase categories: " + ", ".join(categories)
        else:
            reason = "not a phase category: " + ", ".join(unknown)
        problems.append(f"{item.nodeid} ({reason})")

    if problems:
        raise pytest.UsageError(
            f"{len(problems)} collected test(s) lack exactly one phase category "
            "(see docs/reference/test-sequence.md):\n  " + "\n  ".join(problems[:40])
            + ("\n  ..." if len(problems) > 40 else "")
        )
