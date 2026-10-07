/** Shared warrior eligibility. No campaign state, combat engine, IO or UI. */
export interface EligibilityIssue {
  readonly code: "equipment_not_permitted" | "equipment_forbidden" | "equipment_unknown_item"
    | "equipment_limit_exceeded" | "equipment_required_missing" | "equipment_slot_occupied"
    | "equipment_combination_forbidden" | "skill_not_permitted"
    | "skill_pending_special_list" | "construction_clause_unstructured";
  readonly subject_ids: readonly string[];
  readonly message: string;
  readonly rule_id?: string;
  readonly binding_id?: string;
  readonly owner_task?: "KB";
}

/**
 * Issues that report a knowledge-base gap instead of refusing a legal choice.
 * The campaign contract keeps them visible without blocking the change; the
 * shared module owns that distinction so no consumer re-invents it.
 */
export const INFORMATIONAL_ISSUE_CODES: readonly EligibilityIssue["code"][] = [
  "equipment_unknown_item", "skill_pending_special_list", "construction_clause_unstructured",
];

export function issueIsInformational(code: EligibilityIssue["code"]): boolean {
  return INFORMATIONAL_ISSUE_CODES.includes(code);
}

export interface ItemFacts {
  readonly kind: string;
  readonly mechanic_id: string | null;
  readonly tags: readonly string[];
  readonly hands?: number;
}

/**
 * Printed bound on how many missile weapons a member may carry at once, with
 * the printed items it does not count.
 *
 * 'May only purchase ONE non-pebble or non-slingshot missile weapon' is a bound
 * on what the member may carry, so it is judged over the whole equipment set
 * and never over one slot, and it counts the units of the kit rather than the
 * distinct ids. The exempt ids stay offered: the clause leaves them out of the
 * count instead of forbidding them.
 */
export interface MissileWeaponLimit {
  readonly rule_id: string;
  readonly maximum: number;
  /** Item or mechanic ids the printed clause does not count. */
  readonly exempt_item_ids: readonly string[];
}

export interface ProfileFacts {
  readonly band_id: string;
  readonly profile_id: string;
  readonly fixed_equipment: readonly string[];
  readonly equipment_access: readonly { readonly item_id: string; readonly list_id?: string }[] | null;
  readonly equipment_forbids: readonly string[];
  readonly skill_access: readonly string[];
  readonly skill_lists: readonly { readonly rule_id: string; readonly category: string; readonly skills: readonly string[] }[];
  /**
   * Skill tables a `compiler.promoted-hero-skill-access` rule opens for this
   * profile **once it is promoted**. The grant is conditional by its printed
   * text, so it is carried separately: `skill_access` includes it only when the
   * facts describe the configured Hero, and a consumer that validates a
   * promotion can consult the field without granting it to the Henchman.
   */
  readonly promotion_skill_access?: readonly string[];
  readonly active_weapon_forbids?: readonly { readonly rule_id: string; readonly forbids: readonly string[] }[];
  readonly active_weapon_limit?: { readonly rule_id: string; readonly maximum: number };
  /** Compulsory-item obligations of the profile's own printed clauses. */
  readonly required_equipment?: readonly RequiredEquipment[];
  /** Weapon kinds each governed poison may coat for this bearer. */
  readonly poison_application?: readonly PoisonApplication[];
  /**
   * Printed sets of an active weapon a clause admits ('may only use a sword,
   * dagger, or Mage Staff in battle'). A printed permission is an active-use
   * fact: possessing another item stays legal, only fighting with it does not.
   */
  readonly active_weapon_permits?: readonly { readonly rule_id: string; readonly permits: readonly string[] }[];
  /** Printed missile bounds of the profile's own clauses, counted over the set. */
  readonly missile_weapon_limit?: readonly MissileWeaponLimit[];
}

export interface SkillFacts {
  readonly id: string;
  readonly category: string;
  readonly kind: string;
}

/**
 * Printed bound on how many copies of one item a member may carry at the same
 * time, with the profiles the source exempts and the bound they may carry
 * instead ('Only the Sigmarite Matriarch and Sister Superiors may carry two
 * Sigmarite warhammers at the same time'). It bounds **possession**: an
 * ordinary bearer may own one, an exempt bearer up to its own bound.
 */
export interface EquipmentItemCopyLimit {
  readonly item_id: string;
  readonly maximum: number;
  readonly exempt_profile_ids: readonly string[];
  /** Copies the exempt profiles may carry instead; absent means unbounded. */
  readonly exempt_maximum?: number;
}

export interface EquipmentLimits {
  readonly rule_id?: string;
  readonly max_missile_weapons?: number;
  readonly required_tag?: string;
  readonly exempt_profile_ids?: readonly string[];
  readonly item_copy_limit?: EquipmentItemCopyLimit;
}

/**
 * A printed obligation to *acquire* one item of a family, distinct from the
 * active weapon a duel loads. 'Must buy a weapon from the hand-to-hand combat
 * list; a simple dagger is not acceptable' obliges the purchase; the source
 * never obliges attacking with that weapon, so this is a whole-set requirement
 * and not an active-slot one.
 */
export interface RequiredEquipment {
  readonly rule_id: string;
  /**
   * Item kinds, or an item/mechanic id when the obligation names one canonical
   * object ('must include a Chaos Dwarf Blunderbuss'), any one of which
   * satisfies the obligation.
   */
  readonly kinds: readonly string[];
  /** Item/mechanic ids the obligation excludes even when their kind matches. */
  readonly excludes: readonly string[];
}

/**
 * Printed condition on applying a poison to a weapon, admitted per bearer and
 * weapon kind ('Skink Heroes on missile weapons; Saurus on close combat
 * weapons'). A poison outside its admitted kinds is refused for that bearer;
 * the acquisition route and the Trading procedure are separate clauses.
 */
export interface PoisonApplication {
  readonly rule_id: string;
  readonly poisons: readonly string[];
  readonly weapon_kinds: readonly string[];
}

export const EQUIPMENT_TAG_VOCABULARY: readonly string[] = [
  "animal", "blackpowder", "bow", "crossbow", "poison", "thrown", "constant-save-cloak",
];
const HEAVY_ARMOUR = ["armour.heavy-armour", "armour.gromril-armour", "armour.ithilmar-armour", "armour.plate-armour"];
/** Item kinds that are a weapon a profile may hold and swing. */
const WEAPON_KINDS = ["close-combat-weapon", "ranged-weapon"];
const INTERPRETED_TOKENS = ["armour", "armour-suit", "heavy-armour", "ranged-weapons", "weapons",
  "two-handed-weapons", "equipment", "non-thrown-ranged", ...EQUIPMENT_TAG_VOCABULARY];

/**
 * The attack a weaponless creature fights with. It is the profile's own bite or
 * claw, not an item the build selects, so no printed 'never uses weapons or
 * armour' clause can forbid it: the compiler resolves an unequippable profile
 * to exactly this mechanic.
 */
export const NATURAL_ATTACK_ID = "weapon.natural-attacks";

export function tokenForbids(token: string, itemId: string, item: ItemFacts | null): boolean {
  if (token === itemId || token === item?.mechanic_id) return true;
  if (itemId === NATURAL_ATTACK_ID || item?.mechanic_id === NATURAL_ATTACK_ID) return false;
  if (token === "non-thrown-ranged") return item?.kind === "ranged-weapon" && !item.tags.includes("thrown");
  // `equipment` is the printed 'no equipment' clause. The caller has already
  // returned for the neutral ids (an empty hand or no armour) and for the
  // profile's own fixed kit, so nothing here is the absence of a choice.
  if (token === "equipment") return true;
  if (item === null) return false;
  if (EQUIPMENT_TAG_VOCABULARY.includes(token)) return item.tags.includes(token);
  if (token === "armour") return ["armour", "shield-or-defence"].includes(item.kind);
  if (token === "armour-suit") return item.kind === "armour" || item.mechanic_id === "defence.sea-dragon-cloak";
  if (token === "heavy-armour") return item.mechanic_id !== null && HEAVY_ARMOUR.includes(item.mechanic_id);
  // A printed 'may not use weapons' covers held weapons of either reach; a
  // natural attack or an item record with no weapon mechanic is not one.
  if (token === "weapons") return WEAPON_KINDS.includes(item.kind)
    || (item.mechanic_id !== null && item.mechanic_id.startsWith("weapon."));
  // 'may only ever use one at a time', 'may use only one-handed weapons' and
  // 'may not use double-handed weapons' are the same printed fact: the weapon
  // occupies both hands.
  if (token === "two-handed-weapons") return (item.hands ?? 0) >= 2;
  return token === "ranged-weapons" && item.kind === "ranged-weapon";
}

/**
 * Whether a printed permit token admits this item.
 *
 * A permission clause names canonical objects ('a sword, dagger, or Mage
 * Staff'), so the token is matched against the item id, the mechanic that
 * resolves it and the kind the catalogue publishes. Unlike `tokenForbids`
 * there is no family vocabulary to invert: an item outside the printed set is
 * simply not admitted.
 */
export function tokenPermits(token: string, itemId: string, item: ItemFacts | null): boolean {
  return token === itemId || token === item?.mechanic_id || token === item?.kind;
}

/**
 * Neutral defaults a build carries when a slot is empty. They are never rows
 * of a purchasable equipment list, so access cannot refuse them: an empty
 * hand or the normal material is the absence of an equipment choice.
 */
export const NEUTRAL_ITEM_IDS: readonly string[] = ["weapon.fist", "armour.no-armour", "material.normal"];

/**
 * Equipment families of the mechanic catalogue. A binding whose id falls
 * outside them (`skill.*`, `mechanic.*`) is a skill or a passive effect: it is
 * not equipment a profile may be offered, even though the catalogue indexes it
 * beside the weapons and armours.
 */
export const EQUIPMENT_MECHANIC_PREFIXES: readonly string[] = [
  "weapon.", "armour.", "defence.", "material.", "preparation.", "poison.",
];

export function isEquipmentMechanic(id: string): boolean {
  return EQUIPMENT_MECHANIC_PREFIXES.some((prefix) => id.startsWith(prefix));
}

export function equipmentIssue(args: {
  readonly profile: ProfileFacts;
  readonly item_id: string;
  readonly item: ItemFacts | null;
  readonly band_forbids?: readonly string[];
  readonly active_lists?: readonly string[];
  readonly gated_lists?: readonly string[];
}): EligibilityIssue | null {
  const { profile, item_id: itemId, item } = args;
  const subject = [profile.band_id, profile.profile_id, itemId];
  if (NEUTRAL_ITEM_IDS.includes(itemId)) return null;
  if (profile.fixed_equipment.includes(itemId)) return null;
  const offers = (profile.equipment_access ?? []).filter((offer) => offer.list_id === undefined
    || !(args.gated_lists ?? []).includes(offer.list_id) || (args.active_lists ?? []).includes(offer.list_id));
  const offered = profile.equipment_access !== null && offers.some((offer) => offer.item_id === itemId);
  if (profile.equipment_access !== null && !offered) return {
    code: "equipment_not_permitted", subject_ids: subject,
    message: `"${itemId}" is not on any equipment list of ${profile.band_id}/${profile.profile_id}.`,
  };
  const forbids = [...profile.equipment_forbids, ...(args.band_forbids ?? [])];
  for (const token of forbids) if (tokenForbids(token, itemId, item)) return {
    code: "equipment_forbidden", subject_ids: subject,
    message: `"${token}" is forbidden for ${profile.band_id}/${profile.profile_id}.`,
  };
  const unknown = forbids.find((token) => !INTERPRETED_TOKENS.includes(token) && token !== itemId
    && !["armour.", "defence.", "weapon."].some((prefix) => token.startsWith(prefix)));
  if (unknown) return {
    code: "construction_clause_unstructured", subject_ids: subject, rule_id: unknown, owner_task: "KB",
    message: `The prohibition token "${unknown}" of ${profile.band_id}/${profile.profile_id} has no construction contract; the choice is reported, not silently allowed.`,
  };
  if (item === null && offered) return {
    code: "equipment_unknown_item", subject_ids: subject, owner_task: "KB",
    message: `"${itemId}" is offered by ${profile.band_id}/${profile.profile_id} but has no item record in the KB artefact.`,
  };
  return null;
}

/**
 * Verdict on applying one poison to one weapon for a bearer.
 *
 * A printed line can qualify the *application* of a poison by weapon kind and
 * bearer ('Skink Heroes on missile weapons; Saurus on close combat weapons').
 * The fact is published once per bearer and consumed here: when a governed
 * poison coats a weapon outside its admitted kinds the application is refused,
 * while the poison's recipient set stays the canonical one. A bearer the source
 * does not qualify for that poison is not governed and is never refused here.
 */
/**
 * Whether a canonical item record is a missile weapon for the printed
 * application clauses.
 *
 * The item kind the catalogue publishes is the primary signal; a record whose
 * kind the catalogue flattened (`trollheim-equipment` for a weapon) is still a
 * missile when it carries a ranged tag of the tag vocabulary. A held weapon
 * with none of those signals is a close combat weapon.
 */
function itemIsMissile(item: ItemFacts | null): boolean {
  if (!item) return false;
  if (item.kind === "ranged-weapon") return true;
  return ["bow", "crossbow", "blackpowder", "thrown"].some((tag) => item.tags.includes(tag));
}

/**
 * Whether a weapon satisfies one printed weapon-kind of an application clause.
 *
 * `ranged-weapon` and `close-combat-weapon` are the printed reach families, so
 * they are decided by the shared missile reading (and the existing `weapons`
 * token for the held case) instead of by a raw kind equality: the catalogue
 * flattens some weapon records to a family kind, and equality would refuse a
 * legal closer-combat weapon.
 */
function weaponSatisfiesKind(kind: string, itemId: string, item: ItemFacts | null): boolean {
  if (kind === "ranged-weapon") return itemIsMissile(item);
  if (kind === "close-combat-weapon") return !itemIsMissile(item) && tokenForbids("weapons", itemId, item);
  return item?.kind === kind;
}

export function poisonApplicationIssue(args: {
  readonly profile: Pick<ProfileFacts, "band_id" | "profile_id" | "poison_application">;
  readonly poison_id: string;
  readonly poison?: ItemFacts | null;
  readonly weapon_id: string;
  readonly weapon: ItemFacts | null;
}): EligibilityIssue | null {
  const { profile, poison_id: poisonId } = args;
  const poisonIds = [poisonId, args.poison?.mechanic_id ?? ""].filter((id) => id !== "");
  const governed = (profile.poison_application ?? [])
    .filter((application) => application.poisons.some((id) => poisonIds.includes(id)));
  if (!governed.length) return null;
  if (governed.some((application) => application.weapon_kinds
    .some((kind) => weaponSatisfiesKind(kind, args.weapon_id, args.weapon)))) return null;
  const kinds = Array.from(new Set(governed.flatMap((application) => application.weapon_kinds)));
  return {
    code: "equipment_forbidden", rule_id: governed[0]!.rule_id,
    subject_ids: [profile.band_id, profile.profile_id, poisonId, args.weapon_id],
    message: `"${poisonId}" may only be applied to ${kinds.join("/")} by ${profile.band_id}/${profile.profile_id}.`,
  };
}

export function skillIssue(profile: ProfileFacts, skill: SkillFacts, strictEmptyAccess = false): EligibilityIssue | null {
  const subject = [profile.band_id, profile.profile_id, skill.id];
  if (profile.skill_access.length === 0 && !strictEmptyAccess) return null;
  if (!skillCategoryAllowed(profile.skill_access, skill.category, strictEmptyAccess)) return {
    code: "skill_not_permitted", subject_ids: subject,
    message: `"${skill.id}" (${skill.category}) is outside the skill access of ${profile.band_id}/${profile.profile_id}.`,
  };
  if (skill.category === "special") {
    const lists = profile.skill_lists.filter((list) => list.category === "special");
    // A special list with no transcribed members is the prose-only state of
    // the printed table (T09/T10): report it as pending exactly like the
    // absent-list case, instead of refusing the whole catalogue as if the
    // table had been published empty.
    if (lists.length === 0 || lists.every((list) => list.skills.length === 0)) return {
      code: "skill_pending_special_list", subject_ids: subject, owner_task: "KB",
      message: `"${skill.id}" belongs to a band special-skill list whose members are prose-only in the KB; the list rule is not enforced yet.`,
    };
    if (!lists.some((list) => list.skills.includes(skill.id))) return {
      code: "skill_not_permitted", subject_ids: subject,
      ...(lists[0] ? { rule_id: lists[0].rule_id } : {}),
      message: `"${skill.id}" is not on the published special-skill list of ${profile.band_id}/${profile.profile_id} (${lists.map((list) => list.rule_id).join(", ")}).`,
    };
  }
  return null;
}

export function skillCategoryAllowed(access: readonly string[], category: string, strictEmptyAccess = false): boolean {
  return (!access.length && !strictEmptyAccess) || access.includes(category);
}

export function equipmentSetIssues(args: {
  readonly profile: Pick<ProfileFacts, "band_id" | "profile_id" | "required_equipment" | "missile_weapon_limit">;
  readonly limits: EquipmentLimits | null;
  readonly items: readonly { readonly item_id: string; readonly item: ItemFacts | null }[];
}): readonly EligibilityIssue[] {
  const { profile, limits, items } = args;
  const subject = [profile.band_id, profile.profile_id];
  const issues: EligibilityIssue[] = [];
  // The profile's own printed missile bound: one entry is one unit of the kit,
  // and the printed exemptions are left out of the count instead of refused.
  for (const bound of profile.missile_weapon_limit ?? []) {
    const exempt = (entry: { readonly item_id: string; readonly item: ItemFacts | null }) =>
      bound.exempt_item_ids.includes(entry.item_id)
      || (entry.item?.mechanic_id != null && bound.exempt_item_ids.includes(entry.item.mechanic_id));
    const counted = items.filter((entry) => itemIsMissile(entry.item) && !exempt(entry));
    if (counted.length > bound.maximum) issues.push({
      code: "equipment_limit_exceeded", rule_id: bound.rule_id,
      subject_ids: [...subject, ...counted.map((entry) => entry.item_id)],
      message: `${profile.band_id}/${profile.profile_id} carries ${counted.length} missile weapons; the printed clause allows ${bound.maximum}`
        + (bound.exempt_item_ids.length ? ` besides ${bound.exempt_item_ids.join(", ")}.` : "."),
    });
  }
  if (limits) {
    const carried = items.filter((entry) => entry.item?.kind === "ranged-weapon");
    if (typeof limits.max_missile_weapons === "number" && carried.length > limits.max_missile_weapons) issues.push({
      code: "equipment_limit_exceeded", subject_ids: [...subject, ...carried.map((entry) => entry.item_id)],
      ...(limits.rule_id ? { rule_id: limits.rule_id } : {}),
      message: `${profile.band_id}/${profile.profile_id} carries ${carried.length} missile weapons; the band allows ${limits.max_missile_weapons}.`,
    });
    if (!(limits.exempt_profile_ids ?? []).includes(profile.profile_id)
      && limits.required_tag?.trim() && !items.some((entry) => entry.item?.tags.includes(limits.required_tag!))) issues.push({
      code: "equipment_required_missing", subject_ids: subject,
      ...(limits.rule_id ? { rule_id: limits.rule_id } : {}),
      message: `The equipment of ${profile.band_id}/${profile.profile_id} includes no "${limits.required_tag}": the band compiles the kit from that family only.`,
    });
    // A copy bound is a possession bound: two identical hammers are two rows of
    // the owned list, and the exempt bearer carries its own printed maximum.
    const limit = limits.item_copy_limit;
    if (limit) {
      const copies = items.filter((entry) => entry.item_id === limit.item_id
        || entry.item?.mechanic_id === limit.item_id);
      const exempt = limit.exempt_profile_ids.includes(profile.profile_id);
      const maximum = exempt ? limit.exempt_maximum : limit.maximum;
      if (typeof maximum === "number" && copies.length > maximum) issues.push({
        code: "equipment_limit_exceeded", subject_ids: [...subject, limit.item_id],
        ...(limits.rule_id ? { rule_id: limits.rule_id } : {}),
        message: `${profile.band_id}/${profile.profile_id} carries ${copies.length} copies of "${limit.item_id}"; the printed clause allows ${maximum} for this bearer.`,
      });
    }
  }
  // Compulsory-item obligations of the profile's own clause: the whole set must
  // include one item of the family, and the printed items that do not count
  // (the free dagger) never satisfy it.
  for (const requirement of profile.required_equipment ?? []) {
    const satisfied = items.some((entry) => {
      const item = entry.item;
      if (NEUTRAL_ITEM_IDS.includes(entry.item_id)) return false;
      // A `kind` may also name the item or the mechanic that resolves it, so a
      // clause that obliges one canonical object ('must include a Chaos Dwarf
      // Blunderbuss') is satisfiable without inventing a kind the catalogue
      // does not publish.
      const named = requirement.kinds.includes(entry.item_id)
        || (item?.mechanic_id != null && requirement.kinds.includes(item.mechanic_id));
      if (!named && (item === null || !requirement.kinds.includes(item.kind))) return false;
      return ![entry.item_id, item?.mechanic_id ?? ""].some((id) => requirement.excludes.includes(id));
    });
    if (!satisfied) issues.push({
      code: "equipment_required_missing", subject_ids: [...subject, ...requirement.kinds],
      rule_id: requirement.rule_id,
      message: `The equipment of ${profile.band_id}/${profile.profile_id} includes no ${requirement.kinds.join("/")}; the printed clause obliges acquiring one.`,
    });
  }
  return issues;
}

export type RecordData = Readonly<Record<string, unknown>>;
export interface Binding { readonly id: string; readonly parameters?: RecordData }
export interface EditorialProfile {
  readonly id: string;
  readonly type?: string;
  readonly skill_access?: readonly string[];
  readonly equipment_lists?: readonly string[];
  readonly fixed_equipment?: readonly string[];
  readonly equipment_restrictions?: readonly string[];
  readonly rule_ids?: readonly string[];
  /**
   * Selection facts the build declares (a warband variant, `promotion.hero`, a
   * chosen House or Modus Operandi). `configuredProfile` attaches them so a
   * printed entry conditional on the selection reaches only the configured
   * profile.
   */
  readonly variants?: readonly string[];
  readonly hireling_equipment?: HirelingEquipment;
}
export interface HirelingKitEntry {
  readonly item_id: string;
  readonly mechanic_id?: string;
  readonly material_id?: string;
  readonly quantity: { readonly kind: string; readonly value?: number };
}
export interface HirelingEquipment {
  readonly fixed_items?: readonly HirelingKitEntry[];
  readonly optional_items?: readonly HirelingKitEntry[];
  readonly choices?: readonly { readonly choose: number; readonly options: readonly { readonly items: readonly HirelingKitEntry[] }[] }[];
  readonly unique_equipment?: readonly { readonly id: string; readonly rules?: readonly string[] }[];
}
export interface EditorialRule {
  readonly id: string;
  readonly kind?: string;
  readonly eligibility?: readonly string[];
  readonly applies_to?: { readonly band?: boolean; readonly profile_ids?: readonly string[]; readonly profile_types?: readonly string[] };
  readonly runtime?: { readonly grant?: string; readonly implemented?: string; readonly scope?: string };
  readonly bindings?: readonly Binding[];
}
/**
 * Printed recipients of one list line, when the source names them.
 *
 * The profile selectors are a **union**: 'Heroes and Marksmen only' is every
 * hero plus the Marksmen profile, because the printed note enumerates a set of
 * members. A line without `applies_to` reaches every profile its list is
 * declared to. `variants` is a separate, **conjunctive** gate: the line is
 * conditional on the selection the build already declares (the chosen House,
 * the chosen Modus Operandi or another variant), independent of the named
 * recipients.
 */
export interface EquipmentEntry {
  readonly item_id: string;
  readonly applies_to?: {
    readonly profile_types?: readonly string[];
    readonly profile_ids?: readonly string[];
    readonly variants?: readonly string[];
    /** Named profiles the printed line denies even when the selectors reach them. */
    readonly excluded_profile_ids?: readonly string[];
  };
}
export interface EquipmentList { readonly id: string; readonly items?: readonly EquipmentEntry[]; readonly loadouts?: readonly { readonly items?: unknown }[] }

/**
 * Whether a printed line reaches this profile. An entry that names no
 * recipients is offered to the whole list. A variant gate is decided by the
 * build's declared variants, carried on the configured profile, so the
 * offering layer and every decision read one fact instead of a per-band
 * exception.
 */
export function entryReachesProfile(
  entry: EquipmentEntry,
  profile: { readonly id: string; readonly type?: string; readonly variants?: readonly string[] },
): boolean {
  const recipients = entry.applies_to;
  if (!recipients) return true;
  // A named denial is conjunctive with the rest: 'Sniper only ... not
  // available to the Silent Master' reads the variant gate and the exclusion
  // together, and a promoted Henchman of another profile keeps the line.
  if ((recipients.excluded_profile_ids ?? []).includes(profile.id)) return false;
  if (recipients.variants?.length
    && !recipients.variants.some((token) => (profile.variants ?? []).includes(token))) return false;
  if (!recipients.profile_types?.length && !recipients.profile_ids?.length) return true;
  if ((recipients.profile_types ?? []).includes(profile.type ?? "")) return true;
  return (recipients.profile_ids ?? []).includes(profile.id);
}
export interface BandPackage {
  readonly band: { readonly id: string; readonly canonical_family?: string };
  readonly profiles: readonly EditorialProfile[];
  readonly equipment_lists: readonly EquipmentList[];
  readonly special_rules: readonly EditorialRule[];
}
export interface Catalogue {
  readonly packages: Readonly<Record<string, BandPackage>>;
  readonly foreign_packages: Readonly<Record<string, BandPackage>>;
  readonly mechanics: Readonly<Record<string, RecordData>>;
  readonly mappings: Readonly<Record<string, string>>;
  readonly skills: Readonly<Record<string, SkillFacts & { readonly source_refs?: readonly { readonly url?: string }[] }>>;
  readonly items?: Readonly<Record<string, ItemFacts>>;
  readonly free_rules?: Readonly<Record<string, EditorialRule>>;
}
export interface BuildFacts {
  readonly owned_item_ids?: readonly string[] | null;
  readonly open_flame?: boolean;
  readonly mounted?: boolean;
  readonly band_id?: string | null;
  readonly profile_id?: string | null;
  readonly main_weapon_id: string;
  readonly armour_id: string;
  readonly off_hand_id?: string | null;
  readonly extra_hand_id?: string | null;
  readonly main_material_id: string;
  readonly off_material_id: string;
  readonly main_poison_id?: string | null;
  readonly off_poison_id?: string | null;
  readonly defence_ids: readonly string[];
  readonly skill_ids: readonly string[];
  readonly preparation_ids: readonly string[];
  readonly special_rule_ids: readonly string[];
  readonly variant_ids: readonly string[];
}

/** Resolve one complete printed kit, preserving quantities and choice groups.
 * Active positions select a compatible kit when ownership is unspecified;
 * supplied ownership must equal a legal kit, not merely its availability union.
 */
export function resolveHirelingKit(equipment: HirelingEquipment, build: BuildFacts, catalogue: Catalogue,
  rules: readonly EditorialRule[] = []): readonly string[] {
  const unique = equipment.unique_equipment ?? [];
  for (const item of unique) {
    if (!item.id || !item.rules?.length || !item.rules.every(id => {
      const matching = rules.filter(rule => rule.id === id);
      return matching.length === 1 && matching[0]!.runtime?.scope === "NO"
        && matching[0]!.runtime?.implemented === "NO" && !matching[0]!.bindings?.length;
    })) throw new Error("hireling unique equipment needs a canonical combat mapping");
  }
  const expand = (entries: readonly HirelingKitEntry[]): string[] => entries.flatMap(entry => {
    const count = entry.quantity.value;
    if (entry.quantity.kind !== "fixed" || !Number.isInteger(count) || count === undefined || count < 1)
      throw new Error(`unsupported hireling kit quantity: ${entry.item_id}`);
    return Array.from({ length: count }, () => entry.item_id);
  });
  let kits = [[...expand(equipment.fixed_items ?? []), ...unique.map(item => item.id)]];
  for (const group of equipment.choices ?? []) {
    if (group.choose !== 1 || !group.options.length) throw new Error("unsupported hireling equipment choice");
    kits = kits.flatMap(kit => group.options.map(option => [...kit, ...expand(option.items)]));
  }
  for (const entry of equipment.optional_items ?? []) {
    const addition = expand([entry]);
    kits = kits.flatMap(kit => [kit, [...kit, ...addition]]);
  }
  const signature = (items: readonly string[]) => [...items].sort().join("\u0000");
  const neutral = new Set(["weapon.fist", "armour.no-armour"]);
  const active = [build.main_weapon_id, build.off_hand_id, build.extra_hand_id, build.armour_id,
    ...build.defence_ids, ...build.preparation_ids, build.main_poison_id, build.off_poison_id]
    .filter((id): id is string => Boolean(id) && !neutral.has(id ?? ""));
  if (active.some(id => unique.some(item => item.id === id)))
    throw new Error("non-duel unique equipment cannot occupy an active combat position");
  const owned = build.owned_item_ids;
  const matched = kits.find(kit => {
    if (owned != null && signature(kit) !== signature(owned)) return false;
    const entries = [...(equipment.fixed_items ?? []), ...(equipment.optional_items ?? []),
      ...(equipment.choices ?? []).flatMap(group => group.options.flatMap(option => option.items))];
    const mechanic = (id: string) => entries.find(entry => entry.item_id === id)?.mechanic_id ?? catalogue.mappings[id] ?? id;
    for (const [id, material] of [[build.main_weapon_id, build.main_material_id], [build.off_hand_id, build.off_material_id]]) {
      if (!id || neutral.has(id)) {
        if (material !== "material.normal") return false;
        continue;
      }
      const printed = entries.find(entry => kit.includes(entry.item_id) && mechanic(entry.item_id) === id)?.material_id ?? "material.normal";
      if (material !== "material.normal" && material !== printed) return false;
    }
    const remaining = kit.map(mechanic);
    for (const id of active) {
      const position = remaining.indexOf(catalogue.mappings[id] ?? id);
      if (position < 0) return false;
      remaining.splice(position, 1);
    }
    return true;
  });
  if (!matched) throw new Error("hireling active equipment and supplied ownership do not form a complete legal printed kit");
  return matched;
}
export interface BuildContext {
  readonly build: BuildFacts;
  readonly profile: EditorialProfile;
  readonly package: BandPackage;
  readonly catalogue: Catalogue;
  readonly profile_bindings: readonly Binding[];
  readonly compiler_bindings: readonly Binding[];
  readonly contracts: readonly string[];
}

export const BLACKPOWDER_WEAPONS = ["weapon.pistol", "weapon.duelling-pistol"];
export const MISSILE_WEAPONS = BLACKPOWDER_WEAPONS;
export const DRUG_PREPARATIONS = ["preparation.crimson-shade", "preparation.mandrake-root", "preparation.mad-cap-mushrooms", "preparation.head-splitter-mushrooms"];
function strings(value: unknown): string[] {
  return typeof value === "string" ? [value] : Array.isArray(value) ? value.map(String) : [];
}
function containsAny(values: Iterable<string | null | undefined>, wanted: readonly string[]): boolean {
  return Array.from(values).some((value) => value != null && wanted.includes(value));
}
function pythonList(values: readonly string[]): string {
  return `[${values.map((value) => `'${value.replaceAll("'", "\\'")}'`).join(", ")}]`;
}
function loadoutItems(value: unknown): string[] {
  if (typeof value === "string") return [value];
  if (Array.isArray(value)) return value.flatMap(loadoutItems);
  if (value && typeof value === "object") return Object.values(value).flatMap(loadoutItems);
  return [];
}
/* Tokens the specialist bound-equipment stage already interprets from its own selection lists. */
const BOUND_STAGE_TOKENS = ["armour", "ranged-weapons", "heavy-armour", "weapon.lance", "defence.helmet"];
/* Canonical facts of a selected equipment id, merged across every alias of its mechanic. */
export function carriedItemFacts(catalogue: Pick<Catalogue, "items">, id: string): ItemFacts | null {
  if (!id) return null;
  const items = catalogue.items ?? {};
  const direct = items[id];
  if (direct) return direct;
  const aliases = Object.values(items).filter((item) => item.mechanic_id === id);
  if (!aliases.length) return null;
  const kinds = Array.from(new Set(aliases.map((item) => item.kind)));
  return { kind: kinds.length === 1 ? kinds[0]! : "", mechanic_id: id,
    tags: Array.from(new Set(aliases.flatMap((item) => item.tags))) };
}

/**
 * Canonical item facts keyed by item id and by mechanic id.
 *
 * A desktop adapter carries mechanics in its build while the catalogue rows
 * are keyed by item id, so the transport resolves both spellings through the
 * same alias merge `carriedItemFacts` applies to selected equipment: one
 * interpretation, no per-consumer lookup table.
 */
export function catalogueItemFacts(catalogue: Catalogue): Record<string, ItemFacts> {
  const items = catalogue.items ?? {};
  const result: Record<string, ItemFacts> = { ...items };
  for (const id of Object.keys(items)) {
    const facts = carriedItemFacts(catalogue, id);
    const hands = catalogue.mechanics[facts?.mechanic_id ?? ""]?.["hands"];
    if (facts) result[id] = { ...facts, ...(typeof hands === "number" ? { hands } : {}) };
  }
  for (const row of Object.values(items)) {
    if (!row.mechanic_id) continue;
    const merged = carriedItemFacts(catalogue, row.mechanic_id);
    const hands = catalogue.mechanics[row.mechanic_id]?.["hands"];
    if (merged) result[row.mechanic_id] = { ...merged, ...(typeof hands === "number" ? { hands } : {}) };
  }
  return result;
}

export function applicableProfileRules(pack: BandPackage, profile: EditorialProfile): readonly EditorialRule[] {
  return pack.special_rules.filter((rule) => recipientTypeMatches(rule, profile) && ((profile.rule_ids ?? []).includes(rule.id)
    || (rule.runtime?.grant === "profile" && (rule.applies_to?.profile_ids ?? []).includes(profile.id))));
}
function recipientTypeMatches(rule: EditorialRule, profile: EditorialProfile): boolean {
  return !rule.applies_to?.profile_types?.length || rule.applies_to.profile_types.includes(profile.type ?? "");
}

/** Supplied local advancement result, not a campaign promotion calculation. */
export function configuredProfile(profile: EditorialProfile, variants: readonly string[]): EditorialProfile {
  // The selected facts travel with the profile so a printed entry conditional
  // on them is read by the same `entryReachesProfile` the offering layer uses.
  const configured = variants.length ? { ...profile, variants: [...variants] } : profile;
  if (!variants.includes("promotion.hero") || profile.type === "hero") return configured;
  if (profile.type !== "henchman") throw new Error("promotion.hero requires a canonical Henchman profile");
  return { ...configured, type: "hero" };
}
export function applicableRules(pack: BandPackage, profile: EditorialProfile): readonly EditorialRule[] {
  const rules = applicableProfileRules(pack, profile);
  return [...rules, ...pack.special_rules.filter((rule) => !rules.includes(rule) && rule.runtime?.grant === "band"
    && recipientTypeMatches(rule, profile)
    && rule.applies_to?.band === true && (!(rule.applies_to?.profile_ids?.length) || rule.applies_to.profile_ids.includes(profile.id)) && (!(rule.eligibility?.length) || rule.eligibility.includes(profile.id)))];
}

function profileEquipmentItems(pack: BandPackage, profile: EditorialProfile): Set<string> {
  const itemIds = new Set(profile.fixed_equipment ?? []);
  for (const listId of profile.equipment_lists ?? []) {
    const list = pack.equipment_lists.find((entry) => entry.id === listId);
    if (!list) throw new Error(`profile references unknown equipment list: ${pack.band.id}/${profile.id}/${listId}`);
    // Printed recipients the source names ('Heroes only', 'Halfling Cooks
    // only') travel on the entry itself, so the offering layer and every
    // decision read one fact instead of a per-band exception.
    for (const item of list.items ?? []) {
      if (!entryReachesProfile(item, profile)) continue;
      itemIds.add(item.item_id);
    }
    for (const loadout of list.loadouts ?? []) for (const id of loadoutItems(loadout.items)) itemIds.add(id);
  }
  // Printed item eligibility is separate from whether its combat effect runs.
  if (profile.type !== "hero") {
    itemIds.delete("darksteel_blade");
  }
  if (itemIds.has("spirit_knife")) {
    const etherealHero = pack.band.id === "call-of-the-night-haint-mim" && profile.type === "hero"
      && (profile.rule_ids ?? []).some(id => id.endsWith("--ethereal") || id === "revenants--spectral-ascension");
    if (!etherealHero) itemIds.delete("spirit_knife");
  }
  if (pack.band.id === "savage-orcs-kaz" && profile.id === "gobbo-boyz") itemIds.delete("skull_busta");
  return itemIds;
}
export function profileEquipment(pack: BandPackage, profile: EditorialProfile, catalogue: Catalogue): string[] {
  const itemIds = profileEquipmentItems(pack, profile);
  const allowed = new Set(Array.from(itemIds).flatMap((id) => catalogue.mappings[id] ? [catalogue.mappings[id]!] : []));
  // Printed equipment concessions are the bindings of equipment families. The
  // skills family indexes skills and passive mechanics beside the weapons and
  // armours; those are abilities, not equipment offers, so they are excluded
  // here instead of reaching every access projection as an unknown item. A
  // family-prefixed concession without an item record (`weapon.vomit-attack`)
  // stays offered: canonical builds select it as their main weapon, and the
  // missing record is reported informationally, never refused.
  for (const rule of applicableProfileRules(pack, profile)) for (const binding of rule.bindings ?? []) {
    if (isEquipmentMechanic(binding.id) && binding.id in catalogue.mechanics) allowed.add(binding.id);
  }
  return Array.from(allowed).sort();
}

export function specialRuleOptions(pack: BandPackage, profile: EditorialProfile, catalogue: Catalogue): string[] {
  const result = pack.special_rules.filter((rule) => rule.kind === "warband_skill"
    && recipientTypeMatches(rule, profile)
    && (!rule.eligibility?.length || rule.eligibility.includes(profile.id))
    && (!rule.applies_to?.profile_ids?.length || rule.applies_to.profile_ids.includes(profile.id))
    && (Boolean(rule.eligibility?.length || rule.applies_to?.profile_ids?.length) || (profile.skill_access ?? []).includes("special")))
    .map((rule) => rule.id);
  if (applicableRules(pack, profile).some((rule) => rule.runtime?.implemented === "YES"
    && rule.bindings?.some((binding) => binding.id === "compiler.slayer-skill-options"))) {
    const dwarf = catalogue.packages["chaos-streets-dwarf-treasure-hunters"];
    for (const rule of dwarf?.special_rules ?? []) if (rule.kind === "warband_skill" && rule.runtime?.implemented === "YES") result.push(rule.id);
  }
  return result.sort();
}

/** Configured abilities/mutations use the same recipients, independently of duel support. */
export function selectableRuleOptions(pack: BandPackage, profile: EditorialProfile): string[] {
  return pack.special_rules.filter((rule) => rule.kind !== "warband_skill" && rule.runtime?.grant === "selectable"
    && recipientTypeMatches(rule, profile)
    && (!rule.eligibility?.length || rule.eligibility.includes(profile.id))
    && (!rule.applies_to?.profile_ids?.length || rule.applies_to.profile_ids.includes(profile.id)))
    .map((rule) => rule.id).sort();
}

export function buildAccess(context: BuildContext): { equipment: string[]; skills: string[] } {
  const { build, profile, package: pack, catalogue, contracts, profile_bindings, compiler_bindings } = context;
  const equipment = new Set(profileEquipment(pack, profile, catalogue));
  const addLists = (lists: readonly EquipmentList[]) => {
    for (const list of lists) for (const item of list.items ?? []) {
      if (!entryReachesProfile(item, profile)) continue;
      const id = catalogue.mappings[item.item_id];
      if (id) equipment.add(id);
    }
  };
  if (contracts.includes("compiler.pirate-human-mercenary-equipment-access")) addLists(catalogue.foreign_packages["mercenaries"]?.equipment_lists ?? []);
  if (contracts.includes("compiler.foreign-or-native-background")) {
    const background = build.variant_ids.includes("background.native") || (!build.variant_ids.length && ["spirits", "jackals"].includes(profile.id)) ? "native" : "foreign";
    addLists(pack.equipment_lists.filter((list) => list.id === `${background}-${profile.id === "beloved" ? "beloved" : "undead"}-equipment-list`));
  }
  if (contracts.includes("compiler.knighthood") && build.variant_ids.includes("promotion.knight-errant")) {
    equipment.clear(); addLists(pack.equipment_lists.filter((list) => list.id === "knights-equipment-list"));
  }
  if (contracts.includes("compiler.follow-the-darkest-tribe") && build.variant_ids.includes("tribe.kurgan")) {
    for (const candidate of Object.values(catalogue.foreign_packages)) addLists(candidate.equipment_lists.filter((list) => list.items?.some((item) => item.item_id === "wolfcloak")));
  }
  if (contracts.includes("compiler.proven-warrior")) {
    const blackOrc = pack.profiles.find((row) => row.id === "black-orcs");
    addLists(pack.equipment_lists.filter((list) => blackOrc?.equipment_lists?.includes(list.id)));
  }
  if (contracts.includes("compiler.weapon-knowledge")) for (const id of Object.keys(catalogue.mechanics)) if (id.startsWith("weapon.")) equipment.add(id);
  const skills = new Set(profile.skill_access ?? []);
  // A promoted Hero is the configured copy (`configuredProfile`) or a build
  // that declares the promotion variant; the printed grant is conditional on
  // becoming a Hero, so an unpromoted Henchman never receives these tables.
  const promoted = profile.type === "hero" || build.variant_ids.includes("promotion.hero");
  for (const binding of profile_bindings) if (binding.id === "profile.skill-access") for (const value of strings(binding.parameters?.["category"])) skills.add(value);
  for (const binding of compiler_bindings) if (binding.id === "compiler.promoted-hero-skill-access" && promoted) for (const value of strings(binding.parameters?.["allowed_skill_lists"])) skills.add(value);
  if (contracts.includes("compiler.promoted-hero-no-strength-access")) for (const id of build.variant_ids) if (id.startsWith("skill-list.")) skills.add(id.slice(11));
  if (contracts.includes("compiler.slayer-skill-options")) for (const category of ["combat", "strength", "special"]) skills.add(category);
  if (contracts.includes("compiler.proven-warrior")) for (const category of ["combat", "shooting", "strength", "speed", "special"]) skills.add(category);
  if (contracts.includes("compiler.knighthood")) {
    const categories = build.variant_ids.includes("promotion.knight-errant") ? ["combat", "academic", "strength", "speed", "special"]
      : build.variant_ids.includes("promotion.squire") ? ["combat", "academic", "strength", "speed"] : [];
    for (const category of categories) skills.add(category);
  }
  return { equipment: Array.from(equipment).sort(), skills: Array.from(skills).sort() };
}

/** Preserve the desktop's legacy diagnostics while keeping its adapter free of rules. */
export function buildRestriction(context: BuildContext, stage: string): string | null {
  const { build: b, profile: p, package: pack, catalogue: c, contracts, profile_bindings, compiler_bindings } = context;
  const who = `${b.band_id}/${b.profile_id}`;
  const hands = [b.main_weapon_id, b.off_hand_id, b.extra_hand_id];
  const selected = [...hands, b.armour_id, ...b.defence_ids];
  const has = (id: string) => contracts.includes(id);
  const forbiddenSkills = (predicate: (id: string) => boolean) => b.skill_ids.filter(predicate).sort();
  const magic = (id: string) => id.includes("arcane") || id.includes("sorcery");
  // The compiler asks this before it compiles a build that chose no weapon at
  // all: the free dagger is then the engine's default, and a profile whose own
  // printed restriction refuses it fights with its natural attacks instead, the
  // same resolution an unequippable profile receives. Answering here keeps the
  // printed clause the single interpreter of the fallback.
  if (stage === "implicitWeapon") {
    if (b.main_weapon_id !== "weapon.dagger") return null;
    const facts = profileFactsProjection({ pack, profile: p, catalogue: c });
    const issue = equipmentIssue({ profile: facts, item_id: "weapon.dagger", item: carriedItemFacts(c, "weapon.dagger") });
    return issue && !issueIsInformational(issue.code) ? issue.message : null;
  }
  if (stage === "boundEquipment") {
    if (p.hireling_equipment) {
      try { resolveHirelingKit(p.hireling_equipment, b, c, pack.special_rules); }
      catch (error) { return error instanceof Error ? error.message : String(error); }
    }
    const profileFacts = profileFactsProjection({ pack, profile: p, catalogue: c });
    if (profileFacts.active_weapon_limit || profileFacts.active_weapon_forbids?.length
      || profileFacts.active_weapon_permits?.length) {
      const issues = activeWeaponIssues({ profile: profileFacts, items: catalogueItemFacts(c), skills: {},
        slots: { main_weapon_id: b.main_weapon_id, off_hand_id: b.off_hand_id ?? null, extra_hand_id: b.extra_hand_id ?? null } });
      if (issues.length) return issues[0]!.message;
    }
    const forbidden = profile_bindings.filter((binding) => binding.id === "profile.equipment-restrictions").flatMap((binding) => strings(binding.parameters?.["forbids"]));
    if (forbidden.includes("armour") && ((b.armour_id !== "armour.no-armour" || b.defence_ids.includes("defence.sea-dragon-cloak")) || containsAny(selected, ["defence.shield", "defence.buckler", "defence.helmet", "defence.cooking-pot-helmet"]))) return `armour is forbidden for ${who}`;
    if (forbidden.includes("ranged-weapons") && containsAny(selected, MISSILE_WEAPONS)) return `missile weapons are forbidden for ${who}`;
    if (forbidden.includes("heavy-armour") && HEAVY_ARMOUR.includes(b.armour_id)) return `heavy armour is forbidden for ${who}`;
    if (forbidden.includes("weapon.lance") && selected.includes("weapon.lance")) return `lance is forbidden for ${who}`;
    if (forbidden.includes("defence.helmet") && containsAny(selected, ["defence.helmet", "defence.cooking-pot-helmet"])) return `helmet is forbidden for ${who}`;
    // Every remaining token is decided by the same predicate the offering layer
    // uses, so a direct selection meets the same verdict as the offer: the
    // interpreted vocabulary plus the item and mechanic ids the printed clause
    // may name (`weapon.dagger`, `hook_hand`), including a bare catalogue id
    // such as `handgun` whose record publishes no mechanic. A token that names
    // no canonical item stays informational and never becomes a refusal.
    const sharedTokens = forbidden.filter((token) => !BOUND_STAGE_TOKENS.includes(token)
      && (INTERPRETED_TOKENS.includes(token) || token.includes(".") || carriedItemFacts(c, token) !== null));
    if (sharedTokens.length) for (const id of selected) {
      if (!id) continue;
      const issue = equipmentIssue({
        profile: { band_id: b.band_id ?? "custom", profile_id: p.id, fixed_equipment: [], equipment_access: null,
          equipment_forbids: sharedTokens, skill_access: [], skill_lists: [] },
        item_id: id, item: carriedItemFacts(c, id),
      });
      if (issue && !issueIsInformational(issue.code)) return issue.message;
    }
    return null;
  }
  if (stage === "categoryProhibitions") {
    if (has("compiler.no-missile-weapons") && containsAny(hands, MISSILE_WEAPONS)) return `missile weapons are forbidden for ${who}`;
    if (has("compiler.no-blackpowder-weapons") && containsAny(hands, BLACKPOWDER_WEAPONS)) return `blackpowder weapons are forbidden for ${who}`;
    if (has("compiler.strictures") && ["dragon-monks", "warrior-monks"].includes(p.id) && (b.armour_id !== "armour.no-armour" || b.defence_ids.includes("defence.sea-dragon-cloak"))) return "Dragon Monks and Warrior Monks may never wear armour";
    const categories = compiler_bindings.filter((binding) => binding.id === "compiler.forbid-item-categories").flatMap((binding) => strings(binding.parameters?.["categories"]));
    if (categories.includes("poison") && (b.main_poison_id || b.off_poison_id)) return `poisons are forbidden for ${who}`;
    if (categories.includes("drug") && containsAny(b.preparation_ids, DRUG_PREPARATIONS)) return `drugs are forbidden for ${who}`;
    return null;
  }
  if (stage === "requiredInitial") {
    if (has("compiler.sister-special-skills")) {
      const selected = b.special_rule_ids.filter(id => id.startsWith("band--special-skills-"));
      if (selected.length !== 2 || new Set(selected).size !== 2)
        return "Blessing of Sigmar requires exactly two distinct Sisters special skills";
    }
    if (has("compiler.mutant-requires-mutation-at-recruitment") && !b.special_rule_ids.some((id) => id.startsWith("band--mutations-"))) return `at least one mutation is required for ${who}`;
    if (has("compiler.nurgle-s-blessings") && !b.special_rule_ids.some((id) => id.startsWith("band--blessings-of-nurgle-"))) return "Tainted Ones require at least one Blessing of Nurgle";
    return null;
  }
  if (stage === "mutationLimit") return has("compiler.possessed-optional-zero-to-two-mutations-at-recruitment") && b.special_rule_ids.filter((id) => id.startsWith("band--mutations-")).length > 2 ? `at most two mutations are allowed for ${who}` : null;
  if (stage === "initialChoices") {
    const count = b.special_rule_ids.filter((id) => id.startsWith("band--mutations-")).length;
    return has("compiler.mutation-purchase-at-recruitment") && count && !["mutants", "the-possessed"].includes(p.id)
      ? `mutations are available only to Mutants and the Possessed: ${who}` : null;
  }
  if (stage === "profileTail") return profileTail(context);
  if (stage !== "profileSelections") throw new Error(`unknown eligibility stage: ${stage}`);
  if (has("compiler.foreign-or-native-background")) {
    const native = b.variant_ids.includes("background.native") || (!b.variant_ids.length && ["spirits", "jackals"].includes(p.id));
    if (["blood-slaves", "black-hounds"].includes(p.id) && native) return `${p.id} requires the Foreign background`;
    if (["spirits", "jackals"].includes(p.id) && !native) return `${p.id} requires the Native background`;
  }
  if (has("compiler.knighthood") && b.variant_ids.filter((id) => ["promotion.squire", "promotion.knight-errant"].includes(id)).length > 1) return "choose at most one Knighthood promotion";
  if (has("compiler.proven-warrior") && p.id !== "younguns") return "Proven Warrior may only be selected by a Young'un";
  const equipment = new Set([b.main_weapon_id, b.armour_id, ...b.defence_ids]);
  if (b.off_hand_id) equipment.add(b.off_hand_id);
  if (b.main_material_id !== "material.normal") equipment.add(b.main_material_id);
  if (b.off_hand_id && b.off_material_id !== "material.normal") equipment.add(b.off_material_id);
  for (const id of ["armour.no-armour", "weapon.natural-attacks", "weapon.fist"]) equipment.delete(id);
  const knight = (p.rule_ids ?? []).some((id) => id.endsWith("--knight")) || b.variant_ids.includes("promotion.knight-errant");
  if (has("compiler.powder-s-expensive") && p.type !== "hero" && containsAny(hands, BLACKPOWDER_WEAPONS)) return `blackpowder weapons are forbidden for Bandit Henchmen: ${who}`;
  if (has("compiler.chivalry") && knight) {
    if (containsAny(hands, MISSILE_WEAPONS)) return `missile weapons are forbidden for Knights: ${who}`;
    if (b.main_poison_id || b.off_poison_id) return `poisons are forbidden for Knights: ${who}`;
    if (containsAny(b.preparation_ids, DRUG_PREPARATIONS)) return `drugs are forbidden for Knights: ${who}`;
  }
  if (has("compiler.haughty") && containsAny(equipment, ["material.gromril", "material.obsidian", "armour.gromril-armour"])) return `Dwarf-made equipment is forbidden for ${who}`;
  if (has("compiler.chaos-engineer") && Array.from(equipment).some((id) => id.includes("chaos"))) return `Chaos armour is forbidden for ${who}`;
  if (has("compiler.saurus-skill-prohibitions") && ["saurus-totem-warrior", "saurus-braves"].includes(p.id) && containsAny(hands, MISSILE_WEAPONS)) return "missile weapons are forbidden for Saurus";
  const access = buildAccess(context);
  const neutralProfile: ProfileFacts = {
    band_id: b.band_id ?? "custom", profile_id: p.id, fixed_equipment: [], equipment_forbids: [],
    equipment_access: access.equipment.map((item_id) => ({ item_id })), skill_access: access.skills,
    skill_lists: profileSkillLists(pack, p).length ? profileSkillLists(pack, p) : [{ rule_id: p.id, category: "special", skills: Object.values(c.skills).filter((skill) =>
      (skill.source_refs ?? []).some((ref) => [b.band_id, pack.band.canonical_family].some((band) => band && (ref.url ?? "").includes(`/${band}`))))
      .map((skill) => skill.id) }],
  };
  const illegal = Array.from(equipment).filter((id) => equipmentIssue({ profile: neutralProfile,
    item_id: id, item: { kind: "", mechanic_id: id, tags: [] } })?.code === "equipment_not_permitted").sort();
  if (illegal.length) return `equipment is not available to ${who}: ${pythonList(illegal)}`;
  const promoted = b.variant_ids.filter((id) => id.startsWith("skill-list.")).map((id) => id.slice(11));
  if (has("compiler.promoted-hero-no-strength-access")) {
    if (promoted.includes("strength")) return `Strength skill list is forbidden for ${who}`;
    if (promoted.length > 2) return "a promoted Hero may choose at most two skill lists";
  }
  if (has("compiler.saurus-skill-prohibitions") && ["saurus-totem-warrior", "saurus-braves"].includes(p.id)) {
    const ids = forbiddenSkills((id) => c.skills[id]?.category === "academic");
    if (ids.length) return `Academic skills are forbidden for Saurus: ${pythonList(ids)}`;
  }
  for (const [contract, text] of [
    ["compiler.disciple-of-sigmar", `sorcery and Arcane Lore are forbidden for ${who}`],
    ["compiler.swabbie-rabble-loadout", "magic is forbidden for Swabbies"],
    ["compiler.no-arcane-lore", `Arcane Lore is forbidden for ${who}`],
  ] as const) {
    const ids = forbiddenSkills(magic);
    if (has(contract) && ids.length) return `${text}: ${pythonList(ids)}`;
  }
  if (has("compiler.promoted-hero-no-strength-access")) {
    const ids = forbiddenSkills((id) => c.skills[id]?.category === "strength");
    if (ids.length) return `Strength skills are forbidden for ${who}: ${pythonList(ids)}`;
  }
  const banned = compiler_bindings.filter((binding) => binding.id === "compiler.forbid-skill-categories").flatMap((binding) => strings(binding.parameters?.["categories"]));
  const forbidden = forbiddenSkills((id) => banned.includes(c.skills[id]?.category ?? ""));
  if (forbidden.length) return `skills are forbidden for ${who}: ${pythonList(forbidden)}`;
  const illegalSkills = forbiddenSkills((id) => {
    const skill = c.skills[id];
    return !skill || skillIssue(neutralProfile, skill, true) !== null;
  });
  if (illegalSkills.length) return `skills are not available to ${who}: ${pythonList(illegalSkills)}`;
  if (has("compiler.knighthood") && new Set(b.skill_ids.map((id) => c.skills[id]?.category).filter((category) => category !== "special")).size > 2) return "a promoted Squire may use at most two ordinary skill lists";
  const restrictions = (p.equipment_restrictions ?? []).join(" ").toLowerCase();
  if (["never wear armour", "cannot wear armour", "armour is not allowed", "does not allow armour", "using any armour", "non-armour items", "do not wear armour", "any form of armour", "do not use weapons or wear armour", "never use weapons or armour", "cannot use normal equipment"].some((text) => restrictions.includes(text)) && (b.armour_id !== "armour.no-armour" || b.defence_ids.includes("defence.sea-dragon-cloak"))) return `armour is forbidden for ${who}`;
  if ((restrictions.includes("may not use an off-hand weapon") || restrictions.includes("must use one hand")) && b.off_hand_id) return `off-hand equipment is forbidden for ${who}`;
  if ((restrictions.includes("may not use double-handed weapons") || restrictions.includes("double-handed weapons are for")) && c.mechanics[b.main_weapon_id]?.["hands"] === 2 && !has("compiler.proven-warrior")) return `two-handed weapons are forbidden for ${who}`;
  return null;
}

function profileTail(context: BuildContext): string | null {
  const { build: b, profile: p, contracts } = context;
  const has = (id: string) => contracts.includes(id);
  const forbiddenSkills = (predicate: (id: string) => boolean) => b.skill_ids.filter(predicate).sort();
  const magic = (id: string) => id.includes("arcane") || id.includes("sorcery");
  if (has("compiler.sacred-marks") && b.special_rule_ids.filter((id) => id.startsWith("band--sacred-mark-")).length > 1) return "a Lizardman Hero may have at most one Sacred Mark";
  if (has("compiler.tracker-gear") && !["rope_hook", "bolas"].every((id) => (p.fixed_equipment ?? []).includes(id))) return "Trackers must begin with Rope and Hook and Bolas";
  if (has("compiler.vampiric-powers")) {
    const bloodline = p.id.endsWith("-vampire") ? p.id.slice(0, -8) : p.id;
    const foreign = b.special_rule_ids.filter((id) => id.includes("-power-") && !id.includes(`band--${bloodline}-power-`));
    if (foreign.length) return `Vampiric Powers must belong to the Vampire's bloodline: ${pythonList(foreign)}`;
  }
  if (has("compiler.warrior-s-code")) {
    const magicalSkills = forbiddenSkills((id) => magic(id) || id.includes("magic"));
    if (magicalSkills.length) return `magic is forbidden by the Warrior's Code: ${pythonList(magicalSkills)}`;
    const magical = b.special_rule_ids.filter((id) => ["spell", "magic", "arcane"].some((word) => id.includes(word))).sort();
    if (magical.length) return `magic is forbidden by the Warrior's Code: ${pythonList(magical)}`;
  }
  if (has("compiler.follow-the-darkest-tribe") && b.variant_ids.filter((id) => ["tribe.norse", "tribe.kurgan", "tribe.hung"].includes(id)).length > 1) return "choose exactly one Marauder tribe";
  if (has("compiler.foreign-or-native-background") && b.variant_ids.filter((id) => ["background.foreign", "background.native"].includes(id)).length > 1) return "choose exactly one Foreign or Native background";
  return null;
}

/* ------------------------------------------------------------------ *
 * Shared construction context and batch queries (centralization plan §2).
 *
 * Adapters supply plain facts; this layer interprets their rule meaning and
 * returns one decision per proposal. Campaign consumers project their current
 * warrior selections here instead of building a synthetic duel fighter, and
 * duel consumers project the loadout slots they actually compile.
 * ------------------------------------------------------------------ */

/** One selectable entry the context offers, with the canonical facts it needs. */
export interface ContextSelectionFacts {
  /** Stable knowledge-base id of the entry (`weapon.sword`, `skill.dodge`). */
  readonly id: string;
  readonly category?: string;
  readonly kind?: string;
  /** Hand slots the entry occupies when it is selected (`1` or `2`). */
  readonly hands?: number | null;
  /** The entry needs both hands at once, independently of `hands`. */
  readonly paired?: boolean;
  readonly item?: ItemFacts | null;
  readonly skill?: SkillFacts | null;
}

/**
 * Neutral construction context. It carries facts only: no campaign document,
 * no combat engine object and no UI state. `proposals`-style operations below
 * read it, so a browser adapter and the Python transport can build the same
 * shape from their own sources.
 */
export interface ConstructionContext {
  readonly profile: ProfileFacts;
  /** Lookup facts by stable id; membership does not imply selection or ownership. */
  readonly items: Readonly<Record<string, ItemFacts | null>>;
  /** Canonical skills of the current selections, by stable id. */
  readonly skills: Readonly<Record<string, SkillFacts>>;
  /** Entries the operation may select, so options can be offered and checked. */
  readonly selections?: readonly ContextSelectionFacts[];
  /** Band-wide prohibition tokens, already projected by the adapter. */
  readonly band_forbids?: readonly string[];
  readonly active_lists?: readonly string[];
  readonly gated_lists?: readonly string[];
  readonly limits?: EquipmentLimits | null;
  /**
   * Equipment ownership and active duel equipment are different contexts.
   * `possession` lists every item the member owns; the loadout slots below
   * describe the equipment active in this operation.
   */
  readonly possession?: readonly string[];
  readonly slots?: ConstructionSlots;
  readonly operation?: ConstructionOperationContext;
}

/** Active hand slots, armour and accessories of a loadout operation. */
export interface ConstructionSlots {
  readonly main_weapon_id?: string | null;
  readonly off_hand_id?: string | null;
  readonly extra_hand_id?: string | null;
  readonly armour_id?: string | null;
  readonly defence_ids?: readonly string[];
  readonly material_id?: string | null;
  /** Poison active on the main-hand weapon, when a consumer supplies one. */
  readonly main_poison_id?: string | null;
  /** Poison active on the off-hand weapon, when a consumer supplies one. */
  readonly off_poison_id?: string | null;
}

/**
 * Operation context that preserves the established consumer contracts. A
 * manual skill correction, a rolled advance, a campaign purchase and a duel
 * loadout reach the same primitives with different declared facts.
 */
export interface ConstructionOperationContext {
  /** Supplied mounted state of an active loadout, independent of ownership. */
  readonly mounted?: boolean;
  /** Consumer asking for the decision (`combat-lab`, `warband-manager`). */
  readonly product?: string;
  /** A manual correction keeps its documented access convention. */
  readonly manual_skill_change?: boolean;
  /** An advance was rolled, not chosen by hand. */
  readonly advance?: boolean;
  /** A free build keeps its permissive access behaviour. */
  readonly free_build?: boolean;
  /** Skill categories the profile may never acquire (implemented rules). */
  readonly banned_skill_categories?: readonly string[];
  /**
   * Tokens or item ids that lift the two-hand loadout restriction (for
   * example Arms Master / Master of Arms), already resolved by the adapter.
   */
  readonly ignores_hand_restrictions?: readonly string[];
  /**
   * The operation needs owned quantities (`possession`); it does not import
   * campaign state, it only receives the projected counts.
   */
  readonly quantities?: Readonly<Record<string, number>>;
}

/** Kind of change a proposal describes. */
export type SelectionProposalKind = "add" | "remove" | "replace";

/** One proposed addition, replacement or removal. */
export interface SelectionProposal {
  readonly kind: SelectionProposalKind;
  /** Entry being added, replacing or removed. */
  readonly id: string;
  /** Entry the proposal replaces, when `kind` is `replace`. */
  readonly replaces_id?: string;
  /** Family the proposal belongs to; the shared module never guesses it. */
  readonly selection?: "equipment" | "skill";
  /** Skill table of the entry (`combat`, `special`…), when it is a skill. */
  readonly category?: string;
  /** Hand slot the added entry occupies (`main` or `off`). */
  readonly slot?: "main" | "off" | "extra";
  readonly quantity?: number;
  readonly item?: ItemFacts | null;
  readonly skill?: SkillFacts | null;
}

/** One decision, aligned by index with the proposal that produced it. */
export interface SelectionDecision {
  readonly allowed: boolean;
  /** Blocking issues, in the module's established order. */
  readonly issues: readonly EligibilityIssue[];
  /** Knowledge reports that must stay visible without blocking the choice. */
  readonly reports: readonly EligibilityIssue[];
  /** The proposal this decision answers. */
  readonly proposal: SelectionProposal;
}

function selectionFactsOf(context: ConstructionContext, id: string): ContextSelectionFacts | null {
  return (context.selections ?? []).find((entry) => entry.id === id) ?? null;
}

function handsOf(context: ConstructionContext, entry: ContextSelectionFacts | null, id: string): number {
  if (entry?.paired) return 2;
  if (typeof entry?.hands === "number") return entry.hands;
  const item = entry?.item ?? context.items[id];
  if (!item) return 1;
  const facts = (item as unknown as { readonly hands?: number | null }).hands;
  return typeof facts === "number" ? facts : 1;
}

function ignoresHandRestrictions(context: ConstructionContext): boolean {
  return (context.operation?.ignores_hand_restrictions ?? []).length > 0;
}

function activeLoadout(context: ConstructionContext): string[] {
  const slots = context.slots;
  if (!slots) return [];
  return [slots.main_weapon_id, slots.off_hand_id, slots.extra_hand_id, slots.armour_id,
    ...(slots.defence_ids ?? [])].filter((id): id is string => Boolean(id) && id !== "armour.no-armour");
}

/** Count occupied weapon positions, including two copies of the same weapon. */
function activeWeaponIssues(context: ConstructionContext): EligibilityIssue[] {
  for (const restriction of context.profile.active_weapon_forbids ?? []) {
    for (const id of [context.slots?.main_weapon_id, context.slots?.off_hand_id, context.slots?.extra_hand_id]) {
      if (!id || NEUTRAL_ITEM_IDS.includes(id)) continue;
      if (restriction.forbids.some(token => tokenForbids(token, id, itemFactsFor(context, id))))
        return [{ code: "equipment_forbidden", rule_id: restriction.rule_id,
          subject_ids: [context.profile.band_id, context.profile.profile_id, id],
          message: `${id} may not be used by ${context.profile.band_id}/${context.profile.profile_id}.` }];
    }
  }
  // A printed permission bounds the weapon the warrior *uses*, so it is read on
  // the active positions only: the same item may stay in the kit untouched.
  for (const restriction of context.profile.active_weapon_permits ?? []) {
    for (const id of [context.slots?.main_weapon_id, context.slots?.off_hand_id, context.slots?.extra_hand_id]) {
      if (!id || NEUTRAL_ITEM_IDS.includes(id)) continue;
      if (restriction.permits.some(token => tokenPermits(token, id, itemFactsFor(context, id)))) continue;
      return [{ code: "equipment_forbidden", rule_id: restriction.rule_id,
        subject_ids: [context.profile.band_id, context.profile.profile_id, id],
        message: `${id} may not be used by ${context.profile.band_id}/${context.profile.profile_id}; the printed clause admits only ${restriction.permits.join(", ")}.` }];
    }
  }
  if (context.slots) {
    const mechanic = (id: string | null | undefined) => id ? itemFactsFor(context, id)?.mechanic_id ?? id : null;
    const cloakIssue = cloakArmourRestriction({ ...buildFactsOf(context),
      armour_id: mechanic(context.slots.armour_id) ?? "armour.no-armour",
      defence_ids: (context.slots.defence_ids ?? []).map(id => mechanic(id) ?? id) });
    if (cloakIssue) return [{ code: "equipment_combination_forbidden",
      subject_ids: [context.profile.band_id, context.profile.profile_id], message: cloakIssue }];
    const message = skullBustaRestriction({ ...buildFactsOf(context),
      main_weapon_id: mechanic(context.slots.main_weapon_id) ?? "weapon.fist",
      off_hand_id: mechanic(context.slots.off_hand_id), extra_hand_id: mechanic(context.slots.extra_hand_id) });
    if (message) return [{ code: "equipment_combination_forbidden",
      subject_ids: [context.profile.band_id, context.profile.profile_id, "weapon.skull-busta"], message }];
  }
  const hellblade = hellbladeRestriction(buildFactsOf(context));
  if (hellblade) return [{ code: "equipment_combination_forbidden",
    subject_ids: ["weapon.hellblade"], message: hellblade }];
  // A poison's printed application condition is read on the active loadout: the
  // weapon it coats supplies the kind, the bearer's facts the admitted kinds.
  for (const [weaponKey, poisonKey] of [
    ["main_weapon_id", "main_poison_id"], ["off_hand_id", "off_poison_id"],
  ] as const) {
    const poisonId = context.slots?.[poisonKey];
    const weaponId = context.slots?.[weaponKey];
    if (!poisonId || !weaponId || NEUTRAL_ITEM_IDS.includes(weaponId)) continue;
    const poisonIssue = poisonApplicationIssue({ profile: context.profile, poison_id: poisonId,
      poison: itemFactsFor(context, poisonId), weapon_id: weaponId, weapon: itemFactsFor(context, weaponId) });
    if (poisonIssue) return [poisonIssue];
  }
  const limit = context.profile.active_weapon_limit;
  if (!limit || !context.slots) return [];
  const weapons = [context.slots.main_weapon_id, context.slots.off_hand_id, context.slots.extra_hand_id]
    .filter((id): id is string => Boolean(id) && id !== "weapon.fist")
    .filter((id) => {
      const item = itemFactsFor(context, id);
      return (item?.mechanic_id?.startsWith("weapon.") || item?.kind === "close-combat-weapon" || item?.kind === "weapon")
        && handsOf(context, selectionFactsOf(context, id), id) === 1;
    });
  return weapons.length > limit.maximum ? [{ code: "equipment_limit_exceeded", rule_id: limit.rule_id,
    subject_ids: [context.profile.band_id, context.profile.profile_id, ...weapons],
    message: `${context.profile.band_id}/${context.profile.profile_id} may use at most ${limit.maximum} one-handed weapon at a time.` }] : [];
}

function itemFactsFor(context: ConstructionContext, id: string, explicit?: ItemFacts | null): ItemFacts | null {
  if (explicit !== undefined) return explicit;
  return context.items[id] ?? null;
}

function skillFactsFor(context: ConstructionContext, id: string, explicit?: SkillFacts | null): SkillFacts | null {
  if (explicit !== undefined) return explicit;
  return context.skills[id] ?? selectionFactsOf(context, id)?.skill ?? null;
}

/** Shared verdict for one equipment proposal. */
function equipmentProposalIssues(context: ConstructionContext, proposal: SelectionProposal): EligibilityIssue[] {
  const entry = selectionFactsOf(context, proposal.id);
  const issues: EligibilityIssue[] = [];
  const issue = equipmentIssue({
    profile: context.profile,
    item_id: proposal.id,
    item: itemFactsFor(context, proposal.id, proposal.item),
    band_forbids: context.band_forbids ?? [],
    active_lists: context.active_lists ?? [],
    gated_lists: context.gated_lists ?? [],
  });
  if (issue) issues.push(issue);
  const slots = context.slots;
  const mechanic = itemFactsFor(context, proposal.id, proposal.item)?.mechanic_id ?? proposal.id;
  if (slots && (mechanic === "defence.sea-dragon-cloak" || mechanic.startsWith("armour."))) {
    const resolve = (id: string) => itemFactsFor(context, id)?.mechanic_id ?? id;
    const message = cloakArmourRestriction({ ...buildFactsOf(context),
      armour_id: mechanic.startsWith("armour.") ? mechanic : resolve(slots.armour_id ?? "armour.no-armour"),
      defence_ids: [...(slots.defence_ids ?? []).filter(id => id !== proposal.replaces_id).map(resolve),
        ...(mechanic === "defence.sea-dragon-cloak" ? [mechanic] : [])] });
    if (message) issues.push({ code: "equipment_combination_forbidden",
      subject_ids: [context.profile.band_id, context.profile.profile_id, proposal.id], message });
  }
  if (slots && proposal.kind === "add" && proposal.slot !== "main") {
    const main = slots.main_weapon_id ?? "";
    const mainEntry = selectionFactsOf(context, main);
    const occupiesBothHands = main !== "" && handsOf(context, mainEntry, main) === 2;
    const off = slots.off_hand_id ?? "";
    if (occupiesBothHands && !ignoresHandRestrictions(context) && proposal.slot === "off") {
      issues.push({
        code: "equipment_slot_occupied", subject_ids: [context.profile.band_id, context.profile.profile_id, main, proposal.id],
        message: `The main weapon ${main} occupies both hands of ${context.profile.band_id}/${context.profile.profile_id}.`,
      });
    }
    if (proposal.slot === "off" && off !== "" && off !== proposal.id && !ignoresHandRestrictions(context)) {
      issues.push({
        code: "equipment_slot_occupied", subject_ids: [context.profile.band_id, context.profile.profile_id, off, proposal.id],
        message: `The off hand of ${context.profile.band_id}/${context.profile.profile_id} already holds ${off}.`,
      });
    }
  }
  if (slots && (proposal.kind === "replace" || proposal.slot === "main")) {
    const other = slots.off_hand_id ?? "";
    if (other !== "" && other !== proposal.id && !ignoresHandRestrictions(context)) {
      // The combination table is keyed by canonical mechanics, so the shared
      // module resolves the mechanic itself instead of trusting a caller id.
      const mechanic = itemFactsFor(context, proposal.id, proposal.item)?.mechanic_id ?? proposal.id;
      const otherMechanic = itemFactsFor(context, other)?.mechanic_id ?? other;
      const combination = loadoutRestriction({
        build: { ...buildFactsOf(context, mechanic), off_hand_id: otherMechanic },
        main_weapon: { main_hand: true, hands: handsOf(context, entry, proposal.id), paired: Boolean(entry?.paired) },
        off_weapon: { off_hand: true },
        contracts: [], selected_mechanics: [], stage: "hands",
      });
      if (combination) issues.push({
        code: "equipment_combination_forbidden", subject_ids: [context.profile.band_id, context.profile.profile_id, proposal.id, other],
        message: combination,
      });
    }
  }
  if (slots && (proposal.kind === "add" || proposal.kind === "replace")) {
    if (proposal.slot === "main" || proposal.slot === "off" || proposal.slot === "extra") {
      const key = proposal.slot === "main" ? "main_weapon_id" : proposal.slot === "off" ? "off_hand_id" : "extra_hand_id";
      issues.push(...activeWeaponIssues({ ...context, slots: { ...slots, [key]: proposal.id } }));
    }
    const result = activeLoadout(context).filter((id) => id !== (proposal.replaces_id ?? "")).concat(proposal.id);
    const known = result.filter((id) => id !== "" && (itemFactsFor(context, id, id === proposal.id ? proposal.item : undefined) !== null
      || selectionFactsOf(context, id) !== null));
    // Duplicate copies travel: two identical one-handed weapons in the two hand
    // slots are two rows of the set, which is what a copy bound counts.
    for (const setIssue of equipmentSetIssues({
      profile: context.profile, limits: context.limits ?? null,
      items: known.map((item_id) => ({ item_id, item: itemFactsFor(context, item_id) })),
    })) issues.push(setIssue);
  }
  return issues;
}

function buildFactsOf(context: ConstructionContext, mainWeaponId?: string): BuildFacts {
  const slots = context.slots ?? {};
  return {
    mounted: context.operation?.mounted ?? false,
    band_id: context.profile.band_id, profile_id: context.profile.profile_id,
    main_weapon_id: mainWeaponId ?? slots.main_weapon_id ?? "weapon.fist",
    armour_id: slots.armour_id ?? "armour.no-armour",
    off_hand_id: slots.off_hand_id ?? null, extra_hand_id: slots.extra_hand_id ?? null,
    main_material_id: slots.material_id ?? "material.normal", off_material_id: "material.normal",
    main_poison_id: slots.main_poison_id ?? null, off_poison_id: slots.off_poison_id ?? null,
    defence_ids: slots.defence_ids ?? [],
    skill_ids: Object.keys(context.skills), preparation_ids: [], special_rule_ids: [], variant_ids: [],
  };
}

/** Shared verdict for one skill proposal. */
function skillProposalIssues(context: ConstructionContext, proposal: SelectionProposal): EligibilityIssue[] {
  const entry = selectionFactsOf(context, proposal.id);
  const skill = skillFactsFor(context, proposal.id, proposal.skill);
  const category = skill?.category ?? entry?.category ?? proposal.category ?? "";
  const strict = context.operation?.manual_skill_change === true || context.operation?.advance === true;
  const issues: EligibilityIssue[] = [];
  const facts: SkillFacts = skill ?? { id: proposal.id, category, kind: entry?.kind ?? "skill" };
  const issue = skillIssue(context.profile, facts, strict);
  if (issue) issues.push(issue);
  const banned = context.operation?.banned_skill_categories ?? [];
  // An implemented prohibition rule reports once: the access verdict above
  // already carries the same code, and a selector must not show two motives.
  const alreadyRefused = issues.some((entry) => entry.code === "skill_not_permitted");
  if (banned.includes(category) && !alreadyRefused) issues.push({
    code: "skill_not_permitted", subject_ids: [context.profile.band_id, context.profile.profile_id, proposal.id],
    message: `"${proposal.id}" (${category}) is forbidden for ${context.profile.band_id}/${context.profile.profile_id} by an implemented rule.`,
  });
  return issues;
}

function selectionIssues(context: ConstructionContext, proposal: SelectionProposal): EligibilityIssue[] {
  if (proposal.kind === "remove") return [];
  const entry = selectionFactsOf(context, proposal.id);
  const isSkill = proposal.selection === "skill"
    || (proposal.selection === undefined && (entry?.skill !== undefined || context.skills[proposal.id] !== undefined));
  return isSkill ? skillProposalIssues(context, proposal) : equipmentProposalIssues(context, proposal);
}

/**
 * Evaluate proposed additions, replacements or removals in one batch.
 *
 * The caller submits every candidate of a comparison at once: the shared
 * module owns the rule meaning and the caller keeps the transport cost of a
 * single call. `remove` never produces a blocking issue — the plan keeps an
 * invalid existing selection visible and removable.
 */
export function selectionDecisions(
  context: ConstructionContext,
  proposals: readonly SelectionProposal[],
): readonly SelectionDecision[] {
  return proposals.map((proposal) => {
    const issues = selectionIssues(context, proposal);
    return {
      proposal,
      allowed: issues.every((issue) => issueIsInformational(issue.code)),
      issues: issues.filter((issue) => !issueIsInformational(issue.code)),
      reports: issues.filter((issue) => issueIsInformational(issue.code)),
    };
  });
}

/**
 * Evaluate the complete resulting configuration before confirmation.
 *
 * Unlike `selectionDecisions`, an unrelated unfinished requirement does not
 * disable an option here: this operation judges the whole configuration,
 * including the mandatory choices and whole-set limits a draft may still be
 * completing. The `draft` flag permits unfinished mandatory choices so a
 * selector can keep offering the missing option; confirmation checks them.
 */
export function validateConstruction(
  context: ConstructionContext,
  options: { readonly draft?: boolean } = {},
): readonly EligibilityIssue[] {
  const issues: EligibilityIssue[] = [...activeWeaponIssues(context)];
  // The complete configuration is every declared selection plus the active
  // loadout and the owned copies: a whole-set limit must see the resulting kit,
  // never one slot in isolation.
  const declared = [
    ...(context.selections ?? []).filter((entry) => entry.kind !== "skill" && !entry.skill).map((entry) => entry.id),
    ...activeLoadout(context),
  ];
  const possession = context.possession ?? [];
  const ids = Array.from(new Set([...declared, ...possession]));
  for (const id of ids) {
    const item = itemFactsFor(context, id);
    const issue = equipmentIssue({
      profile: context.profile, item_id: id, item,
      band_forbids: context.band_forbids ?? [],
      active_lists: context.active_lists ?? [], gated_lists: context.gated_lists ?? [],
    });
    if (issue) issues.push(issue);
  }
  for (const id of Object.keys(context.skills)) {
    const skill = context.skills[id];
    if (!skill) continue;
    const strict = context.operation?.manual_skill_change === true || context.operation?.advance === true;
    const issue = skillIssue(context.profile, skill, strict);
    if (issue) issues.push(issue);
  }
  // Ownership and the active loadout are different counts of the same kit: the
  // copies of one item are the larger of what is declared and what is owned
  // (two identical hammers in the two hands are two copies; one hammer both
  // wielded and owned is one), and an id only owned is counted per owned copy.
  const occurrences = (ids: readonly string[]): Map<string, number> => {
    const counts = new Map<string, number>();
    for (const id of ids) counts.set(id, (counts.get(id) ?? 0) + 1);
    return counts;
  };
  const declaredCounts = occurrences(declared);
  const ownedCounts = occurrences(possession);
  const setIds: string[] = [];
  for (const id of new Set([...declaredCounts.keys(), ...ownedCounts.keys()])) {
    const copies = Math.max(declaredCounts.get(id) ?? 0, ownedCounts.get(id) ?? 0);
    for (let index = 0; index < copies; index += 1) setIds.push(id);
  }
  const setItems = setIds.map((item_id) => ({ item_id, item: itemFactsFor(context, item_id) }));
  for (const issue of equipmentSetIssues({ profile: context.profile, limits: context.limits ?? null, items: setItems })) {
    if (options.draft && issue.code === "equipment_required_missing") continue;
    issues.push(issue);
  }
  return issues;
}

/* ------------------------------------------------------------------ *
 * Shared fact projection (centralization plan §2).
 *
 * Both adapters already read canonical YAML, but interpreting a rule's
 * bindings into the fact shape is rule meaning, not fact reading. These two
 * functions are the single interpretation: the browser artefact and the
 * Python transport call them instead of each walking `runtime.effects`.
 * ------------------------------------------------------------------ */

/** Bindings of every applicable rule of one profile, flattened in rule order. */
export function profileBindings(pack: BandPackage, profile: EditorialProfile): readonly Binding[] {
  return applicableRules(pack, profile).flatMap((rule) => rule.bindings ?? []);
}

/**
 * Bindings carried by the rules a consumer has selected.
 *
 * An adapter that already knows which rules the user chose must not read the
 * bindings itself: the rule meaning stays here, and the adapter only maps the
 * returned ids onto its own presentation.
 */
export function selectedRuleBindings(
  pack: BandPackage, rule_ids: readonly string[], catalogue?: Catalogue | null,
): readonly Binding[] {
  const byId = new Map<string, EditorialRule>();
  for (const rule of pack.special_rules) byId.set(rule.id, rule);
  for (const candidate of Object.values(catalogue?.packages ?? {})) {
    for (const rule of candidate.special_rules) if (!byId.has(rule.id)) byId.set(rule.id, rule);
  }
  for (const rule of Object.values(catalogue?.free_rules ?? {})) if (!byId.has(rule.id)) byId.set(rule.id, rule);
  return rule_ids.flatMap((id) => byId.get(id)?.bindings ?? []);
}

/**
 * `ProfileFacts` of one profile, from canonical bindings only.
 *
 * The projection reads: the profile's own declared access, the prohibition
 * tokens of its `profile.equipment-restrictions` bindings, the bounded special
 * skill lists of its `profile.skill-access` bindings and the whole-set limits
 * of the applicable band rules. A token or parameter that arrived malformed is
 * reported, never guessed.
 */
export function profileFactsProjection(args: {
  readonly pack: BandPackage;
  readonly profile: EditorialProfile;
  readonly band_id?: string;
  readonly catalogue?: Catalogue | null;
}): ProfileFacts {
  const { pack, profile } = args;
  const bandId = args.band_id ?? pack.band.id;
  const forbids: string[] = [];
  const skillLists: { rule_id: string; category: string; skills: readonly string[] }[] = [];
  const promotionSkills: string[] = [];
  let activeWeaponLimit: ProfileFacts["active_weapon_limit"];
  const activeWeaponForbids: NonNullable<ProfileFacts["active_weapon_forbids"]>[number][] = [];
  const activeWeaponPermits: NonNullable<ProfileFacts["active_weapon_permits"]>[number][] = [];
  const requiredEquipment: RequiredEquipment[] = [];
  const poisonApplication: PoisonApplication[] = [];
  const missileWeaponLimit: MissileWeaponLimit[] = [];
  for (const rule of applicableRules(pack, profile)) for (const binding of rule.bindings ?? []) {
    if (binding.id === "compiler.promoted-hero-skill-access" && rule.runtime?.implemented === "YES") {
      for (const category of strings(binding.parameters?.["allowed_skill_lists"])) {
        if (!promotionSkills.includes(category)) promotionSkills.push(category);
      }
    }
    if (binding.id === "profile.active-weapon-restrictions") {
      // A permission clause ('may only use a sword, dagger or Mage Staff in
      // battle') carries no prohibition token: it is projected only as the
      // permitted set, never as an empty `forbids` row a consumer could read.
      const forbidden = strings(binding.parameters?.["forbids"]);
      if (forbidden.length) activeWeaponForbids.push({ rule_id: rule.id, forbids: forbidden });
      const permits = strings(binding.parameters?.["allowed_kinds"]);
      if (permits.length) activeWeaponPermits.push({ rule_id: rule.id, permits });
    }
    if (binding.id === "profile.equipment-restrictions") {
      const maximum = binding.parameters?.["max_active_one_handed_weapons"];
      if (maximum !== undefined) {
        if (typeof maximum !== "number" || !Number.isInteger(maximum) || maximum < 0) throw new Error("invalid active one-handed weapon limit");
        if (!activeWeaponLimit || maximum < activeWeaponLimit.maximum) activeWeaponLimit = { rule_id: rule.id, maximum };
      }
      for (const token of strings(binding.parameters?.["forbids"])) {
        const trimmed = token.trim();
        // Generator defect (list-valued `forbids` stringified): report, never guess a list.
        if (trimmed && !trimmed.startsWith("[") && !forbids.includes(trimmed)) forbids.push(trimmed);
      }
      const kinds = strings(binding.parameters?.["required_kinds"]);
      if (kinds.length) requiredEquipment.push({ rule_id: rule.id, kinds,
        excludes: strings(binding.parameters?.["required_excludes"]) });
      const governedPoisons = strings(binding.parameters?.["poisons"]);
      if (governedPoisons.length) poisonApplication.push({ rule_id: rule.id, poisons: governedPoisons,
        weapon_kinds: strings(binding.parameters?.["weapon_kinds"]) });
      // A band-wide missile bound belongs to `bandEquipmentLimits`; only a rule
      // granted to the profile itself states a bound of that profile's clause.
      const missileMaximum = binding.parameters?.["max_missile_weapons"];
      if (rule.runtime?.grant !== "band" && missileMaximum !== undefined) {
        if (typeof missileMaximum !== "number" || !Number.isInteger(missileMaximum) || missileMaximum < 0)
          throw new Error("invalid missile weapon limit");
        missileWeaponLimit.push({ rule_id: rule.id, maximum: missileMaximum,
          exempt_item_ids: strings(binding.parameters?.["exempt_item_ids"]) });
      }
    }
    if (binding.id === "profile.skill-access") {
      const category = strings(binding.parameters?.["category"])[0] ?? "";
      const skills = strings(binding.parameters?.["skills"]);
      if (category) skillLists.push({ rule_id: rule.id, category, skills });
    }
  }
  // Effective access is the same materialisation the offering layer uses
  // (`profileEquipment`): declared list ids resolved through the catalogue
  // mappings, the fixed kit and the equipment its own bindings grant. A
  // canonical projection therefore always carries a filterable list — empty
  // included — instead of the legacy unfiltered `null`: absence of a list
  // means the profile may buy no listed equipment, not that it may buy
  // anything. `null` stays reserved for a caller that could not supply the
  // canonical catalogue (custom and free-build contexts), where the module
  // genuinely cannot resolve the profile's offers.
  const access = args.catalogue
    ? Array.from(new Set([...profileEquipmentItems(pack, profile), ...profileEquipment(pack, profile, args.catalogue)]))
      .sort().map((item_id) => ({ item_id }))
    : null;
  const declaredSkills = Array.from(new Set([...(profile.skill_access ?? []), ...skillLists.map((list) => list.category)]));
  return {
    band_id: bandId, profile_id: profile.id, fixed_equipment: profile.fixed_equipment ?? [],
    equipment_access: access, equipment_forbids: forbids,
    // The promotion grant enters `skill_access` only for the configured Hero:
    // a canonical Henchman row carries it in `promotion_skill_access` alone, so
    // no early projection can hand the tables to an unpromoted fighter.
    skill_access: profile.type === "hero"
      ? Array.from(new Set([...declaredSkills, ...promotionSkills])) : declaredSkills,
    skill_lists: skillLists,
    ...(promotionSkills.length ? { promotion_skill_access: promotionSkills } : {}),
    ...(activeWeaponLimit ? { active_weapon_limit: activeWeaponLimit } : {}),
    ...(activeWeaponForbids.length ? { active_weapon_forbids: activeWeaponForbids } : {}),
    ...(activeWeaponPermits.length ? { active_weapon_permits: activeWeaponPermits } : {}),
    ...(requiredEquipment.length ? { required_equipment: requiredEquipment } : {}),
    ...(poisonApplication.length ? { poison_application: poisonApplication } : {}),
    ...(missileWeaponLimit.length ? { missile_weapon_limit: missileWeaponLimit } : {}),
  };
}

/** Whole-set limits one band publishes for its members. */
export function bandEquipmentLimits(pack: BandPackage): EquipmentLimits | null {
  const limits: {
    rule_id?: string; max_missile_weapons?: number; required_tag?: string;
    exempt_profile_ids?: readonly string[]; item_copy_limit?: EquipmentItemCopyLimit;
  } = {};
  for (const rule of pack.special_rules) {
    // A band-wide limit is published by a band grant, exactly like the
    // band-wide prohibition tokens; a profile-grant rule states its own
    // profile's bound and is projected on that profile's facts instead.
    if (rule.runtime?.grant !== "band" || rule.applies_to?.band !== true) continue;
    for (const binding of rule.bindings ?? []) {
      if (binding.id !== "profile.equipment-restrictions") continue;
      const parameters = binding.parameters ?? {};
      const max = parameters["max_missile_weapons"];
      const required = parameters["required_tag"];
      const exempt = strings(parameters["exempt_profile_ids"]);
      const itemId = strings(parameters["max_item_id"])[0] ?? "";
      const maxCopies = parameters["max_item_copies"];
      const copies = itemId !== "" && typeof maxCopies === "number";
      if (typeof max !== "number" && typeof required !== "string" && !exempt.length && !copies) continue;
      limits.rule_id ??= rule.id;
      if (typeof max === "number") limits.max_missile_weapons = max;
      if (typeof required === "string") limits.required_tag = required;
      if (exempt.length) limits.exempt_profile_ids = exempt;
      if (copies) {
        const exemptMaximum = parameters["exempt_max_item_copies"];
        limits.item_copy_limit = { item_id: itemId, maximum: maxCopies as number,
          exempt_profile_ids: exempt,
          ...(typeof exemptMaximum === "number" ? { exempt_maximum: exemptMaximum } : {}) };
      }
    }
  }
  return Object.keys(limits).length ? limits : null;
}

/** Band-wide prohibition tokens of the rules that apply to every member. */
export function bandEquipmentForbids(pack: BandPackage): readonly string[] {
  const result: string[] = [];
  for (const rule of pack.special_rules) {
    if (rule.runtime?.grant !== "band" || rule.applies_to?.band !== true) continue;
    for (const binding of rule.bindings ?? []) {
      if (binding.id !== "profile.equipment-restrictions") continue;
      for (const token of strings(binding.parameters?.["forbids"])) {
        const trimmed = token.trim();
        if (trimmed && !trimmed.startsWith("[") && !result.includes(trimmed)) result.push(trimmed);
      }
    }
  }
  return result;
}

/**
 * Bounded special-skill lists of one profile, keyed by category, from the
 * canonical `profile.skill-access` bindings. Each list carries the id of the
 * rule that published it, so `skillIssue` refusals name their source rule. A
 * list with no published members stays empty on purpose: `skillIssue` reports
 * it as pending instead of presenting the whole special catalogue as legal.
 */
export function profileSkillLists(pack: BandPackage, profile: EditorialProfile): readonly { readonly rule_id: string; readonly category: string; readonly skills: readonly string[] }[] {
  const lists: { rule_id: string; category: string; skills: readonly string[] }[] = [];
  for (const rule of applicableRules(pack, profile)) for (const binding of rule.bindings ?? []) {
    if (binding.id !== "profile.skill-access") continue;
    const category = strings(binding.parameters?.["category"])[0] ?? "";
    if (category) lists.push({ rule_id: rule.id, category, skills: strings(binding.parameters?.["skills"]) });
  }
  return lists;
}

/** Profile recipients are independent of whether either application executes the effect. */
export function specialRuleRestriction(args: {
  readonly build: BuildFacts;
  readonly profile: EditorialProfile | null;
  readonly rule: EditorialRule;
  readonly native_virtue: boolean;
  readonly starting_skills: readonly string[];
  readonly stage?: "recipients" | "prerequisites" | "access";
}): string | null {
  const { build: b, profile: p, rule } = args;
  const unavailable = `special rule is not available to ${b.band_id}/${b.profile_id}: ${rule.id}`;
  if (!args.stage || args.stage === "recipients") {
    if (p && !recipientTypeMatches(rule, p)) return unavailable;
    if (p && rule.eligibility?.length && !rule.eligibility.includes(p.id)) return unavailable;
    if (p && rule.applies_to?.profile_ids?.length && !rule.applies_to.profile_ids.includes(p.id)) return unavailable;
    if (rule.id.startsWith("band--blessings-of-nurgle-") && b.profile_id !== "tainted-ones") return unavailable;
    if (rule.id.startsWith("band--virtue-of-") && !args.native_virtue && !b.special_rule_ids.includes("band--renowned-virtue")) return "a foreign Bretonnian Virtue requires Renowned Virtue";
  }
  if ((!args.stage || args.stage === "prerequisites") && rule.id === "band--clan-pestilens-special-skills-ignore-pain" && ![...b.skill_ids, ...args.starting_skills].includes("skill.resilient")) return "Ignore Pain requires Resilient";
  if ((!args.stage || args.stage === "prerequisites") && rule.id === "strigoi-vampire--curse-of-the-revenant" && !b.special_rule_ids.includes("strigoi-vampire--great-thirster")) return "Curse of the Revenant requires Great Thirster";
  if ((!args.stage || args.stage === "prerequisites") && (
    rule.id === "bullied-goblin--frustratingly-tiny" && b.special_rule_ids.includes("bigsnotz--big-bully")
    || rule.id === "bigsnotz--big-bully" && b.special_rule_ids.includes("bullied-goblin--frustratingly-tiny")
  )) return "Frustratingly Tiny cannot be combined with Big Bully";
  if ((!args.stage || args.stage === "prerequisites") && b.band_id === "marauders-of-chaos"
      && rule.id.startsWith("band--mark-of-")
      && b.special_rule_ids.filter(id => id.startsWith("band--mark-of-")).length > 1) return "a Marauder leader may have only one Mark of Chaos";
  const warbandSkill = rule.kind === "warband_skill" || rule.bindings?.some((binding) => binding.id.startsWith("skill."));
  if ((!args.stage || args.stage === "access") && p && warbandSkill && rule.applies_to?.band === true && !rule.eligibility?.length && !(p.skill_access ?? []).includes("special")) return unavailable;
  return null;
}

function skullBustaRestriction(b: BuildFacts): string | null {
  if ([b.off_hand_id, b.extra_hand_id].includes("weapon.skull-busta")) return "Skull Busta must be the main weapon";
  if (b.main_weapon_id !== "weapon.skull-busta") return null;
  if (b.mounted) return "Skull Busta may not be used while mounted";
  if ([b.off_hand_id, b.extra_hand_id].some(id => id && !["defence.shield", "defence.kite-shield"].includes(id))) return "Skull Busta may only be combined with shields";
  return null;
}

function hellbladeRestriction(b: BuildFacts): string | null {
  if ((b.main_weapon_id === "weapon.hellblade" && b.main_material_id !== "material.normal")
      || (b.off_hand_id === "weapon.hellblade" && b.off_material_id !== "material.normal")) {
    return "Hellblade cannot be made of mortal special metals";
  }
  return null;
}

export function loadoutRestriction(args: {
  readonly build: BuildFacts;
  readonly main_weapon: RecordData;
  readonly off_weapon: RecordData | null;
  readonly contracts: readonly string[];
  readonly selected_mechanics: readonly string[];
  readonly stage?: "hands" | "skills";
}): string | null {
  const { build: b, main_weapon: main, off_weapon: off, contracts, selected_mechanics: mechanics } = args;
  if (args.stage === "skills") return skillLoadoutRestriction(b, contracts, mechanics);
  if (mechanics.includes("mechanic.foul-odour") && (b.open_flame === true || [b.main_weapon_id, b.off_hand_id, b.extra_hand_id].includes("weapon.brazier-iron"))) return "Foul Odour forbids carrying open flames";
  if (mechanics.some(id => ["mechanic.ethereal-hit-save", "mechanic.ghost-pirate-ethereal"].includes(id)) && b.skill_ids.some(id => ["skill.step-aside", "skill.dodge"].includes(id))) return "Ethereal cannot be combined with Dodge or Step Aside";
  const hellblade = hellbladeRestriction(b);
  if (hellblade) return hellblade;
  const skullBusta = skullBustaRestriction(b);
  if (skullBusta) return skullBusta;
  if (!main["main_hand"]) return "illegal main-hand selection";
  if (b.special_rule_ids.includes("strigoi-vampire--curse-of-the-revenant") && !b.special_rule_ids.includes("strigoi-vampire--great-thirster")) return "Curse of the Revenant requires Great Thirster";
  if (b.special_rule_ids.includes("band--clan-pestilens-special-skills-contagious") && !b.special_rule_ids.includes("band--clan-pestilens-special-skills-rotten-body")) return "Contagious requires Rotten Body";
  if (b.special_rule_ids.includes("band--renowned-virtue") && b.special_rule_ids.filter((id) => id.startsWith("band--virtue-of-")).length !== 1) return "Renowned Virtue requires exactly one Bretonnian Virtue";
  if (b.off_hand_id) {
    if (b.off_hand_id.startsWith("weapon.") && !off?.["off_hand"]) return "illegal off-hand selection";
    if ((main["hands"] === 2 || main["paired"]) && !contracts.some((id) => ["compiler.ignore-difficult-to-use-restrictions", "compiler.master-of-arms"].includes(id))) return "main weapon occupies both hands";
    const restricted: Record<string, readonly string[]> = {
      "weapon.morning-star": [], "weapon.natural-attacks": [], "weapon.fist": [],
      "weapon.spear": ["defence.shield", "defence.buckler"],
      "weapon.broadsword": ["defence.shield", "defence.kite-shield"],
      "weapon.squig-prodder": ["defence.shield", "weapon.spiked-gauntlet"],
      "weapon.boar-spear": ["defence.shield", "defence.buckler"],
    };
    if (restricted[b.main_weapon_id] && !restricted[b.main_weapon_id]!.includes(b.off_hand_id)) return `${b.main_weapon_id} cannot be combined with ${b.off_hand_id}`;
    if (["armour.toughened-leathers", "armour.ninja-robes"].includes(b.armour_id) && ["defence.shield", "defence.kite-shield"].includes(b.off_hand_id)) return "toughened leathers cannot be combined with a shield";
    if (["armour.wizard-s-robe", "armour.eshin-assassin-robes"].includes(b.armour_id) && ["defence.shield", "defence.buckler", "defence.kite-shield"].includes(b.off_hand_id)) return `${b.armour_id} cannot be combined with other armour except a helmet`;
  }
  return args.stage === "hands" ? null : skillLoadoutRestriction(b, contracts, mechanics);
}

function skillLoadoutRestriction(b: BuildFacts, contracts: readonly string[], mechanics: readonly string[]): string | null {
  if (contracts.includes("compiler.berserker-incompatible-with-ferocious-charge") && mechanics.includes("skill.ferocious-charge")) return "Berserker may not be combined with Ferocious Charge";
  if (contracts.includes("compiler.censer-bearer-loadout")) {
    if (!mechanics.includes("mechanic.black-hunger")) return "Censer Bearer requires Black Hunger";
    if (b.main_weapon_id !== "weapon.censer" || b.off_hand_id) return "Censer Bearer may use only a Censer in close combat";
  }
  return null;
}

function cloakArmourRestriction(b: BuildFacts): string | null {
  return b.defence_ids.includes("defence.sea-dragon-cloak") && b.armour_id !== "armour.no-armour"
    ? "Sea Dragon cloak occupies the armour choice and cannot be combined with another suit" : null;
}

export function additionalEquipmentRestriction(b: BuildFacts): string | null {
  if (b.special_rule_ids.includes("band--shield-bash") && !["defence.shield", "defence.kite-shield"].includes(b.off_hand_id ?? "")) return "Shield Bash requires a shield or kite shield";
  if (b.extra_hand_id) {
    if (!b.special_rule_ids.some((id) => ["band--mutations-extra-arm", "band--skaven-special-skills-tail-fighting"].includes(id))) return "an extra hand requires Extra Arm or Tail Fighting";
    if (b.extra_hand_id === "defence.kite-shield") return "the extra hand may not carry a kite shield";
    if (!b.extra_hand_id.startsWith("weapon.") && !["defence.shield", "defence.buckler"].includes(b.extra_hand_id)) return "the extra hand must hold a one-handed weapon, shield, or buckler";
  }
  return cloakArmourRestriction(b);
}

export function catalogueEquipment(pack: BandPackage, profile: EditorialProfile, catalogue: Catalogue): string[] {
  let actual = profile;
  if (pack.band.id === "khemri-lahmian-brotherhood" && !profile.equipment_lists?.length) {
    actual = { ...profile, equipment_lists: [`foreign-${profile.id === "beloved" ? "beloved" : "undead"}-equipment-list`] };
  }
  const result = new Set(profileEquipment(pack, actual, catalogue));
  if (pack.band.id === "lustria-pirates") for (const list of catalogue.foreign_packages["mercenaries"]?.equipment_lists ?? []) {
    for (const item of list.items ?? []) if (catalogue.mappings[item.item_id]) result.add(catalogue.mappings[item.item_id]!);
  }
  return Array.from(result).sort();
}

export function selectedRuleCandidates(context: BuildContext): { rules: Record<string, EditorialRule>; message: string | null } {
  const { build: b, package: pack, catalogue: c, contracts } = context;
  const rules = b.band_id ? Object.fromEntries(pack.special_rules.map((rule) => [rule.id, rule])) : { ...c.free_rules };
  if (contracts.includes("compiler.slayer-skill-options")) for (const rule of c.packages["chaos-streets-dwarf-treasure-hunters"]?.special_rules ?? []) {
    if (rule.kind === "warband_skill" && rule.runtime?.implemented === "YES" && !rules[rule.id]) rules[rule.id] = { ...rule, eligibility: [], applies_to: {} };
  }
  if (b.special_rule_ids.includes("band--renowned-virtue")) for (const rule of c.foreign_packages["bretonnian-knights"]?.special_rules ?? []) {
    if (rule.id.startsWith("band--virtue-of-") && !rules[rule.id]) rules[rule.id] = { ...rule, eligibility: [] };
  }
  const count = b.special_rule_ids.filter((id) => id.startsWith("band--mutations-")).length;
  const grants: Record<string, string> = { "beastmen-raiders": "band--beastmen-special-skills-mutant", "marauders-of-chaos": "band--marauder-special-skills-mutant" };
  const grant = grants[b.band_id ?? ""];
  if (count && grant) {
    if (b.special_rule_ids.filter((id) => id === grant).length < count) return { rules, message: `each purchased mutation requires ${grant}` };
    for (const candidate of Object.values(c.packages)) for (const rule of candidate.special_rules) {
      if (rule.id.startsWith("band--mutations-") && !rules[rule.id]) rules[rule.id] = { ...rule, eligibility: [] };
    }
  }
  return { rules, message: null };
}

export function bannedSkillCategories(pack: BandPackage, profile: EditorialProfile): Record<string, string> {
  const banned: Record<string, string> = {};
  for (const rule of applicableRules(pack, profile)) if (rule.runtime?.implemented === "YES") {
    for (const binding of rule.bindings ?? []) if (binding.id === "compiler.forbid-skill-categories") {
      for (const category of strings(binding.parameters?.["categories"])) banned[category] ??= rule.id;
    }
  }
  return banned;
}

export function catalogueSkillChoices(context: BuildContext): Record<string, boolean> {
  const rules = applicableRules(context.package, context.profile);
  const bindings = rules.flatMap((rule) => rule.bindings ?? []);
  const compilerBindings = rules.filter((rule) => rule.runtime?.implemented === "YES").flatMap((rule) => rule.bindings ?? []).filter((binding) => binding.id.startsWith("compiler."));
  const access = buildAccess({ ...context,
    profile_bindings: bindings.filter((binding) => binding.id.startsWith("profile.")),
    compiler_bindings: compilerBindings, contracts: compilerBindings.map((binding) => binding.id),
  });
  const profile: ProfileFacts = {
    band_id: context.package.band.id, profile_id: context.profile.id, fixed_equipment: [],
    equipment_access: null, equipment_forbids: [], skill_access: access.skills, skill_lists: profileSkillLists(context.package, context.profile),
  };
  const banned = bannedSkillCategories(context.package, context.profile);
  return Object.fromEntries(Object.values(context.catalogue.skills).map((skill) => [skill.id,
    skillIssue(profile, skill, true) === null && !(skill.category in banned),
  ]));
}

/** Current warrior facts, not a campaign document or a combat-engine object. */
export interface WarriorEquipmentFacts {
  readonly profile_id?: string;
  readonly profile_name: unknown;
  readonly kind: string;
  readonly skills: readonly string[];
  /** Canonical ids resolved by a consumer whose stored skills are display names. */
  readonly skill_ids?: readonly string[];
  readonly special_rules?: readonly string[];
  readonly equipment: readonly { readonly item_id: string; readonly name: unknown; readonly quantity: number;
    readonly acquisition?: string; readonly base_item_id?: string }[];
  readonly quantity?: number;
  readonly equipment_limits?: Readonly<Record<string, number>>;
}

/** Legacy item-specific restrictions extracted from the Web's application service. */
export function warriorEquipmentRestriction(args: {
  readonly warrior: WarriorEquipmentFacts;
  readonly item_id: string;
  readonly item_name: string;
  readonly category: string;
  readonly profile: RecordData | null;
  readonly amount: number;
  readonly weapon_hands: Readonly<Record<string, number | null | undefined>>;
  /** Python confirms bearer restrictions before checking assignment quantities. */
  readonly stage?: "profile" | "loadout";
  readonly profile_restriction_note?: string;
}): string | null {
  const { warrior, item_id: itemId, item_name: name, category, profile, amount, weapon_hands: hands, stage } = args;
  const weaponId = (row: WarriorEquipmentFacts["equipment"][number]): string => stage
    ? row.base_item_id || row.item_id : row.base_item_id ?? row.item_id;
  if (stage !== "loadout") {
    const identity = [warrior.profile_name, warrior.profile_id, ...warrior.skills, ...(warrior.special_rules ?? [])].join(" ").replace(/[-_]/g, " ").toLowerCase();
    if (stage !== "profile" && ["armour", "shield-or-defence"].includes(category) && profile && strings(profile["equipment_forbids"]).includes("armour")) return "This warrior cannot wear armour, shields or bucklers.";
    const access = Array.isArray(profile?.["equipment_access"]) ? profile["equipment_access"] as readonly { readonly item_id?: string }[] : [];
    const training = stage === "profile"
      ? (warrior.skill_ids ?? []).includes(category === "ranged-weapon" ? "skill.weapons-expert" : "skill.weapons-training")
      : /weapons? (training|expert)/.test(warrior.skills.join(" ").toLowerCase());
    if (["close-combat-weapon", "ranged-weapon"].includes(category) && warrior.profile_id && !warrior.profile_id.startsWith("hireling.") && (stage === "profile" ? profile !== null : access.length > 0)
      && !access.some((row) => row.item_id === itemId) && !training) return "This weapon is outside the warrior's equipment access.";
    if (itemId === "barbed_whip" && warrior.kind !== "hero") return "Barbed Whip may only be assigned to a Marauders of Chaos Hero.";
    if (itemId === "great_axe" && !(warrior.kind === "hero" && identity.includes("chosen of chaos"))) return "Great Axe requires a Marauders Hero with the Chosen of Chaos skill.";
    if (itemId === "reptile_venom" && !(warrior.kind === "henchman" && identity.includes("skink"))) return "Reptile Venom may only be assigned to Skink Henchmen.";
    if (["familiar", "arcane_familiar"].includes(itemId) && !identity.includes("spellcaster")) return "A Familiar may only be assigned to a spellcaster.";
    if (itemId === "book_of_the_dead" && !/(vampire|necromancer)/.test(identity)) return "The Book of the Dead may only be assigned to Vampires or Necromancers.";
    if (itemId === "nightmare" && !/(vampire|necromancer|grave guard)/.test(identity)) return "A Nightmare may only be assigned to Vampires, Necromancers or Grave Guards.";
    if (itemId === "temple_dog" && !/(dragon monk|sister|priest)/.test(identity)) return "A Temple Dog may only be assigned to Dragon Monks, Sisters of Sigmar or Priests.";
    if (["barding", "bretonnian_barding"].includes(itemId) && !warrior.equipment.some((row) => /(warhorse|horse)/i.test(`${row.name} ${row.item_id} ${stage === "profile" ? row.base_item_id ?? "" : ""}`))) return "Barding requires this warrior to have a Warhorse.";
    if (["dark_elf_blade_weapon_upgrade", "poisoned_weapon"].includes(itemId) && !warrior.equipment.some((row) => stage === "profile" ? hands[weaponId(row)] != null : hands[weaponId(row)] !== null)) return stage === "profile"
      ? `${name} requires an equipped weapon to upgrade.` : "This upgrade requires an equipped weapon.";
    if (itemId === "sword_heroes_only" && warrior.kind !== "hero") return "This Sword variant may only be assigned to Heroes.";
    const restricted: Record<string, readonly string[]> = {
      beastlash: ["beastmaster"], broadsword: ["chapel guard knight"], serpent_staff: ["liche priest"], shortsword: ["chapel guard knight"],
      nehekharan_javelin: ["tomb lord"], swivel_gun: ["gunner"], kite_shield: ["chapel guard knight"], asp_arrows: ["tomb lord"],
      conch_shell_horn: ["piranha warrior"], elven_runestones: ["weaver"], parrot: ["captain", "mate"],
    };
    if (restricted[itemId] && !restricted[itemId]!.some((term) => identity.includes(term))) return (stage === "profile" ? args.profile_restriction_note : "") || `${name} cannot be assigned to this warrior.`;
    if (stage === "profile") return null;
  }
  const carried = warrior.equipment.filter((row) => row.acquisition !== (stage === "loadout" ? "starting_grant" : "fixed")), models = warrior.quantity ?? 1;
  const limit = warrior.equipment_limits?.["maximum_one_handed_weapons"];
  if (hands[itemId] === 1 && limit !== undefined) {
    const carriedHands = carried.filter((row) => hands[weaponId(row)] === 1).reduce((sum, row) => sum + row.quantity, 0);
    if (carriedHands + amount > limit * models) return `Injury limits this warrior to ${limit} one-handed weapon(s) per model.`;
  }
  if (!["close-combat-weapon", "ranged-weapon"].includes(category) && (stage === "loadout" ? warrior.equipment : carried).filter((row) => row.item_id === itemId).reduce((sum, row) => sum + row.quantity, 0) + amount > models) return `${name} is already carried; a warrior carries one of these.`;
  return null;
}
