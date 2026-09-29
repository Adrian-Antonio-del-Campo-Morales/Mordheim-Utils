"""Canonical families shared by the vectorized runtime."""
from __future__ import annotations

from collections import Counter
from mordheim_combat.vectorized import OUT
from mordheim_combat.vectorized import STANDING
from mordheim_combat.vectorized import _critical_wound_threshold
from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _rescue_force_of_will
from mordheim_combat.vectorized import _sustain_force_of_will
from mordheim_combat.vectorized import attack_count
from mordheim_combat.vectorized import priority
from mordheim_combat.vectorized import resolve_attacks
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import runtime_bindings
import json as json
import numpy as np
from pathlib import Path
import pytest as pytest
import yaml as yaml


ROOT = Path(__file__).resolve().parents[4] / "sources/knowledge"


class FixedRng:
    def __init__(self, value=6):
        self.value = value

    def integers(self, low, high=None, size=None, dtype=None):
        return np.full(size if size is not None else (), self.value, dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


def _family_binding(rule: dict, kind: str, family_id: str, member: str = "member") -> dict:
    """Return the family's own binding, or fail naming the contract violation.

    The family id names exactly one combat binding (``compiler.*``,
    ``mechanic.*`` or ``trait.*``): the catalogue is the membership contract of
    that binding, not an inventory of every binding a member rule carries.
    Construction obligations (``profile.*``) belong to warband construction and
    have their own owners (T06 effect matrix, T09 contracts), so an additional
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
    assert document["counts"] == {"families": 66, "rules": 101, "kinds": {"compiler": 41, "mechanic": 20, "trait": 5}}
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
            _family_binding(rule, family["kind"], family["id"], member)
            carried = {(binding["kind"], binding["id"]) for binding in runtime_bindings(rule)}
            # No additional binding of the family's own kind: a second compiler,
            # mechanic or trait binding would make family membership ambiguous.
            additional = carried - {(family["kind"], family["id"])}
            assert all(kind != family["kind"] for kind, _ in additional), (
                f"{member}: additional same-kind bindings shadow the family: {sorted(additional)}"
            )


def test_family_binding_lookup_accepts_only_the_family_contract():
    kind, family_id = "compiler", "compiler.bow-discipline"

    def rule_with(*bindings):
        return {"runtime": {"implemented": "YES", "effects": [
            {"id": binding["id"], "binding": binding} for binding in bindings
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


def test_family_roster_covers_each_declared_binding_exactly_once():
    document = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    families = document["families"]
    family_ids = [(family["kind"], family["id"]) for family in families]
    assert len(family_ids) == len(set(family_ids)) == document["counts"]["families"]
    assert Counter(family["kind"] for family in families) == document["counts"]["kinds"]
    members = [member for family in families for member in family["members"]]
    assert len(members) == len(set(members)) == document["counts"]["rules"]


def test_bow_discipline_keeps_both_of_its_declared_bindings():
    """Bow Discipline owns a combat contract and a construction obligation.

    The compiler binding (``compiler.bow-discipline``) is the family's own
    executable contract — the one T13's Combat Simulator consumes; the profile
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


def test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses():
    charging = np.zeros(1, dtype=bool)
    monk_unarmed = compile_fighter(build(
        "battle-monks-of-cathay", "dragon-monks", main_weapon_id="weapon.fist",
    ), ROOT)
    monk_armed = compile_fighter(build(
        "battle-monks-of-cathay", "dragon-monks", main_weapon_id="weapon.quarter-staff",
    ), ROOT)
    assert attack_count(monk_unarmed, charging)[0] == monk_unarmed.characteristics.attacks + 1
    assert attack_count(monk_armed, charging)[0] == monk_armed.characteristics.attacks
    assert any("weapon.fist" in attack.tags for attack in monk_armed.extra_attacks)

    cases = (
        ("skaven-clan-eshin", "assassin-adept", "mordheim", "band--skaven-special-skills-art-of-silent-death"),
        ("trollheim-skaven-clan-eshin", "assassin-adept", "trollheim", "band--skaven-special-skills-art-of-silent-death"),
        ("chaos-streets-deathbringers", "shadow-blade", "trollheim", "band--deathbringer-special-skills-art-of-unarmed-combat"),
    )
    for band_id, profile_id, collection, rule_id in cases:
        unarmed = compile_fighter(build(
            band_id, profile_id, collection=collection, main_weapon_id="weapon.fist",
            special_rule_ids=(rule_id,),
        ), ROOT)
        claws = compile_fighter(build(
            band_id, profile_id, collection=collection, main_weapon_id="weapon.fighting-claws",
            special_rule_ids=(rule_id,),
        ), ROOT)
        assert attack_count(unarmed, charging)[0] == unarmed.characteristics.attacks + 1
        assert attack_count(claws, charging)[0] == claws.characteristics.attacks + 2


def test_art_of_silent_death_criticals_are_always_resolved_on_to_wound():
    natural = EffectSet(tags=("weapon.natural-attacks",))
    fist = EffectSet(tags=("weapon.fist",))
    dagger = EffectSet(tags=("weapon.dagger",))
    eshin = EffectSet(tags=("skill.art-of-silent-death",))
    cathay = EffectSet(tags=("skill.unarmed-critical-strikes",))
    assert _critical_wound_threshold(eshin, natural, False) == 5
    assert _critical_wound_threshold(eshin, dagger, False) == 5
    assert _critical_wound_threshold(cathay, fist, False) == 5
    assert _critical_wound_threshold(cathay, dagger, False) == 6


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


def test_black_hunger_adds_attack_and_resolves_armour_ignoring_backlash():
    fighter = compile_fighter(build(
        "skaven-clan-eshin", "assassin-adept",
        special_rule_ids=("band--skaven-special-skills-black-hunger",),
    ), ROOT)
    assert fighter.global_effects.attacks_bonus == 1
    assert "mechanic.black-hunger" in fighter.global_effects.tags


def test_body_slam_and_bull_charge_replace_charge_attacks(monkeypatch):
    body = compile_fighter(build(
        "pit-fighters", "pit-king",
        special_rule_ids=("band--pit-fighter-skill-body-slam",),
    ), ROOT)
    bull = compile_fighter(build("maneaters", "bulls"), ROOT)
    charging = np.array([True, False])
    assert attack_count(body, charging, True).tolist()[0] == 1
    assert attack_count(bull, charging, True).tolist()[0] == 1

    defender = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    state1, state2 = _new_state(body, 1, FixedRng()), _new_state(defender, 1, FixedRng())
    captured = []
    import mordheim_combat.vectorized._attacks as engine_attacks
    original = engine_attacks._prepare_weapon_attack

    def record(*args, **kwargs):
        captured.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_attacks, "_prepare_weapon_attack", record)
    resolve_attacks(body, defender, np.array([0]), np.array([1]), np.array([True]), state1, state2, FixedRng(6), True)
    slam = next(effect for effect in captured if "mechanic.body-slam" in effect.tags)
    assert slam.strength_bonus == 1 and slam.hit_modifier == 1


def test_bull_charge_knocks_down_on_a_successful_charge_hit():
    attacker = compile_fighter(build("maneaters", "bulls"), ROOT)
    defender = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    attack_state, defence_state = _new_state(attacker, 1, FixedRng()), _new_state(defender, 1, FixedRng())
    resolve_attacks(attacker, defender, np.array([0]), np.array([1]), np.array([True]),
                    attack_state, defence_state, FixedRng(6), True)
    assert defence_state.condition[0] != STANDING


def test_force_of_will_rescues_once_and_then_requires_cumulative_tests():
    fighter = compile_fighter(build(
        "pit-fighters", "pit-king",
        special_rule_ids=("band--pit-fighter-skill-force-of-will",),
    ), ROOT)
    state = _new_state(fighter, 1, FixedRng())
    state.condition[0] = OUT
    _rescue_force_of_will(fighter, state, np.array([0]), FixedRng(1))
    assert state.condition[0] == STANDING and state.wounds[0] == 1
    _sustain_force_of_will(fighter, state, FixedRng(6))
    assert state.condition[0] == OUT
    _rescue_force_of_will(fighter, state, np.array([0]), FixedRng(1))
    assert state.condition[0] == OUT


def test_unpredictable_marks_one_attack_unparryable(monkeypatch):
    attacker = compile_fighter(build(
        "khemri-hobgoblin-raiders", "sneaky", collection="trollheim",
    ), ROOT)
    defender = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    state1, state2 = _new_state(attacker, 1, FixedRng()), _new_state(defender, 1, FixedRng())
    captured = []
    import mordheim_combat.vectorized._attacks as engine_attacks
    original = engine_attacks._prepare_weapon_attack

    def record(*args, **kwargs):
        captured.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_attacks, "_prepare_weapon_attack", record)
    resolve_attacks(attacker, defender, np.array([0]), np.array([1]), np.array([False]),
                    state1, state2, FixedRng(6), False)
    assert captured[0].cannot_be_parried


def test_skink_hunter_overrides_charge_priority_only_against_skinks():
    hunter = compile_fighter(build(
        "amazons-lustria", "serpent-priestess",
        special_rule_ids=("band--amazon-special-skills-skink-hunter",),
    ), ROOT)
    skink = compile_fighter(build("lizardmen", "skink-priest"), ROOT)
    human = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    charging = np.array([False]); charged = np.array([True]); stood = np.array([False])
    assert priority(hunter, skink, True, charging, charged, stood)[0] == 20
    assert priority(hunter, human, True, charging, charged, stood)[0] < 20


def test_shared_compiler_contracts_enforce_construction_rules():
    with pytest.raises(ValueError, match="poisons are forbidden"):
        compile_fighter(build(
            "battle-monks-of-cathay", "dragon-monks", main_poison_id="poison.black-lotus",
        ), ROOT)
    with pytest.raises(ValueError, match="drugs are forbidden"):
        compile_fighter(build(
            "lustria-high-elves", "sword-guardians", collection="trollheim",
            preparation_ids=("preparation.crimson-shade",),
        ), ROOT)
    antidote = compile_fighter(build(
        "lustria-high-elves", "sword-guardians", collection="trollheim",
        preparation_ids=("preparation.tears-of-shallaya",),
    ), ROOT)
    assert antidote.global_effects.poison_immunity

    with pytest.raises(ValueError, match="at least one mutation"):
        compile_fighter(build("cult-of-the-possessed", "mutants"), ROOT)
    mutant = compile_fighter(build(
        "cult-of-the-possessed", "mutants",
        special_rule_ids=("band--mutations-tentacle",),
    ), ROOT)
    assert mutant.global_effects.incoming_attacks_modifier == -1


def test_arms_master_censer_bearer_skill_access_and_pit_fighter_trait():
    with pytest.raises(ValueError, match="occupies both hands"):
        compile_fighter(build(
            "pit-fighters", "pit-king", main_weapon_id="weapon.flail", off_hand_id="weapon.dagger",
        ), ROOT)
    arms_master = compile_fighter(build(
        "pit-fighters", "pit-king", main_weapon_id="weapon.flail", off_hand_id="weapon.dagger",
        special_rule_ids=("band--pit-fighter-skill-arms-master",),
    ), ROOT)
    assert arms_master.off_hand_attacks

    with pytest.raises(ValueError, match="requires Black Hunger"):
        compile_fighter(build(
            "skaven-clan-pestilens", "plague-priest", main_weapon_id="weapon.censer",
            special_rule_ids=("band--clan-pestilens-special-skills-censer-bearer",),
        ), ROOT)
    bearer = compile_fighter(build(
        "skaven-clan-pestilens", "plague-priest", main_weapon_id="weapon.censer",
        special_rule_ids=(
            "band--clan-pestilens-special-skills-black-hunger",
            "band--clan-pestilens-special-skills-censer-bearer",
        ),
    ), ROOT)
    assert bearer.global_effects.frenzy

    ogre = compile_fighter(build(
        "pit-fighters", "ogre-pit-fighter", skill_ids=("skill.mighty-blow",),
    ), ROOT)
    assert ogre.global_effects.strength_bonus == 1
    assert "pit_fighter" in arms_master.global_effects.tags
