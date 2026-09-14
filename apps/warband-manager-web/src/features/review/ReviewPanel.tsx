/**
 * Final review and auxiliary exports for a campaign.
 *
 * Renders the review read model before saving and offers text downloads. The
 * main `.mordheim` export remains owned by the campaign slice.
 * Exporters are pure projections: this component only reads the document and
 * triggers downloads.
 */
import { reviewSummary, ledgerText, rosterSummaryText } from "@app/campaign/features/review/review-exports";
import { followUpNeedsResolution } from "@app/campaign/features/review/follow-up-acknowledgement-workflow";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "../campaign/displayText";

interface ReviewPanelProps {
  readonly document: CampaignDocument;
  readonly locale?: "es" | "en";
  readonly knowledge?: ArtefactKnowledgeReader;
  readonly onReturnToStep?: (step: number) => void;
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

export function ReviewPanel({ document, locale = "en", knowledge, onReturnToStep }: ReviewPanelProps) {
  const app = useCampaignApp();
  const summary = reviewSummary(document);
  const baseName = (summary.warband_name || summary.campaign_name || "campaign").replace(/[^\w-]+/g, "_");

  const t = locale === "es" ? { title:"Revisar antes de exportar",summary:"Resumen de campaña",campaign:"Campaña",warband:"Banda",treasury:"Tesorería",shards:"fragmento(s)",stash:"reserva",roster:"Guerreros",models:"miniatura(s)",heroes:"héroe(s)",henchmen:"secuaces",hirelings:"mercenario(s)",timeline:"Cronología",battles:"batalla(s)",state:"estado",of:"de",inventory:"Inventario",rows:"fila(s)",owned:"objeto(s) en propiedad",draft:"todavía es un borrador",post:"hay una secuencia post-batalla sin terminar",rolls:"seguimiento(s) sin resolver",absent:"guerrero(s) ausentes",safe:"Nada pendiente: puede guardarse.",pending:"Pendiente",returnPending:"Volver al paso pendiente",blocked:"Resuelve los seguimientos pendientes antes de confirmar.",exports:"Exportaciones auxiliares",downloadRoster:"Descargar banda (.txt)",downloadLedger:"Descargar historial (.txt)" } : { title:"Review before export",summary:"Campaign summary",campaign:"Campaign",warband:"Warband",treasury:"Treasury",shards:"shard(s)",stash:"stash",roster:"Roster",models:"model(s)",heroes:"hero(es)",henchmen:"henchmen",hirelings:"hireling(s)",timeline:"Timeline",battles:"battle(s)",state:"state",of:"of",inventory:"Inventory",rows:"row(s)",owned:"item(s) owned",draft:"this is still a draft",post:"a post-battle sequence is unfinished",rolls:"unresolved follow-up(s)",absent:"warrior(s) absent",safe:"Nothing pending — safe to save.",pending:"Pending",returnPending:"Return to pending step",blocked:"Resolve pending follow-ups before confirming.",exports:"Auxiliary exports",downloadRoster:"Download roster (.txt)",downloadLedger:"Download ledger (.txt)" };
  const openFollowUps = document.campaign.post_battles.flatMap((post) => (post.pending_follow_ups ?? []).filter((row) => followUpNeedsResolution(row, post.acknowledgements ?? {})));
  const pendingStep = (() => { const step = openFollowUps[0]?.["step"]; if (step === "injuries") return 0; const value = Number(step); return Number.isInteger(value) && value >= 0 && value <= 7 ? value : 0; })();
  const pending: string[] = [];
  if (summary.is_draft) pending.push(t.draft);
  if (summary.open_follow_ups > 0) pending.push(`${summary.open_follow_ups} ${t.rolls}`);
  if (summary.absent_warriors > 0) pending.push(`${summary.absent_warriors} ${t.absent}`);

  return (
    <section aria-label={locale === "es" ? "Revisión" : "Review"}>
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
              {summary.warband_name} ({knowledgeName(knowledge, "band", document.campaign.identity.band_id, locale, summary.warband_type)})
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
      {openFollowUps.length > 0 && onReturnToStep && <button type="button" onClick={() => onReturnToStep(pendingStep)}>{t.returnPending}</button>}
      {openFollowUps.length > 0 && <p className="condition" role="alert">{t.blocked}</p>}
      {summary.post_battle_pending && <button className="primary" disabled={openFollowUps.length > 0} data-disabled-reason={openFollowUps.length > 0 ? t.blocked : undefined} onClick={() => void app.runAction("finalizePostBattle", {})}>{locale === "es" ? "Confirmar siguiente estado" : "Confirm next state"}</button>}

      <h4>{t.exports}</h4>
      <button
        type="button"
        aria-label={`${locale === "es" ? "Descargar resumen de la banda de" : "Download roster summary for"} ${summary.warband_name}`}
        onClick={() => downloadText(`${baseName}-roster.txt`, rosterSummaryText(document))}
      >
        {t.downloadRoster}
      </button>{" "}
      <button
        type="button"
        aria-label={`${locale === "es" ? "Descargar historial de campaña de" : "Download campaign ledger for"} ${summary.warband_name}`}
        onClick={() => downloadText(`${baseName}-ledger.txt`, ledgerText(document))}
      >
        {t.downloadLedger}
      </button>
    </section>
  );
}
