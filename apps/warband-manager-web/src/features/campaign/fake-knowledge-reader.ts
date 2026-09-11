/**
 * P5.2 stand-in knowledge reader, extended by P6.2 with an artefact-shaped
 * Sisters of Sigmar band (roster members, profiles, items) so the draft
 * workflow composes against the same record shapes the real P4.2 artefact
 * emits. Replaced by P4.3's real adapter in `default-deps.ts` (see
 * docs/decisions/web-migration.md).
 */
import type { KnowledgeQuery, KnowledgeReader, KnowledgeResult } from "./types";

const ROWS: Record<string, Record<string, unknown>> = {
  "band_id:sisters-of-sigmar": {
    id: "sisters-of-sigmar",
    name: "Sisters of Sigmar",
    names: { en: "Sisters of Sigmar", es: "Hermanas de Sigmar" },
    collection: "mordheim",
    roster: {
      minimum_models: 3,
      maximum_models: 15,
      starting_gold: 500,
      members: [
        { profile_id: "sigmarite-matriarch", minimum: 1, maximum: 1 },
        { profile_id: "sister-superior", minimum: 0, maximum: 3 },
        {
          profile_id: "sigmarite-sister",
          minimum: 0,
          maximum: null,
          group_size: { minimum: 1, maximum: 5 },
        },
      ],
    },
  },
  "band_id:mordheim": {
    id: "mordheim",
    name: "Mordheim",
    names: { en: "Mordheim" },
    collection: "mordheim",
  },
  "profile_id:sigmarite-matriarch": {
    id: "sigmarite-matriarch",
    band_id: "sisters-of-sigmar",
    collection: "mordheim",
    type: "hero",
    cost: 70,
    experience: 0,
    name: "Sigmarite Matriarch",
    names: { en: "Sigmarite Matriarch" },
    characteristics: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
    fixed_equipment: ["sigmarite_hammer"],
    skill_access: ["combat", "academic"],
    combat_traits: {},
  },
  "profile_id:sister-superior": {
    id: "sister-superior",
    band_id: "sisters-of-sigmar",
    collection: "mordheim",
    type: "hero",
    cost: 35,
    experience: 0,
    name: "Sister Superior",
    names: { en: "Sister Superior" },
    characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    fixed_equipment: [],
    skill_access: ["combat"],
  },
  "profile_id:sigmarite-sister": {
    id: "sigmarite-sister",
    band_id: "sisters-of-sigmar",
    collection: "mordheim",
    type: "henchman",
    cost: 25,
    experience: 0,
    name: "Sigmarite Sister",
    names: { en: "Sigmarite Sister" },
    characteristics: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    fixed_equipment: [],
  },
  "item_id:sigmarite_hammer": {
    item_id: "sigmarite_hammer",
    kind: "close-combat-weapon",
    name: "Sigmarite Hammer",
    names: { en: "Sigmarite Hammer", es: "Martillo de Sigmar" },
    value: 15,
  },
  "item_id:shield": {
    item_id: "shield",
    kind: "shield-or-defence",
    name: "Shield",
    names: { en: "Shield" },
    value: 5,
  },
  "item_id:dagger": {
    item_id: "dagger",
    kind: "close-combat-weapon",
    name: "Dagger",
    names: { en: "Dagger" },
    value: 2,
  },
  "scenario_id:skirmish": {
    id: "skirmish",
    name: "Skirmish",
    names: { en: "Skirmish", es: "Escaramuza" },
  },
  "scenario_id:raid": {
    id: "raid",
    name: "Raid",
    names: { en: "Raid" },
  },
  // P6.7: hireling profile records the use case resolves by stable id.
  "hireling_id:hireling.hired-sword.warrior-undead-hunter": {
    id: "hireling.hired-sword.warrior-undead-hunter",
    name: "Undead Hunter",
    names: { en: "Undead Hunter" },
    warband_rating: { kind: "base_plus_experience", base: 15, per_experience_point: 1 },
    characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    skills: [],
  },
  "hireling_id:hireling.hired-sword.ogre-bodyguard": {
    id: "hireling.hired-sword.ogre-bodyguard",
    name: "Ogre Bodyguard",
    names: { en: "Ogre Bodyguard" },
    warband_rating: { kind: "fixed", value: 75 },
    characteristics: { M: 6, WS: 3, BS: 2, S: 4, T: 4, W: 3, I: 2, A: 2, Ld: 6 },
    skills: [],
  },
};

export class FakeKnowledgeReader implements KnowledgeReader {
  queryKnowledge(query: KnowledgeQuery): KnowledgeResult {
    const row = ROWS[`${query.id.kind}:${query.id.value}`];
    if (!row) return { ok: false, reason: "not_found" };
    const { names, ...data } = row;
    return {
      ok: true,
      record: {
        kind: query.id.kind.replace(/_id$/, "") as never,
        id: query.id,
        names: names as Record<string, string>,
        data: Object.freeze({ ...data }),
      },
    };
  }

  queryMany(queries: readonly KnowledgeQuery[]): readonly KnowledgeResult[] {
    return queries.map((q) => this.queryKnowledge(q));
  }

  // P6.7 listings (KnowledgeListings structural interface; the real P4.3
  // adapter reads these from the artefact's campaign section).
  private static readonly LISTING_ROWS: Record<string, readonly Record<string, unknown>[]> = {
    warband_groups: [
      { id: "warband-group.sisters", kind: "race", band_ids: ["sisters-of-sigmar"] },
      { id: "warband-group.good-aligned", kind: "alignment", band_ids: ["sisters-of-sigmar"] },
    ],
    "hired-swords-and-dramatis:hired_swords": [
      {
        id: "campaign.hireling.hired-sword.warrior-undead-hunter",
        profile_id: "hireling.hired-sword.warrior-undead-hunter",
        hiring_fee: { resources: { gold_crowns: { cost: 35 } } },
        upkeep: { resources: { gold_crowns: { cost: 15 } } },
        availability: { kind: "common" },
        eligibility: { allow_groups: ["warband-group.good-aligned"] },
      },
      {
        id: "campaign.hireling.hired-sword.ogre-bodyguard",
        profile_id: "hireling.hired-sword.ogre-bodyguard",
        hiring_fee: { resources: { gold_crowns: { cost: 90 } } },
        upkeep: { resources: { gold_crowns: { cost: 30 } } },
        availability: { kind: "common" },
        eligibility: { allow_groups: ["warband-group.undead"] },
      },
    ],
    "hired-swords-and-dramatis:dramatis_personae": [],
  };

  private static readonly LISTING_SECTIONS: Record<string, Record<string, unknown>> = {
    hirelings: {
      profiles: [
        {
          id: "hireling.hired-sword.warrior-undead-hunter",
          kind: "hired-sword",
          name: "Undead Hunter",
          names: { en: "Undead Hunter" },
          warband_rating: { kind: "base_plus_experience", base: 15, per_experience_point: 1 },
        },
        {
          id: "hireling.hired-sword.ogre-bodyguard",
          kind: "hired-sword",
          name: "Ogre Bodyguard",
          names: { en: "Ogre Bodyguard" },
          warband_rating: { kind: "fixed", value: 75 },
        },
      ],
    },
    "trading-post": {
      items: [
        { id: "campaign.trading-post.axe", item_id: "axe", price: { base_gc: 5 }, availability: { kind: "common" } },
        {
          id: "campaign.trading-post.rope",
          item_id: "rope",
          price: { base_gc: 15 },
          availability: { kind: "common" },
        },
      ],
    },
  };

  campaignRows(section: string): readonly Record<string, unknown>[] {
    return FakeKnowledgeReader.LISTING_ROWS[section] ?? [];
  }

  campaignSection(section: string): Readonly<Record<string, unknown>> {
    return FakeKnowledgeReader.LISTING_SECTIONS[section] ?? {};
  }

  itemName(itemId: string): string {
    // Any listing row with a `names`/`name` field resolves first (the
    // real adapter delegates to rowNames); the static map is the fallback.
    for (const section of Object.values(FakeKnowledgeReader.LISTING_SECTIONS)) {
      const profiles = section["profiles"];
      if (Array.isArray(profiles)) {
        const profile = profiles.find(
          (p) => (p as Record<string, unknown>)["id"] === itemId,
        ) as Record<string, unknown> | undefined;
        if (profile) {
          const names = profile["names"] as Record<string, string> | undefined;
          if (names?.["en"]) return names["en"];
          if (typeof profile["name"] === "string") return profile["name"];
        }
      }
    }
    const names: Record<string, string> = { axe: "Axe", rope: "Rope" };
    return names[itemId] ?? itemId;
  }
}
