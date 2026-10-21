"""Trait/construct projection: the admitted construct facts reach the duel.

Each newly bound clause is proved the way the plan asks a *connection* to be
proved: the canonical compiler reaches the shared operator for the printed
recipient, a same-band non-recipient stays without it, and one real consequence
is exercised where the shared operator's own suite does not already have one.
Behaviour of the shared operators is deliberately not re-tested here.
"""
from __future__ import annotations

from mordheim_combat.modular.contexts import weapon_against_opponent
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


@pytest.mark.phase3_rules
def test_construct_poison_immunity_drops_the_poisoned_contribution():
    poisoned = compile_fighter(FighterBuild(
        "mordheim", band_id="ghost-pirates-sar", profile_id="skeleton-mates",
        collection="mordheim", main_weapon_id="weapon.dagger",
        main_poison_id="poison.black-lotus"))
    assert "poison.black-lotus" in poisoned.main_weapon.tags

    construct = canonical("clockworkers-sc", "clockwork-soldiers")
    human = canonical("clockworkers-sc", "master-of-clocks")

    blocked = weapon_against_opponent(poisoned, construct, poisoned.main_weapon)
    kept = weapon_against_opponent(poisoned, human, poisoned.main_weapon)
    assert "poison.black-lotus" not in blocked.tags
    assert "poison.black-lotus" in kept.tags
