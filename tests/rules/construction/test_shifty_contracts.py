"""Construction contract split from ``tests/engines/modular/test_shifty.py``.

The selectable Halfling Shifty skill is admitted only when the loadout names it;
the bare canonical profile does not carry the tag.  The check asserts on
compiled output and never executes a round, so it belongs to the construction
suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


@pytest.mark.phase2_construction
def test_canonical_halfling_skill_is_selected_and_not_automatically_granted():
    unit = compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.mace'))
    assert 'skill.shifty' not in unit.global_effects.tags
    selected = compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.mace',
        special_rule_ids=('halfling-elder--shifty',)))
    assert selected.global_effects.tags.count('skill.shifty') == 1
