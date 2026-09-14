"""Hostile-input probes for the P4.3 KnowledgeReader adapter (Python mirror).

The TypeScript adapter (`packages/typescript/adapters/knowledge-reader/`) is
the web-side consumer, but the *contract* it implements is verified here from
the Python side too: the artefact must never contain the malformations these
probes simulate, and the generator must reject KB drift that would produce
them. This closes the loop: generator guarantees → artefact invariants →
adapter assumptions.

Probes:
1. no record row with a null/empty id;
2. no duplicate ids in any family (adapter maps would silently shadow);
3. every `names` entry is a non-empty string (no numeric/None names);
4. `weapon_hands` values are positive ints;
5. profile rows always carry `collection` + `band_id` (adapter's scoped key).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "knowledge"))
PACKAGE_ROOTS = (
    ROOT / "packages" / "python" / "combat-engine",
    ROOT / "packages" / "python" / "roster-construction",
    ROOT / "packages" / "python" / "core",
    ROOT / "packages" / "python" / "knowledge",
    ROOT / "packages" / "python" / "campaign",
)
for package_root in reversed(PACKAGE_ROOTS):
    sys.path.insert(0, str(package_root))

import generate_knowledge_web as generator  # noqa: E402


def _artefact() -> dict:
    return generator.generate()


def test_no_record_row_carries_a_null_or_empty_id() -> None:
    artefact = _artefact()
    for family, id_field in (("bands", "id"), ("profiles", "id"), ("items", "item_id"), ("skills", "id")):
        for row in artefact[family]:
            value = row.get(id_field)
            assert isinstance(value, str) and value, f"{family}: row with bad {id_field}: {row!r:.120}"


def test_no_duplicate_ids_would_shadow_adapter_maps() -> None:
    artefact = _artefact()
    assert len({row["id"] for row in artefact["bands"]}) == len(artefact["bands"])
    assert len({row["item_id"] for row in artefact["items"]}) == len(artefact["items"])
    scoped = {(row["collection"], row["band_id"], row["id"]) for row in artefact["profiles"]}
    assert len(scoped) == len(artefact["profiles"])


def test_every_name_entry_is_a_non_empty_string() -> None:
    artefact = _artefact()
    for family in ("bands", "profiles", "items", "skills"):
        for row in artefact[family]:
            for locale, value in (row.get("names") or {}).items():
                assert isinstance(value, str) and value.strip(), (
                    f"{family}/{row.get('id', row.get('item_id'))}: bad name for {locale}: {value!r}"
                )


def test_weapon_hands_are_positive_integers() -> None:
    artefact = _artefact()
    for mechanic_id, hands in (artefact.get("weapon_hands") or {}).items():
        assert isinstance(hands, int) and hands > 0, f"weapon_hands[{mechanic_id}] = {hands!r}"


def test_profile_rows_carry_collection_and_band_id() -> None:
    """The TS adapter keys profiles by `collection/band_id/id`; a row missing
    those would fall back to the unscoped map and shadow across bands."""
    artefact = _artefact()
    for row in artefact["profiles"]:
        assert isinstance(row.get("collection"), str) and row["collection"]
        assert isinstance(row.get("band_id"), str) and row["band_id"]
