"""The campaign walk over the precompiled catalogue.

These are catalogue contracts, not a statistical campaign: they check the 43
uniform ``scenario/*`` keys, the four names that used to be duplicated, both
multiattack variants, the three cumulative levels and the exact resolution to
the fighters frozen in ``compiled-cases.json``.  No engine is sampled and no
duel is run here.
"""
from collections import Counter

import pytest

from tests.engines.fixtures.precompiled_catalog import LEVELS
from tests.engines.fixtures.precompiled_catalog import LEVEL_SCENARIOS
from tests.engines.fixtures.precompiled_catalog import SCENARIOS
from tests.engines.fixtures.precompiled_catalog import scenarios_for_level
from tools.verification.parity_catalog import CATALOGUE
from tools.verification.parity_catalog import load
from tools.verification.parity_catalog import select


def test_catalogue_holds_43_unique_uniform_keys():
    assert len(CATALOGUE) == 43
    keys = [key for key, _name in CATALOGUE]
    assert len(set(keys)) == 43
    assert all(key.startswith("scenario/") for key in keys)
    assert set(keys) == {f"scenario/{scenario.name}" for scenario in SCENARIOS}


def test_former_duplicate_names_appear_once_and_multiattack_twice():
    names = Counter(name for _key, name in CATALOGUE)
    for name in ("basic", "defences", "stateful", "long"):
        assert names[name] == 1
    assert names["multiattack-a3-t3"] == 1
    assert names["multiattack-a2-t4"] == 1
    assert "multiattack" not in names


def test_levels_are_cumulative_and_big_is_the_catalogue():
    assert LEVELS == ("small", "normal", "big")
    assert {level: len(LEVEL_SCENARIOS[level]) for level in LEVELS} == {
        "small": 8, "normal": 30, "big": 43,
    }
    assert set(LEVEL_SCENARIOS["small"]) <= set(LEVEL_SCENARIOS["normal"])
    assert set(LEVEL_SCENARIOS["normal"]) < set(LEVEL_SCENARIOS["big"])
    assert set(LEVEL_SCENARIOS["big"]) == {scenario.name for scenario in SCENARIOS}


def test_level_names_never_collide_with_scenario_names():
    # A --scenarios value must select the same scenarios in every tool, so no
    # scenario may be named like a level or another reserved selection value.
    reserved = {*LEVELS, "e2e"}
    names = {scenario.name for scenario in SCENARIOS}
    assert reserved.isdisjoint(names)
    assert not any(name.startswith("battery-") for name in names)


def test_level_selection_returns_its_scenarios_in_catalogue_order():
    for level in LEVELS:
        chosen = select((level,))
        assert [entry.name for entry in chosen] == list(LEVEL_SCENARIOS[level])
        assert {entry.kind for entry in chosen} == {"scenario"}
        assert {entry.name for entry in chosen} == {
            scenario.name for scenario in scenarios_for_level(level)
        }
    # Without --scenarios the campaign selects the eight cheap scenarios.
    assert select() == select(("small",))
    assert len(select()) == 8


def test_big_level_keeps_the_expensive_round_limits():
    by_name = {scenario.name: scenario for scenario in scenarios_for_level("big")}
    assert {"long", "heavy-grind"} <= set(by_name)
    assert by_name["long"].maximum_rounds == 75
    assert by_name["heavy-grind"].maximum_rounds == 75
    # ``normal`` stops before the 75-round grinds; only ``big`` carries them.
    normal = {scenario.name for scenario in scenarios_for_level("normal")}
    assert {"long", "heavy-grind"}.isdisjoint(normal)


def test_scenario_values_select_names_keys_and_unions_and_reject_unknowns():
    # Names and corpus keys are the same scenario; the order asked is kept.
    chosen = select(("scenario/long", "basic"))
    assert [entry.key for entry in chosen] == ["scenario/long", "scenario/basic"]
    # A level plus a name outside it is their union, never a narrowing.
    union = select(("normal", "heavy-grind"))
    assert len(union) == 31 and union[-1] == ("scenario/heavy-grind", "heavy-grind", "scenario")
    with pytest.raises(ValueError, match="unknown scenario"):
        select(("scenario/missing",))
    # The retired level names are not levels any more.
    with pytest.raises(ValueError, match="unknown scenario"):
        select(("full",))


def test_every_catalogue_key_resolves_to_its_frozen_case(cases):
    scenarios, rejected = load(select(("big",)), cases)
    assert rejected == ()
    by_key = {scenario.key: scenario for scenario in scenarios}
    assert set(by_key) == {key for key, _name in CATALOGUE}
    for scenario in scenarios:
        assert scenario.case is cases[scenario.key]
        # Scenario entries carry conditions and their round budget only:
        # sample widths, seeds and benchmark metadata are execution config.
        assert scenario.case.limits.simulations is None
        assert scenario.case.limits.seed is None
        assert scenario.case.limits.batch_size is None
        assert scenario.case.benchmark is None
    # Both multiattack variants remain distinct frozen pairs.
    assert (
        by_key["scenario/multiattack-a3-t3"].case.first
        is not by_key["scenario/multiattack-a2-t4"].case.first
    )


def test_a_missing_frozen_case_is_reported_and_never_replaced(cases):
    scenarios, rejected = load(
        select(("basic", "long")),
        {"scenario/basic": cases["scenario/basic"]},
    )
    assert [scenario.key for scenario in scenarios] == ["scenario/basic"]
    assert [key for key, _reason in rejected] == ["scenario/long"]
    assert "no case" in rejected[0][1]


def test_inputs_the_samplers_cannot_pass_on_reject_the_case(cases):
    from dataclasses import replace

    basic = cases["scenario/basic"]
    scenarios, rejected = load(
        select(("basic",)),
        {"scenario/basic": replace(basic, initial_state={"first": {"attacks": 0}})},
    )
    assert scenarios == ()
    assert rejected[0][0] == "scenario/basic"
    assert rejected[0][1].startswith("incompatible: initial_state overrides")


def test_e2e_and_battery_are_named_sets_like_the_levels():
    # Every tool takes the same values: the E2E corpus and the battery are
    # selected whole by name, or one case at a time by key.
    deliveries = select(("e2e",))
    assert len(deliveries) > 2_000 and {entry.kind for entry in deliveries} == {"e2e"}
    battery = select(("battery",))
    assert {entry.kind for entry in battery} == {"battery"}
    assert all(entry.key == f"battery/{entry.name}" for entry in battery)
    one = select((battery[0].key, deliveries[0].key, "basic"))
    assert [entry.kind for entry in one] == ["battery", "e2e", "scenario"]
    with pytest.raises(ValueError, match="unknown scenario"):
        select(("battery/no-such-case",))


def test_loading_reports_every_case_a_tool_cannot_run(cases):
    # Battery cases compile from the knowledge base into frozen-case form; a
    # scripted-decision case is reported instead of run without its script.
    runnable, rejected = load(select(("battery",)), cases)
    assert runnable and all(item.case.fingerprints["inputs_sha256"] for item in runnable)
    reasons = dict(rejected)
    assert any("scripted decisions" in reason for reason in reasons.values())
    assert len(runnable) + len(rejected) == len(select(("battery",)))
