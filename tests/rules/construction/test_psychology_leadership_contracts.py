"""Construction contracts split from ``tests/engines/modular/test_psychology_leadership.py``.

These tests assert on the canonical compiler itself -- the printed profile
facts and the refusals it produces -- so they keep calling
``compile_fighter`` instead of reading frozen engine inputs.
"""
import pytest
from mordheim_combat.modular.psychology import causes_fear
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options))


def bare(**options):
    """A generic fearless-free fighter with the default Leadership 7."""
    traits = options.pop("trait_overrides", None)
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour",
        trait_overrides=traits or {}, **options))


LAHMIAN_RECIPIENTS = ("beloved", "blood-sister", "blood-slaves", "lackeys")


def lahmian(profile, **options):
    return canonical("khemri-lahmian-brotherhood", profile, "weapon.sword",
                     collection="trollheim", **options)


DECEIVE = ("chaos-streets-undead-bloodlines", "lahmia-vampire", "band--lahmia-power-deceive")


HYPNOTIZE = ("khemri-lahmian-brotherhood", "lahmian-vampire", "band--lahmian-special-skills-hypnotize")


def lahmia_vampire(power):
    band, profile, rule = power
    return canonical(band, profile, "weapon.sword", collection="trollheim", special_rule_ids=(rule,))


@pytest.mark.phase2_construction
def test_ere_we_go_is_shared_by_the_three_green_skin_bands():
    for band, profile, collection, rule in (
        ("black-orcs", "black-orc-boss", "mordheim",
         "band--black-orc-special-skills-ere-we-go"),
        ("orc-mob", "orc-boss", "mordheim", "band--orc-special-skills-ere-we-go"),
        ("chaos-streets-greenskins", "orc-boss", "trollheim",
         "band--orc-special-skills-ere-we-go"),
    ):
        fighter = canonical(band, profile, collection=collection, special_rule_ids=(rule,))
        assert "mechanic.ere-we-go" in fighter.global_effects.tags, band


@pytest.mark.phase2_construction
def test_fear_of_elves_is_a_shared_rule_with_its_own_recipients():
    for band, profile, collection in (
        ("chaos-streets-greenskins", "goblin-warriors", "trollheim"),
        ("lustria-savage-goblins", "savage-goblins", "trollheim"),
    ):
        fighter = canonical(band, profile, collection=collection)
        assert "mechanic.fear-of-elves" in fighter.global_effects.tags, (band, profile)


@pytest.mark.phase2_construction
def test_fear_of_elves_reads_the_models_own_elf_species_fact():
    # The Elf species is the model's own printed fact, never its warband's:
    # `elf_kind` projects `species.elf`, the three printed kinds add the marker
    # Hatred of High/Dark Elves reads, and every one of them frightens both
    # canonical goblin recipients of the shared clause.
    recipients = (canonical("night-goblins-web", "night-goblin-warriors"),
                  canonical("lustria-savage-goblins", "savage-goblins", collection="trollheim"))
    for band, profile, collection, kind_tag in (
        ("wood-elves-of-athel-loren-web", "hunt-master", "mordheim", "species.wood-elf"),
        ("wood-elves-of-athel-loren-web", "glade-guard", "mordheim", "species.wood-elf"),
        ("wood-elves-of-arden-mou", "protector-of-the-hunt", "mordheim", "species.wood-elf"),
        ("lustria-high-elves", "loremaster", "trollheim", "species.high-elf"),
        ("chaos-streets-sons-of-nagarythe", "shadow-warrior", "trollheim", "species.high-elf"),
        ("lothern-sea-patrol-sar", "mist-mage", "mordheim", "species.high-elf"),
        ("lustria-dark-elves", "dark-prince", "trollheim", "species.dark-elf"),
        ("dark-elf-corsairs-mou", "captain", "mordheim", "species.dark-elf"),
        # The Karak Azgal hero is printed as a bare "Elf": it is an Elf whose
        # source names no kind, so it carries the species without a kind marker.
        ("adventurers-kaz", "elf", "mordheim", None),
    ):
        elf = canonical(band, profile, "weapon.sword", collection=collection)
        assert "species.elf" in elf.global_effects.tags, (band, profile, collection)
        if kind_tag is None:
            assert not any(tag in elf.global_effects.tags for tag in
                           ("species.high-elf", "species.dark-elf", "species.wood-elf")), profile
        else:
            assert kind_tag in elf.global_effects.tags, (band, profile, collection)
        for goblin in recipients:
            assert causes_fear(elf, goblin) is True, (band, profile)
    # Negative control: an ordinary model still frightens nobody.
    assert causes_fear(bare(), recipients[0]) is False


@pytest.mark.phase2_construction
def test_fear_of_elves_ignores_an_elf_warbands_non_elf_models():
    # The Ivy Ferret is listed in a Wood Elf warband but its printed Spirit
    # rule makes it a woodland spirit, and the Cold Ones are that Dark Elf
    # warband's animals: warband membership is not a species substitute.
    goblin = canonical("night-goblins-web", "night-goblin-warriors")
    for band, profile, collection in (("wood-elves-of-arden-mou", "ivy-ferret", "mordheim"),
                                      ("lustria-dark-elves", "cold-ones", "trollheim")):
        other = canonical(band, profile, collection=collection)
        assert "species.elf" not in other.global_effects.tags, profile
    # Neither is feared as an Elf: the woodland Spirit prints no Fear at all, and
    # the Cold Ones' Fear is the animal's own printed trait, which the Elves'
    # inherited rule does not have to supply.
    ferret = canonical("wood-elves-of-arden-mou", "ivy-ferret", collection="mordheim")
    assert causes_fear(ferret, goblin) is False
    cold_ones = canonical("lustria-dark-elves", "cold-ones", collection="trollheim")
    assert "mechanic.causes-fear" in cold_ones.global_effects.tags
    assert causes_fear(cold_ones, goblin) is True


@pytest.mark.phase2_construction
def test_accustomed_to_fear_belongs_to_the_four_recipients_only():
    for band, profile, collection in (
        ("khemri-lahmian-brotherhood", "lahmian-vampire", "trollheim"),
        ("khemri-lahmian-brotherhood", "necromancer", "trollheim"),
        ("khemri-lahmian-brotherhood", "skeleton-warriors", "trollheim"),
        ("khemri-lahmian-brotherhood", "black-hounds", "trollheim"),
        # Another band's Skeleton is Undead but no recipient of the clause.
        ("restless-dead", "skeletons", "mordheim"),
    ):
        fighter = canonical(band, profile, collection=collection)
        assert "mechanic.accustomed-to-fear" not in fighter.global_effects.tags, (band, profile)
    # The clause is a filtered exemption, never the unconditional immunity the
    # other Fearless family binds.
    for profile in LAHMIAN_RECIPIENTS:
        assert "mechanic.fear-immunity" not in lahmian(profile).global_effects.tags, profile


@pytest.mark.phase2_construction
def test_the_two_lahmia_powers_are_selectable_by_their_printed_recipient_only():
    # Both powers are selectable band grants, so the shared eligibility layer must
    # accept only the named Lahmia Vampire: a sibling profile of the same band and
    # the other band's Lahmia Vampire are both refused, so no other model can
    # carry either contract into the duel.
    cases = (
        (HYPNOTIZE, "mechanic.lahmian-hypnotize",
         (("khemri-lahmian-brotherhood", "skeleton-warriors"),
          ("khemri-lahmian-brotherhood", "necromancer"),
          ("chaos-streets-undead-bloodlines", "lahmia-vampire"))),
        (DECEIVE, "mechanic.lahmia-deceive",
         (("chaos-streets-undead-bloodlines", "blood-dragon-vampire"),
          ("chaos-streets-undead-bloodlines", "necromancer"),
          ("khemri-lahmian-brotherhood", "lahmian-vampire"))),
    )
    for (band, profile, rule), mechanic, refusals in cases:
        assert mechanic in lahmia_vampire((band, profile, rule)).global_effects.tags
        for other_band, other_profile in refusals:
            try:
                canonical(other_band, other_profile, "weapon.sword", collection="trollheim",
                          special_rule_ids=(rule,))
            except ValueError as error:
                assert "special rule is not available" in str(error), (rule, other_profile)
            else:
                raise AssertionError(f"{rule} was selectable by {other_band}/{other_profile}")
