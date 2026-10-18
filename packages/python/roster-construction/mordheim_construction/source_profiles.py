"""Supplied profile states whose equipment access changes with that state."""
from dataclasses import replace

#: Compiled characteristics by their printed KB key.  Ballistic Skill is absent
#: on purpose: the duel never rolls it, so a supplied variant does not have to
#: agree on it.
CHARACTERISTIC_KEYS = {
    "M": "movement", "WS": "weapon_skill", "S": "strength", "T": "toughness",
    "W": "wounds", "I": "initiative", "A": "attacks", "Ld": "leadership",
}

#: The Human Rememberer's printed line (Dwarf Slayers / 0-1 Rememberer).
HUMAN_REMEMBERER = {"M": 4, "WS": 4, "BS": 2, "S": 3, "T": 3, "W": 1, "I": 4, "A": 1, "Ld": 7}

#: The Human Rememberer's printed Skill Table column: Speed in the place
#: where the Dwarf line has Special.
HUMAN_REMEMBERER_SKILL_ACCESS = ["combat", "shooting", "academic", "speed"]

#: The Town Crier 6 rules the Dwarf Slayers inherit as Dwarfs: the Dwarf
#: Special Skills table and the Dwarf racial rules (Hard to Kill, Hard Head and
#: Hatred of Orcs and Goblins).  A supplied Human Rememberer is a Human for
#: both, so neither rule reaches that profile.
DWARF_INHERITED_RULES = frozenset({
    "band--town-crier-6-dwarf-special-skills",
    "band--town-crier-6-inheritance",
})

#: The Mordheim rulebook list the Human variant is "instead equipped from".
MERCENARY_EQUIPMENT_LIST = "mercenary-equipment-lists"


def _without_dwarf_rules(package):
    """Drop the Human Rememberer from the rules the Slayers inherit as Dwarfs.

    The printed Skill Table gives that column to a Dwarf Rememberer; the Human
    line has Speed instead, and the inherited racial rules (Hard to Kill, Hard
    Head and Hatred of Orcs and Goblins) are Dwarf rules.  The supplied Human
    therefore receives neither, even when a consumer iterates the band's rules
    without reading `skill_access` or the compiled traits.
    """
    rules = package.special_rules
    if not any(str(rule.get("id")) in DWARF_INHERITED_RULES for rule in rules):
        return package
    return replace(package, special_rules=tuple(
        {**rule, "applies_to": {**(rule.get("applies_to") or {}), "profile_ids": [
            recipient for recipient in (rule.get("applies_to") or {}).get("profile_ids") or ()
            if recipient != "rememberer"]}}
        if str(rule.get("id")) in DWARF_INHERITED_RULES else rule
        for rule in rules))


def _supplied_rememberer(build, characteristics, traits, package, profile,
                         random_characteristics, root):
    """Apply the Human Rememberer the caller supplies for the Dwarf Slayers.

    The band prints that its Rememberer is rolled as a Dwarf (1-4) or a Human
    (5-6) at recruitment, and that a Human is instead equipped from the
    rulebook's Mercenary equipment list.  The recruitment roll is the excluded
    campaign producer; the supplied species is the construction fact this
    helper turns into the printed Human character line and equipment access.
    """
    native = (build.collection == "mordheim"
              and build.band_id == "dwarf-slayers-kaz"
              and build.profile_id == "rememberer")
    if not native or build.trait_overrides.get("species") != "human" or package is None:
        return build, characteristics, traits, package, profile, random_characteristics
    from mordheim_knowledge.loader import load_bands
    mercenaries = next((pack for pack in load_bands("mordheim", root)
                        if pack.band.get("id") == "mercenaries"), None)
    lists = tuple(row for row in (mercenaries.equipment_lists if mercenaries else ())
                  if str(row.get("id")) == MERCENARY_EQUIPMENT_LIST)
    if not lists:
        raise ValueError("the Mordheim rulebook Mercenary equipment list is missing")
    printed = profile.get("characteristics") or {}
    values = {}
    for key, field in CHARACTERISTIC_KEYS.items():
        if not isinstance(printed.get(key), int) or HUMAN_REMEMBERER[key] == printed[key]:
            continue
        current = getattr(characteristics, field)
        if current is None:
            raise ValueError(f"cannot apply the Human Rememberer's {field} line: no known base {field}")
        values[field] = current + HUMAN_REMEMBERER[key] - printed[key]
    if values:
        characteristics = replace(characteristics, **values)
    # The printed list belongs to the rulebook package; the added row is the
    # canonical one itself, so its items are not transcribed a second time.
    # The same column states the skill line: Speed replaces the Dwarf line's
    # Special, so the inherited Dwarf Special Skills never reach this one.
    return (build, characteristics, traits,
            _without_dwarf_rules(
                replace(package, equipment_lists=(*package.equipment_lists, *lists))),
            {**profile, "equipment_lists": [MERCENARY_EQUIPMENT_LIST],
             "skill_access": list(HUMAN_REMEMBERER_SKILL_ACCESS)},
            random_characteristics)


def prepare_source_profile(build, characteristics, traits, package, profile,
                           random_characteristics, root=None):
    """Apply Condemned's printed Fate without simulating experience advances."""
    build, characteristics, traits, package, profile, random_characteristics = _supplied_rememberer(
        build, characteristics, traits, package, profile, random_characteristics, root)
    fixed = build.trait_overrides.get("condemned_fixed_characteristics", [])
    native = (build.collection == "mordheim"
              and build.band_id == "marauders-of-chaos"
              and build.profile_id == "condemned")
    if not isinstance(fixed, list) or any(key not in ("WS", "S", "T", "A") for key in fixed):
        raise ValueError("Condemned fixed characteristics must be a list of WS, S, T or A")
    if len(fixed) != len(set(fixed)):
        raise ValueError("Condemned fixed characteristics must be distinct")
    if fixed and not native:
        raise ValueError("Only the Condemned has permanently fixed variable characteristics")
    if not native:
        return build, characteristics, traits, package, profile, random_characteristics
    if fixed and build.characteristics is None:
        raise ValueError("Supply the Condemned's permanently fixed characteristic values")
    random_characteristics = tuple(row for row in random_characteristics if row[0] not in fixed)
    if len(fixed) < 4:
        if (build.main_weapon_id not in {"weapon.dagger", "weapon.fist", "weapon.natural-attacks"}
                or build.off_hand_id or build.extra_hand_id or build.defence_ids
                or build.armour_id != "armour.no-armour"
                or build.main_material_id != "material.normal"
                or build.main_poison_id or build.off_poison_id or build.preparation_ids):
            raise ValueError("The Condemned uses no equipment while a characteristic remains variable")
        # The build's default dagger represents no explicit weapon selection.
        # Fate grants penalty-free unarmed blows; possession of idle items is
        # not a printed prohibition and does not erase the carried inventory.
        build = replace(build, main_weapon_id="weapon.natural-attacks")
    return build, characteristics, traits, package, profile, random_characteristics
