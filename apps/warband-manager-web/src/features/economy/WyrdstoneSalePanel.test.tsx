import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { WyrdstoneSalePanel } from "./WyrdstoneSalePanel";

const base = { campaign: { current_state_number: 1, states: [{ number: 1, models: 6, wyrdstone: 2 }], warriors: [{ id: "h1", name: "Hero", kind: "hero", quantity: 1 }], battles: [], inventory: [], special_rules: [], post_battles: [{ complete: false, sale_resolved: false, step_state: {} }] } } as unknown as CampaignDocument;
const knowledge = { campaignSection: () => ({ sale_table: [] }) } as never;
const run = vi.fn().mockResolvedValue({ ok: true });
const service = { current: () => base, isDirty: () => false, subscribe: () => () => {}, run } as never;

describe("WyrdstoneSalePanel", () => {
  it("blocks sale until exploration is complete", () => {
    render(<CampaignAppProvider service={service}><WyrdstoneSalePanel document={base} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("Complete exploration and its special result first.");
  });

  it("dispatches the one-time sale after exploration", async () => {
    const user = userEvent.setup();
    const ready = {
      ...base,
      campaign: {
        ...base.campaign,
        post_battles: [{ ...base.campaign.post_battles[0], step_state: { exploration: { resolved: true } } }],
      },
    } as CampaignDocument;
    render(<CampaignAppProvider service={service}><WyrdstoneSalePanel document={ready} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    const input = screen.getByLabelText("Shards to sell");
    await user.clear(input);
    await user.type(input, "1");
    await user.click(screen.getByRole("button", { name: "Confirm sale once" }));
    expect(run).toHaveBeenCalledWith("sellWyrdstone", { quantity: 1 });
  });
});
