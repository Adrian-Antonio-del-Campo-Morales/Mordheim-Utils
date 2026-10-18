"""Canonical equipment description absence and magical-artefact locale guards.

An item without a printed rules description must stay out_of_scope without an
invented effect or translation. If it acquires a documented effect or executable
binding, revisit its specific absence notice instead of preserving a fallback.
The six exploration magical artefacts must publish names/effects in both locales.
"""
from __future__ import annotations

from pathlib import Path

import yaml

KB_ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"
CAMPAIGN = KB_ROOT / "catalog" / "campaign" / "exploration-and-income.yaml"

#: The canonical rows whose source publishes no description (2026-09-29 gate).
#: ``yari`` left the set on 2026-10-16: the Deathbringer equipment line's
#: canonical item is now bound to its declared operator ``weapon.yari-one-handed``
#: (the two printed grips are ``weapon.yari-one-handed`` and
#: ``weapon.yari-two-handed``), which is the state its three sibling items
#: (``kusara_kama``, ``death_knife``, ``witch_sword``) already occupy. Its source
#: still publishes no description of its own, so the row carries no effect and the
#: product resolves it through the bound operator instead of the absence notice.
ABSENT_ITEM_IDS = frozenset({
    "ancestral_claw", "anointed_bolts", "carronade",
    "carronade_cannonball", "carronade_chain", "carronade_grapeshot",
    "dispelling_scroll", "feather_headdress", "hochland_long_rifle",
    "horned_rat_amulet", "icon_of_manann", "jungle_roast", "magic_tattoo",
    "magic_tattoos", "pirate_flag", "poison_darts", "poisoned_darts",
    "sacrifice_dagger", "scourge", "shrunken_head", "spider_amulet", "whip",
})

#: The six exploration magical artefacts and the published Spanish name each
#: must carry in both locales (name + effect).
MAGICAL_ARTEFACTS = {
    "campaign.magical-artefact.boots-and-rope-of-pieter": "Las Botas y la Cuerda de Pieter",
    "campaign.magical-artefact.count-of-ventimiglias-misericordia": "La Misericordia del Conde de Ventimiglia",
    "campaign.magical-artefact.attlas-plate-mail": "Coraza de Placas de Att'la",
    "campaign.magical-artefact.bow-of-seeking": "Arco Buscador",
    "campaign.magical-artefact.executioners-hood": "Capucha del Verdugo",
    "campaign.magical-artefact.all-seeing-eye-of-numas": "Ojo que Todo lo Ve de Numas",
}


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _kb_items() -> dict[str, dict]:
    items: dict[str, dict] = {}
    for path in sorted((KB_ROOT / "catalog" / "items").glob("*.yaml")):
        for row in _walk(yaml.safe_load(path.read_text(encoding="utf-8"))):
            if isinstance(row.get("id"), str):
                items.setdefault(row["id"], row)
    return items


def test_canonical_absence_is_real() -> None:
    items = _kb_items()
    missing = sorted(ABSENT_ITEM_IDS - set(items))
    assert not missing, f"rows not found in the canonical KB: {missing}"

    for item_id in sorted(ABSENT_ITEM_IDS):
        row = items[item_id]
        assert row.get("combat_status") == "out_of_scope", f"{item_id} is no longer out_of_scope"
        assert not row.get("effect") and not row.get("effect_i18n"), (
            f"{item_id} now publishes an effect: the specific absence notice must be "
            "replaced by the real description"
        )



def test_magical_artefacts_publish_both_locales() -> None:
    rows = {
        row["id"]: row
        for row in _walk(yaml.safe_load(CAMPAIGN.read_text(encoding="utf-8")))
        if isinstance(row.get("id"), str)
    }
    for artefact_id, spanish in MAGICAL_ARTEFACTS.items():
        row = rows.get(artefact_id)
        assert row, f"{artefact_id} missing from the campaign catalogue"
        assert row.get("result_i18n", {}).get("es") == spanish, f"{artefact_id} Spanish name"
        assert row.get("effect"), f"{artefact_id} English effect"
        assert row.get("effect_i18n", {}).get("es"), f"{artefact_id} Spanish effect"
