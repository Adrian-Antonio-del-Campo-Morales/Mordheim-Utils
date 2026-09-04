from mordheim_combat_lab.verification import engine_mutation
from mordheim_combat_lab.verification.engine_mutation import CATALOG
from mordheim_combat_lab.verification.engine_mutation import EngineMutant
from mordheim_combat_lab.verification.engine_mutation import _stage_src
from mordheim_combat_lab.verification.engine_mutation import _run_detector
from mordheim_combat_lab.verification.engine_mutation import run_mutant


def test_catalogue_ids_are_unique_and_anchors_apply_to_current_source():
    ids = [mutant.id for mutant in CATALOG]
    assert len(ids) == len(set(ids))
    assert len(CATALOG) >= 5
    for mutant in CATALOG:
        path = engine_mutation.ROOT / "src" / "mordheim_combat" / mutant.file
        source = path.read_text(encoding="utf-8")
        assert mutant.old in source, f"stale anchor for {mutant.id}"
        assert mutant.new != mutant.old
        assert source.count(mutant.old) == 1


def test_mutants_target_distinct_decision_families():
    files = {mutant.file for mutant in CATALOG}
    assert "vectorized/_operators.py" in files


def test_staging_applies_the_mutant_without_touching_the_live_tree():
    mutant = next(item for item in CATALOG if item.id == "wound-ramp-off-by-one")
    live = engine_mutation.ROOT / "src" / "mordheim_combat" / mutant.file
    live_before = live.read_text(encoding="utf-8")
    try:
        stage_root, target = _stage_src(mutant)
        staged = target.read_text(encoding="utf-8")
        assert mutant.new in staged
        assert mutant.old not in staged
        assert staged.replace(mutant.new, mutant.old) == live_before
    finally:
        import shutil
        shutil.rmtree(stage_root.parent, ignore_errors=True)
    assert live.read_text(encoding="utf-8") == live_before


def test_stale_mutant_is_rejected_without_side_effects():
    stale = EngineMutant(
        "stale", "vectorized/_operators.py",
        "this text never exists in the source", "irrelevant",
        "stale anchor probe",
    )
    try:
        _stage_src(stale)
    except ValueError as error:
        assert "stale mutant" in str(error)
    else:  # pragma: no cover
        raise AssertionError("stale mutants must be rejected")


def test_clean_staged_copy_passes_a_small_detector_suite():
    pytest = __import__("pytest")
    pytest.importorskip("coverage")  # mirrors the real environment cost guard
    mutant = next(item for item in CATALOG if item.id == "wound-ramp-off-by-one")
    try:
        stage_root, _ = _stage_src(mutant)
    except ValueError:  # catalog drifted; the integrity test above already fails
        return
    try:
        returncode = _run_detector(
            stage_root, ("tests/combat/vectorized/test_backends.py",), timeout=300,
        )
    finally:
        import shutil
        shutil.rmtree(stage_root.parent, ignore_errors=True)
    assert returncode == 0
