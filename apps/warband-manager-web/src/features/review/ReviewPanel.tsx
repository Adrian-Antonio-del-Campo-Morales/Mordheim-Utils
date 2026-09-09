/**
 * P6.8 (web-migration-parallel-plan.md §P6.8): final review & auxiliary
 * exports UI.
 *
 * Renders the review read model (identity, treasury, roster roll-up,
 * pending work) so the user checks the full state before saving, and
 * offers the auxiliary text exports (roster summary, campaign ledger) as
 * downloads — the main `.mordheim` save stays in the slice.
 *
 * Exporters are pure projections (no rules in exporters, plan §P6.8): the
 * panel only reads the document and triggers Blob downloads; rejections
 * cannot occur because nothing here calls use cases.
 *
 * Pure view over the CampaignAppView seam; read models live in the
 * application feature so this file only exports components (react-refresh).
 */
import { reviewSummary, ledgerText, rosterSummaryText } from "@app/campaign/features/review/review-exports";
import type { CampaignDocument } from "../campaign/types";

interface ReviewPanelProps {
  readonly document: CampaignDocument;
}

/** Client-side download of an auxiliary text export. */
function downloadText(filename: string, text: string): void {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = window.document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function ReviewPanel({ document }: ReviewPanelProps) {
  const summary = reviewSummary(document);
  const baseName = (summary.warband_name || summary.campaign_name || "campaign").replace(/[^\w-]+/g, "_");

  const pending: string[] = [];
  if (summary.is_draft) pending.push("this is still a draft");
  if (summary.post_battle_pending) pending.push("a post-battle sequence is unfinished");
  if (summary.open_follow_ups > 0) pending.push(`${summary.open_follow_ups} unresolved injury roll(s)`);
  if (summary.absent_warriors > 0) pending.push(`${summary.absent_warriors} warrior(s) absent`);

  return (
    <section aria-label="Review">
      <h3>Review before export</h3>

      <table>
        <caption>Campaign summary</caption>
        <tbody>
          <tr>
            <th scope="row">Campaign</th>
            <td>{summary.campaign_name}</td>
          </tr>
          <tr>
            <th scope="row">Warband</th>
            <td>
              {summary.warband_name} ({summary.warband_type})
            </td>
          </tr>
          <tr>
            <th scope="row">Treasury</th>
            <td>
              {summary.gold} gc, {summary.wyrdstone_shards} shard(s), stash {summary.stash_value} gc
            </td>
          </tr>
          <tr>
            <th scope="row">Roster</th>
            <td>
              {summary.warriors} model(s) — {summary.heroes} hero(es), {summary.henchmen} henchmen,{" "}
              {summary.hirelings} hireling(s)
            </td>
          </tr>
          <tr>
            <th scope="row">Timeline</th>
            <td>
              {summary.battles} battle(s), state {summary.current_state_number} of {summary.states}
            </td>
          </tr>
          <tr>
            <th scope="row">Inventory</th>
            <td>
              {summary.inventory_items} row(s), {summary.inventory_owned} item(s) owned
            </td>
          </tr>
        </tbody>
      </table>

      <p role="status">
        {pending.length === 0
          ? "Nothing pending — safe to save."
          : `Pending: ${pending.join("; ")}.`}
      </p>

      <h4>Auxiliary exports</h4>
      <button
        type="button"
        aria-label={`Download roster summary for ${summary.warband_name}`}
        onClick={() => downloadText(`${baseName}-roster.txt`, rosterSummaryText(document))}
      >
        Download roster (.txt)
      </button>{" "}
      <button
        type="button"
        aria-label={`Download campaign ledger for ${summary.warband_name}`}
        onClick={() => downloadText(`${baseName}-ledger.txt`, ledgerText(document))}
      >
        Download ledger (.txt)
      </button>
    </section>
  );
}
