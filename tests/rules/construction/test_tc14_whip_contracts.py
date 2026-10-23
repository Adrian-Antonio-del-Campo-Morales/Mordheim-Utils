"""Construction contract for the TC14 whip profiles.

The two printed wielders and the source's TC14 variant compile to the whip's
declared properties (master rule, -1 Strength, +1 enemy save), while the
catalogue keeps the out-of-scope plain ``whip`` item distinct.  Executing the
whip belongs to the modular suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_items


def skinner():
    return compile_fighter(FighterBuild('mordheim', band_id='hirelings.hired-sword.1b',
        profile_id='hireling.hired-sword.mule-skinner', main_weapon_id='weapon.whip-tc14',
        special_rule_ids=('hireling.hired-sword.mule-skinner.skill.animal-handling-falconer',)))


def heinrich():
    return compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b',
        profile_id='hireling.dramatis.heinrich-altdorf-schmidt',
        main_weapon_id='weapon.whip-tc14', armour_id='armour.light-armour'))


@pytest.mark.phase2_construction
def test_canonical_profiles_and_source_variant_stay_distinct():
    for fighter in (skinner(), heinrich()):
        assert 'weapon.whip-tc14' in fighter.main_weapon.tags
        assert 'mechanic.whip-master' in fighter.global_effects.tags
        assert fighter.main_weapon.strength_bonus == -1
        assert fighter.main_weapon.target_armour_bonus == 1
    assert 'mechanic.fear-of-snakes' in heinrich().global_effects.tags
    assert next(item for item in load_items("mordheim") if item['id'] == 'whip')['combat_status'] == 'out_of_scope'
