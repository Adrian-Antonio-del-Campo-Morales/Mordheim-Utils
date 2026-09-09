/**
 * P5.2 stand-in knowledge reader, extended by P6.2 with an artefact-shaped
 * Sisters of Sigmar band (roster members, profiles, items) so the draft
 * workflow composes against the same record shapes the real P4.2 artefact
 * emits. Replaced by P4.3's real adapter in `default-deps.ts` (see
 * docs/decisions/web-kb-bundling.md).
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
}
