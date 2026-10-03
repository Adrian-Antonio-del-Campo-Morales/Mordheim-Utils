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
