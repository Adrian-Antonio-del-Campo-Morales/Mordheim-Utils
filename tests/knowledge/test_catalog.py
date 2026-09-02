"""external.test_catalog: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import COMPILER_CONTRACTS
from mordheim_construction.contracts import PROFILE_RULE_EFFECTS
from mordheim_construction.contracts import SPECIAL_RULE_EFFECTS
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_construction.contracts import validate_execution_contract
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import PROFILE_BINDING_IDS
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_execution_contract
from mordheim_knowledge.loader import load_items
from mordheim_knowledge.loader import load_mechanics
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import load_simulation_mappings
from mordheim_knowledge.loader import load_skills
from mordheim_knowledge.loader import runtime_bindings
from pathlib import Path
import yaml as yaml


ROOT=Path(__file__).resolve().parents[2]/"sources/knowledge"


def profile_build(collection, band_id, profile_id):
    special_rule_ids = (("band--mutations-tentacle",)
                        if band_id in {"cult-of-the-possessed", "trollheim-cult-of-the-possessed"}
                        and profile_id == "mutants"
                        else ("band--blessings-of-nurgle-bloated-foulness",)
                        if band_id == "carnival-of-chaos" and profile_id == "tainted-ones" else ())
    return FighterBuild("mordheim",band_id=band_id,profile_id=profile_id,
                        collection=collection,special_rule_ids=special_rule_ids)


def test_runtime_contains_mordheim_and_trollheim_bands():
    collections={row["id"]:row for row in load_collections(ROOT)}
    assert set(collections)=={"mordheim","trollheim"}
    assert collections["trollheim"]["rulesets"]==["mordheim"]
    assert len(load_bands("mordheim",ROOT))==48
    trollheim=load_bands("trollheim",ROOT)
    assert len(trollheim)==33
    assert all(band.collection=="trollheim" and band.ruleset=="mordheim" for band in trollheim)


def test_trollheim_collection_uses_the_mordheim_combat_ruleset():
    fighter=compile_fighter(FighterBuild(
        "mordheim",band_id="trollheim-mercenaries",profile_id="mercenary-captain",
        collection="trollheim"),ROOT)
    assert fighter.fighter_id=="trollheim-mercenaries:mercenary-captain"


def test_every_trollheim_profile_compiles_under_mordheim_rules():
    compiled=0
    for band in load_bands("trollheim",ROOT):
        for profile in band.profiles:
            compile_fighter(profile_build("trollheim",band.band["id"],profile["id"]),ROOT)
            compiled+=1
    assert compiled==218


def test_collection_and_ruleset_are_independent_and_validated():
    import pytest
    with pytest.raises(ValueError,match="uses ruleset mordheim, not trollheim"):
        compile_fighter(FighterBuild(
            "trollheim",band_id="trollheim-mercenaries",profile_id="mercenary-captain",
            collection="trollheim"),ROOT)
    with pytest.raises(ValueError,match="unknown band collection"):
        load_bands("invented",ROOT)


def test_simple_trollheim_rules_reuse_shared_runtime_traits():
    def compiled(band_id,profile_id):
        return compile_fighter(FighterBuild(
            "mordheim",band_id=band_id,profile_id=profile_id,
            collection="trollheim"),ROOT)
    dire_wolf=compiled("trollheim-undead","dire-wolves")
    assassin=compiled("trollheim-skaven-clan-eshin","assassin-adept")
    zomblintua=compiled("lustria-savage-goblins","zomblintua")
    vulture=compiled("khemri-necromancers","nehekharan-vultures")
    ethereal=compiled("lustria-pygmies","silent-walker")
    assert dire_wolf.global_effects.charge_attacks_bonus==1
    assert assassin.global_effects.armour_penetration==1
    assert zomblintua.global_effects.regeneration_save==5
    assert vulture.injury_profile==3
    assert ethereal.global_effects.ward_save==5


def test_trollheim_innate_armour_profiles_compile_to_shared_natural_saves():
    expected={
        ("khemri-mages","mechanical-beast"):5,
        ("khemri-tomb-guardians","stone-golem"):4,
        ("lustria-dark-elves","cold-ones"):6,
        ("lustria-lizardmen","skink-priest"):6,
        ("lustria-lizardmen","saurus-totem-warrior"):5,
        ("lustria-lizardmen","kroxigor"):4,
        ("lustria-norse","wulfen"):6,
    }
    for (band_id,profile_id),save in expected.items():
        fighter=compile_fighter(FighterBuild(
            "mordheim",band_id=band_id,profile_id=profile_id,
            collection="trollheim"),ROOT)
        assert fighter.natural_armour_save==save


def test_reusable_optional_trollheim_rules_are_bound_but_not_granted():
    expected={
        "band--dwarf-special-skills-true-grit":"skill.tough-as-steel",
        "band--orc-special-skills-eadbasher":"skill.head-crusher",
        "band--lahmia-power-lost-innocence":"skill.always-strikes-first",
        "band--strigoi-power-curse-of-the-reborn":"skill.regeneration",
        "band--lahmian-special-skills-lost-innocence":"skill.always-strikes-first",
        "band--lizardmen-special-skills-hardened-skin":"skill.hard-to-kill",
    }
    found={
        rule["id"]: next((binding["id"] for binding in runtime_bindings(rule, "mechanic")), None)
        for band in load_bands("trollheim",ROOT) for rule in band.special_rules
    }
    assert {rule_id:found.get(rule_id) for rule_id in expected}==expected


def test_profile_special_rules_with_mechanic_ids_are_granted_automatically():
    cases=(
        ("battle-monks-of-cathay", "dragon-monks", "skill.unarmed-critical-strikes"),
        ("gunnery-school-of-nuln", "pistoliers", "skill.crack-shot"),
        ("merchant-caravans", "blackguards", "skill.strongman"),
    )
    for band_id, profile_id, mechanic_id in cases:
        fighter=compile_fighter(FighterBuild("mordheim",band_id=band_id,profile_id=profile_id),ROOT)
        assert mechanic_id in fighter.global_effects.tags


def test_selected_nurgle_blessings_apply_stats_and_traits():
    fighter=compile_fighter(FighterBuild(
        "mordheim",band_id="carnival-of-chaos",profile_id="tainted-ones",
        special_rule_ids=("band--blessings-of-nurgle-bloated-foulness",
                          "band--blessings-of-nurgle-mark-of-nurgle")),ROOT)
    assert fighter.characteristics.toughness==4
    assert fighter.characteristics.wounds==3
    assert fighter.global_effects.poison_immunity


def test_selected_mutation_and_vampiric_powers_compile():
    mutant=compile_fighter(FighterBuild(
        "mordheim",band_id="cult-of-the-possessed",profile_id="mutants",
        special_rule_ids=("band--mutations-tentacle",)),ROOT)
    vampire=compile_fighter(FighterBuild(
        "mordheim",collection="trollheim",band_id="chaos-streets-undead-bloodlines",
        profile_id="strigoi-vampire",
        special_rule_ids=("band--strigoi-power-monstrosity",
                          "band--strigoi-power-iron-sinews",
                          "band--strigoi-power-infinite-hatred")),ROOT)
    assert mutant.global_effects.incoming_attacks_modifier==-1
    assert (vampire.characteristics.wounds,vampire.characteristics.strength)==(3,4)
    assert vampire.global_effects.strength_bonus==1
    assert vampire.global_effects.reroll_hits


def test_new_necromantic_modifications_mutations_and_huge_jaws_compile():
    base_abomination=compile_fighter(FighterBuild(
        "mordheim",collection="trollheim",band_id="khemri-necromancers",
        profile_id="necromantic-abomination"),ROOT)
    modified_abomination=compile_fighter(FighterBuild(
        "mordheim",collection="trollheim",band_id="khemri-necromancers",
        profile_id="necromantic-abomination",special_rule_ids=(
            "band--necromantic-modification-bone-armour",
            "band--necromantic-modification-killers-precision",
            "band--necromantic-modification-enhanced-reflexes")),ROOT)
    assert modified_abomination.characteristics.toughness==base_abomination.characteristics.toughness+1
    assert modified_abomination.characteristics.weapon_skill==base_abomination.characteristics.weapon_skill+1
    assert modified_abomination.characteristics.initiative==base_abomination.characteristics.initiative+1

    for collection,band_id in (("mordheim","cult-of-the-possessed"),
                               ("trollheim","trollheim-cult-of-the-possessed")):
        mutant=compile_fighter(FighterBuild(
            "mordheim",collection=collection,band_id=band_id,profile_id="mutants",
            special_rule_ids=("band--mutations-blackblood" if collection=="mordheim" else
                              "band--mutations-acid-blood",
                              "band--mutations-spines","band--mutations-scorpion-tail")),ROOT)
        assert "acid_blood" in mutant.global_effects.tags
        assert "spines" in mutant.global_effects.tags
        tail=next(attack for attack in mutant.extra_attacks if "rule.scorpion-tail" in attack.tags)
        assert tail.fixed_strength==5

    saurus=compile_fighter(FighterBuild(
        "mordheim",collection="trollheim",band_id="lustria-lizardmen",
        profile_id="saurus-totem-warrior",
        special_rule_ids=("band--sacred-mark-huge-jaws",)),ROOT)
    bite=next(attack for attack in saurus.extra_attacks if "rule.bite-attack" in attack.tags)
    assert bite.strength_bonus==1


def test_special_rule_eligibility_and_unsupported_parts_are_explicit():
    import pytest
    with pytest.raises(ValueError,match="not available"):
        compile_fighter(FighterBuild(
            "mordheim",band_id="carnival-of-chaos",profile_id="brutes",
            special_rule_ids=("band--blessings-of-nurgle-mark-of-nurgle",)),ROOT)
    claw=compile_fighter(FighterBuild(
        "mordheim",band_id="cult-of-the-possessed",profile_id="mutants",
        special_rule_ids=("band--mutations-great-claw",)),ROOT)
    assert len(claw.extra_attacks)==1 and claw.extra_attacks[0].strength_bonus==1


def test_mutant_skill_grants_one_cross_band_mutation_per_selection():
    fighter=compile_fighter(FighterBuild(
        "mordheim",band_id="beastmen-raiders",profile_id="beastmen-chieftain",
        special_rule_ids=("band--beastmen-special-skills-mutant",
                          "band--mutations-tentacle")),ROOT)
    assert fighter.global_effects.incoming_attacks_modifier==-1


def test_profile_special_rules_can_grant_runtime_traits():
    bearer=compile_fighter(FighterBuild("mordheim",band_id="carnival-of-chaos",profile_id="plague-bearers"),ROOT)
    zombie=compile_fighter(FighterBuild("mordheim",band_id="undead",profile_id="zombies"),ROOT)
    liche=compile_fighter(FighterBuild("mordheim",band_id="restless-dead",profile_id="liche"),ROOT)
    bear=compile_fighter(FighterBuild("mordheim",band_id="cursed-cavalcade",profile_id="great-bear"),ROOT)
    totem=compile_fighter(FighterBuild("mordheim",band_id="amazons-mordheim",profile_id="totem-warriors"),ROOT)
    peasant=compile_fighter(FighterBuild("mordheim",band_id="battle-monks-of-cathay",profile_id="raging-peasants"),ROOT)
    snotling=compile_fighter(FighterBuild("mordheim",band_id="night-goblins-web",profile_id="snotlings"),ROOT)
    fanatic=compile_fighter(FighterBuild("mordheim",band_id="night-goblins-mic",profile_id="fanatics"),ROOT)
    warhound=compile_fighter(FighterBuild("mordheim",band_id="lustrian-reavers",profile_id="estalian-warhound"),ROOT)
    monk=compile_fighter(FighterBuild("mordheim",band_id="battle-monks-of-cathay",profile_id="warrior-monks"),ROOT)
    scorpion=compile_fighter(FighterBuild("mordheim",band_id="khemri-tomb-guardians",profile_id="tomb-scorpions",collection="trollheim"),ROOT)
    mordheim_scorpion=compile_fighter(FighterBuild("mordheim",band_id="tomb-guardians",profile_id="tomb-scorpions"),ROOT)
    zomblintua=compile_fighter(FighterBuild("mordheim",band_id="lustria-savage-goblins",profile_id="zomblintua",collection="trollheim"),ROOT)
    halfling=compile_fighter(FighterBuild("mordheim",band_id="mootlanders",profile_id="warriors"),ROOT)
    tilean_duelist=compile_fighter(FighterBuild("mordheim",band_id="lustria-tileans",profile_id="duelists",collection="trollheim"),ROOT)
    tomb_lord=compile_fighter(FighterBuild("mordheim",band_id="tomb-guardians",profile_id="tomb-lord"),ROOT)
    scarecrow=compile_fighter(FighterBuild("mordheim",band_id="restless-dead",profile_id="scarecrows"),ROOT)
    knife=compile_fighter(FighterBuild("mordheim",band_id="chaos-streets-deathbringers",profile_id="knives",collection="trollheim"),ROOT)
    spirit=compile_fighter(FighterBuild("mordheim",band_id="khemri-lahmian-brotherhood",profile_id="spirits",collection="trollheim"),ROOT)
    monkey=compile_fighter(FighterBuild("mordheim",band_id="lustrian-reavers",profile_id="barbary-monkey"),ROOT)
    ranger=compile_fighter(FighterBuild("mordheim",band_id="dwarf-rangers",profile_id="dwarf-clansmen"),ROOT)
    assert bearer.global_effects.poison_immunity
    assert "cloud_of_flies" in bearer.global_effects.tags
    assert zombie.global_effects.poison_immunity
    assert "skill.ignore-pain" in liche.global_effects.tags
    assert "maddened_with_pain" in bear.global_effects.tags
    assert totem.global_effects.frenzy
    assert peasant.injury_profile==2
    assert snotling.injury_profile==1
    assert fanatic.global_effects.frenzy
    assert warhound.natural_armour_save==5
    assert "skill.unarmed-fighting" in monk.global_effects.tags
    assert "poison.black-lotus" in scorpion.main_weapon.tags
    assert "poison.black-lotus" in mordheim_scorpion.main_weapon.tags
    assert zomblintua.main_weapon.concussion
    assert "fragile_halflings" in halfling.global_effects.tags
    assert tilean_duelist.armour_save==6
    assert "flammable" in tomb_lord.global_effects.tags
    assert {"flammable","injury_reroll_out"} <= set(scarecrow.global_effects.tags)
    assert "dagger_master" in knife.global_effects.tags
    assert "spiritual_weapons" in spirit.global_effects.tags
    assert monkey.global_effects.ward_save==5
    assert "concussion_immune" in ranger.global_effects.tags


def test_every_catalogue_mechanic_has_an_executable_definition():
    assert validate_execution_contract("mordheim",ROOT)==[]
    catalog=load_mechanics("mordheim",ROOT); execution=load_execution_contract("mordheim",ROOT)
    ids={row["id"] for key in ("weapons","armours","defences","materials","preparations","poisons","skills") for row in catalog[key]}
    assert ids=={row["id"] for row in execution["mechanics"]}
    assert all(row["handler"]=="effect-set" for row in execution["mechanics"])
    assert all(row["parameters"] for row in execution["mechanics"])
    assert all("target" not in row for row in execution["mechanics"])
    assert all(row["application"] == ("attack" if row["trigger"] == "attack" else "fighter") for row in execution["mechanics"])


def test_execution_metadata_controls_effect_context_and_stacking():
    from mordheim_core.effects import ExecutionEffect
    from mordheim_core.effects import apply_execution_effects
    from mordheim_core.models import EffectSet
    effects={
        "passive": ExecutionEffect(EffectSet(strength_bonus=1), "passive", "fighter", "stack"),
        "attack": ExecutionEffect(EffectSet(strength_bonus=2), "attack", "attack", "stack"),
        "once": ExecutionEffect(EffectSet(strength_bonus=3), "attack", "attack", "once"),
        "best": ExecutionEffect(EffectSet(strength_bonus=4), "attack", "attack", "best"),
    }
    assert apply_execution_effects(EffectSet(), effects, effects, "passive", "fighter").strength_bonus == 1
    assert apply_execution_effects(EffectSet(), ("attack", "once", "once", "best"), effects, "attack", "attack").strength_bonus == 5


def test_all_fixed_profiles_compile_with_stable_ids():
    compiled=0
    for band in load_bands("mordheim",ROOT):
        for profile in band.profiles:
            c=profile.get("characteristics") or {}
            if all(isinstance(c.get(key),int) for key in ("WS","S","T","W","I","A")):
                fighter=compile_fighter(profile_build("mordheim",band.band["id"],profile["id"]),ROOT)
                assert fighter.fighter_id.endswith(profile["id"]);compiled+=1
    assert compiled==313


def test_profile_combat_traits_reference_mechanics_by_id():
    for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT)):
        for profile in band.profiles:
            for skill_id in (profile.get("combat_traits") or {}).get("starting_skills") or ():
                assert skill_id.startswith("skill.")


def test_trollheim_package_and_item_references_are_closed():
    item_ids=set()
    for path in (ROOT/"catalog/items").glob("*.yaml"):
        item_ids.update(row["id"] for row in yaml.safe_load(path.read_text(encoding="utf-8")).get("items") or ())
    mechanics=load_mechanics("mordheim",ROOT)
    mechanic_ids={row["id"] for family in ("weapons","armours","defences","materials","preparations","poisons","skills") for row in mechanics[family]}
    for band in load_bands("trollheim",ROOT):
        profile_ids={profile["id"] for profile in band.profiles}
        roster_ids={member["profile_id"] for member in band.band["roster"]["members"]}
        summoned_ids={profile["id"] for profile in band.profiles if profile.get("type")=="summoned"}
        assert roster_ids==profile_ids-summoned_ids
        rule_ids={rule["id"] for rule in band.special_rules}
        assert set(band.band["rule_ids"])<=rule_ids
        for profile in band.profiles:
            assert set(profile.get("rule_ids") or ())<=rule_ids
        for equipment_list in band.equipment_lists:
            assert {item["item_id"] for item in equipment_list.get("items") or ()}<=item_ids
        for rule in band.special_rules:
            for binding in runtime_bindings(rule, "mechanic"):
                assert binding["id"] in mechanic_ids


def test_special_rule_runtime_metadata_is_canonical_and_binary():
    legacy={"mechanic_id","runtime_grant","runtime_band_grant","runtime_traits"}
    classified=0
    for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT)):
        for rule in band.special_rules:
            assert not legacy.intersection(rule)
            runtime=rule.get("runtime")
            if runtime is None:
                continue
            classified+=1
            assert runtime["implemented"] in {"YES","NO"}
            assert runtime["scope"] in {"YES","NO","LATER"}
    assert classified==1537


def test_every_selectable_rule_has_an_explicit_selection_kind():
    expected={
        "warband_skill", "mutation", "blessing", "virtue", "mark",
        "modification", "profile_ability", "warband_variant",
    }
    selectable=[]
    for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT)):
        selectable.extend(
            rule for rule in band.special_rules
            if (rule.get("runtime") or {}).get("grant")=="selectable"
        )
    # Innate rules can be reclassified as automatic when the written source
    # requires it; this test validates selection kinds, not an obsolete count.
    assert selectable
    assert {rule.get("kind") for rule in selectable}==expected
    assert sum(rule["kind"]=="warband_skill" for rule in selectable)==305


def test_equivalent_no_pain_rules_share_one_runtime_mechanic():
    bindings=[]
    for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT)):
        for rule in band.special_rules:
            if rule.get("name") == "No Pain":
                bindings.extend(binding["id"] for binding in runtime_bindings(rule,"mechanic"))
    assert len(bindings)>=10
    assert set(bindings)=={"skill.ignore-pain"}


def test_every_runtime_binding_resolves_to_a_known_shared_contract():
    mechanics=load_mechanics("mordheim",ROOT)
    mechanic_ids={row["id"] for family in ("weapons","armours","defences","materials","preparations","poisons","skills") for row in mechanics[family]}
    compiler_ids=set()
    for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT)):
        for rule in band.special_rules:
            for binding in runtime_bindings(rule):
                if binding["kind"]=="mechanic":
                    assert binding["id"] in mechanic_ids
                elif binding["kind"]=="trait":
                    assert binding["id"].removeprefix("trait.").replace("-","_") in TRAIT_TYPES
                elif binding["kind"]=="profile":
                    assert binding["id"] in PROFILE_BINDING_IDS
                else:
                    compiler_ids.add(binding["id"])
                    prefix,rule_id=binding["id"].split(".",1)
                    assert (binding["id"] in COMPILER_CONTRACTS
                            or rule_id in (PROFILE_RULE_EFFECTS if prefix=="profile-rule" else SPECIAL_RULE_EFFECTS))
    assert compiler_ids


def test_first_500_previously_unclassified_rules_have_runtime_metadata():
    first=next(band for band in load_bands("mordheim",ROOT) if band.band["id"]=="amazons-lustria")
    last=next(band for band in load_bands("mordheim",ROOT) if band.band["id"]=="night-goblins-web")
    assert next(rule for rule in first.special_rules if rule["id"]=="serpent-priestess--leader")["runtime"]["scope"]=="LATER"
    assert next(rule for rule in last.special_rules if rule["id"]=="band--fear-elves")["runtime"]["scope"]=="LATER"
    assert next(rule for rule in last.special_rules if rule["id"]=="band--distasteful-company")["runtime"]["scope"]=="NO"


def test_second_500_previously_unclassified_rules_have_runtime_metadata():
    first=next(band for band in load_bands("mordheim",ROOT) if band.band["id"]=="night-goblins-web")
    last=next(band for band in load_bands("trollheim",ROOT) if band.band["id"]=="khemri-lahmian-brotherhood")
    assert next(rule for rule in first.special_rules if rule["id"]=="band--distasteful-company")["runtime"]["scope"]=="NO"
    assert next(rule for rule in last.special_rules if rule["id"]=="jackals--pack")["runtime"]["scope"]=="NO"
    assert next(rule for rule in last.special_rules if rule["id"]=="jackals--animal")["runtime"]["scope"]=="NO"


def test_every_special_rule_is_now_classified():
    pending=[]
    for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT)):
        pending.extend(f"{band.band['id']}/{rule['id']}" for rule in band.special_rules if "runtime" not in rule)
    assert pending==[]


def test_body_slam_canonical_binding_is_now_executable():
    bands={band.band["id"]:band for band in (*load_bands("mordheim",ROOT),*load_bands("trollheim",ROOT))}
    rule=next(rule for rule in bands["pit-fighters"].special_rules if rule["id"]=="band--pit-fighter-skill-body-slam")
    assert rule["runtime"]["implemented"]=="YES"
    assert {binding["id"] for binding in runtime_bindings(rule)}=={"mechanic.body-slam"}


def test_final_batch_profile_backed_rules_have_explicit_contracts():
    expected={
        ("khemri-necromancers","nehekharan-vultures--fragile"):{"trait.injury-profile"},
        ("lustria-lizardmen","kroxigor--scaly-skin-4plus"):{
            "trait.natural-armour-save","trait.natural-armour-stacks","trait.natural-armour-worst-save"},
        ("lustria-pygmies","silent-walker--ethereal"):{"trait.ward-save","trait.ward-save-mundane-only"},
        ("trollheim-skaven-clan-eshin","assassin-adept--consummate-fighter"):{"trait.perfect-killer"},
        ("trollheim-undead","dire-wolves--charge"):{"trait.charge-attack-bonus"},
        ("trollheim-mercenaries","band--middenheim-physical-prowess"):{"profile.characteristics"},
    }
    bands={band.band["id"]:band for band in load_bands("trollheim",ROOT)}
    for (band_id,rule_id),binding_ids in expected.items():
        rule=next(rule for rule in bands[band_id].special_rules if rule["id"]==rule_id)
        assert rule["runtime"]["implemented"]=="YES"
        assert {binding["id"] for binding in runtime_bindings(rule)}==binding_ids


def test_revision_specific_defences_and_regeneration_compile_with_their_conditions():
    ethereal=compile_fighter(FighterBuild(
        "mordheim",band_id="lustria-pygmies",profile_id="silent-walker",collection="trollheim"),ROOT)
    daemon=compile_fighter(FighterBuild(
        "mordheim",band_id="carnival-of-chaos",profile_id="plague-bearers"),ROOT)
    zomblintua=compile_fighter(FighterBuild(
        "mordheim",band_id="lustria-savage-goblins",profile_id="zomblintua",collection="trollheim"),ROOT)
    assert ethereal.global_effects.ward_save==5 and ethereal.global_effects.ward_save_mundane_only
    assert daemon.global_effects.natural_armour_negated_by_magic
    assert "attack.magical" in daemon.global_effects.tags
    assert zomblintua.global_effects.regeneration_save==5
    assert zomblintua.global_effects.regeneration_blocked_by_fire


def test_normalized_compiler_families_keep_their_parameters():
    bands={
        band.band["id"]:band
        for collection in ("mordheim","trollheim")
        for band in load_bands(collection,ROOT)
    }
    cases={
        ("ostlanders","ogre--skills"):("compiler.promoted-hero-skill-access",["combat","strength"]),
        ("pit-fighters","ogre-pit-fighter--skills"):("compiler.promoted-hero-skill-access",["combat","strength","special"]),
        ("battle-monks-of-cathay","band--distaste-for-poison"):("compiler.forbid-item-categories",["poison"]),
        ("lustria-high-elves","band--honourable"):("compiler.forbid-item-categories",["poison","drug"]),
    }
    for (band_id,rule_id),(canonical,parameters) in cases.items():
        rule=next(rule for rule in bands[band_id].special_rules if rule["id"]==rule_id)
        binding=runtime_bindings(rule,"compiler")[0]
        assert binding["id"]==canonical
        assert list((binding.get("parameters") or {}).values())[0]==parameters


def test_second_batch_common_rules_use_shared_runtime_bindings():
    expected={
        ("mordheim","orc-mob","troll--regeneration"):("mechanic","skill.regeneration"),
        ("mordheim","skaven-clan-eshin","assassin-adept--perfect-killer"):("trait","trait.perfect-killer"),
        ("mordheim","undead","dire-wolves--charge"):("trait","trait.charge-attack-bonus"),
        ("trollheim","chaos-streets-undead-bloodlines","vampire-bat--summoned-creature"):("trait","trait.injury-profile"),
    }
    collections={name:{band.band["id"]:band for band in load_bands(name,ROOT)} for name in ("mordheim","trollheim")}
    for (collection,band_id,rule_id),binding_expected in expected.items():
        rule=next(rule for rule in collections[collection][band_id].special_rules if rule["id"]==rule_id)
        binding=next(iter(runtime_bindings(rule)))
        assert (binding["kind"],binding["id"])==binding_expected


def test_semantically_equivalent_rules_reuse_executable_contracts():
    blood_dragon=compile_fighter(FighterBuild(
        "mordheim",band_id="chaos-streets-undead-bloodlines",profile_id="blood-dragon-vampire",
        collection="trollheim",special_rule_ids=("band--blood-dragon-power-sword-master",)),ROOT)
    abomination=compile_fighter(FighterBuild(
        "mordheim",band_id="khemri-necromancers",profile_id="necromantic-abomination",
        collection="trollheim",special_rule_ids=(
            "band--necromantic-modification-ogre-flesh",
            "band--necromantic-modification-tremendous-strength",
        )),ROOT)
    beastman=compile_fighter(FighterBuild(
        "mordheim",band_id="beastmen-raiders",profile_id="beastmen-chieftain",
        special_rule_ids=("band--beastmen-special-skills-shaggy-hide",)),ROOT)
    black_orc=compile_fighter(FighterBuild(
        "mordheim",band_id="black-orcs",profile_id="black-orc-boss",
        special_rule_ids=("band--black-orc-special-skills-ard-ead",)),ROOT)
    knight=compile_fighter(FighterBuild(
        "mordheim",band_id="bretonnian-chapel-guard",profile_id="questing-knight",
        main_weapon_id="weapon.flail",special_rule_ids=("band--bulging-muscles",)),ROOT)
    pestilens=compile_fighter(FighterBuild(
        "mordheim",band_id="skaven-clan-pestilens",profile_id="plague-priest",
        special_rule_ids=("band--clan-pestilens-special-skills-rotten-body",)),ROOT)

    assert "skill.sword-master" in blood_dragon.global_effects.tags
    assert "skill.monstrous" in abomination.global_effects.tags
    assert abomination.global_effects.strength_bonus==1
    assert beastman.natural_armour_save==6
    assert black_orc.global_effects.thick_skull
    assert "mechanic.retain-flail-morning-star-strength-bonus" in knight.global_effects.tags
    assert pestilens.global_effects.poison_immunity


def test_black_dwarf_hard_to_kill_excludes_informers():
    dwarf=compile_fighter(FighterBuild("mordheim",band_id="black-dwarfs",profile_id="sorcerer"),ROOT)
    informer=compile_fighter(FighterBuild("mordheim",band_id="black-dwarfs",profile_id="informers"),ROOT)
    assert "skill.hard-to-kill" in dwarf.global_effects.tags
    assert "skill.hard-to-kill" not in informer.global_effects.tags


def test_powerful_build_variants_share_strength_skill_access():
    builds=(
        FighterBuild("mordheim",band_id="dark-elves",profile_id="high-born",
                     skill_ids=("skill.mighty-blow",),special_rule_ids=("band--dark-elf-special-skills-powerful-build",)),
        FighterBuild("mordheim",band_id="shadow-warriors",profile_id="shadow-master",
                     skill_ids=("skill.mighty-blow",),special_rule_ids=("band--shadow-warrior-special-skills-powerful-build",)),
        FighterBuild("mordheim",band_id="lustria-dark-elves",profile_id="dark-prince",collection="trollheim",
                     skill_ids=("skill.mighty-blow",),special_rule_ids=("band--dark-elf-special-skills-strong-constitution",)),
        FighterBuild("mordheim",band_id="chaos-streets-sons-of-nagarythe",profile_id="shadow-master",collection="trollheim",
                     skill_ids=("skill.mighty-blow",),special_rule_ids=("band--shadow-warrior-special-skills-powerful-build",)),
    )
    assert all(compile_fighter(build,ROOT).global_effects.strength_bonus==1 for build in builds)


def test_wight_blades_rule_uses_the_existing_profile_trait():
    grave_guard=compile_fighter(FighterBuild(
        "mordheim",band_id="restless-dead",profile_id="grave-guards"),ROOT)
    assert "wight_blades" in grave_guard.global_effects.tags


def test_biggest_boss_rule_uses_existing_strength_access_profile_contract():
    boss=compile_fighter(FighterBuild(
        "mordheim",band_id="night-goblins-web",profile_id="boss",
        skill_ids=("skill.mighty-blow",)),ROOT)
    assert boss.global_effects.strength_bonus==1


def test_middenheim_variants_share_the_characteristic_contract():
    mordheim=compile_fighter(FighterBuild(
        "mordheim",band_id="mercenaries",profile_id="mercenary-captain",
        special_rule_ids=("band--middenheim-physical-prowess",)),ROOT)
    trollheim=compile_fighter(FighterBuild(
        "mordheim",band_id="trollheim-mercenaries",profile_id="champions",collection="trollheim",
        special_rule_ids=("band--middenheim-physical-prowess",)),ROOT)
    reikland=compile_fighter(FighterBuild(
        "mordheim",band_id="mercenaries",profile_id="mercenary-captain"),ROOT)
    assert mordheim.characteristics.strength==4
    assert trollheim.characteristics.strength==4
    assert reikland.characteristics.strength==3


def test_new_shared_bindings_replace_profile_trait_duplicates():
    ranger=compile_fighter(FighterBuild("mordheim",band_id="dwarf-rangers",profile_id="dwarf-clansmen"),ROOT)
    troll=compile_fighter(FighterBuild("mordheim",band_id="night-goblins-web",profile_id="troll"),ROOT)
    snotling=compile_fighter(FighterBuild("mordheim",band_id="night-goblins-web",profile_id="snotlings"),ROOT)
    halfling=compile_fighter(FighterBuild("mordheim",band_id="mootlanders",profile_id="warriors"),ROOT)
    assert "skill.hard-to-kill" in ranger.global_effects.tags
    assert troll.global_effects.regeneration_save==4
    assert "cloud_of_flies" in snotling.global_effects.tags
    assert "fragile_halflings" in halfling.global_effects.tags


def test_every_catalogue_item_has_a_resolved_simulation_mapping():
    item_ids={row["id"] for row in load_items("mordheim",ROOT)}
    mappings=load_simulation_mappings("mordheim",ROOT)["item_mappings"]
    assert {row["item_id"] for row in mappings}==item_ids
    assert {row["status"] for row in mappings}<={"implemented","out_of_scope"}
    implemented=[row for row in mappings if row["status"]=="implemented"]
    assert all(row.get("engine_option") for row in implemented)
    by_item={row["item_id"]:row for row in mappings}
    assert by_item["blood_root"]["mechanic_id"]=="poison.bloodroot"
    assert by_item["long_boathook"]["mechanic_id"]=="weapon.long-boat-hook"
    assert by_item["mage_robes"]["mechanic_id"]=="armour.wizard-s-robe"


def test_derived_trollheim_item_mappings_feed_profile_equipment_access():
    pirate=compile_fighter(FighterBuild(
        "mordheim",band_id="lustria-pirates",profile_id="pirate-captain",
        collection="trollheim",main_weapon_id="weapon.long-boat-hook"),ROOT)
    mage=compile_fighter(FighterBuild(
        "mordheim",band_id="khemri-mages",profile_id="archmage",
        collection="trollheim",armour_id="armour.wizard-s-robe"),ROOT)
    assert "weapon.long-boat-hook" in pirate.main_weapon.tags
    assert mage.armour_save==6


def test_compiler_rejects_names_and_illegal_hands():
    import pytest
    from mordheim_core.models import Characteristics
    c=Characteristics(3,3,3,1,3,1)
    with pytest.raises(KeyError):compile_fighter(FighterBuild("mordheim",c,main_weapon_id="Sword"),ROOT)
    with pytest.raises(ValueError):compile_fighter(FighterBuild("mordheim",c,main_weapon_id="weapon.flail",off_hand_id="weapon.dagger"),ROOT)
    with pytest.raises(ValueError):compile_fighter(FighterBuild("mordheim",c,defence_ids=("defence.shield",)),ROOT)


def test_representative_effects_compile_in_every_mechanic_family():
    from mordheim_core.models import Characteristics
    c=Characteristics(3,3,3,1,3,1)
    weapon=compile_fighter(FighterBuild("mordheim",c,main_weapon_id="weapon.draich"),ROOT)
    assert weapon.main_weapon.strength_bonus==2 and weapon.main_weapon.parry and weapon.main_weapon.concussion
    material=compile_fighter(FighterBuild("mordheim",c,main_material_id="material.gromril"),ROOT)
    assert material.main_weapon.armour_penetration==1
    poison=compile_fighter(FighterBuild("mordheim",c,main_poison_id="poison.bloodroot"),ROOT)
    assert poison.main_weapon.damage==2
    manbane=compile_fighter(FighterBuild("mordheim",c,main_poison_id="poison.manbane"),ROOT)
    assert manbane.main_weapon.wound_modifier==1
    prepared=compile_fighter(FighterBuild("mordheim",c,preparation_ids=("preparation.mandrake-root",)),ROOT)
    assert prepared.global_effects.toughness_bonus==1
    skilled=compile_fighter(FighterBuild("mordheim",c,skill_ids=("skill.regeneration",)),ROOT)
    assert skilled.global_effects.regeneration_save==4
    expert=compile_fighter(FighterBuild("mordheim",c,skill_ids=("skill.expert-fighter",)),ROOT)
    assert expert.global_effects.wound_modifier==1
    defended=compile_fighter(FighterBuild("mordheim",c,off_hand_id="defence.kite-shield"),ROOT)
    assert defended.armour_save==5


def test_every_catalogued_mechanic_can_be_compiled_in_its_legal_slot():
    from mordheim_core.models import Characteristics
    c=Characteristics(3,3,3,1,3,1);catalog=load_mechanics("mordheim",ROOT)
    exclusions={row["id"] for row in load_runtime_scope("mordheim",ROOT).get("mechanic_exclusions") or ()}
    for row in catalog["weapons"]:
        if row["id"] in exclusions:
            continue
        if row.get("main_hand"):
            compile_fighter(FighterBuild("mordheim",c,main_weapon_id=row["id"]),ROOT)
        elif row.get("off_hand"):
            compile_fighter(FighterBuild("mordheim",c,off_hand_id=row["id"]),ROOT)
    for row in catalog["armours"]:
        if row["id"] in exclusions:
            continue
        kwargs=(
            {"defence_ids": (row["id"],)}
            if row["id"] == "armour.cathayan-quilted-silk"
            else {"armour_id": row["id"]}
        )
        compile_fighter(FighterBuild("mordheim",c,**kwargs),ROOT)
    for row in catalog["defences"]:
        kwargs={"off_hand_id":row["id"]} if row["id"] in {"defence.shield","defence.buckler","defence.kite-shield"} else {"defence_ids":(row["id"],)}
        compile_fighter(FighterBuild("mordheim",c,**kwargs),ROOT)
    for row in catalog["materials"]:compile_fighter(FighterBuild("mordheim",c,main_material_id=row["id"]),ROOT)
    for row in catalog["preparations"]:compile_fighter(FighterBuild("mordheim",c,preparation_ids=(row["id"],)),ROOT)
    for row in catalog["poisons"]:compile_fighter(FighterBuild("mordheim",c,main_poison_id=row["id"]),ROOT)
    for row in catalog["skills"]:
        if row["id"] not in exclusions:compile_fighter(FighterBuild("mordheim",c,skill_ids=(row["id"],)),ROOT)


def test_all_profiles_are_compilable_or_explicitly_outside_duel_scope():
    from mordheim_knowledge.loader import load_runtime_scope
    exclusions={(row["band_id"],row["profile_id"]) for row in load_runtime_scope("mordheim",ROOT)["profile_exclusions"]}
    compiled=0
    for band in load_bands("mordheim",ROOT):
        for profile in band.profiles:
            key=(band.band["id"],profile["id"])
            if key in exclusions:continue
            compile_fighter(profile_build("mordheim",key[0],key[1]),ROOT);compiled+=1
    assert compiled==316 and len(exclusions)==0


def test_fixed_equipment_and_natural_attacks_are_applied_by_profile():
    kroxigor=compile_fighter(FighterBuild("mordheim",band_id="lizardmen",profile_id="kroxigor"),ROOT)
    wolf=compile_fighter(FighterBuild("mordheim",band_id="witch-hunters",profile_id="war-hounds"),ROOT)
    assert "weapon.halberd" in kroxigor.main_weapon.tags
    assert "weapon.natural-attacks" in wolf.main_weapon.tags


def test_profile_access_and_runtime_scope_are_enforced():
    import pytest
    from mordheim_core.models import Characteristics
    with pytest.raises(ValueError,match="not available"):
        compile_fighter(FighterBuild("mordheim",band_id="witch-hunters",profile_id="war-hounds",main_weapon_id="weapon.sword"),ROOT)
    troll=compile_fighter(FighterBuild("mordheim",band_id="orc-mob",profile_id="troll",main_weapon_id="weapon.vomit-attack"),ROOT)
    assert troll.main_weapon.automatic_hit and troll.main_weapon.fixed_strength==5 and troll.main_weapon.ignore_armour
    with pytest.raises(ValueError,match="outside the one-against-one runtime"):
        compile_fighter(FighterBuild("mordheim",Characteristics(3,3,3,1,3,1),skill_ids=("skill.combat-master",)),ROOT)
    with pytest.raises((ValueError,TypeError),match="combat trait"):
        compile_fighter(FighterBuild("mordheim",Characteristics(3,3,3,1,3,1),trait_overrides={"invented_trait":True}),ROOT)


def test_out_of_scope_general_skills_have_explicit_non_implementation_metadata():
    excluded={row["id"] for row in load_runtime_scope("mordheim",ROOT).get("mechanic_exclusions") or ()}
    skills={row["id"]:row for row in load_skills("mordheim",ROOT)}
    added={skill_id for skill_id in excluded if skill_id in skills and (skills[skill_id].get("runtime") or {}).get("scope")=="NO"}
    assert len(added)>=23
    for skill_id in added:
        runtime=skills[skill_id]["runtime"]
        assert runtime["implemented"]=="NO"
        assert runtime["grant"]=="none"
