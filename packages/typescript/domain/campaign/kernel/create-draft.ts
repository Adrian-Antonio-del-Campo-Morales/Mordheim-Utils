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
  UseCaseResult,
  Warrior,
} from "./usecases";
import { rejected } from "./rejections";
import { memberCount } from "./document";

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
  const entries: EquipmentEntry[] = equipmentIds.map((itemId) => ({
    item_id: itemId,
    name: itemName(itemId),
    quantity: input.quantity,
    acquisition: "fixed",
    per_model: true,
  }));
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
    skills: [...inherent, ...startingSkills],
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
 * cheapest henchmen up to the minimum model count (Python
 * `_starter_warriors`). Rejects unknown bands and unusable rosters.
 */
export function createDraft(
  bandId: IdString,
  knowledge: KnowledgeReader,
  campaignName = "New Mordheim Campaign",
): UseCaseResult {
  const bandResult = knowledge.queryKnowledge({ id: { kind: "band_id", value: bandId } });
  if (!bandResult.ok) {
    return rejected("not_found", `Unknown warband id: ${bandId}.`);
  }
  const bandRecord = bandResult.record;
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

  const roster =
    bandRecord.data["roster"] && typeof bandRecord.data["roster"] === "object"
      ? (bandRecord.data["roster"] as OpenPayload)
      : {};
  const members = Array.isArray(roster["members"]) ? (roster["members"] as OpenPayload[]) : [];
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
    rows.push(
      warriorFromProfile(
        profile,
        {
          profile_id: profileId,
          kind: profile["type"] === "hero" ? "hero" : "henchman",
          quantity,
          equipment: [],
        },
        itemName,
        nextOccurrence(profileId),
      ),
    );
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
  const groupMax = (member: OpenPayload): number => {
    const gs = member["group_size"];
    if (gs && typeof gs === "object") {
      const raw = gs as OpenPayload;
      return typeof raw["maximum"] === "number" ? raw["maximum"] : 1;
    }
    return 1;
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
    .filter(({ profile }) => profile["type"] === "henchman")
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
    const perRowCap = Math.max(1, groupMax(member));
    const quantity = Math.min(needed, perRowCap);
    add(profile, quantity, profileId);
  }

  // 3. All-hero-optional bands still need at least one hero.
  if (!rows.some((row) => row.kind === "hero")) {
    const heroCandidates = membersWithProfiles
      .filter(({ profile, member }) => {
        if (profile["type"] !== "hero") return false;
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

  const collectionValue = bandRecord.data["collection"];
  const identity: CampaignIdentity = {
    campaign_name: campaignName,
    warband_name: `My ${bandRecord.names["en"] ?? bandId} Warband`,
    warband_type: bandRecord.names["en"] ?? bandId,
    band_id: bandId,
    mercenary_variant: null,
    ...(typeof collectionValue === "string" ? { collection: collectionValue as IdString } : {}),
  };
  const campaign: Campaign = {
    identity,
    configuration: {
      is_draft: true,
      starting_gold: rules.starting_gold,
      minimum_models: rules.minimum_models,
      maximum_models: rules.maximum_models,
      hero_limit: rules.hero_limit ?? 5,
    },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 0,
    warriors: rows,
    battles: [],
    states: [],
    post_battles: [],
    inventory: [],
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
    const occurrence = (occurrences.get(rowInput.profile_id) ?? 0) + 1;
    occurrences.set(rowInput.profile_id, occurrence);
    const warrior = warriorFromProfile(profile, rowInput, itemName, occurrence);
    // Fixed equipment comes from the profile; listed equipment is purchased.
    const fixedIds = warrior.equipment.map((entry) => entry.item_id);
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

  // Limit checks on the would-be roster (Python formulas).
  const warriors = [...campaign.warriors, ...planned.map((p) => p.warrior)];
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
