"""Khemri p16: the worn Eye protects Abdul and restricts Undead attacks."""
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

PID = 'hireling.dramatis.abdul-alhazred-the-mad-sorcerer'


def tape(*values):
    return StrictDice([{'key': key, 'value': value} for key, value in values])


def abdul(worn=True):
    return compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b',
        profile_id=PID, defence_ids=('defence.eye-pendant',) if worn else ()))


def enemy(undead=True):
    return compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 3, 2, 1, leadership=7),
        main_weapon_id='weapon.mace', trait_overrides={'creature_kind': 'undead' if undead else 'living'}))


def initial(owner, foe):
    return initialize_duel(owner, foe, tape(), context=DuelContext(
        charging=('first',), active_participant='first'))


@pytest.mark.parametrize('ward,saved', [(3, False), (4, True)])
def test_printed_kit_compiles_and_worn_ward_uses_four_plus(ward, saved):
    owner, foe = abdul(), enemy(False)
    assert 'weapon.dagger' in owner.main_weapon.tags
    dice = tape(('a.hit', 4), ('a.wound', 4), ('a.special.ward', ward))
    result = resolve_reference_attack(foe, owner, initialize_fighter(foe, tape(), 'f'),
        initialize_fighter(owner, tape(), 'o'), foe.main_weapon, dice,
        key='a', decisions=StrictDecisions([]))
    dice.finish()
    assert result.saved is saved
    assert result.defender.wounds == (2 if saved else 1)


def test_undead_fail_despite_psychology_immunity_and_retry_next_turn():
    owner, foe = abdul(), enemy()
    foe = replace(foe, global_effects=replace(foe.global_effects,
        tags=(*foe.global_effects.tags, 'mechanic.psychology-immunity')))
    start = initial(owner, foe)
    assert 'mechanic.psychology-immunity' in foe.global_effects.tags
    dice = tape(('round.0.second.eye-pendant.0', 6), ('round.0.second.eye-pendant.1', 6),
                ('round.0.first.attack.0.hit', 1))
    blocked = resolve_round(owner, foe, start, dice, StrictDecisions([]))
    dice.finish()
    assert blocked.state.second.charm_attack_blocked and len(blocked.attacks) == 1
    dice = tape(('round.1.second.eye-pendant.0', 3), ('round.1.second.eye-pendant.1', 4),
                ('round.1.first.attack.0.hit', 1), ('round.1.second.attack.0.hit', 1))
    allowed = resolve_round(owner, foe, blocked.state, dice, StrictDecisions([]))
    dice.finish()
    assert not allowed.state.second.charm_attack_blocked and len(allowed.attacks) == 2


@pytest.mark.parametrize('worn,undead', [(True, False), (False, True)])
def test_living_enemy_or_unworn_pendant_needs_no_test(worn, undead):
    owner, foe = abdul(worn), enemy(undead)
    dice = tape(('round.0.first.attack.0.hit', 1), ('round.0.second.attack.0.hit', 1))
    result = resolve_round(owner, foe, initial(owner, foe), dice, StrictDecisions([]))
    dice.finish()
    assert len(result.attacks) == 2
    if not worn:
        assert 'defence.eye-pendant' not in owner.global_effects.tags
        assert owner.global_effects.ward_save == 7


def test_discarding_the_item_retires_both_ward_and_attack_restriction():
    owner = abdul()
    current = replace(initialize_fighter(owner, tape(), 'a'), equipment_cast_off=True)
    stripped = equipment_for_state(owner, current, first_round=True)
    assert stripped.global_effects.ward_save == 7
    assert 'defence.eye-pendant' not in stripped.global_effects.tags
