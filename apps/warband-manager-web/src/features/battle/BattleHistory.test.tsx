import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { BattleHistory } from "./BattleHistory";
import type { CampaignDocument } from "../campaign/types";

const battle = {
  number: 1, scenario: "Skirmish", date: "01 Aug 2026", opponent: "Cultists", result: "Victory",
  rating_before: 90, models_before: 6, models_after: 7, rating_after: 105, casualties: 1,
  xp_delta: 3, gold_delta: 35, wyrdstone: 1, advances: 0,
  participants: [{ id: "w1", name: "Sigrid", quantity: 1 }, { id: "w3", name: "Otto", quantity: 1 }],
  absentees: [{ id: "w2", name: "Greta", reason: "Injured", remaining_before: 2 }], out_of_action_ids: ["w1"],
  xp_awards: { w1: 3, w3: 1 }, per_group_casualties: { w1: 1 },
  scenario_results: { enemy_out_of_action_by_warrior: { w3: 2 }, objectives: { first: { recipient: "w1", amount: 2 } }, additional_rewards: [{ kind: "exploration", quantity: 1 }] },
} as unknown as CampaignDocument["campaign"]["battles"][number];

describe("BattleHistory", () => {
  it("tells the battle story with its outcome, casualties and highlights", () => {
    render(<BattleHistory battle={battle} locale="en" />);
    expect(screen.getByRole("heading", { name: "Victory against Cultists" })).toBeInTheDocument();
    expect(screen.getByText(/Otto put 2 enemy model/)).toBeInTheDocument();
    expect(screen.getByText(/Sigrid received \+2 XP/)).toBeInTheDocument();
    expect(screen.getByText("An additional exploration benefit was earned.")).toBeInTheDocument();
    expect(screen.getByText("+3 EXP")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "PARTICIPANTS" }));
    expect(screen.getByText("Sigrid").parentElement).toHaveTextContent("1 Out of Action");
    expect(screen.getByText("Greta").parentElement).toHaveTextContent("Did not participate");
    expect(screen.getByText("Greta").parentElement).toHaveTextContent("2 game(s) remaining before this battle");
  });

  it("does not invent casualties or highlights when none were recorded", () => {
    render(<BattleHistory battle={{ ...battle, casualties: 0, out_of_action_ids: [], per_group_casualties: {}, scenario_results: {} }} locale="en" />);
    expect(screen.getByRole("heading", { name: "The warband emerged intact" })).toBeInTheDocument();
    expect(screen.getByText("No special objectives or rewards were recorded.")).toBeInTheDocument();
  });
});
