"""Construction contract: the Clockworkers constructs' admitted immunities.

The check moved here owns the compiler.  The duel consequences of the same four
immunities stay in the modular suite, which consumes the precompiled fighters.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest

BAND = "clockworkers-sc"
CONSTRUCTS = ("clockwork-soldiers", "clockwork-fiend")


def construct(profile_id: str, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=profile_id,
                                        main_weapon_id="weapon.mace", **options))


@pytest.mark.phase2_construction
def test_both_constructs_carry_their_admitted_immunities():
    for profile_id in CONSTRUCTS:
        fighter = construct(profile_id)
        tags = set(fighter.global_effects.tags)
        assert {"mechanic.psychology-immunity", "skill.ignore-pain", "poison_immune"} <= tags
        assert "mechanic.drug-immunity" in tags
        assert fighter.global_effects.poison_immunity
