"""knowledge-web generator: canonical KB YAML -> web JSON artefact (P4.2).

Produces the deterministic JSON artefact the web Warband Manager loads
(``build/generated/knowledge-web/knowledge-web.json``) from the single
canonical source ``sources/knowledge/`` — the same read surface the desktop
``KnowledgePort`` uses, shaped as agreed in
``docs/decisions/web-knowledge-catalog-inventory.md``.

Rules (from the parallel plan, task P4.2):

- reads only ``sources/knowledge`` through ``mordheim_knowledge`` loaders;
- validates structure, unique ids and references **before** writing; a
  validation failure raises and the build must stop;
- output is deterministic: sorted by id, no timestamps, stable key order;
- the artefact is never edited by hand and is not versioned (gitignored);
- Combat Lab / simulation surfaces are excluded (see the inventory doc).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT  # artefact output root: <repo>/build/generated/knowledge-web/
sys.path.insert(0, str(REPO_ROOT / "src"))

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

#: Item kinds the web Campaign Manager consumes (inventory doc decision).
INCLUDED_ITEM_KINDS = frozenset({
    "armour", "close-combat-weapon", "combat-equipment",
    "material-or-upgrade", "ranged-weapon", "shield-or-defence",
    "trollheim-equipment",
})

#: Campaign catalogues the web Campaign Manager consumes, keyed by the name
#: stem used by ``CampaignCatalog.catalogue`` (inventory doc table).
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
            entry["collection"] = str(collection)
            bands.append(entry)
            indexes.setdefault(str(collection), []).append(str(band["id"]))
    return sorted(bands, key=_sort_key), dict(sorted(indexes.items()))


_EXPERIENCE_FORBIDDEN_RULE_REFS = frozenset({
    "shared-rule.brainless", "shared-rule.dead", "shared-rule.never-gain-experience",
    "shared-rule.experience", "shared-rule.animal", "shared-rule.animal-2",
    "shared-rule.animals", "shared-rule.animals-2", "shared-rule.animals-3",
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
            for profile in package.profiles:
                entry = _row(profile, drop=("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n"))
                entry["collection"] = str(collection)
                entry["band_id"] = str(package.band["id"])
                entry["can_gain_experience"] = _profile_can_gain_experience(package, profile)
                profiles.append(entry)
    return sorted(profiles, key=_sort_key)


def _build_items(ruleset: str) -> list[dict]:
    items = []
    for row in load_items(ruleset):
        kind = str(row.get("kind") or "")
        if kind not in INCLUDED_ITEM_KINDS:
            continue  # 'out-of-scope' and other Combat Lab-only kinds stay out
        entry = _row(row, drop=("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n", "effect", "effect_ids"))
        entry["item_id"] = entry.pop("id", "")
        items.append(entry)
    return sorted(items, key=_sort_key)


def _build_skills(ruleset: str) -> list[dict]:
    return sorted((_row(row, drop=("schema_version", "ruleset", "original_locale", "name_i18n", "effect_i18n")) for row in load_skills(ruleset)), key=_sort_key)


def _build_weapon_hands(ruleset: str) -> dict[str, int]:
    hands: dict[str, int] = {}
    for weapon in load_mechanics(ruleset).get("weapons") or ():
        value = weapon.get("hands")
        identifier = str(weapon.get("id") or "")
        if isinstance(value, int) and identifier:
            hands[identifier] = value
    return dict(sorted(hands.items()))


def _build_rules_prose(ruleset: str) -> dict:
    """Browsable rules prose catalogue (RULES browser parity, Agent 0 gap
    `artefact-lacks-prose-catalogue`): every ruleset-tagged document of
    ``catalog/rules`` with per-locale names and effects."""
    catalog = load_rules_catalog(ruleset)
    documents: dict[str, list[dict]] = {}
    for stem in catalog.stems():
        document = catalog.document(stem)
        rows = document.get("rules") or document.get("conditions") or ()
        documents[stem] = sorted((_row(row) for row in rows), key=_sort_key)
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
    text = json.dumps(artefact, ensure_ascii=False, indent=1, sort_keys=False) + "\n"
    if args.check:
        if not output.exists():
            print(f"check failed: {output} does not exist", file=sys.stderr)
            return 1
        if output.read_text(encoding="utf-8") != text:
            print(f"check failed: {output} is not up to date — regenerate it", file=sys.stderr)
            return 1
        print(f"check ok: {output} is up to date")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    size_kb = output.stat().st_size / 1024
    print(f"wrote {output} ({size_kb:.0f} KB, "
          f"{len(artefact['bands'])} bands, {len(artefact['profiles'])} profiles, "
          f"{len(artefact['items'])} items, {len(artefact['skills'])} skills)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
