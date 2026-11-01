"""The modular driver rejects an unresolved Fear test without Leadership."""
import pytest

from mordheim_combat.modular import simulate_duel
from mordheim_core.models import DuelRequest


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
def test_modular_requires_explicit_leadership_against_the_canonical_host(host, plain, second):
    pair = (plain, host) if second else (host, plain)
    with pytest.raises(ValueError, match='explicit non-negative integer Leadership'):
        simulate_duel(DuelRequest(*pair, simulations=1))
