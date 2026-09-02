"""ui.localization: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations



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
}


def translate(locale: str, key: str, **values: object) -> str:
    """Return English UI copy; the locale argument is kept for API stability."""
    text = UI_TEXT["en"].get(key, key)
    return text.format(**values)
