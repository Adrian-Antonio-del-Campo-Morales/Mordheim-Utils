"""The printed Misericordia coup-de-grace clause.

Source (``sources/knowledge``): ``catalog/items/weapons-close-combat.yaml`` /
``misericordia``: *"When attacking knocked down opponents, Misericordia bypasses
all armor saves."*

The operator is armour-scoped, not weapon-scoped: the clause is carried by the
``weapon.misericordia`` execution contract (the only item binding it) as
``ignore_armour_against_knocked_down``.  The check reads the armour stage the
round actually builds, so it distinguishes a denied save from the ordinary
+1 dagger armour bonus.
"""
from __future__ import annotations

from dataclasses import replace

from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import Condition, armour_target, resolve_armour
from mordheim_combat_lab.verification.dice import StrictDice
import pytest


def context(compiled, condition):
    # ``first`` is the Misericordia attacker and ``second`` the armoured target.
    me, enemy = compiled.first, compiled.second
    state = initialize_fighter(me, StrictDice([]), "probe")
    enemy_state = replace(initialize_fighter(enemy, StrictDice([]), "probe"), condition=condition)
    return prepare_armour_context(me, enemy, state, enemy_state, me.main_weapon,
                                  me.main_weapon, key="armour")


@pytest.mark.phase2_construction
def test_contract_publishes_the_condition_scoped_denial():
    from mordheim_construction.contracts import effect_index
    effect = effect_index("mordheim")["weapon.misericordia"].effect
    assert effect.ignore_armour_against_knocked_down is True
    # The generic dagger penalty is unchanged.
    assert effect.target_armour_bonus == 1


@pytest.mark.phase3_rules
def test_a_knocked_down_target_is_denied_its_armour_save_entirely(precompiled):
    knocked = context(precompiled(), Condition.KNOCKED_DOWN)
    assert knocked.ignore_armour is True
    assert armour_target(knocked) > 6
    assert resolve_armour(knocked, StrictDice([])).eligible is False


@pytest.mark.phase3_rules
def test_a_standing_target_still_rolls_the_armour_save(precompiled):
    standing = context(precompiled(), Condition.STANDING)
    assert standing.ignore_armour is False
    target = armour_target(standing)
    assert target <= 6
    assert resolve_armour(standing, StrictDice([{"key": "armour", "value": 1}])).eligible is True
