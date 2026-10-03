"""T13-F042/F043: regression ledger for the catalogue contract repairs.

Both findings were contract/check mismatches, not product defects:

* **F042** — `sisters-of-sigmar`/`band--human-maximum-characteristics` printed
  the Human racial maximum in prose without linking the canonical
  `campaign.limit.racial-maximum.human` entry, so the maintained catalogue test
  refused the document. The repair adds the reference to the English effect and
  its Spanish translation; no table, recipient or combat rule changed.
* **F043** — the hired-sword eligibility gate kept its own allowed-key list,
  which had fallen behind the editorial contract: the schema declares
  `note_i18n` (the reviewed translation of `note`) and the committed catalogue
  uses it. The repair reads the accepted keys from the maintained contract.

Both repaired checks live in ``test_campaign_catalogs.py``; the helpers are
imported below instead of being restated, so these positive and negative cases
exercise the maintained gates and a later relaxation fails here. F042's scan
covers every committed band; F043's malformed blocks are validated with the
maintained document validator.

Contract evidence is not product behaviour. The localized eligibility notes are
editorial data: the loader and campaign eligibility consumers do not read
`eligibility.note_i18n`, while the maintained publication path preserves it
in the catalogue and display-text artefacts. The trace, including the
Albino Stormvermin note, is recorded in
`docs/knowledge/2a2b/tasks/T13-catalogue-contracts.md`.
"""
from __future__ import annotations

import copy

import pytest
import yaml

import test_campaign_catalogs as catalog_tests

ALBINO = "campaign.hireling.hired-sword.albino-stormvermin"
ALBINO_NOTE = "Albino Stormvermin may only be hired by Skaven warbands."
ALBINO_NOTE_ES = "Los Guardias Albinos solo pueden ser contratados por bandas skaven."
SISTERS_RULE = "band--human-maximum-characteristics"
SISTERS_BAND = "sisters-of-sigmar"
HUMAN_MAXIMUM = "campaign.limit.racial-maximum.human"

#: A contract-valid block used as the base of the malformed variants below.
VALID_ELIGIBILITY = {
    "allow_groups": ["warband-group.skaven"],
    "forbid_groups": [],
    "allow_band_ids": [],
    "forbid_band_ids": [],
    "note": ALBINO_NOTE,
    "note_i18n": {"es": ALBINO_NOTE_ES},
}


def sisters_rule() -> dict:
    path = catalog_tests.ROOT / "bands" / "mordheim" / SISTERS_BAND / "special-rules.yaml"
    rules = yaml.safe_load(path.read_text(encoding="utf-8"))["rules"]
    return next(rule for rule in rules if rule["id"] == SISTERS_RULE)


def sisters_effect() -> str:
    return " ".join(str(sisters_rule()["effect"]).split())


def document_with_eligibility(eligibility: dict | None) -> dict:
    """The committed catalogue with one entry's eligibility replaced.

    Everything else stays as committed, so the maintained document validator
    sees exactly the injected block (``None`` removes the block entirely).
    """
    document = copy.deepcopy(catalog_tests.campaign("hired-swords-and-dramatis.yaml"))
    entry = next(row for row in document["hired_swords"] if row["id"] == ALBINO)
    if eligibility is None:
        entry.pop("eligibility", None)
    else:
        entry["eligibility"] = eligibility
    return document


# ---------------------------------------------------------------------------
# F042 — racial-maximum references stay resolved
# ---------------------------------------------------------------------------
def test_f042_sisters_of_sigmar_links_the_human_maximum():
    effect = sisters_effect()
    assert HUMAN_MAXIMUM in catalog_tests.racial_maximum_ids()
    assert catalog_tests.RACIAL_MAXIMUM_REFERENCE.findall(effect) == [HUMAN_MAXIMUM]
    assert HUMAN_MAXIMUM in str(sisters_rule()["effect_i18n"]["es"])
    assert catalog_tests.racial_maximum_reference_problems(
        effect, catalog_tests.racial_maximum_ids(), f"{SISTERS_BAND}: {SISTERS_RULE}"
    ) == []


def test_f042_the_linked_maximum_covers_the_band_groups():
    """The linked entry is the one the band's registry groups declare."""
    maximums = {row["id"]: row for row in catalog_tests.load("catalog/rules/racial-maximums.yaml")["racial_maximums"]}
    registry = yaml.safe_load(
        (catalog_tests.ROOT / "registry" / "warband-groups.yaml").read_text(encoding="utf-8")
    )["groups"]
    band_groups = {
        group["id"] for group in registry
        if SISTERS_BAND in (group.get("band_ids") or ())
    }
    assert "warband-group.human" in band_groups
    assert band_groups & set(maximums[HUMAN_MAXIMUM].get("groups") or ()) == {"warband-group.human"}


def test_f042_every_committed_band_rule_resolves_its_references():
    maximum_ids = catalog_tests.racial_maximum_ids()
    problems: list[str] = []
    rules_with_maximums = 0
    for path in sorted(catalog_tests.BANDS.glob("**/special-rules.yaml")):
        for rule in yaml.safe_load(path.read_text(encoding="utf-8")).get("rules", []):
            text = rule.get("effect") or ""
            if "maximum" not in text.lower():
                continue
            rules_with_maximums += 1
            problems.extend(catalog_tests.racial_maximum_reference_problems(
                text, maximum_ids, f"{path.name}: {rule['id']}"
            ))
    assert problems == []
    assert rules_with_maximums >= 20


def test_f042_a_missing_reference_is_still_reported():
    problems = catalog_tests.racial_maximum_reference_problems(
        "Sisters of Sigmar are Humans and use the Human racial maximum profile.",
        catalog_tests.racial_maximum_ids(),
        "synthetic",
    )
    assert problems == ["synthetic: mentions a max profile without ref"]


def test_f042_an_unknown_maximum_reference_is_still_reported():
    problems = catalog_tests.racial_maximum_reference_problems(
        "The warband uses the maximum profile (campaign.limit.racial-maximum.dragon).",
        catalog_tests.racial_maximum_ids(),
        "synthetic",
    )
    assert problems == ["synthetic: unknown racial maximum campaign.limit.racial-maximum.dragon"]


def test_f042_an_inlined_statline_is_still_reported():
    problems = catalog_tests.racial_maximum_reference_problems(
        "The maximum characteristics profile (campaign.limit.racial-maximum.human) is "
        "M4, WS6, BS6, S4, T4, W3, I6, A4, Ld9.",
        catalog_tests.racial_maximum_ids(),
        "synthetic",
    )
    assert problems == ["synthetic: inlines a statline"]


def test_f042_a_warband_size_maximum_is_not_a_racial_maximum():
    # A roster rule that mentions the maximum *warband size* is printed source
    # prose: it stays outside the reference contract, numbers included.
    assert catalog_tests.racial_maximum_reference_problems(
        "The warband may not exceed the maximum warband size of 15 warriors.",
        catalog_tests.racial_maximum_ids(),
        "synthetic",
    ) == []


# ---------------------------------------------------------------------------
# F043 — the eligibility gate reads the editorial contract
# ---------------------------------------------------------------------------
def test_f043_the_maintained_key_set_comes_from_the_contract():
    keys = catalog_tests.eligibility_keys()
    assert {"allow_band_ids", "allow_groups", "forbid_band_ids", "forbid_groups",
            "expression", "note", "note_i18n"} <= keys
    for unknown in ("note_en", "notes", "include", "when"):
        assert unknown not in keys


def test_f043_the_committed_catalogue_matches_the_contract():
    assert catalog_tests.campaign_schema_problems(
        catalog_tests.campaign("hired-swords-and-dramatis.yaml")
    ) == []


def test_f043_albino_stormvermin_keeps_its_localized_note():
    document = catalog_tests.campaign("hired-swords-and-dramatis.yaml")
    entry = next(row for row in document["hired_swords"] if row["id"] == ALBINO)
    eligibility = entry["eligibility"]
    assert eligibility["note"] == ALBINO_NOTE
    assert eligibility["note_i18n"] == {"es": ALBINO_NOTE_ES}
    assert set(eligibility) <= catalog_tests.eligibility_keys()
    assert catalog_tests.eligibility_reference_problems(
        eligibility,
        catalog_tests.canonical_band_ids(),
        catalog_tests.warband_group_ids(),
        ALBINO,
    ) == []
    assert catalog_tests.campaign_schema_problems(document_with_eligibility(dict(eligibility))) == []


def test_f043_a_valid_localized_note_is_accepted():
    assert catalog_tests.campaign_schema_problems(
        document_with_eligibility(dict(VALID_ELIGIBILITY))
    ) == []
    # the block itself is optional; removing it is not a defect either
    assert catalog_tests.campaign_schema_problems(document_with_eligibility(None)) == []


def test_f043_an_unknown_eligibility_key_is_still_rejected():
    block = {**VALID_ELIGIBILITY, "note_en": "Set in English."}
    assert catalog_tests.eligibility_reference_problems(
        block, catalog_tests.canonical_band_ids(), catalog_tests.warband_group_ids(), "synthetic"
    ) == ["synthetic: unknown eligibility key note_en"]
    schema_problems = catalog_tests.campaign_schema_problems(document_with_eligibility(block))
    assert any("note_en" in problem for problem in schema_problems), schema_problems


@pytest.mark.parametrize("note_i18n", [
    {"fr": "Note en francais."},                       # undeclared locale
    {"es": ""},                                        # empty translation
    {"es": "Nota valida.", "en": "English mirror"},    # an `en` mirror is forbidden
    "Just a string.",                                  # not a mapping
    {},                                                # missing the required `es`
])
def test_f043_a_malformed_localized_note_is_still_rejected(note_i18n):
    block = {**VALID_ELIGIBILITY, "note_i18n": note_i18n}
    problems = catalog_tests.campaign_schema_problems(document_with_eligibility(block))
    assert problems, f"the contract accepted a malformed note_i18n: {note_i18n!r}"


def test_f043_invalid_band_and_group_references_are_still_rejected():
    block = {
        **VALID_ELIGIBILITY,
        "allow_groups": ["warband-group.dragon"],
        "forbid_band_ids": ["no-such-band"],
    }
    assert catalog_tests.eligibility_reference_problems(
        block, catalog_tests.canonical_band_ids(), catalog_tests.warband_group_ids(), "synthetic"
    ) == [
        "synthetic: unknown group warband-group.dragon",
        "synthetic: unknown band no-such-band",
    ]


def test_f043_expression_grammar_is_still_enforced():
    band_ids = catalog_tests.canonical_band_ids()
    groups = catalog_tests.warband_group_ids()
    leaf_keys = {"band_id", "group_id"}
    catalog_tests.check_expression(
        {"any_of": [{"group_id": "warband-group.skaven"}, {"band_id": SISTERS_BAND}]},
        leaf_keys, band_ids, groups, "synthetic",
    )
    catalog_tests.check_expression(
        {"not": {"band_id": "skaven-clan-eshin"}}, leaf_keys, band_ids, groups, "synthetic"
    )
    catalog_tests.check_expression(
        [{"band_id": SISTERS_BAND}], leaf_keys, band_ids, groups, "synthetic"
    )
    for broken in (
        {"band_id": "no-such-band"},
        {"group_id": "warband-group.dragon"},
        {"all_of": []},
        {},
        {"any_of": "not-a-list"},
    ):
        with pytest.raises(AssertionError):
            catalog_tests.check_expression(broken, leaf_keys, band_ids, groups, "synthetic")


def test_f043_the_contract_rejects_expression_next_to_allow_band_ids():
    # The schema declares `expression` and `allow_band_ids` mutually exclusive.
    block = {**VALID_ELIGIBILITY, "expression": {"band_id": SISTERS_BAND}}
    problems = catalog_tests.campaign_schema_problems(document_with_eligibility(block))
    assert problems, "the contract accepted expression plus allow_band_ids"
