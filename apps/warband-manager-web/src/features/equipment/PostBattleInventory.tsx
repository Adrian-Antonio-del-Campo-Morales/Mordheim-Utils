import { textSymbol } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import { useState } from "react";

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { CampaignDocument } from "../campaign/types";
import { ManualCorrectionsPanel } from "../economy/ManualCorrectionsPanel";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";
import { EquipmentPanel } from "./EquipmentPanel";
import { useCloseOnCampaignError } from "../campaign/useCampaignApp";

export function PostBattleInventory({ document, knowledge, locale: requestedLocale }: { readonly document: CampaignDocument; readonly knowledge?: ArtefactKnowledgeReader; readonly locale?: "es" | "en" }) {
  const locale = useLocale(requestedLocale);
  const [dialog, setDialog] = useState<"trade" | "manual" | null>(null);
  useCloseOnCampaignError(() => setDialog(null));
  const unavailable = translate({ key: "ui.dac59621a80e" }, locale);

  return <section className="draft-inventory" aria-label={presentationOutput(translate({ key: "ui.1ad3e768c44c" }, locale))}>
    <div className="inventory-actionbar">
      <p>{presentationOutput(translate({ key: "ui.52cac94aec81" }, locale))}</p>
      <div>
        <button type="button" disabled={!knowledge} data-disabled-reason={(!knowledge ? unavailable : undefined) === undefined ? undefined : presentationOutput((!knowledge ? unavailable : undefined)!)} onClick={() => setDialog("manual")}>{presentationOutput(translate({ key: "ui.30ae8c333dd4" }, locale))}</button>
        <button className="primary" type="button" disabled={!knowledge} data-disabled-reason={(!knowledge ? unavailable : undefined) === undefined ? undefined : presentationOutput((!knowledge ? unavailable : undefined)!)} onClick={() => setDialog("trade")}>{presentationOutput(translate({ key: "ui.f6d2a8faa9f6" }, locale))}</button>
      </div>
    </div>
    <EquipmentPanel document={document} knowledge={knowledge} locale={locale} showTitle={false} />

    {dialog === "trade" && knowledge && <div className="modal-backdrop" role="presentation"><section className="modal inventory-trade-dialog" role="dialog" aria-modal="true" aria-labelledby="post-battle-trade-title"><button className="close" aria-label={presentationOutput(translate({ key: "ui.b61e7685256c" }, locale))} onClick={() => setDialog(null)}>{presentationOutput(textSymbol("×"))}</button><h3 id="post-battle-trade-title">{presentationOutput(translate({ key: "ui.f6d2a8faa9f6" }, locale))}</h3><HirelingsPanel document={document} listings={knowledge} locale={locale} mode="trading" showTradingTitle={false} /></section></div>}
    {dialog === "manual" && knowledge && <div className="modal-backdrop" role="presentation"><section className="modal inventory-manual-dialog" role="dialog" aria-modal="true" aria-labelledby="post-battle-manual-title"><button className="close" aria-label={presentationOutput(translate({ key: "ui.b61e7685256c" }, locale))} onClick={() => setDialog(null)}>{presentationOutput(textSymbol("×"))}</button><h3 id="post-battle-manual-title">{presentationOutput(translate({ key: "ui.7fbc176b9749" }, locale))}</h3><ManualCorrectionsPanel document={document} knowledge={knowledge} locale={locale} /></section></div>}
  </section>;
}
