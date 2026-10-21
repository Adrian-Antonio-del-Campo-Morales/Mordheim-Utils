"""Dreamwalkers of Morr — conditional Fear immunity (band--undead-foes-no-fear).

"Fearless Against the Undead Servants of Necromancers": no Fear test is taken
when the Fear-causing opponent is a vampire, a necromancer, or one of their
undead followers. Fear against any other enemy
stays normal, and the rule grants no general Fear or psychology immunity.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import resolve_fear
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.parity._replay import replay_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import DuelContext, FighterBuild


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


@pytest.mark.compilation
def test_the_band_rule_projects_its_conditional_fear_immunity_tag():
    hers = dreamer()
    assert "mechanic.undead-foes-no-fear" in hers.global_effects.tags
    assert "mechanic.fear-immunity" not in hers.global_effects.tags


@pytest.mark.rule_behavior
def test_an_undead_fear_causing_charger_takes_no_fear_roll_from_the_dreamer():
    foe = grave_guard()
    assert "mechanic.causes-fear" in foe.global_effects.tags
    assert "nature.undead" in foe.global_effects.tags
    result = replay_duel(foe, dreamer(), backend="modular", context=duel_context(),
        rolls=[
            # The undead charge is met without any Fear roll for the dreamer.
            roll("second.guiding-dream", 6),
            roll("round.0.first.attack.0.hit", 1),
            roll("round.0.second.attack.0.hit", 1),
            roll("round.0.second.attack.0.hit.reroll", 1),
        ])
    assert result.winner == 2 and result.rounds == 1
    assert result.conditions == (0, 0)


@pytest.mark.rule_behavior
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
@pytest.mark.rule_behavior
def test_a_canonical_living_necromancer_activates_both_fear_paths(band):
    # Fear is a supplied current effect, not a simulated spell. Identity comes
    # from the printed profile, without inferring Undead from its warband.
    foe = compile_fighter(FighterBuild('mordheim', band_id=band, profile_id='necromancer',
        trait_overrides={'causes_fear': True}))
    assert 'identity.necromancer' in foe.global_effects.tags
    assert 'nature.undead' not in foe.global_effects.tags
    hers = dreamer()
    dice = StrictDice([roll('second.guiding-dream', 6)])
    state = initialize_duel(foe, hers, dice, context=duel_context())
    decisions = StrictDecisions([])
    after = resolve_fear(foe, hers, state, dice, decisions)
    assert not after.second.fear_hit_sixes
    assert resolve_local_leadership(hers, state, dice, decisions, 'direct.fear',
                                    first=False, fear=True, opponent=foe)
    dice.finish(); decisions.finish()


@pytest.mark.rule_behavior
def test_fear_stays_normal_against_an_enemy_that_fails_the_condition():
    # A living caster that is not a necromancer still causes the ordinary
    # Fear test. Double six actually fails it: the charged dreamer hits on sixes.
    foe = compile_fighter(FighterBuild('mordheim', band_id='undead', profile_id='dregs',
        trait_overrides={'causes_fear': True, 'spellcaster': True}))
    assert "species.vampire" not in foe.global_effects.tags
    assert "nature.undead" not in foe.global_effects.tags
    assert 'identity.spellcaster' in foe.global_effects.tags
    assert 'identity.necromancer' not in foe.global_effects.tags
    hers = dreamer()
    dice = StrictDice([roll('second.guiding-dream', 6),
        roll('round.0.second.fear.charged.0', 6), roll('round.0.second.fear.charged.1', 6)])
    state = initialize_duel(foe, hers, dice, context=duel_context())
    decisions = StrictDecisions([])
    after = resolve_fear(foe, hers, state, dice, decisions)
    assert after.second.fear_hit_sixes
    dice.finish(); decisions.finish()
