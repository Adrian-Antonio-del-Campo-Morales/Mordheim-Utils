/**
 * P6.5 acceptance tests: the injuries & recovery workflow over the immutable
 * document helpers — driven from the shapes the `pending-post-battle.json`
 * contract fixture and the desktop post-battle engine produce.
 *
 * Asserted behaviour (plan §P6.5):
 * - read model: injured/absent/pending-roll rows and the restriction flag;
 * - applying an outcome updates the warrior immutably (no input mutation);
 * - absence (`games_to_miss`) lifts only through recovery;
 * - unresolved rolls park on the pending post-battle and stay resumable;
 * - effects this port does not interpret are preserved, not dropped.
 */

import { describe, expect, it } from "vitest";

import type {
  CampaignDocument,
  OpenPayload,
  Warrior,
} from "../../../../domain/campaign/kernel/state";
import {
  applyInjuryOutcome,
  injuryOverview,
  recordFollowUp,
  recover,
  resolveFollowUp,
} from "./injuries-workflow";

function warrior(overrides: Partial<Warrior>): Warrior {
  return {
    id: "w1",
    name: "Sigrid",
    profile_name: "Captain",
    kind: "hero",
    stats: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    equipment: [],
    skills: [],
    experience: 5,
    cost: 35,
    manual_log: [],
    ...overrides,
  } as Warrior;
}

function documentWith(warriors: Warrior[], pendingFollowUps: OpenPayload[] = []): CampaignDocument {
  return {
    campaign: {
      identity: { band_id: "witch_hunters", name: "Sigmar's Shield", is_draft: false },
      configuration: {
        band_id: "witch_hunters",
        band_name: "Witch Hunters",
        is_draft: false,
        starting_gold: 500,
        minimum_models: 3,
        maximum_models: 15,
        hero_limit: 4,
      },
      resources: { gold: 100, wyrdstone_shards: 0 },
      current_state_number: 1,
      warriors,
      battles: [],
      states: [],
      post_battles: [
        {
          battle_number: 1,
          complete: false,
          active_step: 4,
          completed_steps: [0, 1, 2, 3],
          review_open: false,
          pending_follow_ups: pendingFollowUps,
        },
      ],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
    view: {},
  } as unknown as CampaignDocument;
}

const base = () => documentWith([warrior({})]);

describe("injuryOverview", () => {
  it("reports condition, absence and restriction per warrior", () => {
    const doc = documentWith([
      warrior({ games_to_miss: 2, absence_reason: "Smashed hand" }),
      warrior({ condition: "Injured", condition_detail: "eye_injury" }),
      warrior({}),
    ]);
    const overview = injuryOverview(doc);
    expect(overview.total_restricted).toBe(1);
    expect(overview.warriors[0]).toMatchObject({
      warrior_id: "w1",
      games_to_miss: 2,
      absence_reason: "Smashed hand",
      restricted: true,
    });
    expect(overview.warriors[1]).toMatchObject({ condition: "Injured", restricted: false });
    expect(overview.warriors[2].restricted).toBe(false);
  });

  it("lists injury follow-ups parked on the pending post-battle", () => {
    const doc = documentWith([warrior({})], [
      { id: "injury:w1:mangled_leg", type: "injury_roll", warrior_id: "w1", description: "Roll" },
      { id: "other", type: "sale", description: "Sell" },
    ]);
    const overview = injuryOverview(doc);
    expect(overview.open_rolls).toHaveLength(1);
    expect(overview.open_rolls[0]).toMatchObject({ id: "injury:w1:mangled_leg" });
    expect(overview.warriors[0].pending_follow_ups).toHaveLength(1);
  });
});

describe("applyInjuryOutcome", () => {
  it("applies missed games + condition + stat modifier and records history", () => {
    const result = applyInjuryOutcome(base(), {
      warrior_id: "w1",
      result_id: "smashed_hand",
      result: "Smashed hand",
      effects: [
        { kind: "miss_games", value: 2 },
        { kind: "add_condition", condition_id: "smashed_hand" },
        { kind: "stat_modifier", stat: "WS", value: -1 },
      ],
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const warrior = result.document.campaign.warriors[0];
    expect(warrior.games_to_miss).toBe(2);
    expect(warrior.absence_reason).toBe("Smashed hand");
    expect(warrior.condition).toBe("Injured");
    expect(warrior.condition_detail).toBe("smashed_hand");
    expect(warrior.stat_modifiers).toEqual({ WS: -1 });
    expect(warrior.injury_records).toHaveLength(1);
    expect(warrior.injury_records?.[0]).toMatchObject({ result_id: "smashed_hand" });
  });

  it("does not mutate the input document", () => {
    const doc = base();
    const before = structuredClone(doc);
    const result = applyInjuryOutcome(doc, {
      warrior_id: "w1",
      result_id: "mangled_leg",
      result: "Mangled leg",
      effects: [{ kind: "miss_games", value: 1 }],
    });
    expect(result.ok).toBe(true);
    expect(doc).toEqual(before);
  });

  it("rejects unknown warriors and non-positive miss_games", () => {
    expect(applyInjuryOutcome(base(), { warrior_id: "nope", result_id: "x", result: "X" }).ok).toBe(false);
    const bad = applyInjuryOutcome(base(), {
      warrior_id: "w1",
      result_id: "x",
      result: "X",
      effects: [{ kind: "miss_games", value: 0 }],
    });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.reason).toBe("invalid_input");
  });

  it("preserves uninterpreted effects as a parked follow-up (open-payload policy)", () => {
    const result = applyInjuryOutcome(base(), {
      warrior_id: "w1",
      result_id: "bitter_rivalry",
      result: "Bitter rivalry",
      effects: [{ kind: "mysterious_curse", strength: 3 } as never],
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.document.campaign.post_battles[0];
    expect(post.pending_follow_ups).toHaveLength(1);
    expect(post.pending_follow_ups?.[0]).toMatchObject({
      type: "injury_roll",
      warrior_id: "w1",
    });
  });
});

describe("follow-ups and recovery", () => {
  it("records, resolves and clears a parked follow-up", () => {
    const parked = recordFollowUp(base(), {
      warrior_id: "w1",
      result_id: "mangled_leg",
      description: "Resolve the sub-table roll.",
    });
    expect(parked.ok).toBe(true);
    if (!parked.ok) return;
    const id = "injury:w1:mangled_leg";
    const resolved = resolveFollowUp(parked.document, {
      follow_up_id: id,
      outcome: {
        warrior_id: "w1",
        result_id: "multiple_amputation",
        result: "Multiple amputation",
        effects: [{ kind: "stat_modifier", stat: "A", value: -1 }],
      },
    });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    expect(resolved.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(0);
    expect(resolved.document.campaign.warriors[0].stat_modifiers).toEqual({ A: -1 });
    // The follow-up is gone: resolving the same id again is a typed not_found.
    const again = resolveFollowUp(resolved.document, { follow_up_id: id, outcome: { warrior_id: "w1", result_id: "x", result: "X" } });
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.reason).toBe("not_found");
  });

  it("requires a pending post-battle to park a roll", () => {
    const doc = base();
    const closed: CampaignDocument = {
      ...doc,
      campaign: {
        ...doc.campaign,
        post_battles: [{ ...doc.campaign.post_battles[0], complete: true }],
      },
    };
    const result = recordFollowUp(closed, { warrior_id: "w1", result_id: "x", description: "d" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("conflict");
  });

  it("recovery decrements, blocks battles until zero, then clears the absence", () => {
    const doc = documentWith([warrior({ games_to_miss: 2, absence_reason: "Smashed hand", condition: "Injured", condition_detail: "smashed_hand" })]);
    const one = recover(doc, "w1");
    expect(one.ok).toBe(true);
    if (!one.ok) return;
    const row = injuryOverview(one.document).warriors[0];
    expect(row.games_to_miss).toBe(1);
    expect(row.restricted).toBe(true);
    expect(row.absence_reason).toBe("Smashed hand");
    const two = recover(one.document, "w1");
    expect(two.ok).toBe(true);
    if (!two.ok) return;
    const done = injuryOverview(two.document).warriors[0];
    expect(done.games_to_miss).toBe(0);
    expect(done.restricted).toBe(false);
    expect(done.absence_reason).toBeNull();
    expect(done.condition).toBeNull();
    expect("absence_reason" in two.document.campaign.warriors[0]).toBe(false);
    expect(recover(two.document, "w1").ok).toBe(false);
    expect(recover(doc, "ghost").ok).toBe(false);
  });
});
