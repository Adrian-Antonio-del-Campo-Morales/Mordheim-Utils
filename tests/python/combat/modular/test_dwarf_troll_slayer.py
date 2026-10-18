"""The Dwarf Troll Slayer's six printed clauses reach the duel.

Every case compiles the canonical hired-sword package and reads the operator the
modular engine executes.  The intrinsic rules (Hard Head, Hard to Kill,
Deathwish) travel with the profile; the three Troll Slayer skills are selectable
and are never granted unless the loadout names them.
"""
from __future__ import annotations

from mordheim_combat import phases
from mordheim_combat.modular import contexts
from mordheim_combat.modular.psychology import resolve_fear
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

PROFILE = "hireling.hired-sword.dwarf-troll-slayer"
BAND = "hirelings.hired-sword.core"
FEROCIOUS = PROFILE + ".skill.ferocious-charge"
MONSTER = PROFILE + ".skill.monster-slayer"
BERSERK = PROFILE + ".skill.berserker"
OGRE = "hireling.hired-sword.ogre-bodyguard"


def slayer(**options):
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=PROFILE,
                                        collection="mordheim", **options))


def plain(toughness=3, **options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, toughness, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", **options))


def states(attacker, defender, dice=None):
    dice = dice or StrictDice([])
    return (initialize_fighter(attacker, dice, "a"),
            initialize_fighter(defender, dice, "d"))


def test_the_intrinsic_rules_travel_and_the_skills_stay_selectable():
    base = slayer()
    for tag in ("concussion_immune", "skill.hard-to-kill", "mechanic.psychology-immunity"):
        assert base.global_effects.tags.count(tag) == 1
    # The three Troll Slayer skills are a loadout choice, not free intrinsics.
    for tag in ("skill.ferocious-charge", "skill.monster-slayer", "skill.berserker"):
        assert tag not in base.global_effects.tags
    chosen = slayer(special_rule_ids=(FEROCIOUS, MONSTER, BERSERK))
    for tag in ("skill.ferocious-charge", "skill.monster-slayer", "skill.berserker"):
        assert chosen.global_effects.tags.count(tag) == 1


def injury(fighter, weapon, roll):
    context = contexts._injury_context(fighter, weapon, "h01")
    return phases.resolve_injury(
        context, StrictDice([{"key": "h01.injury", "value": roll}])).condition


def test_hard_head_cancels_only_the_mace_concussion():
    mace = plain().main_weapon
    assert mace.concussion
    target = slayer()
    # A 2-4 total from a mace stuns an ordinary fighter; this one is only
    # knocked down.  It is not a blanket immunity: a 6 still takes him out.
    assert injury(plain(), mace, 2) is phases.Condition.STUNNED
    assert injury(target, mace, 2) is phases.Condition.KNOCKED_DOWN
    assert injury(target, mace, 6) is phases.Condition.OUT
    # Hard to Kill opens the Stunned band to 5 while the out-of-action
    # threshold stays at 6, exactly as printed.
    assert injury(target, mace, 5) is phases.Condition.STUNNED
    assert injury(plain(), mace, 5) is phases.Condition.OUT


def test_monster_slayer_wounds_on_four_but_keeps_a_better_strength():
    target = plain(toughness=4)
    _, target_state = states(slayer(), target)

    def required(attacker, weapon):
        own, _ = states(attacker, target)
        context = contexts.prepare_wound_context(
            attacker, target, own, target_state, weapon,
            contexts._combined_effect(attacker, weapon))
        return (context.strength, context.toughness,
                phases.wound_target(context.strength, context.toughness,
                                    context.maximum_target))

    axe = slayer(main_weapon_id="weapon.axe")
    strength, toughness, ordinary = required(axe, axe.main_weapon)
    assert (strength, toughness) == (3, 4)
    assert ordinary == 5
    chosen = slayer(main_weapon_id="weapon.axe", special_rule_ids=(MONSTER,))
    assert required(chosen, chosen.main_weapon)[2] == 4
    # The cap is a maximum: a modified Strength that already wounds on 3+ keeps
    # its better roll instead of being pushed back to 4+.
    heavy = slayer(main_weapon_id="weapon.double-handed-weapon", special_rule_ids=(MONSTER,))
    strength, _, capped = required(heavy, heavy.main_weapon)
    assert strength == 5
    assert capped == 3


def test_berserker_adds_one_only_on_the_charging_turn():
    target = plain()
    chosen = slayer(special_rule_ids=(BERSERK,))
    plain_state, target_state = states(chosen, target)

    def modifier(attacker, *, charging):
        own, other = states(attacker, target)
        return contexts.prepare_hit_context(
            attacker, target, own, other, attacker.main_weapon,
            contexts._combined_effect(attacker, attacker.main_weapon),
            first_round=True, charging=charging).modifier

    assert modifier(chosen, charging=True) == modifier(slayer(), charging=True) + 1
    assert modifier(chosen, charging=False) == modifier(slayer(), charging=False)


def test_ferocious_charge_is_declared_and_expires_with_the_charge():
    """The printed "may" doubles Attacks and costs -1 To Hit only when chosen."""
    foe = plain()
    charger = slayer(main_weapon_id="weapon.axe", special_rule_ids=(FEROCIOUS,))
    state = initialize_duel(charger, foe, StrictDice([]),
        context=DuelContext(charging=("first",), active_participant="first"))
    assert state.first_charged

    # Declared: both printed halves apply in the charge round.
    dice = StrictDice([
        {"key": "round.0.first.attack.0.hit", "value": 1},
        {"key": "round.0.first.attack.1.hit", "value": 1},
        {"key": "round.0.second.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([
        {"key": "round.0.first.ferocious-charge", "value": True}])
    declared = resolve_round(charger, foe, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(declared.attacks) == 3
    # Both of the Slayer's doubled attacks pay the printed -1: WS4 against WS3
    # would hit on 3+, and the foe's reply hits on 4+ anyway.
    assert sorted(attack.hit_target for attack in declared.attacks) == [4, 4, 4]
    state = initialize_duel(charger, foe, StrictDice([]),
        context=DuelContext(charging=("first",), active_participant="first"))

    # Declined: the ordinary single attack and its ordinary to-hit.
    dice = StrictDice([
        {"key": "round.0.first.attack.0.hit", "value": 1},
        {"key": "round.0.second.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([
        {"key": "round.0.first.ferocious-charge", "value": False}])
    declined = resolve_round(charger, foe, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(declined.attacks) == 2
    assert sorted(attack.hit_target for attack in declined.attacks) == [3, 4]

    # The choice is spent: the next round neither offers it nor carries the
    # penalty, and the compiled fighter keeps the skill for a later charge.
    dice = StrictDice([
        {"key": "round.1.second.attack.0.hit", "value": 1},
        {"key": "round.1.first.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    later = resolve_round(charger, foe, declined.state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(later.attacks) == 2
    assert sorted(attack.hit_target for attack in later.attacks) == [3, 4]
    assert "skill.ferocious-charge" in charger.global_effects.tags

    # A lost own turn also prevents this voluntary charge declaration.
    blocked = slayer(main_weapon_id="weapon.axe", special_rule_ids=(FEROCIOUS,),
                     condition_ids=("condition.massively-built-lost-turn",))
    state = initialize_duel(blocked, foe, StrictDice([]),
        context=DuelContext(charging=("first",), active_participant="first"))
    dice = StrictDice([{"key": "round.0.second.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    lost = resolve_round(blocked, foe, state, dice, decisions)
    dice.finish(); decisions.finish()
    assert len(lost.attacks) == 1
    assert not lost.state.first.massively_built_lost_turn


class Recorder:
    """A loose source that records every request, to show an offer came back."""

    def __init__(self):
        self.rolls = []
        self.choices = []

    def roll(self, request):
        self.rolls.append(request.key)
        return 1

    def choose(self, key, context=None):
        self.choices.append(key)
        return True


def test_deathwish_immunity_skips_the_fear_test():
    slayer_fighter = slayer(main_weapon_id="weapon.axe")
    ogre = compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=OGRE,
        collection="mordheim", main_weapon_id="weapon.double-handed-weapon"))
    context = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(slayer_fighter, ogre, StrictDice([]), context=context)
    dice = Recorder()
    result = resolve_fear(slayer_fighter, ogre, state, dice, Recorder())
    assert dice.rolls == []
    assert result.first_charged
    # Negative control: an ordinary charger must take the same test.
    ordinary = plain()
    state = initialize_duel(ordinary, ogre, StrictDice([]), context=context)
    dice = Recorder()
    resolve_fear(ordinary, ogre, state, dice, Recorder())
    assert any(".fear." in key for key in dice.rolls)
