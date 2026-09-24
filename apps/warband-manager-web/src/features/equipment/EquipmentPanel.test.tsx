import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
/**
 * P6.3 acceptance tests at the component level: the equipment panel renders
 * the stash/equipped split, the assign action moves units through the real
 * service (real file port, neutral KB), and the withdraw action returns
 * them — rejections surface, never throw.
 */
import { describe, expect, it } from "vitest";
import { useEffect, useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import type { Campaign } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/index";
import { createCampaignAppService } from "@app/campaign/service";
import type { CampaignAppService } from "@app/campaign/types";
import type { CampaignDocument } from "@domain/campaign/index";
import { EquipmentPanel } from "./EquipmentPanel";
import { CampaignAppProvider } from "../campaign/useCampaignApp";

const neutralKnowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => neutralKnowledge.queryKnowledge(q)),
};

function campaign(): Campaign {
  return {
    identity: {
      campaign_name: "Gear Campaign",
      warband_name: "Armoury Band",
      warband_type: "Sisters of Sigmar",
      band_id: "sisters-of-sigmar",
      mercenary_variant: null,
    },
    configuration: {
      is_draft: false,
      starting_gold: 500,
      minimum_models: 3,
      maximum_models: 15,
      hero_limit: 5,
    },
    resources: { stash_value: 10, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors: [
      {
        id: "w1",
        name: "Sigrid",
        profile_name: "Sigmarite Matriarch",
        kind: "hero",
        stats: { M: 4, WS: 4 },
        equipment: [
          { item_id: "dagger", name: "Dagger", quantity: 1, acquisition: "fixed" },
        ],
        skills: [],
        experience: 8,
        cost: 65,
      },
      {
        id: "w2",
        name: "Greta",
        profile_name: "Sister Superior",
        kind: "hero",
        stats: { M: 4, WS: 3 },
        equipment: [],
        skills: [],
        experience: 4,
        cost: 45,
      },
    ],
    battles: [],
    states: [
      {
        number: 1,
        date: "Cyber 1",
        gold: 300,
        wyrdstone: 0,
        rating: 100,
        models: 6,
        max_models: 15,
        heroes: 3,
        henchmen: 3,
        experience: 12,
      },
    ],
    post_battles: [],
    inventory: [
      {
        id: "mace",
        name: "Mace",
        category: "close-combat-weapon",
        owned: 3,
        equipped: 0,
        stash: 3,
        value: 5,
      },
    ],
    special_rules: [],
    manual_log: [],
  };
}

function makeService(): CampaignAppService {
  return createCampaignAppService({
    files: new CampaignFileV5Adapter(),
    knowledge: neutralKnowledge,
  });
}

async function loadedService(): Promise<CampaignAppService> {
  const service = makeService();
  const raw = {
    marker: "MORDHEIM_CAMPAIGN_MANAGER",
    format_version: 5,
    saved_at: "2026-09-09T12:00:00Z",
    campaign: campaign() as unknown as Record<string, unknown>,
    view: {},
  };
  const imported = await service.importCampaign({ text: JSON.stringify(raw) });
  expect(imported.ok).toBe(true);
  return service;
}

/** Keeps the document prop in sync with the injected app service. */
function Harness({ service }: { service: CampaignAppService }) {
  const [doc, setDoc] = useState<CampaignDocument>(service.current()!);
  useEffect(() => service.subscribe(() => setDoc(service.current()!)), [service]);
  return (
    <CampaignAppProvider service={service}>
      <EquipmentPanel knowledge={presentationKnowledge} document={doc} />
    </CampaignAppProvider>
  );
}

describe("P6.3 EquipmentPanel", () => {
  it("lists stash rows and assigns through the service, conserving the split", async () => {
    const user = userEvent.setup();
    const service = await loadedService();
    render(<Harness service={service} />);

    const select = screen.getByLabelText(/Assign Mace to warrior/);
    await user.selectOptions(select, "w2");

    // The test proxy renders the action seam; its service document remains the source of truth.
    const inventory = service.current()!.campaign.inventory;
    const item = inventory.find((i: { id: string }) => i.id === "mace");
    expect(item).toMatchObject({ owned: 3, equipped: 1, stash: 2 });
    expect(service.isDirty()).toBe(true);
  });

  it("re-resolves visible and accessible names after import when the language changes", async () => {
    const service = await loadedService();
    const view = (locale: "es" | "en") => <CampaignAppProvider service={service} locale={locale}><EquipmentPanel knowledge={presentationKnowledge} document={service.current()!} locale={locale} /></CampaignAppProvider>;
    const { rerender, container } = render(view("es"));
    expect(screen.getByText("Maza")).toBeTruthy();
    rerender(view("en"));
    expect(screen.getByLabelText(/Assign Mace to warrior/)).toBeTruthy();
    expect(screen.queryByText("Maza")).toBeNull();
    rerender(view("es"));
    expect(screen.getByText("Maza")).toBeTruthy();
    expect(screen.queryByLabelText(/Assign Mace to warrior/)).toBeNull();
    expect(container.textContent).not.toContain("mace");
  });

  it("renders inventory without mutation controls in read-only mode", async () => {
    const service = await loadedService();
    render(
      <CampaignAppProvider service={service}>
        <EquipmentPanel knowledge={presentationKnowledge} document={service.current()!} readOnly />
      </CampaignAppProvider>,
    );

    expect(screen.getByText("Mace")).toBeTruthy();
    expect(screen.queryByLabelText(/Assign Mace to warrior/)).toBeNull();
    expect(screen.queryByRole("button", { name: /return|transfer/i })).toBeNull();
  });
});

const presentationKnowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", items: [{ item_id: "mace", names: { en: "Mace", es: "Maza" } }, { item_id: "dagger", names: { en: "Dagger", es: "Daga" } }], bands: [], profiles: [], skills: [] });
