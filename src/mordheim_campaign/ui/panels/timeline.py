from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import POST_BATTLE_STEPS
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import ScrollableFrame


class CampaignTimeline(tk.Frame):
    """Primary campaign navigator.

    The draft initial warband is the only editable pre-history node. Once
    committed it becomes State #0, and every later State is produced by a
    Battle + Post-Battle transition.
    """

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["panel_deep"], **kwargs)
        self.controller = controller
        self.configure(highlightthickness=1, highlightbackground=COLORS["border_soft"])

        header = tk.Frame(self, bg=COLORS["panel_deep"], padx=14, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="CAMPAIGN TIMELINE", bg=COLORS["panel_deep"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        c = controller.state.campaign
        if c.is_draft:
            detail = "Campaign has not started yet"
        else:
            pending = c.pending_post_battle
            detail = f"{len(c.states) - 1} completed battle states"
            if pending:
                detail += f"  ·  Battle #{pending.battle_number} resolving"
        tk.Label(header, text=detail, bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))
        tk.Frame(self, bg=COLORS["border_soft"], height=1).pack(fill="x")

        scroll = ScrollableFrame(self, background=COLORS["panel_deep"])
        scroll.pack(fill="both", expand=True)
        self.scroll = scroll
        self.inner = scroll.inner
        self._selected_row: tk.Frame | None = None

        if c.is_draft:
            self._draft_node()
            self._connector()
            self._future_node("○", "INITIAL STATE", "Created when the draft is committed")
        else:
            if c.states:
                self._state_node(c.states[0], initial=True, current=(c.current_state_number == 0 and not c.battles))
            for battle in c.battles:
                self._connector()
                self._battle_node(battle)
                self._connector(short=True)
                post = c.post_battle(battle.number)
                self._post_node(post)
                if post.complete:
                    state = next((s for s in c.states if s.number == battle.number), None)
                    if state:
                        self._connector()
                        self._state_node(state, current=state.number == c.current_state_number)

        footer = tk.Frame(self, bg=COLORS["panel_deep"], padx=12, pady=9)
        footer.pack(fill="x")
        if c.is_draft:
            text = "NEXT · START CAMPAIGN"
            tone = COLORS["accent"]
        else:
            pending = c.pending_post_battle
            text = f"NEXT STATE PENDING · finish Post-Battle #{pending.battle_number}" if pending else "READY FOR THE NEXT BATTLE"
            tone = COLORS["accent"] if pending else COLORS["muted"]
        tk.Label(footer, text=text, bg=COLORS["panel_deep"], fg=tone, font=("Segoe UI Semibold", 7)).pack(anchor="w")
        self.after_idle(self._reveal_selection)

    def _reveal_selection(self) -> None:
        if self._selected_row is None:
            return
        self.update_idletasks()
        total = max(1, self.inner.winfo_reqheight())
        viewport = max(1, self.scroll.canvas.winfo_height())
        scrollable = max(1, total - viewport)
        target = max(0, self._selected_row.winfo_y() - 70)
        self.scroll.canvas.yview_moveto(min(1.0, target / scrollable))

    def _connector(self, *, short: bool = False) -> None:
        row = tk.Frame(self.inner, bg=COLORS["panel_deep"], height=8 if short else 11)
        row.pack(fill="x")
        row.pack_propagate(False)
        tk.Frame(row, bg=COLORS["border"], width=1).pack(side="left", fill="y", padx=(27, 0))

    def _base_node(self, node_id: str, icon: str, title: str, subtitle: str, *, major: bool, tone: str | None = None) -> tk.Frame:
        selected = self.controller.state.selected_moment == node_id
        bg = COLORS["panel_soft"] if selected else COLORS["panel_deep"]
        row = tk.Frame(self.inner, bg=bg, cursor="hand2", highlightthickness=0)
        row.pack(fill="x")
        if selected:
            self._selected_row = row
            tk.Frame(row, bg=COLORS["accent"], width=3).pack(side="left", fill="y")
        else:
            tk.Frame(row, bg=bg, width=3).pack(side="left", fill="y")

        icon_wrap = tk.Frame(row, bg=bg, width=48, height=40 if major else 34)
        icon_wrap.pack(side="left")
        icon_wrap.pack_propagate(False)
        color = COLORS.get(tone or "text", COLORS["text"])
        tk.Label(icon_wrap, text=icon, bg=bg, fg=color, font=("Segoe UI Symbol", 11 if major else 9)).pack(expand=True)

        text = tk.Frame(row, bg=bg, pady=5 if major else 3)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=title, bg=bg, fg=COLORS["text"] if major else COLORS["muted"], font=("Segoe UI Semibold", 9 if major else 8), anchor="w").pack(fill="x")
        if subtitle:
            tk.Label(text, text=subtitle, bg=bg, fg=COLORS["muted_dark"], font=("Segoe UI", 7), anchor="w").pack(fill="x", pady=(1, 0))
        return row

    def _bind(self, row: tk.Frame, command) -> None:
        widgets = [row, *row.winfo_children()]
        for child in list(row.winfo_children()):
            widgets.extend(child.winfo_children())
        for widget in widgets:
            widget.bind("<Button-1>", lambda _e: command())

    def _draft_node(self) -> None:
        c = self.controller.state.campaign
        subtitle = f"{c.draft_model_count}/{c.maximum_models} models  ·  {c.draft_treasury} gc remaining"
        row = self._base_node("draft:0", "●", "INITIAL WARBAND  ·  DRAFT", subtitle, major=True, tone="accent")
        self._bind(row, self.controller.select_draft)

    def _future_node(self, icon: str, title: str, subtitle: str) -> None:
        row = tk.Frame(self.inner, bg=COLORS["panel_deep"], padx=3)
        row.pack(fill="x")
        icon_wrap = tk.Frame(row, bg=COLORS["panel_deep"], width=48, height=36)
        icon_wrap.pack(side="left")
        icon_wrap.pack_propagate(False)
        tk.Label(icon_wrap, text=icon, bg=COLORS["panel_deep"], fg=COLORS["muted_dark"], font=("Segoe UI Symbol", 10)).pack(expand=True)
        text = tk.Frame(row, bg=COLORS["panel_deep"], pady=4)
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=title, bg=COLORS["panel_deep"], fg=COLORS["muted_dark"], font=("Segoe UI Semibold", 8), anchor="w").pack(fill="x")
        tk.Label(text, text=subtitle, bg=COLORS["panel_deep"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), anchor="w").pack(fill="x", pady=(1, 0))

    def _state_node(self, state, *, initial: bool = False, current: bool = False) -> None:
        if current:
            title = "CURRENT WARBAND"
        elif initial:
            title = "INITIAL STATE"
        else:
            title = f"STATE #{state.number}"
        subtitle = f"Rating {state.rating}  ·  {state.models}/{state.max_models} models"
        row = self._base_node(state.node_id, "●", title, subtitle, major=True, tone="accent" if current else "text")
        self._bind(row, lambda n=state.number: self.controller.select_state(n))

    def _battle_node(self, battle) -> None:
        result_tone = "success" if battle.result.lower() == "victory" else "danger"
        title = f"BATTLE #{battle.number}  ·  {battle.result.upper()}"
        subtitle = f"{battle.scenario} vs. {battle.opponent}"
        row = self._base_node(f"battle:{battle.number}", "⚔", title, subtitle, major=False, tone=result_tone)
        self._bind(row, lambda n=battle.number: self.controller.select_battle(n))

    def _post_node(self, post) -> None:
        if post.complete:
            title = f"POST-BATTLE #{post.battle_number}  ·  COMPLETE"
            subtitle = "Recovery · Exploration & Income · Searches · Warband"
            tone = "muted"
        else:
            title = f"POST-BATTLE #{post.battle_number}  ·  IN PROGRESS"
            subtitle = ("Final Review" if post.review_open else f"Step {post.active_step + 1}/8  ·  {POST_BATTLE_STEPS[post.active_step]}")
            tone = "accent"
        row = self._base_node(post.node_id, "✦", title, subtitle, major=False, tone=tone)
        self._bind(row, lambda n=post.battle_number: self.controller.select_post_battle(n))
