"""T13.2c automatic profile/band grants: canonical loading -> compiled fighter.

Every rule in this matrix carries ``runtime.grant`` ``profile`` or ``band``, so
the canonical band package applies it without an explicit ``special_rule_ids``
selection.  Each expectation is derived from the canonical rule text, its
binding parameters and the KB execution contract
(``sources/knowledge/catalog/mechanics/execution.yaml``) - never from the
compiler output under test.

What a passing assertion proves is the *construction* connection: which
observable property the compiled fighter receives and for which recipients.
It does not prove combat execution; hit/wound/injury d6 resolution belongs to
the combat-engine lots (T13.3-T13.6).  A tag-only observable is labelled as
such.  Rules whose route is loaded but has no reachable compiled example
(parameter vocabulary without a consumer, named skills that are not mechanics,
source-value mismatches, open T13-Q questions) are recorded in the T13.2c
trace register instead of being asserted here as if they worked.

Partition source: ``docs/knowledge/2a2b/tasks/T13-automatic-grants.csv``.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild

COLLECTION = "mordheim"


def compile_band(band_id: str, profile_id: str, *, collection: str = COLLECTION, **kwargs):
    return compile_fighter(
        FighterBuild(
            "mordheim",
            band_id=band_id,
            profile_id=profile_id,
            collection=collection,
            **kwargs,
        )
    )


# ---------------------------------------------------------------------------
# poison immunity: trait.poison-immune -> global_effects.poison_immunity
# ---------------------------------------------------------------------------
POISON_RECIPIENTS = (
    *(("blood-dragons-mou", profile, profile + "--immune-to-poisons")
      for profile in ("vampire", "wights", "skeleton-warriors", "grave-guards", "hell-hounds")),
    ("fallen-the-rel", "revenant", "revenant--immune-to-poison"),
    # "The Cairn Wraith is immune to poison." and the six sibling rules of
    # call-of-the-night-haint-mim (one profile rule per recipient profile).
    ("call-of-the-night-haint-mim", "cairn-wraith", "cairn-wraith--immune-to-poison"),
    ("call-of-the-night-haint-mim", "malignant-spirits", "malignant-spirits--immune-to-poison"),
    ("call-of-the-night-haint-mim", "mourngul", "mourngul--immune-to-poison"),
    ("call-of-the-night-haint-mim", "poltergeists", "poltergeists--immune-to-poison"),
    ("call-of-the-night-haint-mim", "revenants", "revenants--immune-to-poison"),
    ("call-of-the-night-haint-mim", "spirit-hosts", "spirit-hosts--immune-to-poison"),
    ("call-of-the-night-haint-mim", "tomb-banshee", "tomb-banshee--immune-to-poison"),
    # "All Fen Guard are immune to Drugs and Poison, but still affected by
    # Disease." (band-wide, so another profile proves the same route).
    ("fen-guard-mim", "branchwych", "band--immune-to-drugs-and-poison"),
    ("fen-guard-mim", "treekin", "band--immune-to-drugs-and-poison"),
    # "Flesh Constructs are immune to poisons." / Thrall / Zombies.
    ("masters-of-horror-sylv", "flesh-construct", "flesh-construct--immune-to-poison"),
    ("masters-of-horror-sylv", "thrall", "thrall--immune-to-poison"),
    ("masters-of-horror-sylv", "zombies", "zombies--immune-to-poison"),
    # Necrarchs of the Soul Stealers: abomination, vampire, skeletons, thrall,
    # zombie (each profile rule named "Immune to Poison").
    ("necrarchs-the-soul-stealers-lotd1", "abomination", "abomination--immune-to-poison"),
    ("necrarchs-the-soul-stealers-lotd1", "necrarch-vampire", "necrarch-vampire--immune-to-poison"),
    ("necrarchs-the-soul-stealers-lotd1", "skeletal-warrior", "skeletal-warrior--immune-to-poison"),
    ("necrarchs-the-soul-stealers-lotd1", "thrall", "thrall--immune-to-poison"),
    ("necrarchs-the-soul-stealers-lotd1", "zombie", "zombie--immune-to-poison"),
    # Strigoi: "Skeletons are not affected by any drug or poison." / Fell Bats.
    ("strigoi-kaz", "fell-bats", "fell-bats--immune-to-poison"),
    ("strigoi-kaz", "skeletons", "skeletons--immune-to-poison"),
    # "Vampires are not affected by any poison."
    ("survivors-of-strigos-sylv", "strigoi-vampire", "strigoi-vampire--immune-to-poison"),
    # "this warrior is not affected by poison attacks" (Disgusting).
    ("underworld-alliance-mim", "goblin-stinky-gits", "goblin-stinky-gits--disgusting"),
    ("watchmen-mim", "turnkeys", "turnkeys--immune-to-poison"),
)

POISON_NON_RECIPIENTS = (
    ("blood-dragons-mou", "dreg"),
    ("fallen-the-rel", "butcher"),
    # One valid profile per bad whose automatic rules grant no poison immunity.
    ("call-of-the-night-haint-mim", "corpse-master"),
    ("masters-of-horror-sylv", "mad-scientist"),
    ("necrarchs-the-soul-stealers-lotd1", "acolyte"),
    ("necrarchs-the-soul-stealers-lotd1", "waif"),
    ("strigoi-kaz", "vampire"),
    ("survivors-of-strigos-sylv", "seer"),
    ("underworld-alliance-mim", "goblin-bully"),
    ("watchmen-mim", "watch-captain"),
)


@pytest.mark.parametrize(("band_id", "profile_id", "rule_id"), POISON_RECIPIENTS)
def test_poison_immunity_rule_reaches_each_named_recipient(band_id, profile_id, rule_id):
    compiled = compile_band(band_id, profile_id)
    assert compiled.global_effects.poison_immunity is True, rule_id


@pytest.mark.parametrize(("band_id", "profile_id"), POISON_NON_RECIPIENTS)
def test_poison_immunity_stays_absent_from_valid_non_recipients(band_id, profile_id):
    compiled = compile_band(band_id, profile_id)
    assert compiled.global_effects.poison_immunity is False


# ---------------------------------------------------------------------------
# natural armour save: trait.natural-armour-save / compiler scaly skin
# ---------------------------------------------------------------------------
NATURAL_ARMOUR_RECIPIENTS = (
    # "Fen Guard have a 6+ armour save which can be stacked with regular
    # armour" (band-wide 6+).
    ("fen-guard-mim", "branchwych", "band--bark-skin", 6),
    # "A Treekin's Bark save is increased to 4+." - the profile grant replaces
    # the band-wide 6+, it does not add to it (exactly 4, never 10).
    ("fen-guard-mim", "treekin", "treekin--redwood", 4),
    # "The Halfling always has a basic saving throw of 6 ... on top of any
    # armour": one profile rule covering four named recipients.
    ("halflings-mic", "halfling-elder", "halfling-elder--layers-of-fat", 6),
    ("halflings-mic", "halfling-cook", "halfling-elder--layers-of-fat", 6),
    ("halflings-mic", "halfling-thief", "halfling-elder--layers-of-fat", 6),
    ("halflings-mic", "halfling-youths", "halfling-elder--layers-of-fat", 6),
    # Talismanic Tattoos is a special save, corrected under F022/L07.
    # "All Lizardmen ... Saurus 5+, Skinks 6+" (band-wide compiler contract).
    ("lizardmen-lus", "skink-priest", "band--scaly-skin", 6),
    ("lizardmen-lus", "skink-braves", "band--scaly-skin", 6),
    ("lizardmen-lus", "saurus-totem-warriors", "band--scaly-skin", 5),
    ("lizardmen-lus", "saurus-braves", "band--scaly-skin", 5),
    # "Kroxigor have a natural save of 4+." - the profile trait and the
    # band-wide compiler contract must agree on exactly one 4+.
    ("lizardmen-lus", "kroxigor", "kroxigor--scaly-skin", 4),
    # "Fimir have a 6+ armour save" (non-dwarf source of the shared contract).
    ("lords-of-the-marsh-mim", "young-nobles", "band--scaly-skin", 6),
)

# The Fen Guard band rule applies to the whole band, so its only valid
# non-recipient control is a profile outside the band; the Halfling and Sea
# Ghost grants do name their recipients within the band.
NATURAL_ARMOUR_EXCLUDED_PROFILES = (
    ("halflings-mic", "halfling-scouts"),
    ("halflings-mic", "village-ogre"),
    ("sea-ghosts-mim", "wayfinder"),
)


@pytest.mark.parametrize(
    ("band_id", "profile_id", "rule_id", "expected_save"), NATURAL_ARMOUR_RECIPIENTS
)
def test_natural_armour_grant_project_the_source_value_once(
    band_id, profile_id, rule_id, expected_save
):
    compiled = compile_band(band_id, profile_id)
    assert compiled.natural_armour_save == expected_save, rule_id


@pytest.mark.parametrize(("band_id", "profile_id"), NATURAL_ARMOUR_EXCLUDED_PROFILES)
def test_natural_armour_grant_stays_absent_from_named_non_recipients(band_id, profile_id):
    compiled = compile_band(band_id, profile_id)
    assert compiled.natural_armour_save == 7


def test_redwood_replaces_bark_skin_instead_of_stacking_with_it():
    treekin = compile_band("fen-guard-mim", "treekin")
    sibling = compile_band("fen-guard-mim", "branchwych")
    assert treekin.natural_armour_save == 4
    assert sibling.natural_armour_save == 6
    # 4 + 6 or 4 + 4 would mean the band and profile grants both applied.
    assert treekin.natural_armour_save not in {10, 8}


# ---------------------------------------------------------------------------
# frenzy: trait.frenzy -> global_effects.frenzy
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("band_id", "profile_id"),
    (
        # "Witch Elves ... follow the Frenzy special rule."
        ("druchii-mic", "witch-elves"),
        # "Savage Orc Nuttaz are subject to the rules for frenzy."
        ("savage-orcs-kaz", "nuttaz"),
    ),
)
def test_frenzy_grant_reaches_its_recipients(band_id, profile_id):
    assert compile_band(band_id, profile_id).global_effects.frenzy is True


@pytest.mark.parametrize(
    ("band_id", "profile_id"),
    (("druchii-mic", "noble"), ("savage-orcs-kaz", "boss")),
)
def test_frenzy_stays_absent_from_non_recipients(band_id, profile_id):
    assert compile_band(band_id, profile_id).global_effects.frenzy is False


# ---------------------------------------------------------------------------
# no pain: mechanic skill.ignore-pain -> tag-only compiled observable
# ---------------------------------------------------------------------------
NO_PAIN_RECIPIENTS = (
    *(("call-of-the-night-haint-mim", profile, profile + "--no-pain")
      for profile in ("cairn-wraith", "tomb-banshee", "malignant-spirits", "revenants",
                      "spirit-hosts", "poltergeists", "mourngul")),
    *(("masters-of-horror-sylv", profile, profile + "--no-pain")
      for profile in ("thrall", "zombies", "flesh-construct")),
    ("survivors-of-strigos-sylv", "strigoi-vampire", "strigoi-vampire--no-pain"),
    *(("blood-dragons-mou", profile, profile + "--no-pain")
      for profile in ("vampire", "wights", "skeleton-warriors", "grave-guards", "hell-hounds")),
    # "No Pain" profiles; the compiled connection is the skill.ignore-pain tag.
    ("fallen-the-rel", "revenant", "revenant--no-pain"),
    ("necrarchs-the-soul-stealers-lotd1", "abomination", "abomination--no-pain"),
    ("necrarchs-the-soul-stealers-lotd1", "necrarch-vampire", "necrarch-vampire--no-pain"),
    ("necrarchs-the-soul-stealers-lotd1", "skeletal-warrior", "skeletal-warrior--no-pain"),
    ("necrarchs-the-soul-stealers-lotd1", "thrall", "thrall--no-pain"),
    ("necrarchs-the-soul-stealers-lotd1", "zombie", "zombie--no-pain"),
    ("strigoi-kaz", "fell-bats", "fell-bats--no-pain"),
    ("strigoi-kaz", "skeletons", "skeletons--no-pain"),
)


@pytest.mark.parametrize(("band_id", "profile_id", "rule_id"), NO_PAIN_RECIPIENTS)
def test_no_pain_tag_reaches_each_named_recipient(band_id, profile_id, rule_id):
    # Tag-only proof: the compiled fighter carries the skill connection; the
    # injury-table conversion is engine behaviour outside this matrix.
    compiled = compile_band(band_id, profile_id)
    assert "skill.ignore-pain" in compiled.global_effects.tags, rule_id


@pytest.mark.parametrize(
    ("band_id", "profile_id"),
    (("fallen-the-rel", "butcher"), ("necrarchs-the-soul-stealers-lotd1", "acolyte")),
)
def test_no_pain_tag_stays_absent_from_non_recipients(band_id, profile_id):
    assert "skill.ignore-pain" not in compile_band(band_id, profile_id).global_effects.tags


# ---------------------------------------------------------------------------
# regeneration: mechanic skill.regeneration -> save, fire block and tag
# ---------------------------------------------------------------------------
def test_warpstone_troll_regeneration_projects_the_printed_four_plus():
    # "roll a D6; on a result of 4 or more the wound is ignored ... may not
    # regenerate wounds caused by fire" -> 4+, blocked by fire.
    compiled = compile_band("underworld-alliance-mim", "warpstone-troll")
    assert compiled.global_effects.regeneration_save == 4
    assert compiled.global_effects.regeneration_blocked_by_fire is True
    assert "skill.regeneration" in compiled.global_effects.tags


def test_regeneration_absence_in_a_valid_control():
    control = compile_band("underworld-alliance-mim", "goblin-bully")
    assert control.global_effects.regeneration_save == 7
    assert "skill.regeneration" not in control.global_effects.tags


# ---------------------------------------------------------------------------
# hard to kill: mechanic skill.hard-to-kill -> threshold 6 and tag
# ---------------------------------------------------------------------------
HARD_TO_KILL_RECIPIENTS = (
    # "See Mordheim rulebook page 151" (Hard to Kill): out of action only on a
    # 6, so the compiled threshold is 6 and the skill tag is present.
    ("adventurers-kaz", "dwarf", "dwarf--hard-to-kill"),
    ("clan-angrund-kep", "dwarf-noble", "band--hard-to-kill"),
    ("clan-angrund-kep", "dwarf-troll-slayers", "band--hard-to-kill"),
    ("clockworkers-sc", "dwarf-engineer", "dwarf-engineer--hard-to-kill"),
)


@pytest.mark.parametrize(("band_id", "profile_id", "rule_id"), HARD_TO_KILL_RECIPIENTS)
def test_hard_to_kill_threshold_reaches_each_recipient(band_id, profile_id, rule_id):
    compiled = compile_band(band_id, profile_id)
    assert compiled.global_effects.out_of_action_threshold == 6, rule_id
    assert "skill.hard-to-kill" in compiled.global_effects.tags, rule_id


@pytest.mark.parametrize(
    ("band_id", "profile_id"),
    (("adventurers-kaz", "wizard"), ("clockworkers-sc", "master-of-clocks")),
)
def test_hard_to_kill_threshold_stays_absent_from_non_recipients(band_id, profile_id):
    compiled = compile_band(band_id, profile_id)
    assert compiled.global_effects.out_of_action_threshold == 5
    assert "skill.hard-to-kill" not in compiled.global_effects.tags


# ---------------------------------------------------------------------------
# hard head: trait.concussion-immune -> compiled trait tag
# ---------------------------------------------------------------------------
HARD_HEAD_RECIPIENTS = (
    ("dwarf-slayer-cult-web", "giant-slayer", "band--hard-head"),
    ("adventurers-kaz", "dwarf", "dwarf--hard-head"),
    ("clan-angrund-kep", "dwarf-noble", "band--hard-head"),
    ("clan-angrund-kep", "dwarf-troll-slayers", "band--hard-head"),
    ("clockworkers-sc", "dwarf-engineer", "dwarf-engineer--hard-head"),
)


@pytest.mark.parametrize(("band_id", "profile_id", "rule_id"), HARD_HEAD_RECIPIENTS)
def test_hard_head_trait_reaches_each_recipient(band_id, profile_id, rule_id):
    # Tag-only proof: this matrix does not exercise the modular injury consumer.
    assert "concussion_immune" in compile_band(band_id, profile_id).global_effects.tags, rule_id


@pytest.mark.parametrize(
    ("band_id", "profile_id"),
    (("adventurers-kaz", "wizard"), ("clockworkers-sc", "master-of-clocks")),
)
def test_hard_head_trait_stays_absent_from_non_recipients(band_id, profile_id):
    assert "concussion_immune" not in compile_band(band_id, profile_id).global_effects.tags


# ---------------------------------------------------------------------------
# frantic: mechanic skill.always-strikes-first inside a profile grant
# ---------------------------------------------------------------------------
def test_frantic_fanatics_project_the_strike_first_component_once():
    # "will strike first in combat ignoring penalties for weapons or
    # initiative order": the canonical binding is the skill.always-strikes-first
    # mechanic whose execution contract sets priority 1 and its tag.  The
    # same-named rule of night-goblins-mic uses a compiler binding handled by
    # PROFILE_RULE_EFFECTS (priority 10) and is a different origin.
    fanatics = compile_band("night-goblins-kaz", "fanatics")
    assert fanatics.global_effects.priority == 1
    assert "skill.always-strikes-first" in fanatics.global_effects.tags


def test_frantic_component_stays_absent_from_a_non_recipient():
    boss = compile_band("night-goblins-kaz", "big-boss")
    assert "skill.always-strikes-first" not in boss.global_effects.tags
    assert boss.global_effects.priority == 0


# ---------------------------------------------------------------------------
# poisonous: trait.poisonous-injury -> compiled trait tag
# ---------------------------------------------------------------------------
def test_gigantic_spider_poisonous_tag_reaches_the_spider_only():
    # "When it wounds an enemy and a roll is made on the injury table: 1 =
    # knocked down, 2-4 = stunned, 5-6 = out of action" -> the compiled tag
    # connects the profile to the poisonous injury contract.
    spider = compile_band("forest-goblins-lus", "gigantic-spider")
    assert "poisonous_injury" in spider.global_effects.tags
    chieftain = compile_band("forest-goblins-lus", "chieftain")
    assert "poisonous_injury" not in chieftain.global_effects.tags


# ---------------------------------------------------------------------------
# compiler contracts: scaly skin, bite attack, saurus prohibitions, bows
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("band_id", "profile_id", "save"),
    (
        # band-wide Saurus 5+ / Skinks 6+ contract keeps the species split and
        # stays a single natural-save value per fighter.
        ("lizardmen-lus", "saurus-totem-warriors", 5),
        ("lizardmen-lus", "saurus-braves", 5),
        ("lizardmen-lus", "skink-priest", 6),
        ("lizardmen-lus", "kroxigor", 4),
    ),
)
def test_lizardmen_scaly_skin_contract_projects_species_saves(band_id, profile_id, save):
    compiled = compile_band(band_id, profile_id)
    assert compiled.natural_armour_save == save
    assert "compiler.lizardmen-scaly-skin" in compiled.construction_tags


def test_kroxigor_scaly_skin_is_not_applied_twice():
    kroxigor = compile_band("lizardmen-lus", "kroxigor")
    # The profile trait (4+) and the band compiler contract (4+) describe the
    # same save; an additive result would differ from 4.
    assert kroxigor.natural_armour_save == 4


def test_bite_attack_adds_exactly_one_independent_natural_attack():
    saurus = compile_band("lizardmen-lus", "saurus-totem-warriors")
    bites = [attack for attack in saurus.extra_attacks if "rule.bite-attack" in attack.tags]
    assert len(bites) == 1
    assert "weapon.natural-attacks" in bites[0].tags
    # "uses the Saurus' own strength": no weapon modifier is added.
    assert bites[0].strength_bonus == 0
    assert "compiler.bite-attack" in saurus.construction_tags


def test_bite_attack_stays_absent_from_a_non_recipient():
    skink = compile_band("lizardmen-lus", "skink-priest")
    assert not any("rule.bite-attack" in attack.tags for attack in skink.extra_attacks)
    assert "compiler.bite-attack" not in skink.construction_tags


def test_saurus_skill_prohibitions_are_scoped_to_the_eligible_profiles():
    saurus = compile_band("lizardmen-lus", "saurus-totem-warriors")
    assert "compiler.saurus-skill-prohibitions" in saurus.construction_tags
    skink = compile_band("lizardmen-lus", "skink-priest")
    assert "compiler.saurus-skill-prohibitions" not in skink.construction_tags


def test_bow_restrictions_limit_missile_weapons_for_the_whole_band():
    # "may be equipped with only one missile weapon at any time".
    outlaw = compile_band("outlaws-of-stirwood-forest-redux-fbg", "bandit-leader")
    assert outlaw.missile_weapon_limit == 1
    assert "compiler.bow-discipline" in outlaw.construction_tags
    control = compile_band("mercenaries", "mercenary-captain")
    assert control.missile_weapon_limit == 2


# ---------------------------------------------------------------------------
# profile equipment restrictions with a consumed consumption token
# ---------------------------------------------------------------------------
def test_teeny_hands_forbids_armour_for_the_runts():
    bare = compile_band("snotlings-web", "runts")
    assert bare.armour_save == 7  # armour.no-armour compiles
    with pytest.raises(ValueError, match="armour is forbidden for snotlings-web/runts"):
        compile_band("snotlings-web", "runts", armour_id="armour.light-armour")
