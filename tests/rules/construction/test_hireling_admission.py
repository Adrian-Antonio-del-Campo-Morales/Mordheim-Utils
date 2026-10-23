"""Hireling admission: the duel participant route, not a synthetic fixture.

Every case goes through the canonical path the application uses: the hireling
packages `combat_packages` actually offers, `compile_fighter` on a real
`FighterBuild`, the shared eligibility module behind it and a modular consumer on
the compiled pair.  A profile whose printed rules are not implemented stays out
with a named refusal, a printed unique object reaches the duel through its
declared equivalence, and a trait fact only counts once a real round consequence
reads it.
"""
from __future__ import annotations

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_knowledge.campaign import load_campaign_catalog, load_hirelings

PACKAGES = [package for package in combat_packages("mordheim")
            if package.band["id"].startswith("hirelings.")]
BAND_OF = {profile["id"]: package.band["id"]
           for package in PACKAGES for profile in package.profiles}

# The three prepared fear/undead carriers; only the admitted core-grade one can
# be exercised while the other two profiles' intrinsic rules carry no runtime.
TRAIT_CARRIERS = ("hireling.hired-sword.ogre-bodyguard",)


class FixedDice:
    """Answers every duel request the same way; admission is not a dice claim."""

    def __init__(self, value: int = 3) -> None:
        self.value = value

    def roll(self, request):
        return self.value


def compile_hireling(profile_id: str, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=BAND_OF[profile_id], profile_id=profile_id,
        collection="mordheim", **options))


def plain_fighter():
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))


# --- the offered grades ------------------------------------------------------

@pytest.mark.phase2_construction
def test_every_normalized_grade_is_offered_including_core():
    assert sorted(package.band["id"] for package in PACKAGES) == [
        "hirelings.dramatis-personae.1a", "hirelings.dramatis-personae.1b",
        "hirelings.dramatis-personae.1c", "hirelings.dramatis-personae.2a",
        "hirelings.dramatis-personae.2b", "hirelings.dramatis-personae.core",
        "hirelings.hired-sword.1a", "hirelings.hired-sword.1b",
        "hirelings.hired-sword.1c", "hirelings.hired-sword.2a",
        "hirelings.hired-sword.2b", "hirelings.hired-sword.core",
    ]
    # The promoted 2B packages keep their original ids, so existing builds and
    # their construction contracts are untouched by this admission.
    assert "hireling.hired-sword.crimashin" in BAND_OF


@pytest.mark.phase2_construction
def test_a_core_grade_profile_compiles_and_fights():
    """The core kit is a printed "choose two weapons" group, not a crash."""
    bodyguard = compile_hireling("hireling.hired-sword.ogre-bodyguard",
                                 main_weapon_id="weapon.double-handed-weapon")
    assert bodyguard.global_effects is not None
    state = initialize_duel(bodyguard, plain_fighter(), FixedDice())
    assert state is not None


@pytest.mark.phase2_construction
def test_a_profile_with_pending_intrinsic_clauses_is_refused_by_name():
    """A profile is still refused by name while one printed clause has no runtime."""
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.witch")
    drenok = compile_hireling("hireling.dramatis.drenok-johansen-wielder-of-the-great-axe",
        defence_ids=("defence.sabertooth-hide",))
    assert "weapon.icefang-axe" in drenok.main_weapon.tags
    assert "mechanic.drenok-berserker" in drenok.global_effects.tags


@pytest.mark.phase2_construction
def test_the_resolved_clauses_admit_the_previously_refused_profiles():
    """The batch that classified the printed clauses admits the same profiles.

    Ninja Gnoblar's stealth, rooftop movement and hiring restriction and the Dark
    Emissary's spell list and alignment are recorded exclusions, so neither is
    refused for a pending clause any more; each now stops, if at all, at its own
    remaining data blocker, which the guard still names instead of admitting it.
    """
    prospector = compile_hireling("hireling.hired-sword.old-prospector",
        owned_item_ids=("blunderbuss", "hireling.hired-sword.old-prospector.item.pick"),
        main_weapon_id="weapon.double-handed-weapon")
    assert "weapon.double-handed-weapon" in prospector.main_weapon.tags
    gnoblar = compile_hireling("hireling.hired-sword.ninja-gnoblar")
    # The printed kit itself now resolves: the Bo is its mapped first weapon
    # and the Ninja Robe carries its own printed equivalences.
    assert "weapon.bo" in gnoblar.main_weapon.tags
    with pytest.raises(ValueError, match="canonical combat mapping"):
        compile_hireling("hireling.dramatis.dark-emissary")


@pytest.mark.phase2_construction
def test_the_bone_goliath_intrinsic_clauses_now_reach_the_duel():
    """Undead Construct and No Pain are delivered, so the refusal is gone.

    The same profile that the refusal above used to name now compiles with both
    of its printed intrinsic clauses bound to the canonical operators.
    """
    goliath = compile_hireling("hireling.hired-sword.bone-goliath",
                               main_weapon_id="weapon.natural-attacks")
    assert "mechanic.undead-construct" in goliath.global_effects.tags
    assert "skill.ignore-pain" in goliath.global_effects.tags
    assert "mechanic.causes-fear" in goliath.global_effects.tags


@pytest.mark.phase2_construction
def test_belandysh_printed_random_profile_and_complete_kit_compile():
    fighter = compile_hireling("hireling.dramatis.belandysh-condemned-champion-of-chen",
        main_weapon_id="weapon.broadsword-of-damnation", armour_id="armour.chaos-armour",
        defence_ids=("defence.helmet",))
    assert fighter.characteristics.wounds == 3
    assert fighter.random_characteristics == (
        ("WS", 1, 6, 0), ("S", 1, 6, 0), ("T", 1, 6, 0),
        ("I", 1, 6, 0), ("A", 1, 3, 0))
    assert fighter.main_weapon.strength_bonus == 2
    assert fighter.main_weapon.two_handed
    assert fighter.global_effects.strongman


# --- the printed unique object ----------------------------------------------

@pytest.mark.phase2_construction
def test_the_declared_equivalence_reaches_the_duel():
    """The Holy Man's staff counts as a double-handed weapon, so it fights as one."""
    holy_man = compile_hireling("hireling.hired-sword.holy-man",
                               main_weapon_id="weapon.double-handed-weapon")
    assert "weapon.double-handed-weapon" in holy_man.main_weapon.tags
    # The Grave Robber's Pickaxe counts as an axe and the Gravesman's Shovel as
    # a halberd; both heroes are now admitted, so each equivalence is exercised
    # on its own bearer instead of being named as a blocked one.
    robber = compile_hireling("hireling.hired-sword.grave-robber", main_weapon_id="weapon.axe")
    assert "weapon.axe" in robber.main_weapon.tags
    gravesman = compile_hireling("hireling.hired-sword.gravesman", main_weapon_id="weapon.halberd")
    assert "weapon.halberd" in gravesman.main_weapon.tags
    assert gravesman.main_weapon.two_handed


@pytest.mark.phase2_construction
def test_an_item_whose_own_rules_are_excluded_cannot_be_a_weapon():
    """A garment declared out of the duel is not a weapon in an active slot."""
    with pytest.raises(ValueError, match="non-duel unique equipment cannot occupy an active combat position"):
        compile_hireling(
            "hireling.dramatis.snerik-night-goblin-scout",
            main_weapon_id="hireling.dramatis.snerik-night-goblin-scout.item.camouflage-cloak")


@pytest.mark.phase2_construction
def test_source_unique_equivalences_reach_their_actual_active_slots():
    johann = compile_hireling("hireling.dramatis.johann-the-knife", main_weapon_id="weapon.sword",
                             off_hand_id="weapon.sword")
    assert johann.main_weapon.parry and johann.off_hand.parry
    assert "poison.black-lotus" in johann.main_weapon.tags
    assert "poison.black-lotus" in johann.off_hand.tags
    scout = compile_hireling("hireling.hired-sword.halfling-scout", main_weapon_id="weapon.dagger",
                             defence_ids=("defence.helmet",))
    assert scout.helmet_save == 4
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_hireling("hireling.hired-sword.halfling-scout", main_weapon_id="weapon.sword")
    # An explicit weapon outside the printed kit is refused by the kit matcher;
    # the Double-handed weapon is not the printed Bo of this kit.
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_hireling("hireling.hired-sword.ninja-gnoblar", main_weapon_id="weapon.double-handed-weapon")


@pytest.mark.phase2_construction
def test_the_printed_shovel_and_pry_bar_reach_the_gravesman():
    """The shovel counts as a halberd and the pry bar as a club that parries."""
    shovel = "hireling.hired-sword.gravesman.item.shovel"
    pry_bar = "hireling.hired-sword.gravesman.item.pry-bar"
    gravesman = compile_hireling("hireling.hired-sword.gravesman",
                                owned_item_ids=(shovel, pry_bar, "dagger"),
                                main_weapon_id="weapon.halberd")
    assert "weapon.halberd" in gravesman.main_weapon.tags
    # The printed kit carries both objects; the two-handed shovel owns both
    # hands, so the pry bar is the spare rather than a second active weapon.
    assert gravesman.off_hand is None
    club = compile_hireling("hireling.hired-sword.gravesman",
                            owned_item_ids=(shovel, pry_bar, "dagger"),
                            main_weapon_id="weapon.pry-bar")
    assert "weapon.pry-bar" in club.main_weapon.tags
    # The printed pry bar acts as a club in every sense and parries.
    assert club.main_weapon.concussion is True
    assert club.main_weapon.parry is True
    # The same equivalence route on another admitted bearer: the printed
    # equivalence selects the canonical mechanic, not the object's own id.
    holy_man = compile_hireling("hireling.hired-sword.holy-man",
                               owned_item_ids=("staff", "hammer"),
                               main_weapon_id="weapon.double-handed-weapon")
    assert "weapon.double-handed-weapon" in holy_man.main_weapon.tags


@pytest.mark.phase2_construction
def test_a_printed_unique_quantity_is_retained_and_missing_copy_is_refused():
    """Johann's two Long Daggers count as two Swords, with one throwing knife kit."""
    daggers = "hireling.dramatis.johann-the-knife.item.long-daggers"
    kit = (daggers, daggers, "throwing_knives")
    fighter = compile_hireling("hireling.dramatis.johann-the-knife",
        main_weapon_id="weapon.sword", off_hand_id="weapon.sword", owned_item_ids=kit)
    assert fighter.off_hand.parry
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_hireling("hireling.dramatis.johann-the-knife",
            main_weapon_id="weapon.sword", owned_item_ids=(daggers, "throwing_knives"))


@pytest.mark.phase2_construction
def test_aenur_unique_weapon_strength_is_not_granted_twice_by_its_intrinsic_rules():
    fighter = compile_hireling("hireling.dramatis.aenur", main_weapon_id="weapon.ienh-khain")
    assert fighter.main_weapon.strength_bonus == 1
    assert fighter.global_effects.strength_bonus == 1  # printed starting Mighty Blow
    assert fighter.main_weapon.critical_threshold == 5


# --- the prepared trait facts, with a live consequence ------------------------

@pytest.mark.phase2_construction
def test_the_prepared_trait_facts_reach_admitted_hirelings():
    bodyguard = compile_hireling("hireling.hired-sword.ogre-bodyguard",
                                 main_weapon_id="weapon.double-handed-weapon")
    assert "mechanic.causes-fear" in bodyguard.global_effects.tags
    assert "species.ogre" in bodyguard.global_effects.tags
    fury = compile_hireling("hireling.hired-sword.chaos-fury")
    assert "mechanic.causes-fear" in fury.global_effects.tags
    assert "nature.daemon" in fury.global_effects.tags
    # The Dark Mage's Fear and Despise Despoilers rows are admitted.
    mage = compile_hireling("hireling.hired-sword.dark-mage")
    assert "mechanic.causes-fear" in mage.global_effects.tags
    assert "mechanic.despise-despoilers" in mage.global_effects.tags


@pytest.mark.phase2_construction
def test_the_fanatic_reaches_the_duel_with_his_printed_weapon():
    """Maximilian's two intrinsic clauses resolve: leadership and the list.

    The printed double-handed holy weapon is carried through its declared
    double-handed class, Religious Fervour stays the separate Frenzy clause,
    and the hiring restriction is a campaign consequence rather than a duel
    blocker.
    """
    mad = compile_hireling("hireling.dramatis.maximilian-the-mad",
        main_weapon_id="weapon.double-handed-weapon",
        owned_item_ids=("hireling.dramatis.maximilian-the-mad.item.double-handed-holy-weapon",))
    assert "mechanic.fanatical-hatred" in mad.global_effects.tags
    assert "mechanic.automatic-leadership" in mad.global_effects.tags
    assert mad.global_effects.frenzy
    assert mad.main_weapon.two_handed
    assert "weapon.double-handed-weapon" in mad.main_weapon.tags


@pytest.mark.parametrize("carrier", TRAIT_CARRIERS)
@pytest.mark.phase3_rules
def test_a_hired_fear_causer_charges_the_opponent_for_a_die(carrier):
    """The consequence: an enemy charging the hireling spends a die and fails.

    A bool from `causes_fear` would not prove this; the round consumer decides
    whether the charge stands, and a refused charge is the printed outcome.
    """
    fearer = compile_hireling(carrier, main_weapon_id="weapon.double-handed-weapon"
                              if carrier.endswith("ogre-bodyguard") else "weapon.dagger")
    attacker = plain_fighter()
    assert causes_fear(fearer, attacker)
    # A charge is declared, so the fear test is the only roll the round asks
    # for: a roll above the charger's Leadership refuses the charge.
    dice = StrictDice([{"key": "round.0.first.fear.charge.0", "value": 6},
                       {"key": "round.0.first.fear.charge.1", "value": 6}])
    state = initialize_duel(attacker, fearer, FixedDice(), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(attacker, fearer, state, dice, StrictDecisions([]))
    dice.finish()
    assert not result.engaged
    assert result.failed_charges == frozenset({"first"})


@pytest.mark.phase3_rules
def test_the_fear_causer_refuses_the_charge_through_the_round_pipeline():
    """One representative full-round case through initialize_duel → resolve_round.

    The other Fear tests stay focused on `resolve_fear` itself; this one proves
    the same consequence the round consumer produces when the canonical carrier
    reaches the real phase pipeline — the charge never stands.
    """
    fearer = compile_hireling("hireling.hired-sword.ogre-bodyguard",
                              main_weapon_id="weapon.double-handed-weapon")
    attacker = plain_fighter()
    state = initialize_duel(attacker, fearer, FixedDice(), context=DuelContext(
        charging=("first",), active_participant="first"))
    dice = StrictDice([{"key": "round.0.first.fear.charge.0", "value": 6},
                       {"key": "round.0.first.fear.charge.1", "value": 6}])
    result = resolve_round(attacker, fearer, state, dice, StrictDecisions([]))
    dice.finish()
    assert not result.state.engaged
    assert result.state.failed_charges == frozenset({"first"})


@pytest.mark.phase2_construction
def test_trait_carriers_that_stay_out_are_refused_for_a_named_reason():
    """The carriers that remain out name their own blocker, not a trait fact."""
    for carrier in ("hireling.hired-sword.witch", "hireling.hired-sword.swordsmith"):
        with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
            compile_hireling(carrier)
    with pytest.raises(ValueError, match="hireling unique equipment needs a canonical combat mapping"):
        compile_hireling("hireling.hired-sword.halfling-knight")


# --- the supplied profile input a printed rule demands ------------------------

@pytest.mark.phase2_construction
def test_a_hireling_with_a_supplied_configuration_compiles():
    """Snorri and the hired are admitted once their printed input is supplied."""
    snorri = compile_hireling("hireling.dramatis.snorri-nosebiter",
                              owned_item_ids=("dwarf_axe", "hammer"),
                              main_weapon_id="weapon.mace",
                              trait_overrides={"snorri_drunk_result": 5})
    # Fortified with liquor: the printed +1 Strength over his printed 4.
    assert snorri.characteristics.strength == 5
    sister = compile_hireling("hireling.hired-sword.sister-of-sigmar",
                              owned_item_ids=("sigmarite_hammer", "light_armour",
                                              "blessed_water", "arcane_candelabrum"),
                              main_weapon_id="weapon.sigmarite-hammer",
                              special_rule_ids=("band--special-skills-sign-of-sigmar",
                                                "band--special-skills-absolute-faith"))
    assert "mechanic.fear-reroll" in sister.global_effects.tags
    assert "weapon.sigmarite-hammer" in sister.main_weapon.tags


@pytest.mark.phase2_construction
def test_a_blocked_equivalence_names_its_own_blocker():
    """A printed equivalence with no admitted bearer is recorded, not accepted."""
    # Drenok's printed rules are implemented: the unique Axe of Icefang is the
    # double-handed weapon its line names, so his canonical kit admits him and
    # no artificial pending-clause refusal remains.
    drenok = compile_hireling("hireling.dramatis.drenok-johansen-wielder-of-the-great-axe",
                              main_weapon_id="weapon.icefang-axe",
                              defence_ids=("defence.sabertooth-hide",))
    assert "weapon.icefang-axe" in drenok.main_weapon.tags
    assert "weapon.double-handed-weapon" in drenok.main_weapon.tags
    # The Halfling Knight's printed Cavalry Spear still has no canonical combat
    # mapping, so the incomplete equivalence names its own blocker.
    with pytest.raises(ValueError, match="hireling unique equipment needs a canonical combat mapping"):
        compile_hireling("hireling.hired-sword.halfling-knight", main_weapon_id="weapon.lance")


@pytest.mark.phase2_construction
def test_a_printed_drinking_result_outside_the_table_is_refused():
    """Result 1 removes Snorri from the battle, so no participant compiles."""
    with pytest.raises(ValueError, match="drinking result 2-6"):
        compile_hireling("hireling.dramatis.snorri-nosebiter",
                         owned_item_ids=("dwarf_axe", "hammer"),
                         main_weapon_id="weapon.mace",
                         trait_overrides={"snorri_drunk_result": 1})
    # Row 6 grants Frenzy as the table's express Slayer exception.
    snorri = compile_hireling("hireling.dramatis.snorri-nosebiter",
                              owned_item_ids=("dwarf_axe", "hammer"),
                              main_weapon_id="weapon.mace",
                              trait_overrides={"snorri_drunk_result": 6})
    assert "condition.snorri-frenzy" in snorri.global_effects.tags


@pytest.mark.phase2_construction
def test_an_inequivalent_unique_weapon_triggers_a_named_blocker():
    """Refused-without-invention: each blocker names the exact missing input."""
    # The wheelbarrow is a real out-of-duel tool whose own record the module
    # reports as an unknown mechanic id, and the axe the shovel counts as is not a
    # permission the offered kit list carries, so no supplied kit matches.
    with pytest.raises(ValueError, match="complete legal printed kit"):
        compile_hireling("hireling.hired-sword.grave-warden",
                         owned_item_ids=("shovel", "toughened_leathers", "wheelbarrow"),
                         main_weapon_id="weapon.axe")
    # The member unique equipment of the Dark Emissary (staff, spiral) declares no
    # combat equivalence, so the kit itself is the named blocker.
    with pytest.raises(ValueError, match="canonical combat mapping"):
        compile_hireling("hireling.dramatis.dark-emissary",
                         owned_item_ids=("hireling.dramatis.dark-emissary.item.staff-of-darkness",
                                         "hireling.dramatis.dark-emissary.item.spiral"),
                         main_weapon_id="weapon.axe")


@pytest.mark.parametrize("profile_id", [
    "hireling.hired-sword.chaos-fury",
    "hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne",
])
@pytest.mark.phase2_construction
def test_daemonic_flesh_is_armour_and_innate_attacks_are_not_owned_weapons(profile_id):
    daemon = compile_hireling(profile_id)
    assert daemon.natural_armour_save == 5
    assert daemon.natural_armour_unmodified
    assert daemon.global_effects.natural_armour_negated_by_magic
    assert "attack.magical" in daemon.global_effects.tags
    assert daemon.global_effects.ward_save == 7
    assert "weapon.natural-attacks" in daemon.main_weapon.tags
    assert daemon.mutation_equipment == ()
    if "aksho" in profile_id:
        assert "mechanic.craven" in daemon.global_effects.tags
        assert "mechanic.psychology-immunity" not in daemon.global_effects.tags


@pytest.mark.phase2_construction
def test_solkan_marks_are_chosen_only_for_the_printed_variant():
    options = dict(main_weapon_id="weapon.dagger", variant_ids=("deity.solkan",),
                   special_rule_ids=("hireling.hired-sword.priest-of-verena.skill.inquisitor",))
    priest = compile_hireling("hireling.hired-sword.priest-of-verena", **options)
    assert "mechanic.solkan-inquisitor" in priest.global_effects.tags
    assert len(priest.mutation_options) == 36
    assert {option.roll for option in priest.mutation_options} == {
        tens * 10 + units for tens in range(1, 7) for units in range(1, 7)}
    with pytest.raises(ValueError, match="Solkan variant"):
        compile_hireling("hireling.hired-sword.priest-of-verena", **{
            **options, "variant_ids": (), "main_weapon_id": "weapon.sword"})


@pytest.mark.parametrize("profile_id,printed_weapon", [
    ("hireling.hired-sword.arabian-merchant", "weapon.sword"),
    ("hireling.hired-sword.beast-hunter", "weapon.axe"),
    ("hireling.hired-sword.ninja-gnoblar", "weapon.bo"),
    ("hireling.dramatis.crow-master-the", "weapon.quarter-staff"),
])
@pytest.mark.phase2_construction
def test_printed_kit_default_distinguishes_omitted_from_explicit_dagger(profile_id, printed_weapon):
    # The printed kit, not alphabetic sorting or the model's old dagger default,
    # supplies an omitted choice. None is the public representation of omission.
    omitted = compile_hireling(profile_id)
    explicit_none = compile_hireling(profile_id, main_weapon_id=None)
    explicit_legal = compile_hireling(profile_id, main_weapon_id=printed_weapon)
    for fighter in (omitted, explicit_none, explicit_legal):
        assert printed_weapon in fighter.main_weapon.tags
    for illegal in ("weapon.dagger", "weapon.mace"):
        with pytest.raises(ValueError, match="complete legal printed kit|equipment is not available"):
            compile_hireling(profile_id, main_weapon_id=illegal)


@pytest.mark.phase2_construction
def test_omitted_weapon_keeps_the_plain_fighter_dagger_default():
    from mordheim_core.models import Characteristics
    fighter = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)))
    assert "weapon.dagger" in fighter.main_weapon.tags


# --- the individual participant of a composite entry --------------------------

MARQUAND = "hireling.dramatis.marquand"
PAIR = "hireling.dramatis.ulli-and-marquand"


def marquand(**options):
    """The canonical route: the offered package, profile and printed kit."""
    kit = {"main_weapon_id": "weapon.sword", "armour_id": "armour.light-armour"}
    return compile_hireling(MARQUAND, **{**kit, **options})


def printed_characteristics():
    return Characteristics(5, 3, 3, 2, 5, 2, movement=4, leadership=8)


def slower_charger():
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))


def printed_profile_without_the_skills():
    """Control: the same printed characteristics and kit, with no printed skill."""
    return compile_fighter(FighterBuild(
        "mordheim", printed_characteristics(),
        main_weapon_id="weapon.sword", armour_id="armour.light-armour"))


def roll(key, value):
    return {"key": key, "value": value}


def defended_round(defender, rolls):
    """One round in which the second fighter charges the defender."""
    charger = slower_charger()
    dice = StrictDice(rolls)
    state = initialize_duel(defender, charger, dice, context=DuelContext(
        charging=("second",), active_participant="second"))
    result = resolve_round(defender, charger, state, dice, StrictDecisions([]))
    dice.finish()
    return result.state


# The two printed attacks of the defender that miss, and the charger's one
# attack that wounds through the printed Light Armour on a failed 6+.
def defender_misses():
    return [roll("round.0.first.attack.0.hit", 1), roll("round.0.first.attack.1.hit", 1)]


CHARGER_WOUNDS = [roll("round.0.second.attack.0.hit", 6),
                  roll("round.0.second.attack.0.wound", 5),
                  roll("round.0.second.attack.0.armour", 1)]


@pytest.mark.phase1_kb_contracts
def test_the_pair_keeps_its_joint_identity_and_marquand_gains_no_campaign_hire():
    """The composite entry stays as published and no individual hiring opens.

    Ulli & Marquand is one printed entry carrying two warrior profiles, which
    the catalogue cannot model as a single profile: it keeps its
    ``out_of_scope`` adjudication and its joint identity, while the printed
    Marquand line is published as the canonical profile of its own participant.
    Neither the pair nor the participant gains a campaign hiring entry, so joint
    hiring is neither replaced nor split.
    """
    catalogue = load_hirelings("mordheim")
    pair = next(row for row in catalogue.profiles if row["id"] == PAIR)
    assert pair["normalization_status"] == "out_of_scope"
    assert pair.get("out_of_scope_reason")
    assert "characteristics" not in pair
    profile = next(row for row in catalogue.profiles if row["id"] == MARQUAND)
    assert profile["normalization_status"] == "normalized"
    assert profile["characteristics"] == {
        "M": 4, "WS": 5, "BS": 4, "S": 3, "T": 3, "W": 2, "I": 5, "A": 2, "Ld": 8}
    assert profile["starting_skill_ids"] == [
        "skill.step-aside", "skill.lightning-reflexes", "skill.knife-fighter"]
    assert {entry["item_id"] for entry in profile["equipment"]["fixed_items"]} == {
        "sword", "light_armour", "throwing_knives"}
    document = load_campaign_catalog("mordheim").catalogue("hired-swords-and-dramatis")
    offered = {str(row["profile_id"]) for row in document["dramatis_personae"]}
    assert PAIR not in offered and MARQUAND not in offered


@pytest.mark.phase2_construction
def test_marquand_compiles_with_his_printed_kit_and_only_his_admitted_skills():
    """Selection and compilation of the individual participant."""
    fighter = marquand()
    assert fighter.characteristics == printed_characteristics()
    assert fighter.main_weapon.parry                       # the printed Sword
    assert fighter.armour_save == 6                        # the printed Light Armour
    assert fighter.global_effects.step_aside
    assert {"skill.step-aside", "skill.lightning-reflexes"} <= set(fighter.global_effects.tags)
    # Knife-Fighter's whole content is the Shooting-phase throwing attack, so the
    # skill is carried as printed and contributes nothing to the resolved duel.
    assert "skill.knife-fighter" not in fighter.global_effects.tags
    with pytest.raises(ValueError, match="complete legal printed kit|equipment is not available"):
        marquand(main_weapon_id="weapon.mace")


@pytest.mark.phase3_rules
def test_lightning_reflexes_strikes_first_against_the_charge_that_hits_him():
    """The same Initiative decides it: only the printed skill changes the tier."""
    fighter, charger = marquand(), slower_charger()
    control = printed_profile_without_the_skills()

    def charged(unit):
        return phases.resolve_priority(phases.PriorityContext(
            fighter=unit, opponent=charger, charged=True, first_round=True))

    def charging(unit):
        return phases.resolve_priority(phases.PriorityContext(
            fighter=charger, opponent=unit, charging=True, first_round=True))

    assert charged(fighter).priority == charging(fighter).priority == 1
    assert phases.first_acts_before(charged(fighter), charging(fighter), StrictDice([]))
    assert charged(control).priority == 0 and charging(control).priority == 1
    assert not phases.first_acts_before(charged(control), charging(control), StrictDice([]))


@pytest.mark.phase3_rules
def test_step_aside_saves_the_close_combat_wound_only_on_the_printed_five():
    """The ward is his own printed save, with the control asked for no die."""
    saved = defended_round(marquand(), defender_misses() + CHARGER_WOUNDS + [
        roll("round.0.second.attack.0.special.ward", 5)])
    assert (saved.first.wounds, saved.second.wounds) == (2, 2)
    lost = defended_round(marquand(), defender_misses() + CHARGER_WOUNDS + [
        roll("round.0.second.attack.0.special.ward", 4)])
    assert (lost.first.wounds, lost.second.wounds) == (1, 2)
    # The same printed profile without Step Aside never reaches a ward die: its
    # tape runs from the charger's attack to its own two misses, so the absence
    # of the save is proved by the consumed tape itself.
    control = defended_round(printed_profile_without_the_skills(),
                             CHARGER_WOUNDS + defender_misses())
    assert (control.first.wounds, control.second.wounds) == (1, 2)
# --- the second individual participant of the composite entry ----------------

ULLI = "hireling.dramatis.ulli"


def ulli(**options):
    """The canonical route: the offered package, profile and printed kit."""
    kit = {"main_weapon_id": "weapon.double-handed-weapon", "armour_id": "armour.light-armour"}
    return compile_hireling(ULLI, **{**kit, **options})


@pytest.mark.phase1_kb_contracts
def test_the_pair_keeps_its_joint_identity_and_ulli_gains_no_campaign_hire():
    """The composite entry stays as published and no individual hiring opens.

    The same printed entry carries two warrior profiles; the second printed
    line is published as the canonical profile of its own participant, while
    the pair keeps its ``out_of_scope`` adjudication and joint identity.
    """
    catalogue = load_hirelings("mordheim")
    pair = next(row for row in catalogue.profiles if row["id"] == PAIR)
    assert pair["normalization_status"] == "out_of_scope"
    assert pair.get("out_of_scope_reason")
    assert "characteristics" not in pair
    profile = next(row for row in catalogue.profiles if row["id"] == ULLI)
    assert profile["normalization_status"] == "normalized"
    assert profile["characteristics"] == {
        "M": 4, "WS": 4, "BS": 4, "S": 4, "T": 3, "W": 2, "I": 4, "A": 2, "Ld": 7}
    assert profile["starting_skill_ids"] == [
        "skill.strongman", "skill.unstoppable-charge", "skill.combat-master"]
    assert {entry["item_id"] for entry in profile["equipment"]["fixed_items"]} == {
        "two_handed_weapon", "light_armour"}
    document = load_campaign_catalog("mordheim").catalogue("hired-swords-and-dramatis")
    offered = {str(row["profile_id"]) for row in document["dramatis_personae"]}
    assert ULLI not in offered


@pytest.mark.phase2_construction
def test_ulli_compiles_with_his_printed_kit_and_only_his_admitted_skills():
    """Selection and compilation of the second individual participant."""
    fighter = ulli()
    assert fighter.characteristics == Characteristics(
        4, 4, 3, 2, 4, 2, movement=4, leadership=7)
    assert fighter.main_weapon.two_handed
    assert fighter.main_weapon.strength_bonus == 2       # the printed double-handed weapon
    assert fighter.armour_save == 6                      # the printed Light Armour
    assert {"skill.strongman", "skill.unstoppable-charge"} <= set(fighter.global_effects.tags)
    assert fighter.global_effects.strongman
    # Combat Master's whole content is the two-or-more-enemies Attack and the
    # All Alone tests, outside the resolved 1v1 duel, so it contributes nothing.
    assert "skill.combat-master" not in fighter.global_effects.tags
    with pytest.raises(ValueError, match="complete legal printed kit|equipment is not available"):
        ulli(main_weapon_id="weapon.sword")


@pytest.mark.phase3_rules
def test_strongman_removes_the_double_handed_strike_last_penalty_for_ulli():
    """The printed Strongman raises the printed double-handed weapon's tier.

    A charging double-handed weapon that strikes last keeps its penalty tier;
    the same charge with the printed Strongman reaches the ordinary charging
    floor instead.
    """
    fighter = ulli()
    plain = compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 4, 3, 2, 4, 2, movement=4, leadership=7),
        main_weapon_id="weapon.double-handed-weapon", armour_id="armour.light-armour"))

    def charged(unit):
        return phases.PriorityContext(
            fighter=unit, opponent=plain_fighter(), charging=True, first_round=True)

    assert phases.resolve_priority(charged(fighter)).priority == 1
    assert phases.resolve_priority(charged(plain)).priority == -1
