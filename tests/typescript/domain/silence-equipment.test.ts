/**
 * T13-F019 — The Silence's prohibition tokens must reach the bound-equipment stage.
 *
 * The canonical rule `silent-brotherhood-sc/band--the-silence` publishes
 * `profile.equipment-restrictions` with `forbids: [blackpowder, animal]`.
 * Expectations come from the canonical item facts (shared fixture
 * `tests/fixtures/eligibility/silence-equipment.json`, verified against the
 * live KB by the Python suite) and the accepted F035 dispositions; they never
 * come from `buildRestriction` output. The H5 source check (2026-10-04)
 * classifies `crossbow_pistol` as `crossbow`, not `blackpowder`; provenance in
 * `docs/knowledge/2a2b/tasks/T13-silence-equipment.md` section 12.
 */
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import {
  buildRestriction,
  equipmentIssue,
  tokenForbids,
  type BuildContext,
  type BuildFacts,
  type Catalogue,
  type EditorialProfile,
  type ItemFacts,
  type ProfileFacts,
} from "@domain/eligibility/index";

interface Fixture { readonly items: Readonly<Record<string, ItemFacts>> }
const { items } = JSON.parse(readFileSync(
  new URL("../../fixtures/eligibility/silence-equipment.json", import.meta.url), "utf8",
)) as Fixture;

const EMPTY_CATALOGUE: Catalogue = {
  packages: {}, foreign_packages: {}, mechanics: {}, mappings: {}, skills: {},
};
const CATALOGUE: Catalogue = { ...EMPTY_CATALOGUE, items };

const BAND = "silent-brotherhood-sc";
const PROFILE = "silent-master";
const WHO = `${BAND}/${PROFILE}`;

function context(overrides: {
  readonly forbidden?: readonly string[];
  readonly build?: Partial<BuildFacts>;
  readonly bindings?: BuildContext["profile_bindings"];
  readonly catalogue?: Catalogue;
  readonly band?: string;
  readonly profile?: string;
} = {}): BuildContext {
  const band = overrides.band ?? BAND;
  const profileId = overrides.profile ?? PROFILE;
  const forbidden = overrides.forbidden ?? ["blackpowder", "animal"];
  const bindings = overrides.bindings ?? (forbidden.length
    ? [{ id: "profile.equipment-restrictions", parameters: { forbids: [...forbidden] } }]
    : []);
  const build: BuildFacts = {
    band_id: band, profile_id: profileId, main_weapon_id: "weapon.dagger", armour_id: "armour.no-armour",
    off_hand_id: null, extra_hand_id: null, main_material_id: "material.normal", off_material_id: "material.normal",
    main_poison_id: null, off_poison_id: null, defence_ids: [], skill_ids: [], preparation_ids: [],
    special_rule_ids: [], variant_ids: [], ...overrides.build,
  };
  return {
    build,
    profile: { id: profileId } as EditorialProfile,
    package: { band: { id: band }, profiles: [], equipment_lists: [], special_rules: [] },
    catalogue: overrides.catalogue ?? CATALOGUE,
    profile_bindings: bindings,
    compiler_bindings: [],
    contracts: [],
  };
}

function neutral(forbids: readonly string[]): ProfileFacts {
  return {
    band_id: BAND, profile_id: PROFILE, fixed_equipment: [], equipment_access: null,
    equipment_forbids: forbids, skill_access: [], skill_lists: [],
  };
}

describe("T13-F019 blackpowder at the bound-equipment stage", () => {
  it("refuses a blackpowder mechanic through its canonical item aliases", () => {
    const message = buildRestriction(context({ build: { main_weapon_id: "weapon.pistol" } }), "boundEquipment");
    expect(message).toBe(`"blackpowder" is forbidden for ${WHO}.`);
  });

  it("keeps the prohibition when an untagged alias is listed first", () => {
    const colliding: Catalogue = { ...EMPTY_CATALOGUE, items: {
      untagged_alias: { kind: "ranged-weapon", mechanic_id: "weapon.pistol", tags: [] },
      tagged_alias: { kind: "ranged-weapon", mechanic_id: "weapon.pistol", tags: ["blackpowder"] },
    } };
    expect(buildRestriction(context({ catalogue: colliding, build: { main_weapon_id: "weapon.pistol" } }), "boundEquipment"))
      .toContain("blackpowder");
  });

  it("keeps permitted and unknown-fact selections legal", () => {
    expect(buildRestriction(context({ build: { main_weapon_id: "weapon.sword" } }), "boundEquipment")).toBeNull();
    expect(buildRestriction(context({ build: { main_weapon_id: "weapon.unmapped" } }), "boundEquipment")).toBeNull();
    expect(buildRestriction(context({ bindings: [] }), "boundEquipment")).toBeNull();
    expect(buildRestriction(context({ forbidden: ["mystery-token"] }), "boundEquipment")).toBeNull();
  });

  it("checks every bound equipment position", () => {
    expect(buildRestriction(context({ build: { off_hand_id: "weapon.pistol" } }), "boundEquipment")).toContain("blackpowder");
    expect(buildRestriction(context({ build: { extra_hand_id: "weapon.pistol" } }), "boundEquipment")).toContain("blackpowder");
    expect(buildRestriction(context({ build: { armour_id: "weapon.pistol" } }), "boundEquipment")).toContain("blackpowder");
    expect(buildRestriction(context({ build: { defence_ids: ["warhound"] } }), "boundEquipment")).toContain("animal");
  });

  it("keeps the printed crossbow pistol legal", () => {
    // H5 source check: the rulebook prints it under Missile Weapons and the
    // brotherhood list sells it at 35 gc, so it is a crossbow, not blackpowder.
    // Provenance: docs/knowledge/2a2b/tasks/T13-silence-equipment.md section 12.
    expect(items["crossbow_pistol"]!.tags).toEqual(["crossbow"]);
    expect(buildRestriction(context({ build: { extra_hand_id: "crossbow_pistol" } }), "boundEquipment")).toBeNull();
    expect(buildRestriction(context({ build: { armour_id: "crossbow_pistol" } }), "boundEquipment")).toBeNull();
    expect(equipmentIssue({
      profile: neutral(["blackpowder", "animal"]),
      item_id: "crossbow_pistol",
      item: items["crossbow_pistol"]!,
    })).toBeNull();
  });

  it("refuses the animal token at the decision boundary and the stage boundary", () => {
    const issue = equipmentIssue({ profile: neutral(["animal"]), item_id: "warhound", item: items["warhound"]! });
    expect(issue?.code).toBe("equipment_forbidden");
    expect(tokenForbids("animal", "warhound", items["warhound"]!)).toBe(true);
    expect(buildRestriction(context({ build: { defence_ids: ["warhound"] } }), "boundEquipment")).toContain("animal");
  });
});

describe("T13-F019 preservation of the stage's earlier contract", () => {
  it("keeps the five legacy tokens, their diagnostics and their order", () => {
    expect(buildRestriction(context({ forbidden: ["armour"], build: { armour_id: "armour.light-armour" } }), "boundEquipment"))
      .toBe(`armour is forbidden for ${WHO}`);
    expect(buildRestriction(context({ forbidden: ["ranged-weapons"], build: { main_weapon_id: "weapon.pistol" } }), "boundEquipment"))
      .toBe(`missile weapons are forbidden for ${WHO}`);
    expect(buildRestriction(context({ forbidden: ["heavy-armour"], build: { armour_id: "armour.plate-armour" } }), "boundEquipment"))
      .toBe(`heavy armour is forbidden for ${WHO}`);
    expect(buildRestriction(context({ forbidden: ["weapon.lance"], build: { main_weapon_id: "weapon.lance" } }), "boundEquipment"))
      .toBe(`lance is forbidden for ${WHO}`);
    expect(buildRestriction(context({ forbidden: ["defence.helmet"], build: { defence_ids: ["defence.helmet"] } }), "boundEquipment"))
      .toBe(`helmet is forbidden for ${WHO}`);
    expect(buildRestriction(context({
      forbidden: ["armour", "blackpowder"],
      build: { armour_id: "armour.light-armour", main_weapon_id: "weapon.pistol" },
    }), "boundEquipment")).toBe(`armour is forbidden for ${WHO}`);
  });

  it("keeps another band's binding and a permitted kit unchanged", () => {
    const orc = context({
      band: "black-orcs", profile: "orc-nuttaz", forbidden: ["armour", "ranged-weapons"],
      build: { armour_id: "armour.light-armour" },
    });
    expect(buildRestriction(orc, "boundEquipment")).toBe("armour is forbidden for black-orcs/orc-nuttaz");
    expect(buildRestriction(context({ forbidden: [], bindings: [], build: { main_weapon_id: "weapon.sword" } }), "boundEquipment"))
      .toBeNull();
  });
});
