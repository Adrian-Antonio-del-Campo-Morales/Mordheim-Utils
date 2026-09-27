/**
 * T09 construction and selection contracts.
 *
 * One case per mechanism over a fake KnowledgeReader shaped like the real
 * artefact (`equipment_access` rows, `equipment_forbids` tokens, band roster
 * slots, campaign catalogues), plus the persistence round-trip of the choices
 * the contracts let through. The domain decides; the interface only presents.
 *
 * Purity: plain Node, fake reader — no React, no DOM, no filesystem.
 */

import { describe, expect, it } from "vitest";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file/index";
import type { KnowledgeQuery } from "@domain/campaign/kernel/ports";
import type { CampaignDocument, KnowledgeReader, KnowledgeResult } from "@domain/campaign/kernel/usecases";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import { createDraft, warriorFromProfile } from "@domain/campaign/kernel/create-draft";
import { commitInitialWarband } from "@domain/campaign/kernel/commit-warband";
import type { Campaign, Warrior } from "@domain/campaign/kernel/state";
import {
  bandFactsOf,
  characteristicBoundIssueFor,
  characteristicIssuesOf,
  constructionIssuesOf,
  equipmentIssueFor,
  hiringDecisionFor,
  openClausesOf,
  pendingBindingsFor,
  profileExclusionFor,
  profileFactsOf,
  racialMaximumsOf,
  rosterIssuesOf,
  skillFactsOf,
  skillIssueFor,
} from "@domain/campaign/construction";
import { warbandVariants } from "@domain/campaign/band-variants";

/** Fake reader: rows keyed by `family:id`, with the adapter's additive listings. */
function makeReader(
  rows: Record<string, Record<string, unknown>>,
  sections: Record<string, readonly Record<string, unknown>[]> = {},
): KnowledgeReader {
  const reader: KnowledgeReader & {
    list(kind: string): readonly Record<string, unknown>[];
    campaignRows(section: string): readonly Record<string, unknown>[];
    campaignSection(section: string): Readonly<Record<string, unknown>>;
  } = {
    queryKnowledge: (query: KnowledgeQuery): KnowledgeResult => {
      for (const [id, kind] of [
        ["band_id", "band"],
        ["profile_id", "profile"],
        ["item_id", "item"],
        ["skill_id", "skill"],
        ["hireling_id", "hireling"],
      ] as const) {
        if (query.id.kind !== id) continue;
        const row = rows[`${kind}:${query.id.value}`];
        if (!row) return { ok: false, reason: "not_found" };
        return {
          ok: true,
          record: {
            kind,
            id: query.id,
            names: (row.names as Record<string, string>) ?? { en: String(row.name ?? query.id.value) },
            data: row,
          },
        };
      }
      return { ok: false, reason: "not_found" };
    },
    queryMany: (queries) => queries.map((query) => reader.queryKnowledge(query)),
    list: (kind) => sections[kind] ?? [],
    campaignRows: (section) => sections[section] ?? [],
    campaignSection: (section) => (sections[`section:${section}`]?.[0] as Record<string, unknown>) ?? {},
  };
  return reader;
}

const BAND = {
  id: "spirit-hosts-band",
  name: "Spirit Hosts",
  collection: "mordheim",
  rule_ids: ["band--requilary"],
  roster: {
    minimum_models: 3,
    maximum_models: 15,
    starting_gold: 500,
    members: [
      { profile_id: "corpse-master", minimum: 1, maximum: 2 },
      { profile_id: "spirit-hosts", minimum: 1, maximum: 3, group_size: { minimum: 1, maximum: 3 } },
    ],
  },
};

const CORPSE_MASTER = {
  id: "corpse-master",
  band_id: "spirit-hosts-band",
  collection: "mordheim",
  type: "hero",
  name: "Corpse Master",
  cost: 60,
  characteristics: { M: 4, WS: 4, BS: 4, S: 3, T: 4, W: 1, I: 4, A: 1, Ld: 8 },
  equipment_access: [
    { item_id: "sword", list_id: "corpse-master-list", cost: 10 },
    { item_id: "bow", list_id: "corpse-master-list", cost: 15 },
  ],
  equipment_forbids: [] as string[],
  fixed_equipment: [] as string[],
  skill_access: ["combat", "speed"],
  rule_ids: ["corpse-master--gofer"],
  combat_traits: {},
};

const SPIRIT_HOSTS = {
  id: "spirit-hosts",
  band_id: "spirit-hosts-band",
  collection: "mordheim",
  type: "henchman",
  name: "Spirit Hosts",
  cost: 35,
  characteristics: { M: 6, WS: 3, BS: 0, S: 4, T: 4, W: 1, I: 4, A: 2, Ld: 8 },
  equipment_access: [] as Record<string, unknown>[],
  equipment_forbids: ["armour", "ranged-weapons"],
  fixed_equipment: ["spectral_claws"],
  skill_access: [] as string[],
  rule_ids: ["spirit-hosts--spectral-touch"],
  combat_traits: {},
};

/** The profile `registry/runtime-scope.yaml` excludes, under its real band id. */
const EXCLUDED_BAND = "guild-of-disgraced-engineers-mim";
const EXCLUDED_PROFILE = {
  id: "gyrocopter",
  band_id: EXCLUDED_BAND,
  collection: "mordheim",
  type: "henchman",
  name: "Gyrocopter",
  cost: 100,
  characteristics: { M: null, WS: null, BS: null, S: null, T: 5, W: 3, I: null, A: null, Ld: null },
  equipment_access: [] as Record<string, unknown>[],
  equipment_forbids: [] as string[],
  fixed_equipment: [] as string[],
  skill_access: [] as string[],
  rule_ids: [],
  combat_traits: {},
};

const EXCLUDED_BAND_ROW = {
  id: EXCLUDED_BAND,
  name: "Disgraced Engineers",
  collection: "mordheim",
  rule_ids: [],
  roster: {
    minimum_models: 3,
    maximum_models: 12,
    starting_gold: 500,
    members: [{ profile_id: "gyrocopter", minimum: 0, maximum: 1 }],
  },
};

const ITEMS: Record<string, Record<string, unknown> | undefined> = {
  sword: { item_id: "sword", name: "Sword", kind: "close-combat-weapon" },
  bow: { item_id: "bow", name: "Bow", kind: "ranged-weapon" },
  heavy_armour: { item_id: "heavy_armour", name: "Heavy Armour", kind: "armour", mechanic_id: "armour.heavy-armour" },
  light_armour: { item_id: "light_armour", name: "Light Armour", kind: "armour", mechanic_id: "armour.light-armour" },
  shield: { item_id: "shield", name: "Shield", kind: "shield-or-defence", mechanic_id: "defence.shield" },
  spectral_claws: { item_id: "spectral_claws", name: "Spectral Claws", kind: "close-combat-weapon" },
  undefended_item: undefined,
};

function baseReader(overrides: Record<string, Record<string, unknown>> = {}): KnowledgeReader {
  const rows: Record<string, Record<string, unknown>> = {
    [`band:${BAND.id}`]: { ...BAND, ...(overrides.band ?? {}) },
    [`band:${EXCLUDED_BAND}`]: { ...EXCLUDED_BAND_ROW, ...(overrides["band:excluded"] ?? {}) },
    "hireling:hireling.hired-sword.albino-stormvermin": {
      id: "hireling.hired-sword.albino-stormvermin",
      kind: "hired-sword",
      characteristics: { M: 5, WS: 4, BS: 3, S: 4, T: 3, W: 1, I: 4, A: 1, Ld: 5 },
      warband_rating: { base: 30 },
    },
    "profile:corpse-master": { ...CORPSE_MASTER, ...(overrides["profile:corpse-master"] ?? {}) },
    "profile:spirit-hosts": SPIRIT_HOSTS,
    [`profile:gyrocopter`]: EXCLUDED_PROFILE,
    "skill:skill.dodge": { id: "skill.dodge", name: "Dodge", category: "speed", kind: "general" },
    "skill:skill.hard-to-kill": { id: "skill.hard-to-kill", name: "Hard to Kill", category: "special", kind: "special" },
  };
  for (const [id, row] of Object.entries(ITEMS)) {
    if (row) rows[`item:${id}`] = row;
  }
  return makeReader(rows, {
    profile: [rows["profile:corpse-master"], rows["profile:spirit-hosts"], rows["profile:gyrocopter"]],
    racial_maximum: [
      {
        id: "campaign.limit.racial-maximum.corpse-master",
        applies_to: "profile",
        profile: "corpse_master",
        characteristics: {
          movement: 4,
          weapon_skill: 4,
          strength: 4,
          toughness: 4,
          wounds: 2,
          initiative: 5,
          attacks: 3,
          leadership: 9,
        },
      },
    ],
    warband_groups: [{ id: "warband-group.undead", kind: "race", band_ids: [BAND.id] }],
    "section:hired-swords-and-dramatis": [
      {
        hired_swords: [
          {
            id: "campaign.hireling.hired-sword.albino-stormvermin",
            profile_id: "hireling.hired-sword.albino-stormvermin",
            eligibility: {
              allow_groups: ["warband-group.skaven"],
              forbid_groups: [],
              allow_band_ids: [],
              forbid_band_ids: [],
              note: "Albino Stormvermin may only be hired by Skaven warbands.",
            },
          },
          {
            id: "campaign.hireling.hired-sword.grave-warden",
            profile_id: "hireling.hired-sword.grave-warden",
            eligibility: {
              allow_groups: ["warband-group.undead"],
              forbid_groups: [],
              allow_band_ids: [],
              forbid_band_ids: [],
              note: "Any Dwarf, Elf or Human warband may hire a Grave Warden.",
            },
          },
          {
            id: "campaign.hireling.hired-sword.whaler",
            profile_id: "hireling.hired-sword.whaler",
            eligibility: {
              allow_groups: [],
              forbid_groups: ["warband-group.undead"],
              allow_band_ids: [],
              forbid_band_ids: [],
            },
          },
        ],
        dramatis_personae: [
          {
            id: "campaign.hireling.dramatis.the-foole",
            profile_id: "hireling.dramatis.the-foole",
            eligibility: {
              expression: { any_of: [{ band_id: BAND.id }, { group_id: "warband-group.good-aligned" }] },
            },
          },
          {
            id: "campaign.hireling.dramatis.other-foole",
            profile_id: "hireling.dramatis.other-foole",
            eligibility: { expression: { any_of: [{ band_id: "sisters-of-sigmar" }] } },
          },
        ],
      },
    ],
  });
}

function draftOk(result: ReturnType<typeof createDraft>): CampaignDocument {
  if (!result.ok) throw new Error(result.message);
  return result.state;
}

function draftOf(reader: KnowledgeReader, bandId = BAND.id): CampaignDocument {
  return draftOk(createDraft(bandId, reader));
}

function compose(document: CampaignDocument, reader: KnowledgeReader, rows: {
  profile_id: string;
  kind: "hero" | "henchman";
  quantity: number;
  equipment: string[];
}[]) {
  return createDefaultUseCases(reader).composeDraft(document, {
    band_id: document.campaign.identity.band_id,
    rows,
  });
}

function warrior(profileId: string, quantity: number, kind: "hero" | "henchman"): Warrior {
  return {
    id: `${profileId}#1`,
    name: profileId,
    profile_name: profileId,
    kind,
    stats: {},
    equipment: [],
    skills: [],
    experience: 0,
    quantity,
    cost: 30,
    profile_id: profileId,
  };
}

describe("construction contracts: roster composition", () => {
  it("accepts the roster its own draft produces and reports a group below its minimum", () => {
    const reader = baseReader();
    expect(rosterIssuesOf(reader, draftOf(reader).campaign)).toEqual([]);
    const grouped = baseReader({
      band: {
        roster: {
          minimum_models: 3,
          maximum_models: 15,
          starting_gold: 500,
          members: [
            { profile_id: "corpse-master", minimum: 1, maximum: 2 },
            { profile_id: "spirit-hosts", minimum: 1, maximum: 3, group_size: { minimum: 3, maximum: 3 } },
          ],
        },
      },
    });
    const campaign: Campaign = {
      ...draftOf(grouped).campaign,
      warriors: [warrior("corpse-master", 1, "hero"), warrior("spirit-hosts", 2, "henchman")],
    };
    expect(rosterIssuesOf(grouped, campaign).map((issue) => issue.code)).toEqual([
      "roster_group_minimum_missing",
    ]);
    const satisfied: Campaign = {
      ...campaign,
      warriors: [warrior("corpse-master", 1, "hero"), warrior("spirit-hosts", 3, "henchman")],
    };
    expect(rosterIssuesOf(grouped, satisfied)).toEqual([]);
  });

  it("rejects a profile the runtime scope excludes from being a fighter", () => {
    const reader = baseReader();
    expect(profileExclusionFor(EXCLUDED_BAND, "gyrocopter")?.reason).toContain("vehicle");
    const campaign: Campaign = {
      ...draftOf(reader, EXCLUDED_BAND).campaign,
      warriors: [warrior("gyrocopter", 1, "henchman")],
    };
    const issues = rosterIssuesOf(reader, campaign);
    expect(issues.map((issue) => issue.code)).toEqual(["profile_excluded_from_construction"]);
    expect(issues[0].owner_task).toBe("T13");
  });

  it("refuses to commit a band whose mandatory variant is still unchosen", () => {
    const reader = baseReader({
      band: {
        ...BAND,
        roster: { ...BAND.roster, requires_variant_selection: true },
        variants: [
          { id: "foreign", names: { en: "Foreign" }, rule_ids: [], starting_gold: 500 },
          { id: "native", names: { en: "Native" } },
        ],
      },
    });
    const draft = draftOf(reader);
    expect(rosterIssuesOf(reader, draft.campaign).map((issue) => issue.code)).toEqual([
      "variant_selection_required",
    ]);
    const committed = commitInitialWarband(draft, reader);
    expect(committed.ok).toBe(false);
    if (!committed.ok) expect(committed.message).toContain("warband variant");
    const chosen: CampaignDocument = {
      ...draft,
      campaign: {
        ...draft.campaign,
        identity: { ...draft.campaign.identity, mercenary_variant: "foreign" },
      },
    };
    expect(rosterIssuesOf(reader, chosen.campaign)).toEqual([]);
    expect(commitInitialWarband(chosen, reader).ok).toBe(true);
  });

  it("reports a band that demands a variant the knowledge base does not publish", () => {
    const reader = baseReader({
      band: { ...BAND, roster: { ...BAND.roster, requires_variant_selection: true } },
    });
    const draft = draftOf(reader);
    const issues = rosterIssuesOf(reader, draft.campaign);
    expect(issues.map((issue) => issue.code)).toEqual(["variant_options_missing"]);
    expect(issues[0].owner_task).toBe("KB");
    expect(commitInitialWarband(draft, reader).ok).toBe(false);
  });

  it("refuses to compose an excluded profile and to commit an incomplete roster", () => {
    const reader = baseReader();
    const draft = draftOf(reader, EXCLUDED_BAND);
    const composed = compose(draft, reader, [
      { profile_id: "gyrocopter", kind: "henchman", quantity: 1, equipment: [] },
    ]);
    expect(composed.ok).toBe(false);
    if (!composed.ok) expect(composed.message).toContain("outside the warband roster");

    // The band-level model count is satisfied; the missing slot is the failure.
    const readerOneModel = baseReader({
      band: { ...BAND, roster: { ...BAND.roster, minimum_models: 1 } },
    });
    const complete = draftOf(readerOneModel);
    const incomplete: CampaignDocument = {
      campaign: {
        ...complete.campaign,
        warriors: [warrior("corpse-master", 1, "hero")],
      },
      view: complete.view,
    };
    const committed = commitInitialWarband(incomplete, readerOneModel);
    expect(committed.ok).toBe(false);
    if (!committed.ok) expect(committed.message).toContain("requires at least 1 spirit-hosts");
  });

  it("refuses a band whose mandatory slot is an excluded profile", () => {
    const required = baseReader({
      "band:excluded": {
        roster: {
          minimum_models: 3,
          maximum_models: 12,
          starting_gold: 500,
          members: [{ profile_id: "gyrocopter", minimum: 1, maximum: 1 }],
        },
      },
    });
    const draft = createDraft(EXCLUDED_BAND, required);
    expect(draft.ok).toBe(false);
    if (!draft.ok) expect(draft.message).toContain("outside the warband roster");
  });

  it("reports unknown band ids and keeps the band record readable", () => {
    const reader = baseReader();
    expect(bandFactsOf(reader, "nope")).toBeNull();
    expect(bandFactsOf(reader, BAND.id)?.members.map((member) => member.profile_id)).toEqual([
      "corpse-master",
      "spirit-hosts",
    ]);
    const campaign = draftOf(reader).campaign;
    const unknown: Campaign = { ...campaign, identity: { ...campaign.identity, band_id: "nope" } };
    expect(constructionIssuesOf(reader, unknown).map((issue) => issue.code)).toEqual(["band_unknown"]);
  });
});

describe("construction contracts: equipment list", () => {
  it("accepts a listed item and a fixed item, and rejects an item outside the list", () => {
    const reader = baseReader();
    const corpseMaster = profileFactsOf(reader, BAND.id, "corpse-master")!;
    expect(equipmentIssueFor(reader, corpseMaster, "sword")).toBeNull();
    expect(equipmentIssueFor(reader, corpseMaster, "bow")).toBeNull();
    const outside = equipmentIssueFor(reader, corpseMaster, "heavy_armour");
    expect(outside?.code).toBe("equipment_not_permitted");
    const host = profileFactsOf(reader, BAND.id, "spirit-hosts")!;
    expect(equipmentIssueFor(reader, host, "spectral_claws")).toBeNull();
    expect(equipmentIssueFor(reader, host, "sword")?.code).toBe("equipment_not_permitted");
  });

  it("does not filter a legacy row that declares no access list", () => {
    const reader = baseReader();
    const legacy = profileFactsOf(reader, BAND.id, "spirit-hosts")!;
    const withoutAccess = { ...legacy, equipment_access: null };
    expect(equipmentIssueFor(reader, withoutAccess, "sword")).toBeNull();
  });

  it("applies the KB prohibition tokens: armour, heavy armour and ranged weapons", () => {
    const reader = baseReader();
    const host = profileFactsOf(reader, BAND.id, "spirit-hosts")!;
    const armourAccess = { ...host, equipment_access: [{ item_id: "light_armour" }] };
    expect(equipmentIssueFor(reader, armourAccess, "light_armour")?.code).toBe("equipment_forbidden");
    const shieldAccess = { ...host, equipment_access: [{ item_id: "shield" }] };
    expect(equipmentIssueFor(reader, shieldAccess, "shield")?.code).toBe("equipment_forbidden");
    const rangedAccess = { ...host, equipment_access: [{ item_id: "bow" }] };
    expect(equipmentIssueFor(reader, rangedAccess, "bow")?.code).toBe("equipment_forbidden");

    const heavyForbidden = {
      ...host,
      equipment_forbids: ["heavy-armour"],
      equipment_access: [{ item_id: "heavy_armour" }, { item_id: "light_armour" }],
    };
    expect(equipmentIssueFor(reader, heavyForbidden, "heavy_armour")?.code).toBe("equipment_forbidden");
    expect(equipmentIssueFor(reader, heavyForbidden, "light_armour")).toBeNull();
  });

  it("matches a mechanic-id token by stable id, not by name", () => {
    const reader = baseReader();
    const host = profileFactsOf(reader, BAND.id, "spirit-hosts")!;
    const helmetForbidden = {
      ...host,
      equipment_forbids: ["defence.shield"],
      equipment_access: [{ item_id: "shield" }],
    };
    expect(equipmentIssueFor(reader, helmetForbidden, "shield")?.code).toBe("equipment_forbidden");
  });

  it("reports malformed prohibition tokens and uninterpreted tokens instead of guessing", () => {
    const malformedReader = baseReader({
      "profile:corpse-master": { equipment_forbids: ["['armour', 'ranged-weapons']"] },
    });
    const facts = profileFactsOf(malformedReader, BAND.id, "corpse-master")!;
    expect(facts.equipment_forbids).toEqual([]);
    expect(facts.equipment_forbids_malformed).toEqual(["['armour', 'ranged-weapons']"]);

    const unknownReader = baseReader({
      "profile:corpse-master": { equipment_forbids: ["blackpowder-weapons"] },
    });
    const unknownFacts = profileFactsOf(unknownReader, BAND.id, "corpse-master")!;
    const issue = equipmentIssueFor(unknownReader, unknownFacts, "sword");
    expect(issue?.code).toBe("construction_clause_unstructured");
    expect(issue?.owner_task).toBe("KB");
  });

  it("rejects an outside purchase in composeDraft and accepts a legal one", () => {
    const reader = baseReader();
    const draft = draftOf(reader);
    const illegal = compose(draft, reader, [
      { profile_id: "corpse-master", kind: "hero", quantity: 1, equipment: ["heavy_armour"] },
    ]);
    expect(illegal.ok).toBe(false);
    if (!illegal.ok) expect(illegal.message).toContain("not on any equipment list");
    const legal = compose(draft, reader, [
      { profile_id: "corpse-master", kind: "hero", quantity: 1, equipment: ["sword"] },
    ]);
    expect(legal.ok).toBe(true);
  });

  it("keeps a legal item that has no artefact row and reports the gap", () => {
    const reader = baseReader();
    const facts = profileFactsOf(reader, BAND.id, "corpse-master")!;
    const offered = { ...facts, equipment_access: [{ item_id: "undefended_item" }] };
    const issue = equipmentIssueFor(reader, offered, "undefended_item");
    expect(issue?.code).toBe("equipment_unknown_item");
    expect(issue?.owner_task).toBe("KB");
  });
});

describe("construction contracts: skill access", () => {
  it("accepts an allowed category, rejects another and flags the special list", () => {
    const reader = baseReader();
    const facts = profileFactsOf(reader, BAND.id, "corpse-master")!;
    expect(skillIssueFor(facts, skillFactsOf(reader, "skill.dodge")!)).toBeNull();
    const rejected = skillIssueFor(facts, skillFactsOf(reader, "skill.hard-to-kill")!);
    expect(rejected?.code).toBe("skill_not_permitted");
    const specialFacts = { ...facts, skill_access: [...facts.skill_access, "special"] };
    const pending = skillIssueFor(specialFacts, skillFactsOf(reader, "skill.hard-to-kill")!);
    expect(pending?.code).toBe("skill_pending_special_list");
    expect(pending?.owner_task).toBe("KB");
  });

  it("declares no access for a henchman profile and leaves it unfiltered", () => {
    const reader = baseReader();
    const henchman = profileFactsOf(reader, BAND.id, "spirit-hosts")!;
    expect(skillIssueFor(henchman, skillFactsOf(reader, "skill.dodge")!)).toBeNull();
  });
});

describe("construction contracts: characteristic bounds", () => {
  it("rejects a value above the published maximum and leaves exempt profiles free", () => {
    const reader = baseReader();
    const rows = racialMaximumsOf(reader);
    expect(rows).toHaveLength(1);
    const facts = profileFactsOf(reader, BAND.id, "corpse-master")!;
    expect(characteristicBoundIssueFor({ profile: facts, stat: "S", value: 4, rows })).toBeNull();
    const over = characteristicBoundIssueFor({ profile: facts, stat: "S", value: 5, rows });
    expect(over?.code).toBe("characteristic_bound_exceeded");
    expect(over?.rule_id).toBe("campaign.limit.racial-maximum.corpse-master");
    const exempt = profileFactsOf(reader, BAND.id, "spirit-hosts")!;
    expect(characteristicBoundIssueFor({ profile: exempt, stat: "S", value: 9, rows })).toBeNull();
  });

  it("reports printed characteristics that are not fixed numbers", () => {
    const reader = baseReader();
    const issues = characteristicIssuesOf(profileFactsOf(reader, EXCLUDED_BAND, "gyrocopter")!);
    expect(issues).toHaveLength(7);
    expect(new Set(issues.map((issue) => issue.code))).toEqual(new Set(["characteristic_not_fixed"]));
  });

  it("rejects a starting characteristic above the maximum when the profile is created", () => {
    const reader = baseReader({ "profile:corpse-master": { characteristics: { ...CORPSE_MASTER.characteristics, S: 5 } } });
    const composed = compose(draftOf(reader), reader, [
      { profile_id: "corpse-master", kind: "hero", quantity: 1, equipment: [] },
    ]);
    expect(composed.ok).toBe(false);
    if (!composed.ok) expect(composed.message).toContain("exceeds the racial maximum");
  });
});

describe("construction contracts: hiring eligibility", () => {
  it("rejects a hireling whose groups forbid the band", () => {
    const reader = baseReader();
    const decision = hiringDecisionFor(reader, BAND.id, "hireling.hired-sword.albino-stormvermin");
    expect(decision.kind).toBe("rejected");
    expect(decision.clause).toBe("static");
    expect(decision.issue?.code).toBe("hiring_not_permitted");
    const whaler = hiringDecisionFor(reader, BAND.id, "hireling.hired-sword.whaler");
    expect(whaler.kind).toBe("rejected");
  });

  it("accepts a hireling whose groups allow the band", () => {
    const reader = baseReader();
    const decision = hiringDecisionFor(reader, BAND.id, "hireling.hired-sword.grave-warden");
    expect(decision.kind).toBe("allowed");
    expect(decision.clause).toBe("static");
  });

  it("evaluates the boolean eligibility expression", () => {
    const reader = baseReader();
    expect(hiringDecisionFor(reader, BAND.id, "hireling.dramatis.the-foole").kind).toBe("allowed");
    const other = hiringDecisionFor(reader, BAND.id, "hireling.dramatis.other-foole");
    expect(other.kind).toBe("rejected");
    expect(other.clause).toBe("expression");
  });

  it("reports a hireling with no published clause", () => {
    const reader = baseReader();
    const decision = hiringDecisionFor(reader, BAND.id, "hireling.dramatis.unknown");
    expect(decision.kind).toBe("unstructured");
    expect(decision.issue?.code).toBe("hiring_clause_unstructured");
  });

  it("refuses the hire in the kernel use case", () => {
    const reader = baseReader();
    const result = createDefaultUseCases(reader).hireHireling(
      draftOf(reader),
      { profile_id: "hireling.hired-sword.albino-stormvermin" },
      reader,
    );
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_available");
  });
});

describe("construction contracts: pending bindings and open clauses", () => {
  it("transports the declared-but-unimplemented binding to the consumer", () => {
    const reader = baseReader();
    const pending = pendingBindingsFor(profileFactsOf(reader, BAND.id, "spirit-hosts")!);
    expect(pending.map((entry) => entry.binding_id)).toEqual(["trait.spectral-touch"]);
    expect(pending[0].owner_task).toBe("T13");

    const campaign: Campaign = {
      ...draftOf(reader).campaign,
      warriors: [{ ...warrior("spirit-hosts", 2, "henchman"), skills: ["spirit-hosts--spectral-touch"] }],
    };
    const codes = constructionIssuesOf(reader, campaign).map((issue) => issue.code);
    expect(codes).toContain("pending_combat_binding");
  });

  it("reports no open clause for a band without them", () => {
    expect(openClausesOf(bandFactsOf(baseReader(), BAND.id)!, null)).toEqual([]);
  });
});

describe("construction contracts: granted choices and persistence", () => {
  it("grants each starting skill and rule once (no double concession)", () => {
    const created = warriorFromProfile(
      {
        ...CORPSE_MASTER,
        rule_ids: ["corpse-master--gofer", "skill.dodge"],
        inherent_rules: ["corpse-master--gofer", "skill.dodge"],
        combat_traits: { starting_skills: ["skill.dodge"] },
      },
      { profile_id: "corpse-master", kind: "hero", quantity: 1, equipment: [] },
      (itemId) => itemId,
      1,
    );
    expect(created.skills).toContain("corpse-master--gofer");
    expect(created.skills).toContain("skill.dodge");
    expect(new Set(created.skills).size).toBe(created.skills.length);
  });

  it("keeps the construction choices across a file round-trip", () => {
    const reader = baseReader();
    const adapter = new CampaignFileV5Adapter();
    expect(warbandVariants(reader, BAND.id)).toEqual([]);
    // The draft already seeds the mandatory slots (1 corpse-master + 2 spirit-hosts
    // to reach the 3-model minimum); the composed rows are added on top.
    const draft = draftOf(reader);
    const composed = compose(draft, reader, [
      { profile_id: "corpse-master", kind: "hero", quantity: 1, equipment: ["sword"] },
      { profile_id: "spirit-hosts", kind: "henchman", quantity: 1, equipment: [] },
    ]);
    expect(composed.ok).toBe(true);
    if (!composed.ok) return;
    const committed = commitInitialWarband(composed.state, reader);
    expect(committed.ok).toBe(true);
    if (!committed.ok) return;
    const serialized = adapter.serializeCampaign(committed.state.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const parsed = parseCampaignFileDetailed(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const restored = parsed.campaign;
    expect(restored.identity.band_id).toBe(BAND.id);
    const hosts = restored.warriors.filter((row) => row.profile_id === "spirit-hosts");
    expect(hosts.reduce((total, row) => total + (row.quantity ?? 1), 0)).toBe(3);
    expect(hosts.every((row) => row.skills.includes("spirit-hosts--spectral-touch"))).toBe(true);
    expect(restored.warriors.filter((row) => row.profile_id === "corpse-master")).toHaveLength(2);
    expect(restored.configuration.is_draft).toBe(false);
    expect(restored.inventory.some((row) => row.id === "sword")).toBe(true);
  });
});
