"""Call of the Night Haint Violent Entry: a supplied summon turn pays its charge only.

The clause is: "Malignant Spirits contained within the Requilary thirst for the
moment they are released into battle: they gain +1 to hit and +1 Strength if they
charge on the turn they were summoned."

The summoning procedure is outside the duel, so the caller supplies the fact
(``condition.summoned-this-turn``) and the engine pays the printed bonus only when
the same fighter charges on that turn.  A Malignant Spirit is WS3 S3: against a
WS3 T3 opponent the printed charge moves the To Hit target from 4+ to 3+ and the
To Wound target from 4+ to 3+.
"""
from __future__ import annotations

import sys
import pytest

from mordheim_combat.modular.contexts import (_combined_effect, prepare_hit_context,
    prepare_wound_context)
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.phases import resolve_hit
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


SUMMON = "condition.summoned-this-turn"
BAND = "call-of-the-night-haint-mim"
PROFILE = "malignant-spirits"


class Tape:
    """Listed faces are consumed per key in order; unlisted requests answer 1."""

    def __init__(self, faces=None):
        self.faces = {key: list(values) for key, values in (faces or {}).items()}
        self.requests: list[str] = []

    def roll(self, request):
        self.requests.append(request.key)
        queue = self.faces.get(request.key)
        return queue.pop(0) if queue else 1

    def produced(self, key: str) -> int:
        return sum(1 for entry in self.requests if entry == key)

    def finish(self):
        leftover = {key: faces for key, faces in self.faces.items() if faces}
        if leftover:
            raise AssertionError(f"unused listed rolls: {sorted(leftover)}")


class NoDecisions:
    def choose(self, key, context=None):
        raise AssertionError(f"unexpected decision: {key}")


def spirit(*conditions):
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=PROFILE,
        main_weapon_id="weapon.sword", condition_ids=conditions))


def foe():
    """WS3 T3 W2: both printed bonuses move exactly one threshold."""
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace"))


def resolve_one_round(owner, victim, *, dice, charging=("first",)):
    state = initialize_duel(owner, victim, dice,
        context=DuelContext(charging=charging, active_participant="first"))
    return resolve_round(owner, victim, state, dice, NoDecisions())


@pytest.mark.phase3_rules
def test_charging_on_the_summoned_turn_gains_both_printed_bonuses(precompiled):
    compiled = precompiled()
    owner, victim, dice = compiled.first, compiled.second, Tape({
        "round.0.first.attack.0.hit": [3], "round.0.first.attack.0.wound": [3]})
    result = resolve_one_round(owner, victim, dice=dice)
    attack = result.attacks[0]
    assert attack.attacker is not None and attack.hit_target == 3
    assert attack.hit and attack.wounded
    # S3+1 vs T3 wounds on 3+; the unmodified profile needs 4+ and this die fails.
    assert result.state.second.wounds == 1
    dice.finish()


@pytest.mark.phase3_rules
def test_a_charge_without_the_supplied_summon_turn_grants_nothing(precompiled):
    compiled = precompiled()
    owner, victim, dice = compiled.first, compiled.second, Tape({"round.0.first.attack.0.hit": [3]})
    result = resolve_one_round(owner, victim, dice=dice)
    assert result.attacks[0].hit_target == 4
    assert not result.attacks[0].hit
    assert dice.produced("round.0.first.attack.0.wound") == 0
    dice.finish()


@pytest.mark.phase3_rules
def test_the_supplied_fact_without_a_charge_grants_nothing(precompiled):
    compiled = precompiled()
    owner, victim = compiled.first, compiled.second
    dice = Tape({"round.0.first.attack.0.hit": [3]})
    result = resolve_one_round(owner, victim, dice=dice, charging=())
    assert result.attacks[0].hit_target == 4
    assert not result.attacks[0].hit
    assert dice.produced("round.0.first.attack.0.wound") == 0
    dice.finish()
    # The same fighter and die hit when the charge is what is missing, not the fact.
    own, other = initialize_fighter(owner, Tape(), "a"), initialize_fighter(victim, Tape(), "b")
    effect = _combined_effect(owner, owner.main_weapon)
    context = prepare_hit_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=True, charging=False, key="a")
    assert resolve_hit(context, Tape()).target == 4
    context = prepare_hit_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=True, charging=True, key="a")
    assert resolve_hit(context, Tape()).target == 3


@pytest.mark.phase3_rules
def test_the_bonus_does_not_persist_into_later_rounds(precompiled):
    compiled = precompiled()
    owner, victim, dice = compiled.first, compiled.second, Tape({
        "round.0.first.attack.0.hit": [3], "round.0.first.attack.0.wound": [3]})
    first = resolve_one_round(owner, victim, dice=dice)
    assert first.attacks[0].hit_target == 3
    dice.finish()
    dice = Tape({"round.1.first.attack.0.hit": [3]})
    later = resolve_round(owner, victim, first.state, dice, NoDecisions())
    assert later.attacks[0].hit_target == 4
    assert dice.produced("round.1.first.attack.0.wound") == 0
    # The printed Strength bonus expires with the charge too.
    own, other = initialize_fighter(owner, Tape(), "a"), initialize_fighter(victim, Tape(), "b")
    effect = _combined_effect(owner, owner.main_weapon)
    charging = prepare_wound_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=True, charging=True, key="a")
    later_wound = prepare_wound_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=False, charging=True, key="a")
    assert charging.strength == 4 and later_wound.strength == 3
    dice.finish()


@pytest.mark.phase3_rules
def test_repeating_the_supplied_fact_does_not_double_the_bonus():
    single, repeated = spirit(SUMMON), spirit(SUMMON, SUMMON)
    assert single.global_effects.charge_strength_bonus == 1
    assert repeated.global_effects.charge_strength_bonus == 1
    for owner in (single, repeated):
        own, other = initialize_fighter(owner, Tape(), "a"), initialize_fighter(foe(), Tape(), "b")
        effect = _combined_effect(owner, owner.main_weapon)
        context = prepare_hit_context(owner, foe(), own, other, owner.main_weapon, effect,
            first_round=True, charging=True, key="a")
        wound = prepare_wound_context(owner, foe(), own, other, owner.main_weapon, effect,
            first_round=True, charging=True, key="a")
        assert context.modifier == 1 and wound.strength == 4
