"""T13.2d -- selectable rules and equipment: legal selection and compilation.

Derived from the T13.2 partition of
``docs/knowledge/2a2b/tasks/T13-obligations.csv``: 55 register origins whose
canonical band rule declares ``runtime.grant: selectable`` and 95 equipment
origins.  The suite exercises the real construction path (``FighterBuild`` ->
``compile_fighter``) and the real availability surface
(``available_special_rules``) for every origin the runtime is connected to, and
pins the exact runtime gate that refuses the pending selectable origins with
their published source reason.

Expectations come from the canonical KB (recipients, bindings, item mappings
and execution parameters) and the accepted T13.0/T13.1/T13.2a decisions, not
from the compiler output.  This proves selection and compilation only: a
compiled weapon or skill does not certify its combat rolls, criticals, parries
or resolution effects; T13.3/T13.4 and T14 own those.
"""
from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path

import pytest
import yaml

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import available_special_rules
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
REGISTER = ROOT / "docs" / "knowledge" / "2a2b" / "tasks" / "T13-obligations.csv"

#: The ten implemented selectable rules of the partition (eleven origins: Master
#: of Blades contributes two skill bindings) keyed by their canonical band and
#: the recipient checked below.  Dwarf Treasure Hunter copies of the same
#: mechanics are separate origins outside this partition.
IMPLEMENTED = (
    ("grave-robbers-sylv", "graver", "band--special-skill-hardy-constitution"),
    ("clan-angrund-kep", "dwarf-noble", "band--dwarf-special-skills-master-of-blades"),
    ("clan-angrund-kep", "dwarf-noble", "band--dwarf-special-skills-true-grit"),
    ("clan-angrund-kep", "dwarf-noble", "band--dwarf-special-skills-thick-skull"),
    ("clan-angrund-kep", "dwarf-troll-slayers", "band--slayer-special-skills-ferocious-charge"),
    ("clan-angrund-kep", "dwarf-troll-slayers", "band--slayer-special-skills-monster-slayer"),
    ("clan-angrund-kep", "dwarf-troll-slayers", "band--slayer-special-skills-berserker"),
    ("lizardmen-lus", "saurus-totem-warriors", "band--lizardmen-special-skills-saurus-only-bellowing-battle-roar"),
    ("underworld-alliance-mim", "warpstone-troll", "warpstone-troll--vomit-attack"),
    ("halflings-mic", "halfling-elder", "halfling-elder--shifty"),
)

#: Every selectable origin whose runtime is not executable and whose band
#: publishes a selection channel, with a recipient the band really offers it
#: to.  The refusal must name the rule and carry the reason published by the
#: rule's own runtime block.
PENDING = (
    ("dreamwalkers-cult-of-morr-fbg", "dreamer", "band--special-skill-inspiring-presence"),
    ("dreamwalkers-cult-of-morr-fbg", "dreamer", "band--special-skill-fanatical"),
    ("dreamwalkers-cult-of-morr-fbg", "dreamer", "band--special-skill-inured-to-horror"),
    ("grave-robbers-sylv", "graver", "band--special-skill-darkstalker"),
    ("grave-robbers-sylv", "graver", "band--special-skill-instinctual-violence"),
    ("grave-robbers-sylv", "graver", "band--special-skill-de-animator"),
    ("necrarchs-the-soul-stealers-lotd1", "necrarch-vampire", "band--special-skill-pull-of-undeath"),
    ("vampire-hunters-of-sylvania-lotd5", "vampire-hunter", "band--special-skill-iron-will"),
    ("vampire-hunters-of-sylvania-lotd5", "vampire-hunter", "band--special-skill-righteous-aura"),
    ("vampire-hunters-of-sylvania-lotd5", "vampire-hunter", "band--special-skill-thirst-for-vengeance"),
    ("vampire-hunters-of-sylvania-lotd5", "vampire-hunter", "band--special-skill-blessing-of-morr"),
    ("wood-elves-of-athel-loren-web", "hunt-master", "band--skill-elven-luck"),
    ("brood-of-ghurash-the-sc", "broodmother", "band--skill-the-terror"),
    ("brood-of-ghurash-the-sc", "broodmother", "band--skill-ground-pounder"),
    ("brood-of-ghurash-the-sc", "broodmother", "band--skill-titanic-strength"),
    ("brood-of-ghurash-the-sc", "broodmother", "band--skill-hurl"),
    ("call-of-the-night-haint-mim", "cairn-wraith", "band--skill-wight-walk"),
    ("clockworkers-sc", "master-of-clocks", "band--skill-puppeteer"),
    ("clockworkers-sc", "master-of-clocks", "band--skill-rogue-control"),
    ("clockworkers-sc", "master-of-clocks", "band--skill-gift-of-sentience"),
    ("high-elves-lus", "loremaster", "band--skill-miniath"),
    ("high-elves-lus", "loremaster", "band--skill-unerring-strike"),
    ("high-elves-lus", "loremaster", "band--skill-fey-quickness"),
    ("knights-of-the-bitter-moors-mim", "questing-knight", "band--virtue-of-valour"),
    ("knights-of-the-bitter-moors-mim", "questing-knight", "band--virtue-of-discipline"),
    ("knights-of-the-bitter-moors-mim", "questing-knight", "band--virtue-of-noble-disdain"),
    ("knights-of-the-bitter-moors-mim", "questing-knight", "band--virtue-of-the-impetuous"),
    ("lizardmen-lus", "saurus-totem-warriors", "band--lizardmen-special-skills-saurus-only-toughened-hide"),
    ("silent-brotherhood-sc", "silent-master", "band--skill-cutthroat"),
    ("silent-brotherhood-sc", "silent-master", "band--skill-hit-and-run"),
    ("silent-brotherhood-sc", "silent-master", "band--skill-backstabber"),
    ("skaven-of-clan-pestilens-lus", "plague-priest", "band--skill-cloud-of-flies"),
    ("skaven-of-clan-pristekk-sc", "chieftain", "band--skill-thing-handler"),
    ("underworld-alliance-mim", "goblin-bully", "band--skill-wyrdstone-addict"),
    ("underworld-alliance-mim", "goblin-bully", "band--skill-stuff-em-with-green"),
)

#: The remaining pending origins refuse with the same runtime gate, but their
#: current warband-skill availability API omits them. Eight lack its access/
#: eligibility route; bloodline explicitly names vampire as its recipient but is
#: a profile ability, excluded by the API's kind filter. Source legality is not
#: adjudicated here. The missing API channel is recorded as a discrepancy in
#: docs/knowledge/2a2b/tasks/T13-selectable-equipment.md; the runtime refusal
#: below is real either way.
PENDING_WITHOUT_AVAILABILITY_CHANNEL = (
    ("protectorate-of-sigmar-lotd3", "warrior-priest", "band--special-skill-unshakeable-faith"),
    ("protectorate-of-sigmar-lotd3", "warrior-priest", "band--special-skill-utter-determination"),
    ("protectorate-of-sigmar-lotd3", "warrior-priest", "band--special-skill-rousing-sermon"),
    ("araby-smugglers-sar", "rais", "band--skill-pious-fury"),
    ("sea-ghosts-mim", "feast-master", "band--dance-whirling-death"),
    ("sea-ghosts-mim", "feast-master", "band--dance-storm-of-blades"),
    ("sea-ghosts-mim", "feast-master", "band--dance-the-shadows-coil"),
    ("sea-ghosts-mim", "feast-master", "band--dance-woven-mist"),
    ("strigoi-kaz", "vampire", "vampire--bloodline"),
)


def build(band_id, profile_id, **kwargs):
    return FighterBuild("mordheim", band_id=band_id, profile_id=profile_id, **kwargs)


@lru_cache(maxsize=None)
def _package(band_id: str):
    for package in load_bands("mordheim", KNOWLEDGE):
        if str(package.band.get("id")) == band_id:
            return package
    raise AssertionError(f"the canonical KB declares no band {band_id}")


def _rule(band_id: str, rule_id: str) -> dict:
    rule = next((row for row in _package(band_id).special_rules if str(row.get("id")) == rule_id), None)
    assert rule is not None, f"{band_id} declares no rule {rule_id}"
    return rule


def _runtime_reason(band_id: str, rule_id: str) -> str:
    runtime = _rule(band_id, rule_id).get("runtime") or {}
    reason = next((str(effect["reason"]) for effect in runtime.get("effects") or () if effect.get("reason")), "")
    assert reason, f"{rule_id} publishes no runtime reason; the gate must not fall back to a generic message"
    return reason


# --- partition coverage -----------------------------------------------------


def test_the_matrix_tables_cover_every_selectable_origin_of_the_t132_partition():
    """L04 moves one source-backed origin from profile to selectable:
    55 origins over 54 canonical rules; the 95 equipment origins are unchanged.
    """
    with REGISTER.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    t132 = [row for row in rows if "T13.2" in json.loads(row["lots"] or "[]")]
    selectable: set[tuple[str, str]] = set()
    selectable_origins = 0
    equipment = 0
    for row in t132:
        if row["family"] == "item":
            equipment += 1
            continue
        if row["family"] != "band-rule":
            continue
        document = yaml.safe_load((ROOT / row["canonical_file"]).read_text(encoding="utf-8"))
        node = next((rule for rule in document.get("rules") or () if str(rule.get("id")) == row["canonical_id"]), None)
        assert node is not None, f"{row['canonical_file']} publishes no rule {row['canonical_id']}"
        if (node.get("runtime") or {}).get("grant") == "selectable":
            selectable.add((Path(row["canonical_file"]).parent.name, row["canonical_id"]))
            selectable_origins += 1
    assert (selectable_origins, len(selectable), equipment) == (55, 54, 95)
    tabled = {(band_id, rule_id) for band_id, _, rule_id in IMPLEMENTED}
    tabled |= {(band_id, rule_id) for band_id, _, rule_id in PENDING}
    tabled |= {(band_id, rule_id) for band_id, _, rule_id in PENDING_WITHOUT_AVAILABILITY_CHANNEL}
    assert tabled == selectable, (
        "the test tables must cover exactly the partition; missing: "
        f"{sorted(selectable - tabled)}; unexpected: {sorted(tabled - selectable)}"
    )


# --- availability and recipients -------------------------------------------


def test_available_special_rules_offers_each_selectable_rule_to_its_recipients():
    assert _rule("clan-angrund-kep", "band--dwarf-special-skills-master-of-blades").get("runtime", {}).get("grant") == "selectable"
    dwarf_noble = set(available_special_rules(build("clan-angrund-kep", "dwarf-noble"), None))
    assert {
        "band--dwarf-special-skills-master-of-blades",
        "band--dwarf-special-skills-true-grit",
        "band--dwarf-special-skills-thick-skull",
    } <= dwarf_noble
    # Slayer-only rules name their recipient; the ordinary noble is not offered
    # them even though the same band publishes them.
    assert {
        "band--slayer-special-skills-berserker",
        "band--slayer-special-skills-ferocious-charge",
        "band--slayer-special-skills-monster-slayer",
    }.isdisjoint(dwarf_noble)
    slayer = set(available_special_rules(build("clan-angrund-kep", "dwarf-troll-slayers"), None))
    assert {
        "band--slayer-special-skills-berserker",
        "band--slayer-special-skills-ferocious-charge",
        "band--slayer-special-skills-monster-slayer",
    } <= slayer
    saurus = set(available_special_rules(build("lizardmen-lus", "saurus-totem-warriors"), None))
    assert "band--lizardmen-special-skills-saurus-only-bellowing-battle-roar" in saurus


@pytest.mark.parametrize("band_id,profile_id,rule_id", PENDING)
def test_pending_selectable_origins_refuse_with_their_published_source_reason(band_id, profile_id, rule_id):
    # The rule is visible for selection (available_special_rules offers it) but
    # the executable runtime gate must refuse it with the KB reason, never with
    # a generic message.
    assert rule_id in available_special_rules(build(band_id, profile_id), None), (
        "a pending selectable rule must stay visible for selection"
    )
    with pytest.raises(ValueError) as excinfo:
        compile_fighter(build(band_id, profile_id, special_rule_ids=(rule_id,)))
    message = str(excinfo.value)
    assert message.startswith(f"special rule is outside the executable duel runtime: {rule_id}: ")
    assert _runtime_reason(band_id, rule_id) in message


@pytest.mark.parametrize("band_id,profile_id,rule_id", PENDING_WITHOUT_AVAILABILITY_CHANNEL)
def test_pending_selectable_origins_without_channel_still_refuse_with_their_source_reason(band_id, profile_id, rule_id):
    # Only the runtime gate is asserted here: the current warband-skill API
    # omits the rule, so claiming ``available_special_rules`` shows it would be
    # false.  The missing channel is a recorded discrepancy, not a test fixture.
    with pytest.raises(ValueError) as excinfo:
        compile_fighter(build(band_id, profile_id, special_rule_ids=(rule_id,)))
    message = str(excinfo.value)
    assert message.startswith(f"special rule is outside the executable duel runtime: {rule_id}: ")
    assert _runtime_reason(band_id, rule_id) in message


# --- implemented selectable rules ------------------------------------------


def test_hardy_constitution_grants_poison_immunity_and_refuses_non_recipients():
    control = compile_fighter(build("grave-robbers-sylv", "graver"))
    selected = compile_fighter(build(
        "grave-robbers-sylv", "graver",
        special_rule_ids=("band--special-skill-hardy-constitution",),
    ))
    assert control.global_effects.poison_immunity is False
    assert selected.global_effects.poison_immunity is True
    assert "poison_immune" in selected.global_effects.tags
    with pytest.raises(ValueError, match="special rule is not available to grave-robbers-sylv/thugs"):
        compile_fighter(build(
            "grave-robbers-sylv", "thugs",
            special_rule_ids=("band--special-skill-hardy-constitution",),
        ))


def test_master_of_blades_projects_both_shared_mechanics_and_the_parry_variant():
    fighter = compile_fighter(build(
        "clan-angrund-kep", "dwarf-noble",
        special_rule_ids=("band--dwarf-special-skills-master-of-blades",),
    ))
    # One canonical rule, two registered origins/bindings and the reviewed dwarf parry
    # variant; no mechanics from the other Dwarf special skills leak in.
    assert {"skill.unbeatable-warrior", "skill.sword-master", "rule.dwarf-axe-parry-reroll"} <= set(fighter.global_effects.tags)


def test_automatic_band_grants_are_not_doubled_by_the_selectable_copy():
    # clan-angrund-kep grants Hard to Kill and concussion immunity band-wide; the
    # selectable True Grit and Thick Skull copies bind the same mechanics, so the
    # compiled global effects must be identical with and without them.
    for rule_id in ("band--dwarf-special-skills-true-grit", "band--dwarf-special-skills-thick-skull"):
        control = compile_fighter(build("clan-angrund-kep", "dwarf-noble"))
        selected = compile_fighter(build("clan-angrund-kep", "dwarf-noble", special_rule_ids=(rule_id,)))
        assert selected.global_effects == control.global_effects, rule_id
    assert compile_fighter(build("clan-angrund-kep", "dwarf-noble")).global_effects.out_of_action_threshold == 6
    assert "concussion_immune" in compile_fighter(build("clan-angrund-kep", "dwarf-noble")).global_effects.tags


@pytest.mark.parametrize("rule_id,tag", [
    ("band--slayer-special-skills-ferocious-charge", "skill.ferocious-charge"),
    ("band--slayer-special-skills-monster-slayer", "skill.monster-slayer"),
    ("band--slayer-special-skills-berserker", "skill.berserker"),
])
def test_slayer_skills_reach_the_slayer_and_refuse_the_other_records(rule_id, tag):
    selected = compile_fighter(build(
        "clan-angrund-kep", "dwarf-troll-slayers", special_rule_ids=(rule_id,),
    ))
    assert tag in selected.global_effects.tags
    with pytest.raises(ValueError, match=f"special rule is not available to clan-angrund-kep/dwarf-noble: {rule_id}"):
        compile_fighter(build("clan-angrund-kep", "dwarf-noble", special_rule_ids=(rule_id,)))
    with pytest.raises(ValueError, match=f"special rule is not available to clan-angrund-kep/ironbreaker: {rule_id}"):
        compile_fighter(build("clan-angrund-kep", "ironbreaker", special_rule_ids=(rule_id,)))


def test_bellowing_battle_roar_reaches_saurus_and_refuses_skinks():
    selected = compile_fighter(build(
        "lizardmen-lus", "saurus-totem-warriors",
        special_rule_ids=("band--lizardmen-special-skills-saurus-only-bellowing-battle-roar",),
    ))
    assert "skill.bellowing-battle-roar" in selected.global_effects.tags
    with pytest.raises(ValueError, match="special rule is not available to lizardmen-lus/skink-great-crests"):
        compile_fighter(build(
            "lizardmen-lus", "skink-great-crests",
            special_rule_ids=("band--lizardmen-special-skills-saurus-only-bellowing-battle-roar",),
        ))


def test_vomit_attack_is_selectable_only_for_the_warpstone_troll():
    # The selected rule supplies a separate optional attack. The normal hand
    # remains equipped until the modular policy chooses the replacement.
    selected = compile_fighter(build(
        "underworld-alliance-mim", "warpstone-troll",
        special_rule_ids=("warpstone-troll--vomit-attack",),
    ))
    assert selected.fighter_id == "underworld-alliance-mim:warpstone-troll"
    assert selected.vomit_attack is not None
    assert selected.vomit_attack.fixed_strength == 5
    assert "weapon.vomit-attack" not in selected.main_weapon.tags
    with pytest.raises(ValueError, match="special rule is not available to underworld-alliance-mim/goblin-bully"):
        compile_fighter(build(
            "underworld-alliance-mim", "goblin-bully",
            special_rule_ids=("warpstone-troll--vomit-attack",),
        ))


# --- equipment --------------------------------------------------------------


def test_duelling_pistol_is_selectable_in_both_hand_slots_with_its_published_close_combat_profile():
    main = compile_fighter(build(
        "mercenaries", "mercenary-captain", main_weapon_id="weapon.duelling-pistol",
    ))
    assert "weapon.duelling-pistol" in main.main_weapon.tags
    assert main.main_weapon.fixed_strength == 4
    assert main.main_weapon.armour_penetration == 1
    assert main.main_weapon.hit_modifier == 1
    off = compile_fighter(build(
        "mercenaries", "mercenary-captain",
        main_weapon_id="weapon.dagger", off_hand_id="weapon.duelling-pistol",
    ))
    assert off.off_hand is not None and "weapon.duelling-pistol" in off.off_hand.tags
    assert off.off_hand_attacks is True
    # The item is on the Mercenary equipment list; a band that does not publish
    # it must refuse the same mechanic.
    with pytest.raises(ValueError, match="equipment is not available to skaven-clan-pestilens/plague-priest"):
        compile_fighter(build(
            "skaven-clan-pestilens", "plague-priest", main_weapon_id="weapon.duelling-pistol",
        ))


def test_gromril_material_route_prices_the_supported_material_and_refuses_foreign_bands():
    # Keep this Gromril route distinct from L06's source-backed Darksteel Blade:
    # its armour penetration does not certify that item's critical/injury rules.
    dwarf = compile_fighter(build(
        "clan-angrund-kep", "dwarf-noble", main_material_id="material.gromril",
    ))
    assert "material.gromril" in dwarf.main_weapon.tags
    assert dwarf.main_weapon.armour_penetration == 1
    with pytest.raises(ValueError, match="equipment is not available to skaven-clan-pestilens/plague-priest"):
        compile_fighter(build(
            "skaven-clan-pestilens", "plague-priest", main_material_id="material.gromril",
        ))
