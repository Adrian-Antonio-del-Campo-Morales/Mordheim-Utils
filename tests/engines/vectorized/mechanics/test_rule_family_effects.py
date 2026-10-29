"""Vectorized regressions of canonical rule families."""
from __future__ import annotations

from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _prepare_weapon_attack
from mordheim_combat.vectorized import attack_count
from mordheim_combat.vectorized import resolve_attacks
from mordheim_combat.vectorized import simulate_duel
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild
import numpy as np
from pathlib import Path
import pytest as pytest


ROOT = Path(__file__).resolve().parents[4] / "sources/knowledge"


class FixedRng:
    def __init__(self, value: int):
        self.value = value

    def integers(self, low, high=None, size=None, dtype=None):
        return np.full(size if size is not None else (), self.value, dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


def test_anvil_head_death_blow_energy_focus_and_mark_are_executable_combat_choices(vector_case):
    case = vector_case("test_rule_families_a/test_anvil_head_death_blow_energy_focus_and_mark_are_executable_combat_choices-0-0")
    anvil, death = case.first, case.second
    energy = vector_case("test_rule_families_a/test_anvil_head_death_blow_energy_focus_and_mark_are_executable_combat_choices-0-1").first
    mark = vector_case("test_rule_families_a/test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once-0-1").first
    charging = np.array([True])
    assert attack_count(anvil, charging, True)[0] == 1
    assert attack_count(death, charging, True)[0] == 1
    assert attack_count(energy, charging, True)[0] == 2
    assert energy.global_effects.energy_focus_attacks == 2
    assert "mechanic.mark-of-the-old-ones" in mark.global_effects.tags
    assert death.global_effects.hit_modifier == death.global_effects.wound_modifier == death.global_effects.injury_modifier == 1


def test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects(vector_case, compiled_builds):
    case = vector_case("test_rule_families_a/test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects-0-0")
    guardian, marked = case.first, case.second
    # Disability is a permanent supplied result: construction applies Sickly's
    # Toughness penalty once and the frozen build carries that result here.
    cripple = compiled_builds.fighter(build(
        "chaos-streets-mordheim-inhabitants", "cripples", collection="trollheim",
        condition_ids=("condition.disability-4",),
    ), ROOT)
    state = _new_state(cripple, 1, FixedRng(1))
    assert state.disability[0] == 4
    assert state.toughness[0] == cripple.characteristics.toughness

    assert "guardian_unarmed" in guardian.global_effects.tags
    assert marked.characteristics.toughness == 5
    assert marked.global_effects.poison_immunity


def test_animal_friendship_prevents_normal_animals_from_attacking_in_the_duel(vector_case):
    case = vector_case("test_rule_families_a/test_animal_friendship_prevents_normal_animals_from_attacking_in_the_duel-0-0")
    friend, animal = case.first, case.second
    assert "species.animal" in animal.global_effects.tags
    result = simulate_duel(DuelRequest(friend, animal, 40, seed=12, maximum_rounds=20))
    assert result.second_wins == 0


def test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once(vector_case):
    retaliation = vector_case("test_rule_families_a/test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once-0-0")
    attacker, contagious = retaliation.first, retaliation.second
    attack_state, defence_state = _new_state(attacker, 1, FixedRng(6)), _new_state(contagious, 1, FixedRng(6))
    resolve_attacks(attacker, contagious, np.array([0]), np.array([1]), np.array([False]),
                    attack_state, defence_state, FixedRng(6), False)
    assert attack_state.wounds[0] == 1

    marks = vector_case("test_rule_families_a/test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once-0-1")
    marked, target = marks.first, marks.second
    marked_state, target_state = _new_state(marked, 1, FixedRng(1)), _new_state(target, 1, FixedRng(1))
    first = _prepare_weapon_attack(marked, target, marked.main_weapon, np.array([0]), np.array([False]),
                                   marked_state, target_state, FixedRng(1), False)
    second = _prepare_weapon_attack(marked, target, marked.main_weapon, np.array([0]), np.array([False]),
                                    marked_state, target_state, FixedRng(1), False)
    assert first is not None and first.hit_rows.tolist() == [0]
    assert second is not None and second.hit_rows.size == 0
