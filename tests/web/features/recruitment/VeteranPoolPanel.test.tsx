import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { VeteranPoolPanel } from "@src/features/recruitment/VeteranPoolPanel";

const base = { campaign: { post_battles: [{ complete: false, sale_resolved: false, veteran_pool: 7, step_state: {} }] } } as unknown as CampaignDocument;
const service = { current: () => base, isDirty: () => false, subscribe: () => () => {}, run: vi.fn() } as never;

describe("VeteranPoolPanel", () => {
  it("requires wyrdstone sale before rolling veterans", () => {
    render(<CampaignAppProvider service={service}><VeteranPoolPanel document={base} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("Resolve wyrdstone sale first.");
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows the resolved shared veteran pool", () => {
    const resolved = structuredClone(base) as CampaignDocument;
    const post = resolved.campaign.post_battles[0] as unknown as { sale_resolved: boolean; step_state: Record<string, unknown> };
    post.sale_resolved = true;
    post.step_state = { veterans: { resolved: true } };
    render(<CampaignAppProvider service={service}><VeteranPoolPanel document={resolved} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("7 XP");
    expect(screen.getByText(/Shared across later veteran hires/)).toBeInTheDocument();
  });
});
