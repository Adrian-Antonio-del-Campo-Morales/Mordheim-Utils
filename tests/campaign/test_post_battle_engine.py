"""Post-battle write side: outcomes applied to the campaign and committed.

Every projection is pinned to the KB tables the engine reads (wyrdstone sale
table, exploration shard chart, serious injuries) and to the example
campaign's State #7 (gold 72, wyrdstone 4, 8 models). Rating is derived from
actual roster experience (models × 5 + XP), so the narrative State #7 rating
(183) is not asserted — the roster sums to 85 XP → rating 125.
"""
from __future__ import annotations

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_catalogue import HirelingOffer, PostBattleCatalogue
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.application.post_battle_resolution import PostBattleResolver
from mordheim_campaign.application.state import make_example_state
from mordheim_campaign.persistence import load_campaign, save_campaign


def _pending():
    port = KnowledgePort()
    state = make_example_state(port)
    campaign = state.campaign
    post = campaign.pending_post_battle
    assert post is not None and post.battle_number == 8
    return PostBattleEngine(port, campaign, post), state, port


# ----------------------------------------------------------------- projections


def test_projections_match_the_base_state():
    engine, _, _ = _pending()
    assert engine.projected_gold() == 72
    assert engine.projected_shards() == 4
    assert engine.projected_models() == 8
    assert engine.projected_heroes() == 4
    assert engine.projected_henchmen() == 4
    # Rating is derived: 8 models × 5 + 85 roster XP.
    assert engine.projected_experience() == 85
    assert engine.projected_rating() == 125


def test_projections_follow_roster_and_deltas():
    engine, _, _ = _pending()
    engine.add_xp("matriarch", 1)
    engine.apply_exploration((3, 3, 5, 6))
    assert engine.projected_rating() == 126
    assert engine.projected_experience() == 86
    assert engine.projected_shards() > 4  # exploration added shards


# -------------------------------------------------------------- sale of wyrdstone


def test_wyrdstone_sale_value_comes_from_the_kb_table():
    engine, _, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    # State #7 has 8 models -> the 7-9 size band; the table rows pin these.
    assert resolver.wyrdstone_sale_value(1, 8) == 35
    assert resolver.wyrdstone_sale_value(2, 8) == 50
    assert resolver.wyrdstone_sale_value(1, 4) == 40


def test_sell_wyrdstone_applies_once():
    engine, _, post = _pending()
    ok, _ = engine.sell_wyrdstone(2)
    assert ok
    assert engine.projected_gold() == 72 + 50
    assert engine.projected_shards() == 4 - 2
    # Selling is a once-per-sequence action.
    ok, message = engine.sell_wyrdstone(1)
    assert not ok and "once per post-battle" in message


def test_sell_wyrdstone_rejects_more_than_hoard():
    engine, _, _ = _pending()
    ok, message = engine.sell_wyrdstone(99)
    assert not ok and "Only 4 shard(s)" in message


# -------------------------------------------------------------------- injuries


def test_injury_removes_one_henchman_member_then_the_row():
    engine, state, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    group = next(row for row in state.campaign.warriors if row.kind == "henchman" and row.quantity > 1)
    outcome = resolver.resolve_henchman_serious_injury(1)  # Removed
    ok, _ = engine.apply_serious_injury(group.id, outcome)
    assert ok
    assert group.quantity == 1
    ok, _ = engine.apply_serious_injury(group.id, outcome)
    assert ok
    assert group not in state.campaign.warriors


def test_injury_dead_hero_leaves_the_roster():
    engine, state, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    outcome = resolver.resolve_hero_serious_injury(11)  # Dead
    ok, _ = engine.apply_serious_injury(hero.id, outcome)
    assert ok
    assert hero not in state.campaign.warriors
    assert engine.projected_heroes() == 3


def test_injury_characteristic_modifier_applies():
    engine, state, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    outcome = resolver.resolve_hero_serious_injury(22)  # Leg Wound: M -1
    ok, _ = engine.apply_serious_injury(hero.id, outcome)
    assert ok
    assert hero.stat_modifiers.get("M") == -1


def test_full_recovery_leaves_roster_untouched():
    engine, state, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    outcome = resolver.resolve_hero_serious_injury(46)  # Full Recovery
    ok, _ = engine.apply_serious_injury(hero.id, outcome)
    assert ok
    assert hero in state.campaign.warriors
    assert hero.condition is None


# ----------------------------------------------------------------- experience


def test_add_xp_increases_rating():
    engine, _, _ = _pending()
    ok, _ = engine.add_xp("matriarch", 3)
    assert ok
    assert engine.projected_experience() == 88
    assert engine.projected_rating() == 128


# ----------------------------------------------------------------- recruitment


def test_recruit_band_profile_deducts_gold_and_adds_models():
    engine, state, _ = _pending()
    profiles = engine.port.profiles(state.campaign.collection, state.campaign.band_id, kind="henchman")
    profile = next(p for p in profiles if p.cost > 0)
    ok, _ = engine.recruit_band_profile(profile.profile_id, 1)
    assert ok
    assert engine.projected_models() == 9
    assert engine.projected_gold() == 72 - profile.cost


def test_recruit_rejected_without_gold_or_over_cap():
    engine, _, _ = _pending()
    campaign = engine.campaign
    profiles = engine.port.profiles(campaign.collection, campaign.band_id, kind="henchman")
    profile = min(profiles, key=lambda p: p.cost)
    for _ in range(50):
        engine.recruit_band_profile(profile.profile_id, 1)
    ok, message = engine.recruit_band_profile(profile.profile_id, 1)
    assert not ok
    assert ("gold" in message) or ("models" in message)


def test_hire_hireling_from_catalogue():
    engine, state, port = _pending()
    catalogue = PostBattleCatalogue(port, state.campaign.collection, state.campaign.band_id)
    offer = next(
        (entry for entry in catalogue.hired_swords()
         if entry.eligibility == "eligible" and entry.fee_gc is not None),
        None,
    )
    assert offer is not None
    models = engine.projected_models()
    gold = engine.projected_gold()
    ok, _ = engine.hire_hireling(offer)
    assert ok
    assert engine.projected_models() == models + 1
    assert engine.projected_gold() == gold - offer.fee_gc
    hired = next(row for row in state.campaign.warriors if row.profile_id == offer.profile_id)
    assert hired.stats["M"] >= 1  # characteristics copied from the KB profile


def test_hire_conditional_requires_acceptance_roll():
    engine, state, _ = _pending()
    offer = HirelingOffer(
        entry_id="campaign.hireling.william",
        profile_id="hireling.dramatis.william-schakestange-master-bard",
        kind="dramatis",
        name="William Schäkestange, Master Bard",
        availability_label="",
        fee_label=None,
        upkeep_label=None,
        eligibility="conditional",
        fee_gc=0,
        roll_ge=4,
    )
    ok, message = engine.hire_hireling(offer, acceptance_roll=None)
    assert not ok and "acceptance roll" in message
    ok, message = engine.hire_hireling(offer, acceptance_roll=3)
    assert not ok and "failed" in message
    models = engine.projected_models()
    ok, _ = engine.hire_hireling(offer, acceptance_roll=5)
    assert ok
    assert engine.projected_models() == models + 1


def test_employed_hired_sword_on_the_roster_blocks_its_counterpart_in_content():
    """Integration: a hireling row the engine writes feeds the eligibility context."""
    from mordheim_campaign.application.controller import AppController

    controller = AppController()
    controller.new_campaign("Mercs", "mercenaries")
    campaign = controller.state.campaign
    engine = PostBattleEngine(controller.port, campaign, None)
    offer = next(o for o in controller.post_battle_content().hired_swords()
                 if o.profile_id == "hireling.hired-sword.highwayman")
    row = engine._hireling_warrior(offer)  # exactly what a successful hire appends
    campaign.warriors.append(row)
    content = controller.post_battle_content()
    assert not any(
        o.profile_id == "hireling.hired-sword.roadwarden" for o in content.hired_swords()
    )
    assert any(
        o.profile_id == "hireling.hired-sword.highwayman" for o in content.hired_swords()
    )


def test_dramatis_catalogue_marks_william_conditional_for_other_good_bands():
    port = KnowledgePort()
    catalogue = PostBattleCatalogue(port, "mordheim", "bretonnian-knights")
    william = next(o for o in catalogue.dramatis_personae() if "william" in o.profile_id)
    assert william.eligibility == "conditional"
    assert william.roll_ge == 4


# ------------------------------------------------------------------------ items


def test_buy_assign_sell_round_trip():
    engine, state, port = _pending()
    catalogue = PostBattleCatalogue(port, state.campaign.collection, state.campaign.band_id)
    offer = next(o for o in catalogue.common_items() if o.price_gc is not None)
    gold = engine.projected_gold()
    ok, _ = engine.buy_item(offer.item_id, 2, offer.price_gc)
    assert ok
    assert engine.projected_gold() == gold - 2 * offer.price_gc
    row = next(item for item in state.campaign.inventory if item.id == offer.item_id)
    assert row.stash == 2 and row.owned == 2

    warrior = state.campaign.warriors[0]
    ok, _ = engine.assign_item(offer.item_id, warrior.id)
    assert ok
    assert row.stash == 1 and row.equipped == 1
    assert offer.name in warrior.equipment

    ok, _ = engine.sell_item(offer.item_id, 1)
    assert ok
    assert row.stash == 0 and row.owned == 1
    assert engine.projected_gold() == gold - 2 * offer.price_gc + offer.price_gc // 2


def test_buy_item_rejected_when_funds_run_out():
    engine, state, port = _pending()
    catalogue = PostBattleCatalogue(port, state.campaign.collection, state.campaign.band_id)
    offer = next(o for o in catalogue.common_items() if o.price_gc is not None and o.price_gc > 0)
    ok, message = engine.buy_item(offer.item_id, 100, offer.price_gc)
    assert not ok and "Not enough gold" in message


# --------------------------------------------------------------------- commit


def test_commit_creates_the_next_state():
    engine, state, _ = _pending()
    engine.add_xp("matriarch", 1)
    engine.sell_wyrdstone(1)
    engine.post.completed_steps = set(range(8))
    ok, _ = engine.commit()
    assert ok
    snapshot = state.campaign.state(8)
    assert snapshot.gold == 72 + 35
    assert snapshot.wyrdstone == 3
    assert snapshot.rating == 126  # 8 × 5 + 86 roster XP
    assert snapshot.experience == 86
    assert snapshot.models == 8
    assert state.campaign.current_state_number == 8
    assert state.campaign.pending_post_battle is None
    assert engine.post.complete


def test_commit_requires_all_eight_actions():
    engine, _, _ = _pending()
    ok, message = engine.commit()
    assert not ok and "8 actions" in message
    assert engine.post is not None and not engine.post.complete


def test_pending_deltas_survive_a_save_load_round_trip(tmp_path):
    engine, state, _ = _pending()
    engine.sell_wyrdstone(2)
    engine.apply_veteran_pool(7)
    engine.add_xp("matriarch", 1)
    path = save_campaign(tmp_path / "mid.mordheim", state)
    reloaded = load_campaign(path)
    post = reloaded.campaign.pending_post_battle
    assert post is not None
    assert post.gold_delta == 50
    assert post.wyrdstone_sold == 2
    assert post.sale_resolved
    assert post.veteran_pool == 7


def test_legacy_files_without_deltas_load_with_zero_totals(tmp_path):
    engine, state, _ = _pending()
    state.campaign.post_battle(8).complete = False
    path = save_campaign(tmp_path / "legacy.mordheim", state)
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    for post in payload["campaign"]["post_battles"]:
        for key in ("gold_delta", "wyrdstone_delta", "wyrdstone_sold", "veteran_pool", "sale_resolved"):
            post.pop(key, None)
    path.write_text(json.dumps(payload), encoding="utf-8")
    reloaded = load_campaign(path)
    post = reloaded.campaign.pending_post_battle
    assert post.gold_delta == 0 and post.wyrdstone_sold == 0 and post.veteran_pool == 0
    assert not post.sale_resolved
