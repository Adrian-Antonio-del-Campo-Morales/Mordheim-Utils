"""Preparation access: one permission for the picker and the compiled fighter.

A preparation is a Trading Post consumable, not a line of a band's equipment
list, so an empty weapon list never proves it is forbidden. What removes it is
the bearer's own printed clause (`equipment`/items), a drug prohibition of the
band, or the item's own market recipient. Drug immunity suppresses the effect
and never removes the choice.

The offer and the direct compilation are checked as one pair: every case asserts
what the picker shows and what ``compile_fighter`` accepts, so a future change
cannot fix one route and leave the other disagreeing.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands

PREPARATIONS = (
    "preparation.crimson-shade",
    "preparation.mandrake-root",
    "preparation.mad-cap-mushrooms",
    "preparation.head-splitter-mushrooms",
    "preparation.tears-of-shallaya",
)
DRUGS = {
    "preparation.crimson-shade",
    "preparation.mandrake-root",
    "preparation.mad-cap-mushrooms",
    "preparation.head-splitter-mushrooms",
}
MANDRAKE = "preparation.mandrake-root"
TEARS = "preparation.tears-of-shallaya"
# The Shadow Warrior list prints Elven Wine, so the same non-drug class the
# prohibition leaves legal keeps the wine beside the Tears of Shallaya.
WINE = "preparation.elven-wine"

PACKAGES = {
    (collection, str(package.band["id"])): package
    for collection in ("mordheim", "trollheim")
    for package in load_bands(collection)
}


def row(collection: str, band: str, profile_id: str) -> dict:
    return next(profile for profile in PACKAGES[(collection, band)].profiles
                if str(profile["id"]) == profile_id)


def build(collection: str, band: str, profile_id: str, preparation: str | None = None) -> FighterBuild:
    return FighterBuild("mordheim", collection=collection, band_id=band, profile_id=profile_id,
                        **({"preparation_ids": (preparation,)} if preparation else {}))


def options(collection: str, band: str, profile_id: str) -> set[str]:
    return set(desktop_call("preparationOptions", build(collection, band, profile_id),
                            package=PACKAGES[(collection, band)],
                            profile=row(collection, band, profile_id)))


@pytest.mark.eligibility
@pytest.mark.parametrize("band,profile_id", [
    ("chaos-streets-undead-bloodlines", "ghoul"),
    ("chaos-streets-undead-bloodlines", "necromancer"),
    # The printed clause forbids weapons and armour only: a consumable is not
    # covered by it, and the empty equipment list is not a ban.
    ("lustria-amazons", "great-cats"),
])
def test_the_preparation_offer_and_the_compiled_fighter_agree(band, profile_id):
    offered = options("trollheim", band, profile_id)
    assert MANDRAKE in offered
    for preparation in PREPARATIONS:
        accepted = True
        try:
            compile_fighter(build("trollheim", band, profile_id, preparation))
        except ValueError:
            accepted = False
        assert accepted is (preparation in offered), preparation


@pytest.mark.eligibility
def test_a_printed_no_equipment_clause_removes_the_offer_and_the_grant():
    """The Strigoi may not use items at all: neither route admits a consumable."""
    assert options("trollheim", "chaos-streets-undead-bloodlines", "strigoi-vampire") == set()
    with pytest.raises(ValueError, match="equipment"):
        compile_fighter(build("trollheim", "chaos-streets-undead-bloodlines",
                              "strigoi-vampire", MANDRAKE))


@pytest.mark.eligibility
def test_an_any_equipment_vow_removes_the_offer_and_the_grant():
    """'may never have any equipment' admits only its printed exceptions."""
    band = "nipponese-expedition-web"
    assert options("mordheim", band, "vim-to-mage") == set()
    with pytest.raises(ValueError, match="may not be carried"):
        compile_fighter(build("mordheim", band, "vim-to-mage", MANDRAKE))


@pytest.mark.eligibility
@pytest.mark.parametrize("profile_id", ["shadow-master", "shadow-warrior"])
def test_a_drug_prohibition_removes_only_the_drug_class(profile_id):
    """'May not use poisons or drugs' keeps the non-drug preparation legal."""
    band = "chaos-streets-sons-of-nagarythe"
    assert options("trollheim", band, profile_id) == {TEARS, WINE}
    with pytest.raises(ValueError, match="drugs are forbidden"):
        compile_fighter(build("trollheim", band, profile_id, MANDRAKE))
    survivor = compile_fighter(build("trollheim", band, profile_id, TEARS))
    assert TEARS in survivor.global_effects.tags


# Primary: immunity suppresses the carried effect. The offer staying open is
# the secondary guarantee that suppression is not a prohibition.
@pytest.mark.rule_behavior
def test_drug_immunity_is_not_a_prohibition():
    """A Construct still carries the root; only its effect is suppressed."""
    unit = compile_fighter(build("mordheim", "clockworkers-sc", "clockwork-fiend", MANDRAKE))
    assert options("mordheim", "clockworkers-sc", "clockwork-fiend") >= {MANDRAKE}
    assert MANDRAKE not in unit.global_effects.tags
    base = compile_fighter(build("mordheim", "clockworkers-sc", "clockwork-fiend"))
    assert unit.characteristics.toughness == base.characteristics.toughness
