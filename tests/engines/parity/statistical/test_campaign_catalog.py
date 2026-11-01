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


def test_levels_are_cumulative_and_long_is_the_catalogue():
    assert LEVELS == ("small", "normal", "long")
    assert {level: len(LEVEL_SCENARIOS[level]) for level in LEVELS} == {
        "small": 8, "normal": 30, "long": 43,
    }
    assert set(LEVEL_SCENARIOS["small"]) <= set(LEVEL_SCENARIOS["normal"])
    assert set(LEVEL_SCENARIOS["normal"]) < set(LEVEL_SCENARIOS["long"])
    assert set(LEVEL_SCENARIOS["long"]) == {scenario.name for scenario in SCENARIOS}


def test_level_selection_returns_its_scenarios_in_catalogue_order():
    for level in LEVELS:
        chosen = select(level=level)
        assert [name for _key, name in chosen] == list(LEVEL_SCENARIOS[level])
        assert {name for _key, name in chosen} == {
            scenario.name for scenario in scenarios_for_level(level)
        }
    # Without a level the campaign selects the eight cheap scenarios.
    assert select() == select(level="small")
    assert len(select()) == 8


def test_long_level_keeps_the_expensive_round_limits():
    by_name = {scenario.name: scenario for scenario in scenarios_for_level("long")}
    assert {"long", "heavy-grind"} <= set(by_name)
    assert by_name["long"].maximum_rounds == 75
    assert by_name["heavy-grind"].maximum_rounds == 75
    # ``normal`` stops before the 75-round grinds; only ``long`` carries them.
    normal = {scenario.name for scenario in scenarios_for_level("normal")}
    assert {"long", "heavy-grind"}.isdisjoint(normal)


def test_explicit_keys_keep_order_and_reject_unknown_or_out_of_level_keys():
    chosen = select(level="long", keys=("scenario/long", "scenario/basic"))
    assert [key for key, _name in chosen] == ["scenario/basic", "scenario/long"]
    with pytest.raises(ValueError, match="not selected"):
        select(keys=("scenario/missing",))
    with pytest.raises(ValueError, match="not selected"):
        select(level="normal", keys=("scenario/heavy-grind",))
    with pytest.raises(ValueError, match="unknown level"):
        select(level="full")


def test_every_catalogue_key_resolves_to_its_frozen_case(cases):
    scenarios, rejected = load(select(level="long"), cases)
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
        select(level="long", keys=("scenario/basic", "scenario/long")),
        {"scenario/basic": cases["scenario/basic"]},
    )
    assert [scenario.key for scenario in scenarios] == ["scenario/basic"]
    assert [key for key, _reason in rejected] == ["scenario/long"]
    assert "no case" in rejected[0][1]
