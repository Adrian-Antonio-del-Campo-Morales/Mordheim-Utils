"""knowledge.items: integridad de referencias canónicas a objetos.

Verifica que ``catalog/items`` no contenga ids duplicados ni dos objetos con el
mismo nombre normalizado (regresión de short_bow/shortbow y
superior_black_powder/superior_blackpowder) y que toda referencia ``item_id``
de la KB (listas de equipo, catálogos de campaña, hirelings, mecánicas)
resuelva contra el catálogo canónico. Las variables de contexto (prefijo «$»)
pertenecen a procedimientos y se excluyen.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2] / "sources" / "knowledge"
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
    ), "ids duplicados en catalog/items"


def test_no_two_items_share_a_normalized_name() -> None:
    # shortbow/short_bow y superior_black_powder/superior_blackpowder eran dos
    # fichas canónicas para el mismo objeto con grafías distintas.
    names: dict[str, list[str]] = {}
    for path in ITEMS.glob("*.yaml"):
        for item in yaml.safe_load(path.read_text(encoding="utf-8")).get("items", []):
            key = re.sub(r"[^a-z0-9]", "", (item.get("name") or "").lower())
            names.setdefault(key, []).append(item["id"])
    duplicates = {key: value for key, value in names.items()
                  if len(value) > 1 and len(key) > 4}
    assert not duplicates, duplicates


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
