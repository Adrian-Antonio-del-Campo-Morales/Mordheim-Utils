"""Construction contracts for the construct trait projection.

The two checks moved here own the compiler: they assert which printed profiles
of the Clockworkers band carry the construct poison/no-pain consequences, and
that the same band's human heroes stay without them.  The execution of the
poison transport belongs to the modular suite and stays there.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest


def canonical(band, profile, *, collection="mordheim", rules=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", special_rule_ids=tuple(rules), **options))


#: The ``band--constructs`` recipients: exactly the two profiles whose records
#: print the clause, never the band's human heroes.
CONSTRUCTS = ("clockwork-soldiers", "clockwork-fiend")
#: Same band, same band-wide record, profiles that do not print the clause.
HUMANS = ("master-of-clocks", "dwarf-engineer")


@pytest.mark.phase2_construction
def test_the_constructs_reach_the_poison_and_no_pain_connections():
    for profile in CONSTRUCTS:
        compiled = canonical("clockworkers-sc", profile)
        assert compiled.global_effects.poison_immunity, profile
        assert "poison_immune" in compiled.global_effects.tags, profile
        assert "skill.ignore-pain" in compiled.global_effects.tags, profile


@pytest.mark.phase2_construction
def test_the_bands_human_heroes_stay_without_the_construct_consequences():
    for profile in HUMANS:
        compiled = canonical("clockworkers-sc", profile)
        assert not compiled.global_effects.poison_immunity, profile
        assert "poison_immune" not in compiled.global_effects.tags, profile
        assert "skill.ignore-pain" not in compiled.global_effects.tags, profile
