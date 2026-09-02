"""Representative profiles and legal equipment for random opponents."""

DIFFICULTIES = ("Low", "Medium", "High")


def _profile(difficulty, weight, bands, equipment, **stats):
    # Enemy definitions still use the former Spanish abbreviations. Expose the
    # canonical Mordheim characteristics used by the rest of the application.
    for old, canonical in {"HA": "WS", "F": "S", "R": "T", "H": "W"}.items():
        if old in stats:
            stats[canonical] = stats.pop(old)
    return {
        **stats,
        "difficulty": difficulty,
        "weight": float(weight),
        "bands": bands,
        "equipment": equipment,
    }


# Cost and rarity only affect random selection. A rarity of zero represents a
# common item; higher values make the item less likely to be selected.
COMMON_HUMAN = {
    "main": [("Dagger", 2, 0), ("Mace", 3, 0), ("Axe", 5, 0),
             ("Sword", 10, 0), ("Spear", 10, 0), ("Halberd", 10, 0),
             ("Double-handed weapon", 15, 0), ("Flail", 15, 0), ("Pistol", 15, 0),
             ("Duelling pistol", 30, 10)],
    "off": [("None", 0, 0), ("Dagger", 2, 0), ("Mace", 3, 0),
            ("Axe", 5, 0), ("Sword", 10, 0), ("Shield", 5, 0),
            ("Buckler", 5, 0), ("Pistol", 15, 0)],
    "armor": [("No Armour", 0, 0), ("Light armour", 20, 0),
              ("Heavy armour", 50, 0), ("Ithilmar armour", 90, 11),
              ("Plate armour", 80, 9)],
    "helmet": (10, 0),
    "consumables": [
        ("preparation", "Crimson Shade", 39, 8),
        ("preparation", "Mandrake Root", 29, 9),
        ("preparation", "Tears of Shallaya", 17, 12),
        ("poison", "Black Lotus", 14, 9),
        ("poison", "Black Venom", 37, 8),
    ],
}

LIGHT_HUMAN = {
    **COMMON_HUMAN,
    "main": [("Dagger", 2, 0), ("Mace", 3, 0), ("Axe", 5, 0),
             ("Sword", 10, 0), ("Spear", 10, 0)],
    "armor": [("No Armour", 0, 0), ("Light armour", 20, 0)],
}

DWARF = {
    "main": [("Mace", 3, 0), ("Axe", 5, 0), ("Sword", 10, 0),
             ("Double-handed weapon", 15, 0), ("Dwarf axe", 15, 8)],
    "off": [("None", 0, 0), ("Dagger", 2, 0), ("Mace", 3, 0),
            ("Axe", 5, 0), ("Shield", 5, 0), ("Dwarf axe", 15, 8)],
    "armor": [("No Armour", 0, 0), ("Light armour", 20, 0),
              ("Heavy armour", 50, 0), ("Gromril armour", 150, 9)],
    "helmet": (10, 0),
}

SKAVEN = {
    "main": [("Dagger", 2, 0), ("Mace", 3, 0), ("Sword", 10, 0),
             ("Spear", 10, 0), ("Fighting claws", 35, 8),
             ("Weeping blades", 50, 10), ("Disease dagger", 10, 6),
             ("Censer", 40, 9), ("Yari (one-handed)", 10, 6),
             ("Yari (two-handed)", 15, 7), ("Death knife", 20, 8)],
    "off": [("None", 0, 0), ("Dagger", 2, 0), ("Sword", 10, 0),
            ("Shield", 5, 0)],
    "armor": [("No Armour", 0, 0), ("Light armour", 20, 0),
              ("Eshin assassin robes", 50, 10)],
    "helmet": (10, 0),
    "consumables": [
        ("poison", "Black Lotus", 14, 7),
        ("poison", "Black Venom", 37, 8),
        ("poison", "Devil's Toxin", 22, 7),
        ("poison", "Manbane", 37, 9),
    ],
}

ORC = {
    "main": [("Dagger", 2, 0), ("Mace", 3, 0), ("Axe", 5, 0),
             ("Sword", 10, 0), ("Spear", 10, 0), ("Choppa", 15, 0),
             ("Double-handed weapon", 15, 0), ("Chained Squig", 10, 0),
             ("Squig prodder", 15, 0)],
    "off": [("None", 0, 0), ("Dagger", 2, 0), ("Mace", 3, 0),
            ("Axe", 5, 0), ("Shield", 5, 0)],
    "armor": [("No Armour", 0, 0), ("Light armour", 20, 0),
              ("Heavy armour", 50, 0)],
    "helmet": (10, 0),
    "consumables": [
        ("poison", "Black Lotus", 14, 7),
        ("poison", "Black Venom", 37, 6),
        ("poison", "Devil's Toxin", 22, 7),
    ],
}

GOBLIN = {
    **ORC,
    "main": [*ORC["main"], ("Ball and chain", 15, 0)],
}

SIGMAR = {
    **COMMON_HUMAN,
    "main": [("Mace", 3, 0), ("Flail", 15, 0),
             ("Sigmarite hammer", 15, 0), ("Steel whip", 10, 0),
             ("Double-handed weapon", 15, 0)],
}

PIRATE = {
    **COMMON_HUMAN,
    "main": [("Dagger", 2, 0), ("Mace", 3, 0), ("Axe", 5, 0),
             ("Long boat hook", 8, 0), ("Pirate scourge", 8, 0),
             ("Sword", 10, 0), ("Cutlass", 15, 0)],
}

LIZARD = {
    "main": [("Mace", 3, 0), ("Axe", 5, 0), ("Spear", 10, 0),
             ("Stone axe", 15, 0)],
    "off": [("None", 0, 0), ("Mace", 3, 0), ("Axe", 5, 0),
            ("Shield", 5, 0)],
    "armor": [("No Armour", 0, 0), ("Light armour", 20, 0)],
    "helmet": (10, 0),
    "consumables": [
        ("poison", "Reptile Venom", 5, 0),
        ("poison", "Black Lotus", 14, 0),
        ("poison", "Black Venom", 37, 0),
        ("poison", "Nightshade", 19, 6),
        ("poison", "Manbane", 37, 9),
    ],
}

UNARMED = {
    "main": [("Mace", 0, 0)],
    "off": [("None", 0, 0)],
    "armor": [("No Armour", 0, 0)],
    "helmet": None,
}


# These weights are not official percentages. They are obtained by grouping equivalent profiles.
# The grouping also combines appearances in warband lists, allowed slots, and
# mandatory or optional status. A rank-and-file warrior therefore carries much more
# weight than a rare 0-1 elite model that players may not purchase.
ENEMY_PROFILES = {
    "Human recruit": _profile("Low", 22, 12, LIGHT_HUMAN,
        HA=2, F=3, R=3, H=1, I=3, A=1),
    "Human warrior": _profile("Low", 48, 18, COMMON_HUMAN,
        HA=3, F=3, R=3, H=1, I=3, A=1),
    "Human marksman": _profile("Low", 25, 13, LIGHT_HUMAN,
        HA=3, F=3, R=3, H=1, I=3, A=1),
    "Novice zealot or fanatic": _profile("Low", 13, 6, LIGHT_HUMAN,
        HA=2, F=3, R=3, H=1, I=3, A=1),
    "Goblin": _profile("Low", 18, 5, GOBLIN,
        HA=2, F=3, R=3, H=1, I=3, A=1),
    "Skink": _profile("Low", 14, 3, LIZARD,
        HA=2, F=3, R=2, H=1, I=4, A=1),
    "Zombie": _profile("Low", 17, 4, UNARMED,
        HA=2, F=3, R=3, H=1, I=1, A=1),
    "Skeleton": _profile("Low", 13, 4, LIGHT_HUMAN,
        HA=2, F=3, R=3, H=1, I=2, A=1),
    "Giant rat or lesser vermin": _profile("Low", 14, 5, UNARMED,
        HA=2, F=3, R=3, H=1, I=4, A=1),

    "Human veteran": _profile("Medium", 24, 15, COMMON_HUMAN,
        HA=4, F=3, R=3, H=1, I=4, A=1),
    "Swordsman or duelist": _profile("Medium", 12, 6, COMMON_HUMAN,
        HA=4, F=3, R=3, H=1, I=4, A=1, skills=["Expert Swordsman"]),
    "Sister of Sigmar": _profile("Medium", 12, 2, SIGMAR,
        HA=4, F=3, R=3, H=1, I=4, A=1),
    "Dwarf warrior": _profile("Medium", 14, 5, DWARF,
        HA=4, F=3, R=4, H=1, I=2, A=1),
    "Orc": _profile("Medium", 18, 5, ORC,
        HA=3, F=3, R=4, H=1, I=2, A=1),
    "Skaven": _profile("Medium", 20, 5, SKAVEN,
        HA=3, F=3, R=3, H=1, I=4, A=1),
    "Elf warrior": _profile("Medium", 10, 6, COMMON_HUMAN,
        HA=4, F=3, R=3, H=1, I=5, A=1),
    "Saurus": _profile("Medium", 10, 2, LIZARD,
        HA=3, F=4, R=4, H=1, I=2, A=1),
    "Beastman": _profile("Medium", 11, 4, COMMON_HUMAN,
        HA=4, F=4, R=4, H=1, I=3, A=1),
    "Ghoul": _profile("Medium", 12, 4, UNARMED,
        HA=3, F=3, R=4, H=1, I=3, A=2),
    "War wolf or feline": _profile("Medium", 9, 6, UNARMED,
        HA=4, F=4, R=3, H=1, I=4, A=1),
    "Pirate": _profile("Medium", 9, 1, PIRATE,
        HA=3, F=3, R=3, H=1, I=3, A=1),

    "Human leader": _profile("High", 10, 18, COMMON_HUMAN,
        HA=4, F=3, R=3, H=1, I=4, A=1),
    "Dwarf leader": _profile("High", 5, 5, DWARF,
        HA=5, F=3, R=4, H=1, I=3, A=1),
    "Orc leader": _profile("High", 5, 4, ORC,
        HA=4, F=4, R=4, H=1, I=3, A=1),
    "Skaven assassin": _profile("High", 5, 4, SKAVEN,
        HA=4, F=4, R=3, H=1, I=5, A=2),
    "Elf hero": _profile("High", 5, 6, COMMON_HUMAN,
        HA=5, F=3, R=3, H=1, I=6, A=1),
    "Possessed": _profile("High", 5, 1, UNARMED,
        HA=4, F=4, R=4, H=2, I=4, A=2),
    "Vampire": _profile("High", 4, 3, COMMON_HUMAN,
        HA=4, F=4, R=4, H=2, I=5, A=2),
    "Ogre": _profile("High", 4, 4, COMMON_HUMAN,
        HA=3, F=4, R=4, H=3, I=2, A=3),
    "Rat Ogre": _profile("High", 3, 2, UNARMED,
        HA=3, F=5, R=4, H=3, I=4, A=3),
    "Troll": _profile("High", 2, 2, UNARMED,
        HA=3, F=5, R=4, H=3, I=1, A=3),
}


def profiles_for_difficulties(difficulties):
    selected = set(difficulties)
    return [name for name, profile in ENEMY_PROFILES.items()
            if profile["difficulty"] in selected]
