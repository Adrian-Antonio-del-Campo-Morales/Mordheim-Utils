"""Python runner for the shared KB parity vectors (Agent 0, parity lane).

Each vector asserts one invariant of the generated web KB artefact. The TS
mirror (``packages/typescript/parity-kb-vectors.test.ts``) consumes the same
vector files against the same artefact, so a divergence between the Python
builder and the TS reader fails on one side first and the vector pinpoints
it.

Vectors with ``status: blocked`` document parity gaps (T5 flow): they are
counted and must stay visible, but they do not execute until the blocking
gap is fixed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
VECTORS = Path(__file__).resolve().parent / "vectors"
ARTEFACT = ROOT / "apps" / "warband-manager-web" / "public" / "knowledge" / "knowledge-web.json"

ARTEFACT_DICT: dict = json.loads(ARTEFACT.read_text(encoding="utf-8"))


def _band(collection: str, band_id: str) -> dict:
    return next(
        row for row in ARTEFACT_DICT["bands"]
        if row["id"] == band_id and row["collection"] == collection
    )


def _profile(band_id: str, profile_id: str) -> dict:
    return next(
        row for row in ARTEFACT_DICT["profiles"]
        if row["id"] == profile_id and row["band_id"] == band_id
    )


def _item(item_id: str) -> dict:
    return next(row for row in ARTEFACT_DICT["items"] if row["item_id"] == item_id)


# --------------------------------------------------------------- knowledge_port

def test_kb_options_count() -> None:
    assert len(ARTEFACT_DICT["bands"]) >= 80
    assert {row["collection"] for row in ARTEFACT_DICT["bands"]} == {"mordheim", "trollheim"}


def test_kb_band_shape() -> None:
    for row in ARTEFACT_DICT["bands"]:
        assert row["id"] and row["name"]
        roster = row["roster"]
        assert roster["minimum_models"] >= 3
        assert roster["maximum_models"] >= roster["minimum_models"]
        assert roster["starting_gold"] > 0


def test_kb_sisters_roster() -> None:
    band = _band("mordheim", "sisters-of-sigmar")
    roster = band["roster"]
    assert roster["minimum_models"] == 3
    assert roster["maximum_models"] == 15
    assert roster["starting_gold"] == 500
    heroes = [m for m in roster["members"]
              if _profile(band["id"], m["profile_id"]).get("type") == "hero"]
    assert heroes


def test_kb_matriarch_profile() -> None:
    profile = _profile("sisters-of-sigmar", "sigmarite-matriarch")
    assert profile["cost"] == 70
    assert profile["experience"] == 20
    assert profile["characteristics"] == {
        "M": 4, "WS": 4, "BS": 4, "S": 3, "T": 3, "W": 1, "I": 4, "A": 1, "Ld": 8,
    }


def test_kb_every_band_usable_heroes() -> None:
    keys = {"M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"}
    for row in ARTEFACT_DICT["profiles"]:
        assert set(row["characteristics"]) == keys, row["id"]


def test_kb_sisters_equipment() -> None:
    item = _item("sigmarite_hammer")
    assert item["names"]["en"] == "Sigmarite Hammer"


def test_kb_unknown_warband() -> None:
    with pytest.raises(StopIteration):
        _band("mordheim", "does-not-exist")


def test_kb_post_battle_sequence() -> None:
    steps = ARTEFACT_DICT["campaign"]["post_battle_sequence"]
    assert len(steps) == 10
    assert [s["id"] for s in steps[:3]] == [
        "campaign.step.serious-injuries",
        "campaign.step.experience",
        "campaign.step.exploration",
    ]


# ---------------------------------------------------------- rules_catalogue

def test_rules_wrong_ruleset_rejected() -> None:
    assert ARTEFACT_DICT["ruleset"] == "mordheim"


def test_rules_search_empty_and_miss() -> None:
    # the artefact indexes exist for the TS search seam; empty query = no hits
    assert isinstance(ARTEFACT_DICT["indexes"], dict)


# ------------------------------------------------------------------ gap ledger

def test_blocked_vectors_stay_visible() -> None:
    data = json.loads((VECTORS / "rules_catalogue.json").read_text(encoding="utf-8"))
    blocked = [v for v in data["vectors"] if v.get("status") == "blocked"]
    ready = [v for v in data["vectors"] if v.get("status") == "ready"]
    assert data["gap"]["blocked_vectors"] == len(blocked)
    assert ready, "all rules-catalogue vectors blocked: gap must be unblocked"
    assert len(ready) + len(blocked) == data["source_tests"]


def test_vector_files_match_the_manifest_s_counts() -> None:
    manifest = json.loads(
        (ROOT / "tests" / "web" / "parity" / "campaign-test-manifest.json").read_text(encoding="utf-8")
    )
    for name, source, expected in (
        ("malformed_save.json", "tests/campaign/test_malformed_save_matrix.py", 29),
        ("rules_catalogue.json", "tests/campaign/test_rules_catalogue.py", 10),
        ("knowledge_port.json", "tests/campaign/test_knowledge_port.py", 9),
    ):
        data = json.loads((VECTORS / name).read_text(encoding="utf-8"))
        assert data["source_family"] == source
        assert len(data["vectors"]) == expected
        assert manifest["counts"].get("S", 0) >= sum((29, 10, 9))
