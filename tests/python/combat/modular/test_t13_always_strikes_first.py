"""T13 A-block: the printed ``always strikes first`` stanza and its specifications.

Both origins publish the canonical ``skill.always-strikes-first`` operator, whose
maintained meaning is recorded in ``tests/specs``:

* ``semantic/interactions/priority-order.yaml`` /
  ``interaction-combat-order--skill.always-strikes-first``: *"Always Strikes
  First raises priority above the ordinary Initiative order"*; two bearers of the
  skill tie, and the ``priority-tie`` D6 decides.
* ``semantic/grants/editorial-lost-innocence.yaml``: both Lost Innocence origins
  keep strike first while standing up and against a spear, and *"No ordinary
  Initiative advantage defeats strike first."*
* ``semantic/grants/remaining-profile-access.yaml`` /
  ``night-goblin-fanatic-frantic``: Frantic *"grants the Fanatic an absolute
  priority that prevails over Initiative and ordinary weapon modifiers"* - that
  case is the ``night-goblins-mic`` origin, whose compiler binding sets priority
  10.  The ``night-goblins-kaz`` origin deliberately binds the canonical
  mechanic instead, as its own baseline test records.
"""
from __future__ import annotations

import pytest

from mordheim_combat.phases import PriorityContext, resolve_priority
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import effect_index
from mordheim_core.models import Characteristics, FighterBuild


def fighter(band_id=None, profile_id=None, weapon="weapon.mace", initiative=3, **options):
    if band_id is None:
        return compile_fighter(FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 1, initiative, 1),
            main_weapon_id=weapon, **options))
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        main_weapon_id=weapon, **options))


def priority(bearer, opponent, **options):
    return resolve_priority(PriorityContext(bearer, opponent, **options))


def fanatic():
    return fighter("night-goblins-kaz", "fanatics", weapon="weapon.dagger")


def lahmia_vampire():
    return fighter("chaos-streets-undead-bloodlines", "lahmia-vampire",
                   weapon="weapon.sword", collection="trollheim",
                   special_rule_ids=("band--lahmia-power-lost-innocence",))


def test_the_shared_skill_is_the_operator_both_rules_bind():
    effect = effect_index("mordheim")["skill.always-strikes-first"].effect
    assert "skill.always-strikes-first" in effect.tags
    assert effect.priority == 1


def test_the_fanatic_compiles_the_printed_always_strikes_first_tag():
    compiled = fanatic()
    assert "skill.always-strikes-first" in compiled.global_effects.tags
    assert compiled.global_effects.priority == 1


def test_the_operator_raises_priority_above_the_ordinary_order():
    compiled = fanatic()
    ordinary = fighter()
    assert priority(compiled, ordinary).priority == 1
    assert priority(ordinary, compiled).priority == 0


def test_two_bearers_of_the_skill_tie_and_the_roll_breaks_it():
    # A spear shares the strike-first tier, so the ability ties and the order
    # falls to Initiative, exactly as the retained spec case records.
    compiled = fanatic()
    spear = fighter(weapon="weapon.spear")
    assert priority(compiled, spear, first_round=True).priority == 1
    assert priority(spear, compiled, first_round=True).priority == 1


def test_the_fanatic_keeps_strike_first_when_standing_up():
    compiled = fanatic()
    plain = fighter()
    assert priority(compiled, plain, first_round=False, stood_up=True).priority == 1
    # A warrior without the printed rule keeps the standing-up penalty.
    assert priority(plain, plain, first_round=False, stood_up=True).priority == -1


def test_lost_innocence_is_selectable_for_the_lahmia_vampire_alone():
    vampire = lahmia_vampire()
    assert "skill.always-strikes-first" in vampire.global_effects.tags
    with pytest.raises(ValueError):
        fighter("chaos-streets-undead-bloodlines", "strigoi-vampire",
                collection="trollheim",
                special_rule_ids=("band--lahmia-power-lost-innocence",))


def test_no_ordinary_initiative_advantage_defeats_lost_innocence():
    vampire = lahmia_vampire()
    quick = fighter(initiative=10)
    assert priority(vampire, quick).priority == 1
    assert priority(quick, vampire).priority == 0
    # The printed exception survives standing up, and it is the only case that
    # suppresses the standing-up penalty.
    assert priority(vampire, quick, first_round=False, stood_up=True).priority == 1
