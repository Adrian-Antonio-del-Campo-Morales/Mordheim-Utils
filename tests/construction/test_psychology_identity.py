"""Knight-of-Purity construction follows the supplied hero promotion."""
import pytest
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root

ROOT = knowledge_root()

def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options), ROOT)


def test_knight_of_purity_construction_requires_a_supplied_hero_promotion():
    ordinary = canonical('watchmen-mim', 'sergeants', 'weapon.club')
    assert 'mechanic.automatic-leadership' not in ordinary.global_effects.tags
    with pytest.raises(ValueError, match='Hero of the Watch'):
        canonical('watchmen-mim', 'officers', 'weapon.club',
                  trait_overrides={'crusader_of_law': True})
    promoted = canonical('watchmen-mim', 'officers', 'weapon.club',
                         variant_ids=('promotion.hero',), trait_overrides={'crusader_of_law': True})
    assert 'mechanic.automatic-leadership' in promoted.global_effects.tags
