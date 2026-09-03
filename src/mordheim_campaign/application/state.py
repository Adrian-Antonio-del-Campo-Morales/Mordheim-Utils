from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from mordheim_campaign.application.knowledge_port import KnowledgePort, WarbandProfile


@dataclass(slots=True)
class WarriorVM:
    id: str
    name: str
    profile_name: str
    kind: str
    stats: dict[str, int]
    equipment: list[str]
    skills: list[str]
    experience: int
    previous_experience: int | None = None
    quantity: int = 1
    condition: str | None = None
    condition_detail: str | None = None
    cost: int = 0
    equipment_cost: int = 0
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    skill_access: list[str] = field(default_factory=list)
    #: ID canónico del perfil KB (bandas/<collection>/<band>/profiles.yaml).
    profile_id: str = ""


@dataclass(slots=True)
class BattleVM:
    number: int
    date: str
    scenario: str
    opponent: str
    result: str
    gold_delta: int
    wyrdstone: int
    xp_delta: int
    casualties: int
    advances: int
    rating_before: int
    rating_after: int
    models_before: int
    models_after: int
    notes: str = ""
    opponent_rating: int | None = None


@dataclass(slots=True)
class InventoryItemVM:
    id: str
    name: str
    category: str
    owned: int
    equipped: int
    stash: int
    value: int = 0
    rarity: str | None = None


@dataclass(slots=True)
class WarbandStateVM:
    number: int
    date: str
    gold: int
    wyrdstone: int
    rating: int
    models: int
    max_models: int
    heroes: int
    henchmen: int
    experience: int
    label: str = ""

    @property
    def node_id(self) -> str:
        return f"state:{self.number}"


@dataclass(slots=True)
class PostBattleVM:
    battle_number: int
    complete: bool
    active_step: int = 0
    completed_steps: set[int] = field(default_factory=set)
    review_open: bool = False

    @property
    def node_id(self) -> str:
        return f"post:{self.battle_number}"


@dataclass(slots=True)
class CampaignVM:
    campaign_name: str
    warband_name: str
    warband_type: str
    started: str
    current_state_number: int = 0
    warriors: list[WarriorVM] = field(default_factory=list)
    battles: list[BattleVM] = field(default_factory=list)
    states: list[WarbandStateVM] = field(default_factory=list)
    post_battles: list[PostBattleVM] = field(default_factory=list)
    inventory: list[InventoryItemVM] = field(default_factory=list)
    stash_value: int = 0
    rare_finds: int = 0

    # Draft-only construction metadata. In the real application these values
    # are supplied by the selected warband rules rather than the GUI.
    is_draft: bool = False
    starting_gold: int = 500
    minimum_models: int = 3
    maximum_models: int = 15
    hero_limit: int = 5

    # Identidad KB de la banda: los casos de uso posteriores resuelven reglas
    # por estos IDs estables y nunca por el nombre visible.
    collection: str = ""
    band_id: str = ""
    ruleset: str = "mordheim"

    def state(self, number: int) -> WarbandStateVM:
        return next(item for item in self.states if item.number == number)

    def battle(self, number: int) -> BattleVM:
        return next(item for item in self.battles if item.number == number)

    def post_battle(self, number: int) -> PostBattleVM:
        return next(item for item in self.post_battles if item.battle_number == number)

    @property
    def current_state(self) -> WarbandStateVM:
        if not self.states:
            raise LookupError("A draft campaign does not have an immutable state yet.")
        return self.state(self.current_state_number)

    @property
    def pending_post_battle(self) -> PostBattleVM | None:
        return next((item for item in self.post_battles if not item.complete), None)

    @property
    def next_battle_number(self) -> int:
        return max((battle.number for battle in self.battles), default=0) + (0 if self.pending_post_battle else 1)

    @property
    def draft_model_count(self) -> int:
        return sum(w.quantity for w in self.warriors)

    @property
    def draft_hero_count(self) -> int:
        return sum(w.quantity for w in self.warriors if w.kind == "hero")

    @property
    def draft_henchman_count(self) -> int:
        return sum(w.quantity for w in self.warriors if w.kind == "henchman")

    @property
    def draft_experience(self) -> int:
        return sum(w.experience * w.quantity for w in self.warriors)

    @property
    def draft_recruitment_cost(self) -> int:
        return sum(w.cost * w.quantity for w in self.warriors)

    @property
    def draft_equipment_cost(self) -> int:
        return sum(w.equipment_cost * w.quantity for w in self.warriors)

    @property
    def draft_treasury(self) -> int:
        return self.starting_gold - self.draft_recruitment_cost - self.draft_equipment_cost

    @property
    def draft_rating(self) -> int:
        return self.draft_model_count * 5 + self.draft_experience

    @property
    def draft_is_legal(self) -> bool:
        return (
            self.draft_model_count >= self.minimum_models
            and self.draft_model_count <= self.maximum_models
            and 1 <= self.draft_hero_count <= self.hero_limit
            and self.draft_treasury >= 0
        )


@dataclass
class AppState:
    campaign: CampaignVM
    active_view: str = "campaign"
    campaign_mode: str = "timeline"
    selected_moment: str = "draft:0"
    state_section: str = "overview"
    battle_section: str = "overview"
    inventory_mode: str = "item"
    draft_warrior_tab: str = "hero"


STAT_KEYS = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")
POST_BATTLE_STEPS = (
    "Injuries",
    "Experience",
    "Exploration",
    "Sell Wyrdstone",
    "Veterans",
    "Rare Items & Dramatis",
    "Recruitment",
    "Equipment",
)

POST_BATTLE_GROUPS = (
    ("RECOVERY", (0, 1)),
    ("EXPLORATION & INCOME", (2, 3)),
    ("SEARCHES", (4, 5)),
    ("WARBAND", (6, 7)),
)


def _stats(values: tuple[int, ...]) -> dict[str, int]:
    return dict(zip(STAT_KEYS, values, strict=True))


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def _draft_campaign(port: KnowledgePort, option, *, campaign_name: str, warriors: list[WarriorVM]) -> CampaignVM:
    """Campaña en borrador con los límites canónicos de la banda seleccionada."""
    rules = port.roster_rules(option.collection, option.band_id)
    return CampaignVM(
        campaign_name=campaign_name,
        warband_name=f"My {option.name} Warband",
        warband_type=option.name,
        started="Draft",
        warriors=warriors,
        is_draft=True,
        starting_gold=rules.starting_gold,
        minimum_models=rules.minimum_models,
        maximum_models=rules.maximum_models,
        hero_limit=rules.hero_limit or 5,
        collection=option.collection,
        band_id=option.band_id,
    )


def _starter_warriors(port: KnowledgePort, option) -> list[WarriorVM]:
    """Borrador inicial legal mínimo derivado del roster canónico.

    Arranca con los miembros obligatorios (mínimos del roster) y completa hasta
    alcanzar el mínimo de modelos con los secuaces más baratos, sin exceder el
    tesoro inicial.
    """
    profiles = {p.profile_id: p for p in port.profiles(option.collection, option.band_id)}
    rules = port.roster_rules(option.collection, option.band_id)
    rows: list[WarriorVM] = []

    def add(profile: WarbandProfile, quantity: int, *, row_id: str) -> None:
        if quantity <= 0:
            return
        rows.append(warrior_vm(profile, quantity=quantity, row_id=row_id))

    required = [profile for profile in profiles.values() if profile.required]
    occurrences: dict[str, int] = {}
    for profile in required:
        occurrences[profile.profile_id] = occurrences.get(profile.profile_id, 0) + 1
        add(profile, profile.member_minimum, row_id=f"{profile.profile_id}#{occurrences[profile.profile_id]}")

    def model_count() -> int:
        return sum(row.quantity for row in rows)

    fill_candidates = [
        profile for profile in profiles.values()
        if profile.kind == "henchman" and profile.member_maximum != 0 and not profile.random_characteristics
    ]
    for profile in fill_candidates:
        if model_count() >= rules.minimum_models:
            break
        needed = rules.minimum_models - model_count()
        group_cap = profile.group_maximum
        per_row_cap = group_cap if group_cap is not None else (profile.member_maximum if profile.member_maximum is not None else needed)
        quantity = _clamp(needed, 1, per_row_cap)
        occurrences[profile.profile_id] = occurrences.get(profile.profile_id, 0) + 1
        add(profile, quantity, row_id=f"{profile.profile_id}#{occurrences[profile.profile_id]}")
    # Bandas que declaran todos sus héroes opcionales: el borrador necesita al
    # menos un héroe, así que se añade el héroe legal más barato disponible.
    if not any(row.kind == "hero" for row in rows):
        hero_candidates = [
            profile for profile in profiles.values()
            if profile.kind == "hero" and not profile.random_characteristics
            and profile.member_maximum not in (None, 0) and profile.member_maximum > 0
        ]
        for profile in sorted(hero_candidates, key=lambda profile: (profile.cost, profile.name)):
            if profile.cost > rules.starting_gold - sum(row.cost * row.quantity for row in rows):
                continue
            occurrences[profile.profile_id] = occurrences.get(profile.profile_id, 0) + 1
            add(profile, 1, row_id=f"{profile.profile_id}#{occurrences[profile.profile_id]}")
            break
    return rows


def make_draft_state(
    port: KnowledgePort,
    band_id: str,
    *,
    collection: str | None = None,
    campaign_name: str = "New Mordheim Campaign",
) -> AppState:
    """Estado de borrador nuevo: identidad, límites y roster inicial canónicos."""
    package = port.find_package(band_id, collection)
    option = port.warband(package.collection, band_id)
    campaign = _draft_campaign(port, option, campaign_name=campaign_name, warriors=_starter_warriors(port, option))
    return AppState(campaign=campaign, selected_moment="draft:0", draft_warrior_tab="hero")


def make_example_state(port: KnowledgePort) -> AppState:
    """Ejemplo navegable del prototipo construido sobre perfiles canónicos.

    La composición (perfiles, estadísticas, costes, acceso y reglas inherentes)
    proviene de la KB. Los números de batallas/estados posteriores son narrativa
    de ejemplo: ese estado mutable pertenece al modelo de campaña, no a la KB.
    """
    sisters = port.find_package("sisters-of-sigmar")
    option = port.warband(sisters.collection, str(sisters.band["id"]))

    def hero(profile_id: str, name: str, *, experience: int, previous: int | None = None,
             equipment: list[str] | None = None, extra_skills: list[str] | None = None,
             condition: str | None = None, condition_detail: str | None = None,
             modifiers: dict[str, int] | None = None, row_id: str | None = None) -> WarriorVM:
        profile = port.profile(option.collection, option.band_id, profile_id)
        return warrior_vm(
            profile, row_id=row_id or f"{profile_id}:1", name=name, experience=experience,
            previous_experience=previous, equipment=[port.item_name(item) or item for item in equipment or []],
            extra_skills=extra_skills or [], condition=condition, condition_detail=condition_detail,
            stat_modifiers=modifiers or {},
        )

    def group(profile_id: str, *, quantity: int, experience: int, equipment: list[str], row_id: str) -> WarriorVM:
        profile = port.profile(option.collection, option.band_id, profile_id)
        return warrior_vm(
            profile, row_id=row_id, quantity=quantity, experience=experience,
            equipment=[port.item_name(item) or item for item in equipment],
        )

    warriors = [
        hero("sigmarite-matriarch", "Mother Superior", row_id="matriarch", experience=23, previous=20,
             equipment=["sigmarite_hammer", "light_armour"],
             extra_skills=["Strike to Injure", "Expert Swordsman"]),
        hero("sister-superior", "Sister Superior Anna", row_id="anna", experience=19, previous=17,
             equipment=["sigmarite_hammer", "shield", "light_armour"],
             extra_skills=["Step Aside", "Mighty Blow"]),
        hero("sister-superior", "Sister Superior Marta", row_id="marta", experience=13, previous=12,
             equipment=["dagger", "buckler", "light_armour"],
             extra_skills=["Dodge"], condition="Injured", condition_detail="Leg Wound (M -1)",
             modifiers={"M": -1}),
        hero("augur", "Sister Veriet", row_id="veriet", experience=10, previous=8,
             equipment=["hammer", "dagger"], extra_skills=["Dodge", "Faith"]),
        group("sigmarite-sister", row_id="sisters", quantity=2, experience=6, equipment=["hammer", "buckler"]),
        group("novices", row_id="novices", quantity=2, experience=4, equipment=["hammer", "dagger"]),
    ]

    battles = [
        BattleVM(1, "14 Jul 2026", "Skirmish", "Cultists", "Victory", 24, 1, 3, 0, 0, 95, 114, 6, 7, opponent_rating=103),
        BattleVM(2, "17 Jul 2026", "Search & Destroy", "Mercenaries", "Victory", 28, 1, 4, 0, 1, 114, 128, 7, 8, opponent_rating=121),
        BattleVM(3, "24 Jul 2026", "Skirmish", "Undead", "Defeat", 35, 2, 4, 1, 1, 128, 141, 8, 8, opponent_rating=139),
        BattleVM(4, "31 Jul 2026", "Raid", "Cult of the Possessed", "Victory", 30, 3, 5, 1, 1, 141, 151, 8, 9, opponent_rating=148),
        BattleVM(5, "7 Aug 2026", "Hidden Treasure", "Undead", "Victory", 42, 2, 6, 0, 1, 151, 161, 9, 9, opponent_rating=167),
        BattleVM(6, "14 Aug 2026", "Skirmish", "Reiklanders", "Defeat", 55, 4, 9, 2, 1, 161, 174, 9, 9, opponent_rating=176),
        BattleVM(7, "21 Aug 2026", "Skirmish", "Possessed", "Victory", 38, 3, 7, 1, 2, 174, 183, 9, 8, "A costly win near the ruined chapel.", 192),
        BattleVM(8, "28 Aug 2026", "Defend the Find", "Beastmen Raiders", "Victory", 0, 0, 0, 1, 0, 183, 183, 8, 8, "Post-battle still unresolved.", 201),
    ]

    states = [
        WarbandStateVM(0, "14 Jul 2026", 430, 0, 95, 6, 15, 3, 3, 65, "Initial Warband"),
        WarbandStateVM(1, "14 Jul 2026", 92, 1, 114, 7, 15, 3, 4, 79),
        WarbandStateVM(2, "17 Jul 2026", 71, 2, 128, 8, 15, 3, 5, 88),
        WarbandStateVM(3, "24 Jul 2026", 54, 2, 141, 8, 15, 3, 5, 101),
        WarbandStateVM(4, "31 Jul 2026", 49, 3, 151, 9, 15, 4, 5, 106),
        WarbandStateVM(5, "7 Aug 2026", 36, 3, 161, 9, 15, 4, 5, 116),
        WarbandStateVM(6, "14 Aug 2026", 34, 1, 174, 9, 15, 4, 5, 129),
        WarbandStateVM(7, "21 Aug 2026", 72, 4, 183, 8, 15, 4, 4, 143, "Current Warband"),
    ]

    post_battles = [
        *[PostBattleVM(number, True, 7, set(range(8)), False) for number in range(1, 8)],
        PostBattleVM(8, False, 4, set(range(4)), False),
    ]

    inventory = [
        InventoryItemVM("sigmarite_hammer", "Sigmarite Hammer", "Weapon", 2, 2, 0, 15, "Rare"),
        InventoryItemVM("hammer", "Hammer", "Weapon", 5, 5, 0, 3),
        InventoryItemVM("dagger", "Dagger", "Weapon", 4, 3, 1, 2),
        InventoryItemVM("buckler", "Buckler", "Armour", 3, 3, 0, 5),
        InventoryItemVM("light_armour", "Light Armour", "Armour", 3, 3, 0, 20),
        InventoryItemVM("shield", "Shield", "Armour", 1, 1, 0, 5),
        InventoryItemVM("lucky_charm", "Lucky Charm", "Misc", 1, 0, 1, 10),
        InventoryItemVM("healing_herbs", "Healing Herbs", "Consumable", 3, 0, 3, 8),
        InventoryItemVM("holy_relic", "Holy Relic", "Misc", 1, 0, 1, 15, "Rare"),
    ]

    campaign = CampaignVM(
        campaign_name="The Sisters of Morr",
        warband_name="My Sisters of Sigmar Warband",
        warband_type=option.name,
        started="14 Jul 2026",
        current_state_number=7,
        warriors=warriors,
        battles=battles,
        states=states,
        post_battles=post_battles,
        inventory=inventory,
        stash_value=54,
        rare_finds=2,
        collection=option.collection,
        band_id=option.band_id,
    )
    return AppState(campaign=campaign, selected_moment="state:7")


def warrior_vm(
    profile: WarbandProfile,
    *,
    row_id: str | None = None,
    name: str | None = None,
    quantity: int = 1,
    experience: int | None = None,
    previous_experience: int | None = None,
    equipment: list[str] | None = None,
    extra_skills: list[str] | None = None,
    condition: str | None = None,
    condition_detail: str | None = None,
    stat_modifiers: dict[str, int] | None = None,
) -> WarriorVM:
    """Convierte un perfil canónico en el view-model de guerrero usado por la GUI.

    ``equipment`` recibe ya nombres canónicos de catálogo (no IDs); ``skills``
    combina las reglas inherentes del perfil con habilidades ganadas en juego.
    """
    return WarriorVM(
        id=row_id or f"{profile.profile_id}#1",
        name=name or profile.name,
        profile_name=profile.name,
        kind=profile.kind,
        stats={**profile.characteristics, **(stat_modifiers or {})},
        equipment=list(profile.fixed_equipment if equipment is None else equipment),
        skills=list(profile.inherent_rules) + list(extra_skills or []),
        experience=profile.experience if experience is None else experience,
        previous_experience=previous_experience,
        quantity=quantity,
        condition=condition,
        condition_detail=condition_detail,
        cost=profile.cost,
        equipment_cost=0,
        stat_modifiers=dict(stat_modifiers or {}),
        skill_access=list(profile.skill_tables),
        profile_id=profile.profile_id,
    )
