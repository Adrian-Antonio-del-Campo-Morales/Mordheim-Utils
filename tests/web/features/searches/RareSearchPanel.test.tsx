import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { RareSearchPanel } from "@src/features/searches/RareSearchPanel";

const document = { campaign: { warriors: [{ id: "h1", name: "Hero", kind: "hero" }], post_battles: [{ complete: false, step_state: {}, searches: {} }] } } as unknown as CampaignDocument;
const knowledge = { campaignSection: () => ({ items: [], dramatis_personae: [] }), campaignRows: () => [], itemName: (id: string) => id } as never;
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run: vi.fn() } as never;

describe("RareSearchPanel", () => {
  it("resolves saved search labels again in each locale and hides damaged references", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [],
      items: [{ item_id: "internal_rare", names: { es: "Espada especial", en: "Special sword" } }],
      campaign: { "trading-post": { items: [
        { item_id: "internal_rare", availability: { kind: "rare", rarity: 8 }, price: { base_gc: 30 } },
        { item_id: "internal_broken", availability: { kind: "rare", rarity: 9 }, price: { base_gc: 40 } },
      ] } },
    });
    const saved = { ...document, campaign: { ...document.campaign, identity: { band_id: "test" }, post_battles: [{ complete: false, step_state: { veterans: { resolved: true } }, searches: { h1: { kind: "rare", target_id: "rare:internal_rare", item_id: "internal_rare", label: "STALE_ENGLISH", dice: [6, 6], success: true, used: false } } }] } } as unknown as CampaignDocument;
    const view = (locale: "es" | "en") => <CampaignAppProvider service={service} locale={locale}><RareSearchPanel document={saved} knowledge={reader} locale={locale} /></CampaignAppProvider>;
    const { rerender, container } = render(view("es"));
    expect(screen.getByRole("option", { name: /Espada especial/ })).toBeTruthy();
    expect(screen.getByRole("option", { name: /Información no disponible/ })).toBeTruthy();
    rerender(view("en"));
    expect(screen.getByRole("option", { name: /Special sword/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /30 gc/ })).toBeTruthy();
    rerender(view("es"));
    expect(screen.getByRole("option", { name: /Espada especial/ })).toBeTruthy();
    expect(container.textContent).not.toMatch(/internal_|STALE_ENGLISH|Special sword/);
  });

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
