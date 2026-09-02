"""Regresiones vectorizadas de familias canónicas A."""
from __future__ import annotations

from mordheim_combat_lab.combat.vectorized import _new_state
from mordheim_combat_lab.combat.vectorized import _prepare_weapon_attack
from mordheim_combat_lab.combat.vectorized import attack_count
from mordheim_combat_lab.combat.vectorized import resolve_attacks
from mordheim_combat_lab.combat.vectorized import simulate_duel
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import DuelRequest
from mordheim_combat_lab.domain.models import FighterBuild
import numpy as np
from pathlib import Path
import pytest as pytest
import yaml as yaml


ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"


class FixedRng:
    def __init__(self, value: int):
        self.value = value

    def integers(self, low, high=None, size=None, dtype=None):
        return np.full(size if size is not None else (), self.value, dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


def test_first_25_pending_families_moved_to_the_executable_catalogue():
    pending = yaml.safe_load((ROOT / "catalog/rules/pending-canonical-families.yaml").read_text(encoding="utf-8"))
    implemented = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    assert pending["summary"]["families"] == 0
    assert implemented["summary"]["families"] == 66
    assert implemented["summary"]["rules"] == 101


def test_animal_friendship_and_contagious_traits_are_selectable_and_enforce_prerequisites():
    friend = compile_fighter(build(
        "horned-hunters", "horned-hunter",
        special_rule_ids=("band--horned-hunter-special-skills-animal-friendship",),
    ), ROOT)
    assert "animal_friendship" in friend.global_effects.tags

    with pytest.raises(ValueError, match="requires Rotten Body"):
        compile_fighter(build(
            "lustria-clan-pestilens", "plague-priest", collection="trollheim",
            special_rule_ids=("band--clan-pestilens-special-skills-contagious",),
        ), ROOT)
    contagious = compile_fighter(build(
        "lustria-clan-pestilens", "plague-priest", collection="trollheim",
        special_rule_ids=(
            "band--clan-pestilens-special-skills-rotten-body",
            "band--clan-pestilens-special-skills-contagious",
        ),
    ), ROOT)
    assert "contagious" in contagious.global_effects.tags


def test_anvil_head_death_blow_energy_focus_and_mark_are_executable_combat_choices():
    anvil = compile_fighter(build(
        "khemri-necromancers", "necromantic-abomination", collection="trollheim",
        special_rule_ids=("band--necromantic-modification-anvil-head",),
    ), ROOT)
    death = compile_fighter(build(
        "chaos-streets-deathbringers", "shadow-blade", collection="trollheim",
        special_rule_ids=("band--deathbringer-special-skills-death-blow",),
    ), ROOT)
    energy = compile_fighter(build(
        "battle-monks-of-cathay", "dragon-monks",
        characteristics=Characteristics(4, 3, 3, 1, 4, 3),
        main_weapon_id="weapon.fist",
        special_rule_ids=("band--battle-monks-special-skills-energy-focus",),
        energy_focus_attacks=2,
    ), ROOT)
    mark = compile_fighter(build(
        "lustria-lizardmen", "skink-priest", collection="trollheim",
        special_rule_ids=("band--sacred-mark-of-the-old-ones",),
    ), ROOT)
    charging = np.array([True])
    assert attack_count(anvil, charging, True)[0] == 1
    assert attack_count(death, charging, True)[0] == 1
    assert attack_count(energy, charging, True)[0] == 2
    assert energy.global_effects.energy_focus_attacks == 2
    assert "mechanic.mark-of-the-old-ones" in mark.global_effects.tags
    assert death.global_effects.hit_modifier == death.global_effects.wound_modifier == death.global_effects.injury_modifier == 1


def test_disability_guardian_unarmed_and_onogal_have_observable_runtime_effects():
    cripple = compile_fighter(build(
        "chaos-streets-mordheim-inhabitants", "cripples", collection="trollheim",
    ), ROOT)
    state = _new_state(cripple, 1, FixedRng(4))
    assert state.disability[0] == 4
    assert state.toughness[0] == max(1, cripple.characteristics.toughness - 1)

    guardian = compile_fighter(build("carnival-of-chaos", "plague-cart"), ROOT)
    assert "guardian_unarmed" in guardian.global_effects.tags

    marked = compile_fighter(build(
        "marauders-of-chaos", "marauder-chieftain",
        special_rule_ids=("band--mark-of-onogal",),
    ), ROOT)
    assert marked.characteristics.toughness == 5
    assert marked.global_effects.poison_immunity


def test_construction_contracts_enforce_access_restrictions_and_limits():
    outlaw = compile_fighter(build("outlaws-of-stirwood-forest", "bandit-leader"), ROOT)
    tracker = compile_fighter(build(
        "lustria-savage-goblins", "trackers", collection="trollheim",
        special_rule_ids=("band--savage-goblin-special-skills-master-of-throwing-weapons",),
    ), ROOT)
    assert outlaw.missile_weapon_limit == 1
    assert tracker.missile_weapon_limit == 5

    with pytest.raises(ValueError, match="poisons are forbidden for Knights"):
        compile_fighter(build(
            "bretonnian-chapel-guard", "questing-knight",
            main_poison_id="poison.black-lotus",
        ), ROOT)
    # La eleccion de tribu pertenece a la construccion de la banda y a la
    # campana (incluidas opciones montadas), no al constructor de duelos 1v1.
    with pytest.raises(ValueError, match="choose exactly one Foreign or Native background"):
        compile_fighter(build(
            "khemri-lahmian-brotherhood", "lahmian-vampire", collection="trollheim",
            variant_ids=("background.foreign", "background.native"),
        ), ROOT)


def test_pirate_mercenary_access_master_of_arms_and_mutation_contracts():
    pirate = compile_fighter(build(
        "lustria-pirates", "pirate-captain", collection="trollheim",
        armour_id="armour.heavy-armour",
    ), ROOT)
    assert pirate.armour_save <= 5

    ogre = compile_fighter(build(
        "maneaters", "captain", main_weapon_id="weapon.double-handed-weapon", off_hand_id="weapon.sword",
        special_rule_ids=("band--ogres-special-skills-master-of-arms",),
    ), ROOT)
    assert ogre.off_hand_attacks

    with pytest.raises(ValueError, match="at least one mutation"):
        compile_fighter(build("cult-of-the-possessed", "mutants"), ROOT)
    possessed = compile_fighter(build(
        "cult-of-the-possessed", "mutants",
        special_rule_ids=("band--mutations-tentacle",),
    ), ROOT)
    assert possessed.global_effects.incoming_attacks_modifier == -1


def test_remaining_meta_contracts_compile_for_their_legal_profiles():
    builds = (
        build("carnival-of-chaos", "tainted-ones", special_rule_ids=("band--blessings-of-nurgle-bloated-foulness",)),
        build("black-dwarfs", "sorcerer", special_rule_ids=("band--chaos-dwarf-special-skills-chaos-engineer",)),
        build("chaos-streets-undead-bloodlines", "von-carstein-vampire", collection="trollheim"),
        build("outlaws-of-stirwood-forest", "cleric"),
        build("lustria-high-elves", "sword-guardians", collection="trollheim"),
        build("bretonnian-chapel-guard", "squires"),
    )
    assert all(compile_fighter(candidate, ROOT) for candidate in builds)


def test_animal_friendship_prevents_normal_animals_from_attacking_in_the_duel():
    friend = compile_fighter(build(
        "horned-hunters", "horned-hunter",
        special_rule_ids=("band--horned-hunter-special-skills-animal-friendship",),
    ), ROOT)
    animal = compile_fighter(build(
        "khemri-lahmian-brotherhood", "black-hounds", collection="trollheim",
        variant_ids=("background.foreign",),
    ), ROOT)
    assert "species.animal" in animal.global_effects.tags
    result = simulate_duel(DuelRequest(friend, animal, 40, seed=12, maximum_rounds=20))
    assert result.second_wins == 0


def test_contagious_retaliates_and_mark_of_old_ones_is_spent_only_once():
    contagious = compile_fighter(build(
        "lustria-clan-pestilens", "plague-priest", collection="trollheim",
        special_rule_ids=(
            "band--clan-pestilens-special-skills-rotten-body",
            "band--clan-pestilens-special-skills-contagious",
        ),
    ), ROOT)
    attacker = compile_fighter(FighterBuild("mordheim", Characteristics(6, 10, 3, 2, 6, 1)), ROOT)
    attack_state, defence_state = _new_state(attacker, 1, FixedRng(6)), _new_state(contagious, 1, FixedRng(6))
    resolve_attacks(attacker, contagious, np.array([0]), np.array([1]), np.array([False]),
                    attack_state, defence_state, FixedRng(6), False)
    assert attack_state.wounds[0] == 1

    marked = compile_fighter(build(
        "lustria-lizardmen", "skink-priest", collection="trollheim",
        special_rule_ids=("band--sacred-mark-of-the-old-ones",),
    ), ROOT)
    target = compile_fighter(FighterBuild("mordheim", Characteristics(6, 3, 3, 1, 3, 1)), ROOT)
    marked_state, target_state = _new_state(marked, 1, FixedRng(1)), _new_state(target, 1, FixedRng(1))
    first = _prepare_weapon_attack(marked, target, marked.main_weapon, np.array([0]), np.array([False]),
                                   marked_state, target_state, FixedRng(1), False)
    second = _prepare_weapon_attack(marked, target, marked.main_weapon, np.array([0]), np.array([False]),
                                    marked_state, target_state, FixedRng(1), False)
    assert first is not None and first.hit_rows.tolist() == [0]
    assert second is not None and second.hit_rows.size == 0
