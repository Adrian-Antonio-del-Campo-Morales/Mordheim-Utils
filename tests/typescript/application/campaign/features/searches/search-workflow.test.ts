/**
 * Parity port of the desktop rare-item search behaviour in
 * `test_gui_interaction_regressions.py` (`test_rare_search_cannot_be_consumed_twice`,
 * `test_failed_rare_purchase_keeps_search_available`) and the engine resolve
 * flow. Exercised against the web `resolveRareSearch` / `buyRareSearch` seams
 * in `search-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";

import { assignDramatisSearch, assignRareSearch, buyRareSearch, hireDramatisSearch, resolveDramatisSearch, resolveRareSearch, upgradeRareSearch } from "@app/campaign/features/searches/search-workflow";

const reader: any = {
  campaignSection(section: string) {
    if (section === "trading-post") {
      return {
        items: [
          { item_id: "ring_of_the_recluse", availability: { kind: "rare", rarity: 7 }, price: { base_gc: 20 } },
          { item_id: "gromril_weapon", availability: { kind: "rare", rarity: 8 }, price: { base_gc: 0, multiplier: 2 } },
        ],
      };
    }
    if (section === "hired-swords-and-dramatis") {
      return {
        dramatis_personae: [
          {
            profile_id: "hireling.dramatis.william",
            availability: { procedure_id: "campaign.hireling.availability.dramatis-search" },
            eligibility: {},
            hiring_fee: { resources: { gold_crowns: { cost: 30 } } },
            upkeep: { resources: { gold_crowns: { cost: 5 } } },
          },
          {
            profile_id: "hireling.dramatis.maximilian",
            availability: { procedure_id: "campaign.hireling.availability.dramatis-search" },
            eligibility: { forbid_band_ids: ["middenheim"] },
            hiring_fee: { resources: { gold_crowns: { cost: 40 } } },
          },
        ],
      };
    }
    return undefined;
  },
  campaignRows() {
    return [];
  },
  itemName(id: string) {
    if (id === "ring_of_the_recluse") return "Ring of the Recluse";
    if (id === "gromril_weapon") return "Gromril Weapon";
    if (id === "hireling.dramatis.william") return "William";
    if (id === "hireling.dramatis.maximilian") return "Maximilian";
    return id;
  },
};

function makeDoc(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Search", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65, special_rules: [] },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 6, completed_steps: [0, 1, 2, 3, 4, 5], review_open: false,
        pending_follow_ups: [], gold_delta: 0, wyrdstone_delta: 0, wyrdstone_sold: 0,
        experience_applied: false, pending_advances: [],
        step_state: { veterans: { resolved: true } }, sale_resolved: false, equipment_obligations: [], acknowledgements: {}, event_log: [],
        searches: {
          "hero-1": { kind: "rare", target_id: "rare:ring_of_the_recluse", item_id: "ring_of_the_recluse", label: "Ring of the Recluse", modifiers: 0, hero_id: "hero-1" },
        },
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("resolveRareSearch (rare-item 2D6 roll)", () => {
  it("succeeds when the roll plus modifiers meets the rarity", () => {
    const result = resolveRareSearch(makeDoc(), reader, { hero_id: "hero-1", dice: [4, 4] });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const search = result.document.campaign.post_battles[0].searches?.["hero-1"];
    expect(search?.success).toBe(true);
    expect(search?.roll_total).toBe(8);
  });

  it("fails when the roll is below the rarity", () => {
    const result = resolveRareSearch(makeDoc(), reader, { hero_id: "hero-1", dice: [1, 1] });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].searches?.["hero-1"]?.success).toBe(false);
  });

  it("rejects a non-2D6 roll and a second roll", () => {
    const bad = resolveRareSearch(makeDoc(), reader, { hero_id: "hero-1", dice: [4] });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.message).toContain("exactly 2D6");
    const doc = makeDoc();
    const first = resolveRareSearch(doc, reader, { hero_id: "hero-1", dice: [4, 4] });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const again = resolveRareSearch(first.document, reader, { hero_id: "hero-1", dice: [3, 3] });
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.message).toContain("already resolved");
  });
});

describe("buyRareSearch (rare-item purchase)", () => {
  it("buys the found item, marks the search used and logs it", () => {
    const doc = makeDoc();
    const resolved = resolveRareSearch(doc, reader, { hero_id: "hero-1", dice: [4, 4] });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    const result = buyRareSearch(resolved.document, reader, { hero_id: "hero-1" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const item = result.document.campaign.inventory.find((row) => row.id === "ring_of_the_recluse");
    expect(item).toBeDefined();
    expect(item?.owned).toBe(1);
    expect(item?.stash).toBe(1);
    expect(item?.rarity).toBe("Rare 7");
    expect(result.document.campaign.post_battles[0].searches?.["hero-1"]?.used).toBe(true);
    expect(result.document.campaign.post_battles[0].gold_delta).toBe(-20);
  });

  it("cannot be consumed twice", () => {
    const doc = makeDoc();
    const resolved = resolveRareSearch(doc, reader, { hero_id: "hero-1", dice: [4, 4] });
    if (!resolved.ok) return;
    const first = buyRareSearch(resolved.document, reader, { hero_id: "hero-1" });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const second = buyRareSearch(first.document, reader, { hero_id: "hero-1" });
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.message).toContain("not an unused success");
  });

  it("keeps the search available when the purchase fails for lack of gold", () => {
    const doc = makeDoc();
    const resolved = resolveRareSearch(doc, reader, { hero_id: "hero-1", dice: [4, 4] });
    if (!resolved.ok) return;
    const before = resolved.document;
    (before.campaign.states[0] as { gold: number }).gold = 0;
    const result = buyRareSearch(before, reader, { hero_id: "hero-1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Not enough gold");
    // The input document is untouched, so the search remains available.
    expect(before.campaign.post_battles[0].searches?.["hero-1"]?.used).toBeFalsy();
  });

  it("rejects buying a search that did not succeed", () => {
    const doc = makeDoc();
    const resolved = resolveRareSearch(doc, reader, { hero_id: "hero-1", dice: [1, 1] });
    if (!resolved.ok) return;
    const result = buyRareSearch(resolved.document, reader, { hero_id: "hero-1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("not an unused success");
  });
});

/** A pending search on a rare weapon-upgrade offer with a stashed base weapon. */
function makeUpgradeDoc(baseCategory = "weapon", baseValue = 10): CampaignDocument {
  const doc = makeDoc();
  (doc.campaign.post_battles[0] as unknown as { searches: Record<string, unknown> }).searches = {
    "hero-1": { kind: "rare", target_id: "rare:gromril_weapon", item_id: "gromril_weapon", label: "Gromril Weapon", modifiers: 0, hero_id: "hero-1", success: true, used: false },
  };
  (doc.campaign as unknown as { inventory: unknown[] }).inventory = [
    { id: "axe", name: "Axe", category: baseCategory, owned: 1, equipped: 0, stash: 1, value: baseValue },
  ];
  return doc;
}

describe("upgradeRareSearch (rare-item upgrade)", () => {
  it("consumes the base weapon and adds the upgraded record at base × multiplier", () => {
    const result = upgradeRareSearch(makeUpgradeDoc(), reader, { hero_id: "hero-1", base_item_id: "axe" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const inventory = result.document.campaign.inventory;
    expect(inventory.find((row) => row.id === "axe")).toBeUndefined();
    const upgraded = inventory.find((row) => row.id === "gromril_weapon:axe");
    expect(upgraded?.value).toBe(30); // base 10 + 10 × 2
    expect(upgraded?.rarity).toBe("Rare 8");
    expect(upgraded?.special_rules).toContain("Gromril Weapon");
    expect(result.document.campaign.post_battles[0].searches?.["hero-1"]?.used).toBe(true);
    expect(result.document.campaign.post_battles[0].gold_delta).toBe(-20);
  });

  it("only weapons can receive the upgrade", () => {
    const result = upgradeRareSearch(makeUpgradeDoc("armour"), reader, { hero_id: "hero-1", base_item_id: "axe" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Only weapons");
  });

  it("requires a stashed base weapon", () => {
    const result = upgradeRareSearch(makeUpgradeDoc(), reader, { hero_id: "hero-1", base_item_id: "sword" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("available base weapon");
  });

  it("rejects the upgrade when gold is short", () => {
    const doc = makeUpgradeDoc();
    (doc.campaign.states[0] as { gold: number }).gold = 0;
    const result = upgradeRareSearch(doc, reader, { hero_id: "hero-1", base_item_id: "axe" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Not enough gold");
  });

  it("rejects upgrading a weapon that already has the upgrade", () => {
    const doc = makeUpgradeDoc();
    (doc.campaign.inventory as unknown as { special_rules: string[] }[])[0].special_rules = ["Gromril Weapon"];
    const result = upgradeRareSearch(doc, reader, { hero_id: "hero-1", base_item_id: "axe" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("already has this upgrade");
  });

  it("rejects an upgrade offer without a multiplier", () => {
    const doc = makeUpgradeDoc();
    (doc.campaign.post_battles[0] as unknown as { searches: Record<string, unknown> }).searches = {
      "hero-1": { kind: "rare", item_id: "ring_of_the_recluse", success: true, used: false },
    };
    const result = upgradeRareSearch(doc, reader, { hero_id: "hero-1", base_item_id: "axe" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("available base weapon");
  });
});

/** A pending post-battle with no search assigned yet. */
function assignDoc(): CampaignDocument {
  const doc = makeDoc();
  (doc.campaign.post_battles[0] as unknown as { searches: Record<string, unknown> }).searches = {};
  return doc;
}

describe("assignRareSearch / assignDramatisSearch (search assignment gates)", () => {
  it("assigns a rare-item search to a Hero", () => {
    const result = assignRareSearch(assignDoc(), reader, { hero_id: "hero-1", item_id: "ring_of_the_recluse" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const search = result.document.campaign.post_battles[0].searches?.["hero-1"];
    expect(search).toMatchObject({ kind: "rare", item_id: "ring_of_the_recluse", target_id: "rare:ring_of_the_recluse", label: "Ring of the Recluse" });
  });

  it("grants +1 when the Hero has the locating-rare-items rule and clears on null", () => {
    const doc = assignDoc();
    (doc.campaign.warriors[0] as unknown as { special_rules: string[] }).special_rules = ["+1 to rolls for locating rare items"];
    const assigned = assignRareSearch(doc, reader, { hero_id: "hero-1", item_id: "ring_of_the_recluse" });
    expect(assigned.ok).toBe(true);
    if (!assigned.ok) return;
    expect(assigned.document.campaign.post_battles[0].searches?.["hero-1"]?.modifiers).toBe(1);
    const cleared = assignRareSearch(assigned.document, reader, { hero_id: "hero-1", item_id: null });
    expect(cleared.ok).toBe(true);
    if (!cleared.ok) return;
    expect(cleared.document.campaign.post_battles[0].searches?.["hero-1"]).toBeUndefined();
  });

  it("rejects a non-Hero searcher and an unknown rare item", () => {
    const doc = assignDoc();
    (doc.campaign.warriors[0] as unknown as { kind: string }).kind = "henchman";
    const notHero = assignRareSearch(doc, reader, { hero_id: "hero-1", item_id: "ring_of_the_recluse" });
    expect(notHero.ok).toBe(false);
    if (!notHero.ok) expect(notHero.message).toContain("Only a current Hero");
    const unknown = assignRareSearch(assignDoc(), reader, { hero_id: "hero-1", item_id: "nope" });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.message).toContain("Unknown rare");
  });

  it("blocks assignment until veterans are resolved", () => {
    const doc = assignDoc();
    (doc.campaign.post_battles[0] as unknown as { step_state: Record<string, unknown> }).step_state = { veterans: { resolved: false } };
    const result = assignRareSearch(doc, reader, { hero_id: "hero-1", item_id: "ring_of_the_recluse" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("veteran availability");
  });

  it("assigns an eligible Dramatis Persona and rejects ineligible or unknown ones", () => {
    const assigned = assignDramatisSearch(assignDoc(), reader, { hero_id: "hero-1", profile_id: "hireling.dramatis.william" });
    expect(assigned.ok).toBe(true);
    if (!assigned.ok) return;
    expect(assigned.document.campaign.post_battles[0].searches?.["hero-1"]).toMatchObject({ kind: "dramatis", profile_id: "hireling.dramatis.william" });
    // forbid_band_ids includes middenheim.
    const ineligible = assignDramatisSearch(assignDoc(), reader, { hero_id: "hero-1", profile_id: "hireling.dramatis.maximilian" });
    expect(ineligible.ok).toBe(false);
    if (!ineligible.ok) expect(ineligible.message).toContain("eligibility");
    const unknown = assignDramatisSearch(assignDoc(), reader, { hero_id: "hero-1", profile_id: "nope" });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.message).toContain("Unknown Dramatis Persona");
  });
});

describe("resolveDramatisSearch (D6 search roll)", () => {
  function dramatisDoc(): CampaignDocument {
    const assigned = assignDramatisSearch(assignDoc(), reader, { hero_id: "hero-1", profile_id: "hireling.dramatis.william" });
    if (!assigned.ok) throw new Error(assigned.message);
    return assigned.document;
  }

  it("resolves the search with one D6 and leaves it unused", () => {
    const result = resolveDramatisSearch(dramatisDoc(), { hero_id: "hero-1", die: 4 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].searches?.["hero-1"]).toMatchObject({ success: true, used: false, roll_total: 4, dice: [4] });
  });

  it("requires an assigned Dramatis search", () => {
    const result = resolveDramatisSearch(assignDoc(), { hero_id: "hero-1", die: 4 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Assign a Dramatis search first");
  });

  it("rejects a second roll and an out-of-range die", () => {
    const first = resolveDramatisSearch(dramatisDoc(), { hero_id: "hero-1", die: 4 });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const again = resolveDramatisSearch(first.document, { hero_id: "hero-1", die: 3 });
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.message).toContain("already resolved");
    const bad = resolveDramatisSearch(dramatisDoc(), { hero_id: "hero-1", die: 7 });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.message).toContain("one D6");
  });
});

/** Reader fake for the dramatis-hire flow (listings + hireling profile records). */
const dramatisHireReader: any = {
  campaignSection(section: string) {
    if (section === "hired-swords-and-dramatis") {
      return {
        dramatis_personae: [
          {
            profile_id: "hireling.dramatis.william",
            availability: { procedure_id: "campaign.hireling.availability.dramatis-search" },
            eligibility: {},
            hiring_fee: { resources: { gold_crowns: { cost: 30 } } },
            upkeep: { resources: { gold_crowns: { cost: 5 } } },
          },
          {
            profile_id: "hireling.dramatis.nofee",
            availability: { procedure_id: "campaign.hireling.availability.dramatis-search" },
            eligibility: {},
          },
        ],
      };
    }
    if (section === "hirelings") return { rules: [] };
    return undefined;
  },
  campaignRows() {
    return [];
  },
  itemName(id: string) {
    return id === "hireling.dramatis.william" ? "William" : id;
  },
  queryKnowledge(query: { id: { kind: string; value: string } }) {
    if (query.id.kind === "hireling_id" && query.id.value === "hireling.dramatis.william") {
      return {
        ok: true,
        record: {
          names: { en: "William" },
          data: { warband_rating: { kind: "fixed", value: 30 }, characteristics: { M: 4, WS: 4 }, skills: [], rule_ids: [] },
        },
      };
    }
    return { ok: false, reason: "not_found" };
  },
};

/** A pending post-battle whose dramatis search succeeded and is unused. */
function hireDoc(profileId = "hireling.dramatis.william"): CampaignDocument {
  const doc = assignDoc();
  (doc.campaign.post_battles[0] as unknown as { searches: Record<string, unknown> }).searches = {
    "hero-1": { kind: "dramatis", profile_id: profileId, success: true, used: false, dice: [4], hero_id: "hero-1" },
  };
  return doc;
}

describe("hireDramatisSearch (dramatis hire)", () => {
  it("hires the persona, charges its fee, marks the search used and logs it", () => {
    const result = hireDramatisSearch(hireDoc(), dramatisHireReader, { hero_id: "hero-1" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hired = result.document.campaign.warriors.find((w) => w.profile_id === "hireling.dramatis.william");
    expect(hired?.kind).toBe("hireling");
    expect(hired?.cost).toBe(30);
    const post = result.document.campaign.post_battles[0];
    expect(post.searches?.["hero-1"]?.used).toBe(true);
    expect(post.gold_delta).toBe(-30);
    expect(post.event_log?.at(-1)).toMatchObject({ type: "hire", profile_id: "hireling.dramatis.william" });
  });

  it("rejects a search that is not an unused success", () => {
    const doc = hireDoc();
    (doc.campaign.post_battles[0] as unknown as { searches: Record<string, unknown> }).searches = {
      "hero-1": { kind: "dramatis", profile_id: "hireling.dramatis.william", success: true, used: true },
    };
    const result = hireDramatisSearch(doc, dramatisHireReader, { hero_id: "hero-1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("not an unused success");
  });

  it("rejects an unfunded fee", () => {
    const doc = hireDoc();
    (doc.campaign.states[0] as { gold: number }).gold = 0;
    const result = hireDramatisSearch(doc, dramatisHireReader, { hero_id: "hero-1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Not enough gc: 30 needed, 0 available");
  });

  it("rejects a persona that declares no payable fee", () => {
    const result = hireDramatisSearch(hireDoc("hireling.dramatis.nofee"), dramatisHireReader, { hero_id: "hero-1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("no payable hiring fee");
  });
});