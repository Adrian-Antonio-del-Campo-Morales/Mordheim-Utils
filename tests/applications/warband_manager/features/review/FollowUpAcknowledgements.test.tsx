import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { FollowUpAcknowledgements } from "@src/features/review/FollowUpAcknowledgements";

const document = { campaign: { post_battles: [{ complete: false, pending_follow_ups: [{ id: "table-1", type: "custom", description: "Choose the scenario reward" }], acknowledgements: {} }] } } as unknown as CampaignDocument;

describe("FollowUpAcknowledgements", () => {
  it("renders unresolved table-side work and acknowledges it", async () => {
    const runAction = vi.fn().mockResolvedValue({ ok: true });
    const service = { run: runAction, current: () => document, isDirty: () => false, subscribe: () => () => {} } as never;
    render(<CampaignAppProvider service={service}><FollowUpAcknowledgements document={document} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("heading", { name: "Table-side follow-ups" })).toBeInTheDocument();
    expect(screen.getByText("Information unavailable")).toBeInTheDocument();
    expect(screen.queryByText("Choose the scenario reward")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Resolved at table" }));
    expect(runAction).toHaveBeenCalledWith("acknowledgeFollowUp", { follow_up_id: "table-1" });
  });

  it("does not render handled follow-up types", () => {
    const handled = structuredClone(document) as CampaignDocument;
    (handled.campaign.post_battles[0] as unknown as { pending_follow_ups: unknown[] }).pending_follow_ups = [{ id: "injury", type: "injury_roll", description: "Hidden" }];
    const service = { run: vi.fn(), current: () => handled, isDirty: () => false, subscribe: () => () => {} } as never;
    render(<CampaignAppProvider service={service}><FollowUpAcknowledgements document={handled} /></CampaignAppProvider>);
    expect(screen.queryByRole("heading", { name: "Table-side follow-ups" })).not.toBeInTheDocument();
  });
});
