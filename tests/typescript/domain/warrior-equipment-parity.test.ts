import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { warriorEquipmentRestriction } from "@domain/eligibility/index";

interface Case {
  name: string;
  args: Parameters<typeof warriorEquipmentRestriction>[0];
  expected: string | null;
}
// Captured from the Python confirmation gates before deleting their table.
// Both the direct export and the real embedded adapter consume these cases.
const cases: Case[] = JSON.parse(readFileSync(
  new URL("../../fixtures/eligibility/warrior-equipment.json", import.meta.url), "utf8"));

describe("campaign equipment migration parity", () => {
  for (const row of cases) it(row.name, () => {
    expect(warriorEquipmentRestriction(row.args)).toBe(row.expected);
  });
});
