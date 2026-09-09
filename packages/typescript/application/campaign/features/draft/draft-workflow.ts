/**
 * P6.2 (web-migration-parallel-plan.md §7): draft & initial composition
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
      // Dropping a row frees its purchased (non-fixed) equipment back to the
      // stash so the treasury/purchases are not lost; fixed equipment goes
      // with the row (it was never a purchase).
      let inventory = document.campaign.inventory;
      if (removed) {
        const freed = removed.equipment.filter((e) => e.acquisition === "purchase");
        if (freed.length > 0) {
          inventory = document.campaign.inventory.map((item) => {
            const freedEntry = freed.find((e) => e.item_id === item.id);
            return freedEntry
              ? {
                  ...item,
                  equipped: item.equipped - freedEntry.quantity,
                  stash: item.stash + freedEntry.quantity,
                }
              : item;
          });
        }
      }
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
