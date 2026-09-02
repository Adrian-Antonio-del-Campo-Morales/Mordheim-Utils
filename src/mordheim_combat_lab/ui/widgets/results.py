"""ui.widgets.results: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from tkinter import StringVar
from tkinter import ttk


class DuelResultCards(ttk.Frame):
    """Present a ``DuelResult`` without coupling the view to the runtime."""

    def __init__(self, parent):
        super().__init__(parent)
        self.candidate = StringVar(value="—")
        self.enemy = StringVar(value="—")
        self.unresolved = StringVar(value="—")
        self._card("Candidate win rate", self.candidate, 0)
        self._card("Enemy win rate", self.enemy, 1)
        self._card("Unresolved", self.unresolved, 2)

    def _card(self, title: str, value: StringVar, column: int) -> None:
        self.columnconfigure(column, weight=1, uniform="result-cards")
        card = ttk.Frame(self, style="Card.TFrame", padding=(14, 10))
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 5, 5))
        ttk.Label(card, text=title, style="Card.Muted.TLabel").pack(anchor="w")
        ttk.Label(card, textvariable=value, style="Card.TLabel", font=("Segoe UI Semibold", 16)).pack(anchor="w", pady=(3, 0))

    def show(self, result) -> None:
        self.candidate.set(f"{result.first_win_rate:.2f}%")
        self.enemy.set(f"{result.second_win_rate:.2f}%")
        self.unresolved.set(f"{result.unresolved_rate:.2f}%")
