"""C05b: printed skill-table grants, their recipients and one shared guard.

Every case drives the canonical offer (``desktop_call``) and, where the
printed member has an executable consequence, the direct compilation of the
same member. Offer-only rows assert the table reaches exactly the printed
recipients, never that the member effects are granted by the table.
"""
from __future__ import annotations

import pytest

from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands, knowledge_root, read_yaml

ROOT = knowledge_root()
COLLECTION = "mordheim"


def package(band_id, collection=COLLECTION):
    return next(pack for pack in load_bands(collection, ROOT) if pack.band["id"] == band_id)


def profile_of(pack, profile_id):
    return next(row for row in pack.profiles if row["id"] == profile_id)


def build(band_id, profile_id, **options):
    return FighterBuild(COLLECTION, band_id=band_id, profile_id=profile_id,
                        collection=COLLECTION, **options)


def offered(band_id, profile_id, **options):
    pack = package(band_id)
    return desktop_call("specialRules", build(band_id, profile_id, **options), ROOT,
                        package=pack, profile=profile_of(pack, profile_id))


@pytest.mark.phase2_construction
def test_the_village_ogre_promotion_projects_combat_and_strength_only():
    pack = package("halflings-mic")
    ogre = profile_of(pack, "village-ogre")
    facts = desktop_call("profileFacts", build("halflings-mic", "village-ogre"), ROOT,
                         package=pack, profile=ogre)
    assert facts["promotion_skill_access"] == ["combat", "strength"]
    # The grant is a promotion projection: the unpromoted Henchman keeps none
    # of it in its ordinary access.
    assert "combat" not in ogre.get("skill_access", [])
    assert "strength" not in ogre.get("skill_access", [])


@pytest.mark.phase2_construction
def test_the_emissary_reaches_warmonger_alone_and_the_monks_reach_their_table():
    assert "band--battle-monks-special-skills-warmonger" in offered(
        "battle-monks-of-cathay", "emissary")
    for other in ("energy-focus", "lightning-speed", "leap-of-faith", "human-shield"):
        assert f"band--battle-monks-special-skills-{other}" not in offered(
            "battle-monks-of-cathay", "emissary")
    for profile_id in ("officer", "dragon-monks", "warrior-monks"):
        table = offered("battle-monks-of-cathay", profile_id)
        assert "band--battle-monks-special-skills-energy-focus" in table, profile_id
        assert "band--battle-monks-special-skills-warmonger" not in table, profile_id
    # Direct selection of a member outside the Emissary's one printed skill fails.
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build("battle-monks-of-cathay", "emissary",
            special_rule_ids=("band--battle-monks-special-skills-energy-focus",)), ROOT)


@pytest.mark.phase2_construction
def test_powerful_build_grants_strength_and_excludes_the_sorceress():
    rule = "band--dark-elf-special-skills-powerful-build"
    assert rule in offered("dark-elves", "high-born")
    assert rule not in offered("dark-elves", "dark-elf-sorceress")
    accepted = compile_fighter(build("dark-elves", "high-born", special_rule_ids=(rule,),
                                     skill_ids=("skill.mighty-blow",)), ROOT)
    assert "skill.mighty-blow" in accepted.global_effects.tags
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build("dark-elves", "dark-elf-sorceress", special_rule_ids=(rule,)), ROOT)


@pytest.mark.phase2_construction
def test_cunning_opens_the_melee_catalogue_only_through_weapons_training():
    cunning = "charnel-guard--cunning"
    with pytest.raises(ValueError, match="forbidden|not available|not on any equipment list"):
        compile_fighter(build("strigoi-kaz", "charnel-guard",
                              main_weapon_id="weapon.sword"), ROOT)
    # Cunning is an inherent profile rule, not a selectable one; the exception
    # it prints travels with the profile.
    assert "charnel-guard--cunning" in profile_of(package("strigoi-kaz"),
        "charnel-guard")["rule_ids"]
    trained = compile_fighter(build("strigoi-kaz", "charnel-guard",
        skill_ids=("skill.weapons-training",), main_weapon_id="weapon.sword"), ROOT)
    assert trained
    # Weapons Expert is dispositioned separately as missile access; it does not
    # become a second hand-to-hand permission here.
    with pytest.raises(ValueError, match="forbidden|not available|not on any equipment list"):
        compile_fighter(build("strigoi-kaz", "charnel-guard",
            skill_ids=("skill.weapons-expert",), main_weapon_id="weapon.sword"), ROOT)


@pytest.mark.phase2_construction
def test_the_strigany_table_reaches_its_heroes_and_bull_rush_keeps_its_operator():
    for profile_id in ("domnu", "petru", "tinker", "truants"):
        table = offered("channel-rats-mim", profile_id)
        assert "band--strigany-special-skills-bull-rush" in table, profile_id
        assert "band--strigany-special-skills-infiltration" in table, profile_id
    assert "band--strigany-special-skills-bull-rush" not in offered(
        "channel-rats-mim", "gypsies")
    accepted = compile_fighter(build("channel-rats-mim", "domnu",
        special_rule_ids=("band--strigany-special-skills-bull-rush",)), ROOT)
    assert accepted
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build("channel-rats-mim", "gypsies",
            special_rule_ids=("band--strigany-special-skills-bull-rush",)), ROOT)


@pytest.mark.phase2_construction
def test_the_nippon_table_is_access_not_a_grant_of_its_members():
    hatamoto = offered("nipponese-expedition-web", "hatamoto")
    assert "band--nippon-special-skills-iaijutsu" in hatamoto
    assert "band--nippon-special-skills-night-fighter" not in hatamoto
    assert "band--nippon-special-skills-night-fighter" in offered(
        "nipponese-expedition-web", "shinobi")
    # Iaijutsu is offered as a printed member but its deferred effect is not
    # silently granted by the table.
    with pytest.raises(ValueError, match="outside the executable duel runtime"):
        compile_fighter(build("nipponese-expedition-web", "hatamoto",
            special_rule_ids=("band--nippon-special-skills-iaijutsu",)), ROOT)


@pytest.mark.phase2_construction
def test_the_ogre_table_reaches_ogres_and_gnoblars_with_its_named_members():
    for profile_id in ("ogre-hunter", "trappers", "sabre-baiter"):
        table = offered("ogre-hunting-party-web", profile_id)
        assert "band--ogre-hunting-skills-scent-hound" in table, profile_id
    assert "band--ogre-hunting-skills-bull-charge" in offered(
        "ogre-hunting-party-web", "ogre-hunter")
    assert "band--ogre-hunting-skills-set-traps" not in offered(
        "ogre-hunting-party-web", "ogre-hunter")
    assert "band--ogre-hunting-skills-set-traps" in offered(
        "ogre-hunting-party-web", "trappers")


@pytest.mark.phase2_construction
def test_veteran_tracker_requires_exactly_one_named_starting_skill():
    pack = package("ogre-hunting-party-web")
    trapper = profile_of(pack, "trappers")
    assert trapper.get("rule_ids") and "trappers--veteran-tracker" in trapper["rule_ids"]
    with pytest.raises(ValueError, match="exactly one starting special skill"):
        compile_fighter(build("ogre-hunting-party-web", "trappers"), ROOT)
    with pytest.raises(ValueError, match="exactly one starting special skill"):
        compile_fighter(build("ogre-hunting-party-web", "trappers", special_rule_ids=(
            "band--ogre-hunting-skills-netter", "band--ogre-hunting-skills-set-traps")), ROOT)
    accepted = compile_fighter(build("ogre-hunting-party-web", "trappers",
        special_rule_ids=("band--ogre-hunting-skills-netter",)), ROOT)
    assert accepted


@pytest.mark.phase2_construction
def test_savage_orcs_inherit_the_orc_table_without_copying_its_origin():
    savage = offered("savage-orcs-kaz", "boss")
    assert "band--orc-special-skills-ard-ead" in savage
    assert "band--orc-special-skills-eadbasher" in savage
    assert "band--orc-special-skills-ard-ead" not in offered("savage-orcs-kaz", "boyz")
    accepted = compile_fighter(build("savage-orcs-kaz", "boss",
        special_rule_ids=("band--orc-special-skills-ard-ead",)), ROOT)
    assert "skill.thick-skull" in accepted.global_effects.tags


# Primary: the canonical skill reaches the two hirelings. The Ninja's profile
# record is the secondary guarantee where its kit is separately blocked.
@pytest.mark.phase2_construction
def test_the_two_hirelings_take_art_of_silent_death():
    """The printed skill now has a canonical id, so the hirelings carry it."""
    packages = {pack.band["id"]: {row["id"] for row in pack.profiles}
                for pack in combat_packages(COLLECTION)}
    ippan = compile_fighter(FighterBuild(COLLECTION, band_id="hirelings.dramatis-personae.1c",
        profile_id="hireling.dramatis.grand-master-ippan-shu", collection=COLLECTION), ROOT)
    assert "skill.art-of-silent-death" in ippan.global_effects.tags
    # The Ninja's kit still lacks a canonical smoke-bomb mapping, so its own
    # compilation is blocked by that separate hireling gap; the published
    # starting skill is asserted on the profile itself.
    assert "hireling.hired-sword.ninja" in packages["hirelings.hired-sword.1c"]
    ninja = next(row for pack in combat_packages(COLLECTION) for row in pack.profiles
                 if row["id"] == "hireling.hired-sword.ninja")
    assert "skill.art-of-silent-death" in ninja["starting_skill_ids"]


@pytest.mark.phase2_construction
def test_bertha_takes_the_canonical_righteous_fury():
    """The band-scoped skill became canonical, so the hireling starts with it."""
    bertha = compile_fighter(FighterBuild(COLLECTION, band_id="hirelings.dramatis-personae.core",
        profile_id="hireling.dramatis.bertha-bestraufrung", collection=COLLECTION), ROOT)
    assert "skill.righteous-fury" in bertha.global_effects.tags


@pytest.mark.phase1_kb_contracts
def test_da_boss_is_dead_publishes_the_black_orc_successor():
    """The printed handover is campaign data, not a duel mechanic."""
    catalogue = read_yaml(ROOT / "catalog" / "campaign" / "recruitment-and-veterans.yaml")
    clause = next(row for row in catalogue["succession_clauses"]
                  if row["rule_id"] == "band--da-boss-is-dead")
    assert clause["band_id"] == "black-orcs"
    assert clause["leader_profile_ids"] == ["black-orc-boss"]
    assert clause["successor_profile_ids"] == ["black-orcs"]
    band = package("black-orcs")
    profiles = {row["id"] for row in band.profiles}
    assert {"black-orc-boss", "black-orcs"} <= profiles
    rule = next(row for row in band.special_rules if row["id"] == "band--da-boss-is-dead")
    assert rule["runtime"]["scope"] == "NO"
    assert "Oi Behave!" in clause["effect"]


@pytest.mark.phase2_construction
def test_the_seer_becomes_a_bloodfather_with_strength_access_only_under_the_mark():
    mark = "band--mark-of-arkhar"
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build("marauders-of-chaos", "seer", skill_ids=("skill.mighty-blow",)), ROOT)
    accepted = compile_fighter(build("marauders-of-chaos", "seer",
        special_rule_ids=(mark,), skill_ids=("skill.mighty-blow",)), ROOT)
    assert "skill.mighty-blow" in accepted.global_effects.tags
    # The Bloodfather consequence belongs to the Seer: the mark adds no skill
    # list of its own to the Chieftain's projection.
    pack = package("marauders-of-chaos")
    chief = profile_of(pack, "marauder-chieftain")
    chief_facts = desktop_call("profileFacts", build("marauders-of-chaos", "marauder-chieftain",
        special_rule_ids=(mark,)), ROOT, package=pack, profile=chief)
    assert not [row for row in chief_facts["skill_lists"] if row["rule_id"] == mark]
