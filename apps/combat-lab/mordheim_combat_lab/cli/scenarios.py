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

    Prefers the normal import (pytest and the launcher put the checkout root
    on ``sys.path``); otherwise loads the module file below this checkout's
    ``project_root()``, so the installed CLI works from any directory and
    every worktree reads its own sources.
    """
    import importlib
    import sys

    module = sys.modules.get(qualified)
    if module is not None:
        return module
    try:
        return importlib.import_module(qualified)
    except ImportError:
        pass
    import importlib.util

    from mordheim_knowledge.paths import project_root

    path = project_root() / (qualified.replace(".", "/") + ".py")
    specification = importlib.util.spec_from_file_location(qualified, path)
    if specification is None or specification.loader is None:
        raise ImportError(f"cannot load {qualified} from {path}")
    module = importlib.util.module_from_spec(specification)
    # Registered under its canonical name so later `import ...` resolvers
    # and this loader agree on one module object per process.
    sys.modules[qualified] = module
    specification.loader.exec_module(module)
    return module


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
