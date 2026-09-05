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


def test_draft_campaign_cannot_record_battles():
    controller = AppController()  # fresh controller: draft state
    ok, message = controller.record_battle(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="X", result="Victory", xp_delta=1, casualties=0,
    )
    assert not ok and "initial warband" in message
