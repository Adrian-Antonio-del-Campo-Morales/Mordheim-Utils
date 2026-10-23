"""Construction contracts split from ``tests/engines/modular/test_ye_give_way_results.py``.

These tests assert on the canonical compiler itself -- the printed profile
facts and the refusals it produces -- so they keep calling
``compile_fighter`` instead of reading frozen engine inputs.
"""
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def noble(*conditions):
    return compile_fighter(FighterBuild('mordheim', band_id='mazzalupo-web', profile_id='fallen-noble',
        main_weapon_id='weapon.mace', condition_ids=conditions))


def hero(*conditions):
    return compile_fighter(FighterBuild('mordheim', Characteristics(4, 3, 4, 4, 2, 1),
        main_weapon_id='weapon.mace', condition_ids=conditions, trait_overrides={'fighter_kind': 'hero'}))


REFUSED = 'condition.ye-give-way-refused'


WON = 'condition.ye-give-way-victorious'


@pytest.mark.phase2_construction
def test_recipient_guards_and_unselected_noble_has_no_award():
    with pytest.raises(ValueError, match='Hero recipient'):
        compile_fighter(FighterBuild('mordheim', Characteristics(3,3,3,2,2,1), condition_ids=(REFUSED,)))
    with pytest.raises(ValueError, match='Fallen Noble recipient'):
        hero(WON)
    assert noble().characteristics.strength == 3
    assert REFUSED not in noble().global_effects.tags and WON not in noble().global_effects.tags
