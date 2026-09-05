from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame


class EquipmentEditorDialog(tk.Toplevel):
    """Per-warrior equipment editor: reassign between roster and stash.

    Left: every warrior with their carried equipment (RETURN buttons). Right:
    the unassigned stash (ASSIGN buttons). Changes apply immediately through
    the controller and are legal outside the post-battle sequence too.
    """

    def __init__(self, parent: tk.Misc, controller: AppController, *, warrior_id: str | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=COLORS["bg"])
        self.title("Equipment Editor")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=18, pady=18)
        body = outer.body
        body.configure(padx=16, pady=16)

        tk.Label(body, text="EQUIPMENT", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).pack(anchor="w")
        tk.Label(
            body,
            text="Reassign equipment between the roster and the stash. Nothing is bought or sold here; the warband total stays the same.",
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=560, justify="left",
        ).pack(anchor="w", pady=(4, 10))

        columns = tk.Frame(body, bg=COLORS["panel"])
        columns.pack(fill="both", expand=True)
        columns.columnconfigure(0, weight=3)
        columns.columnconfigure(1, weight=2)

        roster = BorderedFrame(columns, background=COLORS["panel_alt"], padding=1)
        roster.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        rb = roster.body
        rb.configure(padx=10, pady=10)
        tk.Label(rb, text="CARRIED BY THE WARBAND", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        scroll = ScrollableFrame(rb, background=COLORS["panel_alt"], height=330)
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll
        for warrior in controller.state.campaign.warriors:
            self._warrior_block(scroll.inner, warrior, highlighted=warrior.id == warrior_id)

        stash = BorderedFrame(columns, background=COLORS["panel_alt"], padding=1)
        stash.grid(row=0, column=1, sticky="nsew")
        sb = stash.body
        sb.configure(padx=10, pady=10)
        tk.Label(sb, text="STASH (UNASSIGNED)", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        self._stash_box = tk.Frame(sb, bg=COLORS["panel_alt"])
        self._stash_box.pack(fill="both", expand=True)

        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(12, 0))
        self._status = tk.StringVar(value="")
        tk.Label(actions, textvariable=self._status, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=380, justify="left").pack(side="left")
        ttk.Button(actions, text="Done", command=self.destroy).pack(side="right")

        self._refresh()
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(self._center)

    # ----------------------------------------------------------------- blocks

    def _warrior_block(self, parent: tk.Misc, warrior, *, highlighted: bool) -> None:
        block = tk.Frame(parent, bg=COLORS["panel_alt"], pady=6)
        block.pack(fill="x")
        if highlighted:
            block.configure(highlightthickness=1, highlightbackground=COLORS["accent"])
        head = tk.Frame(block, bg=COLORS["panel_alt"])
        head.pack(fill="x")
        label = warrior.name + (f"  ·  ×{warrior.quantity}" if warrior.quantity > 1 else "")
        tk.Label(head, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(side="left")
        if warrior.equipment:
            for item_id, name in self._equipped_items(warrior):
                row = tk.Frame(block, bg=COLORS["panel_alt"])
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"• {name}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(side="left", fill="x", expand=True)
                ttk.Button(row, text="RETURN", style="Mini.TButton", width=8,
                           command=lambda i=item_id, w=warrior: self._move(self.controller.return_equipped_item, i, w.id)).pack(side="right")
        else:
            tk.Label(block, text="No equipment", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")

    def _stash_rows(self, parent: tk.Misc) -> None:
        stash_rows = [item for item in self.controller.state.campaign.inventory if item.stash > 0]
        if not stash_rows:
            tk.Label(parent, text="The stash is empty.", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            return
        for item in stash_rows:
            row = tk.Frame(parent, bg=COLORS["panel_alt"], pady=4)
            row.pack(fill="x")
            tk.Label(row, text=f"{item.name} ×{item.stash}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8), anchor="w").pack(side="left", fill="x", expand=True)
            ttk.Button(row, text="ASSIGN…", style="Mini.TButton", width=9,
                       command=lambda i=item.id: self._assign_pick(i)).pack(side="right")

    def _assign_pick(self, item_id: str) -> None:
        """Pick the warrior receiving the stash item."""
        warriors = self.controller.state.campaign.warriors
        dialog = tk.Toplevel(self)
        dialog.title("Assign to…")
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text="Assign to which warrior?", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(padx=16, pady=(12, 6))
        listbox = tk.Listbox(dialog, height=min(10, len(warriors)), width=34, bg=COLORS["entry"], fg=COLORS["text"],
                             selectbackground=COLORS["accent"], selectforeground=COLORS["black"], bd=0, font=("Segoe UI", 9), activestyle="none")
        listbox.pack(padx=16, pady=4)
        for warrior in warriors:
            label = warrior.name + (f"  ·  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            listbox.insert("end", label)
        listbox.selection_set(0)

        def _confirm() -> None:
            selection = listbox.curselection()
            if not selection:
                dialog.destroy()
                return
            warrior = warriors[selection[0]]
            dialog.destroy()
            self._move(self.controller.assign_stash_item, item_id, warrior.id)

        ttk.Button(dialog, text="ASSIGN", style="Accent.TButton", command=_confirm).pack(pady=(4, 12))
        dialog.bind("<Return>", lambda _e: _confirm())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())

    # --------------------------------------------------------------- plumbing

    def _equipped_items(self, warrior) -> list[tuple[str, str]]:
        """(item_id, display name) pairs carried by the warrior."""
        pairs: list[tuple[str, str]] = []
        for name in warrior.equipment:
            row = next((item for item in self.controller.state.campaign.inventory if item.name == name), None)
            pairs.append((row.id if row else f"name:{name}", name))
        return pairs

    def _move(self, action, item_id: str, warrior_id: str) -> None:
        if item_id.startswith("name:"):
            self._status.set("This item is not in the inventory ledger; only ledger items can move.")
            return
        ok, message = action(item_id, warrior_id)
        self._status.set(("✓ " if ok else "⚠ ") + message)
        self._refresh()

    def _refresh(self) -> None:
        """Rebuild lists in place (the dialog edits live campaign state)."""
        for frame in (self._scroll.inner, self._stash_box):
            for child in frame.winfo_children():
                child.destroy()
        for warrior in self.controller.state.campaign.warriors:
            self._warrior_block(self._scroll.inner, warrior, highlighted=False)
        self._stash_rows(self._stash_box)

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")
