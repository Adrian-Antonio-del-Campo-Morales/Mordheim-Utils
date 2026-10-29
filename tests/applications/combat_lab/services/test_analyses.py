from threading import Event
import pytest

from mordheim_combat_lab.application.catalogue import CombatCatalogue, ProfileChoice
from mordheim_combat_lab.application.analyses import (
    AttributeChoice,
    ComparisonCandidate,
    add_improvement_items,
    add_improvements,
    attribute_choices,
    compare_builds,
    improve_attributes,
    improvement_combinations,
)
from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_core.models import Characteristics, FighterBuild, SimulationCancelled


def build(weapon="weapon.dagger"):
    return FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1), main_weapon_id=weapon)


def test_comparison_service_reports_results_and_illegal_variants():
    batch = compare_builds(build(), build(), (
        ComparisonCandidate("mace", "Mace", build("weapon.mace")),
        ComparisonCandidate("unknown", "Unknown", build("weapon.missing")),
    ), DuelExecutionSettings(5, 4, 5, 2), Event())
    assert [row.candidate.id for row in batch.results] == ["mace"]
    assert [candidate.id for candidate, _reason in batch.rejected] == ["unknown"]


def test_comparison_service_honours_cancellation():
    cancelled = Event(); cancelled.set()
    with pytest.raises(SimulationCancelled):
        compare_builds(build(), build(), (), DuelExecutionSettings(1, 0, 1, 1), cancelled)


def skill(index: int):
    from types import SimpleNamespace
    return SimpleNamespace(id=f"skill.{index}", name=f"Skill {index}")


def test_improvement_combinations_covers_single_and_pair_sizes():
    pool = tuple(skill(index) for index in range(4))

    singles = improvement_combinations(pool, 1)
    pairs = improvement_combinations(pool, 2)

    assert tuple(item.skills[0].id for item in singles) == tuple(f"skill.{index}" for index in range(4))
    assert len(pairs) == 6
    assert pairs[0].label == "Skill 0 + Skill 1"
    assert tuple(item.skills[1].id for item in pairs) == (
        "skill.1", "skill.2", "skill.3", "skill.2", "skill.3", "skill.3",
    )


def test_improvement_combinations_rejects_invalid_sizes_and_large_pools():
    pool = tuple(skill(index) for index in range(4))

    assert improvement_combinations(pool, 5) == ()
    with pytest.raises(ValueError, match="between 1 and 5"):
        improvement_combinations(pool, 6)
    # There is deliberately no row cap: large selections simply produce many
    # combinations for the caller to simulate (progress + cancel still apply).
    assert len(improvement_combinations(tuple(skill(index) for index in range(30)), 4)) == 27405


def test_attribute_choices_stop_at_the_racial_maximum():
    catalogue = CombatCatalogue()
    choice = ProfileChoice("mordheim", "sisters-of-sigmar", "sister-superior", "Sister Superior")
    at_maximum = FighterBuild(
        "mordheim", Characteristics(6, 4, 4, 3, 6, 4),
        collection="mordheim", band_id="sisters-of-sigmar", profile_id="sister-superior",
    )

    options = attribute_choices(catalogue, choice, at_maximum)

    assert options == ()  # every human maximum already reached
    # Each choice reports how many further points fit below the maximum.
    base = FighterBuild(
        "mordheim", Characteristics(3, 2, 4, 3, 3, 1),
        collection="mordheim", band_id="sisters-of-sigmar", profile_id="sister-superior",
    )
    steps = {item.id: item.steps for item in attribute_choices(catalogue, choice, base)}
    assert steps["WS"] == 3  # 3 of a human maximum 6
    assert steps["S"] == 2  # 2 of a human maximum 4
    assert "T" not in steps  # already at the toughness maximum

    # A fresh human candidate offers every duel characteristic increase.
    fresh = FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
        collection="mordheim", band_id="sisters-of-sigmar", profile_id="sister-superior",
    )
    assert {item.id for item in attribute_choices(catalogue, choice, fresh)} == {"WS", "S", "T", "W", "I", "A"}


def test_attribute_increases_repeat_until_the_racial_maximum():
    """Strength at 3 steps and size 3 yields exactly [S+1, S+1, S+1]."""
    strength = AttributeChoice("S", "Strength", steps=3)

    combinations = improvement_combinations((strength,), 3)

    assert len(combinations) == 1
    assert [item.id for item in combinations[0].skills] == ["S", "S", "S"]
    assert combinations[0].label == "Strength + Strength + Strength"


def test_repeating_attributes_are_bounded_by_their_remaining_steps():
    strength = AttributeChoice("S", "Strength", steps=2)
    single = skill(0)

    pairs = improvement_combinations((strength, single), 2)

    assert tuple(tuple(item.id for item in combo.skills) for combo in pairs) == (
        ("S", "S"), ("S", "skill.0"),
    )
    triples = improvement_combinations((strength, single), 3)
    assert tuple(tuple(item.id for item in combo.skills) for combo in triples) == (
        ("S", "S", "skill.0"),
    )
    # A skill never repeats inside one combination even when attributes do.
    two_skills = (skill(0), skill(1))
    assert all(
        tuple(item.id for item in combo.skills).count("skill.0") <= 1
        for combo in improvement_combinations(two_skills, 2)
    )
    # Size beyond the total remaining capacity yields nothing to run (the UI
    # pre-checks this and asks for a smaller size).
    assert improvement_combinations((AttributeChoice("S", "Strength", steps=1),), 3) == ()


def test_improve_attributes_stacks_repeated_increases():
    base = FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1))

    raised = improve_attributes(base, {"WS": 2, "S": 1})

    assert (raised.characteristics.weapon_skill, raised.characteristics.strength) == (5, 4)
    with pytest.raises(ValueError, match="unknown characteristic"):
        improve_attributes(base, {"BS": 1})


def test_add_improvement_items_mixes_skills_and_attributes():
    catalogue = CombatCatalogue()
    choice = ProfileChoice("mordheim", "sisters-of-sigmar", "sister-superior", "Sister Superior")
    base = FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
        collection="mordheim", band_id="sisters-of-sigmar", profile_id="sister-superior",
    )
    strength_skill = next(
        item for item in catalogue.skills(choice) if item.id == "skill.mighty-blow"
    )
    attack = next(
        item for item in attribute_choices(catalogue, choice, base) if item.id == "A"
    )

    mixed = add_improvement_items(catalogue, base, (strength_skill, attack, attack))

    assert "skill.mighty-blow" in mixed.skill_ids
    assert mixed.characteristics.attacks == base.characteristics.attacks + 2
