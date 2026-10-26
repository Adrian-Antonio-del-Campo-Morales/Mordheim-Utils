"""Dark Jester and related families: Dark Jester tricks, Mantle of Crows, Needle and Thread,
Backstabber, Thin Flesh, Lycanthrope and Slay Large Creature, end to end in the
modular engine.

Every expectation is derived from the printed clause in
``sources/knowledge/catalog/mechanics/close-combat.yaml`` and
``execution.yaml``, not from current engine behaviour.  The witnesses inject
canonical bindings as well as isolated mechanic tags on compiled fighters.
Decision requests are strict; listed dice keys cannot be drawn twice, and
unlisted Trip dice always fail. Peripheral dice may answer 1, but witnesses
pin the source-derived distinguishing requests and outcomes.
"""
from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import (_combined_effect, prepare_hit_context,
    prepare_wound_context, prepare_armour_context, prepare_special_save_context)
from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.state import initialize_fighter

from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.phases import Condition
from mordheim_core.models import Characteristics, FighterBuild, DuelContext, LocalParticipant


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


class Tape:
    """Listed faces are consumed per key in order; unlisted requests answer 1."""

    def __init__(self, rolls: dict[str, list[int]] | None = None):
        self.rolls = {key: list(faces) for key, faces in (rolls or {}).items()}
        self.requests: list[str] = []

    def roll(self, request):
        key = request.key
        self.requests.append(key)
        queue = self.rolls.get(key)
        if key in self.rolls and not queue:
            raise AssertionError(f"duplicate roll: {key}")
        if (key.endswith(('.wound', '.trip-roll', '.special.ward'))
                or '.injury.' in key) and not queue:
            raise AssertionError(f"unexpected mechanic roll: {key}")
        value = queue.pop(0) if queue else 1
        if not 1 <= value <= request.sides:
            raise ValueError(f"invalid fixture face {value} for D{request.sides}")
        return value

    def produced(self, key: str) -> int:
        """The number of times that key was asked for."""
        return sum(1 for entry in self.requests if entry == key)

    def finish(self):
        """Every listed face was consumed exactly once."""
        leftover = {key: faces for key, faces in self.rolls.items() if faces}
        if leftover:
            raise AssertionError(f"unused listed rolls: {sorted(leftover)}")


class ScriptedChoices:
    """Every decision must be explicitly listed and consumed exactly once."""

    def __init__(self, choices: dict[str, bool] | None = None):
        self.choices = dict(choices or {})
        self.offered: list[str] = []

    def choose(self, key: str, context=None) -> bool:
        self.offered.append(key)
        if key in self.choices:
            value = self.choices.pop(key)
            if not isinstance(value, bool):
                raise ValueError("decision values must be booleans")
            return value
        raise AssertionError(f"unexpected or duplicate decision: {key}")

    def finish(self):
        if self.choices:
            raise AssertionError(f"unused decisions: {sorted(self.choices)}")


def fighter(*tags: str, strength: int = 3):
    """A plain compiled fighter carrying only the supplied mechanic tag(s)."""
    base = compile_fighter(FighterBuild("mordheim",
        Characteristics(3, 3, strength, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))
    return replace(base, global_effects=replace(base.global_effects,
        tags=(*base.global_effects.tags, *tags)))


def duel(first, second, *, dice=None, choices=None, context=None):
    """One resolve_round on the supplied fixture pair."""
    dice = dice if dice is not None else Tape()
    choices = choices if choices is not None else ScriptedChoices()
    if context is None:
        context = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(first, second, dice, context=context)
    return resolve_round(first, second, state, dice, choices)


# --- the mechanic records exist verbatim -------------------------------------


# --- Trip ---------------------------------------------------------------------

# The chooser offers the dodge, the banter and the trip in that order and
# exactly one may be accepted (the round's chosen trick).
TRIP_OFFERS = {f"round.0.first.jester-trick.{slot}": face for slot, face in (
    ("dodge_trick_active", False), ("banter_trick_active", False),
    ("trip_trick_active", True))}


def test_trip_replaces_the_wound_roll_with_a_two_plus_knockdown(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.trip-roll": [2]})
    choices = ScriptedChoices({**TRIP_OFFERS, "round.0.first.attack.0.trip.hit": True})
    result = duel(owner, victim, dice=dice, choices=choices)
    # The 2+ knocked the opponent down and no wound die was drawn: the wound
    # replacement is the printed alternative outcome, not a second step.
    assert result.state.second.condition == Condition.KNOCKED_DOWN
    assert dice.produced("round.0.first.attack.0.wound") == 0
    dice.finish()
    choices.finish()


def test_trip_roll_of_one_leaves_the_victim_standing(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.trip-roll": [1]})
    choices = ScriptedChoices({**TRIP_OFFERS, "round.0.first.attack.0.trip.hit": True})
    result = duel(owner, victim, dice=dice, choices=choices)
    # A 1 misses the printed 2+ and the victim stays standing, no wound.
    assert result.state.second.condition == Condition.STANDING
    assert result.state.second.wounds == 2
    assert dice.produced("round.0.first.attack.0.wound") == 0
    dice.finish()
    choices.finish()


def test_a_declined_trip_rolls_the_ordinary_wound_die(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.second.attack.0.hit": [1]})
    choices = ScriptedChoices({**TRIP_OFFERS, "round.0.first.attack.0.trip.hit": False})
    result = duel(owner, victim, dice=dice, choices=choices)
    # S3 vs T3 wounds on 4+: exercise the successful ordinary wound, where
    # the residual Trip block used to offer the rejected choice a second time.
    assert result.state.second.condition == Condition.STANDING
    assert result.state.second.wounds == 1
    assert result.attacks[0].wounded
    assert choices.offered.count("round.0.first.attack.0.trip.hit") == 1
    assert dice.produced("round.0.first.attack.0.wound") == 1
    assert dice.produced("round.0.first.attack.0.trip-roll") == 0
    dice.finish()
    choices.finish()


def test_trip_is_not_offered_without_its_chosen_slot(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [3],
                 "round.0.second.attack.0.hit": [1]})
    choices = ScriptedChoices({
        "round.0.first.jester-trick.dodge_trick_active": False,
        "round.0.first.jester-trick.banter_trick_active": False,
        "round.0.first.jester-trick.trip_trick_active": False,
    })
    result = duel(owner, victim, dice=dice, choices=choices)
    assert result.state.second.wounds == 2
    assert dice.produced("round.0.first.attack.0.wound") == 1
    choices.finish()


# --- Sidestepper --------------------------------------------------------------

DODGE_OFFERS = {"round.0.second.jester-trick.dodge_trick_active": True}


def test_sidestepper_deflects_a_wounding_hit_on_the_unmodifiable_four_plus(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.special.ward": [4],
                 "round.0.second.attack.0.hit": [1]})
    choices = ScriptedChoices({**DODGE_OFFERS})
    result = duel(owner, victim, dice=dice, choices=choices)
    dice.finish()
    # The 4+ dodge held: the defender keeps both wounds, standing.
    assert result.state.second.wounds == 2
    assert result.state.second.condition == Condition.STANDING
    choices.finish()


def test_sidestepper_fails_on_a_three(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.special.ward": [3],
                 "round.0.second.attack.0.hit": [1]})
    choices = ScriptedChoices({**DODGE_OFFERS})
    result = duel(owner, victim, dice=dice, choices=choices)
    dice.finish()
    # The dodge missed its 4+ and the wounding hit went through.
    assert result.state.second.wounds == 1
    choices.finish()


def test_sidestepper_declined_draws_no_dodge(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.second.attack.0.hit": [1]})
    choices = ScriptedChoices({
        "round.0.second.jester-trick.dodge_trick_active": False,
        "round.0.second.jester-trick.banter_trick_active": False,
        "round.0.second.jester-trick.trip_trick_active": False,
    })
    result = duel(owner, victim, dice=dice, choices=choices)
    # A successful ordinary wound without the chosen trick draws no dodge.
    assert result.state.second.wounds == 1
    assert dice.produced("round.0.first.attack.0.special.ward") == 0
    dice.finish()
    choices.finish()


# --- Babbling Banter ----------------------------------------------------------


def test_banter_lowers_the_banterer_and_raises_attacks_against_it(precompiled):
    owner, victim = precompiled().first, precompiled().second
    # With the plain 1-face tape both sides' to-hit rolls (targets >= 2) miss,
    # so the round produces no other combat die; the discriminator is the
    # wound-free tape asserting the pair's own negative control.
    dice = Tape()
    choices = ScriptedChoices({f"round.0.first.jester-trick.{slot}": face
        for slot, face in (("dodge_trick_active", False),
                           ("banter_trick_active", True))})
    result = duel(owner, victim, dice=dice, choices=choices)
    # The source gives the Jester +1 against the affected enemy and the
    # affected enemy -1: targets 3+ and 5+, not just two ordinary misses.
    assert [attack.hit_target for attack in result.attacks] == [3, 5]
    assert dice.produced("round.0.first.attack.0.wound") == 0
    assert dice.produced("round.0.second.attack.0.wound") == 0
    choices.finish()


def test_the_banter_pair_needs_its_chosen_slot(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [4],
                 "round.0.first.attack.0.wound": [3],
                 "round.0.second.attack.0.hit": [4],
                 "round.0.second.attack.0.wound": [1]})
    choices = ScriptedChoices({
        "round.0.first.jester-trick.dodge_trick_active": False,
        "round.0.first.jester-trick.banter_trick_active": False,
        "round.0.first.jester-trick.trip_trick_active": False,
    })
    result = duel(owner, victim, dice=dice, choices=choices)
    # With the trick declined the plain WS3 vs WS3 target of 4+ applies: both
    # sides hit at the recorded 4 and the first wound roll ran.
    assert len(result.attacks) == 2
    assert result.attacks[0].hit is True
    dice.finish()
    choices.finish()


# --- Mantle of Crows ------------------------------------------------------------


def test_mantle_of_crows_resolves_one_pre_attack_strength_2_hit(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape({"round.0.second.mantle-of-crows.wound": [5]})
    result = duel(owner, victim, dice=dice)
    # The automatic S2 pre-attack hit wounded the victim (no to-hit roll was
    # ever requested before the recorded wound key).
    assert result.state.second.wounds == 1
    assert dice.requests.index("round.0.second.mantle-of-crows.wound") == 0
    dice.finish()


def test_without_the_mantle_no_pre_attack_hit_is_resolved(precompiled):
    owner, victim = precompiled().first, precompiled().second
    dice = Tape()
    result = duel(owner, victim, dice=dice)
    assert result.state.second.wounds == 2
    assert dice.produced("mantle-of-crows") == 0
    assert damageless_pre_hits(dice) == 0
    dice.finish()


def damageless_pre_hits(dice):
    return sum(1 for key in dice.requests if "mantle-of-crows" in key)


# --- Backstabber -----------------------------------------------------------------


def test_backstabber_charging_bonus_applies_in_the_first_round(precompiled):
    owner, victim = precompiled().first, precompiled().second
    # WS3 vs WS3 hits on 4+; the printed +1 makes a 3 hit.
    dice = Tape({"round.0.first.attack.0.hit": [3],
                 "round.0.first.attack.0.wound": [3],
                 "round.0.second.attack.0.hit": [1]})
    result = duel(owner, victim, dice=dice, context=DuelContext(
        charging=("first",), active_participant="first"))
    assert result.attacks[0].hit
    assert dice.produced("round.0.first.attack.0.hit") == 1
    dice.finish()


# --- Thin Flesh -----------------------------------------------------------------


def test_thin_flesh_lowers_only_the_close_combat_wound_resolution(precompiled):
    compiled = precompiled()
    victim, attacker = compiled.first, compiled.second
    # S3 vs T3 wounds on 4+, S3 vs T3-1 (Thin Flesh in close combat) on 3+: the
    # recorded 3 discriminates the melee-only -1 Toughness from the outside
    # count, and no injury needs following because the wound roll took exactly
    # one wound without a critical or injury trigger.
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [3],
                 "round.0.second.attack.0.hit": [1]})
    result = duel(attacker, victim, dice=dice)
    assert result.state.second.wounds == 1
    dice.finish()


# --- Slay Large Creature ----------------------------------------------------------


def test_tricks_expire_and_trip_is_one_nominated_attack_per_turn(precompiled):
    owner, victim = precompiled().first, precompiled().second
    owner = replace(owner, characteristics=replace(owner.characteristics, attacks=2))
    dice = Tape({'round.0.first.attack.0.hit': [6],
                 'round.0.first.attack.1.hit': [6],
                 'round.0.first.attack.0.trip-roll': [1],
                 'round.0.first.attack.1.wound': [3]})
    choices = ScriptedChoices({**TRIP_OFFERS, 'round.0.first.attack.0.trip.hit': True})
    result = duel(owner, victim, dice=dice, choices=choices)
    assert result.state.first.trip_trick_active
    assert 'jester.trip' in result.state.first.resources_spent
    assert dice.produced('round.0.first.attack.1.wound') == 1
    dice.finish()
    choices.finish()
    choices = ScriptedChoices({f'round.1.first.jester-trick.{slot}': False
        for slot in ('dodge_trick_active', 'banter_trick_active', 'trip_trick_active')})
    result = resolve_round(owner, victim, result.state, Tape(), choices)
    assert not any((result.state.first.trip_trick_active,
                    result.state.first.dodge_trick_active, result.state.first.banter_trick_active))
    assert 'jester.trip' not in result.state.first.resources_spent
    choices.finish()


def test_trip_can_be_nominated_after_an_earlier_hit_is_declined(precompiled):
    owner = precompiled().first
    owner = replace(owner, characteristics=replace(owner.characteristics, attacks=2))
    dice = Tape({'round.0.first.attack.0.hit': [6],
                 'round.0.first.attack.0.wound': [3],
                 'round.0.first.attack.1.hit': [6],
                 'round.0.first.attack.1.trip-roll': [1]})
    choices = ScriptedChoices({**TRIP_OFFERS,
        'round.0.first.attack.0.trip.hit': False,
        'round.0.first.attack.1.trip.hit': True})
    result = duel(owner, precompiled().second, dice=dice, choices=choices)
    assert result.state.second.condition == Condition.STANDING
    assert dice.produced('round.0.first.attack.1.wound') == 0
    dice.finish()
    choices.finish()


def test_selection_stops_after_acceptance_and_default_policy_can_simulate(precompiled):
    choices = ScriptedChoices({'round.0.first.jester-trick.dodge_trick_active': True})
    owner, victim = precompiled().first, precompiled().second
    result = duel(owner, victim, choices=choices)
    assert result.state.first.dodge_trick_active
    assert not result.state.first.banter_trick_active and not result.state.first.trip_trick_active
    choices.finish()
    # The real API defaults to AlwaysAccept; it must select one, not crash by
    # accepting three independently offered slots.
    from mordheim_combat.modular.duel import simulate_duel_reference
    result = simulate_duel_reference(owner, victim, 1, maximum_rounds=1)
    assert result.simulations == 1


def test_dodge_and_banter_selection_changes_without_leaking_between_turns(precompiled):
    owner, victim = precompiled().first, precompiled().second
    choices = ScriptedChoices({f'round.0.first.jester-trick.{slot}': slot == 'banter_trick_active'
        for slot in ('dodge_trick_active', 'banter_trick_active')})
    result = duel(owner, victim, choices=choices)
    assert [a.hit_target for a in result.attacks] == [3, 5]
    choices.finish()
    choices = ScriptedChoices({'round.1.first.jester-trick.dodge_trick_active': True})
    result = resolve_round(owner, victim, result.state, Tape(), choices)
    assert sorted(a.hit_target for a in result.attacks) == [4, 4]
    assert not result.state.first.banter_trick_active
    assert prepare_special_save_context(owner, victim.main_weapon,
        defender_state=result.state.first).ward_save == 4
    assert prepare_special_save_context(owner, victim.main_weapon,
        defender_state=result.state.first, melee_attack=False).ward_save == 7
    choices.finish()
    choices = ScriptedChoices({f'round.2.first.jester-trick.{slot}': False
        for slot in ('dodge_trick_active', 'banter_trick_active', 'trip_trick_active')})
    result = resolve_round(owner, victim, result.state, Tape(), choices)
    assert prepare_special_save_context(owner, victim.main_weapon,
        defender_state=result.state.first).ward_save == 7
    choices.finish()


@pytest.mark.parametrize('first_round,charging,unseen,expected', [
    (True, True, True, True), (True, True, False, False),
    (True, False, True, False), (False, True, True, False),
])
def test_backstabber_hit_and_injury_share_trigger_and_expiry(precompiled, first_round, charging, unseen, expected):
    owner, victim = precompiled().first, precompiled().second
    victim = replace(victim, characteristics=replace(victim.characteristics, wounds=1))
    own = initialize_fighter(owner, Tape(), 'first')
    other = initialize_fighter(victim, Tape(), 'second')
    dice = Tape({'attack.hit': [4], 'attack.wound': [4], 'attack.injury.0': [4]})
    result = resolve_reference_attack(owner, victim, own, other, owner.main_weapon,
        dice, key='attack', first_round=first_round, charging=charging)
    assert result.defender.condition == (Condition.OUT if expected else Condition.STUNNED)
    assert prepare_hit_context(owner, victim, own, other, owner.main_weapon,
        _combined_effect(owner, owner.main_weapon), first_round=first_round,
        charging=charging).modifier == int(expected)
    dice.finish()


def test_mantle_is_a_melee_hit_with_thin_flesh_and_selected_dodge(precompiled):
    owner, victim = precompiled().first, precompiled().second
    choices = ScriptedChoices(DODGE_OFFERS)
    # S2 against Thin Flesh's melee T2 wounds on 4+, then the chosen dodge saves.
    dice = Tape({'round.0.second.mantle-of-crows.wound': [4],
                 'round.0.second.mantle-of-crows.special.ward': [4]})
    result = duel(owner, victim, dice=dice, choices=choices)
    assert result.attacks[0].wounded and result.attacks[0].saved
    assert result.state.second.wounds == 2
    assert not any(key.endswith('.mantle-of-crows.hit') for key in dice.requests)
    dice.finish()
    choices.finish()


def test_mantle_repeats_each_phase_at_fixed_strength_without_bearer_damage(precompiled):
    owner, victim = precompiled().first, precompiled().second
    owner = replace(owner, global_effects=replace(owner.global_effects, strength_bonus=4, damage=3))
    victim = replace(victim, characteristics=replace(victim.characteristics, wounds=4))
    dice = Tape({'round.0.second.mantle-of-crows.wound': [5]})
    result = duel(owner, victim, dice=dice)
    assert result.state.second.wounds == 3
    assert result.attacks[0].damage == 1
    assert dice.requests[0] == 'round.0.second.mantle-of-crows.wound'
    dice.finish()
    dice = Tape({'round.1.second.mantle-of-crows.wound': [4]})
    result = resolve_round(owner, victim, result.state, dice, ScriptedChoices())
    assert result.state.second.wounds == 3  # S2 vs T3 needs 5+, not 4+.
    assert dice.requests[0] == 'round.1.second.mantle-of-crows.wound'
    dice.finish()


def test_thin_flesh_does_not_change_profile_or_non_melee_toughness(precompiled):
    owner, victim = precompiled().first, precompiled().second
    own = initialize_fighter(owner, Tape(), 'first')
    other = initialize_fighter(victim, Tape(), 'second')
    effect = _combined_effect(owner, owner.main_weapon)
    assert prepare_wound_context(owner, victim, own, other, owner.main_weapon, effect).toughness == 2
    assert prepare_wound_context(owner, victim, own, other, owner.main_weapon, effect,
        melee_attack=False).toughness == 3
    assert victim.characteristics.toughness == other.toughness == 3
    dice = Tape({'attack.hit': [6], 'attack.wound': [3]})
    result = resolve_reference_attack(owner, victim, own, other, owner.main_weapon,
        dice, key='attack', melee_attack=False)
    assert not result.wounded and result.defender.wounds == 2
    dice.finish()


@pytest.mark.parametrize('first_round,charging,large,expected', [
    (True, True, True, 5), (True, True, False, 4),
    (True, False, True, 3), (False, True, True, 3),
])
def test_slay_large_creature_stacks_with_weapon_charge_and_expires(first_round, charging, large, expected):
    # The recorded pair does not carry the tagged owner and the size-tagged
    # victim this stack test needs.
    owner = fighter('rule.slay-large-creature')
    victim = fighter(*(['size.large'] if large else []))
    owner = replace(owner, main_weapon=replace(owner.main_weapon, charge_strength_bonus=1))
    own = initialize_fighter(owner, Tape(), 'first')
    other = initialize_fighter(victim, Tape(), 'second')
    effect = _combined_effect(owner, owner.main_weapon)
    assert prepare_wound_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=first_round, charging=charging).strength == expected
    armour = prepare_armour_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=first_round, charging=charging)
    assert armour.strength == expected


def test_sidestepper_remains_unmodifiable_for_strong_magical_attacks(precompiled):
    owner, victim = precompiled().first, precompiled().second
    owner = replace(owner, main_weapon=replace(owner.main_weapon,
        tags=(*owner.main_weapon.tags, 'attack.magical')))
    dice = Tape({'round.0.first.attack.0.hit': [6],
                 'round.0.first.attack.0.wound': [4],
                 'round.0.first.attack.0.special.ward': [4]})
    choices = ScriptedChoices(DODGE_OFFERS)
    result = duel(owner, victim, dice=dice, choices=choices)
    assert result.attacks[0].saved and result.state.second.wounds == 2
    dice.finish()
    choices.finish()


# --- Needle and Thread --------------------------------------------------------


def fragile(*tags: str, weapon: str = "weapon.mace"):
    """A plain fighter with a single Wound, so an unsaved wound forces an injury roll."""
    base = compile_fighter(FighterBuild("mordheim",
        Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
        main_weapon_id=weapon, armour_id="armour.no-armour"))
    return replace(base, global_effects=replace(base.global_effects,
        tags=(*base.global_effects.tags, *tags)))


def test_needle_and_thread_sews_the_mouth_of_the_opponent_it_stuns(precompiled):
    owner, victim = precompiled().first, precompiled().second
    # The mace prints 2-4 as stunned, so the recorded 4 is the printed stun that
    # triggers the sewing; a 5 or 6 takes the opponent out and sews nothing.
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.injury.0": [4]})
    result = duel(owner, victim, dice=dice)
    assert result.state.second.condition == Condition.STUNNED
    assert result.state.second.mouth_sewn is True
    # A stunned warrior strikes nothing, so the second side draws no die at all.
    assert dice.produced("round.0.second.attack.0.hit") == 0
    dice.finish()
    # Negative control: the same stun without the mechanic sews no mouth.
    # Both sides are the recorded plain fragile fighter, exactly as before.
    control, victim = precompiled().second, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.injury.0": [4]})
    result = duel(control, victim, dice=dice)
    assert result.state.second.condition == Condition.STUNNED
    assert result.state.second.mouth_sewn is False
    dice.finish()


def leader_fighter(leadership: int, *tags: str):
    """A plain fighter with a supplied warband tag, for Leadership borrows."""
    base = compile_fighter(FighterBuild("mordheim",
        Characteristics(3, 3, 3, 1, 3, 1, leadership=leadership),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))
    return replace(base, global_effects=replace(base.global_effects,
        tags=(*base.global_effects.tags, "band.probe", *tags)))


def borrow(provider):
    """One Leadership test that may borrow the supplied provider within six inches."""
    recipient = leader_fighter(5)
    context = DuelContext(charging=("first",), active_participant="first",
        nearby=(LocalParticipant("boss", "first", provider),),
        distances=(("first", "boss", 4),))
    dice = Tape({"probe.0": [3], "probe.1": [5]})
    state = initialize_duel(recipient, fragile(), Tape(), context=context)
    return state, dice, recipient


def test_a_sewn_leader_cannot_lend_its_leadership_ability():
    # The duel sews the mouth of an opponent it stuns; a Leader is used as a
    # supplied non-combatant fact, so the printed denial reaches the borrow loop
    # through the supplied sewn-mouth fact, exactly as Backstabber's charge does.
    state, dice, recipient = borrow(leader_fighter(9, "mechanic.leader-six"))
    choices = ScriptedChoices({"probe.leader.boss": True})
    assert resolve_local_leadership(recipient, state, dice, choices, "probe", first=True) is True
    # The 8 rolled passes only on the borrowed 9: the Leader's ability was used.
    assert choices.offered == ["probe.leader.boss"]
    dice.finish()
    choices.finish()
    sewn = leader_fighter(9, "mechanic.leader-six", "condition.mouth-sewn")
    state, dice, recipient = borrow(sewn)
    choices = ScriptedChoices()
    assert resolve_local_leadership(recipient, state, dice, choices, "probe", first=True) is False
    # No provider was offered at all, and the roll of 8 fails against the own 5.
    assert choices.offered == []
    dice.finish()
    choices.finish()


# --- Lycanthrope ---------------------------------------------------------------


def test_lycanthrope_transforms_on_a_four_plus_and_keeps_the_wolf_form(precompiled):
    owner, beast = precompiled().first, precompiled().second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.lycanthrope.0": [4],
                 "round.0.second.attack.0.hit": [1]})
    result = duel(owner, beast, dice=dice)
    wolf = result.state.second
    # The printed 4+ escapes: the wolf profile replaces the man's T3/W1 and no
    # injury table is rolled at all.
    assert (wolf.hillman_wolf, wolf.wounds, wolf.condition) == (True, 2, Condition.STANDING)
    assert (wolf.weapon_skill, wolf.strength, wolf.toughness, wolf.initiative, wolf.attacks) == (4, 4, 4, 5, 2)
    dice.finish()
    # The form survives the turn that rolled it: a second round resolves with the
    # wolf state and requests no further transformation die.
    second = Tape({"round.1.first.attack.0.hit": [1], "round.1.second.attack.0.hit": [1]})
    followed = resolve_round(owner, beast, result.state, second, ScriptedChoices())
    assert followed.state.second.hillman_wolf is True
    assert second.produced("round.1.first.attack.0.lycanthrope.0") == 0
    second.finish()


def test_a_failed_lycanthrope_roll_keeps_the_printed_injury_penalty(precompiled):
    # A plain sword, not the mace: the mace's own concussion mapping would mask
    # the printed -1 by turning the modified 2 back into a stun.
    compiled = precompiled()
    owner, beast = compiled.first, compiled.second
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.lycanthrope.0": [3],
                 "round.0.first.attack.0.injury.0": [3]})
    result = duel(owner, beast, dice=dice)
    # A failed roll at -1 turns the printed 3 into 2, which is knocked down;
    # without the penalty the same face is stunned.
    assert result.state.second.condition == Condition.KNOCKED_DOWN
    assert result.state.second.hillman_wolf is False
    dice.finish()
    control, victim = owner, owner
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [4],
                 "round.0.first.attack.0.injury.0": [3]})
    result = duel(control, victim, dice=dice)
    assert result.state.second.condition == Condition.STUNNED
    dice.finish()


def test_the_wolf_form_discards_the_kit_and_keeps_the_bite_attack(precompiled):
    beast = precompiled().first
    man = initialize_fighter(beast, Tape(), "second")
    wolf = replace(man, hillman_wolf=True)
    discarded = equipment_for_state(beast, wolf, first_round=False)
    # Wolf form: every garment and weapon is gone, so only teeth and claws strike
    # with no unarmed penalty and the printed Bite resolves at -1 Strength.
    assert set(discarded.main_weapon.tags) == {"weapon.natural-attacks", "rule.unarmed-without-penalties"}
    assert discarded.off_hand is None and discarded.armour_save == 7 and discarded.helmet_save == 7
    assert discarded.global_effects.parry is False
    assert [(e.tags, e.strength_bonus) for e in discarded.extra_attacks] == \
        [(('rule.hillman-bite',), -1)]
    # Negative control: the man form keeps its carried weapon.
    kept = equipment_for_state(beast, man, first_round=False)
    assert kept.main_weapon is not None and kept.main_weapon.tags != discarded.main_weapon.tags


def test_slay_large_creature_grants_one_strength_on_the_charged_large_target(precompiled):
    slayer, victim = precompiled().first, precompiled().second
    # Charging the large target: S+1 = 4 vs T3 needs a 3+, so the recorded 3
    # discriminates the charge Strength bonus from the ordinary S3-vs-T3 4+.
    dice = Tape({"round.0.first.attack.0.hit": [6],
                 "round.0.first.attack.0.wound": [3],
                 "round.0.second.attack.0.hit": [1]})
    result = duel(slayer, victim, dice=dice, context=DuelContext(
        charging=("first",), active_participant="first"))
    assert result.state.second.wounds == 1
    dice.finish()
