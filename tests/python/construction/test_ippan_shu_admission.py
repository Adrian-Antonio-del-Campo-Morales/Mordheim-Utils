"""Hireling admission: Grand Master Ippan Shu's printed clauses.

Source (``sources/knowledge``): ``catalog/hirelings/dramatis-personae/grade-1c.yaml``
* Grand Master Ippan Shu *: "Bare-handed Fighting: Ippan Shu can fight without
weapons and suffers no penalties when doing so.  In fact, he then counts as
having a second close combat weapon and gets +1 attack."  "Iron Fan: ... The
weapon grants him +1 Initiative and allows him to parry enemy blows and missile
shots."  "Immune to Psychology: ... and automatically passes all Leadership-based
tests."

The profile previously refused to compile because none of its printed clauses had
a runtime at all.  Its two admitted clauses now publish the shared
``skill.unarmed-fighting`` operator and the canonical automatic-Leadership
operator, and the fan reaches the duel as its own canonical weapon; the
shooting-phase missile parry, the free movement rule, the flame-template breath
and the hiring composition each name their own exclusion.
"""
from __future__ import annotations

import pytest

from mordheim_combat.modular.contexts import _attack_strength, _combined_effect
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import (
    AttackPoolContext, PriorityContext, build_attacks, resolve_priority,
)
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild

IPPAN_SHU = "hireling.dramatis.grand-master-ippan-shu"
BAND = "hirelings.dramatis-personae.1c"
FAN = "weapon.iron-fan"


def ippan_shu(weapon="weapon.fist", **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=BAND, profile_id=IPPAN_SHU, main_weapon_id=weapon, **options))


def plain(strength=3):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, strength, 3, 2, 6, 1, leadership=7),
        main_weapon_id="weapon.fist"))


# --- admission ----------------------------------------------------------------

@pytest.mark.phase2_construction
def test_the_profile_compiles_with_its_printed_clauses_bound():
    master = ippan_shu(FAN)
    assert "skill.unarmed-fighting" in master.global_effects.tags
    assert "mechanic.automatic-leadership" in master.global_effects.tags
    assert "mechanic.psychology-immunity" in master.global_effects.tags
    assert master.global_effects.initiative_bonus == 1


@pytest.mark.phase1_kb_contracts
def test_the_excluded_clauses_name_their_own_reason():
    """The four out-of-duel clauses are classified, not left without runtime."""
    from mordheim_construction.combat_packages import combat_packages

    package = next(pack for pack in combat_packages("mordheim") if pack.band["id"] == BAND)
    rules = {rule["id"]: rule for rule in package.special_rules}
    for suffix in ("parry-missiles", "feather-movement", "fire-breath", "campaign-eligibility"):
        rule = rules[f"{IPPAN_SHU}.rule.{suffix}"]
        assert rule["runtime"]["scope"] == "NO", suffix
        assert rule["runtime"]["implemented"] == "NO", suffix
        assert rule["runtime"]["effects"][0]["reason"], suffix


# --- the shared unarmed operator ----------------------------------------------

@pytest.mark.phase3_rules
def test_bare_handed_resolves_one_attack_more_than_the_profile_value():
    master = ippan_shu()
    assert master.characteristics.attacks == 4
    assert build_attacks(AttackPoolContext(master)).attacks == 5
    # The bonus belongs to the printed "when doing so": armed, he keeps A4.
    assert build_attacks(AttackPoolContext(ippan_shu(FAN))).attacks == 4


@pytest.mark.parametrize("skills,weapon,expected", [
    (("skill.unarmed-fighting",), "weapon.fist", 5),
    (("skill.art-of-silent-death",), "weapon.fist", 5),
    (("skill.unarmed-fighting", "skill.art-of-silent-death"), "weapon.fist", 5),
    (("skill.art-of-silent-death",), "weapon.fighting-claws", 6),
    (("skill.unarmed-fighting", "skill.art-of-silent-death"), "weapon.fighting-claws", 6),
    (("skill.unarmed-fighting", "skill.art-of-silent-death"), "weapon.sword", 4),
])
@pytest.mark.phase3_rules
def test_the_same_second_weapon_is_counted_once_without_losing_the_claws_bonus(skills, weapon, expected):
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 4),
        main_weapon_id=weapon, skill_ids=skills))
    assert build_attacks(AttackPoolContext(fighter)).attacks == expected


@pytest.mark.phase3_rules
def test_bare_handed_removes_the_fist_penalty():
    master, foe = ippan_shu(), plain()
    states = {fighter: initialize_fighter(fighter, StrictDice([]), "probe")
              for fighter in (master, foe)}
    effect = _combined_effect(master, master.main_weapon)
    assert _attack_strength(master, foe, states[master], master.main_weapon, effect,
                            False, False)[0] == master.characteristics.strength
    # Negative control: an ordinary warrior still suffers the fist's penalty.
    ordinary = plain()
    ordinary_state = initialize_fighter(ordinary, StrictDice([]), "probe")
    ordinary_effect = _combined_effect(ordinary, ordinary.main_weapon)
    assert _attack_strength(ordinary, foe, ordinary_state, ordinary.main_weapon,
                            ordinary_effect, False, False)[0] == ordinary.characteristics.strength - 1


# --- the iron fan --------------------------------------------------------------

def initiative(fighter):
    return resolve_priority(PriorityContext(fighter=fighter, opponent=plain())).initiative


# Primary: the fan's compiled parry and its single Initiative point. The
# priority resolution below is the secondary guarantee it feeds.
@pytest.mark.phase2_construction
def test_the_iron_fan_parries_and_raises_his_initiative():
    master = ippan_shu(FAN)
    assert master.main_weapon.parry is True
    assert FAN in master.main_weapon.tags
    assert initiative(master) == master.characteristics.initiative + 1
    # The printed clause adds the point once: the fan's own profile does not
    # repeat the Initiative the bearer's rule already carries.
    assert master.main_weapon.initiative_bonus == 0
    # Negative control: the bare hand does not parry, while the printed fan is
    # the only weapon the kit offers, and the bearer's rule still adds the point.
    unarmed = ippan_shu()
    assert unarmed.main_weapon.parry is False
    assert initiative(unarmed) == unarmed.characteristics.initiative + 1
    # Negative control: an ordinary warrior carries no such point.
    ordinary = plain()
    assert initiative(ordinary) == ordinary.characteristics.initiative
