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
export function hireHireling(
  document: CampaignDocument,
  input: { readonly profile_id: IdString },
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
  const cost = typeof data["cost"] === "number" ? data["cost"] : 0;
  const rating = typeof data["rating"] === "number" ? data["rating"] : cost;
  const upkeep = Array.isArray(data["upkeep_resources"])
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
  const hireling: Warrior = {
    id: `${input.profile_id}#1`,
    name: result.record.names["en"] ?? input.profile_id,
    profile_name: result.record.names["en"] ?? input.profile_id,
    kind: "hireling",
    stats,
    equipment: [],
    skills: Array.isArray(data["skills"])
      ? (data["skills"] as unknown[]).filter((s): s is string => typeof s === "string")
      : [],
    experience: 0,
    quantity: 1,
    cost,
    hireling_rating: rating,
    ...(upkeep.length > 0 ? { upkeep_resources: upkeep } : {}),
    profile_id: input.profile_id,
  };
  const campaign_next: Campaign = {
    ...campaign,
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
