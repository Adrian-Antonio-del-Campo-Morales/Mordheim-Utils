"""Construction contracts split from ``tests/engines/modular/test_always_strikes_first.py``.

Both checks assert the compiled output of the canonical builder: the Fanatic's
printed ``skill.always-strikes-first`` tag and priority, and the Lahmia-only
selection of Lost Innocence together with its refusal for another bloodline.
Neither executes a round, so they belong to the construction suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def fighter(band_id=None, profile_id=None, weapon="weapon.mace", initiative=3, **options):
    if band_id is None:
        return compile_fighter(FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 1, initiative, 1),
            main_weapon_id=weapon, **options))
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        main_weapon_id=weapon, **options))


def fanatic():
    return fighter("night-goblins-kaz", "fanatics", weapon="weapon.dagger")


def lahmia_vampire():
    return fighter("chaos-streets-undead-bloodlines", "lahmia-vampire",
                   weapon="weapon.sword", collection="trollheim",
                   special_rule_ids=("band--lahmia-power-lost-innocence",))


def test_the_fanatic_compiles_the_printed_always_strikes_first_tag():
    compiled = fanatic()
    assert "skill.always-strikes-first" in compiled.global_effects.tags
    assert compiled.global_effects.priority == 10


def test_lost_innocence_is_selectable_for_the_lahmia_vampire_alone():
    vampire = lahmia_vampire()
    assert "skill.always-strikes-first" in vampire.global_effects.tags
    with pytest.raises(ValueError):
        fighter("chaos-streets-undead-bloodlines", "strigoi-vampire",
                collection="trollheim",
                special_rule_ids=("band--lahmia-power-lost-innocence",))
