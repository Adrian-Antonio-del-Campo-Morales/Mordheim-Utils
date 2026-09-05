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

    def exploration_dice(self, surviving_heroes: int, warband_won: bool, *, max_dice: int = 6) -> int:
        """Dice a warband rolls: one per surviving hero (+1 when it won)."""
        count = max(0, int(surviving_heroes)) + (1 if warband_won else 0)
        return min(count, max_dice)

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

    # ------------------------------------------------------------- trading

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
