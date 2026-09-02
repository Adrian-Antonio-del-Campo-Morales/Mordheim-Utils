"""ui.constants: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations



COMBAT_MODES = (
    ("Single", "Weapon + Free Hand"),
    ("Shield", "Weapon and Shield"),
    ("Dual", "Two Weapons"),
    ("TwoHand", "Double-Handed Weapon"),
)


DEFAULT_COMBO_SIMULATIONS = 100_000


PROGRESS_POLL_MS = 100


PROGRESS_ANIMATION_MS = 60


SELECTABLE_CATEGORIES = ("core", "1a", "1b", "1c", "trollheim")


CATALOG_CATEGORY_LABELS = {"all": "All", "core": "Core", "1a": "1A", "1b": "1B", "1c": "1C", "trollheim": "Trollheim"}
