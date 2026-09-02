"""Regresiones vectorizadas de familias canónicas B."""
from __future__ import annotations

from mordheim_combat_lab.combat.vectorized import _new_state
from mordheim_combat_lab.combat.vectorized import _prepare_weapon_attack
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import FighterBuild
import numpy as np
from pathlib import Path
import pytest as pytest
import yaml as yaml


ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


class SequenceRng:
    def __init__(self, *values):
        self.values = iter(values)

    def integers(self, low, high=None, size=None, dtype=None):
        value = next(self.values)
        return np.full(size if size is not None else (), value, dtype=dtype or np.int64)


def test_no_scope_yes_rules_remain_without_an_implementation_family():
    pending = yaml.safe_load((ROOT / "catalog/rules/pending-canonical-families.yaml").read_text(encoding="utf-8"))
    implemented = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    assert pending["families"] == []
    assert implemented["summary"] == {"families": 66, "rules": 101, "kinds": {"compiler": 41, "mechanic": 20, "trait": 5}}


def test_mandatory_mutations_and_blessings_are_enforced():
    unmutated_possessed = compile_fighter(
        build("trollheim-cult-of-the-possessed", "the-possessed", collection="trollheim"), ROOT
    )
    assert "compiler.possessed-optional-zero-to-two-mutations-at-recruitment" in unmutated_possessed.construction_tags
    possessed = compile_fighter(build(
        "trollheim-cult-of-the-possessed", "the-possessed", collection="trollheim",
        special_rule_ids=("band--mutations-tentacle",),
    ), ROOT)
    assert "compiler.possessed-optional-zero-to-two-mutations-at-recruitment" in possessed.construction_tags

    with pytest.raises(ValueError, match="at least one Blessing"):
        compile_fighter(build("carnival-of-chaos", "tainted-ones"), ROOT)
    blessed = compile_fighter(build(
        "carnival-of-chaos", "tainted-ones",
        special_rule_ids=("band--blessings-of-nurgle-bloated-foulness",),
    ), ROOT)
    assert blessed.characteristics.toughness == 4


def test_construction_contracts_validate_and_expand_legal_builds():
    dwarf = compile_fighter(build("dwarf-rangers", "dwarf-clansmen"), ROOT)
    marksman = compile_fighter(build("gunnery-school-of-nuln", "marksmen"), ROOT)
    tracker = compile_fighter(build("lustria-savage-goblins", "trackers", collection="trollheim"), ROOT)
    liche = compile_fighter(build("restless-dead", "liche"), ROOT)
    assert "compiler.no-arcane-lore" in dwarf.construction_tags
    assert "compiler.quick-reload" in marksman.construction_tags
    assert "compiler.tracker-gear" in tracker.construction_tags
    assert "compiler.warrior-wizard" in liche.construction_tags

    ogre = compile_fighter(build("ostlanders", "ogre", skill_ids=("skill.mighty-blow",)), ROOT)
    assert ogre.global_effects.strength_bonus == 1
    duelist = compile_fighter(build("hochland-bandits", "duelist", main_weapon_id="weapon.flail"), ROOT)
    assert "compiler.weapon-knowledge" in duelist.construction_tags

    with pytest.raises(ValueError):
        compile_fighter(build("battle-monks-of-cathay", "dragon-monks", armour_id="armour.light-armour"), ROOT)


def test_proven_warrior_renowned_virtue_and_sacred_marks_are_validated():
    proven = compile_fighter(build(
        "black-orcs", "younguns", main_weapon_id="weapon.double-handed-weapon",
        special_rule_ids=("band--black-orc-special-skills-proven-warrior",),
    ), ROOT)
    assert "compiler.proven-warrior" in proven.construction_tags
    with pytest.raises(ValueError, match="Young'un"):
        compile_fighter(build(
            "black-orcs", "black-orc-boss",
            special_rule_ids=("band--black-orc-special-skills-proven-warrior",),
        ), ROOT)

    knight = compile_fighter(build(
        "bretonnian-chapel-guard", "questing-knight",
        special_rule_ids=("band--renowned-virtue", "band--virtue-of-valour"),
    ), ROOT)
    assert "skill.virtue-of-valour" in knight.global_effects.tags
    with pytest.raises(ValueError, match="at most one Sacred Mark"):
        compile_fighter(build(
            "lustria-lizardmen", "saurus-totem-warrior", collection="trollheim",
            special_rule_ids=("band--sacred-mark-huge-jaws", "band--sacred-mark-of-the-old-ones"),
        ), ROOT)


def test_scaly_skin_spawn_amazons_and_untiring_compile_to_combat_effects():
    skink = compile_fighter(build("lizardmen", "skink-priest"), ROOT)
    saurus = compile_fighter(build("lizardmen", "saurus-totem-warrior"), ROOT)
    assert (skink.natural_armour_save, skink.natural_armour_worst_save) == (6, 6)
    assert (saurus.natural_armour_save, saurus.natural_armour_worst_save) == (5, 6)

    spawn = compile_fighter(build("marauders-of-chaos", "spawn-of-chaos"), ROOT)
    amazon = compile_fighter(build("amazons-lustria", "eagle-warriors"), ROOT)
    untiring = compile_fighter(build(
        "bretonnian-chapel-guard", "questing-knight", armour_id="armour.heavy-armour",
        special_rule_ids=("band--untiring",),
    ), ROOT)
    assert "mechanic.spawn-special-attacks" in spawn.global_effects.tags
    assert "mechanic.amazon-isolationists" in amazon.global_effects.tags
    assert untiring.global_effects.armour_save_floor == 5
    assert untiring.global_effects.armour_cannot_be_ignored


def test_spider_infested_penalizes_misses_and_amazons_reroll_against_lizardmen():
    spider = compile_fighter(build(
        "lustria-savage-goblins", "big-boss", collection="trollheim",
        special_rule_ids=("band--savage-goblin-special-skills-spider-infested",),
    ), ROOT)
    attacker = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    attack_state, spider_state = _new_state(attacker, 1, SequenceRng(1)), _new_state(spider, 1, SequenceRng(1))
    _prepare_weapon_attack(attacker, spider, attacker.main_weapon, np.array([0]), np.array([False]),
                           attack_state, spider_state, SequenceRng(1), False)
    assert attack_state.initiative_penalty[0] == 1

    amazon = compile_fighter(build("amazons-lustria", "eagle-warriors"), ROOT)
    lizard = compile_fighter(build("lizardmen", "saurus-totem-warrior"), ROOT)
    amazon_state, lizard_state = _new_state(amazon, 1, SequenceRng(1)), _new_state(lizard, 1, SequenceRng(1))
    prepared = _prepare_weapon_attack(amazon, lizard, amazon.main_weapon, np.array([0]), np.array([False]),
                                      amazon_state, lizard_state, SequenceRng(1, 6), True)
    assert prepared is not None and prepared.hit_rows.tolist() == [0]
