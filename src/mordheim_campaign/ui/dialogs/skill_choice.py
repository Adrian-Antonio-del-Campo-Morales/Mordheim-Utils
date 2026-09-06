from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame
from mordheim_ui.i18n import tr


class SkillChoiceDialog(tk.Toplevel):
    """Pick one KB skill (or lore spell) to commit a choose-one advance.

    Lists the warrior's KB skill tables and marks known skills; spells list
    the warrior's lore and mark known spells. COMMIT validates through the
    engine (duplicates, tables, lore) and reports its message. Promotion mode
    (Lad's Got Talent) commits through ``commit_promotion_skill`` instead.
    """

    def __init__(self, parent: tk.Misc, engine: PostBattleEngine, warrior_id: str, *, want_spells: bool, promotion: bool = False) -> None:
        super().__init__(parent)
        self.engine = engine
        self.warrior_id = warrior_id
        self.want_spells = want_spells
        self.promotion = promotion

        warrior = next((row for row in engine.campaign.warriors if row.id == warrior_id), None)
        if warrior is None:
            self.destroy()
            return

        self.configure(bg=COLORS["bg"])
        self.title(tr('Commit Spell') if want_spells else tr('Promotion Skill') if promotion else tr('Commit Skill'))
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=18, pady=18)
        body = outer.body
        body.configure(padx=20, pady=18)

        if promotion:
            heading = tr('PROMOTION SKILL PICK')
        elif want_spells:
            heading = tr('COMMIT A NEW SPELL')
        else:
            heading = tr('COMMIT A NEW SKILL')
        subtitle = (
            tr('{} chooses one option of this advance. Known entries are listed but cannot be re-picked.').format(warrior.name)
        )
        tk.Label(body, text=heading, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w")
        tk.Label(body, text=subtitle, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=420, justify="left").pack(anchor="w", pady=(4, 12))

        entries = self._spell_entries(warrior.profile_id) if want_spells else self._skill_entries(warrior)
        self._listbox = tk.Listbox(
            body, height=min(10, max(4, len(entries))), width=58,
            bg=COLORS["entry"], fg=COLORS["text"],
            selectbackground=COLORS["accent"], selectforeground=COLORS["black"],
            highlightthickness=1, highlightbackground=COLORS["border_soft"],
            bd=0, font=("Segoe UI", 9), activestyle="none",
        )
        self._listbox.pack(fill="x")
        for spell_id, label in entries:
            self._listbox.insert("end", label)
            if label.startswith("✓"):
                self._listbox.itemconfig("end", fg=COLORS["muted"])
        if entries:
            self._listbox.selection_set(0)
        self._entries = entries

        self._detail_var = tk.StringVar()
        tk.Label(
            body, textvariable=self._detail_var, bg=COLORS["panel"], fg=COLORS["muted"],
            font=("Segoe UI", 8), justify="left", wraplength=430,
        ).pack(anchor="w", pady=(10, 0))

        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(16, 0))
        ttk.Button(actions, text=tr('Cancel'), command=self.destroy).pack(side="right", padx=(0, 6))
        ttk.Button(actions, text="COMMIT", style="Accent.TButton", command=self._commit).pack(side="right")

        self._listbox.bind("<<ListboxSelect>>", lambda _e: self._update_detail())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._update_detail()
        self.after_idle(self._center)

    # ---------------------------------------------------------------- helpers

    def _spell_entries(self, profile_id: str) -> list[tuple[str, str]]:
        lore = self.engine.port.wizard_lore(profile_id, self.engine.campaign.band_id)
        if lore is None:
            return []
        warrior = next(row for row in self.engine.campaign.warriors if row.id == self.warrior_id)
        entries: list[tuple[str, str]] = []
        for spell in self.engine.port.lore_spells(lore):
            spell_id = str(spell.get("id") or "")
            name = str(spell.get("name") or spell_id)
            known = name in warrior.skills
            label = f"✓ {name}" if known else tr('  {}  ·  difficulty {}').format(name, spell.get('difficulty', '?'))
            entries.append((spell_id, label))
        return entries

    def _skill_entries(self, warrior) -> list[tuple[str, str]]:
        allowed = set(self.engine.promotion_hero_tables(self.warrior_id) or ()) if self.promotion else set(warrior.skill_access or ())
        entries: list[tuple[str, str]] = []
        for skill in self.engine.port.skills():
            name = str(skill.get("name") or "")
            table = self.engine.port.skill_table_label(skill)
            if allowed and table not in allowed:
                continue
            known = name in warrior.skills
            label = f"✓ {name}" if known else f"[{table}]  {name}"
            entries.append((name, label))
        entries.sort(key=lambda entry: entry[1])
        return entries

    def _update_detail(self, _event=None) -> None:
        selection = self._listbox.curselection()
        if not selection:
            self._detail_var.set("")
            return
        _payload, label = self._entries[selection[0]]
        if label.startswith("✓"):
            self._detail_var.set(tr('Already known — pick a different entry.'))
            return
        if self.want_spells:
            lore = self.engine.port.wizard_lore(
                next(row.profile_id for row in self.engine.campaign.warriors if row.id == self.warrior_id),
                self.engine.campaign.band_id,
            )
            spells = self.engine.port.lore_spells(lore) if lore else ()
            index = selection[0]
            summary = str(spells[index].get("summary") or "") if index < len(spells) else ""
            self._detail_var.set(summary)
        else:
            _payload, label = self._entries[selection[0]]
            name = label.split("]  ", 1)[-1]
            skill = self.engine.port.skill_by_name(name)
            self._detail_var.set(str(skill.get("summary") or "") if skill else "")

        # Keep the detail text honest for known entries (they cannot be picked).
        if self._listbox.get(selection[0]).startswith("✓"):
            self._detail_var.set(tr('Already known — pick a different entry.'))

    def _commit(self) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        payload, label = self._entries[selection[0]]
        if label.startswith("✓"):
            return
        if self.promotion:
            ok, message = self.engine.commit_promotion_skill(self.warrior_id, payload)
            if not ok:
                self._detail_var.set(message)
                return
            self.destroy()
            return
        if self.want_spells:
            ok, message = self.engine.commit_pending_advance(self.warrior_id, option_kind="generate_spell", spell_id=payload)
        else:
            ok, message = self.engine.commit_pending_advance(self.warrior_id, option_kind="choose_skill", skill_name=payload)
        if not ok:
            self._detail_var.set(message)
            return
        self.destroy()

    def _center(self) -> None:  # mirrors AddWarriorDialog._center
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")
