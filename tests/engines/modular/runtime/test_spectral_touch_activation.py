"""Engine contracts separated from the corresponding rule witnesses."""


from dataclasses import replace


import numpy as np


import pytest


from mordheim_combat.kernel import compile_duel_plan, require_optimized_support


from mordheim_combat.modular import simulate_duel as simulate_modular


from mordheim_combat.modular import duel


from mordheim_combat.modular.pools import _resolve_attack_pool


from mordheim_combat.modular.rounds import resolve_round


from mordheim_combat.modular.state import initialize_duel, initialize_fighter




from mordheim_combat.vectorized import simulate_batch, simulate_duel, simulate_duel_parallel




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


#: The oracle's own contract for this pair: the plain fighter prints no
#: Leadership and must test Fear against the fear-causing host.
LEADERSHIP_CONTRACT = 'explicit non-negative integer Leadership'


@pytest.mark.parametrize('second', [False, True])
@pytest.mark.parametrize('backend', ['auto', 'numpy'])
def test_public_optimized_paths_share_the_oracle_contract(host, plain, second, backend):
    """The canonical host is admitted by the NumPy gate.

    ``trait.spectral-touch`` and the host's other contracts are connected to
    NumPy, so no optimized backend refuses before dispatch any more. The pair
    itself is refused by the same rule in both engines: the plain fighter
    prints no Leadership, so its Fear test raises the oracle's contract.
    """
    pair = (plain, host) if second else (host, plain)
    with pytest.raises(ValueError, match=LEADERSHIP_CONTRACT):
        simulate_modular(DuelRequest(*pair, simulations=1))
    with pytest.raises(ValueError, match=LEADERSHIP_CONTRACT):
        simulate_duel(DuelRequest(*pair, simulations=1), backend=backend)


@pytest.mark.parametrize('second', [False, True])
def test_low_level_optimized_paths_share_the_oracle_contract(host, plain, second):
    pair = (plain, host) if second else (host, plain)
    # The legacy plan (no backend) keeps the frozen native gate and refuses
    # before execution; the NumPy entries execute and raise the oracle's
    # Leadership contract.
    with pytest.raises(ValueError, match='modular engine'):
        compile_duel_plan(*pair)
    compile_duel_plan(*pair, backend='numpy')
    calls = (lambda: simulate_batch(*pair, 1, np.random.default_rng(0), 1),
             lambda: simulate_duel_parallel(DuelRequest(*pair, simulations=1)))
    for call in calls:
        with pytest.raises(ValueError, match=LEADERSHIP_CONTRACT):
            call()


def test_guard_also_rejects_weapon_scoped_spectral_effect(plain):
    # Synthetic transport control: Spirit Knife remains source-gated/F025.
    synthetic = replace(plain, main_weapon=replace(plain.main_weapon,
                        tags=(*plain.main_weapon.tags, TAG)))
    with pytest.raises(ValueError, match='Spectral Touch.*modular'):
        require_optimized_support(synthetic, plain)
    # NumPy connects the behaviour, so only the native gate still refuses it.
    require_optimized_support(synthetic, plain, backend='numpy')
    require_optimized_support(plain, plain)
