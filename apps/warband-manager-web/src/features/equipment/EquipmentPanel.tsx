/**
 * Campaign equipment, stash and reassignment presentation.
 *
 * Renders the inventory read model (equipped/stash split per row) and the
 * per-warrior equipment entries; assign/withdraw actions dispatch through
 * the campaign app service (`assignEquipment` action) — rejections surface
 * via the shell's error seam, never thrown.
 *
 * Pure view over the CampaignAppView seam; read model helpers live in the
 * application feature so this file only exports components (react-refresh).
 */
import { useEffect, useState } from "react";

import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "../campaign/displayText";
import { KnowledgeHint } from "../campaign/KnowledgeHint";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";

interface EquipmentPanelProps {
  readonly document: CampaignDocument;
  readonly readOnly?: boolean;
  readonly locale?: "es" | "en";
  readonly knowledge?: ArtefactKnowledgeReader;
  readonly showTitle?: boolean;
  readonly trading?: boolean;
}

export function EquipmentPanel({ document, readOnly = false, locale = "en", knowledge, showTitle = true, trading = false }: EquipmentPanelProps) {
  const app = useCampaignApp();
  const { campaign } = document;
  const [busy, setBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  useEffect(() => {
    if (app.error) setLocalError(app.error);
  }, [app.error]);

  const assign = async (warriorId: string, itemId: string, quantity: number, direction: "equip" | "stash") => {
    setBusy(true);
    setLocalError(null);
    const ok = await app.runAction("assignEquipment", { warrior_id: warriorId, item_id: itemId, quantity, direction });
    if (!ok) {
      setLocalError(locale === "es" ? "No se pudo asignar el objeto. Comprueba que haya unidades disponibles y que el guerrero pueda llevarlo." : "The item could not be assigned. Check that stock is available and the warrior can carry it.");
    }
    setBusy(false);
  };
  const stashRows = campaign.inventory.filter((item) => item.stash > 0);
  const equippedRows = campaign.inventory.filter((item) => item.equipped > 0);
  const t = locale === "es" ? { title:"Equipo",stash:"En Reserva",emptyStash:"No hay nada en la reserva.",item:"Objeto",equip:"Equipar a",choose:"Elige Guerrero…",equipped:"Equipado",emptyEquipped:"No hay nada equipado.",return:"Devolver 1 a la Reserva",returnSet:"Devolver Juego a la Reserva" } : { title:"Equipment",stash:"In Stash",emptyStash:"Nothing in the stash.",item:"Item",equip:"Equip to",choose:"Choose Warrior…",equipped:"Equipped",emptyEquipped:"Nothing equipped.",return:"Return 1 to Stash",returnSet:"Return Set to Stash" };

  return (
    <section aria-label={t.title} className="equipment-panel">
      {showTitle && <h3>{t.title}</h3>}

      {localError && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {localError}
        </output>
      )}

      <div className="inventory-columns"><div><h4>{t.equipped}</h4>
      {equippedRows.length === 0 ? (
        <p>{t.emptyEquipped}</p>
      ) : (
        <ul className="equipped-list">
          {campaign.warriors.map((warrior) => {
            const entries = warrior.equipment.filter((entry) => entry.acquisition !== "fixed");
            if (entries.length === 0) return null;
            return <li className="equipped-warrior-group" key={warrior.id}>
              <strong>{warrior.name}</strong>
              <ul>
                {entries.map((entry) => <li key={`${warrior.id}:${entry.item_id}`}>
                  <span><KnowledgeHint knowledge={knowledge} kind="item" id={entry.item_id} locale={locale}>{entry.quantity} × {knowledgeName(knowledge, "item", entry.item_id, locale, entry.name)}</KnowledgeHint></span>
                  {!readOnly && <span className="equipment-actions"><button type="button" aria-label={`${locale === "es" ? "Devolver" : "Return"} ${knowledgeName(knowledge, "item", entry.item_id, locale, entry.name)} ${locale === "es" ? "llevado por" : "carried by"} ${warrior.name} ${locale === "es" ? "a la reserva" : "to stash"}`} disabled={busy || entry.transferable === false} data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la transferencia en curso." : "Wait for the current transfer to finish.") : entry.transferable === false ? (locale === "es" ? "Este equipo inicial no se puede transferir." : "This starting equipment cannot be transferred.") : undefined} onClick={() => void assign(warrior.id, entry.item_id, 1, "stash")}>{warrior.kind === "henchman" && entry.per_model ? t.returnSet : t.return}</button></span>}
                </li>)}
              </ul>
            </li>;
          })}
        </ul>
      )}</div><div><h4>{t.stash}</h4>
      {stashRows.length === 0 ? (
        <p>{t.emptyStash}</p>
      ) : (
        <table className="mobile-cards">
          <caption>{t.stash}</caption>
          <thead>
            <tr>
              <th scope="col">{t.item}</th>
              <th scope="col">{t.stash}</th>
              {!readOnly && <th scope="col">{t.equip}</th>}
            </tr>
          </thead>
          <tbody>
            {stashRows.map((item) => (
              <tr key={item.id}>
                <td data-label={t.item}><KnowledgeHint knowledge={knowledge} kind="item" id={item.id} locale={locale}>{knowledgeName(knowledge, "item", item.id, locale, item.name)}</KnowledgeHint></td>
                <td data-label={t.stash}>{item.stash}</td>
                {!readOnly && <td data-label={t.equip}>
                  <select
                    aria-label={`${locale === "es" ? "Asignar" : "Assign"} ${knowledgeName(knowledge, "item", item.id, locale, item.name)} ${locale === "es" ? "a un guerrero" : "to warrior"}`}
                    defaultValue=""
                    disabled={busy}
                    data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la transferencia en curso." : "Wait for the current transfer to finish.") : undefined}
                    onChange={(event) => {
                      const warriorId = event.target.value;
                      if (warriorId) {
                        void assign(warriorId, item.id, 1, "equip");
                        event.target.value = "";
                      }
                    }}
                  >
                    <option value="" disabled>
                      {t.choose}
                    </option>
                    {[...campaign.warriors].sort((a,b)=>a.name.localeCompare(b.name,locale)).map((warrior) => (
                      <option key={warrior.id} value={warrior.id}>
                        {warrior.name}
                      </option>
                    ))}
                  </select>
                </td>}
              </tr>
            ))}
          </tbody>
        </table>
      )}</div></div>
      {trading && knowledge && <HirelingsPanel document={document} listings={knowledge} locale={locale} mode="trading" showTradingTitle={false} />}
    </section>
  );
}
