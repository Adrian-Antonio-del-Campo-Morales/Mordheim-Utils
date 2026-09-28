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
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { marketAvailabilityIssueFor } from "@domain/campaign/kernel/market";

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

  it("treats a prose note beside a structured scope as advisory, not blocking", () => {
    // The printed Chainsaw Sword pattern: `warband_only` plus the same clause
    // written again as prose. The scoped restriction decides.
    const offer = {
      availability: { kind: "common" },
      restrictions: [
        { type: "warband_only", band_ids: [MASTERS] },
        { type: "condition", note: "Masters of Horror only. Cost 15 + D6 gc." },
      ],
    };
    expect(marketAvailabilityIssueFor({ offer, band_id: MASTERS, groups: [], item_name: "Chainsaw Sword" })).toBeNull();
    expect(marketAvailabilityIssueFor({ offer, band_id: OTHER, groups: [], item_name: "Chainsaw Sword" })?.code)
      .toBe("market_warband_only");
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
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8"));
  const reader = ArtefactKnowledgeReader.from(artefact);
  const offers = (artefact.campaign?.["trading-post"]?.items ?? []) as Readonly<Record<string, unknown>>[];

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
