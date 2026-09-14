/**
 * Campaign application service: application service implementing
 * the frozen `CampaignAppService` interface (P3.4). Orchestrates the file
 * port (P3.2), the knowledge reader (P4.3) and the domain use cases
 * (P3.5/P6.x) — the UI never touches JSON, ports or domain internals.
 *
 * Rules honoured here:
 * - everything in memory: no browser storage or implicit filesystem persistence;
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
import { dismissRecruit, recruitBandProfile, recruitGroupMember } from "./features/recruitment/recruitment-workflow";
import { assignDramatisSearch, assignRareSearch, buyRareSearch, hireDramatisSearch, resolveDramatisSearch, resolveRareSearch, upgradeRareSearch } from "./features/searches/search-workflow";
import { resolveHirelingUpkeep } from "./features/hirelings/upkeep-workflow";
import { finalizePostBattle } from "./features/review/finalize-post-battle-workflow";
import { transferEquippedItem } from "./features/equipment/transfer-workflow";
import { setManualSkill } from "./features/advances/manual-skill-workflow";
import { addManualStashItem, correctResource } from "./features/economy/manual-corrections-workflow";
import { buyWeaponUpgrade } from "./features/economy/weapon-upgrade-workflow";
import { resolveEyeInjury, resolveHatred, resolvePrisoner } from "./features/injuries/injury-decisions-workflow";
import { resolveSoldToPits } from "./features/injuries/sold-to-pits-workflow";
import { resolveInjuryTableFollowUp } from "./features/injuries/injury-followup-workflow";
import { resolveScenarioEncampment, resolveScenarioSpellReward } from "./features/exploration/scenario-followups-workflow";
import { acknowledgeFollowUp, followUpNeedsResolution } from "./features/review/follow-up-acknowledgement-workflow";
import { selectedWarbandVariant, warbandVariants } from "../../domain/campaign/band-variants";
import { treasury } from "../../domain/campaign/kernel/document";

const HISTORY_LIMIT = 50;

function equipmentViolation(document: CampaignDocument, knowledge: CampaignAppDeps["knowledge"], warriorId: string, itemId: string, amount: number): string | null {
  const warrior=document.campaign.warriors.find((row)=>row.id===warriorId); const item=knowledge.queryKnowledge({id:{kind:"item_id",value:itemId}});
  if(!warrior)return "Choose a valid warrior and item.";
  if(!item.ok||!item.record)return null;
  const category=String(item.record.data["kind"]??""); const identity=[warrior.profile_name,warrior.profile_id,...warrior.skills,...(warrior.special_rules??[])].join(" ").replace(/[-_]/g," ").toLowerCase();
  const profile=warrior.profile_id?knowledge.queryKnowledge({id:{kind:"profile_id",value:warrior.profile_id}}):null;
  if(["armour","shield-or-defence"].includes(category)&&profile?.ok&&Array.isArray(profile.record.data["equipment_forbids"])&&profile.record.data["equipment_forbids"].includes("armour"))return "This warrior cannot wear armour, shields or bucklers.";
  if(["close-combat-weapon","ranged-weapon"].includes(category)&&warrior.profile_id&&!warrior.profile_id.startsWith("hireling.")){const access=profile?.ok&&Array.isArray(profile.record.data["equipment_access"])?profile.record.data["equipment_access"] as Readonly<Record<string,unknown>>[]:[];if(access.length&&!access.some((row)=>row["item_id"]===itemId)&&!/weapons? (training|expert)/.test(warrior.skills.join(" ").toLowerCase()))return "This weapon is outside the warrior's equipment access.";}
  if(itemId==="barbed_whip"&&warrior.kind!=="hero")return "Barbed Whip may only be assigned to a Marauders of Chaos Hero.";
  if(itemId==="great_axe"&&!(warrior.kind==="hero"&&identity.includes("chosen of chaos")))return "Great Axe requires a Marauders Hero with the Chosen of Chaos skill.";
  if(itemId==="reptile_venom"&&!(warrior.kind==="henchman"&&identity.includes("skink")))return "Reptile Venom may only be assigned to Skink Henchmen.";
  if(["familiar","arcane_familiar"].includes(itemId)&&!identity.includes("spellcaster"))return "A Familiar may only be assigned to a spellcaster.";
  if(itemId==="book_of_the_dead"&&!/(vampire|necromancer)/.test(identity))return "The Book of the Dead may only be assigned to Vampires or Necromancers.";
  if(itemId==="nightmare"&&!/(vampire|necromancer|grave guard)/.test(identity))return "A Nightmare may only be assigned to Vampires, Necromancers or Grave Guards.";
  if(itemId==="temple_dog"&&!/(dragon monk|sister|priest)/.test(identity))return "A Temple Dog may only be assigned to Dragon Monks, Sisters of Sigmar or Priests.";
  if(["barding","bretonnian_barding"].includes(itemId)&&!warrior.equipment.some((row)=>/(warhorse|horse)/i.test(`${row.name} ${row.item_id}`)))return "Barding requires this warrior to have a Warhorse.";
  if(["dark_elf_blade_weapon_upgrade","poisoned_weapon"].includes(itemId)&&!warrior.equipment.some((row)=>(knowledge as typeof knowledge & {weaponHandsFor?(id:string):number|null}).weaponHandsFor?.(row.base_item_id??row.item_id)!==null))return "This upgrade requires an equipped weapon.";
  if(itemId==="sword_heroes_only"&&warrior.kind!=="hero")return "This Sword variant may only be assigned to Heroes.";
  const restricted:Record<string,readonly string[]>={beastlash:["beastmaster"],broadsword:["chapel guard knight"],serpent_staff:["liche priest"],shortsword:["chapel guard knight"],nehekharan_javelin:["tomb lord"],swivel_gun:["gunner"],kite_shield:["chapel guard knight"],asp_arrows:["tomb lord"],conch_shell_horn:["piranha warrior"],elven_runestones:["weaver"],parrot:["captain","mate"]};
  if(restricted[itemId]&&!restricted[itemId].some((term)=>identity.includes(term)))return `${item.record.names["en"]??itemId} cannot be assigned to this warrior.`;
  const carried=warrior.equipment.filter((row)=>row.acquisition!=="fixed"), models=warrior.quantity??1;
  const hands=(knowledge as typeof knowledge & { weaponHandsFor?(id:string):number|null }).weaponHandsFor?.(itemId);
  const limit=warrior.equipment_limits?.["maximum_one_handed_weapons"];
  if(hands===1&&limit!==undefined){const carriedHands=carried.filter((row)=>(knowledge as typeof knowledge & { weaponHandsFor?(id:string):number|null }).weaponHandsFor?.(row.base_item_id??row.item_id)===1).reduce((sum,row)=>sum+row.quantity,0);if(carriedHands+amount>limit*models)return `Injury limits this warrior to ${limit} one-handed weapon(s) per model.`;}
  if(!["close-combat-weapon","ranged-weapon"].includes(category)&&carried.filter((row)=>row.item_id===itemId).reduce((sum,row)=>sum+row.quantity,0)+amount>models)return `${item.record.names["en"]??itemId} is already carried; a warrior carries one of these.`;
  return null;
}

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
  const fingerprint = (document: CampaignDocument): string => JSON.stringify({ campaign: document.campaign, pending_battle_draft: document.view.pending_battle_draft ?? null });
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
      const variants = warbandVariants(deps.knowledge, input.band_id);
      const variant = selectedWarbandVariant(deps.knowledge, input.band_id, input.variant);
      if (variants.length && !variant) return error("rejected", "Choose a valid warband variant.");
      if (!variants.length && input.variant) return error("rejected", "This warband has no variants.");
      const result = useCases.createDraft(input.band_id, deps.knowledge);
      if (!result.ok) return error("rejected", result.message, { reason: result.reason });
      const document = {
        ...result.state,
        campaign: {
          ...result.state.campaign,
          warriors: [],
          inventory: [],
          configuration: { ...result.state.campaign.configuration, ...(variant?.starting_gold ? { starting_gold: variant.starting_gold } : {}) },
          identity: { ...result.state.campaign.identity, campaign_name: input.campaign_name.trim(), warband_name: input.warband_name.trim(), mercenary_variant: variant?.id ?? null },
        },
      };
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
      const editable = !selected || selected === "draft:0" || selected.startsWith("new-battle:") || selected === `state:${state.current.campaign.current_state_number}` || (pending && selected === `post:${pending.battle_number}`);
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
        case "setMercenaryVariant": {
          if (!state.current.campaign.configuration.is_draft || state.current.campaign.identity.mercenary_variant) return error("rejected", "The warband variant is locked after selection.");
          const variant = selectedWarbandVariant(deps.knowledge, state.current.campaign.identity.band_id, String(input["variant"] ?? ""));
          if (!variant) return error("rejected", "Choose a valid warband variant.");
          const band = deps.knowledge.queryKnowledge({ id: { kind: "band_id", value: state.current.campaign.identity.band_id } });
          const roster = band.ok ? band.record.data["roster"] as Readonly<Record<string, unknown>> | undefined : undefined;
          const baseGold = typeof roster?.["starting_gold"] === "number" ? roster["starting_gold"] : state.current.campaign.configuration.starting_gold;
          const startingGold = state.current.campaign.configuration.starting_gold + (variant.starting_gold ?? baseGold) - baseGold;
          const warriors = state.current.campaign.warriors.map((warrior) => {
            const bonuses = warrior.profile_id ? variant.profile_bonuses?.[warrior.profile_id] ?? {} : {};
            return { ...warrior, stats: Object.fromEntries(Object.entries(warrior.stats).map(([key, value]) => [key, value + (bonuses[key] ?? 0)])) };
          });
          return applyResult({ ok: true, state: { ...state.current, campaign: { ...state.current.campaign, warriors, configuration: { ...state.current.campaign.configuration, starting_gold: startingGold }, identity: { ...state.current.campaign.identity, mercenary_variant: variant.id } } } });
        }
        case "setManualSkill": {
          const result = setManualSkill(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "correctResource": { const result=correctResource(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "addManualStashItem": { const result=addManualStashItem(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "buyWeaponUpgrade": { const result=buyWeaponUpgrade(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveEyeInjury": { const result=resolveEyeInjury(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveHatred": { const result=resolveHatred(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolvePrisoner": { const result=resolvePrisoner(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveSoldToPits": { const result=resolveSoldToPits(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveInjuryTableFollowUp": { const result=resolveInjuryTableFollowUp(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveScenarioSpellReward": { const result=resolveScenarioSpellReward(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveScenarioEncampment": { const result=resolveScenarioEncampment(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "acknowledgeFollowUp": { const result=acknowledgeFollowUp(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
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
          return applyResult({ ok: true, state: { ...state.current, view: { ...state.current.view, pending_battle_draft: { ...(state.current.view.pending_battle_draft ?? {}), battle_start_checks: checks } } } });
        }
        case "saveBattleDraft": {
          state.current = { ...state.current, view: { ...state.current.view, pending_battle_draft: { ...((input["draft"] as Record<string, unknown> | undefined) ?? {}), battle_start_checks: state.current.view.pending_battle_draft?.["battle_start_checks"] } } };
          notify();
          return { ok: true, document: state.current };
        }
        case "recordBattle": {
          const checks = (state.current.view.pending_battle_draft?.["battle_start_checks"] ?? {}) as Record<string, { misses_battle?: boolean }>;
          const pendingChecks = state.current.campaign.warriors.filter((warrior) => (warrior.games_to_miss ?? 0) === 0).flatMap((warrior) => (warrior.battle_start_checks ?? []).map((check) => `${warrior.id}:${String(check["check_id"] ?? "")}`)).filter((key) => !checks[key]);
          if (pendingChecks.length) return error("rejected", "Resolve all pre-battle injury checks before recording the battle.");
          const unavailable = new Set(Object.entries(checks).filter(([, value]) => value.misses_battle).map(([key]) => key.split(":")[0]));
          const outOfAction = Array.isArray(input["out_of_action_ids"]) ? input["out_of_action_ids"].map(String) : [];
          if (outOfAction.some((id) => unavailable.has(id))) return error("rejected", "Warriors excluded by a pre-battle injury check cannot be taken out of action.");
          const participants = state.current.campaign.warriors.filter((warrior) => (warrior.games_to_miss ?? 0) === 0 && !unavailable.has(warrior.id)).map((warrior) => warrior.id);
          const absentees = state.current.campaign.warriors.filter((warrior) => !participants.includes(warrior.id)).map((warrior) => ({ id: warrior.id, name: warrior.name, quantity: warrior.quantity ?? 1, reason: unavailable.has(warrior.id) ? "Old Battle Wound" : warrior.absence_reason ?? "Injury", ...(warrior.games_to_miss && warrior.games_to_miss > 0 ? { remaining_before: warrior.games_to_miss } : {}) }));
          const result = useCases.recordBattle(state.current, { ...input, out_of_action_ids: outOfAction, participants, absentees } as never, knowledge);
          if (!result.ok) return applyResult(result);
          const number = result.state.campaign.battles.at(-1)?.number;
          const view = { ...result.state.view, ...(number === undefined ? {} : { selected_moment: `battle:${number}` as const }) };
          delete view.pending_battle_draft;
          return applyResult({ ok: true, state: { ...result.state, view } });
        }
        case "resolvePostBattleStep":
          {
            const post = state.current.campaign.post_battles.find((row) => !row.complete);
            const battle = post && state.current.campaign.battles.find((row) => row.number === post.battle_number);
            if (!post || !battle) return error("rejected", "There is no pending post-battle sequence.");
            const stepMatches = (row: Readonly<Record<string, unknown>>) => String(row["step"] ?? "") === String(post.active_step) || (post.active_step === 0 && row["step"] === "injuries") || (post.active_step === 2 && String(row["step"] ?? "") === "3");
            const unresolved = (post.pending_follow_ups ?? []).some((row) => stepMatches(row) && followUpNeedsResolution(row, post.acknowledgements ?? {}));
            const injuries = new Map<string, number>();
            for (const id of battle.out_of_action_ids ?? []) injuries.set(id, (injuries.get(id) ?? 0) + 1);
            const resolvedInjuries=(post.step_state?.["injuries"]??{}) as Record<string,unknown>;
            if (post.active_step === 0 && ([...injuries].some(([id, count]) => !Array.from({ length: count }, (_, index) => index + 1).every((casualtyIndex) => Boolean(resolvedInjuries[`${id}:${casualtyIndex}`])||state.current!.campaign.warriors.find((warrior) => warrior.id === id)?.injury_records?.some((record) => Number(record["battle_number"]) === battle.number && Number(record["casualty_index"] ?? 1) === casualtyIndex))) || unresolved)) return error("rejected", "Resolve every serious injury and its follow-ups before continuing.");
            if (post.active_step === 1 && (!post.experience_applied || (post.pending_advances ?? []).some((row) => !row["committed"]) || unresolved)) return error("rejected", "Resolve experience, every advance and follow-up before continuing.");
            if (post.active_step === 2 && (!(post.step_state?.["exploration"] as Record<string, unknown> | undefined)?.["resolved"] || unresolved)) return error("rejected", "Resolve exploration and its follow-ups before continuing.");
            if (post.active_step === 3 && !post.sale_resolved) return error("rejected", "Resolve the wyrdstone sale before continuing.");
            if (post.active_step === 4 && !(post.step_state?.["veterans"] as Record<string, unknown> | undefined)?.["resolved"]) return error("rejected", "Resolve veteran availability before continuing.");
            if (post.active_step === 5 && unresolved) return error("rejected", "Resolve every rare-search and Dramatis follow-up before continuing.");
            if (post.active_step === 7) return error("rejected", "Confirm the next state from the review after resolving equipment obligations.");
            return applyResult(useCases.resolvePostBattleStep(state.current, Number(input["battle_number"]), input as never));
          }
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
        case "recruitBandProfile": {
          const result = recruitBandProfile(state.current, knowledge, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "dismissRecruit": {
          const result = dismissRecruit(state.current, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "resolveHirelingUpkeep": {
          const result = resolveHirelingUpkeep(state.current, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
        case "finalizePostBattle": {
          const battleNumber = state.current.campaign.post_battles.find((row) => !row.complete)?.battle_number;
          const result = finalizePostBattle(state.current);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: { ...result.document, view: { ...result.document.view, selected_moment: `post:${battleNumber}` } } });
        }
        case "assignRareSearch": { const result=assignRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "assignDramatisSearch": { const result=assignDramatisSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveRareSearch": { const result=resolveRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "resolveDramatisSearch": { const result=resolveDramatisSearch(state.current,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "buyRareSearch": { const result=buyRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "upgradeRareSearch": { const result=upgradeRareSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "hireDramatisSearch": { const result=hireDramatisSearch(state.current,knowledge,input as never);if(!result.ok)return error("rejected",result.message);return applyResult({ok:true,state:result.document}); }
        case "assignEquipment": {
          const warriorId=String(input["warrior_id"]??""), itemId=String(input["item_id"]??""), direction=input["direction"];
          const warrior=state.current.campaign.warriors.find((row)=>row.id===warriorId);
          if(!warrior||!itemId||(direction!=="equip"&&direction!=="stash")) return error("rejected", "Choose a valid warrior, item and equipment move.", { reason: !warrior ? "not_found" : "invalid_input" });
          const trading=(knowledge as typeof knowledge & { campaignSection?(section:string):Readonly<Record<string,unknown>> }).campaignSection?.("trading-post");
          const tradingEntry=(Array.isArray(trading?.["items"])?trading["items"] as Readonly<Record<string,unknown>>[]:[]).find((row)=>row["item_id"]===itemId);
          const heroesOnly=(Array.isArray(tradingEntry?.["restrictions"])?tradingEntry["restrictions"] as Readonly<Record<string,unknown>>[]:[]).some((row)=>row["type"]==="heroes_only");
          if(direction==="equip"&&heroesOnly&&warrior.kind!=="hero") return error("rejected", "This item may only be assigned to Heroes.");
          if(direction==="equip"&&warrior.profile_id&&!warrior.profile_id.startsWith("hireling.")) {
            const profile=knowledge.queryKnowledge({id:{kind:"profile_id",value:warrior.profile_id}}), item=knowledge.queryKnowledge({id:{kind:"item_id",value:itemId}});
            if(profile.ok) {
              const access=Array.isArray(profile.record.data["equipment_access"])?profile.record.data["equipment_access"] as Readonly<Record<string,unknown>>[]:[], fixed=Array.isArray(profile.record.data["fixed_equipment"])?profile.record.data["fixed_equipment"].map(String):[], restricted=Array.isArray(profile.record.data["equipment_restrictions"])?profile.record.data["equipment_restrictions"]:[];
              if(!access.length&&restricted.length&&!fixed.includes(itemId)) return error("rejected", "This profile cannot carry purchased equipment.");
              const weapon=item.ok&&["close-combat-weapon","ranged-weapon"].includes(String(item.record.data["kind"]??"")), allowed=access.some((row)=>String(row["item_id"]??"")===itemId), trained=warrior.skills.some((skill)=>/weapons? (training|expert)/i.test(skill));
              if(weapon&&access.length&&!allowed&&!trained) return error("rejected", "This weapon is outside the warrior's equipment access.");
            }
          }
          const carriedEntries=warrior.equipment.filter((row)=>row.item_id===itemId&&row.acquisition!=="fixed"), carried=carriedEntries.reduce((total,row)=>total+row.quantity,0);
          const quantity=warrior.kind!=="henchman"?Number(input["quantity"]):direction==="equip"?Math.max(0,(warrior.quantity??1)-carried%(warrior.quantity??1)):Math.min(warrior.quantity??1,carried);
          if(!Number.isInteger(quantity)||quantity<=0)return error("rejected", "This group has no transferable copies of that item.");
          if(direction==="equip"){const violation=equipmentViolation(state.current,knowledge,warriorId,itemId,quantity);if(violation)return error("rejected",violation);}
          const result=useCases.assignEquipment(state.current, { warrior_id:warriorId,item_id:itemId,quantity,direction });
          if(!result.ok)return applyResult(result);
          const resultPost=result.state.campaign.post_battles.find((row)=>!row.complete);
          if(!resultPost)return applyResult(result);
          const obligations=(resultPost.equipment_obligations??[]).flatMap((obligation)=>{const subject=result.state.campaign.warriors.find((row)=>row.id===String(obligation["warrior_id"]??""));if(!subject)return[];const required=(subject.quantity??1)*Number(obligation["copies_per_model"]??1),carried=subject.equipment.filter((row)=>row.item_id===String(obligation["item_id"]??"")).reduce((sum,row)=>sum+row.quantity,0),missing=Math.max(0,required-carried);return missing?[{...obligation,quantity:missing}]:[];});
          return applyResult({ok:true,state:{...result.state,campaign:{...result.state.campaign,post_battles:result.state.campaign.post_battles.map((row)=>row===resultPost?{...row,equipment_obligations:obligations}:row)}}});
        }
        case "transferEquippedItem": {
          const targetId=String(input["target_id"]??""),itemId=String(input["item_id"]??""),target=state.current.campaign.warriors.find((row)=>row.id===targetId),amount=target?.kind==="henchman"?(target.quantity??1):1;
          const violation=target?equipmentViolation(state.current,knowledge,targetId,itemId,amount):"Choose a valid destination.";if(violation)return error("rejected",violation);
          const result = transferEquippedItem(state.current, input as never);
          if (!result.ok) return error("rejected", result.message);
          return applyResult({ ok: true, state: result.document });
        }
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
          const draft = state.current.campaign.configuration.is_draft;
          if (!post && !draft) return error("rejected", "Hired Swords can only be hired during warband creation or post-battle.");
          const listedCosts = Array.isArray(input["fee_resources"]) ? input["fee_resources"].filter((row): row is [string, number] => Array.isArray(row) && typeof row[0] === "string" && Number.isInteger(row[1])) : [];
          const fee = Number(input["fee"]);
          if ((!Number.isInteger(fee) || fee < 0) && listedCosts.length === 0) return error("rejected", "Resolve the hiring fee before hiring.");
          const currentSnapshot = state.current.campaign.states.find((row) => row.number === state.current!.campaign.current_state_number) ?? state.current.campaign.states.at(-1);
          const availableGold = draft ? treasury(state.current.campaign) : (currentSnapshot?.gold ?? 0) + (post?.gold_delta ?? 0);
          const gold = Number.isInteger(fee) ? fee : (listedCosts.find(([key]) => key === "gold_crowns")?.[1] ?? 0);
          if (gold > availableGold) return error("rejected", `Not enough gold: ${gold} gc needed, ${availableGold} available.`);
          const shards = listedCosts.find(([key]) => key === "wyrdstone_fragments")?.[1] ?? 0;
          if (shards > (currentSnapshot?.wyrdstone ?? 0) + (post?.wyrdstone_delta ?? 0)) return error("rejected", "Not enough wyrdstone shards for this hire.");
          const result = useCases.hireHireling(state.current, { ...input, ...(Number.isInteger(fee) ? { fee } : {}) } as never, knowledge);
          if (!result.ok) return applyResult(result);
          if (draft) return applyResult(result);
          const resultPost = result.state.campaign.post_battles.find((row) => !row.complete);
          if (!resultPost) return error("rejected", "Pending post-battle disappeared while hiring.");
          const changed = { ...resultPost, gold_delta: (resultPost.gold_delta ?? 0) - gold, wyrdstone_delta: (resultPost.wyrdstone_delta ?? 0) - shards, event_log: [...(resultPost.event_log ?? []), { step: 6, type: "hire", profile_id: input["profile_id"], description: `Hired for ${listedCosts.map(([key,value]) => `${value} ${key}`).join(" + ") || `${gold} gc`}.` }] };
          const treasures = listedCosts.find(([key]) => key === "treasures")?.[1] ?? 0;
          const points = listedCosts.find(([key]) => key === "campaign_points")?.[1] ?? 0;
          if (treasures > result.state.campaign.resources.treasures || points > result.state.campaign.resources.campaign_points) return error("rejected", "Not enough declared hiring resources.");
          return applyResult({ ok: true, state: { ...result.state, campaign: { ...result.state.campaign, resources: { ...result.state.campaign.resources, treasures: result.state.campaign.resources.treasures - treasures, campaign_points: result.state.campaign.resources.campaign_points - points }, post_battles: result.state.campaign.post_battles.map((row) => row === resultPost ? changed : row) } } });
        }
        case "buyTradingItem": {
          const post = state.current.campaign.post_battles.find((row) => !row.complete);
          if (!post) return error("rejected", "Trading is only available during post-battle.");
          const itemId = String(input["item_id"] ?? "");
          const quantity = Number(input["quantity"]), unitPrice = Number(input["unit_price"]);
          if (!itemId || !Number.isInteger(quantity) || quantity <= 0 || !Number.isInteger(unitPrice) || unitPrice < 0) return error("rejected", "A valid item, quantity and price are required.");
          const catalogue = (knowledge as typeof knowledge & { campaignSection?(section:string):Readonly<Record<string,unknown>> }).campaignSection?.("trading-post");
          const catalogueItems = Array.isArray(catalogue?.["items"]) ? catalogue["items"] as Readonly<Record<string,unknown>>[] : [];
          const catalogueEntry = catalogueItems.find((row) => row["item_id"] === itemId);
          if (!catalogueEntry) return error("rejected", "This item is not listed at the Trading Post.");
          const availability=(catalogueEntry["availability"]??{}) as Readonly<Record<string,unknown>>;
          if (availability["kind"]!=="common") return error("rejected", "Rare items must be obtained through a successful rare search.");
          const price=(catalogueEntry["price"]??{}) as Readonly<Record<string,unknown>>, base=Number(price["base_gc"]??0), variable=(price["optional_variable_cost"]??{}) as Readonly<Record<string,unknown>>, dice=(variable["dice"]??{}) as Readonly<Record<string,unknown>>, count=Number(dice["count"]??0), sides=Number(dice["sides"]??0), multiplier=Number(variable["multiplier"]??1);
          if (!Number.isInteger(base)||base<0) return error("rejected", "This Trading Post item has no supported price.");
          if (count&&sides) { const rolled=(unitPrice-base)/multiplier; if(!Number.isInteger(rolled)||rolled<count||rolled>count*sides)return error("rejected", "The variable price does not match this item's dice range."); }
          else if(unitPrice!==base) return error("rejected", `Invalid item price: expected ${base} gc.`);
          const restrictions = Array.isArray(catalogueEntry?.["restrictions"]) ? catalogueEntry["restrictions"] as Readonly<Record<string,unknown>>[] : [];
          const groups=new Set(((knowledge as typeof knowledge & { list?(kind:string):readonly Readonly<Record<string,unknown>>[] }).list?.("warband_group")??[]).filter((row)=>Array.isArray(row["band_ids"])&&(row["band_ids"] as unknown[]).map(String).includes(state.current!.campaign.identity.band_id)).map((row)=>String(row["id"]??"")));
          for(const restriction of restrictions) { const bandIds=(restriction["band_ids"]??[]) as unknown[], groupIds=(restriction["groups"]??[]) as unknown[],matches=bandIds.map(String).includes(state.current.campaign.identity.band_id)||groupIds.map(String).some((id)=>groups.has(id)); if(restriction["type"]==="warband_only"&&!matches)return error("rejected", "This item is not available to this warband."); if(restriction["type"]==="warband_forbidden"&&matches)return error("rejected", "This item is forbidden to this warband."); if(restriction["type"]==="condition")return error("rejected", String(restriction["note"]??"This item cannot be purchased at the Trading Post.")); }
          const inferredOne = restrictions.some((row) => row["type"] === "profile_only" && String(row["note"] ?? "").toLocaleLowerCase().startsWith("one "));
          const declaredLimit = restrictions.find((row) => row["type"] === "limit_per_warband")?.["value"];
          const limit = Number.isInteger(declaredLimit) ? Number(declaredLimit) : inferredOne ? 1 : null;
          const owned = state.current.campaign.inventory.filter((row) => row.id === itemId).reduce((sum, row) => sum + row.owned, 0);
          if (limit !== null && owned + quantity > limit) return error("rejected", `Warband limit reached: at most ${limit} of this item (own ${owned}).`);
          const snapshot = state.current.campaign.states.find((row) => row.number === state.current!.campaign.current_state_number) ?? state.current.campaign.states.at(-1);
          const available = (snapshot?.gold ?? 0) + (post.gold_delta ?? 0), total = quantity * unitPrice;
          if (total > available) return error("rejected", `Not enough gold: ${total} gc needed, ${available} available.`);
          const known=knowledge.queryKnowledge({id:{kind:"item_id",value:itemId}}), name=known.ok?String(known.record.names["en"]??itemId):itemId, category=known.ok?String(known.record.data["kind"]??"Trading Post"):"Trading Post";
          const found = state.current.campaign.inventory.find((row) => row.id === itemId);
          const inventory = found ? state.current.campaign.inventory.map((row) => row.id === itemId ? { ...row, owned: row.owned + quantity, stash: row.stash + quantity, value: unitPrice } : row) : [...state.current.campaign.inventory, { id: itemId, name, category, owned: quantity, equipped: 0, stash: quantity, value: unitPrice }];
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
