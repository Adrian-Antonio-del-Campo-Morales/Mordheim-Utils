import pytest

from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios


def test_benchmark_suite_has_the_five_required_scenarios():
    assert {item.id for item in benchmark_scenarios()} == {
        "basic", "multiattack", "defences", "stateful", "long",
    }


def test_deep_suite_extends_the_five_core_scenarios():
    ids = {item.id for item in deep_test_scenarios()}
    assert {item.id for item in benchmark_scenarios()} <= ids
    assert len(ids) >= 10


def test_deep_pair_sets_are_stable_and_fast_is_a_full_subset():
    full = deep_test_scenarios("full")
    fast = deep_test_scenarios("fast")
    mini = deep_test_scenarios("mini")
    full_ids = {item.id for item in full}
    assert len(full) == 42
    assert len(fast) == 30
    assert len(mini) == 10
    assert {item.id for item in fast} <= full_ids
    assert {item.id for item in mini} <= full_ids
    assert len(full_ids) == len(full)
    with pytest.raises(ValueError, match="choose 'mini', 'fast' or 'full'"):
        deep_test_scenarios("unknown")


def test_deep_suite_scenarios_compile_into_legal_duels():
    from mordheim_construction.compiler import compile_fighter
    for scenario in deep_test_scenarios():
        compile_fighter(scenario.first)
        compile_fighter(scenario.second)
