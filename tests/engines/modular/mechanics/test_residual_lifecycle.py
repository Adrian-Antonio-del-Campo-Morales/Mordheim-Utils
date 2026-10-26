"""Source discriminators for the residual individual lifecycle contracts."""
import sys
from dataclasses import replace

import pytest


from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.phases import Condition
from tests.engines.shared.dice import StrictDice, StrictDecisions
from mordheim_core.models import Characteristics, DuelContext, FighterBuild, LocalParticipant


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
def test_shanty_canonical_loss_of_only_attack_and_declining(precompiled, band, collection):
    singer = precompiled().first
    enemy = precompiled().second
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
def test_shanty_printed_exclusions_neither_offer_nor_test(precompiled, tag, immune):
    singer, enemy = precompiled().first, precompiled().second
    run(singer, enemy, start(singer, enemy),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])


def test_mordheim_song_does_not_invent_lustria_psychology_exclusion(precompiled):
    singer, enemy = precompiled().first, precompiled().second
    result = run(singer, enemy, start(singer, enemy),
        [('round.0.first.sea-shanty.leadership.0', 6), ('round.0.first.sea-shanty.leadership.1', 6),
         ('round.0.first.attack.0.hit', 1)], [('round.0.first.sea-shanty', True)])
    assert len(result.attacks) == 1


def test_ogre_belch_penalty_expires_but_engagement_resource_persists(precompiled):
    ogre, enemy = precompiled().first, precompiled().second
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
def test_charge_gate_cancels_failed_charge_and_no_blows(precompiled, gate):
    bearer, enemy = precompiled().first, precompiled().second
    key = 'slaanesh-charge' if gate.endswith('slaanesh-charge-test') else 'charismatic-charge'
    result = run(enemy, bearer, start(enemy, bearer),
        [(f'round.0.first.{key}.0', 6), (f'round.0.first.{key}.1', 6)])
    assert not result.state.engaged and result.state.failed_charges == {'first'}
    assert result.attacks == ()


def test_cannot_charge_preserves_defensive_melee(precompiled):
    restricted, enemy = precompiled().first, precompiled().second
    with pytest.raises(ValueError, match='Cannot Charge'):
        start(restricted, enemy)
    run(enemy, restricted, start(enemy, restricted),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])


def test_feral_test_own_turn_only_records_failure_without_movement(precompiled):
    beast, enemy = precompiled().first, precompiled().second
    result = run(beast, enemy, start(beast, enemy),
        [('round.0.first.feral-instinct.0', 6), ('round.0.first.feral-instinct.1', 6),
         ('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])
    assert result.state.first.feral_instinct_failed and result.state.engaged
    run(beast, enemy, result.state,
        [('round.1.priority-tie', 1), ('round.1.second.attack.0.hit', 1), ('round.1.first.attack.0.hit', 1)])


def test_noblesse_stomp_uses_own_strength_and_no_weapon_bonus(precompiled):
    owner = precompiled().first
    owner = replace(owner, main_weapon=replace(owner.main_weapon, strength_bonus=2))
    enemy = precompiled().second
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
def test_petru_initial_bonus_own_recovery_and_permanent_expiry(precompiled, tag, stat, initial, expiry, stays):
    recipient, enemy = precompiled().first, precompiled().second
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


def test_petru_fortitude_extra_wound_never_recovered_by_herbs(precompiled):
    recipient, enemy = precompiled().first, precompiled().second
    state = start(recipient, enemy)
    assert state.first.wounds == 3
    # Once the extra wound is lost, full profile W2 has nothing to heal.
    state = replace(state, first=replace(state.first, wounds=2))
    result = run(recipient, enemy, state,
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)])
    assert result.state.first.wounds == 2


def test_herb_lore_optional_self_heal_threshold_and_cap(precompiled):
    healer, enemy = precompiled().first, precompiled().second
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


def test_danse_macabre_only_own_recovery_can_release_control(precompiled):
    dancer, enemy = precompiled().first, precompiled().second
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


def test_alchemist_supplied_bonuses_and_addiction_preserve_defence(precompiled):
    # ``builders`` provenance: the scientist was compiled before the plain foe.
    scientist, enemy = precompiled().first, precompiled().second
    with pytest.raises(ValueError, match='Cannot Charge'):
        start(scientist, enemy)
    state = start(scientist, enemy, charging=('second',))
    assert (state.first.strength, state.first.toughness) == (4, 4)
    result = run(scientist, enemy, state,
        [('round.0.first.alchemist-brew', 5),
         ('round.0.second.attack.0.hit', 4), ('round.0.second.attack.0.wound', 4)])
    assert len(result.attacks) == 1 and not result.attacks[0].wounded
    assert result.state.first.condition == Condition.STANDING


def test_petru_strength_changes_the_actual_wound_threshold(precompiled):
    recipient, enemy = precompiled().first, precompiled().second
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


def test_supplied_impetuous_charge_skips_psychology_before_charge_only(precompiled):
    errant, enemy = precompiled().first, precompiled().second
    result = run(errant, enemy, start(errant, enemy),
        [('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1)],
        [('round.0.first.impetuous-avoid-compulsion', False)])
    assert result.state.engaged and not result.state.first.stupidity_failed


def test_persistent_frenzy_survives_knocked_down_injury(precompiled):
    from mordheim_combat.modular.attacks import resolve_reference_attack
    attacker, bearer = precompiled().first, precompiled().second
    bearer = replace(bearer, characteristics=replace(bearer.characteristics, wounds=1))
    state = start(attacker, bearer)
    assert state.second.frenzy
    dice = StrictDice([{'key': key, 'value': value} for key, value in
        [('x.hit', 4), ('x.wound', 4), ('x.injury.0', 1)]])
    result = resolve_reference_attack(attacker, bearer, state.first, state.second,
        attacker.main_weapon, dice, key='x')
    dice.finish()
    assert result.defender.condition == Condition.KNOCKED_DOWN and result.defender.frenzy


def test_belandysh_only_needed_characteristics_roll_once_per_turn(precompiled):
    champion, enemy = precompiled().first, precompiled().second
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
def test_belandysh_incapable_of_blows_prefetches_no_unused_characteristics(precompiled, condition):
    # ``builders`` provenance: the plain foe was compiled before the champion.
    enemy, champion = precompiled().first, precompiled().second
    state = start(enemy, champion)
    state = replace(state, first=replace(state.first, on_fire=True),
        second=replace(state.second, condition=condition))
    result = run(enemy, champion, state)
    assert result.attacks == () and result.state.second.random_rolled == frozenset()


@pytest.mark.parametrize('parry,attacks', [(True, 1), (False, 2)])
def test_diestro_main_gauche_elects_a_parry_or_extra_dagger_each_phase(precompiled, parry, attacks):
    diestro = precompiled().first
    enemy = precompiled().second
    result = run(diestro, enemy, start(diestro, enemy),
        [(f'round.0.first.attack.{index}.hit', 1) for index in range(attacks)] +
        [('round.0.second.attack.0.hit', 1)], [('round.0.first.main-gauche-parry', parry)])
    assert len(result.attacks) == attacks+1
    assert result.state.first.parries_remaining == 1  # The rapier keeps its own parry.


@pytest.mark.parametrize('metal,remaining', [(False,2),(True,1)])
def test_electrical_replaces_only_attack_has_separate_initiative_and_recharges(metal, remaining):
    # The synthetic metal-armour condition the parameter selects is not part of
    # the recorded pair.
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


def test_electrical_can_forfeit_natural_extra_and_preserves_remaining_weapon(precompiled):
    from mordheim_core.models import EffectSet
    # The recorded pair keeps the plain foe first and the mutant second.
    mutant = replace(precompiled().second,
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks',),strength_bonus=2),))
    enemy = precompiled().first
    result = run(mutant,enemy,start(mutant,enemy),
        [('round.0.first.electrical-touch.attack.0.wound',3),
         ('round.0.first.electrical-touch.recharge',1,3),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',False),
         ('round.0.first.electrical-touch.forfeit.1',True)])
    assert len(result.attacks)==3 and not result.attacks[0].wounded


def test_djinn_one_power_own_recovery_expiry_and_no_consecutive_repeat(precompiled):
    djinn,enemy=precompiled().first,precompiled().second
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


def test_gaoler_held_pair_tests_strictly_below_strength_minus_one_next_melee(precompiled):
    gaoler=precompiled().first
    enemy=precompiled().second
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


def test_impetuous_released_compulsion_restores_ordinary_fear_charge_test(precompiled):
    errant,enemy=precompiled().first,precompiled().second
    result=run(errant,enemy,start(errant,enemy),
        [('round.0.first.impetuous-release.0',3),('round.0.first.impetuous-release.1',4),
         ('round.0.first.fear.charge.0',6),('round.0.first.fear.charge.1',6)],
        [('round.0.first.impetuous-avoid-compulsion',True)])
    assert not result.state.engaged and result.attacks==()


def test_supplied_netter_cuts_out_only_own_recovery_and_keeps_stood_priority(precompiled):
    victim,enemy=precompiled().first,precompiled().second
    state=start(enemy,victim)
    result=run(enemy,victim,state,
        [('round.0.first.attack.0.wound',1)])
    assert result.state.second.netted and result.state.second.condition==Condition.KNOCKED_DOWN
    result=run(enemy,victim,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert not result.state.second.netted and result.state.second.condition==Condition.STANDING
    assert len(result.attacks)==2


def test_black_hunger_adopted_automatic_activation_only_own_turn_and_backlash(precompiled):
    hungry,enemy=precompiled().first,precompiled().second
    result=run(hungry,enemy,start(hungry,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.first.attack.1.hit',1),
         ('round.0.second.attack.0.hit',1),('round.0.first.black-hunger.hits',1,3),
         ('round.0.first.black-hunger.hit.0.wound',1)])
    assert len(result.attacks)==4
    result=run(hungry,enemy,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert len(result.attacks)==2


def test_raise_insignia_recovery_reroll_expires_before_melee_plain_leadership(precompiled):
    recipient=precompiled().first
    singer=precompiled().second
    result=run(recipient,singer,start(recipient,singer),
        [('round.0.first.feral-instinct.0',6),('round.0.first.feral-instinct.1',6),
         ('round.0.first.feral-instinct.reroll.0',3),('round.0.first.feral-instinct.reroll.1',4),
         ('round.0.second.sea-shanty.leadership.0',6),('round.0.second.sea-shanty.leadership.1',6),
         ('round.0.second.attack.0.hit',1)],
        [('round.0.first.feral-instinct.reroll',True),('round.0.second.sea-shanty',True)])
    assert not result.state.first.feral_instinct_failed and len(result.attacks)==1


def test_electrical_sole_replacement_does_not_draw_unused_ordinary_priority_tie(precompiled):
    mutant,enemy=precompiled().first,precompiled().second
    result=run(mutant,enemy,start(mutant,enemy,charging=()),
        [('round.0.first.electrical-touch.attack.0.wound',1),
         ('round.0.first.electrical-touch.recharge',1,3),('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',True)])
    assert len(result.attacks)==2


def test_electrical_canonical_shallows_mutation_uses_s3_not_hero_strength_or_armour(precompiled):
    mutant=precompiled().first
    assert 'mechanic.electrical-touch' in mutant.global_effects.tags
    enemy=precompiled().second
    result=run(mutant,enemy,start(mutant,enemy),
        [('round.0.first.electrical-touch.attack.0.wound',3),
         ('round.0.first.electrical-touch.recharge',1,3),('round.0.second.attack.0.hit',1)],
        [('round.0.first.electrical-touch.forfeit.0',True)])
    assert mutant.characteristics.strength==4 and not result.attacks[0].wounded


def test_poetry_supplied_victorious_leader_bonus_consumes_first_test_not_first_failure(precompiled):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    leader,enemy=precompiled().first,precompiled().second
    state=start(leader,enemy)
    for key,expected in [('first-test',True),('second-test',False)]:
        dice=StrictDice([{'key':f'{key}.0','value':4},{'key':f'{key}.1','value':4}])
        policy=StrictDecisions([])
        passed,current=resolve_local_leadership(leader,state,dice,policy,key,first=True,return_state=True)
        dice.finish();policy.finish()
        assert passed is expected
        state=replace(state,first=current)
    assert 'poetry-first-leadership' in state.first.resources_spent


def test_songster_reroll_bonus_cannot_increase_leadership_above_ten(precompiled):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_core.models import LocalParticipant
    # Case 0 records the duel pair, case 1 the leadership probe pair.
    duel_case, leadership_case = precompiled(0), precompiled(1)
    recipient, enemy = duel_case.first, duel_case.second
    bard = leadership_case.second
    state=initialize_duel(recipient,enemy,StrictDice([]),context=DuelContext(charging=(),
        active_participant='first',nearby=(LocalParticipant('bard','first',bard),),
        distances=(('first','bard',6),)))
    dice=StrictDice([{'key':f'probe{suffix}','value':value} for suffix,value in
        [('.0',6),('.1',6),('.reroll.0',6),('.reroll.1',5)]])
    policy=StrictDecisions([{'key':'probe.reroll','value':True}])
    assert resolve_local_leadership(recipient,state,dice,policy,'probe',first=True) is False
    dice.finish();policy.finish()


def test_gaoler_declaration_replaces_all_timed_strikes_even_when_grapple_misses(precompiled):
    from mordheim_core.models import EffectSet
    # ``builders`` provenance: the plain foe was compiled before the gaoler.
    enemy=precompiled().first
    gaoler=replace(precompiled().second,
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks','rule.strikes-last-bite')),))
    state=initialize_duel(gaoler,enemy,StrictDice([]),context=DuelContext(
        charging=('second',),active_participant='second'))
    result=run(gaoler,enemy,state,
        [('round.0.second.attack.0.hit',1),('round.0.first.grapple.hit',1)],
        [('round.0.first.torturer-grapple',True)])
    assert len(result.attacks)==2 and not result.attacks[1].hit


def test_declared_black_hunger_still_backlashes_after_charge_fails_fear(precompiled):
    hungry,enemy=precompiled().first,precompiled().second
    result=run(hungry,enemy,start(hungry,enemy),
        [('round.0.first.fear.charge.0',6),('round.0.first.fear.charge.1',6),
         ('round.0.first.black-hunger.hits',1,3),('round.0.first.black-hunger.hit.0.wound',1)])
    assert not result.state.engaged and len(result.attacks)==1
    assert not result.attacks[0].wounded


def test_hypnotic_musk_keeps_supplied_goading_charge_exception_without_producer(precompiled):
    bearer=precompiled().first
    animal=precompiled().second
    result=run(animal,bearer,start(animal,bearer),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert len(result.attacks)==2 and result.state.engaged


def test_shanty_loses_one_ordinary_attack_without_erasing_natural_extra(precompiled):
    from mordheim_core.models import EffectSet
    singer=precompiled().first
    mutant=replace(precompiled().second,extra_attacks=(EffectSet(tags=('weapon.natural-attacks',)),))
    result=run(singer,mutant,start(singer,mutant),
        [('round.0.first.sea-shanty.leadership.0',6),('round.0.first.sea-shanty.leadership.1',6),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],
        [('round.0.first.sea-shanty',True)])
    assert len(result.attacks)==2


def test_electrical_replaces_remaining_extra_after_shanty_loses_ordinary_attack(precompiled):
    from mordheim_core.models import EffectSet
    singer=precompiled().first
    mutant=replace(precompiled().second,
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks',)),))
    result=run(singer,mutant,start(singer,mutant),
        [('round.0.first.sea-shanty.leadership.0',6),('round.0.first.sea-shanty.leadership.1',6),
         ('round.0.first.attack.0.hit',1),('round.0.second.electrical-touch.attack.0.wound',1),
         ('round.0.second.electrical-touch.recharge',1,3)],
        [('round.0.first.sea-shanty',True),('round.0.second.electrical-touch.forfeit.1',True)])
    assert len(result.attacks)==2 and result.attacks[1].hit


def test_explicit_no_contact_suppresses_melee_auras_and_blows_but_keeps_own_recovery(precompiled):
    fighter=precompiled().first
    enemy=precompiled().second
    state=start(fighter,enemy,contacts=())
    assert not state.engaged
    result=run(fighter,enemy,state,
        [('round.0.first.feral-instinct.0',3),('round.0.first.feral-instinct.1',4),
         ('round.0.first.black-hunger.hits',1,3),('round.0.first.black-hunger.hit.0.wound',1)])
    assert not result.state.engaged and len(result.attacks)==1
    assert result.state.round_index==1
    assert not result.attacks[0].wounded


def test_explicit_contact_keeps_normal_duel_without_inferring_from_charge(precompiled):
    fighter,enemy=precompiled().first,precompiled().second
    state=start(fighter,enemy,charging=(),contacts=(('first','second'),))
    assert state.engaged
    result=run(fighter,enemy,state,[('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert len(result.attacks)==2


def test_inquisitor_brand_is_dynamic_once_per_success_and_rechecks_every_combat_phase(precompiled):
    from mordheim_core.models import MutationOption
    # ``builders`` provenance: the plain target was compiled before the priest.
    target=precompiled().first
    priest=replace(precompiled().second,
        mutation_options=(MutationOption(12,stat_ops=(('toughness','halve-ceil',2),)),))
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
def test_inquisitor_does_not_roll_or_brand_excluded_enemy(precompiled, excluded):
    priest,target=precompiled().first,precompiled().second
    result=run(priest,target,start(priest,target),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert not result.state.second.mutations


def test_burning_body_end_every_turn_ignites_only_then_existing_own_recovery_extinguishes(precompiled):
    mutant,target=precompiled().first,precompiled().second
    result=run(mutant,target,start(mutant,target),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1),
         ('round.0.first.burning-body',4)])
    assert result.state.second.on_fire
    result=run(mutant,target,result.state,
        [('round.1.second.fire.extinguish',4),('round.1.first.attack.0.hit',1),
         ('round.1.second.attack.0.hit',1),('round.1.first.burning-body',3)])
    assert not result.state.second.on_fire


def test_ranger_herb_lore_only_supplied_no_contact_recovery_preserves_variant(precompiled):
    ranger,enemy=precompiled().first,precompiled().second
    state=start(ranger,enemy,contacts=())
    state=replace(state,first=replace(state.first,wounds=1))
    result=run(ranger,enemy,state,[('round.0.first.herb-lore',4)],
        [('round.0.first.herb-lore',True)])
    assert result.state.first.wounds==2 and result.attacks==()
    state=start(ranger,enemy)
    state=replace(state,first=replace(state.first,wounds=1))
    result=run(ranger,enemy,state,[('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert result.state.first.wounds==1


def test_poetry_supplied_one_turn_inspiration_changes_ws_and_attacks_then_expires(precompiled):
    recipient,enemy=precompiled().first,precompiled().second
    enemy=replace(enemy,characteristics=replace(enemy.characteristics,weapon_skill=7))
    result=run(recipient,enemy,start(recipient,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.first.attack.1.hit',1),
         ('round.0.second.attack.0.hit',1)])
    assert len(result.attacks)==3 and result.attacks[0].hit_target==4
    result=run(recipient,enemy,result.state,
        [('round.1.first.attack.0.hit',1),('round.1.second.attack.0.hit',1)])
    assert len(result.attacks)==2 and result.attacks[0].hit_target==5


def test_no_contact_keeps_actual_own_fire_recovery_hit_and_state(precompiled):
    victim,enemy=precompiled().first,precompiled().second
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


def test_canonical_dim_witted_promoted_leader_lends_seven_not_own_ten(precompiled):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    # Case 0 records the duel pair, case 1 the leadership probe pair.
    recipient, enemy = precompiled(0).first, precompiled(0).second
    leader=precompiled(1).second
    assert leader.characteristics.leadership==10
    state=initialize_duel(recipient,enemy,StrictDice([]),context=DuelContext(charging=(),
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


def test_canonical_ranger_recovery_heals_only_outside_contact(precompiled):
    ranger=precompiled().first
    # A supplied current +W advancement permits a living, injured self-healer.
    ranger=replace(ranger,characteristics=replace(ranger.characteristics,wounds=2))
    enemy=precompiled().second
    state=start(ranger,enemy,contacts=())
    state=replace(state,first=replace(state.first,wounds=1))
    result=run(ranger,enemy,state,[('round.0.first.herb-lore',4)],
        [('round.0.first.herb-lore',True)])
    assert result.state.first.wounds==2


def test_canonical_inquisitor_prepared_chart_reaches_live_combat_consumer(precompiled):
    priest=precompiled().first
    assert len(priest.mutation_options)==36
    target=precompiled().second
    result=run(priest,target,start(priest,target),
        [('round.0.first.inquisitor.judgement',6),('round.0.first.inquisitor.mutation.tens',1),
         ('round.0.first.inquisitor.mutation.units',2),('round.0.first.attack.0.hit',1),
         ('round.0.second.attack.0.hit',1)])
    assert result.state.second.toughness==2 and len(result.state.second.mutations)==1


def test_canonical_inquisitor_psychology_immunity_reuses_normal_fear_consumer(precompiled):
    priest=precompiled().first
    enemy=precompiled().second
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


def test_the_inquisitor_judgement_belongs_to_the_chosen_mark_alone(precompiled):
    priest=precompiled().first
    assert not priest.mutation_options
    target=precompiled().second
    result=run(priest,target,start(priest,target),
        [('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert not result.state.second.mutations


def test_canonical_nuttaz_only_supplied_required_attempt_is_compulsory(precompiled):
    nuttaz=precompiled().first
    with pytest.raises(ValueError,match='compulsory charge'):
        start(nuttaz,precompiled().second,charging=())
    assert start(nuttaz,precompiled().second).first_charged


def test_no_hand_attacks_retains_separate_late_bite_without_phantom_fist(precompiled):
    from mordheim_core.models import EffectSet
    # ``builders`` provenance: the plain foe was compiled before the mutant.
    enemy=precompiled().first
    mutant=replace(precompiled().second,
        extra_attacks=(EffectSet(tags=('weapon.natural-attacks','rule.strikes-last-bite')),))
    result=run(mutant,enemy,start(mutant,enemy),
        [('round.0.second.attack.0.hit',1),('round.0.first.last-bite.attack.0.hit',1)])
    assert len(result.attacks)==2


def test_inquisitor_subtable_roll_retains_priest_resource_at_live_round_hook(precompiled):
    priest=precompiled().first
    priest=replace(priest,global_effects=replace(priest.global_effects,
        tags=(*priest.global_effects.tags,'mechanic.ranalds-luck')))
    keys=['round.0.first.inquisitor.judgement',
        'round.0.first.inquisitor.mutation.tens','round.0.first.inquisitor.mutation.units']
    choices=[(f'{key}.ranalds-luck.{direction}',False) for key in keys for direction in ('plus','minus')]
    choices.append(('round.0.first.inquisitor.mutation.66.atrophy.ranalds-luck.plus',True))
    target=precompiled().second
    result=run(priest,target,start(priest,target),
        [(keys[0],6),(keys[1],6),(keys[2],6),('round.0.first.inquisitor.mutation.66.atrophy',4),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)],choices)
    assert result.state.second.atrophied_legs==1
    assert 'ranalds-luck' in result.state.first.resources_spent
    assert 'ranalds-luck' not in result.state.second.resources_spent


def test_cutting_out_of_supplied_net_spends_recovery_without_new_djinn_power(precompiled):
    djinn=precompiled().first
    enemy=precompiled().second
    result=run(djinn,enemy,start(djinn,enemy,charging=()),
        [('round.0.second.attack.0.hit',1),('round.0.first.attack.0.hit',1)])
    assert not result.state.first.netted and result.state.first.djinn_power is None
    assert len(result.attacks)==2


def test_personal_one_die_luck_prevents_rerolling_whole_leadership_test_again(precompiled):
    from mordheim_combat.modular.leadership import resolve_local_leadership
    fighter,enemy=precompiled().first,precompiled().second
    state=start(fighter,enemy)
    dice=StrictDice([{'key':key,'value':6} for key in ('probe.0','probe.0.reroll','probe.1')])
    choices=StrictDecisions([{'key':'probe.0.luck','value':True}])
    passed,current=resolve_local_leadership(fighter,state,dice,choices,'probe',first=True,return_state=True)
    dice.finish();choices.finish()
    assert not passed and 'luck' in current.resources_spent


def test_castoff_removes_carried_extra_hand_weapon_but_retains_innate_limb(precompiled):
    from mordheim_combat.modular.equipment import equipment_for_state
    from mordheim_core.models import EffectSet
    carried=EffectSet(tags=('weapon.sword','mutation.carried-weapon','mutation.hand.extra.0'))
    innate=EffectSet(tags=('weapon.natural-attacks','rule.great-claw','mutation.hand.extra.1'))
    fighter=replace(precompiled().first,extra_attacks=(carried,innate))
    state=replace(start(fighter,precompiled().second).first,equipment_cast_off=True)
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


def test_crimson_shade_has_no_effect_on_undead_or_the_possessed():
    # Printed item text: "Crimson Shade has no effect on Undead such as Vampires
    # and Zombies, or the Possessed." The living bearer is the control and the
    # suppressed consequence is the whole preparation: Strength, Movement and
    # the single 1D3 Initiative roll, not just its bonus.
    def bearer(**options):
        return compile_fighter(FighterBuild('mordheim',
            Characteristics(3, 3, 3, 2, 3, 1, movement=3, leadership=7),
            main_weapon_id='weapon.mace',
            preparation_ids=('preparation.crimson-shade',), **options))
    living=bearer()
    assert 'preparation.crimson-shade' in living.global_effects.tags
    assert living.global_effects.strength_bonus==1
    assert living.characteristics.movement==4
    dice=StrictDice([{'key':'probe.crimson-shade','value':3,'sides':3}])
    initialized=initialize_fighter(living,dice,'probe')
    dice.finish()
    assert initialized.initiative==6
    for nature in ('undead','possessed'):
        excluded=bearer(trait_overrides={'creature_kind':nature})
        assert 'preparation.crimson-shade' not in excluded.global_effects.tags,nature
        assert excluded.global_effects.strength_bonus==0,nature
        assert excluded.characteristics.movement==3,nature
        # No preparation die is requested at all: an empty strict tape passes
        # only when the bearer's nature removes the item's contribution.
        dice=StrictDice([])
        initialize_fighter(excluded,dice,'probe')
        dice.finish()


def test_magic_acorn_spends_its_single_first_round_auto_hit_across_the_round_loop(precompiled):
    # Printed item clause: "in the first round of every close combat the Hero
    # automatically hits with a single attack that was rolled as a miss." The
    # shape is proved at the attack level in test_defence_parries_and_ward;
    # here the canonical item binding must carry the spent resource through the
    # whole round loop, so the later round keeps the ordinary miss.
    acorn=precompiled().first
    enemy=precompiled().second
    assert 'mechanic.magic-acorn' in acorn.global_effects.tags
    result=run(acorn,enemy,start(acorn,enemy),
        [('round.0.first.attack.0.hit',1),('round.0.first.attack.0.wound',1),
         ('round.0.second.attack.0.hit',1)])
    assert [attack.hit for attack in result.attacks]==[True,False]
    assert 'magic-acorn' in result.state.first.resources_spent
    later=run(acorn,enemy,result.state,
        [('round.1.priority-tie',1),('round.1.second.attack.0.hit',1),
         ('round.1.first.attack.0.hit',1)])
    assert not any(attack.hit for attack in later.attacks)
    assert 'magic-acorn' in later.state.first.resources_spent


def test_canonical_aquatic_mutants_eye_stalks_reaver_sends_the_fear_consequence(precompiled):
    # Printed pool clause: "or eye stalks (counts as hideous)". The canonical
    # compiler route shallows-beasts-mim/buccaneer -> band--mutations-eye-stalks
    # must reach the shared causes-fear operator through a real round, not only
    # through hand-built tags.
    reaver=precompiled().first
    assert 'mechanic.causes-fear' in reaver.global_effects.tags
    enemy=precompiled().second
    # The charged enemy passes its Leadership test and attacks normally:
    # its own hit is measured against the ordinary WS target.
    result=run(reaver,enemy,start(reaver,enemy),
        [('round.0.second.fear.charged.0',3),('round.0.second.fear.charged.1',4),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',1)])
    assert not result.attacks[-1].hit and result.attacks[-1].hit_target==4
    # A failed test leaves the charged enemy natural-six-only in that round.
    failed=run(reaver,enemy,start(reaver,enemy),
        [('round.0.second.fear.charged.0',4),('round.0.second.fear.charged.1',4),
         ('round.0.first.attack.0.hit',1),('round.0.second.attack.0.hit',4)])
    assert not failed.attacks[-1].hit and failed.attacks[-1].hit_target==6
