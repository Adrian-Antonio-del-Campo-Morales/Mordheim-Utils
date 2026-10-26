"""Rule and characteristic edge cases in the vectorized engine."""
from __future__ import annotations

from dataclasses import replace

from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _prepare_weapon_attack
import numpy as np
import pytest as pytest

class SequenceRng:
    def __init__(self, *values):
        self.values = iter(values)

    def integers(self, low, high=None, size=None, dtype=None):
        value = next(self.values)
        return np.full(size if size is not None else (), value, dtype=dtype or np.int64)

def test_spider_infested_penalizes_misses_and_amazons_reroll_against_lizardmen(vector_case):
    spider_case = vector_case("test_rule_families_b/test_spider_infested_penalizes_misses_and_amazons_reroll_against_lizardmen-0-0")
    amazon_case = vector_case("test_rule_families_b/test_spider_infested_penalizes_misses_and_amazons_reroll_against_lizardmen-0-1")
    attacker, spider = spider_case.first, spider_case.second
    attack_state, spider_state = _new_state(attacker, 1, SequenceRng(1)), _new_state(spider, 1, SequenceRng(1))
    _prepare_weapon_attack(attacker, spider, attacker.main_weapon, np.array([0]), np.array([False]),
                           attack_state, spider_state, SequenceRng(1), False)
    assert attack_state.initiative_penalty[0] == 1

    amazon, lizard = amazon_case.first, amazon_case.second
    amazon_state, lizard_state = _new_state(amazon, 1, SequenceRng(1)), _new_state(lizard, 1, SequenceRng(1))
    prepared = _prepare_weapon_attack(amazon, lizard, amazon.main_weapon, np.array([0]), np.array([False]),
                                      amazon_state, lizard_state, SequenceRng(1, 6), True)
    assert prepared is not None and prepared.hit_rows.tolist() == [0]

def test_lazy_characteristics_absent_initiative_and_guiding_dream_modifier(vector_case):
    from mordheim_combat.vectorized._operators import ABSENT_INITIATIVE
    from mordheim_combat.vectorized._operators import characteristic
    from mordheim_combat.vectorized._operators import effective_initiative
    from mordheim_combat.vectorized._operators import guiding_dream_hit_modifier
    from mordheim_combat.vectorized._operators import hit_targets
    from mordheim_combat.vectorized._state import initialize_fighter

    def tagged(fighter, *tags):
        return replace(fighter, global_effects=replace(
            fighter.global_effects,
            tags=tuple(dict.fromkeys((*fighter.global_effects.tags, *tags))),
        ))

    printed = vector_case("test_rule_families_b/test_lazy_characteristics_absent_initiative_and_guiding_dream_modifier-0-0").first

    # An Inconsistency value is drawn by the operation that needs it, on its
    # own row, and the same turn reuses it.
    variable = replace(
        tagged(printed, "mechanic.inconsistency"),
        random_characteristics=(("WS", 1, 6, 0),),
    )
    variable_state = initialize_fighter(
        variable, 2, np.random.default_rng(1), lazy_inconsistency=True,
    )
    assert variable_state.random_rolled.tolist() == [0, 0]
    drawn = characteristic(
        variable, variable_state, np.array([1]), np.random.default_rng(2), "WS",
    )
    assert variable_state.random_rolled.tolist() == [0, 1]
    assert drawn.tolist() == variable_state.weapon_skill[[1]].tolist()
    again = characteristic(
        variable, variable_state, np.array([1]), np.random.default_rng(3), "WS",
    )
    assert again.tolist() == drawn.tolist()

    # A printed blank Initiative sorts after every printed value and is never
    # upgraded by a bonus.
    absent = replace(
        printed, characteristics=replace(printed.characteristics, initiative=None),
    )
    absent_state = initialize_fighter(absent, 2, np.random.default_rng(4))
    present_state = initialize_fighter(printed, 2, np.random.default_rng(5))
    assert absent_state.initiative_missing.tolist() == [True, True]
    absent_initiative = effective_initiative(absent, absent_state)
    assert absent_initiative.tolist() == [ABSENT_INITIATIVE] * 2
    assert absent_initiative[0] < effective_initiative(printed, present_state)[0]

    # Guiding Dream 2-3 grants +1 To Hit against the nominated opposing Hero.
    dreamer = tagged(printed, "condition.guiding-dream-target")
    dream_state = initialize_fighter(dreamer, 2, np.random.default_rng(6))
    dream_state.guiding_dream_result[:] = [2, 6]
    modifier = guiding_dream_hit_modifier(
        dreamer, tagged(printed, "fighter-kind.hero"), dream_state, np.array([0, 1]),
    )
    assert modifier.tolist() == [1, 0]
    assert hit_targets(np.array([3, 3]), np.array([3, 3])).tolist() == [4, 4]
    assert hit_targets(
        np.array([3, 3]), np.array([3, 3]), guiding_dream=modifier,
    ).tolist() == [3, 4]
    with pytest.raises(ValueError, match="Hero"):
        guiding_dream_hit_modifier(dreamer, printed, dream_state, np.array([0]))
