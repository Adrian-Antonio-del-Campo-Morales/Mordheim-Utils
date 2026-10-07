"""T13-F019 — The Silence's tokens reach the real bound-equipment stage.

Levels exercised: the embedded bundle through the maintained transport
(``validate``/``call``), the maintained compiler/seam route, and the canonical
item projection. Expectations come from the canonical rule, the shared item
facts fixture (verified against the live KB here) and the accepted F035
disposition, never from the code under test.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from mordheim_construction import compiler, restrictions
from mordheim_construction.eligibility import _catalogue, call, context as build_context, validate
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands, load_items, runtime_bindings

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
ITEMS = json.loads((ROOT / "tests/fixtures/eligibility/silence-equipment.json").read_text(encoding="utf-8"))["items"]
BAND = "silent-brotherhood-sc"
PROFILE = "silent-master"
PACK = next(pack for pack in load_bands("mordheim", KB) if str(pack.band["id"]) == BAND)
RULE = next(rule for rule in PACK.special_rules if str(rule["id"]) == "band--the-silence")
BINDINGS = tuple(binding for binding in runtime_bindings(RULE)
                 if str(binding.get("id")) == "profile.equipment-restrictions")
BLACKPOWDER_MESSAGE = f'"blackpowder" is forbidden for {BAND}/{PROFILE}.'


def silence_build(**kwargs) -> FighterBuild:
    values = {"band_id": BAND, "profile_id": PROFILE, "main_weapon_id": "weapon.pistol", **kwargs}
    return FighterBuild("mordheim", **values)


def embedded_context(build: FighterBuild, items=ITEMS, forbidden=("blackpowder", "animal")):
    bindings = [{"kind": "profile", "id": "profile.equipment-restrictions",
                 "parameters": {"forbids": list(forbidden)}}] if forbidden else []
    payload = build_context(build, main_weapon_id=build.main_weapon_id, profile_bindings=bindings)
    payload["catalogue"] = {"packages": {}, "foreign_packages": {}, "mechanics": {}, "mappings": {},
                            "skills": {}, "items": dict(items)}
    return payload


def test_fixture_item_facts_match_the_live_kb_and_the_projection():
    live = {str(row["id"]): row for row in load_items("mordheim", KB)}
    projected = _catalogue("mordheim", "mordheim", KB)["items"]
    assert projected, "the transport must project canonical item facts"
    for item_id, facts in ITEMS.items():
        row = live[item_id]
        assert facts["kind"] == row.get("kind"), item_id
        assert facts["mechanic_id"] == row.get("mechanic_id"), item_id
        assert facts["tags"] == list(row.get("tags") or ()), item_id
        assert projected[item_id] == facts, item_id


def test_silence_refusal_comes_from_the_rule_through_the_real_transport():
    with pytest.raises(ValueError, match='"blackpowder" is forbidden'):
        validate("boundEquipment", silence_build(), KB,
                 main_weapon_id="weapon.pistol", profile_bindings=BINDINGS)


def test_blackpowder_verdict_stays_at_the_stage_and_keeps_lists_incidental():
    """The stage refuses by rule before the equipment list is even consulted."""
    message = call("buildRestriction", embedded_context(silence_build()), "boundEquipment")
    assert message == BLACKPOWDER_MESSAGE
    # A member without the binding, an untagged mechanic and an unmapped id stay legal.
    assert validate("boundEquipment", silence_build(main_weapon_id="weapon.dagger"), KB,
                    main_weapon_id="weapon.dagger", profile_bindings=()) is None
    assert call("buildRestriction", embedded_context(silence_build(main_weapon_id="weapon.sword")),
                "boundEquipment") is None
    assert call("buildRestriction", embedded_context(silence_build(main_weapon_id="weapon.unmapped")),
                "boundEquipment") is None
    assert call("buildRestriction", embedded_context(silence_build(), forbidden=("mystery-token",)),
                "boundEquipment") is None


def test_every_bound_position_and_the_animal_boundary_are_checked():
    # The main hand carries a legal weapon, so every witness proves the stage
    # scans the position it names instead of inheriting the main hand's verdict.
    for position in ({"off_hand_id": "weapon.pistol"},
                     {"extra_hand_id": "weapon.pistol"},
                     {"armour_id": "weapon.pistol"}):
        assert "blackpowder" in call(
            "buildRestriction",
            embedded_context(silence_build(main_weapon_id="weapon.sword", **position)),
            "boundEquipment"), position
    # H5 (2026-10-04): the crossbow pistol is printed under Missile Weapons, not
    # Blackpowder, and the brotherhood list sells it at 35 gc; the stage keeps
    # it legal in every bound position. Source provenance:
    # docs/knowledge/2a2b/tasks/T13-silence-equipment.md section 12.
    assert call("buildRestriction", embedded_context(
        silence_build(main_weapon_id="weapon.sword", extra_hand_id="crossbow_pistol")),
        "boundEquipment") is None
    assert call("buildRestriction", embedded_context(
        silence_build(main_weapon_id="weapon.sword", armour_id="crossbow_pistol")),
        "boundEquipment") is None
    # animal has no admitted Combat Lab equipment position today: this is a
    # boundary witness over its canonical item facts, not a canonical build.
    assert "animal" in call("buildRestriction", embedded_context(
        silence_build(main_weapon_id="weapon.sword", defence_ids=("warhound",))), "boundEquipment")


def test_alias_collisions_keep_the_prohibition_in_both_orders():
    untagged = {"kind": "ranged-weapon", "mechanic_id": "weapon.pistol", "tags": []}
    tagged = {"kind": "ranged-weapon", "mechanic_id": "weapon.pistol", "tags": ["blackpowder"]}
    for items in ({"first": untagged, "second": tagged}, {"first": tagged, "second": untagged}):
        message = call("buildRestriction", embedded_context(silence_build(), items=items), "boundEquipment")
        assert message == BLACKPOWDER_MESSAGE


def test_legacy_tokens_and_their_diagnostics_are_preserved():
    armour = call("buildRestriction", embedded_context(silence_build(armour_id="armour.light-armour"),
                                                       forbidden=("armour",)), "boundEquipment")
    assert armour == f"armour is forbidden for {BAND}/{PROFILE}"
    missiles = call("buildRestriction", embedded_context(silence_build(), forbidden=("ranged-weapons",)),
                    "boundEquipment")
    assert missiles == f"missile weapons are forbidden for {BAND}/{PROFILE}"


def test_maintained_routes_attribute_the_refusal_to_the_rule():
    build = silence_build()
    with pytest.raises(ValueError, match='"blackpowder" is forbidden'):
        restrictions._validate_bound_equipment_restrictions(build, "weapon.pistol", BINDINGS, KB)
    with pytest.raises(ValueError, match='"blackpowder" is forbidden'):
        restrictions._validate_profile_selections(build, PACK, {"id": PROFILE}, KB, "weapon.pistol", BINDINGS)
    with pytest.raises(ValueError, match='"blackpowder" is forbidden'):
        compiler.compile_fighter(build, KB)
    assert restrictions._validate_bound_equipment_restrictions(
        silence_build(main_weapon_id="weapon.dagger"), "weapon.dagger", BINDINGS, KB) is None


def _isolated_kb(tmp_path: Path) -> Path:
    """Minimal KB whose pistol alias carries no blackpowder tag."""
    files = {
        "registry/collections.yaml": {"collections": [{"id": "mordheim", "rulesets": ["mordheim"]}]},
        "bands/mordheim/contract-band/band.yaml": {"id": "contract-band", "ruleset": "mordheim"},
        "bands/mordheim/contract-band/profiles.yaml": {"profiles": [{"id": "member"}]},
        "bands/mordheim/contract-band/equipment-access.yaml": {"equipment_lists": []},
        "bands/mordheim/contract-band/special-rules.yaml": {"rules": [{
            "id": "band--contract-silence",
            "runtime": {"scope": "YES", "implemented": "YES", "grant": "band", "effects": [{
                "id": "profile.equipment-restrictions", "scope": "YES",
                "binding": {"kind": "profile", "id": "profile.equipment-restrictions",
                            "parameters": {"forbids": ["blackpowder"]}},
            }]},
            "applies_to": {"band": True},
        }]},
        "catalog/mechanics/close-combat.yaml": {"ruleset": "mordheim"},
        "catalog/mechanics/simulation-mappings.yaml": {"ruleset": "mordheim", "item_mappings": []},
        "catalog/items/contract.yaml": {"ruleset": "mordheim", "items": [{
            "id": "pistol", "kind": "ranged-weapon", "tags": [], "mechanic_id": "weapon.pistol",
            "combat_status": "out_of_scope",
        }]},
    }
    for relative, document in files.items():
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    return tmp_path


def test_transport_uses_the_callers_root_and_isolates_catalogues(tmp_path):
    binding = [{"kind": "profile", "id": "profile.equipment-restrictions",
                "parameters": {"forbids": ["blackpowder"]}}]
    build = FighterBuild("mordheim", band_id="contract-band", profile_id="member", main_weapon_id="weapon.pistol")
    # The isolated root's pistol carries no blackpowder tag: a default-root
    # fallback would find the canonical tagged alias and refuse.
    assert validate("boundEquipment", build, _isolated_kb(tmp_path),
                    main_weapon_id="weapon.pistol", profile_bindings=binding) is None
    assert _catalogue("mordheim", "mordheim", tmp_path)["items"]["pistol"]["tags"] == []
