"""Campaign persistence: JSON round-trip, robustness and Markdown export.

The persistence layer reads and writes only the neutral v5 contract
(``contracts/campaign-file-v5/``): schema-validated documents, explicit
rejection of retired versions and of documents the contract does not accept.
"""
from dataclasses import asdict
import json
from pathlib import Path

import pytest

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.domain.builders import make_draft_state, make_example_state
from mordheim_campaign.persistence import CampaignFileError, export_campaign_summary, load_campaign, save_campaign

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "contracts" / "campaign-file-v5" / "fixtures"


def _canonical(state):
    """JSON-safe comparable of the state (converts dataclass sets)."""

    def fix(value):
        if isinstance(value, set):
            return sorted(fix(item) for item in value)
        if isinstance(value, dict):
            return {str(key): fix(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [fix(item) for item in value]
        return value

    return fix(asdict(state))


@pytest.mark.parametrize("builder", [lambda port: make_draft_state(port, "sisters-of-sigmar"), make_example_state])
def test_campaign_round_trip(tmp_path, builder):
    port = KnowledgePort()
    original = builder(port)
    path = save_campaign(tmp_path / "campaign.mordheim", original)
    assert path.exists()
    restored = load_campaign(path)
    assert _canonical(restored) == _canonical(original)
    assert restored.campaign.band_id == original.campaign.band_id
    assert restored.selected_moment == original.selected_moment


def test_round_trip_after_draft_edits(tmp_path):
    port = KnowledgePort()
    controller = AppController(port=port)
    controller.add_draft_warriors("sister-superior")
    sisters = next(w for w in controller.state.campaign.warriors if w.profile_id == "sigmarite-sister")
    controller.adjust_draft_group(sisters.id, 1)
    path = save_campaign(tmp_path / "edited.mordheim", controller.state)
    restored = load_campaign(path)
    assert _canonical(restored) == _canonical(controller.state)


def test_hireling_rating_and_capacity_modifier_survive_round_trip(tmp_path):
    from mordheim_campaign.application.post_battle_engine import PostBattleEngine

    controller = AppController()
    controller.new_campaign("Mercs", "mercenaries")
    offer = next(
        row for row in controller.draft_hired_swords()
        if row.profile_id == "hireling.hired-sword.halfling-scout"
    )
    warrior = PostBattleEngine(controller.port, controller.state.campaign, None).hireling_warrior(offer)
    assert warrior is not None
    controller.state.campaign.warriors.append(warrior)

    restored = load_campaign(save_campaign(tmp_path / "hireling.mordheim", controller.state))
    saved = next(row for row in restored.campaign.warriors if row.profile_id == offer.profile_id)
    assert saved.hireling_rating == 5
    assert saved.maximum_models_modifier == 1


def test_special_inventory_rules_survive_round_trip(tmp_path):
    state = make_example_state(KnowledgePort())
    state.campaign.inventory[0].special_rules = ["Scenario effect"]
    state.campaign.warriors[0].equipment[0].special_rules = ["Equipped scenario effect"]
    restored = load_campaign(save_campaign(tmp_path / "special-rules.mordheim", state))
    assert restored.campaign.inventory[0].special_rules == ["Scenario effect"]
    assert restored.campaign.warriors[0].equipment[0].special_rules == ["Equipped scenario effect"]


def test_temporary_rules_and_pending_choice_resume_after_round_trip(tmp_path):
    state = make_example_state(KnowledgePort())
    campaign = state.campaign
    campaign.special_rules = [{
        "source": "exploration", "text": "Temporary rule", "expires_after_battles": 1,
        "consume_when_opponent_contains": [],
    }]
    post = campaign.pending_post_battle
    post.pending_follow_ups = [{
        "type": "exploration_followup", "messages": [],
        "queue": [{"type": "choose_option", "options": [{
            "id": "take", "label": "Take", "then": [
                {"type": "grant_rule", "recipient": "warband", "text": "Resumed rule"}
            ],
        }]}],
    }]
    restored = load_campaign(save_campaign(tmp_path / "mid-sequence.mordheim", state))
    assert restored.campaign.special_rules == campaign.special_rules
    engine = PostBattleEngine(KnowledgePort(), restored.campaign, restored.campaign.pending_post_battle)
    assert engine.exploration_followup_pending()["kind"] == "choose_option"
    ok, message = engine.advance_exploration_followup(option_id="take")
    assert ok, message
    assert any(rule.get("text") == "Resumed rule" for rule in restored.campaign.special_rules)


def test_missing_band_id_is_rejected(tmp_path):
    from mordheim_campaign.domain.models import AppState, CampaignVM

    payload = {
        "marker": "MORDHEIM_CAMPAIGN_MANAGER",
        "format_version": 5,
        "saved_at": "2026-09-08T18:30:00+00:00",
        "campaign": {
            "identity": {"campaign_name": "No KB band", "warband_name": "X", "warband_type": "X", "band_id": ""},
            "configuration": {"is_draft": False},
            "resources": {"stash_value": 0, "rare_finds": 0, "treasures": 0, "campaign_points": 0},
            "warriors": [], "battles": [], "states": [], "post_battles": [], "inventory": [],
            "special_rules": [], "manual_log": [],
        },
    }
    path = tmp_path / "broken.mordheim"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CampaignFileError):
        load_campaign(path)


@pytest.mark.parametrize("version", [1, 2, 3, 4])
def test_retired_format_versions_are_rejected_explicitly(tmp_path, version):
    """v1–v4 are retired: the loader must refuse them naming both versions."""
    payload = {
        "marker": "MORDHEIM_CAMPAIGN_MANAGER",
        "format_version": version,
        "saved_at": "2026-09-08T18:30:00+00:00",
        "campaign": {},
        "view": {},
    }
    path = tmp_path / f"v{version}.mordheim"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CampaignFileError) as excinfo:
        load_campaign(path)
    message = str(excinfo.value)
    assert str(version) in message and "v5" in message


def test_future_format_version_is_rejected(tmp_path):
    payload = {
        "marker": "MORDHEIM_CAMPAIGN_MANAGER",
        "format_version": 6,
        "saved_at": "2026-09-08T18:30:00+00:00",
        "campaign": {},
    }
    path = tmp_path / "v6.mordheim"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CampaignFileError) as excinfo:
        load_campaign(path)
    assert "6" in str(excinfo.value)


def test_schema_violations_are_rejected_with_location(tmp_path):
    """A structurally invalid v5 document fails against the shared schema."""
    port = KnowledgePort()
    state = make_draft_state(port, "sisters-of-sigmar")
    payload = json.loads(
        (FIXTURES / "draft.json").read_text(encoding="utf-8")
    )
    payload["campaign"]["warriors"][0]["kind"] = "boss"  # not an allowed kind
    path = tmp_path / "invalid.mordheim"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CampaignFileError) as excinfo:
        load_campaign(path)
    assert "kind" in str(excinfo.value)


def test_unknown_top_level_section_is_rejected(tmp_path):
    payload = json.loads((FIXTURES / "draft.json").read_text(encoding="utf-8"))
    payload["settings"] = {"theme": "dark"}
    path = tmp_path / "unknown.mordheim"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CampaignFileError):
        load_campaign(path)


@pytest.mark.parametrize("fixture_name", ["draft.json", "active-campaign.json", "pending-post-battle.json", "full-inventory.json"])
def test_fixture_round_trips_through_the_python_implementation(fixture_name):
    """Every contract fixture loads through the reference reader."""
    state = load_campaign(FIXTURES / fixture_name)
    assert state.campaign.band_id


def test_saved_at_is_the_only_volatile_field(tmp_path):
    """Two saves of an unchanged campaign differ only in saved_at."""
    state = make_draft_state(KnowledgePort(), "sisters-of-sigmar")
    first = json.loads(save_campaign(tmp_path / "a.mordheim", state).read_text(encoding="utf-8"))
    second = json.loads(save_campaign(tmp_path / "b.mordheim", state).read_text(encoding="utf-8"))
    first.pop("saved_at"), second.pop("saved_at")
    assert first == second


def test_rejects_foreign_or_corrupt_files(tmp_path):
    port = KnowledgePort()
    save_campaign(tmp_path / "real.mordheim", make_draft_state(port, "sisters-of-sigmar"))
    not_ours = tmp_path / "other.json"
    not_ours.write_text(json.dumps({"marker": "OTHER", "version": 1}), encoding="utf-8")
    with pytest.raises(CampaignFileError):
        load_campaign(not_ours)
    corrupt = tmp_path / "corrupt.mordheim"
    corrupt.write_text("{not json", encoding="utf-8")
    with pytest.raises(CampaignFileError):
        load_campaign(corrupt)
    with pytest.raises(CampaignFileError):
        load_campaign(tmp_path / "missing.mordheim")


def test_suggest_filename_slugifies_campaign_name():
    from mordheim_campaign.domain.models import CampaignVM
    from mordheim_campaign.persistence import suggest_filename

    campaign = CampaignVM("The Campaign of Morr!", "My Warband", "Sisters of Sigmar", "")
    assert suggest_filename(campaign) == "the-campaign-of-morr.mordheim"


def test_export_markdown_summary(tmp_path):
    port = KnowledgePort()
    state = make_example_state(port)
    path = export_campaign_summary(tmp_path / "summary.md", state)
    text = path.read_text(encoding="utf-8")
    assert "The Sisters of Morr" in text
    assert "Sisters of Sigmar" in text
    assert "Mother Superior" in text
    assert "State #7" in text
    assert "Battle #1" in text
    assert "Sigmarite Hammer" in text
