"""T13 A-block group 3: the printed Misericordia coup-de-grace clause.

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
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def attacker():
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
        main_weapon_id="weapon.misericordia"))


def defender():
    # A plain armoured target: the dagger's own +1 still applies when standing.
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.light-armour"))


def context(condition):
    me, enemy = attacker(), defender()
    state = initialize_fighter(me, StrictDice([]), "probe")
    enemy_state = replace(initialize_fighter(enemy, StrictDice([]), "probe"), condition=condition)
    return prepare_armour_context(me, enemy, state, enemy_state, me.main_weapon,
                                  me.main_weapon, key="armour")


def test_contract_publishes_the_condition_scoped_denial():
    from mordheim_construction.contracts import effect_index
    effect = effect_index("mordheim")["weapon.misericordia"].effect
    assert effect.ignore_armour_against_knocked_down is True
    # The generic dagger penalty is unchanged.
    assert effect.target_armour_bonus == 1


def test_a_knocked_down_target_is_denied_its_armour_save_entirely():
    knocked = context(Condition.KNOCKED_DOWN)
    assert knocked.ignore_armour is True
    assert armour_target(knocked) > 6
    assert resolve_armour(knocked, StrictDice([])).eligible is False


def test_a_standing_target_still_rolls_the_armour_save():
    standing = context(Condition.STANDING)
    assert standing.ignore_armour is False
    target = armour_target(standing)
    assert target <= 6
    assert resolve_armour(standing, StrictDice([{"key": "armour", "value": 1}])).eligible is True
