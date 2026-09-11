import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { BattleHistory } from "./BattleHistory";
import type { CampaignDocument } from "../campaign/types";

const battle = {
  number: 1, scenario: "Skirmish", date: "01 Aug 2026", opponent: "Cultists", result: "Victory",
  rating_before: 90, models_before: 6, models_after: 7, rating_after: 105, casualties: 1,
  xp_delta: 3, gold_delta: 35, wyrdstone: 1, advances: 0,
  participants: [{ id: "w1", name: "Sigrid", quantity: 1 }],
  absentees: [{ id: "w2", name: "Greta", reason: "Injured" }], out_of_action_ids: ["w1"],
  scenario_results: { objectives: { first: { recipient: "w1", amount: 2 } }, additional_rewards: [{ kind: "exploration", quantity: 1 }] },
} as unknown as CampaignDocument["campaign"]["battles"][number];

describe("BattleHistory", () => {
  it("shows participants, absentees and scenario consequences", () => {
    render(<BattleHistory battle={battle} locale="en" />);
    expect(screen.getByText(/Sigrid.*Out of Action/)).toBeInTheDocument();
    expect(screen.getByText(/Greta.*Did not participate/)).toBeInTheDocument();
    expect(screen.getByText(/Sigrid received \+2 XP/)).toBeInTheDocument();
    expect(screen.getByText("Scenario exploration rule applied.")).toBeInTheDocument();
  });
});
