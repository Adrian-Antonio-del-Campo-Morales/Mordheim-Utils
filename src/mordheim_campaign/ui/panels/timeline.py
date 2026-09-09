from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.domain.models import POST_BATTLE_STEPS
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import ScrollableFrame
from mordheim_ui.i18n import tr
from mordheim_ui.icons import ui_icon


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
        tk.Label(header, text=tr('CAMPAIGN TIMELINE'), bg=COLORS["panel_deep"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        c = controller.state.campaign
        if c.is_draft:
            detail = tr('Campaign has not started yet')
        else:
            pending = c.pending_post_battle
            detail = tr('{} completed battle states').format(len(c.states) - 1)
            if pending:
                detail += tr('  ·  Battle #{} resolving').format(pending.battle_number)
        tk.Label(header, text=detail, bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))
        tk.Frame(self, bg=COLORS["border_soft"], height=1).pack(fill="x")

        scroll = ScrollableFrame(self, background=COLORS["panel_deep"])
        scroll.pack(fill="both", expand=True)
        self.scroll = scroll
        self.inner = scroll.inner
        self._selected_row: tk.Frame | None = None

        if c.is_draft:
            self._draft_node()
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
            if not c.pending_post_battle:
                self._connector()
                self._pending_battle_node(len(c.battles) + 1)
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

    def _base_node(
        self, node_id: str, icon: str, title: str, subtitle: str, *,
        major: bool, tone: str | None = None,
        action_label: str | None = None, action_command=None, action_enabled: bool = True,
    ) -> tk.Frame:
        selected = self.controller.state.selected_moment == node_id
        bg = COLORS["panel_soft"] if selected else COLORS["panel_deep"]
        row = tk.Frame(self.inner, bg=bg, cursor="hand2", highlightthickness=0)
        row.pack(fill="x")
        if selected:
            self._selected_row = row
            tk.Frame(row, bg=COLORS["accent"], width=3).pack(side="left", fill="y")
        else:
            tk.Frame(row, bg=bg, width=3).pack(side="left", fill="y")

        icon_wrap = tk.Frame(row, bg=bg, width=54, height=48)
        icon_wrap.pack(side="left")
        icon_wrap.pack_propagate(False)
        color = COLORS.get(tone or "text", COLORS["text"])
        tk.Label(
            icon_wrap, image=ui_icon(self, icon, 27 if major else 23),
            bg=bg, fg=color,
        ).pack(expand=True)

        if action_label:
            action = tk.Button(
                row, text=action_label, command=action_command,
                bg=COLORS["accent"] if action_enabled else COLORS["panel_soft"],
                fg=COLORS["bg"] if action_enabled else COLORS["muted_dark"],
                activebackground=COLORS["accent_hover"], activeforeground=COLORS["bg"],
                disabledforeground=COLORS["muted_dark"], state="normal" if action_enabled else "disabled",
                relief="flat", bd=0, highlightthickness=0, padx=10, pady=5,
                font=("Segoe UI Semibold", 8), cursor="hand2" if action_enabled else "arrow",
            )
            action._timeline_action = True
            action.pack(side="right", padx=(3, 7))

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
            if getattr(widget, "_timeline_action", False):
                continue
            widget.bind("<Button-1>", lambda _e: command())

    def _draft_node(self) -> None:
        c = self.controller.state.campaign
        subtitle = tr('{}/{} models  ·  {} gc remaining').format(c.draft_warband_member_count, c.effective_maximum_models, c.draft_treasury)
        row = self._base_node(
            "draft:0", "campaign_navigation_initial_warband", tr('INITIAL WARBAND  ·  DRAFT'), subtitle,
            major=True, tone="accent", action_label=tr('CONFIRM'),
            action_command=self.controller.commit_initial_warband,
            action_enabled=c.draft_is_legal,
        )
        self._bind(row, self.controller.select_draft)

    def _state_node(self, state, *, initial: bool = False, current: bool = False) -> None:
        if current:
            title = tr('CURRENT WARBAND')
        elif initial:
            title = tr('INITIAL STATE')
        else:
            title = tr('STATE #{}').format(state.number)
        subtitle = tr('Rating {}  ·  {}/{} models').format(state.rating, state.models, state.max_models)
        icon = "campaign_navigation_current_warband" if current else "campaign_navigation_warriors"
        row = self._base_node(state.node_id, icon, title, subtitle, major=True, tone="accent" if current else "text")
        self._bind(row, lambda n=state.number: self.controller.select_state(n))

    def _pending_battle_node(self, number: int) -> None:
        row = self._base_node(
            f"new-battle:{number}", "campaign_battle_in_progress",
            tr('BATTLE #{}  ·  IN PROGRESS').format(number),
            tr('Record the battle results to continue'),
            major=False, tone="accent", action_label=tr('ADD BATTLE'),
            action_command=lambda: self.controller.select_battle_entry(number),
        )
        self._bind(row, lambda: self.controller.select_battle_entry(number))

    def _battle_node(self, battle) -> None:
        result = battle.result.lower()
        result_tone = "success" if result == "victory" else ("danger" if result == "defeat" else "text")
        icon = "campaign_battle_victory" if result == "victory" else ("campaign_battle_defeat" if result == "defeat" else "campaign_battle_draw")
        title = tr('BATTLE #{}  ·  {}').format(battle.number, battle.result.upper())
        subtitle = f"{battle.scenario} vs. {battle.opponent}"
        row = self._base_node(f"battle:{battle.number}", icon, title, subtitle, major=False, tone=result_tone)
        self._bind(row, lambda n=battle.number: self.controller.select_battle(n))

    def _post_node(self, post) -> None:
        if post.complete:
            title = tr('POST-BATTLE #{}  ·  COMPLETE').format(post.battle_number)
            subtitle = tr('Recovery · Exploration & Income · Searches · Warband')
            tone = "muted"
        else:
            title = tr('POST-BATTLE #{}  ·  IN PROGRESS').format(post.battle_number)
            subtitle = (tr('Final Review') if post.review_open else tr('Step {}/8  ·  {}').format(post.active_step + 1, POST_BATTLE_STEPS[post.active_step]))
            tone = "accent"
        icon = "campaign_battle_completed" if post.complete else "campaign_battle_post_battle"
        row = self._base_node(
            post.node_id, icon, title, subtitle, major=False, tone=tone,
            action_label=tr('CONTINUE') if not post.complete else None,
            action_command=(lambda n=post.battle_number: self.controller.select_post_battle(n)) if not post.complete else None,
        )
        self._bind(row, lambda n=post.battle_number: self.controller.select_post_battle(n))
