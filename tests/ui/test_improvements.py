"""external.test_improvements: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_core.models import FighterBuild
from mordheim_combat_lab.application.analyses import add_improvement, improvement_choices


def test_improvement_choices_exclude_out_of_scope_and_already_selected_skills():
    catalogue = CombatCatalogue()
    choice = next(
        profile for profile in catalogue.profiles("mordheim", "kislevites")
        if profile.profile_id == "druzhina-captain"
    )
    candidate = FighterBuild(
        "mordheim",
        collection=choice.collection,
        band_id=choice.band_id,
        profile_id=choice.profile_id,
        skill_ids=("skill.mighty-blow",),
    )

    choices = improvement_choices(catalogue, choice, candidate)
    choice_ids = {skill.id for skill in choices}

    assert "skill.acrobat" not in choice_ids
    assert "skill.mighty-blow" not in choice_ids
    assert choice_ids
    assert all(skill.runtime_available for skill in choices)


def test_add_improvement_maps_warband_skills_to_special_rule_ids():
    catalogue = CombatCatalogue()
    choice = next(
        profile for profile in catalogue.profiles("mordheim", "pit-fighters")
        if profile.profile_id == "pit-king"
    )
    candidate = FighterBuild(
        "mordheim",
        collection=choice.collection,
        band_id=choice.band_id,
        profile_id=choice.profile_id,
    )
    skill = next(
        skill for skill in improvement_choices(catalogue, choice, candidate)
        if skill.rule_id == "band--pit-fighter-skill-body-slam"
    )

    improved = add_improvement(catalogue, candidate, skill)

    assert improved.skill_ids == ()
    assert improved.special_rule_ids == ("band--pit-fighter-skill-body-slam",)


def test_improvement_choices_exclude_compound_renowned_virtue():
    catalogue = CombatCatalogue()
    choice = next(
        profile for profile in catalogue.profiles("mordheim", "bretonnian-chapel-guard")
        if profile.profile_id == "questing-knight"
    )
    candidate = FighterBuild(
        "mordheim",
        collection=choice.collection,
        band_id=choice.band_id,
        profile_id=choice.profile_id,
    )

    choices = improvement_choices(catalogue, choice, candidate)

    assert "band--renowned-virtue" not in {skill.rule_id for skill in choices}
