"""T13 A-block: the pike's printed Strike First is scoped to the first turn.

Source (``sources/knowledge/catalog/items/weapons-close-combat.yaml`` and
``sources/knowledge/catalog/mechanics/execution.yaml`` / mordheimer.net):

* ``weapon.pike``: *"A warrior with a pike strikes first in the first turn of a
  hand-to-hand combat."*

The spear carries the same printed wording and the engine already scoped its
strike-first layer to the first turn.  The pike carried only ``priority: 1`` and
kept the layer in every round, so its printed clause was not delivered after the
first turn.  ``resolve_priority`` now applies the same turn scope, and
``tests/specs/semantic/rules/weapon-families-priority-and-armour.yaml`` records
the pike cases beside the spear's.  The scope is a modular change: the optimized
vectorized and native drivers still carry the unscoped flag, which needs its own
porting dispatch.
"""
from __future__ import annotations

from mordheim_combat.phases import PriorityContext, resolve_priority
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def fighter(weapon="weapon.mace", initiative=3):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, initiative, 1), main_weapon_id=weapon))


def priority(attacker, defender, **options):
    return resolve_priority(PriorityContext(attacker, defender, **options))


def test_the_pike_compiles_the_printed_priority_and_two_hands():
    pike = fighter("weapon.pike")
    assert pike.main_weapon.priority == 1
    assert pike.main_weapon.two_handed


def test_the_pike_strikes_first_in_the_first_turn():
    pike = fighter("weapon.pike", initiative=1)
    ordinary = fighter("weapon.mace", initiative=6)
    assert priority(pike, ordinary, first_round=True).priority == 1
    assert priority(ordinary, pike, first_round=True).priority == 0


def test_the_pike_follows_ordinary_order_after_the_first_turn():
    pike = fighter("weapon.pike", initiative=1)
    ordinary = fighter("weapon.mace", initiative=6)
    # The printed clause is turn-scoped: the layer is gone, so the higher
    # Initiative decides the following rounds.
    assert priority(pike, ordinary, first_round=False).priority == 0
    assert priority(ordinary, pike, first_round=False).priority == 0
    assert (priority(ordinary, pike, first_round=False).initiative
            > priority(pike, ordinary, first_round=False).initiative)


def test_the_spear_shares_the_same_turn_scope():
    spear = fighter("weapon.spear", initiative=1)
    ordinary = fighter("weapon.mace", initiative=6)
    assert priority(spear, ordinary, first_round=True).priority == 1
    assert priority(spear, ordinary, first_round=False).priority == 0
