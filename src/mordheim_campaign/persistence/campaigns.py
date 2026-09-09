"""persistence.campaigns: campaign files of the Campaign Manager.

The format is self-contained JSON with a marker and a version (3). It saves the
campaign state managed by the GUI —warband, roster, battles, states (each one
with its roster/inventory snapshot), post-battle and inventory— together with
the UI selection so the same view can be resumed. The KB is never serialised: the file references stable
identities (``band_id``, ``profile_id``, ``item_id``) that the KB resolves
again on load.

Persisted values are external campaign state, never rules.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
import json as json
import re
import os
import tempfile
from pathlib import Path

from mordheim_campaign.application.state import (
    AppState,
    BattleVM,
    CampaignVM,
    EquipmentEntryVM,
    InventoryItemVM,
    PostBattleVM,
    WarbandStateVM,
    WarriorVM,
)

CAMPAIGN_MARKER = "MORDHEIM_CAMPAIGN_MANAGER"
FORMAT_VERSION = 3

FILE_EXTENSION = ".mordheim"


class CampaignFileError(ValueError):
    """The file does not satisfy the current campaign schema."""


def suggest_filename(campaign: CampaignVM) -> str:
    """Readable filename derived from the campaign name."""
    slug = re.sub(r"[^\w]+", "-", campaign.campaign_name).strip("-").lower() or "campaign"
    return f"{slug}{FILE_EXTENSION}"


def _asdict_plain(value):
    """Serialises dataclasses and containers into plain JSON objects."""
    if is_dataclass(value):
        return {field.name: _asdict_plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {str(key): _asdict_plain(item) for key, item in value.items()}
    if isinstance(value, set):
        return sorted(_asdict_plain(item) for item in value)
    if isinstance(value, (list, tuple)):
        return [_asdict_plain(item) for item in value]
    return value


def save_campaign(path, state: AppState) -> Path:
    """Saves the whole campaign (including the active view) to a JSON file."""
    destination = Path(path)
    campaign = state.campaign
    payload = {
        "marker": CAMPAIGN_MARKER,
        "format_version": FORMAT_VERSION,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "campaign": _asdict_plain(campaign),
        "view": {
            "active_view": state.active_view,
            "campaign_mode": state.campaign_mode,
            "selected_moment": state.selected_moment,
            "state_section": state.state_section,
            "battle_section": state.battle_section,
            "inventory_mode": state.inventory_mode,
            "draft_warrior_tab": state.draft_warrior_tab,
            "pending_battle_draft": state.pending_battle_draft,
        },
    }
    temporary = None
    try:
        content = json.dumps(payload, ensure_ascii=False, indent=2)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    except (OSError, TypeError, ValueError) as exc:
        raise CampaignFileError(f"Could not write campaign file: {exc}") from exc
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return destination


def load_campaign(path) -> AppState:
    """Loads a campaign saved by :func:`save_campaign`."""
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CampaignFileError(f"Could not read campaign file: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("marker") != CAMPAIGN_MARKER:
        raise CampaignFileError(f"{source} is not a Mordheim Campaign Manager file.")
    if payload.get("format_version") != FORMAT_VERSION:
        raise CampaignFileError(
            f"Unsupported campaign format version: {payload.get('format_version')} "
            f"(this build reads format {FORMAT_VERSION})."
        )
    try:
        campaign = _campaign_from_payload(dict(payload.get("campaign") or {}))
        view = dict(payload.get("view") or {})
        state = AppState(
            campaign=campaign,
            active_view=str(view.get("active_view") or "campaign"),
            campaign_mode=str(view.get("campaign_mode") or "timeline"),
            selected_moment=str(view.get("selected_moment") or "draft:0"),
            state_section=str(view.get("state_section") or "overview"),
            battle_section=str(view.get("battle_section") or "overview"),
            inventory_mode=str(view.get("inventory_mode") or "item"),
            draft_warrior_tab=str(view.get("draft_warrior_tab") or "hero"),
            pending_battle_draft=dict(view.get("pending_battle_draft") or {}),
        )
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        raise CampaignFileError(f"Invalid campaign payload: {exc}") from exc
    _validate_selection(state)
    return state


def _validate_selection(state: AppState) -> None:
    """Validate domain references and normalize the optional UI selection."""
    campaign = state.campaign
    def unique(values, label):
        values = list(values)
        if len(values) != len(set(values)):
            raise CampaignFileError(f"Duplicate {label} in campaign file.")
        return set(values)
    def nonnegative_integer(value, label):
        if type(value) is not int or value < 0:
            raise CampaignFileError(f"Invalid {label}: expected a nonnegative integer.")

    def validate_roster(roster):
        for warrior in roster:
            if warrior.quantity < 1:
                raise CampaignFileError("Warriors must have a positive model count.")
            for equipment in warrior.equipment:
                nonnegative_integer(equipment.quantity, "equipment quantity")
                nonnegative_integer(equipment.unit_cost, "equipment cost")
                if not isinstance(equipment.acquisition_costs, list):
                    raise CampaignFileError("Invalid equipment acquisition costs.")
                for cost in equipment.acquisition_costs:
                    nonnegative_integer(cost, "equipment acquisition cost")

    def validate_inventory(inventory):
        unique((row.id for row in inventory), "inventory IDs")
        for stock in inventory:
            for value in (stock.owned, stock.equipped, stock.stash, stock.value):
                nonnegative_integer(value, "inventory quantity or value")
            if stock.owned != stock.equipped + stock.stash:
                raise CampaignFileError("Inventory owned copies must equal equipped plus stash copies.")
            for cost in stock.acquisition_costs:
                nonnegative_integer(cost, "inventory acquisition cost")

    validate_roster(campaign.warriors)
    validate_inventory(campaign.inventory)
    for snapshot in campaign.states:
        validate_roster(snapshot.roster)
        validate_inventory(snapshot.inventory)
    states = unique((row.number for row in campaign.states), "state numbers")
    battles = unique((row.number for row in campaign.battles), "battle numbers")
    posts = unique((row.battle_number for row in campaign.post_battles), "post-battle numbers")
    unique((row.id for row in campaign.warriors), "warrior IDs")
    for snapshot in campaign.states:
        unique((row.id for row in snapshot.roster), "snapshot warrior IDs")
    if any(w.quantity < 1 for w in campaign.warriors):
        raise CampaignFileError("Warriors must have a positive model count.")
    live_ids = {warrior.id for warrior in campaign.warriors}
    for post in campaign.post_battles:
        if post.complete:
            continue
        followup_ids = []
        for followup in post.pending_follow_ups:
            identifier = followup.get("id")
            if identifier is None:
                continue  # Legacy queued exploration choices may not carry an ID.
            if not isinstance(identifier, str) or not identifier:
                raise CampaignFileError("Invalid pending follow-up identifier.")
            followup_ids.append(identifier)
        unique(followup_ids, "pending follow-up IDs")
        advance_keys = []
        for advance in post.pending_advances:
            warrior_id = advance.get("warrior_id")
            threshold = advance.get("threshold")
            if not isinstance(warrior_id, str) or (threshold is not None and type(threshold) is not int):
                raise CampaignFileError("Invalid pending advancement reference.")
            if not advance.get("committed"):
                if warrior_id not in live_ids:
                    raise CampaignFileError("A pending advance references a missing warrior.")
                advance_keys.append((warrior_id, threshold))
        unique(advance_keys, "pending advancements")
    if not posts <= battles:
        raise CampaignFileError("A post-battle references a missing battle.")
    if sum(not post.complete for post in campaign.post_battles) > 1:
        raise CampaignFileError("Multiple pending post-battles are not supported.")
    if any(not 0 <= post.active_step < 8 or not post.completed_steps <= set(range(8)) for post in campaign.post_battles):
        raise CampaignFileError("Invalid post-battle step.")
    if not campaign.is_draft and campaign.current_state_number not in states:
        raise CampaignFileError("The current warband state is missing.")
    fallback = "draft:0" if campaign.is_draft else f"state:{campaign.current_state_number}"
    valid = {"draft:0"} if campaign.is_draft else {
        *(f"state:{n}" for n in states), *(f"battle:{n}" for n in battles), *(f"post:{n}" for n in posts)
    }
    if not campaign.is_draft and campaign.pending_post_battle is None:
        valid.add(f"new-battle:{campaign.next_battle_number}")
    if state.selected_moment not in valid:
        state.selected_moment = fallback
    if state.active_view not in {"campaign", "rules", "settings", "statistics"}:
        state.active_view = "campaign"


def _campaign_from_payload(payload: dict) -> CampaignVM:
    campaign = CampaignVM(
        campaign_name=str(payload["campaign_name"]),
        warband_name=str(payload.get("warband_name") or payload["campaign_name"]),
        warband_type=str(payload.get("warband_type") or ""),
        started=str(payload.get("started") or ""),
        current_state_number=int(payload.get("current_state_number") or 0),
        warriors=[_warrior_from_payload(row) for row in payload.get("warriors") or ()],
        battles=[_battle_from_payload(row) for row in payload.get("battles") or ()],
        states=[_state_from_payload(row) for row in payload.get("states") or ()],
        post_battles=[_post_from_payload(row) for row in payload.get("post_battles") or ()],
        inventory=[_inventory_from_payload(row) for row in payload.get("inventory") or ()],
        stash_value=int(payload.get("stash_value") or 0),
        rare_finds=int(payload.get("rare_finds") or 0),
        treasures=int(payload.get("treasures") or 0),
        campaign_points=int(payload.get("campaign_points") or 0),
        special_rules=[dict(row) for row in payload.get("special_rules") or ()],
        unique_reward_ids=[str(value) for value in payload.get("unique_reward_ids") or ()],
        manual_log=[dict(row) for row in payload.get("manual_log") or ()],
        is_draft=bool(payload.get("is_draft") or False),
        starting_gold=int(payload.get("starting_gold", 500)),
        minimum_models=int(payload.get("minimum_models", 3)),
        maximum_models=int(payload.get("maximum_models", 15)),
        hero_limit=int(payload.get("hero_limit", 5)),
        required_profiles={str(key): int(value) for key, value in dict(payload.get("required_profiles") or {}).items()},
        collection=str(payload.get("collection") or ""),
        band_id=str(payload.get("band_id") or ""),
        ruleset=str(payload.get("ruleset") or "mordheim"),
        mercenary_variant=str(payload.get("mercenary_variant") or "") or None,
    )
    if not campaign.band_id:
        raise ValueError("the campaign payload does not identify its KB warband (band_id missing)")
    return campaign


def _warrior_from_payload(row: dict) -> WarriorVM:
    return WarriorVM(
        id=str(row["id"]),
        name=str(row["name"]),
        profile_name=str(row.get("profile_name") or ""),
        kind=str(row.get("kind") or "henchman"),
        stats={str(key): int(value) for key, value in dict(row.get("stats") or {}).items()},
        equipment=[EquipmentEntryVM(**item) for item in row.get("equipment") or ()],
        skills=[str(item) for item in row.get("skills") or ()],
        experience=int(row.get("experience") or 0),
        previous_experience=int(row["previous_experience"]) if row.get("previous_experience") is not None else None,
        advance_experience=int(row["advance_experience"]) if row.get("advance_experience") is not None else None,
        quantity=_strict_integer(row.get("quantity", 1)),
        condition=row.get("condition"),
        condition_detail=row.get("condition_detail"),
        cost=int(row.get("cost") or 0),
        stat_modifiers={str(key): int(value) for key, value in dict(row.get("stat_modifiers") or {}).items()},
        skill_access=[str(item) for item in row.get("skill_access") or ()],
        stat_advances={str(key): int(value) for key, value in dict(row.get("stat_advances") or {}).items()},
        profile_id=str(row.get("profile_id") or ""),
        spell_difficulty_modifiers={
            str(key): int(value)
            for key, value in dict(row.get("spell_difficulty_modifiers") or {}).items()
        },
        equipment_limits={str(key): int(value) for key, value in dict(row.get("equipment_limits") or {}).items()},
        hireling_rating=int(row.get("hireling_rating") or 0),
        maximum_models_modifier=int(row.get("maximum_models_modifier") or 0),
        upkeep_resources=[(str(key), int(value)) for key, value in row.get("upkeep_resources") or ()],
        games_to_miss=max(0, int(row.get("games_to_miss") or 0)),
        absence_reason=str(row.get("absence_reason") or ""),
        hatreds=[str(value) for value in row.get("hatreds") or ()],
        battle_start_checks=[dict(value) for value in row.get("battle_start_checks") or ()],
        injury_records=[dict(value) for value in row.get("injury_records") or ()],
        lost_eyes=[str(value) for value in row.get("lost_eyes") or ()],
        special_rules=[str(value) for value in row.get("special_rules") or ()],
    )


def _battle_from_payload(row: dict) -> BattleVM:
    return BattleVM(
        number=int(row["number"]),
        date=str(row.get("date") or ""),
        scenario=str(row.get("scenario") or ""),
        opponent=str(row.get("opponent") or ""),
        opponent_band_id=str(row.get("opponent_band_id") or ""),
        result=str(row.get("result") or ""),
        gold_delta=int(row.get("gold_delta") or 0),
        wyrdstone=int(row.get("wyrdstone") or 0),
        xp_delta=int(row.get("xp_delta") or 0),
        casualties=int(row.get("casualties") or 0),
        advances=int(row.get("advances") or 0),
        rating_before=int(row.get("rating_before") or 0),
        rating_after=int(row.get("rating_after") or 0),
        models_before=int(row.get("models_before") or 0),
        models_after=int(row.get("models_after") or 0),
        notes=str(row.get("notes") or ""),
        opponent_rating=int(row["opponent_rating"]) if row.get("opponent_rating") is not None else None,
        out_of_action_ids=(
            None if row.get("out_of_action_ids") is None
            else [str(value) for value in row.get("out_of_action_ids") or ()]
        ),
        participants=[dict(item) for item in row.get("participants") or ()],
        per_group_casualties={
            str(key): int(value)
            for key, value in dict(row.get("per_group_casualties") or {}).items()
        },
        xp_awards={
            str(key): int(value)
            for key, value in dict(row.get("xp_awards") or {}).items()
        },
        scenario_results=dict(row.get("scenario_results") or {}),
        absentees=[dict(item) for item in row.get("absentees") or ()],
    )


def _state_from_payload(row: dict) -> WarbandStateVM:
    return WarbandStateVM(
        number=int(row["number"]),
        date=str(row.get("date") or ""),
        gold=int(row.get("gold") or 0),
        wyrdstone=int(row.get("wyrdstone") or 0),
        rating=int(row.get("rating") or 0),
        models=int(row.get("models") or 0),
        max_models=int(row.get("max_models") or 0),
        heroes=int(row.get("heroes") or 0),
        henchmen=int(row.get("henchmen") or 0),
        experience=int(row.get("experience") or 0),
        label=str(row.get("label") or ""),
        roster=[_warrior_from_payload(item) for item in row.get("roster") or ()],
        inventory=[_inventory_from_payload(item) for item in row.get("inventory") or ()],
    )


def _post_from_payload(row: dict) -> PostBattleVM:
    return PostBattleVM(
        battle_number=int(row["battle_number"]),
        complete=bool(row.get("complete") or False),
        active_step=int(row.get("active_step") or 0),
        completed_steps={int(value) for value in row.get("completed_steps") or ()},
        review_open=bool(row.get("review_open") or False),
        # Working totals of a pending sequence; absent in files saved before
        # the write side existed, so they default to zero.
        gold_delta=int(row.get("gold_delta") or 0),
        wyrdstone_delta=int(row.get("wyrdstone_delta") or 0),
        wyrdstone_sold=int(row.get("wyrdstone_sold") or 0),
        sale_resolved=bool(row.get("sale_resolved") or False),
        veteran_pool=int(row.get("veteran_pool") or 0),
        experience_applied=bool(row.get("experience_applied") or False),
        pending_advances=[dict(item) for item in row.get("pending_advances") or ()],
        step_state=dict(row.get("step_state") or {}),
        searches=dict(row.get("searches") or {}),
        acknowledgements=dict(row.get("acknowledgements") or {}),
        event_log=[dict(item) for item in row.get("event_log") or ()],
        equipment_obligations=[dict(item) for item in row.get("equipment_obligations") or ()],
        pending_follow_ups=[dict(item) for item in row.get("pending_follow_ups") or ()],
    )


def _strict_integer(value):
    if type(value) is not int:
        raise ValueError("Counts and costs must be integers.")
    return value


def _inventory_from_payload(row: dict) -> InventoryItemVM:
    return InventoryItemVM(
        id=str(row["id"]),
        name=str(row["name"]),
        category=str(row.get("category") or ""),
        owned=_strict_integer(row.get("owned", 0)),
        equipped=_strict_integer(row.get("equipped", 0)),
        stash=_strict_integer(row.get("stash", 0)),
        value=_strict_integer(row.get("value", 0)),
        rarity=row.get("rarity"),
        special_rules=[str(value) for value in row.get("special_rules") or ()],
        base_item_id=str(row.get("base_item_id") or ""),
        acquisition_costs=[_strict_integer(value) for value in row.get("acquisition_costs") or ()],
    )


def export_campaign_summary(path, state: AppState) -> Path:
    """Writes a readable Markdown summary of the current campaign state."""
    campaign = state.campaign
    lines = [
        f"# {campaign.campaign_name}",
        "",
        f"- Warband: **{campaign.warband_type}** ({campaign.warband_name})",
        f"- Started: {campaign.started or '—'}",
        f"- KB identity: `{campaign.collection}/{campaign.band_id}` · ruleset `{campaign.ruleset}`",
    ]
    if campaign.is_draft:
        lines.append(f"- Status: draft · {campaign.draft_model_count} models · {campaign.draft_treasury} gc remaining")
    else:
        current = campaign.current_state
        lines.append(f"- Status: State #{current.number} · Rating {current.rating} · {current.models} models · {current.gold} gc")
    lines += ["", "## Roster", ""]
    for warrior in campaign.warriors:
        stats = " · ".join(f"{key} {value}" for key, value in warrior.stats.items())
        lines.append(f"- **{warrior.name}** — {warrior.profile_name} ({warrior.kind}"
                     f"{' ×' + str(warrior.quantity) if warrior.quantity > 1 else ''}) · {warrior.cost} gc · EXP {warrior.experience}")
        lines.append(f"  - {stats}")
        if warrior.equipment:
            lines.append("  - Equipment: " + ", ".join(f"{item.name} ×{item.quantity}" for item in warrior.equipment))
        if warrior.skills:
            lines.append("  - Skills / rules: " + ", ".join(warrior.skills))
    if campaign.states:
        lines += ["", "## Timeline states", ""]
        for snapshot in campaign.states:
            label = f" ({snapshot.label})" if snapshot.label else ""
            lines.append(f"- **State #{snapshot.number}**{label} — {snapshot.date} · Rating {snapshot.rating} · "
                         f"{snapshot.models}/{snapshot.max_models} models · {snapshot.gold} gc · {snapshot.experience} XP")
    if campaign.battles:
        lines += ["", "## Battles", ""]
        for battle in campaign.battles:
            lines.append(f"- **Battle #{battle.number}** — {battle.scenario} vs. {battle.opponent} · {battle.result} · "
                         f"{battle.gold_delta:+d} gc · +{battle.wyrdstone} wyrdstone · {battle.rating_before} → {battle.rating_after} rating")
    if campaign.inventory:
        lines += ["", "## Inventory", ""]
        for item in campaign.inventory:
            rarity = f" · {item.rarity}" if item.rarity else ""
            lines.append(f"- {item.name} ×{item.owned} (equipped {item.equipped}, stash {item.stash}) · {item.value} gc{rarity}")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination
