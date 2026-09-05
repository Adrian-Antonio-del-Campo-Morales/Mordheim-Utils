"""knowledge.campaign-catalogs: state and integrity of the campaign catalogues.

Verifies the declarative ingestion of post-battle and campaign rules in
``sources/knowledge/catalog/campaign``: headers, absence of fictitious
examples, canonical counts, reference resolution (items, warbands, groups,
conditions, skills, wizard profiles) and table invariants.

The KB declares rules and tables, never their outcome. These tests only
validate that the data is correctly ingested and referenced; the runtime
read path and its load-time validation live in ``mordheim_knowledge/campaign.py``
(``load_campaign_catalog``, ``load_post_battle_sequence``, ``load_hirelings``,
``load_warband_groups``), covered by ``tests/knowledge/test_campaign_loaders.py``.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import re
import yaml

ROOT = Path(__file__).resolve().parents[2] / "sources/knowledge"
CAMPAIGN = ROOT / "catalog" / "campaign"
ITEMS = ROOT / "catalog" / "items"
SKILLS = ROOT / "catalog" / "skills"
BANDS = ROOT / "bands"
HIRELINGS = ROOT / "catalog" / "hirelings"


def load(rel_path: str) -> dict:
    return yaml.safe_load((ROOT / rel_path).read_text(encoding="utf-8"))


def campaign(name: str) -> dict:
    return yaml.safe_load((CAMPAIGN / name).read_text(encoding="utf-8"))


def campaign_files() -> list[Path]:
    return sorted(CAMPAIGN.glob("*.yaml"))


def collect(node, key: str) -> list:
    """All values of ``key`` in a YAML tree (lists included)."""
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


def canonical_item_ids() -> set[str]:
    ids = []
    for path in ITEMS.glob("*.yaml"):
        ids.extend(item["id"] for item in load(f"catalog/items/{path.name}").get("items", []))
    return set(ids)


def canonical_skill_ids() -> set[str]:
    ids = []
    for path in SKILLS.glob("*.yaml"):
        ids.extend(skill["id"] for skill in load(f"catalog/skills/{path.name}").get("skills", []))
    return set(ids)


def band_profile_ids() -> dict[str, set[str]]:
    """band dir name -> ids of the warband profiles (both collections)."""
    profiles: dict[str, set[str]] = {}
    for band_yaml in BANDS.glob("*/*/band.yaml"):
        band_dir = band_yaml.parent
        profiles[band_dir.name] = {p["id"] for p in yaml.safe_load(
            (band_dir / "profiles.yaml").read_text(encoding="utf-8")).get("profiles", [])}
    return profiles


def hireling_profile_ids() -> set[str]:
    ids = []
    for path in HIRELINGS.glob("**/*.yaml"):
        ids.extend(p["id"] for p in yaml.safe_load(path.read_text(encoding="utf-8")).get("profiles", []))
    return set(ids)


# --------------------------------------------------------------------------
# Headers, ingestion state and absence of fictitious examples
# --------------------------------------------------------------------------

def test_campaign_catalogs_have_headers_and_declare_status():
    for path in campaign_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert document.get("schema_version") in (1, 2), path.name
        assert document.get("ruleset") == "mordheim", path.name
        assert document.get("status") in ("published", "draft"), path.name
        assert document.get("catalog") == f"campaign-{path.stem}", path.name


def test_campaign_catalogs_all_published_and_hired_swords_is_schema_v2():
    statuses = {path.stem: yaml.safe_load(path.read_text(encoding="utf-8")).get("status")
                for path in campaign_files()}
    published = [name for name, status in statuses.items() if status == "published"]
    drafts = [name for name, status in statuses.items() if status == "draft"]
    assert len(published) == 12
    assert drafts == []
    # hired-swords-and-dramatis uses schema v2 (availability resources and
    # procedures); the rest of the campaign catalogues stay on v1.
    assert campaign("hired-swords-and-dramatis.yaml").get("schema_version") == 2


def test_ingested_catalogs_removed_fictitious_examples():
    for path in campaign_files():
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert "examples" not in document, f"{path.name} still carries fictitious examples"


# --------------------------------------------------------------------------
# Canonical conditions
# --------------------------------------------------------------------------

def test_conditions_catalog_is_canonical():
    conditions = load("catalog/rules/conditions.yaml").get("conditions", [])
    assert {c["id"] for c in conditions} == {
        # Effects of campaign serious injuries.
        "campaign.condition.frenzy",
        "campaign.condition.stupidity",
        "campaign.condition.cannot-run",
        "campaign.condition.immune-to-fear",
        "campaign.condition.causes-fear",
        # Canonical psychology conditions of the rulebook.
        "condition.fear",
        "condition.terror",
        "condition.hatred",
        "condition.stubborn",
        "condition.animosity",
        "condition.immune-to-psychology",
        "condition.cold-blooded",
    }
    assert all(c.get("name") for c in conditions)
    assert all(c.get("summary") for c in conditions)
    assert all(c.get("source_refs") for c in conditions)
    assert len({c["id"] for c in conditions}) == len(conditions)


# --------------------------------------------------------------------------
# Trading Post
# --------------------------------------------------------------------------

def test_trading_post_ingestion_state():
    items = campaign("trading-post.yaml")["items"]
    entry_ids = [item["id"] for item in items]
    assert len(items) == 338
    assert len(entry_ids) == len(set(entry_ids))
    assert all(item_id.startswith("campaign.trading-post.") for item_id in entry_ids)
    kinds = Counter(item["availability"]["kind"] for item in items)
    assert dict(kinds) == {"common": 77, "rare": 183, "not_sold": 78}


def test_trading_post_price_and_availability_shapes():
    items = campaign("trading-post.yaml")["items"]
    no_price = sorted(item["id"] for item in items if item.get("price") is None)
    # Four source entries with cost "—" (bec-de-corbin, fist, firepots,
    # masterwork heavy armour) and 78 items the Mordheim Trading Post does not
    # sell (only warband equipment lists).
    assert len(no_price) == 82
    source_no_price = {
        "campaign.trading-post.bec-de-corbin",
        "campaign.trading-post.firepots-miragliano",
        "campaign.trading-post.fist",
        "campaign.trading-post.masterwork-heavy-armour",
    }
    not_sold = [item for item in items if item["availability"]["kind"] == "not_sold"]
    assert len(not_sold) == 78
    assert {item["id"] for item in not_sold} == set(no_price) - source_no_price
    for item in not_sold:
        assert item.get("price") is None, item["id"]
        assert item["restrictions"], item["id"]
    for item in items:
        availability = item["availability"]
        assert availability["kind"] in ("common", "rare", "not_sold")
        if availability["kind"] == "rare":
            assert isinstance(availability["rarity"], int), item["id"]
        if availability["kind"] == "not_sold":
            assert "rarity" not in availability, item["id"]
        price = item.get("price")
        if price is not None:
            assert "base_gc" in price or "multiplier" in price, item["id"]
            if "base_gc" in price:
                assert isinstance(price["base_gc"], int)
            variable = price.get("optional_variable_cost")
            if variable is not None:
                assert "dice" in variable, item["id"]


def test_trading_post_canonical_prices():
    by_id = {item["item_id"]: item for item in campaign("trading-post.yaml")["items"]}
    assert by_id["sword"]["price"]["base_gc"] == 10
    assert by_id["sword"]["availability"] == {"kind": "common"}
    assert by_id["dagger"]["price"]["base_gc"] == 2
    assert by_id["dagger"]["availability"] == {"kind": "common"}
    mordheim_map = by_id["mordheim_map"]
    assert mordheim_map["price"]["base_gc"] == 20
    assert mordheim_map["price"]["optional_variable_cost"]["dice"] == {"count": 4, "sides": 6}
    assert mordheim_map["availability"] == {"kind": "rare", "rarity": 9}


def test_trading_post_restricted_variants_share_item_id_deliberately():
    items = campaign("trading-post.yaml")["items"]
    by_item_id: dict[str, list[dict]] = {}
    for item in items:
        by_item_id.setdefault(item["item_id"], []).append(item)
    repeats = {item_id: entries for item_id, entries in by_item_id.items() if len(entries) > 1}
    assert set(repeats) == {"obsidian_weapon", "pike", "double_barrelled_pistol"}
    for item_id, entries in repeats.items():
        assert len({entry["id"] for entry in entries}) == len(entries)
        # Restricted variants: distinct price and/or rarity in each entry.
        assert len({(entry["price"].get("base_gc"), entry["price"].get("multiplier"),
                     entry["availability"].get("rarity")) for entry in entries}) > 1, item_id


# --------------------------------------------------------------------------
# Serious injuries
# --------------------------------------------------------------------------

def test_serious_injuries_tables_state():
    tables = {t["id"]: t for t in campaign("serious-injuries.yaml")["tables"]}
    assert set(tables) == {"campaign.serious-injuries.hero", "campaign.serious-injuries.henchman"}
    hero = tables["campaign.serious-injuries.hero"]
    assert hero["applies_to"] == "hero"
    assert hero["dice"] == {"count": 2, "sides": 6}
    assert hero["resolution"] == "d66"
    hero_rolls = [str(r["roll"]) for r in hero["results"]]
    assert hero_rolls == ["11-15", "16-21", "22", "23", "24", "25", "26", "31", "32",
                          "33", "34", "35", "36", "41-55", "56", "61", "62-63", "64", "65", "66"]
    henchman = tables["campaign.serious-injuries.henchman"]
    assert henchman["applies_to"] == "henchman"
    assert henchman["dice"] == {"count": 1, "sides": 6}
    assert henchman["resolution"] == "d6"
    assert [str(r["roll"]) for r in henchman["results"]] == ["1-2", "3-6"]


def test_serious_injuries_canonical_outcomes():
    hero = next(t for t in campaign("serious-injuries.yaml")["tables"] if t["id"].endswith(".hero"))
    by_roll = {str(r["roll"]): r for r in hero["results"]}
    assert by_roll["11-15"]["result"] == "Dead"
    assert by_roll["11-15"]["effects"][0]["type"] == "roster.remove_warrior"
    assert by_roll["11-15"]["effects"][0]["reason"] == "dead"
    assert by_roll["41-55"]["result"] == "Full Recovery"
    assert by_roll["66"]["result"] == "Survives Against The Odds"
    effects_66 = by_roll["66"]["effects"]
    assert effects_66[0]["type"] == "reward.grant"
    assert effects_66[0]["resources"]["experience"] == {"kind": "fixed", "value": 1}
    multiple = by_roll["16-21"]["resolution"]
    assert multiple["type"] == "repeat_table"
    assert multiple["table_id"] == "campaign.serious-injuries.hero"
    result_ids = {r["id"] for r in hero["results"]}
    assert set(multiple["reroll_ids"]) <= result_ids


def test_serious_injuries_conditions_land_on_canonical_rolls():
    hero = next(t for t in campaign("serious-injuries.yaml")["tables"] if t["id"].endswith(".hero"))
    roll_conditions: dict[str, set[str]] = {}
    for row in hero["results"]:
        roll = str(row["roll"])
        roll_conditions[roll] = {c for c in collect(row, "condition_id") if isinstance(c, str)}
    assert roll_conditions["24"] == {"campaign.condition.frenzy", "campaign.condition.stupidity"}
    assert roll_conditions["25"] == {"campaign.condition.cannot-run"}
    assert roll_conditions["62-63"] == {"campaign.condition.immune-to-fear"}
    assert roll_conditions["64"] == {"campaign.condition.causes-fear"}
    used = {condition for conditions in roll_conditions.values() for condition in conditions}
    assert used == {"campaign.condition.frenzy", "campaign.condition.stupidity",
                    "campaign.condition.cannot-run", "campaign.condition.immune-to-fear",
                    "campaign.condition.causes-fear"}


# --------------------------------------------------------------------------
# Experience and advances
# --------------------------------------------------------------------------

def test_experience_awards_and_underdog_state():
    document = campaign("experience-and-advances.yaml")
    assert [award["id"] for award in document["awards"]] == [
        "campaign.experience.award.survives",
        "campaign.experience.award.winning-leader",
        "campaign.experience.award.per-enemy-out-of-action",
    ]
    assert document["underdog_bonus"]["id"] == "campaign.experience.underdog-bonus"
    assert len(document["underdog_bonus"]["bands"]) == 6


def test_advance_tables_cover_2_to_12_without_gaps():
    tables = {t["id"]: t for t in campaign("experience-and-advances.yaml")["advancement_tables"]}
    assert set(tables) == {"campaign.advance.hero", "campaign.advance.henchman"}
    expected = {
        "campaign.advance.hero": [(2, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 12)],
        "campaign.advance.henchman": [(2, 4), (5, 5), (6, 7), (8, 8), (9, 9), (10, 12)],
    }
    for table_id, table in tables.items():
        assert table["resolution"]["dice"] == {"count": 2, "sides": 6}
        branches = [(b["when"]["min"], b["when"]["max"]) for b in table["resolution"]["branches"]]
        assert branches == expected[table_id], table_id
        covered = [value for low, high in branches for value in range(low, high + 1)]
        assert sorted(covered) == list(range(2, 13)), table_id
        for branch in table["resolution"]["branches"]:
            assert branch["result"]["type"], table_id


def test_racial_maximums_live_in_the_shared_catalog():
    # Single source of truth: catalog/rules/racial-maximums.yaml. The campaign
    # catalogue does not duplicate the block (`limits` must not reappear there).
    assert "limits" not in campaign("experience-and-advances.yaml")
    limits = load("catalog/rules/racial-maximums.yaml")["racial_maximums"]
    assert len(limits) == 29
    assert len({limit["id"] for limit in limits}) == 29
    assert len({limit["profile"] for limit in limits}) == 29
    expected_characteristics = {
        "movement", "weapon_skill", "ballistic_skill", "strength", "toughness",
        "wounds", "initiative", "attacks", "leadership",
    }
    for limit in limits:
        assert limit["id"].startswith("campaign.limit.racial-maximum.")
        assert limit["applies_to"] == "profile"
        assert set(limit["characteristics"]) == expected_characteristics
        assert limit["source_refs"]


def test_racial_maximum_values_match_band_rules_that_used_to_inline_them():
    # Canonical values fixed by the source (mordheimer.net /docs/campaigns/experience);
    # warband rules reference these ids instead of inlining statlines.
    by_profile = {limit["profile"]: limit["characteristics"]
                  for limit in load("catalog/rules/racial-maximums.yaml")["racial_maximums"]}
    checks = {
        "human": dict(movement=4, weapon_skill=6, ballistic_skill=6, strength=4,
                       toughness=4, wounds=3, initiative=6, attacks=4, leadership=9),
        "elf": dict(movement=5, weapon_skill=7, ballistic_skill=7, leadership=10),
        "dwarf": dict(movement=3, weapon_skill=7, toughness=5, leadership=10),
        "ogre": dict(strength=5, wounds=5, attacks=5),
        "skaven": dict(movement=6, initiative=7, leadership=7),
        "skaven_clan_pestilens": dict(movement=5, toughness=5),
        "vampire": dict(strength=7, toughness=6, wounds=4, leadership=10),
        "ghoul": dict(ballistic_skill=2, toughness=5, attacks=5, leadership=7),
        "goblin": dict(weapon_skill=5, ballistic_skill=6, leadership=7),
        "tomb_lord": dict(strength=5, wounds=5, leadership=9),
        "liche_restless_dead": dict(wounds=8, attacks=3, leadership=10),
        "grave_guard": dict(leadership=10),
        "bull_centaur_black_dwarfs": dict(movement=8, attacks=5, leadership=10),
        "bull_centaur_sons_of_hashut": dict(movement=7, initiative=4),
        "marauder_of_chaos": dict(weapon_skill=7, ballistic_skill=7),
        "warrior_of_chaos": dict(weapon_skill=8, ballistic_skill=8, attacks=5),
    }
    for profile, expected in checks.items():
        assert profile in by_profile, profile
        for key, value in expected.items():
            assert by_profile[profile][key] == value, f"{profile}.{key}"


def test_band_rules_reference_racial_maximums_without_inlining_statlines():
    # Warband rules do not inline racial-maximum statlines: they reference the
    # canonical entries (campaign.limit.racial-maximum.*) and every mention of
    # "maximum profile" must resolve against the shared catalogue.
    maximum_ids = {limit["id"]
                   for limit in load("catalog/rules/racial-maximums.yaml")["racial_maximums"]}
    profile_mention = re.compile(r"maximum (?:characteristic )?profiles?\b", re.IGNORECASE)
    statline = re.compile(r"\bM\d+\s*,?\s+WS\d")
    referenced: list[str] = []
    rules_with_maximums = 0
    for path in sorted(BANDS.glob("**/special-rules.yaml")):
        rules = yaml.safe_load(path.read_text(encoding="utf-8")).get("rules", [])
        for rule in rules:
            texts = [rule.get("effect") or ""]
            i18n = rule.get("effect_i18n") or {}
            if isinstance(i18n, dict):
                texts.append(i18n.get("en") or "")
            text = "\n".join(texts)
            if "maximum" not in text.lower():
                continue
            rules_with_maximums += 1
            # The numeric statline is declared once: in the shared catalogue.
            assert not statline.search(text), f"{path.name}: {rule['id']} inlines a statline"
            if profile_mention.search(text):
                refs = re.findall(r"campaign\.limit\.racial-maximum\.[a-z0-9-]+", text)
                assert refs, f"{path.name}: {rule['id']} mentions a max profile without ref"
                referenced.extend(refs)
    assert rules_with_maximums >= 20  # 81 files, ~20 rules mention maximums
    assert referenced, "expected racial-maximum references from the warbands"
    assert set(referenced) <= maximum_ids


# --------------------------------------------------------------------------
# Exploration and income
# --------------------------------------------------------------------------

def test_exploration_dice_and_shards_chart():
    exploration = campaign("exploration-and-income.yaml")["exploration"]
    assert [row["id"] for row in exploration["dice_allocation"]] == [
        "campaign.exploration.dice.per-surviving-hero",
        "campaign.exploration.dice.bonus-if-won",
    ]
    assert exploration["max_dice"] == 6
    cells = exploration["shards_chart"]["cells"]
    assert len(cells) == 7
    for cell in cells:
        dice_total = cell["when"]["dice_total"]
        if isinstance(dice_total, dict):
            assert "max" not in dice_total or dice_total["min"] <= dice_total["max"]
        else:
            assert isinstance(dice_total, int)
        assert isinstance(cell["shards"], int)


def test_exploration_results_chart_is_ingested():
    results = campaign("exploration-and-income.yaml")["exploration"]["results"]
    assert len(results) == 30
    assert len({row["id"] for row in results}) == 30
    for row in results:
        assert row["id"].startswith("campaign.exploration.result.")
        assert isinstance(row["dice_pattern"], str)
        assert row["outcome"]
        assert row["follow_up"]


def test_wyrdstone_sale_and_magical_artefacts_state():
    document = campaign("exploration-and-income.yaml")
    sale = document["income"]["wyrdstone_sale"]
    assert [input_["id"] for input_ in sale["inputs"]] == ["fragments_sold", "warband_size"]
    assert len(sale["cells"]) == 48
    artefacts = document["magical_artefacts"]["results"]
    assert [artefact["roll"] for artefact in artefacts] == ["1", "2", "3", "4", "5", "6"]
    assert all(artefact["summary"] for artefact in artefacts)


# --------------------------------------------------------------------------
# Recruitment, veterans, rating and rarity
# --------------------------------------------------------------------------

def test_recruitment_and_veterans_state():
    document = campaign("recruitment-and-veterans.yaml")
    assert [policy["id"] for policy in document["recruitment_policy"]] == [
        "campaign.recruitment.free-dagger",
        "campaign.recruitment.common-items-only-for-recruits",
        "campaign.recruitment.henchmen-armed-like-group",
    ]
    availability = document["veteran_availability"]
    assert len(availability) == 1
    entry = availability[0]
    assert entry["id"] == "campaign.veterans.availability"
    assert entry["roll"]["dice"] == {"count": 2, "sides": 6}
    assert entry["experience_pool"]["source"] == "roll_total"
    assert entry["incremental_cost"] == {"per_experience_point_gc": 2}


def test_warband_rating_formula_state():
    formula = campaign("warband-rating.yaml")["formula"]
    assert [component["id"] for component in formula["components"]] == [
        "campaign.warband-rating.per-warrior",
        "campaign.warband-rating.experience",
        "campaign.warband-rating.large-creature",
    ]
    assert isinstance(formula["exclusions"], list)


def test_trading_and_rarity_state():
    document = campaign("trading-and-rarity.yaml")
    tests = document["rarity"]["tests"]
    assert [test["id"] for test in tests] == ["campaign.trading.rarity-test"]
    assert tests[0]["dice"] == {"count": 2, "sides": 6}
    assert tests[0]["success_when"] == "greater_than_or_equal_to_target"
    assert document["rarity"]["market_catalog"] == "trading-post.yaml"
    assert [rule["id"] for rule in document["equipment_allocation"]["rules"]] == [
        "campaign.equipment.sell-at-half-price",
        "campaign.equipment.hoard-in-stash",
        "campaign.equipment.reallocate",
        "campaign.equipment.lost-on-death",
    ]


def test_post_battle_sequence_has_ten_steps():
    sequence = campaign("post-battle-sequence.yaml")["sequence"]
    assert sequence["id"] == "campaign.post-battle"
    assert [step["id"] for step in sequence["steps"]] == [
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
    ]


# --------------------------------------------------------------------------
# Scenarios
# --------------------------------------------------------------------------

def test_scenarios_state_and_selection_tables():
    document = campaign("scenarios.yaml")
    scenarios = document["scenarios"]
    scenario_ids = [scenario["id"] for scenario in scenarios]
    assert len(scenario_ids) == 98
    assert len(set(scenario_ids)) == 98
    assert all(scenario_id.startswith("scenario.") for scenario_id in scenario_ids)
    assert all(scenario.get("name") for scenario in scenarios)


def test_scenario_selection_references_resolve():
    document = campaign("scenarios.yaml")
    scenario_ids = {scenario["id"] for scenario in document["scenarios"]}
    referenced = set()
    for table in document["selection_tables"]:
        rows = table["rows"]
        assert rows
        for row in rows:
            assert "when" in row and row["when"]["min"] <= row["when"]["max"]
            if "scenario" in row:
                referenced.add(row["scenario"])
    assert referenced <= scenario_ids
    assert len(referenced) == 16
    assert {table["id"] for table in document["selection_tables"]} == {
        "campaign.scenario-table.rulebook",
        "campaign.scenario-table.chaos-on-the-streets",
    }


def test_scenario_progression_ingested_for_selection_table_scenarios():
    """The 16 scenarios of the official selection tables have progression."""
    document = campaign("scenarios.yaml")
    scenarios = {scenario["id"]: scenario for scenario in document["scenarios"]}
    referenced = {row["scenario"] for table in document["selection_tables"]
                   for row in table["rows"] if "scenario" in row}
    assert len(referenced) == 16
    for scenario_id in referenced:
        assert scenario_id in scenarios
        progression = scenarios[scenario_id].get("progression")
        assert progression, f"{scenario_id} needs progression data"
        assert progression.get("experience"), f"{scenario_id} needs experience awards"


def test_scenario_progression_shape_and_reference_integrity():
    document = campaign("scenarios.yaml")
    scenarios = document["scenarios"]
    with_progression = [scenario for scenario in scenarios if "progression" in scenario]
    # Full coverage: all 98 scenarios of the catalogue have progression data
    # transcribed from their individual source pages.
    assert len(with_progression) == 98
    xp_award_ids = {award["id"] for award in campaign("experience-and-advances.yaml")["awards"]}
    trading_post = campaign("trading-post.yaml")
    tp_item_ids = {row.get("item_id") for row in trading_post["items"] if row.get("item_id")}
    hub_url = "https://mordheimer.net/docs/campaigns/scenarios"
    for scenario in with_progression:
        progression = scenario["progression"]
        # Individual page URL, not the index.
        url = scenario["source_refs"][0]["url"]
        assert url != hub_url and url.startswith(hub_url + "/"), scenario["id"]
        # Sources without explicit progression awards must document that
        # absence in notes (e.g. AP zombie-invasion scenarios).
        if "experience" not in progression:
            assert progression.get("notes"), \
                f"{scenario['id']}: progression without experience needs a note"
            continue
        experience = progression["experience"]
        assert experience
        for row in experience:
            assert bool(row.get("ref")) != bool(row.get("summary")), \
                f"{scenario['id']}: experience row needs ref XOR summary"
            if "ref" in row:
                assert row["ref"] in xp_award_ids, f"{scenario['id']}: unknown {row['ref']}"
            assert not ("amount" in row and "amount_dice" in row)
            if "amount" in row:
                assert isinstance(row["amount"], int) and row["amount"] > 0
        if "wyrdstone" in progression:
            assert isinstance(progression["wyrdstone"], str) and progression["wyrdstone"]
        if "income" in progression:
            assert isinstance(progression["income"], str) and progression["income"]
        if "loot" in progression:
            loot = progression["loot"]
            assert loot.get("summary"), f"{scenario['id']}: loot needs a summary"
            if "contents" in loot:
                assert loot["contents"]
                for content in loot["contents"]:
                    assert content.get("reward") and content.get("roll")
                    if "when" in content:
                        assert content["when"]["min"] <= content["when"]["max"]
                    if "item_id" in content:
                        assert content["item_id"] in tp_item_ids, \
                            f"{scenario['id']}: unknown item {content['item_id']}"
        if "notes" in progression:
            assert all(isinstance(note, str) and note for note in progression["notes"])


# --------------------------------------------------------------------------
# Magic
# --------------------------------------------------------------------------

def test_magic_assignment_table_covers_lores_and_pending_lores():
    document = campaign("magic.yaml")
    rows = document["lore_assignments"]["rows"]
    defined = {lore["id"] for lore in document["lores"]}
    pending = set(document["pending_lores"])
    used = {row["lore"] for row in rows}
    assert len(rows) == 45
    assert len(defined) == 31
    assert pending == set()
    assert defined.isdisjoint(pending)
    # Every assigned lore is defined and vice versa; nothing pending.
    assert used == defined | pending
    for row in rows:
        assert row["wizard"]
        assert row["profile_id"]
        assert row["lore"]
    # All contractable wizards (hired swords and dramatis personae) with spell
    # lists are linked to their canonical lore (Abdul knows two lists).
    hireling_rows = [row for row in rows if row["profile_id"].startswith("hireling.")]
    assert len(hireling_rows) == 15
    assert len({row["profile_id"] for row in hireling_rows}) == 14


def test_magic_lore_spell_lists_are_complete_per_roll():
    document = campaign("magic.yaml")
    spells = [spell for lore in document["lores"] for spell in lore.get("spells", [])]
    assert len(spells) == 188
    assert len({spell["id"] for spell in spells}) == 188
    # Documented source exceptions: rituals-of-hashut has a fixed ritual
    # (roll 0, the Sorcerer starts with it) and necromancy-restless-dead
    # shares roll 6 between Deathly Visage (Necromancer) and Living Horror (Liche).
    multi_roll = {
        "lore.rituals-of-hashut",
        "lore.necromancy-restless-dead",
    }
    for lore in document["lores"]:
        rolls = [spell["roll"] for spell in lore["spells"]]
        assert all(roll in rolls for roll in ("1", "2", "3", "4", "5", "6")), lore["id"]
        if lore["id"] not in multi_roll:
            assert sorted(rolls) == ["1", "2", "3", "4", "5", "6"], lore["id"]
        for spell in lore["spells"]:
            assert spell["name"]
            assert spell["summary"]
            difficulty = spell["difficulty"]
            assert isinstance(difficulty, int) or difficulty == "auto", spell["id"]
    assert sum(1 for spell in spells if spell["difficulty"] == "auto") == 6


def test_magic_profile_references_resolve():
    document = campaign("magic.yaml")
    band_profiles = band_profile_ids()
    hirelings = hireling_profile_ids()
    for row in document["lore_assignments"]["rows"]:
        band = row.get("band")
        profile_id = row["profile_id"]
        if band is None:
            assert profile_id in hirelings, row["wizard"]
        else:
            assert band in band_profiles, f"{row['wizard']}: unknown band {band}"
            assert profile_id in band_profiles[band], f"{row['wizard']}: {profile_id} not in {band}"


def test_casting_rules_are_declarative():
    casting = campaign("magic.yaml")["casting_rules"]
    assert casting["id"] == "campaign.magic.casting"
    assert casting["summary"]
    assert casting["starting_spells"]
    assert casting["source_refs"]


# --------------------------------------------------------------------------
# Mutations
# --------------------------------------------------------------------------

def test_mutations_ingestion_state():
    document = campaign("mutations.yaml")
    assert document["rules"]["purchase"]
    mutations = document["mutations"]
    assert len(mutations) == 9
    assert len({mutation["id"] for mutation in mutations}) == 9
    for mutation in mutations:
        assert mutation["id"].startswith("campaign.mutation.")
        assert mutation["name"]
        assert isinstance(mutation["cost_gc"], int)
        assert mutation["summary"]
        assert mutation["source_refs"]


# --------------------------------------------------------------------------
# Mercenaries (Hired Swords and Dramatis Personae) — schema v2
# --------------------------------------------------------------------------

def test_hired_swords_campaign_catalog_state():
    """The mercenary catalogue is published with schema v2 and its canonical
    counts: 72 Hired Swords + 26 Dramatis Personae = 98 unique entries."""
    document = campaign("hired-swords-and-dramatis.yaml")
    assert document["status"] == "published"
    assert document["schema_version"] == 2
    assert {entry["id"] for entry in document["hired_swords"]}
    assert len(document["hired_swords"]) == 72
    assert len(document["dramatis_personae"]) == 26
    entries = document["hired_swords"] + document["dramatis_personae"]
    assert len(entries) == 98
    assert len({entry["id"] for entry in entries}) == 98
    assert all(entry["id"].startswith("campaign.hireling.") for entry in entries)
    assert all(entry["profile_id"].startswith("hireling.") for entry in entries)
    # Every entry declares availability, a source reference and a canonical profile.
    assert all(entry.get("availability") for entry in entries)
    assert all(entry.get("source_refs") for entry in entries)
    # 4 Dramatis Personae were deliberately left out of scope (composite or
    # random profile), documented in CAMPAIGN INGESTION RESULTS.md.


def test_hired_swords_profile_ids_resolve_against_hirelings_catalog():
    document = campaign("hired-swords-and-dramatis.yaml")
    known = hireling_profile_ids()
    entries = document["hired_swords"] + document["dramatis_personae"]
    assert all(entry["profile_id"] in known for entry in entries)


def test_hired_swords_availability_and_cost_shapes():
    """Schema v2 shapes: availability procedures, allowed kinds and canonical
    cost resources (gold_crowns, wyrdstone_fragments, treasures,
    campaign_points)."""
    document = campaign("hired-swords-and-dramatis.yaml")
    procedures = {p["id"] for p in document["availability_procedures"]}
    assert procedures == {"campaign.hireling.availability.dramatis-search"}
    allowed_kinds = {"common", "construction", "hero_replacement",
                     "summoning", "special_scenario"}
    resources = set()
    entries = document["hired_swords"] + document["dramatis_personae"]
    for entry in entries:
        availability = entry["availability"]
        if "procedure_id" in availability:
            assert availability["procedure_id"] in procedures, entry["id"]
        else:
            assert availability["kind"] in allowed_kinds, entry["id"]
        for cost_key in ("hiring_fee", "upkeep"):
            cost = entry.get(cost_key)
            if cost is None:
                continue
            assert cost.get("resources"), f"{entry['id']}: {cost_key} without resources"
            resources.update(cost["resources"])
            assert all(v.get("cost") is not None for v in cost["resources"].values())
    assert resources <= {"gold_crowns", "wyrdstone_fragments", "treasures",
                         "campaign_points"}, resources


def test_hired_swords_eligibility_resolves_and_grammar_is_valid():
    """Eligibility: simple lists or a boolean expression; warbands and groups
    resolve against band.yaml and registry/warband-groups.yaml."""
    document = campaign("hired-swords-and-dramatis.yaml")
    band_ids = {yaml.safe_load(path.read_text(encoding="utf-8")).get("id")
                for path in BANDS.glob("*/*/band.yaml")}
    groups = {group["id"] for group in load("registry/warband-groups.yaml").get("groups", [])}
    entries = document["hired_swords"] + document["dramatis_personae"]
    leaf_keys = {"band_id", "group_id"}
    for entry in entries:
        eligibility = entry.get("eligibility") or {}
        if not eligibility:
            continue
        assert eligibility.keys() <= {"allow_groups", "forbid_groups",
                                      "allow_band_ids", "forbid_band_ids",
                                      "expression"}, entry["id"]
        for group in eligibility.get("allow_groups") or []:
            assert group in groups, f"{entry['id']}: unknown group {group}"
        for group in eligibility.get("forbid_groups") or []:
            assert group in groups, f"{entry['id']}: unknown group {group}"
        for band in eligibility.get("allow_band_ids") or []:
            assert band in band_ids, f"{entry['id']}: unknown band {band}"
        for band in eligibility.get("forbid_band_ids") or []:
            assert band in band_ids, f"{entry['id']}: unknown band {band}"
        expression = eligibility.get("expression")
        if expression is not None:
            check_expression(expression, leaf_keys, band_ids, groups, entry["id"])


def check_expression(node, leaf_keys, band_ids, groups, where):
    if isinstance(node, list):
        assert node, where
        for child in node:
            check_expression(child, leaf_keys, band_ids, groups, where)
        return
    assert isinstance(node, dict), where
    combinators = {"all_of", "any_of", "not"}
    leaves = {key for key in node if key in leaf_keys}
    used_combinators = {key for key in node if key in combinators}
    assert leaves or used_combinators, f"{where}: {node}"
    if "not" in node:
        check_expression(node["not"], leaf_keys, band_ids, groups, where)
    for combinator in ("all_of", "any_of"):
        if combinator in node:
            assert isinstance(node[combinator], list) and node[combinator], where
            for child in node[combinator]:
                check_expression(child, leaf_keys, band_ids, groups, where)
    if "band_id" in node:
        assert node["band_id"] in band_ids, f"{where}: unknown band {node['band_id']}"
    if "group_id" in node:
        assert node["group_id"] in groups, f"{where}: unknown group {node['group_id']}"


def test_hired_swords_dynamic_eligibility_rules_are_declared():
    """The 18 dynamic eligibility rules (roster-, mercenary-variant- or
    conditional-roll-dependent) are declared in catalog/hirelings; entries
    without static eligibility correspond exactly to that set."""
    document = campaign("hired-swords-and-dramatis.yaml")
    entries = document["hired_swords"] + document["dramatis_personae"]
    static_less = [entry["id"] for entry in entries if not entry.get("eligibility")]
    declared_rules = set()
    for path in HIRELINGS.glob("**/*.yaml"):
        parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
        for rule in parsed.get("rules", []) or []:
            rule_id = rule.get("id")
            if rule_id and rule_id.endswith(".rule.campaign-eligibility"):
                declared_rules.add(rule_id)
        for profile in parsed.get("profiles", []) or []:
            for rule_id in profile.get("rule_ids", []) or []:
                if rule_id.endswith(".rule.campaign-eligibility"):
                    declared_rules.add(rule_id)
            for rule in profile.get("rules", []) or []:
                if isinstance(rule, dict):
                    rule_id = rule.get("id")
                    if rule_id and rule_id.endswith(".rule.campaign-eligibility"):
                        declared_rules.add(rule_id)
    assert len(declared_rules) == 18
    # No static eligibility <-> declared dynamic rule for that profile.
    # The 18 dynamic rules depend on roster/variant/conditional roll; 6 of
    # them are the only eligibility path (no static list) and the remaining
    # 12 add conditions on top of a static base.
    static_less_profiles = {entry["id"].removeprefix("campaign.")
                            for entry in entries if not entry.get("eligibility")}
    rule_profiles = {".".join(rule_id.split(".")[:3]) for rule_id in declared_rules}
    assert static_less_profiles <= rule_profiles
    assert len(static_less) == 6


def test_hired_swords_goblin_lantern_bearer_is_unrestricted():
    """Documented ingestion decision: the Goblin Lantern Bearer can be hired
    by any warband (no static restriction)."""
    document = campaign("hired-swords-and-dramatis.yaml")
    entry = next(e for e in document["hired_swords"]
                 if e["id"].endswith("goblin-lantern-bearer"))
    eligibility = entry.get("eligibility") or {}
    assert not eligibility.get("allow_groups")
    assert not eligibility.get("forbid_groups")
    assert not eligibility.get("allow_band_ids")
    assert not eligibility.get("forbid_band_ids")
    assert "expression" not in eligibility


def test_hired_swords_no_pending_spell_list_references():
    """The 15 ``spell_list`` references of hired sword and dramatis personae
    profiles are linked to the canonical ``lore_id`` values of magic.yaml
    (lore_assignments.rows); none remains pending in
    ``unresolved_references``."""
    pending = []
    for path in sorted(HIRELINGS.glob("**/*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for profile in document.get("profiles", []):
            for ref in profile.get("unresolved_references") or []:
                if ref.get("kind") == "spell_list":
                    pending.append((path.name, profile["id"], ref.get("source_name")))
    assert pending == [], f"unlinked spell_list: {pending}"


# --------------------------------------------------------------------------
# Reference integrity of the campaign catalogues
# --------------------------------------------------------------------------

def test_campaign_references_resolve_against_canonical_catalogs():
    item_ids = canonical_item_ids()
    skill_ids = canonical_skill_ids()
    conditions = {c["id"] for c in load("catalog/rules/conditions.yaml").get("conditions", [])}
    # trading-post, magic and hired-swords are validated separately (own schema).
    excluded = {"trading-post.yaml", "magic.yaml", "hired-swords-and-dramatis.yaml"}
    for path in campaign_files():
        if path.name in excluded:
            continue
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        # Context variables ($var) belong to procedures, not ids.
        item_refs = [value for value in collect(document, "item_id")
                     if not (isinstance(value, str) and value.startswith("$"))]
        condition_refs = [value for value in collect(document, "condition_id")
                          if not (isinstance(value, str) and value.startswith("$"))]
        skill_refs = [value for value in collect(document, "skill_id")
                      if not (isinstance(value, str) and value.startswith("$"))]
        assert all(ref in item_ids for ref in item_refs), path.name
        assert all(ref in conditions for ref in condition_refs), path.name
        assert all(ref in skill_ids for ref in skill_refs), path.name


def test_trading_post_restrictions_resolve_against_bands_and_groups():
    items = campaign("trading-post.yaml")["items"]
    band_ids = {yaml.safe_load(path.read_text(encoding="utf-8")).get("id")
                for path in BANDS.glob("*/*/band.yaml")}
    groups = {group["id"] for group in load("registry/warband-groups.yaml").get("groups", [])}
    for item in items:
        for restriction in item.get("restrictions") or []:
            for group in restriction.get("groups") or []:
                assert group in groups, f"{item['id']}: unknown group {group}"
            for band in restriction.get("band_ids") or []:
                assert band in band_ids, f"{item['id']}: unknown band {band}"


def test_procedural_placeholders_stay_out_of_canonical_ids():
    # Context variables (prefix "$") are used only in procedures; the generic
    # validator must not treat them as canonical ids.
    document = campaign("trading-and-rarity.yaml")
    assert collect(document, "item_id") == ["$requested_item_id"]
    exploration = campaign("exploration-and-income.yaml")
    bindings = [value for value in collect(exploration, "bind") if isinstance(value, str)]
    assert bindings
    # Local procedure names are declared without "$" and referenced with "$"
    # (e.g. bind: searching_hero -> actor: $searching_hero); "leader" is a
    # literal procedure selector, not a variable.
    actors = [value for value in collect(exploration, "actor") if isinstance(value, str)]
    assert "$searching_hero" in actors
