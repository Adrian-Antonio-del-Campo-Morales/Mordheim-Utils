"""L04: selected canonical Halfling heroes use the accepted Shifty round contract.

The printed profiles and legal mace/dagger choices are unmodified. Free duel
opponents are labelled controls; no foreign skill/loadout is attributed to a
canonical Halfling. S1-S4 composition witnesses remain in the existing suites.
"""
from functools import lru_cache

import numpy as np
import pytest

from mordheim_combat.kernel import compile_duel_plan
from mordheim_combat.modular import duel, simulate_duel as simulate_modular
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.native._combat_compile import compile_duel
from mordheim_combat.vectorized import simulate_batch, simulate_duel, simulate_duel_parallel
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import available_special_rules
from mordheim_core.models import Characteristics, DuelContext, DuelRequest, FighterBuild
from mordheim_knowledge.loader import knowledge_root

BAND = 'halflings-mic'
RULE = 'halfling-elder--shifty'
HEROES = ('halfling-elder', 'halfling-cook', 'halfling-thief', 'halfling-youths')
HENCHMEN = ('halfling-scouts', 'halfling-warriors', 'piggies', 'village-ogre')


def build(profile='halfling-elder', selected=True, **options):
    return FighterBuild('mordheim', band_id=BAND, profile_id=profile,
        main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'),
        special_rule_ids=options.pop('special_rule_ids', (RULE,) if selected else ()), **options)


@lru_cache
def hero(profile='halfling-elder', selected=True):
    return compile_fighter(build(profile, selected))


@pytest.fixture(scope='module')
def opponent():
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 4, 3, 1),
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
def test_canonical_heroes_offer_select_compile_once_and_keep_absence_control(profile):
    assert RULE in available_special_rules(build(profile, False), knowledge_root())
    selected, absent = hero(profile), hero(profile, False)
    assert selected.global_effects.tags.count('skill.shifty') == 1
    assert 'skill.shifty' not in absent.global_effects.tags
    assert selected.characteristics == absent.characteristics
    assert selected.main_weapon == absent.main_weapon
    assert 'weapon.mace' in selected.main_weapon.tags
    assert selected.global_effects.attacks_bonus == absent.global_effects.attacks_bonus == 0
    # The bonus is contextual, never a permanent compiled Attack increment.
    assert selected.characteristics.attacks == 1


@pytest.mark.parametrize('profile', HEROES)
def test_catalogue_offer_roundtrips_into_canonical_rule_selection(profile):
    catalogue = CombatCatalogue()
    choice = next(p for p in catalogue.profiles('mordheim', BAND) if p.profile_id == profile)
    skill = next(s for s in catalogue.skills(choice) if s.rule_id == RULE)
    assert skill.runtime_available and skill.unavailable_reason is None
    assert skill.selection_kind == 'warband_skill'
    ordinary, special = catalogue.skill_rule_ids((skill.id,))
    assert ordinary == () and special == (RULE,)
    assert catalogue.skill_ui_ids(choice, ordinary, special) == (skill.id,)
    assert 'skill.shifty' in compile_fighter(build(profile, special_rule_ids=special)).global_effects.tags


@pytest.mark.parametrize('profile', HENCHMEN)
def test_unpromoted_canonical_henchmen_do_not_offer_or_compile_the_skill(profile):
    assert RULE not in available_special_rules(build(profile, False), knowledge_root())
    with pytest.raises(ValueError, match='special rule is not available'):
        compile_fighter(build(profile))
    control = compile_fighter(build(profile, False, main_weapon_id='weapon.fist'))
    assert 'skill.shifty' not in control.global_effects.tags


def test_foreign_profile_cannot_select_halfling_skill():
    with pytest.raises(ValueError, match='special rule is not available'):
        compile_fighter(FighterBuild('mordheim', band_id='mercenaries',
            profile_id='mercenary-captain', special_rule_ids=(RULE,)))


def test_foreign_profile_cannot_bypass_recipients_with_raw_mechanic_id():
    with pytest.raises(ValueError, match='skills are not available'):
        compile_fighter(FighterBuild('mordheim', band_id='mercenaries',
            profile_id='mercenary-captain', skill_ids=('skill.shifty',)))


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


def test_bonus_does_not_recur_in_later_round_without_another_charge(opponent):
    first = hero()
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


def test_public_modular_request_uses_the_canonical_selection(monkeypatch, opponent):
    dice, decisions = StrictDice([roll('first.shifty'), roll('second'), roll('first')]), StrictDecisions([])
    monkeypatch.setattr(duel, 'SeededDice', lambda seed: dice)
    result = simulate_modular(DuelRequest(hero(), opponent, simulations=1, maximum_rounds=1,
        decision_policy=decisions, context=DuelContext(charging=('second',), active_participant='second')))
    dice.finish()
    decisions.finish()
    assert result.unresolved == 1


def test_canonical_thief_pistol_only_refusal_precedes_any_dice_or_decision(opponent):
    thief = compile_fighter(build('halfling-thief', main_weapon_id='weapon.pistol'))
    dice, decisions = StrictDice([]), StrictDecisions([])
    initial = initialize_duel(thief, opponent, dice,
        context=DuelContext(charging=('second',), active_participant='second'))
    with pytest.raises(ValueError, match='pistol-only bonus allocation is unresolved'):
        resolve_round(thief, opponent, initial, dice, decisions)
    dice.finish()
    decisions.finish()


@pytest.mark.parametrize('second', [False, True])
@pytest.mark.parametrize('backend', ['auto', 'numpy', 'native'])
def test_optimized_entries_explicitly_refuse_the_unported_canonical_skill(second, backend, opponent):
    pair = (opponent, hero()) if second else (hero(), opponent)
    with pytest.raises(ValueError, match='Shifty.*modular'):
        simulate_duel(DuelRequest(*pair, simulations=1), backend=backend)


def test_low_level_optimized_entries_refuse_without_losing_other_guards(opponent):
    pair = (hero(), opponent)
    for call in (lambda: compile_duel_plan(*pair), lambda: compile_duel(*pair),
                 lambda: simulate_batch(*pair, 1, np.random.default_rng(0), 1),
                 lambda: simulate_duel_parallel(DuelRequest(*pair, simulations=1))):
        with pytest.raises(ValueError, match='Shifty.*modular'):
            call()
    compile_duel_plan(hero(selected=False), opponent)
