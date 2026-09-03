"""Persistencia de campañas: round-trip JSON, robustez y exportación Markdown."""
from dataclasses import asdict
import json

import pytest

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.state import make_draft_state, make_example_state
from mordheim_campaign.persistence import CampaignFileError, export_campaign_summary, load_campaign, save_campaign


def _canonical(state):
    """Comparable JSON-safe del estado (convierte conjuntos de dataclasses)."""

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
    path = save_campaign(tmp_path / "campaña.mordheim", original)
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


def test_missing_band_id_is_rejected(tmp_path):
    from mordheim_campaign.application.state import AppState, CampaignVM

    payload = {
        "marker": "MORDHEIM_CAMPAIGN_MANAGER",
        "format_version": 1,
        "campaign": {"campaign_name": "No KB band", "warband_name": "X", "warband_type": "X", "started": ""},
        "view": {},
    }
    path = tmp_path / "broken.mordheim"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(CampaignFileError):
        load_campaign(path)


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
    from mordheim_campaign.application.state import CampaignVM
    from mordheim_campaign.persistence import suggest_filename

    campaign = CampaignVM("La Campaña de Morr!", "My Warband", "Sisters of Sigmar", "")
    assert suggest_filename(campaign) == "la-campaña-de-morr.mordheim"


def test_export_markdown_summary(tmp_path):
    port = KnowledgePort()
    state = make_example_state(port)
    path = export_campaign_summary(tmp_path / "resumen.md", state)
    text = path.read_text(encoding="utf-8")
    assert "The Sisters of Morr" in text
    assert "Sisters of Sigmar" in text
    assert "Mother Superior" in text
    assert "State #7" in text
    assert "Battle #1" in text
    assert "Sigmarite Hammer" in text
