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

from datetime import date
from typing import TYPE_CHECKING

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_resolution import SeriousInjuryOutcome
from mordheim_campaign.application.state import InventoryItemVM, WarbandStateVM, WarriorVM, warrior_vm

if TYPE_CHECKING:
    from mordheim_campaign.application.post_battle_catalogue import HirelingOffer
    from mordheim_campaign.application.state import CampaignVM, PostBattleVM

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

    def __init__(self, port: KnowledgePort, campaign: "CampaignVM", post: "PostBattleVM | None") -> None:
        self.port = port
        self.campaign = campaign
        self.post = post

    # ------------------------------------------------------------ projections

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
        return sum(row.quantity for row in self.campaign.warriors)

    def projected_heroes(self) -> int:
        return sum(row.quantity for row in self.campaign.warriors if row.kind == "hero")

    def projected_henchmen(self) -> int:
        return sum(row.quantity for row in self.campaign.warriors if row.kind == "henchman")

    def projected_experience(self) -> int:
        return sum(row.experience * row.quantity for row in self.campaign.warriors)

    def projected_rating(self) -> int:
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        return PostBattleResolver(self.port).warband_rating(
            self.projected_models(), self.projected_experience()
        )

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

        notes: list[str] = []
        for effect in outcome.effects_raw:
            kind = str(effect.get("type") or "")
            if kind == "roster.remove_warrior":
                if warrior.kind == "henchman" and warrior.quantity > 1:
                    warrior.quantity -= 1
                    notes.append("the group loses one member")
                else:
                    self.campaign.warriors.remove(warrior)
                    notes.append(f"{warrior.name} leaves the roster")
            elif kind == "warrior.characteristic_modifier":
                key = _CHARACTERISTIC_KEYS.get(str(effect.get("characteristic") or ""))
                if key is not None:
                    modifier = int(effect.get("modifier") or 0)
                    warrior.stat_modifiers[key] = warrior.stat_modifiers.get(key, 0) + modifier
                    notes.append(f"{key} {modifier:+d}")
            elif kind == "warrior.add_condition":
                warrior.condition = "Injured"
                warrior.condition_detail = str(effect.get("condition_id") or "lasting condition")
                notes.append("gains a lasting condition")
            elif kind == "warrior.miss_games":
                games = effect.get("games") or {}
                value = int(games.get("value") or 1) if isinstance(games, dict) else int(games or 1)
                warrior.condition = "Injured"
                warrior.condition_detail = f"Misses {value} game{'s' if value != 1 else ''}"
                notes.append(f"misses {value} game{'s' if value != 1 else ''}")
            elif kind == "equipment.disposition":
                scope = str(effect.get("scope") or "")
                disposition = str(effect.get("disposition") or "lost")
                if scope == "carried_by_subject" and warrior.equipment:
                    lost = list(warrior.equipment)
                    warrior.equipment.clear()
                    notes.append(f"{disposition}: {' · '.join(lost)}")
            else:
                notes.append(str(effect.get("type") or "").replace("_", " "))
        if not notes:
            return True, f"{warrior.name}: no lasting effect on the roster."
        return True, f"{warrior.name}: {' · '.join(notes)}."

    # ------------------------------------------------------------- experience

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

    def resolve_pending_advance(self, warrior_id: str, roll_total: int, subroll: int | None = None) -> tuple[bool, str]:
        """Resolve the 2D6 roll (and optional D6 sub-roll) of a pending advance."""
        if self.post is None:
            return False, "No pending post-battle."
        row = self.post.pending_advance_for(warrior_id)
        if row is None:
            return False, f"No pending advance for: {warrior_id}"
        if row.get("committed"):
            return False, "This advance is already committed."
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
        if row.get("promotion_pending"):
            return True, "Promotion in progress: pick the promoted member's second skill."
        row["promotion_offer"] = bool(outcome.final and outcome.note == "promotion")
        if outcome.final and len(outcome.options) == 1 and outcome.options[0].kind != "promote_henchman":
            # Single deterministic option (one characteristic): commit directly.
            ok, message = self.commit_pending_advance(warrior_id, option_kind=outcome.options[0].kind)
            return ok, message
        return True, f"{outcome.title} · {outcome.detail}" if outcome.detail else outcome.title

    def is_wizard(self, warrior_id: str) -> bool:
        """True when the KB assigns this warrior's profile a spell lore."""
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None or not warrior.profile_id:
            return False
        return self.port.wizard_lore(warrior.profile_id, self.campaign.band_id) is not None

    def _pending_outcome(self, warrior_id: str):
        """The resolved KB outcome of a pending advance row (or ``None``)."""
        row = self.post.pending_advance_for(warrior_id) if self.post is not None else None
        if row is None or row.get("roll_total") is None:
            return None, row
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        resolver = PostBattleResolver(self.port)
        kind = str(row.get("table") or "hero")
        outcome = resolver.resolve_advancement(kind, int(row["roll_total"]), is_wizard=self.is_wizard(warrior_id))
        if not outcome.final and row.get("subroll") is not None:
            outcome = resolver.resolve_advancement_subroll(kind, int(row["roll_total"]), int(row["subroll"]))
        return outcome, row

    def advance_options(self, warrior_id: str):
        """Selectable options of a resolved pending advance (may be empty)."""
        outcome, _row = self._pending_outcome(warrior_id)
        return outcome.options if outcome is not None and outcome.final else ()

    def _warrior_race(self, warrior) -> str | None:
        """Race used for racial maximums, resolved from the warband registry."""
        if not self.campaign.band_id:
            return None
        for group in self.port.warband_groups():
            if str(group.get("id") or "") in self._BAND_RACE and self.campaign.band_id in set(group.get("band_ids") or ()):
                return self._BAND_RACE[str(group["id"])]
        return None

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
        row = self.post.pending_advance_for(warrior_id)
        if row is None or row.get("roll_total") is None:
            return False, "Resolve the advance roll first."
        if row.get("committed"):
            return False, "This advance is already committed."
        outcome, row = self._pending_outcome(warrior_id)
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

        if option_kind == "promote_henchman":
            return self.promote_henchman(warrior_id)

        return False, f"Unsupported advance option: {option_kind}"

    # ------------------------------------------------------------- promotion

    #: Pending Lad's Got Talent promotions of this sequence (warrior group ids);
    #: each grants one hero-slot allowance over the static ``hero_limit``.
    def _promotion_hero_allowance(self) -> int:
        if self.post is None:
            return 0
        return sum(
            1
            for row in self.post.pending_advances
            if row.get("promotion_offer") and not row.get("committed") and not row.get("promotion_pending")
        )

    def promotion_hero_tables(self, warrior_id: str) -> tuple[str, ...]:
        """Warband hero skill-table labels for a promoted member's 2 picks."""
        campaign = self.campaign
        heroes = [row for row in campaign.warriors if row.kind == "hero"]
        tables: list[str] = []
        for hero_row in heroes:
            for table in hero_row.skill_access or ():
                if table not in tables:
                    tables.append(table)
        return tuple(tables)

    def promotion_pick_budget(self, warrior_id: str) -> int:
        """Skills still to pick for a pending promotion (2 in total)."""
        if self.post is None:
            return 0
        row = self.post.pending_advance_for(warrior_id)
        if row is None or not row.get("promotion_pending"):
            return 0
        return max(0, 2 - int(row.get("promotion_skills") or 0))

    def commit_promotion_skill(self, warrior_id: str, skill_name: str) -> tuple[bool, str]:
        """One of the two skill picks of a pending Lad's Got Talent promotion."""
        if self.post is None:
            return False, "No pending post-battle."
        warrior = next((row for row in self.campaign.warriors if row.id == warrior_id), None)
        if warrior is None or warrior.kind != "hero":
            return False, "Promote the group member before choosing skills."
        row = self.post.pending_advance_for(warrior_id)
        if row is None or not row.get("promotion_pending"):
            return False, "No pending promotion for this warrior."
        if self.promotion_pick_budget(warrior_id) <= 0:
            return False, "Both promotion skills are already chosen."
        skill = self.port.skill_by_name(skill_name)
        if skill is None:
            return False, f"Unknown skill: {skill_name}"
        if skill_name in warrior.skills:
            return False, f"{warrior.name} already knows {skill_name}."
        tables = self.promotion_hero_tables(warrior_id)
        table = self.port.skill_table_label(skill)
        if tables and table not in tables:
            return False, f"{skill_name} is not on the warband's hero skill tables ({', '.join(tables)})."
        warrior.skills.append(skill_name)
        row["promotion_skills"] = int(row.get("promotion_skills") or 0) + 1
        remaining = self.promotion_pick_budget(warrior_id)
        if remaining == 0:
            row["promotion_pending"] = False
            row["committed"] = True
            row["applied_label"] = f"Promoted · skills: {' + '.join(warrior.skills[-2:])}"
            return True, f"{warrior.name} completes the promotion ({warrior.skills[-2]} and {warrior.skills[-1]})."
        return True, f"{warrior.name} learns {skill_name} ({remaining} promotion pick left)."

    def promote_henchman(self, warrior_id: str, *, member_name: str | None = None) -> tuple[bool, str]:
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
        if warrior.quantity < 2:
            return False, "A group of one cannot split; promote the whole row is not supported yet."
        campaign = self.campaign
        heroes = self.projected_heroes()
        if heroes + 1 > campaign.hero_limit + self._promotion_hero_allowance():
            return False, (
                f"The warband is at its hero maximum ({campaign.hero_limit}) and no promotion "
                "allowance is pending; reroll this advance instead."
            )
        try:
            profile = self.port.profile(campaign.collection, campaign.band_id, warrior.profile_id)
        except Exception:
            return False, f"Unknown profile: {warrior.profile_id}"

        promoted_name = member_name or f"{warrior.profile_name} Champion"
        hero_row = WarriorVM(
            id=f"{warrior.profile_id}#promoted{sum(1 for r in campaign.warriors if r.profile_id == warrior.profile_id)}",
            name=promoted_name,
            profile_name=warrior.profile_name,
            kind="hero",
            stats=dict(warrior.stats),  # preserve accumulated characteristic increases
            equipment=list(warrior.equipment),  # one set stays with the promoted member
            skills=[skill for skill in warrior.skills if skill not in profile.inherent_rules],
            experience=warrior.experience,  # preserve experience
            previous_experience=warrior.previous_experience,
            quantity=1,
            cost=profile.cost,
            skill_access=list(profile.skill_tables),
            stat_advances=dict(warrior.stat_advances),  # preserve advances (KB "preserve")
            profile_id=warrior.profile_id,
        )
        campaign.warriors.append(hero_row)
        warrior.quantity -= 1
        if not warrior.name.endswith(" group"):
            warrior.name = f"{warrior.profile_name} group"

        row = self.post.pending_advance_for(warrior_id)
        if row is not None:
            row["promotion_pending"] = True
            row["promotion_skills"] = 0
            row["warrior_id"] = hero_row.id  # the 2 picks continue on the new hero
            row["warrior_name"] = hero_row.name
        return True, (
            f"{promoted_name} promoted to Hero: pick 2 skills from the warband's hero tables. "
            "The remaining group rerolls this advance."
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

        resolved = PostBattleResolver(self.port).resolve_exploration(tuple(int(value) for value in dice))
        self.post.wyrdstone_delta += resolved.shards
        message = f"{resolved.shards} wyrdstone shard(s) added to the hoard."
        if resolved.matching_dice_note:
            message += f" {resolved.matching_dice_note}"
        return True, message

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

        size = warband_size if warband_size is not None else self.projected_models()
        value = PostBattleResolver(self.port).wyrdstone_sale_value(quantity, size)
        self.post.wyrdstone_sold += quantity
        self.post.gold_delta += value
        self.post.sale_resolved = True
        return True, f"Sold {quantity} shard(s) for {value} gc."

    # --------------------------------------------------------------- veterans

    def apply_veteran_pool(self, pool: int) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        self.post.veteran_pool = max(0, int(pool))
        return True, f"Veteran experience pool set to {self.post.veteran_pool} XP."

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

    def buy_item(self, item_id: str, quantity: int, price_gc: int | None) -> tuple[bool, str]:
        if self.post is None:
            return False, "No pending post-battle."
        quantity = max(1, int(quantity))
        if price_gc is None:
            return False, "This item has no flat price; purchases are not supported yet."
        cost = price_gc * quantity
        if cost > self.projected_gold():
            return False, f"Not enough gold: {cost} gc needed, {self.projected_gold()} gc available."
        row = self._inventory_row(item_id, name=self.port.item_name(item_id) or item_id, price_gc=price_gc)
        row.owned += quantity
        row.stash += quantity
        row.value = price_gc
        self.post.gold_delta -= cost
        return True, f"{quantity}× {row.name} bought for {cost} gc (stash)."

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
        if row is None or row.stash < 1:
            return False, f"No unassigned {row.name if row else item_id or 'item'} in the stash."
        warrior = next((w for w in self.campaign.warriors if w.id == warrior_id), None)
        if warrior is None:
            return False, f"Unknown warrior: {warrior_id}"
        row.stash -= 1
        row.equipped += 1
        warrior.equipment.append(row.name)
        return True, f"{row.name} assigned to {warrior.name}."

    def return_warrior_to_stash(self, item_id: str, warrior_id: str) -> tuple[bool, str]:
        """Return one equipped copy to the stash (keeps ``owned`` intact)."""
        row = next((item for item in self.campaign.inventory if item.id == item_id), None)
        warrior = next((w for w in self.campaign.warriors if w.id == warrior_id), None)
        if row is None or warrior is None:
            return False, "Unknown warrior or item."
        if row.name not in warrior.equipment:
            return False, f"{warrior.name} does not carry {row.name}."
        warrior.equipment.remove(row.name)
        row.equipped = max(0, row.equipped - 1)
        row.stash += 1
        return True, f"{row.name} returned to the stash from {warrior.name}."

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
        return True, f"Sold {quantity}× {row.name} for {price * quantity} gc."

    # ------------------------------------------------------------- recruitment

    def recruit_band_profile(self, profile_id: str, quantity: int = 1) -> tuple[bool, str]:
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
        if self.projected_models() + quantity > campaign.maximum_models:
            return False, f"Cannot exceed {campaign.maximum_models} models."
        taken = sum(row.quantity for row in campaign.warriors if row.profile_id == profile.profile_id)
        if profile.member_maximum is not None and taken + quantity > profile.member_maximum:
            return False, f"Roster limit for {profile.name} reached ({taken}/{profile.member_maximum})."
        if profile.kind == "hero" and self.projected_heroes() + quantity > campaign.hero_limit + self._promotion_hero_allowance():
            return False, f"Cannot exceed {campaign.hero_limit} heroes."
        if profile.kind == "henchman" and profile.group_maximum is not None and quantity > profile.group_maximum:
            return False, f"Groups of {profile.name} hold at most {profile.group_maximum} models."
        occurrences = sum(1 for row in campaign.warriors if row.profile_id == profile_id and row.kind == profile.kind)
        row = warrior_vm(profile, row_id=f"{profile_id}#recruit{occurrences + 1}", quantity=quantity)
        campaign.warriors.append(row)
        self.post.gold_delta -= cost
        return True, f"{profile.name} ×{quantity} recruited for {cost} gc."

    def hire_hireling(self, offer: "HirelingOffer", *, acceptance_roll: int | None = None) -> tuple[bool, str]:
        """Hire a Hired Sword or Dramatis Persona whose fee is paid in gold."""
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
        if offer.fee_gc is None:
            return False, f"{offer.name} is hired for resources other than gold; hiring is not supported yet."
        if offer.fee_gc > self.projected_gold():
            return False, f"Not enough gold: {offer.fee_gc} gc needed, {self.projected_gold()} gc available."
        if self.projected_models() + 1 > self.campaign.maximum_models:
            return False, f"Cannot exceed {self.campaign.maximum_models} models."
        row = self._hireling_warrior(offer)
        if row is None:
            return False, f"Hireling profile not found in the KB: {offer.profile_id}"
        self.campaign.warriors.append(row)
        self.post.gold_delta -= offer.fee_gc
        return True, f"{offer.name} hired for {offer.fee_gc} gc."

    def _hireling_warrior(self, offer: "HirelingOffer") -> WarriorVM | None:
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
            equipment.extend([self.port.item_name(item_id) or item_id] * quantity)
        occurrences = sum(
            1 for row in self.campaign.warriors
            if row.profile_id == offer.profile_id and row.kind == "henchman"
        )
        return WarriorVM(
            id=f"{offer.profile_id}#hire{occurrences + 1}",
            name=offer.name,
            profile_name=offer.name,
            kind="henchman",
            stats=stats,
            equipment=equipment,
            skills=[],
            experience=0,
            quantity=1,
            cost=offer.fee_gc or 0,
            skill_access=[],
            profile_id=offer.profile_id,
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
            max_models=campaign.maximum_models,
            heroes=self.projected_heroes(),
            henchmen=self.projected_henchmen(),
            experience=self.projected_experience(),
            label="Current Warband",
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