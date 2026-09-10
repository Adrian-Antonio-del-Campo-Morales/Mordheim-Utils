/**
 * P3.5 (web-migration-parallel-plan.md §5): immutable document helpers and
 * structural invariants of the campaign kernel.
 *
 * Every helper returns a new document; inputs are never mutated (plan §5.3).
 * The invariants here mirror the Python domain layer (Phase 2) and the v4
 * contract README, so a document valid here survives the file round-trip.
 *
 * Purity: no React, no DOM, no filesystem, no KnowledgeReader dependency.
 */

import type {
  CampaignDocument,
  IdString,
  InventoryItem,
  MomentSelection,
  PostBattle,
  TimelineState,
  Warrior,
} from "../index";
import { rejected } from "./rejections";
import type { UseCaseResult } from "../index";

/** Deep-frozen structural clone (open payloads travel verbatim). */
export function cloneDocument(document: CampaignDocument): CampaignDocument {
  return structuredClone(document);
}

/** Newest committed timeline state, or `null` for a draft. */
export function currentState(document: CampaignDocument): TimelineState | null {
  const { campaign } = document;
  if (campaign.current_state_number === 0 && campaign.states.length === 0) return null;
  return campaign.states.find((state) => state.number === campaign.current_state_number) ?? null;
}

/** Battle number the next `recordBattle` will use. */
export function nextBattleNumber(document: CampaignDocument): number {
  return document.campaign.battles.reduce((max, battle) => Math.max(max, battle.number), 0) + 1;
}

/** Own-band model count: hirelings never consume roster capacity. */
export function memberCount(warriors: readonly Warrior[]): number {
  return warriors.reduce((total, w) => (w.kind === "hireling" ? total : total + (w.quantity ?? 1)), 0);
}

/** Total model count including hirelings (snapshot field `models`). */
export function modelCount(warriors: readonly Warrior[]): number {
  return warriors.reduce((total, w) => total + (w.quantity ?? 1), 0);
}

/** Hero rows counted by quantity. */
export function heroCount(warriors: readonly Warrior[]): number {
  return warriors.reduce((total, w) => (w.kind === "hero" ? total + (w.quantity ?? 1) : total), 0);
}

/** Total experience of own-band members (hirelings excluded). */
export function experienceTotal(warriors: readonly Warrior[]): number {
  return warriors.reduce(
    (total, w) => (w.kind === "hireling" ? total : total + w.experience * (w.quantity ?? 1)),
    0,
  );
}

/** Warband rating: members × 5 + experience + hireling ratings. */
export function rating(warriors: readonly Warrior[]): number {
  const hirelingRating = warriors.reduce(
    (total, w) => (w.kind === "hireling" ? total + (w.hireling_rating ?? 0) : total),
    0,
  );
  return memberCount(warriors) * 5 + experienceTotal(warriors) + hirelingRating;
}

/** Treasury: starting gold minus recruitment and equipment cost. */
export function treasury(campaign: CampaignDocument["campaign"]): number {
  const recruitment = campaign.warriors.reduce((t, w) => t + w.cost * (w.quantity ?? 1), 0);
  if (campaign.configuration.is_draft) {
    // Desktop drafts retain the actual acquisition cost on each equipped
    // purchase.  The inventory row is only an ownership counter, so using
    // its single `value` for equipped copies loses profile-list prices.
    const equipped = campaign.warriors.reduce(
      (total, warrior) => total + warrior.equipment.reduce(
        (sum, item) => sum + (item.acquisition === "purchase" ? (item.unit_cost ?? 0) * item.quantity : 0),
        0,
      ),
      0,
    );
    const stashed = campaign.inventory.reduce((total, item) => total + item.stash * (item.value ?? 0), 0);
    return campaign.configuration.starting_gold - recruitment - equipped - stashed;
  }
  const equipment = campaign.inventory.reduce((t, item) => t + item.owned * (item.value ?? 0), 0);
  return campaign.configuration.starting_gold - recruitment - equipment;
}

/** Maximum models plus hireling modifiers. */
export function effectiveMaximumModels(campaign: CampaignDocument["campaign"]): number {
  return (
    campaign.configuration.maximum_models +
    campaign.warriors.reduce(
      (total, w) => (w.kind === "hireling" ? total + (w.maximum_models_modifier ?? 0) : total),
      0,
    )
  );
}

/**
 * Draft legality (Python `draft_is_legal`): model counts, hero limits and a
 * non-negative treasury.
 */
export function draftIsLegal(campaign: CampaignDocument["campaign"]): boolean {
  return (
    memberCount(campaign.warriors) >= campaign.configuration.minimum_models &&
    memberCount(campaign.warriors) <= effectiveMaximumModels(campaign) &&
    heroCount(campaign.warriors) >= 1 &&
    heroCount(campaign.warriors) <= campaign.configuration.hero_limit &&
    treasury(campaign) >= 0
  );
}

/** View-only patch; `campaign` stays frozen. */
export function withView(
  document: CampaignDocument,
  patch: Partial<CampaignDocument["view"]>,
): CampaignDocument {
  return { campaign: document.campaign, view: { ...document.view, ...patch } };
}

/** Replace the whole campaign section, keeping the view. */
export function withCampaign(
  document: CampaignDocument,
  campaign: CampaignDocument["campaign"],
): CampaignDocument {
  return { campaign, view: document.view };
}

/** The pending (incomplete) post-battle, or `null`. */
export function pendingPostBattle(document: CampaignDocument): PostBattle | null {
  return document.campaign.post_battles.find((post) => !post.complete) ?? null;
}

/** View selection string for a timeline state number. */
export function stateMoment(number: number): MomentSelection {
  return `state:${number}` as MomentSelection;
}

/**
 * Structural invariants shared with the Python writer's checks (P5.1's
 * `validateForExport` delegates here so rule blocks and export agree).
 */
export function validateStructure(document: CampaignDocument): UseCaseResult {
  const { campaign } = document;
  const committed = campaign.current_state_number;
  if (committed !== 0 && !campaign.states.some((s) => s.number === committed)) {
    return rejected(
      "invalid_input",
      `current_state_number ${committed} does not exist in the timeline.`,
    );
  }
  for (let i = 1; i < campaign.states.length; i += 1) {
    if (campaign.states[i].number <= campaign.states[i - 1].number) {
      return rejected("invalid_input", "Timeline states must be strictly ordered by number.");
    }
  }
  const battleNumbers = new Set(campaign.battles.map((b) => b.number));
  if (battleNumbers.size !== campaign.battles.length) {
    return rejected("invalid_input", "Battle numbers must be unique.");
  }
  const postNumbers = new Set(campaign.post_battles.map((p) => p.battle_number));
  if (postNumbers.size !== campaign.post_battles.length) {
    return rejected("invalid_input", "Post-battle records must have unique battle numbers.");
  }
  if (campaign.configuration.is_draft && campaign.states.length > 0) {
    return rejected("invalid_input", "A draft cannot have committed timeline states.");
  }
  const warriorIds = new Set<string>();
  for (const warrior of campaign.warriors) {
    if (warriorIds.has(warrior.id)) {
      return rejected("invalid_input", `Duplicate warrior id: ${warrior.id}.`);
    }
    warriorIds.add(warrior.id);
  }
  const inventoryIds = new Set<string>();
  for (const item of campaign.inventory) {
    if (inventoryIds.has(item.id)) {
      return rejected("invalid_input", `Duplicate inventory item id: ${item.id}.`);
    }
    inventoryIds.add(item.id);
  }
  return { ok: true, state: document };
}

/** Warrior lookup by id. */
export function findWarrior(document: CampaignDocument, id: IdString): Warrior | null {
  return document.campaign.warriors.find((w) => w.id === id) ?? null;
}

/** Inventory row lookup by item id. */
export function findInventoryItem(document: CampaignDocument, id: IdString): InventoryItem | null {
  return document.campaign.inventory.find((item) => item.id === id) ?? null;
}
