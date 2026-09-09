from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui import file_actions
from mordheim_campaign.ui.dialogs.campaign_library import CampaignLibraryDialog
from mordheim_campaign.ui.views.moments.post_battle_moment import PostBattleMoment


def test_renaming_active_save_updates_next_save(tmp_path, monkeypatch):
    c = AppController()
    path = tmp_path / 'before.mordheim'
    monkeypatch.setattr(file_actions.filedialog, 'asksaveasfilename', lambda **kw: str(path))
    file_actions.save_current_campaign(None, c)
    dialog = SimpleNamespace(controller=c, _selected_path=lambda: path, _refresh=lambda: None)
    monkeypatch.setattr('mordheim_campaign.ui.dialogs.campaign_library.messagebox.askstring', lambda *a, **kw: 'after')
    CampaignLibraryDialog._rename(dialog)
    assert c.persist_path == tmp_path / 'after.mordheim'
    file_actions.save_current_campaign(None, c)
    assert not path.exists()


def test_rare_search_cannot_be_consumed_twice():
    holder = {'success': True}
    purchase = Mock(return_value=(True, 'bought'))
    assert PostBattleMoment._consume_rare_purchase(holder, purchase)[0]
    assert not PostBattleMoment._consume_rare_purchase(holder, purchase)[0]
    assert purchase.call_count == 1


@pytest.mark.parametrize('saved', [None, Path('saved.mordheim')])
def test_save_and_close_stays_when_save_cancelled(saved, monkeypatch):
    controller = Mock()
    view = SimpleNamespace(controller=controller)
    monkeypatch.setattr(file_actions, 'save_current_campaign', lambda *a: saved)
    PostBattleMoment._save_and_close(view)
    assert controller.go_to_current_state.call_count == (1 if saved else 0)


@pytest.mark.parametrize('decision,save_result,expected', [(None, None, False), (False, None, True), (True, None, False), (True, 'saved', True)])
def test_unsaved_guard(decision, save_result, expected, monkeypatch):
    c = AppController()
    c.state.campaign.campaign_name = 'Changed'
    monkeypatch.setattr(file_actions.native_messagebox, 'askyesnocancel', lambda *a, **kw: decision)
    save = Mock(return_value=save_result)
    monkeypatch.setattr(file_actions, 'save_current_campaign', save)
    assert file_actions.confirm_discard_changes(None, c) is expected
    assert save.call_count == (1 if decision is True else 0)


def test_dirty_includes_battle_draft_but_not_navigation():
    c = AppController()
    c.navigate('rules')
    assert not c.has_unsaved_changes
    c.state.pending_battle_draft['notes'] = 'Unsaved battle'
    assert c.has_unsaved_changes
    c.clear_undo_history()
    assert c.has_unsaved_changes
    c.mark_saved()
    assert not c.has_unsaved_changes


@pytest.mark.parametrize('value', ['', '1.5', 'abc', 'True'])
def test_numeric_input_rejects_invalid_raw_values(value):
    from mordheim_campaign.ui.input_validation import IntegerVar, IntegerInputError
    variable = SimpleNamespace(_name='field', _tk=SimpleNamespace(globalgetvar=lambda _: value))
    with pytest.raises(IntegerInputError):
        IntegerVar.get(variable)


@pytest.mark.parametrize('value,expected', [(' 2 ', 2), ('-3', -3), (0, 0)])
def test_numeric_input_accepts_integers(value, expected):
    from mordheim_campaign.ui.input_validation import IntegerVar
    variable = SimpleNamespace(_name='field', _tk=SimpleNamespace(globalgetvar=lambda _: value))
    assert IntegerVar.get(variable) == expected


def test_resource_form_reports_invalid_input_without_mutation(monkeypatch):
    from mordheim_campaign.ui.dialogs.manual_management import ResourceCorrectionDialog
    from mordheim_campaign.ui.input_validation import IntegerInputError, messagebox
    c = AppController()
    amount = Mock()
    amount.get.side_effect = IntegerInputError()
    dialog = SimpleNamespace(controller=c, amount=amount, resource=Mock(), reason=Mock(), grab_current=lambda: None)
    error = Mock()
    monkeypatch.setattr(messagebox, 'showerror', error)
    ResourceCorrectionDialog._apply(dialog)
    assert error.call_count == 1
    assert not c.has_unsaved_changes


def test_ctrl_z_in_text_field_does_not_undo_campaign():
    from mordheim_campaign.ui.shell import AppShell
    shell = SimpleNamespace(controller=Mock(can_undo=True), _undo=Mock())
    event = SimpleNamespace(widget=SimpleNamespace(winfo_class=lambda: 'TEntry'))
    assert AppShell._undo_shortcut(shell, event) is None
    shell._undo.assert_not_called()


def test_modal_returns_grab_to_previous_editor():
    from mordheim_campaign.ui.modality import make_modal
    previous, window, owner = Mock(), Mock(), Mock()
    previous.winfo_exists.return_value = True
    window.grab_current.side_effect = [previous, None]
    make_modal(window, owner)
    window.transient.assert_called_once_with(owner.winfo_toplevel())
    callback = window.bind.call_args.args[1]
    callback(SimpleNamespace(widget=object()))
    previous.grab_set.assert_not_called()
    callback(SimpleNamespace(widget=window))
    previous.grab_set.assert_called_once()


def test_failed_rare_purchase_keeps_search_available():
    holder = {'success': True}
    assert not PostBattleMoment._consume_rare_purchase(holder, lambda: (False, 'not enough gold'))[0]
    assert not holder.get('used')


def test_failed_save_does_not_mark_clean(tmp_path, monkeypatch):
    c = AppController()
    c.persist_path = tmp_path / 'campaign.mordheim'
    c.state.campaign.campaign_name = 'Pending'
    monkeypatch.setattr(file_actions, 'save_campaign', Mock(side_effect=OSError('disk full')))
    monkeypatch.setattr(file_actions, '_report_error', Mock())
    assert file_actions.save_current_campaign(None, c) is None
    assert c.has_unsaved_changes


def test_cancelled_load_keeps_state_path_and_undo(tmp_path, monkeypatch):
    c = AppController()
    path = tmp_path / 'campaign.mordheim'
    file_actions.save_campaign(path, c.state)
    c.persist_path = tmp_path / 'active.mordheim'
    c.perform_undoable('edit name', lambda: setattr(c.state.campaign, 'campaign_name', 'Pending'))
    monkeypatch.setattr(file_actions.filedialog, 'askopenfilename', lambda **kw: str(path))
    monkeypatch.setattr(file_actions.native_messagebox, 'askyesnocancel', lambda *a, **kw: None)
    assert file_actions.load_campaign_file(None, c) is None
    assert c.state.campaign.campaign_name == 'Pending'
    assert c.persist_path.name == 'active.mordheim'
    assert c.can_undo


@pytest.mark.parametrize('allowed', [True, False])
def test_close_application_respects_unsaved_decision(allowed, monkeypatch):
    from mordheim_campaign.app import CampaignManagerApp
    app = SimpleNamespace(controller=Mock(), destroy=Mock())
    monkeypatch.setattr(file_actions, 'confirm_discard_changes', lambda *a: allowed)
    CampaignManagerApp._close(app)
    assert app.destroy.call_count == int(allowed)


def test_invalid_preview_keeps_last_battle_draft():
    from mordheim_campaign.ui.dialogs.record_battle import BattleEntryMoment
    from mordheim_campaign.ui.input_validation import IntegerInputError
    c = AppController()
    c.state.pending_battle_draft['notes'] = 'Previously entered'
    xp = Mock()
    xp.get.side_effect = IntegerInputError()
    view = SimpleNamespace(controller=c, number=1, scenario_box=Mock(), _scenario_ids=['test'],
                           opponent_var=Mock(), rating_var=Mock(), result_var=Mock(), xp_var=xp)
    view.scenario_box.current.return_value = 0
    BattleEntryMoment._save_draft(view)
    assert c.state.pending_battle_draft == {'notes': 'Previously entered'}


def test_loading_same_file_after_save_reads_fresh_contents(tmp_path, monkeypatch):
    c = AppController()
    c.persist_path = tmp_path / 'campaign.mordheim'
    file_actions.save_current_campaign(None, c)
    c.state.campaign.campaign_name = 'Updated before reopening'
    monkeypatch.setattr(file_actions.filedialog, 'askopenfilename', lambda **kw: str(c.persist_path))
    monkeypatch.setattr(file_actions.native_messagebox, 'askyesnocancel', lambda *a, **kw: True)
    file_actions.load_campaign_file(None, c)
    assert c.state.campaign.campaign_name == 'Updated before reopening'
    assert not c.has_unsaved_changes
