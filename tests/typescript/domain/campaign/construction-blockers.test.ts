/**
 * T09 §6 blockers: the construction clauses that used to reject a legal choice
 * or allow an invalid one.
 *
 * Seven cases, all of them construction/selection contracts:
 *
 * 1-3. `adventurers-kaz` special-skill tables (`band--barbarian-special-skills`,
 *      `band--dwarf-special-skills`, `band--elf-special-skills` and the Noble
 *      table of the same band): the binding the rules already declare is
 *      materialized for the printed recipients, so the bounded list is enforced
 *      instead of presenting the whole `special` catalogue as legal.
 * 4.   `silent-brotherhood-sc` `band--the-silence`: Black Powder and animals are
 *      prohibited band-wide through the item-tag vocabulary, and a Hired Sword
 *      whose published kit carries either family cannot be hired.
 * 5.   `snotlings-web` `runts--teeny-hands`: the Runts may not wear armour while
 *      the shared Snotling equipment list keeps offering it to everyone else.
 * 6.   `outlaws-of-stirwood-forest*` `band--bow-restrictions`: the member's
 *      complete kit carries at most one missile weapon, that weapon must be a
 *      bow, and the Cleric is exempt — decided as a set, never item by item.
 * 7.   `knights-of-the-bitter-moors-mim` `band--hired-swords`: the printed
 *      narrowing of the hire set (no Black Powder, Magic or Poison) through the
 *      campaign catalogue's stable traits and item tags.
 *
 * The assertions read the freshly generated artefact when
 * `MORDHEIM_KNOWLEDGE_ARTEFACT` points at it (the sweep's convention); the
 * KB-backed cases are additionally gated against the sources in
 * `tests/python/construction/test_construction_blockers.py`.
 *
 * Purity: plain Node, the real reader plus one fixture reader — no React, no
 * DOM, no filesystem write.
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { readArtefactDocument } from "../../../support/kb-artefact";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { KnowledgeQuery } from "@domain/campaign/kernel/ports";
import type { KnowledgeReader, KnowledgeResult } from "@domain/campaign/kernel/usecases";
import type { CampaignDocument } from "@domain/campaign/kernel/usecases";
import { hireHireling } from "@domain/campaign/kernel/hirelings";
import {
  bandFactsOf,
  bandHiringClausesOf,
  equipmentIssueFor,
  hiringClauseRejectionFor,
  hiringDecisionFor,
  itemFactsOf,
  memberEquipmentIssuesFor,
  profileFactsOf,
  rosterIssuesOf,
  skillFactsOf,
  skillIssueFor,
} from "@domain/campaign/construction";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      // The build output first: the published `outputs/` copy is still the
      // pre-T09 artefact T12 regenerates, and T10 verified these blockers
      // against the freshly generated one (`MORDHEIM_KNOWLEDGE_ARTEFACT`
      // overrides both).
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

const KAZ = "adventurers-kaz";
const SILENCE = "silent-brotherhood-sc";
const SNOTLINGS = "snotlings-web";
const OUTLAWS = [
  "outlaws-of-stirwood-forest",
  "outlaws-of-stirwood-forest-redux-fbg",
] as const;
const KNIGHTS = "knights-of-the-bitter-moors-mim";

/** Fake reader: rows keyed by `family:id`, exactly like the adapter's. */
function makeReader(rows: Record<string, Record<string, unknown>>): KnowledgeReader {
  const reader: KnowledgeReader = {
    queryKnowledge: (query: KnowledgeQuery): KnowledgeResult => {
      for (const [id, kind] of [
        ["band_id", "band"],
        ["profile_id", "profile"],
        ["item_id", "item"],
      ] as const) {
        if (query.id.kind !== id) continue;
        const row = rows[`${kind}:${query.id.value}`];
        if (!row) return { ok: false, reason: "not_found" };
        return {
          ok: true,
          record: {
            kind,
            id: query.id,
            names: { en: String(row.name ?? query.id.value) },
            data: row,
          },
        };
      }
      return { ok: false, reason: "not_found" };
    },
    queryMany: (queries) => queries.map((query) => reader.queryKnowledge(query)),
    list: () => [],
  };
  return reader;
}

function campaignDocument(bandId: string): CampaignDocument {
  const document: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: {
        campaign_name: "Blockers",
        warband_name: "Test",
        warband_type: "Middenheim",
        band_id: bandId,
        mercenary_variant: null,
      },
      configuration: {
        is_draft: false,
        starting_gold: 500,
        minimum_models: 3,
        maximum_models: 15,
        hero_limit: 5,
      },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [],
      battles: [],
      states: [
        {
          number: 1,
          date: "2026-09-10",
          gold: 500,
          wyrdstone: 0,
          rating: 0,
          models: 0,
          max_models: 15,
          heroes: 0,
          henchmen: 0,
          experience: 0,
        },
      ],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
  };
  return document as CampaignDocument;
}

describe.skipIf(!ARTEFACT_PATH)("T09 §6 blockers (generated artefact)", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader: KnowledgeReader = ArtefactKnowledgeReader.from(artefact);

  describe("KAZ special-skill tables", () => {
    const recipient: Record<string, string> = {
      barbarian: "skill.hard-to-kill",
      dwarf: "skill.berserker",
      elf: "skill.fey",
      "imperial-noble": "skill.taunt",
    };

    it("lets every published recipient choose a skill of its own list", () => {
      for (const [profileId, skillId] of Object.entries(recipient)) {
        const profile = profileFactsOf(reader, KAZ, profileId);
        const skill = skillFactsOf(reader, skillId);
        expect(profile, profileId).not.toBeNull();
        expect(skill, skillId).not.toBeNull();
        expect(skill?.category, skillId).toBe("special");
        expect(skillIssueFor(profile!, skill!), `${profileId}/${skillId}`).toBeNull();
      }
    });

    it("publishes a bounded list instead of the whole special catalogue", () => {
      const profile = profileFactsOf(reader, KAZ, "elf")!;
      const lists = profile.skill_lists.filter((list) => list.category === "special");
      expect(lists).toHaveLength(1);
      expect(lists[0]?.rule_id).toBe("band--elf-special-skills");
      expect(lists[0]?.skills).toEqual([
        "skill.chosen-of-the-white-tower",
        "skill.fey",
        "skill.fey-quickness",
      ]);
      const catalogue = (artefact.skills as { id: string; category: string }[])
        .filter((skill) => skill.category === "special")
        .map((skill) => skill.id);
      expect(catalogue.length).toBeGreaterThan(20);
      expect(lists[0]?.skills.length).toBeLessThan(catalogue.length);
    });

    it("rejects a special skill outside the published list", () => {
      const profile = profileFactsOf(reader, KAZ, "elf")!;
      const outside = skillFactsOf(reader, "skill.monster-slayer")!;
      const issue = skillIssueFor(profile, outside);
      expect(issue?.code).toBe("skill_not_permitted");
      expect(issue?.rule_id).toBe("band--elf-special-skills");
      // The same skill is legal for a Dwarf, whose own table lists it.
      const dwarf = profileFactsOf(reader, KAZ, "dwarf")!;
      expect(skillIssueFor(dwarf, outside)).toBeNull();
    });

    it("keeps a profile with no special access from using the tables", () => {
      const captain = profileFactsOf(reader, KAZ, "imperial-captain")!;
      expect(captain.skill_access).not.toContain("special");
      expect(captain.skill_lists).toEqual([]);
      const issue = skillIssueFor(captain, skillFactsOf(reader, "skill.fey")!);
      expect(issue?.code).toBe("skill_not_permitted");
    });
  });

  describe("Silent Brotherhood: The Silence", () => {
    it("publishes the prohibition band-wide through item tags", () => {
      const band = bandFactsOf(reader, SILENCE)!;
      expect(band.equipment_forbids).toEqual(["animal", "blackpowder"]);
      // H5 source check (2026-10-04): the rulebook prints the crossbow pistol
      // under Missile Weapons and the brotherhood list sells it at 35 gc, so
      // the catalogue tags it as a crossbow, not as blackpowder. Provenance:
      // docs/knowledge/2a2b/tasks/T13-silence-equipment.md section 12.
      expect(itemFactsOf(reader, "crossbow_pistol")?.tags).toEqual(["crossbow"]);
      expect(itemFactsOf(reader, "pistol")?.tags).toContain("blackpowder");
    });

    it("rejects every Black Powder item for a member and keeps the printed kit", () => {
      const profile = profileFactsOf(reader, SILENCE, "silent-master")!;
      // The printed crossbow pistol the band's list offers stays legal.
      expect(equipmentIssueFor(reader, profile, "crossbow_pistol")).toBeNull();
      // The Black Powder family is still refused. The list does not offer
      // these either, so the access verdict fires first; the tag is the family
      // witness behind it (the decision boundary is covered by the
      // reconciliation suite).
      for (const itemId of ["pistol", "blunderbuss", "handgun"]) {
        expect(itemFactsOf(reader, itemId)?.tags, itemId).toContain("blackpowder");
        expect(equipmentIssueFor(reader, profile, itemId), itemId).not.toBeNull();
      }
      // The band's own list offers the legal kit: it stays permitted.
      const offers = new Set(
        (artefact.profiles as { id: string; band_id: string; equipment_access?: { item_id: string }[] }[])
          .filter((row) => row.id === "silent-master" && row.band_id === SILENCE)
          .flatMap((row) => (row.equipment_access ?? []).map((offer) => offer.item_id)),
      );
      const legal = [...offers].filter((itemId) => {
        const tags = itemFactsOf(reader, itemId)?.tags ?? [];
        return !tags.includes("blackpowder") && !tags.includes("animal");
      });
      expect(legal).toContain("sword");
      expect(legal).toContain("crossbow_pistol");
      expect(equipmentIssueFor(reader, profile, "sword")).toBeNull();
    });

    it("rejects an animal item and an animal profile through the same tag", () => {
      const rows: Record<string, Record<string, unknown>> = {
        [`band:${SILENCE}`]: {
          id: SILENCE,
          name: "Silent Brotherhood",
          roster: { members: [{ profile_id: "warhound" }] },
          equipment_forbids: ["animal", "blackpowder"],
        },
        "item:warhound": { item_id: "warhound", kind: "out-of-scope", tags: ["animal"] },
        "profile:warhound": {
          band_id: SILENCE,
          type: "animal",
          equipment_access: null,
          equipment_forbids: [],
        },
      };
      const fixture = makeReader(rows);
      const band = bandFactsOf(fixture, SILENCE)!;
      const profile = profileFactsOf(fixture, SILENCE, "warhound")!;
      expect(profile.is_animal).toBe(true);
      expect(equipmentIssueFor(fixture, profile, "warhound")?.code).toBe("equipment_forbidden");
      const campaign = { identity: { band_id: SILENCE }, warriors: [{ profile_id: "warhound" }] };
      const issues = rosterIssuesOf(fixture, campaign as never);
      expect(issues.map((issue) => issue.code)).toContain("animal_not_permitted");
      expect(band.equipment_forbids).toContain("animal");
    });

    it("refuses a Hired Sword whose kit carries Black Powder", () => {
      const clause = bandHiringClausesOf(reader, SILENCE);
      expect(clause).toHaveLength(1);
      expect(clause[0]?.rule_id).toBe("band--the-silence");
      const decision = hiringDecisionFor(reader, SILENCE, "hireling.hired-sword.duellist");
      expect(decision.kind).toBe("rejected");
      expect(decision.clause).toBe("band-clause");
      expect(hiringClauseRejectionFor(reader, clause[0]!, "hireling.hired-sword.duellist"))
        .toBe("blackpowder");
      // A Hired Sword whose kit carries no forbidden family is still allowed.
      expect(hiringClauseRejectionFor(reader, clause[0]!, "hireling.hired-sword.human-scout"))
        .toBeNull();
    });
  });

  describe("Snotlings: Teeny Hands", () => {
    it("rejects armour for the Runts", () => {
      const runts = profileFactsOf(reader, SNOTLINGS, "runts")!;
      expect(runts.equipment_forbids).toContain("armour");
      // The shield and the helmet print no recipients, so the Runts' own
      // prohibition is what refuses them and the verdict carries the token.
      for (const itemId of ["shield", "helmet"] as const) {
        expect(equipmentIssueFor(reader, runts, itemId)?.code, itemId).toBe("equipment_forbidden");
      }
      // light_armour prints "Goblin & BigSnotz only" (F074), so the access
      // verdict fires first for the Runts. The refusal is the printed one; the
      // armour token behind it stays latent, exactly like the Black Powder kit.
      expect(equipmentIssueFor(reader, runts, "light_armour")?.code)
        .toBe("equipment_not_permitted");
    });

    it("keeps the shared list usable for the profiles the rule does not name", () => {
      const scouts = profileFactsOf(reader, SNOTLINGS, "scouts")!;
      expect(scouts.equipment_lists).toEqual(["snotling-equipment-list"]);
      expect(profileFactsOf(reader, SNOTLINGS, "runts")!.equipment_lists)
        .toEqual(scouts.equipment_lists);
      expect(scouts.equipment_forbids).not.toContain("armour");
      // The Runts' rule names no entry, so the unqualified entries of the shared
      // list stay open to the other Snotling profiles.
      expect(equipmentIssueFor(reader, scouts, "shield")).toBeNull();
      expect(equipmentIssueFor(reader, scouts, "helmet")).toBeNull();
      // The printed "Goblin & BigSnotz only" clause is what narrows light_armour.
      expect(equipmentIssueFor(reader, scouts, "light_armour")?.code)
        .toBe("equipment_not_permitted");
      expect(equipmentIssueFor(reader, profileFactsOf(reader, SNOTLINGS, "bullied-goblin")!, "light_armour"))
        .toBeNull();
    });
  });

  describe("Outlaws of Stirwood Forest: Bow Restrictions", () => {
    it("permits one bow and requires it for every non-exempt member", () => {
      for (const bandId of OUTLAWS) {
        const profile = profileFactsOf(reader, bandId, "bandit-leader")!;
        expect(memberEquipmentIssuesFor(reader, profile, ["bow"]), bandId).toEqual([]);
        expect(memberEquipmentIssuesFor(reader, profile, ["long_bow"]), bandId).toEqual([]);
        // Printed: "All warriors must carry a type of bow ... as part of their
        // equipment", so a kit without one is refused, not silently allowed.
        expect(
          memberEquipmentIssuesFor(reader, profile, []).map((issue) => issue.code),
          bandId,
        ).toEqual(["equipment_required_missing"]);
      }
    });

    it("rejects two missile weapons", () => {
      const profile = profileFactsOf(reader, OUTLAWS[1], "bandit-leader")!;
      const issues = memberEquipmentIssuesFor(reader, profile, ["bow", "long_bow"]);
      expect(issues.map((issue) => issue.code)).toEqual(["equipment_limit_exceeded"]);
      expect(issues[0]?.rule_id).toBe("band--bow-restrictions");
      expect(issues[0]?.subject_ids).toContain("long_bow");
    });

    it("rejects a missile weapon that is not a bow", () => {
      const profile = profileFactsOf(reader, OUTLAWS[0], "outlaws")!;
      const issues = memberEquipmentIssuesFor(reader, profile, ["crossbow_pistol"]);
      expect(issues.map((issue) => issue.code)).toContain("equipment_required_missing");
      // The crossbow pistol carries the `crossbow` family tag (H5), but the
      // band never offers it: the access verdict fires first and the family
      // refusal stays latent, as the F020 record states.
      expect(itemFactsOf(reader, "crossbow_pistol")?.tags).toContain("crossbow");
      // The band lists carry no crossbow: buying one is refused outright.
      expect(equipmentIssueFor(reader, profile, "crossbow_pistol")?.code)
        .toBe("equipment_not_permitted");
    });

    it("exempts the Cleric from the bow requirement", () => {
      for (const bandId of OUTLAWS) {
        const cleric = profileFactsOf(reader, bandId, "cleric")!;
        expect(bandFactsOf(reader, bandId)!.equipment_limits?.exempt_profile_ids)
          .toContain("cleric");
        expect(memberEquipmentIssuesFor(reader, cleric, []), bandId).toEqual([]);
        expect(memberEquipmentIssuesFor(reader, cleric, ["short_bow"]), bandId).toEqual([]);
        // The printed exception lifts the family only; the missile cap still applies.
        expect(
          memberEquipmentIssuesFor(reader, cleric, ["short_bow", "long_bow"]).map((issue) => issue.code),
          bandId,
        ).toEqual(["equipment_limit_exceeded"]);
      }
    });
  });

  describe("Knights of the Bitter Moors: Hired Swords", () => {
    const clause = () => bandHiringClausesOf(reader, KNIGHTS)[0]!;

    it("permits a Hired Sword applicable to Humans", () => {
      const decision = hiringDecisionFor(reader, KNIGHTS, "hireling.hired-sword.human-scout");
      expect(decision.kind).toBe("allowed");
      expect(hiringClauseRejectionFor(reader, clause(), "hireling.hired-sword.human-scout"))
        .toBeNull();
    });

    it("rejects each printed exclusion", () => {
      // Black Powder: the Duellist's kit carries a duelling pistol.
      const blackpowder = hiringDecisionFor(reader, KNIGHTS, "hireling.hired-sword.duellist");
      expect(blackpowder.kind).toBe("rejected");
      expect(blackpowder.rule_id).toBe("band--hired-swords");
      expect(blackpowder.reason).toContain("blackpowder");
      // Poison: the renegade assassin carries Dark Venom.
      expect(
        hiringDecisionFor(reader, KNIGHTS, "hireling.dramatis.dijin-katal-the-renegade-assassin").kind,
      ).toBe("rejected");
      // Magic: the Warlock is a spellcaster.
      const magic = hiringDecisionFor(reader, KNIGHTS, "hireling.hired-sword.warlock");
      expect(magic.kind).toBe("rejected");
      expect(magic.reason).toContain("spellcaster");
    });

    it("rejects a Hired Sword that is not applicable to Humans", () => {
      const decision = hiringDecisionFor(reader, KNIGHTS, "hireling.hired-sword.dwarf-slayer-pirate");
      expect(decision.kind).toBe("rejected");
      // H5: his printed kit carries Superior Blackpowder, so the band's own
      // clause (no Black Powder) reports first; the entry's non-Human
      // eligibility still rejects him through the same decision (its static and
      // expression paths are covered in construction.test.ts).
      expect(decision.clause).toBe("band-clause");
      expect(decision.rule_id).toBe("band--hired-swords");
      expect(decision.reason).toContain("blackpowder");
      expect(decision.issue?.code).toBe("hiring_not_permitted");
    });

    it("refuses the hire through the hiring flow", () => {
      const document = campaignDocument(KNIGHTS);
      const refused = hireHireling(
        document,
        { profile_id: "hireling.hired-sword.duellist", fee: 30 },
        reader,
      );
      expect(refused.ok).toBe(false);
      const allowed = hireHireling(
        document,
        { profile_id: "hireling.hired-sword.human-scout", fee: 30 },
        reader,
      );
      expect(allowed.ok).toBe(true);
    });
  });

  describe("Printed entry recipients (F074)", () => {
    it("refuses a hero-only entry to the henchmen that share the same list", () => {
      for (const bandId of ["estalian-corsairs-sar", "sartosan-pirates-sar"] as const) {
        const captain = profileFactsOf(reader, bandId, "captain")!;
        const crew = profileFactsOf(reader, bandId, "crew")!;
        // One printed list, two profiles: the clause is local to the entry, so
        // it never narrows the list itself.
        expect(crew.equipment_lists, bandId).toEqual(captain.equipment_lists);
        expect(equipmentIssueFor(reader, captain, "cat_o_nine_tails"), bandId).toBeNull();
        expect(equipmentIssueFor(reader, crew, "cat_o_nine_tails")?.code, bandId)
          .toBe("equipment_not_permitted");
      }
    });

    it("keeps the unqualified entries of the same list open to everyone", () => {
      // The Halfling adventurer list prints short_bow without recipients.
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-scouts")!, "short_bow"))
        .toBeNull();
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-warriors")!, "short_bow"))
        .toBeNull();
      // While the neighbouring clauses stay local to their own entry: a
      // named-profile clause and a hero clause on the same list.
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-cook")!, "bow"))
        .toBeNull();
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-scouts")!, "bow"))
        .toBeNull();
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-warriors")!, "bow")?.code)
        .toBe("equipment_not_permitted");
      // The "Heroes & Halfling Warriors only" clause on the spear is local too:
      // the excluded Henchman is refused while the named one keeps it.
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-scouts")!, "spear")?.code)
        .toBe("equipment_not_permitted");
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "halflings-mic", "halfling-warriors")!, "spear"))
        .toBeNull();
    });

    it("restricts a printed recipient to one named henchman", () => {
      const master = profileFactsOf(reader, "silent-brotherhood-sc", "silent-master")!;
      const novices = profileFactsOf(reader, "silent-brotherhood-sc", "brotherhood-novices")!;
      expect(equipmentIssueFor(reader, master, "long_daggers")).toBeNull();
      expect(equipmentIssueFor(reader, novices, "long_daggers")?.code).toBe("equipment_not_permitted");
      // The Band's Silence still forbids Black Powder through the tag family:
      // the brotherhood list carries no pistol, so the access verdict fires
      // first and the tag stays the family witness behind it.
      expect(itemFactsOf(reader, "pistol")?.tags).toContain("blackpowder");
      expect(equipmentIssueFor(reader, master, "pistol")?.code).toBe("equipment_not_permitted");
    });

    it("reads a Tomb Lord clause from the shared undead list", () => {
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "khemri-tomb-guardians", "tomb-lord")!, "asp_arrows"))
        .toBeNull();
      for (const nonRecipient of ["skeleton-warriors", "necrotect"] as const) {
        expect(equipmentIssueFor(reader, profileFactsOf(reader, "khemri-tomb-guardians", nonRecipient)!, "asp_arrows")?.code, nonRecipient)
          .toBe("equipment_not_permitted");
      }
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "khemri-tomb-guardians", "tomb-lord")!, "serpent_staff")?.code)
        .toBe("equipment_not_permitted");
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "khemri-tomb-guardians", "mortuary-priest")!, "serpent_staff"))
        .toBeNull();
    });

    it("carries the printed Slayer vow as a structured prohibition", () => {
      const slayer = profileFactsOf(reader, "dwarf-slayers-kaz", "troll-slayers")!;
      const clansman = profileFactsOf(reader, "dwarf-slayers-kaz", "clansmen")!;
      expect(slayer.equipment_forbids).toEqual(["armour", "ranged-weapons"]);
      for (const itemId of ["light_armour", "shield", "helmet", "pistol"] as const) {
        expect(equipmentIssueFor(reader, slayer, itemId)?.code, itemId).toBe("equipment_forbidden");
      }
      // The non-Slayer buys on the same list and keeps the armour.
      expect(clansman.equipment_lists).toEqual(slayer.equipment_lists);
      expect(clansman.equipment_forbids).toEqual([]);
      expect(equipmentIssueFor(reader, clansman, "light_armour")).toBeNull();
      expect(equipmentIssueFor(reader, clansman, "helmet")).toBeNull();
    });

    it("applies a printed recipient clause across the collections", () => {
      // Trollheim bands read the same generated artefact and the same decision.
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "lustria-pirates", "pirate-captain")!, "parrot"))
        .toBeNull();
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "lustria-pirates", "crew")!, "parrot")?.code)
        .toBe("equipment_not_permitted");
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "lustria-high-elves", "loremaster")!, "mage_staff"))
        .toBeNull();
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "lustria-high-elves", "explorers")!, "mage_staff")?.code)
        .toBe("equipment_not_permitted");
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "chaos-streets-deathbringers", "shadow-blade")!, "witch_sword"))
        .toBeNull();
      expect(equipmentIssueFor(reader, profileFactsOf(reader, "chaos-streets-deathbringers", "knives")!, "witch_sword")?.code)
        .toBe("equipment_not_permitted");
    });
  });
});
