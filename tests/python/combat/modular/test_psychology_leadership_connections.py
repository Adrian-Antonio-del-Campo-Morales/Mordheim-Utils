"""The canonical Psychology/Leadership connections.

Each newly bound band rule is proved the way the plan asks a *connection* to be
proved: the canonical compiler reaches the shared operator for the printed
recipient, an unselected or non-recipient build stays without it, and one real
phase consequence is exercised where the operator's own suite does not already
have one.  Behaviour of the shared operators is deliberately not re-tested.
"""
from __future__ import annotations

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
import pytest


def canonical(band, profile, *, collection="mordheim", rules=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", special_rule_ids=tuple(rules), **options))


def bare(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour", **options))


# --- Fear and its immunity --------------------------------------------------

@pytest.mark.phase2_construction
def test_causes_fear_reaches_the_compiler():
    troll = canonical("chaos-streets-greenskins", "troll", collection="trollheim")
    assert "mechanic.causes-fear" in troll.global_effects.tags
    zombie = canonical("trollheim-undead", "zombies", collection="trollheim")
    assert "mechanic.causes-fear" in zombie.global_effects.tags
    # Negative control: a sibling build of the same band without the rule.
    orc = canonical("chaos-streets-greenskins", "orc-boyz", collection="trollheim")
    assert "mechanic.causes-fear" not in orc.global_effects.tags


@pytest.mark.phase3_rules
def test_causes_fear_charges_the_opponent_for_a_die():
    troll = canonical("chaos-streets-greenskins", "troll", collection="trollheim")
    plain = bare()
    assert causes_fear(troll, plain)
    dice = StrictDice([{"key": "round.0.first.fear.charge.0", "value": 6},
                       {"key": "round.0.first.fear.charge.1", "value": 6}])
    state = initialize_duel(plain, troll, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(plain, troll, state, dice, StrictDecisions([]))
    dice.finish()
    assert not result.engaged and result.failed_charges == frozenset({"first"})


@pytest.mark.phase2_construction
def test_psychology_immunity_and_fear_immunity_are_distinct_recipients():
    golem = canonical("khemri-tomb-guardians", "stone-golem", collection="trollheim")
    assert "mechanic.psychology-immunity" in golem.global_effects.tags
    zombie = canonical("chaos-streets-undead-bloodlines", "zombie", collection="trollheim")
    assert "mechanic.psychology-immunity" in zombie.global_effects.tags
    blackheart = canonical("hochland-bandits", "blackhearts")
    assert "mechanic.fear-immunity" in blackheart.global_effects.tags
    # The immunity is the fear-only one, not the whole Psychology immunity.
    assert "mechanic.psychology-immunity" not in blackheart.global_effects.tags
    # Negative control: a living sibling of the same band.
    scorpion = canonical("khemri-tomb-guardians", "tomb-scorpions", collection="trollheim")
    assert "mechanic.psychology-immunity" not in scorpion.global_effects.tags


@pytest.mark.phase3_rules
def test_fear_immunity_waives_the_fear_die_for_its_recipient():
    golem = canonical("khemri-tomb-guardians", "stone-golem", collection="trollheim")
    attacker = bare(trait_overrides={"causes_fear": True})
    dice = StrictDice([])
    state = initialize_duel(golem, attacker, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(golem, attacker, state, dice, StrictDecisions([]))
    dice.finish()
    assert result.engaged and not result.failed_charges


@pytest.mark.phase2_construction
def test_selectable_fear_immunity_needs_its_selection():
    skill = "band--pit-fighter-skill-grizzled-veteran"
    selected = canonical("pit-fighters", "pit-king", rules=(skill,))
    assert "mechanic.psychology-immunity" in selected.global_effects.tags
    unselected = canonical("pit-fighters", "pit-king")
    assert "mechanic.psychology-immunity" not in unselected.global_effects.tags


# --- Stupidity, Frenzy, automatic and handler Leadership --------------------

@pytest.mark.phase2_construction
def test_stupidity_and_frenzy_land_on_their_profiles():
    troll = canonical("chaos-streets-greenskins", "troll", collection="trollheim")
    assert "mechanic.stupidity" in troll.global_effects.tags
    goblin = canonical("forest-goblins-lus", "red-toof-clan-goblins")
    assert goblin.global_effects.frenzy
    assert not canonical("forest-goblins-lus", "forest-goblins").global_effects.frenzy


@pytest.mark.phase3_rules
def test_automatic_leadership_auto_passes_a_required_test():
    ruffian = canonical("ostlanders", "ruffians")
    assert "mechanic.automatic-leadership" in ruffian.global_effects.tags
    dice = StrictDice([])
    state = initialize_duel(ruffian, bare(), StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(
        ruffian, state, dice, StrictDecisions([]), "probe", first=True,
        psychology=True, fear=True)
    dice.finish()
    assert passed
    assert "mechanic.automatic-leadership" not in canonical("ostlanders", "jaeger").global_effects.tags


@pytest.mark.phase2_construction
def test_handler_leadership_and_cold_blooded_reach_their_bands():
    monkey = canonical("lustrian-reavers", "barbary-monkey")
    assert "mechanic.handler-leadership" in monkey.global_effects.tags
    saurus = canonical("lustria-lizardmen", "saurus-braves", collection="trollheim")
    assert "mechanic.cold-blooded-psychology" in saurus.global_effects.tags
    # Negative control: another band's animal handler has no Cold Blooded.
    assert "mechanic.cold-blooded-psychology" not in monkey.global_effects.tags


# --- Hatred, the Undead composite and the Leader radius ---------------------

@pytest.mark.phase2_construction
def test_hatred_and_isolationists_reach_their_bands():
    slayer = canonical("pit-fighters", "dwarf-troll-slayer")
    assert "mechanic.hatred-orcs-goblins" in slayer.global_effects.tags
    amazon = canonical("lustria-amazons", "amazon-warriors", collection="trollheim")
    assert "mechanic.amazon-isolationists" in amazon.global_effects.tags


@pytest.mark.phase2_construction
def test_undead_composite_and_its_living_negative_control():
    skeletons = canonical("khemri-lahmian-brotherhood", "skeleton-warriors",
                          collection="trollheim")
    assert "nature.undead" in skeletons.global_effects.tags
    assert "mechanic.causes-fear" in skeletons.global_effects.tags
    assert "mechanic.psychology-immunity" in skeletons.global_effects.tags
    # The living members of the same band are not Undead, which is exactly why
    # the band-wide aggregate stays out of scope.
    jackals = canonical("khemri-lahmian-brotherhood", "jackals", collection="trollheim")
    assert "nature.undead" not in jackals.global_effects.tags
    assert "mechanic.causes-fear" not in jackals.global_effects.tags


@pytest.mark.phase2_construction
def test_leader_range_skills_widen_only_their_selected_bearer():
    power = "band--von-carstein-power-dark-majesty"
    assert "mechanic.leader-twelve" in canonical(
        "chaos-streets-undead-bloodlines", "von-carstein-vampire",
        collection="trollheim", rules=(power,)).global_effects.tags
    assert "mechanic.leader-twelve" not in canonical(
        "chaos-streets-undead-bloodlines", "von-carstein-vampire",
        collection="trollheim").global_effects.tags
