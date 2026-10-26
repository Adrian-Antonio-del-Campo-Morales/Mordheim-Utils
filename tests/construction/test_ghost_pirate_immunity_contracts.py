"""Construction contracts for the Ghost Pirates poison immunity.

The two checks moved here own the compiler: they assert which printed profiles
the canonical record grants the shared poison immunity to, and that the living
profiles of the same band stay without it.  The execution of that immunity
belongs to the modular suite and stays there.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest


def canonical(band, profile, *, collection="mordheim", rules=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", special_rule_ids=tuple(rules), **options))


#: The five Ghost Pirates rules whose printed sentence is "Immune to Poison,
#: Immune to Psychology, and cause/s Fear".
POISON_IMMUNE_RECIPIENTS = (
    "ghost-captain", "screaming-ghosts", "skeleton-mates", "gibbets", "the-bloated",
)


def test_ghost_pirate_poison_immunity_reaches_every_printed_recipient():
    for profile in POISON_IMMUNE_RECIPIENTS:
        compiled = canonical("ghost-pirates-sar", profile)
        assert compiled.global_effects.poison_immunity, profile
        assert "poison_immune" in compiled.global_effects.tags, profile


def test_the_living_ghost_pirate_profiles_stay_without_the_immunity():
    # Negative control: the same band, the profiles whose printed sentence
    # carries no immunity.
    for profile in ("sea-singer", "the-cursed"):
        compiled = canonical("ghost-pirates-sar", profile)
        assert not compiled.global_effects.poison_immunity, profile
        assert "poison_immune" not in compiled.global_effects.tags, profile
