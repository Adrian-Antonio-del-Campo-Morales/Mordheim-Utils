"""Variable prices, variable hiring fees and typed band restrictions.

The KB declares the data structurally already; these tests pin the read side
(``post_battle_catalogue``) and the write side (``post_battle_engine``) over
the example campaign. No KB data is edited.
"""
from __future__ import annotations

from types import SimpleNamespace

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_catalogue import PostBattleCatalogue, resolve_offer_price
from tests.python.campaign.test_post_battle_engine import _pending


def _catalogue(state, port) -> PostBattleCatalogue:
    campaign = state.campaign
    return PostBattleCatalogue(
        port,
        campaign.collection,
        campaign.band_id,
        member_profile_ids=frozenset(row.profile_id for row in campaign.warriors if row.profile_id),
        hired_sword_profile_ids=frozenset(),
    )


# ------------------------------------------------------------------ prices


def test_variable_price_offers_expose_structured_dice_parts():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(o for o in (*catalogue.common_items(), *catalogue.rare_items()) if o.item_id == "blessed_water")
    assert offer.price_gc is None  # no flat price
    assert offer.price_base_gc == 10
    assert offer.price_dice == (3, 6)
    assert offer.price_variable_multiplier is None
    assert offer.price_label == "10 gc + 3D6"
    assert resolve_offer_price(offer, 10) == 20  # 10 + 10
    assert resolve_offer_price(offer, None) is None  # needs the roll


def test_dice_multiplier_variable_price():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(
        o for o in (*catalogue.common_items(), *catalogue.rare_items())
        if o.price_dice is not None and o.price_variable_multiplier is not None
    )
    total = resolve_offer_price(offer, 2)
    assert total == offer.price_base_gc + 2 * offer.price_variable_multiplier


def test_upgrade_multiplier_offer_resolves_from_a_base_record():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(
        o for o in (*catalogue.common_items(), *catalogue.rare_items())
        if o.price_upgrade_multiplier is not None
    )
    assert offer.price_gc is None and offer.price_dice is None
    assert resolve_offer_price(offer, 5) is None  # needs the base record price


def test_same_weapon_upgrade_cannot_be_purchased_twice():
    engine, state, port = _pending()
    offer = next(
        row for row in (*_catalogue(state, port).common_items(), *_catalogue(state, port).rare_items())
        if row.price_upgrade_multiplier is not None
    )
    base = next(row for row in state.campaign.inventory if row.stash and port.weapon_hands(row.base_item_id or row.id) is not None)
    price = base.value * offer.price_upgrade_multiplier
    assert engine.buy_weapon_upgrade(offer, base.id, price)[0]
    upgraded = next(row for row in state.campaign.inventory if offer.name in row.special_rules)

    ok, _ = engine.buy_weapon_upgrade(offer, upgraded.id, upgraded.value * offer.price_upgrade_multiplier)

    assert not ok


def test_weapon_upgrade_rejects_a_forged_price():
    engine, state, port = _pending()
    offer = next(
        row for row in (*_catalogue(state, port).common_items(), *_catalogue(state, port).rare_items())
        if row.price_upgrade_multiplier is not None
    )
    base = next(row for row in state.campaign.inventory if row.stash and port.weapon_hands(row.base_item_id or row.id) is not None)

    ok, _ = engine.buy_weapon_upgrade(offer, base.id, -100)

    assert not ok


def test_buy_with_rolled_variable_price_charges_base_plus_dice():
    engine, state, _ = _pending()
    gold_before = engine.projected_gold()
    ok, message = engine.buy_item("blessed_water", 1, 20)  # 10 + 3D6 rolled 10
    assert ok, message
    assert engine.projected_gold() == gold_before - 20


def test_buy_rejects_beyond_the_warband_limit():
    engine, state, _ = _pending()
    trading = engine.port.campaign_catalog().catalogue("trading-post.yaml")
    limit_item = next(
        str(entry.get("item_id")) for entry in trading.get("items") or ()
        if any(r.get("type") == "limit_per_warband" for r in entry.get("restrictions") or ())
    )
    limit = engine.port.trading_post_restriction(limit_item)["limit_per_warband"]
    # Pre-owned copies count towards the limit.
    row = engine._inventory_row(limit_item, name=engine.port.item_name(limit_item) or limit_item, price_gc=1)
    row.owned = int(limit)
    ok, message = engine.buy_item(limit_item, 1, 1)
    assert not ok and "limit" in message.lower()


# ------------------------------------------------------------------- fees


def test_variable_hiring_fee_is_parsed_and_needs_a_roll():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(o for o in catalogue.hired_swords() if o.entry_id.endswith(".ninja"))
    assert offer.fee_gc is None  # not flat
    assert offer.fee_base_gc == 70 and offer.fee_dice == (3, 6)
    assert offer.fee_label == "70+3D6 gc"
    ok, message = engine.hire_hireling(offer)
    assert not ok and "Roll" in message  # the engine never rolls by itself


def test_variable_hiring_fee_charges_base_plus_roll():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(o for o in catalogue.hired_swords() if o.entry_id.endswith(".ninja"))
    engine.post.gold_delta += 200  # cover the fee without touching the KB example
    gold_before = engine.projected_gold()
    ok, message = engine.hire_hireling(offer, fee_roll=12)  # 70 + 3D6 rolled 12
    assert ok, message
    assert engine.projected_gold() == gold_before - 82
    assert any(row.profile_id == offer.profile_id for row in state.campaign.warriors)


def test_variable_hiring_fee_rejects_rolls_below_the_dice_count():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(o for o in catalogue.hired_swords() if o.entry_id.endswith(".ninja"))
    ok, message = engine.hire_hireling(offer, fee_roll=2)  # below 3D6 minimum
    assert not ok


def test_variable_price_item_can_be_bought_during_creation():
    from mordheim_campaign.application.controller import AppController
    from mordheim_campaign.domain.builders import make_draft_state

    controller = AppController()
    controller.replace_state(make_draft_state(controller.port, "lustria-pirates", collection="trollheim"))
    offer = next(row for row in controller.draft_stash_offers() if getattr(row, "price_dice", None) is not None)
    before = controller.state.campaign.draft_treasury
    resolved_price = (offer.price_base_gc or 0) + offer.price_dice[0]
    ok, message = controller.buy_draft_stash_item(offer.item_id, 1, resolved_price)
    assert ok, message
    assert controller.state.campaign.draft_treasury == before - resolved_price


# ----------------------------------------------------------- restrictions


def test_heroes_only_restriction_flags_the_offer_and_blocks_henchmen():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    offer = next(o for o in (*catalogue.common_items(), *catalogue.rare_items()) if o.heroes_only)
    restriction = port.trading_post_restriction(offer.item_id)
    assert restriction["heroes_only"] is True
    hero = next(w for w in state.campaign.warriors if w.kind == "hero")
    henchman_group = next(w for w in state.campaign.warriors if w.kind == "henchman")
    ok, _ = engine.buy_item(offer.item_id, 1, 1)
    assert ok
    ok, message = engine.move_stash_to_warrior(offer.item_id, henchman_group.id)
    assert not ok and "heroes" in message.lower()
    ok, _ = engine.move_stash_to_warrior(offer.item_id, hero.id)
    assert ok


def test_prose_only_restriction_notes_are_carried_as_text():
    engine, state, port = _pending()
    catalogue = _catalogue(state, port)
    noted = [
        o for o in (*catalogue.common_items(), *catalogue.rare_items())
        if o.restriction_notes
    ]
    assert noted  # condition/profile_only notes stay visible to the player
    for offer in noted:
        assert all(isinstance(note, str) and note for note in offer.restriction_notes)


def test_profile_only_restriction_blocks_the_wrong_bearer():
    engine, state, _ = _pending()
    item_id = "reptile_venom"
    row = engine._inventory_row(item_id, name="Reptile Venom", price_gc=5)
    row.owned = row.stash = 1
    wrong_bearer = next(w for w in state.campaign.warriors if "skink" not in w.profile_name.casefold())

    ok, message = engine.move_stash_to_warrior(item_id, wrong_bearer.id)

    assert not ok
    assert "Skink Henchmen" in message

    wrong_bearer.profile_name = "Skink Hero"
    wrong_bearer.profile_id = "skink-hero"
    wrong_bearer.kind = "hero"
    ok, _ = engine.move_stash_to_warrior(item_id, wrong_bearer.id)
    assert not ok


def test_creation_only_offer_is_hidden_after_creation():
    port = KnowledgePort()
    creation = PostBattleCatalogue(port, "mordheim", "shadow-warriors", phase="creation")
    post_battle = PostBattleCatalogue(port, "mordheim", "shadow-warriors", phase="post_battle")

    assert "standard_of_nagarythe" in {offer.item_id for offer in creation.rare_items()}
    assert "standard_of_nagarythe" not in {offer.item_id for offer in post_battle.rare_items()}


# ------------------------------------------------- published bearer (C03a)


def test_published_bearer_decides_the_offering_route_and_a_direct_selection():
    """The printed bearer is read from the entry, not from its prose note.

    ``arcane_candelabrum`` publishes the Sister of Sigmar's profile id, so any
    other warrior is refused with the printed clause and she is not;
    ``lance_not_questing_knight`` publishes the printed denial, so the Questing
    Knight is refused while a Knight Errant is not. Offering an item and
    accepting a direct selection call this same decision.
    """
    port = KnowledgePort()
    assert port.trading_post_restriction("arcane_candelabrum")["profile_ids"] == (
        "hireling.hired-sword.sister-of-sigmar",)
    sister = SimpleNamespace(profile_id="hireling.hired-sword.sister-of-sigmar", kind="hero", skills=[])
    other = SimpleNamespace(profile_id="ogre-treasure-hunter", kind="hero", skills=[])
    assert port.trading_post_bearer_issue(sister, "arcane_candelabrum") is None
    assert "Sister of Sigmar" in port.trading_post_bearer_issue(other, "arcane_candelabrum")

    assert port.trading_post_restriction("lance_not_questing_knight")["excluded_profile_ids"] == (
        "questing-knight",)
    knight = SimpleNamespace(profile_id="questing-knight", kind="hero", skills=[])
    errant = SimpleNamespace(profile_id="knights-errant", kind="hero", skills=[])
    assert port.trading_post_bearer_issue(knight, "lance_not_questing_knight")
    assert port.trading_post_bearer_issue(errant, "lance_not_questing_knight") is None


def test_published_bearer_reaches_the_engine_assignment_route():
    """A published bearer with no legacy literal rule refuses the wrong warrior.

    The example campaign's first warrior is a Sister of Sigmar, never the
    printed bearer of these entries, so the selection is refused before the
    shared stage's facts with the printed clause.
    """
    engine, state, _ = _pending()
    item_id = "angel_wings"  # published bearer: Armen Abbas, no literal guard
    row = engine._inventory_row(item_id, name="Angel Wings", price_gc=1)
    row.owned = row.stash = 1
    warrior = state.campaign.warriors[0]

    ok, message = engine.move_stash_to_warrior(item_id, warrior.id)

    assert not ok
    assert "Armen Abbas" in message


def test_published_kind_bearer_admits_the_printed_kind_and_refuses_the_other():
    """The printed kind is decided from the entry, on the same route.

    ``barbed_whip`` publishes `profile_types: [hero]`, so the assignment route
    refuses the henchman group with the printed clause, while a hero is not
    stopped by the bearer (the weapon still lies outside her own equipment
    access, which is an acquisition limit and not the bearer's decision).
    """
    engine, state, _ = _pending()
    item_id = "barbed_whip"
    row = engine._inventory_row(item_id, name="Barbed Whip", price_gc=1)
    row.owned = row.stash = 4
    hero = next(w for w in state.campaign.warriors if w.kind == "hero")
    henchman = next(w for w in state.campaign.warriors if w.kind == "henchman")

    ok, message = engine.move_stash_to_warrior(item_id, henchman.id)
    assert not ok and "One Marauders of Chaos Hero only" in message

    _, hero_message = engine.move_stash_to_warrior(item_id, hero.id)
    assert "One Marauders of Chaos Hero only" not in hero_message
