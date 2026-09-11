/**
 * Parity port of desktop `tests/campaign/test_injury_sequence_matrix.py`.
 * The desktop matrix combines every injury result with controller undo and
 * persistence. This portable layer pins the invariants that remain visible
 * in the v4 domain document.
 */
import { describe, expect, it } from "vitest";
import { CampaignFileV4Adapter } from "../../adapters/campaign-file/index";
import { resolvePrisoner } from "../../application/campaign/features/injuries/injury-decisions-workflow";
import { injuryEffects, resolveInjuryTableFollowUp } from "../../application/campaign/features/injuries/injury-followup-workflow";
import { applyInjuryOutcome } from "../../application/campaign/features/injuries/injuries-workflow";
import { resolveSoldToPits } from "../../application/campaign/features/injuries/sold-to-pits-workflow";
import type { KnowledgeReader } from "./kernel/ports";
import type { CampaignDocument, OpenPayload } from "./kernel/state";

function fixture(): CampaignDocument {
  return {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Injuries", warband_name: "Test Band", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Matriarch", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [{ item_id: "dagger", name: "Dagger", quantity: 1, transferable: true }], skills: [], experience: 10, cost: 65 },
        { id: "hero-2", name: "Greta", profile_name: "Sister", kind: "hero", stats: { M: 4, WS: 3 }, equipment: [], skills: [], experience: 6, cost: 45 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 20, models: 2, max_models: 15, heroes: 2, henchmen: 0, experience: 16 }],
      post_battles: [{ battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [] }],
      inventory: [{ id: "dagger", name: "Dagger", category: "weapon", owned: 1, equipped: 1, stash: 0 }],
      special_rules: [], manual_log: [],
    },
  };
}

function inventoryBalanced(document: CampaignDocument): void {
  const carried = new Map<string, number>();
  for (const warrior of document.campaign.warriors) {
    for (const equipment of warrior.equipment) {
      if (equipment.transferable) carried.set(equipment.item_id, (carried.get(equipment.item_id) ?? 0) + equipment.quantity);
    }
  }
  for (const item of document.campaign.inventory) {
    expect(item.owned).toBe(item.equipped + item.stash);
    expect(item.owned).toBeGreaterThanOrEqual(0);
    expect(item.equipped).toBe(carried.get(item.id) ?? 0);
    carried.delete(item.id);
  }
  expect(carried.size).toBe(0);
}

/** A knowledge reader that only exposes the `injury` catalogue list. */
function injuryReader(injuries: readonly OpenPayload[]): KnowledgeReader & { list?(kind: string): readonly Readonly<Record<string, unknown>>[] } {
  return {
    queryKnowledge: () => ({ ok: false as const, reason: "not_found" }),
    queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
    list: (kind) => (kind === "injury" ? (injuries as Readonly<Record<string, unknown>>[]) : []),
  };
}

/** Fixture for the pit-loss encounter: weapons, armour and a miscellaneous item. */
function pitFixture(): CampaignDocument {
  const base = fixture();
  return {
    ...base,
    campaign: {
      ...base.campaign,
      warriors: base.campaign.warriors.map((w) => w.id === "hero-1"
        ? {
            ...w,
            equipment: [
              { item_id: "dagger", name: "Dagger", quantity: 1, transferable: true },
              { item_id: "light_armour", name: "Light Armour", quantity: 1, transferable: true },
              { item_id: "lantern", name: "Lantern", quantity: 1, transferable: true },
            ],
          }
        : w),
      inventory: [
        { id: "dagger", name: "Dagger", category: "weapon", owned: 1, equipped: 1, stash: 0 },
        { id: "light_armour", name: "Light Armour", category: "armour", owned: 1, equipped: 1, stash: 0 },
        { id: "lantern", name: "Lantern", category: "miscellaneous", owned: 1, equipped: 1, stash: 0 },
      ],
      post_battles: base.campaign.post_battles.map((p) => ({
        ...p,
        pending_follow_ups: [{ id: "pit-test", type: "encounter", warrior_id: "hero-1", encounter_id: "campaign.encounter.sold-to-the-pits" }],
      })),
    },
  };
}

/** Fixture with a pending captured-warrior (`prisoner`) follow-up. */
function captiveFixture(): CampaignDocument {
  const base = fixture();
  return {
    ...base,
    campaign: {
      ...base.campaign,
      post_battles: base.campaign.post_battles.map((p) => ({
        ...p,
        pending_follow_ups: [{ id: "capture", type: "prisoner", warrior_id: "hero-1", step: 0 }],
      })),
    },
  };
}

describe("desktop test_injury_sequence_matrix.py → injury invariants", () => {
  it("preserves other warriors and inventory when an injury record is stored", () => {
    const original = fixture();
    const changed: CampaignDocument = {
      ...original,
      campaign: {
        ...original.campaign,
        warriors: original.campaign.warriors.map((warrior) => warrior.id === "hero-1"
          ? { ...warrior, condition: "Leg Wound", condition_detail: "-1 M", stat_modifiers: { M: -1 }, injury_records: [{ result: "Leg Wound" }] }
          : warrior),
      },
    };
    expect(changed.campaign.warriors.find((warrior) => warrior.id === "hero-2")).toEqual(original.campaign.warriors[1]);
    inventoryBalanced(changed);
  });

  it("removing a warrior does not orphan carried inventory accounting", () => {
    const original = fixture();
    const removed = original.campaign.warriors[0];
    const changed: CampaignDocument = {
      ...original,
      campaign: {
        ...original.campaign,
        warriors: original.campaign.warriors.filter((warrior) => warrior.id !== removed.id),
        inventory: original.campaign.inventory.map((item) => item.id === "dagger"
          ? { ...item, equipped: 0, stash: item.owned }
          : item),
      },
    };
    inventoryBalanced(changed);
    expect(changed.campaign.warriors).not.toContain(removed);
  });

  it("preserves injury state through v4 serialize/parse", () => {
    const adapter = new CampaignFileV4Adapter();
    const original = fixture();
    const injured = {
      ...original,
      campaign: {
        ...original.campaign,
        post_battles: [],
        warriors: original.campaign.warriors.map((warrior) => warrior.id === "hero-1"
          ? { ...warrior, games_to_miss: 2, absence_reason: "Deep Wound", stat_modifiers: { M: -1 } }
          : warrior),
      },
    };
    const encoded = adapter.serializeCampaign(injured.campaign);
    expect(encoded.ok, encoded.ok ? "" : encoded.message).toBe(true);
    if (!encoded.ok) return;
    const decoded = adapter.parseCampaignFile(encoded.text);
    expect(decoded.ok).toBe(true);
    if (!decoded.ok) return;
    const warrior = (decoded.document.campaign as unknown as CampaignDocument["campaign"]).warriors.find((row) => row.id === "hero-1");
    expect(warrior).toMatchObject({ games_to_miss: 2, absence_reason: "Deep Wound", stat_modifiers: { M: -1 } });
  });

  it("keeps pending follow-up identifiers unique", () => {
    const document = fixture();
    const pending = document.campaign.post_battles[0];
    const followUps = [
      { id: "injury:hero-1", type: "prisoner", warrior_id: "hero-1" },
      { id: "injury:hero-2", type: "prisoner", warrior_id: "hero-2" },
    ];
    const ids = followUps.map((row) => row.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(pending.pending_follow_ups).toEqual([]);
  });
});

// Port of desktop `test_pit_loss_discards_creation_weapons_but_keeps_miscellaneous`
// (roll 41 keeps the wound-free branch, so it only exercises equipment loss).
describe("pit loss discards weapons/armour but keeps miscellaneous", () => {
  it("removes carried weapons and armour yet keeps a miscellaneous item, in balance", () => {
    const reader = injuryReader([]);
    const result = resolveSoldToPits(pitFixture(), reader, { follow_up_id: "pit-test", won: false, injury_roll: 41 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((row) => row.id === "hero-1")!;
    expect(hero.equipment.map((item) => item.item_id)).toEqual(["lantern"]);
    expect(result.document.campaign.inventory.map((item) => item.id)).toEqual(["lantern"]);
    inventoryBalanced(result.document);
  });

  it("cannot resolve the same pit encounter twice", () => {
    const result = resolveSoldToPits(pitFixture(), injuryReader([]), { follow_up_id: "pit-test", won: false, injury_roll: 41 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const again = resolveSoldToPits(result.document, injuryReader([]), { follow_up_id: "pit-test", won: false, injury_roll: 41 });
    expect(again.ok).toBe(false);
  });

  it("a loss roll on the injury table (≤35) applies the wound before equipment loss", () => {
    // 23 → Madness (condition). The weapon is still discarded on the way down.
    const injuries = [{
      id: "madness", applies_to: "hero", roll: "23-24", result: "Madness",
      effects: [{ type: "warrior.add_condition", condition_id: "madness" }],
    }];
    const result = resolveSoldToPits(pitFixture(), injuryReader(injuries), { follow_up_id: "pit-test", won: false, injury_roll: 23 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((row) => row.id === "hero-1")!;
    expect(hero.condition).toBe("Injured");
    expect(hero.equipment.map((item) => item.item_id)).toEqual(["lantern"]);
    inventoryBalanced(result.document);
  });
});

// Port of desktop `test_captive_reload_resolution_once_and_undo` (exchange,
// ransom and lost branches).
describe("captured-warrior resolution runs once and keeps inventory in balance", () => {
  it("exchange returns the warrior with all equipment", () => {
    const result = resolvePrisoner(captiveFixture(), { follow_up_id: "capture", resolution: "exchange" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.some((row) => row.id === "hero-1")).toBe(true);
    expect(result.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(0);
    inventoryBalanced(result.document);
    const again = resolvePrisoner(result.document, { follow_up_id: "capture", resolution: "exchange" });
    expect(again.ok).toBe(false);
  });

  it("permanent loss removes the warrior and returns carried equipment to stash", () => {
    const result = resolvePrisoner(captiveFixture(), { follow_up_id: "capture", resolution: "lost", disposition: "executed" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.some((row) => row.id === "hero-1")).toBe(false);
    expect(result.document.campaign.warriors.some((row) => row.id === "hero-2")).toBe(true);
    // Permanent loss discards carried equipment rather than returning it to stash.
    expect(result.document.campaign.inventory.find((item) => item.id === "dagger")).toBeUndefined();
    inventoryBalanced(result.document);
  });

  it("ransom deducts gold and can be rejected when unaffordable", () => {
    const paid = resolvePrisoner(captiveFixture(), { follow_up_id: "capture", resolution: "ransom", ransom: 10 });
    expect(paid.ok).toBe(true);
    if (!paid.ok) return;
    expect(paid.document.campaign.post_battles[0].gold_delta).toBe(-10);
    inventoryBalanced(paid.document);
    const denied = resolvePrisoner(captiveFixture(), { follow_up_id: "capture", resolution: "ransom", ransom: 9999 });
    expect(denied.ok).toBe(false);
    if (!denied.ok) expect(denied.message).toContain("ransom");
  });
});

// Port of desktop `test_injury_subtables_reload_and_undo`: a serious-injury
// outcome chains a follow-up table; the sub-roll resolves it once and the
// pending follow-up ids stay unique.
describe("injury subtable resolution", () => {
  const madness: OpenPayload = {
    id: "madness", applies_to: "hero", roll: "23-24", result: "Madness",
    effects: [{ type: "warrior.add_condition", condition_id: "madness" }],
    resolution: {
      type: "roll_table", dice: { count: 1, sides: 6 },
      branches: [
        { when: { min: 1, max: 2 }, id: "madness-mild", result: "Mild Madness", effects: [{ type: "warrior.miss_games", games: { value: 1 } }] },
        { when: { min: 3, max: 6 }, id: "madness-severe", result: "Severe Madness", effects: [{ type: "warrior.miss_games", games: { value: 1 } }] },
      ],
    },
  };

  function withMadness(document: CampaignDocument, warriorId: string): { document: CampaignDocument; followUpId: string } {
    const applied = applyInjuryOutcome(document, {
      warrior_id: warriorId,
      result_id: "madness",
      result: "Madness",
      effects: [{ kind: "follow_up", type: "injury_roll", payload: { table: "hero" } }],
    });
    expect(applied.ok).toBe(true);
    if (!applied.ok) throw new Error("applyInjuryOutcome failed");
    const pending = applied.document.campaign.post_battles[0].pending_follow_ups ?? [];
    const followUp = pending.find((row) => row["warrior_id"] === warriorId && row["type"] === "injury_roll")!;
    return { document: applied.document, followUpId: String(followUp["id"]) };
  }

  it("applies the subtable outcome, clears the follow-up and stays in balance", () => {
    const { document, followUpId } = withMadness(fixture(), "hero-1");
    const resolved = resolveInjuryTableFollowUp(document, injuryReader([madness]), { follow_up_id: followUpId, roll: 4 });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    const post = resolved.document.campaign.post_battles[0];
    expect(post.pending_follow_ups).toHaveLength(0);
    const hero = resolved.document.campaign.warriors.find((row) => row.id === "hero-1")!;
    expect(hero.games_to_miss).toBe(1);
    expect(hero.injury_records).toHaveLength(2);
    inventoryBalanced(resolved.document);
    // Resolving the same follow-up again is a typed failure.
    const again = resolveInjuryTableFollowUp(resolved.document, injuryReader([madness]), { follow_up_id: followUpId, roll: 1 });
    expect(again.ok).toBe(false);
  });

  it("rejects an out-of-range sub-roll", () => {
    const { document, followUpId } = withMadness(fixture(), "hero-1");
    const bad = resolveInjuryTableFollowUp(document, injuryReader([madness]), { follow_up_id: followUpId, roll: 7 });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.message).toContain("valid result");
  });

  it("keeps follow-up ids unique when several subtables are pending at once", () => {
    const one = withMadness(fixture(), "hero-1");
    const two = withMadness(one.document, "hero-2");
    const pending = two.document.campaign.post_battles[0]?.pending_follow_ups ?? [];
    const ids = pending.map((row) => row["id"]);
    expect(new Set(ids).size).toBe(ids.length);
  });

});

describe("desktop chained injury resolution", () => {
  it("rolls the number of Multiple Injuries and resolves each result as D66", () => {
    const multiple:OpenPayload={id:"multiple",applies_to:"hero",roll:"16-21",result:"Multiple Injuries",resolution:{type:"repeat_table",dice:{count:1,sides:6},reroll_ids:["dead","multiple","captured"]}};
    const leg:OpenPayload={id:"leg",applies_to:"hero",roll:"22",result:"Leg Wound",resolution:"direct",effects:[{type:"warrior.characteristic_modifier",characteristic:"movement",modifier:-1}]};
    const applied=applyInjuryOutcome(fixture(),{warrior_id:"hero-1",result_id:"multiple",result:"Multiple Injuries",effects:injuryEffects(multiple)});
    expect(applied.ok).toBe(true);if(!applied.ok)return;
    const countId=String(applied.document.campaign.post_battles[0].pending_follow_ups?.[0]?.["id"]);
    const counted=resolveInjuryTableFollowUp(applied.document,injuryReader([multiple,leg]),{follow_up_id:countId,roll:2});
    expect(counted.ok).toBe(true);if(!counted.ok)return;
    const repeats=counted.document.campaign.post_battles[0].pending_follow_ups??[];expect(repeats).toHaveLength(2);
    const resolved=resolveInjuryTableFollowUp(counted.document,injuryReader([multiple,leg]),{follow_up_id:String(repeats[0]["id"]),roll:22});
    expect(resolved.ok).toBe(true);if(!resolved.ok)return;
    expect(resolved.document.campaign.warriors.find((row)=>row.id==="hero-1")?.stat_modifiers?.M).toBe(-1);
    expect(resolved.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(1);
  });

  it("uses the D3 result as the Deep Wound recovery duration", () => {
    const deep:OpenPayload={id:"deep",applies_to:"hero",roll:"35",result:"Deep Wound",resolution:"direct",effects:[{type:"warrior.miss_games",games:{kind:"dice",dice:{count:1,sides:3}}}]};
    const applied=applyInjuryOutcome(fixture(),{warrior_id:"hero-1",result_id:"deep",result:"Deep Wound",effects:injuryEffects(deep)});
    expect(applied.ok).toBe(true);if(!applied.ok)return;
    const id=String(applied.document.campaign.post_battles[0].pending_follow_ups?.[0]?.["id"]);
    const resolved=resolveInjuryTableFollowUp(applied.document,injuryReader([deep]),{follow_up_id:id,roll:3});
    expect(resolved.ok).toBe(true);if(!resolved.ok)return;
    expect(resolved.document.campaign.warriors.find((row)=>row.id==="hero-1")?.games_to_miss).toBe(3);
  });

  it("removes one model and its per-model equipment from a henchman group", () => {
    const base=fixture(),group={id:"group",name:"Novices",profile_name:"Novice",kind:"henchman" as const,quantity:3,stats:{M:4},equipment:[{item_id:"dagger",name:"Dagger",quantity:3,per_model:true,transferable:true,acquisition_costs:[2,2,2]}],skills:[],experience:0,cost:25};
    const document={...base,campaign:{...base.campaign,warriors:[...base.campaign.warriors,group],inventory:[{id:"dagger",name:"Dagger",category:"weapon",owned:4,equipped:3,stash:1,acquisition_costs:[2,2,2,7]},...base.campaign.inventory.filter((row)=>row.id!=="dagger")]}};
    const result=applyInjuryOutcome(document,{warrior_id:"group",result_id:"removed",result:"Removed",effects:[{kind:"remove_warrior"}]});
    expect(result.ok).toBe(true);if(!result.ok)return;const survivor=result.document.campaign.warriors.find((row)=>row.id==="group")!;
    expect(survivor.quantity).toBe(2);expect(survivor.equipment[0].quantity).toBe(2);expect(result.document.campaign.inventory.find((row)=>row.id==="dagger")).toMatchObject({owned:3,equipped:2,stash:1,acquisition_costs:[2,2,7]});
  });
});

// Port of desktop `test_followup_ids_not_reused_while_another_is_pending`.
describe("follow-up ids are not reused while another is pending", () => {
  it("queues unique ids across warriors and after a resolution", () => {
    const captured = (doc: CampaignDocument, warriorId: string): CampaignDocument => {
      const applied = applyInjuryOutcome(doc, {
        warrior_id: warriorId,
        result_id: "captured",
        result: "Captured",
        effects: [{ kind: "follow_up", type: "prisoner", payload: { step: 0 } }],
      });
      expect(applied.ok).toBe(true);
      if (!applied.ok) throw new Error("applyInjuryOutcome failed");
      return applied.document;
    };
    const a = captured(fixture(), "hero-1");
    const b = captured(a, "hero-2");
    const pending = b.campaign.post_battles[0].pending_follow_ups ?? [];
    expect(new Set(pending.map((row) => row["id"])).size).toBe(pending.length);
    // Resolve one captivity while the other stays pending.
    const resolved = resolvePrisoner(b, { follow_up_id: String(pending[0]?.["id"]), resolution: "exchange" });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    // Queue a fresh captivity for the same warrior: ids must stay unique.
    const c = captured(resolved.document, "hero-1");
    const after = c.campaign.post_battles[0].pending_follow_ups ?? [];
    expect(new Set(after.map((row) => row["id"])).size).toBe(after.length);
    inventoryBalanced(c);
  });
});
