"""Rule regressions of the vectorized engine."""
from __future__ import annotations

from dataclasses import replace
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild
import numpy as np
import pytest as pytest


class FixedRng:
    def __init__(self, *values):
        self.values = list(values)

    def integers(self, low, high=None, size=None, dtype=None):
        if size == 0:
            return np.empty(0, dtype=dtype or np.int64)
        value = self.values.pop(0)
        result = np.asarray(value if np.ndim(value) else np.full(size or 1, value), dtype=dtype)
        return result if size is not None else result.item()


def build(*, attacks=1, strength=3, toughness=3, wounds=1, **changes):
    options = dict(
        ruleset="mordheim",
        characteristics=Characteristics(3, strength, toughness, wounds, 3, attacks),
    )
    options.update(changes)
    return compile_fighter(FighterBuild(**options))


def test_audited_weapon_contracts_expose_their_missing_numeric_effects():
    from mordheim_combat.vectorized import attack_count
    from mordheim_combat.vectorized import priority

    bagh = build(main_weapon_id="weapon.bagh-nakh")
    stiletto = build(main_weapon_id="weapon.stiletto")
    cathayan = build(main_weapon_id="weapon.cathayan-longsword")
    yari = build(main_weapon_id="weapon.yari-two-handed")
    hook = build(main_weapon_id="weapon.long-boat-hook")
    draich = build(main_weapon_id="weapon.draich")
    flags = np.zeros(1, dtype=bool)

    assert (bagh.main_weapon.strength_bonus, bagh.main_weapon.armour_penetration) == (1, 1)
    assert attack_count(stiletto, flags).tolist() == [2]
    assert cathayan.main_weapon.weapon_skill_bonus == 1
    assert priority(yari, build(), False, flags, flags, flags).tolist() == [1]
    assert priority(hook, build(), True, flags, flags, flags).tolist() == [1]
    assert priority(hook, build(), False, flags, flags, flags).tolist() == [0]
    assert draich.main_weapon.critical_injury_bonus == 1


@pytest.mark.parametrize(
    "weapon",
    (
        "weapon.morning-star",
        "weapon.spear",
        "weapon.broadsword",
        "weapon.squig-prodder",
        "weapon.boar-spear",
    ),
)
def test_restricted_weapons_reject_an_illegal_second_weapon(weapon):
    with pytest.raises(ValueError, match="cannot be combined"):
        build(main_weapon_id=weapon, off_hand_id="weapon.dagger")


def test_restricted_weapons_and_toughened_leathers_keep_legal_combinations():
    assert build(main_weapon_id="weapon.spear", off_hand_id="defence.buckler").off_hand is not None
    assert build(main_weapon_id="weapon.broadsword", off_hand_id="defence.shield").off_hand is not None
    assert build(main_weapon_id="weapon.squig-prodder", off_hand_id="weapon.spiked-gauntlet").off_hand is not None
    assert build(armour_id="armour.toughened-leathers", off_hand_id="defence.buckler").off_hand is not None
    with pytest.raises(ValueError, match="toughened leathers"):
        build(armour_id="armour.toughened-leathers", off_hand_id="defence.shield")


def test_frenzy_persists_and_pistols_only_fire_in_the_first_round():
    from mordheim_combat.vectorized import attack_count

    flags = np.zeros(1, dtype=bool)
    frenzy = build(preparation_ids=("preparation.mad-cap-mushrooms",))
    pistol = build(main_weapon_id="weapon.pistol")
    pistol_and_sword = build(main_weapon_id="weapon.pistol", off_hand_id="weapon.sword")
    sword_and_pistol = build(main_weapon_id="weapon.sword", off_hand_id="weapon.pistol", attacks=2)

    assert attack_count(frenzy, flags, first_round=False).tolist() == [2]
    assert attack_count(pistol, flags, first_round=True).tolist() == [1]
    assert attack_count(pistol, flags, first_round=False).tolist() == [0]
    assert attack_count(pistol_and_sword, flags, first_round=True).tolist() == [2]
    assert attack_count(pistol_and_sword, flags, first_round=False).tolist() == [1]
    assert attack_count(sword_and_pistol, flags, first_round=True).tolist() == [3]
    assert attack_count(sword_and_pistol, flags, first_round=False).tolist() == [2]


def test_pistol_and_sword_allocate_attacks_to_the_correct_weapon(monkeypatch):
    import mordheim_combat.vectorized as engine
    import mordheim_combat.vectorized._attacks as engine_attacks

    attacker = build(main_weapon_id="weapon.pistol", off_hand_id="weapon.sword")
    defender = build()
    flags = np.zeros(1, dtype=bool)
    seen = []

    def capture(_attacker, _defender, weapon, active, *_args, **_kwargs):
        if active.size:
            seen.append(weapon.tags)
        return None

    monkeypatch.setattr(engine_attacks, "_prepare_weapon_attack", capture)
    for first_round in (True, False):
        attacks = engine.attack_count(attacker, flags, first_round=first_round)
        engine.resolve_attacks(
            attacker, defender, np.array([0]), attacks, flags,
            engine._new_state(attacker, 1, np.random.default_rng(1)),
            engine._new_state(defender, 1, np.random.default_rng(2)),
            np.random.default_rng(3), first_round,
        )
    assert "weapon.pistol" in seen[0]
    assert "weapon.sword" in seen[1]
    assert "weapon.sword" in seen[2]
    assert len(seen) == 3


def test_resilient_and_reptile_venom_do_not_change_armour_strength():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack

    active = np.array([0])
    flags = np.zeros(1, dtype=bool)
    strong = build(strength=4)
    resilient = build(skill_ids=("skill.resilient",))
    reptile = build(main_poison_id="poison.reptile-venom")

    resilient_attack = _prepare_weapon_attack(
        strong, resilient, strong.main_weapon, active, flags,
        _new_state(strong, 1, np.random.default_rng(1)),
        _new_state(resilient, 1, np.random.default_rng(2)), FixedRng(6), False,
    )
    reptile_attack = _prepare_weapon_attack(
        reptile, build(), reptile.main_weapon, active, flags,
        _new_state(reptile, 1, np.random.default_rng(3)),
        _new_state(build(), 1, np.random.default_rng(4)), FixedRng(6), False,
    )

    assert resilient_attack.strength.tolist() == [3]
    assert resilient_attack.armour_strength.tolist() == [4]
    assert reptile_attack.strength.tolist() == [4]
    assert reptile_attack.armour_strength.tolist() == [3]


def test_automatic_wounds_cannot_claim_a_synthetic_critical():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    attacker = build(main_poison_id="poison.black-lotus")
    defender = build(wounds=2)
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    # Automatic wounds roll no wound die (the modular oracle returns roll 0 for
    # them), so the second die is the dagger-vs-no-armour 6+ save, rolled 1.
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(6, 1), False,
    )
    assert defender_state.wounds.tolist() == [1]
    assert not attacker_state.critical_used[0]


def test_duplicate_wounds_can_claim_only_one_critical_per_row():
    from mordheim_combat.vectorized import _claim_criticals
    from mordheim_combat.vectorized import _new_state

    state = _new_state(build(), 1, np.random.default_rng(1))
    claimed = _claim_criticals(np.array([True, True]), np.array([0, 0]), state)
    assert claimed.tolist() == [True, False]


def test_simultaneous_injuries_keep_the_highest_roll_instead_of_auto_finishing():
    from mordheim_combat.vectorized import KNOCKED_DOWN
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import resolve_attacks

    attacker = replace(build(attacks=2), main_weapon=EffectSet(automatic_hit=True))
    defender = build()
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    resolve_attacks(
        attacker, defender, np.array([0]), np.array([2]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(4, 1, 4, 1), False,
    )
    assert defender_state.condition.tolist() == [KNOCKED_DOWN]


def test_sword_and_buckler_rerolls_a_failed_parry():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits

    defender = build(main_weapon_id="weapon.sword", off_hand_id="defence.buckler")
    state = _new_state(defender, 1, np.random.default_rng(1))
    remaining, blocked, _ = _parry_hits(
        defender, EffectSet(), np.array([0]), np.array([4]), np.array([3]),
        state, FixedRng(3, 5),
    )
    assert remaining.size == 0
    assert blocked.tolist() == [0]


def test_offhand_axe_master_and_starblade_use_their_special_parries():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits

    axe_master = build(
        main_weapon_id="weapon.mace", off_hand_id="weapon.axe",
        skill_ids=("skill.axe-master",),
    )
    starblade = build(main_weapon_id="weapon.starblade")
    remaining, blocked, _ = _parry_hits(
        axe_master, EffectSet(), np.array([0]), np.array([4]), np.array([3]),
        _new_state(axe_master, 1, np.random.default_rng(1)), FixedRng(6),
    )
    assert remaining.size == 0 and blocked.tolist() == [0]
    remaining, blocked, _ = _parry_hits(
        starblade, EffectSet(), np.array([0]), np.array([5]), np.array([3]),
        _new_state(starblade, 1, np.random.default_rng(2)), FixedRng(4),
    )
    assert remaining.size == 0 and blocked.tolist() == [0]


def test_thick_skull_with_a_helmet_replaces_instead_of_stacking_with_helmet_save():
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    attacker = replace(build(), main_weapon=EffectSet(automatic_hit=True, fixed_strength=10))
    defender = build(defence_ids=("defence.helmet",), skill_ids=("skill.thick-skull",))
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    _resolve_weapon(
        attacker, defender, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        attacker_state, defender_state, FixedRng(5, 3, 1), False,
    )
    assert defender_state.condition.tolist() == [STUNNED]


def test_luck_is_consumed_after_its_first_failed_hit_reroll():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack

    attacker = build(skill_ids=("skill.luck",))
    defender = build()
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    active = np.array([0])
    flags = np.zeros(1, dtype=bool)

    first = _prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, active, flags,
        attacker_state, defender_state, FixedRng(3, 6), False,
    )
    second = _prepare_weapon_attack(
        attacker, defender, attacker.main_weapon, active, flags,
        attacker_state, defender_state, FixedRng(3), False,
    )
    assert first.hit_rows.tolist() == [0]
    assert second.hit_rows.size == 0
    assert attacker_state.luck_used.tolist() == [True]


def test_death_blow_bonuses_require_a_profile_with_at_least_two_attacks():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack
    from mordheim_combat.vectorized import attack_count

    one_attack = build(skill_ids=("mechanic.death-blow",))
    two_attacks = build(attacks=2, skill_ids=("mechanic.death-blow",))
    defender = build()
    active = np.array([0])
    flags = np.zeros(1, dtype=bool)

    inactive = _prepare_weapon_attack(
        one_attack, defender, one_attack.main_weapon, active, flags,
        _new_state(one_attack, 1, np.random.default_rng(1)),
        _new_state(defender, 1, np.random.default_rng(2)), FixedRng(6), False,
    )
    active_blow = _prepare_weapon_attack(
        two_attacks, defender, two_attacks.main_weapon, active, flags,
        _new_state(two_attacks, 1, np.random.default_rng(3)),
        _new_state(defender, 1, np.random.default_rng(4)), FixedRng(6), False,
    )
    assert (inactive.effect.hit_modifier, inactive.effect.wound_modifier, inactive.effect.injury_modifier) == (0, 0, 0)
    assert (active_blow.effect.hit_modifier, active_blow.effect.wound_modifier, active_blow.effect.injury_modifier) == (1, 1, 1)
    assert attack_count(two_attacks, flags).tolist() == [1]


def test_strongman_only_cancels_strike_last_for_two_handed_weapons():
    from mordheim_combat.vectorized import priority

    flags = np.zeros(1, dtype=bool)
    broadsword = build(main_weapon_id="weapon.broadsword", skill_ids=("skill.strongman",))
    great_weapon = build(main_weapon_id="weapon.double-handed-weapon", skill_ids=("skill.strongman",))
    assert priority(broadsword, build(), False, flags, flags, flags).tolist() == [-1]
    assert priority(great_weapon, build(), False, flags, flags, flags).tolist() == [0]


def test_shield_strike_is_an_independent_user_strength_attack():
    attacker = build(
        main_weapon_id="weapon.axe", off_hand_id="defence.shield",
        skill_ids=("skill.shield-strike",),
    )
    assert len(attacker.extra_attacks) == 1
    strike = attacker.extra_attacks[0]
    assert strike.tags == ("rule.shield-strike",)
    assert strike.strength_bonus == 0
    # Shield Strike follows the ordinary Strength-based armour modifier.
    assert strike.target_armour_bonus == 0


def test_sigmarite_hammer_gets_its_conditional_wound_bonus():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    attacker = build(main_weapon_id="weapon.sigmarite-hammer")
    attacker = replace(attacker, main_weapon=replace(attacker.main_weapon, automatic_hit=True))
    ordinary = build(toughness=5, wounds=2)
    undead = replace(ordinary, global_effects=EffectSet(tags=("undead_or_possessed",)))

    ordinary_state = _new_state(ordinary, 1, np.random.default_rng(1))
    undead_state = _new_state(undead, 1, np.random.default_rng(2))
    _resolve_weapon(
        attacker, ordinary, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(attacker, 1, np.random.default_rng(3)), ordinary_state, FixedRng(4), False,
    )
    _resolve_weapon(
        attacker, undead, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(attacker, 1, np.random.default_rng(4)), undead_state, FixedRng(4), False,
    )
    assert ordinary_state.wounds.tolist() == [2]
    assert undead_state.wounds.tolist() == [1]


def test_bear_hug_is_granted_automatically_by_the_trained_bear_profile():
    bear = compile_fighter(FighterBuild(
        "mordheim", band_id="kislevites", profile_id="trained-bear",
    ))
    assert bear.global_effects.bear_hug


def test_mandrake_toughness_bonus_is_present_in_runtime_characteristic_tests():
    from mordheim_combat.vectorized import _new_state

    prepared = build(preparation_ids=("preparation.mandrake-root",))
    state = _new_state(prepared, 2, np.random.default_rng(1))
    assert state.toughness.tolist() == [4, 4]


def test_off_hand_material_contributes_to_effective_initiative():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import effective_initiative

    ordinary = build(main_weapon_id="weapon.dagger", off_hand_id="weapon.sword")
    ithilmar = build(
        main_weapon_id="weapon.dagger", off_hand_id="weapon.sword",
        off_material_id="material.ithilmar",
    )
    ordinary_state = _new_state(ordinary, 1, np.random.default_rng(1))
    ithilmar_state = _new_state(ithilmar, 1, np.random.default_rng(2))

    assert effective_initiative(ithilmar, ithilmar_state).tolist() == [
        effective_initiative(ordinary, ordinary_state)[0] + 1
    ]


def test_poisonous_injury_belongs_to_attacker_and_respects_immunity():
    from mordheim_combat.vectorized import KNOCKED_DOWN
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon

    poisonous = replace(
        build(),
        main_weapon=EffectSet(
            tags=("poisonous_injury",), automatic_hit=True, fixed_strength=10,
        ),
    )
    ordinary = build()
    immune = replace(ordinary, global_effects=EffectSet(poison_immunity=True))

    ordinary_state = _new_state(ordinary, 1, np.random.default_rng(1))
    immune_state = _new_state(immune, 1, np.random.default_rng(2))
    _resolve_weapon(
        poisonous, ordinary, poisonous.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(poisonous, 1, np.random.default_rng(3)), ordinary_state,
        FixedRng(5, 2), False,
    )
    _resolve_weapon(
        poisonous, immune, poisonous.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(poisonous, 1, np.random.default_rng(4)), immune_state,
        FixedRng(5, 2), False,
    )

    assert ordinary_state.condition.tolist() == [STUNNED]
    assert immune_state.condition.tolist() == [KNOCKED_DOWN]


def test_amazon_isolationists_recognise_trollheim_lustria_lizardmen():
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack

    amazon = replace(build(), global_effects=EffectSet(tags=("mechanic.amazon-isolationists",)))
    lizard = replace(build(), global_effects=EffectSet(tags=("band.lustria-lizardmen",)))
    prepared = _prepare_weapon_attack(
        amazon, lizard, amazon.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
        _new_state(amazon, 1, np.random.default_rng(1)),
        _new_state(lizard, 1, np.random.default_rng(2)), FixedRng(3, 6), True,
    )
    assert prepared.hit_rows.tolist() == [0]


def test_optional_phase_plan_only_enables_reachable_stateful_phases():
    from mordheim_combat.vectorized import _optional_phase_plan

    ordinary = build()
    inert = _optional_phase_plan(ordinary, ordinary)
    assert not any(getattr(inert, name) for name in inert.__slots__)

    stateful = replace(
        ordinary,
        global_effects=EffectSet(tags=(
            "mechanic.force-of-will", "spines", "mechanic.netter",
            "mechanic.black-hunger",
        )),
        main_weapon=EffectSet(
            tags=("weapon.chained-squig",), ignition_threshold=4,
        ),
    )
    enabled = _optional_phase_plan(stateful, ordinary)
    assert enabled.first_force_of_will
    assert enabled.first_spines
    assert enabled.first_netter
    assert enabled.first_black_hunger
    assert enabled.first_entangle
    assert enabled.second_can_burn
    assert not enabled.first_can_burn
