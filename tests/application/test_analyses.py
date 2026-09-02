from threading import Event
import pytest

from mordheim_combat_lab.application.analyses import ComparisonCandidate, compare_builds
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
