"""Per-warrior Out of Action recording: dialog checklist → Recovery filter.

``record_battle`` stores the warrior ids recorded Out of Action and derives
the ``casualties`` count from them; Recovery (post-battle step 1) then offers
only those warriors. Battles recorded before this feature carry
``out_of_action_ids is None`` and keep offering every warrior.
"""
from __future__ import annotations

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import make_example_state
from mordheim_campaign.ui.views.moments.post_battle_moment import PostBattleMoment


def _settled() -> AppController:
    controller = AppController()
    controller.replace_state(make_example_state(controller.port))
    controller.state.campaign.post_battle(8).complete = True
    return controller


def _record(controller: AppController, **overrides):
    kwargs = dict(
        scenario_id="scenario.skirmish", scenario_name="Skirmish",
        opponent="Cultists", result="Victory", xp_delta=1, casualties=0,
    )
    kwargs.update(overrides)
    return controller.record_battle(**kwargs)


def test_recorded_ids_set_the_casualties_count():
    controller = _settled()
    ids = ["marta", "novices"]
    ok, _ = _record(controller, out_of_action_ids=ids)
    assert ok
    battle = controller.state.campaign.battle(9)
    assert battle.out_of_action_ids == ids
    assert battle.casualties == 2


def test_empty_record_keeps_casualties_zero_and_ids_empty():
    controller = _settled()
    ok, _ = _record(controller, out_of_action_ids=[])
    assert ok
    battle = controller.state.campaign.battle(9)
    assert battle.out_of_action_ids is None and battle.casualties == 0


def test_recovery_prefilter_offers_only_recorded_warriors():
    controller = _settled()
    _record(controller, out_of_action_ids=["marta", "novices"])
    battle = controller.state.campaign.battle(9)
    moment = PostBattleMoment.__new__(PostBattleMoment)  # no Tk init needed
    moment.controller = controller
    marked = moment._out_of_action_warriors(battle)
    assert [w.id for w in marked] == ["marta", "novices"]


def test_recovery_falls_back_to_every_warrior_for_legacy_battles():
    controller = _settled()
    battle = controller.state.campaign.battle(8)  # example narrative battle
    assert battle.out_of_action_ids is None
    moment = PostBattleMoment.__new__(PostBattleMoment)
    moment.controller = controller
    marked = moment._out_of_action_warriors(battle)
    assert len(marked) == len(controller.state.campaign.warriors)


def test_unknown_ids_are_ignored_by_the_filter():
    controller = _settled()
    _record(controller, out_of_action_ids=["marta", "ghost"])
    battle = controller.state.campaign.battle(9)
    moment = PostBattleMoment.__new__(PostBattleMoment)
    moment.controller = controller
    marked = moment._out_of_action_warriors(battle)
    assert [w.id for w in marked] == ["marta"]


def test_out_of_action_ids_survive_save_load(tmp_path):
    from mordheim_campaign.persistence import load_campaign, save_campaign

    controller = _settled()
    _record(controller, out_of_action_ids=["anna"])
    reloaded = load_campaign(save_campaign(tmp_path / "ooa.mordheim", controller.state))
    assert reloaded.campaign.battle(9).out_of_action_ids == ["anna"]
