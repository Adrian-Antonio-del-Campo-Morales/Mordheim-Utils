"""Shared pytest configuration: the primary-category guard.

`docs/reference/test-sequence.md` fixes one primary category per executable
test, chosen from its assertions. The categories are registered in
`pyproject.toml`, so `pytest -m <category>` selects them. Strict marker
registration alone does not detect a missing or a doubled category, so this
guard validates the collected items: it rejects items that carry none, several,
or a marker that is not a category.
"""
from __future__ import annotations

import pytest

PRIMARY_CATEGORIES = frozenset({
    "architecture",
    "data_contract",
    "knowledge_integrity",
    "data_transport",
    "eligibility",
    "compilation",
    "operator",
    "rule_behavior",
    "interaction",
    "workflow",
    "persistence",
    "presentation",
    "end_to_end",
    "test_infrastructure",
    "evidence",
    "parity",
    "performance",
    "delivery",
})

# Pytest's own marks select or skip; they are not a primary category.
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
            reason = "no primary category"
        elif len(categories) > 1:
            reason = "multiple primary categories: " + ", ".join(categories)
        else:
            reason = "not a category: " + ", ".join(unknown)
        problems.append(f"{item.nodeid} ({reason})")

    if problems:
        raise pytest.UsageError(
            f"{len(problems)} collected test(s) lack exactly one primary category "
            "(see docs/reference/test-sequence.md):\n  " + "\n  ".join(problems[:40])
            + ("\n  ..." if len(problems) > 40 else "")
        )
