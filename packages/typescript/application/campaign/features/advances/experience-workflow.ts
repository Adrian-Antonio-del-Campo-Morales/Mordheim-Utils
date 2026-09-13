import type {
  CampaignDocument,
  KnowledgeReader,
  OpenPayload,
  Warrior,
} from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

const HERO_THRESHOLDS = [2, 4, 6, 8, 11, 14, 17, 20, 24, 28, 32, 36, 41, 46, 51, 57, 63, 69, 76, 83, 90] as const;
const HENCHMAN_THRESHOLDS = [2, 5, 9, 14] as const;
const UNDERDOG_BANDS = [[51, 75, 1], [76, 100, 2], [101, 150, 3], [151, 300, 4], [301, Infinity, 5]] as const;

interface CampaignKnowledgeReader extends KnowledgeReader {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
}

function thresholds(knowledge: CampaignKnowledgeReader, kind: Warrior["kind"]): readonly number[] {
  const document = knowledge.campaignSection?.("experience-and-advances");
  const block = document?.["advance_thresholds"] as Readonly<Record<string, unknown>> | undefined;
  const values = block?.[kind === "hero" ? "hero" : "henchman"];
  return Array.isArray(values) && values.every((value) => Number.isInteger(value))
    ? values as number[]
    : kind === "hero" ? HERO_THRESHOLDS : HENCHMAN_THRESHOLDS;
}

function canGainExperience(warrior: Warrior, knowledge: KnowledgeReader): boolean {
  if (warrior.profile_id?.startsWith("hireling.")) return true;
  if (!warrior.profile_id) return true;
  const profile = knowledge.queryKnowledge({ id: { kind: "profile_id", value: warrior.profile_id } });
  if (!profile.ok) return true;
  if (typeof profile.record.data["can_gain_experience"] === "boolean") return profile.record.data["can_gain_experience"];
  return profile.record.data["type"] !== "animal";
}

export function underdogBonusForRatingDifference(difference: number, knowledge: CampaignKnowledgeReader): number {
  const bands = (knowledge.campaignSection?.("experience-and-advances")?.["underdog_bonus"] as Readonly<Record<string, unknown>> | undefined)?.["bands"];
  const table = Array.isArray(bands)
    ? bands.flatMap((band) => {
      const row = band as Readonly<Record<string, unknown>>;
      const limits = (row["when"] as Readonly<Record<string, unknown>> | undefined)?.["rating_difference"] as Readonly<Record<string, unknown>> | undefined;
      return limits && Number.isFinite(limits["min"]) ? [[Number(limits["min"]), limits["max"] == null ? Infinity : Number(limits["max"]), Number(row["amount"] ?? 0)] as const] : [];
    })
    : UNDERDOG_BANDS;
  return table.find(([min, max]) => difference >= min && difference <= max)?.[2] ?? 0;
}

function underdogBonus(battle: CampaignDocument["campaign"]["battles"][number], knowledge: CampaignKnowledgeReader): number {
  return underdogBonusForRatingDifference((battle.opponent_rating ?? 0) - battle.rating_before, knowledge);
}

export interface ExperienceAward {
  readonly warrior_id: string;
  readonly warrior_name: string;
  readonly amount: number;
  readonly eligible: boolean;
  readonly absent: boolean;
}

export type ExperienceWorkflowResult =
  | { readonly ok: true; readonly document: CampaignDocument }
  | { readonly ok: false; readonly reason: "not_found" | "conflict" | "invalid_input"; readonly message: string };

function pendingContext(document: CampaignDocument) {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle = post && document.campaign.battles.find((row) => row.number === post.battle_number);
  return { post, battle };
}

/** Calculated desktop-equivalent battle awards. This read model never mutates. */
export function experienceAwards(document: CampaignDocument, knowledge: CampaignKnowledgeReader): readonly ExperienceAward[] {
  const { battle } = pendingContext(document);
  if (!battle) return [];
  const absent = new Set((battle.absentees ?? []).map((row) => String(row["id"] ?? "")));
  const individual = battle.xp_awards ?? {};
  const hasIndividualAwards = Object.keys(individual).length > 0;
  const bonus = underdogBonus(battle, knowledge);
  return document.campaign.warriors.map((warrior) => {
    const eligible = canGainExperience(warrior, knowledge);
    const isAbsent = absent.has(warrior.id);
    const amount = !eligible || isAbsent
      ? 0
      : Math.max(0, Math.trunc(hasIndividualAwards ? (individual[warrior.id] ?? 0) : battle.xp_delta)) + bonus;
    return { warrior_id: warrior.id, warrior_name: warrior.name, amount, eligible, absent: isAbsent };
  });
}

function seededAdvances(
  warrior: Warrior,
  previousExperience: number,
  postRows: readonly OpenPayload[],
  knowledge: CampaignKnowledgeReader,
): readonly OpenPayload[] {
  if (!canGainExperience(warrior, knowledge)) return [];
  const advanceThresholds = thresholds(knowledge, warrior.kind === "hireling" ? "hero" : warrior.kind);
  const existing = new Set(postRows
    .filter((row) => String(row["warrior_id"] ?? "") === warrior.id)
    .map((row) => Number(row["threshold"])));
  return advanceThresholds
    .filter((threshold) => previousExperience < threshold && threshold <= warrior.experience && !existing.has(threshold))
    .map((threshold) => ({
      warrior_id: warrior.id,
      warrior_name: warrior.name,
      table: warrior.kind,
      threshold,
      roll_total: null,
      subroll: null,
      committed: false,
      applied_label: "",
    }));
}

/** Apply all displayed awards atomically and exactly once. */
export function applyBattleExperience(
  document: CampaignDocument,
  knowledge: CampaignKnowledgeReader,
  overrides?: Readonly<Record<string, number>>,
): ExperienceWorkflowResult {
  const { post, battle } = pendingContext(document);
  if (!post || !battle) return { ok: false, reason: "not_found", message: "No pending post-battle experience step." };
  if (post.experience_applied) return { ok: false, reason: "conflict", message: "Battle experience has already been applied." };

  const calculated = experienceAwards(document, knowledge);
  const awardRows = new Map(calculated.map((row) => [row.warrior_id, row]));
  const knownIds = new Set(calculated.map((row) => row.warrior_id));
  for (const [id, amount] of Object.entries(overrides ?? {})) {
    if (!knownIds.has(id) || !Number.isInteger(amount) || amount < 0) {
      return { ok: false, reason: "invalid_input", message: "Experience awards must use known warriors and non-negative whole numbers." };
    }
    const row = awardRows.get(id);
    if (amount > 0 && (!row?.eligible || row.absent)) {
      return { ok: false, reason: "invalid_input", message: "Absent or ineligible warriors cannot receive battle experience." };
    }
  }
  const awards = new Map(calculated.map((row) => [row.warrior_id, overrides?.[row.warrior_id] ?? row.amount]));
  const injuryExperienceBefore=(post.step_state?.["injury_experience_before"]??{}) as Readonly<Record<string,unknown>>;
  const previous = new Map(document.campaign.warriors.map((warrior) => [warrior.id, injuryExperienceBefore[warrior.id] == null ? warrior.experience : Number(injuryExperienceBefore[warrior.id])]));
  const warriors = document.campaign.warriors.map((warrior) => ({
    ...warrior,
    previous_experience: warrior.experience,
    experience: warrior.experience + (awards.get(warrior.id) ?? 0),
  }));
  const existingRows = post.pending_advances ?? [];
  const newRows = warriors.flatMap((warrior) => seededAdvances(warrior, previous.get(warrior.id) ?? warrior.experience, existingRows, knowledge));
  const postBattles = document.campaign.post_battles.map((row) => row.battle_number === post.battle_number ? {
    ...row,
    experience_applied: true,
    pending_advances: [...existingRows, ...newRows],
    event_log: [...(row.event_log ?? []), {
      step: 2,
      type: "experience",
      description: "Battle experience applied.",
    }],
  } : row);
  return { ok: true, document: withCampaign(document, { ...document.campaign, warriors, post_battles: postBattles }) };
}
