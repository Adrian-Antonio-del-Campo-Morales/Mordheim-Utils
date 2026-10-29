"""Construction contract for the Silent Brotherhood buckler item.

The check owns the compiler: it proves that the cloak the band prints is the
buckler item the catalogue names, that a master without it keeps no parry, and
that a profile the equipment list does not give the cloak to stays refused.
The parry/reroll execution of that item belongs to the modular suite.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_combat.modular.state import _parry_capacity


def bare(band, profile, **options):
    """A profile the equipment lists leave unequippable, compiled with its own kit."""
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile, **options))


def test_silent_brotherhood_cloak_is_the_buckler_item_it_names():
    master = bare("silent-brotherhood-sc", "silent-master", off_hand_id="defence.buckler")
    assert _parry_capacity(master) == 1
    assert _parry_capacity(bare("silent-brotherhood-sc", "silent-master")) == 0
    # A profile the equipment list does not give the cloak to stays refused.
    with pytest.raises(ValueError, match="not available"):
        bare("silent-brotherhood-sc", "thugs", off_hand_id="defence.buckler")
