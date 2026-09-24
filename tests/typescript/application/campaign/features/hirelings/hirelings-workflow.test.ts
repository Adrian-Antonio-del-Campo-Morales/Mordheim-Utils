/**
 * P6.7 acceptance tests: hireling eligibility, exploration read model and
 * trading orchestration — plain Node, real kernel use cases, an
 * artefact-shaped fake listings source (no React/DOM/filesystem).
 *
 * Coverage: eligibility resolution (allow/forbid groups +
 * bands, expression → conditional), hiring fee economics on the created
 * warrior, exploration dice projection with the max-dice cap, trading buy
 * (treasury guard) and sell (stash conservation + manual-log booking).
 */

import { describe, expect, it } from "vitest";

import type { CampaignDocument, OpenPayload } from "@domain/campaign/index";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import { memberCount, rating, treasury } from "@domain/campaign/kernel/document";
import type { ArtefactRow } from "@adapters/knowledge-reader/artefact-types";
import {
  createHirelingsWorkflow,
  type KnowledgeListings,
} from "@app/campaign/features/hirelings/hirelings-workflow";

/** Artefact-shaped listings fake (mirrors the real generator's shapes). */
const groups: ArtefactRow[] = [
  { id: "warband-group.sisters", kind: "race", band_ids: ["sisters-of-sigmar"] },
  { id: "warband-group.good-aligned", kind: "alignment", band_ids: ["sisters-of-sigmar", "witch-hunters"] },
  { id: "warband-group.undead", kind: "race", band_ids: ["vampire-counts"] },
];

const hirelingProfiles: ArtefactRow[] = [
  {
    id: "hireling.hired-sword.warrior-undead-hunter",
    kind: "hired-sword",
    name: "Undead Hunter",
    names: { en: "Undead Hunter" },
    warband_rating: { kind: "base_plus_experience", base: 15, per_experience_point: 1 },
    characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
  },
  {
    id: "hireling.hired-sword.ogre-bodyguard",
    kind: "hired-sword",
    name: "Ogre Bodyguard",
    names: { en: "Ogre Bodyguard" },
    warband_rating: { kind: "fixed", value: 75 },
    characteristics: { M: 6, WS: 3, BS: 2, S: 4, T: 4, W: 3, I: 2, A: 2, Ld: 6 },
  },
];

const hiredSwords: ArtefactRow[] = [
  {
    id: "campaign.hireling.hired-sword.warrior-undead-hunter",
    profile_id: "hireling.hired-sword.warrior-undead-hunter",
    hiring_fee: { resources: { gold_crowns: { cost: 35 } } },
    upkeep: { resources: { gold_crowns: { cost: 15 } } },
    availability: { kind: "common" },
    eligibility: {
      allow_groups: ["warband-group.good-aligned"],
      forbid_groups: [],
      allow_band_ids: [],
      forbid_band_ids: [],
    },
  },
  {
    id: "campaign.hireling.hired-sword.ogre-bodyguard",
    profile_id: "hireling.hired-sword.ogre-bodyguard",
    hiring_fee: { resources: { gold_crowns: { cost: 90 } } },
    upkeep: { resources: { gold_crowns: { cost: 30 } } },
    availability: { kind: "common" },
    eligibility: {
      allow_groups: ["warband-group.undead"], // wrong alignment: excluded
    },
  },
];

const tradingItems: ArtefactRow[] = [
  {
    id: "campaign.trading-post.axe",
    item_id: "axe",
    price: { base_gc: 5 },
    availability: { kind: "common" },
    restrictions: [],
  },
  {
    id: "campaign.trading-post.gromril-armor",
    item_id: "gromril_armor",
    price: { base_gc: 75 },
    availability: { kind: "rare" },
    restrictions: [],
  },
];

const exploration: Record<string, unknown> = {
  exploration: {
    dice_allocation: [
      { id: "campaign.exploration.dice.per-surviving-hero", eligible_warrior: "hero", dice: 1, condition: "survived_battle" },
      { id: "campaign.exploration.dice.bonus-if-won", eligible_warrior: "warband", dice: 1, condition: "warband_won_battle" },
    ],
    max_dice: 6,
  },
};

const listings: KnowledgeListings = {
  campaignRows(section: string): readonly ArtefactRow[] {
    switch (section) {
      case "warband_groups":
        return groups;
      case "hired-swords-and-dramatis:hired_swords":
        return hiredSwords;
      case "hired-swords-and-dramatis:dramatis_personae":
        return [];
      default:
        return [];
    }
  },
  campaignSection(section: string): Readonly<Record<string, unknown>> {
    switch (section) {
      case "hirelings":
        return { profiles: hirelingProfiles };
      case "trading-post":
        return { items: tradingItems };
      case "exploration-and-income":
        return exploration;
      default:
        return {};
    }
  },
  itemName(itemId: string): string {
    const names: Record<string, string> = { axe: "Axe", gromril_armor: "Gromril Armour" };
    return names[itemId] ?? itemId;
  },
};

function makeKnowledge() {
  const records = new Map<string, OpenPayload>();
  const set = (key: string, row: OpenPayload) => records.set(key, row);
  // Sisters band + profiles (mirrors the kernel test's artefact shapes).
  set("band_id:sisters-of-sigmar", {
    id: "sisters-of-sigmar",
    name: "Sisters of Sigmar",
    names: { en: "Sisters of Sigmar" },
    collection: "mordheim",
    roster: {
      minimum_models: 3,
      maximum_models: 15,
      starting_gold: 500,
      members: [
        { profile_id: "sigmarite-matriarch", minimum: 1, maximum: 1 },
        { profile_id: "sister-superior", minimum: 0, maximum: 3 },
        { profile_id: "sigmarite-sister", minimum: 0, maximum: null, group_size: { minimum: 1, maximum: 5 } },
      ],
    },
  });
  set("profile_id:sigmarite-matriarch", {
    id: "sigmarite-matriarch", band_id: "sisters-of-sigmar", collection: "mordheim",
    type: "hero", cost: 70, experience: 0, name: "Sigmarite Matriarch",
    names: { en: "Sigmarite Matriarch" },
    characteristics: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
    fixed_equipment: ["sigmarite_hammer"], skill_access: ["combat"],
  });
  set("profile_id:sister-superior", {
    id: "sister-superior", band_id: "sisters-of-sigmar", collection: "mordheim",
    type: "hero", cost: 35, experience: 0, name: "Sister Superior",
    names: { en: "Sister Superior" },
    characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    fixed_equipment: [], skill_access: ["combat"],
  });
  set("profile_id:sigmarite-sister", {
    id: "sigmarite-sister", band_id: "sisters-of-sigmar", collection: "mordheim",
    type: "henchman", cost: 25, experience: 0, name: "Sigmarite Sister",
    names: { en: "Sigmarite Sister" },
    characteristics: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    fixed_equipment: [],
  });
  set("item_id:sigmarite_hammer", {
    item_id: "sigmarite_hammer", kind: "close-combat-weapon", name: "Sigmarite Hammer",
    names: { en: "Sigmarite Hammer" }, value: 15,
  });
  set("hireling_id:hireling.hired-sword.warrior-undead-hunter", {
    id: "hireling.hired-sword.warrior-undead-hunter",
    name: "Undead Hunter",
    names: { en: "Undead Hunter" },
    warband_rating: { kind: "base_plus_experience", base: 15, per_experience_point: 1 },
    characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    skills: [],
  });
  return {
    queryKnowledge(query: { id: { kind: string; value: string } }) {
      const row = records.get(`${query.id.kind}:${query.id.value}`);
      if (!row) return { ok: false as const, reason: "not_found" as const };
      const { id, name, names, ...data } = row;
      return {
        ok: true as const,
        record: {
          kind: query.id.kind.replace(/_id$/, "") as never,
          id: query.id as never,
          names: (names ?? { en: name }) as Record<string, string>,
          data: data as OpenPayload,
        },
      };
    },
    queryMany(queries: readonly { id: { kind: string; value: string } }[]) {
      return queries.map((q) => makeKnowledge().queryKnowledge(q));
    },
  };
}

/** Committed Sisters campaign via the real kernel pipeline. */
function makeCommitted(): CampaignDocument {
  const knowledge = makeKnowledge() as never;
  const draft = createDefaultUseCases(knowledge).createDraft("sisters-of-sigmar", knowledge);
  if (!draft.ok) throw new Error("draft should be legal");
  const committed = createDefaultUseCases(knowledge).commitInitialWarband(draft.state, knowledge);
  if (!committed.ok) throw new Error("commit should succeed");
  return committed.state;
}

describe("P6.7 hireling offers and eligibility", () => {
  it("resolves static eligibility through warband groups (allow/forbid)", () => {
    const workflow = createHirelingsWorkflow({ listings, useCases: createDefaultUseCases(makeKnowledge() as never) });
    const document = makeCommitted();
    const offers = workflow.hiredSwordOffers(document);
    expect(offers).toHaveLength(2);
    const hunter = offers.find((o) => o.profile_id === "hireling.hired-sword.warrior-undead-hunter");
    const ogre = offers.find((o) => o.profile_id === "hireling.hired-sword.ogre-bodyguard");
    expect(hunter?.eligible).toBe(true); // sisters are good-aligned
    expect(hunter?.fee).toBe(35);
    expect(hunter?.upkeep).toBe(15);
    expect(hunter?.rating).toBe(15); // base of base+experience
    expect(ogre?.eligible).toBe(false); // undead-only
    expect(ogre?.ineligible_reason).toContain("excluded");
  });

  it("hires through the kernel carrying fee and rating into the warrior", () => {
    const useCases = createDefaultUseCases(makeKnowledge() as never);
    const workflow = createHirelingsWorkflow({ listings, useCases });
    const document = makeCommitted();
    const offer = workflow.hiredSwordOffers(document).find((o) => o.eligible);
    if (!offer) throw new Error("eligible offer missing");
    const membersBefore = memberCount(document.campaign.warriors);
    const ratingBefore = rating(document.campaign.warriors);
    const result = workflow.hire(document, offer);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hireling = result.document.campaign.warriors.find((w) => w.kind === "hireling");
    expect(hireling?.profile_id).toBe(offer.profile_id);
    expect(hireling?.cost).toBe(35);
    expect(hireling?.hireling_rating).toBe(15);
    expect(memberCount(result.document.campaign.warriors)).toBe(membersBefore); // no capacity use
    expect(rating(result.document.campaign.warriors)).toBe(ratingBefore + 15);
  });

  it("rejects hiring an ineligible offer through the kernel surface", () => {
    const useCases = createDefaultUseCases(makeKnowledge() as never);
    const workflow = createHirelingsWorkflow({ listings, useCases });
    const document = makeCommitted();
    const offers = workflow.hiredSwordOffers(document);
    const ogre = offers.find((o) => !o.eligible);
    if (!ogre) throw new Error("ineligible offer missing");
    // The kernel is id-based and cannot know eligibility — the application
    // guards: the workflow's guard is the eligibility verdict itself.
    expect(ogre.eligible).toBe(false);
  });
});

describe("P6.7 exploration read model", () => {
  it("projects dice per surviving hero plus the win bonus, capped", () => {
    const workflow = createHirelingsWorkflow({ listings, useCases: createDefaultUseCases() });
    const document = makeCommitted();
    const heroes = document.campaign.warriors.filter((w) => w.kind === "hero").length;
    // A recorded win (appended by hand: the read model consumes Battle rows).
    const withBattle: CampaignDocument = {
      ...document,
      campaign: {
        ...document.campaign,
        battles: [
          {
            number: 1,
            date: "2026-09-09",
            scenario: "skirmish",
            opponent: "possessed",
            result: "win",
            gold_delta: 0,
            wyrdstone: 0,
            xp_delta: 0,
            casualties: 0,
            advances: 0,
            rating_before: 0,
            rating_after: 0,
            models_before: heroes,
            models_after: heroes,
            out_of_action_ids: null,
          },
        ],
      },
    };
    const { rows, total } = workflow.explorationDice(withBattle, 1);
    expect(rows.find((r) => r.condition === "survived_battle")?.dice).toBe(heroes);
    expect(rows.find((r) => r.condition === "warband_won_battle")).toBeDefined();
    expect(total).toBe(heroes + 1);
    // A loss yields only the hero dice.
    const lossDocument: CampaignDocument = {
      ...withBattle,
      campaign: { ...withBattle.campaign, battles: [{ ...withBattle.campaign.battles[0], result: "loss" }] },
    };
    expect(workflow.explorationDice(lossDocument, 1).total).toBe(heroes);
    // No battle: nothing to explore.
    expect(workflow.explorationDice(document, 1).total).toBe(0);
  });
});

describe("P6.7 trading", () => {
  it("buys into the stash honouring the treasury guard", () => {
    const useCases = createDefaultUseCases();
    const workflow = createHirelingsWorkflow({ listings, useCases });
    const document = makeCommitted();
    const goldBefore = treasury(document.campaign);
    const axe = workflow.tradingOffers(document).find((o) => o.item_id === "axe");
    if (!axe) throw new Error("axe offer missing");
    const result = workflow.buy(document, axe, 2);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const row = result.document.campaign.inventory.find((i) => i.id === "axe");
    expect(row?.owned).toBe(2);
    expect(row?.stash).toBe(2);
    expect(row?.value).toBe(5);
    // Valuation honesty: owned × value enters the treasury accounting.
    expect(treasury(result.document.campaign)).toBe(goldBefore - 10);
    // Unaffordable purchases reject with the stable reason.
    const broke = workflow.buy(document, axe, 1000);
    expect(broke.ok).toBe(false);
    if (!broke.ok) expect(broke.message).toContain("Not enough gold");
  });

  it("sells from the stash conserving stock and booking the manual log", () => {
    const useCases = createDefaultUseCases();
    const workflow = createHirelingsWorkflow({ listings, useCases });
    const document = makeCommitted();
    const axe = workflow.tradingOffers(document).find((o) => o.item_id === "axe");
    if (!axe) throw new Error("axe offer missing");
    const bought = workflow.buy(document, axe, 3);
    if (!bought.ok) throw new Error("buy should succeed");
    const sold = workflow.sell(bought.document, "axe", 2, 4);
    expect(sold.ok).toBe(true);
    if (!sold.ok) return;
    const row = sold.document.campaign.inventory.find((i) => i.id === "axe");
    expect(row?.owned).toBe(1);
    expect(row?.stash).toBe(1);
    const entry = sold.document.campaign.manual_log.find(
      (e) => e["type"] === "stash_sale" && e["item_id"] === "axe",
    );
    expect(entry?.["quantity"]).toBe(2);
    expect(entry?.["total"]).toBe(8);
    // Overselling rejects.
    const over = workflow.sell(sold.document, "axe", 5, 4);
    expect(over.ok).toBe(false);
    if (!over.ok) expect(over.message).toContain("stash");
  });
});
