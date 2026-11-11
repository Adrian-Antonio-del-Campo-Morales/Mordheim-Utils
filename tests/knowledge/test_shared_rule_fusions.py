"""Regression coverage for destructive shared-rule consolidations."""

from collections import Counter

import pytest

from mordheim_knowledge.loader import load_bands, load_shared_rules



#: How many band rules reference each fused id. The counts pin the consolidation:
#: every band rule whose printed text is the shared rule (identical, or differing only
#: in the recipient's name) references it instead of restating the prose.
FUSED_REFERENCE_COUNTS = {
    "shared-rule.animal": 20,
    "shared-rule.burn-the-witch": 2,
    "shared-rule.fear": 44,
    "shared-rule.immune-to-poison": 27,
    "shared-rule.immune-to-psychology": 28,
    "shared-rule.large-target": 13,
    "shared-rule.leader": 52,
    "shared-rule.may-not-run": 13,
    "shared-rule.no-pain": 39,
    "shared-rule.thick-skull": 7,
}

RETIRED_RULE_IDS = {
    # 2026-11-11 prose consolidation: numbered variants renamed, "never gains Experience" texts fused.
    "shared-rule.armour-2",
    "shared-rule.brainless",
    "shared-rule.cause-fear-2",
    "shared-rule.dead",
    "shared-rule.experience",
    "shared-rule.hard-head-2",
    "shared-rule.immune-to-poison-3",
    "shared-rule.immune-to-psychology-4",
    "shared-rule.may-not-run-2",
    "shared-rule.no-pain-4",
    "shared-rule.stupidity-2",
    "shared-rule.animal-2",
    "shared-rule.animals",
    "shared-rule.animals-2",
    "shared-rule.animals-3",
    "shared-rule.ard-ead",
    "shared-rule.burn-the-witch-2",
    "shared-rule.fear-2",
    "shared-rule.fear-3",
    "shared-rule.fear-4",
    "shared-rule.fear-5",
    "shared-rule.fear-6",
    "shared-rule.fear-7",
    "shared-rule.immune-to-poison-2",
    "shared-rule.immune-to-poison-4",
    "shared-rule.immune-to-psychology-3",
    "shared-rule.immune-to-psychology-5",
    "shared-rule.large-target-2",
    "shared-rule.leader-2",
    "shared-rule.leader-3",
    "shared-rule.leader-4",
    "shared-rule.leader-5",
    "shared-rule.may-not-run-3",
    "shared-rule.no-pain-2",
    "shared-rule.no-pain-3",
}


def test_fused_shared_rules_are_the_only_reference_targets() -> None:
    shared = load_shared_rules("mordheim")
    assert len(shared) == 143
    assert set(FUSED_REFERENCE_COUNTS) <= set(shared)
    assert RETIRED_RULE_IDS.isdisjoint(shared)

    all_references = [
        str(rule.get("rule_ref"))
        for collection in ("mordheim", "trollheim")
        for package in load_bands(collection)
        for rule in package.special_rules
        if rule.get("rule_ref")
    ]
    assert RETIRED_RULE_IDS.isdisjoint(all_references)
    references = Counter(ref for ref in all_references if ref in FUSED_REFERENCE_COUNTS)
    assert references == FUSED_REFERENCE_COUNTS


def test_fusion_keeps_runtime_on_local_band_rules() -> None:
    bindings = {
        (str(effect.get("binding", {}).get("kind")), str(effect.get("binding", {}).get("id")))
        for collection in ("mordheim", "trollheim")
        for package in load_bands(collection)
        for rule in package.special_rules
        if rule.get("rule_ref") in FUSED_REFERENCE_COUNTS
        for effect in (rule.get("runtime") or {}).get("effects") or ()
        if effect.get("binding")
    }
    assert ("mechanic", "skill.thick-skull") in bindings
    assert ("mechanic", "skill.ignore-pain") in bindings
    assert ("trait", "trait.poison-immune") in bindings
