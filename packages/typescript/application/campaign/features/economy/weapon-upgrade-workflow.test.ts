/**
 * Parity port of the desktop weapon-upgrade guards
 * (`PostBattleEngine.buy_weapon_upgrade`, `test_variable_prices_and_restrictions.py`
 * weapon-upgrade rows): forged prices are rejected, duplicates are rejected,
 * only weapons can receive an upgrade, and the charge lands on the pending
 * post-battle gold delta (the engine-side guards the desktop matrix pins).
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "../../../../adapters/knowledge-reader/index";
import type { Campaign, CampaignDocument } from "../../../../domain/campaign/kernel/usecases";
import { buyWeaponUpgrade } from "./weapon-upgrade-workflow";

const ARTEFACT = JSON.parse(
  readFileSync(
    resolve(__dirname, "../../../../../../apps/warband-manager-web/public/knowledge/knowledge-web.json"),
    "utf-8",
  ),
) as unknown;

const reader = ArtefactKnowledgeReader.from(ARTEFACT) as ArtefactKnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
};

function displayName(targetId: string): string {
  return targetId.replace(/[-_]+/g, " ").replace(/\b\w/g, (letter) => letter.toLocaleUpperCase());
}

function documentWithStash(targetId: string, stash: number, value: number): CampaignDocument {
  const campaign: Campaign = {
    identity: { campaign_name: "Upgrades", warband_name: "Band", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors: [],
    battles: [],
    states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0, label: "Initial Warband" }],
    post_battles: [{
      battle_number: 1, complete: false, active_step: 7, completed_steps: [], review_open: false,
      gold_delta: 0, wyrdstone_delta: 0, event_log: [], pending_follow_ups: [],
    }],
    inventory: [{ id: targetId, name: displayName(targetId), category: "weapon", owned: stash, equipped: 0, stash, value }],
    special_rules: [],
    manual_log: [],
  };
  return { campaign, view: {} };
}

describe("desktop weapon-upgrade guards → web buyWeaponUpgrade", () => {
  it("consumes one stashed base weapon and adds the upgraded record", () => {
    const before = documentWithStash("axe", 2, 5);
    const result = buyWeaponUpgrade(before, reader, { item_id: "gromril_weapon", target_id: "axe", unit_price: 20 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const inventory = result.document.campaign.inventory;
    const base = inventory.find((row) => row.id === "axe");
    expect(base?.owned).toBe(1);
    expect(base?.stash).toBe(1);
    const upgraded = inventory.find((row) => row.id === "gromril_weapon:axe");
    expect(upgraded?.name).toBe("Gromril Weapon Axe");
    expect(upgraded?.owned).toBe(1);
    expect(upgraded?.stash).toBe(1);
    expect(upgraded?.equipped).toBe(0);
    expect(upgraded?.value).toBe(25); // base 5 + upgrade 20
    expect(upgraded?.base_item_id).toBe("axe");
    expect(upgraded?.special_rules).toContain("Gromril Weapon");
    const post = result.document.campaign.post_battles[0];
    expect(post.gold_delta).toBe(-20);
    expect(post.event_log?.at(-1)).toMatchObject({ type: "upgrade_weapon", item_id: "gromril_weapon", base_item_id: "axe" });
  });

  it("rejects a forged or non-positive price without mutation", () => {
    const before = documentWithStash("axe", 1, 5);
    const snapshot = JSON.stringify(before);
    for (const unitPrice of [19, 0, -1, 21]) {
      const result = buyWeaponUpgrade(before, reader, { item_id: "gromril_weapon", target_id: "axe", unit_price: unitPrice });
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.message).toContain("Invalid upgrade price: expected 20");
    }
    expect(JSON.stringify(before)).toBe(snapshot);
  });

  it("rejects upgrading an already-upgraded weapon", () => {
    const before = documentWithStash("axe", 1, 5);
    const first = buyWeaponUpgrade(before, reader, { item_id: "gromril_weapon", target_id: "axe", unit_price: 20 });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const duplicate = buyWeaponUpgrade(first.document, reader, { item_id: "gromril_weapon", target_id: "gromril_weapon:axe", unit_price: 20 });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.message).toContain("already has the Gromril Weapon upgrade");
  });

  it("only weapons can receive an upgrade", () => {
    const before = documentWithStash("light_armour", 1, 10);
    const result = buyWeaponUpgrade(before, reader, { item_id: "gromril_weapon", target_id: "light_armour", unit_price: 40 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Only weapons");
  });

  it("requires a stashed base copy", () => {
    const before = documentWithStash("axe", 0, 5);
    const result = buyWeaponUpgrade(before, reader, { item_id: "gromril_weapon", target_id: "axe", unit_price: 20 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("not available in the stash");
  });

  it("rejects offers without an upgrade multiplier", () => {
    const before = documentWithStash("axe", 1, 5);
    const result = buyWeaponUpgrade(before, reader, { item_id: "dagger", target_id: "axe", unit_price: 2 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("not available");
  });

  it("respects warband-only upgrade restrictions", () => {
    const before = documentWithStash("axe", 1, 5);
    // obsidian_weapon is warband_only for chaos bands; sisters-of-sigmar is not.
    const result = buyWeaponUpgrade(before, reader, { item_id: "obsidian_weapon", target_id: "axe", unit_price: 20 });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("not available to this warband");
  });
});