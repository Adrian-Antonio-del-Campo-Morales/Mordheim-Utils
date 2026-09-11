"""Capture stable desktop campaign-manager views for web parity reviews."""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import time
from pathlib import Path

from PIL import ImageGrab

from mordheim_campaign.persistence import load_campaign
from mordheim_campaign.ui.dialogs.campaign_library import CampaignLibraryDialog
from mordheim_campaign.ui.dialogs.new_campaign import NewCampaignDialog
from mordheim_campaign.ui.views.rules_view import RulesView
from mordheim_desktop.app import CampaignManagerApp


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "gui-capture-sisters-of-morr.mordheim"
OUTPUT = ROOT / "artifacts" / "gui-captures" / "desktop"


def _window_handle(widget) -> int:
    widget.update_idletasks()
    return ctypes.windll.user32.GetAncestor(widget.winfo_id(), 2)


def _window_rect(hwnd: int) -> tuple[int, int, int, int]:
    rect = wintypes.RECT()
    # DWM bounds exclude the transparent resize shadow where other windows
    # would otherwise bleed into the captured PNG.
    result = ctypes.windll.dwmapi.DwmGetWindowAttribute(
        hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)
    )
    if result and not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise ctypes.WinError(result)
    return rect.left, rect.top, rect.right, rect.bottom


def capture(widget, name: str) -> None:
    hwnd = _window_handle(widget)
    ctypes.windll.user32.ShowWindow(hwnd, 9)
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    widget.lift()
    widget.attributes("-topmost", True)
    widget.update_idletasks()
    widget.update()
    time.sleep(0.2)
    widget.update()
    destination = OUTPUT / f"D-{name}.png"
    ImageGrab.grab(_window_rect(hwnd), all_screens=True).save(destination)
    widget.attributes("-topmost", False)
    print(destination.relative_to(ROOT))


def descendants(widget):
    for child in widget.winfo_children():
        yield child
        yield from descendants(child)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    app = CampaignManagerApp()
    app.controller.set_locale("es")
    app.update()

    capture(app, "01-borrador-inicial")

    new_campaign = NewCampaignDialog(app, app.controller)
    capture(new_campaign, "02-nueva-campana")
    new_campaign.destroy()

    app.controller.campaign_library_path = FIXTURE.parent
    library = CampaignLibraryDialog(app, app.controller)
    capture(library, "03-biblioteca")
    library.destroy()

    app.controller.replace_state(load_campaign(FIXTURE))
    app.controller.mark_saved()

    for section, number in (("overview", "04"), ("warriors", "05"), ("inventory", "06")):
        app.controller.select_state(7)
        app.controller.set_state_section(section)
        capture(app, f"{number}-estado-{section}")

    app.controller.select_state(3)
    app.controller.set_state_section("overview")
    capture(app, "07-estado-historico")

    for section, number in (("overview", "08"), ("participants", "09"), ("notes", "10")):
        app.controller.select_battle(7)
        app.controller.set_battle_section(section)
        capture(app, f"{number}-batalla-{section}")

    app.controller.select_post_battle(8)
    capture(app, "11-postbatalla-navegador")
    for step in range(5):
        app.controller.set_post_battle_step(step)
        capture(app, f"{12 + step:02d}-postbatalla-paso-{step + 1}")

    # The committed fixture intentionally stops at step 5. For visual capture,
    # expose the remaining panels only in memory; no rule outcome is applied
    # and the fixture is never saved.
    post = app.controller.state.campaign.post_battle(8)
    for step in range(5, 8):
        post.active_step = step
        post.completed_steps.update(range(step))
        post.review_open = False
        app.controller.notify()
        capture(app, f"{12 + step:02d}-postbatalla-paso-{step + 1}")
    post.completed_steps.update(range(8))
    post.review_open = True
    app.controller.notify()
    capture(app, "20-revision-final")

    app.controller.navigate("rules")
    app.update()
    rules_view = next(widget for widget in descendants(app) if isinstance(widget, RulesView))
    first_rule = rules_view._current_entries()[0]
    rules_view._select(first_rule.entry_id)
    capture(app, "21-reglas")
    app.controller.navigate("settings")
    capture(app, "22-ajustes")

    app.controller.set_locale("en")
    capture(app, "23-ajustes-ingles")
    app.controller.select_state(7)
    app.controller.set_state_section("overview")
    capture(app, "24-campana-ingles")

    app.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
