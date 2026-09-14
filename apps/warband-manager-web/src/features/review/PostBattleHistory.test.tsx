import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { PostBattleHistory } from "./PostBattleHistory";
import type { CampaignDocument } from "../campaign/types";

const document = { campaign: { post_battles: [{ battle_number: 2, complete: true, active_step: 8, completed_steps: [0,1,2,3,4,5,6,7], review_open: false, gold_delta: 19, wyrdstone_delta: -2, wyrdstone_sold: 3, veteran_pool: 7, event_log: [{ step: 0, type: "injury_decision", description: "Sigrid made a full recovery." }, { step: 2, type: "exploration", description: "Found 4 wyrdstone shards." }, { step: 7, type: "buy_item", description: "Bought a sword for 10 gc." }] }] } } as unknown as CampaignDocument;

describe("PostBattleHistory", () => {
  it("presents the sequence as a chronological account with its final balance", () => {
    render(<PostBattleHistory document={document} battleNumber={2} locale="en" />);
    expect(screen.getByRole("heading", { name: "Sequence complete" })).toBeInTheDocument();
    expect(screen.getByText("+19 gc")).toBeInTheDocument();
    expect(screen.getByText("-2")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Injuries and recovery" })).toBeInTheDocument();
    expect(screen.getByText("Sigrid made a full recovery.")).toBeInTheDocument();
    expect(screen.getByText("Found 4 wyrdstone shards.")).toBeInTheDocument();
    expect(screen.getByText("Bought a sword for 10 gc.")).toBeInTheDocument();
  });

  it("states when a completed sequence has no detailed events", () => {
    const quiet = { ...document, campaign: { ...document.campaign, post_battles: [{ ...document.campaign.post_battles[0], event_log: [] }] } } as unknown as CampaignDocument;
    render(<PostBattleHistory document={quiet} battleNumber={2} locale="en" />);
    expect(screen.getByText("The sequence ended with no additional events recorded.")).toBeInTheDocument();
  });
});
