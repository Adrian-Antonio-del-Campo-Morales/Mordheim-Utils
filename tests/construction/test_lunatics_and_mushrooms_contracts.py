"""Construction contracts split from ``tests/engines/modular/test_lunatics_and_mushrooms.py``.

The Fungus Brew is a pre-battle producer: the caller supplies the affected duelist
and the results its batch printed, one canonical condition per result.  These two
cases belong to construction, not to engine execution: they read the compiled
profile that carries the supplied result and the supply table that admits or
refuses a condition.  The duel consequences of the same conditions stay with the
modular execution suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def supplied(conditions, **options):
    """An unidentified duelist carrying only the caller's supplied result."""
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 5, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour",
        condition_ids=tuple(conditions), **options))


def test_every_printed_brew_result_is_supplied_through_its_condition():
    plain = supplied(())
    assert plain.characteristics.initiative == 5
    assert "mechanic.fear-immunity" not in plain.global_effects.tags
    assert plain.armour_save == 7 and plain.global_effects.armour_save_floor == 7
    assert "skill.hatred" not in plain.global_effects.tags
    assert not plain.global_effects.frenzy
    # "2 Dizzy = -1 Initiative" for the battle.
    assert supplied(("condition.fungus-brew-dizzy",)).characteristics.initiative == 4
    # "3 Fearless = immune to Fear" (the admitted individual half).
    fearless = supplied(("condition.fungus-brew-fearless",))
    assert "mechanic.fear-immunity" in fearless.global_effects.tags
    assert "mechanic.psychology-immunity" not in fearless.global_effects.tags
    # "4 Numbed = +1 armour save, which may not be reduced below 6+".
    numbed = supplied(("condition.fungus-brew-numbed",))
    assert numbed.armour_save == 6 and numbed.global_effects.armour_save_bonus == 1
    assert numbed.global_effects.armour_save_floor == 6
    # "5 Belligerent = Hatred against the opposing warband(s)".
    assert "skill.hatred" in supplied(("condition.fungus-brew-belligerent",)).global_effects.tags
    # "6 Loony = Frenzy, followed by Stupidity if Frenzy is lost".
    loony = supplied(("condition.fungus-brew-loony",))
    assert loony.global_effects.frenzy and "mechanic.stupidity" in loony.global_effects.tags
    # A batch of distinct results supplies each of them at once.
    batch = supplied(("condition.fungus-brew-dizzy", "condition.fungus-brew-fearless",
                      "condition.fungus-brew-numbed"))
    assert batch.characteristics.initiative == 4 and batch.armour_save == 6
    assert "mechanic.fear-immunity" in batch.global_effects.tags


def test_the_brew_table_is_a_supplied_state_and_not_an_unadmitted_condition():
    # The supply table admits only canonical conditions whose own runtime binds an
    # operator, so a general rule text cannot be handed in as a supplied result.
    with pytest.raises(ValueError, match="outside the executable duel runtime"):
        supplied(("condition.fear",))
