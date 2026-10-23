"""Construction contracts split from ``tests/engines/modular/test_devoted_and_bitten.py``.

Devoted to the Vampire is a supplied-condition mechanic, so its two construction
checks belong here: the printed recipients carry the two tags and no other
profile does, and the supplied Lahmian Vampire condition is accepted only for a
recipient, never declared by a foreign profile and never down and killed at
once.  The combat evidence for the same clause stays in the modular suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild

DEVOTED = "mechanic.devoted-to-the-vampire"
HATRED = "mechanic.devoted-killer-hatred"


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options))


def lahmain(profile, *, weapon="weapon.mace", down=False, killed=False, **options):
    traits = {}
    if down:
        traits["devoted_vampire_down"] = True
    if killed:
        traits["devoted_vampire_killed"] = True
    return canonical("khemri-lahmian-brotherhood", profile, weapon, collection="trollheim",
        trait_overrides=traits, **options)


# --- Devoted to the Vampire: sharing and the supplied facts ----------------

@pytest.mark.phase2_construction
def test_devoted_is_granted_to_both_printed_recipients_and_to_no_other_profile():
    for profile in ("beloved", "lackeys"):
        fighter = lahmain(profile)
        assert DEVOTED in fighter.global_effects.tags, profile
        assert HATRED in fighter.global_effects.tags, profile
    for profile in ("lahmian-vampire", "necromancer", "blood-sister", "skeleton-warriors"):
        fighter = lahmain(profile)
        assert DEVOTED not in fighter.global_effects.tags, profile
        assert HATRED not in fighter.global_effects.tags, profile


@pytest.mark.phase2_construction
def test_the_supplied_vampire_condition_projects_only_for_a_recipient():
    assert "condition.devoted-vampire-down" in lahmain("beloved", down=True).global_effects.tags
    assert "condition.devoted-vampire-killed" in lahmain("lackeys", killed=True).global_effects.tags
    # Negative control: the condition is not a fact any profile may declare.
    with pytest.raises(ValueError, match="Devoted to the Vampire"):
        compile_fighter(FighterBuild("mordheim", band_id="masters-of-horror-sylv",
            profile_id="the-bitten", main_weapon_id="weapon.mace",
            trait_overrides={"devoted_vampire_down": True}))
    # The Vampire is Knocked Down or dead, never both at once.
    with pytest.raises(ValueError, match="Knocked Down and killed"):
        lahmain("beloved", down=True, killed=True)
