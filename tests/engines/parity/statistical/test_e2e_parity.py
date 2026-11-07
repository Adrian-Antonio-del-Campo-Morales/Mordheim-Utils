"""Focused checks for the consolidated E2E precompiled parity connection.

These tests protect the connection's own contract: explicit selection, delivery
validation against the current YAML, admission of ``translated`` deliveries
only, outcome separation, magnitude expansion and the CLI entry point.  They do
not certify parity and they do not run a campaign: execution tests sample eight
duels of one frozen case.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from tools.verification import e2e_parity

CASES = {
    "simple": (
        "e2e/mechanic/defence.kite-shield/"
        "the-composed-floor-is-carried-as-the-compiled-armour-save"
    ),
    "blocked": (
        "e2e/core/combat-two-weapons/"
        "different-weapons-give-the-off-hand-one-attack"
    ),
    "not_applicable": (
        "e2e/mechanic/armour.cathayan-quilted-silk/"
        "quilted-silk-is-refused-as-a-body-armour"
    ),
    "initial_state": (
        "e2e/rule/mordheim/beastmen-raiders/centigors--drunken/"
        "mechanic.centigor-drunken/results-two-to-five-do-nothing"
    ),
}


def _delivery(case_key: str) -> Path:
    path = e2e_parity.deliveries_directory() / e2e_parity.case_filename(case_key)
    if not path.is_file():
        pytest.skip(f"delivery not present: {path.name}")
    return path


def _result(payload: dict, case_key: str) -> dict:
    return next(item for item in payload["results"] if item["case_key"] == case_key)


def test_selection_is_explicit_and_accepts_both_identifiers():
    index, _ = e2e_parity.discover()
    delivery = e2e_parity.resolve(index, CASES["simple"])
    assert delivery is not None
    validated = delivery.with_validation(e2e_parity.validate(delivery))
    admission = e2e_parity.admit(validated)
    assert admission.case.limits.maximum_rounds == 1
    campaign_case = e2e_parity.build_parity_case(
        admission, simulations=2, seed=2026, magnitudes=("winner",),
    )
    assert campaign_case.maximum_rounds == 50
    assert admission.case.limits.maximum_rounds == 1
    assert e2e_parity.resolve(index, "mechanic/defence.kite-shield::"
                                     "the-composed-floor-is-carried-as-the-compiled-armour-save")
    with pytest.raises(e2e_parity.SelectionError):
        e2e_parity.select(index, [])
    with pytest.raises(e2e_parity.SelectionError):
        e2e_parity.select(index, [CASES["simple"], "e2e/nope/nope/nope"])
    selected = e2e_parity.select(index, [CASES["simple"], CASES["simple"]])
    assert [item.case_key for item in selected] == [CASES["simple"]]


def test_discovery_reports_malformed_and_duplicate_files(tmp_path):
    directory = tmp_path / "deliveries"
    directory.mkdir()
    good = json.loads(_delivery(CASES["simple"]).read_text(encoding="utf-8"))
    (directory / e2e_parity.case_filename(good["case_key"])).write_text(
        json.dumps(good), encoding="utf-8",
    )
    (directory / "broken.json").write_text("{not json", encoding="utf-8")
    index, defects = e2e_parity.discover(directory)
    assert list(index) == [good["case_key"]]
    assert len(defects) == 1 and defects[0].startswith("broken.json")


def test_stale_and_invalid_deliveries_are_classified_not_measured(tmp_path):
    key = CASES["simple"]
    source = json.loads(_delivery(key).read_text(encoding="utf-8"))

    stale = dict(source)
    stale["source"] = dict(source["source"], sha256="0" * 64)
    (tmp_path / e2e_parity.case_filename(key)).write_text(
        json.dumps(stale), encoding="utf-8",
    )
    payload, code = e2e_parity.execute([key], simulations=2, deliveries=tmp_path)
    result = _result(payload, key)
    assert result["outcome"] == "stale-delivery"
    assert result["engines"] == []
    assert code == 1 and payload["summary"]["stale_delivery"] == 1

    invalid = json.loads(_delivery(key).read_text(encoding="utf-8"))
    invalid.pop("schema")
    (tmp_path / e2e_parity.case_filename(key)).write_text(
        json.dumps(invalid), encoding="utf-8",
    )
    payload, code = e2e_parity.execute([key], simulations=2, deliveries=tmp_path)
    assert _result(payload, key)["outcome"] == "invalid-delivery"
    assert code == 1 and payload["summary"]["invalid_delivery"] == 1


def test_blocked_and_not_applicable_are_counted_without_sampling():
    payload, code = e2e_parity.execute(
        [CASES["blocked"], CASES["not_applicable"]], simulations=2,
    )
    blocked = _result(payload, CASES["blocked"])
    missing = _result(payload, CASES["not_applicable"])
    assert blocked["outcome"] == "blocked" and blocked["engines"] == []
    assert missing["outcome"] == "not-applicable" and missing["engines"] == []
    assert payload["summary"]["sampled"] == 0
    assert payload["summary"]["blocked"] == 1
    assert payload["summary"]["not_applicable"] == 1
    assert code == 0


def test_initial_state_is_reported_incompatible():
    payload, code = e2e_parity.execute([CASES["initial_state"]], simulations=2)
    result = _result(payload, CASES["initial_state"])
    assert result["outcome"] == "incompatible"
    assert "initial_state" in result["detail"]
    assert result["engines"] == []
    # Nothing was compared, so the honest incompatibility cannot pass the run.
    assert payload["summary"]["compared"] == 0
    assert any("no case was compared" in item
               for item in payload["checks"]["run_failures"])
    assert code == 1


def test_winner_comparison_ignores_terminal_wounds_and_conditions():
    from mordheim_combat_lab.verification.parity._runner import _compare_case
    from mordheim_core.models import ObservedDuelResult

    def sample(first_wounds, winner):
        return ObservedDuelResult(
            winner=np.full(40, winner, dtype=np.int8),
            resolution_rounds=np.ones(40, dtype=np.int8),
            first_wounds=np.asarray(first_wounds, dtype=np.int8),
            second_wounds=np.zeros(40, dtype=np.int8),
            first_condition=np.zeros(40, dtype=np.int8),
            second_condition=np.zeros(40, dtype=np.int8),
            simulations=40,
            maximum_rounds=1,
        )

    # Oracle 2 = unresolved; candidate 0 = unresolved in its own convention.
    comparisons, failure = _compare_case(
        ("winner",),
        sample([0] * 40, 2), sample([3] * 40, 0), 40,
    )
    assert [item.magnitude for item in comparisons] == ["winner"]
    assert comparisons[0].passed is True
    assert failure is None


def test_cli_refuses_an_unknown_identifier():
    from mordheim_combat_lab.cli.commands import main

    assert main(["parity", "--scenarios", "e2e/nope/nope/nope", "--simulations", "2"]) == 2


def test_outcomes_separate_causes_and_aggregate_conservatively():
    from types import SimpleNamespace

    def row(status, detail=""):
        return SimpleNamespace(status=status, detail=detail)

    assert e2e_parity.classify_row(row("PASS"))[0] == "approved"
    assert e2e_parity.classify_row(row("ERROR", "ERROR: oracle failed"))[0] == "reference-failure"
    assert e2e_parity.classify_row(
        row("DIVERGENCE", "DIVERGENCE:exception:ValueError: boom")
    )[0] == "candidate-failure"
    assert e2e_parity.classify_row(
        row("DIVERGENCE", "DIVERGENCE: winner[first]: modular=0.1")
    )[0] == "divergence"
    assert e2e_parity.classify_row(
        row("INCOMPATIBLE", "INCOMPATIBLE:admission: pending ports")
    )[0] == "incompatible"
    assert e2e_parity.classify_row(
        row("NOT_RUN", "NOT_RUN:outcome-codes: bad code")
    )[0] == "execution-failure"
    assert e2e_parity.classify_row(
        row("NOT_RUN", "NOT_RUN:native-plan: not eligible")
    )[0] == "incompatible"
    for message in e2e_parity.BACKEND_UNAVAILABLE_MESSAGES:
        assert e2e_parity.classify_row(
            row("NOT_RUN", f"NOT_RUN:native-plan: {message}")
        )[0] == "backend-unavailable"
        for prefix in ("native-unavailable", "native-stale"):
            assert e2e_parity.classify_row(
                row("NOT_RUN", f"NOT_RUN:{prefix}: {message}")
            )[0] == "backend-unavailable"
    for message in ("native plan rejected: bad context",
                    "native extension does not support this duel plan"):
        assert e2e_parity.classify_row(
            row("NOT_RUN", f"NOT_RUN:native-plan: {message}")
        )[0] == "incompatible"
    assert "backend-unavailable" in e2e_parity.FAILING_OUTCOMES
    assert e2e_parity.aggregate(
        ["approved", "backend-unavailable"]) == "backend-unavailable"
    assert e2e_parity.aggregate(["approved", "approved"]) == "approved"
    assert e2e_parity.aggregate(["approved", "incompatible"]) == "incompatible"
    assert e2e_parity.aggregate(["divergence", "candidate-failure"]) == "candidate-failure"


def test_removed_magnitudes_are_rejected_before_sampling():
    assert e2e_parity.parse_magnitudes(None) == ("winner",)
    assert e2e_parity.parse_magnitudes("winner,rounds") == ("winner", "rounds")
    for removed in ("wounds", "condition"):
        with pytest.raises(e2e_parity.MagnitudeError):
            e2e_parity.parse_magnitudes("winner," + removed)
        with pytest.raises(e2e_parity.MagnitudeError):
            e2e_parity.execute([], simulations=1, magnitudes=("winner", removed))


def test_cli_lists_every_e2e_delivery_it_cannot_run(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    from mordheim_combat_lab.cli.commands import main
    from mordheim_combat_lab.verification import parity

    expected = []
    for number, status in enumerate(("translated", "blocked", "not-applicable")):
        key = f"e2e/a/case-{number}"
        expected.append(key)
        (tmp_path / f"{number}.json").write_text(json.dumps({
            "case_key": key, "source": {"test_id": f"a::case-{number}"},
            "status": status,
        }), encoding="utf-8")
    monkeypatch.setattr(e2e_parity, "deliveries_directory", lambda root=None: tmp_path)
    sampled = []
    monkeypatch.setattr(parity, "run_parity", lambda cases, **kwargs: (
        sampled.extend(cases) or SimpleNamespace(rows=(), modular_duels=0)))
    # Nothing here can run (blocked, not applicable, an incomplete delivery):
    # every delivery is listed with its reason and the run fails.
    assert main(["parity", "--scenarios", "e2e", "--backend", "modular",
                 "--simulations", "1", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert sampled == []
    assert [row["case"] for row in payload["results"]] == expected
    assert {row["status"] for row in payload["results"]} == {"INCOMPATIBLE"}
    assert all(row["detail"] for row in payload["results"])


# --- Run-level failures and provenance (engine execution is always stubbed) ---

def _row(case, backend, status, detail="", compared=None):
    from types import SimpleNamespace

    compared = status in {"PASS", "DIVERGENCE"} if compared is None else compared
    return SimpleNamespace(
        case=case, backend=backend, status=status, detail=detail,
        executed=compared, compared=compared, approved=status == "PASS",
        comparisons=(), modular_seconds=0.5 if compared else 0.0,
        candidate_seconds=0.1 if compared else 0.0,
    )


@pytest.fixture
def stub_runner(monkeypatch):
    """Replace the shared runner; ``rows[backend]`` gives each backend's row."""
    from types import SimpleNamespace

    from mordheim_combat_lab.verification import parity

    rows: dict[str, tuple] = {}
    calls: list = []

    def fake_run_parity(cases, *, backends, **options):
        cases = list(cases)
        calls.append((cases, tuple(backends)))
        return SimpleNamespace(rows=tuple(
            _row(case.label, backend, *rows[backend])
            for case in cases for backend in backends
        ))

    monkeypatch.setattr(parity, "run_parity", fake_run_parity)
    return SimpleNamespace(rows=rows, calls=calls)


@pytest.fixture
def clean_provenance(monkeypatch):
    """A clean checkout whose packages are imported from it (no warnings)."""
    from mordheim_combat_lab import provenance

    monkeypatch.setattr(provenance, "source_revision", lambda root: {
        "commit": "c" * 40, "branch": "test", "dirty": False, "dirty_paths": [],
    })
    return provenance


def _copy_delivery(case_key: str, directory: Path) -> None:
    directory.mkdir(exist_ok=True)
    shutil.copy(_delivery(case_key), directory / e2e_parity.case_filename(case_key))


def test_missing_native_extension_fails_and_keeps_the_numpy_approval(
    stub_runner, clean_provenance,
):
    stub_runner.rows.update({
        "numpy": ("PASS",),
        "native": ("NOT_RUN", "NOT_RUN:native-unavailable: native extension is not installed"),
    })
    payload, code = e2e_parity.execute(
        [CASES["simple"]], simulations=2, backend="all",
    )
    result = _result(payload, CASES["simple"])
    assert result["outcome"] == "backend-unavailable"
    engines = {item["engine"]: item["outcome"] for item in result["engines"]}
    assert engines == {"numpy": "approved", "native": "backend-unavailable"}
    assert payload["summary"]["backend_unavailable"] == 1
    assert payload["summary"]["failed"] == 1
    assert code == 1


def test_native_plan_incapacity_stays_an_honest_incompatibility(
    stub_runner, clean_provenance,
):
    stub_runner.rows.update({
        "numpy": ("PASS",),
        "native": ("NOT_RUN", "NOT_RUN:native-plan: native extension does not "
                              "support this duel plan"),
    })
    payload, code = e2e_parity.execute(
        [CASES["simple"]], simulations=2, backend="all",
    )
    assert _result(payload, CASES["simple"])["outcome"] == "incompatible"
    assert payload["checks"]["run_failures"] == []
    assert code == 0  # numpy compared the case

    payload, code = e2e_parity.execute(
        [CASES["simple"]], simulations=2, backend="native",
    )
    assert payload["summary"]["compared"] == 0
    assert any("no case was compared" in item
               for item in payload["checks"]["run_failures"])
    assert code == 1


def test_failed_decision_policy_probe_fails_the_run(
    monkeypatch, stub_runner, clean_provenance, capsys,
):
    import mordheim_core.dice

    class Broken:
        def choose(self, key):
            raise RuntimeError("probe API drift")

    monkeypatch.setattr(mordheim_core.dice, "AlwaysAccept", Broken)
    policy = e2e_parity.decision_policy_evidence()
    assert policy["probe_failed"] is True and policy["corresponds"] is False

    payload, code = e2e_parity.execute([CASES["simple"]], simulations=2)
    result = _result(payload, CASES["simple"])
    assert result["outcome"] == "execution-failure"
    assert "probe failed" in result["detail"]
    assert stub_runner.calls == []
    assert any("decision-policy probe failed" in item and "probe API drift" in item
               for item in payload["checks"]["run_failures"])
    assert "E2E PARITY RUN FAILURE" in capsys.readouterr().err
    assert code == 1


def test_disagreeing_decision_policies_fail_the_run(
    monkeypatch, stub_runner, clean_provenance,
):
    monkeypatch.setattr(e2e_parity, "decision_policy_evidence", lambda: {
        "kind": "engine-default", "corresponds": False, "probe_failed": False,
        "detail": "default decision policies disagree; frozen scenarios cannot be compared",
    })
    payload, code = e2e_parity.execute([CASES["simple"]], simulations=2)
    assert _result(payload, CASES["simple"])["outcome"] == "incompatible"
    assert stub_runner.calls == []
    failures = payload["checks"]["run_failures"]
    assert any("disagree" in item for item in failures)
    assert not any("probe failed" in item for item in failures)
    assert code == 1


def test_discovery_defects_fail_the_run_and_reach_the_summary(
    tmp_path, stub_runner, clean_provenance,
):
    stub_runner.rows["numpy"] = ("PASS",)
    directory = tmp_path / "deliveries"
    _copy_delivery(CASES["simple"], directory)
    (directory / "broken.json").write_text("{not json", encoding="utf-8")
    payload, code = e2e_parity.execute(
        [CASES["simple"]], simulations=2, deliveries=directory,
    )
    assert _result(payload, CASES["simple"])["outcome"] == "approved"
    assert payload["summary"]["discovery_defects"] == 1
    assert payload["summary"]["run_failures"] == 1
    assert payload["checks"]["discovery_defects"][0].startswith("broken.json")
    text = e2e_parity.report_markdown(payload)
    assert "## discovery_defects" in text and "## run_failures" in text
    assert code == 1


def test_provenance_is_recorded_and_differences_only_warn(
    tmp_path, monkeypatch, stub_runner, capsys,
):
    from mordheim_combat_lab import provenance

    stub_runner.rows["numpy"] = ("PASS",)
    elsewhere = tmp_path / "other-checkout"
    monkeypatch.setattr(provenance, "source_revision", lambda root: {
        "commit": "d" * 40, "branch": "work", "dirty": True,
        "dirty_paths": ["packages/python/combat-engine/mordheim_combat/phases.py"],
    })
    monkeypatch.setattr(provenance, "imported_package_dirs", lambda: {
        "mordheim_combat": elsewhere / "mordheim_combat",
        "mordheim_core": elsewhere / "mordheim_core",
    })
    payload, code = e2e_parity.execute([CASES["simple"]], simulations=2)
    record = payload["provenance"]
    assert set(record["engine_digests"]) == {"modular", "numpy"}
    assert all(len(value) == 64 for value in record["engine_digests"].values())
    assert "native_build_sha256" in record
    assert record["revision"]["dirty"] is True
    assert payload["repository"]["revision"] == "d" * 40
    assert payload["repository"]["dirty"] is True
    # One warning per package imported from elsewhere, one for the dirty tree.
    assert len(record["warnings"]) == 3
    assert sum("outside" in item for item in record["warnings"]) == 2
    assert any("uncommitted" in item for item in record["warnings"])
    assert capsys.readouterr().err.count("PROVENANCE WARNING") == 3
    assert "## provenance_warnings" in e2e_parity.report_markdown(payload)
    assert payload["checks"]["run_failures"] == []
    assert code == 0


def test_clean_provenance_digests_the_imported_engines(stub_runner, clean_provenance):
    stub_runner.rows.update({"numpy": ("PASS",), "native": ("PASS",)})
    payload, code = e2e_parity.execute(
        [CASES["simple"]], simulations=2, backend="all",
    )
    record = payload["provenance"]
    assert record["warnings"] == []
    assert set(record["engine_digests"]) == {"modular", "numpy", "native"}
    assert len(set(record["engine_digests"].values())) == 3
    assert record["native_build_sha256"] == clean_provenance.native_build_sha256()
    assert record["imported_from"]["mordheim_combat"].startswith(
        e2e_parity.repository_root().as_posix())
    assert e2e_parity.head_revision() == clean_provenance.source_revision(None)["commit"]
    assert code == 0
