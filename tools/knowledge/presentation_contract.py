"""Deterministic, typed presentation index; no inferred translations or ID labels.

The index joins every entry to the catalogue row it describes through a
*stable locator*, never through the position a row happens to occupy in an
array. Object steps are plain keys; array steps are selectors:

- ``[<field>=<value>, ...]``: the smallest conjunction of fields the row
  publishes that names exactly one row of its array — its canonical identifier
  (`id`, `item_id`, `result_id`) plus whatever published scope is needed to make
  that identifier unambiguous (`band_id`, `profile_id`, `list_id`, ...), so the
  entry keeps addressing that row after another row is inserted, removed or
  reordered anywhere in the array.
- ``[#<index>]``: no conjunction of published fields tells the row apart from a
  sibling (the source publishes nothing that identifies it). The consumer
  accepts the row at that position only when it still publishes exactly the text
  of the entry, and otherwise looks for the unique row of the array that does; a
  row that no longer exists, or two rows that cannot be told apart, are rejected
  with a specific error.

The entry identity follows the same rule: a nested catalogue row uses its own
canonical id when that id is unambiguous, and its stable locator otherwise.
"""
from __future__ import annotations

FIELDS = ("name", "effect", "description", "text", "note", "notes", "label", "result", "outcome", "rule", "reward", "author", "wyrdstone")
TODO_TRANSLATE = "TODO-TRANSLATE"
# Personal or editorial credits: a proper name is not translated, so its
# published text stands in every locale unless the source declares a real
# translation (translatable prose, e.g. "Anonymous"). A credit must never turn
# into a pending translation or a generic fallback for merely being text.
PERSONAL_FIELDS = frozenset({"author"})
# Canonical identifier fields a catalogue row may publish for itself.
LOCATOR_FIELDS = ("id", "item_id", "result_id")
# Characters the locator grammar reserves: a step is one path key or one
# bracketed selector, and a selector is a comma-separated conjunction of
# `field=value` pairs, so only brackets and commas are structural inside a value
# (a slash may: `id=localized-label.Animal Handler – Horse/Warhorse`). A value
# carrying one is rejected outright instead of being escaped silently into an
# ambiguous key.
LOCATOR_RESERVED = frozenset("[],{}")
# Names are required for every independently presentable entity. Prose fields
# are optional: their presence in the source makes both locales mandatory.
REQUIRED_FIELDS = {kind: ("name",) for kind in (
    "band", "profile", "item", "skill", "collection", "rule", "mechanic",
    "hireling", "scenario", "lore", "mutation", "injury",
)}

# Campaign catalogue rows the interface addresses by their own stable id
# instead of by their position in the artefact. Keyed by the path of the array
# that holds them, so a reader resolves a decision, clause or grant published
# under a new id without any consumer casting a raw field into a display value.
CAMPAIGN_ROW_KINDS = {
    ("campaign", "recruitment-and-veterans", "creation_decisions"): "creation-decision",
    ("campaign", "recruitment-and-veterans", "lifecycle_clauses"): "lifecycle-clause",
    ("campaign", "recruitment-and-veterans", "succession_clauses"): "succession-clause",
    ("campaign", "recruitment-and-veterans", "advance_access_clauses"): "advance-access-clause",
    ("campaign", "mutations", "grant_rules"): "mutation-grant",
}
# A printed creation roll publishes one outcome per interval; the outcome is
# addressed by the decision that owns it plus its own stable result id.
CREATION_OUTCOME_PATH = ("campaign", "recruitment-and-veterans", "creation_decisions")


def _published_identifier_counts(document: object) -> dict[str, int]:
    """Count every canonical identifier the document publishes, at any depth.

    An identifier that occurs exactly once is unambiguous and may identify a
    entry on its own; one that repeats (`item_id` inside two profiles of the same
    band, a profile id in two bands) cannot, and the stable locator stays the
    identity so two entries can never collide under it.
    """
    counts: dict[str, int] = {}

    def walk(value: object) -> None:
        if isinstance(value, list):
            for row in value:
                walk(row)
            return
        if not isinstance(value, dict):
            return
        for field in LOCATOR_FIELDS:
            text = value.get(field)
            if isinstance(text, str) and text:
                counts[text] = counts.get(text, 0) + 1
        for child in value.values():
            walk(child)

    walk(document)
    return counts


def _canonical_identifier(value: dict, identifiers: dict[str, int]) -> str:
    """The row's own unambiguous canonical id, or `""` when it has none."""
    for field in LOCATOR_FIELDS:
        text = value.get(field)
        if isinstance(text, str) and text and identifiers.get(text) == 1:
            return text
    return ""


def _selector_pairs(row: dict, rows: list) -> list[tuple[str, str]] | None:
    """The smallest conjunction of published fields that names exactly this row.

    The canonical identifier comes first and the published scope is added only
    while the conjunction is still ambiguous — a profile id that two bands share
    needs its `band_id`, an equipment entry listed twice by one profile needs its
    `list_id` — so the step keeps naming the same row whatever else the array
    does. `None` means no conjunction of published fields tells the row apart.
    """
    candidates = [field for field in LOCATOR_FIELDS if _scalar_text(row.get(field)) is not None]
    candidates += sorted(field for field, value in row.items()
                         if field not in LOCATOR_FIELDS and _scalar_text(value) is not None)
    chosen: list[tuple[str, str]] = []
    for field in candidates:
        text = _scalar_text(row.get(field))
        if text is None or LOCATOR_RESERVED.intersection(f"{field}{text}"):
            continue
        chosen.append((field, text))
        if sum(1 for sibling in rows if _matches(sibling, chosen)) == 1:
            return chosen
    return None


def _scalar_text(value: object) -> str | None:
    """A published scalar usable in a selector, as the text it is written as."""
    return value if isinstance(value, str) and value else None


def _matches(row: object, pairs: list[tuple[str, str]]) -> bool:
    return isinstance(row, dict) and all(_scalar_text(row.get(field)) == value for field, value in pairs)


def _locator_step(rows: list, index: int) -> str:
    """Stable array step: the row's canonical identifier plus its scope, or a hint."""
    row = rows[index]
    if isinstance(row, dict):
        pairs = _selector_pairs(row, rows)
        if pairs:
            return "[" + ",".join(f"{field}={value}" for field, value in pairs) + "]"
    return f"[#{index}]"


def build_presentation_entries(artefact: dict) -> list[dict]:
    entries: dict[tuple, dict] = {}
    identifiers = _published_identifier_counts(artefact)

    def visit(value: object, path: tuple[str, ...], owner: dict, parent_id: str = "") -> None:
        if isinstance(value, list):
            for index, row in enumerate(value):
                visit(row, (*path, _locator_step(value, index)), owner, parent_id)
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
        # Campaign catalogue rows the interface addresses by their own stable id.
        campaign_kind = CAMPAIGN_ROW_KINDS.get(path[:-1]) if len(path) == 4 else None
        if campaign_kind:
            kind = campaign_kind
        decision_id = str(value.get("id") or "") if campaign_kind == "creation-decision" else parent_id
        if (len(path) == 6 and path[:3] == CREATION_OUTCOME_PATH and path[4] == "outcomes"
                and isinstance(value.get("result_id"), str)):
            kind = "creation-outcome"
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
                if field in PERSONAL_FIELDS:
                    published = value.get(field)
                    if isinstance(published, str) and published.strip():
                        for locale in ("en", "es"):
                            current = locales.get(locale)
                            if not isinstance(current, str) or not current.strip() or current == TODO_TRANSLATE:
                                locales[locale] = published
                for locale in ("en", "es"):
                    locales.setdefault(locale, TODO_TRANSLATE)
                fields[field] = locales
        if "name" not in fields and "result" in fields:
            fields["name"] = fields["result"]
        if value.get("id") or value.get("result_id") or value.get("item_id"):
            for required in REQUIRED_FIELDS.get(kind, ()):
                fields.setdefault(required, {locale: TODO_TRANSLATE for locale in ("en", "es")})
        if fields:
            if kind == "creation-outcome":
                # The printed result of one interval is addressed by the decision
                # that owns it plus its own stable result id, never by the array
                # position the catalogue happens to publish it at.
                identity = f"{decision_id}/{value['result_id']}"
            elif kind == "record":
                # A nested catalogue row is identified by its own canonical id
                # when that id is unambiguous, and by its stable locator
                # otherwise: never by the position it occupies in an array.
                identity = _canonical_identifier(value, identifiers) or "/".join(path)
            else:
                identity = str(value.get("id") or value.get("item_id") or "/".join(path))
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
                    # One identity must address one text: two rows claiming it
                    # with different prose would make the resolution silently
                    # pick one of them. The same text published under two paths
                    # (`skills/` and `mechanics/skills/` alias one skill row) is
                    # the same entry, and one of the two paths is kept.
                    raise ValueError(f"Duplicate presentation identity {ref}: {previous['source']} / {entry['source']}")
                entries.setdefault(key, entry)
                if str(value.get("id", "")).startswith("campaign.magical-artefact."):
                    item_ref = {"kind": "item", "id": "magical_artefact." + value["id"].removeprefix("campaign.magical-artefact."), "scope": "global"}
                    entries[tuple(sorted(item_ref.items()))] = {**entry, "ref": item_ref}
        for key, child in value.items():
            if key not in {"names", "source_refs", "display_names", "display_effects"} and not key.endswith("_i18n") and not (key == "effects" and isinstance(child, dict)):
                visit(child, (*path, key), context, decision_id)

    visit(artefact, (), {})
    return [entries[key] for key in sorted(entries)]


def presentation_issues(entries: list[dict]) -> list[str]:
    return [f"{entry['source']}:{field}.{locale}"
            for entry in entries for field, values in entry["fields"].items()
            for locale in ("en", "es") if not values.get(locale, "").strip() or TODO_TRANSLATE in values[locale]]
