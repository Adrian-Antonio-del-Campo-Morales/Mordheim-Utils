"""Catalogue contracts for executable combat rule families.

Moved from ``tests/engines/vectorized/test_shared_families.py`` by T08: the
subject is the knowledge catalogue and its runtime bindings, not the
vectorized engine.
"""
from __future__ import annotations

from collections import Counter
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import runtime_bindings
import json as json
from pathlib import Path
import pytest as pytest
import yaml as yaml


ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"


def _family_binding(rule: dict, kind: str, family_id: str, member: str = "member") -> dict:
    """Return the family's own binding, or fail naming the contract violation.

    The family id names exactly one combat binding (``compiler.*``,
    ``mechanic.*`` or ``trait.*``): the catalogue is the membership contract of
    that binding, not an inventory of every binding a member rule carries.
    Construction obligations (``profile.*``) belong to warband construction and
    have their own owners (the effect matrix and construction contracts), so an additional
    profile binding next to the family binding is legitimate — but it can never
    substitute or shadow the family's own executable binding.
    """
    bindings = list(runtime_bindings(rule))
    matches = [binding for binding in bindings if (binding["kind"], binding["id"]) == (kind, family_id)]
    if not matches:
        raise AssertionError(
            f"{member}: family binding ({kind}, {family_id}) absent; "
            f"rule carries {[(binding['kind'], binding['id']) for binding in bindings]}"
        )
    if len(matches) != 1:
        raise AssertionError(f"{member}: family binding ({kind}, {family_id}) declared {len(matches)} times")
    return matches[0]


def test_all_implemented_canonical_families_are_executable_for_every_member():
    document = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    families = document["families"]
    # The counts are declared next to the roster, so they must equal it; freezing
    # them here made the gate fail every time the catalogue grew.
    assert document["counts"] == {
        "families": len(families),
        "rules": sum(len(family["members"]) for family in families),
        "kinds": dict(Counter(family["kind"] for family in families)),
    }
    packages = {
        package.band["id"]: package
        for collection in ("mordheim", "trollheim")
        for package in load_bands(collection, ROOT)
    }
    for family in document["families"]:
        assert family["implemented"] == "YES"
        for member in family["members"]:
            band_id, rule_id = member.split("/", 1)
            rule = next(rule for rule in packages[band_id].special_rules if rule["id"] == rule_id)
            assert rule["runtime"]["implemented"] == "YES"
            # The roster is the membership contract of this one binding, not an
            # inventory of every binding the rule carries: a rule may implement
            # several mechanics and therefore appear in several families.
            _family_binding(rule, family["kind"], family["id"], member)


def test_family_binding_lookup_accepts_only_the_family_contract():
    kind, family_id = "compiler", "compiler.bow-discipline"

    def rule_with(*bindings):
        return {"runtime": {"scope": "YES", "implemented": "YES", "effects": [
            {"id": binding["id"], "scope": "YES", "binding": binding}
            for binding in bindings
        ]}}

    # The family's own binding alone satisfies the contract.
    rule = rule_with({"kind": kind, "id": family_id})
    assert _family_binding(rule, kind, family_id)["id"] == family_id
    # An additional binding owned by another subsystem (warband construction)
    # is legitimate next to the family binding: Bow Discipline carries both its
    # compiler contract and its profile.equipment-restrictions obligation.
    rule = rule_with(
        {"kind": kind, "id": family_id},
        {"kind": "profile", "id": "profile.equipment-restrictions"},
    )
    assert _family_binding(rule, kind, family_id)["id"] == family_id
    # A rule carrying only the additional binding does not provide the family.
    with pytest.raises(AssertionError, match="absent"):
        _family_binding(rule_with({"kind": "profile", "id": "profile.equipment-restrictions"}), kind, family_id)
    # A different binding id does not substitute the family binding.
    with pytest.raises(AssertionError, match="absent"):
        _family_binding(rule_with({"kind": kind, "id": "compiler.some-other-contract"}), kind, family_id)


def test_unique_effect_members_share_the_family_binding_parameters():
    """Identical-effect families must share the family binding parameters.

    ``basis: unique-effect`` declares one identical effect everywhere, so the
    binding parameters cannot differ between members. Wider bases
    (``equivalent-effects``, ``shared-effect``) legitimately parameterise the
    same binding per band, e.g. ``compiler.forbid-item-categories`` forbids
    only poison for the monk bands and poison plus drugs for the honourable
    ones.
    """
    document = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    packages = {
        package.band["id"]: package
        for collection in ("mordheim", "trollheim")
        for package in load_bands(collection, ROOT)
    }
    for family in document["families"]:
        if family["basis"] != "unique-effect":
            continue
        observed = {}
        for member in family["members"]:
            band_id, rule_id = member.split("/", 1)
            rule = next(rule for rule in packages[band_id].special_rules if rule["id"] == rule_id)
            binding = _family_binding(rule, family["kind"], family["id"], member)
            parameters = json.dumps(binding.get("parameters") or {}, sort_keys=True)
            observed.setdefault(parameters, []).append(member)
        assert len(observed) == 1, (
            f"family {family['id']}: unique-effect members disagree on parameters: {observed}"
        )


def test_family_roster_covers_each_declared_binding():
    document = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    families = document["families"]
    family_ids = [(family["kind"], family["id"]) for family in families]
    assert len(family_ids) == len(set(family_ids)) == document["counts"]["families"]
    assert Counter(family["kind"] for family in families) == document["counts"]["kinds"]
    members = [member for family in families for member in family["members"]]
    # A rule may carry two executable bindings, so it is listed once in each
    # binding's family; the catalogue's `rules` count is the membership total.
    assert len(members) == document["counts"]["rules"]
    for family in families:
        assert len(family["members"]) == len(set(family["members"])), (
            f"family {family['id']}: a member is listed more than once"
        )


def test_bow_discipline_keeps_both_of_its_declared_bindings():
    """Bow Discipline owns a combat contract and a construction obligation.

    The compiler binding (``compiler.bow-discipline``) is the family's own
    executable contract — the one the Combat Simulator consumes; the profile
    binding (``profile.equipment-restrictions``) carries the printed band-wide
    equipment restriction (at most one missile weapon, it must be a bow, the
    Cleric is exempt) consumed by warband construction. Neither can replace the
    other, and both stay materialized on the rule.
    """
    packages = {
        package.band["id"]: package
        for collection in ("mordheim", "trollheim")
        for package in load_bands(collection, ROOT)
    }
    members = (
        ("mordheim", "outlaws-of-stirwood-forest", "band--bow-discipline"),
        ("mordheim", "outlaws-of-stirwood-forest-redux-fbg", "band--bow-restrictions"),
    )
    for collection, band_id, rule_id in members:
        package = next(
            package for package in load_bands(collection, ROOT)
            if str(package.band["id"]) == band_id
        )
        rule = next(rule for rule in package.special_rules if rule["id"] == rule_id)
        assert rule["runtime"]["implemented"] == "YES"
        bindings = {(binding["kind"], binding["id"]): binding for binding in runtime_bindings(rule)}
        assert ("compiler", "compiler.bow-discipline") in bindings
        restriction = bindings.get(("profile", "profile.equipment-restrictions"))
        assert restriction is not None, f"{band_id}/{rule_id}: profile.equipment-restrictions binding missing"
        parameters = restriction.get("parameters") or {}
        assert parameters.get("forbids") == "crossbow"
        assert parameters.get("max_missile_weapons") == 1
        assert parameters.get("required_tag") == "bow"
        assert list(parameters.get("exempt_profile_ids") or ()) == ["cleric"]


def test_art_of_silent_death_kb_texts_use_to_wound_and_share_the_eshin_contract():
    packages = {
        package.band["id"]: package
        for collection in ("mordheim", "trollheim")
        for package in load_bands(collection, ROOT)
    }
    members = (
        ("skaven-clan-eshin", "band--skaven-special-skills-art-of-silent-death"),
        ("trollheim-skaven-clan-eshin", "band--skaven-special-skills-art-of-silent-death"),
        ("chaos-streets-deathbringers", "band--deathbringer-special-skills-art-of-unarmed-combat"),
    )
    for band_id, rule_id in members:
        rule = next(rule for rule in packages[band_id].special_rules if rule["id"] == rule_id)
        text = rule["effect"].lower()
        assert "to wound" in text and "to hit roll of 5-6" not in text
        _family_binding(rule, "mechanic", "skill.art-of-silent-death", f"{band_id}/{rule_id}")
