"""Integrity of catalogue references to the frozen engine corpus."""
import pytest

from mordheim_core.models import CompiledFighter
from tests.engines.fixtures.precompiled_catalog import (
    benchmark_case_key,
    benchmark_scenarios,
    deep_test_scenarios,
    parity_case_key,
)


# The scenarios are only usable if construction admits them. The frozen corpus
# is that proof: every benchmark and deep scenario has its precompiled pair and
# the round budget the scenario declares, so the assertion is the presence of
# the admitted inputs, not a compiled field.
@pytest.mark.performance
def test_suite_scenarios_are_admitted_by_the_frozen_corpus(cases):
    for scenario in benchmark_scenarios():
        case = cases[benchmark_case_key(scenario.id)]
        assert isinstance(case.first, CompiledFighter)
        assert isinstance(case.second, CompiledFighter)
        assert case.limits.maximum_rounds == scenario.maximum_rounds
        assert case.benchmark is not None
    for scenario in deep_test_scenarios():
        case = cases[parity_case_key(scenario.id)]
        assert isinstance(case.first, CompiledFighter)
        assert isinstance(case.second, CompiledFighter)
        assert case.limits.maximum_rounds == scenario.maximum_rounds
