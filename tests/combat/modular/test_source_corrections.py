"""Source-derived regressions; research and rulings: docs/modular-remediation.md."""
from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.contexts import _parry_context
from mordheim_combat.modular.contexts import _combined_effect, prepare_armour_context
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.aftermath import _fire_recovery
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import DuelState, initialize_fighter
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import ScriptedDice, AlwaysAccept
from mordheim_core.models import Characteristics, FighterBuild


def fighter(ws=3, strength=3, toughness=3, wounds=3, initiative=3, attacks=1, **options):
    return compile_fighter(FighterBuild(
        'mordheim', characteristics=Characteristics(ws, strength, toughness, wounds, initiative, attacks),
        main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'), **options,
    ))


def state(fighter):
    return initialize_fighter(fighter, ScriptedDice({}), 'init')


def test_broadsword_strongman_exception_does_not_require_two_hands():
    a = fighter(main_weapon_id='weapon.broadsword', skill_ids=('skill.strongman',))
    assert not a.main_weapon.two_handed
    assert phases.resolve_priority(phases.PriorityContext(a, fighter(), first_round=True, charging=True)).priority == 1


def test_spines_cannot_automatically_finish_a_stunned_target():
    from mordheim_combat.modular.aftermath import _spines
    a = fighter(trait_overrides={'spines': True})
    b = fighter()
    _, target, outcomes = _spines(a, b, state(a), replace(state(b), condition=phases.Condition.STUNNED),
        ScriptedDice({'s.wound': 1}), 's')
    assert target.condition == phases.Condition.STUNNED and not outcomes[0].wounded


@pytest.mark.parametrize('charging', [False, True])
def test_strike_last_survives_first_round_unless_strongman(charging):
    opponent = fighter(initiative=1)
    heavy = fighter(main_weapon_id='weapon.double-handed-weapon', initiative=6)
    context = phases.PriorityContext(heavy, opponent, first_round=True, charging=charging)
    assert phases.resolve_priority(context).priority == -1
    strong = fighter(main_weapon_id='weapon.double-handed-weapon', skill_ids=('skill.strongman',))
    assert phases.resolve_priority(replace(context, fighter=strong)).priority == int(charging)


def test_equal_strike_first_tiers_use_initiative_for_two_spears():
    slow = fighter(main_weapon_id='weapon.spear', initiative=1)
    fast = fighter(main_weapon_id='weapon.spear', initiative=6)
    a = phases.resolve_priority(phases.PriorityContext(slow, fast, first_round=True, charged=True))
    b = phases.resolve_priority(phases.PriorityContext(fast, slow, first_round=True, charging=True))
    assert not phases.first_acts_before(a, b, ScriptedDice({}))


@pytest.mark.parametrize('charging', [False, True])
@pytest.mark.parametrize('initiative', [1, 6])
def test_m04_strike_last_controls_whole_round_order(charging, initiative):
    from mordheim_combat_lab.verification.dice import StrictDice
    a = fighter(initiative=initiative, main_weapon_id='weapon.double-handed-weapon')
    b = fighter(initiative=7 - initiative)
    dice = StrictDice([{'key': 'round.0.second.attack.0.hit', 'value': 1},
                       {'key': 'round.0.first.attack.0.hit', 'value': 1}])
    resolve_round(a, b, DuelState(state(a), state(b), first_charged=charging), dice)
    dice.finish()


@pytest.mark.parametrize('charging', [False, True])
@pytest.mark.parametrize('initiative', [1, 6])
@pytest.mark.parametrize('round_index', [0, 1])
def test_m05_spear_order_uses_initiative_in_both_charge_directions(charging, initiative, round_index):
    from mordheim_combat_lab.verification.dice import StrictDice
    a = fighter(initiative=initiative, main_weapon_id='weapon.spear')
    b = fighter(initiative=7 - initiative, main_weapon_id='weapon.spear')
    order = ('first', 'second') if initiative == 6 else ('second', 'first')
    dice = StrictDice([{'key': f'round.{round_index}.{side}.attack.0.hit', 'value': 1} for side in order])
    resolve_round(a, b, DuelState(state(a), state(b), round_index, charging), dice)
    dice.finish()


def test_round_consumes_initialized_initiative():
    a = fighter(initiative=3, preparation_ids=('preparation.crimson-shade',))
    b = fighter(initiative=4)
    sa = initialize_fighter(a, ScriptedDice({'init.crimson-shade': 3}), 'init')
    class OrderedDice(ScriptedDice):
        def __init__(self):
            super().__init__({'round.1.first.attack.0.hit': 1, 'round.1.second.attack.0.hit': 1})
            self.keys = []
        def roll(self, request):
            self.keys.append(request.key)
            return super().roll(request)
    dice = OrderedDice()
    resolve_round(a, b, DuelState(sa, state(b), round_index=1), dice)
    assert dice.keys[0] == 'round.1.first.attack.0.hit'


@pytest.mark.parametrize('value', [5, 6, 10])
def test_natural_six_fails_characteristic_tests(value):
    assert not phases._characteristic_test(value, ScriptedDice({'test': 6}), 'test')
    assert phases._characteristic_test(value, ScriptedDice({'test': 5}), 'test')
    assert phases._characteristic_test(value, ScriptedDice({'test': 6, 'test.reroll': 5}), 'test', reroll=True)


def test_ws_zero_is_automatic_without_a_hit_die():
    result = phases.resolve_hit(phases.HitContext(3, 0), ScriptedDice({}))
    assert result.success and result.roll == 0
    assert not phases.resolve_hit(phases.HitContext(3, 3), ScriptedDice({'hit': 1})).success


@pytest.mark.parametrize('magical,denial,expected', [(False, True, 5), (True, True, 7), (True, False, 5)])
def test_untiring_only_prevents_nonmagical_denial(magical, denial, expected):
    c = phases.ArmourContext(5, strength=6, ignore_armour=denial, armour_save_floor=5,
        armour_cannot_be_ignored=True, magical_attack=magical)
    assert phases.armour_target(c) == expected


@pytest.mark.parametrize('weapon,offhand', [('weapon.fighting-claws', None), ('weapon.dwarf-axe', 'weapon.dwarf-axe')])
def test_equipment_parry_rerolls_do_not_require_a_skill(weapon, offhand):
    defender = fighter(main_weapon_id=weapon, off_hand_id=offhand)
    c = _parry_context(defender, state(defender), fighter().main_weapon, 3, 4, 'p')
    assert phases.resolve_parry(c, ScriptedDice({'p.parry': 1, 'p.parry.reroll': 6})).blocked


def test_frenzy_cannot_exceed_ordinary_fist_cap():
    a = fighter(main_weapon_id='weapon.fist', preparation_ids=('preparation.mad-cap-mushrooms',))
    assert phases.build_attacks(phases.AttackPoolContext(a)).attacks == 1
    ordinary = fighter(attacks=2, off_hand_id='weapon.dagger', preparation_ids=('preparation.mad-cap-mushrooms',))
    assert phases.build_attacks(phases.AttackPoolContext(ordinary)).attacks == 5


def test_stun_from_first_hit_does_not_auto_finish_on_second():
    a, b = fighter(attacks=2), fighter(wounds=1)
    dice = ScriptedDice({'p.attack.0.hit': 4, 'p.attack.1.hit': 4,
        'p.attack.0.wound': 4, 'p.attack.0.injury.0': 3, 'p.attack.1.wound': 1})
    _, result, _ = _resolve_attack_pool(a, b, state(a), state(b), 2, dice,
        key='p', first_round=False, charging=False, decisions=AlwaysAccept())
    assert result.condition == phases.Condition.STUNNED


def test_paralysis_does_not_grant_knockdown_elimination():
    a, b = fighter(), fighter(wounds=3)
    bs = replace(state(b), condition=phases.Condition.PARALYZED)
    _, result, _ = _resolve_attack_pool(a, b, state(a), bs, 1,
        ScriptedDice({'p.attack.0.wound': 4}), key='p', first_round=False,
        charging=False, decisions=AlwaysAccept())
    assert result.condition == phases.Condition.PARALYZED and result.wounds == 2


def test_spittle_tests_on_hit_even_when_wounding_fails():
    a, b = fighter(main_poison_id='poison.spider-spittle'), fighter()
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 4, 'a.spider-spittle': 6, 'a.wound': 1}), key='a')
    assert result.defender.condition == phases.Condition.PARALYZED


@pytest.mark.parametrize('save', ['armour', 'ward'])
def test_m21_spittle_precedes_successful_saving_throws(save):
    from mordheim_combat_lab.verification.dice import StrictDice
    from mordheim_core.models import EffectSet
    a = fighter(main_poison_id='poison.spider-spittle')
    b = fighter(armour_id='armour.heavy-armour') if save == 'armour' else replace(
        fighter(), global_effects=EffectSet(ward_save=5))
    save_key = 'a.armour' if save == 'armour' else 'a.special.ward'
    dice = StrictDice([{'key': 'a.hit', 'value': 4},
        {'key': 'a.spider-spittle', 'value': 6}, {'key': 'a.wound', 'value': 4},
        {'key': save_key, 'value': 6}])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice, key='a')
    dice.finish()
    assert result.saved and result.defender.wounds == 3
    assert result.defender.condition == phases.Condition.PARALYZED


def test_fire_cannot_auto_finish_a_stunned_victim():
    a, b = fighter(), fighter()
    bs = replace(state(b), condition=phases.Condition.STUNNED, on_fire=True)
    result, _, _ = _fire_recovery(b, a, bs, state(a),
        ScriptedDice({'fire.extinguish': 1, 'fire.hit.wound': 1}), 'fire')
    assert result.condition == phases.Condition.STUNNED and result.wounds == 3


def test_burning_hit_does_not_inherit_opponents_offensive_effects():
    from mordheim_core.models import EffectSet
    a = replace(fighter(), global_effects=EffectSet(
        wound_modifier=2, reroll_wounds=True, ignore_armour=True, damage=3))
    b = fighter(armour_id='armour.heavy-armour')
    burning = replace(state(b), on_fire=True)
    # A plain S4 hit fails on 2 against T3; the opponent cannot improve it.
    victim, _, _ = _fire_recovery(b, a, burning, state(a),
        ScriptedDice({'fire.extinguish': 1, 'fire.hit.wound': 2}), 'fire')
    assert victim.wounds == 3
    # The S4 armour modifier makes heavy armour save on 6; no denial applies.
    victim, _, _ = _fire_recovery(b, a, burning, state(a),
        ScriptedDice({'fire.extinguish': 1, 'fire.hit.wound': 4, 'fire.hit.armour': 6}), 'fire')
    assert victim.wounds == 3
    victim, _, _ = _fire_recovery(b, a, burning, state(a),
        ScriptedDice({'fire.extinguish': 1, 'fire.hit.wound': 4, 'fire.hit.armour': 1}), 'fire')
    assert victim.wounds == 2


@pytest.mark.parametrize('rescue_roll,expected', [(1, phases.Condition.STANDING), (6, phases.Condition.OUT)])
def test_fire_resolves_force_of_will_before_returning(rescue_roll, expected):
    a = fighter()
    b = fighter(wounds=1, skill_ids=('mechanic.force-of-will',))
    dice = ScriptedDice({'fire.extinguish': 1, 'fire.hit.wound': 4,
        'fire.hit.injury.0': 5, 'fire.hit.force-of-will.rescue': rescue_roll})
    victim, _, outcomes = _fire_recovery(b, a, replace(state(b), on_fire=True), state(a), dice, 'fire')
    assert victim.condition == expected
    assert 'force-of-will' in victim.resources_spent
    assert outcomes[0].defender == victim


def test_only_active_player_recovers_before_combat():
    a, b = fighter(initiative=1), fighter(initiative=6)
    sa = replace(state(a), condition=phases.Condition.KNOCKED_DOWN)
    result = resolve_round(a, b, DuelState(sa, state(b), round_index=1, first_charged=True),
        ScriptedDice({'round.1.second.attack.0.wound': 1}))
    assert result.state.first.condition == phases.Condition.KNOCKED_DOWN


@pytest.mark.parametrize('paralyzed', [False, True])
def test_m07_four_player_turns_preserve_recovery_fire_and_paralysis_ownership(paralyzed):
    from mordheim_core.models import EffectSet
    from mordheim_combat_lab.verification.dice import StrictDice
    # Suppress ordinary attacks so this sequence isolates recovery ownership.
    effects = EffectSet(tags=('animal_friendship', 'species.animal'))
    a = replace(fighter(initiative=1), global_effects=effects)
    b = replace(fighter(initiative=6), global_effects=effects)
    first_condition = phases.Condition.PARALYZED if paralyzed else phases.Condition.KNOCKED_DOWN
    current = DuelState(replace(state(a), condition=first_condition, on_fire=True),
        replace(state(b), condition=phases.Condition.STUNNED), round_index=1)
    first_expected = ([first_condition] * 3 + [phases.Condition.STANDING] if paralyzed
        else [first_condition] + [phases.Condition.STANDING] * 3)
    second_expected = [phases.Condition.KNOCKED_DOWN] * 2 + [phases.Condition.STANDING] * 2
    for index in range(1, 5):
        assert current.first_player_turn == (index % 2 == 0)
        rolls = []
        if index % 2 == 0:
            rolls = [{'key': f'round.{index}.first.fire.extinguish', 'value': 1},
                     {'key': f'round.{index}.first.fire.hit.wound', 'value': 1}]
            if paralyzed:
                rolls.append({'key': f'round.{index}.first.paralysis', 'value': 6 if index == 2 else 1})
        dice = StrictDice(rolls)
        current = resolve_round(a, b, current, dice).state
        dice.finish()
        assert current.first.condition == first_expected[index - 1]
        assert current.second.condition == second_expected[index - 1]
        assert current.first.on_fire and current.first.wounds == 3


def test_force_of_will_rescues_before_the_remaining_hit():
    a = fighter(attacks=2, initiative=6)
    b = fighter(wounds=1, initiative=1, skill_ids=('mechanic.force-of-will',))
    result = resolve_round(a, b, DuelState(state(a), state(b)), ScriptedDice({
        'round.0.first.attack.0.hit': 4, 'round.0.first.attack.1.hit': 4,
        'round.0.first.attack.0.wound': 4, 'round.0.first.attack.0.injury.0': 5,
        'round.0.first.attack.0.force-of-will.rescue': 1,
        'round.0.first.attack.1.wound': 4, 'round.0.first.attack.1.injury.0': 5,
    }))
    assert result.state.second.condition == phases.Condition.OUT


def test_highest_natural_six_does_not_offer_a_lower_hit_to_parry():
    a, b = fighter(attacks=2), fighter(main_weapon_id='weapon.sword')
    _, _, results = _resolve_attack_pool(a, b, state(a), state(b), 2, ScriptedDice({
        'p.attack.0.hit': 6, 'p.attack.1.hit': 4,
        'p.attack.0.wound': 1, 'p.attack.1.wound': 1,
    }), key='p', first_round=False, charging=False, decisions=AlwaysAccept())
    assert not any(r.parried for r in results)


@pytest.mark.parametrize('roll', range(1, 7))
def test_basic_critical_table_doubles_damage_without_an_injury_roll_at_three_wounds(roll):
    a, b = fighter(), fighter(wounds=3)
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 4, 'a.wound': 6, 'a.critical': roll}), key='a')
    assert result.critical and result.damage == 2 and result.defender.wounds == 1
    assert not result.attacker.critical_available


@pytest.mark.parametrize('roll,armour_save', [(1, True), (2, True), (3, False), (4, False), (5, False), (6, False)])
def test_basic_critical_table_controls_armour_before_damage(roll, armour_save):
    a, b = fighter(), fighter(armour_id='armour.heavy-armour')
    dice = {'a.hit': 4, 'a.wound': 6, 'a.critical': roll}
    if armour_save:
        dice['a.armour'] = 5
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, ScriptedDice(dice), key='a')
    assert result.saved == armour_save
    assert result.defender.wounds == (3 if armour_save else 1)


@pytest.mark.parametrize('critical_roll,condition', [(1, phases.Condition.KNOCKED_DOWN), (3, phases.Condition.KNOCKED_DOWN), (5, phases.Condition.STUNNED)])
def test_only_master_strike_adds_two_to_injury(critical_roll, condition):
    a, b = fighter(main_weapon_id='weapon.sword'), fighter(wounds=1)
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, ScriptedDice({
        'a.hit': 4, 'a.wound': 6, 'a.critical': critical_roll,
        'a.injury.0': 1, 'a.injury.1': 1,
    }), key='a')
    assert result.defender.condition == condition


def test_web_of_steel_changes_the_critical_table_not_every_injury():
    a = fighter(skill_ids=('skill.web-of-steel',))
    b = fighter(armour_id='armour.heavy-armour')
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 4, 'a.wound': 6, 'a.critical': 2}), key='a')
    assert result.damage == 2 and not result.saved


@pytest.mark.parametrize('weapon', ['weapon.pistol', 'weapon.duelling-pistol'])
def test_pistol_total_armour_penalty_is_two(weapon):
    a, b = fighter(main_weapon_id=weapon), fighter(armour_id='armour.gromril-armour')
    c = prepare_armour_context(a, b, state(a), state(b), a.main_weapon, _combined_effect(a, a.main_weapon))
    assert phases.armour_target(c) == 6


def test_dark_elf_blade_changes_stun_boundary_without_flat_injury_bonus():
    a = fighter(main_weapon_id='weapon.sword', main_material_id='material.dark-elf-blade')
    b = fighter(wounds=1)
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 4, 'a.wound': 4, 'a.injury.0': 4}), key='a')
    assert result.defender.condition == phases.Condition.STUNNED


def test_lotus_can_crit_and_a_failed_attempt_keeps_automatic_wound():
    a, b = fighter(main_poison_id='poison.black-lotus'), fighter()
    for wound, damage in [(1, 1), (6, 2)]:
        dice = {'a.hit': 6, 'a.wound': wound}
        if wound == 6:
            dice['a.critical'] = 1
        result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, ScriptedDice(dice), key='a')
        assert result.damage == damage


def test_weapon_disadvantages_reach_the_consumers():
    a, b = fighter(main_weapon_id='weapon.brass-knuckles', initiative=4), fighter(initiative=3)
    assert phases.resolve_priority(phases.PriorityContext(a, b)).initiative == 2
    a = fighter(main_weapon_id='weapon.pirate-scourge')
    c = prepare_armour_context(a, b, state(a), state(b), a.main_weapon, _combined_effect(a, a.main_weapon))
    assert phases.armour_target(c) == 6


def test_rapier_barrage_continues_after_two_failed_wounds():
    a, b = fighter(main_weapon_id='weapon.rapier'), fighter()
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, ScriptedDice({
        'a.hit': 4, 'a.wound': 1,
        'a.barrage.1.hit': 5, 'a.barrage.1.wound': 1,
        'a.barrage.2.hit': 6, 'a.barrage.2.wound': 4,
        'a.barrage.2.armour': 1,
    }), key='a')
    assert result.defender.wounds == 2


def test_rapier_first_continuation_really_requires_five_to_hit():
    a, b = fighter(main_weapon_id='weapon.rapier'), fighter()
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, ScriptedDice({
        'a.hit': 4, 'a.wound': 1, 'a.barrage.1.hit': 4,
    }), key='a')
    assert result.hit_target == 5 and not result.wounded
    assert result.defender.wounds == 3


@pytest.mark.parametrize('ending', ['miss', 'save', 'critical'])
def test_m10_barrage_three_continuations_cap_and_full_resolution(ending):
    from mordheim_combat_lab.verification.dice import StrictDice
    a, b = fighter(main_weapon_id='weapon.rapier'), fighter()
    rolls = [{'key': 'a.hit', 'value': 4}, {'key': 'a.wound', 'value': 1}]
    for index in range(1, 4):
        rolls.extend([{'key': f'a.barrage.{index}.hit', 'value': min(6, 4 + index)},
                      {'key': f'a.barrage.{index}.wound', 'value': 1}])
    rolls.append({'key': 'a.barrage.4.hit', 'value': 5 if ending == 'miss' else 6})
    if ending != 'miss':
        rolls.append({'key': 'a.barrage.4.wound', 'value': 6 if ending == 'critical' else 4})
        rolls.append({'key': 'a.barrage.4.critical' if ending == 'critical' else 'a.barrage.4.armour', 'value': 6})
    dice = StrictDice(rolls)
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice, key='a')
    dice.finish()
    assert result.defender.wounds == (1 if ending == 'critical' else 3)
    assert result.critical == (ending == 'critical')
    assert result.saved == (ending == 'save')


def test_m10_barrage_can_be_declined_without_another_roll():
    from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
    a, b = fighter(main_weapon_id='weapon.rapier'), fighter()
    dice = StrictDice([{'key': 'a.hit', 'value': 4}, {'key': 'a.wound', 'value': 1}])
    decisions = StrictDecisions([{'key': 'a.barrage', 'value': False}])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice, key='a', decisions=decisions)
    dice.finish()
    decisions.finish()
    assert result.defender.wounds == 3 and not result.wounded


@pytest.mark.parametrize('bonus', ['material', 'skill'])
def test_lotus_guaranteed_wound_is_not_a_failed_wound_for_rerolls(bonus):
    options = ({'main_material_id': 'material.dark-steel'} if bonus == 'material'
               else {'skill_ids': ('skill.sure-strike',)})
    a, b = fighter(main_poison_id='poison.black-lotus', **options), fighter()
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 6, 'a.wound': 1}), key='a')
    assert result.wounded and not result.critical and result.damage == 1


@pytest.mark.parametrize('damage', [1, 2, 3])
def test_ball_and_chain_damage_is_a_die_not_a_fixed_wound(damage):
    a = fighter(main_weapon_id='weapon.ball-and-chain', preparation_ids=('preparation.mad-cap-mushrooms',))
    b = fighter(wounds=5)
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 4, 'a.wound': 4, 'a.damage': damage}), key='a')
    assert result.damage == damage and result.defender.wounds == 5 - damage


def test_brace_of_pistols_is_two_attacks_even_for_a_three_attack_profile():
    a = fighter(attacks=3, main_weapon_id='weapon.pistol', off_hand_id='weapon.pistol')
    assert phases.build_attacks(phases.AttackPoolContext(a, first_round=True)).attacks == 2


@pytest.mark.parametrize('attacks', [1, 2, 3])
@pytest.mark.parametrize('off_hand', [None, 'weapon.dagger', 'weapon.pistol'])
def test_m09_pistol_allocation_and_next_turn_fallback(attacks, off_hand):
    from mordheim_combat_lab.verification.dice import StrictDice
    a = fighter(attacks=attacks, initiative=6, main_weapon_id='weapon.pistol', off_hand_id=off_hand)
    b = fighter(toughness=4, wounds=10, initiative=1)
    count = 2 if off_hand == 'weapon.pistol' else attacks + 1 if off_hand else 1
    rolls = [{'key': f'round.0.first.attack.{i}.hit', 'value': 4} for i in range(count)]
    rolls += [{'key': f'round.0.first.attack.{i}.wound', 'value': 4} for i in range(count)]
    rolls.append({'key': 'round.0.second.attack.0.hit', 'value': 1})
    dice = StrictDice(rolls)
    current = resolve_round(a, b, DuelState(state(a), state(b)), dice).state
    dice.finish()
    # S4 pistol wounds T4 on 4; the S3 dagger does not. This identifies shots.
    assert current.second.wounds == (8 if off_hand == 'weapon.pistol' else 9)
    remaining = attacks if off_hand == 'weapon.dagger' else 1
    dice = StrictDice([*[{'key': f'round.1.first.attack.{i}.hit', 'value': 1} for i in range(remaining)],
                       {'key': 'round.1.second.attack.0.hit', 'value': 1}])
    result = resolve_round(a, b, current, dice)
    dice.finish()
    assert len(result.attacks) == remaining + 1


def test_disease_dagger_infects_even_if_the_ordinary_wound_fails():
    a, b = fighter(main_weapon_id='weapon.disease-dagger'), fighter()
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 6, 'a.infection': 6, 'a.wound': 1}), key='a')
    assert result.defender.wounds == 2
    assert result.damage == 1 and result.wounded


@pytest.mark.parametrize('test_roll', range(1, 7))
def test_m17_infection_toughness_test_faces(test_roll):
    from mordheim_combat_lab.verification.dice import StrictDice
    a, b = fighter(main_weapon_id='weapon.disease-dagger'), fighter()
    dice = StrictDice([{'key': 'a.hit', 'value': 6},
        {'key': 'a.infection', 'value': test_roll}, {'key': 'a.wound', 'value': 1}])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice, key='a')
    dice.finish()
    assert result.damage == int(test_roll > 3)
    assert result.defender.wounds == 3 - int(test_roll > 3)


def test_m17_undead_or_possessed_skips_infection_test():
    from mordheim_combat_lab.verification.dice import StrictDice
    from mordheim_core.models import EffectSet
    a = fighter(main_weapon_id='weapon.disease-dagger')
    b = replace(fighter(), global_effects=EffectSet(tags=('undead_or_possessed',)))
    dice = StrictDice([{'key': 'a.hit', 'value': 6}, {'key': 'a.wound', 'value': 1}])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice, key='a')
    dice.finish()
    assert result.defender.wounds == 3


def test_lethal_infection_reacts_once_and_cancels_the_remaining_dagger_wound():
    from mordheim_combat.modular.aftermath import _react_to_wound
    a = fighter(main_weapon_id='weapon.disease-dagger')
    b = fighter(wounds=1, trait_overrides={'acid_blood': True})
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 6, 'a.infection': 6, 'a.infection-wound.injury.0': 6,
                      'a.infection-wound.acid-blood.0.wound': 4}), key='a')
    result = _react_to_wound(a, b, result, ScriptedDice({}), 'a')
    assert result.defender.condition == phases.Condition.OUT
    assert result.damage == 1 and result.attacker.wounds == 2


def test_infection_and_dagger_damage_are_reported_together_without_repeating_acid():
    from mordheim_combat.modular.aftermath import _react_to_wound
    a = fighter(main_weapon_id='weapon.disease-dagger')
    b = fighter(trait_overrides={'acid_blood': True})
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon,
        ScriptedDice({'a.hit': 6, 'a.infection': 6, 'a.infection-wound.acid-blood.0.wound': 4,
                      'a.wound': 4, 'a.armour': 1}), key='a')
    result = _react_to_wound(a, b, result, ScriptedDice({'a.acid-blood.0.wound': 4}), 'a')
    assert result.damage == 2 and result.defender.wounds == 1
    assert result.attacker.wounds == 1


def test_kusara_suppresses_a_reply_but_never_its_last_attack():
    a = fighter(initiative=6, main_weapon_id='weapon.kusara-kama')
    for count in (1, 3):
        b = fighter(attacks=count, initiative=1)
        dice = {'round.0.first.attack.0.hit': 5, 'round.0.first.attack.0.wound': 1}
        dice.update({f'round.0.second.attack.{i}.hit': 1 for i in range(max(1, count - 1))})
        result = resolve_round(a, b, DuelState(state(a), state(b)), ScriptedDice(dice))
        assert len(result.attacks) == 1 + max(1, count - 1)


@pytest.mark.parametrize('attacks', [1, 3])
def test_kusara_minimum_is_per_warrior_not_per_whip_event(attacks):
    a = fighter(initiative=6, main_weapon_id='weapon.kusara-kama')
    b = fighter(initiative=1, attacks=attacks, main_weapon_id='weapon.steel-whip')
    result = resolve_round(a, b, DuelState(state(a), state(b)), ScriptedDice({
        'round.0.first.attack.0.hit': 5, 'round.0.first.attack.0.wound': 1,
        **{f'round.0.second.attack.{index}.hit': 1 for index in range(attacks)},
    }))
    assert len(result.attacks) == 1 + attacks


def test_kusara_preserves_off_hand_identity_for_the_whip_bonus():
    from mordheim_core.dice import ScriptedDecisions
    a = fighter(initiative=6, main_weapon_id='weapon.kusara-kama')
    b = fighter(initiative=1, main_weapon_id='weapon.mace', off_hand_id='weapon.steel-whip')
    result = resolve_round(a, b, DuelState(state(a), state(b)), ScriptedDice({
        'round.0.first.attack.0.hit': 5, 'round.0.first.attack.0.wound': 1,
        'round.0.second.attack.0.hit': 1, 'round.0.second.attack.1.hit': 1,
    }), ScriptedDecisions({'round.0.first.attack.0.kusara-main-hand': False}))
    assert len(result.attacks) == 3


@pytest.mark.parametrize('hamper_main,remaining_wounds', [(True, 2), (False, 3)])
def test_kusara_owner_selects_which_weapon_loses_the_reply_attack(hamper_main, remaining_wounds):
    from mordheim_core.dice import ScriptedDecisions
    a = fighter(initiative=6, main_weapon_id='weapon.kusara-kama', armour_id='armour.heavy-armour')
    b = fighter(initiative=1, main_weapon_id='weapon.dagger', off_hand_id='weapon.axe')
    result = resolve_round(a, b, DuelState(state(a), state(b)), ScriptedDice({
        'round.0.first.attack.0.hit': 5, 'round.0.first.attack.0.wound': 1,
        'round.0.second.attack.0.hit': 4, 'round.0.second.attack.0.wound': 4,
        'round.0.second.attack.0.armour': 4,
    }), ScriptedDecisions({'round.0.first.attack.0.kusara-main-hand': hamper_main}))
    assert result.state.first.wounds == remaining_wounds
    assert len(result.attacks) == 2


def test_serpent_staff_replaces_profile_attacks_and_parries():
    a = fighter(ws=1, strength=1, attacks=3, initiative=1, main_weapon_id='weapon.serpent-staff')
    b = fighter(initiative=6)
    result = resolve_round(a, b, DuelState(state(a), state(b), round_index=1), ScriptedDice({
        'round.1.first.attack.0.hit': 3, 'round.1.first.attack.0.wound': 3,
        'round.1.second.attack.0.hit': 4, 'round.1.second.attack.0.wound': 1,
    }))
    assert result.state.second.wounds == 2 and result.state.first.parries_remaining == 0
    assert len(result.attacks) == 2


def test_m27_declining_staff_power_keeps_normal_attacks_stats_and_parry():
    from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
    a = fighter(ws=1, strength=1, attacks=3, initiative=1, main_weapon_id='weapon.serpent-staff')
    b = fighter(initiative=6, strength=1)
    dice = StrictDice([{'key': 'round.1.second.attack.0.hit', 'value': 4},
        {'key': 'round.1.second.attack.0.parry', 'value': 5},
        *[{'key': f'round.1.first.attack.{i}.hit', 'value': 5} for i in range(3)],
        *[{'key': f'round.1.first.attack.{i}.wound', 'value': 4} for i in range(3)]])
    decisions = StrictDecisions([{'key': 'round.1.first.serpent-staff', 'value': False}])
    result = resolve_round(a, b, DuelState(state(a), state(b), round_index=1), dice, decisions)
    dice.finish()
    decisions.finish()
    assert len(result.attacks) == 4 and result.attacks[0].parried
    assert result.state.first.wounds == result.state.second.wounds == 3


def test_trap_blade_breaks_the_weapon_and_next_round_uses_unarmed_fallback():
    from mordheim_combat.modular.equipment import equipment_for_state
    a, b = fighter(main_weapon_id='weapon.sword'), fighter(main_weapon_id='weapon.sword-breaker')
    sa, _, _ = _resolve_attack_pool(a, b, state(a), state(b), 1, ScriptedDice({
        'p.attack.0.hit': 4, 'p.attack.0.parry': 5, 'p.attack.0.trap-blade': 4,
    }), key='p', first_round=True, charging=True, decisions=AlwaysAccept())
    assert sa.broken_hands == frozenset({'main'})
    active = equipment_for_state(a, sa, first_round=False)
    assert active.main_weapon == a.unarmed_weapon and not active.main_weapon.parry


@pytest.mark.parametrize('parry_roll,weapon', [(1, 'weapon.sword'), (5, 'weapon.sword'), (5, 'weapon.fist')])
def test_m25_failed_parry_trap_and_unarmed_boundaries(parry_roll, weapon):
    from mordheim_combat_lab.verification.dice import StrictDice
    a, b = fighter(main_weapon_id=weapon), fighter(main_weapon_id='weapon.sword-breaker')
    rolls = [{'key': 'p.attack.0.hit', 'value': 4}, {'key': 'p.attack.0.parry', 'value': parry_roll}]
    if parry_roll == 1:
        rolls.append({'key': 'p.attack.0.wound', 'value': 1})
    elif weapon != 'weapon.fist':
        rolls.append({'key': 'p.attack.0.trap-blade', 'value': 3})
    dice = StrictDice(rolls)
    attacker_state, _, _ = _resolve_attack_pool(a, b, state(a), state(b), 1, dice,
        key='p', first_round=True, charging=True, decisions=AlwaysAccept())
    dice.finish()
    assert not attacker_state.broken_hands


@pytest.mark.parametrize('off_hand', [None, 'weapon.dagger'])
def test_m25_break_preserves_prepared_hits_and_projects_surviving_equipment(off_hand):
    from mordheim_combat_lab.verification.dice import StrictDice
    from mordheim_combat.modular.equipment import equipment_for_state
    a = fighter(main_weapon_id='weapon.sword', off_hand_id=off_hand)
    b = fighter(main_weapon_id='weapon.sword-breaker')
    rolls = [{'key': 'p.attack.0.hit', 'value': 5}, {'key': 'p.attack.1.hit', 'value': 4},
        {'key': 'p.attack.0.parry', 'value': 6}, {'key': 'p.attack.0.trap-blade', 'value': 4},
        {'key': 'p.attack.1.wound', 'value': 4}]
    if off_hand:
        rolls.append({'key': 'p.attack.1.armour', 'value': 1})
    dice = StrictDice(rolls)
    attacker_state, defender_state, _ = _resolve_attack_pool(a, b, state(a), state(b), 2, dice,
        key='p', first_round=True, charging=True, decisions=AlwaysAccept())
    dice.finish()
    assert defender_state.wounds == 2 and attacker_state.broken_hands == frozenset({'main'})
    active = equipment_for_state(a, attacker_state, first_round=False)
    assert active.main_weapon == (a.off_hand if off_hand else a.unarmed_weapon)
    assert active.main_hand_slot == ('off' if off_hand else 'unarmed')


def test_spent_brace_falls_back_to_unarmed_instead_of_repeated_pistol_attacks():
    from mordheim_combat.modular.equipment import equipment_for_state
    a = fighter(attacks=3, main_weapon_id='weapon.pistol', off_hand_id='weapon.pistol')
    active = equipment_for_state(a, state(a), first_round=False)
    assert active.main_weapon == a.unarmed_weapon and active.off_hand is None
    assert phases.build_attacks(phases.AttackPoolContext(active)).attacks == 1


def test_charged_whip_bonus_precedes_only_the_ordinary_whip_attacks():
    a = fighter(initiative=5)
    b = fighter(initiative=3, main_weapon_id='weapon.steel-whip')
    class OrderedDice(ScriptedDice):
        def __init__(self):
            super().__init__({'round.0.first.attack.0.hit': 1,
                'round.0.second.whipcrack.attack.0.hit': 1, 'round.0.second.attack.0.hit': 1})
            self.keys = []
        def roll(self, request):
            self.keys.append(request.key)
            return super().roll(request)
    dice = OrderedDice()
    resolve_round(a, b, DuelState(state(a), state(b)), dice)
    assert dice.keys == ['round.0.first.attack.0.hit',
        'round.0.second.whipcrack.attack.0.hit', 'round.0.second.attack.0.hit']


def test_two_whips_get_only_one_whipcrack_bonus_after_frenzy():
    from mordheim_combat.modular.rounds import apply_round_weapon_attack_modifiers
    a = fighter(main_weapon_id='weapon.steel-whip', off_hand_id='weapon.steel-whip',
        preparation_ids=('preparation.mad-cap-mushrooms',))
    count = phases.build_attacks(phases.AttackPoolContext(a, first_round=True, charging=True)).attacks
    assert apply_round_weapon_attack_modifiers(a, fighter(), count,
        first_round=True, charging=True, charged=False) == 4
