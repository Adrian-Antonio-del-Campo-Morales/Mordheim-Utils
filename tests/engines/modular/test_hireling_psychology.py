"""H03a: the assigned hireling psychology facts reach their real consumers.

Every case compiles the canonical catalogue profile and reads the operator the
duel uses: ``causes_fear`` for the trait rows, the first-round Hatred reroll for
the Dark Mage, the charge gate for the Fallen Sister, and the supplied
Leadership penalty for Massively Built.
"""
from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.phases import Condition
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


def hireling(profile_id, band, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile_id, collection="mordheim", **options))


def fighter(band, profile_id, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile_id, collection="mordheim", **options))


def plain(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", **options))


class Recorder:
    """A loose source that records every request, to show an offer came back."""

    def __init__(self):
        self.rolls = []
        self.choices = []

    def roll(self, request):
        self.rolls.append(request.key)
        return 1

    def choose(self, key, context=None):
        self.choices.append(key)
        return True


# The ten trait rows are five profiles whose whole-profile row and individual
# trait row name the same consequence; each must reach the operator exactly once.
def fear_carriers():
    return (
        hireling("hireling.hired-sword.dark-mage", "hirelings.hired-sword.2a"),
        hireling("hireling.hired-sword.ogre-slave-master", "hirelings.hired-sword.2a",
                 main_weapon_id="weapon.axe", off_hand_id="weapon.club",
                 owned_item_ids=("axe", "club", "light_armour")),
        hireling("hireling.hired-sword.bone-goliath", "hirelings.hired-sword.1c",
                 main_weapon_id="weapon.natural-attacks"),
        hireling("hireling.hired-sword.chaos-centaur", "hirelings.hired-sword.1c",
                 main_weapon_id="weapon.spear", off_hand_id="defence.shield",
                 owned_item_ids=("throwing_axe", "shield", "spear")),
        hireling("hireling.hired-sword.ogre-bodyguard", "hirelings.hired-sword.core",
                 main_weapon_id="weapon.double-handed-weapon"),
    )


@pytest.mark.phase3_rules
def test_each_trait_fear_row_reaches_causes_fear_once():
    foe = plain()
    for carrier in fear_carriers():
        assert carrier.global_effects.tags.count("mechanic.causes-fear") == 1
        assert causes_fear(carrier, foe)


@pytest.mark.phase3_rules
def test_the_emissary_fear_belongs_to_its_nurgle_patron_only(precompiled):
    compiled = precompiled()
    khorne, nurgle = compiled.first, compiled.second
    assert "mechanic.causes-fear" not in khorne.global_effects.tags
    assert not causes_fear(khorne, plain())
    assert nurgle.global_effects.tags.count("mechanic.causes-fear") == 1
    assert "identity.chaos-follower" in nurgle.global_effects.tags
    assert "poison.black-lotus" in nurgle.global_effects.tags
    assert causes_fear(nurgle, plain())


@pytest.mark.phase3_rules
def test_dark_mage_hatred_rerolls_only_against_a_necromancer(precompiled):
    compiled = precompiled()
    mage, necromancer = compiled.first, compiled.second
    dregs = fighter("undead", "dregs")
    assert "identity.necromancer" in necromancer.global_effects.tags
    assert "identity.necromancer" not in dregs.global_effects.tags

    def attack(target, tape):
        init = StrictDice([])
        attacker_state = initialize_fighter(mage, init, "a")
        defender_state = initialize_fighter(target, init, "d")
        init.finish()
        dice = StrictDice(tape)
        result = resolve_reference_attack(
            mage, target, attacker_state, defender_state, mage.main_weapon,
            dice, key="attack", first_round=True)
        return result, dice

    result, dice = attack(necromancer, [
        {"key": "attack.hit", "value": 1}, {"key": "attack.hit.reroll", "value": 1}])
    assert [request.key for request in dice.requests] == ["attack.hit", "attack.hit.reroll"]
    assert not result.hit
    result, dice = attack(dregs, [{"key": "attack.hit", "value": 1}])
    assert [request.key for request in dice.requests] == ["attack.hit"]
    assert not result.hit

    # Self Assured is the excluded All Alone clause, not generic immunity.
    assert "mechanic.psychology-immunity" not in mage.global_effects.tags


@pytest.mark.phase3_rules
def test_fallen_sister_must_pass_leadership_to_charge_a_sigmarite(precompiled):
    sister, sigmarite = precompiled(0).first, precompiled(0).second
    dregs = precompiled(2).second
    assert "identity.sigmarite-opponent" in sigmarite.global_effects.tags
    context = DuelContext(charging=("first",), active_participant="first")

    state = initialize_duel(sister, sigmarite, StrictDice([]), context=context)
    dice = StrictDice([
        {"key": "round.0.first.ashamed-and-afraid.0", "value": 6},
        {"key": "round.0.first.ashamed-and-afraid.1", "value": 6}])
    gated = resolve_fear(sister, sigmarite, state, dice, StrictDecisions([]))
    dice.finish()
    assert not gated.first_charged
    assert gated.failed_charges == frozenset({"first"})

    state = initialize_duel(sister, dregs, StrictDice([]), context=context)
    free = resolve_fear(sister, dregs, state, StrictDice([]), StrictDecisions([]))
    assert free.first_charged
    assert not free.failed_charges


@pytest.mark.phase2_construction
def test_massively_built_optional_penalty_is_the_supplied_leadership_fact(precompiled):
    target = precompiled().first
    assert target.characteristics.leadership == 6
    assert "mechanic.causes-fear" not in target.global_effects.tags
    assert "mechanic.psychology-immunity" not in target.global_effects.tags


@pytest.mark.phase3_rules
def test_massively_built_supplied_loss_costs_the_recipients_own_turn_once(precompiled):
    """The printed outcome is a whole lost turn, spent once on the target.

    Fanatic Online 89, p. 2: "The target model must make a Ld check or lose
    his entire next turn as he stands dumbfounded".  The failed check and its
    shooting-phase activation stay outside the duel, so the caller supplies
    the individual outcome.  Female and non-human exemptions belong to that
    supplied fact: the duel adds no blanket immunity, and a supplied Vampire or
    Necromancer target keeps the consequence the source prints for it.
    """
    # Herb Lore and the Rousing Sermon resolve before the attack pool, so the
    # number of attacks alone would not show that the whole turn was lost.
    foe, target = precompiled().first, precompiled().second
    assert "condition.massively-built-lost-turn" in target.global_effects.tags
    assert not target.global_effects.frenzy
    state = initialize_duel(foe, target, StrictDice([]),
        context=DuelContext(charging=(), active_participant="first"))
    state = replace(state, second=replace(state.second, wounds=1))
    assert state.second.massively_built_lost_turn
    assert not state.first.massively_built_lost_turn
    # Herb Lore must have a Wound to heal, or its absence would prove nothing.
    assert state.second.wounds < target.characteristics.wounds

    # The foe's own turn is not the lost one: retaliation stays intact.
    dice = StrictDice([
        {"key": "round.0.priority-tie", "value": 1},
        {"key": "round.0.second.attack.0.hit", "value": 1},
        {"key": "round.0.first.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    first = resolve_round(foe, target, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(first.attacks) == 2
    assert first.state.second.massively_built_lost_turn

    # Its own turn spends the state: the foe's single attack remains, the
    # target's is gone, and no voluntary own-turn action is offered at all.
    # The strict sources make any Herb Lore or Rousing Sermon decision, roll or
    # spend in this turn an unexpected request and therefore a failure.
    dice = StrictDice([
        {"key": "round.1.priority-tie", "value": 1},
        {"key": "round.1.first.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    second = resolve_round(foe, target, first.state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(second.attacks) == 1
    assert not second.state.second.massively_built_lost_turn
    assert second.state.second.condition is Condition.STANDING
    assert second.state.second.wounds == 1
    assert not any("sermon" in spent for spent in second.state.second.resources_spent)

    # The loss expires with that turn: the next phase is an ordinary exchange.
    dice = StrictDice([
        {"key": "round.2.priority-tie", "value": 1},
        {"key": "round.2.second.attack.0.hit", "value": 1},
        {"key": "round.2.first.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    third = resolve_round(foe, target, second.state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(third.attacks) == 2

    # Its next own turn offers both actions again, so the gate is the turn and
    # not a lasting removal of the operators.
    dice, decisions = Recorder(), Recorder()
    fourth = resolve_round(foe, target, third.state, dice, decisions)
    assert "round.3.second.herb-lore" in dice.rolls
    assert "round.3.second.herb-lore" in decisions.choices
    assert "round.3.second.rousing-sermon" in decisions.choices
    assert "round.3.rousing-sermon" in fourth.state.second.resources_spent


@pytest.mark.phase3_rules
def test_the_lost_turn_offers_no_optional_own_action(precompiled):
    """A lost turn is not just an empty attack pool.

    Fanatic Online 89, p. 2: the failed target "lose his entire next turn as he
    stands dumbfounded".  Herb Lore and Rousing Sermon are optional
    declarations of that same own turn, so neither may be offered while the
    supplied state is pending.  Passive effects and compulsory tests are not
    touched by this case.
    """
    foe, target = precompiled().first, precompiled().second
    state = initialize_duel(foe, target, StrictDice([]),
        context=DuelContext(charging=(), active_participant="first"))
    state = replace(state, second=replace(state.second, wounds=1))
    assert state.second.massively_built_lost_turn

    # The opponent's turn first: the pending state is not spent there.
    dice = StrictDice([
        {"key": "round.0.priority-tie", "value": 1},
        {"key": "round.0.second.attack.0.hit", "value": 1},
        {"key": "round.0.first.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    first = resolve_round(foe, target, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert first.state.second.massively_built_lost_turn

    # Round 1 is the target's own turn and it is wounded, so both actions
    # would be requested without the lost-turn gate; the empty script would
    # then fail with an unexpected decision instead of the expected one attack.
    dice = StrictDice([
        {"key": "round.1.priority-tie", "value": 1},
        {"key": "round.1.first.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    result = resolve_round(foe, target, first.state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(result.attacks) == 1
    assert decisions.requests == []
    assert not result.state.second.massively_built_lost_turn
