/**
 * T10 — the campaign side of the Rout test (`raw-recruits--dont-mind-them`).
 *
 * The printed clause: "Any Raw Recruits who are running away or have been taken
 * out of action do not count towards the need to take a Rout test for the
 * warband." The battle-time test is combat (T13); the campaign owns the roster
 * fact, so `routTestFactsFor` reports which recorded participants count.
 *
 * The exemption itself is published data: the band rule names its recipients and
 * the artefact materialises the derived `rout_test_exempt` fact on the profile.
 *
 * Purity: plain Node, the real reader — no React, no DOM.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { routTestFactsFor } from "@domain/campaign/kernel/rout-test";
import type { CampaignDocument } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      // The build output first: T10's evidence is the freshly generated
      // artefact, while `outputs/` still holds the pre-T10 copy T12 regenerates.
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

const BAND = "lothern-sea-patrol-sar";

/** Committed band with one recorded battle: 3 Raw Recruits and 2 Sea Elves. */
function withBattle(outOfAction: readonly string[], participants?: readonly string[]): CampaignDocument {
  const document: unknown = {
    view: { selected_moment: "battle:1" },
    campaign: {
      identity: { campaign_name: "Patrol", warband_name: "Lothern", warband_type: "Lothern Sea Patrol", band_id: BAND, mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "recruits", name: "Raw Recruits", profile_name: "Raw Recruits", kind: "henchman", stats: {}, equipment: [], skills: [], experience: 0, cost: 0, quantity: 3, profile_id: "raw-recruits" },
        { id: "sea-elf", name: "Sea Elf", profile_name: "Sea Elf", kind: "hero", stats: {}, equipment: [], skills: [], experience: 0, cost: 0, quantity: 1, profile_id: "sea-elf" },
        { id: "sea-elf-2", name: "Sea Elf II", profile_name: "Sea Elf", kind: "hero", stats: {}, equipment: [], skills: [], experience: 0, cost: 0, quantity: 1, profile_id: "sea-elf" },
      ],
      battles: [
        {
          number: 1,
          date: "2026-09-27",
          scenario: "skirmish",
          opponent: "Audit",
          result: "win",
          gold_delta: 0,
          wyrdstone: 0,
          xp_delta: 0,
          casualties: outOfAction.length,
          advances: 0,
          rating_before: 0,
          rating_after: 0,
          models_before: 5,
          models_after: 5,
          out_of_action_ids: [...outOfAction],
          ...(participants
            ? { participants: participants.map((id) => ({ id, quantity: id === "recruits" ? 3 : 1 })) }
            : {}),
        },
      ],
      states: [{ number: 1, date: "2026-09-27", gold: 500, wyrdstone: 0, rating: 0, models: 5, max_models: 15, heroes: 2, henchmen: 3, experience: 0 }],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
  };
  return document as CampaignDocument;
}

describe.skipIf(!ARTEFACT_PATH)("T10 Rout-test roster facts (generated artefact)", () => {
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8"));
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("publishes the exemption on the recipients of the printed rule, and only on them", () => {
    const exempt = (artefact.profiles as { id: string; rout_test_exempt?: boolean }[])
      .filter((profile) => profile.rout_test_exempt === true)
      .map((profile) => profile.id);
    expect(exempt).toEqual(["raw-recruits"]);
    // The rule publishes its recipients; the derived fact follows them.
    const rule = (artefact.bands as { id: string }[]).find((band) => band.id === BAND);
    expect(rule).toBeDefined();
    const seaElf = reader.queryKnowledge({ id: { kind: "profile_id", value: "sea-elf" } });
    expect(seaElf.ok && seaElf.record.data["rout_test_exempt"]).toBeFalsy();
  });

  it("excludes the out-of-action Raw Recruits from the count and keeps the rest", () => {
    const facts = routTestFactsFor(withBattle(["recruits"]), reader, 1)!;
    expect(facts.models).toBe(5);
    expect(facts.counted_models).toBe(2);
    expect(facts.out_of_action_models).toBe(3);
    expect(facts.exempt_out_of_action_models).toBe(3);
    const recruits = facts.members.find((member) => member.warrior_id === "recruits")!;
    expect(recruits).toMatchObject({ exempt: true, out_of_action: true, counted_models: 0, quantity: 3 });
    // A Sea Elf out of action still counts: only the printed recipients are exempt.
    const other = routTestFactsFor(withBattle(["sea-elf"]), reader, 1)!;
    expect(other.counted_models).toBe(5);
    expect(other.out_of_action_models).toBe(1);
    expect(other.exempt_out_of_action_models).toBe(0);
  });

  it("keeps a Raw Recruit group that is still fighting in the count", () => {
    const facts = routTestFactsFor(withBattle([], ["recruits", "sea-elf", "sea-elf-2"]), reader, 1)!;
    expect(facts.counted_models).toBe(5);
    expect(facts.members.find((member) => member.warrior_id === "recruits")).toMatchObject({
      exempt: true,
      out_of_action: false,
      counted_models: 3,
    });
  });

  it("reads the battle snapshot, so a later roster change cannot rewrite history", () => {
    // The snapshot holds the group at battle strength even when the class has
    // since grown; the numbers follow the recorded battle.
    const facts = routTestFactsFor(withBattle(["recruits"], ["recruits", "sea-elf"]), reader, 1)!;
    expect(facts.models).toBe(4);
    expect(facts.counted_models).toBe(1);
    expect(routTestFactsFor(withBattle([]), reader, 99)).toBeNull();
  });
});
