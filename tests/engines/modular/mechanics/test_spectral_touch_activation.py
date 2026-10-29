"""Canonical Spirit Host compilation reaches the accepted modular consumer.

The host is the actual KB profile, with its default natural attacks. Opponents
are explicit free-selection duel controls, not purported Night Haint loadouts.
The source's six/one-extra-wound/ordinary-wound clauses and accepted Q019 R1-R4
derive the tapes and expectations. Existing synthetic suites cover composition.
"""
from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat.kernel import compile_duel_plan, require_optimized_support
from mordheim_combat.modular import simulate_duel as simulate_modular
from mordheim_combat.modular import duel
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.vectorized import simulate_batch, simulate_duel, simulate_duel_parallel
from tests.engines.shared.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, DuelContext, DuelRequest

BAND = 'call-of-the-night-haint-mim'
RULE = 'spirit-hosts--spectral-touch'
TAG = 'trait.spectral-touch'


@pytest.fixture(scope='module')
def host(cases):
    return cases[
        'unit/modular/test_spectral_touch_activation/'
        'test_canonical_binding_compiles_exact_consumer_tag_and_legal_natural_weapon-0-0'
    ].first


@pytest.fixture(scope='module')
def plain(cases):
    return cases[
        'unit/modular/test_spectral_touch_activation/'
        'test_canonical_three_attack_pool_retains_each_hits_own_six-0-0'
    ].second


def roll(key, value):
    return {'key': key, 'value': value}


def state(fighter):
    dice = StrictDice([])
    result = initialize_fighter(fighter, dice, 'init')
    dice.finish()
    return result


def test_canonical_binding_compiles_exact_consumer_tag_and_legal_natural_weapon(host):
    assert host.characteristics == Characteristics(2, 2, 2, 3, 2, 3, movement=3, leadership=6)
    assert host.global_effects.tags.count(TAG) == 1
    assert 'spectral_touch' not in host.global_effects.tags
    assert 'weapon.natural-attacks' in host.main_weapon.tags
    assert host.off_hand is None
    assert host.extra_attacks == ()


@pytest.mark.parametrize('faces,damages', [((6, 5, 1), (1, 0, 0)),
                                        ((5, 6, 1), (0, 1, 0)),
                                        ((5, 5, 1), (0, 0, 0))])
def test_canonical_three_attack_pool_retains_each_hits_own_six(host, plain, faces, damages):
    tape = [roll(f'test.attack.{i}.hit', face) for i, face in enumerate(faces)]
    tape += [roll(f'test.attack.{i}.wound', 1) for i in (0, 1)]
    dice, decisions = StrictDice(tape), StrictDecisions([])
    _, defender, outcomes = _resolve_attack_pool(host, plain, state(host), state(plain),
        host.characteristics.attacks, dice, key='test', first_round=False,
        charging=False, decisions=decisions)
    dice.finish()
    decisions.finish()
    assert tuple(o.damage for o in outcomes) == damages
    assert defender.wounds == 4 - sum(damages)
    assert [r.key for r in dice.requests] == [r['key'] for r in tape]


def test_canonical_whole_round_runs_without_injected_traits(host, plain):
    tape = [roll(f'round.0.first.attack.{i}.hit', face)
            for i, face in enumerate((6, 5, 1))]
    tape += [roll(f'round.0.first.attack.{i}.wound', 1) for i in (0, 1)]
    tape += [roll('round.0.second.attack.0.hit', 1)]
    dice, decisions = StrictDice(tape), StrictDecisions([])
    context = DuelContext(charging=(), active_participant='first')
    initial = initialize_duel(host, plain, dice, context=context)
    result = resolve_round(host, plain, initial, dice, decisions)
    dice.finish()
    decisions.finish()
    assert result.state.second.wounds == 3
    assert result.state.first.wounds == 3
    assert host.global_effects.tags.count(TAG) == 1


def test_public_modular_request_runs_the_canonical_fighter(monkeypatch, host, plain):
    # Terminal extra wound makes the public result sensitive to activation.
    defender = replace(plain, characteristics=replace(plain.characteristics, wounds=1))
    tape = [roll(f'round.0.first.attack.{i}.hit', face) for i, face in enumerate((6, 5, 1))]
    tape += [roll('round.0.first.attack.0.spectral-touch.injury.0', 5)]
    dice, decisions = StrictDice(tape), StrictDecisions([])
    monkeypatch.setattr(duel, 'SeededDice', lambda seed: dice)
    result = simulate_modular(DuelRequest(host, defender, simulations=1, maximum_rounds=1,
        decision_policy=decisions, context=DuelContext(charging=(), active_participant='first')))
    dice.finish()
    decisions.finish()
    assert (result.first_wins, result.second_wins, result.unresolved) == (1, 0, 0)






