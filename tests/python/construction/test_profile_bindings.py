"""Automatic profile bindings."""
from __future__ import annotations

from functools import lru_cache

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest as pytest


@lru_cache(maxsize=None)
def _catalogue():
    from mordheim_combat_lab.application.catalogue import CombatCatalogue
    return CombatCatalogue()


def _possession_issues(band: str, profile: str, item: str):
    """Codes of an explicit selection that never passes through the picker."""
    choice = next(row for row in _catalogue().profiles("mordheim", band) if row.profile_id == profile)
    return [issue["code"] for issue in _catalogue().validate_configuration(
        choice, possession=(item,), slots={"main_weapon_id": "weapon.fist"})]


#: (band, list, item, profile, expected code) — one printed recipient clause each.
#: The matrix keeps a forbidden bearer, its lawful control, the local-not-global
#: pair and an unqualified entry of the same list side by side.
PRINTED_RECIPIENTS = [
    ("estalian-corsairs-sar", "crew", "cat_o_nine_tails", "equipment_not_permitted"),
    ("estalian-corsairs-sar", "captain", "cat_o_nine_tails", None),
    ("low-kings-mim", "rapscallions", "lock_picks", "equipment_not_permitted"),
    ("low-kings-mim", "fence", "lock_picks", None),
    ("khorne-raiders-sar", "madbrains", "light_armour", "equipment_not_permitted"),
    ("khorne-raiders-sar", "flayerkin", "light_armour", None),
    ("khorne-raiders-sar", "quartermasters", "light_armour", None),
    ("outlaws-of-stirwood-forest", "outlaws", "hunting_arrows", "equipment_not_permitted"),
    ("outlaws-of-stirwood-forest", "marksmen", "hunting_arrows", None),
    ("outlaws-of-stirwood-forest", "cleric", "hunting_arrows", None),
    ("silent-brotherhood-sc", "brotherhood-novices", "long_daggers", "equipment_not_permitted"),
    ("silent-brotherhood-sc", "silent-master", "long_daggers", None),
    ("sisters-of-sigmar", "novices", "holy_relic", "equipment_not_permitted"),
    ("sisters-of-sigmar", "augur", "holy_relic", None),
    ("protectorate-of-sigmar-lotd3", "warrior-priest", "holy_relic", None),
    ("tomb-guardians", "skeleton-warriors", "asp_arrows", "equipment_not_permitted"),
    ("tomb-guardians", "tomb-lord", "asp_arrows", None),
    ("snotlings-web", "runts", "light_armour", "equipment_not_permitted"),
    ("snotlings-web", "bigsnotz", "light_armour", None),
    ("halflings-mic", "halfling-warriors", "bow", "equipment_not_permitted"),
    ("halflings-mic", "halfling-cook", "bow", None),
    ("halflings-mic", "halfling-scouts", "short_bow", None),
    ("halflings-mic", "halfling-warriors", "spear", None),
    ("halflings-mic", "halfling-scouts", "spear", "equipment_not_permitted"),
    ("silent-brotherhood-sc", "silent-master", "great_weapon", None),
    ("silent-brotherhood-sc", "brotherhood-novices", "great_weapon", "equipment_not_permitted"),
    ("sartosan-pirates-sar", "crew", "cat_o_nine_tails", "equipment_not_permitted"),
    ("sartosan-pirates-sar", "captain", "cat_o_nine_tails", None),
]


@pytest.mark.parametrize("band,profile,item,expected", PRINTED_RECIPIENTS,
                         ids=lambda value: str(value))
def test_printed_entry_recipients_decide_the_explicit_selection(band, profile, item, expected):
    # The item is offered by a list the profile declares, so the verdict comes
    # from the printed recipients alone: an absent option is not proof that a
    # direct selection is refused. Only the recipient outcome is asserted; the
    # band's own kit obligations (bow discipline and the like) are unrelated.
    issues = _possession_issues(band, profile, item)
    if expected is None:
        assert "equipment_not_permitted" not in issues
    else:
        assert expected in issues


def test_f074_rulings_keep_knights_and_promoted_heroes_distinct_from_henchmen():
    catalogue = _catalogue()
    for profile in ("paragon", "gallant", "redeemed-knights", "pilgrims"):
        issues = _possession_issues("order-of-the-mare-web", profile, "heavy_armour")
        assert ("equipment_not_permitted" in issues) == (profile == "pilgrims")
    for profile in ("hunt-master", "deepwood-scout", "glade-guard"):
        choice = next(row for row in catalogue.profiles("mordheim", "wood-elves-of-athel-loren-web")
                      if row.profile_id == profile)
        variants = ((),) if profile == "hunt-master" else ((), ("promotion.hero",))
        for variant_ids in variants:
            for item in ("ithilmar_weapon", "ithilmar_armour"):
                issues = catalogue.validate_configuration(
                    choice, possession=(item,), slots={"main_weapon_id": "weapon.fist"},
                    variant_ids=variant_ids)
                denied = any(issue["code"] == "equipment_not_permitted" for issue in issues)
                assert denied == (profile != "hunt-master" and not variant_ids)


def test_printed_recipients_reach_the_compiler_not_only_the_picker():
    # A direct build that never passes through the picker is judged by the same
    # shared decision: the hero-only katana of the shared pirate list reaches its
    # printed recipients and is refused to the henchmen that also buy there.
    compile_fighter(FighterBuild(
        "mordheim", band_id="pirates-of-the-cathayan-sea-sar", profile_id="disgraced-warlord",
        main_weapon_id="weapon.katana",
    ))
    with pytest.raises(ValueError, match="equipment is not available"):
        compile_fighter(FighterBuild(
            "mordheim", band_id="pirates-of-the-cathayan-sea-sar", profile_id="deck-hands",
            main_weapon_id="weapon.katana",
        ))


def test_slayer_vow_refuses_armour_and_missile_weapons_to_slayers_only():
    # The printed note on the armour, shield, helmet and pistol rows repeats the
    # restriction each Slayer profile carries, so it applies to the Slayer
    # profiles of the shared list and never to the other Dwarfs that buy there.
    for profile in ("troll-slayers", "giant-slayer", "slayers"):
        assert _possession_issues("dwarf-slayers-kaz", profile, "light_armour") == ["equipment_forbidden"]
        assert _possession_issues("dwarf-slayers-kaz", profile, "helmet") == ["equipment_forbidden"]
    for profile in ("clansmen", "rememberer"):
        assert _possession_issues("dwarf-slayers-kaz", profile, "light_armour") == []
        assert _possession_issues("dwarf-slayers-kaz", profile, "helmet") == []


def test_profile_characteristics_projects_selected_bonuses():
    ordinary = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
    ))
    middenheimer = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
        special_rule_ids=("band--middenheim-physical-prowess",),
    ))
    assert middenheimer.characteristics.strength == ordinary.characteristics.strength + 1


def test_profile_fist_overrides_the_unarmed_profile_fallback():
    peasant = compile_fighter(FighterBuild(
        "mordheim", band_id="battle-monks-of-cathay", profile_id="raging-peasants",
    ))
    assert "weapon.fist" in peasant.main_weapon.tags
    assert peasant.main_weapon.strength_bonus == -1
    assert peasant.main_weapon.target_armour_bonus == 1


def test_profile_natural_attacks_selects_the_natural_weapon():
    warhound = compile_fighter(FighterBuild(
        "mordheim", band_id="beastmen-raiders", profile_id="warhounds-of-chaos",
    ))
    assert "weapon.natural-attacks" in warhound.main_weapon.tags
    assert "weapon.fist" not in warhound.main_weapon.tags


def test_profile_random_characteristics_preserves_the_exact_dice_contract():
    condemned = compile_fighter(FighterBuild(
        "mordheim", band_id="marauders-of-chaos", profile_id="condemned",
    ))
    assert condemned.random_characteristics == (
        ("WS", 1, 6, 0),
        ("S", 1, 6, 0),
        ("T", 1, 6, 0),
        ("A", 1, 3, 0),
    )


def test_profile_equipment_restrictions_have_a_legal_and_an_illegal_case():
    compile_fighter(FighterBuild(
        "mordheim", band_id="horned-hunters", profile_id="priest-of-taal",
    ))
    with pytest.raises(ValueError, match="equipment is not available|heavy armour is forbidden"):
        compile_fighter(FighterBuild(
            "mordheim", band_id="horned-hunters", profile_id="priest-of-taal",
            armour_id="armour.heavy-armour",
        ))


def test_profile_armour_prohibition_covers_the_pirate_equipment_lists():
    # Every profile printed with "May not wear armour." offers armour suits on
    # its own equipment list, so the restriction must refuse them at construction
    # instead of relying on the legacy prose match.
    for band, profile in (
        ("bretonnian-buccaneers-sar", "captain"),
        ("estalian-corsairs-sar", "gunners"),
        ("khorne-raiders-sar", "dread-captain"),
        ("pirates-of-the-cathayan-sea-sar", "deck-hands"),
        ("sartosan-pirates-sar", "crew"),
        ("wasteland-privateers-sar", "boatswains"),
        ("nipponese-expedition-web", "warrior-monks"),
    ):
        compile_fighter(FighterBuild(
            "mordheim", band_id=band, profile_id=profile, armour_id="armour.no-armour",
        ))
        with pytest.raises(ValueError, match="forbidden"):
            compile_fighter(FighterBuild(
                "mordheim", band_id=band, profile_id=profile, armour_id="armour.light-armour",
            ))


def test_pirate_armour_prohibition_leaves_hand_held_defences_selectable():
    # "May not wear armour" forbids armour suits, not the shield and helmet the
    # same printed list offers, so the restriction must use the armour-suit token.
    compile_fighter(FighterBuild(
        "mordheim", band_id="bretonnian-buccaneers-sar", profile_id="captain",
        off_hand_id="defence.shield",
    ))


def test_profile_skill_access_has_a_rejected_and_granted_strength_skill():
    with pytest.raises(ValueError, match="skills are not available"):
        compile_fighter(FighterBuild(
            "mordheim", band_id="dark-elves", profile_id="high-born",
            skill_ids=("skill.mighty-blow",),
        ))
    granted = compile_fighter(FighterBuild(
        "mordheim", band_id="dark-elves", profile_id="high-born",
        skill_ids=("skill.mighty-blow",),
        special_rule_ids=("band--dark-elf-special-skills-powerful-build",),
    ))
    assert granted.global_effects.strength_bonus == 1
