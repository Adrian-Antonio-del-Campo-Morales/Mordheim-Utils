"""knowledge.campaign: loader contract for the published campaign catalogues.

``load_post_battle_sequence``, ``load_campaign_catalog``, ``load_hirelings``
and ``load_warband_groups`` (all in ``mordheim_knowledge.campaign``) are the
runtime read path of the KB campaign data: they validate headers, per-document
id uniqueness and reference resolution (items, profiles across band packages
and ``catalog/hirelings``, lores, bands and ``warband-group.*``) and raise
``ValueError`` on a broken catalogue instead of returning partial data.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

import mordheim_knowledge.campaign as campaign_module
from mordheim_knowledge.campaign import load_campaign_catalog
from mordheim_knowledge.campaign import load_hirelings
from mordheim_knowledge.campaign import load_post_battle_sequence
from mordheim_knowledge.campaign import load_warband_groups


SEQUENCE_STEP_IDS = (
    "campaign.step.serious-injuries",
    "campaign.step.experience",
    "campaign.step.exploration",
    "campaign.step.sell-wyrdstone",
    "campaign.step.veterans",
    "campaign.step.rare-items",
    "campaign.step.dramatis-personae",
    "campaign.step.recruit-and-buy-common",
    "campaign.step.reallocate-equipment",
    "campaign.step.update-rating",
)

CAMPAIGN_STEMS = {
    "experience-and-advances", "exploration-and-income",
    "hired-swords-and-dramatis", "magic", "mutations",
    "post-battle-sequence", "recruitment-and-veterans", "scenarios",
    "serious-injuries", "trading-and-rarity", "trading-post",
    "warband-rating",
}


@pytest.fixture(autouse=True)
def _clear_loader_caches():
    """The campaign loaders cache by root; keep injected documents fresh."""
    for loader in (
        campaign_module.load_campaign_catalog,
        campaign_module.load_post_battle_sequence,
        campaign_module.load_hirelings,
        campaign_module.load_warband_groups,
    ):
        loader.cache_clear()
    yield
    for loader in (
        campaign_module.load_campaign_catalog,
        campaign_module.load_post_battle_sequence,
        campaign_module.load_hirelings,
        campaign_module.load_warband_groups,
    ):
        loader.cache_clear()


def _spoof(monkeypatch: pytest.MonkeyPatch, name: str, mutate):
    """Patch ``read_yaml`` so ``catalog/campaign/<name>`` returns a mutation."""
    real_read = campaign_module.read_yaml

    def fake_read(path):
        document = real_read(path)
        if Path(path).name == name:
            document = copy.deepcopy(document)
            mutate(document)
        return document

    monkeypatch.setattr(campaign_module, "read_yaml", fake_read)


# --------------------------------------------------------------------------- #
# Post-battle sequence
# --------------------------------------------------------------------------- #


def test_post_battle_sequence_is_normative():
    sequence = load_post_battle_sequence()
    assert sequence.id == "campaign.post-battle"
    assert [step.id for step in sequence.steps] == list(SEQUENCE_STEP_IDS)
    assert [step.order for step in sequence.steps] == list(range(1, 11))
    assert all(step.name for step in sequence.steps)
    assert all(step.resolves.endswith(".yaml") for step in sequence.steps)
    assert all(step.repeatability in {"once", "repeatable"} for step in sequence.steps)
    # The two "sell wyrdstone" steps resolve to the same catalogue, so the
    # sequence resolves seven distinct documents.
    assert len(sequence.resolved_catalogues) == 7
    assert sequence.steps[0].resolves == "serious-injuries.yaml"
    assert sequence.steps[-1].resolves == "warband-rating.yaml"


def test_post_battle_sequence_rejects_unknown_resolves(monkeypatch):
    def mutate(document):
        document["sequence"]["steps"][0]["resolves"] = "missing-tables.yaml"

    _spoof(monkeypatch, "post-battle-sequence.yaml", mutate)
    with pytest.raises(ValueError, match="resolves unknown catalogue"):
        load_post_battle_sequence()


def test_post_battle_sequence_rejects_contiguous_order_breaks(monkeypatch):
    def mutate(document):
        document["sequence"]["steps"][1]["order"] = 12

    _spoof(monkeypatch, "post-battle-sequence.yaml", mutate)
    with pytest.raises(ValueError, match="contiguous from 1"):
        load_post_battle_sequence()


# --------------------------------------------------------------------------- #
# Campaign catalogue
# --------------------------------------------------------------------------- #


def test_campaign_catalog_loads_every_published_document():
    catalog = load_campaign_catalog()
    assert set(catalog.documents) == CAMPAIGN_STEMS
    # Canonical counts of the biggest read models (also enforced per document
    # by tests/knowledge/test_campaign_catalogs.py against the raw YAML).
    assert len(catalog.catalogue("trading-post.yaml")["items"]) == 338
    trading = catalog.catalogue("trading-post")
    assert len({row["id"] for row in trading["items"]}) == 338
    hired = catalog.catalogue("hired-swords-and-dramatis.yaml")
    assert len(hired["hired_swords"]) == 72
    assert len(hired["dramatis_personae"]) == 26
    magic = catalog.catalogue("magic.yaml")
    assert len(magic["lores"]) == 31
    assert len({spell["id"] for lore in magic["lores"] for spell in lore.get("spells", [])}) == 188
    assert len(catalog.catalogue("scenarios.yaml")["scenarios"]) == 98


def test_campaign_catalog_rejects_bad_schema_version(monkeypatch):
    def mutate(document):
        document["schema_version"] = 99

    _spoof(monkeypatch, "experience-and-advances.yaml", mutate)
    with pytest.raises(ValueError, match="unsupported schema_version"):
        load_campaign_catalog()


def test_campaign_catalog_rejects_duplicate_declared_ids(monkeypatch):
    def mutate(document):
        document["scenarios"][1]["id"] = document["scenarios"][0]["id"]

    _spoof(monkeypatch, "scenarios.yaml", mutate)
    with pytest.raises(ValueError, match="duplicate declared ids"):
        load_campaign_catalog()


def test_campaign_catalog_rejects_unknown_profile_id(monkeypatch):
    def mutate(document):
        document["hired_swords"][0]["profile_id"] = "hireling.hired-sword.nobody"

    _spoof(monkeypatch, "hired-swords-and-dramatis.yaml", mutate)
    with pytest.raises(ValueError, match="unknown hireling profile"):
        load_campaign_catalog()


def test_campaign_catalog_rejects_unknown_warband_group(monkeypatch):
    def mutate(document):
        document["hired_swords"][0]["eligibility"]["allow_groups"] = ["warband-group.nobody"]

    _spoof(monkeypatch, "hired-swords-and-dramatis.yaml", mutate)
    with pytest.raises(ValueError, match="unknown warband group"):
        load_campaign_catalog()


def test_campaign_catalog_rejects_unknown_band_reference(monkeypatch):
    def mutate(document):
        for item in document["items"]:
            restrictions = item.get("restrictions") or ()
            if any(restriction.get("band_ids") for restriction in restrictions):
                restriction = next(r for r in restrictions if r.get("band_ids"))
                restriction["band_ids"][0] = "not-a-band"
                return

    _spoof(monkeypatch, "trading-post.yaml", mutate)
    with pytest.raises(ValueError, match="unknown band reference"):
        load_campaign_catalog()


def test_campaign_catalog_rejects_unknown_item_reference(monkeypatch):
    def mutate(document):
        for scenario in document["scenarios"]:
            contents = (scenario.get("progression") or {}).get("loot", {}).get("contents") or ()
            for content in contents:
                if "item_id" in content:
                    content["item_id"] = "not-an-item"
                    return

    _spoof(monkeypatch, "scenarios.yaml", mutate)
    with pytest.raises(ValueError, match="unknown item reference"):
        load_campaign_catalog()


# --------------------------------------------------------------------------- #
# Hireling catalogue and warband groups (shared resolution pools)
# --------------------------------------------------------------------------- #


def test_hireling_catalogue_profiles_resolve_across_catalog():
    catalogue = load_hirelings()
    profiles = catalogue.profiles
    assert len(profiles) == 102
    ids = [row["id"] for row in profiles]
    assert len(set(ids)) == len(ids)
    assert all(profile_id.startswith("hireling.") for profile_id in ids)
    assert all(row.get("name") for row in profiles)
    # Every entry of the published hiring catalogue names one of these profiles.
    document = load_campaign_catalog().catalogue("hired-swords-and-dramatis.yaml")
    entries = document["hired_swords"] + document["dramatis_personae"]
    assert len(entries) == 98
    assert {entry["profile_id"] for entry in entries} <= catalogue.profile_ids


def test_hireling_catalogue_rejects_duplicate_declared_ids(monkeypatch):
    def mutate(document):
        if len(document.get("profiles", [])) < 2:
            return
        document["profiles"][1]["id"] = document["profiles"][0]["id"]

    _spoof(monkeypatch, "grade-1b.yaml", mutate)
    with pytest.raises(ValueError, match="duplicate declared ids"):
        load_hirelings()


def test_hireling_catalogue_rejects_undeclared_rule_reference(monkeypatch):
    def mutate(document):
        for profile in document.get("profiles", []):
            if profile.get("rule_ids"):
                profile["rule_ids"][0] = "hireling.hired-sword.nobody.rule.ghost"
                return

    _spoof(monkeypatch, "core.yaml", mutate)
    with pytest.raises(ValueError, match="references undeclared rules"):
        load_hirelings()


def test_warband_groups_registry_loads_and_resolves():
    groups = load_warband_groups()
    assert len(groups) == 24
    ids = [group["id"] for group in groups]
    assert len(set(ids)) == len(ids)
    assert all(group_id.startswith("warband-group.") for group_id in ids)
    assert all(group.get("kind") for group in groups)
    # A group used by the published hiring eligibility resolves by construction.
    group_ids = {group["id"] for group in groups}
    document = load_campaign_catalog().catalogue("hired-swords-and-dramatis.yaml")
    for entry in document["hired_swords"] + document["dramatis_personae"]:
        eligibility = entry.get("eligibility") or {}
        assert set(eligibility.get("allow_groups") or []) <= group_ids
