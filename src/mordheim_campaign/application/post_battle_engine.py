"""application.post_battle_engine: the write side of a pending post-battle.

The read side (`post_battle_resolution` / `post_battle_catalogue`) turns dice
and choices into outcomes; this module applies those outcomes to the campaign
— roster, treasury, wyrdstone, hires and stash — and commits the final state.

Design rules:

- Working totals live on the persisted :class:`PostBattleVM` (``gold_delta``,
  ``wyrdstone_delta``, ``wyrdstone_sold``, ``sale_resolved``, ``veteran_pool``)
  so a mid-sequence save/load resumes exactly where the player was. Roster and
  inventory mutations apply *immediately* to the campaign, because those lists
  *are* the current warband; the immutable part stays in the historical
  ``states`` snapshots, which are only ever appended.
- Every mutation returns ``(ok, message)`` and never silently guesses: a
  variable-cost item, a non-gold hiring fee or a missing Mercenary variant is
  an explicit rejection, never a 0 gc assumption.
- The engine reads the KB exclusively through ``KnowledgePort``; it does not
  import Tkinter or YAML.
"""
from __future__ import annotations

import copy
from datetime import date
from typing import TYPE_CHECKING

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_resolution import SeriousInjuryOutcome
from mordheim_campaign.domain.models import EquipmentEntryVM, InventoryItemVM, WarbandStateVM, WarriorVM, unique_warrior_name
from mordheim_campaign.domain.builders import warrior_vm

if TYPE_CHECKING:
    from mordheim_campaign.application.post_battle_catalogue import HirelingOffer
    from mordheim_campaign.domain.models import CampaignVM, PostBattleVM

#: Full characteristic names used by the KB effect types -> display keys.
_CHARACTERISTIC_KEYS = {
    "movement": "M", "weapon_skill": "WS", "ballistic_skill": "BS",
    "strength": "S", "toughness": "T", "wounds": "W", "initiative": "I",
    "attacks": "A", "leadership": "Ld",
}

NEW_STATE_STEPS = 8


def _today() -> str:
    return date.today().strftime("%d %b %Y")


class PostBattleEngine:
    """Apply post-battle outcomes to one warband and commit its next state.

    ``campaign`` and ``post`` are the live objects the UI edits; all mutations
    go through them so the same code underlies the GUI and the tests.
    """

    #: Post-battle step index of each engine mutation, for the event log.
    STEP_INJURIES = 0
    STEP_EXPERIENCE = 1
    STEP_EXPLORATION = 2
    STEP_SELL = 3
    STEP_VETERANS = 4
    STEP_SEARCHES = 5
    STEP_RECRUITMENT = 6
    STEP_EQUIPMENT = 7

    def __init__(self, port: KnowledgePort, campaign: "CampaignVM", post: "PostBattleVM | None") -> None:
        self.port = port
        self.campaign = campaign
        self.post = post

    # ------------------------------------------------------------ projections

    def _log(self, step: int, action: str, message: str, **ids) -> None:
        """Append one structured entry to the pending sequence event log."""
        if self.post is not None:
            self.post.log_event(step, action, message, **ids)

    def _base_state(self) -> WarbandStateVM | None:
        """The immutable state this post-battle transforms (State #N-1).

        Falls back to the campaign's current state when State #N-1 has no
        snapshot (a battle recorded from the table after a skipped sequence).
        """
        if self.post is None or not self.campaign.states:
            return None
        try:
            return self.campaign.state(self.post.battle_number - 1)
        except StopIteration:
            return self.campaign.current_state

    def projected_gold(self) -> int:
        base = self._base_state()
        return (base.gold + self.post.gold_delta) if base is not None and self.post else 0

    def projected_shards(self) -> int:
        base = self._base_state()
        return (base.wyrdstone + self.post.wyrdstone_delta - self.post.wyrdstone_sold) if base is not None and self.post else 0

    def projected_models(self) -> int:
        """All deployed models, including Hired Swords (battle/Rout usage)."""
        return sum(row.quantity for row in self.campaign.warriors)

    def projected_warband_members(self) -> int:
        """Own-band models used by roster limits and wyrdstone income."""
        return sum(row.quantity for row in self.campaign.warriors if row.kind != "hireling")

    def effective_maximum_models(self) -> int:
        return self.campaign.maximum_models + sum(
            row.maximum_models_modifier for row in self.campaign.warriors if row.kind == "hireling"
        )

    def projected_heroes(self) -> int:
        return sum(row.quantity for row in self.campaign.warriors if row.kind == "hero")

    def eligible_exploration_heroes(self, battle) -> int:
        """Heroes still able to explore after this battle's Out of Action results."""
        heroes = {row.id for row in self.campaign.warriors if row.kind == "hero"}
        if battle.out_of_action_ids is None:
            # Old/incomplete battle records cannot identify which casualties
            # were heroes, so do not subtract unrelated models.
            return len(heroes)
        unavailable = heroes.intersection(battle.out_of_action_ids)
        return max(0, len(heroes) - len(unavailable))

    def projected_henchmen(self) -> int:
        return sum(row.quantity for row in self.campaign.warriors if row.kind == "henchman")

    def projected_experience(self) -> int:
        return sum(row.experience * row.quantity for row in self.campaign.warriors if row.kind != "hireling")

    def projected_rating(self) -> int:
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        members = PostBattleResolver(self.port).warband_rating(
            self.projected_warband_members(), self.projected_experience()
        )
        hirelings = sum(
            self.port.hireling_roster_values(row.profile_id, row.experience)[0]
            for row in self.campaign.warriors if row.kind == "hireling"
        )
        return members + hirelings

    def projections(self) -> dict[str, int | str]:
        return {
            "gold": self.projected_gold(),
            "shards": self.projected_shards(),
            "rating": self.projected_rating(),
            "models": self.projected_models(),
            "heroes": self.projected_heroes(),
            "henchmen": self.projected_henchmen(),
            "experience": self.projected_experience(),
        }

    # ---------------------------------------------------------------- injuries

    def apply_serious_injury(self, warrior_id: str, outcome: SeriousInjuryOutcome) -> tuple[bool, str]:
        """Apply one chart row to a warrior; returns what changed (or why not)."""
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"

        pending_before = len(self.post.pending_follow_ups)
        notes = self._apply_injury_effects(warrior, outcome)
        # Typed effects register their own structured interaction. Only retain
        # the generic fallback when the KB describes a follow-up we do not yet
        # model more specifically.
        if outcome.follow_up and len(self.post.pending_follow_ups) == pending_before:
            self._register_injury_followup(warrior_id, outcome)
        self._log(self.STEP_INJURIES, "serious_injury", f"{warrior.name}: {outcome.result}", warrior_id=warrior_id, result_id=outcome.result_id)
        if not notes and not outcome.follow_up:
            return True, f"{warrior.name}: no lasting effect on the roster."
        message = f"{warrior.name}: {' · '.join(notes)}." if notes else f"{warrior.name}: {outcome.result}."
        if outcome.follow_up:
            message += f" Follow-up pending: {outcome.follow_up}"
        return True, message

    def _register_injury_followup(self, warrior_id: str, outcome: SeriousInjuryOutcome) -> None:
        """Fallback record for callers that apply an unresolved injury directly."""
        if self.post is None:
            return
        followup_id = f"injury:{warrior_id}:{outcome.result_id}"
        if any(str(row.get("id")) == followup_id for row in self.post.pending_follow_ups):
            return
        self.post.pending_follow_ups.append({
            "id": followup_id, "step": self.STEP_INJURIES, "type": "injury_roll",
            "warrior_id": warrior_id, "result_id": outcome.result_id,
            "description": outcome.follow_up or "Resolve the injury follow-up roll.",
        })

    def _apply_injury_effects(self, warrior: "WarriorVM", outcome: SeriousInjuryOutcome) -> list[str]:
        """Apply the typed effects of one chart row; returns change notes."""
        notes: list[str] = []
        for effect in outcome.effects_raw:
            kind = str(effect.get("type") or "")
            if kind == "roster.remove_warrior":
                if warrior.kind == "henchman" and warrior.quantity > 1:
                    warrior.quantity -= 1
                    notes.append("the group loses one member")
                else:
                    self._discard_carried_equipment(warrior, weapons_and_armour_only=False)
                    self.campaign.warriors.remove(warrior)
                    notes.append(f"{warrior.name} leaves the roster")
            elif kind == "warrior.characteristic_modifier":
                key = _CHARACTERISTIC_KEYS.get(str(effect.get("characteristic") or ""))
                if key is not None:
                    modifier = int(effect.get("modifier") or 0)
                    warrior.stat_modifiers[key] = warrior.stat_modifiers.get(key, 0) + modifier
                    warrior.injury_records.append({
                        "result_id": outcome.result_id,
                        "name": outcome.result,
                        "characteristic": key,
                        "modifier": modifier,
                    })
                    notes.append(f"{key} {modifier:+d}")
                    if outcome.result_id.endswith("31-blinded-in-one-eye"):
                        self._add_follow_up(self.STEP_INJURIES, {
                            "type": "eye_injury", "warrior_id": warrior.id,
                            "description": f"{warrior.name}: determine which eye was lost.",
                        })
            elif kind == "warrior.add_condition":
                warrior.condition = "Injured"
                warrior.condition_detail = str(effect.get("condition_id") or "lasting condition")
                notes.append("gains a lasting condition")
            elif kind == "warrior.miss_games":
                games = effect.get("games") or {}
                value = int(games.get("value") or 1) if isinstance(games, dict) else int(games or 1)
                warrior.games_to_miss += value
                warrior.absence_reason = outcome.result
                notes.append(f"misses the next {value} game{'s' if value != 1 else ''} ({warrior.games_to_miss} pending in total)")
            elif kind == "warrior.equipment_limit":
                limit = effect.get("maximum_one_handed_weapons")
                detail = f"max {limit} one-handed weapon(s)" if limit is not None else str(effect.get("type"))
                warrior.condition = "Injured"
                warrior.condition_detail = f"Arm wound ({detail})"
                notes.append(f"arm wound: {detail}")
            elif kind == "warrior.battle_start_check":
                failure = effect.get("failure_when") or {}
                check = {
                    "check_id": str(effect.get("check_id") or ""),
                    "dice": dict(effect.get("dice") or {}),
                    "failure_when": dict(failure),
                    "on_failure": [dict(row) for row in effect.get("on_failure") or ()],
                }
                if not any(row.get("check_id") == check["check_id"] for row in warrior.battle_start_checks):
                    warrior.battle_start_checks.append(check)
                notes.append("Old Battle Wound check required before every battle")
            elif kind == "prisoner.create":
                self._add_follow_up(self.STEP_INJURIES, {
                    "type": "prisoner",
                    "description": (
                        f"{warrior.name} was taken captive by the opposing warband: ransom, "
                        "exchange, or sell to slavers (D6x5 gc) before the next battle."
                    ),
                    "warrior_id": warrior.id,
                })
                notes.append("taken captive")
            elif kind == "relationship.add_hatred":
                self._add_follow_up(self.STEP_INJURIES, {
                    "type": "relationship",
                    "description": f"{warrior.name} gains hatred (record the target with the warband relations).",
                    "warrior_id": warrior.id,
                    "target_selector": str(effect.get("target_selector") or ""),
                })
                notes.append("gains a hatred")
            elif kind == "encounter.trigger":
                encounter_id = str(effect.get("encounter_id") or "")
                self._add_follow_up(self.STEP_INJURIES, {
                    "type": "encounter",
                    "encounter_id": encounter_id,
                    "description": (
                        f"{warrior.name}: fight a Pit Fighter and record whether the warrior wins or loses."
                        if encounter_id == "campaign.encounter.sold-to-the-pits"
                        else f"{warrior.name}: a follow-up encounter is triggered (resolve with the scenario rules)."
                    ),
                    "warrior_id": warrior.id,
                })
                notes.append("encounter triggered")
            elif kind == "reward.grant":
                resources = effect.get("resources") or {}
                experience = (resources.get("experience") or {}).get("value")
                if experience is not None:
                    warrior.experience += int(experience)
                    self.sync_pending_advances([warrior])
                    notes.append(f"gains {int(experience)} Experience")
            elif kind == "equipment.disposition":
                scope = str(effect.get("scope") or "")
                disposition = str(effect.get("disposition") or "lost")
                if scope == "carried_by_subject" and warrior.equipment:
                    lost = list(warrior.equipment)
                    warrior.equipment.clear()
                    notes.append(f"{disposition}: {' · '.join(item.name for item in lost)}")
            else:
                notes.append(str(effect.get("type") or "").replace("_", " "))
        return notes

    def _add_follow_up(self, step: int, payload: dict) -> dict:
        """Append one pending follow-up row with a unique id."""
        if self.post is None:
            return payload
        identifier = f"{payload.get('type')}:{len(self.post.pending_follow_ups) + 1}"
        row = {"id": identifier, "step": step, **payload}
        self.post.pending_follow_ups.append(row)
        return row

    def resolve_injury_followup(self, followup_id: str, roll: int) -> tuple[bool, str]:
        """Resolve a persisted injury follow-up (subtable or repeat reroll)."""
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups if item.get("id") == followup_id), None)
        if row is None:
            return False, "Unknown follow-up."
        table = str(row.get("table") or "hero")
        result_id = str(row.get("result_id") or "")
        resolver = self._resolver()
        outcome = resolver.resolve_injury_subtable(table, result_id, roll)
        if outcome is None:
            outcome = resolver.resolve_repeat_reroll(table, result_id, roll)
            if outcome is None:
                return False, f"Roll {roll} lands on an excluded result; roll again."
        self.post.pending_follow_ups.remove(row)
        warrior = next((item for item in self.campaign.warriors if item.id == str(row.get("warrior_id"))), None)
        if warrior is None:
            return True, f"Follow-up resolved: {outcome.result} (the warrior is no longer on the roster)."
        notes = self._apply_injury_effects(warrior, outcome)
        self._log(self.STEP_INJURIES, "injury_followup", f"{warrior.name}: {outcome.result}", warrior_id=warrior.id, result_id=outcome.result_id)
        message = f"{warrior.name}: {outcome.result}" + (f" ({' - '.join(notes)})" if notes else "")
        if outcome.follow_up:
            self._register_injury_followup(warrior.id, outcome)
            message += f". Follow-up pending: {outcome.follow_up}"
        return True, message

    def resolve_sold_to_pits(self, followup_id: str, *, won: bool, injury_roll: int | None = None) -> tuple[bool, str]:
        """Commit the table result of the Sold to the Pits encounter."""
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups if str(item.get("id")) == followup_id), None)
        if row is None or row.get("encounter_id") != "campaign.encounter.sold-to-the-pits":
            return False, "Unknown Sold to the Pits encounter."
        warrior = next((item for item in self.campaign.warriors if item.id == str(row.get("warrior_id"))), None)
        if warrior is None:
            return False, "The warrior is no longer on the roster."

        self.post.pending_follow_ups.remove(row)
        if won:
            self.post.gold_delta += 50
            warrior.experience += 2
            message = f"{warrior.name} wins in the pits: +50 gc and +2 Experience."
            self._log(self.STEP_INJURIES, "sold_to_pits", message, warrior_id=warrior.id, result="won")
            return True, message

        tens, ones = divmod(int(injury_roll or 0), 10)
        if not (1 <= tens <= 6 and 1 <= ones <= 6):
            self.post.pending_follow_ups.append(row)
            return False, "A valid D66 result is required after losing in the pits."

        roll = int(injury_roll)
        injury_message = "no additional lasting injury"
        if roll <= 35:
            outcome = self._resolver().resolve_hero_serious_injury(roll)
            ok, injury_message = self.apply_serious_injury(warrior.id, outcome)
            if not ok:
                self.post.pending_follow_ups.append(row)
                return False, injury_message

        still_present = warrior in self.campaign.warriors
        lost = self._discard_carried_equipment(warrior, weapons_and_armour_only=still_present)
        equipment_text = ", ".join(lost) if lost else "no weapons or armour carried"
        message = f"{warrior.name} loses in the pits ({roll}): {injury_message}; lost equipment: {equipment_text}."
        self._log(self.STEP_INJURIES, "sold_to_pits", message, warrior_id=warrior.id, result="lost", roll=roll)
        return True, message

    def resolve_captured(self, followup_id: str, *, resolution: str, ransom: int = 0,
                         disposition: str = "other") -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups if str(item.get("id")) == followup_id and item.get("type") == "prisoner"), None)
        if row is None:
            return False, "Unknown captured-warrior follow-up."
        warrior = next((item for item in self.campaign.warriors if item.id == str(row.get("warrior_id"))), None)
        if warrior is None:
            return False, "The captured warrior is no longer on the roster."
        resolution = resolution.casefold()
        if resolution == "ransom":
            ransom = max(0, int(ransom))
            if ransom > self.projected_gold():
                return False, f"The warband cannot pay a ransom of {ransom} gc."
            self.post.gold_delta -= ransom
            message = f"{warrior.name} was ransomed for {ransom} gc and returns with all equipment."
        elif resolution == "exchange":
            message = f"{warrior.name} was exchanged or released and returns with all equipment."
        elif resolution == "lost":
            dispositions = {
                "enslaved": "sold into slavery", "executed": "executed",
                "zombie": "raised as a Zombie", "sacrificed": "sacrificed",
                "other": "otherwise permanently lost",
            }
            if disposition not in dispositions:
                return False, "Choose what happened to the captured warrior."
            lost = self._discard_carried_equipment(warrior, weapons_and_armour_only=False)
            self.campaign.warriors.remove(warrior)
            message = (f"{warrior.name} was {dispositions[disposition]}; "
                       f"captured equipment: {', '.join(lost) if lost else 'none'}.")
        else:
            return False, "Choose ransom, exchange, or permanent loss."
        self.post.pending_follow_ups.remove(row)
        self._log(self.STEP_INJURIES, "captured", message, warrior_id=warrior.id,
                  resolution=resolution, disposition=disposition if resolution == "lost" else "")
        return True, message

    def resolve_hatred_target(self, followup_id: str, target: str) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups if str(item.get("id")) == followup_id and item.get("type") == "relationship"), None)
        if row is None:
            return False, "Unknown Bitter Enmity follow-up."
        target = target.strip()
        if not target:
            return False, "Enter the warrior, warband, or warband type hated."
        warrior = next((item for item in self.campaign.warriors if item.id == str(row.get("warrior_id"))), None)
        if warrior is None:
            return False, "The warrior is no longer on the roster."
        if target not in warrior.hatreds:
            warrior.hatreds.append(target)
        self.post.pending_follow_ups.remove(row)
        message = f"{warrior.name} permanently hates {target}."
        self._log(self.STEP_INJURIES, "bitter_enmity", message, warrior_id=warrior.id, target=target)
        return True, message

    def resolve_lost_eye(self, followup_id: str, eye: str) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups if str(item.get("id")) == followup_id and item.get("type") == "eye_injury"), None)
        if row is None:
            return False, "Unknown eye-injury follow-up."
        warrior = next((item for item in self.campaign.warriors if item.id == str(row.get("warrior_id"))), None)
        if warrior is None:
            return False, "The warrior is no longer on the roster."
        eye = eye.casefold()
        if eye not in {"left", "right"} or eye in warrior.lost_eyes:
            return False, "Choose the warrior's remaining eye."
        warrior.lost_eyes.append(eye)
        self.post.pending_follow_ups.remove(row)
        if len(warrior.lost_eyes) >= 2:
            self._discard_carried_equipment(warrior, weapons_and_armour_only=False)
            self.campaign.warriors.remove(warrior)
            message = f"{warrior.name} lost the remaining eye and retires from the warband."
        else:
            message = f"{warrior.name} lost the {eye} eye."
        self._log(self.STEP_INJURIES, "lost_eye", message, warrior_id=warrior.id, eye=eye)
        return True, message

    def _discard_carried_equipment(self, warrior: "WarriorVM", *, weapons_and_armour_only: bool) -> list[str]:
        categories = {row.id: row.category.casefold() for row in self.campaign.inventory}
        discarded = []
        kept = []
        for equipment in warrior.equipment:
            category = categories.get(equipment.item_id, "")
            loses_item = not weapons_and_armour_only or category in {"weapon", "weapons", "armour", "armor"}
            if not loses_item:
                kept.append(equipment)
                continue
            discarded.append(equipment.name)
            inventory = next((row for row in self.campaign.inventory if row.id == equipment.item_id), None)
            if inventory is not None:
                inventory.equipped = max(0, inventory.equipped - equipment.quantity)
                inventory.owned = max(0, inventory.owned - equipment.quantity)
        warrior.equipment = kept
        return discarded

    def _resolver(self):
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        return PostBattleResolver(self.port)

    # ------------------------------------------------------------- experience

    def apply_battle_experience(self) -> tuple[bool, str]:
        """Apply the recorded common battle award once to the surviving roster."""
        if self.post is None:
            return False, "No pending post-battle."
        if self.post.experience_applied:
            return True, "Battle experience already applied."
        battle = self.campaign.battle(self.post.battle_number)
        self.post.experience_applied = True
        if battle.xp_awards:
            for warrior in self.campaign.warriors:
                award = int(battle.xp_awards.get(warrior.id, 0))
                if award > 0:
                    warrior.experience += award
            self.sync_pending_advances()
            self._log(self.STEP_EXPERIENCE, "experience", "Per-warrior scenario awards applied.")
            return True, "Per-warrior scenario awards applied (see the battle record)."
        amount = max(0, int(battle.xp_delta))
        for warrior in self.campaign.warriors:
            warrior.experience += amount
        self.sync_pending_advances()
        self._log(self.STEP_EXPERIENCE, "experience", f"{amount} XP awarded to every surviving warrior.")
        return True, f"{amount} XP applied to each surviving warrior."

    def add_xp(self, warrior_id: str, amount: int) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"
        amount = max(0, int(amount))
        warrior.experience += amount
        message = f"{warrior.name} gains {amount} XP (now {warrior.experience})."
        seeded = self.sync_pending_advances([warrior])
        if seeded:
            message += f" Advance roll earned ({warrior.experience} XP)."
        return True, message

    # -------------------------------------------------------------- advances

    #: Race the warband-side heuristics resolve for racial maximums; the KB
    #: declares maximums per profile race (``catalog/rules/racial-maximums.yaml``).
    _BAND_RACE = {
        "warband-group.human": "human",
        "warband-group.chaos-human": "human",
        "warband-group.human-mercenary": "human",
        "warband-group.elf": "elf",
        "warband-group.high-elf": "elf",
        "warband-group.dark-elf": "elf",
        "warband-group.dwarf": "dwarf",
        "warband-group.chaos-dwarf": "dwarf",
        "warband-group.skaven": "skaven",
        "warband-group.ogre": "ogre",
        "warband-group.goblin": "goblin",
        "warband-group.orc": "orc",
        "warband-group.halfling": "halfling",
        "warband-group.beastmen": "other_beastmen",
        "warband-group.undead": "human",
    }

    def sync_pending_advances(self, warriors=None) -> int:
        """Seed one pending advance per warrior whose XP crossed a threshold.

        Uses the KB ``advance_thresholds`` ladder (heroes and henchman groups);
        a threshold counts when the warrior's current XP is >= the rung and no
        pending/committed advance for that rung exists yet. Returns how many
        new pending rows were added.
        """
        if self.post is None:
            return 0
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        resolver = PostBattleResolver(self.port)
        rows = list(self.campaign.warriors if warriors is None else warriors)
        added = 0
        for warrior in rows:
            kind = "hero" if warrior.kind == "hero" else "henchman"
            thresholds = resolver.advance_thresholds(kind)
            existing_rungs = {
                int(row.get("threshold"))
                for row in self.post.pending_advances
                if str(row.get("warrior_id")) == warrior.id and row.get("threshold") is not None
            }
            for threshold in thresholds:
                if warrior.experience >= threshold and threshold not in existing_rungs:
                    self.post.pending_advances.append({
                        "warrior_id": warrior.id,
                        "warrior_name": warrior.name,
                        "table": kind,
                        "threshold": int(threshold),
                        "roll_total": None,
                        "subroll": None,
                        "committed": False,
                        "applied_label": "",
                    })
                    added += 1
        return added

    def resolve_pending_advance(self, warrior_id: str, roll_total: int, subroll: int | None = None, *, threshold: int | None = None) -> tuple[bool, str]:
        """Resolve the 2D6 roll (and optional D6 sub-roll) of a pending advance."""
        if self.post is None:
            return False, "No pending post-battle."
        row = self.post.pending_advance_for(warrior_id, threshold)
        if row is None:
            return False, f"No pending advance for: {warrior_id}"
        if row.get("committed"):
            return False, "This advance is already committed."
        if row.get("promotion_setup_pending"):
            return False, "Choose two Hero skill lists before rolling the promoted Hero's advance."
        if row.get("reroll_exclude_promotion") and 10 <= int(roll_total) <= 12:
            self.reset_pending_advance_for_reroll(
                warrior_id, threshold=threshold,
                reason=f"Rolled {roll_total}: the remaining Henchmen must reroll results 10-12.",
            )
            return True, "The remaining Henchmen must reroll results 10-12. Roll again."
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        resolver = PostBattleResolver(self.port)
        kind = str(row.get("table") or "hero")
        outcome = resolver.resolve_advancement(kind, int(roll_total), is_wizard=self.is_wizard(warrior_id))
        row["roll_total"] = int(roll_total)
        if not outcome.final:
            if subroll is None:
                return True, f"{outcome.title}: {outcome.detail}"
            outcome = resolver.resolve_advancement_subroll(kind, int(roll_total), int(subroll))
            row["subroll"] = int(subroll)
        row["promotion_offer"] = bool(outcome.final and outcome.note == "promotion")
        if outcome.final and len(outcome.options) == 1 and outcome.options[0].kind != "promote_henchman":
            # Single deterministic option (one characteristic): commit directly.
            ok, message = self.commit_pending_advance(warrior_id, option_kind=outcome.options[0].kind, threshold=threshold)
            if not ok and ("advance cap" in message or "racial maximum" in message):
                self.reset_pending_advance_for_reroll(warrior_id, threshold=threshold, reason=f"Rolled {roll_total}: {outcome.title} — {message}")
                return True, f"{message} Roll this advance again."
            return ok, message
        return True, f"{outcome.title} · {outcome.detail}" if outcome.detail else outcome.title

    def reset_pending_advance_for_reroll(self, warrior_id: str, *, threshold: int | None = None, reason: str = "Reroll required") -> tuple[bool, str]:
        """Keep the rejected result in history and reopen the same advance roll."""
        if self.post is None:
            return False, "No pending post-battle."
        row = self.post.pending_advance_for(warrior_id, threshold)
        if row is None or row.get("committed"):
            return False, "No unresolved advance can be rerolled."
        row.setdefault("roll_history", []).append(reason)
        row["roll_total"] = None
        row["subroll"] = None
        row["promotion_offer"] = False
        return True, reason

    def is_wizard(self, warrior_id: str) -> bool:
        """True when the KB assigns this warrior's profile a spell lore."""
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None or not warrior.profile_id:
            return False
        return self.port.wizard_lore(warrior.profile_id, self.campaign.band_id) is not None

    def _pending_outcome(self, warrior_id: str, threshold: int | None = None):
        """The resolved KB outcome of a pending advance row (or ``None``)."""
        row = self.post.pending_advance_for(warrior_id, threshold) if self.post is not None else None
        if row is None or row.get("roll_total") is None:
            return None, row
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        resolver = PostBattleResolver(self.port)
        kind = str(row.get("table") or "hero")
        outcome = resolver.resolve_advancement(kind, int(row["roll_total"]), is_wizard=self.is_wizard(warrior_id))
        if not outcome.final and row.get("subroll") is not None:
            outcome = resolver.resolve_advancement_subroll(kind, int(row["roll_total"]), int(row["subroll"]))
        return outcome, row

    def advance_options(self, warrior_id: str, threshold: int | None = None):
        """Selectable options of a resolved pending advance (may be empty)."""
        outcome, _row = self._pending_outcome(warrior_id, threshold)
        return outcome.options if outcome is not None and outcome.final else ()

    def _warrior_race(self, warrior) -> str | None:
        """Race used for racial maximums, resolved from the warband registry."""
        if not self.campaign.band_id:
            return None
        for group in self.port.warband_groups():
            if str(group.get("id") or "") in self._BAND_RACE and self.campaign.band_id in set(group.get("band_ids") or ()):
                return self._BAND_RACE[str(group["id"])]
        return None

    def _is_human_henchman_group(self, warrior) -> bool:
        """Whether a prisoner may legally join this Henchman group.

        The KB currently declares race at warband-group level. Requiring a
        normal equipment list additionally excludes animals, undead and other
        intrinsic-attack profiles inside otherwise human warbands.
        """
        if warrior.kind != "henchman" or self._warrior_race(warrior) != "human":
            return False
        try:
            profile = self.port.profile(self.campaign.collection, self.campaign.band_id, warrior.profile_id)
        except Exception:
            return False
        return bool(profile.equipment_list_ids)

    def _racial_maximum(self, warrior, key: str) -> int | None:
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        race = self._warrior_race(warrior)
        if race is None:
            return None
        table = PostBattleResolver(self.port).racial_maximums().get(race)
        if not table or key not in table:
            return None
        return int(table[key])

    def _henchman_advance_cap(self, warrior, key: str) -> int | None:
        """The starting characteristic of a henchman group member (+1 limit).

        Returns the canonical profile value when the warrior is a henchman
        group row (the rule: never more than +1 over the initial value).
        """
        if warrior.kind != "henchman":
            return None
        try:
            profile = self.port.profile(self.campaign.collection, self.campaign.band_id, warrior.profile_id)
        except Exception:
            return None
        return profile.characteristics.get(key)

    def commit_pending_advance(
        self,
        warrior_id: str,
        *,
        option_kind: str,
        characteristic: str | None = None,
        skill_name: str | None = None,
        spell_id: str | None = None,
        threshold: int | None = None,
    ) -> tuple[bool, str]:
        """Apply one option of a resolved pending advance to the roster.

        ``option_kind`` is ``characteristic_increase`` (``characteristic``
        selects among +1 rows), ``choose_skill`` (``skill_name``) or
        ``generate_spell`` (``spell_id``); every pick is validated against the
        warrior's KB skill access, lore and racial/henchman caps.
        """
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"
        row = self.post.pending_advance_for(warrior_id, threshold)
        if row is None or row.get("roll_total") is None:
            return False, "Resolve the advance roll first."
        if row.get("committed"):
            return False, "This advance is already committed."
        outcome, row = self._pending_outcome(warrior_id, threshold)
        if outcome is None or not outcome.final:
            return False, "The advance roll is not resolved yet."

        if option_kind == "characteristic_increase":
            options = [option for option in outcome.options if option.kind == "characteristic_increase"]
            if not options:
                return False, "This advance does not increase a characteristic."
            if characteristic is not None:
                options = [option for option in options if option.characteristic == characteristic]
                if not options:
                    return False, f"+1 {characteristic} is not offered by this advance."
            if len(options) > 1:
                return False, "This advance offers several characteristics; choose one."
            option = options[0]
            key = option.characteristic or "?"
            if key not in warrior.stats:
                return False, f"Unknown characteristic: {key}"
            current = int(warrior.stats.get(key) or 0)
            cap = self._henchman_advance_cap(warrior, key)
            if cap is not None and current >= cap + 1:
                return False, (
                    f"Henchmen never add more than +1 to {key}: the group starts at {cap} "
                    "and has already reached its advance cap (roll again instead)."
                )
            maximum = self._racial_maximum(warrior, key)
            if maximum is not None and current >= maximum:
                return False, f"{key} {current} is already at the {self._warrior_race(warrior)} racial maximum ({maximum})."
            warrior.stats[key] = current + option.amount
            warrior.stat_advances[key] = warrior.stat_advances.get(key, 0) + option.amount
            row["committed"] = True
            row["applied_label"] = f"+{option.amount} {key}"
            return True, f"{warrior.name} gains +{option.amount} {key} (now {warrior.stats[key]})."

        if option_kind == "choose_skill":
            if not skill_name:
                return False, "Choose a skill to commit."
            skill = self.port.skill_by_name(skill_name)
            if skill is None:
                return False, f"Unknown skill: {skill_name}"
            if skill_name in warrior.skills:
                return False, f"{warrior.name} already knows {skill_name}."
            allowed = set(warrior.skill_access or ())
            if allowed and self.port.skill_table_label(skill) not in allowed:
                return False, f"{skill_name} is not on {warrior.name}'s skill tables ({', '.join(sorted(allowed))})."
            category = str(skill.get("category") or "")
            if category in self.port.banned_skill_categories(self.campaign.band_id, warrior.profile_id):
                return False, f"{skill_name} is forbidden for {warrior.name}: the profile may never acquire {category.title()} skills."
            warrior.skills.append(skill_name)
            row["committed"] = True
            row["applied_label"] = f"Skill: {skill_name}"
            return True, f"{warrior.name} learns {skill_name}."

        if option_kind == "generate_spell":
            if not spell_id:
                return False, "Choose a spell to commit."
            lore = self.port.wizard_lore(warrior.profile_id, self.campaign.band_id)
            if lore is None:
                return False, f"{warrior.name} is not a wizard in the KB lore assignments."
            spell = next((entry for entry in self.port.lore_spells(lore) if str(entry.get("id") or "") == spell_id), None)
            if spell is None:
                return False, f"Spell {spell_id} is not in {warrior.name}'s lore ({lore})."
            name = str(spell.get("name") or spell_id)
            if name in warrior.skills:
                return False, f"{warrior.name} already knows {name} (rolled twice: lower its difficulty by 1)."
            warrior.skills.append(name)
            row["committed"] = True
            row["applied_label"] = f"Spell: {name}"
            return True, f"{warrior.name} learns the spell {name}."

        if option_kind == "duplicate_spell":
            # Rolled a spell already known: the advance is spent lowering the
            # spell's casting difficulty by 1 (persisted per warrior + spell).
            if not spell_id:
                return False, "Choose the duplicated spell."
            lore = self.port.wizard_lore(warrior.profile_id, self.campaign.band_id)
            if lore is None:
                return False, f"{warrior.name} is not a wizard in the KB lore assignments."
            spell = next((entry for entry in self.port.lore_spells(lore) if str(entry.get("id") or "") == spell_id), None)
            if spell is None:
                return False, f"Spell {spell_id} is not in {warrior.name}'s lore ({lore})."
            name = str(spell.get("name") or spell_id)
            if name not in warrior.skills:
                return False, f"{warrior.name} does not know {name}; pick it as a new spell instead."
            modifier = warrior.spell_difficulty_modifiers.get(spell_id, 0) - 1
            warrior.spell_difficulty_modifiers[spell_id] = modifier
            row["committed"] = True
            row["applied_label"] = f"Duplicated spell: {name} (difficulty {modifier:+d})"
            return True, f"{warrior.name} deepens {name}: casting difficulty reduced by 1."

        if option_kind == "promote_henchman":
            return self.promote_henchman(warrior_id)

        if option_kind == "external_resolution":
            row["committed"] = True
            row["applied_label"] = "Resolved outside the application"
            return True, "This advance requires a table-side resolution; it has been recorded as resolved."

        return False, f"Unknown advance option in the KB: {option_kind}"

    # ------------------------------------------------------------- promotion

    #: Pending Lad's Got Talent promotions of this sequence (warrior group ids);
    #: each grants one hero-slot allowance over the static ``hero_limit``.
    def _promotion_hero_allowance(self) -> int:
        """Lad's Got Talent never raises the warband's Hero maximum."""
        return 0

    def promotion_hero_tables(self, warrior_id: str) -> tuple[str, ...]:
        """Warband hero skill-table labels for a promoted member's 2 picks."""
        campaign = self.campaign
        tables: list[str] = []
        for profile in self.port.profiles(campaign.collection, campaign.band_id):
            if profile.kind != "hero":
                continue
            for table in profile.skill_tables:
                if table not in tables:
                    tables.append(table)
        return tuple(tables)

    def promotion_pick_budget(self, warrior_id: str) -> int:
        """Hero skill lists still to choose for a pending promotion."""
        if self.post is None:
            return 0
        row = self.post.pending_advance_for(warrior_id)
        if row is None or not row.get("promotion_setup_pending"):
            return 0
        return max(0, 2 - len(row.get("promotion_tables") or ()))

    def set_promotion_skill_tables(self, warrior_id: str, tables: list[str]) -> tuple[bool, str]:
        """Choose two future skill lists for a Lad's Got Talent Hero."""
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None or warrior.kind != "hero":
            return False, "Promote the group member before choosing skill lists."
        row = self.post.pending_advance_for(warrior_id)
        if row is None or not row.get("promotion_setup_pending"):
            return False, "No pending promotion for this warrior."
        selected = list(dict.fromkeys(str(table) for table in tables))
        available = set(self.promotion_hero_tables(warrior_id))
        if len(selected) != 2:
            return False, "Choose exactly two different Hero skill lists."
        if not set(selected) <= available:
            return False, "Every selected list must be available to Heroes in this warband."
        warrior.skill_access = selected
        row["promotion_tables"] = selected
        row["promotion_setup_pending"] = False
        return True, f"{warrior.name} may use {selected[0]} and {selected[1]}; roll one Hero advance now."

    def promote_henchman(self, warrior_id: str, *, member_name: str | None = None, threshold: int | None = None) -> tuple[bool, str]:
        """The Lad's Got Talent: split one member off the group as a Hero.

        The promoted member keeps the group's type, experience and accumulated
        characteristic increases (``preserve`` in the KB row). The remaining
        group stays a henchman row and its player rerolls this advance
        (``remaining_group.reroll_current_advance_excluding``): the pending row
        resets to unresolved. Promotions bypass the static hero limit through
        ``_promotion_hero_allowance`` (``on_maximum_heroes``).
        """
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"
        if warrior.kind != "henchman":
            return False, "The Lad's Got Talent promotes a henchman group member."
        campaign = self.campaign
        heroes = self.projected_heroes()
        if heroes >= campaign.hero_limit:
            self.reset_pending_advance_for_reroll(
                warrior_id, threshold=threshold,
                reason=f"The warband already has its maximum of {campaign.hero_limit} Heroes.",
            )
            return True, f"Hero maximum reached ({campaign.hero_limit}); reroll this advance."
        try:
            profile = self.port.profile(campaign.collection, campaign.band_id, warrior.profile_id)
        except Exception:
            return False, f"Unknown profile: {warrior.profile_id}"

        promoted_name = member_name or f"{warrior.profile_name} Champion"
        non_uniform = [
            item for item in warrior.equipment
            if item.per_model and item.quantity not in (0, warrior.quantity)
        ]
        if non_uniform:
            names = " · ".join(item.name for item in non_uniform)
            return False, (
                f"{warrior.name} carries a non-uniform loadout ({names}). Normalize the "
                "group's equipment first (assign or return copies) so the promoted "
                "member's share is unambiguous."
            )
        promoted_equipment = []
        for item in warrior.equipment:
            if item.per_model and item.quantity > 0:
                promoted_equipment.append(EquipmentEntryVM(item.item_id, item.name, 1, item.acquisition, item.unit_cost, True, item.transferable))
                item.quantity -= 1
        hero_row = WarriorVM(
            id=f"{warrior.profile_id}#promoted{sum(1 for r in campaign.warriors if r.profile_id == warrior.profile_id)}",
            name=promoted_name,
            profile_name=warrior.profile_name,
            kind="hero",
            stats=dict(warrior.stats),  # preserve accumulated characteristic increases
            equipment=promoted_equipment,
            skills=[skill for skill in warrior.skills if skill not in profile.inherent_rules],
            experience=warrior.experience,  # preserve experience
            previous_experience=warrior.previous_experience,
            quantity=1,
            cost=profile.cost,
            skill_access=[],
            stat_advances=dict(warrior.stat_advances),  # preserve advances (KB "preserve")
            profile_id=warrior.profile_id,
            injury_records=[dict(record) for record in warrior.injury_records],
        )
        campaign.warriors.append(hero_row)
        row = self.post.pending_advance_for(warrior_id, threshold)
        remaining = warrior.quantity - 1
        if remaining:
            warrior.quantity = remaining
            if not warrior.name.endswith(" group"):
                warrior.name = f"{warrior.profile_name} group"
            if row is not None:
                row.setdefault("roll_history", []).append("Rolled 10-12: one member became a Hero; remaining group rerolls.")
                row["roll_total"] = None
                row["subroll"] = None
                row["promotion_offer"] = False
                row["reroll_exclude_promotion"] = True
        else:
            campaign.warriors.remove(warrior)
            if row is not None:
                self.post.pending_advances.remove(row)
        self.post.pending_advances.append({
            "warrior_id": hero_row.id, "warrior_name": hero_row.name,
            "table": "hero", "threshold": None, "roll_total": None,
            "subroll": None, "committed": False, "applied_label": "",
            "promotion_immediate": True, "promotion_setup_pending": True,
            "promotion_tables": [],
        })
        return True, (
            f"{promoted_name} promoted to Hero: choose 2 Hero skill lists, then roll one Hero advance. "
            + ("The remaining group rerolls this advance, rerolling 10-12." if remaining else "No Henchmen remain in the group.")
        )

    def pending_advance_summary(self) -> dict[str, int]:
        if self.post is None:
            return {"pending": 0, "resolved": 0, "committed": 0}
        rows = self.post.pending_advances
        return {
            "pending": sum(1 for row in rows if row.get("roll_total") is None and not row.get("committed")),
            "resolved": sum(1 for row in rows if row.get("roll_total") is not None and not row.get("committed")),
            "committed": sum(1 for row in rows if row.get("committed")),
        }

    # ------------------------------------------------------------- exploration

    def apply_exploration(self, dice: tuple[int, ...]) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        dice = tuple(int(value) for value in dice)
        resolver = PostBattleResolver(self.port)
        resolved = resolver.resolve_exploration(dice)
        self.post.wyrdstone_delta += resolved.shards
        self._log(self.STEP_EXPLORATION, "exploration", f"{resolved.shards} wyrdstone shard(s) found.")
        message = f"{resolved.shards} wyrdstone shard(s) added to the hoard."
        if resolved.matching_dice_note:
            message += f" {resolved.matching_dice_note}"
        row = resolver.exploration_followup_row(dice)
        if row is not None:
            follow_up = row.get("follow_up") or {}
            self._add_follow_up(self.STEP_EXPLORATION, {
                "type": "exploration_followup",
                "description": f"{row.get('outcome')} special result: resolve the KB follow-up effects.",
                "result_id": str(row.get("id") or ""),
                "queue": [follow_up] if follow_up else [],
                "messages": [],
                "hero_id": None,
            })
            self._log(self.STEP_EXPLORATION, "exploration_special", str(row.get("outcome") or ""), result_id=row.get("id"))
            message += f" Special result: {row.get('outcome')}."
        return True, message


    # --------------------------------------------------- exploration follow-ups

    def exploration_followup_pending(self) -> dict | None:
        """Next player input the exploration follow-up needs, if any."""
        row = self._exploration_followup_row()
        if row is None:
            return None
        if isinstance(row.get("pending"), dict):
            return row["pending"]
        queue = list(row.get("queue") or ())
        messages = list(row.get("messages") or [])
        pending = self._process_followup_queue(row, queue, messages)
        if pending is None:
            text = "; ".join(row.get("messages") or []) or "follow-up complete"
            self.post.pending_follow_ups.remove(row)
            self._log(self.STEP_EXPLORATION, "exploration_followup", text)
        return pending

    def advance_exploration_followup(self, *, roll: int | None = None, hero_id: str | None = None,
                                     option_id: str | None = None,
                                     warrior_ids: list[str] | None = None) -> tuple[bool, str]:
        """Feed one player answer (die roll or chosen hero) into the queue."""
        row = self._exploration_followup_row()
        if row is None:
            return False, "No exploration follow-up pending."
        queue = list(row.get("queue") or ())
        messages = list(row.get("messages") or [])
        current = row.get("pending") or {}
        if current.get("kind") == "roll":
            if roll is None:
                return False, "A die roll is required."
            queue.insert(0, {"type": "_rolled", "spec": current, "value": int(roll)})
        elif current.get("kind") == "choose_hero":
            if hero_id is None:
                return False, "Choose a Hero."
            row["hero_id"] = str(hero_id)
            continuation = current.get("continuation")
            if isinstance(continuation, dict):
                queue.insert(0, continuation)
        elif current.get("kind") == "choose_option":
            option = next((item for item in current.get("options") or () if str(item.get("id")) == str(option_id)), None)
            if option is None:
                return False, "Choose one of the available options."
            messages.append(str(option.get("label") or option_id))
            if option.get("hero_id"):
                row["hero_id"] = str(option["hero_id"])
            queue[:0] = list(option.get("then") or ())
        elif current.get("kind") == "choose_warriors":
            selected = list(dict.fromkeys(warrior_ids or ()))
            eligible = {str(item.get("id")) for item in current.get("options") or ()}
            maximum = int(current.get("maximum") or 1)
            if len(selected) > maximum or any(item not in eligible for item in selected):
                return False, f"Choose at most {maximum} eligible warriors."
            names = [w.name for w in self.campaign.warriors if w.id in selected]
            text = str(current.get("text") or "").replace("{warriors}", ", ".join(names) or "none")
            queue.insert(0, {"type": "grant_rule", "recipient": "warband", "text": text,
                             "expires_after_battles": current.get("expires_after_battles")})
        messages.extend(current.get("applied") or [])
        row["queue"] = queue
        row["messages"] = messages
        row.pop("pending", None)
        pending = self._process_followup_queue(row, queue, messages)
        if pending is None:
            text = "; ".join(row.get("messages") or []) or "follow-up complete"
            self.post.pending_follow_ups.remove(row)
            self._log(self.STEP_EXPLORATION, "exploration_followup", text)
            return True, text
        return True, "; ".join(row.get("messages") or []) or "Follow-up continues."

    def _exploration_followup_row(self) -> dict | None:
        if self.post is None:
            return None
        return next(
            (item for item in self.post.pending_follow_ups if item.get("type") == "exploration_followup"),
            None,
        )

    def _process_followup_queue(self, row: dict, queue: list, messages: list) -> dict | None:
        """Consume auto-appliable nodes; return the next pending input action."""
        while queue:
            node = queue.pop(0)
            kind = str(node.get("type") or "")
            if kind == "_rolled":
                spec = node.get("spec") or {}
                value = int(node.get("value") or 0)
                if spec.get("magical_artefact"):
                    document = self.port.campaign_catalog().catalogue("exploration-and-income.yaml")
                    artefact = next((item for item in document.get("magical_artefacts", {}).get("results", ())
                                     if int(item.get("roll") or 0) == value), None)
                    if artefact is None:
                        messages.append(f"Magical artefact roll {value} has no result")
                        continue
                    name = str(artefact.get("result") or "Magical artefact")
                    item_id = str(artefact.get("id") or "").removeprefix("campaign.magical-artefact.")
                    item_id = f"magical_artefact.{item_id}"
                    owned = any(item.id == item_id and item.owned > 0 for item in self.campaign.inventory)
                    if owned:
                        messages.append(f"{name} is already owned; roll again")
                        queue.insert(0, {"type": "magical_artefact_table"})
                    else:
                        queue.insert(0, {"type": "grant_special_item", "recipient": "hero",
                                         "label": f"Choose the bearer of {name}",
                                         "item_id": item_id, "name": name,
                                         "text": str(artefact.get("effect") or "")})
                    continue
                row["last_roll"] = value
                rolled_value = value
                value = value * int(spec.get("multiplier") or 1) + int(spec.get("offset") or 0)
                messages.append(f"{spec.get('label')}: {rolled_value}" + (f" → {value}" if value != rolled_value else ""))
                resource = str(spec.get("resource") or "")
                if resource:
                    if resource.startswith("item:"):
                        self._grant_item(resource.removeprefix("item:"), value, messages)
                    else:
                        self._grant_resource(str(spec.get("recipient") or "warband"), resource, value, messages)
                    continuation = spec.get("continuation")
                    if isinstance(continuation, dict):
                        queue.insert(0, continuation)
                    continue
                if spec.get("test"):
                    actor = self._followup_actor(row, spec.get("actor"))
                    characteristic = self._followup_characteristic(actor, str(spec.get("characteristic") or ""))
                    success = value <= characteristic
                    who = actor.name if actor else "test"
                    messages.append(f"{who} {'succeeded' if success else 'failed'} ({value} vs {characteristic})")
                    queue[:0] = list(spec.get("on_success" if success else "on_failure") or ())
                    continue
                for branch in spec.get("branches") or ():
                    when = branch.get("when") or {}
                    low = int(when.get("min") or 0)
                    high = when.get("max")
                    if value >= low and (high is None or value <= int(high)):
                        queue[:0] = list(branch.get("then") or ())
                        break
                continue
            if kind == "sequence":
                queue[:0] = list(node.get("steps") or ())
                continue
            if kind == "conditional":
                context_roll = int(row.get("last_roll") or 0)
                for case in node.get("cases") or ():
                    when = case.get("when") or {}
                    field = str(when.get("field") or "")
                    operator = str(when.get("operator") or "")
                    value = when.get("value")
                    actual = self.campaign.band_id if field == "context.band_id" else context_roll
                    matches = (
                        (operator == "equals" and str(actual) == str(value))
                        or (operator == "in" and str(actual) in [str(item) for item in (value or ())])
                    )
                    if matches:
                        queue[:0] = list(case.get("then") or ())
                        break
                else:
                    queue[:0] = list(node.get("default") or ())
                continue
            if kind in ("grant", "reward.grant"):
                applied = self._apply_followup_grant(row, node, messages)
                if isinstance(applied, dict):
                    row["queue"] = queue
                    row["messages"] = messages
                    row["pending"] = applied
                    return applied
                continue
            if kind == "choose_one":
                if not any(w.kind == "hero" for w in self.campaign.warriors):
                    messages.append("no eligible hero for the choice; skipped")
                    continue
                pending = {"kind": "choose_hero", "label": str(node.get("bind") or "choose a hero"), "applied": []}
                row["queue"] = queue
                row["messages"] = messages
                row["pending"] = pending
                return pending
            if kind == "choose_option":
                pending = {
                    "kind": "choose_option", "label": str(node.get("label") or "Choose an outcome"),
                    "options": copy.deepcopy(list(node.get("options") or ())), "applied": [],
                }
                row["queue"], row["messages"], row["pending"] = queue, messages, pending
                return pending
            if kind == "choose_equipment":
                options = []
                for warrior in self.campaign.warriors:
                    for item in warrior.equipment:
                        if item.quantity > 0:
                            text = str(node.get("text") or "").replace("{item}", item.name)
                            options.append({"id": f"{warrior.id}:{item.item_id}",
                                            "label": f"{warrior.name} — {item.name}", "hero_id": warrior.id,
                                            "then": [{"type": "grant_rule", "recipient": "hero", "text": text}]})
                if not options:
                    messages.append("No equipped item is eligible; reward skipped")
                    continue
                pending = {"kind": "choose_option", "label": str(node.get("label") or "Choose equipment"),
                           "options": options, "applied": []}
                row["queue"], row["messages"], row["pending"] = queue, messages, pending
                return pending
            if kind == "choose_warriors":
                forbidden = {str(value).casefold() for value in node.get("exclude_profiles") or ()}
                options = [{"id": w.id, "label": w.name} for w in self.campaign.warriors
                           if w.profile_name.casefold() not in forbidden]
                pending = {"kind": "choose_warriors", "label": str(node.get("label") or "Choose warriors"),
                           "options": options, "maximum": int(node.get("maximum") or 1),
                           "text": str(node.get("text") or "Selected: {warriors}"),
                           "expires_after_battles": node.get("expires_after_battles"), "applied": []}
                row["queue"], row["messages"], row["pending"] = queue, messages, pending
                return pending
            if kind == "choose_hireling":
                from mordheim_campaign.application.post_battle_catalogue import PostBattleCatalogue
                catalogue = PostBattleCatalogue(
                    self.port, self.campaign.collection, self.campaign.band_id,
                    member_profile_ids=frozenset(w.profile_id for w in self.campaign.warriors if w.kind != "hireling"),
                    hired_sword_profile_ids=frozenset(w.profile_id for w in self.campaign.warriors if w.kind == "hireling"),
                )
                options = [{"id": offer.profile_id, "label": offer.name,
                            "then": [{"type": "hire_free_hireling", "profile_id": offer.profile_id}]}
                           for offer in catalogue.hired_swords() if offer.eligibility == "eligible"]
                if not options:
                    messages.append("No legal Hired Sword is currently available")
                    continue
                pending = {"kind": "choose_option", "label": str(node.get("label") or "Choose a Hired Sword"),
                           "options": options, "applied": []}
                row["queue"], row["messages"], row["pending"] = queue, messages, pending
                return pending
            if kind == "hire_free_hireling":
                from mordheim_campaign.application.post_battle_catalogue import PostBattleCatalogue
                catalogue = PostBattleCatalogue(self.port, self.campaign.collection, self.campaign.band_id,
                    member_profile_ids=frozenset(w.profile_id for w in self.campaign.warriors if w.kind != "hireling"),
                    hired_sword_profile_ids=frozenset(w.profile_id for w in self.campaign.warriors if w.kind == "hireling"))
                offer = next((item for item in catalogue.hired_swords() if item.profile_id == str(node.get("profile_id"))), None)
                warrior = self.hireling_warrior(offer) if offer is not None else None
                if warrior is None:
                    messages.append("The selected Hired Sword could not be added")
                else:
                    warrior.special_rules.append("Returning a Favour: no hiring fee; upkeep begins after the next battle")
                    self.campaign.warriors.append(warrior)
                    messages.append(f"{warrior.name} joins for the next battle without a hiring fee")
                continue
            if kind == "choose_henchman_group":
                options = [{"id": w.id, "label": w.name,
                            "then": [{"type": "prisoner_join_group", "warrior_id": w.id}]}
                           for w in self.campaign.warriors
                           if self._is_human_henchman_group(w)]
                if node.get("allow_decline", True):
                    options.append({"id": "decline", "label": "Do not recruit the prisoner", "then": []})
                pending = {"kind": "choose_option", "label": str(node.get("label") or "Choose a Henchman group"),
                           "options": options, "applied": []}
                row["queue"], row["messages"], row["pending"] = queue, messages, pending
                return pending
            if kind == "prisoner_join_group":
                warrior = next((w for w in self.campaign.warriors if w.id == str(node.get("warrior_id")) and w.kind == "henchman"), None)
                if warrior is None or self.projected_warband_members() >= self.effective_maximum_models():
                    messages.append("The prisoner cannot join that group")
                    continue
                warrior.quantity += 1
                for item in warrior.equipment:
                    if item.per_model and not item.transferable:
                        item.quantity += 1
                    elif item.per_model:
                        self.post.equipment_obligations.append({"warrior_id": warrior.id, "item_id": item.item_id,
                            "item_name": item.name, "quantity": 1})
                messages.append(f"The prisoner joins {warrior.name}; matching equipment is required")
                continue
            if kind == "grant_free_profile":
                wanted = str(node.get("profile_name") or "").casefold()
                profile = next((p for p in self.port.profiles(self.campaign.collection, self.campaign.band_id)
                                if p.name.casefold() == wanted or wanted in p.name.casefold()), None)
                if profile is None or self.projected_warband_members() >= self.effective_maximum_models():
                    messages.append(f"No legal roster slot/profile for free {node.get('profile_name')}")
                    continue
                existing = next((w for w in self.campaign.warriors
                                 if w.kind == "henchman" and w.profile_id == profile.profile_id), None)
                if existing is not None:
                    existing.quantity += 1
                else:
                    count = sum(1 for w in self.campaign.warriors if w.profile_id == profile.profile_id)
                    self.campaign.warriors.append(warrior_vm(self.port, profile,
                        row_id=f"{profile.profile_id}#reward{count + 1}",
                        name=unique_warrior_name(self.campaign.warriors, f"{profile.name} Group")))
                messages.append(f"One {profile.name} joins the warband for free")
                continue
            if kind == "characteristic_test":
                spec = {
                    "kind": "roll",
                    "test": True,
                    "actor": str(node.get("actor") or "leader"),
                    "characteristic": str(node.get("characteristic") or ""),
                    "dice_count": int((node.get("dice") or {}).get("count") or 1),
                    "dice_sides": int((node.get("dice") or {}).get("sides") or 6),
                    "label": f"{node.get('characteristic')} test",
                    "applied": [],
                }
                row["queue"] = queue
                row["messages"] = messages
                row["pending"] = spec
                return spec
            if kind == "roll_table":
                dice = node.get("dice") or {}
                spec = {
                    "kind": "roll",
                    "dice_count": int(dice.get("count") or 1),
                    "dice_sides": int(dice.get("sides") or 6),
                    "branches": [dict(branch) for branch in node.get("branches") or ()],
                    "label": "follow-up roll",
                    "applied": [],
                }
                row["queue"] = queue
                row["messages"] = messages
                row["pending"] = spec
                return spec
            if kind == "magical_artefact_table":
                spec = {"kind": "roll", "dice_count": 1, "dice_sides": 6,
                        "magical_artefact": True, "label": "Magical artefact roll", "applied": []}
                row["queue"], row["messages"], row["pending"] = queue, messages, spec
                return spec
            if kind == "warrior.miss_games":
                warrior = self._followup_actor(row, node.get("subject"))
                games = node.get("games") or {}
                value = int(games.get("value") or 1) if isinstance(games, dict) else int(games or 1)
                if warrior is not None:
                    warrior.games_to_miss += value
                    warrior.absence_reason = str(node.get("reason") or "Injury")
                    messages.append(f"{warrior.name} misses {value} game(s)")
                continue
            if kind == "roster.remove_warrior":
                warrior = self._followup_actor(row, node.get("subject"))
                if warrior is not None:
                    self._discard_carried_equipment(warrior, return_to_stash=False)
                    self.campaign.warriors.remove(warrior)
                    messages.append(f"{warrior.name} was removed from the roster")
                continue
            if kind == "grant_rule":
                text = str(node.get("text") or "").strip()
                target = str(node.get("recipient") or "warband")
                if target == "hero":
                    hero = self._followup_actor(row, "$hero_id")
                    if hero is None:
                        pending = {"kind": "choose_hero", "label": str(node.get("label") or "Choose a Hero"),
                                   "continuation": copy.deepcopy(node), "applied": []}
                        row["queue"], row["messages"], row["pending"] = queue, messages, pending
                        return pending
                    if text and text not in hero.special_rules:
                        hero.special_rules.append(text)
                    if text.startswith("Academic skill access") and "Academic" not in hero.skill_access:
                        hero.skill_access.append("Academic")
                    if text.startswith("Combat skill access") and "Combat" not in hero.skill_access:
                        hero.skill_access.append("Combat")
                    if text.startswith("Haggle") and "Haggle" not in hero.skills:
                        hero.skills.append("Haggle")
                    messages.append(f"{hero.name}: {text}")
                else:
                    rule = {"source": str(row.get("id") or "exploration"), "text": text,
                            "expires_after_battles": node.get("expires_after_battles"),
                            "consume_when_opponent_contains": list(node.get("consume_when_opponent_contains") or ())}
                    if text and not any(item.get("text") == text for item in self.campaign.special_rules):
                        self.campaign.special_rules.append(rule)
                    messages.append(text)
                continue
            if kind == "grant_special_item":
                hero = self._followup_actor(row, "$hero_id")
                if hero is None:
                    pending = {"kind": "choose_hero", "label": str(node.get("label") or "Choose a bearer"),
                               "continuation": copy.deepcopy(node), "applied": []}
                    row["queue"], row["messages"], row["pending"] = queue, messages, pending
                    return pending
                item_id, name, rule = str(node.get("item_id")), str(node.get("name")), str(node.get("text") or "")
                if item_id in self.campaign.unique_reward_ids:
                    messages.append(f"{name} already appeared in this campaign; reward skipped")
                    continue
                stock = InventoryItemVM(item_id, name, "Magical Artefact", 1, 1, 0, 0,
                                        "Unique", [rule] if rule else [])
                self.campaign.inventory.append(stock)
                hero.equipment.append(EquipmentEntryVM(item_id, name, 1, "scenario_reward", 0,
                                                        False, True, list(stock.special_rules)))
                self.campaign.unique_reward_ids.append(item_id)
                messages.append(f"{hero.name} receives {name}")
                continue
            if kind == "grant_compound_item":
                item_id, name = str(node.get("reward_id")), str(node.get("name"))
                stock = next((item for item in self.campaign.inventory if item.id == item_id), None)
                if stock is None:
                    stock = InventoryItemVM(item_id, name, str(node.get("category") or "Weapon"), 0, 0, 0, 0,
                                            None, [str(value) for value in node.get("rules") or ()],
                                            str(node.get("base_item_id") or ""))
                    self.campaign.inventory.append(stock)
                stock.owned += 1
                stock.stash += 1
                messages.append(f"+1 {name} (stash)")
                continue
            messages.append(f"unhandled follow-up step: {kind}")
        row["queue"] = queue
        row["messages"] = messages
        return None

    def _apply_followup_grant(self, row: dict, node: dict, messages: list) -> dict | None:
        """Apply one grant node; return a pending roll action when dice needed."""
        recipient = str(node.get("recipient") or "warband")
        if recipient == "hero" and not row.get("hero_id"):
            return {"kind": "choose_hero", "label": str(node.get("label") or "Choose the Hero who receives this reward"),
                    "continuation": copy.deepcopy(node), "applied": []}
        if recipient == "hero":
            recipient = str(row["hero_id"])
        resources = list((node.get("resources") or {}).items())
        items = list(node.get("items") or ())
        for index, (resource, amount) in enumerate(resources):
            spec = amount if isinstance(amount, dict) else {"kind": "fixed", "value": int(amount)}
            if str(spec.get("kind")) == "fixed":
                self._grant_resource(recipient, str(resource), int(spec.get("value") or 0), messages)
            else:
                dice = spec.get("dice") or {}
                continuation = copy.deepcopy(node)
                continuation["resources"] = dict(resources[index + 1:])
                continuation["items"] = items
                return {
                    "kind": "roll", "resource": str(resource), "recipient": recipient,
                    "dice_count": int(dice.get("count") or 1), "dice_sides": int(dice.get("sides") or 6),
                    "multiplier": int(spec.get("multiplier") or 1), "offset": int(spec.get("offset") or 0),
                    "continuation": continuation, "label": f"{resource} roll", "applied": [],
                }
        for index, item in enumerate(items):
            item_id = str(item.get("item_id") or "")
            quantity_spec = item.get("quantity") or {}
            if str(quantity_spec.get("kind")) == "fixed":
                self._grant_item(item_id, int(quantity_spec.get("value") or 1), messages)
            else:
                dice = quantity_spec.get("dice") or {}
                continuation = copy.deepcopy(node)
                continuation["resources"] = {}
                continuation["items"] = items[index + 1:]
                return {
                    "kind": "roll", "resource": f"item:{item_id}", "recipient": recipient,
                    "dice_count": int(dice.get("count") or 1), "dice_sides": int(dice.get("sides") or 6),
                    "multiplier": int(quantity_spec.get("multiplier") or 1), "offset": int(quantity_spec.get("offset") or 0),
                    "continuation": continuation, "label": f"{item_id} quantity roll", "applied": [],
                }
        if node.get("note"):
            messages.append(str(node["note"]))
        return None

    def _grant_resource(self, recipient: str, resource: str, value: int, messages: list) -> None:
        if resource == "gold_crowns":
            self.post.gold_delta += value
            messages.append(f"+{value} gc")
        elif resource == "wyrdstone_fragments":
            self.post.wyrdstone_delta += value
            messages.append(f"+{value} wyrdstone shard(s)")
        elif resource == "experience":
            heroes = [w for w in self.campaign.warriors if w.kind == "hero"]
            targets = heroes[:1] if recipient == "leader" else (
                heroes if recipient == "heroes" else [w for w in heroes if w.id == recipient]
            )
            for warrior in targets:
                warrior.experience += value
                self.sync_pending_advances([warrior])
            messages.append(f"+{value} XP to {recipient}")
        else:
            messages.append(f"{resource}: {value} (recorded as a note)")

    def _grant_item(self, item_id: str, quantity: int, messages: list) -> None:
        if quantity <= 0:
            return
        name = self.port.item_name(item_id) or item_id
        stock = next((entry for entry in self.campaign.inventory if entry.id == item_id), None)
        if stock is None:
            self.campaign.inventory.append(InventoryItemVM(item_id, name, "Misc", quantity, 0, quantity, 0))
        else:
            stock.owned += quantity
            stock.stash += quantity
        messages.append(f"+{quantity} {name} (stash)")

    def _followup_actor(self, row: dict, actor: object):
        """Resolve $searching_hero / leader / a warrior id to a WarriorVM."""
        if isinstance(actor, str) and actor.startswith("$"):
            actor = row.get("hero_id")
        if isinstance(actor, str) and actor == "leader":
            return next((w for w in self.campaign.warriors if w.kind == "hero"), None)
        if isinstance(actor, str):
            return next((w for w in self.campaign.warriors if w.id == actor), None)
        return None

    def _followup_characteristic(self, warrior, characteristic: str) -> int:
        keys = {"toughness": "T", "leadership": "Ld", "strength": "S", "initiative": "I",
                "weapon_skill": "WS", "attacks": "A", "wounds": "W", "movement": "M", "ballistic_skill": "BS"}
        key = keys.get(characteristic, characteristic)
        if warrior is None:
            return 3
        return int(warrior.stats.get(key, 0)) + int(warrior.stat_modifiers.get(key, 0))

    # ------------------------------------------------------------ sell wyrdstone

    def sell_wyrdstone(self, quantity: int, *, warband_size: int | None = None) -> tuple[bool, str]:
        """Sells shards once per sequence at the KB table price."""
        if self.post is None:
            return False, "No pending post-battle."
        if self.post.sale_resolved:
            return False, "Wyrdstone can only be sold once per post-battle sequence."
        if quantity < 0:
            return False, "Cannot sell a negative quantity."
        available = self.projected_shards()
        if quantity > available:
            return False, f"Only {available} shard(s) available to sell."
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        size = warband_size if warband_size is not None else self.projected_warband_members()
        value = PostBattleResolver(self.port).wyrdstone_sale_value(quantity, size)
        self.post.wyrdstone_sold += quantity
        self.post.gold_delta += value
        self.post.sale_resolved = True
        message = f"Sold {quantity} shard(s) for {value} gc."
        self._log(self.STEP_SELL, "sell_wyrdstone", message, quantity=quantity)
        return True, message

    # --------------------------------------------------------------- veterans

    def apply_veteran_pool(self, pool: int) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        self.post.veteran_pool = max(0, int(pool))
        message = f"Veteran experience pool set to {self.post.veteran_pool} XP."
        self._log(self.STEP_VETERANS, "veteran_pool", message, pool=self.post.veteran_pool)
        return True, message

    # ------------------------------------------------------------------ items

    def _inventory_row(self, item_id: str, *, name: str, price_gc: int | None) -> InventoryItemVM:
        for row in self.campaign.inventory:
            if row.id == item_id:
                return row
        row = InventoryItemVM(
            id=item_id,
            name=name,
            category="Misc",
            owned=0,
            equipped=0,
            stash=0,
            value=price_gc or 0,
        )
        self.campaign.inventory.append(row)
        return row

    def buy_item(self, item_id: str, quantity: int, price_gc: int | None, *, category: str = "Misc", rarity: int | None = None) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        quantity = max(1, int(quantity))
        if price_gc is None:
            return False, "This item has no flat price; purchases are not supported yet."
        limit = self.port.trading_post_restriction(item_id).get("limit_per_warband")
        if limit is not None:
            owned = sum(row.owned for row in self.campaign.inventory if row.id == item_id)
            if owned + quantity > int(limit):
                return False, f"Warband limit reached: at most {limit} of this item (own {owned})."
        cost = price_gc * quantity
        if cost > self.projected_gold():
            return False, f"Not enough gold: {cost} gc needed, {self.projected_gold()} gc available."
        row = self._inventory_row(item_id, name=self.port.item_name(item_id) or item_id, price_gc=price_gc)
        row.owned += quantity
        row.stash += quantity
        row.value = price_gc
        row.category = category or row.category
        row.rarity = f"Rare {rarity}" if rarity is not None else row.rarity
        self.post.gold_delta -= cost
        message = f"{quantity}× {row.name} bought for {cost} gc (stash)."
        self._log(self.STEP_EQUIPMENT, "buy_item", message, item_id=item_id, quantity=quantity)
        return True, message

    def assign_item(self, item_id: str, warrior_id: str) -> tuple[bool, str]:
        """Post-battle assign; delegates to the always-available stash move."""
        return self.move_stash_to_warrior(item_id, warrior_id)

    # ------------------------------------------------- equipment moves (any time)

    def move_stash_to_warrior(self, item_id: str, warrior_id: str) -> tuple[bool, str]:
        """Assign one stash copy to a warrior; legal at any campaign moment.

        Free equipment reallocation between battles is part of the tabletop
        rules, so unlike the post-battle purchases this needs no pending
        sequence. ``assign_item`` (post-battle window) delegates here.
        """
        row = next((item for item in self.campaign.inventory if item.id == item_id), None)
        if row is None:
            return False, f"No unassigned {row.name if row else item_id or 'item'} in the stash."
        warrior = next((w for w in self.campaign.warriors if w.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"
        if self.port.trading_post_restriction(item_id).get("heroes_only") and warrior.kind != "hero":
            return False, f"{self.port.item_name(item_id) or item_id} may only be assigned to heroes."
        restriction = self._profile_assignment_violation(item_id, warrior)
        if restriction:
            return False, restriction
        violation = self.loadout_violation(warrior, row.base_item_id or item_id)
        if violation:
            return False, violation
        existing = next(
            (
                item for item in warrior.equipment
                if item.item_id == item_id
                and item.acquisition == "stash_assignment"
                and item.transferable
                and item.per_model == (warrior.kind == "henchman")
            ),
            None,
        )
        amount = max(0, warrior.quantity - existing.quantity) if warrior.kind == "henchman" and existing else (
            warrior.quantity if warrior.kind == "henchman" else 1
        )
        if amount == 0:
            return False, f"Every member of {warrior.name} already carries {row.name}."
        if row.stash < amount:
            return False, f"{warrior.name} needs {amount}× {row.name}; only {row.stash} in stash."
        per_model = warrior.kind == "henchman"
        row.stash -= amount
        row.equipped += amount
        entry = next(
            (item for item in warrior.equipment if item.item_id == item_id and item.acquisition == "stash_assignment" and item.per_model == per_model),
            None,
        )
        if entry is None:
            warrior.equipment.append(EquipmentEntryVM(item_id, row.name, amount, "stash_assignment", row.value,
                                                       per_model, True, list(row.special_rules), row.base_item_id))
        else:
            entry.quantity += amount
        message = f"{amount}× {row.name} assigned to {warrior.name}."
        if self.post is not None:
            self._log(self.STEP_EQUIPMENT, "assign_item", message, item_id=item_id, warrior_id=warrior.id)
        return True, message

    def _profile_assignment_violation(self, item_id: str, warrior) -> str | None:
        """Enforce the Trading Post's profile-specific bearer restrictions."""
        identity = " ".join(
            (warrior.name, warrior.profile_name, warrior.profile_id, *warrior.skills, *warrior.special_rules)
        ).replace("-", " ").replace("_", " ").casefold()
        equipped = " ".join(
            item.name + " " + item.item_id + " " + item.base_item_id
            for item in warrior.equipment
        ).casefold()
        allowed_terms = {
            "beastlash": ("beastmaster",),
            "broadsword": ("chapel guard knight",),
            "serpent_staff": ("liche priest",),
            "shortsword": ("chapel guard knight",),
            "nehekharan_javelin": ("tomb lord",),
            "swivel_gun": ("gunner",),
            "kite_shield": ("chapel guard knight",),
            "asp_arrows": ("tomb lord",),
            "conch_shell_horn": ("piranha warrior",),
            "elven_runestones": ("weaver",),
            "parrot": ("captain", "mate"),
        }
        if item_id == "barbed_whip" and warrior.kind != "hero":
            return "Barbed Whip may only be assigned to a Marauders of Chaos Hero."
        if item_id == "great_axe" and not (warrior.kind == "hero" and "chosen of chaos" in identity):
            return "Great Axe requires a Marauders Hero with the Chosen of Chaos skill."
        if item_id == "reptile_venom" and not (warrior.kind == "henchman" and "skink" in identity):
            return "Reptile Venom may only be assigned to Skink Henchmen."
        if item_id in {"familiar", "arcane_familiar"} and "spellcaster" not in identity:
            return "A Familiar may only be assigned to a spellcaster."
        if item_id == "book_of_the_dead" and not any(term in identity for term in ("vampire", "necromancer")):
            return "The Book of the Dead may only be assigned to Vampires or Necromancers."
        if item_id == "nightmare" and not any(term in identity for term in ("vampire", "necromancer", "grave guard")):
            return "A Nightmare may only be assigned to Vampires, Necromancers or Grave Guards."
        if item_id == "temple_dog" and not any(term in identity for term in ("dragon monk", "sister", "priest")):
            return "A Temple Dog may only be assigned to Dragon Monks, Sisters of Sigmar or Priests."
        if item_id in {"barding", "bretonnian_barding"} and not any(term in equipped for term in ("warhorse", "horse")):
            return "Barding requires this warrior to have a Warhorse."
        if item_id in {"dark_elf_blade_weapon_upgrade", "poisoned_weapon"} and not any(
            self.port.weapon_hands(item.base_item_id or item.item_id) is not None for item in warrior.equipment
        ):
            return f"{self.port.item_name(item_id) or item_id} requires an equipped weapon to upgrade."
        if item_id == "sword_heroes_only" and warrior.kind != "hero":
            return "This Sword variant may only be assigned to Heroes."
        terms = allowed_terms.get(item_id)
        if terms and not any(term in identity for term in terms):
            note = "; ".join(self.port.trading_post_restriction(item_id).get("notes") or ())
            return note or f"{self.port.item_name(item_id) or item_id} cannot be assigned to this warrior."
        return None

    def loadout_violation(self, warrior: "WarriorVM", item_id: str) -> str | None:
        """Validate structured hand and duplicate limits for one assignment."""
        hands = self.port.weapon_hands(item_id)
        if hands is not None:
            used = sum(
                (self.port.weapon_hands(item.base_item_id or item.item_id) or 1) * item.quantity
                for item in warrior.equipment
                if self.port.weapon_hands(item.base_item_id or item.item_id) is not None
            )
            amount = warrior.quantity if warrior.kind == "henchman" else 1
            budget = 2 * warrior.quantity
            if used + hands * amount > budget:
                return f"Not enough hands: the new weapon needs {hands} per model, {used} of {budget} already used."
        kind = self.port.item_kind(item_id)
        if kind not in ("close-combat-weapon", "ranged-weapon"):
            if any(item.item_id == item_id for item in warrior.equipment):
                return f"{self.port.item_name(item_id) or item_id} is already carried; a warrior carries one of these."
        return None

    def return_warrior_to_stash(self, item_id: str, warrior_id: str) -> tuple[bool, str]:
        """Return one equipped copy to the stash (keeps ``owned`` intact)."""
        row = next((item for item in self.campaign.inventory if item.id == item_id), None)
        warrior = next((w for w in self.campaign.warriors if w.id == warrior_id), None)
        if row is None or warrior is None:
            return False, "Unknown warrior or item."
        entry = next(
            (item for item in warrior.equipment if item.item_id == item_id and item.quantity > 0 and item.transferable),
            None,
        )
        if entry is None:
            return False, f"{warrior.name} does not carry {row.name}."
        amount = warrior.quantity if warrior.kind == "henchman" and entry.per_model else 1
        amount = min(amount, entry.quantity)
        entry.quantity -= amount
        if entry.quantity <= 0:
            warrior.equipment.remove(entry)
        row.equipped = max(0, row.equipped - amount)
        row.stash += amount
        message = f"{amount}× {row.name} returned to the stash from {warrior.name}."
        if self.post is not None:
            self._log(self.STEP_EQUIPMENT, "return_item", message, item_id=item_id, warrior_id=warrior.id)
        return True, message

    def sell_item(self, item_id: str, quantity: int) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        quantity = max(1, int(quantity))
        row = next((item for item in self.campaign.inventory if item.id == item_id), None)
        if row is None:
            return False, "Unknown item."
        if row.stash < quantity:
            return False, f"Only {row.stash} unassigned copy/copies in the stash."
        price = max(0, row.value // 2)
        row.stash -= quantity
        row.owned -= quantity
        if row.owned <= 0:
            self.campaign.inventory.remove(row)
        self.post.gold_delta += price * quantity
        message = f"Sold {quantity}× {row.name} for {price * quantity} gc."
        self._log(self.STEP_EQUIPMENT, "sell_item", message, item_id=item_id, quantity=quantity)
        return True, message

    # ------------------------------------------------------------- recruitment

    def group_recruitment_quote(self, warrior_id: str) -> tuple[bool, dict | str]:
        """Describe the cost and equipment deficit caused by one new member."""
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None or warrior.kind != "henchman":
            return False, "Only an existing henchman group can receive a member."
        available_xp = self.post.veteran_pool if self.post is not None else 0
        gc_per_xp = self._veteran_gc_per_experience()
        requirements = []
        for item in warrior.equipment:
            if not item.per_model or not item.transferable:
                continue
            inventory = next((row for row in self.campaign.inventory if row.id == item.item_id), None)
            in_stash = inventory.stash if inventory is not None else 0
            unit_cost = inventory.value if inventory is not None and inventory.value else (
                self.port.price_override(self.campaign.collection, self.campaign.band_id, item.item_id)
                or self.port.trading_post_price(item.item_id)
                or item.unit_cost
            )
            requirements.append({
                "item_id": item.item_id, "name": item.name,
                "in_stash": min(1, in_stash), "to_buy": 0 if in_stash else 1,
                "unit_cost": max(0, unit_cost),
            })
        required_xp = max(0, warrior.experience)
        return True, {
            "warrior": warrior, "recruit_cost": warrior.cost,
            "required_xp": required_xp, "available_xp": available_xp,
            "experience_gc": required_xp * gc_per_xp,
            "requirements": requirements,
            "equipment_cost": sum(row["to_buy"] * row["unit_cost"] for row in requirements),
        }

    def _veteran_gc_per_experience(self) -> int:
        """KB ``veteran_availability`` incremental cost per experience point."""
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("recruitment-and-veterans.yaml")
        for row in document.get("veteran_availability") or ():
            cost = (row.get("incremental_cost") or {}).get("per_experience_point_gc")
            if cost is not None:
                return int(cost)
        return 0

    def add_member_to_group(self, warrior_id: str) -> tuple[bool, str]:
        """Recruit one model; equipment purchases remain for the Equipment step."""
        if self.post is None:
            return False, "No pending post-battle."
        ok, result = self.group_recruitment_quote(warrior_id)
        if not ok:
            return False, str(result)
        quote = result
        warrior = quote["warrior"]
        if quote["required_xp"] > quote["available_xp"]:
            return False, f"{warrior.name} needs {quote['required_xp']} Veteran XP; only {quote['available_xp']} available."
        total_gc = warrior.cost + quote["experience_gc"]
        if total_gc > self.projected_gold():
            return False, f"Not enough gold: {total_gc} gc needed (recruit + experience cost), {self.projected_gold()} gc available."
        if self.projected_warband_members() + 1 > self.effective_maximum_models():
            return False, f"Cannot exceed {self.effective_maximum_models()} warband members."
        try:
            profile = self.port.profile(self.campaign.collection, self.campaign.band_id, warrior.profile_id)
        except Exception:
            return False, f"Unknown profile: {warrior.profile_id}"
        taken = sum(row.quantity for row in self.campaign.warriors if row.profile_id == warrior.profile_id)
        if profile.member_maximum is not None and taken + 1 > profile.member_maximum:
            return False, f"Roster limit for {profile.name} reached ({taken}/{profile.member_maximum})."
        if profile.group_maximum is not None and warrior.quantity + 1 > profile.group_maximum:
            return False, f"{warrior.name} holds at most {profile.group_maximum} models."

        warrior.quantity += 1
        for item in warrior.equipment:
            if item.per_model and not item.transferable:
                item.quantity += 1
        self.post.veteran_pool -= quote["required_xp"]
        self.post.gold_delta -= total_gc
        for item in warrior.equipment:
            if item.per_model and item.transferable and item.quantity < warrior.quantity:
                missing = warrior.quantity - item.quantity
                self.post.equipment_obligations.append({
                    "warrior_id": warrior.id, "item_id": item.item_id,
                    "item_name": item.name, "quantity": missing,
                })
        self._log(self.STEP_RECRUITMENT, "recruit_member", f"One member joined {warrior.name} for {total_gc} gc.", warrior_id=warrior.id)
        return True, f"One member joined {warrior.name} for {total_gc} gc; equipment remains pending."

    def recruitment_eligibility(self, kind: str) -> tuple:
        """Public eligibility of every KB profile of one kind for hiring.

        Returns (profile, allowed, reason) rows so the GUI never mirrors the
        engine's roster limits.
        """
        campaign = self.campaign
        allowed_rows = []
        for profile in self.port.profiles(campaign.collection, campaign.band_id, kind=kind):
            reason = self._recruitment_blocker(profile, kind)
            allowed_rows.append((profile, reason is None, reason or ""))
        return tuple(allowed_rows)

    def _recruitment_blocker(self, profile, kind: str) -> str | None:
        campaign = self.campaign
        if self.projected_warband_members() >= self.effective_maximum_models():
            return f"the warband is at its maximum of {self.effective_maximum_models()} members"
        if profile.cost > self.projected_gold():
            return f"{profile.cost} gc needed, {self.projected_gold()} gc available"
        taken = sum(row.quantity for row in campaign.warriors if row.profile_id == profile.profile_id)
        if profile.member_maximum is not None and taken >= profile.member_maximum:
            return f"roster limit reached ({taken}/{profile.member_maximum})"
        if kind == "hero" and self.projected_heroes() >= campaign.hero_limit:
            return f"the hero maximum is {campaign.hero_limit}"
        return None

    def dismiss_warrior(self, warrior_id: str, *, one_member: bool = False) -> tuple[bool, str]:
        """Dismiss a warrior, returning transferable carried gear to stash."""
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"
        removing_member = warrior.kind == "henchman" and one_member and warrior.quantity > 1
        amount = 1 if removing_member else warrior.quantity
        for item in list(warrior.equipment):
            returned = min(amount if item.per_model else item.quantity, item.quantity)
            if item.transferable and returned:
                inventory = self._inventory_row(item.item_id, name=item.name, price_gc=item.unit_cost)
                inventory.equipped = max(0, inventory.equipped - returned)
                inventory.stash += returned
                inventory.owned = max(inventory.owned, inventory.equipped + inventory.stash)
            item.quantity -= returned
            if item.quantity <= 0:
                warrior.equipment.remove(item)
        if removing_member:
            warrior.quantity -= 1
            message = f"One member dismissed from {warrior.name}; transferable equipment returned to stash."
            self._log(self.STEP_RECRUITMENT, "dismiss_member", message, warrior_id=warrior.id)
            return True, message
        self.campaign.warriors.remove(warrior)
        message = f"{warrior.name} dismissed; transferable equipment returned to stash."
        self._log(self.STEP_RECRUITMENT, "dismiss_warrior", message, warrior_id=warrior.id)
        return True, message

    def resolve_hireling_upkeep(self, followup_id: str, *, pay: bool) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups
                    if item.get("id") == followup_id and item.get("type") == "hireling_upkeep"), None)
        if row is None:
            return False, "Unknown Hired Sword upkeep."
        warrior = next((item for item in self.campaign.warriors if item.id == row.get("warrior_id")), None)
        if warrior is None:
            self.post.pending_follow_ups.remove(row)
            return True, "The Hired Sword already left the warband."
        if pay:
            costs = [(str(key), int(value)) for key, value in row.get("costs") or ()]
            short = self._check_resource_costs(costs)
            if short:
                return False, short
            paid = self._pay_resource_costs(costs)
            warrior.special_rules[:] = [rule for rule in warrior.special_rules
                                        if not rule.startswith("Returning a Favour:")]
            message = f"{warrior.name}'s upkeep paid: {paid}."
        else:
            self._discard_carried_equipment(warrior, weapons_and_armour_only=False)
            self.campaign.warriors.remove(warrior)
            message = f"{warrior.name} leaves because upkeep was not paid."
        self.post.pending_follow_ups.remove(row)
        self._log(self.STEP_RECRUITMENT, "hireling_upkeep", message, warrior_id=warrior.id)
        return True, message

    def scenario_spell_options(self, hero_id: str) -> tuple[dict, ...]:
        hero = next((row for row in self.campaign.warriors if row.id == hero_id and row.kind == "hero"), None)
        if hero is None:
            return ()
        lores = ["lore.lesser-magic"]
        own_lore = self.port.wizard_lore(hero.profile_id, self.campaign.band_id)
        if own_lore and own_lore not in lores:
            lores.append(own_lore)
        result = []
        for lore in lores:
            for spell in self.port.lore_spells(lore):
                row = dict(spell); row["lore_id"] = lore
                result.append(row)
        return tuple(result)

    def resolve_scenario_spell_reward(self, followup_id: str, hero_id: str,
                                      spell_ids: list[str]) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        followup = next((row for row in self.post.pending_follow_ups
                         if row.get("id") == followup_id and row.get("type") == "scenario_spell_reward"), None)
        hero = next((row for row in self.campaign.warriors if row.id == hero_id and row.kind == "hero"), None)
        if followup is None or hero is None:
            return False, "Unknown Tome of Magic reward or Hero."
        selected = list(dict.fromkeys(str(value) for value in spell_ids))
        if len(selected) != 2:
            return False, "Choose exactly two different spells."
        options = {str(row.get("id") or ""): row for row in self.scenario_spell_options(hero_id)}
        if any(spell_id not in options for spell_id in selected):
            return False, "One selected spell is not available to this Hero."
        names = []
        for spell_id in selected:
            name = str(options[spell_id].get("name") or spell_id)
            if name in hero.skills:
                return False, f"{hero.name} already knows {name}; choose another spell."
            names.append(name)
        hero.skills.extend(names)
        self.post.pending_follow_ups.remove(followup)
        self._log(self.STEP_EXPLORATION, "scenario_spell_reward",
                  f"{hero.name} learns {' and '.join(names)} from the Tome of Magic", warrior_id=hero.id)
        return True, f"{hero.name} learns {' and '.join(names)}."

    def resolve_scenario_encampment(self, followup_id: str, choice: str) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        row = next((item for item in self.post.pending_follow_ups
                    if item.get("id") == followup_id and item.get("type") == "scenario_encampment"), None)
        if row is None or choice not in {"destroy", "occupy"}:
            return False, "Choose whether to destroy or occupy the camp."
        if choice == "occupy":
            text = "Captured camp occupied; captured stash contents are recorded manually during Equipment."
            self.campaign.special_rules.append({"source": followup_id, "text": text,
                                                "expires_after_battles": None,
                                                "consume_when_opponent_contains": []})
            message = "The warband occupies the captured camp. Add the captured stash during Equipment."
        else:
            message = "The captured camp is destroyed. Add any claimed stash during Equipment."
        self.post.pending_follow_ups.remove(row)
        self._log(self.STEP_EXPLORATION, "scenario_encampment", message, choice=choice)
        return True, message

    def recruit_band_profile(self, profile_id: str, quantity: int = 1, name: str | None = None) -> tuple[bool, str]:
        """Recruit a hero or henchman group from the warband's KB roster."""
        if self.post is None:
            return False, "No pending post-battle."
        campaign = self.campaign
        try:
            profile = self.port.profile(campaign.collection, campaign.band_id, profile_id)
        except Exception:
            return False, f"Unknown profile: {profile_id}"
        quantity = max(1, int(quantity))
        cost = profile.cost * quantity
        if cost > self.projected_gold():
            return False, f"Not enough gold: {cost} gc needed, {self.projected_gold()} gc available."
        if self.projected_warband_members() + quantity > self.effective_maximum_models():
            return False, f"Cannot exceed {self.effective_maximum_models()} warband members."
        taken = sum(row.quantity for row in campaign.warriors if row.profile_id == profile.profile_id)
        if profile.member_maximum is not None and taken + quantity > profile.member_maximum:
            return False, f"Roster limit for {profile.name} reached ({taken}/{profile.member_maximum})."
        if profile.kind == "hero" and self.projected_heroes() + quantity > campaign.hero_limit:
            return False, f"Cannot exceed {campaign.hero_limit} heroes."
        if profile.kind == "henchman" and profile.group_maximum is not None and quantity > profile.group_maximum:
            return False, f"Groups of {profile.name} hold at most {profile.group_maximum} models."
        occurrences = sum(1 for row in campaign.warriors if row.profile_id == profile_id and row.kind == profile.kind)
        base_name = profile.name if profile.kind == "hero" else f"{profile.name} Group"
        unique_name = unique_warrior_name(campaign.warriors, name.strip() if name and name.strip() else base_name)
        row = warrior_vm(self.port, profile, row_id=f"{profile_id}#recruit{occurrences + 1}", name=unique_name, quantity=quantity)
        campaign.warriors.append(row)
        self.post.gold_delta -= cost
        message = f"{profile.name} ×{quantity} recruited for {cost} gc."
        self._log(self.STEP_RECRUITMENT, "recruit", message, warrior_id=row.id, profile_id=profile_id)
        return True, message

    def hire_hireling(self, offer: "HirelingOffer", *, acceptance_roll: int | None = None, fee_roll: int | None = None) -> tuple[bool, str]:
        """Hire a Hired Sword or Dramatis Persona whose fee is paid in gold.

        Variable fees (e.g. the ninja's 70+3D6 gc) need ``fee_roll``, the total
        of the KB-declared dice; the engine never rolls by itself.
        """
        if self.post is None:
            return False, "No pending post-battle."
        if offer.eligibility == "variant":
            return False, "This hire needs the warband's Mercenary variant, which is not selected yet."
        if offer.eligibility == "conditional":
            if offer.roll_ge is None:
                return False, "This hire requires an acceptance roll that is not declared."
            if acceptance_roll is None:
                return False, f"An acceptance roll of {offer.roll_ge}+ is required before hiring."
            if int(acceptance_roll) < offer.roll_ge:
                return False, f"Acceptance roll {acceptance_roll} failed (needed {offer.roll_ge}+); the hire is declined."
        costs = list(offer.fee_resources)
        if offer.fee_dice is not None:
            if offer.fee_gc is not None:
                return False, f"{offer.name} declares both a flat and a variable fee; the KB entry is inconsistent."
            if fee_roll is None:
                count, sides = offer.fee_dice
                return False, f"Roll {offer.name}'s hiring fee ({count}D{sides} + {offer.fee_base_gc} gc) before hiring."
            if int(fee_roll) < offer.fee_dice[0]:
                return False, f"Fee roll {fee_roll} is below the minimum {offer.fee_dice[0]} of {offer.fee_dice[0]}D{offer.fee_dice[1]}."
            costs.append(("gold_crowns", int(offer.fee_base_gc or 0) + int(fee_roll)))
        elif offer.fee_gc is not None and not any(resource == "gold_crowns" for resource, _amount in costs):
            costs.append(("gold_crowns", offer.fee_gc))
        if not costs:
            return False, f"{offer.name} declares no hiring fee the application can charge."
        short = self._check_resource_costs(costs)
        if short:
            return False, short
        if any(row.kind == "hireling" and row.profile_id == offer.profile_id for row in self.campaign.warriors):
            return False, f"Only one {offer.name} may be employed by the warband."
        row = self.hireling_warrior(offer)
        if row is None:
            return False, f"Hireling profile not found in the KB: {offer.profile_id}"
        self.campaign.warriors.append(row)
        paid = self._pay_resource_costs(costs)
        self._log(self.STEP_SEARCHES, "hire", f"{offer.name} hired for {paid}", profile_id=offer.profile_id)
        return True, f"{offer.name} hired for {paid}."

    #: Human labels of the KB hiring resources.
    RESOURCE_LABELS = {
        "gold_crowns": "gc",
        "wyrdstone_fragments": "wyrdstone shard(s)",
        "treasures": "treasure(s)",
        "campaign_points": "campaign point(s)",
    }

    def _resource_available(self, resource: str) -> int:
        if resource == "gold_crowns":
            return self.projected_gold()
        if resource == "wyrdstone_fragments":
            return self.projected_shards()
        if resource == "treasures":
            return self.campaign.treasures
        if resource == "campaign_points":
            return self.campaign.campaign_points
        return 0

    def _spend_resource(self, resource: str, amount: int) -> None:
        if resource == "gold_crowns":
            self.post.gold_delta -= amount
        elif resource == "wyrdstone_fragments":
            self.post.wyrdstone_delta -= amount
        elif resource == "treasures":
            self.campaign.treasures -= amount
        elif resource == "campaign_points":
            self.campaign.campaign_points -= amount

    def _check_resource_costs(self, costs) -> str | None:
        for resource, amount in costs:
            label = self.RESOURCE_LABELS.get(resource, resource)
            available = self._resource_available(resource)
            if amount > available:
                return f"Not enough {label}: {amount} needed, {available} available."
        return None

    def _pay_resource_costs(self, costs) -> str:
        pieces: list[str] = []
        for resource, amount in costs:
            self._spend_resource(resource, amount)
            pieces.append(f"{amount} {self.RESOURCE_LABELS.get(resource, resource)}")
        return " + ".join(pieces)

    def hireling_warrior(self, offer: "HirelingOffer") -> WarriorVM | None:
        catalogue = self.port.hireling_catalogue()
        profile = next(
            (row for row in catalogue.profiles if str(row.get("id") or "") == offer.profile_id),
            None,
        )
        if profile is None:
            return None
        characteristics = profile.get("characteristics") or {}
        stats = {key: int(value) if value is not None else 0 for key, value in characteristics.items()}
        equipment = []
        for item in (profile.get("equipment") or {}).get("fixed_items") or ():
            item_id = str(item.get("item_id") or "")
            if not item_id:
                continue
            quantity = 1
            quantity_block = item.get("quantity") or {}
            if isinstance(quantity_block, dict):
                value = quantity_block.get("value")
                if isinstance(value, int):
                    quantity = value
            equipment.append(EquipmentEntryVM(item_id, self.port.item_name(item_id) or item_id, quantity, "hireling_grant", 0, False, False))
        occurrences = sum(
            1 for row in self.campaign.warriors
            if row.profile_id == offer.profile_id and row.kind == "hireling"
        )
        rating, maximum_modifier = self.port.hireling_roster_values(offer.profile_id)
        return WarriorVM(
            id=f"{offer.profile_id}#hire{occurrences + 1}",
            name=offer.name,
            profile_name=offer.name,
            kind="hireling",
            stats=stats,
            equipment=equipment,
            skills=[],
            experience=0,
            quantity=1,
            cost=offer.fee_gc or 0,
            skill_access=[],
            profile_id=offer.profile_id,
            hireling_rating=rating,
            maximum_models_modifier=maximum_modifier,
            upkeep_resources=list(offer.upkeep_resources),
        )

    # ------------------------------------------------------------------ commit

    def commit(self) -> tuple[bool, str]:
        """Create the next immutable State and close the pending post-battle."""
        if self.post is None:
            return False, "No pending post-battle."
        if self.post.complete:
            return False, "This post-battle is already committed."
        if len(self.post.completed_steps) < NEW_STATE_STEPS:
            return False, f"Only {len(self.post.completed_steps)} of {NEW_STATE_STEPS} actions completed."
        if self.projected_warband_members() > self.effective_maximum_models():
            return False, (
                f"The warband has {self.projected_warband_members()} own members but its current maximum "
                f"is {self.effective_maximum_models()}; dismiss members before committing."
            )
        campaign = self.campaign
        number = self.post.battle_number
        # A battle recorded from the table may not have a State #N-1 snapshot
        # (the previous post-battle was skipped): fall back to the current state.
        base = self._base_state()
        if base is None and self.campaign.states:
            base = self.campaign.current_state
        snapshot = WarbandStateVM(
            number=number,
            date=_today(),
            gold=self.projected_gold(),
            wyrdstone=self.projected_shards(),
            rating=self.projected_rating(),
            models=self.projected_models(),
            max_models=self.effective_maximum_models(),
            heroes=self.projected_heroes(),
            henchmen=self.projected_henchmen(),
            experience=self.projected_experience(),
            label="Current Warband",
            roster=copy.deepcopy(campaign.warriors),
            inventory=copy.deepcopy(campaign.inventory),
        )
        campaign.states.append(snapshot)
        campaign.current_state_number = number
        self.post.complete = True
        self.post.completed_steps = set(range(NEW_STATE_STEPS))
        self.post.review_open = False
        return (
            True,
            f"State #{number} committed: {snapshot.models} models · rating {snapshot.rating} · "
            f"{snapshot.gold} gc · {snapshot.wyrdstone} shards.",
        )
