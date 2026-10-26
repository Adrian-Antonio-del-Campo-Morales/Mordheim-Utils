"""Knowledge declarations and bindings separated from modular rule execution."""

import pytest


def test_contract_publishes_the_condition_scoped_denial():
    from mordheim_construction.contracts import effect_index
    effect = effect_index("mordheim")["weapon.misericordia"].effect
    assert effect.ignore_armour_against_knocked_down is True
    # The generic dagger penalty is unchanged.
    assert effect.target_armour_bonus == 1
