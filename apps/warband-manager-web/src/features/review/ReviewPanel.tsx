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
  readonly locale?: "es" | "en";
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

export function ReviewPanel({ document, locale = "en" }: ReviewPanelProps) {
  const summary = reviewSummary(document);
  const baseName = (summary.warband_name || summary.campaign_name || "campaign").replace(/[^\w-]+/g, "_");

  const t = locale === "es" ? { title:"Revisar antes de exportar",summary:"Resumen de campaña",campaign:"Campaña",warband:"Banda",treasury:"Tesorería",shards:"fragmento(s)",stash:"reserva",roster:"Guerreros",models:"miniatura(s)",heroes:"héroe(s)",henchmen:"secuaces",hirelings:"mercenario(s)",timeline:"Cronología",battles:"batalla(s)",state:"estado",of:"de",inventory:"Inventario",rows:"fila(s)",owned:"objeto(s) en propiedad",draft:"todavía es un borrador",post:"hay una secuencia post-batalla sin terminar",rolls:"tirada(s) de heridas sin resolver",absent:"guerrero(s) ausentes",safe:"Nada pendiente: puede guardarse.",pending:"Pendiente",exports:"Exportaciones auxiliares",downloadRoster:"Descargar banda (.txt)",downloadLedger:"Descargar historial (.txt)" } : { title:"Review before export",summary:"Campaign summary",campaign:"Campaign",warband:"Warband",treasury:"Treasury",shards:"shard(s)",stash:"stash",roster:"Roster",models:"model(s)",heroes:"hero(es)",henchmen:"henchmen",hirelings:"hireling(s)",timeline:"Timeline",battles:"battle(s)",state:"state",of:"of",inventory:"Inventory",rows:"row(s)",owned:"item(s) owned",draft:"this is still a draft",post:"a post-battle sequence is unfinished",rolls:"unresolved injury roll(s)",absent:"warrior(s) absent",safe:"Nothing pending — safe to save.",pending:"Pending",exports:"Auxiliary exports",downloadRoster:"Download roster (.txt)",downloadLedger:"Download ledger (.txt)" };
  const pending: string[] = [];
  if (summary.is_draft) pending.push(t.draft);
  if (summary.post_battle_pending) pending.push(t.post);
  if (summary.open_follow_ups > 0) pending.push(`${summary.open_follow_ups} ${t.rolls}`);
  if (summary.absent_warriors > 0) pending.push(`${summary.absent_warriors} ${t.absent}`);

  return (
    <section aria-label="Review">
      <h3>{t.title}</h3>

      <table>
        <caption>{t.summary}</caption>
        <tbody>
          <tr>
            <th scope="row">{t.campaign}</th>
            <td>{summary.campaign_name}</td>
          </tr>
          <tr>
            <th scope="row">{t.warband}</th>
            <td>
              {summary.warband_name} ({summary.warband_type})
            </td>
          </tr>
          <tr>
            <th scope="row">{t.treasury}</th>
            <td>
              {summary.gold} gc, {summary.wyrdstone_shards} {t.shards}, {t.stash} {summary.stash_value} gc
            </td>
          </tr>
          <tr>
            <th scope="row">{t.roster}</th>
            <td>
              {summary.warriors} {t.models} — {summary.heroes} {t.heroes}, {summary.henchmen} {t.henchmen},{" "}
              {summary.hirelings} {t.hirelings}
            </td>
          </tr>
          <tr>
            <th scope="row">{t.timeline}</th>
            <td>
              {summary.battles} {t.battles}, {t.state} {summary.current_state_number} {t.of} {summary.states}
            </td>
          </tr>
          <tr>
            <th scope="row">{t.inventory}</th>
            <td>
              {summary.inventory_items} {t.rows}, {summary.inventory_owned} {t.owned}
            </td>
          </tr>
        </tbody>
      </table>

      <p role="status">
        {pending.length === 0
          ? t.safe
          : `${t.pending}: ${pending.join("; ")}.`}
      </p>

      <h4>{t.exports}</h4>
      <button
        type="button"
        aria-label={`Download roster summary for ${summary.warband_name}`}
        onClick={() => downloadText(`${baseName}-roster.txt`, rosterSummaryText(document))}
      >
        {t.downloadRoster}
      </button>{" "}
      <button
        type="button"
        aria-label={`Download campaign ledger for ${summary.warband_name}`}
        onClick={() => downloadText(`${baseName}-ledger.txt`, ledgerText(document))}
      >
        {t.downloadLedger}
      </button>
    </section>
  );
}
