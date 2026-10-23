"""The canonical connections that reuse existing operators.

Each newly bound rule is proved the way the plan asks a *connection* to be
proved: the canonical compiler reaches the shared operator for the printed
recipient, a non-recipient build stays without it, and one real phase
consequence is exercised.  Behaviour of the shared operators themselves is
deliberately not re-tested here.
"""
from __future__ import annotations

import sys
from mordheim_combat.modular.contexts import weapon_against_opponent
from mordheim_core.models import FighterBuild
import pytest


# The frozen-build loader is the only compilation route in this module: the
# fixture below replaces this name with ``load_builds(...).fighter``, so every
# builder keeps its complete FighterBuild and the local ``replace`` calls stay
# untouched, while nothing compiles here.
compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


def canonical(band, profile, *, collection="mordheim", rules=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", special_rule_ids=tuple(rules), **options))


@pytest.mark.phase3_rules
def test_poison_immunity_drops_the_poisoned_contribution_of_the_attack(precompiled):
    # ``first`` is the recorded poisoned skeleton mate, ``second`` the same
    # profile with its ordinary fist weapon.
    compiled = precompiled()
    poisoned, undead = compiled.first, compiled.second
    assert "poison.black-lotus" in poisoned.main_weapon.tags

    living = canonical("ghost-pirates-sar", "sea-singer")

    blocked = weapon_against_opponent(poisoned, undead, poisoned.main_weapon)
    kept = weapon_against_opponent(poisoned, living, poisoned.main_weapon)
    assert "poison.black-lotus" not in blocked.tags
    assert "poison.black-lotus" in kept.tags
