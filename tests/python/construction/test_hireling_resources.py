"""H03b: hireling resources and variants reach their printed duel operators.

Five families, each with one selected discriminator:

* Marks of Myrmidia's Oracle reroll (a personal once-per-battle die, never a
  second copy for another roll);
* Snorri's pre-battle drinking table (results 2, 3 and 4 here; 5, 6 and the
  refusal of result 1 are already pinned by the admission suite);
* Belandysh's dice profile (rolled when a value is needed, once per turn);
* Innominatus' printed skills (Grizzled Veteran, Death without a face) on his
  own profile, together with the canonical mapping of his Dark Elf Blade;
* the Emissary of Chaos patron branch (exactly one exclusive patron; Khorne's
  frenzy and extra Attack; Nurgle's poison and Fear as separate consequences).
"""
from __future__ import annotations

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import prepare_hit_context
from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear
from mordheim_combat.modular.state import initialize_duel, initialize_fighter, require_characteristics
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

PRIESTESS = "hireling.hired-sword.war-priestess-of-myrmidia"
ORACLE = PRIESTESS + ".rule.marks-of-myrmidia"
EMISSARY = "hireling.hired-sword.emissary-of-chaos"
INNOMINATUS = "hireling.dramatis.innominatus-the-tilean-gladiator"
BELANDYSH = "hireling.dramatis.belandysh-condemned-champion-of-chen"


def priestess(select=True):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.hired-sword.2b", profile_id=PRIESTESS,
        special_rule_ids=(ORACLE,) if select else ()))


def foe():
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.sword"))


def snorri(result):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.dramatis-personae.2b",
        profile_id="hireling.dramatis.snorri-nosebiter",
        trait_overrides={"snorri_drunk_result": result}))


def emissary(patrons):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.hired-sword.2a", profile_id=EMISSARY,
        special_rule_ids=tuple(EMISSARY + f".patron.{patron}" for patron in patrons)))


# --- Marks of Myrmidia: the Oracle reroll -------------------------------

@pytest.mark.rule_behavior
def test_the_oracle_reroll_is_one_personal_die_for_the_whole_battle():
    selected, unselected = priestess(), priestess(select=False)
    assert "mechanic.oracle" in selected.global_effects.tags
    assert "mechanic.oracle" not in unselected.global_effects.tags
    foe_fighter = foe()
    dice = StrictDice([])
    first, second = initialize_fighter(selected, dice, "a"), initialize_fighter(foe_fighter, dice, "d")
    dice.finish()
    # A failed to-hit die is re-rolled by choice; the second result stands.
    dice = StrictDice([{"key": "x.hit", "value": 1}, {"key": "x.hit.reroll", "value": 5}])
    decisions = StrictDecisions([{"key": "x.hit.one-roll-reroll", "value": True}])
    outcome = resolve_reference_attack(selected, foe_fighter, first, second, selected.main_weapon,
                                       dice, key="x", decisions=decisions, hit_only=True)
    dice.finish(); decisions.finish()
    assert outcome.hit and "one-roll-reroll" in outcome.attacker.resources_spent
    # The battle's single reroll is spent: the next roll is never offered one.
    dice = StrictDice([{"key": "y.hit", "value": 6}])
    decisions = StrictDecisions([])
    outcome = resolve_reference_attack(selected, foe_fighter, outcome.attacker, outcome.defender,
                                       selected.main_weapon, dice, key="y",
                                       decisions=decisions, hit_only=True)
    dice.finish(); decisions.finish()
    assert outcome.hit and outcome.attacker.resources_spent == first.resources_spent | {"one-roll-reroll"}


# --- Snorri: the drinking table -----------------------------------------

@pytest.mark.compilation
def test_snorri_results_two_to_four_are_their_own_states():
    # Results 5 (+1 Strength), 6 (Frenzy) and the refusal of result 1 are
    # already pinned by test_hireling_admission; these are the rest.
    base = snorri(3)
    # Result 3 is explicitly "no effect": the printed profile is untouched.
    assert (base.characteristics.weapon_skill, base.characteristics.strength) == (5, 4)
    delicate = snorri(2)
    assert (delicate.characteristics.weapon_skill, delicate.characteristics.strength) == (4, 3)
    # Result 4 is the digestion stench: every model in the melee is at -1 to hit.
    stench, each = snorri(4), foe()
    init = StrictDice([])
    attacking = prepare_hit_context(each, stench, initialize_fighter(each, init, "a"),
                                    initialize_fighter(stench, init, "b"), each.main_weapon,
                                    each.main_weapon, key="probe")
    plain = prepare_hit_context(each, base, initialize_fighter(each, init, "a"),
                                initialize_fighter(base, init, "b"), each.main_weapon,
                                each.main_weapon, key="probe")
    init.finish()
    assert attacking.modifier - plain.modifier == -1


# --- Belandysh: the dice profile ----------------------------------------

@pytest.mark.rule_behavior
def test_belandysh_rolls_his_profile_once_per_turn_when_a_value_is_needed():
    fighter = compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.dramatis-personae.1c", profile_id=BELANDYSH))
    dice = StrictDice([])
    state = initialize_fighter(fighter, dice, "b")
    dice.finish()
    # Inconsistency means "determined whenever needed", not a duel-start roll.
    assert (state.weapon_skill, state.strength, state.attacks) == (1, 1, 1)
    assert not state.random_rolled
    dice = StrictDice([{"key": "b.characteristic.WS.0", "value": 6},
                       {"key": "b.characteristic.S.0", "value": 5},
                       {"key": "b.characteristic.A.0", "value": 2, "sides": 3}])
    state = require_characteristics(fighter, state, dice, "b", {"WS", "S", "A"})
    dice.finish()
    assert (state.weapon_skill, state.strength, state.attacks) == (6, 5, 2)
    # A second requirement in the same turn re-uses the values; no die is asked.
    again = require_characteristics(fighter, state, StrictDice([]), "b", {"WS", "S", "A"})
    assert (again.weapon_skill, again.strength, again.attacks) == (6, 5, 2)


# --- Innominatus: printed skills and the Dark Elf Blade -----------------

@pytest.mark.rule_behavior
def test_innominatus_has_grizzled_veteran_and_death_without_a_face():
    fighter = compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.dramatis-personae.1c", profile_id=INNOMINATUS))
    assert "mechanic.psychology-immunity" in fighter.global_effects.tags
    assert "mechanic.causes-fear" in fighter.global_effects.tags
    opponent = foe()
    assert causes_fear(fighter, opponent)
    assert not causes_fear(opponent, fighter)
    # The Dark Elf Blade keeps the underlying weapon and adds its printed
    # critical/injury property instead of replacing the axe.
    assert {"weapon.dwarf-axe", "material.dark-elf-blade"} <= set(fighter.main_weapon.tags)
    assert fighter.main_weapon.critical_injury_bonus == 1
    # Grizzled Veteran is the psychology immunity: the test is passed without a die.
    dice = StrictDice([])
    duel = initialize_duel(fighter, opponent, dice, context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(fighter, duel, dice, StrictDecisions([]), "probe",
                                      first=True, psychology=True)
    dice.finish()
    assert passed
    # A sibling hireling of the same grade does not inherit his Fear clause
    # (the Grand Master's own printed rule does grant him psychology immunity,
    # so only the Fear tag discriminates the two profiles).
    other = compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.dramatis-personae.1c",
        profile_id="hireling.dramatis.grand-master-ippan-shu"))
    assert "mechanic.causes-fear" not in other.global_effects.tags


# --- Emissary of Chaos: the patron branch -------------------------------

@pytest.mark.eligibility
def test_the_emissary_needs_exactly_one_patron():
    with pytest.raises(ValueError, match="exactly one printed patron"):
        emissary(())
    with pytest.raises(ValueError, match="exactly one printed patron"):
        emissary(("khorne", "nurgle"))


@pytest.mark.eligibility
def test_the_tzeentch_patron_keeps_its_own_academic_skill_access():
    from mordheim_construction.combat_packages import combat_packages
    from mordheim_construction.eligibility import desktop_call

    package = next(pack for pack in combat_packages("mordheim")
                   if str(pack.band["id"]) == "hirelings.hired-sword.2a")
    row = next(profile for profile in package.profiles if profile["id"] == EMISSARY)

    def choices(patron):
        return desktop_call("skillChoices", FighterBuild(
            "mordheim", collection="mordheim", band_id="hirelings.hired-sword.2a",
            profile_id=EMISSARY, special_rule_ids=(EMISSARY + f".patron.{patron}",)),
            package=package, profile=row)

    # Both patrons keep the printed combat/strength access; only Tzeentch opens
    # the academic list, which is the branch's own construction clause.
    khorne, tzeentch = choices("khorne"), choices("tzeentch")
    assert khorne["skill.fearsome"] and not khorne["skill.arcane-lore"]
    assert tzeentch["skill.fearsome"] and tzeentch["skill.arcane-lore"]


@pytest.mark.rule_behavior
def test_khorne_adds_frenzy_and_one_attack_without_duplication():
    khorne, nurgle = emissary(("khorne",)), emissary(("nurgle",))
    assert khorne.global_effects.frenzy and not nurgle.global_effects.frenzy
    # A1 + the printed +1 Attack, then Frenzy's doubling: four, once.
    assert phases.build_attacks(phases.AttackPoolContext(fighter=khorne)).attacks == 4
    assert phases.build_attacks(phases.AttackPoolContext(fighter=nurgle)).attacks == 1


@pytest.mark.rule_behavior
def test_nurgle_poison_reaches_the_attacks_that_carry_it():
    # The Fear half of the Nurgle branch is H03a's discriminator; this case
    # proves only that the printed poison is applied by the attack operator.
    khorne, nurgle = emissary(("khorne",)), emissary(("nurgle",))
    # Black Lotus: the natural six to hit wounds although the wound die would
    # fail, and the attack still allows its armour save.
    them = foe()
    dice = StrictDice([{"key": "n.hit", "value": 6}])
    decisions = StrictDecisions([{"key": "n.lotus-critical", "value": False}])
    outcome = resolve_reference_attack(
        nurgle, them, initialize_fighter(nurgle, StrictDice([]), "n"),
        initialize_fighter(them, StrictDice([]), "d"), nurgle.main_weapon, dice,
        key="n", decisions=decisions)
    dice.finish(); decisions.finish()
    assert outcome.wounded and outcome.damage == 1
    # Khorne's attacks are not poisoned: the same natural six still rolls its
    # wound die, and a failing die leaves no wound.
    dice = StrictDice([{"key": "k.hit", "value": 6}, {"key": "k.wound", "value": 1}])
    decisions = StrictDecisions([])
    outcome = resolve_reference_attack(
        khorne, them, initialize_fighter(khorne, StrictDice([]), "k"),
        initialize_fighter(them, StrictDice([]), "d"), khorne.main_weapon, dice,
        key="k", decisions=decisions)
    dice.finish(); decisions.finish()
    assert not outcome.wounded
