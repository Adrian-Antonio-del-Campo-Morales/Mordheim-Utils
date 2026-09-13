"""Post-battle write side: outcomes applied to the campaign and committed.

Every projection is pinned to the KB tables the engine reads (wyrdstone sale
table, exploration shard chart, serious injuries) and to the example
campaign's State #7 (gold 72, wyrdstone 4, 8 models). Rating is derived from
actual roster experience (models × 5 + XP), so the narrative State #7 rating
(183) is not asserted — the roster sums to 85 XP → rating 125.
"""
from __future__ import annotations

from dataclasses import replace

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_catalogue import HirelingOffer, PostBattleCatalogue
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.application.post_battle_resolution import PostBattleResolver
from mordheim_campaign.domain.models import EquipmentEntryVM
from mordheim_campaign.domain.builders import make_example_state
from mordheim_campaign.persistence import load_campaign, save_campaign
from mordheim_campaign.ui.panels.warrior_card import effective_stat, injury_lines


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


def test_exploration_eligibility_subtracts_only_out_of_action_heroes():
    engine, state, _ = _pending()
    battle = state.campaign.battle(8)
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    henchmen = next(row for row in state.campaign.warriors if row.kind == "henchman")

    battle.out_of_action_ids = [henchmen.id, henchmen.id]
    assert engine.eligible_exploration_heroes(battle) == engine.projected_heroes()

    battle.out_of_action_ids.append(hero.id)
    assert engine.eligible_exploration_heroes(battle) == engine.projected_heroes() - 1


def test_projections_follow_roster_and_deltas():
    engine, _, _ = _pending()
    engine.add_xp("matriarch", 1)
    engine.apply_exploration((3, 3, 5, 6))
    assert engine.projected_rating() == 126
    assert engine.projected_experience() == 86
    assert engine.projected_shards() > 4  # exploration added shards


def test_exploration_variable_grants_apply_and_resume_the_reward():
    engine, state, _ = _pending()
    post = engine.post
    assert post is not None
    post.pending_follow_ups.clear()
    stock = state.campaign.inventory[0]
    starting_gold = engine.projected_gold()
    starting_owned = stock.owned
    starting_stash = stock.stash
    post.pending_follow_ups.append({
        "type": "exploration_followup",
        "queue": [{
            "type": "grant",
            "recipient": "warband",
            "resources": {"gold_crowns": {"kind": "dice", "dice": {"count": 2, "sides": 6}}},
            "items": [{"item_id": stock.id, "quantity": {"kind": "dice", "dice": {"count": 1, "sides": 3}}}],
            "note": "special reward complete",
        }],
        "messages": [],
    })

    pending = engine.exploration_followup_pending()
    assert pending is not None and pending["resource"] == "gold_crowns"
    ok, _ = engine.advance_exploration_followup(roll=7)
    assert ok and engine.projected_gold() == starting_gold + 7

    pending = engine.exploration_followup_pending()
    assert pending is not None and pending["resource"] == f"item:{stock.id}"
    ok, message = engine.advance_exploration_followup(roll=2)
    assert ok
    assert stock.owned == starting_owned + 2
    assert stock.stash == starting_stash + 2
    assert "special reward complete" in message
    assert engine.exploration_followup_pending() is None


def test_exploration_applies_dice_multiplier_and_offset():
    engine, _, _ = _pending()
    engine.post.pending_follow_ups[:] = [{
        "type": "exploration_followup", "messages": [],
        "queue": [{"type": "grant", "recipient": "warband", "resources": {
            "gold_crowns": {"kind": "dice", "dice": {"count": 1, "sides": 6}, "multiplier": 10},
            "wyrdstone_fragments": {"kind": "dice", "dice": {"count": 1, "sides": 6}, "offset": 1},
        }}],
    }]
    gold = engine.projected_gold()
    shards = engine.projected_shards()
    engine.exploration_followup_pending()
    engine.advance_exploration_followup(roll=4)
    engine.advance_exploration_followup(roll=2)
    assert engine.projected_gold() == gold + 40
    assert engine.projected_shards() == shards + 3


def test_exploration_single_hero_reward_requires_and_uses_selection():
    engine, state, _ = _pending()
    heroes = [warrior for warrior in state.campaign.warriors if warrior.kind == "hero"]
    before = {hero.id: hero.experience for hero in heroes}
    engine.post.pending_follow_ups[:] = [{
        "type": "exploration_followup", "messages": [],
        "queue": [{"type": "grant", "recipient": "hero",
                   "resources": {"experience": {"kind": "fixed", "value": 2}}}],
    }]
    assert engine.exploration_followup_pending()["kind"] == "choose_hero"
    engine.advance_exploration_followup(hero_id=heroes[-1].id)
    assert heroes[-1].experience == before[heroes[-1].id] + 2
    assert all(hero.experience == before[hero.id] for hero in heroes[:-1])


def test_exploration_option_applies_selected_branch():
    engine, _, _ = _pending()
    start = engine.projected_gold()
    engine.post.pending_follow_ups[:] = [{
        "type": "exploration_followup", "messages": [],
        "queue": [{"type": "choose_option", "options": [
            {"id": "sell", "label": "Sell", "then": [{"type": "grant", "recipient": "warband",
             "resources": {"gold_crowns": {"kind": "fixed", "value": 100}}}]},
        ]}],
    }]
    assert engine.exploration_followup_pending()["kind"] == "choose_option"
    engine.advance_exploration_followup(option_id="sell")
    assert engine.projected_gold() == start + 100


def test_returning_a_favour_adds_the_selected_hired_sword_for_free():
    engine, state, _ = _pending()
    engine.post.pending_follow_ups.clear()
    before = len(state.campaign.warriors)
    ok, _ = engine.apply_exploration((6, 6, 6))
    assert ok
    pending = engine.exploration_followup_pending()
    assert pending is not None and pending["kind"] == "choose_option"
    ok, _ = engine.advance_exploration_followup(option_id=pending["options"][0]["id"])
    assert ok and len(state.campaign.warriors) == before + 1
    assert state.campaign.warriors[-1].kind == "hireling"
    assert any("Returning a Favour" in rule for rule in state.campaign.warriors[-1].special_rules)


def test_hired_sword_upkeep_must_be_paid_or_the_hireling_leaves():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    hireling = replace(hero, id="upkeep-hireling", name="Test Hireling", kind="hireling",
                       upkeep_resources=[("gold_crowns", 15)], special_rules=["Returning a Favour: free"])
    state.campaign.warriors.append(hireling)
    engine.post.pending_follow_ups.append({
        "id": "upkeep:test", "step": 6, "type": "hireling_upkeep",
        "warrior_id": hireling.id, "costs": [["gold_crowns", 15]],
    })
    before = engine.projected_gold()
    ok, _ = engine.resolve_hireling_upkeep("upkeep:test", pay=True)
    assert ok and engine.projected_gold() == before - 15
    assert not any(rule.startswith("Returning a Favour:") for rule in hireling.special_rules)


def test_unique_magical_artefact_remains_unique_after_bearer_is_lost():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    reward = {"type": "grant_special_item", "recipient": "hero", "item_id": "magical_artefact.test",
              "name": "Test Artefact", "text": "A unique effect"}
    engine.post.pending_follow_ups[:] = [{"type": "exploration_followup", "messages": [], "queue": [reward]}]
    assert engine.exploration_followup_pending()["kind"] == "choose_hero"
    assert engine.advance_exploration_followup(hero_id=hero.id)[0]
    assert "magical_artefact.test" in state.campaign.unique_reward_ids
    state.campaign.warriors.remove(hero)
    engine.post.pending_follow_ups[:] = [{"type": "exploration_followup", "messages": [], "queue": [reward]}]
    other = next(row for row in state.campaign.warriors if row.kind == "hero")
    engine.exploration_followup_pending()
    engine.advance_exploration_followup(hero_id=other.id)
    assert not any(item.item_id == "magical_artefact.test" for item in other.equipment)


def test_gromril_reward_is_one_compound_transferable_item():
    engine, state, _ = _pending()
    engine.post.pending_follow_ups[:] = [{"type": "exploration_followup", "messages": [], "queue": [{
        "type": "grant_compound_item", "reward_id": "scenario_reward.gromril_axe",
        "base_item_id": "axe", "name": "Gromril Axe", "category": "Weapon",
        "rules": ["Gromril weapon"],
    }]}]
    assert engine.exploration_followup_pending() is None
    item = next(row for row in state.campaign.inventory if row.id == "scenario_reward.gromril_axe")
    assert item.stash == 1 and item.base_item_id == "axe" and item.special_rules == ["Gromril weapon"]


def test_prisoner_choice_excludes_non_roster_and_intrinsic_attack_groups():
    engine, state, _ = _pending()
    group = next(row for row in state.campaign.warriors if row.kind == "henchman")
    animal = replace(group, id="animal-group", name="Warhounds", profile_id="missing-animal-profile")
    state.campaign.warriors.append(animal)
    engine.post.pending_follow_ups[:] = [{"type": "exploration_followup", "messages": [],
                                          "queue": [{"type": "choose_henchman_group"}]}]
    pending = engine.exploration_followup_pending()
    ids = {row["id"] for row in pending["options"]}
    assert group.id in ids and animal.id not in ids


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
    assert effective_stat(hero, "M") == hero.stats["M"] - 1
    assert "Injury: Leg Wound · -1 M" in injury_lines(hero)


def test_full_recovery_leaves_roster_untouched():
    engine, state, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    outcome = resolver.resolve_hero_serious_injury(46)  # Full Recovery
    ok, _ = engine.apply_serious_injury(hero.id, outcome)
    assert ok
    assert hero in state.campaign.warriors
    assert hero.condition is None


def test_miss_games_injury_creates_a_persistent_absence_counter():
    engine, state, _ = _pending()
    resolver = PostBattleResolver(engine.port)
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    deep_wound = resolver.resolve_hero_serious_injury(35)
    fixed_effects = tuple(
        {**effect, "games": {"kind": "fixed", "value": 2}}
        if effect.get("type") == "warrior.miss_games" else effect
        for effect in deep_wound.effects_raw
    )

    ok, message = engine.apply_serious_injury(hero.id, replace(deep_wound, effects_raw=fixed_effects))

    assert ok, message
    assert hero.games_to_miss == 2
    assert hero.absence_reason == "Deep Wound"


def _sold_to_pits(engine, hero):
    outcome = PostBattleResolver(engine.port).resolve_hero_serious_injury(65)
    ok, message = engine.apply_serious_injury(hero.id, outcome)
    assert ok, message
    return next(row for row in engine.post.pending_follow_ups if row.get("encounter_id") == "campaign.encounter.sold-to-the-pits")


def test_sold_to_pits_win_grants_gold_and_experience():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    followup = _sold_to_pits(engine, hero)
    gold = engine.post.gold_delta
    experience = hero.experience

    ok, message = engine.resolve_sold_to_pits(followup["id"], won=True)

    assert ok, message
    assert engine.post.gold_delta == gold + 50
    assert hero.experience == experience + 2
    assert followup not in engine.post.pending_follow_ups


def test_sold_to_pits_loss_applies_injury_and_discards_weapons_and_armour():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    followup = _sold_to_pits(engine, hero)
    hero.equipment.append(EquipmentEntryVM("lucky_charm", "Lucky Charm", 1))
    before_movement = hero.stat_modifiers.get("M", 0)

    ok, message = engine.resolve_sold_to_pits(followup["id"], won=False, injury_roll=22)

    assert ok, message
    assert hero.stat_modifiers["M"] == before_movement - 1
    assert all(
        next((row.category for row in state.campaign.inventory if row.id == item.item_id), "").casefold() not in {"weapon", "armour"}
        for item in hero.equipment
    )
    assert any(item.item_id == "lucky_charm" for item in hero.equipment)
    assert followup not in engine.post.pending_follow_ups


def test_captured_can_be_ransomed_or_permanently_lost():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    captured = PostBattleResolver(engine.port).resolve_hero_serious_injury(61)
    ok, message = engine.apply_serious_injury(hero.id, captured)
    assert ok, message
    followup = next(row for row in engine.post.pending_follow_ups if row.get("type") == "prisoner")
    gold = engine.post.gold_delta

    ok, message = engine.resolve_captured(followup["id"], resolution="ransom", ransom=12)
    assert ok, message
    assert hero in state.campaign.warriors
    assert engine.post.gold_delta == gold - 12

    other = next(row for row in state.campaign.warriors if row.kind == "hero" and row is not hero)
    engine.apply_serious_injury(other.id, captured)
    followup = next(row for row in engine.post.pending_follow_ups if row.get("type") == "prisoner")
    ok, message = engine.resolve_captured(followup["id"], resolution="lost")
    assert ok, message
    assert other not in state.campaign.warriors
    assert not other.equipment


def test_bitter_enmity_records_the_selected_target():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    resolver = PostBattleResolver(engine.port)
    hatred = resolver.resolve_injury_subtable("hero", resolver.resolve_hero_serious_injury(56).result_id, 4)
    assert hatred is not None
    engine.apply_serious_injury(hero.id, hatred)
    followup = next(row for row in engine.post.pending_follow_ups if row.get("type") == "relationship")

    ok, message = engine.resolve_hatred_target(followup["id"], "Reiklander Captain")

    assert ok, message
    assert hero.hatreds == ["Reiklander Captain"]
    assert followup not in engine.post.pending_follow_ups


def test_old_battle_wound_becomes_a_persistent_pre_battle_check():
    engine, state, _ = _pending()
    hero = next(row for row in state.campaign.warriors if row.kind == "hero")
    outcome = PostBattleResolver(engine.port).resolve_hero_serious_injury(32)

    ok, message = engine.apply_serious_injury(hero.id, outcome)

    assert ok, message
    assert hero.battle_start_checks[0]["check_id"] == "campaign.check.old-battle-wound"
    assert not any(row.get("type") == "battle_start_check" for row in engine.post.pending_follow_ups)


# ----------------------------------------------------------------- experience


def test_battle_experience_is_applied_once_to_current_survivors():
    engine, state, _ = _pending()
    engine.post.experience_applied = False
    before = {warrior.id: warrior.experience for warrior in state.campaign.warriors}
    amount = state.campaign.battle(8).xp_delta
    assert engine.apply_battle_experience()[0]
    assert all(warrior.experience == before[warrior.id] + amount for warrior in state.campaign.warriors)
    assert engine.apply_battle_experience()[0]
    assert all(warrior.experience == before[warrior.id] + amount for warrior in state.campaign.warriors)


def test_underdog_bonus_is_added_only_for_participating_warriors():
    engine, state, _ = _pending()
    engine.post.experience_applied = False
    battle = state.campaign.battle(8)
    battle.rating_before = 100
    battle.opponent_rating = 201
    battle.xp_delta = 1
    battle.xp_awards = {}
    absentee = state.campaign.warriors[0]
    battle.absentees = [{"id": absentee.id}]
    before = {warrior.id: warrior.experience for warrior in state.campaign.warriors}

    ok, message = engine.apply_battle_experience()

    assert ok, message
    assert absentee.experience == before[absentee.id]
    for warrior in state.campaign.warriors:
        if warrior.id == absentee.id:
            continue
        expected = before[warrior.id] + (4 if engine.port.can_gain_experience(state.campaign.band_id, warrior.profile_id) else 0)
        assert warrior.experience == expected


def test_add_xp_increases_rating():
    engine, _, _ = _pending()
    ok, _ = engine.add_xp("matriarch", 3)
    assert ok
    assert engine.projected_experience() == 88
    assert engine.projected_rating() == 128


def test_existing_group_recruit_uses_veteran_xp_and_leaves_equipment_pending():
    engine, state, _ = _pending()
    group = next(row for row in state.campaign.warriors if row.id == "sisters")
    engine.apply_veteran_pool(group.experience)
    gold = engine.projected_gold()

    ok, _ = engine.add_member_to_group(group.id)

    assert ok and group.quantity == 3
    assert engine.post.veteran_pool == 0
    # KB veteran_availability: joining recruit spends the group's current
    # experience from the pool AND 2 gc per experience point.
    assert engine.projected_gold() == gold - group.cost - 2 * group.experience
    assert all(item.quantity == 2 for item in group.equipment)
    obligations = engine.post.equipment_obligations
    assert obligations and all(row["warrior_id"] == group.id for row in obligations)


def test_matching_group_equipment_settles_obligation_and_commit_blocks_until_then():
    engine, state, _ = _pending()
    group = next(row for row in state.campaign.warriors if row.id == "sisters")
    engine.apply_veteran_pool(group.experience)
    assert engine.add_member_to_group(group.id)[0]
    obligation = engine.post.equipment_obligations[0]
    stock = next(row for row in state.campaign.inventory if row.id == obligation["item_id"])
    stock.owned += 1; stock.stash += 1

    assert engine.move_stash_to_warrior(stock.id, group.id)[0]
    assert not any(row["item_id"] == stock.id for row in engine.post.equipment_obligations)


def test_dismissing_new_group_member_clears_now_unneeded_obligations():
    engine, state, _ = _pending()
    group = next(row for row in state.campaign.warriors if row.id == "sisters")
    engine.apply_veteran_pool(group.experience)
    assert engine.add_member_to_group(group.id)[0]
    assert engine.post.equipment_obligations

    assert engine.dismiss_warrior(group.id, one_member=True)[0]

    assert not engine.post.equipment_obligations


def test_dismissing_one_group_member_returns_one_equipment_set_to_stash():
    engine, state, _ = _pending()
    group = next(row for row in state.campaign.warriors if row.id == "sisters")
    hammer = next(row for row in state.campaign.inventory if row.id == "hammer")
    buckler = next(row for row in state.campaign.inventory if row.id == "buckler")

    ok, _ = engine.dismiss_warrior(group.id, one_member=True)

    assert ok and group.quantity == 1
    assert (hammer.stash, buckler.stash) == (1, 1)
    assert all(item.quantity == 1 for item in group.equipment)


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
    row = engine.hireling_warrior(offer)  # exactly what a successful hire appends
    campaign.warriors.append(row)
    content = controller.post_battle_content()
    assert not any(
        o.profile_id == "hireling.hired-sword.roadwarden" for o in content.hired_swords()
    )
    assert not any(
        o.profile_id == "hireling.hired-sword.highwayman" for o in content.hired_swords()
    )


def test_hired_swords_use_separate_capacity_income_and_rating_counts():
    engine, state, _ = _pending()
    campaign = state.campaign
    henchmen = next(row for row in campaign.warriors if row.kind == "henchman")
    henchmen.quantity += campaign.maximum_models - engine.projected_warband_members()
    offer = HirelingOffer(
        entry_id="campaign.hireling.ogre",
        profile_id="hireling.hired-sword.ogre-bodyguard",
        kind="hired-sword", name="Ogre Bodyguard",
        availability_label="", fee_label="0 gc", upkeep_label="", fee_gc=0,
    )
    models = engine.projected_models()
    rating = engine.projected_rating()

    ok, message = engine.hire_hireling(offer)

    assert ok, message
    assert engine.projected_warband_members() == campaign.maximum_models
    assert engine.projected_models() == models + 1
    assert engine.projected_rating() == rating + 25
    ok, message = engine.hire_hireling(offer)
    assert not ok and "Only one" in message


def test_halfling_scout_increases_only_the_own_member_limit():
    engine, state, _ = _pending()
    offer = HirelingOffer(
        entry_id="campaign.hireling.halfling",
        profile_id="hireling.hired-sword.halfling-scout",
        kind="hired-sword", name="Halfling Scout",
        availability_label="", fee_label="0 gc", upkeep_label="", fee_gc=0,
    )
    row = engine.hireling_warrior(offer)
    assert row is not None
    state.campaign.warriors.append(row)
    assert engine.effective_maximum_models() == state.campaign.maximum_models + 1


def test_losing_capacity_modifier_blocks_commit_until_roster_is_legal():
    engine, state, _ = _pending()
    campaign = state.campaign
    post = engine.post
    assert post is not None
    offer = HirelingOffer(
        entry_id="campaign.hireling.halfling",
        profile_id="hireling.hired-sword.halfling-scout",
        kind="hired-sword", name="Halfling Scout",
        availability_label="", fee_label="0 gc", upkeep_label="", fee_gc=0,
    )
    scout = engine.hireling_warrior(offer)
    assert scout is not None
    campaign.warriors.append(scout)
    group = next(row for row in campaign.warriors if row.kind == "henchman")
    group.quantity += engine.effective_maximum_models() - engine.projected_warband_members()
    assert engine.dismiss_warrior(scout.id)[0]
    post.completed_steps = set(range(8))

    ok, message = engine.commit()

    assert not ok
    assert "dismiss members" in message


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
    offer = next(o for o in catalogue.common_items() if o.item_id == "lantern")
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
    assert any(entry.item_id == offer.item_id for entry in warrior.equipment)

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


def test_rare_purchase_keeps_its_inventory_marker():
    engine, state, port = _pending()
    catalogue = PostBattleCatalogue(port, state.campaign.collection, state.campaign.band_id)
    offer = next(o for o in catalogue.rare_items() if o.price_gc is not None and o.price_gc <= engine.projected_gold())

    ok, _ = engine.buy_item(offer.item_id, 1, offer.price_gc, category=offer.category, rarity=offer.rarity)

    row = next(item for item in state.campaign.inventory if item.id == offer.item_id)
    assert ok
    assert row.stash == 1
    assert row.rarity == f"Rare {offer.rarity}"


# --------------------------------------------------------------------- commit


def test_commit_creates_the_next_state():
    engine, state, _ = _pending()
    engine.add_xp("matriarch", 1)
    assert engine.resolve_pending_advance("matriarch", 8, subroll=2)[0]
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
