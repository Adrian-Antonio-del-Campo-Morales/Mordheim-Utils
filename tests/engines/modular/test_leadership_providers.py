"""The printed Leadership providers, their radii and their conditions.

Each of the six M4f band rules is exercised through the frozen compiled route and
the shared ``leadership.resolve_local_leadership`` consumer: the printed
recipient, the supplied provider of the clause, the printed radius, the printed
equipment or state condition and one observable consequence of the lending, the
re-roll or the automatic pass.  Strict tapes make "no die and no choice were
requested" observable, so a negative control proves the provider was never
offered rather than merely that the test failed.
"""
from __future__ import annotations

import sys

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, DuelContext, FighterBuild, LocalParticipant
import pytest


pytestmark = pytest.mark.phase3_rules

INSPIRING_PRESENCE = "band--special-skill-inspiring-presence"

# The frozen-build loader is the only compilation route in this module: the
# fixture below replaces this name with ``load_builds(...).fighter``, so every
# preparation keeps its complete FighterBuild, its participants, its negative
# controls and its post-compile options while nothing compiles here.
compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)

def canonical(band, profile, weapon="weapon.fist", **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, main_weapon_id=weapon, **options))


def bare(leadership=7):
    """A generic opponent, so the supplied band facts stay the tested side's."""
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=leadership),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))


def probe(recipient, providers, distances, rolls, choices=(), key="probe", **options):
    """One Leadership test with the caller's supplied local facts."""
    context = DuelContext(charging=(), active_participant="first",
                          nearby=tuple(providers), distances=tuple(distances))
    state = initialize_duel(recipient, bare(), StrictDice([]), context=context)
    dice = StrictDice([{"key": name, "value": value} for name, value in rolls])
    decisions = StrictDecisions([{"key": name, "value": value} for name, value in choices])
    passed = resolve_local_leadership(recipient, state, dice, decisions, key, first=True, **options)
    dice.finish()
    decisions.finish()
    return passed


# --- Dreamwalkers: Inspiring Presence (12 inches for the Dreamer) -----------

def test_inspiring_presence_widens_the_dreamer_who_took_it():
    worshipper = canonical("dreamwalkers-cult-of-morr-fbg", "morr-worshwishpers")  # Ld 7
    inspiring = canonical("dreamwalkers-cult-of-morr-fbg", "dreamer",
                          special_rule_ids=(INSPIRING_PRESENCE,))
    plain = canonical("dreamwalkers-cult-of-morr-fbg", "dreamer")
    assert "mechanic.leader-six" in inspiring.global_effects.tags
    assert "mechanic.leader-twelve" in inspiring.global_effects.tags
    assert "mechanic.leader-twelve" not in plain.global_effects.tags
    # Activation: at twelve inches the Worshipper tests on the Dreamer's Ld 8.
    assert probe(worshipper, [LocalParticipant("dreamer", "first", inspiring)],
                 [("first", "dreamer", 12)], [("probe.0", 4), ("probe.1", 4)],
                 [("probe.leader.dreamer", True)]) is True
    # Negative control: without the skill the ordinary Leader is six-inch only, so
    # at twelve inches nothing is offered and the same 8 fails on the own 7.
    assert probe(worshipper, [LocalParticipant("dreamer", "first", plain)],
                 [("first", "dreamer", 12)], [("probe.0", 4), ("probe.1", 4)]) is False
    # The printed skill widens the Leader rule rather than replacing it.
    assert probe(worshipper, [LocalParticipant("dreamer", "first", plain)],
                 [("first", "dreamer", 6)], [("probe.0", 4), ("probe.1", 4)],
                 [("probe.leader.dreamer", True)]) is True


# --- Skryre and Slavers: Slave Driver (3 inches, 6 with a scourge) ----------

def test_slave_driver_lends_at_three_inches_and_at_six_with_a_scourge():
    slave = canonical("skaven-of-clan-skryre-rel", "skaven-slaves")        # Ld 2
    overseer = canonical("skaven-of-clan-skryre-rel", "overseer")          # Ld 6
    scourged = canonical("skaven-of-clan-skryre-rel", "overseer",
                         trait_overrides={"scourge_armed": True})
    assert "mechanic.slave-driver" in overseer.global_effects.tags
    assert "condition.scourge-armed" in scourged.global_effects.tags
    # Activation: inside three inches the slave tests on the Overseer's Ld 6.
    assert probe(slave, [LocalParticipant("overseer", "first", overseer)],
                 [("first", "overseer", 3)], [("probe.0", 3), ("probe.1", 3)],
                 [("probe.leader.overseer", True)]) is True
    # The printed range gate: one inch further, nothing is offered at all.
    assert probe(slave, [LocalParticipant("overseer", "first", overseer)],
                 [("first", "overseer", 4)], [("probe.0", 3), ("probe.1", 3)]) is False
    # Equipment condition: the scourge widens the same clause to six inches.
    assert probe(slave, [LocalParticipant("overseer", "first", scourged)],
                 [("first", "overseer", 6)], [("probe.0", 3), ("probe.1", 3)],
                 [("probe.leader.overseer", True)]) is True
    assert probe(slave, [LocalParticipant("overseer", "first", scourged)],
                 [("first", "overseer", 7)], [("probe.0", 3), ("probe.1", 3)]) is False
    # Provider validity: the clause names his own slaves, and the same-band
    # requirement keeps a foreign warband's leader out.
    assert probe(slave, [LocalParticipant("overseer", "second", overseer)],
                 [("first", "overseer", 3)], [("probe.0", 3), ("probe.1", 3)]) is False
    foreign = canonical("house-guard-sc", "commander")                     # Ld 8
    assert probe(slave, [LocalParticipant("boss", "first", foreign)],
                 [("first", "boss", 3)], [("probe.0", 3), ("probe.1", 3)]) is False
    # The printed recipient is a slave, not every warrior in the Overseer's band.
    verminkin = canonical("skaven-of-clan-skryre-rel", "verminkin")
    assert probe(verminkin, [LocalParticipant("overseer", "first", overseer)],
                 [("first", "overseer", 3)], [("probe.0", 3), ("probe.1", 3)]) is False


def test_slavers_overseer_lends_to_an_explicitly_supplied_slave():
    slave = compile_fighter(FighterBuild('mordheim',
        Characteristics(3, 3, 3, 2, 3, 1, leadership=2), main_weapon_id='weapon.mace',
        trait_overrides={'slave': True}))
    overseer = canonical('slavers-rel', 'overseer')
    assert probe(slave, [LocalParticipant('overseer', 'first', overseer)],
        [('first', 'overseer', 3)], [('probe.0', 3), ('probe.1', 3)],
        [('probe.leader.overseer', True)]) is True
    assert probe(slave, [LocalParticipant('overseer', 'second', overseer)],
        [('first', 'overseer', 3)], [('probe.0', 3), ('probe.1', 3)]) is False


# --- House Guard: Relay Orders (the leader's Leadership through the Adjutant)

def test_relay_orders_lends_the_leaders_leadership_through_the_adjutant():
    guard = canonical("house-guard-sc", "guards")            # Ld 7
    adjutant = canonical("house-guard-sc", "adjutant")       # Ld 6
    commander = canonical("house-guard-sc", "commander")     # Ld 8
    assert "mechanic.relay-orders" in adjutant.global_effects.tags
    nearby = [LocalParticipant("adjutant", "first", adjutant),
              LocalParticipant("commander", "first", commander)]
    # Activation: an 8 passes only on the relayed Ld 8 -- never on the
    # recipient's own 7 nor on the Adjutant's own 6 -- and the choice is offered
    # at the Adjutant's participant id, the relay anchor.
    assert probe(guard, nearby,
                 [("first", "adjutant", 4), ("adjutant", "commander", 5), ("first", "commander", 9)],
                 [("probe.0", 4), ("probe.1", 4)],
                 [("probe.leader.adjutant", True)]) is True
    # The printed prerequisite: no leader the Adjutant can use means no relay,
    # and the Adjutant never lends his own Leadership.
    assert probe(guard, [LocalParticipant("adjutant", "first", adjutant)],
                 [("first", "adjutant", 4)], [("probe.0", 4), ("probe.1", 4)]) is False
    # The relayed leader must be within the Adjutant's own borrow range.
    assert probe(guard, nearby,
                 [("first", "adjutant", 4), ("adjutant", "commander", 7), ("first", "commander", 9)],
                 [("probe.0", 4), ("probe.1", 4)]) is False
    # The Adjutant's own relay range stays the printed six inches.
    assert probe(guard, nearby,
                 [("first", "adjutant", 7), ("adjutant", "commander", 5), ("first", "commander", 9)],
                 [("probe.0", 4), ("probe.1", 4)]) is False


# --- Sea Ghosts: Songster (re-roll with +1 to Leadership) -------------------

def test_songster_rerolls_a_failed_test_with_one_more_leadership():
    lookout = canonical("sea-ghosts-mim", "lookouts")        # Ld 7
    minstrel = canonical("sea-ghosts-mim", "minstrels")      # Ld 8
    assert "mechanic.songster" in minstrel.global_effects.tags
    # Activation: the double six fails on the own 7, and the re-roll is made with
    # +1 Leadership, so the 8 passes on the printed modifier alone.
    assert probe(lookout, [LocalParticipant("minstrel", "first", minstrel)],
                 [("first", "minstrel", 6)],
                 [("probe.0", 6), ("probe.1", 6), ("probe.reroll.0", 4), ("probe.reroll.1", 4)],
                 [("probe.reroll", True)]) is True
    # The printed six inches: beyond them no re-roll is offered.
    assert probe(lookout, [LocalParticipant("minstrel", "first", minstrel)],
                 [("first", "minstrel", 7)], [("probe.0", 6), ("probe.1", 6)]) is False
    # Friendly side only.
    assert probe(lookout, [LocalParticipant("minstrel", "second", minstrel)],
                 [("first", "minstrel", 6)], [("probe.0", 6), ("probe.1", 6)]) is False
    # The clause qualifies the *recipient* ("any friendly model within 6 inches
    # of the warrior"), not the Minstrel: a recipient forbidden to borrow a
    # leader's value still receives the re-roll, and a Knocked Down Minstrel
    # still sings, while one out of action cannot.
    assert probe(lookout, [LocalParticipant("minstrel", "first", minstrel)],
                 [("first", "minstrel", 6)],
                 [("probe.0", 6), ("probe.1", 6), ("probe.reroll.0", 4), ("probe.reroll.1", 4)],
                 [("probe.reroll", True)], own_value_only=True) is True
    down = LocalParticipant("minstrel", "first", minstrel, "knocked-down")
    assert probe(lookout, [down], [("first", "minstrel", 6)],
                 [("probe.0", 6), ("probe.1", 6), ("probe.reroll.0", 4), ("probe.reroll.1", 4)],
                 [("probe.reroll", True)]) is True
    out = LocalParticipant("minstrel", "first", minstrel, "out")
    assert probe(lookout, [out], [("first", "minstrel", 6)],
                 [("probe.0", 6), ("probe.1", 6)]) is False


def test_songster_covers_any_friendly_recipient_without_a_same_band_requirement(precompiled):
    compiled = precompiled()
    recipient, minstrel = compiled.first, compiled.second
    assert probe(recipient, [LocalParticipant('minstrel', 'first', minstrel)],
        [('first', 'minstrel', 6)],
        [('probe.0', 6), ('probe.1', 6), ('probe.reroll.0', 4), ('probe.reroll.1', 4)],
        [('probe.reroll', True)]) is True


# --- Protectorate of Sigmar: Devoted (re-roll within 12 of the Priest) ------

def test_devoted_rerolls_while_the_warrior_priest_is_supplied():
    hound = canonical("protectorate-of-sigmar-lotd3", "hound")               # Ld 6
    priest = canonical("protectorate-of-sigmar-lotd3", "warrior-priest")     # Ld 8
    assert "mechanic.devoted" in hound.global_effects.tags
    reroll = [("probe.0", 6), ("probe.1", 6), ("probe.reroll.0", 3), ("probe.reroll.1", 3)]
    # Activation: the double six fails and the re-roll passes on the own 6.
    assert probe(hound, [LocalParticipant("priest", "first", priest)],
                 [("first", "priest", 12)], reroll, [("probe.reroll", True)]) is True
    # Beyond the printed twelve inches the clause does not apply.
    assert probe(hound, [LocalParticipant("priest", "first", priest)],
                 [("first", "priest", 13)], [("probe.0", 6), ("probe.1", 6)]) is False
    # A Warrior Priest who is only Knocked Down still grants it: unlike the Leader
    # borrow, the clause does not require the named model to stand.
    down = LocalParticipant("priest", "first", priest, "knocked-down")
    assert probe(hound, [down], [("first", "priest", 12)], reroll,
                 [("probe.reroll", True)]) is True
    # Out of action he cannot, and the test simply fails.
    gone = LocalParticipant("priest", "first", priest, "out")
    assert probe(hound, [gone], [("first", "priest", 12)],
                 [("probe.0", 6), ("probe.1", 6)]) is False


# --- Slavers: Broken Spirit (automatic pass while the Merchant stands) ------

def test_broken_spirit_passes_automatically_while_the_slave_merchant_stands():
    eunuch = canonical("slavers-rel", "eunuchs")              # Ld 10
    merchant = canonical("slavers-rel", "slave-merchant")     # Ld 8
    assert "mechanic.broken-spirit" in eunuch.global_effects.tags
    # Activation: the double six fails on the own 10, yet the test passes and the
    # tape holds no roll and no choice at all.
    assert probe(eunuch, [LocalParticipant("merchant", "first", merchant)],
                 [("first", "merchant", 20)], []) is True
    # The printed condition: once the Slave Merchant is out of action the
    # automatic pass ends and the same 12 fails.
    out = LocalParticipant("merchant", "first", merchant, "out")
    assert probe(eunuch, [out], [("first", "merchant", 20)],
                 [("probe.0", 6), ("probe.1", 6)]) is False
    # No supplied Slave Merchant, no condition to read.
    assert probe(eunuch, [], [], [("probe.0", 6), ("probe.1", 6)]) is False
