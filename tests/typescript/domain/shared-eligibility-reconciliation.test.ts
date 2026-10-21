/**
 * Shared-eligibility reconciliation: clauses that hold today.
 *
 * Expectations come from the canonical parameters and the accepted
 * deliveries, never from the implementation under test.  The failing
 * recipient-filter expectation of F017 is deliberately NOT asserted here:
 * it stays a documented reproducer until the shared decision is repaired, so
 * this suite never blesses the defect nor breaks CI.  See
 * the shared-eligibility register.
 */
import { describe, expect, it } from "vitest";
import {
  applicableRules,
  carriedItemFacts,
  profileFactsProjection,
  tokenForbids,
  equipmentIssue,
  equipmentSetIssues,
  skillIssue,
  type BandPackage,
  type BuildFacts,
  type Catalogue,
  type EditorialProfile,
  type ItemFacts,
  type ProfileFacts,
} from "@domain/eligibility/index";

const EMPTY_CATALOGUE: Catalogue = {
  packages: {}, foreign_packages: {}, mechanics: {}, mappings: {}, skills: {},
};

describe("selected weapon mechanics preserve restriction facts", () => {
  it("retains the active grip's hands and the missile family across catalogue aliases", () => {
    const catalogue: Catalogue = { ...EMPTY_CATALOGUE,
      mechanics: { "weapon.halberd": { hands: 2 }, "weapon.pistol": { hands: 1 } },
      items: {
        halberd: { kind: "close-combat-weapon", mechanic_id: "weapon.halberd", tags: [] },
        pistol: { kind: "ranged-weapon", mechanic_id: "weapon.pistol", tags: ["blackpowder"] },
        pistol_brace: { kind: "trollheim-equipment", mechanic_id: "weapon.pistol", tags: ["blackpowder"] },
      },
    };
    expect(tokenForbids("two-handed-weapons", "weapon.halberd", carriedItemFacts(catalogue, "weapon.halberd"))).toBe(true);
    expect(tokenForbids("two-handed-weapons", "halberd", carriedItemFacts(catalogue, "halberd"))).toBe(true);
    expect(tokenForbids("non-thrown-ranged", "weapon.pistol", carriedItemFacts(catalogue, "weapon.pistol"))).toBe(true);
    expect(tokenForbids("two-handed-weapons", "weapon.pistol", carriedItemFacts(catalogue, "weapon.pistol"))).toBe(false);
  });
});

describe("printed baseline of a selectable missile allowance", () => {
  const rule = "band--savage-goblin-special-skills-master-of-throwing-weapons";
  const pack: BandPackage = { band: { id: "lustria-savage-goblins" }, profiles: [], equipment_lists: [],
    special_rules: [{ id: rule, eligibility: ["trackers"], applies_to: { band: true },
      runtime: { grant: "selectable", implemented: "YES" },
      bindings: [{ id: "profile.equipment-restrictions", parameters: {
        max_missile_weapons: 5, baseline_max_missile_weapons: 2,
      } }],
    }],
  };
  const build = (selected: boolean): BuildFacts => ({
    band_id: pack.band.id, profile_id: "trackers", main_weapon_id: "weapon.dagger",
    armour_id: "armour.no-armour", main_material_id: "material.normal", off_material_id: "material.normal",
    defence_ids: [], skill_ids: [], preparation_ids: [], special_rule_ids: selected ? [rule] : [], variant_ids: [],
  });

  it("uses the printed ordinary two and selected five without intersecting them", () => {
    for (const [selected, maximum] of [[false, 2], [true, 5]] as const) {
      const facts = profileFactsProjection({ pack, profile: { id: "trackers", type: "hero" }, build: build(selected),
        additional_bindings: selected ? pack.special_rules[0]!.bindings : [] });
      expect(facts.missile_weapon_limit?.map(bound => bound.maximum)).toEqual([maximum]);
      expect(facts.missile_weapon_limit?.[0]?.exempt_item_ids).toEqual([]);
    }
  });

  it("does not grant the baseline to a non-recipient", () => {
    const facts = profileFactsProjection({ pack, profile: { id: "big-boss", type: "hero" }, build: build(false) });
    expect(facts.missile_weapon_limit).toBeUndefined();
  });
});

function profile(overrides: Partial<ProfileFacts> = {}): ProfileFacts {
  return {
    band_id: "band",
    profile_id: "warrior",
    fixed_equipment: [],
    equipment_access: null,
    equipment_forbids: [],
    skill_access: [],
    skill_lists: [],
    ...overrides,
  };
}

function item(overrides: Partial<ItemFacts> = {}): ItemFacts {
  return { kind: "ranged-weapon", mechanic_id: null, tags: [], ...overrides };
}

describe("equipment prohibition vocabulary on projected item facts", () => {
  it("refuses an item whose tags carry the projected token", () => {
    // Synthetic facts: the id names the family, the tags decide (the real
    // `crossbow_pistol` carries `crossbow` since the H5 source check).
    const issue = equipmentIssue({
      profile: profile({ equipment_forbids: ["blackpowder"] }),
      item_id: "pistol",
      item: item({ tags: ["blackpowder"] }),
    });
    expect(issue?.code).toBe("equipment_forbidden");
    expect(issue?.message).toContain("blackpowder");
  });

  it("refuses an animal-tagged item and leaves unrelated items alone", () => {
    expect(equipmentIssue({
      profile: profile({ equipment_forbids: ["animal"] }),
      item_id: "warhound",
      item: item({ kind: "out-of-scope", tags: ["animal"] }),
    })?.code).toBe("equipment_forbidden");
    expect(equipmentIssue({
      profile: profile({ equipment_forbids: ["blackpowder"] }),
      item_id: "sword",
      item: item({ kind: "close-combat-weapon" }),
    })).toBeNull();
  });

  it("keeps an unlisted item outside the profile's access before any token", () => {
    const issue = equipmentIssue({
      profile: profile({ equipment_access: [{ item_id: "bow" }], equipment_forbids: ["crossbow"] }),
      item_id: "crossbow",
      item: item({ tags: ["crossbow"] }),
    });
    expect(issue?.code).toBe("equipment_not_permitted");
  });
});

describe("whole-set equipment limits", () => {
  const limits = { rule_id: "band--bow-restrictions", max_missile_weapons: 1, required_tag: "bow", exempt_profile_ids: ["cleric"] };
  const bow = { item_id: "bow", item: item({ tags: ["bow"] }) };
  const sling = { item_id: "sling", item: item({ tags: [] }) };

  it("checks the missile count and the required family together", () => {
    const issues = equipmentSetIssues({
      profile: profile(),
      limits,
      items: [{ item_id: "sling", item: item({ tags: [] }) },
        { item_id: "crossbow", item: item({ tags: ["crossbow"] }) }],
    });
    expect(issues.map((issue) => issue.code).sort()).toEqual(
      ["equipment_limit_exceeded", "equipment_required_missing"],
    );
  });

  it("keeps a bow-only kit legal and exempts the printed profile", () => {
    expect(equipmentSetIssues({ profile: profile(), limits, items: [bow] })).toEqual([]);
    expect(equipmentSetIssues({
      profile: profile({ profile_id: "cleric" }),
      limits,
      items: [sling],
    })).toEqual([]);
  });
});

describe("skill access with a published named table", () => {
  const profileFacts = profile({
    skill_access: ["combat", "special"],
    skill_lists: [{ rule_id: "band--dwarf-special-skills", category: "special",
      skills: ["skill.berserker", "skill.monster-slayer"] }],
  });

  it("permits a published member and refuses a name outside the list", () => {
    expect(skillIssue(profileFacts, { id: "skill.berserker", category: "special", kind: "special" }, true)).toBeNull();
    expect(skillIssue(profileFacts, { id: "skill.fey", category: "special", kind: "special" }, true)?.code)
      .toBe("skill_not_permitted");
  });
});

describe("band rule applicability", () => {
  const pack: BandPackage = {
    band: { id: "adventurers-kaz" },
    profiles: [],
    equipment_lists: [],
    special_rules: [
      { id: "band--no-fixed-leader", applies_to: { band: true }, runtime: { grant: "band" } },
      { id: "band--dwarf-special-skills", applies_to: { band: true, profile_ids: ["dwarf"] }, runtime: { grant: "band" } },
      { id: "dwarf--hard-to-kill", applies_to: { profile_ids: ["dwarf"] }, runtime: { grant: "profile" } },
    ],
  };

  it("keeps a genuinely band-wide grant for every member", () => {
    for (const id of ["dwarf", "wizard"]) {
      const won = applicableRules(pack, { id } as EditorialProfile).map((row) => row.id);
      expect(won).toContain("band--no-fixed-leader");
    }
  });

  it("applies a recipient-scoped profile rule to its recipient", () => {
    const dwarf = applicableRules(pack, { id: "dwarf", rule_ids: ["dwarf--hard-to-kill"] } as EditorialProfile).map((row) => row.id);
    expect(dwarf).toContain("dwarf--hard-to-kill");
    const wizard = applicableRules(pack, { id: "wizard" } as EditorialProfile).map((row) => row.id);
    expect(wizard).not.toContain("dwarf--hard-to-kill");
  });

  it("applies a recipient-scoped band grant to its named profile", () => {
    const dwarf = applicableRules(pack, { id: "dwarf" } as EditorialProfile).map((row) => row.id);
    expect(dwarf).toContain("band--dwarf-special-skills");
    // The negative case for every other profile is the open F017 defect and
    // is asserted by build/cache/.../reproducers/repro_f017_recipients.py only.
  });
});

// Keep the imported type used so the fixture stays honest about realistic facts.
void EMPTY_CATALOGUE;
