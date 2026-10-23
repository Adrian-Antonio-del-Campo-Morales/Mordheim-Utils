"""C05b remaining rows: the six printed consequences now connected or disposed.

Each case drives the canonical package, the shared eligibility decision and the
compiler the application uses; the wolf form also reaches the existing modular
werewolf state instead of a second operator being invented.
"""
from __future__ import annotations

import pytest

from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.state import initialize_duel
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root

ROOT = knowledge_root()
COLLECTION = "mordheim"
PACKS = {pack.band["id"]: pack for pack in combat_packages(COLLECTION)}


class FixedDice:
    def roll(self, request):
        return 1


def profile_of(band_id, profile_id):
    return next(row for row in PACKS[band_id].profiles if row["id"] == profile_id)


def build(band_id, profile_id, **options):
    return FighterBuild(COLLECTION, band_id=band_id, profile_id=profile_id,
                        collection=COLLECTION, **options)


def facts(band_id, profile_id, **options):
    return desktop_call("profileFacts", build(band_id, profile_id, **options), ROOT,
                        package=PACKS[band_id], profile=profile_of(band_id, profile_id))


# --- 1. the Mule Skinner's single Animal Handling skill -----------------------

MULE = "hireling.hired-sword.mule-skinner"
MULE_BAND = "hirelings.hired-sword.1b"
ANIMALS = (
    "hireling.hired-sword.mule-skinner.skill.animal-handling-falconer",
    "hireling.hired-sword.mule-skinner.skill.animal-handling-horse",
)


@pytest.mark.phase2_construction
def test_the_mule_skinner_chooses_exactly_one_published_animal_handling_skill():
    offered = desktop_call("specialRules", build(MULE_BAND, MULE), ROOT,
                           package=PACKS[MULE_BAND], profile=profile_of(MULE_BAND, MULE))
    assert offered == list(ANIMALS)
    for chosen in ANIMALS:
        assert compile_fighter(build(MULE_BAND, MULE, special_rule_ids=(chosen,)), ROOT)
    with pytest.raises(ValueError, match="exactly one Animal Handling skill"):
        compile_fighter(build(MULE_BAND, MULE), ROOT)
    with pytest.raises(ValueError, match="exactly one Animal Handling skill"):
        compile_fighter(build(MULE_BAND, MULE, special_rule_ids=ANIMALS), ROOT)


# --- 2. the Cursed Hillman's supplied wolf form -------------------------------

HILLMAN = "hireling.hired-sword.cursed-hillman"
HILLMAN_BAND = "hirelings.hired-sword.2a"
WOLF = "hireling.hired-sword.cursed-hillman.rule.wolf-form"


@pytest.mark.phase2_construction
def test_the_supplied_wolf_form_compiles_the_printed_line_and_uses_the_werewolf_state():
    man = compile_fighter(build(HILLMAN_BAND, HILLMAN), ROOT)
    wolf = compile_fighter(build(HILLMAN_BAND, HILLMAN, special_rule_ids=(WOLF,)), ROOT)
    # Wolf M7 WS4 BS0 S4 T4 W2 I5 A2(3) Ld6, with no cloak save.
    assert (wolf.characteristics.movement, wolf.characteristics.weapon_skill,
            wolf.characteristics.strength, wolf.characteristics.toughness,
            wolf.characteristics.wounds, wolf.characteristics.initiative,
            wolf.characteristics.attacks, wolf.characteristics.leadership) == (
                7, 4, 4, 4, 2, 5, 2, 6)
    assert wolf.armour_save == 7 and wolf.natural_armour_save == 7
    assert man.global_effects.tags == wolf.global_effects.tags
    state = initialize_duel(wolf, man, FixedDice())
    assert state.first.hillman_wolf is True and state.second.hillman_wolf is False
    in_form = equipment_for_state(wolf, state.first, first_round=False)
    assert "weapon.natural-attacks" in in_form.main_weapon.tags
    assert [attack.tags for attack in in_form.extra_attacks] == [("rule.hillman-bite",)]
    assert in_form.armour_save == 7


# --- 3. the War-Priest of Solkan gate ----------------------------------------

PRIEST = "hireling.hired-sword.priest-of-verena"
PRIEST_BAND = "hirelings.hired-sword.2b"


@pytest.mark.phase2_construction
def test_strength_access_belongs_to_the_solkan_variant_alone():
    assert facts(PRIEST_BAND, PRIEST)["skill_access"] == ["academic"]
    solkan = facts(PRIEST_BAND, PRIEST, variant_ids=("deity.solkan",))
    assert solkan["skill_access"] == ["academic", "strength"]
    assert [row["category"] for row in solkan["skill_lists"]] == ["strength"]
    assert compile_fighter(build(PRIEST_BAND, PRIEST, variant_ids=("deity.solkan",),
        skill_ids=("skill.mighty-blow",)), ROOT)
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build(PRIEST_BAND, PRIEST, main_weapon_id="weapon.sword",
            skill_ids=("skill.mighty-blow",)), ROOT)


WITCH_FINDER = "hireling.hired-sword.priest-of-verena.skill.witch-finder"
WITCH_FINDER_CHARGE = "condition.witch-finder-charge"


@pytest.mark.phase2_construction
def test_the_supplied_compulsory_charge_belongs_to_the_marked_witch_finder_alone():
    assert compile_fighter(build(PRIEST_BAND, PRIEST, variant_ids=("deity.solkan",),
        special_rule_ids=(WITCH_FINDER,), condition_ids=(WITCH_FINDER_CHARGE,)), ROOT)
    with pytest.raises(ValueError, match="War-Priest of Solkan variant"):
        compile_fighter(build(PRIEST_BAND, PRIEST, special_rule_ids=(WITCH_FINDER,),
            condition_ids=(WITCH_FINDER_CHARGE,)), ROOT)
    with pytest.raises(ValueError, match="compulsory Witch-finder charge"):
        compile_fighter(build(PRIEST_BAND, PRIEST, variant_ids=("deity.solkan",),
            condition_ids=(WITCH_FINDER_CHARGE,)), ROOT)


# --- 4. the promoted Ogre Pit Fighter ---------------------------------------

PIT = "pit-fighters"


@pytest.mark.phase2_construction
def test_the_promoted_ogre_pit_fighter_opens_its_three_lists_only_after_promotion():
    henchman = facts(PIT, "ogre-pit-fighter")
    assert henchman["skill_access"] == []
    assert henchman["promotion_skill_access"] == ["combat", "strength", "special"]
    promoted = facts(PIT, "ogre-pit-fighter", variant_ids=("promotion.hero",))
    assert promoted["skill_access"] == ["combat", "strength", "special"]
    with pytest.raises(ValueError, match="not available"):
        compile_fighter(build(PIT, "ogre-pit-fighter", skill_ids=("skill.mighty-blow",)), ROOT)
    assert compile_fighter(build(PIT, "ogre-pit-fighter",
        variant_ids=("promotion.hero",), skill_ids=("skill.mighty-blow",)), ROOT)


# --- 5. the Bloodfather's remaining consequences -----------------------------


@pytest.mark.phase1_kb_contracts
def test_the_bloodfather_role_keeps_frenzy_and_classifies_the_closed_consequences():
    seer = compile_fighter(build("marauders-of-chaos", "seer",
        special_rule_ids=("band--mark-of-arkhar",)), ROOT)
    assert seer.global_effects.frenzy is True
    rule = next(row for row in PACKS["marauders-of-chaos"].special_rules
                if row["id"] == "band--mark-of-arkhar")
    by_id = {effect["id"]: effect for effect in rule["runtime"]["effects"]}
    assert by_id["bloodfather--strength-access"]["scope"] == "YES"
    for closed in ("bloodfather--spell-targeting", "bloodfather--cannot-cast",
                   "bloodfather--post-combat-gain"):
        assert by_id[closed]["scope"] == "NO" and by_id[closed]["binding"] is None


# --- 6. Ippan Shu's printed set ----------------------------------------------

IPPAN = "hireling.dramatis.grand-master-ippan-shu"
IPPAN_BAND = "hirelings.dramatis-personae.1c"
SPEED = {"skill.acrobat", "skill.dodge", "skill.jump-up", "skill.leap",
         "skill.lightning-reflexes", "skill.scale-sheer-surfaces", "skill.sprint"}


@pytest.mark.phase2_construction
def test_ippan_shu_reaches_every_speed_skill_and_only_the_admitted_battle_monk_member():
    assert desktop_call("specialRules", build(IPPAN_BAND, IPPAN), ROOT,
                        package=PACKS[IPPAN_BAND], profile=profile_of(IPPAN_BAND, IPPAN)) == [
        "hireling.dramatis.grand-master-ippan-shu.skill.energy-focus"]
    choices = desktop_call("skillChoices", build(IPPAN_BAND, IPPAN), ROOT,
                           package=PACKS[IPPAN_BAND], profile=profile_of(IPPAN_BAND, IPPAN))
    assert {skill for skill, allowed in choices.items() if allowed} == SPEED
    assert not any("warmonger" in skill for skill, allowed in choices.items() if allowed)
    assert compile_fighter(build(IPPAN_BAND, IPPAN), ROOT)
