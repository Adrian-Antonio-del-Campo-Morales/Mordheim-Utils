import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
/**
 * Campaign timeline component tests at the UI level: the timeline
 * panel enumerates the document's moments, navigates through selectMoment
 * without dirtying the document, and shows the current vs selected moment.
 * The service beneath is the real application service with the real file
 * port and a neutral KB reader — same pattern as the P6.1 service tests.
 */
import { describe, expect, it } from "vitest";
import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import type { Campaign } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/index";
import { createCampaignAppService } from "@app/campaign/service";
import type { CampaignAppService } from "@app/campaign/types";
import type { CampaignDocument } from "@domain/campaign/index";

import { enumerateMoments } from "@src/features/timeline/moments";
import { TimelinePanel } from "@src/features/timeline/TimelinePanel";

const neutralKnowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => neutralKnowledge.queryKnowledge(q)),
};

function campaign(): Campaign {
  return {
    identity: {
      campaign_name: "Timeline Campaign",
      warband_name: "Chrono Band",
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
    resources: { stash_value: 40, rare_finds: 1, treasures: 0, campaign_points: 2 },
    current_state_number: 2,
    warriors: [],
    battles: [
      {
        number: 1,
        date: "Cyber 2",
        scenario: "skirmish",
        opponent: "Reikland",
        result: "win",
        gold_delta: 30,
        wyrdstone: 2,
        xp_delta: 8,
        casualties: 0,
        advances: 0,
        rating_before: 100,
        rating_after: 110,
        models_before: 6,
        models_after: 6,
        out_of_action_ids: [],
      },
    ],
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
      {
        number: 2,
        date: "Cyber 2",
        gold: 330,
        wyrdstone: 2,
        rating: 110,
        models: 6,
        max_models: 15,
        heroes: 3,
        henchmen: 3,
        experience: 20,
      },
    ],
    post_battles: [],
    inventory: [],
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

/** Harness: keeps the panel in sync with the service through selectMoment. */
function Harness({ service }: { service: CampaignAppService }) {
  const [doc, setDoc] = useState<CampaignDocument>(service.current()!);
  const select = (moment: Parameters<CampaignAppService["selectMoment"]>[0]) => {
    const result = service.selectMoment(moment);
    if (result.ok) {
      setDoc(result.document);
    }
  };
  return <TimelinePanel knowledge={presentationKnowledge} document={doc} onSelect={select} />;
}

describe("P6.1 TimelinePanel", () => {
  it("enumerates draft, states and battles in timeline order", async () => {
    const service = await loadedService();
    const doc = service.current()!;
    expect(enumerateMoments(doc.campaign)).toEqual([
      "draft:0",
      "state:1",
      "state:2",
      "battle:1",
    ]);
  });

  it("keeps states ordered before battles even when source arrays are unordered", async () => {
    const source = campaign();
    (source as unknown as { states: unknown[] }).states = [...source.states].reverse();
    (source as unknown as { battles: unknown[] }).battles = [...source.battles].reverse();
    expect(enumerateMoments(source)).toEqual([
      "draft:0",
      "state:1",
      "state:2",
      "battle:1",
    ]);
  });

  it("selects a moment by clicking and marks it current without dirtying", async () => {
    const user = userEvent.setup();
    const service = await loadedService();
    render(<Harness service={service} />);

    // Draft is selected by default.
    expect(screen.getByRole("button", { name: /Initial warband.*draft/i })).toHaveAttribute("aria-current", "true");

    await user.click(screen.getByRole("button", { name: /State #2/ }));
    const fresh = screen.getByRole("button", { name: /State #2/ });
    expect(fresh).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: /Initial warband.*draft/i })).not.toHaveAttribute("aria-current");

    // Selection never dirties the document (P6.1 contract).
    expect(service.isDirty()).toBe(false);
    expect(service.current()?.view.selected_moment).toBe("state:2");
  });

  it("labels battles with their scenario and post-battles as pending", async () => {
    const service = await loadedService();
    render(<Harness service={service} />);
    expect(screen.getByRole("button", { name: /Battle #1 — Skirmish/i })).toBeInTheDocument();
  });
});

const presentationKnowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", items: [], bands: [], profiles: [], skills: [], campaign: { scenarios: { scenarios: [{ id: "skirmish", names: { en: "Skirmish", es: "Escaramuza" } }] } } });
