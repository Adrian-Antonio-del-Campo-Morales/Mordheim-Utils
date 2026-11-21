"""Focused checks for the parity deliveries and their catalogue connection.

These tests protect the connection's own contract: explicit selection, delivery
validation against the current conformance YAML, admission of ``translated`` deliveries
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

from tools.verification import parity_deliveries

CASES = {
    "simple": (
        "delivery/mechanic/defence.kite-shield/"
        "the-composed-floor-is-carried-as-the-compiled-armour-save"
    ),
    "blocked": (
        "delivery/core/combat-two-weapons/"
        "different-weapons-give-the-off-hand-one-attack"
    ),
    "not_applicable": (
        "delivery/mechanic/armour.cathayan-quilted-silk/"
        "quilted-silk-is-refused-as-a-body-armour"
    ),
    "initial_state": (
        "delivery/rule/mordheim/beastmen-raiders/centigors--drunken/"
        "mechanic.centigor-drunken/results-two-to-five-do-nothing"
    ),
}


def _delivery(case_key: str) -> Path:
    path = parity_deliveries.deliveries_directory() / parity_deliveries.case_filename(case_key)
    if not path.is_file():
        pytest.skip(f"delivery not present: {path.name}")
    return path


def test_selection_is_explicit_and_accepts_both_identifiers():
    index, _ = parity_deliveries.discover()
    delivery = parity_deliveries.resolve(index, CASES["simple"])
    assert delivery is not None
    validated = delivery.with_validation(parity_deliveries.validate(delivery))
    admission = parity_deliveries.admit(validated)
    assert admission.case.limits.maximum_rounds == 1
    campaign_case = parity_deliveries.build_parity_case(
        admission, simulations=2, seed=2026, magnitudes=("winner",),
    )
    assert campaign_case.maximum_rounds == 50
    assert admission.case.limits.maximum_rounds == 1
    assert parity_deliveries.resolve(index, "mechanic/defence.kite-shield::"
                                     "the-composed-floor-is-carried-as-the-compiled-armour-save")
    with pytest.raises(parity_deliveries.SelectionError):
        parity_deliveries.select(index, [])
    with pytest.raises(parity_deliveries.SelectionError):
        parity_deliveries.select(index, [CASES["simple"], "delivery/nope/nope/nope"])
    selected = parity_deliveries.select(index, [CASES["simple"], CASES["simple"]])
    assert [item.case_key for item in selected] == [CASES["simple"]]


def test_discovery_reports_malformed_and_duplicate_files(tmp_path):
    directory = tmp_path / "deliveries"
    directory.mkdir()
    good = json.loads(_delivery(CASES["simple"]).read_text(encoding="utf-8"))
    (directory / parity_deliveries.case_filename(good["case_key"])).write_text(
        json.dumps(good), encoding="utf-8",
    )
    (directory / "broken.json").write_text("{not json", encoding="utf-8")
    index, defects = parity_deliveries.discover(directory)
    assert list(index) == [good["case_key"]]
    assert len(defects) == 1 and defects[0].startswith("broken.json")


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

    assert main(["parity", "--scenarios", "delivery/nope/nope/nope", "--simulations", "2"]) == 2


def test_cli_lists_every_delivery_it_cannot_run(tmp_path, monkeypatch, capsys):
    from types import SimpleNamespace

    from mordheim_combat_lab.cli.commands import main
    from mordheim_combat_lab.verification import parity

    expected = []
    for number, status in enumerate(("translated", "blocked", "not-applicable")):
        key = f"delivery/a/case-{number}"
        expected.append(key)
        (tmp_path / f"{number}.json").write_text(json.dumps({
            "case_key": key, "source": {"test_id": f"a::case-{number}"},
            "status": status,
        }), encoding="utf-8")
    monkeypatch.setattr(parity_deliveries, "deliveries_directory", lambda root=None: tmp_path)
    sampled = []
    monkeypatch.setattr(parity, "run_parity", lambda cases, **kwargs: (
        sampled.extend(cases) or SimpleNamespace(rows=(), modular_duels=0)))
    # Nothing here can run (blocked, not applicable, an incomplete delivery):
    # every delivery is listed with its reason and the run fails.
    assert main(["parity", "--scenarios", "deliveries", "--backend", "modular",
                 "--simulations", "1", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert sampled == []
    assert [row["case"] for row in payload["results"]] == expected
    assert {row["status"] for row in payload["results"]} == {"INCOMPATIBLE"}
    assert all(row["detail"] for row in payload["results"])


# --- Run-level failures and provenance (engine execution is always stubbed) ---


def _copy_delivery(case_key: str, directory: Path) -> None:
    directory.mkdir(exist_ok=True)
    shutil.copy(_delivery(case_key), directory / parity_deliveries.case_filename(case_key))




def _admit(delivery):
    return parity_deliveries.admit(delivery.with_validation(parity_deliveries.validate(delivery)))


def test_a_stale_or_invalid_delivery_is_classified_not_measured(tmp_path):
    key = CASES["simple"]
    source = json.loads(_delivery(key).read_text(encoding="utf-8"))
    path = tmp_path / parity_deliveries.case_filename(key)

    path.write_text(json.dumps(
        dict(source, source=dict(source["source"], sha256="0" * 64))), encoding="utf-8")
    index, _ = parity_deliveries.discover(tmp_path)
    assert _admit(index[key]).state == "stale"

    invalid = dict(source)
    invalid.pop("schema")
    path.write_text(json.dumps(invalid), encoding="utf-8")
    index, _ = parity_deliveries.discover(tmp_path)
    assert _admit(index[key]).state == "invalid"


def test_declared_non_scenarios_and_inexpressible_inputs_keep_their_reason():
    index, _ = parity_deliveries.discover()
    for name, state in (("blocked", "blocked"), ("not_applicable", "not-applicable")):
        admission = _admit(index[CASES[name]])
        assert admission.state == state
        assert admission.case is None  # never sampled

    admission = _admit(index[CASES["initial_state"]])
    assert admission.state == "incompatible" and "initial_state" in admission.detail


def test_the_catalogue_reports_every_delivery_it_cannot_run():
    # The whole corpus resolves: admitted deliveries are runnable cases, and
    # every other one is listed with its reason instead of disappearing.
    from mordheim_combat_lab.cli.scenarios import load_checkout_module

    catalog = load_checkout_module("tools.verification.parity_catalog")
    runnable, rejected, entries = catalog.resolve(["deliveries"])
    assert len(runnable) + len(rejected) == len(entries)
    assert runnable and rejected
    assert all(reason.split(":")[0] in {"blocked", "not-applicable", "incompatible",
                                        "stale", "invalid", "policy-unverified"}
               for _key, reason in rejected)
    assert all(item.case.limits.maximum_rounds == parity_deliveries.CAMPAIGN_MAXIMUM_ROUNDS
               for item in runnable[:20])
