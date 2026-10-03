"""L06: printed Blood Dragon Killing Blow through canonical attacks and pools."""
from dataclasses import replace

import pytest

from mordheim_combat.kernel import require_optimized_support
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild

TAG = 'mechanic.killing-blow'


def fighter(profile):
    return compile_fighter(FighterBuild('mordheim', band_id='blood-dragons-mou',
        profile_id=profile, main_weapon_id='weapon.mace'))


def opponent(*, ws=3, armour='armour.no-armour', skills=(), defences=(), weapon='weapon.mace'):
    # Explicit free-selection duel controls, not claimed canonical loadouts.
    return compile_fighter(FighterBuild('mordheim', Characteristics(ws, 3, 4, 4, 3, 1),
        main_weapon_id=weapon, armour_id=armour, skill_ids=skills,
        defence_ids=defences))


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, 'init')
    dice.finish()
    return result


def attack(a, b, tape):
    dice = StrictDice([{'key': k, 'value': v} for k, v in tape])
    result = resolve_reference_attack(a, b, state(a), state(b), a.main_weapon, dice, key='a')
    dice.finish()
    return result


@pytest.mark.parametrize('profile', ['wights', 'grave-guards'])
def test_canonical_six_wounds_once_without_a_wound_or_critical_die(profile):
    a = fighter(profile)
    assert a.global_effects.tags.count(TAG) == 1
    result = attack(a, opponent(), [('a.hit', 6)])
    assert result.damage == 1 and result.defender.wounds == 3
    assert not result.critical and result.attacker.critical_available
    with pytest.raises(ValueError, match='Killing Blow'):
        require_optimized_support(a, opponent())


def test_adjacent_hit_and_foreign_profile_still_roll_to_wound():
    for a, face in ((fighter('wights'), 5), (fighter('skeleton-warriors'), 6)):
        result = attack(a, opponent(), [('a.hit', face), ('a.wound', 1)])
        assert result.damage == 0 and result.defender.wounds == 4
    assert TAG not in fighter('skeleton-warriors').global_effects.tags


@pytest.mark.parametrize('options,key,face', [
    ({'armour': 'armour.heavy-armour'}, 'a.armour', 6),
    ({'skills': ('skill.step-aside',)}, 'a.special.ward', 5),
    ({'skills': ('skill.regeneration',)}, 'a.special.regeneration', 4),
    ({'defences': ('defence.lucky-charm',)}, 'a.lucky-charm', 4),
])
def test_source_saves_and_prior_hit_defences_still_apply(options, key, face):
    result = attack(fighter('wights'), opponent(**options), [('a.hit', 6), (key, face)])
    assert result.saved and result.damage == 0 and result.defender.wounds == 4


def test_automatic_hit_is_not_a_natural_six():
    result = attack(fighter('wights'), opponent(ws=0), [('a.wound', 1)])
    assert result.hit and result.damage == 0


def test_free_selection_lotus_keeps_its_explicit_critical_attempt():
    # A supported free-selection composition, not canonical Blood Dragon access
    # to poison. Lotus's existing critical attempt remains distinct from the
    # Killing Blow clause, which does not itself grant a wound die.
    a = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 3, 1),
        main_weapon_id='weapon.mace', main_poison_id='poison.black-lotus', skill_ids=(TAG,)))
    result = attack(a, opponent(), [('a.hit', 6), ('a.wound', 6), ('a.critical', 3)])
    assert result.critical and result.damage == 2
    b = opponent()
    b = replace(b, global_effects=replace(b.global_effects, poison_immunity=True))
    immune = attack(a, b, [('a.hit', 6)])
    assert immune.damage == 1 and not immune.critical


def test_pool_keeps_per_hit_trigger_and_forbids_even_exceptional_six_parries():
    a, b = fighter('wights'), opponent(weapon='weapon.sword')
    # Existing exceptional parry contract can match six; Killing Blow overrides
    # that permission for its triggering hit only. The lower hit remains parryable.
    b = replace(b, global_effects=replace(b.global_effects,
        tags=(*b.global_effects.tags, 'rule.blood-dragon-sword-master', 'skill.swordmaster')))
    dice = StrictDice([{'key': k, 'value': v} for k, v in [
        ('p.attack.0.hit', 6), ('p.attack.1.hit', 4), ('p.attack.1.parry', 4)]])
    decisions = StrictDecisions([])
    _, final, outcomes = _resolve_attack_pool(a, b, state(a), state(b), 2, dice,
        key='p', first_round=False, charging=False, decisions=decisions)
    dice.finish()
    decisions.finish()
    assert [o.damage for o in outcomes] == [1, 0]
    assert outcomes[1].parried and final.wounds == 3
