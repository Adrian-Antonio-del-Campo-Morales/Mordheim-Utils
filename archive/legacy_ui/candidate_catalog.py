"""Candidate catalogue built from the canonical knowledge base."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
import os
import re
import sys
import unicodedata

import yaml

from .rules import (
    ARMORS,
    BODY_ARMORS,
    MAIN_HAND_FORBIDDEN_WEAPONS,
    OFF_HAND_OPTIONS,
    POISONS,
    PREPARATIONS,
    SKILLS,
    WEAPON_MATERIALS,
    WEAPONS_ALL,
)
from .units import movement_to_inches


CATEGORY_ORDER = ("combat", "shooting", "academic", "strength", "speed", "special")
CATEGORY_FILTERS = ("all", "core", "1a", "1b", "1c", "trollheim")
CATEGORY_LABELS = {
    "combat": "Combat", "shooting": "Shooting", "academic": "Academic",
    "strength": "Strength", "speed": "Speed", "special": "Special",
}

GENERAL_SKILLS = {
    "combat": {name: "" for name in ("Strike to Injure", "Combat Master", "Weapons Training", "Web of Steel", "Expert Swordsman", "Step Aside")},
    "shooting": {name: "" for name in ("Quick Shot", "Pistolier", "Eagle Eyes", "Weapons Expert", "Nimble", "Trick Shooter", "Hunter", "Knife-Fighter")},
    "academic": {name: "" for name in ("Battle Tongue", "Sorcery", "Streetwise", "Haggle", "Arcane Lore", "Wyrdstone Hunter", "Warrior Wizard")},
    "strength": {name: "" for name in ("Mighty Blow", "Pit Fighter", "Resilient", "Fearsome", "Strongman", "Unstoppable Charge")},
    "speed": {name: "" for name in ("Leap", "Sprint", "Acrobat", "Lightning Reflexes", "Jump Up", "Dodge", "Scale Sheer Surfaces")},
}
_CORE_SKILL_DESCRIPTIONS = {
    "Strike to Injure": "+1 to Injury rolls caused in close combat.",
    "Combat Master": "+1 Attack while fighting two or more enemies; immune to All Alone tests.",
    "Weapons Training": "May use any close-combat weapon.",
    "Web of Steel": "+1 on close-combat Critical Hit tables.",
    "Expert Swordsman": "Re-roll missed attacks with normal swords or weeping blades when charging.",
    "Step Aside": "Unmodified 5+ save against close-combat wounds after armour saves.",
    "Quick Shot": "May shoot twice with a bow or crossbow, excluding crossbow pistols.",
    "Pistolier": "May fire a brace of pistols twice, subject to reloading.",
    "Eagle Eyes": "+6 inches to missile-weapon range.",
    "Weapons Expert": "May use any missile weapon.",
    "Nimble": "May move and fire move-or-fire weapons; cannot combine with Quick Shot.",
    "Trick Shooter": "Ignores cover modifiers when shooting.",
    "Hunter": "May fire a handgun or Hochland long rifle every turn.",
    "Knife-Fighter": "May throw up to three knives or stars; cannot combine with Quick Shot.",
    "Battle Tongue": "Leader range increases by 6 inches.",
    "Sorcery": "+1 to spell-casting rolls.", "Streetwise": "+2 when searching for rare items.",
    "Haggle": "Once per post-battle sequence, reduces one item's price by 2D6 gc (minimum 1 gc).",
    "Arcane Lore": "May learn Lesser Magic with a Tome of Magic, subject to restrictions.",
    "Wyrdstone Hunter": "May re-roll one Exploration die.",
    "Warrior Wizard": "A spellcaster may cast spells while wearing armour.",
    "Mighty Blow": "+1 Strength in close combat, excluding pistols.",
    "Pit Fighter": "+1 WS and +1 Attack inside buildings or ruins.",
    "Resilient": "Close-combat hits against the warrior suffer -1 Strength without changing save modifiers.",
    "Fearsome": "Causes fear.", "Strongman": "Double-handed weapons not longer strike last.",
    "Unstoppable Charge": "+1 WS when charging.",
    "Leap": "May leap D6 inches once per movement phase in addition to movement.",
    "Sprint": "May run or charge at triple Movement.",
    "Acrobat": "Improved falling, jumping and diving charges.",
    "Lightning Reflexes": "When charged, strikes first and resolves ties by Initiative.",
    "Jump Up": "May ignore most knocked-down Injury results.",
    "Dodge": "5+ save against missile hits before rolling to wound.",
    "Scale Sheer Surfaces": "Climbs up to twice Movement without Initiative tests.",
}
GENERAL_SKILL_DESCRIPTIONS = {
    name: description for skills in GENERAL_SKILLS.values() for name, description in skills.items()
}
GENERAL_SKILL_CATEGORIES = {
    name: category for category, skills in GENERAL_SKILLS.items() for name in skills
}

# a same item receives names different between lists. here ends the poetry.
ITEM_TO_OPTION = {
    "dagger": "Dagger", "sword": "Sword", "club": "Mace",
    "mace": "Mace", "hammer": "Mace", "hammer_or_mace": "Mace", "axe": "Axe",
    "bronze_axe": "Axe", "bronze_dagger": "Dagger", "bronze_spear": "Spear",
    "bronze_sword": "Sword", "sacrifice_dagger": "Dagger",
    "flail": "Flail", "morning_star": "Morning star", "halberd": "Halberd",
    "spear": "Spear", "great_weapon": "Double-handed weapon", "stone_axe": "Stone axe",
    "rapier": "Rapier", "pike": "Pike", "elven_greatsword": "Elven greatsword",
    "ankus": "Ankus", "yambiya": "Yambiya", "katar": "Katar",
    "scythe": "Scythe", "cutlass": "Cutlass", "scimitar": "Scimitar",
    "great_scimitar": "Great scimitar", "bagh_nakh": "Bagh Nakh",
    "sword_breaker": "Sword breaker", "pistol": "Pistol",
    "duelling_pistol": "Duelling pistol", "brazier_staff": "Brazier iron",
    "brass_knuckles": "Brass knuckles", "war_maul": "War maul",
    "double_blade_sword": "Double-bladed sword", "dwarf_axe": "Dwarf axe",
    "trident": "Trident", "spiked_gauntlet": "Spiked gauntlet",
    "sigmarite_hammer": "Sigmarite hammer", "steel_whip": "Steel whip",
    "choppa": "Choppa", "fighting_claws": "Fighting claws",
    "weeping_blades": "Weeping blades", "serpent_staff": "Serpent staff",
    "chained_squig": "Chained Squig", "squig_prodder": "Squig prodder",
    "kusara_kama": "Kusara Kama", "witch_sword": "Witch sword",
    "long_boathook": "Long boat hook", "scourge": "Pirate scourge", "bo": "Bo",
    "poisoned_daggers": "Poisoned daggers", "snake_whip": "Serpent whip",
    "beastmaster_whip": "Beastlash",
    "solar_gauntlet": "Sun gauntlet",
    "unholy_transformation_sword": "Unholy sword",
    "stiletto": "Stiletto", "ancestral_claw": "Claw of the Old Ones",
    "draich": "Draich", "death_knife": "Death knife",
    "plague_dagger": "Disease dagger", "censer": "Censer",
    "ball_and_chain": "Ball and chain", "shield": "Shield", "buckler": "Buckler",
    "two_handed_club": "Double-handed weapon", "chained_club": "Chained Squig",
    "weeping_dagger": "Disease dagger", "whip": "Steel whip",
    "yari": "Yari (one-handed)", "pursuer_style_skink_trident": "Trident",
    "pursuer_style_witch_elf_spear": "Spear",
    "pursuer_style_witch_elf_swords": "Sword",
    "light_armour": "Light armour", "heavy_armour": "Heavy armour",
    "gromril_armour": "Gromril armour", "ithilmar_armour": "Ithilmar armour",
    "hardened_leather": "Toughened leathers", "plate_armour": "Plate armour",
    "wizard_robe": "Wizard's robe", "mage_robes": "Wizard's robe",
    "ninja_robes": "Ninja robes",
    "eshin_assassin_clothes": "Eshin assassin robes",
    "spider_chitin_armour": "Spider chitin armour",
    "sea_dragon_cloak": "Sea Dragon cloak", "helmet": "Helmet",
    "bronze_helmet": "Helmet",
}
ITEM_TO_OPTION.update({
    "mace_hammer": "Mace", "staff_club_mace": "Mace",
    "mace_hammer_club": "Mace", "two_handed_weapon": "Double-handed weapon",
    "dagger_jambiya": "Dagger", "sword_scimitar": "Sword", "shortsword": "Sword",
    "cutlass_sword": "Cutlass", "stone_axe_counts_as_a_club": "Stone axe",
    "cleaver_counts_as_axe": "Axe", "cleaver": "Axe", "battle_axe": "Axe",
    "great_axe": "Double-handed weapon", "ogre_club": "Mace",
    "kitchen_knife": "Dagger", "ladle": "Mace", "tenderiser": "Mace",
    "ball_chain": "Ball and chain", "poison_daggers": "Poisoned daggers",
    "choppa_counts_as_a_morning_star": "Choppa", "boat_hook": "Long boat hook",
    "belaying_pin": "Mace", "beastlash": "Beastlash",
    "barbed_whip": "Beastlash", "cat_o_nine_tails": "Pirate scourge",
    "main_gauche": "Sword breaker", "iron_fist": "Spiked gauntlet",
    "claw_of_the_old_ones": "Claw of the Old Ones", "sun_gauntlet": "Sun gauntlet",
    "disease_dagger": "Disease dagger", "hobgoblin_poisoned_daggers": "Poisoned daggers",
    "sunstaff": "Brazier iron", "sunstaff_lustria": "Brazier iron",
    "lance": "Lance", "lance_not_questing_knight": "Lance",
    "misericordia": "Misericordia", "starblade": "Starblade", "starsword": "Starsword",
    "broadsword": "Broadsword", "dragon_sword": "Dragon Sword",
    "cathayan_longsword": "Cathayan Longsword", "chain_sticks": "Chain Sticks",
    "man_catcher": "Man-catcher", "quarter_staff": "Quarter Staff",
    "sword_heroes_only": "Sword", "sword_gnoblar": "Sword", "staff": "Quarter Staff",
})

EQUIPMENT_ITEM_TO_OPTION = {
    **ITEM_TO_OPTION,
    "lucky_charm": "Lucky charm",
    "mad_mushrooms": "Mad Cap Mushrooms",
    "mad_cap_mushrooms": "Head-splitter mushrooms",
    "crimson_shade": "Crimson Shade",
    "mandrake_root": "Mandrake Root",
    "tears_of_shallaya": "Tears of Shallaya",
    "black_lotus": "Black Lotus",
    "black_venom": "Black Venom",
    "dark_venom": "Black Venom",
    "reptile_venom": "Reptile Venom",
    "manbane": "Manbane",
    "aconite": "Wolfsbane",
    "nightshade": "Nightshade",
    "blood_root": "Bloodroot",
    "bloodroot": "Bloodroot",
    "devil_toxin": "Devil's Toxin",
    "devils_toxin": "Devil's Toxin",
    "spider_spittle": "Spider Spittle",
}

SUPPORTED_EQUIPMENT_OPTIONS = frozenset({
    *(armor for armor in ARMORS if armor not in {"No Armour", "Ninja robes"}),
    "Helmet", "Lucky charm", "Sea Dragon cloak",
    *(value for value in PREPARATIONS if value != "None"),
    *(value for value in POISONS if value != "No Poison"),
})

MATERIAL_ITEMS = {
    "gromril_weapon": "Gromril", "ithilmar_weapon": "Ithilmar",
    "obsidian_weapon": "Obsidian", "dark_steel_weapon": "Dark steel",
    "dark_elf_blade_weapon_upgrade": "Dark Elf blade",
}

COMPOSITE_ITEMS = {
    "pit_style_orc": ("Helmet", "Dagger", "Axe", "Shield"),
    "pit_style_undead": ("Helmet", "Dagger", "Spiked gauntlet", "Sword"),
    "pit_style_empire": ("Helmet", "Dagger", "Double-handed weapon", "Light armour"),
    "pit_style_chaos": ("Helmet", "Dagger", "Morning star", "Light armour"),
    "pursuer_style_skink_trident": ("Helmet", "Dagger", "Trident", "Buckler"),
    "pursuer_style_skink_javelin": ("Helmet", "Dagger", "Buckler"),
    "pursuer_style_witch_elf_swords": ("Helmet", "Dagger", "Sword"),
    "pursuer_style_witch_elf_spear": ("Helmet", "Dagger", "Spear"),
}
# The Mordheim catalogue mixed supplement skills into the five general lists.
# Mordheim's core lists are exact and closed; warband skills come separately
# from each normalized band record.
_CORE_SKILLS = {
    "combat": {"Strike to Injure", "Combat Master", "Weapons Training", "Web of Steel", "Expert Swordsman", "Step Aside"},
    "shooting": {"Quick Shot", "Pistolier", "Eagle Eyes", "Weapons Expert", "Nimble", "Trick Shooter", "Hunter", "Knife-Fighter"},
    "academic": {"Battle Tongue", "Sorcery", "Streetwise", "Haggle", "Arcane Lore", "Wyrdstone Hunter", "Warrior Wizard"},
    "strength": {"Mighty Blow", "Pit Fighter", "Resilient", "Fearsome", "Strongman", "Unstoppable Charge"},
    "speed": {"Leap", "Sprint", "Acrobat", "Lightning Reflexes", "Jump Up", "Dodge", "Scale Sheer Surfaces"},
}
GENERAL_SKILLS = {
    category: {name: description for name, description in skills.items() if name in _CORE_SKILLS[category]}
    for category, skills in GENERAL_SKILLS.items()
}
GENERAL_SKILLS = {
    category: {name: _CORE_SKILL_DESCRIPTIONS[name] for name in skills}
    for category, skills in GENERAL_SKILLS.items()
}
GENERAL_SKILL_DESCRIPTIONS = {
    name: description for skills in GENERAL_SKILLS.values() for name, description in skills.items()
}
GENERAL_SKILL_CATEGORIES = {
    name: category for category, skills in GENERAL_SKILLS.items() for name in skills
}


@dataclass(frozen=True)
class CandidateProfile:
    band_id: str
    band_name: str
    profile_id: str
    name: str
    profile_type: str
    stats: dict[str, int]
    movement_inches: int | str
    weapons: tuple[str, ...]
    armors: tuple[str, ...]
    defenses: tuple[str, ...]
    materials: tuple[str, ...]
    skills: tuple[str, ...]
    skills_by_category: dict[str, tuple[str, ...]]
    helmet_allowed: bool
    fixed_equipment: tuple[str, ...]
    restrictions: tuple[str, ...]
    rules: tuple[str, ...]
    combat_traits: dict[str, object]
    source: dict


@dataclass(frozen=True)
class BandSkill:
    skill_id: str
    name: str
    description: str
    category: str = "special"
    access_tags: tuple[str, ...] = ("special",)


@dataclass(frozen=True)
class Band:
    band_id: str
    name: str
    profiles: tuple[CandidateProfile, ...]
    skills: tuple[BandSkill, ...]
    canonical_family: str = ""
    categories: tuple[str, ...] = ()
    collections: tuple[str, ...] = ()
    grade: str | None = None
    setting: str | None = None
    publication: str | None = None
    sources: tuple[dict, ...] = ()
    original_locale: str = "en"


def _knowledge_root() -> Path:
    candidates = []
    override = os.environ.get("SIMULATOR_KNOWLEDGE_ROOT")
    if override:
        candidates.append(Path(override) / "bands")
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys._MEIPASS) / "sources" / "knowledge" / "bands")
    candidates.extend((
        Path(__file__).resolve().parents[2] / "sources" / "knowledge" / "bands",
        Path(sys.prefix) / "share" / "mordheim_combat_lab" / "knowledge" / "bands",
    ))
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("Mordheim knowledge base not found: sources/knowledge/bands")


def _band_paths() -> tuple[Path, ...]:
    """Return only materialized v1 band records from every collection."""
    return tuple(sorted(_knowledge_root().glob("*/*.yaml")))


def _rule_text(rule) -> str:
    if isinstance(rule, dict):
        name = str(rule.get("name", "Rule"))
        effect = str(rule.get("effect", "")).strip()
        return f"{name}: {effect}" if effect else name
    return str(rule)


def _skill_display_name(name: str) -> str:
    """Use UI title case while preserving acronyms and minor connecting words."""
    minor_words = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or", "the", "to", "with"}
    word_index = 0

    def format_word(match):
        nonlocal word_index
        word = match.group(0)
        is_minor = word.casefold() in minor_words and word_index > 0
        word_index += 1
        if not word.islower():
            return word
        if is_minor:
            return word
        return word[:1].upper() + word[1:]

    return re.sub(r"[A-Za-z]+(?:'[A-Za-z]+)?", format_word, name.strip())


def _band_skills(raw_band: dict) -> tuple[BandSkill, ...]:
    result = []
    seen = set()
    section_headings = {
        "skill", "skills", "special skill", "special skills", "power", "powers",
        "habilidad", "habilidades", "habilidades especiales", "poder", "poderes",
    }
    for rule in raw_band.get("band_rules") or ():
        section = str((rule.get("source") or {}).get("section", "")).casefold()
        if not any(marker in section for marker in ("skill", "power", "habilidad", "poder")):
            continue
        name = _skill_display_name(str(rule.get("name", "Skill")))
        normalized_name = name.casefold()
        section_leaf = section.rsplit("/", 1)[-1].strip()
        is_named_section_heading = (
            section_leaf == normalized_name
            and normalized_name.endswith((" skills", " powers"))
        )
        if normalized_name in section_headings or is_named_section_heading:
            continue
        effect = str(rule.get("effect", ""))
        if name == "Combat Master" and "Parry" in effect:
            name = "Dwarf Combat Master"
        if name.casefold() in seen:
            continue
        seen.add(name.casefold())
        access_tags = ("special",)
        if "power" in section or "poder" in section:
            tags = []
            for marker, tag in (
                ("von carstein", "von_carstein_powers"),
                ("blood dragon", "blood_dragon_powers"),
                ("necrarch", "necrarch_powers"),
                ("lahmia", "lahmia_powers"),
                ("strigoi", "strigoi_powers"),
            ):
                if marker in section:
                    tags.append(tag)
            access_tags = tuple(tags)
        result.append(BandSkill(
            str(rule.get("id", name)), name, effect,
            access_tags=access_tags,
        ))
    return tuple(result)


def _special_skill_allowed(skill: BandSkill, profile: dict) -> bool:
    text = skill.description.casefold()
    profile_name = str(profile.get("name", "")).casefold()
    rules = " ".join(
        f"{rule.get('id', '')} {rule.get('name', '')}" if isinstance(rule, dict) else str(rule)
        for rule in profile.get("rules") or ()
    ).casefold()
    if "only the leader" in text or "only the current leader" in text:
        return "leader" in rules
    explicit = {
        "only master": ("master",),
        "only the master of knowledge": ("master of knowledge",),
        "only explorer": ("explorer",),
        "only explorers": ("explorer",),
        "only troll slayer": ("troll slayer",),
        "only captain": ("captain",),
        "only khann": ("khann",),
        "only warrior priest": ("warrior priest",),
        "only the matriarch": ("matriarch",),
        "only witch doctor": ("witch doctor",),
        "only rangers": ("ranger",),
        "only skinks": ("skink",),
        "only saurus": ("saurus",),
    }
    for marker, allowed_names in explicit.items():
        if marker in text:
            return any(name in profile_name for name in allowed_names)
    if skill.name == "Strong Constitution" and "sorceress" in profile_name:
        return False
    return True


def _general_skill_allowed(name: str, band: dict, profile: dict) -> bool:
    rules = profile.get("rules") or ()
    rule_text = " ".join(
        f"{rule.get('id', '')} {rule.get('name', '')}" if isinstance(rule, dict) else str(rule)
        for rule in rules
    ).casefold()
    is_leader = "leader" in rule_text
    is_caster = any(word in rule_text for word in ("wizard", "sorcer", "witch"))
    uses_prayers = any(word in rule_text for word in ("prayer", "priest"))
    if name in {"Battle Tongue", "Tactician", "Hunch"}:
        return is_leader
    if name in {"Sorcery", "Warrior Wizard", "Magical Aptitude"}:
        return is_caster
    if name in {"Scribe", "Mental Focus"}:
        return is_caster or uses_prayers
    if name == "Arcane Lore":
        forbidden = ("Witch Hunters", "Sisters of Sigmar")
        return str(band.get("name", "")) not in forbidden and not uses_prayers
    return True


def _build_profile(band, profile, equipment_lists, band_skills) -> CandidateProfile:
    item_ids = []
    for list_id in profile.get("equipment_lists") or ():
        item_ids.extend(equipment_lists.get(list_id, ()))

    options = {ITEM_TO_OPTION[item] for item in item_ids if item in ITEM_TO_OPTION}
    for item in item_ids:
        options.update(COMPOSITE_ITEMS.get(item, ()))
    # In the normalized Mordheim roster, a profile without an equipment list
    # is an innate attacker (animals, Giant Rats, Wulfen, etc.), not an empty
    # loadout. Human profiles with special recruitment still receive a list.
    has_natural_attacks = not profile.get("equipment_lists")
    if has_natural_attacks:
        options.add("Natural attacks")
    weapons = tuple(option for option in WEAPONS_ALL if option in options)
    # The yari can be used in either configuration even though it is bought once.
    if "Yari (one-handed)" in options or "Yari (two-handed)" in options:
        weapons = tuple(dict.fromkeys((*weapons, "Yari (one-handed)", "Yari (two-handed)")))
    armors = tuple(armor for armor in BODY_ARMORS if armor in options)
    materials = ("Normal", *(material for item, material in MATERIAL_ITEMS.items() if item in item_ids))
    materials = tuple(material for material in WEAPON_MATERIALS if material in materials)

    skill_categories = set(profile.get("skill_access") or ())
    skills_by_category = {
        category: tuple(
            skill for skill in GENERAL_SKILLS.get(category, ())
            if _general_skill_allowed(skill, band, profile)
        )
        for category in CATEGORY_ORDER[:-1] if category in skill_categories
    }
    special_access = {
        category for category in skill_categories
        if "special" in category or category.endswith("_powers")
    }
    if special_access:
        skills_by_category["special"] = tuple(
            skill.name for skill in band_skills
            if _special_skill_allowed(skill, profile)
            and (
                "special" in skill.access_tags
                or bool(special_access.intersection(skill.access_tags))
            )
        )
    # Some warbands repeat a general skill as a special skill with the same
    # name (for example, Streetwise). It is shown once, retaining the first
    # canonical category available to the warrior.
    seen_skills = set()
    for category in CATEGORY_ORDER:
        unique = tuple(
            skill for skill in skills_by_category.get(category, ())
            if skill not in seen_skills
        )
        if category in skills_by_category:
            skills_by_category[category] = unique
        seen_skills.update(unique)
    allowed_skills = tuple(
        name for category in CATEGORY_ORDER for name in skills_by_category.get(category, ())
    )
    characteristics = profile.get("characteristics") or {}
    rule_records = tuple(profile.get("rules") or ())
    rule_names = {str(rule.get("name", "")).casefold() for rule in rule_records if isinstance(rule, dict)}
    if "vomit attack" in rule_names:
        weapons = tuple(dict.fromkeys((*weapons, "Vomit attack")))
    rule_text = " ".join(
        f"{rule.get('name', '')} {rule.get('effect', '')}" for rule in rule_records
        if isinstance(rule, dict)
    ).casefold()
    starting_skills = []
    for rule_name, skill_name in {
        "not pain": "not Pain", "regeneration": "Regeneration",
        "hard to kill": "Hard to Kill", "expert swordsmen": "Expert Swordsman",
        "strongman": "Strongman", "lightning reflexes": "Lightning Reflexes",
        "unnatural strength": "Strongman", "swordmaster": "Swordmaster",
        "duellist": "Duellist",
        "hatred": "Hatred",
        "frantic": "Always Strikes First",
        "savage": "Extra Attack",
        "blessed sight": "Blessed Sight",
        "inspired cooking": "Blessed Sight",
        "crack shot": "Crack Shot",
        "art of silent death": "Art of Silent Death",
    }.items():
        if rule_name in rule_names:
            starting_skills.append(skill_name)
    natural_save = None
    save_match = re.search(r"(?:natural|special armour|considered to have a)\s+(?:save|armour save)\s+of\s+(\d)\+", rule_text)
    if save_match:
        natural_save = int(save_match.group(1))
    elif save_match := re.search(r"considered to have a\s+(\d)\+\s+armour save", rule_text):
        natural_save = int(save_match.group(1))
    elif "natural 6+ armour" in rule_text:
        natural_save = 6
    combat_traits = {
        "starting_skills": tuple(starting_skills),
        "frenzy": bool(rule_names & {"frenzy", "berserkers"}),
        "poison_immune": "immune to poison" in rule_names,
        "undead_or_possessed": bool(rule_names & {"undead", "demonic", "daemonic"}),
        "concussion_immune": "hard head" in rule_names,
        "cloud_of_flies": (
            "cloud of flies" in rule_names
            or ("dodgy" in rule_names and "hand-to-hand suffer -1 to hit" in rule_text)
        ),
        "charge_attack_bonus": "charge" in rule_names,
        "extra_natural_attacks": int("trample" in rule_names),
        "perfect_killer": "perfect killer" in rule_names,
        "wight_blades": "wight blades" in rule_names,
        "survivor": "survivor" in rule_names,
        "poisonous_injury": "poisonous" in rule_names,
        "maddened_with_pain": "maddened with pain" in rule_names,
        "injury_profile": (
            2 if "downtrodden" in rule_names else 1 if "weedy" in rule_names else 0
        ),
        "counts_as_buckler": "cloak & dagger" in rule_names,
        "natural_armour_save": natural_save,
        "natural_armour_unmodified": "cannot be modified beyond" in rule_text,
        "natural_armour_stacks": "may be combined with other equipment" in rule_text,
    }
    stats = {
        "WS": int(characteristics.get("WS", 0)), "S": int(characteristics.get("S", 0)),
        "T": int(characteristics.get("T", 0)), "W": int(characteristics.get("W", 0)),
        "I": int(characteristics.get("I", 0)), "A": int(characteristics.get("A", 0)),
    }
    return CandidateProfile(
        band_id=str(band["id"]), band_name=str(band["name"]),
        profile_id=str(profile["id"]), name=str(profile["name"]),
        profile_type=str(profile.get("type", "warrior")), stats=stats,
        movement_inches=movement_to_inches(
            characteristics.get("M", 0), str(band.get("original_locale", "en"))
        ),
        weapons=weapons, armors=armors,
        defenses=tuple(value for value in ("Shield", "Buckler") if value in options),
        materials=materials,
        skills=allowed_skills,
        skills_by_category=skills_by_category,
        helmet_allowed="Helmet" in options,
        fixed_equipment=tuple(str(value) for value in profile.get("fixed_equipment") or ()),
        restrictions=tuple(str(value) for value in profile.get("equipment_restrictions") or ()),
        rules=tuple(_rule_text(value) for value in profile.get("rules") or ()),
        combat_traits=combat_traits,
        source=dict(profile.get("source") or {}),
    )


@lru_cache(maxsize=1)
def load_bands() -> tuple[Band, ...]:
    bands = []
    for path in _band_paths():
        with path.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
        if raw.get("schema_version") != 1:
            raise ValueError(f"Unsupported band schema in {path}: {raw.get('schema_version')!r}")
        equipment_lists = {
            entry["id"]: tuple(item["item_id"] for item in entry.get("items") or ())
            for entry in raw.get("equipment_lists") or ()
        }
        band_skills = _band_skills(raw)
        profiles = tuple(
            _build_profile(raw, profile, equipment_lists, band_skills)
            for profile in raw.get("profiles") or ()
        )
        bands.append(Band(
            str(raw["id"]), str(raw["name"]), profiles, band_skills,
            canonical_family=str(raw.get("canonical_family", raw["id"])),
            categories=tuple(str(value) for value in raw.get("categories") or ()),
            collections=tuple(str(value) for value in raw.get("collections") or ()),
            grade=str(raw["grade"]) if raw.get("grade") else None,
            setting=str(raw["setting"]) if raw.get("setting") else None,
            publication=str(raw["publication"]) if raw.get("publication") else None,
            sources=tuple(dict(value) for value in raw.get("sources") or ()),
            original_locale=str(raw.get("original_locale", "en")),
        ))
    family_counts: dict[str, int] = {}
    for band in bands:
        family_counts[band.canonical_family] = family_counts.get(band.canonical_family, 0) + 1
    labelled = []
    for band in bands:
        if family_counts[band.canonical_family] <= 1:
            labelled.append(band)
            continue
        collection = "Trollheim" if "trollheim" in band.collections else "Mordheimer"
        display_name = f"{band.name} — {collection}"
        labelled.append(replace(
            band,
            name=display_name,
            profiles=tuple(replace(profile, band_name=display_name) for profile in band.profiles),
        ))
    return tuple(sorted(labelled, key=lambda band: band.name.casefold()))


def bands_for_category(category: str = "all") -> tuple[Band, ...]:
    key = category.casefold()
    if key not in CATEGORY_FILTERS:
        raise ValueError(f"Unknown band category: {category}")
    if key == "all":
        return load_bands()
    return tuple(band for band in load_bands() if key in band.categories)


def bands_for_categories(categories) -> tuple[Band, ...]:
    """Return the union of several catalogue categories without duplicates."""
    selected = {str(category).casefold() for category in categories}
    unknown = selected - set(CATEGORY_FILTERS)
    if unknown:
        raise ValueError(f"Unknown band categories: {sorted(unknown)}")
    if "all" in selected:
        return load_bands()
    return tuple(
        band for band in load_bands()
        if selected.intersection(band.categories)
    )


def find_profile(band_id: str, profile_id: str) -> CandidateProfile | None:
    for band in load_bands():
        if band.band_id == band_id:
            return next((profile for profile in band.profiles if profile.profile_id == profile_id), None)
    return None


def _expected_cost(value) -> float | None:
    """turns costs with D6 a its value expected to comparisons MOTTA."""
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).casefold().replace(" ", "").replace("×", "x")
    if re.fullmatch(r"\d+(?:[.,]\d+)?", text):
        return float(text.replace(",", "."))
    total = 0.0
    for term in text.split("+"):
        dice = re.fullmatch(r"(?:(\d+))?d6(?:x(\d+))?", term)
        if dice:
            amount = int(dice.group(1) or 1)
            multiplier = int(dice.group(2) or 1)
            total += amount * 3.5 * multiplier
            continue
        try:
            total += float(term)
        except ValueError:
            return None
    return total


def _profile_allows_equipment_item(item: dict, profile: dict) -> bool:
    notes = str(item.get("notes", "")).casefold()
    if "only" not in notes or "only during" in notes:
        return True
    name = str(profile.get("name", "")).casefold()
    profile_type = str(profile.get("type", "")).casefold()
    rules = " ".join(
        f"{rule.get('id', '')} {rule.get('name', '')}"
        if isinstance(rule, dict) else str(rule)
        for rule in profile.get("rules") or ()
    ).casefold()
    if "only heroes" in notes:
        return profile_type == "hero" or "corsair" in name
    if "only leader" in notes:
        return "leader" in rules
    allowed_names = {
        "silent hunter": ("silent hunter",),
        "ruffians and thugs": ("ruffian", "thug"),
        "witch doctor": ("witch doctor",),
        "skink priest": ("skink priest",),
    }
    for marker, names in allowed_names.items():
        if marker in notes:
            return any(value in name for value in names)
    return True


def _global_misc_equipment_for_profile(band: dict, profile: dict) -> set[str]:
    """Market equipment: heroes are not limited to their warband list."""
    if str(profile.get("type", "")).casefold() != "hero":
        return set()
    context = f"{band.get('id', '')} {band.get('name', '')}".casefold()
    profile_name = str(profile.get("name", "")).casefold()
    options = {
        "Lucky charm", "Mad Cap Mushrooms", "Crimson Shade",
        "Mandrake Root", "Tears of Shallaya", "Black Lotus",
        "Black Venom", "Reptile Venom", "Manbane", "Wolfsbane",
        "Nightshade", "Bloodroot", "Devil's Toxin", "Spider Spittle",
    }
    if "goblin" not in context and "goblin" not in profile_name:
        options.discard("Head-splitter mushrooms")
    if any(marker in context for marker in ("undead", "possessed")):
        options.discard("Tears of Shallaya")
    if any(marker in context for marker in (
        "sisters-of-sigmar", "sisters of sigmar", "witch-hunters", "witch hunters",
    )):
        options.discard("Black Lotus")
        options.discard("Black Venom")
        options.discard("Manbane")
    return options


@lru_cache(maxsize=None)
def equipment_options_for_profile(
    band_id: str = "", profile_id: str = "",
) -> tuple[str, ...]:
    if not band_id or not profile_id:
        return tuple(sorted(SUPPORTED_EQUIPMENT_OPTIONS, key=str.casefold))
    for path in _band_paths():
        with path.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
        if str(raw.get("id", "")) != band_id:
            continue
        profile = next(
            (row for row in raw.get("profiles") or () if str(row.get("id", "")) == profile_id),
            None,
        )
        if profile is None:
            return ()
        lists = {
            row["id"]: row.get("items") or ()
            for row in raw.get("equipment_lists") or ()
        }
        allowed = set()
        for list_id in profile.get("equipment_lists") or ():
            for item in lists.get(list_id, ()):
                if not _profile_allows_equipment_item(item, profile):
                    continue
                option = EQUIPMENT_ITEM_TO_OPTION.get(item.get("item_id"))
                if option in SUPPORTED_EQUIPMENT_OPTIONS:
                    allowed.add(option)
                allowed.update(
                    value for value in COMPOSITE_ITEMS.get(item.get("item_id"), ())
                    if value in SUPPORTED_EQUIPMENT_OPTIONS
                )
        allowed.update(_global_misc_equipment_for_profile(raw, profile))
        return tuple(sorted(allowed, key=str.casefold))
    return ()


@lru_cache(maxsize=None)
def equipment_costs_for_profile(band_id: str = "", profile_id: str = "") -> dict[str, float]:
    """Return costs by option, using the warband list when a profile is provided."""
    costs: dict[str, float] = {}
    if band_id and profile_id:
        for path in _band_paths():
            with path.open("r", encoding="utf-8") as stream:
                raw = yaml.safe_load(stream)
            if str(raw.get("id", "")) != band_id:
                continue
            profile = next(
                (row for row in raw.get("profiles") or () if str(row.get("id", "")) == profile_id),
                None,
            )
            if profile is None:
                break
            lists = {
                row["id"]: row.get("items") or ()
                for row in raw.get("equipment_lists") or ()
            }
            for list_id in profile.get("equipment_lists") or ():
                for item in lists.get(list_id, ()):
                    if not _profile_allows_equipment_item(item, profile):
                        continue
                    option = EQUIPMENT_ITEM_TO_OPTION.get(item.get("item_id"))
                    value = _expected_cost(item.get("cost"))
                    if option and value is not None:
                        costs[option] = min(costs.get(option, value), value)
            if "Yari (one-handed)" in costs:
                costs["Yari (two-handed)"] = costs["Yari (one-handed)"]
            return {**equipment_costs_for_profile(), **costs}

    catalog = _knowledge_root().parent / "catalog" / "market-prices.yaml"
    if catalog.is_file():
        with catalog.open("r", encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
        general = raw.get("general") or {}
        rows = (
            *general.get("melee_weapons", ()), *general.get("armour", ()),
            *general.get("drugs_and_poisons", ()),
        )
        for item in rows:
            option = EQUIPMENT_ITEM_TO_OPTION.get(item.get("id"))
            value = _expected_cost(item.get("cost"))
            if option and value is not None:
                costs[option] = value
        for section in (raw.get("lustria") or {}).values():
            if not isinstance(section, (list, tuple)):
                continue
            for item in section:
                option = EQUIPMENT_ITEM_TO_OPTION.get(item.get("id"))
                value = _expected_cost(item.get("cost"))
                if option and value is not None:
                    costs.setdefault(option, value)
    khemri_catalog = _knowledge_root().parent / "catalog" / "market-prices-khemri.yaml"
    if khemri_catalog.is_file():
        with khemri_catalog.open("r", encoding="utf-8") as stream:
            raw_khemri = yaml.safe_load(stream)
        for section in raw_khemri.values():
            if not isinstance(section, (list, tuple)):
                continue
            for item in section:
                if not isinstance(item, dict):
                    continue
                option = EQUIPMENT_ITEM_TO_OPTION.get(item.get("id"))
                value = _expected_cost(item.get("cost"))
                if option and value is not None:
                    costs.setdefault(option, value)
    costs.setdefault("Natural attacks", 0.0)
    for path in _band_paths():
        with path.open("r", encoding="utf-8") as stream:
            band = yaml.safe_load(stream)
        for equipment_list in band.get("equipment_lists") or ():
            for item in equipment_list.get("items") or ():
                option = EQUIPMENT_ITEM_TO_OPTION.get(item.get("item_id"))
                value = _expected_cost(item.get("cost"))
                if option and option not in costs and value is not None:
                    costs[option] = value
    if "Yari (one-handed)" in costs:
        costs["Yari (two-handed)"] = costs["Yari (one-handed)"]
    return costs


def usable_main_weapons(profile: CandidateProfile) -> tuple[str, ...]:
    return tuple(weapon for weapon in profile.weapons if weapon not in MAIN_HAND_FORBIDDEN_WEAPONS)


def usable_offhand_options(profile: CandidateProfile) -> tuple[str, ...]:
    allowed = set(profile.weapons)
    allowed.update(profile.defenses)
    return tuple(option for option in OFF_HAND_OPTIONS if option == "None" or option in allowed)


def _compact_catalog_description(text: str, fallback: str, limit: int = 420) -> str:
    """Reduce raw catalogue entries to a compact rules-focused tooltip."""
    cleaned = " ".join(str(text).replace("\u200b", " ").split())
    if not cleaned:
        return fallback
    marker = re.search(r"\b(?:Range|Save):\s*", cleaned, flags=re.IGNORECASE)
    if marker:
        cleaned = cleaned[marker.start():]
    elif special := re.search(r"\bSpecial Rules\b", cleaned, flags=re.IGNORECASE):
        cleaned = cleaned[special.start():]
    else:
        return fallback
    cleaned = re.sub(r"\s+:\s*", ": ", cleaned)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit + 1]
    sentence_end = max(shortened.rfind(". "), shortened.rfind("; "))
    if sentence_end >= limit // 2:
        return shortened[:sentence_end + 1].rstrip()
    word_end = shortened.rfind(" ", 0, limit)
    return shortened[:word_end if word_end > 0 else limit].rstrip(" ,;:") + "…"


@lru_cache(maxsize=1)
def weapon_descriptions() -> dict[str, str]:
    path = _knowledge_root().parent / "catalog" / "weapons.yaml"
    if not path.is_file():
        path = _knowledge_root().parent / "catalog" / "source" / "close-combat-weapons.yaml"
    if not path.is_file():
        return {"Natural attacks": "Innate attacks without weapon modifiers; the off hand remains unavailable."}
    with path.open("r", encoding="utf-8") as stream:
        records = yaml.safe_load(stream).get("records", ())
    raw_descriptions = {
        str(row["name"]): str(row.get("rule_summary", row.get("text", "")))
        for row in records
    }
    aliases = {
        "Double-handed weapon": "Double-handed weapon",
        "Elven greatsword": "Double-handed Elven sword",
        "Beastlash": "Beastmaster's whip",
        "Yari (one-handed)": "Yari",
        "Yari (two-handed)": "Yari",
    }
    def normalized(value):
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
        return " ".join(value.replace("2h", "double-handed").replace(" of ", " ").split())
    by_normalized = {normalized(name): description for name, description in raw_descriptions.items()}
    descriptions = {}
    for weapon in WEAPONS_ALL:
        source_name = aliases.get(weapon, weapon)
        raw = by_normalized.get(normalized(source_name), "")
        fallback = f"{weapon}: the simulator applies its modelled close-combat rules."
        descriptions[weapon] = _compact_catalog_description(raw, fallback)
    descriptions["Mace"] = "Mace, hammer, or club. All three use the same rules and can cause Stunned results on a 2–4 injury roll."
    descriptions["Natural attacks"] = "Innate attacks without weapon modifiers; the off hand remains unavailable."
    return descriptions


@lru_cache(maxsize=1)
def armour_descriptions() -> dict[str, str]:
    path = _knowledge_root().parent / "catalog" / "armour-and-equipment.yaml"
    if not path.is_file():
        path = _knowledge_root().parent / "catalog" / "source" / "armour.yaml"
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as stream:
        records = yaml.safe_load(stream).get("records", ())
    raw_descriptions = {
        str(row["name"]): str(row.get("rule_summary", row.get("text", "")))
        for row in records
    }
    def normalized(value):
        return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().casefold()
    by_normalized = {normalized(name): description for name, description in raw_descriptions.items()}
    descriptions = {}
    for armour in BODY_ARMORS:
        raw = by_normalized.get(normalized(armour), "")
        fallback = f"{armour}: the simulator applies its modelled armour save and special rules."
        descriptions[armour] = _compact_catalog_description(raw, fallback)
    descriptions["No Armour"] = "No body armour is equipped. Other saves may still apply."
    return descriptions
