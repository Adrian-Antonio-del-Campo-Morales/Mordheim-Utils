"""KnowledgePort: canonical warband/profile reads for the Campaign Manager."""
from mordheim_campaign.application.knowledge_port import CHARACTERISTIC_KEYS, KnowledgePort
from mordheim_campaign.application.state import make_draft_state


def test_options_expose_every_canonical_warband():
    port = KnowledgePort()
    options = port.options()
    assert len(options) >= 80  # mordheim + trollheim collections of the ruleset
    assert {option.collection for option in options} == {"mordheim", "trollheim"}
    for option in options:
        assert option.band_id and option.name
        assert option.minimum_models >= 3
        assert option.maximum_models >= option.minimum_models
        assert option.starting_gold > 0


def test_sisters_roster_is_canonical():
    port = KnowledgePort()
    option = port.warband("mordheim", "sisters-of-sigmar")
    rules = port.roster_rules(option.collection, option.band_id)
    assert rules.minimum_models == 3
    assert rules.maximum_models == 15
    assert rules.starting_gold == 500
    assert rules.hero_limit == 5  # matriarch 1 + augur 1 + sisters superior 3

    profiles = {profile.profile_id: profile for profile in port.profiles(option.collection, option.band_id)}
    matriarch = profiles["sigmarite-matriarch"]
    assert matriarch.kind == "hero"
    assert matriarch.cost == 70
    assert matriarch.experience == 20
    assert matriarch.characteristics == {"M": 4, "WS": 4, "BS": 4, "S": 3, "T": 3, "W": 1, "I": 4, "A": 1, "Ld": 8}
    assert matriarch.required
    assert set(matriarch.inherent_rules) == {"Leader", "Prayers of Sigmar"}
    assert matriarch.skill_tables == ("Combat", "Academic", "Strength", "Speed", "Special")

    augur = profiles["augur"]
    assert augur.inherent_rules == ("Blessed Sight",)

    sisters = profiles["sigmarite-sister"]
    assert sisters.kind == "henchman"
    assert sisters.group_maximum == 5
    assert sisters.member_maximum is None

    novices = profiles["novices"]
    assert novices.kind == "henchman"
    assert novices.member_maximum == 10


def test_every_warband_has_usable_hero_profiles():
    port = KnowledgePort()
    for option in port.options():
        profiles = port.profiles(option.collection, option.band_id)
        heroes = [profile for profile in profiles if profile.kind == "hero"]
        assert heroes, option.band_id
        assert any(not profile.random_characteristics and profile.member_maximum not in (0, None) for profile in heroes), option.band_id
        rules = port.roster_rules(option.collection, option.band_id)
        assert rules.hero_limit and rules.hero_limit > 0, option.band_id
        for profile in profiles:
            assert set(profile.characteristics) == set(CHARACTERISTIC_KEYS)


def test_every_kb_draft_starter_is_legal():
    """The initial draft derived from the KB is legal for every warband."""
    port = KnowledgePort()
    for option in port.options():
        campaign = make_draft_state(port, option.band_id, collection=option.collection).campaign
        assert campaign.draft_is_legal, option.band_id
        assert option.minimum_models <= campaign.draft_model_count <= option.maximum_models
        assert 1 <= campaign.draft_hero_count <= campaign.hero_limit
        assert campaign.draft_treasury >= 0
        assert campaign.band_id == option.band_id
        for warrior in campaign.warriors:
            assert warrior.profile_id
            assert warrior.cost > 0
            assert set(warrior.stats) == set(CHARACTERISTIC_KEYS)


def test_equipment_offers_resolve_canonical_item_names():
    port = KnowledgePort()
    offers = port.equipment("mordheim", "sisters-of-sigmar")
    by_id = {offer.item_id: offer for offer in offers}
    assert by_id["sigmarite_hammer"].name == "Sigmarite Hammer"
    assert by_id["light_armour"].name == "Light Armour"
    assert by_id["dagger"].cost == 2
    # Every list declared by the warband is visible as a creation offer.
    option = port.warband("mordheim", "sisters-of-sigmar")
    lists = {offer.list_id for offer in offers}
    assert "sisters-of-sigmar-equipment-lists" in lists


def test_unknown_warband_raises():
    port = KnowledgePort()
    try:
        port.warband("mordheim", "does-not-exist")
    except ValueError as exc:
        assert "Unknown warband" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("expected an unknown-warband error")


def test_port_exposes_the_kb_post_battle_sequence():
    """The campaign loading contract is reusable from the app's KnowledgePort."""
    port = KnowledgePort()
    sequence = port.post_battle_sequence()
    assert sequence.id == "campaign.post-battle"
    assert len(sequence.steps) == 10
    assert [step.id for step in sequence.steps][:3] == [
        "campaign.step.serious-injuries",
        "campaign.step.experience",
        "campaign.step.exploration",
    ]
    # Every resolved catalogue is available through the same port.
    catalog = port.campaign_catalog()
    for resolves in sequence.resolved_catalogues:
        assert catalog.has_catalogue(resolves)
    assert len(catalog.documents) == 12
    assert len(catalog.catalogue("trading-post.yaml")["items"]) == 338


def test_price_override_only_for_source_confirmed_exceptions():
    """Trading Post prices prevail unless the warband source confirms an exception."""
    port = KnowledgePort()

    # No override for the majority of list prices: creation evidence only.
    assert port.price_override("mordheim", "sisters-of-sigmar", "holy_tome") is None
    assert port.price_override("mordheim", "sisters-of-sigmar", "dagger") is None
    assert port.price_override("mordheim", "mercenaries", "duelling_pistol") is None

    # Impeccable Care (Nuln): black-powder list costs apply always.
    assert port.price_override("mordheim", "gunnery-school-of-nuln", "pistol") == 10
    assert port.price_override("mordheim", "gunnery-school-of-nuln", "handgun") == 25
    assert port.price_override("mordheim", "gunnery-school-of-nuln", "hand_held_mortar") == 70
    # …but the rule covers black-powder weapons, not the Miscellaneous accessory.
    assert port.price_override("mordheim", "gunnery-school-of-nuln", "superior_blackpowder") is None

    # Powder's Expensive! (Hochland): heroes always pay the higher list cost.
    assert port.price_override("mordheim", "hochland-bandits", "pistol") == 20
    # Armour rule (Lizardmen): light armour always costs 50 gc for Lizardmen.
    assert port.price_override("mordheim", "lizardmen", "light_armour") == 50
    assert port.price_override("mordheim", "lizardmen", "javelins") is None

    # The amount always agrees with the printed list cost it encodes.
    for option in port.options():
        for offer in port.equipment(option.collection, option.band_id):
            override = port.price_override(option.collection, option.band_id, offer.item_id)
            if override is not None:
                assert override == offer.cost, (option.band_id, offer.item_id)


def test_port_exposes_hireling_and_group_resolution():
    port = KnowledgePort()
    hirelings = port.hireling_catalogue()
    assert len(hirelings.profiles) == 102
    entries = port.campaign_catalog().catalogue("hired-swords-and-dramatis.yaml")
    entries = entries["hired_swords"] + entries["dramatis_personae"]
    # Hiring entries are the canonical consumers of the profile pool.
    assert {entry["profile_id"] for entry in entries} <= hirelings.profile_ids
    groups = {group["id"] for group in port.warband_groups()}
    assert "warband-group.human-mercenary" in groups
