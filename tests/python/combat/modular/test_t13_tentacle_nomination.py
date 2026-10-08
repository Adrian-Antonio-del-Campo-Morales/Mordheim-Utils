"""T13 A-block: the printed Tentacle nomination.

Source (``sources/knowledge/bands/mordheim/cult-of-the-possessed/special-rules.yaml``
and its trollheim twin): *"One of the mutant's arms ends in a tentacle.  He may
grapple his opponent in close combat to reduce his attacks by -1, down to a
minimum of 1.  The mutant may decide which attack his opponent loses."*

The compiled mutation retains the incoming modifier for count-only consumers.
The modular round defers its optional loss until allocation, including Whipcrack
and separately timed bonuses. One accepted nomination consumes the phase's
single grapple, and a lone attack is never offered for removal.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular import pools
from mordheim_combat.modular import rounds
from mordheim_combat.modular import state as st
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import AlwaysReject
from mordheim_core.dice import ScriptedDecisions
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def build(main_weapon_id="weapon.mace", off_hand_id=None, **options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id=main_weapon_id, off_hand_id=off_hand_id, **options))


def mutant(collection="mordheim", band_id="cult-of-the-possessed", profile_id="mutants"):
    return compile_fighter(FighterBuild(
        "mordheim", collection=collection, band_id=band_id, profile_id=profile_id,
        special_rule_ids=("band--mutations-tentacle",)))


def reduced_count(attacker, defender, *, defer_grapple=False):
    count = phases.build_attacks(phases.AttackPoolContext(attacker)).attacks
    return rounds.apply_opponent_attack_modifiers(
        attacker, defender, count, first_round=False, defer_grapple=defer_grapple)


def pool(attacker, defender, decisions, rolls=()):
    count = reduced_count(attacker, defender, defer_grapple=True)
    attacker_state = st.initialize_fighter(attacker, StrictDice([]), "a")
    defender_state = st.initialize_fighter(defender, StrictDice([]), "d")
    dice = StrictDice([{"key": key, "value": value} for key, value in rolls])
    outcomes = pools._resolve_attack_pool(
        attacker, defender, attacker_state, defender_state, count, dice,
        key="test", first_round=False, charging=False, decisions=decisions)[2]
    dice.finish()
    return count, outcomes


def two_weapons():
    """The main weapon outclasses the off-hand one: Strength 4 against 3."""
    return build(main_weapon_id="weapon.sigmarite-hammer", off_hand_id="weapon.mace")


def test_the_compiled_mutation_publishes_the_grapple_tag():
    fighter = mutant()
    assert fighter.global_effects.incoming_attacks_modifier == -1
    assert "rule.tentacle-grapple" in fighter.global_effects.tags
    trollheim = mutant("trollheim", "trollheim-cult-of-the-possessed", "mutants")
    assert "rule.tentacle-grapple" in trollheim.global_effects.tags
    assert trollheim.global_effects.incoming_attacks_modifier == -1


def test_the_default_nomination_keeps_the_off_hand_attack():
    """The flat modifier already dropped the allocation's first entry."""
    attacker, defender = two_weapons(), mutant()
    assert reduced_count(attacker, defender) == 1
    count, outcomes = pool(attacker, defender, AlwaysAccept(), (
        ("test.attack.0.hit", 5), ("test.attack.0.wound", 3)))
    assert count == 2  # The pool nominates the loss from the real allocation.
    # Strength 3 against Toughness 3 wounds on 4+, so the surviving attack is
    # the off-hand mace and the printed Strength 4 hammer is gone.
    assert len(outcomes) == 1
    assert outcomes[0].wounded is False


def test_the_nomination_can_take_the_main_weapon_instead():
    attacker, defender = two_weapons(), mutant()
    _, outcomes = pool(attacker, defender, ScriptedDecisions({
        "test.grapple-lost-attack.0": False, "test.grapple-lost-attack.1": True,
    }), (("test.attack.0.hit", 5), ("test.attack.0.wound", 3),
         ("test.attack.0.injury.0", 1)))
    assert len(outcomes) == 1
    # The hammer survives and wounds on the same die the mace failed.
    assert outcomes[0].wounded is True


def test_declining_every_offer_keeps_the_whole_pool():
    attacker, defender = two_weapons(), mutant()
    _, outcomes = pool(attacker, defender, ScriptedDecisions({
        "test.grapple-lost-attack.0": False, "test.grapple-lost-attack.1": False,
    }), (("test.attack.0.hit", 1), ("test.attack.1.hit", 1)))
    assert len(outcomes) == 2
    assert [outcome.hit for outcome in outcomes] == [False, False]


def test_a_lone_attack_is_never_taken():
    """The printed minimum of one attack survives the recomposition."""
    attacker = build(main_weapon_id="weapon.mace")
    defender = mutant()
    decisions = RecordingDecisions()
    count, outcomes = pool(attacker, defender, decisions, (("test.attack.0.hit", 1),))
    assert count == 1
    assert len(outcomes) == 1
    assert decisions.keys == []


def test_the_nomination_precedes_every_attack_roll():
    events: list[str] = []

    class Decisions:
        def choose(self, key, context=None):
            events.append(key)
            return True

    class Dice:
        def roll(self, request):
            events.append(request.key)
            return 1

    attacker, defender = two_weapons(), mutant()
    attacker_state = st.initialize_fighter(attacker, StrictDice([]), "a")
    defender_state = st.initialize_fighter(defender, StrictDice([]), "d")
    pools._resolve_attack_pool(
        attacker, defender, attacker_state, defender_state, 2, Dice(),
        key="test", first_round=False, charging=False, decisions=Decisions())
    # The nomination is taken while the pool is assembled, so the first attack
    # roll follows it instead of preceding it.
    assert events[0] == "test.grapple-lost-attack.0"
    assert events[1] == "test.attack.0.hit"


class RecordingDecisions:
    """Accepts the first offer while remembering every key it was given."""

    def __init__(self) -> None:
        self.keys: list[str] = []

    def choose(self, key: str, context: object | None = None) -> bool:
        self.keys.append(key)
        return True


def test_declining_grapple_does_not_create_an_attack_for_a_lone_attacker():
    attacker, defender = build(), mutant()

    class Misses:
        def roll(self, request):
            return 1

    a = st.initialize_fighter(attacker, StrictDice([]), "a")
    d = st.initialize_fighter(defender, StrictDice([]), "d")
    _, _, outcomes = pools._resolve_attack_pool(
        attacker, defender, a, d, 1, Misses(), key="test",
        first_round=False, charging=False, decisions=AlwaysReject())
    assert len(outcomes) == 1


@pytest.mark.parametrize("attacks,charging,shifty", [
    (1, ("first",), False),
    (2, ("second",), False),
    (2, ("second",), True),
])
def test_grapple_removes_one_whip_attack_per_phase(attacks, charging, shifty):
    attacker, defender = build(main_weapon_id="weapon.barbed-whip"), mutant()
    attacker = replace(attacker, characteristics=replace(attacker.characteristics, attacks=attacks))
    if shifty:
        attacker = replace(attacker, global_effects=replace(
            attacker.global_effects, tags=(*attacker.global_effects.tags, "skill.shifty")))

    class Misses:
        def __init__(self):
            self.keys = []

        def roll(self, request):
            self.keys.append(request.key)
            return 1

    dice, decisions = Misses(), RecordingDecisions()
    duel = st.initialize_duel(attacker, defender, dice,
        context=DuelContext(charging=charging, active_participant=charging[0]))
    result = rounds.resolve_round(attacker, defender, duel, dice, decisions)
    hits = [key for key in dice.keys if key.startswith("round.0.first") and key.endswith(".hit")]
    assert len(hits) == attacks + int(shifty)  # +1 Whipcrack, -1 Tentacle
    assert len([key for key in decisions.keys if ".grapple-lost-attack." in key]) == 1
    dice.keys.clear()
    decisions.keys.clear()
    rounds.resolve_round(attacker, defender, result.state, dice, decisions)
    hits = [key for key in dice.keys if key.startswith("round.1.first") and key.endswith(".hit")]
    assert len(hits) == max(1, attacks - 1)
