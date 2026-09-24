from pathlib import Path
import re

from mordheim_combat_lab.report_naming import timestamped_report_path


def test_timestamped_report_path_contains_execution_timestamp_and_preserves_extension():
    path = timestamped_report_path(Path("outputs"), "rules-audit", ".csv")
    assert re.fullmatch(r"rules-audit-\d{8}-\d{6}\.csv", path.name)
