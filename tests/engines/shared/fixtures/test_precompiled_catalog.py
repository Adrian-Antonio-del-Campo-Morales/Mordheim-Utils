"""Integrity of the scenario catalogue against the frozen engine corpus."""
from mordheim_core.models import CompiledFighter
from tests.engines.fixtures.precompiled_catalog import LEVELS
from tests.engines.fixtures.precompiled_catalog import LEVEL_SCENARIOS
from tests.engines.fixtures.precompiled_catalog import SCENARIOS
from tests.engines.fixtures.precompiled_catalog import scenario_key


# The scenarios are only usable if construction admits them. The frozen corpus
# is that proof: every scenario of every level has its precompiled pair and the
# round budget the definition declares, so the assertion is the presence of the
# admitted inputs, not a compiled field.
def test_every_level_is_admitted_by_the_frozen_corpus(cases):
    by_name = {scenario.name: scenario for scenario in SCENARIOS}
    for level in LEVELS:
        for name in LEVEL_SCENARIOS[level]:
            case = cases[scenario_key(name)]
            assert isinstance(case.first, CompiledFighter)
            assert isinstance(case.second, CompiledFighter)
            assert case.limits.maximum_rounds == by_name[name].maximum_rounds
