"""T13 hireling admission: the duel participant route, not a synthetic fixture.

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

from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

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


def test_a_core_grade_profile_compiles_and_fights():
    """The core kit is a printed "choose two weapons" group, not a crash."""
    bodyguard = compile_hireling("hireling.hired-sword.ogre-bodyguard",
                                 main_weapon_id="weapon.double-handed-weapon")
    assert bodyguard.global_effects is not None
    state = initialize_duel(bodyguard, plain_fighter(), FixedDice())
    assert state is not None


def test_a_profile_with_pending_intrinsic_clauses_is_refused_by_name():
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.bone-goliath")
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.dramatis.grand-master-ippan-shu")


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

def test_the_declared_equivalence_reaches_the_duel():
    """The Holy Man's staff counts as a double-handed weapon, so it fights as one."""
    holy_man = compile_hireling("hireling.hired-sword.holy-man",
                               main_weapon_id="weapon.double-handed-weapon")
    assert "weapon.double-handed-weapon" in holy_man.main_weapon.tags
    # The Grave Robber's and Gravesman's equivalences have no admitted bearer to
    # exercise them: both profiles still refuse by name for their pending clause
    # (register rows C06-hatred and the unmapped unique object).
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.grave-robber", main_weapon_id="weapon.axe")
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.gravesman", main_weapon_id="weapon.halberd")


def test_an_item_whose_own_rules_are_excluded_cannot_be_a_weapon():
    """A garment declared out of the duel is not a weapon in an active slot."""
    with pytest.raises(ValueError, match="non-duel unique equipment cannot occupy an active combat position"):
        compile_hireling(
            "hireling.dramatis.snerik-night-goblin-scout",
            main_weapon_id="hireling.dramatis.snerik-night-goblin-scout.item.camouflage-cloak")


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
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.ninja-gnoblar", main_weapon_id="weapon.double-handed-weapon")


def test_the_printed_shovel_equivalence_is_blocked_by_the_pending_clause():
    """The Gravesman's shovel counts as a halberd, but the profile is pending."""
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.gravesman",
                         owned_item_ids=("hireling.hired-sword.gravesman.item.shovel",
                                         "hireling.hired-sword.gravesman.item.pry-bar",
                                         "dagger"),
                         main_weapon_id="weapon.halberd")
    # The same equivalence route on an admitted bearer: the printed equivalence
    # selects the canonical mechanic instead of the object's own bare id.
    holy_man = compile_hireling("hireling.hired-sword.holy-man",
                               owned_item_ids=("staff", "hammer"),
                               main_weapon_id="weapon.double-handed-weapon")
    assert "weapon.double-handed-weapon" in holy_man.main_weapon.tags


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


def test_aenur_unique_weapon_strength_is_not_granted_twice_by_its_intrinsic_rules():
    fighter = compile_hireling("hireling.dramatis.aenur", main_weapon_id="weapon.ienh-khain")
    assert fighter.main_weapon.strength_bonus == 1
    assert fighter.global_effects.strength_bonus == 1  # printed starting Mighty Blow
    assert fighter.main_weapon.critical_threshold == 5


# --- the prepared trait facts, with a live consequence ------------------------

def test_the_prepared_trait_facts_reach_admitted_hirelings():
    bodyguard = compile_hireling("hireling.hired-sword.ogre-bodyguard",
                                 main_weapon_id="weapon.double-handed-weapon")
    assert "mechanic.causes-fear" in bodyguard.global_effects.tags
    assert "species.ogre" in bodyguard.global_effects.tags
    fury = compile_hireling("hireling.hired-sword.chaos-fury")
    assert "mechanic.causes-fear" in fury.global_effects.tags
    assert "nature.daemon" in fury.global_effects.tags
    # Grave Robber still has an unresolved intrinsic rule of its own.
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.grave-robber")


@pytest.mark.parametrize("carrier", TRAIT_CARRIERS)
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


def test_trait_carriers_that_stay_out_are_refused_for_a_named_reason():
    """The carriers that remain out name their own blocker, not a trait fact."""
    for carrier in ("hireling.hired-sword.dark-mage", "hireling.hired-sword.ninja-gnoblar",
                    "hireling.dramatis.innominatus-the-tilean-gladiator"):
        with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
            compile_hireling(carrier)
    with pytest.raises(ValueError, match="hireling unique equipment needs a canonical combat mapping"):
        compile_hireling("hireling.hired-sword.halfling-knight")


# --- the supplied profile input a printed rule demands ------------------------

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


def test_a_blocked_equivalence_names_its_own_blocker():
    """A printed equivalence with no admitted bearer is recorded, not accepted."""
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.hired-sword.old-prospector",
                         owned_item_ids=("blunderbuss",
                                         "hireling.hired-sword.old-prospector.item.pick"),
                         main_weapon_id="weapon.double-handed-weapon")
    with pytest.raises(ValueError, match="hireling unique equipment needs a canonical combat mapping"):
        compile_hireling("hireling.hired-sword.halfling-knight", main_weapon_id="weapon.lance")


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
    # combat equivalence, and the profile's own intrinsic clauses are pending.
    with pytest.raises(ValueError, match="intrinsic duel clauses are pending"):
        compile_hireling("hireling.dramatis.dark-emissary",
                         owned_item_ids=("hireling.dramatis.dark-emissary.item.staff-of-darkness",
                                         "hireling.dramatis.dark-emissary.item.spiral"),
                         main_weapon_id="weapon.axe")


@pytest.mark.parametrize("profile_id", [
    "hireling.hired-sword.chaos-fury",
    "hireling.dramatis.aksho-akhash-the-vile-dreadwing-lord-of-the-carrion-throne",
])
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
