"""construction: Compiles FighterBuilds into CompiledFighter, enforcing legality."""
from __future__ import annotations

from dataclasses import fields, replace
from mordheim_construction.contracts import COMPILER_CONTRACTS
from mordheim_construction.contracts import PROFILE_RULE_EFFECTS
from mordheim_construction.contracts import SPECIAL_RULE_EFFECTS
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_construction.contracts import effect_index
from mordheim_construction.contracts import mechanic_index
from mordheim_construction.contracts import validate_execution_contract
from mordheim_construction.conditions import resolve_supplied_conditions
from mordheim_construction.eligibility import (
    call, construction_call, configuration_context,
    desktop_call, selected_rules, validate_special_rule, validate_loadout, validate_additional_equipment,
)
from mordheim_construction.restrictions import _validate_profile_selections
from mordheim_construction.selection import _applicable_profile_rules
from mordheim_construction.selection import _applicable_rules
from mordheim_construction.selection import _profile
from mordheim_construction.selection import _profile_rule_mechanics
from mordheim_construction.selection import _profile_rule_traits
from mordheim_core.effects import apply_execution_effects
from mordheim_core.effects import merge_effects
from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_runtime_scope
from mordheim_knowledge.loader import runtime_bindings
from pathlib import Path


#: Characteristic fields a construction bonus may target.  The names are the
#: canonical ``mordheim_core.models.Characteristics`` fields.
CHARACTERISTIC_BONUS_KEYS = (
    "weapon_skill", "strength", "toughness", "wounds",
    "initiative", "attacks", "movement", "leadership",
)

#: Optional characteristic fields.  ``None`` means the compiled profile has no
#: known base value, so only a zero bonus can be applied.
OPTIONAL_CHARACTERISTIC_BONUS_KEYS = ("movement", "leadership")


def _characteristic_bonus_block(bonuses, *, source):
    """Validate one ``profile.characteristics``/``stats`` bonus block as data.

    Only the canonical characteristic keys are accepted, and every value must
    be an integer (positive, negative or zero).  Booleans, decimals and strings
    are refused instead of coerced, and an unknown key raises a ``ValueError``
    naming its contract, so a malformed KB entry cannot silently change a
    compiled fighter.
    """
    validated = {}
    for key, value in (bonuses or {}).items():
        if key not in CHARACTERISTIC_BONUS_KEYS:
            raise ValueError(
                f"{source} grants an unknown characteristic bonus {key!r}; "
                f"allowed characteristics are {list(CHARACTERISTIC_BONUS_KEYS)}"
            )
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(
                f"{source} grants a non-integer {key} bonus {value!r}; "
                "only positive, negative or zero integers are accepted"
            )
        validated[key] = validated.get(key, 0) + value
    return validated


def _apply_characteristic_bonuses(characteristics, stat_bonuses):
    """Apply accumulated bonuses, preserving unknown optional characteristics.

    A zero bonus to an unknown ``movement``/``leadership`` keeps it unknown; a
    nonzero bonus to an unknown characteristic is refused rather than inventing
    a base value.  Known characteristics accumulate every valid bonus.
    """
    if not stat_bonuses:
        return characteristics
    values = {}
    for field in fields(Characteristics):
        current = getattr(characteristics, field.name)
        bonus = stat_bonuses.get(field.name, 0)
        if field.name in OPTIONAL_CHARACTERISTIC_BONUS_KEYS and current is None:
            if bonus:
                raise ValueError(
                    f"cannot apply a {bonus:+d} {field.name} bonus: the compiled "
                    f"profile has no known base {field.name}"
                )
            values[field.name] = None
            continue
        values[field.name] = current + bonus
    return Characteristics(**values)


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
    if profile is not None and "hireling_equipment" in profile:
        kit = desktop_call("hirelingKit", build, root, package=package, profile=profile)
        materials = {}
        for entry in profile["hireling_equipment"].get("fixed_items", ()):
            if not entry.get("material_id"):
                continue
            # The sole qualified printed weapon is Crimashin's canonical dagger.
            if entry["item_id"] == "dagger":
                for hand in ("main", "off"):
                    weapon_id = build.main_weapon_id if hand == "main" else build.off_hand_id
                    if weapon_id == "weapon.dagger":
                        materials[hand + "_material_id"] = entry["material_id"]
        build = replace(build, owned_item_ids=tuple(kit), **materials)
    selected_special_mechanics = []
    selected_profile_bindings = []
    selected_compiler_contracts = set()
    selected_compiler_bindings = []
    stat_bonuses = {}
    if build.special_rule_ids:
        rules = selected_rules(build, package, profile, root, automatic_compiler_contracts)
        for rule_id in build.special_rule_ids:
            rule = rules.get(rule_id)
            if rule is None:
                raise ValueError(f"special rule is not available to {build.band_id}: {rule_id}")
            validate_special_rule(build, package, profile, rule, traits.get("starting_skills", ()), "recipients")
            runtime = rule.get("runtime") or {}
            if runtime.get("implemented") != "YES":
                reason = next((str(effect.get("reason")) for effect in runtime.get("effects") or () if effect.get("reason")), "no executable binding")
                raise ValueError(f"special rule is outside the executable duel runtime: {rule_id}: {reason}")
            if runtime.get("grant") != "selectable":
                raise ValueError(f"special rule is not selectable: {rule_id}")
            validate_special_rule(build, package, profile, rule, traits.get("starting_skills", ()), "prerequisites")
            bindings = runtime_bindings(rule)
            if not bindings:
                raise ValueError(f"special rule has no executable contract: {rule_id}")
            validate_special_rule(build, package, profile, rule, traits.get("starting_skills", ()), "access")
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
                # A binding addressed to other profiles is not applied and must
                # not impose any characteristic requirement on this one.
                if profile_ids and build.profile_id not in profile_ids:
                    continue
                for stat, bonus in _characteristic_bonus_block(
                    parameters.get("bonuses"),
                    source=f"{rule_id} binding {binding.get('id')}",
                ).items():
                    stat_bonuses[stat] = stat_bonuses.get(stat, 0) + bonus
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
                    for stat, bonus in _characteristic_bonus_block(
                        definition.get("stats"),
                        source=f"{rule_id} compiler contract",
                    ).items():
                        stat_bonuses[stat] = stat_bonuses.get(stat, 0) + bonus
    characteristics = _apply_characteristic_bonuses(characteristics, stat_bonuses)
    if traits.get("mark_of_onogal_the_crow") and build.profile_id == "marauder-chieftain":
        characteristics = Characteristics(**{
            field.name: (getattr(characteristics, field.name) + (1 if field.name == "toughness" else 0)
                         if getattr(characteristics, field.name) is not None else None)
            for field in fields(Characteristics)
        })
    errors = validate_execution_contract(build.ruleset, root)
    if errors: raise ValueError("; ".join(errors))
    mechanics, effects = mechanic_index(build.ruleset, root), effect_index(build.ruleset, root)
    excluded={row.get("id") for row in load_runtime_scope(build.ruleset,root).get("mechanic_exclusions") or ()}
    # Current conditions are supplied facts, resolved once through the KB
    # catalogue.  The caller names a canonical id; the KB declares the
    # operator, so no adapter carries a second interpretation table.
    supplied = resolve_supplied_conditions(
        build.condition_ids, build.trait_overrides, build.ruleset, root)
    missing_condition_mechanics = sorted(set(supplied.mechanic_ids) - set(effects))
    if missing_condition_mechanics:
        raise ValueError(f"supplied conditions bind unknown mechanics: {missing_condition_mechanics}")
    unavailable_conditions = sorted(set(supplied.mechanic_ids) & excluded)
    if unavailable_conditions:
        raise ValueError(
            f"condition mechanics are outside the one-against-one runtime: {unavailable_conditions}")
    traits.update(supplied.trait_values)
    main_weapon_id=build.main_weapon_id
    automatic_profile_bindings = (
        tuple(
            binding
            for rule in _applicable_rules(package, profile)
            if (rule.get("runtime") or {}).get("grant") != "selectable"
            for binding in runtime_bindings(rule, "profile")
        ) if package is not None else ()
    )
    if any(binding.get("id") == "profile.fist" for binding in automatic_profile_bindings):
        main_weapon_id = "weapon.fist"
    if (profile is not None and build.main_weapon_id=="weapon.dagger"
            and main_weapon_id=="weapon.dagger"):
        allowed=set(desktop_call("equipment", build, root, package=package, profile=profile))
        fixed=set(profile.get("fixed_equipment") or ())
        if fixed:
            weapon_ids=sorted(mid for mid in allowed if mid.startswith("weapon."))
            if weapon_ids:main_weapon_id=weapon_ids[0]
        elif not profile.get("equipment_lists"):
            main_weapon_id="weapon.natural-attacks"
        elif ("weapon.dagger" not in allowed
                # The profile's own printed restriction may refuse the free
                # dagger ('cannot be equipped with weapons'); the shared
                # decision answers, and the creature then fights with its
                # natural attacks instead of carrying an illegal default.
                or desktop_call("implicitWeapon", build, root, package=package, profile=profile) is not None):
            main_weapon_id="weapon.natural-attacks"
    elif (profile is not None and build.main_weapon_id == "weapon.fist"
            and not profile.get("equipment_lists")
            and not profile.get("fixed_equipment")
            and not any(binding.get("id") == "profile.fist" for binding in automatic_profile_bindings)):
        # A neutral empty hand on an unequippable creature is its natural
        # attack, just like the default dagger selection above. Explicit
        # profile.fist contracts retain their own unarmed semantics.
        main_weapon_id = "weapon.natural-attacks"
    selected = [main_weapon_id,build.armour_id,build.main_material_id,*build.defence_ids,*build.skill_ids,*build.preparation_ids]
    selected += [x for x in (build.off_hand_id,build.off_material_id,build.main_poison_id,build.off_poison_id,build.extra_hand_id) if x]
    unknown = [x for x in selected if x not in mechanics and x not in excluded]
    if package is not None and any(x in build.skill_ids for x in unknown):
        # Legality and executable support are separate: an unimplemented member
        # of a published named table is not an unknown catalogue identifier.
        legal = desktop_call("skillChoices", build, root, package=package, profile=profile)
        pending = [x for x in unknown if x in build.skill_ids and legal.get(x)]
        if pending:
            raise ValueError(f"named skills have no executable duel mechanic: {pending}")
    if unknown: raise KeyError(f"unknown mechanic IDs: {unknown}")
    compiler_contracts=automatic_compiler_contracts|selected_compiler_contracts
    compiler_bindings=(*automatic_compiler_bindings,*selected_compiler_bindings)
    if "compiler.lizardmen-scaly-skin" in compiler_contracts:
        natural=4 if build.profile_id=="kroxigor" else 5 if str(build.profile_id).startswith("saurus") else 6
        # The shared contract prints the band default; a clause that names the
        # saved profiles overrides that default for exactly those profiles
        # (Fimir Warriors 5+ while the rest of the band keeps 6+).  Only this
        # binding consumes the value, and a malformed one is refused here
        # instead of silently compiling a wrong save.
        for binding in compiler_bindings:
            parameters=binding.get("parameters") or {}
            if (binding.get("id")!="compiler.lizardmen-scaly-skin"
                    or build.profile_id not in (parameters.get("profile_ids") or ())):
                continue
            value=parameters.get("value")
            if isinstance(value,bool) or not isinstance(value,int) or not 2<=value<=7:
                raise ValueError(
                    f"compiler.lizardmen-scaly-skin prints an invalid natural armour save "
                    f"for {build.profile_id}: {value!r}"
                )
            natural=value
        traits.update({"natural_armour_save":natural,"natural_armour_stacks":True,"natural_armour_worst_save":6})
    loadout_mechanics = (*selected_special_mechanics,
        *(_profile_rule_mechanics(package, profile) if package is not None else ()))
    validate_loadout(build, main_weapon_id, mechanics, compiler_contracts, loadout_mechanics, "hands")
    if build.armour_id == "armour.cathayan-quilted-silk":
        raise ValueError("Cathayan quilted silk is an armour overlay and belongs in defence_ids")
    handed={"defence.shield","defence.buckler","defence.kite-shield"}
    if handed.intersection(build.defence_ids):raise ValueError("hand-held defences belong in off_hand_id")
    if package is not None:_validate_profile_selections(
        build,package,profile,root,main_weapon_id,
        (*selected_profile_bindings, *automatic_profile_bindings),compiler_contracts,compiler_bindings)
    if package is not None and build.owned_item_ids is not None:
        facts = configuration_context(build, package, profile, root=root, possession=build.owned_item_ids,
            slots={"main_weapon_id": main_weapon_id, "off_hand_id": build.off_hand_id,
                   "extra_hand_id": build.extra_hand_id, "armour_id": build.armour_id,
                   "defence_ids": list(build.defence_ids),
                   "main_poison_id": build.main_poison_id, "off_poison_id": build.off_poison_id})
        issues = construction_call("validateConstruction", build, facts, root=root)
        blocked = [issue["message"] for issue in issues if not call("issueIsInformational", issue["code"])]
        if blocked:
            raise ValueError("; ".join(blocked))
    requested=set(build.skill_ids)|set(build.preparation_ids)|set(build.defence_ids)
    if build.main_weapon_id:requested.add(build.main_weapon_id)
    if build.off_hand_id:requested.add(build.off_hand_id)
    unavailable=sorted(requested&excluded)
    if unavailable:raise ValueError(f"mechanics are outside the one-against-one runtime: {unavailable}")
    validate_loadout(build, main_weapon_id, mechanics, compiler_contracts, loadout_mechanics, "skills")
    if "compiler.censer-bearer-loadout" in selected_compiler_contracts:
        traits["frenzy"]=True
    unknown_traits=set(traits)-set(TRAIT_TYPES)
    unknown_overrides=set(build.trait_overrides)-set(TRAIT_TYPES)
    if unknown_traits or unknown_overrides:raise ValueError(f"unknown combat traits: {sorted(unknown_traits|unknown_overrides)}")
    for key,value in build.trait_overrides.items():
        if not isinstance(value,TRAIT_TYPES[key]):raise TypeError(f"invalid combat trait value for {key}: {value!r}")
    traits.update(build.trait_overrides)
    if "elf_kind" in traits and traits["elf_kind"] not in ("high", "dark", "other"):
        raise ValueError("elf_kind must be high, dark or other")
    for key in ("stupidity_leadership", "stupidity_leadership_bonus"):
        if key in traits and (type(traits[key]) is not int or traits[key] < 0):
            raise ValueError(f"{key} must be a non-negative integer")
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
    global_ids += list(supplied.mechanic_ids)
    if (main_weapon_id == "weapon.chainsaw-sword" or build.off_hand_id == "weapon.chainsaw-sword"
            or "chainsaw_sword" in (build.owned_item_ids or ())):
        # Fear is granted by bearing this item, not by landing its attack.
        global_ids.append("mechanic.causes-fear")
    from mordheim_knowledge.loader import load_items
    carried_items = set(build.owned_item_ids or ())
    if profile is not None:
        carried_items.update(profile.get("fixed_equipment") or ())
    if (carried_items.intersection({"holy_relic", "holy_relic_pilgrim_only", "arcane_candelabrum"})
            or "weapon.arcane-candelabrum" in (main_weapon_id, build.off_hand_id)):
        global_ids.append("defence.holy-relic")
    global_ids += [build.armour_id, *build.defence_ids]
    if build.off_hand_id and build.off_hand_id.startswith("defence."):
        global_ids.append(build.off_hand_id)
    global_effects = apply_execution_effects(global_effects, global_ids, effects, "passive", "fighter")
    global_effects = apply_execution_effects(global_effects, global_ids, effects, "duel_start", "fighter")
    for skill_id in traits.get("starting_skills") or ():
        if skill_id not in effects:
            from mordheim_knowledge.loader import load_skills
            source_skill = next((r for r in load_skills(build.ruleset, root) if r['id'] == skill_id), None)
            if source_skill is not None and (source_skill.get('runtime') or {}).get('scope') == 'NO':
                continue
            raise ValueError(f"profile references unknown or unsupported starting skill ID: {skill_id}")
        global_effects = apply_execution_effects(global_effects, (skill_id,), effects, "passive", "fighter")
    # Current conditions are supplied facts, not acquisition or spell rolls.
    trait_tags=tuple({"spectral_touch": "trait.spectral-touch", "causes_fear": "mechanic.causes-fear", "stupidity": "mechanic.stupidity", "stupidity_exempt": "condition.stupidity-exempt", "stupidity_initial_failed": "condition.stupidity-failed"}.get(key, key)
                     for key,value in traits.items() if value is True)
    from mordheim_knowledge.loader import load_items
    carried = set(build.owned_item_ids or ())
    if profile is not None:
        carried.update(profile.get("fixed_equipment") or ())
    if (any(row["id"] in carried and row.get("kind") == "ranged-weapon"
            for row in load_items(build.ruleset, root))
            or any("pistol" in weapon_id for weapon_id in (main_weapon_id, build.off_hand_id) if weapon_id)):
        trait_tags = (*trait_tags, "condition.ranged-armed")
    if traits.get("lit_item"):
        trait_tags = (*trait_tags, "condition.open-flame")
    bloodline = traits.get("vampire_bloodline")
    canonical_bloodline = ((profile.get("combat_traits") or {}).get("vampire_bloodline")
                          if profile is not None else None)
    if bloodline is not None and bloodline not in {"strigoi", "blood-dragon", "necrarch", "lahmian", "von-carstein"}:
        raise ValueError("unknown vampire_bloodline")
    if canonical_bloodline and bloodline not in (None, canonical_bloodline):
        raise ValueError("vampire_bloodline conflicts with the canonical profile")
    bloodline = canonical_bloodline or bloodline
    if bloodline:
        if not traits.get("vampire"):
            raise ValueError("vampire_bloodline requires a Vampire")
        trait_tags = (*trait_tags, f"vampire-bloodline.{bloodline}")
    if traits.get("vampire"):
        trait_tags = (*trait_tags, "species.vampire")
    if traits.get("lizardman"):
        trait_tags = (*trait_tags, "species.lizardman")
    nature = traits.get("creature_kind")
    if nature is not None:
        if nature not in {"living", "undead", "daemon", "possessed"}:
            raise ValueError(f"unknown creature_kind: {nature}")
        trait_tags = (*trait_tags, f"nature.{nature}")
        if nature in {"undead", "possessed"}:
            trait_tags = (*trait_tags, "undead_or_possessed")
    fitting = traits.get("wheelo_fitting")
    if fitting is not None:
        if fitting not in {"axe", "club", "spear", "morning-star"}:
            raise ValueError(f"unknown Wheelo fitting: {fitting}")
        if "mechanic.wheelo-impact" not in global_effects.tags:
            raise ValueError("a supplied legal Wheelo fitting requires a Wheelo")
        trait_tags = (*trait_tags, f"wheelo.fitting.{fitting}")
    if traits.get("righteous_charge_active"):
        if not build.mounted:
            raise ValueError("Righteous Charge requires a mounted recipient")
        if package is not None and build.band_id != "knights-of-the-bitter-moors-mim":
            raise ValueError("Righteous Charge requires a Bitter Moors recipient")
        trait_tags = (*trait_tags, "condition.righteous-charge")
    command = traits.get("active_command")
    if command is not None:
        if command not in {"follow-me-mine-pugnacious-ones", "art-thou-ready-to-die-fighting"}:
            raise ValueError(f"unknown active Command: {command}")
        if package is not None and build.band_id != "mazzalupo":
            raise ValueError("an active Mazzalupo Command requires a Mazzalupo recipient")
        trait_tags = (*trait_tags, f"condition.command.{command}")
    sex = traits.get("sex")
    if sex is not None:
        if sex not in {"male", "female"}:
            raise ValueError(f"unknown sex: {sex}")
        trait_tags = (*trait_tags, f"sex.{sex}")
    species = traits.get("species")
    if species is not None:
        if species not in {"human", "dwarf", "skaven", "orc", "goblin", "halfling", "ogre", "beastman"}:
            raise ValueError(f"unknown species: {species}")
        trait_tags = (*trait_tags, f"species.{species}")
    # Named opposing cult members, not every human/animal in their warband.
    ulric_rival = traits.get("ulric_rival") or (
        package is not None and (
            build.band_id == "sisters-of-sigmar"
            or build.band_id in {"witch-hunters", "trollheim-witch-hunters"}
                and build.profile_id in {"witch-hunter-captain", "witch-hunters", "warrior-priest"}
            or build.band_id == "hirelings.hired-sword.2b"
                and build.profile_id in {"hireling.hired-sword.warrior-priest-of-sigmar-miracle-workers",
                                         "hireling.hired-sword.sister-of-sigmar"}))
    if ulric_rival:
        trait_tags = (*trait_tags, "identity.ulric-rival")
    if traits.get("onogal_follower") or traits.get("mark_of_onogal_the_crow"):
        trait_tags = (*trait_tags, "identity.onogal-follower")
    if traits.get("chaos_follower"):
        trait_tags = (*trait_tags, "identity.chaos-follower")
    if traits.get("aquatic"):
        trait_tags = (*trait_tags, "species.aquatic")
    if traits.get("guiding_dream_target"):
        if "mechanic.guiding-dream" not in global_effects.tags:
            raise ValueError("a nominated Guiding Dream target requires Guiding Dream")
        trait_tags = (*trait_tags, "condition.guiding-dream-target")
    if traits.get("flesh_peddler_mark"):
        if "mechanic.flesh-peddler" not in global_effects.tags:
            raise ValueError("a nominated Flesh-Peddler mark requires Flesh-Peddler")
        trait_tags = (*trait_tags, "condition.flesh-peddler-mark")
    if traits.get("normal_animal"):
        trait_tags = (*trait_tags, "species.normal-animal", "species.animal")
    if traits.get("elf_kind") in ("high", "dark"):
        trait_tags=(*trait_tags,f"species.{traits['elf_kind']}-elf")
    if traits.get("magical_attacks"):
        trait_tags=(*trait_tags,"attack.magical")
    fauna_kind = traits.get("fauna_animal_kind")
    if fauna_kind is not None:
        if fauna_kind not in {"ordinary", "handled", "large-predator"}:
            raise ValueError("unknown fauna_animal_kind")
        trait_tags = (*trait_tags, "species.animal", f"fauna-animal.{fauna_kind}")
    handler_value = traits.get("animal_handler_leadership")
    if handler_value is not None and (type(handler_value) is not int or not 0 <= handler_value <= 10):
        raise ValueError("animal_handler_leadership must be an integer between 0 and 10")
    fighter_kind = traits.get("fighter_kind")
    # Native hirelings use a synthetic construction type, not a source Hero designation.
    source_kind = profile.get("type") if profile is not None and not profile.get("kind") in {"hired-sword", "dramatis-personae"} else None
    if fighter_kind is not None and fighter_kind not in {"hero", "henchman", "animal", "summoned"}:
        raise ValueError("unknown fighter_kind")
    if source_kind is not None and fighter_kind not in (None, source_kind):
        raise ValueError("fighter_kind conflicts with the canonical profile type")
    fighter_kind = source_kind or fighter_kind
    if fighter_kind is not None:
        trait_tags = (*trait_tags, f"fighter-kind.{fighter_kind}")
    house = traits.get("house_guard_house")
    if house is not None:
        if house not in {"fierezza", "halcon", "baluardo"}:
            raise ValueError("unknown House Guard house")
        if package is not None and build.band_id != "house-guard-sc":
            raise ValueError("house_guard_house requires a House Guard recipient")
        trait_tags = (*trait_tags, f"house-guard.{house}")
    origin = traits.get("mercenary_origin")
    if "band--middenheim-physical-prowess" in build.special_rule_ids:
        if origin not in (None, "middenheim"):
            raise ValueError("mercenary_origin conflicts with the selected Middenheim rule")
        origin = "middenheim"
    if origin is not None:
        if origin not in {"reikland", "marienburg", "middenheim", "other"}:
            raise ValueError("unknown mercenary_origin")
        trait_tags = (*trait_tags, "warband-group.human-mercenary", f"mercenary-origin.{origin}")
    if package is not None:
        trait_tags=(*trait_tags,f"band.{package.band.get('id')}")
        family = package.band.get("canonical_family")
        if family in {"witch-hunters", "sisters-of-sigmar"}:
            trait_tags = (*trait_tags, f"band.{family}")
        from mordheim_knowledge.campaign import load_warband_groups
        trait_tags = (*trait_tags, *(row['id'] for row in load_warband_groups(build.ruleset, root)
            if package.band.get('id') in row.get('band_ids', ())))
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
    drinking = traits.get("snorri_drunk_result")
    if "mechanic.snorri-drunk" in global_effects.tags:
        if type(drinking) is not int or drinking not in range(2, 7):
            raise ValueError("Snorri requires a supplied pre-battle drinking result 2-6; result 1 means no participant")
        if drinking == 2:
            characteristics = replace(characteristics,
                weapon_skill=max(1, characteristics.weapon_skill - 1),
                strength=max(1, characteristics.strength - 1))
        elif drinking == 4:
            global_effects = merge_effects(global_effects, EffectSet(tags=("condition.snorri-stench",)))
        elif drinking == 5:
            characteristics = replace(characteristics, strength=characteristics.strength + 1)
        elif drinking == 6:
            # The drinking table explicitly overrides Slayer psychology immunity.
            global_effects = merge_effects(global_effects,
                EffectSet(tags=("condition.snorri-frenzy",), frenzy=True))
    elif drinking is not None:
        raise ValueError("snorri_drunk_result requires Snorri's canonical drinking rule")
    if ("mechanic.wheelo-skill-modifications" in global_effects.tags
            and "skill.mighty-blow" in global_effects.tags):
        # Its source substitutes crew +1 to wound for the ordinary +1 Strength.
        global_effects = replace(global_effects, strength_bonus=global_effects.strength_bonus - 1,
                                 wound_modifier=global_effects.wound_modifier + 1)
    if "compiler.knighthood" in compiler_contracts and "promotion.knight-errant" in build.variant_ids:
        global_effects = merge_effects(global_effects, EffectSet(tags=(
            "promotion.knight-errant", "rule.knight", "rule.vain", "rule.impetuous",
        )))
    if any(binding.get("id") == "profile.fist" and
           (binding.get("parameters") or {}).get("ignore_penalties")
           for binding in (*automatic_profile_bindings, *selected_profile_bindings)):
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
    if ("compiler.aldred-fellblade" in compiler_contracts
            and main_weapon_id == "weapon.double-handed-weapon"):
        # This printed sword can parry; no parry is granted to an empty hand.
        main_effect = replace(main_effect, parry=True)
        if main_without_poison is not None:
            main_without_poison = replace(main_without_poison, parry=True)
    if ("compiler.woodsmen-quarterstaff" in compiler_contracts
            and main_weapon_id == "weapon.quarter-staff"):
        # The Woodsmen source prints S+1, not the generic Balanced staff's I+1.
        # Retain material/poison contributions; replace only the weapon delta.
        generic_staff = effects["weapon.quarter-staff"].effect
        main_effect = replace(main_effect,
            strength_bonus=main_effect.strength_bonus - generic_staff.strength_bonus + 1,
            initiative_bonus=main_effect.initiative_bonus - generic_staff.initiative_bonus)
        if main_without_poison is not None:
            main_without_poison = replace(main_without_poison,
                strength_bonus=main_without_poison.strength_bonus - generic_staff.strength_bonus + 1,
                initiative_bonus=main_without_poison.initiative_bonus - generic_staff.initiative_bonus)
    vomit_attack = (apply_execution_effects(
        EffectSet(), ("weapon.vomit-attack",), effects, "attack", "attack")
        if "weapon.vomit-attack" in selected_special_mechanics else None)
    off_effect=apply_execution_effects(EffectSet(), (build.off_hand_id,), effects, "attack", "attack") if build.off_hand_id else None
    off_without_poison = None
    if off_effect and build.off_hand_id.startswith("weapon."):
        off_ids=[build.off_hand_id, build.off_material_id, *profile_rule_skills]
        if build.off_poison_id:
            off_without_poison = apply_execution_effects(EffectSet(), off_ids, effects, "attack", "attack")
        if build.off_poison_id: off_ids.append(build.off_poison_id)
        off_effect=apply_execution_effects(EffectSet(), off_ids, effects, "attack", "attack")
    if off_effect and build.off_hand_id == "defence.shield" and "mechanic.norse-shieldmaster" in loadout_mechanics:
        off_effect = replace(off_effect, parry=True, tags=(*off_effect.tags, "defence.shield"))
    eagle_count = traits.get("eagle_friends")
    if eagle_count is not None:
        if type(eagle_count) is not int or eagle_count < 1:
            raise ValueError("eagle_friends must be a positive integer")
        if "mechanic.myrmidia-eagle-friend" not in global_effects.tags:
            raise ValueError("eagle_friends requires Eagle Friend")
    extra_attacks=[]
    if "mechanic.myrmidia-eagle-friend" in global_effects.tags:
        extra_attacks.extend(EffectSet(tags=("rule.eagle-friend",), fixed_strength=3, priority=1)
                            for _ in range(eagle_count or 1))
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
    if "compiler.strikes-last-bite" in automatic_compiler_contracts:
        extra_attacks.append(EffectSet(tags=("weapon.natural-attacks", "rule.strikes-last-bite")))
    if ("skill.unarmed-fighting" in global_effects.tags and "weapon.quarter-staff" in main_effect.tags
            and "compiler.woodsmen-quarterstaff" not in compiler_contracts):
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
        extra_attacks.append(merge_effects(effects["weapon.mace"].effect, EffectSet(strength_bonus=-1)))
    validate_additional_equipment(build)
    if build.extra_hand_id:
        extra=effects[build.extra_hand_id].effect
        if build.extra_hand_id.startswith("weapon."):
            extra_attacks.append(extra)
        elif build.extra_hand_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}:
            global_effects=merge_effects(global_effects, extra)
            if "band--mutations-extra-arm" in build.special_rule_ids: extra_attacks.append(effects["weapon.natural-attacks"].effect)
    if "band--sacred-mark-venom-glands" in build.special_rule_ids:
        main_effect=EffectSet(tags=("weapon.natural-attacks", "rule.venom-glands"), target_armour_bonus=1, injury_modifier=1)
        main_without_poison = None
    armour_base = 5 if "defence.sea-dragon-cloak" in build.defence_ids else int(mechanics[build.armour_id].get("base_save") or 7)
    armour_save = armour_base-effects[build.armour_id].effect.armour_save_bonus-global_effects.armour_save_bonus
    if off_effect is not None:armour_save-=off_effect.armour_save_bonus
    if build.off_hand_id == "defence.kite-shield" and build.mounted:armour_save+=1
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
    if traits.get("stupidity_initial_failed") and not ("mechanic.stupidity" in global_effects.tags):
        raise ValueError("initial failed Stupidity requires an active Stupidity condition")
    if "stupidity_leadership" in traits and "mechanic.handler-leadership" not in global_effects.tags:
        raise ValueError("Handler Leadership requires a handler-only Leadership rule")
    if traits.get("stupidity_leadership_bonus", 0) and "mechanic.brood-mentality" not in global_effects.tags:
        raise ValueError("Stupidity Leadership bonus requires Brood Mentality")
    return CompiledFighter(f"{build.band_id or 'custom'}:{build.profile_id or 'custom'}",characteristics,main_effect,off_effect,global_effects,max(1,armour_save),4 if "defence.helmet" in build.defence_ids else 5 if "defence.cooking-pot-helmet" in build.defence_ids else 7,natural_armour_save,bool(build.off_hand_id and build.off_hand_id.startswith("weapon.")),bool(traits.get("natural_armour_unmodified",False)),int(traits.get("injury_profile") or 0),random_characteristics,natural_armour_worst_save=int(traits.get("natural_armour_worst_save") or 7),extra_attacks=tuple(extra_attacks),missile_weapon_limit=missile_weapon_limit,ballistic_skill=ballistic_skill,construction_tags=construction_tags,main_weapon_without_poison=main_without_poison,off_hand_without_poison=off_without_poison,mounted=build.mounted,unarmed_weapon=effects["weapon.fist"].effect,vomit_attack=vomit_attack, stupidity_leadership=traits.get("stupidity_leadership"), stupidity_leadership_bonus=traits.get("stupidity_leadership_bonus", 0), animal_handler_leadership=handler_value)
