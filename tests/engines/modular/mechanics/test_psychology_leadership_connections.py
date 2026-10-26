"""The canonical Psychology/Leadership connections.

Each newly bound band rule is proved the way the plan asks a *connection* to be
proved: the canonical compiler reaches the shared operator for the printed
recipient, an unselected or non-recipient build stays without it, and one real
phase consequence is exercised where the operator's own suite does not already
have one.  Behaviour of the shared operators is deliberately not re-tested.
"""
from __future__ import annotations

import sys
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.state import initialize_duel
from tests.engines.shared.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
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


def bare(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour", **options))


# --- Fear and its immunity --------------------------------------------------

def test_causes_fear_charges_the_opponent_for_a_die(precompiled):
    compiled = precompiled()
    plain, troll = compiled.first, compiled.second
    assert causes_fear(troll, plain)
    dice = StrictDice([{"key": "round.0.first.fear.charge.0", "value": 6},
                       {"key": "round.0.first.fear.charge.1", "value": 6}])
    state = initialize_duel(plain, troll, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(plain, troll, state, dice, StrictDecisions([]))
    dice.finish()
    assert not result.engaged and result.failed_charges == frozenset({"first"})


def test_fear_immunity_waives_the_fear_die_for_its_recipient(precompiled):
    compiled = precompiled()
    golem, attacker = compiled.first, compiled.second
    dice = StrictDice([])
    state = initialize_duel(golem, attacker, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(golem, attacker, state, dice, StrictDecisions([]))
    dice.finish()
    assert result.engaged and not result.failed_charges


# --- Stupidity, Frenzy, automatic and handler Leadership --------------------

def test_automatic_leadership_auto_passes_a_required_test():
    ruffian = canonical("ostlanders", "ruffians")
    assert "mechanic.automatic-leadership" in ruffian.global_effects.tags
    dice = StrictDice([])
    state = initialize_duel(ruffian, bare(), StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(
        ruffian, state, dice, StrictDecisions([]), "probe", first=True,
        psychology=True, fear=True)
    dice.finish()
    assert passed
    assert "mechanic.automatic-leadership" not in canonical("ostlanders", "jaeger").global_effects.tags
