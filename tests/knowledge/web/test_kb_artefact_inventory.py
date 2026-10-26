"""The web KB inventory covers the maintained reader and campaign-file fixtures."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
CONTRACTS = ROOT / "contracts" / "campaign-file-v5"

#: (source path relative to the KB, reason the web Campaign Manager needs it).
#: Includes the TypeScript KnowledgeReader campaign sections and their source files.
REQUIRED_CATALOGUES = {
    "registry/collections.yaml": "collection list",
    "registry/warband-groups.yaml": "band sets",
    "catalog/items/*.yaml": "items and equipment",
    "catalog/skills/*.yaml": "skills",
    "catalog/mechanics/*.yaml": "weapon hands",
    "catalog/rules/racial-maximums.yaml": "racial maximums",
    "catalog/rules/*.yaml": "shared rules display (rules catalogue)",
    "catalog/campaign/trading-post.yaml": "trading post",
    "catalog/campaign/scenarios.yaml": "scenarios",
    "catalog/campaign/post-battle-sequence.yaml": "post-battle order",
    "catalog/campaign/serious-injuries.yaml": "injuries (post-battle engine)",
    "catalog/campaign/experience-and-advances.yaml": "advances (post-battle engine)",
    "catalog/campaign/exploration-and-income.yaml": "exploration (post-battle engine)",
    "catalog/campaign/magic.yaml": "lores and spells",
    "catalog/campaign/mutations.yaml": "mutations (post-battle engine)",
    "catalog/campaign/hired-swords-and-dramatis.yaml": "hiring entries (post-battle engine)",
    "catalog/campaign/scenario-rewards.yaml": "scenario rewards (application)",
    "catalog/campaign/warband-rating.yaml": "rating composition",
    "catalog/campaign/recruitment-and-veterans.yaml": "veterans/recruitment",
    "catalog/campaign/trading-and-rarity.yaml": "rarity availability",
    "catalog/hirelings/**/*.yaml": "hireling profiles, rules and traits",
}

EXCLUDED_SURFACES = [
    "simulation mappings",
    "execution contract",
    "runtime scope",
    "out-of-scope",
]


def _kb_sources() -> dict[str, list[Path]]:
    """Source files keyed by glob pattern (relative to the KB root)."""
    result = {}
    for pattern in REQUIRED_CATALOGUES:
        result[pattern] = sorted(KB.glob(pattern))
    return result


# The first two cases check the maintained required-source inventory itself.
@pytest.mark.evidence
def test_every_required_catalogue_exists() -> None:
    sources = _kb_sources()
    missing_files = {pattern for pattern, paths in sources.items() if not paths}
    assert not missing_files, f"inventory patterns matching no files: {sorted(missing_files)}"


@pytest.mark.evidence
def test_inventory_covers_campaign_sections_read_by_the_web_adapter() -> None:
    reader = ROOT / "packages/typescript/adapters/knowledge-reader/index.ts"
    consumed = set(re.findall(r'campaign\["([a-z_\-]+)"\]', reader.read_text(encoding="utf-8")))
    assert consumed, "no campaign section reads found in the maintained web adapter"
    projected_sources = {
        "hirelings": "catalog/hirelings/**/*.yaml",
        "warband_groups": "registry/warband-groups.yaml",
        "racial_maximums": "catalog/rules/racial-maximums.yaml",
        "post_battle_sequence": "catalog/campaign/post-battle-sequence.yaml",
    }
    sources = {projected_sources.get(name, f"catalog/campaign/{name}.yaml") for name in consumed}
    missing = sources - set(REQUIRED_CATALOGUES)
    assert not missing, f"web campaign catalogues missing from the KB inventory: {sorted(missing)}"


def test_every_band_used_by_v5_fixtures_resolves_against_the_kb() -> None:
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


def test_excluded_combat_lab_surfaces_are_not_inputs() -> None:
    assert not any(surface in pattern for surface in EXCLUDED_SURFACES for pattern in REQUIRED_CATALOGUES)
