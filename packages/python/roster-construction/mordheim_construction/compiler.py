"""construction: Compiles FighterBuilds into CompiledFighter, enforcing legality."""
from __future__ import annotations

from dataclasses import fields, replace
from mordheim_construction.contracts import COMPILER_CONTRACTS
from mordheim_construction.contracts import PROFILE_RULE_EFFECTS
from mordheim_construction.contracts import SPECIAL_RULE_EFFECTS
from mordheim_construction.contracts import VETERAN_TRACKER_SKILLS
from mordheim_construction.contracts import TRAIT_TYPES
from mordheim_construction.contracts import effect_index
from mordheim_construction.contracts import mechanic_index
from mordheim_construction.contracts import validate_execution_contract
from mordheim_construction.conditions import resolve_supplied_conditions
from mordheim_construction.eligibility import (
    _catalogue, call, construction_call, configuration_context,
    desktop_call, selected_rules, validate, validate_special_rule, validate_loadout, validate_additional_equipment,
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
from mordheim_core.models import MutationOption
from mordheim_core.models import CarriedEquipment
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
#: Characteristics a printed profile may leave unfixed.  A bonus that would
#: need such a base is refused instead of inventing one.
OPTIONAL_CHARACTERISTIC_BONUS_KEYS = ("movement", "leadership", "initiative")

#: Worn armour that makes its bearer a metal-clad target for the printed
#: Electrical Touch clause.  The identity belongs to the physical item so that a
#: later mutation which re-evaluates the inventory keeps it while the item is
#: still worn and withdraws it when the item is gone.
METAL_ARMOUR_IDS = frozenset({
    "armour.heavy-armour", "armour.gromril-armour", "armour.ithilmar-armour",
    "armour.plate-armour", "armour.chaos-armour", "armour.attlas-plate-mail",
})
#: The worn defences the ``metal_armour`` supplied fact names when the fighter's
#: own armour is the metal one.
METAL_DEFENCE_IDS = frozenset({
    "defence.shield", "defence.buckler", "defence.kite-shield",
    "defence.helmet", "defence.cooking-pot-helmet",
})
#: The Sea Dragon cloak variants are single physical pieces: one per warrior,
#: whichever variant the source grants. The shared constant-save cloak and the
#: printed Druchii variant must not compose with each other or themselves.
SEA_DRAGON_CLOAK_MECHANIC_IDS = frozenset({
    "defence.sea-dragon-cloak", "defence.sea-dragon-cloak-druchii",
})


def _prepared_mutation_options(ruleset, effects, root):
    """Resolve the source's explicit D66 data into immutable duel inputs."""
    from mordheim_knowledge.campaign import load_campaign_catalog
    rows = load_campaign_catalog(ruleset, root).catalogue("mutations").get("random_mutation_chart") or ()
    if {row["roll"] for row in rows} != {10 * tens + units for tens in range(1, 7) for units in range(1, 7)}:
        raise ValueError("Solkan requires the complete canonical D66 mutation chart")
    def declared_effect(parameters):
        return EffectSet(**{**parameters, "tags": tuple(parameters.get("tags") or ())})
    prepared = []
    for row in rows:
        effect = declared_effect(row.get("effect_parameters") or {})
        for mechanic_id in row.get("effect_ids") or ():
            effect = merge_effects(effect, effects[mechanic_id].effect)
        prepared.append(MutationOption(
            roll=row["roll"], effect=effect,
            stat_ops=tuple(tuple(operation) for operation in row.get("stat_ops") or ()),
            extra_attacks=tuple(declared_effect(parameters) for parameters in row.get("extra_attack_parameters") or ()),
            limb_forms=tuple(effects[mid].effect for mid in row.get("limb_effect_ids") or ()),
        ))
    return tuple(prepared)


def _item_mechanic_resolver(build, profile, mechanics, root):
    """Resolve each physical item of a kit to the executable mechanic it implements."""
    from mordheim_knowledge.loader import load_simulation_mappings
    by_option = {row.get("engine_option"): mid for mid, row in mechanics.items()}
    mappings = {row["item_id"]: row.get("mechanic_id") or by_option.get(row.get("engine_option"))
                for row in load_simulation_mappings(build.ruleset, root).get("item_mappings") or ()
                if row.get("status") == "implemented"}
    equivalent = {}
    for item in (profile or {}).get("hireling_equipment", {}).get("unique_equipment", ()):
        counts_as = item.get("counts_as")
        base = counts_as if isinstance(counts_as, str) else (counts_as or {}).get("item_id")
        equivalent[item["id"]] = mappings.get(item["id"]) or mappings.get(base)

    def mechanic_id(item_id):
        return item_id if item_id in mechanics else equivalent.get(item_id) or mappings.get(item_id)

    return mechanic_id


def _printed_kit(build, profile, mechanics, root):
    """The physical pieces of a band profile's printed fixed kit.

    A band profile carries no hireling kit, so the equipment its source prints
    as mandatory is the `fixed_equipment` list.  Each entry resolves to the
    operator its catalogue item implements while the item keeps its own
    identity: two blade copies stay two pieces, and a weapon qualification (a
    material) or a coating (a poison) declared by the same kit belongs to those
    copies rather than to every weapon the bearer might hold.
    """
    if profile is None or profile.get("hireling_equipment"):
        return ()
    mechanic_id = _item_mechanic_resolver(build, profile, mechanics, root)
    return tuple((item, resolved) for item in profile.get("fixed_equipment") or ()
                 if (resolved := mechanic_id(item)) is not None)


def _printed_compound_kit(build, printed, mechanics):
    """Fill the hands a printed compound kit names and revest its own copies.

    A kit that prints a weapon qualification ('two dark elven blades coated in
    dark venom') declares the compound itself: its weapon copies are the hands
    the source writes, in printed order, and the qualification and coating
    revest exactly those copies.  Each hand keeps the operator of the piece it
    holds, so the second blade is its own copy rather than a second
    contribution of the first.  Returns the build and the one-handed copies.
    """
    def one_handed(mechanic_id):
        row = mechanics.get(mechanic_id) or {}
        return (mechanic_id.startswith("weapon.")
                and mechanic_id not in {"weapon.fist", "weapon.natural-attacks"}
                and int(row.get("hands") or 1) == 1 and not row.get("paired"))

    blades = [mechanic_id for _, mechanic_id in printed if one_handed(mechanic_id)]
    material_id = next((mid for _, mid in printed if mid.startswith("material.")), None)
    poison_id = next((mid for _, mid in printed if mid.startswith("poison.")), None)
    updates = {}
    if len(blades) > 1 and build.off_hand_id is None:
        updates["off_hand_id"] = blades[1]
    if build.owned_item_ids is None:
        # The printed copies are what the bearer carries, so provenance follows
        # each physical piece instead of the operator it implements.  The
        # qualification and coating are consumed by the copies they revest, not
        # carried beside them as pieces of their own.
        updates["owned_item_ids"] = tuple(item for item, mid in printed
                                          if not mid.startswith(("material.", "poison.")))
    # The printed compound names the qualified weapon first ('a dark elven
    # blade and dagger'), so a weapon qualification revests the copies of that
    # weapon only: the dagger beside it is not a second dark elven blade.
    qualified = blades[0] if blades else None
    for hand, weapon_id in (("main", blades[0] if blades else None),
                            ("off", updates.get("off_hand_id", build.off_hand_id))):
        if weapon_id is None or weapon_id not in blades:
            continue
        if (material_id and weapon_id == qualified
                and getattr(build, f"{hand}_material_id") == "material.normal"):
            updates[f"{hand}_material_id"] = material_id
        if poison_id and getattr(build, f"{hand}_poison_id") is None:
            updates[f"{hand}_poison_id"] = poison_id
    return (replace(build, **updates) if updates else build), blades


def _mutation_equipment(build, profile, kit, main_id, main, off, mechanics, effects, root,
                        *, metal_worn=False):
    """Keep physical copies and their active positions; never grant availability."""
    from mordheim_knowledge.loader import load_items
    item_rows = {row["id"]: row for row in load_items(build.ruleset, root)}
    item_kinds = {item_id: row.get("kind") for item_id, row in item_rows.items()}
    mechanic_id = _item_mechanic_resolver(build, profile, mechanics, root)
    # A unique object whose canonical equivalent prints several grips is the
    # same physical piece in each mode, so an active alternate still consumes
    # its one copy instead of adding a second carried object.
    alternates = {}
    for entry in (profile or {}).get("hireling_equipment", {}).get("unique_equipment", ()):
        counts_as = entry.get("counts_as")
        base = counts_as if isinstance(counts_as, str) else (counts_as or {}).get("item_id")
        alternates[entry["id"]] = tuple(
            str(value) for value in (item_rows.get(str(base or "")) or {}).get("alternate_mechanic_ids") or ())
    owned = list(build.owned_item_ids if build.owned_item_ids is not None else kit or ())
    unused = list(owned)
    prepared = []
    armour_defences = {"defence.shield", "defence.buckler", "defence.kite-shield", "defence.helmet",
                       "defence.cooking-pot-helmet", "defence.sea-dragon-cloak", "defence.wolf-pelt-cloak"}
    def physical_kind(item, mid):
        kind = item_kinds.get(item)
        if kind in {"close-combat-weapon", "ranged-weapon"}:
            return "weapon"
        if kind == "armour":
            return "armour"
        if mid and mid.startswith("weapon."):
            return "weapon"
        if mid and mid.startswith("armour."):
            return "armour"
        return "defence" if mid in armour_defences else "other"
    def physical(mid, effect, slot, clean=None):
        index = next((index for index, item in enumerate(unused)
                      if mechanic_id(item) == mid or mid in alternates.get(item, ())), None)
        item = unused.pop(index) if index is not None else mid
        prepared.append(CarriedEquipment(item, effect, physical_kind(item, mid), slot,
            (("wounds", 1),) if mid == "armour.attlas-plate-mail" else (), clean))
    def local_effect(mid):
        effect = effects[mid].effect
        if mid == "defence.sea-dragon-cloak":
            effect = merge_effects(effect, EffectSet(armour_save_bonus=2))
        if mid.startswith("armour."):
            effect = merge_effects(effect, EffectSet(armour_save_bonus=7 - int(mechanics[mid].get("base_save") or 7)))
            if mid in {"armour.gromril-armour", "armour.attlas-plate-mail"}:
                effect = merge_effects(effect, EffectSet(tags=("material.gromril",)))
            elif mid == "armour.ithilmar-armour":
                effect = merge_effects(effect, EffectSet(tags=("material.ithilmar",)))
        if mid in METAL_ARMOUR_IDS or (metal_worn and mid in METAL_DEFENCE_IDS):
            effect = merge_effects(effect, EffectSet(tags=("condition.metal-armour",)))
        return effect
    if main_id not in {"weapon.fist", "weapon.natural-attacks"}:
        item_ids = [main_id, build.main_material_id]
        clean = (apply_execution_effects(EffectSet(), item_ids, effects, "attack", "attack")
                 if build.main_poison_id else None)
        if build.main_poison_id:
            item_ids.append(build.main_poison_id)
        item_effect = apply_execution_effects(EffectSet(), item_ids, effects, "attack", "attack")
        if "stance.wall-of-steel" in build.variant_ids:
            item_effect = replace(item_effect, two_handed=True, parry=True)
            if clean is not None:
                clean = replace(clean, two_handed=True, parry=True)
        physical(main_id, item_effect, "main", clean)
    if build.off_hand_id:
        clean = None
        if build.off_hand_id.startswith("weapon."):
            item_ids = [build.off_hand_id, build.off_material_id]
            if build.off_poison_id:
                clean = apply_execution_effects(EffectSet(), item_ids, effects, "attack", "attack")
            if build.off_poison_id:
                item_ids.append(build.off_poison_id)
            item_effect = apply_execution_effects(EffectSet(), item_ids, effects, "attack", "attack")
        else:
            item_effect = local_effect(build.off_hand_id)
        physical(build.off_hand_id, item_effect, "off", clean)
    if build.extra_hand_id:
        physical(build.extra_hand_id, local_effect(build.extra_hand_id), "extra")
    if build.armour_id != "armour.no-armour":
        physical(build.armour_id, local_effect(build.armour_id), "armour")
    for index, mid in enumerate(build.defence_ids):
        physical(mid, local_effect(mid), f"defence.{index}")
    for item in unused:
        mid = mechanic_id(item)
        kind = physical_kind(item, mid)
        prepared.append(CarriedEquipment(item, local_effect(mid) if mid in effects else EffectSet(), kind,
            stat_bonuses=(("wounds", 1),) if mid == "armour.attlas-plate-mail" else ()))
    return tuple(prepared)


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
    main_weapon_omitted = build.main_weapon_id is None
    if main_weapon_omitted:
        build = replace(build, main_weapon_id="weapon.dagger")
    characteristics, traits, package, profile, random_characteristics = _profile(build, root)
    from mordheim_construction.source_profiles import prepare_source_profile
    build, characteristics, traits, package, profile, random_characteristics = prepare_source_profile(
        build, characteristics, traits, package, profile, random_characteristics, root)
    morr = "hireling.hired-sword.priest-of-morr-miracle-workers"
    if package is not None and morr + ".skill.haunted-mien" in build.special_rule_ids:
        package = replace(package, special_rules=tuple(
            rule for rule in package.special_rules if rule["id"] != morr + ".rule.strictures"))
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
    if 'compiler.assassin-poisoner' in automatic_compiler_contracts:
        allowed = {'poison.black-lotus', 'poison.black-venom'}
        chosen = build.main_poison_id
        if chosen not in allowed or build.off_poison_id not in (None, chosen):
            raise ValueError('Poisoner requires one shared Black Lotus or Dark Venom choice before battle')
        build = replace(build, off_poison_id=chosen if build.off_hand_id else None)
    kit = ()
    if profile is not None and "hireling_equipment" in profile:
        innate = profile["hireling_equipment"].get("innate_weapon_id")
        if innate and main_weapon_omitted:
            build = replace(build, main_weapon_id=innate)
        # Resolve only an omitted choice, before matching the complete printed kit.
        # An explicit dagger is a real selection and must pass the same matcher.
        if package is not None and main_weapon_omitted and not innate:
            item_mappings = _catalogue(build.collection, build.ruleset, root).get("mappings", {})
            weapon_mechanics = mechanic_index(build.ruleset, root)
            equipment = profile["hireling_equipment"]
            # A printed choice is part of the kit the profile carries: with no
            # explicit weapon the first listed option is the default, so the
            # kit's own weapon fills the hand instead of the free dagger.
            entries = [*equipment.get("fixed_items", ()), *equipment.get("unique_equipment", ())]
            for group in equipment.get("choices", ()):
                for option in group.get("options", ()):
                    entries.extend(option.get("items", ()))
                    entries.extend({"item_id": item_id}
                                   for item_id in (option.get("from_item_ids") or ())[:1])
            for entry in entries:
                counts_as = entry.get("counts_as")
                item_id = entry.get("item_id") or entry.get("id", "")
                canonical = counts_as.get("item_id") if isinstance(counts_as, dict) else counts_as
                mapped = item_mappings.get(str(item_id)) or item_mappings.get(str(canonical or ""))
                if mapped and weapon_mechanics.get(mapped, {}).get("main_hand"):
                    build = replace(build, main_weapon_id=mapped)
                    break
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
        # The catalogue's general fixed-equipment clause is the admission of
        # this very consumer: the kit matcher above refuses any ownership that
        # is not the complete printed kit.  A hireling compiled without the
        # clause has lost its prohibition, so the profile is refused instead
        # of quietly accepting extra equipment.
        if "compiler.hireling-fixed-equipment" not in automatic_compiler_contracts:
            raise ValueError(f"hireling profile is missing its fixed-equipment rule: {profile['id']}")
    selected_special_mechanics = []
    selected_profile_bindings = []
    selected_compiler_contracts = set()
    selected_compiler_bindings = []
    stat_bonuses = {}
    if package is not None:
        for rule in _applicable_rules(package, profile):
            if (rule.get("runtime") or {}).get("grant") == "selectable":
                continue
            for binding in runtime_bindings(rule, "profile"):
                if binding.get("id") != "profile.characteristics":
                    continue
                parameters = binding.get("parameters") or {}
                if parameters.get("profile_ids") and build.profile_id not in parameters["profile_ids"]:
                    continue
                for stat, bonus in _characteristic_bonus_block(
                        parameters.get("bonuses"), source=f"{rule['id']} binding profile.characteristics").items():
                    stat_bonuses[stat] = stat_bonuses.get(stat, 0) + bonus
    if build.special_rule_ids:
        rules = selected_rules(build, package, profile, root, automatic_compiler_contracts)
        # The Trapper's printed starting choice is construction fact; its four
        # options keep their own excluded runtime, so the selection is inert.
        veteran_tracker = any(
            binding.get("id") == "compiler.veteran-tracker-skill-choice"
            for rule in _applicable_rules(package, profile)
            for binding in runtime_bindings(rule))
        # Same construction-only pattern for the Mule Skinner's single Animal
        # Handling choice: the chosen member's own content is outside the duel,
        # so the selection is recorded and skipped instead of executed.
        animal_handler = {
            str(option)
            for rule in _applicable_rules(package, profile)
            for binding in runtime_bindings(rule)
            if binding.get("id") == "compiler.animal-handler-skill-choice"
            for option in (binding.get("parameters") or {}).get("options") or ()}
        # A repeated selection resolves once, so a duplicated id never applies
        # its bonuses or mechanics twice.
        for rule_id in dict.fromkeys(build.special_rule_ids):
            rule = rules.get(rule_id)
            if rule is None:
                raise ValueError(f"special rule is not available to {build.band_id}: {rule_id}")
            if veteran_tracker and rule_id in VETERAN_TRACKER_SKILLS:
                continue
            if rule_id in animal_handler:
                continue
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
    supplied_stat_bonuses = {}
    supplied_maxima = {}
    for binding in supplied.profile_bindings:
        if binding.get("id") != "profile.characteristics":
            continue
        parameters = binding.get("parameters") or {}
        for stat, bonus in _characteristic_bonus_block(
            parameters.get("bonuses"), source="supplied condition"
        ).items():
            supplied_stat_bonuses[stat] = supplied_stat_bonuses.get(stat, 0) + bonus
        # A printed bonus may carry its own ceiling (the Brewers' Special Brew
        # raises Weapon Skill and Strength "but never greater than 10").  The
        # limit belongs to the supplied result, so only the characteristics it
        # names are bounded.
        for stat, ceiling in (parameters.get("maximum") or {}).items():
            if stat not in CHARACTERISTIC_BONUS_KEYS or isinstance(ceiling, bool) or not isinstance(ceiling, int):
                raise ValueError(
                    f"supplied condition declares an invalid maximum for {stat!r}: {ceiling!r}")
            supplied_maxima[stat] = min(supplied_maxima.get(stat, ceiling), ceiling)
    characteristics = _apply_characteristic_bonuses(characteristics, supplied_stat_bonuses)
    if supplied_maxima:
        characteristics = replace(characteristics, **{
            stat: min(getattr(characteristics, stat), ceiling)
            for stat, ceiling in supplied_maxima.items()})
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
    ) + supplied.profile_bindings
    # A published natural-weapon grant is what dresses the fighter with claws
    # or jaws: the binding is the source's own declaration, not a hint the
    # compiler may infer from a missing dagger.  An explicit `profile.fist`
    # still wins below because that contract prints its own unarmed penalty
    # and critical range.
    if (any(binding.get("id") == "profile.natural-attacks" for binding in automatic_profile_bindings)
            # An explicit blade is still a choice the caller made: it must reach
            # the access check and be refused, not be swallowed by the grant.
            and build.main_weapon_id in {None, "weapon.dagger"}):
        main_weapon_id = "weapon.natural-attacks"
    if any(binding.get("id") == "profile.fist" for binding in automatic_profile_bindings):
        main_weapon_id = "weapon.fist"
    # A source that prints 'never uses weapons or armour' (or binds the same
    # prohibition) leaves the fighter without any weapon to carry; every other
    # profile that merely omits the free dagger keeps a printed empty hand.
    weaponless = any(
        binding.get("id") == "profile.equipment-restrictions"
        and any(str(token) in {"weapons", "equipment"} for token in
                ((binding.get("parameters") or {}).get("forbids") or ()))
        for binding in automatic_profile_bindings)
    if (profile is not None and not profile.get("hireling_equipment")
            and profile.get("fixed_equipment")
            and main_weapon_id not in {"weapon.dagger", "weapon.fist"}):
        # Selecting a printed blade explicitly keeps the same physical kit and
        # its coatings as the default selection; the UI's choice must not strip it.
        printed = _printed_kit(build, profile, mechanics, root)
        if (any(mid.startswith(("material.", "poison.")) for _, mid in printed)
                and any(mid == main_weapon_id for _, mid in printed)):
            build, _ = _printed_compound_kit(build, printed, mechanics)
    if (profile is not None and not profile.get("hireling_equipment")
            and build.main_weapon_id=="weapon.dagger"
            and main_weapon_id=="weapon.dagger"):
        allowed=set(desktop_call("equipment", build, root, package=package, profile=profile))
        fixed=set(profile.get("fixed_equipment") or ())
        if fixed:
            # A kit that prints a weapon qualification or a coating prints the
            # compound itself, so its own copies fill the hands ('two dark
            # elven blades coated in dark venom' is a main blade and a second
            # one) before the qualification and coating revest them.  A kit
            # that prints neither keeps the shared choice among the weapons its
            # access admits, so no other profile's loadout changes.
            printed=_printed_kit(build, profile, mechanics, root)
            if any(mid.startswith(("material.", "poison.")) for _, mid in printed):
                build, weapon_ids = _printed_compound_kit(build, printed, mechanics)
            else:
                weapon_ids=sorted(mid for mid in allowed if mid.startswith("weapon."))
            if weapon_ids:main_weapon_id=weapon_ids[0]
        elif not profile.get("equipment_lists"):
            main_weapon_id="weapon.natural-attacks"
        elif ("weapon.dagger" not in allowed
                # The profile's own printed restriction may refuse the free
                # dagger ('cannot be equipped with weapons'); the shared
                # decision answers.  A profile that can still carry some
                # other close-combat weapon keeps an ordinary empty hand:
                # only a source that prints no weapon at all fights with its
                # natural attacks, so the free-dagger absence never becomes a
                # better identity with no unarmed penalty.
                or desktop_call("implicitWeapon", build, root, package=package, profile=profile) is not None):
            main_weapon_id=("weapon.natural-attacks" if weaponless else "weapon.fist")
    elif (profile is not None and build.main_weapon_id == "weapon.fist"
            and not profile.get("equipment_lists")
            and not profile.get("fixed_equipment")
            and not any(binding.get("id") == "profile.fist" for binding in automatic_profile_bindings)):
        # A neutral empty hand on an unequippable creature is its natural
        # attack, just like the default dagger selection above. Explicit
        # profile.fist contracts retain their own unarmed semantics.
        main_weapon_id = "weapon.natural-attacks"
    if ((build.main_poison_id and main_weapon_id in {"weapon.fist", "weapon.natural-attacks"})
            or (build.off_poison_id and (not (build.off_hand_id or "").startswith("weapon.")
                                        or build.off_hand_id in {"weapon.fist", "weapon.natural-attacks"}))):
        # A coating needs a weapon to carry it.  The selection layer offers no
        # poison to a fighter with no weapon, so the direct path refuses one
        # instead of quietly poisoning a fist or a claw.
        raise ValueError("a poison needs a carried weapon in the hand it coats")
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
    if build.armour_id == "armour.attlas-plate-mail":
        characteristics = _apply_characteristic_bonuses(characteristics, {"wounds": 1})
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
    # Printed arm restrictions of the campaign mutations (Cult of the Possessed
    # and its trollheim twin), decided where the loadout and the catalogue rows
    # meet.  Extra Arm: 'The mutant may use any single-handed weapon in the
    # extra arm, giving him +1 attack when fighting in hand-to-hand combat.
    # Alternatively, he may carry a shield or a buckler in the extra arm.  If a
    # Possessed chooses to do this, he gains an extra attack but still cannot
    # carry a weapon.'  The shield and buckler alternatives are not judged
    # here: the same clause grants them even to a Possessed.  Great Claw: 'He
    # may carry no weapons in this arm', one of the mutant's arms.
    if build.extra_hand_id and build.extra_hand_id.startswith("weapon."):
        if build.extra_hand_id not in {"weapon.fist", "weapon.natural-attacks"}:
            extra_hand = mechanics[build.extra_hand_id]
            if int(extra_hand.get("hands") or 1) == 2 or extra_hand.get("paired"):
                raise ValueError("the extra hand may carry only a one-handed weapon")
            if package is not None and profile is not None:
                available = set(desktop_call("equipment", build, root, package=package, profile=profile))
                if build.extra_hand_id not in available:
                    raise ValueError(
                        f"equipment is not available to {build.band_id}/{build.profile_id}: "
                        f"['{build.extra_hand_id}']"
                    )
    if "band--mutations-great-claw" in build.special_rule_ids:
        weapon_arms = 1 + int("band--mutations-extra-arm" in build.special_rule_ids)
        occupied_arms = sum(
            max(int(mechanics[mid].get("hands") or 1), 2 if mechanics[mid].get("paired") else 1)
            for mid in (main_weapon_id, build.off_hand_id, build.extra_hand_id)
            if mid and mid.startswith("weapon.")
            and mid not in {"weapon.fist", "weapon.natural-attacks"})
        if occupied_arms > weapon_arms:
            raise ValueError("the Great Claw arm may carry no weapon")
    if build.armour_id == "armour.cathayan-quilted-silk":
        raise ValueError("Cathayan quilted silk is an armour overlay and belongs in defence_ids")
    handed={"defence.shield","defence.buckler","defence.kite-shield"}
    if handed.intersection(build.defence_ids):raise ValueError("hand-held defences belong in off_hand_id")
    if package is not None:_validate_profile_selections(
        build,package,profile,root,main_weapon_id,
        (*selected_profile_bindings, *automatic_profile_bindings),compiler_contracts,compiler_bindings)
    elif supplied.profile_bindings:
        validate("boundEquipment", build, root, main_weapon_id=main_weapon_id,
                 profile_bindings=supplied.profile_bindings)
    if package is not None and build.owned_item_ids is not None:
        facts = configuration_context(build, package, profile, root=root, possession=build.owned_item_ids,
            profile_bindings=supplied.profile_bindings,
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
    # Weapons Training is a supplied permission, not an executable mechanic:
    # where the bearer's clause prints the exception, the skill's own catalogue
    # disposition does not forbid carrying the permission that grants access.
    if "compiler.weapons-training-exception" in compiler_contracts:
        unavailable=[mechanic for mechanic in unavailable if mechanic != "skill.weapons-training"]
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
    for key in ("stupidity_leadership", "stupidity_leadership_bonus", "mob_allies"):
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
        *build.defence_ids, # re-appended below; a defence carried once must not stack twice
    }]
    global_ids += list(profile_rule_skills)
    global_ids += selected_special_mechanics
    global_ids += list(supplied.mechanic_ids)
    # A printed Weapons Training permission is a supplied fact, not an
    # executable effect: the bearer's clause owns the access it opens.
    if "compiler.weapons-training-exception" in compiler_contracts:
        global_ids = [item for item in global_ids if item != "skill.weapons-training"]
    innate_ids = [*build.skill_ids, *build.preparation_ids, *profile_rule_skills,
                  *selected_special_mechanics, *supplied.mechanic_ids]
    if "compiler.weapons-training-exception" in compiler_contracts:
        innate_ids = [item for item in innate_ids if item != "skill.weapons-training"]
    innate_ids = [item for item in innate_ids if item != "condition.executioners-hood"]
    # A printed rule may name a mechanic the bearer implements with a physical
    # item of his own kit: the Wolf-Priest's pelt is the item that grants his 6+
    # save, not an equipment-free quality of the priest.  Such a contribution
    # belongs to the piece, so it leaves the equipment-free provenance while the
    # carried item keeps granting it once, even when it is also selected
    # explicitly (its stacking is "once").
    resolve_item_mechanic = _item_mechanic_resolver(build, profile, mechanics, root)
    carried_mechanics = {resolve_item_mechanic(item) for item in kit}
    innate_ids = [item for item in innate_ids if item not in carried_mechanics]
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
    # Holy Relics: a Battle Pilgrim who owns a relic gains Frenzy, so the grant
    # follows the physical piece (equipment provenance) and only the recipients
    # the rule itself names.
    if ("compiler.holy-relic-frenzy" in compiler_contracts
            and carried_items.intersection({"holy_relic", "holy_relic_pilgrim_only"})):
        global_ids.append("mechanic.holy-relic-frenzy")
    # Fanatical: the source promotes only some Heroes of the Watch into Knights
    # of Purity, so the grant needs both the supplied promotion fact and the
    # rule itself; the band's other members keep rolling their Leadership tests.
    if "compiler.knight-of-purity" in compiler_contracts and traits.get("crusader_of_law"):
        if profile.get("type") != "hero" and "promotion.hero" not in build.variant_ids:
            raise ValueError("crusader_of_law requires a Hero of the Watch")
        global_ids.append("mechanic.automatic-leadership")
    global_ids += [build.armour_id, *build.defence_ids]
    if build.off_hand_id and build.off_hand_id.startswith("defence."):
        global_ids.append(build.off_hand_id)
    drug_ids = {"preparation.crimson-shade", "preparation.mandrake-root",
                "preparation.mad-cap-mushrooms", "preparation.head-splitter-mushrooms",
                "condition.fungus-brew-rowdy", "condition.fungus-brew-dizzy",
                "condition.fungus-brew-fearless", "condition.fungus-brew-numbed",
                "condition.fungus-brew-belligerent", "condition.fungus-brew-loony"}
    if "mechanic.drug-immunity" in global_ids:
        global_ids = [item for item in global_ids if item not in drug_ids]
        innate_ids = [item for item in innate_ids if item not in drug_ids]
    if (traits.get("creature_kind") in {"undead", "possessed"}
            or traits.get("undead_or_possessed")
            or traits.get("undead") or traits.get("possessed")
            or "mechanic.undead" in global_ids):
        inert = {"preparation.crimson-shade", "preparation.mad-cap-mushrooms"}
        global_ids = [item for item in global_ids if item not in inert]
        innate_ids = [item for item in innate_ids if item not in inert]
    if "preparation.crimson-shade" in global_ids and characteristics.movement is not None:
        characteristics = replace(characteristics, movement=characteristics.movement + 1)
    if "condition.fungus-brew-dizzy" in global_ids and characteristics.initiative is not None:
        characteristics = replace(characteristics, initiative=characteristics.initiative - 1)
    global_effects = apply_execution_effects(global_effects, global_ids, effects, "passive", "fighter")
    global_effects = apply_execution_effects(global_effects, global_ids, effects, "duel_start", "fighter")
    if traits.get("metal_armour") and not (
        build.armour_id != "armour.no-armour"
        or "defence.helmet" in build.defence_ids
        or build.off_hand_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}
        or build.extra_hand_id in {"defence.shield", "defence.buckler"}
    ):
        raise ValueError("metal_armour requires an actual worn armour, helmet, shield or buckler")
    if traits.get("metal_armour") or build.armour_id in METAL_ARMOUR_IDS:
        global_effects = merge_effects(global_effects, EffectSet(tags=("condition.metal-armour",)))
    global_effects_without_equipment = apply_execution_effects(
        EffectSet(), innate_ids, effects, "passive", "fighter")
    global_effects_without_equipment = apply_execution_effects(
        global_effects_without_equipment, innate_ids, effects, "duel_start", "fighter")
    selected_skill_mechanics = [
        str(binding["id"])
        for rule in (package.special_rules if package is not None else ())
        if rule.get("kind") == "warband_skill" and rule["id"] in build.special_rule_ids
        for binding in runtime_bindings(rule, "mechanic")
    ]
    skill_effects_ids = [*build.skill_ids, *selected_skill_mechanics]
    if "compiler.weapons-training-exception" in compiler_contracts:
        skill_effects_ids = [item for item in skill_effects_ids if item != "skill.weapons-training"]
    skill_effects_only = apply_execution_effects(
        EffectSet(), skill_effects_ids, effects, "passive", "fighter")
    for skill_id in traits.get("starting_skills") or ():
        if skill_id not in effects:
            from mordheim_knowledge.loader import load_skills
            source_skill = next((r for r in load_skills(build.ruleset, root) if r['id'] == skill_id), None)
            if source_skill is not None and (source_skill.get('runtime') or {}).get('scope') == 'NO':
                continue
            raise ValueError(f"profile references unknown or unsupported starting skill ID: {skill_id}")
        global_effects = apply_execution_effects(global_effects, (skill_id,), effects, "passive", "fighter")
        global_effects_without_equipment = apply_execution_effects(
            global_effects_without_equipment, (skill_id,), effects, "passive", "fighter")
        skill_effects_only = apply_execution_effects(skill_effects_only, (skill_id,), effects, "passive", "fighter")
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
        # The promoted band id is `mazzalupo-web`; the printed warband is its
        # canonical family, which is also what the band package declares.
        if package is not None and (package.band.get("canonical_family") or build.band_id) != "mazzalupo":
            raise ValueError("an active Mazzalupo Command requires a Mazzalupo recipient")
        trait_tags = (*trait_tags, f"condition.command.{command}")
    sex = traits.get("sex")
    if sex is not None:
        if sex not in {"male", "female"}:
            raise ValueError(f"unknown sex: {sex}")
        trait_tags = (*trait_tags, f"sex.{sex}")
    if traits.get("greenskin"):
        trait_tags = (*trait_tags, "identity.greenskin")
    species = traits.get("species")
    if species is not None:
        if species not in {"human", "dwarf", "skaven", "orc", "goblin", "halfling", "ogre", "beastman", "snake", "serpent"}:
            raise ValueError(f"unknown species: {species}")
        trait_tags = (*trait_tags, f"species.{species}")
        if species in {"snake", "serpent"}:
            trait_tags = (*trait_tags, "species.animal")
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
    # Ashamed and Afraid names two concrete opponents, not every Sigmarite:
    # a member of a Sisters of Sigmar warband, or the Warrior-Priest of a
    # Witch Hunters warband.  The tag is the opponent's supplied identity.
    if (build.band_id == "sisters-of-sigmar"
            or build.band_id in {"witch-hunters", "trollheim-witch-hunters"}
            and build.profile_id == "warrior-priest"):
        trait_tags = (*trait_tags, "identity.sigmarite-opponent")
    if traits.get("onogal_follower") or traits.get("mark_of_onogal_the_crow"):
        trait_tags = (*trait_tags, "identity.onogal-follower")
    if traits.get("chaos_follower"):
        trait_tags = (*trait_tags, "identity.chaos-follower")
    if traits.get("aquatic"):
        trait_tags = (*trait_tags, "species.aquatic")
    if traits.get("slave") or (build.band_id == "skaven-of-clan-skryre-rel" and build.profile_id == "skaven-slaves"):
        trait_tags = (*trait_tags, "identity.slave")
    # Free the Slaves! needs the opponent's own slaver identity, supplied by the
    # caller; no band grant, slave-driving aura or campaign producer is read here.
    if traits.get("slaver"):
        trait_tags = (*trait_tags, "identity.slaver")
    # Supplied instance identities: the caller names one warrior and the warband
    # instance it belongs to with its own keys.  They stay supplied facts, never
    # catalogue ids, so two warriors of one profile and two rosters built from
    # one catalogue list remain distinct; a warrior supplied neither carries no
    # instance identity at all.
    for key in ("instance_id", "warband_instance"):
        value = traits.get(key)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"combat trait {key} must be a non-empty supplied identity")
    instance = str(traits.get("instance_id") or "").strip()
    if instance:
        trait_tags = (*trait_tags, f"instance.{instance}")
    warband_instance = str(traits.get("warband_instance") or "").strip()
    if warband_instance:
        trait_tags = (*trait_tags, f"warband-instance.{warband_instance}")
    # Vengeful Hatred (Bitter Enmity): the campaign's further D6 and the player
    # determined which enemy the warrior permanently hates, so the duel is
    # supplied the printed kind of target and that concrete identity.  Three of
    # the four kinds name an instance -- the warrior who caused the injury, that
    # warrior as its warband's leader, or the warband instance -- and only the
    # fourth, every warband of a type, is a category.  A half-supplied pair or an
    # empty identity is refused rather than guessed, and nothing here grants
    # Hatred without a target.
    enmity_kind, enmity_target = traits.get("enmity_kind"), traits.get("enmity_target")
    if (enmity_kind is None) != (enmity_target is None):
        raise ValueError(
            "Bitter Enmity needs the supplied target kind and its concrete identity together")
    if enmity_kind is not None:
        if enmity_kind not in {"individual", "leader", "warband", "warband-type"}:
            raise ValueError(f"unknown Bitter Enmity target kind: {enmity_kind}")
        target = enmity_target.strip()
        if not target:
            raise ValueError("Bitter Enmity needs the concrete identity the injury determined")
        if enmity_kind != "warband-type" and any(character.isspace() for character in target):
            raise ValueError("Bitter Enmity's instance target is one supplied identity key")
        trait_tags = (*trait_tags, "mechanic.vengeful-hatred",
                      f"enmity-target.{enmity_kind}.{target}")
    if traits.get("scourge_armed") or "weapon.pirate-scourge" in (main_weapon_id, build.off_hand_id):
        trait_tags = (*trait_tags, "condition.scourge-armed")
    if traits.get("devoted_vampire_down"):
        trait_tags = (*trait_tags, "condition.devoted-vampire-down")
    if traits.get("devoted_vampire_killed"):
        trait_tags = (*trait_tags, "condition.devoted-vampire-killed")
    if traits.get("spellcaster"):
        trait_tags = (*trait_tags, "identity.spellcaster")
    if traits.get("necromancer"):
        trait_tags = (*trait_tags, "identity.necromancer")
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
    disability_results = set(supplied.condition_ids).intersection(
        {f"condition.disability-{result}" for result in range(1, 7)})
    if "mechanic.disability" in global_effects.tags and not disability_results:
        raise ValueError("Disability requires one permanent supplied result (condition.disability-1..6)")
    if disability_results and "mechanic.disability" not in global_effects.tags:
        raise ValueError("Disability result requires a Cripple with Disability")
    if "condition.disability-hero-nearby" in supplied.condition_ids and "condition.disability-6" not in disability_results:
        raise ValueError("Nearby Hero exemption requires Head Injury result 6")
    if "condition.ye-give-way-refused" in supplied.condition_ids and fighter_kind != "hero":
        raise ValueError("Ye Give Way refusal requires the challenged Hero recipient")
    if "condition.ye-give-way-victorious" in supplied.condition_ids and (
            build.band_id != "mazzalupo-web" or build.profile_id != "fallen-noble"):
        raise ValueError("Ye Give Way victory requires a Fallen Noble recipient")
    if "defence.magic-acorn" in build.defence_ids and fighter_kind != "hero":
        raise ValueError("the Magic Acorn may only be carried by a Hero")
    if set(supplied.condition_ids).intersection({"condition.witch-debilitating", "condition.witch-strength",
            "condition.witch-resilience", "condition.witch-fortitude"}) and fighter_kind != "hero":
        raise ValueError("A Witch potion requires a Hero recipient")
    if any(condition.startswith("condition.petru-") for condition in supplied.condition_ids) and fighter_kind != "hero":
        raise ValueError("Petru's supplied draught requires a Hero recipient")
    if any(condition.startswith("condition.alchemist-") for condition in supplied.condition_ids) and (
        build.band_id != "masters-of-horror-sylv" or build.profile_id != "mad-scientist"
    ):
        raise ValueError("the Alchemist's supplied potion requires the Mad Scientist recipient")
    if any(condition.startswith("condition.troll-brew-") for condition in supplied.condition_ids) and (
        build.collection != "mordheim" or build.band_id != "dwarf-guildsmen-kaz"
        or fighter_kind != "hero" or traits.get("species") not in (None, "dwarf")
    ):
        raise ValueError("only a Dwarf of the Guildsmen brewers may drink the supplied brew; the recipient must be a Hero")
    if any(condition.startswith("condition.power-grab-") for condition in supplied.condition_ids) and (
        build.collection != "mordheim" or build.band_id != "underworld-alliance-mim"
    ):
        raise ValueError("the supplied Power Grab adjustment requires an Underworld Alliance duelist")
    if any(condition in {"condition.rememberer-kaz-support", "condition.rememberer-web-support"}
           for condition in supplied.condition_ids):
        expected_band = ("dwarf-slayers-kaz" if "condition.rememberer-kaz-support" in supplied.condition_ids
                         else "dwarf-slayer-cult-web")
        if build.band_id != expected_band or fighter_kind != "hero" or not any(
            "identity.slayer" in effects[mid].effect.tags for mid in loadout_mechanics if mid in effects
        ):
            raise ValueError("Rememberer support requires a Slayer Hero of the printed source variant")
    if "condition.impetuous-charge" in supplied.condition_ids and (
        build.band_id != "bretonnian-chapel-guard" or build.profile_id != "knights-errant"
    ):
        raise ValueError("a compelled Impetuous charge requires a Knight Errant recipient")
    if "condition.summoned-this-turn" in supplied.condition_ids and (
        build.band_id != "call-of-the-night-haint-mim" or build.profile_id != "malignant-spirits"
    ):
        raise ValueError(
            "a supplied summon turn requires a Malignant Spirits recipient of the Call of the Night Haint")
    if "condition.tomb-robber-dodge-known" in supplied.condition_ids and (
        build.profile_id != "hireling.hired-sword.tomb-robber"
    ):
        raise ValueError("the Dodge upgrade requires the Tomb Robber's Excellent Reflexes")
    if "condition.witch-finder-charge" in supplied.condition_ids and (
        "deity.solkan" not in build.variant_ids
        or "hireling.hired-sword.priest-of-verena.skill.witch-finder" not in build.special_rule_ids
    ):
        raise ValueError("the compulsory Witch-finder charge requires the chosen Mark of Solkan")
    if "condition.bear-handler-nearby" in supplied.condition_ids and (
        build.band_id != "kislevites" or build.profile_id != "trained-bear"
    ):
        raise ValueError("the nearby Bear Tamer waiver requires the native Trained Bear")
    if "condition.adventurer-barbarian-leader" in supplied.condition_ids and (
        build.band_id != "adventurers-kaz" or build.profile_id != "barbarian"
    ):
        raise ValueError("the chosen Barbarian Leader must be the native Adventurer Barbarian")
    if "condition.poetry-victorious-leader" in supplied.condition_ids and (
        build.band_id not in {"ghutani-rel", "muzil-rel", "turjuk-rel"} or build.profile_id != "emir"
    ):
        raise ValueError("victorious Poetry requires the actual Leader of its printed Araby band")
    if "condition.nuttaz-charge" in supplied.condition_ids and (
        build.band_id != "black-orcs" or build.profile_id != "orc-nuttaz"
    ):
        raise ValueError("the required Nuttaz charge needs the native Orc Nuttaz")
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
    intrinsic_effects = EffectSet(
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
        natural_armour_negated_by_fire=bool(traits.get("natural_armour_negated_by_fire",False)),
        regeneration_blocked_by_fire=bool(traits.get("regeneration_blocked_by_fire",False)),
        regeneration_blocked_by_blessed=bool(traits.get("regeneration_blocked_by_blessed",False)),
        caught_fire_threshold=int(traits.get("caught_fire_threshold",7)),
        armour_penetration=int(bool(traits.get("perfect_killer",False))))
    global_effects = merge_effects(global_effects, intrinsic_effects)
    global_effects_without_equipment = merge_effects(
        merge_effects(global_effects_without_equipment, intrinsic_effects),
        merge_effects(automatic_rule_effects, selected_special_effects))
    global_effects = merge_effects(merge_effects(global_effects, automatic_rule_effects), selected_special_effects)
    if "mechanic.spawn-special-attacks" in global_effects.tags:
        # The printed Special Attacks clause rolls the Spawn's Attacks at the
        # beginning of each Close Combat phase.  Its profile writes A as D6+1,
        # but that expression is the clause's own roll, not a characteristic
        # fixed at duel start: the phase operator owns it, so the duel must not
        # ask for the same number twice (once here and once per round).
        random_characteristics = tuple(row for row in random_characteristics if row[0] != "A")
    if traits.get("devoted_vampire_down") or traits.get("devoted_vampire_killed"):
        if "mechanic.devoted-to-the-vampire" not in global_effects.tags:
            raise ValueError("supplied Vampire condition requires Devoted to the Vampire")
        if traits.get("devoted_vampire_down") and traits.get("devoted_vampire_killed"):
            raise ValueError("the supplied Vampire cannot be both Knocked Down and killed")
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
    # An intrinsic unique-item rule connects its own active weapon operator;
    # it is not a second weapon contribution or a bonus on every other hand.
    profile_attack_effects = [mid for mid in profile_rule_skills if not mid.startswith("weapon.")]
    main_ids=[main_weapon_id, build.main_material_id, *profile_attack_effects]
    main_without_poison = (apply_execution_effects(EffectSet(), main_ids, effects, "attack", "attack")
                           if build.main_poison_id else None)
    if build.main_poison_id: main_ids.append(build.main_poison_id)
    main_effect=apply_execution_effects(EffectSet(), main_ids, effects, "attack", "attack")
    if "stance.wall-of-steel" in build.variant_ids:
        main_effect = replace(main_effect, two_handed=True, parry=True)
        if main_without_poison is not None:
            main_without_poison = replace(main_without_poison, two_handed=True, parry=True)
    if build.profile_id == "hireling.hired-sword.chaos-centaur" and main_weapon_id == "weapon.spear":
        main_effect = replace(main_effect, charge_strength_bonus=main_effect.charge_strength_bonus + 1)
    if "mechanic.ogre-unarmed" in global_effects.tags and main_weapon_id in {"weapon.fist", "weapon.natural-attacks"}:
        main_effect = replace(effects["weapon.fist"].effect, strength_bonus=0)
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
        off_ids=[build.off_hand_id, build.off_material_id, *profile_attack_effects]
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
    if "mechanic.centaur-trample" in global_effects.tags:
        extra_attacks.append(EffectSet(tags=("weapon.natural-attacks", "rule.trample")))
    # Spiked Tail: one repeated natural tail attack in each close-combat phase at
    # the bearer's Strength +1.  Fimir Warriors and Young Nobles print the same
    # clause, so one profile contribution carries both recipients.
    if automatic_rule_ids & {"fimir-warriors--spiked-tail", "young-nobles--spiked-tail"}:
        extra_attacks.append(EffectSet(tags=("rule.spiked-tail",), strength_bonus=1))
    # Sword-Gnoblar: the carried gnoblar adds one Strength 2 close-combat attack
    # made at the owning model's Weapon Skill, resolved with the bearer's own
    # attacks (the sole opponent is the directed target in a duel).
    if "sword_gnoblar" in carried_items:
        extra_attacks.append(EffectSet(tags=("rule.sword-gnoblar",), fixed_strength=2))
    if "compiler.bite-attack" in automatic_compiler_contracts:
        extra_attacks.append(EffectSet(
            tags=("weapon.natural-attacks", "rule.bite-attack"),
            strength_bonus=int(bool(traits.get("huge_jaws", False))),
        ))
    if "compiler.strikes-last-bite" in automatic_compiler_contracts:
        extra_attacks.append(EffectSet(tags=("weapon.natural-attacks", "rule.strikes-last-bite")))
    if "mechanic.beak" in global_effects.tags and not any(
        "rule.bite-attack" in attack.tags or "rule.strikes-last-bite" in attack.tags
        for attack in extra_attacks
    ):
        extra_attacks.append(EffectSet(tags=("weapon.natural-attacks", "rule.strikes-last-bite")))
    if "mechanic.prehensile-tail" in global_effects.tags:
        # The equipped tail replaces other tail attacks for the whole phase;
        # a bare tail adds an attack only when there was no existing tail.
        tail_tags = {"rule.spiked-tail", "rule.scorpion-tail", "rule.prehensile-tail"}
        existing_tail = any(tail_tags.intersection(attack.tags) for attack in extra_attacks)
        if build.extra_hand_id:
            extra_attacks = [attack for attack in extra_attacks if not tail_tags.intersection(attack.tags)]
        elif not existing_tail:
            extra_attacks.append(EffectSet(tags=("weapon.natural-attacks", "rule.prehensile-tail")))
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
    if sum(1 for mid in build.defence_ids if mid in SEA_DRAGON_CLOAK_MECHANIC_IDS) > 1:
        raise ValueError("a warrior carries one Sea Dragon cloak, not a stack of cloak variants")
    natural_armour_save=int(traits.get("natural_armour_save") or 7)
    # Toughened Leathers cannot combine with other armour except a helmet or
    # buckler. A natural armour clause saying it combines normally does not
    # waive that item restriction. Keep the natural save, cancel the leather's
    # contribution, and retain permitted helmet/buckler modifiers.
    if (traits.get("natural_armour_stacks") and int(traits.get("natural_armour_save") or 7) <= 6
            and build.armour_id == "armour.toughened-leathers"):
        armour_save+=1
    if traits.get("natural_armour_stacks") and natural_armour_save<=6:
        armour_save-=7-natural_armour_save
    # Printed "no save except shields or skills" clause: the saves a defender
    # keeps when every other source is denied.  ``armour_save`` and
    # ``global_effects`` mix contributions by provenance (a pelt cloak, a
    # mechanic-granted bonus, a supplied trait all reach the same fields), so
    # the shield and skill selections are merged on their own instead of being
    # inferred from the composite total.  The printed Cloak-and-Dagger trait
    # makes its bearer "count as using a shield", so it belongs with the
    # shields, and the mounted kite shield keeps the extra point the composite
    # save also carries.
    # ``effects`` only carries executable mechanics: a profile skill whose
    # runtime scope is NO (Dodge, Leap, Acrobat) is skipped above and has no
    # contribution to merge, so it is filtered out here as well.
    shield_and_skill_ids = tuple(dict.fromkeys(
        mechanic_id
        for mechanic_id in (*global_ids, *(traits.get("starting_skills") or ()))
        if mechanic_id in effects
        and (mechanic_id.startswith("skill.")
             or mechanic_id in {"defence.shield", "defence.buckler", "defence.kite-shield"})
    ))
    shield_and_skill_effects = apply_execution_effects(
        EffectSet(), shield_and_skill_ids, effects, "passive", "fighter")
    shield_and_skill_effects = apply_execution_effects(
        shield_and_skill_effects, shield_and_skill_ids, effects, "duel_start", "fighter")
    if traits.get("counts_as_shield"):
        shield_and_skill_effects = merge_effects(
            shield_and_skill_effects, EffectSet(armour_save_bonus=1))
    if build.off_hand_id == "defence.kite-shield" and build.mounted:
        shield_and_skill_effects = merge_effects(
            shield_and_skill_effects, EffectSet(armour_save_bonus=1))
    missile_weapon_limit=1 if "compiler.bow-discipline" in compiler_contracts else 5 if "compiler.master-of-throwing-weapons" in compiler_contracts else 2
    construction_tags=tuple(sorted(compiler_contracts))
    ballistic_skill=int((profile.get("characteristics") or {}).get("BS") or 0) if profile is not None else 0
    if "condition.disability-3" in supplied.condition_ids:
        ballistic_skill = max(0, ballistic_skill - 1)
    if traits.get("stupidity_initial_failed") and not ("mechanic.stupidity" in global_effects.tags):
        raise ValueError("initial failed Stupidity requires an active Stupidity condition")
    if "stupidity_leadership" in traits and "mechanic.handler-leadership" not in global_effects.tags:
        raise ValueError("Handler Leadership requires a handler-only Leadership rule")
    if traits.get("stupidity_leadership_bonus", 0) and "mechanic.brood-mentality" not in global_effects.tags:
        raise ValueError("Stupidity Leadership bonus requires Brood Mentality")
    if traits.get("mob_allies", 0) and "mechanic.mob-leadership" not in global_effects.tags:
        raise ValueError("Mob Leadership bonus requires the Mob rule")
    mutation_options = (_prepared_mutation_options(build.ruleset, effects, root)
                        if "mechanic.solkan-inquisitor" in global_effects.tags else ())
    mutation_equipment = _mutation_equipment(build, profile, kit, main_weapon_id, main_effect, off_effect,
        mechanics, effects, root, metal_worn=bool(traits.get("metal_armour")))
    compiled = CompiledFighter(f"{build.band_id or 'custom'}:{build.profile_id or 'custom'}",characteristics,main_effect,off_effect,global_effects,max(1,armour_save),4 if "defence.helmet" in build.defence_ids else 5 if "defence.cooking-pot-helmet" in build.defence_ids else 7,natural_armour_save,bool(build.off_hand_id and build.off_hand_id.startswith("weapon.")),bool(traits.get("natural_armour_unmodified",False)),int(traits.get("injury_profile") or 0),random_characteristics,natural_armour_worst_save=int(traits.get("natural_armour_worst_save") or 7),extra_attacks=tuple(extra_attacks),missile_weapon_limit=missile_weapon_limit,ballistic_skill=ballistic_skill,construction_tags=construction_tags,main_weapon_without_poison=main_without_poison,off_hand_without_poison=off_without_poison,mounted=build.mounted,unarmed_weapon=(replace(effects["weapon.fist"].effect, strength_bonus=0) if "mechanic.ogre-unarmed" in global_effects.tags else effects["weapon.fist"].effect),vomit_attack=vomit_attack, shield_and_skill_effects=shield_and_skill_effects, stupidity_leadership=traits.get("stupidity_leadership"), stupidity_leadership_bonus=traits.get("stupidity_leadership_bonus", 0), mob_allies=int(traits.get("mob_allies") or 0), animal_handler_leadership=handler_value, skill_effects_only=skill_effects_only, global_effects_without_equipment=global_effects_without_equipment, mutation_options=mutation_options, mutation_equipment=mutation_equipment, natural_armour_stacks=bool(traits.get("natural_armour_stacks", False)))
    from mordheim_construction.runes import apply_item_modifiers
    bindings = (*automatic_profile_bindings, *selected_profile_bindings)
    compiled = apply_item_modifiers(compiled, bindings, effects, traits)
    from mordheim_construction.equipment_preparations import apply_maintenance
    return apply_maintenance(compiled, bindings, profile)
