"""F060 — source-derived Shifty poisoned-hand transport witnesses.

The cases run the real ``initialize_duel`` -> ``resolve_round`` modular
pipeline on explicit synthetic ``CompiledFighter`` inputs. They never call
``compile_fighter`` or any construction helper: the concurrent
warrior-construction centralization owns that frontier, and this lot proves
engine composition, not legal access.

Accepted contract (permanent rulings, Shifty S2 and Poison timing):
  * one usable carried melee hand is nominated before any attack die;
  * the nominated hand's weapon, clean/poisoned pair and hand slot travel to
    the separately timed bonus attack;
  * ordinary attacks keep their own hand's poison state;
  * Spider Spittle tests immediately on an undefended hit, before the wound
    roll, and only for the weapon that carries it.

Synthetic input provenance (engine composition only, not canonical legality):
  * ``Characteristics(3, 3, 3, 1, I, 1)`` — the reviewed pilot profile shape;
  * main ``weapon.mace`` / off ``weapon.axe`` with a synthetic
    ``hit_modifier=1`` on the off hand so the nominated hand is observable in
    ``AttackOutcome.hit_target`` (same device as the accepted
    ``test_bonus_weapon_choice_is_separate_from_ordinary_allocation``);
  * ``poison.spider-spittle`` on one hand; ``*_without_poison`` is the same
    weapon minus that tag, mirroring the compiler's contextual-poison
    contract (see the ``CompiledFighter`` field comment);
  * ``skill.shifty`` injected as a tag — the accepted pilot binding; canonical
    activation is F004 and is not claimed here;
  * no armour or ward save (7) and no defence ids, so no extra die enters a
    tape; every wound roll fails (S3 vs T3 needs 4) so no injury interrupts
    the observed sequence.
"""
from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, CompiledFighter, DuelContext, EffectSet

SHIFTY_TAG = 'skill.shifty'
SPIDER_SPITTLE_TAG = 'poison.spider-spittle'
HIT = 4
# <= Toughness 3: the Spider Spittle check passes, the target stays standing
# and its own pools remain observable.
SPITTLE_PASSES = 2
# S3 vs T3 needs 4: the wound fails and no injury interrupts the tape.
WOUND_FAILS = 1
NO_SAVE = 7
OFF_HAND_DISCRIMINATOR = 1


def _weapon(tag, *, poisoned=False, hit_modifier=0):
    """Return ``(weapon, clean pair)``; the pair is None for a clean hand.

    This mirrors the compiler contract: the clean pair is the same weapon
    contribution without the poison tag, so contextual poison removal never
    subtracts a guessed numeric bonus.
    """
    base = EffectSet(tags=(tag,), hit_modifier=hit_modifier)
    if not poisoned:
        return base, None
    return EffectSet(tags=(tag, SPIDER_SPITTLE_TAG), hit_modifier=hit_modifier), base


def duelist(*, initiative=5, main_poisoned=False, off_poisoned=False, shifty=True):
    """Synthetic Shifty owner: main mace, off-hand axe, one attack each."""
    main, main_clean = _weapon('weapon.mace', poisoned=main_poisoned)
    off, off_clean = _weapon('weapon.axe', poisoned=off_poisoned,
                             hit_modifier=OFF_HAND_DISCRIMINATOR)
    return CompiledFighter(
        fighter_id='synthetic:f060-duelist',
        characteristics=Characteristics(3, 3, 3, 1, initiative, 1),
        main_weapon=main, off_hand=off,
        global_effects=EffectSet(tags=(SHIFTY_TAG,) if shifty else ()),
        armour_save=NO_SAVE, helmet_save=NO_SAVE, natural_armour_save=NO_SAVE,
        off_hand_attacks=True,
        main_weapon_without_poison=main_clean, off_hand_without_poison=off_clean,
        unarmed_weapon=EffectSet(tags=('weapon.fist',)),
    )


def charger(*, initiative=3):
    """Synthetic charging opponent: clean mace, no off hand, no Shifty."""
    return CompiledFighter(
        fighter_id='synthetic:f060-charger',
        characteristics=Characteristics(3, 3, 3, 1, initiative, 1),
        main_weapon=EffectSet(tags=('weapon.mace',)), off_hand=None,
        global_effects=EffectSet(),
        armour_save=NO_SAVE, helmet_save=NO_SAVE, natural_armour_save=NO_SAVE,
        unarmed_weapon=EffectSet(tags=('weapon.fist',)),
    )


class _TracedDecisions:
    """StrictDecisions wrapper recording each decision and the dice requested so far."""

    def __init__(self, decisions, dice):
        self.decisions = decisions
        self.dice = dice
        self.events = []

    def choose(self, key, context=None):
        self.events.append((key, len(self.dice.requests)))
        return self.decisions.choose(key, context)


def _run(first, second, *, charging, active, tape, choices=()):
    """Run one round through the real pipeline with a fully strict dice/decision tape."""
    dice = StrictDice([{'key': key, 'value': value} for key, value in tape])
    decisions = StrictDecisions([{'key': key, 'value': value} for key, value in choices])
    traced = _TracedDecisions(decisions, dice)
    state = initialize_duel(first, second, dice, context=DuelContext(
        charging=charging, active_participant=active))
    result = resolve_round(first, second, state, dice, traced)
    dice.finish()
    decisions.finish()
    return result, dice.requests, decisions, traced


def _keys(tape):
    return [key for key, _ in tape]


def test_nominated_poisoned_main_transports_spider_spittle_to_bonus_and_ordinary_main():
    """Case A: main hand poisoned, off clean, the main hand is nominated."""
    first, second = duelist(main_poisoned=True), charger()
    tape = (
        ('round.0.first.shifty.attack.0.hit', HIT),
        ('round.0.first.shifty.attack.0.spider-spittle', SPITTLE_PASSES),
        ('round.0.first.shifty.attack.0.wound', WOUND_FAILS),
        ('round.0.second.attack.0.hit', HIT),
        ('round.0.second.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.0.hit', HIT),
        ('round.0.first.attack.1.hit', HIT),
        ('round.0.first.attack.0.spider-spittle', SPITTLE_PASSES),
        ('round.0.first.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.1.wound', WOUND_FAILS),
    )
    result, requests, decisions, traced = _run(
        first, second, charging=('second',), active='second', tape=tape,
        choices=(('round.0.first.shifty.main-weapon', True),))
    keys = [request.key for request in requests]
    # S2: the nomination is decided before any attack die is requested.
    assert traced.events == [('round.0.first.shifty.main-weapon', 0)]
    assert decisions.requests == ['round.0.first.shifty.main-weapon']
    # Poison timing: the test follows the undefended hit and precedes the wound roll.
    assert 'round.0.first.shifty.attack.0.spider-spittle' in keys
    assert 'round.0.first.attack.0.spider-spittle' in keys
    assert 'round.0.first.attack.1.spider-spittle' not in keys
    assert keys == _keys(tape)
    assert [attack.hit_target for attack in result.attacks] == [4, 4, 4, 3]
    assert len(result.attacks) == 4
    assert not any(attack.wounded for attack in result.attacks)
    assert (result.state.first.wounds, result.state.second.wounds) == (1, 1)
    assert result.state.first.condition == phases.Condition.STANDING
    assert result.state.second.condition == phases.Condition.STANDING
    assert result.state.round_index == 1


def test_nominated_poisoned_off_transports_spider_spittle_to_bonus_and_ordinary_off():
    """Case B: off hand poisoned, main clean, the off hand is nominated."""
    first, second = duelist(off_poisoned=True), charger()
    tape = (
        ('round.0.first.shifty.attack.0.hit', HIT),
        ('round.0.first.shifty.attack.0.spider-spittle', SPITTLE_PASSES),
        ('round.0.first.shifty.attack.0.wound', WOUND_FAILS),
        ('round.0.second.attack.0.hit', HIT),
        ('round.0.second.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.0.hit', HIT),
        ('round.0.first.attack.1.hit', HIT),
        ('round.0.first.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.1.spider-spittle', SPITTLE_PASSES),
        ('round.0.first.attack.1.wound', WOUND_FAILS),
    )
    result, requests, decisions, traced = _run(
        first, second, charging=('second',), active='second', tape=tape,
        choices=(('round.0.first.shifty.main-weapon', False),))
    keys = [request.key for request in requests]
    assert traced.events == [('round.0.first.shifty.main-weapon', 0)]
    assert decisions.requests == ['round.0.first.shifty.main-weapon']
    assert 'round.0.first.shifty.attack.0.spider-spittle' in keys
    assert 'round.0.first.attack.0.spider-spittle' not in keys
    assert 'round.0.first.attack.1.spider-spittle' in keys
    assert keys == _keys(tape)
    # The nominated off hand keeps its synthetic +1 hit discriminator.
    assert [attack.hit_target for attack in result.attacks] == [3, 4, 4, 3]
    assert len(result.attacks) == 4
    assert not any(attack.wounded for attack in result.attacks)
    assert (result.state.first.wounds, result.state.second.wounds) == (1, 1)
    assert result.state.first.condition == phases.Condition.STANDING
    assert result.state.second.condition == phases.Condition.STANDING
    assert result.state.round_index == 1


def test_nominating_the_clean_main_keeps_bonus_clean_and_ordinary_off_poisoned():
    """Case C: the clean hand is nominated while the other hand is poisoned."""
    first, second = duelist(off_poisoned=True), charger()
    tape = (
        ('round.0.first.shifty.attack.0.hit', HIT),
        ('round.0.first.shifty.attack.0.wound', WOUND_FAILS),
        ('round.0.second.attack.0.hit', HIT),
        ('round.0.second.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.0.hit', HIT),
        ('round.0.first.attack.1.hit', HIT),
        ('round.0.first.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.1.spider-spittle', SPITTLE_PASSES),
        ('round.0.first.attack.1.wound', WOUND_FAILS),
    )
    result, requests, decisions, traced = _run(
        first, second, charging=('second',), active='second', tape=tape,
        choices=(('round.0.first.shifty.main-weapon', True),))
    keys = [request.key for request in requests]
    assert traced.events == [('round.0.first.shifty.main-weapon', 0)]
    assert decisions.requests == ['round.0.first.shifty.main-weapon']
    # The bonus stays clean: possession of the other hand's poison adds no trigger.
    assert 'round.0.first.shifty.attack.0.spider-spittle' not in keys
    assert 'round.0.first.attack.0.spider-spittle' not in keys
    # The poisoned off hand keeps its own trigger on its own ordinary attack.
    assert 'round.0.first.attack.1.spider-spittle' in keys
    assert keys == _keys(tape)
    assert [attack.hit_target for attack in result.attacks] == [4, 4, 4, 3]
    assert len(result.attacks) == 4
    assert not any(attack.wounded for attack in result.attacks)
    assert (result.state.first.wounds, result.state.second.wounds) == (1, 1)
    assert result.state.first.condition == phases.Condition.STANDING
    assert result.state.second.condition == phases.Condition.STANDING
    assert result.state.round_index == 1


def test_owner_in_second_position_transports_nominated_off_poison():
    """Participant-position control: the Shifty owner is the duel's second fighter."""
    first, second = charger(), duelist(off_poisoned=True)
    tape = (
        ('round.0.second.shifty.attack.0.hit', HIT),
        ('round.0.second.shifty.attack.0.spider-spittle', SPITTLE_PASSES),
        ('round.0.second.shifty.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.0.hit', HIT),
        ('round.0.first.attack.0.wound', WOUND_FAILS),
        ('round.0.second.attack.0.hit', HIT),
        ('round.0.second.attack.1.hit', HIT),
        ('round.0.second.attack.0.wound', WOUND_FAILS),
        ('round.0.second.attack.1.spider-spittle', SPITTLE_PASSES),
        ('round.0.second.attack.1.wound', WOUND_FAILS),
    )
    result, requests, decisions, traced = _run(
        first, second, charging=('first',), active='first', tape=tape,
        choices=(('round.0.second.shifty.main-weapon', False),))
    keys = [request.key for request in requests]
    assert traced.events == [('round.0.second.shifty.main-weapon', 0)]
    assert decisions.requests == ['round.0.second.shifty.main-weapon']
    assert 'round.0.second.shifty.attack.0.spider-spittle' in keys
    assert 'round.0.second.attack.1.spider-spittle' in keys
    assert 'round.0.second.attack.0.spider-spittle' not in keys
    # No bonus, nomination or poison trigger leaks to the charging first fighter.
    assert not any(key.startswith('round.0.first.shifty') for key in keys)
    assert not any(key.startswith('round.0.first.') and key.endswith('.spider-spittle')
                   for key in keys)
    assert keys == _keys(tape)
    assert [attack.hit_target for attack in result.attacks] == [3, 4, 4, 3]
    assert len(result.attacks) == 4
    assert not any(attack.wounded for attack in result.attacks)
    assert (result.state.first.wounds, result.state.second.wounds) == (1, 1)
    assert result.state.first.condition == phases.Condition.STANDING
    assert result.state.second.condition == phases.Condition.STANDING
    assert result.state.round_index == 1


def test_no_shifty_control_keeps_per_hand_poison_without_bonus_or_nomination():
    """Control: without the skill there is no bonus, nomination or trigger leak."""
    first, second = duelist(main_poisoned=True, shifty=False), charger()
    tape = (
        ('round.0.second.attack.0.hit', HIT),
        ('round.0.second.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.0.hit', HIT),
        ('round.0.first.attack.1.hit', HIT),
        ('round.0.first.attack.0.spider-spittle', SPITTLE_PASSES),
        ('round.0.first.attack.0.wound', WOUND_FAILS),
        ('round.0.first.attack.1.wound', WOUND_FAILS),
    )
    result, requests, decisions, traced = _run(
        first, second, charging=('second',), active='second', tape=tape)
    keys = [request.key for request in requests]
    assert traced.events == []
    assert decisions.requests == []
    assert not any('shifty' in key for key in keys)
    assert 'round.0.first.attack.0.spider-spittle' in keys
    assert 'round.0.first.attack.1.spider-spittle' not in keys
    assert keys == _keys(tape)
    # Charger, then the owner's clean main and poisoned off hand: no bonus.
    assert [attack.hit_target for attack in result.attacks] == [4, 4, 3]
    assert len(result.attacks) == 3
    assert not any(attack.wounded for attack in result.attacks)
    assert (result.state.first.wounds, result.state.second.wounds) == (1, 1)
    assert result.state.first.condition == phases.Condition.STANDING
    assert result.state.second.condition == phases.Condition.STANDING
    assert result.state.round_index == 1
