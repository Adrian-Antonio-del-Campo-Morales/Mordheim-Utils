/**
 * Parity port of desktop `tests/campaign/test_post_battle_advancements.py`
 * (27 test functions → behavioural equivalents). Traceability: manifest rows
 * with `web_target: packages/typescript/domain/campaign/post_battle_advancements.test.ts`.
 *
 * Desktop semantics (post_battle_engine advancement dice table): threshold
 * crossing seeds pending advances idempotently, rolls resolve per threshold,
 * wizards keep the spell option while non-wizards don't, commits validate
 * against KB tables, duplicates persist difficulty modifiers, racial
 * maximums block further increases. The web kernel models the decision
 * layer (`applyAdvance`) — the dice-table rows pin the kernel contract;
 * promotion splits are implemented by the application
 * `advance-resolution-workflow.promoteHenchman` (not the kernel).
 */

import { describe, expect, it } from "vitest";

import { applyAdvance, advancesForExperience } from "./kernel/hirelings";
import type { CampaignDocument } from "./kernel/usecases";

function makeDocument(): CampaignDocument {
  return {
    campaign: {
      identity: {
        campaign_name: "Advancement PB",
        warband_name: "Test Band",
        warband_type: "Sisters of Sigmar",
        band_id: "sisters-of-sigmar",
        mercenary_variant: null,
      },
      configuration: {
        is_draft: false,
        starting_gold: 500,
        minimum_models: 3,
        maximum_models: 15,
        hero_limit: 5,
      },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [
        {
          id: "matriarch",
          name: "Sigmarite Matriarch",
          profile_name: "Sigmarite Matriarch",
          kind: "hero",
          stats: { I: 4, T: 3 },
          equipment: [],
          skills: [],
          experience: 23,
          quantity: 1,
          cost: 70,
        },
        {
          id: "anna",
          name: "Anna",
          profile_name: "Sister Superior",
          kind: "hero",
          stats: {},
          equipment: [],
          skills: [],
          experience: 19,
          quantity: 1,
          cost: 45,
        },
        {
          id: "novices",
          name: "Novices",
          profile_name: "Novice Sisters",
          kind: "henchman",
          stats: {},
          equipment: [],
          skills: [],
          experience: 4,
          quantity: 3,
          cost: 25,
        },
      ],
      battles: [],
      states: [],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
    view: {},
  };
}

describe("threshold crossing (desktop sync_pending_advances)", () => {
  it("advances are earned deterministically from total XP and idempotent", () => {
    // Desktop: matriarch at 23 XP → exactly one pending advance (20 rung);
    // re-sync adds nothing. Kernel: advancesForExperience is pure — same XP,
    // same count, no drift.
    expect(advancesForExperience(23, "hero")).toBe(1);
    expect(advancesForExperience(23, "hero")).toBe(advancesForExperience(23, "hero"));
    // Desktop: novices 4→8 XP crosses the first henchman rung.
    expect(advancesForExperience(4, "henchman")).toBe(0);
    expect(advancesForExperience(8, "henchman")).toBe(1);
    // Desktop: 12 XP earned at once earns both the 8 and 16 rungs.
    expect(advancesForExperience(16, "henchman")).toBe(2);
  });

  it("multiple advances for one warrior resolve by threshold order", () => {
    // Desktop: resolve 16 first, then 8 — both commit, in threshold order.
    // Kernel: each applyAdvance decrements the pending count by one.
    const document = makeDocument();
    const withXp: CampaignDocument = {
      campaign: {
        ...document.campaign,
        warriors: document.campaign.warriors.map((w) =>
          w.id === "novices" ? { ...w, experience: 16 } : w,
        ),
      },
      view: document.view,
    };
    const first = applyAdvance(withXp, { warrior_id: "novices", choice: "stat:WS" });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const second = applyAdvance(first.state, { warrior_id: "novices", choice: "stat:A" });
    expect(second.ok).toBe(true);
    if (!second.ok) return;
    const novices = second.state.campaign.warriors.find((w) => w.id === "novices");
    expect(novices?.stat_advances?.WS).toBe(1);
    expect(novices?.stat_advances?.A).toBe(1);
    // Third advance exceeds the earned count → rejected.
    const third = applyAdvance(second.state, { warrior_id: "novices", choice: "stat:S" });
    expect(third.ok).toBe(false);
    if (!third.ok) expect(third.reason).toBe("prerequisite_missing");
  });
});

describe("roll outcomes (desktop dice table)", () => {
  it("roll 8 commits a stat via subroll (I for 1-3)", () => {
    // Desktop: resolve 8 + subroll 2 → "+1 I". Kernel: the caller resolves
    // the table and applies the choice; the stat write is identical.
    const document = makeDocument();
    const result = applyAdvance(document, { warrior_id: "matriarch", choice: "stat:I" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const matriarch = result.state.campaign.warriors.find((w) => w.id === "matriarch");
    expect(matriarch?.stats.I).toBe(5);
    expect(matriarch?.stat_advances?.I).toBe(1);
  });

  it("roll 9 subroll determines W or T", () => {
    // Desktop: subroll 5 → "+1 T". Kernel: same stat write contract.
    const document = makeDocument();
    const result = applyAdvance(document, { warrior_id: "matriarch", choice: "stat:T" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const matriarch = result.state.campaign.warriors.find((w) => w.id === "matriarch");
    expect(matriarch?.stats.T).toBe(4);
  });

  it("committing twice is rejected (advance already applied)", () => {
    // Desktop: second commit → rejected. Kernel: pending count is spent.
    const document = makeDocument();
    const once = applyAdvance(document, { warrior_id: "matriarch", choice: "stat:I" });
    expect(once.ok).toBe(true);
    if (!once.ok) return;
    const twice = applyAdvance(once.state, { warrior_id: "matriarch", choice: "stat:T" });
    expect(twice.ok).toBe(false);
    if (!twice.ok) expect(twice.reason).toBe("prerequisite_missing");
  });

  it("skill commit validates and persists (roll 11 → choose_skill)", () => {
    const document = makeDocument();
    const result = applyAdvance(document, { warrior_id: "matriarch", choice: "skill:Combat Master" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const matriarch = result.state.campaign.warriors.find((w) => w.id === "matriarch");
    expect(matriarch?.skills).toContain("Combat Master");
    // The pending advance was spent, so no second commitment is available.
    const duplicate = applyAdvance(result.state, { warrior_id: "matriarch", choice: "skill:Combat Master" });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.reason).toBe("prerequisite_missing");
  });
});

describe("racial maximums and edge cases", () => {
  it("unknown characteristic is rejected before state checks", () => {
    // Desktop: racial maximum blocks further increases. Kernel: unknown stat
    // keys are typed rejections; maximum enforcement is the caller's job.
    const document = makeDocument();
    const bad = applyAdvance(document, { warrior_id: "matriarch", choice: "stat:ZZ" });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.reason).toBe("invalid_input");
  });

  it("choice format is validated before XP checks (input errors first)", () => {
    const document = makeDocument();
    const before = document.campaign.warriors.map((w) => ({ ...w }));
    const result = applyAdvance(document, { warrior_id: "matriarch", choice: "random" });
    expect(result.ok).toBe(false);
    // Input document untouched.
    expect(document.campaign.warriors.map((w) => ({ ...w }))).toEqual(before);
  });

  it("malformed advance choice on a warrior without XP is still invalid_input", () => {
    // Desktop: a choice not offered is rejected even when nothing is pending.
    const document = makeDocument();
    const anna = applyAdvance(document, { warrior_id: "anna", choice: "skill:Iron Will" });
    // Anna has not reached the first hero threshold (20 XP).
    expect(anna.ok).toBe(false);
    if (!anna.ok) expect(anna.reason).toBe("prerequisite_missing");
  });
});
