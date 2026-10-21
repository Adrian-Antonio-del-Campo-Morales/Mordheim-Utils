"""Full-catalogue entry through the modular engine."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import KeyedDice
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelContext
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_mechanics
from mordheim_knowledge.loader import load_runtime_scope
import pytest


def profile_build(collection, band_id, profile_id):
    mandatory = (
        ("band--mutations-tentacle",)
        if band_id in {"cult-of-the-possessed", "trollheim-cult-of-the-possessed"}
        and profile_id == "mutants"
        else ("band--blessings-of-nurgle-bloated-foulness",)
        if band_id == "carnival-of-chaos" and profile_id == "tainted-ones"
        else ()
    )
    if band_id == "ogre-hunting-party-web" and profile_id == "trappers":
        mandatory = ("band--ogre-hunting-skills-netter",)
    elif band_id == "skaven-of-clan-moulder-web" and profile_id == "rat-ogres":
        mandatory = ("band--mutations-tentacle",)
    overrides = {}
    if band_id == "channel-rats-mim" and profile_id == "fugitives":
        overrides["sex"] = "male"
    if band_id == "house-guard-sc":
        overrides["house_guard_house"] = "fierezza"
    conditions = (
        ("condition.disability-2",)
        if band_id == "chaos-streets-mordheim-inhabitants" and profile_id == "cripples"
        else ()
    )
    return FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        collection=collection, special_rule_ids=mandatory,
        trait_overrides=overrides, condition_ids=conditions,
    )


@pytest.mark.eligibility
def test_modular_runtime_rejects_a_manually_injected_lance():
    fighter = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)))
    lance = replace(fighter, main_weapon=replace(fighter.main_weapon, tags=("weapon.lance",)))
    with pytest.raises(ValueError, match="mounted combat is not supported"):
        initialize_duel(lance, fighter, KeyedDice(1))


@pytest.mark.end_to_end
def test_every_legal_profile_can_execute_a_complete_scalar_round():
    # Profiles the runtime scope excludes (a vehicle and a watercraft) never
    # reach this pipeline; they are declared with their reason in
    # registry/runtime-scope.yaml.  A creature whose printed line has no
    # Initiative (the Necrarchs' Banshee) does reach it: the absence strikes
    # last instead of keeping the profile out.
    exclusions = {
        (str(row["band_id"]), str(row["profile_id"]))
        for row in load_runtime_scope("mordheim").get("profile_exclusions") or ()
    }
    opponent = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
        trait_overrides={"sex": "male", "fighter_kind": "henchman"},
    ))
    executed = 0
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection):
            for profile in band.profiles:
                if (str(band.band["id"]), str(profile["id"])) in exclusions:
                    continue
                fighter = compile_fighter(profile_build(
                    collection, band.band["id"], profile["id"],
                ))
                dice = KeyedDice(executed + 1)
                state = initialize_duel(fighter, opponent, dice)
                result = resolve_round(fighter, opponent, state, dice)
                assert result.state.round_index == 1
                executed += 1
    # Every profile of both collections but the two declared exclusions
    # (534 before the supplement bands were promoted, +1 for the Banshee once its
    # blank Initiative was represented as an absence).
    assert executed == 1054


def _witch_finder_charge(opponent):
    """The Solkan mark is the only bearer; the charge must name its enemy."""
    fighter = compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.hired-sword.2b",
        profile_id="hireling.hired-sword.priest-of-verena",
        variant_ids=("deity.solkan",),
        special_rule_ids=("hireling.hired-sword.priest-of-verena.skill.witch-finder",),
        condition_ids=("condition.witch-finder-charge",),
    ))
    target = replace(opponent, global_effects=replace(
        opponent.global_effects,
        tags=(*opponent.global_effects.tags, "identity.warlock"),
    ))
    return fighter, target


@pytest.mark.end_to_end
def test_every_execution_mechanism_can_enter_the_scalar_round_pipeline():
    characteristics = Characteristics(3, 3, 3, 2, 3, 1, leadership=7)
    opponent = compile_fighter(FighterBuild(
        "mordheim", characteristics,
        trait_overrides={"sex": "male", "fighter_kind": "henchman"},
    ))
    excluded = {
        row["id"] for row in load_runtime_scope("mordheim").get("mechanic_exclusions") or ()
    }
    charge_attempt = {
        "condition.impetuous-charge": "first",
        "condition.nuttaz-charge": "first",
        "mechanic.opposite-sex-charge-test": "second",
    }
    executed = 0
    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        for row in load_mechanics("mordheim")[family]:
            mechanic_id = row["id"]
            if mechanic_id in excluded:
                continue
            if family == "weapons":
                options = ({"main_weapon_id": mechanic_id} if row.get("main_hand")
                           else {"off_hand_id": mechanic_id})
            elif family == "armours":
                options = ({"defence_ids": (mechanic_id,)}
                           if mechanic_id == "armour.cathayan-quilted-silk"
                           else {"armour_id": mechanic_id})
            elif family == "defences":
                options = ({"off_hand_id": mechanic_id}
                           if mechanic_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}
                           else {"defence_ids": (mechanic_id,)})
            elif family == "materials":
                options = {"main_material_id": mechanic_id}
            elif family == "preparations":
                options = {"preparation_ids": (mechanic_id,)}
            elif family == "poisons":
                options = {"main_poison_id": mechanic_id}
            else:
                # Curse of the Revenant prints "Requires Great Thirster", and the
                # compiler enforces that prerequisite, so the row is admitted
                # together with the skill it requires.
                requires = ("mechanic.great-thirster",)
                options = {"skill_ids": (mechanic_id, *(
                    requires if mechanic_id == "mechanic.curse-of-the-revenant" else ()), )}
            context = (DuelContext(charging=(charge_attempt[mechanic_id],),
                                   active_participant="first")
                       if mechanic_id in charge_attempt else None)
            target = opponent
            if mechanic_id == "condition.witch-finder-charge":
                fighter, target = _witch_finder_charge(opponent)
                context = DuelContext(charging=("first",), active_participant="first")
            else:
                # These rows name a recipient or supply a pre-battle/current fact.
                facts = {
                    "defence.magic-acorn": {"trait_overrides": {"fighter_kind": "hero"}},
                    "mechanic.disability": {"condition_ids": ("condition.disability-2",)},
                    "mechanic.snorri-drunk": {"trait_overrides": {"snorri_drunk_result": 2}},
                    "mechanic.dueling-pride": {"trait_overrides": {
                        "house_guard_house": "fierezza", "fighter_kind": "hero"}},
                    "mechanic.opposite-sex-charge-test": {"trait_overrides": {"sex": "female"}},
                }.get(mechanic_id, {})
                fighter = compile_fighter(FighterBuild(
                    "mordheim", characteristics, **options, **facts))
            dice = KeyedDice(10_000 + executed)
            state = initialize_duel(fighter, target, dice, context=context)
            assert resolve_round(fighter, target, state, dice).state.round_index == 1
            executed += 1
    # Promoted local rules add Shifty, local profiles and source-specific variants.
    # Crude Belch needs known enemy Leadership; the generic opponent supplies it.
    # Fey Quickness adds one source-backed melee avoidance operator.
    assert executed == 502
