"""Source-specific L06/L07 clauses through canonical compilation and real attacks."""
from dataclasses import replace

import pytest

from mordheim_combat import phases

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.rounds import select_shadow_dance
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.phases import Condition
from mordheim_combat.phases import AttackPoolContext, build_attacks
from mordheim_combat.kernel import require_optimized_support
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild, DuelContext, LocalParticipant


def canonical(band, profile, weapon='weapon.sword', **options):
    return compile_fighter(FighterBuild('mordheim', band_id=band, profile_id=profile,
        main_weapon_id=weapon, **options))


def enemy(strength=3, *, weapon='weapon.mace', armour='armour.no-armour', **options):
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, strength, 3, 2, 3, 1, leadership=7),
        main_weapon_id=weapon, armour_id=armour, **options))


def dancer(*dances, profile='feast-master', **options):
    return canonical('sea-ghosts-mim', profile, 'weapon.sword',
        special_rule_ids=tuple('band--dance-' + dance for dance in dances), **options)


def test_shadow_dance_choice_alternates_without_persistent_bonuses():
    fighter = dancer('storm-of-blades', 'woven-mist')
    foe = enemy()
    dice = StrictDice([
        {'key': key, 'value': 1} for key in (
            'round.0.first.attack.0.hit', 'round.0.first.attack.1.hit', 'round.0.second.attack.0.hit',
            'round.1.second.attack.0.hit',
            'round.2.first.attack.0.hit', 'round.2.first.attack.1.hit', 'round.2.second.attack.0.hit')])
    choices = StrictDecisions([
        {'key': 'round.0.first.dance.storm-of-blades', 'value': True},
        {'key': 'round.1.first.dance.woven-mist', 'value': True},
        {'key': 'round.2.first.dance.storm-of-blades', 'value': True}])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(
        charging=('first',), active_participant='first'))
    for name, count in [('storm-of-blades', 3), ('woven-mist', 1), ('storm-of-blades', 3)]:
        result = resolve_round(fighter, foe, state, dice, choices)
        assert result.state.first.last_shadow_dance == name
        assert len(result.attacks) == count
        state = result.state
    dice.finish(); choices.finish()
    assert fighter.global_effects.attacks_bonus == 0


@pytest.mark.parametrize('dance,rolls,condition,saved', [
    ('whirling-death', [('hit', 4), ('wound', 4), ('injury.0', 4)], Condition.OUT, False),
    ('the-shadows-coil', [('hit', 4), ('parry', 1), ('wound', 4), ('special.ward', 4)], Condition.STANDING, True),
])
def test_shadow_dances_modify_actual_injury_and_magic_save(dance, rolls, condition, saved):
    fighter = dancer(dance)
    init = StrictDice([]); current = initialize_fighter(fighter, init, 'd'); init.finish()
    choices = StrictDecisions([{'key': 'test.dance.' + dance, 'value': True}])
    active, _ = select_shadow_dance(fighter, current, choices, key='test'); choices.finish()
    foe = enemy()
    if dance == 'whirling-death':
        foe = replace(foe, characteristics=replace(foe.characteristics, wounds=1))
        result = strike(active, foe, rolls)
    else:
        foe = replace(foe, main_weapon=replace(foe.main_weapon,
            tags=(*foe.main_weapon.tags, 'attack.magical')))
        result = strike(foe, active, rolls)
    assert result.defender.condition == condition
    assert result.saved is saved


def test_woven_mist_uses_total_attacks_and_initiative_for_first_strike_ties():
    fighter = dancer('woven-mist')
    fighter = replace(fighter, global_effects=replace(fighter.global_effects, frenzy=True))
    init = StrictDice([]); current = initialize_fighter(fighter, init, 'd'); init.finish()
    choices = StrictDecisions([{'key': 'test.dance.woven-mist', 'value': True}])
    active, _ = select_shadow_dance(fighter, current, choices, key='test'); choices.finish()
    assert build_attacks(AttackPoolContext(active, False, False, False, True)).attacks == 1
    assert build_attacks(AttackPoolContext(fighter, False, False, False, True)).attacks == 2
    foe = enemy(weapon='weapon.spear')
    priority = phases.resolve_priority(phases.PriorityContext(active, foe, True, False, True))
    other = phases.resolve_priority(phases.PriorityContext(foe, active, True, True, False))
    assert priority.priority == other.priority == 1
    assert priority.initiative > other.initiative


def test_shadow_dances_require_a_promoted_minstrel_and_cannot_be_declined_when_available():
    with pytest.raises(ValueError, match='not available'):
        dancer('storm-of-blades', profile='minstrels')
    promoted = dancer('storm-of-blades', profile='minstrels', variant_ids=('promotion.hero',))
    init = StrictDice([]); current = initialize_fighter(promoted, init, 'd'); init.finish()
    choices = StrictDecisions([{'key': 'test.dance.storm-of-blades', 'value': False}])
    with pytest.raises(ValueError, match='must choose'):
        select_shadow_dance(promoted, current, choices, key='test')
    choices.finish()
    # One learned dance has no legal repeat next turn, then becomes available again.
    idle, next_state = select_shadow_dance(promoted,
        replace(current, last_shadow_dance='storm-of-blades'), StrictDecisions([]), key='idle')
    assert idle is promoted and next_state.last_shadow_dance is None


def test_woodsmen_staff_uses_printed_strength_not_balanced_initiative():
    woodsman = canonical('woodsmen-de-artois-mou', 'chief', 'weapon.quarter-staff')
    cathayan = canonical('pirates-of-the-cathayan-sea-sar', 'dragon-monk', 'weapon.quarter-staff')
    assert (woodsman.main_weapon.strength_bonus, woodsman.main_weapon.initiative_bonus) == (1, 0)
    assert (cathayan.main_weapon.strength_bonus, cathayan.main_weapon.initiative_bonus) == (0, 1)
    assert strike(woodsman, enemy(), [('hit', 4), ('wound', 3)]).wounded
    assert not strike(cathayan, enemy(), [('hit', 4), ('wound', 3)]).wounded
    sword = canonical('woodsmen-de-artois-mou', 'chief', 'weapon.sword')
    assert (sword.main_weapon.strength_bonus, sword.main_weapon.initiative_bonus) == (0, 0)


def test_woodsmen_staff_keeps_parry_and_two_hand_compatibility():
    woodsman = canonical('woodsmen-de-artois-mou', 'chief', 'weapon.quarter-staff')
    assert woodsman.main_weapon.two_handed and woodsman.main_weapon.parry
    assert strike(enemy(), woodsman, [('hit', 4), ('parry', 5)]).parried
    for off_hand in ('weapon.sword', 'defence.shield', 'defence.buckler'):
        with pytest.raises(ValueError, match='both hands'):
            canonical('woodsmen-de-artois-mou', 'chief', 'weapon.quarter-staff', off_hand_id=off_hand)


def strike(attacker, defender, rolls):
    init = StrictDice([])
    a, d = initialize_fighter(attacker, init, 'a'), initialize_fighter(defender, init, 'd')
    init.finish()
    dice = StrictDice([{'key': 'x.' + key, 'value': value} for key, value in rolls])
    result = resolve_reference_attack(attacker, defender, a, d, attacker.main_weapon, dice, key='x')
    dice.finish()
    return result


@pytest.mark.parametrize('band,profile,rule', [
    ('dark-elves', 'high-born', 'band--dark-elf-special-skills-fey-quickness'),
    ('druchii-mic', 'noble', 'noble--fey-quickness'),
])
def test_fey_quickness_is_acquired_and_combines_with_step_aside(band, profile, rule):
    base = canonical(band, profile, 'weapon.axe')
    assert base.global_effects.ward_save == 7
    for skills, threshold in (((), 6), (('skill.step-aside',), 4)):
        elf = canonical(band, profile, 'weapon.axe',
            special_rule_ids=(rule,), skill_ids=skills)
        # Keep the canonical defence, with two wounds to isolate the save boundary.
        elf = replace(elf, characteristics=replace(elf.characteristics, wounds=2))
        for face, saved in ((threshold, True), (threshold - 1, False)):
            assert strike(enemy(), elf,
                [('hit', 4), ('wound', 4), ('special.ward', face)]).saved is saved


def test_bestial_is_innate_vampire_ward_against_mundane_and_magic():
    vampire = compile_fighter(FighterBuild('mordheim', band_id='strigoi-kaz', profile_id='vampire'))
    assert vampire.global_effects.ward_save == 6
    for magical in (False, True):
        incoming = enemy(strength=4)
        if magical:
            incoming = replace(incoming, main_weapon=replace(incoming.main_weapon,
                tags=(*incoming.main_weapon.tags, 'attack.magical')))
        for face, saved in ((6, True), (5, False)):
            assert strike(incoming, vampire,
                [('hit', 4), ('wound', 4), ('special.ward', face)]).saved is saved
    guard = compile_fighter(FighterBuild('mordheim', band_id='strigoi-kaz', profile_id='charnel-guard'))
    assert guard.global_effects.ward_save == 7


@pytest.mark.parametrize('profile', ['plague-priest', 'plague-champion'])
def test_pestilens_innate_resilience_does_not_stack_with_the_same_selected_skill(profile):
    skaven = canonical('skaven-of-clan-pestilens-mou', profile, 'weapon.dagger')
    repeated = canonical('skaven-of-clan-pestilens-mou', profile, 'weapon.dagger', skill_ids=('skill.resilient',))
    assert skaven.global_effects.incoming_strength_modifier == -1
    assert repeated.global_effects.incoming_strength_modifier == -1
    assert not strike(enemy(), skaven, [('hit', 4), ('wound', 4)]).wounded
    novice = canonical('skaven-of-clan-pestilens-mou', 'monk-initiate', 'weapon.dagger')
    assert novice.global_effects.incoming_strength_modifier == 0


@pytest.mark.parametrize('face,condition', [(3, Condition.STUNNED), (4, Condition.OUT)])
def test_strigoi_bats_use_their_printed_injury_chart_not_bloated_squishy(face, condition):
    bat = compile_fighter(FighterBuild('mordheim', band_id='strigoi-kaz', profile_id='bats'))
    assert 'mechanic.bat-injury-chart' in bat.global_effects.tags
    assert 'rule.squishy' not in bat.global_effects.tags
    assert strike(enemy(weapon='weapon.axe'), bat,
        [('hit', 4), ('wound', 3), ('injury.0', face)]).defender.condition == condition


@pytest.mark.parametrize('fire', [False, True])
def test_fen_hard_to_kill_is_recipient_and_fire_qualified(fire):
    fen = compile_fighter(FighterBuild('mordheim', band_id='fen-guard-mim', profile_id='dryads'))
    control = compile_fighter(FighterBuild('mordheim', band_id='fen-guard-mim', profile_id='branchwych'))
    assert 'mechanic.fen-hard-to-kill' in fen.global_effects.tags
    assert 'mechanic.fen-hard-to-kill' not in control.global_effects.tags
    incoming = enemy()
    if fire:
        incoming = replace(incoming, main_weapon=replace(incoming.main_weapon,
            tags=(*incoming.main_weapon.tags, 'attack.fire')))
    rolls = [('hit', 4), ('wound', 5), ('armour', 1), ('injury.0', 5)]
    if not fire: rolls.append(('helmet', 1))
    assert strike(incoming, fen, rolls).defender.condition == (Condition.OUT if fire else Condition.STUNNED)


@pytest.mark.parametrize('magical,face,saved', [(False, None, False), (True, 4, True), (True, 3, False)])
def test_magical_void_only_saves_against_magic(magical, face, saved):
    master = compile_fighter(FighterBuild('mordheim', band_id='call-of-the-night-haint-mim', profile_id='corpse-master'))
    master = replace(master, characteristics=replace(master.characteristics, wounds=2))
    incoming = enemy()
    if magical:
        incoming = replace(incoming, main_weapon=replace(incoming.main_weapon,
            tags=(*incoming.main_weapon.tags, 'attack.magical')))
    rolls = [('hit', 4), ('wound', 4)]
    if face is not None: rolls.append(('special.ward', face))
    assert strike(incoming, master, rolls).saved is saved
    if magical:
        # A mundane-only ward cannot hide the independent magic-qualified save.
        master = replace(master, global_effects=replace(master.global_effects,
            ward_save=3, ward_save_mundane_only=True))
        assert strike(incoming, master,
            [('hit', 4), ('wound', 4), ('special.ward', 4)]).saved


@pytest.mark.parametrize('fire', [False, True])
def test_hard_to_rattle_has_a_helmet_reaction_except_against_fire(fire):
    fen = compile_fighter(FighterBuild('mordheim', band_id='fen-guard-mim', profile_id='branchwych'))
    incoming = enemy()
    if fire:
        incoming = replace(incoming, main_weapon=replace(incoming.main_weapon,
            tags=(*incoming.main_weapon.tags, 'attack.fire')))
    init = StrictDice([])
    attacker_state = initialize_fighter(incoming, init, 'a')
    defender_state = replace(initialize_fighter(fen, init, 'd'), wounds=1)
    init.finish()
    rolls = [('hit', 4), ('wound', 4), ('armour', 1), ('injury.0', 3)]
    if not fire: rolls.append(('helmet', 4))
    dice = StrictDice([{'key': 'x.' + key, 'value': value} for key, value in rolls])
    result = resolve_reference_attack(incoming, fen, attacker_state, defender_state,
        incoming.main_weapon, dice, key='x')
    dice.finish()
    assert result.defender.condition == (Condition.STUNNED if fire else Condition.KNOCKED_DOWN)
    if not fire:
        dice = StrictDice([{'key': 'x.' + key, 'value': value}
            for key, value in [*rolls[:-1], ('helmet', 3)]])
        result = resolve_reference_attack(incoming, fen, attacker_state, defender_state,
            incoming.main_weapon, dice, key='x')
        dice.finish()
        assert result.defender.condition == Condition.STUNNED


@pytest.mark.parametrize('priest_first', [True, False])
@pytest.mark.parametrize('wound_face,wounded', [(3, False), (4, True)])
def test_priest_bite_follows_both_double_handed_weapons_and_uses_only_own_strength(priest_first, wound_face, wounded):
    priest = canonical('shallows-beasts-mim', 'mutant-priest', 'weapon.double-handed-weapon')
    foe = enemy(weapon='weapon.double-handed-weapon', armour='armour.heavy-armour')
    first, second = (priest, foe) if priest_first else (foe, priest)
    owner, other = ('first', 'second') if priest_first else ('second', 'first')
    dice = StrictDice([{'key': key, 'value': face} for key, face in [
        (f'round.0.{owner}.attack.0.hit', 1),
        (f'round.0.{other}.attack.0.hit', 1),
        (f'round.0.{owner}.last-bite.attack.0.hit', 4),
        (f'round.0.{owner}.last-bite.attack.0.wound', wound_face),
    ] + ([(f'round.0.{owner}.last-bite.attack.0.armour', 4)] if wounded else [])])
    choices = StrictDecisions([])
    state = initialize_duel(first, second, dice, context=DuelContext(charging=(owner,), active_participant=owner))
    result = resolve_round(first, second, state, dice, choices)
    dice.finish(); choices.finish()
    assert [attack.hit_roll for attack in result.attacks] == [1, 1, 4]
    assert result.attacks[-1].wounded is wounded  # S3 needs 4, rather than the weapon's S5.
    assert not result.attacks[-1].saved  # No fist armour bonus.
    assert (result.state.second if priest_first else result.state.first).wounds == (1 if wounded else 2)
    assert not canonical('shallows-beasts-mim', 'renegades').extra_attacks
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(first, second)


@pytest.mark.parametrize('injury,condition', [(1, Condition.KNOCKED_DOWN), (5, Condition.OUT)])
def test_priest_loses_his_late_bite_when_disabled_before_its_event(injury, condition):
    priest = canonical('shallows-beasts-mim', 'mutant-priest', 'weapon.double-handed-weapon')
    foe = enemy(weapon='weapon.double-handed-weapon')
    dice = StrictDice([{'key': key, 'value': face} for key, face in [
        ('round.0.first.attack.0.hit', 1),
        ('round.0.second.attack.0.hit', 4),
        ('round.0.second.attack.0.wound', 3),
        ('round.0.second.attack.0.injury.0', injury),
    ]])
    choices = StrictDecisions([])
    state = initialize_duel(priest, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(priest, foe, state, dice, choices)
    dice.finish(); choices.finish()
    assert len(result.attacks) == 2 and result.state.first.condition == condition


def test_priest_bite_recurs_in_later_rounds_but_stops_when_ordinary_attack_removes_target():
    priest = canonical('shallows-beasts-mim', 'mutant-priest', 'weapon.double-handed-weapon')
    foe = enemy(weapon='weapon.double-handed-weapon')
    init = StrictDice([])
    state = initialize_duel(priest, foe, init, context=DuelContext(charging=('first',), active_participant='first'))
    init.finish()
    for index in (0, 1):
        dice = StrictDice([{'key': f'round.{index}.{label}.attack.0.hit', 'value': 1}
            for label in ('first', 'second', 'first.last-bite')])
        choices = StrictDecisions([])
        result = resolve_round(priest, foe, state, dice, choices)
        dice.finish(); choices.finish()
        assert len(result.attacks) == 3
        state = result.state
    state = replace(state, second=replace(state.second, wounds=1))
    dice = StrictDice([{'key': f'round.2.first.attack.0.{suffix}', 'value': face}
        for suffix, face in [('hit', 4), ('wound', 2), ('injury.0', 5)]])
    choices = StrictDecisions([])
    result = resolve_round(priest, foe, state, dice, choices)
    dice.finish(); choices.finish()
    assert len(result.attacks) == 1 and result.state.second.condition == Condition.OUT


@pytest.mark.parametrize('charging,base,expected', [(True, 1, 2), (True, 3, 2), (False, 3, 3)])
@pytest.mark.parametrize('selection', ['weapon.dagger', 'weapon.fist'])
def test_sabretusk_charge_replaces_profile_attacks_only_during_actual_charge(charging, base, expected, selection):
    cub = canonical('ogre-hunting-party-web', 'sabretusks', selection)
    assert 'weapon.natural-attacks' in cub.main_weapon.tags
    assert build_attacks(AttackPoolContext(cub, first_round=True,
        charging=charging, base_attacks=base)).attacks == expected
    foe = enemy()
    rolls = ([('round.0.second.fear.charged.0', 3), ('round.0.second.fear.charged.1', 4)]
             if charging else [])
    rolls += [(f'round.0.{label}.attack.{i}.hit', 1)
              for label, count in (('first', expected), ('second', 1)) for i in range(count)]
    dice = StrictDice([{'key': key, 'value': value} for key, value in rolls])
    choices = StrictDecisions([])
    state = initialize_duel(cub, foe, dice, context=DuelContext(
        charging=('first',) if charging else (), active_participant='first'))
    state = replace(state, first=replace(state.first, attacks=base))
    result = resolve_round(cub, foe, state, dice, choices)
    dice.finish(); choices.finish()
    assert len(result.attacks) == expected + 1
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(cub, foe)


def test_unerring_strike_reuses_failed_wound_reroll_on_the_canonical_elf():
    elf = canonical('high-elves-lus', 'loremaster',
        special_rule_ids=('band--skill-unerring-strike',))
    result = strike(elf, enemy(), [('hit', 4), ('wound', 1), ('wound.reroll', 4)])
    assert result.wounded and result.defender.wounds == 1
    ordinary = canonical('high-elves-lus', 'loremaster')
    assert not strike(ordinary, enemy(), [('hit', 4), ('wound', 1)]).wounded


def test_seaguard_can_save_one_reroll_for_a_later_miss_and_bonus_expires_after_first_round():
    guard = canonical('lothern-sea-patrol-sar', 'seaguards', 'weapon.spear')
    # Edited A3 discriminates one chosen miss from every failed hit.
    guard = replace(guard, characteristics=replace(guard.characteristics, attacks=3))
    foe = enemy()
    dice = StrictDice([{'key': key, 'value': face} for key, face in [
        ('round.0.first.attack.0.hit', 1),
        ('round.0.first.attack.1.hit', 1),
        ('round.0.first.attack.1.hit.reroll', 4),
        ('round.0.first.attack.2.hit', 1),
        ('round.0.first.attack.1.wound', 3),
        ('round.0.second.attack.0.hit', 1),
    ]])
    choices = StrictDecisions([
        {'key': 'round.0.first.attack.0.spear-master', 'value': False},
        {'key': 'round.0.first.attack.1.spear-master', 'value': True},
    ])
    state = initialize_duel(guard, foe, dice, context=DuelContext(
        charging=('first',), active_participant='first'))
    result = resolve_round(guard, foe, state, dice, choices)
    dice.finish(); choices.finish()
    assert [attack.hit_roll for attack in result.attacks] == [1, 4, 1, 1]
    assert result.state.second.wounds == 1  # S4 wounds T3 on 3.
    assert 'seaguard-spear-master' in result.state.first.resources_spent
    dice = StrictDice([{'key': key, 'value': face} for key, face in [
        ('round.1.first.attack.0.hit', 4),
        ('round.1.first.attack.1.hit', 1),
        ('round.1.first.attack.2.hit', 1),
        ('round.1.first.attack.0.wound', 3),
        ('round.1.second.attack.0.hit', 1),
    ]])
    choices = StrictDecisions([])
    later = resolve_round(guard, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    assert later.state.second.wounds == 1  # S3 now needs 4; no repeat resource.
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(guard, foe)


def test_seaguard_has_no_spear_bonus_on_other_weapon_or_other_profile():
    foe = enemy()
    for guard in (canonical('lothern-sea-patrol-sar', 'seaguards', 'weapon.axe'),
                  canonical('lothern-sea-patrol-sar', 'ships-company', 'weapon.spear')):
        dice = StrictDice([{'key': key, 'value': face} for key, face in [
            ('round.0.first.attack.0.hit', 4),
            ('round.0.first.attack.0.wound', 3),
            ('round.0.second.attack.0.hit', 1),
        ]])
        choices = StrictDecisions([])
        state = initialize_duel(guard, foe, dice, context=DuelContext(
            charging=('first',), active_participant='first'))
        result = resolve_round(guard, foe, state, dice, choices)
        dice.finish(); choices.finish()
        assert not any(attack.wounded for attack in result.attacks)
        assert 'seaguard-spear-master' not in result.state.first.resources_spent


def test_seaguard_does_not_reroll_a_success_or_reroll_an_already_rerolled_failure():
    guard = canonical('lothern-sea-patrol-sar', 'seaguards', 'weapon.spear')
    # Synthetic unrestricted first-round reroll tests composition, not skill access.
    guard = replace(guard, global_effects=replace(guard.global_effects,
        tags=(*guard.global_effects.tags, 'skill.duellist')),
        characteristics=replace(guard.characteristics, attacks=2))
    foe = enemy()
    dice = StrictDice([{'key': key, 'value': face} for key, face in [
        ('round.0.first.attack.0.hit', 4),
        ('round.0.first.attack.1.hit', 1),
        ('round.0.first.attack.1.hit.reroll', 1),
        ('round.0.first.attack.0.wound', 1),
        ('round.0.second.attack.0.hit', 1),
    ]])
    choices = StrictDecisions([])
    state = initialize_duel(guard, foe, dice, context=DuelContext(
        charging=('first',), active_participant='first'))
    result = resolve_round(guard, foe, state, dice, choices)
    dice.finish(); choices.finish()
    assert [attack.hit_roll for attack in result.attacks] == [4, 1, 1]
    assert 'seaguard-spear-master' not in result.state.first.resources_spent


def test_sabretusk_natural_hide_saves_on_five_and_takes_strength_penalties():
    cub = canonical('ogre-hunting-party-web', 'sabretusks', 'weapon.fist')
    assert cub.natural_armour_save == 5
    assert strike(enemy(), cub, [('hit', 4), ('wound', 5), ('armour', 5)]).saved
    assert not strike(enemy(4), cub, [('hit', 4), ('wound', 4), ('armour', 5), ('injury.0', 1)]).saved


def test_domnu_prize_fighter_only_adds_attack_and_removes_penalties_when_unarmed():
    domnu = canonical('channel-rats-mim', 'domnu', 'weapon.fist')
    armed = canonical('channel-rats-mim', 'domnu', 'weapon.mace')
    assert build_attacks(AttackPoolContext(domnu)).attacks == 3
    assert build_attacks(AttackPoolContext(armed)).attacks == 2
    # S4, rather than ordinary unarmed S3, wounds T3 on 3; no enemy armour bonus.
    assert not strike(domnu, enemy(armour='armour.heavy-armour'),
        [('hit', 4), ('wound', 3), ('armour', 5)]).saved


def test_miniath_canonical_native_parry_uses_the_existing_reroll():
    elf = canonical('high-elves-lus', 'loremaster',
        special_rule_ids=('band--skill-miniath',))
    assert strike(enemy(), elf, [('hit', 4), ('parry', 2), ('parry.reroll', 5)]).parried


@pytest.mark.parametrize('step_aside,face', [(False, 6), (True, 4)])
def test_fey_quickness_has_the_printed_melee_save_and_combination(step_aside, face):
    elf = canonical('high-elves-lus', 'sword-wardens', 'weapon.axe',
        special_rule_ids=('band--skill-fey-quickness',),
        skill_ids=('skill.step-aside',) if step_aside else ())
    assert strike(enemy(), elf, [('hit', 4), ('wound', 4), ('special.ward', face)]).saved


@pytest.mark.parametrize('weapon,off,active', [
    ('weapon.long-daggers', None, True),
    ('weapon.dagger', 'weapon.dagger', True),
    ('weapon.dagger', None, False),
    ('weapon.dagger', 'weapon.sword', False),
])
def test_cutthroat_only_changes_saves_for_an_actual_dagger_pair(weapon, off, active):
    rogue = canonical('silent-brotherhood-sc', 'poisoner', weapon,
        off_hand_id=off, special_rule_ids=('band--skill-cutthroat',))
    # Heavy armour normally saves on 5; a normal dagger improves it to 4.
    # Cutthroat cancels that bonus only for the actual pair.
    face = 5 if weapon == 'weapon.long-daggers' else 4
    outcome = strike(rogue, enemy(armour='armour.heavy-armour'),
        [('hit', 4), ('wound', 4), ('armour', face)])
    assert outcome.saved is not active
    assert outcome.defender.wounds == (1 if active else 2)


def test_perfect_killer_is_automatic_and_not_applied_to_the_other_hero():
    master = canonical('silent-brotherhood-sc', 'silent-master')
    poisoner = canonical('silent-brotherhood-sc', 'poisoner')
    assert master.global_effects.armour_penetration == 1
    assert poisoner.global_effects.armour_penetration == 0
    result = strike(master, enemy(armour='armour.gromril-armour'),
        [('hit', 4), ('wound', 3), ('armour', 5)])
    assert not result.saved and result.defender.wounds == 1


@pytest.mark.parametrize('strength,weapon,qualifies', [
    (5, 'weapon.mace', True), (4, 'weapon.mace', False),
    (4, 'weapon.double-handed-weapon', False),
])
def test_bitter_valour_rerolls_wounds_using_natural_strength(strength, weapon, qualifies):
    knight = canonical('knights-of-the-bitter-moors-mim', 'questing-knight',
        special_rule_ids=('band--virtue-of-valour',))
    result = strike(knight, enemy(strength, weapon=weapon),
        [('hit', 4), ('wound', 1)] + ([('wound.reroll', 4)] if qualifies else []))
    assert result.wounded is qualifies
    assert 'skill.virtue-of-valour' not in knight.global_effects.tags
    assert not strike(knight, enemy(5), [('hit', 1)]).hit
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(knight, enemy())


def test_slimy_makes_four_miss_but_keeps_natural_six_and_named_control():
    troll = canonical('orc-pirates-sar', 'sea-troll', 'weapon.fist')
    ordinary = canonical('orc-pirates-sar', 'orc-boyz', 'weapon.mace')
    attacker = enemy()
    assert not strike(attacker, troll, [('hit', 4)]).hit
    assert strike(attacker, troll, [('hit', 6), ('wound', 1)]).hit
    assert strike(attacker, ordinary, [('hit', 4), ('wound', 1)]).hit
    assert ordinary.global_effects.incoming_hit_modifier == 0


@pytest.mark.parametrize('magical,ignore_armour,face,saved', [
    (False, False, 6, True), (True, True, 6, True), (True, True, 5, False),
])
def test_tattoos_are_a_special_save_even_when_armour_is_negated(magical, ignore_armour, face, saved):
    dancer = canonical('sea-ghosts-mim', 'feast-master', 'weapon.halberd')
    assert dancer.natural_armour_save == 7 and dancer.global_effects.ward_save == 6
    ordinary = canonical('sea-ghosts-mim', 'wayfinder')
    assert ordinary.global_effects.ward_save == 7
    attacker = enemy(6)
    # Synthetic incoming properties isolate save immunity; no battle spell is implemented.
    attacker = replace(attacker, main_weapon=replace(attacker.main_weapon,
        ignore_armour=ignore_armour, tags=attacker.main_weapon.tags + (('attack.magical',) if magical else ())))
    outcome = strike(attacker, dancer,
        [('hit', 4), ('wound', 2), ('special.ward', face)] + ([] if saved else [('injury.0', 1)]))
    assert outcome.saved is saved
    if not saved:
        assert outcome.defender.condition == Condition.KNOCKED_DOWN


def test_local_skill_activation_is_offered_and_refuses_a_foreign_band():
    c = CombatCatalogue()
    for band, profile, rule in (
        ('high-elves-lus', 'loremaster', 'band--skill-unerring-strike'),
        ('silent-brotherhood-sc', 'poisoner', 'band--skill-cutthroat'),
        ('knights-of-the-bitter-moors-mim', 'questing-knight', 'band--virtue-of-valour'),
    ):
        choice = next(r for r in c.profiles('mordheim', band) if r.profile_id == profile)
        assert rule in {r.rule_id for r in c.skills(choice) if r.runtime_available}
    with pytest.raises(ValueError):
        canonical('high-elves-lus', 'loremaster', special_rule_ids=('band--skill-cutthroat',))
    # The PDF table, not the original erroneous profile projection, governs access.
    for profile, categories in (
        ('loremaster', {'academic', 'speed', 'special'}),
        ('sword-wardens', {'combat', 'academic', 'strength', 'speed', 'special'}),
        ('rangers', {'shooting', 'speed', 'special'}),
    ):
        choice = next(r for r in c.profiles('mordheim', 'high-elves-lus') if r.profile_id == profile)
        assert set(c.profile(choice)['skill_access']) == categories
        assert 'band--skill-unerring-strike' in {r.rule_id for r in c.skills(choice) if r.runtime_available}


def test_wolf_rat_bite_uses_strength_four_without_an_armour_penalty():
    rat = canonical('skaven-of-clan-moulder-web', 'wolf-rats', 'weapon.dagger')
    assert 'weapon.natural-attacks' in rat.main_weapon.tags
    assert 'poison.black-lotus' not in rat.main_weapon.tags
    # S4 wounds T3 on 3, yet the printed exception retains light armour's 6+.
    assert strike(rat, enemy(armour='armour.light-armour'),
        [('hit', 4), ('wound', 3), ('armour', 6)]).saved
    assert not strike(rat, enemy(), [('hit', 4), ('wound', 2)]).wounded
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(rat, enemy())


@pytest.mark.parametrize('face,immune,wounded', [(6, False, True), (5, False, False), (6, True, False)])
def test_plague_rat_intrinsic_lotus_respects_the_hit_trigger_and_immunity(face, immune, wounded):
    rat = canonical('skaven-of-clan-pestilens-mou', 'plague-rat', 'weapon.dagger')
    assert 'weapon.natural-attacks' in rat.main_weapon.tags
    assert 'poison.black-lotus' in rat.main_weapon.tags
    defender = canonical('blood-dragons-mou', 'vampire', 'weapon.mace') if immune else enemy()
    outcome = strike(rat, defender, [('hit', face), ('wound', 1)])
    assert outcome.wounded is wounded


def test_blood_dragon_no_pain_changes_the_real_injury_result():
    vampire = canonical('blood-dragons-mou', 'vampire', 'weapon.mace')
    # Reduce only remaining wounds to exercise the injury, keeping canonical effects.
    vampire = replace(vampire, characteristics=replace(vampire.characteristics, wounds=1))
    outcome = strike(enemy(), vampire, [('hit', 4), ('wound', 5), ('injury.0', 4)])
    assert outcome.defender.condition == Condition.KNOCKED_DOWN
    ordinary = enemy()
    ordinary = replace(ordinary, characteristics=replace(ordinary.characteristics, wounds=1))
    assert strike(enemy(), ordinary,
        [('hit', 4), ('wound', 4), ('injury.0', 4)]).defender.condition == Condition.STUNNED


def test_poltergeist_incorporeal_uses_existing_immediate_out_before_no_pain():
    ghost = canonical('call-of-the-night-haint-mim', 'poltergeists', 'weapon.dagger')
    assert ghost.injury_profile == 2
    assert 'skill.ignore-pain' in ghost.global_effects.tags
    outcome = strike(enemy(), ghost, [('hit', 4), ('ethereal', 1), ('wound', 2)])
    assert outcome.defender.condition == Condition.OUT
    assert outcome.damage == 1
    # A failed Ethereal save reaches Incorporeal without an injury die.
    assert not strike(enemy(), ghost, [('hit', 4), ('ethereal', 1), ('wound', 1)]).wounded


@pytest.mark.parametrize('face,condition', [(2, Condition.KNOCKED_DOWN), (5, Condition.STUNNED), (6, Condition.OUT)])
def test_slayer_band_binds_the_dwarf_injury_chart_and_concussion_exemption(face, condition):
    dwarf = canonical('dwarf-slayer-cult-web', 'giant-slayer', 'weapon.axe')
    assert 'skill.hard-to-kill' in dwarf.global_effects.tags
    assert 'concussion_immune' in dwarf.global_effects.tags
    result = strike(enemy(), dwarf, [('hit', 4), ('wound', 5), ('injury.0', face)])
    assert result.defender.condition == condition


def test_clan_angrund_selectable_true_grit_and_thick_skull_use_their_printed_operators():
    # The band previously bound True Grit to skill.hard-to-kill (1-2 knocked
    # down) and Thick Skull to the Hard Head concordance trait, so selecting
    # either skill added nothing beyond the band's automatic grants.
    true_grit = canonical(
        'clan-angrund-kep', 'dwarf-noble', 'weapon.axe',
        special_rule_ids=('band--dwarf-special-skills-true-grit',))
    assert 'skill.tough-as-steel' in true_grit.global_effects.tags
    true_grit = replace(true_grit, characteristics=replace(true_grit.characteristics, wounds=1))
    # Printed True Grit: 1-3 Knocked Down, 4-5 Stunned, 6 Out of Action.
    for face, condition in [(3, Condition.KNOCKED_DOWN), (4, Condition.STUNNED),
                            (6, Condition.OUT)]:
        outcome = strike(enemy(), true_grit, [('hit', 4), ('wound', 5), ('injury.0', face)])
        assert outcome.defender.condition == condition

    thick_skull = canonical(
        'clan-angrund-kep', 'dwarf-noble', 'weapon.axe',
        special_rule_ids=('band--dwarf-special-skills-thick-skull',))
    assert thick_skull.global_effects.thick_skull is True
    thick_skull = replace(thick_skull, characteristics=replace(thick_skull.characteristics, wounds=1))
    # 3+ save converts a Stunned result into Knocked Down; a 2 fails.
    saved = strike(enemy(), thick_skull,
                   [('hit', 4), ('wound', 5), ('injury.0', 4), ('thick-skull', 3)])
    assert saved.defender.condition == Condition.KNOCKED_DOWN
    failed = strike(enemy(), thick_skull,
                    [('hit', 4), ('wound', 5), ('injury.0', 4), ('thick-skull', 2)])
    assert failed.defender.condition == Condition.STUNNED


@pytest.mark.parametrize('profile,injury,ward', [
    ('bigsnotz', 1, 6), ('scouts', 1, 6), ('shaman', 1, 6),
    ('shoota-teams', 1, 6), ('runts', 1, 6),
    ('snotling-mobs', 0, 6), ('bullied-goblin', 0, 7), ('wheelo', 0, 7),
])
def test_snotling_defensive_grants_honor_all_three_printed_exceptions(profile, injury, ward):
    fighter = canonical('snotlings-web', profile, 'weapon.dagger')
    assert fighter.injury_profile == injury
    assert fighter.global_effects.ward_save == ward


@pytest.mark.parametrize('profile,face,condition', [
    ('bigsnotz', 2, Condition.STUNNED), ('bigsnotz', 4, Condition.OUT),
    ('snotling-mobs', 2, Condition.KNOCKED_DOWN),
])
def test_snotling_injury_chart_and_mob_exemption_execute_after_failed_dodgy(profile, face, condition):
    fighter = canonical('snotlings-web', profile, 'weapon.dagger')
    fighter = replace(fighter, characteristics=replace(fighter.characteristics, wounds=1))
    outcome = strike(enemy(weapon='weapon.axe'), fighter,
        [('hit', 4), ('wound', 4), ('special.ward', 5), ('injury.0', face)])
    assert outcome.defender.condition == condition


def test_snotling_dodgy_combines_with_step_aside_and_stops_damage():
    hero = canonical('snotlings-web', 'bigsnotz', 'weapon.dagger', skill_ids=('skill.step-aside',))
    assert strike(enemy(), hero,
        [('hit', 4), ('wound', 4), ('special.ward', 4)]).saved


@pytest.mark.parametrize('magical,face,saved', [(False, None, False), (True, 5, True), (True, 4, False)])
def test_domnu_gypsy_ward_only_applies_to_magical_attacks(magical, face, saved):
    domnu = canonical('survivors-of-strigos-sylv', 'domnu', 'weapon.mace')
    incoming = enemy()
    if magical:
        incoming = replace(incoming, main_weapon=replace(incoming.main_weapon,
            tags=incoming.main_weapon.tags + ('attack.magical',)))
    rolls = [('hit', 4), ('wound', 4)]
    if face is not None: rolls.append(('special.ward', face))
    if not saved: rolls.append(('injury.0', 1))
    assert strike(incoming, domnu, rolls).saved is saved
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(incoming, domnu)


def test_domnu_conditional_ward_preserves_a_stronger_save_and_can_survive_a_mundane_only_one():
    domnu = canonical('survivors-of-strigos-sylv', 'domnu', 'weapon.mace')
    incoming = enemy()
    incoming = replace(incoming, main_weapon=replace(incoming.main_weapon,
        tags=incoming.main_weapon.tags + ('attack.magical',)))
    stronger = replace(domnu, global_effects=replace(domnu.global_effects, ward_save=4))
    assert strike(incoming, stronger, [('hit', 4), ('wound', 4), ('special.ward', 4)]).saved
    mundane = replace(domnu, global_effects=replace(domnu.global_effects,
        ward_save=4, ward_save_mundane_only=True))
    assert strike(incoming, mundane, [('hit', 4), ('wound', 4), ('special.ward', 5)]).saved


@pytest.mark.parametrize('hits,kill', [([6, 1, 1, 6, 1], False), ([5, 1, 1], False), ([6, 1, 1, 6, 1], True)])
def test_mourngul_onslaught_recurses_on_physical_sixes_and_retains_pool_interruption(hits, kill):
    mourngul = canonical('call-of-the-night-haint-mim', 'mourngul', 'weapon.dagger')
    opponent = enemy()
    if kill: opponent = replace(opponent, characteristics=replace(opponent.characteristics, wounds=1))
    init = StrictDice([{'key': 'duel.charge', 'value': 6}])
    state = initialize_duel(mourngul, opponent, init)
    init.finish()
    rolls = [('round.0.second.fear.charged.0', 3), ('round.0.second.fear.charged.1', 4)]
    rolls += [(f'round.0.first.attack.{i}.hit', face) for i, face in enumerate(hits)]
    if kill:
        rolls += [('round.0.first.attack.0.wound', 2), ('round.0.first.attack.0.injury.0', 5)]
    else:
        rolls += [(f'round.0.first.attack.{i}.wound', 1) for i, face in enumerate(hits) if face >= 4]
        rolls.append(('round.0.second.attack.0.hit', 1))
    dice = StrictDice([{'key': key, 'value': value} for key, value in rolls])
    choices = StrictDecisions([])
    result = resolve_round(mourngul, opponent, state, dice, decisions=choices)
    dice.finish(); choices.finish()
    if kill:
        assert result.state.second.condition == Condition.OUT
        assert sum(a.wounded for a in result.attacks) == 1
        assert not any(a.wounded for a in result.attacks[1:])
    else:
        assert [a.hit_roll for a in result.attacks[:-1]] == hits
        assert result.state.second.wounds == 2
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(mourngul, opponent)


# Fear uses the same canonical compiler, round pipeline and strict tapes.
def fear_round(foe, rolls, *, charging='first', choices=(), context=None, state=None):
    cub = canonical('ogre-hunting-party-web', 'sabretusks', 'weapon.fist')
    dice = StrictDice([{'key': key, 'value': face} for key, face in rolls])
    decisions = StrictDecisions([{'key': key, 'value': value} for key, value in choices])
    if state is None:
        state = initialize_duel(cub, foe, dice, context=context or DuelContext(
            charging=(charging,), active_participant=charging))
    result = resolve_round(cub, foe, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result


@pytest.mark.parametrize('ld,face,hit,target', [
    ((3, 4), 4, True, 4), ((6, 6), 5, False, 6), ((6, 6), 6, True, 6),
])
def test_fear_when_charged_changes_hits_only_for_that_round(ld, face, hit, target):
    foe = enemy()
    rolls = [('round.0.second.fear.charged.0', ld[0]),
             ('round.0.second.fear.charged.1', ld[1]),
             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
             ('round.0.second.attack.0.hit', face)]
    if hit:
        rolls.append(('round.0.second.attack.0.wound', 1))
    result = fear_round(foe, rolls)
    assert result.attacks[-1].hit is hit and result.attacks[-1].hit_target == target
    assert result.state.second.fear_hit_sixes is (target == 6)
    later = fear_round(foe, [('round.1.first.attack.0.hit', 1),
                             ('round.1.second.attack.0.hit', 4),
                             ('round.1.second.attack.0.wound', 1)], state=result.state)
    assert later.attacks[-1].hit_target == 4 and later.attacks[-1].hit
    assert not later.state.second.fear_hit_sixes


def test_failed_fear_charge_has_no_contact_attacks_or_invented_winner():
    foe = enemy()
    result = fear_round(foe, [('round.0.second.fear.charge.0', 6),
                             ('round.0.second.fear.charge.1', 6)], charging='second')
    assert not result.state.engaged and not result.attacks
    assert result.state.failed_charges == frozenset({'second'})
    assert result.state.initial_charge_flags == (False, False)
    assert result.state.first_player_turn  # One phase elapsed; the attempted turn was second's.
    assert result.state.initial_first_player_turn is False
    assert result.state.first.condition == result.state.second.condition == Condition.STANDING
    assert result.state.first.active and result.state.second.active
    later = fear_round(foe, [], state=result.state)
    assert later.state == result.state and not later.attacks


def test_successful_fear_charge_retains_its_real_priority_and_only_one_test():
    result = fear_round(enemy(), [('round.0.second.fear.charge.0', 3),
                                 ('round.0.second.fear.charge.1', 4),
                                 ('round.0.second.attack.0.hit', 1),
                                 ('round.0.first.attack.0.hit', 1)], charging='second')
    assert result.state.engaged and not result.state.failed_charges
    assert result.state.initial_charge_flags == (False, True)
    assert not result.state.first.fear_hit_sixes


@pytest.mark.parametrize('kind,foe_count', [('causes-fear', 2), ('automatic', 1), ('frenzy', 2)])
def test_source_fear_exemptions_and_automatic_personal_leadership_consume_no_test_dice(kind, foe_count):
    if kind == 'causes-fear':
        foe = canonical('halflings-mic', 'village-ogre', 'weapon.mace')
    elif kind == 'automatic':
        foe = canonical('cult-of-the-possessed', 'darksouls', 'weapon.mace')
        foe = replace(foe, characteristics=replace(foe.characteristics, leadership=None))
    else:
        foe = enemy(trait_overrides={'frenzy': True})
    rolls = [(f'round.0.{label}.attack.{i}.hit', 1)
             for label, count in (('first', 2), ('second', foe_count)) for i in range(count)]
    result = fear_round(foe, rolls)
    assert result.state.engaged and not result.state.second.fear_hit_sixes
    assert len(result.attacks) == 2 + foe_count


def test_fear_uses_live_frenzy_loss_and_shared_leader_threshold():
    cub = canonical('ogre-hunting-party-web', 'sabretusks', 'weapon.fist')
    foe = enemy(trait_overrides={'frenzy': True})
    setup = StrictDice([])
    state = initialize_duel(cub, foe, setup, context=DuelContext(charging=('first',), active_participant='first'))
    state = replace(state, second=replace(state.second, frenzy=False))
    failed = fear_round(foe, [('round.0.second.fear.charged.0', 6),
                             ('round.0.second.fear.charged.1', 6),
                             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
                             ('round.0.second.attack.0.hit', 5)], state=state)
    assert not failed.attacks[-1].hit and failed.state.second.fear_hit_sixes
    foe = canonical('cult-of-the-possessed', 'brethren', 'weapon.mace')
    leader = canonical('cult-of-the-possessed', 'magister', 'weapon.mace')
    context = DuelContext(nearby=(LocalParticipant('magister', 'second', leader),),
        distances=(('second', 'magister', 6),), charging=('first',), active_participant='first')
    passed = fear_round(foe, [('round.0.second.fear.charged.0', 4),
                             ('round.0.second.fear.charged.1', 4),
                             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
                             ('round.0.second.attack.0.hit', 1)], context=context,
        choices=(('round.0.second.fear.charged.leader.magister', True),))
    assert not passed.state.second.fear_hit_sixes


def test_fear_sixes_override_hit_modifiers_and_automatic_hit_but_allow_one_reroll():
    foe = enemy()
    # Synthetic effect discriminators, not a canonical character/loadout claim.
    foe = replace(foe, main_weapon=replace(foe.main_weapon,
        hit_modifier=99, automatic_hit=True, reroll_hits=True))
    result = fear_round(foe, [('round.0.second.fear.charged.0', 6),
                             ('round.0.second.fear.charged.1', 6),
                             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
                             ('round.0.second.attack.0.hit', 5),
                             ('round.0.second.attack.0.hit.reroll', 6),
                             ('round.0.second.attack.0.wound', 1)])
    assert result.attacks[-1].hit and result.attacks[-1].hit_target == 6
    assert result.attacks[-1].hit_roll == 6


def test_fear_reaches_shifty_and_collectively_prepared_hits_with_hatred_rerolls():
    foe = enemy(off_hand_id='weapon.axe', skill_ids=('skill.shifty', 'skill.hatred'))
    result = fear_round(foe, [('round.0.second.fear.charged.0', 6),
                             ('round.0.second.fear.charged.1', 6),
                             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
                             ('round.0.second.shifty.attack.0.hit', 5),
                             ('round.0.second.shifty.attack.0.hit.reroll', 6),
                             ('round.0.second.shifty.attack.0.wound', 1),
                             ('round.0.second.attack.0.hit', 5),
                             ('round.0.second.attack.0.hit.reroll', 5),
                             ('round.0.second.attack.1.hit', 1),
                             ('round.0.second.attack.1.hit.reroll', 6),
                             ('round.0.second.attack.1.wound', 1)],
        choices=(('round.0.second.shifty.main-weapon', True),))
    assert [attack.hit_target for attack in result.attacks[-3:]] == [6, 6, 6]
    assert [attack.hit for attack in result.attacks[-3:]] == [True, False, True]
    assert [attack.hit_roll for attack in result.attacks[-3:]] == [6, 5, 6]


def test_fear_requires_known_leadership_only_when_a_test_is_required():
    foe = enemy()
    foe = replace(foe, characteristics=replace(foe.characteristics, leadership=None))
    with pytest.raises(ValueError, match='explicit.*Leadership'):
        fear_round(foe, [])
    result = fear_round(foe, [('round.0.first.attack.0.hit', 1),
                             ('round.0.second.attack.0.hit', 1)], context=DuelContext(
        charging=(), active_participant='first'))
    assert result.state.engaged


@pytest.mark.parametrize('observed', [False, True])
def test_failed_fear_charge_stops_both_modular_drivers_as_unresolved(monkeypatch, observed):
    from mordheim_combat.modular import duel as driver
    cub = canonical('ogre-hunting-party-web', 'sabretusks', 'weapon.fist')
    foe = enemy()
    dice = StrictDice([{'key': 'round.0.second.fear.charge.0', 'value': 6},
                       {'key': 'round.0.second.fear.charge.1', 'value': 6}])
    monkeypatch.setattr(driver, 'SeededDice', lambda seed: dice)
    context = DuelContext(charging=('second',), active_participant='second')
    function = driver.simulate_duel_observed if observed else driver.simulate_duel_reference
    result = function(cub, foe, 1, maximum_rounds=10, decisions=StrictDecisions([]), context=context)
    dice.finish()
    aggregate = result.as_result() if observed else result
    assert aggregate.first_wins == aggregate.second_wins == 0 and aggregate.unresolved == 1
    if observed:
        assert result.resolution_rounds.tolist() == [1]
        assert result.first_condition.tolist() == result.second_condition.tolist() == [int(Condition.STANDING)]



def test_fear_does_not_turn_passive_spines_into_a_melee_hit_roll():
    foe = enemy(trait_overrides={'spines': True})
    result = fear_round(foe, [('round.0.second.fear.charged.0', 6),
                             ('round.0.second.fear.charged.1', 6),
                             ('round.0.second.spines.wound', 1),
                             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
                             ('round.0.second.attack.0.hit', 5)])
    assert result.attacks[0].hit  # Strict tape proves no physical hit die was requested.
    assert not result.attacks[-1].hit and result.attacks[-1].hit_target == 6


@pytest.mark.parametrize('source', ['fearsome', 'mutation', 'blessing', 'current-condition', 'canonical-condition'])
def test_acquired_fear_reaches_the_same_real_charge_test(source):
    if source == 'fearsome':
        owner = canonical('mercenaries', 'mercenary-captain', 'weapon.mace', skill_ids=('skill.fearsome',))
        catalogue = CombatCatalogue()
        captain = next(p for p in catalogue.profiles('mordheim', 'mercenaries') if p.profile_id == 'mercenary-captain')
        assert 'skill.fearsome' in catalogue.in_scope_skill_ids(catalogue.skills(captain))
    elif source == 'mutation':
        owner = canonical('cult-of-the-possessed', 'mutants', 'weapon.mace', special_rule_ids=('band--mutations-hideous',))
    elif source == 'blessing':
        owner = canonical('carnival-of-chaos', 'tainted-ones', 'weapon.mace', special_rule_ids=('band--blessings-of-nurgle-hideous',))
    elif source == 'canonical-condition':
        # The canonical id, resolved by construction and not a trait name.
        owner = enemy(condition_ids=('campaign.condition.causes-fear',))
        assert 'mechanic.causes-fear' not in enemy().global_effects.tags
    else:
        owner = enemy(trait_overrides={'causes_fear': True})  # Supplied acquired/current condition.
        assert 'mechanic.causes-fear' not in enemy().global_effects.tags
    assert owner.global_effects.tags.count('mechanic.causes-fear') == 1
    dice = StrictDice([{'key': 'round.0.second.fear.charge.0', 'value': 6},
                       {'key': 'round.0.second.fear.charge.1', 'value': 6}])
    foe = enemy()
    state = initialize_duel(owner, foe, dice, context=DuelContext(charging=('second',), active_participant='second'))
    result = resolve_round(owner, foe, state, dice, StrictDecisions([]))
    dice.finish()
    assert not result.state.engaged and not result.attacks
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(owner, foe)


def test_band_fear_uses_the_printed_recipient_exceptions():
    for band, profile, expected in (
        ('brood-of-ghurash-the-sc', 'firstborns', True),
        ('brood-of-ghurash-the-sc', 'children', False),
        ('maneaters', 'captain', True), ('maneaters', 'youngbloods', False),
        ('tomb-guardians', 'tomb-lord', True), ('tomb-guardians', 'tomb-scorpions', False),
        ('undead', 'vampire', True), ('undead', 'necromancer', False),
        ('beastmen-raiders', 'minotaur', True), ('skaven-clan-eshin', 'rat-ogre', True),
    ):
        assert ('mechanic.causes-fear' in canonical(band, profile, 'weapon.fist').global_effects.tags) is expected, (band, profile)
    with pytest.raises(ValueError, match='available|recipient|only'):
        canonical('cult-of-the-possessed', 'brethren', special_rule_ids=('band--mutations-hideous',))


@pytest.mark.parametrize('hand,animal', [('main', True), ('off', True), ('main', False)])
def test_beastlash_fear_is_wielded_and_animal_specific(hand, animal):
    from mordheim_combat.modular.psychology import causes_fear
    owner = enemy(weapon='weapon.beastlash' if hand == 'main' else 'weapon.mace',
                  off_hand_id='weapon.beastlash' if hand == 'off' else None)
    foe = canonical('halflings-mic', 'piggies', 'weapon.fist') if animal else enemy()
    assert causes_fear(owner, foe) is animal
    rolls = [('round.0.second.fear.charge.0', 6), ('round.0.second.fear.charge.1', 6)] if animal else []
    dice = StrictDice([{'key': key, 'value': face} for key, face in rolls])
    state = initialize_duel(owner, foe, dice, context=DuelContext(charging=('second',), active_participant='second'))
    # No attack tape is needed to prove that only an animal requires the test.
    from mordheim_combat.modular.psychology import resolve_fear
    state = resolve_fear(owner, foe, state, dice, StrictDecisions([]))
    dice.finish()
    assert state.engaged is not animal


def test_chainsaw_sword_grants_bearer_fear_and_only_its_own_armour_penalty():
    owner = canonical('masters-of-horror-sylv', 'mad-scientist', 'weapon.chainsaw-sword')
    assert 'mechanic.causes-fear' in owner.global_effects.tags
    assert owner.main_weapon.armour_penetration == 2 and owner.global_effects.armour_penetration == 0
    defender = enemy(armour='armour.heavy-armour', off_hand_id='defence.shield')
    outcome = strike(owner, defender, [('hit', 4), ('wound', 4), ('armour', 5)])
    assert outcome.wounded and not outcome.saved and outcome.defender.wounds == 1
    carried = canonical('masters-of-horror-sylv', 'mad-scientist', 'weapon.dagger',
                        owned_item_ids=('chainsaw_sword', 'dagger'))
    assert 'mechanic.causes-fear' in carried.global_effects.tags
    assert carried.main_weapon.armour_penetration == 0
    double = enemy(skill_ids=('skill.fearsome',), trait_overrides={'causes_fear': True})
    assert double.global_effects.tags.count('mechanic.causes-fear') == 1


@pytest.mark.parametrize('band,faces,passed', [
    ('lizardmen', (6, 3, 4), True),
    ('lizardmen-lus', (3, 6, 4), True),
    ('lizardmen-lus', (6, 4, 4), False),
])
def test_cold_blooded_psychology_uses_lowest_two_in_the_real_fear_charge(band, faces, passed):
    skink = canonical(band, 'skink-great-crests', 'weapon.axe')
    assert skink.characteristics.leadership == 7
    assert skink.global_effects.tags.count('mechanic.cold-blooded-psychology') == 1
    rolls = [(f'round.0.second.fear.charge.{i}', face) for i, face in enumerate(faces)]
    if passed:
        rolls += [('round.0.second.attack.0.hit', 1), ('round.0.first.attack.0.hit', 1)]
    result = fear_round(skink, rolls, charging='second')
    assert result.state.engaged is passed
    assert bool(result.attacks) is passed
    assert result.state.failed_charges == (frozenset() if passed else frozenset({'second'}))
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(skink, enemy())


@pytest.mark.parametrize('band,profile,faces,passed,attacks', [
    # The Young Noble also prints a Spiked Tail attack (Lords of the Marsh), so a
    # resolved round holds one attack more than the plain Skink's single attack.
    ('lords-of-the-marsh-mim', 'young-nobles', (6, 3, 3), True, 3),
    ('lizardmen-lus', 'skink-great-crests', (3, 5), False, 2),
])
def test_cold_blooded_variants_distinguish_crude_belch_from_psychology(band, profile, faces, passed, attacks):
    halfling = canonical('halflings-mic', 'halfling-elder', 'weapon.mace',
                        special_rule_ids=('halfling-elder--crude-belch',))
    tested = canonical(band, profile, 'weapon.axe')
    assert tested.characteristics.leadership == (6 if band == 'lords-of-the-marsh-mim' else 7)
    rolls = [(f'round.0.first.crude-belch.leadership.{i}', face) for i, face in enumerate(faces)]
    rolls += [('round.0.first.attack.0.hit', 1)]
    if passed:
        rolls += [(f'round.0.second.attack.{i}.hit', 1) for i in range(attacks - 1)]
    dice = StrictDice([{'key': key, 'value': face} for key, face in rolls])
    choices = StrictDecisions([{'key': 'round.0.first.crude-belch', 'value': True}])
    state = initialize_duel(halfling, tested, dice, context=DuelContext(
        charging=('first',), active_participant='first'))
    result = resolve_round(halfling, tested, state, dice, choices)
    dice.finish(); choices.finish()
    assert len(result.attacks) == attacks
    assert result.attacks[-1].hit_roll == (1 if passed else None)


def test_cold_blooded_preserves_explicit_leadership_and_automatic_pass_contracts():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    tested = canonical('lizardmen-lus', 'skink-great-crests', 'weapon.axe')
    foe = enemy()
    dice = StrictDice([])
    state = initialize_duel(tested, foe, dice, context=DuelContext(charging=(), active_participant='first'))
    unknown = replace(tested, characteristics=replace(tested.characteristics, leadership=None))
    with pytest.raises(ValueError, match='explicit.*Leadership'):
        resolve_local_leadership(unknown, state, dice, StrictDecisions([]), 'ld', first=True, psychology=True)
    # In-memory composition discriminator, not a canonical automatic-pass grant to Skinks.
    automatic = replace(unknown, global_effects=replace(unknown.global_effects,
        tags=(*unknown.global_effects.tags, 'mechanic.automatic-leadership')))
    assert resolve_local_leadership(automatic, state, dice, StrictDecisions([]), 'ld', first=True, psychology=True)
    dice.finish()


@pytest.mark.parametrize('profile', ['draich', 'young-nobles', 'shearls'])
def test_craven_can_fail_a_fear_charge_even_when_the_fimir_causes_fear(profile):
    # The Draich causes Fear innately; the other two receive an explicit current
    # acquired-Fear condition, proving the same exception without a fake KB grant.
    fighter = canonical('lords-of-the-marsh-mim', profile, 'weapon.axe',
        **({} if profile == 'draich' else {'trait_overrides': {'causes_fear': True}}))
    assert fighter.global_effects.tags.count('mechanic.craven') == 1
    assert 'mechanic.causes-fear' in fighter.global_effects.tags
    rolls = ([(f'round.0.second.stupidity.{i}', 1) for i in range(3)]
             if profile != 'draich' else [])
    rolls += [(f'round.0.second.fear.charge.{i}', 6) for i in range(3)]
    result = fear_round(fighter, rolls, charging='second')
    assert not result.state.engaged and not result.attacks
    assert result.state.failed_charges == frozenset({'second'})
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, enemy())


@pytest.mark.parametrize('faces,passed', [((6, 4, 4), True), ((6, 6, 6), False)])
def test_draich_craven_received_charge_preserves_cold_blooded_and_sixes_rule(faces, passed):
    draich = canonical('lords-of-the-marsh-mim', 'draich', 'weapon.axe')
    assert draich.characteristics.leadership == 8
    rolls = [(f'round.0.second.fear.charged.{i}', face) for i, face in enumerate(faces)]
    rolls += [('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
              ('round.0.second.attack.0.hit', 5)]
    if passed:
        rolls.append(('round.0.second.attack.0.wound', 1))
    result = fear_round(draich, rolls)
    assert result.state.engaged and not result.state.failed_charges
    assert result.state.second.fear_hit_sixes is not passed
    assert result.attacks[-1].hit is passed
    assert result.attacks[-1].hit_target == (3 if passed else 6)


@pytest.mark.parametrize('profile', ['daemon-fimm', 'young-nobles'])
def test_craven_preserves_ordinary_immunity_and_skips_tests_without_fear(profile):
    from mordheim_combat.modular.psychology import resolve_fear
    fighter = canonical('lords-of-the-marsh-mim', profile,
                        'weapon.fist' if profile == 'daemon-fimm' else 'weapon.axe')
    assert ('mechanic.craven' in fighter.global_effects.tags) is (profile == 'young-nobles')
    foe = (canonical('ogre-hunting-party-web', 'sabretusks', 'weapon.fist')
           if profile == 'daemon-fimm' else enemy())
    dice = StrictDice([])
    decisions = StrictDecisions([])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(
        charging=('first',), active_participant='first'))
    assert resolve_fear(fighter, foe, state, dice, decisions) == state
    dice.finish(); decisions.finish()


@pytest.mark.parametrize('profile', ['young-nobles', 'shearls', 'fimir-warriors'])
def test_stupidity_failure_cancels_only_the_initial_voluntary_charge(profile):
    fighter = canonical('lords-of-the-marsh-mim', profile, 'weapon.axe')
    foe = enemy()
    dice = StrictDice([{'key': f'round.0.first.stupidity.{i}', 'value': 6} for i in range(3)])
    decisions = StrictDecisions([])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(
        charging=('first',), active_participant='first'))
    result = resolve_round(fighter, foe, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert not result.state.engaged and not result.attacks
    assert result.state.first.stupidity_failed
    assert result.state.failed_charges == frozenset({'first'})
    assert fighter.global_effects.tags.count('mechanic.stupidity') == 1
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, foe)


def test_stupidity_persists_through_enemy_turn_then_pass_restores_attacks():
    fighter = canonical('lords-of-the-marsh-mim', 'young-nobles', 'weapon.axe')
    foe = enemy()
    rolls = [(f'round.0.first.stupidity.{i}', 6) for i in range(3)]
    # Hit normally against a stupid, standing model; no automatic hit or WS change.
    rolls += [('round.0.second.attack.0.hit', 5), ('round.0.second.attack.0.wound', 1),
              ('round.1.second.attack.0.hit', 1)]
    rolls += [(f'round.2.first.stupidity.{i}', face) for i, face in enumerate((6, 3, 3))]
    # The recovered Young Noble attacks with its weapon and its Spiked Tail.
    rolls += [('round.2.second.attack.0.hit', 1), ('round.2.first.attack.0.hit', 1),
              ('round.2.first.attack.1.hit', 1)]
    dice = StrictDice([{'key': key, 'value': face} for key, face in rolls])
    decisions = StrictDecisions([])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(
        charging=(), active_participant='first'))
    results = []
    for _ in range(3):
        result = resolve_round(fighter, foe, state, dice, decisions)
        results.append(result); state = result.state
    dice.finish(); decisions.finish()
    assert [len(r.attacks) for r in results] == [1, 1, 3]
    assert [r.state.first.stupidity_failed for r in results] == [True, True, False]
    assert results[0].attacks[0].hit_target == 4 and results[0].attacks[0].hit
    assert state.first.condition == Condition.STANDING


def test_stupidity_frenzy_exemption_uses_no_leadership_dice():
    from mordheim_combat.modular.psychology import resolve_stupidity
    fighter = canonical('lords-of-the-marsh-mim', 'young-nobles', 'weapon.axe')
    foe = enemy()
    dice = StrictDice([]); decisions = StrictDecisions([])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(
        charging=(), active_participant='first'))
    state = replace(state, first=replace(state.first, frenzy=True, stupidity_failed=True))
    result = resolve_stupidity(fighter, foe, state, dice, decisions)
    assert not result.first.stupidity_failed and result.first.frenzy
    dice.finish(); decisions.finish()


TROLL_STUPIDITY_RECIPIENTS = (
    ('black-orcs', 'troll', 'black-orc-boss'),
    ('night-goblins-kaz', 'troll', 'big-boss'),
    ('night-goblins-mic', 'troll', 'big-boss'),
    ('night-goblins-web', 'troll', 'boss'),
    ('orc-mob', 'troll', 'orc-boss'),
    ('underworld-alliance-mim', 'warpstone-troll', 'goblin-bully'),
)


def test_troll_stupidity_recipients_are_canonical_and_do_not_leak():
    for band, profile, control in TROLL_STUPIDITY_RECIPIENTS:
        fighter = canonical(band, profile, 'weapon.fist')
        assert fighter.global_effects.tags.count('mechanic.stupidity') == 1, band
        assert 'mechanic.stupidity' not in canonical(band, control, 'weapon.fist').global_effects.tags, band


@pytest.mark.parametrize('band,profile', [
    ('black-orcs', 'troll'), ('night-goblins-kaz', 'troll'),
    ('underworld-alliance-mim', 'warpstone-troll'),
])
def test_troll_stupidity_failure_suppresses_attacks_in_the_real_round(band, profile):
    fighter = canonical(band, profile, 'weapon.fist', **(
        {'special_rule_ids': ('warpstone-troll--vomit-attack',)}
        if profile == 'warpstone-troll' else {}))
    if profile == 'warpstone-troll':
        assert fighter.vomit_attack is not None
    foe = enemy()
    dice = StrictDice([{'key': key, 'value': face} for key, face in [
        ('round.0.first.stupidity.0', 6), ('round.0.first.stupidity.1', 6),
        ('round.0.second.attack.0.hit', 1),
    ]])
    # A failed Troll cannot choose Vomit as a way around attack suppression.
    decisions = StrictDecisions([])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(
        charging=(), active_participant='first'))
    result = resolve_round(fighter, foe, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert result.state.first.stupidity_failed and result.state.engaged
    assert len(result.attacks) == 1 and result.attacks[0].hit_roll == 1
    assert result.state.first.wounds == fighter.characteristics.wounds


STUPIDITY_COMPLETION_PROFILES = (
    ('skaven-clan-eshin', 'rat-ogre'), ('skaven-clan-pestilens', 'rat-ogre'),
    ('skaven-of-clan-mors-kaz', 'rat-ogre'), ('skaven-of-clan-moulder-web', 'rat-ogres'),
    ('skaven-of-clan-pristekk-sc', 'rat-ogres'), ('crooked-moon-kep', 'troll'),
    ('mazzalupo-web', 'black-sheep'), ('dark-elves', 'cold-one-beasthounds'),
    ('brood-of-ghurash-the-sc', 'firstborns'), ('forest-goblins', 'gigantic-spider'),
    ('forest-goblins-lus', 'gigantic-spider'), ('kislevites', 'trained-bear'),
)


def test_stupidity_completion_canonical_routes_and_brood_recipient_filter():
    for band, profile in STUPIDITY_COMPLETION_PROFILES:
        fighter = canonical(band, profile, 'weapon.fist')
        assert fighter.global_effects.tags.count('mechanic.stupidity') == 1, (band, profile)
    worm = canonical('brood-of-ghurash-the-sc', 'baneworms', 'weapon.fist')
    assert 'mechanic.stupidity' not in worm.global_effects.tags
    with pytest.raises(ValueError, match='Brood Mentality'):
        canonical('brood-of-ghurash-the-sc', 'baneworms', 'weapon.fist',
                  trait_overrides={'stupidity_leadership_bonus': 1})


def test_stupidity_completion_supplied_exemption_skips_unknown_leadership_and_clears_history():
    from mordheim_combat.modular.psychology import resolve_stupidity
    # Eligible helper presence is a supplied active exemption, not a simulated
    # Hero/Sheepherder/Bear Tamer. Species and distance eligibility remain the
    # source contract of that supplied fact; no group model is introduced.
    for band, profile in [('skaven-of-clan-moulder-web', 'rat-ogres'),
                          ('mazzalupo-web', 'black-sheep'), ('kislevites', 'trained-bear')]:
        fighter = canonical(band, profile, 'weapon.fist', trait_overrides={
            'stupidity_exempt': True, 'stupidity_initial_failed': True})
        fighter = replace(fighter, characteristics=replace(fighter.characteristics, leadership=None))
        dice = StrictDice([]); decisions = StrictDecisions([])
        state = initialize_duel(fighter, enemy(), dice, context=DuelContext(charging=(), active_participant='first'))
        assert not state.first.stupidity_failed
        assert not resolve_stupidity(fighter, enemy(), state, dice, decisions).first.stupidity_failed
        dice.finish(); decisions.finish()


@pytest.mark.parametrize('band,profile,leader', [
    ('dark-elves', 'cold-one-beasthounds', 'high-born'),
    ('kislevites', 'trained-bear', 'druzhina-captain'),
])
def test_stupidity_completion_handler_uses_own_value_and_never_borrows_leader(band, profile, leader):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    plain = canonical(band, profile, 'weapon.fist')
    helped = canonical(band, profile, 'weapon.fist', trait_overrides={'stupidity_leadership': 8})
    provider = canonical(band, leader, 'weapon.fist')
    # Synthetic provider capability makes an attempted ordinary Leader loan
    # observable; it does not assert that this pending canonical Leader is active.
    provider = replace(provider, global_effects=replace(provider.global_effects,
        tags=(*provider.global_effects.tags, 'mechanic.leader-six')))
    for tested, expected in [(plain, False), (helped, True)]:
        dice = StrictDice([{'key': 'ld.0', 'value': 4}, {'key': 'ld.1', 'value': 4}])
        decisions = StrictDecisions([])
        state = initialize_duel(tested, enemy(), dice, context=DuelContext(
            charging=(), active_participant='first',
            nearby=(LocalParticipant('leader', 'first', provider),), distances=(('first', 'leader', 6),)))
        assert resolve_local_leadership(tested, state, dice, decisions, 'ld', first=True, psychology=True) is expected
        dice.finish(); decisions.finish()


def test_stupidity_completion_brood_bonus_affects_only_stupidity_tests():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    fighter = canonical('brood-of-ghurash-the-sc', 'firstborns', 'weapon.fist',
                        trait_overrides={'stupidity_leadership_bonus': 2})
    assert fighter.characteristics.leadership == 4
    for is_stupidity, expected in [(True, True), (False, False)]:
        dice = StrictDice([{'key': 'ld.0', 'value': 3}, {'key': 'ld.1', 'value': 3}])
        decisions = StrictDecisions([])
        state = initialize_duel(fighter, enemy(), dice, context=DuelContext(charging=(), active_participant='first'))
        assert resolve_local_leadership(fighter, state, dice, decisions, 'ld', first=True,
                                       psychology=True, stupidity=is_stupidity) is expected
        dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='non-negative integer'):
        canonical('brood-of-ghurash-the-sc', 'firstborns', 'weapon.fist',
                  trait_overrides={'stupidity_leadership_bonus': True})


def test_stupidity_completion_acquired_prior_failure_lasts_until_next_own_turn():
    fighter = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 1, 1, leadership=7),
        main_weapon_id='weapon.mace', trait_overrides={'stupidity': True, 'stupidity_initial_failed': True}))
    foe = enemy()
    rolls = [('round.0.first.attack.0.hit', 1),
             ('round.1.second.stupidity.0', 1), ('round.1.second.stupidity.1', 1),
             ('round.1.first.attack.0.hit', 1), ('round.1.second.attack.0.hit', 1)]
    dice = StrictDice([{'key': key, 'value': face} for key, face in rolls]); decisions = StrictDecisions([])
    state = initialize_duel(foe, fighter, dice, context=DuelContext(charging=(), active_participant='first'))
    assert state.second.stupidity_failed
    first = resolve_round(foe, fighter, state, dice, decisions)
    assert len(first.attacks) == 1 and first.state.second.stupidity_failed
    second = resolve_round(foe, fighter, first.state, dice, decisions)
    assert len(second.attacks) == 2 and not second.state.second.stupidity_failed
    dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='active Stupidity'):
        enemy(trait_overrides={'stupidity_initial_failed': True})


def test_stupidity_completion_disability_head_injury_uses_the_same_turn_operator():
    from mordheim_combat.modular.psychology import resolve_stupidity
    fighter = enemy(skill_ids=('mechanic.disability',))
    dice = StrictDice([{'key': 'first.disability', 'value': 6},
                       {'key': 'round.0.first.stupidity.0', 'value': 6},
                       {'key': 'round.0.first.stupidity.1', 'value': 6}])
    decisions = StrictDecisions([])
    state = initialize_duel(fighter, enemy(), dice, context=DuelContext(charging=(), active_participant='first'))
    assert resolve_stupidity(fighter, enemy(), state, dice, decisions).first.stupidity_failed
    dice.finish(); decisions.finish()


@pytest.mark.parametrize('band,profile,control', [
    ('adventurers-kaz', 'barbarian', 'elf'),
    ('khorne-raiders-sar', 'cannibal-boys', 'plunderers'),
    ('skaven-of-clan-pestilens-mou', 'plague-priest', 'monk-initiate'),
    ('skaven-of-clan-pestilens-mou', 'plague-champion', 'monk-initiate'),
])
def test_remaining_innate_frenzy_grants_execute_and_are_lost_after_knockdown(band, profile, control):
    warrior = canonical(band, profile, 'weapon.flail' if band == 'adventurers-kaz' else 'weapon.dagger')
    assert warrior.global_effects.frenzy
    assert not canonical(band, control, 'weapon.fist').global_effects.frenzy
    base = warrior.characteristics.attacks
    assert build_attacks(AttackPoolContext(warrior)).attacks == base * 2
    assert build_attacks(AttackPoolContext(warrior, frenzy=False)).attacks == base
    foe = enemy()
    dice = StrictDice([{'key': f'round.0.{owner}.attack.{index}.hit', 'value': 1}
                       for owner, count in [('first', base * 2), ('second', 1)]
                       for index in range(count)])
    decisions = StrictDecisions([])
    state = initialize_duel(warrior, foe, dice,
                            context=DuelContext(charging=('first',), active_participant='first'))
    round_result = resolve_round(warrior, foe, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(round_result.attacks) == base * 2 + 1
    # Real injury resolution, rather than forcing the state bit in the fixture.
    result = strike(enemy(strength=6), warrior,
                    [('hit', 6), ('wound', 5), ('injury.0', 1)])
    assert result.defender.condition == Condition.KNOCKED_DOWN
    assert not result.defender.frenzy


@pytest.mark.parametrize('first_round', [True, False])
def test_unlimited_hatred_means_any_enemy_not_infinite_duration(first_round):
    rule = 'band--chaos-dwarfs-special-skills-unlimited-hatred'
    warrior = canonical('sons-of-hashut', 'chaos-dwarf-champions', 'weapon.mace',
                        special_rule_ids=(rule,))
    control = canonical('sons-of-hashut', 'chaos-dwarf-champions', 'weapon.mace')
    assert 'skill.hatred' in warrior.global_effects.tags
    assert 'skill.hatred' not in control.global_effects.tags
    foe = enemy()
    init = StrictDice([])
    a, d = initialize_fighter(warrior, init, 'a'), initialize_fighter(foe, init, 'd')
    init.finish()
    tape = [('x.hit', 1)] + ([('x.hit.reroll', 1)] if first_round else [])
    dice = StrictDice([{'key': key, 'value': value} for key, value in tape])
    result = resolve_reference_attack(warrior, foe, a, d, warrior.main_weapon,
                                     dice, key='x', first_round=first_round)
    dice.finish()
    assert not result.hit
    with pytest.raises(ValueError):
        canonical('sons-of-hashut', 'hobgoblins', 'weapon.mace', special_rule_ids=(rule,))


@pytest.mark.parametrize('band,profile,target', [
    ('adventurers-kaz', 'elf', 'dark'),
    ('dark-elves', 'corsairs', 'high'),
    ('druchii-mic', 'corsairs', 'high'),
    ('shadow-warriors', 'shadow-warrior', 'dark'),
    ('wood-elves-of-athel-loren-web', 'glade-guard', 'dark'),
    ('lothern-sea-patrol-sar', 'sea-rangers', 'dark'),
])
def test_elf_hatred_filters_individual_identity_and_first_combat_turn(band, profile, target):
    warrior = canonical(band, profile, 'weapon.dagger')
    wanted = canonical('dark-elves', 'corsairs', 'weapon.dagger') if target == 'dark' else canonical('high-elves-lus', 'seaguard', 'weapon.dagger')
    animal = canonical('dark-elves', 'cold-one-beasthounds', 'weapon.fist')
    wood_elf = canonical('wood-elves-of-athel-loren-web', 'glade-guard', 'weapon.dagger')
    for foe, first_round, rerolls in [(wanted, True, True), (wanted, False, False),
                                      (animal, True, False), (wood_elf, True, False)]:
        init = StrictDice([])
        a, d = initialize_fighter(warrior, init, 'a'), initialize_fighter(foe, init, 'd')
        init.finish()
        dice = StrictDice([{'key': 'x.hit', 'value': 1}] +
                          ([{'key': 'x.hit.reroll', 'value': 1}] if rerolls else []))
        result = resolve_reference_attack(warrior, foe, a, d, warrior.main_weapon,
                                         dice, key='x', first_round=first_round)
        dice.finish()
        assert not result.hit
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(warrior, wanted)


def test_elf_identity_and_hatred_do_not_spread_to_animals_or_mixed_recruits():
    for band, profile in [('dark-elves', 'cold-one-beasthounds'), ('druchii-mic', 'slavehounds'),
                          ('lothern-sea-patrol-sar', 'commodore')]:
        fighter = canonical(band, profile, 'weapon.fist')
        assert not any(tag.startswith('mechanic.hatred-') for tag in fighter.global_effects.tags)
    for band, profile in [('dark-elves', 'cold-one-beasthounds'), ('druchii-mic', 'slavehounds'),
                          ('lothern-sea-patrol-sar', 'raw-recruits')]:
        assert not any(tag in canonical(band, profile, 'weapon.fist').global_effects.tags
                       for tag in ('species.high-elf', 'species.dark-elf'))
    # The source explicitly allows both Elven and Human Raw Recruits.
    recruit = canonical('lothern-sea-patrol-sar', 'raw-recruits', 'weapon.fist', trait_overrides={'elf_kind': 'high'})
    assert 'species.high-elf' in recruit.global_effects.tags
    assert 'species.dark-elf' in canonical('druchii-mic', 'witch-elves', 'weapon.fist').global_effects.tags
    assert 'species.high-elf' in canonical('shadow-warriors', 'shadow-warrior', 'weapon.fist').global_effects.tags
    assert 'species.high-elf' not in canonical('high-elves-lus', 'seaguard', 'weapon.fist', trait_overrides={'elf_kind': 'other'}).global_effects.tags
    with pytest.raises(ValueError, match='elf_kind'):
        enemy(trait_overrides={'elf_kind': 'wood'})


@pytest.mark.parametrize('band,profile,mandatory', [
    ('bretonnian-chapel-guard', 'battle-pilgrims', True),
    ('dwarf-rangers', 'dwarf-longbeards', False),
])
def test_stubborn_rerolls_failed_individual_tests_once_with_source_correct_choice(band, profile, mandatory):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    fighter = canonical(band, profile, 'weapon.fist')
    prefix = 'round.0.second.fear.charged'
    rolls = [(prefix + '.0', 6), (prefix + '.1', 6),
             (prefix + '.reroll.0', 1), (prefix + '.reroll.1', 1),
             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
             ('round.0.second.attack.0.hit', 6), ('round.0.second.attack.0.wound', 1)]
    choices = () if mandatory else ((prefix + '.reroll', True),)
    result = fear_round(fighter, rolls, choices=choices)
    assert result.state.engaged and not result.state.second.fear_hit_sixes
    dice = StrictDice([{'key': f'ld.{i}', 'value': 1} for i in range(2)])
    decisions = StrictDecisions([])
    assert resolve_local_leadership(fighter, result.state, dice, decisions, 'ld', first=False)
    dice.finish(); decisions.finish()
    # A second failure is final, with no third roll or second decision.
    dice = StrictDice([{'key': f'ld{suffix}.{i}', 'value': 6}
                       for suffix in ('', '.reroll') for i in range(2)])
    decisions = StrictDecisions([] if mandatory else [{'key': 'ld.reroll', 'value': True}])
    assert not resolve_local_leadership(fighter, result.state, dice, decisions, 'ld', first=False)
    dice.finish(); decisions.finish()
    if not mandatory:
        dice = StrictDice([{'key': f'ld.{i}', 'value': 6} for i in range(2)])
        decisions = StrictDecisions([{'key': 'ld.reroll', 'value': False}])
        assert not resolve_local_leadership(fighter, result.state, dice, decisions, 'ld', first=False)
        dice.finish(); decisions.finish()
        # The full Cold-Blooded test is repeated, not only one face.
        fighter = replace(fighter, global_effects=replace(fighter.global_effects,
                          tags=(*fighter.global_effects.tags, 'mechanic.cold-blooded-leadership')))
        tape = [('ld.0', 6), ('ld.1', 6), ('ld.2', 6),
                ('ld.reroll.0', 6), ('ld.reroll.1', 4), ('ld.reroll.2', 4)]
        dice = StrictDice([{'key': key, 'value': face} for key, face in tape])
        decisions = StrictDecisions([{'key': 'ld.reroll', 'value': True}])
        assert resolve_local_leadership(fighter, result.state, dice, decisions, 'ld', first=False)
        dice.finish(); decisions.finish()


@pytest.mark.parametrize('band', ['norse-explorers-btb', 'norse-explorers-lustria'])
def test_barbarian_courage_rerolls_fear_without_rerolling_stupidity(band):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    rule = 'band--norse-special-skills-barbarian-courage'
    fighter = canonical(band, 'jarl', 'weapon.axe', special_rule_ids=(rule,),
                        trait_overrides={'stupidity': True})
    prefix = 'round.0.second.fear.charged'
    rolls = [(prefix + '.0', 6), (prefix + '.1', 6),
             (prefix + '.reroll.0', 1), (prefix + '.reroll.1', 1),
             ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
             ('round.0.second.attack.0.hit', 6), ('round.0.second.attack.1.hit', 6),
             ('round.0.second.attack.0.wound', 1), ('round.0.second.attack.1.wound', 1)]
    result = fear_round(fighter, rolls, choices=((prefix + '.reroll', True),))
    assert not result.state.second.fear_hit_sixes
    dice = StrictDice([{'key': f'ld.{i}', 'value': 6} for i in range(2)])
    decisions = StrictDecisions([])
    assert not resolve_local_leadership(fighter, result.state, dice, decisions,
                                       'ld', first=False, psychology=True, stupidity=True)
    dice.finish(); decisions.finish()
    assert 'mechanic.fear-reroll' not in canonical(band, 'jarl', 'weapon.fist').global_effects.tags
    with pytest.raises(ValueError):
        canonical(band, 'marauders', 'weapon.fist', special_rule_ids=(rule,))


@pytest.mark.parametrize('band,profile,rule', [
    ('beastmen-raiders', 'beastmen-chieftain', 'band--beastmen-special-skills-fearless'),
    ('vampire-hunters-of-sylvania-lotd5', 'vampire-hunter', 'band--special-skill-iron-will'),
])
def test_fear_immunity_skips_the_test_without_general_leadership_immunity(band, profile, rule):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    fighter = canonical(band, profile, 'weapon.fist', special_rule_ids=(rule,))
    fighter = replace(fighter, characteristics=replace(fighter.characteristics, leadership=None))
    rolls = [('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
             ('round.0.second.attack.0.hit', 6), ('round.0.second.attack.0.wound', 1)]
    result = fear_round(fighter, rolls)
    assert not result.state.second.fear_hit_sixes
    assert 'mechanic.fear-immunity' not in canonical(band, profile, 'weapon.fist').global_effects.tags
    with pytest.raises(ValueError, match='Leadership'):
        resolve_local_leadership(fighter, result.state, StrictDice([]), StrictDecisions([]),
                                 'ld', first=False, psychology=True, stupidity=True)
    if band.startswith('vampire-hunters'):
        with pytest.raises(ValueError):
            canonical(band, 'priest-of-morr', 'weapon.fist', special_rule_ids=(rule,))
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, enemy())


@pytest.mark.parametrize('band,profile', [
    ('carnival-of-chaos', 'plague-bearers'),
    ('carnival-of-chaos', 'nurglings'),
    ('carnival-of-chaos', 'plague-cart'),
    ('khorne-raiders-sar', 'madbrains'),
])
def test_explicit_automatic_leadership_passes_without_dice_or_borrowed_leader(band, profile):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_combat.modular.psychology import resolve_stupidity
    fighter = canonical(band, profile, 'weapon.fist', trait_overrides={'stupidity': True})
    assert 'mechanic.automatic-leadership' in fighter.global_effects.tags
    fighter = replace(fighter, characteristics=replace(fighter.characteristics, leadership=None))
    dice, decisions = StrictDice([]), StrictDecisions([])
    state = initialize_duel(fighter, enemy(), dice, context=DuelContext(charging=('first',), active_participant='first'))
    for kwargs in ({}, {'psychology': True, 'fear': True},
                   {'psychology': True, 'stupidity': True}):
        assert resolve_local_leadership(fighter, state, dice, decisions, 'ld', first=True, **kwargs)
    assert not resolve_stupidity(fighter, enemy(), state, dice, decisions).first.stupidity_failed
    dice.finish(); decisions.finish()
    control = canonical(band, 'carnival-master' if band == 'carnival-of-chaos' else 'dread-captain', 'weapon.fist')
    assert 'mechanic.automatic-leadership' not in control.global_effects.tags
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, enemy())


@pytest.mark.parametrize('band,profile', [('undead', 'vampire'), ('fen-guard-mim', 'branchwych')])
def test_psychology_immunity_cancels_individual_tests_and_benefits_only(band, profile):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_combat.modular.psychology import resolve_fear, resolve_stupidity
    fighter = canonical(band, profile, 'weapon.fist',
                        trait_overrides={'frenzy': True, 'stupidity': True, 'stupidity_initial_failed': True})
    fighter = replace(fighter, characteristics=replace(fighter.characteristics, leadership=None),
                      global_effects=replace(fighter.global_effects,
                          tags=(*fighter.global_effects.tags, 'skill.hatred', 'mechanic.hatred-dark-elves')))
    foe = canonical('dark-elves', 'corsairs', 'weapon.dagger')
    foe = replace(foe, global_effects=replace(foe.global_effects,
                                           tags=(*foe.global_effects.tags, 'mechanic.causes-fear')))
    dice, decisions = StrictDice([]), StrictDecisions([])
    state = initialize_duel(fighter, foe, dice,
                           context=DuelContext(charging=('second',), active_participant='second'))
    assert not state.first.frenzy and not state.first.stupidity_failed
    assert not resolve_stupidity(fighter, foe, replace(state, initial_first_player_turn=True), dice, decisions).first.stupidity_failed
    assert not resolve_fear(fighter, foe, state, dice, decisions).first.fear_hit_sixes
    assert resolve_local_leadership(fighter, state, dice, decisions, 'psy', first=True, psychology=True)
    with pytest.raises(ValueError, match='Leadership'):
        resolve_local_leadership(fighter, state, dice, decisions, 'other', first=True)
    # Hatred is suppressed, but an independent weapon reroll still works.
    strike(fighter, enemy(), [('hit', 1)])
    weapon = replace(fighter.main_weapon, reroll_hits=True)
    a, d = initialize_fighter(fighter, dice, 'a'), initialize_fighter(foe, dice, 'd')
    tape = StrictDice([{'key': 'x.hit', 'value': 1}, {'key': 'x.hit.reroll', 'value': 1}])
    resolve_reference_attack(fighter, foe, a, d, weapon, tape, key='x')
    tape.finish(); dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, foe)


def test_tomb_guardians_psychology_immunity_excludes_the_living_scorpion():
    for profile in ('tomb-lord', 'liche-priest', 'acolytes', 'skeleton-warriors', 'tomb-guardians'):
        assert 'mechanic.psychology-immunity' in canonical('tomb-guardians', profile, 'weapon.fist').global_effects.tags
    assert 'mechanic.psychology-immunity' not in canonical('tomb-guardians', 'tomb-scorpions', 'weapon.fist').global_effects.tags


@pytest.mark.parametrize('first_round,immune,reroll', [(True, False, True), (False, False, False), (True, True, False)])
def test_pilgrims_innate_hatred_retains_first_round_and_immunity_limits(first_round, immune, reroll):
    pilgrim = canonical('order-of-the-mare-web', 'pilgrims', 'weapon.mace')
    assert 'skill.hatred' in pilgrim.global_effects.tags
    assert 'skill.hatred' not in canonical('order-of-the-mare-web', 'paragon', 'weapon.mace').global_effects.tags
    if immune:
        pilgrim = replace(pilgrim, global_effects=replace(pilgrim.global_effects,
                           tags=(*pilgrim.global_effects.tags, 'mechanic.psychology-immunity')))
    foe = enemy()
    init = StrictDice([])
    a, d = initialize_fighter(pilgrim, init, 'a'), initialize_fighter(foe, init, 'd')
    init.finish()
    tape = StrictDice([{'key': 'x.hit', 'value': 1}] +
                      ([{'key': 'x.hit.reroll', 'value': 1}] if reroll else []))
    result = resolve_reference_attack(pilgrim, foe, a, d, pilgrim.main_weapon,
                                     tape, key='x', first_round=first_round)
    tape.finish()
    assert not result.hit


def test_spawn_explicit_automatic_leadership_preserves_its_separate_preparation():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    spawn = canonical('marauders-of-chaos', 'spawn-of-chaos', 'weapon.fist')
    assert 'mechanic.automatic-leadership' in spawn.global_effects.tags
    assert 'mechanic.automatic-leadership' not in canonical('marauders-of-chaos', 'marauder-chieftain', 'weapon.fist').global_effects.tags
    spawn = replace(spawn, characteristics=replace(spawn.characteristics, leadership=None))
    dice = StrictDice([{'key': 'first.characteristic.A.0', 'value': 3}])
    decisions = StrictDecisions([])
    state = initialize_duel(spawn, enemy(), dice,
                           context=DuelContext(charging=(), active_participant='first'))
    assert state.first.attacks == 4
    assert resolve_local_leadership(spawn, state, dice, decisions, 'ld', first=True)
    assert resolve_local_leadership(spawn, state, dice, decisions, 'fear', first=True, psychology=True, fear=True)
    dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(spawn, enemy())



def test_remaining_no_pain_grants_share_the_injury_operator_without_activating_bloated():
    recipients = [('ghost-pirates-sar', 'skeleton-mates'), ('ghost-pirates-sar', 'gibbets'),
                  ('necrarchs-mou', 'nosferatu'), ('necrarchs-mou', 'abomination'),
                  ('necrarchs-mou', 'defiled'), ('necrarchs-mou', 'skeleton'),
                  ('metal-mongers-mim', 'machine-ogre')]
    for band, profile in recipients:
        assert 'skill.ignore-pain' in canonical(band, profile, 'weapon.fist').global_effects.tags
    assert 'skill.ignore-pain' not in canonical('ghost-pirates-sar', 'the-bloated', 'weapon.fist').global_effects.tags
    skeleton = canonical('necrarchs-mou', 'skeleton', 'weapon.fist')
    assert strike(enemy(), skeleton, [('hit', 4), ('wound', 4), ('injury.0', 4)]).defender.condition == Condition.KNOCKED_DOWN
    assert strike(enemy(), skeleton, [('hit', 4), ('wound', 4), ('injury.0', 6)]).defender.condition == Condition.OUT


@pytest.mark.parametrize('band,profile', [('black-dwarfs', 'sorcerer'),
                                        ('guild-of-disgraced-engineers-mim', 'expelled-engineer')])
def test_remaining_hard_head_grants_ignore_concussion_without_ignoring_normal_stun(band, profile):
    dwarf = canonical(band, profile, 'weapon.fist')
    assert 'concussion_immune' in dwarf.global_effects.tags
    dwarf = replace(dwarf, characteristics=replace(dwarf.characteristics, wounds=1))
    attacker = enemy(strength=6)
    assert strike(attacker, dwarf, [('hit', 4), ('wound', 5), ('injury.0', 2)]).defender.condition == Condition.KNOCKED_DOWN
    assert strike(attacker, dwarf, [('hit', 4), ('wound', 5), ('injury.0', 4)]).defender.condition == Condition.STUNNED
    if band == 'black-dwarfs':
        informer = canonical(band, 'informers', 'weapon.fist')
        assert 'concussion_immune' not in informer.global_effects.tags
        assert strike(attacker, informer, [('hit', 4), ('wound', 5), ('injury.0', 2)]).defender.condition == Condition.STUNNED


def test_slayer_pirates_compound_injury_rules_exclude_thaggi():
    captain = canonical('slayer-pirates-sar', 'slayer-captain', 'weapon.fist')
    captain = replace(captain, characteristics=replace(captain.characteristics, wounds=1))
    assert 'skill.hard-to-kill' in captain.global_effects.tags
    assert 'concussion_immune' in captain.global_effects.tags
    for face, condition in [(2, Condition.KNOCKED_DOWN), (5, Condition.STUNNED), (6, Condition.OUT)]:
        assert strike(enemy(strength=6), captain, [('hit', 4), ('wound', 5), ('injury.0', face)]).defender.condition == condition
    for profile in ('master-gunner', 'mates', 'sea-trollslayers', 'gunners', 'landlubbers'):
        effects = canonical('slayer-pirates-sar', profile, 'weapon.fist').global_effects
        assert 'skill.hard-to-kill' in effects.tags and 'concussion_immune' in effects.tags
    thaggi = canonical('slayer-pirates-sar', 'thaggi', 'weapon.fist')
    assert 'skill.hard-to-kill' not in thaggi.global_effects.tags
    assert 'concussion_immune' not in thaggi.global_effects.tags



def test_bloated_squishy_overrides_no_pain_per_q037_ruling():
    bloated = canonical('ghost-pirates-sar', 'the-bloated', 'weapon.fist')
    assert 'rule.squishy' in bloated.global_effects.tags
    # The explicit exception also defeats an inherited No Pain contribution.
    bloated = replace(bloated, characteristics=replace(bloated.characteristics, wounds=1),
                      global_effects=replace(bloated.global_effects,
                          tags=(*bloated.global_effects.tags, 'skill.ignore-pain')))
    result = strike(enemy(strength=6), bloated, [('hit', 4), ('wound', 5), ('injury.0', 4)])
    assert result.defender.condition == Condition.STUNNED
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(bloated, enemy())


def test_cloak_uses_the_armour_role_and_normal_shield_helmet_composition():
    cloak = 'defence.sea-dragon-cloak'
    assert enemy(defence_ids=(cloak,)).armour_save == 5
    assert enemy(defence_ids=(cloak,), off_hand_id='defence.shield').armour_save == 4
    assert enemy(defence_ids=(cloak, 'defence.helmet'), off_hand_id='defence.shield').armour_save == 4
    with pytest.raises(ValueError, match='armour choice'):
        enemy(armour='armour.light-armour', defence_ids=(cloak,))
    with pytest.raises(ValueError, match='armour|not available'):
        canonical('dwarf-slayer-cult-web', 'giant-slayer', 'weapon.axe', defence_ids=(cloak,))


def test_revenant_is_selected_requires_thirster_and_recovers_at_own_turn_start_despite_fire():
    from mordheim_combat.modular.aftermath import _revenant_recovery
    thirst = 'strigoi-vampire--great-thirster'
    curse = 'strigoi-vampire--curse-of-the-revenant'
    base = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist')
    assert 'mechanic.curse-of-the-revenant' not in base.global_effects.tags
    with pytest.raises(ValueError, match='requires Great Thirster'):
        canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist', special_rule_ids=(curse,))
    vampire = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist', special_rule_ids=(thirst, curse))
    assert vampire.global_effects.regeneration_save == 7
    dice, decisions = StrictDice([{'key': 'round.0.first.revenant', 'value': 5}]), StrictDecisions([])
    state = initialize_duel(vampire, enemy(), dice,
                           context=DuelContext(charging=(), active_participant='first'))
    state = replace(state, first=replace(state.first, wounds=1, on_fire=True), engaged=False)
    result = resolve_round(vampire, enemy(), state, dice, decisions)
    assert result.state.first.wounds == 2 and result.state.first.on_fire
    dice.finish(); decisions.finish()
    # Re-entering the same turn cannot produce another attempt, even if damaged again.
    current = replace(result.state.first, wounds=1)
    quiet = StrictDice([])
    assert _revenant_recovery(vampire, current, quiet, 'round.0.first.revenant').wounds == 1
    enemy_turn = replace(state, round_index=1)
    assert resolve_round(vampire, enemy(), enemy_turn, quiet, StrictDecisions([])).state.first.wounds == 1
    assert _revenant_recovery(vampire, replace(current, condition=Condition.OUT), quiet, 'next').condition == Condition.OUT
    quiet.finish()
    failed = StrictDice([{'key': 'next', 'value': 4}])
    assert _revenant_recovery(vampire, current, failed, 'next').wounds == 1
    failed.finish()


def test_great_thirster_prerequisite_has_its_own_out_of_action_frenzy_effect():
    from mordheim_combat.modular.aftermath import _react_to_wound
    vampire = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist',
                        special_rule_ids=('strigoi-vampire--great-thirster',))
    foe = enemy()
    foe = replace(foe, characteristics=replace(foe.characteristics, wounds=1))
    outcome = strike(vampire, foe, [('hit', 4), ('wound', 4), ('injury.0', 6)])
    dice = StrictDice([])
    reacted = _react_to_wound(vampire, foe, outcome, dice, 'kill')
    dice.finish()
    assert reacted.defender.condition == Condition.OUT and reacted.attacker.frenzy
    attacker = enemy(strength=6)
    injury_dice = StrictDice([{'key': 'retaliation.' + key, 'value': face}
        for key, face in [('hit', 4), ('wound', 4), ('injury.0', 4)]])
    disabled = resolve_reference_attack(attacker, vampire, initialize_fighter(attacker, StrictDice([]), 'a'),
        replace(reacted.attacker, wounds=1), attacker.main_weapon, injury_dice, key='retaliation')
    injury_dice.finish()
    assert disabled.defender.condition != Condition.STANDING and not disabled.defender.frenzy


@pytest.mark.parametrize('owner', ['first', 'second'])
def test_rousing_sermon_is_priest_only_once_and_expires_after_own_turn(owner):
    skill = 'band--special-skill-rousing-sermon'
    priest = canonical('protectorate-of-sigmar-lotd3', 'warrior-priest', 'weapon.mace', special_rule_ids=(skill,))
    with pytest.raises(ValueError, match='not available'):
        canonical('protectorate-of-sigmar-lotd3', 'templar', 'weapon.fist', special_rule_ids=(skill,))
    foe = enemy()
    foe = replace(foe, characteristics=replace(foe.characteristics, initiative=1))
    first, second = (priest, foe) if owner == 'first' else (foe, priest)
    other = 'second' if owner == 'first' else 'first'
    context = DuelContext(charging=(owner,), active_participant=owner)
    state = initialize_duel(first, second, StrictDice([]), context=context)
    for index, priest_count in [(0, 2), (1, 1), (2, 1)]:
        dice = StrictDice([{'key': f'round.{index}.{label}.attack.{attack}.hit', 'value': 1}
            for label, count in [(owner, priest_count), (other, 1)] for attack in range(count)])
        decisions = StrictDecisions([{'key': f'round.0.{owner}.rousing-sermon', 'value': True}] if index == 0 else [])
        result = resolve_round(first, second, replace(state, round_index=index), dice, decisions)
        assert len(result.attacks) == priest_count + 1
        state = result.state
        dice.finish(); decisions.finish()
    assert 'rousing-sermon' in getattr(state, owner).resources_spent


def test_frantic_ignores_weapon_penalties_low_initiative_and_standing_up():
    fanatic = canonical('crooked-moon-kep', 'fanatics', 'weapon.fist')
    assert 'mechanic.frantic' in fanatic.global_effects.tags
    # Isolate the printed operator from the profile's restricted weapon list.
    slow = replace(fanatic, main_weapon=replace(fanatic.main_weapon, priority=-1),
                   characteristics=replace(fanatic.characteristics, initiative=1))
    foe = enemy()
    foe = replace(foe, characteristics=replace(foe.characteristics, initiative=10))
    for first_round, stood_up in [(True, False), (False, True)]:
        result = phases.resolve_priority(phases.PriorityContext(
            slow, foe, first_round=first_round, charging=False, charged=False, stood_up=stood_up))
        assert result.priority == 30
    dice = StrictDice([{'key': f'round.0.{label}.attack.0.hit', 'value': 1}
                       for label in ('first', 'second')])
    decisions = StrictDecisions([])
    state = initialize_duel(slow, foe, dice, context=DuelContext(charging=('second',), active_participant='second'))
    assert len(resolve_round(slow, foe, state, dice, decisions).attacks) == 2
    dice.finish(); decisions.finish()
    assert 'mechanic.frantic' not in canonical('crooked-moon-kep', 'big-boss', 'weapon.fist').global_effects.tags
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fanatic, foe)


@pytest.mark.parametrize('band,profile,skill', [
    ('sisters-of-sigmar', 'sigmarite-matriarch', 'band--special-skills-absolute-faith'),
    ('bretonnian-chapel-guard', 'questing-knight', 'band--questing-vow'),
])
def test_faith_and_questing_vow_reroll_failed_charge_fear_once(band, profile, skill):
    fighter = canonical(band, profile, 'weapon.fist', special_rule_ids=(skill,))
    foe = enemy(trait_overrides={'causes_fear': True})
    key = 'round.0.first.fear.charge'
    rolls = [(f'{key}.{i}', 6) for i in range(2)]
    rolls += [(f'{key}.reroll.{i}', 1) for i in range(2)]
    rolls += [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)]
    dice = StrictDice([{'key': key, 'value': face} for key, face in rolls])
    decisions = StrictDecisions([{'key': f'{key}.reroll', 'value': True}])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(fighter, foe, state, dice, decisions)
    assert result.state.engaged and len(result.attacks) == 2
    dice.finish(); decisions.finish()


def test_questing_vow_is_acquired_knight_only_and_qualifies_non_fear_leadership():
    from mordheim_combat.modular.rounds import apply_opponent_leadership
    from mordheim_combat.modular.leadership import resolve_local_leadership
    skill = 'band--questing-vow'
    base = canonical('bretonnian-chapel-guard', 'questing-knight', 'weapon.fist')
    assert 'mechanic.questing-vow' not in base.global_effects.tags
    with pytest.raises(ValueError, match='not available'):
        canonical('bretonnian-chapel-guard', 'damsel', 'weapon.fist', special_rule_ids=(skill,))
    knight = canonical('bretonnian-chapel-guard', 'questing-knight', 'weapon.fist', special_rule_ids=(skill,))
    foe = enemy(trait_overrides={'causes_fear': True})
    state = initialize_duel(knight, foe, StrictDice([]), context=DuelContext(charging=(), active_participant='first'))
    qualified = apply_opponent_leadership(knight, foe, state)
    dice = StrictDice([{'key': key, 'value': face} for key, face in
        [('ld.0', 6), ('ld.1', 6), ('ld.reroll.0', 6), ('ld.reroll.1', 6)]])
    decisions = StrictDecisions([{'key': 'ld.reroll', 'value': True}])
    assert not resolve_local_leadership(qualified, state, dice, decisions, 'ld', first=True)
    dice.finish(); decisions.finish()  # No third roll after the failed repeat.
    assert apply_opponent_leadership(knight, enemy(), state) is knight
    assert apply_opponent_leadership(knight, foe, replace(state, engaged=False, first_charged=False, second_charged=False)) is knight


@pytest.mark.parametrize('strength,wound_face,saved', [(3, 4, True), (4, 3, False)])
def test_gibbet_iron_cage_is_inseparable_normal_five_plus_armour(strength, wound_face, saved):
    gibbet = canonical('ghost-pirates-sar', 'gibbets', 'weapon.mace')
    assert gibbet.armour_save == 5 and gibbet.natural_armour_save == 7
    gibbet = replace(gibbet, characteristics=replace(gibbet.characteristics, wounds=2))
    result = strike(enemy(strength=strength), gibbet, [('hit', 4), ('wound', wound_face), ('armour', 5)])
    assert result.saved is saved
    assert result.defender.wounds == (2 if saved else 1)
    assert canonical('ghost-pirates-sar', 'the-cursed', 'weapon.mace').armour_save == 7
    with pytest.raises(ValueError, match='forbidden|not available'):
        canonical('ghost-pirates-sar', 'gibbets', 'weapon.mace', armour_id='armour.light-armour')


def test_frustratingly_tiny_is_acquired_snotling_defence_not_an_innate_goblin_skill():
    skill = 'bullied-goblin--frustratingly-tiny'
    base = canonical('snotlings-web', 'bigsnotz', 'weapon.sword')
    tiny = canonical('snotlings-web', 'bigsnotz', 'weapon.sword', special_rule_ids=(skill,))
    assert base.global_effects.incoming_hit_modifier == 0
    assert tiny.global_effects.incoming_hit_modifier == -1
    # This attacker hits the lower-WS Snotling on 3; Tiny moves that boundary to 4.
    attacker = enemy()
    control = strike(attacker, base, [('hit', 3), ('parry', 1), ('wound', 1)])
    affected = strike(attacker, tiny, [('hit', 3)])
    assert control.hit and not affected.hit and affected.hit_target == 4
    with pytest.raises(ValueError, match='not available'):
        canonical('snotlings-web', 'bullied-goblin', 'weapon.sword', special_rule_ids=(skill,))


@pytest.mark.parametrize('band,profile,rule', [
    ('sisters-of-sigmar', 'sigmarite-matriarch', 'band--special-skills-sign-of-sigmar'),
    ('vampire-hunters-of-sylvania-lotd5', 'vampire-hunter', 'band--special-skill-righteous-aura'),
])
def test_canonical_sigmar_and_righteous_aura_restrict_only_first_round_targets(band, profile, rule):
    from mordheim_combat.modular.rounds import apply_opponent_attack_modifiers
    warded = canonical(band, profile, "weapon.mace", special_rule_ids=(rule,))
    for target in [canonical('undead', 'vampire'),
                   canonical('cult-of-the-possessed', 'the-possessed', 'weapon.fist')]:
        assert 'undead_or_possessed' in target.global_effects.tags
        assert apply_opponent_attack_modifiers(target, warded, 3, first_round=True) == 2
        assert apply_opponent_attack_modifiers(target, warded, 1, first_round=True) == 1
        assert apply_opponent_attack_modifiers(target, warded, 3, first_round=False) == 3
    # Real two-round duel: A2 vampire loses exactly one attack, then recovers it.
    vampire = canonical('undead', 'vampire')
    dice = StrictDice([{'key': key, 'value': 1} for key in (
        'round.0.first.attack.0.hit', 'round.0.second.attack.0.hit',
        'round.1.first.attack.0.hit', 'round.1.first.attack.1.hit',
        'round.1.second.attack.0.hit')])
    decisions = StrictDecisions([])
    state = initialize_duel(vampire, warded, dice,
        context=DuelContext(charging=(), active_participant='first'))
    for expected in (2, 3):
        result = resolve_round(vampire, warded, state, dice, decisions)
        assert len(result.attacks) == expected
        state = result.state
    dice.finish(); decisions.finish()
    human = canonical('undead', 'necromancer')
    assert apply_opponent_attack_modifiers(human, warded, 3, first_round=True) == 3
    assert apply_opponent_attack_modifiers(human, canonical(band, profile, "weapon.mace"), 3, first_round=True) == 3


@pytest.mark.parametrize('condition', [Condition.KNOCKED_DOWN, Condition.STUNNED])
def test_honorable_refuses_incapacitated_opponent_without_dice(condition):
    from mordheim_combat.modular.pools import _resolve_attack_pool
    noble, foe = canonical('adventurers-kaz', 'imperial-noble'), enemy()
    dice = StrictDice([]); decisions = StrictDecisions([])
    a, d = initialize_fighter(noble, dice, 'a'), initialize_fighter(foe, dice, 'd')
    d = replace(d, condition=condition)
    _, after, results = _resolve_attack_pool(noble, foe, a, d, 2, dice,
        key='forbidden', first_round=True, charging=True, decisions=decisions)
    assert results == () and after == d
    result = resolve_reference_attack(noble, foe, a, d, noble.main_weapon, dice, key='direct')
    assert not result.hit and not result.wounded and result.defender == d
    dice.finish(); decisions.finish()
    # No prohibition against an able opponent.
    assert not strike(noble, foe, [('hit', 1)]).hit



def test_exact_creature_facts_distinguish_undead_possessed_daemons_and_normal_animals():
    facts = [('undead', 'vampire', 'weapon.sword', 'nature.undead'),
             ('cult-of-the-possessed', 'the-possessed', 'weapon.fist', 'nature.possessed'),
             ('carnival-of-chaos', 'plague-bearers', 'weapon.fist', 'nature.daemon'),
             ('necrarchs-mou', 'abomination', 'weapon.fist', 'nature.living')]
    for band, profile, weapon, tag in facts:
        assert tag in canonical(band, profile, weapon).global_effects.tags
    friend = canonical('ostlanders', 'elder', 'weapon.mace',
        special_rule_ids=('band--ostlander-special-skills-animal-friendship',))
    from mordheim_combat.modular.rounds import apply_opponent_attack_modifiers
    dog = canonical('witch-hunters', 'war-hounds', 'weapon.fist')
    monster = canonical('lizardmen', 'kroxigor', 'weapon.fist')
    assert apply_opponent_attack_modifiers(dog, friend, 2, first_round=False) == 0
    assert apply_opponent_attack_modifiers(monster, friend, 2, first_round=False) == 2


def test_undead_hatred_charge_and_morr_injury_reuse_real_operators():
    from mordheim_combat.modular.contexts import _hit_reroll
    hunter = canonical('vampire-hunters-of-sylvania-lotd5', 'vampire-hunter', 'weapon.mace',
        special_rule_ids=('band--special-skill-thirst-for-vengeance', 'band--special-skill-blessing-of-morr'))
    zombie = canonical('undead', 'zombies', 'weapon.fist')
    assert _hit_reroll(hunter, zombie, hunter.main_weapon, hunter.global_effects, True, False)
    assert not _hit_reroll(hunter, zombie, hunter.main_weapon, hunter.global_effects, False, False)
    assert not _hit_reroll(hunter, enemy(), hunter.main_weapon, hunter.global_effects, True, False)
    assert build_attacks(AttackPoolContext(hunter, True, True, False, False)).attacks == 2
    assert build_attacks(AttackPoolContext(hunter, False, False, False, False)).attacks == 1
    assert strike(hunter, zombie, [('hit', 4), ('wound', 4), ('injury.0', 4)]).defender.condition == Condition.OUT


@pytest.mark.parametrize('toughness,threshold', [(3, 5), (6, 6)])
def test_hellblade_has_exact_nature_filter_and_deadly_wound_boundary(toughness, threshold):
    from mordheim_combat.modular.contexts import prepare_hit_context, prepare_wound_context, _combined_effect
    blade = canonical('khorne-raiders-sar', 'dread-captain', 'weapon.hellblade')
    foe = replace(enemy(), characteristics=replace(enemy().characteristics, toughness=toughness))
    dice = StrictDice([])
    a, d = initialize_fighter(blade, dice, 'a'), initialize_fighter(foe, dice, 'd'); dice.finish()
    effect = _combined_effect(blade, blade.main_weapon)
    ordinary = prepare_hit_context(blade, foe, a, d, blade.main_weapon, effect)
    for band, profile, weapon in [('undead', 'vampire', 'weapon.sword'), ('carnival-of-chaos', 'plague-bearers', 'weapon.fist')]:
        target = canonical(band, profile, weapon)
        context = prepare_hit_context(blade, target, a, d, blade.main_weapon, effect)
        assert context.modifier == target.global_effects.incoming_hit_modifier - int(
            "cloud_of_flies" in target.global_effects.tags
        )
    wound = prepare_wound_context(blade, foe, a, d, blade.main_weapon, effect, hit_roll=4)
    assert wound.critical_threshold == threshold
    assert blade.main_weapon.two_handed and 'attack.magical' in blade.main_weapon.tags
    with pytest.raises(ValueError, match='mortal special metals'):
        canonical('khorne-raiders-sar', 'dread-captain', 'weapon.hellblade', main_material_id='material.gromril')


def test_torturer_strength_loss_accumulates_to_one_and_exempts_undead():
    from mordheim_combat.modular.aftermath import _react_to_wound
    from mordheim_combat.modular.state import AttackOutcome
    warrior = canonical('cursed-cavalcade', 'aristocrat', 'weapon.mace',
        special_rule_ids=('band--cursed-cavalcade-special-skills-torturer',))
    dice = StrictDice([]); a = initialize_fighter(warrior, dice, 'a')
    for foe, expected in [(enemy(), 1), (canonical('undead', 'vampire'), 4)]:
        d = initialize_fighter(foe, dice, 'd')
        for index in range(4):
            d = _react_to_wound(warrior, foe, AttackOutcome(a, d, wounded=True, damage=1), dice, f'x{index}').defender
        assert d.strength == expected
    dice.finish()


@pytest.mark.parametrize("rolls,blocked", [((6, 6), True), ((1, 1), False)])
def test_mesmerising_dance_blocks_attacks_but_preserves_defence(rolls, blocked):
    amazon = canonical('amazons-lustria', 'serpent-priestess', special_rule_ids=(
        'band--amazon-special-skills-mesmerising-dance',))
    foe = enemy()
    tape = [{'key': f'round.0.second.mesmerising-dance.{i}', 'value': r}
            for i, r in enumerate(rolls)]
    tape += [{'key': 'round.0.first.attack.0.hit', 'value': 1}]
    if not blocked:
        tape += [{'key': 'round.0.second.attack.0.hit', 'value': 1}]
    dice = StrictDice(tape); choices = StrictDecisions([])
    state = initialize_duel(amazon, foe, dice, context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(amazon, foe, state, dice, choices)
    assert result.state.second.charm_attack_blocked is blocked
    assert result.state.second.parries_remaining == state.second.parries_remaining
    assert len(result.attacks) == (1 if blocked else 2)
    dice.finish(); choices.finish()


def test_savage_fury_immunity_and_charge_bonus_and_lizardman_exemption():
    amazon = canonical('amazons-lustria', 'serpent-priestess', special_rule_ids=(
        'band--amazon-special-skills-savage-fury',))
    assert 'mechanic.charm-immunity' in amazon.global_effects.tags
    assert 'mechanic.fear-immunity' in amazon.global_effects.tags
    assert build_attacks(AttackPoolContext(amazon, True, True)).attacks == 2
    lizard = canonical('lizardmen', 'skink-priest')
    assert 'species.lizardman' in lizard.global_effects.tags


def test_shornaal_uses_highest_two_then_stops_testing_after_success():
    mark = canonical('marauders-of-chaos', 'marauder-chieftain', special_rule_ids=(
        'band--mark-of-shornaal',))
    foe = enemy()
    dice = StrictDice([
        *({'key': f'round.0.second.shornaal.{i}', 'value': r} for i, r in enumerate((1, 3, 4))),
        {'key': 'round.0.first.attack.0.hit', 'value': 1},
        {'key': 'round.0.second.attack.0.hit', 'value': 1},
        {'key': 'round.1.first.attack.0.hit', 'value': 1},
        {'key': 'round.1.second.attack.0.hit', 'value': 1},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(mark, foe, dice, context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(mark, foe, state, dice, choices)
    assert 'mark-of-shornaal.passed' in result.state.second.resources_spent
    resolve_round(mark, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    with pytest.raises(ValueError, match='not available'):
        canonical('marauders-of-chaos', 'seer', special_rule_ids=('band--mark-of-shornaal',))


def test_hypnotist_first_attack_breaks_trance_even_when_saved():
    sleuth = canonical('watchmen-mim', 'private-sleuth')
    foe = enemy(armour='armour.heavy-armour')
    dice = StrictDice([
        {'key': 'round.0.first.hypnotist.0', 'value': 6},
        {'key': 'round.0.first.hypnotist.1', 'value': 6},
        {'key': 'round.0.first.attack.0.wound', 'value': 4},
        {'key': 'round.0.first.attack.0.armour', 'value': 6},
        {'key': 'round.0.second.attack.0.hit', 'value': 1},
    ])
    choices = StrictDecisions([{'key': 'round.0.first.hypnotist', 'value': True}])
    state = initialize_duel(sleuth, foe, dice, context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(sleuth, foe, state, dice, choices)
    assert result.attacks[0].hit and result.attacks[0].saved
    assert not result.state.second.entranced
    assert len(result.attacks) == 2
    dice.finish(); choices.finish()


@pytest.mark.parametrize('band,profile,rule', [
    ('ostlanders', 'elder', 'band--ostlander-special-skills-foul-odour'),
    ('horned-hunters', 'horned-hunter', 'band--horned-hunter-special-skills-foul-odour'),
])
def test_foul_odour_exact_opponents_and_fire_strength(band, profile, rule):
    from mordheim_combat.modular.contexts import _attack_strength, _combined_effect, prepare_hit_context
    fighter = canonical(band, profile, special_rule_ids=(rule,))
    foe = enemy()
    init = StrictDice([]); own = initialize_fighter(fighter, init, 'a'); other = initialize_fighter(foe, init, 'b')
    effect = _combined_effect(foe, foe.main_weapon)
    hit = prepare_hit_context(foe, fighter, other, own, foe.main_weapon, effect, first_round=False, charging=False, helpless_at_start=False, key='h')
    assert hit.modifier == -1
    fire = replace(effect, tags=(*effect.tags, 'attack.fire'))
    assert _attack_strength(foe, fighter, other, foe.main_weapon, fire, False, False)[0] == other.strength + 1
    undead = canonical('undead', 'vampire')
    current = initialize_fighter(undead, init, 'u')
    hit = prepare_hit_context(undead, fighter, current, own, undead.main_weapon, _combined_effect(undead, undead.main_weapon), first_round=False, charging=False, helpless_at_start=False, key='h')
    assert hit.modifier == 0
    init.finish()


def test_wraith_touch_single_unarmed_wound_and_liche_recovery():
    from mordheim_combat.modular.rounds import select_attack_replacement
    liche = canonical('restless-dead', 'liche', special_rule_ids=('band--restless-dead-special-skills-wraith-touch',))
    choices = StrictDecisions([{'key': 'x.wraith-touch', 'value': True}, {'key': 'x.wraith-heal', 'value': True}])
    active = select_attack_replacement(liche, first_round=False, charging=False, decisions=choices, key='x')
    assert build_attacks(AttackPoolContext(active, False)).attacks == 1
    foe = enemy()
    init = StrictDice([]); own = replace(initialize_fighter(liche, init, 'a'), wounds=1); other = initialize_fighter(foe, init, 'b'); init.finish()
    dice = StrictDice([{'key': 'x.hit', 'value': 4}, {'key': 'x.armour', 'value': 1}])
    result = resolve_reference_attack(active, foe, own, other, active.main_weapon, dice, key='x', decisions=choices)
    assert result.wounded and result.damage == 1 and result.attacker.wounds == 2
    dice.finish(); choices.finish()
    immune = canonical('undead', 'vampire')
    dice = StrictDice([])
    result = resolve_reference_attack(active, immune, own, initialize_fighter(immune, dice, 'u'), active.main_weapon, dice, key='x')
    assert not result.hit
    dice.finish()


def test_titanic_strength_failed_wound_knocks_down_on_failed_strength():
    fighter = canonical('brood-of-ghurash-the-sc', 'broodmother', 'weapon.axe', special_rule_ids=('band--skill-titanic-strength',))
    foe = enemy()
    result = strike(fighter, foe, [('hit', 4), ('wound', 1), ('titanic-strength', 6)])
    assert result.hit and not result.wounded and result.defender.condition == Condition.KNOCKED_DOWN


@pytest.mark.parametrize('magical,saved', [(False, True), (True, False)])
def test_ethereal_hit_save_precedes_wound_and_ignores_magic(magical, saved):
    spirit = canonical('call-of-the-night-haint-mim', 'malignant-spirits', 'weapon.natural-attacks')
    attacker = enemy()
    if magical:
        attacker = replace(attacker, main_weapon=replace(attacker.main_weapon, tags=(*attacker.main_weapon.tags, 'attack.magical')))
    rolls = [('hit', 4), ('wound', 1)] if magical else [('hit', 4), ('ethereal', 4)]
    result = strike(attacker, spirit, rolls)
    assert result.saved is saved
    assert not result.wounded


def test_centigor_drunken_frenzy_expires_after_its_turn():
    centigor = canonical('beastmen-raiders', 'centigors', 'weapon.axe')
    foe = enemy()
    dice = StrictDice([
        {'key': 'round.0.first.drunken', 'value': 6},
        {'key': 'round.0.first.attack.0.hit', 'value': 1},
        {'key': 'round.0.first.attack.1.hit', 'value': 1},
        {'key': 'round.0.first.attack.2.hit', 'value': 1},
        {'key': 'round.0.second.attack.0.hit', 'value': 1},
        {'key': 'round.1.second.attack.0.hit', 'value': 1},
        {'key': 'round.1.first.attack.0.hit', 'value': 1},
        {'key': 'round.1.first.attack.1.hit', 'value': 1},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(centigor, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(centigor, foe, state, dice, choices)
    assert result.state.first.frenzy
    assert len(result.attacks) == 4
    result = resolve_round(centigor, foe, result.state, dice, choices)
    assert not result.state.first.frenzy and len(result.attacks) == 3
    dice.finish(); choices.finish()


def test_fire_fear_preserves_branchnymph_printed_psychology_exception():
    from mordheim_combat.modular.psychology import resolve_fear
    nymph = canonical('fen-guard-mim', 'branchnymph', 'weapon.natural-attacks')
    assert 'mechanic.psychology-immunity' in nymph.global_effects.tags
    foe = enemy(trait_overrides={'lit_item': True})
    dice = StrictDice([{'key': 'round.0.first.fear.charge.0', 'value': 6},
                       {'key': 'round.0.first.fear.charge.1', 'value': 6}])
    state = initialize_duel(nymph, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_fear(nymph, foe, state, dice, StrictDecisions([]))
    assert not result.engaged and result.failed_charges == frozenset({'first'})
    dice.finish()


def test_racial_hatred_and_noble_disdain_use_canonical_opponent_facts():
    from mordheim_combat.modular.contexts import _hit_reroll, _combined_effect
    hater = canonical('tileans', 'captain')
    skaven = canonical('skaven-clan-eshin', 'assassin-adept')
    assert 'species.skaven' in skaven.global_effects.tags
    assert _hit_reroll(hater, skaven, hater.main_weapon,
                       _combined_effect(hater, hater.main_weapon), True, False)
    assert not _hit_reroll(hater, skaven, hater.main_weapon,
                           _combined_effect(hater, hater.main_weapon), False, False)
    knight = canonical('bretonnian-knights', 'questing-knight',
                       special_rule_ids=('band--virtue-of-noble-disdain',))
    armed = enemy(owned_item_ids=('bow',))
    assert 'condition.ranged-armed' in armed.global_effects.tags
    assert _hit_reroll(knight, armed, knight.main_weapon,
                       _combined_effect(knight, knight.main_weapon), True, False)
    assert not _hit_reroll(knight, enemy(), knight.main_weapon,
                           _combined_effect(knight, knight.main_weapon), True, False)


def test_arkhar_is_a_selected_leader_mark_not_a_bandwide_grant():
    leader = canonical('marauders-of-chaos', 'marauder-chieftain',
                       special_rule_ids=('band--mark-of-arkhar',))
    control = canonical('marauders-of-chaos', 'champions')
    assert leader.global_effects.frenzy and not control.global_effects.frenzy
    with pytest.raises(ValueError):
        canonical('marauders-of-chaos', 'champions', special_rule_ids=('band--mark-of-arkhar',))


@pytest.mark.parametrize('fearing', [False, True])
def test_wheelo_collision_precedes_blows_and_fear_does_not_cancel_charge(fearing):
    wheelo = canonical('snotlings-web', 'wheelo', 'weapon.dagger')
    foe = enemy(trait_overrides={'causes_fear': fearing})
    rolls = ([{'key': 'round.0.first.fear.charge.0', 'value': 6},
              {'key': 'round.0.first.fear.charge.1', 'value': 6}] if fearing else [])
    rolls += [
        {'key': 'round.0.first.impact-count', 'value': 3},
        {'key': 'round.0.first.impact.0.wound', 'value': 1},
        {'key': 'round.0.first.impact.1.wound', 'value': 1},
        {'key': 'round.0.first.attack.0.hit', 'value': 1},
        {'key': 'round.0.first.attack.1.hit', 'value': 1},
        {'key': 'round.0.second.attack.0.hit', 'value': 1},
    ]
    dice = StrictDice(rolls); choices = StrictDecisions([])
    state = initialize_duel(wheelo, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(wheelo, foe, state, dice, choices)
    assert len(result.attacks) == 5 and all(a.hit for a in result.attacks[:2])
    assert result.state.engaged and result.state.first.fear_hit_sixes is fearing
    assert result.attacks[2].hit_target == (6 if fearing else 4)
    dice.finish(); choices.finish()


@pytest.mark.parametrize('sex', ['male', 'female'])
def test_sea_singer_beauty_uses_explicit_sex_and_distinct_charge_tests(sex):
    from mordheim_combat.modular.psychology import resolve_fear
    singer = canonical('ghost-pirates-sar', 'sea-singer', 'weapon.dagger')
    target = enemy(trait_overrides={'sex': sex})
    prefix = 'beauty-charge' if sex == 'male' else 'fear.charge'
    dice = StrictDice([{'key': f'round.0.first.{prefix}.0', 'value': 6},
                       {'key': f'round.0.first.{prefix}.1', 'value': 6}])
    state = initialize_duel(target, singer, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_fear(target, singer, state, dice, StrictDecisions([]))
    assert not result.engaged
    dice.finish()
    unknown = enemy()
    with pytest.raises(ValueError, match='explicit male/female'):
        resolve_fear(unknown, singer, initialize_duel(unknown, singer, StrictDice([]),
            context=DuelContext(charging=('first',), active_participant='first')), StrictDice([]), StrictDecisions([]))



def test_supplied_follow_me_command_expires_after_the_current_turn():
    fighter = enemy(trait_overrides={'active_command': 'follow-me-mine-pugnacious-ones'})
    fighter = replace(fighter, characteristics=replace(fighter.characteristics, initiative=4))
    foe = enemy()
    dice = StrictDice([{'key': f'round.{r}.{side}.attack.0.hit', 'value': 1}
                       for r in (0, 1) for side in ('first', 'second')])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    first = resolve_round(fighter, foe, state, dice, StrictDecisions([]))
    second = resolve_round(fighter, foe, first.state, dice, StrictDecisions([]))
    assert first.attacks[0].hit_target == 3 and second.attacks[0].hit_target == 4
    dice.finish()


@pytest.mark.parametrize('command,condition', [(None, Condition.OUT),
    ('art-thou-ready-to-die-fighting', Condition.STUNNED)])
def test_supplied_ready_to_die_command_changes_the_actual_injury(command, condition):
    fighter = enemy(trait_overrides={'active_command': command} if command else {})
    fighter = replace(fighter, characteristics=replace(fighter.characteristics, wounds=1))
    foe = enemy()
    dice = StrictDice([
        {'key': 'round.0.first.attack.0.hit', 'value': 1},
        {'key': 'round.0.second.attack.0.hit', 'value': 4},
        {'key': 'round.0.second.attack.0.wound', 'value': 4},
        {'key': 'round.0.second.attack.0.injury.0', 'value': 5},
    ])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(fighter, foe, state, dice, StrictDecisions([]))
    assert result.state.first.condition == condition
    dice.finish()



def test_simple_night_goblin_animosity_blocks_only_its_own_turn():
    goblin = canonical('night-goblins-mic', 'big-boss', 'weapon.dagger')
    foe = enemy()
    dice = StrictDice([
        {'key': 'round.0.first.animosity', 'value': 1},
        {'key': 'round.0.second.attack.0.hit', 'value': 1},
        {'key': 'round.1.priority-tie', 'value': 1},
        {'key': 'round.1.second.attack.0.hit', 'value': 1},
        {'key': 'round.1.first.attack.0.hit', 'value': 1},
    ])
    state = initialize_duel(goblin, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(goblin, foe, state, dice, StrictDecisions([]))
    assert result.state.first.animosity_failed and len(result.attacks) == 1
    result = resolve_round(goblin, foe, result.state, dice, StrictDecisions([]))
    assert not result.state.first.animosity_failed and len(result.attacks) == 2
    dice.finish()
    squig = canonical('night-goblins-mic', 'cave-squigs', 'weapon.natural-attacks')
    assert 'mechanic.goblin-squabble' not in squig.global_effects.tags


@pytest.mark.parametrize('species,fear', [('human', True), ('dwarf', False)])
def test_gaoler_reputation_causes_fear_only_in_humans(species, fear):
    from mordheim_combat.modular.psychology import causes_fear
    gaoler = canonical('black-dwarfs', 'gaolers', 'weapon.axe')
    foe = enemy(trait_overrides={'species': species})
    assert causes_fear(gaoler, foe) is fear



@pytest.mark.parametrize('profile,eligible', [('halfling-thief', True), ('village-ogre', False)])
def test_wizened_supplied_leader_reroll_has_halfling_recipients(profile, eligible):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    leader = canonical('halflings-mic', 'halfling-elder', 'weapon.dagger',
                       special_rule_ids=('halfling-elder--wizened-halfling',))
    fighter = canonical('halflings-mic', profile, 'weapon.fist')
    foe = enemy()
    context = DuelContext(charging=('first',), active_participant='first',
        nearby=(LocalParticipant('elder', 'first', leader),), distances=(('first', 'elder', 6),))
    state = initialize_duel(fighter, foe, StrictDice([]), context=context)
    rolls = [{'key': 'probe.0', 'value': 6}, {'key': 'probe.1', 'value': 6}]
    choices = [{'key': 'probe.leader.elder', 'value': False}]
    if eligible:
        rolls += [{'key': 'probe.reroll.0', 'value': 1}, {'key': 'probe.reroll.1', 'value': 1}]
        choices += [{'key': 'probe.reroll', 'value': True}]
    dice = StrictDice(rolls); decisions = StrictDecisions(choices)
    assert resolve_local_leadership(fighter, state, dice, decisions, 'probe', first=True) is eligible
    dice.finish(); decisions.finish()



@pytest.mark.parametrize('profile,immune', [('giant-slayer', True), ('stubbles', False), ('rememberer', False)])
def test_slayer_compound_rule_preserves_novice_and_rememberer_exceptions(profile, immune):
    slayer = canonical('dwarf-slayer-cult-web', profile, 'weapon.axe')
    assert ('mechanic.psychology-immunity' in slayer.global_effects.tags) is immune
    if profile != 'rememberer':
        with pytest.raises(ValueError, match='armour is forbidden'):
            canonical('dwarf-slayer-cult-web', profile, 'weapon.axe', armour_id='armour.light-armour')
    else:
        assert canonical('dwarf-slayer-cult-web', profile, 'weapon.axe', armour_id='armour.light-armour').armour_save < 7


def test_ogre_hunter_huuuuge_preserves_light_armour_but_refuses_heavy():
    # The Ogre Equipment List offers the Cleaver (which counts as an Axe);
    # ``weapon.cleaver`` is the axe-profile weapon the list actually resolves.
    assert canonical('ogre-hunting-party-web', 'ogre-hunter', 'weapon.cleaver', armour_id='armour.light-armour').armour_save == 6
    with pytest.raises(ValueError, match='heavy armour'):
        canonical('ogre-hunting-party-web', 'ogre-hunter', 'weapon.cleaver', armour_id='armour.heavy-armour')



def test_shared_slayer_prohibition_uses_declared_thrown_and_cloak_facts():
    from mordheim_construction.eligibility import call
    from mordheim_knowledge.loader import load_items
    items = {row['id']: row for row in load_items('mordheim')}
    for item_id, forbidden in [('throwing_knives', False), ('javelin', False), ('pistol', True), ('bow', True)]:
        item = items[item_id]
        assert call('tokenForbids', 'non-thrown-ranged', item_id,
                    {'kind': item['kind'], 'tags': item.get('tags', []), 'mechanic_id': None}) is forbidden
    cloak = items['wolf_pelt_cloak']
    assert call('tokenForbids', 'constant-save-cloak', 'wolf_pelt_cloak',
                {'kind': cloak['kind'], 'tags': cloak['tags'], 'mechanic_id': None})



def test_supplied_righteous_charge_is_mounted_and_expires_after_first_round():
    fighter = canonical('knights-of-the-bitter-moors-mim', 'questing-knight',
                       mounted=True, trait_overrides={'righteous_charge_active': True})
    foe = canonical('undead', 'zombies', 'weapon.fist')
    dice = StrictDice([{'key': f'round.{r}.{side}.attack.0.hit', 'value': 1}
                       for r in (0, 1) for side in ('first', 'second')])
    state = initialize_duel(fighter, foe, dice, context=DuelContext(charging=('first',), active_participant='first'))
    first = resolve_round(fighter, foe, state, dice, StrictDecisions([]))
    second = resolve_round(fighter, foe, first.state, dice, StrictDecisions([]))
    assert first.attacks[0].hit_target == second.attacks[0].hit_target - 1
    dice.finish()
    with pytest.raises(ValueError, match='mounted recipient'):
        canonical('knights-of-the-bitter-moors-mim', 'questing-knight',
                  trait_overrides={'righteous_charge_active': True})



def test_foul_odour_refuses_any_supplied_open_flame_through_shared_legality():
    rule = 'band--ostlander-special-skills-foul-odour'
    assert canonical('ostlanders', 'elder', special_rule_ids=(rule,))
    with pytest.raises(ValueError, match='Foul Odour forbids carrying open flames'):
        canonical('ostlanders', 'elder', special_rule_ids=(rule,), trait_overrides={'lit_item': True})


@pytest.mark.parametrize('material,ward', [('material.normal', 4), ('material.gromril', 7), ('material.ithilmar', 7)])
def test_ghost_pirate_ethereal_save_is_source_specific(material, ward):
    from mordheim_combat.modular.contexts import prepare_special_save_context
    ghost = canonical('ghost-pirates-sar', 'ghost-captain', 'weapon.dagger')
    attacker = enemy(main_material_id=material)
    assert prepare_special_save_context(ghost, attacker.main_weapon).ward_save == ward
    assert 'mechanic.ghost-pirate-ethereal' not in canonical('ghost-pirates-sar', 'sea-singer', 'weapon.dagger').global_effects.tags
    if ward == 4:
        dice = StrictDice([{'key': 'probe.hit', 'value': 4}, {'key': 'probe.wound', 'value': 4},
                           {'key': 'probe.special.ward', 'value': 4}])
        outcome = resolve_reference_attack(attacker, ghost, initialize_fighter(attacker, dice, "a"),
            initialize_fighter(ghost, dice, "b"), attacker.main_weapon, dice, key='probe')
        assert outcome.saved and outcome.wounded
        dice.finish()
        with pytest.raises(ValueError, match='Ethereal cannot'):
            canonical('ghost-pirates-sar', 'ghost-captain', 'weapon.dagger', skill_ids=('skill.step-aside',))


@pytest.mark.parametrize('fitting', ['axe', 'club', 'spear', 'morning-star'])
def test_wheelo_fitting_modifies_impact_without_changing_crew(fitting):
    wheelo = canonical('snotlings-web', 'wheelo', 'weapon.dagger', trait_overrides={'wheelo_fitting': fitting})
    foe = replace(enemy(armour='armour.heavy-armour'), characteristics=replace(enemy().characteristics, wounds=1))
    counter = fitting == 'spear'
    rolls = [] if counter else [{'key': 'round.0.first.impact-count', 'value': 1}]
    rolls += [{'key': 'round.0.first.impact.0.wound', 'value': 2 if fitting == 'morning-star' else 4}]
    if fitting in {'club', 'spear'}:
        rolls += [{'key': 'round.0.first.impact.0.armour', 'value': 1}]
    rolls += [{'key': 'round.0.first.impact.0.injury.0', 'value': 2}]
    # Knocked-down targets are hit automatically; crew wound rolls fail.
    # A stunned target is finished automatically by the first crew attack.
    if fitting != 'club':
        rolls += [{'key': f'round.0.first.attack.{i}.wound', 'value': 1} for i in range(2)]
    dice = StrictDice(rolls)
    state = initialize_duel(wheelo, foe, dice, context=DuelContext(
        charging=('second',) if counter else ('first',), active_participant='second' if counter else 'first'))
    result = resolve_round(wheelo, foe, state, dice, StrictDecisions([]))
    assert result.attacks[0].hit and result.attacks[0].wounded
    assert result.attacks[0].defender.condition == (Condition.STUNNED if fitting == 'club' else Condition.KNOCKED_DOWN)
    assert 'wheelo.first-impact' in result.state.first.resources_spent
    dice.finish()
    if fitting == 'axe':
        with pytest.raises(ValueError, match='requires a Wheelo'):
            enemy(trait_overrides={'wheelo_fitting': fitting})


def test_wheelo_mighty_blow_replaces_strength_with_crew_wound_bonus():
    fighter = canonical('snotlings-web', 'wheelo', 'weapon.dagger', skill_ids=('skill.mighty-blow',))
    assert fighter.global_effects.strength_bonus == 0
    assert fighter.global_effects.wound_modifier == 1


def test_norse_shield_and_bulwark_are_equipment_bound():
    from mordheim_combat.modular.contexts import prepare_armour_context
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.norse-bearman-bodyguard',
        'weapon.axe', off_hand_id='defence.shield', armour_id='armour.light-armour')
    foe = enemy()
    dice = StrictDice([])
    state = initialize_fighter(fighter, dice, 'b')
    attacking = initialize_fighter(foe, dice, 'a')
    assert fighter.off_hand.parry
    assert prepare_armour_context(foe, fighter, attacking, state, foe.main_weapon, foe.main_weapon).armour_save == 4
    # Isolate the equipment predicate; this replacement is not a printed kit.
    unarmed = replace(fighter, main_weapon=foe.main_weapon)
    assert prepare_armour_context(foe, unarmed, attacking, state, foe.main_weapon, foe.main_weapon).armour_save == 5
    no_shield = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.norse-bearman-bodyguard',
        'weapon.axe', armour_id='armour.light-armour')
    assert no_shield.off_hand is None
    assert prepare_armour_context(foe, no_shield, attacking, state, foe.main_weapon, foe.main_weapon).armour_save == 6
    dice.finish()


def test_bog_hunter_stink_applies_to_undead_enemies_too():
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.bog-hunter', 'weapon.beastlash')
    foe = enemy(trait_overrides={'creature_kind': 'undead'})
    dice = StrictDice([{'key': 'probe.hit', 'value': 1}])
    outcome = resolve_reference_attack(foe, fighter, initialize_fighter(foe, dice, 'a'),
        initialize_fighter(fighter, dice, 'b'), foe.main_weapon, dice, key='probe')
    assert outcome.hit_target == 5
    assert not outcome.hit
    dice.finish()


@pytest.mark.parametrize('aquatic,expected', [(False, 1), (True, 2)])
def test_native_whaler_doubles_only_unsaved_aquatic_damage(aquatic, expected):
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.whaler', 'weapon.spear')
    foe = enemy(trait_overrides={'aquatic': aquatic})
    foe = replace(foe, characteristics=replace(foe.characteristics, wounds=4))
    dice = StrictDice([{'key': 'x.hit', 'value': 4}, {'key': 'x.wound', 'value': 4}])
    a = initialize_fighter(fighter, dice, 'a'); d = initialize_fighter(foe, dice, 'd')
    result = resolve_reference_attack(fighter, foe, a, d, fighter.main_weapon, dice, key='x')
    dice.finish()
    assert result.damage == expected and result.defender.wounds == 4 - expected
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, foe)


@pytest.mark.parametrize('nominated,sex,target', [(True, 'female', 3), (False, 'female', 4), (False, 'male', 4)])
def test_native_pimp_bonus_requires_nominated_female_opponent(nominated, sex, target):
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.halfling-pimp',
        'weapon.dagger', trait_overrides={'flesh_peddler_mark': nominated})
    foe = enemy(trait_overrides={'sex': sex})
    dice = StrictDice([{'key': 'x.hit', 'value': 1}])
    a = initialize_fighter(fighter, dice, 'a'); d = initialize_fighter(foe, dice, 'd')
    result = resolve_reference_attack(fighter, foe, a, d, fighter.main_weapon, dice, key='x')
    dice.finish()
    assert result.hit_target == target and not result.hit


def test_pimp_nomination_refuses_wrong_recipient_and_nonfemale_target():
    with pytest.raises(ValueError, match='requires Flesh-Peddler'):
        enemy(trait_overrides={'flesh_peddler_mark': True})
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.halfling-pimp',
        'weapon.dagger', trait_overrides={'flesh_peddler_mark': True})
    foe = enemy(trait_overrides={'sex': 'male'})
    dice = StrictDice([])
    with pytest.raises(ValueError, match='explicit female'):
        resolve_reference_attack(fighter, foe, initialize_fighter(fighter, dice, 'a'),
            initialize_fighter(foe, dice, 'd'), fighter.main_weapon, dice, key='x')
    dice.finish()


@pytest.mark.parametrize('profile,weapon,off', [
    ('trickster-priest-of-ranald', 'weapon.sword', 'weapon.dagger'),
    ('druid-priest-of-taal', 'weapon.dagger', None),
])
def test_native_priest_strictures_compile_kit_and_refuse_foreign_equipment(profile, weapon, off):
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.' + profile, weapon, off_hand_id=off)
    assert weapon in fighter.main_weapon.tags
    for override in ({'armour_id': 'armour.heavy-armour'}, {'main_weapon_id': 'weapon.pistol'},
                     {'main_weapon_id': 'weapon.axe'}):
        options = {'off_hand_id': off, **override}
        selected = options.pop('main_weapon_id', weapon)
        with pytest.raises(ValueError):
            canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.' + profile, selected, **options)


@pytest.mark.parametrize('charging,undead,success', [(False, True, False), (True, True, False),
    (True, True, True), (True, False, False)])
def test_morrs_servant_fear_exception_has_both_charge_directions(charging, undead, success):
    from mordheim_combat.modular.psychology import resolve_fear
    from mordheim_combat.modular.state import DuelState
    # Explicit isolated mechanic fixture: canonical Morr remains source-blocked
    # by his ceremonial weapon, so this is not a canonical-access assertion.
    priest = enemy()
    priest = replace(priest, global_effects=replace(priest.global_effects,
        tags=(*priest.global_effects.tags, 'mechanic.morrs-servant')))
    target = enemy(trait_overrides={'creature_kind': 'undead' if undead else 'living'})
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, 'mechanic.psychology-immunity', 'mechanic.fear-immunity', 'mechanic.causes-fear')))
    # A frightening priest avoids unrelated Fear tests on this fixture.
    priest = replace(priest, global_effects=replace(priest.global_effects,
        tags=(*priest.global_effects.tags, 'mechanic.causes-fear')))
    dice = StrictDice([])
    own = initialize_fighter(priest, dice, 'p'); other = initialize_fighter(target, dice, 't')
    state = DuelState(own, other, first_charged=not charging, second_charged=charging)
    suffix = 'charge' if charging else 'charged'
    tape = StrictDice([{'key': 'round.0.second.fear.' + suffix + '.' + str(i),
        'value': 1 if success else 6} for i in range(2)] if undead else [])
    decisions = StrictDecisions([])
    result = resolve_fear(priest, target, state, tape, decisions)
    tape.finish(); decisions.finish()
    if undead and not success:
        if charging: assert not result.second_charged and not result.engaged
        else: assert result.second.fear_hit_sixes
    else:
        assert result.engaged and not result.second.fear_hit_sixes
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(priest, target)


def test_native_morr_ceremonial_scythe_is_a_distinct_complete_weapon():
    priest = canonical('hirelings.hired-sword.2b',
        'hireling.hired-sword.priest-of-morr-miracle-workers', 'weapon.ceremonial-scythe')
    assert priest.main_weapon.strength_bonus == 1
    assert priest.main_weapon.two_handed and priest.main_weapon.armour_penetration == 0
    assert 'mechanic.morrs-servant' in priest.global_effects.tags
    # S4 wounds T3 on 3+ and only Strength reduces the enemy's armour.
    result = strike(priest, enemy(armour='armour.heavy-armour'),
        [('hit', 4), ('wound', 3), ('armour', 6)])
    assert result.wounded and result.saved
    generic = enemy(weapon='weapon.scythe')
    assert generic.main_weapon.strength_bonus == 0 and generic.main_weapon.armour_penetration == 1
    for options in ({'off_hand_id': 'weapon.dagger'}, {'off_hand_id': 'defence.shield'},
                    {'off_hand_id': 'defence.buckler'}, {'armour_id': 'armour.light-armour'}):
        with pytest.raises(ValueError):
            canonical('hirelings.hired-sword.2b',
                'hireling.hired-sword.priest-of-morr-miracle-workers', 'weapon.ceremonial-scythe', **options)
    with pytest.raises(ValueError):
        canonical('hirelings.hired-sword.2b',
            'hireling.hired-sword.priest-of-morr-miracle-workers', 'weapon.scythe')


def test_native_verena_sword_only_keeps_owned_ceremonial_dagger_inactive():
    profile = 'hireling.hired-sword.priest-of-verena'
    priest = canonical('hirelings.hired-sword.2b', profile, 'weapon.sword',
        owned_item_ids=('dagger', 'sword'))
    assert priest.main_weapon.parry
    assert strike(priest, enemy(), [('hit', 4), ('wound', 3)]).wounded is False
    for weapon, off in [('weapon.dagger', None), ('weapon.sword', 'weapon.dagger'),
                        ('weapon.axe', None)]:
        with pytest.raises(ValueError):
            canonical('hirelings.hired-sword.2b', profile, weapon, off_hand_id=off)


@pytest.mark.parametrize('strength,roll,saved', [(3, 6, True), (3, 5, False), (4, None, False)])
def test_native_ulric_pelt_is_strength_modified_armour_not_a_ward(strength, roll, saved):
    wolf = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.wolf-priest-of-ulric-miracle-workers', 'weapon.dagger')
    assert wolf.armour_save == 6 and wolf.global_effects.ward_save == 7
    incoming = enemy(strength=strength)
    tape = [('hit', 4), ('wound', 4)]
    if roll is not None: tape.append(('armour', roll))
    if not saved: tape.append(('injury.0', 1))
    result = strike(incoming, wolf, tape)
    assert result.saved is saved and result.damage == (0 if saved else 1)


def test_ulric_pelt_contributes_once_and_the_printed_kit_refuses_other_armour():
    profile = 'hireling.hired-sword.wolf-priest-of-ulric-miracle-workers'
    wolf = canonical('hirelings.hired-sword.2b', profile, 'weapon.dagger', defence_ids=('defence.wolf-pelt-cloak',))
    assert wolf.armour_save == 6
    for options in ({'armour_id': 'armour.light-armour'}, {'main_weapon_id': 'weapon.pistol'},
                    {'off_hand_id': 'defence.shield'}):
        selected = options.pop('main_weapon_id', 'weapon.dagger')
        with pytest.raises(ValueError): canonical('hirelings.hired-sword.2b', profile, selected, **options)
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(wolf, enemy())


@pytest.mark.parametrize('rival,first_round', [(True, True), (True, False), (False, True)])
def test_ulric_intense_rivals_reuses_first_round_hatred_only(rival, first_round):
    wolf = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.wolf-priest-of-ulric-miracle-workers', 'weapon.dagger')
    target = enemy(trait_overrides={'ulric_rival': rival})
    tape = [{'key': 'x.hit', 'value': 1}]
    if rival and first_round: tape.append({'key': 'x.hit.reroll', 'value': 1})
    dice = StrictDice(tape)
    result = resolve_reference_attack(wolf, target, initialize_fighter(wolf, dice, 'w'),
        initialize_fighter(target, dice, 't'), wolf.main_weapon, dice, key='x', first_round=first_round)
    dice.finish()
    assert not result.hit


def test_ulric_rival_identity_does_not_expand_to_an_entire_witch_hunter_warband():
    hunter = canonical('witch-hunters', 'witch-hunters')
    priest = canonical('witch-hunters', 'warrior-priest', 'weapon.mace')
    zealot = canonical('witch-hunters', 'zealots', 'weapon.mace')
    assert 'identity.ulric-rival' in hunter.global_effects.tags
    assert 'identity.ulric-rival' in priest.global_effects.tags
    assert 'identity.ulric-rival' not in zealot.global_effects.tags


@pytest.mark.parametrize('accept', [True, False])
def test_native_war_honed_first_failure_cannot_be_reserved_for_a_later_test(accept):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_combat.modular.state import DuelState
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.war-priestess-of-myrmidia', 'weapon.dagger')
    foe = enemy()
    dice = StrictDice([{'key': key, 'value': face} for key, face in (
        [('passed.0', 1), ('passed.1', 1), ('failed.0', 6), ('failed.1', 6)]
        + ([('failed.reroll.0', 1), ('failed.reroll.1', 1)] if accept else [])
        + [('later.0', 6), ('later.1', 6)])])
    decisions = StrictDecisions([{'key': 'failed.reroll', 'value': accept}])
    state = DuelState(initialize_fighter(fighter, dice, 'a'), initialize_fighter(foe, dice, 'b'))
    passed, current = resolve_local_leadership(fighter, state, dice, decisions, 'passed', first=True, opponent=foe, return_state=True)
    assert passed and 'leadership.first-failed' not in current.resources_spent
    passed, current = resolve_local_leadership(fighter, replace(state, first=current), dice, decisions, 'failed', first=True, opponent=foe, return_state=True)
    assert passed is accept and 'leadership.first-failed' in current.resources_spent
    passed, current = resolve_local_leadership(fighter, replace(state, first=current), dice, decisions, 'later', first=True, opponent=foe, return_state=True)
    assert not passed and 'leadership.first-failed' in current.resources_spent
    dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='returned fighter state'):
        resolve_local_leadership(fighter, state, StrictDice([]), StrictDecisions([]), 'unsafe', first=True)


def test_war_honed_resource_survives_a_real_crude_belch_round():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    halfling = canonical('halflings-mic', 'halfling-elder', 'weapon.mace', special_rule_ids=('halfling-elder--crude-belch',))
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.war-priestess-of-myrmidia', 'weapon.dagger')
    dice = StrictDice([{'key': key, 'value': face} for key, face in (
        ('round.0.first.crude-belch.leadership.0', 6), ('round.0.first.crude-belch.leadership.1', 6),
        ('round.0.first.crude-belch.leadership.reroll.0', 1), ('round.0.first.crude-belch.leadership.reroll.1', 1),
        ('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1),
        ('later.0', 6), ('later.1', 6))])
    decisions = StrictDecisions([{'key': 'round.0.first.crude-belch', 'value': True},
        {'key': 'round.0.first.crude-belch.leadership.reroll', 'value': True}])
    state = initialize_duel(halfling, fighter, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(halfling, fighter, state, dice, decisions)
    assert len(result.attacks) == 2 and 'leadership.first-failed' in result.state.second.resources_spent
    passed, current = resolve_local_leadership(fighter, result.state, dice, decisions, 'later', first=False,
        psychology=True, opponent=halfling, return_state=True)
    assert not passed and 'leadership.first-failed' in current.resources_spent
    dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, halfling)


@pytest.mark.parametrize('traits,automatic', [({'species': 'orc'}, True), ({'species': 'goblin'}, True),
    ({'chaos_follower': True}, True), ({'creature_kind': 'daemon'}, True), ({'species': 'human'}, False), ({'species': 'skaven'}, True)])
def test_optional_sigmar_enlightened_uses_only_the_supported_opponent_identity(traits, automatic):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_combat.modular.state import DuelState
    profile = 'hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers'
    mark = profile + '.skill.enlightened'
    fighter = canonical('hirelings.hired-sword.2b', profile, 'weapon.dagger', special_rule_ids=(mark,))
    foe = enemy(trait_overrides=traits)
    if traits.get('species') == 'skaven':
        # The user accepts the maintained chaotic classification for this rule.
        foe = replace(foe, global_effects=replace(foe.global_effects,
            tags=(*foe.global_effects.tags, 'warband-group.chaotic')))
    dice = StrictDice([] if automatic else [{'key': 'ld.0', 'value': 6}, {'key': 'ld.1', 'value': 6}])
    state = DuelState(initialize_fighter(fighter, dice, 'a'), initialize_fighter(foe, dice, 'b'))
    passed, current = resolve_local_leadership(fighter, state, dice, StrictDecisions([]), 'ld',
        first=True, opponent=foe, return_state=True)
    assert passed is automatic and not current.resources_spent
    dice.finish()
    assert 'mechanic.sigmar-enlightened' in fighter.global_effects.tags
    assert not any('unity' in tag for tag in fighter.global_effects.tags)
    fearsome = replace(foe, global_effects=replace(foe.global_effects,
        tags=(*foe.global_effects.tags, 'mechanic.causes-fear')))
    keys = [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)] if automatic else [
        ('round.0.first.fear.charge.0', 6), ('round.0.first.fear.charge.1', 6)]
    dice = StrictDice([{'key': key, 'value': value} for key, value in keys])
    choices = StrictDecisions([])
    state = initialize_duel(fighter, fearsome, dice, context=DuelContext(charging=('first',), active_participant='first'))
    result = resolve_round(fighter, fearsome, state, dice, choices)
    assert result.state.engaged is automatic and len(result.attacks) == (2 if automatic else 0)
    dice.finish(); choices.finish()


def test_sigmar_enlightened_is_offered_separately_and_not_granted_to_other_priests():
    from mordheim_construction.selection import available_special_rules
    profile = 'hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers'
    mark = profile + '.skill.enlightened'
    build = FighterBuild('mordheim', band_id='hirelings.hired-sword.2b', profile_id=profile, main_weapon_id='weapon.dagger')
    base = compile_fighter(build)
    assert 'mechanic.sigmar-enlightened' not in base.global_effects.tags
    assert mark in set(available_special_rules(build, None))
    catalogue = CombatCatalogue()
    choice = next(p for p in catalogue.profiles('mordheim', 'hirelings.hired-sword.2b') if p.profile_id == profile)
    option = next(s for s in catalogue.skills(choice) if s.rule_id == mark)
    assert option.runtime_available and option.unavailable_reason is None
    assert catalogue.skill_ui_ids(choice, (), (mark,)) == (option.id,)
    cultist = canonical('cult-of-the-possessed', 'brethren', 'weapon.mace')
    assert 'warband-group.chaotic' in cultist.global_effects.tags
    with pytest.raises(ValueError):
        canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.druid-priest-of-taal', 'weapon.dagger', special_rule_ids=(mark,))


@pytest.mark.parametrize('facts,band_tags,reroll', [
    ({'species': 'skaven'}, (), True),
    ({'creature_kind': 'undead'}, (), True),
    ({'creature_kind': 'possessed'}, (), True),
    ({'species': 'beastman'}, (), True),
    ({'elf_kind': 'dark'}, (), True),
    ({}, ('warband-group.evil',), True),
    ({}, ('warband-group.chaotic', 'warband-group.human'), True),
    ({}, ('warband-group.evil', 'warband-group.human-mercenary'), False),
    ({'species': 'orc'}, (), False),
    ({}, (), False),
])
def test_righteous_fury_shared_sisters_skill_filters_targets_and_first_round(facts, band_tags, reroll):
    fighter = canonical('sisters-of-sigmar', 'sigmarite-matriarch', 'weapon.mace',
        special_rule_ids=('band--special-skills-righteous-fury',))
    target = enemy(trait_overrides=facts)
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, *band_tags)))
    init = StrictDice([])
    own, other = initialize_fighter(fighter, init, 's'), initialize_fighter(target, init, 't')
    init.finish()
    for first in (True, False):
        rolls = [{'key': 'f.hit', 'value': 1}]
        if first and reroll: rolls.append({'key': 'f.hit.reroll', 'value': 1})
        tape = StrictDice(rolls)
        result = resolve_reference_attack(fighter, target, own, other, fighter.main_weapon,
            tape, key='f', first_round=first)
        tape.finish()
        assert not result.hit
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, target)


def test_native_aldred_completes_fellblade_and_its_orc_goblin_extension():
    fighter = canonical('hirelings.dramatis-personae.2b', 'hireling.dramatis.aldred-fellblade',
        'weapon.double-handed-weapon', armour_id='armour.heavy-armour',
        owned_item_ids=('two_handed_weapon', 'heavy_armour', 'shield'))
    assert fighter.main_weapon.parry and fighter.main_weapon.two_handed
    assert fighter.global_effects.strongman and fighter.characteristics.attacks == 2
    assert 'skill.righteous-fury' in fighter.global_effects.tags
    assert 'mechanic.hatred-orcs-goblins' in fighter.global_effects.tags
    assert 'skill.sigmar-s-sign' in fighter.global_effects.tags
    assert 'skill.combat-master' not in fighter.global_effects.tags
    assert strike(enemy(), fighter, [('hit', 4), ('parry', 5)]).parried
    from mordheim_combat.modular.contexts import _hit_reroll, _combined_effect
    for species in ('orc', 'goblin'):
        target = enemy(trait_overrides={'species': species})
        assert _hit_reroll(fighter, target, fighter.main_weapon,
            _combined_effect(fighter, fighter.main_weapon), True, False)
        assert not _hit_reroll(fighter, target, fighter.main_weapon,
            _combined_effect(fighter, fighter.main_weapon), False, False)
    init = StrictDice([])
    target = enemy()
    state = initialize_duel(fighter, target, init, context=DuelContext(charging=('first',), active_participant='first'))
    init.finish()
    # Two ordinary attacks, no multi-opponent Combat Master bonus.
    tape = StrictDice([{'key': key, 'value': 1} for key in (
        'round.0.first.attack.0.hit', 'round.0.first.attack.1.hit', 'round.0.second.attack.0.hit')])
    decisions = StrictDecisions([])
    result = resolve_round(fighter, target, state, tape, decisions)
    tape.finish(); decisions.finish()
    assert len(result.attacks) == 3
    ordinary = enemy(weapon='weapon.double-handed-weapon')
    assert not ordinary.main_weapon.parry
    empty = canonical('hirelings.dramatis-personae.2b', 'hireling.dramatis.aldred-fellblade',
        'weapon.fist', armour_id='armour.heavy-armour')
    assert not empty.main_weapon.parry


@pytest.mark.parametrize('drinking,ws,strength,own_attacks,own_hit,enemy_hit', [
    (2, 4, 3, 3, 3, 4), (3, 5, 4, 3, 3, 4),
    (4, 5, 4, 3, 4, 5), (5, 5, 5, 3, 3, 4), (6, 5, 4, 5, 3, 4),
])
def test_native_snorri_drinking_results_persist_in_both_player_turns(drinking, ws, strength, own_attacks, own_hit, enemy_hit):
    fighter = canonical('hirelings.dramatis-personae.2b', 'hireling.dramatis.snorri-nosebiter',
        'weapon.dwarf-axe', off_hand_id='weapon.mace', trait_overrides={'snorri_drunk_result': drinking})
    assert (fighter.characteristics.weapon_skill, fighter.characteristics.strength) == (ws, strength)
    assert fighter.global_effects.ward_save == 5
    assert 'mechanic.psychology-immunity' in fighter.global_effects.tags
    target = enemy()
    init = StrictDice([])
    state = initialize_duel(fighter, target, init,
        context=DuelContext(charging=('first',), active_participant='first'))
    init.finish()
    assert state.first.frenzy is (drinking == 6)
    for turn in (0, 1):
        keys = [f'round.{turn}.first.attack.{i}.hit' for i in range(own_attacks)]
        opposing = f'round.{turn}.second.attack.0.hit'
        keys = [*keys, opposing] if turn == 0 else [opposing, *keys]
        tape = StrictDice([{'key': key, 'value': 1} for key in keys])
        choices = StrictDecisions([{'key': f'round.{turn}.first.main-weapon-majority', 'value': True}])
        result = resolve_round(fighter, target, state, tape, choices)
        tape.finish(); choices.finish()
        expected = [own_hit] * own_attacks + [enemy_hit]
        if turn == 1: expected = [enemy_hit] + [own_hit] * own_attacks
        assert [attack.hit_target for attack in result.attacks] == expected
        assert not any(attack.hit for attack in result.attacks)
        state = result.state
    assert state.first.frenzy is (drinking == 6)
    with pytest.raises(ValueError, match='modular'):
        require_optimized_support(fighter, target)


def test_snorri_requires_a_participating_result_without_changing_other_profiles():
    profile = 'hireling.dramatis.snorri-nosebiter'
    for value in (None, 1, 0, 7, True, 2.0, '2'):
        traits = {} if value is None else {'snorri_drunk_result': value}
        with pytest.raises((ValueError, TypeError)):
            canonical('hirelings.dramatis-personae.2b', profile, 'weapon.dwarf-axe', trait_overrides=traits)
    with pytest.raises(ValueError, match='canonical drinking rule'):
        enemy(trait_overrides={'snorri_drunk_result': 3})
    with pytest.raises(ValueError):
        canonical('hirelings.dramatis-personae.2b', profile, 'weapon.dwarf-axe',
            armour_id='armour.light-armour', trait_overrides={'snorri_drunk_result': 3})
    # Ordinary psychology immunity still cancels generic Frenzy.
    ordinary = enemy(trait_overrides={'frenzy': True})
    ordinary = replace(ordinary, global_effects=replace(ordinary.global_effects,
        tags=(*ordinary.global_effects.tags, 'mechanic.psychology-immunity')))
    assert not initialize_fighter(ordinary, StrictDice([]), 'plain').frenzy


@pytest.mark.parametrize('band,profile,weapon,owned', [
    ('hirelings.hired-sword.2b', 'hireling.hired-sword.fire-eater', 'weapon.fist', ('fire_stick',)),
    ('hirelings.dramatis-personae.2b', 'hireling.dramatis.armen-abbas', 'weapon.sword',
     ('sword', 'angel_wings', 'stickfire', 'vermin_pot')),
])
def test_shooting_movement_and_postbattle_hireling_clauses_do_not_block_melee(band, profile, weapon, owned):
    fighter = canonical(band, profile, weapon, owned_item_ids=owned)
    target = enemy()
    init = StrictDice([])
    state = initialize_duel(fighter, target, init,
        context=DuelContext(charging=('first',), active_participant='first'))
    init.finish()
    # No breath attack, flight, physician or Rout dice enter this duel.
    tape = StrictDice([{'key': key, 'value': 1} for key in (
        'round.0.first.attack.0.hit', 'round.0.second.attack.0.hit')]); choices = StrictDecisions([])
    result = resolve_round(fighter, target, state, tape, choices)
    tape.finish(); choices.finish()
    assert len(result.attacks) == 2
    assert not any(tag in fighter.global_effects.tags for tag in ('skill.acrobat', 'skill.leap', 'skill.dodge'))


@pytest.mark.parametrize('item', ['holy_relic', 'holy_relic_pilgrim_only', 'arcane_candelabrum'])
def test_carried_relic_passes_only_first_required_leadership_test(item):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    fighter = enemy(owned_item_ids=(item, item))
    foe = enemy()
    state = initialize_duel(fighter, foe, StrictDice([]), context=DuelContext(charging=('first',), active_participant='first'))
    dice = StrictDice([{'key': 'later.0', 'value': 6}, {'key': 'later.1', 'value': 6}])
    decisions = StrictDecisions([])
    passed, current = resolve_local_leadership(fighter, state, dice, decisions, 'first', first=True, return_state=True)
    assert passed and current.resources_spent == frozenset({'leadership.holy-relic'})
    passed, current = resolve_local_leadership(fighter, replace(state, first=current), dice, decisions, 'later', first=True, return_state=True)
    assert not passed and current.resources_spent == frozenset({'leadership.holy-relic'})
    dice.finish(); decisions.finish()
    with pytest.raises(ValueError, match='returned fighter state'):
        resolve_local_leadership(fighter, state, StrictDice([]), StrictDecisions([]), 'unsafe', first=True)
    with pytest.raises(ValueError):
        require_optimized_support(fighter, foe)


def test_arcane_candelabrum_keeps_brazier_attack_but_uses_one_hand():
    fighter = enemy(weapon='weapon.arcane-candelabrum', off_hand_id='weapon.sword')
    assert not fighter.main_weapon.two_handed
    assert fighter.main_weapon.strength_bonus == 1
    assert fighter.main_weapon.ignition_threshold == 5
    assert 'attack.fire' in fighter.main_weapon.tags
    assert 'defence.holy-relic' in fighter.global_effects.tags
    assert fighter.off_hand is not None
    # Reuse the brazier ignition sequence on a real hit.
    outcome = strike(fighter, enemy(), [('hit', 4), ('ignition', 5), ('wound', 1)])
    assert outcome.hit and not outcome.wounded


@pytest.mark.parametrize('skills', [
    ('sign-of-sigmar', 'righteous-fury'), ('sign-of-sigmar', 'absolute-faith'),
    ('sign-of-sigmar', 'protection-of-sigmar'), ('righteous-fury', 'absolute-faith'),
    ('righteous-fury', 'protection-of-sigmar'), ('absolute-faith', 'protection-of-sigmar'),
])
def test_native_sister_chooses_two_source_skills_and_completes_a_duel_round(skills):
    fighter = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.sister-of-sigmar',
        'weapon.arcane-candelabrum', off_hand_id='weapon.sigmarite-hammer', armour_id='armour.light-armour',
        special_rule_ids=tuple('band--special-skills-' + skill for skill in skills))
    expected = {'sign-of-sigmar': 'skill.sigmar-s-sign', 'righteous-fury': 'skill.righteous-fury',
                'absolute-faith': 'mechanic.fear-reroll'}
    for skill, tag in expected.items():
        assert (tag in fighter.global_effects.tags) is (skill in skills)
    assert 'defence.holy-relic' in fighter.global_effects.tags
    target = enemy()
    init = StrictDice([])
    state = initialize_duel(fighter, target, init, context=DuelContext(charging=('first',), active_participant='first'))
    init.finish()
    tape = StrictDice([{'key': key, 'value': 1} for key in (
        'round.0.first.attack.0.hit', 'round.0.first.attack.1.hit', 'round.0.second.attack.0.hit')])
    decisions = StrictDecisions([])
    result = resolve_round(fighter, target, state, tape, decisions)
    tape.finish(); decisions.finish()
    assert len(result.attacks) == 3


def test_native_sister_requires_two_distinct_skills_without_matriarch_access():
    from mordheim_construction.selection import available_special_rules
    build = FighterBuild('mordheim', band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.sister-of-sigmar', main_weapon_id='weapon.sigmarite-hammer')
    choices = available_special_rules(build, None)
    assert set(choices) == {'band--special-skills-' + suffix for suffix in (
        'sign-of-sigmar', 'protection-of-sigmar', 'righteous-fury', 'absolute-faith')}
    sign, fury, faith = ('band--special-skills-' + suffix for suffix in ('sign-of-sigmar', 'righteous-fury', 'absolute-faith'))
    for selected in ((), (sign,), (sign, sign), (sign, fury, faith)):
        with pytest.raises(ValueError, match='exactly two distinct'):
            compile_fighter(replace(build, special_rule_ids=selected))
    with pytest.raises(ValueError, match='not available'):
        compile_fighter(replace(build, special_rule_ids=(sign, 'band--special-skills-utter-determination')))


@pytest.mark.parametrize('nature,expected_ws', [('living', 2), ('daemon', 3), ('undead', 3)])
def test_shallya_aura_affects_both_contacting_duelists_except_daemons_and_undead(nature, expected_ws):
    from mordheim_combat.modular.contexts import prepare_hit_context
    priest = canonical('hirelings.hired-sword.2b', 'hireling.hired-sword.priestess-of-shallya',
        'weapon.quarter-staff', special_rule_ids=(
            'hireling.hired-sword.priestess-of-shallya.skill.tranquil-aura',))
    target = enemy(trait_overrides={'creature_kind': nature})
    init = StrictDice([])
    state = initialize_duel(priest, target, init,
        context=DuelContext(charging=('second',), active_participant='second'))
    init.finish()
    context = prepare_hit_context(priest, target, state.first, state.second,
        priest.main_weapon, priest.main_weapon)
    assert (context.attacker_ws, context.defender_ws) == (1, expected_ws)
    for index in range(2):
        # Staff gives I+1; round zero's charging opponent strikes first.
        order = ('second', 'first') if index == 0 else ('first', 'second')
        tape = StrictDice([{'key': f'round.{index}.{side}.attack.0.hit', 'value': 1} for side in order])
        decisions = StrictDecisions([])
        result = resolve_round(priest, target, state, tape, decisions)
        tape.finish(); decisions.finish()
        assert (result.state.first.weapon_skill, result.state.second.weapon_skill) == (2, 3)
        state = result.state
    weak = replace(target, characteristics=replace(target.characteristics, weapon_skill=1),
        global_effects=replace(target.global_effects, tags=()))
    weak_state = initialize_fighter(weak, StrictDice([]), 'weak')
    context = prepare_hit_context(priest, weak, state.first, weak_state, priest.main_weapon, priest.main_weapon)
    assert context.defender_ws == 0
    assert phases.resolve_hit(context, StrictDice([])).success


def test_shallya_strictures_only_choose_legal_initial_chargers_and_recognize_onogal():
    priest = enemy(skill_ids=('mechanic.shallya-strictures',))
    ordinary = enemy(trait_overrides={'chaos_follower': True})
    state = initialize_duel(priest, ordinary, StrictDice([]))
    assert state.initial_charge_flags == (False, True) and not state.first_player_turn
    state = initialize_duel(ordinary, priest, StrictDice([]))
    assert state.initial_charge_flags == (True, False) and state.first_player_turn
    with pytest.raises(ValueError, match='Shallyan Strictures'):
        initialize_duel(priest, ordinary, StrictDice([]),
            context=DuelContext(charging=('first',), active_participant='first'))
    carnival = replace(ordinary, global_effects=replace(ordinary.global_effects, tags=('band.carnival-of-chaos',)))
    for target in (carnival, enemy(trait_overrides={'onogal_follower': True}),
                   enemy(trait_overrides={'mark_of_onogal_the_crow': True})):
        assert initialize_duel(priest, target, StrictDice([]), context=DuelContext(
            charging=('first',), active_participant='first')).initial_charge_flags == (True, False)
    tape = StrictDice([{'key': 'duel.charge', 'value': 1}])
    state = initialize_duel(priest, priest, tape)
    tape.finish()
    assert state.initial_charge_flags == (False, False) and state.engaged


def test_shallya_shared_binding_keeps_ceremonial_dagger_owned_but_not_active():
    from mordheim_construction.combat_packages import combat_packages
    from mordheim_construction.restrictions import _validate_bound_equipment_restrictions
    from mordheim_knowledge.loader import runtime_bindings
    pack = next(p for p in combat_packages('mordheim') if p.band['id'] == 'hirelings.hired-sword.2b')
    profile = next(p for p in pack.profiles if p['id'] == 'hireling.hired-sword.priestess-of-shallya')
    rule = next(r for r in pack.special_rules if r['id'] == profile['id'] + '.rule.strictures')
    bindings = runtime_bindings(rule, 'profile')
    build = FighterBuild('mordheim', band_id=pack.band['id'], profile_id=profile['id'],
        main_weapon_id='weapon.quarter-staff', owned_item_ids=('dagger', 'staff'))
    _validate_bound_equipment_restrictions(build, build.main_weapon_id, bindings, package=pack, profile=profile)
    for invalid in (replace(build, main_weapon_id='weapon.dagger'), replace(build, armour_id='armour.light-armour')):
        with pytest.raises(ValueError):
            _validate_bound_equipment_restrictions(invalid, invalid.main_weapon_id, bindings, package=pack, profile=profile)


def test_son_of_ulric_removes_the_native_unarmed_penalties():
    base = canonical('hirelings.hired-sword.2b',
        'hireling.hired-sword.wolf-priest-of-ulric-miracle-workers', 'weapon.fist')
    marked = canonical('hirelings.hired-sword.2b',
        'hireling.hired-sword.wolf-priest-of-ulric-miracle-workers', 'weapon.fist',
        special_rule_ids=('hireling.hired-sword.wolf-priest-of-ulric-miracle-workers.skill.son-of-ulric',))
    target = enemy(armour='armour.heavy-armour')
    assert strike(base, target, [('hit', 4), ('wound', 5), ('armour', 4)]).saved
    outcome = strike(marked, target, [('hit', 4), ('wound', 5), ('armour', 4)])
    assert outcome.wounded and not outcome.saved


@pytest.mark.parametrize('band,profile,origin,expected', [
    ('witch-hunters', 'witch-hunters', None, 5),
    ('sisters-of-sigmar', 'sigmarite-sister', None, 5),
    ('mercenaries', 'warriors', 'reikland', 5),
    ('mercenaries', 'warriors', 'marienburg', 4),
    ('mercenaries', 'warriors', 'middenheim', 4),
    ('averlanders', 'marksmen', None, 5),
])
def test_symbol_of_unity_qualifies_the_opposing_warband(band, profile, origin, expected):
    priest = canonical('hirelings.hired-sword.2b',
        'hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers', 'weapon.dagger',
        special_rule_ids=('hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers.skill.symbol-of-unity',))
    target = canonical(band, profile, 'weapon.mace',
        trait_overrides={} if origin is None else {'mercenary_origin': origin})
    assert strike(target, priest, [('hit', 1)]).hit_target == expected
    if band == 'mercenaries':
        unknown = canonical(band, profile, 'weapon.mace')
        with pytest.raises(ValueError, match='explicit origin'):
            strike(unknown, priest, [])


@pytest.mark.parametrize('house,own_profile,target_profile,first_round,reroll', [
    ('fierezza', 'commander', 'mercenary-captain', True, True),
    ('fierezza', 'commander', 'warriors', True, False),
    ('halcon', 'commander', 'mercenary-captain', True, False),
    ('fierezza', 'pikemen', 'mercenary-captain', True, False),
    ('fierezza', 'commander', 'mercenary-captain', False, False),
])
def test_house_guard_pride_requires_fierezza_heroes_on_both_sides(house, own_profile, target_profile, first_round, reroll):
    fighter = canonical('house-guard-sc', own_profile, 'weapon.mace',
        trait_overrides={'house_guard_house': house})
    target = canonical('mercenaries', target_profile, 'weapon.mace')
    a, d = initialize_fighter(fighter, StrictDice([]), 'a'), initialize_fighter(target, StrictDice([]), 'd')
    tape = StrictDice([{'key': 'x.hit', 'value': 1}] +
        ([{'key': 'x.hit.reroll', 'value': 1}] if reroll else []))
    result = resolve_reference_attack(fighter, target, a, d, fighter.main_weapon, tape,
        key='x', first_round=first_round)
    tape.finish()
    assert not result.hit
    if reroll:
        unknown_house = canonical('house-guard-sc', own_profile, 'weapon.mace')
        with pytest.raises(ValueError, match='explicit House Guard house'):
            resolve_reference_attack(unknown_house, target, a, d, unknown_house.main_weapon,
                StrictDice([]), key="x", first_round=True)
        with pytest.raises(ValueError, match='explicit fighter role'):
            resolve_reference_attack(fighter, enemy(), a, d, fighter.main_weapon,
                StrictDice([]), key="x", first_round=True)


def test_pikewall_uses_incoming_charge_and_the_active_first_strike_weapon():
    for weapon, charger, reroll in [('weapon.pike', 'second', True),
                                   ('weapon.mace', 'second', False),
                                   ('weapon.pike', 'first', False)]:
        fighter = canonical('house-guard-sc', 'pikemen', weapon,
            trait_overrides={'house_guard_house': 'fierezza'})
        target = enemy()
        target = replace(target, characteristics=replace(target.characteristics, initiative=2))
        state = initialize_duel(fighter, target, StrictDice([]),
            context=DuelContext(charging=(charger,), active_participant=charger))
        for index in range(2):
            order = ('second', 'first') if index == 0 and charger == 'second' and weapon == 'weapon.mace' else ('first', 'second')
            rolls = []
            for side in order:
                rolls.append({'key': f'round.{index}.{side}.attack.0.hit', 'value': 1})
                if side == 'first' and index == 0 and reroll:
                    rolls.append({'key': f'round.{index}.{side}.attack.0.hit.reroll', 'value': 1})
            tape, decisions = StrictDice(rolls), StrictDecisions([])
            result = resolve_round(fighter, target, state, tape, decisions)
            tape.finish(); decisions.finish()
            assert len(result.attacks) == 2
            state = result.state


@pytest.mark.parametrize('kind,handler,passes', [('ordinary', None, False),
    ('handled', 3, False), ('handled', 9, True), ('large-predator', 3, False)])
def test_tranquil_fauna_uses_handler_leadership_without_cancelling_charge(kind, handler, passes):
    pid = 'hireling.hired-sword.druid-priest-of-taal'
    priest = canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger',
        special_rule_ids=(pid + '.skill.tranquil-fauna',))
    facts = {'fauna_animal_kind': kind}
    if handler is not None:
        facts['animal_handler_leadership'] = handler
    animal = enemy(trait_overrides=facts)
    animal = replace(animal, characteristics=replace(animal.characteristics, initiative=2, leadership=10))
    state = initialize_duel(priest, animal, StrictDice([]), context=DuelContext(
        charging=('second',), active_participant='second'))
    rolls = [] if kind == 'ordinary' else [
        {'key': 'round.0.second.tranquil-fauna.0', 'value': 3},
        {'key': 'round.0.second.tranquil-fauna.1', 'value': 3}]
    if passes:
        rolls.append({'key': 'round.0.second.attack.0.hit', 'value': 1})
    rolls.append({'key': 'round.0.first.attack.0.hit', 'value': 1})
    tape, decisions = StrictDice(rolls), StrictDecisions([])
    result = resolve_round(priest, animal, state, tape, decisions)
    tape.finish(); decisions.finish()
    assert result.state.engaged and result.state.initial_charge_flags == (False, True)
    assert len(result.attacks) == (2 if passes else 1)
    assert result.state.second.charm_attack_blocked is not passes
    # The decision resets: a new combat phase permits a fresh handler test.
    if kind == 'handled' and not passes:
        animal = replace(animal, animal_handler_leadership=9)
        tape = StrictDice([
            {'key': 'round.1.second.tranquil-fauna.0', 'value': 3},
            {'key': 'round.1.second.tranquil-fauna.1', 'value': 3},
            {'key': 'round.1.first.attack.0.hit', 'value': 1},
            {'key': 'round.1.second.attack.0.hit', 'value': 1}])
        decisions = StrictDecisions([])
        again = resolve_round(priest, animal, result.state, tape, decisions)
        tape.finish(); decisions.finish()
        assert len(again.attacks) == 2 and not again.state.second.charm_attack_blocked


def test_tranquil_fauna_does_not_guess_animal_or_handler_facts():
    pid = 'hireling.hired-sword.druid-priest-of-taal'
    priest = canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger',
        special_rule_ids=(pid + '.skill.tranquil-fauna',))
    for facts, message in [({'species': 'animal'}, 'qualification'),
                           ({'fauna_animal_kind': 'handled'}, 'Handler')]:
        # Animal identity is already an established compiled fact; no broad species enum extension.
        if 'species' in facts:
            animal = enemy()
            animal = replace(animal, global_effects=replace(animal.global_effects, tags=('species.animal',)))
        else:
            animal = enemy(trait_overrides=facts)
        state = initialize_duel(priest, animal, StrictDice([]), context=DuelContext(
            charging=('second',), active_participant='second'))
        with pytest.raises(ValueError, match=message):
            resolve_round(priest, animal, state, StrictDice([]), StrictDecisions([]))


@pytest.mark.parametrize('count', [1, 2])
def test_native_eagle_friend_has_separate_first_strike_strength_three_attacks(count):
    pid = 'hireling.hired-sword.war-priestess-of-myrmidia'
    fighter = canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger',
        characteristics=Characteristics(3, 5, 3, 1, 4, 1, leadership=8),
        special_rule_ids=(pid + '.skill.eagle-friend',),
        trait_overrides={'eagle_friends': count, 'frenzy': True})
    target = enemy()
    target = replace(target, characteristics=replace(target.characteristics, toughness=4))
    state = initialize_duel(fighter, target, StrictDice([]), context=DuelContext(
        charging=('second',), active_participant='second'))
    rolls = []
    # Higher I breaks the shared Strike First tier before the charging foe.
    for bird in reversed(range(count)):
        rolls.append({'key': f'round.0.first.eagle.{bird}.attack.0.hit', 'value': 4})
        rolls.append({'key': f'round.0.first.eagle.{bird}.attack.0.wound', 'value': 4})
    rolls += [{'key': 'round.0.second.attack.0.hit', 'value': 1},
              {'key': 'round.0.first.attack.0.hit', 'value': 1},
              {'key': 'round.0.first.attack.1.hit', 'value': 1}]
    tape, decisions = StrictDice(rolls), StrictDecisions([])
    result = resolve_round(fighter, target, state, tape, decisions)
    tape.finish(); decisions.finish()
    assert len(result.attacks) == count + 3
    assert all(attack.hit and not attack.wounded for attack in result.attacks[:count])
    assert len(fighter.extra_attacks) == count  # Frenzy doubles her A, never her birds.
    assert result.state.second.wounds == target.characteristics.wounds
    with pytest.raises(ValueError, match='requires Eagle Friend'):
        canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger', trait_overrides={'eagle_friends': count})


def test_eagle_friend_disappears_with_the_owner_and_respects_tranquil_fauna():
    pid = 'hireling.hired-sword.war-priestess-of-myrmidia'
    fighter = canonical('hirelings.hired-sword.2b', pid, 'weapon.dagger',
        special_rule_ids=(pid + '.skill.eagle-friend',))
    taal_id = 'hireling.hired-sword.druid-priest-of-taal'
    target = canonical('hirelings.hired-sword.2b', taal_id, 'weapon.dagger',
        special_rule_ids=(taal_id + '.skill.tranquil-fauna',))
    state = initialize_duel(fighter, target, StrictDice([]), context=DuelContext(
        charging=('second',), active_participant='second'))
    tape = StrictDice([{'key': 'round.0.second.attack.0.hit', 'value': 1},
                       {'key': 'round.0.first.attack.0.hit', 'value': 1}])
    decisions = StrictDecisions([])
    result = resolve_round(fighter, target, state, tape, decisions)
    tape.finish(); decisions.finish()
    assert len(result.attacks) == 2  # Fauna calms the eagle, not its human owner.
    out = replace(state, first=replace(state.first, condition=Condition.OUT))
    tape, decisions = StrictDice([]), StrictDecisions([])
    result = resolve_round(fighter, target, out, tape, decisions)
    tape.finish(); decisions.finish()
    assert not result.attacks


def test_snerik_keeps_his_source_only_cloak_without_a_fake_duel_effect():
    pid = 'hireling.dramatis.snerik-night-goblin-scout'
    cloak = pid + '.item.camouflage-cloak'
    build = FighterBuild('mordheim', band_id='hirelings.dramatis-personae.2b', profile_id=pid,
        main_weapon_id='weapon.sword', off_hand_id='weapon.dagger',
        owned_item_ids=('dagger', 'sword', 'short_bow', cloak))
    fighter = compile_fighter(build)
    with pytest.raises(ValueError, match='complete legal printed kit'):
        compile_fighter(replace(build, owned_item_ids=('dagger', 'sword', 'short_bow')))
    state = initialize_duel(fighter, enemy(), StrictDice([]), context=DuelContext(
        charging=('second',), active_participant='second'))
    tape = StrictDice([{'key': key, 'value': 1} for key in (
        'round.0.second.attack.0.hit', 'round.0.first.attack.0.hit', 'round.0.first.attack.1.hit')])
    decisions = StrictDecisions([])
    result = resolve_round(fighter, enemy(), state, tape, decisions)
    tape.finish(); decisions.finish()
    assert len(result.attacks) == 3
    assert not any('camouflage' in tag for tag in fighter.global_effects.tags)


@pytest.mark.parametrize('vision,nominated', [(value, True) for value in range(1, 7)] + [(6, False)])
def test_guiding_dream_rolls_once_and_applies_only_to_the_nominated_hero(vision, nominated):
    fighter = canonical('dreamwalkers-cult-of-morr-fbg', 'dreamer', 'weapon.sword',
        trait_overrides={'guiding_dream_target': nominated})
    foe = enemy(trait_overrides={'fighter_kind': 'hero'})
    bonus_hit = nominated and vision in (2, 3)
    count = 2 if nominated and vision == 6 else 1
    tape = [{'key': 'first.guiding-dream', 'value': vision}]
    # Baseline WS4 vs WS3 needs 3: vision lowers it to 2, so a 2 distinguishes it.
    for index in range(count):
        tape.append({'key': f'round.0.first.attack.{index}.hit', 'value': 2 if bonus_hit else 1})
        if bonus_hit:
            tape.append({'key': f'round.0.first.attack.{index}.wound', 'value': 1})
    tape.append({'key': 'round.0.second.attack.0.hit', 'value': 1})
    dice = StrictDice(tape)
    state = initialize_duel(fighter, foe, dice,
        context=DuelContext(charging=('first',), active_participant='first'))
    assert state.first.guiding_dream_result == vision
    assert state.first.strength == 3 + int(nominated and vision in (4, 5))
    assert state.first.frenzy == (nominated and vision == 6)
    result = resolve_round(fighter, foe, state, dice, StrictDecisions([]))
    assert len(result.attacks) == count + 1
    assert result.attacks[0].hit == bonus_hit
    assert result.state.first.guiding_dream_result == vision
    dice.finish()
    # A second combat phase must neither reroll the dream nor stack its Strength.
    second_tape = StrictDice([{'key': f'round.1.{label}.attack.{index}.hit', 'value': 1}
        for label, size in [('first', count), ('second', 1)] for index in range(size)])
    continued = resolve_round(fighter, foe, result.state, second_tape, StrictDecisions([]))
    second_tape.finish()
    assert continued.state.first.strength == state.first.strength


def test_guiding_dream_refuses_a_nominated_nonhero_and_foreign_mark():
    fighter = canonical('dreamwalkers-cult-of-morr-fbg', 'dreamer',
        trait_overrides={'guiding_dream_target': True})
    dice = StrictDice([])
    with pytest.raises(ValueError, match='opposing model to be a Hero'):
        initialize_duel(fighter, enemy(trait_overrides={'fighter_kind': 'henchman'}), dice)
    dice.finish()
    with pytest.raises(ValueError, match='requires Guiding Dream'):
        enemy(trait_overrides={'guiding_dream_target': True})


def test_strigoi_iron_sinews_is_optional_and_changes_real_wounding_once():
    band = 'survivors-of-strigos-sylv'
    base = canonical(band, 'strigoi-vampire', 'weapon.fist')
    fighter = canonical(band, 'strigoi-vampire', 'weapon.fist',
        special_rule_ids=('strigoi-vampire--iron-sinews',))
    assert base.characteristics.strength == 4
    assert fighter.characteristics.strength == 5
    # S5 vs T4 wounds on 3; S4 does not. A two-wound target avoids injury dice.
    foe = replace(enemy(), characteristics=Characteristics(3, 3, 4, 2, 3, 1, leadership=7))
    for attacker, expected in [(base, False), (fighter, True)]:
        init = StrictDice([])
        own = initialize_fighter(attacker, init, 'owner')
        target = initialize_fighter(foe, init, 'target'); init.finish()
        dice = StrictDice([{'key': 'strength.hit', 'value': 4}, {'key': 'strength.wound', 'value': 3}])
        outcome = resolve_reference_attack(attacker, foe, own, target, attacker.main_weapon,
            dice, key='strength', first_round=False)
        dice.finish()
        assert outcome.wounded == expected
    with pytest.raises(ValueError, match='not available'):
        canonical(band, 'seer', special_rule_ids=('strigoi-vampire--iron-sinews',))


@pytest.mark.parametrize('bloodline,first_round,frenzy,rerolled', [
    ('blood-dragon', True, False, True), ('strigoi', True, False, False),
    ('necrarch', False, False, False), ('lahmian', True, True, False),
])
def test_strigoi_kindred_hatred_checks_bloodline_and_preserves_frenzy_and_timing(bloodline, first_round, frenzy, rerolled):
    fighter = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist')
    foe = enemy(trait_overrides={'vampire': True, 'vampire_bloodline': bloodline})
    init = StrictDice([])
    own = replace(initialize_fighter(fighter, init, 'owner'), frenzy=frenzy)
    target = initialize_fighter(foe, init, 'target'); init.finish()
    tape = [{'key': 'kindred.hit', 'value': 1}]
    if rerolled: tape += [{'key': 'kindred.hit.reroll', 'value': 4}, {'key': 'kindred.wound', 'value': 1}]
    dice = StrictDice(tape)
    outcome = resolve_reference_attack(fighter, foe, own, target, fighter.main_weapon,
        dice, key='kindred', first_round=first_round)
    dice.finish()
    assert outcome.hit == rerolled
    # A fresh source compilation is never modified by a duel or selected Strength skill.
    assert fighter.characteristics.strength == 4


def test_kindred_hatred_requires_bloodline_only_for_vampire_opponents():
    fighter = canonical('survivors-of-strigos-sylv', 'strigoi-vampire', 'weapon.fist')
    init = StrictDice([]); own = initialize_fighter(fighter, init, 'owner')
    unknown = enemy(trait_overrides={'vampire': True})
    target = initialize_fighter(unknown, init, 'target'); init.finish()
    dice = StrictDice([])
    with pytest.raises(ValueError, match='explicit bloodline'):
        resolve_reference_attack(fighter, unknown, own, target, fighter.main_weapon,
            dice, key='unknown', first_round=True)
    dice.finish()
    ordinary = enemy(); init = StrictDice([])
    target = initialize_fighter(ordinary, init, 'target'); init.finish()
    dice = StrictDice([{'key': 'ordinary.hit', 'value': 1}])
    assert not resolve_reference_attack(fighter, ordinary, own, target, fighter.main_weapon,
        dice, key='ordinary', first_round=True).hit
    dice.finish()
    with pytest.raises(ValueError, match='conflicts with the canonical profile'):
        canonical('blood-dragons-mou', 'vampire', trait_overrides={'vampire_bloodline': 'strigoi'})


@pytest.mark.parametrize('profile', ['rememberer', 'stubbles', 'axe-hurlers'])
def test_non_slayer_hatred_grant_is_recipient_specific_and_lost_with_psychology_immunity(profile):
    fighter = canonical('dwarf-slayer-cult-web', profile, 'weapon.axe')
    assert 'mechanic.hatred-orcs-goblins' in fighter.global_effects.tags
    foe = enemy(trait_overrides={'species': 'orc'})
    for immune in (False, True):
        actor = replace(fighter, global_effects=replace(fighter.global_effects,
            tags=(*fighter.global_effects.tags, 'mechanic.psychology-immunity'))) if immune else fighter
        init = StrictDice([]); own = initialize_fighter(actor, init, 'owner')
        target = initialize_fighter(foe, init, 'target'); init.finish()
        tape = [{'key': 'slayer.hit', 'value': 1}]
        if not immune: tape += [{'key': 'slayer.hit.reroll', 'value': 4}, {'key': 'slayer.wound', 'value': 1}]
        dice = StrictDice(tape)
        outcome = resolve_reference_attack(actor, foe, own, target, actor.main_weapon,
            dice, key='slayer', first_round=True)
        dice.finish(); assert outcome.hit == (not immune)
    for excluded in ('giant-slayer', 'doomseeker', 'troll-slayers'):
        assert 'mechanic.hatred-orcs-goblins' not in canonical('dwarf-slayer-cult-web', excluded, 'weapon.axe').global_effects.tags


@pytest.mark.parametrize('condition_id,tag', [
    ('campaign.condition.immune-to-fear', 'mechanic.fear-immunity'),
    ('condition.immune-to-psychology', 'mechanic.psychology-immunity'),
])
def test_supplied_immunity_condition_consumes_no_fear_test_dice(condition_id, tag):
    """The two immunities are distinct operators, and neither requests a test."""
    protected = enemy(condition_ids=(condition_id,))
    assert tag in protected.global_effects.tags
    assert 'mechanic.psychology-immunity' not in protected.global_effects.tags or tag.endswith('psychology-immunity')
    # No Fear-test tape: StrictDice fails the run if any test die is requested.
    result = fear_round(protected, [('round.0.first.attack.0.hit', 1),
                                    ('round.0.first.attack.1.hit', 1),
                                    ('round.0.second.attack.0.hit', 1)])
    assert result.state.engaged and not result.state.second.fear_hit_sixes


def test_fear_immunity_is_not_psychology_immunity_in_the_real_stupidity_test():
    from mordheim_combat.modular.psychology import resolve_stupidity
    foe = enemy()
    # Fear immunity alone does not cancel an acquired Stupidity test.
    fear_only = enemy(condition_ids=('campaign.condition.stupidity', 'campaign.condition.immune-to-fear'))
    dice = StrictDice([{'key': 'round.0.first.stupidity.0', 'value': 6},
                       {'key': 'round.0.first.stupidity.1', 'value': 6}])
    state = initialize_duel(fear_only, foe, dice, context=DuelContext(charging=(), active_participant='first'))
    state = resolve_stupidity(fear_only, foe, state, dice, StrictDecisions([]))
    dice.finish()
    assert state.first.stupidity_failed
    # Psychology immunity cancels the same test without consuming dice.
    immune = enemy(condition_ids=('campaign.condition.stupidity', 'condition.immune-to-psychology'))
    dice = StrictDice([])
    state = initialize_duel(immune, foe, dice, context=DuelContext(charging=(), active_participant='first'))
    state = resolve_stupidity(immune, foe, state, dice, StrictDecisions([]))
    dice.finish()
    assert not state.first.stupidity_failed


@pytest.mark.parametrize('first_round', [True, False])
def test_supplied_hatred_condition_tests_any_enemy_in_the_first_round_only(first_round):
    from mordheim_combat.modular.contexts import _hit_reroll
    warrior = enemy(condition_ids=('condition.hatred',))
    assert 'skill.hatred' in warrior.global_effects.tags
    foe = enemy()
    init = StrictDice([])
    a, d = initialize_fighter(warrior, init, 'a'), initialize_fighter(foe, init, 'd')
    init.finish()
    tape = [('x.hit', 1)] + ([('x.hit.reroll', 1)] if first_round else [])
    dice = StrictDice([{'key': key, 'value': value} for key, value in tape])
    result = resolve_reference_attack(warrior, foe, a, d, warrior.main_weapon,
                                     dice, key='x', first_round=first_round)
    dice.finish()
    assert not result.hit
    assert _hit_reroll(warrior, foe, warrior.main_weapon, warrior.global_effects,
                       first_round, False) is first_round
    # Psychology immunity keeps cancelling Hatred, exactly as the operator reads.
    immune = enemy(condition_ids=('condition.hatred', 'condition.immune-to-psychology'))
    assert _hit_reroll(immune, foe, immune.main_weapon, immune.global_effects, True, False) is False
