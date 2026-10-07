"""Halfling source: optional first-round Leadership failure misses the first attack."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild, DuelContext, LocalParticipant


def owner():
    return compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.mace',
        special_rule_ids=('halfling-elder--crude-belch',)))


def opponent(*, off=False, leadership=6, shifty=False):
    fighter = compile_fighter(FighterBuild('mordheim',
        Characteristics(3, 3, 3, 2, 3, 1, leadership=leadership),
        main_weapon_id='weapon.mace', off_hand_id='weapon.axe' if off else None))
    # Synthetic discriminators test allocation, not a claim about legal skills/bonuses.
    if off:
        fighter = replace(fighter, off_hand=replace(fighter.off_hand, hit_modifier=1))
    if shifty:
        fighter = replace(fighter, global_effects=replace(fighter.global_effects,
            tags=(*fighter.global_effects.tags, 'skill.shifty')))
    return fighter


def run(enemy, rolls, *, choose=True, context=None, state=None, bonus=False, leader_choices=()):
    halfling = owner()
    dice = StrictDice([{'key': key, 'value': value} for key, value in rolls])
    choices = [] if choose is None else [('round.0.first.crude-belch', choose)]
    choices.extend(leader_choices)
    if bonus:
        choices.append(('round.0.second.shifty.main-weapon', True))
    decisions = StrictDecisions([{'key': key, 'value': value} for key, value in choices])
    if state is None:
        context = context or DuelContext(charging=('first',), active_participant='first')
        state = initialize_duel(halfling, enemy, dice, context=context)
    result = resolve_round(halfling, enemy, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result


@pytest.mark.parametrize('leadership_rolls,choose,enemy_attacks', [
    ((3, 3), True, True), ((6, 6), True, False), ((), False, True),
])
def test_pass_includes_equality_failure_removes_only_attack_and_decline_skips_test(
        leadership_rolls, choose, enemy_attacks):
    rolls = [(f'round.0.first.crude-belch.leadership.{i}', n) for i, n in enumerate(leadership_rolls)]
    rolls += [('round.0.first.attack.0.hit', 1)]
    if enemy_attacks:
        rolls += [('round.0.second.attack.0.hit', 1)]
    result = run(opponent(), rolls, choose=choose)
    assert len(result.attacks) == 2
    assert result.attacks[-1].hit_roll == (1 if enemy_attacks else None)


def test_first_missed_attack_does_not_switch_the_surviving_hand():
    result = run(opponent(off=True), [
        ('round.0.first.crude-belch.leadership.0', 6),
        ('round.0.first.crude-belch.leadership.1', 6),
        ('round.0.first.attack.0.hit', 1),
        ('round.0.second.attack.1.hit', 3),
        ('round.0.second.attack.1.wound', 1),
    ])
    assert [attack.hit_roll for attack in result.attacks] == [1, None, 3]
    assert result.attacks[-1].hit and result.attacks[-1].hit_target == 3


def test_no_repeat_on_later_round():
    enemy = opponent()
    result = run(enemy, [
        ('round.0.first.crude-belch.leadership.0', 6),
        ('round.0.first.crude-belch.leadership.1', 6),
        ('round.0.first.attack.0.hit', 1),
    ])
    later = run(enemy, [('round.1.first.attack.0.hit', 1),
                       ('round.1.second.attack.0.hit', 1)], state=result.state, choose=None)
    assert later.state.round_index == 2
    assert all(attack.hit_roll == 1 for attack in later.attacks)


def test_explicit_no_contact_skips_decision_and_leadership():
    result = run(opponent(), [('round.0.first.attack.0.hit', 1),
                             ('round.0.second.attack.0.hit', 1)], choose=None,
                 context=DuelContext(contacts=(), charging=('first',), active_participant='first'))
    assert all(attack.hit_roll == 1 for attack in result.attacks)


def test_unknown_leadership_and_additional_enemies_fail_before_attack_dice():
    with pytest.raises(ValueError, match='explicit.*Leadership'):
        run(opponent(leadership=None), [])
    enemy = opponent()
    context = DuelContext(nearby=(LocalParticipant('third', 'second', enemy),),
        contacts=(('first', 'third'),), charging=('first',), active_participant='first')
    with pytest.raises(ValueError, match='multi-participant'):
        run(enemy, [], choose=None, context=context)


def test_timed_shifty_bonus_misses_once_and_ordinary_attack_survives():
    result = run(opponent(off=True, shifty=True), [
        ('round.0.first.crude-belch.leadership.0', 6),
        ('round.0.first.crude-belch.leadership.1', 6),
        ('round.0.first.attack.0.hit', 1),
        ('round.0.second.attack.0.hit', 1),
        ('round.0.second.attack.1.hit', 1),
    ], bonus=True)
    # Both charger and Shifty strike first; the canonical Elder has higher I.
    assert [attack.hit_roll for attack in result.attacks] == [1, None, 1, 1]


def canonical(profile, band='cult-of-the-possessed'):
    return compile_fighter(FighterBuild('mordheim', band_id=band,
        profile_id=profile, main_weapon_id='weapon.mace'))


def leader_context(leader, *, distance=6, condition='standing', side='second'):
    return DuelContext(nearby=(LocalParticipant('leader', side, leader, condition),),
        distances=() if distance is None else (('second', 'leader', distance),),
        charging=('first',), active_participant='first')


@pytest.mark.parametrize('choose,distance,condition,side,foreign,passes', [
    (True, 6, 'standing', 'second', False, True),
    (False, 6, 'standing', 'second', False, False),
    (None, 6.01, 'standing', 'second', False, False),
    (None, 6, 'knocked-down', 'second', False, False),
    (None, 6, 'stunned', 'second', False, False),
    (None, 6, 'fleeing', 'second', False, False),
    (None, 6, 'out', 'second', False, False),
    (None, 6, 'standing', 'first', False, False),
    (None, 6, 'standing', 'second', True, False),
])
def test_canonical_leader_changes_the_actual_crude_belch_test(
        choose, distance, condition, side, foreign, passes):
    enemy = canonical('brethren')  # Ld7; Magister Ld8, tested at equality.
    leader = canonical('halfling-elder', 'halflings-mic') if foreign else canonical('magister')
    rolls = [('round.0.first.crude-belch.leadership.0', 4),
             ('round.0.first.crude-belch.leadership.1', 4),
             ('round.0.first.attack.0.hit', 1)]
    if passes:
        rolls.append(('round.0.second.attack.0.hit', 1))
    choices = () if choose is None else [('round.0.first.crude-belch.leadership.leader.leader', choose)]
    result = run(enemy, rolls, context=leader_context(leader,
        distance=distance, condition=condition, side=side), leader_choices=choices)
    assert result.attacks[-1].hit_roll == (1 if passes else None)


def test_missing_provider_facts_fail_before_leadership_dice_and_decline_keeps_own_value():
    enemy, leader = canonical('brethren'), canonical('magister')
    with pytest.raises(ValueError, match='missing distance'):
        run(enemy, [], context=leader_context(leader, distance=None))
    unknown = replace(leader, characteristics=replace(leader.characteristics, leadership=None))
    with pytest.raises(ValueError, match='explicit.*Leadership'):
        run(enemy, [], context=leader_context(unknown), leader_choices=(
            ('round.0.first.crude-belch.leadership.leader.leader', True),))
    result = run(enemy, [('round.0.first.crude-belch.leadership.0', 3),
                         ('round.0.first.crude-belch.leadership.1', 4),
                         ('round.0.first.attack.0.hit', 1),
                         ('round.0.second.attack.0.hit', 1)],
                 context=leader_context(unknown), leader_choices=(
                     ('round.0.first.crude-belch.leadership.leader.leader', False),))
    assert result.attacks[-1].hit_roll == 1


def test_canonical_darksoul_auto_pass_skips_dice_and_provider_facts():
    enemy = canonical('darksouls')
    assert 'mechanic.automatic-leadership' in enemy.global_effects.tags
    assert 'mechanic.automatic-leadership' not in canonical('brethren').global_effects.tags
    enemy = replace(enemy, characteristics=replace(enemy.characteristics, leadership=None))
    result = run(enemy, [('round.0.first.attack.0.hit', 1),
                         ('round.0.second.attack.0.hit', 1)],
                 context=leader_context(canonical('magister'), distance=None))
    assert all(attack.hit_roll == 1 for attack in result.attacks)


@pytest.mark.parametrize('band,leader,recipient', [
    ('halflings-mic', 'halfling-elder', 'halfling-thief'),
    ('shallows-beasts-mim', 'buccaneer', 'renegades'),
])
def test_additional_canonical_leader_recipients(band, leader, recipient):
    # Canonical compilation supplies both membership and the source-bound tag.
    from mordheim_combat.modular.rounds import resolve_crude_belch
    enemy, provider = canonical(recipient, band), canonical(leader, band)
    assert 'mechanic.leader-six' in provider.global_effects.tags
    assert 'mechanic.leader-six' not in enemy.global_effects.tags
    dice = StrictDice([{'key': 'round.0.first.crude-belch.leadership.0', 'value': 4},
                       {'key': 'round.0.first.crude-belch.leadership.1', 'value': 4}])
    decisions = StrictDecisions([
        {'key': 'round.0.first.crude-belch', 'value': True},
        {'key': 'round.0.first.crude-belch.leadership.leader.leader', 'value': True}])
    state = initialize_duel(owner(), enemy, dice, context=leader_context(provider))
    assert resolve_crude_belch(owner(), enemy, state, dice, decisions, first=True) == (False, state)
    dice.finish()
    decisions.finish()
