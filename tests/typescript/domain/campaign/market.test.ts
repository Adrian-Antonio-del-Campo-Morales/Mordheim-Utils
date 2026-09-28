/**
 * T10 — trading-post availability.
 *
 * Two market obligations arrived from T09:
 * - `repeater_pistol_moh` is a `common` entry of the Masters of Horror whose
 *   printed clause is "Masters of Horror only. Cost 25 + 3D6 gc." Publishing the
 *   clause's scope lets that warband buy it while every other warband keeps being
 *   refused;
 * - `runic_attlas_plate_mail` is `not_sold`: the source prints it as a unique
 *   find of the exploration chart, so the market must refuse it. It reaches the
 *   warband through the chart instead (the row publishes the canonical
 *   `item_id`).
 *
 * Purity: plain Node, the real reader for the published rows plus fixtures.
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { readArtefactDocument } from "../../../support/kb-artefact";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { marketAssignmentIssueFor, marketAvailabilityIssueFor } from "@domain/campaign/kernel/market";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      // The build output first: T10's evidence is the freshly generated
      // artefact, while `outputs/` still holds the pre-T10 copy T12 regenerates.
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

const MASTERS = "masters-of-horror-sylv";
const OTHER = "adventurers-kaz";

describe("T10 market availability verdict", () => {
  it("evaluates a scoped `condition` like a warband restriction", () => {
    const offer = {
      availability: { kind: "common" },
      restrictions: [
        { type: "condition", band_ids: [MASTERS], note: "Masters of Horror only. Cost 25 + 3D6 gc." },
      ],
    };
    expect(marketAvailabilityIssueFor({ offer, band_id: MASTERS, groups: [], item_name: "Repeater Pistol" })).toBeNull();
    const refused = marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: [], item_name: "Repeater Pistol" });
    expect(refused?.code).toBe("market_warband_only");
    expect(refused?.note).toContain("Masters of Horror only");
  });

  it("evaluates a group-scoped clause and a forbidden one", () => {
    const grouped = { availability: { kind: "common" }, restrictions: [{ type: "condition", groups: ["warband-group.human"] }] };
    expect(marketAvailabilityIssueFor({ offer: grouped, band_id: OTHER, groups: ["warband-group.human"], item_name: "Helm" })).toBeNull();
    expect(marketAvailabilityIssueFor({ offer: grouped, band_id: OTHER, groups: ["warband-group.undead"], item_name: "Helm" })?.code)
      .toBe("market_warband_only");
    const forbidden = { availability: { kind: "common" }, restrictions: [{ type: "warband_forbidden", band_ids: [MASTERS] }] };
    expect(marketAvailabilityIssueFor({ offer: forbidden, band_id: MASTERS, groups: [], item_name: "Holy Water" })?.code)
      .toBe("market_warband_forbidden");
    expect(marketAvailabilityIssueFor({ offer: forbidden, band_id: OTHER, groups: [], item_name: "Holy Water" })).toBeNull();
  });

  it("never drops an unscoped note because another restriction carries a scope", () => {
    // The printed Chainsaw Sword pattern: `warband_only` plus the same clause
    // written again as prose. The scope is satisfied, but the note still says
    // something the catalogue has not published as data, so the buy is refused
    // with its own code instead of being waved through.
    const offer = {
      availability: { kind: "common" },
      restrictions: [
        { type: "warband_only", band_ids: [MASTERS] },
        { type: "condition", note: "Masters of Horror only. Cost 15 + D6 gc." },
      ],
    };
    const issue = marketAvailabilityIssueFor({ offer, band_id: MASTERS, groups: [], item_name: "Chainsaw Sword" });
    expect(issue?.code).toBe("market_condition_unstructured");
    expect(issue?.note).toContain("Cost 15 + D6 gc");
    expect(marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: [], item_name: "Chainsaw Sword" })?.code)
      .toBe("market_warband_only");
  });

  it("accepts the same entry once the note is declared as a repetition, or structured", () => {
    const repeated = {
      availability: { kind: "common" },
      restrictions: [
        { type: "warband_only", band_ids: [MASTERS] },
        { type: "condition", note: "Masters of Horror only. Cost 15 + D6 gc.", structure: { repeats_entry: true } },
      ],
    };
    expect(marketAvailabilityIssueFor({ offer: repeated, band_id: MASTERS, groups: [], item_name: "Chainsaw Sword" })).toBeNull();
    // A structured creation-only clause is evaluated instead of refused.
    const creation = {
      availability: { kind: "common" },
      restrictions: [
        { type: "warband_only", band_ids: [MASTERS] },
        { type: "condition", note: "May only be purchased when the warband is created", structure: { creation_only: true } },
      ],
    };
    expect(marketAvailabilityIssueFor({ offer: creation, band_id: MASTERS, groups: [], item_name: "Standard" })?.code)
      .toBe("market_creation_only");
    expect(marketAvailabilityIssueFor({ offer: creation, band_id: MASTERS, groups: [], item_name: "Standard", at_creation: true })).toBeNull();
  });

  it("carries the recipient-scoped half of a structured condition to the assignment route", () => {
    const offer = {
      availability: { kind: "common" },
      restrictions: [
        { type: "warband_only", groups: ["warband-group.undead"] },
        { type: "condition", note: "Vampires, Necromancers and Grave Guards only", structure: { profile_ids: ["vampire", "grave-guards"] } },
      ],
    };
    // The purchase itself is a stash copy: it decides availability, not recipients.
    expect(marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: ["warband-group.undead"], item_name: "Nightmare" })).toBeNull();
    const allowed = marketAssignmentIssueFor(offer, { profile_id: "vampire", kind: "hero", skill_ids: [] }, "Nightmare");
    expect(allowed).toBeNull();
    const refused = marketAssignmentIssueFor(offer, { profile_id: "dire-wolves", kind: "henchman", skill_ids: [] }, "Nightmare");
    expect(refused?.message).toContain("vampire");
  });

  it("keeps refusing an unscoped editorial note", () => {
    const offer = { availability: { kind: "common" }, restrictions: [{ type: "condition", note: "Ask the campaign organiser." }] };
    const issue = marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: [], item_name: "Oddity" });
    expect(issue?.code).toBe("market_condition_unstructured");
    expect(issue?.note).toContain("campaign organiser");
  });

  it("refuses an item that is not a common market entry", () => {
    const rare = { availability: { kind: "rare" }, restrictions: [] };
    expect(marketAvailabilityIssueFor({ offer: rare, band_id: OTHER, groups: [], item_name: "Rare Blade" })?.code)
      .toBe("market_not_common");
    const notSold = { availability: { kind: "not_sold" }, restrictions: [{ type: "condition", note: "Unique: found on the chart." }] };
    const issue = marketAvailabilityIssueFor({ offer: notSold, band_id: OTHER, groups: [], item_name: "Att'la's Plate Mail" });
    expect(issue?.code).toBe("market_not_common");
    expect(issue?.message).toContain("not sold");
  });
});

describe.skipIf(!ARTEFACT_PATH)("T10 market obligations against the published catalogue", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader = ArtefactKnowledgeReader.from(artefact);
  const offers = (artefact.campaign?.["trading-post"]?.items ?? []) as Readonly<Record<string, unknown>>[];

  it("reconciles the 31 unscoped conditions of a scoped entry: structured, blocked or refused, never dropped", () => {
    // The exact case the review named: an entry whose scope comes from one
    // restriction and whose printed clause is written again as an unscoped
    // `condition`. The old verdict read `scoped` once for the whole entry and
    // dropped the note; the reconciliation decides every one of the 31.
    const structured: string[] = [];
    const blocked: string[] = [];
    const refused: string[] = [];
    for (const offer of offers) {
      const restrictions = (offer["restrictions"] ?? []) as Readonly<Record<string, unknown>>[];
      const scope = restrictions.find((row) => row["band_ids"] || row["groups"]);
      const conditions = restrictions.filter(
        (row) => row["type"] === "condition" && !row["band_ids"] && !row["groups"],
      );
      if (!scope || conditions.length === 0) continue;
      const itemId = String(offer["item_id"]);
      // A published `structure` is the machine-readable form of the clause; it
      // decides the purchase, or (for the buyer-scoped keys) travels to the
      // assignment route the rarity rule also gates.
      if (conditions.every((row) => row["structure"] !== undefined)) {
        structured.push(itemId);
        continue;
      }
      // Without one, an entry that is rare or not sold is refused by
      // availability before its restrictions: the clause is explicitly blocked,
      // never dropped.
      if ((offer["availability"] as { kind?: string } | undefined)?.kind !== "common") {
        blocked.push(itemId);
        continue;
      }
      // With the scope satisfied, only the condition itself can refuse the buy,
      // and a clause the catalogue does not publish structurally is reported
      // with its own code instead of being waved through.
      const bandId = ((scope["band_ids"] as string[] | undefined) ?? [])[0] ?? OTHER;
      const groups = (scope["groups"] as string[] | undefined) ?? [];
      const issue = marketAvailabilityIssueFor({ offer, band_id: bandId, groups, item_name: itemId });
      expect(issue?.code, itemId).toBe("market_condition_unstructured");
      refused.push(itemId);
    }
    expect([...structured].sort()).toEqual([
      "bearcloak",
      "blessed_bolts",
      "chainsaw_sword",
      "chest_talon",
      "darksteel_blade",
      "electric_trident",
      "finger_pendant",
      "nightmare",
      "pigback_mount",
      "pry_bar",
      "shield_of_sigmar",
      "silver_tip_stake",
      "slingshot",
      "small_pebble",
      "society_familiar",
      "staff_of_damnation",
      "standard_of_nagarythe",
      "unholy_relic",
      "whirling_blades",
    ]);
    expect([...blocked].sort()).toEqual([
      "amulet_of_the_moon",
      "beastwhip",
      "black_lotus",
      "blessed_water",
      "blowpipe",
      "chaos_steed",
      "dark_elf_blade_weapon_upgrade",
      "dark_venom",
      "temple_dog",
      "thingcatcher",
    ]);
    // The two whose printed clause has no vocabulary yet (a second-copy price,
    // a weapon-upgrade price) are refused with `market_condition_unstructured`:
    // reported to the KB, never silently ignored.
    expect([...refused].sort()).toEqual(["poisoned_weapon", "sharp_stuff"]);
    expect(structured.length + blocked.length + refused.length).toBe(31);
  });

  it("publishes the Masters of Horror clause as a scope on the Repeater Pistol (Masters of Horror)", () => {
    const offer = offers.find((row) => row["item_id"] === "repeater_pistol_moh")!;
    expect(offer).toBeDefined();
    expect(offer["availability"]).toEqual({ kind: "common" });
    expect(offer["price"]).toMatchObject({ base_gc: 25, optional_variable_cost: { dice: { count: 3, sides: 6 } } });
    const scope = offer["restrictions"] as Readonly<Record<string, unknown>>[];
    expect(scope.some((row) => row["type"] === "condition" && (row["band_ids"] as string[])?.includes(MASTERS))).toBe(true);
    expect(marketAvailabilityIssueFor({ offer, band_id: MASTERS, groups: [], item_name: "Repeater Pistol" })).toBeNull();
    expect(marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: [], item_name: "Repeater Pistol" })?.code)
      .toBe("market_warband_only");
    // The item the profile lists and the market entry are the same canonical id.
    expect(reader.queryKnowledge({ id: { kind: "item_id", value: "repeater_pistol_moh" } }).ok).toBe(true);
  });

  it("refuses the unique Att'la's Plate Mail at the market and grants it on the chart", () => {
    const offer = offers.find((row) => row["item_id"] === "runic_attlas_plate_mail")!;
    expect(offer["availability"]).toEqual({ kind: "not_sold" });
    expect(offer["price"]).toBeNull();
    expect(marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: [], item_name: "Att'la's Plate Mail" })?.code)
      .toBe("market_not_common");
    const results = (artefact.campaign?.["exploration-and-income"]?.magical_artefacts?.results ?? []) as Readonly<Record<string, unknown>>[];
    const row = results.find((entry) => entry["id"] === "campaign.magical-artefact.attlas-plate-mail")!;
    // The chart row publishes the canonical item id, so the find enters the
    // warband as the catalogue item and not as a synthesised artefact id.
    expect(row["item_id"]).toBe("runic_attlas_plate_mail");
    expect(row["roll"]).toBe("3");
  });
});
