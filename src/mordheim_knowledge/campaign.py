"""knowledge.campaign: runtime loaders for the published campaign catalogues.

Implements the loading contract tracked as ``campaign.runtime-loaders`` in
``sources/knowledge/CAMPAIGN INGESTION RESULTS.md`` and TODO.md section 5.
The KB campaign data under ``catalog/campaign/**`` is published and inert;
these loaders are the authorised runtime read path and validate, at load
time, the integrity a consumer can rely on:

- headers (``schema_version``, ``ruleset``, ``catalog``, ``status``);
- per-document uniqueness of every declared ``id``;
- reference resolution across the KB: ``item_id`` (``catalog/items``),
  ``profile_id`` (band profiles **and** ``catalog/hirelings/**``),
  ``lore`` (``catalog/campaign/magic.yaml``), band references and
  ``warband-group.*`` (``registry/warband-groups.yaml``), plus the
  catalogue-to-catalogue links of the sequence, scenarios, magic, serious
  injuries and rarity documents.

The loaders never decide rules and never hold campaign state: they return
validated read models.  ``mordheim_campaign.application.knowledge_port`` is
the intended consumer of the loading contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from mordheim_knowledge.loader import knowledge_root
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_items
from mordheim_knowledge.loader import load_skills
from mordheim_knowledge.loader import read_yaml


CAMPAIGN_CATALOGUE_DIR = "catalog/campaign"
HIRELING_CATALOGUE_DIR = "catalog/hirelings"
CONDITIONS_CATALOGUE = "catalog/rules/conditions.yaml"
WARBAND_GROUPS_CATALOGUE = "registry/warband-groups.yaml"

POST_BATTLE_SEQUENCE_STEM = "post-battle-sequence"
HIRED_SWORDS_STEM = "hired-swords-and-dramatis"

SCHEMA_VERSIONS = frozenset({1, 2})
DOCUMENT_STATUSES = frozenset({"published", "draft"})
GROUP_KINDS = frozenset({"race", "alignment", "faction", "culture"})
REPEATABILITIES = frozenset({"once", "repeatable"})
HIRELING_COST_RESOURCES = frozenset({
    "gold_crowns", "wyrdstone_fragments", "treasures", "campaign_points",
})

#: Campaign files whose validation has cross-document responsibilities.
_REQUIRED_CAMPAIGN_STEMS = frozenset({
    "post-battle-sequence", "hired-swords-and-dramatis", "magic",
    "experience-and-advances", "scenarios", "serious-injuries",
    "trading-and-rarity",
})


# --------------------------------------------------------------------------- #
# Small read models returned by the loaders
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class CampaignStep:
    """One post-battle step in normative order."""

    order: int
    id: str
    name: str
    resolves: str  # catalogue file the step resolves, e.g. "serious-injuries.yaml"
    repeatability: str
    source_refs: tuple[dict, ...]


@dataclass(frozen=True, slots=True)
class PostBattleSequence:
    """Validated ``post-battle-sequence.yaml``: the resolution order."""

    id: str
    name: str
    steps: tuple[CampaignStep, ...]
    source_refs: tuple[dict, ...]

    @property
    def resolved_catalogues(self) -> tuple[str, ...]:
        """Filenames the steps resolve, in order, without repetition."""
        seen = []
        for step in self.steps:
            if step.resolves not in seen:
                seen.append(step.resolves)
        return tuple(seen)


@dataclass(frozen=True, slots=True)
class CampaignCatalog:
    """Validated campaign documents keyed by catalogue file name stem."""

    documents: dict[str, dict]  # read-only by convention; ``catalogue`` to look up

    def catalogue(self, name: str) -> dict:
        """Return one document by file name (``trading-post.yaml``) or stem."""
        stem = name[:-5] if name.endswith(".yaml") else name
        try:
            return self.documents[stem]
        except KeyError as exc:
            raise ValueError(f"unknown campaign catalogue: {name}") from exc

    def has_catalogue(self, name: str) -> bool:
        stem = name[:-5] if name.endswith(".yaml") else name
        return stem in self.documents


@dataclass(frozen=True, slots=True)
class HirelingCatalogue:
    """Validated hireling profiles and rules of ``catalog/hirelings``.

    ``profiles`` keeps the profile documents as published (including their
    inline rules); ``rules`` holds the top-level rule declarations of the
    ``rules.yaml`` and shared catalogue files.
    """

    profiles: tuple[dict, ...]
    rules: tuple[dict, ...]

    @property
    def profile_ids(self) -> frozenset[str]:
        return frozenset(str(row.get("id") or "") for row in self.profiles)


# --------------------------------------------------------------------------- #
# Generic tree helpers
# --------------------------------------------------------------------------- #


def _declared_ids(node) -> list[str]:
    """All string ``id`` declarations anywhere in a YAML tree."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "id" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_declared_ids(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_declared_ids(value))
    return found


def _reference_values(node, key: str) -> list[str]:
    """Scalar/list string values stored under ``key`` anywhere in a tree."""
    found: list[str] = []
    if isinstance(node, dict):
        if key in node:
            value = node[key]
            values = value if isinstance(value, list) else [value]
            found.extend(item for item in values if isinstance(item, str))
        for value in node.values():
            found.extend(_reference_values(value, key))
    elif isinstance(node, list):
        for value in node:
            found.extend(_reference_values(value, key))
    return found


def _assert_unique_ids(document: dict, context: str) -> None:
    ids = _declared_ids(document)
    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise ValueError(
            f"campaign catalogue {context}: duplicate declared ids: "
            + ", ".join(duplicates[:8])
        )


def _check_header(
    document: dict,
    path: Path,
    ruleset: str,
    *,
    require_catalog: bool,
    require_status: bool,
) -> None:
    """Header contract shared by every campaign-facing catalogue file."""
    if require_catalog:
        stem = path.stem
        expected = f"campaign-{stem}"
        if document.get("catalog") != expected:
            raise ValueError(
                f"campaign document {path.name}: catalog {document.get('catalog')!r} "
                f"does not match expected {expected!r}"
            )
    if document.get("ruleset") != ruleset:
        raise ValueError(
            f"campaign document {path.name}: ruleset {document.get('ruleset')!r} "
            f"does not match {ruleset!r}"
        )
    version = document.get("schema_version")
    if version not in SCHEMA_VERSIONS:
        raise ValueError(
            f"campaign document {path.name}: unsupported schema_version "
            f"{version!r} (expected one of {sorted(SCHEMA_VERSIONS)})"
        )
    if require_status:
        status = document.get("status")
        if status not in DOCUMENT_STATUSES:
            raise ValueError(
                f"campaign document {path.name}: unsupported status {status!r}"
            )


# --------------------------------------------------------------------------- #
# Canonical pools shared by the validation passes
# --------------------------------------------------------------------------- #


def _canonical_band_data(base: Path, ruleset: str):
    """``(band ids, {band id: profile ids}, all profile ids)`` for a ruleset."""
    band_ids: set[str] = set()
    band_profiles: dict[str, set[str]] = {}
    profile_ids: set[str] = set()
    for collection in load_collections(base):
        if ruleset not in set(collection.get("rulesets") or ()):
            continue
        for package in load_bands(str(collection["id"]), base):
            if package.ruleset != ruleset:
                continue
            band_id = str(package.band.get("id") or "")
            if not band_id:
                raise ValueError(f"band package without id: {package.path}")
            band_ids.add(band_id)
            members = {str(row.get("id") or "") for row in package.profiles}
            members.discard("")
            band_profiles[band_id] = members
            profile_ids |= members
    return band_ids, band_profiles, profile_ids


def _canonical_item_ids(base: Path, ruleset: str) -> set[str]:
    return {str(row.get("id") or "") for row in load_items(ruleset, base)}


def _canonical_condition_ids(base: Path) -> set[str]:
    document = read_yaml(base / CONDITIONS_CATALOGUE)
    return {str(row.get("id") or "") for row in document.get("conditions") or ()}


def _document_stems(base: Path) -> set[str]:
    return {path.stem for path in (base / CAMPAIGN_CATALOGUE_DIR).glob("*.yaml")}


# --------------------------------------------------------------------------- #
# Per-document integrity passes
# --------------------------------------------------------------------------- #


def _sequence_from_document(document: dict) -> PostBattleSequence:
    sequence = document.get("sequence") or {}
    steps = []
    for row in sequence.get("steps") or ():
        steps.append(CampaignStep(
            order=int(row.get("order") or 0),
            id=str(row.get("id") or ""),
            name=str(row.get("name") or ""),
            resolves=str(row.get("resolves") or ""),
            repeatability=str(row.get("repeatability") or ""),
            source_refs=tuple(row.get("source_refs") or ()),
        ))
    if not steps or any(not step.id or not step.name or not step.resolves for step in steps):
        raise ValueError("campaign post-battle sequence has an incomplete step")
    return PostBattleSequence(
        id=str(sequence.get("id") or ""),
        name=str(sequence.get("name") or ""),
        steps=tuple(steps),
        source_refs=tuple(sequence.get("source_refs") or ()),
    )


def _validate_sequence_document(
    sequence: PostBattleSequence, campaign_stems: set[str]
) -> None:
    orders = [step.order for step in sequence.steps]
    if orders != list(range(1, len(orders) + 1)):
        raise ValueError(
            "campaign post-battle sequence steps must be contiguous from 1; "
            f"got orders {orders}"
        )
    resolvable = campaign_stems - {POST_BATTLE_SEQUENCE_STEM}
    for step in sequence.steps:
        stem = step.resolves[:-5] if step.resolves.endswith(".yaml") else step.resolves
        if stem not in resolvable:
            raise ValueError(
                f"post-battle step {step.id} resolves unknown catalogue "
                f"{step.resolves!r}"
            )
        if step.repeatability not in REPEATABILITIES:
            raise ValueError(
                f"post-battle step {step.id}: invalid repeatability "
                f"{step.repeatability!r}"
            )


def _validate_scenarios_document(document: dict) -> None:
    scenario_ids = {
        str(row.get("id") or "")
        for row in document.get("scenarios") or ()
        if row.get("id")
    }
    for value in _reference_values(document, "scenario"):
        if value not in scenario_ids:
            raise ValueError(
                f"campaign catalogue scenarios: selection table references "
                f"unknown scenario {value!r}"
            )


def _validate_magic_document(
    document: dict,
    lore_ids: set[str],
    band_profiles: dict[str, set[str]],
    hireling_ids: set[str],
) -> None:
    for row in document.get("lore_assignments", {}).get("rows") or ():
        lore = row.get("lore")
        if not lore or lore not in lore_ids:
            raise ValueError(
                f"campaign catalogue magic: wizard {row.get('wizard')!r} "
                f"assigned unknown lore {lore!r}"
            )
        profile_id = row.get("profile_id")
        band = row.get("band")
        if band is not None:
            if band not in band_profiles or profile_id not in band_profiles[band]:
                raise ValueError(
                    f"campaign catalogue magic: wizard {row.get('wizard')!r} "
                    f"references {profile_id!r} outside band {band!r}"
                )
        elif profile_id not in hireling_ids:
            raise ValueError(
                f"campaign catalogue magic: wizard {row.get('wizard')!r} "
                f"references unknown hireling profile {profile_id!r}"
            )


def _validate_hired_swords_document(
    document: dict, hireling_ids: set[str]
) -> None:
    procedure_ids = {
        str(row.get("id") or "")
        for row in document.get("availability_procedures") or ()
    }
    entries = list(document.get("hired_swords") or ()) + list(
        document.get("dramatis_personae") or ()
    )
    for entry in entries:
        profile_id = entry.get("profile_id")
        if not profile_id or profile_id not in hireling_ids:
            raise ValueError(
                f"campaign catalogue hired-swords-and-dramatis: entry "
                f"{entry.get('id')!r} references unknown hireling profile "
                f"{profile_id!r}"
            )
        availability = entry.get("availability") or {}
        procedure_id = availability.get("procedure_id")
        if procedure_id is not None and procedure_id not in procedure_ids:
            raise ValueError(
                f"campaign catalogue hired-swords-and-dramatis: entry "
                f"{entry.get('id')!r} references unknown availability procedure "
                f"{procedure_id!r}"
            )
        for cost_key in ("hiring_fee", "upkeep"):
            cost = entry.get(cost_key)
            if not isinstance(cost, dict):
                continue
            resources = cost.get("resources") or {}
            unknown = set(resources) - HIRELING_COST_RESOURCES
            if unknown:
                raise ValueError(
                    f"campaign catalogue hired-swords-and-dramatis: entry "
                    f"{entry.get('id')!r} uses unknown cost resources: "
                    f"{sorted(unknown)}"
                )


def _validate_serious_injuries_document(document: dict) -> None:
    tables = document.get("tables") or ()
    table_ids = {str(row.get("id") or "") for row in tables}
    result_ids = {
        str(row.get("id") or "")
        for table in tables
        for row in table.get("results") or ()
        if row.get("id")
    }
    for value in _reference_values(document, "table_id"):
        if value not in table_ids:
            raise ValueError(
                f"campaign catalogue serious-injuries: resolution references "
                f"unknown table {value!r}"
            )
    for value in _reference_values(document, "reroll_ids"):
        if value not in result_ids:
            raise ValueError(
                f"campaign catalogue serious-injuries: repeat_table references "
                f"unknown result {value!r}"
            )


def _validate_rarity_document(
    document: dict, campaign_stems: set[str]
) -> None:
    market = (document.get("rarity") or {}).get("market_catalog")
    if market is not None:
        stem = market[:-5] if market.endswith(".yaml") else market
        if stem not in campaign_stems:
            raise ValueError(
                f"campaign catalogue trading-and-rarity: rarity market_catalog "
                f"{market!r} does not name a campaign catalogue"
            )


# --------------------------------------------------------------------------- #
# Hireling catalogue (profile resolution for the shared loaders)
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=None)
def load_warband_groups(ruleset: str = "mordheim", root: Path | None = None) -> tuple[dict, ...]:
    """Load and validate ``registry/warband-groups.yaml`` (task 3)."""
    base = root or knowledge_root()
    path = base / WARBAND_GROUPS_CATALOGUE
    document = read_yaml(path)
    _check_header(
        document, path, ruleset,
        require_catalog=False, require_status=False,
    )
    groups = tuple(document.get("groups") or ())
    ids = [str(row.get("id") or "") for row in groups]
    if any(not group_id for group_id in ids):
        raise ValueError(f"warband groups registry has a group without id: {path}")
    if len(ids) != len(set(ids)):
        raise ValueError(f"warband groups registry has duplicate group ids: {path}")
    band_ids = _canonical_band_data(base, ruleset)[0]
    for group in groups:
        kind = group.get("kind")
        if kind not in GROUP_KINDS:
            raise ValueError(
                f"warband group {group.get('id')}: invalid kind {kind!r}"
            )
        for band_id in group.get("band_ids") or ():
            if band_id not in band_ids:
                raise ValueError(
                    f"warband group {group.get('id')}: unknown band {band_id!r}"
                )
    return groups


@lru_cache(maxsize=None)
def load_hirelings(
    ruleset: str = "mordheim", root: Path | None = None
) -> HirelingCatalogue:
    """Load and validate the hireling catalogue of ``catalog/hirelings``.

    Profile ids and declared rule ids must be unique across the catalogue and
    every ``rule_ids``/``special_skill_rule_ids`` reference and equipment
    ``item_id`` must resolve (against the declared rules and ``catalog/items``).
    """
    base = (root or knowledge_root()) / HIRELING_CATALOGUE_DIR
    item_ids = _canonical_item_ids(root or knowledge_root(), ruleset)
    profiles: list[dict] = []
    top_rules: list[dict] = []
    for path in sorted(base.glob("**/*.yaml")):
        document = read_yaml(path)
        _check_header(
            document, path, ruleset,
            require_catalog=False, require_status=False,
        )
        _assert_unique_ids(document, path.name)
        profiles.extend(document.get("profiles") or ())
        top_rules.extend(document.get("rules") or ())

    profile_ids = [str(row.get("id") or "") for row in profiles]
    if any(not profile_id for profile_id in profile_ids):
        raise ValueError("hireling catalogue has a profile without id")
    if len(profile_ids) != len(set(profile_ids)):
        duplicates = sorted({item for item in profile_ids if profile_ids.count(item) > 1})
        raise ValueError(
            "hireling catalogue has duplicate profile ids: "
            + ", ".join(duplicates[:8])
        )

    declared_rules: set[str] = set()
    for profile in profiles:
        declared_rules.update(
            str(rule.get("id") or "")
            for rule in profile.get("rules") or ()
            if isinstance(rule, dict) and rule.get("id")
        )
    declared_rules.update(
        str(rule.get("id") or "") for rule in top_rules if rule.get("id")
    )
    if not declared_rules:
        raise ValueError("hireling catalogue declares no rules")

    missing_rules = sorted({
        value
        for profile in profiles
        for key in ("rule_ids", "special_skill_rule_ids")
        for value in profile.get(key) or ()
    } - declared_rules)
    if missing_rules:
        raise ValueError(
            "hireling catalogue references undeclared rules: "
            + ", ".join(missing_rules[:8])
        )

    for path in sorted(base.glob("**/*.yaml")):
        document = read_yaml(path)
        for value in _reference_values(document, "item_id"):
            if value.startswith("$"):
                continue  # procedure context variable, not a canonical id
            if value not in item_ids:
                raise ValueError(
                    f"hireling catalogue {path.name}: unknown item reference "
                    f"{value!r}"
                )

    return HirelingCatalogue(tuple(profiles), tuple(top_rules))


# --------------------------------------------------------------------------- #
# Campaign catalogue loaders
# --------------------------------------------------------------------------- #


def _load_all_campaign_documents(ruleset: str, root: Path) -> dict[str, dict]:
    """Read + validate every ``catalog/campaign/*.yaml`` document.

    Headers and per-document id uniqueness are checked file by file (one bad
    file cannot silently drag the whole pass); the reference passes follow.
    """
    base = root / CAMPAIGN_CATALOGUE_DIR
    documents: dict[str, dict] = {}
    for path in sorted(base.glob("*.yaml")):
        document = read_yaml(path)
        _check_header(
            document, path, ruleset,
            require_catalog=True, require_status=True,
        )
        _assert_unique_ids(document, path.name)
        documents[path.stem] = document

    campaign_stems = set(documents)
    missing = _REQUIRED_CAMPAIGN_STEMS - campaign_stems
    if missing:
        raise ValueError(
            "campaign catalogue is missing required documents: "
            + ", ".join(sorted(missing))
        )

    # Canonical pools (all behind cached mordheim_knowledge loaders).
    band_ids, band_profiles, profile_ids = _canonical_band_data(root, ruleset)
    hireling_ids = set(load_hirelings(ruleset, root).profile_ids)
    group_ids = {str(row.get("id") or "") for row in load_warband_groups(ruleset, root)}
    item_ids = _canonical_item_ids(root, ruleset)
    condition_ids = _canonical_condition_ids(root)
    skill_ids = {str(row.get("id") or "") for row in load_skills(ruleset, root)}
    magic = documents["magic"]
    lore_ids = {
        str(row.get("id") or "")
        for row in magic.get("lores") or ()
        if row.get("id")
    } | {str(value) for value in magic.get("pending_lores") or ()}
    award_ids = {
        str(row.get("id") or "")
        for row in documents["experience-and-advances"].get("awards") or ()
    }

    # -- document-kind passes ---------------------------------------------
    sequence = _sequence_from_document(documents[POST_BATTLE_SEQUENCE_STEM])
    _validate_sequence_document(sequence, campaign_stems)
    _validate_scenarios_document(documents["scenarios"])
    _validate_magic_document(magic, lore_ids, band_profiles, hireling_ids)
    _validate_hired_swords_document(documents[HIRED_SWORDS_STEM], hireling_ids)
    _validate_serious_injuries_document(documents["serious-injuries"])
    _validate_rarity_document(documents["trading-and-rarity"], campaign_stems)

    # -- generic cross-document reference passes --------------------------
    scalar_pools = (
        ("item_id", item_ids, "item"),
        ("condition_id", condition_ids, "condition"),
        ("skill_id", skill_ids, "skill"),
        ("profile_id", profile_ids | hireling_ids, "profile"),
    )
    band_list_keys = ("band_id", "band_ids", "allow_band_ids", "forbid_band_ids", "band")
    group_list_keys = ("group_id", "groups", "allow_groups", "forbid_groups")

    for stem, document in documents.items():
        for key, pool, label in scalar_pools:
            for value in _reference_values(document, key):
                if value.startswith("$"):
                    continue  # procedure context variable, not a canonical id
                if value not in pool:
                    raise ValueError(
                        f"campaign catalogue {stem}: unknown {label} reference "
                        f"{value!r}"
                    )
        for key in band_list_keys:
            for value in _reference_values(document, key):
                if value not in band_ids:
                    raise ValueError(
                        f"campaign catalogue {stem}: unknown band reference "
                        f"{value!r}"
                    )
        for key in group_list_keys:
            for value in _reference_values(document, key):
                if value not in group_ids:
                    raise ValueError(
                        f"campaign catalogue {stem}: unknown warband group "
                        f"reference {value!r}"
                    )

    # -- scenario progression awards (cross document) ----------------------
    for scenario in documents["scenarios"].get("scenarios") or ():
        experience = (scenario.get("progression") or {}).get("experience") or ()
        for row in experience:
            ref = row.get("ref")
            if ref is not None and ref not in award_ids:
                raise ValueError(
                    f"campaign catalogue scenarios: {scenario.get('id')!r} "
                    f"references unknown experience award {ref!r}"
                )

    return documents


@lru_cache(maxsize=None)
def load_post_battle_sequence(
    ruleset: str = "mordheim", root: Path | None = None
) -> PostBattleSequence:
    """Load and validate the normative ``post-battle-sequence.yaml``."""
    base = (root or knowledge_root()) / CAMPAIGN_CATALOGUE_DIR
    path = base / f"{POST_BATTLE_SEQUENCE_STEM}.yaml"
    document = read_yaml(path)
    _check_header(
        document, path, ruleset,
        require_catalog=True, require_status=True,
    )
    _assert_unique_ids(document, path.name)
    sequence = _sequence_from_document(document)
    _validate_sequence_document(sequence, _document_stems(root or knowledge_root()))
    return sequence


@lru_cache(maxsize=None)
def load_campaign_catalog(
    ruleset: str = "mordheim", root: Path | None = None
) -> CampaignCatalog:
    """Load every campaign catalogue with the full validation contract."""
    documents = _load_all_campaign_documents(ruleset, root or knowledge_root())
    return CampaignCatalog(documents)
