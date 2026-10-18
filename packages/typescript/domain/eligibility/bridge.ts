/** Desktop transport: catalogue caches belong here, not in the pure rules. */
import * as eligibility from "./index";
import type {
  BandPackage, Binding, BuildContext, Catalogue, ConstructionContext, EditorialProfile,
  EquipmentLimits, ProfileFacts, SelectionProposal,
} from "./index";
export * from "./index";
const catalogues = new Map<string, Catalogue>();
export function installCatalogue(key: string, catalogue: Catalogue): boolean {
  catalogues.set(key, catalogue);
  return true;
}

/**
 * Shared fact projection over the transport. `package`/`profile` are canonical
 * rows; the shared module is the single interpreter of their bindings, so no
 * consumer walks `runtime.effects` on its own.
 */
export function profileFacts(pack: BandPackage, profile: EditorialProfile, bandId?: string, catalogue?: Catalogue | null,
  additionalBindings: readonly Binding[] = [], build?: eligibility.BuildFacts): ProfileFacts {
  return eligibility.profileFactsProjection({
    pack, profile, ...(bandId ? { band_id: bandId } : {}), ...(catalogue ? { catalogue } : {}),
    additional_bindings: additionalBindings, ...(build ? { build } : {}),
  });
}

/** Band-wide prohibition tokens and whole-set limits of one canonical band. */
export function bandFacts(pack: BandPackage): { equipment_forbids: readonly string[]; equipment_limits: EquipmentLimits | null } {
  return {
    equipment_forbids: eligibility.bandEquipmentForbids(pack),
    equipment_limits: eligibility.bandEquipmentLimits(pack),
  };
}

/** Bounded special-skill lists one canonical profile publishes. */
export function profileSkillLists(pack: BandPackage, profile: EditorialProfile): ReturnType<typeof eligibility.profileSkillLists> {
  return eligibility.profileSkillLists(pack, profile);
}

/** Bindings of every applicable rule of one canonical profile. */
export function profileBindings(pack: BandPackage, profile: EditorialProfile): readonly Binding[] {
  return eligibility.profileBindings(pack, profile);
}

/** Bindings of the rules one consumer has already selected. */
export function selectedRuleBindings(
  pack: BandPackage, ruleIds: readonly string[], catalogue?: Catalogue | null,
): readonly Binding[] {
  return eligibility.selectedRuleBindings(pack, ruleIds, catalogue);
}
export function desktopCall(operation: string, key: string, input: Omit<BuildContext, "catalogue">): unknown {
  const catalogue = catalogues.get(key);
  if (!catalogue) throw new Error(`eligibility catalogue is not installed: ${key}`);
  // The build's declared selection facts and its supplied conditions are the
  // same kind of fact for a printed recipient: `configuredProfile` carries both
  // so a conditional line is decided by the one `entryReachesProfile`.
  const profile = input.profile.type
    ? eligibility.configuredProfile(input.profile, input.build.variant_ids, input.build.condition_ids ?? [])
    : input.profile;
  const context = { ...input, profile, catalogue };
  input = { ...input, profile };
  if (operation === "hirelingKit") return eligibility.resolveHirelingKit(input.profile.hireling_equipment ?? {}, input.build, catalogue, input.package.special_rules);
  // The offer is the list access its own printed clause still permits: the
  // projection behind `profileEquipment` keeps the full access materialisation
  // for validation, and the picker reads the same predicate the compiler does.
  if (operation === "equipment") return eligibility.profileOffer(input.package, input.profile, catalogue, input.build);
  // Trading Post consumables are not band-list lines: the shared projection
  // decides them from the printed clauses, so the picker and the compiled
  // fighter read one permission.
  if (operation === "preparationOptions") return eligibility.preparationOptions(context);
  if (operation === "specialRules") return eligibility.specialRuleOptions(input.package, input.profile, catalogue, input.build);
  if (operation === "configuredRules") return eligibility.selectableRuleOptions(input.package, input.profile, input.build);
  if (operation === "catalogueEquipment") return eligibility.catalogueEquipment(input.package, input.profile, catalogue, input.build);
  if (operation === "selectedRules") return eligibility.selectedRuleCandidates(context);
  if (operation === "ruleBindings") return eligibility.selectedRuleBindings(
    input.package, input.build.special_rule_ids ?? [], catalogue);
  if (operation === "skillChoices") return eligibility.catalogueSkillChoices(context);
  if (operation === "profileFacts") return profileFacts(input.package, input.profile, input.build.band_id ?? undefined, catalogue, input.profile_bindings, input.build);
  if (operation === "bandFacts") return bandFacts(input.package);
  if (operation === "profileSkillLists") return profileSkillLists(input.package, input.profile);
  if (operation === "profileBindings") return profileBindings(input.package, input.profile);
  if (operation === "selectedRuleBindings") return selectedRuleBindings(
    input.package, input.build.special_rule_ids ?? [], catalogue);
  return eligibility.buildRestriction(context, operation);
}

/**
 * Batch construction queries over the installed catalogue. The catalogue is
 * required because option states need canonical item facts the context cannot
 * carry for every candidate; the transport resolves them once per call and
 * never asks the shared module to guess.
 */
export function constructionCall(
  operation: string, key: string, input: ConstructionContext,
  proposals: readonly SelectionProposal[] = [],
  options: { readonly draft?: boolean } = {},
): unknown {
  const catalogue = catalogues.get(key);
  if (!catalogue) throw new Error(`eligibility catalogue is not installed: ${key}`);
  // The catalogue rows are keyed by item id while desktop contexts carry
  // mechanics: the shared index resolves both spellings before the decision.
  const context = { ...input, items: { ...eligibility.catalogueItemFacts(catalogue), ...input.items } };
  if (operation === "selectionDecisions") return eligibility.selectionDecisions(context, proposals);
  if (operation === "validateConstruction") return eligibility.validateConstruction(context, options);
  throw new Error(`unknown construction operation: ${operation}`);
}
