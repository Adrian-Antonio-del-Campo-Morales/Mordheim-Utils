"""Selected canonical Halfling heroes use the accepted Shifty round contract.

The printed profiles and legal mace/dagger choices are unmodified. Free duel
opponents are labelled controls; no foreign skill/loadout is attributed to a
canonical Halfling. S1-S4 composition witnesses remain in the existing suites.
"""
import sys
from functools import lru_cache

import pytest

from mordheim_combat.modular import duel, simulate_duel as simulate_modular
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, DuelContext, DuelRequest, FighterBuild


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


BAND = 'halflings-mic'
RULE = 'halfling-elder--shifty'
HEROES = ('halfling-elder', 'halfling-cook', 'halfling-thief', 'halfling-youths')


def build(profile='halfling-elder', selected=True, **options):
    return FighterBuild('mordheim', band_id=BAND, profile_id=profile,
        main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'),
        special_rule_ids=options.pop('special_rule_ids', (RULE,) if selected else ()), **options)


@lru_cache
def hero(profile='halfling-elder', selected=True):
    return compile_fighter(build(profile, selected))


@pytest.fixture(scope='module')
def opponent(compiled_builds):
    return compiled_builds.fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 4, 3, 1),
                                       main_weapon_id='weapon.mace'))


def roll(side, face=1, *, round_index=0, index=0):
    return {'key': f'round.{round_index}.{side}.attack.{index}.hit', 'value': face}


def run(first, second, tape, *, charging=('second',), choices=()):
    dice, decisions = StrictDice(tape), StrictDecisions(list(choices))
    initial = initialize_duel(first, second, dice,
        context=DuelContext(charging=charging, active_participant='second'))
    result = resolve_round(first, second, initial, dice, decisions)
    dice.finish()
    decisions.finish()
    assert [r.key for r in dice.requests] == [r['key'] for r in tape]
    return result


@pytest.mark.parametrize('profile', HEROES)
@pytest.mark.parametrize('owner', ('first', 'second'))
def test_actual_canonical_bonus_precedes_charger_but_ordinary_attack_does_not(profile, owner, opponent):
    unit = hero(profile)
    pair = (unit, opponent) if owner == 'first' else (opponent, unit)
    enemy = 'second' if owner == 'first' else 'first'
    result = run(*pair, [roll(f'{owner}.shifty'), roll(enemy), roll(owner)], charging=(enemy,))
    assert len(result.attacks) == 3
    assert result.state.first.wounds == pair[0].characteristics.wounds
    assert result.state.second.wounds == pair[1].characteristics.wounds


@pytest.mark.parametrize('selected,charging', [(False, ('second',)), (True, ()), (True, ('first',))])
def test_absent_not_charged_and_own_charge_controls_have_no_bonus(selected, charging, opponent):
    order = ('second', 'first') if charging == ('second',) else ('first', 'second')
    result = run(hero(selected=selected), opponent, [roll(side) for side in order], charging=charging)
    assert len(result.attacks) == 2


def test_bonus_does_not_recur_in_later_round_without_another_charge(precompiled):
    compiled = precompiled()
    first, opponent = compiled.first, compiled.second
    dice = StrictDice([roll('first.shifty'), roll('second'), roll('first'),
                      roll('first', round_index=1), roll('second', round_index=1)])
    decisions = StrictDecisions([])
    initial = initialize_duel(first, opponent, dice,
        context=DuelContext(charging=('second',), active_participant='second'))
    one = resolve_round(first, opponent, initial, dice, decisions)
    two = resolve_round(first, opponent, one.state, dice, decisions)
    dice.finish()
    decisions.finish()
    assert (len(one.attacks), len(two.attacks)) == (3, 2)


def test_public_modular_request_uses_the_canonical_selection(precompiled, monkeypatch):
    compiled = precompiled()
    dice, decisions = StrictDice([roll('first.shifty'), roll('second'), roll('first')]), StrictDecisions([])
    monkeypatch.setattr(duel, 'SeededDice', lambda seed: dice)
    result = simulate_modular(DuelRequest(compiled.first, compiled.second, simulations=1, maximum_rounds=1,
        decision_policy=decisions, context=DuelContext(charging=('second',), active_participant='second')))
    dice.finish()
    decisions.finish()
    assert result.unresolved == 1


def test_canonical_thief_pistol_bonus_and_shifty_both_execute(precompiled):
    compiled = precompiled()
    thief, opponent = compiled.first, compiled.second
    dice, decisions = StrictDice([roll('first.shifty'), roll('second'), roll('first')]), StrictDecisions([])
    initial = initialize_duel(thief, opponent, dice,
        context=DuelContext(charging=('second',), active_participant='second'))
    result = resolve_round(thief, opponent, initial, dice, decisions)
    assert len(result.attacks) == 3
    dice.finish()
    decisions.finish()


