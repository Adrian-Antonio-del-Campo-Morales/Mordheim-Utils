import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "@src/features/campaign/types";
import type { CampaignAppService } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { HirelingsPanel } from "@src/features/hirelings/HirelingsPanel";

const document = { campaign: { identity: { band_id: "sisters-of-sigmar" }, warriors: [], inventory: [] } } as unknown as CampaignDocument;
const listings = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], campaign: {
  "hired-swords-and-dramatis": { hired_swords: [{ id: "offer", profile_id: "hunter", eligibility: {}, hiring_fee: { resources: { gold_crowns: { cost: 25 } } } }] },
  hirelings: { profiles: [{ id: "hunter", names: { en: "Hunter", es: "Cazador" }, characteristics: {} }] },
} });
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

  it("sorts hired swords by their translated name for the active locale", () => {
    const translated = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], campaign: {
      "hired-swords-and-dramatis": { hired_swords: [
        { id: "offer-a", profile_id: "a", eligibility: {}, hiring_fee: { resources: { gold_crowns: { cost: 10 } } } },
        { id: "offer-b", profile_id: "b", eligibility: {}, hiring_fee: { resources: { gold_crowns: { cost: 10 } } } },
      ] }, hirelings: { profiles: [
        { id: "a", names: { en: "Archer", es: "Zorro" }, characteristics: {} },
        { id: "b", names: { en: "Wizard", es: "Águila" }, characteristics: {} },
      ] },
    } });
    const { rerender } = render(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={translated} locale="es" mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getAllByRole("row").slice(1).map((row) => row.querySelector("td")?.textContent)).toEqual(["Águila", "Zorro"]);

    rerender(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={translated} locale="en" mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getAllByRole("row").slice(1).map((row) => row.querySelector("td")?.textContent)).toEqual(["Archer", "Wizard"]);
  });

  it("shows hiring restrictions in the active language", () => {
    const restricted = {
      campaignRows: (section: string) => section === "hired-swords-and-dramatis:hired_swords" ? [
        { id: "restricted-offer", profile_id: "restricted", eligibility: { forbid_band_ids: ["sisters-of-sigmar"] }, hiring_fee: { resources: { gold_crowns: { cost: 10 } } } },
      ] : [],
      campaignSection: () => ({ profiles: [{ id: "restricted", names: { en: "Restricted", es: "Restringido" }, characteristics: {} }] }),
      itemName: (_id: string, locale: "es" | "en") => locale === "es" ? "Restringido" : "Restricted",
    } as never;
    const { rerender } = render(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={restricted} locale="es" mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getByRole("note")).toHaveTextContent("No disponible: La banda o su grupo están excluidos por las reglas de contratación.");
    expect(screen.getByRole("note")).not.toHaveTextContent("Not available");

    rerender(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={restricted} locale="en" mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getByRole("note")).toHaveTextContent("Not eligible: The warband or its group is excluded by the hiring rules.");
  });

  it("translates dynamic roster restrictions instead of exposing domain text", () => {
    const profileId = "hireling.hired-sword.wolf-priest-of-ulric";
    const dynamic = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [],
      campaign: {
        "hired-swords-and-dramatis": { hired_swords: [{ id: "wolf-priest-offer", profile_id: profileId, eligibility: {}, hiring_fee: { resources: { gold_crowns: { cost: 40 } } } }] },
        hirelings: { profiles: [{ id: profileId, names: { en: "Wolf Priest of Ulric", es: "Sacerdote Lobo de Ulric" }, rule_ids: [`${profileId}.rule.campaign-eligibility`], characteristics: {} }] },
      },
      presentation_entries: [
        { ref: { kind: "hireling", id: profileId }, fields: { name: { en: "Wolf Priest of Ulric", es: "Sacerdote Lobo de Ulric" } }, source: "fixture/profile" },
        { ref: { kind: "rule", id: `${profileId}.rule.campaign-eligibility`, profileId }, fields: { effect: { en: "Available only to Middenheim Mercenaries.", es: "Solo los Mercenarios de Middenheim pueden contratarlo." } }, source: "fixture/rule" },
      ],
    });
    render(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={dynamic} locale="es" mode="hirelings" /></CampaignAppProvider>);
    expect(screen.getByRole("note")).toHaveTextContent("No disponible: Solo los Mercenarios de Middenheim pueden contratarlo.");
    expect(screen.getByRole("note")).not.toHaveTextContent("available only to Middenheim");
  });

  it("can embed buying and selling inside Equipment without a Trading Post heading", () => {
    const reader = { campaignRows: () => [], campaignSection: () => ({}), itemName: (id: string) => id } as never;
    render(<CampaignAppProvider service={service}><HirelingsPanel document={document} listings={reader} mode="trading" showTradingTitle={false} /></CampaignAppProvider>);
    expect(screen.queryByRole("heading", { name: "Trading Post" })).not.toBeInTheDocument();
    expect(screen.getByText("Goods for sale")).toBeInTheDocument();
  });
});
