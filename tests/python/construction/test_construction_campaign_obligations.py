"""T10 campaigns: the KB publishes the data the campaign obligations consume.

T09 handed four obligations to T10. Each one needs a *published* datum; this gate
checks the datum in ``sources/knowledge`` (and its staging origin), so the
behavioural tests in ``tests/typescript`` cannot pass against invented data:

1. the warband-creation roll of `imperial-noble--family-heirloom`
   (`campaign.recruitment-and-veterans.creation_decisions`): the band rule, its
   recipients, the dice and the printed outcome of every interval;
2. the Rout-test exemption of `raw-recruits--dont-mind-them`: the rule names the
   recipients it strips from the warband's muster, and the generator materialises
   that as the per-profile `rout_test_exempt` fact;
3. the market scope of `repeater_pistol_moh`: the printed clause is published as
   a structured `condition` scope, in the canonical catalogue **and** in the
   staging tree the promotion reads, and `runic_attlas_plate_mail` stays a
   unique find that is not sold;
4. the canonical id of the exploration find: the magical-artefact row of
   `Att'la's Plate Mail` publishes the item id of the promoted catalogue row.

The behavioural side lives in
`tests/typescript/domain/campaign/{creation-decisions,rout-test,market}.test.ts`
and `tests/typescript/application/campaign/t10-obligations-flow.test.ts`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mordheim_knowledge.loader import load_bands, load_items, read_yaml

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
STAGING = ROOT / "sources"
CONTRACTS = ROOT / "contracts" / "knowledge-editorial-v1"
COLLECTION = "mordheim"

KAZ = "adventurers-kaz"
PATROL = "lothern-sea-patrol-sar"
MASTERS = "masters-of-horror-sylv"
HEIRLOOM = "imperial-noble--family-heirloom"
ROUT_RULE = "raw-recruits--dont-mind-them"
ARTEFACT_NAME = "Att'la's Plate Mail"


def _band(band_id: str):
    return next(band for band in load_bands(COLLECTION, KB) if str(band.band["id"]) == band_id)


def _rule(band, rule_id: str) -> dict:
    rule = next((row for row in band.special_rules if str(row.get("id")) == rule_id), None)
    assert rule is not None, f"{band.band['id']} declares no rule {rule_id}"
    return rule


def _campaign(stem: str) -> dict:
    return read_yaml(KB / "catalog" / "campaign" / f"{stem}.yaml")


def _artefact() -> dict:
    path = ROOT / "build" / "generated" / "knowledge-web" / "knowledge-web.json"
    if not path.exists():
        pytest.skip("run tools/knowledge/generate_knowledge_web.py to check the artefact side")
    return json.loads(path.read_text(encoding="utf-8"))


def test_family_heirloom_publishes_the_printed_creation_roll():
    catalogue = _campaign("recruitment-and-veterans")
    decisions = catalogue.get("creation_decisions") or ()
    assert decisions, "the campaign catalogue must publish the creation rolls"
    entry = next(
        (row for row in decisions if str(row.get("id")) == "campaign.creation.family-heirloom"),
        None,
    )
    assert entry is not None, "the Family Heirloom roll must be published under a stable id"
    assert entry["band_id"] == KAZ
    assert entry["rule_id"] == HEIRLOOM
    assert entry["profile_ids"] == ["imperial-noble"]
    assert entry["required"] is True
    assert entry["roll"]["dice"] == {"count": 1, "sides": 6}
    assert entry["name_i18n"]["es"].strip()
    assert entry.get("note", "").strip()

    # The roll is owed by the band that prints the rule, for the profile the
    # rule names: both must exist in the KB.
    band = _band(KAZ)
    rule = _rule(band, HEIRLOOM)
    assert "imperial-noble" in [str(row.get("id")) for row in band.profiles]
    assert "imperial-noble" in (
        (rule.get("applies_to") or {}).get("profile_ids") or ()
    ), "the rule must name its recipient profile"

    # Every interval of the published table transcribes the printed sentence,
    # and the three intervals cover the whole D6 exactly once.
    printed = " ".join(str(rule.get("effect") or "").split())
    outcomes = entry["outcomes"]
    assert [(row["when"]["min"], row["when"]["max"]) for row in outcomes] == [
        (1, 2),
        (3, 4),
        (5, 6),
    ]
    for row in outcomes:
        text = " ".join(str(row["result"]).split())
        assert text in printed, f"outcome {row['result_id']!r} is not the printed wording"
        assert str(row["result_id"]).strip()
        assert row["result_i18n"]["es"].strip()


def test_rout_exemption_names_its_recipients_and_the_generator_curates_them_once():
    band = _band(PATROL)
    rule = _rule(band, ROUT_RULE)
    assert (rule.get("applies_to") or {}).get("profile_ids") == ["raw-recruits"], (
        "the clause must name the members it removes from the muster"
    )
    printed = " ".join(str(rule.get("effect") or "").split())
    assert "do not count towards the need to take a Rout test" in printed

    # The recipient set is the published half; the meaning is curated once in the
    # generator, keyed by the band that owns the band-local rule id.
    generator = (ROOT / "tools" / "knowledge" / "generate_knowledge_web.py").read_text(encoding="utf-8")
    assert f'("{PATROL}", "{ROUT_RULE}")' in generator, (
        "the Rout-test exemption must be curated in the generator, keyed by band and rule"
    )

    artefact = _artefact()
    exempt = [
        str(profile["id"])
        for profile in artefact["profiles"]
        if profile.get("rout_test_exempt") is True
    ]
    assert exempt == ["raw-recruits"], f"unexpected Rout-test exemptions: {exempt}"
    patrol = next(row for row in artefact["profiles"] if str(row["id"]) == "raw-recruits")
    assert patrol["band_id"] == PATROL


def test_repeater_pistol_market_scope_is_published_and_stays_out_of_construction():
    canonical = _campaign("trading-post")
    entry = next(
        (row for row in canonical["items"] if str(row.get("item_id")) == "repeater_pistol_moh"),
        None,
    )
    assert entry is not None, "the Trading Post must publish the Masters of Horror variant"
    assert entry["availability"] == {"kind": "common"}
    assert entry["price"] == {
        "base_gc": 25,
        "optional_variable_cost": {"dice": {"count": 3, "sides": 6}},
    }
    scoped = [
        row for row in entry.get("restrictions") or ()
        if row.get("type") == "condition" and row.get("band_ids")
    ]
    assert len(scoped) == 1, "the printed clause must carry its band scope as data"
    assert scoped[0]["band_ids"] == [MASTERS]
    assert "Masters of Horror only" in str(scoped[0]["note"])

    # The band exists and the item is not offered by any construction list: the
    # obligation is market availability, never construction.
    assert _band(MASTERS)
    offered = {
        str(item.get("item_id"))
        for band in load_bands(COLLECTION, KB)
        for list_ in band.equipment_lists
        for item in list_.get("items") or ()
    }
    assert "repeater_pistol_moh" not in offered

    # The staging tree the promotion reads carries the same scope, so promoting
    # to the canonical KB stays a no-op.
    staging = read_yaml(STAGING / "2A" / "catalog" / "trading-post-2a.yaml")
    staged = next(
        (row for row in staging["items"] if str(row.get("item_id")) == "repeater_pistol_moh"),
        None,
    )
    assert staged is not None, "the staging tree must still publish the entry"
    assert any(
        row.get("type") == "condition" and row.get("band_ids") == [MASTERS]
        for row in staged.get("restrictions") or ()
    ), "the staging mirror must carry the structured scope"


def test_unique_plate_mail_is_not_sold_and_reaches_the_warband_by_item_id():
    canonical = _campaign("trading-post")
    entry = next(
        (row for row in canonical["items"] if str(row.get("item_id")) == "runic_attlas_plate_mail"),
        None,
    )
    assert entry is not None
    assert entry["availability"] == {"kind": "not_sold"}
    assert entry["price"] is None

    items = {str(row.get("id")): row for row in load_items(COLLECTION, KB)}
    item = items["runic_attlas_plate_mail"]
    assert item["name"] == ARTEFACT_NAME
    assert item["kind"] == "armour"

    catalogue = _campaign("exploration-and-income")
    results = (catalogue.get("magical_artefacts") or {}).get("results") or ()
    row = next(
        (entry for entry in results if str(entry.get("id")) == "campaign.magical-artefact.attlas-plate-mail"),
        None,
    )
    assert row is not None, "the magical-artefact chart must publish the find"
    assert row["roll"] == "3"
    assert row["result"] == item["name"], "the chart row and the item must be the same artefact"
    assert row["item_id"] == "runic_attlas_plate_mail", (
        "the chart must publish the canonical item id so the find is granted as the catalogue item"
    )


CATHAY = "pirates-of-the-cathayan-sea-sar"
SLAYER = "dwarf-slayer-cult-web"
SHALLOWS = "shallows-beasts-mim"


def test_succession_clause_publishes_the_leader_and_the_successors():
    catalogue = _campaign("recruitment-and-veterans")
    entry = next(
        (row for row in catalogue.get("succession_clauses") or () if row.get("rule_id") == "band--succession"),
        None,
    )
    assert entry is not None, "the printed succession rule must be published as data"
    assert entry["band_id"] == CATHAY
    assert entry["leader_profile_ids"] == ["disgraced-warlord"]
    assert entry["successor_profile_ids"] == ["shanghaires"]

    band = _band(CATHAY)
    rule = _rule(band, "band--succession")
    printed = " ".join(str(rule.get("effect") or "").split())
    assert "Shanghai'ers" in printed
    profiles = {str(row.get("id")) for row in band.profiles}
    assert {"disgraced-warlord", "shanghaires"} <= profiles, (
        "the published leader and successor profiles must exist in the band"
    )
    # The leader profile is the one that carries the band's printed Leader rule.
    leader_rules = [
        str(row.get("id"))
        for row in band.special_rules
        if (row.get("applies_to") or {}).get("profile_ids") == ["disgraced-warlord"]
        and str(row.get("id", "")).endswith("--leader")
    ]
    assert leader_rules, "the published leader profile must carry the band's Leader rule"


def test_born_marksmen_publishes_the_granted_skill_list():
    catalogue = _campaign("recruitment-and-veterans")
    entry = next(
        (row for row in catalogue.get("advance_access_clauses") or () if row.get("rule_id") == "axe-hurlers--born-marksmen"),
        None,
    )
    assert entry is not None, "the printed grant must be published as data"
    assert entry["band_id"] == SLAYER
    assert entry["trigger"] == "that-lads-got-talent"
    assert entry["profile_ids"] == ["axe-hurlers"]
    assert entry["skill_lists"] == ["shooting"]

    rule = _rule(_band(SLAYER), "axe-hurlers--born-marksmen")
    assert (rule.get("applies_to") or {}).get("profile_ids") == ["axe-hurlers"]
    printed = " ".join(str(rule.get("effect") or "").split())
    assert "Shooting skills" in printed


def test_mutation_grant_publishes_priced_ids_and_names_the_unpriced_ones():
    catalogue = _campaign("mutations")
    entry = next(
        (row for row in catalogue.get("grant_rules") or () if row.get("rule_id") == "band--aquatic-mutants"),
        None,
    )
    assert entry is not None, "the printed mutation grant must be published as data"
    assert entry["band_id"] == SHALLOWS
    assert entry["recipients"] == "hero"
    assert entry["limit_per_warrior"] == 1
    assert entry["mutation_ids"] == [
        "campaign.mutation.blackblood",
        "campaign.mutation.great-claw",
        "campaign.mutation.tentacle",
    ]
    priced = {str(row["id"]) for row in catalogue["mutations"]}
    assert set(entry["mutation_ids"]) <= priced, "every granted id must be priced in the catalogue"
    # The printed names the catalogue does not price are transcribed, never invented.
    printed = " ".join(str(_rule(_band(SHALLOWS), "band--aquatic-mutants").get("effect") or "").split())
    for name in entry["unrouted_mutation_names"]:
        assert name in printed, name
    assert not any("prehensile" in str(row["id"]) or "mer-creature" in str(row["id"]) for row in catalogue["mutations"])
    assert catalogue["rules"]["purchase"]["timing"] == "at_recruitment_only"
    assert catalogue["rules"]["purchase"]["pricing"] == {
        "first_mutation": "listed_price",
        "second_and_subsequent": "double_listed_price",
    }


def test_withdrawal_rules_name_the_members_that_leave_the_table():
    cases = (
        ("bretonnian-buccaneers-sar", "swabbies--blimey-they-got-away", "swabbies"),
        (CATHAY, "floordogs--wo-kao-they-got-away", "floordogs"),
    )
    for band_id, rule_id, profile in cases:
        rule = _rule(_band(band_id), rule_id)
        assert (rule.get("applies_to") or {}).get("profile_ids") == [profile]
        printed = " ".join(str(rule.get("effect") or "").split())
        assert "Remove them from your warband roster as if they had been killed" in printed


def test_artefact_carries_the_new_campaign_sections():
    artefact = _artefact()
    recruitment = artefact["campaign"]["recruitment-and-veterans"]
    assert recruitment["succession_clauses"][0]["rule_id"] == "band--succession"
    assert recruitment["advance_access_clauses"][0]["rule_id"] == "axe-hurlers--born-marksmen"
    assert artefact["campaign"]["mutations"]["grant_rules"][0]["rule_id"] == "band--aquatic-mutants"


def test_campaign_catalogue_schemas_publish_the_new_fields():
    recruitment = json.loads(
        (CONTRACTS / "campaign-recruitment-and-veterans.yaml.schema.json").read_text(encoding="utf-8")
    )
    assert "creation_decisions" in recruitment["properties"]
    assert "creation_decision" in recruitment["$defs"]
    outcome = recruitment["$defs"]["creation_outcome"]
    assert outcome["additionalProperties"] is False
    assert set(outcome["required"]) == {"when", "result_id", "result", "result_i18n"}

    exploration = json.loads(
        (CONTRACTS / "campaign-exploration-and-income.yaml.schema.json").read_text(encoding="utf-8")
    )
    results = exploration["$defs"]["magical_artefacts"]["properties"]["results"]["items"]
    assert "item_id" in results["properties"], (
        "the chart row must be able to publish the canonical item id"
    )
    assert results["additionalProperties"] is False

    trading = json.loads(
        (CONTRACTS / "campaign-trading-post.yaml.schema.json").read_text(encoding="utf-8")
    )
    restriction = trading["$defs"]["restriction"]
    assert "band_ids" in restriction["properties"]
    assert "groups" in restriction["properties"]

    # T10 second pass: succession, advancement access and mutation grants.
    assert "succession_clauses" in recruitment["properties"]
    assert "advance_access_clauses" in recruitment["properties"]
    assert "succession_clause" in recruitment["$defs"]
    assert "advance_access_clause" in recruitment["$defs"]
    mutations = json.loads(
        (CONTRACTS / "campaign-mutations.yaml.schema.json").read_text(encoding="utf-8")
    )
    assert "grant_rules" in mutations["properties"]
    assert "grant_rule" in mutations["$defs"]
