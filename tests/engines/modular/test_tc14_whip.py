"""TC14 p11: the actual whip, optional rerolls and disarming a physical piece."""
import sys
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


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


def tape(*rolls):
    return StrictDice([{'key': key, 'value': value} for key, value in rolls])


def choices(*values):
    return StrictDecisions([{'key': key, 'value': value} for key, value in values])


def heinrich():
    return compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b',
        profile_id='hireling.dramatis.heinrich-altdorf-schmidt',
        main_weapon_id='weapon.whip-tc14', armour_id='armour.light-armour'))


def enemy(**options):
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id=options.pop('main_weapon_id', 'weapon.mace'), **options))


def state(fighter):
    return initialize_fighter(fighter, tape(), 'init')


def strike(owner, foe, rolls, decisions, *, key='r', defender_state=None):
    dice = tape(*rolls)
    result = resolve_reference_attack(owner, foe, state(owner), defender_state or state(foe),
        owner.main_weapon, dice, key=key, decisions=decisions)
    dice.finish(); decisions.finish()
    return result


@pytest.mark.phase3_rules
@pytest.mark.parametrize('wound,saved', [(4, False), (5, True)])
def test_normal_whip_hit_uses_minus_one_strength_no_parry_and_plus_one_enemy_save(precompiled, wound, saved):
    compiled = precompiled()
    owner, foe = compiled.first, compiled.second
    rolls = [('r.hit', 4), ('r.wound', wound)]
    if saved:
        rolls.append(('r.armour', 5))
    result = strike(owner, foe, rolls,
        choices(('r.whip-disarm.main', False), ('r.whip-master', False)))
    assert result.saved == saved and result.wounded == saved


@pytest.mark.phase3_rules
def test_whip_master_can_repeat_a_success_and_must_keep_the_worse_result_without_spending(precompiled):
    compiled = precompiled()
    result = strike(compiled.first, compiled.second, [('r.hit', 4), ('r.hit.reroll', 1)],
        choices(('r.whip-disarm.main', False), ('r.whip-master', True)))
    assert not result.hit and not result.attacker.resources_spent


@pytest.mark.phase4_modular
@pytest.mark.parametrize('other', ['ordinary', 'oracle', 'scryer'])
def test_whip_master_never_adds_a_third_roll(precompiled, other):
    compiled = precompiled()
    owner, foe = compiled.first, compiled.second
    initial_choices = [('r.whip-disarm.main', False)]
    if other == 'ordinary':
        owner = replace(owner, global_effects=replace(owner.global_effects, reroll_hits=True))
    else:
        owner = replace(owner, global_effects=replace(owner.global_effects,
            tags=(*owner.global_effects.tags, f'mechanic.{other}')))
        initial_choices.append((f'r.hit.{"one-roll-reroll" if other == "oracle" else "scryer"}', True))
    if other == 'scryer':
        initial_choices.append(('r.wound.scryer', False))
    rolls = [('r.hit', 1), ('r.hit.scryer.reroll' if other == 'scryer' else 'r.hit.reroll', 4),
             ('r.wound', 1)]
    result = strike(owner, foe, rolls, choices(*initial_choices))
    assert result.hit and not result.wounded


@pytest.mark.phase3_rules
@pytest.mark.parametrize('hold,dropped', [(3, True), (5, False)])
def test_disarm_always_grants_one_hold_attempt_without_wounding_or_using_normal_parries(precompiled, hold, dropped):
    compiled = precompiled()
    # mace: no native parry, no shield, no armour
    result = strike(compiled.first, compiled.second, [('r.hit', 4), ('r.disarm-hold', hold)],
        choices(('r.whip-disarm.main', True), ('r.whip-master', False)))
    assert ('main' in result.defender.broken_hands) == dropped
    assert result.defender.wounds == 3 and not result.wounded
    assert result.defender.parries_remaining == 0


@pytest.mark.phase3_rules
def test_two_disarms_drop_the_active_weapon_then_its_distinct_carried_backup(precompiled):
    compiled = precompiled()
    owner, original = compiled.first, compiled.second
    first = strike(owner, original, [('a.hit', 4), ('a.disarm-hold', 3)],
        choices(('a.whip-disarm.main', True), ('a.whip-master', False)), key='a')
    armed = equipment_for_state(original, first.defender, first_round=True)
    assert 'weapon.sword' in armed.main_weapon.tags and armed.main_hand_slot.startswith('backup.')
    slot = armed.main_hand_slot
    second = strike(owner, armed, [('b.hit', 4), ('b.disarm-hold', 3)],
        choices((f'b.whip-disarm.{slot}', True), ('b.whip-master', False)),
        key='b', defender_state=first.defender)
    unarmed = equipment_for_state(original, second.defender, first_round=False)
    assert 'weapon.fist' in unarmed.main_weapon.tags
    assert second.defender.broken_hands == frozenset({'main', slot})


@pytest.mark.phase2_construction
def test_indestructible_weapon_is_not_offered_as_a_disarm_target(precompiled):
    compiled = precompiled()
    result = strike(compiled.first, compiled.second,
        [('r.hit', 4), ('r.wound', 1)], choices(('r.whip-master', False)))
    assert not result.defender.broken_hands


@pytest.mark.phase3_rules
def test_pool_preserves_the_declaration_without_asking_again_or_rolling_to_wound(precompiled):
    compiled = precompiled()
    owner, foe = compiled.first, compiled.second
    dice = tape(('p.attack.0.hit', 4), ('p.attack.0.disarm-hold', 3))
    decisions = choices(('p.attack.0.whip-disarm.main', True), ('p.attack.0.whip-master', False))
    _, defender, outcomes = _resolve_attack_pool(owner, foe, state(owner), state(foe), 1, dice,
        key='p', first_round=True, charging=False, decisions=decisions)
    dice.finish(); decisions.finish()
    assert defender.broken_hands == frozenset({'main'}) and defender.wounds == 3
    assert len(outcomes) == 1 and not outcomes[0].wounded


@pytest.mark.phase3_rules
@pytest.mark.parametrize('species', ['snake', 'serpent'])
def test_snake_fear_is_opponent_qualified_and_does_not_make_heinrich_cause_fear(species):
    owner = heinrich()
    snake = enemy(trait_overrides={'species': species})
    animal = enemy(trait_overrides={'fauna_animal_kind': 'ordinary'})
    assert causes_fear(snake, owner)
    assert not causes_fear(owner, snake)
    assert not causes_fear(snake, enemy())
    assert not causes_fear(animal, owner)


@pytest.mark.phase3_rules
@pytest.mark.parametrize('receiving', [False, True])
def test_canonical_snake_fear_reaches_charges_and_the_actual_round(precompiled, receiving):
    compiled = precompiled()
    owner, snake = compiled.first, compiled.second
    initial = initialize_duel(owner, snake, tape(), context=DuelContext(
        charging=('second',) if receiving else ('first',), active_participant='first'))
    suffix = 'charged' if receiving else 'charge'
    prefix = f'round.0.first.fear.{suffix}'
    dice = tape((f'{prefix}.0', 6), (f'{prefix}.1', 6))
    decisions = choices((f'{prefix}.0.luck', False), (f'{prefix}.1.luck', False))
    if receiving:
        resolved = resolve_fear(owner, snake, initial, dice, decisions)
        assert resolved.first.fear_hit_sixes
    else:
        resolved = resolve_round(owner, snake, initial, dice, decisions)
        assert not resolved.attacks and not resolved.state.engaged
        assert 'first' in resolved.state.failed_charges
    dice.finish(); decisions.finish()


@pytest.mark.phase3_rules
def test_tc14_reach_does_not_inherit_the_other_whips_charge_bonus(precompiled):
    compiled = precompiled()
    owner, foe = compiled.first, compiled.second
    dice = tape(('p.attack.0.hit', 1))
    decisions = choices(('p.attack.0.whip-disarm.main', False), ('p.attack.0.whip-master', False))
    _, _, outcomes = _resolve_attack_pool(owner, foe, state(owner), state(foe), 1, dice,
        key='p', first_round=True, charging=True, decisions=decisions)
    dice.finish(); decisions.finish()
    assert len(outcomes) == 1


@pytest.mark.phase4_modular
@pytest.mark.parametrize('off_hand', [False, True])
def test_disarmed_opponent_replies_with_surviving_weapon_in_the_same_round(precompiled, off_hand):
    compiled = precompiled()
    owner, foe = compiled.first, compiled.second
    initial = initialize_duel(owner, foe, tape(), context=DuelContext(
        charging=('first',), active_participant='first'))
    dice = tape(('round.0.first.attack.0.hit', 4), ('round.0.first.attack.0.disarm-hold', 3),
                ('round.0.second.attack.0.hit', 4), ('round.0.second.attack.0.wound', 3))
    decisions = choices(('round.0.first.attack.0.whip-disarm.main', True),
                        ('round.0.first.attack.0.whip-master', False))
    result = resolve_round(owner, foe, initial, dice, decisions)
    dice.finish(); decisions.finish()
    # Backup mace S3 fails on 3; the discarded rune sword's S4 would wound.
    # Losing a second weapon also retires its extra attack.
    assert result.state.first.wounds == owner.characteristics.wounds
    assert result.state.second.broken_hands == frozenset({'main'})
    assert len(result.attacks) == 2 and not result.attacks[-1].wounded


@pytest.mark.phase3_rules
@pytest.mark.parametrize('hit,hold,dropped', [(6, 6, True), (4, 5, False)])
def test_hold_attempt_is_one_roll_even_against_a_six_or_overwhelming_strength(precompiled, hit, hold, dropped):
    compiled = precompiled()
    owner, foe = compiled.first, compiled.second
    result = strike(owner, foe, [('r.hit', hit), ('r.disarm-hold', hold)],
        choices(('r.whip-disarm.main', True)))
    assert ('main' in result.defender.broken_hands) == dropped
    assert result.defender.wounds == 3
