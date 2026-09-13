import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { HirelingUpkeepPanel } from "./HirelingUpkeepPanel";

const document = { campaign: { warriors: [{ id: "hs", name: "Hunter" }], post_battles: [{ complete: false, pending_follow_ups: [{ id: "upkeep:1", type: "hireling_upkeep", warrior_id: "hs", costs: [["gold_crowns", 15]] }] }] } } as unknown as CampaignDocument;
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run: vi.fn().mockResolvedValue({ ok: true }) } as never;

describe("HirelingUpkeepPanel", () => {
  it("shows the cost and dispatches payment", async () => {
    const user = userEvent.setup();
    render(<CampaignAppProvider service={service}><HirelingUpkeepPanel document={document} locale="en" /></CampaignAppProvider>);
    expect(screen.getByText("15 Gold Crowns")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Pay" }));
    expect((service as unknown as { run: ReturnType<typeof vi.fn> }).run).toHaveBeenCalledWith("resolveHirelingUpkeep", { follow_up_id: "upkeep:1", pay: true });
  });

  it("sorts upkeep entries alphabetically", () => {
    const sortedDocument = { campaign: { warriors: [{ id: "z", name: "Zelote" }, { id: "a", name: "Águila" }], post_battles: [{ complete: false, pending_follow_ups: [{ id: "upkeep:z", type: "hireling_upkeep", warrior_id: "z", costs: [] }, { id: "upkeep:a", type: "hireling_upkeep", warrior_id: "a", costs: [] }] }] } } as unknown as CampaignDocument;
    render(<CampaignAppProvider service={service}><HirelingUpkeepPanel document={sortedDocument} locale="es" /></CampaignAppProvider>);
    expect(screen.getAllByRole("article").map((row) => row.querySelector("strong")?.textContent)).toEqual(["Águila", "Zelote"]);
  });
});
