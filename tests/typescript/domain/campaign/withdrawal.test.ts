/**
 * T10 — withdrawal of the members that left the table.
 *
 * The domain operation receives the ids T13 will hand it and applies the roster
 * consequence of "Blimey/Got Away": a hero or one-member group is removed, a
 * henchman group loses one member, the last member removes the group, an audit
 * entry is written once and a repeated call cannot remove a member twice.
 *
 * Purity: plain Node, the real v5 adapter, no React and no knowledge reader.
 */
import { describe, expect, it } from "vitest";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";
import {
  withdrawLeftTableMembers,
  withdrawalLog,
  withdrawnMemberIds,
} from "@domain/campaign/kernel/withdrawal";
import type { Campaign, CampaignDocument, Warrior } from "@domain/campaign/kernel/usecases";

const adapter = new CampaignFileV5Adapter();

function warrior(id: string, profileId: string, kind: Warrior["kind"], quantity = 1, equipment: Warrior["equipment"] = []): Warrior {
  return {
    id,
    name: `${profileId} ${id}`,
    profile_name: profileId,
    kind,
    stats: {},
    equipment,
    skills: [],
    experience: 0,
    cost: 0,
    quantity,
    profile_id: profileId,
  };
}

function campaign(warriors: readonly Warrior[]): Campaign {
  return {
    identity: { campaign_name: "Withdrawal", warband_name: "Pirates", warband_type: "Pirates", band_id: "pirates-of-the-cathayan-sea-sar", mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors,
    battles: [],
    states: [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0 }],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
}

function document(warriors: readonly Warrior[]): CampaignDocument {
  return { campaign: campaign(warriors), view: {} };
}

function roundtrip(state: CampaignDocument): CampaignDocument {
  const serialized = adapter.serializeCampaign(state.campaign);
  expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
  if (!serialized.ok) return state;
  const parsed = parseCampaignFileDetailed(serialized.text);
  expect(parsed.ok).toBe(true);
  if (!parsed.ok) return state;
  return { campaign: parsed.campaign, view: parsed.view };
}

describe("T10 withdrawal (campaign consequence)", () => {
  it("removes a hero and records the audit entry", () => {
    const result = withdrawLeftTableMembers(document([warrior("warlord", "disgraced-warlord", "hero"), warrior("mate", "shanghaires", "hero")]), {
      member_ids: ["mate"],
      reason: "left the table",
      battle_number: 1,
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.state.campaign.warriors.map((row) => row.id)).toEqual(["warlord"]);
    const log = withdrawalLog(result.state);
    expect(log).toHaveLength(1);
    expect(log[0]).toMatchObject({ kind: "left_table_withdrawal", order: 1, battle_number: 1, reason: "left the table" });
    expect(log[0]?.members).toEqual([{ warrior_id: "mate", name: "shanghaires mate", profile_id: "shanghaires", quantity: 1 }]);
    expect(withdrawnMemberIds(result.state).has("mate")).toBe(true);
  });

  it("reduces a group by one member and keeps the rest", () => {
    const group = warrior("deck", "deck-hands", "henchman", 3, [
      { item_id: "sword", name: "Sword", quantity: 3, per_model: true, acquisition: "purchase" },
    ]);
    const result = withdrawLeftTableMembers(document([warrior("warlord", "disgraced-warlord", "hero"), group]), { member_ids: ["deck"] });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const row = result.state.campaign.warriors.find((item) => item.id === "deck");
    expect(row?.quantity).toBe(2);
    expect(row?.equipment[0]?.quantity).toBe(2);
  });

  it("removes a group when its last member leaves", () => {
    const result = withdrawLeftTableMembers(document([warrior("deck", "deck-hands", "henchman", 1)]), { member_ids: ["deck"] });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.state.campaign.warriors.some((row) => row.id === "deck")).toBe(false);
  });

  it("refuses a duplicate id in the same request and a second call for the same member", () => {
    const duplicate = withdrawLeftTableMembers(document([warrior("mate", "shanghaires", "hero")]), { member_ids: ["mate", "mate"] });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.reason).toBe("not_found");

    const first = withdrawLeftTableMembers(document([warrior("mate", "shanghaires", "hero")]), { member_ids: ["mate"] });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const again = withdrawLeftTableMembers(first.state, { member_ids: ["mate"] });
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.reason).toBe("conflict");
  });

  it("rejects an unknown id and an empty request", () => {
    const unknown = withdrawLeftTableMembers(document([warrior("mate", "shanghaires", "hero")]), { member_ids: ["ghost"] });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.reason).toBe("not_found");
    const empty = withdrawLeftTableMembers(document([warrior("mate", "shanghaires", "hero")]), { member_ids: [] });
    expect(empty.ok).toBe(false);
    if (!empty.ok) expect(empty.reason).toBe("invalid_input");
  });

  it("keeps the removal and the audit across a v5 round-trip", () => {
    const removed = withdrawLeftTableMembers(document([warrior("warlord", "disgraced-warlord", "hero"), warrior("deck", "deck-hands", "henchman", 2)]), { member_ids: ["deck"] });
    expect(removed.ok).toBe(true);
    if (!removed.ok) return;
    const restored = roundtrip(removed.state);
    expect(restored.campaign.warriors.find((row) => row.id === "deck")?.quantity).toBe(1);
    expect(withdrawalLog(restored)).toHaveLength(1);
    expect(withdrawnMemberIds(restored).has("deck")).toBe(true);
  });

  it("is not available while the warband is still a draft", () => {
    const draft = document([warrior("mate", "shanghaires", "hero")]);
    const state: CampaignDocument = { campaign: { ...draft.campaign, configuration: { ...draft.campaign.configuration, is_draft: true }, current_state_number: 0 }, view: {} };
    const result = withdrawLeftTableMembers(state, { member_ids: ["mate"] });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_permitted_in_draft");
  });
});
