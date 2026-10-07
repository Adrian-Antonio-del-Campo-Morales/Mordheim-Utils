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
  it("an inseparable suit prohibits another suit or cloak, not shields or helmets", () => {
    const profile = { ...cases[0]!.context.profile, equipment_access: null, equipment_forbids: ["armour-suit"] };
    const allowed = [
      { kind: "armour", mechanic_id: "armour.heavy-armour", tags: [] },
      { kind: "shield-or-defence", mechanic_id: "defence.sea-dragon-cloak", tags: [] },
      { kind: "shield-or-defence", mechanic_id: "defence.shield", tags: [] },
      { kind: "shield-or-defence", mechanic_id: "defence.helmet", tags: [] },
    ].map(item => eligibility.equipmentIssue({ profile, item_id: item.mechanic_id, item }) === null);
    expect(allowed).toEqual([false, false, true, true]);
  });
  it("Tiny and Big Bully are mutually exclusive in both selection orders", () => {
    const build = { main_weapon_id: "weapon.fist", armour_id: "armour.no-armour",
      main_material_id: "material.normal", off_material_id: "material.normal",
      defence_ids: [], skill_ids: [], preparation_ids: [], variant_ids: [],
      special_rule_ids: ["bullied-goblin--frustratingly-tiny", "bigsnotz--big-bully"] };
    for (const id of build.special_rule_ids) {
      expect(eligibility.specialRuleRestriction({ build, profile: null,
        rule: { id }, native_virtue: false, starting_skills: [], stage: "prerequisites" }))
        .toBe("Frustratingly Tiny cannot be combined with Big Bully");
    }
  });
  it("a sea dragon cloak occupies armour but combines normally with a shield", () => {
    const context: ConstructionContext = {
      ...cases[0]!.context,
      profile: { ...cases[0]!.context.profile, equipment_access: null },
      items: {
        cloak: { kind: "armour", mechanic_id: "defence.sea-dragon-cloak", tags: [] },
        light: { kind: "armour", mechanic_id: "armour.light-armour", tags: [] },
        shield: { kind: "shield", mechanic_id: "defence.shield", tags: [] },
      },
      slots: { armour_id: null, defence_ids: ["cloak"], off_hand_id: "shield" },
    };
    expect(eligibility.validateConstruction(context, { draft: true })).toEqual([]);
    expect(eligibility.selectionDecisions(context, [
      { kind: "add", id: "light", selection: "equipment", slot: "armour" },
    ])[0]!.allowed).toBe(false);
    const suited = { ...context, slots: { armour_id: "light", defence_ids: [] } };
    expect(eligibility.selectionDecisions(suited, [
      { kind: "add", id: "cloak", selection: "equipment" },
    ])[0]!.allowed).toBe(false);
    expect(eligibility.validateConstruction({ ...context,
      slots: { ...context.slots, armour_id: "light" } }, { draft: true })
      .some(issue => issue.code === "equipment_combination_forbidden")).toBe(true);
  });
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


it("source-only unique hireling kit items stay owned, inactive and fail closed", () => {
  const equipment = { fixed_items: [{ item_id: "sword", quantity: { kind: "fixed", value: 1 } }],
    unique_equipment: [{ id: "private-cloak", rules: ["cloak-rule"] }] };
  const build = { main_weapon_id: "weapon.sword", armour_id: "armour.no-armour",
    main_material_id: "material.normal", off_material_id: "material.normal",
    defence_ids: [], skill_ids: [], preparation_ids: [], variant_ids: [], special_rule_ids: [] };
  const catalogue: eligibility.Catalogue = { packages: {}, foreign_packages: {}, mechanics: {},
    mappings: { sword: "weapon.sword" }, skills: {} };
  const rule = { id: "cloak-rule", runtime: { scope: "NO", implemented: "NO" }, bindings: [] };
  expect(eligibility.resolveHirelingKit(equipment, build, catalogue, [rule])).toEqual(["sword", "private-cloak"]);
  expect(() => eligibility.resolveHirelingKit(equipment, { ...build, owned_item_ids: ["sword"] }, catalogue, [rule]))
    .toThrow("complete legal printed kit");
  expect(() => eligibility.resolveHirelingKit(equipment, { ...build, main_weapon_id: "private-cloak" }, catalogue, [rule]))
    .toThrow("active combat position");
  for (const rules of [[], [rule, rule], [{ ...rule, runtime: { scope: "LATER", implemented: "NO" } }],
    [{ ...rule, runtime: { scope: "NO", implemented: "YES" } }],
    [{ ...rule, bindings: [{ kind: "mechanic", id: "mechanic.fake" }] }]]) {
    expect(() => eligibility.resolveHirelingKit(equipment, build, catalogue, rules)).toThrow("canonical combat mapping");
  }
});
