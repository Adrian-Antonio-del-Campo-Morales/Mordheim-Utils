"""Cripples p149: permanent supplied outcomes, not a fresh creation roll per duel."""
import pytest
from mordheim_combat.modular.psychology import resolve_stupidity
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def tape(*values):
    return StrictDice([{'key': key, 'value': value} for key, value in values])


def cripple(result, **options):
    conditions = (f'condition.disability-{result}',) if result else ()
    return compile_fighter(FighterBuild('mordheim', collection='trollheim',
        band_id='chaos-streets-mordheim-inhabitants', profile_id='cripples',
        main_weapon_id='weapon.club', condition_ids=conditions, **options))


def foe():
    return compile_fighter(FighterBuild('mordheim', Characteristics(2,3,3,2,2,1)))


@pytest.mark.parametrize('result,expected', [(1,(3,2,2,3,3,2)),(2,(4,3,1,3,3,2)),
    (3,(4,3,2,3,3,1)),(4,(4,3,2,3,2,2)),(5,(4,3,2,2,3,2)),(6,(4,3,2,3,3,2))])
@pytest.mark.phase2_construction
def test_each_source_result_is_compiled_once_and_initializes_without_a_table_roll(result, expected):
    owner = cripple(result)
    stats = owner.characteristics
    assert (stats.movement, stats.initiative, stats.weapon_skill, stats.strength,
            stats.toughness, owner.ballistic_skill) == expected
    dice = tape()
    state = initialize_duel(owner, foe(), dice, context=DuelContext(charging=(), active_participant='first'))
    dice.finish()
    assert f'disability.{result}' in state.first.resources_spent
    assert state.first.weapon_skill == stats.weapon_skill and state.first.strength == stats.strength


@pytest.mark.parametrize('offhand', ['weapon.dagger','defence.shield'])
@pytest.mark.phase2_construction
def test_parkinson_rejects_a_second_weapon_or_shield(offhand):
    with pytest.raises(ValueError, match='at most|forbidden'):
        cripple(2, off_hand_id=offhand)


@pytest.mark.phase2_construction
def test_non_parkinson_result_does_not_inherit_the_restriction():
    assert cripple(5, off_hand_id='weapon.dagger').off_hand_attacks


@pytest.mark.phase2_construction
def test_table_result_is_required_unique_and_recipient_specific():
    with pytest.raises(ValueError, match='permanent supplied result'):
        cripple(None)
    with pytest.raises(ValueError, match='choose only one'):
        compile_fighter(FighterBuild('mordheim', Characteristics(2,3,3,2,2,1),
            skill_ids=('mechanic.disability',), condition_ids=('condition.disability-1','condition.disability-2')))
    with pytest.raises(ValueError, match='requires a Cripple'):
        compile_fighter(FighterBuild('mordheim', Characteristics(2,3,3,2,2,1), condition_ids=('condition.disability-2',)))


@pytest.mark.phase3_rules
def test_head_injury_hero_proximity_is_current_and_has_a_qualified_recipient():
    owner = compile_fighter(FighterBuild('mordheim', Characteristics(2,3,3,2,2,1,leadership=7),
        skill_ids=('mechanic.disability',),
        condition_ids=('condition.disability-6','condition.disability-hero-nearby')))
    dice = tape()
    state = initialize_duel(owner, foe(), dice, context=DuelContext(charging=(), active_participant='first'))
    result = resolve_stupidity(owner, foe(), state, dice, StrictDecisions([]))
    dice.finish()
    assert not result.first.stupidity_failed
    # Removing current proximity does not cure the permanent Head Injury.
    absent = compile_fighter(FighterBuild('mordheim', Characteristics(2,3,3,2,2,1,leadership=7),
        skill_ids=('mechanic.disability',), condition_ids=('condition.disability-6',)))
    dice = tape(('round.0.first.stupidity.0',6),('round.0.first.stupidity.1',6))
    assert resolve_stupidity(absent, foe(), state, dice, StrictDecisions([])).first.stupidity_failed
    dice.finish()
    with pytest.raises(ValueError, match='requires Head Injury'):
        compile_fighter(FighterBuild('mordheim', Characteristics(2,3,3,2,2,1),
            skill_ids=('mechanic.disability',), condition_ids=('condition.disability-2','condition.disability-hero-nearby')))


@pytest.mark.parametrize('distance,side,condition,exempt', [(6,'first','standing',True),
    (6.01,'first','standing',False),(6,'second','standing',False),(6,'first','out',False)])
@pytest.mark.phase3_rules
def test_head_injury_reads_the_six_inch_boundary_side_and_active_hero(distance, side, condition, exempt):
    from mordheim_core.models import LocalParticipant
    owner = cripple(6)
    provider = compile_fighter(FighterBuild('mordheim', Characteristics(3,3,3,2,2,1),
        trait_overrides={'fighter_kind':'hero'}))
    dice = tape() if exempt else tape(('round.0.first.stupidity.0',6),('round.0.first.stupidity.1',6))
    state = initialize_duel(owner, foe(), tape(), context=DuelContext(charging=(),
        active_participant='first', nearby=(LocalParticipant('hero',side,provider,condition=condition),),
        distances=(('first','hero',distance),)))
    assert resolve_stupidity(owner, foe(), state, dice, StrictDecisions([])).first.stupidity_failed is not exempt
    dice.finish()
