"""construction.restrictions: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_construction.contracts import BLACKPOWDER_WEAPONS
from mordheim_construction.contracts import DRUG_PREPARATIONS
from mordheim_construction.contracts import MISSILE_WEAPONS
from mordheim_construction.selection import _profile_allowed_mechanics
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_simulation_mappings
from mordheim_knowledge.loader import load_skills


def _validate_bound_equipment_restrictions(build, main_weapon_id, profile_bindings):
    """Apply explicit prohibitions regardless of the access list."""
    forbidden = set()
    for binding in profile_bindings:
        if binding.get("id") != "profile.equipment-restrictions":
            continue
        values = (binding.get("parameters") or {}).get("forbids", ())
        forbidden.update((values,) if isinstance(values, str) else values)
    selected = {main_weapon_id, build.armour_id, build.off_hand_id,
                build.extra_hand_id, *build.defence_ids}
    armour_defences = {"defence.shield", "defence.buckler", "defence.helmet",
                      "defence.cooking-pot-helmet"}
    if "armour" in forbidden and (
        build.armour_id != "armour.no-armour" or selected & armour_defences
    ):
        raise ValueError(f"armour is forbidden for {build.band_id}/{build.profile_id}")
    if "ranged-weapons" in forbidden and selected & MISSILE_WEAPONS:
        raise ValueError(f"missile weapons are forbidden for {build.band_id}/{build.profile_id}")
    if "heavy-armour" in forbidden and build.armour_id in {
        "armour.heavy-armour", "armour.gromril-armour", "armour.ithilmar-armour", "armour.plate-armour"
    }:
        raise ValueError(f"heavy armour is forbidden for {build.band_id}/{build.profile_id}")
    if "weapon.lance" in forbidden and "weapon.lance" in selected:
        raise ValueError(f"lance is forbidden for {build.band_id}/{build.profile_id}")
    if "defence.helmet" in forbidden and selected & {"defence.helmet", "defence.cooking-pot-helmet"}:
        raise ValueError(f"helmet is forbidden for {build.band_id}/{build.profile_id}")


def _validate_category_prohibitions(build, main_weapon_id, compiler_contracts, compiler_bindings):
    """Explicit prohibitions, independent of the available equipment lists."""
    hands = {main_weapon_id, build.off_hand_id, build.extra_hand_id}
    if "compiler.no-missile-weapons" in compiler_contracts and hands & MISSILE_WEAPONS:
        raise ValueError(f"missile weapons are forbidden for {build.band_id}/{build.profile_id}")
    if "compiler.no-blackpowder-weapons" in compiler_contracts and hands & BLACKPOWDER_WEAPONS:
        raise ValueError(f"blackpowder weapons are forbidden for {build.band_id}/{build.profile_id}")
    if ("compiler.strictures" in compiler_contracts
            and build.profile_id in {"dragon-monks", "warrior-monks"}
            and build.armour_id != "armour.no-armour"):
        raise ValueError("Dragon Monks and Warrior Monks may never wear armour")
    categories = {
        category for binding in compiler_bindings
        if binding.get("id") == "compiler.forbid-item-categories"
        for category in (binding.get("parameters") or {}).get("categories", ())
    }
    if "poison" in categories and (build.main_poison_id or build.off_poison_id):
        raise ValueError(f"poisons are forbidden for {build.band_id}/{build.profile_id}")
    if "drug" in categories and set(build.preparation_ids) & DRUG_PREPARATIONS:
        raise ValueError(f"drugs are forbidden for {build.band_id}/{build.profile_id}")


def _validate_required_initial_choices(build, compiler_contracts):
    """Mandatory choices of initial construction, not campaign history."""
    if "compiler.mutant-requires-mutation-at-recruitment" in compiler_contracts:
        if not any(rule_id.startswith("band--mutations-") for rule_id in build.special_rule_ids):
            raise ValueError(f"at least one mutation is required for {build.band_id}/{build.profile_id}")
    if "compiler.nurgle-s-blessings" in compiler_contracts:
        if not any(rule_id.startswith("band--blessings-of-nurgle-") for rule_id in build.special_rule_ids):
            raise ValueError("Tainted Ones require at least one Blessing of Nurgle")


def _validate_possessed_mutation_limit(build, compiler_contracts, mutation_count):
    if ("compiler.possessed-optional-zero-to-two-mutations-at-recruitment" in compiler_contracts
            and mutation_count > 2):
        raise ValueError(f"at most two mutations are allowed for {build.band_id}/{build.profile_id}")


def _validate_profile_selections(build, package, profile, mechanics, root, main_weapon_id,
                                 profile_bindings=(), compiler_contracts=(), compiler_bindings=()):
    _validate_bound_equipment_restrictions(build, main_weapon_id, profile_bindings)
    _validate_category_prohibitions(build, main_weapon_id, compiler_contracts, compiler_bindings)
    allowed=_profile_allowed_mechanics(package,profile,mechanics,build.ruleset,root)
    access_contracts={
        "compiler.pirate-human-mercenary-equipment-access",
        "compiler.foreign-or-native-background",
        "compiler.knighthood",
        "compiler.follow-the-darkest-tribe",
        "compiler.proven-warrior",
        "compiler.weapon-knowledge",
    }
    if access_contracts & set(compiler_contracts):
        mapping={str(row["item_id"]):row for row in load_simulation_mappings(build.ruleset,root).get("item_mappings") or ()}
        by_option={str(row.get("engine_option")):mid for mid,row in mechanics.items() if row.get("engine_option")}
        def add_equipment_lists(equipment_lists):
            for equipment_list in equipment_lists:
                for item in equipment_list.get("items") or ():
                    row=mapping.get(str(item.get("item_id")))
                    mechanic_id=(row or {}).get("mechanic_id") or by_option.get(str((row or {}).get("engine_option")))
                    if row and row.get("status")=="implemented" and mechanic_id in mechanics:
                        allowed.add(str(mechanic_id))
    if "compiler.pirate-human-mercenary-equipment-access" in compiler_contracts:
        mercenary = next(
            candidate for candidate in load_bands("mordheim", root)
            if candidate.band.get("id") == "mercenaries"
        )
        add_equipment_lists(mercenary.equipment_lists)
    if "compiler.foreign-or-native-background" in compiler_contracts:
        background=("native" if "background.native" in build.variant_ids or (
            not build.variant_ids and build.profile_id in {"spirits","jackals"}
        ) else "foreign")
        beloved="beloved" if build.profile_id=="beloved" else "undead"
        list_id=f"{background}-{beloved}-equipment-list"
        add_equipment_lists(row for row in package.equipment_lists if row.get("id")==list_id)
        if build.profile_id in {"blood-slaves","black-hounds"} and background!="foreign":
            raise ValueError(f"{build.profile_id} requires the Foreign background")
        if build.profile_id in {"spirits","jackals"} and background!="native":
            raise ValueError(f"{build.profile_id} requires the Native background")
    if "compiler.knighthood" in compiler_contracts:
        promotions=set(build.variant_ids)&{"promotion.squire","promotion.knight-errant"}
        if len(promotions)>1:raise ValueError("choose at most one Knighthood promotion")
        if "promotion.knight-errant" in promotions:
            allowed.clear()
            add_equipment_lists(row for row in package.equipment_lists if row.get("id")=="knights-equipment-list")
    if "compiler.follow-the-darkest-tribe" in compiler_contracts and "tribe.kurgan" in build.variant_ids:
        for candidate in load_bands("mordheim",root):
            for equipment_list in candidate.equipment_lists:
                if any(item.get("item_id")=="wolfcloak" for item in equipment_list.get("items") or ()):
                    add_equipment_lists((equipment_list,))
    if "compiler.proven-warrior" in compiler_contracts:
        if build.profile_id != "younguns":
            raise ValueError("Proven Warrior may only be selected by a Young'un")
        black_orc = next(candidate for candidate in package.profiles if candidate.get("id") == "black-orcs")
        add_equipment_lists(
            row for row in package.equipment_lists
            if row.get("id") in set(black_orc.get("equipment_lists") or ())
        )
    if "compiler.weapon-knowledge" in compiler_contracts:
        allowed.update(mechanic_id for mechanic_id in mechanics if mechanic_id.startswith("weapon."))
    equipment={main_weapon_id,build.armour_id,*build.defence_ids}
    if build.off_hand_id:equipment.add(build.off_hand_id)
    if build.main_material_id!="material.normal":equipment.add(build.main_material_id)
    if build.off_hand_id and build.off_material_id!="material.normal":equipment.add(build.off_material_id)
    equipment.discard("armour.no-armour")
    if main_weapon_id in {"weapon.natural-attacks", "weapon.fist"}:equipment.discard(main_weapon_id)
    hand_equipment={main_weapon_id,build.off_hand_id}
    is_knight=(any(str(rule_id).endswith("--knight") for rule_id in profile.get("rule_ids") or ())
               or "promotion.knight-errant" in build.variant_ids)
    if "compiler.powder-s-expensive" in compiler_contracts and profile.get("type") != "hero" and hand_equipment & BLACKPOWDER_WEAPONS:
        raise ValueError(f"blackpowder weapons are forbidden for Bandit Henchmen: {build.band_id}/{build.profile_id}")
    if "compiler.chivalry" in compiler_contracts and is_knight:
        if hand_equipment & MISSILE_WEAPONS:
            raise ValueError(f"missile weapons are forbidden for Knights: {build.band_id}/{build.profile_id}")
        if build.main_poison_id or build.off_poison_id:
            raise ValueError(f"poisons are forbidden for Knights: {build.band_id}/{build.profile_id}")
        if set(build.preparation_ids) & DRUG_PREPARATIONS:
            raise ValueError(f"drugs are forbidden for Knights: {build.band_id}/{build.profile_id}")
    if "compiler.haughty" in compiler_contracts:
        dwarf_made={"material.gromril","material.obsidian","armour.gromril-armour"}
        if equipment & dwarf_made:
            raise ValueError(f"Dwarf-made equipment is forbidden for {build.band_id}/{build.profile_id}")
    if "compiler.chaos-engineer" in compiler_contracts and any("chaos" in item for item in equipment if item):
        raise ValueError(f"Chaos armour is forbidden for {build.band_id}/{build.profile_id}")
    if ("compiler.saurus-skill-prohibitions" in compiler_contracts
            and build.profile_id in {"saurus-totem-warrior","saurus-braves"}
            and hand_equipment & MISSILE_WEAPONS):
        raise ValueError("missile weapons are forbidden for Saurus")
    illegal=sorted(equipment-allowed)
    if illegal:raise ValueError(f"equipment is not available to {build.band_id}/{build.profile_id}: {illegal}")
    skills={str(row["id"]):row for row in load_skills(build.ruleset,root)}
    access=set(profile.get("skill_access") or ())
    access.update(
        str((binding.get("parameters") or {}).get("category"))
        for binding in profile_bindings
        if binding.get("id") == "profile.skill-access"
        and (binding.get("parameters") or {}).get("category")
    )
    for binding in compiler_bindings:
        if binding.get("id") == "compiler.promoted-hero-skill-access":
            access.update(str(category) for category in (binding.get("parameters") or {}).get("allowed_skill_lists") or ())
    promoted_lists={
        str(value).removeprefix("skill-list.") for value in build.variant_ids
        if str(value).startswith("skill-list.")
    }
    if "compiler.promoted-hero-no-strength-access" in compiler_contracts:
        if "strength" in promoted_lists:
            raise ValueError(f"Strength skill list is forbidden for {build.band_id}/{build.profile_id}")
        if len(promoted_lists) > 2:
            raise ValueError("a promoted Hero may choose at most two skill lists")
        access.update(promoted_lists)
    if "compiler.slayer-skill-options" in compiler_contracts:
        access.update(("combat", "strength", "special"))
    if "compiler.proven-warrior" in compiler_contracts:
        access.update(("combat", "shooting", "strength", "speed", "special"))
    if "compiler.knighthood" in compiler_contracts:
        if "promotion.knight-errant" in build.variant_ids:
            access.update(("combat","academic","strength","speed","special"))
        elif "promotion.squire" in build.variant_ids:
            access.update(("combat","academic","strength","speed"))
    def skill_is_available(skill_id):
        skill = skills.get(skill_id)
        if skill is None or skill.get("category") not in access:
            return False
        if skill.get("category") != "special":
            return True
        source_ids = {build.band_id, str(package.band.get("canonical_family") or "")}
        return any(
            any(f"/{band_id}" in str(reference.get("url") or "") for band_id in source_ids if band_id)
            for reference in skill.get("source_refs") or ()
        )
    if "compiler.saurus-skill-prohibitions" in compiler_contracts and build.profile_id in {"saurus-totem-warrior","saurus-braves"}:
        academic=sorted(skill for skill in build.skill_ids if (skills.get(skill) or {}).get("category")=="academic")
        if academic:raise ValueError(f"Academic skills are forbidden for Saurus: {academic}")
    if "compiler.disciple-of-sigmar" in compiler_contracts:
        forbidden=sorted(skill for skill in build.skill_ids if "arcane" in skill or "sorcery" in skill)
        if forbidden:raise ValueError(f"sorcery and Arcane Lore are forbidden for {build.band_id}/{build.profile_id}: {forbidden}")
    if "compiler.swabbie-rabble-loadout" in compiler_contracts:
        forbidden=sorted(skill for skill in build.skill_ids if "arcane" in skill or "sorcery" in skill)
        if forbidden:raise ValueError(f"magic is forbidden for Swabbies: {forbidden}")
    if "compiler.no-arcane-lore" in compiler_contracts:
        forbidden=sorted(skill for skill in build.skill_ids if "arcane" in skill or "sorcery" in skill)
        if forbidden:raise ValueError(f"Arcane Lore is forbidden for {build.band_id}/{build.profile_id}: {forbidden}")
    illegal_skills=sorted(skill for skill in build.skill_ids if not skill_is_available(skill))
    if illegal_skills:raise ValueError(f"skills are not available to {build.band_id}/{build.profile_id}: {illegal_skills}")
    if "compiler.knighthood" in compiler_contracts:
        ordinary_categories={
            str((skills.get(skill) or {}).get("category")) for skill in build.skill_ids
            if (skills.get(skill) or {}).get("category") != "special"
        }
        if len(ordinary_categories)>2:
            raise ValueError("a promoted Squire may use at most two ordinary skill lists")
    if "compiler.promoted-hero-no-strength-access" in compiler_contracts:
        strength_skills=sorted(skill for skill in build.skill_ids if (skills.get(skill) or {}).get("category")=="strength")
        if strength_skills:raise ValueError(f"Strength skills are forbidden for {build.band_id}/{build.profile_id}: {strength_skills}")
    restrictions=" ".join(profile.get("equipment_restrictions") or ()).lower()
    forbids_armour=any(text in restrictions for text in (
        "never wear armour","cannot wear armour","armour is not allowed","does not allow armour",
        "using any armour","non-armour items","do not wear armour","any form of armour",
        "do not use weapons or wear armour","never use weapons or armour","cannot use normal equipment"))
    if forbids_armour and build.armour_id!="armour.no-armour":raise ValueError(f"armour is forbidden for {build.band_id}/{build.profile_id}")
    if ("may not use an off-hand weapon" in restrictions or "must use one hand" in restrictions) and build.off_hand_id:
        raise ValueError(f"off-hand equipment is forbidden for {build.band_id}/{build.profile_id}")
    if ("may not use double-handed weapons" in restrictions or "double-handed weapons are for" in restrictions) and mechanics[main_weapon_id].get("hands")==2 and "compiler.proven-warrior" not in compiler_contracts:
        raise ValueError(f"two-handed weapons are forbidden for {build.band_id}/{build.profile_id}")
    _validate_required_initial_choices(build, compiler_contracts)
    mutation_count=sum(rule_id.startswith("band--mutations-") for rule_id in build.special_rule_ids)
    if "compiler.mutation-purchase-at-recruitment" in compiler_contracts and mutation_count and build.profile_id not in {"mutants","the-possessed"}:
        raise ValueError(f"mutations are available only to Mutants and the Possessed: {build.band_id}/{build.profile_id}")
    _validate_possessed_mutation_limit(build, compiler_contracts, mutation_count)
    if "compiler.sacred-marks" in compiler_contracts:
        sacred_count=sum(rule_id.startswith("band--sacred-mark-") for rule_id in build.special_rule_ids)
        if sacred_count > 1:
            raise ValueError("a Lizardman Hero may have at most one Sacred Mark")
    if "compiler.tracker-gear" in compiler_contracts:
        fixed=set(profile.get("fixed_equipment") or ())
        if not {"rope_hook","bolas"}<=fixed:
            raise ValueError("Trackers must begin with Rope and Hook and Bolas")
    if "compiler.vampiric-powers" in compiler_contracts:
        powers=[rule_id for rule_id in build.special_rule_ids if "-power-" in rule_id]
        bloodline=build.profile_id.removesuffix("-vampire")
        foreign=[rule_id for rule_id in powers if f"band--{bloodline}-power-" not in rule_id]
        if foreign:raise ValueError(f"Vampiric Powers must belong to the Vampire's bloodline: {foreign}")
    if "compiler.warrior-s-code" in compiler_contracts:
        magical_skills=sorted(skill for skill in build.skill_ids if "arcane" in skill or "sorcery" in skill or "magic" in skill)
        if magical_skills:raise ValueError(f"magic is forbidden by the Warrior's Code: {magical_skills}")
        magical=sorted(rule_id for rule_id in build.special_rule_ids if any(word in rule_id for word in ("spell","magic","arcane")))
        if magical:raise ValueError(f"magic is forbidden by the Warrior's Code: {magical}")
    if "compiler.follow-the-darkest-tribe" in compiler_contracts:
        selected=set(build.variant_ids)&{"tribe.norse","tribe.kurgan","tribe.hung"}
        if len(selected)>1:raise ValueError("choose exactly one Marauder tribe")
    if "compiler.foreign-or-native-background" in compiler_contracts:
        selected=set(build.variant_ids)&{"background.foreign","background.native"}
        if len(selected)>1:raise ValueError("choose exactly one Foreign or Native background")
