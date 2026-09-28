/**
 * P3.5: commit the initial warband — the pure port of the Python
 * `domain/warband_service.commit_initial_warband`.
 *
 * Draft → State #0: freezes the construction limits into the first immutable
 * timeline state and folds the fixed equipment into the inventory. Pure over
 * the document; the KB entered when the draft was built.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { Campaign, CampaignDocument, EquipmentEntry, InventoryItem, UseCaseResult } from "./usecases";
import type { KnowledgeReader } from "./ports";
import type { TimelineState } from "./state";
import { rejected } from "./rejections";
import { rosterIssuesOf } from "../construction";
import { owedCreationDecisions, type CreationDecisionReader } from "./creation-decisions";
import {
  cloneDocument,
  draftIsLegal,
  effectiveMaximumModels,
  experienceTotal,
  heroCount,
  memberCount,
  modelCount,
  rating,
  treasury,
} from "./document";

/** Which equipment entries count as fixed (folded into inventory at commit). */
function isFixed(entry: EquipmentEntry): boolean {
  if (entry.transferable === true) return false;
  return entry.acquisition === undefined || entry.acquisition !== "stash_assignment";
}

function foldEquipmentIntoInventory(campaign: Campaign): InventoryItem[] {
  const inventory = campaign.inventory.map((item) => ({ ...item }));
  for (const warrior of campaign.warriors) {
    for (const equipment of warrior.equipment) {
      if (!isFixed(equipment)) continue;
      const value = equipment.unit_cost ?? 0;
      let row = inventory.find((item) => item.id === equipment.item_id);
      if (!row) {
        row = {
          id: equipment.item_id,
          name: equipment.name,
          category: "Equipment",
          owned: 0,
          equipped: 0,
          stash: 0,
          value,
        };
        inventory.push(row);
      }
      row.owned += equipment.quantity;
      row.equipped += equipment.quantity;
    }
  }
  return inventory;
}

/**
 * Commit the draft as State #0. Rejects when the draft is already committed
 * or illegal (with the specific violation, mirroring `draft_is_legal`).
 *
 * With a reader, the roster is also checked against the band record's declared
 * minimums (member slots and henchman group sizes) and its runtime-scope
 * exclusions — the same verdicts the interface presents (T09).
 */
export function commitInitialWarband(
  document: CampaignDocument,
  knowledge?: KnowledgeReader,
): UseCaseResult {
  const { campaign } = document;
  if (!campaign.configuration.is_draft) {
    return rejected(
      "not_permitted_when_committed",
      "The initial warband has already been committed.",
    );
  }
  if (memberCount(campaign.warriors) < campaign.configuration.minimum_models) {
    return rejected(
      "limit_violated",
      `A warband needs at least ${campaign.configuration.minimum_models} models to commit (currently ${memberCount(campaign.warriors)}).`,
    );
  }
  if (memberCount(campaign.warriors) > effectiveMaximumModels(campaign)) {
    return rejected(
      "limit_violated",
      `The warband exceeds its maximum of ${effectiveMaximumModels(campaign)} models.`,
    );
  }
  const heroes = heroCount(campaign.warriors);
  if (heroes < 1) {
    return rejected("limit_violated", "The warband needs at least one hero to commit.");
  }
  if (heroes > campaign.configuration.hero_limit) {
    return rejected(
      "limit_violated",
      `The warband exceeds its hero limit of ${campaign.configuration.hero_limit}.`,
    );
  }
  if (treasury(campaign) < 0) {
    return rejected("limit_violated", "The draft exceeds the starting treasury.");
  }
  if (!draftIsLegal(campaign)) {
    return rejected("limit_violated", "The draft is not legal.");
  }
  if (knowledge) {
    const fatal = rosterIssuesOf(knowledge, campaign).find((issue) =>
      issue.code === "roster_minimum_missing" ||
      issue.code === "roster_group_minimum_missing" ||
      issue.code === "profile_unknown" ||
      issue.code === "profile_excluded_from_construction" ||
      issue.code === "variant_selection_required" ||
      issue.code === "variant_options_missing" ||
      issue.code === "variant_unknown_option" ||
      issue.code === "profile_not_permitted_for_variant" ||
      issue.code === "band_unknown",
    );
    if (fatal) return rejected("limit_violated", fatal.message);
    // A printed creation roll the rules require is part of the warband, not an
    // optional flourish: the draft cannot commit while one is still owed.
    const owed = owedCreationDecisions(document, knowledge as CreationDecisionReader);
    if (owed.length) {
      return {
        ok: false,
        reason: "prerequisite_missing",
        message: `Record the required creation roll first: ${owed.map((decision) => decision.name).join(", ")}.`,
        subject_ids: owed.map((decision) => decision.id),
      };
    }
  }

  const started = new Date().toISOString().slice(0, 10);
  const state: TimelineState = {
    number: 0,
    date: started,
    gold: treasury(campaign),
    wyrdstone: 0,
    rating: rating(campaign.warriors),
    models: modelCount(campaign.warriors),
    max_models: effectiveMaximumModels(campaign),
    heroes: heroCount(campaign.warriors),
    henchmen: campaign.warriors.reduce(
      (total, w) => (w.kind === "henchman" ? total + (w.quantity ?? 1) : total),
      0,
    ),
    experience: experienceTotal(campaign.warriors),
    label: "Initial Warband",
    roster: cloneDocument({ campaign, view: {} }).campaign.warriors,
    inventory: cloneDocument({ campaign, view: {} }).campaign.inventory,
  };
  const nextCampaign: Campaign = {
    ...campaign,
    configuration: { ...campaign.configuration, is_draft: false },
    identity: { ...campaign.identity, started },
    current_state_number: 0,
    states: [state],
    inventory: foldEquipmentIntoInventory(campaign),
  };
  return { ok: true, state: { campaign: nextCampaign, view: document.view } };
}
