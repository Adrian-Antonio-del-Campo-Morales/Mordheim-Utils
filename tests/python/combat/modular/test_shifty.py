"""Source-derived Shifty timing cases on the actual modular round pipeline.

Synthetic fixtures isolate the accepted S1-S4 composition contract. Canonical
selection is exercised below and in test_shifty_activation.py without injection.
"""
from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, EffectSet, FighterBuild


def fighter(initiative=5, attacks=1, shifty=False, **options):
    unit = compile_fighter(FighterBuild('mordheim',
        Characteristics(3, 3, 3, 1, initiative, attacks),
        main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'), **options))
    if shifty:
        unit = replace(unit, global_effects=replace(unit.global_effects,
            tags=(*unit.global_effects.tags, 'skill.shifty')))
    return unit


def roll(key, value=1):
    return {'key': key, 'value': value}


def miss(side, index=0, round_index=0):
    return roll(f'round.{round_index}.{side}.attack.{index}.hit')


def run(first, second, rolls, *, charging=('second',), choices=(), transform=None):
    dice, decisions = StrictDice(rolls), StrictDecisions(list(choices))
    state = initialize_duel(first, second, dice,
        context=DuelContext(charging=charging, active_participant='second'))
    if transform:
        state = transform(state)
    result = resolve_round(first, second, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result, dice.requests


@pytest.mark.parametrize('owner', ['first', 'second'])
def test_only_bonus_precedes_charger_and_ordinary_attacks(owner):
    defender, charger = fighter(shifty=True), fighter(initiative=3)
    first, second = (defender, charger) if owner == 'first' else (charger, defender)
    foe = 'second' if owner == 'first' else 'first'
    result, requests = run(first, second,
        [miss(f'{owner}.shifty'), miss(foe), miss(owner)], charging=(foe,))
    assert len(result.attacks) == 3
    assert [request.key for request in requests] == [
        f'round.0.{owner}.shifty.attack.0.hit', f'round.0.{foe}.attack.0.hit',
        f'round.0.{owner}.attack.0.hit']
    assert result.state.first.wounds == result.state.second.wounds == 1


def test_faster_charger_precedes_bonus_in_same_strike_first_tier():
    result, _ = run(fighter(initiative=3, shifty=True), fighter(initiative=5),
        [miss('second'), miss('first.shifty'), miss('first')])
    assert len(result.attacks) == 3


@pytest.mark.parametrize('tie,order', [(1, ['second', 'first.shifty', 'first']),
                                      (6, ['first.shifty', 'second', 'first'])])
def test_bonus_tie_has_explicit_unbiased_die(tie, order):
    run(fighter(shifty=True), fighter(),
        [roll('round.0.first.shifty-priority-tie', tie), *(miss(side) for side in order)])


@pytest.mark.parametrize('charging,order', [((), ['first', 'second']),
                                           (('first',), ['first', 'second'])])
def test_own_charge_and_no_charge_do_not_grant_bonus(charging, order):
    result, _ = run(fighter(shifty=True), fighter(initiative=3),
        [miss(side) for side in order], charging=charging)
    assert len(result.attacks) == 2


def test_absent_skill_preserves_ordinary_dice_order():
    result, _ = run(fighter(), fighter(initiative=3), [miss('second'), miss('first')])
    assert len(result.attacks) == 2


def test_bonus_expires_after_initial_charge_phase():
    first, second = fighter(shifty=True), fighter(initiative=3)
    result, _ = run(first, second, [miss('first.shifty'), miss('second'), miss('first')])
    dice, choices = StrictDice([miss('first', round_index=1), miss('second', round_index=1)]), StrictDecisions([])
    later = resolve_round(first, second, result.state, dice, choices)
    dice.finish()
    choices.finish()
    assert len(later.attacks) == 2 and later.state.round_index == 2


def test_frenzy_does_not_double_separate_bonus():
    first = fighter(attacks=2, shifty=True, preparation_ids=('preparation.mad-cap-mushrooms',))
    result, _ = run(first, fighter(initiative=3),
        [miss('first.shifty'), miss('second'), *(miss('first', i) for i in range(4))])
    assert len(result.attacks) == 6


@pytest.mark.parametrize('tie,order', [(6, ['first.shifty', 'first', 'second.shifty', 'second']),
                                      (1, ['second.shifty', 'second', 'first.shifty', 'first'])])
def test_both_charged_fighters_get_one_bonus_and_reuse_warrior_tie(tie, order):
    result, _ = run(fighter(shifty=True), fighter(shifty=True),
        [roll('round.0.priority-tie', tie), *(miss(side) for side in order)],
        charging=('first', 'second'))
    assert len(result.attacks) == 4


def test_bonus_removal_prevents_both_later_pools():
    result, _ = run(fighter(shifty=True), fighter(initiative=3), [
        roll('round.0.first.shifty.attack.0.hit', 4),
        roll('round.0.first.shifty.attack.0.wound', 4),
        roll('round.0.first.shifty.attack.0.injury.0', 5)])
    assert len(result.attacks) == 1
    assert result.state.second.condition == phases.Condition.OUT


def test_charger_removes_shifty_before_bonus_can_resolve():
    result, _ = run(fighter(initiative=3, shifty=True), fighter(initiative=5), [
        roll('round.0.second.attack.0.hit', 4), roll('round.0.second.attack.0.wound', 4),
        roll('round.0.second.attack.0.injury.0', 5)])
    assert len(result.attacks) == 1
    assert result.state.first.condition == phases.Condition.OUT


@pytest.mark.parametrize('condition', [phases.Condition.STUNNED, phases.Condition.OUT])
def test_incapacitated_warrior_cannot_use_bonus(condition):
    result, _ = run(fighter(shifty=True), fighter(initiative=3), [],
        transform=lambda state: replace(state,
            first=replace(state.first, condition=condition),
            second=replace(state.second, condition=phases.Condition.OUT)))
    assert result.attacks == ()


def test_shifty_and_charged_whip_have_distinct_single_bonuses():
    result, _ = run(fighter(shifty=True, main_weapon_id='weapon.steel-whip'), fighter(initiative=3),
        [miss('first.shifty'), miss('first.whipcrack'), miss('second'), miss('first')])
    assert len(result.attacks) == 4


@pytest.mark.parametrize('main', [True, False])
def test_bonus_weapon_choice_is_separate_from_ordinary_allocation(main):
    # A distinct modifier makes the selected weapon observable in the hit result.
    first = fighter(shifty=True, off_hand_id='weapon.axe')
    first = replace(first, off_hand=replace(first.off_hand, hit_modifier=1))
    result, _ = run(first, fighter(initiative=3),
        [miss('first.shifty'), miss('second'), miss('first'), miss('first', 1)],
        choices=[{'key': 'round.0.first.shifty.main-weapon', 'value': main}])
    assert result.attacks[0].hit_target == (4 if main else 3)
    assert [attack.hit_target for attack in result.attacks[2:]] == [4, 3]


def test_single_bonus_does_not_duplicate_extra_natural_attacks():
    first = fighter(shifty=True)
    first = replace(first, extra_attacks=(EffectSet(),))
    result, _ = run(first, fighter(initiative=3),
        [miss('first.shifty'), miss('second'), miss('first'), miss('first', 1)])
    assert len(result.attacks) == 4


def test_both_charge_bonus_is_not_a_second_bull_charge_replacement():
    first = fighter(shifty=True)
    first = replace(first, global_effects=replace(first.global_effects,
        tags=(*first.global_effects.tags, 'mechanic.bull-charge')))
    result, _ = run(first, fighter(initiative=3),
        [miss('first.shifty'), roll('round.0.first.bull-charge.hit'), miss('second')],
        charging=('first', 'second'),
        choices=[{'key': 'round.0.first.bull-charge', 'value': True}])
    assert len(result.attacks) == 3


def test_strike_last_is_not_erased_by_bonus():
    first = fighter(shifty=True, main_weapon_id='weapon.double-handed-weapon')
    result, _ = run(first, fighter(initiative=3),
        [miss('second'), miss('first.shifty'), miss('first')])
    assert len(result.attacks) == 3


def test_incoming_pool_modifier_is_applied_once_to_combined_attack_count():
    second = fighter(initiative=3)
    second = replace(second, global_effects=replace(second.global_effects, incoming_attacks_modifier=-1))
    result, _ = run(fighter(shifty=True), second, [miss('first.shifty'), miss('second')])
    assert len(result.attacks) == 2


def test_selected_hand_suppression_is_spent_once_across_bonus_and_ordinary():
    first = fighter(initiative=3, shifty=True)
    result, _ = run(first, fighter(initiative=6, main_weapon_id='weapon.kusara-kama'),
        [roll('round.0.second.attack.0.hit', 5), roll('round.0.second.attack.0.wound'), miss('first')])
    assert len(result.attacks) == 2
    assert result.state.first.attack_penalty == 0


def test_lucky_charm_spent_on_bonus_stays_spent_for_ordinary_attack():
    result, _ = run(fighter(shifty=True), fighter(initiative=3, defence_ids=('defence.lucky-charm',)), [
        roll('round.0.first.shifty.attack.0.hit', 4),
        roll('round.0.first.shifty.attack.0.lucky-charm', 6), miss('second'),
        roll('round.0.first.attack.0.hit', 4), roll('round.0.first.attack.0.wound')])
    assert len(result.attacks) == 3 and result.attacks[0].saved
    assert result.state.second.lucky_charm is False


def test_on_fire_prevents_bonus_and_ordinary_attacks():
    result, _ = run(fighter(shifty=True), fighter(initiative=3), [miss('second')],
        transform=lambda state: replace(state, first=replace(state.first, on_fire=True)))
    assert len(result.attacks) == 1


def test_standing_up_retains_strike_last_for_bonus():
    result, _ = run(fighter(shifty=True), fighter(initiative=3),
        [miss('second'), miss('first.shifty'), miss('first')],
        transform=lambda state: replace(state, initial_first_player_turn=True,
            first=replace(state.first, condition=phases.Condition.KNOCKED_DOWN)))
    assert len(result.attacks) == 3


def test_strongman_removes_weapon_strike_last_before_bonus_priority():
    result, _ = run(fighter(shifty=True, main_weapon_id='weapon.double-handed-weapon',
        skill_ids=('skill.strongman',)), fighter(initiative=3),
        [miss('first.shifty'), miss('second'), miss('first')])
    assert len(result.attacks) == 3


def test_suppression_of_selected_off_hand_does_not_remove_main_attack_twice():
    first = fighter(initiative=3, shifty=True, off_hand_id='weapon.axe')
    result, _ = run(first, fighter(initiative=6, main_weapon_id='weapon.kusara-kama'),
        [roll('round.0.second.attack.0.hit', 5), roll('round.0.second.attack.0.wound'),
         miss('first'), miss('first', 1)],
        choices=[{'key': 'round.0.first.shifty.main-weapon', 'value': False},
                 {'key': 'round.0.second.attack.0.kusara-main-hand', 'value': False}])
    assert len(result.attacks) == 3 and result.state.first.hampered_hands == ()


def test_melee_bonus_does_not_create_an_additional_pistol_shot():
    first = fighter(shifty=True, main_weapon_id='weapon.pistol', off_hand_id='weapon.axe')
    second = fighter(initiative=3)
    second = replace(second, characteristics=replace(second.characteristics, wounds=3))
    result, _ = run(first, second, [
        roll('round.0.first.shifty.attack.0.hit', 4), roll('round.0.first.shifty.attack.0.wound', 3),
        miss('second'), roll('round.0.first.attack.0.hit', 4), miss('first', 1),
        roll('round.0.first.attack.0.wound', 3)])
    assert len(result.attacks) == 4
    # S3 axe fails to wound on 3; the one ordinary S4 pistol shot succeeds.
    assert not result.attacks[0].wounded and result.attacks[2].wounded
    assert result.state.second.wounds == 2


@pytest.mark.parametrize('off_hand', [None, 'weapon.pistol'])
def test_pistol_only_bonus_stacks_with_the_ordinary_pistol_attack(off_hand):
    first = fighter(shifty=True, main_weapon_id='weapon.pistol', off_hand_id=off_hand)
    count = 2 if off_hand else 1
    result, requests = run(first, fighter(initiative=3),
        [miss('first.shifty'), miss('second'), *(miss('first', i) for i in range(count))])
    assert len(result.attacks) == count + 2
    assert requests[0].key == 'round.0.first.shifty.attack.0.hit'


def test_removing_provisional_binding_is_detected_by_the_timing_fixture():
    from mordheim_combat_lab.verification.reports import EvidenceMismatch
    first = fighter(shifty=True)
    mutated = replace(first, global_effects=replace(first.global_effects,
        tags=tuple(tag for tag in first.global_effects.tags if tag != 'skill.shifty')))
    with pytest.raises(EvidenceMismatch, match='expected.*shifty'):
        run(mutated, fighter(initiative=3), [miss('first.shifty'), miss('second'), miss('first')])


def test_promoting_entire_pool_is_detected_by_the_timing_fixture(monkeypatch):
    from mordheim_combat_lab.verification.reports import EvidenceMismatch
    original = phases.resolve_priority

    def wrong_priority(context):
        result = original(context)
        if 'skill.shifty' in context.fighter.global_effects.tags:
            return replace(result, priority=1)
        return result

    monkeypatch.setattr(phases, 'resolve_priority', wrong_priority)
    with pytest.raises(EvidenceMismatch, match='expected.*second'):
        run(fighter(shifty=True), fighter(initiative=3),
            [miss('first.shifty'), miss('second'), miss('first')])


def test_whole_pool_staff_mode_replaces_bonus_as_well_as_ordinary_attacks():
    result, _ = run(fighter(shifty=True, main_weapon_id='weapon.serpent-staff'), fighter(initiative=3),
        [miss('first'), miss('second')],
        choices=[{'key': 'round.0.first.serpent-staff', 'value': True}])
    assert len(result.attacks) == 2


def test_declining_staff_mode_keeps_shifty_and_normal_attacks():
    result, _ = run(fighter(shifty=True, main_weapon_id='weapon.serpent-staff'), fighter(initiative=3),
        [miss('first.shifty'), miss('second'), miss('first')],
        choices=[{'key': 'round.0.first.serpent-staff', 'value': False}])
    assert len(result.attacks) == 3


def test_canonical_halfling_skill_is_selected_and_not_automatically_granted():
    unit = compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.mace'))
    assert 'skill.shifty' not in unit.global_effects.tags
    selected = compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.mace',
        special_rule_ids=('halfling-elder--shifty',)))
    assert selected.global_effects.tags.count('skill.shifty') == 1


def test_canonical_selected_skill_reaches_actual_round():
    unit = compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.mace',
        special_rule_ids=('halfling-elder--shifty',)))
    result, _ = run(unit, fighter(initiative=3), [miss('first.shifty'), miss('second'), miss('first')])
    assert len(result.attacks) == 3


def test_unarmed_one_attack_cap_is_preserved_with_bonus_priority():
    result, _ = run(fighter(shifty=True, attacks=3, main_weapon_id='weapon.fist'),
        fighter(initiative=3), [miss('first.shifty'), miss('second')])
    assert len(result.attacks) == 2


@pytest.mark.parametrize('tie,order', [(6, ['first.shifty', 'first.whipcrack', 'second', 'first']),
                                      (1, ['second', 'first.shifty', 'first.whipcrack', 'first'])])
def test_bonus_reuses_existing_whip_tie_without_splitting_warrior_order(tie, order):
    result, _ = run(fighter(shifty=True, main_weapon_id='weapon.steel-whip'), fighter(),
        [roll('round.0.first.whip-priority-tie', tie), *(miss(side) for side in order)])
    assert len(result.attacks) == 4


def test_public_modular_replay_observes_terminal_state_after_bonus():
    from mordheim_combat_lab.verification.parity import replay_duel
    result = replay_duel(fighter(shifty=True), fighter(initiative=3), backend='modular',
        context=DuelContext(charging=('second',), active_participant='second'),
        rolls=[roll('round.0.first.shifty.attack.0.hit', 4),
               roll('round.0.first.shifty.attack.0.wound', 4),
               roll('round.0.first.shifty.attack.0.injury.0', 5)])
    assert result.backend == 'modular'
    assert result.terminal == (0, 1, (1, 0), (0, 4), (frozenset(), frozenset()))


def test_trap_blade_breaks_bonus_weapon_before_ordinary_hit_is_prepared():
    result, _ = run(fighter(shifty=True), fighter(initiative=3, main_weapon_id='weapon.sword-breaker'), [
        roll('round.0.first.shifty.attack.0.hit', 4),
        roll('round.0.first.shifty.attack.0.parry', 5),
        roll('round.0.first.shifty.attack.0.trap-blade', 4), miss('second'),
        roll('round.0.first.attack.0.hit', 4), roll('round.0.first.attack.0.wound', 4)])
    assert result.attacks[0].parried and not result.attacks[-1].wounded
    assert result.state.first.broken_hands == frozenset({'main'})


def test_trap_blade_uses_surviving_hand_without_retaining_second_weapon_bonus():
    second = fighter(initiative=3, main_weapon_id='weapon.sword-breaker')
    second = replace(second, characteristics=replace(second.characteristics, wounds=3))
    result, _ = run(fighter(shifty=True, off_hand_id='weapon.axe'), second, [
        roll('round.0.first.shifty.attack.0.hit', 4),
        roll('round.0.first.shifty.attack.0.parry', 5),
        roll('round.0.first.shifty.attack.0.trap-blade', 4), miss('second'),
        roll('round.0.first.attack.0.hit', 4), roll('round.0.first.attack.0.wound', 4)],
        choices=[{'key': 'round.0.first.shifty.main-weapon', 'value': True}])
    assert len(result.attacks) == 3 and result.state.second.wounds == 2
    assert result.state.first.broken_hands == frozenset({'main'})
