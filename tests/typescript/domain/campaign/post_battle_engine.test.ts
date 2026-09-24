/**
 * Parity port of desktop `tests/python/campaign/test_post_battle_engine.py`.
 *
 * The web kernel currently exposes post-battle navigation and preservation of
 * open payloads, while the desktop engine also owns injuries, exploration,
 * recruitment and commit projections. The portable tests below pin the
 * behaviours available at the frozen domain boundary; the post-battle
 * workflows (exploration, injuries, recruitment, equipment obligations and
 * commit) now live on the service.
 */
import { describe, expect, it } from "vitest";
import { resolvePostBattleStep, POST_BATTLE_STEP_COUNT } from "@domain/campaign/kernel/post-battle-steps";
import type { CampaignDocument } from "@domain/campaign/kernel/state";

function document(): CampaignDocument {
  return {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: {
        campaign_name: "Post Battle",
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
      current_state_number: 1,
      warriors: [
        {
          id: "hero-1",
          name: "Sigrid",
          profile_name: "Matriarch",
          kind: "hero",
          stats: { M: 4, WS: 4 },
          equipment: [],
          skills: [],
          experience: 10,
          cost: 65,
        },
      ],
      battles: [],
      states: [{
        number: 1,
        date: "2026-09-10",
        gold: 500,
        wyrdstone: 2,
        rating: 15,
        models: 1,
        max_models: 15,
        heroes: 1,
        henchmen: 0,
        experience: 10,
      }],
      post_battles: [{
        battle_number: 1,
        complete: false,
        active_step: 0,
        completed_steps: [],
        review_open: false,
        gold_delta: 20,
        wyrdstone_delta: 1,
        step_state: {},
        pending_follow_ups: [],
      }],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
  };
}

describe("desktop test_post_battle_engine.py → post-battle state parity", () => {
  it("starts with the expected projected resource deltas", () => {
    const current = document().campaign.post_battles[0];
    expect(current.gold_delta).toBe(20);
    expect(current.wyrdstone_delta).toBe(1);
    expect(document().campaign.states[0].gold + (current.gold_delta ?? 0)).toBe(520);
    expect(document().campaign.states[0].wyrdstone + (current.wyrdstone_delta ?? 0)).toBe(3);
  });

  it("resolves post-battle steps in order and records completion", () => {
    let current = document();
    for (let step = 0; step < POST_BATTLE_STEP_COUNT; step += 1) {
      const result = resolvePostBattleStep(current, 1, { source: "desktop-parity", step });
      expect(result.ok).toBe(true);
      if (!result.ok) return;
      current = result.state;
      const post = current.campaign.post_battles[0];
      expect(post.active_step).toBe(step + 1);
      expect(post.completed_steps).toEqual(Array.from({ length: step + 1 }, (_, index) => index));
      expect(post.step_state?.[String(step)]).toEqual({ source: "desktop-parity", step });
    }
    const post = current.campaign.post_battles[0];
    expect(post.complete).toBe(true);
    expect(post.review_open).toBe(true);
  });

  it("preserves step-local payloads verbatim", () => {
    const payload = {
      selected_warrior_id: "hero-1",
      rolls: [1, 4, 6],
      nested: { outcome: "full-recovery" },
    };
    const result = resolvePostBattleStep(document(), 1, payload);
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.state.campaign.post_battles[0].step_state?.["0"]).toEqual(payload);
  });

  it("does not leave the injuries step while a casualty or follow-up is unresolved", () => {
    const base=document(),blocked={...base,campaign:{...base.campaign,battles:[{number:1,date:"2026-09-10",scenario:"skirmish",opponent:"Undead",result:"loss",gold_delta:0,wyrdstone:0,xp_delta:0,casualties:1,advances:0,rating_before:15,rating_after:15,models_before:1,models_after:1,out_of_action_ids:["hero-1"]}],post_battles:[{...base.campaign.post_battles[0],pending_follow_ups:[{id:"injury:hero-1",step:"injuries",type:"injury_roll",warrior_id:"hero-1"}]}]}};
    const unresolved=resolvePostBattleStep(blocked,1,{});expect(unresolved.ok).toBe(false);if(!unresolved.ok)expect(unresolved.reason).toBe("prerequisite_missing");
    const ready={...blocked,campaign:{...blocked.campaign,post_battles:[{...blocked.campaign.post_battles[0],pending_follow_ups:[],step_state:{injuries:{"hero-1:1":{resolved:true}}}}]}};
    expect(resolvePostBattleStep(ready,1,{}).ok).toBe(true);
  });

  it("rejects resolving a different battle than the pending sequence", () => {
    const result = resolvePostBattleStep(document(), 99, {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("conflict");
  });

  it("rejects resolving after all post-battle steps are complete", () => {
    let current = document();
    for (let step = 0; step < POST_BATTLE_STEP_COUNT; step += 1) {
      const result = resolvePostBattleStep(current, 1, {});
      expect(result.ok).toBe(true);
      if (!result.ok) return;
      current = result.state;
    }
    const rejected = resolvePostBattleStep(current, 1, {});
    expect(rejected.ok).toBe(false);
    if (!rejected.ok) expect(rejected.reason).toBe("not_found");
  });

  it("does not mutate the source document while resolving a step", () => {
    const before = document();
    const snapshot = JSON.stringify(before);
    const result = resolvePostBattleStep(before, 1, { value: 7 });
    expect(result.ok).toBe(true);
    expect(JSON.stringify(before)).toBe(snapshot);
  });

  it("keeps campaign state separate from view selection", () => {
    const before = document();
    const result = resolvePostBattleStep(before, 1, { value: 7 });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.state.view).toEqual(before.view);
      expect(result.state.campaign.identity).toEqual(before.campaign.identity);
    }
  });

  it("keeps pending resource deltas when advancing a step", () => {
    const before = document();
    const result = resolvePostBattleStep(before, 1, { gold_delta: 35, wyrdstone_sold: 1 });
    expect(result.ok).toBe(true);
    if (result.ok) {
      const post = result.state.campaign.post_battles[0];
      expect(post.gold_delta).toBe(20);
      expect(post.wyrdstone_delta).toBe(1);
      expect(post.step_state?.["0"]).toEqual({ gold_delta: 35, wyrdstone_sold: 1 });
    }
  });

  // Exploration, injuries, recruitment, equipment obligations and commit
  // projection are exposed through the application service.
});
