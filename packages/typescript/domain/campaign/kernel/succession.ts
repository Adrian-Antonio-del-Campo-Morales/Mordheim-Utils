/**
 * T10: leader succession.
 *
 * Printed band rules hand the warband to a named successor when its leader is
 * lost — the Cathayan Pirates ("Succession"): "If the Disgraced Warlord is
 * killed, one of the Shanghai'ers will take over in the same manner as a
 * Champion taking over for a Mercenary warband."
 *
 * The KB publishes the two ids that clause needs — the leader profile (the one
 * that carries the band's printed `--leader` rule) and the eligible successor
 * profiles — in `campaign.recruitment-and-veterans.succession_clauses`. The
 * module never infers leadership from a translated name and holds no band table
 * in TypeScript.
 *
 * `currentLeaderId` reads the published leader profile first (the original
 * leader) and then the latest recorded succession whose successor is still in
 * the roster, so a reopen reconstructs who leads without a second write.
 *
 * Not published by the available sources: the core-book tie-break / "no
 * candidate" consequence behind "the same manner as a Champion taking over".
 * The mechanism is therefore closed at the published boundary: several
 * candidates ask the caller to choose, and no candidate leaves the succession
 * owed with a typed rejection instead of inventing a rule.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignDocument, IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import type { UseCaseResult } from "../index";
import { withCampaign } from "./document";

/** Stable marker of a recorded succession inside `campaign.special_rules`. */
export const SUCCESSION_MARKER = "leader_succession";

/** Reader that can also reach the published campaign catalogues. */
export type SuccessionReader = KnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

export interface SuccessionClauseFacts {
  readonly id: IdString;
  readonly band_id: IdString;
  readonly rule_id: IdString;
  /** Profiles whose roster member is the band's leader. */
  readonly leader_profile_ids: readonly IdString[];
  /** Profiles the printed rule allows to take over. */
  readonly successor_profile_ids: readonly IdString[];
  readonly name: string;
  readonly name_i18n: Readonly<Record<string, string>>;
  readonly effect: string;
}

function names(value: unknown): Readonly<Record<string, string>> {
  if (!value || typeof value !== "object") return {};
  const out: Record<string, string> = {};
  for (const [key, text] of Object.entries(value as OpenPayload)) {
    if (typeof text === "string" && text.trim()) out[key] = text;
  }
  return out;
}

function identifiers(value: unknown): readonly IdString[] {
  return Array.isArray(value) ? value.map(String).filter((id) => id.length > 0) : [];
}

/** Every succession clause the artefact publishes for a band, in catalogue order. */
export function successionClausesOf(
  reader: SuccessionReader,
  bandId: IdString,
): readonly SuccessionClauseFacts[] {
  const rows = reader.campaignSection?.("recruitment-and-veterans")?.["succession_clauses"];
  if (!Array.isArray(rows) || !bandId) return [];
  return rows.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];
    const row = entry as OpenPayload;
    const id = String(row["id"] ?? "");
    if (!id || String(row["band_id"] ?? "") !== bandId) return [];
    return [{
      id,
      band_id: String(row["band_id"] ?? ""),
      rule_id: String(row["rule_id"] ?? ""),
      leader_profile_ids: identifiers(row["leader_profile_ids"]),
      successor_profile_ids: identifiers(row["successor_profile_ids"]),
      name: String(row["name"] ?? id),
      name_i18n: names(row["name_i18n"]),
      effect: String(row["effect"] ?? ""),
    }];
  });
}

/** Recorded successions of this campaign, oldest first. */
export function successionLog(document: CampaignDocument): readonly OpenPayload[] {
  return document.campaign.special_rules.filter((row) => row["kind"] === SUCCESSION_MARKER);
}

/** Roster members whose profile the clause publishes as a leader. */
export function leadersFor(document: CampaignDocument, clause: SuccessionClauseFacts): readonly IdString[] {
  return document.campaign.warriors
    .filter((warrior) => warrior.profile_id !== undefined && clause.leader_profile_ids.includes(warrior.profile_id))
    .map((warrior) => warrior.id);
}

/** Roster members the clause publishes as eligible successors. */
export function successorsFor(document: CampaignDocument, clause: SuccessionClauseFacts): readonly IdString[] {
  return document.campaign.warriors
    .filter((warrior) => warrior.profile_id !== undefined && clause.successor_profile_ids.includes(warrior.profile_id))
    .map((warrior) => warrior.id);
}

/**
 * Warrior id of the current leader, or `null` when the warband has none.
 * The published leader profile wins; a recorded successor stands in once the
 * original leader is gone.
 */
export function currentLeaderId(
  document: CampaignDocument,
  reader: SuccessionReader,
): IdString | null {
  const clauses = successionClausesOf(reader, document.campaign.identity.band_id);
  const roster = new Set(document.campaign.warriors.map((warrior) => warrior.id));
  for (const clause of clauses) {
    const seated = leadersFor(document, clause).find((id) => roster.has(id));
    if (seated) return seated;
  }
  const recorded = successionLog(document);
  for (let index = recorded.length - 1; index >= 0; index -= 1) {
    const successor = String(recorded[index]?.["successor_id"] ?? "");
    if (successor && roster.has(successor)) return successor;
  }
  return null;
}

export interface PendingSuccession {
  readonly clause: SuccessionClauseFacts;
  readonly candidates: readonly IdString[];
}

/**
 * The succession the warband still owes: the printed clause fires while no
 * leader is seated and returns the successor rows the caller can choose among.
 */
export function pendingSuccession(
  document: CampaignDocument,
  reader: SuccessionReader,
): PendingSuccession | null {
  if (currentLeaderId(document, reader) !== null) return null;
  for (const clause of successionClausesOf(reader, document.campaign.identity.band_id)) {
    if (clause.leader_profile_ids.length === 0 && clause.successor_profile_ids.length === 0) continue;
    return { clause, candidates: successorsFor(document, clause) };
  }
  return null;
}

/**
 * Seat a successor after the leader was lost. The caller names the successor;
 * with exactly one eligible candidate the choice is unambiguous and may be
 * omitted. The event reaches `campaign.special_rules` under the stable
 * `leader_succession` marker.
 */
export function succeedLeader(
  document: CampaignDocument,
  reader: SuccessionReader,
  input: { readonly clause_id: IdString; readonly successor_warrior_id?: IdString },
): UseCaseResult {
  const clause = successionClausesOf(reader, document.campaign.identity.band_id).find((row) => row.id === input.clause_id);
  if (!clause) {
    return { ok: false, reason: "not_found", message: `Unknown succession clause "${input.clause_id}" for ${document.campaign.identity.band_id || "an empty identity"}.`, subject_ids: [input.clause_id] };
  }
  const leader = currentLeaderId(document, reader);
  if (leader !== null) {
    return { ok: false, reason: "conflict", message: `${clause.name} only applies once the leader is gone; ${leader} still leads the warband.`, subject_ids: [leader] };
  }
  const candidates = successorsFor(document, clause);
  if (candidates.length === 0) {
    return { ok: false, reason: "prerequisite_missing", message: `No eligible successor (${clause.successor_profile_ids.join(", ") || "none published"}) is in the warband.`, subject_ids: [...clause.successor_profile_ids] };
  }
  const requested = String(input.successor_warrior_id ?? "").trim();
  let successor = "";
  if (requested) {
    if (!candidates.includes(requested)) {
      return { ok: false, reason: "not_found", message: `${requested} cannot succeed under ${clause.name}.`, subject_ids: [requested, ...candidates] };
    }
    successor = requested;
  } else if (candidates.length === 1) {
    successor = candidates[0];
  } else {
    return { ok: false, reason: "invalid_input", message: `Choose which successor takes over: ${candidates.join(", ")}.`, subject_ids: [...candidates] };
  }
  const warrior = document.campaign.warriors.find((row) => row.id === successor);
  const order = successionLog(document).length + 1;
  const text = `${warrior?.name ?? successor} takes over the warband (${clause.name}).`;
  const entry: OpenPayload = {
    kind: SUCCESSION_MARKER,
    clause_id: clause.id,
    rule_id: clause.rule_id,
    successor_id: successor,
    order,
    text,
    texts: { en: text },
    source: clause.rule_id,
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
