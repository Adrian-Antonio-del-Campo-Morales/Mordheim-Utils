"""Battle creation: real scenarios, opponents, XP and casualties.

``record_battle`` replaces the example narrative: every Battle node is
recorded from table facts, snapshots the pre-battle rating/models and opens
the pending PostBattleVM the eight-step sequence then resolves. The example
campaign ships with Post-Battle #8 pending, so tests close it first.
"""
from __future__ import annotations

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import make_example_state
from mordheim_campaign.persistence import load_campaign, save_campaign


def _settled() -> AppController:
    """Example campaign with no pending post-battle, ready for battle #9."""
    controller = AppController()
    controller.replace_state(make_example_state(controller.port))
    controller.state.campaign.post_battle(8).complete = True
    return controller


def test_scenario_options_come_from_the_kb():
    controller = _settled()
    options = controller.scenario_options()
    ids = {scenario_id for scenario_id, _name, _mode in options}
    assert "scenario.skirmish" in ids and "scenario.defend-the-find" in ids
    modes = {mode for _sid, _name, mode in options}
    assert "1v1" in modes


def test_record_battle_creates_real_nodes():
    controller = _settled()
    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish",
        scenario_name="Skirmish",
        opponent="Reiklanders",
        result="Victory",
        xp_delta=1,
        casualties=0,
    )
    assert ok, message
    campaign = controller.state.campaign
    battle = campaign.battle(9)  # example history ends at battle 8
    assert battle.scenario == "Skirmish" and battle.opponent == "Reiklanders"
    assert battle.result == "Victory" and battle.xp_delta == 1
    assert battle.rating_before == 183 and battle.models_before == 8  # State #7 snapshot
    assert battle.date  # recorded today
    post = campaign.post_battle(9)
    assert post.battle_number == 9 and not post.complete
    assert campaign.pending_post_battle is post
    # The view jumped to the recorded battle.
    assert controller.state.selected_moment == "battle:9"


def test_record_battle_blocks_while_a_post_battle_is_pending():
    controller = _settled()
    ok, _ = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="X", result="Victory", xp_delta=1, casualties=0,
    )
    assert ok
    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Y", result="Defeat", xp_delta=1, casualties=1,
    )
    assert not ok and "pending" in message


def test_record_battle_validates_scenario_and_result():
    controller = _settled()
    ok, message = controller.record_battle(
        scenario_id="scenario.not-real", scenario_name="Ghost",
        opponent="X", result="Victory", xp_delta=1, casualties=0,
    )
    assert not ok and "Unknown scenario" in message
    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="X", result="Flawless", xp_delta=1, casualties=0,
    )
    assert not ok and "Victory, Defeat or Draw" in message


def test_committed_post_battle_unblocks_the_next_battle():
    controller = _settled()
    controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Cultists", result="Victory", xp_delta=2, casualties=1,
    )
    engine = controller.post_battle_engine()
    engine.post.completed_steps = set(range(8))
    ok, _ = engine.commit()
    assert ok
    assert controller.state.campaign.pending_post_battle is None
    ok, message = controller.record_battle(
        scenario_id="scenario.wyrdstone-hunt", scenario_name="Wyrdstone Hunt",
        opponent="Skaven", result="Defeat", xp_delta=1, casualties=2,
    )
    assert ok, message
    assert controller.state.campaign.battles[-1].number == 10


def test_recorded_battle_survives_save_load(tmp_path):
    controller = _settled()
    controller.record_battle(
        scenario_id="scenario.hidden-treasure", scenario_name="Hidden Treasure",
        opponent="Beastmen", result="Draw", xp_delta=3, casualties=1,
        opponent_rating=150, notes="Near the ruined bell tower.",
    )
    path = save_campaign(tmp_path / "b.mordheim", controller.state)
    reloaded = load_campaign(path)
    battle = reloaded.campaign.battle(9)
    assert battle.scenario == "Hidden Treasure" and battle.result == "Draw"
    assert battle.opponent_rating == 150 and battle.notes.startswith("Near")
    assert reloaded.campaign.pending_post_battle is not None
    assert reloaded.campaign.pending_post_battle.battle_number == 9


def test_unavailable_warrior_is_excluded_and_one_missed_game_is_consumed(tmp_path):
    controller = _settled()
    campaign = controller.state.campaign
    warrior = campaign.warriors[0]
    warrior.games_to_miss = 2
    warrior.absence_reason = "Deep Wound"

    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Undead", result="Defeat", xp_delta=1, casualties=0,
    )

    assert ok, message
    battle = campaign.battle(9)
    assert warrior.id not in {row["id"] for row in battle.participants}
    assert battle.absentees == [{
        "id": warrior.id, "name": warrior.name, "kind": warrior.kind,
        "quantity": warrior.quantity, "reason": "Deep Wound", "remaining_before": 2,
    }]
    assert battle.models_before == 7
    assert warrior.games_to_miss == 1

    restored = load_campaign(save_campaign(tmp_path / "absence.mordheim", controller.state))
    saved = next(row for row in restored.campaign.warriors if row.id == warrior.id)
    assert saved.games_to_miss == 1 and saved.absence_reason == "Deep Wound"
    assert restored.campaign.battle(9).absentees[0]["id"] == warrior.id


def test_unavailable_warrior_cannot_receive_battle_results():
    controller = _settled()
    warrior = controller.state.campaign.warriors[0]
    warrior.games_to_miss = 1

    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Undead", result="Defeat", xp_delta=1, casualties=1,
        out_of_action_ids=[warrior.id], xp_awards={warrior.id: 1},
    )

    assert not ok
    assert "Unavailable" in message
    assert warrior.games_to_miss == 1


def test_old_battle_wound_check_controls_participation_without_persistent_counter():
    controller = _settled()
    warrior = controller.state.campaign.warriors[0]
    warrior.battle_start_checks = [{
        "check_id": "campaign.check.old-battle-wound",
        "dice": {"count": 1, "sides": 6},
        "failure_when": {"min": 1, "max": 1},
        "on_failure": [{"type": "warrior.miss_games", "games": {"kind": "fixed", "value": 1}}],
    }]

    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Skaven", result="Draw", xp_delta=1, casualties=0,
    )
    assert not ok and "pre-battle" in message

    ok, message = controller.resolve_battle_start_check(warrior.id, "campaign.check.old-battle-wound", 1)
    assert ok, message
    available, unavailable = controller.battle_availability()
    assert warrior not in available
    assert unavailable[0][0] is warrior and unavailable[0][2]

    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Skaven", result="Draw", xp_delta=1, casualties=0,
    )
    assert ok, message
    assert controller.state.campaign.battle(9).absentees[0]["reason"] == "Old Battle Wound"
    assert warrior.games_to_miss == 0


def test_enemy_out_of_action_experience_is_owned_by_each_hero():
    controller = _settled()
    warriors = controller.state.campaign.warriors
    heroes = [warrior for warrior in warriors if warrior.kind == "hero"]
    awards = controller.scenario_rewards().compute_for(
        "scenario.hidden-treasure", warriors, result="Defeat",
        enemy_out_of_action={heroes[0].id: 2, heroes[1].id: 1},
    )
    assert awards[heroes[0].id] == 3  # survived + two enemies
    assert awards[heroes[1].id] == 2  # survived + one enemy


def test_manual_scenario_awards_declare_the_required_recipient_control():
    controller = _settled()

    breakthrough = controller.scenario_rewards().plan("scenario.breakthrough")
    hidden_treasure = controller.scenario_rewards().plan("scenario.hidden-treasure")
    kidnapped = controller.scenario_rewards().plan("scenario.kidnapped")
    hunted = controller.scenario_rewards().plan("scenario.the-hunters-become-the-hunted")

    assert breakthrough[-1].selection == "multiple"
    assert hidden_treasure[-1].selection == "single"
    assert {row.selection for row in kidnapped if row.amount_dice} == {"distributed"}
    assert hunted[-1].selection == "multiple"


def test_hidden_treasure_loot_seeds_post_battle_and_stash():
    controller = _settled()
    campaign = controller.state.campaign
    sword = next((item for item in campaign.inventory if item.id == "sword"), None)
    starting_swords = sword.stash if sword else 0
    ok, message = controller.record_battle(
        scenario_id="scenario.hidden-treasure", scenario_name="Hidden Treasure",
        opponent="Skaven", result="Victory", xp_delta=0, casualties=0,
        scenario_results={
            "scenario_id": "scenario.hidden-treasure",
            "additional_rewards": [
                {"kind": "resource", "resource": "gold_crowns", "quantity": 31},
                {"kind": "resource", "resource": "wyrdstone_fragments", "quantity": 2},
                {"kind": "item", "item_id": "light_armour", "quantity": 1},
                {"kind": "item", "item_id": "sword", "quantity": 1},
            ],
        },
    )
    assert ok, message
    battle = campaign.battle(9)
    post = campaign.post_battle(9)
    assert battle.gold_delta == 31 and post.gold_delta == 31
    assert battle.wyrdstone == 2 and post.wyrdstone_delta == 2
    sword = next(item for item in campaign.inventory if item.id == "sword")
    assert sword.stash == starting_swords + 1
    assert any(item.id == "light_armour" and item.stash >= 1 for item in campaign.inventory)


def test_house_rule_rewards_use_the_same_post_battle_pipeline():
    controller = _settled()
    campaign = controller.state.campaign
    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Undead", result="Draw", xp_delta=0, casualties=0,
        scenario_results={
            "scenario_id": "scenario.skirmish",
            "additional_rewards": [
                {"kind": "resource", "resource": "gold_crowns", "quantity": 17, "source": "house_rule"},
                {"kind": "resource", "resource": "wyrdstone_fragments", "quantity": 2, "source": "house_rule"},
                {"kind": "item", "item_id": "sword", "quantity": 3, "source": "house_rule"},
            ],
        },
    )
    assert ok, message
    post = campaign.post_battle(9)
    assert post.gold_delta == 17 and post.wyrdstone_delta == 2
    assert next(item for item in campaign.inventory if item.id == "sword").stash == 3


def test_scenario_special_reward_is_structured_assignable_inventory():
    controller = _settled()
    ok, message = controller.record_battle(
        scenario_id="scenario.wizards-mansion", scenario_name="Wizard's Mansion",
        opponent="Skaven", result="Victory", xp_delta=0, casualties=0,
        scenario_results={"additional_rewards": [{
            "kind": "special", "special_id": "athame", "label": "Athame",
            "rule": "Athame scenario rules", "quantity": 1,
        }]},
    )
    assert ok, message
    item = next(row for row in controller.state.campaign.inventory if row.id == "scenario_reward.athame")
    assert item.stash == 1 and item.special_rules == ["Athame scenario rules"]
    hero = next(row for row in controller.state.campaign.warriors if row.kind == "hero")
    ok, message = controller.assign_stash_item(item.id, hero.id)
    assert ok, message
    equipped = next(row for row in hero.equipment if row.item_id == item.id)
    assert equipped.special_rules == item.special_rules


def test_magical_scenario_reward_creates_followup_instead_of_fake_item():
    controller = _settled()
    ok, message = controller.record_battle(
        scenario_id="scenario.monster-hunt", scenario_name="Monster Hunt",
        opponent="Skaven", result="Victory", xp_delta=0, casualties=0,
        scenario_results={"additional_rewards": [{
            "kind": "special", "special_id": "magical-artefact", "label": "Magical artefact", "quantity": 1,
        }]},
    )
    assert ok, message
    post = controller.state.campaign.pending_post_battle
    followup = next(row for row in post.pending_follow_ups if row.get("type") == "exploration_followup")
    assert followup["queue"] == [{"type": "magical_artefact_table"}]
    assert not any(row.id == "scenario_reward.magical-artefact" for row in controller.state.campaign.inventory)


def test_wand_reward_requires_a_hero_and_becomes_equipment():
    controller = _settled()
    assert controller.record_battle(
        scenario_id="scenario.the-item-lost", scenario_name="The Item Lost",
        opponent="Possessed", result="Victory", xp_delta=0, casualties=0,
        scenario_results={"additional_rewards": [{
            "kind": "special", "special_id": "scenario.the-item-lost.reward",
            "label": "Wand of Phyrros", "quantity": 1, "rule": "Use Fires of U'Zhul once per game.",
        }]},
    )[0]
    engine = controller.post_battle_engine()
    assert engine.exploration_followup_pending()["kind"] == "choose_hero"
    hero = next(row for row in controller.state.campaign.warriors if row.kind == "hero")
    assert engine.advance_exploration_followup(hero_id=hero.id)[0]
    assert any(item.item_id == "scenario_reward.wand_of_phyrros" for item in hero.equipment)


def test_tome_reward_grants_exactly_two_selected_spells():
    controller = _settled()
    controller.state.campaign.band_id = "mercenaries"
    assert controller.record_battle(
        scenario_id="scenario.assault-on-the-rock", scenario_name="Assault on the Rock",
        opponent="Orcs", result="Victory", xp_delta=0, casualties=0,
        scenario_results={"additional_rewards": [{
            "kind": "special", "special_id": "scenario.assault-on-the-rock.reward",
            "label": "Tome of Magic", "quantity": 1,
        }]},
    )[0]
    engine = controller.post_battle_engine()
    row = next(value for value in engine.post.pending_follow_ups if value["type"] == "scenario_spell_reward")
    hero = next(value for value in controller.state.campaign.warriors if value.kind == "hero")
    spells = engine.scenario_spell_options(hero.id)[:2]
    assert engine.resolve_scenario_spell_reward(row["id"], hero.id, [spell["id"] for spell in spells])[0]
    assert all(spell["name"] in hero.skills for spell in spells)


def test_encampment_reward_requires_destroy_or_occupy_choice():
    controller = _settled()
    assert controller.record_battle(
        scenario_id="scenario.encampment-raid", scenario_name="Encampment Raid",
        opponent="Mercenaries", result="Victory", xp_delta=0, casualties=0,
        scenario_results={"additional_rewards": [{
            "kind": "special", "special_id": "scenario.encampment-raid.reward",
            "label": "Captured camp", "quantity": 1,
        }]},
    )[0]
    engine = controller.post_battle_engine()
    row = next(value for value in engine.post.pending_follow_ups if value["type"] == "scenario_encampment")
    assert engine.resolve_scenario_encampment(row["id"], "occupy")[0]
    assert any("captured camp" in rule["text"].casefold() for rule in controller.state.campaign.special_rules)


def test_draft_campaign_cannot_record_battles():
    controller = AppController()  # fresh controller: draft state
    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="X", result="Victory", xp_delta=1, casualties=0,
    )
    assert not ok and "initial warband" in message
