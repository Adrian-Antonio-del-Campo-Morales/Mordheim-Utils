"""Magic Acorn construction eligibility."""
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild



def test_magic_acorn_requires_a_hero():
    with pytest.raises(ValueError,match='Hero|hero'):
        compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,3,1),
            defence_ids=('defence.magic-acorn',)))
