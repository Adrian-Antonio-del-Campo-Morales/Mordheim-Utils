from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.state import WarriorVM
from mordheim_campaign.ui.equipment_display import equipment_quantity_suffix
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ExperienceTrack
from mordheim_ui.i18n import tr


_INJURY_BY_CHARACTERISTIC = {
    "M": "Leg Wound", "T": "Chest Wound", "BS": "Blinded In One Eye",
    "I": "Nervous Condition", "WS": "Hand Injury",
}


def effective_stat(warrior: WarriorVM, key: str) -> int:
    return int(warrior.stats.get(key, 0)) + int(warrior.stat_modifiers.get(key, 0))


def injury_lines(warrior: WarriorVM) -> list[str]:
    """Human-readable injury summary lines; the fixed prefix is translated."""
    lines = []
    recorded_totals: dict[str, int] = {}
    for record in warrior.injury_records:
        key = str(record.get("characteristic") or "")
        modifier = int(record.get("modifier") or 0)
        name = str(record.get("name") or _INJURY_BY_CHARACTERISTIC.get(key) or tr("Lasting Injury"))
        lines.append(tr("Injury: {} · {} {}").format(name, modifier, key))
        recorded_totals[key] = recorded_totals.get(key, 0) + modifier
    for key, modifier in warrior.stat_modifiers.items():
        remainder = int(modifier) - recorded_totals.get(key, 0)
        if remainder:
            lines.append(tr("Injury: {} · {} {}").format(
                tr(_INJURY_BY_CHARACTERISTIC.get(key, "Lasting Injury")), remainder, key))
    known_names = [str(record.get("name") or "") for record in warrior.injury_records]
    known_names.extend(_INJURY_BY_CHARACTERISTIC.get(key, "") for key, value in warrior.stat_modifiers.items() if value)
    if warrior.condition_detail and not any(name and name.casefold() in warrior.condition_detail.casefold() for name in known_names):
        detail = warrior.condition_detail.rsplit(".", 1)[-1].replace("-", " ").strip()
        lines.append(tr("Injury: {}").format(detail))
    if warrior.games_to_miss > 0:
        name = warrior.absence_reason or tr("Recovery")
        lines.append(tr("Injury: {} · misses {} more battle(s)").format(name, warrior.games_to_miss))
    for target in warrior.hatreds:
        lines.append(tr("Injury: Bitter Enmity · Hatred: {}").format(target))
    for check in warrior.battle_start_checks:
        if check.get("check_id") == "campaign.check.old-battle-wound":
            lines.append(tr("Injury: Old Battle Wound · roll D6 before each battle; misses it on 1"))
    if warrior.lost_eyes:
        lines.append(tr("Injury: Blinded In One Eye · lost {} eye").format(", ".join(warrior.lost_eyes)))
    return list(dict.fromkeys(lines))


class WarriorCard(BorderedFrame):
    def __init__(self, master: tk.Misc, warrior: WarriorVM, *, on_edit=None, **kwargs) -> None:
        super().__init__(master, background=COLORS["panel_alt"], padding=1, **kwargs)
        self.warrior = warrior
        card = self.body

        header = tk.Frame(card, bg=COLORS["panel_deep"], height=38)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=warrior.name.upper(), bg=COLORS["panel_deep"], fg=COLORS["text"], font=("Georgia", 11, "bold"), padx=11).pack(side="left", fill="y")
        label = warrior.profile_name if warrior.kind == "hero" else tr('{} · {} members').format(warrior.profile_name, warrior.quantity)
        tk.Label(header, text=label, bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=8)
        ttk.Button(header, text="•••", style="Mini.TButton", command=on_edit).pack(side="right", padx=7, pady=5)
        if warrior.condition:
            tk.Label(header, text=warrior.condition.upper(), bg=COLORS["panel_deep"], fg=COLORS["danger"], font=("Segoe UI Semibold", 8)).pack(side="right", padx=8)

        body = tk.Frame(card, bg=COLORS["panel_alt"])
        body.pack(fill="x")
        body.columnconfigure(0, weight=40)
        body.columnconfigure(1, weight=28)
        body.columnconfigure(2, weight=32)

        identity = tk.Frame(body, bg=COLORS["panel_alt"], padx=11, pady=9)
        identity.grid(row=0, column=0, sticky="nsew")
        stats = tk.Frame(identity, bg=COLORS["border_soft"])
        stats.pack(fill="x")
        keys = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")
        for i, key in enumerate(keys):
            stats.columnconfigure(i, weight=1)
            tk.Label(stats, text=key, bg=COLORS["black"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7), pady=3).grid(row=0, column=i, sticky="ew", padx=(1 if i else 0, 0))
            value = effective_stat(warrior, key)
            changed = bool(warrior.stat_modifiers.get(key))
            tk.Label(stats, text=str(value), bg=COLORS["panel_soft"], fg=COLORS["danger"] if changed else COLORS["text"], font=("Segoe UI Semibold" if changed else "Segoe UI", 9), pady=4).grid(row=1, column=i, sticky="ew", padx=(1 if i else 0, 0), pady=(1, 0))

        exp = tk.Frame(identity, bg=COLORS["panel_alt"])
        exp.pack(fill="x", pady=(8, 0))
        previous = warrior.previous_experience if warrior.previous_experience is not None else warrior.experience
        tk.Label(exp, text=tr('EXP  {} → {}').format(previous, warrior.experience) if previous != warrior.experience else f"EXP  {warrior.experience}", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        ExperienceTrack(exp, warrior.experience, previous_experience=previous, track_type=warrior.kind).pack(fill="x", pady=(3, 0))
        equip = tk.Frame(body, bg=COLORS["panel_alt"], padx=12, pady=9)
        equip.grid(row=0, column=1, sticky="nsew", padx=(1, 0))
        tk.Label(equip, text=tr('EQUIPMENT'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        for item in warrior.equipment[:5]:
            suffix = equipment_quantity_suffix(warrior, item)
            tk.Label(equip, text=f"• {item.name}{suffix}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=1)
            for rule in item.special_rules:
                tk.Label(equip, text=f"  {rule}", bg=COLORS["panel_alt"], fg=COLORS["accent"],
                         font=("Segoe UI", 7), anchor="w", wraplength=300, justify="left").pack(fill="x")

        skills = tk.Frame(body, bg=COLORS["panel_alt"], padx=12, pady=9)
        skills.grid(row=0, column=2, sticky="nsew", padx=(1, 0))
        tk.Label(skills, text=tr('SKILLS / INJURIES'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        if warrior.skills:
            for skill in warrior.skills[:5]:
                tk.Label(skills, text=f"• {skill}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=1)
        else:
            tk.Label(skills, text=tr("None"), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        for line in injury_lines(warrior):
            tk.Label(
                skills, text=f"• {line}", bg=COLORS["panel_alt"], fg=COLORS["danger"],
                font=("Segoe UI", 8), anchor="w", wraplength=300, justify="left",
            ).pack(fill="x", pady=1)
        for rule in warrior.special_rules:
            tk.Label(skills, text=f"• {rule}", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI", 8), anchor="w", wraplength=300, justify="left").pack(fill="x", pady=1)
