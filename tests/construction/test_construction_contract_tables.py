"""Contract parity: the shared tables stay true to the promoted KB.

``packages/typescript/domain/campaign/construction-tables.json`` carries the two
facts the Web domain cannot derive from the generated artefact: the
``runtime-scope.yaml`` profile exclusions (with their reasons, verbatim) and the
KB rules that declare a binding while ``runtime.implemented != YES``.  This gate
projects both straight from ``sources/knowledge``, so the table cannot drift.

``construction-clauses.json`` holds the ``open_clauses`` whose KB record publishes no
executable construction shape (owner KB).  Every entry is resolved against the
promoted KB here, and their number is pinned so that absorbing a clause is a
deliberate edit instead of silent drift.  The retired T09 bookkeeping (transfers,
review matrix, reconciliation totals) is archived in
``docs/archive/construction-clauses-ledger-2026-11-12.json``; the clauses it recorded as
absorbed are pinned below so they keep publishing structure.

The gate only reads; regenerating the tables stays in ``build/cache/t09``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from mordheim_knowledge.loader import (
    load_bands,
    load_items,
    load_runtime_scope,
    read_yaml,
    runtime_bindings,
)

pytestmark = pytest.mark.evidence

ROOT = Path(__file__).resolve().parents[2]
KB = ROOT / "sources" / "knowledge"
DOMAIN = ROOT / "packages" / "typescript" / "domain" / "campaign"
TABLES = DOMAIN / "construction-tables.json"
CLAUSES = DOMAIN / "construction-clauses.json"
COLLECTION = "mordheim"
MECHANISMS = {
    "E01-profile-trait-binding",
    "E02-skill-access",
    "E03-selectable-skill",
    "E04-roster-composition",
    "E05-equipment-list",
    "E06-hiring-eligibility",
    "E07-characteristic-bounds",
}
OPEN_KEYS = {"rule_id", "band_id", "mechanism", "scope", "owner_task", "reason"}
TRANSFER_KEYS = {"effect_id", "owner", "mechanism", "to_task", "reason"}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _bands() -> dict[str, object]:
    return {str(band.band["id"]): band for band in load_bands(COLLECTION, KB)}


def _rule(bands: dict[str, object], band_id: str, rule_id: str) -> dict:
    band = bands.get(band_id)
    assert band is not None, f"table names an unknown band: {band_id}"
    rule = next((r for r in band.special_rules if str(r.get("id")) == rule_id), None)
    assert rule is not None, f"{band_id} declares no rule {rule_id}; the table is stale"
    return rule


def test_both_tables_declare_their_schema():
    tables = _load(TABLES)
    clauses = _load(CLAUSES)
    assert tables["schema_version"] == 1
    assert clauses["schema_version"] == 2
    assert {"profile_exclusions", "pending_bindings"} <= set(tables)
    assert set(clauses) == {"schema_version", "comment", "open_clauses"}


def test_runtime_scope_exclusions_are_a_verbatim_projection():
    declared = [
        (row["band_id"], row["profile_id"], row["reason"])
        for row in _load(TABLES)["profile_exclusions"]
    ]
    source = [
        (row["band_id"], row["profile_id"], row["reason"])
        for row in load_runtime_scope(COLLECTION, KB)["profile_exclusions"]
    ]
    assert declared, "the table must keep the declared runtime-scope exclusions"
    assert declared == source, (
        "construction-tables.json profile_exclusions must mirror "
        "sources/knowledge/registry/runtime-scope.yaml verbatim (band, profile, reason)"
    )


def test_every_excluded_profile_is_a_real_band_member():
    bands = _bands()
    for row in _load(TABLES)["profile_exclusions"]:
        band = bands.get(row["band_id"])
        assert band is not None, row["band_id"]
        profile_ids = {str(profile["id"]) for profile in band.profiles}
        assert row["profile_id"] in profile_ids, (
            f"{row['band_id']} publishes no profile {row['profile_id']}; the exclusion is stale"
        )


def test_pending_bindings_are_exactly_the_unimplemented_bindings():
    table = _load(TABLES)["pending_bindings"]
    declared = {(row["band_id"], row["rule_id"], row["binding_id"]) for row in table}
    assert len(declared) == len(table), "duplicate pending binding rows"

    bands = _bands()
    discovered = set()
    for band_id, band in bands.items():
        for rule in band.special_rules:
            runtime = rule.get("runtime") or {}
            if runtime.get("implemented") == "YES":
                continue
            for binding in runtime_bindings(rule, include_pending=True):
                discovered.add((band_id, str(rule.get("id")), str(binding.get("id"))))

    assert declared == discovered, (
        "pending_bindings must be every KB rule with a binding whose runtime.implemented "
        "is not YES: missing=%s extra=%s" % (sorted(discovered - declared), sorted(declared - discovered))
    )
    for row in table:
        assert row["owner_task"], "a pending binding needs an owning task"
        rule = _rule(bands, row["band_id"], row["rule_id"])
        recipients = (rule.get("applies_to") or {}).get("profile_ids") or ()
        assert row["profile_id"] in recipients, (
            f"{row['rule_id']} does not grant {row['profile_id']}; the transport row is wrong"
        )


def test_open_clauses_resolve_and_are_still_unstructured():
    clauses = _load(CLAUSES)["open_clauses"]
    bands = _bands()
    items = {str(row.get("id")): row for row in load_items(COLLECTION, KB)}
    for row in clauses:
        assert set(row) == OPEN_KEYS, row
        assert row["mechanism"] in MECHANISMS, row
        assert row["owner_task"] == "KB", row
        assert row["reason"].strip(), row
        if row["band_id"] == "":
            # Out-of-scope record (a mount, a Dramatis Personae kit): the KB marks
            # it out of scope, so the artefact carries no row construction could use.
            record = items.get(row["rule_id"])
            assert record is not None, f"{row['rule_id']} is not a KB item record"
            assert record.get("kind") == "out-of-scope", (
                f"{row['rule_id']} is now a {record.get('kind')} record; revisit the clause"
            )
            continue
        rule = _rule(bands, row["band_id"], row["rule_id"])
        runtime = rule.get("runtime") or {}
        if runtime.get("implemented") == "YES":
            # Implemented for another consumer.  Recipients alone do not close the
            # clause: `profile.skill-access` with only `parameters.category` grants
            # the whole category.  The printed member list in `parameters.skills`
            # is what makes the access placeable at construction.
            structured = bool((rule.get("applies_to") or {}).get("profile_ids")) and any(
                (effect.get("binding") or {}).get("id") == "profile.skill-access"
                and (effect.get("binding") or {}).get("parameters", {}).get("skills")
                for effect in runtime.get("effects") or ()
            )
            assert not structured, (
                f"{row['rule_id']} now publishes recipients and a member list; the clause can be structured"
            )
        else:
            assert runtime_bindings(rule) == (), (
                f"{row['rule_id']} is executable now; the clause belongs to the contract"
            )


def test_open_clauses_are_unique_per_band_and_rule():
    clauses = _load(CLAUSES)["open_clauses"]
    keys = [(row["rule_id"], row["band_id"]) for row in clauses]
    assert len(keys) == len(set(keys)), "an open clause is listed twice for the same band"


SECTION_SIX_RULES = {
    "band--barbarian-special-skills",
    "band--dwarf-special-skills",
    "band--elf-special-skills",
    "band--the-silence",
    "runts--teeny-hands",
    "band--bow-restrictions",
    "band--hired-swords",
}

#: The clauses the retired T09 ledger recorded as absorbed (band, rule, mechanism).
ABSORBED = (
    ("dwarf-slayer-cult-web", "axe-hurlers--born-marksmen", "E02-skill-access"),
    ("dwarf-slayer-cult-web", "band--slayer-special-skills", "E02-skill-access"),
    ("dwarf-slayers-kaz", "band--slayer-special-skills", "E02-skill-access"),
    ("adventurers-kaz", "band--barbarian-special-skills", "E02-skill-access"),
    ("adventurers-kaz", "band--dwarf-special-skills", "E02-skill-access"),
    ("adventurers-kaz", "band--elf-special-skills", "E02-skill-access"),
    ("outlaws-of-stirwood-forest-redux-fbg", "band--bow-restrictions", "E05-equipment-list"),
    ("snotlings-web", "runts--teeny-hands", "E05-equipment-list"),
    ("knights-of-the-bitter-moors-mim", "band--hired-swords", "E06-hiring-eligibility"),
    ("silent-brotherhood-sc", "band--the-silence", "E06-hiring-eligibility"),
)


def test_the_absorbed_clauses_keep_publishing_kb_structure():
    clauses = _load(CLAUSES)
    bands = _bands()
    assert {rule_id for _, rule_id, _ in ABSORBED} >= SECTION_SIX_RULES
    open_keys = {(row["band_id"], row["rule_id"]) for row in clauses["open_clauses"]}
    hired = read_yaml(KB / "catalog" / "campaign" / "hired-swords-and-dramatis.yaml")
    hiring_rules = {str(row["rule_id"]) for row in hired.get("band_hiring_clauses") or ()}
    for band_id, rule_id, mechanism in ABSORBED:
        assert (band_id, rule_id) not in open_keys, f"{rule_id} is absorbed but listed as open"
        rule = _rule(bands, band_id, rule_id)
        # The clause became structure: either the rule publishes an executable
        # construction binding, or the campaign catalogue carries its band clause.
        assert runtime_bindings(rule) or rule_id in hiring_rules, (
            f"{rule_id} is recorded as absorbed but publishes no construction binding")
        if mechanism == "E02-skill-access":
            effects = [
                effect
                for effect in (rule.get("runtime") or {}).get("effects") or ()
                if (effect.get("binding") or {}).get("id") == "profile.skill-access"
            ]
            assert (rule.get("applies_to") or {}).get("profile_ids"), (
                f"{rule_id} must name its recipients")
            assert any(
                (effect.get("binding") or {}).get("parameters", {}).get("skills")
                for effect in effects
            ), f"{rule_id} must publish the printed member list, not the whole catalogue"


def test_the_open_clause_count_is_pinned():
    # 26 since the T09 ledger; absorbing one is a deliberate edit of this number.
    assert len(_load(CLAUSES)["open_clauses"]) == 26
