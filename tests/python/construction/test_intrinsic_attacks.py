"""C01a — intrinsic attacks and equipment restrictions of the native Mordheim rules.

Every expectation is a printed line of the canonical KB, decided by the shared
module through the embedded runtime:

* each of the 27 C01a clauses compiles a legal configuration with no fictitious
  physical weapon: the fighter fights with the profile's own bite, claw or bone
  (``weapon.natural-attacks``), or with the one piece the same line prints as
  what the bearer already carries (the Snotlings' pointy stick and the Skaven
  Slaves' scavenged dagger, both the dagger operator);
* a weapon, armour piece or other object the clause refuses is refused on the
  direct compilation path and is never offered by the selection layer;
* Fuerza, número de ataques y penalizaciones follow each source: the natural
  attack keeps the printed Strength and the printed Attacks value (the fist cap
  never applies), the dagger-kit profiles keep the dagger's +1 enemy armour save,
  and no clause receives a general immunity to the fist penalties;
* the printed exceptions survive the same profile's own 'no equipment' clause:
  the bones the Ghouls and the Charnel Guard use as primitive weapons keep their
  attacks, and a printed kit is never refused by the prohibition that names it;
* the Necrarchs' Banshee completes the 27 printed clauses: its profile line
  prints no Initiative at all (``I: null``), and that absence travels as an
  absence - the compiled fighter keeps ``initiative is None``, the combat order
  makes it strike last (``phases.resolve_priority``), and every test the printed
  rules resolve without a number resolves without one: Sweep's Initiative test
  cannot be passed by a profile that prints no Initiative, so its one attack
  hits, and a second fighter that also strikes last keeps the printed
  Initiative order instead of receiving an invented tie-break;
* the two intrinsic consequences the profile carries are connected to the
  existing mechanisms: the printed "not affected by any drug or poison" reaches
  the enemy's poison rider (``poison_immunity`` plus the compiler's drug
  suppression), and Cold Steel decides on the identity of the incoming attack -
  steel and iron at -1 to hit, blessed and magic weapons hitting normally, and
  the body identities its gloss excepts unable to harm the bearer at all - with
  the ordinary wound, armour, save and injury procedure untouched for the
  attacks that can harm her.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.attacks import _combined_effect
from mordheim_combat.modular.contexts import prepare_hit_context, prepare_wound_context
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_knowledge.loader import load_bands, load_items

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "sources" / "knowledge"
PACKAGES = {str(package.band["id"]): package for package in load_bands("mordheim", KNOWLEDGE)}

#: Mechanics a profile may be *given*: a weapon, an armour suit or a defence
#: piece that has a canonical item record. A concession with no such record (the
#: Troll's own vomiting attack) is not a piece a clause can refuse.
EQUIPMENT_KINDS = {"close-combat-weapon", "ranged-weapon", "armour", "shield-or-defence"}
EQUIPMENT_MECHANICS = {str(row.get("mechanic_id")) for row in load_items("mordheim", KNOWLEDGE)
                       if row.get("mechanic_id") and row.get("kind") in EQUIPMENT_KINDS}

NATURAL = "weapon.natural-attacks"
STICK = "weapon.dagger"

#: The 27 printed clauses: (band, profile, forbidden class, intrinsic attack).
#: ``weapons`` refuses held weapons, ``armour`` adds the armour and its pieces,
#: ``equipment`` is the printed 'no equipment' clause. The intrinsic attack is
#: what the compiled fighter fights with when the build carries nothing.
C01A = [
    ("halflings-mic", "piggies", "weapons", NATURAL),
    ("horned-hunters", "warhounds", "armour", NATURAL),
    ("lustrian-reavers", "barbary-monkey", "armour", NATURAL),
    ("lustrian-reavers", "estalian-warhound", "armour", NATURAL),
    ("maneaters", "sabretusks", "armour", NATURAL),
    ("marauders-of-chaos", "warhounds-of-chaos", "armour", NATURAL),
    ("mazzalupo-web", "black-sheep", "armour", NATURAL),
    ("necrarchs-mou", "abomination", "weapons", NATURAL),
    ("necrarchs-mou", "banshee", "equipment", NATURAL),
    ("necrarchs-the-soul-stealers-lotd1", "abomination", "weapons", NATURAL),
    ("necrarchs-the-soul-stealers-lotd1", "zombie", "equipment", NATURAL),
    ("night-goblins-mic", "cave-squigs", "armour", NATURAL),
    ("night-goblins-mic", "snotling-mob-consists-of-5-snotlings", "equipment", STICK),
    ("night-goblins-mic", "troll", "armour", NATURAL),
    ("norse-explorers-btb", "wolves", "armour", NATURAL),
    ("protectorate-of-sigmar-lotd3", "hound", "armour", NATURAL),
    ("skaven-of-clan-skryre-rel", "giant-rats", "armour", NATURAL),
    ("skaven-of-clan-skryre-rel", "skaven-slaves", "equipment", STICK),
    ("slavers-rel", "hounds", "armour", NATURAL),
    ("strigoi-kaz", "bats", "equipment", NATURAL),
    ("strigoi-kaz", "charnel-guard", "equipment", NATURAL),
    ("strigoi-kaz", "fell-bats", "equipment", NATURAL),
    ("strigoi-kaz", "ghouls", "equipment", NATURAL),
    ("strigoi-kaz", "vampire", "equipment", NATURAL),
    ("tomb-guardians", "tomb-scorpions", "armour", NATURAL),
    ("witch-hunters", "war-hounds", "armour", NATURAL),
    ("wood-elves-of-arden-mou", "ivy-ferret", "equipment", NATURAL),
]


def profile_row(band: str, profile_id: str) -> dict:
    return next(row for row in PACKAGES[band].profiles if str(row["id"]) == profile_id)


def compiled(band: str, profile_id: str, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile_id, **options))


def offers(band: str, profile_id: str) -> set:
    row = profile_row(band, profile_id)
    facts = desktop_call("profileFacts", FighterBuild("mordheim", band_id=band, profile_id=profile_id),
                         package=PACKAGES[band], profile=row)
    return {str(entry["item_id"]) for entry in facts.get("equipment_access") or ()}


@pytest.mark.parametrize("band,profile,forbidden,intrinsic", C01A)
@pytest.mark.compilation
def test_every_clause_fights_with_its_printed_intrinsic_attack(band, profile, forbidden, intrinsic):
    """A legal configuration with no fictitious weapon, at the printed S and A."""
    row = profile_row(band, profile)
    unit = compiled(band, profile)
    assert intrinsic in unit.main_weapon.tags
    assert "weapon.fist" not in unit.main_weapon.tags
    assert unit.characteristics.strength == row["characteristics"]["S"]
    assert phases.build_attacks(phases.AttackPoolContext(fighter=unit)).attacks \
        == row["characteristics"]["A"]
    # The dagger the line prints ('counts as a dagger') keeps the dagger's own
    # modifier; a bite, claw or bone carries no dagger-like penalty at all.
    assert unit.main_weapon.target_armour_bonus == (1 if intrinsic == STICK else 0)


@pytest.mark.parametrize("band,profile,forbidden,intrinsic", C01A)
@pytest.mark.eligibility
def test_every_clause_refuses_what_it_forbids_on_the_direct_path(band, profile, forbidden, intrinsic):
    """The printed refusal, asked of a build that never passed through a picker."""
    with pytest.raises(ValueError):
        compiled(band, profile, main_weapon_id="weapon.sword")
    if forbidden in {"armour", "equipment"}:
        with pytest.raises(ValueError):
            compiled(band, profile, armour_id="armour.light-armour")
        with pytest.raises(ValueError):
            compiled(band, profile, defence_ids=("defence.helmet",))
    if forbidden == "equipment":
        # 'No equipment' is not only weapons and armour: a coating and a
        # preparation are objects the bearer carries.
        with pytest.raises(ValueError):
            compiled(band, profile, main_poison_id="poison.black-lotus")
        with pytest.raises(ValueError):
            compiled(band, profile, preparation_ids=("preparation.mandrake-root",))


@pytest.mark.parametrize("band,profile,forbidden,intrinsic", C01A)
@pytest.mark.eligibility
def test_the_selection_layer_offers_no_piece_the_clause_refuses(band, profile, forbidden, intrinsic):
    """The offered set carries no weapon, armour or defence beyond the printed kit."""
    kit = set(profile_row(band, profile).get("fixed_equipment") or ())
    items = {str(row["id"]): row for row in load_items("mordheim", KNOWLEDGE)}
    by_mechanic = {str(row.get("mechanic_id")) for row in items.values()
                   if row["id"] in kit and row.get("mechanic_id")}
    offered = offers(band, profile)
    assert offered & EQUIPMENT_MECHANICS == by_mechanic
    assert offered & {item for item, row in items.items() if row.get("kind") in EQUIPMENT_KINDS} <= kit


#: (band, profile, printed attacks, the rolls the round asks for). The foe
#: carries one attack and is charged, so every recorded To Hit roll above the
#: foe's own is one real attack of the intrinsic weapon; the fear rolls are the
#: charge test the Ghoul's cause-fear rule forces on the charged fighter.
DUEL = [
    ("night-goblins-mic", "snotling-mob-consists-of-5-snotlings", 1, [
        ("round.0.first.attack.0.hit", 2), ("round.0.second.attack.0.hit", 2)]),
    ("skaven-of-clan-skryre-rel", "skaven-slaves", 1, [
        ("round.0.first.attack.0.hit", 2), ("round.0.second.attack.0.hit", 2)]),
    ("strigoi-kaz", "ghouls", 2, [
        ("round.0.second.fear.charged.0", 2), ("round.0.second.fear.charged.1", 2),
        ("round.0.first.attack.0.hit", 2), ("round.0.first.attack.1.hit", 2),
        ("round.0.second.attack.0.hit", 2)]),
]


@pytest.mark.parametrize("band,profile,attacks,rolls", DUEL)
@pytest.mark.rule_behavior
def test_the_printed_kit_and_the_printed_bones_reach_the_duel(band, profile, attacks, rolls):
    """The declared attack resolves as a real round, not merely as a binding."""
    unit = compiled(band, profile)
    foe = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
                                       main_weapon_id="weapon.mace"))
    dice = StrictDice([{"key": key, "value": value} for key, value in rolls])
    choices = StrictDecisions([])
    state = initialize_duel(unit, foe, dice,
                            context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(unit, foe, state, dice, choices)
    assert len(result.attacks) == attacks + 1
    dice.finish()
    choices.finish()


@pytest.mark.compilation
def test_no_clause_receives_a_general_immunity_to_the_fist_penalties():
    """The printed 'no penalty' lines stay per-profile; no general fist waiver."""
    for band, profile, forbidden, intrinsic in C01A:
        unit = compiled(band, profile)
        assert not phases.ignores_unarmed_penalties(unit.global_effects), f"{band}/{profile}"
        assert unit.main_weapon.strength_bonus == 0, f"{band}/{profile}"


def foe(initiative: int = 5):
    return compile_fighter(FighterBuild("mordheim",
                                        Characteristics(3, 3, 3, 1, initiative, 1, leadership=7),
                                        main_weapon_id="weapon.mace"))


@pytest.mark.compilation
def test_the_blank_initiative_is_never_replaced_by_a_number():
    """The printed blank travels as an absence, and the order strikes last."""
    row = profile_row("necrarchs-mou", "banshee")
    assert row["characteristics"]["I"] is None
    unit = compiled("necrarchs-mou", "banshee")
    assert unit.characteristics.initiative is None
    # The remaining printed characteristics still arrive as their own numbers.
    assert (unit.characteristics.weapon_skill, unit.characteristics.strength,
            unit.characteristics.toughness, unit.characteristics.wounds,
            unit.characteristics.attacks, unit.characteristics.leadership) == (4, 3, 4, 1, 1, 5)
    opponent = foe()
    # The absent Initiative overrides the first-round charge floor: charging
    # raises an ordinary Initiative, never an absent one.
    assert phases.resolve_priority(phases.PriorityContext(unit, opponent, first_round=True, charging=True)) \
        == phases.PriorityResult(-1, None)
    assert phases.resolve_priority(phases.PriorityContext(unit, opponent, first_round=False)) \
        == phases.PriorityResult(-1, None)
    assert phases.resolve_priority(phases.PriorityContext(opponent, unit, first_round=True, charging=True)) \
        == phases.PriorityResult(1, 5)


@pytest.mark.rule_behavior
def test_a_real_round_charges_the_banshee_and_still_puts_it_last():
    """The declared order resolves inside one round, charging included."""
    unit = compiled("necrarchs-mou", "banshee")
    opponent = foe()
    dice = StrictDice([{"key": "round.0.second.fear.charged.0", "value": 3},
                       {"key": "round.0.second.fear.charged.1", "value": 3},
                       {"key": "round.0.second.attack.0.hit", "value": 3},
                       {"key": "round.0.first.attack.0.hit", "value": 3},
                       {"key": "round.0.first.attack.0.wound", "value": 3}])
    choices = StrictDecisions([])
    state = initialize_duel(unit, opponent, dice,
                            context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(unit, opponent, state, dice, choices)
    assert [attack.attacker.initiative for attack in result.attacks] == [5, None]
    dice.finish()
    choices.finish()


def _attack_contexts(attacker, defender):
    """The modular hit and wound contexts of one declared attack."""
    dice = StrictDice([])
    attacker_state = initialize_fighter(attacker, dice, "attacker")
    defender_state = initialize_fighter(defender, dice, "defender")
    weapon = attacker.main_weapon
    effect = _combined_effect(attacker, weapon)
    return (
        prepare_hit_context(attacker, defender, attacker_state, defender_state,
                            weapon, effect, allow_luck=False),
        prepare_wound_context(attacker, defender, attacker_state, defender_state,
                              weapon, effect, allow_luck=False),
    )


def _human(weapon_id, *, ws=4, strength=3, attacks=1, initiative=4, skills=()):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(ws, strength, 4, 1, initiative, attacks, leadership=7),
        main_weapon_id=weapon_id, skill_ids=tuple(skills)))


#: (attack identity, its printed To Hit modifier, whether Cold Steel leaves it
#: unable to harm the bearer). Steel and iron are at -1; a magical weapon hits
#: normally; the body identities the gloss excepts cannot harm her at all.
COLD_STEEL = [
    ("weapon.sword", -1, False),
    ("weapon.mace", -1, False),
    ("weapon.dagger", -1, False),
    ("weapon.club", 0, True),
    ("weapon.hellblade", 0, False),
    ("weapon.fist", 0, True),
    ("weapon.natural-attacks", 0, True),
]


@pytest.mark.parametrize("weapon_id,modifier,unharmed", COLD_STEEL)
@pytest.mark.rule_behavior
def test_cold_steel_reads_the_attack_identity_and_keeps_its_exceptions(weapon_id, modifier, unharmed):
    """The clause decides on the weapon carried, never on a visible name."""
    unit = compiled("necrarchs-mou", "banshee")
    attacker = _human(weapon_id)
    hit, wound = _attack_contexts(attacker, unit)
    base = phases.to_hit_target(hit.attacker_ws, hit.defender_ws)
    assert hit.modifier == modifier
    assert base - hit.modifier == (5 if modifier else 4)
    assert wound.unharmed is unharmed


@pytest.mark.rule_behavior
def test_a_club_offered_by_the_selection_layer_is_not_a_metal_weapon():
    """Selection → configuration → attack: the offered club carries weapon.club."""
    items = {str(row["id"]): row for row in load_items("mordheim", KNOWLEDGE)}
    assert items["club"]["mechanic_id"] == "weapon.club"
    band = "amazons-lustria"
    profile = next(row for row in PACKAGES[band].profiles
                   if "club" in offers(band, str(row["id"])))
    attacker = compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=str(profile["id"]),
        main_weapon_id=items["club"]["mechanic_id"]))
    unit = compiled("necrarchs-mou", "banshee")
    hit, wound = _attack_contexts(attacker, unit)
    # The shared mace behaviour is still present; only the metal identity is gone.
    assert "weapon.club" in attacker.main_weapon.tags
    assert "weapon.mace" in attacker.main_weapon.tags
    assert attacker.main_weapon.concussion is True
    assert hit.modifier == 0 and wound.unharmed is True


@pytest.mark.rule_behavior
def test_cold_steel_exempts_only_the_canonical_blessed_weapon():
    """The supplied Sisters blessing names one weapon, not the whole bearer.

    ``condition.blessed-weapon`` is the canonical supplied result of the printed
    blessing: it marks the weapon the bearer names with ``attack.blessed``.  The
    other hand keeps its ordinary Cold Steel treatment.
    """
    unit = compiled("necrarchs-mou", "banshee")
    bearer = compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 3, 4, 1, 4, 1, leadership=7),
        band_id="sisters-of-sigmar", profile_id="sister-superior",
        main_weapon_id="weapon.mace", off_hand_id="weapon.dagger",
        condition_ids=("condition.blessed-weapon",),
        trait_overrides={"blessed_weapon_slots": ["main"]}))
    assert "attack.blessed" in bearer.main_weapon.tags
    assert "attack.blessed" not in bearer.off_hand.tags
    blessed_hit, blessed_wound = _attack_contexts(bearer, unit)
    off_effect = _combined_effect(bearer, bearer.off_hand)
    dice = StrictDice([])
    off_hit = prepare_hit_context(
        bearer, unit, initialize_fighter(bearer, dice, "attacker"),
        initialize_fighter(unit, dice, "defender"), bearer.off_hand, off_effect,
        allow_luck=False)
    assert blessed_hit.modifier == 0 and blessed_wound.unharmed is False
    assert off_hit.modifier == -1


@pytest.mark.interaction
def test_a_steel_hit_wounds_the_banshee_through_the_ordinary_injury_procedure():
    """Composition: the admitted wound continues into the normal injury chart."""
    unit = compiled("necrarchs-mou", "banshee")
    attacker = _human("weapon.sword")
    dice = StrictDice([
        {"key": "duel.charge", "value": 3},
        {"key": "round.0.first.fear.charged.0", "value": 3},
        {"key": "round.0.first.fear.charged.1", "value": 3},
        {"key": "round.0.first.attack.0.hit", "value": 5},
        {"key": "round.0.first.attack.0.wound", "value": 5},
        {"key": "round.0.first.attack.0.injury.0", "value": 1},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(attacker, unit, dice, context=DuelContext())
    result = resolve_round(attacker, unit, state, dice, choices)
    attack = result.attacks[0]
    assert (attack.hit, attack.hit_target, attack.wounded, attack.damage) == (True, 5, True, 1)
    assert phases.Phase.INJURY in attack.trace
    dice.finish()
    choices.finish()


@pytest.mark.rule_behavior
def test_the_printed_poison_and_drug_immunity_reaches_the_enemy_attack():
    """An enemy poison rider is suppressed for the Banshee only."""
    unit = compiled("necrarchs-mou", "banshee")
    assert unit.global_effects.poison_immunity is True
    assert "mechanic.drug-immunity" in unit.global_effects.tags
    attacker = _human("weapon.weeping-blades")
    assert "poison.black-lotus" in attacker.main_weapon.tags
    dice = StrictDice([])
    attacker_state = initialize_fighter(attacker, dice, "attacker")
    immune_state = initialize_fighter(unit, dice, "defender")
    plain = compile_fighter(FighterBuild("mordheim", Characteristics(4, 3, 4, 1, 4, 1, leadership=7)))
    plain_state = initialize_fighter(plain, dice, "plain")
    weapon = attacker.main_weapon
    effect = _combined_effect(attacker, weapon)
    immune = prepare_wound_context(attacker, unit, attacker_state, immune_state, weapon, effect,
                                   hit_roll=6, allow_luck=False)
    control = prepare_wound_context(attacker, plain, attacker_state, plain_state, weapon, effect,
                                    hit_roll=6, allow_luck=False)
    assert immune.failure_still_wounds is False
    assert control.failure_still_wounds is True


@pytest.mark.interaction
def test_sweep_against_the_absent_initiative_resolves_instead_of_aborting():
    """Sweep's printed condition cannot be met, so its one attack hits."""
    unit = compiled("necrarchs-mou", "banshee")
    sweeper = _human("weapon.double-handed-weapon", ws=3, initiative=5, attacks=2,
                     skills=("skill.sweep",))
    dice = StrictDice([
        {"key": "round.0.first.fear.charge.0", "value": 3},
        {"key": "round.0.first.fear.charge.1", "value": 3},
        {"key": "round.0.first.attack.0.wound", "value": 2},
        {"key": "round.0.second.attack.0.hit", "value": 2},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(sweeper, unit, dice,
                            context=DuelContext(charging=("first",), active_participant="first"))
    result = resolve_round(sweeper, unit, state, dice, choices)
    sweep, reply = result.attacks
    assert (sweep.hit, sweep.hit_target, sweep.wounded) == (True, 0, False)
    assert reply.hit is False
    dice.finish()
    choices.finish()


@pytest.mark.interaction
def test_a_second_strike_last_attacker_keeps_the_printed_initiative_order():
    """Both strike last: the printed Initiative orders the pair, no roll invented."""
    unit = compiled("necrarchs-mou", "banshee")
    great = _human("weapon.double-handed-weapon", attacks=2)
    assert phases.resolve_priority(phases.PriorityContext(unit, great)) \
        == phases.PriorityResult(-1, None)
    assert phases.resolve_priority(phases.PriorityContext(great, unit)) \
        == phases.PriorityResult(-1, 4)
    absent, printed = phases.PriorityResult(-1, None), phases.PriorityResult(-1, 4)
    assert phases.first_acts_before(printed, absent, StrictDice([])) is True
    assert phases.first_acts_before(absent, printed, StrictDice([])) is False
    # Two absent values are not separated by Initiative: the printed tie roll decides.
    assert phases.first_acts_before(absent, absent, StrictDice([{"key": "tie", "value": 5}]), key="tie") is True
    assert phases.first_acts_before(absent, absent, StrictDice([{"key": "tie", "value": 2}]), key="tie") is False


@pytest.mark.interaction
def test_the_round_orders_two_strike_last_fighters_without_an_absent_value():
    """The great weapon and the Banshee both strike last; 4 orders against None."""
    unit = compiled("necrarchs-mou", "banshee")
    great = _human("weapon.double-handed-weapon", attacks=2)
    dice = StrictDice([
        {"key": "duel.charge", "value": 3},
        {"key": "round.0.first.fear.charged.0", "value": 3},
        {"key": "round.0.first.fear.charged.1", "value": 3},
        {"key": "round.0.first.attack.0.hit", "value": 2},
        {"key": "round.0.first.attack.1.hit", "value": 2},
        {"key": "round.0.second.attack.0.hit", "value": 2},
    ])
    choices = StrictDecisions([])
    state = initialize_duel(great, unit, dice, context=DuelContext())
    result = resolve_round(great, unit, state, dice, choices)
    assert [attack.hit_target for attack in result.attacks] == [5, 5, 4]
    assert all("priority-tie" not in request.key for request in dice.requests)
    dice.finish()
    choices.finish()
