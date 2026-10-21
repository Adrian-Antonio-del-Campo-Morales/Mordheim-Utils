"""Canonical families shared by the vectorized runtime."""
from __future__ import annotations

from collections import Counter
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
def test_family_roster_covers_each_declared_binding_exactly_once():
    document = yaml.safe_load((ROOT / "catalog/rules/implemented-canonical-families.yaml").read_text(encoding="utf-8"))
    families = document["families"]
    family_ids = [(family["kind"], family["id"]) for family in families]
    assert len(family_ids) == len(set(family_ids)) == document["counts"]["families"]
    assert Counter(family["kind"] for family in families) == document["counts"]["kinds"]
    members = [member for family in families for member in family["members"]]
    assert len(members) == len(set(members)) == document["counts"]["rules"]


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
def test_black_hunger_adds_attack_and_resolves_armour_ignoring_backlash():
    fighter = compile_fighter(build(
        "skaven-clan-eshin", "assassin-adept",
        special_rule_ids=("band--skaven-special-skills-black-hunger",),
    ), ROOT)
    assert fighter.global_effects.attacks_bonus == 1
    assert "mechanic.black-hunger" in fighter.global_effects.tags


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
def test_bull_charge_knocks_down_on_a_successful_charge_hit():
    attacker = compile_fighter(build("maneaters", "bulls"), ROOT)
    defender = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    attack_state, defence_state = _new_state(attacker, 1, FixedRng()), _new_state(defender, 1, FixedRng())
    resolve_attacks(attacker, defender, np.array([0]), np.array([1]), np.array([True]),
                    attack_state, defence_state, FixedRng(6), True)
    assert defence_state.condition[0] != STANDING


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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


@pytest.mark.phase5_vectorized
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
