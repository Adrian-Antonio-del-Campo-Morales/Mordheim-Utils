"""Construction contract for the canonical Vomit Attack option.

The option is compiled as a separate effect and must not alter the printed
weapon or the normal effects; the execution witnesses stay in the modular suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import EffectSet, FighterBuild

RULE = "warpstone-troll--vomit-attack"



def troll(selected=True):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="underworld-alliance-mim", profile_id="warpstone-troll",
        special_rule_ids=(RULE,) if selected else (),
    ))


def test_canonical_selection_retains_normal_weapon_and_compiles_separate_option():
    selected, absent = troll(), troll(False)
    assert selected.main_weapon == absent.main_weapon
    assert selected.global_effects == absent.global_effects
    assert absent.vomit_attack is None
    assert selected.vomit_attack == EffectSet(
        tags=("weapon.vomit-attack",), cannot_be_parried=True, ignore_armour=True,
        fixed_strength=5, automatic_hit=True,
    )
