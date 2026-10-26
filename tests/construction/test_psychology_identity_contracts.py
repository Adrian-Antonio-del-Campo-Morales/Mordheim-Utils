"""Construction contracts for psychology identity, split out of the modular suite.

These two checks assert what the canonical compiler produces (the printed
identity of the Tomb Scorpion in both printings) or refuses (a half-supplied
Bitter Enmity fact), so they belong to construction and own the compiler.
Names, markers, parametrisations and assertions are the ones the modular file
carried before the split; the builders and constants are copied so the module
stays standalone.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root

ROOT = knowledge_root()


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options), ROOT)


# --- Tomb Scorpions: living, and therefore not Undead ----------------------

def test_tomb_scorpions_are_living_and_not_undead_in_both_printings():
    for band, collection in (("tomb-guardians", "mordheim"),
                            ("khemri-tomb-guardians", "trollheim")):
        scorpion = canonical(band, "tomb-scorpions", collection=collection)
        assert "nature.living" in scorpion.global_effects.tags, band
        assert "nature.undead" not in scorpion.global_effects.tags, band
        # "affected by Psychology normally": the identity grants no immunity.
        assert "mechanic.psychology-immunity" not in scorpion.global_effects.tags, band


# --- Vengeful Hatred: the supplied target the injury determined -------------

def injured(kind, target):
    """A Bitter Enmity recipient whose campaign relationship is supplied."""
    return canonical("mercenaries", "warriors", trait_overrides={
        "enmity_kind": kind, "enmity_target": target})


def test_vengeful_hatred_refuses_a_half_supplied_or_empty_target():
    with pytest.raises(ValueError, match="target kind and its concrete identity together"):
        canonical("mercenaries", "warriors", trait_overrides={"enmity_kind": "warband"})
    with pytest.raises(ValueError, match="unknown Bitter Enmity target kind"):
        injured("tribe", "undead")
    with pytest.raises(ValueError, match="concrete identity the injury determined"):
        injured("individual", "  ")
    with pytest.raises(ValueError, match="one supplied identity key"):
        injured("warband", "roster-a roster-b")
    with pytest.raises(ValueError, match="non-empty supplied identity"):
        canonical("mercenaries", "warriors", trait_overrides={"instance_id": "  "})
