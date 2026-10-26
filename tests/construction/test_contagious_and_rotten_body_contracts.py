"""Construction contract for Contagious on both Clan Pestilens origins.

The prerequisite refusal and the printed recipient list belong to the compiler;
the execution of the reaction stays in the modular suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild

ORIGINS = (("mordheim", "skaven-clan-pestilens"), ("trollheim", "lustria-clan-pestilens"))
ROTTEN_BODY = "band--clan-pestilens-special-skills-rotten-body"
CONTAGIOUS = "band--clan-pestilens-special-skills-contagious"



def priest(collection="mordheim", rules=(ROTTEN_BODY, CONTAGIOUS)):
    band = dict(ORIGINS)[collection]
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id="plague-priest", collection=collection,
        main_weapon_id="weapon.club", special_rule_ids=rules,
    ))


@pytest.mark.parametrize("collection,band", ORIGINS)
def test_each_origin_executes_contagious_under_its_rotten_body_prerequisite(collection, band):
    tagged = priest(collection)
    assert "contagious" in tagged.global_effects.tags
    assert "poison_immune" in tagged.global_effects.tags
    with pytest.raises(ValueError, match="Contagious requires Rotten Body"):
        priest(collection, rules=(CONTAGIOUS,))
    lonely = priest(collection, rules=(ROTTEN_BODY,))
    assert "contagious" not in lonely.global_effects.tags
    # The recipients are untouched: a profile outside the printed list is refused.
    with pytest.raises(ValueError, match="special rule is not available"):
        compile_fighter(FighterBuild(
            "mordheim", band_id=band, profile_id="plague-novices", collection=collection,
            main_weapon_id="weapon.club", special_rule_ids=(ROTTEN_BODY, CONTAGIOUS),
        ))
