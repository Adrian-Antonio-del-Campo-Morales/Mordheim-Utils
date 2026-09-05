"""external.test_i18n: KB locale policy and localized display names."""
from __future__ import annotations

import pytest

from mordheim_knowledge.i18n import (
    CANONICAL_LOCALE,
    SUPPORTED_LOCALES,
    current_locale,
    display_effect,
    display_name,
    resolved_name,
    set_locale,
)


@pytest.fixture(autouse=True)
def _restore_locale():
    yield
    set_locale(CANONICAL_LOCALE)


# Bretonnian rules are the one record family with reviewed Spanish
# translations in the KB (name_i18n.es / effect_i18n.es).
_BRETONNIAN_RULES = "bands/mordheim/bretonnian-knights/special-rules.yaml"


def _translated_rule() -> dict:
    import yaml

    from mordheim_knowledge.loader import knowledge_root

    document = yaml.safe_load((knowledge_root() / _BRETONNIAN_RULES).read_text(encoding="utf-8"))
    for rule in document.get("rules") or ():
        spanish = (rule.get("name_i18n") or {}).get("es")
        if rule.get("name") and spanish:
            return rule
    raise AssertionError("the Bretonnian translated fixture rule disappeared from the KB")


def test_default_locale_is_canonical_english_and_mordheim_locale_env_is_read(monkeypatch):
    assert set_locale() == CANONICAL_LOCALE
    monkeypatch.setenv("MORDHEIM_LOCALE", "es")
    assert set_locale() == "es"
    assert current_locale() == "es"


def test_unsupported_locale_is_ignored():
    set_locale("es")
    assert set_locale("de") == "es"
    assert set_locale("xx-YY") == "es"


def test_display_name_prefers_the_reviewed_translation_in_the_active_locale():
    rule = _translated_rule()
    set_locale("es")
    assert display_name(rule) == str(rule["name_i18n"]["es"])
    set_locale("en")
    assert display_name(rule) == str(rule["name"])


def test_display_name_falls_back_to_the_canonical_name_when_translation_is_missing():
    record = {"id": "skill.regeneration", "name": "Regeneration", "name_i18n": {"es": None}}
    set_locale("es")
    assert display_name(record) == "Regeneration"


def test_display_name_falls_back_to_any_translated_locale():
    rule = _translated_rule()
    record = {"name": None, "name_i18n": {"es": str(rule["name_i18n"]["es"])}}
    set_locale("en")
    assert display_name(record) == str(rule["name_i18n"]["es"])

def test_display_name_returns_empty_for_untranslated_and_resolved_name_uses_the_id():
    record = {"id": "skill.regeneration", "name": "Regeneration", "name_i18n": {"es": None}}
    set_locale("es")
    assert display_name(record) == "Regeneration"
    assert resolved_name(record) == "Regeneration"


def test_display_name_and_resolved_name_tolerate_non_dict_records():
    assert display_name(None, "fallback-id") == "fallback-id"
    assert display_name({"name": None}, "") == ""
    assert resolved_name(None, "fallback-id") == "fallback-id"
    assert resolved_name({"id": "weapon.axe"}, "") == "weapon.axe"


def test_display_effect_prefers_the_canonical_prose_under_english_and_the_translation_under_spanish():
    record = {"effect": "The warrior regenerates.", "effect_i18n": {"es": "El guerrero regenera."}}
    assert display_effect(record) == "The warrior regenerates."
    set_locale("es")
    assert display_effect(record) == "El guerrero regenera."
    stripped = {"effect": None, "effect_i18n": {"es": "El guerrero regenera."}}
    assert display_effect(stripped) == "El guerrero regenera."


def test_supported_locales_is_english_and_spanish():
    assert SUPPORTED_LOCALES == frozenset({"en", "es"})
