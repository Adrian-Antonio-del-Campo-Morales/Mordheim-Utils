"""knowledge.items: integrity of canonical object references.

Verifies that ``catalog/items`` has no duplicated ids and no two objects with
the same normalized name (regression of short_bow/shortbow and
superior_black_powder/superior_blackpowder) and that every ``item_id``
reference in the KB (equipment lists, campaign catalogues, hirelings,
mechanics) resolves against the canonical catalogue. Context variables
(prefix "$") belong to procedures and are excluded.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"
ITEMS = ROOT / "catalog" / "items"


def canonical_item_ids() -> dict[str, Path]:
    ids: dict[str, Path] = {}
    for path in sorted(ITEMS.glob("*.yaml")):
        for item in yaml.safe_load(path.read_text(encoding="utf-8")).get("items", []):
            ids.setdefault(item["id"], path)
    return ids


def collect(node, key: str) -> list:
    found = []
    if isinstance(node, dict):
        if key in node:
            value = node[key]
            found.extend(value if isinstance(value, list) else [value])
        for child in node.values():
            found.extend(collect(child, key))
    elif isinstance(node, list):
        for child in node:
            found.extend(collect(child, key))
    return found


def test_no_duplicate_item_ids() -> None:
    ids = canonical_item_ids()
    assert len(ids) == sum(
        len(yaml.safe_load(path.read_text(encoding="utf-8")).get("items", []))
        for path in ITEMS.glob("*.yaml")
    ), "duplicated ids in catalog/items"


#: Name collisions the knowledge base publishes on purpose, by normalized name.
#:
#: The two former offenders — `shortbow`/`short_bow` and
#: `superior_black_powder`/`superior_blackpowder` — were two canonical records
#: for *one* object. These three are not: each pair is two records of two
#: different sources that happen to share a printed name, and merging one of
#: them would have dropped the prose, the price or the special rules of the
#: other. T07 promoted them, so they are declared here.
PUBLISHED_NAME_COLLISIONS = {
    # The KB's trollheim record and the MiM variant T05 declared (ITEM_VARIANTS).
    "familiar": ("familiar", "society_familiar"),
    # 2A Clan Moulder (Strength +1, Iron Grip) vs 2B Clan Pristekk (Capture).
    "thingcatcher": ("thingcatcher", "thing_catcher"),
    # The 2B variant T05 declared vs the KB's own out-of-scope record.
    "wolfcloak": ("wolf_cloak", "wolfcloak"),
}


def test_no_two_items_share_a_normalized_name() -> None:
    # shortbow/short_bow and superior_black_powder/superior_blackpowder used to
    # be two canonical records for the same object with different spellings.
    # The comparison is for equality: a collision that is not declared above
    # fails here, and a declared pair that stops colliding fails too until it
    # leaves the table.
    names: dict[str, list[str]] = {}
    for path in ITEMS.glob("*.yaml"):
        for item in yaml.safe_load(path.read_text(encoding="utf-8")).get("items", []):
            key = re.sub(r"[^a-z0-9]", "", (item.get("name") or "").lower())
            names.setdefault(key, []).append(item["id"])
    duplicates = {key: sorted(value) for key, value in names.items()
                  if len(value) > 1 and len(key) > 4}
    assert duplicates == {
        key: sorted(pair) for key, pair in PUBLISHED_NAME_COLLISIONS.items()
    }, duplicates


def test_every_item_id_reference_in_the_kb_resolves() -> None:
    ids = canonical_item_ids()
    dangling: list[tuple[str, str]] = []
    references = 0
    for path in ROOT.rglob("*.yaml"):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        if document is None:
            continue
        for ref in collect(document, "item_id"):
            if isinstance(ref, str) and ref.startswith("$"):
                continue  # variable de contexto de un procedimiento
            if not isinstance(ref, str):
                continue
            references += 1
            if ref not in ids:
                dangling.append((path.relative_to(ROOT).as_posix(), ref))
    assert references > 1000
    assert not dangling, dangling
