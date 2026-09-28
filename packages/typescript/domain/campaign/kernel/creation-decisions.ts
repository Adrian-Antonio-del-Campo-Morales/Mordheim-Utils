/**
 * T10: warband-creation decisions.
 *
 * Some printed band rules ask for a roll while the warband is being created
 * (`imperial-noble--family-heirloom`: "When creating the warband roll a D6 to
 * see what its power is"). The KB publishes each of those rolls as data in
 * `campaign.recruitment-and-veterans.creation_decisions` (band, rule, recipient
 * profiles, dice and the printed outcome of every interval), so this module
 * never reads the rule prose.
 *
 * Contract:
 * - a decision is *owed* while the draft roster holds one of its recipient
 *   profiles and the printed rule is declared `required`;
 * - the dice are injected by the caller (the same convention as exploration,
 *   the veteran pool and the injury tables) and the roll order is the order in
 *   which the results were recorded;
 * - the recorded outcome is persisted in `campaign.special_rules` — the v5
 *   free-form campaign effect list — keyed by the stable `decision_id` and
 *   `outcome_id`, never by a translated sentence;
 * - a campaign file written before the decision existed simply has no entry, so
 *   it loads unchanged and the decision becomes owed again.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignDocument, IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import type { UseCaseResult } from "../index";
import { withCampaign } from "./document";

/** Stable marker of a recorded creation decision inside `special_rules`. */
export const CREATION_DECISION_MARKER = "creation_decision";

/** Reader that can also reach the published campaign catalogues. */
export type CreationDecisionReader = KnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

export interface CreationDecisionOutcome {
  readonly result_id: IdString;
  readonly min: number;
  readonly max: number;
  readonly result: string;
  readonly result_i18n: Readonly<Record<string, string>>;
}

export interface CreationDecisionFacts {
  readonly id: IdString;
  readonly band_id: IdString;
  readonly rule_id: IdString;
  readonly profile_ids: readonly IdString[];
  readonly name: string;
  readonly name_i18n: Readonly<Record<string, string>>;
  readonly required: boolean;
  readonly dice: { readonly count: number; readonly sides: number };
  readonly outcomes: readonly CreationDecisionOutcome[];
}

function names(value: unknown): Readonly<Record<string, string>> {
  if (!value || typeof value !== "object") return {};
  const out: Record<string, string> = {};
  for (const [key, text] of Object.entries(value as OpenPayload)) {
    if (typeof text === "string" && text.trim()) out[key] = text;
  }
  return out;
}

function outcomesOf(value: unknown): readonly CreationDecisionOutcome[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];
    const row = entry as OpenPayload;
    const when = (row["when"] ?? {}) as OpenPayload;
    const resultId = String(row["result_id"] ?? "");
    const result = String(row["result"] ?? "");
    const min = Number(when["min"]);
    if (!resultId || !result || !Number.isInteger(min)) return [];
    const max = when["max"] == null ? min : Number(when["max"]);
    return [{
      result_id: resultId,
      min,
      max: Number.isInteger(max) ? max : min,
      result,
      result_i18n: names(row["result_i18n"]),
    }];
  });
}

/** Every creation decision the artefact publishes for a band, in catalogue order. */
export function creationDecisionsOf(
  reader: CreationDecisionReader,
  bandId: IdString,
): readonly CreationDecisionFacts[] {
  const section = reader.campaignSection?.("recruitment-and-veterans");
  const rows = section?.["creation_decisions"];
  if (!Array.isArray(rows)) return [];
  return rows.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];
    const row = entry as OpenPayload;
    const dice = ((row["roll"] as OpenPayload | undefined)?.["dice"] ?? {}) as OpenPayload;
    const id = String(row["id"] ?? "");
    if (!id || String(row["band_id"] ?? "") !== bandId) return [];
    const count = Number(dice["count"] ?? 1);
    const sides = Number(dice["sides"] ?? 6);
    return [{
      id,
      band_id: String(row["band_id"] ?? ""),
      rule_id: String(row["rule_id"] ?? ""),
      profile_ids: Array.isArray(row["profile_ids"]) ? row["profile_ids"].map(String) : [],
      name: String(row["name"] ?? id),
      name_i18n: names(row["name_i18n"]),
      // Absent `required` means required: a printed creation roll cannot be
      // skipped, and an explicit `false` is the only way to declare it optional.
      required: row["required"] !== false,
      dice: { count: Number.isInteger(count) && count > 0 ? count : 1, sides: Number.isInteger(sides) && sides > 0 ? sides : 6 },
      outcomes: outcomesOf(row["outcomes"]),
    }];
  });
}

/** Recorded outcome of a decision, or `null` while it is still owed. */
export function recordedCreationDecision(
  document: CampaignDocument,
  decisionId: IdString,
): OpenPayload | null {
  return document.campaign.special_rules.find(
    (row) => row["kind"] === CREATION_DECISION_MARKER && row["decision_id"] === decisionId,
  ) ?? null;
}

/**
 * Decisions the current draft still owes: required, with a recipient present in
 * the roster, and without a recorded outcome.
 */
export function owedCreationDecisions(
  document: CampaignDocument,
  reader: CreationDecisionReader,
): readonly CreationDecisionFacts[] {
  const bandId = document.campaign.identity.band_id;
  if (!bandId) return [];
  const present = new Set(document.campaign.warriors.map((warrior) => warrior.profile_id ?? ""));
  return creationDecisionsOf(reader, bandId).filter(
    (decision) =>
      decision.required &&
      decision.profile_ids.some((profileId) => present.has(profileId)) &&
      recordedCreationDecision(document, decision.id) === null,
  );
}

/** Printed outcome the roll reaches, or `null` when the roll is outside the table. */
export function creationDecisionOutcomeFor(
  decision: CreationDecisionFacts,
  total: number,
): CreationDecisionOutcome | null {
  return decision.outcomes.find((outcome) => total >= outcome.min && total <= outcome.max) ?? null;
}

/**
 * Record one creation roll. The caller injects the dice total (already rolled,
 * exactly like the exploration and injury tables) and the outcome reaches the
 * warband's persistent `special_rules`.
 */
export function resolveCreationDecision(
  document: CampaignDocument,
  reader: CreationDecisionReader,
  input: { readonly decision_id: IdString; readonly roll: number },
): UseCaseResult {
  const bandId = document.campaign.identity.band_id;
  const decision = creationDecisionsOf(reader, bandId).find((row) => row.id === input.decision_id);
  if (!decision) {
    return {
      ok: false,
      reason: "not_found",
      message: `Unknown creation decision "${input.decision_id}" for ${bandId || "an empty identity"}.`,
      subject_ids: [input.decision_id],
    };
  }
  // A printed creation roll belongs to the creation phase: it is recorded while
  // the roster is being built, never inserted later as a persistent effect in the
  // middle of a post-battle.
  if (!document.campaign.configuration.is_draft) {
    return {
      ok: false,
      reason: "not_permitted_when_committed",
      message: `${decision.name} is rolled while the warband is created.`,
      subject_ids: [decision.id],
    };
  }
  // The roll must be owed by the roster in front of it: a decision whose
  // recipient profiles are absent would only persist an effect nobody carries.
  const profiles = new Set(document.campaign.warriors.map((warrior) => warrior.profile_id ?? ""));
  if (decision.profile_ids.length > 0 && !decision.profile_ids.some((profileId) => profiles.has(profileId))) {
    return {
      ok: false,
      reason: "prerequisite_missing",
      message: `${decision.name} applies to ${decision.profile_ids.join(", ")}, which the warband does not include.`,
      subject_ids: [decision.id, ...decision.profile_ids],
    };
  }
  const { count, sides } = decision.dice;
  if (!Number.isInteger(input.roll) || input.roll < count || input.roll > count * sides) {
    return {
      ok: false,
      reason: "invalid_input",
      message: `Enter a result from ${count} to ${count * sides}.`,
      subject_ids: [decision.id],
    };
  }
  if (recordedCreationDecision(document, decision.id)) {
    return {
      ok: false,
      reason: "conflict",
      message: `${decision.name} has already been rolled for this warband.`,
      subject_ids: [decision.id],
    };
  }
  const outcome = creationDecisionOutcomeFor(decision, input.roll);
  if (!outcome) {
    return {
      ok: false,
      reason: "invalid_input",
      message: `The printed table of ${decision.name} has no result for ${input.roll}.`,
      subject_ids: [decision.id],
    };
  }
  const recorded = document.campaign.special_rules.filter(
    (row) => row["kind"] === CREATION_DECISION_MARKER,
  ).length;
  const entry: OpenPayload = {
    kind: CREATION_DECISION_MARKER,
    decision_id: decision.id,
    rule_id: decision.rule_id,
    outcome_id: outcome.result_id,
    roll: input.roll,
    // Rolls are recorded in the order they happened, so a reload restores the
    // same sequence the table asked for.
    order: recorded + 1,
    text: outcome.result,
    texts: { en: outcome.result, ...outcome.result_i18n },
    source: decision.rule_id,
    expires_after_battles: null,
    consume_when_opponent_contains: [],
  };
  return {
    ok: true,
    state: withCampaign(document, {
      ...document.campaign,
      special_rules: [...document.campaign.special_rules, entry],
    }),
  };
}
