"""Construction contract for Spectral Touch recipients.

Only the printed Spirit Hosts carry the Spectral Touch grant; the other canonical
profiles of the band compile without the consumer tag.  Running the grant is the
modular suite's job and stays there.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild

BAND = 'call-of-the-night-haint-mim'
TAG = 'trait.spectral-touch'


@pytest.mark.parametrize('profile', ['cairn-wraith', 'corpse-master', 'tomb-banshee',
                                    'malignant-spirits', 'revenants', 'poltergeists', 'mourngul'])
def test_other_canonical_profiles_do_not_receive_spectral_touch(profile):
    fighter = compile_fighter(FighterBuild('mordheim', band_id=BAND, profile_id=profile))
    assert TAG not in fighter.global_effects.tags
