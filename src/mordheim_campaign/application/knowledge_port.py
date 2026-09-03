"""knowledge_port: lectura KB canónica para el gestor de campaña.

El recorrido autorizado es ``YAML de la KB → knowledge.loader → application → ui``
(véase ``sources/knowledge/catalog/campaign/README-HOWTO.md``). Este módulo es la
frontera ``application`` de ese recorrido: consume exclusivamente los cargadores de
``mordheim_knowledge`` y expone DTOs planos de bandas, perfiles, límites de banda y
equipo disponible. Los widgets Tk no deben importar ``mordheim_knowledge`` ni leer
YAML directamente; deben depender de estos DTOs y de las acciones del controlador.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from mordheim_knowledge.loader import BandPackage
from mordheim_knowledge.loader import load_bands
from mordheim_knowledge.loader import load_collections
from mordheim_knowledge.loader import load_items
from mordheim_knowledge.loader import load_skills


CHARACTERISTIC_KEYS = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")

#: Tipos de perfil que se compran en grupos como si fueran secuaces.
GROUP_PROFILE_TYPES = frozenset({"henchman", "animal"})

#: Etiquetas humanas de las tablas de habilidades canónicas de un perfil.
SKILL_TABLE_LABELS = {
    "combat": "Combat",
    "academic": "Academic",
    "strength": "Strength",
    "speed": "Speed",
    "shooting": "Shooting",
    "special": "Special",
}


class KnowledgePortError(ValueError):
    """Un identificador de banda/perfil no se resuelve en la KB cargada."""


_DICE_EXPRESSION = re.compile(r"(\d*)D(\d+)(?:\+(\d+))?", re.IGNORECASE)


def _characteristics(row: dict) -> tuple[dict[str, int], bool]:
    """Características numéricas; detecta perfiles aleatorios o compuestos.

    Los valores en dados (p. ej. ``2D6``) o ausentes (perfiles con componentes)
    no son individualmente deterministas: se marcan como aleatorios y, como hace
    el compilador, se proyectan a su valor mínimo para poder mostrarlos.
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
    """Una banda seleccionable para crear una campaña."""

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
    """Un perfil canónico del roster de una banda, listo para mostrar y añadir."""

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
    member_maximum: int | None  # None = sin tope declarado (tope real: modelos máx.)
    group_minimum: int
    group_maximum: int | None
    equipment_list_ids: tuple[str, ...]
    fixed_equipment: tuple[str, ...]

    @property
    def is_hero(self) -> bool:
        return self.kind == "hero"


@dataclass(frozen=True, slots=True)
class EquipmentOffer:
    """Un objeto del acceso de equipo canónico de una banda, con su coste de creación."""

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
    """Composición y límites canónicos de una banda."""

    minimum_models: int
    maximum_models: int
    starting_gold: int
    hero_limit: int | None

    @property
    def hero_limit_label(self) -> str:
        return "—" if self.hero_limit is None else str(self.hero_limit)


class KnowledgePort:
    """Read model canónico de bandas/perfiles para el Campaign Manager.

    No decide reglas ni contiene estado de campaña: mapea los documentos
    validados por ``mordheim_knowledge`` a DTOs de solo lectura. Los cargadores
    están cacheados, de modo que el índice de paquetes se construye una vez.
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

    # ------------------------------------------------------------------ bands

    def collections(self) -> tuple[tuple[str, str], ...]:
        """Colecciones activas para este ruleset: (id, nombre)."""
        return tuple((str(row["id"]), str(row.get("name") or row["id"])) for row in self._collections)

    def options(self, collection: str | None = None) -> tuple[WarbandOption, ...]:
        """Todas las bandas seleccionables, ordenadas por nombre."""
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
                name=str(band.get("name") or band_id),
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
        """Localiza un paquete de banda por su ``band_id`` canónico."""
        if collection is not None and (collection, band_id) in self._packages:
            return self._packages[(collection, band_id)]
        matches = [package for (package_collection, _), package in self._packages.items() if package.band["id"] == band_id]
        if not matches:
            raise KnowledgePortError(f"Unknown warband: {band_id}")
        return matches[0]

    # ---------------------------------------------------------------- profiles

    def roster_rules(self, collection: str, band_id: str) -> RosterRules:
        """Límites de composición de la banda: modelos, oro inicial y héroes."""
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
        """Perfiles del roster en orden editorial, filtrables por tipo."""
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
                    (str(value), self._skills.get(str(value), {}).get("name"))
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
                name=_title(str(profile.get("name") or profile["id"])),
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
                    str(self._items.get(str(value), {}).get("name") or value)
                    for value in profile.get("fixed_equipment") or ()
                ),
            ))
        return tuple(result)

    @staticmethod
    def _inherent_rules(package: BandPackage, profile_id: str) -> tuple[str, ...]:
        """Reglas fijas del perfil (grant ``profile``) declaradas por la banda."""
        names = []
        for rule in package.special_rules:
            applies = rule.get("applies_to") or {}
            if profile_id not in set(applies.get("profile_ids") or ()):
                continue
            if (rule.get("runtime") or {}).get("grant") != "profile":
                continue
            name = str(rule.get("name") or rule.get("id") or "")
            if name and not any(existing == name for existing in names):
                names.append(name)
        return tuple(names)

    # -------------------------------------------------------------- equipment

    def equipment(self, collection: str, band_id: str) -> tuple[EquipmentOffer, ...]:
        """Ofertas de equipo de creación: acceso canónico de la banda + nombres de catálogo."""
        package = self._packages[(collection, band_id)]
        offers = []
        for equipment_list in package.equipment_lists:
            list_name = str(equipment_list.get("name") or equipment_list.get("id") or "")
            for item in equipment_list.get("items") or ():
                item_id = str(item.get("item_id") or "")
                item_row = self._items.get(item_id)
                name = str(item_row.get("name") or item_id) if item_row else item_id
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
        row = self._items.get(item_id)
        return str(row["name"]) if row else None

    def items_for_profile(self, profile: WarbandProfile) -> tuple[EquipmentOffer, ...]:
        """Ofertas aplicables a un perfil concreto (sus listas de equipo)."""
        allowed = set(profile.equipment_list_ids)
        return tuple(offer for offer in self.equipment(profile.collection, profile.band_id) if offer.list_id in allowed)
