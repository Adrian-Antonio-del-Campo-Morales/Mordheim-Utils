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


from mordheim_combat.native._combat_compile import compile_duel


from mordheim_combat.vectorized import simulate_batch, simulate_duel, simulate_duel_parallel


from mordheim_combat_lab.application.catalogue import CombatCatalogue


from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice


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
@pytest.mark.parametrize('backend', ['auto', 'numpy', 'native'])
def test_public_optimized_paths_refuse_unported_canonical_effect(host, plain, second, backend):
    """The canonical host still carries a contract pending on the native gate.

    ``trait.spectral-touch`` itself is connected to NumPy; the gate-level
    admission is pinned by ``test_guard_also_rejects_weapon_scoped_spectral_
    effect``. The host's local-modifier contract keeps the native (and auto)
    gates refusing before dispatch. NumPy has since connected it, so its gate
    admits the pair and execution surfaces the modular reference's own
    refusal: this frozen defender carries no explicit Leadership, so the fear
    test against the host is unresolvable on every engine.
    """
    pair = (plain, host) if second else (host, plain)
    if backend == 'numpy':
        require_optimized_support(*pair, backend='numpy')
        refusal = 'explicit non-negative integer Leadership'
        with pytest.raises(ValueError, match=refusal):
            simulate_modular(DuelRequest(*pair, simulations=1))
        with pytest.raises(ValueError, match=refusal):
            simulate_duel(DuelRequest(*pair, simulations=1), backend=backend)
    else:
        with pytest.raises(ValueError, match='modular engine'):
            simulate_duel(DuelRequest(*pair, simulations=1), backend=backend)


@pytest.mark.parametrize('second', [False, True])
def test_low_level_optimized_paths_refuse_before_execution(host, plain, second):
    pair = (plain, host) if second else (host, plain)
    # The native-gated entries still refuse before execution and name the
    # host's pending local-modifier contract, not Spectral Touch.
    for call in (lambda: compile_duel_plan(*pair), lambda: compile_duel(*pair)):
        with pytest.raises(ValueError, match='modular engine'):
            call()
    # The NumPy entries are fully connected: the gate admits the pair and
    # execution surfaces the modular reference's refusal of the frozen
    # defender's missing Leadership instead.
    for call in (lambda: simulate_batch(*pair, 1, np.random.default_rng(0), 1),
                 lambda: simulate_duel_parallel(DuelRequest(*pair, simulations=1))):
        with pytest.raises(ValueError, match='explicit non-negative integer Leadership'):
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
