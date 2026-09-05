"""Shared UI string catalogue for both applications.

Single sanctioned translation layer of the interface strings: widgets call
:func:`tr` with a stable English key, and every UI string is a member of
``STRINGS``. The shared theme stays string-free; ``ui`` areas must not define
their own lookup tables. Keys are the current English literals, so an
untranslated key renders exactly as before — a missing translation degrades
to English instead of crashing.

Translate at display time: shared data (``POST_BATTLE_STEPS``,
``POST_BATTLE_GROUPS``, KB names) keeps its canonical English form and every
widget applies ``tr`` when rendering.

Locale selection: :func:`set_locale` (``None`` defers to the
``MORDHEIM_LOCALE`` environment variable). Application entry points call it
once before widgets are built, together with
``mordheim_knowledge.i18n.set_locale`` for the KB display names — this layer
stays independent of ``mordheim_knowledge`` on purpose.

``STRINGS`` is kept alphabetically sorted (``tests/ui/test_ui_i18n.py``
enforces it) so a translator can review it top to bottom.
"""
from __future__ import annotations

import os

CANONICAL_LOCALE = "en"
SUPPORTED_LOCALES = frozenset({"en", "es"})

_active_locale = CANONICAL_LOCALE

#: Interface strings by canonical English key. An ``es`` entry marks the
#: string as translated; add new strings here with their English key first.
STRINGS: dict[str, dict[str, str]] = {
    # Post-battle sequence navigator (mordheim_campaign.ui.components)
    "8 / 8 ACTIONS COMPLETE": {"es": "8 / 8 ACCIONES COMPLETADAS"},
    "COMPLETE": {"es": "COMPLETADO"},
    "CONTINUE TO {}  ›": {"es": "CONTINUAR A {}  ›"},
    "CURRENT": {"es": "ACTUAL"},
    "CURRENT PHASE  ·  {}": {"es": "FASE ACTUAL  ·  {}"},
    "DONE": {"es": "HECHO"},
    "EQUIPMENT": {"es": "EQUIPAMIENTO"},
    "EXPLORATION & INCOME": {"es": "EXPLORACIÓN E INGRESOS"},
    "Experience": {"es": "Experiencia"},
    "Exploration": {"es": "Exploración"},
    "FINAL ACTION": {"es": "ACCIÓN FINAL"},
    "FINAL REVIEW": {"es": "REVISIÓN FINAL"},
    "FINAL REVIEW  ·  ALL 8 ACTIONS COMPLETE": {"es": "REVISIÓN FINAL  ·  LAS 8 ACCIONES COMPLETADAS"},
    "FINAL REVIEW IS AN APP CONFIRMATION, NOT AN ADDITIONAL POST-BATTLE RULE STEP": {
        "es": "LA REVISIÓN FINAL ES UNA CONFIRMACIÓN DE LA APLICACIÓN, NO UN PASO ADICIONAL DE POST-BATALLA"
    },
    "IN PROGRESS": {"es": "EN CURSO"},
    "Injuries": {"es": "Heridas"},
    "LOCKED": {"es": "BLOQUEADO"},
    "NEXT": {"es": "SIGUIENTE"},
    "Next: Commit new warband state": {"es": "Siguiente: confirmar el nuevo estado de la banda"},
    "Next: Final Review": {"es": "Siguiente: Revisión Final"},
    "Next: {}": {"es": "Siguiente: {}"},
    "Rare Items & Dramatis": {"es": "Objetos raros y Dramatis"},
    "RECOVERY": {"es": "RECUPERACIÓN"},
    "Recruitment": {"es": "Reclutamiento"},
    "SEARCHES": {"es": "BÚSQUEDAS"},
    "SELL WYRDSTONE": {"es": "VENDER WYRDSTONE"},
    "Sell Wyrdstone": {"es": "Vender wyrdstone"},
    "SEQUENCE COMPLETE": {"es": "SECUENCIA COMPLETA"},
    "STEP {} OF {}": {"es": "PASO {} DE {}"},
    "Veterans": {"es": "Veteranos"},
    "WARBAND": {"es": "BANDA"},
    # Post-battle steps (application/state.py POST_BATTLE_STEPS)
    "{} ACTIONS REMAIN": {"es": "{} ACCIONES PENDIENTES"},
}


def set_locale(locale: str | None = None) -> str:
    """Select the UI locale (``"en"`` / ``"es"``); returns the effective one.

    ``None`` defers to ``MORDHEIM_LOCALE``. Unsupported locales keep the
    current selection, so a typo can never blank the interface.
    """
    global _active_locale
    candidate = str(locale or os.environ.get("MORDHEIM_LOCALE") or CANONICAL_LOCALE).strip().lower().split("-", 1)[0]
    if candidate in SUPPORTED_LOCALES:
        _active_locale = candidate
    return _active_locale


def current_locale() -> str:
    """The active UI locale (canonical English unless changed)."""
    return _active_locale


def tr(key: str) -> str:
    """Translate one UI string in the active locale.

    Untranslated or unknown keys return the key itself (the English literal),
    keeping the current interface byte-identical under ``en``.
    """
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_active_locale) or key
