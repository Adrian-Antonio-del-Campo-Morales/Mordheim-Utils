"""campaign.domain.models: the campaign state model.

Pure, immutable-by-discipline dataclasses plus the derived projections
(draft legality, rating, treasury, timeline node ids). The module imports no
UI toolkit, no locale singleton and no filesystem: it is the state both the
desktop application and the web application operate on.

The construction builders that need the KnowledgePort live in
``campaign.domain.builders``; the module keeps a TYPE_CHECKING import only.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
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
    #: Per-copy acquisition costs (oldest first). Empty = pre-acquisition-cost
    #: file or fixed equipment: the unit cost stands in for every copy.
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
    #: Experience baseline for the pending advance row (``0`` for hires made
    #: after the campaign started). ``None`` = pre-advance-experience file.
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
    #: Remaining equip capacity by KB category key (post-battle equipment
    #: step). Empty = unrestricted (pre-limit files).
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
    #: Per-copy acquisition costs (oldest first). Empty = pre-acquisition-cost
    #: file: the item value stands in for every owned copy.
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
    #: Draft-time minimum member counts per required KB profile id, seeded by
    #: the controller when a draft is created/replaced and persisted with the
    #: campaign (the v4 writer carries it). Consumed by ``has_required_profiles``.
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
        """Per-copy costs of the stash copies, net of the copies equipped from
        this stock (equipped copies were paid when they left the stash).
        Legacy stocks without a per-copy ledger value every stash copy at the
        item value."""
        if len(stock.acquisition_costs) != stock.owned:
            return [stock.value] * stock.stash
        costs = list(stock.acquisition_costs)
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
        """True when every required draft profile has its minimum member count."""
        return all(
            sum(w.quantity for w in self.warriors if w.profile_id == profile_id) >= minimum
            for profile_id, minimum in self.required_profiles.items()
        )

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
