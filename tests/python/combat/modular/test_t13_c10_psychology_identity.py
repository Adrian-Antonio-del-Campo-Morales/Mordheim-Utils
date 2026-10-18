"""C10 psychology, Hatred and shared identity: living Scorpions, Gnoblars, Fear immunity.

Tomb Scorpions print "living creatures and are affected by Psychology normally"
in both warbands, so the compiled identity is living and never Undead; the
Dreamwalkers' printed Fear exemption reads exactly that Undead identity, so it
must stop covering the Scorpion.  Gnoblars print "count as 'Greenskins'", the
identity the canonical Hatred selects on.  Instinctual Violence prints a Fear
immunity next to a nominated strike-first attack: the exemption is bound only for
an Undead charger and only one nominated attack takes the Strike First tier.
"Free the Slaves!" names the opponent's own slaver identity as the hated group,
so the targeted Hatred replaces the unconditional one on both Pit Fighter bands.
The Fanatical auto-pass follows the supplied Knight-of-Purity promotion instead of
the whole Watch, and both grants need the supplied fact.
"""
from __future__ import annotations

import pytest

from dataclasses import replace

from mordheim_combat.modular.contexts import _combined_effect, _hit_reroll
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.leadership import undead_foes_fear_immunity
from collections import Counter

import mordheim_combat.modular.pools as pools
from mordheim_combat.modular.pools import pool_attack_weapons
from mordheim_combat.modular.psychology import fears_opponent_fire, resolve_fear
from mordheim_combat.modular.rounds import _strike_first_fighter, resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_knowledge.loader import knowledge_root

ROOT = knowledge_root()


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options), ROOT)


def rerolls(attacker, defender, *, first_round=True):
    return _hit_reroll(attacker, defender, attacker.main_weapon,
                       _combined_effect(attacker, attacker.main_weapon), first_round, False)


def morr_bearer():
    bearer = canonical("dreamwalkers-cult-of-morr-fbg", "priest-of-morr")
    assert "mechanic.undead-foes-no-fear" in bearer.global_effects.tags
    return bearer


# --- Tomb Scorpions: living, and therefore not Undead ----------------------

def test_tomb_scorpions_are_living_and_not_undead_in_both_printings():
    for band, collection in (("tomb-guardians", "mordheim"),
                            ("khemri-tomb-guardians", "trollheim")):
        scorpion = canonical(band, "tomb-scorpions", collection=collection)
        assert "nature.living" in scorpion.global_effects.tags, band
        assert "nature.undead" not in scorpion.global_effects.tags, band
        # "affected by Psychology normally": the identity grants no immunity.
        assert "mechanic.psychology-immunity" not in scorpion.global_effects.tags, band


def test_the_living_identity_stops_the_undead_foe_exemption_covering_scorpions():
    # The admitted consumer of the living/Undead classification: the
    # Dreamwalkers' Fear exemption names the opponent's Undead identity.
    bearer = morr_bearer()
    scorpion = canonical("tomb-guardians", "tomb-scorpions")
    assert undead_foes_fear_immunity(bearer, scorpion) is False
    # Positive control from the same printed identity.
    assert undead_foes_fear_immunity(bearer, canonical("undead", "zombies")) is True


def test_stone_golem_is_animated_and_carries_no_undead_identity():
    # Reconciliation: the printed "animated being and is not Undead" already
    # holds; nothing in the record claims a creature kind for the construct.
    golem = canonical("khemri-tomb-guardians", "stone-golem", collection="trollheim")
    assert "nature.undead" not in golem.global_effects.tags
    assert undead_foes_fear_immunity(morr_bearer(), golem) is False


# --- Gnoblars count as Greenskins -----------------------------------------

def test_gnoblars_count_as_greenskins_for_the_canonical_hatred():
    for profile in ("gnoblar-fighters", "flingers"):
        tags = canonical("ogre-hunting-party-web", profile).global_effects.tags
        assert "identity.greenskin" in tags, profile
        assert "species.goblin" not in tags, profile
    dwarf = canonical("dwarf-rangers", "dwarf-clansmen", "weapon.mace")
    assert "mechanic.hatred-orcs-goblins" in dwarf.global_effects.tags
    assert rerolls(dwarf, canonical("ogre-hunting-party-web", "gnoblar-fighters")) is True
    assert rerolls(dwarf, canonical("ogre-hunting-party-web", "flingers")) is True
    # Negative control: the band's own beasts are not Greenskins, and the
    # shared Hatred timing stays first-round only.
    assert rerolls(dwarf, canonical("ogre-hunting-party-web", "sabretusks")) is False
    assert rerolls(dwarf, canonical("ogre-hunting-party-web", "gnoblar-fighters"),
                   first_round=False) is False


# --- Instinctual Violence: the Fear half only ------------------------------

SKILL = "band--special-skill-instinctual-violence"


def graver(**options):
    return canonical("grave-robbers-sylv", "graver", "weapon.mace", **options)


# --- Instinctual Violence: both admitted halves ----------------------------

def test_the_selected_skill_grants_the_undead_charger_exemption_and_one_strike():
    selected = graver(special_rule_ids=(SKILL,))
    assert "mechanic.fear-immunity-undead-chargers" in selected.global_effects.tags
    assert "mechanic.nominated-strike-first" in selected.global_effects.tags
    assert "mechanic.psychology-immunity" not in selected.global_effects.tags
    # The nomination is one attack, never a pool-wide Strike First.
    assert selected.global_effects.priority == 0


def test_the_fear_exemption_needs_an_undead_charger():
    bearer = graver(special_rule_ids=(SKILL,))
    zombie = canonical("undead", "zombies")
    charged = initialize_duel(bearer, zombie, StrictDice([]),
        context=DuelContext(charging=("second",), active_participant="second"))
    # The Undead foe charged: no Fear test is rolled at all.
    dice, policy = StrictDice([]), StrictDecisions([])
    assert resolve_local_leadership(bearer, charged, dice, policy, "probe", first=True,
                                   fear=True, opponent=zombie) is True
    dice.finish(); policy.finish()
    # The bearer charges instead: the undead identity alone is not enough.
    own_charge = initialize_duel(bearer, zombie, StrictDice([]),
        context=DuelContext(charging=("first",), active_participant="first"))
    dice, policy = StrictDice([{"key": "probe.0", "value": 1}, {"key": "probe.1", "value": 1}]), StrictDecisions([])
    assert resolve_local_leadership(bearer, own_charge, dice, policy, "probe", first=True,
                                   fear=True, opponent=zombie) is True
    dice.finish()  # the Fear test was really taken
    # A living charger is not the printed predicate either.
    living = canonical("mercenaries", "warriors")
    dice, policy = StrictDice([{"key": "probe.0", "value": 1}, {"key": "probe.1", "value": 1}]), StrictDecisions([])
    assert resolve_local_leadership(bearer, charged, dice, policy, "probe", first=True,
                                   fear=True, opponent=living) is True
    dice.finish()


def synthetic(initiative=5, attacks=1, nominated=False, off_hand=None, wounds=1,
              main="weapon.mace"):
    unit = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, wounds, initiative, attacks),
        main_weapon_id=main, off_hand_id=off_hand))
    if nominated:
        unit = replace(unit, global_effects=replace(unit.global_effects,
            tags=(*unit.global_effects.tags, "mechanic.nominated-strike-first")))
    return unit


def miss(side, index=0):
    return {"key": f"round.0.{side}.attack.{index}.hit", "value": 1}


def scheduled(first, second, rolls, decisions=()):
    dice, policy = StrictDice(list(rolls)), StrictDecisions(list(decisions))
    state = initialize_duel(first, second, dice,
        context=DuelContext(charging=("second",), active_participant="second"))
    result = resolve_round(first, second, state, dice, policy)
    dice.finish(); policy.finish()
    return result


def test_only_the_nominated_attack_strikes_first():
    # Fixture: the foe's charge already takes the Strike First tier and a higher
    # Initiative would otherwise decide, so only the nomination can lift the
    # bearer's own attack ahead of it.
    bearer = synthetic(initiative=5, attacks=2, nominated=True)
    result = scheduled(bearer, synthetic(initiative=3), [
        {"key": "round.0.first.strike-first.attack.0.hit", "value": 1}, miss("second"), miss("first")],
        decisions=[{"key": "round.0.first.strike-first.attack.0", "value": True}])
    assert len(result.attacks) == 3
    # Declining every offer leaves the ordinary pool and its order untouched:
    # both ordinary attacks still resolve, none moved and none lost.
    declined = scheduled(bearer, synthetic(initiative=3),
        [miss("second"), miss("first", 0), miss("first", 1)],
        decisions=[{"key": "round.0.first.strike-first.attack.0", "value": False},
                   {"key": "round.0.first.strike-first.attack.1", "value": False}])
    assert len(declined.attacks) == 3
    # A bearer without the printed rule is never offered the nomination.
    ordinary = synthetic(initiative=5, attacks=2)
    result = scheduled(ordinary, synthetic(initiative=3), [miss("second"), miss("first", 0), miss("first", 1)])
    assert len(result.attacks) == 3


def test_declining_nomination_keeps_the_prepared_secondary_majority_once():
    bearer = synthetic(initiative=5, attacks=2, nominated=True, off_hand="weapon.dagger")
    result = scheduled(bearer, synthetic(initiative=3),
        [miss("second"), miss("first", 0), miss("first", 1), miss("first", 2)],
        decisions=[{"key": "round.0.first.main-weapon-majority", "value": False},
                   {"key": "round.0.first.strike-first.attack.0", "value": False},
                   {"key": "round.0.first.strike-first.attack.1", "value": False},
                   {"key": "round.0.first.strike-first.attack.2", "value": False}])
    assert len(result.attacks) == 4


def test_the_nominated_attack_leaves_the_ordinary_pool_without_duplicating_it():
    """The nominated slot leaves the pool; the remaining allocation is kept.

    Fixture: two hand weapons, so the pool allocates the mace twice and the
    dagger in its own last slot, and only the dagger raises the defender's
    armour save.  A nominated dagger must therefore leave the ordinary pool
    with the two mace attacks and no armour die of its own; an ordinary
    allocation that re-derived a shorter pool would resolve the dagger twice.
    """
    bearer = synthetic(initiative=5, attacks=2, nominated=True, off_hand="weapon.dagger")
    assert bearer.off_hand is not None and bearer.off_hand_attacks
    allocated = pool_attack_weapons(
        bearer, 3, first_round=True, charging=False,
        decisions=StrictDecisions([
            {"key": "round.0.first.main-weapon-majority", "value": True}]),
        key="round.0.first")
    assert allocated[0] == bearer.main_weapon and allocated[2] == bearer.off_hand
    dice, policy = StrictDice([
        {"key": "round.0.first.strike-first.attack.0.hit", "value": 1},
        {"key": "round.0.second.attack.0.hit", "value": 1},
        {"key": "round.0.first.attack.0.hit", "value": 5},
        {"key": "round.0.first.attack.1.hit", "value": 5},
        {"key": "round.0.first.attack.0.wound", "value": 4},
        {"key": "round.0.first.attack.1.wound", "value": 4},
    ]), StrictDecisions([
        # The pool's own weapon choice is answered first: the offers are made
        # over that allocation, so the nominated slot is a real pool weapon.
        {"key": "round.0.first.main-weapon-majority", "value": True},
        {"key": "round.0.first.strike-first.attack.0", "value": False},
        {"key": "round.0.first.strike-first.attack.1", "value": False},
        {"key": "round.0.first.strike-first.attack.2", "value": True},
    ])
    foe = synthetic(initiative=3, wounds=3)
    state = initialize_duel(bearer, foe, dice,
        context=DuelContext(charging=("second",), active_participant="second"))
    result = resolve_round(bearer, foe, state, dice, policy)
    dice.finish(); policy.finish()
    # Four attacks: the nominated dagger strike, both leftover maces and the
    # charging foe's own reply, so the pool neither duplicated nor lost one.
    assert len(result.attacks) == 4
    assert not [request.key for request in dice.requests if request.key.endswith(".armour")]


def test_the_nominated_strike_keeps_the_allocated_weapons_profile_and_slot():
    # The offers follow the pool's own allocation, so the nominated strike is one
    # of the bearer's real allocated attacks and keeps that weapon's provenance.
    bearer = synthetic(initiative=5, attacks=2, nominated=True, off_hand="weapon.dagger")
    assert bearer.off_hand_attacks and bearer.off_hand is not None
    allocated = pool_attack_weapons(bearer, 2, first_round=True, charging=False,
        decisions=StrictDecisions([]), key="round.0.first")
    assert len(allocated) == 2 and allocated[1] == bearer.off_hand
    strike = _strike_first_fighter(bearer, allocated[1])
    assert strike.main_weapon == bearer.off_hand
    assert strike.main_hand_slot == bearer.off_hand_slot
    assert strike.off_hand is None and strike.off_hand_attacks is False
    assert strike.extra_attacks == ()
    # A nominated main-hand attack keeps the main slot instead.
    main = _strike_first_fighter(bearer, allocated[0])
    assert main.main_weapon == bearer.main_weapon
    assert main.main_hand_slot == bearer.main_hand_slot


class FixedDice:
    """Every die comes up 1, so every attack misses and the pool resolves whole."""

    def roll(self, request):
        return 1


def weapon_tag(weapon):
    return next(tag for tag in weapon.tags if tag.startswith("weapon."))


def _allocation_versus_resolved(monkeypatch, unit, *, majority, nomination, charging, count):
    """The bearer's own resolved weapons beside the pool's own allocation."""
    seen: list[str] = []
    original = pools.resolve_reference_attack

    def spy(attacker, defender, attacker_state, defender_state, weapon, dice, **options):
        key = str(options.get("key") or "")
        if key.startswith("round.0.first") and (
                key.endswith(".strike-first") or key.split(".")[-2] == "attack"):
            seen.append(weapon_tag(weapon))
        return original(attacker, defender, attacker_state, defender_state,
                        weapon, dice, **options)

    monkeypatch.setattr(pools, "resolve_reference_attack", spy)
    policy = StrictDecisions(
        [{"key": "round.0.first.main-weapon-majority", "value": majority}]
        + [{"key": f"round.0.first.strike-first.attack.{index}", "value": index == nomination}
           for index in range(nomination + 1)])
    dice = FixedDice()
    foe = synthetic(initiative=1, attacks=1)
    state = initialize_duel(unit, foe, dice, context=DuelContext(
        charging=("first",) if charging else (), active_participant="first"))
    resolve_round(unit, foe, state, dice, policy)
    policy.finish()
    allocation = pool_attack_weapons(
        unit, count, first_round=True, charging=charging,
        decisions=StrictDecisions(
            [{"key": "round.0.first.main-weapon-majority", "value": majority}]),
        key="round.0.first")
    return Counter(seen), Counter(weapon_tag(weapon) for weapon in allocation)


def test_the_nominated_attack_and_the_remainder_share_the_pools_own_allocation(monkeypatch):
    """One allocation governs the choice, the named strike and the remainder.

    Both reported allocation defects: with two hand weapons the off-hand
    majority moves a dagger into the pool instead of a second mace, and a
    charging bearer's printed Whipcrack adds its own whip.  The bearer
    nominates one of his own attacks, so the Strike First strike and the
    ordinary pool that keeps resolving must be the same allocation: the
    nominated attack is the weapon the pool allocated for that position, and
    the resolved weapons are exactly the pool's own allocation.
    """
    cases = (
        # mace + dagger, the off hand carrying the majority: one mace and two
        # daggers, never two maces and one dagger.
        (synthetic(initiative=5, attacks=2, nominated=True, off_hand="weapon.dagger"),
         False, 1, False, 3, Counter({"weapon.dagger": 2, "weapon.mace": 1})),
        # A charging bearer whose printed Whipcrack adds a whip: two maces and
        # two whips, never three maces and one whip.
        (synthetic(initiative=5, attacks=2, nominated=True, off_hand="weapon.mace",
                   main="weapon.steel-whip"),
         False, 3, True, 4, Counter({"weapon.mace": 2, "weapon.steel-whip": 2})),
    )
    for unit, majority, nomination, charging, count, expected in cases:
        resolved, allocation = _allocation_versus_resolved(
            monkeypatch, unit, majority=majority, nomination=nomination,
            charging=charging, count=count)
        assert allocation == expected
        assert resolved == expected


# --- Fanatical: the promoted Knights of Purity only -------------------------

def watchman(profile="watch-captain", **options):
    return canonical("watchmen-mim", profile, **options)


def test_fanatical_auto_pass_follows_the_supplied_promotion_only():
    promoted = watchman(trait_overrides={"crusader_of_law": True})
    assert "mechanic.automatic-leadership" in promoted.global_effects.tags
    # The printed recipients are the promoted Knights of Purity, never the band
    # and never an unpromoted Watchman.
    assert "mechanic.automatic-leadership" not in watchman().global_effects.tags
    assert "mechanic.automatic-leadership" not in watchman("rookies").global_effects.tags
    # The supplied fact alone never reaches another warband.
    outsider = canonical("undead", "zombies", trait_overrides={"crusader_of_law": True})
    assert "mechanic.automatic-leadership" not in outsider.global_effects.tags
    # A promoted Knight really passes a required Leadership test without a roll.
    state = initialize_duel(promoted, canonical("undead", "zombies"), StrictDice([]),
        context=DuelContext(charging=("second",), active_participant="second"))
    dice, policy = StrictDice([]), StrictDecisions([])
    assert resolve_local_leadership(promoted, state, dice, policy, "probe", first=True,
                                   fear=False) is True
    dice.finish(); policy.finish()


# --- Fear of Fire: the rider that outlives the Psychology immunity ---------

BRANCHNYMPH = ("fen-guard-mim", "branchnymph")


def test_the_psychology_immune_bearer_still_takes_the_fear_of_fire_rider():
    """"Note that Fear of Fire still applies" limits the immunity it is printed next to."""
    nymph = canonical(*BRANCHNYMPH, "weapon.mace")
    assert "mechanic.psychology-immunity" in nymph.global_effects.tags
    assert "mechanic.fears-fire" in nymph.global_effects.tags
    assert "mechanic.causes-fear" in nymph.global_effects.tags
    # Ordinary fear: the immunity is honoured and no die is asked for at all.
    plain = canonical("kislevites", "trained-bear", "weapon.fist")
    assert "mechanic.causes-fear" in plain.global_effects.tags
    dice = StrictDice([])
    state = initialize_duel(nymph, plain, dice,
        context=DuelContext(charging=("first",), active_participant="first"))
    assert resolve_fear(nymph, plain, state, dice, StrictDecisions([])).failed_charges == frozenset()
    dice.finish()
    # The printed fire source: the supplied open flame the rider names makes the
    # immune duelist test Fear again, and a failed charge cancels the contact.
    burn = canonical("mercenaries", "warriors", trait_overrides={"lit_item": True})
    assert "condition.open-flame" in burn.global_effects.tags
    assert fears_opponent_fire(nymph, burn) is True
    dice = StrictDice([
        {"key": "round.0.first.fear.charge.0", "value": 6},
        {"key": "round.0.first.fear.charge.1", "value": 6},
    ])
    state = initialize_duel(nymph, burn, dice,
        context=DuelContext(charging=("first",), active_participant="first"))
    feared = resolve_fear(nymph, burn, state, dice, StrictDecisions([]))
    dice.finish()
    assert feared.failed_charges == frozenset({"first"})
    assert feared.engaged is False


# --- Free the Slaves!: the recipient's own slaver identity ------------------

PIT = ("chaos-streets-pit-fighters", "pit-fighters")
SLAVERS = "slavers-rel"
# The printed members of the Slaver warband that are slavers themselves; the
# same print's broken slaves, hired Ogre and hounds are not.
PRINTED_SLAVERS = ("slave-merchant", "overseer", "caravan-guards")
NOT_SLAVERS = ("eunuchs", "ogre-bodyguard")


def pit_fighter(**options):
    # The Trollheim printing carries the same rule_ref and prints no psychology
    # immunity on this profile, so the Hatred itself is observable here; the
    # Mordheim profiles print "immune to psychology", which suppresses any
    # psychology-based reroll for them and is not part of this clause.
    return canonical(*PIT, collection="trollheim", **options)


def slaver(profile="slave-merchant"):
    """A printed Slaver of the Slaver warband, compiled from its own facts.

    The chain is canonical configuration -> compile_fighter -> consumer: the
    identity is read from the source-backed ``combat_traits`` of the profile,
    so no band grant, slave-driving aura or campaign rule is guessed in place
    of the printed record.
    """
    return canonical(SLAVERS, profile)


def test_free_the_slaves_targets_the_opponents_own_slaver_identity():
    fighter = pit_fighter()
    assert "mechanic.hatred-slavers" in fighter.global_effects.tags
    # Reconciliation: the unconditional Hatred the record carried rerolled
    # against every opponent; the printed group is the slaver's own.
    assert "skill.hatred" not in fighter.global_effects.tags
    for profile in PRINTED_SLAVERS:
        opponent = slaver(profile)
        assert "identity.slaver" in opponent.global_effects.tags, profile
        assert rerolls(fighter, opponent) is True, profile
        assert rerolls(fighter, opponent, first_round=False) is False, profile
    for profile in NOT_SLAVERS:
        assert "identity.slaver" not in slaver(profile).global_effects.tags, profile
    # The printed slave-driving aura is not the producer: a fighter of another
    # warband that carries no slaver record is never hated for the Overseer's
    # rule, and the native identity does not leak outside the Slavers.
    plain = canonical("mercenaries", "warriors")
    assert "identity.slaver" not in plain.global_effects.tags
    assert rerolls(fighter, plain) is False
    # The explicit supplied fact stays available for an opponent whose slaver
    # status the source leaves to a caller-supplied record.
    supplied = canonical("mercenaries", "warriors", trait_overrides={"slaver": True})
    assert "identity.slaver" in supplied.global_effects.tags
    assert rerolls(fighter, supplied) is True
    # Ordinary Hatred timing and psychology, reused unchanged.
    effect = _combined_effect(fighter, fighter.main_weapon)
    assert _hit_reroll(fighter, slaver(), fighter.main_weapon, effect, True, False,
                       frenzy=True) is False


# --- Holy Relics: possession, not identity ---------------------------------

PILGRIM = ("bretonnian-chapel-guard", "battle-pilgrims")
RELIC = "holy_relic_pilgrim_only"


def pilgrim(**options):
    return compile_fighter(FighterBuild("mordheim", band_id=PILGRIM[0], profile_id=PILGRIM[1],
        main_weapon_id="weapon.mace", **options), ROOT)


def test_the_holy_relic_grants_frenzy_only_while_it_is_owned():
    owner = pilgrim(owned_item_ids=(RELIC,))
    assert owner.global_effects.frenzy is True
    assert "mechanic.holy-relic-frenzy" in owner.global_effects.tags
    # Possession-driven provenance: the grant belongs to the carried kit and
    # leaves with it, so it never becomes an identity fact of the profile.
    assert "mechanic.holy-relic-frenzy" not in owner.global_effects_without_equipment.tags
    assert "defence.holy-relic" not in owner.global_effects_without_equipment.tags
    bare = pilgrim()
    assert bare.global_effects.frenzy is False
    assert "mechanic.holy-relic-frenzy" not in bare.global_effects.tags
    # The relic's printed first-Leadership-test resource stays with the piece.
    assert "defence.holy-relic" in owner.global_effects.tags


def test_a_frenzied_relic_bearer_is_immune_to_his_own_hatred():
    owner = pilgrim(owned_item_ids=(RELIC,))
    foe = canonical("undead", "zombies")
    effect = _combined_effect(owner, owner.main_weapon)
    assert "skill.hatred" in owner.global_effects.tags
    assert _hit_reroll(owner, foe, owner.main_weapon, effect, True, False) is True
    # The printed parenthetical: while frenzied the Hatred reroll is suppressed.
    assert _hit_reroll(owner, foe, owner.main_weapon, effect, True, False, frenzy=True) is False


def test_knight_of_purity_autopass_requires_a_supplied_hero_promotion():
    knight = canonical('watchmen-mim', 'sergeants', 'weapon.mace',
                       trait_overrides={'crusader_of_law': True})
    state = initialize_duel(knight, knight, StrictDice([]),
                            context=DuelContext(charging=(), active_participant='first'))
    dice = StrictDice([])
    assert resolve_local_leadership(knight, state, dice, StrictDecisions([]),
                                    'knight', first=True, fear=False) is True
    dice.finish()
    ordinary = canonical('watchmen-mim', 'sergeants', 'weapon.mace')
    assert 'mechanic.automatic-leadership' not in ordinary.global_effects.tags
    with pytest.raises(ValueError, match='Hero of the Watch'):
        canonical('watchmen-mim', 'officers', 'weapon.mace',
                  trait_overrides={'crusader_of_law': True})
    promoted = canonical('watchmen-mim', 'officers', 'weapon.mace',
                         variant_ids=('promotion.hero',), trait_overrides={'crusader_of_law': True})
    assert 'mechanic.automatic-leadership' in promoted.global_effects.tags


# --- Vengeful Hatred: the target the serious injury determined ---------------
#
# Bitter Enmity (serious injury 56) prints four kinds of hated enemy: the
# individual who caused the injury (the enemy leader when a henchman caused it),
# that warband's leader, the whole warband, or every warband of its type.  The
# further D6 and the campaign are not simulated: the caller supplies the kind and
# the concrete identity.  Three kinds name an instance -- the warrior who caused
# the injury, that same warrior as its warband's leader, or the warband instance
# it belongs to -- and only the fourth, every warband of a type, is a category.
# Two warriors of one profile and two rosters built from one catalogue list
# therefore stay distinct.

def injured(kind, target):
    """A Bitter Enmity recipient whose campaign relationship is supplied."""
    return canonical("mercenaries", "warriors", trait_overrides={
        "enmity_kind": kind, "enmity_target": target})


def instance_of(band, profile, instance, warband_instance, *, collection="mordheim"):
    """One warrior of one roster: its own supplied instance keys, never a category."""
    fighter = canonical(band, profile, collection=collection, trait_overrides={
        "instance_id": instance, "warband_instance": warband_instance})
    assert f"instance.{instance}" in fighter.global_effects.tags
    assert f"warband-instance.{warband_instance}" in fighter.global_effects.tags
    return fighter


def test_vengeful_hatred_individual_selects_only_the_identified_warrior():
    """Two warriors of the same profile: only the identified one is hated."""
    bearer = injured("individual", "zombie-3")
    assert "mechanic.vengeful-hatred" in bearer.global_effects.tags
    assert "enmity-target.individual.zombie-3" in bearer.global_effects.tags
    named = instance_of("undead", "zombies", "zombie-3", "roster-a")
    # The catalogue profile is no longer an individual identity of its own.
    assert "individual.undead.zombies" not in named.global_effects.tags
    assert rerolls(bearer, named) is True
    # The same profile in the same warband is another warrior, so the profile
    # never stands in for the individual the injury determined.
    assert rerolls(bearer, instance_of("undead", "zombies", "zombie-4", "roster-a")) is False
    # A warrior supplied no instance identity carries no individual identity.
    assert rerolls(bearer, canonical("undead", "zombies")) is False
    # Ordinary Hatred timing, and an unsupplied relationship grants nothing.
    assert rerolls(bearer, named, first_round=False) is False
    plain = canonical("mercenaries", "warriors")
    assert "mechanic.vengeful-hatred" not in plain.global_effects.tags
    assert rerolls(plain, named) is False


def test_vengeful_hatred_warband_selects_only_the_identified_warband():
    """Two warbands of one type: the concrete branch matches only its own."""
    bearer = injured("warband", "roster-a")
    assert "enmity-target.warband.roster-a" in bearer.global_effects.tags
    assert rerolls(bearer, instance_of("undead", "zombies", "zombie-3", "roster-a")) is True
    # Another roster of the same catalogue list and the Trollheim printing of
    # that same type are other warbands, not the concrete one.
    same_type = instance_of("undead", "zombies", "zombie-4", "roster-b")
    twin = instance_of("trollheim-undead", "zombies", "zombie-4", "roster-b",
                       collection="trollheim")
    assert "warband-group.undead" in same_type.global_effects.tags
    assert "warband-group.undead" in twin.global_effects.tags
    assert rerolls(bearer, same_type) is False
    assert rerolls(bearer, twin) is False
    assert rerolls(bearer, canonical("mercenaries", "warriors")) is False


def test_vengeful_hatred_warband_type_covers_every_warband_of_that_type():
    """The only category branch: every warband of the type, whatever its roster."""
    bearer = injured("warband-type", "undead")
    assert "enmity-target.warband-type.undead" in bearer.global_effects.tags
    for band, collection in (("undead", "mordheim"), ("trollheim-undead", "trollheim")):
        for warband_instance in ("roster-a", "roster-b"):
            foe = instance_of(band, "zombies", "zombie-3", warband_instance,
                              collection=collection)
            assert "warband-group.undead" in foe.global_effects.tags, band
            assert rerolls(bearer, foe) is True, (band, warband_instance)
    # Negative recipient: the printed type is not every enemy, so a warband
    # outside it stays in ordinary combat.
    assert rerolls(bearer, canonical("night-goblins-web", "night-goblin-warriors")) is False


def test_vengeful_hatred_leader_is_the_identified_instance_that_holds_the_rule():
    """Leader names the determined individual, so the skill alone never grants."""
    bearer = injured("leader", "leader-1")
    assert "enmity-target.leader.leader-1" in bearer.global_effects.tags
    named = instance_of("undead", "vampire", "leader-1", "roster-a")
    assert "mechanic.leader-six" in named.global_effects.tags
    assert rerolls(bearer, named) is True
    # Another warrior of the same profile holding the same printed Leader rule is
    # a different individual, so its Leadership is not the determined leader.
    assert rerolls(bearer, instance_of("undead", "vampire", "leader-2", "roster-a")) is False
    # The relationship is permanent: losing the Leader rule does not change
    # the identity selected when the injury occurred or transfer it to a successor.
    former_leader = replace(named, global_effects=replace(
        named.global_effects, tags=tuple(tag for tag in named.global_effects.tags
                                        if not tag.startswith("mechanic.leader-"))))
    assert rerolls(bearer, former_leader) is True


def test_vengeful_hatred_refuses_a_half_supplied_or_empty_target():
    with pytest.raises(ValueError, match="target kind and its concrete identity together"):
        canonical("mercenaries", "warriors", trait_overrides={"enmity_kind": "warband"})
    with pytest.raises(ValueError, match="unknown Bitter Enmity target kind"):
        injured("tribe", "undead")
    with pytest.raises(ValueError, match="concrete identity the injury determined"):
        injured("individual", "  ")
    with pytest.raises(ValueError, match="one supplied identity key"):
        injured("warband", "roster-a roster-b")
    with pytest.raises(ValueError, match="non-empty supplied identity"):
        canonical("mercenaries", "warriors", trait_overrides={"instance_id": "  "})
