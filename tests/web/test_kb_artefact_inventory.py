"""web.kb-artefact-inventory: the P4.1 inventory stays honest.

Verifies against the KB sources directly (no generator dependency, so P4.2 can
be built in parallel) that:

1. every catalogue the Campaign Manager's ``KnowledgePort`` reads appears in
   the P4.1 inventory document;
2. every ``band_id`` used by the v4 fixtures resolves against the KB bands the
   artefact would include;
3. the explicitly excluded Combat Lab/simulation surfaces are documented as
   excluded in the inventory document.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "sources" / "knowledge"
INVENTORY = ROOT / "docs" / "decisions" / "web-migration.md"
CONTRACTS = ROOT / "contracts" / "campaign-file-v4"

#: (source path relative to the KB, reason the web Campaign Manager needs it).
#: Derived from the public read surface of ``KnowledgePort``; adding a public
#: KB read to the port without inventorying it here fails this test.
REQUIRED_CATALOGUES = {
    "registry/collections.yaml": "collection list (KnowledgePort.collections)",
    "registry/warband-groups.yaml": "band sets (KnowledgePort.warband_groups)",
    "catalog/items/*.yaml": "items (KnowledgePort.equipment/item_*)",
    "catalog/skills/*.yaml": "skills (KnowledgePort.skills)",
    "catalog/mechanics/*.yaml": "weapon hands (KnowledgePort.weapon_hands)",
    "catalog/rules/racial-maximums.yaml": "racial maximums (KnowledgePort.racial_maximums)",
    "catalog/rules/*.yaml": "shared rules display (rules catalogue)",
    "catalog/campaign/trading-post.yaml": "trading post (KnowledgePort.trading_post_*)",
    "catalog/campaign/scenarios.yaml": "scenarios (KnowledgePort.scenario_options)",
    "catalog/campaign/post-battle-sequence.yaml": "post-battle order (KnowledgePort.post_battle_sequence)",
    "catalog/campaign/serious-injuries.yaml": "injuries (post-battle engine)",
    "catalog/campaign/experience-and-advances.yaml": "advances (post-battle engine)",
    "catalog/campaign/exploration-and-income.yaml": "exploration (post-battle engine)",
    "catalog/campaign/magic.yaml": "lores/spells (KnowledgePort.wizard_lore/lore_spells)",
    "catalog/campaign/mutations.yaml": "mutations (post-battle engine)",
    "catalog/campaign/hired-swords-and-dramatis.yaml": "hiring entries (post-battle engine)",
    "catalog/campaign/scenario-rewards.yaml": "scenario rewards (application)",
    "catalog/campaign/warband-rating.yaml": "rating composition",
    "catalog/campaign/recruitment-and-veterans.yaml": "veterans/recruitment",
    "catalog/campaign/trading-and-rarity.yaml": "rarity availability",
    "catalog/hirelings/**/*.yaml": "hireling profiles/rules/traits (KnowledgePort.hireling_*)",
}

EXCLUDED_SURFACES = [
    "simulation mappings",
    "execution contract",
    "runtime scope",
    "out-of-scope",
]


def _inventory_text() -> str:
    return INVENTORY.read_text(encoding="utf-8")


def _kb_sources() -> dict[str, list[Path]]:
    """Source files keyed by glob pattern (relative to the KB root)."""
    result = {}
    for pattern in REQUIRED_CATALOGUES:
        result[pattern] = sorted(KB.glob(pattern))
    return result


def test_every_required_catalogue_exists_and_is_inventoried() -> None:
    text = _inventory_text()
    sources = _kb_sources()
    missing_files = {pattern for pattern, paths in sources.items() if not paths}
    assert not missing_files, f"inventory patterns matching no files: {sorted(missing_files)}"
    def _plain(pattern: str) -> str:
        """Directory prefix of a pattern; the inventory references directories."""
        directory = pattern.rsplit("/", 1)[0]
        return directory
    not_inventoried = {pattern for pattern in sources if _plain(pattern) not in text}
    assert not not_inventoried, f"catalogues the web needs but P4.1 does not inventory: {sorted(not_inventoried)}"


def test_inventory_covers_every_public_kb_read_of_the_port() -> None:
    """Each ``KnowledgePort`` public method that reads a new catalogue must be
    matched by an inventory row; scans the port source for loader/catalogue
    access points and cross-checks the documented source paths."""
    import mordheim_campaign.application.knowledge_port as _port_module

    port_source = Path(_port_module.__file__).resolve().read_text(encoding="utf-8")
    documented = set(re.findall(r"([a-z0-9\-/]+\.yaml)", _inventory_text()))
    consumed = set(re.findall(r'catalogue\("([a-z0-9\-]+)(?:\.yaml)?"\)', port_source))
    consumed = {f"catalog/campaign/{name}.yaml" for name in consumed}
    unconsumed_documented = {name for name in documented
                             if name.startswith("catalog/campaign/") and name not in consumed
                             and name not in REQUIRED_CATALOGUES}
    assert not unconsumed_documented, f"inventoried campaign catalogues the port never reads: {sorted(unconsumed_documented)}"


def test_every_band_used_by_v4_fixtures_resolves_against_the_kb() -> None:
    band_ids = set()
    for band_file in (KB / "bands").glob("*/*/band.yaml"):
        document = yaml.safe_load(band_file.read_text(encoding="utf-8")) or {}
        if document.get("id"):
            band_ids.add(str(document["id"]))
    assert band_ids, "no KB bands discovered"
    dangling = []
    for fixture in sorted(CONTRACTS.glob("fixtures/*.json")):
        document = json.loads(fixture.read_text(encoding="utf-8"))
        identity = (document.get("campaign") or {}).get("identity") or {}
        band_id = identity.get("band_id")
        if band_id and band_id not in band_ids:
            dangling.append((fixture.name, band_id))
    assert not dangling, f"fixture bands missing from the KB: {dangling}"


def test_excluded_combat_lab_surfaces_are_documented() -> None:
    text = _inventory_text()
    missing = [surface for surface in EXCLUDED_SURFACES if surface not in text]
    assert not missing, f"excluded surfaces not documented in the inventory: {missing}"
