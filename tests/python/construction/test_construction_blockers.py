"""T09 §6 blockers: the KB publishes the datum the construction contract reads.

The seven clauses T09 had to close by itself are gated here, straight from
``sources/knowledge``:

1-3. `adventurers-kaz` special-skill tables: each rule names its recipients and
     publishes the printed member list (bounded, not the whole `special`
     catalogue), and every listed skill is a published `special` skill;
4.   `silent-brotherhood-sc` `band--the-silence`: a band-wide prohibition whose
     tokens are catalogue item tags — the tag vocabulary is closed and shared
     with the shared eligibility domain constant;
5.   `snotlings-web` `runts--teeny-hands`: the Runts prohibit armour by token
     while the shared list keeps carrying the armour items;
6.   `outlaws-of-stirwood-forest*` bow restrictions: the printed limit (one
     missile weapon, a mandatory bow, the Cleric exemption) is published as
     data and every named exception is a real profile of the band;
7.   `knights-of-the-bitter-moors-mim` `band--hired-swords`: the printed
     narrowing lives in the campaign catalogue's `band_hiring_clauses`, keyed by
     the band rule and by stable trait/item-tag ids.

The behavioural side of the same seven clauses (accept/reject verdicts) is
proved in `tests/typescript/domain/campaign/construction-blockers.test.ts`.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from mordheim_knowledge.loader import load_bands, load_items, read_yaml

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
CONTRACTS = ROOT / "contracts" / "knowledge-editorial-v1"
COLLECTION = "mordheim"
CONSTRUCTION = ROOT / "packages" / "typescript" / "domain" / "eligibility" / "index.ts"

KAZ = "adventurers-kaz"
SILENCE = "silent-brotherhood-sc"
SNOTLINGS = "snotlings-web"
OUTLAWS = ("outlaws-of-stirwood-forest", "outlaws-of-stirwood-forest-redux-fbg")
KNIGHTS = "knights-of-the-bitter-moors-mim"

SKILL_TABLES = {
    "barbarian": ("band--barbarian-special-skills", {"skill.hard-to-kill", "skill.ferocious-charge",
                                                     "skill.instinctive-warrior"}),
    "dwarf": ("band--dwarf-special-skills", {"skill.berserker", "skill.ferocious-charge",
                                             "skill.magic-resistant", "skill.monster-slayer"}),
    "elf": ("band--elf-special-skills", {"skill.fey", "skill.chosen-of-the-white-tower",
                                         "skill.fey-quickness"}),
    "imperial-noble": ("band--noble-special-skills", {"skill.trading-flair", "skill.taunt"}),
}


def _band(band_id: str):
    return next(band for band in load_bands(COLLECTION, KB) if str(band.band["id"]) == band_id)


def _rule(band, rule_id: str) -> dict:
    rule = next((row for row in band.special_rules if str(row.get("id")) == rule_id), None)
    assert rule is not None, f"{band.band['id']} declares no rule {rule_id}"
    return rule


def _binding(rule: dict, binding_id: str) -> dict | None:
    for effect in (rule.get("runtime") or {}).get("effects") or ():
        if effect.get("scope") != "YES":
            continue
        binding = effect.get("binding") or {}
        if binding.get("id") == binding_id:
            return binding
    return None


def _tag_vocabulary() -> set[str]:
    """Closed item-tag vocabulary of the item contract (`$defs.item.properties.tags`)."""
    schema = json.loads((CONTRACTS / "catalog-items.yaml.schema.json").read_text(encoding="utf-8"))
    return {
        str(value)
        for value in schema["$defs"]["item"]["properties"]["tags"]["items"]["enum"]
    }


def _item_tags() -> dict[str, set[str]]:
    tags: dict[str, set[str]] = {}
    for row in load_items(COLLECTION, KB):
        declared = {str(value) for value in row.get("tags") or ()}
        if declared:
            tags[str(row.get("id"))] = declared
    return tags


def test_kaz_skill_tables_name_their_recipients_and_publish_the_printed_members():
    band = _band(KAZ)
    profiles = {str(row.get("id")) for row in band.profiles}
    special = {
        str(row.get("id")): row
        for row in read_yaml(KB / "catalog" / "skills" / "warband.yaml").get("skills", [])
        if str(row.get("category")) == "special"
    }
    assert len(special) > 20, "the special catalogue must be the whole printed set"
    for profile_id, (rule_id, skills) in SKILL_TABLES.items():
        assert profile_id in profiles, f"{KAZ} declares no profile {profile_id}"
        rule = _rule(band, rule_id)
        recipients = (rule.get("applies_to") or {}).get("profile_ids") or ()
        assert profile_id in recipients, (
            f"{rule_id} does not name its recipient {profile_id}: the artefact grants nothing"
        )
        binding = _binding(rule, "profile.skill-access")
        assert binding is not None, f"{rule_id} publishes no profile.skill-access binding"
        parameters = binding.get("parameters") or {}
        assert parameters.get("category") == "special", rule_id
        published = {str(skill) for skill in parameters.get("skills") or ()}
        assert published == skills, (
            f"{rule_id} must publish exactly the printed member list (got {sorted(published)})"
        )
        assert published < set(special), (
            f"{rule_id} must not grant the whole special catalogue"
        )
        for skill_id in published:
            assert special.get(skill_id) is not None, f"{skill_id} is not a published special skill"


def test_silence_tokens_are_catalogue_item_tags_and_the_vocabulary_is_closed():
    band = _band(SILENCE)
    rules = [
        rule for rule in band.special_rules
        if (rule.get("applies_to") or {}).get("band") and _binding(rule, "profile.equipment-restrictions")
    ]
    assert rules, "the Silence must publish a band-wide equipment prohibition"
    forbidden: set[str] = set()
    for rule in rules:
        parameters = (_binding(rule, "profile.equipment-restrictions") or {}).get("parameters") or {}
        values = parameters.get("forbids")
        forbidden.update([values] if isinstance(values, str) else [str(value) for value in values or ()])
    assert forbidden == {"blackpowder", "animal"}, sorted(forbidden)

    vocabulary = _tag_vocabulary()
    # The domain resolves a prohibition token through this closed vocabulary.
    declared = re.search(
        r"EQUIPMENT_TAG_VOCABULARY: readonly string\[\] = \[(.*?)\];",
        CONSTRUCTION.read_text(encoding="utf-8"),
        re.DOTALL,
    )
    assert declared is not None, "shared eligibility must declare the item-tag vocabulary"
    domain = set(re.findall(r'"([a-z-]+)"', declared.group(1)))
    assert domain == vocabulary, (
        f"the domain vocabulary and the item contract diverged: {sorted(domain ^ vocabulary)}"
    )
    assert forbidden <= vocabulary, (
        f"{sorted(forbidden - vocabulary)} are not catalogue item tags"
    )
    tags = _item_tags()
    assert any("blackpowder" in value for value in tags.values()), "no item is tagged blackpowder"
    for item_id, declared_tags in tags.items():
        assert declared_tags <= vocabulary, f"{item_id} uses a tag outside the vocabulary"


def test_teeny_hands_forbids_armour_without_emptying_the_shared_list():
    band = _band(SNOTLINGS)
    runts = next((row for row in band.profiles if str(row.get("id")) == "runts"), None)
    assert runts is not None, "the Runts profile must exist"
    rule = _rule(band, "runts--teeny-hands")
    assert "runts" in (rule.get("applies_to") or {}).get("profile_ids") or (), (
        "runts--teeny-hands must name the profile it binds"
    )
    binding = _binding(rule, "profile.equipment-restrictions")
    assert binding is not None, "runts--teeny-hands publishes no equipment prohibition"
    assert (binding.get("parameters") or {}).get("forbids") == "armour"
    # The prohibition is a profile token: the shared list keeps offering armour
    # to the other slots that use it.
    shared = [
        list_ for list_ in band.equipment_lists
        if "snotling-equipment-list" == str(list_.get("id"))
    ]
    assert shared, "the shared Snotling equipment list must stay published"
    offered = {str(item.get("item_id")) for item in shared[0].get("items") or ()}
    assert {"light_armour", "shield"} <= offered, (
        "the armour items must stay on the shared list; only the profile forbids them"
    )
    others = [row for row in band.profiles if str(row.get("id")) in {"scouts", "bigsnotz"}]
    assert others, "profiles sharing the list must stay published"
    for other in others:
        assert "snotling-equipment-list" in [str(value) for value in other.get("equipment_lists") or ()]


def test_bow_restrictions_publish_the_limit_and_its_printed_exception():
    for band_id in OUTLAWS:
        band = _band(band_id)
        profiles = {str(row.get("id")) for row in band.profiles}
        rule = next(
            (
                row for row in band.special_rules
                if row.get("applies_to", {}).get("band")
                and (_binding(row, "profile.equipment-restrictions") or {}).get("parameters", {}).get(
                    "max_missile_weapons"
                )
            ),
            None,
        )
        assert rule is not None, f"{band_id} publishes no bow limit"
        parameters = (_binding(rule, "profile.equipment-restrictions") or {}).get("parameters") or {}
        assert parameters["max_missile_weapons"] == 1, rule
        assert parameters["required_tag"] == "bow", rule
        assert "crossbow" in (
            [parameters["forbids"]] if isinstance(parameters.get("forbids"), str)
            else list(parameters.get("forbids") or ())
        ), rule
        exempt = [str(value) for value in parameters.get("exempt_profile_ids") or ()]
        assert exempt == ["cleric"], rule
        for profile_id in exempt:
            assert profile_id in profiles, f"{band_id} declares no profile {profile_id}"


def test_hired_swords_clause_is_published_with_stable_ids():
    catalogue = read_yaml(KB / "catalog" / "campaign" / "hired-swords-and-dramatis.yaml")
    clauses = [
        row for row in catalogue.get("band_hiring_clauses") or ()
        if str(row.get("band_id")) == KNIGHTS
    ]
    assert len(clauses) == 1, "the band's printed narrowing must be published once"
    clause = clauses[0]
    band = _band(KNIGHTS)
    _rule(band, str(clause["rule_id"]))  # the clause names a real band rule
    assert clause["rule_id"] == "band--hired-swords", clause
    assert clause.get("note", "").strip(), "the clause must carry the printed sentence"
    groups = read_yaml(KB / "registry" / "warband-groups.yaml").get("groups", [])
    human = next(row for row in groups if str(row.get("id")) == "warband-group.human")
    assert KNIGHTS in [str(value) for value in human.get("band_ids") or ()], (
        "Bretonnians count as Humans; the group membership carries that"
    )
    traits = {
        str(row["profile_id"]): {str(value) for value in row.get("traits") or ()}
        for row in read_yaml(KB / "catalog" / "hirelings" / "traits.yaml").get("traits", [])
    }
    vocabulary = _tag_vocabulary()
    excluded_traits = {str(value) for value in clause.get("exclude_traits") or ()}
    assert excluded_traits == {"spellcaster"}, clause
    assert excluded_traits <= {trait for values in traits.values() for trait in values}, (
        "the excluded traits must be published hireling traits"
    )
    excluded_tags = {str(value) for value in clause.get("exclude_item_tags") or ()}
    assert excluded_tags == {"blackpowder", "poison"}, clause
    assert excluded_tags <= vocabulary, (
        f"{sorted(excluded_tags - vocabulary)} are not catalogue item tags"
    )
    tags = _item_tags()
    for tag in excluded_tags:
        assert any(tag in values for values in tags.values()), f"no item is tagged {tag}"
