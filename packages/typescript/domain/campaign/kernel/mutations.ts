/**
 * T10: campaign mutations.
 *
 * The canonical catalogue lives in `campaign.mutations` and already publishes
 * the purchase rules ("only when they are recruited"; the first mutation at
 * list price, the second and later at double price). Printed band rules that
 * grant a mutation list their selectable ids in
 * `campaign.mutations.grant_rules`, so this module never reads the rule prose.
 *
 * A mutation's *battle* effect stays with T13; what the campaign owns is the
 * acquisition, the cost and the persisted state. Only catalogue ids carry a
 * published cost — the "Corrupted Characters" ids the band rules name but the
 * KB does not publish are refused here (`not_found`) and enumerated in the
 * task's blocked list.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignDocument, IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import type { UseCaseResult } from "../index";
import { currentState, treasury, withCampaign } from "./document";

/** Stable marker of a bought mutation inside `campaign.special_rules`. */
export const MUTATION_MARKER = "mutation";

/** Reader that can also reach the published campaign catalogues. */
export type MutationReader = KnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

export interface MutationFacts {
  readonly id: IdString;
  readonly name: string;
  readonly name_i18n: Readonly<Record<string, string>>;
  /** Listed price in gold crowns, when the catalogue publishes one. */
  readonly cost_gc: number | null;
  readonly effect: string;
}

export interface MutationGrantFacts {
  readonly id: IdString;
  readonly band_id: IdString;
  readonly rule_id: IdString;
  /** `hero` restricts the grant to Heroes; `any` leaves it open. */
  readonly recipients: "hero" | "any";
  /** Recipient profiles, empty when the printed rule names no profile. */
  readonly profile_ids: readonly IdString[];
  /** Mutation ids the printed rule lists (already intersected with the catalogue). */
  readonly mutation_ids: readonly IdString[];
  /** Printed ids the rule names but the catalogue does not publish. */
  readonly unrouted_mutation_names: readonly string[];
  readonly limit_per_warrior: number | null;
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

function rows(reader: MutationReader, key: string): readonly OpenPayload[] {
  const value = reader.campaignSection?.("mutations")?.[key];
  return Array.isArray(value) ? (value as OpenPayload[]).filter((row) => row && typeof row === "object") : [];
}

/** The canonical mutation catalogue keyed by stable id. */
export function mutationCatalogue(reader: MutationReader): readonly MutationFacts[] {
  return rows(reader, "mutations").flatMap((row) => {
    const id = String(row["id"] ?? "");
    if (!id) return [];
    const cost = Number(row["cost_gc"]);
    return [{
      id,
      name: String(row["name"] ?? id),
      name_i18n: names(row["name_i18n"]),
      cost_gc: Number.isFinite(cost) ? cost : null,
      effect: String(row["effect"] ?? ""),
    }];
  });
}

/** Printed grant rules the artefact publishes for a band. */
export function mutationGrantRulesOf(reader: MutationReader, bandId: IdString): readonly MutationGrantFacts[] {
  if (!bandId) return [];
  return rows(reader, "grant_rules").flatMap((row) => {
    const id = String(row["id"] ?? "");
    if (!id || String(row["band_id"] ?? "") !== bandId) return [];
    const recipients = row["recipients"] === "hero" ? "hero" : "any";
    const limit = Number(row["limit_per_warrior"]);
    return [{
      id,
      band_id: String(row["band_id"] ?? ""),
      rule_id: String(row["rule_id"] ?? ""),
      recipients,
      profile_ids: identifiers(row["profile_ids"]),
      mutation_ids: identifiers(row["mutation_ids"]),
      unrouted_mutation_names: Array.isArray(row["unrouted_mutation_names"]) ? row["unrouted_mutation_names"].map(String) : [],
      limit_per_warrior: Number.isInteger(limit) && limit >= 0 ? limit : null,
      name: String(row["name"] ?? id),
      name_i18n: names(row["name_i18n"]),
      effect: String(row["effect"] ?? ""),
    }];
  });
}

/** Mutations a warband may buy, with their listed price. */
export function availableMutations(reader: MutationReader, bandId: IdString): readonly MutationFacts[] {
  const catalogue = new Map(mutationCatalogue(reader).map((mutation) => [mutation.id, mutation]));
  const available = new Map<IdString, MutationFacts>();
  for (const rule of mutationGrantRulesOf(reader, bandId)) {
    for (const id of rule.mutation_ids) {
      const mutation = catalogue.get(id);
      if (mutation) available.set(id, mutation);
    }
  }
  return [...available.values()];
}

/** Mutations a warrior already owns, in purchase order. */
export function mutationsOf(document: CampaignDocument, warriorId: IdString): readonly IdString[] {
  return document.campaign.special_rules
    .filter((row) => row["kind"] === MUTATION_MARKER && row["warrior_id"] === warriorId)
    .map((row) => String(row["mutation_id"] ?? ""))
    .filter((id) => id.length > 0);
}

/**
 * The published purchase policy, as the catalogue states it
 * (`campaign.mutations.rules.purchase.pricing`): the multiplier of the first
 * mutation and of the second and later ones. The vocabulary is closed: a policy
 * value the application does not know is refused explicitly instead of being
 * replaced by a hardcoded price rule.
 */
export const MUTATION_PRICE_MULTIPLIERS: Readonly<Record<string, number>> = {
  listed_price: 1,
  double_listed_price: 2,
};

export type MutationPricingPolicy =
  | { readonly ok: true; readonly first: number; readonly second_and_subsequent: number }
  | { readonly ok: false; readonly first: string; readonly second_and_subsequent: string };

/** The published pricing policy of the catalogue, or an explicit unknown one. */
export function mutationPricingPolicy(reader: MutationReader): MutationPricingPolicy {
  const purchase = reader.campaignSection?.("mutations")?.["rules"];
  const rules = purchase && typeof purchase === "object" ? (purchase as OpenPayload) : {};
  const purchaseRules =
    rules["purchase"] && typeof rules["purchase"] === "object" ? (rules["purchase"] as OpenPayload) : {};
  const pricing =
    purchaseRules["pricing"] && typeof purchaseRules["pricing"] === "object"
      ? (purchaseRules["pricing"] as OpenPayload)
      : {};
  const first = String(pricing["first_mutation"] ?? "");
  const later = String(pricing["second_and_subsequent"] ?? "");
  const firstMultiplier = MUTATION_PRICE_MULTIPLIERS[first];
  const laterMultiplier = MUTATION_PRICE_MULTIPLIERS[later];
  if (firstMultiplier === undefined || laterMultiplier === undefined) {
    return { ok: false, first, second_and_subsequent: later };
  }
  return { ok: true, first: firstMultiplier, second_and_subsequent: laterMultiplier };
}

/** Printed price multiplier: the second mutation and later cost double. */
export function mutationPriceMultiplier(purchased: number, policy: MutationPricingPolicy): number | null {
  if (!policy.ok) return null;
  return purchased <= 0 ? policy.first : policy.second_and_subsequent;
}

/** Listed price of a mutation for a warrior who already owns `purchased`. */
export function mutationPrice(reader: MutationReader, mutationId: IdString, purchased: number): number | null {
  const mutation = mutationCatalogue(reader).find((row) => row.id === mutationId);
  if (!mutation || mutation.cost_gc === null) return null;
  const multiplier = mutationPriceMultiplier(purchased, mutationPricingPolicy(reader));
  if (multiplier === null) return null;
  return mutation.cost_gc * multiplier;
}

/**
 * Whether a member joined during the pending post-battle. The recruitment flow
 * records one event per addition (`recruit` for a new profile, `recruit_member`
 * for a member added to an existing group) with the `warrior_id` it created, so
 * the moment of recruitment survives a save and a reopen instead of being
 * inferred from the mere existence of a post-battle.
 */
export function recruitedDuringPost(
  post: { readonly event_log?: readonly unknown[] } | OpenPayload | undefined | null,
  warriorId: IdString,
): boolean {
  const log = post && typeof post === "object" ? post["event_log"] : undefined;
  if (!Array.isArray(log)) return false;
  return log.some((entry) => {
    if (!entry || typeof entry !== "object") return false;
    const event = entry as OpenPayload;
    const type = String(event["type"] ?? "");
    return (
      (type === "recruit" || type === "recruit_member") &&
      String(event["warrior_id"] ?? "") === warriorId
    );
  });
}

/**
 * Buy one mutation for a member while he is being recruited (during the initial
 * draft or the post-battle recruitment). The price is written off against the
 * available gold and the purchase is recorded in `campaign.special_rules`.
 */
export function buyMutation(
  document: CampaignDocument,
  reader: MutationReader,
  input: { readonly warrior_id: IdString; readonly mutation_id: IdString },
): UseCaseResult {
  const bandId = document.campaign.identity.band_id;
  const warrior = document.campaign.warriors.find((row) => row.id === input.warrior_id);
  const draft = document.campaign.configuration.is_draft;
  const post = document.campaign.post_battles.find((row) => !row.complete);
  if (!draft && !post) {
    return { ok: false, reason: "not_permitted_when_committed", message: "Mutations may only be bought while a member is being recruited." };
  }
  if (!warrior) {
    return { ok: false, reason: "not_found", message: `${input.warrior_id} is not a member of this warband.`, subject_ids: [input.warrior_id] };
  }
  // The printed rule is `at_recruitment_only`: a post-battle is the moment a
  // member *joins*, not a window to mutate a veteran. Only the members this
  // pending post-battle recruited may buy, and the event log says who they are.
  if (!draft && !recruitedDuringPost(post, warrior.id)) {
    return {
      ok: false,
      reason: "not_permitted_when_committed",
      message: `${warrior.name} joined before this post-battle: mutations are bought when a member is recruited, not later.`,
      subject_ids: [warrior.id],
    };
  }
  const rule = mutationGrantRulesOf(reader, bandId).find((row) => row.mutation_ids.includes(input.mutation_id));
  if (!rule) {
    const known = mutationCatalogue(reader).some((row) => row.id === input.mutation_id);
    return {
      ok: false,
      reason: known ? "not_permitted_in_draft" : "not_found",
      message: known
        ? `${warrior.name}'s warband has no printed grant for ${input.mutation_id}.`
        : `Unknown mutation "${input.mutation_id}".`,
      subject_ids: [input.mutation_id],
    };
  }
  if (rule.recipients === "hero" && warrior.kind !== "hero") {
    return { ok: false, reason: "invalid_input", message: `${rule.name} grants mutations to Heroes only.`, subject_ids: [warrior.id] };
  }
  if (rule.profile_ids.length > 0 && !(warrior.profile_id && rule.profile_ids.includes(warrior.profile_id))) {
    return { ok: false, reason: "invalid_input", message: `${rule.name} does not grant mutations to ${warrior.profile_name}.`, subject_ids: [warrior.id] };
  }
  const owned = mutationsOf(document, warrior.id);
  if (owned.includes(input.mutation_id)) {
    return { ok: false, reason: "conflict", message: `${warrior.name} already has ${input.mutation_id}.`, subject_ids: [warrior.id, input.mutation_id] };
  }
  if (rule.limit_per_warrior !== null && owned.length >= rule.limit_per_warrior) {
    return { ok: false, reason: "limit_reached", message: `${warrior.name} may hold at most ${rule.limit_per_warrior} mutation(s).`, subject_ids: [warrior.id] };
  }
  const pricing = mutationPricingPolicy(reader);
  if (!pricing.ok) {
    return {
      ok: false,
      reason: "not_available",
      message: `The mutation purchase policy "${pricing.first}" / "${pricing.second_and_subsequent}" has no contract.`,
      subject_ids: [input.mutation_id],
    };
  }
  const price = mutationPrice(reader, input.mutation_id, owned.length);
  if (price === null) {
    return { ok: false, reason: "not_found", message: `No listed price is published for ${input.mutation_id}.`, subject_ids: [input.mutation_id] };
  }
  const available = draft
    ? treasury(document.campaign)
    : (currentState(document)?.gold ?? 0) + (post?.gold_delta ?? 0);
  if (price > available) {
    return { ok: false, reason: "limit_violated", message: `Not enough gold: ${price} gc needed, ${available} available.` };
  }
  const order = document.campaign.special_rules.filter((row) => row["kind"] === MUTATION_MARKER).length + 1;
  const mutation = mutationCatalogue(reader).find((row) => row.id === input.mutation_id)!;
  const text = `${warrior.name} gains ${mutation.name} for ${price} gc.`;
  const entry: OpenPayload = {
    kind: MUTATION_MARKER,
    warrior_id: warrior.id,
    mutation_id: input.mutation_id,
    grant_rule_id: rule.id,
    rule_id: rule.rule_id,
    cost_gc: price,
    order,
    text,
    texts: { en: text, ...mutation.name_i18n },
    source: rule.rule_id,
    expires_after_battles: null,
    consume_when_opponent_contains: [],
  };
  // During the draft the purchase raises the member's recruitment cost, which is
  // exactly what `treasury` subtracts; after a battle the cost leaves the
  // pending post-battle's gold.
  const warriors = draft
    ? document.campaign.warriors.map((row) => row.id === warrior.id ? { ...row, cost: row.cost + price } : row)
    : document.campaign.warriors;
  const postBattles = draft || !post
    ? document.campaign.post_battles
    : document.campaign.post_battles.map((row) =>
        row === post
          ? { ...row, gold_delta: (row.gold_delta ?? 0) - price, event_log: [...(row.event_log ?? []), { ...entry, step: row.active_step, type: MUTATION_MARKER }] }
          : row,
      );
  return {
    ok: true,
    state: withCampaign(document, {
      ...document.campaign,
      warriors,
      post_battles: postBattles,
      special_rules: [...document.campaign.special_rules, entry],
    }),
  };
}
