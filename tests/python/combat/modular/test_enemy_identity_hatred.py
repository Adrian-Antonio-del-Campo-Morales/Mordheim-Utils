"""Enemy identity, conditioned Leadership and qualified Hatred.

Each Hatred clause is exercised three ways on the canonical compiler and the
modular hit-reroll consumer: activation against the printed hated identity, a
negative control that must not fire, and the printed exception.  Burn the Witch
reads the compiled spellcaster identity (no spell is cast), Hang the Bandit the
canonical Bandit/Outlaw warband class, and Profound Hatred every opposing
warband except the Sisters of Sigmar.
"""
from __future__ import annotations

from dataclasses import replace

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import _combined_effect, _hit_reroll
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root
import pytest


pytestmark = pytest.mark.rule_behavior

# The shared root resolves the documented knowledge overlay when one is exported,
# so this family reads the same tree the rest of the construction suite reads.
ROOT = knowledge_root()


def canonical(band, profile, weapon="weapon.fist", *, collection="mordheim"):
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
        collection=collection, main_weapon_id=weapon), ROOT)


def rerolls(attacker, defender, *, first_round=True):
    return _hit_reroll(attacker, defender, attacker.main_weapon,
                       _combined_effect(attacker, attacker.main_weapon), first_round, False)


# --- Burn the Witch --------------------------------------------------------

def test_burn_the_witch_targets_the_compiled_spellcaster_identity():
    captain = canonical("witch-hunters", "witch-hunter-captain", "weapon.mace")
    shaman = canonical("night-goblins-web", "shaman")
    assert "mechanic.burn-the-witch" in captain.global_effects.tags
    # The target is capable of casting spells; nothing is cast during the duel.
    assert "identity.spellcaster" in shaman.global_effects.tags
    assert rerolls(captain, shaman) is True
    # Negative control: an ordinary warrior of the same warband is not a caster.
    assert "identity.spellcaster" not in canonical(
        "night-goblins-web", "night-goblin-warriors").global_effects.tags
    assert rerolls(captain, canonical("night-goblins-web", "night-goblin-warriors")) is False
    # The shared Hatred timing is first-round only.
    assert rerolls(captain, shaman, first_round=False) is False


def test_burn_the_witch_is_shared_by_both_witch_hunter_warbands():
    caster = canonical("night-goblins-web", "shaman")
    for band, profile, collection in (
        ("witch-hunters", "witch-hunter-captain", "mordheim"),
        ("witch-hunters", "witch-hunters", "mordheim"),
        ("trollheim-witch-hunters", "witch-hunter-captain", "trollheim"),
        ("trollheim-witch-hunters", "witch-hunters", "trollheim"),
    ):
        hunter = canonical(band, profile, "weapon.mace", collection=collection)
        assert "mechanic.burn-the-witch" in hunter.global_effects.tags, (band, profile)
        assert rerolls(hunter, caster) is True, (band, profile)


def test_burn_the_witch_targets_the_casters_the_rule_name_list_missed():
    # The two canonical casters whose printed rule heading never says "Wizard":
    # the Apprentice Sorcerer's "Rituals of Chaos" and the Mist Mage's
    # "Wizard (Mist Mage)".  Both carry the identity as a profile fact.
    hunter = canonical("witch-hunters", "witch-hunters", "weapon.mace")
    for band, profile in (("sons-of-hashut", "apprentice-sorcerer"),
                          ("lothern-sea-patrol-sar", "mist-mage")):
        caster = canonical(band, profile)
        assert "identity.spellcaster" in caster.global_effects.tags, (band, profile)
        assert rerolls(hunter, caster) is True, (band, profile)


def test_burn_the_witch_excludes_prayer_users_from_the_caster_identity():
    # The printed clause names spellcasting.  A priest who only uses Prayers is
    # not a caster, which is the same distinction the campaign's Witch Hunter
    # hiring rule draws.
    hunter = canonical("witch-hunters", "witch-hunters", "weapon.mace")
    matriarch = canonical("sisters-of-sigmar", "sigmarite-matriarch")
    assert "identity.spellcaster" not in matriarch.global_effects.tags
    assert rerolls(hunter, matriarch) is False
    # The Woodsmen Friar's rule is headed "Wizard" but prints only the prayers
    # of Taal; the capability is read from that text, not from the heading.
    friar = canonical("woodsmen-de-artois-mou", "friar")
    assert "identity.spellcaster" not in friar.global_effects.tags
    assert rerolls(hunter, friar) is False


# --- Hang the Bandit -------------------------------------------------------

def test_hang_the_bandit_targets_the_canonical_bandit_and_outlaw_warbands():
    hunter = canonical("horned-hunters", "horned-hunter")
    assert "mechanic.hang-the-bandit" in hunter.global_effects.tags
    for band, profile in (("hochland-bandits", "bandit-prince"),
                          ("outlaws-of-stirwood-forest", "bandit-leader"),
                          ("outlaws-of-stirwood-forest-redux-fbg", "bandit-leader")):
        outlaw = canonical(band, profile)
        assert "warband-group.bandit" in outlaw.global_effects.tags, band
        assert rerolls(hunter, outlaw) is True, band
    # Negative control: a non-bandit warband is not the printed category.
    assert rerolls(hunter, canonical("mercenaries", "warriors")) is False
    assert rerolls(hunter, canonical("hochland-bandits", "bandit-prince"), first_round=False) is False


def test_hang_the_bandit_is_shared_by_the_horned_hunter_and_the_initiates():
    outlaw = canonical("hochland-bandits", "bandit-prince")
    for profile in ("horned-hunter", "initiates"):
        fighter = canonical("horned-hunters", profile)
        assert "mechanic.hang-the-bandit" in fighter.global_effects.tags, profile
        assert rerolls(fighter, outlaw) is True, profile


# --- Profound Hatred -------------------------------------------------------

def test_profound_hatred_covers_every_opposing_warband_except_the_sisters():
    soul = canonical("chaos-streets-mordheim-inhabitants", "desolate-soul", collection="trollheim")
    assert "mechanic.profound-hatred" in soul.global_effects.tags
    for band, profile in (("mercenaries", "warriors"), ("night-goblins-web", "night-goblin-warriors"),
                          ("undead", "zombies"), ("witch-hunters", "witch-hunters")):
        assert rerolls(soul, canonical(band, profile)) is True, (band, profile)
    # Semantic exception: the printed carve-out.
    sister = canonical("sisters-of-sigmar", "augur")
    assert "band.sisters-of-sigmar" in sister.global_effects.tags
    assert rerolls(soul, sister) is False
    # The shared Hatred timing is first-round only.
    assert rerolls(soul, canonical("mercenaries", "warriors"), first_round=False) is False


# --- Fanatical (Maximilian the Mad) ----------------------------------------

MAXIMILIAN = "hireling.dramatis.maximilian-the-mad"


def maximilian(**options):
    """The source's own bearer, through his printed double-handed kit."""
    return compile_fighter(FighterBuild("mordheim",
        band_id="hirelings.dramatis-personae.1b", profile_id=MAXIMILIAN, collection="mordheim",
        main_weapon_id="weapon.double-handed-weapon",
        owned_item_ids=(f"{MAXIMILIAN}.item.double-handed-holy-weapon",), **options), ROOT)


def test_fanatical_covers_every_printed_warband_category():
    fanatic = maximilian()
    assert "mechanic.fanatical-hatred" in fanatic.global_effects.tags
    for band, profile in (("orc-mob", "orc-boss"),
                          ("black-orcs", "black-orc-boss"),
                          ("forest-goblins", "chieftain"),
                          ("horned-hunters", "horned-hunter"),
                          ("sisters-of-sigmar", "augur"),
                          ("skaven-clan-eshin", "assassin-adept"),
                          ("undead", "zombies"),
                          ("beastmen-raiders", "beastmen-chieftain"),
                          ("cult-of-the-possessed", "magister"),
                          ("carnival-of-chaos", "carnival-master")):
        assert rerolls(fanatic, canonical(band, profile)) is True, band
    # "Middenheimers" is the Mercenary variant, not a species: the same band is
    # eligible without it and hated with it.
    assert rerolls(fanatic, canonical("mercenaries", "mercenary-captain")) is False
    middenheim = compile_fighter(FighterBuild("mordheim", band_id="mercenaries",
        profile_id="mercenary-captain", collection="mordheim",
        special_rule_ids=("band--middenheim-physical-prowess",)), ROOT)
    assert "mercenary-origin.middenheim" in middenheim.global_effects.tags
    assert rerolls(fanatic, middenheim) is True
    # An unlisted warband is never covered.
    assert rerolls(fanatic, canonical("witch-hunters", "witch-hunters")) is False
    # "Orcs and Goblins" is the canonical category the KB uses for that printed
    # name, so every list inside it is named by the source's category.
    assert rerolls(fanatic, canonical("night-goblins-web", "night-goblin-warriors")) is True
    # The shared Hatred timing is first-round only.
    assert rerolls(fanatic, canonical("carnival-of-chaos", "carnival-master"),
                   first_round=False) is False


def test_fanatical_still_takes_the_ordinary_hatred_exemptions():
    """His own Frenzy and the shared gates suppress the printed Hatred."""
    fanatic = maximilian()
    assert fanatic.global_effects.frenzy  # the separate Religious Fervour clause
    target = canonical("cult-of-the-possessed", "magister")
    assert _hit_reroll(fanatic, target, fanatic.main_weapon,
                       _combined_effect(fanatic, fanatic.main_weapon), True, False) is True
    assert _hit_reroll(fanatic, target, fanatic.main_weapon,
                       _combined_effect(fanatic, fanatic.main_weapon), True, False,
                       frenzy=True) is False


def test_fanatical_reaches_the_attack_tape_only_for_a_listed_warband():
    """The canonical pipeline asks for the reroll, and only where the list says so.

    A tape that is not consumed proves the opposite: the exemption keeps the
    listed reroll out of the dice stream while Frenzy holds, and the unlisted
    warband is never offered it at all.
    """
    fanatic = maximilian()
    init = StrictDice([])
    own = initialize_fighter(fanatic, init, "f")
    init.finish()
    assert own.frenzy
    for band, profile, reroll in (("carnival-of-chaos", "carnival-master", False),
                                  ("witch-hunters", "witch-hunters", False)):
        target = canonical(band, profile)
        tape = StrictDice([{"key": "f.hit", "value": 1}]
                          + ([{"key": "f.hit.reroll", "value": 1}] if reroll else []))
        result = resolve_reference_attack(fanatic, target, own, initialize_fighter(target, tape, "t"),
                                          fanatic.main_weapon, tape, key="f", first_round=True)
        tape.finish()
        assert not result.hit
    # With Frenzy not active the printed list is the only difference left.
    calm = replace(own, frenzy=False)
    for band, profile, reroll in (("carnival-of-chaos", "carnival-master", True),
                                  ("witch-hunters", "witch-hunters", False)):
        target = canonical(band, profile)
        tape = StrictDice([{"key": "f.hit", "value": 1}]
                          + ([{"key": "f.hit.reroll", "value": 1}] if reroll else []))
        result = resolve_reference_attack(fanatic, target, calm, initialize_fighter(target, tape, "t"),
                                          fanatic.main_weapon, tape, key="f", first_round=True)
        tape.finish()
        assert not result.hit
