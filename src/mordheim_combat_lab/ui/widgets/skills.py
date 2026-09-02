"""ui.widgets.skills: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_ui.lab_theme import COLORS
from mordheim_combat_lab.ui.widgets.feedback import tooltip_manager
import tkinter as tk


class SkillChecklist(tk.Canvas):
    """Grouped skill selector rendered by one canvas instead of many widgets."""

    CATEGORY_ORDER = (
        "Combat",
        "Shooting",
        "Academic",
        "Strength",
        "Speed",
        "Special",
        "Other Rules",
    )
    CARD_GAP = 6
    CARD_PADDING_X = 8
    CARD_PADDING_Y = 6
    CHECK_SIZE = 13
    HEADER_HEIGHT = 26
    MIN_HEIGHT = 48
    MAX_ROWS_PER_CATEGORY = 10
    OUTER_PAD = 2
    ROW_HEIGHT = 22
    MIN_CARD_WIDTH = 190
    COUNTER_WIDTH = 58

    def __init__(self, parent, on_change=None):
        super().__init__(parent, background=COLORS["bg"], borderwidth=0, highlightthickness=0, height=self.MIN_HEIGHT)
        self.on_change = on_change
        self._skills: dict[str, object] = {}
        self._visible_categories: tuple[str, ...] = ()
        self._selected: set[str] = set()
        self._enabled_ids: set[str] = set()
        self._category_offsets: dict[str, int] = {}
        self._redraw_after_id = None
        self._hovered_skill_id = None
        self._counter_skill_id: str | None = None
        self._counter_value = 0
        self._counter_minimum = 0
        self._counter_maximum = 0
        self._counter_command = None
        self.bind("<Configure>", self._schedule_redraw, add="+")
        self.bind("<Motion>", self._on_motion, add="+")
        self.bind("<Leave>", self._on_leave, add="+")
        self.bind("<Button-1>", self._on_click, add="+")
        self.bind("<MouseWheel>", self._on_mousewheel, add="+")
        self.bind("<Button-4>", lambda _event: self.yview_scroll(-1, "units"), add="+")
        self.bind("<Button-5>", lambda _event: self.yview_scroll(1, "units"), add="+")
        self._redraw()

    def set_skills(self, skills, *, categories=()) -> None:
        """Replace skills, retaining explicitly requested empty categories."""
        self._skills = {skill.id: skill for skill in skills}
        self._visible_categories = tuple(str(category).title() for category in categories)
        self._selected.clear()
        self._enabled_ids = set(self._skills)
        self._category_offsets.clear()
        self.configure(height=self._desired_height())
        self._schedule_redraw()

    def set_enabled_ids(self, skill_ids) -> None:
        """Enable a legal subset while keeping every skill visible."""
        self._enabled_ids = set(skill_ids).intersection(self._skills)
        self._selected.intersection_update(self._enabled_ids)
        self._schedule_redraw()

    def set_selected_ids(self, skill_ids) -> None:
        """Restore a selection without generating one notification per ID."""
        self._selected = set(skill_ids).intersection(self._skills)
        self._schedule_redraw()

    def selected_ids(self) -> tuple[str, ...]:
        """Return selected IDs in catalogue display order."""
        return tuple(skill_id for skill_id in self._skills if skill_id in self._selected)

    def configure_inline_counter(self, skill_id: str, *, value: int = 0,
                                 minimum: int = 0, maximum: int = 19,
                                 command=None) -> None:
        """Attach a compact ``− value +`` control to one selected skill."""
        self._counter_skill_id = skill_id
        self._counter_minimum = minimum
        self._counter_maximum = maximum
        self._counter_command = command
        self.set_inline_counter_value(value)

    def set_inline_counter_value(self, value: int) -> None:
        self._counter_value = min(self._counter_maximum, max(self._counter_minimum, int(value)))
        self._schedule_redraw()

    def _grouped_skills(self) -> list[tuple[str, list[object]]]:
        grouped: dict[str, list[object]] = {
            category: [] for category in self._visible_categories
        }
        for skill in self._skills.values():
            grouped.setdefault(str(skill.category).title(), []).append(skill)
        category_order = {category: index for index, category in enumerate(self.CATEGORY_ORDER)}
        return [
            (category, sorted(skills, key=lambda skill: str(skill.name).casefold()))
            for category, skills in sorted(
                grouped.items(),
                key=lambda group: (category_order.get(group[0], len(category_order)), group[0]),
            )
        ]

    def _desired_height(self) -> int:
        groups = self._grouped_skills()
        if not groups:
            return self.MIN_HEIGHT
        card_height = self._card_height(groups)
        columns = self._column_count(len(groups))
        category_rows = (len(groups) + columns - 1) // columns
        return max(self.MIN_HEIGHT, self.OUTER_PAD * 2 + category_rows * card_height + (category_rows - 1) * self.CARD_GAP)

    def _column_count(self, group_count: int) -> int:
        """Fit category cards into rows instead of clipping narrow cards."""
        return max(1, min(group_count, max(1, (self.winfo_width() - self.OUTER_PAD * 2 + self.CARD_GAP) // (self.MIN_CARD_WIDTH + self.CARD_GAP))))

    def _card_height(self, groups) -> int:
        """Keep the selector's layout stable; scrolling never grows a card."""
        return self.CARD_PADDING_Y * 2 + self.HEADER_HEIGHT + self.MAX_ROWS_PER_CATEGORY * self.ROW_HEIGHT

    def _schedule_redraw(self, _event=None) -> None:
        if self._redraw_after_id is None:
            self._redraw_after_id = self.after_idle(self._run_scheduled_redraw)

    def _run_scheduled_redraw(self) -> None:
        self._redraw_after_id = None
        if self.winfo_exists():
            self._redraw()

    def _toggle(self, skill_id: str, _event=None) -> str:
        if skill_id not in self._enabled_ids:
            return "break"
        if skill_id in self._selected:
            self._selected.remove(skill_id)
        else:
            self._selected.add(skill_id)
        self._redraw()
        if self.on_change:
            self.on_change()
        return "break"

    def _skill_id_at_pointer(self) -> str | None:
        """Resolve the skill under the pointer from its Canvas item tag."""
        items = self.find_withtag("current")
        if not items:
            return None
        for tag in self.gettags(items[0]):
            if tag.startswith("skill-"):
                return tag.removeprefix("skill-")
        return None

    def _on_click(self, _event=None) -> str | None:
        for item in self.find_withtag("current"):
            for tag in self.gettags(item):
                if tag == "counter-decrement":
                    self._change_counter(-1)
                    return "break"
                if tag == "counter-increment":
                    self._change_counter(1)
                    return "break"
                if tag.startswith("scroll-up-"):
                    self._scroll_category(tag.removeprefix("scroll-up-"), -1)
                    return "break"
                if tag.startswith("scroll-down-"):
                    self._scroll_category(tag.removeprefix("scroll-down-"), 1)
                    return "break"
        skill_id = self._skill_id_at_pointer()
        return self._toggle(skill_id) if skill_id else None

    def _change_counter(self, delta: int) -> None:
        if self._counter_skill_id not in self._selected:
            return
        value = min(self._counter_maximum, max(self._counter_minimum, self._counter_value + delta))
        if value == self._counter_value:
            return
        self._counter_value = value
        self._redraw()
        if self._counter_command:
            self._counter_command(value)

    def _on_motion(self, event) -> None:
        skill_id = self._skill_id_at_pointer()
        if skill_id == self._hovered_skill_id:
            return
        self._hovered_skill_id = skill_id
        if skill_id is None:
            self.configure(cursor="")
            tooltip_manager(self).hide(self)
            return
        self.configure(cursor="hand2" if skill_id in self._enabled_ids else "")
        tooltip_manager(self).schedule(
            self,
            self._tooltip_text(skill_id),
            event.x_root + 16,
            event.y_root + 18,
        )

    def _tooltip_text(self, skill_id: str) -> str:
        """Combine the rule summary with the KB's reason for a disabled skill."""
        skill = self._skills[skill_id]
        text = str(skill.summary or "")
        if skill_id in self._enabled_ids:
            return text
        reason = str(getattr(skill, "unavailable_reason", "") or "").strip()
        if reason:
            return f"{text}\n\n{reason}" if text else reason
        access_notice = "Not available to this warrior's skill access."
        return f"{text}\n\n{access_notice}" if text else access_notice

    def _on_leave(self, _event=None) -> None:
        self._hovered_skill_id = None
        self.configure(cursor="")
        tooltip_manager(self).hide(self)

    def _on_mousewheel(self, event) -> str:
        """Scroll only the category currently under the pointer."""
        category = self._category_at_pointer(event)
        if category:
            steps = max(1, abs(event.delta) // 120)
            self._scroll_category(category, -steps if event.delta > 0 else steps)
        return "break"

    def _category_at_pointer(self, event=None) -> str | None:
        items = (
            reversed(self.find_overlapping(event.x, event.y, event.x, event.y))
            if event is not None else self.find_withtag("current")
        )
        for item in items:
            for tag in self.gettags(item):
                if tag.startswith("category-"):
                    return tag.removeprefix("category-")
        return None

    def _scroll_category(self, category: str, amount: int) -> None:
        skills = dict(self._grouped_skills()).get(category, ())
        maximum = max(0, len(skills) - self.MAX_ROWS_PER_CATEGORY)
        offset = min(maximum, max(0, self._category_offsets.get(category, 0) + amount))
        if offset != self._category_offsets.get(category, 0):
            self._category_offsets[category] = offset
            self._redraw()

    def _draw_checkbox(self, x: float, y: float, checked: bool, enabled: bool, tags) -> None:
        fill = COLORS["accent"] if checked and enabled else COLORS["surface_alt"]
        outline = COLORS["accent"] if checked and enabled else COLORS["border_light"] if enabled else COLORS["border"]
        self.create_rectangle(x, y, x + self.CHECK_SIZE, y + self.CHECK_SIZE, fill=fill, outline=outline, tags=tags)
        if checked:
            self.create_text(x + self.CHECK_SIZE / 2, y + self.CHECK_SIZE / 2 - 0.5, text="✓", fill="#111111" if enabled else COLORS["text_disabled"], font=("Segoe UI Semibold", 9), tags=tags)

    def _redraw(self) -> None:
        self.delete("all")
        self._hovered_skill_id = None
        tooltip_manager(self).hide(self)
        groups = self._grouped_skills()
        width = max(1, self.winfo_width())
        height = max(self.MIN_HEIGHT, self._desired_height())
        if int(self.cget("height")) != height:
            self.configure(height=height)
        if not groups:
            self.create_text(6, height / 2, text="No selectable skills are available for this profile.", fill=COLORS["text_muted"], font=("Segoe UI", 9), anchor="w")
            return
        columns = self._column_count(len(groups))
        card_height = self._card_height(groups)
        usable_width = width - self.OUTER_PAD * 2 - self.CARD_GAP * (columns - 1)
        card_width = max(80.0, usable_width / columns)
        for index, (category, skills) in enumerate(groups):
            category_tag = f"category-{category}"
            offset = min(self._category_offsets.get(category, 0), max(0, len(skills) - self.MAX_ROWS_PER_CATEGORY))
            visible_skills = skills[offset:offset + self.MAX_ROWS_PER_CATEGORY]
            category_enabled = any(skill.id in self._enabled_ids for skill in skills)
            row, column = divmod(index, columns)
            x1 = self.OUTER_PAD + column * (card_width + self.CARD_GAP)
            x2 = min(width - self.OUTER_PAD, x1 + card_width)
            y1 = self.OUTER_PAD + row * (card_height + self.CARD_GAP)
            y2 = y1 + card_height
            self.create_rectangle(x1, y1, x2, y2, fill=COLORS["surface"], outline=COLORS["border"] if category_enabled else COLORS["border_light"], tags=(category_tag,))
            self.create_text(x1 + self.CARD_PADDING_X, y1 + self.CARD_PADDING_Y + 8, text=category, fill=COLORS["text"] if category_enabled else COLORS["text_disabled"], font=("Segoe UI Semibold", 10), anchor="w", tags=(category_tag,))
            if len(skills) > self.MAX_ROWS_PER_CATEGORY:
                arrow_fill = COLORS["text"] if category_enabled else COLORS["text_disabled"]
                range_label = f"{offset + 1}–{offset + len(visible_skills)} / {len(skills)}"
                self.create_text(x2 - self.CARD_PADDING_X - 31, y1 + self.CARD_PADDING_Y + 8, text=range_label, fill=arrow_fill, font=("Segoe UI", 7), anchor="e", tags=(category_tag,))
                self.create_text(x2 - self.CARD_PADDING_X - 13, y1 + self.CARD_PADDING_Y + 8, text="▴" if offset else "·", fill=arrow_fill, font=("Segoe UI", 9), anchor="e", tags=(category_tag, f"scroll-up-{category}"))
                self.create_text(x2 - self.CARD_PADDING_X, y1 + self.CARD_PADDING_Y + 8, text="▾" if offset < len(skills) - self.MAX_ROWS_PER_CATEGORY else "·", fill=arrow_fill, font=("Segoe UI", 9), anchor="e", tags=(category_tag, f"scroll-down-{category}"))
            row_top = y1 + self.CARD_PADDING_Y + self.HEADER_HEIGHT
            for row_index, skill in enumerate(visible_skills):
                row_y1 = row_top + row_index * self.ROW_HEIGHT
                skill_tag = f"skill-{skill.id}"
                tags = ("skill", skill_tag, category_tag)
                self.create_rectangle(x1 + 1, row_y1, x2 - 1, row_y1 + self.ROW_HEIGHT, fill=COLORS["surface"], outline="", tags=tags)
                check_x = x1 + self.CARD_PADDING_X
                check_y = row_y1 + (self.ROW_HEIGHT - self.CHECK_SIZE) / 2
                enabled = skill.id in self._enabled_ids
                self._draw_checkbox(check_x, check_y, skill.id in self._selected, enabled, tags)
                has_counter = skill.id == self._counter_skill_id and skill.id in self._selected
                text_x2 = x2 - self.CARD_PADDING_X - (self.COUNTER_WIDTH if has_counter else 0)
                self.create_text(check_x + self.CHECK_SIZE + 7, row_y1 + self.ROW_HEIGHT / 2, text=skill.name, fill=COLORS["text"] if enabled else COLORS["text_disabled"], font=("Segoe UI", 9), anchor="w", tags=tags)
                if has_counter:
                    counter_x = text_x2
                    counter_y = row_y1 + self.ROW_HEIGHT / 2
                    counter_tags = ("counter", category_tag, f"skill-{skill.id}")
                    button_fill = COLORS["surface_alt"] if enabled else COLORS["surface"]
                    button_text = COLORS["text"] if enabled else COLORS["text_disabled"]
                    self.create_rectangle(counter_x, row_y1 + 2, counter_x + 17, row_y1 + self.ROW_HEIGHT - 2, fill=button_fill, outline=COLORS["border"], tags=(*counter_tags, "counter-decrement"))
                    self.create_text(counter_x + 8.5, counter_y, text="−", fill=button_text, font=("Segoe UI Semibold", 10), tags=(*counter_tags, "counter-decrement"))
                    self.create_text(counter_x + 29, counter_y, text=str(self._counter_value), fill=COLORS["accent"] if enabled else COLORS["text_disabled"], font=("Segoe UI Semibold", 9), tags=counter_tags)
                    self.create_rectangle(counter_x + 40, row_y1 + 2, counter_x + 57, row_y1 + self.ROW_HEIGHT - 2, fill=button_fill, outline=COLORS["border"], tags=(*counter_tags, "counter-increment"))
                    self.create_text(counter_x + 48.5, counter_y, text="+", fill=button_text, font=("Segoe UI Semibold", 10), tags=(*counter_tags, "counter-increment"))
            if len(skills) > self.MAX_ROWS_PER_CATEGORY:
                track_x1, track_x2 = x2 - 10, x2 - 3
                track_y1 = row_top + 2
                track_y2 = row_top + self.MAX_ROWS_PER_CATEGORY * self.ROW_HEIGHT - 2
                track_height = track_y2 - track_y1
                thumb_height = max(18, track_height * self.MAX_ROWS_PER_CATEGORY / len(skills))
                thumb_y1 = track_y1 + (track_height - thumb_height) * offset / (len(skills) - self.MAX_ROWS_PER_CATEGORY)
                self.create_rectangle(track_x1, track_y1, track_x2, track_y2, fill=COLORS["border_light"], outline="", tags=(category_tag,))
                self.create_rectangle(track_x1, thumb_y1, track_x2, thumb_y1 + thumb_height, fill=COLORS["accent"], outline="", tags=(category_tag,))
