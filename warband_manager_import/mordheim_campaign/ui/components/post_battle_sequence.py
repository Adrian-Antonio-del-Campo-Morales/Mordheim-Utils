from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Sequence

from mordheim_ui.theme import COLORS


class _StepDot(tk.Canvas):
    """Compact state marker used inside one post-battle chapter."""

    def __init__(self, master: tk.Misc, number: int, *, state: str, **kwargs) -> None:
        bg = master.cget("bg")
        super().__init__(master, width=23, height=23, bg=bg, bd=0, highlightthickness=0, **kwargs)
        if state == "complete":
            fill, outline, fg, text = COLORS["success_dark"], COLORS["success"], COLORS["success"], "✓"
        elif state == "active":
            fill, outline, fg, text = COLORS["accent_dark"], COLORS["accent"], COLORS["white"], str(number)
        else:
            fill, outline, fg, text = COLORS["panel_soft"], COLORS["border"], COLORS["muted_dark"], str(number)
        self.create_oval(2, 2, 21, 21, fill=fill, outline=outline, width=2)
        self.create_text(11.5, 11.5, text=text, fill=fg, font=("Segoe UI Semibold", 7))


class PostBattleSequence(tk.Frame):
    """Four-chapter, eight-step post-battle progress navigator.

    The interface deliberately exposes eight user actions rather than mirroring
    every bookkeeping line in the source sequence. Rare-item and Dramatis
    searches share one UI phase, while warband rating is derived automatically
    and appears in the final review instead of becoming a user task.
    """

    def __init__(
        self,
        master: tk.Misc,
        steps: Sequence[str],
        groups: Sequence[tuple[str, Sequence[int]]],
        active_index: int,
        completed: set[int] | None = None,
        on_select: Callable[[int], None] | None = None,
        *,
        review_active: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(
            master,
            bg=COLORS["panel_deep"],
            highlightthickness=1,
            highlightbackground=COLORS["border_soft"],
            **kwargs,
        )
        self.steps = list(steps)
        self.groups = [(title, tuple(indices)) for title, indices in groups]
        self.active_index = active_index
        self.completed = completed or set()
        self.on_select = on_select
        self.review_active = review_active
        self._build()

    def _step_state(self, index: int) -> str:
        if index in self.completed:
            return "complete"
        if not self.review_active and index == self.active_index:
            return "active"
        return "future"

    def _build(self) -> None:
        head = tk.Frame(self, bg=COLORS["panel_deep"], padx=14, pady=9)
        head.pack(fill="x")
        if self.review_active:
            kicker = "SEQUENCE COMPLETE"
            title = "FINAL REVIEW"
            status = "8 / 8 ACTIONS COMPLETE"
        else:
            kicker = f"STEP {self.active_index + 1} OF {len(self.steps)}"
            title = self.steps[self.active_index].upper()
            remaining = len(self.steps) - self.active_index - 1
            status = "FINAL ACTION" if remaining == 0 else f"{remaining} ACTIONS REMAIN"
        left = tk.Frame(head, bg=COLORS["panel_deep"])
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=kicker, bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(left, text=title, bg=COLORS["panel_deep"], fg=COLORS["text"], font=("Georgia", 13)).pack(anchor="w", pady=(2, 0))
        tk.Label(head, text=status, bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="right")

        tk.Frame(self, bg=COLORS["border_soft"], height=1).pack(fill="x")

        chapters = tk.Frame(self, bg=COLORS["panel_deep"], padx=10, pady=10)
        chapters.pack(fill="x")
        for col in range(len(self.groups)):
            chapters.columnconfigure(col * 2, weight=1, uniform="postbattle-group")

        for group_pos, (group_title, indices) in enumerate(self.groups):
            all_done = all(index in self.completed for index in indices)
            is_active_group = not self.review_active and self.active_index in indices
            group_border = COLORS["accent"] if is_active_group else (COLORS["success"] if all_done else COLORS["border_soft"])
            group = tk.Frame(
                chapters,
                bg=COLORS["panel_deep"],
                highlightthickness=1,
                highlightbackground=group_border,
                padx=10,
                pady=8,
            )
            group.grid(row=0, column=group_pos * 2, sticky="nsew")

            title_row = tk.Frame(group, bg=COLORS["panel_deep"])
            title_row.pack(fill="x", pady=(0, 6))
            title_fg = COLORS["accent"] if is_active_group else (COLORS["success"] if all_done else COLORS["muted"])
            tk.Label(title_row, text=group_title, bg=COLORS["panel_deep"], fg=title_fg, font=("Segoe UI Semibold", 7)).pack(side="left")
            if all_done:
                tk.Label(title_row, text="DONE", bg=COLORS["panel_deep"], fg=COLORS["success"], font=("Segoe UI Semibold", 6)).pack(side="right")
            elif is_active_group:
                tk.Label(title_row, text="CURRENT", bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 6)).pack(side="right")

            for index in indices:
                state = self._step_state(index)
                row = tk.Frame(
                    group,
                    bg=COLORS["panel_deep"],
                    cursor="hand2" if state in {"complete", "active"} and self.on_select else "arrow",
                )
                row.pack(fill="x", pady=2)
                _StepDot(row, index + 1, state=state).pack(side="left")
                text = tk.Frame(row, bg=COLORS["panel_deep"])
                text.pack(side="left", fill="x", expand=True, padx=(6, 0))
                fg = COLORS["success"] if state == "complete" else (COLORS["accent"] if state == "active" else COLORS["muted_dark"])
                tk.Label(text, text=self.steps[index].upper(), bg=COLORS["panel_deep"], fg=fg, font=("Segoe UI Semibold", 7), anchor="w").pack(fill="x")
                if state == "complete":
                    status_text = "COMPLETE"
                elif state == "active":
                    status_text = "IN PROGRESS"
                elif index == self.active_index + 1 and not self.review_active:
                    status_text = "NEXT"
                else:
                    status_text = "LOCKED"
                tk.Label(text, text=status_text, bg=COLORS["panel_deep"], fg=COLORS["muted_dark"], font=("Segoe UI", 6), anchor="w").pack(fill="x")
                if state in {"complete", "active"} and self.on_select:
                    self._bind_all(row, lambda i=index: self.on_select(i))

            if group_pos < len(self.groups) - 1:
                connector = tk.Frame(chapters, bg=COLORS["panel_deep"], width=28)
                connector.grid(row=0, column=group_pos * 2 + 1, sticky="nsew")
                connector.grid_propagate(False)
                tk.Label(
                    connector,
                    text="→",
                    bg=COLORS["panel_deep"],
                    fg=COLORS["success"] if all_done else COLORS["border"],
                    font=("Segoe UI Symbol", 13),
                ).place(relx=.5, rely=.55, anchor="center")

        if self.review_active:
            review = tk.Frame(self, bg=COLORS["panel_deep"], padx=12, pady=0)
            review.pack(fill="x", pady=(0, 9))
            tk.Label(
                review,
                text="✓  FINAL REVIEW IS AN APP CONFIRMATION, NOT AN ADDITIONAL POST-BATTLE RULE STEP",
                bg=COLORS["panel_deep"], fg=COLORS["success"], font=("Segoe UI Semibold", 7),
            ).pack(anchor="center")

    @staticmethod
    def _bind_all(widget: tk.Misc, command: Callable[[], None]) -> None:
        widget.bind("<Button-1>", lambda _e: command())
        for child in widget.winfo_children():
            PostBattleSequence._bind_all(child, command)
