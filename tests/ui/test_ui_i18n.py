"""external.test_i18n: shared UI string catalogue and translation behavior."""
from __future__ import annotations

import pytest

from mordheim_ui import i18n
from mordheim_ui.i18n import CANONICAL_LOCALE, STRINGS, current_locale, set_locale, tr


@pytest.fixture(autouse=True)
def _restore_locale():
    yield
    set_locale(CANONICAL_LOCALE)


def test_default_locale_is_english_and_env_override_is_read(monkeypatch):
    assert set_locale() == CANONICAL_LOCALE
    monkeypatch.setenv("MORDHEIM_LOCALE", "es")
    assert set_locale() == "es"
    assert current_locale() == "es"


def test_unsupported_locale_keeps_the_current_selection():
    set_locale("es")
    assert set_locale("de") == "es"


def test_unknown_keys_return_the_english_key_itself():
    set_locale("es")
    assert tr("THERE IS NO SUCH STRING") == "THERE IS NO SUCH STRING"


def test_english_locale_renders_keys_byte_identical():
    set_locale("en")
    for key in STRINGS:
        assert tr(key) == key


def test_translated_strings_have_a_spanish_entry_and_english_is_the_key():
    for key, entry in STRINGS.items():
        assert set(entry) <= {"en", "es"}, key
        assert entry.get("es"), key
        assert "en" not in entry or entry["en"] == key, key


def test_post_battle_chrome_translates_under_spanish():
    set_locale("es")
    assert tr("RECOVERY") == "RECUPERACIÓN"
    assert tr("STEP {} OF {}").format(2, 8) == "PASO 2 DE 8"
    assert tr("Injuries").upper() == "HERIDAS"
    assert tr("{} ACTIONS REMAIN").format(3) == "3 ACCIONES PENDIENTES"


def test_every_catalogue_key_translates_in_spanish():
    set_locale("es")
    untranslated = [key for key in STRINGS if tr(key) == key]
    assert untranslated == [], untranslated
