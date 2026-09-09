from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date

from mordheim_campaign.application.knowledge_port import KnowledgePort, WarbandProfile


@dataclass(slots=True)
class EquipmentEntryVM:
    item_id: str
    name: str
    quantity: int = 1
    acquisition: str = "purchase"
    unit_cost: int = 0
    per_model: bool = False
    transferable: bool = True
    special_rules: list[str] = field(default_factory=list)
    base_item_id: str = ""

    acquisition_costs: list[int] = field(default_factory=list)

    @property
    def copy_costs(self) -> list[int]:
        return (list(self.acquisition_costs) if len(self.acquisition_costs) == self.quantity
                else [self.unit_cost] * self.quantity)

    @property
    def total_cost(self) -> int:
        return self.quantity * self.unit_cost


@dataclass(slots=True)
class WarriorVM:
    id: str
    name: str
    profile_name: str
    kind: str
    stats: dict[str, int]
    equipment: list[EquipmentEntryVM]
    skills: list[str]
    experience: int
    previous_experience: int | None = None
    advance_experience: int | None = None
    quantity: int = 1
    condition: str | None = None
    condition_detail: str | None = None
    cost: int = 0
    stat_modifiers: dict[str, int] = field(default_factory=dict)
    skill_access: list[str] = field(default_factory=list)
    #: Characteristic points gained from post-battle advance rolls, by display
    #: key (``WS``, ``S``…). Distinct from ``stat_modifiers`` (injury effects):
    #: advances are bought by experience and count towards henchman limits.
    stat_advances: dict[str, int] = field(default_factory=dict)
    #: Canonical KB profile id (bands/<collection>/<band>/profiles.yaml).
    profile_id: str = ""
    #: Per-spell casting-difficulty modifiers gained in play. A repeated spell
    #: generation result lowers the duplicate spell's difficulty by 1 (KB
    #: rule); one entry per spell name, value -1.
    spell_difficulty_modifiers: dict[str, int] = field(default_factory=dict)
    equipment_limits: dict[str, int] = field(default_factory=dict)
    hireling_rating: int = 0
    maximum_models_modifier: int = 0
    upkeep_resources: list[tuple[str, int]] = field(default_factory=list)
    #: Future battles this warrior must sit out. Decremented only when a
    #: battle is recorded, never while navigating the post-battle sequence.
    games_to_miss: int = 0
    absence_reason: str = ""
    hatreds: list[str] = field(default_factory=list)
    battle_start_checks: list[dict] = field(default_factory=list)
    #: Structured lasting characteristic injuries for roster presentation.
    injury_records: list[dict] = field(default_factory=list)
    lost_eyes: list[str] = field(default_factory=list)
    special_rules: list[str] = field(default_factory=list)


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
    #: Warrior ids recorded Out of Action at the end of the battle. Table
    #: facts recorded at creation; Recovery (post-battle step 1) resolves
    #: their injury rolls. ``None`` = not recorded (legacy files): the UI
    #: then offers every warrior.
    out_of_action_ids: list[str] | None = None
    #: Roster snapshot at battle time (id, name, kind, quantity, condition),
    #: so historical reviews do not depend on the live roster.
    participants: list[dict] = field(default_factory=list)
    #: Explicit per-group Out-of-Action counts (warrior_id -> members lost).
    #: ``out_of_action_ids`` is derived from this map when present.
    per_group_casualties: dict[str, int] = field(default_factory=dict)
    #: Per-warrior experience award recorded with the battle
    #: (warrior_id -> XP). Empty for legacy battles: the uniform ``xp_delta``
    #: applies to every surviving warrior instead.
    xp_awards: dict[str, int] = field(default_factory=dict)
    #: Answers recorded for the structured scenario result fields
    #: (award id or question id -> value). Free-form, award-plan driven.
    scenario_results: dict = field(default_factory=dict)
    #: Roster members unavailable for this battle, snapshotted before their
    #: remaining absence counter is decremented.
    absentees: list[dict] = field(default_factory=list)
    #: Stable KB identity when the opponent was selected from the catalogue.
    #: The visible name remains available for custom/unlisted opponents.
    opponent_band_id: str = ""


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
    special_rules: list[str] = field(default_factory=list)
    base_item_id: str = ""

    acquisition_costs: list[int] = field(default_factory=list)

    @property
    def total_acquisition_cost(self) -> int:
        return sum(self.acquisition_costs) if len(self.acquisition_costs) == self.owned else self.value * self.owned

    def add_stock(self, quantity: int, unit_cost: int) -> None:
        if len(self.acquisition_costs) != self.owned:
            self.acquisition_costs = [self.value] * self.owned
        self.acquisition_costs.extend([unit_cost] * quantity)
        self.owned += quantity

    def remove_stock(self, quantity: int, *, unit_cost: int | None = None) -> int:
        if not 0 <= quantity <= self.owned:
            raise ValueError("Cannot remove more copies than the inventory owns.")
        if len(self.acquisition_costs) != self.owned:
            self.acquisition_costs = [self.value] * self.owned
        refund = 0
        for _ in range(quantity):
            index = (self.acquisition_costs.index(unit_cost)
                     if unit_cost is not None and unit_cost in self.acquisition_costs else 0)
            refund += self.acquisition_costs.pop(index)
        self.owned -= quantity
        return refund


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
    #: Roster and inventory deep-copied when the state was committed, so any
    #: timeline moment can be exported (PDF) exactly as it was then. Empty
    #: only in snapshots built before this field existed.
    roster: list["WarriorVM"] = field(default_factory=list)
    inventory: list["InventoryItemVM"] = field(default_factory=list)

    @property
    def node_id(self) -> str:
        return f"state:{self.number}"


@dataclass(slots=True)
class PostBattleVM:
    battle_number: int
    complete: bool = False
    active_step: int = 0
    completed_steps: set[int] = field(default_factory=set)
    review_open: bool = False
    #: Working totals of the pending sequence, persisted so a mid-sequence
    #: save/load resumes exactly where the player was. Roster and inventory
    #: mutations live directly on the campaign; only the numeric deltas are
    #: owned here.
    gold_delta: int = 0
    wyrdstone_delta: int = 0
    wyrdstone_sold: int = 0
    sale_resolved: bool = False
    veteran_pool: int = 0
    experience_applied: bool = False
    #: Pending advance rolls of this sequence, persisted so a mid-sequence
    #: save/load resumes. One row per warrior that crossed a threshold:
    #:
    #: - ``roll_total``/``subroll``: dice as rolled (``None`` until resolved);
    #: - ``committed``: the pick is applied to the roster;
    #: - ``table``: hero | henchman (the KB advancement table that resolves it).
    pending_advances: list[dict] = field(default_factory=list)
    #: Step-local working data of the pending sequence (unresolved dice,
    #: sale quantity, sub-roll choices), keyed by step index. Persisted so
    #: navigating away or a mid-sequence save/load cannot discard them.
    step_state: dict = field(default_factory=dict)
    #: Hero search assignments and results of step 06, keyed by hero id:
    #: {target, kind (rare|dramatis), item_id, modifiers, roll, success, used}.
    searches: dict = field(default_factory=dict)
    #: Explicit acknowledgement that an effect was resolved outside the
    #: application, keyed by step: list of acknowledged item ids.
    acknowledgements: dict = field(default_factory=dict)
    #: Structured log of every applied mutation of this sequence, rendered by
    #: the completed review: {step, action, ids, message}.
    event_log: list[dict] = field(default_factory=list)
    #: Per-group equipment obligations created by recruitment:
    #: [{warrior_id, item_id, quantity}]. Settled by the Equipment step.
    equipment_obligations: list[dict] = field(default_factory=list)
    #: Pending follow-up actions (injury subtables, exploration specials,
    #: advancement effects) awaiting resolution or acknowledgement:
    #: {id, step, type, description, ...}.
    pending_follow_ups: list[dict] = field(default_factory=list)

    def log_event(self, step: int, action: str, message: str, **ids) -> None:
        """Append one structured entry to the sequence event log."""
        self.event_log.append({"step": step, "action": action, "ids": {k: str(v) for k, v in ids.items() if v is not None}, "message": message})

    def acknowledge(self, step: int, item: str) -> None:
        acknowledged = self.acknowledgements.setdefault(str(step), [])
        if item not in acknowledged:
            acknowledged.append(item)

    def is_acknowledged(self, step: int, item: str) -> bool:
        return item in self.acknowledgements.get(str(step), [])

    def follow_ups_for_step(self, step: int) -> list[dict]:
        return [row for row in self.pending_follow_ups if row.get("step") is not None and int(row["step"]) == int(step)]

    def unacknowledged_follow_ups(self, step: int) -> list[dict]:
        """Pending follow-ups of one step the player has not acknowledged yet."""
        mandatory_types = {
            "injury_followup", "exploration_followup", "prisoner", "relationship",
            "eye_injury", "hireling_upkeep",
            "scenario_spell_reward", "scenario_encampment",
        }
        return [
            row for row in self.follow_ups_for_step(step)
            if (
                row.get("mandatory") is True
                or row.get("type") in mandatory_types
                or (row.get("type") == "encounter" and row.get("encounter_id") == "campaign.encounter.sold-to-the-pits")
                or not self.is_acknowledged(step, str(row.get("id")))
            )
        ]

    def pending_advance_for(self, warrior_id: str, threshold: int | None = None) -> dict | None:
        """The advance row being worked on: the first uncommitted row of the
        warrior, falling back to its first (already committed) row.

        ``threshold`` identifies one concrete earned advance when a warrior
        crossed several XP rungs in the same sequence.
        """
        rows = [row for row in self.pending_advances if str(row.get("warrior_id")) == warrior_id]
        if threshold is not None:
            return next((row for row in rows if int(row.get("threshold") or -1) == int(threshold)), None)
        return next((row for row in rows if not row.get("committed")), rows[0] if rows else None)

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
    #: Non-gold hiring resources declared by the KB hireling catalogue
    #: (per-resource fee/upkeep). Wyrdstone shards live on the states;
    #: these pools are campaign-level counters.
    treasures: int = 0
    campaign_points: int = 0
    special_rules: list[dict] = field(default_factory=list)
    #: Unique rewards already generated in this campaign. This history is
    #: intentionally independent from current ownership: losing the bearer
    #: must not make a unique magical artefact available again.
    unique_reward_ids: list[str] = field(default_factory=list)
    #: User-authored corrections made outside normal campaign resolution.
    manual_log: list[dict] = field(default_factory=list)

    # Draft-only construction metadata. In the real application these values
    # are supplied by the selected warband rules rather than the GUI.
    is_draft: bool = False
    starting_gold: int = 500
    minimum_models: int = 3
    maximum_models: int = 15
    hero_limit: int = 5
    required_profiles: dict[str, int] = field(default_factory=dict)

    # KB identity of the warband: later use cases resolve rules by these
    # stable ids, never by the visible name.
    collection: str = ""
    band_id: str = ""
    ruleset: str = "mordheim"
    #: Mercenary variant chosen by variant-capable warbands (reikland /
    #: middenheim / marienburg / ostermark); ``None`` elsewhere or before
    #: selection. Drives the variant-dependent hire-eligibility rules.
    mercenary_variant: str | None = None

    def next_warrior_id(self, prefix: str) -> str:
        occupied = {row.id for row in self.warriors}
        occupied.update(row.id for state in self.states for row in state.roster)
        occupied.update(str(row.get("id")) for battle in self.battles
                        for row in (*battle.participants, *battle.absentees))
        occupied.update(str(row.get("warrior_id")) for post in self.post_battles
                        for row in post.pending_advances)
        occupied.update(str(value) for post in self.post_battles for event in post.event_log
                        for key, value in (event.get("ids") or {}).items()
                        if key in {"warrior_id", "source_id", "target_id"})
        index = 1
        while f"{prefix}{index}" in occupied:
            index += 1
        return f"{prefix}{index}"

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
    def draft_warband_member_count(self) -> int:
        """Own-band models; Hired Swords never consume roster capacity."""
        return sum(w.quantity for w in self.warriors if w.kind != "hireling")

    @property
    def effective_maximum_models(self) -> int:
        return self.maximum_models + sum(w.maximum_models_modifier for w in self.warriors if w.kind == "hireling")

    @property
    def draft_hero_count(self) -> int:
        return sum(w.quantity for w in self.warriors if w.kind == "hero")

    @property
    def draft_henchman_count(self) -> int:
        return sum(w.quantity for w in self.warriors if w.kind == "henchman")

    @property
    def draft_experience(self) -> int:
        return sum(w.experience * w.quantity for w in self.warriors if w.kind != "hireling")

    @property
    def draft_recruitment_cost(self) -> int:
        return sum(w.cost * w.quantity for w in self.warriors)

    def stash_acquisition_costs(self, stock: InventoryItemVM) -> list[int]:
        if len(stock.acquisition_costs) != stock.owned:
            return [stock.value] * stock.stash
        costs = (list(stock.acquisition_costs) if len(stock.acquisition_costs) == stock.owned
                 else [stock.value] * stock.owned)
        for warrior in self.warriors:
            for equipment in warrior.equipment:
                if (equipment.item_id != stock.id or not equipment.transferable
                        or (self.is_draft and equipment.acquisition == "fixed")):
                    continue
                for cost in equipment.copy_costs:
                    if not costs:
                        break
                    costs.pop(costs.index(cost) if cost in costs else 0)
        return costs

    @property
    def draft_equipment_cost(self) -> int:
        return sum(item.total_acquisition_cost for item in self.inventory)

    @property
    def draft_treasury(self) -> int:
        return self.starting_gold - self.draft_recruitment_cost - self.draft_equipment_cost

    @property
    def draft_rating(self) -> int:
        members = self.draft_warband_member_count * 5 + self.draft_experience
        hirelings = sum(w.hireling_rating for w in self.warriors if w.kind == "hireling")
        return members + hirelings

    @property
    def has_required_profiles(self) -> bool:
        return all(sum(w.quantity for w in self.warriors if w.profile_id == profile_id) >= minimum
                   for profile_id, minimum in self.required_profiles.items())

    @property
    def draft_is_legal(self) -> bool:
        return (
            self.draft_warband_member_count >= self.minimum_models
            and self.draft_warband_member_count <= self.effective_maximum_models
            and 1 <= self.draft_hero_count <= self.hero_limit
            and self.draft_treasury >= 0
            and self.has_required_profiles
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
    #: Partially entered battle-entry draft (record-battle dialog), persisted
    #: so navigating to another timeline row does not discard it. Cleared
    #: when the battle is recorded or the dialog is cancelled.
    pending_battle_draft: dict = field(default_factory=dict)


def unique_warrior_name(warriors, base: str, *, exclude_id: str | None = None) -> str:
    """Stable, human-readable unique roster name using Roman suffixes."""
    taken = {row.name.casefold() for row in warriors if row.id != exclude_id}
    if base.casefold() not in taken:
        return base
    numerals = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
    index = 2
    while True:
        number = index
        suffix = ""
        for value, numeral in numerals:
            while number >= value:
                suffix += numeral
                number -= value
        candidate = f"{base} {suffix}"
        if candidate.casefold() not in taken:
            return candidate
        index += 1


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
    """Draft campaign with the canonical limits of the selected warband."""
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
        required_profiles={p.profile_id: p.member_minimum for p in port.profiles(option.collection, option.band_id) if p.required},
        collection=option.collection,
        band_id=option.band_id,
    )


def _starter_warriors(port: KnowledgePort, option) -> list[WarriorVM]:
    """Initial legal draft derived from the canonical roster.

    Starts with the mandatory members (roster minimums) and fills up to the
    minimum model count with the cheapest henchmen, without exceeding the
    starting treasury.
    """
    profiles = {p.profile_id: p for p in port.profiles(option.collection, option.band_id)}
    rules = port.roster_rules(option.collection, option.band_id)
    rows: list[WarriorVM] = []

    def add(profile: WarbandProfile, quantity: int, *, row_id: str) -> None:
        if quantity <= 0:
            return
        rows.append(warrior_vm(port, profile, quantity=quantity, row_id=row_id))

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
    # Warbands that declare all their heroes optional: the draft still needs
    # at least one hero, so the cheapest legal hero available is added.
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
    """New draft state: canonical identity, limits and initial roster."""
    package = port.find_package(band_id, collection)
    option = port.warband(package.collection, band_id)
    campaign = _draft_campaign(port, option, campaign_name=campaign_name, warriors=_starter_warriors(port, option))
    return AppState(campaign=campaign, selected_moment="draft:0", draft_warrior_tab="hero")


def make_example_state(port: KnowledgePort) -> AppState:
    """Navigable prototype example built on canonical profiles.

    The composition (profiles, stats, costs, access and inherent rules) comes
    from the KB. The later battle/state numbers are example narrative: that
    mutable state belongs to the campaign model, not the KB.
    """
    sisters = port.find_package("sisters-of-sigmar")
    option = port.warband(sisters.collection, str(sisters.band["id"]))

    def hero(profile_id: str, name: str, *, experience: int, previous: int | None = None,
             equipment: list[str] | None = None, extra_skills: list[str] | None = None,
             condition: str | None = None, condition_detail: str | None = None,
             modifiers: dict[str, int] | None = None, row_id: str | None = None) -> WarriorVM:
        profile = port.profile(option.collection, option.band_id, profile_id)
        return warrior_vm(
            port, profile, row_id=row_id or f"{profile_id}:1", name=name, experience=experience,
            previous_experience=previous, equipment=equipment or [],
            extra_skills=extra_skills or [], condition=condition, condition_detail=condition_detail,
            stat_modifiers=modifiers or {},
        )

    def group(profile_id: str, *, quantity: int, experience: int, equipment: list[str], row_id: str) -> WarriorVM:
        profile = port.profile(option.collection, option.band_id, profile_id)
        return warrior_vm(
            port, profile, row_id=row_id, quantity=quantity, experience=experience,
            equipment=equipment,
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
        *[PostBattleVM(number, True, 7, set(range(8)), False, experience_applied=True) for number in range(1, 8)],
        PostBattleVM(8, False, 4, set(range(4)), False, experience_applied=True),
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

    # The current state carries the live roster/inventory as its snapshot;
    # earlier example states stay aggregate-only.
    states[-1].roster = copy.deepcopy(warriors)
    states[-1].inventory = copy.deepcopy(inventory)

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
    port: KnowledgePort,
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
    """Converts a canonical profile into the warrior view-model used by the GUI.

    ``equipment`` receives canonical item ids. ``skills`` combines profile
    rules with skills gained in play.
    """
    item_ids = list(profile.fixed_equipment if equipment is None else equipment)
    entries = [
        EquipmentEntryVM(
            item_id=item_id,
            name=port.item_name(item_id) or item_id,
            quantity=quantity,
            acquisition="fixed",
            per_model=True,
        )
        for item_id in item_ids
    ]
    if equipment is None:
        free = next((offer for offer in port.items_for_profile(profile) if offer.first_free), None)
        if free is not None and all(item.item_id != free.item_id for item in entries):
            entries.append(EquipmentEntryVM(free.item_id, free.name, quantity, "starting_grant", 0, True, False))
    return WarriorVM(
        id=row_id or f"{profile.profile_id}#1",
        name=name or profile.name,
        profile_name=profile.name,
        kind=profile.kind,
        stats=dict(profile.characteristics),
        equipment=entries,
        skills=list(dict.fromkeys([*profile.inherent_rules, *profile.starting_skills, *(extra_skills or [])])),
        experience=profile.experience if experience is None else experience,
        previous_experience=previous_experience,
        advance_experience=profile.experience if experience is None else 0,
        quantity=quantity,
        condition=condition,
        condition_detail=condition_detail,
        cost=profile.cost,
        stat_modifiers=dict(stat_modifiers or {}),
        skill_access=list(profile.skill_tables),
        profile_id=profile.profile_id,
    )
