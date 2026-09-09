"""persistence.campaigns: campaign files of the Campaign Manager.

The format is self-contained JSON with a marker and a version. v4 is the
neutral contract shared with the web application: it is documented with a JSON
Schema and fixtures in ``contracts/campaign-file-v4/`` (see that README). The
file saves the campaign state managed by the GUI —identity, configuration,
resources, warriors, battles, states (each one with its roster/inventory
snapshot), post-battle and inventory— together with the UI selection so the
same view can be resumed. The KB is never serialised: the file references stable
identities (``band_id``, ``profile_id``, ``item_id``) that the KB resolves
again on load.

Persisted values are external campaign state, never rules.

Compatibility policy: only v4 is read and written. Documents with versions
1–3 are rejected explicitly with a message that names both the found and the
supported version. Loading validates the document against the v4 JSON Schema
before reconstructing the state, so a malformed file fails with a precise
error instead of a deep constructor one.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
import json as json
import os
import tempfile
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from mordheim_campaign.domain.models import (
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
FORMAT_VERSION = 4
#: Versions the application used before the neutral v4 contract. Never read.
RETIRED_FORMAT_VERSIONS = (1, 2, 3)

FILE_EXTENSION = ".mordheim"

_CONTRACT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3] / "contracts" / "campaign-file-v4" / "campaign-file-v4.schema.json"
)


class CampaignFileError(ValueError):
    """The file does not satisfy the current campaign schema."""


def _schema() -> dict:
    """The v4 JSON Schema of the shared contract.

    The contract lives in the repository; the schema is read from disk rather
    than duplicated in code so the contract stays the single source of truth.
    """
    try:
        return json.loads(_CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignFileError(f"Cannot read the v4 campaign contract schema: {exc}") from exc


def _validate_document(payload: dict) -> None:
    """Validates the raw document against the v4 contract schema."""
    schema = _schema()
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        raise CampaignFileError(f"Invalid v4 campaign contract schema: {exc}") from exc
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda error: list(error.absolute_path))
    if errors:
        first = errors[0]
        location = "/".join(str(part) for part in first.absolute_path) or "(document root)"
        raise CampaignFileError(
            f"The campaign file does not satisfy the v4 contract at '{location}': {first.message}"
        )


def suggest_filename(campaign: CampaignVM) -> str:
    """Readable filename derived from the campaign name."""
    import re

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


# --------------------------------------------------------------------------
# v4 document composition
# --------------------------------------------------------------------------


def _document(state: AppState, *, saved_at: str) -> dict:
    """Builds the neutral v4 document from the application state."""
    campaign = state.campaign
    return {
        "marker": CAMPAIGN_MARKER,
        "format_version": FORMAT_VERSION,
        "saved_at": saved_at,
        "campaign": {
            "identity": {
                "campaign_name": campaign.campaign_name,
                "warband_name": campaign.warband_name,
                "warband_type": campaign.warband_type,
                "started": campaign.started,
                "collection": campaign.collection,
                "band_id": campaign.band_id,
                "ruleset": campaign.ruleset,
                "mercenary_variant": campaign.mercenary_variant,
            },
            "configuration": {
                "is_draft": campaign.is_draft,
                "starting_gold": campaign.starting_gold,
                "minimum_models": campaign.minimum_models,
                "maximum_models": campaign.maximum_models,
                "hero_limit": campaign.hero_limit,
                **({"required_profiles": dict(campaign.required_profiles)} if campaign.required_profiles else {}),
            },
            "resources": {
                "stash_value": campaign.stash_value,
                "rare_finds": campaign.rare_finds,
                "treasures": campaign.treasures,
                "campaign_points": campaign.campaign_points,
            },
            "current_state_number": campaign.current_state_number,
            "warriors": [_warrior_document(warrior) for warrior in campaign.warriors],
            "battles": [_battle_document(battle) for battle in campaign.battles],
            "states": [_state_document(snapshot) for snapshot in campaign.states],
            "post_battles": [_post_battle_document(post) for post in campaign.post_battles],
            "inventory": [_inventory_document(item) for item in campaign.inventory],
            "special_rules": _asdict_plain(campaign.special_rules),
            "unique_reward_ids": list(campaign.unique_reward_ids),
            "manual_log": _asdict_plain(campaign.manual_log),
        },
        "view": {
            "active_view": state.active_view,
            "campaign_mode": state.campaign_mode,
            "selected_moment": state.selected_moment,
            "state_section": state.state_section,
            "battle_section": state.battle_section,
            "inventory_mode": state.inventory_mode,
            "draft_warrior_tab": state.draft_warrior_tab,
            "pending_battle_draft": _asdict_plain(state.pending_battle_draft),
        },
    }


def _warrior_document(warrior: WarriorVM) -> dict:
    return {
        "id": warrior.id,
        "name": warrior.name,
        "profile_name": warrior.profile_name,
        "kind": warrior.kind,
        "stats": dict(warrior.stats),
        "equipment": [_equipment_document(entry) for entry in warrior.equipment],
        "skills": list(warrior.skills),
        "experience": warrior.experience,
        "previous_experience": warrior.previous_experience,
        **({"advance_experience": warrior.advance_experience} if warrior.advance_experience is not None else {}),
        "quantity": warrior.quantity,
        "condition": warrior.condition,
        "condition_detail": warrior.condition_detail,
        "cost": warrior.cost,
        "stat_modifiers": dict(warrior.stat_modifiers),
        "skill_access": list(warrior.skill_access),
        "stat_advances": dict(warrior.stat_advances),
        "profile_id": warrior.profile_id,
        "spell_difficulty_modifiers": dict(warrior.spell_difficulty_modifiers),
        **({"equipment_limits": dict(warrior.equipment_limits)} if warrior.equipment_limits else {}),
        "hireling_rating": warrior.hireling_rating,
        "maximum_models_modifier": warrior.maximum_models_modifier,
        "upkeep_resources": [[key, value] for key, value in warrior.upkeep_resources],
        "games_to_miss": warrior.games_to_miss,
        "absence_reason": warrior.absence_reason,
        "hatreds": list(warrior.hatreds),
        "battle_start_checks": _asdict_plain(warrior.battle_start_checks),
        "injury_records": _asdict_plain(warrior.injury_records),
        "lost_eyes": list(warrior.lost_eyes),
        "special_rules": list(warrior.special_rules),
    }


def _equipment_document(entry: EquipmentEntryVM) -> dict:
    return {
        "item_id": entry.item_id,
        "name": entry.name,
        "quantity": entry.quantity,
        "acquisition": entry.acquisition,
        "unit_cost": entry.unit_cost,
        "per_model": entry.per_model,
        "transferable": entry.transferable,
        "special_rules": list(entry.special_rules),
        "base_item_id": entry.base_item_id,
        **({"acquisition_costs": list(entry.acquisition_costs)} if entry.acquisition_costs else {}),
    }


def _battle_document(battle: BattleVM) -> dict:
    return {
        "number": battle.number,
        "date": battle.date,
        "scenario": battle.scenario,
        "opponent": battle.opponent,
        "opponent_band_id": battle.opponent_band_id,
        "result": battle.result,
        "gold_delta": battle.gold_delta,
        "wyrdstone": battle.wyrdstone,
        "xp_delta": battle.xp_delta,
        "casualties": battle.casualties,
        "advances": battle.advances,
        "rating_before": battle.rating_before,
        "rating_after": battle.rating_after,
        "models_before": battle.models_before,
        "models_after": battle.models_after,
        "notes": battle.notes,
        "opponent_rating": battle.opponent_rating,
        "out_of_action_ids": (
            None if battle.out_of_action_ids is None
            else list(battle.out_of_action_ids)
        ),
        "participants": _asdict_plain(battle.participants),
        "per_group_casualties": dict(battle.per_group_casualties),
        "xp_awards": dict(battle.xp_awards),
        "scenario_results": _asdict_plain(battle.scenario_results),
        "absentees": _asdict_plain(battle.absentees),
    }


def _state_document(snapshot: WarbandStateVM) -> dict:
    return {
        "number": snapshot.number,
        "date": snapshot.date,
        "gold": snapshot.gold,
        "wyrdstone": snapshot.wyrdstone,
        "rating": snapshot.rating,
        "models": snapshot.models,
        "max_models": snapshot.max_models,
        "heroes": snapshot.heroes,
        "henchmen": snapshot.henchmen,
        "experience": snapshot.experience,
        "label": snapshot.label,
        "roster": [_warrior_document(warrior) for warrior in snapshot.roster],
        "inventory": [_inventory_document(item) for item in snapshot.inventory],
    }


def _post_battle_document(post: PostBattleVM) -> dict:
    return {
        "battle_number": post.battle_number,
        "complete": post.complete,
        "active_step": post.active_step,
        "completed_steps": sorted(post.completed_steps),
        "review_open": post.review_open,
        "gold_delta": post.gold_delta,
        "wyrdstone_delta": post.wyrdstone_delta,
        "wyrdstone_sold": post.wyrdstone_sold,
        "sale_resolved": post.sale_resolved,
        "veteran_pool": post.veteran_pool,
        "experience_applied": post.experience_applied,
        "pending_advances": _asdict_plain(post.pending_advances),
        "step_state": _asdict_plain(post.step_state),
        "searches": _asdict_plain(post.searches),
        "acknowledgements": _asdict_plain(post.acknowledgements),
        "event_log": _asdict_plain(post.event_log),
        "equipment_obligations": _asdict_plain(post.equipment_obligations),
        "pending_follow_ups": _asdict_plain(post.pending_follow_ups),
    }


def _inventory_document(item: InventoryItemVM) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "category": item.category,
        "owned": item.owned,
        "equipped": item.equipped,
        "stash": item.stash,
        "value": item.value,
        "rarity": item.rarity,
        "special_rules": list(item.special_rules),
        "base_item_id": item.base_item_id,
        **({"acquisition_costs": list(item.acquisition_costs)} if item.acquisition_costs else {}),
    }


# --------------------------------------------------------------------------
# v4 document parsing
# --------------------------------------------------------------------------


def _require(row: dict, key: str, context: str):
    if key not in row:
        raise CampaignFileError(f"Missing '{key}' in {context}.")
    return row[key]


def _int_map(row: dict, key: str, context: str) -> dict[str, int]:
    return {str(key_): int(value) for key_, value in dict(row.get(key) or {}).items()}


def _campaign_from_document(payload: dict) -> CampaignVM:
    identity = dict(payload.get("identity") or {})
    configuration = dict(payload.get("configuration") or {})
    resources = dict(payload.get("resources") or {})
    if not str(identity.get("band_id") or ""):
        raise CampaignFileError("the campaign document does not identify its KB warband (band_id missing)")
    return CampaignVM(
        campaign_name=str(_require(identity, "campaign_name", "campaign.identity")),
        warband_name=str(identity.get("warband_name") or identity["campaign_name"]),
        warband_type=str(identity.get("warband_type") or ""),
        started=str(identity.get("started") or ""),
        collection=str(identity.get("collection") or ""),
        band_id=str(identity["band_id"]),
        ruleset=str(identity.get("ruleset") or "mordheim"),
        mercenary_variant=str(identity["mercenary_variant"]) if identity.get("mercenary_variant") is not None else None,
        is_draft=bool(configuration.get("is_draft") or False),
        starting_gold=int(configuration.get("starting_gold") or 500),
        minimum_models=int(configuration.get("minimum_models") or 3),
        maximum_models=int(configuration.get("maximum_models") or 15),
        hero_limit=int(configuration.get("hero_limit") or 5),
        **({"required_profiles": {str(key): int(value) for key, value in dict(configuration.get("required_profiles") or {}).items()}}
           if configuration.get("required_profiles") else {}),
        stash_value=int(resources.get("stash_value") or 0),
        rare_finds=int(resources.get("rare_finds") or 0),
        treasures=int(resources.get("treasures") or 0),
        campaign_points=int(resources.get("campaign_points") or 0),
        current_state_number=int(payload.get("current_state_number") or 0),
        warriors=[_warrior_from_document(row) for row in payload.get("warriors") or ()],
        battles=[_battle_from_document(row) for row in payload.get("battles") or ()],
        states=[_state_from_document(row) for row in payload.get("states") or ()],
        post_battles=[_post_battle_from_document(row) for row in payload.get("post_battles") or ()],
        inventory=[_inventory_from_document(row) for row in payload.get("inventory") or ()],
        special_rules=[dict(row) for row in payload.get("special_rules") or ()],
        unique_reward_ids=[str(value) for value in payload.get("unique_reward_ids") or ()],
        manual_log=[dict(row) for row in payload.get("manual_log") or ()],
    )


def _warrior_from_document(row: dict) -> WarriorVM:
    context = "warrior"
    return WarriorVM(
        id=str(_require(row, "id", context)),
        name=str(row.get("name") or ""),
        profile_name=str(row.get("profile_name") or ""),
        kind=str(row.get("kind") or "henchman"),
        stats=_int_map(row, "stats", context),
        equipment=[_equipment_from_document(item) for item in row.get("equipment") or ()],
        skills=[str(item) for item in row.get("skills") or ()],
        experience=int(row.get("experience") or 0),
        previous_experience=int(row["previous_experience"]) if row.get("previous_experience") is not None else None,
        advance_experience=int(row["advance_experience"]) if row.get("advance_experience") is not None else None,
        quantity=_strict_integer(row.get("quantity", 1), "warrior quantity"),
        condition=row.get("condition"),
        condition_detail=row.get("condition_detail"),
        cost=int(row.get("cost") or 0),
        stat_modifiers=_int_map(row, "stat_modifiers", context),
        skill_access=[str(item) for item in row.get("skill_access") or ()],
        stat_advances=_int_map(row, "stat_advances", context),
        profile_id=str(row.get("profile_id") or ""),
        spell_difficulty_modifiers=_int_map(row, "spell_difficulty_modifiers", context),
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


def _equipment_from_document(row: dict) -> EquipmentEntryVM:
    return EquipmentEntryVM(
        item_id=str(_require(row, "item_id", "equipment entry")),
        name=str(row.get("name") or ""),
        quantity=int(row.get("quantity") or 1),
        acquisition=str(row.get("acquisition") or "purchase"),
        unit_cost=int(row.get("unit_cost") or 0),
        per_model=bool(row.get("per_model") or False),
        transferable=bool(row.get("transferable") if row.get("transferable") is not None else True),
        special_rules=[str(value) for value in row.get("special_rules") or ()],
        base_item_id=str(row.get("base_item_id") or ""),
        acquisition_costs=[_strict_integer(value, "equipment acquisition cost") for value in row.get("acquisition_costs") or ()],
    )


def _battle_from_document(row: dict) -> BattleVM:
    context = "battle"
    return BattleVM(
        number=int(_require(row, "number", context)),
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
        per_group_casualties=_int_map(row, "per_group_casualties", context),
        xp_awards=_int_map(row, "xp_awards", context),
        scenario_results=dict(row.get("scenario_results") or {}),
        absentees=[dict(item) for item in row.get("absentees") or ()],
    )


def _state_from_document(row: dict) -> WarbandStateVM:
    return WarbandStateVM(
        number=int(_require(row, "number", "state")),
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
        roster=[_warrior_from_document(item) for item in row.get("roster") or ()],
        inventory=[_inventory_from_document(item) for item in row.get("inventory") or ()],
    )


def _post_battle_from_document(row: dict) -> PostBattleVM:
    return PostBattleVM(
        battle_number=int(_require(row, "battle_number", "post_battle")),
        complete=bool(row.get("complete") or False),
        active_step=int(row.get("active_step") or 0),
        completed_steps={int(value) for value in row.get("completed_steps") or ()},
        review_open=bool(row.get("review_open") or False),
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


def _inventory_from_document(row: dict) -> InventoryItemVM:
    return InventoryItemVM(
        id=str(_require(row, "id", "inventory item")),
        name=str(row.get("name") or ""),
        category=str(row.get("category") or ""),
        owned=_strict_integer(row.get("owned", 0), "inventory owned"),
        equipped=_strict_integer(row.get("equipped", 0), "inventory equipped"),
        stash=_strict_integer(row.get("stash", 0), "inventory stash"),
        value=_strict_integer(row.get("value", 0), "inventory value"),
        rarity=row.get("rarity"),
        special_rules=[str(value) for value in row.get("special_rules") or ()],
        base_item_id=str(row.get("base_item_id") or ""),
        acquisition_costs=[_strict_integer(value, "inventory acquisition cost") for value in row.get("acquisition_costs") or ()],
    )


def _strict_integer(value, label: str) -> int:
    """Strict integer read: booleans and floats are refused, not coerced."""
    if type(value) is not int:
        raise CampaignFileError(f"Invalid {label}: counts and costs must be integers.")
    return value


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def save_campaign(path, state: AppState) -> Path:
    """Saves the whole campaign (including the active view) as a v4 document.

    The write is atomic (temp file + fsync + replace): a failed save must
    never truncate or corrupt the last valid file.
    """
    destination = Path(path)
    payload = _document(state, saved_at=datetime.now(timezone.utc).isoformat())
    _validate_document(payload)  # never write a document the contract would reject
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
    """Loads a v4 campaign document saved by :func:`save_campaign`.

    v1–v3 files are retired and rejected explicitly; the document must also
    satisfy the shared v4 JSON Schema before the state is reconstructed.
    """
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CampaignFileError(f"Could not read campaign file: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("marker") != CAMPAIGN_MARKER:
        raise CampaignFileError(f"{source} is not a Mordheim Campaign Manager file.")
    version = payload.get("format_version")
    if version in RETIRED_FORMAT_VERSIONS:
        raise CampaignFileError(
            f"Retired campaign format version {version} is no longer supported: "
            f"this build reads only the neutral format v4. "
            f"Open and re-export the campaign with an application of format v3 or earlier first."
        )
    if version != FORMAT_VERSION:
        raise CampaignFileError(
            f"Unsupported campaign format version: {version} (this build reads format {FORMAT_VERSION})."
        )
    _validate_document(payload)
    try:
        campaign = _campaign_from_document(dict(payload["campaign"]))
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
    except (KeyError, TypeError, ValueError) as exc:
        raise CampaignFileError(f"Invalid campaign payload: {exc}") from exc
    _validate_document_integrity(state.campaign)
    _validate_selection(state)
    return state


def _validate_document_integrity(campaign) -> None:
    """Domain-reference validation of a loaded campaign (ported from the
    desktop loader hardening): unique ids/numbers, nonnegative counts,
    inventory conservation, and pending post-battle references."""

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


def _validate_selection(state: AppState) -> None:
    """Validate domain references and normalize the optional UI selection."""
    campaign = state.campaign

    states = {row.number for row in campaign.states}
    battles = {row.number for row in campaign.battles}
    posts = {row.battle_number for row in campaign.post_battles}
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
