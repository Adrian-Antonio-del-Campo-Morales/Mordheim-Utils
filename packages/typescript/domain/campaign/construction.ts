/**
 * T09: construction and selection contracts for the Warband Manager Web.
 *
 * These are the shared entry points T10 (campaign) and T11 (interface) consume;
 * they are also the decision surface the automated checks exercise. Every rule
 * is enforced in the domain — the web interface may only *present* the
 * verdicts, never decide them.
 *
 * Sources of truth:
 * - construction facts come from the generated KB artefact through the frozen
 *   `KnowledgeReader` port (band roster, profile equipment/skill access,
 *   characteristic cells, campaign catalogues); no YAML ever reaches this
 *   module and no identity is ever resolved by display name;
 * - the two facts the artefact cannot carry — the runtime-scope profile
 *   exclusions and the bindings declared while `implemented != YES` — live in
 *   `construction-tables.json`, whose parity with
 *   `sources/knowledge/registry/{runtime-scope,bindings}.yaml` is gated by
 *   `tests/python/construction/test_construction_contract_tables.py`.
 *
 * Issue codes are stable: T10 and T11 branch on them, never on the message.
 *
 * Purity: no React, no DOM, no browser globals, no filesystem.
 */

import {
  warbandVariants,
  type WarbandVariant,
  type WarbandVariantRosterMember,
} from "./band-variants";
import type { KnowledgeReader, KnowledgeResult } from "./kernel/ports";
import type { Campaign, IdString, OpenPayload, Warrior } from "./kernel/state";
import TABLES from "./construction-tables.json";
import CLAUSES from "./construction-clauses.json";

/** Stable reason a construction choice is refused or left pending. */
export type ConstructionIssueCode =
  | "band_unknown"
  | "profile_unknown"
  | "profile_excluded_from_construction"
  | "roster_minimum_missing"
  | "roster_group_minimum_missing"
  | "equipment_not_permitted"
  | "equipment_forbidden"
  | "equipment_unknown_item"
  | "equipment_limit_exceeded"
  | "equipment_required_missing"
  | "skill_not_permitted"
  | "skill_pending_special_list"
  | "characteristic_bound_exceeded"
  | "characteristic_not_fixed"
  | "hiring_not_permitted"
  | "hiring_clause_unstructured"
  | "pending_combat_binding"
  | "variant_selection_required"
  | "variant_options_missing"
  | "variant_unknown_option"
  | "variant_consequence_unstructured"
  | "variant_gate_unpublished"
  | "variant_member_maximum_unpublished"
  | "profile_not_permitted_for_variant"
  | "animal_not_permitted"
  | "construction_clause_unstructured";

/** Task that owns closing a declared gap (`KB` = knowledge base follow-up). */
export type ConstructionOwner = "T10" | "T11" | "T13" | "KB";

/**
 * One construction verdict. `subject_ids` always carries the stable KB ids
 * involved so tests and T11 branch on ids, and `rule_id`/`binding_id` are
 * present exactly when the verdict comes from a declared KB clause.
 */
export interface ConstructionIssue {
  readonly code: ConstructionIssueCode;
  readonly subject_ids: readonly IdString[];
  readonly message: string;
  readonly rule_id?: IdString;
  readonly binding_id?: IdString;
  /** Owner of the gap when the issue is pending rather than a rejection. */
  readonly owner_task?: ConstructionOwner;
}

/**
 * Construction limits a band rule states over the whole equipment set of one
 * member (`profile.equipment-restrictions` parameters): how many missile
 * weapons it may carry, the item tag its own kit must include, and the printed
 * profiles that requirement does not bind.
 */
export interface BandEquipmentLimits {
  /** Band rule that states the limit, for traceability of the verdict. */
  readonly rule_id?: IdString;
  readonly max_missile_weapons?: number;
  readonly required_tag?: string;
  readonly exempt_profile_ids?: readonly IdString[];
}

/** Roster limits and slots declared by the band record. */
export interface RosterMemberFacts {
  readonly profile_id: IdString;
  readonly minimum: number | null;
  readonly maximum: number | null;
  readonly group_size: { readonly minimum: number | null; readonly maximum: number | null } | null;
}

export interface BandFacts {
  readonly band_id: IdString;
  readonly name: string;
  readonly collection: string | null;
  readonly rule_ids: readonly IdString[];
  readonly minimum_models: number | null;
  readonly maximum_models: number | null;
  readonly starting_gold: number | null;
  readonly members: readonly RosterMemberFacts[];
  /** Equipment list ids the band publishes, in stable order. */
  readonly equipment_lists: readonly IdString[];
  /**
   * Band-wide prohibition tokens (`profile.equipment-restrictions` on a
   * band rule): item ids, interpreted family tokens or item tags.
   */
  readonly equipment_forbids: readonly string[];
  /** Whole-set equipment limits, when a band rule publishes them. */
  readonly equipment_limits: BandEquipmentLimits | null;
  /** The KB demands choosing a warband variant before the warband is usable. */
  readonly requires_variant_selection: boolean;
  /** Dimensions of the published options (`background`, `bloodline`…), from their ids. */
  readonly variant_dimensions: readonly string[];
}

/** One bounded skill list a band rule grants one profile. */
export interface ProfileSkillList {
  readonly rule_id: IdString;
  readonly category: string;
  /** Printed membership of the list; empty while the KB publishes no members. */
  readonly skills: readonly IdString[];
}

/** One entry of the profile's declared equipment access. */
export interface EquipmentOffer {
  readonly item_id: IdString;
  readonly list_id?: string;
  readonly cost?: number;
  readonly notes?: string;
}

export interface ProfileFacts {
  readonly band_id: IdString;
  readonly profile_id: IdString;
  readonly name: string;
  readonly kind: "hero" | "henchman" | "other";
  /** The profile is an animal (`type: animal`), the family a band may forbid. */
  readonly is_animal: boolean;
  /** `null` when the row does not declare access (legacy rows / hand fakes). */
  readonly equipment_access: readonly EquipmentOffer[] | null;
  /** Equipment lists the row declares (`profiles.yaml` `equipment_lists`). */
  readonly equipment_lists: readonly IdString[];
  readonly fixed_equipment: readonly IdString[];
  readonly equipment_forbids: readonly string[];
  /** Tokens that arrived malformed in the source (reported, never invented). */
  readonly equipment_forbids_malformed: readonly string[];
  readonly equipment_restrictions: readonly string[];
  readonly skill_access: readonly string[];
  /** Bounded special-skill lists a band rule grants this profile. */
  readonly skill_lists: readonly ProfileSkillList[];
  readonly rule_ids: readonly IdString[];
  readonly inherent_rules: readonly IdString[];
  readonly combat_traits: OpenPayload;
  readonly characteristics: Readonly<Record<string, unknown>>;
  /** Bloodline option the profile belongs to (`profiles.yaml` `bloodline`). */
  readonly bloodline: string | null;
}

export interface ProfileExclusionTable {
  readonly band_id: string;
  readonly profile_id: string;
  readonly reason: string;
}

export interface PendingBindingTable {
  readonly rule_id: string;
  readonly band_id: string;
  readonly profile_id: string;
  readonly binding_id: string;
  readonly declared_scope: string;
  readonly owner_task: ConstructionOwner;
  readonly reason: string;
}

/** Profile exclusions published by `registry/runtime-scope.yaml`. */
export const PROFILE_EXCLUSIONS: readonly ProfileExclusionTable[] =
  TABLES.profile_exclusions as readonly ProfileExclusionTable[];

/** Bindings declared in the KB while `runtime.implemented != YES`. */
export const PENDING_BINDINGS: readonly PendingBindingTable[] =
  TABLES.pending_bindings as readonly PendingBindingTable[];

/** Characteristic display key → canonical racial-maximum key. */
const RACIAL_MAXIMUM_KEYS: Readonly<Record<string, string>> = {
  M: "movement",
  WS: "weapon_skill",
  BS: "ballistic_skill",
  S: "strength",
  T: "toughness",
  W: "wounds",
  I: "initiative",
  A: "attacks",
  Ld: "leadership",
};

function nonNegative(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function strings(values: unknown): string[] {
  return Array.isArray(values) ? values.filter((value): value is string => typeof value === "string") : [];
}

/** Stable band facts, or `null` when the id is unknown. */
export function bandFactsOf(reader: KnowledgeReader, bandId: IdString): BandFacts | null {
  const result: KnowledgeResult = reader.queryKnowledge({ id: { kind: "band_id", value: bandId } });
  if (!result.ok) return null;
  const data = result.record.data as OpenPayload;
  const roster = data["roster"] && typeof data["roster"] === "object" ? (data["roster"] as OpenPayload) : {};
  const members = Array.isArray(roster["members"]) ? (roster["members"] as OpenPayload[]) : [];
  return {
    band_id: bandId,
    name: typeof result.record.names["en"] === "string" ? (result.record.names["en"] as string) : bandId,
    collection: typeof data["collection"] === "string" ? (data["collection"] as string) : null,
    rule_ids: strings(data["rule_ids"]),
    // The option *ids* define the dimension; a display name never does.
    variant_dimensions: [
      ...new Set(
        warbandVariants(reader, bandId)
          .map((option) => variantDimensionOf(option.id)?.dimension ?? "")
          .filter((dimension) => dimension !== ""),
      ),
    ].sort(),
    requires_variant_selection: roster["requires_variant_selection"] === true,
    equipment_lists: [
      ...new Set(
        (Array.isArray(data["equipment_access"]) ? (data["equipment_access"] as OpenPayload[]) : [])
          .map((offer) => String(offer["list_id"] ?? ""))
          .filter((listId) => listId !== ""),
      ),
    ].sort(),
    equipment_forbids: strings(data["equipment_forbids"]),
    equipment_limits:
      data["equipment_limits"] && typeof data["equipment_limits"] === "object"
        ? (data["equipment_limits"] as BandEquipmentLimits)
        : null,
    minimum_models: nonNegative(roster["minimum_models"]),
    maximum_models: nonNegative(roster["maximum_models"]),
    starting_gold: nonNegative(roster["starting_gold"]),
    members: members
      .filter((member) => typeof member["profile_id"] === "string")
      .map((member) => {
        const group = member["group_size"] && typeof member["group_size"] === "object"
          ? (member["group_size"] as OpenPayload)
          : null;
        return {
          profile_id: member["profile_id"] as string,
          minimum: nonNegative(member["minimum"]),
          maximum: nonNegative(member["maximum"]),
          group_size: group
            ? { minimum: nonNegative(group["minimum"]), maximum: nonNegative(group["maximum"]) }
            : null,
        };
      }),
  };
}

/** Stable profile facts scoped to one band, or `null` when the id is unknown. */
export function profileFactsOf(
  reader: KnowledgeReader,
  bandId: IdString,
  profileId: IdString,
): ProfileFacts | null {
  const catalogue = reader as KnowledgeReader & {
    list?(kind: "profile"): readonly OpenPayload[];
  };
  let row: OpenPayload | null = null;
  const scoped = catalogue.list?.("profile").find(
    (profile) => profile["id"] === profileId && profile["band_id"] === bandId,
  );
  if (scoped) {
    row = scoped;
  } else {
    const result = reader.queryKnowledge({ id: { kind: "profile_id", value: profileId } });
    if (result.ok) {
      const data = result.record.data as OpenPayload;
      // Profiles are band-scoped: an unscoped hit from another band is not this profile.
      if (typeof data["band_id"] !== "string" || data["band_id"] === bandId) row = data;
    }
  }
  if (!row) return null;
  const forbids: string[] = [];
  const malformed: string[] = [];
  for (const token of strings(row["equipment_forbids"])) {
    const trimmed = token.trim();
    if (!trimmed) continue;
    if (trimmed.startsWith("[")) {
      // Generator defect (list-valued `forbids` stringified): report, never guess a list.
      malformed.push(trimmed);
      continue;
    }
    forbids.push(trimmed);
  }
  const access = Array.isArray(row["equipment_access"])
    ? (row["equipment_access"] as OpenPayload[]).map((offer) => ({
        item_id: String(offer["item_id"] ?? ""),
        ...(typeof offer["list_id"] === "string" ? { list_id: offer["list_id"] } : {}),
        ...(nonNegative(offer["cost"]) !== null ? { cost: nonNegative(offer["cost"]) as number } : {}),
        ...(typeof offer["notes"] === "string" ? { notes: offer["notes"] } : {}),
      })).filter((offer) => offer.item_id !== "")
    : null;
  return {
    band_id: bandId,
    profile_id: profileId,
    name: typeof row["name"] === "string" ? (row["name"] as string) : profileId,
    kind: row["type"] === "hero" ? "hero" : row["type"] === "henchman" ? "henchman" : "other",
    is_animal: row["type"] === "animal",
    equipment_access: access,
    equipment_lists: strings(row["equipment_lists"]),
    fixed_equipment: strings(row["fixed_equipment"]),
    equipment_forbids: forbids,
    equipment_forbids_malformed: malformed,
    equipment_restrictions: strings(row["equipment_restrictions"]),
    skill_access: strings(row["skill_access"]),
    skill_lists: (Array.isArray(row["skill_lists"]) ? (row["skill_lists"] as OpenPayload[]) : [])
      .map((list) => ({
        rule_id: String(list["rule_id"] ?? ""),
        category: String(list["category"] ?? ""),
        skills: strings(list["skills"]),
      }))
      .filter((list) => list.rule_id !== "" && list.category !== ""),
    rule_ids: strings(row["rule_ids"]),
    inherent_rules: strings(row["inherent_rules"]),
    bloodline:
      typeof row["bloodline"] === "string" && row["bloodline"].trim() !== ""
        ? row["bloodline"].trim()
        : null,
    combat_traits: row["combat_traits"] && typeof row["combat_traits"] === "object"
      ? (row["combat_traits"] as OpenPayload)
      : {},
    characteristics: row["characteristics"] && typeof row["characteristics"] === "object"
      ? (row["characteristics"] as OpenPayload)
      : {},
  };
}

/** Runtime-scope exclusion of one profile, or `null` when it is a normal profile. */
export function profileExclusionFor(
  bandId: IdString,
  profileId: IdString,
): ProfileExclusionTable | null {
  return (
    PROFILE_EXCLUSIONS.find(
      (entry) => entry.band_id === bandId && entry.profile_id === profileId,
    ) ?? null
  );
}

/** Mandatory warband-variant choice declared by the band record. */
export interface VariantRequirement {
  readonly required: boolean;
  readonly options: readonly WarbandVariant[];
}

/**
 * Whether the band record demands choosing a warband variant (a background or
 * bloodline) before the warband is committed, and which options the KB
 * publishes. A band that demands it without publishing options is a KB gap:
 * the contract reports it instead of defaulting the choice.
 */
export function variantRequirementOf(
  reader: KnowledgeReader,
  bandId: IdString,
): VariantRequirement {
  const result = reader.queryKnowledge({ id: { kind: "band_id", value: bandId } });
  if (!result.ok) return { required: false, options: [] };
  const roster = result.record.data["roster"];
  const required =
    !!roster &&
    typeof roster === "object" &&
    (roster as OpenPayload)["requires_variant_selection"] === true;
  return { required, options: required ? warbandVariants(reader, bandId) : [] };
}

/** Stable prefix and value of a published option id (`background.native`). */
export function variantDimensionOf(
  variantId: IdString,
): { readonly dimension: string; readonly value: string } | null {
  const [dimension, ...rest] = String(variantId ?? "").trim().toLowerCase().split(".");
  const value = rest.join(".");
  return dimension && value ? { dimension, value } : null;
}

/** Whether one published option opens a roster slot (`variant.roster_members`). */
export function variantOpens(option: WarbandVariant, profileId: IdString): boolean {
  return (option.roster_members ?? []).some((row) => row.profile_id === profileId);
}

/** The published slot row of one option, or `null` when the option does not open it. */
export function variantSlotOf(
  option: WarbandVariant,
  profileId: IdString,
): WarbandVariantRosterMember | null {
  return (option.roster_members ?? []).find((entry) => entry.profile_id === profileId) ?? null;
}

/** Printed bound the option publishes for a slot it opens, or `null` while absent. */
export function variantMaximumOf(option: WarbandVariant, profileId: IdString): number | null | undefined {
  const row = variantSlotOf(option, profileId);
  if (!row) return undefined;
  return row.maximum ?? null;
}

/**
 * Whether the published option carries any construction consequence at all: the
 * slots it opens, the lists it activates, or the effects the existing campaign
 * contract already consumes (rules, treasury, characteristic bonuses).
 */
export function variantPublishesConstruction(option: WarbandVariant): boolean {
  return (
    (option.roster_members ?? []).length > 0 ||
    (option.equipment_lists ?? []).length > 0 ||
    option.rule_ids.length > 0 ||
    option.starting_gold !== undefined ||
    option.profile_bonuses !== undefined
  );
}

/** One roster slot gated by the mandatory variant choice. */
export interface MemberVariantGate {
  readonly profile_id: IdString;
  /** Published options that open the slot; empty is a KB gap and is reported. */
  readonly option_ids: readonly IdString[];
}

/**
 * Roster slots gated by the mandatory variant choice. The KB marks a slot that
 * only a chosen variant opens with `maximum: 0`, and each published option
 * declares the slots it opens in its own `roster_members`; the contract reads
 * exactly those two published facts. A band that does not demand the choice
 * gates nothing: optional variants keep the behaviour they had.
 */
export function variantGatesOf(reader: KnowledgeReader, band: BandFacts): readonly MemberVariantGate[] {
  if (!band.requires_variant_selection) return [];
  const options = warbandVariants(reader, band.band_id);
  return band.members
    .filter((member) => member.maximum === 0)
    .map((member) => ({
      profile_id: member.profile_id,
      option_ids: options.filter((option) => variantOpens(option, member.profile_id)).map((option) => option.id),
    }));
}

/** Construction frame of a band under a published option, or without a choice. */
export interface VariantFrame {
  /** The selected option, or `null` while the choice is still open. */
  readonly variant_id: IdString | null;
  readonly dimension: string | null;
  readonly value: string | null;
  /** Members usable under the selection, with the limits the contract resolves. */
  readonly available: readonly RosterMemberFacts[];
  /** Declared members the selection forbids. */
  readonly removed_profiles: readonly IdString[];
  /** Profile the selection makes mandatory (the chosen Vampire is the leader). */
  readonly leader_profile: IdString | null;
  /** Equipment lists the selection activates (the background's lists). */
  readonly equipment_lists: readonly IdString[];
  /** Published option with no construction contract (reported, never applied). */
  readonly unstructured: boolean;
}

/**
 * Resolves the construction consequence of the published option over one band:
 *
 * - the slots the option opens become available, with the bound the option
 *   declares (`maximum: 1` for the Vampire the printed `band--choose-bloodline`
 *   makes the single leader) and no bound while the source does not fix one;
 * - the slots the option does not open stay locked (their published slot is
 *   `0/0`, the KB marker for a variant-locked member);
 * - the option activates the equipment lists it declares;
 * - no selection leaves every gated member locked, which is exactly the
 *   published `0/0` state a `requires_variant_selection` band starts in.
 */
export function variantFrameOf(
  reader: KnowledgeReader,
  band: BandFacts,
  variantId: IdString | null | undefined,
): VariantFrame {
  const selected = String(variantId ?? "").trim().toLowerCase();
  const dimension = variantDimensionOf(selected);
  const chosen =
    selected === ""
      ? null
      : warbandVariants(reader, band.band_id).find((option) => option.id === selected) ?? null;
  const gates = new Set(variantGatesOf(reader, band).map((gate) => gate.profile_id));
  const available: RosterMemberFacts[] = [];
  const removed: IdString[] = [];
  let leader: IdString | null = null;
  for (const member of band.members) {
    if (!gates.has(member.profile_id)) {
      available.push(member);
      continue;
    }
    const slot = chosen ? variantSlotOf(chosen, member.profile_id) : null;
    if (!slot) {
      removed.push(member.profile_id);
      continue;
    }
    const maximum = slot.maximum ?? null;
    available.push({ ...member, minimum: slot.minimum ?? member.minimum, maximum });
    if (maximum === 1) leader = member.profile_id;
  }
  return {
    variant_id: selected === "" ? null : selected,
    dimension: dimension?.dimension ?? null,
    value: dimension?.value ?? null,
    available,
    removed_profiles: removed,
    leader_profile: leader,
    equipment_lists: chosen?.equipment_lists ?? [],
    unstructured: chosen !== null && !variantPublishesConstruction(chosen),
  };
}

/**
 * Equipment lists the selected option activates for one profile: the lists the
 * option declares that the profile itself declares. A profile that declares
 * none of them keeps no activated list, which is how the weaponless Black Hounds
 * and Jackals stay closed.
 */
export function variantActiveListsOf(
  reader: KnowledgeReader,
  band: BandFacts,
  profile: ProfileFacts,
  variantId: IdString | null | undefined,
): readonly IdString[] {
  const frame = variantFrameOf(reader, band, variantId);
  if (frame.equipment_lists.length === 0) return [];
  return frame.equipment_lists.filter((listId) => profile.equipment_lists.includes(listId));
}

/** Every list any published option of the band activates, the choice's domain. */
export function variantGatedListsOf(reader: KnowledgeReader, band: BandFacts): ReadonlySet<IdString> {
  return new Set(
    warbandVariants(reader, band.band_id).flatMap((option) => option.equipment_lists ?? []),
  );
}


/**
 * Roster slots the mandatory choice gates, resolved against the published
 * options: a slot no option opens, and an opened slot whose printed bound the
 * source does not fix, are reported to the KB instead of being guessed.
 */
function variantGateIssues(reader: KnowledgeReader, bandId: IdString): ConstructionIssue[] {
  const band = bandFactsOf(reader, bandId);
  if (!band) return [];
  const issues: ConstructionIssue[] = [];
  for (const gate of variantGatesOf(reader, band)) {
    if (gate.option_ids.length === 0) {
      issues.push({
        code: "variant_gate_unpublished",
        subject_ids: [bandId, gate.profile_id],
        owner_task: "KB",
        message: `"${gate.profile_id}" is locked to the warband variant choice of "${bandId}", but no published option opens it.`,
      });
    }
  }
  for (const option of warbandVariants(reader, bandId)) {
    for (const row of option.roster_members ?? []) {
      if (row.maximum === undefined || row.maximum === null) {
        issues.push({
          code: "variant_member_maximum_unpublished",
          subject_ids: [bandId, option.id, row.profile_id],
          owner_task: "KB",
          message: `Option "${option.id}" of "${bandId}" opens "${row.profile_id}" without a published maximum; the slot is bounded by the warband size only.`,
        });
      }
    }
  }
  return issues;
}

/**
 * Verdict of the mandatory variant choice: an unknown option is rejected, a
 * published option without a construction contract is reported to the KB, and
 * a demanded choice is required before the warband is usable.
 */
function variantSelectionIssues(
  reader: KnowledgeReader,
  campaign: Campaign,
): ConstructionIssue[] {
  const bandId = campaign.identity.band_id;
  const requirement = variantRequirementOf(reader, bandId);
  const options = requirement.options.length > 0 ? requirement.options : warbandVariants(reader, bandId);
  const selected = String(campaign.identity.mercenary_variant ?? "").trim().toLowerCase();
  const chosen = options.find((option) => option.id === selected) ?? null;
  if (selected !== "" && chosen === null) {
    return [
      {
        code: "variant_unknown_option",
        subject_ids: [bandId, selected],
        message: `"${selected}" is not a published warband variant of "${bandId}".`,
      },
    ];
  }
  // An option is structured when the contract can apply at least one published
  // consequence: the slots it opens, the lists it activates, or the effects the
  // existing campaign contract already consumes. Anything else is reported to
  // the KB instead of being applied silently.
  if (chosen && !variantPublishesConstruction(chosen)) {
    return [
      {
        code: "variant_consequence_unstructured",
        subject_ids: [bandId, chosen.id],
        owner_task: "KB",
        message: `"${chosen.id}" is published as a warband variant of "${bandId}" without a construction contract; its effect is reported, not applied.`,
      },
    ];
  }
  const gateReports = variantGateIssues(reader, bandId);
  if (!requirement.required) return gateReports;
  if (selected !== "" && chosen) return gateReports;
  if (options.length === 0) {
    return [
      {
        code: "variant_options_missing",
        subject_ids: [bandId],
        message: `"${bandId}" requires choosing a warband variant, but the knowledge base publishes no variant options for it.`,
        owner_task: "KB",
      },
    ];
  }
  return [
    {
      code: "variant_selection_required",
      subject_ids: [bandId, ...options.map((option) => option.id)],
      message: `"${bandId}" requires choosing one warband variant to commit (${options.map((option) => option.id).join(", ")}).`,
    },
  ];
}

/** Bindings the KB declares while the executable contract does not exist yet. */
export function pendingBindingsFor(profile: ProfileFacts): readonly PendingBindingTable[] {
  return PENDING_BINDINGS.filter(
    (entry) =>
      profile.rule_ids.includes(entry.rule_id) ||
      profile.inherent_rules.includes(entry.rule_id),
  );
}

/** Contract accepted by T09, with the mechanism family it closes. */
export interface OpenClauseTable {
  readonly rule_id: string;
  readonly band_id: string;
  readonly mechanism: string;
  readonly scope: "equipment" | "roster" | "skills" | "characteristics" | "hiring";
  readonly owner_task: ConstructionOwner;
  readonly reason: string;
}

export interface TransferTable {
  readonly effect_id: string;
  readonly owner: string;
  readonly mechanism: string;
  readonly to_task: "T10" | "T13";
  readonly reason: string;
}

/**
 * Clauses owned by T09 whose KB record declares no executable structure: the
 * construction contract reports them instead of inventing a decision.
 */
export const OPEN_CLAUSES: readonly OpenClauseTable[] =
  CLAUSES.open_clauses as readonly OpenClauseTable[];

/** T09 obligations whose subsystem belongs to T10/T13; declared, never re-routed. */
export const TRANSFERS: readonly TransferTable[] = CLAUSES.transfers as readonly TransferTable[];

/**
 * Open construction clauses of a band (`profile === null`) or the clauses that
 * one profile adds on top of the band-wide ones.
 */
export function openClausesOf(
  band: BandFacts,
  profile: ProfileFacts | null,
): readonly OpenClauseTable[] {
  return OPEN_CLAUSES.filter((clause) => {
    if (clause.band_id !== band.band_id) return false;
    if (profile === null) return band.rule_ids.includes(clause.rule_id);
    return (
      profile.rule_ids.includes(clause.rule_id) || profile.inherent_rules.includes(clause.rule_id)
    );
  });
}

/** Canonical facts of a KB item row, when the reader exposes it. */
export function itemFactsOf(
  reader: KnowledgeReader,
  itemId: IdString,
): { readonly kind: string; readonly mechanic_id: string | null; readonly tags: readonly string[] } | null {
  const result = reader.queryKnowledge({ id: { kind: "item_id", value: itemId } });
  if (!result.ok) return null;
  const data = result.record.data as OpenPayload;
  const kind = data["kind"];
  if (typeof kind !== "string") return null;
  return {
    kind,
    mechanic_id: typeof data["mechanic_id"] === "string" ? (data["mechanic_id"] as string) : null,
    tags: strings(data["tags"]),
  };
}

/**
 * Closed item-tag vocabulary of `catalog-items.yaml.schema.json`: the families
 * the printed rules reason about as a set. A prohibition token resolves through
 * these tags, so no band keeps its own list of item ids. The contract gate
 * `tests/python/construction/test_construction_contract_tables.py` asserts this
 * list and the schema enum stay identical.
 */
export const EQUIPMENT_TAG_VOCABULARY: readonly string[] = [
  "animal",
  "blackpowder",
  "bow",
  "crossbow",
  "poison",
];

/** Item kinds the `armour` prohibition token covers (body armour + defences). */
const ARMOUR_KINDS: readonly string[] = ["armour", "shield-or-defence"];

/**
 * Mechanics the `heavy-armour` prohibition token covers; the promoted item row
 * carries the canonical `mechanic_id`, so the token resolves by id, never by name.
 */
const HEAVY_ARMOUR_MECHANICS: readonly string[] = [
  "armour.heavy-armour",
  "armour.gromril-armour",
  "armour.ithilmar-armour",
  "armour.plate-armour",
];

/** Tokens the contract interprets; anything else is reported, never guessed. */
const INTERPRETED_TOKENS: readonly string[] = [
  "armour",
  "heavy-armour",
  "ranged-weapons",
  ...EQUIPMENT_TAG_VOCABULARY,
];

/** Whether one forbids token designates this item, by id, mechanic or tag. */
function tokenForbids(
  token: string,
  itemId: IdString,
  item: { readonly kind: string; readonly mechanic_id: string | null; readonly tags: readonly string[] } | null,
): boolean {
  if (token === itemId || token === item?.mechanic_id) return true;
  if (item === null) return false;
  if (EQUIPMENT_TAG_VOCABULARY.includes(token)) return item.tags.includes(token);
  if (token === "armour") return ARMOUR_KINDS.includes(item.kind);
  if (token === "heavy-armour") {
    return item.mechanic_id !== null && HEAVY_ARMOUR_MECHANICS.includes(item.mechanic_id);
  }
  return token === "ranged-weapons" && item.kind === "ranged-weapon";
}

/**
 * Equipment verdict for one profile, from `equipment_access` plus the KB's
 * `profile.equipment-restrictions` prohibition tokens, plus the lists the
 * selected background variant activates. `null` means the choice is permitted.
 *
 * A profile row that does not declare `equipment_access` cannot be filtered
 * (legacy rows and hand-built fakes); rows that declare it are enforced, empty
 * included — that is how a vehicle or a creature with no purchasable list is
 * kept from silently accepting any item.
 */
export function equipmentIssueFor(
  reader: KnowledgeReader,
  profile: ProfileFacts,
  itemId: IdString,
  variantId: IdString | null = null,
): ConstructionIssue | null {
  const subject = [profile.band_id, profile.profile_id, itemId];
  if (profile.fixed_equipment.includes(itemId)) return null;
  const band = bandFactsOf(reader, profile.band_id);
  const activeLists = band ? variantActiveListsOf(reader, band, profile, variantId) : [];
  // Lists an option of the band activates are resolved by the choice: until an
  // option is selected none of them is assigned, so a profile that declares a
  // candidate list cannot buy from it yet (the printed "Use only the Undead
  // Equipment List assigned by the selected Foreign or Native background").
  const gatedLists = band ? variantGatedListsOf(reader, band) : new Set<IdString>();
  const offers = (profile.equipment_access ?? []).filter(
    (offer) =>
      offer.list_id === undefined ||
      !gatedLists.has(offer.list_id) ||
      activeLists.includes(offer.list_id),
  );
  const declaredAccess = profile.equipment_access !== null;
  const offered = declaredAccess && offers.some((offer) => offer.item_id === itemId);
  if (declaredAccess && !offered) {
    return {
      code: "equipment_not_permitted",
      subject_ids: subject,
      message: `"${itemId}" is not on any equipment list of ${profile.band_id}/${profile.profile_id}.`,
    };
  }
  const item = itemFactsOf(reader, itemId);
  const bandForbids = band ? band.equipment_forbids : [];
  for (const token of [...profile.equipment_forbids, ...bandForbids]) {
    if (tokenForbids(token, itemId, item)) {
      return {
        code: "equipment_forbidden",
        subject_ids: subject,
        message: `"${token}" is forbidden for ${profile.band_id}/${profile.profile_id}.`,
      };
    }
  }
  const unknownToken = [...profile.equipment_forbids, ...bandForbids].find(
    (token) =>
      !INTERPRETED_TOKENS.includes(token) &&
      token !== itemId &&
      !token.startsWith("armour.") &&
      !token.startsWith("defence.") &&
      !token.startsWith("weapon."),
  );
  if (unknownToken) {
    return {
      code: "construction_clause_unstructured",
      subject_ids: subject,
      rule_id: unknownToken,
      owner_task: "KB",
      message: `The prohibition token "${unknownToken}" of ${profile.band_id}/${profile.profile_id} has no construction contract; the choice is reported, not silently allowed.`,
    };
  }
  if (item === null && offered) {
    // The list offers an id the artefact publishes no row for (KB `out-of-scope`
    // kinds): report it — the choice stays legal, the record is the gap.
    return {
      code: "equipment_unknown_item",
      subject_ids: subject,
      message: `"${itemId}" is offered by ${profile.band_id}/${profile.profile_id} but has no item record in the KB artefact.`,
      owner_task: "KB",
    };
  }
  return null;
}

/** One catalogue skill, as construction sees it. */
export interface SkillFacts {
  readonly id: IdString;
  readonly category: string;
  readonly kind: string;
}

/** Canonical skill facts by stable id, or `null` when the skill is unknown. */
export function skillFactsOf(reader: KnowledgeReader, skillId: IdString): SkillFacts | null {
  const result = reader.queryKnowledge({ id: { kind: "skill_id", value: skillId } });
  if (!result.ok) return null;
  const data = result.record.data as OpenPayload;
  return {
    id: skillId,
    category: typeof data["category"] === "string" ? (data["category"] as string) : "",
    kind: typeof data["kind"] === "string" ? (data["kind"] as string) : "general",
  };
}

/**
 * Skill-selection verdict from the profile's declared access.
 *
 * - a category outside a non-empty `skill_access` is rejected;
 * - `special` access is accepted *and* reported as pending: the printed member
 *   list of each band special-skill list is prose-only in the KB, so the
 *   contract must not present the whole special catalogue as legal;
 * - an empty `skill_access` declares nothing and is not filtered here (the
 *   campaign workflows keep their documented convention).
 */
export function skillIssueFor(profile: ProfileFacts, skill: SkillFacts): ConstructionIssue | null {
  const subject = [profile.band_id, profile.profile_id, skill.id];
  if (profile.skill_access.length === 0) return null;
  if (!profile.skill_access.includes(skill.category)) {
    return {
      code: "skill_not_permitted",
      subject_ids: subject,
      message: `"${skill.id}" (${skill.category}) is outside the skill access of ${profile.band_id}/${profile.profile_id}.`,
    };
  }
  if (skill.category === "special") {
    const lists = profile.skill_lists.filter((list) => list.category === "special");
    if (lists.length === 0) {
      return {
        code: "skill_pending_special_list",
        subject_ids: subject,
        message: `"${skill.id}" belongs to a band special-skill list whose members are prose-only in the KB; the list rule is not enforced yet.`,
        owner_task: "KB",
      };
    }
    // The band publishes the printed membership: only those skills are legal, and
    // a skill of the special catalogue outside them is rejected, never allowed.
    if (!lists.some((list) => list.skills.includes(skill.id))) {
      return {
        code: "skill_not_permitted",
        subject_ids: subject,
        rule_id: lists[0]?.rule_id,
        message: `"${skill.id}" is not on the published special-skill list of ${profile.band_id}/${profile.profile_id} (${lists.map((list) => list.rule_id).join(", ")}).`,
      };
    }
  }
  return null;
}

/**
 * Whole-set equipment verdict of one member.
 *
 * A band rule can state a limit over the equipment a member carries at once
 * (`profile.equipment-restrictions` parameters): how many missile weapons, and
 * which item family the kit must include. Both are decided by the complete set,
 * so the contract evaluates the member's equipment as a whole and cannot be
 * satisfied or violated by one item in isolation. `exempt_profile_ids` carries
 * the printed exceptions (`crossbow_pistol`-style errata stay in the catalogue).
 */
export function memberEquipmentIssuesFor(
  reader: KnowledgeReader,
  profile: ProfileFacts,
  itemIds: readonly IdString[],
): readonly ConstructionIssue[] {
  const band = bandFactsOf(reader, profile.band_id);
  const limits = band?.equipment_limits ?? null;
  if (!limits || (limits.exempt_profile_ids ?? []).includes(profile.profile_id)) return [];
  const subject = [profile.band_id, profile.profile_id];
  const facts = itemIds.map((itemId) => ({ itemId, item: itemFactsOf(reader, itemId) }));
  const issues: ConstructionIssue[] = [];
  const maximum = limits.max_missile_weapons;
  if (typeof maximum === "number") {
    const carried = facts.filter((entry) => entry.item?.kind === "ranged-weapon");
    if (carried.length > maximum) {
      issues.push({
        code: "equipment_limit_exceeded",
        subject_ids: [...subject, ...carried.map((entry) => entry.itemId)],
        ...(limits.rule_id ? { rule_id: limits.rule_id } : {}),
        message: `${profile.band_id}/${profile.profile_id} carries ${carried.length} missile weapons; the band allows ${maximum}.`,
      });
    }
  }
  const required = limits.required_tag;
  if (required && required.trim() !== "") {
    const satisfied = facts.some((entry) => entry.item?.tags.includes(required));
    if (!satisfied) {
      issues.push({
        code: "equipment_required_missing",
        subject_ids: subject,
        ...(limits.rule_id ? { rule_id: limits.rule_id } : {}),
        message: `The equipment of ${profile.band_id}/${profile.profile_id} includes no "${required}": the band compiles the kit from that family only.`,
      });
    }
  }
  return issues;
}

/** One `campaign.racial_maximums` row. */
export interface RacialMaximumFacts {
  readonly id: string;
  readonly profile_key: string;
  readonly characteristics: Readonly<Record<string, number>>;
}

/** Key used to match a profile against the racial-maximum table. */
export function racialMaximumKey(value: string): string {
  return value.trim().toLocaleLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_+|_+$/g, "");
}

/** Every racial-maximum row the artefact publishes, when the reader lists them. */
export function racialMaximumsOf(reader: KnowledgeReader): readonly RacialMaximumFacts[] {
  const listing = reader as KnowledgeReader & {
    list?(kind: "racial_maximum"): readonly OpenPayload[];
  };
  return (listing.list?.("racial_maximum") ?? []).flatMap((row) => {
    const id = typeof row["id"] === "string" ? (row["id"] as string) : "";
    const profileKey = typeof row["profile"] === "string" ? (row["profile"] as string) : "";
    const characteristics = row["characteristics"];
    if (!id || !profileKey || !characteristics || typeof characteristics !== "object") return [];
    const bounds: Record<string, number> = {};
    for (const [key, value] of Object.entries(characteristics as OpenPayload)) {
      if (typeof value === "number") bounds[key] = value;
    }
    return [{ id, profile_key: profileKey, characteristics: bounds }];
  });
}

/** Racial-maximum row that governs one profile, or `null` when it is exempt. */
export function racialMaximumFor(
  profile: ProfileFacts,
  rows: readonly RacialMaximumFacts[],
): RacialMaximumFacts | null {
  const keys = new Set([racialMaximumKey(profile.name), racialMaximumKey(profile.profile_id)]);
  return rows.find((row) => keys.has(racialMaximumKey(row.profile_key))) ?? null;
}

/**
 * Characteristic verdict for an explicit value: a bound the profile exceeds is
 * rejected; a bound the profile does not have leaves it exempt.
 */
export function characteristicBoundIssueFor(args: {
  readonly profile: ProfileFacts;
  readonly stat: string;
  readonly value: number;
  readonly rows: readonly RacialMaximumFacts[];
}): ConstructionIssue | null {
  const row = racialMaximumFor(args.profile, args.rows);
  const key = RACIAL_MAXIMUM_KEYS[args.stat];
  if (!row || !key) return null;
  const bound = row.characteristics[key];
  if (typeof bound !== "number" || args.value <= bound) return null;
  return {
    code: "characteristic_bound_exceeded",
    subject_ids: [args.profile.band_id, args.profile.profile_id, args.stat],
    rule_id: row.id,
    message: `${args.stat} ${args.value} exceeds the racial maximum ${bound} of ${row.profile_key}.`,
  };
}

/**
 * Printed characteristics that are not fixed numbers (`2D6`, `D6`, blank).
 * They are pending contracts, not construction errors: the member stays legal,
 * the roll or substitution belongs to the battle/campaign layer.
 */
export function characteristicIssuesOf(profile: ProfileFacts): readonly ConstructionIssue[] {
  const issues: ConstructionIssue[] = [];
  for (const [stat, value] of Object.entries(profile.characteristics)) {
    if (typeof value === "number") continue;
    const printed = value === null || value === undefined ? "blank" : String(value);
    issues.push({
      code: "characteristic_not_fixed",
      subject_ids: [profile.band_id, profile.profile_id, stat],
      message: `${stat} of ${profile.band_id}/${profile.profile_id} is not a fixed value in the source (${printed}); the substitution/roll is not part of construction.`,
    });
  }
  return issues;
}

/** Roster membership of one warrior row. */
function quantityOf(warrior: Warrior): number {
  return typeof warrior.quantity === "number" && warrior.quantity > 0 ? warrior.quantity : 1;
}

/**
 * Roster-composition verdicts for a campaign: excluded profiles, required
 * member minimums, per-group minimums and unknown profiles — all read from the
 * band record, none from display names.
 */
export function rosterIssuesOf(reader: KnowledgeReader, campaign: Campaign): readonly ConstructionIssue[] {
  const band = bandFactsOf(reader, campaign.identity.band_id);
  if (!band) {
    return [
      {
        code: "band_unknown",
        subject_ids: [campaign.identity.band_id],
        message: `Unknown warband id "${campaign.identity.band_id}".`,
      },
    ];
  }
  const issues: ConstructionIssue[] = [...variantSelectionIssues(reader, campaign)];
  const frame = variantFrameOf(reader, band, campaign.identity.mercenary_variant);
  const members = new Map(band.members.map((member) => [member.profile_id, member]));
  const removed = new Set(frame.removed_profiles);
  for (const warrior of campaign.warriors) {
    if (warrior.kind === "hireling") continue;
    const profileId = warrior.profile_id;
    if (!profileId) continue;
    const exclusion = profileExclusionFor(band.band_id, profileId);
    if (exclusion) {
      issues.push({
        code: "profile_excluded_from_construction",
        subject_ids: [band.band_id, profileId],
        message: `${profileId} is outside the warband roster as a fighter: ${exclusion.reason}`,
        owner_task: "T13",
      });
      continue;
    }
    if (band.equipment_forbids.includes("animal")) {
      const fact = profileFactsOf(reader, band.band_id, profileId);
      if (fact?.is_animal) {
        issues.push({
          code: "animal_not_permitted",
          subject_ids: [band.band_id, profileId],
          message: `"${band.band_id}" may not field animals: "${profileId}" is an animal profile.`,
        });
      }
    }
    if (!members.has(profileId)) {
      issues.push({
        code: "profile_unknown",
        subject_ids: [band.band_id, profileId],
        message: `Profile "${profileId}" is not on the roster of "${band.band_id}".`,
      });
      continue;
    }
    if (removed.has(profileId) && frame.variant_id) {
      issues.push({
        code: "profile_not_permitted_for_variant",
        subject_ids: [band.band_id, profileId, frame.variant_id],
        message: `"${profileId}" is not available under the selected warband variant "${frame.variant_id}" of "${band.band_id}".`,
      });
    }
  }
  for (const member of frame.available) {
    const taken = campaign.warriors
      .filter((warrior) => warrior.profile_id === member.profile_id && warrior.kind !== "hireling")
      .reduce((total, warrior) => total + quantityOf(warrior), 0);
    if (member.minimum !== null && member.minimum > 0 && taken < member.minimum) {
      issues.push({
        code: "roster_minimum_missing",
        subject_ids: [band.band_id, member.profile_id],
        message: `"${band.band_id}" requires at least ${member.minimum} ${member.profile_id} (currently ${taken}).`,
      });
    }
    const groupMinimum = member.group_size?.minimum ?? null;
    if (groupMinimum === null || groupMinimum <= 1) continue;
    for (const warrior of campaign.warriors.filter(
      (row) => row.profile_id === member.profile_id && row.kind === "henchman",
    )) {
      if (quantityOf(warrior) < groupMinimum) {
        issues.push({
          code: "roster_group_minimum_missing",
          subject_ids: [band.band_id, member.profile_id, warrior.id],
          message: `A group of "${member.profile_id}" holds at least ${groupMinimum} models; "${warrior.id}" holds ${quantityOf(warrior)}.`,
        });
      }
    }
  }
  return issues;
}

/** Static hiring verdict from the campaign catalogue. */
export interface HiringDecision {
  readonly hireling_id: IdString;
  readonly kind: "allowed" | "rejected" | "unstructured";
  /** `static` = simple lists, `expression` = boolean predicate, `band-clause` = the band's own printed narrowing, `dynamic` = profile rules only. */
  readonly clause: "static" | "expression" | "band-clause" | "dynamic" | "none";
  /** Band rule the clause belongs to, when the verdict came from a band clause. */
  readonly rule_id?: IdString;
  readonly reason: string;
  readonly issue?: ConstructionIssue;
}

interface EligibilityLists {
  readonly allow_groups: readonly string[];
  readonly forbid_groups: readonly string[];
  readonly allow_band_ids: readonly string[];
  readonly forbid_band_ids: readonly string[];
  readonly note?: string;
  readonly expression?: OpenPayload;
}

/** Groups the band belongs to, from `campaign.warband_groups`. */
export function bandGroupsOf(reader: KnowledgeReader, bandId: IdString): readonly string[] {
  const listing = reader as KnowledgeReader & {
    campaignRows?(section: string): readonly OpenPayload[];
  };
  const rows = listing.campaignRows?.("warband_groups") ?? [];
  return rows
    .filter((row) => strings(row["band_ids"]).includes(bandId))
    .map((row) => String(row["id"] ?? ""))
    .filter((id) => id !== "");
}

/** One `campaign.hireling.*` catalogue row, when the reader exposes it. */
export function hirelingCatalogueRowOf(
  reader: KnowledgeReader,
  hirelingId: IdString,
): EligibilityLists | null {
  const sectionReader = reader as KnowledgeReader & {
    campaignSection?(section: string): Readonly<Record<string, unknown>>;
  };
  const section = sectionReader.campaignSection?.("hired-swords-and-dramatis");
  if (!section) return null;
  const rowId = `campaign.${hirelingId}`;
  for (const key of ["hired_swords", "dramatis_personae"] as const) {
    const rows = Array.isArray(section[key]) ? (section[key] as OpenPayload[]) : [];
    const row = rows.find((candidate) => candidate["id"] === rowId);
    if (!row) continue;
    const eligibility = row["eligibility"] && typeof row["eligibility"] === "object"
      ? (row["eligibility"] as OpenPayload)
      : {};
    return {
      allow_groups: strings(eligibility["allow_groups"]),
      forbid_groups: strings(eligibility["forbid_groups"]),
      allow_band_ids: strings(eligibility["allow_band_ids"]),
      forbid_band_ids: strings(eligibility["forbid_band_ids"]),
      ...(typeof eligibility["note"] === "string" ? { note: eligibility["note"] } : {}),
      ...(eligibility["expression"] && typeof eligibility["expression"] === "object"
        ? { expression: eligibility["expression"] as OpenPayload }
        : {}),
    };
  }
  return null;
}

/** Evaluate one `eligibility.expression` node against the band's groups. */
function expressionMatches(node: OpenPayload, bandId: IdString, groups: readonly string[]): boolean {
  if (Array.isArray(node["any_of"])) {
    return (node["any_of"] as OpenPayload[]).some((child) => expressionMatches(child, bandId, groups));
  }
  if (Array.isArray(node["all_of"])) {
    return (node["all_of"] as OpenPayload[]).every((child) => expressionMatches(child, bandId, groups));
  }
  if (node["not"] && typeof node["not"] === "object") {
    return !expressionMatches(node["not"] as OpenPayload, bandId, groups);
  }
  if (typeof node["band_id"] === "string") return node["band_id"] === bandId;
  if (typeof node["group_id"] === "string") return groups.includes(node["group_id"]);
  return false;
}

/** One band-side clause narrowing the hire set of a warband. */
export interface BandHiringClause {
  readonly rule_id: IdString;
  readonly band_id: IdString;
  /** Hireling traits the band may not hire (`catalog/hirelings/traits.yaml`). */
  readonly exclude_traits: readonly string[];
  /** Item tags the band's Hired Swords may not use (`catalog/items` tags). */
  readonly exclude_item_tags: readonly string[];
  readonly note?: string;
}

/**
 * Band-side hiring clauses published by the campaign catalogue, in stable
 * order. The clause belongs to a band rule and excludes by stable trait and
 * item-tag ids, so a reader never keeps its own table of hireling ids.
 */
export function bandHiringClausesOf(reader: KnowledgeReader, bandId: IdString): readonly BandHiringClause[] {
  const sectionReader = reader as KnowledgeReader & {
    campaignSection?(section: string): Readonly<Record<string, unknown>>;
  };
  const section = sectionReader.campaignSection?.("hired-swords-and-dramatis");
  const rows = section && Array.isArray(section["band_hiring_clauses"])
    ? (section["band_hiring_clauses"] as OpenPayload[])
    : [];
  return rows
    .filter((row) => row["band_id"] === bandId && typeof row["rule_id"] === "string")
    .map((row) => ({
      rule_id: String(row["rule_id"]),
      band_id: bandId,
      exclude_traits: strings(row["exclude_traits"]),
      exclude_item_tags: strings(row["exclude_item_tags"]),
      ...(typeof row["note"] === "string" ? { note: row["note"] } : {}),
    }));
}

/** Traits the catalogue publishes for one Hired Sword or Dramatis Personae. */
export function hirelingTraitsOf(reader: KnowledgeReader, hirelingId: IdString): readonly string[] {
  const sectionReader = reader as KnowledgeReader & {
    campaignSection?(section: string): Readonly<Record<string, unknown>>;
  };
  const table = sectionReader.campaignSection?.("hirelings")?.["traits"];
  if (!table || typeof table !== "object") return [];
  return strings((table as Record<string, unknown>)[hirelingId]);
}

/**
 * Every item the catalogue publishes as part of one hireling's kit: the fixed
 * equipment, the optional purchases and every option of its choice blocks.
 * The hiring clause reads these through the catalogue, so a band that may not
 * hire a Black Powder Hired Sword never keeps its own list of hireling ids.
 */
export function hirelingKitItemsOf(reader: KnowledgeReader, hirelingId: IdString): readonly IdString[] {
  const sectionReader = reader as KnowledgeReader & {
    campaignSection?(section: string): Readonly<Record<string, unknown>>;
  };
  const profiles = sectionReader.campaignSection?.("hirelings")?.["profiles"];
  if (!Array.isArray(profiles)) return [];
  const profile = (profiles as OpenPayload[]).find((candidate) => candidate["id"] === hirelingId);
  const equipment = profile?.["equipment"];
  if (!equipment || typeof equipment !== "object") return [];
  const bag = equipment as OpenPayload;
  const items = new Set<IdString>();
  for (const key of ["fixed_items", "optional_items"] as const) {
    const rows = Array.isArray(bag[key]) ? (bag[key] as OpenPayload[]) : [];
    for (const row of rows) {
      if (typeof row["item_id"] === "string") items.add(row["item_id"] as IdString);
    }
  }
  const choices = Array.isArray(bag["choices"]) ? (bag["choices"] as OpenPayload[]) : [];
  for (const block of choices) {
    const options = Array.isArray(block["options"]) ? (block["options"] as OpenPayload[]) : [];
    for (const option of options) {
      const optionItems = Array.isArray(option["items"]) ? (option["items"] as OpenPayload[]) : [];
      for (const row of optionItems) {
        if (typeof row["item_id"] === "string") items.add(row["item_id"] as IdString);
      }
    }
  }
  return [...items];
}

/**
 * Band-side verdict of one clause over one hireling: the traits it excludes and
 * the item tags its kit carries. `null` means the clause does not reject.
 */
export function hiringClauseRejectionFor(
  reader: KnowledgeReader,
  clause: BandHiringClause,
  hirelingId: IdString,
): string | null {
  const traits = new Set(hirelingTraitsOf(reader, hirelingId));
  const excludedTrait = clause.exclude_traits.find((trait) => traits.has(trait));
  if (excludedTrait) return excludedTrait;
  for (const itemId of hirelingKitItemsOf(reader, hirelingId)) {
    const tags = itemFactsOf(reader, itemId)?.tags ?? [];
    const excludedTag = clause.exclude_item_tags.find((tag) => tags.includes(tag));
    if (excludedTag) return excludedTag;
  }
  return null;
}

/**
 * Hiring verdict of one hireling for one band, using the KB semantics
 * (`campaign.hired-swords-and-dramatis.eligibility_semantics`): forbid wins;
 * empty allow lists mean no positive filter; an expression replaces the lists.
 * Roster-dependent clauses stay with the dynamic rule evaluator
 * (`hire-eligibility.ts`), which the decision reports as `dynamic`.
 */
export function hiringDecisionFor(
  reader: KnowledgeReader,
  bandId: IdString,
  hirelingId: IdString,
): HiringDecision {
  const groups = bandGroupsOf(reader, bandId);
  const row = hirelingCatalogueRowOf(reader, hirelingId);
  const subject = [bandId, hirelingId];
  if (!row) {
    return {
      kind: "unstructured",
      hireling_id: hirelingId,
      clause: "none",
      reason: `"${hirelingId}" has no eligibility entry in the campaign catalogue; the roster-dependent rules remain the only gate.`,
      issue: {
        code: "hiring_clause_unstructured",
        subject_ids: subject,
        message: `No published eligibility entry for "${hirelingId}" in the campaign catalogue.`,
        owner_task: "KB",
      },
    };
  }
  const forbidden = [...row.forbid_groups, ...row.forbid_band_ids].some(
    (token) => token === bandId || groups.includes(token),
  );
  if (forbidden) {
    return {
      kind: "rejected",
      hireling_id: hirelingId,
      clause: row.expression ? "expression" : "static",
      reason: row.note ?? `"${bandId}" is on the forbidden list for "${hirelingId}".`,
      issue: {
        code: "hiring_not_permitted",
        subject_ids: subject,
        message: `"${hirelingId}" may not be hired by "${bandId}".`,
      },
    };
  }
  // Band-side clauses: a warband's own printed exceptions narrow the hire set
  // (traits and kit item tags), independently of the entry's own filters.
  for (const clause of bandHiringClausesOf(reader, bandId)) {
    const excluded = hiringClauseRejectionFor(reader, clause, hirelingId);
    if (!excluded) continue;
    return {
      kind: "rejected",
      hireling_id: hirelingId,
      clause: "band-clause",
      rule_id: clause.rule_id,
      reason: `"${bandId}" may not hire "${hirelingId}": the band rule ${clause.rule_id} excludes "${excluded}".`,
      issue: {
        code: "hiring_not_permitted",
        subject_ids: subject,
        rule_id: clause.rule_id,
        message: `"${bandId}" may not hire "${hirelingId}" (${clause.rule_id}).`,
      },
    };
  }
  if (row.expression) {
    return expressionMatches(row.expression, bandId, groups)
      ? {
          kind: "allowed",
          hireling_id: hirelingId,
          clause: "expression",
          reason: row.note ?? `"${hirelingId}" accepts "${bandId}".`,
        }
      : {
          kind: "rejected",
          hireling_id: hirelingId,
          clause: "expression",
          reason: row.note ?? `"${bandId}" does not satisfy the eligibility of "${hirelingId}".`,
          issue: {
            code: "hiring_not_permitted",
            subject_ids: subject,
            message: `"${hirelingId}" may not be hired by "${bandId}".`,
          },
        };
  }
  const hasAllow = row.allow_groups.length > 0 || row.allow_band_ids.length > 0;
  if (!hasAllow) {
    return {
      kind: "allowed",
      hireling_id: hirelingId,
      clause: "static",
      reason: row.note ?? `"${hirelingId}" declares no positive band filter.`,
    };
  }
  const allowed = row.allow_band_ids.includes(bandId) || row.allow_groups.some((group) => groups.includes(group));
  if (allowed) {
    return {
      kind: "allowed",
      hireling_id: hirelingId,
      clause: "static",
      reason: row.note ?? `"${bandId}" is allowed to hire "${hirelingId}".`,
    };
  }
  return {
    kind: "rejected",
    hireling_id: hirelingId,
    clause: "static",
    reason: row.note ?? `"${bandId}" is not on the allow lists of "${hirelingId}".`,
    issue: {
      code: "hiring_not_permitted",
      subject_ids: subject,
      message: `"${hirelingId}" may not be hired by "${bandId}".`,
    },
  };
}

/**
 * Every construction verdict of a document, in one pass: roster composition,
 * equipment, skills, characteristic bounds, pending bindings and open clauses.
 * T10/T11 consume the list; nothing here mutates the document.
 */
export function constructionIssuesOf(
  reader: KnowledgeReader,
  campaign: Campaign,
): readonly ConstructionIssue[] {
  const issues: ConstructionIssue[] = [...rosterIssuesOf(reader, campaign)];
  const band = bandFactsOf(reader, campaign.identity.band_id);
  if (!band) return issues;
  const rows = racialMaximumsOf(reader);
  for (const warrior of campaign.warriors) {
    if (warrior.kind === "hireling" || !warrior.profile_id) continue;
    const profile = profileFactsOf(reader, band.band_id, warrior.profile_id);
    if (!profile) continue;
    for (const entry of warrior.equipment) {
      if (entry.acquisition === "fixed") continue;
      const issue = equipmentIssueFor(
        reader,
        profile,
        entry.item_id,
        campaign.identity.mercenary_variant ?? null,
      );
      if (issue && !(entry.acquisition === "starting_grant" && issue.code === "equipment_not_permitted")) {
        issues.push(issue);
      }
    }
    // Limits stated over the complete set (missile-weapon count, compulsory
    // family): the kit is decided as a whole, never item by item.
    issues.push(
      ...memberEquipmentIssuesFor(
        reader,
        profile,
        warrior.equipment.map((entry) => entry.item_id),
      ),
    );
    for (const [stat, value] of Object.entries(warrior.stats)) {
      if (typeof value !== "number") continue;
      const issue = characteristicBoundIssueFor({ profile, stat, value, rows });
      if (issue) issues.push(issue);
    }
    for (const ruleId of warrior.skills) {
      const pending = PENDING_BINDINGS.find((entry) => entry.rule_id === ruleId);
      if (pending) {
        issues.push({
          code: "pending_combat_binding",
          subject_ids: [band.band_id, warrior.id, pending.rule_id],
          rule_id: pending.rule_id,
          binding_id: pending.binding_id,
          owner_task: pending.owner_task,
          message: `"${pending.rule_id}" declares ${pending.binding_id} without an executable contract: combat resolution is pending.`,
        });
      }
    }
    for (const clause of openClausesOf(band, profile)) {
      issues.push({
        code: "construction_clause_unstructured",
        subject_ids: [band.band_id, profile.profile_id, clause.rule_id],
        rule_id: clause.rule_id,
        owner_task: clause.owner_task,
        message: `"${clause.rule_id}" (${clause.scope}) is a construction clause the KB does not express structurally: ${clause.reason}`,
      });
    }
  }
  for (const clause of openClausesOf(band, null)) {
    issues.push({
      code: "construction_clause_unstructured",
      subject_ids: [band.band_id, clause.rule_id],
      rule_id: clause.rule_id,
      owner_task: clause.owner_task,
      message: `"${clause.rule_id}" (${clause.scope}) is a construction clause the KB does not express structurally: ${clause.reason}`,
    });
  }
  return issues;
}
