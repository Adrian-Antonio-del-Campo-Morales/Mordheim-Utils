"""Private Sleuth Scryer (watchmen-mim) — D13-style focal discriminators.

The printed rule: "A Sleuth can re-roll any rolls in close combat (the second
result must be accepted)."  The dice the rule touches stay her own; the player
chooses per roll and the second result always stands, so nothing is spent and
a roll that was already re-rolled (by her, by Luck or by the oracle reroll)
is never repeated.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.aftermath import _react_to_wound
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.psychology import resolve_fear
from mordheim_combat.modular.rounds import resolve_crude_belch
from mordheim_combat.modular.state import AttackOutcome, initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import ScriptedDice
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def sleuth(**options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="watchmen-mim", profile_id="private-sleuth",
        main_weapon_id="weapon.sword", **options))


def opponent(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.sword", **options))


def state(fighter, side="a"):
    dice = StrictDice([])
    result = initialize_fighter(fighter, dice, side)
    dice.finish()
    return result


def strike(atk, dfn, rolls, decisions):
    init = StrictDice([])
    first, second = initialize_fighter(atk, init, "a"), initialize_fighter(dfn, init, "d")
    init.finish()
    dice = StrictDice([{"key": "x." + key, "value": value} for key, value in rolls])
    chosen = StrictDecisions([{"key": "x." + key, "value": value}
                              for key, value in decisions])
    result = resolve_reference_attack(atk, dfn, first, second, atk.main_weapon,
                                      dice, key="x", decisions=chosen)
    dice.finish()
    chosen.finish()
    return result


@pytest.mark.phase2_construction
def test_the_sleuth_project_her_scryer_binding_and_rerolls_her_own_hit_die():
    hers = sleuth()
    assert "mechanic.scryer" in hers.global_effects.tags


@pytest.mark.phase3_rules
def test_initialisation_and_preparations_never_request_a_scryer_decision():
    # A real initialisation that actually rolls a die (the Crimson Shade
    # preparation roll) runs through the OwnedRollDice wrapper as well, but a
    # non-combat site must never ask for a Scryer choice: an empty decision
    # list fails loudly if the wrapper offers one.
    from mordheim_combat.modular.state import initialize_fighter
    hers = sleuth(preparation_ids=("preparation.crimson-shade",))
    dice = StrictDice([{"key": "a.crimson-shade", "value": 3, "sides": 3}])
    choices = StrictDecisions([])
    initialize_fighter(hers, dice, "a", decisions=choices)
    dice.finish()
    choices.finish()


@pytest.mark.phase3_rules
def test_scryer_reroll_needs_the_players_choice_and_sends_no_resources():
    hers = sleuth()
    result = strike(hers, opponent(), [("hit", 1), ("hit.scryer.reroll", 5),
                                       ("parry", 1), ("wound", 4)],
                    [("hit.scryer", True), ("wound.scryer", False)])
    assert result.hit
    assert "scryer" not in result.attacker.resources_spent


@pytest.mark.phase3_rules
def test_declining_the_choice_keeps_the_first_roll():
    hers = sleuth()
    result = strike(hers, opponent(), [("hit", 1)], [("hit.scryer", False)])
    assert not result.hit


@pytest.mark.phase3_rules
def test_the_second_result_must_be_accepted_even_when_it_is_worse():
    hers = sleuth()
    result = strike(hers, opponent(), [("hit", 5), ("hit.scryer.reroll", 1)],
                    [("hit.scryer", True)])
    assert not result.hit


@pytest.mark.phase3_rules
def test_the_sleuth_rerolls_her_own_parry_die_but_not_the_attackers_dice():
    # The attacking opponent's dice belong to the opponent: the defending
    # Sleuth never receives a scryer decision on them, and her own parry die
    # may be re-rolled once.
    foe = opponent()
    hers = sleuth()
    result = strike(foe, hers, [("hit", 4), ("parry", 1), ("parry.scryer.reroll", 6)],
                    [("parry.scryer", True)])
    assert result.parried


@pytest.mark.phase4_modular
def test_a_roll_already_rerolled_is_never_rerolled_again():
    # The oracle reroll consumes the attack's once-per-battle reroll and its
    # .reroll key; the Scryer must not duplicate it on the same die, so the
    # decision list carries no scryer choice for that roll.
    hers = sleuth(special_rule_ids=())
    from mordheim_core.models import EffectSet
    from dataclasses import replace as _replace
    hers = _replace(hers, global_effects=_replace(hers.global_effects,
        tags=(*hers.global_effects.tags, "mechanic.oracle")))
    result = strike(hers, opponent(), [("hit", 1), ("hit.reroll", 5),
                                       ("parry", 1), ("wound", 4)],
                    [("hit.one-roll-reroll", True), ("wound.scryer", False)])
    assert result.hit and result.wounded


@pytest.mark.phase4_modular
@pytest.mark.parametrize('melee', [True, False])
def test_contagious_reaction_keeps_the_originating_combat_scope(melee):
    hers, foe = sleuth(), opponent()
    foe = replace(foe, global_effects=replace(foe.global_effects,
        tags=(*foe.global_effects.tags, 'contagious')))
    outcome = AttackOutcome(state(hers), replace(state(foe), condition=phases.Condition.OUT),
                            damage=1, melee_attack=melee)
    rolls = []
    if melee:
        rolls.append({'key': 'x.contagious', 'value': 6})
        rolls.append({'key': 'x.contagious.scryer.reroll', 'value': 1})
    dice = StrictDice(rolls)
    decisions = StrictDecisions([{'key': 'x.contagious.scryer', 'value': True}] if melee else [])
    result = _react_to_wound(hers, foe, outcome, dice, 'x', decisions=decisions)
    dice.finish(); decisions.finish()
    assert result.attacker.wounds == outcome.attacker.wounds


@pytest.mark.phase4_modular
@pytest.mark.parametrize('melee', [True, False])
def test_immediate_force_of_will_keeps_the_originating_combat_scope(melee):
    hers, foe = sleuth(), opponent()
    hers = replace(hers, global_effects=replace(hers.global_effects,
        tags=(*hers.global_effects.tags, 'mechanic.force-of-will')))
    outcome = AttackOutcome(state(foe), replace(state(hers), condition=phases.Condition.OUT, wounds=0),
                            melee_attack=melee)
    rolls = [{'key': 'x.force-of-will.rescue', 'value': 6}]
    if melee:
        rolls.append({'key': 'x.force-of-will.rescue.scryer.reroll', 'value': 1})
    dice = StrictDice(rolls)
    decisions = StrictDecisions([{'key': 'x.force-of-will.rescue.scryer', 'value': True}] if melee else [])
    result = _react_to_wound(foe, hers, outcome, dice, 'x', decisions=decisions)
    dice.finish(); decisions.finish()
    assert result.defender.force_of_will_active is melee


@pytest.mark.phase4_modular
@pytest.mark.parametrize('phase', ['hit', 'wound'])
def test_an_ordinary_reroll_must_accept_scryers_second_result(phase):
    hers = sleuth()
    hers = replace(hers, global_effects=replace(hers.global_effects,
        **{'reroll_hits' if phase == 'hit' else 'reroll_wounds': True}))
    rolls = [] if phase == 'hit' else [('hit', 4), ('parry', 1)]
    choices = [] if phase == 'hit' else [('hit.scryer', False)]
    result = strike(hers, opponent(), rolls + [(phase, 1), (phase + '.scryer.reroll', 1)],
                    choices + [(phase + '.scryer', True)])
    # No third die exists: the ordinary reroll must reuse the accepted 1.
    assert not (result.hit if phase == 'hit' else result.wounded)


@pytest.mark.phase4_modular
def test_scryer_can_repeat_the_defenders_gaoler_grapple_strength_test():
    hers, gaoler = sleuth(), opponent()
    gaoler = replace(gaoler, global_effects=replace(gaoler.global_effects,
        tags=(*gaoler.global_effects.tags, 'mechanic.gaoler-grapple')))
    dice = StrictDice([
        {'key': 'x.grapple.hit', 'value': 4}, {'key': 'x.grapple.parry', 'value': 1},
        {'key': 'x.grapple.strength', 'value': 6},
        {'key': 'x.grapple.strength.scryer.reroll', 'value': 1},
    ])
    choices = StrictDecisions([
        {'key': 'x.grapple.parry.scryer', 'value': False},
        {'key': 'x.grapple.strength.scryer', 'value': True},
    ])
    first, second, _ = _resolve_attack_pool(gaoler, hers, state(gaoler), state(hers),
        1, dice, key='x', first_round=False, charging=False,
        decisions=choices, grapple_declared=True)
    dice.finish(); choices.finish()
    assert not first.grappling and not second.grappled


@pytest.mark.phase4_modular
def test_scryer_reaches_the_canonical_crude_belch_leadership_test():
    hers = sleuth()
    elder = compile_fighter(FighterBuild('mordheim', band_id='halflings-mic',
        profile_id='halfling-elder', main_weapon_id='weapon.sword',
        special_rule_ids=('halfling-elder--crude-belch',)))
    initial = initialize_duel(elder, hers, StrictDice([]),
        context=DuelContext(charging=('first',), active_participant='first'))
    key = 'round.0.first.crude-belch'
    dice = StrictDice([
        {'key': key + '.leadership.0', 'value': 6},
        {'key': key + '.leadership.0.scryer.reroll', 'value': 1},
        {'key': key + '.leadership.1', 'value': 6},
    ])
    choices = StrictDecisions([
        {'key': key, 'value': True},
        {'key': key + '.leadership.0.scryer', 'value': True},
        {'key': key + '.leadership.1.scryer', 'value': False},
    ])
    misses, after = resolve_crude_belch(elder, hers, initial, dice, choices, first=True)
    dice.finish(); choices.finish()
    assert not misses and after.second.resources_spent == initial.second.resources_spent


@pytest.mark.phase4_modular
@pytest.mark.parametrize('receiving', [True, False])
def test_scryer_distinguishes_fear_in_melee_from_the_precontact_charge_test(receiving):
    hers, foe = sleuth(), opponent(skill_ids=('mechanic.causes-fear',))
    first, second = (foe, hers) if receiving else (hers, foe)
    initial = initialize_duel(first, second, StrictDice([]),
        context=DuelContext(charging=('first',), active_participant='first'))
    key = 'round.0.second.fear.charged' if receiving else 'round.0.first.fear.charge'
    rolls = [{'key': key + '.0', 'value': 6}]
    if receiving:
        rolls.append({'key': key + '.0.scryer.reroll', 'value': 1})
    rolls.append({'key': key + '.1', 'value': 6})
    dice = StrictDice(rolls)
    choices = StrictDecisions([
        {'key': key + '.0.scryer', 'value': True},
        {'key': key + '.1.scryer', 'value': False},
    ] if receiving else [])
    after = resolve_fear(first, second, initial, dice, choices)
    dice.finish(); choices.finish()
    if receiving:
        assert not after.second.fear_hit_sixes
    else:
        assert 'first' in after.failed_charges and not after.engaged
