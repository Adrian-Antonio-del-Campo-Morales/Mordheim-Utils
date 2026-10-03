import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import * as eligibility from "@domain/eligibility/index";
import type { ConstructionContext, SelectionProposal } from "@domain/eligibility/index";

/**
 * The maintained module is the single interpretation of these decisions. The
 * embedded Python suite (`tests/python/construction/test_construction_context_parity.py`)
 * runs the same fixture through MiniRacer, so an equivalent context and
 * proposal set must produce equivalent decisions on both entry points.
 */
interface Case {
  name: string;
  context: ConstructionContext;
  proposals: SelectionProposal[];
  allowed: boolean[];
  issue_codes: string[][];
  report_codes: string[][];
  validation_codes: string[];
}
const cases: Case[] = JSON.parse(readFileSync(
  new URL("../../fixtures/eligibility/construction-context.json", import.meta.url), "utf8"));

describe("shared construction context contract", () => {
  for (const row of cases) {
    it(`selectionDecisions: ${row.name}`, () => {
      const decisions = eligibility.selectionDecisions(row.context, row.proposals);
      expect(decisions.map((decision) => decision.allowed)).toEqual(row.allowed);
      expect(decisions.map((decision) => decision.issues.map((issue) => issue.code)))
        .toEqual(row.issue_codes);
      expect(decisions.map((decision) => decision.reports.map((issue) => issue.code)))
        .toEqual(row.report_codes);
    });
    it(`validateConstruction: ${row.name}`, () => {
      const issues = eligibility.validateConstruction(row.context, { draft: true });
      expect(issues.map((issue) => issue.code)).toEqual(row.validation_codes);
    });
  }

  it("an informational code never blocks a legal choice", () => {
    expect(eligibility.issueIsInformational("equipment_unknown_item")).toBe(true);
    expect(eligibility.issueIsInformational("construction_clause_unstructured")).toBe(true);
    expect(eligibility.issueIsInformational("equipment_forbidden")).toBe(false);
    expect(eligibility.issueIsInformational("equipment_slot_occupied")).toBe(false);
  });

  it("a batch returns one decision per proposal, in order", () => {
    const context = cases[0]!.context;
    const decisions = eligibility.selectionDecisions(context, [
      { kind: "add", id: "sword", selection: "equipment", slot: "main" },
      { kind: "add", id: "dagger", selection: "equipment", slot: "off" },
      { kind: "remove", id: "dagger", selection: "equipment" },
    ]);
    expect(decisions.map((decision) => decision.proposal.id)).toEqual(["sword", "dagger", "dagger"]);
  });
});
