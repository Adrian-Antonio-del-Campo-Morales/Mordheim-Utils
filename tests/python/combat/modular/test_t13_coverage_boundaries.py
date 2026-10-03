"""Source-preserving F040 witnesses for a formerly covered attack boundary."""
from dataclasses import replace
from pathlib import Path

import pytest

from mordheim_combat.modular import attacks
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import Condition
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


@pytest.mark.parametrize('removed', ['attacker', 'defender'])
def test_removed_participant_cannot_start_an_attack_or_consume_requests(removed):
    fighter = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1),
                                          main_weapon_id='weapon.rapier'))
    dice, decisions = StrictDice([]), StrictDecisions([])
    active = initialize_fighter(fighter, dice, 'init')
    inactive = replace(active, condition=Condition.OUT, wounds=0)
    first, second = (inactive, active) if removed == 'attacker' else (active, inactive)
    result = attacks.resolve_reference_attack(fighter, fighter, first, second,
        fighter.main_weapon, dice, key='removed', decisions=decisions)
    dice.finish()
    decisions.finish()
    assert result.attacker == first and result.defender == second
    assert not result.hit and not result.wounded and not result.barrage_available
    assert result.damage == result.damage_already_reacted == 0


def test_removed_participant_witness_detects_guard_removal(monkeypatch):
    source = Path(attacks.__file__).read_text(encoding='utf-8')
    guard = ('    if not attacker_state.active or not defender_state.active:\n'
             '        return AttackOutcome(attacker_state, defender_state)\n')
    assert source.count(guard) == 1
    namespace = {'__name__': 'inactive_attack_guard_mutant'}
    exec(compile(source.replace(guard, '', 1), '<isolated inactive attack mutant>', 'exec'), namespace)
    monkeypatch.setattr(attacks, '_resolve_reference_attack_once', namespace['_resolve_reference_attack_once'])
    with pytest.raises(AssertionError):
        test_removed_participant_cannot_start_an_attack_or_consume_requests('attacker')
