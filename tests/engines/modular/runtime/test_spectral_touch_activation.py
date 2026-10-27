"""Engine contracts separated from the corresponding rule witnesses."""


from dataclasses import replace


import pytest


from mordheim_combat.kernel import compile_duel_plan, require_optimized_support


from mordheim_combat.modular import simulate_duel as simulate_modular


from mordheim_combat.modular import duel


from mordheim_combat.modular.pools import _resolve_attack_pool


from mordheim_combat.modular.rounds import resolve_round


from mordheim_combat.modular.state import initialize_duel, initialize_fighter




from mordheim_combat.native import simulate_duel




from tests.engines.shared.dice import StrictDecisions, StrictDice


from mordheim_core.models import Characteristics, DuelContext, DuelRequest


TAG = 'trait.spectral-touch'


@pytest.fixture(scope='module')
def host(cases):
    return cases[
        'unit/modular/test_spectral_touch_activation/'
        'test_canonical_binding_compiles_exact_consumer_tag_and_legal_natural_weapon-0-0'
    ].first


@pytest.fixture(scope='module')
def plain(cases):
    return cases[
        'unit/modular/test_spectral_touch_activation/'
        'test_canonical_three_attack_pool_retains_each_hits_own_six-0-0'
    ].second


@pytest.mark.parametrize('second', [False, True])
def test_public_optimized_paths_refuse_unported_canonical_effect(host, plain, second):
    """The canonical host still carries another pending contract.

    The gate-level admission is pinned by ``test_guard_also_rejects_weapon_
    scoped_spectral_effect``. This host also carries a pending local-modifier
    contract, so the native backend refuses before dispatch and names that
    first contract, not Spectral Touch.
    """
    pair = (plain, host) if second else (host, plain)
    with pytest.raises(ValueError, match='modular engine'):
        simulate_duel(DuelRequest(*pair, simulations=1))


@pytest.mark.parametrize('second', [False, True])
def test_low_level_optimized_paths_refuse_before_execution(host, plain, second):
    pair = (plain, host) if second else (host, plain)
    calls = (lambda: compile_duel_plan(*pair, backend='native'),
             lambda: simulate_duel(DuelRequest(*pair, simulations=1)))
    # Every entry still refuses, but the host's pending local-modifier contract
    # is named before the connected Spectral Touch behaviour.
    for call in calls:
        with pytest.raises(ValueError, match='modular engine'):
            call()


def test_guard_also_rejects_weapon_scoped_spectral_effect(plain):
    # Synthetic transport control: Spirit Knife remains source-gated/F025.
    synthetic = replace(plain, main_weapon=replace(plain.main_weapon,
                        tags=(*plain.main_weapon.tags, TAG)))
    with pytest.raises(ValueError, match='Spectral Touch.*modular'):
        require_optimized_support(synthetic, plain)
    # The NumPy gate connects the behaviour; only the native gate refuses it.
    require_optimized_support(synthetic, plain, backend='numpy')
    require_optimized_support(plain, plain)
