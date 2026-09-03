"""ui.widgets.progress: responsibility extracted without altering the rules."""
from __future__ import annotations

from threading import Event
from tkinter import DoubleVar
from tkinter import StringVar
from tkinter import ttk


class AnalysisProgress(ttk.Frame):
    """Present bounded analysis progress and own its cancellation event."""

    def __init__(self, parent):
        super().__init__(parent)
        self.value = DoubleVar(value=0)
        self.message = StringVar(value="")
        self._total = 0
        self.cancel_event: Event | None = None
        self.bar = ttk.Progressbar(self, maximum=100, variable=self.value, style="Horizontal.TProgressbar")
        self.bar.pack(side="left", fill="x", expand=True)
        ttk.Label(self, textvariable=self.message, style="Muted.TLabel", width=28).pack(side="left", padx=(8, 8))
        self.cancel_button = ttk.Button(self, text="Cancel", command=self.cancel, state="disabled")
        self.cancel_button.pack(side="left")

    def start(self, total: int) -> Event:
        """Reset the UI and return the event passed to every simulation request."""
        self._total = max(1, total)
        self.value.set(0)
        self.message.set(f"0 / {total}")
        self.cancel_event = Event()
        self.cancel_button.configure(state="normal")
        return self.cancel_event

    def advance(self, completed: int) -> None:
        self.value.set(min(100.0, completed * 100.0 / self._total))
        self.message.set(f"{min(completed, self._total)} / {self._total}")

    def cancel(self) -> None:
        if self.cancel_event is not None:
            self.cancel_event.set()
            self.message.set("Cancelling…")
            self.cancel_button.configure(state="disabled")

    def finish(self, message: str) -> None:
        self.cancel_button.configure(state="disabled")
        self.message.set(message)
