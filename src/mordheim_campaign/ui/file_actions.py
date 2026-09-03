"""Acciones de fichero del Campaign Manager.

Solo esta capa conoce los diálogos de Tk; las decisiones (qué guardar, con qué
formato) viven en ``mordheim_campaign.persistence`` y el estado se reemplaza a
través de :class:`AppController`.
"""
from __future__ import annotations

from tkinter import filedialog, messagebox

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.persistence import (
    CampaignFileError,
    export_campaign_summary,
    load_campaign,
    save_campaign,
    suggest_filename,
)

_FILE_TYPES = (("Mordheim campaign", "*.mordheim"), ("JSON", "*.json"), ("All files", "*.*"))


def _report_error(parent, action: str, exc: Exception) -> None:
    messagebox.showerror(f"Campaign {action} error", str(exc), parent=parent)


def save_current_campaign(parent, controller: AppController):
    """Guarda la campaña activa; pide ruta solo la primera vez."""
    path = controller.persist_path
    if path is None:
        path = filedialog.asksaveasfilename(
            parent=parent,
            title="Save Mordheim campaign",
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
    """Guarda la campaña en una ruta elegida por el usuario (Save As / Export)."""
    path = filedialog.asksaveasfilename(
        parent=parent,
        title="Save a copy of the Mordheim campaign",
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
    """Carga una campaña guardada y la convierte en el estado activo."""
    path = filedialog.askopenfilename(parent=parent, title="Load Mordheim campaign", filetypes=_FILE_TYPES)
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
    """Exporta un resumen Markdown legible del estado actual."""
    path = filedialog.asksaveasfilename(
        parent=parent,
        title="Export campaign summary",
        defaultextension=".md",
        initialfile=f"{suggest_filename(controller.state.campaign).removesuffix('.mordheim')}-summary.md",
        filetypes=(("Markdown", "*.md"), ("Text", "*.txt"), ("All files", "*.*")),
    )
    if not path:
        return None
    try:
        export_campaign_summary(path, controller.state)
    except OSError as exc:
        _report_error(parent, "export", exc)
        return None
    return path
