"""P3.2 ↔ P3.3 cross-check: the TypeScript P3.2 adapter must produce
documents the Python contract reader accepts.

The TS round-trip test writes an artefact listing the fixtures it
round-tripped and the files it emitted. This module validates each emitted
file against the v5 schema via the desktop reader — the same acceptance the
plan demands for the Python↔web round-trip.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mordheim_campaign.persistence.campaigns import load_campaign

REPO_ROOT = Path(__file__).resolve().parents[3]
ARTEFACT = REPO_ROOT / "packages" / "typescript" / "adapters" / "campaign-file" / "_ts-roundtrip-artefact.json"

pytestmark = pytest.mark.skipif(
    not ARTEFACT.exists(),
    reason="TS round-trip artefact not present (P3.2 tests not run in this checkout)",
)


def _artefact() -> dict:
    return json.loads(ARTEFACT.read_text(encoding="utf-8"))


def test_artefact_lists_all_four_fixtures() -> None:
    data = _artefact()
    assert set(data["round_tripped"]) == {
        "draft.json",
        "active-campaign.json",
        "pending-post-battle.json",
        "full-inventory.json",
    }


def test_every_serialized_document_is_schema_valid() -> None:
    data = _artefact()
    for fixture, filename in sorted(data["serialized"].items()):
        path = ARTEFACT.parent / filename
        state = load_campaign(path)
        assert state.campaign.band_id, fixture


def test_serialized_documents_are_semantically_equal_to_fixtures() -> None:
    data = _artefact()
    for fixture, filename in sorted(data["serialized"].items()):
        original = json.loads((REPO_ROOT / "contracts" / "campaign-file-v5" / "fixtures" / fixture).read_text(encoding="utf-8"))
        reserialized = json.loads((ARTEFACT.parent / filename).read_text(encoding="utf-8"))
        original.pop("saved_at", None)
        reserialized.pop("saved_at", None)
        original.pop("view", None)
        reserialized.pop("view", None)
        assert reserialized == original, fixture
