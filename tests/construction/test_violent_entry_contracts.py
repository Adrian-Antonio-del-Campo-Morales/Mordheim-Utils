"""Construction contracts split from ``tests/engines/modular/test_violent_entry_supplied_summon.py``.

These tests assert on the canonical compiler itself -- the printed profile
facts and the refusals it produces -- so they keep calling
``compile_fighter`` instead of reading frozen engine inputs.
"""
import pytest
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.selection import _profile_rule_mechanics
from mordheim_core.models import Characteristics, FighterBuild


SUMMON = "condition.summoned-this-turn"


BAND = "call-of-the-night-haint-mim"


PROFILE = "malignant-spirits"


def test_the_supplied_fact_needs_its_malignant_spirits_recipient():
    with pytest.raises(ValueError, match="Malignant Spirits recipient"):
        compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1),
            main_weapon_id="weapon.mace", condition_ids=(SUMMON,)))
    with pytest.raises(ValueError, match="Malignant Spirits recipient"):
        compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id="revenants",
            condition_ids=(SUMMON,)))


def test_the_rule_binds_the_bonus_to_the_supplied_fact_without_granting_it():
    package = next(p for p in combat_packages("mordheim") if p.band["id"] == BAND)
    rule = next(r for r in package.special_rules if r["id"] == "malignant-spirits--violent-entry")
    runtime = rule["runtime"]
    assert runtime["scope"] == "YES" and runtime["implemented"] == "YES"
    assert runtime["grant"] == "none"
    assert [effect["binding"] for effect in runtime["effects"]
            if effect["binding"]] == [{"kind": "mechanic", "id": SUMMON}]
    record = next(p for p in package.profiles if p["id"] == PROFILE)
    # An unselected spirit gets the charge from its printed profile, never this bonus.
    assert SUMMON not in _profile_rule_mechanics(package, record)
    plain = compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=PROFILE,
        main_weapon_id="weapon.sword"))
    assert SUMMON not in plain.global_effects.tags
    assert plain.global_effects.charge_strength_bonus == 0
