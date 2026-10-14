"""T13 M4d: Devoted to the Vampire and The Bitten, end to end in the modular engine.

Both families are supplied-condition mechanics, so every expectation here is
derived from the printed clause and not from the current engine behaviour:

* Devoted to the Vampire (Khemri Lahmian Beloved and Lackeys) reads a supplied
  Lahmian Vampire condition - Knocked Down, or killed in close combat by the
  opposing duellist - and its Frenzy is the one Frenzy that ends by itself, when
  she stands up or when her killer dies.  Her killer is also the target of the
  printed Hatred, whose duration is that model being in action.
* The Bitten (Masters of Horror) rolls on its own turn, keeps the Transformed
  form until a 1, does not roll while transformed and in combat, casts off all
  equipment save a dagger and suffers no penalties for fighting unarmed.

``KeyedDice`` is a strict, order-independent tape: an unlisted request and an
unused entry both fail, so a negative control proves that no die was asked for
and an activation proves the printed die or reroll was consumed exactly once.
A roll of 1 is below every To Hit target here, so a miss costs no further die.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import FighterState, initialize_duel
from mordheim_combat.phases import Condition
from mordheim_combat_lab.verification.dice import StrictDecisions
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

DEVOTED = "mechanic.devoted-to-the-vampire"
HATRED = "mechanic.devoted-killer-hatred"
TRANSFORM = "mechanic.bitten-transform"


class KeyedDice:
    """Every listed die is asked exactly once and no other die is asked."""

    def __init__(self, values: dict[str, int]):
        if len(values) != len(set(values)):
            raise ValueError("duplicate die keys in the fixture")
        self.values = dict(values)
        self.requests: list[str] = []

    def roll(self, request):
        self.requests.append(request.key)
        if request.key not in self.values:
            raise EvidenceMismatch(f"unexpected roll {request.key} D{request.sides}")
        return self.values.pop(request.key)

    def finish(self):
        if self.values:
            raise EvidenceMismatch(f"unused rolls: {sorted(self.values)}")


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options))


def bare(*, weapon="weapon.mace", off_hand_id=None, armour="armour.no-armour", wounds=1, **traits):
    """An unidentified opponent, so no band rule can be mistaken for the clause."""
    return compile_fighter(FighterBuild("mordheim", Characteristics(4, 3, 3, wounds, 5, 1, leadership=7),
        main_weapon_id=weapon, off_hand_id=off_hand_id, armour_id=armour,
        trait_overrides=traits))


def lahmain(profile, *, weapon="weapon.mace", down=False, killed=False, **options):
    traits = {}
    if down:
        traits["devoted_vampire_down"] = True
    if killed:
        traits["devoted_vampire_killed"] = True
    return canonical("khemri-lahmian-brotherhood", profile, weapon, collection="trollheim",
        trait_overrides=traits, **options)


def bitten(*, weapon="weapon.mace", **traits):
    return compile_fighter(FighterBuild("mordheim", band_id="masters-of-horror-sylv",
        profile_id="the-bitten", main_weapon_id=weapon, trait_overrides=traits))


def duel(first, second, *, charging="first"):
    return initialize_duel(first, second, KeyedDice({}), context=DuelContext(
        charging=(charging,), active_participant="first"))


def misses(round_index, owner, count, *, first=0):
    """Below every To Hit target in these fixtures, and no wound die follows."""
    return {f"round.{round_index}.{owner}.attack.{index}.hit": 1
            for index in range(first, first + count)}


def drop(fighter, tag):
    """The same fighter, re-supplied one combat phase later without one fact."""
    return replace(fighter, global_effects=replace(fighter.global_effects,
        tags=tuple(entry for entry in fighter.global_effects.tags if entry != tag)))


# --- Devoted to the Vampire: sharing and the supplied facts ----------------

def test_devoted_is_granted_to_both_printed_recipients_and_to_no_other_profile():
    for profile in ("beloved", "lackeys"):
        fighter = lahmain(profile)
        assert DEVOTED in fighter.global_effects.tags, profile
        assert HATRED in fighter.global_effects.tags, profile
    for profile in ("lahmian-vampire", "necromancer", "blood-sister", "skeleton-warriors"):
        fighter = lahmain(profile)
        assert DEVOTED not in fighter.global_effects.tags, profile
        assert HATRED not in fighter.global_effects.tags, profile


def test_the_supplied_vampire_condition_projects_only_for_a_recipient():
    assert "condition.devoted-vampire-down" in lahmain("beloved", down=True).global_effects.tags
    assert "condition.devoted-vampire-killed" in lahmain("lackeys", killed=True).global_effects.tags
    # Negative control: the condition is not a fact any profile may declare.
    with pytest.raises(ValueError, match="Devoted to the Vampire"):
        compile_fighter(FighterBuild("mordheim", band_id="masters-of-horror-sylv",
            profile_id="the-bitten", main_weapon_id="weapon.mace",
            trait_overrides={"devoted_vampire_down": True}))
    # The Vampire is Knocked Down or dead, never both at once.
    with pytest.raises(ValueError, match="Knocked Down and killed"):
        lahmain("beloved", down=True, killed=True)


# --- Devoted to the Vampire: Frenzy while she is down ----------------------

def test_devoted_frenzy_lasts_until_the_supplied_vampire_stands_up():
    bearer = lahmain("beloved", down=True)
    foe = bare()
    dice = KeyedDice({**misses(0, "first", 2), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(bearer, foe, duel(bearer, foe), dice, choices)
    dice.finish(); choices.finish()
    # Frenzy doubles her printed one Attack; the foe still strikes once.
    assert result.state.first.frenzy and len(result.attacks) == 3
    # She stands up: the withdrawn supplied fact ends exactly that frenzy, and
    # nothing else has to be undone.
    stood = drop(bearer, "condition.devoted-vampire-down")
    dice = KeyedDice({**misses(1, "first", 1), **misses(1, "second", 1)})
    choices = StrictDecisions([])
    after = resolve_round(stood, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    assert not after.state.first.frenzy and len(after.attacks) == 2


def test_devoted_frenzy_is_not_granted_without_its_supplied_condition():
    bearer = lahmain("beloved")
    foe = bare()
    dice = KeyedDice({**misses(0, "first", 1), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(bearer, foe, duel(bearer, foe), dice, choices)
    dice.finish(); choices.finish()
    assert not result.state.first.frenzy
    assert len(result.attacks) == 2  # her single printed Attack, undoubled


# --- Devoted to the Vampire: Hatred against her killer --------------------

def test_devoted_hatred_rerolls_a_first_round_miss_against_the_killer():
    bearer = lahmain("beloved", killed=True)
    killer = bare()
    dice = KeyedDice({
        "round.0.first.attack.0.hit": 1,
        "round.0.first.attack.0.hit.reroll": 1,   # only the printed Hatred asks for it
        **misses(0, "first", 1, first=1),
        "round.0.first.attack.1.hit.reroll": 1,
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    result = resolve_round(bearer, killer, duel(bearer, killer), dice, choices)
    dice.finish(); choices.finish()
    # The kill prints Frenzy as well as Hatred, so her pool is doubled too.
    assert result.state.first.frenzy and len(result.attacks) == 3
    assert "round.0.first.attack.0.hit.reroll" in dice.requests
    assert result.attacks[0].hit_roll == 1 and not result.attacks[0].hit


def test_devoted_hatred_and_frenzy_end_after_the_killer_dies():
    bearer = lahmain("beloved", killed=True)
    killer = bare()
    before = duel(bearer, killer)
    fallen = replace(before, second=replace(before.second, condition=Condition.OUT))
    # No reroll die is offered: the printed Hatred lasts only while the killer is
    # in action, and the Frenzy the kill caused ends with that model too.
    dice = KeyedDice({})
    choices = StrictDecisions([])
    result = resolve_round(bearer, killer, fallen, dice, choices)
    dice.finish(); choices.finish()
    assert not result.state.first.frenzy
    assert not result.attacks


# --- The Bitten: activation, persistence and the combat exception ---------

def test_the_bitten_transforms_on_six_and_persists_without_rolling_in_combat():
    mutant = bitten()
    foe = bare()
    dice = KeyedDice({"round.0.first.bitten": 6, **misses(0, "first", 2), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, duel(mutant, foe), dice, choices)
    dice.finish(); choices.finish()
    # The form prints Frenzy, which doubles the printed one Attack, and the
    # printed unarmed penalty removal lifts the one-Attack fist cap with it.
    assert result.state.first.transformed and result.state.first.frenzy
    assert len(result.attacks) == 3
    # On the opponent's turn no transformation die is asked for, and the form
    # survives the phase.
    dice = KeyedDice({**misses(1, "first", 2), **misses(1, "second", 1)})
    choices = StrictDecisions([])
    second = resolve_round(mutant, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    assert second.state.first.transformed and second.state.first.frenzy
    # Back on its own turn it is Transformed and in combat, so the printed
    # exception consumes no die for as long as the form lasts.
    dice = KeyedDice({**misses(2, "first", 2), **misses(2, "second", 1)})
    choices = StrictDecisions([])
    third = resolve_round(mutant, foe, second.state, dice, choices)
    dice.finish(); choices.finish()
    assert third.state.first.transformed
    assert "round.2.first.bitten" not in dice.requests


def test_the_bitten_reverts_to_human_form_on_a_roll_of_one():
    mutant = bitten()
    foe = bare()
    chained = replace(duel(mutant, foe), engaged=False,
        first=replace(FighterState(wounds=1), transformed=True))
    # Madness applies in the own Recovery phase even without contact.
    dice = KeyedDice({"round.0.first.bitten": 1,
                     "round.0.first.stupidity.0": 1, "round.0.first.stupidity.1": 1})
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, chained, dice, choices)
    dice.finish(); choices.finish()
    assert not result.state.first.transformed
    assert result.state.first.bitten_result == 1
    assert not result.attacks


def test_the_bitten_acts_normally_on_two_to_five():
    mutant = bitten()
    foe = bare()
    dice = KeyedDice({"round.0.first.bitten": 4, **misses(0, "first", 1), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, duel(mutant, foe), dice, choices)
    dice.finish(); choices.finish()
    assert not result.state.first.transformed and not result.state.first.frenzy
    assert result.state.first.bitten_result == 4
    assert len(result.attacks) == 2


# --- The Bitten: Madness lasts this turn only -----------------------------

def test_the_bitten_madness_is_a_this_turn_stupidity():
    mutant = bitten()
    foe = bare()
    # The opponent closes the charge, so the Bitten is not the charging side and
    # its failure reads only as the printed consequence, never as a charge that
    # failed to be completed.
    dice = KeyedDice({
        "round.0.first.bitten": 1,
        "round.0.first.stupidity.0": 6,
        "round.0.first.stupidity.1": 6,
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, duel(mutant, foe, charging="second"), dice, choices)
    dice.finish(); choices.finish()
    # The failed test is the printed consequence: no attack that phase, while the
    # opponent still strikes.
    assert result.state.first.stupidity_failed
    assert len(result.attacks) == 1
    # The result is this-turn only: the next phase grants no Stupidity at all,
    # which the tape proves because no Leadership die is offered, and the Bitten
    # strikes exactly as the printed "Act as normal" branch does.
    dice = KeyedDice({**misses(1, "first", 1), **misses(1, "second", 1)})
    choices = StrictDecisions([])
    after = resolve_round(mutant, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    assert not after.state.first.stupidity_failed and after.state.first.bitten_result == 0
    assert len(after.attacks) == 2


def test_the_bitten_madness_never_tests_another_model():
    mutant = bitten()
    foe = bare()
    dice = KeyedDice({"round.0.first.bitten": 3, **misses(0, "first", 1), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, duel(mutant, foe), dice, choices)
    dice.finish(); choices.finish()
    assert not result.state.first.stupidity_failed and not result.state.second.stupidity_failed


# --- The Bitten: cast-off equipment and unarmed penalties -----------------

def test_transforming_casts_off_everything_except_a_dagger():
    armed = bare(weapon="weapon.sword", off_hand_id="defence.shield", armour="armour.light-armour")
    assert armed.armour_save < 7 and armed.off_hand is not None
    stripped = equipment_for_state(armed, FighterState(wounds=1, transformed=True), first_round=True)
    assert stripped.off_hand is None
    assert "weapon.fist" in stripped.main_weapon.tags  # no dagger was carried
    assert stripped.armour_save == 7 and stripped.helmet_save == 7
    # A carried dagger is retained, in its own hand.
    dagger = bare(weapon="weapon.dagger")
    kept = equipment_for_state(dagger, FighterState(wounds=1, transformed=True), first_round=True)
    assert "weapon.dagger" in kept.main_weapon.tags and kept.off_hand is None
    # Negative control: the untransformed fighter keeps its whole equipment.
    assert equipment_for_state(armed, FighterState(wounds=1), first_round=True) == armed
    assert equipment_for_state(dagger, FighterState(wounds=1), first_round=True) == dagger


def test_transforming_casts_off_the_shield_but_never_a_skill():
    # "cast off all equipment": a shield's save and a shield's parry are
    # equipment and go with it, while a skill's own save or parry is not
    # equipment and stays.  The skill half of the aggregate is what survives.
    shielded = bare(off_hand_id="defence.shield", starting_skills=("skill.defensive-stance",))
    assert shielded.shield_and_skill_effects.armour_save_bonus == 1  # the shield
    assert shielded.shield_and_skill_effects.parry  # the skill
    stripped = equipment_for_state(shielded, FighterState(wounds=1, transformed=True), first_round=True)
    assert stripped.shield_and_skill_effects.armour_save_bonus == 0
    assert stripped.shield_and_skill_effects.parry
    # Negative control: with no such skill, the same cast-off leaves neither.
    plain = bare(off_hand_id="defence.shield")
    assert plain.shield_and_skill_effects.parry is False
    without = equipment_for_state(plain, FighterState(wounds=1, transformed=True), first_round=True)
    assert not without.shield_and_skill_effects.parry
    assert without.shield_and_skill_effects.armour_save_bonus == 0


def test_transformed_equipment_loss_is_never_recovered_by_the_reversion():
    mutant = bitten(weapon="weapon.sword")
    foe = bare()
    dice = KeyedDice({"round.0.first.bitten": 6, **misses(0, "first", 2), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, duel(mutant, foe), dice, choices)
    dice.finish(); choices.finish()
    assert result.state.first.transformed
    # Round 2 is the Bitten's own turn again; out of combat the printed result of
    # 1 reverts it.
    dice = KeyedDice({"round.2.first.bitten": 1,
                     "round.2.first.stupidity.0": 1, "round.2.first.stupidity.1": 1})
    choices = StrictDecisions([])
    reverted = resolve_round(mutant, foe,
        replace(result.state, round_index=2, engaged=False), dice, choices)
    dice.finish(); choices.finish()
    # Reverting is a result of 1, not an injury: the discarded sword is gone, so
    # the next phase fights with the compiled fist fallback, un-doubled.
    assert not reverted.state.first.transformed
    dice = KeyedDice({"round.4.first.bitten": 4, **misses(4, "first", 1), **misses(4, "second", 1)})
    choices = StrictDecisions([])
    after = resolve_round(mutant, foe,
        replace(reverted.state, round_index=4, engaged=True), dice, choices)
    dice.finish(); choices.finish()
    assert len(after.attacks) == 2 and not after.state.first.transformed


def test_a_transformed_bitten_suffers_no_penalty_for_fighting_unarmed():
    mutant = bitten(weapon="weapon.fist")
    # Toughness 3 makes the printed -1 to Strength the discriminator; two wounds
    # keep the struck opponent standing, so the phase is read whole.
    foe = bare(wounds=2)
    dice = KeyedDice({
        "round.0.first.bitten": 6,
        "round.0.first.attack.0.hit": 4,
        "round.0.first.attack.0.wound": 3,
        **misses(0, "first", 1, first=1),
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    result = resolve_round(mutant, foe, duel(mutant, foe), dice, choices)
    dice.finish(); choices.finish()
    assert sum(attack.wounded for attack in result.attacks) == 1
    assert result.state.second.condition == Condition.STANDING
    # Negative control: an untransformed Bitten keeps the printed penalty, so the
    # very same face of 3 does not wound the same opponent.
    dice = KeyedDice({
        "round.0.first.bitten": 4,
        "round.0.first.attack.0.hit": 4,
        "round.0.first.attack.0.wound": 3,
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    plain = resolve_round(mutant, foe, duel(mutant, foe), dice, choices)
    dice.finish(); choices.finish()
    assert sum(attack.wounded for attack in plain.attacks) == 0
