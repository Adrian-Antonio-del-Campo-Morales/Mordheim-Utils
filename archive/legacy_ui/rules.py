"""Simulator profile, equipment, and constant catalogue."""

# Optional rules that globally alter a simulation. The keys are
# guardan in the workbooks of Excel to that a game pueda reproducirse.
HOUSE_RULES = {
    "anti_offhand": {"name": "Off-hand Penalty", "description": "The extra attack granted by an off-hand weapon suffers -1 to hit."},
    "anti_dual": {"name": "Two-weapon Penalty", "description": "While fighting with two weapons, all attacks suffer -1 to hit."},
    "cheap_armour": {"name": "Cheaper Armour", "description": "Armour, helmets, shields, and bucklers cost half price, rounded up."},
    "better_armour": {"name": "Better Armour", "description": "All body armour grants +1 Armour point."},
    "hard_armour": {"name": "Harder Armour", "description": "Strength-based armour penetration starts at S5 instead of S4."},
    "useful_shields": {"name": "Useful Shields", "description": "A shield used with a hand weapon grants +1 additional Armour point against close-combat attacks."},
    "expensive_junk": {"name": "Expensive Junk", "description": "Clubs and slings cost 5 gc."},
}
HOUSE_RULE_CONFIG_KEYS = {
    "anti_offhand": "house_rule_offhand_penalty",
    "anti_dual": "house_rule_dual_penalty",
    "cheap_armour": "house_rule_cheap_armour",
    "better_armour": "house_rule_better_armour",
    "hard_armour": "house_rule_hard_armour",
    "useful_shields": "house_rule_useful_shields",
    "expensive_junk": "house_rule_expensive_junk",
}

# Skills and equipment

SKILLS = [
    "Expert Fighter",
    "Web of Steel",
    "Expert Swordsman",
    "Step Aside",
    "Mighty Blow",
    "Resilient",
    "Unstoppable Charge",
    "Ferocious Charge",
    "Lightning Reflexes",
    "Jump Up",
    "Strongman",
    "Tireless",
    "Axe Master",
    "Axe Expert",
    "Shield Strike",
    "Sweep",
    "Elven Agility",
    "Elven Agility",
    "Weapons of the North",
    "Art of Unarmed Combat",
    "Mighty Biceps",
    "Art of Unarmed Combat",
    "Red Fury",
    "Strength of Steel",
    "Crushing Blow",
    "Sure Strike",
    "Infallible",
    "Ignore Pain",
    "Always Strikes First",
    "Always Strikes First",
    "Sword Master",
    "Unbeatable Warrior",
    "Knife Fighting",
    "Shield Mastery",
    "Head Crusher",
    "Regeneration",
    "Monster Slayer",
    "Miniath",
    "Monstrous",
    "Very Tough",
    "Infinite Hatred",
    "Defensive Stance",
    "Tough as Steel",
    "Vampire Reflexes",
    "Bellowing Battle Roar",
    "Inspiring Sermon",
    "Sigmar's Sign",
    "Iron Sinews",
    "Hardy Constitution",
    "Thick Skull",
    "Hard to Kill",
    "Berserker",
    "Thick Skull",
    "Luck",
    "Virtue of Valour",
]

SKILL_DESCRIPTIONS = {
    'Expert Fighter': '+1 to wound rolls.',
    'Web of Steel': '+1 on the Critical Hit table.',
    'Expert Swordsman': 'Re-rolls missed attacks with swords or scimitars when charging.',
    'Step Aside': 'Unmodified 5+ special save against close-combat wounds.',
    'Mighty Blow': '+1 base Strength.',
    'Resilient': 'Incoming close-combat attacks suffer -1 Strength, to a minimum of 1.',
    'Unstoppable Charge': '+1 Weapon Skill while charging.',
    'Ferocious Charge': 'Doubles Attacks while charging, with -1 to hit that turn.',
    'Lightning Reflexes': 'When charged, attack order is determined by Initiative.',
    'Jump Up': 'Ignores Knocked Down results except those caused by a helmet.',
    'Strongman': 'Double-handed weapons no longer strike last.',
    'Tireless': 'Retains the Strength bonus of heavy weapons in later rounds.',
    'Axe Master': 'May parry with normal axes.',
    'Axe Expert': 'Re-rolls missed axe attacks when charging.',
    'Shield Strike': 'Gains an additional attack at the user’s Strength with poor armour penetration.',
    'Sweep': 'With a double-handed weapon, replaces all attacks with one automatic hit if the opponent fails an Initiative test.',
    'Elven Agility': '6+ special save in close combat; improves to 4+ with Step Aside.',
    'Weapons of the North': 'Re-rolls failed hit rolls with an axe or double-handed weapon.',
    'Art of Unarmed Combat': '+1 Attack while fighting unarmed or with claws.',
    'Mighty Biceps': 'Retains the Strength bonus of heavy weapons.',
    'Red Fury': '+1 Attack.',
    'Strength of Steel': '+1 Strength while charging.',
    'Crushing Blow': 'Attacks cannot be parried.',
    'Sure Strike': 'Re-rolls failed wound rolls.',
    'Infallible': 'Re-rolls failed hit rolls while charging.',
    'Ignore Pain': 'Stunned results become Knocked Down.',
    'Always Strikes First': 'Strikes first in close combat.',
    'Sword Master': 'Parries matching rolls and re-rolls one failed parry.',
    'Unbeatable Warrior': 'Improves parries and allows two parries with two Parry weapons.',
    'Knife Fighting': '+1 WS and +1 on the Injury table with a dagger or yambiya.',
    'Shield Mastery': 'A shield can parry and retains its armour save.',
    'Head Crusher': 'Knocked Down results caused by the warrior become Stunned.',
    'Regeneration': 'Regenerates unsaved wounds on 4+.',
    'Monster Slayer': 'Always wounds on at least 4+.',
    'Miniath': 'Re-rolls one failed parry when using a Parry weapon.',
    'Monstrous': '+1 Wound.',
    'Very Tough': '+1 armour save.',
    'Infinite Hatred': 'Re-rolls failed hit rolls.',
    'Defensive Stance': 'May parry with any weapon; Parry weapons match the roll.',
    'Tough as Steel': 'Only goes Out of Action on a 6 on the Injury table.',
    'Vampire Reflexes': '6+ special save against wounds.',
    'Bellowing Battle Roar': 'Enemies suffer -1 to hit in the first round.',
    'Inspiring Sermon': '+1 Attack for the turn.',
    "Sigmar's Sign": 'Undead and Possessed enemies lose one attack in the first round.',
    'Iron Sinews': '+1 Strength.',
    'Hardy Constitution': 'Ignores a critical hit on 5+.',
    'Thick Skull': 'Turns Stunned into Knocked Down on 3+, or 2+ with a Helmet.',
    'Hard to Kill': 'Only goes Out of Action on a 6 on the Injury table.',
    'Berserker': '+1 to hit while charging.',
    'Luck': 'Re-roll one of your own rolls once per battle.',
    'Virtue of Valour': 'Re-rolls hit rolls against enemies with higher Strength.',
}
WEAPONS_GENERAL = [
    "Sword",
    "Mace",
    "Dagger",
    "Axe",
    "Flail",
    "Morning star",
    "Halberd",
    "Spear",
    "Double-handed weapon",
    "Stone axe",
    "Rapier",
    "Pike",
    "Elven greatsword",
    "Ankus",
    "Yambiya",
    "Katar",
    "Scythe",
    "Cutlass",
    "Scimitar",
    "Great scimitar",
    "Bagh Nakh",
    "Sword breaker",
    "Pistol",
    "Duelling pistol",
]

WEAPONS_EXCLUSIVE = [
    "Natural attacks",
    "Brazier iron",
    "Brass knuckles",
    "War maul",
    "Double-bladed sword",
    "Dwarf axe",
    "Trident",
    "Spiked gauntlet",
    "Sigmarite hammer",
    "Steel whip",
    "Choppa",
    "Fighting claws",
    "Weeping blades",
    "Serpent staff",
    "Chained Squig",
    "Squig prodder",
    "Kusara Kama",
    "Witch sword",
    "Long boat hook",
    "Pirate scourge",
    "Bo",
    "Poisoned daggers",
    "Serpent whip",
    "Beastlash",
    "Sun gauntlet",
    "Unholy sword",
    "Stiletto",
    "Claw of the Old Ones",
    "Draich",
    "Yari (one-handed)",
    "Yari (two-handed)",
    "Death knife",
    "Disease dagger",
    "Censer",
    "Ball and chain",
]

MAIN_HAND_FORBIDDEN_WEAPONS = {"Sun gauntlet"}
WEAPONS_ALL = [*WEAPONS_GENERAL, *WEAPONS_EXCLUSIVE]
WEAPONS_MAIN = [
    weapon for weapon in WEAPONS_ALL
    if weapon not in MAIN_HAND_FORBIDDEN_WEAPONS
]

TWO_HANDED_WEAPONS = {
    "Double-handed weapon", "Flail", "Halberd", "Scythe", "Pike",
    "Elven greatsword", "Great scimitar", "Brazier iron",
    "War maul", "Double-bladed sword", "Serpent staff",
    "Kusara Kama", "Long boat hook", "Bo", "Draich", "Yari (two-handed)",
    "Censer", "Ball and chain",
}

PAIRED_WEAPONS = {
    "Bagh Nakh", "Brass knuckles", "Fighting claws",
    "Weeping blades", "Poisoned daggers",
}

# A morning star requires the wielder's full attention and cannot be paired with
# another weapon or a buckler. A spear only allows a shield or buckler. Choppas
# and Squig prodders have their own shield or gauntlet exception.
OFFHAND_RESTRICTED_WEAPONS = {
    *TWO_HANDED_WEAPONS,
    *PAIRED_WEAPONS,
    "Morning star",
    "Spear",
    "Choppa",
    "Squig prodder",
}

OFFHAND_GENERAL = [
    "None",
    "Shield",
    "Buckler",
    *(weapon for weapon in WEAPONS_GENERAL if weapon not in OFFHAND_RESTRICTED_WEAPONS),
]

OFFHAND_EXCLUSIVE = [
    "None",
    *(weapon for weapon in WEAPONS_EXCLUSIVE if weapon not in OFFHAND_RESTRICTED_WEAPONS),
]

OFF_HAND_OPTIONS = list(dict.fromkeys([*OFFHAND_GENERAL, *OFFHAND_EXCLUSIVE]))

WEAPON_MATERIALS = ["Normal", "Gromril", "Ithilmar", "Obsidian", "Dark steel"]

ARMORS = [
    "No Armour",
    "Light armour",
    "Heavy armour",
    "Gromril armour",
    "Ithilmar armour",
    "Toughened leathers",
    "Plate armour",
    "Wizard's robe",
    "Ninja robes",
    "Eshin assassin robes",
    "Spider chitin armour",
]

# The cloak grants a saving throw, but it is special equipment rather than
# body armour.
BODY_ARMORS = tuple(ARMORS)

PREPARATIONS = [
    "None",
    "Mad Cap Mushrooms",
    "Head-splitter mushrooms",
    "Crimson Shade",
    "Mandrake Root",
    "Tears of Shallaya",
]

PREPARATION_DESCRIPTIONS = {
    "None": "No drugs or antidotes.",
    "Mad Cap Mushrooms": "Frenzy: doubles Attacks until Knocked Down or Stunned.",
    "Head-splitter mushrooms": "Frenzy; also allows the use of a Ball and Chain.",
    "Crimson Shade": "+1 S and +1D3 I for the entire battle.",
    "Mandrake Root": "+1 T and Stunned results become Knocked Down instead.",
    "Tears of Shallaya": "Immunity to all poisons for the battle.",
}

POISONS = [
    "No Poison",
    "Black Lotus",
    "Black Venom",
    "Reptile Venom",
    "Manbane",
    "Wolfsbane",
    "Nightshade",
    "Bloodroot",
    "Devil's Toxin",
    "Spider Spittle",
]

EQUIPMENT_SELECTOR_OPTIONS = (
    "Helmet",
    "Lucky charm",
    "Sea Dragon cloak",
    *(value for value in PREPARATIONS if value != "None"),
)

POISON_DESCRIPTIONS = {
    "No Poison": "The weapon retains its normal rules.",
    "Black Lotus": "A natural 6 to hit wounds automatically.",
    "Black Venom": "+1 S when wounding and calculating armour penetration.",
    "Reptile Venom": "+1 S when wounding, without increasing armour penetration.",
    "Manbane": "+1 to wound rolls; a natural 1 always fails.",
    "Wolfsbane": "Causes critical hits on 5-6 unless a natural 6 is required to wound.",
    "Nightshade": "Each unsaved wound reduces the opponent’s Initiative by 1, to a minimum of 1.",
    "Bloodroot": "Doubles wounds caused.",
    "Devil's Toxin": "Re-rolls failed wound rolls; the re-roll cannot cause a critical hit.",
    "Spider Spittle": "to the hit, the opponent cheques R or is paralized.",
}


# The engine uses integers so batches remain compact and fast.

WEAPON_SWORD = 0
WEAPON_MACE = 1
WEAPON_DAGGER = 2
WEAPON_2H = 3
WEAPON_AXE = 4
WEAPON_FLAIL = 5
WEAPON_MORNING_STAR = 6
WEAPON_HALBERD = 7
WEAPON_SPEAR = 8
WEAPON_STONE_AXE = 9
WEAPON_RAPIER = 10
WEAPON_PIKE = 11
WEAPON_ELVEN_2H = 12
WEAPON_ANKUS = 13
WEAPON_YAMBIYA = 14
WEAPON_KATAR = 15
WEAPON_SCYTHE = 16
WEAPON_CUTLASS = 17
WEAPON_SCIMITAR = 18
WEAPON_GREAT_SCIMITAR = 19
WEAPON_BAGH_NAKH = 20
WEAPON_SWORD_BREAKER = 21
WEAPON_BRAZIER_STAFF = 22
WEAPON_BRASS_KNUCKLES = 23
WEAPON_WAR_MAUL = 24
WEAPON_DOUBLE_BLADE = 25
WEAPON_DWARF_AXE = 26
WEAPON_TRIDENT = 27
WEAPON_SPIKED_GAUNTLET = 28
WEAPON_SIGMARITE_HAMMER = 29
WEAPON_STEEL_WHIP = 30
WEAPON_CHOPPA = 31
WEAPON_ESHIN_CLAWS = 32
WEAPON_WEEPING_BLADES = 33
WEAPON_SERPENT_STAFF = 34
WEAPON_CHAINED_SQUIG = 35
WEAPON_SQUIG_PROD = 36
WEAPON_KUSARA_KAMA = 37
WEAPON_WITCH_BLADE = 38
WEAPON_LONG_HOOK = 39
WEAPON_PIRATE_SCOURGE = 40
WEAPON_PISTOL = 41
WEAPON_DUELING_PISTOL = 42
WEAPON_BO = 43
WEAPON_POISONED_DAGGERS = 44
WEAPON_SERPENT_WHIP = 45
WEAPON_BEASTMASTER_WHIP = 46
WEAPON_SUN_GAUNTLET = 47
WEAPON_UNHOLY_SWORD = 48
WEAPON_STILETTO = 49
WEAPON_ANCESTRAL_CLAW = 50
WEAPON_DRAICH = 51
WEAPON_YARI_ONE = 52
WEAPON_YARI_TWO = 53
WEAPON_DEATH_KNIFE = 54
WEAPON_PLAGUE_DAGGER = 55
WEAPON_CENSER = 56
WEAPON_BALL_AND_CHAIN = 57
WEAPON_NATURAL = 58
WEAPON_UNARMED = 59
WEAPON_LANCE = 60
WEAPON_MISERICORDIA = 61
WEAPON_STARBLADE = 62
WEAPON_STARSWORD = 63
WEAPON_BROADSWORD = 64
WEAPON_DRAGON_SWORD = 65
WEAPON_CATHAYAN_LONGSWORD = 66
WEAPON_CHAIN_STICKS = 67
WEAPON_MAN_CATCHER = 68
WEAPON_QUARTER_STAFF = 69
WEAPON_VOMIT_ATTACK = 70

OFF_NONE = -1
OFF_SHIELD = -2
OFF_BUCKLER = -3

MATERIAL_NORMAL = 0
MATERIAL_GROMRIL = 1
MATERIAL_ITHILMAR = 2
MATERIAL_OBSIDIAN = 3
MATERIAL_DARK_STEEL = 4
MATERIAL_DARK_ELF_BLADE = 5

ARMOR_NONE = 0
ARMOR_LIGHT = 1
ARMOR_HEAVY = 2
ARMOR_GROMRIL = 3
ARMOR_ITHILMAR = 4
ARMOR_HARDENED_LEATHER = 5
ARMOR_PLATE = 6
ARMOR_WIZARD_ROBE = 7
ARMOR_NINJA_GARB = 8
ARMOR_ESHIN_ROBES = 9
ARMOR_CHITIN = 10
ARMOR_CODES = {
    "No Armour": ARMOR_NONE,
    "Light armour": ARMOR_LIGHT,
    "Heavy armour": ARMOR_HEAVY,
    "Gromril armour": ARMOR_GROMRIL,
    "Ithilmar armour": ARMOR_ITHILMAR,
    "Toughened leathers": ARMOR_HARDENED_LEATHER,
    "Plate armour": ARMOR_PLATE,
    "Wizard's robe": ARMOR_WIZARD_ROBE,
    "Ninja robes": ARMOR_NINJA_GARB,
    "Eshin assassin robes": ARMOR_ESHIN_ROBES,
    "Spider chitin armour": ARMOR_CHITIN,
}

PREPARATION_NONE = 0
PREPARATION_CRIMSON_SHADE = 1
PREPARATION_MANDRAKE_ROOT = 2
PREPARATION_SHALLAYA_TEARS = 4
PREPARATION_MAD_CAP = 8
PREPARATION_HEAD_SPLITTER = 16

PREPARATION_CODES = {
    "None": PREPARATION_NONE,
    "Crimson Shade": PREPARATION_CRIMSON_SHADE,
    "Mandrake Root": PREPARATION_MANDRAKE_ROOT,
    "Tears of Shallaya": PREPARATION_SHALLAYA_TEARS,
    "Mad Cap Mushrooms": PREPARATION_MAD_CAP,
    "Head-splitter mushrooms": PREPARATION_HEAD_SPLITTER,
}

POISON_NONE = 0
POISON_BLACK_LOTUS = 1
POISON_BLACK_VENOM = 2
POISON_REPTILE = 3
POISON_MANBANE = 4
POISON_WOLFSBANE = 5
POISON_NIGHTSHADE = 6
POISON_BLOODROOT = 7
POISON_DEVIL_TOXIN = 8
POISON_SPIDER_SPIT = 9

POISON_CODES = {
    "No Poison": POISON_NONE,
    "Black Lotus": POISON_BLACK_LOTUS,
    "Black Venom": POISON_BLACK_VENOM,
    "Reptile Venom": POISON_REPTILE,
    "Manbane": POISON_MANBANE,
    "Wolfsbane": POISON_WOLFSBANE,
    "Nightshade": POISON_NIGHTSHADE,
    "Bloodroot": POISON_BLOODROOT,
    "Devil's Toxin": POISON_DEVIL_TOXIN,
    "Spider Spittle": POISON_SPIDER_SPIT,
}

WEAPON_CODES = {
    "Natural attacks": WEAPON_NATURAL,
    "Sword": WEAPON_SWORD,
    "Mace": WEAPON_MACE,
    "Dagger": WEAPON_DAGGER,
    "Double-handed weapon": WEAPON_2H,
    "Axe": WEAPON_AXE,
    "Flail": WEAPON_FLAIL,
    "Morning star": WEAPON_MORNING_STAR,
    "Halberd": WEAPON_HALBERD,
    "Spear": WEAPON_SPEAR,
    "Stone axe": WEAPON_STONE_AXE,
    "Rapier": WEAPON_RAPIER,
    "Pike": WEAPON_PIKE,
    "Elven greatsword": WEAPON_ELVEN_2H,
    "Ankus": WEAPON_ANKUS,
    "Yambiya": WEAPON_YAMBIYA,
    "Katar": WEAPON_KATAR,
    "Scythe": WEAPON_SCYTHE,
    "Cutlass": WEAPON_CUTLASS,
    "Scimitar": WEAPON_SCIMITAR,
    "Great scimitar": WEAPON_GREAT_SCIMITAR,
    "Bagh Nakh": WEAPON_BAGH_NAKH,
    "Sword breaker": WEAPON_SWORD_BREAKER,
    "Brazier iron": WEAPON_BRAZIER_STAFF,
    "Brass knuckles": WEAPON_BRASS_KNUCKLES,
    "War maul": WEAPON_WAR_MAUL,
    "Double-bladed sword": WEAPON_DOUBLE_BLADE,
    "Dwarf axe": WEAPON_DWARF_AXE,
    "Trident": WEAPON_TRIDENT,
    "Spiked gauntlet": WEAPON_SPIKED_GAUNTLET,
    "Sigmarite hammer": WEAPON_SIGMARITE_HAMMER,
    "Steel whip": WEAPON_STEEL_WHIP,
    "Choppa": WEAPON_CHOPPA,
    "Fighting claws": WEAPON_ESHIN_CLAWS,
    "Weeping blades": WEAPON_WEEPING_BLADES,
    "Serpent staff": WEAPON_SERPENT_STAFF,
    "Chained Squig": WEAPON_CHAINED_SQUIG,
    "Squig prodder": WEAPON_SQUIG_PROD,
    "Kusara Kama": WEAPON_KUSARA_KAMA,
    "Witch sword": WEAPON_WITCH_BLADE,
    "Long boat hook": WEAPON_LONG_HOOK,
    "Pirate scourge": WEAPON_PIRATE_SCOURGE,
    "Pistol": WEAPON_PISTOL,
    "Duelling pistol": WEAPON_DUELING_PISTOL,
    "Bo": WEAPON_BO,
    "Poisoned daggers": WEAPON_POISONED_DAGGERS,
    "Serpent whip": WEAPON_SERPENT_WHIP,
    "Beastlash": WEAPON_BEASTMASTER_WHIP,
    "Sun gauntlet": WEAPON_SUN_GAUNTLET,
    "Unholy sword": WEAPON_UNHOLY_SWORD,
    "Stiletto": WEAPON_STILETTO,
    "Claw of the Old Ones": WEAPON_ANCESTRAL_CLAW,
    "Draich": WEAPON_DRAICH,
    "Yari (one-handed)": WEAPON_YARI_ONE,
    "Yari (two-handed)": WEAPON_YARI_TWO,
    "Death knife": WEAPON_DEATH_KNIFE,
    "Disease dagger": WEAPON_PLAGUE_DAGGER,
    "Censer": WEAPON_CENSER,
    "Ball and chain": WEAPON_BALL_AND_CHAIN,
}

OFFHAND_CODES = {
    "None": OFF_NONE,
    "Shield": OFF_SHIELD,
    "Buckler": OFF_BUCKLER,
}
OFFHAND_CODES.update(
    {
        weapon: WEAPON_CODES[weapon]
        for weapon in OFF_HAND_OPTIONS
        if weapon not in OFFHAND_CODES
    }
)

MATERIAL_CODES = {
    "Normal": MATERIAL_NORMAL,
    "Gromril": MATERIAL_GROMRIL,
    "Ithilmar": MATERIAL_ITHILMAR,
    "Obsidian": MATERIAL_OBSIDIAN,
    "Dark steel": MATERIAL_DARK_STEEL,
    "Dark Elf blade": MATERIAL_DARK_ELF_BLADE,
}


# One mask bit per skill, so the kernel does not carry lists or dictionaries.
SKILL_EXPERT = 1 << 0
SKILL_CHARGE = 1 << 1
SKILL_SIDESTEP = 1 << 2
SKILL_POWER = 1 << 3
SKILL_SEASONED = 1 << 4
SKILL_FENCER = 1 << 5
SKILL_UNSTOPPABLE = 1 << 6
SKILL_CAT_REFLEXES = 1 << 7
SKILL_SPRING_UP = 1 << 8
SKILL_STRONGMAN = 1 << 9
SKILL_TIRELESS = 1 << 10
SKILL_AXE_MASTER = 1 << 11
SKILL_AXE_EXPERT = 1 << 12
SKILL_SHIELD_STRIKE = 1 << 13
SKILL_SWEEP = 1 << 14
SKILL_ELVEN_AGILITY = 1 << 15
SKILL_NORTHERN_WEAPONS = 1 << 16
SKILL_UNARMED_ART = 1 << 17
SKILL_RED_FURY = 1 << 18
SKILL_UNPARRYABLE = 1 << 19
SKILL_REROLL_WOUNDS = 1 << 20
SKILL_IGNORE_PAIN = 1 << 21
SKILL_ALWAYS_FIRST = 1 << 22
SKILL_SWORD_MASTER = 1 << 23
SKILL_SHIELD_MASTERY = 1 << 24
SKILL_MINIATH = 1 << 25
SKILL_MONSTROUS = 1 << 26
SKILL_VERY_TOUGH = 1 << 27
SKILL_REROLL_HITS = 1 << 28
SKILL_DEFENSIVE_STANCE = 1 << 29
SKILL_VAMPIRE_REFLEXES = 1 << 30
SKILL_IRON_SINEWS = 1 << 31
SKILL_CHARGE_REROLL = 1 << 32
SKILL_HEAD_CRUSHER = 1 << 33
SKILL_REGENERATION = 1 << 34
SKILL_MONSTER_SLAYER = 1 << 35
SKILL_HARDENED_SKIN = 1 << 36
SKILL_CRITICAL_RESISTANCE = 1 << 37
SKILL_FEROCIOUS_CHARGE = 1 << 38
SKILL_CHARGE_STRENGTH = 1 << 39
SKILL_UNBEATABLE = 1 << 40
SKILL_KNIFE_FIGHT = 1 << 41
SKILL_BATTLE_ROAR = 1 << 42
SKILL_SIGMAR_SIGNAL = 1 << 43
SKILL_VALOUR = 1 << 44
SKILL_STONE_SKULL = 1 << 45
SKILL_LUCK = 1 << 46
SKILL_STRIKE_TO_INJURE = 1 << 47
SKILL_DUELLIST = 1 << 48
SKILL_HATRED = 1 << 49
SKILL_PISTOL_CRACK_SHOT = 1 << 50
SKILL_ART_OF_SILENT_DEATH = 1 << 51
SKILL_CHARGE_EXTRA_ATTACK = 1 << 52
SKILL_SHAGGY_HIDE = 1 << 53
SKILL_BERSERKER_HIT = 1 << 54
SKILL_FOUL_ODOUR = 1 << 55
SKILL_TRUE_GRIT = 1 << 56
SKILL_NORSE_BERSERK_CHARGE = 1 << 57

# Exact source spellings and publication variants that share an already
# implemented mechanic. Distinct weapons are deliberately not approximated.
WEAPON_CODES.update({
    "Ball and Chain": WEAPON_BALL_AND_CHAIN,
    "Boat Hook": WEAPON_LONG_HOOK,
    "Brass Knuckles": WEAPON_BRASS_KNUCKLES,
    "Brazier Iron": WEAPON_BRAZIER_STAFF,
    "Cat or' Nine Tails": WEAPON_PIRATE_SCOURGE,
    "Cleaver": WEAPON_AXE,
    "Club": WEAPON_MACE, "Mace": WEAPON_MACE, "Hammer": WEAPON_MACE,
    "Club, Mace or Hammer": WEAPON_MACE,
    "Disease Dagger": WEAPON_PLAGUE_DAGGER,
    "Dwarf Axe": WEAPON_DWARF_AXE,
    "Fighting Claws": WEAPON_ESHIN_CLAWS,
    "Fist": WEAPON_UNARMED,
    "Morning Star": WEAPON_MORNING_STAR,
    "Pike (Merchant Caravans)": WEAPON_PIKE, "Pike (Tileans)": WEAPON_PIKE,
    "Poison Daggers": WEAPON_POISONED_DAGGERS,
    "Quarter Staff": WEAPON_BO,
    "Serpent Staff": WEAPON_SERPENT_STAFF,
    "Sigmarite Warhammer": WEAPON_SIGMARITE_HAMMER,
    "Steel Whip": WEAPON_STEEL_WHIP,
    "Sword Breaker": WEAPON_SWORD_BREAKER,
    "Weeping Blades": WEAPON_WEEPING_BLADES,
})

WEAPONS_ALL = [*WEAPONS_GENERAL, *WEAPONS_EXCLUSIVE]
BODY_ARMORS = tuple(ARMORS)
WEAPON_MATERIALS.append("Dark Elf blade")

_MORDHEIM_ADDITIONAL_WEAPON_CODES = {
    "Lance": WEAPON_LANCE, "Misericordia": WEAPON_MISERICORDIA,
    "Starblade": WEAPON_STARBLADE, "Starsword": WEAPON_STARSWORD,
    "Broadsword": WEAPON_BROADSWORD, "Dragon Sword": WEAPON_DRAGON_SWORD,
    "Cathayan Longsword": WEAPON_CATHAYAN_LONGSWORD,
    "Chain Sticks": WEAPON_CHAIN_STICKS, "Man-catcher": WEAPON_MAN_CATCHER,
    "Quarter Staff": WEAPON_QUARTER_STAFF,
    "Vomit attack": WEAPON_VOMIT_ATTACK,
}
WEAPON_CODES.update(_MORDHEIM_ADDITIONAL_WEAPON_CODES)
WEAPONS_EXCLUSIVE.extend(_MORDHEIM_ADDITIONAL_WEAPON_CODES)
WEAPONS_ALL = [*WEAPONS_GENERAL, *WEAPONS_EXCLUSIVE]
WEAPONS_MAIN = [weapon for weapon in WEAPONS_ALL if weapon not in MAIN_HAND_FORBIDDEN_WEAPONS]
TWO_HANDED_WEAPONS.update({"Dragon Sword", "Chain Sticks", "Man-catcher", "Quarter Staff"})
OFFHAND_RESTRICTED_WEAPONS.update(
    {"Lance", "Broadsword", "Dragon Sword", "Chain Sticks", "Man-catcher", "Quarter Staff", "Vomit attack"}
)
OFF_HAND_OPTIONS = list(dict.fromkeys([
    *OFF_HAND_OPTIONS,
    *(weapon for weapon in _MORDHEIM_ADDITIONAL_WEAPON_CODES
      if weapon not in OFFHAND_RESTRICTED_WEAPONS and weapon != "Lance"),
]))
OFFHAND_CODES.update({
    weapon: code for weapon, code in _MORDHEIM_ADDITIONAL_WEAPON_CODES.items()
    if weapon in OFF_HAND_OPTIONS
})
