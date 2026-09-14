/**
 * Parity implementation of the desktop campaign hire-eligibility rules.
 * — the 18 roster-dependent `*.rule.campaign-eligibility` rules.
 *
 * Facts come only from the web KB artefact: `campaign.hirelings.traits`
 * (canonical trait table) and `campaign.warband_groups` (band → groups).
 * The application-side heuristics (employer band sets, variant sets, profile
 * keyword lists) mirror the desktop constants exactly.
 *
 * Decisions never guess: a rule needing a fact the context lacks returns an
 * explicit `needs_variant`/`conditional` verdict (desktop semantics).
 */

export type DecisionKind = "allowed" | "rejected" | "needs_variant" | "conditional";

export interface Decision {
  readonly kind: DecisionKind;
  readonly rule_id: string;
  readonly reason: string;
  /** For `conditional`: minimum D6 roll for acceptance (desktop `roll_ge`). */
  readonly roll_ge?: number;
}

export interface WarbandHireContext {
  readonly band_id: string;
  readonly band_groups: ReadonlySet<string>;
  readonly member_profile_ids: ReadonlySet<string>;
  readonly hired_sword_profile_ids: ReadonlySet<string>;
  readonly variant?: string | null;
  /** Canonical hireling traits: profile id → trait set. */
  readonly hireling_traits: ReadonlyMap<string, ReadonlySet<string>>;
}

const SPELLCASTER_PROFILE_KEYWORDS = [
  "magister", "matriarch", "priestess", "shaman", "warlock", "necromancer",
  "vampire", "sorcerer", "wizard", "lich",
] as const;

const FEAR_PROFILE_KEYWORDS = [
  "possessed", "vampire", "zombie", "ghoul", "beastman", "gor", "ogre",
  "troll", "mutant", "daemon", "plague-bearer", "nurgling", "kroxigor",
  "snotling", "squig", "spawn",
] as const;

const MERCENARY_EMPLOYER_BANDS: ReadonlySet<string> = new Set([
  "mercenaries", "averlanders", "ostlanders", "tileans", "lustria-tileans",
  "trollheim-mercenaries",
]);
const WITCH_HUNTER_EMPLOYER_BANDS: ReadonlySet<string> = new Set([
  "witch-hunters", "trollheim-witch-hunters",
]);
const VARIANT_CAPABLE_BANDS: ReadonlySet<string> = new Set([
  "mercenaries", "trollheim-mercenaries",
]);
export const MERCENARY_VARIANTS: ReadonlySet<string> = new Set([
  "reikland", "middenheim", "marienburg", "ostermark",
]);
export function mercenaryVariantsForBand(bandId:string):readonly string[]{return VARIANT_CAPABLE_BANDS.has(bandId)?[...MERCENARY_VARIANTS]:[];}
const FEAR_BAND_GROUPS: ReadonlySet<string> = new Set([
  "warband-group.undead", "warband-group.beastmen", "warband-group.ogre",
  "warband-group.orc", "warband-group.skaven", "warband-group.chaotic",
]);
const SPELLCASTER_BAND_GROUPS: ReadonlySet<string> = new Set([
  "warband-group.undead", "warband-group.chaotic",
]);

function hasKeyword(ids: ReadonlySet<string>, keywords: readonly string[]): boolean {
  for (const id of ids) {
    const folded = id.toLowerCase();
    if (keywords.some((k) => folded.includes(k))) return true;
  }
  return false;
}

function traitsOf(ids: ReadonlySet<string>, traits: ReadonlyMap<string, ReadonlySet<string>>): Set<string> {
  const out = new Set<string>();
  for (const id of ids) traits.get(id)?.forEach((t) => out.add(t));
  return out;
}

interface RosterFacts {
  isMercenaryEmployer: boolean;
  isWitchHunterEmployer: boolean;
  hasElfMember: boolean;
  hasDwarfMember: boolean;
  hasHumanMember: boolean;
  hasUndeadMember: boolean;
  hasFearCausingMember: boolean;
  hasSpellcasterMember: boolean;
  hasWarriorPriestMember: boolean;
  hasElvenHiredSword: boolean;
  hasEvilHiredSword: boolean;
  hasHighwayman: boolean;
  hasRoadwarden: boolean;
  isMiddenheim: boolean;
  variantCapable: boolean;
  variantKnown: boolean;
  williamAutoEmployer: boolean;
}

function buildFacts(ctx: WarbandHireContext): RosterFacts {
  const members = ctx.member_profile_ids;
  const hired = ctx.hired_sword_profile_ids;
  const all = new Set<string>([...members, ...hired]);
  const groups = ctx.band_groups;
  const traits = ctx.hireling_traits;
  const memberTraits = traitsOf(members, traits);
  const hiredTraits = traitsOf(hired, traits);
  const allTraits = new Set<string>([...memberTraits, ...hiredTraits]);

  const isMercenary = MERCENARY_EMPLOYER_BANDS.has(ctx.band_id);
  const isWitchHunter = WITCH_HUNTER_EMPLOYER_BANDS.has(ctx.band_id);
  const bandElf = groups.has("warband-group.elf") || groups.has("warband-group.high-elf") || groups.has("warband-group.dark-elf");
  const bandDwarf = groups.has("warband-group.dwarf");
  const bandHuman = groups.has("warband-group.human") || groups.has("warband-group.human-mercenary");
  const bandUndead = groups.has("warband-group.undead");

  const variantCapable = VARIANT_CAPABLE_BANDS.has(ctx.band_id);
  const variant = (ctx.variant ?? "").trim().toLowerCase();
  const variantKnown = variantCapable && variant.length > 0 && MERCENARY_VARIANTS.has(variant);
  const isMiddenheim = variant === "middenheim";
  const williamAuto = isMercenary || isWitchHunter || ctx.band_id === "sisters-of-sigmar";

  let spellcasterMembers =
    hasKeyword(all, SPELLCASTER_PROFILE_KEYWORDS) ||
    [...groups].some((g) => SPELLCASTER_BAND_GROUPS.has(g));
  // Priests never taint the roster for the Witch Hunter rule.
  const priestsOnly = allTraits.has("priest") && !hasKeyword(all, SPELLCASTER_PROFILE_KEYWORDS);
  spellcasterMembers = spellcasterMembers && !priestsOnly;

  return {
    isMercenaryEmployer: isMercenary,
    isWitchHunterEmployer: isWitchHunter,
    hasElfMember: bandElf || allTraits.has("elf"),
    hasDwarfMember: bandDwarf || allTraits.has("dwarf"),
    hasHumanMember: bandHuman || allTraits.has("human"),
    hasUndeadMember: bandUndead || allTraits.has("undead"),
    hasFearCausingMember:
      [...groups].some((g) => FEAR_BAND_GROUPS.has(g)) ||
      hiredTraits.has("fear-causing") ||
      hasKeyword(all, FEAR_PROFILE_KEYWORDS),
    hasSpellcasterMember: spellcasterMembers,
    hasWarriorPriestMember:
      hired.has("hireling.hired-sword.warrior-priest-of-sigmar") ||
      allTraits.has("priest"),
    hasElvenHiredSword: hiredTraits.has("elf"),
    hasEvilHiredSword: hiredTraits.has("evil"),
    hasHighwayman: hired.has("hireling.hired-sword.highwayman"),
    hasRoadwarden: hired.has("hireling.hired-sword.roadwarden"),
    isMiddenheim,
    variantCapable,
    variantKnown,
    williamAutoEmployer: williamAuto,
  };
}

function allowed(ruleId: string, reason: string): Decision {
  return { kind: "allowed", rule_id: ruleId, reason };
}
function rejected(ruleId: string, reason: string): Decision {
  return { kind: "rejected", rule_id: ruleId, reason };
}

const R = "rule.campaign-eligibility";

/** Evaluate one `*.rule.campaign-eligibility` rule against a context. */
export function evaluateRule(ruleId: string, ctx: WarbandHireContext): Decision {
  const f = buildFacts(ctx);
  const dwarfRule = (name: string): Decision => {
    if (f.isMercenaryEmployer || f.isWitchHunterEmployer || f.hasElfMember) {
      return allowed(ruleId, `Mercenaries and Witch Hunters may hire the ${name}; a roster that includes Elves may also hire him.`);
    }
    return rejected(ruleId, `Only Mercenaries, Witch Hunters or a roster that includes Elves may hire the ${name}.`);
  };

  if (ruleId === `hireling.hired-sword.dwarf-troll-slayer.${R}`) return dwarfRule("Dwarf Troll Slayer");
  if (ruleId === `hireling.hired-sword.dwarf-treasure-hunter.${R}`) return dwarfRule("Dwarf Treasure Hunter");
  if (ruleId === `hireling.hired-sword.runesmith-journeyman.${R}`) return dwarfRule("Runesmith Journeyman");
  if (ruleId === `hireling.hired-sword.elf-ranger.${R}`) {
    if (f.isMercenaryEmployer || f.isWitchHunterEmployer || f.hasDwarfMember) {
      return allowed(ruleId, "Mercenaries and Witch Hunters may hire the Elf Ranger; a roster that includes Dwarfs may also hire him.");
    }
    return rejected(ruleId, "Only Mercenaries, Witch Hunters or a roster that includes Dwarfs may hire the Elf Ranger.");
  }
  if (ruleId === `hireling.hired-sword.cathayan-merchant.${R}`) {
    if (f.hasHumanMember || f.hasDwarfMember) {
      return allowed(ruleId, "The Cathayan Merchant may be hired when the warband includes Humans or Dwarfs (Battle Monks of Cathay count).");
    }
    return rejected(ruleId, "The Cathayan Merchant only joins warbands that include Humans or Dwarfs.");
  }
  if (ruleId === `hireling.hired-sword.grave-robber.${R}`) {
    if (f.hasUndeadMember) {
      return allowed(ruleId, "The Grave Robber joins warbands that include a Vampire, Necromancer or Liche.");
    }
    return rejected(ruleId, "The Grave Robber only joins warbands that include a Vampire, Necromancer or Liche.");
  }
  if (ruleId === `hireling.hired-sword.ninja-gnoblar.${R}`) {
    if (!f.hasFearCausingMember) {
      return allowed(ruleId, "The Ninja Gnoblar joins warbands with no fear-causing creatures.");
    }
    return rejected(ruleId, "The Ninja Gnoblar will not join a warband that contains fear-causing creatures.");
  }
  if (ruleId === `hireling.hired-sword.witch-hunter.${R}`) {
    if (!f.hasSpellcasterMember) {
      return allowed(ruleId, "The Witch Hunter does not work for warbands with a spellcaster (priests of Sigmar, Ulric, Taal or Morr excepted).");
    }
    return rejected(ruleId, "The Witch Hunter refuses warbands whose roster contains a spellcaster (except priests of Sigmar, Ulric, Taal or Morr).");
  }
  if (ruleId === `hireling.hired-sword.highwayman.${R}`) {
    if (!f.hasRoadwarden) {
      return allowed(ruleId, "The Highwayman may be hired when no Roadwarden serves the warband.");
    }
    return rejected(ruleId, "The Highwayman cannot be hired by (or remain with) a warband that employs a Roadwarden.");
  }
  if (ruleId === `hireling.hired-sword.roadwarden.${R}`) {
    if (!f.hasHighwayman) {
      return allowed(ruleId, "The Roadwarden may be hired when no Highwayman serves the warband.");
    }
    return rejected(ruleId, "The Roadwarden cannot be hired by a warband that employs a Highwayman.");
  }
  if (ruleId === `hireling.hired-sword.knight-of-the-white-wolf.${R}`) {
    if (!f.hasWarriorPriestMember) {
      return allowed(ruleId, "The Knight of the White Wolf joins warbands without a Warrior Priest.");
    }
    return rejected(ruleId, "The Knight of the White Wolf will not join (or remain with) a warband that contains a Warrior Priest.");
  }
  if (ruleId === `hireling.hired-sword.shadow-warrior.${R}`) {
    if (!f.hasEvilHiredSword) {
      return allowed(ruleId, "The Shadow Warrior joins warbands without evil Hired Swords.");
    }
    return rejected(ruleId, "The Shadow Warrior cannot be hired by (or remain with) a warband that employs an evil Hired Sword.");
  }
  if (ruleId === `hireling.dramatis.dijin-katal-the-renegade-assassin.${R}`) {
    if (!f.hasElvenHiredSword) {
      return allowed(ruleId, "Dijin Katal joins warbands without Elven Hired Swords.");
    }
    return rejected(ruleId, "Dijin Katal cannot be hired by a warband whose roster contains any type of Elven Hired Sword.");
  }
  if (ruleId === `hireling.dramatis.maximilian-the-mad.${R}` || ruleId === `hireling.hired-sword.warrior-priest-of-sigmar.${R}`) {
    if (!f.variantCapable) {
      return allowed(ruleId, "Not a variant-capable warband; the rule does not apply.");
    }
    if (f.variantKnown) {
      if (f.isMiddenheim) return rejected(ruleId, "Middenheimers may not hire this warrior.");
      return allowed(ruleId, "The selected Mercenary variant may hire this warrior.");
    }
    return { kind: "needs_variant", rule_id: ruleId, reason: "Requires the warband's Mercenary variant (Middenheimers are excluded)." };
  }
  if (ruleId === `hireling.hired-sword.wolf-priest-of-ulric.${R}`) {
    if (f.variantCapable && f.variantKnown) {
      if (f.isMiddenheim) {
        return allowed(ruleId, "Middenheim Mercenaries may hire the Wolf Priest of Ulric as a Hero replacement.");
      }
      return rejected(ruleId, "Only Middenheim Mercenaries may hire the Wolf Priest of Ulric.");
    }
    if (f.variantCapable) {
      return { kind: "needs_variant", rule_id: ruleId, reason: "Only available to Middenheim Mercenaries; select the Mercenary variant to confirm." };
    }
    return rejected(ruleId, "The Wolf Priest of Ulric is available only to Middenheim Mercenaries.");
  }
  if (ruleId === `hireling.dramatis.william-schakestange-master-bard.${R}`) {
    if (f.williamAutoEmployer) {
      return allowed(ruleId, "Mercenaries, Sisters of Sigmar and Witch Hunters hire William automatically.");
    }
    if (ctx.band_groups.has("warband-group.good-aligned")) {
      return { kind: "conditional", rule_id: ruleId, reason: "Other good-aligned warbands hire William on a D6 roll of 4+.", roll_ge: 4 };
    }
    return rejected(ruleId, "William only joins good-aligned warbands.");
  }
  if (ruleId === `hireling.dramatis.grand-master-ippan-shu.${R}`) {
    if (f.hasHumanMember || f.hasElfMember) {
      return allowed(ruleId, "Ippan Shu may be hired when the warband includes Humans or Elves.");
    }
    return rejected(ruleId, "Ippan Shu may only be hired when the warband includes Humans or Elves.");
  }
  throw new Error(`no evaluator registered for dynamic rule ${ruleId}`);
}

/** The 18 dynamic rule ids every hireling profile declares (desktop KNOWN_RULES). */
/** Profile's rule ids, either the `rule_ids` shortcut or inline `rules` rows. */
function profileRuleIds(profile: { id: string; rule_ids?: readonly string[]; rules?: readonly { id: string }[] }): string[] {
  if (profile.rule_ids) return profile.rule_ids.map(String);
  return (profile.rules ?? []).map((r) => String(r.id));
}

/** The dynamic campaign-eligibility rules declared on one profile. */
export function dynamicRulesForProfile(
  profileId: string,
  profiles: readonly { id: string; rule_ids?: readonly string[]; rules?: readonly { id: string }[] }[],
): string[] {
  const row = profiles.find((p) => p.id === profileId);
  return row ? profileRuleIds(row).filter((id) => id.endsWith(R)) : [];
}

/** All dynamic rule ids declared across the given profiles (order-stable). */
export function declaredDynamicRules(
  profiles: readonly { id: string; rule_ids?: readonly string[]; rules?: readonly { id: string }[] }[],
): Set<string> {
  const out = new Set<string>();
  for (const row of profiles) {
    for (const id of profileRuleIds(row)) {
      if (id.endsWith(R)) out.add(String(id));
    }
  }
  return out;
}
