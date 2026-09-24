import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, campaignPersonalName, warbandPersonalName, type PresentationValue } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
/**
 * Final review and auxiliary exports for a campaign.
 *
 * Renders the review read model before saving and offers text downloads. The
 * main `.mordheim` export remains owned by the campaign slice.
 * Exporters are pure projections: this component only reads the document and
 * triggers downloads.
 */
import { reviewSummary } from "@app/campaign/features/review/review-exports";
import { localizedLedger, localizedRoster } from "./readable-exports";
import { downloadPresentation } from "./download-presentation";
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

export function ReviewPanel({ document, locale: requestedLocale, knowledge, onReturnToStep }: ReviewPanelProps) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const summary = reviewSummary(document);
  const baseName = (summary.warband_name || summary.campaign_name || "campaign").replace(/[^\w-]+/g, "_");

  const t = ({ title: translate({ key: "ui.ba054282332c" }, locale), summary: translate({ key: "ui.3c5d43a2de47" }, locale), campaign: translate({ key: "ui.13624dd6f3e9" }, locale), warband: translate({ key: "ui.e64208a1bf43" }, locale), treasury: translate({ key: "ui.29be415cf396" }, locale), shards: translate({ key: "ui.64ef7133a1b8" }, locale), stash: translate({ key: "ui.ed8804dbcedb" }, locale), roster: translate({ key: "ui.3087408dfd27" }, locale), models: translate({ key: "ui.6c166d43fe19" }, locale), heroes: translate({ key: "ui.057aae2ea258" }, locale), henchmen: translate({ key: "ui.d30f55c2913b" }, locale), hirelings: translate({ key: "ui.a8384bb6532f" }, locale), timeline: translate({ key: "ui.d77ec83a8d1d" }, locale), battles: translate({ key: "ui.b7f848785b92" }, locale), state: translate({ key: "ui.37b55afd1403" }, locale), of: translate({ key: "ui.efeae3b09c13" }, locale), inventory: translate({ key: "ui.1ad3e768c44c" }, locale), rows: translate({ key: "ui.ddabce88c86c" }, locale), owned: translate({ key: "ui.74951b75f6fe" }, locale), draft: translate({ key: "ui.b6d0683bec1e" }, locale), post: translate({ key: "ui.7582bdb3189c" }, locale), rolls: translate({ key: "ui.2c0b15f98523" }, locale), absent: translate({ key: "ui.16815f1fb805" }, locale), safe: translate({ key: "ui.ff5ca866477f" }, locale), pending: translate({ key: "ui.8071fe9b52ff" }, locale), returnPending: translate({ key: "ui.29a744fbaa80" }, locale), blocked: translate({ key: "ui.6d920ed78914" }, locale), exports: translate({ key: "ui.038049a55fc8" }, locale), downloadRoster: translate({ key: "ui.6ba1c81b348a" }, locale), downloadLedger: translate({ key: "ui.ae53efb315e5" }, locale) });
  const openFollowUps = document.campaign.post_battles.flatMap((post) => (post.pending_follow_ups ?? []).filter((row) => followUpNeedsResolution(row, post.acknowledgements ?? {})));
  const pendingStep = (() => { const step = openFollowUps[0]?.["step"]; if (step === "injuries") return 0; const value = Number(step); return Number.isInteger(value) && value >= 0 && value <= 7 ? value : 0; })();
  const pending: PresentationValue[] = [];
  if (summary.is_draft) pending.push(t.draft);
  if (summary.open_follow_ups > 0) pending.push(textJoin([textNumber(summary.open_follow_ups, locale), t.rolls]));
  if (summary.absent_warriors > 0) pending.push(textJoin([textNumber(summary.absent_warriors, locale), t.absent]));

  return (
    <section aria-label={presentationOutput(translate({ key: "ui.d128195913f6" }, locale))}>
      <h3>{presentationOutput(t.title)}</h3>

      <table>
        <caption>{presentationOutput(t.summary)}</caption>
        <tbody>
          <tr>
            <th scope="row">{presentationOutput(t.campaign)}</th>
            <td>{presentationOutput(campaignPersonalName(document.campaign, locale))}</td>
          </tr>
          <tr>
            <th scope="row">{presentationOutput(t.warband)}</th>
            <td>
              {presentationOutput(textJoin([warbandPersonalName(document.campaign, locale), textJoin([textSymbol("("), knowledgeName(knowledge, "band", document.campaign.identity.band_id, locale), textSymbol(")")], "")]))}
            </td>
          </tr>
          <tr>
            <th scope="row">{presentationOutput(t.treasury)}</th>
            <td>
              {presentationOutput(textJoin([textJoin([textNumber(summary.gold, locale), translate({ key: "ui.cb8fa67082cb" }, locale)], ""), textJoin([textNumber(summary.wyrdstone_shards, locale), t.shards]), textJoin([t.stash, textJoin([textNumber(summary.stash_value, locale), translate({ key: "ui.cb8fa67082cb" }, locale)], "")])], ", "))}
            </td>
          </tr>
          <tr>
            <th scope="row">{presentationOutput(t.roster)}</th>
            <td>
              {presentationOutput(textJoin([textJoin([textNumber(summary.warriors, locale), t.models]), textJoin([textNumber(summary.heroes, locale), t.heroes]), textJoin([textNumber(summary.henchmen, locale), t.henchmen]), textJoin([textNumber(summary.hirelings, locale), t.hirelings])], ", "))}
            </td>
          </tr>
          <tr>
            <th scope="row">{presentationOutput(t.timeline)}</th>
            <td>
              {presentationOutput(textJoin([textJoin([textNumber(summary.battles, locale), t.battles]), textJoin([t.state, textNumber(summary.current_state_number, locale), t.of, textNumber(summary.states, locale)])], ", "))}
            </td>
          </tr>
          <tr>
            <th scope="row">{presentationOutput(t.inventory)}</th>
            <td>
              {presentationOutput(textJoin([textJoin([textNumber(summary.inventory_items, locale), t.rows]), textJoin([textNumber(summary.inventory_owned, locale), t.owned])], ", "))}
            </td>
          </tr>
        </tbody>
      </table>

      <p role="status">
        {presentationOutput(pending.length === 0
          ? t.safe
          : textJoin([textJoin([t.pending, textSymbol(":")], ""), textJoin(pending, ", ")]))}
      </p>
      {openFollowUps.length > 0 && onReturnToStep && <button type="button" onClick={() => onReturnToStep(pendingStep)}>{presentationOutput(t.returnPending)}</button>}
      {openFollowUps.length > 0 && <p className="condition" role="alert">{presentationOutput(t.blocked)}</p>}
      {summary.post_battle_pending && <button className="primary" disabled={openFollowUps.length > 0} data-disabled-reason={openFollowUps.length > 0 ? presentationOutput(t.blocked) : undefined} onClick={() => void app.runAction("finalizePostBattle", {})}>{presentationOutput(translate({ key: "ui.1160ade2beac" }, locale))}</button>}

      <h4>{presentationOutput(t.exports)}</h4>
      <button
        type="button"
        aria-label={presentationOutput(textJoin([translate({ key: "ui.266f95057684" }, locale), warbandPersonalName(document.campaign, locale)]))}
        onClick={() => downloadPresentation(`${baseName}-roster.txt`, localizedRoster(document, locale, knowledge))}
      >
        {presentationOutput(t.downloadRoster)}
      </button>
      <button
        type="button"
        aria-label={presentationOutput(textJoin([translate({ key: "ui.5c50dac10736" }, locale), warbandPersonalName(document.campaign, locale)]))}
        onClick={() => downloadPresentation(`${baseName}-ledger.txt`, localizedLedger(document, locale, knowledge))}
      >
        {presentationOutput(t.downloadLedger)}
      </button>
    </section>
  );
}
