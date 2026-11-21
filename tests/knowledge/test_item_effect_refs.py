"""Items that are list rows naming another item share its printed entry (``effect_ref``).

The text lives once, on the referenced item; the referencing record keeps its own
id, mechanic and status. The loader refuses a reference that would duplicate or
chain the text, and the web artefact projects the referenced entry.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mordheim_knowledge.loader import load_items
from tools.knowledge import generate_knowledge_web as generator


def test_every_reference_resolves_to_an_item_with_its_own_text() -> None:
    items = {row["id"]: row for row in load_items("mordheim")}
    refs = {item_id: row["effect_ref"] for item_id, row in items.items() if row.get("effect_ref")}
    assert len(refs) == 46
    for item_id, target in refs.items():
        assert "effect" not in items[item_id], item_id
        assert items[target].get("effect") and not items[target].get("effect_ref"), item_id


def _catalogue(tmp_path: Path, rows: list[dict]) -> Path:
    directory = tmp_path / "catalog" / "items"
    directory.mkdir(parents=True)
    (directory / "items.yaml").write_text(
        yaml.safe_dump({"schema_version": 2, "ruleset": "mordheim", "items": rows}), encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("rows", [
    # A record that references another and also restates prose.
    [{"id": "sword", "effect": "Parry."}, {"id": "scimitar", "effect_ref": "sword", "effect": "Parry."}],
    # A reference to a reference.
    [{"id": "sword", "effect": "Parry."}, {"id": "scimitar", "effect_ref": "sword"},
     {"id": "sabre", "effect_ref": "scimitar"}],
    # A reference to an unknown item.
    [{"id": "scimitar", "effect_ref": "sword"}],
])
def test_the_loader_refuses_duplicated_chained_or_unknown_references(tmp_path, rows) -> None:
    load_items.cache_clear()
    try:
        with pytest.raises(ValueError, match="effect_ref"):
            load_items("mordheim", _catalogue(tmp_path, rows))
    finally:
        load_items.cache_clear()


def test_the_artefact_shows_the_referenced_entry_in_both_locales() -> None:
    items = {item["item_id"]: item for item in generator._build_items("mordheim")}
    assert items["sword_scimitar"]["effects"] == items["sword"]["effects"]
    assert items["club"]["effects"] == items["mace"]["effects"]
    assert "effect_ref" not in items["sword_scimitar"]
