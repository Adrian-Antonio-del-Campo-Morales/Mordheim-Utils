"""The printed ``always strikes first`` stanza and its specifications.

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
  priority that prevails over Initiative and ordinary weapon modifiers"* - both
  origins use the compiler binding that sets priority 10, while keeping the
  canonical mechanic tag the stand-up rule reads.
"""
from __future__ import annotations

import sys
import pytest

from mordheim_combat.phases import PriorityContext, resolve_priority
from mordheim_core.models import Characteristics, FighterBuild


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


def test_the_operator_raises_priority_above_the_ordinary_order(precompiled):
    compiled, ordinary = precompiled().first, precompiled().second
    assert priority(compiled, ordinary).priority == 10
    assert priority(ordinary, compiled).priority == 0


def test_two_bearers_of_the_skill_tie_and_the_roll_breaks_it(precompiled):
    # A spear shares the strike-first tier, so the ability ties and the order
    # falls to Initiative, exactly as the retained spec case records.
    compiled, spear = precompiled().first, precompiled().second
    assert priority(compiled, spear, first_round=True).priority == 10
    assert priority(spear, compiled, first_round=True).priority == 1


def test_the_fanatic_keeps_strike_first_when_standing_up(precompiled):
    compiled = precompiled().first
    plain = precompiled().second
    assert priority(compiled, plain, first_round=False, stood_up=True).priority == 10
    # A warrior without the printed rule keeps the standing-up penalty.
    assert priority(plain, plain, first_round=False, stood_up=True).priority == -1


def test_no_ordinary_initiative_advantage_defeats_lost_innocence(precompiled):
    vampire, quick = precompiled().first, precompiled().second
    assert priority(vampire, quick).priority == 10
    assert priority(quick, vampire).priority == 0
    # The printed exception survives standing up, and it is the only case that
    # suppresses the standing-up penalty.
    assert priority(vampire, quick, first_round=False, stood_up=True).priority == 10
