/**
 * Parity port of the desktop manual-correction behaviour in `controller.py`
 * (`adjust_resource`, `manually_add_item`) — no dedicated desktop test; ported
 * from the implementation. Exercised against the web `correctResource` /
 * `addManualStashItem` seams in `manual-corrections-workflow.ts` — no service.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, KnowledgeReader } from "@domain/campaign/index";

import { addManualStashItem, correctResource } from "@app/campaign/features/economy/manual-corrections-workflow";

function makeDoc(is_draft = false, withPost = true): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Corrections", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 2, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: withPost ? [{
        battle_number: 1, complete: false, active_step: 2, completed_steps: [], review_open: false,
        pending_follow_ups: [], gold_delta: 0, wyrdstone_delta: 0, wyrdstone_sold: 0,
        experience_applied: false, pending_advances: [],
        step_state: {}, sale_resolved: false, equipment_obligations: [], acknowledgements: {}, event_log: [], searches: {},
      }] : [],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

const itemReader: KnowledgeReader = {
  queryKnowledge(query: { id: { kind: string; value: string } }) {
    if (query.id.kind === "item_id" && query.id.value === "axe") {
      return {
        ok: true as const,
        record: {
          kind: "item" as never,
          id: query.id as never,
          names: { en: "Axe" } as Record<string, string>,
          data: { kind: "close-combat-weapon", value: 5 },
        },
      };
    }
    return { ok: false as const, reason: "not_found" as const };
  },
  queryMany() {
    return [];
  },
} as unknown as KnowledgeReader;

describe("correctResource (desktop adjust_resource)", () => {
  it("adjusts post-battle gold on the delta and logs the correction", () => {
    const result = correctResource(makeDoc(), { resource: "gold_crowns", delta: 50, reason: "refund" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.document.campaign.post_battles[0];
    expect(post.gold_delta).toBe(50);
    expect(result.document.campaign.manual_log.at(-1)).toMatchObject({ type: "manual_resource_correction", resource: "gold_crowns", delta: 50, reason: "refund" });
    expect(post.event_log?.at(-1)).toMatchObject({ type: "manual_resource_correction", resource: "gold_crowns" });
  });

  it("routes each resource to its own field", () => {
    const wyr = correctResource(makeDoc(), { resource: "wyrdstone_fragments", delta: 3, reason: "audit" });
    expect(wyr.ok && wyr.document.campaign.post_battles[0].wyrdstone_delta).toBe(3);
    const treasure = correctResource(makeDoc(), { resource: "treasures", delta: 2, reason: "audit" });
    expect(treasure.ok && treasure.document.campaign.resources.treasures).toBe(2);
    const points = correctResource(makeDoc(), { resource: "campaign_points", delta: 4, reason: "audit" });
    expect(points.ok && points.document.campaign.resources.campaign_points).toBe(4);
  });

  it("requires a reason, a non-zero whole delta and a known resource", () => {
    const noReason = correctResource(makeDoc(), { resource: "gold_crowns", delta: 5, reason: "  " });
    expect(noReason.ok).toBe(false);
    if (!noReason.ok) expect(noReason.message).toContain("reason");
    const zero = correctResource(makeDoc(), { resource: "gold_crowns", delta: 0, reason: "audit" });
    expect(zero.ok).toBe(false);
    if (!zero.ok) expect(zero.message).toContain("non-zero");
    const unknown = correctResource(makeDoc(), { resource: "nonsense", delta: 5, reason: "audit" });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.message).toContain("Unknown resource");
  });

  it("rejects a correction that would leave a negative balance", () => {
    const result = correctResource(makeDoc(), { resource: "gold_crowns", delta: -600, reason: "spend" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("negative balance");
  });

  it("allows only gold during creation and rejects outside draft/post-battle", () => {
    const draftGold = correctResource(makeDoc(true), { resource: "gold_crowns", delta: 25, reason: "top-up" });
    expect(draftGold.ok).toBe(true);
    if (draftGold.ok) expect(draftGold.document.campaign.configuration.starting_gold).toBe(525);
    const draftWyr = correctResource(makeDoc(true), { resource: "wyrdstone_fragments", delta: 1, reason: "top-up" });
    expect(draftWyr.ok).toBe(false);
    if (!draftWyr.ok) expect(draftWyr.message).toContain("Only gold crowns");
    const outside = correctResource(makeDoc(false, false), { resource: "gold_crowns", delta: 5, reason: "top-up" });
    expect(outside.ok).toBe(false);
    if (!outside.ok) expect(outside.message).toContain("only during creation or post-battle");
  });
});

describe("addManualStashItem (desktop manually_add_item)", () => {
  it("adds a KB item into the stash and logs it", () => {
    const result = addManualStashItem(makeDoc(), itemReader, { item_id: "axe", quantity: 2, reason: "gift" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const row = result.document.campaign.inventory.find((item) => item.id === "axe");
    expect(row?.owned).toBe(2);
    expect(row?.stash).toBe(2);
    expect(row?.value).toBe(5);
    expect(result.document.campaign.manual_log.at(-1)).toMatchObject({ type: "manual_item_correction", item_id: "axe", quantity: 2 });
    expect(result.document.campaign.post_battles[0].event_log?.at(-1)).toMatchObject({ type: "manual_item_correction" });
  });

  it("increments an existing inventory row", () => {
    const doc = makeDoc();
    (doc.campaign as unknown as { inventory: unknown[] }).inventory = [{ id: "axe", name: "Axe", category: "weapon", owned: 1, equipped: 0, stash: 1, value: 5 }];
    const result = addManualStashItem(doc, itemReader, { item_id: "axe", quantity: 3, reason: "gift" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const row = result.document.campaign.inventory.find((item) => item.id === "axe");
    expect(row?.owned).toBe(4);
    expect(row?.stash).toBe(4);
  });

  it("rejects a blank reason, a non-positive quantity, an unknown item and the wrong phase", () => {
    const noReason = addManualStashItem(makeDoc(), itemReader, { item_id: "axe", quantity: 1, reason: " " });
    expect(noReason.ok).toBe(false);
    if (!noReason.ok) expect(noReason.message).toContain("reason");
    const badQuantity = addManualStashItem(makeDoc(), itemReader, { item_id: "axe", quantity: 0, reason: "gift" });
    expect(badQuantity.ok).toBe(false);
    if (!badQuantity.ok) expect(badQuantity.message).toContain("positive");
    const unknown = addManualStashItem(makeDoc(), itemReader, { item_id: "nope", quantity: 1, reason: "gift" });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.message).toContain("KB catalogue");
    const outside = addManualStashItem(makeDoc(false, false), itemReader, { item_id: "axe", quantity: 1, reason: "gift" });
    expect(outside.ok).toBe(false);
    if (!outside.ok) expect(outside.message).toContain("only during creation or post-battle");
  });
});