"""Tkinter graphical interface for the simulator."""

import os
import json
import math
import multiprocessing
import queue
import random
import re
import threading
import time
import tkinter as tk
import unicodedata
from datetime import datetime
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from itertools import combinations, combinations_with_replacement
from pathlib import Path
from tkinter import filedialog, font as tkfont, messagebox, ttk

import numpy as np

from .engine import (
    ENEMY_VARIANTS_PER_PROFILE,
    SimulationCancelled,
    _generate_shared_enemy_selection,
    effective_fighter_key,
    run_task_batch,
    run_single_task_optimized,
)
from .enemies import DIFFICULTIES, ENEMY_PROFILES, profiles_for_difficulties
from .candidate_catalog import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    bands_for_categories,
    GENERAL_SKILL_CATEGORIES,
    GENERAL_SKILL_DESCRIPTIONS,
    armour_descriptions,
    equipment_costs_for_profile,
    equipment_options_for_profile,
    find_profile,
    load_bands,
    usable_main_weapons,
    usable_offhand_options,
    weapon_descriptions,
)
from .units import format_movement
from .rules import *
from .workbooks import (
    CATALOG_SCHEMA_VERSION,
    FORMAT_VERSION,
    CandidateWorkbookError,
    load_candidate_workbook,
    save_candidate_workbook,
)


# Tk on Windows can flood the event loop with Configure events while
# dragging the main window. A small movement-only delay lets pending
# geometry events coalesce and keeps complex tabs responsive.
WINDOW_MOVE_THROTTLE_MS = 12 if os.name == "nt" else 0

COMBAT_MODES = (
    ("Single", "Weapon + Free Hand"),
    ("Shield", "Weapon and Shield"),
    ("Dual", "Two Weapons"),
    ("TwoHand", "Double-Handed Weapon"),
)
DELTA_POSITIVE = "#16833b"
DELTA_NEGATIVE = "#c62828"
DELTA_NEUTRAL = "#666666"
DEFAULT_COMBO_SIMULATIONS = 100_000
PROGRESS_POLL_MS = 100
PROGRESS_ANIMATION_MS = 60
TASK_GROUP_SIZE = 2
MOTTA_CONSTANT = 507.4
MOTTA_COST_FLOOR = 0.01
CATALOG_CATEGORY_LABELS = {
    "en": {"all": "All", "core": "Core", "1a": "1A", "1b": "1B", "1c": "1C", "trollheim": "Trollheim"},
    "es": {"all": "Todas", "core": "Básicas", "1a": "1A", "1b": "1B", "1c": "1C", "trollheim": "Trollheim"},
}
SELECTABLE_CATEGORIES = ("core", "1a", "1b", "1c", "trollheim")
UI_TEXT = {
    "en": {
        "subtitle": "Simulation Workbook", "catalog": "Catalog:", "language": "Language:",
        "import": "Import ▾", "load_candidate": "Load Candidate", "load_enemies": "Load Enemies",
        "load": "Load", "save": "Save", "candidate": "Candidate", "enemy": "Enemy",
        "combos": "Improvements", "weapons": "Weapons", "equipment": "Equipment",
        "house_rules": "House Rules", "identity": " Identity and Source ", "name": "Name:",
        "warband": "Warband:", "warrior": "Warrior:", "free_selection": "Free Selection",
        "selected_categories": "{count} selected", "movement": "Movement",
    },
    "es": {
        "subtitle": "Libro de simulación", "catalog": "Catálogo:", "language": "Idioma:",
        "import": "Importar ▾", "load_candidate": "Cargar candidato", "load_enemies": "Cargar enemigos",
        "load": "Cargar", "save": "Guardar", "candidate": "Candidato", "enemy": "Enemigo",
        "combos": "Mejoras", "weapons": "Armas", "equipment": "Equipo",
        "house_rules": "Reglas de la casa", "identity": " Identidad y procedencia ", "name": "Nombre:",
        "warband": "Banda:", "warrior": "Guerrero:", "free_selection": "Selección libre",
        "selected_categories": "{count} seleccionadas", "movement": "Movimiento",
    },
}


def _settings_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "Mordheim Combat Lab" / "settings.json"


def _load_preferences() -> dict:
    try:
        value = json.loads(_settings_path().read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_preferences(locale: str, categories) -> None:
    path = _settings_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"locale": locale, "categories": sorted(categories)}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass

# ---------------------------------------------------------------------
# Visual theme
# ---------------------------------------------------------------------

COLORS = {
    "bg": "#17191D",
    "surface": "#202329",
    "surface_alt": "#272B32",
    "surface_hover": "#30353D",
    "border": "#383D46",
    "border_light": "#454B56",
    "text": "#EEEDE8",
    "text_muted": "#A6ABB3",
    "text_disabled": "#686D75",
    "accent": "#B68A4A",
    "accent_hover": "#C99A55",
    "accent_pressed": "#9F743B",
    "danger": "#B94A48",
    "danger_hover": "#CC5754",
    "success": "#4E9668",
    "warning": "#C69A4B",
    "selection": "#343B45",
}


def _configure_simulation_worker():
    """Let Windows service the interface before compute-heavy worker processes."""
    if os.name != "nt":
        return
    try:
        import ctypes

        below_normal_priority = 0x00004000
        process = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetPriorityClass(
            process, below_normal_priority
        )
    except (AttributeError, OSError):
        pass

# Tooltips

class ToolTip:

    def __init__(
        self,
        widget,
        text,
    ):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget._tooltip_attached = True

        self.widget.bind(
            "<Enter>",
            self.show_tip,
            add="+",
        )

        self.widget.bind(
            "<Leave>",
            self.hide_tip,
            add="+",
        )

    def show_tip(
        self,
        event=None,
    ):
        text = self.text() if callable(self.text) else self.text
        if self.tip_window or not text:
            return

        try:
            box = self.widget.bbox("insert")
        except (AttributeError, tk.TclError):
            box = None
        x, y, _cx, cy = box or (0, 0, 0, 0)

        x = (
            x
            + self.widget.winfo_rootx()
            + 25
        )

        y = (
            y
            + self.widget.winfo_rooty()
            + 20
        )

        self.tip_window = tw = tk.Toplevel(
            self.widget
        )

        tw.wm_overrideredirect(True)

        tw.wm_geometry(
            f"+{x}+{y}"
        )

        label = tk.Label(
            tw,
            text=text,
            justify=tk.LEFT,
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLORS["border_light"],
            font=("Segoe UI", 9, "normal"),
            wraplength=420,
        )

        label.pack(
            ipadx=4,
            ipady=2,
        )

    def hide_tip(
        self,
        event=None,
    ):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class TreeviewToolTip:
    """Contextual help for headings and cells, with row highlighting."""

    def __init__(self, tree, explanations=None, rule_resolver=None):
        self.tree = tree
        self.explanations = explanations or {}
        self.rule_resolver = rule_resolver
        self.tip_window = None
        self.tip_label = None
        self.last_target = None
        self.hover_item = None
        tree._tooltip_attached = True
        tree.tag_configure("__hover_help__", background=COLORS["selection"])
        tree.bind("<Motion>", self._motion, add="+")
        tree.bind("<Leave>", self._leave, add="+")

    def _column(self, x):
        token = self.tree.identify_column(x)
        if not token or token == "#0":
            return None
        index = int(token[1:]) - 1
        displayed = self.tree.cget("displaycolumns")
        columns = (
            tuple(self.tree.cget("columns"))
            if displayed == "#all" else tuple(displayed)
        )
        return columns[index] if 0 <= index < len(columns) else None


    def _motion(self, event):
        region = self.tree.identify_region(event.x, event.y)
        column = self._column(event.x)
        item = (
            self.tree.identify_row(event.y)
            if region in ("cell", "tree")
            else ""
        )

        self._highlight(item)

        if region == "heading" and column:
            target = ("heading", column)

            if target == self.last_target:
                return

            title = self.tree.heading(column).get("text", column)
            text = self.explanations.get(
                column,
                f"Click to sort by “{title}”.",
            )

        elif item and column:
            target = (item, column)

            # Do not rebuild rule descriptions on every mouse pixel while
            # remaining inside the same cell.
            if target == self.last_target:
                return

            title = self.tree.heading(column).get("text", column)
            value = (
                self.tree.set(item, column)
                or "No value for this configuration"
            )
            detail = self.explanations.get(column, "")
            rule_detail = (
                self.rule_resolver(value)
                if self.rule_resolver
                else ""
            )
            useful_detail = rule_detail or detail
            text = (
                f"{title}: {value}"
                + (
                    f"\n{useful_detail}"
                    if useful_detail
                    else ""
                )
            )

        else:
            self._hide()
            return

        self._show(
            text,
            event.x_root + 16,
            event.y_root + 18,
        )
        self.last_target = target

    def _highlight(self, item):
        if item == self.hover_item:
            return
        if self.hover_item and self.tree.exists(self.hover_item):
            tags = tuple(t for t in self.tree.item(self.hover_item, "tags") if t != "__hover_help__")
            self.tree.item(self.hover_item, tags=tags)
        self.hover_item = item
        if item:
            tags = tuple(self.tree.item(item, "tags"))
            if "__hover_help__" not in tags:
                self.tree.item(item, tags=(*tags, "__hover_help__"))

    def _show(self, text, x, y):
        self._hide()
        self.tip_window = tw = tk.Toplevel(self.tree)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        self.tip_label = tk.Label(
            tw, text=text, justify=tk.LEFT, background=COLORS["surface_alt"], foreground=COLORS["text"],
            relief=tk.SOLID, borderwidth=1, highlightthickness=1,
            highlightbackground=COLORS["border_light"], font=("Segoe UI", 9), wraplength=460,
        )
        self.tip_label.pack(ipadx=4, ipady=2)

    def _hide(self):
        if self.tip_window:
            self.tip_window.destroy()
        self.tip_window = None
        self.tip_label = None
        self.last_target = None

    def _leave(self, _event=None):
        self._highlight("")
        self._hide()


class ToggleSwitch(tk.Canvas):
    """Small on/off switch backed by a BooleanVar."""

    def __init__(
        self,
        parent,
        variable,
        command=None,
        width=38,
        height=20,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            borderwidth=0,
            background=COLORS["surface"],
            cursor="hand2",
            **kwargs,
        )
        self.variable = variable
        self.command = command
        self._switch_width = width
        self._switch_height = height
        self._state = "normal"

        self.bind("<Button-1>", self._toggle, add="+")
        self.variable.trace_add("write", self._variable_changed)
        self._draw()

    def _variable_changed(self, *_args):
        self._draw()

    def _toggle(self, _event=None):
        if self._state == "disabled":
            return "break"

        self.variable.set(not self.variable.get())

        if self.command:
            self.command()

        return "break"

    def _draw(self):
        self.delete("all")

        width = self._switch_width
        height = self._switch_height
        radius = height // 2
        enabled = self._state != "disabled"
        selected = bool(self.variable.get())

        if not enabled:
            track = COLORS["border"]
            knob = COLORS["text_disabled"]
        elif selected:
            track = COLORS["accent"]
            knob = "#111111"
        else:
            track = COLORS["surface_hover"]
            knob = COLORS["text_muted"]

        # Rounded track.
        self.create_oval(
            1,
            1,
            height - 1,
            height - 1,
            fill=track,
            outline=track,
        )
        self.create_oval(
            width - height + 1,
            1,
            width - 1,
            height - 1,
            fill=track,
            outline=track,
        )
        self.create_rectangle(
            radius,
            1,
            width - radius,
            height - 1,
            fill=track,
            outline=track,
        )

        knob_size = height - 6
        knob_y = 3

        if selected:
            knob_x = width - knob_size - 3
        else:
            knob_x = 3

        self.create_oval(
            knob_x,
            knob_y,
            knob_x + knob_size,
            knob_y + knob_size,
            fill=knob,
            outline=knob,
        )

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        state = kwargs.pop("state", None)
        if state is not None:
            self._state = state
            super().configure(
                cursor="" if state == "disabled" else "hand2"
            )

        result = super().configure(**kwargs)
        self._draw()
        return result

    config = configure


class _ProgressStatusProxy:
    """Compatibility object exposing Label-like config(text=...)."""

    def __init__(self, progress):
        self.progress = progress

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        if "text" in kwargs:
            self.progress.set_status(kwargs["text"])

    config = configure

    def cget(self, option):
        if option == "text":
            return self.progress.status_text
        raise tk.TclError(f"unknown option {option}")


class InlineProgressBar(tk.Canvas):
    """Canvas progress bar with text rendered directly over the fill."""

    def __init__(
        self,
        parent,
        variable,
        maximum=100,
        height=30,
        **kwargs,
    ):
        super().__init__(
            parent,
            height=height,
            highlightthickness=0,
            borderwidth=0,
            background=COLORS["surface_alt"],
            **kwargs,
        )

        self.variable = variable
        self.maximum = float(maximum)
        self.mode = "determinate"
        self.status_text = "Ready"
        self._animation_after_id = None
        self._animation_position = 0.0
        self._animation_direction = 1

        self.status_proxy = _ProgressStatusProxy(self)

        self.bind("<Configure>", lambda _event: self._redraw(), add="+")
        self.variable.trace_add("write", self._variable_changed)
        self._redraw()

    def _variable_changed(self, *_args):
        if self.mode == "determinate":
            self._redraw()

    def set_status(self, text):
        self.status_text = str(text)
        self._redraw()

    def _redraw(self):
        self.delete("all")

        width = max(1, self.winfo_width())
        height = max(1, self.winfo_height())

        self.create_rectangle(
            0,
            0,
            width,
            height,
            fill=COLORS["surface_alt"],
            outline=COLORS["border"],
        )

        if self.mode == "indeterminate":
            chunk_width = max(50, int(width * 0.22))
            max_x = max(0, width - chunk_width)
            x = int(max_x * self._animation_position)

            self.create_rectangle(
                x,
                1,
                min(width, x + chunk_width),
                height - 1,
                fill=COLORS["accent"],
                outline="",
            )
        else:
            try:
                value = float(self.variable.get())
            except (TypeError, ValueError, tk.TclError):
                value = 0.0

            fraction = 0.0
            if self.maximum > 0:
                fraction = max(0.0, min(1.0, value / self.maximum))

            fill_width = int(width * fraction)

            if fill_width > 0:
                self.create_rectangle(
                    1,
                    1,
                    max(1, fill_width),
                    height - 1,
                    fill=COLORS["accent"],
                    outline="",
                )

        # Draw text directly on the canvas: there is no opaque label
        # obscuring the progress above/below/behind the text.
        self.create_text(
            width // 2,
            height // 2,
            text=self.status_text,
            fill=COLORS["text"],
            font=("Segoe UI Semibold", 9),
            anchor="center",
        )

    def start(self, interval=50):
        self.stop()
        self.mode = "indeterminate"

        def animate():
            self._animation_position += 0.035 * self._animation_direction

            if self._animation_position >= 1.0:
                self._animation_position = 1.0
                self._animation_direction = -1
            elif self._animation_position <= 0.0:
                self._animation_position = 0.0
                self._animation_direction = 1

            self._redraw()
            self._animation_after_id = self.after(interval, animate)

        animate()

    def stop(self):
        if self._animation_after_id is not None:
            try:
                self.after_cancel(self._animation_after_id)
            except tk.TclError:
                pass
            self._animation_after_id = None

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        mode = kwargs.pop("mode", None)
        maximum = kwargs.pop("maximum", None)

        if mode is not None:
            self.mode = mode
            if mode != "indeterminate":
                self.stop()

        if maximum is not None:
            self.maximum = float(maximum)

        result = super().configure(**kwargs)
        self._redraw()
        return result

    config = configure


# Editor of warriors


class SkillChecklistCanvas(tk.Canvas):
    """Compact multi-column skill selector rendered as one Tk widget.

    The existing BooleanVars remain the source of truth.  Only their visual
    representation moves from many ttk.Checkbuttons/LabelFrames to one Canvas.
    """

    HEADER_HEIGHT = 26
    ROW_HEIGHT = 22
    OUTER_PAD = 2
    CARD_GAP = 6
    CARD_PAD_X = 8
    CARD_PAD_Y = 6
    CHECK_SIZE = 13
    MIN_HEIGHT = 48
    TOOLTIP_DELAY_MS = 450

    def __init__(
        self,
        parent,
        variables,
        descriptions,
        categories,
        allowed_skills=(),
        **kwargs,
    ):
        super().__init__(
            parent,
            highlightthickness=0,
            borderwidth=0,
            background=COLORS["bg"],
            **kwargs,
        )

        self.variables = variables
        self.descriptions = descriptions
        self.categories = categories
        self.allowed_skills = frozenset()
        self._enabled = True
        self._hitboxes = []
        self._hover_skill = None
        self._redraw_after_id = None
        self._tooltip_after_id = None
        self._tooltip_window = None
        self._tooltip_label = None
        self._tooltip_position = (0, 0)
        self._tooltip_attached = True

        for variable in self.variables.values():
            variable.trace_add(
                "write",
                self._variable_changed,
            )

        self.bind(
            "<Configure>",
            self._on_configure,
            add="+",
        )
        self.bind(
            "<Motion>",
            self._on_motion,
            add="+",
        )
        self.bind(
            "<Leave>",
            self._on_leave,
            add="+",
        )
        self.bind(
            "<Button-1>",
            self._on_click,
            add="+",
        )

        self.set_allowed_skills(allowed_skills)

    def _variable_changed(self, *_args):
        self._schedule_redraw()

    def _schedule_redraw(self):
        if self._redraw_after_id is not None:
            return

        try:
            self._redraw_after_id = self.after_idle(
                self._run_scheduled_redraw
            )
        except tk.TclError:
            self._redraw_after_id = None

    def _run_scheduled_redraw(self):
        self._redraw_after_id = None
        try:
            self._redraw()
        except tk.TclError:
            pass

    def _on_configure(self, _event=None):
        self._schedule_redraw()

    def _visible_categories(self):
        grouped = {
            category: []
            for category in CATEGORY_ORDER
        }

        for skill in self.variables:
            if skill not in self.allowed_skills:
                continue

            category = self.categories.get(
                skill,
                "special",
            )

            if category not in grouped:
                category = "special"

            grouped.setdefault(
                category,
                [],
            ).append(skill)

        return [
            (category, grouped.get(category, []))
            for category in CATEGORY_ORDER
            if grouped.get(category)
        ]

    def _desired_height(self):
        visible = self._visible_categories()

        if not visible:
            return self.MIN_HEIGHT

        longest = max(
            len(skills)
            for _category, skills in visible
        )

        return max(
            self.MIN_HEIGHT,
            (
                self.OUTER_PAD * 2
                + self.CARD_PAD_Y * 2
                + self.HEADER_HEIGHT
                + longest * self.ROW_HEIGHT
            ),
        )

    def set_allowed_skills(self, allowed_skills):
        allowed = frozenset(
            skill
            for skill in allowed_skills
            if skill in self.variables
        )

        if allowed == self.allowed_skills:
            return

        self.allowed_skills = allowed
        self._hover_skill = None
        self._hide_tooltip()
        super().configure(
            height=self._desired_height()
        )
        self._schedule_redraw()

    def set_enabled(self, enabled=True):
        self._enabled = bool(enabled)
        self._hover_skill = None
        self._hide_tooltip()

        try:
            super().configure(
                cursor="" if not self._enabled else "arrow"
            )
        except tk.TclError:
            pass

        self._schedule_redraw()

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        state = kwargs.pop(
            "state",
            None,
        )

        if state is not None:
            self.set_enabled(
                state != "disabled"
            )

        result = super().configure(**kwargs)
        self._schedule_redraw()
        return result

    config = configure

    def _skill_at(self, x, y):
        for x1, y1, x2, y2, skill in self._hitboxes:
            if x1 <= x <= x2 and y1 <= y <= y2:
                return skill
        return None

    def _on_motion(self, event):
        skill = self._skill_at(
            event.x,
            event.y,
        )

        try:
            super().configure(
                cursor=(
                    "hand2"
                    if self._enabled and skill
                    else "arrow"
                )
            )
        except tk.TclError:
            pass

        if skill == self._hover_skill:
            if skill:
                self._tooltip_position = (
                    event.x_root + 16,
                    event.y_root + 18,
                )
            return

        self._hover_skill = skill
        self._hide_tooltip()

        if skill:
            self._tooltip_position = (
                event.x_root + 16,
                event.y_root + 18,
            )
            self._tooltip_after_id = self.after(
                self.TOOLTIP_DELAY_MS,
                self._show_hover_tooltip,
            )

        self._schedule_redraw()

    def _on_leave(self, _event=None):
        self._hover_skill = None
        self._hide_tooltip()

        try:
            super().configure(
                cursor="arrow"
            )
        except tk.TclError:
            pass

        self._schedule_redraw()

    def _on_click(self, event):
        if not self._enabled:
            return "break"

        skill = self._skill_at(
            event.x,
            event.y,
        )

        if not skill:
            return None

        variable = self.variables[skill]
        variable.set(
            not bool(variable.get())
        )

        return "break"

    def _show_hover_tooltip(self):
        self._tooltip_after_id = None

        skill = self._hover_skill
        if not skill:
            return

        description = self.descriptions.get(
            skill,
            "No description available.",
        )

        if not description:
            return

        try:
            x, y = self._tooltip_position

            window = tk.Toplevel(self)
            window.wm_overrideredirect(True)
            window.wm_geometry(
                f"+{x}+{y}"
            )

            label = tk.Label(
                window,
                text=description,
                justify=tk.LEFT,
                background=COLORS["surface_alt"],
                foreground=COLORS["text"],
                relief=tk.SOLID,
                borderwidth=1,
                highlightthickness=1,
                highlightbackground=COLORS["border_light"],
                font=("Segoe UI", 9),
                wraplength=420,
            )
            label.pack(
                ipadx=4,
                ipady=2,
            )

            self._tooltip_window = window
            self._tooltip_label = label

        except tk.TclError:
            self._tooltip_window = None
            self._tooltip_label = None

    def _hide_tooltip(self):
        if self._tooltip_after_id is not None:
            try:
                self.after_cancel(
                    self._tooltip_after_id
                )
            except tk.TclError:
                pass
            self._tooltip_after_id = None

        window = self._tooltip_window
        self._tooltip_window = None
        self._tooltip_label = None

        if window is not None:
            try:
                window.destroy()
            except tk.TclError:
                pass

    def _draw_checkbox(
        self,
        x,
        y,
        checked,
        enabled,
    ):
        size = self.CHECK_SIZE

        if checked and enabled:
            fill = COLORS["accent"]
            outline = COLORS["accent"]
            mark = "#111111"
        elif checked:
            fill = COLORS["border"]
            outline = COLORS["border"]
            mark = COLORS["text_disabled"]
        else:
            fill = COLORS["surface_alt"]
            outline = (
                COLORS["border_light"]
                if enabled
                else COLORS["border"]
            )
            mark = COLORS["text_disabled"]

        self.create_rectangle(
            x,
            y,
            x + size,
            y + size,
            fill=fill,
            outline=outline,
            width=1,
        )

        if checked:
            self.create_text(
                x + size / 2,
                y + size / 2 - 0.5,
                text="✓",
                fill=mark,
                font=("Segoe UI Semibold", 9),
                anchor="center",
            )

    def _redraw(self):
        self.delete("all")
        self._hitboxes = []

        width = max(
            1,
            int(self.winfo_width()),
        )
        height = max(
            self.MIN_HEIGHT,
            self._desired_height(),
        )

        visible = self._visible_categories()

        if not visible:
            self.create_text(
                6,
                height / 2,
                text=(
                    "No selectable skills are available "
                    "for this profile."
                ),
                fill=COLORS["text_muted"],
                font=("Segoe UI", 9),
                anchor="w",
            )
            return

        category_count = len(visible)
        usable_width = (
            width
            - self.OUTER_PAD * 2
            - self.CARD_GAP * (category_count - 1)
        )

        card_width = max(
            80.0,
            usable_width / category_count,
        )

        for index, (category, skills) in enumerate(visible):
            x1 = (
                self.OUTER_PAD
                + index * (card_width + self.CARD_GAP)
            )
            x2 = min(
                width - self.OUTER_PAD,
                x1 + card_width,
            )
            y1 = self.OUTER_PAD
            y2 = height - self.OUTER_PAD

            self.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=COLORS["surface"],
                outline=COLORS["border"],
                width=1,
            )

            self.create_text(
                x1 + self.CARD_PAD_X,
                y1 + self.CARD_PAD_Y + 8,
                text=CATEGORY_LABELS[category],
                fill=COLORS["text"],
                font=("Segoe UI Semibold", 10),
                anchor="w",
            )

            row_top = (
                y1
                + self.CARD_PAD_Y
                + self.HEADER_HEIGHT
            )

            for row_index, skill in enumerate(skills):
                row_y1 = (
                    row_top
                    + row_index * self.ROW_HEIGHT
                )
                row_y2 = row_y1 + self.ROW_HEIGHT

                hovered = (
                    skill == self._hover_skill
                )

                if hovered:
                    self.create_rectangle(
                        x1 + 1,
                        row_y1,
                        x2 - 1,
                        row_y2,
                        fill=COLORS["surface_hover"],
                        outline="",
                    )

                check_x = (
                    x1
                    + self.CARD_PAD_X
                )
                check_y = (
                    row_y1
                    + (
                        self.ROW_HEIGHT
                        - self.CHECK_SIZE
                    ) / 2
                )

                checked = bool(
                    self.variables[skill].get()
                )

                self._draw_checkbox(
                    check_x,
                    check_y,
                    checked,
                    self._enabled,
                )

                self.create_text(
                    check_x
                    + self.CHECK_SIZE
                    + 7,
                    row_y1 + self.ROW_HEIGHT / 2,
                    text=skill,
                    fill=(
                        COLORS["text"]
                        if self._enabled
                        else COLORS["text_disabled"]
                    ),
                    font=("Segoe UI", 9),
                    anchor="w",
                )

                self._hitboxes.append(
                    (
                        x1 + 1,
                        row_y1,
                        x2 - 1,
                        row_y2,
                        skill,
                    )
                )


class _StatValueProxy:
    """Entry-like compatibility proxy backed by StatGridCanvas."""

    def __init__(self, canvas, attribute):
        self.canvas = canvas
        self.attribute = attribute

    def get(self):
        return self.canvas.get_value(self.attribute)

    def delete(self, _first=0, _last=None):
        self.canvas.set_value(self.attribute, "")

    def insert(self, _index, value):
        self.canvas.set_value(self.attribute, value)

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)
        state = kwargs.pop("state", None)
        if state is not None:
            self.canvas.set_enabled(state != "disabled")

    config = configure


class StatGridCanvas(tk.Canvas):
    """Render all six warrior attributes as one lightweight widget."""

    HEIGHT = 70
    OUTER_PAD = 1
    GAP = 4
    CARD_PAD = 6
    CONTROL_HEIGHT = 30
    BUTTON_WIDTH = 30
    VALUE_MIN_WIDTH = 42

    def __init__(
        self,
        parent,
        values,
        **kwargs,
    ):
        super().__init__(
            parent,
            height=self.HEIGHT,
            highlightthickness=0,
            borderwidth=0,
            background=COLORS["bg"],
            cursor="arrow",
            **kwargs,
        )

        self.values = {
            key: str(value)
            for key, value in values.items()
        }
        self.attributes = tuple(values)
        self._enabled = True
        self._hitboxes = []
        self._hover_target = None
        self._editor = None
        self._editing_attribute = None
        self._redraw_after_id = None

        self.bind(
            "<Configure>",
            self._schedule_redraw,
            add="+",
        )
        self.bind(
            "<Motion>",
            self._on_motion,
            add="+",
        )
        self.bind(
            "<Leave>",
            self._on_leave,
            add="+",
        )
        self.bind(
            "<Button-1>",
            self._on_click,
            add="+",
        )

        self._schedule_redraw()

    def proxies(self):
        return {
            attribute: _StatValueProxy(
                self,
                attribute,
            )
            for attribute in self.attributes
        }

    def get_value(self, attribute):
        return self.values.get(
            attribute,
            "0",
        )

    def set_value(self, attribute, value):
        if attribute not in self.values:
            return

        self.values[attribute] = str(value)
        self._schedule_redraw()

    def change_value(self, attribute, delta):
        try:
            current = int(
                self.values.get(
                    attribute,
                    "0",
                )
            )
        except (TypeError, ValueError):
            current = 0

        self.values[attribute] = str(
            max(
                0,
                current + delta,
            )
        )
        self._schedule_redraw()

    def set_enabled(self, enabled=True):
        self._enabled = bool(enabled)

        if not self._enabled:
            self._finish_edit(
                commit=True,
            )

        try:
            super().configure(
                cursor="arrow",
            )
        except tk.TclError:
            pass

        self._hover_target = None
        self._schedule_redraw()

    def configure(self, cnf=None, **kwargs):
        if cnf:
            kwargs.update(cnf)

        state = kwargs.pop(
            "state",
            None,
        )

        if state is not None:
            self.set_enabled(
                state != "disabled"
            )

        result = super().configure(**kwargs)
        self._schedule_redraw()
        return result

    config = configure

    def _schedule_redraw(self, _event=None):
        if self._redraw_after_id is not None:
            return

        try:
            self._redraw_after_id = self.after_idle(
                self._run_scheduled_redraw
            )
        except tk.TclError:
            self._redraw_after_id = None

    def _run_scheduled_redraw(self):
        self._redraw_after_id = None

        try:
            self._redraw()
        except tk.TclError:
            pass

    def _target_at(self, x, y):
        for (
            x1,
            y1,
            x2,
            y2,
            attribute,
            action,
        ) in self._hitboxes:
            if (
                x1 <= x <= x2
                and y1 <= y <= y2
            ):
                return attribute, action

        return None

    def _on_motion(self, event):
        target = self._target_at(
            event.x,
            event.y,
        )

        if target != self._hover_target:
            self._hover_target = target
            self._schedule_redraw()

        try:
            super().configure(
                cursor=(
                    "hand2"
                    if self._enabled and target
                    else "arrow"
                )
            )
        except tk.TclError:
            pass

    def _on_leave(self, _event=None):
        if self._hover_target is not None:
            self._hover_target = None
            self._schedule_redraw()

        try:
            super().configure(
                cursor="arrow",
            )
        except tk.TclError:
            pass

    def _on_click(self, event):
        if not self._enabled:
            return "break"

        target = self._target_at(
            event.x,
            event.y,
        )

        if target is None:
            self._finish_edit(
                commit=True,
            )
            return None

        attribute, action = target

        if action == "minus":
            self._finish_edit(
                commit=True,
            )
            self.change_value(
                attribute,
                -1,
            )

        elif action == "plus":
            self._finish_edit(
                commit=True,
            )
            self.change_value(
                attribute,
                1,
            )

        elif action == "value":
            self._begin_edit(
                attribute,
            )

        return "break"

    def _value_box(self, attribute):
        for (
            x1,
            y1,
            x2,
            y2,
            current_attribute,
            action,
        ) in self._hitboxes:
            if (
                current_attribute == attribute
                and action == "value"
            ):
                return x1, y1, x2, y2

        return None

    def _ensure_editor(self):
        if self._editor is not None:
            return self._editor

        editor = ttk.Entry(
            self,
            width=4,
            justify="center",
            style="Stat.TEntry",
            font=("Segoe UI Semibold", 11),
        )

        editor.bind(
            "<Return>",
            lambda _event:
                self._finish_edit(commit=True),
            add="+",
        )

        editor.bind(
            "<Escape>",
            lambda _event:
                self._finish_edit(commit=False),
            add="+",
        )

        editor.bind(
            "<FocusOut>",
            lambda _event:
                self._finish_edit(commit=True),
            add="+",
        )

        self._editor = editor
        return editor

    def _begin_edit(self, attribute):
        box = self._value_box(attribute)
        if box is None:
            return

        self._finish_edit(
            commit=True,
        )

        editor = self._ensure_editor()
        self._editing_attribute = attribute

        editor.delete(
            0,
            tk.END,
        )
        editor.insert(
            0,
            self.values.get(
                attribute,
                "0",
            ),
        )

        x1, y1, x2, y2 = box

        editor.place(
            x=int(x1),
            y=int(y1),
            width=max(
                self.VALUE_MIN_WIDTH,
                int(x2 - x1),
            ),
            height=max(
                24,
                int(y2 - y1),
            ),
        )

        editor.focus_set()
        editor.selection_range(
            0,
            tk.END,
        )

    def _finish_edit(
        self,
        commit=True,
    ):
        editor = self._editor
        attribute = self._editing_attribute

        if (
            editor is None
            or attribute is None
        ):
            return

        if commit:
            try:
                value = max(
                    0,
                    int(
                        editor.get().strip()
                    ),
                )
            except (TypeError, ValueError):
                try:
                    value = max(
                        0,
                        int(
                            self.values.get(
                                attribute,
                                "0",
                            )
                        ),
                    )
                except (TypeError, ValueError):
                    value = 0

            self.values[attribute] = str(
                value
            )

        editor.place_forget()
        self._editing_attribute = None
        self._schedule_redraw()

    def _draw_button(
        self,
        x1,
        y1,
        x2,
        y2,
        text,
        hovered,
    ):
        if not self._enabled:
            fill = COLORS["surface"]
            foreground = COLORS["text_disabled"]
            outline = COLORS["border"]
        elif hovered:
            fill = COLORS["surface_hover"]
            foreground = COLORS["text"]
            outline = COLORS["border_light"]
        else:
            fill = COLORS["surface_alt"]
            foreground = COLORS["text"]
            outline = COLORS["border"]

        self.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=fill,
            outline=outline,
            width=1,
        )

        self.create_text(
            (x1 + x2) / 2,
            (y1 + y2) / 2 - 1,
            text=text,
            fill=foreground,
            font=("Segoe UI Semibold", 12),
            anchor="center",
        )

    def _redraw(self):
        self.delete("all")
        self._hitboxes = []

        width = max(
            1,
            int(self.winfo_width()),
        )
        height = max(
            self.HEIGHT,
            int(self.winfo_height()),
        )

        count = max(
            1,
            len(self.attributes),
        )

        usable_width = (
            width
            - self.OUTER_PAD * 2
            - self.GAP * (count - 1)
        )

        card_width = max(
            88.0,
            usable_width / count,
        )

        card_y1 = self.OUTER_PAD
        card_y2 = height - self.OUTER_PAD

        for index, attribute in enumerate(
            self.attributes
        ):
            x1 = (
                self.OUTER_PAD
                + index * (
                    card_width
                    + self.GAP
                )
            )

            x2 = min(
                width - self.OUTER_PAD,
                x1 + card_width,
            )

            self.create_rectangle(
                x1,
                card_y1,
                x2,
                card_y2,
                fill=COLORS["surface"],
                outline=COLORS["border"],
                width=1,
            )

            self.create_text(
                (x1 + x2) / 2,
                card_y1 + 13,
                text=attribute,
                fill=(
                    COLORS["text"]
                    if self._enabled
                    else COLORS["text_disabled"]
                ),
                font=("Segoe UI Semibold", 10),
                anchor="center",
            )

            controls_y1 = (
                card_y2
                - self.CONTROL_HEIGHT
                - self.CARD_PAD
            )

            controls_y2 = (
                card_y2
                - self.CARD_PAD
            )

            inner_x1 = x1 + self.CARD_PAD
            inner_x2 = x2 - self.CARD_PAD

            minus_x1 = inner_x1
            minus_x2 = (
                minus_x1
                + self.BUTTON_WIDTH
            )

            plus_x2 = inner_x2
            plus_x1 = (
                plus_x2
                - self.BUTTON_WIDTH
            )

            value_x1 = (
                minus_x2
                + 3
            )
            value_x2 = (
                plus_x1
                - 3
            )

            self._draw_button(
                minus_x1,
                controls_y1,
                minus_x2,
                controls_y2,
                "−",
                (
                    self._hover_target
                    == (
                        attribute,
                        "minus",
                    )
                ),
            )

            self._draw_button(
                plus_x1,
                controls_y1,
                plus_x2,
                controls_y2,
                "+",
                (
                    self._hover_target
                    == (
                        attribute,
                        "plus",
                    )
                ),
            )

            value_hovered = (
                self._hover_target
                == (
                    attribute,
                    "value",
                )
            )

            self.create_rectangle(
                value_x1,
                controls_y1,
                value_x2,
                controls_y2,
                fill=(
                    COLORS["surface_hover"]
                    if (
                        self._enabled
                        and value_hovered
                    )
                    else COLORS["bg"]
                ),
                outline=(
                    COLORS["accent"]
                    if (
                        self._enabled
                        and value_hovered
                    )
                    else COLORS["border"]
                ),
                width=1,
            )

            if (
                self._editing_attribute
                != attribute
            ):
                self.create_text(
                    (
                        value_x1
                        + value_x2
                    ) / 2,
                    (
                        controls_y1
                        + controls_y2
                    ) / 2,
                    text=self.values.get(
                        attribute,
                        "0",
                    ),
                    fill=(
                        COLORS["text"]
                        if self._enabled
                        else COLORS["text_disabled"]
                    ),
                    font=(
                        "Segoe UI Semibold",
                        11,
                    ),
                    anchor="center",
                )

            self._hitboxes.extend(
                (
                    (
                        minus_x1,
                        controls_y1,
                        minus_x2,
                        controls_y2,
                        attribute,
                        "minus",
                    ),
                    (
                        value_x1,
                        controls_y1,
                        value_x2,
                        controls_y2,
                        attribute,
                        "value",
                    ),
                    (
                        plus_x1,
                        controls_y1,
                        plus_x2,
                        controls_y2,
                        attribute,
                        "plus",
                    ),
                )
            )


class WarriorConfigFrame(ttk.Frame):

    def __init__(
        self,
        parent,
        title,
        show_house_rules=False,
        skill_descriptions=None,
        skill_categories=None,
    ):
        super().__init__(parent)
        self.title = title

        self.stats = {
            "WS": 4,
            "S": 3,
            "T": 3,
            "W": 1,
            "I": 4,
            "A": 1,
        }

        self.skill_descriptions = skill_descriptions or SKILL_DESCRIPTIONS
        self.skill_categories = skill_categories or {
            skill: "combat" for skill in self.skill_descriptions
        }
        self.skills = {
            s: tk.BooleanVar()
            for s in self.skill_descriptions
        }

        self.eq_main_general = tk.StringVar(value=WEAPONS_GENERAL[0])
        self.eq_main_exclusive = tk.StringVar(value="None")

        self.eq_off_general = tk.StringVar(value="None")
        self.eq_off_exclusive = tk.StringVar(value="None")

        self.eq_main_material = tk.StringVar(value=WEAPON_MATERIALS[0])
        self.eq_off_material = tk.StringVar(value=WEAPON_MATERIALS[0])
        self.eq_main_poison = tk.StringVar(value="No Poison")
        self.eq_off_poison = tk.StringVar(value="No Poison")

        self.equipment_vars = {
            name: tk.BooleanVar(value=False)
            for name in EQUIPMENT_SELECTOR_OPTIONS
        }
        self.eq_has_helmet = self.equipment_vars["Helmet"]
        self.equipment_button_text = tk.StringVar(value="None ▾")
        self._equipment_menu_indices = {}
        self._allowed_equipment = set(EQUIPMENT_SELECTOR_OPTIONS)

        self.eq_armor = tk.StringVar(
            value=BODY_ARMORS[0]
        )
        self.show_house_rules = show_house_rules
        self.house_rule_offhand_penalty = tk.BooleanVar(value=False)
        self.house_rule_dual_penalty = tk.BooleanVar(value=False)
        self.undead_or_possessed = tk.BooleanVar(value=False)

        self.attr_entries = {}
        self.attr_buttons = []
        self.interactable_widgets = []
        self.option_filter = None

        self._build_gui()


    def _build_gui(self):
        # Shared Candidate / Enemy warrior editor.
        # The same compact layout is intentionally used everywhere.

        content = ttk.Frame(
            self,
            padding=(14, 6, 14, 10),
        )
        content.pack(fill="both", expand=True)


        # -------------------------------------------------------------
        # Basic attributes
        # -------------------------------------------------------------
        attributes_section = ttk.Frame(content)
        attributes_section.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Label(
            attributes_section,
            text="BASIC ATTRIBUTES",
            style="Section.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 4),
        )

        self.stats_canvas = StatGridCanvas(
            attributes_section,
            self.stats,
        )
        self.stats_canvas.pack(
            fill="x",
        )

        # Keep the original Entry-like API used by change_stat(),
        # get_config_dict() and load_config(), without creating six
        # permanent Entry widgets.
        self.attr_entries = (
            self.stats_canvas.proxies()
        )
        self.attr_buttons = []
        self.interactable_widgets.append(
            self.stats_canvas
        )

        # -------------------------------------------------------------
        # Equipment
        # -------------------------------------------------------------
        equipment_section = ttk.Frame(content)
        equipment_section.pack(fill="x", pady=(0, 10))

        ttk.Label(
            equipment_section,
            text="EQUIPMENT",
            style="Section.TLabel",
        ).pack(anchor="w", pady=(0, 4))

        eq_frame = ttk.Frame(equipment_section)
        eq_frame.pack(fill="x")
        eq_frame.columnconfigure(0, weight=1, uniform="hands")
        eq_frame.columnconfigure(1, weight=1, uniform="hands")

        main_hand = ttk.LabelFrame(
            eq_frame,
            text="Main Hand",
            style="Card.TLabelframe",
            padding=(8, 5),
        )
        main_hand.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        off_hand = ttk.LabelFrame(
            eq_frame,
            text="Off Hand",
            style="Card.TLabelframe",
            padding=(8, 5),
        )
        off_hand.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        for panel in (main_hand, off_hand):
            panel.columnconfigure(1, weight=1, uniform="compact_hand_fields")
            panel.columnconfigure(3, weight=1, uniform="compact_hand_fields")

        def field_position(index):
            row = index // 2
            pair = index % 2
            label_column = pair * 2
            widget_column = label_column + 1
            return row, label_column, widget_column

        def place_field(panel, index, label_text, widget):
            row, label_column, widget_column = field_position(index)

            ttk.Label(
                panel,
                text=label_text,
                style="Card.TLabel",
            ).grid(
                row=row,
                column=label_column,
                sticky="w",
                padx=(0, 6),
                pady=2,
            )

            widget.grid(
                row=row,
                column=widget_column,
                sticky="ew",
                padx=((0, 10) if widget_column == 1 else (0, 0)),
                pady=2,
            )

        self.cb_main = ttk.Combobox(
            main_hand,
            textvariable=self.eq_main_general,
            values=("None", *WEAPONS_GENERAL),
            state="readonly",
            width=20,
        )
        place_field(main_hand, 0, "General", self.cb_main)
        self.cb_main.bind(
            "<<ComboboxSelected>>",
            lambda event: self._select_weapon("main", "general"),
        )
        ToolTip(
            self.cb_main,
            lambda: weapon_descriptions().get(
                self.eq_main_general.get(),
                "",
            ),
        )

        self.cb_main_exclusive = ttk.Combobox(
            main_hand,
            textvariable=self.eq_main_exclusive,
            values=(
                "None",
                *(
                    weapon for weapon in WEAPONS_EXCLUSIVE
                    if weapon not in MAIN_HAND_FORBIDDEN_WEAPONS
                ),
            ),
            state="readonly",
            width=20,
        )
        place_field(main_hand, 1, "Special", self.cb_main_exclusive)
        self.cb_main_exclusive.bind(
            "<<ComboboxSelected>>",
            lambda event: self._select_weapon("main", "exclusive"),
        )
        ToolTip(
            self.cb_main_exclusive,
            lambda: weapon_descriptions().get(
                self.eq_main_exclusive.get(),
                "",
            ),
        )

        self.cb_main_material = ttk.Combobox(
            main_hand,
            textvariable=self.eq_main_material,
            values=WEAPON_MATERIALS,
            state="readonly",
            width=20,
        )
        place_field(main_hand, 2, "Material", self.cb_main_material)

        self.cb_main_poison = ttk.Combobox(
            main_hand,
            textvariable=self.eq_main_poison,
            values=POISONS,
            state="readonly",
            width=20,
        )
        place_field(main_hand, 3, "Poison", self.cb_main_poison)
        ToolTip(
            self.cb_main_poison,
            lambda: POISON_DESCRIPTIONS.get(
                self.eq_main_poison.get(),
                "",
            ),
        )

        self.cb_offhand = ttk.Combobox(
            off_hand,
            textvariable=self.eq_off_general,
            values=OFFHAND_GENERAL,
            state="readonly",
            width=20,
        )
        place_field(off_hand, 0, "General", self.cb_offhand)
        self.cb_offhand.bind(
            "<<ComboboxSelected>>",
            lambda event: self._select_weapon("off", "general"),
        )
        ToolTip(
            self.cb_offhand,
            lambda: weapon_descriptions().get(
                self.eq_off_general.get(),
                "",
            ),
        )

        self.cb_off_exclusive = ttk.Combobox(
            off_hand,
            textvariable=self.eq_off_exclusive,
            values=OFFHAND_EXCLUSIVE,
            state="readonly",
            width=20,
        )
        place_field(off_hand, 1, "Special", self.cb_off_exclusive)
        self.cb_off_exclusive.bind(
            "<<ComboboxSelected>>",
            lambda event: self._select_weapon("off", "exclusive"),
        )
        ToolTip(
            self.cb_off_exclusive,
            lambda: weapon_descriptions().get(
                self.eq_off_exclusive.get(),
                "",
            ),
        )

        self.cb_off_material = ttk.Combobox(
            off_hand,
            textvariable=self.eq_off_material,
            values=WEAPON_MATERIALS,
            state="readonly",
            width=20,
        )
        place_field(off_hand, 2, "Material", self.cb_off_material)

        self.cb_off_poison = ttk.Combobox(
            off_hand,
            textvariable=self.eq_off_poison,
            values=POISONS,
            state="readonly",
            width=20,
        )
        place_field(off_hand, 3, "Poison", self.cb_off_poison)
        ToolTip(
            self.cb_off_poison,
            lambda: POISON_DESCRIPTIONS.get(
                self.eq_off_poison.get(),
                "",
            ),
        )

        defense = ttk.Frame(
            equipment_section,
            style="Card.TFrame",
            padding=(8, 5),
        )
        defense.pack(fill="x", pady=(6, 0))
        defense.columnconfigure(0, weight=1, uniform="defense")
        defense.columnconfigure(1, weight=1, uniform="defense")

        armor_cell = ttk.Frame(defense, style="Card.TFrame")
        armor_cell.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        armor_cell.columnconfigure(1, weight=1)

        ttk.Label(
            armor_cell,
            text="Armour",
            style="Card.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.cb_armor = ttk.Combobox(
            armor_cell,
            textvariable=self.eq_armor,
            values=BODY_ARMORS,
            state="readonly",
            width=18,
        )
        self.cb_armor.grid(row=0, column=1, sticky="ew")
        self.cb_armor.bind(
            "<<ComboboxSelected>>",
            self.on_equipment_change,
        )
        ToolTip(
            self.cb_armor,
            lambda: armour_descriptions().get(
                self.eq_armor.get(),
                "",
            ),
        )

        equipment_cell = ttk.Frame(defense, style="Card.TFrame")
        equipment_cell.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        equipment_cell.columnconfigure(1, weight=1)

        ttk.Label(
            equipment_cell,
            text="Equipment",
            style="Card.TLabel",
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self.equipment_button = ttk.Menubutton(
            equipment_cell,
            textvariable=self.equipment_button_text,
            style="Card.TMenubutton",
        )
        self.equipment_button.grid(row=0, column=1, sticky="ew")

        self.equipment_menu = tk.Menu(
            self.equipment_button,
            tearoff=False,
        )
        self.equipment_button.configure(menu=self.equipment_menu)

        for name in EQUIPMENT_SELECTOR_OPTIONS:
            self.equipment_menu.add_checkbutton(
                label=name,
                variable=self.equipment_vars[name],
                command=lambda item=name:
                    self._equipment_selection_changed(item),
            )
            self._equipment_menu_indices[name] = (
                self.equipment_menu.index("end")
            )

        self.interactable_widgets.extend(
            (
                self.cb_main,
                self.cb_main_exclusive,
                self.cb_offhand,
                self.cb_off_exclusive,
                self.cb_main_material,
                self.cb_off_material,
                self.cb_main_poison,
                self.cb_off_poison,
                self.cb_armor,
                self.equipment_button,
            )
        )

        if self.show_house_rules:
            house_rules = ttk.LabelFrame(
                content,
                text="House Rules",
                style="Card.TLabelframe",
                padding=(10, 8),
            )
            house_rules.pack(fill="x", pady=(0, 10))

            black_rule = ttk.Checkbutton(
                house_rules,
                text=(
                    "House rule intended to keep two weapons from being "
                    "overwhelmingly strong and from always being the best "
                    "option regardless of weapon quality or any other rule "
                    "in the game."
                ),
                variable=self.house_rule_offhand_penalty,
                style="Card.TCheckbutton",
            )
            black_rule.pack(fill="x", anchor="w", pady=(1, 4))

            red_rule = ttk.Checkbutton(
                house_rules,
                text=(
                    "House rule intended to keep two weapons from being "
                    "overwhelmingly strong and from always being the best "
                    "option regardless of weapon quality or any other rule "
                    "in the game."
                ),
                variable=self.house_rule_dual_penalty,
                style="Card.TCheckbutton",
            )
            red_rule.pack(fill="x", anchor="w", pady=(4, 1))

            self.interactable_widgets.extend((black_rule, red_rule))


        # -------------------------------------------------------------
        # Skills
        # -------------------------------------------------------------
        skills_section = ttk.Frame(content)
        skills_section.pack(fill="x")

        ttk.Label(
            skills_section,
            text="SKILLS",
            style="Section.TLabel",
        ).pack(anchor="w", pady=(0, 4))


        initial_skills = set(
            GENERAL_SKILL_DESCRIPTIONS
        ).intersection(self.skills)

        self.skill_canvas = SkillChecklistCanvas(
            skills_section,
            variables=self.skills,
            descriptions=self.skill_descriptions,
            categories=self.skill_categories,
            allowed_skills=initial_skills,
        )
        self.skill_canvas.pack(
            fill="x",
        )
        self.interactable_widgets.append(
            self.skill_canvas
        )

        traits = ttk.Frame(skills_section)
        traits.pack(fill="x", pady=(5, 0))

        unholy = ttk.Checkbutton(
            traits,
            text="Undead or Possessed",
            variable=self.undead_or_possessed,
        )
        unholy.pack(anchor="center")

        ToolTip(
            unholy,
            "Enables conditional rules such as the Sigmarite hammer’s +1 to wound.",
        )
        self.interactable_widgets.append(unholy)


    def set_option_filter(self, profile=None, extra_skills=()):
        """Restrict controls to modelled options that are legal for the profile."""
        self.option_filter = profile
        if profile is None:
            main_allowed = tuple(WEAPONS_MAIN)
            off_allowed = tuple(OFF_HAND_OPTIONS)
            armor_allowed = tuple(BODY_ARMORS)
            material_allowed = tuple(WEAPON_MATERIALS)
            skill_allowed = set(GENERAL_SKILL_DESCRIPTIONS) | set(extra_skills)
            helmet_allowed = True
            equipment_allowed = set(EQUIPMENT_SELECTOR_OPTIONS)
            poison_allowed = set(POISONS)
        else:
            main_allowed = usable_main_weapons(profile)
            off_allowed = usable_offhand_options(profile)
            armor_allowed = (
                "No Armour",
                *(armor for armor in profile.armors if armor in BODY_ARMORS),
            )
            material_allowed = profile.materials
            skill_allowed = set(profile.skills)
            helmet_allowed = profile.helmet_allowed
            equipment_allowed = set(equipment_options_for_profile(
                profile.band_id, profile.profile_id
            )).intersection(EQUIPMENT_SELECTOR_OPTIONS)
            if not helmet_allowed:
                equipment_allowed.discard("Helmet")
            poison_allowed = {"No Poison"}.union(
                set(equipment_options_for_profile(
                    profile.band_id, profile.profile_id
                )).intersection(POISONS)
            )

        self._allowed_main = set(main_allowed)
        self._allowed_off = set(off_allowed)
        self._allowed_armor = set(armor_allowed)
        self._allowed_materials = set(material_allowed)
        self._helmet_allowed = helmet_allowed
        self._allowed_equipment = equipment_allowed
        self._allowed_poisons = poison_allowed
        self.cb_main.config(values=("None", *(w for w in WEAPONS_GENERAL if w in self._allowed_main)))
        self.cb_main_exclusive.config(values=(
            "None", *(w for w in WEAPONS_EXCLUSIVE if w in self._allowed_main)
        ))
        self.cb_offhand.config(values=tuple(w for w in OFFHAND_GENERAL if w in self._allowed_off))
        self.cb_off_exclusive.config(values=tuple(w for w in OFFHAND_EXCLUSIVE if w in self._allowed_off))
        self.cb_armor.config(values=tuple(a for a in BODY_ARMORS if a in self._allowed_armor))
        self.cb_main_material.config(values=tuple(m for m in WEAPON_MATERIALS if m in self._allowed_materials))
        self.cb_off_material.config(values=tuple(m for m in WEAPON_MATERIALS if m in self._allowed_materials))
        poison_values = tuple(poison for poison in POISONS if poison in poison_allowed)
        self.cb_main_poison.config(values=poison_values)
        self.cb_off_poison.config(values=poison_values)

        for skill, variable in self.skills.items():
            if skill not in skill_allowed:
                variable.set(False)

        self.skill_canvas.set_allowed_skills(skill_allowed)

        if self._selected_main_weapon() not in self._allowed_main:
            replacement = next(iter(main_allowed), "Dagger")
            self.eq_main_general.set(replacement if replacement in WEAPONS_GENERAL else "None")
            self.eq_main_exclusive.set(replacement if replacement in WEAPONS_EXCLUSIVE else "None")
        if self._selected_offhand() not in self._allowed_off:
            self.eq_off_general.set("None")
            self.eq_off_exclusive.set("None")
        if self.eq_armor.get() not in self._allowed_armor:
            self.eq_armor.set("No Armour")
        if self.eq_main_material.get() not in self._allowed_materials:
            self.eq_main_material.set("Normal")
        if self.eq_off_material.get() not in self._allowed_materials:
            self.eq_off_material.set("Normal")
        if self.eq_main_poison.get() not in poison_allowed:
            self.eq_main_poison.set("No Poison")
        if self.eq_off_poison.get() not in poison_allowed:
            self.eq_off_poison.set("No Poison")
        for name, variable in self.equipment_vars.items():
            allowed = name in equipment_allowed
            if not allowed:
                variable.set(False)
            self.equipment_menu.entryconfigure(
                self._equipment_menu_indices[name],
                state="normal" if allowed else "disabled",
            )
        self._update_equipment_summary()
        self.on_equipment_change()

    def _equipment_selection_changed(self, selected_name):
        """Update the multiple-equipment selection counter."""
        self._update_equipment_summary()

    def _update_equipment_summary(self):
        selected = [
            name for name in EQUIPMENT_SELECTOR_OPTIONS
            if self.equipment_vars[name].get()
        ]
        self.equipment_button_text.set(
            "None ▾" if not selected else f"{len(selected)} selected ▾"
        )

    def change_stat(
        self,
        attr,
        delta,
    ):
        try:
            current = int(
                self.attr_entries[attr].get()
            )

        except ValueError:
            current = 0

        new_value = max(
            0,
            current + delta,
        )

        self.attr_entries[attr].delete(
            0,
            tk.END,
        )

        self.attr_entries[attr].insert(
            0,
            str(new_value),
        )

    def set_enabled(
        self,
        enabled=True,
    ):
        state = (
            "normal"
            if enabled
            else "disabled"
        )

        for widget in self.interactable_widgets:

            if isinstance(
                widget,
                ttk.Combobox,
            ):

                widget.config(
                    state=(
                        "readonly"
                        if enabled
                        else "disabled"
                    )
                )

            else:

                widget.config(
                    state=state
                )

        if enabled:
            self.on_equipment_change()

    def _select_weapon(self, hand, category):
        if hand == "main":
            if category == "general":
                self.eq_main_exclusive.set("None")
            elif self.eq_main_exclusive.get() != "None":
                self.eq_main_general.set("None")
            elif self.eq_main_general.get() == "None":
                self.eq_main_general.set("Dagger")
        else:
            if category == "general":
                self.eq_off_exclusive.set("None")
            elif self.eq_off_exclusive.get() != "None":
                self.eq_off_general.set("None")
        self.on_equipment_change()

    def _selected_main_weapon(self):
        exclusive = self.eq_main_exclusive.get()
        general = self.eq_main_general.get()
        return exclusive if exclusive != "None" else (
            general if general != "None" else "Dagger"
        )

    def _selected_offhand(self):
        exclusive = self.eq_off_exclusive.get()
        return exclusive if exclusive != "None" else self.eq_off_general.get()

    def on_equipment_change(self, event=None):
        main_weapon = self._selected_main_weapon()
        off_disabled = (
            main_weapon in TWO_HANDED_WEAPONS
            or main_weapon in PAIRED_WEAPONS
            or main_weapon == "Natural attacks"
        )

        if main_weapon == "Spear":
            self.cb_offhand.config(values=tuple(v for v in ("None", "Shield", "Buckler") if v in self._allowed_off))
            self.cb_off_exclusive.config(state="disabled")
            self.eq_off_exclusive.set("None")
            if self.eq_off_general.get() not in ("None", "Shield", "Buckler"):
                self.eq_off_general.set("None")
        elif main_weapon == "Morning star":
            self.cb_offhand.config(values=tuple(v for v in ("None", "Shield") if v in self._allowed_off))
            self.cb_off_exclusive.config(state="disabled")
            self.eq_off_exclusive.set("None")
            if self.eq_off_general.get() not in ("None", "Shield"):
                self.eq_off_general.set("None")
        elif main_weapon in ("Choppa", "Squig prodder"):
            self.cb_offhand.config(values=tuple(v for v in ("None", "Shield") if v in self._allowed_off))
            self.cb_off_exclusive.config(
                values=tuple(v for v in ("None", "Spiked gauntlet") if v in self._allowed_off),
                state="readonly",
            )
            if self.eq_off_general.get() not in ("None", "Shield"):
                self.eq_off_general.set("None")
            if self.eq_off_exclusive.get() not in (
                "None", "Spiked gauntlet",
            ):
                self.eq_off_exclusive.set("None")
        else:
            self.cb_offhand.config(values=tuple(v for v in OFFHAND_GENERAL if v in self._allowed_off))
            self.cb_off_exclusive.config(values=tuple(v for v in OFFHAND_EXCLUSIVE if v in self._allowed_off))
            self.cb_off_exclusive.config(state="readonly")

        armor = self.eq_armor.get()
        forbidden_defences = set()
        if armor in ("Toughened leathers", "Ninja robes"):
            forbidden_defences.add("Shield")
        elif armor in ("Wizard's robe", "Eshin assassin robes"):
            forbidden_defences.update(("Shield", "Buckler"))
        if forbidden_defences:
            allowed = tuple(
                value for value in self.cb_offhand.cget("values")
                if value not in forbidden_defences
            )
            self.cb_offhand.config(values=allowed)
            if self.eq_off_general.get() in forbidden_defences:
                self.eq_off_general.set("None")

        if off_disabled:
            self.eq_off_general.set("None")
            self.eq_off_exclusive.set("None")
            self.cb_offhand.config(state="disabled")
            self.cb_off_exclusive.config(state="disabled")
            self.cb_off_material.config(state="disabled")
            self.eq_off_poison.set("No Poison")
            self.cb_off_poison.config(state="disabled")
        else:
            self.cb_offhand.config(state="readonly")
            self.cb_off_material.config(state="readonly")
            off_weapon = self._selected_offhand()
            if off_weapon in ("None", "Shield", "Buckler"):
                self.eq_off_poison.set("No Poison")
                self.cb_off_poison.config(state="disabled")
            else:
                self.cb_off_poison.config(state="readonly")
    def get_config_dict(self):

        result = {}

        for key, entry in (
            self.attr_entries.items()
        ):
            result[key] = int(
                entry.get()
            )

        result["skills"] = [
            skill
            for skill, variable
            in self.skills.items()
            if variable.get()
        ]

        result["main_weapon"] = self._selected_main_weapon()
        result["off_hand"] = self._selected_offhand()
        result["main_weapon_material"] = self.eq_main_material.get()
        result["offhand_material"] = self.eq_off_material.get()
        selected_preparations = [
            name for name in PREPARATIONS
            if name != "None" and self.equipment_vars[name].get()
        ]
        result["preparations"] = selected_preparations
        result["main_poison"] = self.eq_main_poison.get()
        result["offhand_poison"] = self.eq_off_poison.get()

        result["has_helmet"] = (
            self.eq_has_helmet.get()
        )

        result["has_luck_amulet"] = self.equipment_vars["Lucky charm"].get()
        result["has_sea_dragon_cloak"] = self.equipment_vars["Sea Dragon cloak"].get()
        result["house_rule_offhand_penalty"] = self.house_rule_offhand_penalty.get()
        result["house_rule_dual_penalty"] = self.house_rule_dual_penalty.get()
        result["undead_or_possessed"] = self.undead_or_possessed.get()

        result["armor"] = (
            self.eq_armor.get()
        )

        return result

    def load_config(self, config):
        for attribute, entry in self.attr_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(config.get(attribute, self.stats[attribute])))

        selected_skills = set(config.get("skills", ()))
        for skill, variable in self.skills.items():
            variable.set(skill in selected_skills)

        main_weapon = config.get("main_weapon", WEAPONS_GENERAL[0])
        off_hand = config.get("off_hand", "None")
        self.eq_main_general.set(
            "None" if main_weapon in WEAPONS_EXCLUSIVE else main_weapon
        )
        self.eq_main_exclusive.set(
            main_weapon if main_weapon in WEAPONS_EXCLUSIVE else "None"
        )
        self.eq_off_general.set(
            "None" if off_hand in OFFHAND_EXCLUSIVE else off_hand
        )
        self.eq_off_exclusive.set(
            off_hand if off_hand in OFFHAND_EXCLUSIVE else "None"
        )
        self.eq_main_material.set(config.get("main_weapon_material", "Normal"))
        self.eq_off_material.set(config.get("offhand_material", "Normal"))
        self.eq_armor.set(config.get("armor", BODY_ARMORS[0]))
        for variable in self.equipment_vars.values():
            variable.set(False)
        self.eq_has_helmet.set(config.get("has_helmet", False))
        self.equipment_vars["Lucky charm"].set(
            config.get("has_luck_amulet", False)
        )
        self.equipment_vars["Sea Dragon cloak"].set(
            config.get("has_sea_dragon_cloak", False)
        )
        for preparation in config.get("preparations", ()):
            if preparation in self.equipment_vars:
                self.equipment_vars[preparation].set(True)
        self.eq_main_poison.set(config.get("main_poison", "No Poison"))
        self.eq_off_poison.set(config.get("offhand_poison", "No Poison"))
        self._update_equipment_summary()
        self.house_rule_offhand_penalty.set(
            config.get("house_rule_offhand_penalty", False)
        )
        self.house_rule_dual_penalty.set(config.get("house_rule_dual_penalty", False))
        self.undead_or_possessed.set(config.get("undead_or_possessed", False))
        self.on_equipment_change()


class EnemyProfileEditor(ttk.Frame):
    """Complete manual-opponent editor, created only when visible."""

    def __init__(
        self,
        parent,
        bands,
        initial=None,
        on_name_change=None,
        skill_descriptions=None,
        skill_categories=None,
    ):
        super().__init__(parent)
        self.bands = bands
        self.band_by_name = {band.name: band for band in bands}
        self.on_name_change = on_name_change
        self.name = tk.StringVar(value="Enemy")
        self.band_id = tk.StringVar()
        self.profile_id = tk.StringVar()
        self.status = tk.StringVar(value="Free Selection")

        selector = ttk.Frame(self)
        selector.pack(fill="x", padx=8, pady=(5, 2))
        for column in (1, 3, 5):
            selector.columnconfigure(column, weight=1)
        ttk.Label(selector, text="Name:").grid(row=0, column=0, padx=(0, 3))
        name_entry = ttk.Entry(selector, textvariable=self.name)
        name_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(selector, text="Warband:").grid(row=0, column=2, padx=(0, 3))
        self.band_combo = ttk.Combobox(
            selector, state="readonly",
            values=("Free Selection", *(band.name for band in bands)),
        )
        self.band_combo.grid(row=0, column=3, sticky="ew", padx=(0, 8))
        ttk.Label(selector, text="Warrior:").grid(row=0, column=4, padx=(0, 3))
        self.profile_combo = ttk.Combobox(selector, state="disabled")
        self.profile_combo.grid(row=0, column=5, sticky="ew")
        ttk.Label(selector, textvariable=self.status, font=("Arial", 8, "italic")).grid(
            row=1, column=0, columnspan=6, sticky="w", pady=(3, 0)
        )
        self.band_combo.bind("<<ComboboxSelected>>", self._band_changed)
        self.profile_combo.bind("<<ComboboxSelected>>", self._profile_changed)
        self.name.trace_add("write", self._name_changed)

        if skill_descriptions is None or skill_categories is None:
            descriptions = dict(GENERAL_SKILL_DESCRIPTIONS)
            categories = dict(GENERAL_SKILL_CATEGORIES)

            for band in bands:
                descriptions.update(
                    (skill.name, skill.description)
                    for skill in band.skills
                )
                for skill in band.skills:
                    categories.setdefault(skill.name, "special")
        else:
            descriptions = skill_descriptions
            categories = skill_categories

        self.config = WarriorConfigFrame(
            self, "Enemy configuration", skill_descriptions=descriptions,
            skill_categories=categories,
        )
        self.config.pack(fill="both", expand=True, padx=0, pady=(2, 5))
        self.config.set_option_filter(None)
        self.band_combo.set("Free Selection")
        if initial:
            self.load_config(initial)

    def _name_changed(self, *_args):
        if self.on_name_change:
            self.on_name_change(self.name.get().strip() or "Enemy")

    def _band_changed(self, _event=None):
        band = self.band_by_name.get(self.band_combo.get())
        self.profile_id.set("")
        if band is None:
            self.band_id.set("")
            self.profile_combo.set("")
            self.profile_combo.config(values=(), state="disabled")
            self.config.set_option_filter(None)
            self.status.set("Free selection: all common options.")
            return
        self.band_id.set(band.band_id)
        self.profile_combo.config(values=tuple(p.name for p in band.profiles), state="readonly")
        self.profile_combo.set("Select a Warrior")
        self.config.set_option_filter(None, extra_skills=(s.name for s in band.skills))
        self.status.set(f"{len(band.profiles)} profiles available.")

    def _profile_changed(self, _event=None):
        band = next((band for band in self.bands if band.band_id == self.band_id.get()), None)
        if not band:
            return
        profile = next((p for p in band.profiles if p.name == self.profile_combo.get()), None)
        if not profile:
            return
        self.profile_id.set(profile.profile_id)
        self.name.set(profile.name)
        default_weapon = next(iter(usable_main_weapons(profile)), "Dagger")
        self.config.load_config({
            **profile.stats, "skills": [], "main_weapon": default_weapon,
            "off_hand": "None", "armor": "No Armour",
        })
        self.config.set_option_filter(profile)
        self.status.set(
            f"Canonical profile: {profile.band_name} · {profile.profile_type} · "
            f"{self.winfo_toplevel()._tr('movement')}: "
            f"{format_movement(profile.movement_inches, self.winfo_toplevel().locale.get())}."
        )

    def get_config_dict(self):
        result = self.config.get_config_dict()
        profile = find_profile(self.band_id.get(), self.profile_id.get())
        result.update({
            "enemy_name": self.name.get().strip() or "Enemy",
            "enemy_band_id": self.band_id.get(),
            "enemy_profile_id": self.profile_id.get(),
            "allowed_upgrade_skills": (
                [skill for skill in profile.skills if skill in SKILLS]
                if profile else list(SKILLS)
            ),
        })
        return result

    def load_config(self, data):
        self.name.set(data.get("enemy_name", "Enemy"))
        band_id = data.get("enemy_band_id", "")
        profile_id = data.get("enemy_profile_id", "")
        profile = find_profile(band_id, profile_id)
        if profile:
            band = next(b for b in self.bands if b.band_id == band_id)
            self.band_id.set(band_id)
            self.profile_id.set(profile_id)
            self.band_combo.set(band.name)
            self.profile_combo.config(values=tuple(p.name for p in band.profiles), state="readonly")
            self.profile_combo.set(profile.name)
            self.config.load_config(data)
            self.config.set_option_filter(profile)
            self.status.set(f"Profile loaded: {band.name} · {profile.name}.")
        else:
            self.band_id.set("")
            self.profile_id.set("")
            self.band_combo.set("Free Selection")
            self.profile_combo.config(values=(), state="disabled")
            self.config.load_config(data)
            self.config.set_option_filter(None)

    def set_enabled(self, enabled):
        self.config.set_enabled(enabled)
        for child in self.winfo_children()[0].winfo_children():
            try:
                if child is self.band_combo:
                    child.config(state="readonly" if enabled else "disabled")
                elif child is self.profile_combo:
                    child.config(
                        state="readonly" if enabled and self.band_id.get() else "disabled"
                    )
                else:
                    child.config(state="normal" if enabled else "disabled")
            except tk.TclError:
                pass


# Main window

class CombatLabApp(tk.Tk):

    def _tr(self, key):
        return UI_TEXT[self.locale.get()].get(key, UI_TEXT["en"].get(key, key))

    def _category_labels(self):
        return CATALOG_CATEGORY_LABELS[self.locale.get()]

    def _configure_styles(self):
        # Configure the visual language of the application.
        style = ttk.Style(self)

        # Native Windows themes ignore many colour settings.
        style.theme_use("clam")

        self.configure(background=COLORS["bg"])

        default_font = ("Segoe UI", 10)
        small_font = ("Segoe UI", 9)
        section_font = ("Segoe UI Semibold", 11)
        heading_font = ("Segoe UI Semibold", 15)
        title_font = ("Segoe UI Semibold", 18)

        self.option_add("*Font", default_font)
        self.option_add("*Menu.Font", default_font)
        self.option_add("*Menu.background", COLORS["surface_alt"])
        self.option_add("*Menu.foreground", COLORS["text"])
        self.option_add("*Menu.activeBackground", COLORS["accent"])
        self.option_add("*Menu.activeForeground", "#111111")
        self.option_add("*Menu.borderWidth", 0)
        self.option_add("*TCombobox*Listbox.background", COLORS["surface_alt"])
        self.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
        self.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
        self.option_add("*TCombobox*Listbox.selectForeground", "#111111")
        self.option_add("*TCombobox*Listbox.font", default_font)

        style.configure(
            ".",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["surface"],
            bordercolor=COLORS["border"],
            darkcolor=COLORS["border"],
            lightcolor=COLORS["border"],
            troughcolor=COLORS["surface"],
            focuscolor=COLORS["accent"],
            font=default_font,
        )

        style.configure("TFrame", background=COLORS["bg"])
        style.configure("Card.TFrame", background=COLORS["surface"], relief="flat")

        style.configure(
            "Card.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
        )
        style.configure(
            "Card.Muted.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text_muted"],
        )
        style.configure(
            "Card.Section.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 11),
        )

        style.configure(
            "Card.TCheckbutton",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            padding=(2, 3),
        )
        style.map(
            "Card.TCheckbutton",
            background=[("active", COLORS["surface"])],
            foreground=[("disabled", COLORS["text_disabled"])],
        )

        style.configure(
            "TMenubutton",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=(10, 6),
            relief="flat",
        )
        style.map(
            "TMenubutton",
            background=[
                ("active", COLORS["surface_hover"]),
                ("pressed", COLORS["surface_hover"]),
                ("disabled", COLORS["surface"]),
            ],
            foreground=[("disabled", COLORS["text_disabled"])],
        )

        style.configure(
            "Card.TMenubutton",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=(10, 6),
            relief="flat",
        )
        style.map(
            "Card.TMenubutton",
            background=[
                ("active", COLORS["surface_hover"]),
                ("pressed", COLORS["surface_hover"]),
                ("disabled", COLORS["surface"]),
            ],
            foreground=[("disabled", COLORS["text_disabled"])],
        )

        style.configure(
            "Stat.TButton",
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            padding=(5, 4),
            relief="flat",
        )
        style.map(
            "Stat.TButton",
            background=[
                ("active", COLORS["surface_hover"]),
                ("pressed", COLORS["accent_pressed"]),
            ],
            foreground=[("pressed", "#111111")],
        )

        style.configure(
            "Stat.TEntry",
            fieldbackground=COLORS["bg"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            insertcolor=COLORS["text"],
            padding=(4, 5),
        )
        style.map(
            "Stat.TEntry",
            bordercolor=[("focus", COLORS["accent"])],
        )

        style.configure(
            "TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
        )
        style.configure("Muted.TLabel", foreground=COLORS["text_muted"])
        style.configure("Title.TLabel", font=title_font, foreground=COLORS["text"])
        style.configure("Heading.TLabel", font=heading_font, foreground=COLORS["text"])
        style.configure("Section.TLabel", font=section_font, foreground=COLORS["text"])
        style.configure("TSeparator", background=COLORS["border"])

        style.configure(
            "TButton",
            padding=(12, 7),
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            borderwidth=1,
            relief="flat",
        )
        style.map(
            "TButton",
            background=[
                ("pressed", COLORS["surface_hover"]),
                ("active", COLORS["surface_hover"]),
                ("disabled", COLORS["surface"]),
            ],
            foreground=[("disabled", COLORS["text_disabled"])],
            bordercolor=[
                ("focus", COLORS["accent"]),
                ("active", COLORS["border_light"]),
            ],
        )

        style.configure(
            "Accent.TButton",
            background=COLORS["accent"],
            foreground="#111111",
            bordercolor=COLORS["accent"],
            font=("Segoe UI Semibold", 10),
            padding=(16, 8),
        )
        style.map(
            "Accent.TButton",
            background=[
                ("pressed", COLORS["accent_pressed"]),
                ("active", COLORS["accent_hover"]),
                ("disabled", COLORS["surface_alt"]),
            ],
            foreground=[("disabled", COLORS["text_disabled"])],
        )

        style.configure(
            "Danger.TButton",
            background=COLORS["danger"],
            foreground="#FFFFFF",
            bordercolor=COLORS["danger"],
            font=("Segoe UI Semibold", 10),
            padding=(16, 8),
        )
        style.map(
            "Danger.TButton",
            background=[
                ("active", COLORS["danger_hover"]),
                ("pressed", COLORS["danger"]),
            ],
        )

        style.configure(
            "TEntry",
            fieldbackground=COLORS["surface_alt"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            insertcolor=COLORS["text"],
            padding=(7, 6),
        )
        style.map("TEntry", bordercolor=[("focus", COLORS["accent"])])

        style.configure(
            "TCombobox",
            fieldbackground=COLORS["surface_alt"],
            background=COLORS["surface_alt"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text_muted"],
            bordercolor=COLORS["border"],
            padding=(6, 5),
        )
        style.map(
            "TCombobox",
            fieldbackground=[
                ("readonly", COLORS["surface_alt"]),
                ("disabled", COLORS["surface"]),
            ],
            foreground=[
                ("readonly", COLORS["text"]),
                ("disabled", COLORS["text_disabled"]),
            ],
            selectbackground=[("readonly", COLORS["surface_alt"])],
            selectforeground=[("readonly", COLORS["text"])],
            bordercolor=[("focus", COLORS["accent"])],
        )

        style.configure(
            "TSpinbox",
            fieldbackground=COLORS["surface_alt"],
            foreground=COLORS["text"],
            arrowcolor=COLORS["text_muted"],
            bordercolor=COLORS["border"],
            padding=(5, 5),
        )

        style.configure(
            "TCheckbutton",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            padding=(2, 3),
        )
        style.map(
            "TCheckbutton",
            background=[("active", COLORS["bg"])],
            foreground=[("disabled", COLORS["text_disabled"])],
        )

        style.configure(
            "TRadiobutton",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            padding=(2, 3),
        )
        style.map(
            "TRadiobutton",
            background=[("active", COLORS["bg"])],
            foreground=[("disabled", COLORS["text_disabled"])],
        )

        style.configure(
            "TLabelframe",
            background=COLORS["bg"],
            bordercolor=COLORS["border"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=small_font,
        )

        style.configure(
            "Card.TLabelframe",
            background=COLORS["surface"],
            bordercolor=COLORS["border"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "Card.TLabelframe.Label",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=section_font,
        )

        style.configure(
            "TNotebook",
            background=COLORS["bg"],
            borderwidth=0,
            tabmargins=(12, 6, 12, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            borderwidth=0,
            padding=(15, 9),
            font=("Segoe UI Semibold", 8),
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", COLORS["surface"]),
                ("active", COLORS["surface_alt"]),
            ],
            foreground=[
                ("selected", COLORS["accent"]),
                ("active", COLORS["text"]),
            ],
        )

        style.configure(
            "Treeview",
            background=COLORS["surface"],
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            borderwidth=0,
            rowheight=30,
        )
        style.map(
            "Treeview",
            background=[("selected", COLORS["selection"])],
            foreground=[("selected", COLORS["text"])],
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["surface_alt"],
            foreground=COLORS["text_muted"],
            bordercolor=COLORS["border"],
            relief="flat",
            font=("Segoe UI Semibold", 9),
            padding=(6, 8),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", COLORS["surface_hover"])],
            foreground=[("active", COLORS["text"])],
        )

        for scrollbar_style in ("Vertical.TScrollbar", "Horizontal.TScrollbar"):
            style.configure(
                scrollbar_style,
                background=COLORS["surface_alt"],
                troughcolor=COLORS["bg"],
                bordercolor=COLORS["bg"],
                arrowcolor=COLORS["text_muted"],
            )


        style.configure(
            "AnalysisTitle.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 12),
        )
        style.configure(
            "AnalysisSubtitle.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "AnalysisCardTitle.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "AnalysisStatus.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text_muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "ModeValue.TLabel",
            background=COLORS["surface"],
            foreground=COLORS["text"],
            font=("Segoe UI Semibold", 15),
        )
        style.configure(
            "AnalysisPanel.TLabelframe",
            background=COLORS["bg"],
            bordercolor=COLORS["border"],
            borderwidth=1,
            relief="solid",
        )
        style.configure(
            "AnalysisPanel.TLabelframe.Label",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=("Segoe UI Semibold", 9),
        )


        style.configure(
            "Analysis.Horizontal.TProgressbar",
            background=COLORS["accent"],
            troughcolor=COLORS["surface_alt"],
            bordercolor=COLORS["surface_alt"],
            borderwidth=0,
            thickness=34,
        )

        style.configure(
            "Horizontal.TProgressbar",
            background=COLORS["accent"],
            troughcolor=COLORS["surface_alt"],
            bordercolor=COLORS["surface_alt"],
            borderwidth=0,
            thickness=7,
        )


    def __init__(self):

        super().__init__()

        preferences = _load_preferences()
        saved_locale = str(preferences.get("locale", "en")).casefold()
        self.locale = tk.StringVar(value=saved_locale if saved_locale in {"en", "es"} else "en")
        saved_categories = preferences.get("categories")
        if not isinstance(saved_categories, list):
            legacy = str(preferences.get("category", "all")).casefold()
            saved_categories = list(SELECTABLE_CATEGORIES) if legacy == "all" else [legacy]
        self._catalog_categories = {
            str(value).casefold() for value in saved_categories
            if str(value).casefold() in SELECTABLE_CATEGORIES
        } or set(SELECTABLE_CATEGORIES)
        self.catalog_category_vars = {
            category: tk.BooleanVar(value=category in self._catalog_categories)
            for category in SELECTABLE_CATEGORIES
        }

        self._configure_styles()

        self.title(
            "Mordheim Combat Lab"
        )

        header = ttk.Frame(self, padding=(20, 14, 20, 10))
        header.pack(fill="x")

        branding = ttk.Frame(header)
        branding.pack(side="left")

        ttk.Label(
            branding,
            text="Mordheim Combat Lab",
            style="Title.TLabel",
        ).pack(anchor="w")

        self.subtitle_label = ttk.Label(
            branding,
            text=self._tr("subtitle"),
            style="Muted.TLabel",
        )
        self.subtitle_label.pack(anchor="w", pady=(1, 0))

        actions = ttk.Frame(header)
        actions.pack(side="right")

        self.catalog_header_label = ttk.Label(actions, text=self._tr("catalog"), style="Muted.TLabel")
        self.catalog_header_label.pack(side="left", padx=(0, 4))
        self.catalog_category_button = ttk.Menubutton(actions, width=18)
        self.catalog_category_menu = tk.Menu(self.catalog_category_button, tearoff=False)
        for category in SELECTABLE_CATEGORIES:
            self.catalog_category_menu.add_checkbutton(
                label=self._category_labels()[category],
                variable=self.catalog_category_vars[category],
                command=self._catalog_categories_changed,
            )
        self.catalog_category_button.configure(menu=self.catalog_category_menu)
        self._update_catalog_button_text()
        self.catalog_category_button.pack(side="left", padx=(0, 10))

        self.language_header_label = ttk.Label(actions, text=self._tr("language"), style="Muted.TLabel")
        self.language_header_label.pack(side="left", padx=(0, 4))
        self.locale_combo = ttk.Combobox(actions, state="readonly", width=8, values=("English", "Español"))
        self.locale_combo.set("Español" if self.locale.get() == "es" else "English")
        self.locale_combo.bind("<<ComboboxSelected>>", self._language_changed)
        self.locale_combo.pack(side="left", padx=(0, 10))

        self.import_button = ttk.Menubutton(actions, text=self._tr("import"))
        self.import_menu = tk.Menu(self.import_button, tearoff=False)
        self.import_menu.add_command(label=self._tr("load_candidate"), command=self._load_candidate_only)
        self.import_menu.add_command(label=self._tr("load_enemies"), command=self._load_enemies_only)
        self.import_button.configure(menu=self.import_menu)
        self.import_button.pack(side="left", padx=(0, 6))
        ToolTip(
            self.import_button,
            "Load only the candidate or only the configured enemies from a workbook.",
        )

        self.load_button = ttk.Button(actions, text=self._tr("load"), command=self._load_candidate)
        self.load_button.pack(side="left", padx=(0, 6))
        ToolTip(
            self.load_button,
            "Loads the candidate, enemies, and simulations saved in an Excel workbook.",
        )

        self.save_button = ttk.Button(
            actions,
            text=self._tr("save"),
            command=self._save_candidate,
            style="Accent.TButton",
        )
        self.save_button.pack(side="left")
        ToolTip(
            self.save_button,
            "Saves the candidate, enemies, and all calculated simulations to an Excel workbook.",
        )

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.enemy_check_widgets = []
        self.enemy_difficulties = {
            difficulty: tk.BooleanVar(value=True)
            for difficulty in DIFFICULTIES
        }
        self.enemy_level = tk.IntVar(value=0)
        self.enemy_mode = tk.StringVar(value="sample")
        self.simulations_combos = tk.StringVar(value=str(DEFAULT_COMBO_SIMULATIONS))
        self.simulations_equipment = tk.StringVar(value=str(DEFAULT_COMBO_SIMULATIONS))
        self.simulations_weapons = tk.StringVar(value=str(DEFAULT_COMBO_SIMULATIONS))
        self.combo_view = tk.StringVar(value="optimal")
        self.equipment_view = tk.StringVar(value="optimal")
        self.weapon_view = tk.StringVar(value="optimal")
        self.combo_search = tk.StringVar()
        self.improvement_count = tk.IntVar(value=1)
        self.equipment_max_items = tk.IntVar(value=1)
        self.combo_visible_modes = {mode for mode, _title in COMBAT_MODES}
        self.equipment_visible_modes = {mode for mode, _title in COMBAT_MODES}
        self.weapon_visible_modes = {mode for mode, _title in COMBAT_MODES}
        self.equipment_item_vars = {
            label: tk.BooleanVar(
                value=label in {
                    "Light armour", "Heavy armour", "Helmet",
                    "Lucky charm",
                }
            )
            for label, _kind, _value in self._equipment_options()
        }
        self.improvement_attribute_vars = {
            attr: tk.BooleanVar(value=True) for attr in ("I", "WS", "S", "T", "A", "W")
        }
        self.improvement_skill_vars = {
            skill: tk.BooleanVar(value=True) for skill in SKILLS
        }
        common_weapons = {
            "Dagger", "Mace", "Axe", "Sword", "Spear", "Halberd",
            "Double-handed weapon", "Flail", "Morning star",
        }
        self.weapon_item_vars = {
            weapon: tk.BooleanVar(value=weapon in common_weapons)
            for weapon in WEAPONS_ALL
        }
        self.weapon_material_vars = {
            material: tk.BooleanVar(value=material == "Normal")
            for material in WEAPON_MATERIALS
        }
        self.weapon_defense_vars = {
            defense: tk.BooleanVar(value=defense == "Shield")
            for defense in ("Shield", "Buckler")
        }
        self.candidate_name = tk.StringVar(value="Candidate")
        self.candidate_band_id = tk.StringVar(value="")
        self.candidate_profile_id = tk.StringVar(value="")
        self.candidate_catalog_status = tk.StringVar(value="Free selection: all simulator options are available.")
        self.house_rule_vars = {
            key: tk.BooleanVar(value=False) for key in HOUSE_RULES
        }
        self.candidate_workbook_path = None
        self._all_candidate_bands = load_bands()
        self._candidate_bands = bands_for_categories(self._catalog_categories)
        self._band_by_name = {
            band.name: band
            for band in self._candidate_bands
        }

        # Immutable UI catalogues reused every time Candidate or Enemy
        # is lazily rebuilt.
        self._warrior_skill_descriptions = dict(
            GENERAL_SKILL_DESCRIPTIONS
        )
        self._warrior_skill_categories = dict(
            GENERAL_SKILL_CATEGORIES
        )

        for band in self._candidate_bands:
            self._warrior_skill_descriptions.update(
                (skill.name, skill.description)
                for skill in band.skills
            )
            for skill in band.skills:
                self._warrior_skill_categories.setdefault(
                    skill.name,
                    "special",
                )

        # Treeview tooltip lookups are stable for the life of the app.
        self._rule_tooltip_descriptions = (
            self._build_rule_tooltip_descriptions()
        )
        self._rule_tooltip_cache = {}
        self._warrior_snapshots = {}
        self._enemy_profiles = []
        self._active_enemy_editor_index = None
        self._active_tab_key = "candidate"
        self._tab_transitioning = False

        tab_specs = (
            ("candidate", self._tr("candidate"), self.setup_tab_candidate),
            ("enemy", self._tr("enemy"), self.setup_tab_enemy),
            ("combos", self._tr("combos"), self.setup_tab_combos),
            ("weapons", self._tr("weapons"), self.setup_tab_weapons),
            ("equipment", self._tr("equipment"), self.setup_tab_equipment),
            ("house_rules", self._tr("house_rules"), self.setup_tab_house_rules),
        )
        self._lazy_tabs = {}
        self._built_tabs = set()
        for key, title, builder in tab_specs:
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=title)
            self._lazy_tabs[str(tab)] = (key, tab, builder)

        self._build_lazy_tab("candidate")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = min(1280, max(900, screen_width - 100))
        height = min(1050, max(700, screen_height - 30))
        x = max(0, (screen_width - width) // 2)
        y = max(0, (screen_height - height) // 2)
        self.minsize(900, 700)
        self.geometry(f"{width}x{height}+{x}+{y}")

        self._initialize_window_move_throttle()

    def _build_lazy_tab(self, requested_key):
        if requested_key in self._built_tabs:
            return

        for key, tab, builder in self._lazy_tabs.values():
            if key != requested_key:
                continue

            self._built_tabs.add(key)
            builder(tab)

            # Automatic contextual help is useful only for result tables.
            # Candidate/Enemy already attach their rule-specific tooltips
            # directly while creating their controls.
            if requested_key in {"combos", "weapons", "equipment"}:
                self._install_context_help(tab)


            return

    def _install_context_help(self, root):
        """Install only contextual help that adds information not already visible.

        Specific rule/skill/weapon/equipment tooltips are attached where the
        controls are created. This fallback is therefore intentionally limited
        to result tables.
        """
        for widget in self._widget_descendants(root):
            if getattr(widget, "_tooltip_attached", False):
                continue
            if isinstance(widget, ttk.Treeview):
                TreeviewToolTip(
                    widget,
                    self._tree_help_explanations(),
                    self._rule_tooltip_for_value,
                )


    @staticmethod
    def _widget_descendants(root):
        """Return descendants without the O(n²) pop(0) queue pattern."""
        descendants = []
        pending = list(root.winfo_children())

        while pending:
            widget = pending.pop()
            descendants.append(widget)
            pending.extend(widget.winfo_children())

        return descendants


    def _initialize_window_move_throttle(self):
        """Throttle pure window movement on Windows to coalesce Configure events."""
        if WINDOW_MOVE_THROTTLE_MS <= 0:
            return

        self._window_move_throttle_geometry = None
        self.bind(
            "<Configure>",
            self._throttle_window_move,
            add="+",
        )

    def _throttle_window_move(self, event):
        """Delay only pure top-level movement; resizing is never throttled."""
        if event.widget is not self:
            return

        geometry = (
            int(event.x),
            int(event.y),
            int(event.width),
            int(event.height),
        )

        previous = self._window_move_throttle_geometry
        self._window_move_throttle_geometry = geometry

        if previous is None:
            return

        throttle_ms = WINDOW_MOVE_THROTTLE_MS

        if throttle_ms <= 0:
            return

        moved = geometry[:2] != previous[:2]
        resized = geometry[2:] != previous[2:]

        if moved and not resized:
            time.sleep(
                throttle_ms / 1000.0
            )


    @staticmethod
    def _tree_help_explanations():
        return {
            "Optimal": (
                "Best win percentage among applicable modes; "
                "Parentheses show the improvement over the baseline. The star "
                "marks the highest win percentage in the table."
            ),
            "Motta": (
                "Cost-effectiveness: 507.4 × improvement / "
                "√(cost² + 0.01²). Regularisation makes near-zero costs "
                "produce large but finite values, while preserving the sign, "
                "and a zero improvement equals 0. The star marks the best MOTTA score."
            ),
            "Cost": (
                "Breakdown of outstanding component costs for the configuration. "
                "Sorting uses the total sum."
            ),
            "Main": "Main-hand weapon, including its material when applicable.",
            "Off": "Off-hand weapon, shield, buckler or free hand.",
        }


    def _build_rule_tooltip_descriptions(self):
        """Build the immutable rule-description lookup once."""
        descriptions = {}
        descriptions.update(weapon_descriptions())
        descriptions.update(armour_descriptions())
        descriptions.update(GENERAL_SKILL_DESCRIPTIONS)
        descriptions.update(SKILL_DESCRIPTIONS)
        descriptions.update(PREPARATION_DESCRIPTIONS)
        descriptions.update(POISON_DESCRIPTIONS)

        for band in self._candidate_bands:
            descriptions.update(
                (skill.name, skill.description)
                for skill in band.skills
            )

        descriptions.update({
            "Shield": "Improves the armour save by 1.",
            "Buckler": (
                "Allows a parry; with a sword, may re-roll one failed parry."
            ),
            "Helmet": "Protects against certain injury and stun results.",
            "Lucky charm": "Cancels the first hit suffered, subject to its rules.",
            "None": "The hand is empty.",
            "without weapons": (
                "Unarmed combat: -1 Strength, and the opponent improves "
                "their save by 1."
            ),
        })

        return descriptions

    def _rule_tooltip_for_value(self, value):
        """Find rules for items or skills written in a table cell."""
        text = str(value).replace("★", "").strip()

        if text in self._rule_tooltip_cache:
            return self._rule_tooltip_cache[text]

        if not text or re.search(r"\d+(?:[.,]\d+)?%", text):
            self._rule_tooltip_cache[text] = ""
            return ""

        descriptions = self._rule_tooltip_descriptions

        normalized = re.sub(
            r"\s+\((?:normal|Gromril|Ithilmar|Obsidian|Dark steel)\)",
            "",
            text,
        )

        if normalized in descriptions:
            result = descriptions[normalized]
            self._rule_tooltip_cache[text] = result
            return result

        matches = [
            (name, description)
            for name, description in descriptions.items()
            if name not in {"None"} and name in normalized
        ]
        matches.sort(
            key=lambda pair: len(pair[0]),
            reverse=True,
        )

        seen = set()
        lines = []

        for name, description in matches:
            if name in seen or any(
                name in selected for selected in seen
            ):
                continue

            seen.add(name)
            lines.append(f"{name}: {description}")

        result = "\n".join(lines[:3])
        self._rule_tooltip_cache[text] = result
        return result


    def _on_tab_changed(self, _event=None):
        if self._tab_transitioning:
            return
        selected = self.notebook.select()
        tab_data = self._lazy_tabs.get(selected)
        if not tab_data:
            return
        requested_key = tab_data[0]
        if requested_key == self._active_tab_key:
            return
        if getattr(self, "_simulation_running", False):
            self.notebook.select(self._tab_id_for(self._active_tab_key))
            return
        self._tab_transitioning = True
        try:
            self._unload_tab(self._active_tab_key)
            self._build_lazy_tab(requested_key)
            self._active_tab_key = requested_key
        finally:
            self._tab_transitioning = False

    def _tab_id_for(self, requested_key):
        for tab_id, (key, _tab, _builder) in self._lazy_tabs.items():
            if key == requested_key:
                return tab_id
        raise KeyError(requested_key)

    def _unload_tab(self, key):
        if key not in self._built_tabs:
            return
        if key == "candidate" and hasattr(self, "candidate_config"):
            self._warrior_snapshots[key] = self._candidate_config_dict()
        elif key == "enemy":
            pending = getattr(self, "_enemy_materialize_after_id", None)
            if pending is not None:
                self.after_cancel(pending)
                self._enemy_materialize_after_id = None
            self._save_active_enemy_editor()
            self._warrior_snapshots[key] = [
                dict(profile) for profile in self._enemy_profiles
            ]

        tab = self.nametowidget(self._tab_id_for(key))
        self._built_tabs.discard(key)
        for child in tab.winfo_children():
            child.destroy()
        if key == "enemy":
            self.enemy_editor = None
            self.enemy_config = None

    def _candidate_for_simulation(self):
        if "candidate" in self._built_tabs:
            config = self._candidate_config_dict()
        else:
            config = self._warrior_snapshots["candidate"].copy()
        return self._apply_house_rules(config)

    def _house_rules_payload(self):
        return {
            key: bool(variable.get())
            for key, variable in self.house_rule_vars.items()
        }

    def _update_catalog_button_text(self):
        count = len(self._catalog_categories)
        if count == len(SELECTABLE_CATEGORIES):
            text = self._category_labels()["all"]
        elif count == 1:
            text = self._category_labels()[next(iter(self._catalog_categories))]
        else:
            text = self._tr("selected_categories").format(count=count)
        self.catalog_category_button.configure(text=f"{text} ▾")

    def _catalog_categories_changed(self):
        selected = {
            category for category, variable in self.catalog_category_vars.items()
            if variable.get()
        }
        if not selected:
            for category in self._catalog_categories:
                self.catalog_category_vars[category].set(True)
            self.bell()
            return
        allowed = bands_for_categories(selected)
        allowed_ids = {band.band_id for band in allowed}
        current_band_id = self.candidate_band_id.get()
        if current_band_id and current_band_id not in allowed_ids:
            confirmed = messagebox.askyesno(
                "Change catalog category",
                "The current warband is not available in this category. "
                "Clear the selected warband, warrior, and calculated results?",
                parent=self,
            )
            if not confirmed:
                for category, variable in self.catalog_category_vars.items():
                    variable.set(category in self._catalog_categories)
                return
            self.candidate_band_id.set("")
            self.candidate_profile_id.set("")
            self._warrior_snapshots.pop("candidate", None)
            for attribute in (
                "_combo_table_data", "_combo_card_data", "_weapon_table_data",
                "_weapon_card_data", "_equipment_table_data", "_equipment_card_data",
            ):
                setattr(self, attribute, None)

        self._catalog_categories = selected
        self._update_catalog_button_text()
        self._candidate_bands = allowed
        self._band_by_name = {band.name: band for band in allowed}
        if "candidate" in self._built_tabs:
            self.candidate_band_combo.configure(
                values=(self._tr("free_selection"), *(band.name for band in allowed))
            )
            if not current_band_id or current_band_id not in allowed_ids:
                self.candidate_band_combo.set(self._tr("free_selection"))
                self.candidate_profile_combo.set("")
                self.candidate_profile_combo.configure(values=(), state="disabled")
                self.candidate_config.set_option_filter(None)
        if "enemy" in self._built_tabs:
            self._unload_tab("enemy")
            self._build_lazy_tab("enemy")
        _save_preferences(self.locale.get(), selected)

    def _language_changed(self, _event=None):
        self.locale.set("es" if self.locale_combo.get() == "Español" else "en")
        self._apply_locale()
        _save_preferences(self.locale.get(), self._catalog_categories)

    def _apply_locale(self):
        self.subtitle_label.configure(text=self._tr("subtitle"))
        self.catalog_header_label.configure(text=self._tr("catalog"))
        self.language_header_label.configure(text=self._tr("language"))
        self.import_button.configure(text=self._tr("import"))
        self.import_menu.entryconfigure(0, label=self._tr("load_candidate"))
        self.import_menu.entryconfigure(1, label=self._tr("load_enemies"))
        self.load_button.configure(text=self._tr("load"))
        self.save_button.configure(text=self._tr("save"))
        for index, category in enumerate(SELECTABLE_CATEGORIES):
            self.catalog_category_menu.entryconfigure(index, label=self._category_labels()[category])
        self._update_catalog_button_text()
        for tab_id, (key, _tab, _builder) in self._lazy_tabs.items():
            self.notebook.tab(tab_id, text=self._tr(key))
        if "candidate" in self._built_tabs:
            self.candidate_source_frame.configure(text=self._tr("identity"))
            self.candidate_name_label.configure(text=self._tr("name"))
            self.candidate_band_label.configure(text=self._tr("warband"))
            self.candidate_profile_label.configure(text=self._tr("warrior"))
            if not self.candidate_band_id.get():
                self.candidate_band_combo.set(self._tr("free_selection"))

    def _apply_house_rules(self, config):
        result = dict(config)
        selected = self._house_rules_payload()
        for rule_key, config_key in HOUSE_RULE_CONFIG_KEYS.items():
            result[config_key] = selected.get(rule_key, False)
        return result

    def _restore_house_rules(self, values):
        values = values if isinstance(values, dict) else {}
        for key, variable in self.house_rule_vars.items():
            variable.set(bool(values.get(key, False)))


    def setup_tab_house_rules(self, tab):
        heading = ttk.Frame(
            tab,
            padding=(20, 14, 20, 8),
        )
        heading.pack(fill="x")

        ttk.Label(
            heading,
            text="House Rules",
            style="AnalysisTitle.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            heading,
            text=(
                "Select the rules applied globally to the candidate, "
                "all enemies, and the cost analysis."
            ),
            style="AnalysisSubtitle.TLabel",
            wraplength=980,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

        rules_frame = ttk.Frame(
            tab,
            padding=(20, 2, 20, 16),
        )
        rules_frame.pack(
            fill="both",
            expand=True,
        )
        rules_frame.columnconfigure(0, weight=1)

        for row, (key, rule) in enumerate(HOUSE_RULES.items()):
            card = ttk.Frame(
                rules_frame,
                style="Card.TFrame",
                padding=(14, 10),
            )
            card.grid(
                row=row,
                column=0,
                sticky="ew",
                pady=(0, 7),
            )
            card.columnconfigure(0, weight=1)

            text_area = ttk.Frame(
                card,
                style="Card.TFrame",
            )
            text_area.grid(
                row=0,
                column=0,
                sticky="ew",
                padx=(0, 16),
            )

            ttk.Label(
                text_area,
                text=rule["name"],
                style="Card.Section.TLabel",
            ).pack(anchor="w")

            ttk.Label(
                text_area,
                text=rule["description"],
                style="Card.Muted.TLabel",
                wraplength=940,
                justify="left",
            ).pack(
                anchor="w",
                pady=(3, 0),
            )

            switch = ToggleSwitch(
                card,
                variable=self.house_rule_vars[key],
            )
            switch.grid(
                row=0,
                column=1,
                sticky="e",
            )


    def _custom_enemies_for_simulation(self):
        if "enemy" in self._built_tabs:
            self._save_active_enemy_editor()
            return [dict(profile) for profile in self._enemy_profiles]
        stored = self._warrior_snapshots.get("enemy", self._enemy_profiles)
        return [dict(profile) for profile in stored]

    def _manual_enemy_indices(self, enemies, total_simulations, seed):
        variants = 24 if self.enemy_level.get() else 1
        count = max(1, len(enemies) * variants)
        rng = np.random.default_rng(seed + 808)
        return rng.integers(0, count, total_simulations, dtype=np.int64)

    def setup_tab_candidate(self, tab):

        selector = self.candidate_source_frame = ttk.LabelFrame(tab, text=self._tr("identity"))
        selector.pack(fill="x", padx=15, pady=(12, 3))
        selector.columnconfigure(1, weight=2)
        selector.columnconfigure(3, weight=2)
        selector.columnconfigure(5, weight=2)
        self.candidate_name_label = ttk.Label(selector, text=self._tr("name"))
        self.candidate_name_label.grid(row=0, column=0, padx=(10, 4), pady=7)
        ttk.Entry(selector, textvariable=self.candidate_name).grid(
            row=0, column=1, sticky="ew", padx=(0, 10), pady=7
        )
        self.candidate_band_label = ttk.Label(selector, text=self._tr("warband"))
        self.candidate_band_label.grid(row=0, column=2, padx=(0, 4), pady=7)
        self.candidate_band_combo = ttk.Combobox(
            selector, state="readonly",
            values=(self._tr("free_selection"), *(band.name for band in self._candidate_bands)),
        )
        self.candidate_band_combo.grid(row=0, column=3, sticky="ew", padx=(0, 10), pady=7)
        self.candidate_band_combo.bind("<<ComboboxSelected>>", self._candidate_band_changed)
        self.candidate_profile_label = ttk.Label(selector, text=self._tr("warrior"))
        self.candidate_profile_label.grid(row=0, column=4, padx=(0, 4), pady=7)
        self.candidate_profile_combo = ttk.Combobox(selector, state="disabled")
        self.candidate_profile_combo.grid(row=0, column=5, sticky="ew", padx=(0, 10), pady=7)
        self.candidate_profile_combo.bind("<<ComboboxSelected>>", self._candidate_profile_changed)

        action_frame = ttk.Frame(selector)
        action_frame.grid(row=1, column=0, columnspan=6, sticky="ew", padx=10, pady=(0, 7))
        ttk.Label(action_frame, textvariable=self.candidate_catalog_status).pack(side="left", fill="x", expand=True)

        self.candidate_config = WarriorConfigFrame(
            tab,
            "Candidate Warrior Configuration",
            show_house_rules=False,
            skill_descriptions=self._warrior_skill_descriptions,
            skill_categories=self._warrior_skill_categories,
        )

        self.candidate_config.pack(
            fill="both",
            expand=True,
            padx=5,
            pady=(3, 12),
        )
        self.candidate_config.set_option_filter(None)
        if "candidate" in self._warrior_snapshots:
            self._restore_candidate_payload(self._warrior_snapshots["candidate"])
        else:
            self.candidate_band_combo.set(self._tr("free_selection"))

    def _candidate_config_dict(self):
        config = self.candidate_config.get_config_dict()
        config.update({
            "candidate_name": self.candidate_name.get().strip() or "Candidate",
            "candidate_band_id": self.candidate_band_id.get(),
            "candidate_profile_id": self.candidate_profile_id.get(),
        })
        return config

    def _candidate_band_changed(self, _event=None):
        band = self._band_by_name.get(self.candidate_band_combo.get())
        if band is None:
            self.candidate_band_id.set("")
            self.candidate_profile_id.set("")
            self.candidate_profile_combo.set("")
            self.candidate_profile_combo.config(values=(), state="disabled")
            self.candidate_config.set_option_filter(None)
            self.candidate_catalog_status.set("Free selection: all simulator options are available.")
            self._refresh_improvement_filters()
            return
        self.candidate_band_id.set(band.band_id)
        self.candidate_profile_id.set("")
        self.candidate_profile_combo.config(
            values=tuple(profile.name for profile in band.profiles), state="readonly"
        )
        self.candidate_profile_combo.set("Select a Warrior")
        self.candidate_config.set_option_filter(
            None, extra_skills=(skill.name for skill in band.skills)
        )
        self.candidate_catalog_status.set(
            f"{len(band.profiles)} profiles available. Choose one to apply its restrictions."
        )
        self._refresh_improvement_filters()

    def _candidate_profile_changed(self, _event=None):
        band = next((b for b in self._candidate_bands if b.band_id == self.candidate_band_id.get()), None)
        if band is None:
            return
        profile = next((p for p in band.profiles if p.name == self.candidate_profile_combo.get()), None)
        if profile is None:
            return
        self.candidate_profile_id.set(profile.profile_id)
        self.candidate_name.set(profile.name)
        default_weapon = next(iter(usable_main_weapons(profile)), "Dagger")
        self.candidate_config.load_config({
            **profile.stats, **profile.combat_traits,
            "skills": list(profile.combat_traits.get("starting_skills", ())),
            "main_weapon": default_weapon, "off_hand": "None", "armor": "No Armour",
        })
        self.candidate_config.set_option_filter(profile)
        omitted = []
        if profile.fixed_equipment:
            omitted.append("documented fixed equipment")
        if profile.rules:
            omitted.append("profile-specific rules")
        suffix = f" · {' and '.join(omitted)}" if omitted else ""
        self.candidate_catalog_status.set(
            f"Canonical profile applied: {profile.band_name} · {profile.profile_type} · "
            f"{self._tr('movement')}: {format_movement(profile.movement_inches, self.locale.get())}{suffix}."
        )
        self._refresh_improvement_filters()

    def _candidate_metadata(self):
        profile = find_profile(self.candidate_band_id.get(), self.candidate_profile_id.get())
        metadata = {
            "name": self.candidate_name.get().strip() or "Candidate",
            "band_id": self.candidate_band_id.get(),
            "profile_id": self.candidate_profile_id.get(),
            "band_name": "Free Selection",
            "profile_name": "Free Profile",
        }
        if profile:
            metadata.update({
                "band_name": profile.band_name, "profile_name": profile.name,
                "profile_type": profile.profile_type, "fixed_equipment": profile.fixed_equipment,
                "restrictions": profile.restrictions, "rules": profile.rules,
                "source": profile.source,
            })
        return metadata

    def _candidate_workbook_payload(self):
        difficulties = [name for name, variable in self.enemy_difficulties.items() if variable.get()]
        opponent = {
            "mode": "Random Sample" if self.enemy_mode.get() == "sample" else "Configurable Opponent",
            "level": self.enemy_level.get(),
            "description": ", ".join(difficulties) if self.enemy_mode.get() == "sample" else "Configurable Profile",
        }
        # They are also retained while the random sample is active, so
        # "Load Enemies" can always restore the configured profiles.
        enemy_profiles = self._custom_enemies_for_simulation()
        return {
            "catalog_schema_version": CATALOG_SCHEMA_VERSION,
            "catalog_categories": sorted(self._catalog_categories),
            "locale": self.locale.get(),
            "config": self._candidate_for_simulation(), "candidate": self._candidate_metadata(),
            "house_rules": self._house_rules_payload(),
            "opponent": opponent,
            "enemies": {
                "mode": self.enemy_mode.get(), "level": self.enemy_level.get(),
                "difficulties": difficulties, "profiles": enemy_profiles,
            },
            "results": self._simulation_results_payload(),
        }

    def _simulation_results_payload(self):
        specs = (
            ("combos", "Improvements", self.simulations_combos),
            ("weapons", "Weapons", self.simulations_weapons),
            ("equipment", "Equipment", self.simulations_equipment),
        )
        results = []
        for target, title, count_var in specs:
            table_data = getattr(self, f"_{target.rstrip('s')}_table_data", None)
            card_data = getattr(self, f"_{target.rstrip('s')}_card_data", None)
            if target == "equipment":
                table_data = getattr(self, "_equipment_table_data", None)
                card_data = getattr(self, "_equipment_card_data", None)
            if not table_data:
                continue
            selection_count = (
                self.improvement_count.get() if target == "combos"
                else self.equipment_max_items.get() if target == "equipment"
                else None
            )
            headers, rows = self._result_export_rows(
                target, table_data, selection_count=selection_count
            )
            results.append({
                "format_version": FORMAT_VERSION,
                "target": target, "title": title,
                "selection_count": selection_count,
                "iterations": int(count_var.get()),
                "generated_at": getattr(self, f"_{target}_generated_at", datetime.now().isoformat(timespec="seconds")),
                "opponent": self._opponent_description(),
                "view": {"combos": self.combo_view, "weapons": self.weapon_view,
                         "equipment": self.equipment_view}[target].get(),
                "headers": headers, "rows": rows,
                "table_data": table_data, "card_data": card_data,
            })
        return results

    def _opponent_description(self):
        if self.enemy_mode.get() == "custom":
            names = [p.get("enemy_name", "Enemy") for p in self._custom_enemies_for_simulation()]
            return f"Configurable opponent (level {self.enemy_level.get()}): {', '.join(names)}"
        difficulties = [name for name, var in self.enemy_difficulties.items() if var.get()]
        return f"Random sample (level {self.enemy_level.get()}): {', '.join(difficulties)}"

    @staticmethod
    def _result_export_rows(target, table_data, selection_count=None):
        data, equipment, *extra = table_data
        loadout_costs = extra[0] if target in {"weapons", "equipment"} and extra else {}
        label_headers = {
            "combos": tuple(
                f"Improvement {index}" for index in range(1, (selection_count or 2) + 1)
            ),
            "weapons": ("Main Weapon", "Off-Hand Weapon"),
            "equipment": tuple(
                f"Item {index}" for index in range(1, (selection_count or 3) + 1)
            ),
        }[target]
        value_headers = (
            *(f"{title} %" for _mode, title in COMBAT_MODES),
            *(f"{title} Hit %" for _mode, title in COMBAT_MODES),
        )
        if target in {"weapons", "equipment"}:
            value_headers = (*value_headers, "Cost", "MOTTA Score")
        headers = (*label_headers, *value_headers, "Best Mode", "Optimal Equipment")
        rows_by_label = {}
        base_rates = {}
        for mode, mode_data in data.items():
            base_rates[mode], values = mode_data
            for label, rate, impact in values:
                rows_by_label.setdefault(label, {})[mode] = (rate, impact)
        rows_by_label = {"BASELINE": {mode: (rate, 0.0) for mode, rate in base_rates.items()}, **rows_by_label}
        rows = []
        for label, values in rows_by_label.items():
            parts = {
                "combos": tuple(label.split(" + ")),
                "weapons": tuple(label.split(" || ", 1)),
                "equipment": tuple(part for part in label.split(" || ") if part),
            }[target]
            parts = (*parts, *("—" for _ in range(len(label_headers) - len(parts))))
            available = {
                mode: result for mode, result in values.items()
                if result and result[0] is not None
            }
            if not available:
                continue
            best_mode = max(available, key=lambda mode: available[mode][0])
            rates = tuple(
                available[mode][0] if mode in available else None
                for mode, _title in COMBAT_MODES
            )
            impacts = tuple(
                available[mode][1] if mode in available else None
                for mode, _title in COMBAT_MODES
            )
            extra_values = ()
            if target in {"weapons", "equipment"} and label != "BASELINE":
                if target == "weapons":
                    main_cost, off_cost = loadout_costs.get(label, (None, None))
                    _display, total_cost = CombatLabApp._weapon_cost_display(main_cost, off_cost)
                else:
                    _display, total_cost = CombatLabApp._equipment_cost_display(
                        loadout_costs.get(label, (None,))
                    )
                motta = CombatLabApp._motta_index(
                    available[best_mode][1], total_cost
                )
                extra_values = (total_cost, motta)
            elif target in {"weapons", "equipment"}:
                extra_values = (None, None)
            rows.append((
                *parts, *rates, *impacts, *extra_values,
                best_mode, equipment.get(best_mode, "—"),
            ))
        return headers, rows

    def _save_candidate(self):
        default_name = re.sub(r"[^\w.-]+", "_", self.candidate_name.get().strip(), flags=re.UNICODE).strip("_") or "Candidate"
        path = filedialog.asksaveasfilename(
            title="Save Simulation Workbook", defaultextension=".xlsx",
            filetypes=(("Excel Workbook", "*.xlsx"),), initialfile=f"{default_name}.xlsx",
        )
        if not path:
            return
        try:
            save_candidate_workbook(path, self._candidate_workbook_payload())
        except (OSError, ValueError, KeyError, TypeError) as exc:
            messagebox.showerror("Could Not Save", str(exc))
            return
        self.candidate_workbook_path = path
        messagebox.showinfo(
            "Workbook Saved",
            "The candidate, enemies, and sample configuration have been saved.",
        )

    def _load_candidate(self):
        path = filedialog.askopenfilename(
            title="Load Simulation Workbook", filetypes=(("Excel Workbook", "*.xlsx"),)
        )
        if not path:
            return
        try:
            payload = load_candidate_workbook(path)
            self._apply_workbook_context(payload)
            self._restore_house_rules(payload.get("house_rules"))
            self._restore_candidate_state(payload["config"])
            enemies = payload.get("enemies") or {}
            self.enemy_mode.set(enemies.get("mode", self.enemy_mode.get()))
            self.enemy_level.set(int(enemies.get("level", self.enemy_level.get())))
            selected_difficulties = set(enemies.get("difficulties", ()))
            if selected_difficulties:
                for name, variable in self.enemy_difficulties.items():
                    variable.set(name in selected_difficulties)
            self._restore_enemies_state(enemies, force_custom=False)
            self._restore_results_state(payload.get("results") or ())
        except (OSError, CandidateWorkbookError, KeyError, ValueError) as exc:
            messagebox.showerror("Could Not Load", str(exc))
            return
        self.candidate_workbook_path = path
        messagebox.showinfo("Workbook Loaded", "The candidate, enemies, and simulations were restored successfully.")

    def _choose_workbook(self, title):
        return filedialog.askopenfilename(title=title, filetypes=(("Excel Workbook", "*.xlsx"),))

    def _apply_workbook_context(self, payload):
        categories = payload.get("catalog_categories")
        if not isinstance(categories, list):
            legacy = str(payload.get("catalog_category", "all")).casefold()
            categories = list(SELECTABLE_CATEGORIES) if legacy == "all" else [legacy]
        categories = {
            str(value).casefold() for value in categories
            if str(value).casefold() in SELECTABLE_CATEGORIES
        } or set(SELECTABLE_CATEGORIES)
        locale = str(payload.get("locale", self.locale.get())).casefold()
        if locale not in {"en", "es"}:
            locale = "en"
        self.locale.set(locale)
        self.locale_combo.set("Español" if locale == "es" else "English")
        self._catalog_categories = categories
        for category, variable in self.catalog_category_vars.items():
            variable.set(category in categories)
        self._candidate_bands = bands_for_categories(categories)
        self._band_by_name = {band.name: band for band in self._candidate_bands}
        if "candidate" in self._built_tabs:
            self.candidate_band_combo.configure(
                values=(self._tr("free_selection"), *(band.name for band in self._candidate_bands))
            )
        self._apply_locale()
        _save_preferences(locale, categories)

    def _load_candidate_only(self):
        path = self._choose_workbook("Load Candidate")
        if not path:
            return
        try:
            payload = load_candidate_workbook(path)
            self._apply_workbook_context(payload)
            self._restore_candidate_state(payload["config"])
        except (OSError, CandidateWorkbookError, KeyError, ValueError) as exc:
            messagebox.showerror("Could Not Load", str(exc))
            return
        messagebox.showinfo("Candidate Loaded", "The current candidate was replaced successfully.")

    def _load_enemies_only(self):
        path = self._choose_workbook("Load Enemies")
        if not path:
            return
        try:
            payload = load_candidate_workbook(path)
            self._apply_workbook_context(payload)
            self._restore_enemies_state(payload["enemies"], force_custom=True)
        except (OSError, CandidateWorkbookError, KeyError, ValueError) as exc:
            messagebox.showerror("Could Not Load", str(exc))
            return
        messagebox.showinfo("Enemies Loaded", "The current enemies were replaced and Configurable Opponent mode was activated.")

    def _restore_candidate_state(self, config):
        self._warrior_snapshots["candidate"] = dict(config)
        self.candidate_name.set(config.get("candidate_name", "Candidate"))
        self.candidate_band_id.set(config.get("candidate_band_id", ""))
        self.candidate_profile_id.set(config.get("candidate_profile_id", ""))
        if "candidate" in self._built_tabs:
            self._restore_candidate_payload(config)

    def _costs_with_house_rules(self, costs):
        adjusted = dict(costs)
        if self.house_rule_vars["cheap_armour"].get():
            armour_items = {
                *(armor for armor in BODY_ARMORS if armor != "No Armour"),
                "Helmet", "Shield", "Buckler",
            }
            for item in armour_items:
                if item in adjusted:
                    adjusted[item] = float(math.ceil(adjusted[item] / 2.0))
        if self.house_rule_vars["expensive_junk"].get():
            for item in ("Mace", "Sling"):
                adjusted[item] = 5.0
        return adjusted

    def _restore_enemies_state(self, enemies, force_custom=False):
        profiles = [dict(profile) for profile in (enemies.get("profiles") or ())]
        if not profiles:
            profiles = [{"enemy_name": "Enemy 1"}]
        was_built = "enemy" in self._built_tabs
        if was_built:
            self._unload_tab("enemy")
        self.enemy_mode.set("custom" if force_custom else enemies.get("mode", "sample"))
        self.enemy_level.set(int(enemies.get("level", self.enemy_level.get())))
        selected = set(enemies.get("difficulties") or ())
        for name, variable in self.enemy_difficulties.items():
            variable.set(name in selected)
        self._enemy_profiles = profiles
        self._warrior_snapshots["enemy"] = [dict(profile) for profile in profiles]
        if was_built:
            self._build_lazy_tab("enemy")

    def _restore_results_state(self, results):
        for result in results:
            target = result.get("target")
            setattr(self, f"_{target}_generated_at", result.get("generated_at"))
            table_name = {"combos": "_combo_table_data",
                          "weapons": "_weapon_table_data", "equipment": "_equipment_table_data"}[target]
            card_name = {"combos": "_combo_card_data",
                         "weapons": "_weapon_card_data", "equipment": "_equipment_card_data"}[target]
            setattr(self, table_name, result.get("table_data"))
            setattr(self, card_name, result.get("card_data"))
            if target == "combos":
                self.improvement_count.set(int(result.get("selection_count", 1)))
            elif target == "equipment":
                self.equipment_max_items.set(int(result.get("selection_count", 1)))
            count_var = {"combos": self.simulations_combos,
                         "weapons": self.simulations_weapons, "equipment": self.simulations_equipment}[target]
            count_var.set(str(result.get("iterations", count_var.get())))
            view_var = {"combos": self.combo_view,
                        "weapons": self.weapon_view, "equipment": self.equipment_view}[target]
            view_var.set(result.get("view", view_var.get()))
            if target in self._built_tabs:
                self._restore_simulation_tab(target)

    def _restore_candidate_payload(self, config):
        self.candidate_name.set(config.get("candidate_name", "Candidate"))
        band_id = config.get("candidate_band_id", "")
        profile_id = config.get("candidate_profile_id", "")
        profile = find_profile(band_id, profile_id)
        if profile:
            self.candidate_band_id.set(band_id)
            self.candidate_profile_id.set(profile_id)
            self.candidate_band_combo.set(profile.band_name)
            band = next(b for b in self._candidate_bands if b.band_id == band_id)
            self.candidate_profile_combo.config(values=tuple(p.name for p in band.profiles), state="readonly")
            self.candidate_profile_combo.set(profile.name)
            self.candidate_config.set_option_filter(profile)
            self.candidate_catalog_status.set(f"Profile loaded: {profile.band_name} · {profile.name}.")
        else:
            self.candidate_band_id.set("")
            self.candidate_profile_id.set("")
            self.candidate_band_combo.set("Free Selection")
            self.candidate_profile_combo.set("")
            self.candidate_profile_combo.config(values=(), state="disabled")
            self.candidate_config.set_option_filter(None)
            self.candidate_catalog_status.set("Free selection loaded.")
        self.candidate_config.load_config(config)
        self.candidate_config.set_option_filter(profile)

    def setup_tab_enemy(self, tab):

        self.enemy_check_widgets = []

        level_frame = ttk.LabelFrame(
            tab,
            text=" Opponent Level ",
        )
        level_frame.pack(fill="x", padx=15, pady=(0, 7))
        ttk.Label(
            level_frame,
            text="Level Increases:",
            font=("Arial", 10, "bold"),
        ).pack(side="left", padx=(12, 6), pady=8)
        self.enemy_level_spin = ttk.Spinbox(
            level_frame, from_=0, to=20, textvariable=self.enemy_level,
            width=6, justify="center", font=("Arial", 10, "bold"),
        )
        self.enemy_level_spin.pack(side="left", pady=8)
        ttk.Label(
            level_frame,
            text="Each level adds a new random improvement in every combat.",
        ).pack(side="left", padx=12, pady=8)
        ToolTip(
            self.enemy_level_spin,
            "Applies to every opponent mode. Each level adds a random improvement to the opponent.",
        )

        self.enemy_mode_notebook = ttk.Notebook(tab)
        self.enemy_mode_notebook.pack(fill="both", expand=True, padx=15, pady=(0, 5))
        self.enemy_sample_page = ttk.Frame(self.enemy_mode_notebook)
        self.enemy_custom_page = ttk.Frame(self.enemy_mode_notebook)
        self.enemy_mode_notebook.add(self.enemy_sample_page, text="Random Sample")
        self.enemy_mode_notebook.add(self.enemy_custom_page, text="Configurable Opponents")
        self.enemy_mode_notebook.bind("<<NotebookTabChanged>>", self._enemy_mode_tab_changed)

        ttk.Label(
            self.enemy_sample_page,
            text=(
                "The simulator selects profiles, legal equipment, and improvements "
                "for each combat, respecting the frequency of each difficulty group."
            ),
            justify="left",
            wraplength=1050,
        ).pack(
            anchor="w",
            padx=12,
            pady=(12, 8),
        )

        self.checklist_frame = ttk.Frame(
            self.enemy_sample_page
        )

        self.checklist_frame.pack(
            fill="x",
            padx=12,
            pady=(2, 10),
        )

        difficulty_row = ttk.Frame(self.checklist_frame)
        difficulty_row.pack(fill="x", pady=(0, 5))
        ttk.Label(difficulty_row, text="Difficulty:", font=("Arial", 9, "bold")).pack(side="left")
        for difficulty in DIFFICULTIES:
            checkbox = ttk.Checkbutton(
                difficulty_row,
                text=difficulty,
                variable=self.enemy_difficulties[difficulty],
            )
            checkbox.pack(side="left", padx=8)
            self.enemy_check_widgets.append(checkbox)

        ttk.Label(
            self.enemy_custom_page,
            text=(
                "Each tab represents a possible opponent. "
                "The level adds random improvements to all of them."
            ),
            justify="left",
        ).pack(
            anchor="w",
            padx=12,
            pady=(8, 4),
        )

        enemy_tools = ttk.Frame(self.enemy_custom_page)
        enemy_tools.pack(fill="x", padx=10, pady=(2, 0))
        self.btn_add_enemy = ttk.Button(
            enemy_tools, text="＋ Add Enemy", command=self._add_enemy_profile
        )
        self.btn_add_enemy.pack(side="left")
        self.btn_remove_enemy = ttk.Button(
            enemy_tools, text="− Remove Enemy", command=self._remove_enemy_profile
        )
        self.btn_remove_enemy.pack(side="left", padx=6)

        self.enemy_notebook = ttk.Notebook(self.enemy_custom_page)
        self.enemy_notebook.pack(fill="both", expand=True, padx=10, pady=(3, 5))
        self.enemy_notebook.bind("<<NotebookTabChanged>>", self._enemy_tab_changed)

        stored = self._warrior_snapshots.get("enemy", self._enemy_profiles)
        self._enemy_profiles = [dict(profile) for profile in stored]
        if not self._enemy_profiles:
            self._enemy_profiles = [{"enemy_name": "Enemy 1"}]
        self._active_enemy_editor_index = None
        self.enemy_editor = None
        self.enemy_config = None
        for index, profile in enumerate(self._enemy_profiles):
            page = ttk.Frame(self.enemy_notebook)
            self.enemy_notebook.add(page, text=profile.get("enemy_name", f"Enemy {index + 1}"))
        self._enemy_materialize_after_id = self.after_idle(self._materialize_selected_enemy)

        self.toggle_enemy_mode()

    def _enemy_mode_tab_changed(self, _event=None):
        if not hasattr(self, "enemy_mode_notebook"):
            return
        self.enemy_mode.set(
            "custom"
            if self.enemy_mode_notebook.select() == str(self.enemy_custom_page)
            else "sample"
        )
        self.toggle_enemy_mode(sync_tab=False)

    def toggle_enemy_mode(self, sync_tab=True):

        is_custom = (
            self.enemy_mode.get()
            == "custom"
        )

        if sync_tab and hasattr(self, "enemy_mode_notebook"):
            target = self.enemy_custom_page if is_custom else self.enemy_sample_page
            if self.enemy_mode_notebook.select() != str(target):
                self.enemy_mode_notebook.select(target)

        if is_custom:

            for checkbox in (
                self.enemy_check_widgets
            ):
                checkbox.config(
                    state="disabled"
                )

            if self._enemy_editor_exists():
                self.enemy_editor.set_enabled(True)

        else:

            for checkbox in (
                self.enemy_check_widgets
            ):
                checkbox.config(
                    state="normal"
                )

            if self._enemy_editor_exists():
                self.enemy_editor.set_enabled(False)

        if hasattr(self, "btn_remove_enemy"):
            self.btn_remove_enemy.config(state="normal" if is_custom else "disabled")
        if hasattr(self, "btn_add_enemy"):
            self.btn_add_enemy.config(state="normal" if is_custom else "disabled")
        if hasattr(self, "enemy_notebook"):
            self.enemy_notebook.state(("!disabled",) if is_custom else ("disabled",))

    def _save_active_enemy_editor(self):
        index = self._active_enemy_editor_index
        if index is not None and self._enemy_editor_exists():
            self._enemy_profiles[index] = self.enemy_editor.get_config_dict()

    def _enemy_editor_exists(self):
        editor = getattr(self, "enemy_editor", None)
        if editor is None:
            return False
        try:
            return bool(editor.winfo_exists())
        except tk.TclError:
            return False

    def _materialize_selected_enemy(self):
        self._enemy_materialize_after_id = None
        if not hasattr(self, "enemy_notebook") or not self.enemy_notebook.tabs():
            return
        selected = self.enemy_notebook.select()
        index = self.enemy_notebook.index(selected)
        if index == self._active_enemy_editor_index and self._enemy_editor_exists():
            return
        self._save_active_enemy_editor()
        if self._enemy_editor_exists():
            self.enemy_editor.destroy()
        page = self.nametowidget(selected)
        self._active_enemy_editor_index = index
        self.enemy_editor = EnemyProfileEditor(
            page,
            self._candidate_bands,
            self._enemy_profiles[index],
            on_name_change=lambda name, page_id=selected:
                self.enemy_notebook.tab(page_id, text=name),
            skill_descriptions=self._warrior_skill_descriptions,
            skill_categories=self._warrior_skill_categories,
        )
        self.enemy_editor.pack(fill="both", expand=True)
        self.enemy_config = self.enemy_editor.config  # Shared-control compatibility.
        self.enemy_editor.set_enabled(self.enemy_mode.get() == "custom")

    def _enemy_tab_changed(self, _event=None):
        self._materialize_selected_enemy()

    def _add_enemy_profile(self):
        self._save_active_enemy_editor()
        number = len(self._enemy_profiles) + 1
        self._enemy_profiles.append({"enemy_name": f"Enemy {number}"})
        page = ttk.Frame(self.enemy_notebook)
        self.enemy_notebook.add(page, text=f"Enemy {number}")
        self.enemy_notebook.select(page)
        self._materialize_selected_enemy()

    def _remove_enemy_profile(self):
        if len(self._enemy_profiles) <= 1:
            messagebox.showinfo("Enemies", "At least one manual profile must remain.")
            return
        index = self.enemy_notebook.index(self.enemy_notebook.select())
        self._save_active_enemy_editor()
        page_id = self.enemy_notebook.tabs()[index]
        if hasattr(self, "enemy_editor"):
            self.enemy_editor.destroy()
        self._active_enemy_editor_index = None
        self.enemy_notebook.forget(page_id)
        del self._enemy_profiles[index]
        self._materialize_selected_enemy()

    def _sort_treeview(self, tree, column, descending=False):
        rows = [(tree.set(item, column), item) for item in tree.get_children("")]
        rows.sort(key=lambda row: self._tree_sort_key(row[0]), reverse=descending)
        for index, (_, item) in enumerate(rows):
            tree.move(item, "", index)
        tree.heading(column, command=lambda: self._sort_treeview(tree, column, not descending))

    def _sort_weapon_cost(self, descending=False):
        rows = [
            (self.weapon_tree.set(item, "CostTotal"), item)
            for item in self.weapon_tree.get_children("")
        ]
        rows.sort(
            key=lambda row: self._tree_sort_key(row[0]), reverse=descending
        )
        for index, (_value, item) in enumerate(rows):
            self.weapon_tree.move(item, "", index)
        self.weapon_tree.heading(
            "Cost",
            command=lambda: self._sort_weapon_cost(not descending),
        )

    def _sort_equipment_cost(self, descending=False):
        rows = [
            (self.equipment_tree.set(item, "CostTotal"), item)
            for item in self.equipment_tree.get_children("")
        ]
        rows.sort(
            key=lambda row: self._tree_sort_key(row[0]), reverse=descending
        )
        for index, (_value, item) in enumerate(rows):
            self.equipment_tree.move(item, "", index)
        self.equipment_tree.heading(
            "Cost",
            command=lambda: self._sort_equipment_cost(not descending),
        )

    @staticmethod
    def _tree_sort_key(value):
        value = str(value)
        text = value.replace("★", "").replace("%", "").replace("+", "").replace("−", "-").strip()
        number = re.search(r"-?\d+(?:[.,]\d+)?", text)
        if number:
            return 0, float(number.group().replace(",", ".")), ""
        return 1, 0.0, value.casefold()

    def _configure_sortable_tree(self, tree, columns):
        tree.configure(show="tree headings")
        tree.heading("#0", text="")
        tree.column("#0", width=0, minwidth=0, stretch=False)
        for column, title in columns:
            tree.heading(
                column,
                text=title,
                anchor="center",
                command=lambda c=column: self._sort_treeview(tree, c, False),
            )
            tree.column(column, anchor="center")
        tree.bind(
            "<Configure>",
            lambda _event, result_tree=tree: self._center_tree_columns(result_tree),
            add="+",
        )

    @staticmethod
    def _visible_tree_columns(tree):
        columns = tree.cget("displaycolumns")
        if columns == "#all":
            return tuple(tree.cget("columns"))
        return tuple(columns)

    def _autosize_tree_columns(self, tree):
        """Adjust displayed columns and keep the block centred."""
        text_font = tkfont.nametofont("TkDefaultFont")
        for column in self._visible_tree_columns(tree):
            widest = text_font.measure(tree.heading(column, "text"))
            for item in tree.get_children(""):
                widest = max(widest, text_font.measure(str(tree.set(item, column))))
            tree.column(column, width=widest + 28, minwidth=30, stretch=False)
        self._center_tree_columns(tree)

    @staticmethod
    def _center_tree_columns(tree):
        """Use the empty tree column as a dynamic left margin."""
        try:
            columns = CombatLabApp._visible_tree_columns(tree)
            content_width = sum(int(tree.column(column, "width")) for column in columns)
            margin = max(0, (tree.winfo_width() - content_width) // 2)
            tree.column("#0", width=margin, minwidth=margin, stretch=False)
        except tk.TclError:
            pass

    @staticmethod
    def _pack_scrollable_tree(tree, pady=(4, 10)):
        frame = tree.master
        frame.pack(fill="both", expand=True, padx=10, pady=pady)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        ttk.Sizegrip(frame).grid(row=1, column=1, sticky="se")
        return frame


    def _create_mode_cards(self, parent, target):
        """Single-line summary: equipment, result, delta and switch."""
        section = ttk.Frame(
            parent,
            padding=(20, 2, 20, 1),
        )
        section.pack(fill="x")

        title_row = ttk.Frame(section)
        title_row.pack(fill="x")

        ttk.Label(
            title_row,
            text="HAND CONFIGURATIONS",
            style="Section.TLabel",
        ).pack(side="left")

        help_text = (
            "Each switch shows or hides that hand configuration in the results. "
            "The row displays the actual equipment, win rate and delta."
        )

        container = ttk.Frame(section)
        container.pack(
            fill="x",
            pady=(3, 2),
        )

        cards = {}

        for column, (mode, _title) in enumerate(COMBAT_MODES):
            container.columnconfigure(
                column,
                weight=1,
                uniform="mode_cards",
            )

            card = ttk.Frame(
                container,
                style="Card.TFrame",
                padding=(8, 6),
            )
            card.grid(
                row=0,
                column=column,
                sticky="nsew",
                padx=(0 if column == 0 else 3, 0),
            )
            card.columnconfigure(0, weight=1)

            shown = tk.BooleanVar(value=True)

            equipment = ttk.Label(
                card,
                text="Equipment Pending",
                style="Card.Section.TLabel",
                anchor="w",
            )
            equipment.grid(
                row=0,
                column=0,
                sticky="ew",
            )

            rate = ttk.Label(
                card,
                text="No Results",
                style="Card.Section.TLabel",
            )
            rate.grid(
                row=0,
                column=1,
                sticky="e",
                padx=(8, 0),
            )

            delta = ttk.Label(
                card,
                text="",
                style="Card.Muted.TLabel",
            )
            delta.grid(
                row=0,
                column=2,
                sticky="e",
                padx=(5, 5),
            )

            toggle = ToggleSwitch(
                card,
                variable=shown,
                command=lambda m=mode, t=target:
                    self._toggle_mode_column(t, m),
            )
            toggle.grid(
                row=0,
                column=3,
                sticky="e",
                padx=(4, 0),
            )

            ToolTip(card, help_text)

            cards[mode] = {
                "equipment": equipment,
                "rate": rate,
                "delta": delta,
                "shown": shown,
                "toggle": toggle,
            }

        return cards


    def _toggle_mode_column(self, target, mode):
        if target == "combos":
            visible, cards = self.combo_visible_modes, self.combo_cards
        elif target == "equipment":
            visible, cards = self.equipment_visible_modes, self.equipment_cards
        else:
            visible, cards = self.weapon_visible_modes, self.weapon_cards

        if mode in visible:
            if len(visible) == 1:
                return
            visible.remove(mode)
        else:
            visible.add(mode)

        self._apply_result_view(target)
        renderers = {
            "combos": self._render_combo_table,
            "equipment": self._render_equipment_table,
            "weapons": self._render_weapon_table,
        }
        renderers[target]()
        self._refresh_mode_card_visibility(cards, visible)

    @staticmethod
    def _refresh_mode_card_visibility(cards, visible):
        for mode, _title in COMBAT_MODES:
            is_visible = mode in visible
            cards[mode]["shown"].set(is_visible)
            if is_visible and len(visible) == 1:
                cards[mode]["toggle"].config(
                    state="disabled",
                )
            else:
                cards[mode]["toggle"].config(
                    state="normal",
                )

    @staticmethod
    def _reset_mode_cards(cards, visible):
        for card in cards.values():
            card["equipment"].config(text="Preparing equipment...")
            card["rate"].config(text="Calculating...")
            card["delta"].config(text="")
        CombatLabApp._refresh_mode_card_visibility(cards, visible)

    def _apply_result_view(self, target):
        if target == "combos":
            tree, view_var = self.combo_tree, self.combo_view
            visible = self.combo_visible_modes
            fixed = tuple(
                f"Improvement{index}" for index in range(1, self.improvement_count.get() + 1)
            )
        elif target == "equipment":
            tree, view_var = self.equipment_tree, self.equipment_view
            visible = self.equipment_visible_modes
            fixed = tuple(
                f"Item{index}" for index in range(1, self.equipment_max_items.get() + 1)
            )
        else:
            tree, view_var = self.weapon_tree, self.weapon_view
            visible, fixed = self.weapon_visible_modes, ("Main", "Off")

        if target == "weapons":
            tree.configure(displaycolumns=("Main", "Off", "Optimal", "Motta", "Cost"))
            return
        if target == "equipment":
            tree.configure(displaycolumns=(
                *fixed, "Optimal", "Motta", "Cost",
            ))
            return

        if view_var.get() == "optimal":
            optimal_columns = (*fixed, "Optimal")
            if target != "weapons":
                optimal_columns += ("Equipment",)
            tree.configure(displaycolumns=optimal_columns)
        else:
            tree.configure(
                displaycolumns=(
                    *fixed,
                    *(mode for mode, _title in COMBAT_MODES if mode in visible),
                )
            )

    def _change_result_view(self, target):
        self._apply_result_view(target)
        renderers = {
            "combos": self._render_combo_table,
            "equipment": self._render_equipment_table,
            "weapons": self._render_weapon_table,
        }
        renderers[target]()

    def _restore_simulation_tab(self, target):
        if target == "combos":
            table_name, cards_name = "_combo_table_data", "_combo_card_data"
            cards, renderer = self.combo_cards, self._render_combo_table
        elif target == "equipment":
            table_name, cards_name = "_equipment_table_data", "_equipment_card_data"
            cards, renderer = None, self._render_equipment_table
        else:
            table_name, cards_name = "_weapon_table_data", "_weapon_card_data"
            cards, renderer = None, self._render_weapon_table
        card_data = getattr(self, cards_name, None)
        if card_data and cards is not None:
            base_rates, user_mode_key, equipment = card_data
            self._update_mode_cards(cards, base_rates, user_mode_key, equipment)
        self._apply_result_view(target)
        if getattr(self, table_name, None):
            renderer()

    def _clear_combo_filters(self):
        self.combo_search.set("")
        self._render_combo_table()

    @staticmethod
    def _combo_parts(label):
        return tuple(label.split(" + "))

    @staticmethod
    def _combo_matches(parts, search):
        normalize = lambda text: "".join(
            character for character in unicodedata.normalize("NFD", text.casefold())
            if unicodedata.category(character) != "Mn"
        )
        query = normalize(search.strip())
        return not query or query in normalize(" + ".join(parts))

    @staticmethod
    def _best_visible_mode(values, visible_modes):
        available = set(values).intersection(visible_modes)
        if not available:
            return None
        return max(available, key=lambda mode: values[mode][0])

    @staticmethod
    def _equipment_description(candidate):
        main = candidate.get("main_weapon", "—")
        off = candidate.get("off_hand", "None")
        main_material = candidate.get("main_weapon_material", "Normal")
        off_material = candidate.get("offhand_material", "Normal")

        if main_material != "Normal":
            main = f"{main} ({main_material})"
        if off_material != "Normal" and off not in ("None", "Shield"):
            off = f"{off} ({off_material})"
        return main if off == "None" else f"{main} + {off}"

    def _update_mode_cards(self, cards, base_rates, user_mode_key, equipment):
        user_rate = base_rates[user_mode_key]
        if cards is getattr(self, "combo_cards", None):
            visible = self.combo_visible_modes
        elif cards is getattr(self, "equipment_cards", None):
            visible = self.equipment_visible_modes
        else:
            visible = self.weapon_visible_modes
        for mode, _title in COMBAT_MODES:
            rate = base_rates[mode]
            delta = rate - user_rate
            cards[mode]["equipment"].config(text=equipment.get(mode, "—"))
            cards[mode]["rate"].config(text=f"{rate:.2f}%")
            if delta > 0.00001:
                arrow, color = "▲", DELTA_POSITIVE
            elif delta < -0.00001:
                arrow, color = "▼", DELTA_NEGATIVE
            else:
                arrow, color = "=", DELTA_NEUTRAL
            cards[mode]["delta"].config(
                text=f"{arrow} {abs(delta):.2f}%",
                foreground=color,
            )
        self._refresh_mode_card_visibility(cards, visible)


    def _create_analysis_header(
        self,
        parent,
        title,
        description,
    ):
        """Compact title and description for analysis tabs."""
        header = ttk.Frame(
            parent,
            padding=(20, 8, 20, 4),
        )
        header.pack(fill="x")

        ttk.Label(
            header,
            text=title,
            style="AnalysisTitle.TLabel",
        ).pack(side="left")

        ttk.Label(
            header,
            text=description,
            style="AnalysisSubtitle.TLabel",
        ).pack(
            side="left",
            padx=(14, 0),
        )


    @staticmethod
    def _create_analysis_controls(parent):
        """Single-row simulation toolbar."""
        controls = ttk.Frame(
            parent,
            style="Card.TFrame",
            padding=(12, 7),
        )
        controls.pack(
            fill="x",
            padx=20,
            pady=(0, 6),
        )
        return controls


    @staticmethod
    def _attach_analysis_progress(
        controls,
        progress_var,
    ):
        """Use all remaining toolbar width for the integrated progress bar."""
        progress_bar = InlineProgressBar(
            controls,
            variable=progress_var,
            maximum=100,
            height=30,
        )
        progress_bar.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(18, 10),
        )

        return progress_bar, progress_bar.status_proxy


    def setup_tab_equipment(self, tab):

        profile = find_profile(
            self.candidate_band_id.get(), self.candidate_profile_id.get()
        )
        allowed = set(equipment_options_for_profile(
            self.candidate_band_id.get(), self.candidate_profile_id.get()
        ))
        self._equipment_filter_allowed = allowed
        for label, variable in self.equipment_item_vars.items():
            if profile:
                variable.set(label in allowed)
            elif label not in allowed:
                variable.set(False)

        self.equipment_progress_var = tk.DoubleVar()
        self._create_analysis_header(
            tab,
            "Equipment",
            (
                "Compare combinations with the exact selected number of items. "
                "The reference is the candidate's exact current equipment."
            ),
        )

        controls = self._create_analysis_controls(tab)
        ttk.Label(controls, text="Simulations:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        ttk.Entry(
            controls, textvariable=self.simulations_equipment, width=12
        ).pack(side="left", padx=(0, 10))
        ttk.Label(controls, text="Number of Items:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        equipment_count_selector = ttk.Combobox(
            controls,
            textvariable=self.equipment_max_items,
            values=(1, 2, 3, 4, 5),
            state="readonly",
            width=3,
            justify="center",
        )
        equipment_count_selector.pack(side="left", padx=(0, 10))
        equipment_count_selector.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._selection_count_changed("equipment"),
        )
        self.btn_equipment_run = self._create_simulate_button(
            controls, self.start_equipment_thread,
        )
        (
            self.equipment_progress_bar,
            self.equipment_status_label,
        ) = self._attach_analysis_progress(
            controls,
            self.equipment_progress_var,
        )

        filter_bar = self._create_compare_panel(tab)
        option_groups = (
            ("Armour", tuple(a for a in BODY_ARMORS if a != "No Armour")),
            (
                "Equipment",
                ("Helmet", "Lucky charm", "Sea Dragon cloak"),
            ),
            ("Preparations", tuple(p for p in PREPARATIONS if p != "None")),
            ("Poisons", tuple(p for p in POISONS if p != "No Poison")),
        )
        for title, values in option_groups:
            self._build_named_filter_menu(
                filter_bar, title, self.equipment_item_vars, values, allowed
            )
        origin = (
            f"Options available for {profile.name} ({profile.band_name})."
            if profile else "Free selection: all items available to the simulator."
        )
        ttk.Label(filter_bar, text=origin, style="Muted.TLabel").pack(side="left", padx=(10, 0))

        equipment_table = ttk.Frame(tab)
        self.equipment_tree = ttk.Treeview(
            equipment_table,
            columns=(
                "Item1", "Item2", "Item3", "Item4", "Item5", "Optimal", "Motta", "Cost",
                "CostTotal", "Equipment",
            ),
            show="headings",
        )
        self._configure_sortable_tree(self.equipment_tree, [
            ("Item1", "Item 1"),
            ("Item2", "Item 2"),
            ("Item3", "Item 3"),
            ("Item4", "Item 4"),
            ("Item5", "Item 5"),
            ("Optimal", "Best Result"),
            ("Motta", "MOTTA Score"),
            ("Cost", "Cost"),
            ("CostTotal", "Cost Total"),
            ("Equipment", "Equipment Used"),
        ])
        for index in range(1, 6):
            self.equipment_tree.column(f"Item{index}", width=170)
        self.equipment_tree.column("Optimal", width=180, anchor="center")
        self.equipment_tree.column("Motta", width=130, anchor="center")
        self.equipment_tree.column("Cost", width=170, anchor="center")
        self.equipment_tree.column("CostTotal", width=0, minwidth=0, stretch=False)
        self.equipment_tree.column("Equipment", width=220, anchor="center")
        self._apply_result_view("equipment")
        self.equipment_tree.heading(
            "Cost", text="Cost", anchor="center",
            command=lambda: self._sort_equipment_cost(False),
        )
        self._pack_scrollable_tree(self.equipment_tree, pady=(2, 6))
        self._restore_simulation_tab("equipment")

    def setup_tab_weapons(self, tab):

        profile = find_profile(
            self.candidate_band_id.get(), self.candidate_profile_id.get()
        )
        allowed_weapons = set(profile.weapons if profile else WEAPONS_ALL)
        allowed_materials = set(profile.materials if profile else WEAPON_MATERIALS)
        allowed_defenses = set(profile.defenses if profile else ("Shield", "Buckler"))
        self._weapon_filter_allowed = allowed_weapons
        self._weapon_material_allowed = allowed_materials
        self._weapon_defense_allowed = allowed_defenses
        for weapon, variable in self.weapon_item_vars.items():
            if weapon not in allowed_weapons:
                variable.set(False)
        for material, variable in self.weapon_material_vars.items():
            if material not in allowed_materials:
                variable.set(False)
        for defense, variable in self.weapon_defense_vars.items():
            if defense not in allowed_defenses:
                variable.set(False)
        if profile:
            for value in allowed_weapons:
                self.weapon_item_vars[value].set(True)
            for value in allowed_materials:
                self.weapon_material_vars[value].set(True)
            for value in allowed_defenses:
                self.weapon_defense_vars[value].set(True)
        if allowed_weapons and not any(
            self.weapon_item_vars[value].get() for value in allowed_weapons
        ):
            first_weapon = next(
                (value for value in WEAPONS_ALL if value in allowed_weapons), None
            )
            if first_weapon:
                self.weapon_item_vars[first_weapon].set(True)
        if not any(self.weapon_material_vars[value].get() for value in allowed_materials):
            self.weapon_material_vars["Normal"].set(True)

        self.weapon_progress_var = tk.DoubleVar()
        self._create_analysis_header(
            tab,
            "Weapons",
            (
                "Compare each weapon alone, with a shield or buckler, in legal pairs, "
                "and weapons that occupy both hands, using only available equipment."
            ),
        )

        controls = self._create_analysis_controls(tab)
        ttk.Label(controls, text="Simulations:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        ttk.Entry(
            controls, textvariable=self.simulations_weapons, width=12
        ).pack(side="left", padx=(0, 10))
        self.btn_weapons_run = self._create_simulate_button(
            controls, self.start_weapon_thread,
        )
        (
            self.weapon_progress_bar,
            self.weapon_status_label,
        ) = self._attach_analysis_progress(
            controls,
            self.weapon_progress_var,
        )

        filter_bar = self._create_compare_panel(tab)
        self._build_weapon_filter_menu(
            filter_bar, "Common Weapons", WEAPONS_GENERAL, allowed_weapons
        )
        self._build_weapon_filter_menu(
            filter_bar, "Special Weapons", WEAPONS_EXCLUSIVE, allowed_weapons
        )
        self._build_named_filter_menu(
            filter_bar, "Materials", self.weapon_material_vars, WEAPON_MATERIALS,
            allowed_materials,
        )
        self._build_named_filter_menu(
            filter_bar, "Defences", self.weapon_defense_vars, ("Shield", "Buckler"),
            allowed_defenses,
        )
        origin = (
            f"Options available for {profile.name} ({profile.band_name})."
            if profile else "Free selection: all simulator options are available."
        )
        ttk.Label(filter_bar, text=origin, style="Muted.TLabel").pack(side="left", padx=(10, 0))

        weapon_table = ttk.Frame(tab)
        self.weapon_tree = ttk.Treeview(
            weapon_table,
            columns=(
                "Main", "Off", "Single", "Shield", "Dual", "TwoHand",
                "Optimal", "Motta", "Cost", "CostTotal", "Equipment",
            ),
            show="headings",
        )
        self._configure_sortable_tree(self.weapon_tree, [
            ("Main", "Main Weapon"),
            ("Off", "Off-Hand Weapon"),
            ("Single", "Free Hand"),
            ("Shield", "Shield"),
            ("Dual", "Two Weapons"),
            ("TwoHand", "Two Hands"),
            ("Optimal", "Best Result"),
            ("Motta", "MOTTA Score"),
            ("Cost", "Cost"),
            ("CostTotal", "Cost Total"),
            ("Equipment", "Equipment Used"),
        ])
        self.weapon_tree.column("Main", width=230)
        self.weapon_tree.column("Off", width=230)
        for mode, _title in COMBAT_MODES:
            self.weapon_tree.column(mode, width=150, anchor="center")
        self.weapon_tree.column("Optimal", width=180, anchor="center")
        self.weapon_tree.column("Cost", width=150, anchor="center")
        self.weapon_tree.column("Motta", width=130, anchor="center")
        self.weapon_tree.column("CostTotal", width=0, minwidth=0, stretch=False)
        self.weapon_tree.column("Equipment", width=220, anchor="center")
        self.weapon_tree.configure(
            displaycolumns=("Main", "Off", "Optimal", "Motta", "Cost")
        )
        self.weapon_tree.heading(
            "Cost", text="Cost", anchor="center",
            command=lambda: self._sort_weapon_cost(False),
        )
        self._pack_scrollable_tree(self.weapon_tree, pady=(2, 6))
        self._restore_simulation_tab("weapons")

    def _build_weapon_filter_menu(self, parent, title, ordered, allowed):
        return self._build_named_filter_menu(
            parent, title, self.weapon_item_vars, ordered, allowed
        )

    def _build_named_filter_menu(self, parent, title, variables, ordered, allowed):
        button = ttk.Menubutton(parent, text=f"{title} ▾")
        button.pack(side="left", padx=3)
        menu = tk.Menu(button, tearoff=False)
        available = [value for value in ordered if value in allowed]
        if available:
            for value in available:
                menu.add_checkbutton(label=value, variable=variables[value])
            menu.add_separator()
            menu.add_command(
                label="Select All",
                command=lambda values=tuple(available): self._set_named_filters(variables, values, True),
            )
            menu.add_command(
                label="Clear All",
                command=lambda values=tuple(available): self._set_named_filters(variables, values, False),
            )
        else:
            menu.add_command(label="Unavailable for This Warrior", state="disabled")
            button.config(state="disabled")
        button.config(menu=menu)
        return button


    @staticmethod
    def _create_compare_panel(parent):
        """Compact shared filter/options panel for analysis tabs."""
        panel = ttk.LabelFrame(
            parent,
            text="FILTERS",
            style="AnalysisPanel.TLabelframe",
            padding=(9, 4),
        )
        panel.pack(
            fill="x",
            padx=20,
            pady=(0, 5),
        )
        return panel


    @staticmethod
    def _create_simulate_button(parent, command):
        button = ttk.Button(
            parent,
            text="Simulate",
            command=command,
            style="Accent.TButton",
        )
        button._default_action = command
        button._default_text = "Simulate"
        button.pack(side="right")
        return button

    def setup_tab_combos(self, tab):

        self.combo_progress_var = tk.DoubleVar()
        self._create_analysis_header(
            tab,
            "Improvements",
            (
                "Compare attribute increases and new skills, individually or in "
                "combinations, according to the selected warband and warrior."
            ),
        )

        controls = self._create_analysis_controls(tab)
        ttk.Label(controls, text="Simulations:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        ttk.Entry(controls, textvariable=self.simulations_combos, width=12).pack(side="left", padx=(0, 10))
        ttk.Label(controls, text="Number of Improvements:", style="Card.TLabel").pack(side="left", padx=(0, 5))
        count_selector = ttk.Combobox(
            controls, textvariable=self.improvement_count, values=(1, 2, 3, 4, 5),
            state="readonly", width=3, justify="center",
        )
        count_selector.pack(side="left", padx=(0, 10))
        count_selector.bind("<<ComboboxSelected>>", self._improvement_count_changed)
        self.btn_combo_run = self._create_simulate_button(
            controls, self.start_combo_thread,
        )
        (
            self.combo_progress_bar,
            self.combo_status_label,
        ) = self._attach_analysis_progress(
            controls,
            self.combo_progress_var,
        )


        filter_view_row = ttk.Frame(tab)
        filter_view_row.pack(
            fill="x",
            padx=20,
            pady=(0, 5),
        )

        self.improvement_filter_bar = ttk.LabelFrame(
            filter_view_row,
            text="FILTERS",
            style="AnalysisPanel.TLabelframe",
            padding=(9, 4),
        )
        self.improvement_filter_bar.pack(
            side="left",
            fill="x",
            expand=True,
        )
        self._refresh_improvement_filters()

        view_controls = ttk.Frame(filter_view_row)
        view_controls.pack(
            side="right",
            padx=(12, 0),
        )

        ttk.Label(
            view_controls,
            text="View:",
            style="Muted.TLabel",
        ).pack(
            side="left",
            padx=(0, 5),
        )

        ttk.Radiobutton(
            view_controls,
            text="By Equipment",
            variable=self.combo_view,
            value="equipment",
            command=lambda: self._change_result_view("combos"),
        ).pack(
            side="left",
            padx=3,
        )

        ttk.Radiobutton(
            view_controls,
            text="Optimal",
            variable=self.combo_view,
            value="optimal",
            command=lambda: self._change_result_view("combos"),
        ).pack(
            side="left",
            padx=3,
        )

        # Keep combination search in the same compact row as the view controls.
        ttk.Label(
            view_controls,
            text="Search combination:",
            style="Muted.TLabel",
        ).pack(
            side="left",
            padx=(12, 5),
        )

        if not getattr(self, "_combo_search_trace_added", False):
            self.combo_search.trace_add(
                "write",
                lambda *_args: self._render_combo_table(),
            )
            self._combo_search_trace_added = True

        ttk.Entry(
            view_controls,
            textvariable=self.combo_search,
            width=22,
        ).pack(side="left")

        ttk.Button(
            view_controls,
            text="Clear",
            command=self._clear_combo_filters,
        ).pack(
            side="left",
            padx=(6, 0),
        )

        self.combo_cards = self._create_mode_cards(tab, "combos")

        combo_table = ttk.Frame(tab)
        self.combo_tree = ttk.Treeview(
            combo_table,
            columns=("Improvement1", "Improvement2", "Improvement3", "Improvement4", "Improvement5",
                     "Single", "Shield", "Dual", "TwoHand", "Optimal", "Equipment"),
            show="headings",
        )
        self._configure_sortable_tree(self.combo_tree, [
            ("Improvement1", "Improvement 1"),
            ("Improvement2", "Improvement 2"),
            ("Improvement3", "Improvement 3"),
            ("Improvement4", "Improvement 4"),
            ("Improvement5", "Improvement 5"),
            ("Single", "Free Hand"),
            ("Shield", "Shield"),
            ("Dual", "Two Weapons"),
            ("TwoHand", "Two Hands"),
            ("Optimal", "Best Result"),
            ("Equipment", "Equipment Used"),
        ])
        for index in range(1, 6):
            self.combo_tree.column(f"Improvement{index}", width=145)
        for mode, _title in COMBAT_MODES:
            self.combo_tree.column(mode, width=150, anchor="center")
        self.combo_tree.column("Optimal", width=180, anchor="center")
        self.combo_tree.column("Equipment", width=220, anchor="center")
        self._apply_result_view("combos")
        self._pack_scrollable_tree(self.combo_tree, pady=(2, 6))
        self._restore_simulation_tab("combos")

    def _available_improvement_skills(self):
        profile = find_profile(self.candidate_band_id.get(), self.candidate_profile_id.get())
        if profile:
            return {skill for skill in profile.skills if skill in SKILLS}
        band = next(
            (item for item in self._candidate_bands if item.band_id == self.candidate_band_id.get()),
            None,
        )
        if band:
            return {skill.name for skill in band.skills if skill.name in SKILLS}
        return set(SKILLS)

    def _refresh_improvement_filters(self):
        bar = getattr(self, "improvement_filter_bar", None)
        if bar is None:
            return
        try:
            if not bar.winfo_exists():
                self.improvement_filter_bar = None
                return
        except tk.TclError:
            self.improvement_filter_bar = None
            return
        for child in bar.winfo_children():
            child.destroy()
        self._build_named_filter_menu(
            bar, "Attribute Increases", self.improvement_attribute_vars,
            tuple(self.improvement_attribute_vars), set(self.improvement_attribute_vars),
        )

        available = self._available_improvement_skills()
        try:
            owned = set(self._candidate_for_simulation().get("skills", ()))
        except (AttributeError, ValueError):
            owned = set()
        for skill, variable in self.improvement_skill_vars.items():
            variable.set(skill in available and skill not in owned)

        button = ttk.Menubutton(bar, text="Skills ▾")
        button.pack(side="left", padx=3)
        menu = tk.Menu(button, tearoff=False)
        if available:
            for skill in SKILLS:
                if skill not in available:
                    continue
                if skill in owned:
                    menu.add_checkbutton(
                        label=f"✓ {skill} (already owned by the candidate)",
                        variable=self.improvement_skill_vars[skill], state="disabled",
                    )
                else:
                    menu.add_checkbutton(label=skill, variable=self.improvement_skill_vars[skill])
            selectable = tuple(skill for skill in SKILLS if skill in available and skill not in owned)
            menu.add_separator()
            menu.add_command(
                label="Select All",
                command=lambda: self._set_named_filters(self.improvement_skill_vars, selectable, True),
            )
            menu.add_command(
                label="Clear All",
                command=lambda: self._set_named_filters(self.improvement_skill_vars, selectable, False),
            )
        else:
            menu.add_command(label="No Skills Available", state="disabled")
        button.config(menu=menu)

    def _improvement_count_changed(self, _event=None):
        self._selection_count_changed("combos")

    def _selection_count_changed(self, target):
        tree = getattr(
            self, "combo_tree" if target == "combos" else "equipment_tree", None
        )
        if tree is None:
            return
        setattr(
            self,
            "_combo_table_data" if target == "combos" else "_equipment_table_data",
            None,
        )
        for row in tree.get_children():
            tree.delete(row)
        self._apply_result_view(target)

    def get_user_mode_key(
        self,
        candidate,
    ):

        main_weapon = candidate.get(
            "main_weapon"
        )

        off_hand = candidate.get(
            "off_hand"
        )

        if main_weapon in TWO_HANDED_WEAPONS:
            return "TwoHand"

        if off_hand in ("Shield", "Buckler"):
            return "Shield"

        if off_hand not in ("None", "Shield", "Buckler") or main_weapon in PAIRED_WEAPONS:
            return "Dual"

        return "Single"

    def build_setup(
        self,
        base_candidate,
        mode,
    ):

        candidate = base_candidate.copy()

        main_weapon = (
            base_candidate["main_weapon"]
        )

        one_handed_weapon = (
            main_weapon
            if main_weapon not in TWO_HANDED_WEAPONS
            else "Sword"
        )

        if mode == "Single":

            candidate["main_weapon"] = (
                one_handed_weapon
            )

            candidate["off_hand"] = (
                "None"
            )

        elif mode == "Shield":

            candidate["main_weapon"] = (
                one_handed_weapon
            )

            candidate["off_hand"] = (
                "Shield"
            )

        elif mode == "Dual":

            candidate["main_weapon"] = (
                one_handed_weapon
            )

            off_hand = base_candidate[
                "off_hand"
            ]

            if off_hand in (
                "None",
                "Shield",
                "Buckler",
            ):
                off_hand = "Dagger"

            candidate["off_hand"] = (
                off_hand
            )

        elif mode == "TwoHand":

            candidate["main_weapon"] = (
                "Double-handed weapon"
            )

            candidate["off_hand"] = (
                "None"
            )

        return candidate

    def _apply_upgrade(self, candidate, upgrade):
        """Return an improved copy without modifying the base profile."""
        result = candidate.copy()
        result["skills"] = list(candidate.get("skills", []))

        if not upgrade:
            return result

        upgrade_type, value = upgrade

        if upgrade_type == "attr":
            result[value] += 1
        elif upgrade_type == "skill":
            if value not in result["skills"]:
                result["skills"].append(value)
        elif upgrade_type == "item":
            result[value] = True

        return result

    def _build_upgrade_list(self, base_candidate):
        """List improvements that still apply to this profile."""
        upgrades = []

        for attr in ["I", "WS", "S", "T", "A", "W"]:
            attribute_vars = getattr(self, "improvement_attribute_vars", None)
            if attribute_vars is not None and not attribute_vars[attr].get():
                continue
            upgrades.append(
                (
                    f"+1 {attr}",
                    ("attr", attr),
                )
            )

        available_skills = (
            self._available_improvement_skills()
            if hasattr(self, "_available_improvement_skills") else set(SKILLS)
        )
        skill_vars = getattr(self, "improvement_skill_vars", None)
        for skill in SKILLS:
            if (skill in available_skills
                    and (skill_vars is None or skill_vars[skill].get())
                    and skill not in base_candidate.get("skills", [])):
                upgrades.append(
                    (
                        skill,
                        ("skill", skill),
                    )
                )

        return upgrades

    @staticmethod
    def _equipment_options():
        options = []
        supported = set(equipment_options_for_profile())
        for armor in BODY_ARMORS:
            if armor in supported:
                options.append((armor, "armor", armor))
        if "Sea Dragon cloak" in supported:
            options.append(("Sea Dragon cloak", "cloak", True))
        if "Helmet" in supported:
            options.append(("Helmet", "helmet", True))
        if "Lucky charm" in supported:
            options.append(("Lucky charm", "amulet", True))
        options.extend(
            (name, "preparation", name)
            for name in PREPARATIONS if name in supported
        )
        options.extend(
            (name, "poison", name)
            for name in POISONS if name in supported
        )
        return options

    def _selected_equipment_options(self):
        selected = self.equipment_item_vars
        return [
            option for option in self._equipment_options()
            if selected[option[0]].get()
            and option[0] in getattr(
                self, "_equipment_filter_allowed", self.equipment_item_vars
            )
        ]

    @staticmethod
    def _equipment_combination_is_legal(items):
        exclusive_slots = {"armor"}
        kinds = [item[1] for item in items]
        if any(kinds.count(kind) > 1 for kind in exclusive_slots):
            return False
        if kinds.count("poison") > 2:
            return False
        non_poisons = [item for item in items if item[1] != "poison"]
        return len(non_poisons) == len(set(non_poisons))

    @staticmethod
    def _equipment_loadouts(options, maximum_items):
        loadouts = []
        for items in combinations_with_replacement(options, maximum_items):
            if CombatLabApp._equipment_combination_is_legal(items):
                loadouts.append((tuple(item[0] for item in items), items))
        return loadouts

    @staticmethod
    def _set_named_filters(variables, values, selected):
        for value in values:
            variables[value].set(selected)

    def _selected_weapons(self):
        return [
            weapon for weapon, variable in self.weapon_item_vars.items()
            if variable.get()
            and weapon in getattr(self, "_weapon_filter_allowed", self.weapon_item_vars)
        ]

    def _selected_weapon_materials(self):
        return [
            material for material, variable in self.weapon_material_vars.items()
            if variable.get()
            and material in getattr(self, "_weapon_material_allowed", self.weapon_material_vars)
        ]

    def _selected_weapon_defenses(self):
        return [
            defense for defense, variable in self.weapon_defense_vars.items()
            if variable.get()
            and defense in getattr(self, "_weapon_defense_allowed", self.weapon_defense_vars)
        ]

    @staticmethod
    def _weapon_loadouts(weapons, defenses=("Shield",)):
        loadouts = [("Single", "None", "None")]
        one_handed = [
            weapon for weapon in weapons
            if weapon not in TWO_HANDED_WEAPONS and weapon not in PAIRED_WEAPONS
        ]
        offhand = [weapon for weapon in one_handed if weapon in OFFHAND_CODES]
        main_hand = [
            weapon for weapon in one_handed
            if weapon not in MAIN_HAND_FORBIDDEN_WEAPONS
        ]
        for weapon in main_hand:
            loadouts.append(("Single", weapon, "None"))
            for defense in defenses:
                if weapon in {"Morning star", "Natural attacks"}:
                    continue
                if weapon in {"Choppa", "Squig prodder"} and defense != "Shield":
                    continue
                if weapon == "Broadsword" and defense != "Shield":
                    continue
                loadouts.append(("Shield", weapon, defense))
        for main in main_hand:
            if main in {"Morning star", "Broadsword"}:
                continue
            if main in {"Choppa", "Squig prodder"}:
                if "Spiked gauntlet" in offhand:
                    loadouts.append(("Dual", main, "Spiked gauntlet"))
                continue
            if main == "Spear":
                continue
            for off in offhand:
                loadouts.append(("Dual", main, off))
        for weapon in weapons:
            if weapon in TWO_HANDED_WEAPONS or weapon in PAIRED_WEAPONS:
                loadouts.append(("TwoHand", weapon, "None"))
        return loadouts

    @staticmethod
    def _materialized_weapon_loadouts(weapons, materials, defenses):
        """Expand legal configurations with each weapon material."""
        loadouts = []
        for mode, main, off in CombatLabApp._weapon_loadouts(weapons, defenses):
            main_materials = materials if main in WEAPONS_ALL else ("Normal",)
            off_materials = materials if off in WEAPONS_ALL else ("Normal",)
            for main_material in main_materials:
                for off_material in off_materials:
                    loadouts.append((
                        mode, main, off, main_material, off_material,
                    ))
        return loadouts

    @staticmethod
    def _weapon_with_material(weapon, material):
        if weapon in ("None", "Shield", "Buckler"):
            return weapon
        if material == "Normal":
            return weapon
        return f"{weapon} ({material})"

    @staticmethod
    def _weapon_loadout_label(main, off, main_material, off_material):
        if main == "None" and off == "None":
            return "Unarmed || None"
        return (
            f"{CombatLabApp._weapon_with_material(main, main_material)} || "
            f"{CombatLabApp._weapon_with_material(off, off_material)}"
        )

    @staticmethod
    def _canonical_weapon_candidate(candidate, mode):
        """Canonicalise reversed hands that produce the same dual attack.

        With a single base Attack, two simple weapons generate one attack with each
        one. Sorting them avoids simulating the same profile twice with different dice
        results. Swap the complete package for each hand to
        preserve materials and poisons.
        """
        result = candidate.copy()
        if mode != "Dual" or effective_fighter_key(result)[5] != 1:
            return result
        main = result.get("main_weapon", "None")
        off = result.get("off_hand", "None")
        interchangeable = {"Sword", "Dagger", "Mace", "Axe"}
        if main not in interchangeable or off not in interchangeable:
            return result
        if "Axe Master" in result.get("skills", ()):
            return result

        main_bundle = (
            main,
            result.get("main_weapon_material", "Normal"),
            result.get("main_poison", "No Poison"),
        )
        off_bundle = (
            off,
            result.get("offhand_material", "Normal"),
            result.get("offhand_poison", "No Poison"),
        )
        if tuple(str(value).casefold() for value in off_bundle) >= tuple(
            str(value).casefold() for value in main_bundle
        ):
            return result
        result["main_weapon"], result["main_weapon_material"], result["main_poison"] = (
            off_bundle
        )
        result["off_hand"], result["offhand_material"], result["offhand_poison"] = (
            main_bundle
        )
        return result

    @staticmethod
    def _weapon_cost(weapon, material, costs):
        if weapon == "None":
            return 0.0
        base_cost = costs.get(weapon)
        if base_cost is None:
            return None
        if material == "Dark Elf blade":
            return base_cost + 20.0
        multiplier = {
            "Normal": 1.0,
            "Gromril": 4.0,
            "Ithilmar": 3.0,
            "Obsidian": 5.0,
            "Dark steel": 3.0,
        }.get(material, 1.0)
        return base_cost * multiplier

    @staticmethod
    def _weapon_cost_display(main_cost, off_cost, show_off=None):
        if main_cost is None or off_cost is None:
            return "Cost unavailable", None
        total = main_cost + off_cost
        number = lambda value: f"{value:g}"
        include_offhand = bool(off_cost) if show_off is None else show_off
        if include_offhand:
            return f"{number(main_cost)} + {number(off_cost)} = {number(total)} gc", total
        return f"{number(main_cost)} gc", total

    @staticmethod
    def _motta_index(improvement, total_cost):
        if total_cost is None:
            return None
        regularized_cost = math.hypot(total_cost, MOTTA_COST_FLOOR)
        return improvement / regularized_cost * MOTTA_CONSTANT

    @staticmethod
    def _equipment_item_key(weapon, material="Normal"):
        if weapon == "None":
            return None
        normalized_material = (
            "Normal" if material == "Normal" else material
        )
        if weapon in ("Shield", "Buckler"):
            normalized_material = "Normal"
        return weapon, normalized_material

    @staticmethod
    def _weapon_acquisition_costs(
        main, off, main_material, off_material, candidate, costs,
    ):
        """Return the remaining cost after deducting already owned equipment once."""
        owned = []
        for weapon, material in (
            (candidate.get("main_weapon", "None"), candidate.get("main_weapon_material", "Normal")),
            (candidate.get("off_hand", "None"), candidate.get("offhand_material", "Normal")),
        ):
            key = CombatLabApp._equipment_item_key(weapon, material)
            if key is not None:
                owned.append(key)

        # Every warrior owns one free normal dagger. If that dagger is
        # already equipped, it is the same item rather than a second copy.
        free_dagger = ("Dagger", "Normal")
        if free_dagger not in owned:
            owned.append(free_dagger)

        result = []
        for weapon, material in ((main, main_material), (off, off_material)):
            key = CombatLabApp._equipment_item_key(weapon, material)
            if key is None:
                result.append(0.0)
            elif key in owned:
                owned.remove(key)
                result.append(0.0)
            else:
                result.append(CombatLabApp._weapon_cost(weapon, material, costs))
        return tuple(result)

    @staticmethod
    def _apply_equipment_items(candidate, items):
        """Add selected items to the candidate's current equipment."""
        result = candidate.copy()
        preparations = list(result.get("preparations") or ())
        preparations_changed = False
        poison_slots = [
            result.get("main_poison", "No Poison"),
            result.get("offhand_poison", "No Poison"),
        ]
        claimed_poison_slots = [False, False]
        for _label, kind, value in items:
            if kind == "armor":
                result["armor"] = value
            elif kind == "helmet":
                result["has_helmet"] = True
            elif kind == "amulet":
                result["has_luck_amulet"] = True
            elif kind == "cloak":
                result["has_sea_dragon_cloak"] = True
            elif kind == "preparation":
                if value not in preparations:
                    preparations.append(value)
                    preparations_changed = True
            elif kind == "poison":
                matching = next((
                    index for index, poison in enumerate(poison_slots)
                    if poison == value and not claimed_poison_slots[index]
                ), None)
                if matching is None:
                    matching = next((
                        index for index, poison in enumerate(poison_slots)
                        if poison == "No Poison"
                        and not claimed_poison_slots[index]
                    ), None)
                if matching is None:
                    matching = next((
                        index for index, claimed in enumerate(claimed_poison_slots)
                        if not claimed
                    ), 1)
                poison_slots[matching] = value
                claimed_poison_slots[matching] = True
        result["main_poison"], result["offhand_poison"] = poison_slots
        if preparations_changed or "preparations" in result:
            result["preparations"] = preparations
        return result

    @staticmethod
    def _owned_optional_equipment(candidate):
        owned = []
        armor = candidate.get("armor", "No Armour")
        if armor != "No Armour":
            owned.append(armor)
        if candidate.get("has_helmet", False):
            owned.append("Helmet")
        if candidate.get("has_luck_amulet", False):
            owned.append("Lucky charm")
        if candidate.get("has_sea_dragon_cloak", False):
            owned.append("Sea Dragon cloak")
        owned.extend(candidate.get("preparations", ()))
        for poison in (
            candidate.get("main_poison", "No Poison"),
            candidate.get("offhand_poison", "No Poison"),
        ):
            if poison != "No Poison":
                owned.append(poison)
        return owned

    @staticmethod
    def _equipment_acquisition_costs(labels, candidate, costs):
        owned = CombatLabApp._owned_optional_equipment(candidate)
        result = []
        for label in labels:
            if label in owned:
                owned.remove(label)
                result.append(0.0)
            else:
                result.append(costs.get(label))
        return tuple(result)

    @staticmethod
    def _equipment_cost_display(component_costs):
        if any(value is None for value in component_costs):
            return "Cost unavailable", None
        total = sum(component_costs)
        parts = " + ".join(f"{value:g}" for value in component_costs)
        if len(component_costs) > 1:
            return f"{parts} = {total:g} gc", total
        return f"{total:g} gc", total

    @staticmethod
    def _read_simulation_count(variable):
        total = int(variable.get().replace("_", "").strip())
        if total < 1:
            raise ValueError("The number of simulations must be greater than zero.")
        return total

    def _active_enemy_names(self):
        difficulties = [
            name for name, variable in self.enemy_difficulties.items()
            if variable.get()
        ]
        return profiles_for_difficulties(difficulties)

    def _disable_simulation_buttons(self):
        for name in (
            "btn_equipment_run", "btn_weapons_run", "btn_combo_run",
        ):
            button = getattr(self, name, None)
            if button is not None:
                try:
                    button.config(state="disabled")
                except tk.TclError:
                    # The tab that owns the button may be unloaded.
                    pass

    def _activate_cancel_button(self, button):
        self._simulation_cancel_event = threading.Event()
        button.config(
            state="normal",
            text="Cancel",
            command=self.cancel_simulation,
            style="Danger.TButton",
        )

    def cancel_simulation(self):
        if not getattr(self, "_simulation_running", False):
            return
        cancel_event = getattr(self, "_simulation_cancel_event", None)
        if cancel_event is not None:
            cancel_event.set()
        button = getattr(self, "_active_button", None)
        if button is not None:
            try:
                button.config(text="Cancelling...", state="disabled")
            except tk.TclError:
                pass
        label = getattr(self, "_active_status_label", None)
        if label is not None:
            label.config(text="Cancelling...")

    @staticmethod
    def _run_tasks(
        tasks, progress_queue, total_simulations, completion_weights=None,
        cancel_event=None,
    ):
        """Distribute complete comparisons without splitting any combat."""
        completion_weights = completion_weights or {}

        def worker_task(task, worker_cancel_event):
            return (
                *task[:10], None, task[11], *task[12:], worker_cancel_event,
            )

        def cancelled():
            return cancel_event is not None and cancel_event.is_set()

        def report(result):
            if progress_queue is not None:
                weight = completion_weights.get((result[0], result[1]), 1)
                progress_queue.put(("chunk", 0, total_simulations * weight))

        if len(tasks) < 4 or len(tasks) * total_simulations < 100_000:
            results = []
            for task in tasks:
                if cancelled():
                    raise SimulationCancelled("Simulation cancelled by the user.")
                result = run_single_task_optimized(worker_task(task, cancel_event))
                results.append(result)
                report(result)
            return results

        available_cpus = os.cpu_count() or 4
        # Keep one CPU available so the interface remains responsive.
        worker_limit = max(1, available_cpus - 1)
        worker_count = min(8, worker_limit, len(tasks))
        results = []

        with multiprocessing.Manager() as manager:
            worker_cancel_event = manager.Event()
            process_tasks = [
                worker_task(task, worker_cancel_event) for task in tasks
            ]
            groups = [
                process_tasks[index:index + TASK_GROUP_SIZE]
                for index in range(0, len(process_tasks), TASK_GROUP_SIZE)
            ]
            with ProcessPoolExecutor(
                max_workers=worker_count,
                initializer=_configure_simulation_worker,
            ) as executor:
                pending = {
                    executor.submit(run_task_batch, group)
                    for group in groups if group
                }
                while pending:
                    if cancelled():
                        worker_cancel_event.set()
                        for future in pending:
                            future.cancel()
                        raise SimulationCancelled(
                            "Simulation cancelled by the user."
                        )
                    done, pending = wait(
                        pending, timeout=0.1, return_when=FIRST_COMPLETED
                    )
                    for future in done:
                        batch = future.result()
                        results.extend(batch)
                        for result in batch:
                            report(result)
        return results

    @staticmethod
    def _deduplicate_tasks(tasks):
        """Group combinations that produce the same effective fighter."""
        unique_tasks = []
        aliases = {}
        canonical_by_key = {}

        for task in tasks:
            mode, label, candidate = task[0], task[1], task[2]
            key = (mode, effective_fighter_key(candidate))
            canonical = canonical_by_key.get(key)
            if canonical is None:
                canonical = (mode, label)
                canonical_by_key[key] = canonical
                unique_tasks.append(task)
                aliases[canonical] = []
            aliases[canonical].append((label, task[9]))

        return unique_tasks, aliases

    def _enable_simulation_buttons(self):
        for name in (
            "btn_equipment_run", "btn_weapons_run", "btn_combo_run",
        ):
            button = getattr(self, name, None)
            if button is not None:
                try:
                    default_text = getattr(button, "_default_text", "Simulate")
                    default_action = getattr(button, "_default_action", None)
                    button.config(state="normal", text=default_text)
                    if default_action is not None:
                        button.config(
                            command=default_action,
                            style="Accent.TButton",
                        )
                except tk.TclError:
                    # As above, there is no button to reactivate when the tab does not exist.
                    pass

    def _simulation_cancelled(self):
        self._enable_simulation_buttons()
        self._cancel_progress_poll()
        self._switch_progress_to_determinate()
        label = getattr(self, "_active_status_label", None)
        if label is not None:
            elapsed = time.perf_counter() - self._simulation_started_at
            label.config(
                text=f"Simulation cancelled · {self._format_elapsed(elapsed)}"
            )

    def start_equipment_thread(self):
        try:
            base_candidate = self._candidate_for_simulation()
            total_simulations = self._read_simulation_count(
                self.simulations_equipment
            )
            selected_options = self._selected_equipment_options()
            if not selected_options:
                raise ValueError("Select at least one item to compare.")
            maximum_items = int(self.equipment_max_items.get())
            equipment_costs = self._costs_with_house_rules(
                equipment_costs_for_profile(
                    self.candidate_band_id.get(), self.candidate_profile_id.get()
                )
            )
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        if self.enemy_mode.get() == "sample" and not self._active_enemy_names():
            messagebox.showerror(
                "Sample Error", "Select at least one enemy."
            )
            return

        self._disable_simulation_buttons()
        self._active_progress_var = self.equipment_progress_var
        self._active_status_label = self.equipment_status_label
        self._active_progress_bar = self.equipment_progress_bar
        self._active_button = self.btn_equipment_run
        self._activate_cancel_button(self.btn_equipment_run)
        self._progress_target = 0.0
        self._simulation_started_at = time.perf_counter()
        self._progress_indeterminate = True
        self._cancel_progress_poll()

        self.equipment_progress_var.set(0)
        self.equipment_progress_bar.config(mode="indeterminate")
        self.equipment_progress_bar.start(PROGRESS_ANIMATION_MS)
        self.equipment_status_label.config(text="Preparing item combinations...")
        for row in self.equipment_tree.get_children():
            self.equipment_tree.delete(row)

        self._simulation_running = True
        threading.Thread(
            target=self.run_equipment_simulations_threadpool,
            args=(
                base_candidate, self.enemy_mode.get(), total_simulations,
                selected_options, maximum_items, equipment_costs,
            ),
            daemon=True,
        ).start()

    def run_equipment_simulations_threadpool(
        self, base_candidate, enemy_mode, total_simulations, options,
        maximum_items, equipment_costs,
    ):
        try:
            custom_enemy = None
            active_pool_names = []
            if enemy_mode == "custom":
                custom_enemy = self._custom_enemies_for_simulation()
            else:
                active_pool_names = self._active_enemy_names()

            loadouts = self._equipment_loadouts(options, maximum_items)
            mode = "Single"
            loadout_costs = {}
            master_seed = random.randint(1, 2_147_483_647)

            if enemy_mode == "sample":
                self.after(
                    0, self._set_status,
                    "Generating shared enemy sample...",
                )
                shared_enemy_indices = _generate_shared_enemy_selection(
                    active_pool_names, total_simulations, master_seed,
                    ENEMY_VARIANTS_PER_PROFILE,
                )
            else:
                shared_enemy_indices = self._manual_enemy_indices(
                    custom_enemy, total_simulations, master_seed
                )

            progress_queue = queue.Queue()
            self._progress_queue = progress_queue
            self._progress_chunks_done = 0
            tasks = [(
                mode, "BASELINE", base_candidate.copy(), enemy_mode, custom_enemy,
                active_pool_names, shared_enemy_indices, total_simulations,
                master_seed, True, progress_queue, 0, self.enemy_level.get(),
            )]
            for labels, items in loadouts:
                candidate_test = self._apply_equipment_items(base_candidate, items)
                padded_labels = (*labels, *("",) * (5 - len(labels)))
                label = " || ".join(padded_labels)
                component_costs = self._equipment_acquisition_costs(
                    labels, base_candidate, equipment_costs
                )
                loadout_costs[label] = component_costs
                tasks.append((
                    mode, label, candidate_test, enemy_mode, custom_enemy,
                    active_pool_names, shared_enemy_indices, total_simulations,
                    master_seed, False, progress_queue,
                    len(tasks), self.enemy_level.get(),
                ))

            total_tasks = len(tasks)
            unique_tasks, aliases = self._deduplicate_tasks(tasks)
            completion_weights = {
                canonical: len(group) for canonical, group in aliases.items()
            }
            self._progress_chunk_total = total_tasks * total_simulations
            self.after(
                0, self._set_status,
                f"Running {len(unique_tasks)} effective combats for "
                f"{total_tasks} results...",
            )
            self._progress_poll_id = self.after(
                PROGRESS_POLL_MS, self._poll_simulation_progress
            )

            raw_results = {mode: []}
            for mode, label, win_rate, _is_base in self._run_tasks(
                unique_tasks, progress_queue, total_simulations, completion_weights,
                self._simulation_cancel_event,
            ):
                for alias_label, alias_is_base in aliases[(mode, label)]:
                    raw_results[mode].append(
                        (alias_label, win_rate, alias_is_base)
                    )

            equipment_results = {}
            for mode, data in raw_results.items():
                base_rate = next(rate for _label, rate, is_base in data if is_base)
                equipment_results[mode] = (
                    base_rate,
                    [
                        (label, rate, rate - base_rate)
                        for label, rate, is_base in data if not is_base
                    ],
                )

            self._simulation_running = False
            self.after(
                0, self.update_ui_with_equipment_results, equipment_results,
                self.get_user_mode_key(base_candidate),
                {
                    mode: self._equipment_description(base_candidate)
                },
                loadout_costs,
            )
        except SimulationCancelled:
            self._simulation_running = False
            self.after(0, self._simulation_cancelled)

        except Exception as exc:
            self._simulation_running = False
            self.after(0, self._simulation_error, exc)

    def update_ui_with_equipment_results(
        self, equipment_results, user_mode_key, equipment, loadout_costs
    ):
        self._equipment_card_data = None
        self._equipment_table_data = (
            equipment_results, equipment, loadout_costs,
        )
        self._equipment_generated_at = datetime.now().isoformat(timespec="seconds")
        self._render_equipment_table()

        self._finish_progress(
            self.equipment_progress_var,
            self.equipment_status_label,
            "Equipment analysis complete",
        )
        self._enable_simulation_buttons()

    def _render_equipment_table(self):
        table_data = getattr(self, "_equipment_table_data", None)
        if not table_data:
            return
        equipment_results, equipment, *extra = table_data
        loadout_costs = extra[0] if extra else {}
        rows = {}
        for mode, (_base_rate, results) in equipment_results.items():
            for label, rate, impact in results:
                rows.setdefault(label, {})[mode] = (rate, impact)

        for item in self.equipment_tree.get_children():
            self.equipment_tree.delete(item)
        ordered = sorted(
            rows.items(),
            key=lambda item: max(
                (
                    value[0] for mode, value in item[1].items()
                    if mode in self.equipment_visible_modes
                ),
                default=-1.0,
            ),
            reverse=True,
        )
        summaries = {}
        for label, values in ordered:
            best_mode = max(values, key=lambda value: values[value][0])
            best_rate, best_impact = values[best_mode]
            _display, total_cost = self._equipment_cost_display(
                loadout_costs.get(label, (None,))
            )
            summaries[label] = (
                best_mode, best_rate, best_impact,
                self._motta_index(best_impact, total_cost),
            )
        highest_rate = max((value[1] for value in summaries.values()), default=None)
        highest_motta = max(
            (value[3] for value in summaries.values() if value[3] is not None),
            default=None,
        )
        for label, values in ordered:
            item_cells = tuple(part or "—" for part in label.split(" || "))
            best_mode, best_rate, best_impact, motta = summaries[label]
            cost_display, total_cost = self._equipment_cost_display(
                loadout_costs.get(label, (None,))
            )
            victory_marker = (
                "★ " if highest_rate is not None
                and abs(best_rate - highest_rate) < 0.00001 else ""
            )
            motta_marker = (
                "★ " if motta is not None and highest_motta is not None
                and abs(motta - highest_motta) < 0.00001 else ""
            )
            self.equipment_tree.insert(
                "", "end",
                values=(
                    *item_cells,
                    f"{victory_marker}{best_rate:.2f}% ({best_impact:+.2f}%)",
                    f"{motta_marker}{motta:.2f}" if motta is not None else "—",
                    cost_display,
                    f"{total_cost:g}" if total_cost is not None else "",
                    equipment[best_mode],
                ),
            )
        self._autosize_tree_columns(self.equipment_tree)

    def start_weapon_thread(self):
        try:
            base_candidate = self._candidate_for_simulation()
            total_simulations = self._read_simulation_count(self.simulations_weapons)
            weapons = self._selected_weapons()
            if not weapons:
                raise ValueError("Select at least one weapon to compare.")
            materials = self._selected_weapon_materials()
            if not materials:
                raise ValueError("Select at least one material to compare.")
            defenses = self._selected_weapon_defenses()
            weapon_costs = self._costs_with_house_rules(
                equipment_costs_for_profile(
                    self.candidate_band_id.get(), self.candidate_profile_id.get()
                )
            )
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        if self.enemy_mode.get() == "sample" and not self._active_enemy_names():
            messagebox.showerror(
                "Sample Error", "Select at least one enemy."
            )
            return

        self._disable_simulation_buttons()
        self._active_progress_var = self.weapon_progress_var
        self._active_status_label = self.weapon_status_label
        self._active_progress_bar = self.weapon_progress_bar
        self._active_button = self.btn_weapons_run
        self._activate_cancel_button(self.btn_weapons_run)
        self._simulation_started_at = time.perf_counter()
        self._progress_indeterminate = True
        self._cancel_progress_poll()
        self.weapon_progress_var.set(0)
        self.weapon_progress_bar.config(mode="indeterminate")
        self.weapon_progress_bar.start(PROGRESS_ANIMATION_MS)
        self.weapon_status_label.config(text="Preparing weapon configurations...")
        for row in self.weapon_tree.get_children():
            self.weapon_tree.delete(row)

        self._simulation_running = True
        threading.Thread(
            target=self.run_weapon_simulations_threadpool,
            args=(
                base_candidate, self.enemy_mode.get(), total_simulations,
                weapons, materials, defenses, weapon_costs,
            ),
            daemon=True,
        ).start()

    def run_weapon_simulations_threadpool(
        self, base_candidate, enemy_mode, total_simulations, weapons,
        materials, defenses, weapon_costs,
    ):
        try:
            custom_enemy = None
            active_pool_names = []
            if enemy_mode == "custom":
                custom_enemy = self._custom_enemies_for_simulation()
            else:
                active_pool_names = self._active_enemy_names()

            modes = [mode for mode, _title in COMBAT_MODES]
            loadouts = self._materialized_weapon_loadouts(
                weapons, materials, defenses
            )
            loadout_costs = {}
            master_seed = random.randint(1, 2_147_483_647)
            if enemy_mode == "sample":
                self.after(
                    0, self._set_status,
                    "Generating shared enemy sample...",
                )
                shared_enemy_indices = _generate_shared_enemy_selection(
                    active_pool_names, total_simulations, master_seed,
                    ENEMY_VARIANTS_PER_PROFILE,
                )
            else:
                shared_enemy_indices = self._manual_enemy_indices(
                    custom_enemy, total_simulations, master_seed
                )

            progress_queue = queue.Queue()
            self._progress_queue = progress_queue
            self._progress_chunks_done = 0
            tasks = []
            # In this comparison all configurations must be measured against
            # the candidate's exact current equipment. Previously each mode created
            # its own reference (for example, Dual already added a dagger), hiding the
            # real improvement of rows matching that artificial reference.
            for mode in modes:
                current = self._canonical_weapon_candidate(base_candidate, mode)
                tasks.append((
                    mode, "BASELINE", current, enemy_mode, custom_enemy,
                    active_pool_names, shared_enemy_indices, total_simulations,
                    master_seed + modes.index(mode) * 100_000,
                    True, progress_queue,
                    len(tasks), self.enemy_level.get(),
                ))

            for mode, main, off, main_material, off_material in loadouts:
                candidate = base_candidate.copy()
                candidate["main_weapon"] = main
                candidate["off_hand"] = off
                candidate["main_weapon_material"] = main_material
                candidate["offhand_material"] = off_material
                candidate = self._canonical_weapon_candidate(candidate, mode)
                label = self._weapon_loadout_label(
                    main, off, main_material, off_material
                )
                main_cost, off_cost = self._weapon_acquisition_costs(
                    main, off, main_material, off_material,
                    base_candidate, weapon_costs,
                )
                loadout_costs[label] = (main_cost, off_cost)
                tasks.append((
                    mode, label, candidate, enemy_mode, custom_enemy,
                    active_pool_names, shared_enemy_indices, total_simulations,
                    master_seed + modes.index(mode) * 100_000,
                    False, progress_queue, len(tasks), self.enemy_level.get(),
                ))

            total_tasks = len(tasks)
            unique_tasks, aliases = self._deduplicate_tasks(tasks)
            completion_weights = {
                canonical: len(group) for canonical, group in aliases.items()
            }
            self._progress_chunk_total = total_tasks * total_simulations
            self.after(
                0, self._set_status,
                f"Running {len(unique_tasks)} effective combats for "
                f"{total_tasks} configurations...",
            )
            self._progress_poll_id = self.after(
                PROGRESS_POLL_MS, self._poll_simulation_progress
            )

            raw_results = {mode: [] for mode in modes}
            for mode, label, win_rate, _is_base in self._run_tasks(
                unique_tasks, progress_queue, total_simulations, completion_weights,
                self._simulation_cancel_event,
            ):
                for alias_label, alias_is_base in aliases[(mode, label)]:
                    raw_results[mode].append((alias_label, win_rate, alias_is_base))

            weapon_results = {}
            for mode, data in raw_results.items():
                base_rate = next(rate for _label, rate, is_base in data if is_base)
                weapon_results[mode] = (
                    base_rate,
                    [
                        (label, rate, rate - base_rate)
                        for label, rate, is_base in data if not is_base
                    ],
                )

            self._simulation_running = False
            self.after(
                0, self.update_ui_with_weapon_results, weapon_results,
                self.get_user_mode_key(base_candidate),
                {
                    mode: self._equipment_description(base_candidate)
                    for mode, _title in COMBAT_MODES
                },
                loadout_costs,
            )
        except SimulationCancelled:
            self._simulation_running = False
            self.after(0, self._simulation_cancelled)

        except Exception as exc:
            self._simulation_running = False
            self.after(0, self._simulation_error, exc)

    def update_ui_with_weapon_results(
        self, weapon_results, user_mode_key, equipment, loadout_costs,
    ):
        self._weapon_card_data = None
        self._weapon_table_data = (weapon_results, equipment, loadout_costs)
        self._weapons_generated_at = datetime.now().isoformat(timespec="seconds")
        self._render_weapon_table()
        self._finish_progress(
            self.weapon_progress_var,
            self.weapon_status_label,
            "Weapon analysis complete",
        )
        self._enable_simulation_buttons()

    def _render_weapon_table(self):
        table_data = getattr(self, "_weapon_table_data", None)
        if not table_data:
            return
        weapon_results, equipment, *extra = table_data
        loadout_costs = extra[0] if extra else {}
        rows = {}
        for mode, (_base_rate, results) in weapon_results.items():
            for label, rate, impact in results:
                rows.setdefault(label, {})[mode] = (rate, impact)

        for item in self.weapon_tree.get_children():
            self.weapon_tree.delete(item)
        ordered = sorted(
            rows.items(),
            key=lambda item: max(
                (
                    value[0] for mode, value in item[1].items()
                    if mode in self.weapon_visible_modes
                ),
                default=-1.0,
            ),
            reverse=True,
        )
        summaries = {}
        for label, values in ordered:
            best_mode = self._best_visible_mode(values, self.weapon_visible_modes)
            if best_mode is None:
                continue
            best_rate, best_impact = values[best_mode]
            main_cost, off_cost = loadout_costs.get(label, (None, None))
            _cost_display, total_cost = self._weapon_cost_display(main_cost, off_cost)
            summaries[label] = (
                best_mode, best_rate, best_impact,
                self._motta_index(best_impact, total_cost),
            )
        highest_rate = max(
            (summary[1] for summary in summaries.values()), default=None
        )
        highest_motta = max(
            (summary[3] for summary in summaries.values() if summary[3] is not None),
            default=None,
        )
        for label, values in ordered:
            main, off = label.split(" || ", 1)
            summary = summaries.get(label)
            if summary is None:
                continue
            best_mode, best_rate, best_impact, motta = summary
            cells = []
            for mode, _title in COMBAT_MODES:
                if mode not in values:
                    cells.append("")
                    continue
                rate, impact = values[mode]
                cells.append(f"{rate:.2f}% ({impact:+.2f}%)")
            main_cost, off_cost = loadout_costs.get(label, (None, None))
            cost_display, total_cost = self._weapon_cost_display(
                main_cost, off_cost, off != "None"
            )
            victory_marker = (
                "★ " if highest_rate is not None
                and abs(best_rate - highest_rate) < 0.00001 else ""
            )
            motta_marker = (
                "★ " if motta is not None and highest_motta is not None
                and abs(motta - highest_motta) < 0.00001 else ""
            )
            self.weapon_tree.insert(
                "", "end",
                values=(
                    main,
                    off if off != "None" else "—",
                    *cells,
                    f"{victory_marker}{best_rate:.2f}% ({best_impact:+.2f}%)",
                    f"{motta_marker}{motta:.2f}" if motta is not None else "—",
                    cost_display,
                    f"{total_cost:g}" if total_cost is not None else "",
                    equipment[best_mode],
                ),
            )
        self._autosize_tree_columns(self.weapon_tree)

    def start_combo_thread(self):
        try:
            base_candidate = self._candidate_for_simulation()
            total_simulations = self._read_simulation_count(self.simulations_combos)
            improvement_count = int(self.improvement_count.get())
        except ValueError:
            messagebox.showerror(
                "Error",
                "Enter valid numeric values.",
            )
            return

        if self.enemy_mode.get() == "sample":
            active_enemies = self._active_enemy_names()
            if not active_enemies:
                messagebox.showerror(
                    "Sample Error",
                    "Select at least one enemy.",
                )
                return

        self._disable_simulation_buttons()
        self._active_progress_var = self.combo_progress_var
        self._active_status_label = self.combo_status_label
        self._active_progress_bar = self.combo_progress_bar
        self._active_button = self.btn_combo_run
        self._activate_cancel_button(self.btn_combo_run)
        self._progress_target = 0.0
        self._simulation_started_at = time.perf_counter()
        self._progress_indeterminate = True
        self._cancel_progress_poll()

        self.combo_progress_var.set(0)
        self.combo_progress_bar.config(mode="indeterminate")
        self.combo_progress_bar.start(PROGRESS_ANIMATION_MS)
        self.combo_status_label.config(text="Preparing combinations...")

        for row in self.combo_tree.get_children():
            self.combo_tree.delete(row)
        self._reset_mode_cards(self.combo_cards, self.combo_visible_modes)

        enemy_mode = self.enemy_mode.get()
        self._simulation_running = True

        threading.Thread(
            target=self.run_combo_simulations_threadpool,
            args=(base_candidate, enemy_mode, total_simulations, improvement_count),
            daemon=True,
        ).start()

    def run_combo_simulations_threadpool(
        self, base_candidate, enemy_mode, total_simulations, improvement_count
    ):
        try:
            custom_enemy = None
            active_pool_names = []

            if enemy_mode == "custom":
                custom_enemy = self._custom_enemies_for_simulation()
            else:
                active_pool_names = self._active_enemy_names()

            upgrade_options = self._build_upgrade_list(base_candidate)
            if len(upgrade_options) < improvement_count:
                raise ValueError(
                    f"Not enough improvements are selected to build combinations of {improvement_count}."
                )

            modes = ["Single", "Shield", "Dual", "TwoHand"]
            master_seed = random.randint(1, 2_147_483_647)

            if enemy_mode == "sample":
                self.after(0, self._set_status, "Generating shared enemy sample...")
                shared_enemy_indices = _generate_shared_enemy_selection(
                    active_pool_names,
                    total_simulations,
                    master_seed,
                    ENEMY_VARIANTS_PER_PROFILE,
                )
            else:
                shared_enemy_indices = self._manual_enemy_indices(
                    custom_enemy, total_simulations, master_seed
                )

            progress_queue = queue.Queue()
            self._progress_queue = progress_queue
            self._progress_chunks_done = 0
            self._progress_chunk_total = 0

            tasks = []

            # One reference per tactic; without it the delta would be meaningless.
            for mode_index, mode in enumerate(modes):
                base_test = self.build_setup(base_candidate, mode)
                tasks.append((
                    mode,
                    "BASELINE",
                    base_test,
                    enemy_mode,
                    custom_enemy,
                    active_pool_names,
                    shared_enemy_indices,
                    total_simulations,
                    master_seed + mode_index * 1000,
                    True,
                    progress_queue,
                    len(tasks),
                    self.enemy_level.get(),
                ))

            for mode_index, mode in enumerate(modes):
                for combo_index, selected in enumerate(
                    combinations(upgrade_options, improvement_count)
                ):
                    candidate_test = base_candidate
                    for _label, upgrade in selected:
                        candidate_test = self._apply_upgrade(candidate_test, upgrade)
                    candidate_test = self.build_setup(candidate_test, mode)

                    tasks.append((
                        mode,
                        " + ".join(label for label, _upgrade in selected),
                        candidate_test,
                        enemy_mode,
                        custom_enemy,
                        active_pool_names,
                        shared_enemy_indices,
                        total_simulations,
                        master_seed + mode_index * 1_000_000 + combo_index,
                        False,
                        progress_queue,
                        len(tasks),
                        self.enemy_level.get(),
                    ))

            total_tasks = len(tasks)
            unique_tasks, aliases = self._deduplicate_tasks(tasks)
            completion_weights = {
                canonical: len(group)
                for canonical, group in aliases.items()
            }
            raw_results = {mode: [] for mode in modes}

            self.after(
                0,
                self._set_status,
                f"Running {len(unique_tasks)} effective combats for "
                f"{total_tasks} results...",
            )

            self._progress_chunk_total = total_tasks * total_simulations
            self._progress_poll_id = self.after(
                PROGRESS_POLL_MS, self._poll_simulation_progress
            )

            for mode, label, win_rate, _is_base in self._run_tasks(
                unique_tasks, progress_queue, total_simulations, completion_weights,
                self._simulation_cancel_event,
            ):
                for alias_label, alias_is_base in aliases[(mode, label)]:
                    raw_results[mode].append((alias_label, win_rate, alias_is_base))

            combo_results = {}
            for mode, data in raw_results.items():
                base_rate = next(
                    rate for label, rate, is_base in data if is_base
                )
                combos = [
                    (label, rate, rate - base_rate)
                    for label, rate, is_base in data
                    if not is_base
                ]
                combo_results[mode] = (base_rate, combos)

            self._simulation_running = False
            self.after(
                0,
                self.update_ui_with_combo_results,
                combo_results,
                self.get_user_mode_key(base_candidate),
                {
                    mode: self._equipment_description(self.build_setup(base_candidate, mode))
                    for mode, _title in COMBAT_MODES
                },
            )

        except SimulationCancelled:
            self._simulation_running = False
            self.after(0, self._simulation_cancelled)

        except Exception as exc:
            self._simulation_running = False
            self.after(0, self._simulation_error, exc)

    def update_ui_with_combo_results(self, combo_results, user_mode_key, equipment):
        base_rates = {mode: data[0] for mode, data in combo_results.items()}
        self._update_mode_cards(self.combo_cards, base_rates, user_mode_key, equipment)
        self._combo_card_data = (base_rates, user_mode_key, equipment)

        self._combo_table_data = (combo_results, equipment)
        self._combos_generated_at = datetime.now().isoformat(timespec="seconds")
        self._render_combo_table()

        active_progress_var = self._active_progress_var
        active_status_label = self._active_status_label

        self._finish_progress(active_progress_var, active_status_label, "Improvement analysis complete")
        self._enable_simulation_buttons()

    def _render_combo_table(self):
        if not getattr(self, "_combo_table_data", None):
            return
        combo_results, equipment = self._combo_table_data
        visible_modes = self.combo_visible_modes
        search = self.combo_search.get()
        for item in self.combo_tree.get_children():
            self.combo_tree.delete(item)

        rows = {}
        for mode, (_base_rate, combos) in combo_results.items():
            for label, rate, impact in combos:
                rows.setdefault(label, {})[mode] = (rate, impact)

        ordered_rows = sorted(
            rows.items(),
            key=lambda item: max(
                item[1][mode][0] for mode in visible_modes
            ),
            reverse=True,
        )
        for label, values in ordered_rows:
            parts = self._combo_parts(label)
            if not self._combo_matches(parts, search):
                continue
            best_mode = self._best_visible_mode(values, visible_modes)
            cells = []
            for mode, _title in COMBAT_MODES:
                rate, impact = values[mode]
                marker = "★ " if mode == best_mode else ""
                cells.append(f"{marker}{rate:.2f}% ({impact:+.2f}%)")
            optimal = f"★ {values[best_mode][0]:.2f}% ({values[best_mode][1]:+.2f}%)"
            improvement_cells = (*parts, *("—" for _ in range(5 - len(parts))))
            self.combo_tree.insert(
                "", "end",
                values=(*improvement_cells, *cells, optimal, equipment[best_mode]),
            )
        self._autosize_tree_columns(self.combo_tree)

    def _set_status(
        self,
        text,
    ):
        label = getattr(self, "_active_status_label", None)
        if label is not None:
            label.config(text=text)

    def _switch_progress_to_determinate(self):
        if not getattr(self, "_progress_indeterminate", False):
            return
        bar = getattr(self, "_active_progress_bar", None)
        if bar is None:
            return
        bar.stop()
        bar.config(mode="determinate")
        self._active_progress_var.set(0.0)
        self._progress_indeterminate = False

    def _cancel_progress_poll(self):
        poll_id = getattr(self, "_progress_poll_id", None)
        if poll_id is not None:
            try:
                self.after_cancel(poll_id)
            except tk.TclError:
                pass
        self._progress_poll_id = None

    def _finish_progress(self, progress_var, status_label, message):
        self._cancel_progress_poll()
        self._switch_progress_to_determinate()
        progress_var.set(100.0)
        elapsed = time.perf_counter() - self._simulation_started_at
        status_label.config(
            text=f"✓ {message} · {self._format_elapsed(elapsed)}"
        )

    @staticmethod
    def _format_elapsed(seconds):
        if seconds < 60:
            return f"{seconds:.1f} s"
        minutes, remaining = divmod(int(round(seconds)), 60)
        return f"{minutes} min {remaining:02d} s"

    def _poll_simulation_progress(self):
        """Drain the progress queue without blocking Tkinter."""
        self._progress_poll_id = None
        q = getattr(self, "_progress_queue", None)
        if q is None:
            return

        received = 0
        try:
            while True:
                kind, _task_id, amount = q.get_nowait()
                if kind == "chunk":
                    received += amount
        except queue.Empty:
            pass

        if received:
            self._switch_progress_to_determinate()
            self._progress_chunks_done += received

        total = max(1, int(self._progress_chunk_total))
        target = min(
            100.0,
            self._progress_chunks_done * 100.0 / total,
        )

        progress_var = getattr(self, "_active_progress_var", None)
        status_label = getattr(self, "_active_status_label", None)
        if progress_var is None or status_label is None:
            return

        if not getattr(self, "_progress_indeterminate", False):
            current = target
            progress_var.set(current)
        else:
            current = 0.0

        completed = min(
            int(self._progress_chunks_done),
            total,
        )
        if getattr(self, "_progress_indeterminate", False):
            status_label.config(text="Starting workers...")
        else:
            status_label.config(
                text=(
                    f"{current:.1f}% · "
                    f"{completed:,}/{total:,} combats"
                )
            )

        if getattr(self, "_simulation_running", False):
            self._progress_poll_id = self.after(
                PROGRESS_POLL_MS, self._poll_simulation_progress
            )

    def _simulation_error(
        self,
        exc,
    ):

        self._enable_simulation_buttons()
        self._cancel_progress_poll()
        self._switch_progress_to_determinate()

        active_status_label = getattr(self, "_active_status_label", None)
        if active_status_label is not None:
            active_status_label.config(text="Error.")

        messagebox.showerror(
            "Simulator Error",
            str(exc),
        )
