"""campaign.domain.battle_service: recording a battle.

Pure use case over the campaign model: validates the table facts, derives the
snapshot numbers, appends the ``BattleVM`` node and opens its pending
post-battle with the scenario loot and hireling-upkeep follow-ups. The KB
enters only through the read model passed as ``port``; no UI, locale or
filesystem dependency exists here.
"""
from __future__ import annotations

from datetime import date

from mordheim_campaign.domain.models import BattleVM, CampaignVM, InventoryItemVM, PostBattleVM


def record_battle(
    campaign: CampaignVM,
    port,
    *,
    scenario_id: str,
    scenario_name: str,
    opponent: str,
    result: str,
    xp_delta: int,
    casualties: int,
    gold_delta: int = 0,
    wyrdstone: int = 0,
    opponent_rating: int | None = None,
    notes: str = "",
    out_of_action_ids: list[str] | None = None,
    per_group_casualties: dict[str, int] | None = None,
    xp_awards: dict[str, int] | None = None,
    scenario_results: dict | None = None,
    available_warriors: list | None = None,
    unavailable_rows: list[tuple] | None = None,
    opponent_band_id: str = "",
) -> tuple[bool, str]:
    """Record a played battle and open its pending post-battle.

    Table facts only: the scenario comes from the KB catalogue (already
    validated by the caller through ``port``) and the derived numbers (rating,
    models) snapshot the warband *before* the post-battle mutations. The
    resulting ``PostBattleVM`` is the node the eight-step sequence then
    transforms into the next immutable state.

    ``available_warriors``/``unavailable_rows`` are the pre-battle availability
    computed by :func:`battle_availability`; passing them keeps this service
    free of dialog-working-state knowledge (the pending battle-entry draft
    stays in the application layer).
    """
    if campaign.is_draft:
        return False, "Commit the initial warband before recording battles."
    if campaign.pending_post_battle is not None:
        return False, (
            f"Post-Battle #{campaign.pending_post_battle.battle_number} is still pending; "
            "commit it before recording the next battle."
        )
    known = {known_id for known_id, _name, _mode in port.scenario_options()}
    if scenario_id not in known:
        return False, f"Unknown scenario: {scenario_id}"
    result = result.strip().casefold().capitalize()
    if result not in ("Victory", "Defeat", "Draw"):
        return False, "Result must be Victory, Defeat or Draw."
    available = available_warriors if available_warriors is not None else list(campaign.warriors)
    unavailable = unavailable_rows if unavailable_rows is not None else []
    available_ids = {warrior.id for warrior in available}
    known_ids = {warrior.id for warrior in campaign.warriors}
    submitted_ids = set(out_of_action_ids or ()) | set((per_group_casualties or {}).keys()) | set((xp_awards or {}).keys())
    # Unknown ids are simply ignored by the post-battle filter; only ids
    # naming a real warrior that cannot receive results are rejected.
    invalid_ids = submitted_ids & (known_ids - available_ids)
    if invalid_ids:
        names = [warrior.name for warrior, _reason, _temporary in unavailable if warrior.id in invalid_ids]
        return False, f"Unavailable warriors cannot receive battle results: {', '.join(names or sorted(invalid_ids))}."
    number = campaign.next_battle_number
    base = campaign.current_state
    opponent_name = opponent.strip() or "Unknown opponent"
    if not opponent_band_id:
        opponent_band_id = next((
            option.band_id for option in port.options()
            if option.name.casefold() == opponent_name.casefold()
        ), "")
    battle = BattleVM(
        number=number,
        date=date.today().strftime("%d %b %Y"),
        scenario=scenario_name or scenario_id,
        opponent=opponent_name,
        opponent_band_id=opponent_band_id,
        result=result,
        gold_delta=int(gold_delta),
        wyrdstone=max(0, int(wyrdstone)),
        xp_delta=max(0, int(xp_delta)),
        casualties=max(0, int(casualties)),
        advances=0,
        rating_before=base.rating,
        rating_after=base.rating,
        models_before=sum(warrior.quantity for warrior in available),
        models_after=base.models,
        notes=notes.strip(),
        opponent_rating=opponent_rating,
        out_of_action_ids=list(out_of_action_ids) if out_of_action_ids is not None else None,
        per_group_casualties=dict(per_group_casualties or {}),
        xp_awards={str(key): max(0, int(value)) for key, value in dict(xp_awards or {}).items()},
        scenario_results=dict(scenario_results or {}),
        participants=[
            {
                "id": warrior.id, "name": warrior.name, "kind": warrior.kind,
                "quantity": warrior.quantity, "profile_name": warrior.profile_name,
                "condition": warrior.condition or "",
            }
            for warrior in available
        ],
        absentees=[
            {
                "id": warrior.id, "name": warrior.name, "kind": warrior.kind,
                "quantity": warrior.quantity, "reason": reason,
                "remaining_before": warrior.games_to_miss,
            }
            for warrior, reason, _temporary in unavailable
        ],
    )
    if battle.out_of_action_ids is not None:
        battle.casualties = len(battle.out_of_action_ids)
    elif battle.per_group_casualties:
        battle.casualties = sum(battle.per_group_casualties.values())
        battle.out_of_action_ids = [
            warrior_id
            for warrior_id, count in battle.per_group_casualties.items()
            for _ in range(count)
        ]
    campaign.battles.append(battle)
    opponent_key = f"{battle.opponent_band_id} {battle.opponent}".casefold()
    retained_rules = []
    for rule in campaign.special_rules:
        triggers = [str(value).casefold() for value in rule.get("consume_when_opponent_contains") or ()]
        applies = not triggers or any(value in opponent_key for value in triggers)
        expires = rule.get("expires_after_battles")
        if expires is None or not applies:
            retained_rules.append(rule)
            continue
        remaining = int(expires) - 1
        if remaining > 0:
            rule["expires_after_battles"] = remaining
            retained_rules.append(rule)
    campaign.special_rules[:] = retained_rules
    for warrior, _reason, temporary in unavailable:
        if temporary:
            continue
        warrior.games_to_miss = max(0, warrior.games_to_miss - 1)
        if warrior.games_to_miss == 0:
            warrior.absence_reason = ""
    post_battle = PostBattleVM(battle_number=number, complete=False)
    _apply_recorded_scenario_loot(campaign, port, battle, post_battle)
    for warrior in campaign.warriors:
        if warrior.kind != "hireling" or not warrior.upkeep_resources:
            continue
        post_battle.pending_follow_ups.append({
            "id": f"upkeep:{number}:{warrior.id}", "step": 6, "type": "hireling_upkeep",
            "warrior_id": warrior.id, "costs": [[key, value] for key, value in warrior.upkeep_resources],
            "description": f"Pay {warrior.name}'s upkeep or dismiss the Hired Sword.",
        })
    campaign.post_battles.append(post_battle)
    return True, f"Battle #{number} recorded · {battle.scenario} vs. {battle.opponent} ({result})."


def battle_availability(campaign: CampaignVM, resolved_checks: dict) -> tuple[list, list[tuple]]:
    """Who can fight the next battle, from absences and pre-battle checks.

    ``resolved_checks`` maps ``"<warrior_id>:<check_id>"`` to the recorded roll
    result of the pending battle-entry draft (application working state); an
    unresolved check never blocks a warrior here.
    """
    available = []
    unavailable: list[tuple] = []
    for warrior in campaign.warriors:
        if warrior.games_to_miss > 0:
            unavailable.append((warrior, warrior.absence_reason or "Injury", False))
            continue
        failed = any(
            bool(resolved_checks.get(f"{warrior.id}:{check.get('check_id')}", {}).get("misses_battle"))
            for check in warrior.battle_start_checks
        )
        if failed:
            unavailable.append((warrior, "Old Battle Wound", True))
        else:
            available.append(warrior)
    return available, unavailable


def pending_battle_start_checks(campaign: CampaignVM, resolved_checks: dict) -> list[tuple[object, dict]]:
    """Pre-battle injury checks of available warriors not yet resolved."""
    return [
        (warrior, check)
        for warrior in campaign.warriors
        if warrior.games_to_miss <= 0
        for check in warrior.battle_start_checks
        if f"{warrior.id}:{check.get('check_id')}" not in resolved_checks
    ]


def _apply_recorded_scenario_loot(campaign: CampaignVM, port, battle: BattleVM, post_battle: PostBattleVM) -> None:
    """Apply normalized KB scenario rewards to the pending campaign state."""
    results = battle.scenario_results or {}
    summaries = []
    for reward in results.get("additional_rewards") or ():
        kind = str(reward.get("kind") or "")
        quantity = max(0, int(reward.get("quantity") or 0))
        source = str(reward.get("source") or "scenario")
        source_label = "House rule" if source == "house_rule" else "Scenario"
        if kind == "resource" and reward.get("resource") == "gold_crowns":
            battle.gold_delta += quantity
            post_battle.gold_delta += quantity
            summaries.append(f"{source_label}: +{quantity} gc")
            continue
        if kind == "resource" and reward.get("resource") == "wyrdstone_fragments":
            battle.wyrdstone += quantity
            post_battle.wyrdstone_delta += quantity
            summaries.append(f"{source_label}: +{quantity} wyrdstone")
            continue
        if kind == "exploration":
            post_battle.step_state["scenario_exploration"] = {
                "extra_dice": int(reward.get("extra_dice") or 0),
                "reroll_all": bool(reward.get("reroll_all")),
            }
            summaries.append("scenario exploration rule enabled")
            continue
        if kind not in {"item", "special"} or quantity <= 0:
            continue
        if kind == "special":
            special_id = str(reward.get("special_id") or "")
            no_reward = ("nothing" in special_id or "failure" in special_id or "illusions" in special_id)
            if no_reward:
                summaries.append(str(reward.get("label") or "No reward"))
                continue
            if "magical-artefact" in special_id:
                for index in range(quantity):
                    post_battle.pending_follow_ups.append({
                        "id": f"scenario:{battle.number}:{special_id}:{index + 1}", "step": 2,
                        "type": "exploration_followup", "queue": [{"type": "magical_artefact_table"}],
                        "messages": [str(reward.get("label") or "Magical artefact found")],
                    })
                summaries.append("magical artefact roll pending")
                continue
            if special_id == "scenario.assault-on-the-rock.reward":
                forbidden = campaign.band_id in {"sisters-of-sigmar", "witch-hunters"} or any(
                    "priest of morr" in " ".join((warrior.name, warrior.profile_name,
                                                  *warrior.skills, *warrior.special_rules)).casefold()
                    for warrior in campaign.warriors
                )
                if forbidden:
                    summaries.append("Tome of Magic cannot be used by this warband")
                else:
                    post_battle.pending_follow_ups.append({
                        "id": f"scenario:{battle.number}:tome-of-magic", "step": 2,
                        "type": "scenario_spell_reward", "mandatory": True,
                        "description": "Choose a Hero and exactly two spells granted by the Tome of Magic.",
                    })
                    summaries.append("Tome of Magic spell selection pending")
                continue
            if special_id == "scenario.the-item-lost.reward":
                post_battle.pending_follow_ups.append({
                    "id": f"scenario:{battle.number}:wand-of-phyrros", "step": 2,
                    "type": "exploration_followup", "mandatory": True, "messages": [],
                    "queue": [{"type": "grant_special_item", "recipient": "hero",
                               "item_id": "scenario_reward.wand_of_phyrros", "name": "Wand of Phyrros",
                               "text": str(reward.get("rule") or reward.get("label") or "")}],
                })
                summaries.append("Wand of Phyrros bearer selection pending")
                continue
            if special_id == "scenario.encampment-raid.reward":
                post_battle.pending_follow_ups.append({
                    "id": f"scenario:{battle.number}:encampment", "step": 2,
                    "type": "scenario_encampment", "mandatory": True,
                    "description": "Choose whether to destroy or occupy the captured camp; add captured stash items in Equipment.",
                })
                summaries.append("captured camp decision pending")
                continue
            if special_id == "scenario.the-night-of-the-headless-one.reward":
                item_id = "scenario_reward.skull_of_the_headless_one"
                stock = next((entry for entry in campaign.inventory if entry.id == item_id), None)
                if stock is None:
                    stock = InventoryItemVM(item_id, "Skull of the Headless One", "Scenario Reward",
                                            0, 0, 0, 0, "Unique",
                                            [str(reward.get("rule") or reward.get("label") or "")])
                    campaign.inventory.append(stock)
                stock.owned += quantity; stock.stash += quantity
                summaries.append(f"+{quantity} Skull of the Headless One")
                continue
            if any(token in special_id for token in ("worthless-inventories", "straggler-", "encampment-raid")):
                text = str(reward.get("rule") or reward.get("label") or special_id)
                campaign.special_rules.append({
                    "source": f"scenario:{battle.number}", "text": text,
                    "expires_after_battles": None, "consume_when_opponent_contains": [],
                })
                summaries.append(text)
                continue
        canonical_special_items = {
            "dispel-scroll": "dispelling_scroll",
            "holy-or-unholy-relic": "holy_relic",
        }
        item_id = str(reward.get("item_id") or canonical_special_items.get(
            str(reward.get("special_id") or ""), f"scenario_reward.{reward.get('special_id') or 'special'}"
        ))
        stock = next((entry for entry in campaign.inventory if entry.id == item_id), None)
        if stock is None:
            name = port.item_name(item_id) or str(reward.get("label") or item_id.replace("_", " ").title())
            stock = InventoryItemVM(item_id, name, "Scenario Reward", 0, 0, 0, 0)
            campaign.inventory.append(stock)
        if kind == "special":
            rule = str(reward.get("rule") or reward.get("label") or "").strip()
            if rule and rule not in stock.special_rules:
                stock.special_rules.append(rule)
        stock.owned += quantity
        stock.stash += quantity
        summaries.append(f"{source_label}: +{quantity} {stock.name}")
    if summaries:
        post_battle.log_event(2, "scenario_reward", ", ".join(summaries))
