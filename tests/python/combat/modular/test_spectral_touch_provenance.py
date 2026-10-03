"""F056 — Spectral Touch mixed-hit provenance witnesses on the real modular pool.

The accepted Q019 contract (R1–R4) gives every successful attack its own
natural-die provenance: only the attack whose *final* hit die is a natural six
adds the single extra wound, and it adds it before that attack's ordinary wound
roll. This file pins that per-hit reading with two successful hits whose
physical faces are 6 and 5 in both orders, so a whole-pool/propagated
provenance regression becomes observable in the maintained corpus.

The cases run the real ``_resolve_attack_pool`` with explicit synthetic
``CompiledFighter`` inputs, the maintained ``initialize_fighter`` helper and the
maintained strict dice/decision tapes. They never call ``compile_fighter`` or
construction helpers: the concurrent warrior-construction centralization owns
that frontier, and these inputs prove engine composition, not canonical
activation, equipment legality or product construction.

Synthetic input provenance (engine composition only):
  * profile shape ``Characteristics(3, 3, 3, 4, 3, 1)`` — WS3/S3/T3/W4/I3/A1,
    mirroring the F007 review probe;
  * main ``weapon.axe``, no off hand, no extra attacks;
  * the attacker carries the pilot ``trait.spectral-touch`` tag; canonical
    Spirit Host activation is F008 and is not claimed here;
  * no armour (save 7), no natural save, no ward/regeneration, no parry
    capacity and no reaction traits, so no die can hide the difference;
  * hit faces 6/5 both beat the WS3-vs-WS3 target of 4; both ordinary wound
    rolls are 1, which always fails S3 vs T3 (needs 4); the extra contribution
    is dice-free by the accepted contract (review B7).
"""
from pathlib import Path
import sys

import pytest

from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, CompiledFighter, EffectSet

POOL_KEY = 'provenance'
HIT_FACES = ((6, 5), (5, 6))
# S3 vs T3 needs 4; a 1 always fails, so the ordinary contribution is inert.
WOUND_FAILS = 1
NO_SAVE = 7


def _fighter(*, spectral):
    return CompiledFighter(
        fighter_id='synthetic:f056-spectral' if spectral else 'synthetic:f056-plain',
        characteristics=Characteristics(3, 3, 3, 4, 3, 1),
        main_weapon=EffectSet(tags=('weapon.axe',)),
        off_hand=None,
        global_effects=EffectSet(tags=('trait.spectral-touch',) if spectral else ()),
        armour_save=NO_SAVE, helmet_save=NO_SAVE, natural_armour_save=NO_SAVE,
        unarmed_weapon=EffectSet(tags=('weapon.fist',)),
    )


def _state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, 'init')
    dice.finish()
    return result


def _mixed_tape(faces):
    """Exact source-derived order: both hit dice, then each hit's wound die."""
    return [
        {'key': f'{POOL_KEY}.attack.0.hit', 'value': faces[0]},
        {'key': f'{POOL_KEY}.attack.1.hit', 'value': faces[1]},
        {'key': f'{POOL_KEY}.attack.0.wound', 'value': WOUND_FAILS},
        {'key': f'{POOL_KEY}.attack.1.wound', 'value': WOUND_FAILS},
    ]


def _run_pool(attacker, defender, tape):
    dice, decisions = StrictDice(list(tape)), StrictDecisions([])
    attacker_state, defender_state, outcomes = _resolve_attack_pool(
        attacker, defender, _state(attacker), _state(defender), 2, dice,
        key=POOL_KEY, first_round=False, charging=False, decisions=decisions,
    )
    dice.finish()
    decisions.finish()
    return defender_state, outcomes, dice.requests, decisions


def assert_mixed_provenance(faces, *, spectral):
    """Strict mixed-hit witness shared by the maintained and mutant cases.

    Every check is semantic and self-contained; the mutant case below relies on
    the damage assertion to reject a propagated whole-pool provenance.
    """
    defender_state, outcomes, requests, decisions = _run_pool(
        _fighter(spectral=spectral), _fighter(spectral=False), _mixed_tape(faces),
    )
    keys = [request.key for request in requests]
    # Contract item 7: all hit dice are prepared before any wound is resolved.
    assert keys[:2] == [f'{POOL_KEY}.attack.0.hit', f'{POOL_KEY}.attack.1.hit'], (
        f'collective hit preparation order changed: {keys}')
    assert keys[2:] == [f'{POOL_KEY}.attack.0.wound', f'{POOL_KEY}.attack.1.wound'], (
        f'per-hit wound order changed: {keys}')
    assert len(outcomes) == 2, f'outcome count {len(outcomes)} != 2'
    assert [outcome.hit for outcome in outcomes] == [True, True], (
        f'both faces beat the 4+ target: {[outcome.hit_roll for outcome in outcomes]}')
    assert [outcome.hit_roll for outcome in outcomes] == list(faces), (
        f'outcome order {[outcome.hit_roll for outcome in outcomes]} != {list(faces)}')
    expected_damages = ([1, 0] if faces == (6, 5) else [0, 1]) if spectral else [0, 0]
    damages = [outcome.damage for outcome in outcomes]
    assert damages == expected_damages, f'per-hit damages {damages} != {expected_damages}'
    expected_wounds = 3 if spectral else 4
    assert defender_state.wounds == expected_wounds, (
        f'final wounds {defender_state.wounds} != {expected_wounds}')
    assert decisions.requests == [], f'unexpected decisions: {decisions.requests}'
    assert not any('spectral-touch' in key for key in keys), f'hidden extra roll: {keys}'
    return defender_state, outcomes


@pytest.mark.parametrize('faces', HIT_FACES)
def test_mixed_successful_hits_keep_per_hit_natural_six_provenance(faces):
    """Faces 6/5: only the hit whose own die is six adds the extra wound."""
    assert_mixed_provenance(faces, spectral=True)


@pytest.mark.parametrize('faces', HIT_FACES)
def test_mixed_hits_without_spectral_touch_add_no_extra_wound(faces):
    """The same faces without the trait hit twice and add nothing."""
    assert_mixed_provenance(faces, spectral=False)


def _pooled_provenance_mutant():
    """In-memory copy of ``pools.py`` where every prepared hit shares the flag.

    The single-token substitution is the registered F1/F056 reproducer:
    ``natural_hit_six=any(p.natural_hit_six for _, p in prepared_attacks)``.
    No live engine file is edited; the namespace is discarded on return.
    """
    from mordheim_combat.modular import pools

    source = Path(pools.__file__).read_text(encoding='utf-8')
    source = source.replace(
        'from .attacks import resolve_reference_attack',
        'from mordheim_combat.modular.attacks import resolve_reference_attack',
    ).replace(
        'from .equipment import whipcrack_weapon',
        'from mordheim_combat.modular.equipment import whipcrack_weapon',
    )
    anchor = 'natural_hit_six=prepared.natural_hit_six, defences_resolved=True,'
    assert source.count(anchor) == 2
    replacement = ('natural_hit_six=any(p.natural_hit_six for _, p in prepared_attacks),'
                   ' defences_resolved=True,')
    namespace = {'__name__': 'isolated_pooled_provenance_mutant'}
    exec(compile(source.replace(anchor, replacement),
                 '<isolated pooled provenance mutation>', 'exec'), namespace)
    return namespace['_resolve_attack_pool']


@pytest.mark.parametrize('faces', HIT_FACES)
def test_pooled_provenance_mutant_is_rejected_by_the_mixed_witness(monkeypatch, faces):
    """The maintained witness passes on the engine and fails under the mutant."""
    assert_mixed_provenance(faces, spectral=True)
    monkeypatch.setattr(sys.modules[__name__], '_resolve_attack_pool',
                        _pooled_provenance_mutant())
    with pytest.raises(AssertionError) as failure:
        assert_mixed_provenance(faces, spectral=True)
    message = str(failure.value)
    assert 'per-hit damages' in message, (
        f'mutant detected outside the semantic damage assertion: {message}')
    assert '[1, 1]' in message, (
        f'mutant did not pool both extras into one damage each: {message}')
