/**
 * T11: campaign obligations of the produced campaign contracts (T10).
 *
 * This module is the only place the interface turns a campaign verdict into
 * presentation. Two rules hold everywhere here:
 *
 * 1. **No rule is re-implemented.** Every fact comes from the T10 domain
 *    contract (creation decisions, lifecycle clauses, succession, mutations,
 *    Rout facts, withdrawals, market availability). The module reads published
 *    rows and phrases values; it never decides legality.
 * 2. **The stable code and its parameters are the identity.** A rejection
 *    carries `reason` plus `subject_ids`; the visible sentence is resolved by
 *    code with names looked up from the knowledge base, so no technical id is
 *    ever printed and the English diagnostic is never the only representation.
 *
 * Banned in this module: English diagnostics as visible text, ids as visible
 * text, and any copy of a construction or campaign rule.
 */

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { unavailableText, type TextField, type TextReference, type TextResolution } from "@adapters/knowledge-reader/presentation";
import type { KnowledgeKind } from "@domain/campaign/kernel/ports";
import type { AppError, CampaignDocument, IdString, OpenPayload } from "./types";
import { creationDecisionsOf, owedCreationDecisions, recordedCreationDecision, type CreationDecisionFacts } from "@domain/campaign/kernel/creation-decisions";
import { missingRequiredMembers } from "@domain/campaign/kernel/lifecycle";
import { marketAvailabilityIssueFor, type MarketIssueCode } from "@domain/campaign/kernel/market";
import { mutationCatalogue, mutationGrantRulesOf, mutationPrice, mutationsOf, type MutationGrantFacts } from "@domain/campaign/kernel/mutations";
import { routTestFactsFor } from "@domain/campaign/kernel/rout-test";
import { currentLeaderId, pendingSuccession, successionClausesOf } from "@domain/campaign/kernel/succession";
import { withdrawalLog } from "@domain/campaign/kernel/withdrawal";
import { knowledgeName, persistedSystemText } from "./displayText";
import { translate, type Locale, type UiText } from "./i18n-core";
import { warriorPersonalName, type FormattedText, type PresentationValue } from "./presentation-values";

/** Stable rejection reasons the interface knows how to phrase. */
export type CampaignIssueCode =
  | "prerequisite_missing"
  | "not_found"
  | "invalid_input"
  | "conflict"
  | "limit_reached"
  | "limit_violated"
  | "not_available"
  | "not_permitted_in_draft"
  | "not_permitted_when_committed"
  | "lifecycle_member_required"
  | "market_creation_only"
  /** T09/T10 advance contract: a `special` list still published as prose. */
  | "skill_pending_special_list"
  | MarketIssueCode;

const CAMPAIGN_ISSUE_CODES: readonly string[] = [
  "prerequisite_missing",
  "not_found",
  "invalid_input",
  "conflict",
  "limit_reached",
  "limit_violated",
  "not_available",
  "not_permitted_in_draft",
  "not_permitted_when_committed",
  "lifecycle_member_required",
  "skill_pending_special_list",
  "market_not_listed",
  "market_not_common",
  "market_warband_only",
  "market_warband_forbidden",
  "market_creation_only",
  "market_condition_unstructured",
];

/**
 * Structured identity of a rejected campaign action: the stable code and the
 * parameters the domain identified. `code === null` means the rejection came
 * from a path that publishes no code (legacy prose), and the caller falls back
 * to the sentence catalogue.
 */
export interface CampaignIssueSignal {
  readonly code: CampaignIssueCode | null;
  readonly subjectIds: readonly IdString[];
}

/** Read the stable code and parameters of a rejection, without parsing prose. */
export function campaignIssueSignal(error: AppError): CampaignIssueSignal {
  const detail = (error.detail ?? {}) as Readonly<Record<string, unknown>>;
  const reason = detail["reason"];
  const identifiers = detail["subject_ids"];
  return {
    code: typeof reason === "string" && CAMPAIGN_ISSUE_CODES.includes(reason) ? (reason as CampaignIssueCode) : null,
    subjectIds: Array.isArray(identifiers) ? identifiers.map(String) : [],
  };
}

/**
 * A campaign-catalogue row publishes its own translated name fields. English
 * may read the canonical field (which is the English text by contract); any
 * other locale without its own translation is a missing datum, never an
 * English leak.
 */
function catalogueName(locale: Locale, name: unknown, nameI18n: unknown): PresentationValue {
  const translations = nameI18n && typeof nameI18n === "object" ? (nameI18n as Readonly<Record<string, unknown>>) : {};
  const localized = translations[locale];
  if (typeof localized === "string" && localized.trim()) return localized as FormattedText;
  if (locale === "en" && typeof name === "string" && name.trim()) return name as FormattedText;
  return unavailableText(locale);
}

/** Published text of a recorded campaign entry, in the active language only. */
function recordedText(locale: Locale, text: unknown, texts: unknown): PresentationValue {
  const translations = texts && typeof texts === "object" ? (texts as Readonly<Record<string, unknown>>) : {};
  const localized = translations[locale];
  return typeof localized === "string" && localized.trim() ? (localized as FormattedText) : persistedSystemText(text, undefined, locale);
}

/**
 * Name of a member recorded in the campaign log. The member is already gone, so
 * the sanctioned `warriorPersonalName` adapter has no row to read: the persisted
 * audit entry is the only source. A field-specific adapter for that record (the
 * shape of `manualCorrectionReason`) is a T12 presentation item.
 */
function recordedMemberName(locale: Locale, value: unknown): PresentationValue {
  return typeof value === "string" && value.trim() ? (value as FormattedText) : unavailableText(locale);
}

/**
 * The presentation boundary accepts any loaded document. A partially built one
 * (a stub session, a fixture without a roster) is normalised so the campaign
 * facts return nothing instead of throwing: the lists become empty, the identity
 * carries no band, and the moment counts as a composition — a document with no
 * configuration is not a committed warband, so no obligation is invented for it.
 */
function armedDocument(document: CampaignDocument): CampaignDocument {
  const campaign = document?.campaign;
  if (
    campaign?.configuration &&
    campaign?.identity &&
    [campaign.warriors, campaign.special_rules, campaign.inventory, campaign.manual_log, campaign.post_battles, campaign.battles].every((rows) => Array.isArray(rows))
  ) return document;
  const list = <T>(rows: readonly T[] | undefined): readonly T[] => (Array.isArray(rows) ? rows : []);
  return {
    ...document,
    campaign: {
      ...(campaign ?? {}),
      identity: campaign?.identity ?? ({ band_id: "" } as CampaignDocument["campaign"]["identity"]),
      configuration: campaign?.configuration ?? ({ is_draft: true } as CampaignDocument["campaign"]["configuration"]),
      warriors: list(campaign?.warriors),
      special_rules: list(campaign?.special_rules),
      inventory: list(campaign?.inventory),
      manual_log: list(campaign?.manual_log),
      post_battles: list(campaign?.post_battles),
      battles: list(campaign?.battles),
    },
  } as CampaignDocument;
}

/** Name resolvers the issue catalogue uses, all of them resolved from the KB. */
export interface ObligationNames {
  /** `null` when no published creation decision carries that id. */
  readonly decisionName: (id: string) => PresentationValue | null;
  /** `null` when no published lifecycle or succession clause carries that id. */
  readonly clauseName: (id: string) => PresentationValue | null;
  readonly ruleName: (id: string) => PresentationValue;
  readonly profileName: (id: string) => PresentationValue;
  readonly itemName: (id: string) => PresentationValue;
}

/**
 * Name resolvers for one campaign. Everything is resolved from published rows:
 * a row without a translation in the active language resolves to the shared
 * unavailable message, never to an id.
 */
export function obligationNamesOf(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): ObligationNames {
  const doc = armedDocument(document);
  const bandId = doc.campaign.identity.band_id;
  const decisions = creationDecisionsOf(reader, bandId);
  const clauses = [...missingRequiredMembers(doc, reader), ...successionClausesOf(reader, bandId)];
  return {
    decisionName: (id) => {
      const decision = decisions.find((row) => row.id === id);
      return decision ? catalogueName(locale, decision.name, decision.name_i18n) : null;
    },
    clauseName: (id) => {
      const clause = clauses.find((row) => row.id === id);
      return clause ? catalogueName(locale, clause.name, clause.name_i18n) : null;
    },
    ruleName: (id) => knowledgeName(reader, "rule", id, locale),
    profileName: (id) => knowledgeName(reader, "profile", id, locale, undefined, bandId),
    itemName: (id) => knowledgeName(reader, "item", id, locale),
  };
}

export interface CampaignIssueText {
  readonly text: UiText;
  /** `alert` for a rejection, `status` for a pending obligation or missing datum. */
  readonly severity: "alert" | "status";
}

/**
 * Phrase one rejection: the code decides the sentence, the parameters supply
 * the names, and an unknown code returns `null` so the caller keeps its own
 * fallback instead of printing the raw diagnostic.
 */
export function campaignIssueText(signal: CampaignIssueSignal, names: ObligationNames, locale: Locale): CampaignIssueText | null {
  const [first, second] = signal.subjectIds;
  const item = () => names.itemName(first ?? "");
  switch (signal.code) {
    case "market_not_common":
      return { text: translate({ key: "campaign.market.not-common", args: { item: item() } }, locale), severity: "alert" };
    case "market_not_listed":
      return { text: translate({ key: "campaign.market.not-listed", args: { item: item() } }, locale), severity: "alert" };
    case "market_warband_only":
      return { text: translate({ key: "campaign.market.warband-only", args: { item: item() } }, locale), severity: "alert" };
    case "market_warband_forbidden":
      return { text: translate({ key: "campaign.market.warband-forbidden", args: { item: item() } }, locale), severity: "alert" };
    case "market_creation_only":
      return { text: translate({ key: "campaign.market.creation-only", args: { item: item() } }, locale), severity: "alert" };
    case "market_condition_unstructured":
      return { text: translate({ key: "campaign.market.condition-unstructured", args: { item: item() } }, locale), severity: "status" };
    case "prerequisite_missing": {
      // The parameters identify what is missing: a printed creation roll, a
      // mandatory roster member, or a published successor profile.
      const decision = first ? names.decisionName(first) : null;
      if (decision) return { text: translate({ key: "campaign.decision.required", args: { name: decision } }, locale), severity: "status" };
      const clause = first ? names.clauseName(first) : null;
      if (clause) {
        return {
          text: translate({ key: "campaign.lifecycle.required", args: { clause, profile: names.profileName(second ?? first) } }, locale),
          severity: "status",
        };
      }
      if (first) return { text: translate({ key: "campaign.succession.no-candidate", args: { name: names.profileName(first) } }, locale), severity: "status" };
      return { text: translate({ key: "campaign.error-prerequisite" }, locale), severity: "status" };
    }
    case "not_found":
      return { text: translate({ key: "campaign.error-not-found" }, locale), severity: "alert" };
    case "invalid_input":
      return { text: translate({ key: "campaign.error-invalid" }, locale), severity: "alert" };
    case "conflict":
      return { text: translate({ key: "campaign.error-conflict" }, locale), severity: "alert" };
    case "limit_reached":
      return { text: translate({ key: "campaign.error-limit" }, locale), severity: "alert" };
    case "limit_violated":
      return { text: translate({ key: "campaign.error-unmet" }, locale), severity: "alert" };
    case "not_available":
      return { text: translate({ key: "campaign.error-unavailable" }, locale), severity: "alert" };
    case "not_permitted_in_draft":
      return { text: translate({ key: "campaign.error-draft-only" }, locale), severity: "alert" };
    case "not_permitted_when_committed":
      return { text: translate({ key: "campaign.error-recruiting-only" }, locale), severity: "alert" };
    case "lifecycle_member_required":
      // The parameters are the clause and the printed profile it requires, so
      // the sentence names what the roster still owes instead of a row id.
      return {
        text: translate({
          key: "campaign.lifecycle.required",
          args: { clause: names.clauseName(first ?? "") ?? unavailableText(locale), profile: names.profileName(second ?? "") },
        }, locale),
        severity: "status",
      };
    case "skill_pending_special_list":
      // The advance refused the choice because the KB publishes no members for
      // the band special-skill list. The cause is the missing datum, not the
      // user's input, so it is a pending fact and not an error; the parameters
      // (band, profile, skill) are ids and stay unpublished.
      return { text: translate({ key: "campaign.advance.pending-special-list" }, locale), severity: "status" };
    default:
      return null;
  }
}

/** Phrased rejection for one error, or `null` when the code is unknown. */
export function campaignErrorText(error: AppError, document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): CampaignIssueText | null {
  return campaignIssueText(campaignIssueSignal(error), obligationNamesOf(document, reader, locale), locale);
}

// ---------------------------------------------------------------------------
// Creation decisions
// ---------------------------------------------------------------------------

export interface PendingDecisionFacts {
  readonly id: IdString;
  readonly name: PresentationValue;
  readonly ruleId: IdString;
  readonly dice: { readonly count: number; readonly sides: number };
}

/** Creation rolls the warband still owes, in published order. */
export function pendingDecisionFacts(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): readonly PendingDecisionFacts[] {
  return owedCreationDecisions(armedDocument(document), reader).map((decision: CreationDecisionFacts) => ({
    id: decision.id,
    name: catalogueName(locale, decision.name, decision.name_i18n),
    ruleId: decision.rule_id,
    dice: decision.dice,
  }));
}

export interface RecordedDecisionFacts {
  readonly id: IdString;
  readonly name: PresentationValue;
  readonly order: number;
  readonly roll: number;
  readonly outcome: PresentationValue;
}

/** Recorded creation rolls, oldest first: the order the table asked for. */
export function recordedDecisionFacts(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): readonly RecordedDecisionFacts[] {
  const doc = armedDocument(document);
  return creationDecisionsOf(reader, doc.campaign.identity.band_id)
    .flatMap((decision: CreationDecisionFacts) => {
      const recorded = recordedCreationDecision(doc, decision.id);
      if (!recorded) return [];
      return [{
        id: decision.id,
        name: catalogueName(locale, decision.name, decision.name_i18n),
        order: Number(recorded["order"] ?? 0),
        roll: Number(recorded["roll"] ?? 0),
        outcome: recordedText(locale, recorded["text"], recorded["texts"]),
      }];
    })
    .sort((left, right) => left.order - right.order);
}

// ---------------------------------------------------------------------------
// Roster lifecycle
// ---------------------------------------------------------------------------

export interface RequiredMemberFacts {
  readonly clauseId: IdString;
  readonly clauseName: PresentationValue;
  readonly ruleId: IdString;
  readonly profiles: readonly { readonly id: IdString; readonly name: PresentationValue }[];
}

/** Printed members the roster still owes before any other recruit is legal. */
export function requiredMemberFacts(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): readonly RequiredMemberFacts[] {
  const doc = armedDocument(document);
  return missingRequiredMembers(doc, reader).map((clause) => ({
    clauseId: clause.id,
    clauseName: catalogueName(locale, clause.name, clause.name_i18n),
    ruleId: clause.rule_id,
    profiles: clause.profile_ids.map((id) => ({ id, name: knowledgeName(reader, "profile", id, locale, undefined, doc.campaign.identity.band_id) })),
  }));
}

// ---------------------------------------------------------------------------
// Leader succession
// ---------------------------------------------------------------------------

export interface LeaderFacts {
  readonly leader: { readonly warriorId: IdString; readonly name: PresentationValue } | null;
  readonly pending: {
    readonly clauseId: IdString;
    readonly clauseName: PresentationValue;
    readonly ruleId: IdString;
    readonly candidates: readonly { readonly id: IdString; readonly name: PresentationValue }[];
  } | null;
  /** True when the source does not publish a tie-break or the no-candidate consequence. */
  readonly sourceLimit: boolean;
}

/** Who leads now, and the succession the warband still owes. */
export function leaderFacts(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): LeaderFacts {
  const doc = armedDocument(document);
  const leaderId = currentLeaderId(doc, reader);
  if (leaderId) {
    const leader = doc.campaign.warriors.find((row) => row.id === leaderId);
    return { leader: { warriorId: leaderId, name: warriorPersonalName(leader, locale) }, pending: null, sourceLimit: false };
  }
  const pending = pendingSuccession(doc, reader);
  if (!pending) return { leader: null, pending: null, sourceLimit: false };
  const candidates = doc.campaign.warriors
    .filter((row) => pending.clause.successor_profile_ids.includes(String(row.profile_id ?? "")))
    .map((row) => ({ id: row.id, name: warriorPersonalName(row, locale) }));
  return {
    leader: null,
    pending: {
      clauseId: pending.clause.id,
      clauseName: catalogueName(locale, pending.clause.name, pending.clause.name_i18n),
      ruleId: pending.clause.rule_id,
      candidates,
    },
    sourceLimit: candidates.length !== 1,
  };
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export interface MutationOfferFacts {
  readonly id: IdString;
  readonly name: PresentationValue;
  /** Listed price for this warrior (double from the second purchase). */
  readonly price: number | null;
  readonly owned: boolean;
}

export interface WarriorMutationFacts {
  readonly warriorId: IdString;
  readonly ruleName: PresentationValue;
  readonly ruleId: IdString;
  readonly recipients: MutationGrantFacts["recipients"];
  readonly limitPerWarrior: number | null;
  readonly purchased: number;
  readonly offers: readonly MutationOfferFacts[];
  /** Printed mutations the catalogue does not price; a missing datum, never an option. */
  readonly unpricedCount: number;
}

/** Mutations one recruiting member may buy: catalogue rows with a published price. */
export function mutationFactsFor(document: CampaignDocument, reader: ArtefactKnowledgeReader, warriorId: IdString, locale: Locale): WarriorMutationFacts | null {
  const doc = armedDocument(document);
  const rule = mutationGrantRulesOf(reader, doc.campaign.identity.band_id)[0];
  if (!rule) return null;
  const catalogue = mutationCatalogue(reader);
  const purchased = mutationsOf(doc, warriorId);
  const offers = rule.mutation_ids.flatMap((id) => {
    const mutation = catalogue.find((row) => row.id === id);
    if (!mutation) return [];
    return [{
      id,
      name: catalogueName(locale, mutation.name, mutation.name_i18n),
      price: mutationPrice(reader, id, purchased.length),
      owned: purchased.includes(id),
    }];
  });
  return {
    warriorId,
    ruleName: catalogueName(locale, rule.name, rule.name_i18n),
    ruleId: rule.rule_id,
    recipients: rule.recipients,
    limitPerWarrior: rule.limit_per_warrior,
    purchased: purchased.length,
    offers,
    unpricedCount: rule.unrouted_mutation_names.length,
  };
}

/** Whether the campaign is at a moment where a mutation may still be bought. */
export function mutationPurchaseWindow(document: CampaignDocument): boolean {
  const doc = armedDocument(document);
  return doc.campaign.configuration?.is_draft === true || doc.campaign.post_battles.some((row) => !row.complete);
}

// ---------------------------------------------------------------------------
// Rout facts
// ---------------------------------------------------------------------------

export interface RoutMemberFacts {
  readonly warriorId: IdString;
  readonly name: PresentationValue;
  /** Published profile of the row; the exemption is a profile-level rule. */
  readonly profileName: PresentationValue | null;
  readonly quantity: number;
  readonly countedModels: number;
  readonly exempt: boolean;
}

export interface RoutPresentation {
  readonly battleNumber: number;
  readonly models: number;
  readonly countedModels: number;
  readonly exemptOutOfActionModels: number;
  readonly members: readonly RoutMemberFacts[];
}

/** The roster facts the Rout test reads, recomputed by the domain. */
export function routPresentationFor(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale, battleNumber: number): RoutPresentation | null {
  const doc = armedDocument(document);
  const facts = routTestFactsFor(doc, reader, battleNumber);
  if (!facts) return null;
  return {
    battleNumber: facts.battle_number,
    models: facts.models,
    countedModels: facts.counted_models,
    exemptOutOfActionModels: facts.exempt_out_of_action_models,
    members: facts.members.map((member) => ({
      warriorId: member.warrior_id,
      name: warriorPersonalName(doc.campaign.warriors.find((row) => row.id === member.warrior_id), locale),
      profileName: member.profile_id
        ? knowledgeName(reader, "profile", member.profile_id, locale, undefined, doc.campaign.identity.band_id)
        : null,
      quantity: member.quantity,
      countedModels: member.counted_models,
      exempt: member.exempt,
    })),
  };
}

// ---------------------------------------------------------------------------
// Withdrawals that came from the battle (T13's trigger, T10's consequence)
// ---------------------------------------------------------------------------

export interface WithdrawalAuditFacts {
  readonly order: number;
  readonly battleNumber: number | null;
  readonly members: readonly { readonly name: PresentationValue; readonly quantity: number }[];
}

/** Audit trail of the members a withdrawal removed, oldest first. */
export function withdrawalAuditFacts(document: CampaignDocument, locale: Locale): readonly WithdrawalAuditFacts[] {
  return withdrawalLog(armedDocument(document)).map((entry) => ({
    order: Number(entry["order"] ?? 0),
    battleNumber: typeof entry["battle_number"] === "number" ? entry["battle_number"] : null,
    members: (Array.isArray(entry["members"]) ? (entry["members"] as OpenPayload[]) : []).map((member) => ({
      name: recordedMemberName(locale, member["name"]),
      quantity: Number(member["quantity"] ?? 1),
    })),
  }));
}

// ---------------------------------------------------------------------------
// Unique finds (canonical id plus the id older campaigns persisted)
// ---------------------------------------------------------------------------

function magicalArtefactRows(reader: ArtefactKnowledgeReader): readonly OpenPayload[] {
  const section = reader.campaignSection("exploration-and-income");
  const table = (section["magical_artefacts"] ?? {}) as OpenPayload;
  return Array.isArray(table["results"]) ? (table["results"] as OpenPayload[]) : [];
}

/**
 * Canonical item id of a unique find, accepting the id older campaigns saved
 * (`magical_artefact.<row>`) so both spellings resolve to one object.
 */
export function canonicalUniqueItemId(reader: ArtefactKnowledgeReader, id: string): string | null {
  for (const row of magicalArtefactRows(reader)) {
    const canonical = String(row["item_id"] ?? "").trim();
    if (!canonical) continue;
    const legacy = `magical_artefact.${String(row["id"] ?? "").replace("campaign.magical-artefact.", "")}`;
    if (id === canonical || id === legacy) return canonical;
  }
  return null;
}

export interface UniqueFindFacts {
  readonly id: IdString;
  readonly name: PresentationValue;
  readonly owned: number;
  readonly stash: number;
  /** True when a campaign saved under the row-derived id is being presented. */
  readonly legacyOnly: boolean;
}

/**
 * Unique finds held by the warband, merged by canonical id: a campaign that
 * stored the legacy id and one that stored the canonical id describe the same
 * object and never appear twice.
 */
export function uniqueFindFacts(document: CampaignDocument, reader: ArtefactKnowledgeReader, locale: Locale): readonly UniqueFindFacts[] {
  const merged = new Map<string, { owned: number; stash: number; legacyOnly: boolean }>();
  for (const row of armedDocument(document).campaign.inventory) {
    const canonical = canonicalUniqueItemId(reader, row.id);
    if (!canonical) continue;
    const current = merged.get(canonical) ?? { owned: 0, stash: 0, legacyOnly: true };
    merged.set(canonical, {
      owned: current.owned + row.owned,
      stash: current.stash + row.stash,
      legacyOnly: current.legacyOnly && canonical !== row.id,
    });
  }
  return [...merged].map(([id, totals]) => ({
    id,
    name: knowledgeName(reader, "item", id, locale),
    owned: totals.owned,
    stash: totals.stash,
    legacyOnly: totals.legacyOnly,
  }));
}

// ---------------------------------------------------------------------------
// Market availability
// ---------------------------------------------------------------------------

export interface MarketAvailabilityFacts {
  readonly available: boolean;
  readonly text: UiText | null;
}

/**
 * Structural reader the market verdict needs: the trading panel lists offers
 * through `KnowledgeListings`, which is not a full `KnowledgeReader`.
 */
export interface MarketReader {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
  list?(kind: KnowledgeKind): readonly Readonly<Record<string, unknown>>[];
  resolveKbText?(ref: TextReference, field: TextField, locale: Locale): TextResolution;
}

/**
 * Availability of one Trading Post offer for the loaded warband. The verdict
 * comes from the T10 domain contract; the interface only phrases it, and the
 * service remains the authority when the purchase is attempted.
 */
export function marketAvailabilityFacts(document: CampaignDocument, reader: MarketReader, itemId: IdString, locale: Locale): MarketAvailabilityFacts {
  const doc = armedDocument(document);
  const bandId = doc.campaign.identity.band_id;
  const items = ((reader.campaignSection?.("trading-post") ?? {})["items"] ?? []) as readonly OpenPayload[];
  const offer = Array.isArray(items) ? items.find((row) => row["item_id"] === itemId) : undefined;
  // Only the item name is needed to phrase a market verdict; the other
  // resolvers stay empty so no unpublished row is consulted by accident.
  const names: ObligationNames = {
    decisionName: () => null,
    clauseName: () => null,
    ruleName: (id) => knowledgeName(reader, "rule", id, locale),
    profileName: (id) => knowledgeName(reader, "profile", id, locale, undefined, bandId),
    itemName: (id) => knowledgeName(reader, "item", id, locale),
  };
  const phrase = (code: MarketIssueCode): UiText | null => campaignIssueText({ code, subjectIds: [itemId] }, names, locale)?.text ?? null;
  if (!offer) return { available: false, text: phrase("market_not_listed") };
  const groups = (reader.list?.("warband_group") ?? [])
    .filter((row) => Array.isArray(row["band_ids"]) && (row["band_ids"] as unknown[]).map(String).includes(bandId))
    .map((row) => String(row["id"] ?? ""));
  const issue = marketAvailabilityIssueFor({
    offer,
    band_id: bandId,
    groups,
    item_name: String(names.itemName(itemId)),
    // A printed "creation only" clause is decided by the moment the warband is
    // in, which the interface reads from the document it was handed.
    at_creation: doc.campaign.configuration?.is_draft === true,
  });
  return issue ? { available: false, text: phrase(issue.code) } : { available: true, text: null };
}
