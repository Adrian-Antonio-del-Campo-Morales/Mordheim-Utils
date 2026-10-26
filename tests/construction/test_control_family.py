"""Construction rejects control powers for ineligible recipients."""
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild



def test_khemrian_seduction_rejects_an_ineligible_recipient():
    rule = "band--lahmian-special-skills-seduction"
    build = dict(band_id="khemri-lahmian-brotherhood", collection="trollheim")
    with pytest.raises(ValueError, match="special rule is not available"):
        compile_fighter(FighterBuild(
            "mordheim", profile_id="skeleton-warriors", special_rule_ids=(rule,), **build))
