"""T13-F073: runtime classification of the catalogued skills that already have an operator.

The 51 candidates carry the printed text of a skill whose behaviour is already
implemented and consumed.  F073 adds only the shared classification: one YES
effect bound by id to the mechanic of the same id in the maintained execution
contract.  The matrix pins the three classes the lot must not blur:

* classified candidates (scope YES, implemented YES, grant none, one bound effect),
* the printed clauses the entry itself leaves outside the duel runtime
  (an explicit NO effect with its reason), and
* the skills with no operator at all, which stay unclassified: a name match is
  never an equivalence, and an unbound YES effect may not be declared implemented.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_knowledge.loader import load_execution_contract
from mordheim_knowledge.loader import load_skills
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"

#: C-combat-results.csv rows with status=metadata_gap and source_file catalog/skills/*.yaml.
CLASSIFIED = (
    "skill.expert-swordsman", "skill.jump-up", "skill.lightning-reflexes", "skill.mighty-blow",
    "skill.resilient", "skill.step-aside", "skill.strike-to-injure", "skill.strongman",
    "skill.unstoppable-charge", "skill.web-of-steel",
    "skill.always-strikes-first", "skill.axe-expert", "skill.axe-master",
    "skill.bellowing-battle-roar", "skill.berserker", "skill.crushing-blow",
    "skill.defensive-stance", "skill.elven-agility", "skill.expert-fighter",
    "skill.ferocious-charge", "skill.hard-to-kill", "skill.hardy-constitution",
    "skill.head-crusher", "skill.ignore-pain", "skill.infallible", "skill.infinite-hatred",
    "skill.inspiring-sermon", "skill.iron-sinews", "skill.knife-fighting", "skill.luck",
    "skill.mighty-biceps", "skill.miniath", "skill.monster-slayer", "skill.monstrous",
    "skill.red-fury", "skill.regeneration", "skill.shield-mastery", "skill.shield-strike",
    "skill.sigmar-s-sign", "skill.strength-of-steel", "skill.sure-strike", "skill.sweep",
    "skill.sword-master", "skill.thick-skull", "skill.tireless", "skill.tough-as-steel",
    "skill.unarmed-fighting", "skill.unbeatable-warrior", "skill.vampire-reflexes",
    "skill.virtue-of-valour", "skill.weapons-of-the-north",
)

#: Advancement clauses outside the duel runtime, kept as explicit NO effects.
OUT_OF_SCOPE_CLAUSES = {
    "skill.iron-sinews": "unimplemented.skill.iron-sinews.characteristic-maximum",
    "skill.red-fury": "unimplemented.skill.red-fury.characteristic-maximum",
    "skill.strength-of-steel": "unimplemented.skill.strength-of-steel.characteristic-maximum",
}

#: C rows with status=connection_gap plus the review-excluded skills: no operator exists,
#: so F073 adds no classification and no invented equivalence.
WITHOUT_OPERATOR = (
    "skill.chosen-of-the-white-tower", "skill.fey", "skill.fey-quickness",
    "skill.instinctive-warrior", "skill.magic-resistant", "skill.taunt",
    "skill.trading-flair",
)

#: Field or tag the maintained engine exposes for the classified operator.
OBSERVABLE = (
    ("skill.crushing-blow", "cannot_be_parried", True),
    ("skill.expert-fighter", "wound_modifier", 1),
    ("skill.mighty-blow", "strength_bonus", 1),
    ("skill.resilient", "incoming_strength_modifier", -1),
    ("skill.step-aside", "step_aside", True),
)


def skills():
    return {row["id"]: row for row in load_skills("mordheim", ROOT)}


def execution_ids():
    contract = load_execution_contract("mordheim", ROOT)
    return {row["id"] for row in contract["mechanics"]}


def test_every_candidate_classifies_its_existing_operator():
    catalogued = skills()
    mechanics = execution_ids()
    assert len(CLASSIFIED) == len(set(CLASSIFIED))
    for skill_id in CLASSIFIED:
        skill = catalogued[skill_id]
        runtime = skill["runtime"]
        assert (runtime["scope"], runtime["implemented"], runtime["grant"]) == ("YES", "YES", "none")
        yes = [effect for effect in runtime["effects"] if effect["scope"] == "YES"]
        assert yes, skill_id
        for effect in yes:
            assert effect["binding"] is not None, skill_id
            assert effect["binding"]["kind"] == "mechanic", skill_id
            assert effect["binding"]["id"] == skill_id, skill_id
            assert effect["binding"]["id"] in mechanics, skill_id
        for effect in runtime["effects"]:
            if effect["binding"] is None:
                assert effect["reason"].strip(), skill_id


def test_classification_does_not_change_who_receives_the_skill():
    catalogued = skills()
    for skill_id in CLASSIFIED:
        skill = catalogued[skill_id]
        assert skill["kind"] in {"general", "warband"}, skill_id
        assert skill["effect"].strip(), skill_id
        assert skill["runtime"]["grant"] == "none", skill_id


def test_the_remaining_clauses_are_explicit_and_never_invent_an_operator():
    catalogued = skills()
    for skill_id in CLASSIFIED:
        effects = catalogued[skill_id]["runtime"]["effects"]
        expected = 2 if skill_id in OUT_OF_SCOPE_CLAUSES else 1
        assert len(effects) == expected, skill_id
        if skill_id not in OUT_OF_SCOPE_CLAUSES:
            continue
        clause = effects[1]
        assert clause["id"] == OUT_OF_SCOPE_CLAUSES[skill_id], skill_id
        assert clause["scope"] == "NO" and clause["binding"] is None, skill_id
        assert clause["reason"].strip(), skill_id
        assert clause["id"] not in execution_ids(), skill_id


def test_skills_without_an_operator_stay_unclassified():
    catalogued = skills()
    mechanics = execution_ids()
    for skill_id in WITHOUT_OPERATOR:
        runtime = catalogued[skill_id].get("runtime")
        if runtime is None:
            continue
        for effect in runtime.get("effects") or ():
            if effect.get("scope") != "YES":
                continue
            binding = effect.get("binding") or {}
            assert binding.get("id") in mechanics, f"{skill_id}: unverified equivalence"


@pytest.mark.parametrize("skill_id,field,expected", OBSERVABLE)
def test_the_bound_operator_is_executed_and_not_only_declared(skill_id, field, expected):
    build = FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1), skill_ids=(skill_id,))
    compiled = compile_fighter(build, ROOT)
    assert getattr(compiled.global_effects, field) == expected
    without = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    assert getattr(without.global_effects, field) != expected


def test_a_tag_only_operator_reaches_the_compiled_fighter():
    build = FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1),
                         skill_ids=("skill.expert-swordsman",))
    assert "skill.expert-swordsman" in compile_fighter(build, ROOT).global_effects.tags
    without = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)), ROOT)
    assert "skill.expert-swordsman" not in without.global_effects.tags


def test_mighty_blow_excludes_both_pistols_but_bonuses_the_melee_hand():
    from dataclasses import replace
    from mordheim_combat.modular.contexts import _combined_effect, prepare_wound_context
    from mordheim_combat.modular.state import initialize_fighter
    from mordheim_combat_lab.verification.dice import StrictDice

    base = FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1),
                        main_weapon_id="weapon.sword")
    defender = compile_fighter(base, ROOT)
    dice = StrictDice([])
    defender_state = initialize_fighter(defender, dice, "defender")
    for pistol in ("weapon.pistol", "weapon.duelling-pistol"):
        for skills, melee_strength in (((), 3), (("skill.mighty-blow",), 4)):
            fighter = compile_fighter(replace(base, off_hand_id=pistol, skill_ids=skills), ROOT)
            state = initialize_fighter(fighter, dice, "attacker")
            for weapon, expected in ((fighter.main_weapon, melee_strength), (fighter.off_hand, 4)):
                context = prepare_wound_context(
                    fighter, defender, state, defender_state, weapon,
                    _combined_effect(fighter, weapon), first_round=True)
                assert context.strength == expected
    dice.finish()


def test_ignore_pain_prerequisite_is_covered_by_shared_construction():
    base = FighterBuild("mordheim", band_id="skaven-clan-pestilens",
                        profile_id="plague-priest", main_weapon_id="weapon.sword",
                        special_rule_ids=("band--clan-pestilens-special-skills-ignore-pain",))
    with pytest.raises(ValueError, match="Ignore Pain requires Resilient"):
        compile_fighter(base, ROOT)
    from dataclasses import replace
    fighter = compile_fighter(replace(base, skill_ids=("skill.resilient",)), ROOT)
    assert "skill.ignore-pain" in fighter.global_effects.tags
