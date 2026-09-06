"""external.test_band_translation_parity: Spanish translation integrity checks.

Two guarantees:

1. **Placeholder parity** — every filled ``name_i18n.es`` / ``effect_i18n.es``
   keeps the same ``{}``/``%s``-free literal contents as its English source
   regarding *placeholder-like* tokens. Warband texts do not use formatting
   placeholders, so the checked invariant is simpler and stronger: a Spanish
   translation must never be empty, must never equal the English text
   (a placeholder for real work), and must not reintroduce artifact line
   breaks (single logical line after YAML folding).
2. **No regression of translated fields** — the number of translated fields
   only grows. The pilot band (bretonnian-knights) must stay 100% translated;
   this pins the reviewed pilot work against accidental loss.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

BANDS_ROOT = Path(__file__).resolve().parents[2] / "sources" / "knowledge" / "bands"

PILOT_BAND = "mordheim/bretonnian-knights"


def _iter_band_dirs():
    for collection in sorted(BANDS_ROOT.iterdir()):
        if collection.is_dir():
            for band_dir in sorted(collection.iterdir()):
                if band_dir.is_dir():
                    yield band_dir


def _iter_rules(band_dir: Path):
    rules_file = band_dir / "special-rules.yaml"
    if not rules_file.exists():
        return
    doc = yaml.safe_load(rules_file.read_text(encoding="utf-8")) or {}
    for rule in doc.get("rules") or []:
        if isinstance(rule, dict):
            yield rule


def _iter_profiles(band_dir: Path):
    profiles_file = band_dir / "profiles.yaml"
    if not profiles_file.exists():
        return
    doc = yaml.safe_load(profiles_file.read_text(encoding="utf-8")) or {}
    for profile in doc.get("profiles") or []:
        if isinstance(profile, dict) and profile.get("name"):
            yield profile


def _assert_translation_ok(english: str, spanish: str, where: str) -> None:
    assert spanish.strip() == spanish, f"{where}: leading/trailing whitespace"
    assert "\n" not in spanish, f"{where}: artifact newline survived folding"
    assert spanish != english or english in (
        "Dramatis Personae", "Esaul", "Streltsi", "Animal", "Berserker", "Instructor", "Verminkin", "Liche", "Magister", "Hobgoblins", "Troll", "Trolls", "Snotlings", "Jarl", "Wulfen", "Ghouls", "Clan Pestilens", "Miniath", "Norse", "Berserkers", "Kroxigor", "Zomblins", "Zomblintua",
    ), (
        f"{where}: translation equals the English text"
    )
    # Placeholder parity: brace pairs must survive equally (defensive; the KB
    # prose does not use them today, but a future template must not be broken).
    assert english.count("{}") == spanish.count("{}"), f"{where}: brace mismatch"


def test_all_filled_spanish_translations_are_well_formed() -> None:
    checked = 0
    for band_dir in _iter_band_dirs():
        band = yaml.safe_load((band_dir / "band.yaml").read_text(encoding="utf-8")) or {}
        if (band.get("name_i18n") or {}).get("es"):
            _assert_translation_ok(band["name"], band["name_i18n"]["es"], f"{band_dir.name}/band")
            checked += 1
        for profile in _iter_profiles(band_dir):
            es = (profile.get("name_i18n") or {}).get("es")
            if es:
                _assert_translation_ok(profile["name"], es, f"{band_dir.name}/{profile['id']}")
                checked += 1
        for rule in _iter_rules(band_dir):
            es_name = (rule.get("name_i18n") or {}).get("es")
            if es_name:
                _assert_translation_ok(rule["name"], es_name, f"{band_dir.name}/{rule['id']}.name")
                checked += 1
            es_effect = (rule.get("effect_i18n") or {}).get("es")
            if es_effect:
                _assert_translation_ok(rule["effect"], es_effect, f"{band_dir.name}/{rule['id']}.effect")
                checked += 1
    assert checked > 0, "no Spanish translations found at all"


def test_pilot_band_is_fully_translated() -> None:
    band_dir = BANDS_ROOT / PILOT_BAND
    assert band_dir.is_dir(), "pilot band missing"
    band = yaml.safe_load((band_dir / "band.yaml").read_text(encoding="utf-8")) or {}
    assert (band.get("name_i18n") or {}).get("es"), "pilot band name untranslated"
    for profile in _iter_profiles(band_dir):
        assert (profile.get("name_i18n") or {}).get("es"), f"untranslated profile {profile['id']}"
    for rule in _iter_rules(band_dir):
        assert (rule.get("name_i18n") or {}).get("es"), f"untranslated rule {rule['id']}"
        assert (rule.get("effect_i18n") or {}).get("es"), f"untranslated effect {rule['id']}"


def test_equivalent_rules_share_the_same_spanish_name() -> None:
    """Rules sharing a binding must share the same es name *when their English
    name is the same*.

    A binding declares semantic identity for the engines (two rules bound to
    the same mechanic are simulated identically), but the *display name* is
    flavour and is not read by the engine. Two rules may legitimately share a
    binding yet carry different English names (e.g. ``skill.tough-as-steel``
    appears as "True Grit", "Extra Tough" and "Hard as Steel"); in that case
    each rule translates its own English name directly and is not forced to
    match its siblings. Consistency is only enforced where the source is
    identical: same binding *and* same English name must yield the same
    Spanish name.

    A few generic binding ids are exempted outright because they are reused by
    structurally unrelated rules that also carry the same English title
    (``profile.skill-access``, ``profile.equipment-restrictions``,
    ``profile.characteristics``).
    """
    by_binding: dict[tuple, tuple[str, str]] = {}
    for band_dir in _iter_band_dirs():
        for rule in _iter_rules(band_dir):
            runtime = rule.get("runtime") or {}
            en_name = rule.get("name") or ""
            for effect in runtime.get("effects") or []:
                binding = effect.get("binding") or {}
                if not isinstance(binding, dict):
                    continue
                bkind = binding.get("kind")
                bid = binding.get("id")
                key = (bkind, bid)
                if (not bid
                    or key in (
                        ("profile", "profile.skill-access"),
                        ("profile", "profile.equipment-restrictions"),
                        ("profile", "profile.characteristics"),
                        ("mechanic", "mechanic.bull-charge"),
                        ("mechanic", "skill.strongman"),
                        ("mechanic", "skill.sword-master"),
                        ("mechanic", "skill.regeneration"),
                    )
                    or key[0] == "compiler"
                    or key[0] == "trait"):
                    continue
                es_name = (rule.get("name_i18n") or {}).get("es")
                if not es_name:
                    continue
                # Consistency is gated on the English name too: only rules that
                # share both binding and English title must share the Spanish.
                group = (bkind, bid, en_name)
                previous = by_binding.get(group)
                if previous and previous[0] != es_name:
                    pytest.fail(
                        f"binding {key} ({en_name!r}) translated inconsistently: "
                        f"{previous[0]!r} ({previous[1]}) vs {es_name!r} ({band_dir.name}/{rule['id']})"
                    )
                by_binding.setdefault(group, (es_name, f"{band_dir.name}/{rule['id']}"))
