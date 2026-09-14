/**
 * Experience and advances workflow: the
 * application feature block over the kernel's `applyAdvance` use case.
 *
 * What this adds beyond the kernel:
 * - **Pending read model**: per warrior, advances earned (XP vs the shared
 *   threshold table) minus advances taken (`stat_advances` + learned
 *   skills) — the list the UI renders;
 * - **Choice orchestration**: applying a `stat:<KEY>` / `skill:<name>`
 *   choice through the service, with the rejection-as-value convention;
 * - **Export safety**: choices mutate only warrior rows (`stat_advances`,
 *   `skills`, `stats`), which the v5 contract snapshots verbatim — no
 *   payload rewriting here.
 *
 * The kernel remains the only document mutator. Purity: plain Node.
 */
import type { CampaignDocument, IdString, UseCaseResult } from "../../../../domain/campaign/kernel/usecases";
import type {
  CampaignUseCases,
  Warrior,
} from "../../../../domain/campaign/kernel/usecases";
import { advancesForExperience } from "../../../../domain/campaign/kernel/hirelings";

/** One warrior's advance ledger, for the UI list. */
export interface WarriorAdvanceStatus {
  readonly warrior_id: IdString;
  readonly warrior_name: string;
  readonly kind: Warrior["kind"];
  readonly experience: number;
  readonly earned: number;
  readonly taken: number;
  readonly pending: number;
  /** Learned skills so far (profile-inherent excluded). */
  readonly learned_skills: readonly string[];
  /** Characteristic points taken, by stat key. */
  readonly stat_advances: Readonly<Record<string, number>>;
  /** Hirelings never take advances — the UI hides the picker. */
  readonly eligible: boolean;
}

export interface AdvancesOverview {
  readonly warriors: readonly WarriorAdvanceStatus[];
  readonly total_pending: number;
}

/**
 * Skills a warrior learned in play (not part of the starting kit).
 *
 * The kernel's `applyAdvance` uses the same rule: without a starting-kit
 * marker every listed skill counts as learned. Over-counting taken
 * advances can only *hide* a pending advance, never grant an unearned one.
 */
function learnedSkills(warrior: Warrior): readonly string[] {
  return [...new Set(warrior.skills)];
}

/** Read model for the advances panel. */
export function advancesOverview(document: CampaignDocument): AdvancesOverview {
  const warriors = document.campaign.warriors.map((warrior: Warrior) => {
    const earned = advancesForExperience(warrior.experience, warrior.kind === "hero" ? "hero" : "henchman");
    const statTaken = warrior.stat_advances
      ? Object.values(warrior.stat_advances).reduce((total, value) => total + value, 0)
      : 0;
    const skillsTaken = new Set(learnedSkills(warrior)).size;
    const taken = statTaken + skillsTaken;
    const pending = warrior.kind === "hireling" ? 0 : Math.max(0, earned - taken);
    return {
      warrior_id: warrior.id,
      warrior_name: warrior.name,
      kind: warrior.kind,
      experience: warrior.experience,
      earned,
      taken,
      pending,
      learned_skills: [...new Set(learnedSkills(warrior))],
      stat_advances: warrior.stat_advances ?? {},
      eligible: warrior.kind !== "hireling",
    };
  });
  return {
    warriors,
    total_pending: warriors.reduce((total, w) => total + w.pending, 0),
  };
}

/** Apply one advance choice (`stat:<KEY>` or `skill:<name>`) to a warrior. */
export function applyAdvanceChoice(
  useCases: CampaignUseCases,
  document: CampaignDocument,
  warriorId: IdString,
  choice: string,
  table: string = "common",
): UseCaseResult {
  return useCases.applyAdvance(document, { warrior_id: warriorId, table, choice });
}
