"""T13-F011/T13-F012: printed profile save thresholds on the canonical compiler.

Sources (``sources/knowledge``):

1. ``bands/mordheim/lords-of-the-marsh-mim/special-rules.yaml`` /
   ``band--scaly-skin``: *"Fimir have a 6+ armour save that cannot be modified
   beyond 6 by Strength; a 'no save' result on the Critical Hit Charts negates
   it. Light armour adds +1. Fimir Warriors have a 5+ armour save."*  The
   band-wide clause and the species clause are one printed sentence: the band
   save stays 6+ with a 6+ Strength floor, while Fimir Warriors print 5+.
2. ``bands/mordheim/underworld-alliance-mim/special-rules.yaml`` /
   ``boglars--regeneration``: *"Whenever an enemy successfully inflicts a
   wound on a Boglar, roll a D6; on a result of 5 or more the wound is ignored
   and the Boglar is unhurt. Boglars may not regenerate wounds caused by fire
   or fire-based magic."*

The expectations below are read from those clauses, never from the compiled
output.  Compilation uses the canonical ``FighterBuild``/``compile_fighter``
path; no trait is substituted by hand.  Combat evidence for the same clauses
lives in ``tests/python/combat/modular/test_t13_profile_save_thresholds.py``.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import effect_index
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands, read_yaml, runtime_bindings

ROOT = Path(__file__).resolve().parents[3]
KB = ROOT / "sources" / "knowledge"
LORDS_OF_THE_MARSH = KB / "bands" / "mordheim" / "lords-of-the-marsh-mim" / "special-rules.yaml"
UNDERWORLD_ALLIANCE = KB / "bands" / "mordheim" / "underworld-alliance-mim" / "special-rules.yaml"


def compile_band(band_id: str, profile_id: str, collection: str = "mordheim", **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id, collection=collection, **options
    ))


def rule(path: Path, rule_id: str) -> dict:
    document = read_yaml(path)
    return next(row for row in document["rules"] if row["id"] == rule_id)


def band_profiles(band_id: str, collection: str = "mordheim") -> set[str]:
    package = next(band for band in load_bands(collection, KB) if band.band["id"] == band_id)
    return {str(profile["id"]) for profile in package.profiles}


# ---------------------------------------------------------------------------
# source publication
# ---------------------------------------------------------------------------
def test_scaly_skin_rule_publishes_the_band_cap_and_the_fimir_warriors_clause():
    text = " ".join(str(rule(LORDS_OF_THE_MARSH, "band--scaly-skin")["effect"]).split())
    assert "Fimir have a 6+ armour save that cannot be modified beyond 6 by Strength" in text
    assert "a 'no save' result on the Critical Hit Charts negates it" in text
    assert "Light armour adds +1" in text
    assert "Fimir Warriors have a 5+ armour save" in text
    assert rule(LORDS_OF_THE_MARSH, "band--scaly-skin")["applies_to"]["band"] is True


def test_boglar_rule_publishes_the_five_or_more_and_the_fire_prohibition():
    text = " ".join(str(rule(UNDERWORLD_ALLIANCE, "boglars--regeneration")["effect"]).split())
    assert "on a result of 5 or more the wound is ignored" in text
    assert "may not regenerate wounds caused by fire or fire-based magic" in text
    assert rule(UNDERWORLD_ALLIANCE, "boglars--regeneration")["applies_to"]["profile_ids"] == ["boglars"]


def test_fimir_override_names_only_real_fimir_warriors_recipients():
    binding = runtime_bindings(rule(LORDS_OF_THE_MARSH, "band--scaly-skin"), "compiler")[0]
    assert binding["id"] == "compiler.lizardmen-scaly-skin"
    parameters = binding.get("parameters") or {}
    assert parameters.get("profile_ids") == ["fimir-warriors"]
    assert parameters.get("value") == 5
    assert set(parameters["profile_ids"]) <= band_profiles("lords-of-the-marsh-mim")
    # Young Nobles keep the band-wide 6+; they are not a recipient of the override.
    assert "young-nobles" not in parameters["profile_ids"]


def test_boglar_binding_points_at_the_printed_five_plus_mechanic():
    effect = rule(UNDERWORLD_ALLIANCE, "boglars--regeneration")["runtime"]["effects"][0]
    assert effect["binding"] == {"kind": "mechanic", "id": "skill.regeneration-5-plus"}


# ---------------------------------------------------------------------------
# Fimir Warriors: printed 5+ under the band-wide 6+ floor
# ---------------------------------------------------------------------------
def test_fimir_warriors_compile_the_printed_five_plus():
    compiled = compile_band("lords-of-the-marsh-mim", "fimir-warriors")
    assert compiled.natural_armour_save == 5
    assert "compiler.lizardmen-scaly-skin" in compiled.construction_tags


def test_fimir_warriors_keep_the_band_strength_floor_of_six():
    compiled = compile_band("lords-of-the-marsh-mim", "fimir-warriors")
    # "cannot be modified beyond 6 by Strength": the compiled floor stays the
    # band-wide 6+, not the 5+ species value.
    assert compiled.natural_armour_worst_save == 6


def test_fimir_warriors_do_not_apply_the_band_and_species_values_twice():
    compiled = compile_band("lords-of-the-marsh-mim", "fimir-warriors")
    # 5 (species) + 6 (band) or 4 (Kroxigor-style) would mean a double contract.
    assert compiled.natural_armour_save not in {10, 11, 4, 6}


def test_young_nobles_keep_the_band_six_plus():
    compiled = compile_band("lords-of-the-marsh-mim", "young-nobles")
    assert compiled.natural_armour_save == 6
    assert compiled.natural_armour_worst_save == 6
    assert "compiler.lizardmen-scaly-skin" in compiled.construction_tags


def test_fimir_warriors_accept_light_armour_without_changing_the_natural_value():
    # "Light armour adds +1" is a composition clause; the natural contribution
    # itself stays 5+.
    compiled = compile_band("lords-of-the-marsh-mim", "fimir-warriors", armour_id="armour.light-armour")
    assert compiled.natural_armour_save == 5
    assert compiled.natural_armour_worst_save == 6


REMAINING_BAND_PROFILES = (
    # The band clause is band-wide, so the other Fimir profiles keep the 6+.
    ("mordheim", "lords-of-the-marsh-mim", "shearls", 6),
    ("mordheim", "lords-of-the-marsh-mim", "daemon-fimm", 6),
)


@pytest.mark.parametrize(("collection", "band_id", "profile_id", "expected"), REMAINING_BAND_PROFILES)
def test_band_wide_six_plus_stays_for_other_fimir_profiles(collection, band_id, profile_id, expected):
    assert compile_band(band_id, profile_id, collection).natural_armour_save == expected


# ---------------------------------------------------------------------------
# unrelated Lizardmen species values stay intact
# ---------------------------------------------------------------------------
LIZARDMEN_SPECIES_SAVES = (
    ("mordheim", "lizardmen", "skink-priest", 6),
    ("mordheim", "lizardmen", "saurus-braves", 5),
    ("mordheim", "lizardmen", "saurus-totem-warrior", 5),
    ("mordheim", "lizardmen", "kroxigor", 4),
    ("mordheim", "lizardmen-lus", "skink-braves", 6),
    ("mordheim", "lizardmen-lus", "saurus-totem-warriors", 5),
    ("mordheim", "lizardmen-lus", "saurus-braves", 5),
    ("mordheim", "lizardmen-lus", "kroxigor", 4),
    ("trollheim", "lustria-lizardmen", "skink-priest", 6),
    ("trollheim", "lustria-lizardmen", "saurus-braves", 5),
    ("trollheim", "lustria-lizardmen", "kroxigor", 4),
)


@pytest.mark.parametrize(("collection", "band_id", "profile_id", "expected"), LIZARDMEN_SPECIES_SAVES)
def test_lizardmen_scaly_skin_species_values_are_untouched(collection, band_id, profile_id, expected):
    compiled = compile_band(band_id, profile_id, collection)
    assert compiled.natural_armour_save == expected
    assert compiled.natural_armour_worst_save == 6
    assert "compiler.lizardmen-scaly-skin" in compiled.construction_tags


def test_a_profile_without_the_contract_keeps_no_natural_save():
    compiled = compile_band("underworld-alliance-mim", "goblin-bully")
    assert compiled.natural_armour_save == 7
    assert "compiler.lizardmen-scaly-skin" not in compiled.construction_tags


# ---------------------------------------------------------------------------
# Boglars: printed 5+ with the fire prohibition; Warpstone Troll keeps 4+
# ---------------------------------------------------------------------------
def test_boglars_compile_the_printed_five_plus_with_the_fire_prohibition():
    compiled = compile_band("underworld-alliance-mim", "boglars")
    assert compiled.global_effects.regeneration_save == 5
    assert compiled.global_effects.regeneration_blocked_by_fire is True
    assert "skill.regeneration-5-plus" in compiled.global_effects.tags


def test_boglars_do_not_also_keep_the_generic_four_plus_contribution():
    # The composition keeps the best save: a surviving 4+ contribution would
    # lower the compiled value back to 4.
    compiled = compile_band("underworld-alliance-mim", "boglars")
    assert compiled.global_effects.regeneration_save == 5
    assert "skill.regeneration" not in compiled.global_effects.tags


def test_warpstone_troll_keeps_the_printed_four_plus():
    compiled = compile_band("underworld-alliance-mim", "warpstone-troll")
    assert compiled.global_effects.regeneration_save == 4
    assert compiled.global_effects.regeneration_blocked_by_fire is True
    assert "skill.regeneration" in compiled.global_effects.tags
    binding = runtime_bindings(rule(UNDERWORLD_ALLIANCE, "warpstone-troll--regeneration"), "mechanic")[0]
    assert binding["id"] == "skill.regeneration"


@pytest.mark.parametrize("profile_id", ("goblin-bully", "sewer-squigs"))
def test_boglar_regeneration_stays_absent_from_valid_controls(profile_id):
    compiled = compile_band("underworld-alliance-mim", profile_id)
    assert compiled.global_effects.regeneration_save == 7
    assert compiled.global_effects.regeneration_blocked_by_fire is False


# ---------------------------------------------------------------------------
# shared effects, recipients and cross-compilation contamination
# ---------------------------------------------------------------------------
def test_shared_regeneration_mechanic_effects_are_not_altered():
    effects = effect_index("mordheim")
    assert effects["skill.regeneration"].effect.regeneration_save == 4
    assert effects["skill.regeneration"].effect.regeneration_blocked_by_fire is True
    assert effects["skill.regeneration-5-plus"].effect.regeneration_save == 5
    assert effects["skill.regeneration-5-plus"].effect.regeneration_blocked_by_fire is True


def test_compiling_boglars_does_not_mutate_the_cached_mechanic_effects():
    before = {name: effect.effect for name, effect in effect_index("mordheim").items()}
    compile_band("underworld-alliance-mim", "boglars")
    after = {name: effect.effect for name, effect in effect_index("mordheim").items()}
    assert after == before


def test_controls_are_stable_before_and_after_boglars_in_one_process():
    troll_before = compile_band("underworld-alliance-mim", "warpstone-troll")
    boglar = compile_band("underworld-alliance-mim", "boglars")
    young_nobles_before = compile_band("lords-of-the-marsh-mim", "young-nobles")
    fimir = compile_band("lords-of-the-marsh-mim", "fimir-warriors")
    troll_after = compile_band("underworld-alliance-mim", "warpstone-troll")
    young_nobles_after = compile_band("lords-of-the-marsh-mim", "young-nobles")
    assert troll_after == troll_before
    assert young_nobles_after == young_nobles_before
    assert troll_before.global_effects.regeneration_save == 4
    assert boglar.global_effects.regeneration_save == 5
    assert fimir.natural_armour_save == 5


def test_reverse_order_recompilation_is_identical():
    order = (
        ("underworld-alliance-mim", "warpstone-troll"),
        ("lords-of-the-marsh-mim", "fimir-warriors"),
        ("underworld-alliance-mim", "boglars"),
        ("lords-of-the-marsh-mim", "young-nobles"),
    )
    first = {pair: compile_band(*pair) for pair in order}
    second = {pair: compile_band(*pair) for pair in reversed(order)}
    assert first == second
