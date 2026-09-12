import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "../campaign/types";
import type { CampaignAppService } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { HirelingsPanel } from "./HirelingsPanel";

const document = { campaign: { identity: { band_id: "sisters-of-sigmar" }, warriors: [], inventory: [] } } as unknown as CampaignDocument;
const listings = {
  campaignRows: (section: string) => section === "hired-swords-and-dramatis:hired_swords" ? [{ id: "offer", profile_id: "hunter", eligibility: {}, hiring_fee: { resources: { gold_crowns: { cost: 25 } } } }] : [],
  campaignSection: () => ({ profiles: [{ id: "hunter", names: { en: "Hunter" }, characteristics: {} }] }),
  itemName: (id: string) => id === "hunter" ? "Hunter" : id,
} as never;
const run = vi.fn().mockResolvedValue({ ok: true, document });
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run } as unknown as CampaignAppService;

describe("HirelingsPanel", () => {
  it("shows an empty state when no eligible offers exist", () => {
    const empty = { campaign: { identity: { band_id: "sisters-of-sigmar" }, warriors: [], inventory: [] } } as unknown as CampaignDocument;
    const reader = { campaignRows: () => [], campaignSection: () => ({}) } as never;
    render(<CampaignAppProvider service={service}><HirelingsPanel document={empty} listings={reader} mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("No hireling offers available.");
  });

  it("dispatches an eligible hire through the application seam", async () => {
    const user = userEvent.setup();
    render(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={listings} mode="hirelings" /></CampaignAppProvider>);
    await user.click(screen.getByRole("button", { name: "Hire Hunter" }));
    expect(run).toHaveBeenCalledWith("hireHireling", expect.objectContaining({ profile_id: "hunter", fee: 25 }));
    expect(screen.getByRole("status")).toHaveTextContent("Hired: Hunter");
  });

  it("shows the hired profile and disables hiring it again", () => {
    const hired = { ...document, campaign: { ...document.campaign, warriors: [{ id:"hunter#1", profile_id:"hunter", profile_name:"Hunter", name:"Hunter", kind:"hireling", cost:25, hireling_rating:15, experience:0, stats:{ M:4, WS:3 }, equipment:[], skills:[] }] } } as CampaignDocument;
    render(<CampaignAppProvider service={service}><HirelingsPanel document={hired} listings={listings} mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getByRole("button", { name: /Already hired/ })).toBeDisabled();
  });

  it("can embed buying and selling inside Equipment without a Trading Post heading", () => {
    const reader = { campaignRows: () => [], campaignSection: () => ({}), itemName: (id: string) => id } as never;
    render(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={reader} mode="trading" showTradingTitle={false} /></CampaignAppProvider>);
    expect(screen.queryByRole("heading", { name: "Trading Post" })).not.toBeInTheDocument();
    expect(screen.getByText("Goods for sale")).toBeInTheDocument();
  });
});
