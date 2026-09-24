/**
 * Parity port of desktop `tests/python/campaign/test_post_battle_resolution.py`
 * (9 test functions → behavioural equivalents). Traceability: manifest rows
 * with `web_target: tests/typescript/domain/campaign/post_battle_resolution.test.ts`.
 *
 * Driven by the real web KB artefact — every expectation is pinned to the
 * published campaign catalogue rows, mirroring the desktop test.
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import {
  PostBattleResolver,
  type ResolverArtefact,
} from "@domain/campaign/post_battle_resolution";

const ARTEFACT = JSON.parse(
  readFileSync(
    resolve(__dirname, "../../../../outputs/web-public/knowledge/knowledge-web.json"),
    "utf-8",
  ),
) as ResolverArtefact;

function resolver(): PostBattleResolver {
  return new PostBattleResolver(ARTEFACT);
}

describe("hero serious injuries (KB chart)", () => {
  it("hero serious injury rows are KB rows", () => {
    const r = resolver();
    const expectations: [number, string][] = [
      [11, "Dead"], [15, "Dead"],
      [16, "Multiple Injuries"], [21, "Multiple Injuries"],
      [22, "Leg Wound"], [24, "Madness"], [25, "Smashed Leg"],
      [31, "Blinded In One Eye"], [46, "Full Recovery"], [55, "Full Recovery"],
      [56, "Bitter Enmity"], [61, "Captured"], [62, "Hardened"],
      [66, "Survives Against The Odds"],
    ];
    for (const [d66, expected] of expectations) {
      expect(r.resolveHeroSeriousInjury(d66).result, `d66 ${d66}`).toBe(expected);
    }
    const dead = r.resolveHeroSeriousInjury(11);
    expect(dead.effects).toContain("The warrior is permanently removed from the roster.");
    const leg = r.resolveHeroSeriousInjury(22);
    expect(leg.effects[0]).toContain("movement");
    expect(leg.effects[0]).toContain("-1");
    const multiple = r.resolveHeroSeriousInjury(21);
    expect(multiple.follow_up).not.toBeNull();
    expect(multiple.follow_up).toContain("again");
    // Madness needs the follow-up D6 subtable.
    expect(r.resolveHeroSeriousInjury(24).follow_up).not.toBeNull();
  });

  it("serious injury effects expose concrete details and KB notes", () => {
    const r = resolver();
    const oldWound = r.resolveHeroSeriousInjury(32);
    expect(oldWound.effects[0]).toContain("Before each battle roll D6");
    expect(oldWound.effects[0]).toContain("on 1");

    const blinded = r.resolveHeroSeriousInjury(31);
    expect(blinded.effects[0].toLowerCase()).toContain("ballistic skill");
    expect(blinded.note?.toLowerCase()).toContain("remaining good eye");

    const captured = r.resolveHeroSeriousInjury(61);
    expect(captured.effects[0].toLowerCase()).toContain("equipment remains");
    expect(captured.note?.toLowerCase()).toContain("ransom");
  });

  it("hero d66 chart regions follow row-major order", () => {
    const r = resolver();
    // Row 16-21 covers the corner rolls 16 and 21; both Multiple Injuries.
    expect(r.resolveHeroSeriousInjury(16).result).toBe("Multiple Injuries");
    expect(r.resolveHeroSeriousInjury(21).result).toBe("Multiple Injuries");
    // 41-55 covers the recovery square; 56 is separate.
    for (const d66 of [41, 44, 46, 51, 55]) {
      expect(r.resolveHeroSeriousInjury(d66).result, `d66 ${d66}`).toBe("Full Recovery");
    }
    expect(r.resolveHeroSeriousInjury(56).result).toBe("Bitter Enmity");
    // 62-63 covers both corners.
    expect(r.resolveHeroSeriousInjury(62).result).toBe("Hardened");
    expect(r.resolveHeroSeriousInjury(63).result).toBe("Hardened");
  });
});

describe("henchman survival (KB chart)", () => {
  it("henchman survival chart", () => {
    const r = resolver();
    expect(r.resolveHenchmanSeriousInjury(1).result).toBe("Removed");
    expect(r.resolveHenchmanSeriousInjury(2).result).toBe("Removed");
    for (const roll of [3, 4, 5, 6]) {
      const outcome = r.resolveHenchmanSeriousInjury(roll);
      expect(outcome.result).toBe("Full Recovery");
      expect(outcome.effects).toEqual([]);
    }
  });
});

describe("KB looking-glass values", () => {
  it("advance thresholds, rating and racial maximums come from the KB", () => {
    const r = resolver();
    expect(r.advanceThresholds("hero").length).toBeGreaterThan(0);
    expect(r.advanceThresholds("hero")).toEqual([2, 4, 6, 8, 11, 14, 17, 20, 24, 28, 32, 36, 41, 46, 51, 57, 63, 69, 76, 83, 90]);
    expect(r.advanceThresholds("henchman")).toEqual([2, 5, 9, 14]);
    // Warband rating: 5 per model + 1 per XP.
    expect(r.warbandRating(8, 85)).toBe(125);
    // Racial maximums caps keyed by race (artefact uses full stat names).
    const maximums = r.racialMaximums();
    expect(maximums["human"]?.["weapon_skill"]).toBe(6);
    expect(maximums["human"]?.["strength"]).toBe(4);
    expect(maximums["elf"]?.["movement"]).toBe(5);
    expect(maximums["elf"]?.["initiative"]).toBe(9);
  });
});

describe("exploration (KB charts)", () => {
  it("exploration shards by total", () => {
    const r = resolver();
    expect(r.resolveExploration([1, 1, 1, 1]).shards).toBe(1); // total 4
    expect(r.resolveExploration([3, 3, 5, 6]).shards).toBe(3); // total 17
    expect(r.resolveExploration([6, 6, 6, 6]).shards).toBe(4); // total 24
    // Empty roll yields no shards and no match.
    expect(r.resolveExploration([]).shards).toBe(0);
  });

  it("exploration matching dice special results", () => {
    const r = resolver();
    const pair = r.resolveExploration([3, 3, 5, 6]);
    expect(pair.matches).toEqual([[3, 2, "Corpse"]]);
    expect(pair.matching_dice_note).toContain("Corpse");
    const triple = r.resolveExploration([2, 2, 2, 5]);
    expect(triple.matches).toEqual([[2, 3, "Smithy"]]);
    // No special when every die differs.
    expect(r.resolveExploration([1, 2, 4, 6]).matches).toEqual([]);
    // Largest set wins over a smaller pair.
    const mixed = r.resolveExploration([4, 4, 4, 5, 5]);
    expect(mixed.matches).toEqual([[4, 3, "Fletcher"]]);
  });

  it("exploration dice allocation caps at six", () => {
    const r = resolver();
    expect(r.explorationDice(4, false)).toBe(4);
    expect(r.explorationDice(4, true)).toBe(5);
    expect(r.explorationDice(9, true)).toBe(6);
    expect(r.explorationDice(0, false)).toBe(0);
  });
});

describe("rarity search (KB trading post)", () => {
  it("rarity search against trading post", () => {
    const r = resolver();
    // Holy Tome is rare 8 in the Trading Post.
    expect(r.resolveRaritySearch("holy_tome", 8)).toMatchObject({ rarity: 8, success: true });
    expect(r.resolveRaritySearch("holy_tome", 7).success).toBe(false);
    // Common items need no test.
    const dagger = r.resolveRaritySearch("dagger", 2);
    expect(dagger.rarity).toBeNull();
    expect(dagger.success).toBe(true);
    // Modifiers shift the target down (e.g. +1 to rare rolls).
    expect(r.resolveRaritySearch("holy_tome", 7, 1).success).toBe(true);
    // Items without a sellable Trading Post row cannot be searched.
    expect(r.resolveRaritySearch("hochland_long_rifle", 12).success).toBe(false);
  });
});
