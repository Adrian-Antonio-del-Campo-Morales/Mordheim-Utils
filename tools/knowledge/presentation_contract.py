"""Deterministic, typed presentation index; no inferred translations or ID labels."""
from __future__ import annotations

FIELDS = ("name", "effect", "description", "text", "note", "notes", "label", "result", "outcome", "rule", "reward", "author", "wyrdstone")
TODO_TRANSLATE = "TODO-TRANSLATE"
# Names are required for every independently presentable entity. Prose fields
# are optional: their presence in the source makes both locales mandatory.
REQUIRED_FIELDS = {kind: ("name",) for kind in (
    "band", "profile", "item", "skill", "collection", "rule", "mechanic",
    "hireling", "scenario", "lore", "mutation", "injury",
)}


def build_presentation_entries(artefact: dict) -> list[dict]:
    entries: dict[tuple, dict] = {}

    def visit(value: object, path: tuple[str, ...], owner: dict) -> None:
        if isinstance(value, list):
            for index, row in enumerate(value):
                visit(row, (*path, str(index)), owner)
            return
        if not isinstance(value, dict):
            return
        context = dict(owner)
        if value.get("band_id"):
            context["bandId"] = str(value["band_id"])
        root = path[0] if path else ""
        kind = {"bands": "band", "profiles": "profile", "items": "item", "skills": "skill", "collections": "collection", "rules_prose": "rule"}.get(root, "record")
        if (root != "rules_prose" and len(path) > 2) or (root == "rules_prose" and len(path) != 3):
            kind = "record"
        if root == "mechanics" and len(path) == 3:
            kind = "skill" if str(value.get("id", "")).startswith(("skill.", "spell.")) else "mechanic"
        if root == "campaign":
            if len(path) >= 3:
                section, rows = path[1:3]
                kind = {("hirelings", "profiles"): "hireling", ("hirelings", "rules"): "rule", ("scenarios", "scenarios"): "scenario", ("magic", "lores"): "lore", ("mutations", "mutations"): "mutation"}.get((section, rows), "record") if len(path) == 4 else "record"
                if section == "magic" and len(path) == 6 and path[4] == "spells":
                    kind = "skill"
                if section == "serious-injuries" and len(path) == 6 and path[4] == "results":
                    kind = "injury"
                if section == "serious-injuries" and len(path) == 4 and value.get("id"):
                    context["tableId"] = str(value["id"])
        fields = {}
        for field in FIELDS:
            locales = {}
            canonical = value.get(field)
            if field == "notes" and isinstance(canonical, list) and all(isinstance(line, str) for line in canonical):
                canonical = "\n".join(canonical)
            if isinstance(canonical, str) and canonical.strip():
                locales["en"] = canonical
            for key in (f"{field}_i18n", {"name": "names", "effect": "effects"}.get(field, f"{field}_i18n")):
                translations = value.get(key)
                if isinstance(translations, dict):
                    for lang, text in translations.items():
                        locales[lang] = text if isinstance(text, str) and text.strip() else TODO_TRANSLATE
            if locales:
                for locale in ("en", "es"):
                    locales.setdefault(locale, TODO_TRANSLATE)
                fields[field] = locales
        if "name" not in fields and "result" in fields:
            fields["name"] = fields["result"]
        if value.get("id") or value.get("item_id"):
            for required in REQUIRED_FIELDS.get(kind, ()):
                fields.setdefault(required, {locale: TODO_TRANSLATE for locale in ("en", "es")})
        if fields:
            identity = "/".join(path) if kind == "record" else str(value.get("id") or value.get("item_id") or "/".join(path))
            if kind == "rule" and identity.startswith(("skill.", "spell.")):
                kind = "skill"
            profiles = (value.get("applies_to") or {}).get("profile_ids", []) if isinstance(value.get("applies_to"), dict) else []
            for profile in profiles or [None]:
                ref = {"kind": kind, "id": identity, **context}
                if profile:
                    ref["profileId"] = str(profile)
                if not context and not profile:
                    ref["scope"] = "global"
                key = tuple(sorted(ref.items()))
                entry = {"ref": ref, "fields": fields, "source": "/".join(path)}
                previous = entries.get(key)
                if previous and previous["fields"] != fields:
                    raise ValueError(f"Ambiguous presentation identity {ref}: {previous['source']} / {entry['source']}")
                entries.setdefault(key, entry)
                if str(value.get("id", "")).startswith("campaign.magical-artefact."):
                    item_ref = {"kind": "item", "id": "magical_artefact." + value["id"].removeprefix("campaign.magical-artefact."), "scope": "global"}
                    entries[tuple(sorted(item_ref.items()))] = {**entry, "ref": item_ref}
        for key, child in value.items():
            if key not in {"names", "source_refs", "display_names", "display_effects"} and not key.endswith("_i18n") and not (key == "effects" and isinstance(child, dict)):
                visit(child, (*path, key), context)

    visit(artefact, (), {})
    return [entries[key] for key in sorted(entries)]


def presentation_issues(entries: list[dict]) -> list[str]:
    return [f"{entry['source']}:{field}.{locale}"
            for entry in entries for field, values in entry["fields"].items()
            for locale in ("en", "es") if not values.get(locale, "").strip() or TODO_TRANSLATE in values[locale]]
