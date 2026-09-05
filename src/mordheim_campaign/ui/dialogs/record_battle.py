from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame


class RecordBattleDialog(tk.Toplevel):
    """Record a played battle as table facts and open its post-battle.

    The scenario picker lists the KB scenario catalogue (1v1 entries first);
    the opponent is free text; result is Victory / Defeat / Draw. Derived
    numbers (rating, models) snapshot automatically from the current state —
    only what the player knows at the table is asked.
    """

    def __init__(self, parent: tk.Misc, controller: AppController) -> None:
        super().__init__(parent)
        self.controller = controller
        self._ooa_vars: dict[str, tk.BooleanVar] = {}
        self.configure(bg=COLORS["bg"])
        self.title("Record Battle")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=18, pady=18)
        body = outer.body
        body.configure(padx=20, pady=18)

        tk.Label(body, text="RECORD BATTLE", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).pack(anchor="w")
        tk.Label(
            body,
            text="Record the table facts of a played battle. The post-battle sequence that follows applies injuries, experience, exploration and trading.",
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(4, 12))

        self._scenarios = controller.scenario_options()
        self._build_scenario(body)
        self._build_opponent(body)
        self._build_result(body)
        self._build_counters(body)
        self._build_casualties(body)
        self._build_notes(body)
        self._build_actions(body)
        self._casualties_hint = tk.Label(body, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8))
        self._casualties_hint.pack(anchor="w", pady=(0, 8))

        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(self._center)

    # ----------------------------------------------------------------- rows

    def _row(self, body: tk.Frame, label: str) -> tk.Frame:
        row = tk.Frame(body, bg=COLORS["panel"])
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8), width=16, anchor="w").pack(side="left")
        return row

    def _build_scenario(self, body: tk.Frame) -> None:
        row = self._row(body, "SCENARIO")
        # 1v1 scenarios first, then multiplayer, keeping catalogue order inside each group.
        ordered = sorted(self._scenarios, key=lambda entry: (entry[2] != "1v1",))
        labels = [f"{name}  ·  {mode}" for _sid, name, mode in ordered]
        self._scenario_ids = [scenario_id for scenario_id, _name, _mode in ordered]
        self._scenario_names = {scenario_id: name for scenario_id, name, _mode in self._scenarios}
        self.scenario_box = ttk.Combobox(row, state="readonly", values=labels, width=34)
        self.scenario_box.pack(side="left")
        self.scenario_box.set(labels[0] if labels else "(no scenarios)")

    def _build_opponent(self, body: tk.Frame) -> None:
        row = self._row(body, "OPPONENT")
        self.opponent_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.opponent_var, width=28).pack(side="left")
        rating_row = tk.Frame(body, bg=COLORS["panel"])
        rating_row.pack(fill="x", pady=(0, 8))
        tk.Label(rating_row, text="OPPONENT RATING", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8), width=16, anchor="w").pack(side="left")
        self.rating_var = tk.StringVar()
        ttk.Entry(rating_row, textvariable=self.rating_var, width=8).pack(side="left")
        tk.Label(rating_row, text="(optional)", bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left", padx=(6, 0))

    def _build_result(self, body: tk.Frame) -> None:
        row = self._row(body, "RESULT")
        self.result_var = tk.StringVar(value="Victory")
        for value in ("Victory", "Defeat", "Draw"):
            ttk.Radiobutton(row, text=value, value=value, variable=self.result_var).pack(side="left", padx=(0, 10))

    def _build_counters(self, body: tk.Frame) -> None:
        row = self._row(body, "EXPERIENCE")
        self.xp_var = tk.IntVar(value=1)
        ttk.Spinbox(row, from_=0, to=99, width=5, textvariable=self.xp_var).pack(side="left")
        tk.Label(row, text="total XP granted to each surviving warrior", bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left", padx=(8, 0))

    def _build_casualties(self, body: tk.Frame) -> None:
        """Checklist of warriors recorded Out of Action (drives Recovery)."""
        self._row(body, "OUT OF ACTION")
        warriors = self.controller.state.campaign.warriors
        box = tk.Frame(body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"])
        box.pack(fill="x", pady=(0, 8))
        inner = tk.Frame(box, bg=COLORS["panel"], padx=10, pady=8)
        inner.pack(fill="x")
        for warrior in warriors:
            label = warrior.name + (f"  ·  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            var = tk.BooleanVar(value=False)
            self._ooa_vars[warrior.id] = var
            ttk.Checkbutton(
                inner, text=label, variable=var,
                command=self._update_hint,
            ).pack(anchor="w", pady=1)
        tk.Label(
            body,
            text="Marked warriors roll on the serious-injury charts in Recovery (post-battle step 1). Henchman groups: ticking marks the whole group's survival roll.",
            bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=430, justify="left",
        ).pack(anchor="w")

    def _build_notes(self, body: tk.Frame) -> None:
        row = self._row(body, "NOTES")
        self.notes_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.notes_var, width=30).pack(side="left")

    def _build_actions(self, body: tk.Frame) -> None:
        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(16, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="RECORD & RESOLVE", style="Accent.TButton", command=self._record).pack(side="right")

    # --------------------------------------------------------------- actions    def _update_hint(self) -> None:
        count = len(self._out_of_action_ids())
        self._casualties_hint.configure(text=f"{count} warrior(s) recorded Out of Action")

    def _out_of_action_ids(self) -> list[str]:
        return [warrior_id for warrior_id, var in self._ooa_vars.items() if var.get()]

    def _record(self) -> None:
        index = max(0, self.scenario_box.current())
        scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
        scenario_name = self._scenario_names.get(scenario_id, scenario_id)
        rating_text = self.rating_var.get().strip()
        try:
            opponent_rating = int(rating_text) if rating_text else None
        except ValueError:
            opponent_rating = None
        ok, message = self.controller.record_battle(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            opponent=self.opponent_var.get(),
            result=self.result_var.get(),
            xp_delta=max(0, int(self.xp_var.get())),
            casualties=len(self._out_of_action_ids()),
            opponent_rating=opponent_rating,
            notes=self.notes_var.get(),
            out_of_action_ids=self._out_of_action_ids(),
        )
        if not ok:
            messagebox_parent = self.winfo_toplevel()
            from tkinter import messagebox

            messagebox.showerror("Cannot record battle", message, parent=messagebox_parent)
            return
        self.destroy()

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")
