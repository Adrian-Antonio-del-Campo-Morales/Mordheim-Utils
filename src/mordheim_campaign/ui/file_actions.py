"""File actions of the Campaign Manager.

Only this layer knows the Tk dialogs; the decisions (what to save, in which
format) live in ``mordheim_campaign.persistence`` and the state is replaced
through :class:`AppController`.
"""
from __future__ import annotations

from tkinter import filedialog, messagebox
from mordheim_ui.i18n import tr

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.persistence import (
    CampaignFileError,
    export_campaign_summary,
    load_campaign,
    save_campaign,
    suggest_filename,
)

_FILE_TYPES = (("Mordheim campaign", "*.mordheim"), (tr('JSON'), "*.json"), (tr('All files'), "*.*"))


def _report_error(parent, action: str, exc: Exception) -> None:
    messagebox.showerror(tr('Campaign {} error').format(action), str(exc), parent=parent)


def save_current_campaign(parent, controller: AppController):
    """Saves the active campaign; asks for a path only the first time."""
    path = controller.persist_path
    if path is None:
        path = filedialog.asksaveasfilename(
            parent=parent,
            title=tr('Save Mordheim campaign'),
            defaultextension=".mordheim",
            initialfile=suggest_filename(controller.state.campaign),
            filetypes=_FILE_TYPES,
        )
    if not path:
        return None
    try:
        save_campaign(path, controller.state)
    except (CampaignFileError, OSError) as exc:
        _report_error(parent, "save", exc)
        return None
    controller.persist_path = path
    return path


def save_campaign_copy(parent, controller: AppController):
    """Saves the campaign to a user-chosen path (Save As / Export)."""
    path = filedialog.asksaveasfilename(
        parent=parent,
        title=tr('Save a copy of the Mordheim campaign'),
        defaultextension=".mordheim",
        initialfile=suggest_filename(controller.state.campaign),
        filetypes=_FILE_TYPES,
    )
    if not path:
        return None
    try:
        save_campaign(path, controller.state)
    except (CampaignFileError, OSError) as exc:
        _report_error(parent, "save", exc)
        return None
    controller.persist_path = path
    return path


def load_campaign_file(parent, controller: AppController):
    """Loads a saved campaign and makes it the active state."""
    path = filedialog.askopenfilename(parent=parent, title=tr('Load Mordheim campaign'), filetypes=_FILE_TYPES)
    if not path:
        return None
    try:
        state = load_campaign(path)
    except (CampaignFileError, OSError) as exc:
        _report_error(parent, "load", exc)
        return None
    controller.persist_path = path
    controller.replace_state(state)
    return path


def export_campaign_markdown(parent, controller: AppController):
    """Exports a readable Markdown summary of the current state."""
    path = filedialog.asksaveasfilename(
        parent=parent,
        title=tr('Export campaign summary'),
        defaultextension=".md",
        initialfile=f"{suggest_filename(controller.state.campaign).removesuffix('.mordheim')}-summary.md",
        filetypes=((tr('Markdown'), "*.md"), (tr('Text'), "*.txt"), (tr('All files'), "*.*")),
    )
    if not path:
        return None
    try:
        export_campaign_summary(path, controller.state)
    except OSError as exc:
        _report_error(parent, "export", exc)
        return None
    return path
