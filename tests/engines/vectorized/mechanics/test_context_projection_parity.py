"""Context-projection parity between the modular oracle and vectorized operators."""
from __future__ import annotations

from dataclasses import replace

from mordheim_combat import phases as _phases
from mordheim_combat.modular.contexts import (
    _injury_context as _modular_injury_context,
    _parry_context as _modular_parry_context,
    prepare_armour_context as _modular_armour_context,
    prepare_hit_context as _modular_hit_context,
    prepare_special_save_context as _modular_special_save_context,
    prepare_wound_context as _modular_wound_context,
)
from mordheim_combat.modular.state import initialize_fighter as _modular_initialize
from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _operators as _ops
from mordheim_core.effects import merge_effects
from mordheim_core.models import EffectSet
import numpy as np
import pytest as pytest

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
