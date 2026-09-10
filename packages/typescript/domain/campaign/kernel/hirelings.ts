/**
 * P3.5: hirelings and advances — implementing the frozen `hireHireling` and
 * `applyAdvance` use cases (bases for P6.7 and P6.6).
 *
 * Hirelings never consume roster capacity (Python
 * `draft_warband_member_count` rule) but add their rating; upkeep resources
 * travel as `[resource_id, amount]` pairs (contract encoding). Advances
 * apply a chosen characteristic point or skill once XP crosses a threshold.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import type {
  AdvanceChoiceInput,
  Campaign,
  CampaignDocument,
  UseCaseResult,
  Warrior,
} from "./usecases";
import { rejected } from "./rejections";
import { findWarrior, withCampaign } from "./document";

/** XP thresholds between advances (canonical Mordheim table). */
export const ADVANCE_THRESHOLDS = [2, 5, 8, 11, 14, 18, 22, 26, 31, 36] as const;

/** Advances earned for total XP (>=0). */
export function advancesForExperience(experience: number): number {
  return ADVANCE_THRESHOLDS.filter((threshold) => experience >= threshold).length;
}

const STAT_KEYS = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const;

/**
 * Hires a Hired Sword from the KB hireling catalogue. Rejects unknown
 * profiles, non-hireling profiles, duplicate hires of the same profile and
 * a resulting rating the caller must accept explicitly (rating itself is
 * never capped, mirroring the desktop).
 */
export interface HireHirelingInput {
  readonly profile_id: IdString;
  /**
   * Hiring fee in gold crowns from the catalogue offer (P6.7 listings). The
   * profile row itself carries no fee — the offer does — so the application
   * passes the resolved fee here. Optional for callers without listings.
   */
  readonly fee?: number;
  /** Non-gold upkeep pairs from the offer (`[resource_id, amount]`). */
  readonly upkeep_resources?: readonly (readonly [IdString, number])[];
}

export function hireHireling(
  document: CampaignDocument,
  input: HireHirelingInput,
  knowledge: KnowledgeReader,
): UseCaseResult {
  const { campaign } = document;
  if (campaign.configuration.is_draft) {
    return rejected("not_permitted_in_draft", "Hire the hired sword after committing the warband.");
  }
  const result = knowledge.queryKnowledge({
    id: { kind: "hireling_id", value: input.profile_id },
  });
  if (!result.ok) {
    return rejected("not_found", `Unknown hireling profile: ${input.profile_id}.`);
  }
  const data = result.record.data as OpenPayload;
  if (campaign.warriors.some((w) => w.profile_id === input.profile_id)) {
    return rejected("conflict", `A ${result.record.names["en"] ?? input.profile_id} is already hired.`);
  }
  // Rating: the profile's `warband_rating` block — `fixed` value or the
  // `base` of a base+experience rating (XP 0 at hiring time), mirroring the
  // desktop `hireling_roster_values`. Cost: the offer's hiring fee when the
  // caller knows it, else the rating base (never silently 0).
  const ratingBlock =
    data["warband_rating"] && typeof data["warband_rating"] === "object"
      ? (data["warband_rating"] as OpenPayload)
      : {};
  const ratingFixed = typeof ratingBlock["value"] === "number" ? ratingBlock["value"] : null;
  const ratingBase = typeof ratingBlock["base"] === "number" ? ratingBlock["base"] : 0;
  const rating = ratingFixed ?? ratingBase;
  const cost = typeof input.fee === "number" ? input.fee : rating;
  const upkeep =
    input.upkeep_resources && input.upkeep_resources.length > 0
      ? input.upkeep_resources
      : Array.isArray(data["upkeep_resources"])
        ? (data["upkeep_resources"] as unknown[]).filter(
            (row): row is [IdString, number] =>
              Array.isArray(row) && typeof row[0] === "string" && typeof row[1] === "number",
          )
        : [];
  const characteristics =
    data["characteristics"] && typeof data["characteristics"] === "object"
      ? (data["characteristics"] as OpenPayload)
      : {};
  const stats: Record<string, number> = {};
  for (const key of STAT_KEYS) {
    const value = characteristics[key];
    if (typeof value === "number") stats[key] = value;
  }
  const equipmentBlock = data["equipment"] && typeof data["equipment"] === "object"
    ? data["equipment"] as OpenPayload
    : {};
  const fixedItems = Array.isArray(equipmentBlock["fixed_items"])
    ? equipmentBlock["fixed_items"] as OpenPayload[]
    : [];
  const equipment = fixedItems.flatMap((entry) => {
    const itemId = typeof entry["item_id"] === "string" ? entry["item_id"] : null;
    if (!itemId) return [];
    const quantityBlock = entry["quantity"] && typeof entry["quantity"] === "object"
      ? entry["quantity"] as OpenPayload
      : {};
    const quantity = Number.isInteger(quantityBlock["value"]) ? Number(quantityBlock["value"]) : 1;
    const item = knowledge.queryKnowledge({ id: { kind: "item_id", value: itemId } });
    return [{
      item_id: itemId,
      name: item.ok ? item.record.names["en"] ?? itemId : itemId,
      quantity,
      acquisition: "hireling_grant",
      unit_cost: 0,
      per_model: false,
      transferable: false,
    }];
  });
  const startingSkillIds = Array.isArray(data["starting_skill_ids"])
    ? (data["starting_skill_ids"] as unknown[]).filter((id): id is string => typeof id === "string")
    : [];
  const skills = startingSkillIds.map((skillId) => {
    const skill = knowledge.queryKnowledge({ id: { kind: "skill_id", value: skillId } });
    return skill.ok ? skill.record.names["en"] ?? skillId : skillId;
  });
  const sectionReader = knowledge as KnowledgeReader & {
    campaignSection?(section: string): Readonly<Record<string, unknown>>;
  };
  const rules = sectionReader.campaignSection?.("hirelings")?.["rules"];
  const ruleIds = new Set(Array.isArray(data["rule_ids"]) ? data["rule_ids"].map(String) : []);
  const maximumModelsModifier = Array.isArray(rules)
    ? (rules as OpenPayload[])
      .filter((rule) => ruleIds.has(String(rule["id"])))
      .flatMap((rule) => Array.isArray(rule["mechanics"]) ? rule["mechanics"] as OpenPayload[] : [])
      .filter((mechanic) => mechanic["type"] === "warband.maximum_models_modifier")
      .reduce((sum, mechanic) => sum + Number(mechanic["value"] ?? 0), 0)
    : 0;
  const hireling: Warrior = {
    id: `${input.profile_id}#1`,
    name: result.record.names["en"] ?? input.profile_id,
    profile_name: result.record.names["en"] ?? input.profile_id,
    kind: "hireling",
    stats,
    equipment,
    skills,
    experience: 0,
    quantity: 1,
    cost,
    hireling_rating: rating,
    ...(maximumModelsModifier !== 0 ? { maximum_models_modifier: maximumModelsModifier } : {}),
    ...(upkeep.length > 0 ? { upkeep_resources: upkeep } : {}),
    ...(Array.isArray(data["skill_access"])
      ? { skill_access: (data["skill_access"] as unknown[]).filter((row): row is string => typeof row === "string") }
      : {}),
    profile_id: input.profile_id,
  };
  const inventory = campaign.inventory.map((row) => ({ ...row }));
  for (const entry of equipment) {
    const stock = inventory.find((row) => row.id === entry.item_id);
    if (stock) {
      stock.owned += entry.quantity;
      stock.equipped += entry.quantity;
    } else {
      inventory.push({ id: entry.item_id, name: entry.name, category: "Equipment", owned: entry.quantity, equipped: entry.quantity, stash: 0, value: entry.unit_cost ?? 0 });
    }
  }
  const campaign_next: Campaign = {
    ...campaign,
    inventory,
    warriors: [...campaign.warriors, hireling],
  };
  return { ok: true, state: withCampaign(document, campaign_next) };
}

/**
 * Applies an advance choice (characteristic +1 or a new skill) to a warrior
 * whose XP crossed the next threshold. `input.choice` is `stat:<KEY>` for a
 * characteristic point or `skill:<name>` for a skill. Records the advance on
 * the warrior (`stat_advances` / `skills`) — full advance-table rolls with
 * P6.6.
 */
export function applyAdvance(
  document: CampaignDocument,
  input: AdvanceChoiceInput,
): UseCaseResult {
  const warrior = findWarrior(document, input.warrior_id);
  if (!warrior) {
    return rejected("not_found", `Unknown warrior id: ${input.warrior_id}.`);
  }
  if (warrior.kind === "hireling") {
    return rejected("invalid_input", "Hired Swords do not take advances.");
  }
  // Validate the choice format before the state checks so callers get
  // input errors even when no advance is pending.
  const statMatch = /^stat:([A-Za-z]{1,2})$/.exec(input.choice);
  const skillMatch = statMatch ? null : /^skill:(.+)$/.exec(input.choice);
  if (!statMatch && !skillMatch) {
    return rejected(
      "invalid_input",
      `Advance choice must be "stat:<KEY>" or "skill:<name>", got "${input.choice}".`,
    );
  }
  if (statMatch) {
    const key = statMatch[1].toUpperCase();
    if (!(STAT_KEYS as readonly string[]).includes(key)) {
      return rejected("invalid_input", `Unknown characteristic: ${statMatch[1]}.`);
    }
  }
  const earned = advancesForExperience(warrior.experience);
  const taken =
    (warrior.stat_advances ? Object.values(warrior.stat_advances).reduce((t, v) => t + v, 0) : 0) +
    warrior.skills.filter((s) => !warrior.skills.slice(0, warrior.skills.indexOf(s)).includes(s) && isLearnedSkill(warrior, s)).length;
  const pending = earned - taken;
  if (pending <= 0) {
    return rejected(
      "prerequisite_missing",
      `${warrior.name} has no pending advance (${earned} earned, ${taken} taken).`,
    );
  }
  if (statMatch) {
    const key = statMatch[1].toUpperCase();
    const statAdvances = { ...(warrior.stat_advances ?? {}) };
    statAdvances[key] = (statAdvances[key] ?? 0) + 1;
    const stats = { ...warrior.stats, [key]: (warrior.stats[key] ?? 0) + 1 };
    const nextWarriors: Warrior[] = document.campaign.warriors.map((w) =>
      w.id === input.warrior_id ? { ...w, stat_advances: statAdvances, stats } : w,
    );
    return { ok: true, state: withCampaign(document, { ...document.campaign, warriors: nextWarriors }) };
  }
  if (skillMatch) {
    const skill = skillMatch[1];
    if (warrior.skills.includes(skill)) {
      return rejected("conflict", `${warrior.name} already knows "${skill}".`);
    }
    const nextWarriors: Warrior[] = document.campaign.warriors.map((w) =>
      w.id === input.warrior_id ? { ...w, skills: [...w.skills, skill] } : w,
    );
    return { ok: true, state: withCampaign(document, { ...document.campaign, warriors: nextWarriors }) };
  }
  return rejected(
    "invalid_input",
    `Advance choice must be "stat:<KEY>" or "skill:<name>", got "${input.choice}".`,
  );
}

/** Skill that came from the profile's starting kit vs. one learned later. */
function isLearnedSkill(warrior: Warrior, skill: string): boolean {
  return (warrior as Warrior & { learned_skills?: readonly string[] }).learned_skills?.includes(skill) ?? true;
}
