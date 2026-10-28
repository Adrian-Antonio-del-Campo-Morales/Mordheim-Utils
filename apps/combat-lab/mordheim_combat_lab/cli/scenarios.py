"""Compatibility names for the shared, frozen scenario catalogue.

Benchmarking, calibration and parity select the same scenario definitions.
Historical pair-set names remain aliases for the cumulative catalogue levels.
"""
from tests.engines.fixtures.precompiled_catalog import (
    SCENARIOS,
    Scenario as BenchmarkScenario,
    scenarios_for_level,
)

DEEP_SCENARIOS = SCENARIOS
MINI_DEEP_SCENARIO_IDS = tuple(item.name for item in scenarios_for_level("small"))
FAST_DEEP_SCENARIO_IDS = tuple(item.name for item in scenarios_for_level("normal"))
FULL_DEEP_SCENARIO_IDS = tuple(item.name for item in scenarios_for_level("long"))
DEEP_SCENARIO_SET_IDS = {
    "mini": MINI_DEEP_SCENARIO_IDS,
    "fast": FAST_DEEP_SCENARIO_IDS,
    "full": FULL_DEEP_SCENARIO_IDS,
}


def benchmark_scenarios() -> tuple[BenchmarkScenario, ...]:
    """The default, small selection of the shared scenario catalogue."""
    return scenarios_for_level("small")


def deep_test_scenarios(pair_set: str = "full") -> tuple[BenchmarkScenario, ...]:
    """Select the shared levels using historical command-line aliases."""
    try:
        level = {"mini": "small", "fast": "normal", "full": "long"}[pair_set]
    except KeyError as error:
        raise ValueError(
            f"unknown deep pair set {pair_set!r}; choose 'mini', 'fast' or 'full'"
        ) from error
    return scenarios_for_level(level)
