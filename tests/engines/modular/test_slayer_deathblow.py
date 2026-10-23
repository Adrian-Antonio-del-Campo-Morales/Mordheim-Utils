"""C05a combat: the printed Slayer Deathblow and the declared True Grit chart.

Deathblow is the printed Slayer skill whose content is *not* the Deathbringer
Death Blow: a Slayer taken out of action in hand-to-hand makes the attacks he
has still to make, and the printed clause says he may do it even while knocked
down or stunned.  The cases below drive the real round pipeline through the
transport the duel uses, and the control proves an already-resolved pool is
never repeated.  The True Grit case proves the shared injury operator prefers
the declared 1-3/4-5/6 chart over the Hard to Kill threshold that a bare
``out_of_action_threshold`` 6 would describe.
"""
import sys
from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.kernel import require_optimized_support
from mordheim_combat.modular.contexts import _injury_context
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_core.models import DuelContext, EffectSet, FighterBuild
from mordheim_knowledge.loader import knowledge_root


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


ROOT = knowledge_root()


def roll(key, value=1):
    return {"key": key, "value": value}


def kill(side):
    """The rolls one certain attack needs to take the other duelist out."""
    return [roll(f"round.0.{side}.attack.0.wound", 5), roll(f"round.0.{side}.attack.0.injury.0", 5)]


def run(first, second, rolls, *, transform=None, choices=()):
    dice, decisions = StrictDice(rolls), StrictDecisions(list(choices))
    state = initialize_duel(first, second, dice,
        context=DuelContext(charging=(), active_participant="first"))
    if transform:
        state = transform(state)
    result = resolve_round(first, second, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result, [request.key for request in dice.requests]


@pytest.mark.phase3_rules
def test_a_slayer_killed_before_he_strikes_makes_his_remaining_attacks(precompiled):
    slayer, killer = precompiled().first, precompiled().second
    result, keys = run(killer, slayer, kill("first") + [roll("round.0.second.attack.0.hit"),
                                                       roll("round.0.second.attack.1.hit")],
        choices=[{"key": "round.0.second.deathblow", "value": True}])
    assert result.state.second.condition == phases.Condition.OUT
    # The remainder is exactly the pool the phase allocated: two attacks, once.
    assert keys == ["round.0.first.attack.0.wound", "round.0.first.attack.0.injury.0",
                    "round.0.second.attack.0.hit", "round.0.second.attack.1.hit"]


@pytest.mark.phase3_rules
def test_a_slayer_who_already_struck_makes_no_second_pool(precompiled):
    slayer, killer = precompiled().first, precompiled().second
    result, keys = run(slayer, killer, [roll("round.0.first.attack.0.hit"),
                                         roll("round.0.first.attack.1.hit")] + kill("second"))
    assert result.state.first.condition == phases.Condition.OUT
    # Nothing is duplicated: the Slayer's own pool already resolved.
    assert keys == ["round.0.first.attack.0.hit", "round.0.first.attack.1.hit",
                    "round.0.second.attack.0.wound", "round.0.second.attack.0.injury.0"]


@pytest.mark.phase3_rules
def test_a_successful_deathblow_resolves_the_wound_and_injury(precompiled):
    compiled = precompiled()
    slayer, killer = compiled.first, compiled.second
    result, keys = run(killer, slayer, kill("first") + kill("second"),
        choices=[{"key": "round.0.second.deathblow", "value": True}])
    assert result.state.first.condition == phases.Condition.OUT
    assert result.state.second.condition == phases.Condition.OUT
    assert keys == ["round.0.first.attack.0.wound", "round.0.first.attack.0.injury.0",
                    "round.0.second.attack.0.wound", "round.0.second.attack.0.injury.0"]


@pytest.mark.phase4_modular
def test_deathblow_preserves_the_remainder_after_one_nominated_early_attack(precompiled):
    compiled = precompiled()
    slayer = compiled.first
    killer = compiled.second
    slayer = replace(slayer, global_effects=replace(slayer.global_effects,
        tags=(*slayer.global_effects.tags, "mechanic.nominated-strike-first")))
    rolls = [roll("round.0.first.strike-first.attack.0.hit"), *kill("second"),
             roll("round.0.first.attack.0.hit")]
    result, keys = run(slayer, killer, rolls,
        choices=[{"key": "round.0.first.strike-first.attack.0", "value": True},
                 {"key": "round.0.first.deathblow", "value": True}])
    assert result.state.first.condition == phases.Condition.OUT
    assert keys == [entry["key"] for entry in rolls]


@pytest.mark.phase3_rules
def test_the_printed_clause_survives_being_knocked_down_first(precompiled):
    slayer, killer = precompiled().first, precompiled().second
    # A Knocked Down warrior is removed by the wound itself, so the pool that
    # takes him out of action needs no injury roll here.
    result, keys = run(killer, slayer, [roll("round.0.first.attack.0.wound", 5),
                                        roll("round.0.second.attack.0.hit"),
                                        roll("round.0.second.attack.1.hit")],
        transform=lambda state: replace(state, second=replace(state.second,
            condition=phases.Condition.KNOCKED_DOWN)),
        choices=[{"key": "round.0.second.deathblow", "value": True}])
    assert result.state.second.condition == phases.Condition.OUT
    # The phase allocated no pool to a warrior who was already Knocked Down, so
    # this is the captured remainder the printed clause restores.
    assert keys == ["round.0.first.attack.0.wound",
                    "round.0.second.attack.0.hit", "round.0.second.attack.1.hit"]


@pytest.mark.phase3_rules
def test_a_slayer_without_the_skill_is_removed_without_a_last_pool(precompiled):
    slayer, killer = precompiled().first, precompiled().second
    result, keys = run(killer, slayer, kill("first"))
    assert result.state.second.condition == phases.Condition.OUT
    assert keys == ["round.0.first.attack.0.wound", "round.0.first.attack.0.injury.0"]


@pytest.mark.phase3_rules
def test_the_slayer_may_decline_deathblow(precompiled):
    compiled = precompiled()
    result, keys = run(compiled.first, compiled.second,
        kill("first"), choices=[{"key": "round.0.second.deathblow", "value": False}])
    assert result.state.second.condition == phases.Condition.OUT
    assert keys == ["round.0.first.attack.0.wound", "round.0.first.attack.0.injury.0"]


@pytest.mark.phase0_preflight
def test_deathblow_declares_itself_a_modular_only_operator(precompiled):
    slayer, killer = precompiled().first, precompiled().second
    with pytest.raises(ValueError, match="modular"):
        require_optimized_support(slayer, killer)


@pytest.mark.phase3_rules
def test_tough_as_steel_declares_and_consumes_the_printed_true_grit_chart():
    unit = compile_fighter(FighterBuild("mordheim", band_id="dwarf-slayer-cult-web",
        profile_id="giant-slayer", skill_ids=("skill.tough-as-steel",)), ROOT)
    assert unit.global_effects.true_grit is True
    context = _injury_context(unit, EffectSet(), "test")
    chart = [phases.injury_condition(total, context).name for total in (3, 4, 5, 6)]
    assert chart == ["KNOCKED_DOWN", "STUNNED", "STUNNED", "OUT"]
    # Total 3 is the discriminator: a bare threshold of 6 is Hard to Kill.
    hard = phases.InjuryContext(out_threshold=6, hard_to_kill=True)
    assert phases.injury_condition(3, hard) == phases.Condition.STUNNED
