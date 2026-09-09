"""PDF export of the warband at one timeline moment (persistence.warband_pdf)."""
import copy
from dataclasses import asdict

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.domain.models import InventoryItemVM
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.domain.builders import make_example_state
from mordheim_campaign.persistence import load_campaign, save_campaign
from mordheim_campaign.persistence.warband_pdf import export_warband_pdf


def _assert_pdf(path):
    data = path.read_bytes()
    assert data.startswith(b"%PDF-"), f"{path} is not a PDF"
    assert b"%%EOF" in data[-1024:], f"{path} has no EOF marker"
    assert len(data) > 500, f"{path} is suspiciously small"


def test_state_roster_snapshot_freezes_at_commit():
    port = KnowledgePort()
    controller = AppController(port=port)
    controller.commit_initial_warband()
    campaign = controller.state.campaign
    assert not campaign.is_draft
    snapshot = campaign.state(0)
    assert snapshot.roster, "the committed state must snapshot its roster"

    frozen = asdict(snapshot)
    # Mutate the live campaign afterwards (as the post-battle engine would).
    campaign.warriors[0].name = "Renamed After Commit"
    campaign.warriors[0].stats["WS"] = 9
    campaign.warriors.pop()
    campaign.inventory.append(InventoryItemVM("bonus_item", "Bonus Item", "Misc", 1, 0, 1, 5))

    assert asdict(snapshot) == frozen
    assert all(warrior.name != "Renamed After Commit" for warrior in snapshot.roster)


def test_snapshot_round_trip(tmp_path):
    port = KnowledgePort()
    original = make_example_state(port)
    path = save_campaign(tmp_path / "campaign.mordheim", original)
    restored = load_campaign(path)
    assert restored.campaign.state(7).roster == original.campaign.state(7).roster
    assert restored.campaign.state(7).inventory == original.campaign.state(7).inventory


def test_pdf_export_of_a_committed_state(tmp_path):
    port = KnowledgePort()
    campaign = make_example_state(port).campaign
    path = export_warband_pdf(tmp_path / "state7.pdf", campaign, state_number=7)
    assert path.exists()
    _assert_pdf(path)


def test_pdf_export_of_the_draft(tmp_path):
    port = KnowledgePort()
    controller = AppController(port=port)
    path = export_warband_pdf(tmp_path / "draft.pdf", controller.state.campaign, state_number=None)
    assert path.exists()
    _assert_pdf(path)


def test_pdf_export_survives_non_latin1_text(tmp_path):
    port = KnowledgePort()
    campaign = make_example_state(port).campaign
    campaign.warriors[0].name = "Sister Ana — \u201eCu\u00e9ntamelo\u201c ⚠ \U0001f3b2 \u2026"
    campaign.warriors[0].condition = "Fuera de combate — \u22121 M"
    path = export_warband_pdf(tmp_path / "weird.pdf", campaign, state_number=7)
    _assert_pdf(path)


def test_ui_wrapper_exports_the_selected_moment(tmp_path, monkeypatch):
    """Regression: the UI wrapper must call the persistence exporter, not itself."""
    from mordheim_campaign.ui import file_actions as ui_file_actions

    port = KnowledgePort()
    controller = AppController(port=port)  # starts on the draft moment
    target = tmp_path / "export.pdf"
    monkeypatch.setattr(ui_file_actions.filedialog, "asksaveasfilename", lambda **kwargs: str(target))
    result = ui_file_actions.export_warband_pdf(parent=None, controller=controller)
    assert result == str(target)
    _assert_pdf(target)
