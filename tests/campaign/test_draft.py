"""Borrador y ejemplo: perfiles canónicos + acciones de edición del controlador."""
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.state import make_example_state


def _controller() -> AppController:
    return AppController(port=KnowledgePort())


def test_controller_default_draft_is_sisters_starter():
    controller = _controller()
    campaign = controller.state.campaign
    assert campaign.band_id == "sisters-of-sigmar"
    assert campaign.collection == "mordheim"
    assert campaign.warband_type == "Sisters of Sigmar"
    assert campaign.is_draft
    assert campaign.draft_is_legal


def test_cannot_add_beyond_profile_limits():
    controller = _controller()
    # Máximo de la banda: 1 matriarca + 1 augur + 3 superioras = 5 héroes.
    for _ in range(3):
        ok, _ = controller.add_draft_warriors("sister-superior")
        assert ok
    ok, message = controller.add_draft_warriors("sister-superior")
    assert not ok and "limit" in message.lower()
    ok, _ = controller.add_draft_warriors("augur")
    assert ok
    ok, _ = controller.add_draft_warriors("augur")
    assert not ok  # máximo 1 augur


def test_henchmen_groups_respect_group_limits():
    controller = _controller()
    ok, message = controller.add_draft_warriors("sigmarite-sister", 6)
    assert not ok and "at most 5" in message  # group_size máximo 5
    ok, _ = controller.add_draft_warriors("sigmarite-sister", 5)
    assert ok


def test_treasury_guard_blocks_unaffordable_additions():
    from mordheim_campaign.application.state import make_draft_state

    port = KnowledgePort()
    controller = AppController(port=port, state=make_draft_state(port, "lustrian-reavers"))
    # Héroes caros de Lustrian Reavers: el tesoro inicial no alcanza para todos.
    assert controller.add_draft_warriors("conqueror", 1)[0]
    assert controller.add_draft_warriors("trapmaster", 1)[0]
    ok, message = controller.add_draft_warriors("saurus-slayer", 1)
    assert not ok and "gold" in message.lower()


def test_group_resize_and_removal():
    controller = _controller()
    sisters = next(w for w in controller.state.campaign.warriors if w.profile_id == "sigmarite-sister")
    ok, _ = controller.adjust_draft_group(sisters.id, 1)
    assert ok and sisters.quantity == 3
    ok, _ = controller.adjust_draft_group(sisters.id, -2)
    assert ok and sisters.quantity == 1
    ok, _ = controller.adjust_draft_group(sisters.id, -1)
    assert not ok  # un grupo conserva al menos un miembro
    ok, message = controller.remove_draft_warrior(sisters.id)
    assert ok
    assert all(w.id != sisters.id for w in controller.state.campaign.warriors)


def test_hero_names_are_unique():
    controller = _controller()
    controller.add_draft_warriors("sister-superior")
    controller.add_draft_warriors("sister-superior")
    names = [w.name for w in controller.state.campaign.warriors if w.kind == "hero"]
    assert len(names) == len(set(names))
    assert "Sister Superior II" in names


def test_commit_initial_warband_creates_state_zero():
    controller = _controller()
    campaign = controller.state.campaign
    controller.commit_initial_warband()
    assert not campaign.is_draft
    assert campaign.current_state_number == 0
    assert len(campaign.states) == 1
    state = campaign.current_state
    assert state.models == campaign.draft_model_count
    assert state.gold == campaign.draft_treasury
    assert controller.state.selected_moment == "state:0"


def test_draft_edits_are_ignored_after_commit():
    controller = _controller()
    controller.commit_initial_warband()
    ok, _ = controller.add_draft_warriors("novices")
    assert not ok


def test_example_state_profiles_are_canonical():
    port = KnowledgePort()
    state = make_example_state(port)
    campaign = state.campaign
    assert campaign.band_id == "sisters-of-sigmar"
    assert not campaign.is_draft
    assert campaign.current_state_number == 7
    assert {warrior.profile_id for warrior in campaign.warriors} == {
        "sigmarite-matriarch", "sister-superior", "augur", "sigmarite-sister", "novices",
    }
    canonical = {
        profile.profile_id: profile
        for profile in port.profiles(campaign.collection, campaign.band_id)
    }
    for warrior in campaign.warriors:
        profile = canonical[warrior.profile_id]
        assert warrior.stats == {**profile.characteristics, **warrior.stat_modifiers}
        assert warrior.cost == profile.cost
        assert warrior.kind == profile.kind
        assert warrior.profile_name == profile.name
