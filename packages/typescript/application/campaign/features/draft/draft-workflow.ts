/**
 * Web migration draft workflow: draft & initial composition
 * feature — application-layer orchestration over the P3.5 kernel use cases.
 *
 * Owns the *workflow* of building a warband draft:
 *  1. `startDraft` — create a draft for a warband selected from the KB;
 *  2. `addRow` / `removeRow` — compose the roster (the kernel validates
 *     gold/model/hero limits per batch);
 *  3. `commit` — draft → State #0.
 *
 * The UI never calls domain use cases directly: it talks to the P5.1
 * service through this workflow so every change flows through undo/history
 * and the dirty flag. All results are values — no exceptions cross layers.
 *
 * Purity: no React, no DOM, no filesystem. The KB is read through the
 * injected `KnowledgeReader` only.
 */

import type {
  CampaignDocument,
  DraftCompositionInput,
  IdString,
  KnowledgeReader,
  UseCaseResult,
} from "../../../../domain/campaign/index";
import type { CampaignUseCases } from "../../../../domain/campaign/index";
import { effectiveMaximumModels, memberCount, treasury } from "../../../../domain/campaign/kernel/document";

/** Why a workflow step failed (stable reasons for the UI). */
export type DraftWorkflowError =
  | { readonly ok: false; readonly reason: "not_found"; readonly message: string }
  | { readonly ok: false; readonly reason: "campaign_loaded"; readonly message: string }
  | { readonly ok: false; readonly reason: "rejected"; readonly message: string; readonly detail?: string };

export type DraftWorkflowResult =
  | { readonly ok: true; readonly document: CampaignDocument }
  | DraftWorkflowError;

function fromUseCase(result: UseCaseResult): DraftWorkflowResult {
  if (result.ok) return { ok: true, document: result.state };
  return { ok: false, reason: "rejected", message: result.message, detail: result.reason };
}

/** A warband option the UI can offer in the selection list. */
export interface WarbandOption {
  readonly band_id: IdString;
  readonly collection?: IdString;
  readonly name: string;
  readonly es_name?: string;
}

/**
 * Lists warband options from the KB. The frozen `KnowledgeReader` has no
 * listing method, so the feature receives candidate band ids from the UI
 * (populated by the build-time band index) and resolves each by stable id —
 * unknown candidates are filtered, never guessed.
 */
export function resolveWarbandOptions(
  candidates: readonly IdString[],
  knowledge: KnowledgeReader,
): WarbandOption[] {
  const options: WarbandOption[] = [];
  for (const bandId of candidates) {
    const result = knowledge.queryKnowledge({ id: { kind: "band_id", value: bandId } });
    if (!result.ok) continue;
    const names = result.record.names as Readonly<Record<string, string>>;
    const collectionValue = result.record.data["collection"];
    const esName = names["es"];
    const option: WarbandOption = {
      band_id: bandId,
      ...(typeof collectionValue === "string" ? { collection: collectionValue as IdString } : {}),
      name: names["en"] ?? bandId,
      ...(typeof esName === "string" ? { es_name: esName } : {}),
    };
    options.push(option);
  }
  return options;
}

/** Dependencies of the draft workflow (a slice of the P5.1 service world). */
export interface DraftWorkflowDeps {
  readonly knowledge: KnowledgeReader;
  readonly useCases: CampaignUseCases;
}

/** Creates the draft workflow bound to the injected ports. */
export function createDraftWorkflow(deps: DraftWorkflowDeps) {
  const { knowledge, useCases } = deps;

  return {
    resolveWarbandOptions: (candidates: readonly IdString[]): WarbandOption[] =>
      resolveWarbandOptions(candidates, knowledge),

    /** Step 1 — create a draft for the chosen warband. */
    startDraft(bandId: IdString, campaignName?: string): DraftWorkflowResult {
      const result = useCases.createDraft(bandId, knowledge);
      if (!result.ok) return fromUseCase(result);
      if (campaignName) {
        const renamed = {
          campaign: {
            ...result.state.campaign,
            identity: { ...result.state.campaign.identity, campaign_name: campaignName },
          },
          view: result.state.view,
        };
        return { ok: true, document: renamed };
      }
      return { ok: true, document: result.state };
    },

    /** Step 2a — append one composition row (hero/henchman group) to the draft. */
    addRow(
      document: CampaignDocument,
      row: {
        readonly profile_id: IdString;
        readonly kind: "hero" | "henchman";
        readonly quantity: number;
        readonly equipment: readonly IdString[];
      },
    ): DraftWorkflowResult {
      const input: DraftCompositionInput = {
        band_id: document.campaign.identity.band_id,
        rows: [row],
      };
      return fromUseCase(useCases.composeDraft(document, input));
    },

    /** Step 2b — drop a whole row from the draft (drafts only). */
    removeRow(document: CampaignDocument, rowId: IdString): DraftWorkflowResult {
      if (!document.campaign.configuration.is_draft) {
        return {
          ok: false,
          reason: "rejected",
          message: "Only a draft can change its roster; this campaign is committed.",
        };
      }
      const row = document.campaign.warriors.find((w) => w.id === rowId);
      if (!row) {
        return { ok: false, reason: "not_found", message: `Unknown roster row: ${rowId}.` };
      }
      if (row.kind === "hero" && document.campaign.warriors.filter((w) => w.kind === "hero").length === 1) {
        return {
          ok: false,
          reason: "rejected",
          message: "A warband needs at least one hero — remove other heroes first or commit.",
        };
      }
      const removed = document.campaign.warriors.find((w) => w.id === rowId);
      const warriors = document.campaign.warriors.filter((w) => w.id !== rowId);
      // Desktop refunds creation purchases when their draft row disappears.
      // Fixed equipment goes with the profile; it was never paid from the
      // starting treasury.
      let inventory = document.campaign.inventory;
      if (removed) {
        const freed = removed.equipment.filter((e) => e.acquisition === "purchase");
        if (freed.length > 0) {
          inventory = document.campaign.inventory
            .map((item) => {
              const refunded = freed.filter((entry) => entry.item_id === item.id).reduce((total, entry) => total + entry.quantity, 0);
              return refunded > 0 ? { ...item, owned: item.owned - refunded, equipped: item.equipped - refunded } : item;
            })
            .filter((item) => item.owned > 0);
        }
      }
      return { ok: true, document: { campaign: { ...document.campaign, warriors, inventory }, view: document.view } };
    },

    /** Resize an existing henchman group, mirroring desktop group controls. */
    adjustGroup(document: CampaignDocument, rowId: IdString, delta: number): DraftWorkflowResult {
      if (!document.campaign.configuration.is_draft) return { ok: false, reason: "rejected", message: "Only the initial warband draft can be edited." };
      if (!Number.isInteger(delta) || !delta) return { ok: false, reason: "rejected", message: "Group adjustment must be a non-zero whole number." };
      const warrior = document.campaign.warriors.find((row) => row.id === rowId);
      if (!warrior) return { ok: false, reason: "not_found", message: "Warrior not found in the draft." };
      if (warrior.kind !== "henchman" || !warrior.profile_id) return { ok: false, reason: "rejected", message: "Heroes are individuals; add or remove them instead." };
      const profileResult = knowledge.queryKnowledge({ id: { kind: "profile_id", value: warrior.profile_id } });
      if (!profileResult.ok || profileResult.record.data["band_id"] !== document.campaign.identity.band_id) return { ok: false, reason: "not_found", message: "Profile is no longer available in the knowledge base." };
      const bandResult = knowledge.queryKnowledge({ id: { kind: "band_id", value: document.campaign.identity.band_id } });
      const roster = bandResult.ok && bandResult.record.data["roster"] && typeof bandResult.record.data["roster"] === "object"
        ? bandResult.record.data["roster"] as Record<string, unknown> : {};
      const members = Array.isArray(roster["members"]) ? roster["members"] as readonly Record<string, unknown>[] : [];
      const member = members.find((row) => row["profile_id"] === warrior.profile_id) ?? {};
      const oldQuantity = warrior.quantity ?? 1;
      const nextQuantity = oldQuantity + delta;
      if (nextQuantity < 1) return { ok: false, reason: "rejected", message: "A henchman group keeps at least one member." };
      const group = member["group_size"] as Record<string, unknown> | undefined;
      const groupMaximum = typeof group?.["maximum"] === "number" ? group["maximum"] : null;
      if (groupMaximum !== null && nextQuantity > groupMaximum) return { ok: false, reason: "rejected", message: `This group holds at most ${groupMaximum} models.` };
      const profileMaximum = typeof member["maximum"] === "number" ? member["maximum"] : null;
      const profileTaken = document.campaign.warriors.filter((row) => row.profile_id === warrior.profile_id).reduce((total, row) => total + (row.quantity ?? 1), 0);
      if (delta > 0 && profileMaximum !== null && profileTaken + delta > profileMaximum) return { ok: false, reason: "rejected", message: "Roster limit for this profile reached." };
      if (delta > 0 && memberCount(document.campaign.warriors) + delta > effectiveMaximumModels(document.campaign)) return { ok: false, reason: "rejected", message: `Cannot exceed ${effectiveMaximumModels(document.campaign)} warband members.` };
      const perModelCost = warrior.equipment.filter((item) => item.acquisition === "purchase" && item.per_model).reduce((total, item) => total + (item.unit_cost ?? 0) * (item.quantity / oldQuantity), 0);
      const additional = delta > 0 ? delta * (warrior.cost + perModelCost) : 0;
      if (additional > treasury(document.campaign)) return { ok: false, reason: "rejected", message: "Not enough gold for added members and their equipment." };
      if (warrior.equipment.some((item) => item.per_model && item.quantity % oldQuantity !== 0)) return { ok: false, reason: "rejected", message: "Normalize group equipment before changing its size." };
      const equipment = warrior.equipment.map((item) => item.per_model ? { ...item, quantity: item.quantity + delta * (item.quantity / oldQuantity) } : item).filter((item) => item.quantity > 0);
      const inventory = document.campaign.inventory.map((item) => {
        const purchased = warrior.equipment.filter((entry) => entry.acquisition === "purchase" && entry.per_model && entry.item_id === item.id).reduce((total, entry) => total + delta * (entry.quantity / oldQuantity), 0);
        return purchased ? { ...item, owned: item.owned + purchased, equipped: item.equipped + purchased } : item;
      }).filter((item) => item.owned > 0);
      const warriors = document.campaign.warriors.map((row) => row.id === warrior.id ? { ...row, quantity: nextQuantity, equipment } : row);
      return { ok: true, document: { campaign: { ...document.campaign, warriors, inventory }, view: document.view } };
    },

    /** Step 3 — commit the legal draft as State #0. */
    commit(document: CampaignDocument): DraftWorkflowResult {
      return fromUseCase(useCases.commitInitialWarband(document, knowledge));
    },

    /** Live composition status for the UI's limits display. */
    status(document: CampaignDocument): {
      readonly models: number;
      readonly minimum_models: number;
      readonly maximum_models: number;
      readonly heroes: number;
      readonly hero_limit: number;
      readonly treasury: number;
      readonly legal: boolean;
    } {
      const { campaign } = document;
      const models = campaign.warriors.reduce(
        (total, w) => (w.kind === "hireling" ? total : total + (w.quantity ?? 1)),
        0,
      );
      const heroes = campaign.warriors.reduce(
        (total, w) => (w.kind === "hero" ? total + (w.quantity ?? 1) : total),
        0,
      );
      const recruitment = campaign.warriors.reduce((t, w) => t + w.cost * (w.quantity ?? 1), 0);
      const equipment = campaign.inventory.reduce((t, item) => t + item.owned * (item.value ?? 0), 0);
      const treasury = campaign.configuration.starting_gold - recruitment - equipment;
      const legal =
        models >= campaign.configuration.minimum_models &&
        models <= campaign.configuration.maximum_models &&
        heroes >= 1 &&
        heroes <= campaign.configuration.hero_limit &&
        treasury >= 0;
      return {
        models,
        minimum_models: campaign.configuration.minimum_models,
        maximum_models: campaign.configuration.maximum_models,
        heroes,
        hero_limit: campaign.configuration.hero_limit,
        treasury,
        legal,
      };
    },
  };
}

export type DraftWorkflow = ReturnType<typeof createDraftWorkflow>;
