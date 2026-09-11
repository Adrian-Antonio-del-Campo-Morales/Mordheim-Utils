"""web.knowledge-artefact: the P4.2 generator is deterministic and complete.

Tests the YAML → JSON web generator (`tools/knowledge/generate_knowledge_web.py`)
against the Knowledge Base inventory:

1. the artefact builds and contains every required top section;
2. output is byte-identical across runs (no timestamps, stable order);
3. every band/profile/item/skill id is unique in its declared scope;
4. every stable id resolves (profiles→bands, trading-post item ids→KB items);
5. excluded Combat Lab data never leaks into the artefact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools" / "knowledge"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(ROOT / "src"))

import generate_knowledge_web as generator  # noqa: E402


def _artefact() -> dict:
    return generator.generate()


def test_artefact_has_every_required_top_section() -> None:
    artefact = _artefact()
    for key in ("schema_version", "ruleset", "collections", "bands", "profiles",
                "items", "skills", "weapon_hands", "campaign", "indexes"):
        assert key in artefact, f"missing top section {key!r}"
    assert artefact["schema_version"] == 1
    assert artefact["ruleset"] == "mordheim"
    for stem in generator.CAMPAIGN_CATALOGUE_STEMS:
        assert stem in artefact["campaign"], f"campaign catalogue {stem!r} missing from the artefact"


def test_output_is_byte_identical_across_runs() -> None:
    first = json.dumps(_artefact(), ensure_ascii=False, indent=1, sort_keys=False)
    second = json.dumps(_artefact(), ensure_ascii=False, indent=1, sort_keys=False)
    assert first == second


def test_ids_are_unique_in_their_declared_scope() -> None:
    artefact = _artefact()
    assert len({str(band["id"]) for band in artefact["bands"]}) == len(artefact["bands"])
    assert len({str(item["item_id"]) for item in artefact["items"]}) == len(artefact["items"])
    assert len({str(skill["id"]) for skill in artefact["skills"]}) == len(artefact["skills"])
    scoped = {(str(profile["collection"]), str(profile["band_id"]), str(profile["id"]))
              for profile in artefact["profiles"]}
    assert len(scoped) == len(artefact["profiles"])


def test_stable_references_resolve() -> None:
    artefact = _artefact()
    band_keys = {(str(band["collection"]), str(band["id"])) for band in artefact["bands"]}
    for profile in artefact["profiles"]:
        assert (str(profile["collection"]), str(profile["band_id"])) in band_keys
    all_item_ids = {str(row["id"]) for row in __import__("mordheim_knowledge.loader", fromlist=["load_items"]).load_items(artefact["ruleset"])}
    artefact_item_ids = {str(item["item_id"]) for item in artefact["items"]}
    assert artefact_item_ids <= all_item_ids
    # indexes stay coherent
    assert set(artefact["indexes"]["items_by_id"]) == artefact_item_ids


def test_profiles_materialize_shared_special_rule_references() -> None:
    artefact = _artefact()
    profile = next(row for row in artefact["profiles"] if row["id"] == "serpent-priestess")
    assert "shared-rule.leader" in profile["rule_ids"]


def test_excluded_combat_lab_data_does_not_leak() -> None:
    artefact = _artefact()
    for item in artefact["items"]:
        assert item["kind"] != "out-of-scope"
    text = json.dumps(artefact)
    for forbidden in ("simulation-mappings", "execution-contract", "runtime-scope"):
        assert forbidden not in text


def test_display_names_travel_per_locale_with_canonical_english() -> None:
    artefact = _artefact()
    sample = artefact["bands"][0]
    assert "names" in sample and sample["names"].get("en"), "canonical English name missing"
    translated = [item for item in artefact["items"] if "es" in item.get("names", {})]
    assert translated, "expected at least some Spanish translations in the KB"


def test_unsupported_ruleset_fails_with_actionable_error() -> None:
    """A ruleset whose KB catalogues do not exist stops the build with a clear
    GenerationError naming the ruleset — never a raw loader traceback."""
    import pytest

    with pytest.raises(generator.GenerationError, match="trollheim"):
        generator.generate("trollheim")


def test_collections_of_the_artefact_match_the_ruleset() -> None:
    artefact = _artefact()
    for collection in artefact["collections"]:
        assert artefact["ruleset"] in collection["rulesets"]
    indexed = artefact["indexes"]["bands_by_collection"]
    assert set(indexed) == {str(collection["id"]) for collection in artefact["collections"]}
