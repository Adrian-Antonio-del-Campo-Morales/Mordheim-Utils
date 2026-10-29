"""Shared variant data and sibling isolation across the declarative corpus.

Sibling variants reuse one declaration through the YAML features the loader
already supports — anchors, aliases and merge keys — instead of a second
templating layer.  An alias makes the *same* object reachable from several
scenarios, so sharing is observable rather than assumed.

This module proves four things about that sharing:

* the corpus really does share variant data between sibling scenarios;
* executing the corpus does not change the shared data it was declared with;
* a sibling's collected result does not depend on the order its siblings ran in;
* editing one variant leaves its siblings' declarations and results intact.

Each scenario still keeps its own identity, its own dice and its own
expectations; sharing data never shares an outcome.
"""
from __future__ import annotations

from copy import deepcopy

from mordheim_knowledge.loader import knowledge_root
from mordheim_modular_e2e.corpus import load_corpus
from mordheim_modular_e2e.execution.dice import EvidenceMismatch
from mordheim_modular_e2e.execution.runner import check_case
import pytest

CORPUS = load_corpus()
BY_IDENTITY = {scenario.test_id: scenario for scenario in CORPUS}


def _containers(value, path=""):
    """Yield every mapping and list reachable from ``value`` with its path."""
    if isinstance(value, dict):
        yield path, value
        for key, item in value.items():
            yield from _containers(item, f"{path}.{key}")
    elif isinstance(value, list):
        yield path, value
        for index, item in enumerate(value):
            yield from _containers(item, f"{path}.{index}")


def shared_variant_data(scenarios):
    """Return the containers two or more scenarios of one document reach as objects.

    YAML resolves an alias to the anchored object itself, so identity sharing is
    exactly what the loader produced from ``&anchor``/``*alias``.  A merge key
    builds a new mapping and therefore shares its *source* with the merged
    sibling instead of the sibling's own mapping.
    """
    groups: dict[tuple[str, int], tuple[object, list[tuple[str, str]]]] = {}
    for scenario in scenarios:
        for path, container in _containers(scenario.case):
            container, reachable = groups.setdefault(
                (scenario.source, id(container)), (container, []))
            reachable.append((scenario.test_id, path))
    return {
        key: value for key, value in groups.items()
        if len({test_id for test_id, _ in value[1]}) > 1
    }


def _sibling_pair():
    """Two scenarios of one document that reach at least one shared container."""
    groups = shared_variant_data(CORPUS)
    assert groups, "the corpus must share variant data through YAML anchors"
    _, reachable = max(groups.values(), key=lambda value: len(value[1]))
    first, second = reachable[0][0], reachable[1][0]
    return BY_IDENTITY[first], BY_IDENTITY[second]


def test_the_corpus_shares_variant_data_between_siblings():
    groups = shared_variant_data(CORPUS)
    assert groups, "no document shares a declaration between two scenarios"
    for (source, _), (container, reachable) in groups.items():
        assert source.endswith(".yaml")
        assert len({test_id for test_id, _ in reachable}) > 1, (
            "a shared declaration must be reachable from sibling scenarios")
        assert deepcopy(container) == container


def _execute_corpus():
    """Attempt every case; individual verdicts remain in test_cases."""
    executed = 0
    for scenario in CORPUS:
        try:
            check_case(scenario.case, knowledge_root())
        except Exception:  # Individual failures must not abort the sharing check.
            continue
        executed += 1
    return executed


def test_executing_the_corpus_does_not_change_shared_variant_data():
    groups = shared_variant_data(CORPUS)
    before = {key: deepcopy(container) for key, (container, _) in groups.items()}
    executed = _execute_corpus()
    assert executed, "no scenario completed; the sharing invariant was not exercised"
    after_groups = shared_variant_data(CORPUS)
    assert set(after_groups) == set(before), (
        "executing the corpus changed which declarations are shared")
    for key, snapshot in before.items():
        assert after_groups[key][0] == snapshot, (
            f"executing the corpus mutated a shared declaration: {key[0]}")


def test_a_sibling_result_does_not_depend_on_the_order_its_siblings_run():
    first, second = _sibling_pair()
    assert first.test_id != second.test_id
    alone = check_case(first.case, knowledge_root())
    check_case(second.case, knowledge_root())
    assert check_case(first.case, knowledge_root()) == alone
    other = check_case(second.case, knowledge_root())
    check_case(first.case, knowledge_root())
    assert check_case(second.case, knowledge_root()) == other


def test_editing_one_variant_leaves_its_siblings_intact():
    edited_source, sibling = _sibling_pair()
    declared = deepcopy(edited_source.case)
    sibling_before = check_case(sibling.case, knowledge_root())

    edited = deepcopy(edited_source.case)
    edited["expect_final"] = {**edited["expect_final"], "rounds_executed": 99}
    try:
        check_case(edited, knowledge_root())
    except EvidenceMismatch as error:
        assert "expected 99" in str(error)
    else:
        raise AssertionError("an edited variant must fail its own wrong expectation")

    assert edited_source.case == declared, "the edited copy was written back into the corpus"
    assert check_case(edited_source.case, knowledge_root()) is not None
    assert check_case(sibling.case, knowledge_root()) == sibling_before, (
        "editing and running one variant changed its sibling's result")
