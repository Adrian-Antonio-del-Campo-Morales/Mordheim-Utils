"""Knowledge declarations and bindings separated from modular rule execution."""

import pytest

ITEM = "count_of_ventimiglias_misericordia"
MECHANIC = "weapon.count-of-ventimiglias-misericordia"
CAVALCADE_DAGGER = "weapon.misericordia"


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
