import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { RareSearchPanel } from "./RareSearchPanel";

const document = { campaign: { warriors: [{ id: "h1", name: "Hero", kind: "hero" }], post_battles: [{ complete: false, step_state: {}, searches: {} }] } } as unknown as CampaignDocument;
const knowledge = { campaignSection: () => ({ items: [], dramatis_personae: [] }), campaignRows: () => [], itemName: (id: string) => id } as never;
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run: vi.fn() } as never;

describe("RareSearchPanel", () => {
  it("blocks searches until veterans are resolved", () => {
    render(<CampaignAppProvider service={service}><RareSearchPanel document={document} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("Resolve veteran availability first.");
  });

  it("offers the available hero when searches are unlocked", async () => {
    const unlocked = {
      ...document,
      campaign: {
        ...document.campaign,
        post_battles: [{ ...document.campaign.post_battles[0], step_state: { veterans: { resolved: true } } }],
      },
    } as CampaignDocument;
    render(<CampaignAppProvider service={service}><RareSearchPanel document={unlocked} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("heading", { name: /Rare items and Dramatis/ })).toBeInTheDocument();
    expect(screen.getByLabelText("Search target")).toBeInTheDocument();
  });
});
