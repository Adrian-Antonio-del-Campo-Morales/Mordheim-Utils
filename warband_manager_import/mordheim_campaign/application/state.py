from __future__ import annotations

from dataclasses import dataclass, field


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
    # will be supplied by the selected warband rules rather than the GUI.
    is_draft: bool = False
    starting_gold: int = 500
    minimum_models: int = 3
    maximum_models: int = 15
    hero_limit: int = 5

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


def _creation_warriors() -> list[WarriorVM]:
    return [
        WarriorVM(
            id="matriarch",
            name="Mother Superior",
            profile_name="Sigmarite Matriarch",
            kind="hero",
            stats=_stats((4, 4, 4, 3, 3, 1, 4, 1, 8)),
            equipment=[],
            skills=["Leader", "Prayers of Sigmar"],
            skill_access=["Combat", "Academic", "Strength", "Special"],
            experience=20,
            cost=70,
        ),
        WarriorVM(
            id="sister-group",
            name="Sigmarite Sisters",
            profile_name="Sigmarite Sister",
            kind="henchman",
            stats=_stats((4, 3, 3, 3, 3, 1, 3, 1, 7)),
            equipment=[],
            skills=[],
            experience=0,
            quantity=1,
            cost=25,
        ),
        WarriorVM(
            id="novices",
            name="Novices",
            profile_name="Novice",
            kind="henchman",
            stats=_stats((4, 2, 2, 3, 3, 1, 3, 1, 6)),
            equipment=[],
            skills=[],
            experience=0,
            quantity=4,
            cost=15,
        ),
    ]


def make_creation_demo_state(*, campaign_name: str = "The Sisters of Morr", warband_type: str = "Sisters of Sigmar", empty: bool = False) -> AppState:
    campaign = CampaignVM(
        campaign_name=campaign_name,
        warband_name="My Sisters of Sigmar Warband" if warband_type == "Sisters of Sigmar" else f"My {warband_type} Warband",
        warband_type=warband_type,
        started="Draft",
        warriors=[] if empty else _creation_warriors(),
        is_draft=True,
        starting_gold=500,
        minimum_models=3,
        maximum_models=15,
        hero_limit=5,
    )
    return AppState(campaign=campaign, selected_moment="draft:0", draft_warrior_tab="hero")


def make_demo_state() -> AppState:
    warriors = [
        WarriorVM(
            id="matriarch", name="Mother Superior", profile_name="Matriarch", kind="hero",
            stats=_stats((4, 4, 4, 3, 3, 1, 4, 1, 8)),
            equipment=["Sigmarite Warhammer", "Light Armour", "Hand Weapon", "Rosary"],
            skills=["Strike to Injure", "Expert Swordsman", "Leader", "Prayers of Sigmar"],
            skill_access=["Combat", "Academic", "Strength", "Special"],
            experience=23, cost=70,
        ),
        WarriorVM(
            id="anna", name="Sister Superior Anna", profile_name="Sister Superior", kind="hero",
            stats=_stats((4, 4, 3, 3, 3, 1, 4, 1, 8)),
            equipment=["Sigmarite Hammer", "Light Armour", "Shield"],
            skills=["Step Aside", "Mighty Blow", "Faith"], skill_access=["Combat", "Strength"],
            experience=19, cost=35,
        ),
        WarriorVM(
            id="marta", name="Sister Superior Marta", profile_name="Sister Superior", kind="hero",
            stats=_stats((3, 4, 3, 3, 3, 1, 4, 1, 8)),
            equipment=["Crossbow", "Light Armour", "Dagger"],
            skills=["Marksman", "Dodge", "Prayer of Healing"], skill_access=["Shooting", "Speed"],
            experience=13, condition="Injured", condition_detail="Leg Wound (M -1)", cost=35,
        ),
        WarriorVM(
            id="veriet", name="Sister Veriet", profile_name="Augur", kind="hero",
            stats=_stats((4, 3, 3, 3, 3, 1, 4, 1, 7)),
            equipment=["Sword", "Light Armour"], skills=["Dodge", "Faith"], skill_access=["Speed", "Special"], experience=10, cost=25,
        ),
        WarriorVM(
            id="sisters", name="Sigmarite Sisters", profile_name="Sigmarite Sister", kind="henchman",
            stats=_stats((4, 3, 3, 3, 3, 1, 3, 1, 7)),
            equipment=["Hammer", "Buckler"], skills=[], experience=6, quantity=2, cost=25,
        ),
        WarriorVM(
            id="novices", name="Novices", profile_name="Novices", kind="henchman",
            stats=_stats((4, 2, 2, 3, 3, 1, 3, 1, 6)),
            equipment=["Hammer", "Dagger"], skills=[], experience=4, quantity=2, cost=15,
        ),
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
        InventoryItemVM("sigmarite-warhammer", "Sigmarite Warhammer", "Weapon", 1, 1, 0, 15, "Rare"),
        InventoryItemVM("hammer", "Hammer", "Weapon", 5, 4, 1, 3),
        InventoryItemVM("sword", "Sword", "Weapon", 3, 2, 1, 10),
        InventoryItemVM("crossbow", "Crossbow", "Weapon", 2, 1, 1, 25),
        InventoryItemVM("light-armour", "Light Armour", "Armour", 4, 3, 1, 20),
        InventoryItemVM("shield", "Shield", "Armour", 2, 1, 1, 5),
        InventoryItemVM("rope-hook", "Rope & Hook", "Misc", 2, 1, 1, 5),
        InventoryItemVM("lucky-charm", "Lucky Charm", "Misc", 2, 1, 1, 10),
        InventoryItemVM("healing-herbs", "Healing Herbs", "Consumable", 4, 0, 4, 8),
        InventoryItemVM("holy-relic", "Holy Relic", "Misc", 1, 0, 1, 15, "Rare"),
    ]

    campaign = CampaignVM(
        campaign_name="The Sisters of Morr",
        warband_name="My Sisters of Sigmar Warband",
        warband_type="Sisters of Sigmar",
        started="14 Jul 2026",
        current_state_number=7,
        warriors=warriors,
        battles=battles,
        states=states,
        post_battles=post_battles,
        inventory=inventory,
        stash_value=118,
        rare_finds=2,
    )
    return AppState(campaign=campaign, selected_moment="state:7")
