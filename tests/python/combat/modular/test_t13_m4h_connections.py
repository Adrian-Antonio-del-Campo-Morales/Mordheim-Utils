"""T13 M4h: the canonical connections that reuse existing operators.

Each newly bound rule is proved the way the plan asks a *connection* to be
proved: the canonical compiler reaches the shared operator for the printed
recipient, a non-recipient build stays without it, and one real phase
consequence is exercised.  Behaviour of the shared operators themselves is
deliberately not re-tested here.
"""
from __future__ import annotations

from mordheim_combat.modular.contexts import weapon_against_opponent
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


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


def test_poison_immunity_drops_the_poisoned_contribution_of_the_attack():
    poisoned = compile_fighter(FighterBuild(
        "mordheim", band_id="ghost-pirates-sar", profile_id="skeleton-mates",
        collection="mordheim", main_weapon_id="weapon.dagger",
        main_poison_id="poison.black-lotus"))
    assert "poison.black-lotus" in poisoned.main_weapon.tags

    undead = canonical("ghost-pirates-sar", "skeleton-mates")
    living = canonical("ghost-pirates-sar", "sea-singer")

    blocked = weapon_against_opponent(poisoned, undead, poisoned.main_weapon)
    kept = weapon_against_opponent(poisoned, living, poisoned.main_weapon)
    assert "poison.black-lotus" not in blocked.tags
    assert "poison.black-lotus" in kept.tags
