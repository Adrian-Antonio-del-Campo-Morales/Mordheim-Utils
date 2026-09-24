"""KB locale policy and localized display names.

The knowledge base is **canonical English** by convention (see the
"Locale policy" section of ``docs/reference/knowledge-base.md``): the English
``name`` / ``effect`` fields are the single canonical source. The
``name_i18n`` / ``effect_i18n`` blocks store only *translations* for
non-canonical locales (``es``) — they never carry an ``en`` mirror of the
canonical English.

This module is the single sanctioned reader of those blocks:

- :func:`set_locale` / :func:`current_locale` select the *display* locale of
  the applications (``en`` by default; ``MORDHEIM_LOCALE`` env override).
- :func:`display_name` / :func:`display_effect` resolve the best available
  text for a record without ever modifying the KB: a reviewed translation in
  the active locale wins, then the canonical English text, then any other
  translated entry (so records keep working while translations land
  incrementally).

The KB itself never changes meaning: ids, bindings and engine behaviour stay
canonical regardless of the display locale.
"""
from __future__ import annotations

import os

#: The canonical locale the KB is authored in.
CANONICAL_LOCALE = "en"

#: Locales with an authorised translation effort.
SUPPORTED_LOCALES = frozenset({"en", "es"})

#: Non-canonical locales, in resolution order, used only as a last resort so
#: a record without canonical text still shows something readable.
_TRANSLATED_LOCALES = ("es",)

_active_locale = CANONICAL_LOCALE


def _normalize(locale: str | None) -> str:
    value = str(locale or CANONICAL_LOCALE).strip().lower()
    return value.split("-", 1)[0] or CANONICAL_LOCALE


def set_locale(locale: str | None = None) -> str:
    """Select the display locale (``"en"`` / ``"es"``); returns the effective one.

    ``None`` defers to the ``MORDHEIM_LOCALE`` environment variable and then to
    the canonical locale. Unsupported locales are ignored, keeping the current
    selection, so a typo can never silently blank every name.
    """
    global _active_locale
    if locale is None:
        locale = os.environ.get("MORDHEIM_LOCALE")
    candidate = _normalize(locale)
    if candidate in SUPPORTED_LOCALES:
        _active_locale = candidate
    return _active_locale


def current_locale() -> str:
    """The active display locale (canonical English unless changed)."""
    return _active_locale


def display_name(record: object, fallback: str | None = None) -> str:
    """Best display name of one KB record (dict row).

    Resolution order: the reviewed ``name_i18n`` entry of the active locale
    (when it is not the canonical one), the canonical ``name`` field, and
    finally any other translated locale present. Non-dict records and
    missing values fall back to ``fallback`` (the caller's id, typically) so
    ids remain visible instead of crashing.
    """
    i18n = record.get("name_i18n") if isinstance(record, dict) else None
    if isinstance(i18n, dict) and _active_locale != CANONICAL_LOCALE:
        value = str(i18n.get(_active_locale) or "").strip()
        if value:
            return value
    if isinstance(record, dict):
        name = str(record.get("name") or "").strip()
        if name:
            return name
        if isinstance(i18n, dict):
            for locale in _TRANSLATED_LOCALES:
                value = str(i18n.get(locale) or "").strip()
                if value:
                    return value
    return str(fallback or "").strip()


def resolved_name(record: object, fallback: str | None = None) -> str:
    """Best display name of one KB record, never returning an empty string.

    Like :func:`display_name` but the last resort is the record's ``id`` and
    then ``fallback``, so callers always get something visible.
    """
    name = display_name(record)
    if name:
        return name
    record_id = str(record.get("id") or "") if isinstance(record, dict) else ""
    return record_id or str(fallback or "").strip()


def display_effect(record: object) -> str:
    """Best display effect text of one KB record (dict row), same policy.

    The reviewed ``effect_i18n`` entry of the active locale wins when it is
    not the canonical one; otherwise the canonical ``effect`` prose, then
    any other translated entry.
    """
    i18n = record.get("effect_i18n") if isinstance(record, dict) else None
    if isinstance(i18n, dict) and _active_locale != CANONICAL_LOCALE:
        value = str(i18n.get(_active_locale) or "").strip()
        if value:
            return value
    if isinstance(record, dict):
        effect = str(record.get("effect") or "").strip()
        if effect:
            return effect
        if isinstance(i18n, dict):
            for locale in _TRANSLATED_LOCALES:
                value = str(i18n.get(locale) or "").strip()
                if value:
                    return value
    return ""
