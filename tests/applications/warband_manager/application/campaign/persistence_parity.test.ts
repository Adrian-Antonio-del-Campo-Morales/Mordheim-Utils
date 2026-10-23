/** Portable parity translation of the persistence portions of test_persistence.py. */
import { describe, expect, it } from "vitest";
import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";

const adapter = new CampaignFileV5Adapter();

function campaignFromFixture(name: string) {
  // Keep the fixture source in the adapter tests; this file exercises the
  // application-facing contract without duplicating filesystem fixture IO.
  const samples: Record<string, string> = {
    draft: JSON.stringify({
      identity: { campaign_name: "Draft", warband_name: "Band", warband_type: "Sisters", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: true, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 }, current_state_number: 0,
      warriors: [], battles: [], states: [], post_battles: [], inventory: [], special_rules: [], manual_log: [],
    }),
  };
  return JSON.parse(samples[name]);
}

describe("desktop persistence parity", () => {
  it("serializes and restores a draft without changing campaign data", () => {
    const campaign = campaignFromFixture("draft");
    const saved = adapter.serializeCampaign(campaign);
    expect(saved.ok).toBe(true);
    if (!saved.ok) return;
    const loaded = parseCampaignFileDetailed(saved.text);
    expect(loaded.ok).toBe(true);
    if (loaded.ok) expect(loaded.campaign).toEqual(campaign);
  });

  it("rejects corrupt JSON and retired formats through the application port", () => {
    expect(adapter.parseCampaignFile("{broken").ok).toBe(false);
    for (const version of [1, 2, 3, 4]) {
      const result = adapter.parseCampaignFile(JSON.stringify({
        marker: "MORDHEIM_CAMPAIGN_MANAGER", format_version: version,
        saved_at: "2026-09-10T00:00:00Z", campaign: {},
      }));
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.reason).toBe("retired_version");
    }
  });

  it("refuses malformed campaign data before any file text is emitted", () => {
    const result = adapter.serializeCampaign({ identity: {} } as never);
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("schema_violation");
      expect(result.message).toContain("Refusing to save");
    }
  });

  // Markdown-summary and filename-slug parity can be asserted against the
  // existing seams: `review-exports.ts` (ledgerText/rosterSummaryText) and
  // `service.prepareExport` (the .mordheim export filename slug).
});
