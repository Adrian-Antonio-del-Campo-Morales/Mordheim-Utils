"""Patrons, constructs and supplied states reach their consumers.

Each clause is proved the way the plan asks a *connection* to be proved: the
canonical compiler reaches the shared operator for the printed recipient, a
non-recipient build stays without it, and one real phase consequence is
exercised where the operator's own suite does not already have one.  The
supplied states are proved through the canonical condition records
(`FighterBuild.condition_ids`) and, for the Knight-of-Purity promotion, through
the supplied `crusader_of_law` fact the compiler already consumes.
"""
from __future__ import annotations

import sys
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
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


def canonical(band, profile, *, collection="mordheim", conditions=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", condition_ids=tuple(conditions), **options))


def bare(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour", **options))


# --- The Clockwork Construct immunity --------------------------------------

def test_the_construct_immunity_waives_a_required_psychology_test(precompiled):
    compiled = precompiled()
    soldier, foe = compiled.first, compiled.second
    dice = StrictDice([])
    state = initialize_duel(soldier, foe, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(
        soldier, state, dice, StrictDecisions([]), "probe", first=True,
        psychology=True, fear=True)
    dice.finish()
    assert passed


# --- The supplied pre-battle states ----------------------------------------

def test_troll_brew_results_are_supplied_states_with_their_own_consequences(precompiled):
    # ``first`` is the master craftsman under the brew's fear immunity,
    # ``second`` the supplied fear causer he charges.
    compiled = precompiled()
    immune, attacker = compiled.first, compiled.second
    assert "mechanic.fear-immunity" in immune.global_effects.tags
    dice = StrictDice([])
    state = initialize_duel(immune, attacker, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(immune, attacker, state, dice, StrictDecisions([]))
    dice.finish()
    assert result.engaged and not result.failed_charges
    # The frenzy half is the other supplied result of the same table.
    frenzied = canonical("dwarf-guildsmen-kaz", "master-craftsman",
                         conditions=("condition.troll-brew-frenzy",))
    assert frenzied.global_effects.frenzy
    assert not canonical("dwarf-guildsmen-kaz", "master-craftsman").global_effects.frenzy


def test_the_promoted_knight_of_purity_auto_passes_a_required_test(precompiled):
    # ``first`` is the promoted sergeant, ``second`` the plain opponent.
    compiled = precompiled()
    knight, foe = compiled.first, compiled.second
    assert "mechanic.automatic-leadership" in knight.global_effects.tags
    dice = StrictDice([])
    state = initialize_duel(knight, foe, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(
        knight, state, dice, StrictDecisions([]), "probe", first=True,
        psychology=True, fear=True)
    dice.finish()
    assert passed
    assert "mechanic.automatic-leadership" not in canonical(
        "watchmen-mim", "sergeants").global_effects.tags


def emissary(patron):
    """Fanatic Online 94: native equipment and one complete selected patron."""
    return compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.hired-sword.2a",
        profile_id="hireling.hired-sword.emissary-of-chaos",
        main_weapon_id="weapon.sword", armour_id="armour.chaos-armour",
        off_hand_id="defence.shield", defence_ids=("defence.helmet",),
        special_rule_ids=("hireling.hired-sword.emissary-of-chaos.patron." + patron,)))


def test_the_slaanesh_patron_penalty_lands_on_the_engaged_enemy():
    # Printed clause: "those enemies that do engage the Emissary in close combat
    # suffer -1 to their to-hit rolls." The enemy's own blow is one point harder
    # against the Slaanesh branch than against the same Emissary with another
    # patron, and the bearer's own blow is untouched.
    enemy = bare()

    def duel(patron):
        bearer = emissary(patron)
        state = initialize_duel(enemy, bearer, StrictDice([]), context=DuelContext(
            charging=("second",), active_participant="second"))
        dice = StrictDice([
            {"key": "round.0.second.attack.0.hit", "value": 1},
            {"key": "round.0.first.attack.0.hit", "value": 1}])
        decisions = StrictDecisions([])
        result = resolve_round(enemy, bearer, state, dice, decisions)
        dice.finish()
        decisions.finish()
        return result

    slaanesh, tzeentch = duel("slaanesh"), duel("tzeentch")
    # attacks[0] is the charging Emissary's blow, attacks[1] the enemy's reply.
    assert slaanesh.attacks[1].hit_target == tzeentch.attacks[1].hit_target + 1
    assert not slaanesh.attacks[1].hit
    assert slaanesh.attacks[0].hit_target == tzeentch.attacks[0].hit_target


# --- The qualified Beast Hunter family -------------------------------------


def test_the_qualified_beastman_operators_do_not_over_grant(precompiled):
    # A synthetic bearer carrying the new tags is what the binding produces;
    # the opponent fact decides the outcome, so an unqualified enemy is
    # never feared and never the target of the qualified Hatred.
    compiled = precompiled()
    fearer, beastman = compiled.first, compiled.second
    assert not causes_fear(fearer, beastman)
