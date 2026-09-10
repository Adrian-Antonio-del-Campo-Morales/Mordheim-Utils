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
import { buyDraftEquipment, buyDraftStashItem, removeDraftEquipment, removeDraftStashItem } from "../../domain/campaign/kernel/equipment";
import type { CampaignUseCases } from "../../domain/campaign/index";
import {
  applyInjuryOutcome,
  recover,
  resolveFollowUp,
  type InjuriesWorkflowResult,
} from "./features/injuries/injuries-workflow";
import { createDraftWorkflow } from "./features/draft/draft-workflow";
import { applyBattleExperience } from "./features/advances/experience-workflow";
import { commitAdvanceChoice, promoteHenchman, resolveAdvanceRoll, setPromotionSkillTables } from "./features/advances/advance-resolution-workflow";
import { applyExploration, continueExploration } from "./features/exploration/exploration-workflow";
import { sellWyrdstone } from "./features/economy/wyrdstone-sale-workflow";
import { applyVeteranPool } from "./features/recruitment/veteran-workflow";
import { recruitGroupMember } from "./features/recruitment/recruitment-workflow";
import { assignDramatisSearch, assignRareSearch, buyRareSearch, hireDramatisSearch, resolveDramatisSearch, resolveRareSearch } from "./features/searches/search-workflow";

const HISTORY_LIMIT = 50;

interface ServiceState {
  current: CampaignDocument | null;
  dirty: boolean;
  baseline: string | null;
  /** Undo stack of previously current documents (newest last). */
  history: CampaignDocument[];
}

export function createCampaignAppService(deps: CampaignAppDeps): CampaignAppService {
  const useCases: CampaignUseCases = deps.useCases ?? createDefaultUseCases(deps.knowledge);
  const draftWorkflow = createDraftWorkflow({ knowledge: deps.knowledge, useCases });
  const state: ServiceState = { current: null, dirty: false, baseline: null, history: [] };
  const listeners = new Set<() => void>();
  const fingerprint = (document: CampaignDocument): string => JSON.stringify(document.campaign);
  function notify(): void {
    state.dirty = state.current !== null && fingerprint(state.current) !== state.baseline;
    for (const listener of listeners) listener();
  }

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
    notify();
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
    notify();
    return { ok: true, document: result.document };
  }

  return {
    async createCampaign(input): Promise<AppResult> {
      if (state.current) return error("already_loaded", "A campaign is already loaded.");
      if (!input.campaign_name.trim() || !input.warband_name.trim()) return error("rejected", "Campaign and warband names are required.");
      const result = useCases.createDraft(input.band_id, deps.knowledge);
      if (!result.ok) return error("rejected", result.message, { reason: result.reason });
      const document = { ...result.state, campaign: { ...result.state.campaign, identity: { ...result.state.campaign.identity, campaign_name: input.campaign_name.trim(), warband_name: input.warband_name.trim() } } };
      state.current = document;
      state.history = [];
      state.baseline = null;
      notify();
      return { ok: true, document };
    },
    canUndo: () => state.history.length > 0,
    subscribe(listener) { listeners.add(listener); return () => { listeners.delete(listener); }; },
    markExported(document) { state.baseline = fingerprint(document); notify(); },
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
      state.baseline = fingerprint(document);
      notify();
      return { ok: true, document };
    },

    async exportCampaign(): Promise<AppResult & { payload?: ExportPayload }> {
      const result = await this.prepareExport();
      if (result.ok) this.markExported(result.document);
      return result;
    },

    async prepareExport(): Promise<AppResult & { payload?: ExportPayload }> {
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
      const selected = state.current.view.selected_moment;
      const pending = state.current.campaign.post_battles.find((post) => !post.complete);
      const editable = !selected || selected === "draft:0" || selected === `state:${state.current.campaign.current_state_number}` || (pending && selected === `post:${pending.battle_number}`);
      if (action !== "undo" && action !== "renameCampaign" && action !== "renameWarband" && !editable) return error("rejected", "Historical moments are read-only.");
      switch (action) {
        case "renameCampaign":
        case "renameWarband": {
          const key = action === "renameCampaign" ? "campaign_name" : "warband_name";
          const name = String(input[key] ?? input["name"] ?? "").trim();
          if (!name) return error("rejected", "A name is required.");
          return applyResult({ ok: true, state: { ...state.current, campaign: { ...state.current.campaign, identity: { ...state.current.campaign.identity, [key]: name } } } });
        }
        case "renameWarrior": {
          if (!state.current.campaign.configuration.is_draft) return error("rejected", "Warrior renaming is available during initial composition.");
          const name = String(input["name"] ?? "").trim();
          const id = String(input["warrior_id"] ?? "");
          if (!name || !state.current.campaign.warriors.some((warrior) => warrior.id === id)) return error("rejected", "A valid warrior and name are required.");
          if (state.current.campaign.warriors.some((warrior) => warrior.id !== id && warrior.name.localeCompare(name, undefined, { sensitivity: "accent" }) === 0)) return error("rejected", "Another warrior or group already uses that name.");
          return applyResult({ ok: true, state: { ...state.current, campaign: { ...state.current.campaign, warriors: state.current.campaign.warriors.map((warrior) => warrior.id === id ? { ...warrior, name } : warrior) } } });
        }
        case "composeDraft": {
          const result = useCases.composeDraft(state.current, input as never);
          if (!result.ok) return applyResult(result);
          const name = String(input["name"] ?? "").trim();
          if (!name) return applyResult(result);
          const previousIds = new Set(state.current.campaign.warriors.map((warrior) => warrior.id));
          const added = result.state.campaign.warriors.find((warrior) => !previousIds.has(warrior.id));
          if (!added) return applyResult(result);
          return applyResult({ ok: true, state: { ...result.state, campaign: { ...result.state.campaign, warriors: result.state.campaign.warriors.map((warrior) => warrior.id === added.id ? { ...warrior, name } : warrior) } } });
        }
        case "removeDraftRow": {
          const result = draftWorkflow.removeRow(state.current, String(input["warrior_id"] ?? ""));
          if (!result.ok) return error("rejected", result.message, { reason: result.reason });
          return applyResult({ ok: true, state: result.document });
        }
        case "adjustDraftGroup": {
          const result = draftWorkflow.adjustGroup(state.current, String(input["warrior_id"] ?? ""), Number(input["delta"]));
          if (!result.ok) return error("rejected", result.message, { reason: result.reason });
          return applyResult({ ok: true, state: result.document });
        }
        case "commitInitialWarband":
          return applyResult(useCases.commitInitialWarband(state.current, knowledge));
        case "resolveBattleStartCheck": {
          const warriorId = String(input["warrior_id"] ?? ""); const checkId = String(input["check_id"] ?? ""); const roll = Number(input["roll"]);
          const warrior = state.current.campaign.warriors.find((row) => row.id === warriorId);
          const check = warrior?.battle_start_checks?.find((row) => String(row["check_id"] ?? "") === checkId);
          if (!warrior || !check) return error("rejected", "Unknown pre-battle injury check.");
          const dice = (check["dice"] ?? {}) as Record<string, unknown>; const count = Number(dice["count"] ?? 1); const sides = Number(dice["sides"] ?? 6);
          if (!Number.isInteger(roll) || roll < count || roll > count * sides) return error("rejected", `Enter a result from ${count} to ${count * sides}.`);
          const failure = (check["failure_when"] ?? {}) as Record<string, unknown>; const min = Number(failure["min"] ?? 0); const max = Number(failure["max"] ?? min);
          const checks = { ...((state.current.view.pending_battle_draft?.["battle_start_checks"] ?? {}) as Record<string, unknown>), [`${warriorId}:${checkId}`]: { roll, misses_battle: roll >= min && roll <= max, reason: "Old Battle Wound" } };
          return applyResult({ ok: true, state: { ...state.current, view: { ...state.current.view, pending_battle_draft: { ...(state.current.view.pending_battle_draft ?? {}), battle_start_checks: checks } } });
        }
        case "recordBattle": {
          const checks = (state.current.view.pending_battle_draft?.["battle_start_checks"] ?? {}) as Record<string, { misses_battle?: boolean }>;
          const pendingChecks = state.current.campaign.warriors.filter((warrior) => (warrior.games_to_miss ?? 0) === 0).flatMap((warrior) => (warrior.battle_start_checks ?? []).map((check) => `${warrior.id}:${String(check["check_id"] ?? "")}`)).filter((key) => !checks[key]);
          if (pendingChecks.length) return error("rejected", "Resolve all pre-battle injury checks before recording the battle.");
          const unavailable = new Set(Object.entries(checks).filter(([, value]) => value.misses_battle).map(([key]) => key.split(":")[0]));
          const outOfAction = Array.isArray(input["out_of_action_ids"]) ? input["out_of_action_ids"].map(String) : [];
          if (outOfAction.some((id) => unavailable.has(id))) return error("rejected", "Warriors excluded by a pre-battle injury check cannot be taken out of action.");
          const participants = state.current.campaign.warriors.filter((warrior) => (warrior.games_to_miss ?? 0) === 0 && !unavailable.has(warrior.id)).map((warrior) => warrior.id);
          const result = useCases.recordBattle(state.current, { ...input, out_of_action_ids: outOfAction, participants } as never, knowledge);
          if (!result.ok) return applyResult(result);
          return applyResult({ ok: true, state: { ...result.state, view: { ...result.state.view, pending_battle_draft: undefined } } });
        }
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
        case "applyBattleExperience": {
          const result = applyBattleExperience(
            state.current,
            knowledge,
            (input["awards"] ?? undefined) as Readonly<Record<string, number>> | undefined,
          );
          if (!result.ok) return error("rejected", result.message, { reason: result.reason });
          return applyResult({ ok: true, state: result.document });
        }
        case "resolveAdvanceRoll": {
          const result = resolveAdvanceRoll(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "commitAdvanceChoice": {
          const result = commitAdvanceChoice(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "promoteHenchman": {
          const result = promoteHenchman(state.current, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "setPromotionSkillTables": {
          const result = setPromotionSkillTables(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "applyExploration": {
          const dice = Array.isArray(input["dice"]) ? input["dice"].map(Number) : [];
          const result = applyExploration(state.current, knowledge, dice);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "continueExploration": {
          const result = continueExploration(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "sellWyrdstone": {
          const result = sellWyrdstone(state.current, knowledge, Number(input["quantity"]));
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "applyVeteranPool": {
          const dice = Array.isArray(input["dice"]) ? input["dice"].map(Number) : [];
          const result = applyVeteranPool(state.current, dice);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "recruitGroupMember": {
          const result = recruitGroupMember(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "assignRareSearch": { const result=assignRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "assignDramatisSearch": { const result=assignDramatisSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveRareSearch": { const result=resolveRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveDramatisSearch": { const result=resolveDramatisSearch(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "buyRareSearch": { const result=buyRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "hireDramatisSearch": { const result=hireDramatisSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "assignEquipment":
          return applyResult(useCases.assignEquipment(state.current, input as never));
        case "buyDraftEquipment":
          return applyResult(buyDraftEquipment(state.current, input as never, knowledge));
        case "removeDraftEquipment":
          return applyResult(removeDraftEquipment(state.current, input as never));
        case "buyDraftStashItem":
          return applyResult(buyDraftStashItem(state.current, input as never, knowledge));
        case "removeDraftStashItem":
          return applyResult(removeDraftStashItem(state.current, input as never));
        case "hireHireling": {
          const post = state.current.campaign.post_battles.find((row) => !row.complete);
          if (!post) return error("rejected", "Hired Swords can only be hired during post-battle.");
          const fee = Number(input["fee"]);
          if (!Number.isInteger(fee) || fee < 0) return error("rejected", "Resolve the hiring fee before hiring.");
          const currentSnapshot = state.current.campaign.states.find((row) => row.number === state.current!.campaign.current_state_number) ?? state.current.campaign.states.at(-1);
          const availableGold = (currentSnapshot?.gold ?? 0) + (post.gold_delta ?? 0);
          if (fee > availableGold) return error("rejected", `Not enough gold: ${fee} gc needed, ${availableGold} available.`);
          const result = useCases.hireHireling(state.current, input as never, knowledge);
          if (!result.ok) return applyResult(result);
          const resultPost = result.state.campaign.post_battles.find((row) => !row.complete);
          if (!resultPost) return error("rejected", "Pending post-battle disappeared while hiring.");
          const changed = { ...resultPost, gold_delta: (resultPost.gold_delta ?? 0) - fee, event_log: [...(resultPost.event_log ?? []), { step: 6, type: "hire", profile_id: input["profile_id"], description: `Hired for ${fee} gc.` }] };
          return applyResult({ ok: true, state: { ...result.state, campaign: { ...result.state.campaign, post_battles: result.state.campaign.post_battles.map((row) => row === resultPost ? changed : row) } } });
        }
        case "buyTradingItem": {
          const post = state.current.campaign.post_battles.find((row) => !row.complete);
          if (!post) return error("rejected", "Trading is only available during post-battle.");
          const itemId = String(input["item_id"] ?? ""), name = String(input["name"] ?? itemId);
          const quantity = Number(input["quantity"]), unitPrice = Number(input["unit_price"]);
          if (!itemId || !Number.isInteger(quantity) || quantity <= 0 || !Number.isInteger(unitPrice) || unitPrice < 0) return error("rejected", "A valid item, quantity and price are required.");
          const catalogue = (knowledge as typeof knowledge & { campaignSection?(section:string):Readonly<Record<string,unknown>> }).campaignSection?.("trading-post");
          const catalogueItems = Array.isArray(catalogue?.["items"]) ? catalogue["items"] as Readonly<Record<string,unknown>>[] : [];
          const catalogueEntry = catalogueItems.find((row) => row["item_id"] === itemId);
          const restrictions = Array.isArray(catalogueEntry?.["restrictions"]) ? catalogueEntry["restrictions"] as Readonly<Record<string,unknown>>[] : [];
          const inferredOne = restrictions.some((row) => row["type"] === "profile_only" && String(row["note"] ?? "").toLocaleLowerCase().startsWith("one "));
          const declaredLimit = restrictions.find((row) => row["type"] === "limit_per_warband")?.["value"];
          const limit = Number.isInteger(declaredLimit) ? Number(declaredLimit) : inferredOne ? 1 : null;
          const owned = state.current.campaign.inventory.filter((row) => row.id === itemId).reduce((sum, row) => sum + row.owned, 0);
          if (limit !== null && owned + quantity > limit) return error("rejected", `Warband limit reached: at most ${limit} of this item (own ${owned}).`);
          const snapshot = state.current.campaign.states.find((row) => row.number === state.current!.campaign.current_state_number) ?? state.current.campaign.states.at(-1);
          const available = (snapshot?.gold ?? 0) + (post.gold_delta ?? 0), total = quantity * unitPrice;
          if (total > available) return error("rejected", `Not enough gold: ${total} gc needed, ${available} available.`);
          const found = state.current.campaign.inventory.find((row) => row.id === itemId);
          const inventory = found ? state.current.campaign.inventory.map((row) => row.id === itemId ? { ...row, owned: row.owned + quantity, stash: row.stash + quantity, value: unitPrice } : row) : [...state.current.campaign.inventory, { id: itemId, name, category: String(input["category"] ?? "Trading Post"), owned: quantity, equipped: 0, stash: quantity, value: unitPrice }];
          const changed = { ...post, gold_delta: (post.gold_delta ?? 0) - total, event_log: [...(post.event_log ?? []), { step: 7, type: "buy_item", item_id: itemId, quantity, description: `${quantity}× ${name} bought for ${total} gc.` }] };
          return applyResult({ ok: true, state: { ...state.current, campaign: { ...state.current.campaign, inventory, post_battles: state.current.campaign.post_battles.map((row) => row === post ? changed : row) } } });
        }
        case "sellStashItem": {
          const post = state.current.campaign.post_battles.find((row) => !row.complete);
          if (!post) return error("rejected", "Trading is only available during post-battle.");
          const itemId = String(input["item_id"] ?? ""), quantity = Number(input["quantity"]);
          const found = state.current.campaign.inventory.find((row) => row.id === itemId);
          if (!found) return error("rejected", "Unknown inventory item.");
          if (!Number.isInteger(quantity) || quantity <= 0 || found.stash < quantity) return error("rejected", `Only ${found.stash} unassigned copy/copies are available.`);
          const unitPrice = Math.max(0, Math.floor((found.value ?? 0) / 2)), total = unitPrice * quantity;
          const inventory = state.current.campaign.inventory.map((row) => row.id === itemId ? { ...row, owned: row.owned - quantity, stash: row.stash - quantity } : row).filter((row) => row.owned > 0);
          const changed = { ...post, gold_delta: (post.gold_delta ?? 0) + total, event_log: [...(post.event_log ?? []), { step: 7, type: "sell_item", item_id: itemId, quantity, description: `${quantity}× ${found.name} sold for ${total} gc.` }] };
          return applyResult({ ok: true, state: { ...state.current, campaign: { ...state.current.campaign, inventory, post_battles: state.current.campaign.post_battles.map((row) => row === post ? changed : row) } } });
        }
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
          notify();
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
      notify();
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
