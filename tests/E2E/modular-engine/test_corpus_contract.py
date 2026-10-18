"""Engine-free contract tests for the declarative corpus.

Every assertion here exercises ``corpus.py`` only — the loader and its pure
static contract plus the pure dotted-path assertion the runner delegates to —
so no combat-package module is imported (guarded by
``test_corpus_is_importable_without_combat`` running earlier in an isolated
interpreter).  Synthetic valid and invalid documents demonstrate each contract
failure; no existing case file is imported or patched.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

from mordheim_modular_e2e.corpus import (
    CASES_DIRECTORY,
    CorpusError,
    Scenario,
    assert_observations,
    load_corpus,
    lookup_observation,
    scenario_contract_errors,
    validate_scenario,
)

HERE = Path(__file__).resolve().parent


def contract(raw, source: str = "synthetic.yaml", index: int = 0) -> Scenario:
    """The loader's own path: reusing ``validate_scenario`` keeps one truth."""
    return validate_scenario(raw, source, index)


def write(tmp_path: Path, documents, name: str = "synthetic.yaml") -> Path:
    path = tmp_path / name
    path.write_text(yaml.safe_dump(documents), encoding="utf-8")
    return path


#: A minimal legitimate scenario: the metadata, one build and one observation.
VALID = {
    "id": "the-grant-is-declared-on-the-compiled-bearer",
    "audit_id": "core/synthetic-rule",
    "covers": ["whole"],
    "fighters": {"first": {"collection": "mordheim", "band_id": "synthetic-band",
                           "profile_id": "synthetic-profile"},
                 "second": {}},
    "expect_final": {"state.second.wounds": 1},
}


def test_a_minimal_legitimate_scenario_loads():
    scenario = contract(VALID)
    assert scenario.test_id == "core/synthetic-rule::the-grant-is-declared-on-the-compiled-bearer"
    assert scenario.covers == ("whole",)


def test_a_scenario_with_only_expect_fighters_is_a_legal_observation():
    expected = dict(VALID)
    del expected["expect_final"]
    expected["expect_fighters"] = {"first.tags.syn-tag": True}
    scenario = contract(expected)
    assert scenario.case["expect_fighters"] == {"first.tags.syn-tag": True}


def test_normal_scenarios_without_expect_fighters_keep_loading(tmp_path):
    legacy = {
        "id": "ordinary-observation",
        "audit_id": "core/synthetic-rule",
        "covers": ["whole"],
        "fighters": {"first": {}, "second": {}},
        "rolls": [{"key": "round.0.first.attack.0.hit", "value": 4}],
        "expect_final": {"state.second.wounds": 0},
    }
    directory = tmp_path / "cases"
    directory.mkdir()
    (directory / "synthetic.yaml").write_text(
        yaml.safe_dump([VALID, legacy]), encoding="utf-8")
    scenarios = load_corpus(directory)
    assert [item.scenario_id for item in scenarios] == (
        ["the-grant-is-declared-on-the-compiled-bearer", "ordinary-observation"])


def test_unknown_scenario_fields_fail():
    dirty = {**VALID, "expect_weapon_skill": 3}
    with pytest.raises(CorpusError, match="unknown scenario fields"):
        contract(dirty)


def test_identity_contracts_fail():
    for dirty, message in (
            ({**VALID, "id": "  "}, "id must be a nonempty string"),
            ({**VALID, "audit_id": ""}, "audit_id must be a nonempty string"),
            ({**VALID, "covers": []}, "covers must be a nonempty list of clause ids"),
            ({**VALID, "covers": "whole"}, "covers must be a nonempty list of clause ids"),
            ({**VALID, "covers": ["whole", 12]}, "covers entry must be a nonempty string"),
    ):
        with pytest.raises(CorpusError, match=message):
            contract(dirty)


def test_the_refusal_channel_is_exclusive_and_named():
    with pytest.raises(CorpusError, match="expect_error must be a nonempty string"):
        contract({**VALID, "expect_final": {"state.first.wounds": 3}, "expect_error": "  "})
    if True:
        dirty = {**VALID, "expect_final": {"state.first.wounds": 3},
                 "expect_error": "reason"}
        del dirty["expect_final"]
        dirty["expect_final"] = {"state.first.wounds": 3}
        with pytest.raises(CorpusError, match="expect_error cannot be combined"):
            contract(dirty)
    with pytest.raises(CorpusError, match="expect_error cannot be combined"):
        contract({**VALID, "expect_final": {"state.first.wounds": 3},
                  "expect_error": "reason"})
    dirty = dict(VALID)
    del dirty["expect_final"]
    dirty["expect_error"] = "refusal reason"
    assert contract(dirty)  # a refusal alone is a legal scenario


def test_a_case_without_any_observation_fails():
    dirty = dict(VALID)
    del dirty["expect_final"]
    with pytest.raises(CorpusError, match="a scenario must assert an observation"):
        contract(dirty)


def test_an_empty_events_list_is_a_legal_absence_assertion():
    dirty = dict(VALID)
    del dirty["expect_final"]
    dirty["expect_events"] = []
    assert contract(dirty).case["expect_events"] == []


def test_maximum_rounds_must_be_a_positive_integer_without_bools():
    for bad in (0, -1, True, 1.5, "3", None):
        with pytest.raises(CorpusError, match="maximum_rounds must be a positive integer"):
            contract({**VALID, "maximum_rounds": bad})
    assert contract({**VALID, "maximum_rounds": 4})


def test_fighters_are_limited_to_first_and_second():
    for dirty in ({**VALID, "fighters": {"first": {}, "third": {}}},
                  {**VALID, "initial_state": {"first": {}, "second": {}, "third": {}}},
                  {**VALID, "fighters": None}):
        with pytest.raises(CorpusError, match="participants|must be a mapping"):
            contract(dirty)
    assert contract({**VALID, "initial_state": {"first": {}}})


def test_roll_entries_match_the_strict_dice_contract():
    for message, entry in (
            ("must declare a nonempty string key", {"value": 3}),
            ("must declare a nonempty string key", {"key": "  ", "value": 3}),
            ("integer die value", {"key": "k"}),
            ("booleans are not dice values", {"key": "k", "value": True}),
            ("outside the faces", {"key": "k", "value": 0}),
            ("outside the faces", {"key": "k", "value": 7}),
            ("outside the faces", {"key": "k", "value": 3, "sides": 2}),
            ("positive integer side count", {"key": "k", "value": 3, "sides": 0}),
            ("positive integer side count", {"key": "k", "value": 3, "sides": True}),
            ("outside the faces", {"key": "k", "value": 11, "sides": 10}),
            ("unknown fields", {"key": "k", "value": 3, "die": 6}),
    ):
        with pytest.raises(CorpusError, match=message):
            contract({**VALID, "rolls": [entry]})
    assert contract({**VALID, "rolls": [{"key": "k", "value": 3}, {"key": "k2", "value": 6, "sides": 6}]})


def test_roll_entries_must_be_a_list_of_mappings():
    with pytest.raises(CorpusError, match="rolls must be a list"):
        contract({**VALID, "rolls": {"key": 3}})
    with pytest.raises(CorpusError, match="must be a mapping"):
        contract({**VALID, "rolls": ["round.0"]})


def test_decision_entries_require_a_key_and_a_boolean():
    for message, entry in (
            ("nonempty string key", {"value": True}),
            ("nonempty string key", {"key": " ", "value": True}),
            ("values must be booleans", {"key": "k", "value": 1}),
            ("values must be booleans", {"key": "k"}),
    ):
        with pytest.raises(CorpusError, match=message):
            contract({**VALID, "decisions": [entry]})
    assert contract({**VALID, "decisions": [{"key": "k", "value": False}]})


def test_observations_must_be_nonempty_mappings_of_nonempty_paths():
    for dirty, message in (
            ({**VALID, "expect_events": "nothing"}, "expect_events must be an ordered list"),
            ({**VALID, "expect_rounds": {}}, "expect_rounds must be a nonempty mapping"),
            ({**VALID, "expect_rounds": True}, "expect_rounds must be a nonempty mapping"),
            ({**VALID, "expect_fighters": {}},
             "expect_fighters must be a nonempty mapping of nonempty dotted paths"),
            ({**VALID, "expect_fighters": {"": True}},
             "expect_fighters must be a nonempty mapping of nonempty dotted paths"),
    ):
        with pytest.raises(CorpusError, match=message):
            contract(dirty)


def test_round_checkpoints_must_be_non_negative_integer_indices():
    with pytest.raises(CorpusError, match="non-negative integer indices"):
        contract({**VALID, "expect_rounds": {True: {"state.first.wounds": 1}}})
    with pytest.raises(CorpusError, match="non-negative integer indices"):
        contract({**VALID, "expect_rounds": {-1: {"state.first.wounds": 1}}})
    with pytest.raises(CorpusError, match="non-negative integer indices"):
        contract({**VALID, "expect_rounds": {"x": {"state.first.wounds": 1}}})
    checkpoint = {**VALID, "expect_rounds": {"0": {"state.first.wounds": 1}, 1: None}}
    with pytest.raises(CorpusError, match="checkpoint 1 must be a nonempty mapping"):
        contract(checkpoint)
    assert contract({**VALID, "expect_rounds": {"0": {"state.first.wounds": 1}}})


def test_the_pure_lookup_rejects_unknown_paths():
    with pytest.raises(CorpusError, match="observation does not exist"):
        lookup_observation({"a": {"b": 1}}, "a.missing")
    with pytest.raises(CorpusError, match="observation does not exist"):
        lookup_observation({"attacks": [{}, {}]}, "attacks.2.hit")
    assert lookup_observation({"a": {"b": [7, 8]}}, "a.b.1") == 8


def test_the_pure_assertion_separates_bools_from_ints_and_prefixes_the_label():
    observed = {"state": {"first": {"wounds": 1}, "pinned": 1}}
    with pytest.raises(CorpusError, match=r"final\.state\.pinned: got 1, expected True"):
        assert_observations(observed, {"state.pinned": True}, "final")
    with pytest.raises(CorpusError, match=r"final\.state\.pinned: got True, expected 1"):
        assert_observations({"state": {"pinned": True}},
                           {"state.pinned": 1}, "final")


def test_the_pure_assertion_requires_a_nonempty_mapping_of_nonempty_paths():
    for expected in ({}, "not-a-mapping", {"": 1}):
        with pytest.raises(CorpusError, match="expectations must be a nonempty mapping"
                                               "|observation paths must be nonempty strings"):
            assert_observations({"a": 1}, expected, "final")
    assert_observations({"a": 1}, {"a": 1}, "final")  # the happy path holds


def test_the_pure_assertion_labels_missing_paths_with_the_channel():
    with pytest.raises(CorpusError, match=r"^fighters\.first\.tags: observation does not exist$"):
        assert_observations({"first": {}}, {"first.tags": True}, "fighters")


def test_loading_rejects_a_duplicate_scenario_identity(tmp_path):
    same = {**VALID, "expect_final": {"state.second.wounds": 2}}
    directory = tmp_path / "cases"
    directory.mkdir()
    (directory / "synthetic.yaml").write_text(
        yaml.safe_dump([VALID, same]), encoding="utf-8")
    with pytest.raises(CorpusError, match="duplicate scenario 'core/synthetic-rule::the-grant-is-declared-on-the-compiled-bearer'"):
        load_corpus(directory)


def test_a_non_list_document_fails_at_load(tmp_path):
    directory = tmp_path / "cases"
    directory.mkdir()
    (directory / "not-a-list.yaml").write_text("id: not-a-list\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="must be a list of scenarios"):
        load_corpus(directory)


def test_the_real_corpus_directory_constant_points_at_the_cases_tree():
    assert CASES_DIRECTORY.name == "cases"
    assert (CASES_DIRECTORY / "core").is_dir()


# Delegating the pure assertion must keep the loader meaning stable even when
# some other test sped the loader up ahead of this file:
def test_errors_are_value_errors_so_callers_kept_their_except_shape():
    with pytest.raises(ValueError):
        contract({**VALID, "id": "  "})


def test_corpus_is_importable_without_combat():
    """The loader and its contract import no combat package anywhere."""
    code = textwrap.dedent("""
        import sys
        import corpus
        scenario = corpus.validate_scenario(
            {"id": "s", "audit_id": "core/synthetic-rule", "covers": ["whole"],
             "expect_final": {"state.first.wounds": 1}},
            "isolated.yaml", 0)
        assert scenario.test_id == "core/synthetic-rule::s"
        combat = [name for name in sys.modules
                  if name.startswith(("mordheim_combat", "mordheim_construction",
                                      "mordheim_core", "mordheim_knowledge"))]
        assert not combat, combat
    """)
    result = subprocess.run(
        [sys.executable, "-c", code], cwd=str(HERE), capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


# --- Structural validator (validate_corpus.py) contract --------------
# The validator is engine-free too: its unit tests below import it through the
# same package and feed it small synthetic corpora; nothing inside ``cases``
# is read or mutated by them.  It must reuse the loader above - never a second
# parser - and must report authoring-metadata conflicts without turning
# coverage gaps into scenario failures (exit codes 0 / 1 / 2 only).
import contextlib
import importlib
import io

import yaml as yaml_for_validator


@pytest.fixture(scope="module")
def validator():
    return importlib.import_module("mordheim_modular_e2e.validate_corpus")


def _corpus_file(directory: Path, name: str, header: str, *documents) -> None:
    """A synthetic corpus file: one YAML document, a list of scenarios."""
    directory.mkdir(parents=True, exist_ok=True)
    body = yaml_for_validator.safe_dump(list(documents))
    (directory / name).write_text(header + body, encoding="utf-8")


TODO_HEADER = "# authoring_status: TODO\n# execution_status: UNEXECUTED\n\n"


class _SyntheticInventory:
    """The register, synthetic: same structure and coverage math, no CSV read.

    ``test_inventory.Coverage`` itself is reused, so the acceptance/exit codes
    the validator produces are computed by the real coverage logic; only the
    register contents are synthetic and stable across corpus edits.
    """

    declared = {"core/synthetic-rule": {"whole", "minimal"}}
    admitted = {"core/synthetic-rule": {"whole"}}
    admitted_ids = {"core/synthetic-rule"}

    def read_register(self):
        return self.declared, self.admitted, set(self.admitted_ids)

    def coverage(self, scenarios):
        from mordheim_modular_e2e.corpus import group_by_audit
        from mordheim_modular_e2e.test_inventory import Coverage
        grouped = group_by_audit(scenarios)
        covered = {current: {clause for scenario in group for clause in scenario.covers}
                   for current, group in grouped.items()}
        return Coverage(len(scenarios), covered, self.admitted,
                         self.admitted_ids)


def _run(validator, directory, *, real=False, require_complete=False):
    corpus, inventory = validator._import_support()
    if not real:
        inventory = _SyntheticInventory()
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = validator.report(corpus, inventory, directory, require_complete)
    return code, buffer.getvalue()


def test_the_real_corpus_reports_clean_integrity_but_declared_gaps(validator):
    """Sorted whole-tree run: nothing malformed, coverage gaps stay report-only."""
    code, text = _run(validator, CASES_DIRECTORY, real=True)
    assert code == 0
    assert "unknown clause references: 0" in text
    assert "--require-complete" in text or "reported gaps are information" in text


def test_a_minimal_synthetic_corpus_is_accepted(validator, tmp_path):
    directory = tmp_path / "cases"
    _corpus_file(directory, "ok.yaml", TODO_HEADER,
                 {"id": "s", "audit_id": "core/synthetic-rule", "covers": ["whole"],
                  "expect_final": {"state.first.wounds": 1}})
    code, text = _run(validator, directory)
    assert code == 0
    assert "scenarios declared: 1" in text


def test_unknown_and_duplicate_identity_and_unknown_clause_fail(validator, tmp_path):
    directory = tmp_path / "cases"
    _corpus_file(directory, "ok.yaml", TODO_HEADER,
                 {"id": "s", "audit_id": "core/synthetic-rule", "covers": ["whole"],
                  "expect_final": {"state.first.wounds": 1}})
    _corpus_file(directory, "unknown.yaml", TODO_HEADER,
                 {"id": "other", "audit_id": "core/other", "covers": ["whole"],
                  "expect_final": {"state.first.wounds": 1}})
    _corpus_file(directory, "wrongclause.yaml", TODO_HEADER,
                 {"id": "third", "audit_id": "core/synthetic-rule",
                  "covers": ["missing-clause"],
                  "expect_final": {"state.first.wounds": 1}})
    _corpus_file(directory, "duplicate.yaml", TODO_HEADER,
                 {"id": "s", "audit_id": "core/synthetic-rule", "covers": ["whole"],
                  "expect_final": {"state.second.wounds": 2}})
    code, text = _run(validator, directory)
    assert code == 1
    assert "unknown audit_id declarations" in text
    assert "unknown clause references: 1" in text
    assert "duplicate scenario" in text


def test_a_malformed_file_fails_integrity_but_the_rest_loads(validator, tmp_path):
    directory = tmp_path / "cases"
    _corpus_file(directory, "ok.yaml", TODO_HEADER,
                 {"id": "s", "audit_id": "core/synthetic-rule", "covers": ["whole"],
                  "expect_final": {"state.first.wounds": 1}})
    (directory / "broken.yaml").write_text("id: [unclosed\n", encoding="utf-8")
    code, text = _run(validator, directory)
    assert code == 1
    assert "invalid YAML" in text
    assert "scenarios declared: 1" in text


def test_retired_identities_are_reported_outside_the_pending_work(validator, tmp_path):
    directory = tmp_path / "cases"
    _corpus_file(directory, "retired.yaml", TODO_HEADER,
                 {"id": "s", "audit_id": "retired/some-old-identity",
                  "covers": ["whole"],
                  "expect_final": {"state.first.wounds": 1}})
    code, text = _run(validator, directory, require_complete=True)
    assert code == 2
    assert "Retired" in text and "retired/some-old-identity" in text


def test_authoring_marker_state_conflicts_are_reported_per_file(validator, tmp_path):
    directory = tmp_path / "cases"
    def scenario(name):
        return {"id": name, "audit_id": "core/synthetic-rule", "covers": ["whole"],
                "expect_final": {"state.first.wounds": 1}}
    _corpus_file(directory,
                 "marker-unknown-clause.yaml",
                 "# authoring_status: AUTHORED\n# execution_status: UNEXECUTED\n"
                 "# Clause: whole (scope: YES)\n# AUTHORED[not-declared]: text\n",
                 scenario("marker-unknown-clause"))
    _corpus_file(directory,
                 "status-without-marker.yaml",
                 "# authoring_status: AUTHORED\n# execution_status: UNEXECUTED\n"
                 "# Clause: whole (scope: YES)\n",
                 scenario("status-without-marker"))
    _corpus_file(directory,
                 "double-marker.yaml",
                 "# authoring_status: PARTIAL\n# execution_status: UNEXECUTED\n"
                 "# Clause: whole (scope: YES)\n# PARTIAL[whole]: text\n"
                 "# AUTHORED[whole]: text\n",
                 scenario("double-marker"))
    _corpus_file(directory,
                 "reviewed-with-held.yaml",
                 "# authoring_status: REVIEWED\n# execution_status: UNEXECUTED\n"
                 "# Clause: whole (scope: YES)\n# PARTIAL[whole]: text\n",
                 scenario("reviewed-with-held"))
    _corpus_file(directory,
                 "authored-not-covering.yaml",
                 "# authoring_status: AUTHORED\n# execution_status: UNEXECUTED\n"
                 "# Clause: whole (scope: YES)\n# AUTHORED[whole]: text\n"
                 "# Clause: minimal (scope: YES)\n",
                 scenario("authored-not-covering"))
    code, text = _run(validator, directory)
    assert code == 0  # metadata conflicts are reported, integrity is clean
    assert "AUTHORED[not-declared] does not name a declared clause" in text
    assert "authoring_status AUTHORED without any AUTHORED[...] marker" in text
    assert "carries both PARTIAL and AUTHORED markers" in text
    assert "REVIEWED with PARTIAL (held-clause) markers" in text
    assert "AUTHORED with in-scope clauses not covered here" in text
    assert "authoring metadata conflicts: 5 findings" in text


def test_require_complete_fails_when_a_declared_clause_is_uncovered(validator, tmp_path):
    directory = tmp_path / "cases"
    _corpus_file(directory, "partial.yaml", TODO_HEADER,
                 {"id": "s", "audit_id": "core/synthetic-rule", "covers": [],
                  "expect_final": {"state.first.wounds": 1}})
    code, _ = _run(validator, directory, require_complete=True)
    assert code == 2


# --- JSON handoff not needed; the ledger keeps the whole contract ---------
