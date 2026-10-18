"""construction: Construction contracts and shared compile-time data."""
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
    "condemned_fixed_characteristics": list,
    "rune_iron_slots": list, "rune_stone_slots": list, "rune_fury_slots": list,
    "rune_striking_slots": list, "rune_speed_slots": list, "rune_cleaving_slots": list,
    "blessed_weapon_slots": list, "honing_slots": list, "coating_slots": list,
    "craftsman_strength_slots": list, "craftsman_initiative_slots": list,
    "snorri_drunk_result": int,
    "chaos_follower": bool, "onogal_follower": bool, "ulric_rival": bool, "aquatic": bool, "greenskin": bool, "flesh_peddler_mark": bool, "guiding_dream_target": bool,
    "eagle_friends": int,
    "fauna_animal_kind": str, "animal_handler_leadership": int,
    "house_guard_house": str, "fighter_kind": str, "vampire_bloodline": str,
    "mercenary_origin": str, "elf_kind": str, "creature_kind": str, "active_command": str, "righteous_charge_active": bool, "wheelo_fitting": str, "sex": str, "species": str, "lit_item": bool, "vampire": bool, "normal_animal": bool, "lizardman": bool,
    "stupidity": bool, "stupidity_exempt": bool, "stupidity_initial_failed": bool,
    "stupidity_leadership": int, "stupidity_leadership_bonus": int,
    # Printed Mob: how many other allied Peasants the caller supplies within
    # three inches; the engine never counts the group itself.
    "mob_allies": int,
    "starting_skills": (list,tuple), "natural_armour_save": int, "injury_profile": int,
    "ward_save": int, "regeneration_save": int,
    "extra_natural_attacks": int, "poison_immune": bool, "undead_or_possessed": bool,
    "frenzy": bool, "causes_fear": bool, "cloud_of_flies": bool, "natural_armour_stacks": bool,
    # Printed Cold-Blooded variant of a supplied condition: the two sources
    # disagree (Lizardmen apply it to Psychology and Rout, Fimir to
    # Leadership), so the caller declares which one the warrior has.
    "cold_blooded_origin": str,
    "charge_attack_bonus": bool, "first_round_charge_attack_bonus": bool, "maddened_with_pain": bool,
    "natural_armour_unmodified": bool, "poisonous_injury": bool, "survivor": bool,
    "natural_armour_worst_save": int,
    "concussion_immune": bool, "wight_blades": bool, "perfect_killer": bool,
    "counts_as_buckler": bool, "counts_as_shield": bool, "fragile_halflings": bool,
    "flammable": bool,
    "ward_save_mundane_only": bool,
    "natural_armour_negated_by_magic": bool,
    "natural_armour_negated_by_fire": bool,
    "scourge_armed": bool,
    "slave": bool,
    # Supplied identity of the opposing model: Free the Slaves! selects on it,
    # exactly as `slave` carries the opposite printed fact.
    "slaver": bool,
    # Bitter Enmity (serious injury 56): the campaign determines which enemy the
    # warrior hates, so the duel is supplied both the printed kind of target and
    # its concrete identity.  A category never stands in for a named warrior and
    # no supplied pair grants Hatred against every enemy.
    "enmity_kind": str,
    "enmity_target": str,
    # Supplied instance identities: the caller's own keys for one warrior and for
    # the warband instance it belongs to.  Bitter Enmity's three instance kinds
    # select these, never a catalogue profile or band, so two warriors of one
    # profile and two rosters built from one catalogue list stay distinct.
    "instance_id": str,
    "warband_instance": str,
    # Supplied promotion fact: this Hero of the Watch has become a Knight of
    # Purity, the only recipient the printed Fanatical rule names.
    "crusader_of_law": bool,
    "devoted_vampire_down": bool,
    "devoted_vampire_killed": bool,
    "spellcaster": bool,
    "necromancer": bool,
    "metal_armour": bool,
    "magical_attacks": bool,
    "spectral_touch": bool,
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
    "compiler.holy-relic-frenzy",
    "compiler.knight-of-purity",
    "compiler.aquatic-mutants",
    "compiler.johann-crimson-shade",
    "compiler.hireling-fixed-equipment",
    "compiler.assassin-poisoner",
    "compiler.woodsmen-quarterstaff",
    "compiler.aldred-fellblade",
    "compiler.zomblintua-blunt-attacks",
    "compiler.no-blackpowder-weapons",
    "compiler.ignore-difficult-to-use-restrictions",
    "compiler.censer-bearer-loadout",
    "compiler.forbid-item-categories",
    "compiler.mutant-requires-mutation-at-recruitment",
    "compiler.swabbie-rabble-loadout",
    "compiler.promoted-hero-skill-access",
    "compiler.pit-fighter-fighting-styles",
    "compiler.no-missile-weapons",
    "compiler.forbid-skill-categories",
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
    "compiler.mercenary-equipment-at-creation",
    "compiler.knighthood",
    "compiler.master-of-arms",
    "compiler.master-of-throwing-weapons",
    "compiler.mutation-purchase-at-recruitment",
    "compiler.rat-ogre-single-mutation-at-recruitment",
    "compiler.twistkin-single-mutation-at-recruitment",
    "compiler.veteran-tracker-skill-choice",
    "compiler.animal-handler-skill-choice",
    "compiler.hillman-wolf-form",
    "compiler.inherited-orc-special-skills",
    "compiler.bite-attack",
    "compiler.strikes-last-bite",
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
    "compiler.sister-special-skills",
    "compiler.strictures",
    "compiler.tracker-gear",
    "compiler.vampiric-powers",
    "compiler.warrior-wizard",
    "compiler.warrior-s-code",
    "compiler.weapon-knowledge",
    "compiler.weapons-training-exception",
    "compiler.lizardmen-scaly-skin",
}


# 'A trapper starts with ONE of the following Special Skills'. The choice is
# admitted construction; each option keeps its own excluded runtime, so the
# selection stays inert instead of granting the member's subsystem.
VETERAN_TRACKER_SKILLS = (
    "band--ogre-hunting-skills-infiltration",
    "band--ogre-hunting-skills-set-traps",
    "band--ogre-hunting-skills-netter",
    "band--ogre-hunting-skills-scent-hound",
)


SPECIAL_RULE_EFFECTS = {
    "band--beastmen-special-skills-mutant": {},
    "band--marauder-special-skills-mutant": {},
    # Chosen of Chaos: the admitted construction consequence is the capability
    # itself, so a build can carry the selection the printed market clauses
    # require. Nothing is added to the fighter: the printed campaign maximum is
    # advancement (outside the duel), and the Hero equipment list the same
    # sentence grants is already the declared list of every recipient of the
    # rule, exactly as its own '(if he does not already)' reads.
    "band--marauder-special-skills-chosen-of-chaos": {},
    # Tentacle: the printed grapple lets the mutant nominate which of the
    # opponent's attacks is lost, so the compiled effect carries the rule's
    # own tag beside the flat modifier the optimized drivers already apply.
    "band--mutations-tentacle": {"effects": {"incoming_attacks_modifier": -1,
        "tags": ("rule.tentacle-grapple",)}},
    "band--blessings-of-nurgle-cloud-of-flies": {"traits": {"cloud_of_flies": True}},
    # Bloated Foulness: +1 Wound, +1 Toughness and Movement -1 (its source
    # wording); movement is carried, not consumed by the duel engine.
    "band--blessings-of-nurgle-bloated-foulness": {"stats": {"toughness": 1, "wounds": 1, "movement": -1}},
    "band--blessings-of-nurgle-mark-of-nurgle": {"stats": {"wounds": 1}, "traits": {"poison_immune": True}},
    "band--blood-dragon-power-red-fury": {"effects": {"attacks_bonus": 1}},
    "band--blood-dragon-power-infallible": {"effects": {"charge_reroll_hits": True}},
    "band--blood-dragon-power-strength-of-steel": {"effects": {"charge_strength_bonus": 1}},
    "band--lahmia-power-lost-innocence": {"effects": {"priority": 10}},
    "band--strigoi-power-monstrosity": {"stats": {"wounds": 1}},
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
    "band--mutations-tentacle": {"effects": {"incoming_attacks_modifier": -1,
        "tags": ("rule.tentacle-grapple",)}},
    "band--shield-bash": {},
    "band--skaven-special-skills-tail-fighting": {},
    "band--sacred-mark-venom-glands": {},
}


PROFILE_RULE_EFFECTS = {
    # Cold Steel (Necrarchs Banshee): the printed clause reads the identity of
    # the incoming attack -- a steel or iron weapon can harm the bearer at -1 to
    # hit, a blessed or magical one hits normally, and the body identities its
    # gloss excepts ("anything but clubs, fists etc.") cannot harm her at all.
    # The bearer therefore carries one declared tag, and the modular consumers
    # resolve it on the attack's own weapon and properties, never on a visible
    # weapon name.  Missile references stay outside the duel.
    "banshee--cold-steel": {"effects": {"tags": ("defence.cold-steel",)}},
    "fanatics--frantic": {"effects": {"priority": 10}},
    "centigors--trample": {},
    # Spiked Tail adds one repeated natural tail attack at the bearer's
    # Strength +1; the extra attack itself is assembled in ``compile_fighter``
    # because it is a separate profile, not a flat bonus on the bearer's pool.
    "fimir-warriors--spiked-tail": {},
    "young-nobles--spiked-tail": {},
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
