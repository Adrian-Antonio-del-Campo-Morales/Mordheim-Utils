import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as eligibility from "@domain/eligibility/index";

interface Case { name: string; operation: "equipmentIssue" | "skillIssue" | "equipmentSetIssues"; args: unknown[]; codes: string[] }
const cases: Case[] = JSON.parse(readFileSync(new URL("../../fixtures/eligibility/decisions.json", import.meta.url), "utf8"));

describe("shared browser and desktop decision contract", () => {
  for (const row of cases) it(row.name, () => {
    const invoke = eligibility[row.operation] as (...args: unknown[]) => eligibility.EligibilityIssue | readonly eligibility.EligibilityIssue[] | null;
    const result = invoke(...row.args);
    const issues = Array.isArray(result) ? result : result ? [result] : [];
    expect(issues.map((issue: eligibility.EligibilityIssue) => issue.code)).toEqual(row.codes);
  });
});

/**
 * Printed per-entry recipients ('Heroes only', 'Halfling Cooks only') travel on
 * the equipment entry itself, so the offering layer and every decision read one
 * fact. The embedded Python suite (`tests/python/construction/test_shared_eligibility.py`)
 * runs the same fixture through MiniRacer.
 */
interface RecipientCase {
  name: string;
  package: eligibility.BandPackage;
  profile: eligibility.EditorialProfile;
  offers: string[];
}
const recipients: RecipientCase[] = JSON.parse(readFileSync(
  new URL("../../fixtures/eligibility/entry-recipients.json", import.meta.url), "utf8"));
const emptyCatalogue = { packages: {}, foreign_packages: {}, mechanics: {}, mappings: {}, skills: {} };

describe("printed entry recipients", () => {
  for (const row of recipients) it(row.name, () => {
    const facts = eligibility.profileFactsProjection({ pack: row.package, profile: row.profile, catalogue: emptyCatalogue });
    expect((facts.equipment_access ?? []).map((offer) => offer.item_id)).toEqual(row.offers);
  });
});
