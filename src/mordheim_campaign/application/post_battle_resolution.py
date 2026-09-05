"""application.post_battle_resolution: KB-backed post-battle dice resolution.

Pure read-side use case between the KB loaders and the widgets (the HOWTO
pattern): the UI asks ``PostBattleResolver`` to turn dice + choices into the
outcomes the campaign catalogues define, instead of displaying canned text.
It never decides rules beyond reading the validated catalogues through
``KnowledgePort`` and never touches campaign state: purchases, treasury and
roster mutations remain application/persistence work elsewhere.

Implemented resolutions
-----------------------
- Serious injuries (``serious-injuries.yaml``): the hero D66 chart and the
  henchman D6 chart, including typed effect summaries.
- Exploration (``exploration-and-income.yaml``): dice allocation, wyrdstone
  shards by total and the matching-dice special results.
- Rare-item search (``trading-and-rarity.yaml``): the 2D6 rarity test against
  the Trading Post availability of a requested item.
"""
from __future__ import annotations

from dataclasses import dataclass

from mordheim_campaign.application.knowledge_port import KnowledgePort


@dataclass(frozen=True, slots=True)
class SeriousInjuryOutcome:
    """One row of the serious-injury chart, resolved for a roll."""

    table: str  # "hero" | "henchman"
    roll: int  # D66 value (11-66) or D6 value
    result_id: str
    result: str
    effects: tuple[str, ...]  # human summaries of the typed effects
    follow_up: str | None  # what the outcome needs next (reroll / subtable)
    #: The typed effect rows as declared in the catalogue; the write side
    #: (post-battle engine) applies them to the roster.
    effects_raw: tuple[dict, ...] = ()


@dataclass(frozen=True, slots=True)
class ExplorationResult:
    """Exploration for one warband's post-battle phase."""

    dice_count: int
    dice: tuple[int, ...]
    total: int
    shards: int
    matches: tuple[tuple[int, int, str], ...]  # (die value, count, outcome)
    matching_dice_note: str


@dataclass(frozen=True, slots=True)
class RaritySearch:
    """Result of one hero's rare-item search."""

    item_id: str
    rarity: int | None  # None = common (no test needed)
    roll_total: int
    modifiers: int
    success: bool
    note: str


#: Full characteristic names used by the KB effect types -> display keys.
CHARACTERISTIC_KEYS = {
    "movement": "M", "weapon_skill": "WS", "ballistic_skill": "BS",
    "strength": "S", "toughness": "T", "wounds": "W", "initiative": "I",
    "attacks": "A", "leadership": "Ld",
}



@dataclass(frozen=True, slots=True)
class AdvancementOption:
    """One selectable improvement of an advance roll."""

    kind: str  # characteristic_increase | choose_skill | generate_spell | promote_henchman
    label: str
    characteristic: str | None = None  # display key (M/WS/…) for increases
    amount: int = 0


@dataclass(frozen=True, slots=True)
class AdvancementOutcome:
    """Resolved 2D6 row of the hero/henchman advancement table."""

    table: str  # "hero" | "henchman"
    roll: int  # 2D6 total
    title: str
    detail: str
    final: bool  # False: a D6 sub-roll is still required
    options: tuple[AdvancementOption, ...] = ()
    note: str = ""
    #: D6 sub-roll result for ``roll_table`` rows (deterministic afterwards).
    subroll: int | None = None


#: Human summaries of the typed serious-injury effects.
_EFFECT_LABELS = {
    "roster.remove_warrior": "removes the warrior from the roster",
    "warrior.characteristic_modifier": "permanent characteristic modifier",
    "warrior.battle_start_check": "battle-start characteristic check",
    "warrior.miss_games": "misses games",
    "warrior.add_condition": "gains a lasting condition",
    "equipment.disposition": "equipment is lost or sold",
    "prisoner.create": "warrior is captured",
    "encounter.trigger": "triggers a special encounter",
    "reward.grant": "gains a reward",
}


def _effect_labels(effects) -> tuple[str, ...]:
    labels = []
    for effect in effects or ():
        kind = str(effect.get("type") or "")
        label = _EFFECT_LABELS.get(kind, kind.replace("_", " "))
        if kind == "warrior.characteristic_modifier":
            characteristic = effect.get("characteristic")
            modifier = effect.get("modifier")
            if characteristic and modifier is not None:
                label = f"permanent {characteristic} {int(modifier):+d}"
        labels.append(label)
    return tuple(dict.fromkeys(labels))


def _d66_index(tens: int, ones: int) -> int:
    """Printed-chart position of a D66 roll (row-major: 11..16, 21..26 …)."""
    return (tens - 1) * 6 + (ones - 1)


def _inf(value) -> int:
    return 10**9 if value is None else int(value)


def _range_contains(roll: str, tens: int, ones: int) -> bool:
    """Whether a D66 roll falls inside a chart range like ``41-55``.

    The printed D66 chart reads row-major; a range spans the region between
    its two corner rolls (e.g. ``16-21`` covers the rolls 16 and 21, and
    ``41-55`` covers 41-46 and 51-55). Matching by row-major position
    reproduces exactly that.
    """
    first, _, last = roll.partition("-")
    if not first or not last:
        return f"{tens}{ones}" == roll
    return _d66_index(int(first[0]), int(first[1])) <= _d66_index(tens, ones) <= _d66_index(int(last[0]), int(last[1]))


class PostBattleResolver:
    """Pure KB lookups used by the post-battle screens (no UI imports)."""

    def __init__(self, port: KnowledgePort) -> None:
        self.port = port

    # ------------------------------------------------------------- injuries

    def _serious_injury_table(self, kind: str) -> list[dict]:
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("serious-injuries.yaml")
        for table in document.get("tables") or ():
            if table.get("applies_to") == kind:
                return list(table.get("results") or ())
        return []

    def _resolve_table_roll(self, kind: str, value: int, tens: int | None = None, ones: int | None = None) -> SeriousInjuryOutcome | None:
        for row in self._serious_injury_table(kind):
            roll_key = str(row.get("roll") or "")
            if kind == "hero" and tens is not None and ones is not None:
                if not _range_contains(roll_key, tens, ones):
                    continue
            elif kind == "henchman":
                low, _, high = roll_key.partition("-")
                if low and high:
                    if not (int(low) <= value <= int(high)):
                        continue
                elif value != int(roll_key):
                    continue
            else:
                continue
            resolution = row.get("resolution")
            follow_up = None
            if isinstance(resolution, dict):
                if resolution.get("type") == "repeat_table":
                    follow_up = "Roll again on the same chart (D66)."
                elif resolution.get("type") == "roll_table":
                    follow_up = "Follow-up D6 subtable required."
            elif row.get("result") == "Multiple Injuries":
                follow_up = "Roll again on the same chart (D66)."
            return SeriousInjuryOutcome(
                table=kind,
                roll=value if kind == "henchman" else tens * 10 + ones,
                result_id=str(row.get("id") or ""),
                result=str(row.get("result") or roll_key),
                effects=_effect_labels(row.get("effects")),
                follow_up=follow_up,
                effects_raw=tuple(dict(effect) for effect in row.get("effects") or ()),
            )
        return None

    def resolve_hero_serious_injury(self, d66: int) -> SeriousInjuryOutcome:
        """Resolve the hero D66 chart (two dice: tens and ones digit)."""
        tens = max(1, min(6, d66 // 10))
        ones = max(1, min(6, d66 % 10))
        outcome = self._resolve_table_roll("hero", 0, tens=tens, ones=ones)
        if outcome is None:
            outcome = SeriousInjuryOutcome("hero", tens * 10 + ones, "", "Full Recovery", (), None)
        return outcome

    def resolve_henchman_serious_injury(self, d6: int) -> SeriousInjuryOutcome:
        """Resolve the henchman D6 chart."""
        roll = max(1, min(6, int(d6)))
        outcome = self._resolve_table_roll("henchman", roll)
        if outcome is None:
            outcome = SeriousInjuryOutcome("henchman", roll, "", "Full Recovery", (), None)
        return outcome

    # ---------------------------------------------------------- exploration

    def exploration_dice(self, surviving_heroes: int, warband_won: bool, *, max_dice: int | None = None) -> int:
        """Exploration dice from the KB ``dice_allocation`` declaration.

        Reads the per-surviving-hero and bonus-if-won entries and the declared
        ``max_dice`` cap of ``exploration-and-income.yaml``; both parameters
        stay so callers may preview before choosing.
        """
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("exploration-and-income.yaml")
        exploration = document.get("exploration") or {}
        dice = 0
        for entry in exploration.get("dice_allocation") or ():
            eligible = str(entry.get("eligible_warrior") or "")
            condition = str(entry.get("condition") or "")
            amount = int(entry.get("dice") or 0)
            if eligible == "hero" and condition == "survived_battle" and surviving_heroes > 0:
                dice += amount * max(0, int(surviving_heroes))
            elif eligible == "warband" and condition == "warband_won_battle" and warband_won:
                dice += amount
        cap = max_dice if max_dice is not None else int(exploration.get("max_dice") or 6)
        return min(dice, max(0, cap))

    def resolve_exploration(self, dice: tuple[int, ...]) -> ExplorationResult:
        """Shards by total and the matching-dice special result (largest set)."""
        values = tuple(sorted(int(d) for d in dice))
        total = sum(values)
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("exploration-and-income.yaml")
        exploration = document.get("exploration") or {}
        shards = 0
        for cell in (exploration.get("shards_chart") or {}).get("cells") or ():
            when = cell.get("when") or {}
            bounds = when.get("dice_total") or {}
            if total >= int(bounds.get("min") or 0) and (bounds.get("max") is None or total <= int(bounds.get("max") or 0)):
                shards = int(cell.get("shards") or 0)
                break

        matches: list[tuple[int, int, str]] = []
        counts: dict[int, int] = {}
        for value in values:
            counts[value] = counts.get(value, 0) + 1
        special = [(value, count) for value, count in counts.items() if count >= 2]
        if special:
            value, count = max(special, key=lambda item: (item[1], item[0]))
            pattern = ",".join(str(value) for _ in range(count))
            for row in exploration.get("results") or ():
                if str(row.get("dice_pattern") or "") == pattern:
                    matches.append((value, count, str(row.get("outcome") or "")))
                    break

        note = ""
        if matches:
            value, count, outcome = matches[0]
            note = f"{count} dice rolled {value}: {outcome}."
        return ExplorationResult(
            dice_count=len(values),
            dice=values,
            total=total,
            shards=shards,
            matches=tuple(matches),
            matching_dice_note=note,
        )

    # ----------------------------------------------------------- advancement

    def advance_thresholds(self, kind: str) -> tuple[int, ...]:
        """XP ladder at which Advance rolls are earned, from the KB catalogue.

        ``experience-and-advances.yaml`` declares the canonical thresholds
        ("advance_thresholds" block); the *accumulated* experience of a
        concrete warrior is campaign state and never lives in the KB.
        """
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("experience-and-advances.yaml")
        block = document.get("advance_thresholds") or {}
        values = block.get("hero" if kind == "hero" else "henchman") or ()
        return tuple(int(value) for value in values)

    def _advancement_table(self, kind: str) -> dict:
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("experience-and-advances.yaml")
        applies_to = "hero" if kind == "hero" else "henchman_group"
        for table in document.get("advancement_tables") or ():
            if table.get("applies_to") == applies_to:
                return table
        return {}

    def resolve_advancement(self, kind: str, total: int, *, is_wizard: bool = False) -> AdvancementOutcome:
        """Resolve the 2D6 advance-roll row for a hero/henchman group.

        Wizard-only options (``generate_spell``) are dropped when the subject
        is not a wizard. Rolls whose row is a ``roll_table`` return a
        non-final outcome; resolve the follow-up die with
        :meth:`resolve_advancement_subroll`.
        """
        table = self._advancement_table(kind)
        for branch in (table.get("resolution") or {}).get("branches") or ():
            when = branch.get("when") or {}
            if not (int(when.get("min") or 0) <= total <= _inf(when.get("max"))):
                continue
            result = branch.get("result") or {}
            return self._advancement_outcome(kind, total, result, is_wizard=is_wizard)
        return AdvancementOutcome(kind, total, "No advance", "No row matches the roll.", True)

    def resolve_advancement_subroll(self, kind: str, total: int, subroll: int) -> AdvancementOutcome:
        """Resolve the D6 sub-roll of a ``roll_table`` advance row."""
        table = self._advancement_table(kind)
        branches = (table.get("resolution") or {}).get("branches") or []
        for branch in branches:
            when = branch.get("when") or {}
            if not (int(when.get("min") or 0) <= total <= _inf(when.get("max"))):
                continue
            result = branch.get("result") or {}
            sub = (result.get("branches") or [])
            for sub_branch in sub:
                sub_when = sub_branch.get("when") or {}
                if int(sub_when.get("min") or 0) <= int(subroll) <= _inf(sub_when.get("max")):
                    return self._advancement_outcome(kind, total, sub_branch.get("result") or {}, is_wizard=False, subroll=subroll)
        return AdvancementOutcome(kind, total, "No advance", "No sub-row matches the roll.", True, subroll=subroll)

    def _advancement_outcome(self, kind: str, total: int, result: dict, *, is_wizard: bool, subroll: int | None = None) -> AdvancementOutcome:
        result_type = str(result.get("type") or "")
        if result_type == "characteristic_increase":
            key = CHARACTERISTIC_KEYS.get(str(result.get("characteristic") or ""), "?")
            amount = int(result.get("amount") or 1)
            return AdvancementOutcome(
                kind, total, f"Characteristic Increase · +{amount} {key}",
                f"{key} increases by {amount}.", True,
                (AdvancementOption("characteristic_increase", f"+{amount} {key}", key, amount),),
                subroll=subroll,
            )
        if result_type == "choose_one":
            labels = []
            options = []
            for option in result.get("options") or ():
                option_type = str(option.get("type") or "")
                if option_type == "characteristic_increase":
                    key = CHARACTERISTIC_KEYS.get(str(option.get("characteristic") or ""), "?")
                    amount = int(option.get("amount") or 1)
                    labels.append(f"+{amount} {key}")
                    options.append(AdvancementOption("characteristic_increase", f"+{amount} {key}", key, amount))
                elif option_type == "choose_skill":
                    labels.append("New Skill")
                    options.append(AdvancementOption("choose_skill", "New Skill"))
                elif option_type == "generate_spell":
                    if is_wizard:
                        labels.append("New Spell")
                        options.append(AdvancementOption("generate_spell", "New Spell"))
            return AdvancementOutcome(
                kind, total, "Choice", " · ".join(labels) or "No option", True,
                tuple(options), subroll=subroll,
            )
        if result_type == "roll_table":
            return AdvancementOutcome(
                kind, total, "Characteristic Increase", "Roll D6 to determine which characteristic increases.",
                False, subroll=subroll,
            )
        if result_type == "promote_henchman":
            return AdvancementOutcome(
                kind, total, "The Lad's Got Talent",
                "One member becomes a Hero and picks 2 skills from the warband's hero tables; "
                "the remaining group rerolls this advance.",
                True, (AdvancementOption("promote_henchman", "Promote a member"),),
                note="promotion", subroll=subroll,
            )
        return AdvancementOutcome(kind, total, str(result_type or "No advance"), "", True, subroll=subroll)

    # -------------------------------------------------------------- rating

    def warband_rating(self, models: int, experience: int) -> int:
        """Warband rating from the KB formula components
        (``warband-rating.yaml``: 5 per model + 1 per total experience)."""
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("warband-rating.yaml")
        total = 0
        for component in (document.get("formula") or {}).get("components") or ():
            if str(component.get("applies_to") or "") != "warrior":
                continue
            operation = str(component.get("operation") or "")
            value = int(component.get("value") or 0)
            if operation == "add_per_model":
                total += value * models
            elif operation == "add_experience":
                total += value * experience
        return total

    def racial_maximums(self) -> dict[str, dict[str, int]]:
        """Racial characteristic caps keyed by race then display key, from
        ``catalog/rules/racial-maximums.yaml`` (``campaign.limit.racial-maximum.*``)."""
        result: dict[str, dict[str, int]] = {}
        for row in self.port.racial_maximums():
            race = str(row.get("profile") or "")
            result[race] = {
                CHARACTERISTIC_KEYS.get(str(key), str(key)): int(value)
                for key, value in (row.get("characteristics") or {}).items()
            }
        return result

    # ------------------------------------------------------------- trading

    def wyrdstone_sale_value(self, fragments: int, warband_size: int) -> int:
        """Profit in gc of selling wyrdstone shards, from the KB sale table.

        The table is keyed by (fragments sold, current warband size); the
        most specific matching cell wins. Returns 0 when no cell matches.
        """
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("exploration-and-income.yaml")
        table = (document.get("income") or {}).get("wyrdstone_sale") or {}
        profit = 0
        for cell in table.get("cells") or ():
            when = cell.get("when") or {}
            fragments_when = when.get("fragments_sold") or {}
            size_when = when.get("warband_size") or {}
            if not (int(fragments_when.get("min") or 0) <= fragments <= _inf(fragments_when.get("max"))):
                continue
            if not (int(size_when.get("min") or 0) <= warband_size <= _inf(size_when.get("max"))):
                continue
            profit = max(profit, int(cell.get("profit_gc") or 0))
        return profit

    def resolve_rarity_search(self, item_id: str, roll_total: int, *, modifiers: int = 0) -> RaritySearch:
        """2D6 rarity test for a requested Trading Post item.

        Common items are always available and never require the test; items
        without a sellable Trading Post row cannot be searched for here.
        """
        catalog = self.port.campaign_catalog()
        trading = catalog.catalogue("trading-post.yaml")
        rarity: int | None = None
        for entry in trading.get("items") or ():
            if str(entry.get("item_id") or "") != item_id:
                continue
            availability = entry.get("availability") or {}
            if availability.get("kind") == "common":
                return RaritySearch(item_id, None, roll_total, modifiers, True,
                                    "Common item: always available, no rarity test required.")
            if availability.get("kind") == "rare":
                rarity = availability.get("rarity")
                break
        if rarity is None:
            return RaritySearch(item_id, None, roll_total, modifiers, False,
                                "No Trading Post availability declared for this item.")
        target = int(rarity) - int(modifiers)
        success = int(roll_total) >= target
        modifier_text = f" (modifiers {modifiers:+d})" if modifiers else ""
        note = (f"Rarity {rarity}: a 2D6 roll of {roll_total}{modifier_text} "
                + ("finds the item." if success else "does not find the item."))
        return RaritySearch(item_id, rarity, roll_total, modifiers, success, note)
