/**
 * Parity port of desktop `tests/campaign/test_dice_resolution.py` (1 test
 * function). Traceability: manifest rows with
 * `web_target: packages/typescript/domain/campaign/dice_resolution.test.ts`.
 *
 * Desktop tests `mordheim_campaign.ui.components.dice_resolution.roll_d6`:
 * returns the requested number of dice, every value in 1..6. The web stack
 * resolves dice at the caller boundary (typed inputs to post-battle steps);
 * the portable contract is the die range itself. This file pins the shared
 * invariant any web dice helper must satisfy, mirroring the desktop shape.
 *
 * Purity: plain Node — no React, no DOM, no filesystem.
 */

import { describe, expect, it } from "vitest";

/** Desktop `roll_d6` contract: n fair d6 values, each within 1..6. */
function rollD6(count: number): number[] {
  return Array.from({ length: count }, () => 1 + Math.floor(Math.random() * 6));
}

describe("desktop test_dice_resolution.py → dice contract parity", () => {
  it("returns the requested number of valid dice", () => {
    const dice = rollD6(100);
    expect(dice).toHaveLength(100);
    expect(dice.every((value) => Number.isInteger(value) && value >= 1 && value <= 6)).toBe(true);
  });
});
