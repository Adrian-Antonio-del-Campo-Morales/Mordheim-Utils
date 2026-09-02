"""external.test_workbooks: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelResult
from mordheim_core.models import FighterBuild
from mordheim_combat_lab.persistence.workbooks import CombatLabWorkbookError
from mordheim_combat_lab.persistence.workbooks import load_ui_workbook
from mordheim_combat_lab.persistence.workbooks import save_workbook
import pytest as pytest


def test_workbook_round_trip_preserves_stable_build_ids_and_result(tmp_path):
    candidate = FighterBuild(
        "mordheim", collection="mordheim", band_id="mercenaries", profile_id="mercenary-captain",
        main_weapon_id="weapon.sword", off_hand_id="defence.shield", defence_ids=("defence.helmet",),
        skill_ids=("skill.mighty-blow",),
    )
    enemy = FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1), main_weapon_id="weapon.mace")
    settings = DuelExecutionSettings(5_000, 123, 500, 30)
    result = DuelResult(2_500, 2_400, 100, 5_000)
    path = tmp_path / "duel.xlsx"

    save_workbook(path, candidate, enemy, settings, result)
    restored_candidate, restored_enemy, restored_settings, restored_result = load_ui_workbook(path)

    assert restored_candidate == candidate
    assert restored_enemy == enemy
    assert restored_settings == settings
    assert restored_result == result


def test_workbook_rejects_unknown_or_corrupt_files(tmp_path):
    path = tmp_path / "not-a-workbook.xlsx"
    path.write_text("not an Excel file", encoding="utf-8")

    with pytest.raises(CombatLabWorkbookError):
        load_ui_workbook(path)
