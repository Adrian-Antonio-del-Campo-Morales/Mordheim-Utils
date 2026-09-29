"""Executable record of the equipment visible-completeness decision.

The dynamic visible-completeness gate
(``tools/web/presentation-completeness-audit.mjs``, surface
``rules-catalogue/equipment``) reported 72 generic-fallback findings covering 30
objects. Twenty-four of them are canonical item rows whose source never
published a rules description: they carry ``combat_status: out_of_scope`` and
neither ``effect`` nor ``effect_i18n`` in the promoted KB, and no staging
document declares them. Inventing an effect or a translation would be a data
defect, so the product renders a specific localized absence notice instead of
the generic fallback (``RulesCatalogue`` / ``sourceDescriptionUnavailableText``),
and this test keeps the evidence executable.

KB↔staging parity is therefore *not applicable* for those 24 rows, and the test
asserts exactly that: if a row ever gains an effect, or a 2A/2B document ever
starts declaring one, the absence is no longer real and the decision must be
revisited. The mirror contract that *is* applicable — the six exploration
magical artefacts, which must publish both locales for their names and effects
in the canonical campaign catalogue — is checked too.
"""
from __future__ import annotations

from pathlib import Path

import yaml

KB_ROOT = Path(__file__).resolve().parents[3] / "sources" / "knowledge"
STAGING_ROOTS = (
    Path(__file__).resolve().parents[3] / "sources" / "2A",
    Path(__file__).resolve().parents[3] / "sources" / "2B",
)
CAMPAIGN = KB_ROOT / "catalog" / "campaign" / "exploration-and-income.yaml"

#: The 24 canonical rows whose source publishes no description (2026-09-29 gate).
ABSENT_ITEM_IDS = frozenset({
    "ancestral_claw", "anointed_bolts", "bronze_breastplate", "carronade",
    "carronade_cannonball", "carronade_chain", "carronade_grapeshot",
    "dispelling_scroll", "feather_headdress", "hochland_long_rifle",
    "horned_rat_amulet", "icon_of_manann", "jungle_roast", "magic_tattoo",
    "magic_tattoos", "pirate_flag", "poison_darts", "poisoned_darts",
    "sacrifice_dagger", "scourge", "shrunken_head", "spider_amulet", "whip",
    "yari",
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


def test_canonical_absence_is_real_and_has_no_staging_mirror() -> None:
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

    staged: list[str] = []
    for root in STAGING_ROOTS:
        for path in sorted(root.rglob("*.yaml")):
            for row in _walk(yaml.safe_load(path.read_text(encoding="utf-8"))):
                if row.get("id") in ABSENT_ITEM_IDS and (row.get("effect") or row.get("effect_i18n")):
                    staged.append(f"{path.relative_to(root.parent)}#{row['id']}")
    assert not staged, (
        "staging publishes an effect for a row the KB leaves undocumented; the mirror "
        f"contract now applies: {staged}"
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
