"""C07b — the printed equivalences that decide a duel.

Wall of Steel turns the Ashigaru's own spear into a two-handed parrying weapon
while the ordinary spear keeps nothing; the Pristekk thinglash's flexible lash
refuses the defender's parry and still leaves him the printed save, while its
whipcrack adds exactly one bonus attack; the Shock Rod strikes first when
charged; the Balanced Travel Staff decides the priority tie by its own
Initiative, and the shovel's halberd profile adds the printed Strength.
"""
from __future__ import annotations

import sys
from dataclasses import replace

from mordheim_combat import phases
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.equipment import whipcrack_weapon
from mordheim_combat.modular.rounds import apply_round_weapon_attack_modifiers
from mordheim_combat.modular.state import initialize_fighter
from tests.engines.shared.dice import StrictDice
from mordheim_core.models import Characteristics, FighterBuild
import pytest


# The frozen-build loader is the only compilation route in this module: the
# fixture below replaces this name with ``load_builds(...).fighter``, so every
# builder keeps its complete FighterBuild and the local ``replace`` calls stay
# untouched, while nothing compiles here.
compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)




def tape(*rolls):
    return StrictDice([{"key": key, "value": value} for key, value in rolls])


def band(band_id, profile_id, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band_id, profile_id=profile_id,
                                        collection=collection, **options))


def custom(weapon="weapon.mace", **options):
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
                                        main_weapon_id=weapon, **options))


def state(fighter):
    return initialize_fighter(fighter, tape(), "init")


def strike(owner, foe, rolls, *, key="r"):
    dice = tape(*rolls)
    result = resolve_reference_attack(owner, foe, state(owner), state(foe), owner.main_weapon, dice, key=key)
    dice.finish()
    return result


def test_the_ashigaru_spear_parries_only_under_wall_of_steel():
    """The stance adds the parry; the same spear without it never offers one."""
    stance = band("nipponese-expedition-web", "ashigaru", main_weapon_id="weapon.spear",
                  variant_ids=("stance.wall-of-steel",))
    plain = band("nipponese-expedition-web", "ashigaru", main_weapon_id="weapon.spear")
    assert stance.main_weapon.parry and stance.main_weapon.two_handed
    assert not plain.main_weapon.parry and not plain.main_weapon.two_handed
    attacker = custom()
    parried = strike(attacker, stance, [("r.hit", 4), ("r.parry", 5)])
    assert parried.parried and parried.defender.wounds == stance.characteristics.wounds
    # The ordinary spear asks for no parry roll at all: the tape that carries
    # none resolves straight to the printed injury.
    wounded = strike(attacker, plain, [("r.hit", 4), ("r.wound", 4), ("r.injury.0", 3)])
    assert wounded.wounded and not wounded.parried


def test_the_thinglash_refuses_the_defenders_parry(precompiled):
    """A flexible lash cannot be parried; the sword's own parry still works on a mace."""
    lash_case, control_case = precompiled(0), precompiled(1)
    lash, swordsman = lash_case.first, lash_case.second
    assert lash.main_weapon.cannot_be_parried
    hit = strike(lash, swordsman, [("r.hit", 4), ("r.wound", 3)])
    assert hit.wounded and not hit.parried
    control = strike(control_case.first, control_case.second, [("r.hit", 4), ("r.parry", 5)])
    assert control.parried and not control.wounded


def test_the_thinglash_grants_the_printed_save_and_its_own_strength(precompiled):
    """The printed +1 enemy save is the attack's own target bonus, and S+1 wounds."""
    armed_case, plain_case = precompiled(0), precompiled(1)
    lash, light = armed_case.first, armed_case.second
    assert strike(lash, light, [("r.hit", 4), ("r.wound", 3), ("r.armour", 6)]).saved
    context = prepare_armour_context(lash, light, state(lash), state(light), lash.main_weapon,
                                     lash.main_weapon, first_round=True, charging=False,
                                     key="r.armour", melee_attack=True)
    assert phases.armour_target(context) == 6
    # Without the printed bonus the same attack leaves no save at all.
    assert phases.armour_target(replace(context, target_armour_bonus=0)) == 7
    # The printed Strength reaches the wound roll: S3 +1 wounds Toughness 3 on 3.
    assert strike(lash, plain_case.second, [("r.hit", 4), ("r.wound", 3)]).wounded


def test_the_thinglash_whipcrack_adds_one_bonus_attack(precompiled):
    """Whipcrack is one bonus attack when charging or charged, and never the foe's."""
    lash, mace = precompiled(0).first, precompiled(0).second
    assert whipcrack_weapon(lash) is not None and whipcrack_weapon(mace) is None
    assert apply_round_weapon_attack_modifiers(lash, mace, 2, first_round=True,
                                               charging=True, charged=False) == 3
    assert apply_round_weapon_attack_modifiers(lash, mace, 2, first_round=True,
                                               charging=False, charged=True) == 3
    assert apply_round_weapon_attack_modifiers(mace, lash, 2, first_round=True,
                                               charging=True, charged=False) == 2


def test_the_shock_rod_strikes_first_when_charged(precompiled):
    """First strike decides the tier; the plain mace shares it with nobody."""
    rod, mace = precompiled(0).first, precompiled(0).second
    assert rod.main_weapon.two_handed
    assert phases.resolve_priority(phases.PriorityContext(rod, mace, first_round=True,
                                                          charged=True)).priority == 1
    assert phases.resolve_priority(phases.PriorityContext(mace, rod, first_round=True,
                                                          charged=True)).priority == 0


def test_the_balanced_travel_staff_decides_the_priority_tie_by_its_own_initiative(precompiled):
    """+1 Initiative in close combat orders two otherwise equal fighters."""
    wizard, foe = precompiled(0).first, precompiled(0).second
    staff = phases.resolve_priority(phases.PriorityContext(wizard, foe, first_round=True))
    bare = phases.resolve_priority(phases.PriorityContext(foe, wizard, first_round=True))
    assert staff.priority == bare.priority
    assert staff.initiative == bare.initiative + 1
    assert phases.first_acts_before(staff, bare, tape(), key="tie")


def test_the_sylvania_shovel_halberd_adds_the_printed_strength(precompiled):
    """The shovel fights as the halberd: +1 Strength on the wound roll."""
    shovel_case, plain_case = precompiled(0), precompiled(1)
    assert strike(shovel_case.first, shovel_case.second, [("r.hit", 4), ("r.wound", 3)]).wounded
    # The same roll of 3 fails for an unmodified Strength 3 attacker.
    assert not strike(plain_case.first, plain_case.second, [("r.hit", 4), ("r.wound", 3)]).wounded
