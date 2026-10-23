"""Construction contracts split from ``tests/engines/modular/test_dark_jester_and_related_families.py``.

These two tests assert what the canonical compiler and its compiled-consumer
helpers read: the admitted mechanic records of the Dark Jester and its related
families, the refusals that must not be guessed, and the supplied charge/size
facts reaching the shared hit and wound contexts.  They keep the canonical
``FighterBuild``/``compile_fighter`` route and do not execute a duel.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat.modular.contexts import (_combined_effect, prepare_hit_context,
    prepare_wound_context)
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import _profile_rule_mechanics
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


class Tape:
    """Listed faces are consumed per key in order; unlisted requests answer 1."""

    def __init__(self, rolls: dict[str, list[int]] | None = None):
        self.rolls = {key: list(faces) for key, faces in (rolls or {}).items()}
        self.requests: list[str] = []

    def roll(self, request):
        key = request.key
        self.requests.append(key)
        queue = self.rolls.get(key)
        if key in self.rolls and not queue:
            raise AssertionError(f"duplicate roll: {key}")
        if (key.endswith(('.wound', '.trip-roll', '.special.ward'))
                or '.injury.' in key) and not queue:
            raise AssertionError(f"unexpected mechanic roll: {key}")
        value = queue.pop(0) if queue else 1
        if not 1 <= value <= request.sides:
            raise ValueError(f"invalid fixture face {value} for D{request.sides}")
        return value

    def produced(self, key: str) -> int:
        """The number of times that key was asked for."""
        return sum(1 for entry in self.requests if entry == key)

    def finish(self):
        """Every listed face was consumed exactly once."""
        leftover = {key: faces for key, faces in self.rolls.items() if faces}
        if leftover:
            raise AssertionError(f"unused listed rolls: {sorted(leftover)}")


class ScriptedChoices:
    """Every decision must be explicitly listed and consumed exactly once."""

    def __init__(self, choices: dict[str, bool] | None = None):
        self.choices = dict(choices or {})
        self.offered: list[str] = []

    def choose(self, key: str, context=None) -> bool:
        self.offered.append(key)
        if key in self.choices:
            value = self.choices.pop(key)
            if not isinstance(value, bool):
                raise ValueError("decision values must be booleans")
            return value
        raise AssertionError(f"unexpected or duplicate decision: {key}")

    def finish(self):
        if self.choices:
            raise AssertionError(f"unused decisions: {sorted(self.choices)}")


def fighter(*tags: str, strength: int = 3):
    """A plain compiled fighter carrying only the supplied mechanic tag(s)."""
    base = compile_fighter(FighterBuild("mordheim",
        Characteristics(3, 3, strength, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour"))
    return replace(base, global_effects=replace(base.global_effects,
        tags=(*base.global_effects.tags, *tags)))


def duel(first, second, *, dice=None, choices=None, context=None):
    """One resolve_round on the supplied fixture pair."""
    dice = dice if dice is not None else Tape()
    choices = choices if choices is not None else ScriptedChoices()
    if context is None:
        context = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(first, second, dice, context=context)
    return resolve_round(first, second, state, dice, choices)


# The chooser offers the dodge, the banter and the trip in that order and
# exactly one may be accepted (the round's chosen trick).
TRIP_OFFERS = {f"round.0.first.jester-trick.{slot}": face for slot, face in (
    ("dodge_trick_active", False), ("banter_trick_active", False),
    ("trip_trick_active", True))}


@pytest.mark.phase2_construction
def test_canonical_bindings_and_honest_admission():
    packages = {p.band['id']: p for p in combat_packages('mordheim')}
    jester = compile_fighter(FighterBuild('mordheim',
        band_id='hirelings.dramatis-personae.2a',
        profile_id='hireling.dramatis.the-dark-jester-in-mordheim',
        main_weapon_id='weapon.club'))
    assert {'mechanic.confound-and-confuse', 'mechanic.dodge-sidestepper',
            'mechanic.babbling-banter'} <= set(jester.global_effects.tags)
    dice = Tape({'round.0.first.attack.0.hit': [6],
                 'round.0.first.attack.0.trip-roll': [1]})
    choices = ScriptedChoices({**TRIP_OFFERS, 'round.0.first.attack.0.trip.hit': True})
    result = duel(jester, fighter(), dice=dice, choices=choices)
    assert not result.attacks[0].wounded
    assert dice.produced('round.0.first.attack.0.wound') == 0
    assert choices.offered.count('round.0.first.attack.0.trip.hit') == 1
    dice.finish()
    choices.finish()
    for band, profile, mechanic in (
        ('hirelings.hired-sword.1a', 'hireling.hired-sword.imperial-assassin', 'skill.backstabber'),
        ('hirelings.hired-sword.2a', 'hireling.hired-sword.cursed-hillman', 'rule.thin-flesh'),
        ('hirelings.hired-sword.2a', 'hireling.hired-sword.halfling-knight', 'rule.slay-large-creature'),
    ):
        package = packages[band]
        record = next(p for p in package.profiles if p['id'] == profile)
        assert mechanic in _profile_rule_mechanics(package, record)
    # The bonus is bound, but the printed cavalry spear still has no
    # canonical item mapping. Do not silently substitute an ordinary spear.
    with pytest.raises(ValueError, match='unique equipment needs a canonical combat mapping'):
        compile_fighter(FighterBuild('mordheim',
            band_id='hirelings.hired-sword.2a', profile_id='hireling.hired-sword.halfling-knight',
            main_weapon_id='weapon.sword'))
    # The intrinsic clauses of three carriers now resolve, so they compile
    # through their printed kits instead of being refused for a pending clause.
    crow = compile_fighter(FighterBuild('mordheim',
        band_id='hirelings.dramatis-personae.1b', profile_id='hireling.dramatis.crow-master-the',
        main_weapon_id='weapon.quarter-staff'))
    assert {'mechanic.mantle-of-crows', 'mechanic.needle-and-thread'} <= set(crow.global_effects.tags)
    # The default weapon of an omitted main selection is the printed Staff of
    # this kit; the distinct explicit weapons outside the kit stay refused by
    # the matcher, never silently substituted.
    crow_default = compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b',
        profile_id='hireling.dramatis.crow-master-the'))
    assert 'weapon.quarter-staff' in crow_default.main_weapon.tags
    with pytest.raises(ValueError, match='complete legal printed kit'):
        compile_fighter(FighterBuild('mordheim', band_id='hirelings.dramatis-personae.1b',
            profile_id='hireling.dramatis.crow-master-the', main_weapon_id='weapon.mace'))
    hillman = compile_fighter(FighterBuild('mordheim',
        band_id='hirelings.hired-sword.2a', profile_id='hireling.hired-sword.cursed-hillman'))
    assert {'mechanic.hillman-lycanthrope', 'rule.thin-flesh'} <= set(hillman.global_effects.tags)
    # Poisoner: one supplied battle poison is shared by the bearer's weapons, and
    # an absent or contradictory choice is refused by name instead of guessed.
    assassin = FighterBuild('mordheim', band_id='hirelings.hired-sword.1a',
        profile_id='hireling.hired-sword.imperial-assassin', main_weapon_id='weapon.sword')
    for incomplete in (assassin, replace(assassin, main_poison_id='poison.black-lotus',
                                         off_poison_id='poison.black-venom')):
        with pytest.raises(ValueError, match='one shared Black Lotus or Dark Venom'):
            compile_fighter(incomplete)
    poisoned = compile_fighter(replace(assassin, main_poison_id='poison.black-lotus'))
    assert 'skill.backstabber' in poisoned.global_effects.tags


@pytest.mark.phase2_construction
def test_supplied_charge_and_size_reach_compiled_consumers():
    owner = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1),
        trait_overrides={'starting_skills': ['skill.backstabber', 'rule.slay-large-creature']},
        condition_ids=('condition.unseen-charge',)))
    victim = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1),
        condition_ids=('condition.large-target',)))
    assert 'condition.unseen-charge' in owner.global_effects.tags
    assert 'size.large' in victim.global_effects.tags
    own = initialize_fighter(owner, Tape(), 'first')
    other = initialize_fighter(victim, Tape(), 'second')
    effect = _combined_effect(owner, owner.main_weapon)
    assert prepare_hit_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=True, charging=True).modifier == 1
    assert prepare_wound_context(owner, victim, own, other, owner.main_weapon, effect,
        first_round=True, charging=True).strength == 4
    for mechanic, tag in (('rule.thin-flesh', 'rule.thin-flesh'),
                         ('mechanic.mantle-of-crows', 'mechanic.mantle-of-crows')):
        compiled = compile_fighter(FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1),
            trait_overrides={'starting_skills': [mechanic]}))
        assert tag in compiled.global_effects.tags
