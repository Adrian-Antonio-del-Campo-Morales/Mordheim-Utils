"""Familias canónicas compartidas del runtime vectorizado."""
from __future__ import annotations

from mordheim_combat_lab.combat.vectorized import OUT
from mordheim_combat_lab.combat.vectorized import STANDING
from mordheim_combat_lab.combat.vectorized import _critical_wound_threshold
from mordheim_combat_lab.combat.vectorized import _new_state
from mordheim_combat_lab.combat.vectorized import _rescue_force_of_will
from mordheim_combat_lab.combat.vectorized import _sustain_force_of_will
from mordheim_combat_lab.combat.vectorized import attack_count
from mordheim_combat_lab.combat.vectorized import priority
from mordheim_combat_lab.combat.vectorized import resolve_attacks
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import EffectSet
from mordheim_combat_lab.domain.models import FighterBuild
from mordheim_combat_lab.knowledge.loader import load_bands
from mordheim_combat_lab.knowledge.loader import runtime_bindings
import numpy as np
from pathlib import Path
import pytest as pytest
import yaml as yaml


ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"


class FixedRng:
    def __init__(self, value=6):
        self.value = value

    def integers(self, low, high=None, size=None, dtype=None):
        return np.full(size if size is not None else (), self.value, dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


def test_all_implemented_canonical_families_are_executable_for_every_member():
    document = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    assert document["summary"] == {"families": 66, "rules": 101, "kinds": {"compiler": 41, "mechanic": 20, "trait": 5}}
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
            assert {(binding["kind"], binding["id"]) for binding in runtime_bindings(rule)} == {
                (family["kind"], family["id"])
            }


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
        assert {(binding["kind"], binding["id"]) for binding in runtime_bindings(rule)} == {
            ("mechanic", "skill.art-of-silent-death")
        }


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
    import mordheim_combat_lab.combat.vectorized as engine
    original = engine._prepare_weapon_attack

    def record(*args, **kwargs):
        captured.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, "_prepare_weapon_attack", record)
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
    import mordheim_combat_lab.combat.vectorized as engine
    original = engine._prepare_weapon_attack

    def record(*args, **kwargs):
        captured.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(engine, "_prepare_weapon_attack", record)
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
