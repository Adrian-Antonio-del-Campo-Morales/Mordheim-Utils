"""Canonical families shared by the vectorized runtime."""
from __future__ import annotations

from mordheim_combat.vectorized import KNOCKED_DOWN
from mordheim_combat.vectorized import OUT
from mordheim_combat.vectorized import STANDING
from mordheim_combat.vectorized import STUNNED
from mordheim_combat.vectorized import _critical_wound_threshold
from mordheim_combat.vectorized import _new_state
from mordheim_combat.vectorized import _rescue_force_of_will
from mordheim_combat.vectorized import _sustain_force_of_will
from mordheim_combat.vectorized import attack_count
from mordheim_combat.vectorized import priority
from mordheim_combat.vectorized import resolve_attacks
from mordheim_core.models import Characteristics
from mordheim_core.models import EffectSet
import numpy as np
import pytest as pytest


class FixedRng:
    def __init__(self, value=6):
        self.value = value

    def integers(self, low, high=None, size=None, dtype=None):
        return np.full(size if size is not None else (), self.value, dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses(vector_case):
    charging = np.zeros(1, dtype=bool)
    monks = vector_case("test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-0")
    monk_unarmed, monk_armed = monks.first, monks.second
    assert attack_count(monk_unarmed, charging)[0] == monk_unarmed.characteristics.attacks + 1
    assert attack_count(monk_armed, charging)[0] == monk_armed.characteristics.attacks
    assert any("weapon.fist" in attack.tags for attack in monk_armed.extra_attacks)

    variants = (
        (
            "test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-1",
            "test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-4",
        ),
        (
            "test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-2",
            "test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-5",
        ),
        (
            "test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-3",
            "test_shared_families/test_unarmed_fighting_and_eshin_mastery_have_their_exact_attack_bonuses-0-6",
        ),
    )
    for unarmed_key, claws_key in variants:
        unarmed = vector_case(unarmed_key).first
        claws = vector_case(claws_key).first
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


def test_black_hunger_adds_attack_and_resolves_armour_ignoring_backlash(vector_case):
    case = vector_case("test_shared_families/test_black_hunger_adds_attack_and_resolves_armour_ignoring_backlash-0-0")
    fighter = case.first
    # The printed +1 Attack is not a compiled bonus: the round driver applies
    # it on the bearer's own turn only, together with the end-of-turn backlash
    # (certified by ``mechanic-black-hunger/own-turn-attack-bonus``).
    assert fighter.global_effects.attacks_bonus == 0
    assert "mechanic.black-hunger" in fighter.global_effects.tags


def test_body_slam_and_bull_charge_replace_charge_attacks(monkeypatch, vector_case):
    case = vector_case("test_shared_families/test_body_slam_and_bull_charge_replace_charge_attacks-0-0")
    body = case.first
    # The same frozen bull profile used by its own charge case.
    bull = vector_case("test_shared_families/test_bull_charge_knocks_down_on_a_successful_charge_hit-0-0").first
    charging = np.array([True, False])
    assert attack_count(body, charging, True).tolist()[0] == 1
    assert attack_count(bull, charging, True).tolist()[0] == 1

    defender = case.second
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


def test_bull_charge_knocks_down_on_a_successful_charge_hit(vector_case):
    case = vector_case("test_shared_families/test_bull_charge_knocks_down_on_a_successful_charge_hit-0-0")
    attacker, defender = case.first, case.second
    attack_state, defence_state = _new_state(attacker, 1, FixedRng()), _new_state(defender, 1, FixedRng())
    resolve_attacks(attacker, defender, np.array([0]), np.array([1]), np.array([True]),
                    attack_state, defence_state, FixedRng(6), True)
    assert defence_state.condition[0] != STANDING


def test_force_of_will_rescues_once_and_then_requires_cumulative_tests(vector_case):
    case = vector_case("test_shared_families/test_force_of_will_rescues_once_and_then_requires_cumulative_tests-0-0")
    fighter = case.first
    state = _new_state(fighter, 1, FixedRng())
    state.condition[0] = OUT
    _rescue_force_of_will(fighter, state, np.array([0]), FixedRng(1))
    assert state.condition[0] == STANDING and state.wounds[0] == 1
    _sustain_force_of_will(fighter, state, FixedRng(6))
    assert state.condition[0] == OUT
    _rescue_force_of_will(fighter, state, np.array([0]), FixedRng(1))
    assert state.condition[0] == OUT


def test_unpredictable_marks_one_attack_unparryable(monkeypatch, vector_case):
    case = vector_case("test_shared_families/test_unpredictable_marks_one_attack_unparryable-0-0")
    attacker, defender = case.first, case.second
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


def test_skink_hunter_overrides_charge_priority_only_against_skinks(vector_case):
    case = vector_case("test_shared_families/test_skink_hunter_overrides_charge_priority_only_against_skinks-0-0")
    hunter, skink = case.first, case.second
    # The plain fighter is the frozen base shared with the bull-charge case.
    human = vector_case("test_shared_families/test_bull_charge_knocks_down_on_a_successful_charge_hit-0-0").second
    charging = np.array([False]); charged = np.array([True]); stood = np.array([False])
    assert priority(hunter, skink, True, charging, charged, stood)[0] == 20
    assert priority(hunter, human, True, charging, charged, stood)[0] < 20


class ScriptedRng:
    """A generator that returns a fixed script of dice, then repeats the last."""

    def __init__(self, values):
        self.values = list(values)
        self.index = 0

    def integers(self, low, high=None, size=None, dtype=None):
        count = 1 if size is None else int(np.prod(size))
        drawn = []
        for _ in range(count):
            drawn.append(self.values[min(self.index, len(self.values) - 1)])
            self.index += 1
        array = np.array(drawn, dtype=dtype or np.int64)
        return array.reshape(size) if size is not None else int(array[0])

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def synthetic(tags=(), weapon_tags=("weapon.sword",), wounds=3, weapon_skill=5,
             armour_save=7, weapon=None, **kwargs):
    from mordheim_core.models import CompiledFighter
    return CompiledFighter(
        "test:synthetic", Characteristics(weapon_skill, 3, 3, wounds, 3, 1),
        weapon if weapon is not None else EffectSet(tags=weapon_tags), None,
        EffectSet(tags=tags), armour_save, 7, 7,
        unarmed_weapon=EffectSet(tags=("weapon.fist",)), **kwargs,
    )


def _resolve(attacker, defender, rng, attacks=1):
    attack_state = _new_state(attacker, 1, ScriptedRng([6]))
    defence_state = _new_state(defender, 1, ScriptedRng([6]))
    resolve_attacks(
        attacker, defender, np.array([0]), np.array([attacks]), np.array([False]),
        attack_state, defence_state, rng, False,
    )
    return attack_state, defence_state


def test_ethereal_hit_save_and_killing_blow_intercept_the_hit():
    attacker = synthetic()
    ethereal = synthetic(tags=("mechanic.ethereal-hit-save",))
    # Hit roll 6, then the ethereal save 6 passes: the wound is intercepted.
    _, saved = _resolve(attacker, ethereal, ScriptedRng([6, 6]))
    assert saved.wounds[0] == 3
    # The same save fails on a 3 and the attack continues to wound.
    _, wounded = _resolve(attacker, ethereal, ScriptedRng([6, 3, 6, 1, 1]))
    assert wounded.wounds[0] < 3

    # A natural six wounds automatically under Killing Blow: no To Wound die is
    # drawn, so the scripted 1 that would fail the roll never applies.
    killer = synthetic(tags=("mechanic.killing-blow",))
    _, killed = _resolve(killer, synthetic(), ScriptedRng([6, 1, 1, 1, 1, 1]))
    assert killed.wounds[0] == 2
    _, plain = _resolve(synthetic(), synthetic(), ScriptedRng([6, 1, 1, 1, 1, 1]))
    assert plain.wounds[0] == 3


def test_wound_reactions_weaken_and_knock_down_their_own_row():
    torturer = synthetic(tags=("mechanic.torturer",))
    _, victim = _resolve(torturer, synthetic(), ScriptedRng([6]))
    assert victim.strength[0] == 2 and victim.torture_strength_loss[0] == 1

    # Titanic Strength: a failed wound still knocks down a standing opponent
    # unless its Strength test passes (a 6 always fails).
    titanic = synthetic(tags=("mechanic.titanic-strength",))
    _, failed = _resolve(titanic, synthetic(), ScriptedRng([6, 1, 6]))
    assert failed.condition[0] == KNOCKED_DOWN
    _, resisted = _resolve(titanic, synthetic(), ScriptedRng([6, 1, 1]))
    assert resisted.condition[0] == STANDING

    # Hard to Rattle improves the helmet reaction to 4+, turning the injury's
    # Stunned result into Knocked Down; without it the same roll stays Stunned.
    _, stunned = _resolve(synthetic(), synthetic(wounds=1), ScriptedRng([4]))
    assert stunned.condition[0] == STUNNED
    _, rattled = _resolve(
        synthetic(), synthetic(tags=("mechanic.hard-to-rattle",), wounds=1), ScriptedRng([4]),
    )
    assert rattled.condition[0] == KNOCKED_DOWN

    # Spectral Touch: the natural six resolves one extra wound through the
    # saves before the attack's own (failed) To Wound roll.
    _, touched = _resolve(synthetic(tags=("trait.spectral-touch",)), synthetic(), ScriptedRng([6, 1, 1]))
    assert touched.wounds[0] == 2
    _, untouched = _resolve(synthetic(), synthetic(), ScriptedRng([6, 1, 1]))
    assert untouched.wounds[0] == 3

    # Wraith Touch wounds automatically (no To Wound die is drawn, so the
    # scripted 1 never applies) and has no effect at all on the Undead.
    wraith = synthetic(weapon=EffectSet(
        tags=("weapon.fist", "effect.wraith-touch", "effect.no-critical"),
        strength_bonus=-1, target_armour_bonus=1,
    ))
    _, wraith_wounded = _resolve(wraith, synthetic(), ScriptedRng([6, 1]))
    assert wraith_wounded.wounds[0] == 2
    _, wraith_warded = _resolve(wraith, synthetic(tags=("nature.undead",)), ScriptedRng([6, 1]))
    assert wraith_warded.wounds[0] == 3


def test_parry_and_armour_corrections_follow_the_modular_contract():
    # Eshin Assassin robes reroll a failed armour save; the second result stands.
    robed = synthetic(tags=("armour.eshin-assassin-robes",), armour_save=4)
    _, saved = _resolve(synthetic(), robed, ScriptedRng([6, 6, 2, 1, 6]))
    assert saved.wounds[0] == 3
    _, plain = _resolve(synthetic(), synthetic(armour_save=4), ScriptedRng([6, 6, 2, 1, 6]))
    assert plain.wounds[0] < 3

    # A successful parry with a sword-breaker traps the blow on 4+ and breaks
    # the attacking hand on its own row.
    breaker = synthetic(weapon=EffectSet(
        tags=("weapon.sword", "weapon.sword-breaker"), parry=True,
    ))
    attacker_state, _ = _resolve(synthetic(), breaker, ScriptedRng([4, 5, 4]))
    assert attacker_state.broken_hands[0] & 1
    intact_state, _ = _resolve(synthetic(), synthetic(), ScriptedRng([4, 5, 4]))
    assert not intact_state.broken_hands[0]

    # Chosen of the White Tower parries without a parrying weapon: the modular
    # capacity grants the attempt the shared helper does not seed.
    white_tower = synthetic(tags=("skill.chosen-of-the-white-tower",))
    _, blocked = _resolve(synthetic(), white_tower, ScriptedRng([4, 5]))
    assert blocked.wounds[0] == 3
    _, unblocked = _resolve(synthetic(), synthetic(), ScriptedRng([4, 5]))
    assert unblocked.wounds[0] < 3
    # A second pool in the same round must not replenish a spent parry.
    attack_state, defence_state = _new_state(synthetic(), 1, ScriptedRng([4, 5])), _new_state(
        white_tower, 1, ScriptedRng([4, 5]))
    for _ in range(2):
        resolve_attacks(
            synthetic(), white_tower, np.array([0]), np.array([1]), np.array([False]),
            attack_state, defence_state, ScriptedRng([4, 5]), False,
        )
    assert defence_state.wounds[0] < 3


def test_phase_resources_reroll_one_hit_per_row():
    # Seaguard Spear Master: the failed opening-round hit is rerolled once and
    # the phase resource is spent.
    spearman = synthetic(weapon_skill=1, tags=("mechanic.seaguard-spear-master",),
                         weapon=EffectSet(tags=("weapon.spear",)))
    attack_state = _new_state(spearman, 1, ScriptedRng([3]))
    defence_state = _new_state(synthetic(), 1, ScriptedRng([6]))
    resolve_attacks(
        spearman, synthetic(), np.array([0]), np.array([1]), np.array([False]),
        attack_state, defence_state, ScriptedRng([3, 6, 6]), True,
    )
    assert defence_state.wounds[0] < 3
    assert attack_state.seaguard_used[0]

    # A die Hatred already rerolled is not repeated: 1 -> 1 still fails and the
    # spear's resource stays available for a later miss.
    hatful = synthetic(weapon_skill=5,
                       tags=("mechanic.seaguard-spear-master", "skill.hatred"),
                       weapon=EffectSet(tags=("weapon.spear",)))
    attack_state = _new_state(hatful, 1, ScriptedRng([3]))
    defence_state = _new_state(synthetic(), 1, ScriptedRng([6]))
    resolve_attacks(
        hatful, synthetic(), np.array([0]), np.array([1]), np.array([False]),
        attack_state, defence_state, ScriptedRng([1, 1, 6]), True,
    )
    assert defence_state.wounds[0] == 3
    assert not attack_state.seaguard_used[0]

    # Corruption: the defender forces the successful hit to be rerolled and
    # the new miss stands; the resource is spent once.
    attacker, corrupted = synthetic(), synthetic(tags=("mechanic.corruption",))
    attack_state = _new_state(attacker, 1, FixedRng())
    defence_state = _new_state(corrupted, 1, FixedRng())
    resolve_attacks(
        attacker, corrupted, np.array([0]), np.array([1]), np.array([False]),
        attack_state, defence_state, ScriptedRng([6, 1]), False,
    )
    assert defence_state.wounds[0] == 3
    assert defence_state.corruption_used[0]

    # Corruption does not repeat a hit Hatred's reroll restored either.
    hatful = synthetic(tags=("skill.hatred",))
    attack_state = _new_state(hatful, 1, FixedRng())
    defence_state = _new_state(corrupted, 1, FixedRng())
    resolve_attacks(
        hatful, corrupted, np.array([0]), np.array([1]), np.array([False]),
        attack_state, defence_state, ScriptedRng([1, 6, 4]), True,
    )
    assert defence_state.wounds[0] == 2
    assert not defence_state.corruption_used[0]


def test_honorable_skips_helpless_targets_and_onslaught_extends_the_pool(monkeypatch):
    import mordheim_combat.vectorized._attacks as engine_attacks
    original = engine_attacks._prepare_weapon_attack
    captured = []

    def record(*args, **kwargs):
        captured.append(args[2])
        return original(*args, **kwargs)

    monkeypatch.setattr(engine_attacks, "_prepare_weapon_attack", record)
    # A natural six on the first hit earns exactly one more attack; that one
    # rolls a 3 against target 4 and earns nothing further.
    _resolve(synthetic(tags=("mechanic.ravening-onslaught",)), synthetic(), ScriptedRng([6, 3]))
    assert len(captured) == 2
    captured.clear()
    _resolve(synthetic(), synthetic(), ScriptedRng([6, 3]))
    assert len(captured) == 1
    captured.clear()

    # Honorable: the bearer does not strike a Knocked Down opponent at all.
    attacker, defender = synthetic(tags=("mechanic.honorable",)), synthetic()
    attack_state, defence_state = _new_state(attacker, 1, FixedRng()), _new_state(defender, 1, FixedRng())
    defence_state.condition[0] = KNOCKED_DOWN
    resolve_attacks(
        attacker, defender, np.array([0]), np.array([1]), np.array([False]),
        attack_state, defence_state, FixedRng(6), False,
    )
    assert defence_state.wounds[0] == defence_state.starting_wounds[0]
    assert not captured


def test_equipment_loss_and_festooned_pistols_are_projected_per_row():
    from mordheim_core.models import CarriedEquipment
    from mordheim_combat.vectorized._equipment import equipment_for_rows, phase_equipment

    backup = synthetic(mutation_equipment=(
        CarriedEquipment("backup-axe", EffectSet(tags=("weapon.axe",)), "weapon"),
    ))
    assert phase_equipment(backup, first_round=True).main_weapon.tags == ("weapon.sword",)
    lost = phase_equipment(backup, first_round=True, broken_hands=1)
    assert lost.main_hand_slot == "backup.0" and "weapon.axe" in lost.main_weapon.tags

    # The broken hand is one simulation's own state: the other row keeps its
    # printed sword and only the affected row draws the carried backup.
    state = _new_state(backup, 2, FixedRng())
    state.broken_hands[1] = 1
    projected = equipment_for_rows(backup, state, np.array([0, 1]), first_round=True)
    assert projected[0].main_hand_slot == "main"
    assert projected[0].main_weapon.tags == ("weapon.sword",)
    assert projected[1].main_hand_slot == "backup.0"

    festooned = synthetic(tags=("mechanic.festooned-with-pistols",), weapon_tags=("weapon.pistol",))
    club = phase_equipment(festooned, first_round=False).main_weapon
    assert "weapon.mace" in club.tags and club.concussion
    discarded = phase_equipment(synthetic(weapon_tags=("weapon.pistol",)), first_round=False)
    assert "weapon.mace" not in discarded.main_weapon.tags
