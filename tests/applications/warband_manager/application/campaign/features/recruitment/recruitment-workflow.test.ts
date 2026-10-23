/**
 * Parity port of the desktop recruitment/veteran tests:
 * `test_post_battle_engine.py` (existing-group recruit, dismiss one member,
 * recruit band profile), `test_extended_audit_regressions.py` (two weapons
 * per member, obligations), `test_economy_sequence_matrix.py` (heroes are
 * recruited individually) and `test_campaign_sequence_matrix.py` (recruited
 * fixed equipment is registered). Exercised against the existing
 * `recruitment-workflow.ts` / `veteran-workflow.ts` seams — no service.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/kernel/ports";
import {
  dismissRecruit,
  recruitBandProfile,
  recruitGroupMember,
} from "@app/campaign/features/recruitment/recruitment-workflow";
import { applyVeteranPool } from "@app/campaign/features/recruitment/veteran-workflow";

/** KB reader: a Sisters of Sigmar band with a henchman and a hero profile. */
function reader(): KnowledgeReader & {
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
} {
  const queryKnowledge: KnowledgeReader["queryKnowledge"] = (query) => {
    if (query.id.kind === "band_id") {
      return {
        ok: true,
        record: {
          kind: "band",
          id: { kind: "band_id", value: "sisters-of-sigmar" },
          names: { en: "Sisters of Sigmar" },
          data: {
            roster: {
              members: [
                { profile_id: "sister", maximum: 5, group_size: { maximum: 5 } },
                { profile_id: "matriarch", maximum: 1, group_size: { maximum: 1 } },
              ],
            },
          },
        },
      };
    }
    if (query.id.kind === "profile_id" && query.id.value === "sister") {
      return {
        ok: true,
        record: {
          kind: "profile",
          id: { kind: "profile_id", value: "sister" },
          names: { en: "Sister" },
          data: {
            type: "henchman", cost: 45, experience: 0,
            characteristics: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
            fixed_equipment: ["dagger"], combat_traits: { starting_skills: [] },
            inherent_rules: [], skill_access: [],
          },
        },
      };
    }
    if (query.id.kind === "profile_id" && query.id.value === "matriarch") {
      return {
        ok: true,
        record: {
          kind: "profile",
          id: { kind: "profile_id", value: "matriarch" },
          names: { en: "Matriarch", es: "Matriarca" },
          data: {
            type: "hero", cost: 65, experience: 10,
            characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 8 },
            fixed_equipment: [], combat_traits: { starting_skills: [] },
            inherent_rules: [], skill_access: [],
          },
        },
      };
    }
    return { ok: false, reason: "not_found" };
  };
  return {
    queryKnowledge,
    queryMany: (queries) => queries.map((q) => queryKnowledge(q)),
    list: () => [],
    campaignSection: (section) =>
      section === "recruitment-and-veterans"
        ? { veteran_availability: [{ incremental_cost: { per_experience_point_gc: 2 } }] }
        : {},
  };
}

/** A pending post-battle with the veteran pool already resolved. */
function makePending(): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Recruit", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "matriarch", name: "Sigrid", profile_name: "Matriarch", kind: "hero", profile_id: "matriarch", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
        {
          id: "sisters", name: "Sisters", profile_name: "Sister", kind: "henchman", profile_id: "sister",
          stats: { M: 4, WS: 3 }, skills: [], experience: 5, cost: 45,
          equipment: [
            { item_id: "hammer", name: "Hammer", quantity: 1, per_model: true, acquisition: "purchase", transferable: true, unit_cost: 5 },
            { item_id: "club", name: "Club", quantity: 1, per_model: true, acquisition: "fixed", transferable: false, unit_cost: 0 },
          ],
        },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 2, max_models: 15, heroes: 1, henchmen: 1, experience: 15 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false,
        pending_follow_ups: [], veteran_pool: 5, sale_resolved: true,
        step_state: { veterans: { resolved: true, dice: [2, 3], pool: 5 } },
        gold_delta: 0, equipment_obligations: [], event_log: [], searches: {},
      }],
      inventory: [{ id: "hammer", name: "Hammer", category: "close-combat-weapon", owned: 1, equipped: 1, stash: 0, value: 5 }],
      special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("recruitGroupMember (desktop add_member_to_group)", () => {
  it("spends veteran XP + gold, adds a member and leaves equipment obligations pending", () => {
    const result = recruitGroupMember(makePending(), reader(), { warrior_id: "sisters" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const group = result.document.campaign.warriors.find((w) => w.id === "sisters")!;
    expect((group as { quantity?: number }).quantity).toBe(2);
    const post = result.document.campaign.post_battles[0];
    // cost 45 + experience 5 × rate 2 = 55 gc from the pool-gated recruit.
    expect(post.veteran_pool).toBe(0);
    expect(post.gold_delta).toBe(-55);
    expect((post.equipment_obligations ?? []).length).toBeGreaterThan(0);
    // Fixed per-model equipment is registered in inventory.
    expect(result.document.campaign.inventory.find((i) => i.id === "club")).toMatchObject({ owned: 1, equipped: 1 });
  });

  it("is rejected until veteran availability is resolved", () => {
    const doc = makePending();
    (doc.campaign.post_battles[0] as { step_state?: unknown }).step_state = {};
    const result = recruitGroupMember(doc, reader(), { warrior_id: "sisters" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("veteran");
  });
});

describe("dismissRecruit one_member (desktop dismiss_warrior)", () => {
  function group(quantity: number, obligation?: number): CampaignDocument {
    const doc = makePending();
    return {
      ...doc,
      campaign: {
        ...doc.campaign,
        warriors: doc.campaign.warriors.map((w) =>
          w.id === "sisters"
            ? {
                ...w,
                quantity,
                equipment: [{ item_id: "hammer", name: "Hammer", quantity, per_model: true, acquisition: "purchase", transferable: true, unit_cost: 5 }],
              }
            : w,
        ),
        inventory: [{ id: "hammer", name: "Hammer", category: "close-combat-weapon", owned: quantity, equipped: quantity, stash: 0, value: 5 }],
        post_battles: doc.campaign.post_battles.map((p) => ({
          ...p,
          equipment_obligations: obligation
            ? [{ warrior_id: "sisters", item_id: "hammer", item_name: "Hammer", quantity: obligation }]
            : [],
        })),
      },
    };
  }

  it("returns one equipment set to stash", () => {
    const result = dismissRecruit(group(2), { warrior_id: "sisters", one_member: true });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const sisters = result.document.campaign.warriors.find((w) => w.id === "sisters")!;
    expect((sisters as { quantity?: number }).quantity).toBe(1);
    const hammer = result.document.campaign.inventory.find((i) => i.id === "hammer")!;
    expect(hammer).toMatchObject({ equipped: 1, stash: 1 });
  });

  it("clears the now-unneeded equipment obligations", () => {
    const result = dismissRecruit(group(2, 1), { warrior_id: "sisters", one_member: true });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].equipment_obligations).toHaveLength(0);
  });
});

describe("recruitBandProfile (desktop recruit_band_profile)", () => {
  it("adds a henchman, deducts gold and registers fixed equipment", () => {
    const result = recruitBandProfile(makePending(), reader(), { profile_id: "sister", quantity: 1, name: "Sigrid" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.filter((w) => w.profile_id === "sister")).toHaveLength(2);
    expect(result.document.campaign.post_battles[0].gold_delta).toBe(-45);
    expect(result.document.campaign.inventory.find((i) => i.id === "dagger")).toBeTruthy();
    expect(result.document.campaign.warriors.at(-1)?.name).toBe("Sigrid II");
  });

  it("rejects multi-member hero rows", () => {
    const result = recruitBandProfile(makePending(), reader(), { profile_id: "matriarch", quantity: 2 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("individually");
  });

  it("uses the requested locale for an automatic Hero name", () => {
    const pending=makePending();
    const document={...pending,campaign:{...pending.campaign,warriors:pending.campaign.warriors.filter((warrior)=>warrior.profile_id!=="matriarch")}};
    const result = recruitBandProfile(document, reader(), { profile_id: "matriarch", locale: "es" });
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.document.campaign.warriors.at(-1)?.name).toBe("Matriarca");
  });

  it("rejects recruitment over the roster limit", () => {
    const result = recruitBandProfile(makePending(), reader(), { profile_id: "sister", quantity: 5 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("limit");
  });
});

describe("applyVeteranPool (desktop apply_veteran_pool)", () => {
  it("sets the pool from 2D6 and refuses a second roll", () => {
    const doc = makePending();
    const post = doc.campaign.post_battles[0] as { veteran_pool?: number; step_state?: unknown };
    post.veteran_pool = 0;
    post.step_state = {};
    const result = applyVeteranPool(doc, [2, 3]);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].veteran_pool).toBe(5);
    const again = applyVeteranPool(result.document, [1, 1]);
    expect(again.ok).toBe(false);
  });

  it("requires exactly 2D6 in range", () => {
    expect(applyVeteranPool(makePending(), [7, 1]).ok).toBe(false);
  });
});
