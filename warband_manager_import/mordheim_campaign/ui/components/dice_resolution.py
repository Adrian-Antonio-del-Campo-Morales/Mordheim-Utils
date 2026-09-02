from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable, Sequence

from mordheim_ui.theme import COLORS


class DiceResolutionCard(tk.Frame):
    """Prototype interaction for any post-battle decision that needs dice.

    The card always starts unresolved. The player chooses whether the app rolls
    or whether physical dice are entered manually. This keeps the UI neutral
    about how people prefer to play at the table.
    """

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        subtitle: str,
        notation: str,
        dice_count: int,
        demo_dice: Sequence[int],
        combine: str = "sum",
        outcome_title: str = "",
        outcome_detail: str = "",
        choices: Sequence[str] | None = None,
        outcome_tone: str = "accent",
        outcome_actions: Sequence[tuple[str, Callable[[], None], str]] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border_soft"], **kwargs)
        self.notation = notation
        self.dice_count = dice_count
        self.demo_dice = list(demo_dice)
        self.combine = combine
        self.outcome_title = outcome_title
        self.outcome_detail = outcome_detail
        self.choices = list(choices or [])
        self.outcome_tone = outcome_tone
        self.outcome_actions = list(outcome_actions or [])
        self.manual_vars = [tk.IntVar(value=self.demo_dice[i] if i < len(self.demo_dice) else 1) for i in range(dice_count)]

        header = tk.Frame(self, bg=COLORS["panel_alt"], padx=13, pady=10)
        header.pack(fill="x")
        left = tk.Frame(header, bg=COLORS["panel_alt"])
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=title, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        tk.Label(left, text=subtitle, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
        tk.Label(header, text=notation, bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8), padx=9, pady=4).pack(side="right")

        tk.Frame(self, bg=COLORS["border_soft"], height=1).pack(fill="x")
        self.body = tk.Frame(self, bg=COLORS["panel_alt"], padx=13, pady=11)
        self.body.pack(fill="x")
        self._show_method_choice()

    def _clear_body(self) -> None:
        for child in self.body.winfo_children():
            child.destroy()

    def _show_method_choice(self) -> None:
        self._clear_body()
        tk.Label(
            self.body,
            text="HOW DO YOU WANT TO RESOLVE THIS ROLL?",
            bg=COLORS["panel_alt"], fg=COLORS["muted"],
            font=("Segoe UI Semibold", 7),
        ).pack(anchor="w", pady=(0, 8))
        actions = tk.Frame(self.body, bg=COLORS["panel_alt"])
        actions.pack(anchor="w")
        ttk.Button(actions, text="🎲  ROLL IN APP", style="Accent.TButton", command=self._roll_in_app).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="ENTER MANUALLY", command=self._show_manual_entry).pack(side="left")
        tk.Label(
            self.body,
            text="You can use physical dice at the table and enter exactly what you rolled.",
            bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7),
        ).pack(anchor="w", pady=(8, 0))

    def _show_manual_entry(self) -> None:
        self._clear_body()
        top = tk.Frame(self.body, bg=COLORS["panel_alt"])
        top.pack(fill="x")
        tk.Label(top, text=f"ENTER {self.notation} RESULT", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8)).pack(side="left")
        ttk.Button(top, text="CHANGE METHOD", style="Mini.TButton", command=self._show_method_choice).pack(side="right")

        dice = tk.Frame(self.body, bg=COLORS["panel_alt"])
        dice.pack(anchor="w", pady=(10, 10))
        for index, variable in enumerate(self.manual_vars, start=1):
            field = tk.Frame(dice, bg=COLORS["panel_alt"])
            field.pack(side="left", padx=(0, 8))
            if self.dice_count > 1:
                tk.Label(field, text=f"DIE {index}", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 6)).pack(anchor="w")
            ttk.Spinbox(field, from_=1, to=6, width=4, textvariable=variable).pack(anchor="w", pady=(2, 0))
        ttk.Button(dice, text="USE RESULT", style="Accent.TButton", command=self._accept_manual).pack(side="left", padx=(6, 0), pady=(12 if self.dice_count > 1 else 0, 0))

    def _roll_in_app(self) -> None:
        # Deterministic demo values keep screenshots/reviews reproducible. The
        # real implementation will swap this for the campaign dice service.
        self._show_result(self.demo_dice, source="Rolled in app")

    def _accept_manual(self) -> None:
        self._show_result([max(1, min(6, int(var.get()))) for var in self.manual_vars], source="Entered manually")

    def _format_value(self, dice: Sequence[int]) -> str:
        if self.combine == "d66":
            return "".join(str(value) for value in dice[:2])
        if self.combine == "list":
            return "  ".join(str(value) for value in dice)
        return str(sum(dice))

    def _show_result(self, dice: Sequence[int], *, source: str) -> None:
        self._clear_body()
        header = tk.Frame(self.body, bg=COLORS["panel_alt"])
        header.pack(fill="x")
        tk.Label(header, text=source.upper(), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="left")
        ttk.Button(header, text="ROLL AGAIN / EDIT", style="Mini.TButton", command=self._show_method_choice).pack(side="right")

        result = tk.Frame(self.body, bg=COLORS["panel_alt"])
        result.pack(fill="x", pady=(8, 4))
        tk.Label(result, text=f"{self.notation}  {self._format_value(dice)}", bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Georgia", 14), padx=12, pady=6).pack(side="left")
        if self.outcome_title:
            outcome = tk.Frame(result, bg=COLORS["panel_alt"])
            outcome.pack(side="left", padx=(12, 0))
            tk.Label(outcome, text=self.outcome_title.upper(), bg=COLORS["panel_alt"], fg=COLORS.get(self.outcome_tone, COLORS["accent"]), font=("Segoe UI Semibold", 9)).pack(anchor="w")
            if self.outcome_detail:
                tk.Label(outcome, text=self.outcome_detail, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

        if self.choices:
            tk.Label(self.body, text="CHOOSE THE RESULT", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(anchor="w", pady=(8, 5))
            row = tk.Frame(self.body, bg=COLORS["panel_alt"])
            row.pack(anchor="w")
            for label in self.choices:
                ttk.Button(row, text=label, style="Mini.TButton").pack(side="left", padx=(0, 6))

        if self.outcome_actions:
            actions = tk.Frame(self.body, bg=COLORS["panel_alt"])
            actions.pack(fill="x", pady=(10, 0))
            tk.Label(actions, text="AVAILABLE ACTION", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="left")
            for label, callback, style in reversed(self.outcome_actions):
                ttk.Button(actions, text=label, style=style, command=callback).pack(side="right", padx=(6, 0))
