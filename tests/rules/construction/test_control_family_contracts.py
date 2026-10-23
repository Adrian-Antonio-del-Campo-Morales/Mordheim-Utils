"""Construction contract: the Lahmia vampire's own bloodline power.

The canonical record declares Enchanting Beauty for the profile and admits the
Lahmia power only for that bloodline, refusing the Hypnotic Gaze of another one.
This is a compilation contract, so it builds the profile itself.
"""
from __future__ import annotations

import pathlib

import pytest
import yaml

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild

ROOT = pathlib.Path(__file__).resolve().parents[3]

BAND = "sources/knowledge/bands/trollheim/chaos-streets-undead-bloodlines"


def band_profile_with_rule(relative_dir: str, rule_id: str) -> str:
    document = yaml.safe_load((ROOT / relative_dir / "profiles.yaml").read_text(encoding="utf-8"))
    for profile in document["profiles"]:
        if rule_id in (profile.get("rule_ids") or ()):
            return profile["id"]
    raise AssertionError(f"no profile of {relative_dir} carries {rule_id}")


@pytest.mark.phase2_construction
def test_the_lahmia_vampire_reaches_its_own_bloodline_power():
    vampire = band_profile_with_rule(BAND, "lahmia-vampire--enchanting-beauty")
    build = dict(band_id="chaos-streets-undead-bloodlines", profile_id=vampire,
                 collection="trollheim", main_weapon_id="weapon.mace",
                 armour_id="armour.no-armour")
    selected = compile_fighter(FighterBuild(
        "mordheim", special_rule_ids=("band--lahmia-power-seduction",), **build))
    tags = selected.global_effects.tags
    assert "mechanic.lahmia-seduction" in tags
    # Enchanting Beauty is the profile's own rule and needs no selection.
    assert "mechanic.enchanting-beauty" in tags
    unselected = compile_fighter(FighterBuild("mordheim", **build))
    assert "mechanic.lahmia-seduction" not in unselected.global_effects.tags
    # Hypnotic Gaze is a vampiric power of another bloodline, so the Lahmia
    # vampire cannot be given it; its route is the record binding above plus the
    # consumer witness below.
    with pytest.raises(ValueError, match="bloodline"):
        compile_fighter(FighterBuild(
            "mordheim", special_rule_ids=("band--vampire-power-hypnotic-gaze",), **build))
