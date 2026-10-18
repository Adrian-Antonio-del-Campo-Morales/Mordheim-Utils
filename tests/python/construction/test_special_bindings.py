"""Special construction bindings."""
from __future__ import annotations

import pytest

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


AQUATIC_POOL = (
    "band--mutations-blackblood",
    "band--mutations-great-claw",
    "band--mutations-tentacle",
    "band--mutations-prehensile-tail",
    "band--mutations-beak",
    "band--mutations-electrical-touch",
    "band--mutations-mer-creature",
    "band--mutations-suckers",
    "band--mutations-eye-stalks",
)


def _aquatic(*extra, **kwargs):
    return compile_fighter(build(
        "shallows-beasts-mim", "buccaneer",
        main_weapon_id="weapon.mace", **kwargs, special_rule_ids=extra,
    ))


def test_every_aquatic_mutants_pool_member_compiles_its_projected_state():
    # The grant rule of `shallows-beasts-mim / band--aquatic-mutants` lets any
    # Hero select one mutation from the printed pool; each member projects the
    # consequence its own catalogue entry declares. Mer-Creature and Suckers
    # keep their terrain and climbing content outside the duel: Mer-Creature
    # only lowers its land Movement, Suckers compiles without a duel effect.
    blackblood = _aquatic("band--mutations-blackblood")
    great_claw = _aquatic("band--mutations-great-claw")
    tentacle = _aquatic("band--mutations-tentacle")
    tail = _aquatic("band--mutations-prehensile-tail")
    beak = _aquatic("band--mutations-beak")
    electrical = _aquatic("band--mutations-electrical-touch")
    mer_creature = _aquatic("band--mutations-mer-creature")
    suckers = _aquatic("band--mutations-suckers")
    eye_stalks = _aquatic("band--mutations-eye-stalks")
    assert "acid_blood" in blackblood.global_effects.tags
    assert any("rule.great-claw" in attack.tags and attack.strength_bonus == 1
               for attack in great_claw.extra_attacks)
    assert ("rule.tentacle-grapple" in tentacle.global_effects.tags
            and tentacle.global_effects.incoming_attacks_modifier == -1)
    assert any("rule.prehensile-tail" in attack.tags for attack in tail.extra_attacks)
    assert any("rule.strikes-last-bite" in attack.tags for attack in beak.extra_attacks)
    assert "mechanic.electrical-touch" in electrical.global_effects.tags
    assert "species.aquatic" in mer_creature.global_effects.tags
    assert mer_creature.characteristics.movement == 3
    assert sorted(suckers.global_effects.tags) == sorted(_aquatic().global_effects.tags)
    assert "mechanic.causes-fear" in eye_stalks.global_effects.tags


def test_aquatic_mutants_access_is_one_pool_member_per_hero():
    grant = compile_fighter(FighterBuild(
        "mordheim", band_id="shallows-beasts-mim", profile_id="buccaneer",
        main_weapon_id="weapon.mace",
    ))
    # The selected rule is the only mutation access; without it nothing mutates.
    assert not any(tag.startswith("band--") for tag in grant.global_effects.tags)
    for member in AQUATIC_POOL:
        assert _aquatic(member).construction_tags is not None
    with pytest.raises(ValueError, match="at most one Aquatic mutation"):
        _aquatic("band--mutations-blackblood", "band--mutations-beak")


def test_aquatic_mutants_pool_is_closed_and_hero_only():
    # Mutations outside the printed pool (a Possessed Extra Arm or Scorpion
    # Tail) are not selectable, and a non-Hero cannot receive the grant.
    for foreign in ("band--mutations-extra-arm", "band--mutations-scorpion-tail"):
        with pytest.raises(ValueError, match="not available to shallows-beasts-mim"):
            _aquatic(foreign)
    with pytest.raises(ValueError, match="not available to shallows-beasts-mim/wreckers"):
        compile_fighter(FighterBuild(
            "mordheim", band_id="shallows-beasts-mim", profile_id="wreckers",
            main_weapon_id="weapon.mace",
            special_rule_ids=("band--mutations-blackblood",),
        ))


def test_extra_arm_and_great_claw_enforce_their_printed_arm_rules():
    """Extra Arm: 'The mutant may use any single-handed weapon in the extra
    arm...  Alternatively, he may carry a shield or a buckler in the extra arm.
    If a Possessed chooses to do this, he gains an extra attack but still
    cannot carry a weapon.'  Great Claw: 'He may carry no weapons in this arm.'
    """
    shield_arm = compile_fighter(build(
        "cult-of-the-possessed", "mutants", extra_hand_id="defence.shield",
        special_rule_ids=("band--mutations-extra-arm",),
    ))
    possessed = compile_fighter(build(
        "cult-of-the-possessed", "the-possessed", extra_hand_id="defence.shield",
        special_rule_ids=("band--mutations-extra-arm",),
    ))
    # Both alternative loadouts of the extra arm pay the extra attack, and the
    # Possessed keeps his own 'never use weapons' restriction.
    for fighter in (shield_arm, possessed):
        assert any("weapon.natural-attacks" in attack.tags for attack in fighter.extra_attacks)
    with pytest.raises(ValueError, match="one-handed weapon"):
        compile_fighter(build(
            "cult-of-the-possessed", "mutants", extra_hand_id="weapon.halberd",
            special_rule_ids=("band--mutations-extra-arm",),
        ))
    with pytest.raises(ValueError, match="equipment is not available"):
        compile_fighter(build(
            "cult-of-the-possessed", "the-possessed", extra_hand_id="weapon.dagger",
            special_rule_ids=("band--mutations-extra-arm",),
        ))
    # The claw arm carries nothing, so the mutant keeps one weapon at most and
    # never a weapon that occupies both of its arms.
    for illegal in (dict(main_weapon_id="weapon.sword", off_hand_id="weapon.sword"),
                    dict(main_weapon_id="weapon.double-handed-weapon")):
        with pytest.raises(ValueError, match="Great Claw arm may carry no weapon"):
            compile_fighter(build(
                "cult-of-the-possessed", "mutants",
                special_rule_ids=("band--mutations-great-claw",), **illegal,
            ))
    legal = compile_fighter(build(
        "cult-of-the-possessed", "mutants", main_weapon_id="weapon.sword",
        off_hand_id="defence.shield", special_rule_ids=("band--mutations-great-claw",),
    ))
    assert any("rule.great-claw" in attack.tags and attack.strength_bonus == 1
               for attack in legal.extra_attacks)
    # The claw removes one weapon arm, not all arms beyond the original pair.
    # An Extra Arm leaves two weapon-capable arms and a claw that may hold a shield.
    combined = ("band--mutations-great-claw", "band--mutations-extra-arm")
    legal_extra = compile_fighter(build(
        "cult-of-the-possessed", "mutants", main_weapon_id="weapon.sword",
        off_hand_id="weapon.dagger", extra_hand_id="defence.shield", special_rule_ids=combined,
    ))
    assert legal_extra.off_hand_attacks
    with pytest.raises(ValueError, match="Great Claw arm may carry no weapon"):
        compile_fighter(build(
            "cult-of-the-possessed", "mutants", main_weapon_id="weapon.sword",
            off_hand_id="weapon.dagger", extra_hand_id="weapon.mace", special_rule_ids=combined,
        ))
