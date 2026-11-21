"""The shared, frozen scenario catalogue as the CLI sees it.

Benchmarking, calibration and parity resolve their ``--scenarios`` values
through one function, ``select_scenarios``: a level (``small``, ``normal``,
``big``) or a scenario name selects the same scenarios in every tool.

The catalogue lives in the test fixtures (``tests/engines/fixtures/``), which
are not an installed package: importing ``tests`` only works with the checkout
root on ``sys.path``. So the CLI resolves this checkout's root through the
installed ``mordheim_knowledge`` package (each worktree's editable install
points at its own sources) and loads the catalogue module from its file,
reusing an already-imported ``tests`` package when one exists (pytest, the
launcher) so there is never a second copy of the module.
"""
from __future__ import annotations


def load_checkout_module(qualified: str):
    """Import a checkout-level module (``tests.*``, ``tools.*``) by name.

    The checkout root is put first on ``sys.path`` (found through the
    installed ``mordheim_knowledge``, whose editable install points at this
    checkout), so the installed CLI works from any directory, every worktree
    reads its own sources, and a loaded module can import its own
    ``tests.*``/``tools.*`` dependencies.
    """
    import importlib
    import sys

    from mordheim_knowledge.paths import project_root

    root = str(project_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    return importlib.import_module(qualified)


_catalog = load_checkout_module("tests.engines.fixtures.precompiled_catalog")
SCENARIOS = _catalog.SCENARIOS
BenchmarkScenario = _catalog.Scenario
scenarios_for_level = _catalog.scenarios_for_level
scenario_key = _catalog.scenario_key

DEEP_SCENARIOS = SCENARIOS
LEVELS = _catalog.LEVELS
select_scenarios = _catalog.select_scenarios
is_scenario_token = _catalog.is_scenario_token


def benchmark_scenarios() -> tuple[BenchmarkScenario, ...]:
    """The default, small selection of the shared scenario catalogue."""
    return scenarios_for_level("small")
