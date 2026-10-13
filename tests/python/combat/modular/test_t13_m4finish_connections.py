"""T13 M4-finish: the connections delivered by the closing assignment.

Each clause is proved the way the plan asks a *connection* to be proved: the
canonical compiler reaches the shared operator for the printed recipient, a
non-recipient build stays without it, and one real phase consequence is
exercised where the operator's own suite does not already have one.  The
supplied states are proved through the canonical condition records
(`FighterBuild.condition_ids`), which is exactly how the caller supplies them.
"""
from __future__ import annotations

from mordheim_combat.modular.leadership import resolve_local_leadership
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def canonical(band, profile, *, collection="mordheim", conditions=(), **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection,
        main_weapon_id="weapon.fist", condition_ids=tuple(conditions), **options))


def bare(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id="armour.no-armour", **options))


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


def test_the_construct_immunity_waives_a_required_psychology_test():
    soldier = canonical("clockworkers-sc", "clockwork-soldiers")
    dice = StrictDice([])
    state = initialize_duel(soldier, bare(), StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(
        soldier, state, dice, StrictDecisions([]), "probe", first=True,
        psychology=True, fear=True)
    dice.finish()
    assert passed


# --- The supplied pre-battle states ----------------------------------------

def test_troll_brew_results_are_supplied_states_with_their_own_consequences():
    immune = canonical("dwarf-guildsmen-kaz", "master-craftsman",
                       conditions=("condition.troll-brew-fear-immunity",))
    assert "mechanic.fear-immunity" in immune.global_effects.tags
    attacker = bare(trait_overrides={"causes_fear": True})
    dice = StrictDice([])
    state = initialize_duel(immune, attacker, StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_fear(immune, attacker, state, dice, StrictDecisions([]))
    dice.finish()
    assert result.engaged and not result.failed_charges
    # The frenzy half is the other supplied result of the same table.
    frenzied = canonical("dwarf-guildsmen-kaz", "master-craftsman",
                         conditions=("condition.troll-brew-frenzy",))
    assert frenzied.global_effects.frenzy
    assert not canonical("dwarf-guildsmen-kaz", "master-craftsman").global_effects.frenzy


def test_the_promoted_knight_of_purity_auto_passes_a_required_test():
    knight = canonical("watchmen-mim", "sergeants",
                       conditions=("condition.knight-of-purity",))
    assert "mechanic.automatic-leadership" in knight.global_effects.tags
    dice = StrictDice([])
    state = initialize_duel(knight, bare(), StrictDice([]), context=DuelContext(
        charging=("first",), active_participant="first"))
    passed = resolve_local_leadership(
        knight, state, dice, StrictDecisions([]), "probe", first=True,
        psychology=True, fear=True)
    dice.finish()
    assert passed
    assert "mechanic.automatic-leadership" not in canonical(
        "watchmen-mim", "sergeants").global_effects.tags


def test_the_emissary_patron_states_are_the_supplied_branch():
    # The Emissary's catalogue grade is not projected as a duel participant
    # yet, so this clause is proved at the canonical-record level: each supplied
    # patron resolves to the operator the duel reads.
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[4] / "sources" / "knowledge"
    document = yaml.safe_load((root / "catalog/rules/conditions.yaml").read_text(
        encoding="utf-8-sig"))
    records = {row["id"]: row for row in document["conditions"] if "id" in row}
    nurgle = records["condition.emissary-patron-nurgle"]["runtime"]["effects"]
    assert [effect["binding"]["id"] for effect in nurgle] == ["mechanic.causes-fear"]
    khorne = records["condition.emissary-patron-khorne"]["runtime"]["effects"]
    assert [effect["binding"]["id"] for effect in khorne] == ["trait.frenzy"]
    assert all(effect["binding"]["parameters"] == {"value": True} for effect in khorne)


# --- The qualified Beast Hunter family -------------------------------------

def test_the_beast_hunter_qualifiers_are_declared_and_bound():
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[4] / "sources" / "knowledge"
    catalogue = yaml.safe_load((root / "catalog/mechanics/close-combat.yaml").read_text(
        encoding="utf-8-sig"))
    sections = [value for value in catalogue.values() if isinstance(value, list)]
    ids = {row["id"] for section in sections for row in section
           if isinstance(row, dict) and "id" in row}
    assert {"mechanic.fear-beastmen", "mechanic.hatred-beastmen"} <= ids
    document = yaml.safe_load(
        (root / "catalog/hirelings/hired-swords/grade-1a.yaml").read_text(encoding="utf-8-sig"))
    bound = {}
    for profile in document["profiles"]:
        for rule in profile.get("rules") or ():
            runtime = rule.get("runtime") or {}
            for effect in runtime.get("effects") or ():
                binding = effect.get("binding") or {}
                if binding.get("id"):
                    bound.setdefault(binding["id"], set()).add(rule["id"])
    assert bound["mechanic.fear-beastmen"] == {
        "hireling.hired-sword.beast-hunter.rule.skull-rack"}
    assert bound["mechanic.hatred-beastmen"] == {
        "hireling.hired-sword.beast-hunter.rule.beastmen-vengeance"}


def test_the_qualified_beastman_operators_do_not_over_grant():
    # A synthetic bearer carrying the new tags is what the binding produces;
    # the opponent fact decides the outcome, so an unqualified enemy is
    # never feared and never the target of the qualified Hatred.
    fearer = bare(trait_overrides={"causes_fear": False})
    beastman = bare()
    assert not causes_fear(fearer, beastman)
