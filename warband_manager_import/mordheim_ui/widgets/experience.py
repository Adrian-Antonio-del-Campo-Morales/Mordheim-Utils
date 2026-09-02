from __future__ import annotations

import tkinter as tk

from mordheim_ui.theme import COLORS


class ExperienceTrack(tk.Canvas):
    """Reusable Mordheim experience grid, extended with a previous-XP overlay."""

    HERO_COLUMNS = 45
    HERO_ROWS = 2
    HERO_SHADED = {
        (0, 2), (0, 4), (0, 6), (0, 8), (0, 11), (0, 14), (0, 17),
        (0, 20), (0, 24), (0, 28), (0, 32), (0, 36), (0, 41),
        (1, 1), (1, 6), (1, 12), (1, 18), (1, 24), (1, 31), (1, 38), (1, 45),
    }
    HENCHMAN_COLUMNS = 14
    HENCHMAN_ROWS = 1
    HENCHMAN_SHADED = {(0, 2), (0, 5), (0, 9), (0, 14)}

    def __init__(self, master: tk.Misc, experience: int, *, previous_experience: int | None = None, track_type: str = "hero", **kwargs) -> None:
        self.experience = max(0, int(experience))
        self.previous_experience = self.experience if previous_experience is None else max(0, int(previous_experience))
        self.track_type = track_type
        if track_type == "henchman":
            self.columns, self.rows, self.shaded_cells = self.HENCHMAN_COLUMNS, self.HENCHMAN_ROWS, self.HENCHMAN_SHADED
            requested_height, requested_width = 26, 240
        else:
            self.columns, self.rows, self.shaded_cells = self.HERO_COLUMNS, self.HERO_ROWS, self.HERO_SHADED
            requested_height, requested_width = 32, 440
        super().__init__(master, width=requested_width, height=requested_height, background=COLORS["panel"], highlightthickness=0, bd=0, **kwargs)
        self.bind("<Configure>", lambda _e: self._redraw())
        self.after_idle(self._redraw)

    @property
    def capacity(self) -> int:
        return self.columns * self.rows

    def _redraw(self) -> None:
        self.delete("all")
        width, height = max(1, self.winfo_width()), max(1, self.winfo_height())
        pad = 2
        usable_width, usable_height = max(1, width - pad * 2), max(1, height - pad * 2)
        cell_size = min(usable_width / self.columns, usable_height / self.rows)
        grid_width, grid_height = cell_size * self.columns, cell_size * self.rows
        offset_x = pad + (usable_width - grid_width) / 2
        offset_y = pad + (usable_height - grid_height) / 2
        current = min(self.experience, self.capacity)
        previous = min(self.previous_experience, self.capacity)

        for row in range(self.rows):
            for col0 in range(self.columns):
                column = col0 + 1
                index = row * self.columns + col0
                x0, y0 = offset_x + col0 * cell_size, offset_y + row * cell_size
                x1, y1 = x0 + cell_size, y0 + cell_size
                threshold = (row, column) in self.shaded_cells
                if index < previous:
                    fill = COLORS["accent_dark"] if threshold else COLORS["accent"]
                elif index < current:
                    fill = COLORS["success"]
                elif threshold:
                    fill = COLORS["border"]
                else:
                    fill = COLORS["panel_soft"]
                self.create_rectangle(x0, y0, x1, y1, fill=fill, outline=COLORS["black"], width=1)
