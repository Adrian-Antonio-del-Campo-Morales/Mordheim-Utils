from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk

from mordheim_campaign.ui.file_actions import confirm_discard_changes
from mordheim_campaign.persistence import CampaignFileError, load_campaign
from mordheim_campaign.ui.dialogs.new_campaign import NewCampaignDialog
from mordheim_ui import themed_dialogs as messagebox
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.windowing import center_on_application
from mordheim_ui.widgets import BorderedFrame


class CampaignLibraryDialog(tk.Toplevel):
    """Small local library of saved campaign files."""

    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=COLORS["bg"]); self.title(tr("Campaign library")); self.resizable(False, False)
        self.transient(parent.winfo_toplevel()); self.grab_set()
        outer = BorderedFrame(self, background=COLORS["panel"], padding=1); outer.pack(padx=14, pady=14)
        body = outer.body; body.configure(padx=14, pady=12)
        tk.Label(body, text=tr("CAMPAIGN LIBRARY"), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w")
        self.path_var = tk.StringVar(value=str(controller.campaign_library_path))
        tk.Label(body, textvariable=self.path_var, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 8))
        filters = tk.Frame(body, bg=COLORS["panel"]); filters.pack(fill="x", pady=(0, 7))
        self.query_var = tk.StringVar(); self.query_var.trace_add("write", lambda *_: self._refresh())
        ttk.Entry(filters, textvariable=self.query_var, width=43).pack(side="left", fill="x", expand=True)
        self.sort_var = tk.StringVar(value=tr("Most recent"))
        sort_box = ttk.Combobox(filters, state="readonly", width=18, textvariable=self.sort_var,
                                values=(tr("Most recent"), tr("Name"), tr("Most battles")))
        sort_box.pack(side="left", padx=(7, 0)); sort_box.bind("<<ComboboxSelected>>", lambda _e: self._refresh())
        self.listbox = tk.Listbox(body, width=72, height=15, bg=COLORS["entry"], fg=COLORS["text"],
                                  selectbackground=COLORS["accent"], selectforeground=COLORS["black"], bd=0,
                                  highlightthickness=1, highlightbackground=COLORS["border_soft"])
        self.listbox.pack(fill="both", expand=True); self.listbox.bind("<Double-Button-1>", lambda _e: self._open())
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self._show_summary())
        self.summary_var = tk.StringVar(value=tr("Select a campaign to see its summary."))
        tk.Label(body, textvariable=self.summary_var, bg=COLORS["panel_alt"], fg=COLORS["text"],
                 font=("Segoe UI", 8), justify="left", anchor="w", padx=9, pady=7).pack(fill="x", pady=(7, 0))
        actions = tk.Frame(body, bg=COLORS["panel"]); actions.pack(fill="x", pady=(9, 0))
        ttk.Button(actions, text=tr("CHOOSE FOLDER"), command=self._choose_folder).pack(side="left")
        ttk.Button(actions, text=tr("BROWSE…"), command=self._browse).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text=tr("DELETE"), command=self._delete).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text=tr("RENAME…"), command=self._rename).pack(side="left", padx=(6, 0))
        ttk.Button(actions, text=tr("NEW CAMPAIGN"), command=self._new).pack(side="right", padx=(6, 0))
        ttk.Button(actions, text=tr("OPEN"), style="Accent.TButton", command=self._open).pack(side="right")
        self._refresh(); self.after_idle(lambda: center_on_application(self))

    def _refresh(self) -> None:
        files = list(self.controller.campaign_library_path.glob("*.mordheim")) if self.controller.campaign_library_path.exists() else []
        query = self.query_var.get().strip().casefold()
        if query:
            files = [path for path in files if query in path.stem.casefold()]
        if self.sort_var.get() == tr("Name"):
            files.sort(key=lambda path: path.stem.casefold())
        elif self.sort_var.get() == tr("Most battles"):
            files.sort(key=self._battle_count, reverse=True)
        else:
            files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
        self.files = files
        self.listbox.delete(0, "end")
        for path in self.files:
            self.listbox.insert("end", path.stem)
        if self.files:
            self.listbox.selection_set(0); self._show_summary()
        else:
            self.summary_var.set(tr("No matching campaigns."))

    @staticmethod
    def _battle_count(path: Path) -> int:
        try:
            return len(load_campaign(path).campaign.battles)
        except (CampaignFileError, OSError, ValueError):
            return -1

    def _selected_path(self) -> Path | None:
        selected = self.listbox.curselection()
        return self.files[selected[0]] if selected else None

    def _show_summary(self) -> None:
        path = self._selected_path()
        if path is None: return
        try:
            campaign = load_campaign(path).campaign
            status = tr("Initial creation") if campaign.is_draft else (
                tr("Post-battle pending") if campaign.pending_post_battle else tr("Ready for battle")
            )
            self.summary_var.set(
                f"{campaign.campaign_name}  ·  {campaign.warband_name}\n"
                f"{campaign.warband_type}  ·  {len(campaign.battles)} {tr('battles')}  ·  {status}"
            )
        except (CampaignFileError, OSError, ValueError) as exc:
            self.summary_var.set(tr("Cannot read campaign: {} ").format(exc).strip())

    def _choose_folder(self) -> None:
        selected = filedialog.askdirectory(parent=self, initialdir=self.controller.campaign_library_path)
        if selected:
            self.controller.campaign_library_path = Path(selected)
            self.path_var.set(selected); self._refresh()

    def _open(self) -> None:
        path = self._selected_path()
        if path is None: return
        if not confirm_discard_changes(self, self.controller):
            return
        try:
            state = load_campaign(path)
        except (CampaignFileError, OSError) as exc:
            messagebox.showerror(tr("Campaign load error"), str(exc), parent=self); return
        self.controller.persist_path = path; self.destroy(); self.controller.replace_state(state)
        self.controller.mark_saved()

    def _browse(self) -> None:
        selected = filedialog.askopenfilename(parent=self, initialdir=self.controller.campaign_library_path,
                                              filetypes=((tr("Mordheim campaign"), "*.mordheim"),))
        if selected:
            path = Path(selected)
            if not confirm_discard_changes(self, self.controller):
                return
            try:
                state = load_campaign(path)
            except (CampaignFileError, OSError) as exc:
                messagebox.showerror(tr("Campaign load error"), str(exc), parent=self); return
            self.controller.persist_path = path; self.destroy(); self.controller.replace_state(state)
            self.controller.mark_saved()

    def _rename(self) -> None:
        path = self._selected_path()
        if path is None: return
        name = messagebox.askstring(tr("Rename campaign file"), tr("New file name:"), parent=self,
                                    initialvalue=path.stem)
        if not name: return
        safe_name = "".join(character for character in name.strip() if character not in '<>:"/\\|?*').rstrip(". ")
        if not safe_name:
            messagebox.showerror(tr("Cannot rename"), tr("Enter a valid file name."), parent=self); return
        destination = path.with_name(safe_name + path.suffix)
        if destination.exists() and destination != path:
            messagebox.showerror(tr("Cannot rename"), tr("A campaign with that file name already exists."), parent=self); return
        try:
            path.rename(destination)
        except OSError as exc:
            messagebox.showerror(tr("Cannot rename"), str(exc), parent=self); return
        if self.controller.persist_path == path:
            self.controller.persist_path = destination
        self._refresh()

    def _delete(self) -> None:
        path = self._selected_path()
        if path is None: return
        if not messagebox.askyesno(tr("Delete campaign"),
                                   tr("Permanently delete '{}'? ").format(path.stem).strip(), parent=self):
            return
        try:
            path.unlink()
        except OSError as exc:
            messagebox.showerror(tr("Cannot delete"), str(exc), parent=self); return
        if self.controller.persist_path == path:
            self.controller.persist_path = None
        self._refresh()

    def _new(self) -> None:
        self.destroy(); NewCampaignDialog(self.master, self.controller)
