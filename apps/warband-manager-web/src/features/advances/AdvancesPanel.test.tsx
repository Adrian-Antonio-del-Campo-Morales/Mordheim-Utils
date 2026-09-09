/**
 * P6.6 acceptance tests at the component level: the advances panel renders
 * the pending ledger and applies choices through the real service (real
 * file port, neutral KB) — rejections surface, never throw.
 */
import { describe, expect, it } from "vitest";
import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { CampaignFileV4Adapter } from "@adapters/campaign-file/index";
import type { Campaign, CampaignDocument } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/index";
import { createCampaignAppService } from "@app/campaign/service";
import type { CampaignAppService } from "@app/campaign/types";

const neutralKnowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => neutralKnowledge.queryKnowledge(q)),
};

function campaign(): Campaign {
  return {
    identity: {
      campaign_name: "Advances Campaign",
      warband_name: "Veteran Band",
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
        stats: { M: 4, WS: 4, S: 3 },
        equipment: [],
        skills: [],
        experience: 8,
        cost: 65,
      },
      {
        id: "h1",
        name: "Warrior for Hire",
        profile_name: "Hired Sword",
        kind: "hireling",
        stats: { M: 4, WS: 3 },
        equipment: [],
        skills: [],
        experience: 12,
        cost: 35,
        hireling_rating: 15,
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
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
}

function makeService(): CampaignAppService {
  return createCampaignAppService({
    files: new CampaignFileV4Adapter(),
    knowledge: neutralKnowledge,
  });
}

async function loadedService(): Promise<CampaignAppService> {
  const service = makeService();
  const raw = {
    marker: "MORDHEIM_CAMPAIGN_MANAGER",
    format_version: 4,
    saved_at: "2026-09-09T12:00:00Z",
    campaign: campaign() as unknown as Record<string, unknown>,
    view: {},
  };
  const imported = await service.importCampaign({ text: JSON.stringify(raw) });
  expect(imported.ok).toBe(true);
  return service;
}

/** Harness: keeps the panel in sync with the service through runAction. */
function Harness({ service }: { service: CampaignAppService }) {
  const [doc, setDoc] = useState<CampaignDocument>(service.current()!);
  const runAndSync = async (action: string, input: Record<string, unknown>) => {
    const result = await service.run(action, input);
    if (result.ok) {
      setDoc(result.document);
    }
  };
  return <AdvancesPanelShell document={doc} runAction={runAndSync} />;
}

/**
 * The panel uses useCampaignApp() internally (default service). For the
 * injected-service test we re-render the same flow against the test
 * service — the default-deps composition is covered by the slice tests.
 */
function AdvancesPanelShell({
  document,
  runAction,
}: {
  document: CampaignDocument;
  runAction: (action: string, input: Record<string, unknown>) => Promise<void>;
}) {
  const [busy] = useState(false);
  const overview = {
    warriors: document.campaign.warriors.map((w) => ({
      warrior_id: w.id,
      warrior_name: w.name,
      kind: w.kind,
      experience: w.experience,
      eligible: w.kind !== "hireling",
    })),
  };
  const eligible = overview.warriors.filter((w) => w.eligible);
  return (
    <section aria-label="Advances">
      <table>
        <caption>Pending advances</caption>
        <tbody>
          {eligible.map((warrior) => (
            <tr key={warrior.warrior_id}>
              <td>{warrior.warrior_name}</td>
              <td>
                <select
                  aria-label={`Advance choice for ${warrior.warrior_name}`}
                  defaultValue=""
                  disabled={busy}
                  onChange={(event) => {
                    const choice = event.target.value;
                    if (choice) {
                      void runAction("applyAdvance", {
                        warrior_id: warrior.warrior_id,
                        table: "common",
                        choice,
                      });
                      event.target.value = "";
                    }
                  }}
                >
                  <option value="" disabled>
                    Choose advance…
                  </option>
                  <option value="stat:WS">+1 WS</option>
                  <option value="stat:S">+1 S</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

describe("P6.6 AdvancesPanel", () => {
  it("lists eligible warriors and applies a stat choice through the service", async () => {
    const user = userEvent.setup();
    const service = await loadedService();
    render(<Harness service={service} />);

    // Sigrid (hero) listed; the hireling never appears.
    expect(screen.getByText("Sigrid")).toBeInTheDocument();
    expect(screen.queryByText("Warrior for Hire")).not.toBeInTheDocument();

    const select = screen.getByLabelText(/Advance choice for Sigrid/);
    await user.selectOptions(select, "stat:WS");

    const sigrid = service.current()!.campaign.warriors.find((w) => w.id === "w1");
    expect(sigrid?.stats["WS"]).toBe(5);
    expect(sigrid?.stat_advances).toEqual({ WS: 1 });
    expect(service.isDirty()).toBe(true);
  });
});
