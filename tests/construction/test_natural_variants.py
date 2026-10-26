"""C01c — natural attacks and Trollheim variants.

Each case is a printed line of a Trollheim source, decided through the same
compiled fighter the duel consumes:

* a creature that prints "no weapons or armour" fights with its own natural
  attack, keeps the printed Strength and Attacks value, is offered no piece and
  refuses one on the direct path;
* a profile that can carry weapons but whose list omits the free dagger keeps an
  ordinary empty hand instead of receiving a better natural attack;
* the printed bones are read as the source writes them: the Cannibal Dwarfs'
  "bones count as Clubs" keep the club identity, while the Ghouls' bones stay
  narrative and add no equipment piece;
* the Dire Wolves' Charge is the printed second attack of the charging turn, and
  it resolves as a real round;
* a coating needs a weapon to carry it, so a weaponless fighter refuses a poison.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_knowledge.loader import load_bands, runtime_bindings

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {str(package.band["id"]): package for package in load_bands("trollheim", KNOWLEDGE)}
NATURAL = "weapon.natural-attacks"

#: The selected C01c creatures that print no weapon at all.
WEAPONLESS = [
    ("trollheim-undead", "zombies"),
    ("trollheim-undead", "ghouls"),
    ("trollheim-undead", "dire-wolves"),
    ("chaos-streets-greenskins", "cave-squigs"),
    ("chaos-streets-greenskins", "troll"),
    ("khemri-cursed-of-karak-zorn", "shadowed"),
    ("khemri-tomb-guardians", "tomb-scorpions"),
    ("khemri-tomb-guardians", "stone-golem"),
    ("khemri-hobgoblin-raiders", "giant-wolves"),
    ("khemri-mages", "mechanical-beast"),
    ("khemri-necromancers", "nehekharan-vultures"),
    ("trollheim-skaven-clan-eshin", "giant-rats"),
    ("trollheim-skaven-clan-eshin", "rat-ogre"),
    ("trollheim-witch-hunters", "war-hounds"),
]

#: Creatures whose natural weapon is a published grant, not an inference.
PUBLISHED_NATURAL = [
    ("lustria-amazons", "great-cats"),
    ("lustria-dark-elves", "cold-ones"),
    ("lustria-norse", "wulfen"),
    ("lustria-norse", "wolves"),
    ("chaos-streets-mordheim-inhabitants", "street-dogs"),
    ("chaos-streets-sigmar-protectorate", "protectorate-mastiff"),
    ("chaos-streets-undead-bloodlines", "strigoi-vampire"),
    ("chaos-streets-undead-bloodlines", "carrion-ghoul"),
    ("chaos-streets-undead-bloodlines", "zombie"),
    ("chaos-streets-undead-bloodlines", "ghoul"),
    ("khemri-lahmian-brotherhood", "black-hounds"),
    ("khemri-lahmian-brotherhood", "jackals"),
    ("lustria-clan-pestilens", "rat-ogre"),
]

#: Profiles that can carry weapons but whose list has no free dagger.
ARMED_WITHOUT_DAGGER = [
    ("trollheim-witch-hunters", "flagellants"),
    ("khemri-tomb-guardians", "mortuary-acolytes"),
    ("khemri-tomb-guardians", "tomb-lord"),
    ("khemri-tomb-guardians", "skeleton-warriors"),
]


def row(band: str, profile_id: str) -> dict:
    return next(profile for profile in PACKAGES[band].profiles if str(profile["id"]) == profile_id)


def compiled(band: str, profile_id: str, **options):
    return compile_fighter(FighterBuild("mordheim", collection="trollheim", band_id=band,
                                        profile_id=profile_id, **options))


def offers(band: str, profile_id: str) -> set:
    facts = desktop_call("profileFacts", FighterBuild(
        "mordheim", collection="trollheim", band_id=band, profile_id=profile_id),
        package=PACKAGES[band], profile=row(band, profile_id))
    return {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}


@pytest.mark.parametrize("band,profile", WEAPONLESS)
def test_a_creature_with_no_weapon_fights_with_its_printed_natural_attack(band, profile):
    """The printed S and A travel; no fictitious piece is offered or accepted."""
    printed = row(band, profile)["characteristics"]
    unit = compiled(band, profile)
    assert NATURAL in unit.main_weapon.tags
    assert "weapon.fist" not in unit.main_weapon.tags
    assert unit.characteristics.strength == printed["S"]
    assert phases.build_attacks(phases.AttackPoolContext(fighter=unit)).attacks == printed["A"]
    # Neither the free dagger's Strength penalty nor its enemy armour bonus.
    assert (unit.main_weapon.strength_bonus, unit.main_weapon.target_armour_bonus) == (0, 0)
    assert not phases.ignores_unarmed_penalties(unit.global_effects)
    # The Troll's own vomiting attack is a printed special attack, not a piece.
    assert not {item for item in offers(band, profile) - {"weapon.vomit-attack"}
                if item.startswith(("weapon.", "armour.", "defence."))}
    with pytest.raises(ValueError):
        compiled(band, profile, main_weapon_id="weapon.sword")
    with pytest.raises(ValueError):
        compiled(band, profile, armour_id="armour.light-armour")


@pytest.mark.parametrize("band,profile", ARMED_WITHOUT_DAGGER)
def test_an_armed_profile_that_lacks_the_free_dagger_keeps_an_empty_hand(band, profile):
    """A list without a dagger is not a printed 'no weapons' clause."""
    unit = compiled(band, profile)
    assert "weapon.fist" in unit.main_weapon.tags
    assert NATURAL not in unit.main_weapon.tags
    # The printed unarmed penalties are still the fist's own.
    assert (unit.main_weapon.strength_bonus, unit.main_weapon.target_armour_bonus) == (-1, 1)
    assert any(item.startswith("weapon.") for item in offers(band, profile))


@pytest.mark.parametrize("band,profile", PUBLISHED_NATURAL)
def test_a_published_natural_weapon_grant_dresses_the_fighter(band, profile):
    """The band declares `profile.natural-attacks`; the compiler consumes it."""
    grants = [binding for rule in PACKAGES[band].special_rules
              if profile in ((rule.get("applies_to") or {}).get("profile_ids") or ())
              for binding in runtime_bindings(rule, "profile")]
    assert "profile.natural-attacks" in {binding["id"] for binding in grants}
    printed = row(band, profile)["characteristics"]
    unit = compiled(band, profile)
    assert NATURAL in unit.main_weapon.tags
    assert unit.characteristics.strength == printed["S"]
    assert phases.build_attacks(phases.AttackPoolContext(fighter=unit)).attacks == printed["A"]
    # "suffers no penalty for fighting without equipment": no fist Strength
    # penalty and no bonus armour to the opponent.
    assert (unit.main_weapon.strength_bonus, unit.main_weapon.target_armour_bonus) == (0, 0)
    # The grant never becomes a licence: the printed prohibition still refuses
    # an explicit blade or suit of armour on the direct path.
    assert not {item for item in offers(band, profile)
                if item.startswith(("weapon.", "armour.", "defence."))}
    with pytest.raises(ValueError):
        compiled(band, profile, main_weapon_id="weapon.sword")
    with pytest.raises(ValueError):
        compiled(band, profile, armour_id="armour.light-armour")


def test_the_shared_natural_weapons_declaration_reaches_every_band_that_cites_it():
    cited = 0
    for collection in ("mordheim", "trollheim"):
        for package in load_bands(collection, KNOWLEDGE):
            for rule in package.special_rules:
                if rule.get("rule_ref") != "shared-rule.natural-weapons":
                    continue
                cited += 1
                assert "profile.natural-attacks" in {
                    binding["id"] for binding in runtime_bindings(rule, "profile")}
    assert cited >= 2


def test_the_printed_bones_are_read_as_each_source_writes_them():
    """Cannibal Dwarfs count as Clubs; the Ghouls' bones are not equipment."""
    dwarfs = compiled("khemri-cursed-of-karak-zorn", "cannibal-dwarfs")
    assert "weapon.club" in dwarfs.main_weapon.tags
    assert "weapon.mace" in dwarfs.main_weapon.tags
    assert "weapon.natural-attacks" not in dwarfs.main_weapon.tags
    assert "weapon.club" in offers("khemri-cursed-of-karak-zorn", "cannibal-dwarfs")

    ghouls = compiled("trollheim-undead", "ghouls")
    assert NATURAL in ghouls.main_weapon.tags
    assert not {item for item in offers("trollheim-undead", "ghouls")
                if item.startswith(("weapon.", "armour.", "defence."))}
    with pytest.raises(ValueError):
        compiled("trollheim-undead", "ghouls", main_weapon_id="weapon.club")


def test_the_dire_wolves_charge_is_the_printed_second_attack():
    """One Attack normally, two when charging, and the round rolls both."""
    wolf = compiled("trollheim-undead", "dire-wolves")
    assert phases.build_attacks(phases.AttackPoolContext(fighter=wolf)).attacks == 1
    assert phases.build_attacks(phases.AttackPoolContext(fighter=wolf, charging=True)).attacks == 2
    foe = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
                                       main_weapon_id="weapon.mace"))
    dice = StrictDice([
        {"key": "round.0.second.fear.charged.0", "value": 2},
        {"key": "round.0.second.fear.charged.1", "value": 2},
        {"key": "round.0.first.attack.0.hit", "value": 2},
        {"key": "round.0.first.attack.1.hit", "value": 2},
        {"key": "round.0.second.attack.0.hit", "value": 2},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(wolf, foe, dice,
                            context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(wolf, foe, state, dice, choices)
    assert len(result.attacks) == 3
    dice.finish()
    choices.finish()


def test_the_tomb_scorpion_sting_rides_its_own_natural_attack():
    """The printed sting is the creature's attack, not a bought poison."""
    scorpion = compiled("khemri-tomb-guardians", "tomb-scorpions")
    assert NATURAL in scorpion.main_weapon.tags
    assert "poison.black-lotus" in scorpion.main_weapon.tags


def test_a_weaponless_fighter_refuses_a_poison_with_no_weapon_to_coat():
    """The offer never grants one, and the direct path agrees."""
    with pytest.raises(ValueError):
        compiled("trollheim-undead", "zombies", main_poison_id="poison.black-lotus")
    # A fighter that does carry a weapon keeps the ordinary coating path.
    vampire = compiled("trollheim-undead", "vampire", main_weapon_id="weapon.sword",
                       main_poison_id="poison.black-lotus")
    assert "poison.black-lotus" in vampire.main_weapon.tags


@pytest.mark.parametrize("hand", ["main", "off"])
@pytest.mark.parametrize("weapon", ["weapon.fist", "weapon.natural-attacks"])
def test_a_coating_requires_a_carried_weapon_in_either_hand(hand, weapon):
    loadout = {"main_weapon_id": "weapon.sword"}
    loadout["main_weapon_id" if hand == "main" else "off_hand_id"] = weapon
    loadout[f"{hand}_poison_id"] = "poison.black-lotus"
    with pytest.raises(ValueError, match="weapon in the hand it coats"):
        compile_fighter(FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 1, 3, 1), **loadout))


def test_poison_requires_a_weapon_in_its_own_hand():
    for off_hand in (None, "defence.shield"):
        with pytest.raises(ValueError, match="weapon in the hand it coats"):
            compile_fighter(FighterBuild(
                "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
                main_weapon_id="weapon.sword", off_hand_id=off_hand,
                off_poison_id="poison.black-lotus"))
    bearer = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
        main_weapon_id="weapon.sword", off_hand_id="weapon.dagger",
        off_poison_id="poison.black-lotus"))
    assert "poison.black-lotus" in bearer.off_hand.tags
    assert "poison.black-lotus" not in bearer.main_weapon.tags
