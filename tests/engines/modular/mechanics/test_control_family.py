"""Control family: the printed Vampire control powers and Hypnotic Dance.

Canonical bindings and recipient eligibility are checked separately under
``tests/knowledge`` and ``tests/construction``. These tests prove the modular
consequence with negative controls.
The runtime witnesses use synthetic tag injections on a plain compiled fighter
(exactly as ``test_crude_belch`` does for Shifty and the Mark of Shornaal), so
they discriminate the consumer and make no claim about a legal build.
"""
from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from mordheim_combat.modular.rounds import (
    CONTROL_POWERS,
    SEDUCTION_RESOURCES,
    resolve_round,
)
from mordheim_combat.modular.state import initialize_duel
compile_fighter = None
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Use frozen build results for the migrated preparations."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)









class ControlDice:
    """Fail the named tests and answer every other request low.

    A 2D6 Leadership test against the table's own value 7 fails on the high
    value and passes on the low one, and the same low value misses an ordinary
    to-hit roll, so a clause that makes a hit automatic is distinguishable from
    one that rolls for it.
    """

    def __init__(self, *failing: str, high: int = 6, low: int = 2) -> None:
        self.failing, self.high, self.low = failing, high, low

    def roll(self, request):
        return (self.high if any(request.key.startswith(prefix) for prefix in self.failing)
                else self.low)


def synthetic(*tags: str):
    """A plain compiled fighter carrying only the supplied discriminating tags."""
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))
    return replace(fighter, global_effects=replace(
        fighter.global_effects, tags=(*fighter.global_effects.tags, *tags)))


def duel(owner, victim, dice, *, state=None):
    if state is None:
        state = initialize_duel(owner, victim, dice, context=DuelContext(
            charging=("first",), active_participant="first"))
    return resolve_round(owner, victim, state, dice)


# --- the canonical records carry their printed binding ----------------------



def test_khemrian_seduction_reaches_the_legal_selected_recipient_and_round(precompiled):
    compiled = precompiled()
    plain, selected = compiled.first, compiled.second
    assert "mechanic.lahmian-seduction" not in plain.global_effects.tags
    assert "mechanic.lahmian-seduction" in selected.global_effects.tags
    result = duel(selected, synthetic(), ControlDice("round.0.second.lahmian-seduction"))
    assert result.state.second.charm_attack_blocked


def test_the_control_table_keeps_each_printed_qualifier_separate():
    table = {power.tag: power for power in CONTROL_POWERS}
    gaze, lahmia, lahmian = (table["mechanic.hypnotic-gaze"],
                             table["mechanic.lahmia-seduction"],
                             table["mechanic.lahmian-seduction"])
    assert gaze.own_value_only and gaze.auto_hit
    assert gaze.exclusions == ("mechanic.psychology-immunity",)
    assert lahmia.exclusions == ("mechanic.psychology-immunity", "nature.undead",
                                 "nature.daemon", "mechanic.stupidity")
    assert lahmia.male_only and lahmia.own_turn_only and lahmia.persistent
    assert lahmian.own_test and lahmian.persistent and not lahmian.male_only
    assert len(SEDUCTION_RESOURCES) == 2


# --- Hypnotic Gaze ----------------------------------------------------------

def test_hypnotic_gaze_bars_the_target_and_makes_attacks_automatic(precompiled):
    compiled = precompiled()
    owner, victim = compiled.first, compiled.second
    result = duel(owner, victim, ControlDice("round.0.second.hypnotic-gaze"))
    assert result.state.second.charm_attack_blocked
    assert result.state.second.charm_auto_hit
    # The barred victim contributes nothing, and the gazer's single attack hits
    # although every ordinary to-hit request answers low: the clause makes the
    # hit automatic, and the engine records the always-hits face (the convention
    # test_crude_belch uses for its automatic hits), never a rolled value.
    assert len(result.attacks) == 1
    assert result.attacks[0].hit is True
    # No to-hit roll was drawn: the recorded face stays 0, while an ordinary
    # attack of this same duel records the face it drew (the low 2).
    assert result.attacks[0].hit_roll == 0
    ordinary = duel(victim, victim, ControlDice())
    assert [attack.hit_roll for attack in ordinary.attacks] == [2, 2]


def test_the_gaze_needs_its_printed_selection(precompiled):
    compiled = precompiled()
    result = duel(compiled.first, compiled.second, ControlDice())
    assert not result.state.second.charm_attack_blocked
    assert not result.state.second.charm_auto_hit
    assert [attack.hit for attack in result.attacks] == [False, False]


def test_the_gaze_spares_a_psychology_immune_target(precompiled):
    compiled = precompiled()
    owner, victim = compiled.first, compiled.second
    result = duel(owner, victim,
                  ControlDice("round.0.second.hypnotic-gaze"))
    assert not result.state.second.charm_attack_blocked
    assert len(result.attacks) == 2


# --- the two Seduction copies ----------------------------------------------

@pytest.mark.usefixtures('_frozen_compiles')
def test_lahmia_seduction_controls_only_the_printed_male_recipient(precompiled):
    compiled = precompiled()
    owner, victim = compiled.first, compiled.second
    result = duel(owner, victim, ControlDice("round.0.second.lahmia-seduction"))
    assert "seduction.controlled.lahmia" in result.state.second.resources_spent
    assert result.state.second.charm_attack_blocked
    # Only the Vampire struck: the controlled warrior's own attack was barred.
    assert len(result.attacks) == 1
    assert result.attacks[0].hit is False
    # The printed recipient is male; a female opponent is unaffected.
    female = duel(owner, synthetic("sex.female"),
                  ControlDice("round.0.second.lahmia-seduction"))
    assert not female.state.second.resources_spent
    assert len(female.attacks) == 2
    # The fact is supplied, never inferred.
    with pytest.raises(ValueError, match="explicit male/female"):
        duel(owner, synthetic(), ControlDice())


def test_lahmia_control_survives_a_missed_round_and_ends_in_the_recovery_test(precompiled):
    compiled = precompiled()
    owner, victim = compiled.first, compiled.second
    established = duel(owner, victim, ControlDice("round.0.second.lahmia-seduction"))
    assert "seduction.controlled.lahmia" in established.state.second.resources_spent
    # Round 1 misses again, so only the printed Recovery-phase test can end it.
    later = duel(owner, victim, ControlDice(), state=established.state)
    assert later.state.round_index == 2
    assert "seduction.controlled.lahmia" not in later.state.second.resources_spent
    assert not later.state.second.charm_attack_blocked
    assert len(later.attacks) == 2


def test_lahmian_seduction_needs_the_vampires_own_test_first(precompiled):
    compiled = precompiled()
    owner, victim = compiled.first, compiled.second
    # The Vampire's own test passes and the victim's own test fails: the control
    # holds for that phase and the printed attack releases it.
    controlled = duel(owner, victim, ControlDice(
        "round.0.second.lahmian-seduction.0", "round.0.second.lahmian-seduction.1"))
    assert controlled.state.second.charm_attack_blocked
    assert len(controlled.attacks) == 1
    assert "seduction.controlled.lahmian" not in controlled.state.second.resources_spent
    # A failed own test leaves the victim alone, in reach and unbarred.
    refused = duel(owner, victim, ControlDice("round.0.first.lahmian-seduction.own-test"))
    assert not refused.state.second.charm_attack_blocked
    assert not refused.state.second.resources_spent
    assert len(refused.attacks) == 2
