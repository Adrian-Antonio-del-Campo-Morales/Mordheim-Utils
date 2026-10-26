"""Printed Blood Dragon Killing Blow through canonical attacks and pools."""
import sys
from dataclasses import replace

import pytest

from mordheim_combat.kernel import require_optimized_support
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.state import initialize_fighter
from tests.engines.shared.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, FighterBuild


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
def test_canonical_six_wounds_once_without_a_wound_or_critical_die(precompiled, profile):
    compiled = precompiled()
    a, foe = compiled.first, compiled.second
    assert a.global_effects.tags.count(TAG) == 1
    result = attack(a, foe, [('a.hit', 6)])
    assert result.damage == 1 and result.defender.wounds == 3
    assert not result.critical and result.attacker.critical_available
    # Wights and Grave Guards also carry pending native local modifiers
    # (causes-fear/psychology-immunity) that the gate names before Killing
    # Blow. The invariant under test is that the entry refuses before it can
    # silently drop the behaviour, not which pending capability is named.
    with pytest.raises(ValueError, match='modular engine'):
        require_optimized_support(a, foe)


def test_adjacent_hit_and_foreign_profile_still_roll_to_wound(precompiled):
    # ``first`` is the recorded Wight and ``second`` the skeleton warriors; the
    # plain opponent they strike is the synthetic control the corpus lacks.
    compiled = precompiled()
    wights, skeletons = compiled.first, compiled.second
    for a, face in ((wights, 5), (skeletons, 6)):
        result = attack(a, opponent(), [('a.hit', face), ('a.wound', 1)])
        assert result.damage == 0 and result.defender.wounds == 4
    assert TAG not in skeletons.global_effects.tags


@pytest.mark.parametrize('options,key,face', [
    ({'armour': 'armour.heavy-armour'}, 'a.armour', 6),
    ({'skills': ('skill.step-aside',)}, 'a.special.ward', 5),
    ({'skills': ('skill.regeneration',)}, 'a.special.regeneration', 4),
    ({'defences': ('defence.lucky-charm',)}, 'a.lucky-charm', 4),
])
def test_source_saves_and_prior_hit_defences_still_apply(precompiled, options, key, face):
    compiled = precompiled()
    result = attack(compiled.first, compiled.second, [('a.hit', 6), (key, face)])
    assert result.saved and result.damage == 0 and result.defender.wounds == 4


def test_automatic_hit_is_not_a_natural_six(precompiled):
    compiled = precompiled()
    result = attack(compiled.first, compiled.second, [('a.wound', 1)])
    assert result.hit and result.damage == 0


def test_free_selection_lotus_keeps_its_explicit_critical_attempt(precompiled):
    # A supported free-selection composition, not canonical Blood Dragon access
    # to poison. Lotus's existing critical attempt remains distinct from the
    # Killing Blow clause, which does not itself grant a wound die.
    compiled = precompiled()
    a, b = compiled.first, compiled.second
    result = attack(a, b, [('a.hit', 6), ('a.wound', 6), ('a.critical', 3)])
    assert result.critical and result.damage == 2
    b = replace(b, global_effects=replace(b.global_effects, poison_immunity=True))
    immune = attack(a, b, [('a.hit', 6)])
    assert immune.damage == 1 and not immune.critical


def test_pool_keeps_per_hit_trigger_and_forbids_even_exceptional_six_parries(precompiled):
    # Existing exceptional parry contract can match six; Killing Blow overrides
    # that permission for its triggering hit only. The lower hit remains parryable.
    compiled = precompiled()
    a, b = compiled.first, compiled.second
    dice = StrictDice([{'key': k, 'value': v} for k, v in [
        ('p.attack.0.hit', 6), ('p.attack.1.hit', 4), ('p.attack.1.parry', 4)]])
    decisions = StrictDecisions([])
    _, final, outcomes = _resolve_attack_pool(a, b, state(a), state(b), 2, dice,
        key='p', first_round=False, charging=False, decisions=decisions)
    dice.finish()
    decisions.finish()
    assert [o.damage for o in outcomes] == [1, 0]
    assert outcomes[1].parried and final.wounds == 3
