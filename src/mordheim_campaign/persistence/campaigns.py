"""persistence.campaigns: ficheros de campaña del Campaign Manager.

El formato es JSON autocontenido con marcador y versión. Guarda el estado de la
campaña gestionado en la GUI —banda, roster, batallas, estados, post-batalla e
inventario— junto con la selección de UI para poder reanudar la misma vista.
La KB nunca se serializa: el fichero referencia identidades estables
(``band_id``, ``profile_id``, ``item_id``) que la KB vuelve a resolver al cargar.

Los valores persistidos son estado externo de la campaña, nunca reglas.
"""
from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
import json as json
import re
from pathlib import Path

from mordheim_campaign.application.state import (
    AppState,
    BattleVM,
    CampaignVM,
    InventoryItemVM,
    PostBattleVM,
    WarbandStateVM,
    WarriorVM,
)

CAMPAIGN_MARKER = "MORDHEIM_CAMPAIGN_MANAGER"
FORMAT_VERSION = 1

FILE_EXTENSION = ".mordheim"


class CampaignFileError(ValueError):
    """El fichero no satisface el esquema actual de campaña."""


def suggest_filename(campaign: CampaignVM) -> str:
    """Nombre de fichero legible derivado del nombre de la campaña."""
    slug = re.sub(r"[^\w]+", "-", campaign.campaign_name).strip("-").lower() or "campaign"
    return f"{slug}{FILE_EXTENSION}"


def _asdict_plain(value):
    """Serializa dataclasses y contenedores en objetos simples JSON."""
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
    """Escribe la campaña completa (incluida la vista activa) en un fichero JSON."""
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
        },
    }
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError as exc:
        raise CampaignFileError(f"Could not write campaign file: {exc}") from exc
    return destination


def load_campaign(path) -> AppState:
    """Carga una campaña guardada por :func:`save_campaign`."""
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CampaignFileError(f"Could not read campaign file: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("marker") != CAMPAIGN_MARKER:
        raise CampaignFileError(f"{source} is not a Mordheim Campaign Manager file.")
    if int(payload.get("format_version") or -1) != FORMAT_VERSION:
        raise CampaignFileError(f"Unsupported campaign format version: {payload.get('format_version')}")
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
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise CampaignFileError(f"Invalid campaign payload: {exc}") from exc
    _validate_selection(state)
    return state


def _validate_selection(state: AppState) -> None:
    """Asegura que la selección de vista apunte a un nodo existente."""
    campaign = state.campaign
    node = state.selected_moment
    kind = node.split(":", 1)[0] if ":" in node else node
    valid_kinds = {"draft", "state", "battle", "post"}
    if kind not in valid_kinds:
        state.selected_moment = "draft:0" if campaign.is_draft else "state:0"
        return
    if kind == "draft" and not campaign.is_draft:
        state.selected_moment = "state:0"
    if kind == "state" and campaign.is_draft:
        state.selected_moment = "draft:0"
    if kind in {"battle", "post"}:
        numbers = {battle.number for battle in campaign.battles}
        wanted = node.split(":", 1)[1]
        if wanted.isdigit() and int(wanted) not in numbers:
            state.selected_moment = "draft:0" if campaign.is_draft else "state:0"
        if kind == "post" and campaign.is_draft:
            state.selected_moment = "draft:0"
    if not campaign.states and not campaign.is_draft:
        state.selected_moment = "draft:0"


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
        is_draft=bool(payload.get("is_draft") or False),
        starting_gold=int(payload.get("starting_gold") or 500),
        minimum_models=int(payload.get("minimum_models") or 3),
        maximum_models=int(payload.get("maximum_models") or 15),
        hero_limit=int(payload.get("hero_limit") or 5),
        collection=str(payload.get("collection") or ""),
        band_id=str(payload.get("band_id") or ""),
        ruleset=str(payload.get("ruleset") or "mordheim"),
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
        equipment=[str(item) for item in row.get("equipment") or ()],
        skills=[str(item) for item in row.get("skills") or ()],
        experience=int(row.get("experience") or 0),
        previous_experience=int(row["previous_experience"]) if row.get("previous_experience") is not None else None,
        quantity=int(row.get("quantity") or 1),
        condition=row.get("condition"),
        condition_detail=row.get("condition_detail"),
        cost=int(row.get("cost") or 0),
        equipment_cost=int(row.get("equipment_cost") or 0),
        stat_modifiers={str(key): int(value) for key, value in dict(row.get("stat_modifiers") or {}).items()},
        skill_access=[str(item) for item in row.get("skill_access") or ()],
        profile_id=str(row.get("profile_id") or ""),
    )


def _battle_from_payload(row: dict) -> BattleVM:
    return BattleVM(
        number=int(row["number"]),
        date=str(row.get("date") or ""),
        scenario=str(row.get("scenario") or ""),
        opponent=str(row.get("opponent") or ""),
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
    )


def _post_from_payload(row: dict) -> PostBattleVM:
    return PostBattleVM(
        battle_number=int(row["battle_number"]),
        complete=bool(row.get("complete") or False),
        active_step=int(row.get("active_step") or 0),
        completed_steps={int(value) for value in row.get("completed_steps") or ()},
        review_open=bool(row.get("review_open") or False),
    )


def _inventory_from_payload(row: dict) -> InventoryItemVM:
    return InventoryItemVM(
        id=str(row["id"]),
        name=str(row["name"]),
        category=str(row.get("category") or ""),
        owned=int(row.get("owned") or 0),
        equipped=int(row.get("equipped") or 0),
        stash=int(row.get("stash") or 0),
        value=int(row.get("value") or 0),
        rarity=row.get("rarity"),
    )


def export_campaign_summary(path, state: AppState) -> Path:
    """Escribe un resumen Markdown legible del estado actual de la campaña."""
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
            lines.append("  - Equipment: " + ", ".join(warrior.equipment))
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
