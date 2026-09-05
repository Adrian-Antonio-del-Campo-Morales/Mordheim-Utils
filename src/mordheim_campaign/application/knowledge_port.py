"""knowledge_port: canonical KB reads for the campaign manager.

The authorised path is ``KB YAML → knowledge.loader → application → ui``
(see ``sources/knowledge/catalog/campaign/README-HOWTO.md``). This module is the
``application`` boundary of that path: it consumes exclusively the loaders in
``mordheim_knowledge`` and exposes flat DTOs for warbands, profiles, warband
limits and available equipment. Tk widgets must not import ``mordheim_knowledge``
or read YAML directly; they must depend on these DTOs and controller actions.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from mordheim_knowledge.campaign import CampaignCatalog
from mordheim_knowledge.campaign import HirelingCatalogue
from mordheim_knowledge.campaign import PostBattleSequence
from mordheim_knowledge.campaign import load_campaign_catalog
from mordheim_knowledge.campaign import load_hireling_traits
from mordheim_knowledge.campaign import load_hirelings
from mordheim_knowledge.campaign import load_post_battle_sequence
from mordheim_knowledge.campaign import load_warband_groups
from mordheim_knowledge.loader import BandPackage
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_items
from mordheim_knowledge.loader import load_racial_maximums
from mordheim_knowledge.loader import load_skills
from mordheim_knowledge.i18n import display_name as kb_display_name
from mordheim_knowledge.i18n import resolved_name as kb_resolved_name


CHARACTERISTIC_KEYS = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")

#: Profile types purchased in groups, like henchmen.
GROUP_PROFILE_TYPES = frozenset({"henchman", "animal"})

#: Human labels for the canonical skill tables of a profile.
SKILL_TABLE_LABELS = {
    "combat": "Combat",
    "academic": "Academic",
    "strength": "Strength",
    "speed": "Speed",
    "shooting": "Shooting",
    "special": "Special",
}


class KnowledgePortError(ValueError):
    """A warband/profile identifier does not resolve in the loaded KB."""


_DICE_EXPRESSION = re.compile(r"(\d*)D(\d+)(?:\+(\d+))?", re.IGNORECASE)


def _characteristics(row: dict) -> tuple[dict[str, int], bool]:
    """Numeric characteristics; detects random or composite profiles.

    Dice values (e.g. ``2D6``) or absent values (profiles built from components)
    are not individually deterministic: they are marked as random and, as the
    compiler does, projected to their minimum value so they can be displayed.
    """
    raw = row.get("characteristics") or {}
    values: dict[str, int] = {}
    random_characteristics = False
    for key in CHARACTERISTIC_KEYS:
        value = raw.get(key)
        if isinstance(value, int):
            values[key] = value
            continue
        match = _DICE_EXPRESSION.fullmatch(str(value)) if value is not None else None
        random_characteristics = True
        values[key] = int(match.group(1) or 1) + int(match.group(3) or 0) if match else 0
    return values, random_characteristics


def _title(value: str) -> str:
    return " ".join(part.capitalize() if part else part for part in value.split())


def _category_labels(skill_access: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(SKILL_TABLE_LABELS.get(table, table.title()) for table in skill_access)


@dataclass(frozen=True, slots=True)
class WarbandOption:
    """A warband selectable to start a campaign."""

    collection: str
    band_id: str
    name: str
    source_label: str
    categories: tuple[str, ...]
    grade: str
    publication: str
    minimum_models: int
    maximum_models: int
    starting_gold: int

    @property
    def label(self) -> str:
        return self.name if self.collection == "mordheim" else f"{self.name} · {self.source_label}"


@dataclass(frozen=True, slots=True)
class WarbandProfile:
    """A canonical warband roster profile, ready to show and add."""

    collection: str
    band_id: str
    profile_id: str
    name: str
    kind: str  # "hero" | "henchman"
    cost: int
    experience: int
    characteristics: dict[str, int]
    random_characteristics: bool
    skill_access: tuple[str, ...]
    skill_tables: tuple[str, ...]
    inherent_rules: tuple[str, ...]
    starting_skills: tuple[str, ...]
    required: bool
    member_minimum: int
    member_maximum: int | None  # None = no declared cap (real cap: max models)
    group_minimum: int
    group_maximum: int | None
    equipment_list_ids: tuple[str, ...]
    fixed_equipment: tuple[str, ...]

    @property
    def is_hero(self) -> bool:
        return self.kind == "hero"


@dataclass(frozen=True, slots=True)
class EquipmentOffer:
    """An item from a warband's canonical equipment access, with creation cost."""

    list_id: str
    list_name: str
    item_id: str
    name: str
    cost: int | None
    notes: str

    @property
    def cost_label(self) -> str:
        return "—" if self.cost is None else f"{self.cost} gc"


@dataclass(frozen=True, slots=True)
class RosterRules:
    """Canonical composition and limits of a warband."""

    minimum_models: int
    maximum_models: int
    starting_gold: int
    hero_limit: int | None

    @property
    def hero_limit_label(self) -> str:
        return "—" if self.hero_limit is None else str(self.hero_limit)


class KnowledgePort:
    """Canonical read model of warbands/profiles for the Campaign Manager.

    It does not decide rules or hold campaign state: it maps the documents
    validated by ``mordheim_knowledge`` to read-only DTOs. Loaders are cached,
    so the package index is built only once.
    """

    def __init__(self, ruleset: str = "mordheim") -> None:
        self.ruleset = ruleset
        self._collections = tuple(
            row for row in load_collections()
            if ruleset in set(row.get("rulesets") or ())
        )
        self._packages: dict[tuple[str, str], BandPackage] = {}
        for collection in self._collections:
            for package in load_bands(str(collection["id"])):
                if package.ruleset == ruleset:
                    self._packages[(package.collection, str(package.band["id"]))] = package
        self._items = {
            str(row["id"]): row
            for row in load_items(ruleset)
        }
        self._skills = {
            str(row["id"]): row
            for row in load_skills(ruleset)
        }
        self._profiles_cache: dict[tuple[str, str], tuple[WarbandProfile, ...]] = {}
        self._hireling_traits_cache: dict[str, frozenset[str]] | None = None

    # ------------------------------------------------------------------ bands

    def collections(self) -> tuple[tuple[str, str], ...]:
        """Active collections for this ruleset: (id, name)."""
        return tuple((str(row["id"]), kb_resolved_name(row, row["id"])) for row in self._collections)

    def options(self, collection: str | None = None) -> tuple[WarbandOption, ...]:
        """All selectable warbands, ordered by name."""
        wanted = {collection} if collection else None
        options = []
        for (package_collection, band_id), package in self._packages.items():
            if wanted is not None and package_collection not in wanted:
                continue
            band = package.band
            roster = band.get("roster") or {}
            source_label = dict(self.collections()).get(package_collection, package_collection)
            options.append(WarbandOption(
                collection=package_collection,
                band_id=band_id,
                name=kb_resolved_name(band, band_id),
                source_label=str(source_label),
                categories=tuple(str(value) for value in band.get("categories") or ()),
                grade=str(band.get("grade") or ""),
                publication=str(band.get("publication") or ""),
                minimum_models=int(roster.get("minimum_models") or 0),
                maximum_models=int(roster.get("maximum_models") or 0),
                starting_gold=int(roster.get("starting_gold") or 0),
            ))
        return tuple(sorted(options, key=lambda option: option.name.casefold()))

    def warband(self, collection: str, band_id: str) -> WarbandOption:
        try:
            return next(option for option in self.options(collection) if option.band_id == band_id)
        except StopIteration as exc:
            raise KnowledgePortError(f"Unknown warband: {collection}/{band_id}") from exc

    def find_package(self, band_id: str, collection: str | None = None) -> BandPackage:
        """Locate a warband package by its canonical ``band_id``."""
        if collection is not None and (collection, band_id) in self._packages:
            return self._packages[(collection, band_id)]
        matches = [package for (package_collection, _), package in self._packages.items() if package.band["id"] == band_id]
        if not matches:
            raise KnowledgePortError(f"Unknown warband: {band_id}")
        return matches[0]

    # ---------------------------------------------------------------- profiles

    def roster_rules(self, collection: str, band_id: str) -> RosterRules:
        """Warband composition limits: models, starting gold and heroes."""
        package = self._packages[(collection, band_id)]
        roster = package.band.get("roster") or {}
        hero_caps = []
        for member in roster.get("members") or ():
            profile = next(row for row in package.profiles if str(row["id"]) == str(member.get("profile_id")))
            if str(profile.get("type")) != "hero":
                continue
            maximum = member.get("maximum")
            if maximum is not None:
                hero_caps.append(int(maximum))
        return RosterRules(
            minimum_models=int(roster.get("minimum_models") or 0),
            maximum_models=int(roster.get("maximum_models") or 0),
            starting_gold=int(roster.get("starting_gold") or 0),
            hero_limit=sum(hero_caps) if hero_caps else None,
        )

    def profiles(self, collection: str, band_id: str, *, kind: str | None = None) -> tuple[WarbandProfile, ...]:
        """Roster profiles in editorial order, filterable by kind."""
        key = (collection, band_id)
        if key not in self._profiles_cache:
            self._profiles_cache[key] = self._build_profiles(collection, band_id)
        profiles = self._profiles_cache[key]
        if kind is not None:
            profiles = tuple(profile for profile in profiles if profile.kind == kind)
        return profiles

    def profile(self, collection: str, band_id: str, profile_id: str) -> WarbandProfile:
        try:
            return next(profile for profile in self.profiles(collection, band_id) if profile.profile_id == profile_id)
        except StopIteration as exc:
            raise KnowledgePortError(f"Unknown profile: {collection}/{band_id}/{profile_id}") from exc

    def _build_profiles(self, collection: str, band_id: str) -> tuple[WarbandProfile, ...]:
        package = self._packages[(collection, band_id)]
        rows = {str(row["id"]): row for row in package.profiles}
        roster = package.band.get("roster") or {}
        result = []
        for member in roster.get("members") or ():
            profile = rows.get(str(member.get("profile_id")))
            if profile is None:
                continue
            profile_type = str(profile.get("type") or "")
            if profile_type not in GROUP_PROFILE_TYPES and profile_type != "hero":
                continue
            kind = "henchman" if profile_type in GROUP_PROFILE_TYPES else "hero"
            inherent = self._inherent_rules(package, str(profile["id"]))
            starting = tuple(
                name for skill_id, name in (
                    (str(value), kb_display_name(self._skills.get(str(value))))
                    for value in (profile.get("combat_traits") or {}).get("starting_skills") or ()
                )
                if name and not any(existing == name for existing in inherent)
            )
            group_size = member.get("group_size") or {}
            values, random_characteristics = _characteristics(profile)
            result.append(WarbandProfile(
                collection=collection,
                band_id=band_id,
                profile_id=str(profile["id"]),
                name=_title(kb_resolved_name(profile, profile["id"])),
                kind=kind,
                cost=int(profile.get("cost") or 0),
                experience=int(profile.get("experience") or 0),
                characteristics=values,
                random_characteristics=random_characteristics,
                skill_access=tuple(str(value) for value in profile.get("skill_access") or ()),
                skill_tables=_category_labels(tuple(str(value) for value in profile.get("skill_access") or ())),
                inherent_rules=inherent,
                starting_skills=starting,
                required=int(member.get("minimum") or 0) > 0,
                member_minimum=int(member.get("minimum") or 0),
                member_maximum=member.get("maximum"),
                group_minimum=int(group_size.get("minimum") or 1),
                group_maximum=group_size.get("maximum"),
                equipment_list_ids=tuple(str(value) for value in profile.get("equipment_lists") or ()),
                fixed_equipment=tuple(
                    kb_resolved_name(self._items.get(str(value)), value)
                    for value in profile.get("fixed_equipment") or ()
                ),
            ))
        return tuple(result)

    @staticmethod
    def _inherent_rules(package: BandPackage, profile_id: str) -> tuple[str, ...]:
        """Fixed profile rules (grant ``profile``) declared by the warband."""
        names = []
        for rule in package.special_rules:
            applies = rule.get("applies_to") or {}
            if profile_id not in set(applies.get("profile_ids") or ()):
                continue
            if (rule.get("runtime") or {}).get("grant") != "profile":
                continue
            name = str(rule.get("name") or rule.get("id") or "")  # editorial rules keep their canonical name
            if name and not any(existing == name for existing in names):
                names.append(name)
        return tuple(names)

    # -------------------------------------------------------------- equipment

    def equipment(self, collection: str, band_id: str) -> tuple[EquipmentOffer, ...]:
        """Creation equipment offers: canonical warband access + catalogue names."""
        package = self._packages[(collection, band_id)]
        offers = []
        for equipment_list in package.equipment_lists:
            list_name = str(equipment_list.get("name") or equipment_list.get("id") or "")
            for item in equipment_list.get("items") or ():
                item_id = str(item.get("item_id") or "")
                item_row = self._items.get(item_id)
                name = kb_display_name(item_row, item_id) if item_row else item_id
                cost = item.get("cost")
                offers.append(EquipmentOffer(
                    list_id=str(equipment_list["id"]),
                    list_name=list_name,
                    item_id=item_id,
                    name=name,
                    cost=int(cost) if isinstance(cost, int) else cost if isinstance(cost, float) else None,
                    notes=str(item.get("notes") or ""),
                ))
        return tuple(sorted(offers, key=lambda offer: (offer.name.casefold(), offer.item_id)))

    def item_name(self, item_id: str) -> str | None:
        """Display name of one item (KB locale policy), ``None`` if unknown."""
        row = self._items.get(item_id)
        return kb_display_name(row, item_id) or None if row else None

    def price_override(self, collection: str, band_id: str, item_id: str) -> int | None:
        """Flat Trading Post price exception a warband pays for an item.

        The warband equipment lists keep their printed ``cost`` as historical
        evidence; the Trading Post is the market price unless the warband's own
        source confirms an exception, which is declared as ``price_override``
        on the equipment-access row (see the campaign catalogue README).
        Returns the overriding amount in gc, or ``None`` when the Trading Post
        prevails.
        """
        package = self._packages.get((collection, band_id))
        if package is None:
            return None
        for equipment_list in package.equipment_lists:
            for item in equipment_list.get("items") or ():
                if str(item.get("item_id") or "") != item_id:
                    continue
                override = item.get("price_override")
                if isinstance(override, dict):
                    base = override.get("base_gc")
                    return int(base) if isinstance(base, (int, float)) else None
                if isinstance(override, (int, float)):
                    return int(override)
        return None

    def items_for_profile(self, profile: WarbandProfile) -> tuple[EquipmentOffer, ...]:
        """Offers applicable to a concrete profile (its equipment lists)."""
        allowed = set(profile.equipment_list_ids)
        return tuple(offer for offer in self.equipment(profile.collection, profile.band_id) if offer.list_id in allowed)

    # -------------------------------------------------------------- campaign

    def post_battle_sequence(self) -> PostBattleSequence:
        """Normative KB post-battle resolution order (validated at load).

        The catalogue the step resolves can be read from the returned
        ``CampaignCatalog`` via ``campaign_catalog().catalogue(step.resolves)``.
        """
        return load_post_battle_sequence(self.ruleset)

    def campaign_catalog(self) -> CampaignCatalog:
        """Every published campaign document, validated at load time.

        Read model for post-battle tables (trading post, injuries, advances,
        exploration, scenarios, magic, mutations, hiring); keyed by catalogue
        file name stem. Never decide rules here: this is the KB read boundary.
        """
        return load_campaign_catalog(self.ruleset)

    def hireling_catalogue(self) -> HirelingCatalogue:
        """Hireling profiles and rules of ``catalog/hirelings`` (validated).

        Profiles referenced by ``campaign.hireling.*`` hiring entries resolve
        against this catalogue; ``profile_ids`` is the authoritative pool.
        """
        return load_hirelings(self.ruleset)

    def warband_groups(self) -> tuple[dict, ...]:
        """Reusable ``warband-group.*`` band sets from the registry (validated)."""
        return load_warband_groups(self.ruleset)

    def hireling_traits(self) -> dict[str, frozenset[str]]:
        """Intrinsic traits of hireling profiles (``catalog/hirelings/traits.yaml``),
        keyed by profile id; validated to resolve against the hireling catalogue.

        Read model for the roster-dependent eligibility rules (race,
        fear-causing, evil, spellcaster, priest), so the application does not
        keep its own curated trait sets."""
        if self._hireling_traits_cache is None:
            self._hireling_traits_cache = {
                str(row["profile_id"]): frozenset(str(trait) for trait in row.get("traits") or ())
                for row in load_hireling_traits(self.ruleset)
            }
        return self._hireling_traits_cache

    def scenario_options(self) -> tuple[tuple[str, str, str], ...]:
        """Playable scenarios: (id, name, player_mode) from ``scenarios.yaml``."""
        document = self.campaign_catalog().catalogue("scenarios")
        return tuple(
            (str(row.get("id") or ""), str(row.get("name") or ""), str(row.get("player_mode") or ""))
            for row in document.get("scenarios") or ()
            if row.get("id")
        )

    def skills(self) -> tuple[dict, ...]:
        """Canonical skill catalogue rows (``catalog/skills/*.yaml``)."""
        return tuple(self._skills.values())

    def skill_by_name(self, name: str) -> dict | None:
        """One skill row by its canonical display name (``Acrobat``)."""
        wanted = name.strip().casefold()
        return next((row for row in self._skills.values() if str(row.get("name")).casefold() == wanted), None)

    def skill_table_label(self, skill_id_or_row) -> str:
        """Human table label (``Combat``) of one skill row or id."""
        row = skill_id_or_row if isinstance(skill_id_or_row, dict) else self._skills.get(str(skill_id_or_row), {})
        return SKILL_TABLE_LABELS.get(str(row.get("category") or ""), str(row.get("category") or "").title())

    def wizard_lore(self, profile_id: str, band_id: str) -> str | None:
        """Lore id assigned to a wizard profile (``magic.yaml``), else ``None``.

        A profile is a wizard exactly when the KB assigns it a lore; the
        band must match for band profiles (hirelings have ``band: null``).
        """
        magic = self.campaign_catalog().catalogue("magic")
        for row in magic.get("lore_assignments", {}).get("rows") or ():
            if str(row.get("profile_id") or "") != profile_id:
                continue
            row_band = row.get("band")
            if row_band is None or str(row_band) == band_id:
                return str(row.get("lore") or "") or None
        return None

    def lore_spells(self, lore_id: str) -> tuple[dict, ...]:
        """Spell rows of one lore (``magic.yaml`` ``lores[].spells``)."""
        magic = self.campaign_catalog().catalogue("magic")
        for lore in magic.get("lores") or ():
            if str(lore.get("id") or "") == lore_id:
                return tuple(lore.get("spells") or ())
        return ()

    def racial_maximums(self) -> tuple[dict, ...]:
        """Racial characteristic maximums of ``catalog/rules/racial-maximums.yaml``."""
        return load_racial_maximums(self.ruleset)
