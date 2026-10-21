"""Campaign artefact: the Count of Ventimiglia's Misericordia.

Source (``sources/knowledge``): ``catalog/campaign/exploration-and-income.yaml``
/ ``campaign.magical-artefact.count-of-ventimiglias-misericordia``: *"Treated as a
sword. Opponents wounded by it are stunned on a result of 1-3 (Undead are knocked
down as normal) and put out of action on a 4-6."*

The artefact is supplied, not acquired: the physical piece enters the kit
(``count_of_ventimiglias_misericordia``) and its weapon mechanic is selected
(``weapon.count-of-ventimiglias-misericordia``), the same possession/selection
pair the equipment catalogue already uses.  The clause pinned here is the printed
table itself, resolved through the ordinary injury stage, so the sword's parry and
every ordinary injury consumer stay unchanged.  The Cursed Cavalcade
``weapon.misericordia`` is a different weapon with a different consequence and is
checked here for conservation, never re-used.
"""
from __future__ import annotations

import pytest

from mordheim_combat.kernel import require_optimized_support
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.phases import Condition
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

ITEM = "count_of_ventimiglias_misericordia"
MECHANIC = "weapon.count-of-ventimiglias-misericordia"
CAVALCADE_DAGGER = "weapon.misericordia"


def tape(*values):
    return StrictDice([{"key": key, "value": value} for key, value in values])


def bearer():
    """The supplied bearer: the artefact is carried and selected as the weapon."""
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id=MECHANIC, owned_item_ids=(ITEM,)))


def living_opponent():
    """One Wound, so a single unsaved wound reaches the Injury chart."""
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7),
        main_weapon_id="weapon.mace"))


def undead_opponent():
    """Canonical Undead with No Pain: the source's own knocked-down exception."""
    return compile_fighter(FighterBuild(
        "mordheim", band_id="trollheim-undead", profile_id="zombies",
        collection="trollheim", main_weapon_id="weapon.fist"))


def strike(foe, injury_face, *, fear=False):
    """One round: configuration -> compile_fighter -> initialize_duel -> resolve_round.

    The defender is the second participant and carries a single Wound, so the
    first unsaved wound resolves its injury inside this round; the charging
    attacker strikes first and its attack chain is the only one rolled.
    """
    owner = bearer()
    rolls = [("round.0.first.attack.0.hit", 4), ("round.0.first.attack.0.wound", 4),
             ("round.0.first.attack.0.injury.0", injury_face)]
    if fear:
        # Undead cause Fear: the charging attacker tests and passes on 1+1.
        rolls = [("round.0.first.fear.charge.0", 1), ("round.0.first.fear.charge.1", 1), *rolls]
    dice = tape(*rolls)
    start = initialize_duel(owner, foe, tape(), context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_round(owner, foe, start, dice, StrictDecisions([]))
    dice.finish()
    assert result.state.first.condition == Condition.STANDING
    return result.state.second.condition


@pytest.mark.phase3_rules
@pytest.mark.parametrize("face,condition", [
    (1, Condition.STUNNED), (3, Condition.STUNNED), (4, Condition.OUT), (6, Condition.OUT),
])
def test_the_printed_table_stuns_on_one_to_three_and_takes_out_on_four_to_six(face, condition):
    owner = bearer()
    # The physical artefact is carried and its mechanic is the selected weapon:
    # "treated as a sword" is the sword tag plus the printed parry.
    assert [piece.item_id for piece in owner.mutation_equipment if piece.item_id == ITEM] == [ITEM]
    assert "weapon.sword" in owner.main_weapon.tags
    assert owner.main_weapon.parry is True
    # The optimized ports cannot express this table, so the duel stays modular.
    with pytest.raises(ValueError, match="modular"):
        require_optimized_support(owner, living_opponent())
    # 1-3 is stunned where the core chart would knock the victim down, and 4
    # takes it out of action where the core chart would still only stun.
    assert strike(living_opponent(), face) == condition


@pytest.mark.phase3_rules
@pytest.mark.parametrize("face,condition", [
    (1, Condition.KNOCKED_DOWN), (3, Condition.KNOCKED_DOWN), (4, Condition.OUT),
])
def test_undead_are_knocked_down_by_the_stun_band_instead_of_stunned(face, condition):
    foe = undead_opponent()
    # No Pain is the canonical Undead clause that turns the stun into a knock-down.
    assert "nature.undead" in foe.global_effects.tags
    assert "skill.ignore-pain" in foe.global_effects.tags
    assert strike(foe, face, fear=True) == condition


@pytest.mark.phase1_kb_contracts
def test_the_canonical_item_resolves_to_its_own_mechanic_and_the_cavalcade_dagger_is_conserved():
    from mordheim_knowledge.campaign import load_campaign_catalog
    from mordheim_knowledge.loader import load_items, load_mechanics, load_simulation_mappings
    from mordheim_construction.contracts import effect_index

    rows = {row["id"]: row for row in load_items("mordheim")}
    assert rows[ITEM]["combat_status"] == "implemented"
    assert rows[ITEM]["mechanic_id"] == MECHANIC
    mappings = {row["item_id"]: row
                for row in load_simulation_mappings("mordheim")["item_mappings"]}
    assert mappings[ITEM]["status"] == "implemented"
    # The item joins its mechanic exactly as the compiler resolves it.
    by_option = {row.get("engine_option"): row["id"] for row in load_mechanics("mordheim")["weapons"]}
    assert by_option[mappings[ITEM]["engine_option"]] == MECHANIC
    # The campaign row grants the canonical id instead of synthesising one.
    catalogue = load_campaign_catalog("mordheim").catalogue("exploration-and-income")
    artefact = next(row for row in catalogue["magical_artefacts"]["results"]
                    if row["id"] == "campaign.magical-artefact.count-of-ventimiglias-misericordia")
    assert artefact["item_id"] == ITEM
    # Distinguished identities: the artefact is not the Cursed Cavalcade dagger.
    mine = effect_index("mordheim")[MECHANIC].effect
    dagger = effect_index("mordheim")[CAVALCADE_DAGGER].effect
    assert MECHANIC != CAVALCADE_DAGGER and mine != dagger
    assert "weapon.count-of-ventimiglias-misericordia" in mine.tags
    assert "weapon.count-of-ventimiglias-misericordia" not in dagger.tags
    # The dagger's own clause is untouched: +1 enemy armour save and the
    # coup-de-grace denial against a knocked-down opponent.
    assert dagger.target_armour_bonus == 1
    assert dagger.ignore_armour_against_knocked_down is True
