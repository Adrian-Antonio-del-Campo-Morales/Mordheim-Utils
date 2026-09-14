"""Generate the deterministic browser knowledge artefact from canonical YAML.

The generator reads only ``sources/knowledge`` through the sanctioned loaders,
validates structure and references before writing, sorts records and never
includes timestamps. Outputs are generated files, not documentation or release
source; they are ignored and must not be hand-edited.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT  # artefact output root: <repo>/build/generated/knowledge-web/
PACKAGE_ROOTS = (
    REPO_ROOT / "packages" / "python" / "combat-engine",
    REPO_ROOT / "packages" / "python" / "roster-construction",
    REPO_ROOT / "packages" / "python" / "core",
    REPO_ROOT / "packages" / "python" / "knowledge",
    REPO_ROOT / "packages" / "python" / "adapters" / "desktop-ui",
    REPO_ROOT / "packages" / "python" / "campaign",
)
for package_root in reversed(PACKAGE_ROOTS):
    sys.path.insert(0, str(package_root))

from mordheim_knowledge.campaign import (  # noqa: E402
    load_campaign_catalog,
    load_hireling_traits,
    load_hirelings,
    load_post_battle_sequence,
    load_warband_groups,
)
from mordheim_knowledge.i18n import SUPPORTED_LOCALES, CANONICAL_LOCALE  # noqa: E402
from mordheim_knowledge.loader import (  # noqa: E402
    load_bands,
    load_collections,
    load_items,
    load_mechanics,
    load_racial_maximums,
    load_skills,
)
from mordheim_knowledge.rules_catalog import load_rules_catalog  # noqa: E402

SCHEMA_VERSION = 1
DEFAULT_RULESET = "mordheim"
OUTPUT_RELATIVE = Path("build") / "generated" / "knowledge-web" / "knowledge-web.json"
RULES_PROSE_FILENAME = "rules-prose.json"
DISPLAY_TEXT_FILENAME = "display-text.json"

#: Item kinds consumed by the browser Campaign Manager.
INCLUDED_ITEM_KINDS = frozenset({
    "armour", "close-combat-weapon", "combat-equipment",
    "material-or-upgrade", "ranged-weapon", "shield-or-defence",
    "trollheim-equipment",
})

#: Catalogue stems used by ``CampaignCatalog.catalogue``.
CAMPAIGN_CATALOGUE_STEMS = (
    "trading-post", "scenarios", "serious-injuries",
    "experience-and-advances", "exploration-and-income", "magic",
    "mutations", "hired-swords-and-dramatis", "scenario-rewards",
    "warband-rating", "recruitment-and-veterans", "trading-and-rarity",
)


class GenerationError(RuntimeError):
    """The KB or the generated artefact failed validation; build must stop."""


def _names(record: dict) -> dict[str, str]:
    """Per-locale display names: canonical English + reviewed translations.

    The KB keeps English canonical in ``name`` and translations in
    ``name_i18n`` (never an ``en`` mirror), so the artefact reconstructs the
    full locale map here; the web resolves the locale client-side.
    """
    names = {CANONICAL_LOCALE: str(record.get("name") or "")}
    for locale in sorted(SUPPORTED_LOCALES - {CANONICAL_LOCALE}):
        value = str((record.get("name_i18n") or {}).get(locale) or "").strip()
        if value:
            names[locale] = value
    return {locale: value for locale, value in names.items() if value}


def _effects(record: dict) -> dict[str, str]:
    effects = {CANONICAL_LOCALE: str(record.get("effect") or "")}
    for locale in sorted(SUPPORTED_LOCALES - {CANONICAL_LOCALE}):
        value = str((record.get("effect_i18n") or {}).get(locale) or "").strip()
        if value:
            effects[locale] = value
    return {locale: value for locale, value in effects.items() if value}


def _row(record: dict, *, drop: tuple[str, ...] = ("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n")) -> dict:
    """Copy a KB row dropping schema bookkeeping; names/effects travel per locale."""
    row = {key: value for key, value in record.items() if key not in drop}
    names = _names(record)
    if names:
        row["names"] = names
    effects = _effects(record)
    if effects:
        row["effects"] = effects
    return row


def _sort_key(record: dict) -> tuple:
    return (str(record.get("id") or record.get("item_id") or record.get("skill_id") or ""),)


def _require_unique(records: list[dict], id_key: str, context: str, *, scope: tuple[str, ...] = ("id",)) -> None:
    """Ids must be unique within the declared scope (e.g. per band)."""
    seen: set[tuple[str, ...]] = set()
    for record in records:
        identifier = str(record.get(id_key) or "")
        if not identifier:
            raise GenerationError(f"{context}: row without {id_key}: {record!r}")
        key = tuple(str(record.get(part) or "") for part in scope) + (identifier,)
        if key in seen:
            raise GenerationError(f"{context}: duplicated {id_key} {'/'.join(key)!r}")
        seen.add(key)


def _build_collections(ruleset: str) -> list[dict]:
    return [
        {"id": str(row["id"]), "names": _names(row),
         "rulesets": sorted(str(value) for value in row.get("rulesets") or ())}
        for row in sorted(load_collections(), key=_sort_key)
        if ruleset in set(row.get("rulesets") or ())
    ]


def _build_bands(ruleset: str) -> tuple[list[dict], dict[str, list[str]]]:
    bands: list[dict] = []
    indexes: dict[str, list[str]] = {}
    for collection in (row["id"] for row in load_collections() if ruleset in set(row.get("rulesets") or ())):
        for package in load_bands(str(collection)):
            if package.ruleset != ruleset:
                continue
            band = dict(package.band)
            roster = dict(band.get("roster") or {})
            members = sorted(
                ({key: value for key, value in member.items()} for member in roster.get("members") or ()),
                key=lambda member: str(member.get("profile_id") or ""),
            )
            if members:
                roster["members"] = members
            band["roster"] = roster
            entry = _row(band)
            entry["variants"] = sorted(
                (_row(variant, drop=("name_i18n", "effect_i18n")) for variant in band.get("variants") or ()),
                key=_sort_key,
            )
            entry["collection"] = str(collection)
            access: list[dict] = []
            for equipment_list in package.equipment_lists:
                list_id = str(equipment_list.get("id") or "")
                for item in equipment_list.get("items") or ():
                    item_id = str(item.get("item_id") or "")
                    if not item_id:
                        continue
                    row = {"item_id": item_id, "list_id": list_id}
                    if isinstance(item.get("cost"), int):
                        row["cost"] = item["cost"]
                    access.append(row)
            entry["equipment_access"] = sorted(
                access,
                key=lambda row: (str(row["item_id"]), str(row["list_id"])),
            )
            bands.append(entry)
            indexes.setdefault(str(collection), []).append(str(band["id"]))
    return sorted(bands, key=_sort_key), dict(sorted(indexes.items()))


_EXPERIENCE_FORBIDDEN_RULE_REFS = frozenset({
    "shared-rule.brainless", "shared-rule.dead", "shared-rule.never-gain-experience",
    "shared-rule.experience", "shared-rule.animal",
})


def _profile_can_gain_experience(package, profile: dict) -> bool:
    """Materialize the same decision as desktop KnowledgePort.can_gain_experience."""
    profile_id = str(profile.get("id") or "")
    if str(profile.get("type") or "") == "animal":
        return False
    return not any(
        profile_id in ((rule.get("applies_to") or {}).get("profile_ids") or ())
        and rule.get("rule_ref") in _EXPERIENCE_FORBIDDEN_RULE_REFS
        for rule in package.special_rules
    )


def _build_profiles(ruleset: str) -> list[dict]:
    profiles: list[dict] = []
    for collection in (row["id"] for row in load_collections() if ruleset in set(row.get("rulesets") or ())):
        for package in load_bands(str(collection)):
            if package.ruleset != ruleset:
                continue
            equipment_lists = {
                str(equipment_list.get("id") or ""): equipment_list
                for equipment_list in package.equipment_lists
            }
            for profile in package.profiles:
                entry = _row(profile, drop=("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n"))
                entry["collection"] = str(collection)
                entry["band_id"] = str(package.band["id"])
                entry["can_gain_experience"] = _profile_can_gain_experience(package, profile)
                entry["rule_ids"] = sorted({
                    *map(str, entry.get("rule_ids") or ()),
                    *(str(rule["rule_ref"]) for rule in package.special_rules
                      if rule.get("rule_ref") and str(profile["id"]) in set((rule.get("applies_to") or {}).get("profile_ids") or ())),
                })
                entry["equipment_forbids"] = sorted({
                    str(effect.get("binding", {}).get("parameters", {}).get("forbids"))
                    for rule in package.special_rules
                    if str(profile["id"]) in set((rule.get("applies_to") or {}).get("profile_ids") or ())
                    for effect in (rule.get("runtime") or {}).get("effects") or ()
                    if isinstance(effect, dict)
                    and isinstance(effect.get("binding"), dict)
                    and effect["binding"].get("id") == "profile.equipment-restrictions"
                    and effect["binding"].get("parameters", {}).get("forbids")
                })
                # The desktop resolves a profile's initial purchases through
                # its named equipment lists.  Materialise that relationship
                # in the web artefact so UI readers can show both permitted
                # equipment and reverse rule links without reopening YAML.
                access: list[dict] = []
                # Every band may expose a common equipment list in addition
                # to profile-specific lists.  The desktop resolver applies
                # both; materialise both here so common grants (for example
                # the first free dagger) reach every eligible profile.
                profile_list_ids = list(profile.get("equipment_lists") or ())
                profile_list_ids.extend(
                    list_id for list_id in equipment_lists
                    if list_id.endswith("-equipment-lists") and list_id not in profile_list_ids
                )
                for list_id in profile_list_ids:
                    equipment_list = equipment_lists.get(str(list_id))
                    if not equipment_list:
                        continue
                    for item in equipment_list.get("items") or ():
                        item_id = str(item.get("item_id") or "")
                        if not item_id:
                            continue
                        row = {"item_id": item_id, "list_id": str(list_id)}
                        if isinstance(item.get("cost"), int):
                            row["cost"] = item["cost"]
                        if isinstance(item.get("notes"), str) and item["notes"].strip():
                            row["notes"] = item["notes"].strip()
                        access.append(row)
                entry["equipment_access"] = sorted(
                    access,
                    key=lambda row: (str(row["item_id"]), str(row["list_id"])),
                )
                profiles.append(entry)
    return sorted(profiles, key=_sort_key)


def _build_items(ruleset: str) -> list[dict]:
    mechanics = {
        str(row.get("id") or ""): row
        for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons")
        for row in load_mechanics(ruleset).get(family) or ()
    }
    mechanics_by_name = {str(row.get("name") or "").casefold(): row for row in mechanics.values() if row.get("name")}
    items = []
    for row in load_items(ruleset):
        kind = str(row.get("kind") or "")
        if kind not in INCLUDED_ITEM_KINDS and str(row.get("id") or "") not in {"rope_hook", "healing_herbs", "elven_cloak"}:
            continue  # campaign-only items are needed by web tooltips
        entry = _row(row, drop=("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n", "effect_ids"))
        entry["item_id"] = entry.pop("id", "")
        mechanic = mechanics.get(str(row.get("mechanic_id") or "")) or mechanics_by_name.get(str(row.get("name") or "").casefold())
        if mechanic and not entry.get("effect"):
            if mechanic.get("effect"):
                entry["effect"] = mechanic["effect"]
            translations = mechanic.get("effect_i18n") or {}
            if translations:
                entry["effects"] = {
                    CANONICAL_LOCALE: str(mechanic.get("effect") or ""),
                    **{str(key): str(value) for key, value in translations.items() if value},
                }
        items.append(entry)
    by_id = {str(item["item_id"]): item for item in items}
    aliases = {
        "carronade": "swivel_gun",
        "carronade_cannonball": "ball_shot",
        "carronade_chain": "chain_shot",
        "carronade_grapeshot": "grape_shot",
        "horse_damsel_squire_only": "horse",
        "magic_tattoos": "magic_tattoo",
        "poisoned_darts": "poison_darts",
        "throwing_axes_same_as_throwing_knives": "throwing_knives",
    }
    for item_id, base_id in aliases.items():
        item, base = by_id.get(item_id), by_id.get(base_id)
        if item and base and not item.get("effect") and not item.get("effects"):
            if base.get("effect"): item["effect"] = base["effect"]
            if base.get("effects"): item["effects"] = base["effects"]
    kind_es = {
        "armour": "armadura", "close-combat-weapon": "arma de combate cuerpo a cuerpo",
        "combat-equipment": "equipo", "material-or-upgrade": "material o mejora",
        "out-of-scope": "equipo de campaña", "ranged-weapon": "arma de proyectiles",
        "shield-or-defence": "escudo o defensa", "trollheim-equipment": "equipo de suplemento",
    }
    for item in items:
        if item.get("effect") or item.get("effects"):
            continue
        source = next((str(ref.get("section") or ref.get("manual") or "").strip()
                       for ref in item.get("source_refs") or () if isinstance(ref, dict)), "Mordheimer")
        name = (item.get("names") or {}).get("en") or item["item_id"]
        spanish = (item.get("names") or {}).get("es") or name
        item["effects"] = {
            "en": f"{name}: campaign equipment. Rules reference: {source}.",
            "es": f"{spanish}: {kind_es.get(str(item.get('kind')), 'equipo de campaña')}. Referencia de reglas: {source}.",
        }
    return sorted(items, key=_sort_key)


def _build_skills(ruleset: str) -> list[dict]:
    return sorted((_row(row, drop=("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n")) for row in load_skills(ruleset)), key=_sort_key)


def _build_display_values(ruleset: str, skills: list[dict], rules_prose: dict, field: str) -> dict[str, dict[str, str]]:
    """Compact canonical display values for every id that may appear on a roster."""
    values: dict[str, dict[str, str]] = {}
    conflicting: set[str] = set()

    def add(row: dict, key: str | None = None) -> None:
        identifier = str(row.get("id") or "")
        localized_values = row.get(field) or (_names(row) if field == "names" else _effects(row))
        if not identifier or not isinstance(localized_values, dict):
            return
        localized = {str(locale): str(value) for locale, value in localized_values.items() if str(value).strip()}
        if not localized:
            return
        identifier = key or identifier
        if identifier in conflicting:
            return
        existing = values.get(identifier)
        if existing and existing != localized:
            values.pop(identifier)
            conflicting.add(identifier)
            return
        values[identifier] = localized

    for row in skills:
        add(row)
    for rows in rules_prose.values():
        for row in rows:
            add(row)
    for row in rules_prose.get("profile-special-rules", ()):
        applies_to = row.get("applies_to") or {}
        for profile_id in applies_to.get("profile_ids") or ():
            add(row, f"{profile_id}:{row['id']}")
            if row.get("band_id"):
                add(row, f"{row['band_id']}:{profile_id}:{row['id']}")
    for rows in load_mechanics(ruleset).values():
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    add(row)
    return dict(sorted(values.items()))


def _build_display_names(ruleset: str, skills: list[dict], rules_prose: dict) -> dict[str, dict[str, str]]:
    return _build_display_values(ruleset, skills, rules_prose, "names")


def _build_display_effects(ruleset: str, skills: list[dict], rules_prose: dict) -> dict[str, dict[str, str]]:
    return _build_display_values(ruleset, skills, rules_prose, "effects")


def _build_weapon_hands(ruleset: str) -> dict[str, int]:
    hands: dict[str, int] = {}
    for weapon in load_mechanics(ruleset).get("weapons") or ():
        value = weapon.get("hands")
        identifier = str(weapon.get("id") or "")
        if isinstance(value, int) and identifier:
            hands[identifier] = value
    return dict(sorted(hands.items()))


def _build_rules_prose(ruleset: str) -> dict:
    """Browsable rules prose catalogue for the browser rules view."""
    catalog = load_rules_catalog(ruleset)
    documents: dict[str, list[dict]] = {}
    for stem in catalog.stems():
        document = catalog.document(stem)
        rows = document.get("rules") or document.get("conditions") or ()
        documents[stem] = sorted((_row(row) for row in rows), key=_sort_key)
    # A profile can grant a band-specific rule directly, rather than a shared
    # ``rule_ref``. Keep every direct rule scoped by band, while publishing
    # globally unique ids with the shared catalogue for legacy lookups.
    special_rules = {str(row["id"]): row for row in documents.get("special-rules", ())}
    band_rules: list[dict] = []
    label_rules: list[dict] = []
    for collection in (row["id"] for row in load_collections() if ruleset in set(row.get("rulesets") or ())):
        for package in load_bands(str(collection)):
            if package.ruleset != ruleset:
                continue
            for rule in package.special_rules:
                label_rules.append(_row(rule))
                if rule.get("rule_ref"):
                    continue
                entry = {**_row(rule), "band_id": str(package.band["id"])}
                identifier = str(entry.get("id") or "")
                if not identifier:
                    raise GenerationError(f"band special rule without id: {package.band['id']!r}")
                band_rules.append(entry)
    direct_counts: dict[str, int] = {}
    for entry in band_rules:
        identifier = str(entry["id"])
        direct_counts[identifier] = direct_counts.get(identifier, 0) + 1
    for entry in band_rules:
        identifier = str(entry["id"])
        if direct_counts[identifier] == 1 and identifier not in special_rules:
            special_rules[identifier] = entry
    documents["special-rules"] = sorted(special_rules.values(), key=_sort_key)
    # Tooltips rendered from a warrior card know the profile id, so they can
    # safely disambiguate direct rules whose ids are reused by several bands.
    documents["profile-special-rules"] = sorted(band_rules, key=_sort_key)
    # Duplicate direct-rule ids cannot safely expose one rule's prose globally,
    # but their display names can still be localized when every occurrence
    # agrees. Publish those labels separately for campaign files that store
    # either the stable rule id or (in older files) the English name.
    localized_labels: dict[str, dict] = {}
    localized_ids: dict[str, dict] = {}
    conflicting_ids: set[str] = set()
    for entry in label_rules:
        names = entry.get("names") or {}
        english, spanish = str(names.get("en") or "").strip(), str(names.get("es") or "").strip()
        if not english or not spanish:
            continue
        identifier = str(entry.get("id") or "").strip()
        previous = localized_labels.get(english)
        if previous and previous["names"]["es"] != spanish:
            raise GenerationError(f"conflicting Spanish rule label for {english!r}")
        localized_labels[english] = {"id": f"localized-label.{english}", "names": {"en": english, "es": spanish}}
        if identifier and identifier not in conflicting_ids:
            candidate = {"id": identifier, "names": {"en": english, "es": spanish}}
            if identifier in localized_ids and localized_ids[identifier]["names"] != candidate["names"]:
                localized_ids.pop(identifier)
                conflicting_ids.add(identifier)
            else:
                localized_ids[identifier] = candidate
    localized_labels.update({f"id:{key}": value for key, value in localized_ids.items()})
    documents["localized-labels"] = sorted(localized_labels.values(), key=_sort_key)
    return dict(sorted(documents.items()))


def _build_campaign_section(ruleset: str, item_ids: set[str]) -> dict:
    catalogue = load_campaign_catalog(ruleset)
    section: dict = {}
    for stem in CAMPAIGN_CATALOGUE_STEMS:
        if not catalogue.has_catalogue(stem):
            continue  # optional catalogue; the inventory test flags gaps if the port needs it
        document = catalogue.catalogue(stem)
        cleaned = {key: value for key, value in document.items()
                   if key not in ("schema_version", "ruleset", "source")}
        section[stem] = cleaned
    section = dict(sorted(section.items()))

    # Hirelings: profiles, rules and traits as separate deterministic arrays.
    hirelings = load_hirelings(ruleset)
    traits = load_hireling_traits(ruleset)
    section["hirelings"] = {
        "profiles": sorted((_row(profile) for profile in hirelings.profiles), key=_sort_key),
        "rules": sorted((_row(rule) for rule in hirelings.rules), key=_sort_key),
        "traits": {
            str(row["profile_id"]): sorted(str(trait) for trait in row.get("traits") or ())
            for row in sorted(traits, key=lambda row: str(row["profile_id"]))
        },
    }
    section["warband_groups"] = sorted(
        (dict(group) for group in load_warband_groups(ruleset)), key=_sort_key,
    )
    section["racial_maximums"] = sorted(
        (dict(row) for row in load_racial_maximums(ruleset)), key=_sort_key,
    )
    # Post-battle sequence: step ids and their resolved catalogue references.
    sequence = load_post_battle_sequence(ruleset)
    section["post_battle_sequence"] = [
        {"id": step.id, "name": step.name, "resolves": step.resolves,
         "order": step.order, "repeatability": step.repeatability}
        for step in sorted(sequence.steps, key=lambda step: step.order)
    ]
    return section


def _validate_references(artefact: dict, all_item_ids: set[str]) -> None:
    """Reference checks that stop the build before anything is written."""
    item_ids = {str(item["item_id"]) for item in artefact["items"]}
    # The Trading Post references the full canonical item catalogue, including
    # kinds the artefact excludes (out-of-scope) — validate against the KB, and
    # only require the artefact's own items to exist in the KB universe.
    outside = sorted(item_ids - all_item_ids)
    if outside:
        raise GenerationError(f"artefact items missing from the KB catalogue: {outside}")
    band_ids = {str(band["id"]) for band in artefact["bands"]}
    collection_band = {(str(band["collection"]), str(band["id"])) for band in artefact["bands"]}
    for profile in artefact["profiles"]:
        key = (str(profile["collection"]), str(profile["band_id"]))
        if key not in collection_band:
            raise GenerationError(f"profiles: unknown band {'/'.join(key)!r}")
    lore_assignments = ((artefact["campaign"].get("magic") or {}).get("lore_assignments") or {}).get("rows") or []
    profile_ids = {str(profile["id"]) for profile in artefact["profiles"]}
    hireling_ids = {str(profile["id"]) for profile in artefact["campaign"]["hirelings"]["profiles"]}
    for assignment in lore_assignments:
        owner = str(assignment.get("profile_id") or "")
        if owner and owner not in profile_ids and owner not in hireling_ids:
            raise GenerationError(f"magic.lore_assignments: unknown profile_id {owner!r}")


def generate(ruleset: str = DEFAULT_RULESET) -> dict:
    """Build the full artefact dict (validated but not written)."""
    artefact: dict = {
        "schema_version": SCHEMA_VERSION,
        "ruleset": ruleset,
    }
    try:
        artefact["collections"] = _build_collections(ruleset)
        bands, bands_index = _build_bands(ruleset)
        artefact["bands"] = bands
        artefact["profiles"] = _build_profiles(ruleset)
        artefact["items"] = _build_items(ruleset)
        artefact["skills"] = _build_skills(ruleset)
        artefact["weapon_hands"] = _build_weapon_hands(ruleset)
        artefact["rules_prose"] = _build_rules_prose(ruleset)
        artefact["display_names"] = _build_display_names(ruleset, artefact["skills"], artefact["rules_prose"])
        artefact["display_effects"] = _build_display_effects(ruleset, artefact["skills"], artefact["rules_prose"])
        artefact["campaign"] = _build_campaign_section(ruleset, {str(item["item_id"]) for item in artefact["items"]})
    except GenerationError:
        raise
    except Exception as exc:
        # KB loader failures (e.g. a ruleset whose catalogues do not exist)
        # must stop the build with a clear, actionable message — never a raw
        # traceback from deep inside the loader.
        raise GenerationError(
            f"cannot generate the KB artefact for ruleset {ruleset!r}: {exc}"
        ) from exc
    _require_unique(artefact["collections"], "id", "collections")
    _require_unique(artefact["bands"], "id", "bands")
    _require_unique(artefact["profiles"], "id", "profiles", scope=("collection", "band_id"))
    _require_unique(artefact["items"], "item_id", "items")
    _require_unique(artefact["skills"], "id", "skills")
    artefact["indexes"] = {
        "bands_by_collection": bands_index,
        "items_by_id": {
            str(item["item_id"]): index
            for index, item in enumerate(artefact["items"])
        },
    }
    _validate_references(artefact, {str(row["id"]) for row in load_items(ruleset)})
    return artefact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ruleset", default=DEFAULT_RULESET)
    parser.add_argument("--output", type=Path, default=None,
                        help="output JSON path (default: <repo>/build/generated/knowledge-web/knowledge-web.json)")
    parser.add_argument("--check", action="store_true",
                        help="generate and compare against the existing artefact instead of writing")
    args = parser.parse_args(argv)
    output = args.output or ROOT / OUTPUT_RELATIVE
    output = Path(output).resolve()

    artefact = generate(args.ruleset)
    rules_prose = artefact.pop("rules_prose")
    display_text = {
        "display_names": artefact.pop("display_names"),
        "display_effects": artefact.pop("display_effects"),
    }
    artefact["rules_prose_url"] = RULES_PROSE_FILENAME
    artefact["display_text_url"] = DISPLAY_TEXT_FILENAME
    text = json.dumps(artefact, ensure_ascii=False, separators=(",", ":")) + "\n"
    rules_text = json.dumps(rules_prose, ensure_ascii=False, separators=(",", ":")) + "\n"
    display_text_text = json.dumps(display_text, ensure_ascii=False, separators=(",", ":")) + "\n"
    rules_output = output.with_name(RULES_PROSE_FILENAME)
    display_text_output = output.with_name(DISPLAY_TEXT_FILENAME)
    if args.check:
        for path, expected in ((output, text), (rules_output, rules_text), (display_text_output, display_text_text)):
            if not path.exists():
                print(f"check failed: {path} does not exist", file=sys.stderr)
                return 1
            if path.read_text(encoding="utf-8") != expected:
                print(f"check failed: {path} is not up to date — regenerate it", file=sys.stderr)
                return 1
        print(f"check ok: {output} is up to date")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    rules_output.write_text(rules_text, encoding="utf-8")
    display_text_output.write_text(display_text_text, encoding="utf-8")
    size_kb = output.stat().st_size / 1024
    print(f"wrote {output}, {rules_output.name}, and {display_text_output.name} ({size_kb:.0f} KB main, "
          f"{len(artefact['bands'])} bands, {len(artefact['profiles'])} profiles, "
          f"{len(artefact['items'])} items, {len(artefact['skills'])} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
