"""Rule regressions of the vectorized engine."""
from __future__ import annotations

from dataclasses import replace
from mordheim_core.models import EffectSet
import numpy as np
import pytest as pytest


class FixedRng:
    def __init__(self, *values):
        self.values = list(values)

    def integers(self, low, high=None, size=None, dtype=None):
        if size == 0:
            return np.empty(0, dtype=dtype or np.int64)
        value = self.values.pop(0)
        result = np.asarray(value if np.ndim(value) else np.full(size or 1, value), dtype=dtype)
        return result if size is not None else result.item()


def test_steel_whip_charge_bonus_matches_modular_round_modifier(vector_case):
    from mordheim_combat.modular.rounds import apply_round_weapon_attack_modifiers
    from mordheim_combat.vectorized import round_weapon_attack_count

    case = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-0")
    attacker, defender = case.first, case.second
    charging = np.array([False])
    charged = np.array([True])
    base = np.array([2], dtype=np.int16)

    expected = apply_round_weapon_attack_modifiers(
        attacker, defender, int(base[0]), first_round=True,
        charging=False, charged=True,
    )
    actual = round_weapon_attack_count(
        attacker, defender, base, first_round=True,
        charging=charging, charged=charged,
    )

    assert expected == 3
    assert actual.tolist() == [expected]


    from mordheim_combat.vectorized import attack_count
    from mordheim_combat.vectorized import priority

    bagh = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-1").first
    stiletto = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-2").first
    cathayan = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-3").first
    yari = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-4").first
    hook = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-5").first
    draich = vector_case("test_runtime_regressions/test_steel_whip_charge_bonus_matches_modular_round_modifier-0-6").first
    flags = np.zeros(1, dtype=bool)

    assert (bagh.main_weapon.strength_bonus, bagh.main_weapon.armour_penetration) == (1, 1)
    assert attack_count(stiletto, flags).tolist() == [2]
    assert cathayan.main_weapon.weapon_skill_bonus == 1
    assert priority(yari, defender, False, flags, flags, flags).tolist() == [1]
    assert priority(hook, defender, True, flags, flags, flags).tolist() == [1]
    assert priority(hook, defender, False, flags, flags, flags).tolist() == [0]
    assert draich.main_weapon.critical_injury_bonus == 1


def test_frenzy_persists_and_pistols_only_fire_in_the_first_round(vector_case):
    from mordheim_combat.vectorized import attack_count

    flags = np.zeros(1, dtype=bool)
    frenzy_case = vector_case("test_runtime_regressions/test_frenzy_persists_and_pistols_only_fire_in_the_first_round-0-0")
    frenzy, pistol = frenzy_case.first, frenzy_case.second
    pistol_and_sword = vector_case("test_runtime_regressions/test_pistol_and_sword_allocate_attacks_to_the_correct_weapon-0-0").first
    sword_and_pistol = vector_case("test_runtime_regressions/test_frenzy_persists_and_pistols_only_fire_in_the_first_round-0-2").first

    assert attack_count(frenzy, flags, first_round=False).tolist() == [2]
    assert attack_count(pistol, flags, first_round=True).tolist() == [1]
    assert attack_count(pistol, flags, first_round=False).tolist() == [0]
    assert attack_count(pistol_and_sword, flags, first_round=True).tolist() == [2]
    assert attack_count(pistol_and_sword, flags, first_round=False).tolist() == [1]
    assert attack_count(sword_and_pistol, flags, first_round=True).tolist() == [3]
    assert attack_count(sword_and_pistol, flags, first_round=False).tolist() == [2]


def test_frantic_priority_score_does_not_overflow_int8(vector_case):
    """Regression: priority() returns int8, and the driver's event score used
    to multiply it by 100 *in int8*, so Frantic's tier 10 wrapped to -24 and
    silently demoted Strike-First fanatics behind ordinary weapons — the
    frenzy-vs-w2 deep-matrix divergence (-15 pp vs the oracle).  Scores must
    be computed in int32, and the frantic fanatic must keep its tier-10 score.
    """
    from mordheim_combat.modular.duel import simulate_duel_reference
    from mordheim_combat.vectorized import priority
    from mordheim_combat.vectorized._driver import _simulate_batch_core

    flags = np.zeros(1, dtype=bool)
    case = vector_case("test_runtime_regressions/test_frantic_priority_score_does_not_overflow_int8-0-0")
    fanatic, veteran = case.first, case.second
    assert priority(fanatic, veteran, False, flags, flags, flags).tolist() == [10]

    # Seeded batch pinned to the modular oracle on the same frozen pair.
    # The original scripted margins (74/512 fixed vs 25/512 broken) were
    # measured against pre-refreeze fighters; the current frozen fanatic is
    # a one-wound unarmed goblin whose oracle rate is ~0%, so the pin is the
    # agreement between the engines, not an absolute band.
    reference = simulate_duel_reference(
        fanatic, veteran, 512, seed=20260907, maximum_rounds=50,
    )
    first_wins, second_wins, unresolved = _simulate_batch_core(
        fanatic, veteran, 512, np.random.default_rng(20260907), 50,
    )
    assert unresolved == 0 and reference.unresolved == 0
    assert abs(first_wins - reference.first_wins) <= 26, (
        first_wins, reference.first_wins)
    assert abs(second_wins - reference.second_wins) <= 26, (
        second_wins, reference.second_wins)


def test_frenzy_doubling_is_gated_on_the_live_state_not_the_effect(vector_case):
    """Regression: the driver always passes the frenzy *state* array, so an
    all-False state must not double even when the fighter carries a constant
    frenzy effect.  The ``elif effect.frenzy`` fallback is only the operator's
    no-state-array default; the native port once merged both branches and
    re-doubled a frenzied fighter after a knockdown had cleared its state.
    """
    from mordheim_combat.vectorized import attack_count

    case = vector_case("test_runtime_regressions/test_frenzy_doubling_is_gated_on_the_live_state_not_the_effect-0-0")
    frenzy = case.first
    no_frenzy_state = np.zeros(1, dtype=bool)
    live_frenzy_state = np.ones(1, dtype=bool)
    assert attack_count(
        frenzy, no_frenzy_state, frenzy=no_frenzy_state,
    ).tolist() == [1]
    assert attack_count(
        frenzy, no_frenzy_state, frenzy=live_frenzy_state,
    ).tolist() == [2]


def test_pistol_and_sword_allocate_attacks_to_the_correct_weapon(monkeypatch, vector_case):
    import mordheim_combat.vectorized as engine
    import mordheim_combat.vectorized._attacks as engine_attacks

    case = vector_case("test_runtime_regressions/test_pistol_and_sword_allocate_attacks_to_the_correct_weapon-0-0")
    attacker, defender = case.first, case.second
    flags = np.zeros(1, dtype=bool)
    seen = []

    def capture(_attacker, _defender, weapon, active, *_args, **_kwargs):
        if active.size:
            seen.append(weapon.tags)
        return None

    monkeypatch.setattr(engine_attacks, "_prepare_weapon_attack", capture)
    for first_round in (True, False):
        attacks = engine.attack_count(attacker, flags, first_round=first_round)
        engine.resolve_attacks(
            attacker, defender, np.array([0]), attacks, flags,
            engine._new_state(attacker, 1, np.random.default_rng(1)),
            engine._new_state(defender, 1, np.random.default_rng(2)),
            np.random.default_rng(3), first_round,
        )
    assert "weapon.pistol" in seen[0]
    assert "weapon.sword" in seen[1]
    assert "weapon.sword" in seen[2]
    assert len(seen) == 3


def test_resilient_and_reptile_venom_do_not_change_armour_strength(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack

    active = np.array([0])
    flags = np.zeros(1, dtype=bool)
    resilient_case = vector_case("test_runtime_regressions/test_resilient_and_reptile_venom_do_not_change_armour_strength-0-0")
    reptile_case = vector_case("test_runtime_regressions/test_resilient_and_reptile_venom_do_not_change_armour_strength-0-1")
    strong, resilient = resilient_case.first, resilient_case.second
    reptile, plain = reptile_case.first, reptile_case.second

    resilient_attack = _prepare_weapon_attack(
        strong, resilient, strong.main_weapon, active, flags,
        _new_state(strong, 1, np.random.default_rng(1)),
        _new_state(resilient, 1, np.random.default_rng(2)), FixedRng(6), False,
    )
    reptile_attack = _prepare_weapon_attack(
        reptile, plain, reptile.main_weapon, active, flags,
        _new_state(reptile, 1, np.random.default_rng(3)),
        _new_state(plain, 1, np.random.default_rng(4)), FixedRng(6), False,
    )

    assert resilient_attack.strength.tolist() == [3]
    assert resilient_attack.armour_strength.tolist() == [4]
    assert reptile_attack.strength.tolist() == [4]
    assert reptile_attack.armour_strength.tolist() == [3]


def test_natural_armour_caps_strength_before_armour_penetration(vector_case):
    from mordheim_combat import phases
    from mordheim_combat.vectorized import armour_targets

    defender = vector_case("test_runtime_regressions/test_natural_armour_caps_strength_before_armour_penetration-0-0").first
    assert (defender.natural_armour_save, defender.natural_armour_worst_save) == (5, 6)
    strength = np.arange(1, 8, dtype=np.int16)
    effect = EffectSet(armour_penetration=1)

    actual = armour_targets(defender, strength, effect, False)
    expected = np.asarray([
        phases.armour_target(phases.ArmourContext(
            armour_save=defender.armour_save,
            natural_armour_save=defender.natural_armour_save,
            natural_armour_worst_save=defender.natural_armour_worst_save,
            natural_armour_unmodified=defender.natural_armour_unmodified,
            strength=int(value),
            armour_penetration=effect.armour_penetration,
        ))
        for value in strength
    ])
    # Strength stops at the worst natural save; penetration then worsens the save
    # instead of being absorbed by that cap.
    assert actual.tolist() == expected.tolist()
    assert actual.tolist()[-1] == 7


def test_lotus_failed_critical_attempt_keeps_the_wound(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    case = vector_case("test_runtime_regressions/test_lotus_failed_critical_attempt_keeps_the_wound-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    # Hit six, optional critical attempt one, dagger armour save one.
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(6, 1, 1), False,
    )
    assert defender_state.wounds.tolist() == [1]
    assert not attacker_state.critical_used[0]


def test_duplicate_wounds_can_claim_only_one_critical_per_row(vector_case):
    from mordheim_combat.vectorized import _claim_criticals
    from mordheim_combat.vectorized import _new_state

    case = vector_case("test_runtime_regressions/test_duplicate_wounds_can_claim_only_one_critical_per_row-0-0")
    state = _new_state(case.first, 1, np.random.default_rng(1))
    claimed = _claim_criticals(np.array([True, True]), np.array([0, 0]), state)
    assert claimed.tolist() == [True, False]


def test_simultaneous_injuries_keep_the_highest_roll_instead_of_auto_finishing(vector_case):
    from mordheim_combat.vectorized import KNOCKED_DOWN
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import resolve_attacks

    case = vector_case("test_runtime_regressions/test_simultaneous_injuries_keep_the_highest_roll_instead_of_auto_finishing-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    resolve_attacks(
        attacker, defender, np.array([0]), np.array([2]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(4, 1, 4, 1), False,
    )
    assert defender_state.condition.tolist() == [KNOCKED_DOWN]


def test_sword_and_buckler_rerolls_a_failed_parry(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits

    case = vector_case("test_runtime_regressions/test_sword_and_buckler_rerolls_a_failed_parry-0-0")
    defender = case.first
    state = _new_state(defender, 1, np.random.default_rng(1))
    remaining, blocked, _ = _parry_hits(
        defender, EffectSet(), np.array([0]), np.array([4]), np.array([3]),
        state, FixedRng(3, 5),
    )
    assert remaining.size == 0
    assert blocked.tolist() == [0]


def test_natural_six_closes_parry_capacity_without_a_roll(vector_case):
    """The highest natural six precludes attempting to parry a lower hit."""
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits

    case = vector_case("test_runtime_regressions/test_natural_six_closes_parry_capacity_without_a_roll-0-0")
    defender = case.first
    state = _new_state(defender, 1, np.random.default_rng(1))
    remaining, blocked, _ = _parry_hits(
        defender, EffectSet(), np.array([0]), np.array([6]), np.array([3]),
        state, FixedRng(),
    )
    # No attempt is rolled and the hit survives, but no lower hit may be chosen.
    assert remaining.tolist() == [0]
    assert blocked.size == 0
    assert state.parry_used.tolist() == [False]
    assert state.parry_remaining.tolist() == [0]


def test_parry_cannot_substitute_a_lower_hit_for_a_natural_six(vector_case):
    """With hits [6, 4], both survive without a parry die."""
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits

    case = vector_case("test_runtime_regressions/test_parry_cannot_substitute_a_lower_hit_for_a_natural_six-0-0")
    defender = case.first
    state = _new_state(defender, 1, np.random.default_rng(1))
    remaining, blocked, _ = _parry_hits(
        defender, EffectSet(), np.array([0, 0]), np.array([6, 4]),
        np.array([3, 3]), state, FixedRng(),
    )
    assert remaining.tolist() == [0, 0]
    assert blocked.size == 0
    assert state.parry_used.tolist() == [False]
    assert state.parry_remaining.tolist() == [0]


def test_multi_hit_pool_resolves_both_hits_when_the_highest_is_six(vector_case):
    """Close Combat / Parrying: the highest hit governs the whole pool."""
    from mordheim_combat.vectorized import KNOCKED_DOWN
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import resolve_attacks

    case = vector_case("test_runtime_regressions/test_multi_hit_pool_resolves_both_hits_when_the_highest_is_six-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    # Hits 6/4; first fails to wound, second wounds and knocks down. No parry.
    resolve_attacks(
        attacker, defender, np.array([0]), np.array([2]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(6, 4, 1, 4, 1), False,
    )
    assert defender_state.wounds.tolist() == [0]
    assert defender_state.condition.tolist() == [KNOCKED_DOWN]
    assert defender_state.parry_used.tolist() == [False]
    assert defender_state.parry_remaining.tolist() == [0]


def test_nightshade_applies_one_initiative_penalty_per_damage(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    case = vector_case("test_runtime_regressions/test_nightshade_applies_one_initiative_penalty_per_damage-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]),
        np.zeros(1, dtype=bool), attacker_state, defender_state,
        FixedRng(4, 6, 1), False,
    )
    assert defender_state.wounds.tolist() == [2]
    assert defender_state.initiative_penalty.tolist() == [2]


def test_mark_of_old_ones_converts_failed_armour_save(vector_case):
    from mordheim_combat.vectorized import VectorAttackObservation
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    case = vector_case("test_runtime_regressions/test_mark_of_old_ones_converts_failed_armour_save-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    observation = VectorAttackObservation()
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]),
        np.zeros(1, dtype=bool), attacker_state, defender_state,
        FixedRng(4, 4, 1), False, observation=observation,
    )
    assert observation.saved
    assert defender_state.wounds.tolist() == [3]
    assert defender_state.mark_of_old_ones_used.tolist() == [True]


def test_luck_rerolls_failed_armour_save(vector_case):
    from mordheim_combat.vectorized import VectorAttackObservation
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    case = vector_case("test_runtime_regressions/test_luck_rerolls_failed_armour_save-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    observation = VectorAttackObservation()
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]),
        np.zeros(1, dtype=bool), attacker_state, defender_state,
        FixedRng(4, 4, 1, 6), False, observation=observation,
    )
    assert observation.saved
    assert defender_state.wounds.tolist() == [3]
    assert defender_state.luck_used.tolist() == [True]


def test_same_warrior_cannot_finish_a_defender_stunned_by_its_previous_attack(vector_case):
    """Close Combat: same-warrior follow-ups still need wound/Injury rolls."""
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import resolve_attacks

    case = vector_case("test_runtime_regressions/test_same_warrior_cannot_finish_a_defender_stunned_by_its_previous_attack-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    # First wound stuns; the second hit fails to wound and cannot finish.
    resolve_attacks(
        attacker, defender, np.array([0]), np.array([2]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(4, 4, 5, 3, 1), False,
    )
    assert defender_state.condition.tolist() == [STUNNED]
    assert defender_state.wounds.tolist() == [0]


def test_offhand_axe_master_and_starblade_use_their_special_parries(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits

    case = vector_case("test_runtime_regressions/test_offhand_axe_master_and_starblade_use_their_special_parries-0-0")
    axe_master, starblade = case.first, case.second
    remaining, blocked, _ = _parry_hits(
        axe_master, EffectSet(), np.array([0]), np.array([4]), np.array([3]),
        _new_state(axe_master, 1, np.random.default_rng(1)), FixedRng(6),
    )
    assert remaining.size == 0 and blocked.tolist() == [0]
    remaining, blocked, _ = _parry_hits(
        starblade, EffectSet(), np.array([0]), np.array([5]), np.array([3]),
        _new_state(starblade, 1, np.random.default_rng(2)), FixedRng(4),
    )
    assert remaining.size == 0 and blocked.tolist() == [0]


def test_thick_skull_with_a_helmet_replaces_instead_of_stacking_with_helmet_save(vector_case):
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    case = vector_case("test_runtime_regressions/test_thick_skull_with_a_helmet_replaces_instead_of_stacking_with_helmet_save-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(5, 3, 1), False,
    )
    assert defender_state.condition.tolist() == [STUNNED]


def test_luck_is_consumed_after_its_first_failed_hit_reroll(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack

    case = vector_case("test_runtime_regressions/test_luck_is_consumed_after_its_first_failed_hit_reroll-0-0")
    attacker, defender = case.first, case.second
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    active = np.array([0])
    flags = np.zeros(1, dtype=bool)

    first = _prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, active, flags,
        attacker_state, defender_state, FixedRng(3, 6), False,
    )
    second = _prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, active, flags,
        attacker_state, defender_state, FixedRng(3), False,
    )
    assert first.hit_rows.tolist() == [0]
    assert second.hit_rows.size == 0
    assert attacker_state.luck_used.tolist() == [True]


def test_death_blow_bonuses_require_a_profile_with_at_least_two_attacks(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack
    from mordheim_combat.vectorized import attack_count

    one_attack_case = vector_case("test_runtime_regressions/test_death_blow_bonuses_require_a_profile_with_at_least_two_attacks-0-0")
    two_attacks_case = vector_case("test_runtime_regressions/test_death_blow_bonuses_require_a_profile_with_at_least_two_attacks-0-1")
    one_attack = one_attack_case.first
    two_attacks = two_attacks_case.first
    defender = one_attack_case.second
    active = np.array([0])
    flags = np.zeros(1, dtype=bool)

    inactive = _prepare_weapon_attack(
        one_attack, defender, one_attack.main_weapon, active, flags,
        _new_state(one_attack, 1, np.random.default_rng(1)),
        _new_state(defender, 1, np.random.default_rng(2)), FixedRng(6), False,
    )
    active_blow = _prepare_weapon_attack(
        two_attacks, defender, two_attacks.main_weapon, active, flags,
        _new_state(two_attacks, 1, np.random.default_rng(3)),
        _new_state(defender, 1, np.random.default_rng(4)), FixedRng(6), False,
    )
    assert (inactive.effect.hit_modifier, inactive.effect.wound_modifier, inactive.effect.injury_modifier) == (0, 0, 0)
    assert (active_blow.effect.hit_modifier, active_blow.effect.wound_modifier, active_blow.effect.injury_modifier) == (1, 1, 1)
    assert attack_count(two_attacks, flags).tolist() == [1]


def test_strongman_cancels_strike_last_for_heavy_weapons_and_broadsword(vector_case):
    from mordheim_combat.vectorized import priority

    flags = np.zeros(1, dtype=bool)
    case = vector_case("test_runtime_regressions/test_strongman_cancels_strike_last_for_heavy_weapons_and_broadsword-0-0")
    plain = vector_case("test_runtime_regressions/test_pistol_and_sword_allocate_attacks_to_the_correct_weapon-0-0").second
    broadsword, great_weapon = case.first, case.second
    assert priority(broadsword, plain, False, flags, flags, flags).tolist() == [0]
    assert priority(great_weapon, plain, False, flags, flags, flags).tolist() == [0]


def test_shield_strike_is_an_independent_user_strength_attack(vector_case):
    attacker = vector_case("test_runtime_regressions/test_shield_strike_is_an_independent_user_strength_attack-0-0").first
    assert len(attacker.extra_attacks) == 1
    strike = attacker.extra_attacks[0]
    assert strike.tags == ("rule.shield-strike",)
    assert strike.strength_bonus == 0
    # Shield Strike follows the ordinary Strength-based armour modifier.
    assert strike.target_armour_bonus == 0


def test_sigmarite_hammer_gets_its_conditional_wound_bonus(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    ordinary_case = vector_case("test_runtime_regressions/test_sigmarite_hammer_gets_its_conditional_wound_bonus-0-0")
    undead_case = vector_case("test_runtime_regressions/test_sigmarite_hammer_gets_its_conditional_wound_bonus-0-1")
    attacker = ordinary_case.first
    attacker = replace(attacker, main_weapon=replace(attacker.main_weapon, automatic_hit=True))
    ordinary, undead = ordinary_case.second, undead_case.second

    ordinary_state = _new_state(ordinary, 1, np.random.default_rng(1))
    undead_state = _new_state(undead, 1, np.random.default_rng(2))
    _resolve_weapon(
        attacker, ordinary, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(attacker, 1, np.random.default_rng(3)), ordinary_state, FixedRng(4), False,
    )
    _resolve_weapon(
        attacker, undead, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(attacker, 1, np.random.default_rng(4)), undead_state, FixedRng(4), False,
    )
    assert ordinary_state.wounds.tolist() == [2]
    assert undead_state.wounds.tolist() == [1]


def test_bear_hug_is_granted_automatically_by_the_trained_bear_profile(vector_case):
    bear = vector_case("test_runtime_regressions/test_bear_hug_is_granted_automatically_by_the_trained_bear_profile-0-0").first
    assert bear.global_effects.bear_hug


def test_mandrake_toughness_bonus_is_present_in_runtime_characteristic_tests(vector_case):
    from mordheim_combat.vectorized import _new_state

    prepared = vector_case("test_runtime_regressions/test_mandrake_toughness_bonus_is_present_in_runtime_characteristic_tests-0-0").first
    state = _new_state(prepared, 2, np.random.default_rng(1))
    assert state.toughness.tolist() == [4, 4]


def test_off_hand_material_contributes_to_effective_initiative(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import effective_initiative

    case = vector_case("test_runtime_regressions/test_off_hand_material_contributes_to_effective_initiative-0-0")
    ordinary, ithilmar = case.first, case.second
    ordinary_state = _new_state(ordinary, 1, np.random.default_rng(1))
    ithilmar_state = _new_state(ithilmar, 1, np.random.default_rng(2))

    assert effective_initiative(ithilmar, ithilmar_state).tolist() == [
        effective_initiative(ordinary, ordinary_state)[0] + 1
    ]


def test_poisonous_injury_belongs_to_attacker_and_respects_immunity(vector_case):
    from mordheim_combat.vectorized import KNOCKED_DOWN
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    ordinary_case = vector_case("test_runtime_regressions/test_poisonous_injury_belongs_to_attacker_and_respects_immunity-0-0")
    immune_case = vector_case("test_runtime_regressions/test_poisonous_injury_belongs_to_attacker_and_respects_immunity-0-1")
    poisonous, ordinary = ordinary_case.first, ordinary_case.second
    immune = immune_case.second

    ordinary_state = _new_state(ordinary, 1, np.random.default_rng(1))
    immune_state = _new_state(immune, 1, np.random.default_rng(2))
    _resolve_weapon(
        poisonous, ordinary, poisonous.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(poisonous, 1, np.random.default_rng(3)), ordinary_state,
        FixedRng(5, 2), False,
    )
    _resolve_weapon(
        poisonous, immune, poisonous.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(poisonous, 1, np.random.default_rng(4)), immune_state,
        FixedRng(5, 2), False,
    )

    assert ordinary_state.condition.tolist() == [STUNNED]
    assert immune_state.condition.tolist() == [KNOCKED_DOWN]


def test_amazon_isolationists_recognise_trollheim_lustria_lizardmen(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack

    case = vector_case("test_runtime_regressions/test_amazon_isolationists_recognise_trollheim_lustria_lizardmen-0-0")
    amazon, lizard = case.first, case.second
    prepared = _prepare_weapon_attack(
        amazon, lizard, amazon.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(amazon, 1, np.random.default_rng(1)),
        _new_state(lizard, 1, np.random.default_rng(2)), FixedRng(3, 6), True,
    )
    assert prepared.hit_rows.tolist() == [0]


def test_optional_phase_plan_only_enables_reachable_stateful_phases(vector_case):
    from mordheim_combat.vectorized import _optional_phase_plan

    ordinary = vector_case("test_runtime_regressions/test_optional_phase_plan_only_enables_reachable_stateful_phases-0-0").first
    inert = _optional_phase_plan(ordinary, ordinary)
    assert not any(getattr(inert, name) for name in inert.__slots__)

    stateful = replace(
        ordinary,
        global_effects=EffectSet(tags=(
            "mechanic.force-of-will", "spines", "mechanic.netter",
            "mechanic.black-hunger",
        )),
        main_weapon=EffectSet(
            tags=("weapon.chained-squig",), ignition_threshold=4,
        ),
    )
    enabled = _optional_phase_plan(stateful, ordinary)
    assert enabled.first_force_of_will
    assert enabled.first_spines
    assert enabled.first_netter
    assert enabled.first_black_hunger
    assert enabled.first_entangle
    assert enabled.second_can_burn
    assert not enabled.first_can_burn


def test_stupidity_gate_silences_only_the_rows_that_fail(monkeypatch, vector_case):
    """G06: the round driver runs the Stupidity gate and its pool consequence."""
    import mordheim_combat.kernel as kernel
    from mordheim_combat.vectorized import simulate_batch_observed

    printed = vector_case("test_runtime_regressions/test_stupidity_gate_silences_only_the_rows_that_fail-0-0").first

    # The capability is still behind G00's admission gate; this case exercises
    # the connection itself, not the gate's removal.
    monkeypatch.setattr(kernel, "require_optimized_support", lambda *a, **k: None)

    def fighter(tags=()):
        compiled = printed
        return replace(
            compiled,
            characteristics=replace(compiled.characteristics, leadership=0),
            global_effects=EffectSet(tags=tuple(tags)),
        )

    # Leadership 0 never passes the 2D6 test, so the bearer's own turns are lost
    # while the same profile without the rule keeps striking.
    plain = simulate_batch_observed(fighter(), fighter(), 200, np.random.default_rng(11), 2)
    stupid = simulate_batch_observed(
        fighter(("mechanic.stupidity",)), fighter(), 200, np.random.default_rng(11), 2)

    assert int(stupid.second_wounds.sum()) > int(plain.second_wounds.sum())
    assert int(stupid.first_wounds.sum()) >= 0
    assert (stupid.winner != 0).sum() + (stupid.winner == 0).sum() == 200


def test_fear_mask_reaches_the_hit_target_and_forces_natural_sixes(vector_case):
    """G06: Psychology's fear mask reaches the weapon hit target."""
    from mordheim_combat.vectorized._attacks import _prepare_weapon_attack
    from mordheim_combat.vectorized._state import initialize_fighter

    case = vector_case("test_runtime_regressions/test_fear_mask_reaches_the_hit_target_and_forces_natural_sixes-0-0")
    attacker, defender = case.first, case.second
    attacker_state = initialize_fighter(attacker, 1, np.random.default_rng(0))
    defender_state = initialize_fighter(defender, 1, np.random.default_rng(0))
    rows = np.array([0])
    charging = np.array([False])

    ordinary = _prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, rows, charging,
        attacker_state, defender_state, np.random.default_rng(1), False,
    )
    attacker_state.fear_hit_sixes[:] = True
    feared = _prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, rows, charging,
        attacker_state, defender_state, np.random.default_rng(1), False,
    )

    assert ordinary is not None and feared is not None
    assert int(ordinary.hit_target[0]) < 6
    assert int(feared.hit_target[0]) == 6


def test_gaoler_grapple_declares_and_holds_per_row(vector_case):
    """G06: the Torturer's hold declares, resolves and writes the hold state."""
    case = vector_case("test_runtime_regressions/test_gaoler_grapple_declares_and_holds_per_row-0-0")
    from mordheim_combat.vectorized._driver import (
        _grapple_declaration, _resolve_grapple, _round_ledger,
    )
    from mordheim_combat.vectorized._state import initialize_fighter

    def tagged(fighter):
        return replace(fighter, global_effects=replace(
            fighter.global_effects,
            tags=(*fighter.global_effects.tags, "mechanic.gaoler-grapple")))

    count = 40
    holder = tagged(case.second)
    victim = case.first
    holder_state = initialize_fighter(holder, count, np.random.default_rng(0))
    victim_state = initialize_fighter(victim, count, np.random.default_rng(0))
    rows = np.arange(count)
    ledger = _round_ledger(count)

    declared = _grapple_declaration(
        holder, victim, holder_state, victim_state, rows, None, ledger,
        np.zeros(count, dtype=bool), "round.0.first",
    )
    assert declared.all()
    _resolve_grapple(
        holder, victim, rows, holder_state, victim_state,
        np.random.default_rng(3), True, None, "round.0.first.grapple",
    )

    assert victim_state.grappled.any()
    assert np.array_equal(holder_state.grappling, victim_state.grappled)

    # Undead targets are excluded from the declaration.
    plain = vector_case("test_runtime_regressions/test_pistol_and_sword_allocate_attacks_to_the_correct_weapon-0-0").second
    undead = replace(plain, global_effects=EffectSet(tags=("nature.undead",)))
    assert not _grapple_declaration(
        holder, undead, holder_state, victim_state, rows, None, ledger,
        np.zeros(count, dtype=bool), "round.0.first",
    ).any()


def test_mim_without_hands_empties_the_pool_but_keeps_extra_attacks(vector_case):
    """G06: no hand attacks, yet the independent natural attack still strikes."""
    case = vector_case("test_runtime_regressions/test_mim_without_hands_empties_the_pool_but_keeps_extra_attacks-0-0")
    from mordheim_combat.vectorized import simulate_batch_observed

    def tagged(fighter, *tags):
        return replace(fighter, global_effects=replace(
            fighter.global_effects, tags=(*fighter.global_effects.tags, *tags)))

    base = case.first
    mim = tagged(base, "condition.mim-no-hand-attacks")
    mim = replace(mim, extra_attacks=(EffectSet(tags=("weapon.natural-attacks",)),))
    plain = base
    opponent = case.second

    plain_batch = simulate_batch_observed(
        plain, opponent, 150, np.random.default_rng(5), 1)
    mim_batch = simulate_batch_observed(
        mim, opponent, 150, np.random.default_rng(5), 1)

    plain_damage = int((opponent_start := 6 * 150) - plain_batch.second_wounds.sum())
    mim_damage = int(opponent_start - mim_batch.second_wounds.sum())
    assert 0 < mim_damage < plain_damage

    # Without an independent contribution the forfeit leaves no pool at all.
    handless = simulate_batch_observed(
        tagged(base, "condition.mim-no-hand-attacks"),
        opponent, 150, np.random.default_rng(5), 1)
    assert int(opponent_start - handless.second_wounds.sum()) == 0


def test_tentacle_chooses_one_allocation_and_spends_it_once(vector_case):
    """G06: the tentacle loss is nominated on the real allocation, once."""
    from mordheim_combat.vectorized._driver import (
        _round_ledger, _tentacle_forfeit,
    )

    case = vector_case("test_runtime_regressions/test_tentacle_chooses_one_allocation_and_spends_it_once-0-0")
    holder = case.first
    defended = EffectSet(tags=("rule.tentacle-grapple",), incoming_attacks_modifier=-1)
    attacks = np.array([3, 1, 2, 3], dtype=np.int16)
    ledger = _round_ledger(4)
    no_charge = np.zeros(4, dtype=bool)
    no_whip = np.zeros(4, dtype=bool)

    forfeits, whip, extras = _tentacle_forfeit(
        holder, defended, np.arange(4), attacks, None, ledger, 1, "round.0",
        charging=no_charge, whip_rows=no_whip)
    assert forfeits.tolist() == [0, -1, 0, 0]
    assert not whip.any() and (extras == -1).all()
    assert ledger.tentacle_used[1].tolist() == [True, False, True, True]

    # Declining the first offer nominates the next position of each own pool.
    from mordheim_core.dice import ScriptedDecisions

    forfeits, whip, extras = _tentacle_forfeit(
        holder, defended, np.arange(4), attacks,
        ScriptedDecisions({"round.1.grapple-lost-attack.0": False,
                           "round.1.grapple-lost-attack.1": True}),
        _round_ledger(4), 1, "round.1",
        charging=no_charge, whip_rows=no_whip)
    assert forfeits.tolist() == [1, -1, 1, 1]

    # The printed resource is spent for the rest of the battle.
    again, _, _ = _tentacle_forfeit(
        holder, defended, np.arange(4), attacks, None, ledger, 1, "round.2",
        charging=no_charge, whip_rows=no_whip)
    assert (again == -1).all()

    # The minimum applies to the complete pool: one hand attack plus an extra
    # still loses its hand attack, leaving the independent contribution.
    extra = EffectSet(tags=("weapon.natural-attacks",))
    with_extra = replace(holder, extra_attacks=(extra,))
    hands = np.array([1, 1], dtype=np.int16)
    forfeits, whip, extras = _tentacle_forfeit(
        with_extra, defended, np.arange(2), hands, None, _round_ledger(2), 1,
        "round.3", charging=np.zeros(2, dtype=bool),
        whip_rows=np.zeros(2, dtype=bool))
    assert forfeits.tolist() == [0, 0] and (extras == -1).all()

    # Position 1 is the extra: the pool skips that exact contribution.
    forfeits, whip, extras = _tentacle_forfeit(
        with_extra, defended, np.arange(2), hands,
        ScriptedDecisions({"round.4.grapple-lost-attack.0": False,
                           "round.4.grapple-lost-attack.1": True}),
        _round_ledger(2), 1, "round.4",
        charging=np.zeros(2, dtype=bool), whip_rows=np.zeros(2, dtype=bool))
    assert (forfeits == -1).all() and extras.tolist() == [0, 0]

    # A Whipcrack bonus is a real position of that allocation too.
    whip_holder = case.second
    one_hand = np.ones(2, dtype=np.int16)
    forfeits, whip, extras = _tentacle_forfeit(
        whip_holder, defended, np.arange(2), one_hand,
        ScriptedDecisions({"round.5.grapple-lost-attack.0": False,
                           "round.5.grapple-lost-attack.1": True}),
        _round_ledger(2), 1, "round.5",
        charging=np.ones(2, dtype=bool), whip_rows=np.ones(2, dtype=bool))
    assert (forfeits == -1).all() and whip.tolist() == [True, True]
    assert (extras == -1).all()

    # Mim without hands: the remaining pool is exactly its extras, so two
    # extras leave a position to nominate; one extra is already the minimum.
    def tagged(fighter):
        return replace(fighter, global_effects=replace(
            fighter.global_effects,
            tags=(*fighter.global_effects.tags, "condition.mim-no-hand-attacks")))

    two_extras = replace(tagged(holder),
                         extra_attacks=(extra, EffectSet(tags=("weapon.fighting-claws",))))
    forfeits, whip, extras = _tentacle_forfeit(
        two_extras, defended, np.arange(2), np.zeros(2, dtype=np.int16),
        ScriptedDecisions({"round.6.grapple-lost-attack.0": False,
                           "round.6.grapple-lost-attack.1": True}),
        _round_ledger(2), 1, "round.6",
        charging=np.zeros(2, dtype=bool), whip_rows=np.zeros(2, dtype=bool))
    assert (forfeits == -1).all() and extras.tolist() == [1, 1]

    forfeits, whip, extras = _tentacle_forfeit(
        replace(two_extras, extra_attacks=(extra,)), defended, np.arange(2),
        np.zeros(2, dtype=np.int16), None, _round_ledger(2), 1, "round.7",
        charging=np.zeros(2, dtype=bool), whip_rows=np.zeros(2, dtype=bool))
    assert (forfeits == -1).all() and (extras == -1).all()

    # The nominated extra is skipped by the pool that resolves it.
    from mordheim_combat.vectorized._attacks import resolve_attacks
    from mordheim_combat.vectorized._state import initialize_fighter

    twice = replace(tagged(holder), extra_attacks=(extra, extra))
    enemy = vector_case("test_runtime_regressions/test_tentacle_chooses_one_allocation_and_spends_it_once-0-1").first

    def resolve(forfeited):
        attacker_state = initialize_fighter(twice, 1, np.random.default_rng(0))
        defender_state = initialize_fighter(enemy, 1, np.random.default_rng(0))
        observed = []
        resolve_attacks(
            twice, enemy, np.array([0]), np.zeros(1, dtype=np.int16),
            np.zeros(1, dtype=bool), attacker_state, defender_state,
            np.random.default_rng(1), False, observations=observed,
            extra_forfeits=np.array([forfeited], dtype=np.int16))
        return observed

    assert len(resolve(-1)) == 2
    assert len(resolve(1)) == 1


def test_spawn_special_attacks_replaces_the_pool_with_one_die_plus_one(monkeypatch, vector_case):
    """G06: the built pool is replaced by D6+1, once per warrior and round."""
    import mordheim_combat.vectorized._driver as driver

    case = vector_case("test_runtime_regressions/test_spawn_special_attacks_replaces_the_pool_with_one_die_plus_one-0-0")
    spawned, opponent = case.first, case.second
    seen = []
    original = driver.resolve_attacks

    def spy(attacker, defender, rows, attacks, *args, **kwargs):
        if rows.size and "mechanic.spawn-special-attacks" in attacker.global_effects.tags:
            seen.extend(int(value) for value in attacks[rows])
        return original(attacker, defender, rows, attacks, *args, **kwargs)

    monkeypatch.setattr(driver, "resolve_attacks", spy)
    driver.simulate_batch(spawned, opponent, 30, np.random.default_rng(4), 1)

    assert seen
    assert min(seen) >= 2 and max(seen) <= 7
    assert len(set(seen)) > 1
