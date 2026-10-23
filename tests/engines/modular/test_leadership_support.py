"""Supplied Leadership providers and support facts.

The admitted individual consequences, read from the frozen compiled builds and
the real ``leadership``/``psychology`` consumers.  Every case supplies the
nearby participant explicitly as a
``LocalParticipant``: no third fighter, group count or table position is
simulated anywhere here.

* Dim-Witted (Adventurers of Karak Azgal): the Barbarian leader lends his
  effective 7 within six inches, because the shared six-inch borrow recognises
  him (``mechanic.leader-six`` next to ``mechanic.dim-witted-leader``);
* Dark Majesty (Chaos in the Streets): the Vampire's supplied Leader radius is
  twelve inches, not six;
* Mob (Battle Monks of Cathay): the caller supplies how many other allied
  Peasants are within three inches and each adds +1 Leadership, while the same
  printed sentence's no-leader-benefit half is the shared own-leadership
  condition;
* Songster (Dwarf Slayer Cult, Rememberer only): a supplied friendly model
  within six inches re-rolls one failed Leadership test at +1, capped at 10;
* Poetry (the three Araby Rel bands): the supplied "won the last battle" fact
  gives the Leader's own first Leadership test of the scenario +1, spent once;
* the conditional Rat Ogre Stupidity of the shared record: a supplied exempting
  hero skips the test entirely.

The operators are consumed by ``leadership.resolve_local_leadership`` and
``psychology.resolve_stupidity``; these cases prove the fact configured in
construction reaches them.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import resolve_stupidity
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, DuelContext, FighterBuild, LocalParticipant

DARK_MAJESTY = "band--von-carstein-power-dark-majesty"
MOB = "raging-peasants--mob"
SONGSTER = "band--rememberer-skills"


def canonical(compile_fighter, band, profile, weapon="weapon.fist", *,
              collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options))


def led(compile_fighter, band, profile, leadership, *, collection="mordheim", **options):
    """A band member whose supplied Leadership replaces the printed one."""
    return compile_fighter(FighterBuild("mordheim",
        Characteristics(3, 3, 3, 2, 3, 1, leadership=leadership), band_id=band,
        profile_id=profile, collection=collection, main_weapon_id="weapon.fist", **options))


def bare(compile_fighter, **options):
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour", **options))


def leadership_test(compile_fighter, recipient, providers, faces, decisions=None,
                    reroll_faces=()):
    """One Leadership test with the supplied same-side participants.

    ``providers`` is a tuple of ``(participant_id, fighter, inches)``; the
    opponent of the test is a generic fighter that is never borrowed from.
    ``faces`` feeds the first die pair and ``reroll_faces`` an accepted re-roll,
    which the engine asks for under its own ``{key}.reroll`` naming.
    """
    context = DuelContext(charging=("first",), active_participant="first",
        nearby=tuple(LocalParticipant(pid, "first", fighter) for pid, fighter, _ in providers),
        distances=tuple(("first", pid, inches) for pid, _, inches in providers))
    state = initialize_duel(recipient, bare(compile_fighter), StrictDice([]), context=context)
    rolls = [{"key": f"probe.{index}", "value": value} for index, value in enumerate(faces)]
    rolls += [{"key": f"probe.reroll.{index}", "value": value}
              for index, value in enumerate(reroll_faces)]
    dice, policy = StrictDice(rolls), StrictDecisions(decisions or [])
    passed = resolve_local_leadership(recipient, state, dice, policy, "probe", first=True)
    dice.finish()
    return passed


# --- Dim-Witted ------------------------------------------------------------

@pytest.mark.phase3_rules
def test_dim_witted_leader_lends_his_seven_within_six_inches(precompiled, compiled_builds):
    leader = precompiled().first
    assert {"mechanic.leader-six", "mechanic.dim-witted-leader"} <= set(leader.global_effects.tags)
    # The printed supply: this leader's effective 7 for members within six
    # inches.  A roll of seven fails on the member's own six and passes borrowed.
    member = led(compiled_builds.fighter, "adventurers-kaz", "dwarf", 6)
    borrowed = leadership_test(compiled_builds.fighter, member, (("barbarian", leader, 4),),
                               (3, 4), [{"key": "probe.leader.barbarian", "value": True}])
    assert borrowed is True
    # Negative control: beyond the printed six inches no leader value is offered
    # at all, so the tape stays empty and the own six fails.
    assert leadership_test(compiled_builds.fighter, member, (("barbarian", leader, 7),),
                           (3, 4)) is False


# --- Dark Majesty ----------------------------------------------------------

@pytest.mark.phase3_rules
def test_dark_majesty_widens_the_supplied_leader_radius_to_twelve(precompiled, compiled_builds):
    compiled = precompiled()
    vampire, plain = compiled.first, compiled.second
    assert {"mechanic.leader-six", "mechanic.leader-twelve"} <= set(vampire.global_effects.tags)
    member = led(compiled_builds.fighter, "chaos-streets-undead-bloodlines",
                 "von-carstein-vampire", 6, collection="trollheim")
    # Ten inches: the increased radius reaches, the ordinary one does not.
    widened = leadership_test(compiled_builds.fighter, member, (("vampire", vampire, 10),),
                              (3, 4), [{"key": "probe.leader.vampire", "value": True}])
    assert widened is True
    assert leadership_test(compiled_builds.fighter, member, (("vampire", plain, 10),),
                           (3, 4)) is False


# --- Mob -------------------------------------------------------------------

@pytest.mark.phase3_rules
def test_mob_adds_the_supplied_ally_count_and_denies_the_leader_rule(precompiled, compiled_builds):
    peasant = led(compiled_builds.fighter, "battle-monks-of-cathay", "raging-peasants", 5,
                  trait_overrides={"mob_allies": 2})
    assert {"mechanic.mob-leadership", "mechanic.own-leadership"} <= set(peasant.global_effects.tags)
    # Five plus the two supplied allies reaches seven.
    assert leadership_test(compiled_builds.fighter, peasant, (), (3, 4)) is True
    # Negative control: the same peasant without the supplied count fails on 5.
    unsupplied = led(compiled_builds.fighter, "battle-monks-of-cathay", "raging-peasants", 5)
    assert leadership_test(compiled_builds.fighter, unsupplied, (), (3, 4)) is False
    # The printed rage half: no leader value is offered even at four inches, so
    # the strict tape must not be asked for a leader decision.
    leader = precompiled().second
    assert leadership_test(compiled_builds.fighter, peasant, (("emissary", leader, 4),),
                           (3, 4)) is True


# --- Songster --------------------------------------------------------------

@pytest.mark.phase3_rules
def test_songster_rerolls_one_failed_leadership_test_at_plus_one(precompiled, compiled_builds):
    compiled = precompiled()
    bard, silent = compiled.first, compiled.second
    assert "mechanic.songster" in bard.global_effects.tags
    # A Rememberer who never took the skill sings for nobody.
    assert "mechanic.songster" not in silent.global_effects.tags
    member = led(compiled_builds.fighter, "dwarf-slayer-cult-web", "giant-slayer", 6)
    sixes = (6, 6)
    # Six fails the own test, and the printed +1 within six inches passes the
    # single re-roll the gift allows (three on the two re-rolled dice): one
    # Leadership die pair beyond the failed test, never a second test.
    assert leadership_test(compiled_builds.fighter, member, (("bard", bard, 4),), (6, 6),
                           [{"key": "probe.reroll", "value": True}],
                           reroll_faces=(3, 4)) is True
    # Negative control: outside six inches no support reaches and six fails.
    assert leadership_test(compiled_builds.fighter, member, (("bard", bard, 7),), sixes) is False
    # And the silent provider is not a provider at all.
    assert leadership_test(compiled_builds.fighter, member, (("bard", silent, 4),), sixes) is False


# --- Poetry ----------------------------------------------------------------

@pytest.mark.phase3_rules
def test_supplied_victorious_poetry_raises_the_leaders_first_test_once(precompiled, compiled_builds):
    # The Scholar produces the campaign qualification; it does not receive
    # the leader's supplied bonus automatically on its own profile.
    for band in ("ghutani-rel", "muzil-rel", "turjuk-rel"):
        scholar = canonical(compiled_builds.fighter, band, "scholar")
        assert "condition.poetry-victorious-leader" not in scholar.global_effects.tags
    poetry, bare_case = precompiled(0).first, precompiled(0).second
    leader = poetry
    assert "condition.poetry-victorious-leader" in leader.global_effects.tags
    state = initialize_duel(leader, bare_case, StrictDice([]),
                            context=DuelContext(charging=("first",), active_participant="first"))
    # Six and one is seven: it fails on the printed six and passes on the
    # supplied +1, which the printed clause allows once.
    dice, decisions = StrictDice([{"key": "poetry.0", "value": 6},
                                  {"key": "poetry.1", "value": 1}]), StrictDecisions([])
    passed, spent = resolve_local_leadership(leader, state, dice, decisions, "poetry",
                                             first=True, return_state=True)
    dice.finish()
    assert passed is True
    assert "poetry-first-leadership" in spent.resources_spent
    # The gift is spent: the same roll fails on the second test of the scenario.
    again = StrictDice([{"key": "second.0", "value": 6},
                        {"key": "second.1", "value": 1}])
    repeated, _ = resolve_local_leadership(leader, replace(state, first=spent), again,
                                           StrictDecisions([]), "second", first=True,
                                           return_state=True)
    again.finish()
    assert repeated is False
    # Negative control: without the supplied fact the printed six is all he has.
    plain, bare_again = precompiled(3).first, precompiled(3).second
    assert "condition.poetry-victorious-leader" not in plain.global_effects.tags
    state = initialize_duel(plain, bare_again, StrictDice([]),
                            context=DuelContext(charging=("first",), active_participant="first"))
    dice, decisions = StrictDice([{"key": "plain.0", "value": 6},
                                  {"key": "plain.1", "value": 1}]), StrictDecisions([])
    failed, _ = resolve_local_leadership(plain, state, dice, decisions, "plain", first=True,
                                        return_state=True)
    dice.finish()
    assert failed is False


# --- Shared conditional Stupidity ------------------------------------------

@pytest.mark.phase3_rules
def test_a_supplied_exempting_hero_skips_the_conditional_stupidity_test(precompiled):
    ogre, foe = precompiled(0).first, precompiled(0).second
    assert "mechanic.stupidity" in ogre.global_effects.tags
    assert "condition.stupidity-exempt" in ogre.global_effects.tags
    state = initialize_duel(ogre, foe, StrictDice([]),
                            context=DuelContext(charging=(), active_participant="first"))
    dice, decisions = StrictDice([]), StrictDecisions([])
    refreshed = resolve_stupidity(ogre, foe, state, dice, decisions)
    dice.finish()
    assert not refreshed.first.stupidity_failed
    # Negative control: without the supplied exemption the same warrior does
    # test, and a failed test leaves it marked as failed.
    plain, foe = precompiled(2).first, precompiled(2).second
    state = initialize_duel(plain, foe, StrictDice([]),
                            context=DuelContext(charging=(), active_participant="first"))
    failed = resolve_stupidity(plain, foe, state,
                               StrictDice([{"key": "round.0.first.stupidity.0", "value": 6},
                                           {"key": "round.0.first.stupidity.1", "value": 6}]),
                               StrictDecisions([]))
    assert failed.first.stupidity_failed
