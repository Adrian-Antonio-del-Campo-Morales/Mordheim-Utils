/**
 * Parity port of the desktop variable-fee and conditional-hire flows in
 * `test_variable_prices_and_restrictions.py`
 * (`test_variable_hiring_fee_is_parsed_and_needs_a_roll`,
 * `test_variable_hiring_fee_charges_base_plus_roll`) and
 * `test_post_battle_engine.py` (`test_hire_conditional_requires_acceptance_roll`).
 * Exercises the web `createHirelingsWorkflow` offers/hire wiring over the kernel
 * `hireHireling` seam — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, OpenPayload } from "../../../../domain/campaign/index";
import { createDefaultUseCases } from "../../../../domain/campaign/kernel/default-usecases";

import { createHirelingsWorkflow, type KnowledgeListings } from "./hirelings-workflow";

const NINJA = "hireling.hired-sword.ninja";
const WILLIAM = "hireling.dramatis.william-schakestange-master-bard";
const WILLIAM_RULE = `${WILLIAM}.rule.campaign-eligibility`;

const listings: KnowledgeListings = {
  campaignRows(section: string) {
    if (section === "warband_groups") {
      return [{ id: "warband-group.good-aligned", kind: "alignment", band_ids: ["kislevites"] }];
    }
    if (section === "hired-swords-and-dramatis:hired_swords") {
      return [{ id: "campaign.hireling.ninja", profile_id: NINJA, hiring_fee: { resources: { gold_crowns: { cost: "70+3D6" } } }, eligibility: {} }];
    }
    if (section === "hired-swords-and-dramatis:dramatis_personae") {
      return [{ id: "campaign.hireling.william", profile_id: WILLIAM, hiring_fee: { resources: { gold_crowns: { cost: 30 } } }, eligibility: {} }];
    }
    return [];
  },
  campaignSection(section: string) {
    if (section === "hirelings") {
      return {
        profiles: [
          { id: NINJA, rule_ids: [] },
          { id: WILLIAM, rule_ids: [WILLIAM_RULE] },
        ],
        traits: { [WILLIAM]: ["human"] },
      };
    }
    return {};
  },
  itemName(id: string) {
    return id === NINJA ? "Ninja" : id === WILLIAM ? "William" : id;
  },
};

function makeKnowledge() {
  const records = new Map<string, OpenPayload>();
  records.set(`hireling_id:${NINJA}`, { id: NINJA, names: { en: "Ninja" }, warband_rating: { kind: "fixed", value: 40 }, characteristics: { M: 4, WS: 4 }, skills: [], rule_ids: [] });
  records.set(`hireling_id:${WILLIAM}`, { id: WILLIAM, names: { en: "William" }, warband_rating: { kind: "fixed", value: 30 }, characteristics: { M: 4, WS: 4 }, skills: [], rule_ids: [] });
  return {
    queryKnowledge(query: { id: { kind: string; value: string } }) {
      const row = records.get(`${query.id.kind}:${query.id.value}`);
      if (!row) return { ok: false as const, reason: "not_found" as const };
      const { id, names, ...data } = row;
      return { ok: true as const, record: { kind: query.id.kind.replace(/_id$/, "") as never, id: query.id as never, names: (names ?? {}) as Record<string, string>, data: data as OpenPayload } };
    },
    queryMany() {
      return [];
    },
  } as never;
}

function makeDoc(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Hire", warband_name: "Kislev", warband_type: "Kislevites", band_id: "kislevites", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [],
      battles: [],
      states: [{ number: 1, date: "2026-09-11", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

function workflow() {
  return createHirelingsWorkflow({ listings, useCases: createDefaultUseCases(makeKnowledge()) });
}

describe("hirelings workflow — variable fee (desktop fee_roll)", () => {
  it("surfaces the dice fee and requires a fee roll", () => {
    const wf = workflow();
    const offer = wf.hiredSwordOffers(makeDoc()).find((o) => o.profile_id === NINJA);
    expect(offer?.fee).toBeNull();
    expect(offer?.fee_base).toBe(70);
    expect(offer?.fee_dice).toEqual([3, 6]);

    const missing = wf.hire(makeDoc(), offer!);
    expect(missing.ok).toBe(false);
    if (!missing.ok) expect(missing.message).toContain("Roll");

    const below = wf.hire(makeDoc(), offer!, [], { feeRoll: 2 });
    expect(below.ok).toBe(false);

    const hired = wf.hire(makeDoc(), offer!, [], { feeRoll: 12 });
    expect(hired.ok).toBe(true);
    if (hired.ok) expect(hired.document.campaign.warriors.find((w) => w.profile_id === NINJA)?.cost).toBe(82);
  });
});

describe("hirelings workflow — conditional hire (desktop acceptance_roll)", () => {
  it("surfaces roll_ge and gates the hire on the acceptance roll", () => {
    const wf = workflow();
    const william = wf.dramatisPersonaeOffers(makeDoc()).find((o) => o.profile_id === WILLIAM);
    expect(william?.eligible).toBe(true);
    expect(william?.roll_ge).toBe(4);

    const missing = wf.hire(makeDoc(), william!);
    expect(missing.ok).toBe(false);
    if (!missing.ok) expect(missing.message).toContain("acceptance roll");

    const failed = wf.hire(makeDoc(), william!, [], { acceptanceRoll: 3 });
    expect(failed.ok).toBe(false);
    if (!failed.ok) expect(failed.message).toContain("failed");

    const hired = wf.hire(makeDoc(), william!, [], { acceptanceRoll: 5 });
    expect(hired.ok).toBe(true);
    if (hired.ok) expect(hired.document.campaign.warriors.some((w) => w.profile_id === WILLIAM)).toBe(true);
  });
});