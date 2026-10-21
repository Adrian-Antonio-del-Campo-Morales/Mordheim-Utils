"""Source Mazzalupo Ye Give Way: supplied persistent personal results only."""
from dataclasses import replace
import pytest
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import _combined_effect, prepare_hit_context
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_fighter, initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

REFUSED = 'condition.ye-give-way-refused'
WON = 'condition.ye-give-way-victorious'


def tape(*values):
    return StrictDice([{'key': key, 'value': value} for key, value in values])


def noble(*conditions):
    return compile_fighter(FighterBuild('mordheim', band_id='mazzalupo-web', profile_id='fallen-noble',
        main_weapon_id='weapon.mace', condition_ids=conditions))


def hero(*conditions):
    return compile_fighter(FighterBuild('mordheim', Characteristics(4, 3, 4, 4, 2, 1),
        main_weapon_id='weapon.mace', condition_ids=conditions, trait_overrides={'fighter_kind': 'hero'}))


@pytest.mark.phase3_rules
@pytest.mark.parametrize('conditions,hit,wounded,strength', [((), False, False, 3),
    ((WON,), True, True, 4), ((WON, WON), True, True, 4)])
def test_source_hit_and_strength_boundaries_without_stacking(conditions, hit, wounded, strength):
    owner, foe = noble(*conditions), hero()
    dice = tape(('a.hit', 3), *( [('a.wound', 4)] if hit else []))
    result = resolve_reference_attack(owner, foe, initialize_fighter(owner, tape(), 'o'),
        initialize_fighter(foe, tape(), 'f'), owner.main_weapon, dice, key='a', decisions=StrictDecisions([]))
    dice.finish()
    assert owner.characteristics.strength == strength
    assert result.hit is hit and result.wounded is wounded


@pytest.mark.phase3_rules
def test_refusal_is_non_stacking_persistent_and_does_not_cancel_later_duels():
    owner, foe = hero(REFUSED, REFUSED), hero()
    assert owner.characteristics.strength == 3
    start = initialize_duel(owner, foe, tape(), context=DuelContext(charging=('first',), active_participant='first'))
    for index in range(2):
        dice = tape(*([('round.1.priority-tie', 4)] if index else []),
            (f'round.{index}.first.attack.0.hit', 4), (f'round.{index}.second.attack.0.hit', 1))
        result = resolve_round(owner, foe, start, dice, StrictDecisions([]))
        dice.finish()
        assert result.state.engaged and not result.attacks[0].hit
        assert not result.state.first.resources_spent
        start = result.state
    # Both historical outcomes can coexist; their distinct hit modifiers cancel.
    combined = noble(REFUSED, WON)
    dice = tape(('a.hit', 4), ('a.wound', 1))
    attack = resolve_reference_attack(combined, foe, initialize_fighter(combined, tape(), 'a'),
        initialize_fighter(foe, tape(), 'b'), combined.main_weapon, dice, key='a', decisions=StrictDecisions([]))
    dice.finish()
    assert attack.hit and combined.characteristics.strength == 4


@pytest.mark.phase3_rules
@pytest.mark.parametrize('condition', [REFUSED, WON])
def test_modifiers_do_not_leak_into_non_melee_contexts(condition):
    owner, foe = (noble(condition) if condition == WON else hero(condition)), hero()
    a, b = initialize_fighter(owner, tape(), 'a'), initialize_fighter(foe, tape(), 'b')
    context = prepare_hit_context(owner, foe, a, b, owner.main_weapon,
        _combined_effect(owner, owner.main_weapon), first_round=False, charging=False,
        key='a', melee_attack=False)
    assert context.modifier == 0


@pytest.mark.phase2_construction
def test_recipient_guards_and_unselected_noble_has_no_award():
    with pytest.raises(ValueError, match='Hero recipient'):
        compile_fighter(FighterBuild('mordheim', Characteristics(3,3,3,2,2,1), condition_ids=(REFUSED,)))
    with pytest.raises(ValueError, match='Fallen Noble recipient'):
        hero(WON)
    assert noble().characteristics.strength == 3
    assert REFUSED not in noble().global_effects.tags and WON not in noble().global_effects.tags
