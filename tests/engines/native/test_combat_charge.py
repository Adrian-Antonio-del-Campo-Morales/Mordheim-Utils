"""Combat Charge uses the native bearer's finalized, phase-local charge."""
from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from mordheim_core.models import DuelContext, EffectSet
from tools.verification.compiled_cases import load_cases

native = pytest.importorskip("mordheim_combat._combat_native")


@lru_cache(maxsize=1)
def _base():
    path = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
    base = load_cases(path)["scenario/basic"].first
    return replace(base, main_weapon=EffectSet(tags=("weapon.mace",)),
                   main_weapon_without_poison=None, off_hand=None,
                   off_hand_without_poison=None, off_hand_attacks=False,
                   extra_attacks=(), global_effects=EffectSet())


class Tape:
    def __init__(self, *values):
        self.values = list(values)

    def integers(self, low, high, size=None):
        count = 1 if size is None else int(size)
        assert len(self.values) >= count, "unexpected extra die"
        drawn, self.values = self.values[:count], self.values[count:]
        return np.asarray(drawn, dtype=np.int8)

    def random(self, size=None):
        return np.zeros(size)


@pytest.mark.parametrize("owner_first", [True, False])
@pytest.mark.parametrize("mode", ["charge", "receive", "neither"])
@pytest.mark.parametrize("skills", [(3, 3), (2, 1)])
def test_combat_charge_adds_attacks_and_both_ws_bonuses_then_expires(owner_first, mode, skills):
    base = _base()
    own_ws, enemy_ws = skills
    owner = replace(base, global_effects=EffectSet(tags=("skill.combat-charge",)),
        characteristics=replace(base.characteristics, weapon_skill=own_ws, initiative=4))
    enemy = replace(base,
        characteristics=replace(base.characteristics, weapon_skill=enemy_ws, initiative=2))
    first, second = (owner, enemy) if owner_first else (enemy, owner)
    own_label, enemy_label = (("first", "second") if owner_first else ("second", "first"))
    charging = (own_label,) if mode == "charge" else (enemy_label,) if mode == "receive" else ()
    if skills == (3, 3):
        # A 3 hits only with the offensive WS bonus; all wound dice are 1.
        opening = (3, 1, 1, 1) if mode == "charge" else (1, 3) if mode == "receive" else (3, 1)
        later = (3, 1)  # The same 3 must miss once the WS bonus expires.
    else:
        # WS3 against WS1 makes the opponent's 4 miss. Without the defensive
        # bonus it hits and draws a (failed) wound die instead.
        opening = (1, 1, 4) if mode == "charge" else (4, 1, 1) if mode == "receive" else (1, 4, 1)
        later = (1, 4, 1)
    tape = Tape(*opening, *later)
    result = native.simulate_batch_observed(first, second, 1, tape, 2,
        context=DuelContext(charging=charging, active_participant=charging[0] if charging else own_label))
    assert not tape.values
    assert result.rounds.tolist() == [2]
    assert result.first_wounds.tolist() == [first.characteristics.wounds]
    assert result.second_wounds.tolist() == [second.characteristics.wounds]


def test_combat_charge_preserves_plain_fighters_and_cancelled_charges():
    base = _base()
    context = DuelContext(charging=("first",), active_participant="first")
    tape = Tape(1, 1)
    native.simulate_batch_observed(base, base, 1, tape, 1, context=context)
    assert not tape.values  # An untagged charge still has one attack per side.
    owner = replace(base, global_effects=EffectSet(tags=("skill.combat-charge",)),
        characteristics=replace(base.characteristics, leadership=0))
    enemy = replace(base, global_effects=EffectSet(tags=("mechanic.causes-fear",)))
    tape = Tape(1, 1)
    result = native.simulate_batch_observed(owner, enemy, 1, tape, 1, context=context)
    assert not tape.values and result.winner.tolist() == [0]
    assert result.first_wounds.tolist() == [owner.characteristics.wounds]
    assert result.second_wounds.tolist() == [enemy.characteristics.wounds]


def test_combat_charge_attack_bonus_is_doubled_by_frenzy_only_during_charge():
    base = _base()
    owner = replace(base, global_effects=EffectSet(tags=("skill.combat-charge",), frenzy=True),
                    characteristics=replace(base.characteristics, initiative=4))
    enemy = replace(base, characteristics=replace(base.characteristics, initiative=2))
    # Opening: (A1 + 1) doubled to four blows; later: A1 doubled to two.
    tape = Tape(*([1] * 8))
    result = native.simulate_batch_observed(owner, enemy, 1, tape, 2,
        context=DuelContext(charging=("first",), active_participant="first"))
    assert not tape.values and result.rounds.tolist() == [2]
