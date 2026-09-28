/**
 * P3.5: draft creation and composition — the pure port of the Python
 * `domain/builders.py` draft path and the composition rules of
 * `CampaignVM.draft_is_legal`.
 *
 * The KB enters only through the frozen `KnowledgeReader` port: the band
 * record's `roster` (minimum/maximum models, starting gold, member caps) and
 * the band's profile records (kind, cost, characteristics, fixed equipment)
 * are read by stable id, never by name. Fakes work the same way.
 *
 * `composeDraft` honours the frozen batch `DraftCompositionInput`
 * (`band_id` + `rows[]`); the KnowledgeReader is closed over by
 * `createDefaultUseCases` because the frozen `CampaignUseCases` surface does
 * not pass it per call.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignIdentity, IdString, OpenPayload } from "./state";
import type { KnowledgeReader } from "./ports";
import type {
  Campaign,
  CampaignDocument,
  DraftCompositionInput,
  EquipmentEntry,
  InventoryItem,
  UseCaseResult,
  Warrior,
} from "./usecases";
import { rejected } from "./rejections";
import { memberCount, uniqueWarriorName } from "./document";
import { selectedWarbandVariant, warbandVariants } from "../band-variants";
import {
  bandFactsOf,
  characteristicBoundIssueFor,
  equipmentIssueFor,
  itemFactsOf,
  profileExclusionFor,
  profileFactsOf,
  racialMaximumResolutionFor,
  racialMaximumsOf,
  variantFrameOf,
} from "../construction";

/** Characteristic display keys, in KB order. */
export const STAT_KEYS = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const;

/** Composition limits read from the band record's roster payload. */
export interface RosterRules {
  readonly minimum_models: number;
  readonly maximum_models: number;
  readonly starting_gold: number;
  /** Sum of hero member caps; `null` when the band declares no hero caps. */
  readonly hero_limit: number | null;
}

/** Profile-kind resolver: profile id → "hero" | "henchman" | null (unknown). */
export type ProfileKindOf = (profileId: IdString) => "hero" | "henchman" | null;

/** Extracts the roster rules from a band KnowledgeRecord. */
export function rosterRulesOf(
  bandRecord: { readonly data: OpenPayload },
  profileKindOf: ProfileKindOf,
): RosterRules | null {
  const roster = bandRecord.data["roster"];
  if (!roster || typeof roster !== "object") return null;
  const raw = roster as OpenPayload;
  const minimumModels = raw["minimum_models"];
  const maximumModels = raw["maximum_models"];
  const startingGold = raw["starting_gold"];
  if (
    typeof minimumModels !== "number" ||
    typeof maximumModels !== "number" ||
    typeof startingGold !== "number"
  ) {
    return null;
  }
  const members = Array.isArray(raw["members"]) ? (raw["members"] as OpenPayload[]) : [];
  const heroCaps: number[] = [];
  for (const member of members) {
    const profileId = member["profile_id"];
    if (typeof profileId !== "string") continue;
    if (profileKindOf(profileId) !== "hero") continue;
    const maximum = member["maximum"];
    if (typeof maximum === "number") heroCaps.push(maximum);
  }
  return {
    minimum_models: minimumModels,
    maximum_models: maximumModels,
    starting_gold: startingGold,
    hero_limit: heroCaps.length > 0 ? heroCaps.reduce((t, c) => t + c, 0) : null,
  };
}

function profileRecord(
  knowledge: KnowledgeReader,
  bandId: IdString,
  profileId: IdString,
): OpenPayload | null {
  const catalogue = knowledge as KnowledgeReader & {
    list?(kind: "profile"): readonly OpenPayload[];
  };
  const scoped = catalogue.list?.("profile").find(
    (profile) => profile["id"] === profileId && profile["band_id"] === bandId,
  );
  if (scoped) return scoped;

  const result = knowledge.queryKnowledge({ id: { kind: "profile_id", value: profileId } });
  if (!result.ok) return null;
  const data = result.record.data as OpenPayload;
  // Profiles are scoped per band in the artefact; a hit whose `band_id`
  // disagrees belongs to another band's unscoped fallback row.
  if (typeof data["band_id"] === "string" && data["band_id"] !== bandId) return null;
  return data;
}

function statMap(characteristics: OpenPayload): Record<string, number> {
  const stats: Record<string, number> = {};
  for (const key of STAT_KEYS) {
    const value = characteristics[key];
    if (typeof value === "number") stats[key] = value;
  }
  return stats;
}

/** Item display name resolver honouring the canonical English; falls back to the id. */
function makeItemName(knowledge: KnowledgeReader): (itemId: IdString) => string {
  return (itemId) => {
    const result = knowledge.queryKnowledge({ id: { kind: "item_id", value: itemId } });
    if (!result.ok) return itemId;
    const names = result.record.names as Readonly<Record<string, string>>;
    return names["en"] ?? itemId;
  };
}

/**
 * Cheapest item of one family the profile's lists offer, at its creation price.
 * Used by the starter for a band rule that requires a compulsory family
 * (`profile.equipment-restrictions` `required_tag`).
 */
function requiredTagOffer(
  knowledge: KnowledgeReader,
  bandId: IdString,
  profileId: IdString,
  tag: string,
): { readonly item_id: IdString; readonly cost: number } | null {
  const profile = profileRecord(knowledge, bandId, profileId);
  if (!profile) return null;
  const offers = Array.isArray(profile["equipment_access"])
    ? (profile["equipment_access"] as OpenPayload[])
    : [];
  const candidates = offers.flatMap((offer) => {
    const itemId = offer["item_id"];
    if (typeof itemId !== "string") return [];
    if (!(itemFactsOf(knowledge, itemId)?.tags ?? []).includes(tag)) return [];
    const listed = offer["cost"];
    const item = knowledge.queryKnowledge({ id: { kind: "item_id", value: itemId } });
    const cost =
      typeof listed === "number"
        ? listed
        : item.ok && typeof item.record.data["value"] === "number"
          ? (item.record.data["value"] as number)
          : 0;
    return [{ item_id: itemId, cost }];
  });
  return candidates.sort((left, right) => left.cost - right.cost)[0] ?? null;
}

/**
 * Builds a draft warrior row from a KB profile payload. Only the profile's
 * *fixed* equipment is attached here (acquisition "fixed"); listed
 * equipment is appended by `composeDraft` as "purchase" entries so the
 * two acquisition paths never blur.
 */
export function warriorFromProfile(
  profile: OpenPayload,
  input: {
    readonly profile_id: IdString;
    readonly kind: "hero" | "henchman";
    readonly quantity: number;
    readonly equipment?: readonly IdString[];
  },
  itemName: (itemId: IdString) => string,
  occurrence: number,
): Warrior {
  const kind = profile["type"] === "hero" ? "hero" : "henchman";
  const characteristics =
    profile["characteristics"] && typeof profile["characteristics"] === "object"
      ? (profile["characteristics"] as OpenPayload)
      : {};
  const fixed = Array.isArray(profile["fixed_equipment"])
    ? (profile["fixed_equipment"] as unknown[])
    : [];
  const equipmentIds = fixed.filter((id): id is IdString => typeof id === "string");
  const equipmentAccess = Array.isArray(profile["equipment_access"])
    ? profile["equipment_access"] as OpenPayload[]
    : [];
  const freeDagger = equipmentAccess.find((offer) => {
    const itemId = offer["item_id"];
    const note = typeof offer["notes"] === "string" ? offer["notes"].toLowerCase() : "";
    return typeof itemId === "string" && itemId.includes("dagger") && (!note || ((note.includes("first") || note.includes("1st")) && note.includes("free")));
  });
  const entries: EquipmentEntry[] = equipmentIds.map((itemId) => ({
    item_id: itemId,
    name: itemName(itemId),
    quantity: input.quantity,
    acquisition: "fixed",
    per_model: true,
  }));
  const freeDaggerId = freeDagger?.["item_id"];
  if (typeof freeDaggerId === "string" && !equipmentIds.includes(freeDaggerId)) {
    entries.push({
      item_id: freeDaggerId,
      name: itemName(freeDaggerId),
      quantity: input.quantity,
      acquisition: "starting_grant",
      unit_cost: 0,
      per_model: true,
      transferable: false,
    });
  }
  const combatTraits =
    profile["combat_traits"] && typeof profile["combat_traits"] === "object"
      ? (profile["combat_traits"] as OpenPayload)
      : {};
  const startingSkills = Array.isArray(combatTraits["starting_skills"])
    ? (combatTraits["starting_skills"] as unknown[]).filter(
        (s): s is string => typeof s === "string",
      )
    : [];
  const inherent = Array.isArray(profile["inherent_rules"])
    ? (profile["inherent_rules"] as unknown[]).filter((s): s is string => typeof s === "string")
    : [];
  const profileRules = Array.isArray(profile["rule_ids"])
    ? (profile["rule_ids"] as unknown[]).filter((s): s is string => typeof s === "string")
    : [];
  const skillAccess = Array.isArray(profile["skill_access"])
    ? (profile["skill_access"] as unknown[]).filter((s): s is string => typeof s === "string")
    : [];
  return {
    id: `${input.profile_id}#${occurrence}`,
    name: typeof profile["name"] === "string" ? profile["name"] : input.profile_id,
    profile_name: typeof profile["name"] === "string" ? profile["name"] : input.profile_id,
    kind,
    stats: statMap(characteristics),
    equipment: entries,
    skills: [...new Set([...inherent, ...profileRules, ...startingSkills])],
    experience: typeof profile["experience"] === "number" ? profile["experience"] : 0,
    quantity: input.quantity,
    cost: typeof profile["cost"] === "number" ? profile["cost"] : 0,
    profile_id: input.profile_id,
    skill_access: skillAccess,
  };
}

/**
 * Creates a draft for a warband: identity and configuration from the band
 * record's roster, an initial roster filled from member minimums, then the
 * cheapest henchmen up to the minimum model count (the shared
 * `mordheim_construction` starter algorithm). Rejects unknown bands and
 * unusable rosters.
 *
 * `variantId` is the mandatory warband variant when it is already chosen
 * (`background.native`, `bloodline.lahmia`…): the draft is built for that
 * option — its slots open and a bloodline's Vampire arrives as the leader — and
 * the choice travels in `identity.mercenary_variant`. Without it, a band that
 * demands the choice keeps every gated slot locked.
 */
export function createDraft(
  bandId: IdString,
  knowledge: KnowledgeReader,
  campaignName = "New Mordheim Campaign",
  variantId: string | null = null,
): UseCaseResult {
  const bandResult = knowledge.queryKnowledge({ id: { kind: "band_id", value: bandId } });
  if (!bandResult.ok) {
    return rejected("not_found", `Unknown warband id: ${bandId}.`);
  }
  const bandRecord = bandResult.record;
  const requestedVariant = String(variantId ?? "").trim().toLowerCase();
  if (
    requestedVariant &&
    !warbandVariants(knowledge, bandId).some((option) => option.id === requestedVariant)
  ) {
    return rejected("invalid_input", `Unknown warband variant for ${bandId}: ${variantId}.`);
  }
  const rules = rosterRulesOf(bandRecord, (profileId) => {
    const profile = profileRecord(knowledge, bandId, profileId);
    if (!profile) return null;
    return profile["type"] === "hero" ? "hero" : "henchman";
  });
  if (!rules) {
    return rejected(
      "invalid_input",
      `Warband "${bandId}" has no usable roster definition in the knowledge base.`,
    );
  }
  // A band whose mandatory roster needs a profile the runtime-scope excludes
  // cannot produce a legal draft (T09: an exclusion is never turned into a
  // normal profile, and never into a generic allowlist).
  const declaredRoster =
    bandRecord.data["roster"] && typeof bandRecord.data["roster"] === "object"
      ? (bandRecord.data["roster"] as OpenPayload)
      : {};
  const declaredMembers = Array.isArray(declaredRoster["members"])
    ? (declaredRoster["members"] as OpenPayload[])
    : [];
  for (const member of declaredMembers) {
    const profileId = member["profile_id"];
    const minimum = member["minimum"];
    if (typeof profileId !== "string" || typeof minimum !== "number" || minimum <= 0) continue;
    const exclusion = profileExclusionFor(bandId, profileId);
    if (exclusion) {
      return rejected(
        "invalid_input",
        `Warband "${bandId}" requires ${profileId}, which is outside the warband roster as a fighter: ${exclusion.reason}`,
      );
    }
  }

  // The mandatory variant choice resolves which declared slots are open: a
  // gated member stays locked until its option is chosen (the published `0/0`
  // state), and the chosen bloodline's Vampire becomes the mandatory leader.
  const band = bandFactsOf(knowledge, bandId);
  const frame = band ? variantFrameOf(knowledge, band, requestedVariant || null) : null;
  const members: OpenPayload[] = frame
    ? frame.available.map((member) => ({
        profile_id: member.profile_id,
        minimum: member.minimum,
        maximum: member.maximum,
        ...(member.group_size ? { group_size: { ...member.group_size } } : {}),
      }))
    : declaredMembers;
  // The hero cap belongs to the resolved frame too: the declared maxima do not
  // include the leader a bloodline unlocks and still count the Vampires the
  // choice removes (the Chaos in the Streets band publishes them at `0/0`).
  const heroCaps = members
    .filter((member) => typeof member["profile_id"] === "string")
    .filter((member) => {
      const profile = profileRecord(knowledge, bandId, member["profile_id"] as IdString);
      return profile !== null && profile["type"] === "hero";
    })
    .map((member) => member["maximum"])
    .filter((maximum): maximum is number => typeof maximum === "number");
  const heroLimit = heroCaps.length > 0 ? heroCaps.reduce((total, cap) => total + cap, 0) : rules.hero_limit;
  const itemName = makeItemName(knowledge);

  const occurrences = new Map<IdString, number>();
  const nextOccurrence = (profileId: IdString): number => {
    const next = (occurrences.get(profileId) ?? 0) + 1;
    occurrences.set(profileId, next);
    return next;
  };

  const rows: Warrior[] = [];
  const add = (profile: OpenPayload, quantity: number, profileId: IdString): void => {
    if (quantity <= 0) return;
    const warrior = warriorFromProfile(
      profile,
      {
        profile_id: profileId,
        kind: profile["type"] === "hero" ? "hero" : "henchman",
        quantity,
        equipment: [],
      },
      itemName,
      nextOccurrence(profileId),
    );
    rows.push({ ...warrior, name: uniqueWarriorName(rows, warrior.name) });
  };

  // 1. Mandatory members (roster minimums).
  for (const member of members) {
    const profileId = member["profile_id"];
    if (typeof profileId !== "string") continue;
    const minimum = member["minimum"];
    if (typeof minimum !== "number" || minimum <= 0) continue;
    const profile = profileRecord(knowledge, bandId, profileId);
    if (!profile) continue;
    add(profile, minimum, profileId);
  }

  // 2. Fill up to the minimum model count with the cheapest henchman groups.
  // Mirrors the shared Python starter algorithm: without a declared
  // `group_size`, a row may hold as many models as the member maximum allows
  // (or as many as still needed), never silently one.
  const groupMax = (member: OpenPayload): number | null => {
    const gs = member["group_size"];
    if (gs && typeof gs === "object") {
      const raw = gs as OpenPayload;
      return typeof raw["maximum"] === "number" ? raw["maximum"] : null;
    }
    return null;
  };
  const membersWithProfiles = members
    .map((member) => {
      const profileId = member["profile_id"];
      if (typeof profileId !== "string") return null;
      const profile = profileRecord(knowledge, bandId, profileId);
      return profile ? { member, profile, profileId } : null;
    })
    .filter((entry): entry is NonNullable<typeof entry> => entry !== null);
  const fillCandidates = membersWithProfiles
    .filter(({ profileId, profile }) => profile["type"] === "henchman" && !profileExclusionFor(bandId, profileId))
    .sort((a, b) => {
      const costA = typeof a.profile["cost"] === "number" ? a.profile["cost"] : Number.MAX_SAFE_INTEGER;
      const costB = typeof b.profile["cost"] === "number" ? b.profile["cost"] : Number.MAX_SAFE_INTEGER;
      return costA - costB;
    });
  for (const { member, profile, profileId } of fillCandidates) {
    if (memberCount(rows) >= rules.minimum_models) break;
    const needed = rules.minimum_models - memberCount(rows);
    if (needed <= 0) break;
    if (member["maximum"] === 0) continue; // closed member slot
    const memberMaximum = typeof member["maximum"] === "number" ? (member["maximum"] as number) : null;
    const perRowCap = groupMax(member) ?? memberMaximum ?? needed;
    const quantity = Math.min(needed, Math.max(1, perRowCap));
    add(profile, quantity, profileId);
  }

  // 3. All-hero-optional bands still need at least one hero.
  if (!rows.some((row) => row.kind === "hero")) {
    const heroCandidates = membersWithProfiles
      .filter(({ profile, profileId, member }) => {
        if (profile["type"] !== "hero" || profileExclusionFor(bandId, profileId)) return false;
        const maximum = member["maximum"];
        return maximum !== 0 && (typeof maximum !== "number" || maximum > 0);
      })
      .sort((a, b) => {
        const costA = typeof a.profile["cost"] === "number" ? a.profile["cost"] : Number.MAX_SAFE_INTEGER;
        const costB = typeof b.profile["cost"] === "number" ? b.profile["cost"] : Number.MAX_SAFE_INTEGER;
        return costA - costB;
      });
    for (const { profile, profileId } of heroCandidates) {
      const cost = typeof profile["cost"] === "number" ? profile["cost"] : 0;
      const spent = rows.reduce((t, row) => t + row.cost * (row.quantity ?? 1), 0);
      if (cost > rules.starting_gold - spent) continue;
      add(profile, 1, profileId);
      break;
    }
  }

  // 4. A band rule can require every member's kit to include an item family
  //    (`profile.equipment-restrictions` `required_tag`). The starter buys the
  //    cheapest permitted item of that family for every member the rule does not
  //    exempt, so the automatically built warband is the legal one the commit
  //    gate accepts — never a roster the construction contract refuses.
  const requiredTag = band?.equipment_limits?.required_tag?.trim() ?? "";
  const exemptProfiles = new Set(band?.equipment_limits?.exempt_profile_ids ?? []);
  const compulsory: { readonly item_id: IdString; readonly name: string; readonly copies: number; readonly cost: number }[] = [];
  const roster: Warrior[] = requiredTag
    ? rows.map((row) => {
        const copies = row.quantity ?? 1;
        if (!row.profile_id || exemptProfiles.has(row.profile_id)) return row;
        const holds = row.equipment.some(
          (entry) => (itemFactsOf(knowledge, entry.item_id)?.tags ?? []).includes(requiredTag),
        );
        if (holds) return row;
        const offer = requiredTagOffer(knowledge, bandId, row.profile_id, requiredTag);
        if (!offer) return row;
        compulsory.push({ item_id: offer.item_id, name: itemName(offer.item_id), copies, cost: offer.cost });
        return {
          ...row,
          equipment: [
            ...row.equipment,
            {
              item_id: offer.item_id,
              name: itemName(offer.item_id),
              quantity: copies,
              acquisition: "purchase" as const,
              unit_cost: offer.cost,
              per_model: true,
              acquisition_costs: Array(copies).fill(offer.cost),
            },
          ],
        };
      })
    : rows;
  let compulsoryInventory: InventoryItem[] = [];
  for (const entry of compulsory) {
    const existing = compulsoryInventory.find((item) => item.id === entry.item_id);
    compulsoryInventory = existing
      ? compulsoryInventory.map((item) => item === existing
          ? {
              ...item,
              owned: item.owned + entry.copies,
              equipped: item.equipped + entry.copies,
              acquisition_costs: [...(item.acquisition_costs ?? []), ...Array(entry.copies).fill(entry.cost)],
            }
          : item)
      : [
          ...compulsoryInventory,
          {
            id: entry.item_id,
            name: entry.name,
            category: "Equipment",
            owned: entry.copies,
            equipped: entry.copies,
            stash: 0,
            value: entry.cost,
            acquisition_costs: Array(entry.copies).fill(entry.cost),
          },
        ];
  }

  const collectionValue = bandRecord.data["collection"];
  const identity: CampaignIdentity = {
    campaign_name: campaignName,
    warband_name: `My ${bandRecord.names["en"] ?? bandId} Warband`,
    warband_type: bandRecord.names["en"] ?? bandId,
    band_id: bandId,
    mercenary_variant: requestedVariant || null,
    ...(typeof collectionValue === "string" ? { collection: collectionValue as IdString } : {}),
  };
  const campaign: Campaign = {
    identity,
    configuration: {
      is_draft: true,
      starting_gold: rules.starting_gold,
      minimum_models: rules.minimum_models,
      maximum_models: rules.maximum_models,
      hero_limit: heroLimit ?? 5,
    },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 0,
    warriors: roster,
    battles: [],
    states: [],
    post_battles: [],
    inventory: compulsoryInventory,
    special_rules: [],
    manual_log: [],
  };
  return { ok: true, state: { campaign, view: {} } };
}

/**
 * Applies a whole composition batch to the draft (frozen
 * `DraftCompositionInput`): appends one warrior row per entry and purchases
 * its listed equipment into the inventory, validating gold, model and hero
 * limits with the Python `draft_is_legal` formulas before committing.
 */
export function composeDraft(
  document: CampaignDocument,
  input: DraftCompositionInput,
  knowledge: KnowledgeReader,
): UseCaseResult {
  const { campaign } = document;
  if (!campaign.configuration.is_draft) {
    return rejected("not_permitted_when_committed", "Only a draft can be composed.");
  }
  if (input.band_id && input.band_id !== campaign.identity.band_id) {
    return rejected(
      "conflict",
      `Composition batch targets warband "${input.band_id}" but the draft is "${campaign.identity.band_id}".`,
    );
  }
  if (!Array.isArray(input.rows) || input.rows.length === 0) {
    return rejected("invalid_input", "Composition batch needs at least one row.");
  }

  const bandResult = knowledge.queryKnowledge({ id: { kind: "band_id", value: campaign.identity.band_id } });
  const bandRoster = bandResult.ok && bandResult.record.data["roster"] && typeof bandResult.record.data["roster"] === "object"
    ? bandResult.record.data["roster"] as OpenPayload : {};
  const rosterMembers = Array.isArray(bandRoster["members"]) ? bandRoster["members"] as OpenPayload[] : [];
  // The composition frame resolves the mandatory variant choice: a member the
  // selection forbids cannot be added, and its limits are the ones the choice
  // publishes (the background's lists and the chosen bloodline's leader slot).
  const band = bandFactsOf(knowledge, campaign.identity.band_id);
  const frame = band ? variantFrameOf(knowledge, band, campaign.identity.mercenary_variant) : null;
  const effectiveMembers: OpenPayload[] = frame
    ? frame.available.map((member) => ({
        profile_id: member.profile_id,
        minimum: member.minimum,
        maximum: member.maximum,
        ...(member.group_size ? { group_size: { ...member.group_size } } : {}),
      }))
    : rosterMembers;
  const effectiveById = new Map(effectiveMembers.map((member) => [String(member["profile_id"]), member]));
  const removedByVariant = new Set<string>(frame?.removed_profiles ?? []);

  const itemName = makeItemName(knowledge);
  const occurrences = new Map<IdString, number>();
  for (const row of campaign.warriors) {
    if (!row.profile_id) continue;
    const match = /#(\d+)$/.exec(row.id);
    const index = match ? Number(match[1]) : 0;
    if (index > (occurrences.get(row.profile_id) ?? 0)) {
      occurrences.set(row.profile_id, index);
    }
  }

  // Resolve and build every row first; abort on the first problem without
  // touching the document.
  interface PlannedRow {
    readonly warrior: Warrior;
    readonly purchased: readonly { readonly itemId: IdString; readonly value: number }[];
  }
  const planned: PlannedRow[] = [];
  for (const rowInput of input.rows) {
    const profile = profileRecord(knowledge, campaign.identity.band_id, rowInput.profile_id);
    if (!profile) {
      return rejected("not_found", `Unknown profile id: ${rowInput.profile_id}.`);
    }
    if (rowInput.quantity <= 0) {
      return rejected("invalid_input", "Row quantity must be positive.");
    }
    const kind = profile["type"] === "hero" ? "hero" : "henchman";
    if (kind !== rowInput.kind) {
      return rejected(
        "invalid_input",
        `Profile "${rowInput.profile_id}" is a ${kind} row, not ${rowInput.kind}.`,
      );
    }
    const declaredMember = rosterMembers.find((candidate) => candidate["profile_id"] === rowInput.profile_id);
    if (!declaredMember) return rejected("not_available", `Profile "${rowInput.profile_id}" is not available to this warband.`);
    if (removedByVariant.has(rowInput.profile_id)) {
      return rejected(
        "not_available",
        `"${rowInput.profile_id}" is not available under the selected warband variant "${frame?.variant_id}".`,
      );
    }
    const member = effectiveById.get(rowInput.profile_id) ?? declaredMember;
    const exclusion = profileExclusionFor(campaign.identity.band_id, rowInput.profile_id);
    if (exclusion) {
      return rejected(
        "not_available",
        `"${rowInput.profile_id}" is outside the warband roster as a fighter: ${exclusion.reason}`,
      );
    }
    if (kind === "hero" && rowInput.quantity !== 1) {
      return rejected("limit_violated", "Heroes must be recruited individually.");
    }
    const groupSize = member["group_size"] && typeof member["group_size"] === "object" ? member["group_size"] as OpenPayload : {};
    const groupMaximum = groupSize["maximum"];
    if (kind === "henchman" && typeof groupMaximum === "number" && rowInput.quantity > groupMaximum) {
      return rejected("limit_violated", `Groups of "${rowInput.profile_id}" hold at most ${groupMaximum} models.`);
    }
    const occurrence = (occurrences.get(rowInput.profile_id) ?? 0) + 1;
    occurrences.set(rowInput.profile_id, occurrence);
    const created = warriorFromProfile(profile, rowInput, itemName, occurrence);
    const bonuses = selectedWarbandVariant(knowledge, campaign.identity.band_id, campaign.identity.mercenary_variant)?.profile_bonuses?.[rowInput.profile_id] ?? {};
    const variantStats = Object.fromEntries(Object.entries(created.stats).map(([key, value]) => [key, value + (bonuses[key] ?? 0)]));
    const warrior = { ...created, stats: variantStats, name: uniqueWarriorName([...campaign.warriors, ...planned.map((row) => row.warrior)], created.name) };
    // Fixed equipment comes from the profile; listed equipment is purchased.
    const fixedIds = warrior.equipment.map((entry) => entry.item_id);
    const facts = profileFactsOf(knowledge, campaign.identity.band_id, rowInput.profile_id);
    for (const itemId of rowInput.equipment) {
      if (fixedIds.includes(itemId) || !facts) continue;
      const issue = equipmentIssueFor(
        knowledge,
        facts,
        itemId,
        campaign.identity.mercenary_variant ?? null,
      );
      if (issue && (issue.code === "equipment_not_permitted" || issue.code === "equipment_forbidden")) {
        return rejected("not_available", issue.message);
      }
    }
    const purchased = rowInput.equipment
      .filter((itemId: IdString) => !fixedIds.includes(itemId))
      .map((itemId: IdString) => {
        const item = knowledge.queryKnowledge({ id: { kind: "item_id", value: itemId } });
        const value =
          item.ok && typeof item.record.data["value"] === "number"
            ? (item.record.data["value"] as number)
            : 0;
        return { itemId, value };
      });
    const equippedEntries: EquipmentEntry[] = [
      ...warrior.equipment,
      ...purchased.map((entry: { readonly itemId: IdString; readonly value: number }) => ({
        item_id: entry.itemId,
        name: itemName(entry.itemId),
        quantity: rowInput.quantity,
        acquisition: "purchase" as const,
        unit_cost: entry.value,
      })),
    ];
    const built: Warrior = { ...warrior, equipment: equippedEntries };
    planned.push({ warrior: built, purchased });
  }

  // Starting characteristics must stay inside the published racial maximum; the
  // row is resolved by stable ids (the band's race groups and the catalogue's
  // explicit profile keys), never by the printed name. A profile the catalogue
  // leaves without a key stays explicitly unbounded here: the profile itself is
  // printed and legal, so the missing maximum is a KB report, not a rejection.
  const maximums = racialMaximumsOf(knowledge);
  for (const row of planned) {
    if (!row.warrior.profile_id) continue;
    const facts = profileFactsOf(knowledge, campaign.identity.band_id, row.warrior.profile_id);
    if (!facts) continue;
    const bound = racialMaximumResolutionFor(knowledge, campaign.identity.band_id, row.warrior.profile_id, maximums);
    for (const [stat, value] of Object.entries(row.warrior.stats)) {
      if (typeof value !== "number") continue;
      const printed = facts.characteristics[stat];
      const issue = characteristicBoundIssueFor({
        profile: facts,
        stat,
        value,
        row: bound.row,
        printed: typeof printed === "number" ? printed : null,
      });
      if (issue) return rejected("limit_violated", issue.message);
    }
  }

  // Limit checks on the would-be roster (Python formulas).
  const warriors = [...campaign.warriors, ...planned.map((p) => p.warrior)];
  for (const member of effectiveMembers) {
    const profileId = typeof member["profile_id"] === "string" ? member["profile_id"] : "";
    const maximum = member["maximum"];
    if (!profileId || typeof maximum !== "number") continue;
    const taken = warriors.filter((warrior) => warrior.profile_id === profileId).reduce((total, warrior) => total + (warrior.quantity ?? 1), 0);
    if (taken > maximum) return rejected("limit_reached", `Roster limit for "${profileId}" is ${maximum} models.`);
  }
  const memberTotal = warriors.reduce(
    (t, w) => (w.kind === "hireling" ? t : t + (w.quantity ?? 1)),
    0,
  );
  if (memberTotal > campaign.configuration.maximum_models) {
    return rejected(
      "limit_reached",
      `Warband limit is ${campaign.configuration.maximum_models} models; this composition would reach ${memberTotal}.`,
    );
  }
  const heroes = warriors.reduce((t, w) => (w.kind === "hero" ? t + (w.quantity ?? 1) : t), 0);
  if (heroes > campaign.configuration.hero_limit) {
    return rejected(
      "limit_reached",
      `Hero limit is ${campaign.configuration.hero_limit}; this composition would reach ${heroes}.`,
    );
  }
  const recruitment = warriors.reduce((t, w) => t + w.cost * (w.quantity ?? 1), 0);
  const purchasedCost = planned.reduce(
    (t, p) => t + p.purchased.reduce((s, entry) => s + entry.value * entryValueUnits(p.warrior), 0),
    0,
  );
  function entryValueUnits(warrior: Warrior): number {
    return warrior.quantity ?? 1;
  }
  const equipmentCost =
    campaign.inventory.reduce((t, item) => t + item.owned * (item.value ?? 0), 0) + purchasedCost;
  if (campaign.configuration.starting_gold - recruitment - equipmentCost < 0) {
    return rejected(
      "limit_violated",
      "Not enough gold in the starting treasury for this composition.",
    );
  }

  // Commit: new warriors + purchased equipment folded into inventory rows.
  const inventory = [...campaign.inventory];
  for (const p of planned) {
    for (const entry of p.purchased) {
      const existing = inventory.findIndex((item) => item.id === entry.itemId);
      const units = p.warrior.quantity ?? 1;
      if (existing >= 0) {
        const item = inventory[existing];
        inventory[existing] = { ...item, owned: item.owned + units, equipped: item.equipped + units };
      } else {
        const itemRecord = knowledge.queryKnowledge({
          id: { kind: "item_id", value: entry.itemId },
        });
        inventory.push({
          id: entry.itemId,
          name: itemRecord.ok
            ? ((itemRecord.record.names as Readonly<Record<string, string>>)["en"] ?? entry.itemId)
            : entry.itemId,
          category:
            itemRecord.ok && typeof itemRecord.record.data["kind"] === "string"
              ? (itemRecord.record.data["kind"] as string)
              : "Equipment",
          owned: units,
          equipped: units,
          stash: 0,
          value: entry.value,
        });
      }
    }
  }
  const nextCampaign: Campaign = { ...campaign, warriors, inventory };
  return { ok: true, state: { campaign: nextCampaign, view: document.view } };
}
