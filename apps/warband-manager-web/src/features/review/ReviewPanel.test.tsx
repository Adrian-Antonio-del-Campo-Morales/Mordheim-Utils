/**
 * P6.8 component tests: the review panel renders the pre-export summary,
 * surfaces pending work through the status seam, and triggers the auxiliary
 * text downloads — pure projections of the document.
 */
import { describe, expect, it, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { ReviewPanel } from "./ReviewPanel";

const document = {
  campaign: {
    identity: {
      campaign_name: "Review Campaign",
      warband_name: "Ledger Band",
      warband_type: "Witch Hunters",
      band_id: "witch_hunters",
      mercenary_variant: null,
    },
    configuration: {
      is_draft: false,
      starting_gold: 500,
      minimum_models: 3,
      maximum_models: 15,
      hero_limit: 4,
    },
    resources: { stash_value: 30, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 2,
    warriors: [
      {
        id: "w1",
        name: "Sigrid",
        profile_name: "Captain",
        kind: "hero",
        stats: { M: 4, WS: 4 },
        equipment: [],
        skills: [],
        experience: 5,
        cost: 35,
        manual_log: [],
      },
    ],
    battles: [
      {
        number: 1,
        date: "01 Aug 2026",
        scenario: "Skirmish",
        opponent: "Cultists",
        result: "Victory",
        gold_delta: 35,
        wyrdstone: 1,
        xp_delta: 3,
        casualties: 0,
        advances: 0,
        rating_before: 90,
        rating_after: 105,
        models_before: 6,
        models_after: 7,
        out_of_action_ids: null,
      },
    ],
    states: [
      {
        number: 2,
        date: "08 Aug 2026",
        gold: 240,
        wyrdstone: 2,
        rating: 115,
        models: 6,
        max_models: 15,
        heroes: 2,
        henchmen: 4,
        experience: 13,
      },
    ],
    post_battles: [],
    inventory: [
      { id: "mace", name: "Mace", category: "ccw", owned: 2, equipped: 1, stash: 1, value: 5 },
    ],
    special_rules: [],
    manual_log: [{ message: "Warband re-equipped before the storm.", date: "02 Aug 2026" }],
  },
  view: {},
} as unknown as CampaignDocument;

const idleService = { current: () => null, isDirty: () => false, subscribe: () => () => {}, run: async () => ({ ok: true }) } as never;
function renderReview(props: React.ComponentProps<typeof ReviewPanel>) {
  return render(<CampaignAppProvider service={idleService}><ReviewPanel {...props} /></CampaignAppProvider>);
}

describe("ReviewPanel", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders the pre-export summary with treasury and roll-ups", () => {
    renderReview({ document });
    expect(screen.getByRole("heading", { name: "Review before export" })).toBeInTheDocument();
    expect(screen.getByText(/Ledger Band \(Witch Hunters\)/)).toBeInTheDocument();
    expect(screen.getByText(/240 gc, 2 shard/)).toBeInTheDocument();
    expect(screen.getByText(/1 battle\(s\), state 2 of 1/)).toBeInTheDocument();
  });

  it("does not report the closing confirmation as unfinished work", () => {
    const pending = structuredClone(document) as CampaignDocument;
    (pending.campaign as unknown as { post_battles: unknown[] }).post_battles = [{ complete: false, pending_follow_ups: [] }];
    renderReview({ document: pending });
    expect(screen.getByRole("status")).toHaveTextContent("Nothing pending — safe to save.");
    expect(screen.getByRole("button", { name: /Confirm next state/ })).toBeInTheDocument();
  });

  it("names generic follow-ups correctly and returns to their post-battle step", () => {
    const pending = structuredClone(document) as CampaignDocument;
    (pending.campaign as unknown as { post_battles: unknown[] }).post_battles = [{
      complete: false,
      pending_follow_ups: [{ id: "upkeep:1:ranger", type: "hireling_upkeep", step: 6, warrior_id: "ranger" }],
      acknowledgements: {},
    }];
    const onReturnToStep = vi.fn();
    renderReview({ document: pending, locale: "es", onReturnToStep });

    expect(screen.getByRole("status")).toHaveTextContent("1 seguimiento(s) sin resolver");
    expect(screen.queryByText(/tirada\(s\) de heridas/)).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Resuelve los seguimientos pendientes antes de confirmar.");
    expect(screen.getByRole("button", { name: "Confirmar siguiente estado" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Volver al paso pendiente" }));
    expect(onReturnToStep).toHaveBeenCalledWith(6);
  });

  it("surfaces pending work through the status seam", () => {
    const pending = structuredClone(document) as CampaignDocument;
    (pending.campaign.warriors[0] as { games_to_miss?: number }).games_to_miss = 2;
    renderReview({ document: pending });
    const status = screen.getByRole("status");
    expect(status).toHaveTextContent(/Pending: 1 warrior\(s\) absent/);
  });

  it("reports a clean campaign as safe to save", () => {
    renderReview({ document });
    expect(screen.getByRole("status")).toHaveTextContent("Nothing pending — safe to save.");
  });

  it("downloads auxiliary exports as blobs (no service round-trip)", () => {
    const clicks: HTMLAnchorElement[] = [];
    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    const originalCreate = window.document.createElement.bind(window.document);
    vi.spyOn(window.document, "createElement").mockImplementation(((tag: string) => {
      const el = originalCreate(tag) as HTMLAnchorElement;
      if (tag === "a") {
        clicks.push(el);
        el.click = vi.fn();
      }
      return el;
    }) as typeof window.document.createElement);

    renderReview({ document });
    fireEvent.click(screen.getByLabelText("Download roster summary for Ledger Band"));
    fireEvent.click(screen.getByLabelText("Download campaign ledger for Ledger Band"));

    expect(clicks).toHaveLength(2);
    expect(clicks[0].download).toBe("Ledger_Band-roster.txt");
    expect(clicks[1].download).toBe("Ledger_Band-ledger.txt");
    expect(clicks[1].href).toBe("blob:mock");
    expect(revokeObjectURL).toHaveBeenCalledTimes(2);
    vi.unstubAllGlobals();
  });
});
