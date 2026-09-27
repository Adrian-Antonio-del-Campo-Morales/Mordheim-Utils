"""T09 contract parity: the shared tables stay true to the promoted KB.

``packages/typescript/domain/campaign/construction-tables.json`` carries the two
facts the Web domain cannot derive from the generated artefact: the
``runtime-scope.yaml`` profile exclusions (with their reasons, verbatim) and the
KB rules that declare a binding while ``runtime.implemented != YES``.  This gate
projects both straight from ``sources/knowledge``, so the table cannot drift.

``construction-clauses.json`` is the T09 ledger of the accepted T06 matrix: the
``open_clauses`` whose KB record publishes no executable shape (owner KB) and
the ``transfers`` whose subsystem belongs to T10/T13.  Every entry is resolved
against the promoted KB here, and the reconciliation totals are pinned so that
absorbing a clause is a deliberate edit instead of silent drift.

The gate only reads; regenerating the tables stays in ``build/cache/t09``.
"""
from __future__ import annotations

import json
from pathlib import Path

from mordheim_knowledge.loader import (
    load_bands,
    load_items,
    load_runtime_scope,
    read_yaml,
    runtime_bindings,
)

ROOT = Path(__file__).resolve().parents[3]
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
    assert clauses["schema_version"] == 1
    assert {"profile_exclusions", "pending_bindings"} <= set(tables)
    assert {"reconciliation", "open_clauses", "transfers"} <= set(clauses)


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
            # Implemented for another consumer, but it publishes no recipient set:
            # the clause is a band-wide grant the construction contract cannot place.
            assert not (rule.get("applies_to") or {}).get("profile_ids"), (
                f"{row['rule_id']} now publishes recipients; the clause can be structured"
            )
        else:
            assert runtime_bindings(rule) == (), (
                f"{row['rule_id']} is executable now; the clause belongs to the contract"
            )


def test_open_clauses_are_unique_per_band_and_rule():
    clauses = _load(CLAUSES)["open_clauses"]
    keys = [(row["rule_id"], row["band_id"]) for row in clauses]
    assert len(keys) == len(set(keys)), "an open clause is listed twice for the same band"


def test_transfers_are_declared_once_and_owned():
    transfers = _load(CLAUSES)["transfers"]
    ids = [row["effect_id"] for row in transfers]
    assert len(ids) == len(set(ids)), "a transferred obligation is listed twice"
    for row in transfers:
        assert set(row) == TRANSFER_KEYS, row
        assert row["mechanism"] in MECHANISMS, row
        assert row["to_task"] in {"T10", "T13"}, row
        # `owner` is the rule or effect the accepted matrix attributes the
        # clause to; `effect_id` is the obligation key. Both must be present.
        assert row["owner"].strip() and row["effect_id"].strip(), row
        assert row["reason"].strip(), row


def test_every_non_covered_obligation_carries_a_review_category():
    clauses = _load(CLAUSES)
    review = clauses["review"]
    categories = review["categories"]
    assert set(categories) <= {
        "blocker",
        "pending-owner",
        "covered-data",
        "combat",
        "by-plan",
        "system-excluded",
    }, sorted(categories)
    assert categories.get("blocker", 0) == 0, (
        "T09 must not close with an open blocker: absorb it (KB + contract + test) or it stays a "
        "construction-validity defect"
    )
    assert sum(categories.values()) == (
        len(clauses["open_clauses"])
        + len(clauses["transfers"])
        + len(review["system_excluded"])
    ), "every non-covered obligation must be reviewed exactly once"
    assert len(review["rows"]) == sum(categories.values())
    review_keys = {row["key"] for row in review["rows"] if "key" in row}
    declared = {
        f"{row['band_id']}|{row['rule_id']}" if row["band_id"] else row["rule_id"]
        for row in clauses["open_clauses"]
    }
    assert review_keys == declared, "the review must cover every open clause"
    for row in review["rows"]:
        assert row["category"].strip(), row
        if row["category"] == "blocker":
            continue
        # Clause rows carry `evidence`, transferred obligations carry `reason`.
        assert (row.get("evidence") or row.get("reason") or "").strip(), row
    assert review["categories"] == clauses["reconciliation"]["review_categories"]


SECTION_SIX_RULES = {
    "band--barbarian-special-skills",
    "band--dwarf-special-skills",
    "band--elf-special-skills",
    "band--the-silence",
    "runts--teeny-hands",
    "band--bow-restrictions",
    "band--hired-swords",
}
ABSORBED_KEYS = {
    "rule_id", "band_id", "mechanism", "impact", "kb_change", "contract", "test", "evidence",
    "category", "key",
}


def test_the_section_six_blockers_are_absorbed_with_kb_contract_and_test():
    clauses = _load(CLAUSES)
    absorbed = clauses["review"]["closed_by_t09"]
    bands = _bands()
    assert {row["rule_id"] for row in absorbed} >= SECTION_SIX_RULES, (
        "the seven blockers of \u00a76 must be recorded as absorbed: %s"
        % sorted(SECTION_SIX_RULES - {row["rule_id"] for row in absorbed})
    )
    open_keys = {
        f"{row['band_id']}|{row['rule_id']}" if row["band_id"] else row["rule_id"]
        for row in clauses["open_clauses"]
    }
    hired = read_yaml(KB / "catalog" / "campaign" / "hired-swords-and-dramatis.yaml")
    hiring_rules = {str(row["rule_id"]) for row in hired.get("band_hiring_clauses") or ()}
    for row in absorbed:
        assert set(row) == ABSORBED_KEYS, row
        assert row["category"] == "absorbed", row
        assert row["impact"] in {"over-allow", "under-allow"}, row
        assert row["kb_change"].strip() and row["contract"].strip() and row["test"].strip(), row
        assert row["evidence"].strip(), row
        assert row["key"] not in open_keys, (
            f"{row['key']} is absorbed but still listed as an open clause"
        )
        rule = _rule(bands, row["band_id"], row["rule_id"])
        # The clause became structure: either the rule publishes an executable
        # construction binding, or the campaign catalogue carries its band clause.
        bindings = runtime_bindings(rule)
        structured = bool(bindings) or row["rule_id"] in hiring_rules
        assert structured, (
            f"{row['rule_id']} is recorded as absorbed but publishes no construction binding"
        )
        if row["mechanism"] == "E02-skill-access":
            effects = [
                effect
                for effect in (rule.get("runtime") or {}).get("effects") or ()
                if (effect.get("binding") or {}).get("id") == "profile.skill-access"
            ]
            assert (rule.get("applies_to") or {}).get("profile_ids"), (
                f"{row['rule_id']} must name its recipients"
            )
            assert any(
                (effect.get("binding") or {}).get("parameters", {}).get("skills")
                for effect in effects
            ), f"{row['rule_id']} must publish the printed member list, not the whole catalogue"


def test_battle_magic_records_are_adjudicated_as_system_excluded():
    review = _load(CLAUSES)["review"]
    coordination = review["coordination"]
    assert coordination["decided_by"] == "coordinador", coordination
    assert coordination["decision"] == "sistema excluido", coordination
    assert coordination["motive"] == "X4", coordination
    excluded = review["system_excluded"]
    assert len(excluded) == 12, "the twelve spell records are the adjudicated set"
    transferred = {row["effect_id"] for row in _load(CLAUSES)["transfers"]}
    for row in excluded:
        assert row["effect_id"].startswith("spell."), row
        assert row["category"] == "system-excluded", row
        assert row["destination"] == "sistema excluido" and row["motive"] == "X4", row
        assert row["owner_task"] == "plan" and row["reason"].strip(), row
        assert row["effect_id"] not in transferred, (
            f"{row['effect_id']} is excluded by the plan, not transferred to another task"
        )
        # Traceability: the effect stays in the review matrix.
        assert any(entry.get("effect_id") == row["effect_id"] for entry in review["rows"]), row
    assert coordination["effects"] == sorted(row["effect_id"] for row in excluded)
    assert {row["effect_id"] for row in review["misrouted_by_t06"]} == set(coordination["effects"])
    for row in review["combat"]:
        assert row["to_task"] == "T13", row
    for row in review["pending_owner"]:
        assert row["owner_task"] in {"T10", "T13", "KB", "plan"}, row
    for row in review["covered_by_published_data"]:
        assert row["category"] == "covered-data" and row["evidence"].strip(), row


def test_the_125_obligations_are_reconciled_totals_in_the_table():
    clauses = _load(CLAUSES)
    reconciliation = clauses["reconciliation"]
    review = clauses["review"]
    assert reconciliation["total_obligations"] == 125, (
        "the accepted T06 matrix routes 125 obligations to T09; regenerate the ledger "
        "(python build/cache/t09/t09-classify.py) instead of editing this number"
    )
    assert reconciliation["open_clauses"] == len(clauses["open_clauses"])
    assert reconciliation["transfers"] == len(clauses["transfers"])
    assert reconciliation["excluded_by_plan"] == len(review["system_excluded"])
    assert reconciliation["absorbed_clauses"] == len(review["closed_by_t09"])
    assert reconciliation["review_categories"] == review["categories"]
    assert reconciliation["covered_by_contract"] == (
        reconciliation["total_obligations"]
        - reconciliation["open_clauses"]
        - reconciliation["transfers"]
        - reconciliation["excluded_by_plan"]
    ), "the four buckets must exhaust the matrix"
    assert reconciliation["review_categories"] == review["categories"]
