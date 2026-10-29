"""Construction contracts for patron and supplied states, split from modular.

The four checks moved here assert what the canonical compiler produces (the
Night Goblin Hatred recipients and their exemptions, the Clockwork Construct
immunity and its negative control, and the four supplied Chaos patron
branches).  They own the compiler and are not engine rounds; names, markers
and assertions are the ones the modular file carried.  The builders and
constants are copied so the module stays standalone.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def canonical(band, profile, *, collection="mordheim", conditions=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", condition_ids=tuple(conditions), **options))


def emissary(patron):
    """Fanatic Online 94: native equipment and one complete selected patron."""
    return compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.hired-sword.2a",
        profile_id="hireling.hired-sword.emissary-of-chaos",
        main_weapon_id="weapon.sword", armour_id="armour.chaos-armour",
        off_hand_id="defence.shield", defence_ids=("defence.helmet",),
        special_rule_ids=("hireling.hired-sword.emissary-of-chaos.patron." + patron,)))


# --- Night Goblin Hatred of Dwarfs -----------------------------------------

def test_hate_stunties_reaches_the_night_goblins_only():
    boss = canonical("night-goblins-mic", "big-boss")
    assert "mechanic.hatred-dwarfs" in boss.global_effects.tags
    # The printed exemption: a Fanatic is not affected.
    assert "mechanic.hatred-dwarfs" not in canonical(
        "night-goblins-mic", "fanatics").global_effects.tags
    # A sibling species of the same warband stays without it too.
    assert "mechanic.hatred-dwarfs" not in canonical(
        "night-goblins-mic", "cave-squigs").global_effects.tags


def test_hate_stunties_is_gone_from_the_sibling_bands_other_records():
    for band, profile in (("night-goblins-web", "boss"), ("night-goblins-kaz", "big-boss")):
        assert "mechanic.hatred-dwarfs" in canonical(band, profile).global_effects.tags
    assert "mechanic.hatred-dwarfs" not in canonical(
        "night-goblins-web", "night-goblin-fanatics").global_effects.tags


# --- The Clockwork Construct immunity --------------------------------------

def test_constructs_are_psychology_immune_and_the_human_heroes_are_not():
    soldier = canonical("clockworkers-sc", "clockwork-soldiers")
    assert "mechanic.psychology-immunity" in soldier.global_effects.tags
    assert "mechanic.psychology-immunity" in canonical(
        "clockworkers-sc", "clockwork-fiend").global_effects.tags
    # Negative control: the band's own living profiles stay unaffected.
    assert "mechanic.psychology-immunity" not in canonical(
        "clockworkers-sc", "apprentices").global_effects.tags


# --- The supplied pre-battle states ----------------------------------------

def test_the_emissary_patron_states_are_the_supplied_branch():
    khorne, nurgle = emissary("khorne"), emissary("nurgle")
    slaanesh, tzeentch = emissary("slaanesh"), emissary("tzeentch")
    assert khorne.global_effects.frenzy
    assert khorne.global_effects.attacks_bonus == 1
    assert "poison.black-lotus" in nurgle.global_effects.tags
    assert "mechanic.causes-fear" in nurgle.global_effects.tags
    assert "mechanic.causes-fear" not in slaanesh.global_effects.tags
    assert "mechanic.slaanesh-charge-test" in slaanesh.global_effects.tags
    assert slaanesh.global_effects.incoming_hit_modifier == -1
    assert "identity.spellcaster" in tzeentch.global_effects.tags
    assert "poison.black-lotus" not in khorne.global_effects.tags
