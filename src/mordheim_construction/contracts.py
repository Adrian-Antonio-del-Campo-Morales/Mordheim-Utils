"""construction.contracts: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from dataclasses import fields
from functools import lru_cache
from mordheim_core.effects import ExecutionEffect
from mordheim_core.models import EffectSet
from mordheim_knowledge.loader import load_execution_contract
from mordheim_knowledge.loader import load_mechanics
from pathlib import Path


COLLECTIONS = ("weapons","armours","defences","materials","preparations","poisons","skills")


EFFECT_FIELDS = {field.name for field in fields(EffectSet)}


TRAIT_TYPES = {
    "starting_skills": (list,tuple), "natural_armour_save": int, "injury_profile": int,
    "ward_save": int, "regeneration_save": int,
    "extra_natural_attacks": int, "poison_immune": bool, "undead_or_possessed": bool,
    "frenzy": bool, "cloud_of_flies": bool, "natural_armour_stacks": bool,
    "charge_attack_bonus": bool, "first_round_charge_attack_bonus": bool, "maddened_with_pain": bool,
    "natural_armour_unmodified": bool, "poisonous_injury": bool, "survivor": bool,
    "natural_armour_worst_save": int,
    "concussion_immune": bool, "wight_blades": bool, "perfect_killer": bool,
    "counts_as_buckler": bool, "counts_as_shield": bool, "fragile_halflings": bool,
    "flammable": bool,
    "ward_save_mundane_only": bool,
    "natural_armour_negated_by_magic": bool,
    "magical_attacks": bool,
    "regeneration_blocked_by_fire": bool,
    "regeneration_blocked_by_blessed": bool,
    "caught_fire_threshold": int,
    "injury_reroll_out": bool,
    "dagger_master": bool,
    "spiritual_weapons": bool,
    "bear_hug": bool,
    "acid_blood": bool,
    "spines": bool,
    "scorpion_tail": bool,
    "huge_jaws": bool,
    "pit_fighter": bool,
    "animal_friendship": bool,
    "contagious": bool,
    "guardian_unarmed": bool,
    "mark_of_onogal_the_crow": bool,
}


COMPILER_CONTRACTS = {
    "compiler.no-blackpowder-weapons",
    "compiler.ignore-difficult-to-use-restrictions",
    "compiler.censer-bearer-loadout",
    "compiler.forbid-item-categories",
    "compiler.mutant-requires-mutation-at-recruitment",
    "compiler.swabbie-rabble-loadout",
    "compiler.promoted-hero-skill-access",
    "compiler.pit-fighter-fighting-styles",
    "compiler.no-missile-weapons",
    "compiler.promoted-hero-no-strength-access",
    "compiler.blessings-of-nurgle",
    "compiler.bow-discipline",
    "compiler.chaos-engineer",
    "compiler.chivalry",
    "compiler.choose-a-bloodline",
    "compiler.disciple-of-sigmar",
    "compiler.follow-the-darkest-tribe",
    "compiler.foreign-or-native-background",
    "compiler.haughty",
    "compiler.pirate-human-mercenary-equipment-access",
    "compiler.knighthood",
    "compiler.master-of-arms",
    "compiler.master-of-throwing-weapons",
    "compiler.mutation-purchase-at-recruitment",
    "compiler.bite-attack",
    "compiler.berserker-incompatible-with-ferocious-charge",
    "compiler.possessed-optional-mutations-at-recruitment",
    "compiler.possessed-optional-zero-to-two-mutations-at-recruitment",
    "compiler.no-arcane-lore",
    "compiler.nurgle-s-blessings",
    "compiler.powder-s-expensive",
    "compiler.promotions",
    "compiler.proud-to-a-fault",
    "compiler.proven-warrior",
    "compiler.quick-reload",
    "compiler.renowned-virtue",
    "compiler.sacred-marks",
    "compiler.saurus-skill-prohibitions",
    "compiler.slayer-skill-options",
    "compiler.strictures",
    "compiler.tracker-gear",
    "compiler.vampiric-powers",
    "compiler.warrior-wizard",
    "compiler.warrior-s-code",
    "compiler.weapon-knowledge",
    "compiler.lizardmen-scaly-skin",
}


BLACKPOWDER_WEAPONS = {"weapon.pistol", "weapon.duelling-pistol"}


MISSILE_WEAPONS = BLACKPOWDER_WEAPONS


DRUG_PREPARATIONS = {
    "preparation.crimson-shade", "preparation.mandrake-root",
    "preparation.mad-cap-mushrooms", "preparation.head-splitter-mushrooms",
}


SPECIAL_RULE_EFFECTS = {
    "band--beastmen-special-skills-mutant": {},
    "band--marauder-special-skills-mutant": {},
    "band--mutations-tentacle": {"effects": {"incoming_attacks_modifier": -1}},
    "band--blessings-of-nurgle-cloud-of-flies": {"traits": {"cloud_of_flies": True}},
    "band--blessings-of-nurgle-bloated-foulness": {"stats": {"toughness": 1, "wounds": 1}},
    "band--blessings-of-nurgle-mark-of-nurgle": {"stats": {"wounds": 1}, "traits": {"poison_immune": True}},
    "band--blood-dragon-power-red-fury": {"effects": {"attacks_bonus": 1}},
    "band--blood-dragon-power-infallible": {"effects": {"charge_reroll_hits": True}},
    "band--blood-dragon-power-strength-of-steel": {"effects": {"charge_strength_bonus": 1}},
    "band--lahmia-power-lost-innocence": {"effects": {"priority": 10}},
    "band--strigoi-power-monstrosity": {"stats": {"wounds": 1}},
    "band--strigoi-power-iron-sinews": {"stats": {"strength": 1}},
    "band--strigoi-power-infinite-hatred": {"effects": {"reroll_hits": True}},
    # Optional profile rules are selected through FighterBuild.special_rule_ids.
    # Their persistent 1v1 effects live here; inherent profile rules belong in
    # PROFILE_RULE_EFFECTS below.
    # Bear Hug's source binding retains the historic special-rule namespace;
    # PROFILE_RULE_EFFECTS is what grants it automatically to the Bear.
    "trained-bear--bear-hug": {"effects": {"bear_hug": True}},
    "band--mutations-extra-arm": {},
    "band--mutations-great-claw": {},
    "band--beastmen-special-skills-horned-one": {},
    "band--norse-special-skills-berserk-charge": {"effects": {"tags": ("rule.berserk-charge",)}},
    "band--necromantic-modification-multiple-limbs": {"effects": {"attacks_bonus": 1}},
    "band--necromantic-modification-putrid-stench": {"effects": {"incoming_hit_modifier": -1, "tags": ("rule.putrid-stench",)}},
    "band--mutations-tentacle": {"effects": {"incoming_attacks_modifier": -1}},
    "band--shield-bash": {},
    "band--skaven-special-skills-tail-fighting": {},
    "band--sacred-mark-venom-glands": {},
}


PROFILE_RULE_EFFECTS = {
    "fanatics--frantic": {"effects": {"priority": 10}},
    "centigors--trample": {},
    "trained-bear--bear-hug": {"effects": {"bear_hug": True}},
}


@lru_cache(maxsize=None)
def mechanic_index(ruleset: str, root: Path | None = None):
    doc = load_mechanics(ruleset, root)
    return {str(row["id"]): row for collection in COLLECTIONS for row in doc.get(collection, ())}


@lru_cache(maxsize=None)
def effect_index(ruleset: str, root: Path | None = None):
    result = {}
    for row in load_execution_contract(ruleset, root).get("mechanics") or ():
        mechanic_id=str(row.get("id", ""))
        if not mechanic_id or mechanic_id in result: raise ValueError(f"missing or duplicate execution ID: {mechanic_id!r}")
        if row.get("handler")!="effect-set": raise ValueError(f"unknown handler for {mechanic_id}: {row.get('handler')!r}")
        trigger = row.get("trigger")
        application = row.get("application")
        if trigger not in {"passive","duel_start","attack"}: raise ValueError(f"unknown trigger for {mechanic_id}")
        if application not in {"fighter","attack"}: raise ValueError(f"unknown application for {mechanic_id}")
        expected_application = "attack" if trigger == "attack" else "fighter"
        if application != expected_application:
            raise ValueError(f"invalid trigger/application for {mechanic_id}: {trigger}/{application}")
        if row.get("stacking") not in {"stack","best","once"}: raise ValueError(f"unknown stacking rule for {mechanic_id}")
        params = dict(row.get("parameters") or {})
        unknown = set(params) - EFFECT_FIELDS
        if unknown: raise ValueError(f"unknown parameters for {row.get('id')}: {sorted(unknown)}")
        if "tags" in params: params["tags"]=tuple(params["tags"])
        result[mechanic_id] = ExecutionEffect(EffectSet(**params), trigger, application, row["stacking"])
    return result


def validate_execution_contract(ruleset="mordheim", root=None):
    try: mechanics, effects = mechanic_index(ruleset, root), effect_index(ruleset, root)
    except (TypeError, ValueError) as exc: return [str(exc)]
    errors = []
    if set(mechanics)-set(effects): errors.append(f"mechanics without execution: {sorted(set(mechanics)-set(effects))}")
    if set(effects)-set(mechanics): errors.append(f"execution without mechanic: {sorted(set(effects)-set(mechanics))}")
    empty=[mid for mid,row in ((str(r.get("id")),r) for r in load_execution_contract(ruleset,root).get("mechanics") or ()) if not (row.get("parameters") or {})]
    if empty:errors.append(f"mechanics with empty contracts: {sorted(empty)}")
    return errors
