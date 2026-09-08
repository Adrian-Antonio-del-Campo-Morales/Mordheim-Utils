from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import make_example_state


def test_successful_action_can_be_undone() -> None:
    controller = AppController()
    before = len(controller.state.campaign.warriors)

    result = controller.perform_undoable(
        "Hire Sister Superior", lambda: controller.add_draft_warriors("sister-superior"))

    assert result[0] and controller.can_undo
    assert controller.undo_label == "Undo: Hire Sister Superior"
    assert len(controller.state.campaign.warriors) == before + 1
    assert controller.undo()[0]
    assert len(controller.state.campaign.warriors) == before


def test_failed_or_unchanged_action_is_not_recorded() -> None:
    controller = AppController()

    result = controller.perform_undoable(
        "Invalid hire", lambda: controller.add_draft_warriors("not-a-profile"))

    assert not result[0]
    assert not controller.can_undo
    controller.perform_undoable("No change", lambda: (True, "Nothing changed"))
    assert not controller.can_undo


def test_multiple_actions_are_undone_in_reverse_order() -> None:
    controller = AppController()
    starting_gold = controller.state.campaign.starting_gold
    for amount in (10, 20, 30):
        controller.perform_undoable(
            f"Add {amount} gc",
            lambda value=amount: (setattr(controller.state.campaign, "starting_gold",
                                           controller.state.campaign.starting_gold + value) or True, "ok"),
        )

    controller.undo()
    assert controller.state.campaign.starting_gold == starting_gold + 30
    controller.undo()
    controller.undo()
    assert controller.state.campaign.starting_gold == starting_gold


def test_undo_removes_a_stored_dice_result_so_it_can_be_rolled_again() -> None:
    controller = AppController()
    controller.replace_state(make_example_state(controller.port))
    holder = controller.state.campaign.pending_post_battle.step_state.setdefault("exploration", {})

    controller.perform_undoable("Exploration roll", lambda: holder.update(dice=[6, 6, 2]))
    assert holder["dice"] == [6, 6, 2]
    controller.undo()

    restored = controller.state.campaign.pending_post_battle.step_state.setdefault("exploration", {})
    assert "dice" not in restored
    controller.perform_undoable("Exploration roll", lambda: restored.update(dice=[1, 3, 5]))
    assert restored["dice"] == [1, 3, 5]


def test_replacing_campaign_clears_history() -> None:
    controller = AppController()
    controller.perform_undoable(
        "Correction", lambda: (setattr(controller.state.campaign, "starting_gold", 999) or True, "ok"))
    assert controller.can_undo

    controller.replace_state(make_example_state(controller.port))

    assert not controller.can_undo

