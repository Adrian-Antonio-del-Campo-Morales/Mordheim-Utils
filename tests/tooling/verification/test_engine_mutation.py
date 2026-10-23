import pytest

from mordheim_combat_lab.verification import engine_mutation
from mordheim_combat_lab.verification.engine_mutation import CATALOG


pytestmark = pytest.mark.phase0_preflight


def test_catalogue_ids_are_unique_and_anchors_apply_to_current_source():
    ids = [mutant.id for mutant in CATALOG]
    assert len(ids) == len(set(ids))
    assert len(CATALOG) >= 5
    for mutant in CATALOG:
        path = engine_mutation.ROOT / "packages/python/combat-engine/mordheim_combat" / mutant.file
        source = path.read_text(encoding="utf-8")
        assert mutant.old in source, f"stale anchor for {mutant.id}"
        assert mutant.new != mutant.old
        assert source.count(mutant.old) == 1


def test_mutants_target_distinct_decision_families():
    files = {mutant.file for mutant in CATALOG}
    assert "vectorized/_operators.py" in files
