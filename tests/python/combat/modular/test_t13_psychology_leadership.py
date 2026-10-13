"""T13 M4: individual Fear qualifiers and the supplied Leader radius variants.

Each contract is exercised three ways on the canonical compiler and the real
modular pipeline: activation, a negative control that must not fire, and the
printed semantic exception.  'Ere We Go! and Fear of Elves are read through
``psychology``; the 12"/4" Leader radii through ``leadership`` with a supplied
``DuelContext``.  Strict tapes make "no die was requested" observable.
"""
from __future__ import annotations

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear
from mordheim_combat.modular.psychology import resolve_fear
from mordheim_combat.modular.rounds import apply_opponent_leadership
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild, LocalParticipant

ERE_WE_GO = "band--black-orc-special-skills-ere-we-go"


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim", **options):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon, **options))


def bare(**options):
    """A generic fearless-free fighter with the default Leadership 7."""
    traits = options.pop("trait_overrides", None)
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour",
        trait_overrides=traits or {}, **options))


def fear_state(first, second, charging, rolls):
    dice = StrictDice([{"key": key, "value": value} for key, value in rolls])
    state = initialize_duel(first, second, StrictDice([]), context=DuelContext(
        charging=(charging,), active_participant=charging))
    result = resolve_fear(first, second, state, dice, StrictDecisions([]))
    dice.finish()
    return result


# --- 'Ere We Go! -----------------------------------------------------------

def test_ere_we_go_grants_its_bearer_and_nothing_else():
    boss = canonical("black-orcs", "black-orc-boss", special_rule_ids=(ERE_WE_GO,))
    assert "mechanic.ere-we-go" in boss.global_effects.tags
    unselected = canonical("black-orcs", "black-orc-boss")
    assert "mechanic.ere-we-go" not in unselected.global_effects.tags


def test_ere_we_go_waives_only_the_bearers_own_charging_fear_test():
    fearer = bare(trait_overrides={"causes_fear": True})
    assert causes_fear(fearer, canonical("black-orcs", "black-orc-boss"))
    boss = canonical("black-orcs", "black-orc-boss", special_rule_ids=(ERE_WE_GO,))
    # Activation: the charging bearer consumes no Fear dice at all.
    engaged = fear_state(boss, fearer, "first", [])
    assert engaged.engaged and not engaged.failed_charges
    # Negative control: the same charge without the rule needs the two dice and
    # a failure cancels contact.
    plain = canonical("black-orcs", "black-orc-boss")
    failed = fear_state(plain, fearer, "first", [
        ("round.0.first.fear.charge.0", 6), ("round.0.first.fear.charge.1", 6)])
    assert not failed.engaged and failed.failed_charges == frozenset({"first"})
    # Semantic exception: the waiver is charge-only; being charged still tests.
    charged = fear_state(boss, fearer, "second", [
        ("round.0.first.fear.charged.0", 6), ("round.0.first.fear.charged.1", 6)])
    assert charged.first.fear_hit_sixes


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


# --- Fear of Elves ---------------------------------------------------------

def test_fear_of_elves_is_a_recipient_qualified_directional_fear():
    elf = canonical("high-elves-lus", "loremaster", "weapon.sword")
    goblin = canonical("night-goblins-web", "night-goblin-warriors")
    assert causes_fear(elf, goblin) is True
    # The Elf does not fear the Fear-bearer; the clause is one-directional.
    assert causes_fear(goblin, elf) is False
    # Negative control: an ordinary opponent causes no Fear in the goblin.
    assert causes_fear(bare(), goblin) is False


def test_fear_of_elves_keeps_the_printed_band_and_fanatic_exemptions():
    elf = canonical("high-elves-lus", "loremaster", "weapon.sword")
    goblin = canonical("night-goblins-web", "night-goblin-warriors")
    charged = fear_state(elf, goblin, "first", [
        ("round.0.second.fear.charged.0", 6), ("round.0.second.fear.charged.1", 6)])
    assert charged.second.fear_hit_sixes
    for profile in ("night-goblin-fanatics", "troll", "cave-squigs"):
        exempt = canonical("night-goblins-web", profile)
        assert "mechanic.fear-of-elves" not in exempt.global_effects.tags, profile
        assert causes_fear(elf, exempt) is False, profile
    assert fear_state(elf, canonical("night-goblins-web", "night-goblin-fanatics"),
                      "first", []).engaged


def test_fear_of_elves_is_a_shared_rule_with_its_own_recipients():
    for band, profile, collection in (
        ("chaos-streets-greenskins", "goblin-warriors", "trollheim"),
        ("lustria-savage-goblins", "savage-goblins", "trollheim"),
    ):
        fighter = canonical(band, profile, collection=collection)
        assert "mechanic.fear-of-elves" in fighter.global_effects.tags, (band, profile)


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


# --- Supplied Leader radius variants --------------------------------------

def leader_pass(recipient, provider, participant_id, distance, faces, decision=None):
    context = DuelContext(charging=("first",), active_participant="first",
        nearby=(LocalParticipant(participant_id, "first", provider),),
        distances=(("first", participant_id, distance),))
    state = initialize_duel(recipient, bare(), StrictDice([]), context=context)
    rolls = [{"key": f"probe.{index}", "value": value} for index, value in enumerate(faces)]
    choices = ([{"key": f"probe.leader.{participant_id}", "value": decision}]
               if decision is not None else [])
    dice, decisions = StrictDice(rolls), StrictDecisions(choices)
    passed = resolve_local_leadership(recipient, state, dice, decisions, "probe", first=True)
    dice.finish()
    decisions.finish()
    return passed


def test_battle_tongue_widens_the_reikland_captains_supplied_radius():
    leader = canonical("mercenaries", "mercenary-captain", "weapon.sword")
    warrior = canonical("mercenaries", "warriors")
    assert leader.characteristics.leadership == 8 and warrior.characteristics.leadership == 7
    # Activation: a roll of 8 passes only on the borrowed 8, and the twelve-inch
    # radius still offers the leader at 12".
    assert leader_pass(warrior, leader, "captain", 12, (3, 5), True) is True
    # The canonical six-inch default is untouched.
    assert leader_pass(warrior, leader, "captain", 6, (3, 5), True) is True
    # Negative control: beyond twelve inches the leader is never offered, so the
    # unconsumed decision proves the range gate and the roll of 8 fails at 7.
    assert leader_pass(warrior, leader, "captain", 13, (3, 5)) is False
    # Semantic exception: only the printed leader profile is a provider.
    assert leader_pass(warrior, warrior, "other", 8, (3, 5)) is False


def test_only_the_named_leaders_carry_the_extended_radius():
    assert "mechanic.leader-twelve" in canonical(
        "gunnery-school-of-nuln", "senior-gunnery-officer", "weapon.sword").global_effects.tags
    assert "mechanic.leader-twelve" in canonical(
        "norse-explorers-btb", "jarl", "weapon.sword",
        special_rule_ids=("band--norse-special-skills-battle-tongue",)).global_effects.tags
    # Untaught profiles and the rest of the warband keep the ordinary radius.
    assert "mechanic.leader-twelve" not in canonical(
        "mercenaries", "warriors").global_effects.tags
    assert "mechanic.leader-twelve" not in canonical(
        "norse-explorers-btb", "bondsmen").global_effects.tags


def supplied_leadership(recipient, providers, faces, decisions=None):
    """One Leadership test with the supplied same-side providers.

    ``providers`` is a tuple of ``(participant_id, fighter, condition, inches)``.
    """
    context = DuelContext(charging=("first",), active_participant="first",
        nearby=tuple(LocalParticipant(pid, "first", fighter, condition)
                     for pid, fighter, condition, _ in providers),
        distances=tuple(("first", pid, inches) for pid, _, _, inches in providers))
    state = initialize_duel(recipient, bare(), StrictDice([]), context=context)
    rolls = [{"key": f"probe.{index}", "value": value} for index, value in enumerate(faces)]
    dice, policy = StrictDice(rolls), StrictDecisions(decisions or [])
    passed = resolve_local_leadership(recipient, state, dice, policy, "probe", first=True)
    dice.finish()
    policy.finish()
    return passed


def test_second_in_command_yields_to_a_usable_witch_doctor():
    boss = canonical("lustria-savage-goblins", "big-boss", "weapon.sword", collection="trollheim")
    doctor = canonical("lustria-savage-goblins", "witch-doctor", "weapon.sword", collection="trollheim")
    goblin = canonical("lustria-savage-goblins", "savage-goblins", collection="trollheim")
    assert "mechanic.leader-fallback" in boss.global_effects.tags
    assert "mechanic.leader-fallback" not in doctor.global_effects.tags
    assert "mechanic.leader-six" in doctor.global_effects.tags
    assert (boss.characteristics.leadership, doctor.characteristics.leadership,
            goblin.characteristics.leadership) == (7, 6, 5)
    seven = (4, 3)
    # Activation: a standing Witch Doctor within six inches lends his 6, so the
    # seven the Big Boss would give is withheld and the roll of seven fails.
    assert supplied_leadership(goblin, (("doctor", doctor, "standing", 6),
                                        ("boss", boss, "standing", 4)), seven,
                               [{"key": "probe.leader.doctor", "value": True}]) is False
    # Not usable, knocked down: the printed fallback applies and the borrowed 7
    # passes the same roll.
    assert supplied_leadership(goblin, (("doctor", doctor, "knocked-down", 6),
                                        ("boss", boss, "standing", 4)), seven,
                               [{"key": "probe.leader.boss", "value": True}]) is True
    # Not usable, beyond his own six-inch radius: the fallback applies again.
    assert supplied_leadership(goblin, (("doctor", doctor, "standing", 7),
                                        ("boss", boss, "standing", 4)), seven,
                               [{"key": "probe.leader.boss", "value": True}]) is True
    # Absent: no supplied Witch Doctor at all leaves the fallback in place.
    assert supplied_leadership(goblin, (("boss", boss, "standing", 4),), seven,
                               [{"key": "probe.leader.boss", "value": True}]) is True
    # Negative control: the fallback never suppresses itself, so a lone Big Boss
    # beyond four inches is still no provider (no decision is ever requested).
    assert supplied_leadership(goblin, (("boss", boss, "standing", 5),), seven) is False


def test_second_in_command_grants_only_the_four_inch_big_boss_radius():
    boss = canonical("lustria-savage-goblins", "big-boss", "weapon.sword", collection="trollheim")
    goblin = canonical("lustria-savage-goblins", "savage-goblins", collection="trollheim")
    assert "mechanic.leader-four" in boss.global_effects.tags
    assert boss.characteristics.leadership == 7 and goblin.characteristics.leadership == 5
    # Activation: a roll of 6 passes on the borrowed 7 at four inches.
    assert leader_pass(goblin, boss, "boss", 4, (3, 3), True) is True
    # Negative control: at five inches the shorter radius offers nothing.
    assert leader_pass(goblin, boss, "boss", 5, (3, 3)) is False
    # Semantic exception: the ordinary six-inch Leader of the Witch Doctor is a
    # different profile, so a plain Savage Goblin is never itself a provider.
    assert leader_pass(goblin, goblin, "peer", 4, (3, 3)) is False


# --- M4: Accustomed to Fear and the Lahmia powers --------------------------

LAHMIAN_RECIPIENTS = ("beloved", "blood-sister", "blood-slaves", "lackeys")


def lahmian(profile, **options):
    return canonical("khemri-lahmian-brotherhood", profile, "weapon.sword",
                     collection="trollheim", **options)


def test_accustomed_to_fear_exempts_only_the_three_printed_undead_kinds():
    # The exemption names Vampires, Skeletons and Spirits -- the fear-causing
    # model's own facts, not "Undead" as a whole.
    # Every fear-causer below really causes Fear, so the exemption -- not a
    # missing trigger -- is what removes the test.
    exempt = {
        "vampire": (lahmian("lahmian-vampire"), "species.vampire"),
        "skeleton": (canonical("restless-dead", "skeletons"), "undead-kind.skeleton"),
        "spirit": (canonical("ghost-pirates-sar", "screaming-ghosts"), "undead-kind.spirit"),
    }
    still_feared = {
        # An Undead warband's animals and a Wight both cause Fear without being
        # any of the three named kinds, so "Undead" as a whole is not exempt.
        "dire-wolves": canonical("undead", "dire-wolves"),
        "wight": canonical("necrarchs-mou", "wight"),
        "ordinary": bare(trait_overrides={"causes_fear": True}),
    }
    for profile in LAHMIAN_RECIPIENTS:
        recipient = lahmian(profile)
        assert "mechanic.accustomed-to-fear" in recipient.global_effects.tags, profile
        for name, (enemy, tag) in exempt.items():
            assert tag in enemy.global_effects.tags, (name, tag)
            assert causes_fear(enemy, recipient) is True, (profile, name)
            # Activation: the charged recipient consumes no Fear die at all, so
            # the strict empty tape proves no test was requested.
            exempt_state = fear_state(recipient, enemy, "second", [])
            assert exempt_state.engaged and not exempt_state.failed_charges, (profile, name)
            assert exempt_state.first.fear_hit_sixes is False, (profile, name)
        for name, enemy in still_feared.items():
            # Negative control: every other fear-causer still forces the test,
            # and a failed one leaves the printed sixes restriction.
            assert causes_fear(enemy, recipient) is True, (profile, name)
            feared = fear_state(recipient, enemy, "second", [
                ("round.0.first.fear.charged.0", 6), ("round.0.first.fear.charged.1", 6)])
            assert feared.first.fear_hit_sixes is True, (profile, name)


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


# --- M4: the two Lahmia powers at the start of the combat phase ------------

DECEIVE = ("chaos-streets-undead-bloodlines", "lahmia-vampire", "band--lahmia-power-deceive")
HYPNOTIZE = ("khemri-lahmian-brotherhood", "lahmian-vampire", "band--lahmian-special-skills-hypnotize")


def lahmia_vampire(power):
    band, profile, rule = power
    return canonical(band, profile, "weapon.sword", collection="trollheim", special_rule_ids=(rule,))


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


def savage_goblin_pair():
    """A Savage Goblin and the eligible Big Boss provider of its own warband."""
    goblin = canonical("lustria-savage-goblins", "savage-goblins", "weapon.mace", collection="trollheim")
    boss = canonical("lustria-savage-goblins", "big-boss", "weapon.sword", collection="trollheim")
    assert (goblin.characteristics.leadership, boss.characteristics.leadership) == (5, 7)
    return goblin, boss


def with_provider(boss, side, inches=4):
    """A duel context offering ``boss`` to ``side`` at ``inches``."""
    return DuelContext(charging=(), active_participant="first",
        nearby=(LocalParticipant("boss", side, boss),),
        distances=((side, "boss", inches),))


def bare_duel(first, second):
    return initialize_duel(first, second, StrictDice([]),
        context=DuelContext(charging=(), active_participant="first"))


def tape(*rows):
    return StrictDice([{"key": key, "value": value} for key, value in rows])


def test_deceive_bars_a_failed_enemy_for_that_combat_phase_only():
    vampire = lahmia_vampire(DECEIVE)
    assert "mechanic.lahmia-deceive" in vampire.global_effects.tags
    enemy = bare()
    # Activation: the vampire names the in-contact enemy, its own seven fails on
    # a double six, and the tape holds only the vampire's two misses -- the
    # barred enemy never asks for a die at all.
    dice = tape(("round.0.second.deceive.0", 6), ("round.0.second.deceive.1", 6),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.deceive", "value": True}])
    blocked = resolve_round(vampire, enemy, bare_duel(vampire, enemy), dice, decisions)
    dice.finish()
    decisions.finish()
    assert blocked.state.second.charm_attack_blocked is True
    assert len(blocked.attacks) == 2 and not blocked.attacks[0].hit
    # The suppression lasts that combat phase only: the next phase tests again,
    # the doubled three passes the enemy's own seven, and both sides strike.
    dice = tape(("round.1.second.deceive.0", 3), ("round.1.second.deceive.1", 3),
                ("round.1.first.attack.0.hit", 1), ("round.1.first.attack.1.hit", 1),
                ("round.1.second.attack.0.hit", 1))
    decisions = StrictDecisions([{"key": "round.1.second.deceive", "value": True}])
    after = resolve_round(vampire, enemy, blocked.state, dice, decisions)
    dice.finish()
    decisions.finish()
    assert after.state.second.charm_attack_blocked is False
    assert len(after.attacks) == 3


def test_deceive_passes_over_undead_daemons_and_psychology_immune_enemies():
    vampire = lahmia_vampire(DECEIVE)
    # The Trollheim Zombie prints both Undead and immunity to Psychology, the
    # Carnival's two Daemons print Daemon and immunity, and the Deathwish Slayers
    # print immunity alone: between them the whole printed exclusion list is
    # present as real model facts.
    zombie = canonical("trollheim-undead", "zombies", collection="trollheim")
    assert "nature.undead" in zombie.global_effects.tags
    assert "mechanic.psychology-immunity" in zombie.global_effects.tags
    slayers = canonical("clan-angrund-kep", "dwarf-troll-slayers", "weapon.mace")
    assert "mechanic.psychology-immunity" in slayers.global_effects.tags
    daemons = canonical("carnival-of-chaos", "plague-bearers")
    assert "nature.daemon" in daemons.global_effects.tags
    for name, enemy, theirs in (("zombie", zombie, 1), ("slayers", slayers, 1), ("daemons", daemons, 2)):
        # No decision is ever offered and no Leadership die is ever consumed;
        # every attack on the tape is one of the two sides' own.
        rows = [("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1)]
        rows += [(f"round.0.second.attack.{index}.hit", 1) for index in range(theirs)]
        dice, decisions = tape(*rows), StrictDecisions([])
        result = resolve_round(vampire, enemy, bare_duel(vampire, enemy), dice, decisions)
        dice.finish()
        decisions.finish()
        assert result.state.second.charm_attack_blocked is False, name
        assert len(result.attacks) == 2 + theirs, name


def test_deceive_never_borrows_a_nearby_leader_for_the_enemy():
    # Deceive prints "using its own Leadership": the eligible four-inch Big Boss
    # of the enemy's own warband is never offered, so the doubled three that the
    # borrowed seven would pass fails against the goblin's own five.
    vampire = lahmia_vampire(DECEIVE)
    goblin, boss = savage_goblin_pair()
    dice = tape(("round.0.second.deceive.0", 3), ("round.0.second.deceive.1", 3),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.deceive", "value": True}])
    blocked = resolve_round(vampire, goblin,
        initialize_duel(vampire, goblin, StrictDice([]), context=with_provider(boss, "second")),
        dice, decisions)
    dice.finish()
    decisions.finish()
    assert blocked.state.second.charm_attack_blocked is True
    assert len(blocked.attacks) == 2


def test_hypnotize_bars_the_target_and_lifts_attackers_to_hit_by_one():
    vampire = lahmia_vampire(HYPNOTIZE)
    assert "mechanic.lahmian-hypnotize" in vampire.global_effects.tags
    enemy = bare()
    dice = tape(("round.0.second.hypnotize.0", 6), ("round.0.second.hypnotize.1", 6),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.hypnotize", "value": True}])
    result = resolve_round(vampire, enemy, bare_duel(vampire, enemy), dice, decisions)
    dice.finish()
    decisions.finish()
    assert result.state.second.charm_attack_blocked is True
    assert len(result.attacks) == 2
    # The printed modifier: the vampire's five against the enemy's three needs
    # 2+ against a hypnotized model and 3+ in the control phase below.
    assert [attack.hit_target for attack in result.attacks] == [2, 2]
    dice = tape(("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1),
                ("round.0.second.attack.0.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.hypnotize", "value": False}])
    plain = resolve_round(vampire, enemy, bare_duel(vampire, enemy), dice, decisions)
    dice.finish()
    decisions.finish()
    assert [attack.hit_target for attack in plain.attacks] == [3, 3, 4]


def test_hypnotize_reads_a_supplied_leaders_leadership():
    # Hypnotize prints "a Leadership test", not "its own": the doubled three is
    # six, which the goblin's own five fails and the eligible Big Boss passes.
    vampire = lahmia_vampire(HYPNOTIZE)
    goblin, boss = savage_goblin_pair()
    dice = tape(("round.0.second.hypnotize.0", 3), ("round.0.second.hypnotize.1", 3),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1),
                ("round.0.second.attack.0.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.hypnotize", "value": True},
                                 {"key": "round.0.second.hypnotize.leader.boss", "value": True}])
    borrowed = resolve_round(vampire, goblin,
        initialize_duel(vampire, goblin, StrictDice([]), context=with_provider(boss, "second")),
        dice, decisions)
    dice.finish()
    decisions.finish()
    assert borrowed.state.second.charm_attack_blocked is False
    assert len(borrowed.attacks) == 3
    # Own value: with no provider supplied the same six fails against five.
    dice = tape(("round.0.second.hypnotize.0", 3), ("round.0.second.hypnotize.1", 3),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.hypnotize", "value": True}])
    blocked = resolve_round(vampire, goblin, bare_duel(vampire, goblin), dice, decisions)
    dice.finish()
    decisions.finish()
    assert blocked.state.second.charm_attack_blocked is True


def test_hypnotize_affects_a_non_immune_enemy_but_not_a_psychology_immune_one():
    # The printed exception is immunity to Psychology alone, so a plain enemy is
    # a valid target while the Undead Wight and the Deathwish Slayers, which both
    # print that immunity, are not.
    vampire = lahmia_vampire(HYPNOTIZE)
    goblin = canonical("night-goblins-web", "night-goblin-warriors")
    assert "mechanic.psychology-immunity" not in goblin.global_effects.tags
    dice = tape(("round.0.second.hypnotize.0", 6), ("round.0.second.hypnotize.1", 6),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1))
    decisions = StrictDecisions([{"key": "round.0.second.hypnotize", "value": True}])
    result = resolve_round(vampire, goblin, bare_duel(vampire, goblin), dice, decisions)
    dice.finish()
    decisions.finish()
    assert result.state.second.charm_attack_blocked is True
    wight = canonical("necrarchs-mou", "wight", "weapon.sword")
    slayers = canonical("clan-angrund-kep", "dwarf-troll-slayers", "weapon.mace")
    for enemy in (wight, slayers):
        assert "mechanic.psychology-immunity" in enemy.global_effects.tags
        # No decision is ever offered to an immune enemy, so the tape holds only
        # the three attacks and the unaffected enemy keeps its own blow.
        dice, decisions = tape(("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1),
                               ("round.0.second.attack.0.hit", 1)), StrictDecisions([])
        exempt = resolve_round(vampire, enemy, bare_duel(vampire, enemy), dice, decisions)
        dice.finish()
        decisions.finish()
        assert exempt.state.second.charm_attack_blocked is False
        assert len(exempt.attacks) == 3


def test_enchanting_beauty_lowers_a_borrowed_leadership_too():
    # "Any living enemy in base contact suffers -1 Leadership": the borrowed
    # seven of an eligible same-warband leader drops with it.
    vampire = canonical("chaos-streets-undead-bloodlines", "lahmia-vampire", "weapon.sword",
                        collection="trollheim")
    goblin, boss = savage_goblin_pair()
    state = initialize_duel(goblin, vampire, StrictDice([]), context=with_provider(boss, "first"))
    faces = [{"key": f"probe.{index}", "value": value} for index, value in enumerate((4, 3))]
    borrowed = StrictDecisions([{"key": "probe.leader.boss", "value": True}])
    assert resolve_local_leadership(goblin, state, StrictDice(list(faces)),
                                    borrowed, "probe", first=True) is True
    borrowed.finish()
    tagged = apply_opponent_leadership(goblin, vampire, state)
    assert "condition.enchanting-beauty" in tagged.global_effects.tags
    borrowed = StrictDecisions([{"key": "probe.leader.boss", "value": True}])
    assert resolve_local_leadership(tagged, state, StrictDice(list(faces)),
                                    borrowed, "probe", first=True) is False
    borrowed.finish()


def test_enchanting_beauty_lowers_only_a_living_contacting_enemy():
    vampire = canonical("chaos-streets-undead-bloodlines", "lahmia-vampire", "weapon.sword",
                        collection="trollheim")
    assert "mechanic.enchanting-beauty" in vampire.global_effects.tags
    living, undead, daemon = (bare(), canonical("necrarchs-mou", "wight", "weapon.sword"),
                              canonical("carnival-of-chaos", "plague-bearers"))
    contact = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(living, vampire, StrictDice([]), context=contact)
    tagged = apply_opponent_leadership(living, vampire, state)
    assert "condition.enchanting-beauty" in tagged.global_effects.tags
    # The printed exemption: "no effect on Undead or Daemons".
    assert "condition.enchanting-beauty" not in apply_opponent_leadership(
        undead, vampire, state).global_effects.tags
    assert "condition.enchanting-beauty" not in apply_opponent_leadership(
        daemon, vampire, state).global_effects.tags
    # Observable consequence: a roll of seven passes on the enemy's own seven
    # and fails once the contacting beauty drops it to six.
    faces = [{"key": f"probe.{index}", "value": value} for index, value in enumerate((3, 4))]
    plain = initialize_duel(living, vampire, StrictDice([]), context=contact)
    assert resolve_local_leadership(living, plain, StrictDice(list(faces)),
                                    StrictDecisions([]), "probe", first=True) is True
    lowered = initialize_duel(tagged, vampire, StrictDice([]), context=contact)
    assert resolve_local_leadership(tagged, lowered, StrictDice(list(faces)),
                                    StrictDecisions([]), "probe", first=True) is False


def test_deceive_tests_the_targets_own_leadership_not_a_supplied_leaders():
    # Deceive prints "using its own Leadership", so the borrowed-leader path is
    # skipped even when an eligible same-band provider stands in range.
    goblin = canonical("lustria-savage-goblins", "savage-goblins", collection="trollheim")
    boss = canonical("lustria-savage-goblins", "big-boss", "weapon.sword", collection="trollheim")
    assert (goblin.characteristics.leadership, boss.characteristics.leadership) == (5, 7)
    six = ({"key": "probe.0", "value": 3}, {"key": "probe.1", "value": 3})
    context = DuelContext(charging=("first",), active_participant="first",
        nearby=(LocalParticipant("boss", "first", boss),),
        distances=(("first", "boss", 4),))
    state = initialize_duel(goblin, bare(), StrictDice([]), context=context)
    # Own value: six fails against the goblin's five, and no leader decision is
    # ever requested (the strict tape would raise on an unexpected one).
    assert resolve_local_leadership(goblin, state, StrictDice([dict(row) for row in six]),
                                    StrictDecisions([]), "probe", first=True,
                                    own_value_only=True) is False
    # Borrowed value: the same six passes on the supplied leader's seven, which
    # is the behaviour Deceive's printed wording excludes.
    borrowed = StrictDecisions([{"key": "probe.leader.boss", "value": True}])
    assert resolve_local_leadership(goblin, state, StrictDice([dict(row) for row in six]),
                                    borrowed, "probe", first=True) is True


def test_enchanting_beauty_waits_for_the_contact_a_charge_has_not_made_yet():
    # The clause names an enemy *in base contact*, and a voluntary charge is
    # resolved before that contact exists.  The vampire supplies Fear explicitly
    # so both cases really test; the same model (Leadership 7) and the same 3+4
    # dice decide the charge, and only the role changes: the charger's own test
    # is out of contact and passes on its seven, while the side that was charged
    # is in contact, tests on six and fails the same seven.
    vampire = canonical("chaos-streets-undead-bloodlines", "lahmia-vampire", "weapon.sword",
                        collection="trollheim", trait_overrides={"causes_fear": True})
    enemy = bare()
    assert "mechanic.enchanting-beauty" in vampire.global_effects.tags
    assert "mechanic.causes-fear" in vampire.global_effects.tags
    dice = tape(("round.0.first.fear.charge.0", 3), ("round.0.first.fear.charge.1", 4),
                ("round.0.first.attack.0.hit", 1), ("round.0.second.attack.0.hit", 1),
                ("round.0.second.attack.1.hit", 1))
    decisions = StrictDecisions([])
    charging = resolve_round(enemy, vampire, initialize_duel(enemy, vampire, StrictDice([]),
        context=DuelContext(charging=("first",), active_participant="first")), dice, decisions)
    dice.finish()
    decisions.finish()
    assert charging.state.engaged and not charging.state.failed_charges
    assert charging.state.first.fear_hit_sixes is False
    dice = tape(("round.0.second.fear.charged.0", 3), ("round.0.second.fear.charged.1", 4),
                ("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1),
                ("round.0.second.attack.0.hit", 1))
    decisions = StrictDecisions([])
    contacting = resolve_round(vampire, enemy, initialize_duel(vampire, enemy, StrictDice([]),
        context=DuelContext(charging=("first",), active_participant="first")), dice, decisions)
    dice.finish()
    decisions.finish()
    assert contacting.state.second.fear_hit_sixes is True


def test_both_lahmia_powers_keep_the_tests_resource_consumption_on_success():
    # One shared witness for both powers: a carried relic auto-passes the first
    # required Leadership test and pays for it, so the spend must survive the
    # power's success path.  In the next phase the relic is already spent, the
    # same power must roll, the doubled six fails on its own seven and the
    # suppression appears then, with the resource still consumed.
    for power, name in ((DECEIVE, "deceive"), (HYPNOTIZE, "hypnotize")):
        vampire = lahmia_vampire(power)
        relic = bare(owned_item_ids=("holy_relic",))
        assert "defence.holy-relic" in relic.global_effects.tags
        dice = tape(("round.0.first.attack.0.hit", 1), ("round.0.first.attack.1.hit", 1),
                    ("round.0.second.attack.0.hit", 1))
        decisions = StrictDecisions([{"key": f"round.0.second.{name}", "value": True}])
        passed = resolve_round(vampire, relic, bare_duel(vampire, relic), dice, decisions)
        dice.finish()
        decisions.finish()
        assert passed.state.second.resources_spent == frozenset({"leadership.holy-relic"})
        assert passed.state.second.charm_attack_blocked is False
        dice = tape((f"round.1.second.{name}.0", 6), (f"round.1.second.{name}.1", 6),
                    ("round.1.first.attack.0.hit", 1), ("round.1.first.attack.1.hit", 1))
        decisions = StrictDecisions([{"key": f"round.1.second.{name}", "value": True}])
        failed = resolve_round(vampire, relic, passed.state, dice, decisions)
        dice.finish()
        decisions.finish()
        assert failed.state.second.resources_spent == frozenset({"leadership.holy-relic"})
        assert failed.state.second.charm_attack_blocked is True
        assert len(failed.attacks) == 2


# --- Ghostly Howl ----------------------------------------------------------

def test_ghostly_howl_costs_the_tested_enemy_a_die_of_leadership():
    """The printed -D6 reaches its opponent's fear test and nothing else."""
    banshee = canonical("call-of-the-night-haint-mim", "tomb-banshee")
    assert "mechanic.ghostly-howl" in banshee.global_effects.tags
    enemy = bare()
    assert causes_fear(banshee, enemy)
    # Activation: the charged enemy's Leadership 7 drops by the howl's 6, so an
    # otherwise-passing total of 2 fails and hits-on-sixes appears.
    failed = fear_state(banshee, enemy, "first", [
        ("round.0.second.fear.charged.ghostly-howl", 6),
        ("round.0.second.fear.charged.0", 1), ("round.0.second.fear.charged.1", 1)])
    assert failed.second.fear_hit_sixes
    # Negative control: a fear causer without the howl requests no penalty die at
    # all (the strict tape refuses an unexpected or an unused roll individually)
    # and the same total passes.
    passed = fear_state(bare(trait_overrides={"causes_fear": True}), bare(), "first", [
        ("round.0.second.fear.charged.0", 1), ("round.0.second.fear.charged.1", 1)])
    assert not passed.second.fear_hit_sixes
    # Scope: the penalty belongs to fear tests, so an ordinary Leadership test of
    # the same opponent spends its own two dice only.
    state = initialize_duel(banshee, enemy, tape(("duel.charge", 6)))
    dice = tape(("round.0.second.plain.0", 1), ("round.0.second.plain.1", 1))
    resolve_local_leadership(enemy, state, dice, StrictDecisions([]),
                             "round.0.second.plain", first=False, opponent=banshee)
    dice.finish()
