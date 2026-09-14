/**
 * Battle workflow: battle recording feature —
 * application-layer orchestration over the P3.5 kernel `recordBattle` and
 * `resolvePostBattleStep` use cases.
 *
 * Owns the *workflow* of playing a battle:
 *  1. `readiness` — who can fight (absences block; the kernel rejects
 *     results naming unavailable warriors);
 *  2. `record` — validate table facts, snapshot numbers, append the battle
 *     and open the pending post-battle;
 *  3. `resolveStep` — walk the eight post-battle steps forward; step input
 *     payloads are preserved verbatim (contract open-payload policy).
 *
 * The UI never calls domain use cases directly; everything flows through
 * this workflow so the P5.1 service keeps undo/history and the dirty flag.
 * All results are values — no exceptions cross layers.
 *
 * Purity: no React, no DOM, no filesystem. The KB is read through the
 * injected `KnowledgeReader` only.
 */

import type {
  CampaignDocument,
  IdString,
  KnowledgeReader,
  OpenPayloadInput,
  UseCaseResult,
} from "../../../../domain/campaign/index";
import type { CampaignUseCases } from "../../../../domain/campaign/index";

/** A warrior row with the availability facts the UI shows. */
export interface AvailabilityRow {
  readonly warrior_id: IdString;
  readonly name: string;
  readonly kind: string;
  readonly quantity: number;
  readonly available: boolean;
  readonly reason: string | null;
}

/** Why a workflow step failed (stable reasons for the UI). */
export type BattleWorkflowError =
  | { readonly ok: false; readonly reason: "no_campaign" | "not_found" | "rejected"; readonly message: string };

export type BattleWorkflowResult =
  | { readonly ok: true; readonly document: CampaignDocument }
  | BattleWorkflowError;

function fromUseCase(result: UseCaseResult): BattleWorkflowResult {
  if (result.ok) return { ok: true, document: result.state };
  return { ok: false, reason: "rejected", message: result.message };
}

/** Input of `record` — mirrors the frozen `RecordBattleInput` fields the UI collects. */
export interface RecordBattleRequest {
  readonly scenario: IdString;
  readonly opponent: string;
  readonly result: "win" | "loss" | "draw";
  readonly gold_delta: number;
  readonly wyrdstone: number;
  readonly xp_delta: number;
  readonly out_of_action_ids: readonly IdString[];
  readonly notes?: string;
}

/** Dependencies of the battle workflow (a slice of the P5.1 service world). */
export interface BattleWorkflowDeps {
  readonly knowledge: KnowledgeReader;
  readonly useCases: CampaignUseCases;
  /** Canonical scenario ids offered by the picker (P8.1 generates this). */
  readonly scenarioCandidates?: readonly IdString[];
}

export function createBattleWorkflow(deps: BattleWorkflowDeps) {
  const { knowledge, useCases } = deps;
  const scenarioCandidates = deps.scenarioCandidates ?? [
    "skirmish",
    "search-and-destroy",
    "hidden-treasure",
    "raid",
    "defend-the-find",
    "breakthrough",
  ];

  return {
    /** Scenario picker options: candidates resolved against the KB. */
    scenarioOptions(): { readonly id: IdString; readonly name: string }[] {
      const options: { id: IdString; name: string }[] = [];
      for (const id of scenarioCandidates) {
        const result = knowledge.queryKnowledge({ id: { kind: "scenario_id", value: id } });
        if (!result.ok) continue;
        const names = result.record.names as Readonly<Record<string, string>>;
        options.push({ id, name: names["en"] ?? id });
      }
      return options;
    },

    /** Who can fight the next battle (absences block; availability checks are
     * handled by the application workflow).
     */
    readiness(document: CampaignDocument): AvailabilityRow[] {
      return document.campaign.warriors.map((warrior) => {
        const absent = (warrior.games_to_miss ?? 0) > 0;
        return {
          warrior_id: warrior.id,
          name: warrior.name,
          kind: warrior.kind,
          quantity: warrior.quantity ?? 1,
          available: !absent,
          reason: absent ? (warrior.absence_reason ?? "Injury") : null,
        };
      });
    },

    /** True while a post-battle sequence is pending (blocks the next battle). */
    hasPendingPostBattle(document: CampaignDocument): boolean {
      return document.campaign.post_battles.some((post) => !post.complete);
    },

    /** The pending post-battle (step state for the UI), or null. */
    pendingPostBattle(document: CampaignDocument) {
      return document.campaign.post_battles.find((post) => !post.complete) ?? null;
    },

    /** Step 2 — record the battle and open its pending post-battle. */
    record(document: CampaignDocument, request: RecordBattleRequest): BattleWorkflowResult {
      const available = this.readiness(document);
      const unavailable = new Set(
        available.filter((row) => !row.available).map((row) => row.warrior_id),
      );
      const unknown = request.out_of_action_ids.filter(
        (id) => !available.some((row) => row.warrior_id === id),
      );
      if (unknown.length > 0) {
        return { ok: false, reason: "not_found", message: `Unknown warrior id: ${unknown[0]}.` };
      }
      const blocked = request.out_of_action_ids.filter((id) => unavailable.has(id));
      if (blocked.length > 0) {
        const names = blocked
          .map((id) => available.find((row) => row.warrior_id === id)?.name ?? id)
          .join(", ");
        return {
          ok: false,
          reason: "rejected",
          message: `Unavailable warriors cannot receive battle results: ${names}.`,
        };
      }
      const input = {
        ...request,
        casualties: request.out_of_action_ids.length,
        ...(request.notes ? { notes: request.notes } : {}),
      };
      return fromUseCase(useCases.recordBattle(document, input, knowledge));
    },

    /** Step 3 — resolve the active post-battle step (forward-only). */
    resolveStep(document: CampaignDocument, input: OpenPayloadInput): BattleWorkflowResult {
      const pending = this.pendingPostBattle(document);
      if (!pending) {
        return { ok: false, reason: "rejected", message: "There is no pending post-battle sequence." };
      }
      return fromUseCase(
        useCases.resolvePostBattleStep(document, pending.battle_number, input),
      );
    },
  };
}

export type BattleWorkflow = ReturnType<typeof createBattleWorkflow>;
