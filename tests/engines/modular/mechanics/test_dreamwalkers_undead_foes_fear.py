"""Dreamwalkers of Morr — conditional Fear immunity (band--undead-foes-no-fear).

"Fearless Against the Undead Servants of Necromancers": no Fear test is taken
when the Fear-causing opponent is a vampire, a necromancer, or one of their
undead followers. Fear against any other enemy
stays normal, and the rule grants no general Fear or psychology immunity.
"""
from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import resolve_fear
from mordheim_combat.modular.state import initialize_duel
from tests.engines.modular.replay import replay_duel
from tests.engines.shared.dice import StrictDecisions, StrictDice
from mordheim_core.models import DuelContext, FighterBuild


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


def dreamer(**options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="dreamwalkers-cult-of-morr-fbg", profile_id="dreamer",
        **options))


def grave_guard(**options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="restless-dead", profile_id="grave-guards", **options))


def roll(key, value, sides=6):
    return {"key": key, "value": value, "sides": sides}


def duel_context():
    return DuelContext(charging=("first",), active_participant="first")


def test_the_band_rule_projects_its_conditional_fear_immunity_tag(precompiled):
    hers = precompiled().first
    assert "mechanic.undead-foes-no-fear" in hers.global_effects.tags
    assert "mechanic.fear-immunity" not in hers.global_effects.tags


def test_an_undead_fear_causing_charger_takes_no_fear_roll_from_the_dreamer(precompiled):
    compiled = precompiled()
    foe, hers = compiled.first, compiled.second
    assert "mechanic.causes-fear" in foe.global_effects.tags
    assert "nature.undead" in foe.global_effects.tags
    result = replay_duel(foe, hers, backend="modular", context=duel_context(),
        rolls=[
            # The undead charge is met without any Fear roll for the dreamer.
            roll("second.guiding-dream", 6),
            roll("round.0.first.attack.0.hit", 1),
            roll("round.0.second.attack.0.hit", 1),
            roll("round.0.second.attack.0.hit.reroll", 1),
        ])
    assert result.winner == 2 and result.rounds == 1
    assert result.conditions == (0, 0)


def test_a_vampire_charger_takes_no_fear_roll_either():
    # The other printed identity: a vampire (species.vampire) who causes Fear
    # without any Undead follower identity.
    from mordheim_core.models import Characteristics, EffectSet
    base = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.sword"))
    foe = replace(base, global_effects=replace(base.global_effects,
        tags=(*base.global_effects.tags, "mechanic.causes-fear", "species.vampire")))
    assert "nature.undead" not in foe.global_effects.tags
    result = replay_duel(foe, dreamer(), backend="modular", context=duel_context(),
        rolls=[
            roll("second.guiding-dream", 6),
            roll("round.0.first.attack.0.hit", 1),
            roll("round.0.second.attack.0.hit", 1),
        ])
    assert result.winner == 2 and result.rounds == 1
    assert result.conditions == (0, 0)


@pytest.mark.parametrize('band', ['undead', 'restless-dead'])
def test_a_canonical_living_necromancer_activates_both_fear_paths(precompiled, band):
    # Fear is a supplied current effect, not a simulated spell. Identity comes
    # from the printed profile, without inferring Undead from its warband.
    compiled = precompiled()
    foe, hers = compiled.first, compiled.second
    assert 'identity.necromancer' in foe.global_effects.tags
    assert 'nature.undead' not in foe.global_effects.tags
    dice = StrictDice([roll('second.guiding-dream', 6)])
    state = initialize_duel(foe, hers, dice, context=duel_context())
    decisions = StrictDecisions([])
    after = resolve_fear(foe, hers, state, dice, decisions)
    assert not after.second.fear_hit_sixes
    assert resolve_local_leadership(hers, state, dice, decisions, 'direct.fear',
                                    first=False, fear=True, opponent=foe)
    dice.finish(); decisions.finish()


def test_fear_stays_normal_against_an_enemy_that_fails_the_condition(precompiled):
    # A living caster that is not a necromancer still causes the ordinary
    # Fear test. Double six actually fails it: the charged dreamer hits on sixes.
    compiled = precompiled()
    foe, hers = compiled.first, compiled.second
    assert "species.vampire" not in foe.global_effects.tags
    assert "nature.undead" not in foe.global_effects.tags
    assert 'identity.spellcaster' in foe.global_effects.tags
    assert 'identity.necromancer' not in foe.global_effects.tags
    dice = StrictDice([roll('second.guiding-dream', 6),
        roll('round.0.second.fear.charged.0', 6), roll('round.0.second.fear.charged.1', 6)])
    state = initialize_duel(foe, hers, dice, context=duel_context())
    decisions = StrictDecisions([])
    after = resolve_fear(foe, hers, state, dice, decisions)
    assert after.second.fear_hit_sixes
    dice.finish(); decisions.finish()
