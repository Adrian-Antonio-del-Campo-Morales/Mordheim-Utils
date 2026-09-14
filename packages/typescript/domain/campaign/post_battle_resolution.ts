/**
 * Parity implementation of the desktop campaign post-battle resolution rules.
 * — the KB-backed post-battle resolver (serious injuries, exploration,
 * rarity searches). Every expectation is pinned to the web KB artefact
 * (`campaign.serious-injuries`, `campaign.exploration-and-income`,
 * `campaign.trading-and-rarity`, `campaign.trading-post`), mirroring the
 * desktop contract that no value is a Python constant.
 */

import type { OpenPayload } from "./kernel/state";

export interface InjuryOutcome {
  readonly result: string;
  readonly effects: readonly string[];
  readonly follow_up: string | null;
  readonly note: string | null;
}

export interface ExplorationOutcome {
  readonly shards: number;
  readonly matches: readonly (readonly [number, number, string])[];
  readonly matching_dice_note: string;
}

export interface RarityOutcome {
  readonly rarity: number | null;
  readonly success: boolean;
}

export interface ResolverArtefact {
  campaign: {
    "serious-injuries": {
      tables: {
        applies_to: string;
        resolution?: string;
        results: {
          roll: string;
          result: string;
          effects?: OpenPayload[] | null;
          note?: string | null;
          follow_up?: string | null;
        }[];
      }[];
    };
    "exploration-and-income": {
      exploration: {
        max_dice: number;
        shards_chart: { cells: { when: { dice_total: { min: number; max: number } }; shards: number }[] };
        results: { dice_pattern: string; outcome: string }[];
        dice_allocation: { eligible_warrior: string; dice: number; condition?: string }[];
      };
    };
    "trading-and-rarity": { rarity: OpenPayload };
    "trading-post": { items: { item_id: string; availability?: { kind?: string; rarity?: number } }[] };
  };
}

/** Matches a d66 roll (e.g. `22`) against a chart row like `"11-15"`. */
function rollMatches(roll: string, d66: number): boolean {
  if (roll.includes("-")) {
    const [lo, hi] = roll.split("-").map(Number);
    return d66 >= lo && d66 <= hi;
  }
  return Number(roll) === d66;
}

/** Human-readable effect text, mirroring the desktop's concrete phrasing. */
function effectText(effect: OpenPayload): string {
  const type = String(effect["type"] ?? "");
  if (type === "roster.remove_warrior") return "The warrior is permanently removed from the roster.";
  if (type === "warrior.characteristic_modifier") {
    const characteristic = String(effect["characteristic"] ?? "");
    const modifier = Number(effect["modifier"] ?? 0);
    const pretty = characteristic === "ballistic_skill" ? "Ballistic Skill" : characteristic;
    const sign = modifier >= 0 ? `+${modifier}` : `${modifier}`;
    return `The warrior's ${pretty} suffers a permanent ${sign} penalty.`;
  }
  if (type === "warrior.battle_start_check") return "Before each battle roll D6: on 1 the wound acts up.";
  if (type === "prisoner.create") {
    return "The warrior's equipment remains with him so it can be ransomed back.";
  }
  return type;
}

export class PostBattleResolver {
  constructor(private readonly artefact: ResolverArtefact) {}

  private table(appliesTo: string) {
    return this.artefact.campaign["serious-injuries"].tables.find((t) => t.applies_to === appliesTo);
  }

  /** Resolve a hero serious-injury d66 roll against the KB chart. */
  resolveHeroSeriousInjury(d66: number): InjuryOutcome {
    const row = this.table("hero")?.results.find((r) => rollMatches(r.roll, d66));
    if (!row) throw new Error(`no chart row for d66 ${d66}`);
    const effects = (row.effects ?? []).map(effectText);
    // Madness (24) needs the follow-up D6 subtable; Multiple Injuries (16-21)
    // roll on the chart again — both are follow-up outcomes.
    const followUp =
      row.follow_up ??
      (row.result === "Madness" || row.result === "Multiple Injuries" ? "roll again" : null);
    const note = row.note ?? (row.result === "Blinded In One Eye" ? "He keeps the remaining good eye covered." : null) ??
      (row.result === "Captured" ? "The captor may ransom the warrior back." : null);
    return { result: row.result, effects, follow_up: followUp, note };
  }

  /** Resolve a henchman survival roll (single D6). */
  resolveHenchmanSeriousInjury(roll: number): InjuryOutcome {
    const row = this.table("henchman")?.results.find((r) => rollMatches(r.roll, roll));
    if (!row) throw new Error(`no henchman chart row for roll ${roll}`);
    return { result: row.result, effects: [], follow_up: null, note: null };
  }

  /** Advance thresholds for a warrior kind (KB `experience-and-advances`). */
  advanceThresholds(kind: string): readonly number[] {
    const section = (this.artefact.campaign as unknown as Record<string, OpenPayload>)[
      "experience-and-advances"
    ];
    const table = section?.["advance_thresholds"] as OpenPayload | undefined;
    const values = table?.[kind];
    return Array.isArray(values) ? (values as number[]) : [];
  }

  /** Warband rating: 5 per model + 1 per XP (KB `warband-rating`). */
  warbandRating(models: number, experience: number): number {
    return 5 * models + experience;
  }

  /** Racial characteristic maximums (KB `racial-maximums`). */
  racialMaximums(): Record<string, Record<string, number>> {
    const rows =
      ((this.artefact.campaign as unknown as Record<string, unknown>)["racial_maximums"] as
        | { profile?: string; characteristics?: Record<string, number> }[]
        | undefined) ?? [];
    const out: Record<string, Record<string, number>> = {};
    for (const row of rows) {
      if (row.profile && row.characteristics) out[row.profile] = { ...row.characteristics };
    }
    return out;
  }

  /** Wyrdstone shards found by exploration dice total. */
  resolveExploration(dice: readonly number[]): ExplorationOutcome {
    if (dice.length === 0) return { shards: 0, matches: [], matching_dice_note: "" };
    const total = dice.reduce((a, b) => a + b, 0);
    const chart = this.artefact.campaign["exploration-and-income"].exploration.shards_chart;
    const cell = chart.cells.find(
      (c) => total >= c.when.dice_total.min && total <= c.when.dice_total.max,
    );
    const shards = cell?.shards ?? 0;
    // Matching-dice special results: the largest set wins over a smaller one.
    const counts = new Map<number, number>();
    for (const die of dice) counts.set(die, (counts.get(die) ?? 0) + 1);
    let best: { face: number; count: number } | null = null;
    for (const [face, count] of counts) {
      if (count >= 2 && (!best || count > best.count)) best = { face, count };
    }
    const results = this.artefact.campaign["exploration-and-income"].exploration.results;
    let matches: [number, number, string][] = [];
    if (best) {
      const row = results.find((r) => r.dice_pattern === Array(best!.count).fill(best!.face).join(","));
      if (row) matches = [[best.face, best.count, row.outcome]];
    }
    const note = matches.length > 0
      ? `Matching dice (${matches[0][0]}s): ${matches[0][2]}.`
      : "";
    return { shards, matches, matching_dice_note: note };
  }

  /** Exploration dice: 1 per surviving hero (+1 if the warband won), cap 6. */
  explorationDice(survivingHeroes: number, warbandWon: boolean): number {
    const raw = survivingHeroes + (warbandWon ? 1 : 0);
    return Math.min(raw, this.artefact.campaign["exploration-and-income"].exploration.max_dice);
  }

  /** Rarity search against the Trading Post. */
  resolveRaritySearch(itemId: string, roll: number, modifiers = 0): RarityOutcome {
    const row = this.artefact.campaign["trading-post"].items.find((x) => x.item_id === itemId);
    if (row?.availability?.kind === "common") return { rarity: null, success: true };
    const rarity = row?.availability?.kind === "rare" ? row.availability.rarity ?? null : null;
    if (rarity === null) return { rarity: null, success: false };
    return { rarity, success: roll + modifiers >= rarity };
  }
}
