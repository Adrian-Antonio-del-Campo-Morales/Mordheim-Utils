/**
 * Parity port of the desktop wyrdstone-sale behaviour in
 * `test_post_battle_engine.py` (`test_wyrdstone_sale_value_comes_from_the_kb_table`,
 * `test_sell_wyrdstone_applies_once`, `test_sell_wyrdstone_rejects_more_than_hoard`),
 * grounded in desktop `sell_wyrdstone` / `wyrdstone_sale_value`.
 * Exercised against the web `quoteWyrdstoneSale` / `sellWyrdstone` seams in
 * `wyrdstone-sale-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";

import { quoteWyrdstoneSale, sellWyrdstone } from "@app/campaign/features/economy/wyrdstone-sale-workflow";

/** A pending post-battle with 8 models and 4 shards available to sell. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function makePending(): { doc: CampaignDocument; reader: any } {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Sale", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
        { id: "hench-1", name: "Swordsmen", profile_name: "Swordsman", kind: "henchman", stats: { M: 4, WS: 3 }, equipment: [], skills: [], experience: 5, cost: 30, quantity: 7 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 2, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 4, completed_steps: [0, 1, 2, 3], review_open: false,
        pending_follow_ups: [], gold_delta: 20, wyrdstone_delta: 2, wyrdstone_sold: 0,
        experience_applied: false, pending_advances: [],
        step_state: {}, sale_resolved: false, equipment_obligations: [], acknowledgements: {}, event_log: [], searches: {},
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const reader: any = {
    campaignSection(section: string) {
      if (section === "exploration-and-income") {
        return {
          income: {
            wyrdstone_sale: {
              cells: [
                { when: { fragments_sold: { min: 1, max: 1 }, warband_size: { min: 7, max: 9 } }, profit_gc: 35 },
                { when: { fragments_sold: { min: 2, max: 2 }, warband_size: { min: 7, max: 9 } }, profit_gc: 50 },
              ],
            },
          },
        };
      }
      return undefined;
    },
  };
  return { doc: doc as CampaignDocument, reader };
}

describe("sellWyrdstone (desktop sell_wyrdstone)", () => {
  it("quotes the sale price from the KB table by quantity and warband size", () => {
    const { doc, reader } = makePending();
    expect(quoteWyrdstoneSale(doc, reader, 1)).toMatchObject({ quantity: 1, warband_size: 8, available: 4, profit: 35 });
    expect(quoteWyrdstoneSale(doc, reader, 2)).toMatchObject({ quantity: 2, warband_size: 8, profit: 50 });
  });

  it("applies the sale once, bumping gold_delta and marking the sequence resolved", () => {
    const { doc, reader } = makePending();
    const result = sellWyrdstone(doc, reader, 2);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.document.campaign.post_battles[0];
    expect(post.gold_delta).toBe(20 + 50);
    expect(post.wyrdstone_sold).toBe(2);
    expect(post.sale_resolved).toBe(true);
    const second = sellWyrdstone(result.document, reader, 1);
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.message).toContain("once per post-battle");
  });

  it("rejects selling more shards than are available", () => {
    const { doc, reader } = makePending();
    const result = sellWyrdstone(doc, reader, 99);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Only 4 shard");
  });

  it("rejects a negative or non-whole quantity", () => {
    const { doc, reader } = makePending();
    const negative = sellWyrdstone(doc, reader, -1);
    expect(negative.ok).toBe(false);
    const fractional = sellWyrdstone(doc, reader, 1.5);
    expect(fractional.ok).toBe(false);
  });

  it("blocks the sale while an exploration special-result follow-up is pending", () => {
    const { doc, reader } = makePending();
    (doc.campaign.post_battles[0] as unknown as { pending_follow_ups: unknown[] }).pending_follow_ups = [
      { type: "exploration_followup" },
    ];
    const result = sellWyrdstone(doc, reader, 1);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("exploration");
  });

  it("requires a pending post-battle to sell at all", () => {
    const { doc, reader } = makePending();
    (doc.campaign as unknown as { post_battles: unknown[] }).post_battles = [];
    const result = sellWyrdstone(doc, reader, 1);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("No pending post-battle");
  });
});