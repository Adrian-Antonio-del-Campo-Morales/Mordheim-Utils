/**
 * Parity port of desktop `tests/campaign/test_equipment_editor.py` (9 test
 * functions → the subset the web kernel expresses). Traceability: manifest
 * rows with `web_target: packages/typescript/domain/campaign/equipment_editor.test.ts`.
 *
 * Mapping (desktop `assign_stash_item`/`return_equipped_item` → web
 * `assignEquipment` kernel use case):
 * - round-trip keeps the ledger (`owned = equipped + stash`) → covered;
 * - return rejects items not carried → typed `limit_violated`;
 * - assign rejects when the stash is empty → typed `limit_violated`;
 * - moves work without a pending post-battle → no post-battle coupling;
 * - moves survive save/load → real `CampaignFileV4Adapter` round-trip;
 * - henchman groups carry equipment as a group → quantity carried in one go;
 * - display suffix (`×2`) is UI-only — not portable, documented delta;
 * - bought dagger stays separate from the free starting dagger → entries
 *   keep distinct `acquisition` values; the fixed (starting) entry is not
 *   withdrawable;
 * - weapon-carriage limits live in the desktop post-battle engine (KB
 *   equip-capacity data) — not yet in the web kernel; documented gap.
 *
 * Purity: plain Node, real file adapter, fake KB — no React, no DOM, no fs.
 */

import { describe, expect, it } from "vitest";

import { assignEquipment } from "../../domain/campaign/kernel/equipment";
import { cloneDocument } from "../../domain/campaign/kernel/document";
import type { CampaignDocument } from "../../domain/campaign/kernel/usecases";
import { CampaignFileV4Adapter } from "../../adapters/campaign-file/index";

function makeDocument(): CampaignDocument {
  return {
    campaign: {
      identity: {
        campaign_name: "Equipment Campaign",
        warband_name: "Test Band",
        warband_type: "Sisters of Sigmar",
        band_id: "sisters-of-sigmar",
        mercenary_variant: null,
      },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [
        { id: "marta", name: "Marta", profile_name: "Sister Superior", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 2, cost: 45 },
        { id: "group", name: "Novices", profile_name: "Novice Sisters", kind: "henchman", stats: { WS: 3 }, equipment: [], skills: [], experience: 0, cost: 25, quantity: 3 },
      ],
      battles: [],
      states: [{ number: 0, date: "2026-09-10", gold: 380, wyrdstone: 0, rating: 30, models: 4, max_models: 15, heroes: 1, henchmen: 3, experience: 0, label: "Initial Warband" }],
      post_battles: [],
      inventory: [
        { id: "herbs", name: "Healing Herbs", category: "Woundcare", owned: 2, equipped: 0, stash: 2, value: 10 },
        { id: "dagger", name: "Dagger", category: "close-combat-weapon", owned: 1, equipped: 0, stash: 1, value: 2 },
      ],
      special_rules: [],
      manual_log: [],
    },
    view: {},
  };
}

const files = new CampaignFileV4Adapter();

describe("desktop test_equipment_editor.py → web assignEquipment parity", () => {
  it("assign and return round-trip keeps the ledger consistent", () => {
    const document = makeDocument();
    const before = document.campaign.inventory[0];
    const assign = assignEquipment(document, { warrior_id: "marta", item_id: "herbs", quantity: 1, direction: "equip" });
    expect(assign.ok).toBe(true);
    if (!assign.ok) return;
    const mid = assign.state.campaign.inventory.find((i) => i.id === "herbs")!;
    expect(mid.owned).toBe(before.owned);
    expect(mid.equipped).toBe(before.equipped + 1);
    expect(mid.stash).toBe(before.stash - 1);
    expect(assign.state.campaign.warriors[0].equipment.some((e) => e.item_id === "herbs")).toBe(true);
    const back = assignEquipment(assign.state, { warrior_id: "marta", item_id: "herbs", quantity: 1, direction: "stash" });
    expect(back.ok).toBe(true);
    if (!back.ok) return;
    const end = back.state.campaign.inventory.find((i) => i.id === "herbs")!;
    expect(end.owned).toBe(before.owned);
    expect(end.equipped).toBe(before.equipped);
    expect(end.stash).toBe(before.stash);
    expect(back.state.campaign.warriors[0].equipment.some((e) => e.item_id === "herbs")).toBe(false);
  });

  it("return rejects items the warrior does not carry", () => {
    const result = assignEquipment(makeDocument(), { warrior_id: "marta", item_id: "herbs", quantity: 1, direction: "stash" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("limit_violated");
  });

  it("assign rejects when the stash is empty", () => {
    const document = makeDocument();
    const emptied: CampaignDocument = {
      campaign: {
        ...document.campaign,
        inventory: document.campaign.inventory.map((i) => (i.id === "herbs" ? { ...i, stash: 0 } : i)),
      },
      view: document.view,
    };
    const result = assignEquipment(emptied, { warrior_id: "marta", item_id: "herbs", quantity: 1, direction: "equip" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("limit_violated");
  });

  it("moves work without a pending post-battle", () => {
    // The document has no pending post-battle at all — moves still work.
    const document = makeDocument();
    const assign = assignEquipment(document, { warrior_id: "marta", item_id: "herbs", quantity: 1, direction: "equip" });
    expect(assign.ok).toBe(true);
  });

  it("moves survive save/load", () => {
    const document = makeDocument();
    const assign = assignEquipment(document, { warrior_id: "marta", item_id: "herbs", quantity: 1, direction: "equip" });
    if (!assign.ok) throw new Error(assign.message);
    const serialized = files.serializeCampaign(assign.state.campaign);
    if (!serialized.ok) throw new Error(serialized.message);
    const parsed = files.parseCampaignFile(serialized.text);
    if (!parsed.ok) throw new Error(parsed.message);
    const restored = parsed.document.campaign as unknown as CampaignDocument["campaign"];
    const warrior = restored.warriors.find((w) => w.id === "marta")!;
    const item = restored.inventory.find((i) => i.id === "herbs")!;
    expect(warrior.equipment.some((e) => e.item_id === "herbs")).toBe(true);
    expect(item.equipped).toBe(1);
    expect(item.stash).toBe(1);
  });

  it("henchman group carries equipment as a group", () => {
    const document = makeDocument();
    const assign = assignEquipment(document, { warrior_id: "group", item_id: "herbs", quantity: 2, direction: "equip" });
    expect(assign.ok).toBe(true);
    if (!assign.ok) return;
    const group = assign.state.campaign.warriors.find((w) => w.id === "group")!;
    expect(group.equipment.find((e) => e.item_id === "herbs")?.quantity).toBe(2);
    const item = assign.state.campaign.inventory.find((i) => i.id === "herbs")!;
    expect(item.stash).toBe(0);
    const back = assignEquipment(assign.state, { warrior_id: "group", item_id: "herbs", quantity: 2, direction: "stash" });
    expect(back.ok).toBe(true);
    if (!back.ok) return;
    expect(back.state.campaign.inventory.find((i) => i.id === "herbs")?.stash).toBe(2);
  });

  it("bought dagger stays separate from a non-transferable starting dagger", () => {
    const document = makeDocument();
    const withFixed: CampaignDocument = {
      campaign: {
        ...document.campaign,
        warriors: document.campaign.warriors.map((w) =>
          w.id === "marta"
            ? {
                ...w,
                equipment: [{ item_id: "dagger", name: "Dagger", quantity: 1, acquisition: "fixed", per_model: true, transferable: false }],
              }
            : w,
        ),
      },
      view: document.view,
    };
    // The fixed (starting) entry cannot be withdrawn...
    const withdrawFixed = assignEquipment(withFixed, { warrior_id: "marta", item_id: "dagger", quantity: 1, direction: "stash" });
    expect(withdrawFixed.ok).toBe(false);
    // ...but a bought copy from the stash joins as its own stash_assignment entry.
    const buy = assignEquipment(withFixed, { warrior_id: "marta", item_id: "dagger", quantity: 1, direction: "equip" });
    expect(buy.ok).toBe(true);
    if (!buy.ok) return;
    const entries = buy.state.campaign.warriors.find((w) => w.id === "marta")!.equipment.filter((e) => e.item_id === "dagger");
    expect(entries).toHaveLength(2);
    expect(entries.some((e) => e.acquisition === "fixed" && e.transferable === false)).toBe(true);
    expect(entries.some((e) => e.acquisition === "stash_assignment" && e.transferable !== false)).toBe(true);
    // The bought copy can go back; the fixed one remains.
    const back = assignEquipment(buy.state, { warrior_id: "marta", item_id: "dagger", quantity: 1, direction: "stash" });
    expect(back.ok).toBe(true);
    if (!back.ok) return;
    const remaining = back.state.campaign.warriors.find((w) => w.id === "marta")!.equipment;
    expect(remaining).toHaveLength(1);
    expect(remaining[0].acquisition).toBe("fixed");
  });

  it("assignment quantity must be a positive integer (ledger safety)", () => {
    const result = assignEquipment(makeDocument(), { warrior_id: "marta", item_id: "herbs", quantity: 0, direction: "equip" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("invalid_input");
  });

  it("unknown warrior or item ids are typed not_found values", () => {
    const document = makeDocument();
    const ghostWarrior = assignEquipment(document, { warrior_id: "ghost", item_id: "herbs", quantity: 1, direction: "equip" });
    expect(ghostWarrior.ok).toBe(false);
    if (!ghostWarrior.ok) expect(ghostWarrior.reason).toBe("not_found");
    const ghostItem = assignEquipment(document, { warrior_id: "marta", item_id: "ghost", quantity: 1, direction: "equip" });
    expect(ghostItem.ok).toBe(false);
    if (!ghostItem.ok) expect(ghostItem.reason).toBe("not_found");
  });
});
