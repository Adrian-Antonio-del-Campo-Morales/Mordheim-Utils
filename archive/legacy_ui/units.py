"""Locale-aware tabletop distance conversion helpers.

The canonical rules value is inches.  Trollheim source profiles retain their
published centimetre values and are converted only when displayed or compared.
"""

from __future__ import annotations

import re


CENTIMETRES_PER_INCH = 2.5
_DICE_MOVEMENT = re.compile(r"^(?P<count>\d+)D(?P<sides>\d+)(?P<modifier>[+-]\d+)?$")
_SPANISH_PROFILE_MOVEMENT = {5: 2, 8: 3, 10: 4, 12: 5, 15: 6, 22: 9}
_ENGLISH_PROFILE_MOVEMENT = {inches: centimetres for centimetres, inches in _SPANISH_PROFILE_MOVEMENT.items()}


def movement_to_inches(value: int | str, source_locale: str) -> int | str:
    """Return a profile movement value in canonical game inches.

    Spanish Mordheim publications round half centimetres up (3\" is printed as
    8 cm), so ordinary distances use the same convention.  Dice expressions
    are converted per die, e.g. ``5D6 cm`` becomes ``2D6\"``.
    """
    if source_locale != "es":
        return value
    if isinstance(value, int):
        if value in _SPANISH_PROFILE_MOVEMENT:
            return _SPANISH_PROFILE_MOVEMENT[value]
        return int(value / CENTIMETRES_PER_INCH + 0.5)
    match = _DICE_MOVEMENT.fullmatch(str(value))
    if not match:
        return value
    count = int(int(match["count"]) / CENTIMETRES_PER_INCH + 0.5)
    modifier = match["modifier"] or ""
    if modifier:
        modifier = f"{int(int(modifier) / CENTIMETRES_PER_INCH + (0.5 if int(modifier) >= 0 else -0.5)):+d}"
        if modifier == "+0":
            modifier = ""
    return f"{count}D{match['sides']}{modifier}"


def format_movement(value_in_inches: int | str, locale: str) -> str:
    """Format a canonical movement value using the selected UI locale."""
    if locale == "en":
        return f'{value_in_inches}"'
    if isinstance(value_in_inches, int):
        if value_in_inches in _ENGLISH_PROFILE_MOVEMENT:
            return f"{_ENGLISH_PROFILE_MOVEMENT[value_in_inches]} cm"
        return f"{int(value_in_inches * CENTIMETRES_PER_INCH + 0.5)} cm"
    match = _DICE_MOVEMENT.fullmatch(str(value_in_inches))
    if not match:
        return str(value_in_inches)
    count = int(int(match["count"]) * CENTIMETRES_PER_INCH + 0.5)
    modifier = match["modifier"] or ""
    if modifier:
        modifier = f"{int(int(modifier) * CENTIMETRES_PER_INCH + (0.5 if int(modifier) >= 0 else -0.5)):+d}"
        if modifier == "+0":
            modifier = ""
    return f"{count}D{match['sides']}{modifier} cm"
