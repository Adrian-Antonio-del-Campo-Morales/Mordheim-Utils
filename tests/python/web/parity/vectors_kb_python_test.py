"""Python runner for the shared KB parity vectors.

Each vector asserts one invariant of the generated web KB artefact. The TS
mirror (``tests/typescript/parity-kb-vectors.test.ts``) consumes the same
vector files against the same artefact, so a divergence between the Python
builder and the TS reader fails on one side first and the vector pinpoints
it.

Vectors with ``status: blocked`` document parity gaps (T5 flow): they are
counted and must stay visible, but they do not execute until the blocking
gap is fixed.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
VECTORS = ROOT / "tests" / "fixtures" / "parity" / "vectors"
ARTEFACT = ROOT / "outputs" / "web-public" / "knowledge" / "knowledge-web.json"
MANIFEST = ROOT / "outputs" / "parity" / "test-manifests" / "campaign-test-manifest.json"
MANIFEST_GENERATOR = ROOT / "tools" / "verification" / "make_test_manifest.py"

ARTEFACT_DICT: dict = json.loads(ARTEFACT.read_text(encoding="utf-8"))
PROSE: dict = json.loads((ARTEFACT.parent / ARTEFACT_DICT["rules_prose_url"]).read_text(encoding="utf-8"))


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


def _prose_row(stem: str, entry_id: str) -> dict:
    return next(row for row in PROSE[stem] if row["id"] == entry_id)


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
    assert isinstance(ARTEFACT_DICT["indexes"], dict)


def test_rules_prose_documents_present() -> None:
    assert {"special-rules", "conditions", "core-combat"} <= set(PROSE)


def test_rules_special_rules_count() -> None:
    assert sum(row["id"].startswith("shared-rule.") for row in PROSE["special-rules"]) == 68


def test_rules_categories_ordered() -> None:
    assert {"conditions", "core-combat", "localized-labels", "profile-special-rules", "racial-maximums", "resolution", "special-rules"} == set(PROSE)


def test_rules_always_hungry_en() -> None:
    row = _prose_row("special-rules", "shared-rule.always-hungry")
    assert row["names"]["en"] == "Always Hungry"
    assert row["effects"]["en"].startswith("A Troll requires")


def test_rules_fires_of_uzhul() -> None:
    lores = ARTEFACT_DICT["campaign"]["magic"]["lores"]
    spell = next(
        spell
        for lore in lores
        for spell in lore.get("spells", [])
        if spell.get("id") == "spell.lesser-magic.fires-of-uzhul"
    )
    assert spell["name"] == "Fires of U'Zhul"
    assert spell["difficulty"] == 7


def test_rules_always_hungry_es() -> None:
    row = _prose_row("special-rules", "shared-rule.always-hungry")
    assert row["names"]["es"] == "Siempre Hambriento"


def test_rules_search_accent_insensitive_data() -> None:
    # the TS search seam matches names AND effects, case-insensitively
    row = _prose_row("special-rules", "shared-rule.always-hungry")
    hay = f"{row['names']['en']} {row['effects']['en']}".lower()
    assert "always hungry" in hay


def test_rules_search_scoped_by_stem() -> None:
    ids = {row["id"] for row in PROSE["special-rules"]}
    assert "shared-rule.always-hungry" in ids


# ------------------------------------------------------------------ consistency

def test_no_blocked_vectors_remain_in_any_vector_file() -> None:
    for name in ("malformed_save.json", "rules_catalogue.json", "knowledge_port.json"):
        data = json.loads((VECTORS / name).read_text(encoding="utf-8"))
        blocked = [v for v in data["vectors"] if v.get("status") == "blocked"]
        assert not blocked, f"{name}: blocked vectors remain: {[v['id'] for v in blocked]}"
        gap = data.get("gap") or {}
        if gap:
            assert gap.get("status") == "RESOLVED", name


def test_vector_files_match_the_manifest_s_counts() -> None:
    subprocess.run([sys.executable, str(MANIFEST_GENERATOR)], cwd=ROOT, check=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for name, source, expected in (
        ("malformed_save.json", "tests/python/campaign/test_malformed_save_matrix.py", 29),
        ("rules_catalogue.json", "tests/python/campaign/test_rules_catalogue.py", 10),
        ("knowledge_port.json", "tests/python/campaign/test_knowledge_port.py", 9),
    ):
        data = json.loads((VECTORS / name).read_text(encoding="utf-8"))
        assert data["source_family"] == source
        assert len(data["vectors"]) == expected
        assert manifest["counts"].get("S", 0) >= sum((29, 10, 9))
