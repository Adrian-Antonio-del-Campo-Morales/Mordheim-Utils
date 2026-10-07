/**
 * T13 construction restrictions through the Warband Manager transport.
 *
 * The shared decision (`packages/typescript/domain/eligibility/index.ts`) owns
 * legality; these cases drive the campaign domain over the generated artefact,
 * which is the route Warband Manager actually uses, so they prove the facts
 * travel (`profile.required_equipment`, the band `equipment_limits` copy bound,
 * the profile `poison_application`) and not only that the pure predicate can
 * decide a hand-built token:
 *
 * 1. Sisters of Sigmar: one Sigmarite Hammer for the ordinary bearer, two for
 *    the exempt Matriarch / Sister Superior, and the refusal carries the clause.
 * 2. Knights Errant: the compulsory hand-to-hand weapon, satisfied by a real
 *    weapon and never by the free dagger.
 * 3. Lizardmen: the published poison application per bearer and weapon kind
 *    (Skink melee refused, Saurus melee admitted).
 * 4. Sons of Hashut: the compulsory canonical Blunderbuss.
 *
 * The House Guard and Silent Brotherhood lines are conditional on a build
 * selection (`applies_to.variants`) that the campaign file cannot carry today
 * (`identity.mercenary_variant` names a published warband variant, and neither
 * band publishes one), so the case records the boundary instead of inventing a
 * default: the shared predicate decides the gate (Combat Lab transports it in
 * `variant_ids`) while the canonical-profile artefact keeps conditional lines
 * out of every access list.
 *
 * Purity: plain Node, the real reader and the generated artefact — no React.
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { readArtefactDocument } from "../../../support/kb-artefact";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import {
  entryReachesProfile, poisonApplicationIssue,
  type ItemFacts, type PoisonApplication,
} from "@domain/eligibility/index";
import {
  bandFactsOf,
  equipmentIssueFor,
  itemFactsOf,
  memberEquipmentIssuesFor,
  profileFactsOf,
  type ProfileFacts,
} from "@domain/campaign/construction";
import { warbandVariants } from "@domain/campaign/band-variants";
import type { KnowledgeReader } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

const SISTERS = "sisters-of-sigmar";
const KNIGHTS = "bretonnian-knights-errant-mou";
const LIZARDS = "lizardmen-lus";
const HASHUT = "sons-of-hashut";
const HOUSE = "house-guard-sc";
const SILENCE = "silent-brotherhood-sc";
const MOOT = "mootlanders";
const SNOTLINGS = "snotlings-web";
const MARE = "order-of-the-mare-web";
const GHUTANI = "ghutani-rel";

type ArtefactProfile = Readonly<Record<string, unknown>>;

describe.skipIf(!ARTEFACT_PATH)("T13 construction restrictions through the Warband Manager transport", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader: KnowledgeReader = ArtefactKnowledgeReader.from(artefact);
  const rows = (artefact as Readonly<Record<string, unknown>>)["profiles"] as readonly ArtefactProfile[] | undefined;
  const row = (bandId: string, profileId: string): ArtefactProfile => {
    const found = (rows ?? []).find(
      (profile) => profile["band_id"] === bandId && profile["id"] === profileId,
    );
    expect(found, `${bandId}/${profileId} must be published`).toBeTruthy();
    return found as ArtefactProfile;
  };
  const facts = (bandId: string, profileId: string): ProfileFacts =>
    profileFactsOf(reader, bandId, profileId) as ProfileFacts;
  const applications = (bandId: string, profileId: string): readonly PoisonApplication[] =>
    ((row(bandId, profileId)["poison_application"] ?? []) as readonly PoisonApplication[]);

  describe("Sisters of Sigmar: the Sigmarite Hammer copy bound", () => {
    it("publishes the printed clause on the band and the exemption on its bearers", () => {
      const limits = bandFactsOf(reader, SISTERS)?.equipment_limits;
      expect(limits?.item_copy_limit).toEqual({
        item_id: "weapon.sigmarite-hammer",
        maximum: 1,
        exempt_profile_ids: ["sigmarite-matriarch", "sister-superior"],
        exempt_maximum: 2,
      });
      expect(limits?.rule_id).toBe("band--sigmarite-hammer-pair");
    });

    it("allows one hammer, refuses two for the ordinary bearer and admits two for the exempt one", () => {
      const sister = facts(SISTERS, "sigmarite-sister");
      expect(memberEquipmentIssuesFor(reader, sister, ["sigmarite_hammer"])).toEqual([]);
      const two = memberEquipmentIssuesFor(reader, sister, ["sigmarite_hammer", "sigmarite_hammer"]);
      expect(two.map((issue) => issue.code)).toEqual(["equipment_limit_exceeded"]);
      expect(two[0]?.rule_id).toBe("band--sigmarite-hammer-pair");
      expect(two[0]?.message).toContain("the printed clause allows 1 for this bearer");

      const matriarch = facts(SISTERS, "sigmarite-matriarch");
      expect(memberEquipmentIssuesFor(reader, matriarch, ["sigmarite_hammer", "sigmarite_hammer"])).toEqual([]);
      expect(memberEquipmentIssuesFor(reader, matriarch, ["sigmarite_hammer", "sigmarite_hammer", "sigmarite_hammer"])
        .map((issue) => issue.code)).toEqual(["equipment_limit_exceeded"]);
      const superior = facts(SISTERS, "sister-superior");
      expect(memberEquipmentIssuesFor(reader, superior, ["sigmarite_hammer", "sigmarite_hammer"])).toEqual([]);
    });

    it("counts the bound by the canonical weapon, not by the row's spelling", () => {
      // The bound names the mechanic id, so an alias/bundle id of the same
      // canonical weapon is still one of its copies.
      const sister = facts(SISTERS, "sigmarite-sister");
      expect(itemFactsOf(reader, "sigmarite_hammer")?.mechanic_id).toBe("weapon.sigmarite-hammer");
      const two = memberEquipmentIssuesFor(reader, sister, ["sigmarite_hammer", "sigmarite_hammer"]);
      expect(two.length).toBe(1);
    });
  });

  describe("Knights Errant: the compulsory hand-to-hand weapon", () => {
    it("publishes the obligation with the printed dagger exclusion", () => {
      expect(row(KNIGHTS, "knights-errant")["required_equipment"]).toEqual([
        { rule_id: "knights-errant--hand-to-hand-weapon", kinds: ["close-combat-weapon"], excludes: ["weapon.dagger"] },
      ]);
    });

    it("refuses an empty kit and a lone free dagger, and admits a real weapon", () => {
      const knight = facts(KNIGHTS, "knights-errant");
      const missing = memberEquipmentIssuesFor(reader, knight, []);
      expect(missing.map((issue) => issue.code)).toEqual(["equipment_required_missing"]);
      expect(missing[0]?.rule_id).toBe("knights-errant--hand-to-hand-weapon");

      const dagger = memberEquipmentIssuesFor(reader, knight, ["dagger"]);
      expect(dagger.map((issue) => issue.code)).toEqual(["equipment_required_missing"]);
      expect(itemFactsOf(reader, "dagger")?.mechanic_id).toBe("weapon.dagger");

      expect(memberEquipmentIssuesFor(reader, knight, ["sword"])).toEqual([]);
      expect(memberEquipmentIssuesFor(reader, knight, ["dagger", "sword"])).toEqual([]);
    });

    it("keeps the obligation off the profiles the clause does not name", () => {
      const squires = facts(KNIGHTS, "squires");
      expect(squires.required_equipment).toEqual([]);
      expect(memberEquipmentIssuesFor(reader, squires, [])).toEqual([]);
    });
  });

  describe("Lizardmen: poison application by bearer and weapon kind", () => {
    it("publishes the application fact per bearer", () => {
      expect(applications(LIZARDS, "skink-priest")).toEqual([
        { rule_id: "band--skink-poison-application", poisons: ["poison.black-venom", "poison.black-lotus"], weapon_kinds: ["ranged-weapon"] },
      ]);
      expect(applications(LIZARDS, "saurus-braves")).toEqual([
        { rule_id: "band--saurus-poison-application", poisons: ["poison.black-venom", "poison.black-lotus"], weapon_kinds: ["close-combat-weapon"] },
      ]);
      expect(applications(LIZARDS, "skink-braves")).toEqual([
        { rule_id: "band--skink-henchman-poison-application", poisons: ["poison.reptile-venom"], weapon_kinds: ["ranged-weapon"] },
      ]);
    });

    it("refuses a Skink melee application and admits the Saurus melee one", () => {
      const sword = itemFactsOf(reader, "sword") as ItemFacts;
      const bow = itemFactsOf(reader, "short_bow") as ItemFacts;
      const skink = {
        band_id: LIZARDS, profile_id: "skink-priest", poison_application: applications(LIZARDS, "skink-priest"),
      };
      const saurus = {
        band_id: LIZARDS, profile_id: "saurus-braves", poison_application: applications(LIZARDS, "saurus-braves"),
      };

      expect(poisonApplicationIssue({
        profile: skink, poison_id: "poison.black-venom", weapon_id: "sword", weapon: sword,
      })?.rule_id).toBe("band--skink-poison-application");
      expect(poisonApplicationIssue({
        profile: skink, poison_id: "poison.black-venom", weapon_id: "short_bow", weapon: bow,
      })).toBeNull();
      expect(poisonApplicationIssue({
        profile: saurus, poison_id: "poison.black-venom", weapon_id: "sword", weapon: sword,
      })).toBeNull();
      // A poison the bearer's clause does not name stays ungoverned here.
      expect(poisonApplicationIssue({
        profile: saurus, poison_id: "poison.reptile-venom", weapon_id: "sword", weapon: sword,
      })).toBeNull();
    });
  });

  describe("Sons of Hashut: the compulsory canonical Blunderbuss", () => {
    it("publishes the obligation and decides it as a whole kit", () => {
      expect(row(HASHUT, "blunderbuss-chaos-dwarfs")["required_equipment"]).toEqual([
        { rule_id: "blunderbuss-chaos-dwarfs--equipment-restrictions", kinds: ["chaos_dwarf_blunderbuss"], excludes: [] },
      ]);
      const bearer = facts(HASHUT, "blunderbuss-chaos-dwarfs");
      expect(memberEquipmentIssuesFor(reader, bearer, []).map((issue) => issue.code))
        .toEqual(["equipment_required_missing"]);
      expect(memberEquipmentIssuesFor(reader, bearer, ["chaos_dwarf_blunderbuss"])).toEqual([]);
      // A generic blunderbuss is a different canonical object: it does not satisfy it.
      expect(memberEquipmentIssuesFor(reader, bearer, ["blunderbuss"]).map((issue) => issue.code))
        .toEqual(["equipment_required_missing"]);
    });
  });

  describe("House and Sniper conditional lines: predicate decided, product selection absent", () => {
    it("decides the House gate on the build's real selection", () => {
      const rapier = { item_id: "rapier", applies_to: { variants: ["house.fierezza"] } };
      expect(entryReachesProfile(rapier, { id: "commander", type: "hero", variants: ["house.fierezza"] })).toBe(true);
      expect(entryReachesProfile(rapier, { id: "commander", type: "hero", variants: ["house.halcon"] })).toBe(false);
      expect(entryReachesProfile(rapier, { id: "commander", type: "hero", variants: [] })).toBe(false);
      expect(entryReachesProfile(rapier, { id: "sergeants", type: "hero", variants: [] })).toBe(false);
    });

    it("keeps the Sniper line and the named Silent Master denial conjunctive", () => {
      const crossbow = {
        item_id: "crossbow",
        applies_to: { variants: ["modus-operandi.sniper"], excluded_profile_ids: ["silent-master"] },
      };
      expect(entryReachesProfile(crossbow, { id: "poisoner", type: "hero", variants: ["modus-operandi.sniper"] })).toBe(true);
      expect(entryReachesProfile(crossbow, { id: "assassins", type: "hero", variants: ["modus-operandi.sniper"] })).toBe(true);
      expect(entryReachesProfile(crossbow, { id: "brotherhood-novices", type: "henchman", variants: ["modus-operandi.sniper"] })).toBe(true);
      // The printed exclusion names only the Silent Master, selection included.
      expect(entryReachesProfile(crossbow, { id: "silent-master", type: "hero", variants: ["modus-operandi.sniper"] })).toBe(false);
      // A bearer without the selection never receives the conditional line.
      expect(entryReachesProfile(crossbow, { id: "poisoner", type: "hero", variants: [] })).toBe(false);
    });

    it("records the product boundary: neither band publishes a selectable variant", () => {
      // Warband Manager carries the selection in `identity.mercenary_variant`,
      // which names a published warband variant. These two bands publish none,
      // so the campaign cannot configure a House or a Modus Operandi; the
      // canonical-profile artefact therefore keeps the conditional lines out of
      // every access list instead of offering them to the wrong bearer.
      expect(warbandVariants(reader, HOUSE)).toEqual([]);
      expect(warbandVariants(reader, SILENCE)).toEqual([]);
      const commander = facts(HOUSE, "commander");
      const offered = new Set((commander.equipment_access ?? []).map((offer) => offer.item_id));
      expect(offered.has("crossbow")).toBe(true);
      for (const itemId of ["rapier", "sword_breaker", "crossbow_pistol", "long_bow", "house_guard_plate_armour", "pavise"]) {
        expect(offered.has(itemId), itemId).toBe(false);
      }
      // An unconditional line still decides normally through the campaign route.
      expect(equipmentIssueFor(reader, commander, "crossbow")).toBeNull();
      expect(equipmentIssueFor(reader, commander, "rapier")?.code).toBe("equipment_not_permitted");

      for (const profileId of ["poisoner", "silent-master"]) {
        const profile = facts(SILENCE, profileId);
        const items = new Set((profile.equipment_access ?? []).map((offer) => offer.item_id));
        for (const itemId of ["crossbow", "long_bow"]) expect(items.has(itemId), `${profileId}:${itemId}`).toBe(false);
        // The brotherhood's own unconditional line stays offered.
        expect(items.has("crossbow_pistol")).toBe(true);
      }
    });
  });

  describe("Mootlanders: the Halfling Equipment List concession", () => {
    it("offers the additionally purchasable pistol and keeps the list in force", () => {
      const elder = facts(MOOT, "moot-elder");
      const offered = new Set((elder.equipment_access ?? []).map((offer) => offer.item_id));
      // The referenced list is the profile's own declared list, and the clause's
      // additional item is published as its canonical mechanic concession.
      expect(elder.equipment_lists).toEqual(["mootlander-equipment-list"]);
      expect(offered.has("weapon.pistol")).toBe(true);
      expect(offered.has("sling")).toBe(true);
      // The list restrictions stay in force: an item on no list is refused.
      expect(equipmentIssueFor(reader, elder, "weapon.pistol")).toBeNull();
      expect(equipmentIssueFor(reader, elder, "axe")?.code).toBe("equipment_not_permitted");
      // The concession reaches no other profile of the band.
      expect(equipmentIssueFor(reader, facts(MOOT, "master-chef"), "weapon.pistol")?.code)
        .toBe("equipment_not_permitted");
    });
  });

  describe("Snotling Shoota Teams: the one-missile-weapon possession bound", () => {
    it("publishes the bound with its printed exemptions on the named profile only", () => {
      expect(row(SNOTLINGS, "shoota-teams")["missile_weapon_limit"]).toEqual([
        { rule_id: "shoota-teams--one-missile-weapon", maximum: 1, exempt_item_ids: ["small_pebble", "slingshot"] },
      ]);
      expect(row(SNOTLINGS, "scouts")["missile_weapon_limit"]).toBeUndefined();
    });

    it("exempts pebbles and slingshots and counts units, not distinct ids", () => {
      const team = facts(SNOTLINGS, "shoota-teams");
      expect(memberEquipmentIssuesFor(reader, team, ["small_pebble", "slingshot", "small_pebble"])).toEqual([]);
      expect(memberEquipmentIssuesFor(reader, team, ["crossbow"])).toEqual([]);
      const two = memberEquipmentIssuesFor(reader, team, ["crossbow", "blunderbuss", "small_pebble"]);
      expect(two.map((issue) => issue.code)).toEqual(["equipment_limit_exceeded"]);
      expect(two[0]?.rule_id).toBe("shoota-teams--one-missile-weapon");
      expect(two[0]?.message).toContain("besides small_pebble, slingshot");
      expect(memberEquipmentIssuesFor(reader, team, ["crossbow", "crossbow"]).length).toBe(1);
      // The bound belongs to the team, never to the band's other profiles.
      expect(memberEquipmentIssuesFor(reader, facts(SNOTLINGS, "scouts"), ["crossbow", "blunderbuss"]))
        .toEqual([]);
    });
  });

  describe("Dame of the Mare: the intrinsic ancient armour", () => {
    it("publishes the armour as fixed equipment no armour line replaces", () => {
      const dame = facts(MARE, "dame-of-the-mare");
      expect(dame.fixed_equipment).toEqual(["dame_ancient_armour"]);
      expect(equipmentIssueFor(reader, dame, "dame_ancient_armour")).toBeNull();
      for (const itemId of ["light_armour", "heavy_armour"]) {
        expect(equipmentIssueFor(reader, dame, itemId)?.code, itemId).toBe("equipment_not_permitted");
      }
      // The armour is the Dame's own line, not a band-wide fact.
      expect(facts(MARE, "gallant").fixed_equipment).toEqual([]);
    });
  });

  describe("Ghutani Flagellants: the Townsmen note is a list reference", () => {
    it("realises it as the declared list instead of inventing a prohibition", () => {
      const flagellants = facts(GHUTANI, "flagellants");
      const townsmen = facts(GHUTANI, "townsmen");
      expect(flagellants.equipment_lists).toEqual(["townsmen-equipment-list"]);
      expect((flagellants.equipment_access ?? []).map((offer) => offer.item_id).sort())
        .toEqual((townsmen.equipment_access ?? []).map((offer) => offer.item_id).sort());
      expect(flagellants.equipment_forbids).toEqual([]);
      // The printed access decides both ways.
      expect(equipmentIssueFor(reader, flagellants, "sword")).toBeNull();
      expect(equipmentIssueFor(reader, flagellants, "bow")?.code).toBe("equipment_not_permitted");
    });
  });
});
