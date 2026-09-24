"""Variable prices, variable hiring fees and typed band restrictions.

The KB declares the data structurally already; these tests pin the read side
(``post_battle_catalogue``) and the write side (``post_battle_engine``) over
the example campaign. No KB data is edited.
"""
from __future__ import annotations

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
