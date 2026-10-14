"""Source discriminators for the residual individual lifecycle contracts."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.phases import Condition
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild, LocalParticipant


def bare(*tags, attacks=1, initiative=3, strength=3, condition_ids=()):
    fighter = compile_fighter(FighterBuild('mordheim',
        Characteristics(3, strength, 3, 2, initiative, attacks, leadership=7),
        main_weapon_id='weapon.mace',condition_ids=condition_ids))
    return replace(fighter, global_effects=replace(fighter.global_effects,
        tags=(*fighter.global_effects.tags, *tags)))


def start(first, second, *, charging=('first',), contacts=None):
    return initialize_duel(first, second, StrictDice([]), context=DuelContext(
        charging=charging, active_participant='first', contacts=contacts))


def run(first, second, state, rolls=(), choices=()):
    dice = StrictDice([{'key': entry[0], 'value': entry[1], 'sides': entry[2] if len(entry) == 3 else 6}
                      for entry in rolls])
    decisions = StrictDecisions([{'key': key, 'value': value} for key, value in choices])
    result = resolve_round(first, second, state, dice, decisions)
    dice.finish(); decisions.finish()
    return result


@pytest.mark.parametrize('band,collection', [('pirates', 'mordheim'), ('lustria-pirates', 'trollheim')])
def test_shanty_canonical_loss_of_only_attack_and_declining(band, collection):
    singer = compile_fighter(FighterBuild('mordheim', band_id=band,
        profile_id='ships-mates', collection=collection, main_weapon_id='weapon.mace',
        special_rule_ids=('band--pirate-special-skills-sea-shanty-singer',)))
    enemy = bare()
    result = run(singer, enemy, start(singer, enemy),
        [('round.0.first.sea-shanty.leadership.0', 6),
         ('round.0.first.sea-shanty.leadership.1', 6), ('round.0.first.attack.0.hit', 1)],
        [('round.0.first.sea-shanty', True)])
    assert len(result.attacks) == 1
    # A new combat phase offers the optional song again; declining restores the attack.
    result = run(singer, enemy, result.state,
        [('round.1.priority-tie', 1), ('round.1.second.attack.0.hit', 1), ('round.1.first.attack.0.hit', 1)],
        [('round.1.first.sea-shanty', False)] if collection == 'trollheim' else ())
    assert len(result.attacks) == 2


@pytest.mark.parametrize('tag,immune', [('mechanic.sea-shanty', 'nature.undead'),
    ('mechanic.sea-shanty', 'nature.possessed'),
    ('mechanic.sea-shanty-psychology', 'mechanic.psychology-immunity')])
def test_shanty_printed_exclusions_neither_offer_nor_test(tag, immune):
    singer, enemy = bare(tag), bare(immune)
    run(singer, enemy, start(singer, enemy),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])


def test_mordheim_song_does_not_invent_lustria_psychology_exclusion():
    singer, enemy = bare('mechanic.sea-shanty'), bare('mechanic.psychology-immunity')
    result = run(singer, enemy, start(singer, enemy),
        [('round.0.first.sea-shanty.leadership.0', 6), ('round.0.first.sea-shanty.leadership.1', 6),
         ('round.0.first.attack.0.hit', 1)], [('round.0.first.sea-shanty', True)])
    assert len(result.attacks) == 1


def test_ogre_belch_penalty_expires_but_engagement_resource_persists():
    ogre, enemy = bare('mechanic.crude-belch-ogre'), bare()
    result = run(ogre, enemy, start(ogre, enemy),
        [('round.0.first.crude-belch-ogre.leadership.0', 6),
         ('round.0.first.crude-belch-ogre.leadership.1', 6),
         ('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)],
        [('round.0.first.crude-belch-ogre', True)])
    assert result.attacks[1].hit_target == 5
    assert 'crude-belch-ogre' in result.state.first.resources_spent
    result = run(ogre, enemy, result.state,
        [('round.1.priority-tie', 1), ('round.1.second.attack.0.hit', 1), ('round.1.first.attack.0.hit', 1)])
    assert result.attacks[0].hit_target == 4


@pytest.mark.parametrize('gate', ['mechanic.slaanesh-charge-test', 'mechanic.opposite-sex-charge-test'])
def test_charge_gate_cancels_failed_charge_and_no_blows(gate):
    bearer, enemy = bare(gate, 'sex.male'), bare('sex.female')
    key = 'slaanesh-charge' if gate.endswith('slaanesh-charge-test') else 'charismatic-charge'
    result = run(enemy, bearer, start(enemy, bearer),
        [(f'round.0.first.{key}.0', 6), (f'round.0.first.{key}.1', 6)])
    assert not result.state.engaged and result.state.failed_charges == {'first'}
    assert result.attacks == ()


def test_cannot_charge_preserves_defensive_melee():
    restricted, enemy = bare('mechanic.cannot-charge'), bare()
    with pytest.raises(ValueError, match='Cannot Charge'):
        start(restricted, enemy)
    run(enemy, restricted, start(enemy, restricted),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])


def test_feral_test_own_turn_only_records_failure_without_movement():
    beast, enemy = bare('mechanic.feral-instinct'), bare()
    result = run(beast, enemy, start(beast, enemy),
        [('round.0.first.feral-instinct.0', 6), ('round.0.first.feral-instinct.1', 6),
         ('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])
    assert result.state.first.feral_instinct_failed and result.state.engaged
    run(beast, enemy, result.state,
        [('round.1.priority-tie', 1), ('round.1.second.attack.0.hit', 1), ('round.1.first.attack.0.hit', 1)])


def test_noblesse_stomp_uses_own_strength_and_no_weapon_bonus():
    owner = bare('mechanic.noblesse-stomp')
    owner = replace(owner, main_weapon=replace(owner.main_weapon, strength_bonus=2))
    enemy = bare()
    state = start(owner, enemy)
    state = replace(state, second=replace(state.second, condition=Condition.KNOCKED_DOWN))
    # Ordinary S5 needs 2+, but the stomp at the warrior's own S3 needs 4+.
    result = run(owner, enemy, state,
        [('round.0.first.attack.0.wound', 1), ('round.0.first.stomp.attack.0.wound', 3)])
    assert len(result.attacks) == 2 and all(not attack.wounded for attack in result.attacks)


@pytest.mark.parametrize('tag,stat,initial,expiry,stays', [
    ('condition.petru-strength', 'strength', 4, 1, 2),
    ('condition.petru-resilience', 'toughness', 4, 1, 2),
    ('condition.petru-debilitating', 'toughness', 2, 6, 5)])
def test_petru_initial_bonus_own_recovery_and_permanent_expiry(tag, stat, initial, expiry, stays):
    recipient, enemy = bare(tag), bare()
    state = start(recipient, enemy)
    assert getattr(state.first, stat) == initial
    key = tag.removeprefix('condition.')
    result = run(recipient, enemy, state,
        [(f'round.0.first.{key}', stays), ('round.0.first.attack.0.hit', 1),
         ('round.0.second.attack.0.hit', 1)])
    assert getattr(result.state.first, stat) == initial
    # Opposing turn spends no expiry die.
    result = run(recipient, enemy, result.state,
        [('round.1.priority-tie', 4), ('round.1.first.attack.0.hit', 1),
         ('round.1.second.attack.0.hit', 1)])
    result = run(recipient, enemy, result.state,
        [(f'round.2.first.{key}', expiry), ('round.2.priority-tie', 4),
         ('round.2.first.attack.0.hit', 1), ('round.2.second.attack.0.hit', 1)])
    assert getattr(result.state.first, stat) == 3
    assert tag in result.state.first.resources_spent


def test_petru_fortitude_extra_wound_never_recovered_by_herbs():
    recipient, enemy = bare('condition.petru-fortitude', 'mechanic.herb-lore'), bare()
    state = start(recipient, enemy)
    assert state.first.wounds == 3
    # Once the extra wound is lost, full profile W2 has nothing to heal.
    state = replace(state, first=replace(state.first, wounds=2))
    result = run(recipient, enemy, state,
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])
    assert result.state.first.wounds == 2


def test_herb_lore_optional_self_heal_threshold_and_cap():
    healer, enemy = bare('mechanic.herb-lore'), bare()
    state = start(healer, enemy)
    state = replace(state, first=replace(state.first, wounds=1))
    result = run(healer, enemy, state,
        [('round.0.first.herb-lore', 4), ('round.0.first.attack.0.hit', 1),
         ('round.0.second.attack.0.hit', 1)], [('round.0.first.herb-lore', True)])
    assert result.state.first.wounds == 2
    # An opponent turn cannot trigger the healer's recovery ability.
    run(healer, enemy, result.state,
        [('round.1.priority-tie', 4), ('round.1.first.attack.0.hit', 1),
         ('round.1.second.attack.0.hit', 1)])


def test_danse_macabre_only_own_recovery_can_release_control():
    dancer, enemy = bare('condition.danse-macabre-controlled'), bare(initiative=2)
    result = run(dancer, enemy, start(dancer, enemy, charging=()),
        [('round.0.first.danse-macabre.0', 6), ('round.0.first.danse-macabre.1', 6),
         ('round.0.second.attack.0.hit', 1)])
    assert result.state.first.danse_macabre_controlled and len(result.attacks) == 1
    result = run(dancer, enemy, result.state,
        [('round.1.second.attack.0.hit', 1)])
    assert result.state.first.danse_macabre_controlled
    result = run(dancer, enemy, result.state,
        [('round.2.first.danse-macabre.0', 3), ('round.2.first.danse-macabre.1', 4),
         ('round.2.first.attack.0.hit', 1),
         ('round.2.second.attack.0.hit', 1)])
    assert not result.state.first.danse_macabre_controlled and len(result.attacks) == 2


def test_alchemist_supplied_bonuses_and_addiction_preserve_defence():
    scientist, enemy = bare('condition.alchemist-aberrantius-vigortia', 'condition.alchemist-addicted'), bare()
    with pytest.raises(ValueError, match='Cannot Charge'):
        start(scientist, enemy)
    state = start(scientist, enemy, charging=('second',))
    assert (state.first.strength, state.first.toughness) == (4, 4)
    result = run(scientist, enemy, state,
        [('round.0.second.attack.0.hit', 4), ('round.0.second.attack.0.wound', 4)])
    assert len(result.attacks) == 1 and not result.attacks[0].wounded
    assert result.state.first.condition == Condition.STANDING


def test_petru_strength_changes_the_actual_wound_threshold():
    recipient, enemy = bare('condition.petru-strength'), bare()
    result = run(recipient, enemy, start(recipient, enemy),
        [('round.0.first.petru-strength', 2), ('round.0.first.attack.0.hit', 4),
         ('round.0.first.attack.0.wound', 3), ('round.0.second.attack.0.hit', 1)])
    assert result.attacks[0].wounded and result.state.second.wounds == 1


def test_hypnotic_musk_only_the_printed_animal_or_beast_charger_tests():
    owner, animal = bare('mechanic.hypnotic-musk'), bare('species.animal')
    result = run(animal, owner, start(animal, owner),
        [('round.0.first.hypnotic-musk-charge.0', 6),
         ('round.0.first.hypnotic-musk-charge.1', 6)])
    assert result.attacks == () and not result.state.engaged
    human = bare('species.human')
    run(human, owner, start(human, owner),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])


def test_supplied_impetuous_charge_skips_psychology_before_charge_only():
    errant, enemy = bare('condition.impetuous-charge', 'mechanic.stupidity'), bare('mechanic.causes-fear')
    result = run(errant, enemy, start(errant, enemy),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)],
        [('round.0.first.impetuous-avoid-compulsion', False)])
    assert result.state.engaged and not result.state.first.stupidity_failed


def test_persistent_frenzy_survives_knocked_down_injury():
    from mordheim_combat.modular.attacks import resolve_reference_attack
    attacker, bearer = bare(), bare('mechanic.persistent-frenzy')
    bearer = replace(bearer, characteristics=replace(bearer.characteristics, wounds=1))
    state = start(attacker, bearer)
    assert state.second.frenzy
    dice = StrictDice([{'key': key, 'value': value} for key, value in
        [('x.hit', 4), ('x.wound', 4), ('x.injury.0', 1)]])
    result = resolve_reference_attack(attacker, bearer, state.first, state.second,
        attacker.main_weapon, dice, key='x')
    dice.finish()
    assert result.defender.condition == Condition.KNOCKED_DOWN and result.defender.frenzy


def belandysh():
    return compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1c',
        profile_id='hireling.dramatis.belandysh-condemned-champion-of-chen',
        main_weapon_id='weapon.broadsword-of-damnation', armour_id='armour.chaos-armour',
        defence_ids=('defence.helmet',)))


def test_belandysh_only_needed_characteristics_roll_once_per_turn():
    champion, enemy = belandysh(), bare('mechanic.psychology-immunity')
    state = start(champion, enemy)  # No unused random value is prefetched.
    result = run(champion, enemy, state,
        [('round.0.first.characteristic.A.0', 2, 3),
         ('round.0.first.attack.0.attacker.characteristic.WS.0', 3),
         ('round.0.first.attack.0.hit', 1), ('round.0.first.attack.1.hit', 1),
         ('round.0.second.attack.0.hit', 1)])
    assert result.state.first.random_rolled == {'A', 'WS'}
    assert len(result.attacks) == 3
    # Initiative is first needed when the next turn has equal priority tiers.
    result = run(champion, enemy, result.state,
        [('round.1.first.characteristic.I.0', 6), ('round.1.first.characteristic.A.0', 1, 3),
         ('round.1.first.attack.0.attacker.characteristic.WS.0', 2),
         ('round.1.first.attack.0.hit', 1), ('round.1.second.attack.0.hit', 1)])
    assert result.state.first.random_rolled == {'I', 'A', 'WS'}


@pytest.mark.parametrize('condition', [Condition.KNOCKED_DOWN, Condition.OUT])
def test_belandysh_incapable_of_blows_prefetches_no_unused_characteristics(condition):
    enemy, champion = bare('mechanic.psychology-immunity'), belandysh()
    state = start(enemy, champion)
    state = replace(state, first=replace(state.first, on_fire=True),
        second=replace(state.second, condition=condition))
    result = run(enemy, champion, state)
    assert result.attacks == () and result.state.second.random_rolled == frozenset()


@pytest.mark.parametrize('parry,attacks', [(True, 1), (False, 2)])
def test_diestro_main_gauche_elects_a_parry_or_extra_dagger_each_phase(parry, attacks):
    diestro = compile_fighter(FighterBuild('mordheim', band_id='hirelings.hired-sword.2a',
        profile_id='hireling.hired-sword.estalian-diestro', main_weapon_id='weapon.rapier',
        off_hand_id='weapon.main-gauche'))
    enemy = bare()
    result = run(diestro, enemy, start(diestro, enemy),
        [(f'round.0.first.attack.{index}.hit', 1) for index in range(attacks)] +
        [('round.0.second.attack.0.hit', 1)], [('round.0.first.main-gauche-parry', parry)])
    assert len(result.attacks) == attacks+1
    assert result.state.first.parries_remaining == 1  # The rapier keeps its own parry.


@pytest.mark.parametrize('metal,remaining', [(False,2),(True,1)])
def test_electrical_replaces_only_attack_has_separate_initiative_and_recharges(metal,remaining):
    mutant = bare('mechanic.electrical-touch')
    enemy = bare(*(('condition.metal-armour',) if metal else ()), initiative=2)
    result = run(mutant, enemy, start(mutant, enemy),
        [('round.0.first.electrical-touch.attack.0.wound',3),
         ('round.0.first.electrical-touch.recharge',3,3),
         ('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',True)])
    assert len(result.attacks) == 2 and result.attacks[0].hit
    assert result.state.second.wounds == remaining
    assert result.state.first.electrical_available_at == 3
    for index in (1,2):
        result = run(mutant,enemy,result.state,
            [(f'round.{index}.first.attack.0.hit',1),(f'round.{index}.second.attack.0.hit',1)])
        assert len(result.attacks) == 2
    result = run(mutant,enemy,result.state,
        [('round.3.first.electrical-touch.attack.0.wound',1),
         ('round.3.first.electrical-touch.recharge',1,3),('round.3.second.attack.0.hit',1)],
        [('round.3.first.electrical-touch.forfeit.0',True)])
    assert result.state.first.electrical_available_at == 4


def test_electrical_can_forfeit_natural_extra_and_preserves_remaining_weapon():
    from mordheim_core.models import EffectSet
    mutant = replace(bare('mechanic.electrical-touch'),
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks',),strength_bonus=2),))
    enemy = bare(initiative=2)
    result = run(mutant,enemy,start(mutant,enemy),
        [('round.0.first.electrical-touch.attack.0.wound',3),
         ('round.0.first.electrical-touch.recharge',1,3),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',False),
         ('round.0.first.electrical-touch.forfeit.1',True)])
    assert len(result.attacks)==3 and not result.attacks[0].wounded


def test_djinn_one_power_own_recovery_expiry_and_no_consecutive_repeat():
    djinn,enemy=bare('mechanic.djinns-curse',initiative=4),bare(initiative=2)
    result=run(djinn,enemy,start(djinn,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],
        [('round.0.first.djinn-power.curse',False),('round.0.first.djinn-power.luck',True)])
    assert result.state.first.djinn_power=='luck'
    result=run(djinn,enemy,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert result.state.first.djinn_power=='luck'
    result=run(djinn,enemy,result.state,
        [('round.2.first.attack.0.hit',1),('round.2.second.attack.0.hit',1)],
        [('round.2.first.djinn-power.curse',True)])
    assert result.state.first.djinn_power=='curse'
    result=run(djinn,enemy,result.state,
        [('round.3.first.attack.0.hit',1),('round.3.second.attack.0.hit',1)])
    assert result.state.first.djinn_power=='curse'
    result=run(djinn,enemy,result.state,
        [('round.4.first.attack.0.hit',1),('round.4.second.attack.0.hit',1)],
        [('round.4.first.djinn-power.luck',False)])
    assert result.state.first.djinn_power is None
    assert result.state.first.last_djinn_power is None


def test_gaoler_held_pair_tests_strictly_below_strength_minus_one_next_melee():
    gaoler=compile_fighter(FighterBuild('mordheim',band_id='hirelings.hired-sword.1b',
        profile_id='hireling.hired-sword.gaoler',main_weapon_id='weapon.flail',owned_item_ids=('flail',)))
    enemy=bare(initiative=2)
    result=run(gaoler,enemy,start(gaoler,enemy),
        [('round.0.first.grapple.hit',4),('round.0.first.grapple.strength',2)],
        [('round.0.first.torturer-grapple',True)])
    assert result.state.first.grappling and result.state.second.grappled
    assert len(result.attacks)==1 and not result.attacks[0].wounded
    result=run(gaoler,enemy,result.state,[('round.1.second.grapple-escape',2)])
    assert result.attacks==() and result.state.second.grappled
    result=run(gaoler,enemy,result.state,
        [('round.2.second.grapple-escape',1),('round.2.first.attack.0.hit',1),
         ('round.2.second.attack.0.hit',1)],[('round.2.first.torturer-grapple',False)])
    assert not result.state.second.grappled and not result.state.first.grappling
    assert len(result.attacks)==2


def test_impetuous_released_compulsion_restores_ordinary_fear_charge_test():
    errant,enemy=bare('condition.impetuous-charge'),bare('mechanic.causes-fear')
    result=run(errant,enemy,start(errant,enemy),
        [('round.0.first.impetuous-release.0',3),('round.0.first.impetuous-release.1',4),
         ('round.0.first.fear.charge.0',6),('round.0.first.fear.charge.1',6)],
        [('round.0.first.impetuous-avoid-compulsion',True)])
    assert not result.state.engaged and result.attacks==()


def test_supplied_netter_cuts_out_only_own_recovery_and_keeps_stood_priority():
    victim,enemy=bare(initiative=4,condition_ids=('condition.netted',)),bare(initiative=2)
    state=start(enemy,victim)
    result=run(enemy,victim,state,
        [('round.0.first.attack.0.wound',1)])
    assert result.state.second.netted and result.state.second.condition==Condition.KNOCKED_DOWN
    result=run(enemy,victim,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert not result.state.second.netted and result.state.second.condition==Condition.STANDING
    assert len(result.attacks)==2


def test_black_hunger_adopted_automatic_activation_only_own_turn_and_backlash():
    hungry,enemy=bare('mechanic.black-hunger',initiative=4),bare(initiative=2)
    result=run(hungry,enemy,start(hungry,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.first.attack.1.hit',1),
         ('round.0.second.attack.0.hit',1),('round.0.first.black-hunger.hits',1,3),
         ('round.0.first.black-hunger.hit.0.wound',1)])
    assert len(result.attacks)==4
    result=run(hungry,enemy,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert len(result.attacks)==2


def test_raise_insignia_recovery_reroll_expires_before_melee_plain_leadership():
    recipient=bare('mechanic.feral-instinct',initiative=4,
        condition_ids=('condition.command.raise-our-insignia',))
    singer=bare('mechanic.sea-shanty-psychology',initiative=2)
    result=run(recipient,singer,start(recipient,singer),
        [('round.0.first.feral-instinct.0',6),('round.0.first.feral-instinct.1',6),
         ('round.0.first.feral-instinct.reroll.0',3),('round.0.first.feral-instinct.reroll.1',4),
         ('round.0.second.sea-shanty.leadership.0',6),('round.0.second.sea-shanty.leadership.1',6),
         ('round.0.second.attack.0.hit',1)],
        [('round.0.first.feral-instinct.reroll',True),('round.0.second.sea-shanty',True)])
    assert not result.state.first.feral_instinct_failed and len(result.attacks)==1


def test_electrical_sole_replacement_does_not_draw_unused_ordinary_priority_tie():
    mutant,enemy=bare('mechanic.electrical-touch'),bare()
    result=run(mutant,enemy,start(mutant,enemy,charging=()),
        [('round.0.first.electrical-touch.attack.0.wound',1),
         ('round.0.first.electrical-touch.recharge',1,3),('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',True)])
    assert len(result.attacks)==2


def test_electrical_canonical_shallows_mutation_uses_s3_not_hero_strength_or_armour():
    mutant=compile_fighter(FighterBuild('mordheim',band_id='shallows-beasts-mim',
        profile_id='buccaneer',main_weapon_id='weapon.mace',
        special_rule_ids=('band--mutations-electrical-touch',)))
    assert 'mechanic.electrical-touch' in mutant.global_effects.tags
    enemy=bare(initiative=2)
    result=run(mutant,enemy,start(mutant,enemy),
        [('round.0.first.electrical-touch.attack.0.wound',3),
         ('round.0.first.electrical-touch.recharge',1,3),('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',True)])
    assert mutant.characteristics.strength==4 and not result.attacks[0].wounded


def test_poetry_supplied_victorious_leader_bonus_consumes_first_test_not_first_failure():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    leader,enemy=bare('condition.poetry-victorious-leader'),bare()
    state=start(leader,enemy)
    for key,expected in [('first-test',True),('second-test',False)]:
        dice=StrictDice([{'key':f'{key}.0','value':4},{'key':f'{key}.1','value':4}])
        policy=StrictDecisions([])
        passed,current=resolve_local_leadership(leader,state,dice,policy,key,first=True,return_state=True)
        dice.finish();policy.finish()
        assert passed is expected
        state=replace(state,first=current)
    assert 'poetry-first-leadership' in state.first.resources_spent


def test_songster_reroll_bonus_cannot_increase_leadership_above_ten():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_core.models import LocalParticipant
    recipient=replace(bare(),characteristics=replace(bare().characteristics,leadership=10))
    bard=bare('mechanic.songster')
    enemy=bare()
    state=initialize_duel(recipient,enemy,StrictDice([]),context=DuelContext(charging=(),
        active_participant='first',nearby=(LocalParticipant('bard','first',bard),),
        distances=(('first','bard',6),)))
    dice=StrictDice([{'key':f'probe{suffix}','value':value} for suffix,value in
        [('.0',6),('.1',6),('.reroll.0',6),('.reroll.1',5)]])
    policy=StrictDecisions([{'key':'probe.reroll','value':True}])
    assert resolve_local_leadership(recipient,state,dice,policy,'probe',first=True) is False
    dice.finish();policy.finish()


def test_gaoler_declaration_replaces_all_timed_strikes_even_when_grapple_misses():
    from mordheim_core.models import EffectSet
    gaoler=replace(bare('mechanic.gaoler-grapple','skill.shifty',initiative=4),
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks','rule.strikes-last-bite')),))
    enemy=bare(initiative=2)
    state=initialize_duel(gaoler,enemy,StrictDice([]),context=DuelContext(
        charging=('second',),active_participant='second'))
    result=run(gaoler,enemy,state,
        [('round.0.second.attack.0.hit',1),('round.0.first.grapple.hit',1)],
        [('round.0.first.torturer-grapple',True)])
    assert len(result.attacks)==2 and not result.attacks[1].hit


def test_declared_black_hunger_still_backlashes_after_charge_fails_fear():
    hungry,enemy=bare('mechanic.black-hunger'),bare('mechanic.causes-fear')
    result=run(hungry,enemy,start(hungry,enemy),
        [('round.0.first.fear.charge.0',6),('round.0.first.fear.charge.1',6),
         ('round.0.first.black-hunger.hits',1,3),('round.0.first.black-hunger.hit.0.wound',1)])
    assert not result.state.engaged and len(result.attacks)==1
    assert not result.attacks[0].wounded


def test_hypnotic_musk_keeps_supplied_goading_charge_exception_without_producer():
    bearer=bare('mechanic.hypnotic-musk',initiative=2)
    animal=bare('species.animal','condition.goading-charge',initiative=4)
    result=run(animal,bearer,start(animal,bearer),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert len(result.attacks)==2 and result.state.engaged


def test_shanty_loses_one_ordinary_attack_without_erasing_natural_extra():
    from mordheim_core.models import EffectSet
    singer=bare('mechanic.sea-shanty',initiative=4)
    mutant=replace(bare(initiative=2),extra_attacks=(EffectSet(tags=('weapon.natural-attacks',)),))
    result=run(singer,mutant,start(singer,mutant),
        [('round.0.first.sea-shanty.leadership.0',6),('round.0.first.sea-shanty.leadership.1',6),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],
        [('round.0.first.sea-shanty',True)])
    assert len(result.attacks)==2


def test_electrical_replaces_remaining_extra_after_shanty_loses_ordinary_attack():
    from mordheim_core.models import EffectSet
    singer=bare('mechanic.sea-shanty',initiative=4)
    mutant=replace(bare('mechanic.electrical-touch',initiative=2),
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks',)),))
    result=run(singer,mutant,start(singer,mutant),
        [('round.0.first.sea-shanty.leadership.0',6),('round.0.first.sea-shanty.leadership.1',6),
         ('round.0.first.attack.0.hit',1),('round.0.second.electrical-touch.attack.0.wound',1),
         ('round.0.second.electrical-touch.recharge',1,3)],
        [('round.0.first.sea-shanty',True),('round.0.second.electrical-touch.forfeit.1',True)])
    assert len(result.attacks)==2 and result.attacks[1].hit


def test_explicit_no_contact_suppresses_melee_auras_and_blows_but_keeps_own_recovery():
    fighter=bare('mechanic.feral-instinct','mechanic.black-hunger',
        'mechanic.confound-and-confuse','mechanic.sea-shanty',initiative=4)
    enemy=bare('mechanic.mantle-of-crows',initiative=2)
    state=start(fighter,enemy,contacts=())
    assert not state.engaged
    result=run(fighter,enemy,state,
        [('round.0.first.feral-instinct.0',3),('round.0.first.feral-instinct.1',4),
         ('round.0.first.black-hunger.hits',1,3),('round.0.first.black-hunger.hit.0.wound',1)])
    assert not result.state.engaged and len(result.attacks)==1
    assert result.state.round_index==1
    assert not result.attacks[0].wounded


def test_explicit_contact_keeps_normal_duel_without_inferring_from_charge():
    fighter,enemy=bare(initiative=4),bare(initiative=2)
    state=start(fighter,enemy,charging=(),contacts=(('first','second'),))
    assert state.engaged
    result=run(fighter,enemy,state,[('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert len(result.attacks)==2


def test_inquisitor_brand_is_dynamic_once_per_success_and_rechecks_every_combat_phase():
    from mordheim_core.models import MutationOption
    priest=replace(bare('mechanic.solkan-inquisitor',initiative=4),
        mutation_options=(MutationOption(12,stat_ops=(('toughness','halve-ceil',2),)),))
    target=bare(initiative=2)
    result=run(priest,target,start(priest,target),
        [('round.0.first.inquisitor.judgement',6),('round.0.first.inquisitor.mutation.tens',1),
         ('round.0.first.inquisitor.mutation.units',2),('round.0.first.attack.0.hit',4),
         ('round.0.first.attack.0.wound',3),('round.0.second.attack.0.hit',1)])
    assert result.state.second.toughness==2 and result.state.second.wounds==1
    assert len(result.state.second.mutations)==1
    result=run(priest,target,result.state,
        [('round.1.first.inquisitor.judgement',1),('round.1.first.attack.0.hit',4),
         ('round.1.first.attack.0.wound',2),('round.1.second.attack.0.hit',1)])
    assert result.state.second.toughness==2 and result.state.second.wounds==1
    assert not result.attacks[0].wounded


@pytest.mark.parametrize('excluded',['nature.undead','identity.chaos-follower','warband-group.chaotic'])
def test_inquisitor_does_not_roll_or_brand_excluded_enemy(excluded):
    priest,target=bare('mechanic.solkan-inquisitor',initiative=4),bare(excluded,initiative=2)
    result=run(priest,target,start(priest,target),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert not result.state.second.mutations


def test_burning_body_end_every_turn_ignites_only_then_existing_own_recovery_extinguishes():
    mutant,target=bare('mechanic.burning-body',initiative=4),bare(initiative=2)
    result=run(mutant,target,start(mutant,target),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1),
         ('round.0.first.burning-body',4)])
    assert result.state.second.on_fire
    result=run(mutant,target,result.state,
        [('round.1.second.fire.extinguish',4),('round.1.first.attack.0.hit',1),
         ('round.1.second.attack.0.hit',1),('round.1.first.burning-body',3)])
    assert not result.state.second.on_fire


def test_ranger_herb_lore_only_supplied_no_contact_recovery_preserves_variant():
    ranger,enemy=bare('mechanic.herb-lore-outside-combat',initiative=4),bare(initiative=2)
    state=start(ranger,enemy,contacts=())
    state=replace(state,first=replace(state.first,wounds=1))
    result=run(ranger,enemy,state,[('round.0.first.herb-lore',4)],
        [('round.0.first.herb-lore',True)])
    assert result.state.first.wounds==2 and result.attacks==()
    state=start(ranger,enemy)
    state=replace(state,first=replace(state.first,wounds=1))
    result=run(ranger,enemy,state,[('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert result.state.first.wounds==1


def test_poetry_supplied_one_turn_inspiration_changes_ws_and_attacks_then_expires():
    recipient,enemy=bare('condition.poetry-inspired',initiative=4),bare(initiative=2)
    enemy=replace(enemy,characteristics=replace(enemy.characteristics,weapon_skill=7))
    result=run(recipient,enemy,start(recipient,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.first.attack.1.hit',1),
         ('round.0.second.attack.0.hit',1)])
    assert len(result.attacks)==3 and result.attacks[0].hit_target==4
    result=run(recipient,enemy,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert len(result.attacks)==2 and result.attacks[0].hit_target==5


def test_no_contact_keeps_actual_own_fire_recovery_hit_and_state():
    victim,enemy=bare(),bare('mechanic.mantle-of-crows')
    state=start(victim,enemy,contacts=())
    state=replace(state,round_index=2,first=replace(state.first,on_fire=True))
    result=run(victim,enemy,state,[('round.2.first.fire.extinguish',1),
        ('round.2.first.fire.hit.wound',3)])
    assert len(result.attacks)==1 and result.attacks[0].wounded
    assert result.state.first.wounds==1 and not result.state.engaged


@pytest.mark.parametrize('persistent',[False,True])
def test_supplied_netted_knockdown_loses_ordinary_frenzy_but_preserves_hood_exception(persistent):
    fighter=bare('condition.netted',*(('mechanic.persistent-frenzy',) if persistent else ()))
    fighter=replace(fighter,global_effects=replace(fighter.global_effects,frenzy=True))
    state=start(bare(),fighter)
    assert state.second.condition==Condition.KNOCKED_DOWN
    assert state.second.frenzy is persistent


def test_canonical_bear_supplied_tamer_waiver_and_explicit_out_provider():
    bear=compile_fighter(FighterBuild('mordheim',band_id='kislevites',profile_id='trained-bear',
        condition_ids=('condition.bear-handler-nearby',)))
    enemy=bare()
    run(bear,enemy,start(bear,enemy,charging=(),contacts=()))
    tamer=compile_fighter(FighterBuild('mordheim',band_id='kislevites',profile_id='bear-tamer'))
    state=initialize_duel(bear,enemy,StrictDice([]),context=DuelContext(charging=(),
        active_participant='first',contacts=(),nearby=(LocalParticipant('tamer','first',tamer,condition='out'),),
        distances=(('first','tamer',6),)))
    result=run(bear,enemy,state,[('round.0.first.stupidity.0',6),('round.0.first.stupidity.1',6)])
    assert result.state.first.stupidity_failed


def test_canonical_bear_uses_only_nearby_tamer_leadership_for_other_tests():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    bear=compile_fighter(FighterBuild('mordheim',band_id='kislevites',profile_id='trained-bear'))
    for profile,choices,expected in [('bear-tamer',[{'key':'probe.handler.provider','value':True}],True),
                                      ('druzhina-captain',[],False)]:
        provider=compile_fighter(FighterBuild('mordheim',band_id='kislevites',profile_id=profile))
        state=initialize_duel(bear,bare(),StrictDice([]),context=DuelContext(charging=(),
            active_participant='first',nearby=(LocalParticipant('provider','first',provider),),
            distances=(('first','provider',6),)))
        dice=StrictDice([{'key':'probe.0','value':3},{'key':'probe.1','value':4}])
        decisions=StrictDecisions(choices)
        assert resolve_local_leadership(bear,state,dice,decisions,'probe',first=True) is expected
        dice.finish();decisions.finish()


def test_canonical_dim_witted_promoted_leader_lends_seven_not_own_ten():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    leader=compile_fighter(FighterBuild('mordheim',band_id='adventurers-kaz',profile_id='barbarian',
        condition_ids=('condition.adventurer-barbarian-leader',)))
    recipient=compile_fighter(FighterBuild('mordheim',band_id='adventurers-kaz',profile_id='dwarf'))
    assert leader.characteristics.leadership==10
    state=initialize_duel(recipient,bare(),StrictDice([]),context=DuelContext(charging=(),
        active_participant='first',nearby=(LocalParticipant('leader','first',leader),),
        distances=(('first','leader',6),)))
    dice=StrictDice([{'key':'probe.0','value':3},{'key':'probe.1','value':4}])
    choices=StrictDecisions([{'key':'probe.leader.leader','value':True}])
    assert resolve_local_leadership(recipient,state,dice,choices,'probe',first=True)
    dice.finish();choices.finish()
    dice=StrictDice([{'key':'probe.0','value':4},{'key':'probe.1','value':4}])
    choices=StrictDecisions([{'key':'probe.leader.leader','value':True}])
    assert not resolve_local_leadership(recipient,state,dice,choices,'probe',first=True)
    dice.finish();choices.finish()


@pytest.mark.parametrize('band',['ghutani-rel','muzil-rel','turjuk-rel'])
def test_canonical_poetry_leader_first_test_and_separate_inspiration(band):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    leader=compile_fighter(FighterBuild('mordheim',band_id=band,profile_id='emir',
        condition_ids=('condition.poetry-victorious-leader','condition.poetry-inspired')))
    enemy=bare(initiative=1)
    state=start(leader,enemy)
    assert state.first.weapon_skill==leader.characteristics.weapon_skill+1
    value=leader.characteristics.leadership+1
    dice=StrictDice([{'key':'probe.0','value':min(6,value-1)},{'key':'probe.1','value':value-min(6,value-1)}])
    passed,current=resolve_local_leadership(leader,state,dice,StrictDecisions([]),'probe',first=True,return_state=True)
    dice.finish()
    assert passed and 'poetry-first-leadership' in current.resources_spent


def test_canonical_ranger_recovery_heals_only_outside_contact():
    ranger=compile_fighter(FighterBuild('mordheim',band_id='hirelings.hired-sword.1b',
        profile_id='hireling.hired-sword.kislev-ranger',
        main_weapon_id='weapon.sword',special_rule_ids=('hireling.hired-sword.kislev-ranger.rule.herb-lore',)))
    # A supplied current +W advancement permits a living, injured self-healer.
    ranger=replace(ranger,characteristics=replace(ranger.characteristics,wounds=2))
    enemy=bare()
    state=start(ranger,enemy,contacts=())
    state=replace(state,first=replace(state.first,wounds=1))
    result=run(ranger,enemy,state,[('round.0.first.herb-lore',4)],
        [('round.0.first.herb-lore',True)])
    assert result.state.first.wounds==2


def test_canonical_inquisitor_prepared_chart_reaches_live_combat_consumer():
    priest=compile_fighter(FighterBuild('mordheim',band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.priest-of-verena',variant_ids=('deity.solkan',),
        special_rule_ids=('hireling.hired-sword.priest-of-verena.skill.inquisitor',)))
    assert len(priest.mutation_options)==36
    target=bare(initiative=1)
    result=run(priest,target,start(priest,target),
        [('round.0.first.inquisitor.judgement',6),('round.0.first.inquisitor.mutation.tens',1),
         ('round.0.first.inquisitor.mutation.units',2),('round.0.first.attack.0.hit',1),
         ('round.0.second.attack.0.hit',1)])
    assert result.state.second.toughness==2 and len(result.state.second.mutations)==1


def test_canonical_inquisitor_psychology_immunity_reuses_normal_fear_consumer():
    priest=compile_fighter(FighterBuild('mordheim',band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.priest-of-verena',variant_ids=('deity.solkan',),
        special_rule_ids=('hireling.hired-sword.priest-of-verena.skill.inquisitor',)))
    enemy=bare('nature.undead','mechanic.causes-fear',initiative=1)
    result=run(priest,enemy,start(priest,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert result.state.engaged and not result.state.failed_charges


def test_canonical_witch_finder_supplied_attempt_requires_named_enemy_and_mark():
    priest=compile_fighter(FighterBuild('mordheim',band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.priest-of-verena',variant_ids=('deity.solkan',),
        special_rule_ids=('hireling.hired-sword.priest-of-verena.skill.witch-finder',),
        condition_ids=('condition.witch-finder-charge',)))
    with pytest.raises(ValueError,match='Witch-finder'):
        start(priest,bare())
    with pytest.raises(ValueError,match='Witch-finder'):
        start(priest,bare('identity.warlock'),charging=())
    state=start(priest,bare('identity.warlock'))
    assert state.first_charged


def test_canonical_nuttaz_only_supplied_required_attempt_is_compulsory():
    nuttaz=compile_fighter(FighterBuild('mordheim',band_id='black-orcs',profile_id='orc-nuttaz',
        main_weapon_id='weapon.axe',condition_ids=('condition.nuttaz-charge',)))
    with pytest.raises(ValueError,match='compulsory charge'):
        start(nuttaz,bare(),charging=())
    assert start(nuttaz,bare()).first_charged


def test_no_hand_attacks_retains_separate_late_bite_without_phantom_fist():
    from mordheim_core.models import EffectSet
    mutant=replace(bare('condition.mim-no-hand-attacks',initiative=4),
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks','rule.strikes-last-bite')),))
    enemy=bare(initiative=2)
    result=run(mutant,enemy,start(mutant,enemy),
        [('round.0.second.attack.0.hit',1),('round.0.first.last-bite.attack.0.hit',1)])
    assert len(result.attacks)==2


def test_inquisitor_subtable_roll_retains_priest_resource_at_live_round_hook():
    priest=compile_fighter(FighterBuild('mordheim',band_id='hirelings.hired-sword.2b',
        profile_id='hireling.hired-sword.priest-of-verena',variant_ids=('deity.solkan',),
        special_rule_ids=('hireling.hired-sword.priest-of-verena.skill.inquisitor',)))
    priest=replace(priest,global_effects=replace(priest.global_effects,
        tags=(*priest.global_effects.tags,'mechanic.ranalds-luck')))
    keys=['round.0.first.inquisitor.judgement',
        'round.0.first.inquisitor.mutation.tens','round.0.first.inquisitor.mutation.units']
    choices=[(f'{key}.ranalds-luck.{direction}',False) for key in keys for direction in ('plus','minus')]
    choices.append(('round.0.first.inquisitor.mutation.66.atrophy.ranalds-luck.plus',True))
    target=bare(initiative=1)
    result=run(priest,target,start(priest,target),
        [(keys[0],6),(keys[1],6),(keys[2],6),('round.0.first.inquisitor.mutation.66.atrophy',4),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],choices)
    assert result.state.second.atrophied_legs==1
    assert 'ranalds-luck' in result.state.first.resources_spent
    assert 'ranalds-luck' not in result.state.second.resources_spent


def test_cutting_out_of_supplied_net_spends_recovery_without_new_djinn_power():
    djinn=bare('mechanic.djinns-curse',initiative=4,condition_ids=('condition.netted',))
    enemy=bare(initiative=2)
    result=run(djinn,enemy,start(djinn,enemy,charging=()),
        [('round.0.second.attack.0.hit',1),('round.0.first.attack.0.hit',1)])
    assert not result.state.first.netted and result.state.first.djinn_power is None
    assert len(result.attacks)==2


def test_personal_one_die_luck_prevents_rerolling_whole_leadership_test_again():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    fighter,enemy=bare('skill.luck','mechanic.leadership-reroll'),bare()
    state=start(fighter,enemy)
    dice=StrictDice([{'key':key,'value':6} for key in ('probe.0','probe.0.reroll','probe.1')])
    choices=StrictDecisions([{'key':'probe.0.luck','value':True}])
    passed,current=resolve_local_leadership(fighter,state,dice,choices,'probe',first=True,return_state=True)
    dice.finish();choices.finish()
    assert not passed and 'luck' in current.resources_spent


def test_castoff_removes_carried_extra_hand_weapon_but_retains_innate_limb():
    from mordheim_combat.modular.equipment import equipment_for_state
    from mordheim_core.models import EffectSet
    carried=EffectSet(tags=('weapon.sword','mutation.carried-weapon','mutation.hand.extra.0'))
    innate=EffectSet(tags=('weapon.natural-attacks','rule.great-claw','mutation.hand.extra.1'))
    fighter=replace(bare(),extra_attacks=(carried,innate))
    state=replace(start(fighter,bare()).first,equipment_cast_off=True)
    projected=equipment_for_state(fighter,state,first_round=True)
    assert projected.extra_attacks==(innate,)


def test_castoff_retains_only_actual_extra_hand_dagger_in_its_physical_slot():
    from mordheim_combat.modular.equipment import equipment_for_state
    from mordheim_core.models import CarriedEquipment
    dagger=compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,3,1,leadership=7),
        main_weapon_id='weapon.dagger')).main_weapon
    fighter=replace(bare(),mutation_equipment=(CarriedEquipment('owned-dagger',dagger,'weapon','extra.0'),))
    state=replace(start(fighter,bare()).first,equipment_cast_off=True)
    projected=equipment_for_state(fighter,state,first_round=True)
    assert 'weapon.fist' in projected.main_weapon.tags
    assert len(projected.extra_attacks)==1 and 'weapon.dagger' in projected.extra_attacks[0].tags
    assert 'mutation.hand.extra.0' in projected.extra_attacks[0].tags
