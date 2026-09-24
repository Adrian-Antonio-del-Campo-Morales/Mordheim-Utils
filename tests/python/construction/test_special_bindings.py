"""Special construction bindings."""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def build(band_id, profile_id, *, collection="mordheim", **kwargs):
    return FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        collection=collection, **kwargs,
    )


def test_automatic_profile_handlers_compile_trample_frantic_and_bear_hug():
    centigor = compile_fighter(build("beastmen-raiders", "centigors"))
    fanatic = compile_fighter(build("night-goblins-mic", "fanatics"))
    bear = compile_fighter(build("kislevites", "trained-bear"))
    assert any("rule.trample" in attack.tags for attack in centigor.extra_attacks)
    assert fanatic.global_effects.priority == 10
    assert bear.global_effects.bear_hug


def test_mutant_grants_and_mutation_handlers_have_distinct_observables():
    beastman = compile_fighter(build(
        "beastmen-raiders", "beastmen-chieftain",
        special_rule_ids=(
            "band--beastmen-special-skills-mutant", "band--mutations-tentacle",
        ),
    ))
    marauder = compile_fighter(build(
        "marauders-of-chaos", "marauder-chieftain",
        special_rule_ids=(
            "band--marauder-special-skills-mutant", "band--mutations-tentacle",
        ),
    ))
    claw = compile_fighter(build(
        "cult-of-the-possessed", "mutants",
        special_rule_ids=("band--mutations-great-claw",),
    ))
    extra_arm = compile_fighter(build(
        "cult-of-the-possessed", "mutants", extra_hand_id="weapon.dagger",
        special_rule_ids=("band--mutations-extra-arm",),
    ))
    assert beastman.global_effects.incoming_attacks_modifier == -1
    assert marauder.global_effects.incoming_attacks_modifier == -1
    assert any(attack.strength_bonus == 1 for attack in claw.extra_attacks)
    assert any("weapon.dagger" in attack.tags for attack in extra_arm.extra_attacks)


def test_horn_shield_and_tail_handlers_compile_independent_attacks():
    horned = compile_fighter(build(
        "beastmen-raiders", "beastmen-chieftain",
        special_rule_ids=("band--beastmen-special-skills-horned-one",),
    ))
    shield = compile_fighter(build(
        "bretonnian-chapel-guard", "questing-knight", off_hand_id="defence.shield",
        special_rule_ids=("band--shield-bash",),
    ))
    tail = compile_fighter(build(
        "skaven-clan-eshin", "night-runners", extra_hand_id="weapon.dagger",
        special_rule_ids=("band--skaven-special-skills-tail-fighting",),
    ))
    assert any("rule.horned-one" in attack.tags for attack in horned.extra_attacks)
    assert any("weapon.mace" in attack.tags and attack.strength_bonus == -1
               for attack in shield.extra_attacks)
    assert any("weapon.dagger" in attack.tags for attack in tail.extra_attacks)


def test_all_three_nurgle_blessing_handlers_change_compiled_state():
    base = compile_fighter(build(
        "carnival-of-chaos", "tainted-ones",
        special_rule_ids=("band--blessings-of-nurgle-nurgles-rot",),
    ))
    bloated = compile_fighter(build(
        "carnival-of-chaos", "tainted-ones",
        special_rule_ids=("band--blessings-of-nurgle-bloated-foulness",),
    ))
    marked = compile_fighter(build(
        "carnival-of-chaos", "tainted-ones",
        special_rule_ids=("band--blessings-of-nurgle-mark-of-nurgle",),
    ))
    assert base.global_effects.poison_immunity
    assert (bloated.characteristics.toughness, bloated.characteristics.wounds) == (4, 2)
    assert marked.characteristics.wounds == 2 and marked.global_effects.poison_immunity


def test_remaining_selected_handlers_project_their_exact_combat_modifier():
    berserk = compile_fighter(build(
        "norse-explorers-btb", "jarl",
        special_rule_ids=("band--norse-special-skills-berserk-charge",),
    ))
    strigoi = compile_fighter(build(
        "chaos-streets-undead-bloodlines", "strigoi-vampire", collection="trollheim",
        special_rule_ids=("band--strigoi-power-monstrosity",),
    ))
    multiple = compile_fighter(build(
        "khemri-necromancers", "necromantic-abomination", collection="trollheim",
        special_rule_ids=("band--necromantic-modification-multiple-limbs",),
    ))
    putrid = compile_fighter(build(
        "khemri-necromancers", "necromantic-abomination", collection="trollheim",
        special_rule_ids=("band--necromantic-modification-putrid-stench",),
    ))
    venom = compile_fighter(build(
        "lustria-lizardmen", "skink-priest", collection="trollheim",
        special_rule_ids=("band--sacred-mark-venom-glands",),
    ))
    # Berserk Charge is weapon-dependent, not a universal charge reroll.
    assert "rule.berserk-charge" in berserk.global_effects.tags
    assert not berserk.global_effects.charge_reroll_hits
    assert strigoi.characteristics.wounds == 3
    assert multiple.global_effects.attacks_bonus == 1
    assert putrid.global_effects.incoming_hit_modifier == -1
    assert "rule.putrid-stench" in putrid.global_effects.tags
    assert "rule.venom-glands" in venom.main_weapon.tags
    assert venom.main_weapon.target_armour_bonus == 1
    assert venom.main_weapon.injury_modifier == 1
