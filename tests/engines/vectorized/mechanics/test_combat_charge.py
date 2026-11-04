"""Combat Charge masks and phase lifetime, without cross-engine sampling."""
from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat.vectorized import _driver as driver
from mordheim_core.models import DuelContext, EffectSet


class LowRng:
    def integers(self, low, high=None, size=None, dtype=None):
        return np.ones(size if size is not None else (), dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def pair(vector_case, own_ws=3, enemy_ws=3, selected=True):
    plain = vector_case(
        "test_psychology_vectorized/test_the_holy_relic_passes_once_and_the_next_test_rolls_normally-0-0"
    ).second
    owner = replace(plain,
        global_effects=EffectSet(tags=("skill.combat-charge",) if selected else ()),
        characteristics=replace(plain.characteristics, weapon_skill=own_ws, initiative=4, attacks=1))
    enemy = replace(plain, global_effects=EffectSet(),
        characteristics=replace(plain.characteristics, weapon_skill=enemy_ws, initiative=2, attacks=1))
    return owner, enemy


@pytest.mark.parametrize("owner_first", [True, False])
@pytest.mark.parametrize("charging", [True, False])
@pytest.mark.parametrize("weapon_skills", [(3, 3), (2, 1)])
def test_combat_charge_boosts_only_own_charge_and_expires(vector_case, owner_first, charging, weapon_skills):
    owner, enemy = pair(vector_case, *weapon_skills)
    first, second = (owner, enemy) if owner_first else (enemy, owner)
    owner_label = "first" if owner_first else "second"
    enemy_label = "second" if owner_first else "first"
    charger = owner_label if charging else enemy_label
    observations = []
    result = driver.simulate_batch_observed(
        first, second, 1, LowRng(), 2,
        context=DuelContext(charging=(charger,), active_participant=charger),
        observations=observations)
    own_ws, enemy_ws = weapon_skills
    expected = ([3, 3, 5 if own_ws == 2 else 4] if charging
                else [4, 3 if own_ws > enemy_ws else 4])
    expected += [3 if own_ws > enemy_ws else 4, 4]
    assert [attack.hit_target for attack in observations] == expected
    assert result.rounds.tolist() == [2]
    assert owner.global_effects.attacks_bonus == 0
    assert owner.characteristics.weapon_skill == own_ws


def test_combat_charge_masks_mixed_rows_and_restores_ws(vector_case, monkeypatch):
    owner, enemy = pair(vector_case, 2, 1)
    states, pools = [], []
    initialize, resolve = driver.initialize_fighter, driver.resolve_attacks

    def capture_state(*args, **kwargs):
        state = initialize(*args, **kwargs)
        states.append(state)
        return state

    def capture_pool(attacker, defender, rows, attacks, *args, **kwargs):
        pools.append((kwargs["decision_prefix"], rows.tolist(), attacks[rows].tolist(),
                      args[1].weapon_skill[rows].tolist()))
        return resolve(attacker, defender, rows, attacks, *args, **kwargs)

    class MixedRng(LowRng):
        def random(self, size=None):
            return np.array([0.1, 0.9]) if size == 2 else super().random(size)

    monkeypatch.setattr(driver, "initialize_fighter", capture_state)
    monkeypatch.setattr(driver, "resolve_attacks", capture_pool)
    driver.simulate_batch(owner, enemy, 2, MixedRng(), 1)
    own = [entry for entry in pools if entry[0] == "round.0.first"]
    assert sorted((row, attacks, ws) for _, rows, counts, skills in own
                  for row, attacks, ws in zip(rows, counts, skills)) == [(0, 2, 3), (1, 1, 2)]
    assert states[0].weapon_skill.tolist() == [2, 2]


def test_plain_and_cancelled_charges_receive_no_combat_charge_bonus(vector_case):
    owner, enemy = pair(vector_case, selected=False)
    context = DuelContext(charging=("first",), active_participant="first")
    observations = []
    driver.simulate_batch_observed(owner, enemy, 1, LowRng(), 1,
                                  context=context, observations=observations)
    assert [attack.hit_target for attack in observations] == [4, 4]
    owner = replace(owner, global_effects=EffectSet(tags=("skill.combat-charge",)))
    observations = []
    driver.simulate_batch_observed(owner, enemy, 1, LowRng(), 1,
        context=DuelContext(charging=(), active_participant="first"), observations=observations)
    assert [attack.hit_target for attack in observations] == [4, 4]
    owner = replace(owner, characteristics=replace(owner.characteristics, leadership=0))
    enemy = replace(enemy, global_effects=EffectSet(tags=("mechanic.causes-fear",)))
    observations = []
    result = driver.simulate_batch_observed(owner, enemy, 1, LowRng(), 1,
                                           context=context, observations=observations)
    assert not observations and result.winner.tolist() == [0]


def test_combat_charge_bonus_uses_the_existing_frenzy_order(vector_case):
    from mordheim_combat.vectorized._operators import attack_count

    owner, _ = pair(vector_case)
    charging = np.array([True, False])
    frenzy = np.ones(2, dtype=bool)
    assert attack_count(owner, charging, first_round=True, frenzy=frenzy).tolist() == [4, 2]
    assert attack_count(owner, charging, first_round=False, frenzy=frenzy).tolist() == [2, 2]
