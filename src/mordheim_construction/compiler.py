"""construction.compiler: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import fields
from mordheim_construction.contracts import COMPILER_CONTRACTS
from mordheim_construction.contracts import PROFILE_RULE_EFFECTS
from mordheim_construction.contracts import SPECIAL_RULE_EFFECTS
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_construction.contracts import effect_index
from mordheim_construction.contracts import mechanic_index
from mordheim_construction.contracts import validate_execution_contract
from mordheim_construction.restrictions import _validate_profile_selections
from mordheim_construction.selection import _applicable_profile_rules
from mordheim_construction.selection import _applicable_rules
from mordheim_construction.selection import _profile
from mordheim_construction.selection import _profile_allowed_mechanics
from mordheim_construction.selection import _profile_rule_mechanics
from mordheim_construction.selection import _profile_rule_traits
from mordheim_core.effects import apply_execution_effects
from mordheim_core.effects import merge_effects
from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import runtime_bindings
from pathlib import Path


def compile_fighter(build: FighterBuild, root: Path | None = None) -> CompiledFighter:
    characteristics, traits, package, profile, random_characteristics = _profile(build, root)
    if package is not None:
        traits = {**traits, **_profile_rule_traits(package, profile)}
    automatic_rule_effects = EffectSet()
    automatic_compiler_contracts = set()
    automatic_compiler_bindings = []
    if package is not None:
        for rule in _applicable_rules(package, profile):
            runtime = rule.get("runtime") or {}
            if runtime.get("implemented") != "YES" or runtime.get("grant") not in {"profile", "band"}:
                continue
            for binding in runtime_bindings(rule, "compiler"):
                binding_id=str(binding["id"])
                if binding_id in COMPILER_CONTRACTS:
                    automatic_compiler_contracts.add(binding_id)
                    automatic_compiler_bindings.append(binding)
                    continue
                contract = PROFILE_RULE_EFFECTS.get(str(rule.get("id")))
                if contract is None:
                    raise ValueError(f"profile rule has no executable compiler contract: {rule.get('id')}")
                automatic_rule_effects = merge_effects(automatic_rule_effects, EffectSet(**contract.get("effects", {})))
                traits.update(contract.get("traits", {}))
    selected_special_effects = EffectSet()
    selected_special_mechanics = []
    selected_profile_bindings = []
    selected_compiler_contracts = set()
    selected_compiler_bindings = []
    stat_bonuses = {}
    if build.special_rule_ids:
        if package is None:
            rules = {
                str(rule.get("id")): rule
                for collection in load_collections(root)
                if build.ruleset in collection.get("rulesets", ())
                for candidate_package in load_bands(str(collection["id"]), root)
                for rule in candidate_package.special_rules
                if str(rule.get("id")) in build.special_rule_ids
            }
        else:
            rules = {str(rule.get("id")): rule for rule in package.special_rules}
        if "compiler.slayer-skill-options" in automatic_compiler_contracts:
            dwarf_package = next(
                candidate for candidate in load_bands(build.collection, root)
                if candidate.band.get("id") == "chaos-streets-dwarf-treasure-hunters"
            )
            for candidate in dwarf_package.special_rules:
                if candidate.get("kind") == "warband_skill" and (candidate.get("runtime") or {}).get("implemented") == "YES":
                    rules.setdefault(str(candidate["id"]), {**candidate, "eligibility": [], "applies_to": {}})
        if "band--renowned-virtue" in build.special_rule_ids:
            bretonnians=next(candidate for candidate in load_bands("mordheim",root) if candidate.band.get("id")=="bretonnian-knights")
            for candidate in bretonnians.special_rules:
                candidate_id=str(candidate.get("id"))
                if candidate_id.startswith("band--virtue-of-"):
                    rules.setdefault(candidate_id,{**candidate,"eligibility":[]})
        mutation_count = sum(rule_id.startswith("band--mutations-") for rule_id in build.special_rule_ids)
        external_mutation_grants = {
            "beastmen-raiders": "band--beastmen-special-skills-mutant",
            "marauders-of-chaos": "band--marauder-special-skills-mutant",
        }
        mutation_grant = external_mutation_grants.get(build.band_id)
        if mutation_count and mutation_grant:
            if build.special_rule_ids.count(mutation_grant) < mutation_count:
                raise ValueError(f"each purchased mutation requires {mutation_grant}")
            for candidate_package in load_bands(build.collection, root):
                for candidate in candidate_package.special_rules:
                    candidate_id = str(candidate.get("id"))
                    if candidate_id.startswith("band--mutations-"):
                        rules.setdefault(candidate_id, {**candidate, "eligibility": []})
        for rule_id in build.special_rule_ids:
            rule = rules.get(rule_id)
            if rule is None:
                raise ValueError(f"special rule is not available to {build.band_id}: {rule_id}")
            eligible = set(rule.get("eligibility") or ())
            if package is not None and eligible and build.profile_id not in eligible:
                raise ValueError(f"special rule is not available to {build.band_id}/{build.profile_id}: {rule_id}")
            applicable_profiles = set((rule.get("applies_to") or {}).get("profile_ids") or ())
            if package is not None and applicable_profiles and build.profile_id not in applicable_profiles:
                raise ValueError(f"special rule is not available to {build.band_id}/{build.profile_id}: {rule_id}")
            if rule_id.startswith("band--blessings-of-nurgle-") and build.profile_id != "tainted-ones":
                raise ValueError(f"special rule is not available to {build.band_id}/{build.profile_id}: {rule_id}")
            native_virtue = package is not None and any(
                candidate.get("id") == rule_id for candidate in package.special_rules
            )
            if (rule_id.startswith("band--virtue-of-") and not native_virtue
                    and "band--renowned-virtue" not in build.special_rule_ids):
                raise ValueError("a foreign Bretonnian Virtue requires Renowned Virtue")
            runtime = rule.get("runtime") or {}
            if runtime.get("implemented") != "YES":
                reason = next((str(effect.get("reason")) for effect in runtime.get("effects") or () if effect.get("reason")), "no executable binding")
                raise ValueError(f"special rule is outside the executable duel runtime: {rule_id}: {reason}")
            if runtime.get("grant") != "selectable":
                raise ValueError(f"special rule is not selectable: {rule_id}")
            if (rule_id == "band--clan-pestilens-special-skills-ignore-pain"
                    and "skill.resilient" not in build.skill_ids
                    and "skill.resilient" not in traits.get("starting_skills", ())):
                raise ValueError("Ignore Pain requires Resilient")
            bindings = runtime_bindings(rule)
            if not bindings:
                raise ValueError(f"special rule has no executable contract: {rule_id}")
            # Special-skill access also applies when the skill compiles to a
            # trait (e.g. Shaggy Hide), not just a skill.* mechanic.
            selects_warband_skill = rule.get("kind") == "warband_skill" or any(
                binding.get("kind") == "mechanic" and str(binding.get("id", "")).startswith("skill.")
                for binding in bindings
            )
            if (
                package is not None
                and selects_warband_skill
                and rule.get("applies_to", {}).get("band") is True
                and not eligible
                and "special" not in set(profile.get("skill_access") or ())
            ):
                raise ValueError(
                    f"special rule is not available to {build.band_id}/{build.profile_id}: {rule_id}"
                )
            selected_special_mechanics.extend(str(binding["id"]) for binding in bindings if binding.get("kind") == "mechanic")
            # Editorial variants sharing Sword Master do not share every condition.
            parry_variant = {
                "band--blood-dragon-power-sword-master": "rule.blood-dragon-sword-master",
                "band--dwarf-special-skills-master-of-blades": "rule.dwarf-axe-parry-reroll",
            }.get(rule_id)
            if parry_variant:
                selected_special_effects = merge_effects(
                    selected_special_effects, EffectSet(tags=(parry_variant,)))
            selected_profile_bindings.extend(binding for binding in bindings if binding.get("kind") == "profile")
            for binding in (binding for binding in bindings if binding.get("id") == "profile.characteristics"):
                parameters = binding.get("parameters") or {}
                profile_ids = set(parameters.get("profile_ids") or ())
                if profile_ids and build.profile_id not in profile_ids:
                    continue
                for stat, bonus in (parameters.get("bonuses") or {}).items():
                    stat_bonuses[str(stat)] = stat_bonuses.get(str(stat), 0) + int(bonus)
            for binding in (binding for binding in bindings if binding.get("kind") == "trait"):
                key = str(binding["id"]).removeprefix("trait.").replace("-", "_")
                traits[key] = (binding.get("parameters") or {}).get("value")
            if any(binding.get("kind") == "compiler" for binding in bindings):
                for binding in (binding for binding in bindings if binding.get("kind") == "compiler"):
                    binding_id=str(binding["id"])
                    if binding_id in COMPILER_CONTRACTS:
                        selected_compiler_contracts.add(binding_id)
                        selected_compiler_bindings.append(binding)
                        continue
                    definition = SPECIAL_RULE_EFFECTS.get(rule_id)
                    if definition is None:
                        raise ValueError(f"special rule has no executable compiler contract: {rule_id}")
                    selected_special_effects = merge_effects(selected_special_effects, EffectSet(**definition.get("effects", {})))
                    traits.update(definition.get("traits", {}))
                    for stat, bonus in definition.get("stats", {}).items():
                        stat_bonuses[stat] = stat_bonuses.get(stat, 0) + bonus
    if stat_bonuses:
        characteristics = Characteristics(**{
            field.name: getattr(characteristics, field.name) + stat_bonuses.get(field.name, 0)
            for field in fields(Characteristics)
        })
    if traits.get("mark_of_onogal_the_crow") and build.profile_id == "marauder-chieftain":
        characteristics = Characteristics(**{
            field.name: getattr(characteristics, field.name) + (1 if field.name == "toughness" else 0)
            for field in fields(Characteristics)
        })
    errors = validate_execution_contract(build.ruleset, root)
    if errors: raise ValueError("; ".join(errors))
    mechanics, effects = mechanic_index(build.ruleset, root), effect_index(build.ruleset, root)
    excluded={row.get("id") for row in load_runtime_scope(build.ruleset,root).get("mechanic_exclusions") or ()}
    main_weapon_id=build.main_weapon_id
    automatic_profile_bindings = (
        tuple(
            binding
            for rule in _applicable_rules(package, profile)
            for binding in runtime_bindings(rule, "profile")
        ) if package is not None else ()
    )
    if any(binding.get("id") == "profile.fist" for binding in automatic_profile_bindings):
        main_weapon_id = "weapon.fist"
    if (profile is not None and build.main_weapon_id=="weapon.dagger"
            and main_weapon_id=="weapon.dagger"):
        allowed=_profile_allowed_mechanics(package,profile,mechanics,build.ruleset,root)
        fixed=set(profile.get("fixed_equipment") or ())
        if fixed:
            weapon_ids=sorted(mid for mid in allowed if mid.startswith("weapon."))
            if weapon_ids:main_weapon_id=weapon_ids[0]
        elif not profile.get("equipment_lists"):
            main_weapon_id="weapon.natural-attacks"
        elif "weapon.dagger" not in allowed:
            main_weapon_id="weapon.natural-attacks"
    selected = [main_weapon_id,build.armour_id,build.main_material_id,*build.defence_ids,*build.skill_ids,*build.preparation_ids]
    selected += [x for x in (build.off_hand_id,build.off_material_id,build.main_poison_id,build.off_poison_id,build.extra_hand_id) if x]
    unknown = [x for x in selected if x not in mechanics and x not in excluded]
    if unknown: raise KeyError(f"unknown mechanic IDs: {unknown}")
    main_row = mechanics[main_weapon_id]
    if not main_row.get("main_hand",False): raise ValueError("illegal main-hand selection")
    compiler_contracts=automatic_compiler_contracts|selected_compiler_contracts
    compiler_bindings=(*automatic_compiler_bindings,*selected_compiler_bindings)
    if "compiler.lizardmen-scaly-skin" in compiler_contracts:
        natural=4 if build.profile_id=="kroxigor" else 5 if str(build.profile_id).startswith("saurus") else 6
        traits.update({"natural_armour_save":natural,"natural_armour_stacks":True,"natural_armour_worst_save":6})
    if "band--clan-pestilens-special-skills-contagious" in build.special_rule_ids:
        if "band--clan-pestilens-special-skills-rotten-body" not in build.special_rule_ids:
            raise ValueError("Contagious requires Rotten Body")
    if "band--renowned-virtue" in build.special_rule_ids:
        virtues=[rule_id for rule_id in build.special_rule_ids if rule_id.startswith("band--virtue-of-")]
        if len(virtues)!=1:raise ValueError("Renowned Virtue requires exactly one Bretonnian Virtue")
    if build.off_hand_id:
        off_row = mechanics[build.off_hand_id]
        if build.off_hand_id.startswith("weapon.") and not off_row.get("off_hand",False): raise ValueError("illegal off-hand selection")
        arms_master=bool({"compiler.ignore-difficult-to-use-restrictions","compiler.master-of-arms"}&compiler_contracts)
        if (main_row.get("hands") == 2 or main_row.get("paired")) and not arms_master: raise ValueError("main weapon occupies both hands")
        restricted_off_hands = {
            "weapon.morning-star": set(),
            "weapon.natural-attacks": set(),
            "weapon.fist": set(),
            "weapon.spear": {"defence.shield", "defence.buckler"},
            "weapon.broadsword": {"defence.shield", "defence.kite-shield"},
            "weapon.squig-prodder": {"defence.shield", "weapon.spiked-gauntlet"},
            "weapon.boar-spear": {"defence.shield", "defence.buckler"},
        }
        if main_weapon_id in restricted_off_hands and build.off_hand_id not in restricted_off_hands[main_weapon_id]:
            raise ValueError(f"{main_weapon_id} cannot be combined with {build.off_hand_id}")
        if build.armour_id in {"armour.toughened-leathers", "armour.ninja-robes"} and build.off_hand_id in {"defence.shield", "defence.kite-shield"}:
            raise ValueError("toughened leathers cannot be combined with a shield")
        if build.armour_id in {"armour.wizard-s-robe", "armour.eshin-assassin-robes"} and build.off_hand_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}:
            raise ValueError(f"{build.armour_id} cannot be combined with other armour except a helmet")
    if build.armour_id == "armour.cathayan-quilted-silk":
        raise ValueError("Cathayan quilted silk is an armour overlay and belongs in defence_ids")
    handed={"defence.shield","defence.buckler","defence.kite-shield"}
    if handed.intersection(build.defence_ids):raise ValueError("hand-held defences belong in off_hand_id")
    if package is not None:_validate_profile_selections(
        build,package,profile,mechanics,root,main_weapon_id,
        (*selected_profile_bindings, *automatic_profile_bindings),compiler_contracts,compiler_bindings)
    requested=set(build.skill_ids)|set(build.preparation_ids)|set(build.defence_ids)
    if build.main_weapon_id:requested.add(build.main_weapon_id)
    if build.off_hand_id:requested.add(build.off_hand_id)
    unavailable=sorted(requested&excluded)
    if unavailable:raise ValueError(f"mechanics are outside the one-against-one runtime: {unavailable}")
    if "compiler.berserker-incompatible-with-ferocious-charge" in compiler_contracts and "skill.ferocious-charge" in selected_special_mechanics:
        raise ValueError("Berserker may not be combined with Ferocious Charge")
    if "compiler.censer-bearer-loadout" in selected_compiler_contracts:
        if "mechanic.black-hunger" not in selected_special_mechanics:
            raise ValueError("Censer Bearer requires Black Hunger")
        if main_weapon_id!="weapon.censer" or build.off_hand_id:
            raise ValueError("Censer Bearer may use only a Censer in close combat")
        traits["frenzy"]=True
    unknown_traits=set(traits)-set(TRAIT_TYPES)
    unknown_overrides=set(build.trait_overrides)-set(TRAIT_TYPES)
    if unknown_traits or unknown_overrides:raise ValueError(f"unknown combat traits: {sorted(unknown_traits|unknown_overrides)}")
    for key,value in build.trait_overrides.items():
        if not isinstance(value,TRAIT_TYPES[key]):raise TypeError(f"invalid combat trait value for {key}: {value!r}")
    traits.update(build.trait_overrides)
    for key,value in traits.items():
        if not isinstance(value,TRAIT_TYPES[key]):raise TypeError(f"invalid combat trait value for {key}: {value!r}")
    for key in ("natural_armour_save","natural_armour_worst_save","ward_save","regeneration_save"):
        if key in traits and not 2 <= int(traits[key]) <= 7:
            raise ValueError(f"combat trait {key} must be between 2 and 7")
    if "injury_profile" in traits and int(traits["injury_profile"]) not in range(5):
        raise ValueError("combat trait injury_profile must be between 0 and 4")
    if "caught_fire_threshold" in traits and int(traits["caught_fire_threshold"]) not in range(2,7):
        raise ValueError("combat trait caught_fire_threshold must be between 2 and 6")
    global_effects = EffectSet()
    profile_rule_skills = _profile_rule_mechanics(package, profile) if package is not None else ()
    global_ids = [item for item in selected if item not in {
        main_weapon_id, build.off_hand_id, build.armour_id, build.main_material_id,
        build.off_material_id, build.main_poison_id, build.off_poison_id,
    }]
    global_ids += list(profile_rule_skills)
    global_ids += selected_special_mechanics
    global_ids += [build.armour_id, *build.defence_ids]
    if build.off_hand_id and build.off_hand_id.startswith("defence."):
        global_ids.append(build.off_hand_id)
    global_effects = apply_execution_effects(global_effects, global_ids, effects, "passive", "fighter")
    global_effects = apply_execution_effects(global_effects, global_ids, effects, "duel_start", "fighter")
    for skill_id in traits.get("starting_skills") or ():
        if skill_id not in effects: raise ValueError(f"profile references unknown starting skill ID: {skill_id}")
        global_effects = apply_execution_effects(global_effects, (skill_id,), effects, "passive", "fighter")
    trait_tags=tuple(key for key,value in traits.items() if value is True)
    if traits.get("magical_attacks"):
        trait_tags=(*trait_tags,"attack.magical")
    if package is not None:
        trait_tags=(*trait_tags,f"band.{package.band.get('id')}")
    if profile is not None and "skink" in f"{profile.get('id','')} {profile.get('name','')}".lower():
        trait_tags=(*trait_tags,"species.skink")
    if profile is not None and any(
        str(rule_id).endswith(("--animal", "--animals"))
        for rule_id in profile.get("rule_ids") or ()
    ):
        trait_tags=(*trait_tags,"species.animal")
    global_effects = merge_effects(global_effects,EffectSet(
        tags=trait_tags,attacks_bonus=int(traits.get("extra_natural_attacks",0)),
        charge_attacks_bonus=int(bool(traits.get("charge_attack_bonus",False))),
        first_round_charge_attacks_bonus=int(bool(traits.get("first_round_charge_attack_bonus",False))),
        poison_immunity=bool(traits.get("poison_immune",False) or traits.get("mark_of_onogal_the_crow",False)), bear_hug=bool(traits.get("bear_hug",False)),
        frenzy=bool(traits.get("frenzy",False)),
        parry=bool(traits.get("counts_as_buckler",False)),
        armour_save_bonus=int(bool(traits.get("counts_as_shield",False))),
        ward_save=int(traits.get("ward_save",7)),
        regeneration_save=int(traits.get("regeneration_save",7)),
        ward_save_mundane_only=bool(traits.get("ward_save_mundane_only",False)),
        natural_armour_negated_by_magic=bool(traits.get("natural_armour_negated_by_magic",False)),
        regeneration_blocked_by_fire=bool(traits.get("regeneration_blocked_by_fire",False)),
        regeneration_blocked_by_blessed=bool(traits.get("regeneration_blocked_by_blessed",False)),
        caught_fire_threshold=int(traits.get("caught_fire_threshold",7)),
        armour_penetration=int(bool(traits.get("perfect_killer",False)))))
    global_effects = merge_effects(merge_effects(global_effects, automatic_rule_effects), selected_special_effects)
    if "compiler.knighthood" in compiler_contracts and "promotion.knight-errant" in build.variant_ids:
        global_effects = merge_effects(global_effects, EffectSet(tags=(
            "promotion.knight-errant", "rule.knight", "rule.vain", "rule.impetuous",
        )))
    if any(binding.get("id") == "profile.fist" and
           (binding.get("parameters") or {}).get("ignore_penalties")
           for binding in automatic_profile_bindings):
        global_effects = merge_effects(global_effects, EffectSet(tags=("rule.unarmed-without-penalties",)))
    if "mechanic.energy-focus" in global_effects.tags:
        if build.energy_focus_attacks > characteristics.attacks:
            raise ValueError("Energy Focus cannot sacrifice more Attacks than the profile has")
        global_effects = merge_effects(global_effects, EffectSet(energy_focus_attacks=build.energy_focus_attacks))
    elif build.energy_focus_attacks:
        raise ValueError("energy_focus_attacks requires Energy Focus")
    main_ids=[main_weapon_id, build.main_material_id, *profile_rule_skills]
    main_without_poison = (apply_execution_effects(EffectSet(), main_ids, effects, "attack", "attack")
                           if build.main_poison_id else None)
    if build.main_poison_id: main_ids.append(build.main_poison_id)
    main_effect=apply_execution_effects(EffectSet(), main_ids, effects, "attack", "attack")
    off_effect=apply_execution_effects(EffectSet(), (build.off_hand_id,), effects, "attack", "attack") if build.off_hand_id else None
    off_without_poison = None
    if off_effect and build.off_hand_id.startswith("weapon."):
        off_ids=[build.off_hand_id, build.off_material_id, *profile_rule_skills]
        if build.off_poison_id:
            off_without_poison = apply_execution_effects(EffectSet(), off_ids, effects, "attack", "attack")
        if build.off_poison_id: off_ids.append(build.off_poison_id)
        off_effect=apply_execution_effects(EffectSet(), off_ids, effects, "attack", "attack")
    extra_attacks=[]
    automatic_rule_ids = {str(rule.get("id")) for rule in _applicable_profile_rules(package, profile)} if package is not None else set()
    # Natural and profile-granted attacks are resolved independently, so
    # weapon modifiers never leak into horns, hooves, claws, or bites.
    if "centigors--trample" in automatic_rule_ids:
        extra_attacks.append(EffectSet(tags=("rule.trample",)))
    if "compiler.bite-attack" in automatic_compiler_contracts:
        extra_attacks.append(EffectSet(
            tags=("weapon.natural-attacks", "rule.bite-attack"),
            strength_bonus=int(bool(traits.get("huge_jaws", False))),
        ))
    if "skill.unarmed-fighting" in global_effects.tags and "weapon.quarter-staff" in main_effect.tags:
        extra_attacks.append(effects["weapon.fist"].effect)
    if "skill.shield-strike" in global_effects.tags and build.off_hand_id == "defence.shield":
        extra_attacks.append(EffectSet(tags=("rule.shield-strike",)))
    if traits.get("scorpion_tail", False):
        extra_attacks.append(EffectSet(tags=("rule.scorpion-tail",), fixed_strength=5))
    if "band--beastmen-special-skills-horned-one" in build.special_rule_ids:
        extra_attacks.append(EffectSet(tags=("rule.horned-one",), charge_strength_bonus=0))
    if "band--mutations-great-claw" in build.special_rule_ids:
        extra_attacks.append(EffectSet(tags=("rule.great-claw",), strength_bonus=1))
    if "band--shield-bash" in build.special_rule_ids:
        if not (build.off_hand_id in {"defence.shield", "defence.kite-shield"}): raise ValueError("Shield Bash requires a shield or kite shield")
        extra_attacks.append(merge_effects(effects["weapon.mace"].effect, EffectSet(strength_bonus=-1)))
    if build.extra_hand_id:
        if not any(rule_id in build.special_rule_ids for rule_id in ("band--mutations-extra-arm", "band--skaven-special-skills-tail-fighting")):
            raise ValueError("an extra hand requires Extra Arm or Tail Fighting")
        if build.extra_hand_id == "defence.kite-shield":
            raise ValueError("the extra hand may not carry a kite shield")
        extra=effects[build.extra_hand_id].effect
        if build.extra_hand_id.startswith("weapon."):
            extra_attacks.append(extra)
        elif build.extra_hand_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}:
            global_effects=merge_effects(global_effects, extra)
            if "band--mutations-extra-arm" in build.special_rule_ids: extra_attacks.append(effects["weapon.natural-attacks"].effect)
        else: raise ValueError("the extra hand must hold a one-handed weapon, shield, or buckler")
    if "band--sacred-mark-venom-glands" in build.special_rule_ids:
        main_effect=EffectSet(tags=("weapon.natural-attacks", "rule.venom-glands"), target_armour_bonus=1, injury_modifier=1)
        main_without_poison = None
    armour_save = int(mechanics[build.armour_id].get("base_save") or 7)-effects[build.armour_id].effect.armour_save_bonus-global_effects.armour_save_bonus
    if off_effect is not None:armour_save-=off_effect.armour_save_bonus
    if build.off_hand_id == "defence.kite-shield" and build.mounted:armour_save+=1
    if "defence.sea-dragon-cloak" in build.defence_ids:
        if (build.armour_id != "armour.no-armour"
                or build.off_hand_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}
                or set(build.defence_ids) & {"defence.helmet", "defence.cooking-pot-helmet"}):
            raise ValueError("Sea Dragon cloak cannot be combined with other armour")
        armour_save=min(armour_save,5)
    if "armour.cathayan-quilted-silk" in build.defence_ids:armour_save-=1
    natural_armour_save=int(traits.get("natural_armour_save") or 7)
    # Hardened Leather explicitly gives no additional bonus to a Scaly Skin
    # save.  Keep all other modifiers (for example, a shield), but cancel the
    # leather's own 6+ contribution before composing the natural save.
    if traits.get("natural_armour_stacks") and build.armour_id=="armour.toughened-leathers":
        armour_save+=1
    if traits.get("natural_armour_stacks") and natural_armour_save<=6:
        armour_save-=7-natural_armour_save
    missile_weapon_limit=1 if "compiler.bow-discipline" in compiler_contracts else 5 if "compiler.master-of-throwing-weapons" in compiler_contracts else 2
    construction_tags=tuple(sorted(compiler_contracts))
    ballistic_skill=int((profile.get("characteristics") or {}).get("BS") or 0) if profile is not None else 0
    return CompiledFighter(f"{build.band_id or 'custom'}:{build.profile_id or 'custom'}",characteristics,main_effect,off_effect,global_effects,max(1,armour_save),4 if "defence.helmet" in build.defence_ids else 5 if "defence.cooking-pot-helmet" in build.defence_ids else 7,natural_armour_save,bool(build.off_hand_id and build.off_hand_id.startswith("weapon.")),bool(traits.get("natural_armour_unmodified",False)),int(traits.get("injury_profile") or 0),random_characteristics,natural_armour_worst_save=int(traits.get("natural_armour_worst_save") or 7),extra_attacks=tuple(extra_attacks),missile_weapon_limit=missile_weapon_limit,ballistic_skill=ballistic_skill,construction_tags=construction_tags,main_weapon_without_poison=main_without_poison,off_hand_without_poison=off_without_poison,mounted=build.mounted,unarmed_weapon=effects["weapon.fist"].effect)
