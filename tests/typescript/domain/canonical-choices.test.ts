import { describe, expect, it } from "vitest";
import { configuredProfile, profileFactsProjection, selectableRuleOptions, specialRuleOptions,
  equipmentSetIssues, selectionDecisions, validateConstruction, type BandPackage, type Catalogue, type ConstructionContext } from "@domain/eligibility/index";

const pack: BandPackage = {
  band: { id: "local" }, profiles: [], equipment_lists: [], special_rules: [{
    id: "teeny-hands", applies_to: { profile_ids: ["runt"], profile_types: ["henchman"] },
    runtime: { grant: "profile", implemented: "YES" }, bindings: [{ id: "profile.equipment-restrictions",
      parameters: { max_active_one_handed_weapons: 1, forbids: "armour" } }],
  }, { id: "hero-skill", kind: "warband_skill", applies_to: { profile_ids: ["runt"], profile_types: ["hero"] },
    runtime: { grant: "selectable" } },
  { id: "local-ability", kind: "profile_ability", applies_to: { profile_ids: ["runt"] }, runtime: { grant: "selectable" } }],
};
const profile = { id: "runt", type: "henchman", rule_ids: ["teeny-hands"] };
const catalogue: Catalogue = { packages: {}, foreign_packages: {}, mechanics: {}, mappings: {}, skills: {} };
function context(promoted = false): ConstructionContext {
  return { profile: profileFactsProjection({ pack, profile: configuredProfile(profile, promoted ? ["promotion.hero"] : []) }),
    items: { sword: { kind: "close-combat-weapon", mechanic_id: "weapon.sword", tags: [], hands: 1 },
      staff: { kind: "close-combat-weapon", mechanic_id: "weapon.double-handed", tags: [], hands: 2 } },
    skills: {}, slots: { main_weapon_id: "sword" }, possession: ["sword", "staff"] };
}

describe("L05 shared configured recipient and active-position contract", () => {
  it("uses Skull Busta's shared active-loadout restrictions in batch decisions", () => {
    const input: ConstructionContext = { ...context(),
      profile: { ...context().profile, active_weapon_limit: undefined, equipment_access: null, equipment_forbids: [] },
      skills: {}, items: {
        skull_busta: { kind: "close-combat-weapon", mechanic_id: "weapon.skull-busta", tags: [], hands: 1 },
        club: { kind: "close-combat-weapon", mechanic_id: "weapon.mace", tags: [], hands: 1 },
        shield: { kind: "shield-or-defence", mechanic_id: "defence.shield", tags: [], hands: 1 },
      }, possession: ["skull_busta"], slots: { main_weapon_id: "skull_busta" },
    };
    expect(validateConstruction(input)).toEqual([]);
    expect(validateConstruction({ ...input, slots: { ...input.slots, off_hand_id: "shield" } })).toEqual([]);
    const mounted = { ...input, operation: { mounted: true } };
    expect(validateConstruction(mounted)[0]?.message).toContain("while mounted");
    expect(validateConstruction({ ...mounted, slots: { main_weapon_id: "club" } })).toEqual([]);
    expect(selectionDecisions(input, [{ kind: "add", id: "club", slot: "off" }])[0]?.allowed).toBe(false);
    expect(selectionDecisions(input, [{ kind: "add", id: "club", slot: "extra" }])[0]?.allowed).toBe(false);
    expect(selectionDecisions(input, [{ kind: "add", id: "shield", slot: "off" }])[0]?.allowed).toBe(true);
    expect(validateConstruction({ ...input, slots: { main_weapon_id: "club", off_hand_id: "skull_busta" } })[0]?.message)
      .toContain("main weapon");
  });
  it("exempts a Cleric from the compulsory bow without exempting the missile limit", () => {
    const input = { profile: { band_id: "outlaws", profile_id: "cleric" },
      limits: { required_tag: "bow", exempt_profile_ids: ["cleric"], max_missile_weapons: 1 } };
    const bow = { item_id: "bow", item: { kind: "ranged-weapon", mechanic_id: null, tags: ["bow"] } };
    expect(equipmentSetIssues({ ...input, items: [] })).toEqual([]);
    expect(equipmentSetIssues({ ...input, items: [bow] })).toEqual([]);
    expect(equipmentSetIssues({ ...input, items: [bow, bow] }).map(i => i.code)).toEqual(["equipment_limit_exceeded"]);
    expect(equipmentSetIssues({ ...input, profile: { ...input.profile, profile_id: "bandit-leader" }, items: [] })
      .map(i => i.code)).toEqual(["equipment_required_missing"]);
  });
  it("counts identical weapons in two occupied slots and never holstered possessions", () => {
    const input = context();
    expect(validateConstruction(input)).toEqual([]);
    const dual = { ...input, slots: { main_weapon_id: "sword", off_hand_id: "sword" } };
    expect(validateConstruction(dual).map(i => i.code)).toEqual(["equipment_limit_exceeded"]);
    expect(validateConstruction(dual)[0]?.rule_id).toBe("teeny-hands");
  });
  it("checks the resulting active slots of the proposal", () => {
    const decisions = selectionDecisions(context(), [{ kind: "add", id: "sword", slot: "off" }]);
    expect(decisions[0]?.allowed).toBe(false);
    expect(decisions[0]?.issues.map(i => i.code)).toEqual(["equipment_limit_exceeded"]);
    expect(selectionDecisions(context(), [{ kind: "replace", id: "sword", slot: "main" }])[0]?.allowed).toBe(true);
  });
  it("uses declared hands rather than counting every weapon as one-handed", () => {
    expect(validateConstruction({ ...context(), slots: { main_weapon_id: "staff" } })).toEqual([]);
  });
  it("removes the entire Runt restriction for a supplied promoted type without mutating the source", () => {
    const promoted = context(true);
    expect(promoted.profile.active_weapon_limit).toBeUndefined();
    expect(promoted.profile.equipment_forbids).toEqual([]);
    expect(validateConstruction({ ...promoted, slots: { main_weapon_id: "sword", off_hand_id: "sword" } })).toEqual([]);
    expect(profile.type).toBe("henchman");
  });
  it("honours the same id AND type recipients for offerings", () => {
    expect(specialRuleOptions(pack, profile, catalogue)).toEqual([]);
    expect(specialRuleOptions(pack, configuredProfile(profile, ["promotion.hero"]), catalogue)).toEqual(["hero-skill"]);
    expect(specialRuleOptions(pack, { id: "other", type: "hero" }, catalogue)).toEqual([]);
    expect(selectableRuleOptions(pack, profile)).toEqual(["local-ability"]);
    expect(selectableRuleOptions(pack, { id: "other", type: "hero" })).toEqual([]);
  });
  it("rejects applying promotion to an animal and malformed active counts", () => {
    expect(() => configuredProfile({ id: "animal", type: "animal" }, ["promotion.hero"])).toThrow("Henchman");
    const malformed = { ...pack, special_rules: [{ ...pack.special_rules[0]!, bindings: [{
      id: "profile.equipment-restrictions", parameters: { max_active_one_handed_weapons: true } }] }] };
    expect(() => profileFactsProjection({ pack: malformed, profile })).toThrow("invalid active");
  });
});
