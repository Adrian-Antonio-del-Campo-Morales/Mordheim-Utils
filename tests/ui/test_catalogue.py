"""external.test_catalogue: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_skills


def test_catalogue_exposes_kb_profiles_and_profile_equipment():
    catalogue = CombatCatalogue()
    choices = catalogue.profiles("mordheim", "mercenaries")
    captain = next(choice for choice in choices if choice.profile_id == "mercenary-captain")

    assert captain.name == "Mercenary captain"
    assert ("weapon.sword", "Sword") in catalogue.weapons(captain)
    assert catalogue.profile(captain)["characteristics"]["WS"] == 4
    assert (None, "Free hand") in catalogue.off_hand_options(captain)
    assert ("armour.no-armour", "No armour") in catalogue.armours(captain)
    assert catalogue.mechanic("weapon.sword")["hands"] == 1
    assert (None, "No helmet") in catalogue.helmets(captain)
    assert ("material.normal", "Normal") in catalogue.materials(captain)
    assert (None, "No preparation") in catalogue.preparations(captain)
    assert (None, "No poison") in catalogue.poisons(captain)
    assert ("defence.helmet", "Helmet") in catalogue.helmets(captain)
    skills = catalogue.skills(captain)
    assert {skill.id for skill in skills} >= {"skill.mighty-blow", "skill.step-aside", "skill.combat-master"}
    assert "skill.combat-master" not in catalogue.in_scope_skill_ids(skills)
    combat_master = next(skill for skill in skills if skill.id == "skill.combat-master")
    assert combat_master.unavailable_reason == (
        "Its effect requires two or more opponents; the runtime simulates one-against-one duels."
    )
    sprint = next(skill for skill in catalogue.skills(None) if skill.id == "skill.sprint")
    assert sprint.unavailable_reason and sprint.unavailable_reason.startswith("Does not impact duel simulations: ")
    assert catalogue.profile_rules(captain)[0].name == "Leader"


def test_profile_keeps_all_general_skill_categories_visible():
    catalogue = CombatCatalogue()
    profile = next(
        choice for choice in catalogue.profiles("mordheim", "amazons-lustria")
        if choice.profile_id == "eagle-warriors"
    )
    general_skills = [skill for skill in catalogue.skills(profile) if skill.selection_kind == "skill"]

    assert {skill.category for skill in general_skills} == {
        str(skill["category"])
        for skill in load_skills("mordheim")
        if skill.get("category") != "special"
    }
    inaccessible = next(skill for skill in general_skills if skill.category not in catalogue.profile(profile)["skill_access"])
    assert not inaccessible.runtime_available


def test_mordheim_amazons_have_no_special_skills():
    catalogue = CombatCatalogue()
    priestess = next(
        choice for choice in catalogue.profiles("mordheim", "amazons-mordheim")
        if choice.profile_id == "priestess"
    )

    assert not [skill for skill in catalogue.skills(priestess) if skill.category == "special"]


def test_catalogue_exposes_runtime_options_for_free_selection():
    catalogue = CombatCatalogue()

    assert ("weapon.sword", "Sword") in catalogue.weapons(None)
    assert ("armour.no-armour", "No armour") in catalogue.armours(None)
    assert {skill.id for skill in catalogue.skills(None)} >= {"skill.mighty-blow", "skill.step-aside"}


def test_catalogue_filters_bands_by_the_legacy_collection_grades():
    catalogue = CombatCatalogue()

    core = catalogue.bands_for_categories({"core"})
    trollheim = catalogue.bands_for_categories({"trollheim"})

    assert core
    assert trollheim
    assert all("core" in package.band.get("categories", ()) for package in core)
    assert all("trollheim" in package.band.get("categories", ()) for package in trollheim)


def test_catalogue_limits_special_skills_to_the_selected_warband():
    catalogue = CombatCatalogue()
    amazon = catalogue.profiles("mordheim", "amazons-lustria")[0]
    arabian = catalogue.profiles("mordheim", "arabian-tomb-raiders")[0]
    lizardman = catalogue.profiles("mordheim", "lizardmen")[0]

    amazon_special = {skill.rule_id for skill in catalogue.skills(amazon) if skill.category == "special"}
    arabian_special = {skill.rule_id for skill in catalogue.skills(arabian) if skill.category == "special"}
    lizardman_special = {skill.rule_id for skill in catalogue.skills(lizardman) if skill.category == "special"}

    assert len(amazon_special) == 5
    assert arabian_special == {
        "band--arabian-tomb-raiders-special-skills-sand-worm",
        "band--arabian-tomb-raiders-special-skills-hit-and-run",
        "band--arabian-tomb-raiders-special-skills-weather-tolerant",
    }
    assert lizardman_special == {
        "band--lizardmen-special-skills-skinks-only-infiltration",
        "band--lizardmen-special-skills-skinks-only-great-hunter",
        "band--lizardmen-special-skills-saurus-only-bellowing-battle-roar",
        "band--lizardmen-special-skills-saurus-only-toughened-hide",
    }
    bellowing_roar = next(
        skill for skill in catalogue.skills(lizardman)
        if skill.rule_id == "band--lizardmen-special-skills-saurus-only-bellowing-battle-roar"
    )
    assert not bellowing_roar.runtime_available


def test_catalogue_uses_a_trollheim_band_canonical_family_for_special_skills():
    catalogue = CombatCatalogue()
    lizardman = next(
        choice for choice in catalogue.profiles("trollheim", "lustria-lizardmen")
        if choice.profile_id == "saurus-totem-warrior"
    )

    assert "band--lizardmen-special-skills-battle-roar" in {
        skill.rule_id for skill in catalogue.skills(lizardman) if skill.category == "special"
    }


def test_catalogue_exposes_executable_warband_skills_in_the_skill_list():
    catalogue = CombatCatalogue()
    pit_king = next(
        choice for choice in catalogue.profiles("mordheim", "pit-fighters")
        if choice.profile_id == "pit-king"
    )
    rules = {skill.rule_id for skill in catalogue.skills(pit_king) if skill.selection_kind == "warband_skill"}

    assert {
        "band--pit-fighter-skill-arms-master",
        "band--pit-fighter-skill-body-slam",
        "band--pit-fighter-skill-force-of-will",
    } <= rules


def test_catalogue_exposes_new_first_batch_choices_and_pirate_mercenary_equipment():
    catalogue = CombatCatalogue()
    horned = next(choice for choice in catalogue.profiles("mordheim", "horned-hunters") if choice.profile_id == "horned-hunter")
    ogre = next(choice for choice in catalogue.profiles("mordheim", "maneaters") if choice.profile_id == "captain")
    pirate = next(choice for choice in catalogue.profiles("trollheim", "lustria-pirates") if choice.profile_id == "pirate-captain")

    assert "band--horned-hunter-special-skills-animal-friendship" in {skill.rule_id for skill in catalogue.skills(horned)}
    assert "band--ogres-special-skills-master-of-arms" in {skill.rule_id for skill in catalogue.skills(ogre)}
    assert ("armour.heavy-armour", "Heavy armour") in catalogue.armours(pirate)


def test_profile_lists_every_special_skill_from_its_band_only():
    catalogue = CombatCatalogue()

    for package in catalogue.bands_for_categories(set()):
        for choice in catalogue.profiles(package.collection, str(package.band["id"])):
            warband_rule_ids = {
                str(rule["id"])
                for rule in package.special_rules
                if rule.get("kind") == "warband_skill"
            }
            for skill in catalogue.skills(choice):
                if skill.category != "special":
                    continue
                assert skill.rule_id in warband_rule_ids


def test_free_selection_lists_every_warband_skill_but_does_not_grant_band_access():
    catalogue = CombatCatalogue()
    skills = catalogue.skills(None)
    warband_skills = [skill for skill in skills if skill.selection_kind == "warband_skill"]

    assert len(warband_skills) == 305
    hit_and_run = next(skill for skill in warband_skills if skill.rule_id == "band--arabian-tomb-raiders-special-skills-hit-and-run")
    assert not hit_and_run.runtime_available
    assert hit_and_run.unavailable_reason
    assert hit_and_run.name.endswith("· Arabian Tomb Raiders")


def test_selected_band_omits_the_redundant_warband_name_from_special_skills():
    catalogue = CombatCatalogue()
    raider = catalogue.profiles("mordheim", "arabian-tomb-raiders")[0]
    hit_and_run = next(
        skill for skill in catalogue.skills(raider)
        if skill.rule_id == "band--arabian-tomb-raiders-special-skills-hit-and-run"
    )

    assert hit_and_run.name == "Hit and Run"


def test_battle_monk_special_skills_respect_the_skill_table_and_rule_eligibility():
    catalogue = CombatCatalogue()
    profiles = {
        choice.profile_id: choice
        for choice in catalogue.profiles("mordheim", "battle-monks-of-cathay")
    }
    energy_focus = "band--battle-monks-special-skills-energy-focus"

    dragon_energy = next(skill for skill in catalogue.skills(profiles["dragon-monks"]) if skill.rule_id == energy_focus)
    officer_energy = next(skill for skill in catalogue.skills(profiles["officer"]) if skill.rule_id == energy_focus)
    assert dragon_energy.runtime_available
    assert not officer_energy.runtime_available


def test_warband_skill_ui_identity_maps_to_the_selected_band_rule():
    catalogue = CombatCatalogue()
    saurus = next(
        choice for choice in catalogue.profiles("mordheim", "lizardmen")
        if choice.profile_id == "saurus-totem-warrior"
    )
    battle_roar = next(
        skill for skill in catalogue.skills(saurus)
        if skill.rule_id == "band--lizardmen-special-skills-saurus-only-bellowing-battle-roar"
    )

    ordinary, special = catalogue.skill_rule_ids((battle_roar.id, "skill.mighty-blow"))
    assert ordinary == ("skill.mighty-blow",)
    assert special == (battle_roar.rule_id,)
    assert battle_roar.id in catalogue.skill_ui_ids(saurus, ordinary, special)


def test_profile_build_can_apply_user_edited_characteristics():
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(5, 4, 4, 2, 5, 2),
        band_id="mercenaries", profile_id="mercenary-captain",
    ))

    assert fighter.fighter_id == "mercenaries:mercenary-captain"
    assert fighter.characteristics == Characteristics(5, 4, 4, 2, 5, 2)
