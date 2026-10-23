"""Vectorized regressions of canonical rule families B."""
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


# --- G03 context projections: modular oracle vs vectorized operators ---------

from mordheim_combat import phases as _phases
from mordheim_combat.modular.contexts import (
    _attack_strength as _modular_attack_strength,
    _injury_context as _modular_injury_context,
    _parry_context as _modular_parry_context,
    prepare_armour_context as _modular_armour_context,
    prepare_hit_context as _modular_hit_context,
    prepare_special_save_context as _modular_special_save_context,
    prepare_wound_context as _modular_wound_context,
)
from mordheim_combat.modular.state import initialize_fighter as _modular_initialize
from mordheim_combat.vectorized import _operators as _ops
from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet


class FixedDice:
    """Deterministic dice source so both engines start from equal state."""

    def roll(self, request):
        return 3


def _tagged(fighter, *, global_effects=(), weapon=()):
    changes = {}
    if global_effects:
        changes["global_effects"] = merge_effects(
            fighter.global_effects, EffectSet(tags=tuple(global_effects)),
        )
    if weapon:
        changes["main_weapon"] = merge_effects(
            fighter.main_weapon, EffectSet(tags=tuple(weapon)),
        )
    return replace(fighter, **changes) if changes else fighter


def _mirror(fighter, count=2):
    """Build one modular and one vectorized state with identical values."""
    modular = _modular_initialize(fighter, FixedDice(), "duel")
    vector = _new_state(fighter, count, np.random.default_rng(7))
    for name in ("weapon_skill", "strength", "toughness", "initiative", "attacks"):
        getattr(vector, name)[:] = getattr(modular, name)
    vector.condition[:] = int(modular.condition)
    vector.frenzy[:] = modular.frenzy
    vector.critical_used[:] = not modular.critical_available
    vector.parry_remaining[:] = modular.parries_remaining
    return modular, vector, np.arange(count)


@pytest.mark.phase5_vectorized
def test_hit_context_projection_matches_modular_hatred_hellblade_and_guiding_dream(vector_case):
    case = vector_case("test_rule_families_b/test_hit_context_projection_matches_modular_hatred_hellblade_and_guiding_dream-0-0")
    attacker = _tagged(
        case.first,
        global_effects=(
            "skill.hatred", "condition.guiding-dream-target", "mechanic.guiding-dream",
        ),
        weapon=("weapon.hellblade",),
    )
    defender = _tagged(
        case.second,
        global_effects=("species.beastman", "fighter-kind.hero"),
    )
    modular, vector, rows = _mirror(attacker)
    vector.guiding_dream_result[:] = 2
    effect = merge_effects(attacker.main_weapon, attacker.global_effects)
    expected = _modular_hit_context(
        attacker, defender, modular, _mirror(defender)[0],
        attacker.main_weapon, effect, first_round=True, charging=True,
    )
    actual = _ops.hit_context(
        attacker, defender, vector, _mirror(defender)[1],
        attacker.main_weapon, effect, rows, first_round=True, charging=np.ones(2, dtype=bool),
    )
    assert actual.weapon_skill.tolist() == [expected.attacker_ws] * 2
    assert actual.defender_weapon_skill.tolist() == [expected.defender_ws] * 2
    assert actual.modifier.tolist() == [expected.modifier] * 2
    assert actual.reroll.tolist() == [expected.reroll] * 2
    assert actual.needs_sixes.tolist() == [expected.needs_sixes] * 2

    # Psychology owns the full-batch mask; subset order must survive projection.
    _, vector, _ = _mirror(attacker, count=3)
    rows = np.array([2, 0])
    fear = np.array([True, False, False])
    for melee in (True, False):
        actual = _ops.hit_context(
            attacker, defender, vector, _mirror(defender, count=3)[1],
            attacker.main_weapon, effect, rows, needs_sixes=fear, melee_attack=melee,
        )
        assert actual.needs_sixes.tolist() == [False, melee]
        assert fear.tolist() == [True, False, False]

    # Optional state columns use the same selection, including mixed booleans.
    from types import SimpleNamespace
    attack_view = SimpleNamespace(**{name: getattr(vector, name) for name in vector.__slots__})
    defence = _mirror(defender, count=3)[1]
    defence_view = SimpleNamespace(**{name: getattr(defence, name) for name in defence.__slots__})
    attack_view.fear_hit_sixes = fear
    attack_view.banter_trick_active = fear
    defence_view.banter_trick_active = ~fear
    defence_view.charm_auto_hit = fear
    actual = _ops.hit_context(
        attacker, defender, attack_view, defence_view, attacker.main_weapon, effect, rows,
    )
    base = _ops.hit_context(attacker, defender, vector, defence, attacker.main_weapon, effect, rows)
    assert actual.needs_sixes.tolist() == [False, True]
    assert actual.automatic.tolist() == [False, True]
    assert (actual.modifier - base.modifier).tolist() == [-1, 1]


@pytest.mark.phase5_vectorized
def test_wound_and_armour_projection_match_modular_across_rows(vector_case):
    case = vector_case("test_rule_families_b/test_wound_and_armour_projection_match_modular_across_rows-0-0")
    attacker = _tagged(
        case.first,
        weapon=("effect.wraith-touch",),
    )
    defender = _tagged(
        case.second,
        global_effects=("rule.thin-flesh", "nature.undead"),
    )
    modular_a, vector_a, rows = _mirror(attacker)
    modular_d, vector_d, _ = _mirror(defender)
    effect = merge_effects(attacker.main_weapon, attacker.global_effects)
    expected_wound = _modular_wound_context(
        attacker, defender, modular_a, modular_d, attacker.main_weapon, effect,
        hit_roll=6, first_round=True, charging=True,
    )
    actual_wound = _ops.wound_context(
        attacker, defender, vector_a, vector_d, attacker.main_weapon, effect, rows,
        hit_roll=6, first_round=True, charging=np.ones(2, dtype=bool),
    )
    assert actual_wound.strength.tolist() == [expected_wound.strength] * 2
    assert actual_wound.toughness.tolist() == [expected_wound.toughness] * 2
    assert actual_wound.modifier.tolist() == [expected_wound.modifier] * 2
    assert actual_wound.automatic.tolist() == [expected_wound.automatic] * 2
    assert actual_wound.maximum_target == expected_wound.maximum_target
    assert actual_wound.critical_threshold.tolist() == [expected_wound.critical_threshold] * 2
    assert actual_wound.failure_still_wounds.tolist() == [expected_wound.failure_still_wounds] * 2
    assert actual_wound.unharmed.tolist() == [expected_wound.unharmed] * 2

    expected_armour = _phases.armour_target(_modular_armour_context(
        attacker, defender, modular_a, modular_d, attacker.main_weapon, effect,
        first_round=True, charging=True,
    ))
    actual_armour = _ops.armour_target_values(_ops.armour_context(
        attacker, defender, vector_a, vector_d, attacker.main_weapon, effect, rows,
        first_round=True, charging=np.ones(2, dtype=bool),
    ))
    assert actual_armour.tolist() == [expected_armour] * 2


@pytest.mark.phase5_vectorized
def test_special_save_and_parry_projection_match_modular(vector_case):
    case = vector_case("test_rule_families_b/test_special_save_and_parry_projection_match_modular-0-0")
    attacker = case.first
    defender = _tagged(
        case.second,
        global_effects=("skill.vampire-reflexes",),
    )
    modular_a, vector_a, rows = _mirror(attacker)
    modular_d, vector_d, _ = _mirror(defender)
    incoming = EffectSet(tags=("attack.magical",))
    expected_save = _modular_special_save_context(
        defender, incoming, defender_state=modular_d,
    )
    actual_save = _ops.special_save_context(defender, incoming, vector_d, rows)
    assert actual_save.ward_save.tolist() == [expected_save.ward_save] * 2
    assert actual_save.regeneration_save.tolist() == [expected_save.regeneration_save] * 2
    assert actual_save.ward_blocked.tolist() == [expected_save.ward_blocked] * 2
    assert actual_save.regeneration_blocked.tolist() == [expected_save.regeneration_blocked] * 2
    assert actual_save.ward_unmodifiable.tolist() == [expected_save.ward_unmodifiable] * 2

    effect = merge_effects(attacker.main_weapon, attacker.global_effects)
    expected_parry = _modular_parry_context(
        defender, modular_d, effect, expected_save.ward_save, 4, "test",
    )
    actual_parry = _ops.parry_context(
        defender, vector_d, effect, np.full(2, expected_save.ward_save), np.full(2, 4), rows,
    )
    assert actual_parry.eligible.tolist() == [expected_parry is not None] * 2
    assert actual_parry.match_allowed == expected_parry.match_allowed
    assert actual_parry.fixed_target == expected_parry.fixed_target
    assert actual_parry.reroll.tolist() == [expected_parry.reroll] * 2
    assert actual_parry.can_parry_six == expected_parry.can_parry_six

    # One row's dodge cannot unblock a mundane-only ward on another row.
    rows = np.array([2, 0])
    dodge = np.array([True, False, False])
    _, vector_d, _ = _mirror(defender, count=3)
    for tags in ((), ("condition.djinns-luck-active",), ("mechanic.gypsy-ward",)):
        bearer = replace(defender, global_effects=replace(
            defender.global_effects, ward_save=5, ward_save_mundane_only=True,
            tags=(*defender.global_effects.tags, *tags),
        ))
        actual = _ops.special_save_context(
            bearer, incoming, vector_d, rows, dodge_trick_active=dodge,
        )
        expected = [
            _modular_special_save_context(
                bearer, incoming,
                defender_state=replace(modular_d, dodge_trick_active=bool(dodge[row])),
            ) for row in rows
        ]
        for name in ("ward_save", "ward_blocked", "ward_unmodifiable"):
            assert getattr(actual, name).tolist() == [getattr(item, name) for item in expected]
        assert dodge.tolist() == [True, False, False]


@pytest.mark.phase5_vectorized
def test_injury_projection_matches_modular_table_on_divergent_rows(vector_case):
    case = vector_case("test_rule_families_b/test_injury_projection_matches_modular_table_on_divergent_rows-0-0")
    defender = _tagged(
        case.first,
        global_effects=("mechanic.bat-injury-chart",),
    )
    effect = EffectSet(
        tags=("weapon.count-of-ventimiglias-misericordia",),
        injury_modifier=1,
    )
    modular, vector, rows = _mirror(defender)
    vector.condition[0] = _phases.Condition.STANDING
    vector.condition[1] = _phases.Condition.KNOCKED_DOWN
    expected_context = _modular_injury_context(defender, effect, "test", modular)
    actual_context = _ops.injury_context(defender, effect, vector, rows)
    totals = np.arange(1, 8)
    expected = np.array([
        _phases.injury_condition(int(total), expected_context) for total in totals
    ], dtype=np.int8)
    assert actual_context.modifier.tolist() == [expected_context.modifier] * 2
    assert actual_context.out_threshold.tolist() == [expected_context.out_threshold] * 2
    assert actual_context.stun_threshold.tolist() == [expected_context.stun_threshold] * 2
    matrix = np.tile(totals, (2, 1))
    assert _ops.injury_results(matrix, actual_context)[0].tolist() == expected.tolist()
