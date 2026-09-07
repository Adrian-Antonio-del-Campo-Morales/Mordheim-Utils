from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, PageHeader, ScrollableFrame
from mordheim_ui.i18n import tr


class RulesView(tk.Frame):
    """Searchable KB browser: categories on the left, detail on the right.

    Read-only and stateless: everything comes from
    ``application.rules_catalogue`` through the controller's KnowledgePort,
    so the view works with or without an open campaign.
    """

    SEARCH_DEBOUNCE_MS = 250

    def __init__(self, master: tk.Misc, controller, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self._category_id: str | None = None
        self._selected_id: str | None = None
        self._search_job: str | None = None

        catalogue = self._catalogue()
        categories = catalogue.categories()
        self._category_id = categories[0].category_id if categories else None

        PageHeader(
            self, tr('Rules'),
            tr('Search and browse the Mordheim knowledge base without campaign-management clutter.'),
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        toolbar = tk.Frame(self, bg=COLORS["bg"])
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        if categories:
            from mordheim_ui.widgets import SegmentedTabs

            self._tabs = SegmentedTabs(
                toolbar,
                tuple((category.category_id, tr(category.label)) for category in categories),
                self._category_id or "",
                self._set_category,
            )
            self._tabs.pack(side="left", padx=(0, 12))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_search_changed)
        self._search_box = ttk.Entry(toolbar, textvariable=self._search_var, width=36)
        self._search_box.pack(side="right")
        self._search_hint = tk.Label(
            toolbar, text=tr('SEARCH'), bg=COLORS["bg"], fg=COLORS["muted"],
            font=("Segoe UI Semibold", 8),
        )
        self._search_hint.pack(side="right", padx=(0, 6))

        panes = tk.PanedWindow(
            self, orient="horizontal", sashwidth=4,
            bg=COLORS["border"], bd=0,
        )
        panes.grid(row=2, column=0, sticky="nsew")

        # Master: category row list -------------------------------------------
        master_box = BorderedFrame(panes, background=COLORS["panel"], padding=1)
        panes.add(master_box, minsize=260, width=360, stretch="never")
        master_body = master_box.body
        master_body.configure(padx=0, pady=0)
        self._list_scroll = ScrollableFrame(master_body, background=COLORS["panel"])
        self._list_scroll.pack(fill="both", expand=True)
        self._list_host = self._list_scroll.inner

        # Detail: selected entry ----------------------------------------------
        detail_box = BorderedFrame(panes, background=COLORS["panel"], padding=1)
        panes.add(detail_box, minsize=340, stretch="always")
        self._detail_scroll = ScrollableFrame(detail_box.body, background=COLORS["panel"])
        self._detail_scroll.pack(fill="both", expand=True)
        self._detail_host = self._detail_scroll.inner

        self._rebuild_list()
        self._rebuild_detail()

    # ------------------------------------------------------------- plumbing

    def _catalogue(self):
        return self.controller.port.rules_catalogue()

    def _set_category(self, category_id: str) -> None:
        self._category_id = category_id
        self._search_var.set("")  # category switch resets the query
        self._selected_id = None
        self._rebuild_list()
        self._rebuild_detail()

    def _on_search_changed(self, *_args) -> None:
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(self.SEARCH_DEBOUNCE_MS, self._apply_search)

    def _apply_search(self) -> None:
        self._search_job = None
        self._selected_id = None
        self._rebuild_list()
        self._rebuild_detail()

    # ---------------------------------------------------------------- master

    def _current_entries(self):
        catalogue = self._catalogue()
        text = self._search_var.get().strip()
        if text:
            return catalogue.search(text, self._category_id)
        return catalogue.entries(self._category_id or "") if self._category_id else ()

    def _rebuild_list(self) -> None:
        for child in self._list_host.winfo_children():
            child.destroy()
        entries = self._current_entries()
        text = self._search_var.get().strip()
        if not entries:
            message = (
                tr('No entries match the search.')
                if text
                else tr('This category has no entries.')
            )
            tk.Label(
                self._list_host, text=message, bg=COLORS["panel"], fg=COLORS["muted"],
                font=("Segoe UI", 9), wraplength=280, justify="left", padx=12, pady=12,
            ).pack(anchor="w")
            return
        for entry in entries:
            selected = entry.entry_id == self._selected_id
            row = tk.Frame(self._list_host, bg=COLORS["panel_soft"] if selected else COLORS["panel"])
            row.pack(fill="x")
            command = lambda entry_id=entry.entry_id: self._select(entry_id)
            tk.Button(
                row, text=entry.name, command=command,
                bg=COLORS["panel_soft"] if selected else COLORS["panel"],
                fg=COLORS["accent"] if selected else COLORS["text"],
                activebackground=COLORS["panel_soft"], activeforeground=COLORS["text"],
                relief="flat", bd=0, highlightthickness=0, anchor="w", cursor="hand2",
                font=("Segoe UI", 9), padx=12, pady=6,
            ).pack(fill="x")
            if entry.tags:
                tk.Label(
                    row, text="  ".join(entry.tags), bg=row["bg"], fg=COLORS["muted_dark"],
                    font=("Segoe UI", 7), anchor="w",
                ).pack(fill="x", padx=(12, 8), pady=(0, 4))
            tk.Frame(self._list_host, bg=COLORS["border_soft"], height=1).pack(fill="x")

    def _select(self, entry_id: str) -> None:
        self._selected_id = entry_id
        self._rebuild_list()
        self._rebuild_detail()

    # ---------------------------------------------------------------- detail

    def _rebuild_detail(self) -> None:
        for child in self._detail_host.winfo_children():
            child.destroy()
        catalogue = self._catalogue()
        entries = self._current_entries()
        entry = next((row for row in entries if row.entry_id == self._selected_id), None)
        if entry is None and len(entries) == 1:
            entry = entries[0]
        host = self._detail_host
        if entry is None:
            tk.Label(
                host, text=tr('Select an entry to read its rules.'),
                bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), padx=16, pady=16,
            ).pack(anchor="w")
            return
        tk.Label(
            host, text=entry.name, bg=COLORS["panel"], fg=COLORS["text"],
            font=("Georgia", 15), wraplength=520, justify="left",
        ).pack(anchor="w", padx=16, pady=(16, 2))
        if entry.tags:
            tk.Label(
                host, text="  ·  ".join(entry.tags), bg=COLORS["panel"], fg=COLORS["accent"],
                font=("Segoe UI Semibold", 8), wraplength=520, justify="left",
            ).pack(anchor="w", padx=16, pady=(0, 8))
        tk.Frame(host, bg=COLORS["border_soft"], height=1).pack(fill="x", padx=16)
        tk.Label(
            host, text=entry.effect or tr('No effect text is recorded for this entry.'),
            bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10),
            wraplength=520, justify="left",
        ).pack(anchor="w", padx=16, pady=12)
        if entry.source_refs:
            tk.Label(
                host, text=tr('SOURCES'), bg=COLORS["panel"], fg=COLORS["accent"],
                font=("Segoe UI Semibold", 8),
            ).pack(anchor="w", padx=16)
            for label in entry.source_refs:
                tk.Label(
                    host, text=f"— {label}", bg=COLORS["panel"], fg=COLORS["muted"],
                    font=("Segoe UI", 7), wraplength=520, justify="left",
                ).pack(anchor="w", padx=(24, 16))
