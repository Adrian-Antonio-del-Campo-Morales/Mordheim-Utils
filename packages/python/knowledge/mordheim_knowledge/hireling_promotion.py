"""Give the staged hirelings the promotion shape of the knowledge base.

A staged hireling file mixes what the KB keeps apart, so this pass is a split:

* **The family split.** The KB holds Hired Swords in
  ``catalog/hirelings/hired-swords/`` and Dramatis Personae in
  ``catalog/hirelings/dramatis-personae/``, each with its own contract. The
  staged files mix them. A profile the source only *names* is faithful as
  ``normalization_status: name-only`` and is published in the Dramatis
  catalogue as ``out_of_scope`` with its reason — the contract's own way of
  keeping a record that cannot be modelled yet.
* **The campaign side.** The KB keeps a Hired Sword's hiring fee, upkeep,
  availability and eligibility in ``catalog/campaign/hired-swords-and-dramatis.yaml``
  and points back at the profile with ``profile_id``; the profile never repeats
  them. The staged ``hire_fee`` and ``available_to`` therefore leave the profile
  and become a *staged campaign document* in the KB shape. A fee the source
  prints in a currency the catalogue does not model keeps the amount and says so
  in the ``cost`` expression, which is the field the contract reserves for
  exactly that.
* **The KB record shapes.** The Miracle Workers priests are Hired Swords of
  their chapter — the source prints them with stats, a fee and their own prayers
  — so they become ``kind: hired-sword`` under the ``hireling.hired-sword.*``
  id; ``choice_groups`` becomes the KB's ``equipment.choices``; the starting
  Experience a priest begins with is the ``experience`` field ``profiles.yaml``
  already uses; the per-profile ``lore_assignments`` travel to
  ``campaign/magic.yaml`` as rows (``magic_promotion`` writes them).

The catalogue envelope is the KB envelope too: the catalogue id becomes the
family id the KB uses, and a document the staged tree does not have yet (the
Dramatis catalogue, the campaign side) is written only when a profile still
carries the facts that feed it, so a second run is a no-op.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from mordheim_knowledge import open_field_normalization as lexical
from mordheim_knowledge import staging_promotion as promotion
from mordheim_knowledge.editorial_schemas import validate_document

_STAGING_PROMOTION_SCHEMA = "hireling-profile-hired-sword.yaml.schema.json"
_DRAMATIS_SCHEMA = "hireling-profile-dramatis-personae.yaml.schema.json"
_CAMPAIGN_SCHEMA = "campaign-hired-swords-and-dramatis.yaml.schema.json"
_DRAMATIS_CATALOGUE = "hirelings-dramatis-personae"
_HIRED_SWORD_CATALOGUE = "hirelings-hired-swords"

#: ``(staging tree, document relative to the tree)`` of the staged campaign side.
CAMPAIGN_DOCUMENTS: dict[str, str] = {"2B": "catalog/hired-swords-and-dramatis-2b.yaml"}
#: The staged Dramatis catalogue of a tree.
DRAMATIS_DOCUMENTS: dict[str, str] = {"2B": "catalog/hirelings/dramatis-personae/grade-2b.yaml"}

#: ``normalization_status: name-only`` is faithful to the source: it lists the
#: hireling but prints no profile. The reason travels to the Dramatis catalogue,
#: where the contract makes it mandatory for an ``out_of_scope`` record.
OUT_OF_SCOPE_REASONS: dict[str, str] = {
    "hireling.dramatis.strigani-seer-necromancer": (
        "The source lists the Strigani Seer Necromancer among the Hired Swords the Strigoi Vampire "
        "warband may hire (only when it has no vampire) and prints no stat block; the profile stays "
        "unmodelled until the referenced source document is recovered."
    ),
    "hireling.dramatis.snerik-night-goblin-scout": (
        "The sources list Snerik Night Goblin Scout as hireable by the Night Goblin and Savage Orc "
        "warbands and print no profile; the entry stays unmodelled until the referenced source "
        "document is recovered."
    ),
}

#: The static half of each printed "may be hired" rule, in the registry's group
#: vocabulary. The other half — a warband that "contains non-humans", a warband
#: kind with no band id of its own — travels verbatim in ``eligibility.note``,
#: the field the contract keeps for what the lists cannot express.
GROUP = "warband-group."


def _groups(*names: str) -> list[str]:
    return [GROUP + name for name in names]


HIRELING_ELIGIBILITY: dict[str, dict[str, list[str]]] = {
    # Grade 2b — Karak Azgal anthology and Lords of the Marsh.
    "hireling.hired-sword.black-orc-bodyguard": {"allow_groups": _groups("orcs-and-goblins")},
    "hireling.hired-sword.bog-hunter": {
        "allow_groups": _groups("beastmen", "orcs-and-goblins"),
        "allow_band_ids": ["lords-of-the-marsh-mim"],
    },
    "hireling.hired-sword.whaler": {
        "forbid_groups": _groups("undead", "skaven"),
        "allow_band_ids": ["lords-of-the-marsh-mim"],
    },
    # mim-specialists.
    "hireling.hired-sword.ogre-treasure-hunter": {"forbid_groups": _groups("skaven")},
    "hireling.hired-sword.grave-warden": {"allow_groups": _groups("dwarf", "elf", "human")},
    "hireling.hired-sword.halfling-fence": {
        "forbid_groups": _groups("skaven", "undead", "beastmen", "orcs-and-goblins")
    },
    "hireling.hired-sword.halfling-pimp": {
        "forbid_groups": _groups("skaven", "undead", "beastmen", "orcs-and-goblins")
    },
    "hireling.hired-sword.albino-stormvermin": {"allow_groups": _groups("skaven")},
    "hireling.hired-sword.norse-bearman-bodyguard": {"forbid_groups": _groups("undead", "skaven")},
    "hireling.hired-sword.fire-eater": {
        "allow_groups": _groups("human"),
        "allow_band_ids": ["battle-monks-of-cathay", "maneaters"],
    },
    "hireling.hired-sword.sister-of-sigmar": {
        "allow_groups": _groups("dwarf", "elf", "human"),
        "forbid_band_ids": ["witch-hunters", "trollheim-witch-hunters"],
    },
    "hireling.hired-sword.midshipman": {
        "forbid_groups": _groups("skaven", "beastmen", "orcs-and-goblins")
    },
    # Miracle Workers priests: the chapter's own hiring rules.
    "hireling.hired-sword.mariner-priest-of-manann": {
        "allow_groups": _groups("human", "elf", "dwarf"),
        "forbid_groups": _groups("chaotic", "orcs-and-goblins", "dark-elf", "skaven", "undead"),
    },
    "hireling.hired-sword.priest-of-morr": {"allow_groups": _groups("human", "elf")},
    "hireling.hired-sword.war-priestess-of-myrmidia": {
        "allow_band_ids": ["tileans", "merchant-caravans", "watchmen-mim"]
    },
    "hireling.hired-sword.trickster-priest-of-ranald": {"allow_groups": _groups("human", "dwarf")},
    "hireling.hired-sword.priestess-of-shallya": {"allow_groups": _groups("human", "elf", "dwarf")},
    "hireling.hired-sword.warrior-priest-of-sigmar": {
        "allow_groups": _groups("human"),
        "forbid_band_ids": [
            "witch-hunters",
            "trollheim-witch-hunters",
            "pit-fighters",
            "pirates",
            "kislevites",
            "tileans",
            "norse-explorers-btb",
            "norse-explorers-lustria",
        ],
    },
    "hireling.hired-sword.druid-priest-of-taal": {
        "allow_groups": _groups("human"),
        "forbid_band_ids": [
            "witch-hunters",
            "trollheim-witch-hunters",
            "sisters-of-sigmar",
            "pit-fighters",
            "kislevites",
            "tileans",
            "norse-explorers-btb",
            "norse-explorers-lustria",
        ],
    },
    "hireling.hired-sword.wolf-priest-of-ulric": {},
    "hireling.hired-sword.priest-of-verena": {
        "allow_groups": _groups("human"),
        "forbid_band_ids": [
            "witch-hunters",
            "trollheim-witch-hunters",
            "sisters-of-sigmar",
            "pit-fighters",
            "pirates",
            "kislevites",
            "tileans",
            "norse-explorers-btb",
            "norse-explorers-lustria",
        ],
    },
    # Dramatis Personae.
    "hireling.dramatis.snorri-nosebiter": {"allow_groups": _groups("human", "dwarf")},
    "hireling.dramatis.aldred-fellblade": {"allow_groups": _groups("human")},
    "hireling.dramatis.armen-abbas": {
        "forbid_groups": _groups("sigmar-devoted"),
        "forbid_band_ids": ["witch-hunters", "trollheim-witch-hunters"],
    },
}

#: A price printed in a currency the KB does not model (Araby's dinars). The
#: contract's ``cost`` accepts the source's expression instead of a number, so
#: the amount stays and the currency travels with it.
_DINARS = re.compile(r"dinars?", re.IGNORECASE)
_DINAR_PREAMBLE = re.compile(r"^Priced in dinars[^.]*\.\s*")
_DINAR_TAIL = re.compile(r"^Priced in dinars[^.]*\.\s*")

#: The staged comments that describe the staged split, rewritten to the split
#: the promotion leaves behind (the file records survive; the prose must not lie).
HEADER_REWRITES: tuple[tuple[str, str], ...] = (
    (
        'Band availability lives in the "available_to" list of each profile (mirrors the\n'
        "# static eligibility of catalog/campaign/hired-swords-and-dramatis.yaml in the KB).",
        "# Band availability, hiring fees and eligibility live in the staged campaign\n"
        "# catalogue (catalog/hired-swords-and-dramatis-2b.yaml), which mirrors the KB\n"
        "# document catalog/campaign/hired-swords-and-dramatis.yaml.",
    ),
    (
        "# Name-only entries (the 2B sources list them as hireable but print no profile;\n"
        "# characteristics left null pending the external source documents):",
        "# Name-only entries moved to the staged Dramatis catalogue\n"
        "# (catalog/hirelings/dramatis-personae/grade-2b.yaml) as `out_of_scope`, with the\n"
        "# reason the profile cannot be modelled yet:",
    ),
)


def hireling_family(profile: dict) -> str:
    """Which KB catalogue keeps the profile: ``hired-swords`` or ``dramatis``."""
    if profile.get("kind") == "dramatis-personae":
        return "dramatis"
    if profile.get("normalization_status") == "name-only":
        return "dramatis"
    return "hired-swords"


def promoted_hireling_id(profile_id: str, family: str) -> str:
    """The KB id of a profile: ``hireling.<family>.<slug>``."""
    slug = profile_id.split(".", 2)[2]
    return f"hireling.{'dramatis' if family == 'dramatis' else 'hired-sword'}.{slug}"


def _renamed(node, old: str, new: str):
    """Rewrite the ids that follow a profile id, at any depth."""
    if isinstance(node, dict):
        return {key: _renamed(value, old, new) for key, value in node.items()}
    if isinstance(node, list):
        return [_renamed(value, old, new) for value in node]
    if isinstance(node, str) and node.startswith(old):
        return new + node[len(old):]
    return node


def promoted_choices(groups: list[dict]) -> list[dict]:
    """The staged ``choice_groups`` as the KB's ``equipment.choices``."""
    choices: list[dict] = []
    for group in groups:
        choose = group.get("choose")
        if not isinstance(choose, dict) or choose.get("kind") != "fixed":
            raise ValueError(f"Unsupported choice arity: {choose!r}")
        options = []
        for option in group.get("options") or []:
            if option.get("kind") != "item":
                raise ValueError(f"Unsupported choice option: {option.get('kind')!r}")
            item = {key: value for key, value in option.items() if key not in ("kind", "id")}
            options.append({"items": [item]})
        choices.append({"choose": int(choose["value"]), "options": options})
    return choices


def promoted_hireling_profile(profile: dict) -> dict:
    """One staged profile in the KB record shape; idempotent by construction."""
    promoted = {key: value for key, value in profile.items()}
    for key in ("available_to", "hire_fee", "lore_assignments"):
        promoted.pop(key, None)
    if "starting_experience" in promoted:
        promoted["experience"] = promoted.pop("starting_experience")
    family = hireling_family(profile)
    new_id = promoted_hireling_id(str(profile["id"]), family)
    if new_id != profile["id"]:
        promoted = _renamed(promoted, str(profile["id"]), new_id)
    equipment = promoted.get("equipment")
    if isinstance(equipment, dict) and "choice_groups" in equipment:
        promoted["equipment"] = {key: value for key, value in equipment.items() if key != "choice_groups"}
        promoted["equipment"]["choices"] = promoted_choices(equipment["choice_groups"])
    if family == "hired-swords":
        promoted["kind"] = "hired-sword"
    else:
        promoted["kind"] = "dramatis-personae"
        promoted.pop("experience", None)
        if profile.get("normalization_status") == "name-only":
            promoted["normalization_status"] = "out_of_scope"
            promoted["out_of_scope_reason"] = OUT_OF_SCOPE_REASONS[new_id]
        for key in ("characteristics", "warband_rating", "equipment", "rules", "skill_access"):
            if promoted.get(key) in (None, [], {}):
                promoted.pop(key, None)
    return promoted


def promoted_hireling_document(document: dict) -> dict:
    """A staged hireling file in the KB shape: the Hired Swords it still keeps."""
    kept = [
        profile
        for profile in document.get("profiles") or []
        if hireling_family(profile) == "hired-swords"
    ]
    return {
        **document,
        "catalog": _HIRED_SWORD_CATALOGUE,
        "profiles": [promoted_hireling_profile(profile) for profile in kept],
    }


def _dump(document: dict) -> str:
    return yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100
    )


def _existing(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return yaml.safe_load(lexical.read_text(path))


def _entries_of(document: dict | None) -> list[dict]:
    if not document:
        return []
    return list(document.get("hired_swords") or []) + list(document.get("dramatis_personae") or [])


def campaign_entry(profile: dict) -> dict:
    """One staged hireling in the shape of a ``hired-swords-and-dramatis`` entry."""
    family = hireling_family(profile)
    new_id = promoted_hireling_id(str(profile["id"]), family)
    slug = new_id.split(".", 2)[2]
    fee = profile.get("hire_fee") or {}
    note = str(fee.get("note") or "")
    tails = _DINAR_TAIL.sub("", note).strip()

    def cost(value, extra: bool) -> int | str | None:
        if value is None:
            return None
        if not _DINARS.search(note):
            return value
        text = f"{value} dinars"
        if extra and tails:
            text += f"; {tails.rstrip('.')}"
        return text

    old = str(profile["id"])
    eligibility = HIRELING_ELIGIBILITY.get(new_id, {})
    existing_eligibility = {
        "allow_groups": eligibility.get("allow_groups", []),
        "forbid_groups": eligibility.get("forbid_groups", []),
        "allow_band_ids": eligibility.get("allow_band_ids", []),
        "forbid_band_ids": eligibility.get("forbid_band_ids", []),
    }
    entry = {
        "id": f"campaign.hireling.{'dramatis' if family == 'dramatis' else 'hired-sword'}.{slug}",
        "profile_id": new_id,
        "hiring_fee": {"resources": {"gold_crowns": {"cost": cost(fee.get("hire"), True)}}},
        "upkeep": (
            {"resources": {"gold_crowns": {"cost": cost(fee.get("upkeep"), False)}}}
            if cost(fee.get("upkeep"), False) is not None
            else None
        ),
        "availability": (
            {"procedure_id": "campaign.hireling.availability.dramatis-search"}
            if family == "dramatis"
            else {"kind": "common"}
        ),
        "source_refs": _renamed(profile.get("source_refs") or [], old, new_id),
        "eligibility": {
            **existing_eligibility,
            "note": " ".join(
                entry.get("note", "") for entry in (profile.get("available_to") or [])
            ).strip(),
        },
    }
    return entry


def campaign_document(tree: str, profiles: list[dict]) -> str:
    """The staged campaign side of a tree, in the KB document shape."""
    target = promotion._kb_document("campaign/hired-swords-and-dramatis.yaml")
    entries = [campaign_entry(profile) for profile in profiles if _has_fee(profile)]
    entries.sort(key=lambda entry: entry["id"])
    document = {
        "schema_version": target["schema_version"],
        "ruleset": target["ruleset"],
        "catalog": target["catalog"],
        "status": promotion.STAGED_STATUS,
        "availability_procedures": target["availability_procedures"],
        "hired_swords": [entry for entry in entries if entry["id"].startswith("campaign.hireling.hired-sword.")],
        "dramatis_personae": [entry for entry in entries if entry["id"].startswith("campaign.hireling.dramatis.")],
        "eligibility_semantics": target["eligibility_semantics"],
        "effect_ids": target["effect_ids"],
    }
    return _dump(document)


def _has_fee(profile: dict) -> bool:
    fee = profile.get("hire_fee")
    return isinstance(fee, dict) and fee.get("hire") is not None


def dramatis_document(tree: str, profiles: list[dict]) -> str:
    """The staged Dramatis catalogue of a tree, in the KB document shape."""
    promoted = sorted(
        (promoted_hireling_profile(profile) for profile in profiles),
        key=lambda profile: profile["id"],
    )
    grades = {profile.get("grade") for profile in promoted}
    if len(grades) != 1:
        raise ValueError(f"{tree}: the Dramatis records carry several grades: {sorted(grades)}")
    document = {
        "schema_version": 1,
        "ruleset": "mordheim",
        "catalog": _DRAMATIS_CATALOGUE,
        "grade": promoted[0]["grade"],
        "profiles": promoted,
    }
    return _dump(document)


def _staged_profiles(tree: str) -> list[dict]:
    root = promotion._tree_root(tree) / "catalog" / "hirelings"
    profiles: list[dict] = []
    for path in sorted(root.glob("*.yaml")):
        document = yaml.safe_load(lexical.read_text(path)) or {}
        profiles.extend(document.get("profiles") or [])
    return profiles


def _built_edit(path: Path, text: str, schema_path: str, label: str) -> list[lexical.Edit]:
    """Publish a rebuilt document when it differs, after the contract accepts it."""
    current = lexical.read_text(path) if path.is_file() else ""
    if current and yaml.safe_load(current) == yaml.safe_load(text):
        return []
    problems = validate_document(schema_path, yaml.safe_load(text))
    if problems:
        raise ValueError(f"{path}: the promoted document does not match the contract: {problems[:3]}")
    lexical.publish(path, text)
    return [lexical.Edit(path, [label], text, current)]


def hireling_edits(tree: str) -> list[lexical.Edit]:
    """The hireling split, the Dramatis catalogue and the campaign side of a tree."""
    if tree not in CAMPAIGN_DOCUMENTS:
        return []
    profiles = _staged_profiles(tree)
    dramatis = [profile for profile in profiles if hireling_family(profile) == "dramatis"]

    edits: list[lexical.Edit] = []
    dramatis_relative = DRAMATIS_DOCUMENTS[tree]
    dramatis_path = promotion._document_path(tree, dramatis_relative)
    existing_dramatis = _existing(dramatis_path)
    if dramatis and existing_dramatis is None:
        text = dramatis_document(tree, dramatis)
        edits += _built_edit(
            dramatis_path,
            text,
            _DRAMATIS_SCHEMA,
            f"{len(dramatis)} Dramatis profiles split out of the Hired Sword files",
        )
    campaign_path = promotion._document_path(tree, CAMPAIGN_DOCUMENTS[tree])
    existing_campaign = _existing(campaign_path)
    fresh = [profile for profile in profiles if _has_fee(profile)]
    if fresh and existing_campaign is None:
        text = campaign_document(tree, profiles)
        edits += _built_edit(
            campaign_path,
            text,
            _CAMPAIGN_SCHEMA,
            f"{len(fresh)} hiring, upkeep and eligibility entries",
        )
    for path in sorted((promotion._tree_root(tree) / "catalog" / "hirelings").glob("*.yaml")):
        edits += _promoted_file(tree, path)
    return edits


def _promoted_file(tree: str, path: Path) -> list[lexical.Edit]:
    """Rewrite one staged hireling file: records promoted, Dramatis records moved out."""
    original = lexical.read_text(path)
    document = yaml.safe_load(original) or {}
    promoted = promoted_hireling_document(document)
    if yaml.safe_load(original) == promoted:
        return []
    lines = lexical.lines(original)
    ending = lexical.line_ending(lines[0]) if lines else "\n"
    for index, line in enumerate(lines):
        if promotion._own_key(line, "catalog", 0):
            lines[index] = lexical.replace_scalar(line, "catalog", _HIRED_SWORD_CATALOGUE)
            break
    moved = 0
    for start, end in reversed(promotion._records(lines)):
        record_id = promotion._record_id(lines[start])
        profile = next(
            (item for item in document.get("profiles") or [] if str(item["id"]) == record_id), None
        )
        if profile is None:
            continue
        record = promoted_hireling_profile(profile)
        if hireling_family(profile) == "dramatis":
            del lines[start:end]
            moved += 1
            continue
        body = _dump(record).splitlines()
        block = ["- " + body[0]] + ["  " + line if line.strip() else "" for line in body[1:]]
        lines[start:end] = [line + ending for line in block]
    text = "".join(lines)
    for old, new in HEADER_REWRITES:
        if old in text:
            text = text.replace(old, new, 1)
    if yaml.safe_load(text) != promoted:
        raise ValueError(f"{path}: the hireling pass changed more than the promotion shape")
    problems = validate_document(_STAGING_PROMOTION_SCHEMA, yaml.safe_load(text))
    if problems:
        raise ValueError(f"{path}: the promoted file does not match the contract: {problems[:3]}")
    lexical.publish(path, text)
    changes = [f"{len(promoted['profiles'])} Hired Sword profiles kept in the KB shape"]
    if moved:
        changes.append(f"{moved} Dramatis records moved to {DRAMATIS_DOCUMENTS[tree]}")
    return [lexical.Edit(path, changes, text, original)]
