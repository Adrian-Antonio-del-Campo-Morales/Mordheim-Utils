/**
 * T10 (post-review) — the T09 equipment contract on every route that can change
 * a member's kit.
 *
 * The review found that `composeDraft` honoured the construction contract while
 * the incremental routes did not: a draft could buy a forbidden item, a stash
 * move could break the compulsory family and the commit gate ignored the
 * equipment verdicts entirely. These tests drive the real artefact through the
 * incremental route (`buyDraftEquipment`), the confirmation route
 * (`commitInitialWarband`) and the service seam (`assignEquipment`,
 * `transferEquippedItem`), for the published cases the review named:
 *
 * - `silent-brotherhood-sc / silent-master` + `crossbow_pistol` (the printed
 *   list item; H5 shows it is not blackpowder, so the gate accepts it) and an
 *   unlisted blackpowder item (still refused);
 * - `outlaws-of-stirwood-forest-redux-fbg / bandit-leader` (band compiles the kit
 *   from `bow` only, one missile weapon, `cleric` exempt);
 * - `khemri-lahmian-brotherhood / lahmian-vampire` (the background variant
 *   activates the equipment lists).
 *
 * Purity: plain Node, the real reader and the real v5 adapter — no React.
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { readArtefactDocument } from "../../../support/kb-artefact";
import { join } from "node:path";

import { CampaignFileV5Adapter } from "@adapters/campaign-file";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { createCampaignAppService } from "@app/campaign/service";
import { itemFactsOf } from "@domain/campaign/construction";
import { buyDraftEquipment } from "@domain/campaign/kernel/equipment";
import { commitInitialWarband } from "@domain/campaign/kernel/commit-warband";
import { createDraft } from "@domain/campaign/kernel/create-draft";
import type { Campaign, CampaignDocument, Warrior } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

const SHADOWS = "silent-brotherhood-sc";
const OUTLAWS = "outlaws-of-stirwood-forest-redux-fbg";
const LAHMIAN = "khemri-lahmian-brotherhood";
const adapter = new CampaignFileV5Adapter();

function warrior(
  id: string,
  profileId: string,
  kind: Warrior["kind"],
  quantity = 1,
  equipment: Warrior["equipment"] = [],
): Warrior {
  return {
    id,
    name: `${profileId} ${id}`,
    profile_name: profileId,
    kind,
    stats: {},
    equipment,
    skills: [],
    experience: 0,
    cost: 0,
    quantity,
    profile_id: profileId,
  };
}

function item(itemId: string, quantity = 1): Warrior["equipment"][number] {
  return { item_id: itemId, name: itemId, quantity, per_model: true, acquisition: "purchase", unit_cost: 5 };
}

function draftDocument(
  bandId: string,
  warriors: readonly Warrior[],
  variant: string | null = null,
): CampaignDocument {
  const campaign: Campaign = {
    identity: { campaign_name: "Equipment gate", warband_name: "Band", warband_type: bandId, band_id: bandId, mercenary_variant: variant },
    configuration: { is_draft: true, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 0,
    warriors,
    battles: [],
    states: [],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
  return { campaign, view: { selected_moment: "draft:0" } };
}

describe.skipIf(!ARTEFACT_PATH)("T10 review: the equipment contract on the incremental route", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("accepts the printed crossbow pistol and still refuses an unlisted blackpowder item", () => {
    // H5 source check (2026-10-04): the rulebook prints the crossbow pistol
    // under Missile Weapons and the brotherhood list sells it at 35 gc, so the
    // band's own Silence does not refuse it. Provenance:
    // docs/knowledge/2a2b/tasks/T13-silence-equipment.md section 12.
    const document = draftDocument(SHADOWS, [warrior("master", "silent-master", "hero")]);
    const bought = buyDraftEquipment(document, { warrior_id: "master", item_id: "crossbow_pistol", unit_price: 35 }, reader);
    expect(bought.ok, bought.ok ? "" : bought.message).toBe(true);
    // A blackpowder item the band's lists do not offer cannot enter the roster:
    // the confirmation route judges the composition and refuses it.
    const composed = draftDocument(SHADOWS, [
      warrior("master", "silent-master", "hero", 1, [item("pistol")]),
      warrior("novices", "brotherhood-novices", "henchman", 2),
    ]);
    const committed = commitInitialWarband(composed, reader);
    expect(committed.ok).toBe(false);
    if (!committed.ok) expect(committed.message).toContain("not on any equipment list");
  });

  it("refuses a missile weapon the band does not offer, and the family outside its printed list", () => {
    const document = draftDocument(OUTLAWS, [warrior("leader", "bandit-leader", "hero")]);
    // A crossbow is named by the band prohibition; a throwing knife is not on
    // any of the profile's lists: neither reaches the roster through a purchase.
    const crossbow = buyDraftEquipment(document, { warrior_id: "leader", item_id: "crossbow", unit_price: 25 }, reader);
    expect(crossbow.ok).toBe(false);
    if (!crossbow.ok) expect(crossbow.message).toMatch(/crossbow|forbidden/);
    const knives = buyDraftEquipment(document, { warrior_id: "leader", item_id: "throwing_knives", unit_price: 10 }, reader);
    expect(knives.ok).toBe(false);
    if (!knives.ok) expect(knives.message).toContain("not on any equipment list");
  });

  it("accepts the printed bow, refuses a second missile weapon and refuses a kit without the family", () => {
    const document = draftDocument(OUTLAWS, [warrior("leader", "bandit-leader", "hero")]);
    const bow = buyDraftEquipment(document, { warrior_id: "leader", item_id: "bow", unit_price: 10 }, reader);
    expect(bow.ok, bow.ok ? "" : bow.message).toBe(true);
    if (!bow.ok) return;
    const second = buyDraftEquipment(bow.state, { warrior_id: "leader", item_id: "long_bow", unit_price: 20 }, reader);
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.message).toContain("missile weapons");
    // Removing the compulsory family is refused by the same contract: the kit is
    // judged as a whole, not as the item being moved. The rest of the roster is
    // legal so the missing bow is what refuses the commit.
    const withoutBow = draftDocument(OUTLAWS, [
      warrior("leader", "bandit-leader", "hero", 1, [item("sword")]),
      warrior("outlaws", "outlaws", "henchman", 2, [item("bow", 2)]),
    ]);
    const committed = commitInitialWarband(withoutBow, reader);
    expect(committed.ok).toBe(false);
    if (!committed.ok) expect(committed.message).toContain("no \"bow\"");
  });

  it("keeps the missile cap on the profile exempt from the compulsory family", () => {
    const document = draftDocument(OUTLAWS, [warrior("cleric", "cleric", "hero")]);
    // The printed exception only lifts the compulsory bow: the Cleric may carry
    // none or one missile weapon, never two.
    const bow = buyDraftEquipment(document, { warrior_id: "cleric", item_id: "bow", unit_price: 10 }, reader);
    expect(bow.ok, bow.ok ? "" : bow.message).toBe(true);
    if (!bow.ok) return;
    const second = buyDraftEquipment(bow.state, { warrior_id: "cleric", item_id: "long_bow", unit_price: 20 }, reader);
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.message).toContain("missile weapons");
  });

  it("activates the equipment lists the selected background publishes", () => {
    const vampire = (variantId: string | null) =>
      draftDocument(LAHMIAN, [warrior("vampire", "lahmian-vampire", "hero")], variantId);
    // `heavy_armour` belongs to the Foreign background list only: before the
    // choice, and with the Native background, the item is not on any active list.
    const beforeChoice = buyDraftEquipment(vampire(null), { warrior_id: "vampire", item_id: "heavy_armour", unit_price: 40 }, reader);
    expect(beforeChoice.ok).toBe(false);
    if (!beforeChoice.ok) expect(beforeChoice.message).toContain("not on any equipment list");
    const native = buyDraftEquipment(vampire("background.native"), { warrior_id: "vampire", item_id: "heavy_armour", unit_price: 40 }, reader);
    expect(native.ok).toBe(false);
    const foreign = buyDraftEquipment(vampire("background.foreign"), { warrior_id: "vampire", item_id: "heavy_armour", unit_price: 40 }, reader);
    expect(foreign.ok, foreign.ok ? "" : foreign.message).toBe(true);
  });

  it("composes a legal starter for a band with a compulsory family and commits it", () => {
    const created = createDraft(OUTLAWS, reader, "Outlaws", null);
    expect(created.ok, created.ok ? "" : created.message).toBe(true);
    if (!created.ok) return;
    const members = created.state.campaign.warriors;
    expect(members.length).toBeGreaterThanOrEqual(1);
    // Every member the rule does not exempt carries an item of the bow family
    // from the start (the starter buys the cheapest listed bow, `short_bow`).
    for (const member of members) {
      if (member.profile_id === "cleric") continue;
      expect(
        member.equipment.some((entry) => (itemFactsOf(reader, entry.item_id)?.tags ?? []).includes("bow")),
        `${member.id}`,
      ).toBe(true);
    }
    const committed = commitInitialWarband(created.state, reader);
    expect(committed.ok, committed.ok ? "" : committed.message).toBe(true);
  });
});

describe.skipIf(!ARTEFACT_PATH)("T10 review: the equipment contract on the service routes", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader = ArtefactKnowledgeReader.from(artefact);

  async function loadService(campaign: Campaign) {
    const serialized = adapter.serializeCampaign(campaign);
    expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
    if (!serialized.ok) throw new Error(serialized.message);
    const service = createCampaignAppService({ files: adapter, knowledge: reader });
    const imported = await service.importCampaign({ text: serialized.text });
    expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
    return service;
  }

  function committedCampaign(warriors: readonly Warrior[], bandId = OUTLAWS): Campaign {
    return {
      identity: { campaign_name: "Gate", warband_name: "Band", warband_type: bandId, band_id: bandId, mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors,
      battles: [],
      states: [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 3, max_models: 15, heroes: 2, henchmen: 1, experience: 0 }],
      post_battles: [],
      inventory: [
        { id: "bow", name: "Bow", category: "Equipment", owned: 2, equipped: 2, stash: 0, value: 5 },
        { id: "light_armour", name: "Light Armour", category: "Equipment", owned: 1, equipped: 0, stash: 1, value: 5 },
      ],
      special_rules: [],
      manual_log: [],
    };
  }

  it("refuses a stash assignment that would break the member's kit", async () => {
    const service = await loadService(
      committedCampaign([warrior("leader", "bandit-leader", "hero", 1, [item("bow")]), warrior("mark", "marksmen", "henchman")]),
    );
    // The second member may not carry a kit with no bow of its own.
    const assigned = await service.run("assignEquipment", { warrior_id: "mark", item_id: "light_armour", quantity: 1, direction: "equip" });
    expect(assigned.ok).toBe(false);
    if (!assigned.ok) expect(assigned.message).toContain("no \"bow\"");
  });

  it("refuses a transfer that would leave the source without its compulsory kit", async () => {
    const service = await loadService(
      committedCampaign([
        warrior("leader", "bandit-leader", "hero", 1, [item("bow")]),
        warrior("mark", "marksmen", "henchman", 1, [item("bow")]),
      ]),
    );
    const moved = await service.run("transferEquippedItem", { source_id: "leader", target_id: "mark", item_id: "bow", quantity: 1 });
    expect(moved.ok).toBe(false);
    if (!moved.ok) expect(moved.message).toContain("no \"bow\"");
  });
});
