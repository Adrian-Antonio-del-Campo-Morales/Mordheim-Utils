"""Enemy identity, conditioned Leadership and qualified Hatred.

Each Hatred clause is exercised three ways on the canonical compiler and the
modular hit-reroll consumer: activation against the printed hated identity, a
negative control that must not fire, and the printed exception.  Burn the Witch
reads the compiled spellcaster identity (no spell is cast), Hang the Bandit the
canonical Bandit/Outlaw warband class, and Profound Hatred every opposing
warband except the Sisters of Sigmar.
"""
from __future__ import annotations

import sys
from dataclasses import replace

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import _combined_effect, _hit_reroll
from mordheim_combat.modular.state import initialize_fighter
from tests.engines.shared.dice import StrictDice
from mordheim_core.models import FighterBuild
from pathlib import Path
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



# The shared root resolves the documented knowledge overlay when one is exported,
# so this family reads the same tree the rest of the construction suite reads.
ROOT = Path(__file__).resolve().parents[4] / "sources" / "knowledge"


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim"):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon), ROOT)


def rerolls(attacker, defender, *, first_round=True):
    return _hit_reroll(attacker, defender, attacker.main_weapon,
                       _combined_effect(attacker, attacker.main_weapon), first_round, False)


# --- Fanatical (Maximilian the Mad) ----------------------------------------

MAXIMILIAN = "hireling.dramatis.maximilian-the-mad"


def maximilian(**options):
    """The source's own bearer, through his printed double-handed kit."""
    return compile_fighter(FighterBuild("mordheim",
        band_id="hirelings.dramatis-personae.1b", profile_id=MAXIMILIAN, collection="mordheim",
        main_weapon_id="weapon.double-handed-weapon",
        owned_item_ids=(f"{MAXIMILIAN}.item.double-handed-holy-weapon",), **options), ROOT)


def test_fanatical_still_takes_the_ordinary_hatred_exemptions(precompiled):
    """His own Frenzy and the shared gates suppress the printed Hatred."""
    compiled = precompiled()
    fanatic, target = compiled.first, compiled.second
    assert fanatic.global_effects.frenzy  # the separate Religious Fervour clause
    assert _hit_reroll(fanatic, target, fanatic.main_weapon,
                       _combined_effect(fanatic, fanatic.main_weapon), True, False) is True
    assert _hit_reroll(fanatic, target, fanatic.main_weapon,
                       _combined_effect(fanatic, fanatic.main_weapon), True, False,
                       frenzy=True) is False


def test_fanatical_reaches_the_attack_tape_only_for_a_listed_warband():
    """The canonical pipeline asks for the reroll, and only where the list says so.

    A tape that is not consumed proves the opposite: the exemption keeps the
    listed reroll out of the dice stream while Frenzy holds, and the unlisted
    warband is never offered it at all.
    """
    fanatic = maximilian()
    init = StrictDice([])
    own = initialize_fighter(fanatic, init, "f")
    init.finish()
    assert own.frenzy
    for band, profile, reroll in (("carnival-of-chaos", "carnival-master", False),
                                  ("witch-hunters", "witch-hunters", False)):
        target = canonical(band, profile)
        tape = StrictDice([{"key": "f.hit", "value": 1}]
                          + ([{"key": "f.hit.reroll", "value": 1}] if reroll else []))
        result = resolve_reference_attack(fanatic, target, own, initialize_fighter(target, tape, "t"),
                                          fanatic.main_weapon, tape, key="f", first_round=True)
        tape.finish()
        assert not result.hit
    # With Frenzy not active the printed list is the only difference left.
    calm = replace(own, frenzy=False)
    for band, profile, reroll in (("carnival-of-chaos", "carnival-master", True),
                                  ("witch-hunters", "witch-hunters", False)):
        target = canonical(band, profile)
        tape = StrictDice([{"key": "f.hit", "value": 1}]
                          + ([{"key": "f.hit.reroll", "value": 1}] if reroll else []))
        result = resolve_reference_attack(fanatic, target, calm, initialize_fighter(target, tape, "t"),
                                          fanatic.main_weapon, tape, key="f", first_round=True)
        tape.finish()
        assert not result.hit
