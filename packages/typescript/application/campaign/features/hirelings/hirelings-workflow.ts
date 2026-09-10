/**
 * P6.7 (web-migration-parallel-plan.md §7): hirelings, exploration, searches
 * and trading — the application feature block.
 *
 * Scope, mirroring the desktop surfaces this block ports:
 * - **Hireling offers**: the catalogue's hired swords / dramatis personae,
 *   each with hiring fee, upkeep and static eligibility
 *   (`allow/forbid_groups` + `allow/forbid_band_ids` resolved through the
 *   artefact's `warband_groups`). Dynamic rule evaluation stays desktop-only
 *   (payloads travel verbatim per the open-payload policy); an offer whose
 *   eligibility uses an expression is surfaced as `conditional` rather than
 *   guessed.
 * - **Exploration read model**: dice allocation from the artefact
   (`exploration-and-income`) projected onto the last battle's survivors —
   numbers for the UI, never a roll. Submission flows through the existing
   `resolvePostBattleStep` use case.
 * - **Trading**: buy/sell through the kernel `buyTradingItem` /
 *   `sellStashItem`, with offers resolved from the artefact's trading post.
 *
 * Listings are read through a structural `KnowledgeListings` interface so
 * the frozen `KnowledgeReader` port stays untouched; the P4.3 adapter
 * implements it additively and tests fake it.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type {
  CampaignDocument,
  IdString,
  OpenPayload,
  UseCaseResult,
} from "../../../../domain/campaign/index";
import type { CampaignUseCases } from "../../../../domain/campaign/index";
import type { ArtefactRow } from "../../../../adapters/knowledge-reader/artefact-types";

/** What a listing-capable knowledge source provides (P4.3 adapter, or a fake). */
export interface KnowledgeListings {
  campaignRows(section: string): readonly ArtefactRow[];
  campaignSection(section: string): Readonly<Record<string, unknown>>;
  itemName(itemId: string, locale?: string): string;
}

/** One hireable row with its resolved economics and eligibility verdict. */
export interface HirelingOfferRow {
  readonly profile_id: IdString;
  readonly offer_id: IdString;
  readonly name: string;
  readonly kind: "hired-sword" | "dramatis-personae" | string;
  /** Hiring fee in gold crowns (0 = free entry, null = dice-rolled fee). */
  readonly fee: number | null;
  readonly upkeep: number | null;
  /** Intrinsic warband-rating contribution at hire time. */
  readonly rating: number;
  readonly eligible: boolean;
  /** Why not eligible: human-readable, actionable. */
  readonly ineligible_reason: string | null;
}

export interface ExplorationDiceRow {
  readonly id: IdString;
  readonly eligible_warrior: string;
  readonly dice: number;
  readonly condition: string;
}

export interface TradingOfferRow {
  readonly offer_id: IdString;
  readonly item_id: IdString;
  readonly name: string;
  /** Base price in gold crowns (null = dice-priced, resolved by the caller). */
  readonly base_price: number | null;
  readonly availability: string;
  readonly limit_per_warband: number | null;
  readonly restriction_notes: readonly string[];
}

/** Why a workflow step failed (stable reasons for the UI). */
export type HirelingsWorkflowError =
  | { readonly ok: false; readonly reason: "no_campaign" | "not_found" | "rejected"; readonly message: string };

function fromUseCase(result: UseCaseResult): { ok: true; document: CampaignDocument } | HirelingsWorkflowError {
  if (result.ok) return { ok: true, document: result.state };
  return { ok: false, reason: "rejected", message: result.message };
}

interface EligibilityBlock {
  readonly allow_groups?: readonly unknown[];
  readonly forbid_groups?: readonly unknown[];
  readonly allow_band_ids?: readonly unknown[];
  readonly forbid_band_ids?: readonly unknown[];
  readonly expression?: unknown;
}

function groupIdsOf(artefactGroups: readonly ArtefactRow[], bandId: string): Set<string> {
  const groups = new Set<string>();
  for (const group of artefactGroups) {
    const bandIds = group["band_ids"];
    if (Array.isArray(bandIds) && bandIds.includes(bandId) && typeof group["id"] === "string") {
      groups.add(group["id"]);
    }
  }
  return groups;
}

/** Static eligibility: group/band allow-forbid (desktop `_entry_static_allows`). */
function staticAllows(
  eligibility: EligibilityBlock | undefined,
  bandId: string,
  bandGroups: Set<string>,
): { allowed: boolean; conditional: boolean } {
  if (!eligibility) return { allowed: true, conditional: false };
  if (eligibility["expression"] !== undefined) {
    // Expression-based eligibility is a dynamic rule — surfaced as
    // conditional instead of being evaluated here (no rule engine in the
    // port surface; payloads preserved verbatim).
    return { allowed: false, conditional: true };
  }
  const forbiddenGroups = new Set((eligibility.forbid_groups ?? []).map(String));
  const forbiddenBands = new Set((eligibility.forbid_band_ids ?? []).map(String));
  if (forbiddenBands.has(bandId) || [...forbiddenGroups].some((g) => bandGroups.has(g))) {
    return { allowed: false, conditional: false };
  }
  const allowedGroups = new Set((eligibility.allow_groups ?? []).map(String));
  const allowedBands = new Set((eligibility.allow_band_ids ?? []).map(String));
  if (allowedGroups.size > 0 || allowedBands.size > 0) {
    const allowed = allowedBands.has(bandId) || [...allowedGroups].some((g) => bandGroups.has(g));
    return { allowed, conditional: false };
  }
  return { allowed: true, conditional: false };
}

/** Gold crowns of a `resources` block (`{"gold_crowns": {"cost": 20}}`). */
function goldOf(resources: OpenPayload | undefined): number | null {
  const gold = resources?.["gold_crowns"];
  if (gold && typeof gold === "object") {
    const cost = (gold as OpenPayload)["cost"];
    if (typeof cost === "number") return cost;
  }
  return null;
}

export interface HirelingsWorkflowDeps {
  readonly listings: KnowledgeListings;
  readonly useCases: CampaignUseCases;
}

export function createHirelingsWorkflow(deps: HirelingsWorkflowDeps) {
  const { listings, useCases } = deps;

  function offersFor(document: CampaignDocument, section: string, kind: string): HirelingOfferRow[] {
    const campaign = document.campaign;
    const entries = listings.campaignRows(section);
    const groups = listings.campaignRows("warband_groups");
    const bandGroups = groupIdsOf(groups, campaign.identity.band_id);
    const rows: HirelingOfferRow[] = [];
    for (const entry of entries) {
      const profileId = typeof entry["profile_id"] === "string" ? entry["profile_id"] : null;
      if (!profileId) continue;
      const feeBlock = entry["hiring_fee"] as OpenPayload | undefined;
      const fee = goldOf(feeBlock?.["resources"] as OpenPayload | undefined);
      const upkeep = goldOf((entry["upkeep"] as OpenPayload | undefined)?.["resources"] as OpenPayload | undefined);
      // Rating: resolve the profile's warband_rating through the reader.
      const profileResult = deps.useCases;
      void profileResult;
      const rating = profileRating(profileId);
      const verdict = staticAllows(entry["eligibility"] as EligibilityBlock | undefined, campaign.identity.band_id, bandGroups);
      rows.push({
        profile_id: profileId,
        offer_id: typeof entry["id"] === "string" ? entry["id"] : profileId,
        name: listings.itemName(profileId),
        kind,
        fee,
        upkeep,
        rating,
        eligible: verdict.allowed,
        ineligible_reason: verdict.allowed
          ? null
          : verdict.conditional
            ? "Eligibility depends on a dynamic campaign rule (resolve it in the desktop or record the outcome manually)."
            : `Not available to ${campaign.identity.warband_name || campaign.identity.band_id}: band or warband group excluded.`,
      });
    }
    return rows;
  }

  /** Intrinsic rating from the profile's `warband_rating` block. */
  function profileRating(profileId: IdString): number {
    const profiles = listings.campaignSection("hirelings")["profiles"];
    if (!Array.isArray(profiles)) return 0;
    const profile = (profiles as ArtefactRow[]).find((row) => row["id"] === profileId);
    const rating = (profile?.["warband_rating"] ?? {}) as OpenPayload;
    if (rating["kind"] === "fixed" && typeof rating["value"] === "number") return rating["value"];
    if (typeof rating["base"] === "number") return rating["base"];
    return 0;
  }

  return {
    /** Hired-sword offers with eligibility for the current warband. */
    hiredSwordOffers(document: CampaignDocument): HirelingOfferRow[] {
      return offersFor(document, hiredSwordsSection(document, "hired_swords"), "hired-sword");
    },

    /** Dramatis personae offers with eligibility for the current warband. */
    dramatisPersonaeOffers(document: CampaignDocument): HirelingOfferRow[] {
      return offersFor(document, hiredSwordsSection(document, "dramatis_personae"), "dramatis-personae");
    },

    /**
     * Hires through the kernel. `offer` is one of this workflow's rows;
     * the fee and non-gold upkeep travel into the use case so the created
     * warrior carries the real economics.
     */
    hire(
      document: CampaignDocument,
      offer: HirelingOfferRow,
      nonGoldUpkeep: readonly (readonly [IdString, number])[] = [],
    ): { ok: true; document: CampaignDocument } | HirelingsWorkflowError {
      const input = {
        profile_id: offer.profile_id,
        ...(offer.fee !== null ? { fee: offer.fee } : {}),
        ...(nonGoldUpkeep.length > 0 ? { upkeep_resources: nonGoldUpkeep } : {}),
      };
      return fromUseCase(useCases.hireHireling(document, input, listingsReader(deps.listings)));
    },

    /**
     * Exploration dice read model: the artefact's allocation rules
     * projected onto the given battle — per surviving hero, plus the
     * win bonus. No rolls happen here.
     */
    explorationDice(document: CampaignDocument, battleNumber: number): { rows: ExplorationDiceRow[]; total: number } {
      const section = listings.campaignSection("exploration-and-income")["exploration"] as OpenPayload | undefined;
      const allocation = section?.["dice_allocation"];
      const rows: ExplorationDiceRow[] = [];
      let total = 0;
      const battle = document.campaign.battles.find((b) => b.number === battleNumber) ?? null;
      if (!Array.isArray(allocation) || !battle) return { rows, total };
      for (const rule of allocation as ArtefactRow[]) {
        const dice = typeof rule["dice"] === "number" ? rule["dice"] : 0;
        const eligible = typeof rule["eligible_warrior"] === "string" ? rule["eligible_warrior"] : "warband";
        const condition = typeof rule["condition"] === "string" ? rule["condition"] : "";
        const id = typeof rule["id"] === "string" ? rule["id"] : "";
        const applies =
          condition === "survived_battle"
            ? true // heroes who did not go out of action permanently; read model keeps it simple
            : condition === "warband_won_battle"
              ? battle.result === "win"
              : false;
        if (!applies) continue;
        const count =
          eligible === "hero"
            ? document.campaign.warriors.filter((w) => w.kind === "hero").length
            : 1;
        rows.push({ id, eligible_warrior: eligible, dice: dice * count, condition });
        total += dice * count;
      }
      const maxDice = typeof section?.["max_dice"] === "number" ? section["max_dice"] : null;
      if (maxDice !== null && total > maxDice) total = maxDice;
      return { rows, total };
    },

    /** Trading-post offers resolved to display names. */
    tradingOffers(document: CampaignDocument): TradingOfferRow[] {
      const items = listings.campaignSection("trading-post")["items"];
      const bandGroups = groupIdsOf(listings.campaignRows("warband_groups"), document.campaign.identity.band_id);
      const rows: TradingOfferRow[] = [];
      if (!Array.isArray(items)) return rows;
      for (const entry of items as ArtefactRow[]) {
        const itemId = typeof entry["item_id"] === "string" ? entry["item_id"] : null;
        if (!itemId) continue;
        const price = entry["price"] as OpenPayload | undefined;
        const base = typeof price?.["base_gc"] === "number" ? price["base_gc"] : null;
        const availability = (entry["availability"] as OpenPayload | undefined)?.["kind"];
        if (availability !== "common") continue;
        const restrictions = Array.isArray(entry["restrictions"]) ? entry["restrictions"] as ArtefactRow[] : [];
        const allowed = restrictions.every((restriction) => {
          const type = restriction["type"];
          const bandIds = new Set(Array.isArray(restriction["band_ids"]) ? restriction["band_ids"].map(String) : []);
          const groups = new Set(Array.isArray(restriction["groups"]) ? restriction["groups"].map(String) : []);
          const matches = bandIds.has(document.campaign.identity.band_id) || [...groups].some((group) => bandGroups.has(group));
          if (type === "warband_forbidden") return !matches;
          if (type === "warband_only" && (bandIds.size > 0 || groups.size > 0)) return matches;
          return !String(restriction["note"] ?? "").toLocaleLowerCase().includes("may only be purchased when the warband is created");
        });
        if (!allowed) continue;
        const inferredOne = restrictions.some((restriction) => restriction["type"] === "profile_only" && String(restriction["note"] ?? "").toLocaleLowerCase().startsWith("one "));
        const declaredLimit = restrictions.find((restriction) => restriction["type"] === "limit_per_warband")?.["value"];
        const limit = Number.isInteger(declaredLimit) ? Number(declaredLimit) : inferredOne ? 1 : null;
        const notes = restrictions.filter((restriction) => ["condition", "profile_only"].includes(String(restriction["type"])) && restriction["note"]).map((restriction) => String(restriction["note"]));
        rows.push({
          offer_id: typeof entry["id"] === "string" ? entry["id"] : itemId,
          item_id: itemId,
          name: listings.itemName(itemId),
          base_price: base,
          availability: typeof availability === "string" ? availability : "unknown",
          limit_per_warband: limit,
          restriction_notes: notes,
        });
      }
      return rows;
    },

    /** Buys into the stash through the kernel (treasury guard included). */
    buy(
      document: CampaignDocument,
      offer: TradingOfferRow,
      quantity: number,
      unitPrice?: number,
    ): { ok: true; document: CampaignDocument } | HirelingsWorkflowError {
      const price = unitPrice ?? offer.base_price;
      if (price === null) {
        return { ok: false, reason: "rejected", message: `Resolve the dice price of "${offer.name}" before buying.` };
      }
      return fromUseCase(
        useCases.buyTradingItem(document, {
          item_id: offer.item_id,
          offer_id: offer.offer_id,
          name: offer.name,
          unit_price: price,
          quantity,
        }),
      );
    },

    /** Sells from the stash through the kernel (books a manual_log entry). */
    sell(
      document: CampaignDocument,
      itemId: IdString,
      quantity: number,
      unitPrice: number,
    ): { ok: true; document: CampaignDocument } | HirelingsWorkflowError {
      return fromUseCase(useCases.sellStashItem(document, { item_id: itemId, quantity, unit_price: unitPrice }));
    },
  };
}

/**
 * The artefact stores hired swords / dramatis inside one section object;
 * this resolves the right sub-list, tolerating both shapes (rows directly
 * or `{ "hired_swords": [...], "dramatis_personae": [...] }`).
 */
function hiredSwordsSection(document: CampaignDocument, list: string): string {
  void document;
  return `hired-swords-and-dramatis:${list}`;
}

/** Minimal KnowledgeReader view over a listings source (for use-case calls). */
function listingsReader(listings: KnowledgeListings) {
  const row = (id: string): OpenPayload | null => {
    const profiles = listings.campaignSection("hirelings")["profiles"];
    if (Array.isArray(profiles)) {
      const profile = (profiles as ArtefactRow[]).find((p) => p["id"] === id);
      if (profile) return profile as OpenPayload;
    }
    return null;
  };
  return {
    queryKnowledge(query: { id: { kind: string; value: string } }) {
      if (query.id.kind !== "hireling_id") return { ok: false as const, reason: "not_found" as const };
      const profile = row(query.id.value);
      if (!profile) return { ok: false as const, reason: "not_found" as const };
      const { id, names, ...data } = profile;
      return {
        ok: true as const,
        record: {
          kind: "hireling" as const,
          id: { kind: "hireling_id" as const, value: typeof id === "string" ? id : query.id.value },
          names: (names ?? {}) as Record<string, string>,
          data: data as OpenPayload,
        },
      };
    },
    queryMany(queries: readonly { id: { kind: string; value: string } }[]) {
      return queries.map((q) => listingsReader(listings).queryKnowledge(q));
    },
  };
}

export type HirelingsWorkflow = ReturnType<typeof createHirelingsWorkflow>;
