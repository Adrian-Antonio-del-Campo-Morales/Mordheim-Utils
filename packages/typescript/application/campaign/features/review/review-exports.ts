/**
 * P6.8 (web-migration-parallel-plan.md §7): final review & auxiliary
 * exports — the read models the pre-export review panel renders and the
 * plain-text auxiliary exports (roster summary, campaign ledger) the user
 * can download beside the main `.mordheim` file.
 *
 * Rule discipline (plan §P6.8 acceptance): exporters are **pure projections
 * of the current document** — they never mutate it, never call use cases,
 * never derive new campaign facts. The no-rules guarantee is asserted in
 * `review-exports.test.ts` (byte-stable output, document deep-equal after
 * export).
 *
 * Purity: no React, no DOM, no filesystem, no KnowledgeReader.
 */

import type {
  CampaignDocument,
  OpenPayload,
} from "../../../../domain/campaign/kernel/state";
import { currentState } from "../../../../domain/campaign/kernel/document";

/** Read model for the pre-export review panel. */
export interface ReviewSummary {
  readonly campaign_name: string;
  readonly warband_name: string;
  readonly warband_type: string;
  readonly is_draft: boolean;
  readonly gold: number;
  readonly wyrdstone_shards: number;
  readonly stash_value: number;
  readonly warriors: number;
  readonly heroes: number;
  readonly henchmen: number;
  readonly hirelings: number;
  readonly battles: number;
  readonly states: number;
  readonly current_state_number: number;
  /** True while a post-battle sequence is unfinished. */
  readonly post_battle_pending: boolean;
  /** Unresolved injury rolls parked on the pending post-battle. */
  readonly open_follow_ups: number;
  readonly inventory_items: number;
  readonly inventory_owned: number;
  /** Warriors missing games (blocked from the next battle). */
  readonly absent_warriors: number;
}

/** Aggregate everything the user should review before saving. */
export function reviewSummary(document: CampaignDocument): ReviewSummary {
  const { campaign } = document;
  const byKind = (kind: string) =>
    campaign.warriors.filter((w) => w.kind === kind).reduce((total, w) => total + (w.quantity ?? 1), 0);
  // The treasury lives on the newest committed timeline state; drafts have 0.
  const state = currentState(document);
  return {
    campaign_name: campaign.identity.campaign_name ?? "",
    warband_name: campaign.identity.warband_name ?? "",
    warband_type: campaign.identity.warband_type ?? "",
    is_draft: campaign.configuration.is_draft,
    gold: state?.gold ?? 0,
    wyrdstone_shards: state?.wyrdstone ?? 0,
    stash_value: campaign.resources.stash_value ?? 0,
    warriors: campaign.warriors.reduce((total, w) => total + (w.quantity ?? 1), 0),
    heroes: byKind("hero"),
    henchmen: byKind("henchman"),
    hirelings: byKind("hireling"),
    battles: campaign.battles.length,
    states: campaign.states.length,
    current_state_number: campaign.current_state_number,
    post_battle_pending: campaign.post_battles.some((post) => !post.complete),
    open_follow_ups: campaign.post_battles.reduce(
      (total, post) => total + (post.pending_follow_ups?.length ?? 0),
      0,
    ),
    inventory_items: campaign.inventory.length,
    inventory_owned: campaign.inventory.reduce((total, item) => total + item.owned, 0),
    absent_warriors: campaign.warriors.filter((w) => (w.games_to_miss ?? 0) > 0).length,
  };
}

/** One rendered ledger line. */
interface LedgerLine {
  readonly source: string;
  readonly text: string;
}

function collectLines(document: CampaignDocument): LedgerLine[] {
  const lines: LedgerLine[] = [];
  for (const battle of document.campaign.battles) {
    lines.push({
      source: `Battle ${battle.number}`,
      text: `${battle.date} — ${battle.scenario} vs ${battle.opponent}: ${battle.result} (gold ${battle.gold_delta >= 0 ? "+" : ""}${battle.gold_delta}, xp +${battle.xp_delta})`,
    });
  }
  for (const post of document.campaign.post_battles) {
    for (const entry of post.event_log ?? []) {
      const payload = entry as { step?: unknown; message?: unknown };
      lines.push({
        source: `Post-Battle ${post.battle_number} step ${String(payload.step ?? "?")}`,
        text: String(payload.message ?? JSON.stringify(entry)),
      });
    }
  }
  for (const entry of document.campaign.manual_log as readonly OpenPayload[]) {
    const payload = entry as { message?: unknown; date?: unknown };
    lines.push({
      source: `Manual log${payload.date ? ` (${String(payload.date)})` : ""}`,
      text: String(payload.message ?? JSON.stringify(entry)),
    });
  }
  return lines;
}

/** Auxiliary export: the full campaign ledger as plain text. */
export function ledgerText(document: CampaignDocument): string {
  const { campaign } = document;
  const header = [
    `Campaign: ${campaign.identity.campaign_name ?? ""}`,
    `Warband: ${campaign.identity.warband_name ?? ""} (${campaign.identity.warband_type ?? ""})`,
    `Timeline state: ${campaign.current_state_number}`,
    "",
  ].join("\n");
  const body = collectLines(document)
    .map((line) => `[${line.source}] ${line.text}`)
    .join("\n");
  return `${header}${body || "(no entries)"}\n`;
}

/** Auxiliary export: the roster as plain text. */
export function rosterSummaryText(document: CampaignDocument): string {
  const rows = document.campaign.warriors.map((warrior) => {
    const parts = [
      warrior.name,
      `${warrior.profile_name} (${warrior.kind})`,
      `xp ${warrior.experience}`,
      `${(warrior.quantity ?? 1)} model(s)`,
    ];
    if ((warrior.games_to_miss ?? 0) > 0) {
      parts.push(`ABSENT: misses ${warrior.games_to_miss} game(s) (${warrior.absence_reason ?? "Injury"})`);
    }
    if (warrior.condition) {
      parts.push(`condition: ${warrior.condition}${warrior.condition_detail ? ` (${warrior.condition_detail})` : ""}`);
    }
    return `- ${parts.join(" | ")}`;
  });
  return `${document.campaign.warriors.length} warrior row(s)\n${rows.join("\n")}\n`;
}
