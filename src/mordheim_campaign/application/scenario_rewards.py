"""application.scenario_rewards: structured per-warrior experience awards.

Builds the award plan of a KB scenario from ``scenarios.yaml`` ``progression``
blocks and the canonical awards of ``experience-and-advances.yaml``, then
computes the per-warrior XP totals from the recorded battle facts (result,
surviving roster and enemy Out-of-Action count). Rows that are only prose in
the KB stay ``manual``: the player assigns them by hand in the battle dialog.
"""
from __future__ import annotations

from dataclasses import dataclass

from mordheim_campaign.application.knowledge_port import KnowledgePort


@dataclass(frozen=True, slots=True)
class AwardRow:
    award_id: str
    label: str
    recipient: str  # hero_and_henchman_group | leader | hero | manual
    trigger: str
    amount: int
    amount_dice: str | None
    manual: bool


class ScenarioRewards:
    """Read-only award planner over the campaign catalogue."""

    def __init__(self, port: KnowledgePort) -> None:
        self.port = port

    # ------------------------------------------------------------------ plan

    def _awards(self) -> dict[str, dict]:
        catalog = self.port.campaign_catalog()
        document = catalog.catalogue("experience-and-advances.yaml")
        return {str(row.get("id") or ""): dict(row) for row in document.get("awards") or ()}

    def plan(self, scenario_id: str) -> tuple[AwardRow, ...]:
        """The ordered award rows of one scenario."""
        catalog = self.port.campaign_catalog()
        scenarios = catalog.catalogue("scenarios.yaml")
        scenario = next(
            (row for row in scenarios.get("scenarios") or () if str(row.get("id") or "") == scenario_id),
            None,
        )
        awards = self._awards()
        rows: list[AwardRow] = []
        for entry in (scenario or {}).get("progression", {}).get("experience") or ():
            ref = entry.get("ref")
            if ref:
                award = awards.get(str(ref))
                if award is None:
                    continue
                rows.append(AwardRow(
                    award_id=str(ref),
                    label=str(award.get("id") or "").rsplit(".", 1)[-1].replace("-", " ").title(),
                    recipient=str(award.get("recipient") or "manual"),
                    trigger=str(award.get("trigger") or ""),
                    amount=int(award.get("amount") or 0),
                    amount_dice=None,
                    manual=False,
                ))
                continue
            rows.append(AwardRow(
                award_id=str(entry.get("effect") or "manual award")[:80],
                label=str(entry.get("effect") or "Manual award"),
                recipient="manual",
                trigger="declared_by_scenario",
                amount=int(entry.get("amount") or 0),
                amount_dice=str(entry.get("amount_dice")) if entry.get("amount_dice") else None,
                manual=True,
            ))
        return tuple(rows)

    # --------------------------------------------------------------- compute

    def compute(
        self,
        rows: tuple[AwardRow, ...],
        warriors,
        *,
        result: str,
        enemy_out_of_action: int = 0,
    ) -> dict[str, int]:
        """Per-warrior XP totals from the battle facts (manual rows excluded)."""
        totals: dict[str, int] = {}
        leader = next((w for w in warriors if w.kind == "hero"), None)
        for row in rows:
            if row.manual or row.amount <= 0:
                continue
            trigger = row.trigger
            if trigger == "survived_battle":
                for warrior in warriors:
                    totals[warrior.id] = totals.get(warrior.id, 0) + row.amount
            elif trigger == "warband_won_battle":
                if result == "Victory" and leader is not None:
                    totals[leader.id] = totals.get(leader.id, 0) + row.amount
            elif trigger == "enemy_put_out_of_action":
                if enemy_out_of_action > 0:
                    for warrior in warriors:
                        if warrior.kind == "hero":
                            totals[warrior.id] = totals.get(warrior.id, 0) + row.amount * enemy_out_of_action
        return totals

    def compute_for(self, scenario_id: str, warriors, *, result: str, enemy_out_of_action: int = 0) -> dict[str, int]:
        return self.compute(self.plan(scenario_id), warriors, result=result, enemy_out_of_action=enemy_out_of_action)
