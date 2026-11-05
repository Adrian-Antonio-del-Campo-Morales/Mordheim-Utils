"""Accessory-path optimizations, round 2: projection shortcut and no-op skips.

None of these may change a simulation result. Each check compares the fast
path with the plain computation it replaces.
"""
from __future__ import annotations

from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.state import FighterState
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
from mordheim_combat_lab.cli.scenarios import deep_test_scenarios


def _fighters():
    for scenario in deep_test_scenarios("full"):
        yield from compile_benchmark_fighters(scenario)


def test_equipment_projection_identity_shortcut_equals_the_full_projection(monkeypatch):
    from mordheim_combat.modular import equipment

    base = FighterState(wounds=1)
    cases = [(fighter, first_round) for fighter in _fighters() for first_round in (True, False)]
    fast = [equipment_for_state(fighter, base, first_round=first_round)
            for fighter, first_round in cases]
    shortcuts = [equipment._projection_is_identity(fighter, base, first_round)
                 for fighter, first_round in cases]
    assert any(shortcuts), "the catalogue should exercise the shortcut"
    for (fighter, _), result, taken in zip(cases, fast, shortcuts):
        if taken:
            assert result is fighter
    # With the shortcut disabled the full projection must be value-equal.
    monkeypatch.setattr(equipment, "_projection_is_identity", lambda *a: False)
    full = [equipment_for_state(fighter, base, first_round=first_round)
            for fighter, first_round in cases]
    assert full == fast


def test_equipment_shortcut_is_refused_when_state_touches_equipment():
    from mordheim_combat.modular import equipment

    fighter, _ = compile_benchmark_fighters(benchmark_scenarios()[0])
    base = FighterState(wounds=1)
    assert equipment._projection_is_identity(fighter, base, True)
    for changed in (
        FighterState(wounds=1, broken_hands=frozenset({fighter.main_hand_slot})),
        FighterState(wounds=1, transformed=True),
        FighterState(wounds=1, equipment_cast_off=True),
        FighterState(wounds=1, hillman_wolf=True),
    ):
        assert not equipment._projection_is_identity(fighter, changed, True)


def test_equipment_projection_still_drops_a_spent_pistol():
    pistol_bearer = next(
        fighter for scenario in deep_test_scenarios("full")
        for fighter in compile_benchmark_fighters(scenario)
        if any("pistol" in tag for tag in fighter.main_weapon.tags))
    state = FighterState(wounds=1)
    opening = equipment_for_state(pistol_bearer, state, first_round=True)
    later = equipment_for_state(pistol_bearer, state, first_round=False)
    assert opening is pistol_bearer
    assert later is not pistol_bearer
    assert later.main_weapon != pistol_bearer.main_weapon


def test_no_op_resource_merges_leave_resources_exactly_as_the_body_did():
    from mordheim_combat.modular import attacks
    from mordheim_core.dice import ScriptedDice

    scenario = benchmark_scenarios()[0]
    attacker, defender = compile_benchmark_fighters(scenario)
    a_state = FighterState(wounds=2, weapon_skill=3, strength=3, toughness=3,
                           attacks=1, initiative=3, parries_remaining=0,
                           resources_spent=frozenset({"already"}))
    d_state = FighterState(wounds=2, weapon_skill=3, strength=3, toughness=3,
                           attacks=1, initiative=3, parries_remaining=0)
    result = attacks.resolve_reference_attack(
        attacker, defender, a_state, d_state, attacker.main_weapon,
        ScriptedDice([6, 6, 6, 6, 6, 6]), key="t", first_round=True, charging=True)
    # No reroll resource exists on these fighters: nothing was spent, and the
    # pre-existing resource survives untouched.
    assert result.attacker.resources_spent == frozenset({"already"})
    assert result.defender.resources_spent == frozenset()
