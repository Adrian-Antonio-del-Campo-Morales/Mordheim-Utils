"""C01b — profile declarations and the intrinsic attacks they print.

Each clause of the package is a profile line of the Mordheim KB.  The shared
module answers three questions, and this file asks them in that order:

* the direct compilation path is legal with no fictitious physical weapon: the
  fighter fights with its own bite, claw, hoof or sting (``weapon.natural-attacks``)
  at the printed Strength and Attacks, or with the one piece the same line prints
  as what it already carries (the Warpstone Troll's club);
* the equipment the printed line refuses is refused on that direct path, and the
  offering layer never hands it to the selection.  ``equipment`` means every
  object the profile could carry (the printed "never carry equipment" family),
  while a line that only names weapons and armour keeps the teeth of its own
  words: those two families are refused and the line claims nothing else, so
  other shared requirements (such as a carried weapon for a coating) still apply;
* the intrinsic consequences already declared beside the line reach the modular
  duel: the Spawn's rolled Attacks, the Sabretusk's charge, the Spirit Host's
  spectral touch and the Tomb Scorpion's Black Lotus sting.  The Dragon Monk's
  printed Unarmed Mastery grants its +1 Attack while it fights with its body and
  not while it wields the quarterstaff its list sells.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import configuration_context, construction_call, desktop_call
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_knowledge.loader import load_bands, load_items

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {str(package.band["id"]): package for package in load_bands("mordheim", KNOWLEDGE)}

NATURAL = "weapon.natural-attacks"
CLUB = "weapon.mace"

#: The 21 printed clauses: (band, profile, what the line refuses, S, A, carried).
#: ``equipment`` is the printed 'never carry equipment' family; ``weapons-armour``
#: and ``weapons`` are the narrower lines; ``none`` prints no prohibition (it only
#: states how the creature fights); ``armour`` is the Dragon Monk's line.
C01B = [
    ("call-of-the-night-haint-mim", "spirit-hosts", "none", 2, 3, NATURAL),
    ("call-of-the-night-haint-mim", "poltergeists", "none", 1, 1, NATURAL),
    ("druchii-mic", "slavehounds", "none", 4, 1, NATURAL),
    ("fen-guard-mim", "treekin", "weapons", 4, 2, NATURAL),
    ("marauders-of-chaos", "warhounds-of-chaos", "weapons-armour", 4, 1, NATURAL),
    ("marauders-of-chaos", "spawn-of-chaos", "equipment", 4, 2, NATURAL),
    ("masters-of-horror-sylv", "wolfman", "equipment", 4, 2, NATURAL),
    ("norse-explorers-btb", "wulfen", "weapons-armour", 4, 2, NATURAL),
    ("norse-explorers-lustria", "wulfen", "weapons-armour", 4, 2, NATURAL),
    ("ogre-hunting-party-web", "sabretusks", "none", 4, 1, NATURAL),
    ("order-of-the-mare-web", "companion-filly", "equipment", 3, 2, NATURAL),
    ("pirates-of-the-cathayan-sea-sar", "dragon-monk", "armour", 3, 2, NATURAL),
    ("restless-dead", "zombies", "weapons-armour", 3, 1, NATURAL),
    ("restless-dead", "scarecrows", "equipment", 3, 2, NATURAL),
    ("survivors-of-strigos-sylv", "strigoi-vampire", "weapons", 4, 2, NATURAL),
    ("survivors-of-strigos-sylv", "ghouls", "equipment", 3, 2, NATURAL),
    ("tomb-guardians", "tomb-scorpions", "weapons-armour", 2, 1, NATURAL),
    ("undead", "ghouls", "equipment", 3, 2, NATURAL),
    ("undead", "zombies", "weapons-armour", 3, 1, NATURAL),
    ("underworld-alliance-mim", "sewer-squigs", "weapons-armour", 4, 1, NATURAL),
    ("underworld-alliance-mim", "warpstone-troll", "none", 4, 4, CLUB),
]


def profile_row(band: str, profile_id: str) -> dict:
    return next(row for row in PACKAGES[band].profiles if str(row["id"]) == profile_id)


def compiled(band: str, profile_id: str, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile_id, **options))


def offered(band: str, profile_id: str) -> set[str]:
    row = profile_row(band, profile_id)
    facts = desktop_call("profileFacts", FighterBuild("mordheim", band_id=band, profile_id=profile_id),
                         package=PACKAGES[band], profile=row)
    return {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}


DRAGON_MONK = ("pirates-of-the-cathayan-sea-sar", "dragon-monk")


@pytest.mark.parametrize("band,profile,refused,strength,attacks,carried", C01B)
@pytest.mark.compilation
def test_every_profile_fights_with_its_printed_intrinsic_attack(
    band, profile, refused, strength, attacks, carried,
):
    """A legal configuration with no fictitious weapon, at the printed S and A."""
    row = profile_row(band, profile)
    printed = row["characteristics"]["A"]
    unit = compiled(band, profile)
    assert ("weapon.fist" if (band, profile) == DRAGON_MONK else carried) in unit.main_weapon.tags
    if (band, profile) != DRAGON_MONK:
        assert "weapon.fist" not in unit.main_weapon.tags
    assert unit.characteristics.strength == row["characteristics"]["S"] == strength
    # The Spawn prints D6+1 and the phase operator rolls it; the Dragon Monk's
    # printed A1 becomes A2 while it fights unarmed (Unarmed Mastery).
    assert unit.characteristics.attacks == (printed if isinstance(printed, int) else 2)
    assert printed == attacks or printed == "D6+1" or (band, profile) == DRAGON_MONK
    assert phases.build_attacks(phases.AttackPoolContext(fighter=unit)).attacks == attacks
    # A body attack carries no dagger-like modifier: the enemy gains nothing.
    if (band, profile) == DRAGON_MONK:
        from mordheim_combat.modular.attacks import _combined_effect
        from mordheim_combat.modular.contexts import prepare_armour_context
        from mordheim_combat.modular.state import initialize_fighter
        current = initialize_fighter(unit, StrictDice([]), "monk")
        armour = prepare_armour_context(unit, unit, current, current, unit.main_weapon,
                                        _combined_effect(unit, unit.main_weapon))
        assert armour.strength == strength
        assert armour.target_armour_bonus == 0
    else:
        assert unit.main_weapon.target_armour_bonus == 0


@pytest.mark.parametrize("band,profile,refused,strength,attacks,carried", C01B)
@pytest.mark.eligibility
def test_every_profile_refuses_what_its_printed_line_refuses(
    band, profile, refused, strength, attacks, carried,
):
    """The printed refusal, asked of a build that never passed through a picker."""
    if refused in {"weapons", "weapons-armour"}:
        with pytest.raises(ValueError):
            compiled(band, profile, main_weapon_id="weapon.sword")
    if refused in {"armour", "weapons-armour"}:
        with pytest.raises(ValueError):
            compiled(band, profile, armour_id="armour.light-armour")
        with pytest.raises(ValueError):
            compiled(band, profile, defence_ids=("defence.helmet",))
    elif refused == "armour":
        # The Dragon Monk's line prints armour and nothing else: its list sells
        # the swords and staves the source gives it.
        with pytest.raises(ValueError):
            compiled(band, profile, armour_id="armour.light-armour")
        assert "weapon.sword" in offered(band, profile)
    if refused == "equipment":
        # 'Never carry equipment' is not only weapons and armour: a coating and a
        # preparation are objects the bearer would carry.
        with pytest.raises(ValueError):
            compiled(band, profile, main_poison_id="poison.black-lotus")
        with pytest.raises(ValueError):
            compiled(band, profile, preparation_ids=("preparation.mandrake-root",))
    if refused == "weapons-armour":
        # The narrower line names weapons and armour only; it adds no poison
        # prohibition. These profiles carry no weapon at all, so the shared
        # coating rule -- a poison needs a carried weapon -- refuses the poison,
        # not the printed line.
        with pytest.raises(ValueError, match="a poison needs a carried weapon in the hand it coats"):
            compiled(band, profile, main_poison_id="poison.black-lotus")


@pytest.mark.parametrize("band,profile,refused,strength,attacks,carried", C01B)
@pytest.mark.eligibility
def test_the_selection_layer_offers_no_piece_the_printed_line_refuses(
    band, profile, refused, strength, attacks, carried,
):
    """The offered set carries no armour or defence where the line refuses them."""
    kit = set(profile_row(band, profile).get("fixed_equipment") or ())
    items = {str(row["id"]): row for row in load_items("mordheim", KNOWLEDGE)}
    kinds = {item_id: row.get("kind") for item_id, row in items.items()}
    offered_ids = offered(band, profile)
    offered_armour = {item for item in offered_ids if kinds.get(item) in {"armour", "shield-or-defence"}}
    if refused in {"armour", "weapons-armour"}:
        assert offered_armour <= kit, f"{band}/{profile} offers {offered_armour - kit}"
    if refused in {"equipment", "weapons"}:
        offered_weapons = {item for item in offered_ids
                           if (kinds.get(item) in {"close-combat-weapon", "ranged-weapon"})}
        assert offered_weapons <= kit, f"{band}/{profile} offers {offered_weapons - kit}"


@pytest.mark.compilation
def test_the_declared_intrinsic_consequences_reach_the_compiled_fighter():
    """The rules beside each line bind the operator the modular engine reads."""
    expectations = {
        ("call-of-the-night-haint-mim", "spirit-hosts"): "trait.spectral-touch",
        ("marauders-of-chaos", "spawn-of-chaos"): "mechanic.spawn-special-attacks",
        ("ogre-hunting-party-web", "sabretusks"): "mechanic.sabretusk-charge",
        ("pirates-of-the-cathayan-sea-sar", "dragon-monk"): "skill.unarmed-fighting",
        ("tomb-guardians", "tomb-scorpions"): "poison.black-lotus",
    }
    for (band, profile), tag in expectations.items():
        unit = compiled(band, profile)
        assert tag in unit.global_effects.tags or tag in unit.main_weapon.tags, f"{band}/{profile}: {tag}"


SCORPION = ("tomb-guardians", "tomb-scorpions")
WITCH_ELVES = ("druchii-mic", "witch-elves")


@pytest.mark.compilation
def test_the_sting_applies_black_lotus_without_equipping_it():
    """The rider stays on the body attack and never becomes a carried flask."""
    scorpion = compiled(*SCORPION)
    assert "poison.black-lotus" in scorpion.main_weapon.tags
    # The rider is the weapon's own effect, so composing the attack must not add
    # a second poison contribution on top of it.
    assert "poison.black-lotus" not in scorpion.global_effects.tags
    with pytest.raises(ValueError):
        compiled(*SCORPION, main_poison_id="poison.black-lotus")


@pytest.mark.eligibility
def test_the_intrinsic_rule_grants_no_equipment_access():
    """Neither the offer nor the canonical verdict reads the rider as a grant."""
    assert "poison.black-lotus" not in offered(*SCORPION)
    build = FighterBuild("mordheim", band_id=SCORPION[0], profile_id=SCORPION[1])
    context = configuration_context(
        build, PACKAGES[SCORPION[0]], profile_row(*SCORPION),
        possession=("poison.black-lotus",),
        slots={"main_weapon_id": "weapon.natural-attacks", "main_poison_id": "poison.black-lotus"})
    blocked = {(issue["code"], issue["subject_ids"][-1])
               for issue in construction_call("validateConstruction", build, context)}
    assert ("equipment_not_permitted", "poison.black-lotus") in blocked


@pytest.mark.eligibility
def test_a_profile_with_printed_access_keeps_its_purchased_poison():
    """The distinction is the declaration's, not a blanket poison filter."""
    assert "poison.black-lotus" in offered(*WITCH_ELVES)
    witch = compiled(*WITCH_ELVES, main_weapon_id="weapon.dagger",
                     main_poison_id="poison.black-lotus")
    assert "poison.black-lotus" in witch.main_weapon.tags


@pytest.mark.rule_behavior
def test_the_dragon_monks_unarmed_mastery_follows_the_body_attack():
    """'+1 Attack when doing so' is the body attack; the quarterstaff keeps A1."""
    monk = compiled("pirates-of-the-cathayan-sea-sar", "dragon-monk")
    assert phases.build_attacks(phases.AttackPoolContext(fighter=monk)).attacks == 2
    armed = compiled("pirates-of-the-cathayan-sea-sar", "dragon-monk",
                     main_weapon_id="weapon.quarter-staff")
    assert phases.build_attacks(phases.AttackPoolContext(fighter=armed)).attacks == 1


@pytest.mark.eligibility
def test_the_dragon_monk_refuses_poison_on_his_legal_weapon():
    for poison in ("poison.black-lotus", "poison.black-venom"):
        with pytest.raises(ValueError, match="poison"):
            compiled(*DRAGON_MONK, main_weapon_id="weapon.quarter-staff", main_poison_id=poison)


@pytest.mark.rule_behavior
def test_the_dragon_monk_critical_threshold_belongs_only_to_body_attacks():
    from mordheim_combat.modular.attacks import _combined_effect
    from mordheim_combat.modular.contexts import prepare_wound_context
    from mordheim_combat.modular.state import initialize_fighter

    foe = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1),
                                       main_weapon_id="weapon.mace"))
    for weapon, threshold in ((None, 5), ("weapon.quarter-staff", 6)):
        monk = compiled(*DRAGON_MONK, **({"main_weapon_id": weapon} if weapon else {}))
        dice = StrictDice([])
        wound = prepare_wound_context(
            monk, foe, initialize_fighter(monk, dice, "monk"),
            initialize_fighter(foe, dice, "foe"), monk.main_weapon,
            _combined_effect(monk, monk.main_weapon), allow_luck=False)
        assert wound.critical_threshold == threshold
        dice.finish()


@pytest.mark.rule_behavior
def test_the_sabretusk_charge_replaces_its_single_attack():
    """The printed charge is A2, not a generic bonus on the A1 line."""
    sabretusk = compiled("ogre-hunting-party-web", "sabretusks")
    assert phases.build_attacks(phases.AttackPoolContext(fighter=sabretusk)).attacks == 1
    assert phases.build_attacks(phases.AttackPoolContext(
        fighter=sabretusk, charging=True)).attacks == 2


@pytest.mark.rule_behavior
def test_the_spawn_rolls_its_attacks_in_a_real_round():
    """The Spawn's D6+1 is resolved by the duel, not only by a binding."""
    spawn = compiled("marauders-of-chaos", "spawn-of-chaos")
    foe = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
                                       main_weapon_id="weapon.mace"))
    dice = StrictDice([
        {"key": "round.0.second.fear.charged.0", "value": 2},
        {"key": "round.0.second.fear.charged.1", "value": 2},
        {"key": "round.0.first.spawn-attacks", "value": 3},
        {"key": "round.0.first.attack.0.hit", "value": 1},
        {"key": "round.0.first.attack.1.hit", "value": 1},
        {"key": "round.0.first.attack.2.hit", "value": 1},
        {"key": "round.0.first.attack.3.hit", "value": 1},
        {"key": "round.0.second.attack.0.hit", "value": 1},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(spawn, foe, dice,
                            context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(spawn, foe, state, dice, choices)
    assert len(result.attacks) == 4 + 1
    dice.finish()
    choices.finish()
