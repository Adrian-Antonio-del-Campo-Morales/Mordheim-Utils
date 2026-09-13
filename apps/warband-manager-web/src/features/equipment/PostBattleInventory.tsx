import { useState } from "react";

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { CampaignDocument } from "../campaign/types";
import { ManualCorrectionsPanel } from "../economy/ManualCorrectionsPanel";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";
import { EquipmentPanel } from "./EquipmentPanel";

export function PostBattleInventory({ document, knowledge, locale = "en" }: { readonly document: CampaignDocument; readonly knowledge?: ArtefactKnowledgeReader; readonly locale?: "es" | "en" }) {
  const [dialog, setDialog] = useState<"trade" | "manual" | null>(null);
  const unavailable = locale === "es" ? "No se han cargado los datos de conocimiento necesarios." : "The required knowledge data is not loaded.";

  return <section className="draft-inventory" aria-label={locale === "es" ? "Inventario" : "Inventory"}>
    <div className="inventory-actionbar">
      <p>{locale === "es" ? "Mueve el equipo entre los guerreros y la reserva." : "Move equipment between warriors and the stash."}</p>
      <div>
        <button type="button" disabled={!knowledge} data-disabled-reason={!knowledge ? unavailable : undefined} onClick={() => setDialog("manual")}>{locale === "es" ? "AÑADIR OBJETO / RECURSOS" : "ADD ITEM / RESOURCES"}</button>
        <button className="primary" type="button" disabled={!knowledge} data-disabled-reason={!knowledge ? unavailable : undefined} onClick={() => setDialog("trade")}>{locale === "es" ? "COMPRAR Y VENDER" : "BUY AND SELL"}</button>
      </div>
    </div>
    <EquipmentPanel document={document} knowledge={knowledge} locale={locale} showTitle={false} />

    {dialog === "trade" && knowledge && <div className="modal-backdrop" role="presentation"><section className="modal inventory-trade-dialog" role="dialog" aria-modal="true" aria-labelledby="post-battle-trade-title"><button className="close" aria-label={locale === "es" ? "Cerrar" : "Close"} onClick={() => setDialog(null)}>×</button><h3 id="post-battle-trade-title">{locale === "es" ? "COMPRAR Y VENDER" : "BUY AND SELL"}</h3><HirelingsPanel document={document} listings={knowledge} locale={locale} mode="trading" showTradingTitle={false} /></section></div>}
    {dialog === "manual" && knowledge && <div className="modal-backdrop" role="presentation"><section className="modal inventory-manual-dialog" role="dialog" aria-modal="true" aria-labelledby="post-battle-manual-title"><button className="close" aria-label={locale === "es" ? "Cerrar" : "Close"} onClick={() => setDialog(null)}>×</button><h3 id="post-battle-manual-title">{locale === "es" ? "AJUSTES MANUALES" : "MANUAL ADJUSTMENTS"}</h3><ManualCorrectionsPanel document={document} knowledge={knowledge} locale={locale} /></section></div>}
  </section>;
}
