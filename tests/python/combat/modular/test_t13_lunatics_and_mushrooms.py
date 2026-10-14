"""T13 M4g: the Lunatics recurring state and the Mushroom consumable states.

Source expectations retain the printed clock and named grants. Lunatics
cross-turn duration assertions preserve the recovered implementation pending
an explicit source/ruling decision; they do not certify accumulation semantics.

* Lustria Pygmies *Lunatics* rolls its own D6 at the start of EACH player turn:
  1-3 gains Frenzy and 4-6 gains Stupidity. The model's printed Immunity to
  Psychology does not cancel the grant its own profile prints.
* The Fungus Brew is a pre-battle producer: the caller supplies the affected
  duelist and the results its batch printed, one canonical condition per result.
  *Loony* supplies Frenzy and Stupidity together, which is the printed
  composition the warband's Mad Cap Masters rule qualifies: the Stupidity test is
  skipped while the Frenzy holds and applies again once it is lost.
* The Mad Cap Mushrooms print that they have no effect on Undead or the
  Possessed, while any other printed Frenzy the warrior carries still stands.
* *Numbed* prints +1 armour save "which may not be reduced below 6+": the floor
  bounds the ordinary arithmetic and is not the separate printed preservation
  against armour-ignoring attacks.

``KeyedDice`` is a strict, order-independent tape: an unlisted request and an
unused entry both fail, so a negative control proves that no die was asked for.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

LUNATICS = "mechanic.lunatics"
MUSHROOMS = ("preparation.mad-cap-mushrooms", "preparation.head-splitter-mushrooms")
BREW_CONDITIONS = (
    "condition.fungus-brew-dizzy", "condition.fungus-brew-fearless",
    "condition.fungus-brew-numbed", "condition.fungus-brew-belligerent",
    "condition.fungus-brew-loony",
)


class KeyedDice:
    """Every listed die is asked exactly once and no other die is asked."""

    def __init__(self, values: dict[str, int]):
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


def lunatic(weapon="weapon.mace", **options):
    return compile_fighter(FighterBuild("mordheim", band_id="lustria-pygmies",
        profile_id="wild-lunatics", collection="trollheim", main_weapon_id=weapon, **options))


def pygmy(profile="pygmies"):
    return compile_fighter(FighterBuild("mordheim", band_id="lustria-pygmies",
        profile_id=profile, collection="trollheim", main_weapon_id="weapon.mace"))


def bare(*, weapon="weapon.mace", wounds=2, strength=3, **options):
    """An unidentified opponent, so no band rule can be mistaken for the clause."""
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, strength, 3, wounds, 5, 1,
        leadership=7), main_weapon_id=weapon, armour_id="armour.no-armour", **options))


def supplied(conditions, **options):
    """An unidentified duelist carrying only the caller's supplied result."""
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 5, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour",
        condition_ids=tuple(conditions), **options))


def duel(first, second, *, charging="first"):
    return initialize_duel(first, second, KeyedDice({}), context=DuelContext(
        charging=(charging,), active_participant="first"))


def misses(round_index, owner, count, *, first=0):
    """Below every To Hit target in these fixtures, and no wound die follows."""
    return {f"round.{round_index}.{owner}.attack.{index}.hit": 1
            for index in range(first, first + count)}


# --- Lunatics: the printed recipient and its every-player-turn D6 -------------------

def test_the_lunatics_rule_reaches_its_printed_recipient_only():
    fighter = lunatic()
    assert LUNATICS in fighter.global_effects.tags
    # The same profile also prints Immunity to Psychology; the grant is this
    # profile's own printed consequence and is not cancelled by it.
    assert "mechanic.psychology-immunity" in fighter.global_effects.tags
    # Negative control: a sibling build of the same warband without the rule.
    assert LUNATICS not in pygmy().global_effects.tags


def test_a_roll_of_one_to_three_grants_frenzy_and_retains_recovered_duration():
    fighter, foe = lunatic(), bare()
    dice = KeyedDice({"round.0.first.lunatics": 2, **misses(0, "first", 2), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(fighter, foe, duel(fighter, foe), dice, choices)
    dice.finish(); choices.finish()
    # Frenzy doubles the printed one Attack, and the foe still strikes once.
    assert result.state.first.frenzy and result.state.first.lunatic_result == 2
    assert len(result.attacks) == 3
    # The source says EACH turn: the opponent's player turn also requires its
    # die, independently of the still-pending duration/accumulation ruling.
    dice = KeyedDice({"round.1.first.lunatics": 2, **misses(1, "first", 2), **misses(1, "second", 1)})
    choices = StrictDecisions([])
    second = resolve_round(fighter, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    assert "round.1.first.lunatics" in dice.requests
    assert second.state.first.frenzy and len(second.attacks) == 3


def test_a_roll_of_four_to_six_grants_the_printed_stupidity():
    fighter, foe = lunatic(), bare()
    # The opponent closes the charge, so the failure reads only as the printed
    # consequence and never as a charge that failed to be completed.
    dice = KeyedDice({
        "round.0.first.lunatics": 5,
        "round.0.first.stupidity.0": 6, "round.0.first.stupidity.1": 6,
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    result = resolve_round(fighter, foe, duel(fighter, foe, charging="second"), dice, choices)
    dice.finish(); choices.finish()
    # The failed test is the printed consequence: no attack that phase, while the
    # foe still strikes once, and the grant is carried on the state.
    assert result.state.first.stupidity_failed and result.state.first.lunatic_stupidity
    assert not result.state.first.frenzy
    assert len(result.attacks) == 1
    # Retained compatibility, pending duration ruling: the state survives the opponent's turn
    # and the next own turn asks for the test again.
    dice = KeyedDice({"round.1.first.lunatics": 5, **misses(1, "second", 1)})
    choices = StrictDecisions([])
    second = resolve_round(fighter, foe, result.state, dice, choices)
    dice.finish(); choices.finish()
    assert second.state.first.lunatic_stupidity
    dice = KeyedDice({
        "round.2.first.lunatics": 4,
        "round.2.first.stupidity.0": 6, "round.2.first.stupidity.1": 6,
        **misses(2, "second", 1),
    })
    choices = StrictDecisions([])
    third = resolve_round(fighter, foe, second.state, dice, choices)
    dice.finish(); choices.finish()
    assert third.state.first.stupidity_failed and len(third.attacks) == 1


def test_the_granted_frenzy_exempts_the_stupidity_and_its_loss_resumes_it():
    fighter, foe = lunatic(), bare()
    # The Frenzy the same printed rule granted holds: the model's own printed
    # Immunity to Psychology would pass the test anyway, so the tape's absence of
    # any Stupidity die proves the printed exemption is what skipped it.
    opening = duel(fighter, foe)
    holding = replace(opening, first=replace(opening.first, lunatic_stupidity=True, frenzy=True))
    dice = KeyedDice({"round.0.first.lunatics": 3, **misses(0, "first", 2), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(fighter, foe, holding, dice, choices)
    dice.finish(); choices.finish()
    assert "round.0.first.stupidity.0" not in dice.requests
    assert result.state.first.frenzy and not result.state.first.stupidity_failed
    # The printed damage reaction clears the Frenzy when the warrior is Knocked
    # Down or Stunned (attacks.resolve_wound_damage); the Stupidity applies again.
    lost = replace(result.state, first=replace(result.state.first, frenzy=False))
    dice = KeyedDice({
        "round.2.first.lunatics": 5,
        "round.2.first.stupidity.0": 6, "round.2.first.stupidity.1": 6,
        **misses(2, "second", 1),
    })
    choices = StrictDecisions([])
    resumed = resolve_round(fighter, foe, replace(lost, round_index=2), dice, choices)
    dice.finish(); choices.finish()
    assert resumed.state.first.stupidity_failed and len(resumed.attacks) == 1


# --- Fungus Brew: the supplied results are canonical conditions ------------

def test_every_printed_brew_result_is_supplied_through_its_condition():
    plain = supplied(())
    assert plain.characteristics.initiative == 5
    assert "mechanic.fear-immunity" not in plain.global_effects.tags
    assert plain.armour_save == 7 and plain.global_effects.armour_save_floor == 7
    assert "skill.hatred" not in plain.global_effects.tags
    assert not plain.global_effects.frenzy
    # "2 Dizzy = -1 Initiative" for the battle.
    assert supplied(("condition.fungus-brew-dizzy",)).characteristics.initiative == 4
    # "3 Fearless = immune to Fear" (the admitted individual half).
    fearless = supplied(("condition.fungus-brew-fearless",))
    assert "mechanic.fear-immunity" in fearless.global_effects.tags
    assert "mechanic.psychology-immunity" not in fearless.global_effects.tags
    # "4 Numbed = +1 armour save, which may not be reduced below 6+".
    numbed = supplied(("condition.fungus-brew-numbed",))
    assert numbed.armour_save == 6 and numbed.global_effects.armour_save_bonus == 1
    assert numbed.global_effects.armour_save_floor == 6
    # "5 Belligerent = Hatred against the opposing warband(s)".
    assert "skill.hatred" in supplied(("condition.fungus-brew-belligerent",)).global_effects.tags
    # "6 Loony = Frenzy, followed by Stupidity if Frenzy is lost".
    loony = supplied(("condition.fungus-brew-loony",))
    assert loony.global_effects.frenzy and "mechanic.stupidity" in loony.global_effects.tags
    # A batch of distinct results supplies each of them at once.
    batch = supplied(("condition.fungus-brew-dizzy", "condition.fungus-brew-fearless",
                      "condition.fungus-brew-numbed"))
    assert batch.characteristics.initiative == 4 and batch.armour_save == 6
    assert "mechanic.fear-immunity" in batch.global_effects.tags


def test_the_brew_table_is_a_supplied_state_and_not_an_unadmitted_condition():
    # The supply table admits only canonical conditions whose own runtime binds an
    # operator, so a general rule text cannot be handed in as a supplied result.
    with pytest.raises(ValueError, match="outside the executable duel runtime"):
        supplied(("condition.fear",))


def test_the_belligerent_brew_rerolls_a_first_round_miss_like_hatred():
    drinker, foe = supplied(("condition.fungus-brew-belligerent",)), bare()
    dice = KeyedDice({
        "round.0.first.attack.0.hit": 1,
        "round.0.first.attack.0.hit.reroll": 1,   # only the printed Hatred asks for it
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    result = resolve_round(drinker, foe, duel(drinker, foe), dice, choices)
    dice.finish(); choices.finish()
    assert "round.0.first.attack.0.hit.reroll" in dice.requests
    assert not result.attacks[0].hit and result.state.second.wounds == 2


def test_the_loony_stupidity_is_ignored_while_its_frenzy_holds():
    drinker, foe = supplied(("condition.fungus-brew-loony",)), bare()
    dice = KeyedDice({**misses(0, "first", 2), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(drinker, foe, duel(drinker, foe), dice, choices)
    dice.finish(); choices.finish()
    # Frenzy and Stupidity are supplied together; while the Frenzy holds no
    # Stupidity die is asked for and the doubled pool strikes.
    assert result.state.first.frenzy and not result.state.first.stupidity_failed
    assert len(result.attacks) == 3
    # Once the printed damage reaction clears the Frenzy, the Stupidity applies
    # normally again - the same printed composition as Mad Cap Masters.
    opening = duel(drinker, foe, charging="second")
    fallen = replace(opening, first=replace(opening.first, frenzy=False))
    dice = KeyedDice({
        "round.0.first.stupidity.0": 6, "round.0.first.stupidity.1": 6,
        **misses(0, "second", 1),
    })
    choices = StrictDecisions([])
    resumed = resolve_round(drinker, foe, fallen, dice, choices)
    dice.finish(); choices.finish()
    assert resumed.state.first.stupidity_failed and len(resumed.attacks) == 1


# --- Rowdy: the supplied result widens the own-turn animosity band --------

def goblin(**options):
    """A Night Goblin carrying its warband's own printed squabble rule."""
    return compile_fighter(FighterBuild("mordheim", band_id="crooked-moon-kep",
        profile_id="night-goblins", main_weapon_id="weapon.mace", **options))


def test_the_rowdy_result_widens_the_own_turn_animosity_band_to_one_or_two():
    squabbler, foe = goblin(), bare()
    # The ordinary printed contract fails on a 1 only.
    assert "mechanic.goblin-squabble" in squabbler.global_effects.tags
    assert "mechanic.fungus-rowdy" not in squabbler.global_effects.tags
    dice = KeyedDice({"round.0.first.animosity": 2,
                      **misses(0, "first", 1), **misses(0, "second", 1)})
    choices = StrictDecisions([])
    result = resolve_round(squabbler, foe, duel(squabbler, foe), dice, choices)
    dice.finish(); choices.finish()
    assert not result.state.first.animosity_failed and len(result.attacks) == 2
    # The supplied printed Rowdy result widens that same band to 1-2, so the same
    # 2 now suppresses the bearer's own attacks for the turn, and only its own:
    # the opponent's pool is untouched and no bearer attack die is asked for.
    rowdy = goblin(condition_ids=("condition.fungus-brew-rowdy",))
    assert "mechanic.fungus-rowdy" in rowdy.global_effects.tags
    dice = KeyedDice({"round.0.first.animosity": 2, **misses(0, "second", 1)})
    choices = StrictDecisions([])
    suppressed = resolve_round(rowdy, foe, duel(rowdy, foe), dice, choices)
    dice.finish(); choices.finish()
    assert suppressed.state.first.animosity_failed
    assert "round.0.first.attack.0.hit" not in dice.requests
    assert len(suppressed.attacks) == 1
    # A 1 suppresses under both contracts, and a 3 under neither.
    for roll, widened in ((1, False), (1, True), (3, True)):
        fighter = rowdy if widened else squabbler
        bearer_strikes = {} if roll == 1 else misses(0, "first", 1)
        dice = KeyedDice({"round.0.first.animosity": roll,
                          **bearer_strikes, **misses(0, "second", 1)})
        choices = StrictDecisions([])
        outcome = resolve_round(fighter, foe, duel(fighter, foe), dice, choices)
        dice.finish(); choices.finish()
        assert outcome.state.first.animosity_failed == (roll == 1), (roll, widened)


# --- Numbed: the +1 save and its printed 6+ limit --------------------------

def test_the_numbed_floor_bounds_the_arithmetic_but_never_an_armour_ignoring_attack():
    numbed = supplied(("condition.fungus-brew-numbed",))
    # A Strength 6 blow would take an unarmoured save past 6+; the printed limit
    # keeps it at 6+, so a six still saves.
    target = phases.armour_target(phases.ArmourContext(
        armour_save=numbed.armour_save, strength=6,
        armour_save_floor=numbed.global_effects.armour_save_floor))
    assert target == 6
    # Negative control: the same blow against the same duelist without the brew
    # leaves no save at all.
    plain = supplied(())
    assert phases.armour_target(phases.ArmourContext(
        armour_save=plain.armour_save, strength=6,
        armour_save_floor=plain.global_effects.armour_save_floor)) == 7
    # The limit is not the printed preservation against armour-ignoring attacks,
    # which stays the separate armour_cannot_be_ignored contract: such an attack
    # negates this save as it negates any other.
    assert phases.armour_target(phases.ArmourContext(
        armour_save=numbed.armour_save, strength=6, ignore_armour=True,
        armour_save_floor=numbed.global_effects.armour_save_floor)) == 7


def test_the_numbed_save_holds_a_normal_blow_that_an_unprepared_bearer_takes():
    numbed, foe = supplied(("condition.fungus-brew-numbed",)), bare()
    dice = KeyedDice({
        "round.0.first.attack.0.hit": 4,
        "round.0.first.attack.0.wound": 4,
        "round.0.first.attack.0.armour": 6,
        "round.0.second.attack.0.hit": 1,
    })
    choices = StrictDecisions([])
    result = resolve_round(foe, numbed, duel(foe, numbed), dice, choices)
    dice.finish(); choices.finish()
    assert result.attacks[0].saved and result.state.second.wounds == 2
    # The unprepared bearer of the same profile takes the same blow with no save
    # die at all.
    plain = supplied(())
    dice = KeyedDice({
        "round.0.first.attack.0.hit": 4,
        "round.0.first.attack.0.wound": 4,
        "round.0.second.attack.0.hit": 1,
    })
    choices = StrictDecisions([])
    plain_result = resolve_round(foe, plain, duel(foe, plain), dice, choices)
    dice.finish(); choices.finish()
    assert "round.0.first.attack.0.armour" not in dice.requests
    assert not plain_result.attacks[0].saved and plain_result.state.second.wounds == 1


# --- The Mad Cap Mushrooms' printed exclusion -----------------------------

def test_the_mushrooms_have_no_effect_on_undead_or_the_possessed():
    # "The Mad Cap Mushroom has no effect on Undead such as Vampires and Zombies,
    # or the Possessed": the printed sentence belongs to that item's own text.
    living = bare(preparation_ids=MUSHROOMS)
    assert living.global_effects.frenzy
    for nature in ("undead", "possessed"):
        excluded = bare(preparation_ids=("preparation.mad-cap-mushrooms",),
                        trait_overrides={"creature_kind": nature})
        assert "undead_or_possessed" in excluded.global_effects.tags, nature
        assert not excluded.global_effects.frenzy, nature
        # The Head-Splitter Mushrooms print "Frenzy; also allows the use of a Ball
        # and Chain" and no exclusion, so their grant is not narrowed by the other
        # item's sentence.
        splitter = bare(preparation_ids=("preparation.head-splitter-mushrooms",),
                        trait_overrides={"creature_kind": nature})
        assert splitter.global_effects.frenzy, nature
    # Only the excluded item's own contribution is void: another printed Frenzy
    # the warrior carries still stands.
    other = bare(preparation_ids=("preparation.mad-cap-mushrooms",),
                 trait_overrides={"creature_kind": "undead"},
                 condition_ids=("campaign.condition.frenzy",))
    assert other.global_effects.frenzy
