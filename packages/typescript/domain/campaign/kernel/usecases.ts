/**
 * P3.4 (web-migration-parallel-plan.md §4): frozen public use-case surface.
 * Operations return explicit results — rejected operations are values, not
 * thrown exceptions — so the application layer (P5.1) presents them without
 * try/catch discipline, and parallel feature blocks (P6.x) share one calling
 * convention.
 *
 * Purity: no React, no browser, no filesystem. Ports are injected.
 */

import type {
  Battle,
  CampaignDocument,
  IdString,
  MomentSelection,
} from "./state";
import type { KnowledgeReader } from "./ports";

/** Why a use case refused to run (stable reasons; UI maps them to messages). */
export type UseCaseRejectionReason =
  | "not_found"
  | "invalid_input"
  | "limit_reached"
  | "limit_violated"
  | "not_available"
  | "not_permitted_in_draft"
  | "not_permitted_when_committed"
  | "prerequisite_missing"
  | "conflict";

export interface UseCaseRejection {
  readonly ok: false;
  readonly reason: UseCaseRejectionReason;
  /** Human-readable, actionable; safe to show in UI. */
  readonly message: string;
  /** Ids involved (warrior, item, step...), for tests and diagnostics. */
  readonly subject_ids?: readonly IdString[];
}

export type UseCaseResult = { readonly ok: true; readonly state: CampaignDocument } | UseCaseRejection;

/** Input for the draft phase: compose the initial warband. */
export interface DraftCompositionInput {
  /** Stable KB id of the chosen warband. */
  readonly band_id: IdString;
  /** Profile rows added so far, as profile_id + role. */
  readonly rows: readonly {
    readonly profile_id: IdString;
    readonly kind: "hero" | "henchman";
    readonly quantity: number;
    readonly equipment: readonly IdString[];
  }[];
}

export interface RecordBattleInput {
  readonly scenario: string;
  readonly opponent: string;
  readonly opponent_band_id?: IdString;
  readonly result: Battle["result"];
  readonly gold_delta: number;
  readonly wyrdstone: number;
  readonly xp_delta: number;
  readonly casualties: number;
  readonly out_of_action_ids: readonly IdString[] | null;
  readonly participants?: readonly IdString[];
  /** Warriors excluded before deployment, with a display reason. */
  readonly absentees?: readonly OpenPayload[];
  readonly notes?: string;
  /** Per-warrior XP awards (enemy OOA ownership, desktop `xp_awards`). */
  readonly xp_awards?: Readonly<Record<string, number>>;
  /** Structured scenario-reward payload, preserved in place (open payload). */
  readonly scenario_results?: Record<string, unknown>;
}

export interface AdvanceChoiceInput {
  readonly warrior_id: IdString;
  /** Which advance table/roll the player picks. */
  readonly table: string;
  readonly choice: string;
}

/**
 * Pure campaign use cases. Implementations live in P3.5 (kernel behaviour)
 * and P6.x feature blocks; every function is synchronous and returns a new
 * document, never mutating its input.
 */
export interface CampaignUseCases {
  /** Draft: create an empty draft for a warband. */
  createDraft(bandId: IdString, knowledge: KnowledgeReader): UseCaseResult;

  /** Draft: compose rows and validate gold/model/hero limits. */
  composeDraft(document: CampaignDocument, input: DraftCompositionInput): UseCaseResult;

  /** Draft → State #0: freeze construction limits, fold fixed equipment. */
  commitInitialWarband(document: CampaignDocument, knowledge: KnowledgeReader): UseCaseResult;

  /** Move the view selection without touching campaign state. */
  selectMoment(document: CampaignDocument, moment: MomentSelection): UseCaseResult;

  /** Record a battle: validate pre-battle availability, append battle + pending post-battle. */
  recordBattle(document: CampaignDocument, input: RecordBattleInput, knowledge: KnowledgeReader): UseCaseResult;

  /** Post-battle: navigate steps / resolve the active one. */
  resolvePostBattleStep(document: CampaignDocument, battleNumber: number, input: OpenPayloadInput): UseCaseResult;

  /** Post-battle: apply a warrior advance choice (P6.6). */
  applyAdvance(document: CampaignDocument, input: AdvanceChoiceInput): UseCaseResult;

  /** Inventory: assign/withdraw equipment between stash and warriors (P6.3). */
  assignEquipment(
    document: CampaignDocument,
    input: { warrior_id: IdString; item_id: IdString; quantity: number; direction: "equip" | "stash" },
  ): UseCaseResult;

  /** Hirelings: resolve hiring eligibility and hire (P6.7). */
  hireHireling(document: CampaignDocument, input: { profile_id: IdString }, knowledge: KnowledgeReader): UseCaseResult;

  /** Trading: buy an item into the stash (P6.7). */
  buyTradingItem(document: CampaignDocument, input: BuyTradingItemInput): UseCaseResult;

  /** Trading: sell from the stash, booking a manual-log entry (P6.7). */
  sellStashItem(document: CampaignDocument, input: SellStashItemInput): UseCaseResult;

  /** Export preparation: validate the whole state before serialization (P6.8). */
  validateForExport(document: CampaignDocument): UseCaseResult;
}

export interface OpenPayloadInput {
  readonly [key: string]: unknown;
}

/** P6.7 trading inputs (re-exported from the kernel implementation). */
export type { BuyTradingItemInput, SellStashItemInput } from "./trading";
import type { BuyTradingItemInput, SellStashItemInput } from "./trading";

/** Re-export the state/ports types as the package's public surface. */
export type {
  Battle,
  Campaign,
  CampaignDocument,
  DraftConfiguration,
  EquipmentEntry,
  IdString,
  InventoryItem,
  MomentSelection,
  PostBattle,
  Warrior,
} from "./state";
export type { CampaignFilePort, KnowledgeReader, KnowledgeResult } from "./ports";
