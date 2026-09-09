/**
 * P5.1 (web-migration-parallel-plan.md §5): application service implementing
 * the frozen `CampaignAppService` interface (P3.4). Orchestrates the file
 * port (P3.2), the knowledge reader (P4.3) and the domain use cases
 * (P3.5/P6.x) — the UI never touches JSON, ports or domain internals.
 *
 * Rules honoured here:
 * - everything in memory: no browser storage, no filesystem (plan §2.4);
 * - history/undo is separated from rule logic: the service keeps a plain
 *   undo stack of documents and restores them verbatim;
 * - file-port and use-case failures become `AppError` values with stable
 *   reasons — no exceptions cross this boundary to the UI;
 * - ports are injected via `CampaignAppDeps` (composition in P5.2).
 */

import type {
  CampaignAppService,
  AppError,
  AppResult,
  ExportPayload,
  ImportRequest,
} from "./types";
import type { CampaignAppDeps } from "./types";
import type {
  CampaignDocument,
  MomentSelection,
  UseCaseResult,
} from "../../domain/campaign/index";
import { createDefaultUseCases } from "../../domain/campaign/kernel/default-usecases";
import type { CampaignUseCases } from "../../domain/campaign/index";
import {
  applyInjuryOutcome,
  recover,
  resolveFollowUp,
  type InjuriesWorkflowResult,
} from "./features/injuries/injuries-workflow";

const HISTORY_LIMIT = 50;

interface ServiceState {
  current: CampaignDocument | null;
  dirty: boolean;
  /** Undo stack of previously current documents (newest last). */
  history: CampaignDocument[];
}

export function createCampaignAppService(deps: CampaignAppDeps): CampaignAppService {
  const useCases: CampaignUseCases = deps.useCases ?? createDefaultUseCases(deps.knowledge);
  const state: ServiceState = { current: null, dirty: false, history: [] };

  function error(reason: AppError["reason"], message: string, detail?: Readonly<Record<string, unknown>>): AppError {
    return { ok: false, reason, message, ...(detail ? { detail } : {}) };
  }

  /** Apply a use-case result to the service state on success. */
  function applyResult(result: UseCaseResult): AppResult {
    if (!result.ok) {
      return error("rejected", result.message, { reason: result.reason });
    }
    if (state.current) {
      state.history.push(state.current);
      if (state.history.length > HISTORY_LIMIT) state.history.shift();
    }
    state.current = result.state;
    state.dirty = true;
    return { ok: true, document: result.state };
  }

  /** Same state discipline for injuries-workflow results (P6.5). */
  function applyInjuries(result: InjuriesWorkflowResult): AppResult {
    if (!result.ok) {
      // The frozen AppErrorReason keeps `rejected`; the specific workflow
      // reason travels in detail for the UI.
      return error("rejected", result.message, { reason: result.reason });
    }
    if (state.current) {
      state.history.push(state.current);
      if (state.history.length > HISTORY_LIMIT) state.history.shift();
    }
    state.current = result.document;
    state.dirty = true;
    return { ok: true, document: result.document };
  }

  return {
    async importCampaign(request: ImportRequest): Promise<AppResult> {
      if (state.current && !request.confirm_replace) {
        return error(
          "already_loaded",
          "A campaign is already loaded. Confirm replacement to discard unsaved changes.",
          { dirty: state.dirty },
        );
      }
      const parsed = deps.files.parseCampaignFile(request.text);
      if (!parsed.ok) {
        return error("file_error", parsed.message, {
          file_reason: parsed.reason,
          ...(parsed.location ? { location: parsed.location } : {}),
          ...(parsed.found_version !== undefined ? { found_version: parsed.found_version } : {}),
          supported_versions: parsed.supported_versions,
        });
      }
      const document: CampaignDocument = {
        campaign: parsed.document.campaign as unknown as CampaignDocument["campaign"],
        view: (parsed.document.view ?? {}) as CampaignDocument["view"],
      };
      // Validate before handing it to the UI (P6.8 semantics, applied early).
      const validated = useCases.validateForExport(document);
      if (!validated.ok) {
        return error("file_error", `Campaign rejected by domain validation: ${validated.message}`, {
          reason: validated.reason,
        });
      }
      state.current = document;
      state.dirty = false;
      state.history = [];
      return { ok: true, document };
    },

    async exportCampaign(): Promise<AppResult & { payload?: ExportPayload }> {
      if (!state.current) {
        return error("no_campaign_loaded", "No campaign is loaded.");
      }
      const validated = useCases.validateForExport(state.current);
      if (!validated.ok) {
        return error("rejected", `Campaign failed export validation: ${validated.message}`, {
          reason: validated.reason,
        });
      }
      const serialized = deps.files.serializeCampaign(state.current.campaign);
      if (!serialized.ok) {
        return error("file_error", serialized.message, { file_reason: serialized.reason });
      }
      state.dirty = false;
      const identity = state.current.campaign.identity;
      const filename = `${(identity.warband_name || identity.campaign_name || "campaign")
        .replace(/[^\w-]+/g, "_")}.mordheim`;
      return { ok: true, document: state.current, payload: { filename, text: serialized.text } };
    },

    async run(action: string, input: Readonly<Record<string, unknown>>): Promise<AppResult> {
      if (!state.current) {
        return error("no_campaign_loaded", `Cannot run "${action}": no campaign is loaded.`);
      }
      const knowledge = deps.knowledge;
      switch (action) {
        case "composeDraft":
          return applyResult(useCases.composeDraft(state.current, input as never));
        case "commitInitialWarband":
          return applyResult(useCases.commitInitialWarband(state.current, knowledge));
        case "recordBattle":
          return applyResult(useCases.recordBattle(state.current, input as never, knowledge));
        case "resolvePostBattleStep":
          return applyResult(
            useCases.resolvePostBattleStep(
              state.current,
              Number(input["battle_number"]),
              input as never,
            ),
          );
        case "applyAdvance":
          return applyResult(useCases.applyAdvance(state.current, input as never));
        case "assignEquipment":
          return applyResult(useCases.assignEquipment(state.current, input as never));
        case "hireHireling":
          return applyResult(useCases.hireHireling(state.current, input as never, knowledge));
        case "buyTradingItem":
          return applyResult(useCases.buyTradingItem(state.current, input as never));
        case "sellStashItem":
          return applyResult(useCases.sellStashItem(state.current, input as never));
        case "applyInjuryOutcome":
          return applyInjuries(applyInjuryOutcome(state.current, input as never));
        case "resolveInjuryFollowUp":
          return applyInjuries(
            resolveFollowUp(state.current, {
              follow_up_id: String(input["follow_up_id"] ?? ""),
              outcome: (input["outcome"] ?? {}) as never,
            }),
          );
        case "recoverWarrior":
          return applyInjuries(recover(state.current, String(input["warrior_id"] ?? "")));
        case "undo": {
          const previous = state.history.pop();
          if (!previous) {
            return error("rejected", "Nothing to undo.");
          }
          state.current = previous;
          // Restoring the previous document clears the unsaved-changes flag:
          // what is on disk again matches what is in memory.
          state.dirty = false;
          return { ok: true, document: previous };
        }
        default:
          return error("unknown", `Unknown action "${action}".`);
      }
    },

    selectMoment(moment: MomentSelection): AppResult {
      if (!state.current) {
        return error("no_campaign_loaded", "No campaign is loaded.");
      }
      // View selection never mutates campaign state and never dirties.
      const result = useCases.selectMoment(state.current, moment);
      if (!result.ok) {
        return error("rejected", result.message, { reason: result.reason });
      }
      state.current = result.state;
      return { ok: true, document: result.state };
    },

    isDirty(): boolean {
      return state.dirty;
    },

    current(): CampaignDocument | null {
      return state.current;
    },
  };
}
