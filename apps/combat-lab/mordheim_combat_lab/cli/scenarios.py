"""Compatibility names for the shared, frozen scenario catalogue.

Benchmarking, calibration and parity select the same scenario definitions
through the one set of cumulative catalogue level names: ``small``, ``normal``
and ``long``.  The ``mini``/``fast``/``full`` pair-set names they used to carry
were aliases of exactly those levels and have been retired.

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
SMALL_SCENARIO_IDS = tuple(item.name for item in scenarios_for_level("small"))
NORMAL_SCENARIO_IDS = tuple(item.name for item in scenarios_for_level("normal"))
LONG_SCENARIO_IDS = tuple(item.name for item in scenarios_for_level("long"))
DEEP_SCENARIO_SET_IDS = {
    "small": SMALL_SCENARIO_IDS,
    "normal": NORMAL_SCENARIO_IDS,
    "long": LONG_SCENARIO_IDS,
}


def benchmark_scenarios() -> tuple[BenchmarkScenario, ...]:
    """The default, small selection of the shared scenario catalogue."""
    return scenarios_for_level("small")


def deep_test_scenarios(level: str = "long") -> tuple[BenchmarkScenario, ...]:
    """Select one cumulative level of the shared scenario catalogue.

    The retired ``mini``/``fast``/``full`` aliases selected exactly these
    levels, so they are rejected with the name that replaced them.
    """
    retired = {"mini": "small", "fast": "normal", "full": "long"}
    if level in retired:
        raise ValueError(
            f"pair set {level!r} was renamed to {retired[level]!r}; "
            f"choose one of {', '.join(LEVELS)}"
        )
    return scenarios_for_level(level)
