"""Native virtues do not require the granting of foreign virtues."""
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


@pytest.mark.parametrize("collection, band", [
    ("mordheim", "bretonnian-knights"),
    ("trollheim", "chaos-streets-bretonnian-knights"),
])
def test_native_virtue_keeps_profile_access_restrictions(collection, band):
    for profile in ("questing-knight", "knights-errant", "squires"):
        result = compile_fighter(FighterBuild(
            "mordheim", collection=collection, band_id=band, profile_id=profile,
            special_rule_ids=("band--virtue-of-valour",),
        ))
        assert "skill.virtue-of-valour" in result.global_effects.tags
    with pytest.raises(ValueError, match="special rule is not available"):
        compile_fighter(FighterBuild(
            "mordheim", collection=collection, band_id=band, profile_id="men-at-arms",
            special_rule_ids=("band--virtue-of-valour",),
        ))


def test_foreign_virtue_still_requires_its_grant():
    with pytest.raises(ValueError, match="foreign Bretonnian Virtue requires Renowned Virtue"):
        compile_fighter(FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
            special_rule_ids=("band--virtue-of-valour",),
        ))
