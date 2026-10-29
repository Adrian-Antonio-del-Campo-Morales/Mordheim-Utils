"""Charge consequences and alternative actions of the printed skill lists.

Every expectation is a printed line read live from ``sources/knowledge/bands``;
the band packages are the only source of recipients.  The three capabilities of
the block are:

* Animal Fury composes its two admitted consequences on one selection: the
  individual Fear immunity and the shared charge attack bonus, which
  ``build_attacks`` consumes on a charging turn only;
* the Netter clause of the four bands whose printed list carries it (Crooked
  Moon, Karak Azgal and Mordheimer Night Goblins, Ogre Hunting Party): the
  Night Goblin records declare the caught victim's canonical ``condition.netted`` for their
  printed recipients and keep the printed net throw, escape test and failed
  charge as an explicit NO producer, while the Ogre record is a supply clause
  that grants three Nets and no technique;
* the Ogre Hunting Party Bull Charge selection reaches the existing pool
  substitution instead of creating a second implementation: one +1 attack in
  place of the Ogre's normal pool, and a knock-down on the unparried hit.

The operators themselves are resolved by the engine suites
(``test_stateful_rules``, ``test_complex_sequences``); these cases prove the
selectable-rule connections, the recipients and the charge/no-charge split.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_combat.modular.contexts import _hit_reroll
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import DuelState, initialize_fighter
from mordheim_combat.phases import AttackPoolContext, Condition, build_attacks
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import available_special_rules
from mordheim_core.dice import AlwaysAccept, RollRequest
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_knowledge.loader import load_bands, load_items, runtime_bindings

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "sources" / "knowledge"

ANIMAL_FURY = "band--amazon-special-skills-animal-fury"
BERSERK_CHARGE = "band--norse-special-skills-berserk-charge"
NETTER = "band--night-goblin-special-skills-netter"
OGRE_NETTER = "band--ogre-hunting-skills-netter"
OGRE_BULL_CHARGE = "band--ogre-hunting-skills-bull-charge"


class ConstantDice:
    def __init__(self, value: int):
        self.value = value
        self.keys: list[str] = []

    def roll(self, request: RollRequest):
        self.keys.append(request.key)
        return min(self.value, request.sides)


class TapeDice:
    def __init__(self, *values: int):
        self.values = iter(values)

    def roll(self, request: RollRequest):
        value = next(self.values)
        assert 1 <= value <= request.sides
        return value


def build(band: str, profile: str, *rules: str, collection: str = "mordheim", **loadout) -> FighterBuild:
    return FighterBuild("mordheim", band_id=band, profile_id=profile,
                        collection=collection, special_rule_ids=rules, **loadout)


def compiled(band: str, profile: str, *rules: str, collection: str = "mordheim", **loadout):
    return compile_fighter(build(band, profile, *rules, collection=collection, **loadout), KNOWLEDGE)


def attacks_while(*, charging: bool) -> int:
    """The attack pool of one fighter on a charging and on an ordinary turn."""
    fighter = compiled("lustria-amazons", "amazon-priestess", ANIMAL_FURY, collection="trollheim")
    return build_attacks(AttackPoolContext(
        fighter=fighter, first_round=charging, charging=charging)).attacks


def test_animal_fury_composes_fear_immunity_with_the_charge_attack():
    fury = compiled("lustria-amazons", "amazon-priestess", ANIMAL_FURY, collection="trollheim")
    # One selection, both printed consequences: the psychology state and the
    # charge attack trait the attack builder reads.
    assert "mechanic.fear-immunity" in fury.global_effects.tags
    assert fury.global_effects.charge_attacks_bonus == 1
    # The printed +1 belongs to the turn she charges and to no other turn.
    assert attacks_while(charging=True) == attacks_while(charging=False) + 1


def test_animal_fury_stays_a_selectable_special_skill_of_its_printed_recipients():
    assert ANIMAL_FURY in available_special_rules(
        build("lustria-amazons", "amazon-priestess", collection="trollheim"), KNOWLEDGE)
    with pytest.raises(ValueError, match="not available"):
        compiled("lustria-amazons", "amazon-warriors", ANIMAL_FURY, collection="trollheim")


#: Printed recipients of each Netter clause: the Night Goblin skill-list
#: bands keep their printed list, and the hunting party names its two Gnoblar
#: heroes.
NETTER_RECORDS = (
    ("night-goblins-mic", "band--night-goblin-special-skills-netter", None),
    ("night-goblins-kaz", "band--night-goblin-special-skills-netter", None),
    ("crooked-moon-kep", "band--night-goblin-special-skills-netter", None),
    ("ogre-hunting-party-web", OGRE_NETTER, ("trappers", "sabre-baiter")),
)


def band_rule(band: str, rule_id: str) -> dict:
    package = next(row for row in load_bands("mordheim", KNOWLEDGE) if row.band["id"] == band)
    return next(rule for rule in package.special_rules if rule["id"] == rule_id)


@pytest.mark.parametrize(("band", "rule_id", "recipients"), NETTER_RECORDS)
def test_the_netter_clauses_reach_the_supplied_caught_victim_and_not_the_helper(band, rule_id, recipients):
    rule = band_rule(band, rule_id)
    runtime = rule["runtime"]
    # The procedure the clause prints is the excluded producer: the helper that
    # resolves a thrown net is not this rule's consumer and is not bound here.
    producer = next(effect for effect in runtime["effects"] if effect["scope"] == "NO")
    assert producer["binding"] is None and producer["reason"]
    # The helper that resolves a thrown net has no caller in the modular runtime,
    # so no clause binds it: the binding that claimed it is gone.
    bound = {binding["id"] for binding in runtime_bindings(rule, include_pending=True)}
    assert "mechanic.netter" not in bound
    # Recipients and provenance survive the correction.
    applies_to = rule["applies_to"]
    assert applies_to.get("band") is True or tuple(applies_to.get("profile_ids") or ()) == recipients
    assert rule["source"]["url"]


@pytest.mark.parametrize(("band", "profile"), (
    ("night-goblins-mic", "big-boss"),
    ("night-goblins-kaz", "big-boss"),
    ("crooked-moon-kep", "big-boss"),
    ("ogre-hunting-party-web", "trappers"),
))
def test_the_netter_clauses_declare_the_supplied_caught_victim_and_grant_no_technique(band, profile):
    rule_id = OGRE_NETTER if band == "ogre-hunting-party-web" else NETTER
    rule = band_rule(band, rule_id)
    runtime = rule["runtime"]
    bound = {binding["id"] for binding in runtime_bindings(rule, include_pending=True)}
    if band == "ogre-hunting-party-web":
        # Supply, not technique: three Nets are not the Night Goblin net charge.
        assert bound == set()
        assert "3 Nets" in rule["effect"]
        # Net supply grants no melee technique. The current duel constructor
        # rejects the inert inventory; that rejection alone is not the scope proof.
        piece = next(row for row in load_items("mordheim", KNOWLEDGE) if row.get("id") == "net")
        assert piece.get("combat_status") == "out_of_scope" and not piece.get("mechanic_id")
        with pytest.raises(ValueError, match="not on any equipment list"):
            compiled(band, profile, rule_id, owned_item_ids=("net", "net", "net"))
        # Veteran Tracker records Netter as the Trapper's required starting
        # choice without executing its excluded supply clause.
        fighter = compiled(band, profile, rule_id)
        assert "mechanic.netter" not in fighter.global_effects.tags
    else:
        # The admitted consequence is the caught victim itself, supplied to the
        # duel through the canonical condition the runtime already consumes.
        assert bound == {"condition.netted"}
        assert runtime["grant"] == "none"
    # Outside the Trapper's construction-only starting choice, the excluded
    # clauses remain unavailable to the duel.
    rejected_profile = "sabre-baiter" if band == "ogre-hunting-party-web" else profile
    with pytest.raises(ValueError, match="not selectable|outside the executable duel runtime"):
        compiled(band, rejected_profile, rule_id)
    if band == "ogre-hunting-party-web":
        assert rule_id in available_special_rules(
            FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
                         band_id=band, profile_id=profile), KNOWLEDGE)
    elif band == "night-goblins-mic":
        # This origin retains its printed warband-skill list for editorial
        # selection; the separate compile refusal above enforces duel scope.
        assert rule_id in available_special_rules(
            FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
                         band_id=band, profile_id=profile), KNOWLEDGE)
    else:
        assert rule_id not in available_special_rules(
            FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
                         band_id=band, profile_id=profile), KNOWLEDGE)


def test_the_supplied_caught_victim_consequence_is_configurable_and_consumed_by_the_duel():
    caught_fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
        condition_ids=("condition.netted",)), KNOWLEDGE)
    standing_fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7)))
    assert "condition.netted" in caught_fighter.global_effects.tags
    dice = ConstantDice(1)
    caught = initialize_fighter(caught_fighter, dice, "caught")
    # Caught in a net: counts as knocked down from the start of the duel.
    assert caught.netted and caught.condition == Condition.KNOCKED_DOWN
    # Hit automatically in combat while the same low roll misses a standing enemy.
    goblin = compiled("night-goblins-kaz", "big-boss")
    attacker = initialize_fighter(goblin, dice, "attacker")
    _, _, standing = _resolve_attack_pool(goblin, standing_fighter, attacker,
        initialize_fighter(standing_fighter, dice, "standing"), 1, TapeDice(1),
        key="caught.control", first_round=False, charging=False, decisions=AlwaysAccept())
    assert not standing[0].hit and standing[0].defender.condition == Condition.STANDING
    _, _, netted = _resolve_attack_pool(goblin, caught_fighter, attacker, caught, 1, TapeDice(1),
        key="caught.auto", first_round=False, charging=False, decisions=AlwaysAccept())
    assert netted[0].hit
    # In its own recovery it cuts free and strikes last as if it had stood up:
    # the round consumes the supplied state, and no throw or escape test is
    # produced anywhere here because the netter selected nothing.
    round_state = DuelState(caught, initialize_fighter(goblin, dice, "second"))
    after = resolve_round(caught_fighter, goblin, round_state, ConstantDice(1), AlwaysAccept()).state
    assert not after.first.netted and after.first.condition == Condition.STANDING


#: The two Norse bands print the shared charge clause on their own skill list.
BERSERK_RECIPIENTS = (
    ("norse-explorers-btb", "jarl"),
    ("norse-explorers-lustria", "jarl"),
)


@pytest.mark.parametrize(("band", "profile"), BERSERK_RECIPIENTS)
def test_berserk_charge_reaches_its_recipients_and_only_rerolls_a_charging_saxon_blow(band, profile):
    opponent = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7)))
    assert BERSERK_CHARGE in available_special_rules(build(band, profile), KNOWLEDGE)
    axe = compiled(band, profile, BERSERK_CHARGE, main_weapon_id="weapon.axe")
    assert "rule.berserk-charge" in axe.global_effects.tags
    # The printed reroll belongs to the turn he charges, and to the axe or
    # double handed weapon the printed clause names: neither half alone grants it.
    assert _hit_reroll(axe, opponent, axe.main_weapon, axe.global_effects, True, True)
    assert not _hit_reroll(axe, opponent, axe.main_weapon, axe.global_effects, True, False)
    sword = compiled(band, profile, BERSERK_CHARGE, main_weapon_id="weapon.sword")
    assert not _hit_reroll(sword, opponent, sword.main_weapon, sword.global_effects, True, True)


#: The three bands printing the shared clause on their own Dire Wolf profile.
DIRE_WOLF_ORIGINS = (
    ("undead", "dire-wolves", "mordheim"),
    ("trollheim-undead", "dire-wolves", "trollheim"),
    ("chaos-streets-undead-bloodlines", "dire-wolf", "trollheim"),
)


@pytest.mark.parametrize(("band", "profile", "collection"), DIRE_WOLF_ORIGINS)
def test_dire_wolf_charge_adds_its_printed_second_attack_only_when_charging(band, profile, collection):
    wolf = compiled(band, profile, collection=collection)
    assert wolf.global_effects.charge_attacks_bonus == 1
    assert build_attacks(AttackPoolContext(
        fighter=wolf, first_round=True, charging=True)).attacks == 2
    assert build_attacks(AttackPoolContext(
        fighter=wolf, first_round=False, charging=False)).attacks == 1


def test_ogre_bull_charge_reuses_the_pool_substitution_for_its_selection():
    attacker = compiled("ogre-hunting-party-web", "ogre-hunter", OGRE_BULL_CHARGE)
    target = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7)))
    assert "mechanic.bull-charge" in attacker.global_effects.tags
    dice = ConstantDice(1)
    defender, opponent = (initialize_fighter(fighter, dice, key)
                          for fighter, key in ((attacker, "attacker"), (target, "defender")))
    # A declared charging Bull Charge: the printed single +1 attack replaces the
    # Ogre's normal pool, so one outcome is recorded and no To Wound roll is made.
    _, final_defender, outcomes = _resolve_attack_pool(
        attacker, target, defender, opponent, 1, TapeDice(6),
        key="bull-charge", first_round=True, charging=True, decisions=AlwaysAccept())
    assert len(outcomes) == 1
    assert outcomes[0].hit and final_defender.condition == Condition.KNOCKED_DOWN


def test_bull_charge_carries_its_printed_to_hit_modifier_and_only_knocks_down_on_success():
    attacker = compiled("ogre-hunting-party-web", "ogre-hunter", OGRE_BULL_CHARGE)
    ordinary = compiled("ogre-hunting-party-web", "ogre-hunter")
    target = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7)))

    def charge(fighter, face: int):
        dice = ConstantDice(1)
        defender, opponent = (initialize_fighter(unit, dice, key)
                              for unit, key in ((fighter, "attacker"), (target, "defender")))
        return _resolve_attack_pool(fighter, target, defender, opponent, 1, TapeDice(face),
            key=f"bull-charge.{face}", first_round=True, charging=True,
            decisions=AlwaysAccept())

    # The printed +1 To Hit is what turns this charge's low roll into a hit: the
    # same warrior's ordinary charging pool misses it and knocks nobody down.
    _, plain_defender, plain = charge(ordinary, 2)
    assert not plain[0].hit and plain_defender.condition == Condition.STANDING
    _, hit_defender, hit = charge(attacker, 2)
    assert hit[0].hit and hit_defender.condition == Condition.KNOCKED_DOWN
    # Knock down is conditional on the attack landing, not a flat charge effect.
    _, missed_defender, missed = charge(attacker, 1)
    assert not missed[0].hit and missed_defender.condition == Condition.STANDING
