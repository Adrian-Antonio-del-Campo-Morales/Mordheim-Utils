import { describe, expect, it } from "vitest";
import { validateConstruction } from "@domain/eligibility/index";
import type { Catalogue, ConstructionContext } from "@domain/eligibility/index";
import { constructionCall, installCatalogue } from "@domain/eligibility/bridge";

const bow = { kind: "ranged-weapon", mechanic_id: "weapon.bow", tags: ["bow"] };
const sword = { kind: "close-combat-weapon", mechanic_id: "weapon.sword", tags: [] };
const catalogue: Catalogue = {
  packages: {}, foreign_packages: {}, mechanics: {}, mappings: {}, skills: {},
  items: { bow, sword },
};
const context: ConstructionContext = {
  profile: {
    band_id: "fixture", profile_id: "hero", fixed_equipment: [],
    equipment_access: [{ item_id: "weapon.sword" }], equipment_forbids: [],
    skill_access: ["combat"], skill_lists: [],
  },
  items: {}, skills: {}, selections: [], slots: { main_weapon_id: "weapon.fist" },
};
const key = "construction-validation-transport";
installCatalogue(key, catalogue);

describe("catalogue-backed construction validation", () => {
  it("does not validate unselected lookup entries as equipment", () => {
    expect(validateConstruction({ ...context, items: { bow, sword } })).toEqual([]);
    expect(constructionCall("validateConstruction", key, context)).toEqual([]);
  });

  it("still refuses selected and owned items outside access", () => {
    for (const build of [
      { ...context, selections: [{ id: "weapon.bow", kind: "equipment" }] },
      { ...context, possession: ["weapon.bow"] },
    ]) {
      const issues = constructionCall("validateConstruction", key, build) as
        ReturnType<typeof validateConstruction>;
      expect(issues.map((issue) => [issue.code, issue.subject_ids.at(-1)]))
        .toEqual([["equipment_not_permitted", "weapon.bow"]]);
    }
  });

  it("does not let an unselected bow satisfy a mandatory choice", () => {
    const missing = { ...context, limits: { required_tag: "bow" } };
    expect((constructionCall("validateConstruction", key, missing) as
      ReturnType<typeof validateConstruction>).map((issue) => issue.code))
      .toEqual(["equipment_required_missing"]);
  });

  it("allows draft validation explicitly, without weakening confirmation", () => {
    const missing = { ...context, limits: { required_tag: "bow" } };
    expect(constructionCall("validateConstruction", key, missing, [], { draft: true }))
      .toEqual([]);
  });
});
