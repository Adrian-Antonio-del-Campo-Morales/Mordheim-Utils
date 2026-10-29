"""Knowledge declarations and bindings separated from modular rule execution."""

import pytest

from mordheim_construction.contracts import effect_index


def test_the_shared_skill_is_the_operator_both_rules_bind():
    effect = effect_index("mordheim")["skill.always-strikes-first"].effect
    assert "skill.always-strikes-first" in effect.tags
    assert effect.priority == 1
